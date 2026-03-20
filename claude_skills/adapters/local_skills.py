from __future__ import annotations

from pathlib import Path
from typing import Any

from ..models import CapabilityKind, CapabilityObservation, ConfidenceLevel, Evidence, capability_id
from ..utils import first_heading, parse_frontmatter_file, sanitize_data


def load_local_skills(skills_dir: Path) -> tuple[list[CapabilityObservation], list[Path]]:
    observations: list[CapabilityObservation] = []
    missing_skill_dirs: list[Path] = []

    if not skills_dir.is_dir():
        return observations, missing_skill_dirs

    for entry in sorted(path for path in skills_dir.iterdir() if path.is_dir()):
        skill_md = entry / "SKILL.md"
        if not skill_md.is_file():
            missing_skill_dirs.append(entry)
            continue

        frontmatter, body = parse_frontmatter_file(skill_md)
        skill_name = str(frontmatter.get("name") or entry.name)
        description = _string_or_none(frontmatter.get("description"))
        facts = {
            "directory_name": entry.name,
            "manifest_complete": True,
            "license": frontmatter.get("license"),
            "compatibility": frontmatter.get("compatibility"),
            "allowed_tools": frontmatter.get("allowed-tools"),
            "skill_author": _extract_skill_author(frontmatter),
            "heading": first_heading(body),
        }

        observations.append(
            CapabilityObservation(
                id=capability_id(CapabilityKind.SKILL, skill_name),
                kind=CapabilityKind.SKILL,
                name=skill_name,
                description=description,
                installed_locally=True,
                reasons=["Found local skill directory with SKILL.md."],
                source=Evidence(
                    source_type="local_skill",
                    source_path=str(skill_md),
                    confidence=ConfidenceLevel.MEDIUM,
                    facts=sanitize_data(facts),
                ),
            )
        )

    return observations, missing_skill_dirs


def _extract_skill_author(frontmatter: dict[str, Any]) -> str | None:
    metadata = frontmatter.get("metadata")
    if not isinstance(metadata, dict):
        return None
    author = metadata.get("skill-author")
    return str(author) if author else None


def _string_or_none(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None
