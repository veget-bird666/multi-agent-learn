"""
资源库向量索引 — 基于 ChromaDB 的多模态资源元数据索引。

负责将已上传的资源（视频、图片等）的元数据嵌入到向量空间，
支持按语义搜索匹配的资源。

使用方式：
    from app.rag.resource_library import get_resource_library

    lib = get_resource_library()
    results = lib.search("C语言指针", type_filter="video")

同步策略：
    asset-manager 上传文件到 OSS 的同时写入 resources.json。
    本模块在每次搜索前自动检测 resources.json 是否更新，
    若有变更则增量/全量同步到 ChromaDB，保证索引始终最新。
"""
import json
import os
from pathlib import Path
from typing import Optional

import chromadb
from chromadb.config import Settings

from app.config import settings
from app.rag.embeddings import get_embeddings

# asset-manager 的资源元数据路径
_RESOURCES_JSON = (
    Path(__file__).resolve().parent.parent.parent.parent
    / "asset-manager" / "data" / "resources.json"
)


class ResourceLibrary:
    """
    资源库向量索引。

    将资源的标题、描述、关键词、学科等字段拼合成一段搜索文本，
    嵌入到向量空间，通过余弦相似度进行语义匹配。
    """

    def __init__(self):
        client = chromadb.PersistentClient(
            path=settings.CHROMA_PERSIST_DIR,
            settings=Settings(anonymized_telemetry=False),
        )
        self._embedder = get_embeddings()
        self.collection = client.get_or_create_collection(
            name="resource_library",
            metadata={"hnsw:space": "cosine"},
        )
        # 追踪 resources.json 的最后修改时间，用于增量同步
        self._json_mtime: float = 0.0

    # ── 写入 ─────────────────────────────────────────────

    def add_resource(self, resource: dict, rid: str = "") -> str:
        """添加或更新一条资源记录到索引。"""
        rid = rid or resource.get("id") or ""

        # 构建可搜索文本
        text_parts = [
            resource.get("title", ""),
            resource.get("description", ""),
            resource.get("subject", ""),
            " ".join(str(k) for k in (resource.get("keywords", []) or [])),
        ]
        search_text = " ".join(t for t in text_parts if t).strip()
        if not search_text:
            search_text = resource.get("filename", resource.get("oss_key", ""))

        embedding = self._embedder.embed_documents([search_text])[0]

        # ChromaDB metadata 必须是 flat dict（不能嵌套 list）
        metadata = {
            "type": resource.get("resource_type", "other"),
            "title": resource.get("title", "") or "",
            "url": resource.get("url", "") or "",
            "subject": resource.get("subject", "") or "",
            "description": resource.get("description", "") or "",
            "filename": resource.get("filename", "") or "",
            "oss_key": resource.get("oss_key", "") or "",
            "difficulty": resource.get("difficulty", "") or "",
            "keywords": ",".join(
                str(k) for k in (resource.get("keywords", []) or [])
            ),
        }

        # upsert（重复 rid 会覆盖）
        self.collection.upsert(
            ids=[rid],
            documents=[search_text],
            embeddings=[embedding],
            metadatas=[metadata],
        )
        return rid

    # ── 检索 ─────────────────────────────────────────────

    def search(
        self,
        query: str,
        k: int = 5,
        type_filter: Optional[str] = None,
    ) -> list[dict]:
        """
        向量语义搜索，返回匹配的资源。

        搜索前自动检查 resources.json 是否有更新，保证索引最新。

        参数:
            query: 搜索词（如 "C语言指针"）
            k: 返回条数
            type_filter: 可选资源类型过滤（如 "video"、"image"）

        返回:
            [{"id", "title", "url", "description", "subject",
              "filename", "oss_key", "resource_type", "keywords", "distance"}, ...]
        """
        # 每次搜索前检查 resources.json 是否更新
        self._sync_if_needed()

        if self.collection.count() == 0:
            return []

        query_embedding = self._embedder.embed_query(query)

        where = {"type": type_filter} if type_filter else None

        raw = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=k,
            include=["documents", "metadatas", "distances"],
            where=where,
        )

        results = []
        if raw["metadatas"] and raw["metadatas"][0]:
            ids_list = raw["ids"][0] if raw["ids"] else []
            for i, meta in enumerate(raw["metadatas"][0]):
                kw_str = meta.get("keywords", "") or ""
                keywords = kw_str.split(",") if kw_str else []
                rid = ids_list[i] if i < len(ids_list) else ""

                results.append({
                    "id": rid,
                    "title": meta.get("title", ""),
                    "url": meta.get("url", ""),
                    "description": meta.get("description", ""),
                    "subject": meta.get("subject", ""),
                    "filename": meta.get("filename", ""),
                    "oss_key": meta.get("oss_key", ""),
                    "resource_type": meta.get("type", ""),
                    "difficulty": meta.get("difficulty", ""),
                    "keywords": keywords,
                    "distance": raw["distances"][0][i] if raw["distances"] else 0.0,
                })
        return results

    # ── 管理 ─────────────────────────────────────────────

    def delete(self, rid: str) -> bool:
        """按 ID 从索引中删除。"""
        try:
            self.collection.delete(ids=[rid])
            return True
        except Exception:
            return False

    def delete_by_key(self, oss_key: str) -> int:
        """按 OSS 路径删除（遍历匹配）。"""
        all_data = self.collection.get()
        to_remove = []
        for i, meta in enumerate(all_data.get("metadatas", []) or []):
            if meta and meta.get("oss_key") == oss_key:
                rid = all_data["ids"][i] if all_data["ids"] and i < len(all_data["ids"]) else ""
                if rid:
                    to_remove.append(rid)
        for rid in to_remove:
            self.delete(rid)
        return len(to_remove)

    def count(self) -> int:
        return self.collection.count()

    def clear(self):
        """清空索引。"""
        all_ids = self.collection.get()["ids"]
        if all_ids:
            self.collection.delete(ids=all_ids)

    def force_sync(self):
        """强制全量同步（忽略 mtime 检查）。"""
        self._json_mtime = 0.0
        self._sync_if_needed(force=True)

    def _sync_if_needed(self, force: bool = False):
        """
        检测 resources.json 是否更新，有变更则增量/全量同步。

        策略：
        - 首次同步（_json_mtime == 0）：全量写入
        - 后续检测到 mtime 变化：清空后全量重写（简单可靠）
        """
        if not _RESOURCES_JSON.exists():
            return

        current_mtime = _RESOURCES_JSON.stat().st_mtime

        # 没有变更且不是强制同步，跳过
        if not force and self._json_mtime > 0 and current_mtime <= self._json_mtime:
            return

        try:
            with open(_RESOURCES_JSON, "r", encoding="utf-8") as f:
                all_resources = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError) as e:
            print(f"[ResourceLibrary]  读取 resources.json 失败: {e}")
            return

        print(f"[ResourceLibrary]  检测到 resources.json 变更，同步 {len(all_resources)} 条资源到 ChromaDB")

        # 全量重写：清空索引后重新写入
        # 简单可靠，适合数据量不大的场景
        self.clear()
        count = 0
        for r in all_resources:
            try:
                rid = r.get("id", "")
                self.add_resource(r, rid=rid)
                count += 1
            except Exception as e:
                print(f"[ResourceLibrary]  同步单条失败: {e}")

        self._json_mtime = current_mtime
        print(f"[ResourceLibrary]  同步完成: {count} 条")


# 模块级单例
_lib: Optional[ResourceLibrary] = None


def get_resource_library() -> ResourceLibrary:
    """获取 ResourceLibrary 单例。"""
    global _lib
    if _lib is None:
        _lib = ResourceLibrary()
    return _lib
