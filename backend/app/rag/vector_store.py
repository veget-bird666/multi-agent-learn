"""
ChromaDB 向量存储封装 — 提供统一的增删查接口。

用法:
    store = VectorStore()
    store.search("C语言指针", k=3)
    store.add_chunks([{"text": "...", "metadata": {...}}, ...])
    store.count()
"""
from typing import Optional
import uuid

import chromadb
from chromadb.config import Settings

from app.config import settings
from app.rag.embeddings import get_embeddings


class VectorStore:
    """ChromaDB 封装，自动使用 MaaS Embedding 模型。"""

    def __init__(self, collection_name: str = "knowledge_base"):
        client = chromadb.PersistentClient(
            path=settings.CHROMA_PERSIST_DIR,
            settings=Settings(anonymized_telemetry=False),
        )
        self._embedder = get_embeddings()
        self.collection = client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )
        self._collection_name = collection_name

    # ── 写入 ─────────────────────────────────────────────

    def add_chunks(self, chunks: list[dict]) -> int:
        """
        批量添加文本切片。

        参数:
            chunks: [{"text": str, "metadata": dict}, ...]

        返回:
            成功添加的切片数量
        """
        if not chunks:
            return 0

        texts = [c["text"] for c in chunks]
        metadatas = [c.get("metadata") or {} for c in chunks]
        ids = [str(uuid.uuid4()) for _ in chunks]

        # 嵌入文本（批量，一次调用）
        embeddings = self._embedder.embed_documents(texts)

        self.collection.add(
            ids=ids,
            documents=texts,
            embeddings=embeddings,
            metadatas=metadatas,
        )
        return len(chunks)

    # ── 检索 ─────────────────────────────────────────────

    def search(
        self,
        query: str,
        k: int = 5,
        where: Optional[dict] = None,
    ) -> list[dict]:
        """
        向量检索，返回匹配的文本切片。

        参数:
            query: 用户查询（自动转 embedding）
            k: 返回条数
            where: 过滤条件，如 {"subject": "c_programming"}

        返回:
            [{"text": str, "metadata": dict, "distance": float}, ...]
        """
        query_embedding = self._embedder.embed_query(query)

        kwargs = {
            "query_embeddings": [query_embedding],
            "n_results": k,
            "include": ["documents", "metadatas", "distances"],
        }
        if where:
            kwargs["where"] = where

        raw = self.collection.query(**kwargs)

        results = []
        if raw["documents"] and raw["documents"][0]:
            for i, doc in enumerate(raw["documents"][0]):
                results.append({
                    "text": doc,
                    "metadata": raw["metadatas"][0][i] if raw["metadatas"] else {},
                    "distance": raw["distances"][0][i] if raw["distances"] else 0.0,
                })
        return results

    # ── 管理 ─────────────────────────────────────────────

    def count(self) -> int:
        """返回集合中的文档数量。"""
        return self.collection.count()

    def clear(self) -> None:
        """清空集合中所有数据。"""
        all_ids = self.collection.get()["ids"]
        if all_ids:
            self.collection.delete(ids=all_ids)

    def delete_collection(self) -> None:
        """删除整个集合。"""
        client = chromadb.PersistentClient(
            path=settings.CHROMA_PERSIST_DIR,
            settings=Settings(anonymized_telemetry=False),
        )
        client.delete_collection(self._collection_name)
