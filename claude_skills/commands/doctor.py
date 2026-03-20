from __future__ import annotations

import typer

from ..inventory import build_inventory
from ..output import print_json, render_issues



def doctor_command(json_output: bool = typer.Option(False, "--json", help="Emit JSON instead of rich tables.")) -> None:
    report = build_inventory()
    if json_output:
        print_json([issue.model_dump(mode="json") for issue in report.issues])
        return
    render_issues(report.issues)
