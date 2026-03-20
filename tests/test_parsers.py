from __future__ import annotations

from pathlib import Path

from claude_skills.adapters.local_skills import load_local_skills
from claude_skills.adapters.skill_lock import load_skill_lock
from claude_skills.utils import parse_frontmatter_text, sanitize_data



def test_parse_frontmatter_text_extracts_yaml_and_body() -> None:
    text = """---
name: sample
metadata:
  skill-author: Alice
---
# Heading
Body
"""
    frontmatter, body = parse_frontmatter_text(text)

    assert frontmatter["name"] == "sample"
    assert frontmatter["metadata"]["skill-author"] == "Alice"
    assert body.startswith("# Heading")



def test_sanitize_data_redacts_sensitive_values() -> None:
    payload = {
        "env": {"ANTHROPIC_AUTH_TOKEN": "sk-secret", "SAFE": "ok"},
        "headers": {"Authorization": "Bearer abc"},
    }

    sanitized = sanitize_data(payload)

    assert sanitized["env"]["ANTHROPIC_AUTH_TOKEN"] == "<redacted>"
    assert sanitized["headers"]["Authorization"] == "<redacted>"
    assert sanitized["env"]["SAFE"] == "ok"



def test_load_local_skills_reads_skill_markdown(tmp_path: Path) -> None:
    skill_dir = tmp_path / "skills" / "sample"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        """---
name: sample
description: test skill
license: MIT
---
# Sample Skill
""",
        encoding="utf-8",
    )

    observations, missing = load_local_skills(tmp_path / "skills")

    assert not missing
    assert len(observations) == 1
    observation = observations[0]
    assert observation.name == "sample"
    assert observation.source.facts["license"] == "MIT"
    assert observation.source.facts["heading"] == "Sample Skill"



def test_load_skill_lock_reads_records(tmp_path: Path) -> None:
    lock_path = tmp_path / ".skill-lock.json"
    lock_path.write_text(
        '{"version":3,"skills":{"demo":{"sourceUrl":"https://example.com/repo.git","pluginName":"demo-pack"}}}',
        encoding="utf-8",
    )

    observations = load_skill_lock(lock_path)

    assert len(observations) == 1
    assert observations[0].name == "demo"
    assert observations[0].source.facts["pluginName"] == "demo-pack"
