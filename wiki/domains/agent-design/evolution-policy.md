---
title: "Agent 自我进化方案"
summary: "设计儿童绘本智能体的自我进化能力。根据用户对话反馈主动发起提案，分级处理对 Agent 配置 / 原始资料 / Wiki / Skill / Schema 等内容的更新。影响小且有明确依据的可静默更新 + 告知；影响大或仅是建议的必须经用户确认。"
source: "用户提案"
version: 1
---

# Agent 自我进化方案（设计稿 v1）

> 状态：**待评审，未实施**。本文仅作为方案设计，最终落点（新增/修改哪些文件）需用户确认后再分阶段执行。
>
> 适用范围：本项目的整套智能体系统（CLAUDE.md / .claude/agents/* / .claude/skills/* / schema/* / wiki/* / raw/*）。

---

## 0. 核心目标与约束

### 0.1 目标

让智能体在长期使用中具备「基于用户反馈持续自我校准」的能力，而不是只在首次搭建时由用户手动迭代。闭环：

```
用户对话反馈
  → Agent 识别「可改进信号」
    → 形成「进化提案」（带影响分级 + 依据）
      → 静默执行（小影响 / 明确依据） OR 申请许可（大影响 / 仅是建议）
        → 落地到对应文件（Agent / Skill / Schema / Wiki / Raw / Log）
          → 记录到 wiki/log.md（变更留痕）
            → 通知用户（已完成 / 已应用 / 已降级）
```

### 0.2 硬约束

1. **保护 `raw/`**：原始资料只增不改（与 `schema/lint-rules.md` 一致），进化流程不修改 `raw/` 下任何文件。
2. **不修改 `CLAUDE.md` 的硬性规则段落**（如语言规则、版本化规则、质检可插拔规则等），如有冲突的提案升级到用户层确认。
3. **不删除任何文件**：所有进化都是「新增或修改」，删除必须经用户明确同意。
4. **进化可追溯**：每一次自进化都必须有 `wiki/log.md` 条目，注明「提案来源 / 触发信号 / 决策依据 / 落地 diff 摘要」。
5. **进化方向不可绕过用户否决**：用户说「不同意 / 不要改」则该次提案永久归档，不再触发同类自动落地（除非用户后续主动撤销否决）。

---

## 1. 进化作用域地图

把智能体系统按「影响半径」+「可逆性」+「依据强度」三维度拆分，明确每个象限的默认处理策略：

| 作用域 | 典型文件 | 影响半径 | 可逆性 | 依据强度 | 默认处理 | 用户是否需要确认 |
|---|---|---|---|---|---|---|
| **会话级缓存** | `.agent-cache/cache/research-cache.json` | 仅当前会话 | 高（可重建） | 强（mtime） | 静默写入 | ❌ |
| **临时产物** | `.agent-cache/cache/` 下其他 JSON、`.agent-cache/memory/YYYY-MM-DD.md` | 单次会话 / 当天 | 高 | 强 | 静默写入 | ❌ |
| **质检配置开关** | `schema/quality-checks/active.json`（`active_checks` / `_inactive_checks` 增删条目） | 全系统 | 中（可回滚 `log.md`） | 中（需对质检项有验证） | **需许可** | ✅ |
| **质检规则文件** | `schema/quality-checks/**/*.md` | 全系统 | 中 | 弱（修改需谨慎） | **需许可** | ✅ |
| **Agent 行为定义** | `.claude/agents/*.md`（工作流步骤、I/O Contract、Constraints） | 全系统 | 中 | 弱 | **需许可** | ✅ |
| **Skill 行为定义** | `.claude/skills/*/SKILL.md` | 涉及该 Skill 的工作流 | 中 | 弱 | **需许可** | ✅ |
| **Wiki 知识库（项目）** | `wiki/projects/{id}/*.md`（增量条目 / 修正记录 / 置信度升级） | 单项目 | 中 | 中 | 静默更新 + 告知 | ❌ |
| **Wiki 知识库（领域）** | `wiki/domains/*/*.md` | 跨项目 | 中 | 弱 | **需许可** | ✅ |
| **Wiki 索引/日志** | `wiki/index.md` / `wiki/log.md` | 导航 + 历史 | 高 | 强（机械式追加） | 静默追加 + 告知 | ❌ |
| **质检规则目录元数据** | `schema/quality-checks/README.md` | 全系统 | 中 | 弱 | **需许可** | ✅ |
| **新 Agent / 新 Skill** | `.claude/agents/*.md` / `.claude/skills/*/SKILL.md`（新增） | 全系统 | 低（新增后影响长尾） | 弱 | **需许可** | ✅ |
| **`raw/` 文件** | `raw/**/*` | 永久（只增不改） | ❌ 不可逆 | — | **禁止** | — |
| **`CLAUDE.md` 硬性规则** | `CLAUDE.md` 第 1-11 条硬性规则 | 全系统 | 低 | — | **禁止** | — |

> **决策原则一句话**：影响半径 = 全系统 / 可逆性 = 低 / 依据强度 = 弱 → 任何一项命中即「需许可」；其余默认「静默 + 告知」。

---

## 2. 反馈信号识别（触发器）

智能体在对话中识别以下信号时启动「进化评估」：

### 2.1 显式信号（用户直接表达）

| 触发词 / 句式 | 含义 | 默认处理 |
|---|---|---|
| "这个规则可以改成 ……" | 规则优化建议 | 触发：方案 → 评估 → 提案 |
| "加一个 / 去掉一个质检项" | 质检配置变更 | 触发：方案 → 评估 → 提案 |
| "以后默认就 ……" | 行为偏好固化 | 触发：偏好入 `wiki/domains/agent-design/user-preferences.md`（新建需许可） |
| "下次别再 ……" | 反向偏好（否决类） | 触发：归档到 `.agent-cache/memory/neg-vetoes.json`（静默） |
| "我刚发现 ……" / "刚才 ……" | 实战反馈 | 触发：写入 `wiki/log.md` 实战反馈节（静默） |
| "写得太啰嗦 / 格式不对" | 输出风格修正 | 触发：影响范围评估，提案可能涉及 `CLAUDE.md` 语言规则（需许可） |
| "日志 / 索引漏更新了" | 流程遗漏报告 | 触发：补写 + 标记漏更链路（静默） |
| "这个 raw/ 文件有问题" | 原始资料问题 | **禁止**改 `raw/`，改为"建议重新摄入"提案（需许可） |

### 2.2 隐式信号（行为模式）

| 模式 | 识别方式 | 默认处理 |
|---|---|---|
| 同一类型错误在 N 次会话中重复出现 | 智能体在 `.agent-cache/memory/` 每日记忆文件中 grep 关键词 | 触发：根因分析 → 提议加/改规则 |
| 质检连续 FAIL 且质检项本身存在量化漏洞 | 同一质检项在多脚本中触发 FAIL 但 `schema/quality-checks/{id}.md` 无量化锚点 | 触发：提议增加量化锚点 |
| 主编工作流降级为人工处理的频次过高 | 统计半自动修复降级率 | 触发：提议放宽修复条件 / 优化创意 Agent 提示词 |
| 用户在质检 FAIL 后手动说"这个不算问题" | 用户反馈 | 触发：调整 `fail_action` / `target` 阈值（需许可） |

> **隐式信号处理时机**：不在每轮对话实时检测，而是在每次会话结束前批量跑一次「进化评估」，避免每轮打扰用户。

---

## 3. 提案生成（核心环节）

### 3.1 提案数据结构

```json
{
  "proposal_id": "prop-2026-07-06-001",
  "triggered_at": "2026-07-06T14:47:52+08:00",
  "trigger_source": "explicit | implicit",
  "trigger_signal": "用户原话 / 隐式模式描述",

  "title": "为 composition 质检项增加 Markdown 注释剥离",
  "summary": "demo2 验收发现 composition 5 项判定会误把 '> ⚠️' 引用块计入",
  "evidence": [
    "wiki/log.md 第 80 行：'composition 量化基于插图描述原文，注释行会被错误计入'",
    "schema/quality-checks/illustration/composition.md 第 X 步未含预处理"
  ],

  "scope_files": [
    {
      "path": ".claude/agents/quality-agent.md",
      "change_type": "edit | add | delete | forbidden",
      "change_summary": "Step 2.6 增加文本预处理：剥离 '> ' 引用块 / HTML 注释 / YAML frontmatter"
    }
  ],

  "impact_grade": "small | medium | large",
  "reversibility": "high | medium | low",
  "evidence_strength": "strong | medium | weak",

  "default_action": "auto_apply | ask_user | forbidden",
  "applied_at": null,
  "user_decision": null,
  "applied_diff": null
}
```

### 3.2 影响分级算法

```text
IF scope_files 中存在 CLAUDE.md 第 1-11 硬性规则段落 OR raw/ 下任何文件
    → forbidden
ELSE IF scope_files 包含「新增 Agent / 新增 Skill / 删除任何文件」
    → impact_grade = large
    → default_action = ask_user
ELSE IF scope_files 仅命中「Wiki 索引 / Wiki 日志 / 会话缓存 / 当日 memory」
    → impact_grade = small
    → default_action = auto_apply
ELSE
    → 按下表评分（每一维度 0/1/2 分）
       - 影响半径：单项目 (0) / 单 Skill (1) / 全系统 (2)
       - 可逆性：高 (0) / 中 (1) / 低 (2)
       - 依据强度：强 (0) / 中 (1) / 弱 (2)
    → 总分 ≤ 1：small / auto_apply
    → 总分 = 2-3：small / ask_user
    → 总分 = 4：medium / ask_user
    → 总分 = 5-6：large / ask_user
```

### 3.3 提案输出模板

**auto_apply 类（静默执行 + 告知）**：

```markdown
## 🟢 已应用：{title}

- **触发信号**：{trigger_signal}
- **影响分级**：small
- **依据**：{evidence 摘要}
- **落地 diff 摘要**：
  - `{file_path}`: {change_summary}
  - ...
- **下一步**：已更新 `wiki/log.md` 记录本次自进化（{proposal_id}）。如需回滚请说"回滚 {proposal_id}"。
```

**ask_user 类（必须许可）**：

```markdown
## 🟡 需要您确认：{title}

- **触发信号**：{trigger_signal}
- **影响分级**：{impact_grade} / 依据强度：{evidence_strength}
- **依据**：
  {evidence 列表}
- **建议落地**：
  | 文件 | 变更类型 | 变更摘要 |
  |---|---|---|
  | ... | edit/add | ... |
- **风险与回滚**：{回滚方法}
- **选项**：
  - **A 全部应用**（推荐）
  - **B 部分应用**（请指定哪些）
  - **C 不应用，仅记录到否决清单**
  - **D 暂缓**（等更多反馈）
```

---

## 4. 落地执行（分级处理）

### 4.1 静默执行清单（auto_apply）

满足下列**全部**条件才允许静默执行：

1. `default_action == auto_apply`
2. 文件存在且可写
3. 写入是「追加」或「局部修改」（非整页覆盖）
4. 修改后能跑通 `wiki-lint-agent`（L1-L4 全 PASS 或仅 WARNING，无 FAIL）

执行流程：

```
1. 读取目标文件
2. 应用 diff（Edit 工具）
3. 立即跑 wiki-lint（限定 L1+L3）
4. 若 LINT 通过：
   - 追加 wiki/log.md 一条 [自进化] 记录
   - 追加 .agent-cache/memory/YYYY-MM-DD.md 一条会话内记录
   - 用 auto_apply 模板向用户报告
5. 若 LINT 失败：
   - 立即回滚到修改前（Edit 工具反向）
   - 降级为 ask_user，重新走流程
```

### 4.2 用户许可流程（ask_user）

```
1. 用 ask_user 模板向用户呈现提案
2. 等用户回复（A/B/C/D）
3. 收到回复后：
   - A → 走 §4.1 静默执行流程
   - B → 按用户指定子集走 §4.1
   - C → 写入 .agent-cache/memory/neg-vetoes.json（永不静默触发）
   - D → 写入 .agent-cache/memory/deferred-proposals.json（带 validUntil）
```

### 4.3 禁止清单（forbidden）

直接告知用户「该操作被硬约束禁止」，不进入提案流程：

- 修改 `raw/` 下任何文件
- 修改 `CLAUDE.md` 第 1-11 条硬性规则
- 删除任何文件

---

## 5. 关键文件与角色改造

> 本节是「方案 → 实施」阶段的具体落点。如用户批准本方案，再按本节改造文件。

### 5.1 新增文件

| 路径 | 用途 |
|---|---|
| `wiki/domains/agent-design/evolution-policy.md` | 本文档（已创建，待评审） |
| `wiki/domains/agent-design/auto-apply-trace.md` | auto_apply 类执行的累计留痕（每周一清理 > 30 天条目） |
| `.agent-cache/memory/neg-vetoes.json` | 用户否决清单，永久生效，结构：`{proposal_id, signal_keyword, rejected_at, reason}` |
| `.agent-cache/memory/deferred-proposals.json` | 延期提案清单，结构：`{proposal_id, deferred_at, validUntil, reason}` |
| `.agent-cache/memory/proposals/pending-{proposal_id}.json` | 提案暂存，等用户回复期间不丢 |

### 5.2 修改文件

| 路径 | 改造内容 | 风险等级 |
|---|---|---|
| `.claude/agents/picturebook-creator-agent.md` | 新增「Step 0：进化评估」+ 触发器表 + 提案生成 + §4.1/4.2/4.3 流程 | 中 |
| `wiki/domains/agent-design/MEMORY.md`（项目级） | 记录本方案的简版原则 + 触发词清单（与 `.agent-cache/memory/MEMORY.md` 不同，这是项目级） | 低 |
| `wiki/log.md` | 标记方案上线节点（执行时才追加） | 低 |
| `wiki/index.md` | 增加 `domains/agent-design/` 导航（执行时才追加） | 低 |
| `CLAUDE.md` | 在「硬性规则」之后增加「§自进化规则」段，引用 `evolution-policy.md` | 中 |

> **注意**：`CLAUDE.md` 改动属于"硬性规则文件"周边的辅助段落（不修改硬性规则本身），按本方案仍按"ask_user"处理。

### 5.3 不修改文件

- `.claude/agents/{research,creative,quality,illustration,wiki-ingest,wiki-lint}-agent.md`：行为定义由 `picturebook-creator-agent` 的进化评估统一调度，子 Agent 不内嵌进化逻辑（保持职责单一）。
- `.claude/skills/*/SKILL.md`：进化机制本身不放在 Skill 里，由主编 Agent 主导。
- `schema/quality-checks/*.md`：本身是「被进化对象」，但其变更必须经用户确认（已在 §1 表中标 medium/large）。

---

## 6. 防失控机制

### 6.1 双层熔断

| 维度 | 阈值 | 触发后行为 |
|---|---|---|
| 单次会话 auto_apply 次数 | > 5 次 | 立即降级为 ask_user，后续提案一律走许可 |
| 单次会话 wiki/log.md 追加次数 | > 20 条 | 同上 |
| 同一 proposal_id 在 7 天内被回滚 ≥ 2 次 | 触发 | 暂停该类型自进化 30 天，提示用户 |
| 提案的 evidence 字段为空 | 触发 | 一律走 ask_user，evidence 不允许空 |
| 提案涉及 `CLAUDE.md` 任何段落 | 触发 | 一律 ask_user，且模板标注「⚠️ 涉及主控规则」 |

### 6.2 审计回看

用户随时可说"列出本会话所有自进化记录"或"回滚 prop-xxx"：

- 列出 → 汇总 `wiki/log.md` 内 `[自进化]` 标记 + `.agent-cache/memory/proposals/`
- 回滚 → 读取提案中的 `applied_diff`，用 Edit 反向操作，并新增一条 `[自进化回滚]` 记录

### 6.3 否决优先

`.agent-cache/memory/neg-vetoes.json` 中任何条目永久生效，除非用户主动撤销。即使后续有更多类似信号，也必须 ask_user。

---

## 7. 实施路线图（建议 3 阶段）

### Phase 1：基础设施（建议先做）

1. 创建 `wiki/domains/agent-design/` 目录
2. 落地本文档作为 `evolution-policy.md` v1
3. 创建 `.agent-cache/memory/{neg-vetoes,deferred-proposals}.json`（空数组结构）
4. 不修改任何 Agent 文件，先以"主编 Agent 内部流程"方式手工跑通 1-2 个示例

**验收**：能在 1 次对话里跑完 auto_apply 全流程（提议 → 评估 → 落地 → 写 log → 通知），且 wiki-lint 仍 PASS。

### Phase 2：主编 Agent 改造

1. 修改 `picturebook-creator-agent.md`：增加 Step 0 进化评估 + 触发器表
2. 不修改子 Agent
3. 跑通 3 个示例：1 个 auto_apply + 1 个 ask_user + 1 个 forbidden

**验收**：3 个示例的输出与本文档 §3.3 模板完全一致。

### Phase 3：CLAUDE.md 落地与全量验证

1. 在 `CLAUDE.md` 增加「自进化规则」段落，引用本方案
2. 用 `wiki-lint-agent` 跑一次全量 L1-L4
3. 用 demo2 脚本回归一次，确认自进化未污染已有工作流

**验收**：`wiki-lint-agent` 全 PASS（无新增 FAIL），demo2 端到端跑通。

---

## 8. 与现有机制的关系

| 现有机制 | 与本方案的关系 |
|---|---|
| **CLAUDE.md 硬性规则** | 本方案不修改，但新增段落引用本方案 |
| **wiki-ingest v3 置信度分级** | 本方案中 Wiki 写入同样遵循四级置信度（unverified / cross-validated / feedback-confirmed / human-approved） |
| **P2-4 半自动修复** | 半自动修复是「单次质检 FAIL 的处理」，本方案是「跨会话持续校准」。两者互不冲突，半自动修复仍由主编工作流 B Step 4.5 负责 |
| **`.agent-cache/memory/` 会话记忆** | 会话结束时批量跑一次「进化评估」，是隐式信号的来源与输入数据 |

---

## 9. 开放问题（用户已决策 6/6）

> 本节在 v1 评审后由用户决策，落地为 v1.1。每条决策同时给出「决策结论 + 决策依据 + 落地动作」。

### 9.1 静默执行的告知时机 ✅ 已决策

**结论**：双阶段告知 —— **每次 auto_apply 立即告知 + 会话结束时再次统一汇总**。

**决策依据**：
- 每次立即告知 → 用户对单条进化的"知情度"最高，符合 §0.2 第 5 条"告知"硬约束
- 会话结束再汇总 → 用户能在一次对话复盘里看到完整自进化清单，方便审计
- 不只选一种的原因：单条粒度的告知会被大量其他输出"淹没"；纯汇总告知又违背"实时知情"

**落地动作**：
- §3.3 auto_apply 模板**保持不变**（每条立即告知）
- 新增「**会话结束自进化汇总模板**」：

  ```markdown
  ## 📋 本会话自进化汇总

  本会话共发生 N 次自进化（M 次 auto_apply + K 次 ask_user + 0 次 forbidden）：

  | # | 时间 | 类型 | 提案 | 影响 | 依据 |
  |---|---|---|---|---|---|
  | 1 | HH:MM | auto_apply | 简短标题 | small | 一句话依据 |
  | 2 | HH:MM | ask_user | 简短标题 | medium | 一句话依据（您已回复 B） |
  | ... | ... | ... | ... | ... | ... |

  详细 diff：wiki/log.md 自本会话起至末尾的 `[自进化]` 标记
  ```

- 主编 Agent 在会话结束时插入「自进化汇总」步骤，从 `.agent-cache/memory/proposals/` 提取本次会话所有 proposal
- 汇总模板本身**也走 auto_apply**（属于会话级产物）

### 9.2 否决清单是否入 `wiki/` ✅ 已决策（关键决策）

**结论**：**双轨制** ——
- **否决事实**入 `wiki/domains/agent-design/neg-vetoes.md`（项目级公开 Wiki）
- **否决全文细节**留在 `.agent-cache/memory/neg-vetoes.json`（仅主编 Agent 可读）

**为什么双轨，而不是单选**：
- 单选 memory → 团队成员看不到，不利于协作（CLAUDE.md 第 1 条「本知识库是供外部智能体系统读取的」）
- 单选 wiki → 暴露过多上下文，可能让用户「不雅」的决定被永久公开（如"这个 IP 钩子太土了"）
- 双轨 → 既保留审计可见性，又保护决策细节隐私

**`wiki/domains/agent-design/neg-vetoes.md` 内容形态**：

```markdown
# 用户否决记录

> 本页是公开的否决事实摘要，详细 JSON 留在 `.agent-cache/memory/neg-vetoes.json`（仅主编 Agent 可读）。
> 维护规则：仅追加，不修改，不删除（与 `wiki/log.md` 一致）。

| 否决时间 | 提案 ID | 信号关键词 | 否决原因（用户原话 / 脱敏） | 撤销方式 |
|---|---|---|---|---|
| 2026-07-06 | prop-001 | "默认加 IP 钩子" | "当前项目不需要" | 说"撤销否决 prop-001" |
| ... |
```

**`neg-vetoes.json` 详细 JSON 结构**（保留 7 天内的完整 diff + 用户原话）：

```json
{
  "vetoes": [
    {
      "proposal_id": "prop-2026-07-06-001",
      "rejected_at": "2026-07-06T15:20:00+08:00",
      "signal_keyword": "默认加 IP 钩子",
      "user_quote": "当前项目不需要 IP 钩子，太商业化了",
      "scope": "wiki/projects/demo/content-spec.md",
      "user_visible_reason": "当前项目不需要",
      "expires_at": "2026-07-13T15:20:00+08:00"
    }
  ]
}
```

**落地动作**：
- 新增 `wiki/domains/agent-design/neg-vetoes.md`（Phase 1 创建，初始为空表头）
- 主编 Agent 收到用户"否决"回复时，**双写**：JSON 全文入 memory + 脱敏摘要入 wiki
- 否决内容**自动 7 天后从 memory 清理**（防止长尾堆积），但 wiki 摘要**永久保留**
- 7 天后再次出现同类信号：检测 `neg-vetoes.json` 已无，但 `wiki/neg-vetoes.md` 仍在 → 走 ask_user，模板里**主动呈现历史否决摘要**（避免重复打扰用户）

**影响**：
- ✅ 协作友好：团队成员 / 其他 Agent 启动时读 `wiki/neg-vetoes.md` 即可知道"哪些方向被否过"
- ✅ 隐私保护：用户原话不公开，仅"脱敏原因"上线
- ✅ 自我学习：7 天后仍能从 wiki 摘要里反推，避免重复打扰
- ⚠️ 微小复杂度：双写逻辑 + 7 天 memory 清理任务，需在 Phase 1 实现

### 9.3 Phase 1 是否先完整跑通 ✅ 已决策

**结论**：**必须先做一次完整跑通**，不通过则不进入 Phase 2。

**决策依据**：
- v1 描述的"auto_apply 全流程"在跑通前是"纸面规则"，实际可能踩到 wiki-lint 失败、JSON 写入冲突、log.md 重复追加等细节
- 没有"端到端跑通证据"就进入 Phase 2 改 Agent，会把流程 bug 固化进 Agent 行为

**Phase 1.5 新增任务**（在原 Phase 1 与 Phase 2 之间）：

1. **跑通场景 1（auto_apply）**：用"补一条 wiki/log.md"的真实场景走完全流程
   - 验收：log.md 出现 [自进化] 标记、wiki-lint 仍 PASS、auto-apply-trace.md 有记录
2. **跑通场景 2（ask_user）**：用"改质检项 target 阈值"的真实场景走完全流程
   - 验收：呈现提案 → 用户回复 A → 落地 + 写 log
3. **跑通场景 3（forbidden）**：用"改 raw/ 下文件"的真实场景触发拒绝
   - 验收：拒绝消息引用 §1 forbidden 条款，无任何文件被修改
4. **跑通场景 4（veto + 二次触发）**：先否决一类信号，7 天内（模拟）再触发同类信号
   - 验收：第二次触发走 ask_user，模板呈现历史否决摘要

**只有 4 个场景全部跑通且无 wiki-lint FAIL 才进入 Phase 2。**

**Phase 1.5 验收产物**：
- `wiki/domains/agent-design/runs/phase1.5-{date}.md` —— 每个场景的完整过程记录
- 这 4 个 run 文件本身**不被 `wiki-lint` 检查**（临时运行记录，不进正式知识库），落地到 `wiki/domains/agent-design/runs/` 子目录

### 9.4 `auto-apply-trace.md` 清理策略 ✅ 已决策

**结论**：**按 proposal_id 去重保留最新版**，不按时间清理。

**决策依据**：
- 时间清理（30 天）会丢失历史 audit 链：用户问"3 个月前我同意过什么"，查不到
- proposal_id 去重可以保证：同一 proposal_id 的所有状态（pending / applied / rolled-back）合并成最新一条，保留完整生命周期
- 30 天清理的初衷是"避免 trace 文件膨胀"，用去重即可达成同等效果

**trace 文件结构**（按 proposal_id 唯一键）：

```markdown
# Auto-apply 留痕

> 仅记录 auto_apply 类型的执行。ask_user 走 wiki/log.md，forbidden 不留痕。
> 维护规则：按 proposal_id 去重，同一 ID 多次出现时**覆盖**为最新状态（不修改历史事实，仅更新状态字段）。

| proposal_id | 时间 | 触发信号 | 影响 | 落地文件 | 状态 | 状态变更时间 |
|---|---|---|---|---|---|---|
| prop-001 | 2026-07-06 15:20 | "格式不对" | small | wiki/index.md | applied | 2026-07-06 15:20 |
| prop-001 | 2026-07-06 16:00 | 同上 | small | wiki/index.md | rolled-back | 2026-07-06 16:30 |
| prop-002 | ... | ... | ... | ... | applied | ... |
```

**清理策略**：
- **不主动按时间清理**
- 仅当 trace 行数 > 200 时，**保留最近 100 条**（按"状态变更时间"排序）
- 回滚条目**永久保留**（不计入 100 条配额）—— 回滚本身就是审计关键证据

**落地动作**：
- 主编 Agent 维护一个 in-memory map：proposal_id → 最新状态
- 每次状态变更（applied / rolled-back）用 Edit 工具**精准修改**对应行（非追加）
- 200 条阈值检测在每次写入前跑一次

### 9.5 隐式信号检测是否加缓存 ✅ 已决策

**结论**：**加缓存**，缓存策略复用 `research-agent` v1 P1-3 的 `.agent-cache/cache/research-cache.json` 模式。

**决策依据**：
- 隐式信号检测（grep 错误关键词、统计质检降级率、扫描 `.agent-cache/memory/`）是 IO 密集型
- 每次会话结束都全量跑一次，N 次会话 = N 次扫描，成本高
- 缓存能避免重复扫描，但**缓存过期策略**比 research 复杂（research 只看 mtime，隐式信号还要看"信号量是否变化"）

**缓存设计**：

| 字段 | 类型 | 说明 |
|---|---|---|
| `cache_path` | `.agent-cache/cache/implicit-signal-cache.json` | 缓存文件路径 |
| `cache_key` | string | `sha256(.agent-cache/memory/ 目录树 + active.json 内容 + log.md 末尾 100 行)` |
| `cache_value` | object | `{detected_signals: [...], last_scan_at: timestamp, scan_cost_ms: number}` |
| `invalidation` | 三种 | (1) cache_key 不匹配 → 全量重扫 (2) 用户说"刷新隐式信号" → 强制重扫 (3) 距上次扫描 > 24h → 强制重扫 |

**触发条件**：
- 会话结束前执行隐式信号扫描
- 命中缓存 → 直接返回 `detected_signals`，耗时 < 100ms
- 未命中 → 全量扫描 + 写缓存，耗时可达数秒（首次）

**与 research 缓存的关系**：
- 不复用同一文件（关注点不同：research 关注 wiki 内容，implicit-signal 关注会话记忆 + 行为模式）
- 但用同样的 mtime / hash 比对模式
- 同一目录（`.agent-cache/cache/`）便于统一管理

**落地动作**：
- Phase 1 创建 `.agent-cache/cache/implicit-signal-cache.json`（空结构）
- Phase 2 在主编 Agent 中加「Step -0.5 隐式信号扫描」，与 research 缓存同位置
- 不新建 Skill，把扫描逻辑直接放在主编 Agent（保持职责单一原则）

### 9.6 「影响大」的判定边界 ✅ 已决策

**结论**：**以"是否影响其他 Agent 的 I/O Contract"作为核心判定标准**，辅以 2 条辅助标准。

**决策依据**：
- v1 提议的"是否影响其他 Agent 的 I/O Contract"是核心但不够 —— 例如修改 creative-agent 的 prompt 模板不影响 I/O Contract，但实际行为变化大
- 需要一个**组合判定**，让 Agent 内部可计算

**判定三标准**（满足任一即 large）：

1. **I/O Contract 影响**（核心）
   - 改动会导致其他 Agent 的输入/输出字段变化？（如加/减字段、改字段名、改类型）
   - 改动会让 I/O Contract 的 `required` 标记改变？
2. **多 Agent 共享**（辅助）
   - 该文件被 ≥ 2 个其他 Agent 引用？（如 `illustration-spec.md` 被 illustration-agent + creative-agent + 质检项同时引用）
3. **质检语义**（辅助）
   - 改动会让 ≥ 1 个 active_checks 的语义失效？（如改 `severity`、`fail_action` 含义）

**决策树**（在 §3.2 算法中插入）：

```text
IF 改动命中 I/O Contract 影响 OR 多 Agent 共享 OR 质检语义
    → impact_grade = large
    → default_action = ask_user（且模板标注「⚠️ 跨 Agent 影响」）
ELSE
    → 走原 §3.2 三维评分
```

**典型场景示例**：

| 改动 | 命中 | 判定 |
|---|---|---|
| 修改 picturebook-creator-agent 的 Step 顺序 | 否（不影响子 Agent I/O） | small / ask_user（按三维评分） |
| 给 creative-agent 增加 `user_constraints` 字段 | ✅ I/O Contract | large / ask_user |
| 修改 `illustration-spec.md` §4 | ✅ 多 Agent 共享 | large / ask_user |
| 修改 `active.json` 的 `text/lexile` 阈值 | ✅ 质检语义 | large / ask_user |
| 修改子 Agent 的 prompt 措辞 | ❌（不影响 I/O） | 走三维评分 |
| 修改 wiki/projects/demo/content-spec.md | ❌（项目级，单 Agent 用） | small / auto_apply |

**落地动作**：
- 在 §3.2 算法前增加决策树 §3.2.1（命名"跨 Agent 影响快筛"）
- 主编 Agent 在生成 proposal 时跑此快筛，结果写入 proposal 的 `cross_agent_impact: boolean` 字段
- 模板里命中 large 的提案自动追加 ⚠️ 标记

---

## 10. 决策落地清单（v1.1 增量）

| 决策 | 影响的文档段落 | 状态 |
|---|---|---|
| 9.1 双阶段告知 | §3.3（新增会话结束模板）、§7 Phase 1.5 | 待回写 |
| 9.2 双轨制否决 | §5.1（新增 `wiki/domains/agent-design/neg-vetoes.md`）、§4.2、§6.3 | 待回写 |
| 9.3 Phase 1.5 端到端跑通 | §7（新增 Phase 1.5 子阶段） | 待回写 |
| 9.4 trace 按 proposal_id 去重 | §5.2（trace 文件结构）、§4.1 | 待回写 |
| 9.5 隐式信号加缓存 | §2.2（新增缓存设计）、§5.1（新增 `implicit-signal-cache.json`） | 待回写 |
| 9.6 large 判定 = I/O + 共享 + 语义 | §3.2（新增 §3.2.1 快筛决策树） | 待回写 |

---

**文档版本**：v1.1（2026-07-06 15:20）
**变更说明**：6 个开放问题全部决策，新增 §10 决策落地清单，下一步：用户确认 v1.1 后回写各段到正文。

