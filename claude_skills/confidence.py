from __future__ import annotations

from collections.abc import Iterable

from .categorizer import categorize_capability
from .models import Availability, Capability, CapabilityKind, ConfidenceLevel, RelationshipType
from .utils import unique_strings


PLUGIN_SKILL_SOURCES = {"plugin_cache_skill"}
LOCAL_SKILL_SOURCES = {"local_skill"}
LOCKFILE_SOURCES = {"skill_lock"}
MARKETPLACE_MCP_SOURCES = {"marketplace_mcp"}
INSTALLED_MCP_SOURCES = {"installed_mcp"}


def finalize_capabilities(capabilities: list[Capability]) -> list[Capability]:
    index = {capability.id: capability for capability in capabilities}
    finalized: list[Capability] = []
    for capability in capabilities:
        categorized = capability.model_copy(update={"category": capability.category or categorize_capability(capability)})
        finalized.append(_score_capability(categorized, index))
    return sorted(finalized, key=lambda capability: capability.sort_key())


def _score_capability(capability: Capability, index: dict[str, Capability]) -> Capability:
    reasons = list(capability.reasons)
    source_types = {source.source_type for source in capability.sources}
    provider_plugins = _provider_plugins(capability, index)
    provider_names = [plugin.name for plugin in provider_plugins]

    if capability.builtin or capability.kind == CapabilityKind.TOOL:
        reasons.append("Capability comes from the static builtin catalog.")
        return capability.model_copy(
            update={
                "installed_locally": True,
                "enabled": True,
                "callable_now": True,
                "availability": Availability.BUILTIN,
                "confidence": ConfidenceLevel.HIGH,
                "reasons": unique_strings(reasons),
            }
        )

    if capability.kind == CapabilityKind.PLUGIN:
        if capability.installed_locally and capability.enabled:
            reasons.append("Plugin is installed locally and enabled in Claude settings.")
            return capability.model_copy(
                update={
                    "callable_now": True,
                    "availability": Availability.ENABLED,
                    "confidence": ConfidenceLevel.HIGH,
                    "reasons": unique_strings(reasons),
                }
            )
        if capability.installed_locally:
            reasons.append("Plugin is installed locally but not enabled in Claude settings.")
            return capability.model_copy(
                update={
                    "callable_now": False,
                    "availability": Availability.INSTALLED,
                    "confidence": ConfidenceLevel.MEDIUM,
                    "reasons": unique_strings(reasons),
                }
            )
        if capability.marketplace_visible:
            reasons.append("Plugin is visible in a marketplace but no local install record was found.")
            return capability.model_copy(
                update={
                    "callable_now": False,
                    "availability": Availability.MARKETPLACE_ONLY,
                    "confidence": ConfidenceLevel.LOW,
                    "reasons": unique_strings(reasons),
                }
            )
        if capability.enabled:
            reasons.append("Plugin is enabled in settings but no local install record was found.")
        return capability.model_copy(
            update={
                "callable_now": False,
                "availability": Availability.UNKNOWN,
                "confidence": ConfidenceLevel.LOW,
                "reasons": unique_strings(reasons),
            }
        )

    if capability.kind == CapabilityKind.SKILL:
        if provider_plugins and any(plugin.installed_locally and plugin.enabled for plugin in provider_plugins) and source_types & PLUGIN_SKILL_SOURCES:
            reasons.append(
                f"Skill is packaged in an installed and enabled plugin: {', '.join(provider_names)}."
            )
            return capability.model_copy(
                update={
                    "enabled": True,
                    "callable_now": True,
                    "availability": Availability.ENABLED,
                    "confidence": ConfidenceLevel.HIGH,
                    "reasons": unique_strings(reasons),
                }
            )
        if capability.installed_locally and _has_complete_manifest(capability, LOCAL_SKILL_SOURCES):
            reasons.append("Local SKILL.md exists with parseable frontmatter, but current session exposure is inferred.")
            return capability.model_copy(
                update={
                    "callable_now": True,
                    "availability": Availability.INSTALLED,
                    "confidence": ConfidenceLevel.MEDIUM,
                    "reasons": unique_strings(reasons),
                }
            )
        if source_types & LOCKFILE_SOURCES:
            reasons.append("Skill appears in the lockfile, but local content is incomplete or missing.")
            return capability.model_copy(
                update={
                    "callable_now": False,
                    "availability": Availability.UNKNOWN,
                    "confidence": ConfidenceLevel.LOW,
                    "reasons": unique_strings(reasons),
                }
            )
        if capability.marketplace_visible:
            reasons.append("Skill is only visible through marketplace metadata.")
            return capability.model_copy(
                update={
                    "callable_now": False,
                    "availability": Availability.MARKETPLACE_ONLY,
                    "confidence": ConfidenceLevel.LOW,
                    "reasons": unique_strings(reasons),
                }
            )
        return capability.model_copy(
            update={
                "callable_now": False,
                "availability": Availability.UNKNOWN,
                "confidence": ConfidenceLevel.LOW,
                "reasons": unique_strings(reasons),
            }
        )

    if capability.kind == CapabilityKind.MCP_SERVER:
        required_env = _collect_fact_values(capability, "required_env_vars")
        missing_env = _collect_fact_values(capability, "missing_env_vars")
        provider_enabled = any(plugin.installed_locally and plugin.enabled for plugin in provider_plugins)
        provider_installed = any(plugin.installed_locally for plugin in provider_plugins)

        if capability.installed_locally and not missing_env and (provider_enabled or not provider_plugins):
            reasons.append("Installed MCP definition has all required environment variables configured.")
            if provider_names:
                reasons.append(f"MCP server is exposed by enabled plugin: {', '.join(provider_names)}.")
            return capability.model_copy(
                update={
                    "enabled": True if provider_enabled else capability.enabled,
                    "callable_now": True,
                    "availability": Availability.ENABLED if provider_enabled else Availability.INSTALLED,
                    "confidence": ConfidenceLevel.HIGH,
                    "reasons": unique_strings(reasons),
                }
            )

        if capability.installed_locally and missing_env:
            reasons.append(
                "Installed MCP definition is missing required environment variables: "
                + ", ".join(sorted(missing_env))
                + "."
            )
            return capability.model_copy(
                update={
                    "enabled": True if provider_enabled else capability.enabled,
                    "callable_now": False,
                    "availability": Availability.ENABLED if provider_enabled else Availability.INSTALLED,
                    "confidence": ConfidenceLevel.MEDIUM,
                    "reasons": unique_strings(reasons),
                }
            )

        if capability.installed_locally and provider_installed and not provider_enabled:
            reasons.append("Installed MCP definition belongs to a plugin that is not enabled.")
            return capability.model_copy(
                update={
                    "callable_now": False,
                    "availability": Availability.INSTALLED,
                    "confidence": ConfidenceLevel.MEDIUM,
                    "reasons": unique_strings(reasons),
                }
            )

        if capability.marketplace_visible or source_types & MARKETPLACE_MCP_SOURCES:
            reasons.append("MCP server is visible in marketplace metadata only.")
            return capability.model_copy(
                update={
                    "callable_now": False,
                    "availability": Availability.MARKETPLACE_ONLY,
                    "confidence": ConfidenceLevel.LOW,
                    "reasons": unique_strings(reasons),
                }
            )

        return capability.model_copy(
            update={
                "callable_now": False,
                "availability": Availability.UNKNOWN,
                "confidence": ConfidenceLevel.LOW,
                "reasons": unique_strings(reasons),
            }
        )

    return capability


def _provider_plugins(capability: Capability, index: dict[str, Capability]) -> list[Capability]:
    providers: list[Capability] = []
    for relationship in capability.relationships:
        if relationship.type != RelationshipType.PROVIDED_BY.value:
            continue
        plugin = index.get(relationship.target_id)
        if plugin is not None:
            providers.append(plugin)
    return providers


def _collect_fact_values(capability: Capability, key: str) -> set[str]:
    values: set[str] = set()
    for source in capability.sources:
        raw = source.facts.get(key)
        if isinstance(raw, str):
            values.add(raw)
        elif isinstance(raw, Iterable):
            for item in raw:
                if isinstance(item, str):
                    values.add(item)
    return values


def _has_complete_manifest(capability: Capability, allowed_source_types: set[str]) -> bool:
    for source in capability.sources:
        if source.source_type in allowed_source_types and source.facts.get("manifest_complete"):
            return True
    return False
