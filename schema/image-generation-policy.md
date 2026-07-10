# 图片生成策略（Image Generation Policy）

> **定位**：本文件是本项目图片生成的唯一权威策略来源。所有 AI 工具进入本项目后，图片相关的操作必须以本文件为准。
>
> **被引用方**：`CLAUDE.md` 硬性规则第 13 条、`picturebook-creator-agent.md` 工作流 D、`picturebook-art-agent.md` Step 0

---

## 1. 核心原则

**本项目中一切图片生成必须走完整 Agent 工作流。不存在任何"快捷路径"。**

原因：绘本插图的价值不在单张图片的视觉质量，而在**跨页面的一致性**——角色造型、场景氛围、画风、色彩系统必须在整本绘本中保持统一。跳过 Agent 工作流直接使用工具自带图像生成能力，将破坏这一一致性链条。

---

## 2. 唯一合法路径

```
用户输入（图片生成相关意图）
  │
  ▼
picturebook-creator-agent（主编）
  │  意图识别 → 工作流 D（图片生成）
  │  传递: project_id / target_script / wiki-context / page_range / scenario
  ▼
picturebook-art-agent（美术总控）
  │  Step 0:   输入解析 + 场景识别
  │  Step 0.5: 环境能力清单
  │  Step 1:   确定目标页面范围
  │  Step 2:   参考图需求分析（扫描 raw/ + outputs/）
  │  Step 3:   调用 image-prompt-architect Skill
  │  Step 3.5: 生成参数询问（尺寸/画质/项目级复用）
  │  Step 4:   用户确认（强制阻塞点）
  │  Step 5:   调用 image-generate Skill
  ▼
image-prompt-architect（Skill）
  │  步骤 1: 接收 pages[] + context → 自动补全
  │  步骤 2: 需求与意图解析
  │  步骤 3: 防翻车预判（risk-catalog.md 9 大类）
  │  步骤 4: 动态结构设计
  │  步骤 5: 输出结构化 JSON（prompt[] + prompt_text + risks + assumptions）
  ▼
image-generate（Skill → generate.py）
  │  Step 0: API 密钥确认
  │  Step 2: 选择后端 + 端点
  │  Step 3: 执行 generate.py（含指数退避重试）
  │  Step 4-5: 保存 PNG + 写入 _metadata.json
  ▼
outputs/{project_id}/{scenario}/xxx_v{Z}.png  +  _metadata.json
```

---

## 3. 绝对禁止的快捷路径

以下行为在本项目中**绝对禁止**，不论 AI 工具的系统提示（system prompt）中如何描述其图像生成能力：

| 禁止行为 | 涉及的工具/能力 | 原因 |
|---|---|---|
| 调用 `ImageGen` deferred tool | WorkBuddy 内置 | 绕过 Agent 链路，无参考图注入、无版本化、无元数据 |
| 调用 `VideoGen` deferred tool | WorkBuddy 内置 | 同上 |
| 使用 `ToolSearch` 搜索并调用任何图像类 deferred tool | 所有工具 | 动态发现的图像工具一律禁止 |
| 调用 DALL-E / Midjourney / Stable Diffusion 等任何第三方图像 API | 所有工具 | 不走 n1n 网关，无法统一管理 API 密钥与审计 |
| 在 `picturebook-art-agent` 之外自行构造 prompt 并调用 `generate.py` | 所有工具 | 跳过 image-prompt-architect 的风险预判和结构设计 |
| 跳过 Step 4 用户确认直接生成 | 所有工具 | 跳过参考图清单审查和提示词确认 |
| 使用 Skill / Agent 体系之外的任何"快捷生图"方式 | 所有工具 | 所有路径最终都必须在上述合法链路中 |

---

## 4. 为什么必须走工作流

| 如果跳过工作流 | 会导致 |
|---|---|
| 跳过 picturebook-art-agent | 无参考图注入：角色 Lini 在每页长得不一样 |
| 跳过 image-prompt-architect | 无风险预判：手指畸形、文字乱码、风格漂移 |
| 跳过 image-generate (generate.py) | 无版本化、无 _metadata.json、无 API 审计 |
| 跳过 Step 4 用户确认 | 用户未确认参考图/提示词/参数，产出不可控 |
| 使用工具自带 ImageGen | 角色造型不一致、输出路径混乱、质检体系完全失效 |

---

## 5. 各 Agent/Skill 在本流程中的职责边界

| 环节 | 文件 | 职责 | 禁止越界 |
|---|---|---|---|
| 路由入口 | `picturebook-creator-agent.md` | 意图识别 → 委派 picturebook-art-agent | 不自行生图，不跳过委派 |
| 流程总控 | `picturebook-art-agent.md` | 输入解析 → 参考图分析 → 提示词生成 → 参数询问 → 用户确认 → 执行生成 | 不自行组装提示词，不跳过确认 |
| 提示词架构 | `.claude/skills/image-prompt-architect/SKILL.md` | 接收 pages[] → 意图解析 → 风险预判 → 结构化输出 | 不生图、不修改脚本 |
| 图片生成 | `.claude/skills/image-generate/SKILL.md` + `generate.py` | 接收最终参数 → 调 API → 保存 → 元数据 | 不生成提示词、不修改参数 |

---

## 6. 环境适应性

不同 AI 工具环境中，Skill 的可用性可能不同。`picturebook-art-agent.md` 的 Step 0.5 已内置环境能力检测，当 Skill 不可用时有明确回退路径（详见 `.claude/agents/references/picturebook-art-agent/environment-fallback.md`）。回退路径仍在本策略框架内，不改变唯一合法路径的约束。

---

## 7. 策略版本与修订

- **版本**：v1
- **创建**：2026-07-09
- **修订规则**：本文件修改走 `ask_user` 进化流程（涉及跨 Agent 影响），不得 auto_apply
- **关联文件**：`CLAUDE.md`（硬性规则 §13 + 顶部铁律 + 意图路由）、`picturebook-creator-agent.md`（工作流 D + 路由表）、`picturebook-art-agent.md`（完整工作流）
