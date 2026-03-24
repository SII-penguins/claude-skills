from __future__ import annotations

from collections import Counter
from typing import Any
import sys

from rich.console import Console
from rich.table import Table

from .models import Capability, InventoryIssue, InventoryReport
from .recommendation import CapabilityRecommendation
from .utils import pretty_json

console = Console()


def render_scan_summary(report: InventoryReport) -> None:
    kind_counts = Counter(capability.kind.value for capability in report.capabilities)
    availability_counts = Counter(capability.availability.value for capability in report.capabilities)
    confidence_counts = Counter(capability.confidence.value for capability in report.capabilities)

    console.print(f"Capabilities: {len(report.capabilities)}")
    console.print(f"Issues: {len(report.issues)}")

    kind_table = Table(title="By kind")
    kind_table.add_column("Kind")
    kind_table.add_column("Count", justify="right")
    for kind, count in sorted(kind_counts.items()):
        kind_table.add_row(kind, str(count))
    console.print(kind_table)

    availability_table = Table(title="By availability")
    availability_table.add_column("Availability")
    availability_table.add_column("Count", justify="right")
    for availability, count in sorted(availability_counts.items()):
        availability_table.add_row(availability, str(count))
    console.print(availability_table)

    confidence_table = Table(title="By confidence")
    confidence_table.add_column("Confidence")
    confidence_table.add_column("Count", justify="right")
    for confidence, count in sorted(confidence_counts.items()):
        confidence_table.add_row(confidence, str(count))
    console.print(confidence_table)


def render_capabilities_table(capabilities: list[Capability], *, title: str | None = None) -> None:
    table = Table(title=title)
    table.add_column("Name")
    table.add_column("Kind")
    table.add_column("Installed")
    table.add_column("Enabled")
    table.add_column("Callable")
    table.add_column("Availability")
    table.add_column("Confidence")
    table.add_column("Category")
    table.add_column("Plugin")

    for capability in capabilities:
        providers = ", ".join(capability.provider_plugins())
        table.add_row(
            capability.name,
            capability.kind.value,
            _format_bool(capability.installed_locally),
            _format_bool(capability.enabled),
            _format_bool(capability.callable_now),
            capability.availability.value,
            capability.confidence.value,
            capability.category or "",
            providers,
        )

    console.print(table)


def render_recommendations_table(recommendations: list[CapabilityRecommendation], *, query: str) -> None:
    if not recommendations:
        console.print(f"No relevant capabilities found for: {query}")
        return

    table = Table(title=f'Recommendations for "{query}"')
    table.add_column("Name")
    table.add_column("Kind")
    table.add_column("Availability")
    table.add_column("Confidence")
    table.add_column("Score", justify="right")
    table.add_column("Why recommended")

    for recommendation in recommendations:
        why_lines = [*recommendation.match_reasons[:2], recommendation.readiness_summary]
        table.add_row(
            recommendation.capability.name,
            recommendation.capability.kind.value,
            recommendation.capability.availability.value,
            recommendation.capability.confidence.value,
            str(recommendation.score),
            "\n".join(why_lines),
        )

    console.print(table)



def render_capability_details(capability: Capability, related: list[Capability]) -> None:
    summary = Table(title=capability.name)
    summary.add_column("Field")
    summary.add_column("Value")
    summary.add_row("ID", capability.id)
    summary.add_row("Kind", capability.kind.value)
    summary.add_row("Description", capability.description or "")
    summary.add_row("Category", capability.category or "")
    summary.add_row("Installed", _format_bool(capability.installed_locally))
    summary.add_row("Enabled", _format_bool(capability.enabled))
    summary.add_row("Callable", _format_bool(capability.callable_now))
    summary.add_row("Availability", capability.availability.value)
    summary.add_row("Confidence", capability.confidence.value)
    summary.add_row("Marketplace visible", _format_bool(capability.marketplace_visible))
    summary.add_row("Builtin", _format_bool(capability.builtin))
    summary.add_row("Reasons", "\n".join(capability.reasons) or "")
    console.print(summary)

    if capability.relationships:
        relationship_table = Table(title="Relationships")
        relationship_table.add_column("Type")
        relationship_table.add_column("Target")
        relationship_table.add_column("Details")
        for relationship in capability.relationships:
            relationship_table.add_row(
                relationship.type,
                relationship.target_name or relationship.target_id,
                pretty_json(relationship.details) if relationship.details else "",
            )
        console.print(relationship_table)

    if related:
        related_table = Table(title="Related capabilities")
        related_table.add_column("Name")
        related_table.add_column("Kind")
        related_table.add_column("Relationship")
        for item in related:
            relationship_types = ", ".join(
                relationship.type
                for relationship in item.relationships
                if relationship.target_id == capability.id
            )
            related_table.add_row(item.name, item.kind.value, relationship_types)
        console.print(related_table)

    evidence_table = Table(title="Evidence")
    evidence_table.add_column("Source")
    evidence_table.add_column("Path")
    evidence_table.add_column("Confidence")
    evidence_table.add_column("Facts")
    for source in capability.sources:
        evidence_table.add_row(
            source.source_type,
            source.source_path or "",
            source.confidence.value,
            pretty_json(source.facts) if source.facts else "",
        )
    console.print(evidence_table)


def render_issues(issues: list[InventoryIssue]) -> None:
    if not issues:
        console.print("No issues found.")
        return

    table = Table(title="Doctor")
    table.add_column("Severity")
    table.add_column("Code")
    table.add_column("Capability")
    table.add_column("Message")
    table.add_column("Details")

    for issue in issues:
        table.add_row(
            issue.severity.value,
            issue.code,
            issue.capability_name or issue.capability_id or "",
            issue.message,
            pretty_json(issue.details) if issue.details else "",
        )

    console.print(table)


def print_json(payload: Any) -> None:
    sys.stdout.write(pretty_json(payload) + "\n")


def _format_bool(value: bool | None) -> str:
    if value is True:
        return "yes"
    if value is False:
        return "no"
    return "n/a"
