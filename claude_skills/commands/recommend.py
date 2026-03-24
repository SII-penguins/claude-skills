from __future__ import annotations

import typer

from ..inventory import build_inventory
from ..models import CapabilityKind
from ..output import print_json, render_recommendations_table
from ..recommendation import recommend_capabilities



def recommend_command(
    query: str = typer.Argument(..., help="Natural-language task or capability question."),
    kind: str = typer.Option("", "--kind", help="Filter recommendations by capability kind."),
    top: int = typer.Option(5, "--top", min=1, help="Maximum number of recommendations to return."),
    callable_first: bool = typer.Option(
        False,
        "--callable-first",
        help="Further prioritize capabilities that are callable right now.",
    ),
    json_output: bool = typer.Option(False, "--json", help="Emit JSON instead of rich tables."),
) -> None:
    kind_filter = _parse_kind(kind)
    report = build_inventory()
    recommendations = recommend_capabilities(
        report.capabilities,
        query,
        kind=kind_filter,
        top=top,
        callable_first=callable_first,
    )

    if json_output:
        print_json(
            {
                "query": query,
                "kind": kind_filter.value if kind_filter else None,
                "top": top,
                "callable_first": callable_first,
                "recommendations": [recommendation.model_dump(mode="json") for recommendation in recommendations],
            }
        )
        return

    render_recommendations_table(recommendations, query=query)



def _parse_kind(kind: str) -> CapabilityKind | None:
    if not kind:
        return None
    try:
        return CapabilityKind(kind)
    except ValueError as error:
        raise typer.BadParameter("kind must be one of: skill, plugin, mcp_server, tool") from error
