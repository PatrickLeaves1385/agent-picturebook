---
name: image-generate
description: 调用 n1n API 生成图片，支持 gpt-image-2（OpenAI 兼容）和 nano-banana-2（Gemini 3.1 Flash Image）双后端。支持文生图 + 图生图（多参考图）。只负责接收最终参数 → 调用 generate.py → 保存 → 元数据。不负责提示词生成。
---

# Image Generate Skill

## Goal

将 `image-prompt-architect` 生成的最终提示词 + 用户确认的全部参考图，通过 n1n API 转化为绘本图片。**本 Skill 只负责调用 generate.py，不参与提示词生成。**

## 支持的后端

| 后端 | 模型 | 端点 | 分辨率 | 参考图格式 |
|---|---|---|---|---|
| `gpt-image-2`（默认） | gpt-image-2 | `/v1/images/generations` / `/v1/images/edits` | 像素尺寸（768x1024 等） | multipart form-data |
| `nano-banana-2` | gemini-3.1-flash-image | `/v1beta/models/gemini-3.1-flash-image:generateContent` | 1K / 2K / 4K | base64 内联 (inline_data) |

两个后端共用同一套 n1n API 密钥，无需额外配置。

## Read First

执行前必须读取：
1. `CLAUDE.md`（语言规则、版本化规则）
2. `wiki/domains/illustration/illustration-spec.md` §7（版本化命名规则）

---

## Process

### Step 0：API 密钥确认（首次执行前）

**在首次调用 API 前，必须确认 n1n API 密钥是否可用（按以下优先级）：**

1. 优先读取环境变量 `N1N_API_KEY`（推荐，避免密钥明文落盘）
2. 否则读取 `.agent-cache/n1n-api-key` 文件
3. 若两者都未找到：
   - **主动询问用户**：「请提供您的 n1n API 密钥（注册地址：https://llm-api.net/register）」
   - 用户提供后保存（建议设置 `N1N_API_KEY` 环境变量，或写入 `.agent-cache/n1n-api-key`）
4. `generate.py` 内置「命令行参数 → 环境变量 → 文件」三层回退，Skill 调用时按需传入 `--api-key`

### Step 1：接收输入

从 picturebook-art-agent 接收（用户已确认后的最终参数）：

| 参数 | 说明 | 示例 |
|---|---|---|
| `confirmed_prompt` | 用户确认的最终生图提示词 | `image-prompt-architect` 生成 |
| `reference_images` | 用户确认的**全部**参考图路径列表 | `["raw/chars/lulu.png", "raw/scene/jungle.png"]` |
| `image_size` | 像素尺寸（或比例自动映射） | `"1024x1024"` / `"1:1"` |
| `image_quality` | 画质 | `"low"` / `"medium"` / `"high"` |
| `output_path` | 图片输出路径 | `outputs/{project_id}/illustrations/ep1_p1_v1.png` |
| `backend` | 生图后端（可选，默认 `gpt-image-2`） | `"gpt-image-2"` / `"nano-banana-2"` |
| `resolution` | nano-banana-2 分辨率（可选，默认 `1K`） | `"1K"` / `"2K"` / `"4K"` |
| `page` | 页码 | 1 |
| `episode` | 集编号 | 1 |

**关键约束**：
- `confirmed_prompt` 已确认，不得修改
- `reference_images` 是全部参考图，**必须全部使用，不得减少**
- `image_size` 和 `image_quality` 由用户指定，禁止默认值

### Step 2：选择后端与端点

根据 picturebook-art-agent 传入的 `backend` 参数选择：

| backend | 模型 | 文生图端点 | 图生图端点 |
|---|---|---|---|
| `gpt-image-2`（默认） | gpt-image-2 | `POST /v1/images/generations` | `POST /v1/images/edits` |
| `nano-banana-2` | gemini-3.1-flash-image | `POST /v1beta/models/gemini-3.1-flash-image:generateContent`（同一端点） |

- 认证：统一使用 `Authorization: Bearer {api_key}`
- 超时：400 秒
- 重试：`generate.py` 自动指数退避重试最多 3 次

### Step 3：调用 generate.py 生成图片

通过 Bash 执行 generate.py：

**gpt-image-2 文生图（无参考图）**：
```bash
python .claude/skills/image-generate/generate.py \
  --prompt "{confirmed_prompt}" \
  --size "{image_size}" \
  --quality "{image_quality}" \
  --api-key "${N1N_API_KEY:-$(cat .agent-cache/n1n-api-key)}" \
  --output "{output_path}" \
  --backend gpt-image-2 \
  --json
```

**gpt-image-2 图生图（有参考图）**：
```bash
python .claude/skills/image-generate/generate.py \
  --prompt "{confirmed_prompt}" \
  --size "{image_size}" \
  --quality "{image_quality}" \
  --api-key "${N1N_API_KEY:-$(cat .agent-cache/n1n-api-key)}" \
  --output "{output_path}" \
  --backend gpt-image-2 \
  --refs "{ref_1}" "{ref_2}" "{ref_3}" \
  --json
```

**nano-banana-2 文生图（无参考图）**：
```bash
python .claude/skills/image-generate/generate.py \
  --prompt "{confirmed_prompt}" \
  --size "{image_size}" \
  --quality "{image_quality}" \
  --api-key "${N1N_API_KEY:-$(cat .agent-cache/n1n-api-key)}" \
  --output "{output_path}" \
  --backend nano-banana-2 \
  --resolution "{resolution}" \
  --json
```

**nano-banana-2 图生图（有参考图）**：
```bash
python .claude/skills/image-generate/generate.py \
  --prompt "{confirmed_prompt}" \
  --size "{image_size}" \
  --quality "{image_quality}" \
  --api-key "${N1N_API_KEY:-$(cat .agent-cache/n1n-api-key)}" \
  --output "{output_path}" \
  --backend nano-banana-2 \
  --resolution "{resolution}" \
  --refs "{ref_1}" "{ref_2}" \
  --json
```

**参数说明**：

| 参数 | 说明 |
|---|---|
| `--prompt` | 已确认的完整提示词 |
| `--size` | **gpt-image-2**：具体像素尺寸（如 `1024×768`）或比例（自动按 1K 映射，见下方映射表）。**不支持**"比例+分辨率"组合。<br>**nano-banana-2**：宽高比例（如 `1:1`、`4:3`），仅作 `aspectRatio` 参数，不映射为像素。 |
| `--quality` | 画质：`low` / `medium` / `high` / `auto`（必填，无默认值） |
| `--api-key` | n1n API 密钥（Bearer Token） |
| `--output` | 目标文件路径 |
| `--refs` | 参考图路径列表（空格分隔，可选多张） |
| `--backend` | 后端选择：`gpt-image-2`（默认）/ `nano-banana-2` |
| `--resolution` | **nano-banana-2 专用**。分辨率等级：`1K`（默认）/ `2K` / `4K`。gpt-image-2 忽略此参数。 |

**比例 → 像素映射表**：

| 比例 | 1K 像素 | 2K 像素 | 4K 像素 |
|---|---|---|---|
| `21:9` | 1344×576 | 2016×864 | 3808×1632 |
| `16:9` | 1280×720 | 2048×1152 | 3840×2160 |
| `5:4` | 1040×832 | 2080×1664 | 3200×2560 |
| `4:3` | 1024×768 | 2048×1536 | 3264×2448 |
| `3:2` | 1008×672 | 2064×1376 | 3504×2336 |
| `1:1` | 1024×1024 | 2048×2048 | 2880×2880 |
| `2:3` | 672×1008 | 1376×2064 | 2336×3504 |
| `3:4` | 768×1024 | 1536×2048 | 2448×3264 |
| `4:5` | 832×1040 | 1664×2080 | 2560×3200 |
| `9:16` | 720×1280 | 1152×2048 | 2160×3840 |

**两后端参数差异**：

| | gpt-image-2 | nano-banana-2 |
|---|---|---|
| 接收格式 | 具体像素数（如 `1024×768`） | 宽高比例 + 分辨率（如 `4:3` + `2K`） |
| `--size` 作用 | 直接作为请求 `size` 参数 | 提取为 `aspectRatio`（仅含 `:` 的比例串） |
| `--resolution` 作用 | **忽略** | 映射为 `imageSize`（`1K`/`2K`/`4K`） |
| 比例自动映射 | `map_size()` 将比例映射为 1K 像素 | 原始比例串直接传入 API，不映射 |

**参数严格性**：

| 参数 | 禁止行为 | 正确行为 |
|---|---|---|
| `size` | ❌ 默认 `1024x1024` | ✅ 从输入参数获取 |
| `quality` | ❌ 默认任何值 | ✅ 必填，缺失时报错 |

### Step 4：保存图片（含格式修正）

`generate.py` 已处理：
- API 返回的 base64 图片自动解码写入 `--output` 指定路径
- 目标目录不存在时自动创建
- 版本号由 picturebook-art-agent 在传入 `output_path` 时确定
- **格式自检**：写入后检测文件头。若实际格式为 JPEG（`\xFF\xD8`）但扩展名为 `.png`，自动重命名为 `.jpg`；反之亦然。这意味着 nano-banana-2 输出的 `.png` 文件可能被修正为 `.jpg`——调用方应以 `generate.py` 返回的 `output_path` 为准，而非预设扩展名

### Step 5：记录元数据（generate.py 自动写入）

生成成功后，`generate.py` 自动在同目录写入/追加 `_metadata.json`（无需 Agent 手动写）。文件名符合 `ep{X}_p{Y}_v{Z}.png` 时自动解析出 episode/page/version；其他命名（如 `direct_prompt_*`）留 null。

```json
{
  "ep1_p1_v1.png": {
    "page": 1,
    "episode": 1,
    "version": 1,
    "generated_at": "2026-07-07T16:30:27",
    "prompt_source": "image-prompt-architect",
    "image_size": "1254x1254",
    "requested_size": "1024x1024",
    "image_quality": "high",
    "model": "gpt-image-2",
    "backend": "gpt-image-2",
    "api_endpoint": "generations",
    "api_gateway": "n1n",
    "references_used": {
      "injected": ["raw/chars/lulu.png", "raw/scene/jungle.png"],
      "text_referenced": []
    },
    "revised_prompt": "",
    "status": "generated"
  }
}
```

- `image_size`：**实际输出像素**（读取已生成文件的真实宽高，非请求参数）
- `requested_size`：调用方请求的尺寸（`--size` 比例映射后或 `--resolution` 映射后的值），用于比对"请求 vs 实际"的偏差
- `revised_prompt`：API 返回的中文修订提示词（图生图更常见，文生图可能为空）。完成汇报时可摘要此字段，便于审计"实际生成用了什么"。

---

## 错误处理

| 现象 | 处理 |
|---|---|
| API 返回错误（429/5xx/网络） | `generate.py` 自动指数退避重试最多 3 次；仍失败则标注该页 `[!] 生成失败` |
| 401 Unauthorized | API 密钥无效，提示用户重新提供 |
| 输出目录不存在 | `generate.py` 自动创建 |
| 版本号冲突 | 由 picturebook-art-agent 在传入前确定 |
| 参考图文件不存在 | `generate.py` 返回 `FileNotFoundError`，标注 `[!]` |
| `image_size` 或 `image_quality` 缺失 | 回传错误给 picturebook-art-agent |
| API 超时（>400s） | 返回超时错误，标注生成失败 |

---

## Output

生成结果分两层：

**① generate.py 原始输出（脚本直接打印，供 Agent 读取）**：
```json
{ "output_path": "outputs/{project_id}/illustrations/ep1_p1_v1.png", "revised_prompt": "..." }
```

**② Skill / Agent 组装汇报（补充来自上下文的字段：page / episode / version / references_used 等）**：
```json
{
  "page": 1, "episode": 1,
  "image_path": "outputs/{project_id}/illustrations/ep1_p1_v1.png",
  "status": "success", "version": 1,
  "image_size": "1024x1024", "image_quality": "high",
  "prompt_source": "image-prompt-architect",
  "model": "gpt-image-2",
  "backend": "gpt-image-2",
  "api_gateway": "n1n",
  "references_used": {"injected": ["raw/chars/lulu.png"], "text_referenced": []},
  "generated_at": "2026-07-07T10:00:00",
  "revised_prompt": "..."
}
```

失败（脚本以非零码退出，stderr 打印 `{"error": "..."}`）：
```json
{ "page": 3, "status": "failed", "error": "API 返回 429 限流" }
```

---

## 完成清单

- 成功生成 N 页，失败 M 页
- 每张图片的文件路径和版本号
- 使用的后端、尺寸和画质
- 失败页的页码和错误原因
- 参考图使用情况：gpt-image-2 通过 multipart 注入 / nano-banana-2 通过 base64 内联 {M} 张
