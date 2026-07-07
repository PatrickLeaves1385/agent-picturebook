---
id: "text/page-count"
category: "text"
severity: "error"
method: "count"
target: "由项目 content-spec.md 定义"
skill: null
fail_action: "block"
priority: "project-overridable"
description: "校验脚本页数是否符合项目 content-spec.md 指定的页数。目标页数从 wiki-context 中提取，不做通用假设。"
---
# 页数校验

统计脚本文件中标记的页面数量，与项目 content-spec.md 指定的页数比对。

## 检测方法
- 在脚本 Markdown 文件中搜索页面标记（如 `## 第 N 页` 或 `## Page N`）
- 统计页面总数
- 从 wiki-context 中的 content-spec 提取目标页数

## 验收标准
- 页面总数 = content-spec.md 指定页数 → PASS
- 页面总数 != 指定页数 → FAIL，标注实际页数与目标页数
- wiki 中无 content-spec 或未指定页数 → SKIP（标注"项目未定义篇幅，跳过"）

## 注意
- 目标页数完全由项目 content-spec.md 定义，不硬编码默认页数
- 无 content-spec 时跳过检测，不阻断流程
