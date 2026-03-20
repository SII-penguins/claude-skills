from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import yaml

SENSITIVE_KEYWORDS = (
    "token",
    "secret",
    "password",
    "authorization",
    "api_key",
    "apikey",
    "cookie",
    "session",
    "private_key",
    "access_key",
)
EXACT_SENSITIVE_KEYS = {
    "auth",
    "authentication",
    "credentials",
}
ENV_PLACEHOLDER_RE = re.compile(r"\$\{([A-Z0-9_]+)\}")
BEARER_RE = re.compile(r"^(Bearer)\s+(.+)$", re.IGNORECASE)


def load_json_file(path: Path) -> Any | None:
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def parse_frontmatter_text(text: str) -> tuple[dict[str, Any], str]:
    text = text.lstrip("\ufeff")
    if not text.startswith("---"):
        return {}, text

    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, text

    end_index: int | None = None
    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            end_index = index
            break

    if end_index is None:
        return {}, text

    frontmatter_block = "\n".join(lines[1:end_index])
    body = "\n".join(lines[end_index + 1 :])

    parsed = yaml.safe_load(frontmatter_block) or {}
    if not isinstance(parsed, dict):
        parsed = {}
    return parsed, body


def parse_frontmatter_file(path: Path) -> tuple[dict[str, Any], str]:
    return parse_frontmatter_text(path.read_text(encoding="utf-8"))


def first_heading(markdown_body: str) -> str | None:
    for raw_line in markdown_body.splitlines():
        line = raw_line.strip()
        if line.startswith("#"):
            return line.lstrip("#").strip() or None
    return None


def looks_sensitive_key(key: str | None) -> bool:
    if not key:
        return False
    lowered = key.lower()
    normalized = lowered.replace("-", "_")
    if normalized in EXACT_SENSITIVE_KEYS:
        return True
    return any(keyword in lowered for keyword in SENSITIVE_KEYWORDS)


def redact_string(value: str, *, key: str | None = None) -> str:
    if "${" in value:
        return value

    bearer_match = BEARER_RE.match(value.strip())
    if bearer_match:
        return f"{bearer_match.group(1)} <redacted>"

    if value.startswith("sk-"):
        return "<redacted>"

    if looks_sensitive_key(key):
        return "<redacted>"

    return value


def sanitize_data(value: Any, *, key: str | None = None) -> Any:
    if isinstance(value, dict):
        sanitized: dict[str, Any] = {}
        for child_key, child_value in value.items():
            child_key_str = str(child_key)
            if looks_sensitive_key(child_key_str) and not _is_placeholder_only(child_value):
                sanitized[child_key_str] = "<redacted>"
            else:
                sanitized[child_key_str] = sanitize_data(child_value, key=child_key_str)
        return sanitized

    if isinstance(value, list):
        return [sanitize_data(item, key=key) for item in value]

    if isinstance(value, tuple):
        return [sanitize_data(item, key=key) for item in value]

    if isinstance(value, str):
        return redact_string(value, key=key)

    if isinstance(value, Path):
        return str(value)

    return value


def extract_env_placeholders(value: Any) -> set[str]:
    found: set[str] = set()

    if isinstance(value, dict):
        for child in value.values():
            found.update(extract_env_placeholders(child))
        return found

    if isinstance(value, (list, tuple)):
        for child in value:
            found.update(extract_env_placeholders(child))
        return found

    if isinstance(value, str):
        return set(ENV_PLACEHOLDER_RE.findall(value))

    return found



def _is_placeholder_only(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    stripped = value.strip()
    if not stripped:
        return False
    return bool(ENV_PLACEHOLDER_RE.fullmatch(stripped) or re.fullmatch(r"Bearer\s+\$\{[A-Z0-9_]+\}", stripped))



def unique_strings(values: list[str]) -> list[str]:
    seen: set[str] = set()
    unique: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            unique.append(value)
    return unique


def compact_json(value: Any) -> str:
    return json.dumps(sanitize_data(value), ensure_ascii=False, sort_keys=True)


def pretty_json(value: Any) -> str:
    return json.dumps(sanitize_data(value), ensure_ascii=False, indent=2, sort_keys=True)
