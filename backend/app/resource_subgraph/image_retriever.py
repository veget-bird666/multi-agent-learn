"""
图片检索器（image_retriever）
职责：通过 RAG 从知识库中检索与当前知识点相关的现有图片/图表资源，返回图片链接。
不生成图片，只检索已有资源。
"""
import time
from app.resource_subgraph.state import ResourceSubState
from app.models.resources import Resource


def image_retriever(state: ResourceSubState) -> dict:
    """
    从知识库检索图片资源。
    返回现有图片链接（如系统架构图、流程图、示意图等）。
    """
    knowledge_point = state.get("knowledge_point", "")
    rewritten = state.get("rewritten_query", "")
    cleaned_topic = state.get("cleaned_topic", "")

    topic = cleaned_topic or rewritten or knowledge_point
    if not topic:
        print(f"[ImageRetriever]  无知识点，跳过")
        return {"generated_resources": []}

    print(f"\n[ImageRetriever]   检索图片: {topic}")

    # ── RAG 检索（骨架，后续接入 ChromaDB）──
    image_urls = _retrieve_images(topic)

    resources = []
    for i, url in enumerate(image_urls):
        resources.append(Resource(
            id=f"img_{int(time.time())}_{i}",
            type="image",
            title=url.get("title", f"{topic} 相关图片"),
            content=url.get("url", ""),
            knowledge_point=knowledge_point or topic,
            difficulty="medium",
        ))

    print(f"[ImageRetriever]  检索到 {len(resources)} 张图片")
    return {"generated_resources": resources}


def _retrieve_images(topic: str) -> list[dict]:
    """
    RAG 检索图片资源。
    从 ChromaDB 中检索与 topic 相关的图片记录（预存了图片 URL 和描述）。

    Returns:
        [{"title": "图片标题", "url": "https://..."}, ...]
    """
    # TODO: 接入 ChromaDB
    # 示例实现：
    #   docs = chroma_collection.similarity_search(topic, k=5)
    #   results = []
    #   for doc in docs:
    #       meta = doc.metadata
    #       if meta.get("type") == "image":
    #           results.append({"title": meta.get("title", ""), "url": meta.get("url", "")})
    #   return results
    return []
