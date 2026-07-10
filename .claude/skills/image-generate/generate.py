"""
n1n 图片生成 API 调用封装（多后端）。
由 image-generate Skill 通过 Bash 调用，
负责后端选择、端点路由、HTTP请求（带重试）、base64解码保存、元数据写入。

支持后端:
- gpt-image-2:  OpenAI 兼容接口，/v1/images/generations 和 /v1/images/edits
- nano-banana-2:  Gemini 3.1 Flash Image，/v1beta/models/gemini-3.1-flash-image:generateContent

API 网关: https://llm-api.net (n1n，国内直连)
"""

import sys
import re
import json
import time
import base64
import argparse
import os
import requests
from datetime import datetime
from pathlib import Path


# === 配置 ===
BASE_URL = "https://llm-api.net"
TIMEOUT = 400                  # 单请求超时（秒），多参考图生成可达 3-4 分钟
MAX_RETRIES = 3                # 瞬时错误（429/5xx/网络）重试次数

# 后端模型名
MODEL_GPT = "gpt-image-2"
MODEL_GEMINI = "gemini-3.1-flash-image"

# 分辨率 → 像素映射（nano-banana-2，以 1:1 比例为基准）
# 注意：仅用于 _metadata.json 的 requested_size 近似值，实际输出尺寸由 API 按具体 aspectRatio 决定
RESOLUTION_MAP = {
    "1K": "1024x1024",
    "2K": "2048x2048",
    "4K": "2880x2880",
}


def map_size(ratio_or_size: str) -> str:
    """如果输入是比例（如 '1:1'）则映射为像素尺寸，否则原样返回。
    
    仅用于 gpt-image-2 后端（将比例转为具体像素）。
    nano-banana-2 不使用此函数（比例+分辨率直接透传 API）。
    所有映射值来自 n1n 官方文档，默认取 1K 分辨率。
    """
    ratio_map = {
        "21:9":  "1344x576",
        "16:9":  "1280x720",
        "5:4":   "1040x832",
        "4:3":   "1024x768",
        "3:2":   "1008x672",
        "1:1":   "1024x1024",
        "2:3":   "672x1008",
        "3:4":   "768x1024",
        "4:5":   "832x1040",
        "9:16":  "720x1280",
    }
    cleaned = ratio_or_size.strip().replace(" ", "")
    if cleaned in ratio_map:
        return ratio_map[cleaned]
    return cleaned


def _request_with_retry(fn) -> requests.Response:
    """执行 HTTP 请求，对瞬时错误做指数退避重试。

    重试范围：网络连接异常、超时、429 限流、5xx 服务端错误。
    不重试：401 鉴权错误（密钥无效，重试无意义）。
    """
    last_exc = None
    for attempt in range(MAX_RETRIES):
        try:
            return fn()
        except requests.HTTPError as e:
            status = e.response.status_code if e.response is not None else 0
            if status == 401:
                raise  # 鉴权失败，立即抛出，不重试
            last_exc = e
            if attempt < MAX_RETRIES - 1:
                wait = 5 * (2 ** attempt)
                print(f"[retry] HTTP {status}，{wait}s 后重试 ({attempt+1}/{MAX_RETRIES-1})",
                      file=sys.stderr)
                time.sleep(wait)
        except requests.RequestException as e:
            last_exc = e
            if attempt < MAX_RETRIES - 1:
                wait = 5 * (2 ** attempt)
                print(f"[retry] 网络错误: {e}，{wait}s 后重试 ({attempt+1}/{MAX_RETRIES-1})",
                      file=sys.stderr)
                time.sleep(wait)
    raise last_exc


def _parse_version(output_path: str):
    """从文件名解析 episode/page/version。仅对 ep{X}_p{Y}_v{Z}.png 有效。"""
    name = Path(output_path).stem
    m = re.match(r"ep(\d+)_p(\d+)_v(\d+)", name)
    if m:
        return int(m.group(1)), int(m.group(2)), int(m.group(3))
    return None, None, None


def _detect_image_format(filepath: Path) -> str:
    """检测图片实际格式，返回 'PNG' 或 'JPEG'。"""
    with open(filepath, 'rb') as f:
        header = f.read(4)
    if header[:2] == b'\xff\xd8':
        return 'JPEG'
    elif header[:4] == b'\x89PNG':
        return 'PNG'
    return 'UNKNOWN'


def _get_image_dimensions(filepath: Path) -> tuple[int, int]:
    """读取图片实际像素尺寸（优先 PIL，回退 struct 解析 PNG）。"""
    try:
        from PIL import Image
        with Image.open(filepath) as img:
            return img.width, img.height
    except ImportError:
        pass

    import struct
    with open(filepath, 'rb') as f:
        header = f.read(24)
    if header[:4] == b'\x89PNG':
        w, h = struct.unpack('>II', header[16:24])
        return w, h
    if header[:2] == b'\xff\xd8':
        # JPEG：扫描 SOF0 标记（0xFFC0）读取尺寸
        with open(filepath, 'rb') as f:
            f.seek(2)
            while True:
                marker_byte = f.read(1)
                if marker_byte != b'\xff':
                    continue
                marker = f.read(1)
                if marker in (b'\xc0', b'\xc1', b'\xc2'):
                    f.seek(3, 1)
                    h, w = struct.unpack('>HH', f.read(4))
                    return w, h
                seg_len = struct.unpack('>H', f.read(2))[0]
                f.seek(seg_len - 2, 1)
    raise RuntimeError(f"无法解析图片尺寸: {filepath}")


def _write_metadata(output_path: str, model: str, requested_size: str, quality: str,
                    endpoint: str, references: list, revised_prompt: str, backend: str):
    """生成成功后，在同目录写入/追加 _metadata.json。"""
    out = Path(output_path)
    meta_path = out.parent / "_metadata.json"
    ep, page, ver = _parse_version(output_path)

    # 读取实际像素尺寸
    actual_w, actual_h = _get_image_dimensions(out)
    actual_size = f"{actual_w}x{actual_h}"

    entry = {
        "page": page,
        "episode": ep,
        "version": ver,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "prompt_source": "image-prompt-architect",
        "image_size": actual_size,           # 真实输出像素
        "requested_size": requested_size,    # 调用方请求的尺寸（比例映射后）
        "image_quality": quality,
        "model": model,
        "backend": backend,
        "api_endpoint": endpoint,
        "api_gateway": "n1n",
        "references_used": {
            "injected": references,
            "text_referenced": [],
        },
        "revised_prompt": revised_prompt,
        "status": "generated",
    }

    data = {}
    if meta_path.exists():
        try:
            data = json.loads(meta_path.read_text(encoding="utf-8"))
        except Exception:
            data = {}
    data[out.name] = entry
    meta_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


# ============================================================
#  GPT-IMAGE-2 后端（OpenAI 兼容）
# ============================================================

def _extract_b64_openai(result: dict) -> str:
    """从 OpenAI 兼容响应中提取 base64 图片数据。"""
    if "data" in result and isinstance(result["data"], list) and len(result["data"]) > 0:
        return result["data"][0].get("b64_json", "")
    if "choices" in result:
        for choice in result.get("choices", []):
            msg = choice.get("message", {})
            content = msg.get("content", "")
            if isinstance(content, str) and len(content) > 100:
                return content
    if result.get("b64_json"):
        return result["b64_json"]
    return ""


def _extract_revised_openai(result: dict) -> str:
    """从 OpenAI 兼容响应中提取修订提示词。"""
    if "data" in result and isinstance(result["data"], list) and len(result["data"]) > 0:
        return result["data"][0].get("revised_prompt", "") or ""
    return ""


def gpt_text_to_image(
    prompt: str, size: str, quality: str,
    api_key: str, output_path: str,
) -> dict:
    """文生图：POST /v1/images/generations（无参考图）。"""
    url = f"{BASE_URL}/v1/images/generations"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": MODEL_GPT,
        "prompt": prompt,
        "size": map_size(size),
        "n": 1,
        "quality": quality,
        "response_format": "b64_json",
    }

    resp = _request_with_retry(
        lambda: requests.post(url, headers=headers, json=payload, timeout=TIMEOUT)
    )
    resp.raise_for_status()
    result = resp.json()

    b64 = _extract_b64_openai(result)
    if not b64:
        raise RuntimeError("API 未返回 b64_json 数据: " + json.dumps(result, ensure_ascii=False)[:300])

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(base64.b64decode(b64))

    # 检测实际格式，必要时修正扩展名
    fmt = _detect_image_format(out)
    if fmt == "JPEG" and out.suffix.lower() != ".jpg":
        new_path = out.with_suffix(".jpg")
        out.rename(new_path)
        out = new_path
    elif fmt == "PNG" and out.suffix.lower() != ".png":
        new_path = out.with_suffix(".png")
        out.rename(new_path)
        out = new_path

    revised = _extract_revised_openai(result)
    _write_metadata(str(out), MODEL_GPT, map_size(size), quality,
                    "generations", [], revised, "gpt-image-2")

    return {
        "output_path": str(out),
        "revised_prompt": revised,
    }


def gpt_image_to_image(
    prompt: str, size: str, quality: str,
    api_key: str, reference_images: list[str], output_path: str,
) -> dict:
    """图生图：POST /v1/images/edits（multipart form-data，支持多张参考图）。"""
    url = f"{BASE_URL}/v1/images/edits"
    headers = {"Authorization": f"Bearer {api_key}"}

    data = {
        "model": (None, MODEL_GPT),
        "prompt": (None, prompt),
        "n": (None, "1"),
        "size": (None, map_size(size)),
        "response_format": (None, "b64_json"),
    }
    if quality:
        data["quality"] = (None, quality)

    files = []
    for ref_path in reference_images:
        p = Path(ref_path)
        if not p.exists():
            raise FileNotFoundError(f"参考图不存在: {ref_path}")
        ext = p.suffix.lower()
        mime = "image/png" if ext == ".png" else "image/jpeg" if ext in (".jpg", ".jpeg") else "image/png"
        files.append(("image", (p.name, p.read_bytes(), mime)))

    resp = _request_with_retry(
        lambda: requests.post(url, headers=headers, data=data, files=files, timeout=TIMEOUT)
    )
    resp.raise_for_status()
    result = resp.json()

    b64 = _extract_b64_openai(result)
    if not b64:
        raise RuntimeError("API 未返回 b64_json 数据: " + json.dumps(result, ensure_ascii=False)[:300])

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(base64.b64decode(b64))

    # 检测实际格式，必要时修正扩展名
    fmt = _detect_image_format(out)
    if fmt == "JPEG" and out.suffix.lower() != ".jpg":
        new_path = out.with_suffix(".jpg")
        out.rename(new_path)
        out = new_path
    elif fmt == "PNG" and out.suffix.lower() != ".png":
        new_path = out.with_suffix(".png")
        out.rename(new_path)
        out = new_path

    revised = _extract_revised_openai(result)

    _write_metadata(str(out), MODEL_GPT, map_size(size), quality,
                    "edits", list(reference_images), revised, "gpt-image-2")

    return {
        "output_path": str(out),
        "revised_prompt": revised,
    }


# ============================================================
#  NANO-BANANA-2 后端（Gemini 3.1 Flash Image）
# ============================================================

def _image_to_base64_data_uri(image_path: str) -> tuple[str, str]:
    """将本地图片转为 base64 data URI，返回 (data_uri, mime_type)。"""
    p = Path(image_path)
    if not p.exists():
        raise FileNotFoundError(f"参考图不存在: {image_path}")
    ext = p.suffix.lower()
    mime = "image/png" if ext == ".png" else "image/jpeg" if ext in (".jpg", ".jpeg") else "image/png"
    b64 = base64.b64encode(p.read_bytes()).decode("ascii")
    return b64, mime


def _build_gemini_payload(prompt: str, reference_images: list[str],
                          aspect_ratio: str = None, image_size: str = None) -> dict:
    """构建 Gemini generateContent 请求体。

    parts[] 包含:
    - 文生图: [{"text": "prompt"}]
    - 图生图: [{"text": "prompt"}, {"inline_data": {...}}, ...]

    generationConfig.imageConfig（n1n 原生支持）:
    - aspectRatio: 宽高比例，如 "1:1", "4:3", "16:9", "9:16" 等
    - imageSize:   分辨率等级，如 "1K", "2K", "4K"
    """
    parts = [{"text": prompt}]

    for ref_path in reference_images:
        b64_data, mime_type = _image_to_base64_data_uri(ref_path)
        parts.append({
            "inline_data": {
                "mime_type": mime_type,
                "data": b64_data,
            }
        })

    gen_config = {
        "responseModalities": ["IMAGE", "TEXT"],
    }

    # 通过 imageConfig 指定宽高比和分辨率（n1n 原生支持）
    image_config = {}
    if aspect_ratio:
        image_config["aspectRatio"] = aspect_ratio
    if image_size:
        image_config["imageSize"] = image_size
    if image_config:
        gen_config["imageConfig"] = image_config

    return {
        "contents": [{
            "role": "user",
            "parts": parts,
        }],
        "generationConfig": gen_config,
    }


def _extract_gemini_b64(result: dict) -> str:
    """从 Gemini generateContent 响应中提取 base64 图片数据。

    响应格式（Gemini 原生）:
    {
      "candidates": [{
        "content": {
          "parts": [
            {"text": "..."},
            {"inlineData": {"mimeType": "image/png", "data": "<base64>"}}
          ]
        },
        "finishReason": "STOP"
      }]
    }
    """
    candidates = result.get("candidates", [])
    for candidate in candidates:
        content = candidate.get("content", {})
        for part in content.get("parts", []):
            inline = part.get("inlineData") or part.get("inline_data")
            if inline and inline.get("data"):
                return inline["data"]
    return ""


def _extract_gemini_text(result: dict) -> str:
    """从 Gemini 响应中提取文本内容（修订提示词等）。"""
    candidates = result.get("candidates", [])
    texts = []
    for candidate in candidates:
        content = candidate.get("content", {})
        for part in content.get("parts", []):
            if "text" in part and part["text"]:
                texts.append(part["text"])
    return " ".join(texts).strip()


def _resolution_to_size(resolution: str) -> str:
    """将分辨率（1K/2K/4K）映射为像素尺寸字符串。"""
    return RESOLUTION_MAP.get(resolution.upper(), "1024x1024")


def gemini_generate(
    prompt: str, size: str, quality: str,
    api_key: str, reference_images: list[str], output_path: str,
    resolution: str = "1K",
) -> dict:
    """通过 n1n Gemini 端点生成图片。

    端点: POST /v1beta/models/gemini-3.1-flash-image:generateContent
    请求格式: Gemini 原生 contents[].parts[]
    参考图: base64 内联（inline_data）
    分辨率: 1K / 2K / 4K
    """
    url = f"{BASE_URL}/v1beta/models/{MODEL_GEMINI}:generateContent"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    # 解析 aspect ratio（从 size 参数提取比例部分，如 "1:1", "4:3"）
    cleaned_size = size.strip().replace(" ", "")
    aspect_ratio = cleaned_size if ':' in cleaned_size else None

    payload = _build_gemini_payload(prompt, reference_images,
                                    aspect_ratio=aspect_ratio,
                                    image_size=resolution.upper())

    resp = _request_with_retry(
        lambda: requests.post(url, headers=headers, json=payload, timeout=TIMEOUT)
    )
    resp.raise_for_status()
    result = resp.json()

    b64 = _extract_gemini_b64(result)
    if not b64:
        raise RuntimeError("Gemini API 未返回图片数据: " + json.dumps(result, ensure_ascii=False)[:500])

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(base64.b64decode(b64))

    # 检测实际格式，必要时修正扩展名（nano-banana-2 输出 JPEG 但存为 .png）
    fmt = _detect_image_format(out)
    if fmt == "JPEG" and out.suffix.lower() != ".jpg":
        new_path = out.with_suffix(".jpg")
        out.rename(new_path)
        out = new_path
    elif fmt == "PNG" and out.suffix.lower() != ".png":
        new_path = out.with_suffix(".png")
        out.rename(new_path)
        out = new_path

    revised = _extract_gemini_text(result)

    endpoint_label = "gemini-generateContent"
    requested_size = _resolution_to_size(resolution)

    _write_metadata(str(out), MODEL_GEMINI, requested_size, quality,
                    endpoint_label, list(reference_images), revised, "nano-banana-2")

    return {
        "output_path": str(out),
        "revised_prompt": revised,
    }


# ============================================================
#  主入口
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="n1n 图片生成（多后端）")
    parser.add_argument("--prompt", required=True, help="生成提示词")
    parser.add_argument("--size", required=True, help="尺寸（比例如 1:1 或像素如 1024x1024）")
    parser.add_argument("--quality", required=True, help="画质: low/medium/high/auto")
    parser.add_argument("--api-key", required=False, default=None,
                        help="n1n API 密钥（Bearer Token）。缺省时回退到环境变量 N1N_API_KEY 或 .agent-cache/n1n-api-key 文件")
    parser.add_argument("--output", required=True, help="输出文件路径")
    parser.add_argument("--refs", nargs="*", default=[], help="参考图路径列表（可选，空格分隔，支持多张）")
    parser.add_argument("--json", action="store_true", help="以 JSON 格式输出结果")
    parser.add_argument("--backend", default="gpt-image-2", choices=["gpt-image-2", "nano-banana-2"],
                        help="生图后端: gpt-image-2（默认，OpenAI兼容）/ nano-banana-2（Gemini 3.1 Flash Image）")
    parser.add_argument("--resolution", default="1K", choices=["1K", "2K", "4K"],
                        help="nano-banana-2 分辨率: 1K/2K/4K（仅 nano-banana-2 后端有效）")

    args = parser.parse_args()

    # 解析 API Key：命令行参数 > 环境变量 N1N_API_KEY > .agent-cache/n1n-api-key 文件
    api_key = args.api_key or os.environ.get("N1N_API_KEY")
    if not api_key:
        key_file = Path(".agent-cache/n1n-api-key")
        if key_file.exists():
            api_key = key_file.read_text(encoding="utf-8").strip()
    if not api_key:
        print(json.dumps({
            "error": "缺少 n1n API 密钥：请通过 --api-key 传入、设置环境变量 N1N_API_KEY，或在 .agent-cache/n1n-api-key 放置密钥文件"
        }, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)

    try:
        if args.backend == "nano-banana-2":
            result = gemini_generate(
                prompt=args.prompt,
                size=args.size,
                quality=args.quality,
                api_key=api_key,
                reference_images=args.refs,
                output_path=args.output,
                resolution=args.resolution,
            )
        else:
            # gpt-image-2（默认）
            if args.refs:
                result = gpt_image_to_image(
                    prompt=args.prompt,
                    size=args.size,
                    quality=args.quality,
                    api_key=api_key,
                    reference_images=args.refs,
                    output_path=args.output,
                )
            else:
                result = gpt_text_to_image(
                    prompt=args.prompt,
                    size=args.size,
                    quality=args.quality,
                    api_key=api_key,
                    output_path=args.output,
                )

        if args.json:
            print(json.dumps(result, ensure_ascii=False))
        else:
            print(result["output_path"])

    except requests.HTTPError as e:
        detail = ""
        try:
            detail = e.response.text[:500]
        except Exception:
            pass
        error_payload = {"error": f"API 返回 {e.response.status_code}: {detail}"}
        print(json.dumps(error_payload, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        error_payload = {"error": str(e)}
        print(json.dumps(error_payload, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
