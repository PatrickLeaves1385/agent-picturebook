---
name: illustration-generate
description: 调用 ImageGen 生成绘本插图。只负责接收最终参数 → 调用工具 → 保存 → 元数据。不负责提示词生成（提示词由 image-prompt-architect Skill 生成）。
---

# Illustration Generate Skill

## Goal

将 `image-prompt-architect` 生成的最终提示词 + 用户确认的所有参考图，转化为实际绘本插图。**本 Skill 只负责调用 ImageGen 工具，不参与提示词生成。**

## Read First

执行前必须读取：
1. `CLAUDE.md`（语言规则、版本化规则）
2. `wiki/domains/illustration/illustration-spec.md` §7（版本化命名规则）

---

## Process

### Step 1：接收输入

从 illustration-agent 接收（用户已确认后的最终参数）：

| 参数 | 说明 | 示例 | 来源 |
|---|---|---|---|
| `confirmed_prompt` | 用户确认的最终生图提示词 | 完整 prompt | `image-prompt-architect` Skill 生成 |
| `reference_images` | 用户确认的**全部**参考图路径列表 | `["raw/chars/lulu.png", "raw/chars/laura.png", "raw/scene/jungle.png", "raw/style/art_v1.png"]` | Step 2 参考图分析中所有 `✅ 已就绪` 项 |
| `image_size` | 用户指定的画幅尺寸 | `"1024x1024"` | 用户在参数确认阶段指定 |
| `image_quality` | 用户指定的画质 | `"high"` | 用户在参数确认阶段指定 |
| `output_path` | 图片输出路径（由 illustration-agent 指定） | `raw/project/ep1_p1_v1.png` | illustration-agent |
| `page` | 页码 | 1 | illustration-agent |
| `episode` | 集编号 | 1 | illustration-agent |

**关键约束**：
- 本 Skill 只接收 illustration-agent 在**用户确认全部参数后**委派的调用
- `confirmed_prompt` 已由 `image-prompt-architect` Skill 生成并经用户确认，本 Skill **不得修改**
- `reference_images` 是用户确认的全部参考图，**必须全部使用，不得减少**
- `image_size` 和 `image_quality` 由用户指定，**不得使用默认值替代**

### Step 2：参考图注入（必须全部使用）

`reference_images` 中的所有参考图**必须全部注入**，不得挑选、不得缩减。按优先级排列：人设图 > 场景图 > 风格参考图。

**注入策略**：
1. 先检查 ImageGen 工具 schema 的 `image` 参数能力
2. **支持多张** → 所有参考图通过 `image` 参数全部传入
3. **仅支持单张** → 取优先级最高的第一张通过 `image` 参数传入；其余参考图的文件名已在 `confirmed_prompt` 中引用（由 image-prompt-architect 写入），以文字形式注入

**调用方式**：

```
DeferExecuteTool(
  toolName="ImageGen",
  params={
    "prompt": "{confirmed_prompt}",
    "image": "{reference_images[0] 或 全部参考图}",  // 按 ImageGen 能力决定
    "size": "{image_size}",
    "quality": "{image_quality}"
  }
)
```

**注入结果记录**：执行后在返回给 illustration-agent 的结果中，区分两类参考图：

```json
{
  "references_used": {
    "injected": ["raw/chars/lulu_v2.png"],           // 通过 image 参数直接注入
    "text_referenced": ["raw/scene/jungle_v1.png"]   // 仅在 prompt 中文字引用
  }
}
```

### Step 3：调用 ImageGen

调用 ImageGen 生成图片。**参数全部来自输入，不设默认值。**

**工具调用流程**：
1. 使用 `ToolSearch` 加载 ImageGen 工具 schema：
   ```
   ToolSearch(tool_names=["ImageGen"])
   ```
2. 使用 `DeferExecuteTool` 调用 ImageGen，参数完全来自输入：
   ```
   DeferExecuteTool(
     toolName="ImageGen",
     params={
       "prompt": "{confirmed_prompt}",
       "size": "{image_size}",
       "quality": "{image_quality}"
     }
   )
   ```

**画幅与画质**：由 illustration-agent 在参数确认阶段向用户询问获得，本 Skill 不自行决定。

### Step 4：保存图片

从 ImageGen 返回结果中获取图片数据，保存到指定路径：
- 确保目标目录存在
- 文件名格式：`ep{X}_p{Y}_v{Z}.png`
- 版本号自动检测并递增，遵循 `illustration-spec.md` §7

### Step 5：记录元数据

在同目录下生成或追加图片元数据文件 `_metadata.json`：

```json
{
  "ep{X}_p{Y}_v{Z}.png": {
    "page": Y,
    "episode": X,
    "version": Z,
    "generated_at": "2026-07-06T10:00:00",
    "prompt_source": "image-prompt-architect",
    "image_size": "1024x1024",
    "image_quality": "high",
    "references_used": {
      "injected": ["raw/chars/lulu_v2.png"],
      "text_referenced": ["raw/scene/jungle_v1.png"]
    },
    "character_refs": ["lulu", "laura"],
    "status": "generated"
  }
}
```

新增字段说明：
- `prompt_source`：固定为 `"image-prompt-architect"`
- `image_size`：记录用户指定的画幅
- `image_quality`：记录用户指定的画质
- `references_used.injected`：通过 ImageGen `image` 参数直接注入的参考图
- `references_used.text_referenced`：仅在 prompt 中文字引用的参考图

---

## 画幅与画质约束

本 Skill **禁止**使用以下默认值：

| 参数 | 禁止行为 | 正确行为 |
|---|---|---|
| `size` | ❌ 默认 `1024x1024` | ✅ 从输入参数 `image_size` 获取 |
| `quality` | ❌ 默认 `high` | ✅ 从输入参数 `image_quality` 获取 |

如果输入参数缺失 `image_size` 或 `image_quality`，**不得自行填充**，必须回传错误给 illustration-agent 要求补充。

---

## 错误处理

| 现象 | 处理 |
|---|---|
| ImageGen 返回错误 | 重试 1 次，如仍失败则标注该页 `[!] 生成失败`，继续下一页 |
| 输出目录不存在 | 自动创建完整目录路径 |
| 版本号冲突 | 自动递增到下一个可用版本号 |
| 参考图文件不存在 | 标注 `[!]` 该参考图缺失：若为最高优先级图（将注入 ImageGen），降级为取次优先级图注入；若为文字引用图，从 prompt 中移除对应文件名引用。在元数据中记录 `missing_refs: [...]` |
| `image_size` 或 `image_quality` 缺失 | 回传错误给 illustration-agent，**不自行填充** |

---

## Output

完成后返回给 illustration-agent：

```json
{
  "page": 1,
  "episode": 1,
  "image_path": "raw/project/ep1_p1_v1.png",
  "status": "success",
  "version": 1,
  "image_size": "1024x1024",
  "image_quality": "high",
  "prompt_source": "image-prompt-architect",
  "references_used": {
    "injected": ["raw/chars/lulu_v2.png"],
    "text_referenced": ["raw/scene/jungle_v1.png"]
  },
  "generated_at": "2026-07-06T10:00:00"
}
```

或失败时：

```json
{
  "page": 3,
  "status": "failed",
  "error": "ImageGen API timeout",
  "retry_attempted": true
}
```

**字段说明**：

| 字段 | 说明 |
|---|---|
| `references_used.injected` | 通过 ImageGen `image` 参数直接注入的参考图（对画面影响最大） |
| `references_used.text_referenced` | 仅在 prompt_text 中以文件名引用的参考图（文字层面约束） |

---

## 完成清单

执行完毕后向 illustration-agent 报告：
- 成功生成 N 页，失败 M 页
- 每张图片的文件路径和版本号
- 使用的画幅和画质参数
- 失败页的页码和错误原因
- 参考图使用情况：直接注入 {M} 张 + 文字引用 {K} 张
