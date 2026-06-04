"""
知识库构建脚本 — 读取 knowledge_base/ 下的知识文件，切片后写入 ChromaDB。

用法:
    cd backend
    python -m scripts.build_knowledge_base

效果:
    遍历 app/knowledge_base/ 下所有 .md 文件，按 Markdown 标题切片，
    经 MaaS Embedding 模型向量化后，存入 ChromaDB（chroma_data/）。
    脚本幂等——每次执行会先清空已有数据再重建。
"""
import os
import sys

# 将项目根目录（backend/）加入 sys.path，确保可以 import app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.rag.vector_store import VectorStore
from app.rag.chunking import auto_chunk


# 知识库文件根目录
KNOWLEDGE_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..", "app", "knowledge_base",
)


def discover_files(root: str) -> list[dict]:
    """
    扫描知识库目录，返回文件列表。

    返回:
        [{"path": str, "subject": str, "rel_path": str}, ...]
    """
    files = []
    if not os.path.isdir(root):
        print(f"[Build]  知识库目录不存在: {root}")
        return files

    for dirpath, _, filenames in os.walk(root):
        for fname in filenames:
            if not fname.endswith(".md"):
                continue
            full_path = os.path.join(dirpath, fname)
            rel_path = os.path.relpath(full_path, root)
            subject = os.path.basename(os.path.dirname(full_path))
            files.append({
                "path": full_path,
                "subject": subject,
                "rel_path": rel_path,
            })

    files.sort(key=lambda x: x["path"])
    return files


def main():
    print("=" * 50)
    print("  知识库构建脚本")
    print("=" * 50)

    # 1. 扫描文件
    files = discover_files(KNOWLEDGE_DIR)
    if not files:
        print(f"\n[Build]  在 {KNOWLEDGE_DIR} 下未找到 .md 文件")
        print("[Build]  请先在 knowledge_base/ 中添加知识文件")
        return

    print(f"\n[Build]  发现 {len(files)} 个文件：")
    for f in files:
        print(f"         {f['subject']:20s}  {f['rel_path']}")

    # 2. 读取 + 切片
    all_chunks = []
    for f in files:
        with open(f["path"], "r", encoding="utf-8") as fh:
            text = fh.read()

        metadata = {"subject": f["subject"]}
        chunks = auto_chunk(
            text,
            source=f["rel_path"],
            metadata=metadata,
            chunk_size=500,
            overlap=50,
        )
        print(f"         {f['rel_path']:30s} → {len(chunks)} 个切片")
        all_chunks.extend(chunks)

    print(f"\n[Build]  共 {len(all_chunks)} 个切片，开始写入 ChromaDB...")

    # 3. 写入向量库
    store = VectorStore()
    old_count = store.count()

    # 幂等：先清空再写入
    if old_count > 0:
        print(f"[Build]  清空已有数据 ({old_count} 条)...")
        store.clear()

    added = store.add_chunks(all_chunks)
    new_count = store.count()

    print(f"[Build]  完成！已写入 {added} 个切片，当前库共 {new_count} 条")
    print("=" * 50)


if __name__ == "__main__":
    main()
