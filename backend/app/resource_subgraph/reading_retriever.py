"""
扩展阅读检索器（reading_retriever）
职责：从 ChromaDB 资源库中检索与当前知识点相关的扩展阅读材料（PDF/PPT等），
      并根据学生画像生成个性化推荐理由，返回阅读链接。

在资源生成子图中，由 planner 在合适的时机通过 Send() 并行调用。

检索方式：
  1. 通过 ResourceLibrary（ChromaDB 向量索引）做语义匹配
  2. 用 LLM 根据学生画像为每篇材料生成一句"推荐理由"
  3. 按难度匹配度排序，优先推荐适合当前学生水平的材料

数据来源：
  asset-manager 上传的扩展阅读材料（PDF/PPT等）元数据，
  经 ResourceLibrary 自动同步到 ChromaDB。
"""
import time
from langchain_core.prompts import ChatPromptTemplate

from app.resource_subgraph.state import ResourceSubState
from app.models.resources import Resource
from app.rag.resource_library import get_resource_library
from app.core.llm import chat_llm


# ── 推荐理由生成 ───────────────────────────────────────

_RECOMMEND_PROMPT = """你是一个学习规划师，负责为学生的学习材料撰写推荐理由。

## 学生画像
{cognitive_hint}
{knowledge_hint}
{interest_hint}

## 待推荐材料
标题：{title}
简介：{description}
所属学科：{subject}
难度：{difficulty}

## 输出要求
用一句话（20字以内）说明"为什么推荐这篇材料给该学生"，要贴合画像。
示例：
- "你偏实践型，这篇有大量代码示例适合你"
- "你对基础概念还需巩固，这篇讲解详细适合入门"
- "你对算法感兴趣，这篇深入分析了经典算法"
"""


def _generate_recommendation(
    title: str,
    description: str,
    subject: str,
    difficulty: str,
    profile: dict | None,
) -> str:
    """LLM 生成个性化推荐理由。"""
    if not profile:
        return "推荐阅读"

    cognitive_style = profile.get("cognitive_style", "")
    knowledge_base = profile.get("knowledge_base", "")
    interest_areas = profile.get("interest_areas", [])

    cognitive_hint = f"认知风格：{cognitive_style}" if cognitive_style else ""
    knowledge_hint = f"知识基础：{knowledge_base}" if knowledge_base else ""
    interest_hint = (
        f"兴趣领域：{', '.join(interest_areas[:3])}"
        if interest_areas else ""
    )

    try:
        prompt = ChatPromptTemplate.from_messages([("system", _RECOMMEND_PROMPT)])
        chain = prompt | chat_llm
        result = chain.invoke({
            "cognitive_hint": cognitive_hint,
            "knowledge_hint": knowledge_hint,
            "interest_hint": interest_hint,
            "title": title,
            "description": description or "（暂无简介）",
            "subject": subject or "通用",
            "difficulty": difficulty or "medium",
        })
        reason = result.content.strip().strip('"').strip("'")
        if len(reason) > 60:
            reason = reason[:60] + "…"
        return reason
    except Exception as e:
        print(f"[ReadingRetriever]  推荐理由生成失败: {e}")
        return "推荐阅读"


# ── 难度匹配 ──────────────────────────────────────────

_DIFFICULTY_ORDER = {"easy": 1, "medium": 2, "hard": 3}


def _match_score(material_difficulty: str, profile: dict | None) -> int:
    """
    计算材料与学生的匹配度分数。
    分数越高越匹配：材料难度与学生知识基础对齐。
    """
    if not profile:
        return 1

    knowledge_base = (profile.get("knowledge_base") or "").lower()
    # 简化的规则：知识基础弱 → 偏好 easy；基础好 → 偏好 hard
    profile_level = 2  # 默认 medium
    if any(kw in knowledge_base for kw in ["基础", "入门", "薄弱", "零基础"]):
        profile_level = 1
    elif any(kw in knowledge_base for kw in ["进阶", "深入", "熟练", "良好"]):
        profile_level = 3

    material_level = _DIFFICULTY_ORDER.get(material_difficulty, 2)
    return 3 - abs(profile_level - material_level)


# ── 主函数 ────────────────────────────────────────────

def reading_retriever(state: ResourceSubState) -> dict:
    """
    从 ChromaDB 资源库检索扩展阅读材料。

    输入（从子图 state 读取）：
        - cleaned_topic: planner 提取的纯净主题（优先级最高）
        - rewritten_query: rewrite_node 重写后的查询
        - knowledge_point: 原始知识点
        - profile: 学生画像（用于个性化推荐理由）

    输出：
        - generated_resources: 匹配到的扩展阅读 Resource 列表
    """
    knowledge_point = state.get("knowledge_point", "")
    rewritten = state.get("rewritten_query", "")
    cleaned_topic = state.get("cleaned_topic", "")
    profile = state.get("profile")
    profile_dict = profile.model_dump() if profile and hasattr(profile, "model_dump") else (
        profile if isinstance(profile, dict) else None
    )

    # 优先级：cleaned_topic > rewritten_query > knowledge_point
    topic = (cleaned_topic or rewritten or knowledge_point).strip()
    if not topic:
        print(f"[ReadingRetriever]  无知识点/查询词，跳过")
        return {"generated_resources": []}

    print(f"\n[ReadingRetriever]  检索扩展阅读: 「{topic}」")

    # ── 从 ChromaDB 检索 ──
    lib = get_resource_library()
    matches = lib.search(query=topic, k=5, type_filter="extra_reading")

    if not matches:
        print(f"[ReadingRetriever]  未匹配到扩展阅读材料")
        return {"generated_resources": []}

    # ── 难度匹配评分 ──
    for m in matches:
        difficulty = m.get("difficulty", "medium")
        if not difficulty or difficulty not in _DIFFICULTY_ORDER:
            difficulty = "medium"
        m["_match_score"] = _match_score(difficulty, profile_dict)
        m["_difficulty"] = difficulty

    # 按匹配度降序排列
    matches.sort(key=lambda m: m.get("_match_score", 0), reverse=True)

    # ── 组装为 Resource 对象（含推荐理由）──
    resources: list[Resource] = []
    now = int(time.time())

    # 为前 3 篇生成推荐理由（LLM 调用有成本，限制数量）
    for i, m in enumerate(matches[:3]):
        title = m.get("title") or m.get("filename", f"{topic} 相关阅读")
        reading_url = m.get("url", "")
        subject = m.get("subject", "")
        description = m.get("description", "")
        difficulty = m.get("_difficulty", "medium")
        distance = m.get("distance", 0)
        similarity = (1 - distance) * 100

        # 生成个性化推荐理由
        recommendation = _generate_recommendation(
            title=title,
            description=description,
            subject=subject,
            difficulty=difficulty,
            profile=profile_dict,
        )

        # 将推荐理由作为 title 的后缀展示
        display_title = f"{title} — {recommendation}" if recommendation != "推荐阅读" else title
        content = reading_url

        resources.append(Resource(
            id=f"reading_{now}_{i}",
            type="extra_reading",
            title=display_title,
            content=content,
            knowledge_point=knowledge_point or topic,
            difficulty=difficulty,
        ))
        print(f"   [{similarity:.0f}%] {title} → {recommendation}")

    print(f"[ReadingRetriever]  检索完成: {len(resources)} 篇扩展阅读")
    return {"generated_resources": resources}
