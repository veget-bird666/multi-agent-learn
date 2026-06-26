"""
视频检索器（video_retriever）
职责：从 ChromaDB 资源库中检索与当前知识点相关的现有视频资源，返回视频链接。
不生成视频，只检索已有的 OSS 视频。

在资源生成子图中，由 planner 在合适的时机（用户需求涉及视频时）通过 Send() 并行调用。

检索方式：
  通过 ResourceLibrary（ChromaDB 向量索引）做语义匹配，
  索引数据由 asset-manager 上传时自动同步，或首次使用时从 JSON 自动加载。
"""
import time

from app.resource_subgraph.state import ResourceSubState
from app.models.resources import Resource
from app.rag.resource_library import get_resource_library


def video_retriever(state: ResourceSubState) -> dict:
    """
    从 ChromaDB 资源库检索视频资源。

    输入（从子图 state 读取）：
        - cleaned_topic: planner 提取的纯净主题（优先级最高）
        - rewritten_query: rewrite_node 重写后的查询
        - knowledge_point: 原始知识点

    输出：
        - generated_resources: 匹配到的视频 Resource 列表
    """
    knowledge_point = state.get("knowledge_point", "")
    rewritten = state.get("rewritten_query", "")
    cleaned_topic = state.get("cleaned_topic", "")

    # 优先级：cleaned_topic > rewritten_query > knowledge_point
    topic = (cleaned_topic or rewritten or knowledge_point).strip()
    if not topic:
        print(f"[VideoRetriever]  无知识点/查询词，跳过")
        return {"generated_resources": []}

    print(f"\n[VideoRetriever]  检索视频: 「{topic}」")

    # ── 从 ChromaDB 检索 ──
    lib = get_resource_library()
    matches = lib.search(query=topic, k=5, type_filter="video")

    if not matches:
        print(f"[VideoRetriever]  未匹配到相关视频")
        return {"generated_resources": []}

    # ── 组装为 Resource 对象 ──
    resources: list[Resource] = []
    now = int(time.time())
    for i, m in enumerate(matches):
        title = m.get("title") or m.get("filename", f"{topic} 相关视频")
        video_url = m.get("url", "")
        subject = m.get("subject", "")
        distance = m.get("distance", 0)
        similarity = (1 - distance) * 100  # 余弦距离转相似度百分比

        resources.append(Resource(
            id=f"video_{now}_{i}",
            type="video",
            title=title,
            content=video_url,
            knowledge_point=knowledge_point or topic,
            difficulty="medium",
        ))
        print(f"   [{similarity:.0f}%] {title} | {subject} | {video_url[:60]}...")

    print(f"[VideoRetriever]  检索完成: {len(resources)} 个相关视频")
    return {"generated_resources": resources}
