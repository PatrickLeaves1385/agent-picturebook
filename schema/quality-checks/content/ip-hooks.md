---
id: "content/ip-hooks"
category: "content"
severity: "error"
method: "pattern"
target: "由用户或 wiki-context 中定义的项目专属 IP 钩子"
skill: null
fail_action: "block"
priority: "project-overridable"
description: "校验脚本中是否包含了项目定义的全部 IP 钩子元素。具体钩子从 wiki-context 或用户输入中提取，不做通用假设。"
---
# IP 钩子完整性检测

搜索脚本全文，确认项目定义的 IP 钩子全部出现。

## 检测方法
1. 从 wiki-context 中提取项目定义的 IP 钩子（如 content-spec 页中列出的视觉符号/标志台词/收尾仪式等）
2. 如 wiki 中无 IP 钩子定义，此检测自动跳过
3. 对每个定义好的钩子：关键词搜索（不区分大小写），比对最低出现次数

## 注意
- 此检测不预设任何具体的钩子内容（不做"必须有 Oh my feathers"之类的假设）
- 钩子内容由项目知识库定义，质检员仅校验是否满足
- 如 wiki 中无钩子定义 → SKIP（标注"项目未定义 IP 钩子，跳过"）
