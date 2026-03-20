from __future__ import annotations

from claude_skills.inventory import build_inventory_from_observations, filter_capabilities, find_capability
from claude_skills.models import CapabilityKind, CapabilityObservation, ConfidenceLevel, Evidence, Relationship, RelationshipType, capability_id



def test_merge_combines_plugin_and_skill_relationships() -> None:
    plugin_observation = CapabilityObservation(
        id="plugin:demo@market",
        kind=CapabilityKind.PLUGIN,
        name="demo@market",
        installed_locally=True,
        enabled=True,
        source=Evidence(source_type="installed_plugin", confidence=ConfidenceLevel.HIGH),
    )
    skill_observation = CapabilityObservation(
        id=capability_id(CapabilityKind.SKILL, "demo-skill"),
        kind=CapabilityKind.SKILL,
        name="demo-skill",
        installed_locally=True,
        relationships=[
            Relationship(
                type=RelationshipType.PROVIDED_BY.value,
                target_id="plugin:demo@market",
                target_name="demo@market",
            )
        ],
        source=Evidence(
            source_type="plugin_cache_skill",
            confidence=ConfidenceLevel.HIGH,
            facts={"manifest_complete": True},
        ),
    )

    report = build_inventory_from_observations([plugin_observation, skill_observation])
    capability = find_capability(report.capabilities, "demo-skill")

    assert capability is not None
    assert capability.callable_now is True
    assert capability.confidence.value == "high"
    assert capability.provider_plugins() == ["demo@market"]



def test_filter_capabilities_by_plugin() -> None:
    plugin_observation = CapabilityObservation(
        id="plugin:demo@market",
        kind=CapabilityKind.PLUGIN,
        name="demo@market",
        installed_locally=True,
        enabled=True,
        source=Evidence(source_type="installed_plugin", confidence=ConfidenceLevel.HIGH),
    )
    skill_observation = CapabilityObservation(
        id=capability_id(CapabilityKind.SKILL, "demo-skill"),
        kind=CapabilityKind.SKILL,
        name="demo-skill",
        installed_locally=True,
        relationships=[
            Relationship(
                type=RelationshipType.PROVIDED_BY.value,
                target_id="plugin:demo@market",
                target_name="demo@market",
            )
        ],
        source=Evidence(
            source_type="plugin_cache_skill",
            confidence=ConfidenceLevel.HIGH,
            facts={"manifest_complete": True},
        ),
    )

    report = build_inventory_from_observations([plugin_observation, skill_observation])
    filtered = filter_capabilities(report.capabilities, plugin="demo@market")

    assert [capability.name for capability in filtered] == ["demo-skill"]
