from __future__ import annotations

import typer

from .commands.callable import callable_command
from .commands.doctor import doctor_command
from .commands.export import export_command
from .commands.list_cmd import list_command
from .commands.recommend import recommend_command
from .commands.scan import scan_command
from .commands.show import show_command

app = typer.Typer(help="Claude Skills inventories and explains Claude-related capabilities on the local machine.")

app.command("scan")(scan_command)
app.command("list")(list_command)
app.command("recommend")(recommend_command)
app.command("show")(show_command)
app.command("callable")(callable_command)
app.command("doctor")(doctor_command)
app.command("export")(export_command)


if __name__ == "__main__":
    app()
