# dialogue.json — 完整对话流 Schema

`dialogue.json` 记录人类用户与 AI 的完整对话过程。AI 消息包含**思考过程 + 全部工具调用细节 + 产物关联**，是导入平台重建会话上下文的核心文件。

## 完整示例

```json
{
  "session_id": "20260706A1B2C3",
  "project_name": "demo2",
  "messages": [
    {
      "message_id": "20260706A1B2C3001",
      "role": "user",
      "timestamp": 1782359558,
      "timestamp_iso": "2026-07-06T14:32:38+08:00",
      "content": "帮我为 demo2 生成一个 5 页测试脚本"
    },
    {
      "message_id": "20260706A1B2C3002",
      "role": "ai",
      "timestamp": 1782359620,
      "timestamp_iso": "2026-07-06T14:33:40+08:00",
      "content": "好的，我基于 Mia 和 Finn 的角色设定，生成了一个 5 页测试脚本，已写入 test_v1.md。",
      "thinking": "用户要 demo2 的测试脚本。需要先读 characters.md 和 worldview.md 获取角色设定，再读 content-spec.md 确认页数要求为 5 页...",
      "steps": [
        {
          "type": "tool_call",
          "tool": "Read",
          "params": {
            "file_path": "wiki/projects/demo2/characters.md"
          },
          "result_summary": "已读取 characters.md：Mia 是勇敢的小兔子，Finn 是聪明的狐狸，两人住在月光花园"
        },
        {
          "type": "tool_call",
          "tool": "Read",
          "params": {
            "file_path": "wiki/projects/demo2/content-spec.md"
          },
          "result_summary": "已读取 content-spec.md：目标蓝思值 250-300L，每故事 5 页"
        },
        {
          "type": "tool_call",
          "tool": "Write",
          "params": {
            "file_path": "wiki/projects/demo2/scripts/test_v1.md",
            "content_preview": "# demo2 测试脚本 v1\n\n## 第1页\nMia 站在月光花园入口...（共5页）"
          }
        }
      ],
      "files_created": [
        {
          "filename": "test_v1.md"
        }
      ],
      "images_created": []
    },
    {
      "message_id": "20260706A1B2C3003",
      "role": "user",
      "timestamp": 1782359800,
      "timestamp_iso": "2026-07-06T14:36:40+08:00",
      "content": "给第 1 页配张图"
    },
    {
      "message_id": "20260706A1B2C3004",
      "role": "ai",
      "timestamp": 1782359900,
      "timestamp_iso": "2026-07-06T14:38:20+08:00",
      "content": "第 1 页插图已生成。画面中 Mia 站在月光花园入口，周围的萤火虫在满月下散发出柔和的光芒。",
      "thinking": "用户要为第 1 页配图。需要先读 test_v1.md 获取第 1 页的 illustration_description...然后调用 image-generate 生成，版本号从 v1 开始...",
      "steps": [
        {
          "type": "tool_call",
          "tool": "Read",
          "params": {
            "file_path": "wiki/projects/demo2/scripts/test_v1.md",
            "offset": 1,
            "limit": 10
          },
          "result_summary": "已提取第1页插图描述：全景建立镜头。Mia 站在月光花园入口，萤火虫环绕，满月挂在夜空"
        },
        {
          "type": "tool_call",
          "tool": "image-generate",
          "params": {
            "prompt": "A wide establishing shot. Mia, a brave little rabbit, stands at the entrance of the Moonlit Garden. Fireflies surround her, and a full moon hangs in the night sky. Soft magical atmosphere, children's picture book illustration style."
          },
          "result_summary": "图片已生成，保存为 demo2_ep1_p1_v1.png"
        }
      ],
      "files_created": [],
      "images_created": [
        {
          "filename": "demo2_ep1_p1_v1.png",
          "description": "Mia 站在月光花园入口，萤火虫环绕，满月当空"
        }
      ]
    }
  ]
}
```

## 字段说明

### 顶层

| 字段 | 类型 | 必须 | 说明 |
|---|---|---|---|
| `session_id` | string | 是 | 会话唯一标识，与 `manifest.json` 一致 |
| `project_name` | string | 是 | 绘本项目名 |
| `messages` | array | 是 | 消息数组，按时间顺序排列 |

### 所有消息共有

| 字段 | 类型 | 必须 | 说明 |
|---|---|---|---|
| `message_id` | string | 是 | `{session_id}{三位序号}`，如 `20260706A1B2C3001` |
| `role` | string | 是 | `"user"` 或 `"ai"` |
| `timestamp` | number | 是 | 10 位 Unix 秒级整数 |
| `timestamp_iso` | string | 是 | ISO 8601 格式，可读性备份 |
| `content` | string | 是 | 消息全文。用户消息原样收录；AI 消息取最终回复完整原文，不归纳不缩写 |

### 仅 AI 消息有

| 字段 | 类型 | 必须 | 说明 |
|---|---|---|---|
| `thinking` | string | 是 | AI 的完整思考过程（推理链、决策依据、判断逻辑）。从会话上下文中提取 AI 在回复前展示的思考内容 |
| `steps` | array | 是 | 执行步骤数组，完整记录 AI 本轮做了什么 |
| `files_created` | array | 是 | 本消息产出的文件列表。无产出时为空数组 `[]` |
| `images_created` | array | 是 | 本消息产出的图片列表。无产出时为空数组 `[]` |

### steps[] — 执行步骤

| 字段 | 类型 | 必须 | 说明 |
|---|---|---|---|
| `type` | string | 是 | `"tool_call"`（工具调用）或 `"command"`（命令执行） |
| `tool` | string | 是 | 工具名：Read / Write / Edit / image-generate / Bash / Grep / Glob / Glob / WebFetch / WebSearch 等 |
| `params` | object | 是 | 调用时传入的参数。敏感信息（token、密码等）需脱敏或省略 |
| `result_summary` | string | 否 | 执行结果摘要。输出较短时保留全文；很长时提取关键信息 |

#### 特殊工具的参数处理

**Write 工具**：写入内容通常很长，`params` 中用 `content_preview` 替代原始内容——截取前约 200 字符 + `...（共N字）`：

```json
{
  "type": "tool_call",
  "tool": "Write",
  "params": {
    "file_path": "wiki/projects/demo2/scripts/test_v1.md",
    "content_preview": "# demo2 测试脚本 v1\n\n## 第1页\nMia 站在月光花园入口...（共2100字）"
  }
}
```

**image-generate 工具**：参数中记录 prompt，结果摘要中记录生成的文件名。

### files_created[] — 本消息产出的文件

| 字段 | 类型 | 必须 | 说明 |
|---|---|---|---|
| `filename` | string | 是 | `files/` 目录下的文件名（纯文件名，无路径） |

### images_created[] — 本消息产出的图片

| 字段 | 类型 | 必须 | 说明 |
|---|---|---|---|
| `filename` | string | 是 | `images/` 目录下的文件名 |
| `description` | string | 否 | 图片描述，从 image-generate 调用的 prompt 或 AI 回复中提取 |

## 用户消息格式

用户消息只含共有字段，无 `thinking`、`steps`、`files_created`、`images_created`：

```json
{
  "message_id": "20260706A1B2C3001",
  "role": "user",
  "timestamp": 1782359558,
  "timestamp_iso": "2026-07-06T14:32:38+08:00",
  "content": "帮我为 demo2 生成一个 5 页测试脚本"
}
```

## AI 纯文本消息格式

若 AI 本轮无任何工具调用（仅纯文本回复），`steps`、`files_created`、`images_created` 均为空数组：

```json
{
  "message_id": "20260706A1B2C3005",
  "role": "ai",
  "timestamp": 1782360000,
  "timestamp_iso": "2026-07-06T14:40:00+08:00",
  "content": "脚本看起来不错，你觉得还需要调整什么吗？",
  "thinking": "用户还没有回复下一步指令，应该询问用户是否满意当前结果，或是否需要进一步修改。",
  "steps": [],
  "files_created": [],
  "images_created": []
}
```

## 目录关联

```
data_collect/{项目名}/{session_id}/
├── manifest.json
├── dialogue.json          ← 本文件
├── files/                 ← AI 消息 files_created[].filename 指向这里
└── images/                ← AI 消息 images_created[].filename 指向这里
```
