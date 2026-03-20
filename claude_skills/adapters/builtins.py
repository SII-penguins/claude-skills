from __future__ import annotations

from ..models import CapabilityKind, CapabilityObservation, ConfidenceLevel, Evidence, capability_id

BUILTIN_TOOLS = [
    ("Task", "Launches specialized subagents for exploration, planning, and execution."),
    ("Bash", "Runs terminal commands in the local environment."),
    ("Read", "Reads local files including text, images, PDFs, and notebooks."),
    ("Write", "Creates or replaces local files."),
    ("Edit", "Applies exact string replacements to existing files."),
    ("Glob", "Finds files by pathname patterns."),
    ("Grep", "Searches file contents with ripgrep semantics."),
    ("WebFetch", "Fetches and summarizes content from a URL."),
    ("WebSearch", "Searches the public web for current information."),
    ("AskUserQuestion", "Prompts the user to choose between options or clarify requirements."),
    ("Skill", "Invokes installed user-facing Claude Code skills."),
    ("NotebookEdit", "Edits notebook cells in Jupyter .ipynb files."),
]



def load_builtin_catalog() -> list[CapabilityObservation]:
    observations: list[CapabilityObservation] = []
    for name, description in BUILTIN_TOOLS:
        observations.append(
            CapabilityObservation(
                id=capability_id(CapabilityKind.TOOL, name),
                kind=CapabilityKind.TOOL,
                name=name,
                description=description,
                installed_locally=True,
                enabled=True,
                callable_now=True,
                builtin=True,
                reasons=["Tool is part of the static builtin catalog."],
                source=Evidence(
                    source_type="builtin_catalog",
                    source_path=None,
                    confidence=ConfidenceLevel.HIGH,
                    facts={"catalog": "static"},
                ),
            )
        )
    return observations
