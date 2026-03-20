from __future__ import annotations

from pathlib import Path

from ..models import CapabilityKind, CapabilityObservation, ConfidenceLevel, Evidence, Relationship, RelationshipType, capability_id
from ..utils import extract_env_placeholders, load_json_file, sanitize_data
from .installed_plugins import InstalledPluginRecord
from .marketplaces import MarketplaceRecord



def load_mcp_definitions(
    *,
    marketplaces: list[MarketplaceRecord],
    installed_plugin_records: list[InstalledPluginRecord],
    available_env_keys: set[str],
) -> list[CapabilityObservation]:
    observations: list[CapabilityObservation] = []

    for marketplace in marketplaces:
        for mcp_path in sorted(marketplace.install_location.rglob(".mcp.json")):
            observations.extend(
                _load_mcp_file(
                    mcp_path=mcp_path,
                    source_type="marketplace_mcp",
                    confidence=ConfidenceLevel.LOW,
                    available_env_keys=available_env_keys,
                    marketplace_name=marketplace.name,
                    installed_locally=False,
                )
            )

    for record in installed_plugin_records:
        mcp_path = record.install_path / ".mcp.json"
        if mcp_path.is_file():
            observations.extend(
                _load_mcp_file(
                    mcp_path=mcp_path,
                    source_type="installed_mcp",
                    confidence=ConfidenceLevel.HIGH,
                    available_env_keys=available_env_keys,
                    marketplace_name=record.marketplace_name,
                    installed_locally=True,
                    plugin_key=record.plugin_key,
                )
            )

    return observations



def _load_mcp_file(
    *,
    mcp_path: Path,
    source_type: str,
    confidence: ConfidenceLevel,
    available_env_keys: set[str],
    marketplace_name: str | None,
    installed_locally: bool,
    plugin_key: str | None = None,
) -> list[CapabilityObservation]:
    payload = load_json_file(mcp_path)
    if not isinstance(payload, dict):
        return []

    resolved_plugin_key = plugin_key or _plugin_key_for_path(mcp_path, marketplace_name)
    observations: list[CapabilityObservation] = []

    for server_name, raw_config in sorted(payload.items()):
        if not isinstance(raw_config, dict):
            continue
        required_env_vars = sorted(extract_env_placeholders(raw_config))
        missing_env_vars = sorted(env_var for env_var in required_env_vars if env_var not in available_env_keys)
        transport = str(raw_config.get("type")) if raw_config.get("type") else None

        relationships = []
        if resolved_plugin_key:
            relationships.append(
                Relationship(
                    type=RelationshipType.PROVIDED_BY.value,
                    target_id=f"plugin:{resolved_plugin_key}",
                    target_name=resolved_plugin_key,
                )
            )

        observations.append(
            CapabilityObservation(
                id=capability_id(CapabilityKind.MCP_SERVER, str(server_name)),
                kind=CapabilityKind.MCP_SERVER,
                name=str(server_name),
                description=_describe_mcp_server(server_name, raw_config, resolved_plugin_key),
                installed_locally=installed_locally,
                marketplace_visible=not installed_locally,
                reasons=["MCP server definition was found in plugin metadata."],
                relationships=relationships,
                source=Evidence(
                    source_type=source_type,
                    source_path=str(mcp_path),
                    confidence=confidence,
                    facts=sanitize_data(
                        {
                            "transport": transport,
                            "required_env_vars": required_env_vars,
                            "missing_env_vars": missing_env_vars,
                            "config": raw_config,
                            "marketplace": marketplace_name,
                            "plugin": resolved_plugin_key,
                            "auth_required": bool(required_env_vars),
                        }
                    ),
                ),
            )
        )

    return observations



def _plugin_key_for_path(mcp_path: Path, marketplace_name: str | None) -> str | None:
    plugin_root = mcp_path.parent
    plugin_json = plugin_root / ".claude-plugin" / "plugin.json"
    payload = load_json_file(plugin_json)
    if isinstance(payload, dict):
        plugin_name = str(payload.get("name") or plugin_root.name)
    else:
        plugin_name = plugin_root.name

    if marketplace_name:
        return f"{plugin_name}@{marketplace_name}"
    return plugin_name



def _describe_mcp_server(server_name: object, raw_config: dict, plugin_key: str | None) -> str:
    transport = raw_config.get("type")
    if plugin_key:
        return f"MCP server '{server_name}' defined by plugin {plugin_key} using {transport or 'unknown'} transport."
    return f"MCP server '{server_name}' using {transport or 'unknown'} transport."
