from __future__ import annotations

from .models import Capability, CapabilityKind

CATEGORY_DOCUMENTS = "文档与内容"
CATEGORY_DEV = "开发辅助 / 工作流"
CATEGORY_MCP = "MCP / 外部集成"
CATEGORY_DATA = "数据科学 / ML / 统计"
CATEGORY_BIO = "生物信息 / 医药 / 科研"
CATEGORY_CHEM = "化学 / 材料 / 药物"
CATEGORY_GEO = "地理空间 / 遥感"
CATEGORY_FINANCE = "金融 / 商业"
CATEGORY_REASONING = "通用决策 / 推理"
CATEGORY_OTHER = "其他"


CATEGORY_RULES: list[tuple[str, tuple[str, ...]]] = [
    (
        CATEGORY_DOCUMENTS,
        (
            "pdf",
            "docx",
            "pptx",
            "xlsx",
            "document",
            "word",
            "powerpoint",
            "spreadsheet",
            "slide",
            "presentation",
            "brand",
            "canvas",
            "content",
            "theme",
            "gif",
        ),
    ),
    (
        CATEGORY_MCP,
        (
            "mcp",
            "github",
            "gitlab",
            "slack",
            "stripe",
            "supabase",
            "linear",
            "firebase",
            "asana",
            "playwright",
            "serena",
            "context7",
            "integration",
            "external api",
        ),
    ),
    (
        CATEGORY_DATA,
        (
            "data science",
            "machine learning",
            "ml",
            "statistics",
            "statistical",
            "pandas",
            "numpy",
            "model training",
        ),
    ),
    (
        CATEGORY_BIO,
        (
            "biology",
            "bioinformatics",
            "genomics",
            "protein",
            "clinical",
            "medical",
            "pharma",
            "drug discovery",
        ),
    ),
    (
        CATEGORY_CHEM,
        (
            "chemistry",
            "chemical",
            "molecule",
            "molecular",
            "materials",
            "catalyst",
            "compound",
        ),
    ),
    (
        CATEGORY_GEO,
        (
            "geospatial",
            "remote sensing",
            "gis",
            "satellite",
            "map",
            "spatial",
            "raster",
        ),
    ),
    (
        CATEGORY_FINANCE,
        (
            "finance",
            "financial",
            "sales",
            "marketing",
            "business",
            "revenue",
            "accounting",
            "commercial",
        ),
    ),
    (
        CATEGORY_REASONING,
        (
            "reasoning",
            "decision",
            "systematic",
            "plan",
            "planning",
            "debugging",
            "analysis",
        ),
    ),
    (
        CATEGORY_DEV,
        (
            "frontend",
            "webapp",
            "workflow",
            "hook",
            "agent",
            "plugin",
            "sdk",
            "api",
            "review",
            "testing",
            "test",
            "code",
            "debug",
            "commit",
            "developer",
            "tool",
            "bash",
        ),
    ),
]


def categorize_text(name: str, description: str | None, kind: CapabilityKind) -> str:
    haystack = f"{name} {description or ''}".casefold()

    if kind == CapabilityKind.MCP_SERVER:
        return CATEGORY_MCP
    if kind == CapabilityKind.TOOL:
        return CATEGORY_DEV

    for category, keywords in CATEGORY_RULES:
        if any(keyword in haystack for keyword in keywords):
            return category

    return CATEGORY_OTHER


def categorize_capability(capability: Capability) -> str:
    return categorize_text(capability.name, capability.description, capability.kind)
