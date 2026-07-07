#!/usr/bin/env python3
"""
Lexile Checker -- 通过 CoGrader API 检测英文文本蓝思值。

零依赖，仅需 Python 3.7+ 标准库。
用法:
    python lexile_api.py <file.txt>          # 从文件读取
    python lexile_api.py -                   # 从管道/标准输入读取
    echo "some text" | python lexile_api.py -  # 管道传入

策略: 始终优先完整文本调用 API；仅当全文调用失败时才降级为分块模式。

API: CoGrader Vocabulary Analyzer (https://cograder.com/tools/vocabulary-analyzer/)
- 免登录，免费，无配额限制
"""

import json
import sys
import time
import urllib.request
import urllib.error
import argparse


API_URL = "https://cograder.com/api/vocabulary-analyzer/"
MAX_RETRIES = 3
RETRY_DELAY = 5  # 秒
CHUNK_MAX_WORDS = 500  # 分块时每块最大词数（仅作为最后降级手段）
CONNECT_TIMEOUT = 120  # 单次请求总超时（秒）


def check_python_version():
    """检查 Python 版本 >= 3.7"""
    if sys.version_info < (3, 7):
        print("[ERROR] Python 3.7+ required.")
        print("Current: {}".format(sys.version))
        print("Download: https://python.org")
        sys.exit(1)


def read_text(filepath):
    """从文件或 stdin 读取文本，自动处理 UTF-8 BOM"""
    if filepath == "-":
        return sys.stdin.read()
    try:
        with open(filepath, "r", encoding="utf-8-sig") as f:
            return f.read()
    except FileNotFoundError:
        print("[ERROR] File not found '{}'".format(filepath))
        sys.exit(1)
    except UnicodeDecodeError:
        print("[ERROR] File is not UTF-8.")
        print("  Convert: iconv -f GBK -t UTF-8 input.txt > output.txt")
        sys.exit(1)


def call_api(text):
    """调用 CoGrader API，内置重试 + 超时处理"""
    payload = json.dumps({"text": text}, ensure_ascii=False).encode("utf-8")

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            req = urllib.request.Request(
                API_URL, data=payload,
                headers={
                    "Content-Type": "application/json",
                    "Origin": "https://cograder.com",
                    "Referer": "https://cograder.com/tools/vocabulary-analyzer/",
                    "User-Agent": "LexileChecker/2.0",
                },
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=CONNECT_TIMEOUT) as resp:
                return json.loads(resp.read().decode("utf-8"))

        except urllib.error.HTTPError as e:
            body = ""
            try:
                body = e.read().decode("utf-8")[:200]
            except Exception:
                pass
            if e.code == 500:
                if attempt < MAX_RETRIES:
                    delay = RETRY_DELAY * attempt
                    print("  [RETRY {}/{}] HTTP 500, waiting {}s...".format(
                        attempt, MAX_RETRIES, delay))
                    time.sleep(delay)
                    continue
                print("[ERROR] Server returned 500 after {} retries.".format(MAX_RETRIES))
                if body:
                    print("  Response: {}".format(body))
                print("  Smaller text chunks may succeed (automatic chunked fallback will retry if applicable)")
                return None
            elif e.code == 429:
                if attempt < MAX_RETRIES:
                    delay = RETRY_DELAY * attempt * 2
                    print("  [RETRY {}/{}] Rate limited, waiting {}s...".format(
                        attempt, MAX_RETRIES, delay))
                    time.sleep(delay)
                    continue
                print("[ERROR] API rate limited. Wait 60s and retry.")
                return None
            else:
                print("[ERROR] HTTP {} - {}".format(e.code, e.reason))
                return None

        except urllib.error.URLError as e:
            if attempt < MAX_RETRIES:
                delay = RETRY_DELAY * attempt
                print("  [RETRY {}/{}] Network error, waiting {}s...".format(
                    attempt, MAX_RETRIES, delay))
                time.sleep(delay)
                continue
            print("[ERROR] Cannot reach CoGrader API.")
            print("  Reason: {}".format(e.reason))
            print("  Check: curl -s -o /dev/null -w '%{{http_code}}' https://cograder.com")
            return None

        except TimeoutError:
            if attempt < MAX_RETRIES:
                delay = RETRY_DELAY * attempt
                print("  [RETRY {}/{}] Timeout, waiting {}s...".format(
                    attempt, MAX_RETRIES, delay))
                time.sleep(delay)
                continue
            print("[ERROR] Request timed out. API may be slow.")
            print("  Smaller text chunks may succeed on retry (try --chunk-size 200)")
            return None

        except json.JSONDecodeError:
            print("[ERROR] API returned invalid JSON. Retry later.")
            return None

    return None


def split_into_chunks(text, max_words):
    """按句子边界拆分为词数可控的块"""
    import re
    # 按句子边界分割（保留标点）
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    chunks = []
    current = []
    current_words = 0
    for s in sentences:
        wc = len(s.split())
        if current_words + wc > max_words and current:
            chunks.append(" ".join(current))
            current = []
            current_words = 0
        current.append(s)
        current_words += wc
    if current:
        chunks.append(" ".join(current))
    return chunks


def call_api_chunked(text, chunk_size):
    """分块调用 API 并汇总结果"""
    chunks = split_into_chunks(text, chunk_size)
    if len(chunks) == 1:
        # 不分块
        return call_api(text)

    print("  Splitting into {} chunks (max {} words each)...".format(
        len(chunks), chunk_size))

    results = []
    all_awl = set()
    all_tier2 = set()
    all_lexile = []

    for i, chunk in enumerate(chunks):
        print("  Chunk {}/{} ({} words)...".format(i + 1, len(chunks), len(chunk.split())))
        r = call_api(chunk)
        if r is None:
            print("  Warning: Chunk {} failed, skipping.".format(i + 1))
            continue
        results.append(r)
        all_lexile.append(r.get("lexileEstimate", 0))
        all_awl.update(r.get("awlWords", []))
        all_tier2.update(r.get("tier2Words", []))
        time.sleep(1)  # 避免频率限制

    if not results:
        print("[ERROR] All chunks failed.")
        sys.exit(1)

    # 汇总：Lexile 取中位数，AWL/Tier2 取并集
    all_lexile.sort()
    median_lexile = all_lexile[len(all_lexile) // 2]

    return {
        "lexileEstimate": int(median_lexile),
        "lexileBandLabel": lexile_to_band(int(median_lexile)),
        "awlCoverage": len(all_awl) / max(result.get("wordCount", 1) for result in results) if all_awl else 0,
        "awlWords": sorted(all_awl),
        "tier2Words": sorted(all_tier2),
        "wordCount": sum(r.get("wordCount", 0) for r in results),
        "sentenceCount": sum(r.get("sentenceCount", 0) for r in results),
        "registerAssessment": "(Chunked analysis, {} segments)".format(len(results)),
    }


def lexile_to_band(lexile):
    """Lexile 值映射到年级标签（近似）"""
    if lexile <= 200:
        return "Beginning Reader"
    elif lexile <= 300:
        return "Grade K-1"
    elif lexile <= 450:
        return "Grade 1-2"
    elif lexile <= 600:
        return "Grade 2-3"
    elif lexile <= 750:
        return "Grade 3-4"
    elif lexile <= 900:
        return "Grade 4-5"
    elif lexile <= 1000:
        return "Grade 5-6"
    elif lexile <= 1100:
        return "Grade 6-8"
    elif lexile <= 1200:
        return "Grade 9-10"
    else:
        return "Grade 11-12"


def grade_to_age(lexile_band):
    """将 Lexile 年级标签映射到大致年龄"""
    mapping = {
        "Beginning Reader": "2-5 岁",
        "Grade K-1": "5-7 岁",
        "Grade 1-2": "6-8 岁",
        "Grade 2-3": "7-9 岁",
        "Grade 3-4": "8-10 岁",
        "Grade 4-5": "9-11 岁",
        "Grade 5-6": "10-12 岁",
        "Grade 6-8": "11-14 岁",
        "Grade 9-10": "14-16 岁",
        "Grade 11-12": "16-18 岁",
    }
    return mapping.get(lexile_band, lexile_band)


def format_output(result):
    """格式化输出检测结果"""
    lexile = result.get("lexileEstimate", "N/A")
    band = result.get("lexileBandLabel", "N/A")
    awl = result.get("awlCoverage", 0)
    awl_words = result.get("awlWords", [])
    tier2 = result.get("tier2Words", [])
    word_count = result.get("wordCount", 0)
    sentence_count = result.get("sentenceCount", 0)
    register = result.get("registerAssessment", "")

    in_range = ""
    if isinstance(lexile, int) and 200 <= lexile <= 350:
        in_range = " [in target range for children's picture books: 200L-350L]"

    avg_sl = word_count / sentence_count if sentence_count > 0 else 0

    print("=" * 60)
    print("  Lexile Analysis Results")
    print("=" * 60)
    print("  Lexile Estimate :  {}L{}".format(lexile, in_range))
    print("  Grade Band      :  {} ({})".format(band, grade_to_age(band)))
    print("  Word Count      :  {}".format(word_count))
    print("  Sentence Count  :  {}".format(sentence_count))
    print("  Avg. Sent. Len  :  {:.1f} words/sentence".format(avg_sl))
    print("")
    # API returns awlCoverage inconsistently: sometimes as fraction (0.012),
    # sometimes as percentage (1.2). Detect and normalize.
    if awl > 1.0:
        awl_display = "{}%".format(round(awl, 1))
    else:
        awl_display = "{:.1%}".format(awl)

    print("  AWL Coverage    :  {}".format(awl_display))
    print("  AWL Words       :  {}".format(
        ", ".join(awl_words) if awl_words else "(none)"))
    print("  Tier 2 Vocab    :  {}".format(
        ", ".join(tier2) if tier2 else "(none)"))
    print("")
    if register and not register.startswith("(Chunked"):
        clean = register.replace("\n", " ").strip()
        print("  Register        :  {}...".format(clean[:250]))
    elif register:
        print("  Note            :  {}".format(register))
    print("=" * 60)

    return {
        "lexile": lexile,
        "band": band,
        "in_target_range": bool(isinstance(lexile, int) and 200 <= lexile <= 350),
    }


def main():
    parser = argparse.ArgumentParser(
        description="Lexile Checker - 通过 CoGrader API 检测英文文本蓝思值")
    parser.add_argument("input", nargs="?", default="-",
                        help="Input file (use '-' for stdin)")
    parser.add_argument("--chunk-size", type=int, default=CHUNK_MAX_WORDS,
                        help="Fallback chunk size in words (default: {})".format(CHUNK_MAX_WORDS))
    parser.add_argument("--no-chunk", action="store_true",
                        help="Disable chunked fallback entirely")
    args = parser.parse_args()

    check_python_version()

    text = read_text(args.input).strip()
    if not text:
        print("[ERROR] Input is empty. Need at least 2 English sentences.")
        sys.exit(1)

    word_count = len(text.split())
    sent_count = text.count(".") + text.count("!") + text.count("?")
    print("  Input: {} words / ~{} sentences".format(word_count, sent_count))

    # Always try full-text first for the most accurate Lexile measurement.
    # CoGrader's Lexile algorithm evaluates the complete text as a single unit;
    # chunking fundamentally breaks sentence-length and word-frequency statistics.
    result = call_api(text)

    if result is not None:
        format_output(result)
        return

    # Full-text call failed. Unless --no-chunk, try chunked fallback with warning.
    if args.no_chunk:
        print("[ERROR] Full-text API call failed and --no-chunk is set. Aborting.")
        print("  Try again later or paste the text directly at https://cograder.com/tools/vocabulary-analyzer/")
        sys.exit(1)

    print("\n  Full-text call failed. Falling back to chunked mode...")
    print("  NOTE: Chunked Lexile is approximate. For the most accurate")
    print("  result, paste directly at https://cograder.com/tools/vocabulary-analyzer/")
    print("")

    result = call_api_chunked(text, args.chunk_size)
    if result is None:
        print("[ERROR] All attempts (full-text + chunked) failed.")
        print("  Try pasting directly: https://cograder.com/tools/vocabulary-analyzer/")
        sys.exit(1)

    format_output(result)


if __name__ == "__main__":
    main()
