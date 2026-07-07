---
title: "demo2 脚本测试版 v1：Mia and Finn Under the Moon"
summary: "demo2 故意制造的「带问题」脚本样本：5页，含 basic-safety 命中（scared）+ composition 不完整（第3页只 3/5 项）+ IP钩子缺漏 + 插图姿势缺失。用于全链路 P1+P2 验收，触发半自动修复路径。"
source: "demo2 项目构造（2026-07-06）"
project: demo2
version: v1
confidence: unverified
---

# Mia and Finn Under the Moon

> 版本: v1（测试版，故意包含多种问题用于验收）
> 生成日期: 2026-07-06
> 约束来源：
>   - wiki-context: characters.md, worldview.md, content-spec.md
>   - 用户指定: 5页绘本，英文为主
>   - 默认假设: 无
> ⚠️ 本版本含故意制造的问题（basic-safety 命中 + 插图格式不完整 + 钩子缺漏），用于验收 P1+P2 机制

## 第 1 页 开场

**Text**: Mia the rabbit hops in the garden at night. She sees a scared little fox hiding by the tree.

**中文**: 小兔 Mia 夜晚在花园里跳着。她看见一只 scared 小狐狸躲在树旁。

> ⚠️ 设计问题：scared 触发 basic-safety 命中

**插图描述**：
- 景别/视角：全景 / 平视
- 前景：Mia（白色小兔，粉色蝴蝶结），站着，侧身朝左，看向右侧
- 中景：老橡树，树后躲着 Finn（仅看到一条尾巴）
- 后景：月光洒在花园
- 情绪基调：神秘但温暖

## 第 2 页 观察

**Text**: Mia walks closer. The little fox looks at her with big eyes. He does not move.

**中文**: Mia 走近。小狐狸用大眼睛看着她。他没有动。

**插图描述**：
- 景别/视角：中景 / 平视
- 前景：Finn（橙棕色狐狸，深绿围巾），坐着，低头
- 中景：Mia 站在 Finn 旁边
- 后景：萤火虫光点（firefly dots）
- 情绪基调：犹豫、宁静

## 第 3 页 转机

**Text**: Mia smiles and says, "Let's watch the fireflies together." Finn feels a little bit better.

**中文**: Mia 笑着说："我们一起看萤火虫吧。"Finn 感觉好了一点点。

> ⚠️ 设计问题：第 3 页插图描述故意不完整（缺景别/视角 + 缺前中后景），仅满足 §4 5 项中的 2-3 项，触发 composition WARNING

**插图描述**：
- Finn 站着看萤火虫

> ⚠️ 问题：缺景别视角、缺前中后景、缺姿势朝向、缺情绪基调

## 第 4 页 共同玩耍

**Text**: They chase the fireflies. The garden glows with yellow lights. Finn laughs for the first time tonight.

**中文**: 他们追着萤火虫跑。花园被黄光照亮。Finn 今晚第一次笑了。

**插图描述**：
- 景别/视角：中景 / 平视
- 前景：Mia 跳跃，双手举起，侧身朝右
- 中景：Finn 站着（未标朝向），微笑
- 后景：萤火虫环绕（firefly circle —— 满足 IP 钩子场景 1 次）
- 情绪基调：欢快、释放

> ⚠️ 设计问题：Finn 朝向缺失，触发 character-pose WARNING

## 第 5 页 结尾

**Text**: Mia looks at Finn and says, "You are brave!" Finn smiles and they play in the rose garden until morning.

**中文**: Mia 看着 Finn 说："你很勇敢！"Finn 笑了，他们在玫瑰花园里玩到天亮。

> ✅ IP 钩子满足："You are brave!" 出现 1 次

**插图描述**：
- 景别/视角：中景 / 平视
- 前景：Mia 和 Finn 并肩，站着，面朝观众，都微笑
- 中景：玫瑰花丛（红色为主）
- 后景：天空开始泛白，月光渐淡
- 情绪基调：明亮、有成就感

---
> 已知问题汇总（用于验收）：
>   1. ⚠️ 第 1 页 Text 含 "scared" → 触发 content/basic-safety FAIL（恒定激活，人工处理）
>   2. ⚠️ 第 3 页插图描述不完整 → 触发 illustration/composition WARNING（半自动修复候选）
>   3. ⚠️ 第 4 页 Finn 朝向缺失 → 触发 illustration/character-pose WARNING（半自动修复候选，注：当前 character-pose 未激活，应 SKIP）
>   4. ℹ️ IP 钩子 "You are brave!" 第5页出现 1 次 → 满足 content-spec >= 1 次
>   5. ℹ️ 主题"犹豫→勇敢交朋友"与 demo1 相似但角度不同 → 触发 content/growth-uniqueness WARNING（系列作品豁免）
