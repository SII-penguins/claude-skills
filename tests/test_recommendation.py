from __future__ import annotations

import json

from typer.testing import CliRunner

from claude_skills.categorizer import CATEGORY_DOCUMENTS, CATEGORY_MCP
from claude_skills.main import app
from claude_skills.models import (
    Availability,
    Capability,
    CapabilityKind,
    ConfidenceLevel,
    Evidence,
    InventoryReport,
    Relationship,
    RelationshipType,
)
from claude_skills.recommendation import recommend_capabilities

runner = CliRunner()



def make_capability(
    *,
    name: str,
    kind: CapabilityKind,
    description: str,
    category: str,
    availability: Availability,
    confidence: ConfidenceLevel,
    callable_now: bool,
    relationships: list[Relationship] | None = None,
    source_facts: dict | None = None,
) -> Capability:
    return Capability(
        id=f"{kind.value}:{name}",
        kind=kind,
        name=name,
        description=description,
        category=category,
        installed_locally=availability in {Availability.ENABLED, Availability.INSTALLED, Availability.BUILTIN},
        enabled=availability in {Availability.ENABLED, Availability.BUILTIN},
        callable_now=callable_now,
        availability=availability,
        confidence=confidence,
        relationships=relationships or [],
        sources=[
            Evidence(
                source_type="test",
                confidence=confidence,
                facts=source_facts or {},
            )
        ],
    )



def test_pdf_query_prioritizes_pdf_skill() -> None:
    pdf = make_capability(
        name="pdf",
        kind=CapabilityKind.SKILL,
        description="Inspect PDF files and extract tables from documents.",
        category=CATEGORY_DOCUMENTS,
        availability=Availability.ENABLED,
        confidence=ConfidenceLevel.HIGH,
        callable_now=True,
    )
    xlsx = make_capability(
        name="xlsx",
        kind=CapabilityKind.SKILL,
        description="Create and analyze spreadsheets.",
        category=CATEGORY_DOCUMENTS,
        availability=Availability.ENABLED,
        confidence=ConfidenceLevel.HIGH,
        callable_now=True,
    )
    read_tool = make_capability(
        name="Read",
        kind=CapabilityKind.TOOL,
        description="Reads local files including text, images, PDFs, and notebooks.",
        category="开发辅助 / 工作流",
        availability=Availability.BUILTIN,
        confidence=ConfidenceLevel.HIGH,
        callable_now=True,
    )

    recommendations = recommend_capabilities(
        [read_tool, xlsx, pdf],
        "I need to inspect a PDF and extract tables",
        top=3,
    )

    assert recommendations[0].capability.name == "pdf"
    assert any("pdf" in reason.casefold() for reason in recommendations[0].match_reasons)



def test_github_query_recommends_github_and_explains_unavailability() -> None:
    github = make_capability(
        name="github",
        kind=CapabilityKind.MCP_SERVER,
        description="Official GitHub MCP server for repositories, issues, and pull requests.",
        category=CATEGORY_MCP,
        availability=Availability.MARKETPLACE_ONLY,
        confidence=ConfidenceLevel.LOW,
        callable_now=False,
    )
    slack = make_capability(
        name="slack",
        kind=CapabilityKind.MCP_SERVER,
        description="Slack MCP server for team messaging.",
        category=CATEGORY_MCP,
        availability=Availability.ENABLED,
        confidence=ConfidenceLevel.HIGH,
        callable_now=True,
    )

    recommendations = recommend_capabilities(
        [slack, github],
        "why can't I use github right now",
        top=2,
    )

    assert recommendations[0].capability.name == "github"
    assert "not installed locally" in recommendations[0].readiness_summary.casefold()



def test_marketplace_only_is_ranked_below_callable_match() -> None:
    callable_xlsx = make_capability(
        name="xlsx",
        kind=CapabilityKind.SKILL,
        description="Work with spreadsheets, worksheets, and tables.",
        category=CATEGORY_DOCUMENTS,
        availability=Availability.ENABLED,
        confidence=ConfidenceLevel.HIGH,
        callable_now=True,
    )
    marketplace_plugin = make_capability(
        name="spreadsheet-suite",
        kind=CapabilityKind.PLUGIN,
        description="Spreadsheet and table workflows for Excel-style documents.",
        category=CATEGORY_DOCUMENTS,
        availability=Availability.MARKETPLACE_ONLY,
        confidence=ConfidenceLevel.LOW,
        callable_now=False,
    )

    recommendations = recommend_capabilities(
        [marketplace_plugin, callable_xlsx],
        "what can I use for spreadsheets",
        top=2,
    )

    assert [item.capability.name for item in recommendations] == ["xlsx", "spreadsheet-suite"]



def test_callable_high_confidence_capability_is_prioritized() -> None:
    medium_ready = make_capability(
        name="pdf-medium",
        kind=CapabilityKind.SKILL,
        description="PDF processing workflows.",
        category=CATEGORY_DOCUMENTS,
        availability=Availability.INSTALLED,
        confidence=ConfidenceLevel.MEDIUM,
        callable_now=True,
    )
    high_ready = make_capability(
        name="pdf-high",
        kind=CapabilityKind.SKILL,
        description="PDF processing workflows.",
        category=CATEGORY_DOCUMENTS,
        availability=Availability.ENABLED,
        confidence=ConfidenceLevel.HIGH,
        callable_now=True,
    )

    recommendations = recommend_capabilities([medium_ready, high_ready], "pdf", top=2)

    assert [item.capability.name for item in recommendations] == ["pdf-high", "pdf-medium"]



def test_spreadsheet_query_prioritizes_xlsx_skill_over_builtin_read() -> None:
    xlsx = make_capability(
        name="xlsx",
        kind=CapabilityKind.SKILL,
        description="Create and edit spreadsheet files, tables, and Excel workbooks.",
        category=CATEGORY_DOCUMENTS,
        availability=Availability.ENABLED,
        confidence=ConfidenceLevel.HIGH,
        callable_now=True,
    )
    read_tool = make_capability(
        name="Read",
        kind=CapabilityKind.TOOL,
        description="Reads local files including text, images, PDFs, and notebooks.",
        category="开发辅助 / 工作流",
        availability=Availability.BUILTIN,
        confidence=ConfidenceLevel.HIGH,
        callable_now=True,
    )

    recommendations = recommend_capabilities(
        [read_tool, xlsx],
        "what can I use for spreadsheets",
        top=2,
    )

    assert recommendations[0].capability.name == "xlsx"



def test_provider_plugin_name_contributes_to_matching() -> None:
    docx = make_capability(
        name="docx",
        kind=CapabilityKind.SKILL,
        description="Create and inspect Word documents.",
        category=CATEGORY_DOCUMENTS,
        availability=Availability.ENABLED,
        confidence=ConfidenceLevel.HIGH,
        callable_now=True,
        relationships=[
            Relationship(
                type=RelationshipType.PROVIDED_BY.value,
                target_id="plugin:document-skills@anthropic-agent-skills",
                target_name="document-skills@anthropic-agent-skills",
            )
        ],
    )
    github = make_capability(
        name="github",
        kind=CapabilityKind.MCP_SERVER,
        description="GitHub MCP server.",
        category=CATEGORY_MCP,
        availability=Availability.ENABLED,
        confidence=ConfidenceLevel.HIGH,
        callable_now=True,
    )

    recommendations = recommend_capabilities(
        [github, docx],
        "what is available in the document-skills plugin",
        top=2,
    )

    assert recommendations[0].capability.name == "docx"
    assert any("matching plugin" in reason.casefold() for reason in recommendations[0].match_reasons)



def test_recommend_command_supports_json_output(monkeypatch) -> None:
    github = make_capability(
        name="github",
        kind=CapabilityKind.MCP_SERVER,
        description="Official GitHub MCP server.",
        category=CATEGORY_MCP,
        availability=Availability.MARKETPLACE_ONLY,
        confidence=ConfidenceLevel.LOW,
        callable_now=False,
    )

    def fake_build_inventory() -> InventoryReport:
        return InventoryReport(capabilities=[github], issues=[])

    monkeypatch.setattr("claude_skills.commands.recommend.build_inventory", fake_build_inventory)

    result = runner.invoke(app, ["recommend", "what can I use for github", "--json"])

    assert result.exit_code == 0, result.stdout
    payload = json.loads(result.stdout)
    assert payload["query"] == "what can I use for github"
    assert payload["recommendations"][0]["capability"]["name"] == "github"
