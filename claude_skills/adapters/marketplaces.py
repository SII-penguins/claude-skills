from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ..models import CapabilityKind, CapabilityObservation, ConfidenceLevel, Evidence
from ..utils import load_json_file, sanitize_data


@dataclass
class MarketplaceRecord:
    name: str
    install_location: Path
    source: dict
    last_updated: str | None



def load_known_marketplaces(known_marketplaces_path: Path) -> list[MarketplaceRecord]:
    payload = load_json_file(known_marketplaces_path)
    if not isinstance(payload, dict):
        return []

    marketplaces: list[MarketplaceRecord] = []
    for marketplace_name, raw_marketplace in sorted(payload.items()):
        if not isinstance(raw_marketplace, dict):
            continue
        install_location = raw_marketplace.get("installLocation")
        if not isinstance(install_location, str):
            continue
        marketplaces.append(
            MarketplaceRecord(
                name=str(marketplace_name),
                install_location=Path(install_location),
                source=raw_marketplace.get("source") if isinstance(raw_marketplace.get("source"), dict) else {},
                last_updated=str(raw_marketplace.get("lastUpdated")) if raw_marketplace.get("lastUpdated") else None,
            )
        )
    return marketplaces



def load_marketplace_plugins(marketplaces: list[MarketplaceRecord]) -> list[CapabilityObservation]:
    observations: list[CapabilityObservation] = []
    for marketplace in marketplaces:
        observations.extend(_load_marketplace_plugins(marketplace))
    return observations



def _load_marketplace_plugins(marketplace: MarketplaceRecord) -> list[CapabilityObservation]:
    observations: list[CapabilityObservation] = []
    for plugin_json in sorted(marketplace.install_location.rglob(".claude-plugin/plugin.json")):
        payload = load_json_file(plugin_json)
        if not isinstance(payload, dict):
            continue
        plugin_name = str(payload.get("name") or plugin_json.parent.parent.name)
        full_name = f"{plugin_name}@{marketplace.name}"
        observations.append(
            CapabilityObservation(
                id=f"plugin:{full_name}",
                kind=CapabilityKind.PLUGIN,
                name=full_name,
                description=_string_or_none(payload.get("description")),
                marketplace_visible=True,
                reasons=["Plugin is visible in a local marketplace cache."],
                source=Evidence(
                    source_type="marketplace_plugin",
                    source_path=str(plugin_json),
                    confidence=ConfidenceLevel.LOW,
                    facts=sanitize_data(
                        {
                            "marketplace": marketplace.name,
                            "author": payload.get("author"),
                            "last_updated": marketplace.last_updated,
                            "location": str(plugin_json.parent.parent),
                        }
                    ),
                ),
            )
        )
    return observations



def _string_or_none(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None
