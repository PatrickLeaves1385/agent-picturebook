---
id: "text/awl"
category: "text"
severity: "warning"
method: "api"
target: "<2%"
skill: "lexile-check"
fail_action: "flag"
priority: "project-overridable"
description: "检测学术词汇（AWL）覆盖率。儿童绘本应以日常语言为主，AWL 覆盖率超过 2% 说明学术词汇过多，需替换为日常用词。"
---
# AWL 学术词汇检测

调用 `lexile-check` Skill 获取 AWL 覆盖率。

## 检测范围
- 与蓝思值检测共用同一文本输入
- 从 lexile-check 返回结果中提取 `awlCoverage` 字段

## 验收标准
- AWL 覆盖率 < 2% → PASS
- AWL 覆盖率 >= 2% → WARNING，列出检出的 AWL 词汇，建议替换为日常用词

## 注意
- 此检测作为 warning 而非 error，因为少量学术词汇可能是主题必需
