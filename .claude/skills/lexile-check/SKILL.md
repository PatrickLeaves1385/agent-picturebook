---
name: lexile-check
description: 检测英文文本的蓝思值（Lexile）。触发条件：用户提到"蓝思值"、"lexile"、"检测英文文本难度"、"检查绘本英文等级"、"阅读分级"等。
---

# Lexile Check Skill

通过 CoGrader 免费 API 检测英文文本的蓝思值、AWL 覆盖率、Tier 2 词汇等指标。
API: https://cograder.com/tools/vocabulary-analyzer/ (免登录、免费、无配额限制)

## 执行步骤

### 步骤 0: 环境自检与自动修复

按顺序执行以下检查，**所有安装操作必须自动执行，不提示用户手动下载**：

#### 0.1 检查 Python

```bash
python --version 2>&1 || python3 --version 2>&1 || py --version 2>&1
```

如果输出 `Python 3.7.x` 或更高版本 -> 记录实际可用的命令名 (`python` / `python3` / `py`) 为 `$PYTHON`，跳到步骤 0.2。

如果无输出或版本 < 3.7 -> 执行 **0.1B 自动安装 Python**。

#### 0.1B 自动安装 Python

**先检测操作系统：**

```bash
uname -s 2>/dev/null || echo "Windows"
# 或 PowerShell: $env:OS
```

**Windows (使用 winget，Windows 10+ 内置):**

```powershell
# 使用 Start-Process 避免交互式弹窗
winget install Python.Python.3.12 --silent --accept-package-agreements --accept-source-agreements 2>&1

# 如果 winget 不可用（极旧的 Windows），回退到直接下载：
# PowerShell 静默下载安装：
# $url = "https://www.python.org/ftp/python/3.12.8/python-3.12.8-amd64.exe"
# $out = "$env:TEMP\python-installer.exe"
# Invoke-WebRequest -Uri $url -OutFile $out
# Start-Process -Wait -FilePath $out -ArgumentList "/quiet","InstallAllUsers=1","PrependPath=1","Include_test=0"
# Remove-Item $out
```

安装后需要刷新 PATH。在 Windows 上因为 Claude 的每个 Bash/PowerShell 调用都是独立进程，**安装完成后在新的 shell 中验证**：
```powershell
# 尝试常见路径
$py = Get-Command python -ErrorAction SilentlyContinue
if (-not $py) { $py = Get-Command py -ErrorAction SilentlyContinue }
if (-not $py) {
    # winget 安装后的默认路径
    $candidates = @(
        "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe",
        "$env:ProgramFiles\Python312\python.exe",
        "C:\Python312\python.exe"
    )
    foreach ($c in $candidates) { if (Test-Path $c) { $py = $c; break } }
}
```

如果所有路径都找不到 -> 提示用户重新打开终端后重试。

**macOS:**

优先使用 brew，无 brew 时用官方 pkg：
```bash
if command -v brew &>/dev/null; then
  brew install python@3.12 2>&1
else
  # 无 brew：下载官方 pkg 静默安装
  curl -sL "https://www.python.org/ftp/python/3.12.8/python-3.12.8-macos11.pkg" -o /tmp/python.pkg
  sudo installer -pkg /tmp/python.pkg -target / 2>&1
  rm -f /tmp/python.pkg
fi
```

安装后验证：`/usr/local/bin/python3.12 --version` 或 `/usr/local/bin/python3 --version`。

**Linux:**

```bash
# Debian/Ubuntu
if command -v apt-get &>/dev/null; then
  sudo apt-get update -qq && sudo apt-get install -y -qq python3 python3-venv 2>&1
# Red Hat/CentOS/Fedora
elif command -v dnf &>/dev/null; then
  sudo dnf install -y python3 2>&1
elif command -v yum &>/dev/null; then
  sudo yum install -y python3 2>&1
# Arch
elif command -v pacman &>/dev/null; then
  sudo pacman -S --noconfirm python 2>&1
# Alpine
elif command -v apk &>/dev/null; then
  sudo apk add --no-cache python3 2>&1
else
  echo "ERROR: Unknown Linux distribution, cannot auto-install Python"
  exit 1
fi
```

安装后验证：`python3 --version`

#### 0.2 检查脚本文件

```bash
ls -la "{{SKILL_DIR}}/lexile_api.py"
```

如果文件存在 -> 通过。

#### 0.3 检查网络

```bash
curl -s -o /dev/null -w "%{http_code}" "https://cograder.com" --connect-timeout 10 2>&1
```

- 返回 `200`/`301`/`302` -> 通过
- 返回空或超时 -> 执行代理检测

**代理检测（中国大陆常见问题）：**
```bash
# 测试是否有代理环境变量
echo "HTTP_PROXY=$HTTP_PROXY"
echo "HTTPS_PROXY=$HTTPS_PROXY"
# 如果没有代理但网络不通，提示用户：
# "CoGrader API 当前不可达，可能需要 VPN 或代理。你可以在浏览器打开 https://cograder.com 验证。"
```

#### 0.4 最终确认

输出环境检测摘要：
```
Environment check summary:
- OS: <detected>
- Python: <version> ($PYTHON command)
- Script: found
- Network: <ok/blocked>
```

### 步骤 1: 准备文本

1. 从用户指定的文件中提取英文正文
2. 如果用户引用的是 Markdown 绘本脚本，只提取 `**Text**：` 或 `- **Text**：` 后面的英文行
3. 将提取的英文文本写入临时文件（UTF-8）

提取示例（绘本脚本格式）:
```python
import re
with open(script_path, 'r', encoding='utf-8') as f:
    content = f.read()
lines = []
for line in content.split('\n'):
    m = re.match(r'^- \*\*Text\*\*[：:]\s*(.+)', line)
    if m:
        lines.append(m.group(1))
text = '\n'.join(lines)
with open(temp_file, 'w', encoding='utf-8') as f:
    f.write(text)
```

### 步骤 2: 调用脚本检测

默认使用英文全文进行单次 API 调用，**不按词数自动分块**。

```bash
$PYTHON "{{SKILL_DIR}}/lexile_api.py" <temp_file>
```

**脚本默认行为：**
- 始终优先用完整英文文本调用 API（无论词数多少）
- 仅当全文调用失败（网络错误 / 服务器 500 / 超时等）时，自动降级为分块模式作为兜底
- 分块兜底：按句子边界拆分（默认每块 ≤ 500 词），逐块调用后取 Lexile 中位数，结果标注 `"(Chunked analysis)"`
- 内置：3 次重试 + 指数退避 + 120s 超时 + 429 速率限制处理

**可选参数：**
- `--chunk-size <N>`：指定分块兜底时的每块最大词数（默认 500）
- `--no-chunk`：禁用分块兜底，全文调用失败即报错退出

```bash
# 禁用分块兜底（仅全文检测，失败即退出）
$PYTHON "{{SKILL_DIR}}/lexile_api.py" <temp_file> --no-chunk
```

> 注：CoGrader 蓝思算法以完整文本为单位评估句长与词频分布，分块会破坏统计准确性，因此分块仅作为失败兜底，不作为默认策略。

### 步骤 3: 解读结果

| 字段 | 含义 |
|---|---|
| Lexile Estimate | 蓝思值，200L-350L 为儿童绘本推荐区间 |
| Grade Band | 美国 K-12 年级 + 大致年龄 |
| Word / Sentence Count | 文本统计 |
| AWL Coverage | 学术词汇覆盖，日常写作 <4%，学术写作 6%-12% |
| AWL Words / Tier 2 Vocab | 检出词汇列表 |

**绘本项目验收参考：**
- 目标蓝思值: 250L-350L
- AWL 覆盖率: <2% 为佳（绘本 = 日常语言）
- Lexile < 250 → 句子过短，增加 1-2 个复合句
- Lexile > 300 → 句子过长，拆分或替换低频词

### 步骤 4: 报告与清理

将结果以表格展示，判断是否在目标区间内。清理临时文件。

### 步骤 3.5：结构化输出契约（供 quality-agent 解析）

`quality-agent` 通过 `active.json` 的 `_skill_groups.result_mapping` 读取本 Skill 的返回字段（`text/lexile → lexileEstimate`、`text/awl → awlCoverage`）。因此本 Skill 在给出人类可读表格的同时，**必须**输出一段可被解析的结构化 JSON，字段与 `lexile_api.py` 的 API 响应一致：

```json
{
  "lexileEstimate": 265,
  "awlCoverage": 1.8,
  "awlWords": ["demonstrate", "..."],
  "tier2Words": ["..."],
  "wordCount": 120,
  "sentenceCount": 12,
  "registerAssessment": "...",
  "note": ""   // 可选："(Chunked analysis)" / "(Low word count)"
}
```

- `lexileEstimate`、`awlCoverage` 为必填，quality-agent 据此比对 `target`（默认 250-350L，AWL <2%）。
- 分块或低词数时通过 `note` 字段标注，不丢失调试信息。
- 目标区间以 `schema/quality-checks/text/lexile.md`（250-350L）与项目级 `content-spec.md` 覆盖值为准。

## 常见问题

| 现象 | 原因 | 自动处理 |
|---|---|---|
| Python 未安装 | 新系统/精简系统 | **自动安装** (winget/brew/apt) |
| Python 版本 < 3.7 | 系统自带旧版 | 装新版到用户目录，不影响系统 Python |
| `python` 命令找不到 | Windows 未加入 PATH | 自动探测 `py` / `python3` / 安装目录 |
| 安装后 PATH 未刷新 | 当前 shell 未重载 | 尝试已知安装路径直接调用 |
| 服务器 500 | 文本过长/特殊字符 | 自动重试；失败则分块 |
| 网络超时 | 中国大陆访问慢 | 重试 + 退避；检测代理环境变量 |
| API 返回 `{error: string}` | 输入格式不对 | 至少 2 句，检查 JSON 转义 |
| 分块后 Lexile 偏低 | 短文本固有偏差 | 结果标注 `"(Chunked)"`，建议增大 chunk-size |
| `winget` 不存在 | 极旧的 Windows | 回退到 PowerShell 直接下载官方安装包 |
| `sudo` 需要密码 | 受限 Linux 环境 | 尝试 `apt-get` 的非 sudo 替代（如 `--user` 标志的 pip 方式） |

## API 说明

- **端点**: `POST https://cograder.com/api/vocabulary-analyzer/`
- **请求格式**: `{"text": "英文文本内容"}`
- **响应字段**: `lexileEstimate`, `lexileBandLabel`, `awlCoverage`, `awlWords`, `tier2Words`, `wordCount`, `sentenceCount`, `registerAssessment`
- **限制**: 免登录，免费，无硬性配额
- **蓝思值为估计值**，非 MetaMetrics 官方认证值，适用于教学决策

## 完成清单

执行完毕后向用户报告:
- 蓝思值是否在目标区间内
- 不在区间内时给出具体调整建议（句长、词汇替换）
- 如果使用了分块模式，提醒结果有标注 "(Chunked analysis)"
