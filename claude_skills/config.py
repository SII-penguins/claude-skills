from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel


class ClaudeSkillsPaths(BaseModel):
    agents_skills_dir: Path
    skill_lock_path: Path
    claude_settings_path: Path
    installed_plugins_path: Path
    plugin_cache_dir: Path
    known_marketplaces_path: Path
    marketplaces_dir: Path

    @classmethod
    def default(cls, home: Path | None = None) -> "ClaudeSkillsPaths":
        home = home or Path.home()
        return cls(
            agents_skills_dir=home / ".agents" / "skills",
            skill_lock_path=home / ".agents" / ".skill-lock.json",
            claude_settings_path=home / ".claude" / "settings.json",
            installed_plugins_path=home / ".claude" / "plugins" / "installed_plugins.json",
            plugin_cache_dir=home / ".claude" / "plugins" / "cache",
            known_marketplaces_path=home / ".claude" / "plugins" / "known_marketplaces.json",
            marketplaces_dir=home / ".claude" / "plugins" / "marketplaces",
        )
