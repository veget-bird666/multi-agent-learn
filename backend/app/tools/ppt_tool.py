"""
PPT 生成工具：基于文多多 AiPPT 开放平台便携式生成 API

两个步骤：
  1. create-task  → 获得 taskId
  2. task-result  → 轮询直到 status=success，拿到 fileUrl

用法：
    from app.tools.ppt_tool import generate_ppt
    url = generate_ppt("C语言指针详解")
"""
import json
import time
from typing import Optional

import requests

from app.config import settings


# 默认模板 ID（教育培训类）
DEFAULT_TEMPLATE_ID = "2031929779984429056"

# 轮询配置
POLL_INTERVAL = 3       # 秒
POLL_TIMEOUT = 300      # 总超时 5 分钟


class DocmeePPTGenerator:
    """文多多 AiPPT 便携式生成 API 封装"""

    API_CREATE = "https://open.docmee.cn/v2/api/portable/create-task"
    API_RESULT = "https://open.docmee.cn/v2/api/portable/task-result"

    def __init__(self, token: str):
        self.token = token

    # ── 请求头 ──────────────────────────────────────────

    def _headers(self) -> dict:
        return {
            "Content-Type": "application/json",
            "token": self.token,
        }

    # ── 第一步：创建任务 ────────────────────────────────

    def create_task(self, topic: str, template_id: str = None,
                    length: str = "medium", lang: str = "zh") -> Optional[str]:
        """
        创建便携版 PPT 生成任务，返回 taskId。

        参数:
            topic: PPT 主题
            template_id: 模板 ID，默认教育培训类模板
            length: 内容长度 short / medium / long
            lang: 输出语言（zh / en 等）
        """
        body = {
            "type": 1,                                  # 智能生成
            "content": topic,
            "templateId": template_id or DEFAULT_TEMPLATE_ID,
            "stream": False,
            "length": length,
            "lang": lang,
            "scene": "教育培训",                         # 演示场景
            "audience": "学生",                          # 受众
        }

        print(f"[DocmeePPT]  创建任务: {topic[:40]}...")
        print(f"[DocmeePPT]  templateId={body['templateId']}")

        try:
            resp = requests.post(self.API_CREATE,
                                 headers=self._headers(),
                                 json=body,
                                 timeout=30)
        except requests.RequestException as e:
            print(f"[DocmeePPT]  网络请求失败: {e}")
            return None

        if resp.status_code != 200:
            print(f"[DocmeePPT]  HTTP {resp.status_code}: {resp.text[:200]}")
            return None

        result = resp.json()
        if result.get("code") != 0:
            print(f"[DocmeePPT]  API 错误: {result.get('message', result)}")
            return None

        task_id = result.get("data", {}).get("taskId")
        if task_id:
            print(f"[DocmeePPT]  任务创建成功: taskId={task_id}")
            return task_id

        print(f"[DocmeePPT]  响应中无 taskId: {result}")
        return None

    # ── 第二步(轮询)：查询结果 ──────────────────────────

    def query_result(self, task_id: str) -> dict:
        """查询一次任务状态，返回 data 字段。"""
        body = {"taskId": task_id}
        try:
            resp = requests.post(self.API_RESULT,
                                 headers=self._headers(),
                                 json=body,
                                 timeout=15)
        except requests.RequestException as e:
            return {"status": "error", "errorMessage": str(e)}

        if resp.status_code != 200:
            return {"status": "error", "errorMessage": f"HTTP {resp.status_code}"}

        result = resp.json()
        if result.get("code") != 0:
            return {"status": "error",
                    "errorMessage": result.get("message", "unknown error")}

        return result.get("data", {})

    def poll_result(self, task_id: str) -> Optional[str]:
        """
        轮询任务结果，返回 PPT 下载地址（fileUrl）。
        超时返回 None。
        """
        deadline = time.time() + POLL_TIMEOUT

        while time.time() < deadline:
            data = self.query_result(task_id)
            status = data.get("status", "")
            progress = data.get("progress")
            step = data.get("step", "")

            if status == "success":
                file_url = data.get("fileUrl")
                if file_url:
                    print(f"[DocmeePPT]  生成成功: {file_url}")
                    return file_url
                # 有 status=success 但无 fileUrl，等下一轮
                print(f"[DocmeePPT]  status=success 但无 fileUrl，继续等待")
                time.sleep(POLL_INTERVAL)
                continue

            elif status == "failed":
                err_msg = data.get("errorMessage", "未知错误")
                err_code = data.get("errorCode", "")
                print(f"[DocmeePPT]  生成失败: [{err_code}] {err_msg}")
                return None

            elif status == "pending" or status == "processing":
                print(f"[DocmeePPT]  生成中... progress={progress} step={step}")
                time.sleep(POLL_INTERVAL)
                continue

            else:
                print(f"[DocmeePPT]  未知状态: {status}")
                time.sleep(POLL_INTERVAL)
                continue

        print(f"[DocmeePPT]  轮询超时 ({POLL_TIMEOUT}s)")
        return None

    # ── 一站式生成 ──────────────────────────────────────

    def generate(self, topic: str, template_id: str = None,
                 length: str = "medium") -> str:
        """
        根据主题生成 PPT，返回下载链接。

        参数:
            topic: PPT 主题
            template_id: 模板 ID
            length: 内容长度

        返回:
            PPT 文件的下载 URL，失败时返回错误描述
        """
        if not self.token:
            return (
                "PPT 生成失败：未配置文多多 AiPPT API Key。\n"
                "请将 API Key 填入 backend/.env 的 DOCMEE_API_KEY。"
            )

        # 创建任务
        task_id = self.create_task(topic, template_id, length)
        if not task_id:
            return "PPT 生成失败：无法创建生成任务，请检查 API Key 和网络连接"

        # 轮询结果
        file_url = self.poll_result(task_id)
        if file_url:
            return file_url

        return "PPT 生成失败：生成超时或出错，请稍后重试"


# ── 快捷入口 ─────────────────────────────────────────

def generate_ppt(topic: str, template_id: str = None,
                 use_outline: bool = True) -> str:
    """
    根据主题生成 PPT，返回下载链接。

    参数:
        topic: PPT 主题/标题
        template_id: 模板 ID，不传则用默认教育培训模板
        use_outline: 文多多便携版无需此参数，保留仅用于兼容旧接口

    返回:
        PPT 文件的下载 URL，失败时返回错误描述
    """
    token = settings.DOCMEE_API_KEY
    generator = DocmeePPTGenerator(token)
    return generator.generate(topic, template_id)


def list_ppt_templates(page: int = 1, page_size: int = 20) -> str:
    """
    查询可用 PPT 模板列表，返回格式化文本。
    使用文多多随机模板 API（展示最新模板供参考）。
    """
    token = settings.DOCMEE_API_KEY
    if not token:
        return "查询失败：未配置 DOCMEE_API_KEY"

    try:
        resp = requests.post(
            "https://open.docmee.cn/api/ppt/randomTemplates",
            headers={"Content-Type": "application/json", "token": token},
            json={"pageNum": page, "pageSize": page_size},
            timeout=15,
        )
    except requests.RequestException as e:
        return f"查询失败: {e}"

    if resp.status_code != 200:
        return f"查询失败: HTTP {resp.status_code}"

    result = resp.json()
    if result.get("code") != 0:
        return f"查询失败: {result.get('message', '未知错误')}"

    templates = result.get("data", [])
    if not templates:
        return "暂无可用模板"

    lines = ["可用 PPT 模板（ID → 名称）："]
    for t in templates[:20]:
        tid = t.get("id", "")
        subject = t.get("subject", "未知")
        category = t.get("category", "")
        style = t.get("style", "")
        lines.append(f"  {tid}  {subject} [{category} / {style}]")
    lines.append("")
    lines.append("提示：在 .env 中设置 DOCMEE_TEMPLATE_ID 可更换默认模板")
    return "\n".join(lines)


# ── LangChain Tool（供 Function Calling 绑定）───────

from langchain_core.tools import tool as lc_tool


@lc_tool
def generate_ppt_tool(topic: str, use_outline: bool = True,
                      topic_details: str = "") -> str:
    """
    根据学习主题或知识点自动生成 PPT 课件，返回下载链接。

    适用场景：
    - 学生需要系统性地学习某个知识点时，生成配套 PPT 课件
    - 老师需要备课材料时，快速生成教学 PPT

    参数:
        topic: PPT 的主题或标题，如 "C语言指针详解"
        use_outline: 保留参数，无需关注
        topic_details: 额外内容说明，会融入主题中让生成更精准

    返回:
        PPT 文件的下载链接，失败时返回错误描述
    """
    enriched = f"{topic} - {topic_details}" if topic_details else topic
    return generate_ppt(enriched)


# ── 测试 ─────────────────────────────────────────────

if __name__ == "__main__":
    # 测试：查询模板
    print("=== 查询模板 ===")
    print(list_ppt_templates(page=1, page_size=5))

    # 测试：生成 PPT
    print("\n=== 生成 PPT ===")
    url = generate_ppt("C语言指针与数组的区别与联系")
    print(f"结果: {url}")
