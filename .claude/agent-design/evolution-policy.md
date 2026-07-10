---
title: "Agent 自我进化方案"
summary: "设计儿童绘本智能体的自我进化能力。根据用户对话反馈主动发起提案，分级处理对 Agent 配置 / 原始资料 / Wiki / Skill / Schema 等内容的更新。影响小且有明确依据的可静默更新 + 告知；影响大或仅是建议的必须经用户确认。"
source: "用户提案"
version: 2
---

# Agent 自我进化方案（v2，瘦身版）

> 状态：**已落地 v2**（2026-07-08 瘦身，砍掉纸面机制，保留真实抓过 bug/被验证有用的部分）。v1.1 的完整历史设计与 6 项开放问题决策见本文件 §7「历史摘要」，不再逐条展开。
>
> 位置说明：本文件与 `neg-vetoes.md` 于 2026-07-08 从 `wiki/domains/agent-design/` 迁移到 `.claude/agent-design/`——二者是 Agent 系统的治理文档，不是绘本创作的领域知识，迁移后与 `wiki/log.md`（纯知识库日志）、`.claude/log.md`（系统变更日志）的分工保持一致。
>
> 适用范围：本项目的整套智能体系统（CLAUDE.md / .claude/agents/* / .claude/skills/* / schema/* / wiki/* / raw/* / data_collect/*）。

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
          → 记录到日志（变更留痕，见 §0.2 第 4 条的分流规则）
            → 通知用户（已完成 / 已应用 / 已降级）
```

### 0.2 硬约束

1. **保护 `raw/`**：原始资料只增不改（与 `schema/lint-rules.md` 一致），进化流程不修改 `raw/` 下任何文件。
2. **不修改 `CLAUDE.md` 的硬性规则段落**（如语言规则、版本化规则、质检可插拔规则等），如有冲突的提案升级到用户层确认。
3. **不删除任何文件**：所有进化都是「新增或修改」，删除必须经用户明确同意。
4. **进化可追溯，按内容分流记录**：
   - 改动的是 `wiki/domains/` 或 `wiki/projects/` 下的知识内容 → 记入 `wiki/log.md`
   - 改动的是 Agent / Skill / Schema / `CLAUDE.md` / hooks 等系统本身 → 记入 `.claude/log.md`
   - 每条记录注明「提案来源 / 触发信号 / 决策依据 / 落地 diff 摘要」——这两个文件是**唯一**的留痕落点，不再维护单独的 trace 文件
5. **进化方向不可绕过用户否决**：用户说「不同意 / 不要改」则该次提案永久归档于 `.claude/agent-design/neg-vetoes.md`，不再触发同类自动落地（除非用户后续主动撤销否决）。

---

## 1. 进化作用域地图

把智能体系统按典型文件归类，明确每类的默认处理策略。这张表覆盖了实际会遇到的几乎所有场景，不需要额外的数值公式。

| 作用域 | 典型文件 | 默认处理 | 用户是否需要确认 |
|---|---|---|---|
| **会话级缓存** | `.agent-cache/cache/research-cache.json` | 静默写入 | ❌ |
| **临时产物** | `.agent-cache/cache/` 下其他 JSON、`.agent-cache/memory/YYYY-MM-DD.md` | 静默写入 | ❌ |
| **质检配置开关** | `schema/quality-checks/active.json`（`active_checks` / `_inactive_checks` 增删条目） | **需许可** | ✅ |
| **质检规则文件** | `schema/quality-checks/**/*.md` | **需许可** | ✅ |
| **Agent 行为定义** | `.claude/agents/*.md`（工作流步骤、I/O Contract、Constraints） | **需许可**（含 diff 预览 + 回滚命令，见 §4.2） | ✅ |
| **Skill 行为定义** | `.claude/skills/*/SKILL.md` | **需许可**（含 diff 预览 + 回滚命令，见 §4.2） | ✅ |
| **Wiki 知识库（项目）** | `wiki/projects/{id}/*.md`（增量条目 / 修正记录 / 置信度升级） | 静默更新 + 告知 | ❌ |
| **Wiki 知识库（领域）** | `wiki/domains/*/*.md` | **需许可** | ✅ |
| **Wiki 索引/日志** | `wiki/index.md` / `wiki/log.md` | 静默追加 + 告知 | ❌ |
| **Agent 系统日志** | `.claude/log.md` | 静默追加 + 告知 | ❌ |
| **质检规则目录元数据** | `schema/quality-checks/README.md` | **需许可** | ✅ |
| **新 Agent / 新 Skill** | `.claude/agents/*.md` / `.claude/skills/*/SKILL.md`（新增） | **需许可** | ✅ |
| **`raw/` 文件** | `raw/**/*` | **禁止** | — |
| **`CLAUDE.md` 硬性规则** | `CLAUDE.md` 第 1-11 条硬性规则 | **禁止** | — |

**跨 Agent 影响快筛**（命中任一即视为需许可 + 提案模板标注 ⚠️「跨 Agent 影响」，即使作用域地图本身已判定需许可，这条也用来给 ask_user 提案加重要性标注）：

1. 改动会导致其他 Agent 的 I/O Contract 字段变化（加/减字段、改字段名、改 `required` 标记）
2. 该文件被 ≥2 个 Agent 引用（如 `illustration-spec.md`）
3. 改动会让 ≥1 个 `active_checks` 项的语义失效（如改 `severity`、`fail_action` 含义）

> **决策原则一句话**：命中作用域地图的"需许可"行，或命中上面 3 条快筛任一条 → `ask_user`；命中"禁止"行 → `forbidden`；其余 → `auto_apply`。不再需要额外的数值打分。

---

## 2. 反馈信号识别（触发器）

智能体在对话中识别以下**显式信号**（用户直接表达）时启动「进化评估」：

| 触发词 / 句式 | 含义 | 默认处理 |
|---|---|---|
| "这个规则可以改成 ……" | 规则优化建议 | 触发：方案 → 评估 → 提案 |
| "加一个 / 去掉一个质检项" | 质检配置变更 | 触发：方案 → 评估 → 提案 |
| "以后默认就 ……" | 行为偏好固化 | 触发：偏好入对应作用域文件（新建需许可） |
| "下次别再 ……" | 反向偏好（否决类） | 触发：归档到 `.claude/agent-design/neg-vetoes.md`（需许可，走 §4 ask_user 的 C 分支） |
| "我刚发现 ……" / "刚才 ……" | 实战反馈 | 触发：写入对应日志的实战反馈节（静默） |
| "写得太啰嗦 / 格式不对" | 输出风格修正 | 触发：影响范围评估，提案可能涉及 `CLAUDE.md` 语言规则（需许可） |
| "日志 / 索引漏更新了" | 流程遗漏报告 | 触发：补写 + 标记漏更链路（静默） |
| "这个 raw/ 文件有问题" | 原始资料问题 | **禁止**改 `raw/`，改为"建议重新摄入"提案（需许可） |

> 只识别显式信号。曾设计过的"隐式行为模式检测"（跨会话统计重复错误/降级率等）从未被任何 Skill 实际接入过（`session-export` Skill 全文不引用它），属于纯纸面机制，v2 已移除。如未来真的需要，按显式信号的模式重新设计并先跑通一个真实场景再落地。

---

## 3. 提案生成（核心环节）

### 3.1 提案数据结构

```json
{
  "proposal_id": "prop-{date}-{seq}",
  "trigger_signal": "用户原话摘录",
  "signal_keyword": "归一化关键词",
  "evidence": "依据描述（不可为空，为空一律 ask_user）",
  "scope_files": ["目标文件路径"],
  "cross_agent_impact": true,
  "default_action": "auto_apply | ask_user | forbidden",
  "applied_diff": "变更摘要"
}
```

### 3.2 判定流程

```text
IF scope_files 命中 CLAUDE.md 第 1-11 硬性规则段落 OR raw/ 下任何文件
    → forbidden
ELSE IF scope_files 命中 §1 作用域地图「需许可」行 OR 命中 §1 跨 Agent 影响快筛任一条
    → ask_user（命中快筛时提案标注 ⚠️「跨 Agent 影响」）
ELSE
    → auto_apply
```

### 3.3 提案输出模板

**auto_apply 类（静默执行 + 告知）**：

```markdown
## 🟢 已应用：{title}

- **触发信号**：{trigger_signal}
- **依据**：{evidence 摘要}
- **落地 diff 摘要**：
  - `{file_path}`: {change_summary}
  - ...
- **下一步**：已更新日志记录本次自进化（{proposal_id}）。如需回滚请说"回滚 {proposal_id}"。
```

**ask_user 类（必须许可）**：

```markdown
## 🟡 需要您确认：{title}

- **触发信号**：{trigger_signal}
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
  - **D 暂缓**（不做持久化跟踪，之后重新提起即可）

> 若本次改动涉及 `.claude/agents/*.md` 或 `.claude/skills/*/SKILL.md` 自身定义，本提案必须额外附上逐行 diff + 具体回滚命令（见 §4.2）。
```

---

## 4. 落地执行（分级处理）

### 4.1 三分支执行流程

**auto_apply**：
```
1. 读取目标文件
2. 应用 diff（Edit 工具，仅追加/局部修改）
3. 跑 wiki-lint（限定 L1+L3，仅当改动涉及 wiki/ 时）
4. 通过 → 按 §0.2 第 4 条分流追加 [自进化] 记录（wiki/log.md 或 .claude/log.md）→ 立即告知用户
5. 失败 → 立即回滚 + 降级为 ask_user
```

**ask_user**：
```
1. 按 §3.3 模板呈现提案（A/B/C/D 四选一 + 回滚方式）
2. 等用户回复
3. A → 走 auto_apply 流程 / B → 按子集走 auto_apply 流程 / C → 追加一行到 neg-vetoes.md / D → 不做记录，结束本轮
```

**forbidden**：
```
直接告知用户「该操作被硬约束禁止」：
- 修改 raw/ 下任何文件
- 修改 CLAUDE.md 第 1-11 条硬性规则
- 删除任何文件
拒绝消息含 3 条替代方案：重新摄入 / 新增反馈文件 / 走 wiki/projects/ 增量更新
```

### 4.2 修改 Agent/Skill 定义文件的强制 diff 预览

当 `scope_files` 命中 `.claude/agents/*.md` 或 `.claude/skills/*/SKILL.md` 时，ask_user 提案必须额外满足：

1. 附上实际逐行 diff（旧文本 vs 新文本），不能只用一句话摘要替代
2. 回滚方式给出具体命令，例如：
   ```
   git diff .claude/agents/{name}.md        # 查看改动
   git checkout -- .claude/agents/{name}.md # 撤销改动（未提交前）
   ```
3. diff 或回滚命令缺失时，不得进入 A（auto_apply）执行

### 4.3 否决记录

用户选 C（否决）时，追加一行到 `.claude/agent-design/neg-vetoes.md`：

```markdown
| 否决时间 | 提案 ID | 信号关键词 | 否决原因（脱敏） |
|---|---|---|---|
| 2026-07-06 | prop-001 | "默认加 IP 钩子" | 当前项目不需要 |
```

这是**唯一**的否决记录来源，永久生效（不设过期时间），除非用户主动说"撤销否决 {proposal_id}"。同类信号再次出现时，evolution-agent 检测到本表已有记录 → 走 ask_user，提案中主动呈现历史否决摘要。

---

## 5. 熔断保护

| 触发条件 | 响应 |
|---|---|
| 单次会话 auto_apply > 5 次 | 降级为 ask_user |
| 单次会话日志追加 > 20 条（wiki/log.md + .claude/log.md 合计） | 同上 |
| 提案 `evidence` 字段为空 | 一律 ask_user |
| 涉及 `CLAUDE.md` 任何段落 | 一律 ask_user（标注 ⚠️） |

状态存于 `.agent-cache/memory/circuit-breaker.json`（`session.auto_apply_count` / `session.log_append_count`），文件不存在时视为全零并自动创建。

> v1.1 曾设计"同一 proposal_id 7 天内回滚 ≥2 次 → 暂停该类型 30 天"，需要跨会话持续追踪单个提案的回滚历史。这个项目从未出现过一次回滚记录，规则从未被真正触发过，v2 已移除；如未来真的遇到反复回滚同一提案的情况，再按实际发生的场景补规则。

---

## 6. 与现有机制的关系

| 现有机制 | 与本方案的关系 |
|---|---|
| **CLAUDE.md 硬性规则** | 本方案不修改，但新增段落引用本方案 |
| **wiki-ingest 置信度分级** | 本方案中 Wiki 写入同样遵循四级置信度（unverified / cross-validated / feedback-confirmed / human-approved） |
| **半自动修复** | 半自动修复是「单次质检 FAIL 的处理」，本方案是「跨会话持续校准」。两者互不冲突，半自动修复仍由主编工作流 B Step 4.5 负责 |
| **`session-export` Skill** | 与本方案无耦合（v1 曾设想的"隐式信号批量扫描"从未接入，已移除相关设计） |

---

## 7. 历史摘要（v1.1 → v2 瘦身记录）

v1.1（2026-07-06 定稿）在本方案基础上还包含以下机制，2026-07-08 复盘后确认为"设计了但从未被真实场景验证/收益不成比例"，予以移除，详细历史不再展开，仅存此摘要供追溯：

- **3 维数值打分**（影响半径×可逆性×依据强度，各 0-2 分求和）：4 个 Phase 1.5 验收场景全部直接命中作用域地图分支，从未真正走到数值公式
- **隐式信号检测 + 24h 缓存**：`session-export` Skill 从未接入，纯纸面设计
- **会话结束自进化汇总**：与"每次 auto_apply 立即告知"功能重叠
- **否决双轨制**（`neg-vetoes.json` 7 天过期 + `neg-vetoes.md` 永久）：单用户项目无团队协作场景，判断始终基于 wiki 页面，json 侧从未真正参与决策
- **auto-apply-trace.md 独立留痕文件**：与知识/系统日志的 `[自进化]` 记录完全重复，且要求"按 proposal_id 精确定位行覆盖式 Edit"这种脆弱操作，已删除该文件，历史 3 条记录并入 2026-07-08 的日志条目

Phase 1→2→3 的实施过程记录（PoC 跑通 4 个场景、`.agent-cache/memory/runs-archive/` 下的 10 个 run 文件）仍然是真实发生过的验证证据，不受本次瘦身影响，继续保留在 `.agent-cache/memory/runs-archive/`。

---

**文档版本**：v2（2026-07-08）
**变更说明**：在 v1.1 基础上砍掉未被验证/收益不成比例的治理机制（详见 §7），保留作用域地图、显式信号、三分支执行、单轨否决、简化熔断。多 Agent 架构、主线创作工作流、全部 Skill 均不受影响。同日随 `neg-vetoes.md` 一起从 `wiki/domains/agent-design/` 迁移到 `.claude/agent-design/`，并同步补充日志分流规则（wiki/log.md vs .claude/log.md）。
