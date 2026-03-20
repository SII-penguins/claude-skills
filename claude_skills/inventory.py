from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Iterable

from .adapters.builtins import load_builtin_catalog
from .adapters.claude_settings import load_claude_settings
from .adapters.installed_plugins import load_installed_plugins
from .adapters.local_skills import load_local_skills
from .adapters.marketplaces import load_known_marketplaces, load_marketplace_plugins
from .adapters.mcp import load_mcp_definitions
from .adapters.plugin_cache import load_plugin_cache
from .adapters.skill_lock import load_skill_lock
from .confidence import finalize_capabilities
from .config import ClaudeSkillsPaths
from .models import (
    Capability,
    CapabilityKind,
    CapabilityObservation,
    InventoryIssue,
    InventoryReport,
    IssueSeverity,
    Relationship,
)
from .utils import unique_strings

SOURCE_PRIORITY = {
    "builtin_catalog": 100,
    "plugin_cache_manifest": 90,
    "plugin_cache_skill": 90,
    "installed_mcp": 90,
    "marketplace_plugin": 80,
    "marketplace_mcp": 80,
    "installed_plugin": 70,
    "claude_settings": 70,
    "local_skill": 65,
    "skill_lock": 55,
}


def build_inventory(paths: ClaudeSkillsPaths | None = None) -> InventoryReport:
    paths = paths or ClaudeSkillsPaths.default()

    local_skill_observations, missing_skill_dirs = load_local_skills(paths.agents_skills_dir)
    lockfile_observations = load_skill_lock(paths.skill_lock_path)
    settings_state = load_claude_settings(paths.claude_settings_path)
    installed_plugins_state = load_installed_plugins(paths.installed_plugins_path)
    plugin_cache_observations = load_plugin_cache(installed_plugins_state.records)
    marketplaces = load_known_marketplaces(paths.known_marketplaces_path)
    marketplace_plugin_observations = load_marketplace_plugins(marketplaces)
    mcp_observations = load_mcp_definitions(
        marketplaces=marketplaces,
        installed_plugin_records=installed_plugins_state.records,
        available_env_keys=settings_state.available_env_keys,
    )

    observations: list[CapabilityObservation] = []
    observations.extend(load_builtin_catalog())
    observations.extend(local_skill_observations)
    observations.extend(lockfile_observations)
    observations.extend(settings_state.observations)
    observations.extend(installed_plugins_state.observations)
    observations.extend(plugin_cache_observations)
    observations.extend(marketplace_plugin_observations)
    observations.extend(mcp_observations)

    report = build_inventory_from_observations(observations)
    report.issues.extend(_issues_for_missing_skill_dirs(missing_skill_dirs))
    report.issues = sorted(report.issues, key=lambda issue: (issue.severity.value, issue.code, issue.capability_name or ""))
    return report


def build_inventory_from_observations(observations: list[CapabilityObservation]) -> InventoryReport:
    merged = merge_observations(observations)
    finalized = finalize_capabilities(merged)
    issues = diagnose_capabilities(finalized)
    return InventoryReport(capabilities=finalized, issues=issues)


def merge_observations(observations: list[CapabilityObservation]) -> list[Capability]:
    capabilities: dict[str, Capability] = {}
    priorities: dict[tuple[str, str], int] = {}

    for observation in observations:
        capability = capabilities.get(observation.id)
        if capability is None:
            capability = Capability(id=observation.id, kind=observation.kind, name=observation.name)
            capabilities[observation.id] = capability

        _assign_preferred(capability, priorities, "name", observation.name, observation.source.source_type)
        _assign_preferred(capability, priorities, "description", observation.description, observation.source.source_type)
        _assign_preferred(capability, priorities, "category", observation.category, observation.source.source_type)

        if observation.installed_locally is True:
            capability.installed_locally = True
        if observation.marketplace_visible is True:
            capability.marketplace_visible = True
        if observation.builtin is True:
            capability.builtin = True

        capability.enabled = _merge_optional_bool(capability.enabled, observation.enabled)
        capability.callable_now = capability.callable_now or bool(observation.callable_now)

        capability.reasons = unique_strings([*capability.reasons, *observation.reasons])
        capability.relationships = _merge_relationships(capability.relationships, observation.relationships)
        capability.sources.append(observation.source)

    return list(capabilities.values())


def filter_capabilities(
    capabilities: list[Capability],
    *,
    kind: CapabilityKind | None = None,
    installed: bool | None = None,
    enabled: bool | None = None,
    callable_now: bool | None = None,
    marketplace_only: bool = False,
    category: str | None = None,
    plugin: str | None = None,
) -> list[Capability]:
    filtered = capabilities

    if kind is not None:
        filtered = [capability for capability in filtered if capability.kind == kind]
    if installed is not None:
        filtered = [capability for capability in filtered if capability.installed_locally is installed]
    if enabled is not None:
        filtered = [capability for capability in filtered if capability.enabled is enabled]
    if callable_now is not None:
        filtered = [capability for capability in filtered if capability.callable_now is callable_now]
    if marketplace_only:
        filtered = [capability for capability in filtered if capability.availability.value == "marketplace_only"]
    if category:
        filtered = [capability for capability in filtered if capability.category == category]
    if plugin:
        normalized = plugin.casefold()
        filtered = [
            capability
            for capability in filtered
            if any(
                relationship.target_id.casefold() == f"plugin:{plugin}".casefold()
                or (relationship.target_name or "").casefold() == normalized
                or relationship.target_id.removeprefix("plugin:").casefold() == normalized
                for relationship in capability.relationships
            )
        ]

    return sorted(filtered, key=lambda capability: capability.sort_key())


def find_capability(capabilities: list[Capability], query: str) -> Capability | None:
    exact_matches = [capability for capability in capabilities if capability.matches(query)]
    if exact_matches:
        return sorted(exact_matches, key=lambda capability: capability.sort_key())[0]

    normalized = query.casefold()
    partial_matches = [
        capability
        for capability in capabilities
        if normalized in capability.name.casefold() or normalized in capability.id.casefold()
    ]
    if len(partial_matches) == 1:
        return partial_matches[0]
    return None


def related_capabilities(capabilities: list[Capability], capability_id: str) -> list[Capability]:
    related: list[Capability] = []
    for capability in capabilities:
        if any(relationship.target_id == capability_id for relationship in capability.relationships):
            related.append(capability)
    return sorted(related, key=lambda item: item.sort_key())


def summarize(report: InventoryReport) -> dict[str, Counter[str]]:
    kind_counts = Counter(capability.kind.value for capability in report.capabilities)
    availability_counts = Counter(capability.availability.value for capability in report.capabilities)
    confidence_counts = Counter(capability.confidence.value for capability in report.capabilities)
    return {
        "kind": kind_counts,
        "availability": availability_counts,
        "confidence": confidence_counts,
    }


def diagnose_capabilities(capabilities: list[Capability]) -> list[InventoryIssue]:
    issues: list[InventoryIssue] = []

    for capability in capabilities:
        source_types = {source.source_type for source in capability.sources}

        if capability.kind == CapabilityKind.PLUGIN and capability.enabled and not capability.installed_locally:
            issues.append(
                InventoryIssue(
                    code="enabled_plugin_missing_install",
                    severity=IssueSeverity.ERROR,
                    capability_id=capability.id,
                    capability_name=capability.name,
                    message="Plugin is enabled in settings but no installation record was found.",
                )
            )

        if capability.kind == CapabilityKind.SKILL and "skill_lock" in source_types and not capability.installed_locally:
            issues.append(
                InventoryIssue(
                    code="lockfile_missing_skill_content",
                    severity=IssueSeverity.WARNING,
                    capability_id=capability.id,
                    capability_name=capability.name,
                    message="Skill appears in the lockfile but no local SKILL.md content was found.",
                )
            )

        if capability.kind == CapabilityKind.MCP_SERVER:
            missing_env = sorted(
                {
                    env_var
                    for source in capability.sources
                    for env_var in source.facts.get("missing_env_vars", [])
                    if isinstance(env_var, str)
                }
            )
            if missing_env:
                issues.append(
                    InventoryIssue(
                        code="mcp_missing_env",
                        severity=IssueSeverity.WARNING,
                        capability_id=capability.id,
                        capability_name=capability.name,
                        message="MCP server is missing required environment variables.",
                        details={"missing_env_vars": missing_env},
                    )
                )

        if capability.availability.value == "marketplace_only":
            issues.append(
                InventoryIssue(
                    code="marketplace_only",
                    severity=IssueSeverity.INFO,
                    capability_id=capability.id,
                    capability_name=capability.name,
                    message="Capability is visible in marketplace metadata but is not installed locally.",
                )
            )

    return issues


def _issues_for_missing_skill_dirs(directories: Iterable[Path]) -> list[InventoryIssue]:
    issues: list[InventoryIssue] = []
    for directory in directories:
        issues.append(
            InventoryIssue(
                code="missing_skill_markdown",
                severity=IssueSeverity.WARNING,
                capability_name=directory.name,
                message="Skill directory exists locally but SKILL.md is missing.",
                details={"path": str(directory)},
            )
        )
    return issues


def _assign_preferred(
    capability: Capability,
    priorities: dict[tuple[str, str], int],
    field_name: str,
    value: str | None,
    source_type: str,
) -> None:
    if not value:
        return

    priority = SOURCE_PRIORITY.get(source_type, 0)
    key = (capability.id, field_name)
    current_priority = priorities.get(key, -1)
    if current_priority > priority:
        return

    setattr(capability, field_name, value)
    priorities[key] = priority


def _merge_optional_bool(current: bool | None, incoming: bool | None) -> bool | None:
    if incoming is None:
        return current
    if current is None:
        return incoming
    return current or incoming


def _merge_relationships(existing: list[Relationship], incoming: list[Relationship]) -> list[Relationship]:
    merged = list(existing)
    seen = {
        (relationship.type, relationship.target_id, relationship.target_name or "", tuple(sorted(relationship.details.items())))
        for relationship in merged
    }
    for relationship in incoming:
        key = (
            relationship.type,
            relationship.target_id,
            relationship.target_name or "",
            tuple(sorted(relationship.details.items())),
        )
        if key not in seen:
            merged.append(relationship)
            seen.add(key)
    return merged
