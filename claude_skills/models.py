from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class CapabilityKind(StrEnum):
    SKILL = "skill"
    PLUGIN = "plugin"
    MCP_SERVER = "mcp_server"
    TOOL = "tool"


class Availability(StrEnum):
    INSTALLED = "installed"
    ENABLED = "enabled"
    MARKETPLACE_ONLY = "marketplace_only"
    BUILTIN = "builtin"
    UNKNOWN = "unknown"


class ConfidenceLevel(StrEnum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class RelationshipType(StrEnum):
    PROVIDED_BY = "provided_by"
    EXPOSED_BY = "exposed_by"


class IssueSeverity(StrEnum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class Relationship(BaseModel):
    type: str
    target_id: str
    target_name: str | None = None
    details: dict[str, Any] = Field(default_factory=dict)


class Evidence(BaseModel):
    source_type: str
    source_path: str | None = None
    facts: dict[str, Any] = Field(default_factory=dict)
    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM


class CapabilityObservation(BaseModel):
    id: str
    kind: CapabilityKind
    name: str
    description: str | None = None
    category: str | None = None
    installed_locally: bool | None = None
    enabled: bool | None = None
    callable_now: bool | None = None
    marketplace_visible: bool | None = None
    builtin: bool | None = None
    reasons: list[str] = Field(default_factory=list)
    relationships: list[Relationship] = Field(default_factory=list)
    source: Evidence


class Capability(BaseModel):
    id: str
    kind: CapabilityKind
    name: str
    description: str | None = None
    category: str | None = None
    installed_locally: bool = False
    enabled: bool | None = None
    callable_now: bool = False
    availability: Availability = Availability.UNKNOWN
    confidence: ConfidenceLevel = ConfidenceLevel.LOW
    marketplace_visible: bool = False
    builtin: bool = False
    reasons: list[str] = Field(default_factory=list)
    relationships: list[Relationship] = Field(default_factory=list)
    sources: list[Evidence] = Field(default_factory=list)

    def provider_plugins(self) -> list[str]:
        providers: list[str] = []
        for relationship in self.relationships:
            if relationship.type == RelationshipType.PROVIDED_BY.value:
                providers.append(relationship.target_name or relationship.target_id.removeprefix("plugin:"))
        return providers

    def matches(self, query: str) -> bool:
        normalized = query.casefold()
        suffix = self.id.split(":", 1)[1].casefold() if ":" in self.id else self.id.casefold()
        return (
            self.id.casefold() == normalized
            or self.name.casefold() == normalized
            or suffix == normalized
        )

    def sort_key(self) -> tuple[str, str]:
        return self.kind.value, self.name.casefold()


class InventoryIssue(BaseModel):
    code: str
    severity: IssueSeverity
    message: str
    capability_id: str | None = None
    capability_name: str | None = None
    details: dict[str, Any] = Field(default_factory=dict)


class InventoryReport(BaseModel):
    capabilities: list[Capability]
    issues: list[InventoryIssue] = Field(default_factory=list)


def capability_id(kind: CapabilityKind, name: str) -> str:
    return f"{kind.value}:{name}"
