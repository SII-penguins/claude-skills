from __future__ import annotations

from pathlib import Path

import typer

from ..inventory import build_inventory
from ..output import print_json
from ..utils import pretty_json



def export_command(output: str = typer.Argument("", help="Optional file path for JSON export.")) -> None:
    report = build_inventory()
    payload = report.model_dump(mode="json")
    if not output:
        print_json(payload)
        return

    Path(output).write_text(pretty_json(payload) + "\n", encoding="utf-8")
