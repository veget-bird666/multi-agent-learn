"""
资源管理服务 — 上传本地文件到阿里云 OSS，附带资源元数据

启动：
    cd asset-manager
    pip install -r requirements.txt
    cp .env.example .env
    python server.py

访问：http://localhost:8001
"""
import base64
import hashlib
import hmac
import json
import os
import uuid
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path
from urllib.parse import quote

from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import HTMLResponse

# ── 加载 .env ───────────────────────────────────────────────
load_dotenv()

OSS_ACCESS_KEY_ID = os.getenv("OSS_ACCESS_KEY_ID", "")
OSS_ACCESS_KEY_SECRET = os.getenv("OSS_ACCESS_KEY_SECRET", "")
OSS_ENDPOINT = os.getenv("OSS_ENDPOINT", "oss-cn-guangzhou.aliyuncs.com")  # 不含 https://
OSS_BUCKET = os.getenv("OSS_BUCKET", "")
OSS_PUBLIC_DOMAIN = os.getenv("OSS_PUBLIC_DOMAIN", "")
PORT = int(os.getenv("PORT", "8001"))

# ── 数据存储 ────────────────────────────────────────────────
DATA_DIR = Path(__file__).parent / "data"
DATA_FILE = DATA_DIR / "resources.json"
DATA_DIR.mkdir(exist_ok=True)

OSS_AVAILABLE = bool(OSS_ACCESS_KEY_ID and OSS_ACCESS_KEY_SECRET and OSS_BUCKET)

# 清除代理环境变量（防 Clash/V2Ray/360 等拦截 HTTPS 请求）
for var in ("HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy", "ALL_PROXY", "all_proxy"):
    os.environ.pop(var, None)


# ── OSS 签名（阿里云 REST API）──────────────────────────────
# 阿里云 OSS 签名算法（HMAC-SHA1）：
#   Signature = base64(hmac_sha1(Key, VERB + "\n" + MD5 + "\n" + TYPE + "\n" + DATE + "\n" + Headers + Resource))

def _oss_sign(verb: str, content_md5: str, content_type: str, date: str, resource: str) -> str:
    """计算 OSS HMAC-SHA1 签名。"""
    string_to_sign = f"{verb}\n{content_md5}\n{content_type}\n{date}\n{resource}"
    h = hmac.new(OSS_ACCESS_KEY_SECRET.encode("utf-8"), string_to_sign.encode("utf-8"), hashlib.sha1)
    return base64.b64encode(h.digest()).decode()


def _oss_upload(key: str, data: bytes, content_type: str) -> tuple[bool, str]:
    """
    通过 REST API 直接上传文件到阿里云 OSS。
    返回 (是否成功, 错误消息或 URL)。
    """
    import requests as req
    from requests.packages.urllib3.exceptions import InsecureRequestWarning
    req.packages.urllib3.disable_warnings(InsecureRequestWarning)

    # 日期必须为 RFC 1123 格式
    date_str = datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S GMT")

    # CanonicalizedResource = /Bucket/Key（原始路径，不 URL 编码）
    resource = f"/{OSS_BUCKET}/{key}"

    content_type_val = content_type or "application/octet-stream"
    signature = _oss_sign("PUT", "", content_type_val, date_str, resource)

    host = f"{OSS_BUCKET}.{OSS_ENDPOINT}"
    # URL 中的 Key 需要 URL 编码（保留 /）
    encoded_key = quote(key, safe="/")
    url = f"https://{host}/{encoded_key}"
    headers = {
        "Date": date_str,
        "Content-Type": content_type_val,
        "Content-Length": str(len(data)),
        "Authorization": f"OSS {OSS_ACCESS_KEY_ID}:{signature}",
    }

    print(f"[Upload]  PUT → {url} ({len(data)/1024:.1f} KB)")
    resp = req.put(url, data=data, headers=headers, timeout=300, verify=False)
    print(f"[Upload]  HTTP {resp.status_code} {resp.reason}")

    if resp.status_code // 100 == 2:
        oss_url = f"https://{host}/{encoded_key}"
        return True, oss_url

    err = resp.text[:500] if resp.text else resp.reason
    print(f"[Upload]  OSS 错误: {err}")
    return False, err


def build_oss_url(key: str) -> str:
    """构建 OSS 对象的公网可访问 URL。"""
    if OSS_PUBLIC_DOMAIN:
        return f"https://{OSS_PUBLIC_DOMAIN}/{key}"
    return f"https://{OSS_BUCKET}.{OSS_ENDPOINT}/{key}"


# ── 资源类型 ────────────────────────────────────────────────
RESOURCE_TYPES = {
    "image": "图片",
    "video": "视频",
    "ppt": "PPT课件",
    "document": "文档",
    "mindmap": "思维导图",
    "exam": "试卷",
    "code": "代码示例",
    "other": "其他",
}

TYPE_DIR_MAP = {
    "image": "images",
    "video": "videos",
    "ppt": "ppt",
    "document": "documents",
    "mindmap": "mindmaps",
    "exam": "exams",
    "code": "code",
    "other": "other",
}


# ── 数据操作 ────────────────────────────────────────────────

def _load_resources() -> list[dict]:
    if not DATA_FILE.exists():
        return []
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return []


def _save_resources(resources: list[dict]):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(resources, f, ensure_ascii=False, indent=2)


# ── FastAPI 应用 ────────────────────────────────────────────

app = FastAPI(title="资源管理工具", version="0.1.0")


@app.get("/api/status")
async def get_status():
    return {
        "oss_configured": OSS_AVAILABLE,
        "oss_bucket": OSS_BUCKET if OSS_AVAILABLE else "",
        "oss_endpoint": OSS_ENDPOINT if OSS_AVAILABLE else "",
        "resource_count": len(_load_resources()),
    }


@app.get("/api/types")
async def list_types():
    return {"types": [{"id": k, "label": v} for k, v in RESOURCE_TYPES.items()]}


@app.get("/api/resources")
async def list_resources():
    return {"resources": _load_resources()}


@app.delete("/api/resources/{rid}")
async def delete_resource(rid: str):
    resources = _load_resources()
    resources = [r for r in resources if r.get("id") != rid]
    _save_resources(resources)
    return {"message": "已删除"}


@app.post("/api/upload")
async def upload_resource(
    file: UploadFile = File(...),
    resource_type: str = Form("other"),
    title: str = Form(""),
    description: str = Form(""),
    keywords: str = Form(""),
    subject: str = Form(""),
):
    """上传文件到 OSS 并记录元数据。"""
    if resource_type not in RESOURCE_TYPES:
        raise HTTPException(400, f"不支持的资源类型: {resource_type}")
    if not file.filename:
        raise HTTPException(400, "文件名不能为空")

    # ── 生成 OSS 存储路径 ──────────────────────────────
    ext = Path(file.filename).suffix or ""
    rid = uuid.uuid4().hex[:12]
    sub_dir = TYPE_DIR_MAP.get(resource_type, "other")
    subject_dir = subject.strip().replace(" ", "_") if subject.strip() else "general"
    oss_key = f"{sub_dir}/{subject_dir}/{rid}{ext}"

    # ── 上传到 OSS（直接 REST API）────────────────────
    file_bytes = await file.read()
    file_size = len(file_bytes)
    uploaded_url = ""
    oss_ok = False

    if OSS_AVAILABLE:
        ok, result = _oss_upload(oss_key, file_bytes, file.content_type)
        if ok:
            uploaded_url = result
            oss_ok = True
        else:
            print(f"[Upload]  上传失败: {result}")
            uploaded_url = f"local://{oss_key}"
    else:
        uploaded_url = f"local://{oss_key}"

    # ── 关键词解析 ────────────────────────────────────
    kw_list = [kw.strip() for kw in keywords.split(",") if kw.strip()]

    # ── 保存元数据 ────────────────────────────────────
    resource_entry = {
        "id": rid,
        "oss_key": oss_key,
        "url": uploaded_url,
        "oss_uploaded": oss_ok,
        "filename": file.filename,
        "file_size": file_size,
        "resource_type": resource_type,
        "title": title or file.filename,
        "description": description,
        "keywords": kw_list,
        "subject": subject,
        "created_at": datetime.now().isoformat(timespec="seconds"),
    }
    resources = _load_resources()
    resources.append(resource_entry)
    _save_resources(resources)

    return {
        "resource": resource_entry,
        "message": "上传成功" if oss_ok else f"文件已保存到本地（OSS 上传失败: {result if not oss_ok and OSS_AVAILABLE else '未配置'}）",
    }


@app.get("/", response_class=HTMLResponse)
async def index():
    html_path = Path(__file__).parent / "static" / "index.html"
    if not html_path.exists():
        return HTMLResponse("<h1>Frontend not found</h1>")
    return HTMLResponse(html_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    import uvicorn

    if not OSS_AVAILABLE:
        print("[WARN] OSS 配置不完整，文件将仅保存到本地记录（不上传）")
        print("      请完善 .env 中的 OSS_ACCESS_KEY_ID, OSS_ACCESS_KEY_SECRET, OSS_BUCKET")
    else:
        print(f"[OK] OSS 配置就绪: bucket={OSS_BUCKET}, endpoint={OSS_ENDPOINT}")

    print(f"[START] http://localhost:{PORT}")
    print(f"[DATA] {DATA_FILE}")
    print()
    uvicorn.run(app, host="0.0.0.0", port=PORT)
