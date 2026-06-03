"""
视频检索器（video_retriever）
职责：通过 RAG 从知识库中检索与当前知识点相关的现有视频资源，返回视频链接。
不生成视频，只检索已有资源。
"""
import time
from app.resource_subgraph.state import ResourceSubState
from app.models.resources import Resource


def video_retriever(state: ResourceSubState) -> dict:
    """
    从知识库检索视频资源。
    返回现有视频链接（如教学视频、操作演示等）。
    """
    knowledge_point = state.get("knowledge_point", "")
    rewritten = state.get("rewritten_query", "")

    topic = rewritten or knowledge_point
    if not topic:
        print(f"[VideoRetriever] ⚠️ 无知识点，跳过")
        return {"generated_resources": []}

    print(f"\n[VideoRetriever] 🎬 检索视频: {topic}")

    # ── RAG 检索（骨架，后续接入 ChromaDB）──
    video_urls = _retrieve_videos(topic)

    resources = []
    for i, url in enumerate(video_urls):
        resources.append(Resource(
            id=f"vid_{int(time.time())}_{i}",
            type="video",
            title=url.get("title", f"{topic} 相关视频"),
            content=url.get("url", ""),
            knowledge_point=knowledge_point or topic,
            difficulty="medium",
        ))

    print(f"[VideoRetriever] ✅ 检索到 {len(resources)} 个视频")
    return {"generated_resources": resources}


def _retrieve_videos(topic: str) -> list[dict]:
    """
    RAG 检索视频资源。
    从 ChromaDB 中检索与 topic 相关的视频记录。

    Returns:
        [{"title": "视频标题", "url": "https://..."}, ...]
    """
    # TODO: 接入 ChromaDB
    return []
