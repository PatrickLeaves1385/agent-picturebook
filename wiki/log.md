---
title: "知识库变更日志"
summary: "wiki/ 知识库内容变更日志，仅记录 wiki/ 下的知识页面增删改。追加式，不修改历史条目。Agent 系统自身变更见 .claude/log.md。"
---

# 知识库变更日志

> 本文件记录 wiki/ 知识库内容变更（新增/更新/废弃知识页面）。追加式日志，不修改历史条目（CLAUDE.md 硬性规则 #5）。
> Agent 系统自身变更（Agent/Skill/Schema/CLAUDE.md 等）记录在 `.claude/log.md`，与本文件分离。

## 变更记录

<!-- 追加格式：
## YYYY-MM-DD
- 操作（新增/更新/废弃）：页面路径 — 简述
-->

## 2026-07-09

### 首次知识摄入（sync 模式，manifest 不存在 → 降级全量 create）

**触发**：用户"更新知识库"→ 工作流 E → wiki-ingest-agent（sync 模式）

**差异摘要**：新增 15 文件 / 修改 0 / 删除 0 / 无变化 0（`.agent-cache/cache/ingest-manifest.json` 不存在，全部 raw 文件视为新增）

**提取方式**：
- python-docx：10 个 .docx（标准提取）
- antiword：1 个 .doc（受欢迎IP分析.doc，标准提取）
- pdfplumber：1 个 .pdf（种族刻板印象清单.pdf，标准提取）
- Read 直接读取：2 个 .md（Lini characters/worldview）+ 1 个 .txt（北美本土风俗与日常生活）+ 1 个 .md（行业规范，含 20 网页链接）
- WebFetch 网页链接处理：行业规范.md 含 20 个 URL，逐一 WebFetch 访问，18 成功 / 2 失败（FCC 返回 Access Denied、CARU 为 PDF 二进制无法解析）

**新增页面（15 个）**：

项目知识 `wiki/projects/lini/`（2 个）：
- 新增：wiki/projects/lini/characters.md — 小熊猫 Lini 角色设定（性格/视觉/表情/关系/否定项）
- 新增：wiki/projects/lini/worldview.md — 月牙茶园世界观（主题/规则/场景/故事引擎/世界圣经）

领域知识 `wiki/domains/`（13 个）：

ip-design（4 个）：
- 新增：wiki/domains/ip-design/ip-design-principles.md — IP 设计方法论 9 节 + 角色 Brief 模板
- 新增：wiki/domains/ip-design/ip-design-prohibitions.md — 20 条禁止规则 + 检查清单
- 新增：wiki/domains/ip-design/popular-ip-analysis.md — 竞品分层矩阵 + 四标杆拆解 + 底层规律
- 新增：wiki/domains/ip-design/rejected-ip-analysis.md — 被抵制形态 + 案例库 + 防御性设计清单

story-craft（4 个）：
- 新增：wiki/domains/story-craft/story-craft-principles.md — 方法论 12 节 + Brief 与大纲模板
- 新增：wiki/domains/story-craft/story-craft-prohibitions.md — 六类 22 条边界 + 发布前清单
- 新增：wiki/domains/story-craft/popular-story-analysis.md — 长青绘本 + 动画案例 + 八大共性规律
- 新增：wiki/domains/story-craft/rejected-story-analysis.md — 双向风险 + 禁书数据 + 防御清单

child-development（1 个）：
- 新增：wiki/domains/child-development/child-development-stages.md — 2–12 岁四年龄段分层详解

north-america-context（3 个）：
- 新增：wiki/domains/north-america-context/daily-life.md — 美国儿童每日生活十大章节
- 新增：wiki/domains/north-america-context/stereotypes-checklist.md — 种族刻板印象 8 母版 + 6 族裔清单
- 新增：wiki/domains/north-america-context/literary-elements-and-folklore.md — 文学元素与本土传说

industry-standards（1 个）：
- 新增：wiki/domains/industry-standards/regulations.md — 行业规范汇总（含 18/20 网页原文提取）

**置信度**：全部 `unverified`（首次摄入，单一来源）

**待人工确认**：
- 行业规范.md 的 2 个失败链接（FCC 儿童电视规则、CARU 广告自律准则 PDF）需后续手动补充
- Lini 项目角色/世界观设定建议经 sensitivity reader 确认后升级为 human-approved
- 所有领域知识建议经领域专家复核后升级置信度

**非标准提取**：无（全部使用标准提取方式：python-docx / antiword / pdfplumber / Read / WebFetch）

**manifest**：本次摄入后创建 `.agent-cache/cache/ingest-manifest.json`（15 条 entry，status=active）
