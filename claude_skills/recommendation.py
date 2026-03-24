from __future__ import annotations

import re
from collections.abc import Iterable

from pydantic import BaseModel, Field

from .categorizer import CATEGORY_DATA, CATEGORY_DEV, CATEGORY_DOCUMENTS, CATEGORY_FINANCE, CATEGORY_MCP, CATEGORY_REASONING
from .models import Availability, Capability, CapabilityKind, ConfidenceLevel
from .utils import unique_strings

STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "can",
    "for",
    "from",
    "help",
    "how",
    "i",
    "inspect",
    "is",
    "it",
    "me",
    "my",
    "need",
    "now",
    "of",
    "or",
    "right",
    "something",
    "that",
    "the",
    "these",
    "this",
    "to",
    "use",
    "what",
    "which",
    "why",
    "with",
}
TOKEN_RE = re.compile(r"[a-z0-9]+")
DIAGNOSTIC_PATTERNS = (
    "why can't",
    "why cant",
    "cannot use",
    "can't use",
    "cant use",
    "not available",
    "why is",
    "why isn't",
    "why isnt",
    "diagnose",
    "unavailable",
)

QUERY_ALIASES = {
    "doc": {"document", "documents"},
    "docs": {"document", "documents"},
    "excel": {"xlsx", "spreadsheet", "spreadsheets"},
    "github": {"git", "issue", "issues", "pr", "pull", "repository", "repo"},
    "mcp": {"integration", "server", "servers"},
    "plugin": {"plugins"},
    "plugins": {"plugin"},
    "sheet": {"spreadsheet", "spreadsheets", "xlsx"},
    "sheets": {"spreadsheet", "spreadsheets", "xlsx"},
    "spreadsheet": {"excel", "spreadsheets", "xlsx"},
    "spreadsheets": {"excel", "spreadsheet", "xlsx"},
    "tool": {"tools"},
    "tools": {"tool"},
}
CATEGORY_QUERY_KEYWORDS = {
    CATEGORY_DOCUMENTS: {
        "brand",
        "canvas",
        "content",
        "doc",
        "docx",
        "document",
        "documents",
        "excel",
        "pdf",
        "pptx",
        "presentation",
        "presentations",
        "powerpoint",
        "slide",
        "slides",
        "spreadsheet",
        "spreadsheets",
        "table",
        "tables",
        "word",
        "workbook",
        "workbooks",
        "xlsx",
    },
    CATEGORY_MCP: {
        "api",
        "external",
        "github",
        "gitlab",
        "integration",
        "integrations",
        "linear",
        "mcp",
        "playwright",
        "server",
        "servers",
        "slack",
        "stripe",
        "supabase",
    },
    CATEGORY_DEV: {
        "agent",
        "agents",
        "automation",
        "bash",
        "cli",
        "code",
        "command",
        "commands",
        "commit",
        "debug",
        "developer",
        "hook",
        "hooks",
        "plugin",
        "plugins",
        "review",
        "sdk",
        "terminal",
        "test",
        "testing",
        "tool",
        "tools",
        "workflow",
        "workflows",
    },
    CATEGORY_DATA: {
        "data",
        "ml",
        "model",
        "models",
        "numpy",
        "pandas",
        "statistics",
        "training",
    },
    CATEGORY_FINANCE: {
        "accounting",
        "business",
        "commercial",
        "finance",
        "financial",
        "marketing",
        "revenue",
        "sales",
    },
    CATEGORY_REASONING: {
        "analysis",
        "debugging",
        "decision",
        "plan",
        "planning",
        "reasoning",
        "systematic",
    },
}
KIND_QUERY_KEYWORDS = {
    CapabilityKind.SKILL: {"skill", "skills"},
    CapabilityKind.PLUGIN: {"plugin", "plugins"},
    CapabilityKind.MCP_SERVER: {"integration", "integrations", "mcp", "server", "servers"},
    CapabilityKind.TOOL: {"builtin", "tool", "tools"},
}


class CapabilityRecommendation(BaseModel):
    capability: Capability
    score: int
    match_reasons: list[str] = Field(default_factory=list)
    readiness_summary: str



def recommend_capabilities(
    capabilities: list[Capability],
    query: str,
    *,
    kind: CapabilityKind | None = None,
    top: int = 5,
    callable_first: bool = False,
) -> list[CapabilityRecommendation]:
    query_text = _normalize_text(query)
    raw_query_tokens = _tokenize(query)
    expanded_query_tokens = _tokenize(query, expand_aliases=True)
    diagnostic_query = _is_diagnostic_query(query_text)

    recommendations: list[CapabilityRecommendation] = []
    for capability in capabilities:
        if kind is not None and capability.kind != kind:
            continue
        recommendation = _recommend_capability(
            capability,
            query_text=query_text,
            raw_query_tokens=raw_query_tokens,
            expanded_query_tokens=expanded_query_tokens,
            diagnostic_query=diagnostic_query,
            callable_first=callable_first,
        )
        if recommendation is not None:
            recommendations.append(recommendation)

    recommendations.sort(
        key=lambda recommendation: (
            -recommendation.score,
            -int(recommendation.capability.callable_now),
            -_confidence_weight(recommendation.capability.confidence),
            recommendation.capability.sort_key(),
        )
    )
    return recommendations[:top]



def _recommend_capability(
    capability: Capability,
    *,
    query_text: str,
    raw_query_tokens: set[str],
    expanded_query_tokens: set[str],
    diagnostic_query: bool,
    callable_first: bool,
) -> CapabilityRecommendation | None:
    relevance_score = 0
    match_reasons: list[str] = []

    name_text = _normalize_text(capability.name)
    suffix_text = _normalize_text(capability.id.split(":", 1)[1] if ":" in capability.id else capability.id)
    provider_names = capability.provider_plugins()
    provider_text = " ".join(provider_names)

    name_tokens = _tokenize(capability.name)
    description_tokens = _tokenize(capability.description or "")
    provider_tokens = _tokenize(provider_text)

    if query_text and (query_text == name_text or query_text == suffix_text):
        relevance_score += 100
        match_reasons.append(f"Exact name match for `{capability.name}`.")
    elif len(name_text) >= 3 and _contains_phrase(query_text, name_text):
        relevance_score += 80
        match_reasons.append(f"The query mentions `{capability.name}` directly.")
    elif len(suffix_text) >= 3 and _contains_phrase(query_text, suffix_text):
        relevance_score += 60
        match_reasons.append(f"The query mentions `{suffix_text}` directly.")

    name_hits = sorted(raw_query_tokens & name_tokens)
    if name_hits:
        relevance_score += 16 * len(name_hits)
        match_reasons.append(f"Name matches query terms: {', '.join(name_hits)}.")

    alias_name_hits = sorted((expanded_query_tokens - raw_query_tokens) & name_tokens)
    if alias_name_hits:
        relevance_score += 12 * len(alias_name_hits)
        match_reasons.append(f"Name matches query synonyms: {', '.join(alias_name_hits)}.")

    description_hits = sorted(expanded_query_tokens & description_tokens)
    if description_hits:
        relevance_score += 8 * len(description_hits)
        match_reasons.append(f"Description matches query terms: {', '.join(description_hits)}.")

    provider_hits = sorted(expanded_query_tokens & provider_tokens)
    if provider_hits and provider_names:
        relevance_score += 10 * len(provider_hits)
        providers = ", ".join(provider_names)
        match_reasons.append(f"Provided by a matching plugin: {providers}.")

    direct_query_terms = {query_text, *raw_query_tokens}
    if capability.name.casefold() in direct_query_terms:
        relevance_score += 60
        match_reasons.append(f"The query explicitly asks about `{capability.name}`.")

    category_keywords = CATEGORY_QUERY_KEYWORDS.get(capability.category or "", set())
    category_hits = sorted(expanded_query_tokens & category_keywords)
    if category_hits:
        relevance_score += 18
        if capability.category:
            match_reasons.append(f"Fits the `{capability.category}` category implied by the query.")

    kind_hits = sorted(raw_query_tokens & KIND_QUERY_KEYWORDS[capability.kind])
    if kind_hits:
        relevance_score += 6
        match_reasons.append(f"The query explicitly mentions {capability.kind.value.replace('_', ' ')} concepts.")

    if diagnostic_query and (
        name_hits
        or provider_hits
        or query_text == name_text
        or query_text == suffix_text
        or capability.name.casefold() in direct_query_terms
    ):
        relevance_score += 22
        match_reasons.append("Useful for diagnosing current availability on this machine.")

    if relevance_score <= 0:
        return None

    readiness_score = _readiness_score(capability, callable_first=callable_first)
    score = relevance_score + readiness_score + _kind_specificity_bonus(capability.kind)
    return CapabilityRecommendation(
        capability=capability,
        score=score,
        match_reasons=unique_strings(match_reasons),
        readiness_summary=_readiness_summary(capability),
    )



def _readiness_score(capability: Capability, *, callable_first: bool) -> int:
    score = 0

    if capability.callable_now:
        score += 28
    if callable_first and capability.callable_now:
        score += 10

    if capability.availability == Availability.ENABLED:
        score += 14
    elif capability.availability == Availability.BUILTIN:
        score += 12
    elif capability.availability == Availability.INSTALLED:
        score += 6
    elif capability.availability == Availability.MARKETPLACE_ONLY:
        score -= 12

    score += _confidence_weight(capability.confidence)

    missing_env = _collect_fact_values(capability, "missing_env_vars")
    if missing_env:
        score -= 10

    return score



def _readiness_summary(capability: Capability) -> str:
    missing_env = sorted(_collect_fact_values(capability, "missing_env_vars"))
    if capability.callable_now:
        if capability.builtin or capability.availability == Availability.BUILTIN:
            return "Ready now: builtin capability with high confidence."
        if capability.availability == Availability.ENABLED:
            return f"Ready now: enabled on this machine with {capability.confidence.value} confidence."
        if capability.availability == Availability.INSTALLED:
            return f"Probably ready now: installed locally with {capability.confidence.value} confidence."
        return f"Likely ready now with {capability.confidence.value} confidence."

    if capability.availability == Availability.MARKETPLACE_ONLY:
        if missing_env:
            return (
                "Not ready now: visible in marketplace metadata but not installed locally. "
                "Metadata also references missing environment variables: "
                + ", ".join(missing_env)
                + "."
            )
        return "Not ready now: visible in marketplace metadata but not installed locally."
    if capability.availability == Availability.INSTALLED and missing_env:
        return "Not ready now: installed locally but missing environment variables: " + ", ".join(missing_env) + "."
    if missing_env:
        return "Not ready now: missing environment variables: " + ", ".join(missing_env) + "."
    if capability.availability == Availability.INSTALLED:
        return "Not ready now: installed locally, but it is not currently enabled or callable."
    if capability.availability == Availability.UNKNOWN:
        return "Readiness is unclear: local evidence is incomplete."
    return f"Not ready now: current availability is `{capability.availability.value}`."



def _kind_specificity_bonus(kind: CapabilityKind) -> int:
    if kind == CapabilityKind.SKILL:
        return 4
    if kind == CapabilityKind.MCP_SERVER:
        return 3
    if kind == CapabilityKind.TOOL:
        return 2
    return 0



def _confidence_weight(confidence: ConfidenceLevel) -> int:
    if confidence == ConfidenceLevel.HIGH:
        return 10
    if confidence == ConfidenceLevel.MEDIUM:
        return 5
    return 0



def _normalize_text(text: str) -> str:
    return " ".join(text.casefold().replace("'", "").split())



def _contains_phrase(haystack: str, needle: str) -> bool:
    if not needle:
        return False
    pattern = rf"(?:^|\s){re.escape(needle)}(?:$|\s)"
    return re.search(pattern, haystack) is not None



def _tokenize(text: str, *, expand_aliases: bool = False) -> set[str]:
    tokens: set[str] = set()
    for raw_token in TOKEN_RE.findall(_normalize_text(text)):
        for token in _token_variants(raw_token, expand_aliases=expand_aliases):
            if len(token) < 2:
                continue
            if token in STOPWORDS:
                continue
            tokens.add(token)
    return tokens



def _token_variants(token: str, *, expand_aliases: bool = False) -> set[str]:
    variants = {token.strip("@._+-") or token}
    normalized = token.strip("@._+-")
    if normalized:
        variants.add(normalized)

    if normalized.endswith("ies") and len(normalized) > 4:
        variants.add(normalized[:-3] + "y")
    if normalized.endswith("es") and len(normalized) > 4:
        variants.add(normalized[:-2])
    if normalized.endswith("s") and len(normalized) > 3 and not normalized.endswith("ss"):
        variants.add(normalized[:-1])

    if expand_aliases:
        for value in list(variants):
            variants.update(QUERY_ALIASES.get(value, set()))

    return {value for value in variants if value}



def _is_diagnostic_query(query_text: str) -> bool:
    return any(pattern in query_text for pattern in DIAGNOSTIC_PATTERNS)



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
