# Claude Skills

Claude Skills is a Python CLI that inventories Claude-related capabilities on the current machine and explains:

- 有什么能力
- 来自哪里
- 现在是否可调用
- 它是本地存在、已启用，还是仅 marketplace 可见

安装后的命令名是：`claude-skill`

## 它会盘点哪些来源

- 本地 skills：`~/.agents/skills`
- skills lockfile：`~/.agents/.skill-lock.json`
- Claude settings：`~/.claude/settings.json`
- installed plugins：`~/.claude/plugins/installed_plugins.json`
- installed plugin cache：`~/.claude/plugins/cache`
- marketplace plugins / MCP：`~/.claude/plugins/known_marketplaces.json` 和 `~/.claude/plugins/marketplaces`
- 内置工具静态 catalog

## 快速开始

```bash
claude-skill scan
claude-skill list --kind skill
claude-skill show github
claude-skill callable
claude-skill doctor
```

如果你想拿机器可读的结果，可以给大多数命令加 `--json`。

## Commands

### `claude-skill scan`
汇总扫描全部来源，输出总览统计。

适合回答：
- 一共有多少能力
- skill / plugin / MCP / tool 各有多少
- installed / enabled / marketplace_only 各有多少
- high / medium / low confidence 各有多少

示例：

```bash
claude-skill scan
claude-skill scan --json
```

---

### `claude-skill list`
统一列出能力，并支持筛选。

常用参数：
- `--kind`：按类型筛选，支持 `skill`、`plugin`、`mcp_server`、`tool`
- `--installed` / `--not-installed`
- `--enabled` / `--disabled`
- `--callable` / `--not-callable`
- `--marketplace-only`
- `--category`
- `--plugin`
- `--json`

适合回答：
- 当前有哪些 MCP server
- 哪些能力来自某个 plugin
- 哪些只是 marketplace 可见但未安装
- 哪些是当前更可能可调用的本地能力

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
claude-skill list --category "文档与内容"
claude-skill list --kind skill --json
```

---

### `claude-skill show <name>`
显示单个能力的完整归并结果。

会展示：
- 基本信息：kind、description、category
- 状态：installed、enabled、callable、availability、confidence
- reasons：为什么会被判定成这样
- relationships：它由哪个 plugin 提供，或者和谁有关
- evidence：证据来自哪些文件

适合回答：
- `github` 这个 MCP 到底是哪里来的
- 某个 plugin 是否真的安装且启用
- 某个 skill 为什么被判定为 high / medium / low

示例：

```bash
claude-skill show github
claude-skill show pdf
claude-skill show "document-skills@anthropic-agent-skills"
claude-skill show github --json
```

说明：
- 对 skill，常见名字是 `pdf`、`docx`、`find-skills`
- 对 plugin，通常用完整名，例如 `document-skills@anthropic-agent-skills`
- 对 MCP server，常见名字如 `github`、`slack`、`stripe`

---

### `claude-skill callable`
专门列出“当前最可能可调用”的能力。

它只会保留：
- `callable_now = true`
- `confidence` 为 `high` 或 `medium`

适合回答：
- 现在最值得优先尝试的能力有哪些
- 哪些已经不是纯 marketplace 展示，而是本地/启用状态下较可信的能力

示例：

```bash
claude-skill callable
claude-skill callable --json
```

---

### `claude-skill doctor`
检查异常和歧义。

当前会重点报告：
- marketplace only 能力
- MCP 缺失必要环境变量
- enabled 但未安装
- lockfile 有记录但本地内容缺失
- skill 目录存在但缺少 `SKILL.md`

适合回答：
- 为什么某个能力没有被判成 callable
- 为什么 settings 里开了，但实际上不可用
- 哪些地方还需要补 env / 安装 / 启用

示例：

```bash
claude-skill doctor
claude-skill doctor --json
```

---

### `claude-skill export [output]`
导出完整 JSON，便于后续接 Web / TUI / 脚本处理。

行为：
- 不带参数：打印到 stdout
- 带路径参数：写入指定文件

示例：

```bash
claude-skill export
claude-skill export /tmp/claude-skill.json
```

## 如何理解输出字段

每个 capability 会尽量统一成这些字段：

- `kind`：能力类型，`skill | plugin | mcp_server | tool`
- `installed_locally`：本地是否存在安装痕迹
- `enabled`：是否在 settings 中启用，或根据上下文可视为启用
- `callable_now`：当前是否较可能可调用
- `availability`：
  - `enabled`
  - `installed`
  - `marketplace_only`
  - `builtin`
  - `unknown`
- `confidence`：
  - `high`
  - `medium`
  - `low`
- `reasons`：为什么被判成这个状态
- `sources`：证据来自哪些文件
- `relationships`：例如某个 skill 由哪个 plugin 提供

## 常见使用场景

### 看整体盘点
```bash
claude-skill scan
```

### 看所有 MCP server
```bash
claude-skill list --kind mcp_server
```

### 看某个 plugin 提供了哪些 skill
```bash
claude-skill list --plugin "document-skills@anthropic-agent-skills"
```

### 看 GitHub MCP 的来源和状态
```bash
claude-skill show github
```

### 只看当前更可能能用的能力
```bash
claude-skill callable
```

### 排查为什么某些能力不可用
```bash
claude-skill doctor
```

## 示例：`github` 和 `document-skills`

### 示例 1：查看 `github`

```bash
claude-skill show github
```

这个例子通常表示你在看一个 **MCP server**，而不是普通 skill 或 plugin。

你应该重点关注这些字段：
- `kind = mcp_server`
- `availability = marketplace_only` 表示它目前只是 marketplace 中可见
- `confidence = low` 表示当前不能高置信度判断为本机可直接调用
- `callable_now = false` 表示现在不应把它当作“已经可用”
- `relationships` 里通常会看到它来自某个 plugin，例如 `github@claude-plugins-official`
- `sources` 里会显示它来自某个 `.mcp.json`

如果你用 JSON 查看：

```bash
claude-skill show github --json
```

在当前机器上，你会看到它大致反映这些事实：
- 来源是 marketplace 中的 GitHub MCP 定义
- 不是本地已安装并启用的 MCP
- 它会声明需要的环境变量，例如 `GITHUB_PERSONAL_ACCESS_TOKEN`
- 因此它会被识别为“可见，但当前不算可调用”

这个例子适合用来理解：
- marketplace 可见 ≠ 本机已经可用
- 有定义 ≠ 当前会话就能调用

---

### 示例 2：查看 `document-skills@anthropic-agent-skills`

```bash
claude-skill show "document-skills@anthropic-agent-skills"
```

这个例子通常表示你在看一个 **plugin**。

你应该重点关注这些字段：
- `kind = plugin`
- `installed_locally = true` 表示本地有安装记录
- `enabled = true` 表示在 Claude settings 中已启用
- `callable_now = true` 表示它当前很可能可用
- `availability = enabled`
- `confidence = high`

在当前机器上，这个例子会反映这些事实：
- plugin 已安装
- plugin 已启用
- 它提供的一批打包 skills 可以从 installed cache 中被扫描到

如果你想继续看它提供了哪些能力：

```bash
claude-skill list --plugin "document-skills@anthropic-agent-skills"
```

在当前机器上，这会列出这类能力，例如：
- `pdf`
- `docx`
- `frontend-design`
- 以及同一插件缓存里扫描到的其他 skills

如果你再深入看某个 skill：

```bash
claude-skill show pdf
```

你会更容易理解一条 skill 是如何被判定为：
- 来自某个 plugin
- 当前可调用
- 为什么是 `high` 或 `medium` confidence

这个例子适合用来理解：
- plugin 已安装 + 已启用时，plugin 自带 skill 的 callable 置信度通常更高
- `show plugin` 和 `list --plugin ...` 应该配合使用

## 安全说明

- 输出会对敏感信息做脱敏
- 不会直接回显 settings / MCP 配置里的真实 token
- 像 `${GITHUB_PERSONAL_ACCESS_TOKEN}` 这样的环境变量占位符会保留，方便判断缺少哪些配置

## Development

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
pytest
```

本地开发时也可以直接运行：

```bash
claude-skill --help
claude-skill scan
claude-skill list --kind skill
```
