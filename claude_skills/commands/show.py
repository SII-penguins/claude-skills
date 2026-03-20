from __future__ import annotations

import typer

from ..inventory import build_inventory, find_capability, related_capabilities
from ..output import print_json, render_capability_details



def show_command(name: str, json_output: bool = typer.Option(False, "--json", help="Emit JSON instead of rich tables.")) -> None:
    report = build_inventory()
    capability = find_capability(report.capabilities, name)
    if capability is None:
        raise typer.Exit(code=1)

    related = related_capabilities(report.capabilities, capability.id)
    if json_output:
        print_json(
            {
                "capability": capability.model_dump(mode="json"),
                "related": [item.model_dump(mode="json") for item in related],
            }
        )
        return
    render_capability_details(capability, related)
