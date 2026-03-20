from __future__ import annotations

from pathlib import Path

from ..models import CapabilityKind, CapabilityObservation, ConfidenceLevel, Evidence, Relationship, RelationshipType, capability_id
from ..utils import first_heading, load_json_file, parse_frontmatter_file, sanitize_data
from .installed_plugins import InstalledPluginRecord



def load_plugin_cache(records: list[InstalledPluginRecord]) -> list[CapabilityObservation]:
    observations: list[CapabilityObservation] = []
    for record in records:
        observations.extend(_load_record(record))
    return observations



def _load_record(record: InstalledPluginRecord) -> list[CapabilityObservation]:
    marketplace_manifest_path = record.install_path / ".claude-plugin" / "marketplace.json"
    plugin_manifest_path = record.install_path / ".claude-plugin" / "plugin.json"

    if marketplace_manifest_path.is_file():
        return _load_marketplace_bundle(record, marketplace_manifest_path)
    if plugin_manifest_path.is_file():
        return _load_single_plugin(record, plugin_manifest_path)
    return []



def _load_marketplace_bundle(record: InstalledPluginRecord, manifest_path: Path) -> list[CapabilityObservation]:
    payload = load_json_file(manifest_path)
    if not isinstance(payload, dict):
        return []

    plugins = payload.get("plugins")
    if not isinstance(plugins, list):
        return []

    observations: list[CapabilityObservation] = []
    install_root = manifest_path.parent.parent
    saw_matching_plugin = False
    referenced_skill_paths: set[Path] = set()

    for plugin_entry in plugins:
        if not isinstance(plugin_entry, dict):
            continue
        plugin_name = str(plugin_entry.get("name") or "").strip()
        if plugin_name != record.plugin_name:
            continue

        saw_matching_plugin = True
        observations.append(
            CapabilityObservation(
                id=f"plugin:{record.plugin_key}",
                kind=CapabilityKind.PLUGIN,
                name=record.plugin_key,
                description=_string_or_none(plugin_entry.get("description")),
                installed_locally=True,
                reasons=["Installed plugin metadata was found in the plugin cache."],
                source=Evidence(
                    source_type="plugin_cache_manifest",
                    source_path=str(manifest_path),
                    confidence=ConfidenceLevel.HIGH,
                    facts=sanitize_data(
                        {
                            "plugin_name": plugin_name,
                            "marketplace_name": record.marketplace_name,
                            "source": plugin_entry.get("source"),
                            "strict": plugin_entry.get("strict"),
                            "skills": plugin_entry.get("skills") or [],
                        }
                    ),
                ),
            )
        )

        for skill_reference in plugin_entry.get("skills") or []:
            skill_dir = _resolve_skill_reference(install_root, skill_reference)
            if skill_dir is None:
                continue
            skill_md = skill_dir / "SKILL.md"
            if not skill_md.is_file():
                continue
            referenced_skill_paths.add(skill_md.resolve())
            observations.extend(_skill_observations_for_path(record, skill_md))

    if not saw_matching_plugin:
        return []

    skills_dir = record.install_path / "skills"
    if skills_dir.is_dir():
        for skill_md in sorted(skills_dir.glob("*/SKILL.md")):
            resolved = skill_md.resolve()
            if resolved in referenced_skill_paths:
                continue
            observations.extend(_skill_observations_for_path(record, skill_md))

    return observations



def _load_single_plugin(record: InstalledPluginRecord, manifest_path: Path) -> list[CapabilityObservation]:
    payload = load_json_file(manifest_path)
    if not isinstance(payload, dict):
        return []

    observations: list[CapabilityObservation] = [
        CapabilityObservation(
            id=f"plugin:{record.plugin_key}",
            kind=CapabilityKind.PLUGIN,
            name=record.plugin_key,
            description=_string_or_none(payload.get("description")),
            installed_locally=True,
            reasons=["Installed plugin metadata was found in the plugin cache."],
            source=Evidence(
                source_type="plugin_cache_manifest",
                source_path=str(manifest_path),
                confidence=ConfidenceLevel.HIGH,
                facts=sanitize_data(payload),
            ),
        )
    ]

    skills_dir = record.install_path / "skills"
    if skills_dir.is_dir():
        for skill_md in sorted(skills_dir.glob("*/SKILL.md")):
            observations.extend(_skill_observations_for_path(record, skill_md))

    return observations



def _resolve_skill_reference(base_dir: Path, skill_reference: object) -> Path | None:
    if not isinstance(skill_reference, str):
        return None
    return (base_dir / skill_reference).resolve()



def _skill_observations_for_path(record: InstalledPluginRecord, skill_md: Path) -> list[CapabilityObservation]:
    frontmatter, body = parse_frontmatter_file(skill_md)
    skill_name = str(frontmatter.get("name") or skill_md.parent.name)
    description = _string_or_none(frontmatter.get("description"))
    facts = {
        "manifest_complete": True,
        "license": frontmatter.get("license"),
        "compatibility": frontmatter.get("compatibility"),
        "allowed_tools": frontmatter.get("allowed-tools"),
        "heading": first_heading(body),
        "plugin": record.plugin_key,
    }

    return [
        CapabilityObservation(
            id=capability_id(CapabilityKind.SKILL, skill_name),
            kind=CapabilityKind.SKILL,
            name=skill_name,
            description=description,
            installed_locally=True,
            reasons=["Skill is bundled inside an installed plugin cache."],
            relationships=[
                Relationship(
                    type=RelationshipType.PROVIDED_BY.value,
                    target_id=f"plugin:{record.plugin_key}",
                    target_name=record.plugin_key,
                )
            ],
            source=Evidence(
                source_type="plugin_cache_skill",
                source_path=str(skill_md),
                confidence=ConfidenceLevel.HIGH,
                facts=sanitize_data(facts),
            ),
        )
    ]



def _string_or_none(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None
