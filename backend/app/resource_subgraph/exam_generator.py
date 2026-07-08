"""
试卷生成器（exam_generator）
职责：RAG 检索题库 + LLM 生成 JSON 格式的试卷（含选择题、填空题、简答题等）。
      支持绑定到学习路径的特定阶段和知识点。
"""
import json
import time
from langchain_core.prompts import ChatPromptTemplate

from app.core.llm import chat_llm
from app.models.resources import Resource
from app.resource_subgraph.state import ResourceSubState

SYSTEM_PROMPT = """你是一个专业的出题老师，擅长针对知识点设计高质量试卷。

## 试卷要求
1. 题型丰富：包含选择题、填空题、简答题（可酌情增加编程题或论述题）
2. 难度分层：约 30% 基础题 + 50% 中等题 + 20% 进阶题
3. 防幻觉：所有题目必须基于公认学科知识，不得编造不存在的概念、技术或数据
4. 覆盖核心：覆盖知识点的核心概念，不考偏题怪题
4. 附参考答案和解析

## 题库参考
{rag_context}

## 输出格式
必须输出纯 JSON，不要包含 markdown 代码块标记或额外说明。
```json
{{
  "title": "试卷标题",
  "knowledge_point": "知识点名称",
  "total_score": 100,
  "questions": [
    {{
      "id": 1,
      "type": "choice",
      "difficulty": "easy",
      "question": "题目内容",
      "options": ["A. 选项1", "B. 选项2", "C. 选项3", "D. 选项4"],
      "user_answer": "",
      "answer": "A",
      "explanation": "解析内容",
      "step_order": 2,
      "knowledge_point": "指针概念"
    }}
  ]
}}
```

注意：
- 每道题都包含 `user_answer` 字段（初始为空字符串），供学生填写答案后使用。
- `answer` 和 `explanation` 在初始展示时对学生隐藏，待学生作答后再展示对照。
- 如果提供了"学习阶段上下文"，每道题必须填写 `step_order` 和 `knowledge_point` 字段。
"""


def exam_generator(state: ResourceSubState) -> dict:
    """
    生成 JSON 格式试卷，可绑定到学习路径的特定阶段和知识点。
    """
    knowledge_point = state.get("knowledge_point", "")
    profile = state.get("profile")
    rewritten = state.get("rewritten_query", "")
    cleaned_topic = state.get("cleaned_topic", "")

    # ── 学习路径上下文 ────────────────────────────────
    path_id = state.get("path_id")
    step_order = state.get("step_order")
    step_kps = state.get("step_knowledge_points", [])

    topic = cleaned_topic or rewritten or knowledge_point
    if not topic:
        print(f"[ExamGenerator]  无知识点，跳过")
        return {"generated_resources": []}

    print(f"\n[ExamGenerator]  开始生成试卷: {topic}")
    if step_order is not None:
        print(f"[ExamGenerator]   绑定路径阶段: step={step_order}, KPs={step_kps}")

    # ── RAG 检索题库 ──
    rag_context = _retrieve_exam_context(topic)
    difficulty = _estimate_difficulty(profile)

    # ── 接收反思重试的反馈 ──────────────────────────────
    error_feedback = state.get("exam_error_feedback", "")
    if error_feedback:
        print(f"[ExamGenerator]  收到反思反馈，重试生成: {error_feedback}")

    # ★ 有聚焦阶段时，以阶段知识点为出题核心（直接取代 topic 参数）
    if step_order is not None and step_kps:
        kp_list = "、".join(step_kps)
        user_prompt = (
            f"请严格围绕以下学习阶段的内容出题：\n"
            f"阶段：第{step_order}阶段 — {topic}\n"
            f"知识点范围：{kp_list}\n"
            f"难度级别：{difficulty}\n"
            f"包含选择题、填空题和简答题。\n"
            f"每道题必须从「{kp_list}」中选择一个作为其 `knowledge_point` 字段，"
            f"且 `step_order` 字段固定为 {step_order}。"
        )
    else:
        user_prompt = (
            f"请为知识点「{topic}」生成一份试卷。\n"
            f"难度级别：{difficulty}\n"
            f"包含选择题、填空题和简答题。"
        )

    # 重试时追加反馈信息
    if error_feedback:
        user_prompt += (
            f"\n\n上次生成存在以下问题，请修正：\n{error_feedback}"
        )

    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        ("user", user_prompt),
    ])

    chain = prompt | chat_llm

    try:
        result = chain.invoke({"rag_context": rag_context})
        content = result.content.strip()

        # 清理可能的 markdown 代码块标记
        if content.startswith("```"):
            content = content.split("\n", 1)[1] if "\n" in content else content
            content = content.rsplit("```", 1)[0].strip()
            if content.startswith("json"):
                content = content[4:].strip()

        # 验证合法 JSON
        json.loads(content)

        # 如果绑定了路径阶段，确保每道题都有 step_order 和 knowledge_point
        if step_order is not None:
            content = _patch_exam_json(content, step_order, step_kps)

        resource = Resource(
            id=f"exam_{int(time.time())}",
            type="exam",
            title=f"{topic} 试卷",
            content=content,
            knowledge_point=knowledge_point or topic,
            difficulty=difficulty,
            path_id=path_id,
            step_order=step_order,
        )
        question_count = content.count('"question"')
        print(f"[ExamGenerator]  试卷生成完成 ({question_count} 道题)")
        return {"generated_resources": [resource]}

    except json.JSONDecodeError as e:
        print(f"[ExamGenerator]  JSON 解析失败: {e}")
        resource = Resource(
            id=f"exam_fallback_{int(time.time())}",
            type="exam",
            title=f"{topic} 试卷（格式异常）",
            content=result.content if 'result' in dir() else "生成失败",
            knowledge_point=knowledge_point or topic,
            difficulty=difficulty,
            path_id=path_id,
            step_order=step_order,
        )
        return {"generated_resources": [resource]}
    except Exception as e:
        print(f"[ExamGenerator]  生成失败: {e}")
        return {"generated_resources": []}


# ── 内部辅助 ────────────────────────────────────────────

def _patch_exam_json(content: str, step_order: int, step_kps: list[str]) -> str:
    """
    确保试卷 JSON 中每道题都包含 step_order 和 knowledge_point 字段。
    """
    try:
        data = json.loads(content)
        questions = data.get("questions", [])
        if not questions:
            return content

        import random
        # 如果没有 step_kps，用 knowledge_point 字段作为备选
        kp_pool = step_kps if step_kps else [data.get("knowledge_point", "未分类")]

        modified = False
        for q in questions:
            if "step_order" not in q:
                q["step_order"] = step_order
                modified = True
            if not q.get("knowledge_point"):
                q["knowledge_point"] = random.choice(kp_pool)
                modified = True

        if modified:
            return json.dumps(data, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[ExamGenerator]  补全题目字段失败: {e}")

    return content


def _retrieve_exam_context(topic: str) -> str:
    """RAG 检索题库参考。"""
    try:
        from app.rag.retriever import search_knowledge, format_rag_results
        results = search_knowledge(topic, k=5)
        if results:
            return format_rag_results(results, max_chars=2000)
    except Exception as e:
        print(f"[ExamGenerator]  RAG 检索异常: {e}")
    return "（暂无题库参考）"


def _estimate_difficulty(profile) -> str:
    """根据知识基础估算试卷难度。"""
    if not profile or not profile.knowledge_base:
        return "medium"
    kb = profile.knowledge_base.lower()
    if any(k in kb for k in ["零基础", "入门", "初级", "较差"]):
        return "easy"
    if any(k in kb for k in ["高级", "深入", "熟练"]):
        return "hard"
    return "medium"
