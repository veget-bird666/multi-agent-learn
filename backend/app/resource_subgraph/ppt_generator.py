"""
PPT 生成器（ppt_generator）
职责：封装现有的 ppt_tool，作为子图中的一个独立节点。
      生成后将 PPT 文件下载到本地，通过静态文件服务提供给前端。
"""
import time
import requests
from pathlib import Path

from app.resource_subgraph.state import ResourceSubState
from app.models.resources import Resource
from app.tools.ppt_tool import generate_ppt

# PPT 本地存储目录
PPT_OUTPUT_DIR = Path(__file__).resolve().parents[2] / "generated" / "ppt"


def ppt_generator(state: ResourceSubState) -> dict:
    """
    根据知识点生成 PPT 课件。
    内部调用讯飞 PPT API（通过 ppt_tool.generate_ppt），获得下载链接后
    下载到本地 generated/ppt/ 目录，返回本地 URL。
    """
    knowledge_point = state.get("knowledge_point", "")
    rewritten = state.get("rewritten_query", "")
    cleaned_topic = state.get("cleaned_topic", "")

    topic = cleaned_topic or rewritten or knowledge_point
    if not topic:
        print(f"[PPTGenerator]  无知识点，跳过")
        return {"generated_resources": []}

    print(f"\n[PPTGenerator]  开始生成 PPT: {topic}")

    try:
        # 调用现有的 PPT 生成工具，获得讯飞下载链接
        download_url = generate_ppt(topic, use_outline=True)

        if not download_url or "失败" in download_url:
            print(f"[PPTGenerator]  PPT 生成未成功: {download_url}")
            return {"generated_resources": []}

        # 下载 PPT 文件到本地
        local_url = _download_ppt(download_url, topic)

        resource = Resource(
            id=f"ppt_{int(time.time())}",
            type="ppt",
            title=f"{topic} 课件",
            content=local_url,  # 本地可访问 URL
            knowledge_point=knowledge_point or topic,
            difficulty="medium",
        )
        print(f"[PPTGenerator]  PPT 生成完成: {local_url}")
        return {"generated_resources": [resource]}

    except Exception as e:
        print(f"[PPTGenerator]  生成失败: {e}")
        return {"generated_resources": []}


def _download_ppt(url: str, topic: str) -> str:
    """
    从讯飞下载链接下载 PPT 文件到本地。

    返回:
        本地可访问的 URL 路径（如 /api/static/ppt/xxx.pptx）
    """
    PPT_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # 生成文件名：主题_时间戳.pptx
    safe_topic = "".join(c for c in topic if c.isalnum() or c in " _-")
    filename = f"{safe_topic}_{int(time.time())}.pptx"
    filepath = PPT_OUTPUT_DIR / filename

    print(f"[PPTGenerator]  下载 PPT 到本地: {filename}")
    try:
        resp = requests.get(url, timeout=120, stream=True)
        resp.raise_for_status()
        with open(filepath, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                f.write(chunk)

        file_size = filepath.stat().st_size
        print(f"[PPTGenerator]  下载完成: {file_size / 1024:.1f} KB")
        return f"/static/ppt/{filename}"

    except Exception as e:
        print(f"[PPTGenerator]  下载失败，回退到讯飞原链接: {e}")
        # 下载失败时回退到原文链接
        return url
