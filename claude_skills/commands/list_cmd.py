from __future__ import annotations

import typer

from ..inventory import build_inventory, filter_capabilities
from ..models import CapabilityKind
from ..output import print_json, render_capabilities_table



def list_command(
    kind: str = typer.Option("", "--kind", help="Filter by capability kind."),
    installed: bool = typer.Option(False, "--installed", help="Only show installed capabilities."),
    not_installed: bool = typer.Option(False, "--not-installed", help="Only show non-installed capabilities."),
    enabled: bool = typer.Option(False, "--enabled", help="Only show enabled capabilities."),
    disabled: bool = typer.Option(False, "--disabled", help="Only show disabled capabilities."),
    callable_now: bool = typer.Option(False, "--callable", help="Only show callable capabilities."),
    not_callable: bool = typer.Option(False, "--not-callable", help="Only show non-callable capabilities."),
    marketplace_only: bool = typer.Option(False, "--marketplace-only", help="Only show marketplace-only entries."),
    category: str = typer.Option("", "--category", help="Filter by category."),
    plugin: str = typer.Option("", "--plugin", help="Only show capabilities provided by a plugin."),
    json_output: bool = typer.Option(False, "--json", help="Emit JSON instead of rich tables."),
) -> None:
    kind_filter = _parse_kind(kind)
    installed_filter = _exclusive_bool(installed, not_installed, "installed")
    enabled_filter = _exclusive_bool(enabled, disabled, "enabled")
    callable_filter = _exclusive_bool(callable_now, not_callable, "callable")

    report = build_inventory()
    capabilities = filter_capabilities(
        report.capabilities,
        kind=kind_filter,
        installed=installed_filter,
        enabled=enabled_filter,
        callable_now=callable_filter,
        marketplace_only=marketplace_only,
        category=category or None,
        plugin=plugin or None,
    )
    if json_output:
        print_json([capability.model_dump(mode="json") for capability in capabilities])
        return
    render_capabilities_table(capabilities, title="Capabilities")



def _parse_kind(kind: str) -> CapabilityKind | None:
    if not kind:
        return None
    try:
        return CapabilityKind(kind)
    except ValueError as error:
        raise typer.BadParameter(
            "kind must be one of: skill, plugin, mcp_server, tool"
        ) from error



def _exclusive_bool(include: bool, exclude: bool, label: str) -> bool | None:
    if include and exclude:
        raise typer.BadParameter(f"Use only one of --{label} or --not-{label}.")
    if include:
        return True
    if exclude:
        return False
    return None
