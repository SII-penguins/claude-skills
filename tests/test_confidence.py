from __future__ import annotations

from claude_skills.confidence import finalize_capabilities
from claude_skills.models import Capability, CapabilityKind, ConfidenceLevel, Evidence, Relationship, RelationshipType



def test_local_skill_without_session_evidence_is_medium_confidence_callable() -> None:
    capability = Capability(
        id="skill:local-demo",
        kind=CapabilityKind.SKILL,
        name="local-demo",
        installed_locally=True,
        sources=[
            Evidence(
                source_type="local_skill",
                confidence=ConfidenceLevel.MEDIUM,
                facts={"manifest_complete": True},
            )
        ],
    )

    finalized = finalize_capabilities([capability])[0]

    assert finalized.callable_now is True
    assert finalized.confidence.value == "medium"
    assert finalized.availability.value == "installed"



def test_installed_enabled_plugin_skill_is_high_confidence_callable() -> None:
    plugin = Capability(
        id="plugin:bundle@market",
        kind=CapabilityKind.PLUGIN,
        name="bundle@market",
        installed_locally=True,
        enabled=True,
        sources=[Evidence(source_type="installed_plugin", confidence=ConfidenceLevel.HIGH)],
    )
    skill = Capability(
        id="skill:pdf",
        kind=CapabilityKind.SKILL,
        name="pdf",
        installed_locally=True,
        relationships=[
            Relationship(
                type=RelationshipType.PROVIDED_BY.value,
                target_id="plugin:bundle@market",
                target_name="bundle@market",
            )
        ],
        sources=[
            Evidence(
                source_type="plugin_cache_skill",
                confidence=ConfidenceLevel.HIGH,
                facts={"manifest_complete": True},
            )
        ],
    )

    finalized = {capability.id: capability for capability in finalize_capabilities([plugin, skill])}

    assert finalized["skill:pdf"].callable_now is True
    assert finalized["skill:pdf"].confidence.value == "high"
    assert finalized["skill:pdf"].availability.value == "enabled"



def test_marketplace_mcp_is_low_confidence_not_callable() -> None:
    capability = Capability(
        id="mcp_server:github",
        kind=CapabilityKind.MCP_SERVER,
        name="github",
        marketplace_visible=True,
        sources=[Evidence(source_type="marketplace_mcp", confidence=ConfidenceLevel.LOW)],
    )

    finalized = finalize_capabilities([capability])[0]

    assert finalized.callable_now is False
    assert finalized.confidence.value == "low"
    assert finalized.availability.value == "marketplace_only"
