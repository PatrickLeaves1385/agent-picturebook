---
title: "用户否决记录"
summary: "唯一的否决记录来源（v2 起不再维护单独的 json 侧记录）。维护规则：仅追加，不修改，不删除，永久生效。"
source: "Agent 自进化（evolution-policy.md v2 §4.3）"
version: 2
---

# 用户否决记录

> 本表是**唯一**的否决记录来源，永久生效，除非用户主动说"撤销否决 {proposal_id}"。
> 再次出现同类信号：evolution-agent 检测到本表已有记录 → 走 ask_user，提案中主动呈现历史否决摘要。
> 位置说明：本文件与 `evolution-policy.md` 于 2026-07-08 从 `wiki/domains/agent-design/` 迁移到 `.claude/agent-design/`。

## 否决摘要表

| 否决时间 | 提案 ID | 信号关键词 | 否决原因（脱敏） | 撤销方式 |
|---|---|---|---|---|

<!-- 否决记录为追加式。新否决在此表新增一行，格式见表头。撤销否决由用户主动发起。 -->
