# manifest.json — 会话清单 Schema

`manifest.json` 是导出产物目录的**索引入口**。导入平台只需读这一个文件，即可了解整个会话的全貌——有哪些产出、在哪里、如何与对话关联。

## 完整示例

```json
{
  "schema_version": "3.0",
  "exported_at": "2026-07-06T17:30:00+08:00",

  "session": {
    "session_id": "20260706A1B2C3",
    "project_name": "demo2"
  },

  "summary": {
    "message_count": 24,
    "user_messages": 12,
    "ai_messages": 12,
    "file_count": 2,
    "image_count": 3
  },

  "files": [
    {
      "filename": "test_v1.md",
      "source_message_id": "20260706A1B2C3002",
      "size_bytes": 4145
    },
    {
      "filename": "characters_v1.md",
      "source_message_id": "20260706A1B2C3006",
      "size_bytes": 1279
    }
  ],

  "images": [
    {
      "filename": "demo2_ep1_p1_v1.png",
      "source_message_id": "20260706A1B2C3004",
      "episode": 1,
      "page": 1,
      "description": "Mia 站在月光花园入口，萤火虫环绕",
      "found": true
    },
    {
      "filename": "demo2_ep1_p2_v1.png",
      "source_message_id": "20260706A1B2C3007",
      "episode": 1,
      "page": 2,
      "description": "Finn 从树后探出头，手里拿着一朵发光的蘑菇",
      "found": true
    }
  ]
}
```

## 字段说明

### 顶层

| 字段 | 类型 | 必须 | 说明 |
|---|---|---|---|
| `schema_version` | string | 是 | 固定 `"3.0"` |
| `exported_at` | string | 是 | 导出时间，ISO 8601 格式，如 `"2026-07-06T17:30:00+08:00"` |

### session — 会话元数据

| 字段 | 类型 | 必须 | 说明 |
|---|---|---|---|
| `session_id` | string | 是 | 会话唯一标识，格式 `{YYYYMMDD}{6位大写HEX}` |
| `project_name` | string | 是 | 绘本项目名，来自 `wiki/index.md` |

### summary — 数量统计

| 字段 | 类型 | 必须 | 说明 |
|---|---|---|---|
| `message_count` | number | 是 | 对话消息总数 |
| `user_messages` | number | 是 | 用户消息数 |
| `ai_messages` | number | 是 | AI 消息数 |
| `file_count` | number | 是 | `files/` 下文件数 |
| `image_count` | number | 是 | `images/` 下图片数（含未找到的） |

### files[] — 产物文件清单

| 字段 | 类型 | 必须 | 说明 |
|---|---|---|---|
| `filename` | string | 是 | `files/` 目录下的实际文件名（纯文件名，无路径） |
| `source_message_id` | string | 是 | 指向 `dialogue.json` 中生成该文件的 AI 消息 ID |
| `size_bytes` | number | 否 | 文件大小（字节），便于导入方做容量预估 |

### images[] — 生成图片清单

| 字段 | 类型 | 必须 | 说明 |
|---|---|---|---|
| `filename` | string | 是 | `images/` 目录下的实际文件名 |
| `source_message_id` | string | 是 | 指向 `dialogue.json` 中生成该图片的 AI 消息 ID |
| `episode` | number | 否 | 绘本集数，可从文件名或上下文推断 |
| `page` | number | 否 | 绘本页数，可从文件名或上下文推断 |
| `description` | string | 否 | 图片描述，从生成时的 prompt 提取 |
| `found` | boolean | 是 | 是否成功复制。`false` 时 `images/` 下无对应文件 |

## 溯源机制

manifest.json 与 dialogue.json 通过 `source_message_id` 双向关联：

- **正向（消息 → 产物）**：读 `dialogue.json` 中 AI 消息的 `files_created` / `images_created` → 拿 filename 去 `files/` / `images/` 取文件
- **反向（产物 → 消息）**：读 `manifest.json` 中 file/image 的 `source_message_id` → 在 `dialogue.json` 中找到对应消息 → 看到生成时的完整对话上下文

## 目录关联

```
data_collect/{项目名}/{session_id}/
├── manifest.json          ← 本文件
├── dialogue.json          ← 对话流
├── files/                 ← files[].filename 指向这里
│   └── test_v1.md
└── images/                ← images[].filename 指向这里
    └── demo2_ep1_p1_v1.png
```
