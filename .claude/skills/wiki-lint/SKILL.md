---
name: wiki-lint
description: 当需要检查仓库结构、索引、日志和知识分区完整性时使用。
---

# Wiki Lint Skill

## Goal

对当前仓库做结构与治理检查。

## Required Reads

1. `CLAUDE.md`
2. `schema/lint-rules.md`
3. `wiki/index.md`
4. `wiki/log.md`

## Check Scope

- `raw/` 是否被误改
- 正式 Wiki 页面是否有来源
- 正式页面是否已登记到 `wiki/index.md`
- 知识变更是否同步记录到 `wiki/log.md`
- 项目知识与通用知识是否放错目录

## Output

默认输出至对话中，不自动写入文件。

## Constraints

- 默认不自动修复业务内容
- 只输出 `PASS / PASS_WITH_WARNINGS / FAIL` 及问题说明
- 对人工未确认内容优先给 `WARNING`
- `raw/` 误改、索引缺失、日志缺失优先给 `ERROR`
