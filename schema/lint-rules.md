# Lint Rules

## Required Files

- `CLAUDE.md`
- `wiki/index.md`
- `wiki/log.md`
- `schema/lint-rules.md`
- `schema/quality-checks/active.json`

## Raw Rules（用户原始资料）

- `raw/` 为用户自由管理的**原始资料层**，不预设子目录结构。
- 用户可按自己的喜好组织 `raw/` 下的文件和目录。
- `raw/` 下的文件**只增不改**，已有文件不覆盖。
- 不允许把结构化 Wiki 页面写回 `raw/`。
- Agent 须动态扫描 `raw/` 的实际文件树获取内容，不依赖预设路径。

## Outputs Rules（Agent 生成产出物）

- `outputs/{project_id}/` 为 Agent **生成产出物**目录，按类型分子目录（scripts/illustrations/characters/scenes/props）。
- 生成产物遵循版本化规则（`_v1`/`_v2` 递增）。
- `outputs/{project_id}/` 中的图片同时作为后续生成的参考图来源。
- `outputs/{project_id}/` 中的图片由 picturebook-art-agent 读取作为参考图来源。
- **定稿项目文件必须落 `outputs/{project_id}/`，建议用户同时保留副本到 `raw/`，严禁直接写入 `wiki/`。**

## Ingest Rules（知识摄入追踪）

- `wiki-ingest-agent` 通过 `.agent-cache/cache/ingest-manifest.json` 追踪 raw/ → wiki/ 映射。
- `sync` 模式自动检测 raw/ 文件的增删改，分路径安全处理。
- raw/ 文件删除时，wiki 页面标记废弃但不删除内容。
- manifest 丢失/损坏时降级为全量 create 模式。

## Wiki Rules

正式 Wiki 页面必须：

1. 有标题
2. 有用途说明或摘要
3. 有来源
4. 能被 `wiki/index.md` 导航到

Wiki 页面可通过相对路径引用 `raw/` 中的文件。

## Index Rules

以下页面必须被索引:

- `wiki/projects/**/*.md`
- `wiki/domains/**/*.md`

## Log Rules

`wiki/log.md` 与 `.claude/log.md` 分工不同，二者均为**追加式**日志（只增不改历史条目）：

以下变更必须追加 `wiki/log.md`（知识库变更日志，仅 wiki/ 内容）：

- 新增 `wiki/domains/` 或 `wiki/projects/` 下的知识页面
- 更新已有知识页面内容

以下变更必须追加 `.claude/log.md`（Agent 系统变更日志）：

- 新增/移除/更新质检项（`schema/quality-checks/` 变更）
- `.claude/agents/*.md`、`.claude/skills/*/SKILL.md` 变更
- `CLAUDE.md`、`.claude/hooks/`、`.claude/settings.json` 变更
- `.claude/agent-design/` 下进化机制文档变更（evolution-policy.md / neg-vetoes.md，系统治理内容，非创作知识）

## Knowledge Placement Rules

- 项目专属知识 -> `wiki/projects/{project_id}/`
- 跨项目通用领域知识 -> `wiki/domains/{domain_id}/`
- 质检规则 -> `schema/quality-checks/`
- 原始资料 -> `raw/`（用户自主组织）
- ❌ 知识库范围（`wiki/` + `schema/`）不包含 Skills 和 Agent 定义本体 -> 定义存放在本仓库 `.claude/` 下（Agent Harness，与知识库并存，非外部依赖）

## Quality Check Rules

- 质检规则配置文件位于 `schema/quality-checks/`，按 category 分子目录（`text/`、`content/`、`illustration/`、`future/`）。
- 每个质检项为独立 `.md` 文件，包含 id、category、severity、method、target、skill、fail_action、description 基础字段；另可声明 `priority`（`project-overridable` | `global-only`）、`activation_mode`（如 `always-on`）、`target_source` 等可选扩展字段（详见 `schema/quality-checks/README.md`）。L4 校验要求激活项声明 `priority`，缺失视为 `project-overridable`（向前兼容，给 WARNING）。
- `active.json` 控制当前启用的质检项列表，新增质检项需同步更新。
- 质检系统由 `quality-agent` 驱动，不硬编码在 Agent 代码中。
