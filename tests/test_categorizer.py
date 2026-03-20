from __future__ import annotations

from claude_skills.categorizer import CATEGORY_DEV, CATEGORY_DOCUMENTS, CATEGORY_FINANCE, CATEGORY_MCP, categorize_text
from claude_skills.models import CapabilityKind



def test_document_skill_category() -> None:
    assert categorize_text("pdf", "Process PDF documents", CapabilityKind.SKILL) == CATEGORY_DOCUMENTS



def test_marketplace_server_category() -> None:
    assert categorize_text("github", "Official GitHub MCP server", CapabilityKind.MCP_SERVER) == CATEGORY_MCP



def test_marketing_skill_category() -> None:
    assert categorize_text("copywriting", "Marketing copywriting workflows", CapabilityKind.SKILL) == CATEGORY_FINANCE



def test_builtin_tool_category() -> None:
    assert categorize_text("Bash", "Runs terminal commands", CapabilityKind.TOOL) == CATEGORY_DEV
