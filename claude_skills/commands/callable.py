from __future__ import annotations

import typer

from ..confidence import ConfidenceLevel
from ..inventory import build_inventory
from ..output import print_json, render_capabilities_table



def callable_command(json_output: bool = typer.Option(False, "--json", help="Emit JSON instead of rich tables.")) -> None:
    report = build_inventory()
    capabilities = [
        capability
        for capability in report.capabilities
        if capability.callable_now and capability.confidence in {ConfidenceLevel.HIGH, ConfidenceLevel.MEDIUM}
    ]

    if json_output:
        print_json([capability.model_dump(mode="json") for capability in capabilities])
        return
    render_capabilities_table(capabilities, title="Likely callable now")
