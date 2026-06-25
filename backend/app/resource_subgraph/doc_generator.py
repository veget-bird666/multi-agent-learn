"""
文档生成器（doc_generator）
职责：根据知识点 + 学生画像，RAG 检索相关资料后，LLM 生成 Markdown 格式的系统性讲解文档。
"""
import time
from langchain_core.prompts import ChatPromptTemplate

from app.core.llm import chat_llm
from app.models.resources import Resource
from app.resource_subgraph.state import ResourceSubState

SYSTEM_PROMPT = """你是一个专业的教育内容创作者，擅长将复杂知识讲得清晰易懂。

## 写作要求
1. 结构清晰：有目录、分章节、有小标题
2. 内容准确：无事实性错误，重要概念给出准确定义
3. 防幻觉：所有内容必须基于参考资料或公认学科知识，不得编造不存在的概念、数据或引用
4. 适配学生：根据学生的认知风格和知识基础调整讲解方式
   - 举例型：多给生活案例和类比
   - 公式型：展示完整推理过程
   - 实践型：多给代码/操作示例
5. 通俗易懂：适当使用类比和 Mermaid 图表
6. **篇幅控制：回复控制在 1500 字以内**，只覆盖最核心内容，不要展开太多

## 参考资料
{rag_context}

## 学生画像参考
{profile_summary}"""


def doc_generator(state: ResourceSubState) -> dict:
    """
    生成 Markdown 讲解文档。
    """
    knowledge_point = state.get("knowledge_point", "")
    profile = state.get("profile")
    rewritten = state.get("rewritten_query", "")
    cleaned_topic = state.get("cleaned_topic", "")

    topic = cleaned_topic or rewritten or knowledge_point
    if not topic:
        print(f"[DocGenerator]  无知识点，跳过")
        return {"generated_resources": []}

    print(f"\n[DocGenerator]  开始生成文档: {topic}")

    # ── RAG 检索（骨架，后续接入 ChromaDB）──
    rag_context = _retrieve_doc_context(topic)
    profile_summary = _build_profile_summary(profile)

    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        ("user", "请生成关于「{topic}」的系统性学习文档。" if not rewritten
                 else "请根据以下需求生成学习文档：{rewritten}\n\n聚焦知识点：{topic}"),
    ])

    chain = prompt | chat_llm
    try:
        result = chain.invoke({
            "topic": topic,
            "rewritten": rewritten or topic,
            "rag_context": rag_context,
            "profile_summary": profile_summary,
        })

        resource = Resource(
            id=f"doc_{int(time.time())}",
            type="document",
            title=f"{topic} 学习文档",
            content=result.content,
            knowledge_point=knowledge_point or topic,
            difficulty=_estimate_difficulty(profile),
        )
        print(f"[DocGenerator]  文档生成完成 ({len(result.content)} 字)")
        return {"generated_resources": [resource]}

    except Exception as e:
        print(f"[DocGenerator]  生成失败: {e}")
        return {"generated_resources": []}


# ── 内部辅助 ────────────────────────────────────────────

def _retrieve_doc_context(topic: str) -> str:
    """RAG 检索文档参考资料。"""
    # TODO: 接入 ChromaDB，检索与 topic 相关的课程切片
    # 示例：
    #   docs = chroma_collection.similarity_search(topic, k=3)
    #   return "\n\n".join(d.page_content for d in docs)
    return "（暂无参考资料）"


def _build_profile_summary(profile) -> str:
    """构建画像摘要字符串。"""
    if not profile:
        return "暂无画像数据"
    items = []
    for label, val in [
        ("认知风格", profile.cognitive_style),
        ("知识基础", profile.knowledge_base),
        ("兴趣领域", ", ".join(profile.interest_areas[:3]) if profile.interest_areas else None),
    ]:
        if val:
            items.append(f"{label}={val}")
    return "；".join(items) if items else "暂无画像数据"


def _estimate_difficulty(profile) -> str:
    """根据知识基础估算文档难度。"""
    if not profile or not profile.knowledge_base:
        return "medium"
    kb = profile.knowledge_base.lower()
    if any(k in kb for k in ["零基础", "入门", "初级", "较差"]):
        return "easy"
    if any(k in kb for k in ["高级", "深入", "熟练"]):
        return "hard"
    return "medium"
