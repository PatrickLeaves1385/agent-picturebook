# Picturebook Creator — 儿童绘本创作知识库 + 智能体系统

一套可被任意 AI 编程工具读取和操作的儿童绘本创作平台。它维护领域知识和项目知识，驱动从文字创作到插图生成的完整流水线，并通过可插拔质检系统保证创作质量。

## 核心能力

- **知识库管理**：结构化维护跨项目领域知识（`wiki/domains/`）和项目专属知识（`wiki/projects/`），支持多模态摄入（PDF / 图片 / Markdown / JSON）
- **绘本创作**：从创意构思 → 脚本写作 → 质量检测 → 插图生成的全链路流水线
- **可插拔质检**：12 项独立检测项（8 激活 + 4 未激活），按需开关，不依赖 Agent 代码硬编码
- **工具无关**：设计为可被 Claude Code / WorkBuddy / Cursor / Windsurf 等任意 AI 工具读取，运行时数据统一落 `.agent-cache/`

## 目录结构

```
├── CLAUDE.md                    # 主控规则（硬性规则 + 自进化规则）
├── README.md                    # 本文件
├── raw/                         # 用户原始资料（图片/PDF/草稿），只增不改
├── outputs/                     # Agent 生成产出物，按项目分目录，版本化
│   └── {project_id}/            #   项目资产目录
│       ├── scripts/             #     故事脚本
│       ├── illustrations/       #     绘本插图
│       ├── characters/          #     角色人设图
│       ├── scenes/              #     场景图
│       └── props/               #     道具图
├── wiki/                        # 结构化知识层（只读，Agent 可直接读取）
│   ├── index.md                 # 知识库导航索引
│   ├── log.md                   # 知识库变更日志（仅 wiki/ 内容）
│   ├── domains/                 # 跨项目通用领域知识（内容随 raw/ 摄入动态生成，不在此列举）
│   └── projects/                # 项目专属知识（内容随 raw/ 摄入动态生成，不在此列举）
├── schema/                      # 规则层（只读）
│   ├── lint-rules.md            #   Wiki 校验规则（L1-L4）
│   └── quality-checks/          #   可插拔质检系统
│       ├── active.json          #     当前启用的质检项清单
│       ├── text/                #     文本质量：蓝思值/AWL/页数/文字量
│       ├── content/             #     内容质量：安全/情感/IP钩子/成长点/角色一致性
│       └── illustration/        #     插图质量：构图/姿势朝向/风格一致性
├── .claude/                     # Agent 工具运行时配置
│   ├── log.md                   #   Agent 系统变更日志（Agent/Skill/Schema 等迭代）
│   ├── agents/                  #   1 主编 + 7 子 Agent 定义
│   ├── agent-design/            #   Agent 自进化方案与否决记录（evolution-policy.md / neg-vetoes.md）
│   └── skills/                  #   核心 Skill（wiki-ingest/wiki-lint/lexile-check/…）
├── .agent-cache/                # 工具无关的项目运行时数据
│   ├── cache/                   #   可重建的派生缓存
│   ├── memory/                  #   跨会话持久化记忆
│   └── telemetry/               #   Agent 观测日志（JSONL）
└── data_collect/                # 会话导出层
```

## Agent 架构

1 个主编 Agent + 7 个子 Agent（含 evolution-agent），通过结构化 I/O Contract 协作：

```
用户输入
  │
  ├── evolution-agent ───── 自进化信号识别与处理
  │
  └── picturebook-creator-agent（主编·路由）
       │
       ├── research-agent         检索 wiki/ → 组装上下文
       ├── creative-agent         创意 / 脚本 / 修改（3 模式）
       │     └── quality-agent    读 active.json → 质检 → 报告
       ├── picturebook-art-agent     五类生图场景（插图/角色/场景/道具/风格）总控，n1n 双后端（gpt-image-2/nano-banana-2）+ 参考图注入 + 参数询问 + 用户确认 + 版本化
       ├── wiki-ingest-agent      多模态摄入 + 增删改全覆盖（sync 模式，委派 wiki-ingest Skill）
       └── wiki-lint-agent        L1-L4 四层完整性检查
```

## 可插拔质检系统

当前激活 8 项质检，1 项恒定激活：

| 类别 | 检测项 | 状态 | 说明 |
|---|---|---|---|
| 文本 | text/lexile | ✅ 激活 | 蓝思值检测（支持项目级覆盖） |
| 文本 | text/awl | ✅ 激活 | AWL 学术词汇覆盖率 |
| 文本 | text/page-count | ✅ 激活 | 页数校验 |
| 内容 | content/basic-safety | 🔒 恒定 | 基础安全（负面/恐怖/阴暗词检测） |
| 内容 | content/emotion-tone | ✅ 激活 | 情感基调量化（正负词比+禁止词） |
| 内容 | content/ip-hooks | ✅ 激活 | IP 钩子完整性 |
| 内容 | content/growth-uniqueness | ✅ 激活 | 成长点唯一性（跨项目对比） |
| 插图 | illustration/composition | ✅ 激活 | 构图规范（5 项验收量化） |

增删质检项只需编辑 `schema/quality-checks/active.json`，无需修改 Agent 代码。

## 快速开始

### 运行知识完整性检查

```
wiki-lint：扫描 wiki/ 和 schema/，验证结构/内容/引用/配置完整性
```

### 摄入新知识

将资料放入 `raw/` 后，触发摄入流程：

```
wiki-ingest：扫描 raw/ 实际文件树 → 多模态解析 → 写入 wiki/
```

### 创作绘本

```
"帮我写一个关于友谊的绘本故事"
→ creative-agent 生成脚本 → quality-agent 质检 → picturebook-art-agent 生成插图
```

> **🚫 重要**：本项目中图片生成必须走完整 Agent 工作流，**严禁使用 AI 工具自带的图像生成能力**（如 ImageGen / DALL-E 等）。详细策略见 `schema/image-generation-policy.md`。

### 生成插图

```
"给 Lini 第 1 集第 1 页配图"
→ picturebook-creator-agent → picturebook-art-agent → image-prompt-architect → image-generate (n1n API)
```

完整工作流共 4 个环节：主编路由 → 美术总控（参考图分析 + 参数询问 + 用户确认）→ 提示词架构师（风险预判）→ 生成脚本（调用 API + 版本化 + 元数据）。只有这条路径能保证角色造型一致性和可追溯性。

## 校验脚本

`.claude/hooks/validate-wiki.sh` 是一个**独立的**仓库完整性预检脚本。它检查：必需文件存在、`raw/` 只增不改、wiki 索引/日志标题规范。

在 Claude Code 中，本仓库已通过 `.claude/settings.json` 将其挂载为 `PostToolUse` hook（`matcher: Edit|Write`），每次 Edit/Write 之后自动运行一次：

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          { "type": "command", "command": "sh .claude/hooks/validate-wiki.sh" }
        ]
      }
    ]
  }
}
```

> 这是**事后校验**（PostToolUse 无法阻止写入已经发生），不是真正的前置阻断；但脚本失败会立即在下一步反馈给 Agent，促使当轮就修正，而不是等到事后手动跑 lint 才发现。`.claude/settings.json` 是 Claude Code 专属机制，其他 AI 工具（WorkBuddy / Cursor 等）不读取该文件，在这些工具中该脚本仍需手动运行：

```bash
sh .claude/hooks/validate-wiki.sh
```

> 注意：该钩子仅做基础文件 / raw 保护，不执行 wiki-lint 的 L1-L4 实质检查；完整质检请用 `wiki-lint` Skill。

## 硬性规则摘要

0. 所有 AI 工具读写 `.agent-cache/`，禁止创建工具专属记忆目录
1. 所有输出使用中文
2. `raw/` 只增不改，已有文件不覆盖
3. 写入 `wiki/` 前必须先读对应 `schema/` 规则
4. Wiki 页面变更后必须更新 `wiki/index.md`
5. 知识变更后必须追加 `wiki/log.md`
6. 项目知识 → `wiki/projects/{id}/`，领域知识 → `wiki/domains/{id}/`
7. 创作产物一旦落本地文件必须版本化（`_v1`/`_v2`...）
8. 质检规则可插拔，由 `active.json` 控制

完整规则见 `CLAUDE.md`。

## 当前状态

- **自进化系统**：v2（2026-07-08 瘦身，砍掉未验证/收益不成比例的治理机制，详见 `.claude/agent-design/evolution-policy.md` §7）
- **质检系统**：v4，8 激活 + 4 未激活（差额已说明），支持项目级覆盖 + Skill 分组
- **提示词语言**：中文（2026-07-07 切换）
- **维护者**：用户通过自然语言对话驱动
