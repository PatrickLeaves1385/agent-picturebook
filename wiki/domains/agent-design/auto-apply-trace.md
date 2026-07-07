---
title: "Auto-apply 留痕"
summary: "记录所有 auto_apply 类型的自进化执行。ask_user 走 wiki/log.md，forbidden 不留痕。维护规则：按 proposal_id 去重，同一 ID 多次出现时覆盖为最新状态（不修改历史事实，仅更新状态字段）。200 条阈值时保留最近 100 条，回滚条目永久保留不计入配额。"
source: "Agent 自进化（evolution-policy.md v1.1 §9.4）"
version: 1
---

# Auto-apply 留痕

> 仅记录 auto_apply 类型的执行。ask_user 与 forbidden 不在本表记录。
> 维护规则详见 evolution-policy.md v1.1 §9.4。

## 状态字段说明

- `applied` — 已应用
- `rolled-back` — 已回滚（永久保留，不计入 100 条配额）
- `failed-lint` — 落地后 wiki-lint 失败已自动回滚

## 留痕表

| proposal_id | 时间 | 触发信号 | 影响 | 落地文件 | 状态 | 状态变更时间 |
|---|---|---|---|---|---|---|
| prop-2026-07-06-001 | 2026-07-06 15:30 | Phase 1.5 场景 1 实施需求 | small | wiki/log.md | applied | 2026-07-06 15:30 |
| prop-2026-07-06-002 | 2026-07-06 15:35 | 用户原话"放宽蓝思值上限 300→350" | large | schema/quality-checks/text/lexile.md | applied | 2026-07-06 15:35 |
| prop-2026-07-06-007 | 2026-07-06 16:12 | 消 L4 WARNING（7 个 priority 字段） | small | schema/quality-checks/{text/awl, text/page-count, content/emotion-tone, content/ip-hooks, content/growth-uniqueness, illustration/composition, content/basic-safety}.md | applied | 2026-07-06 16:12 |
