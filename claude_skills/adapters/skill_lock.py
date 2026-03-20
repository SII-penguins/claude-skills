from __future__ import annotations

from pathlib import Path

from ..models import CapabilityKind, CapabilityObservation, ConfidenceLevel, Evidence, capability_id
from ..utils import load_json_file, sanitize_data


def load_skill_lock(lock_path: Path) -> list[CapabilityObservation]:
    payload = load_json_file(lock_path)
    if not isinstance(payload, dict):
        return []

    skills = payload.get("skills")
    if not isinstance(skills, dict):
        return []

    observations: list[CapabilityObservation] = []
    for skill_name, raw_skill in sorted(skills.items()):
        if not isinstance(raw_skill, dict):
            continue
        observations.append(
            CapabilityObservation(
                id=capability_id(CapabilityKind.SKILL, str(skill_name)),
                kind=CapabilityKind.SKILL,
                name=str(skill_name),
                reasons=["Skill is recorded in the lockfile."],
                source=Evidence(
                    source_type="skill_lock",
                    source_path=str(lock_path),
                    confidence=ConfidenceLevel.MEDIUM,
                    facts=sanitize_data(raw_skill),
                ),
            )
        )

    return observations
