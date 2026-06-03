"""
资源生成工具集：由 LLM 驱动的内容类资源
每个工具封装一种资源类型的生成逻辑，可供 resource_agent 通过 bind_tools 调用

当前工具：
- generate_document  — Markdown 讲解文档
- generate_exercises — 练习题
"""
from langchain_core.tools import tool
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import SystemMessage, HumanMessage

from app.core.llm import chat_llm


@tool
def generate_document(
    topic: str,
    knowledge_point: str = "",
    student_profile: str = "",
    outline_points: list[str] = [],
    style_hint: str = "标准",
) -> str:
    """
    根据知识点生成 Markdown 格式的系统性讲解文档。
    适用于学生需要完整文字讲解来理解某个知识点时调用。

    Args:
        topic: 文档主题或标题，如 "C语言指针详解"
        knowledge_point: 关联的知识点名称
        student_profile: 学生画像摘要
        outline_points: 大纲要点列表，指定文档应覆盖的各个章节主题
        style_hint: 讲解风格 —— "标准" / "举例为主" / "原理推导" / "对比分析"
    """
    outline_str = ""
    if outline_points:
        outline_str = "\n".join(f"  {i+1}. {p}" for i, p in enumerate(outline_points))
        outline_str = f"\n## 大纲要求\n请按以下大纲组织内容：\n{outline_str}\n"

    prompt = ChatPromptTemplate.from_messages([
        ("system", (
            "你是一个专业的教育内容创作者，擅长将复杂知识讲得清晰易懂。\n"
            "请根据以下信息生成一份完整的 Markdown 格式学习文档。\n\n"
            "## 写作要求\n"
            "1. 结构清晰：有目录、分章节、有小标题\n"
            "2. 内容准确：无事实性错误，重要概念给出准确定义\n"
            "3. 适配风格：{style_hint} 风格下，举例型多给生活案例，推导型展示完整推理过程\n"
            "4. 通俗易懂：适当使用类比和图示（ASCII 示意图或 Mermaid）\n"
            "5. 篇幅适中：覆盖核心内容，不注水\n"
            "{outline_str}"
            "## 学生画像参考\n"
            "{student_profile}\n\n"
            "如果学生画像为空则按通用标准输出。"
        )),
        ("user", "请生成关于「{topic}」的学习文档。知识点：{knowledge_point}"),
    ])

    chain = prompt | chat_llm
    result = chain.invoke({
        "topic": topic,
        "knowledge_point": knowledge_point or topic,
        "style_hint": style_hint,
        "outline_str": outline_str,
        "student_profile": student_profile or "暂无画像数据",
    })
    return result.content


@tool
def generate_exercises(
    topic: str,
    count: int = 5,
    difficulty: str = "medium",
    question_types: str = "选择题,填空题,简答题",
) -> str:
    """
    根据知识点生成练习题，用于检验学生的掌握程度。
    适合在学习文档或 PPT 之后调用，帮助学生巩固理解。

    Args:
        topic: 知识点或主题，如 "C语言指针"
        count: 题目数量
        difficulty: 难度 "easy" / "medium" / "hard"
        question_types: 题目类型，逗号分隔，如 "选择题,填空题,简答题,编程题"
    """
    prompt = ChatPromptTemplate.from_messages([
        ("system", (
            "你是一个专业的出题老师，擅长针对知识点设计高质量练习题。\n\n"
            "## 出题要求\n"
            "1. 覆盖核心概念，不考偏题怪题\n"
            "2. 难度适配：{difficulty}\n"
            "3. 题目类型：{question_types}\n"
            "4. 每种题型 2-4 道，总计约 {count} 道\n"
            "5. 附参考答案或解析\n\n"
            "## 输出格式（Markdown）\n"
            "```\n"
            "### 一、选择题\n"
            "1. ...\n"
            "**答案**：...\n"
            "**解析**：...\n"
            "```\n"
        )),
        ("user", "请为知识点「{topic}」出 {count} 道练习题。"),
    ])

    chain = prompt | chat_llm
    result = chain.invoke({
        "topic": topic,
        "count": count,
        "difficulty": difficulty,
        "question_types": question_types,
    })
    return result.content
