---
title: "Agent 系统变更日志"
summary: "Agent Harness 自身迭代记录（Agent/Skill/Schema/CLAUDE.md/Hooks/进化机制等），与 wiki/log.md 分离。追加式，不修改历史条目。"
source: "schema/lint-rules.md §Log Rules"
---

# Agent 系统变更日志

> 本文件记录 Agent Harness 自身的迭代变更，与 `wiki/log.md`（知识库内容变更）分工分离。
> 追加式日志，不修改历史条目（CLAUDE.md 硬性规则 + schema/lint-rules.md §Log Rules）。
> `wiki/log.md` 仅记录 `wiki/` 下知识页面的增删改；本文件记录 Agent/Skill/Schema/CLAUDE.md/Hooks/`.claude/agent-design/` 等系统层面的变更。

## 记录范围

以下变更必须追加到本文件：

- 新增/移除/更新质检项（`schema/quality-checks/` 变更，含 `active.json`）
- `.claude/agents/*.md`、`.claude/skills/*/SKILL.md` 变更
- `CLAUDE.md`、`.claude/hooks/`、`.claude/settings.json` 变更
- `.claude/agent-design/` 下进化机制文档变更（`evolution-policy.md` / `neg-vetoes.md`，系统治理内容，非创作知识）

## 变更记录

<!-- 追加格式：
## YYYY-MM-DD
- 操作（新增/更新/移除/修复）：文件路径 — 简述（原因/影响/关联）
-->
