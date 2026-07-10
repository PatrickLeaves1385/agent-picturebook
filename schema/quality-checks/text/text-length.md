---
id: "text/text-length"
category: "text"
severity: "warning"
method: "count"
target: "每页 1-2 句，每句 5-10 词"
skill: null
fail_action: "flag"
priority: "project-overridable"
description: "校验每页文字量是否在 1-2 句、每句约 5-10 词的范围内。过长或过短影响低龄儿童阅读体验。"
---
# 每页文字量校验

逐页检查英文文本的句数和词数。

## 检测方法
- 逐页提取 `**Text**：` 后的英文文本
- 统计每页句子数（按英文句号/问号/感叹号分句）
- 统计每句词数

## 验收标准
- 每页 1-2 句 → PASS
- 每句 5-10 词 → PASS
- 超出范围 → WARNING，标注具体页码和建议

## 注意
- 纯画面页（无文本）和晚安收尾页（固定句式）允许例外
- 此检测为 warning，非阻塞性
