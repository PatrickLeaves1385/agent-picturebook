# 可插拔质检系统

绘本质量的自动化检测系统。质检规则与 Agent 代码完全解耦，新增/更新/删除质检项只需编辑本目录下的配置文件，无需触碰任何 Agent 或 Skill 代码。

## 目录结构

```
schema/quality-checks/
├── README.md              # 本文件
├── active.json            # 当前启用的质检项清单（唯一控制开关）
├── text/                  # 文本质量检测
│   ├── lexile.md          # 蓝思值
│   ├── awl.md             # AWL 学术词汇
│   ├── page-count.md      # 页数校验
│   └── text-length.md     # 每页文字量
├── content/               # 内容质量检测
│   ├── emotion-tone.md    # 情感基调
│   ├── ip-hooks.md        # IP 钩子完整性
│   ├── growth-uniqueness.md  # 成长点唯一性
│   └── character-consistency.md  # 角色一致性
├── illustration/          # 插图质量检测
│   ├── composition.md     # 构图规范
│   ├── character-pose.md  # 角色姿势朝向
│   └── style-consistency.md  # 风格一致性
└── future/                # 预留：未来扩展
    └── _template.md       # 新建质检项模板
```

## 质检项配置文件格式

每个质检项是一个独立的 `.md` 文件，使用 YAML frontmatter 定义元数据：

```yaml
---
id: "category/check-name"       # 唯一标识，与 active.json 中的 key 对应
category: "text"                # text | content | illustration | future
severity: "error"               # error（阻断）| warning（标注）
method: "api"                   # api | pattern | count | semantic | manual
target: "250-300"               # 目标值/范围
skill: "lexile-check"           # method=api 时调用的 Skill 名称
fail_action: "flag"             # block（阻断流程）| flag（标注继续）
description: "一句话描述检测逻辑"
---
# 详细说明（可选）
```

### method 字段说明

| method | 含义 | 示例 |
|---|---|---|
| `api` | 调用 Skill API 获取结果 | 蓝思值检测（lexile-check） |
| `pattern` | 正则或关键词匹配 | IP 钩子检测（搜索 "Oh my feathers"） |
| `count` | 计数校验（页数/词数） | 页数校验（==19） |
| `semantic` | LLM 语义审查 | 情感基调分析（无负面情绪） |
| `manual` | 人工审阅（仅标注提醒） | 风格一致性最终判断 |

### fail_action 字段说明

| fail_action | 含义 |
|---|---|
| `block` | 不通过时阻断流程，必须修改后重检 |
| `flag` | 不通过时标注提醒，但不阻断流程 |

## 使用方式

### 新增质检项

1. 在对应 category 目录下新建 `{check-name}.md`，按上述格式填写
2. 在 `active.json` 的 `active_checks` 数组中添加 `"category/check-name"`
3. 完成。quality-agent 下次运行时自动加载

### 停用质检项

1. 在 `active.json` 的 `active_checks` 数组中删除对应的 key
2. 完成。配置文件保留不删，方便日后重新启用

### 修改质检项

1. 直接编辑对应 `.md` 文件中的 YAML frontmatter 字段
2. 如需修改检测逻辑描述，编辑正文内容
3. 无需修改 `active.json`（除非变更了 key 名称）

### 删除质检项

1. 在 `active.json` 中删除对应 key
2. 删除对应 `.md` 文件（或移动到 `_archived/` 目录留存）

## quality-agent 工作流

```
1. 读取 schema/quality-checks/active.json → 获取 active_checks 列表
2. 逐一加载每个 active_checks 对应的 .md 配置文件
3. 根据 method 字段选择执行方式：
   - api → 调用对应 Skill
   - pattern → 在目标文本中执行正则/关键词搜索
   - count → 执行计数校验
   - semantic → 使用 LLM 进行语义审查
   - manual → 标注待人工审阅
4. 汇总所有结果，按 severity 分级输出
5. 生成结构化质检报告
```

## 质检报告格式

```
=== 质检报告 ===
目标文件：{file_path}
检测时间：{timestamp}
激活检测项：{count} 项

PASS (X/Y):
  ✅ text/lexile: 265L (250-300L)
  ✅ text/awl: 1.2% (<2%)
  ...

FAIL (X/Y):
  ❌ content/ip-hooks: 缺少 "Oh my feathers!" （第5页）
  ⚠️ content/emotion-tone: 第8页出现 "scared" 需确认情感基调
  ...

建议：
- {具体修改建议}
```
