---
id: "content/basic-safety"
category: "content"
severity: "error"
method: "pattern"
target: "基础安全词命中数 = 0"
skill: null
fail_action: "block"
activation_mode: "always-on"
priority: "global-only"
description: "通用兜底基础安全检测。恒定激活，不依赖 wiki-context。检查负面情绪词、恐怖元素、阴暗元素等绘本禁忌内容是否出现。空知识库场景下仍可执行，避免质检形同虚设。"
---
# 基础安全检测（通用兜底）

通用兜底质检项，**不依赖 wiki-context**，任何项目/任何状态下都应激活。解决空知识库场景下其他质检项 SKIP 导致质检形同虚设的问题。

## 检测方法

完全基于关键词搜索，**纯自动统计，无 LLM 介入**。逐页扫描 `**Text**:` / `**中文**:` 段，统计以下三类词表的命中数。

### 词表 1：负面情绪词

| 类别 | 词 |
|---|---|
| 恐惧 | scared / afraid / terrified / fearful / frightened |
| 悲伤 | sad / crying / weep / sob / tearful / sorrowful |
| 愤怒 | angry / rage / furious / mad / hateful |
| 暴力 | hurt / pain / fight / hit / kick / punch |
| 孤独极端 | alone / lonely / abandoned / hopeless |

### 词表 2：恐怖元素

| 类别 | 词 |
|---|---|
| 怪物 | monster / ghost / demon / witch / vampire / zombie |
| 黑暗 | dark / darkness / shadow / nightmare |
| 伤害 | blood / wound / die / death / kill |
| 威胁 | threat / terror / horror / scary |

### 词表 3：阴暗元素

| 类别 | 词 |
|---|---|
| 压抑 | hopeless / despair / miserable / wretched |
| 危险 | danger / dangerous / poison / venom / trap |
| 负面结果 | fail / failure / lose / lost / broken |

## 验收标准

| 词表 | 命中数阈值 | 判定 |
|---|---|---|
| 词表 1（负面情绪） | = 0 | ✅ PASS / ❌ FAIL（>0） |
| 词表 2（恐怖元素） | = 0 | ✅ PASS / ❌ FAIL（>0） |
| 词表 3（阴暗元素） | = 0 | ✅ PASS / ❌ FAIL（>0） |

**3 个词表全部 PASS → 该项 PASS；任一 FAIL → 该项 FAIL。**

## 量化信号（自动统计）

```
negative_emotion_hits = count(词表 1 命中)
horror_hits = count(词表 2 命中)
dark_element_hits = count(词表 3 命中)
total_hits = sum(...)
```

报告输出：
- 每类命中数
- 命中词 + 所在页码
- 建议替换词（常见替换参考见下表）

## 常见替换建议

| 命中词 | 建议替换 |
|---|---|
| scared | shy / careful / curious |
| sad | thoughtful / quiet |
| cry | tear (only if contextually needed) |
| angry | confused / surprised |
| hurt | bump / ouch (mild) |
| monster | creature / surprise |
| dark | deep blue / soft purple |
| fail | try / practice |
| alone | by himself / quietly |

## 检测范围

- 提取脚本中所有 `**Text**:` 与 `**中文**:` 后的文本
- 不区分大小写
- 整词匹配（避免 happy 误命中 hopeless 中的 hope）

## 注意事项

- 此检测是**基础安全网**，不替代项目级 emotion-tone / character-consistency 等深度语义检测
- 词表维护在质检项 `.md` 文件中（修改词表无需改 Agent 代码）
- 项目可追加自定义禁用词到 wiki 中，quality-agent 自动合并
- **恒定激活**：在 `active.json` 中不通过 `active_checks` 控制，而是通过 `activation_mode: always-on` 强制启用，避免被误停用

## 与 illustration-spec.md 禁止项的关系

illustration-spec.md §6 定义了图片侧的禁止项（不允许在图片中出现恐惧/哭泣/愤怒表情），本检测是文字侧的镜像——同一底线在文字和图片两处都生效。词表是 §6 的可执行实例化。

**本文件（basic-safety.md）是文本侧禁止词的单一权威来源**：emotion-tone 维度 2 直接复用本词表，避免在多处重复定义导致 union 漏判。如需扩充禁词，统一在本文件维护。
