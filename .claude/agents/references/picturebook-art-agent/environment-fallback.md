# picturebook-art-agent — 环境能力检测与回退路径

> 供 `.claude/agents/picturebook-art-agent.md` 引用。本文档覆盖三处环境相关的低频分支：Step 0.5 环境能力清单、Step 3.4 提示词生成回退、Step 5.9 图片生成回退。这些分支只在工具/Skill 不可用时才会真正触发，主文件只保留一句话指令 + 到本文档的引用链接。

## Step 0.5：环境能力清单

在进入 Step 1 之前，检测当前运行环境中的工具/Skill 可用性，**输出显式能力清单**。本步骤的目的：识别哪些步骤有原生工具支持、哪些需回退路径、哪些不可跳过，防止执行者在 Skill 不可用时无声降级。

### 0.5.1 检测项

| 能力点 | 检查方式 | 可用性判定 | 影响步骤 |
|---|---|---|---|
| `Skill(image-prompt-architect)` | 探测当前环境是否有 Skill 工具且 `image-prompt-architect` 在可用技能列表中 | `available` / `fallback` | Step 3 |
| `Skill(image-generate)` + n1n API | 探测 `image-generate` Skill 是否可用 + 检查 `.agent-cache/n1n-api-key` 或环境变量 `N1N_API_KEY` 是否存在 | `available` / `fallback` / `blocked` | Step 5 |
| 直接图像生成能力（ImageGen 或等效） | 检查当前环境是否有原生图像生成工具 | `available` / `blocked` | Step 5 fallback |

### 0.5.2 输出格式

提供给 Step 4 确认清单展示用：

```
## 🛠️ 环境能力清单
- image-prompt-architect: {✅ available / ⚠️ fallback（手动构造）}
- image-generate + n1n API: {✅ available / ⚠️ fallback（手动调 generate.py / 退回通用生成工具）}
- 强制约束（以下步骤无工具依赖，任何环境不得跳过）：
   Step 3.5（参数询问）· Step 4（用户确认）· 正确定义输出路径
```

落 `log.md` 的记录格式：每次生图完成后追加 `[cap] agent=art env={env_id} arch={available/fallback} gen={available/fallback/blocked}`。

### 0.5.3 回退路径的后续通知

标记为 `fallback` 的能力点，在最终确认清单（Step 4）中追加标注 `⚠️ 使用回退路径`，并在 `log.md` 中单独记录回退的原因和替代方式。用户有权在 Step 4 阶段因回退路径而要求中止或改用其他生成方式。

---

## Step 3.4：提示词生成回退（当 image-prompt-architect 不可用时）

当 Step 0.5 环境检测判定 `Skill(image-prompt-architect)` 为 `fallback` 时，按 image-prompt-architect SKILL.md 方法论**手动构造**提示词，不得自行随意拼写英文 prompt：

1. **意图拆解**：从 characters.md / worldview.md / 脚本中提取 → 主体 / 动作 / 环境 / 情绪 / 镜头 / 光影 / 风格
2. **风险排查**：读取 `.claude/skills/image-prompt-architect/references/risk-catalog.md`，逐条匹配意图，记录真实命中的风险
3. **分行结构**（遵循 image-prompt-architect 排版规则）：
   - ✅ 主体行 → 空间/环境行 → 光影行 → 镜头行 → 风格行 → 禁止项末行
   - ✅ 每个语义模块单行，不碎片化、不串联
   - ✅ 负面约束用自然语言嵌入末行（`不要`/`禁止`/`无`），正向描述中不出现不想要的词
4. **输出格式**：手工组装等效 JSON（prompt[] + prompt_text + risks_found + assumptions），确保 `prompt_text` 可直接传入图像生成 API
5. **标注回退**：Step 4 确认清单中追加 `⚠️ 提示词由手动回退路径生成（image-prompt-architect Skill 不可用）`，并在 `log.md` 记录

> 回退路径不改变后续流程。Step 4 仍然输出确认清单等用户确认，Step 5 选择对应的回退方案继续执行。

---

## Step 5.9：图片生成回退（当 image-generate 不可用时）

当 Step 0.5 环境检测判定 `Skill(image-generate)` 为 `fallback` 或 `blocked` 时，按以下优先级尝试生成：

**路径 1：手动调用 generate.py**
```
python .claude/skills/image-generate/generate.py --prompt "{confirmed_prompt}" --size {image_size} --quality {image_quality} --output {output_path} --api-key {N1N_API_KEY}
```
- 前提：n1n API 密钥可用（环境变量 `N1N_API_KEY` 或 `.agent-cache/n1n-api-key`）
- 手动调用时同样遵循版本化规则和逐页汇报

**路径 2：退回通用图像生成工具（路径 1 不可用时）**
- 使用当前环境提供的原生图像生成能力（如 ImageGen 工具），传入相同的 `confirmed_prompt` 和参数
- 限制：可能不支持多参考图、不兼容 n1n 尺寸/画质参数语义 → 标注在 `log.md`

**回退标记**：
生成完成后在 `log.md` 追加：`⚠️ 本次生成使用回退路径 {路径1/2}（image-generate Skill 不可用）[{env_id}]`
