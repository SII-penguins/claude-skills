---
name: claude-skills-companion
description: This skill should be used when the user asks what Claude-related capabilities are available on the current machine, asks whether local support exists for PDF, docx, xlsx, github, MCP, plugins, or tools, asks why a capability is unavailable, or asks for the best currently available capability for a task. It should use the `claude-skill` CLI to discover, recommend, and diagnose local capabilities.
---

# Claude Skills Companion

Use this skill as a discovery and diagnosis layer for local Claude capabilities. Do not pretend to directly execute a skill, plugin, MCP server, or tool before confirming that it exists and is currently available.

## When to use this skill

Use this skill when the user is asking questions such as:

- "What can I use for PDFs on this machine?"
- "Do I have anything for spreadsheets?"
- "Why can't I use github right now?"
- "What Claude skills or MCP servers are available?"
- "Recommend the best capability for this task."
- "Show me whether docx / xlsx / github / MCP support is installed."

Do not use this skill for executing the underlying domain task itself unless the discovery step is complete and the user is explicitly moving on to that next step.

## Core workflow

### 1. Recommend the best capability for a task

When the user asks "what should I use" or gives a natural-language task description, start with:

```bash
claude-skill recommend "<user request>"
```

Examples:

```bash
claude-skill recommend "I need to extract tables from a PDF"
claude-skill recommend "what can I use for spreadsheets?"
claude-skill recommend "why can't I use github right now?"
```

Use `--json` when structured post-processing is helpful:

```bash
claude-skill recommend "I need help with spreadsheets" --json
```

### 2. Inspect one capability in detail

When the top recommendation needs explanation, inspect the merged record:

```bash
claude-skill show <name>
```

Examples:

```bash
claude-skill show github
claude-skill show pdf
claude-skill show "document-skills@anthropic-agent-skills"
```

Use this to confirm:

- where the capability comes from
- whether it is installed locally
- whether it is enabled
- why it is or is not callable now
- which plugin provides a skill
- whether MCP configuration is missing environment variables

### 3. Inventory what exists

When the user wants a broader overview, use:

```bash
claude-skill scan
claude-skill list
claude-skill list --kind skill
claude-skill list --kind mcp_server
claude-skill callable
```

Use filtered `list` queries when the user asks for a subset such as skills, MCP servers, or capabilities provided by one plugin.

### 4. Diagnose why something is unavailable

When the user asks why a capability cannot be used, check both the recommendation output and explicit diagnostics:

```bash
claude-skill doctor
claude-skill show <name>
```

Pay attention to findings such as:

- capability is marketplace-only
- plugin is enabled in settings but missing locally
- skill exists in the lockfile but local content is missing
- MCP server is missing required environment variables

## Response guidelines

- Summarize findings instead of pasting raw CLI tables back verbatim.
- Separate "why this is relevant" from "why it is or is not usable right now."
- Prefer the most relevant capability that is callable now.
- If the best textual match is not available, say so clearly and name the best currently callable fallback.
- For "why can't I use X right now" questions, explicitly cite readiness details such as marketplace-only state, disabled plugin state, or missing environment variables.
- If the user wants to proceed after discovery, suggest the exact capability name that should be used next.

## Suggested patterns

### Best capability recommendation

1. Run `claude-skill recommend "<task>"`
2. Summarize the top 1-3 matches
3. Highlight which one is callable now
4. If needed, run `claude-skill show <top-result>` for more detail

### Availability diagnosis

1. Run `claude-skill recommend "why can't I use <name> right now"`
2. Run `claude-skill show <name>`
3. Run `claude-skill doctor` if the reason is still ambiguous
4. Summarize the blocking condition and the best fallback

### Capability inventory

1. Run `claude-skill scan` or filtered `claude-skill list`
2. If the user needs only currently usable items, run `claude-skill callable`
3. Summarize the relevant subset for the user's task

## Important constraint

This skill is a capability-discovery wrapper around the `claude-skill` CLI. It should not claim that a PDF skill, GitHub MCP server, plugin, or builtin tool is usable without checking the local inventory first.
