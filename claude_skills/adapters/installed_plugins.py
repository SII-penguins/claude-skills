from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ..models import CapabilityKind, CapabilityObservation, ConfidenceLevel, Evidence
from ..utils import load_json_file, sanitize_data


@dataclass
class InstalledPluginRecord:
    plugin_key: str
    plugin_name: str
    marketplace_name: str | None
    install_path: Path
    version: str | None
    scope: str | None
    git_commit_sha: str | None
    installed_at: str | None
    last_updated: str | None


@dataclass
class InstalledPluginsState:
    observations: list[CapabilityObservation]
    records: list[InstalledPluginRecord]



def load_installed_plugins(installed_plugins_path: Path) -> InstalledPluginsState:
    payload = load_json_file(installed_plugins_path)
    if not isinstance(payload, dict):
        return InstalledPluginsState(observations=[], records=[])

    plugins = payload.get("plugins")
    if not isinstance(plugins, dict):
        return InstalledPluginsState(observations=[], records=[])

    observations: list[CapabilityObservation] = []
    records: list[InstalledPluginRecord] = []

    for plugin_key, entries in sorted(plugins.items()):
        plugin_name, marketplace_name = _split_plugin_key(str(plugin_key))
        if not isinstance(entries, list):
            continue

        for entry in entries:
            if not isinstance(entry, dict):
                continue
            install_path_raw = entry.get("installPath")
            if not isinstance(install_path_raw, str):
                continue
            record = InstalledPluginRecord(
                plugin_key=str(plugin_key),
                plugin_name=plugin_name,
                marketplace_name=marketplace_name,
                install_path=Path(install_path_raw),
                version=_string_or_none(entry.get("version")),
                scope=_string_or_none(entry.get("scope")),
                git_commit_sha=_string_or_none(entry.get("gitCommitSha")),
                installed_at=_string_or_none(entry.get("installedAt")),
                last_updated=_string_or_none(entry.get("lastUpdated")),
            )
            records.append(record)
            observations.append(
                CapabilityObservation(
                    id=f"plugin:{record.plugin_key}",
                    kind=CapabilityKind.PLUGIN,
                    name=record.plugin_key,
                    installed_locally=True,
                    reasons=["Plugin installation record exists locally."],
                    source=Evidence(
                        source_type="installed_plugin",
                        source_path=str(installed_plugins_path),
                        confidence=ConfidenceLevel.HIGH,
                        facts=sanitize_data(
                            {
                                "scope": record.scope,
                                "install_path": str(record.install_path),
                                "version": record.version,
                                "git_commit_sha": record.git_commit_sha,
                                "installed_at": record.installed_at,
                                "last_updated": record.last_updated,
                            }
                        ),
                    ),
                )
            )

    return InstalledPluginsState(observations=observations, records=records)


def _split_plugin_key(plugin_key: str) -> tuple[str, str | None]:
    if "@" not in plugin_key:
        return plugin_key, None
    plugin_name, marketplace_name = plugin_key.rsplit("@", 1)
    return plugin_name, marketplace_name


def _string_or_none(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None
