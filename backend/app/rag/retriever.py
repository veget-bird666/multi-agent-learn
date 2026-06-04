"""
检索层 — 封装 VectorStore，提供面向 Agent 的高阶检索接口。

用法:
    from app.rag.retriever import search_knowledge, format_rag_results

    results = search_knowledge("C语言指针是什么", k=3)
    context = format_rag_results(results)
    # → 将 context 注入 LLM prompt
"""
from app.rag.vector_store import VectorStore

# 模块级单例，避免每次检索都重建 ChromaDB 客户端
_store: VectorStore | None = None


def _get_store() -> VectorStore:
    global _store
    if _store is None:
        _store = VectorStore()
    return _store


def search_knowledge(
    query: str,
    k: int = 5,
    subject: str | None = None,
) -> list[dict]:
    """
    检索知识库，返回相关文本切片。

    参数:
        query: 用户查询
        k: 返回的切片数量
        subject: 可选的学科过滤（如 "c_programming"、"python"）

    返回:
        [{"text": str, "metadata": dict, "distance": float}, ...]
    """
    store = _get_store()

    if store.count() == 0:
        print("[RAG]  知识库为空，跳过检索")
        return []

    where = {"subject": subject} if subject else None
    results = store.search(query, k=k, where=where)

    print(f"[RAG]  检索 query: {query[:40]}... 命中 {len(results)} 条")
    for r in results:
        src = r["metadata"].get("source", "?")
        sec = r["metadata"].get("section", "")
        print(f"       [{src}] {sec} (距离: {r['distance']:.4f})")

    return results


def format_rag_results(results: list[dict], max_chars: int = 2000) -> str:
    """
    将检索结果组装为可供 LLM prompt 使用的上下文文本。

    参数:
        results: search_knowledge 的返回值
        max_chars: 上下文总字符上限

    返回:
        格式化后的纯文本，空列表返回空字符串
    """
    if not results:
        return ""

    parts = []
    total = 0
    for r in results:
        src = r["metadata"].get("source", "未知来源")
        sec = r["metadata"].get("section", "")
        header = f"[来源: {src}" + (f" / {sec}]" if sec else "]")

        text = r["text"]
        # 截断单个过长切片
        if len(text) > 600:
            text = text[:600] + "..."

        entry = f"{header}\n{text}\n"
        if total + len(entry) > max_chars:
            # 超出上限时部分截断
            remaining = max_chars - total
            if remaining > 100:
                parts.append(entry[:remaining] + "...")
            break

        parts.append(entry)
        total += len(entry)

    return "\n".join(parts)


def count_knowledge() -> int:
    """返回知识库中的切片总数。"""
    return _get_store().count()
