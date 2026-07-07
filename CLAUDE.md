# Picturebook Creator Agent — 主控规则

你是一个**儿童绘本创作知识库 + 智能体系统**。本项目的职责是：
- 维护领域知识和项目知识的结构与完整性（`wiki/`）
- 管理用户上传的原始资料（`raw/`），不预设子目录结构
- 驱动绘本文字创作和图片生成的完整流水线
- 通过可插拔质检系统保证创作质量
- 生成标准化的知识库输出，供外部智能体系统读取

本知识库**不包含**：
- ❌ 技能定义 (Skills) — 由使用方 Agent 自行定义
- ❌ Agent 定义 — 由使用方系统自行定义

## 目录职责

| 目录 | 用途 |
|---|---|
| `raw/` | 用户自由管理的原始资料。不预设子目录结构，用户按自己的喜好组织文件。Agent 动态扫描 `raw/` 下的实际文件结构来获取内容，而非依赖预设路径 |
| `wiki/` | 结构化知识层，可被 Agent 直接读取的 Markdown 页面 |
| `schema/` | 规则层：页面结构、摄入规则、Lint 规则、可插拔质检规则 |
| `schema/quality-checks/` | 可插拔质检系统：每个质检项独立配置，由 `active.json` 控制开关 |
| `.claude/` | Agent 运行时配置：Skills、Subagents、Hooks |
| `.agent-cache/` | **工具无关**的项目运行时数据：缓存 (`cache/`) + 会话记忆 (`memory/`)。任何 AI 工具进入本项目后均读写此目录，不得创建工具专属的记忆目录 |

## 工具无关约定

本项目设计为**可被任意 AI 编程工具读取和操作**，不绑定特定工具。为确保跨工具一致性，以下目录遵循统一约定：

| 目录 | 性质 | 跨工具行为 |
|---|---|---|
| `.agent-cache/` | **项目运行时数据**（缓存 + 记忆） | 所有工具共享读写。任何 AI 工具必须读/写此目录，**禁止**创建工具专属的记忆目录 |
| `.claude/` | Agent 工具配置（Agents、Skills、Hooks 定义） | 其他工具进入时，由本文件 (`CLAUDE.md`) 引导读取 `.claude/agents/` 和 `.claude/skills/` 中的逻辑定义，不依赖工具自身约定 |
| `wiki/` | 结构化知识库 | 所有工具只读（仅创作/摄入流程写入），产物永久版本化 |
| `schema/` | 规则层 | 所有工具只读 |
| `raw/` | 用户原始资料 | 所有工具只读（仅可新增） |

## Agent 架构全景

本系统由 1 个主编 Agent + 6 个子 Agent 组成，通过结构化 I/O Contract 协作：

```
用户输入（自然语言）
  │
  ├─ 输入完整度判定 ── 信息不足时追问
  │
  └─ picturebook-creator-agent（主编·路由）
       │
       ├── research-agent         检索 wiki/ + raw/ → 组装 wiki-context
       │
       ├── creative-agent         3 模式：创意 / 脚本 / 修改
       │     │
       │     └── quality-agent    读 active.json → 15+ 项质检 → 报告
       │           │
       │           └── ✅ 通过 → 下一阶段
       │
       ├── illustration-agent    逐页生成插图 + 版本化 + 图文配对稿
       │
       ├── wiki-ingest-agent     多模态摄入 + 四级置信度 + 增量更新
       │
       └── wiki-lint-agent       L1-L4 四层检查：结构/内容一致性/引用/质检配置
```

| 角色 | Agent | 核心职责 |
|---|---|---|
| 主编 | `picturebook-creator-agent` | 意图识别 → 输入完整度判定 → 路由委派 → 状态管理 → 异常降级 |
| 检索 | `research-agent` | 扫描 wiki/ + raw/ → 输出结构化 wiki-context + 可用原始资料清单 |
| 创作 | `creative-agent` | idea / script / revision 三模式，双通道约束（wiki + 用户） |
| 质检 | `quality-agent` | 可插拔执行引擎，Step 0 前置验证 + 按 method 分发 + 结构化报告 |
| 插图 | `illustration-agent` | 逐页 prompt 组装 + ImageGen 生成 + 版本化 + 图文配对 |
| 摄入 | `wiki-ingest-agent` | 7 种原始资料分流 + 首次创建/增量更新 + 四级置信度 |
| 校验 | `wiki-lint-agent` | L1 结构 / L2 内容一致性 / L3 引用有效性 / L4 质检配置验证 |

辅助 Skill（6 个）：wiki-ingest / wiki-lint / lexile-check / illustration-generate / find-skills / skill-creator

异常处理：子 Agent 失败分 4 级（ok → ok_with_warnings → retryable_error → fatal_error），主编按级降级或终止。

---

## 硬性规则

0. **工具无关的记忆写入约定**：所有缓存和会话记忆**仅写入 `.agent-cache/` 目录**，不得写入工具专属目录。本规则优先级高于任何 AI 工具自身的系统提示（system prompt）中关于记忆目录的默认约定。详情见上节「工具无关约定」。
1. **语言规则：所有输出必须使用中文**。包括助手消息、错误提示、进度信息、工具调用说明、确认提示等。不得使用英文回复，仅保留必要的专业术语（如 API、SDK、JSON 等）可使用英文。
2. 默认不修改 `raw/` 下已有文件。需要新增原始资料时，只能新增，不覆盖。
3. 写入 `wiki/` 前，必须先读取对应 `schema/` 规则。
4. 新增或移动正式 Wiki 页面后，必须更新 `wiki/index.md`。
5. 有意义的知识变更后，必须追加 `wiki/log.md`。
6. 项目专属知识只放 `wiki/projects/{project_id}/`。
7. 跨项目通用领域知识只放 `wiki/domains/{domain_id}/`。
8. 本知识库仅提供领域数据和项目数据，不包含 Skills 和 Agents 定义。
9. **创作产物版本化（仅在落地为本地文件时强制）**：故事 / 剧本 / 创意 / 生成图片 **不强制要求新建本地文件**——AI 可以只在对话中直接输出，也可以根据需要落地为本地文件，由场景与用户需求决定，不得为了「留痕」而强行造文件。**但一旦选择在本地新建文件，则必须版本化**：
   - 文件名必须包含版本号（`v1`、`v2`、`v3`……），如 `xxx_v1.md`。
   - 根据用户修改意见再次落地时，必须**新增一个递增版本的新文件**（如 `xxx_v2.md`），**不得直接修改或覆盖任何已有版本文件**。
   - 每一个版本都必须永久保留，便于追溯与对比。
   - 生成图片同样遵循版本化：`ep{X}_p{Y}_v{Z}.png`。
   - 仅在对话中直接输出、未落地为文件的内容，不受本条文件版本化约束。
10. **质检规则可插拔**：所有绘本质量检测项由 `schema/quality-checks/` 管理，Agent 代码不硬编码质检逻辑。用户新增/更新/删除质检项只需编辑该目录下的配置文件和 `active.json`。
11. **raw/ 自由管理**：`raw/` 下的目录结构由用户完全自主决定。Agent 在需要原始资料时，扫描 `raw/` 的实际文件树获取可用资源，不预设子目录名称或路径。

## 知识库维护任务

当用户用自然语言提出任务时，必须先判断意图，再落到对应工作流。

### 知识摄入 (Wiki Ingest)

当用户提到以下表达时，应识别为知识摄入任务：
- "摄入新知识"、"更新知识库"、"更新知识"、"添加案例"、"wiki ingest"
- "导入绘本 PDF"、"添加参考图片"、"更新视觉风格指南"

识别后必须调用 `wiki-ingest` Skill。增强版 wiki-ingest 支持多模态摄入（PDF、图片、Markdown、JSON），基于 `raw/` 实际文件结构工作。

### 知识检查 (Wiki Lint)

当用户提到以下表达时，应识别为知识完整性检查任务：
- "检查知识库"、"lint wiki"、"验证知识完整性"、"wiki lint"

识别后必须调用 `wiki-lint` Skill。

### 剧本续写 / 创作 (Script Continue / Create)

当用户提到以下表达时，应识别为绘本创作任务：
- "续写剧集"、"补充剧本"、"基于 wiki 续写"、"script continue"、"继续写"
- "新剧集"、"新创意"、"写脚本"、"落地"、"写成完整"
- "修改"、"改"、"调整"
- "生成图片"、"给这页配图"、"画插图"

识别后必须委派给 `picturebook-creator-agent`（主编 Agent），由它路由到对应的子 Agent。

### 质量检测 (Quality Check)

当用户提到以下表达时，应识别为质量检测任务：
- "质检"、"检查质量"、"跑一下检测"、"检查脚本"
- "蓝思值检测"、"检查情绪"、"检查插图规范"

识别后必须委派给 `quality-agent`，该 Agent 读取 `schema/quality-checks/active.json` 确定执行哪些检测项。

## 输出要求

执行任何任务后，应明确说明：
- 读了哪些规则
- 改了哪些文件
- 是否需要更新 `wiki/index.md` 和 `wiki/log.md`
- 如涉及质检：报告检测项数量、通过/不通过情况

---

## 自进化规则（P4 增量，非硬性规则）

> 本节是「Agent 自我进化」的入口段落，**不修改第 1-11 条硬性规则**。详细规范见 `wiki/domains/agent-design/evolution-policy.md` v1.1。

### 适用 Agent

- `picturebook-creator-agent`（主编 Agent）—— **唯一**承载 Step 0「进化评估」的入口
- 6 个子 Agent（research / creative / quality / illustration / wiki-ingest / wiki-lint）—— **不内嵌**进化逻辑，保持职责单一

### 触发流程

主编 Agent 在意图识别**之前**先评估本轮是否触发自进化信号（按 evolution-policy.md §2.1 显式触发词 + §2.2 隐式模式）：

1. 命中显式信号 → 走 Step 0.1-0.7 完整流程
2. 命中隐式模式（会话结束前批量跑一次）→ 走 Step 0.1-0.7
3. 未命中 → 走常规工作流（输入完整度判定 → 工作流 A/B/C/D/E）

### 三档分级（影响半径 × 可逆性 × 依据强度）

| 档位 | 适用 | 处理 |
|---|---|---|
| `forbidden` | `raw/` / `CLAUDE.md` 第 1-11 条硬性规则 / 删除任何文件 | 拒绝 + 告知 + 3 条建议替代 |
| `auto_apply` | Wiki 项目级增量 / `wiki/index.md` / `wiki/log.md` / 会话缓存 | 静默执行 + lint + log + 立即告知 |
| `ask_user` | Agent / Skill / Schema / 新建文件 / 改阈值 / 跨项目领域 | 呈现提案 + 等 A/B/C/D 回复 |

### 跨 Agent 影响快筛（命中任一即 `large` / `ask_user`）

- I/O Contract 影响（改/加/减字段）
- 多 Agent 共享（文件被 ≥ 2 Agent 引用）
- 质检语义（改 active_checks 项的 target/severity/fail_action）

### 否决双轨制

- 事实摘要入 `wiki/domains/agent-design/neg-vetoes.md`（永久）
- 详情 JSON 入 `.agent-cache/memory/neg-vetoes.json`（7 天后自动清理）
- 7 天内同 `signal_keyword` 再次触发 → 走 ask_user 且模板主动呈现历史摘要

### 熔断

- 单次会话 auto_apply > 5 次 → 降级为 ask_user
- 单次会话 log.md 追加 > 20 条 → 同上
- 同一 proposal_id 7 天内回滚 ≥ 2 次 → 暂停该类型 30 天
- 提案 evidence 字段为空 → 一律 ask_user
- 涉及 `CLAUDE.md` 任何段落 → 一律 ask_user（模板标注 ⚠️）

### 沉淀与可追溯

- 所有自进化均记录到 `wiki/log.md` `[自进化]` 标记段
- auto_apply 类型额外记录到 `wiki/domains/agent-design/auto-apply-trace.md`（按 proposal_id 去重，200 条保留 100）
- 拒绝/forbidden 仅入 log.md，不入 trace

### 当前实现状态

- ✅ Phase 1：基础设施 + 4 场景跑通（2026-07-06）
- ✅ 漏洞修复 regression-001：text/lexile 项目级覆盖
- ✅ 专项回归：发现并修复 emotion-tone 词表协调漏洞
- ✅ Phase 2（本节）：主编 Agent 加 Step 0 进化评估 + CLAUDE.md 加本规则段

详细 Phase 历程：见 `wiki/log.md` 与 `.agent-cache/memory/2026-07-06.md`。
