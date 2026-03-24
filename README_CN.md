# Claude Skills

[English](./README.md)

[![Python 3.13+](https://img.shields.io/badge/python-3.13%2B-blue.svg)](https://www.python.org/)
[![Tests](https://github.com/SII-penguins/claude-skills/actions/workflows/ci.yml/badge.svg)](https://github.com/SII-penguins/claude-skills/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](./LICENSE)

Claude Skills 是一个 Python CLI，用来盘点本机与 Claude 相关的能力，并解释：

- 当前有哪些能力
- 它们来自哪里
- 它们现在是否大概率可调用
- 它们属于本地已安装、已启用、内置能力，还是仅在 marketplace 中可见

安装后的命令名是：

```bash
claude-skill
```

## 项目简介

Claude Skills 会扫描本机的 Claude 相关状态，并将结果统一归并成一份 capability inventory。它适合回答这类问题：

- 当前机器上有哪些 skill、plugin、MCP server 和 builtin tool？
- 哪些能力是真正安装在本地的？
- 哪些能力当前处于启用状态？
- 哪些能力只是 marketplace 元数据里可见？
- 为什么某个能力会被判断为 callable 或 not callable？

## 它会扫描哪些来源

Claude Skills 当前会聚合以下来源：

- 本地 skills：`~/.agents/skills`
- skills lockfile：`~/.agents/.skill-lock.json`
- Claude settings：`~/.claude/settings.json`
- installed plugins：`~/.claude/plugins/installed_plugins.json`
- installed plugin cache：`~/.claude/plugins/cache`
- known marketplaces：`~/.claude/plugins/known_marketplaces.json`
- `~/.claude/plugins/marketplaces` 下的 marketplace plugin / MCP 元数据
- 一份静态 builtin tool catalog

## 环境要求

- Python `3.13+`
- 本机最好存在一些 Claude 相关状态目录，例如 `~/.agents` 或 `~/.claude`

如果这些目录不存在，工具仍然可以运行，但输出会是不完整的局部结果。

## 安装方式

如果你是在 GitHub 上看到这个仓库，并希望把它安装到自己的电脑上使用，可以用以下任一方式。

### 方式 1：克隆仓库后本地安装

这是最清晰、也最适合想查看源码或自行修改的人。

```bash
git clone https://github.com/SII-penguins/claude-skills.git
cd claude-skills
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install .
```

如果你使用的是 Windows PowerShell，激活虚拟环境请使用：

```powershell
.venv\Scripts\Activate.ps1
```

你也可以使用 SSH 克隆：

```bash
git clone git@github.com:SII-penguins/claude-skills.git
```

### 方式 2：直接从 GitHub 安装

如果你只想安装使用，不需要先拿到工作副本：

```bash
python3 -m pip install "git+https://github.com/SII-penguins/claude-skills.git"
```

如果仓库是私有的，这一步通常要求你的机器已经完成 GitHub 认证。

### 验证安装是否成功

安装完成后，执行：

```bash
claude-skill --help
```

如果提示命令不存在，通常需要检查：

- 你是否已经激活虚拟环境
- 你是不是把包安装到了另一个 Python 环境
- 当前环境的 `bin` 目录是否在 `PATH` 中

## 快速开始

```bash
claude-skill scan
claude-skill list --kind skill
claude-skill recommend "I need to inspect a PDF and extract tables"
claude-skill show github
claude-skill callable
claude-skill doctor
```

如果你需要机器可读输出，大多数命令都支持 `--json`。

## CLI 使用说明

### `claude-skill scan`
扫描所有支持的数据源，并输出总体统计。

适合用来回答：
- 总共有多少 capability
- 按类型分类后各有多少（`skill`、`plugin`、`mcp_server`、`tool`）
- 按 availability 分类后各有多少（`enabled`、`installed`、`marketplace_only`、`builtin`）
- 按 confidence 分类后各有多少（`high`、`medium`、`low`）

示例：

```bash
claude-skill scan
claude-skill scan --json
```

### `claude-skill list`
按统一视图列出 capability，并支持过滤。

常见筛选参数：
- `--kind`：`skill`、`plugin`、`mcp_server`、`tool`
- `--installed` / `--not-installed`
- `--enabled` / `--disabled`
- `--callable` / `--not-callable`
- `--marketplace-only`
- `--category`
- `--plugin`
- `--json`

示例：

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

### `claude-skill recommend <query>`
根据自然语言任务描述或诊断问题，推荐最相关的 capability。

这个命令会基于确定性的启发式规则，同时考虑“相关性”和“当前可用性”，适合回答例如：

- 某个任务现在该用什么能力
- 当前机器上有什么可用于 spreadsheet、PDF、GitHub 的能力
- 为什么某个能力现在不能用

常用参数：
- `--kind`：只看 `skill`、`plugin`、`mcp_server`、`tool`
- `--top`：控制返回多少条推荐
- `--callable-first`：进一步优先当前可调用项
- `--json`：输出机器可读 JSON

示例：

```bash
claude-skill recommend "I need to inspect a PDF and extract tables"
claude-skill recommend "what can I use for spreadsheets?"
claude-skill recommend "why can't I use github right now"
claude-skill recommend "I need help with spreadsheets" --json
```

### `claude-skill show <name>`
显示某个单独 capability 的完整归并结果，包括证据和关系。

适合用来回答：
- 它的来源是什么
- 为什么它会被判定为 callable / not callable
- 某个 skill 是由哪个 plugin 提供的
- 哪些文件构成了这个判断的证据

示例：

```bash
claude-skill show github
claude-skill show pdf
claude-skill show "document-skills@anthropic-agent-skills"
claude-skill show github --json
```

说明：
- skill 通常用名字查询，例如 `pdf`、`docx`、`find-skills`
- plugin 通常用完整名查询，例如 `document-skills@anthropic-agent-skills`
- MCP server 通常用名字查询，例如 `github`、`slack`、`stripe`

### `claude-skill callable`
列出当前最可能可调用的 capability。

该命令只保留满足以下条件的项：
- `callable_now = true`
- `confidence = high` 或 `medium`

示例：

```bash
claude-skill callable
claude-skill callable --json
```

### `claude-skill doctor`
报告 inventory 中的异常和歧义。

典型检查包括：
- marketplace-only capability
- MCP server 缺失必要环境变量
- settings 中启用但本地没有安装记录的 plugin
- lockfile 中有记录但本地缺失内容的 skill
- 本地 skill 目录存在但缺少 `SKILL.md`

示例：

```bash
claude-skill doctor
claude-skill doctor --json
```

### `claude-skill export [output]`
导出完整 inventory JSON。

行为：
- 不带参数：输出到 stdout
- 带路径参数：写入指定文件

示例：

```bash
claude-skill export
claude-skill export /tmp/claude-skills.json
```

## 如何理解输出字段

每个 capability 会被归并成统一模型，包含例如：

- `kind`：`skill | plugin | mcp_server | tool`
- `installed_locally`：是否有本地安装证据
- `enabled`：是否启用，或根据上下文可推断为启用
- `callable_now`：当前是否较可能可调用
- `availability`：`enabled | installed | marketplace_only | builtin | unknown`
- `confidence`：`high | medium | low`
- `reasons`：文字化解释为什么被判成当前状态
- `sources`：按来源拆分的证据记录
- `relationships`：例如“这个 skill 由哪个 plugin 提供”

## Companion skill

仓库里还包含了一个随仓库版本管理的 companion skill：

- `skills/claude-skills-companion/SKILL.md`

它的作用是让 Claude 在用户提出这类问题时，优先通过 `claude-skill` CLI 做能力发现、推荐和诊断：

- 当前机器上有哪些 Claude 相关能力
- 本机是否有 PDF / docx / xlsx / github / MCP 支持
- 为什么某个能力现在不可用
- 当前最适合这个任务、而且真的可用的能力是什么

这个 companion skill 常用的底层命令包括：

```bash
claude-skill recommend "I need to extract tables from a PDF"
claude-skill show github
claude-skill doctor
claude-skill list --kind skill
```

如果你想把它安装到本地 `~/.agents/skills`，可以直接复制：

```bash
mkdir -p ~/.agents/skills
cp -R skills/claude-skills-companion ~/.agents/skills/
```

你也可以只把它作为 repo asset 保留在仓库中统一管理。

## 示例用法

### 查看 GitHub MCP 定义

```bash
claude-skill show github
```

通常这会展示一个 `mcp_server` 类型的 capability。如果它只是出现在 marketplace 元数据里而没有本地安装，常见结果会是：

- `availability = marketplace_only`
- `confidence = low`
- `callable_now = false`

它适合帮助你理解：
- “元数据里可见”
- 和“当前机器上真实可用”

这两件事不是一回事。

### 查看一个已安装并启用的 plugin

```bash
claude-skill show "document-skills@anthropic-agent-skills"
```

这通常会展示一个 `plugin` capability。如果当前机器上它已安装且已启用，常见结果会是：

- `installed_locally = true`
- `enabled = true`
- `callable_now = true`
- `availability = enabled`
- `confidence = high`

查看它提供了哪些能力：

```bash
claude-skill list --plugin "document-skills@anthropic-agent-skills"
```

查看它提供的某个具体 skill：

```bash
claude-skill show pdf
```

## 安全与隐私

Claude Skills 会尽量对敏感信息做脱敏。

- settings 和 MCP 配置中的 secret 不会以明文输出
- 像 `${GITHUB_PERSONAL_ACCESS_TOKEN}` 这样的 auth placeholder 会在有助于排查时保留
- 每份证据按来源独立保存，既能保留 provenance，又避免把秘密信息混入普通说明中

## 开发

以可编辑模式安装，并带上开发依赖：

```bash
git clone https://github.com/SII-penguins/claude-skills.git
cd claude-skills
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -e .[dev]
pytest
```

本地开发时运行 CLI：

```bash
claude-skill --help
claude-skill scan
claude-skill list --kind skill
```

## 常见问题

### `claude-skill: command not found`

常见原因：
- 虚拟环境没有激活
- 包被安装到了另一个 Python 环境
- 当前环境的 `bin` 目录不在 `PATH` 中

### 输出看起来不完整

请检查这些路径在你的机器上是否存在：

- `~/.agents/skills`
- `~/.agents/.skill-lock.json`
- `~/.claude/settings.json`
- `~/.claude/plugins/installed_plugins.json`

如果这些路径不存在，Claude Skills 只能报告当前机器上实际存在的那部分来源。

## License

本项目使用 [MIT License](./LICENSE)。
