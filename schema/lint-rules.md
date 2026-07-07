# Lint Rules

## Required Files

- `CLAUDE.md`
- `wiki/index.md`
- `wiki/log.md`
- `schema/lint-rules.md`
- `schema/quality-checks/active.json`

## Raw Rules

- `raw/` 为用户自由管理的原始资料层，不预设子目录结构。
- 用户可按自己的喜好组织 `raw/` 下的文件和目录。
- `raw/` 下的文件只增不改，已有文件不覆盖。
- 不允许把结构化 Wiki 页面写回 `raw/`。
- Agent 须动态扫描 `raw/` 的实际文件树获取内容，不依赖预设路径。
- 版本化创作文件落地时，建议落在 `raw/` 内用户指定的位置。

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

以下变更必须追加 `wiki/log.md`：

- 新增 Wiki 页面
- 更新 Wiki 页面
- 新增/移除/更新质检项（`schema/quality-checks/` 变更）

## Knowledge Placement Rules

- 项目专属知识 -> `wiki/projects/{project_id}/`
- 跨项目通用领域知识 -> `wiki/domains/{domain_id}/`
- 质检规则 -> `schema/quality-checks/`
- 原始资料 -> `raw/`（用户自主组织）
- ❌ 本知识库不包含 Skills 和 Agents 定义

## Quality Check Rules

- 质检规则配置文件位于 `schema/quality-checks/`，按 category 分子目录（`text/`、`content/`、`illustration/`、`future/`）。
- 每个质检项为独立 `.md` 文件，包含 id、category、severity、method、target、skill、fail_action、description 字段。
- `active.json` 控制当前启用的质检项列表，新增质检项需同步更新。
- 质检系统由 `quality-agent` 驱动，不硬编码在 Agent 代码中。
