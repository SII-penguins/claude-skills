# Claude Skills

[![Python 3.13+](https://img.shields.io/badge/python-3.13%2B-blue.svg)](https://www.python.org/)
[![Tests](https://github.com/SII-penguins/claude-skills/actions/workflows/ci.yml/badge.svg)](https://github.com/SII-penguins/claude-skills/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](./LICENSE)

A Python CLI for inventorying Claude-related capabilities on a local machine and explaining:

- what capabilities exist
- where they come from
- whether they are likely callable now
- whether they are locally installed, enabled, builtin, or only visible in marketplace metadata

- 中文说明：[`README_CN.md`](./README_CN.md)

## Features

Claude Skills builds a unified inventory across multiple Claude-related sources and helps answer questions such as:

- What skills, plugins, MCP servers, and builtin tools are present?
- Which capabilities are actually installed locally?
- Which capabilities are enabled right now?
- Which items are only visible in marketplace metadata?
- Why is a capability considered callable or not callable?

## Data sources

Claude Skills currently scans and merges information from:

- local skills: `~/.agents/skills`
- skills lockfile: `~/.agents/.skill-lock.json`
- Claude settings: `~/.claude/settings.json`
- installed plugins: `~/.claude/plugins/installed_plugins.json`
- installed plugin cache: `~/.claude/plugins/cache`
- known marketplaces: `~/.claude/plugins/known_marketplaces.json`
- marketplace plugin and MCP metadata under `~/.claude/plugins/marketplaces`
- a static builtin tool catalog

## Requirements

- Python `3.13+`
- A machine with some Claude-related local state under `~/.agents` and/or `~/.claude`

If those directories do not exist, the CLI will still run, but the resulting inventory will be partial.

## Installation

If you found this repository on GitHub and want to use it locally, use one of the following approaches.

### Option 1: Clone the repository and install locally

Recommended if you want a local working copy, plan to inspect the code, or may modify it.

```bash
git clone https://github.com/SII-penguins/claude-skills.git
cd claude-skills
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install .
```

Windows PowerShell activation:

```powershell
.venv\Scripts\Activate.ps1
```

You can also clone over SSH:

```bash
git clone git@github.com:SII-penguins/claude-skills.git
```

### Option 2: Install directly from GitHub

Recommended if you just want the CLI without keeping a local working copy first.

```bash
python3 -m pip install "git+https://github.com/SII-penguins/claude-skills.git"
```

If the repository is private, make sure your machine is already authenticated with GitHub.

### Verify the installation

After installation, verify that the command is available:

```bash
claude-skill --help
```

If the command is not found, check whether:

- your virtual environment is activated
- the package was installed into a different Python environment
- the selected environment’s `bin` directory is on your `PATH`

## Quick start

```bash
claude-skill scan
claude-skill list --kind skill
claude-skill show github
claude-skill callable
claude-skill doctor
```

Use `--json` on most commands when you want machine-readable output.

## CLI reference

### `claude-skill scan`
Scan all supported sources and print an inventory summary.

Useful for:
- total capability counts
- counts by kind (`skill`, `plugin`, `mcp_server`, `tool`)
- counts by availability (`enabled`, `installed`, `marketplace_only`, `builtin`)
- counts by confidence (`high`, `medium`, `low`)

Examples:

```bash
claude-skill scan
claude-skill scan --json
```

### `claude-skill list`
List capabilities in a unified view with filters.

Common filters:
- `--kind` (`skill`, `plugin`, `mcp_server`, `tool`)
- `--installed` / `--not-installed`
- `--enabled` / `--disabled`
- `--callable` / `--not-callable`
- `--marketplace-only`
- `--category`
- `--plugin`
- `--json`

Examples:

```bash
claude-skill list
claude-skill list --kind skill
claude-skill list --kind mcp_server
claude-skill list --installed
claude-skill list --enabled
claude-skill list --callable
claude-skill list --marketplace-only
claude-skill list --plugin "document-skills@anthropic-agent-skills"
claude-skill list --kind skill --json
```

### `claude-skill show <name>`
Show the merged record for a single capability, including evidence and relationships.

Useful for:
- understanding provenance
- understanding why something is callable or not callable
- seeing which plugin provides a skill
- seeing which files contributed evidence

Examples:

```bash
claude-skill show github
claude-skill show pdf
claude-skill show "document-skills@anthropic-agent-skills"
claude-skill show github --json
```

### `claude-skill callable`
List capabilities that are most likely callable right now.

This command only includes items that are:
- `callable_now = true`
- `confidence = high` or `medium`

Examples:

```bash
claude-skill callable
claude-skill callable --json
```

### `claude-skill doctor`
Report anomalies and ambiguities in the inventory.

Typical checks include:
- marketplace-only capabilities
- MCP servers missing required environment variables
- enabled plugins with no local install record
- skills recorded in the lockfile but missing locally
- local skill directories without `SKILL.md`

Examples:

```bash
claude-skill doctor
claude-skill doctor --json
```

### `claude-skill export [output]`
Export the full inventory as JSON.

Behavior:
- without an argument: writes JSON to stdout
- with a path argument: writes JSON to the specified file

Examples:

```bash
claude-skill export
claude-skill export /tmp/claude-skills.json
```

## How to read the output

Each capability is normalized into a model with fields such as:

- `kind`: `skill | plugin | mcp_server | tool`
- `installed_locally`: whether local installation evidence exists
- `enabled`: whether the capability is enabled or inferred as enabled
- `callable_now`: whether it is likely callable now
- `availability`: `enabled | installed | marketplace_only | builtin | unknown`
- `confidence`: `high | medium | low`
- `reasons`: human-readable explanation of the classification
- `sources`: per-source evidence records
- `relationships`: links such as “this skill is provided by this plugin”

## Example workflows

### Inspect the GitHub MCP definition

```bash
claude-skill show github
```

This usually shows an `mcp_server` capability sourced from marketplace metadata. If it is not installed locally, it will typically appear as:

- `availability = marketplace_only`
- `confidence = low`
- `callable_now = false`

This is useful for understanding the difference between:
- visible in metadata
- actually available on the current machine

### Inspect an installed and enabled plugin

```bash
claude-skill show "document-skills@anthropic-agent-skills"
```

On a machine where it is installed and enabled, you should typically expect:

- `installed_locally = true`
- `enabled = true`
- `callable_now = true`
- `availability = enabled`
- `confidence = high`

To list capabilities provided by that plugin:

```bash
claude-skill list --plugin "document-skills@anthropic-agent-skills"
```

To inspect one bundled skill in detail:

```bash
claude-skill show pdf
```

## Security and privacy

Claude Skills is designed to redact sensitive values in its output.

- secrets from settings and MCP configs are not printed in plaintext
- auth placeholders such as `${GITHUB_PERSONAL_ACCESS_TOKEN}` are preserved when useful for diagnosis
- evidence is stored per source so provenance remains visible without exposing secrets

## Development

Install in editable mode with development dependencies:

```bash
git clone https://github.com/SII-penguins/claude-skills.git
cd claude-skills
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -e .[dev]
pytest
```

Run the CLI locally during development:

```bash
claude-skill --help
claude-skill scan
claude-skill list --kind skill
```

## Troubleshooting

### `claude-skill: command not found`

Common causes:
- the virtual environment is not activated
- the package was installed into a different Python environment
- the environment’s `bin` directory is not on your `PATH`

### The inventory looks incomplete

Check whether these paths exist on your machine:

- `~/.agents/skills`
- `~/.agents/.skill-lock.json`
- `~/.claude/settings.json`
- `~/.claude/plugins/installed_plugins.json`

If they do not exist, Claude Skills can only report the subset of sources that are available.

## License

This project is licensed under the [MIT License](./LICENSE).
