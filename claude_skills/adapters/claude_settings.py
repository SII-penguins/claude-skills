from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from ..models import CapabilityKind, CapabilityObservation, ConfidenceLevel, Evidence
from ..utils import load_json_file, sanitize_data


@dataclass
class ClaudeSettingsState:
    observations: list[CapabilityObservation]
    available_env_keys: set[str]



def load_claude_settings(settings_path: Path) -> ClaudeSettingsState:
    payload = load_json_file(settings_path)
    if not isinstance(payload, dict):
        return ClaudeSettingsState(observations=[], available_env_keys=set(os.environ))

    enabled_plugins = payload.get("enabledPlugins")
    env = payload.get("env")

    configured_env_keys = set(env.keys()) if isinstance(env, dict) else set()
    available_env_keys = set(os.environ).union(configured_env_keys)

    observations: list[CapabilityObservation] = []
    if isinstance(enabled_plugins, dict):
        for plugin_name, enabled in sorted(enabled_plugins.items()):
            if not isinstance(enabled, bool):
                continue
            observations.append(
                CapabilityObservation(
                    id=f"plugin:{plugin_name}",
                    kind=CapabilityKind.PLUGIN,
                    name=str(plugin_name),
                    enabled=enabled,
                    reasons=["Plugin enablement comes from Claude settings."],
                    source=Evidence(
                        source_type="claude_settings",
                        source_path=str(settings_path),
                        confidence=ConfidenceLevel.HIGH,
                        facts=sanitize_data(
                            {
                                "enabled": enabled,
                                "env_keys": sorted(configured_env_keys),
                            }
                        ),
                    ),
                )
            )

    return ClaudeSettingsState(observations=observations, available_env_keys=available_env_keys)
