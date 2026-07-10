---
id: "text/lexile"
category: "text"
severity: "error"
method: "api"
target: "250-350"
skill: "lexile-check"
fail_action: "block"
priority: "project-overridable"
target_source: "active.json | project.content-spec.md"
description: "检测英文文本的蓝思值（Lexile），目标区间 250-350L。低于 250L 说明句子过短需增加复合句，高于 350L 说明句子过长需拆分或替换低频词。项目级 content-spec.md 如显式声明「目标蓝思值」字段，可覆盖默认区间（priority=project-overridable）。"
---
# 蓝思值检测

调用 `lexile-check` Skill，通过 CoGrader API 检测脚本英文文本的蓝思值。

## 检测范围
- 提取脚本中所有 `**Text**：` 后的英文文本行
- 合并为完整英文文本后调用 API

## 验收标准
- 默认目标区间：250L-350L（来自 active.json target）
- 若项目 `wiki/projects/{id}/content-spec.md` 显式声明「目标蓝思值：XXX-YYY」，则以项目值为准（priority=project-overridable）
- 不在区间内 → FAIL，标注当前值并给出调整建议（句长/词汇替换）

## 优先级与覆盖机制

| 优先级 | 来源 | 适用条件 |
|---|---|---|
| 1（最高） | 项目 content-spec.md 显式声明 | 含「目标蓝思值：XXX-YYY」字样 |
| 2 | active.json target | 默认 |
| 3 | 兜底 | 当前 schema 中的硬编码值 |

quality-agent Step 1.5「项目级覆盖解析」自动检测项目级覆盖，解析后的 `effective_target` 写入 wiki-context。

## 特殊处理
- 如文本词数过少导致 API 返回误差，结果标注 `"(Low word count)"`
- 分块检测结果标注 `"(Chunked analysis)"`

## 变更记录
- **2026-07-06**：[自进化 prop-2026-07-06-002] target 上限 300 → 350，依据：用户反馈 demo 项目 300 太紧。详见 `.agent-cache/memory/runs-archive/phase1.5-2026-07-06-scenario2.md`
- **2026-07-06**：[修复 regression-001] 加 priority=project-overridable + target_source 字段，暴露项目级覆盖机制。详见 `.agent-cache/memory/runs-archive/regression-demo2-2026-07-06.md` §4.4
