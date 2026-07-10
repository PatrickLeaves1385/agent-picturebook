---
name: session-export
description: 将当前绘本创作会话导出为标准化 JSON 对话流 + 产物文件副本，供导入到其他绘本创作平台。触发词：导出会话、会话导出、导出本次会话、导出对话、导出对话流、归档会话、session export。
---

# Session Export Skill

## 目标

把当前会话导出为一组标准化的 JSON 文件，并复制会话中产出的所有本地文件与图片。导出产物可直接导入到另一个绘本创作线上平台。

## 产物目录结构

```
data_collect/{项目名}/
└── {session_id}/
    ├── manifest.json          ← 会话清单：统计 + 文件/图片索引（导入方第一入口）
    ├── dialogue.json          ← 完整对话流（含 AI 思考 + 全部工具调用细节）
    ├── files/                 ← 会话中 AI 产出的本地文件副本（平铺，无目录结构）
    │   ├── test_v1.md
    │   └── characters_v1.md
    └── images/                ← 会话中 AI 生成的图片副本（平铺）
        ├── demo2_ep1_p1_v1.png
        └── demo2_ep1_p2_v1.png
```

目录名与文件名中的非法字符（`\ / : * ? " < > |`）替换为 `-`。

## 重要前提（必须由主会话执行）

本技能依赖**当前会话的完整对话上下文**来重建对话流与产物清单，因此**必须由掌握会话上下文的 Agent 直接执行，不能委派给冷启动的子 Agent**。

## Read First

执行前必须读取：

1. `CLAUDE.md`（语言规则：全程中文）
2. `wiki/index.md`（确定项目名称与项目 ID）
3. Schema 参考文件（位于本技能 `references/` 目录）：
   - `references/dialogue-schema.md` — dialogue.json 完整 Schema（含示例 + 字段表 + 特殊工具处理规则）
   - `references/manifest-schema.md` — manifest.json 完整 Schema（含示例 + 字段表 + 溯源机制）

> 以上两个 schema 文件是产物的**权威字段定义**。执行导出时，按 schema 文件中的字段说明精确构造 JSON。如有疑问以 schema 文件为准。

## 统一 ID

- **`session_id`**：格式 `{YYYYMMDD}{6位大写十六进制}`，一段连续 id、无分隔符、无前缀。贯穿全部产物。生成命令：
  ```
  python -c "import datetime,uuid;print(datetime.datetime.now().strftime('%Y%m%d')+uuid.uuid4().hex[:6].upper())"
  ```
- **`message_id`**：`{session_id}{三位序号}`，从 `001` 起递增。用户和 AI 消息统一递增。

## 流程（6 步）

### 第 1 步：生成 session_id

按上方的 Python 命令生成，示例：`20260706A1B2C3`。

### 第 2 步：确定项目名，建目录

从对话内容 + `wiki/index.md` 确定本次会话的绘本项目名（如 `demo2`）。建目录：

```
data_collect/{项目名}/{session_id}/
```

子目录：`files/` 和 `images/`。

### 第 3 步：重建对话流 → dialogue.json

**Schema 权威定义见 `references/dialogue-schema.md`**。本步按该文件字段说明精确构造对话流。

逐条整理用户与 AI 的消息。AI 消息**必须包含完整执行过程**：`thinking`（思考） + `steps`（全部工具调用参数与结果） + `files_created` / `images_created`（产物关联）。

用户消息只含共有字段（`message_id`、`role`、`timestamp`、`timestamp_iso`、`content`），无 `thinking`、`steps`、`files_created`、`images_created`。

要点：

1. 本技能自身的导出指令不计入 dialogue.json
2. 逐条遍历会话，用户消息和 AI 消息交替排列，message_id 从 `001` 起统一递增
3. AI 消息的 `steps` 数组按实际执行顺序排列，每条记录 `type` / `tool` / `params` / `result_summary`
4. AI 消息的 `thinking` 从会话上下文中提取 AI 展示的完整思考内容
5. Write 工具的 params 用 `content_preview`（截取前约 200 字符 + `...（共N字）`）替代完整内容
6. AI 若无工具调用（纯文本回复），`steps`、`files_created`、`images_created` 均为空数组 `[]`
7. 各字段的类型、是否必须、具体取值规则详见 `references/dialogue-schema.md`

### 第 4 步：复制本地产物文件 → files/

遍历 dialogue.json 中所有 `files_created`。对每条：

1. 在项目目录中搜索该文件名（`find` 或 `Glob`）
2. 确认文件存在后，复制到 `{session_id}/files/` 目录
3. 平铺存放，不保留原始目录结构

由于本项目的创作 Agent 在输出同名文件时会自动递增版本号（`test_v1.md` → `test_v2.md`），`files/` 下不会出现同名冲突。若极少数情况下仍冲突，第二个文件加 `_2` 后缀。

### 第 5 步：复制生成图片 → images/

遍历 dialogue.json 中所有 `images_created`。对每条：

1. **优先查 image-generate 返回值**：如果会话中 image-generate（n1n gpt-image-2）的返回结果包含了本地保存路径，直接复制该文件
2. **次选文件名搜索**：在项目目录中按 filename 搜索（`find` 或 `Glob`）
3. **最后按命名约定推断**：按 `{项目名}_ep{集}_p{页}_v{版本}.png` 或类似模式搜索
4. **找不到时**：`manifest.json` 中该图片仍记录，但标注 `found: false`，`images/` 下无对应文件

### 第 6 步：生成 manifest.json

**Schema 权威定义见 `references/manifest-schema.md`**。本步按该文件字段说明精确构造会话清单。

汇总以上所有信息：`session` 元数据 + `summary` 统计 + `files` 清单 + `images` 清单。每个 file/image 必须写入 `source_message_id` 以建立与 `dialogue.json` 的双向溯源。

各字段的类型、是否必须、具体取值规则详见 `references/manifest-schema.md`。

## 溯源机制

- **正向（消息 → 产物）**：读 dialogue.json，AI 消息的 `files_created` / `images_created` 指出本轮产出了什么，去 `files/` 或 `images/` 取文件
- **反向（产物 → 消息）**：读 manifest.json，每个 file/image 的 `source_message_id` 指向 dialogue.json 中的消息，可看到生成时的对话上下文

## 输出策略

- 导出根目录为 `data_collect/`（不存在则新建）
- 按 `{项目名}/{session_id}/` 两层结构组织，同一项目的多次会话自然归类
- 全部产物只新增、不覆盖。若目标目录已存在，换一个新的 session_id 或提示用户
- 本技能**不修改** `wiki/`、`raw/`、`.claude/`，产出仅写入 `data_collect/`

## Completion

完成后必须说明：

- 读取了哪些规则 / 文件
- 生成的 `session_id` 与项目名
- 产物目录路径
- dialogue.json 中 message 总数（用户 / AI 各多少）
- files/ 中文件数量与文件名列表
- images/ 中图片数量与文件名列表
- 是否有图片未找到（`found: false`）
- manifest.json 路径
