"""
文本切片模块 — 将原始知识库文件切分为适于向量检索的文本块。

提供两种策略：
- chunk_markdown: 按 Markdown 标题层级切片（推荐）
- chunk_text: 纯文本按字数切片（兜底）
"""
import re
from typing import Optional


def chunk_markdown(
    text: str,
    source: str = "",
    metadata: Optional[dict] = None,
    chunk_size: int = 500,
    overlap: int = 50,
) -> list[dict]:
    """
    按 Markdown 标题（## 或 ###）分割文本，每个标题下内容为一个独立块。

    参数:
        text: Markdown 原文
        source: 来源文件名
        metadata: 附加元数据（如 subject、difficulty 等）
        chunk_size: 块目标字符数
        overlap: 块间重叠字符数

    返回:
        [{"text": str, "metadata": {...}}, ...]
    """
    metadata = metadata or {}
    base_meta = {"source": source, **metadata}

    # 按标题行分割（支持 ## 和 ###）
    sections = re.split(r"(?=^#{2,3}\s)", text, flags=re.MULTILINE)
    sections = [s.strip() for s in sections if s.strip()]

    chunks = []
    for sec in sections:
        lines = sec.split("\n")
        heading = lines[0] if lines else ""

        # 提取标题文字作为章节标识
        section_title = re.sub(r"^#+\s*", "", heading).strip()

        # 将标题下的内容按 chunk_size 进一步切分（长章节）
        content = "\n".join(lines[1:]).strip() if len(lines) > 1 else ""
        if not content:
            # 只有标题没有正文时，把标题本身作为一个块
            chunks.append({
                "text": heading,
                "metadata": {**base_meta, "section": section_title},
            })
            continue

        # 如果内容短，直接作为一个块
        if len(content) <= chunk_size:
            chunks.append({
                "text": f"{heading}\n{content}",
                "metadata": {**base_meta, "section": section_title},
            })
            continue

        # 长内容：按段落进一步拆分
        paragraphs = re.split(r"\n\s*\n", content)
        current = ""
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            if len(current) + len(para) <= chunk_size:
                current += "\n\n" + para if current else para
            else:
                if current:
                    chunks.append({
                        "text": f"{heading}\n{current}",
                        "metadata": {**base_meta, "section": section_title},
                    })
                current = para

        if current:
            chunks.append({
                "text": f"{heading}\n{current}",
                "metadata": {**base_meta, "section": section_title},
            })

    # 重叠后处理：相邻块拼接 overlap 字符
    if overlap > 0 and len(chunks) > 1:
        for i in range(len(chunks) - 1):
            tail = chunks[i]["text"][-overlap:]
            if tail:
                chunks[i + 1]["text"] = tail + "\n" + chunks[i + 1]["text"]

    return chunks


def chunk_text(
    text: str,
    source: str = "",
    metadata: Optional[dict] = None,
    chunk_size: int = 500,
    overlap: int = 50,
) -> list[dict]:
    """
    纯文本按固定长度切片（兜底策略）。

    参数:
        text: 原始文本
        source: 来源文件名
        metadata: 附加元数据
        chunk_size: 目标字符数
        overlap: 重叠字符数

    返回:
        [{"text": str, "metadata": {...}}, ...]
    """
    metadata = metadata or {}
    base_meta = {"source": source, **metadata}

    chunks = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunk_text_content = text[start:end]
        chunks.append({
            "text": chunk_text_content,
            "metadata": {**base_meta, "char_start": start, "char_end": end},
        })
        start += chunk_size - overlap

    return chunks


def auto_chunk(
    text: str,
    source: str = "",
    metadata: Optional[dict] = None,
    chunk_size: int = 500,
    overlap: int = 50,
) -> list[dict]:
    """
    自动检测文本类型，选择合适切片策略。
    - 包含 Markdown 标题 → chunk_markdown
    - 纯文本 → chunk_text
    """
    if re.search(r"(?m)^#{2,3}\s", text):
        return chunk_markdown(text, source, metadata, chunk_size, overlap)
    return chunk_text(text, source, metadata, chunk_size, overlap)
