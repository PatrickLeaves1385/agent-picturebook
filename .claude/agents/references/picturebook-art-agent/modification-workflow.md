# picturebook-art-agent — 修改意见注入机制

> 供 `.claude/agents/picturebook-art-agent.md` 引用。两个触发点共用同一个核心原则：**用户提出修改意见时不手动调整 prompt，而是把修改意见作为新的一轮 image-prompt-architect 调用**，让 Skill 重新走完整的意图解析→风险预判→输出流程。

## 触发点 A：确认阶段收到修改意见（对应主文件 §4.5 用户回复处理）

用户在 Step 4 确认清单阶段提出修改意见时：

1. 保留原始 `pages[]` 数组（同一页的原始 description / characters / scene / reference_images）
2. 在 `context` 中追加 `modification_request` 字段，值为用户的完整修改意见原文
3. 重新调用 `image-prompt-architect`，Skill 会在步骤 2 中将 `modification_request` 作为**最高优先级额外意图**注入，覆盖原有相关意图（如改颜色 → 替换原颜色意图）
4. Skill 重新执行完整步骤 3→4→5（风险预判 + 结构设计 + 输出），确保修改后重新评估风险
5. 拿到新的 `prompt_text` 后，重新输出确认清单

```
用户: "蓝色太多了，改成暖色调，角色表情再开心一点"
  │
  ├─ 1. 保留原始 pages[]（description 不变）
  ├─ 2. context.modification_request = "蓝色太多改成暖色调 + 角色表情更开心"
  ├─ 3. 调用 image-prompt-architect
  │     └─ 步骤2: 注入两条最高优先级意图
  │         - 意图_修改: "色调改为暖色系（橙/金/琥珀），减少蓝色"
  │         - 意图_修改: "角色表情更加开心愉快"
  │     └─ 步骤3: 重新跑风险预判
  │     └─ 步骤5: 输出新 prompt_text
  ├─ 4. 重新输出确认清单（标注"第2轮修改"）
  └─ 5. 等待用户再次确认
```

## 触发点 B：生成后单页返工（对应主文件「单页修改模式」）

当用户对某页**已生成的图片**不满意时，**必须重新调用 `image-prompt-architect` Skill** 生成新提示词，不得手动调整 prompt：

1. 提取该页的当前插图描述原文
2. 将用户的修改意见作为**额外意图**，与原始页面数据合并，重新构造 `pages[]` 数组（只包含目标修改页）
3. 在 `context` 中追加 `modification_request: "{用户修改意见}"` 字段，供 image-prompt-architect 感知本次是修改任务
4. 调用 `image-prompt-architect`，生成新提示词（Skill 会重新跑步骤 2→3→4→5，修改意见会被纳入意图解析和风险预判）
5. 重新输出确认清单（参考图清单 + 新提示词 + 风险提示 + 假设标注）
6. 用户确认后重新生成 → 版本号递增 → `ep{X}_p{Y}_v{new_num}.png`
7. 旧版本保留不删
