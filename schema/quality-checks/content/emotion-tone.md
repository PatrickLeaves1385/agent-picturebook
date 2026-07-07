---
id: "content/emotion-tone"
category: "content"
severity: "error"
method: "semantic"
target: "正向/负向词比 >= 2.0；禁止词命中 = 0"
skill: null
fail_action: "block"
priority: "project-overridable"
description: "审查脚本的情感基调。量化锚点：1) 正向/负向情绪词比例；2) 禁止词命中数；3) 转机与结尾达标情况。具体约束与词表从 wiki-context 或用户输入中提取。"
---
# 情感基调审查

## 量化锚点（v2 新增）

每页按以下 3 维度量化打分，**先看量化分，再做 LLM 语义审查微调**：

### 维度 1：正向/负向词比例（自动统计）

| 词表来源 | 范围 |
|---|---|
| 通用正向词表 | happy/smile/play/laugh/friend/love/brave/try/joy/fun/warm/sunny/bright 等 |
| 通用负向词表 | sad/cry/scared/angry/alone/afraid/dark/hate/lose/fail/hurt 等 |
| 项目扩展词表 | wiki-context 中 content-spec 定义的情感关键词（如有） |

- 用 Grep 统计全文正向词 / 负向词次数
- **比例 = 正向次数 / max(负向次数, 1)**
- 比例 >= 2.0 → 该维度 PASS
- 比例 < 2.0 但 >= 1.0 → WARNING
- 比例 < 1.0 → FAIL

### 维度 2：禁止词命中（硬阻断）

禁止词表（恒定底线，定义在 illustration-spec.md §6 的情感类禁用词）：
- 恐惧：scared/afraid/terrified
- 悲伤：sad/crying/weep
- 愤怒：angry/hate
- 暴力：hurt/pain/fight

**全文禁止词命中数 = 0** → 该维度 PASS
**命中 >= 1 次** → FAIL（必须修改）

### 维度 3：转机 + 结尾达标（基于页面结构）

| 检查项 | 规则 |
|---|---|
| 转机页存在 | 末页的前 N-1 页中至少 1 页出现主动尝试/突破/学习关键词 |
| 结尾基调 | 末页正向词 >= 2 且 禁止词 = 0 |

## 判定综合

| 综合结果 | 条件 |
|---|---|
| ✅ PASS | 维度1 PASS + 维度2 PASS + 维度3 全通过 |
| ⚠️ WARNING | 维度1 WARNING 且其他维度 PASS |
| ❌ FAIL | 任意维度 FAIL |

## 检测方法

1. 读目标文件 + 读 wiki-context 提取项目情感约束
2. **先执行 quality-agent Step 2.6 文本预处理**（剥离 `> ` 引用块/HTML 注释/YAML frontmatter），避免人工注释中的"⚠️ 触发 basic-safety"等自指描述干扰判定
3. 用 Grep 自动统计维度1/2（客观信号，无需 LLM）
4. 用 LLM 审查维度3 + 综合判定微调（处理歧义、补充项目特有情感约束）

## 检测方法（原语义审查部分保留）

- 从 wiki-context 中提取项目的情感基调要求
- 如 wiki 和用户均未定义情感基调约束，此检测自动跳过
- 定义了约束时，逐页审查是否符合

## 常见绘本情感约束参考

以下为常见约束类型示例，实际检测以 wiki-context 中的定义为准：
- 正向情绪：角色的情绪反应是积极面对而非消极逃避
- 转机来源：成长来自自然意外或领悟，而非说教或外部强制
- 结尾基调：明亮有成就感，而非悲伤或遗憾

## 注意
- 量化锚点为客观信号基线，LLM 审查用于处理边界情况（如讽刺、反语）
- 维表由 quality-agent 维护，可由项目扩展
- 维度2 硬阻断优先级最高
- 此检测不预设具体项目的情感规则
- 规则来源必须可追溯（wiki 页面或用户输入）
- 无约束定义 → SKIP
