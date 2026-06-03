"""
PPT 生成工具：基于讯飞开放平台 PPT API (zwapi.xfyun.cn)

两种生成模式：
1. 大纲模式（推荐）：createOutline → createPptByOutline → 轮询 → 下载链接
2. 直出模式：create_task → 轮询 → 下载链接

用法：
    from app.tools.ppt_tool import generate_ppt
    url = generate_ppt("C语言指针详解")
"""
import hashlib
import hmac
import base64
import json
import time
from typing import Optional

import requests
from requests_toolbelt.multipart.encoder import MultipartEncoder

from langchain_core.tools import tool

from app.config import settings


class PPTGenerator:
    """讯飞开放平台 PPT API 封装"""

    BASE_URL = "https://zwapi.xfyun.cn/api/ppt/v2"
    DEFAULT_TEMPLATE = "20240718489569D"

    def __init__(self, app_id: str, api_secret: str):
        self.app_id = app_id
        self.api_secret = api_secret

    # ── 签名 ──────────────────────────────────────────

    def _sign(self, ts: int) -> str:
        auth = hashlib.md5(f"{self.app_id}{ts}".encode("utf-8")).hexdigest()
        return base64.b64encode(
            hmac.new(
                self.api_secret.encode("utf-8"),
                auth.encode("utf-8"),
                hashlib.sha1,
            ).digest()
        ).decode("utf-8")

    def _common_headers(self) -> dict:
        ts = int(time.time())
        return {
            "appId": self.app_id,
            "timestamp": str(ts),
            "signature": self._sign(ts),
        }

    # ── 第一步：生成大纲 ──────────────────────────────

    def create_outline(self, topic: str, search: bool = False) -> Optional[str]:
        """根据主题生成 PPT 大纲"""
        url = f"{self.BASE_URL}/createOutline"
        form = MultipartEncoder(
            fields={
                "query": topic,
                "language": "cn",
                "search": str(search),
            }
        )
        headers = self._common_headers()
        headers["Content-Type"] = form.content_type

        resp = requests.post(url, data=form, headers=headers)
        result = resp.json()

        if result.get("code") == 0:
            outline = result["data"]["outline"]
            print(f"[PPT] ✅ 大纲生成成功 ({len(outline)} 字)")
            return outline

        print(f"[PPT] ❌ 大纲生成失败: {result.get('message', '未知错误')}")
        return None

    # ── 第二步：根据大纲创建 PPT 任务 ──────────────────

    def create_ppt_by_outline(
        self, topic: str, outline: str, template_id: str = None
    ) -> Optional[str]:
        """根据大纲创建 PPT 任务，返回 sid（任务ID）"""
        url = f"{self.BASE_URL}/createPptByOutline"
        body = {
            "query": topic,
            "outline": outline,
            "templateId": template_id or self.DEFAULT_TEMPLATE,
            "isCardNote": True,
            "search": False,
            "isFigure": True,
            "aiImage": "normal",
        }
        headers = self._common_headers()
        headers["Content-Type"] = "application/json; charset=utf-8"

        resp = requests.post(url, json=body, headers=headers)
        result = resp.json()

        if result.get("code") == 0:
            sid = result["data"]["sid"]
            print(f"[PPT] ✅ 创建任务成功 sid={sid}")
            return sid

        print(f"[PPT] ❌ 创建 PPT 任务失败: {result.get('message', '未知错误')}")
        return None

    # ── 方案B：直出模式（跳过大纲）────────────────────

    def create_task_direct(
        self, topic: str, template_id: str = None
    ) -> Optional[str]:
        """直接创建 PPT 任务（不先生成大纲），返回 sid"""
        url = f"{self.BASE_URL}/create"
        form = MultipartEncoder(
            fields={
                "query": topic,
                "templateId": template_id or self.DEFAULT_TEMPLATE,
                "isCardNote": "True",
                "search": "False",
                "isFigure": "True",
                "aiImage": "normal",
            }
        )
        headers = self._common_headers()
        headers["Content-Type"] = form.content_type

        resp = requests.post(url, data=form, headers=headers)
        result = resp.json()

        if result.get("code") == 0:
            sid = result["data"]["sid"]
            print(f"[PPT] ✅ 直出任务创建成功 sid={sid}")
            return sid

        print(f"[PPT] ❌ 直出任务创建失败: {result.get('message', '未知错误')}")
        return None

    # ── 轮询等待 ─────────────────────────────────────

    def poll_result(self, sid: str, interval: int = 3, timeout: int = 300) -> Optional[str]:
        """轮询 PPT 生成进度，返回下载 URL"""
        url = f"{self.BASE_URL}/progress"
        headers = self._common_headers()
        deadline = time.time() + timeout

        while time.time() < deadline:
            resp = requests.get(url, params={"sid": sid}, headers=headers)
            data = resp.json().get("data", {})

            ppt_status = data.get("pptStatus")
            img_status = data.get("aiImageStatus")
            note_status = data.get("cardNoteStatus")

            if ppt_status == "done" and img_status == "done" and note_status == "done":
                ppt_url = data.get("pptUrl")
                print(f"[PPT] ✅ 生成完成: {ppt_url}")
                return ppt_url

            if ppt_status == "fail":
                print(f"[PPT] ❌ 生成失败: {resp.text}")
                return None

            print(f"[PPT] ⏳ 生成中... ppt={ppt_status} img={img_status} note={note_status}")
            time.sleep(interval)

        print(f"[PPT] ❌ 轮询超时 ({timeout}s)")
        return None

    # ── 模板列表 ─────────────────────────────────────

    def list_templates(self, page: int = 1, page_size: int = 10) -> list[dict]:
        """查询可用 PPT 模板列表"""
        url = f"{self.BASE_URL}/template/list"
        headers = self._common_headers()
        params = {"pageNum": page, "pageSize": page_size}

        resp = requests.get(url, params=params, headers=headers)
        result = resp.json()

        if result.get("code") == 0:
            return result["data"].get("list", [])
        print(f"[PPT] ❌ 查询模板失败: {result.get('message', '未知错误')}")
        return []


# ── 快捷入口（供 Agent 直接调用）────────────────────

def generate_ppt(
    topic: str,
    template_id: str = None,
    use_outline: bool = True,
) -> str:
    """
    根据主题生成 PPT，返回下载链接。

    参数:
        topic: PPT 主题 / 标题
        template_id: 模板 ID，不传则用默认
        use_outline: 是否先走大纲（推荐 True，质量更高）

    返回:
        PPT 文件的下载 URL，失败时返回错误描述
    """
    app_id = settings.XF_ZWAPI_APPID
    api_secret = settings.XF_ZWAPI_APISECRET

    if not app_id or not api_secret:
        return "PPT 生成失败：未配置讯飞开放平台凭证（XF_ZWAPI_APPID / XF_ZWAPI_APISECRET）"

    ppt = PPTGenerator(app_id, api_secret)

    # 方案A：大纲模式（推荐）
    if use_outline:
        outline = ppt.create_outline(topic)
        if outline:
            sid = ppt.create_ppt_by_outline(topic, outline, template_id)
        else:
            print("[PPT] ⚠️ 大纲生成失败，降级为直出模式")
            sid = ppt.create_task_direct(topic, template_id)
    else:
        sid = ppt.create_task_direct(topic, template_id)

    if not sid:
        return "PPT 生成失败：创建任务失败"

    download_url = ppt.poll_result(sid)
    return download_url or "PPT 生成失败：生成超时或出错"


def list_ppt_templates(page: int = 1, page_size: int = 10) -> str:
    """查询可用 PPT 模板列表，返回格式化文本"""
    ppt = PPTGenerator(settings.XF_ZWAPI_APPID, settings.XF_ZWAPI_APISECRET)
    templates = ppt.list_templates(page, page_size)

    if not templates:
        return "暂无可用模板"

    lines = ["可用 PPT 模板："]
    for t in templates:
        lines.append(f"- {t.get('name', '未知')} (ID: {t.get('templateId', '')})")
    return "\n".join(lines)


# ── 测试 ────────────────────────────────────────────

@tool
def generate_ppt_tool(topic: str, use_outline: bool = True, topic_details: str = "") -> str:
    """
    根据学习主题或知识点自动生成 PPT 课件，返回下载链接。

    适用场景：
    - 学生需要系统性地学习某个知识点时，生成配套 PPT 课件
    - 老师需要备课材料时，快速生成教学 PPT

    参数:
        topic: PPT 的主题或标题，如 "C语言指针详解"
        use_outline: 是否先由 AI 生成大纲再制作 PPT（推荐 True）
        topic_details: 额外内容说明（如大纲要点、重点覆盖范围），会融入主题中让生成更精准

    返回:
        PPT 文件的下载链接，失败时返回错误描述
    """
    enriched = f"{topic} - {topic_details}" if topic_details else topic
    return generate_ppt(enriched, use_outline=use_outline)


if __name__ == "__main__":
    # 测试：查询模板
    print("=== 查询模板 ===")
    print(list_ppt_templates(page=1, page_size=5))

    # 测试：生成 PPT
    print("\n=== 生成 PPT ===")
    url = generate_ppt("C语言指针与数组的区别与联系", use_outline=True)
    print(f"下载链接: {url}")
