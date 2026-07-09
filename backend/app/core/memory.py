"""
教学经验记忆库 — 基于 ChromaDB 的向量检索

当学生表示"理解了"时，chat_agent 整理当前教学对话存入此库。
后续类似提问可检索到历史成功教学经验作为参考，帮助 Agent
复用以往有效的讲解策略。

用法:
    from app.core.memory import teaching_memory

    # 存入一条教学经验
    teaching_memory.save(
        question="指针到底是什么？",
        answer="指针就是存储内存地址的变量...",
        teaching_approach="用门牌号类比内存地址",
        focus_points="强调变量本质区别",
        knowledge_point="指针概念",
    )

    # 检索相关经验
    results = teaching_memory.search("指针和数组的区别", k=3)
"""
import uuid
from typing import Optional

import chromadb
from chromadb.config import Settings

from app.config import settings
from app.rag.embeddings import get_embeddings


class TeachingMemory:
    """教学经验记忆库 — 存入和检索成功教学案例。"""

    COLLECTION_NAME = "successful_teachings"

    def __init__(self):
        client = chromadb.PersistentClient(
            path=settings.CHROMA_PERSIST_DIR,
            settings=Settings(anonymized_telemetry=False),
        )
        self._embedder = get_embeddings()
        self.collection = client.get_or_create_collection(
            name=self.COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )

    # ── 写入 ─────────────────────────────────────────────

    def save(
        self,
        question: str,
        answer: str,
        teaching_approach: str = "",
        focus_points: str = "",
        knowledge_point: str = "",
    ) -> str:
        """
        存入一条成功教学经验。

        参数:
            question:  学生提出的问题（触发教学的原始问题）
            answer:    有效的教学回答
            teaching_approach: 教学策略描述（如"用门牌号类比内存地址"）
            focus_points:      讲解侧重点（如"指针的变量属性、数组的常量属性"）
            knowledge_point:   关联知识点（如"指针与数组区别"）

        返回:
            存入记录的 UUID
        """
        doc_parts = [f"学生问题：{question}", f"有效回答：{answer}"]
        if teaching_approach:
            doc_parts.append(f"教学策略：{teaching_approach}")
        doc = "\n".join(doc_parts)

        _id = str(uuid.uuid4())
        embedding = self._embedder.embed_query(doc)

        self.collection.add(
            ids=[_id],
            documents=[doc],
            embeddings=[embedding],
            metadatas=[{
                "knowledge_point": knowledge_point or "",
                "teaching_approach": teaching_approach or "",
                "focus_points": focus_points or "",
                "success_count": 1,
            }],
        )
        kp_tag = f" [{knowledge_point}]" if knowledge_point else ""
        print(f"[TeachingMemory]  存入教学经验{kp_tag} (ID={_id[:8]}...)")
        return _id

    # ── 检索 ─────────────────────────────────────────────

    def search(
        self,
        query: str,
        k: int = 3,
        where: Optional[dict] = None,
    ) -> list[dict]:
        """
        检索与当前问题相关的历史教学经验。

        参数:
            query:  当前学生问题
            k:      返回条数
            where:  过滤条件（如 {"knowledge_point": "指针概念"}）

        返回:
            [{
                "question": str,
                "answer": str,
                "teaching_approach": str,
                "focus_points": str,
                "knowledge_point": str,
                "distance": float,       # 余弦距离，越小越相似
            }, ...]
        """
        q_emb = self._embedder.embed_query(query)
        kwargs = {
            "query_embeddings": [q_emb],
            "n_results": k,
            "include": ["documents", "metadatas", "distances"],
        }
        if where:
            kwargs["where"] = where

        raw = self.collection.query(**kwargs)
        results = []
        if raw["documents"] and raw["documents"][0]:
            for i, doc in enumerate(raw["documents"][0]):
                meta = raw["metadatas"][0][i] if raw["metadatas"] else {}
                results.append(self._parse_result(doc, meta, raw["distances"][0][i] if raw["distances"] else 0.0))
        return results

    # ── 管理 ─────────────────────────────────────────────

    def count(self) -> int:
        """返回集合中的教学经验总数。"""
        return self.collection.count()

    # ── 内部方法 ─────────────────────────────────────────

    @staticmethod
    def _parse_result(doc: str, meta: dict, distance: float) -> dict:
        """解析 ChromaDB 返回的文档和元数据为结构化结果。"""
        question, answer = "", ""
        if "学生问题：" in doc:
            question = doc.split("学生问题：")[1].split("\n")[0]
        if "有效回答：" in doc:
            answer = doc.split("有效回答：")[1].split("\n")[0]

        return {
            "question": question,
            "answer": answer,
            "teaching_approach": meta.get("teaching_approach", ""),
            "focus_points": meta.get("focus_points", ""),
            "knowledge_point": meta.get("knowledge_point", ""),
            "distance": distance,
        }


# 全局单例
teaching_memory = TeachingMemory()
