# 确认清单模板（Step 4.3 引用）

本文档是 `picturebook-art-agent` Step 4.3 的输出模板。Agent 按此骨架填充动态字段后呈现给用户。

---

## 输出结构

对每个目标页面依次输出以下块：

```
---
## 🎨 生图确认清单

**场景**：{绘本插图 / 角色人设图 / 场景图 / 道具图}
**目标**：{第 n 集第 m 页 / 角色：{角色名} / 场景：{场景名} / 道具：{道具名}}
**来源**：{脚本路径 / 角色wiki / 场景wiki / 道具定义 / 用户直接提供}
**输入类型**：{指定集+页 / 指定素材 / 直接提示词}
**生成参数**：{模型} / {宽高比例} / {分辨率} / {画质或—} / {适用范围}
{gpt-image-2 时：实际像素：{如 1024×768}（来自 {比例}+{分辨率} 查表）}

---

### 📋 参考图清单（生成时将全部使用，以下 ✅ 项目均会注入）

| # | 类别 | 角色/场景 | 状态 | 路径 | 注入方式 |
|---|---|---|---|---|---|
| 1 | 人设图 | {角色A} | {✅/⚠️/❌} | {path} | {🖼️ multipart / base64 / —} |
| 2 | 人设图 | {角色B} | {✅/⚠️/❌} | {path} | {🖼️ / —} |
| 3 | 场景图 | {场景名} | {✅/⚠️/❌} | {path} | {🖼️ / —} |
| 4 | 风格参考 | 绘本风格 | {✅/⚠️/❌} | {path} | {🖼️ / —} |

**注入方式说明**：
- {gpt-image-2 时} 🖼️ **multipart 上传**：通过 n1n `/v1/images/edits` 端点
- {nano-banana-2 时} 🧬 **base64 内联**：通过 `contents[].parts[].inline_data`
- — **不注入**：未就绪（⚠️ 仅文字或 ❌ 缺失）

> ⚠️ 生成时使用以上**全部 ✅ 已就绪**的参考图（共 {N} 张），不得减少。

### 📝 生图提示词

> 提示词生成方式：image-prompt-architect Skill（流水线模式）

```
{image-prompt-architect 返回的 prompt_text（截断显示前 200 字符）}
```

### ⚙️ 实际调用参数摘要

{⚠️ 以下两段按所选后端二选一输出，不输出两个。}

{若 gpt-image-2：}

| 参数 | 值 |
|---|---|
| `prompt` | `{prompt_text 截断前 100 字符}...` |
| `backend` | `gpt-image-2` |
| `size` | `{如 1024×768}`（来自 {比例}+{分辨率} 查表） |
| `quality` | `{用户指定的画质}` |
| `model` | `gpt-image-2` |
| `endpoint` | `generations`（无参考图）/ `edits`（有参考图，multipart） |
| `gateway` | `n1n`（llm-api.net） |

{若 nano-banana-2：}

| 参数 | 值 |
|---|---|
| `prompt` | `{prompt_text 截断前 100 字符}...` |
| `backend` | `nano-banana-2` |
| `size` | `{如 4:3}`（aspectRatio，不映射像素） |
| `resolution` | `{1K / 2K / 4K}`（imageSize） |
| `model` | `gemini-3.1-flash-image` |
| `endpoint` | `gemini-generateContent` |
| `gateway` | `n1n`（llm-api.net） |

### ⚠️ 风险提示（来自 image-prompt-architect 步骤 3）

{如有 risks_found，逐条列出；无则写"无显著风险"}

### 💡 假设标注（来自 image-prompt-architect 步骤 1）

{如有 assumptions，逐条列出；无则写"无"}

---

**请确认：**
- 参考图是否齐全？注入方式是否可接受？
- 提示词是否需要修改？
- 调用参数（模型/比例/分辨率/画质）是否正确？
- 风险提示和假设标注是否可接受？
- 回复「确认」或「开始生成」进入图片生成步骤
```

## 多页汇总（Step 4.4）

多于一页时，先输出汇总表：

| 页码 | 参考图就绪率 | 人设图 | 场景图 | 提示词来源 |
|---|---|---|---|---|
| 1 | 3/4 | ✅✅⚠️ | ❌ | image-prompt-architect |
| 2 | 2/3 | ✅⚠️ | ❌ | image-prompt-architect |

汇总后逐页展开详情（每个页面一个确认块）。
