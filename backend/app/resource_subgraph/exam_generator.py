"""
试卷生成器（exam_generator）
职责：RAG 检索题库 + LLM 生成 JSON 格式的试卷（含选择题、填空题、简答题等）。
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
3. 覆盖核心：覆盖知识点的核心概念，不考偏题怪题
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
      "answer": "A",
      "explanation": "解析内容"
    }},
    {{
      "id": 2,
      "type": "fill",
      "difficulty": "medium",
      "question": "填空题目（__为填空位置）",
      "answer": "正确答案",
      "explanation": "解析内容"
    }},
    {{
      "id": 3,
      "type": "short_answer",
      "difficulty": "hard",
      "question": "简答题内容",
      "answer": "参考答案要点",
      "explanation": "评分要点"
    }}
  ]
}}
```"""


def exam_generator(state: ResourceSubState) -> dict:
    """
    生成 JSON 格式试卷。
    """
    knowledge_point = state.get("knowledge_point", "")
    profile = state.get("profile")
    rewritten = state.get("rewritten_query", "")
    cleaned_topic = state.get("cleaned_topic", "")

    topic = cleaned_topic or rewritten or knowledge_point
    if not topic:
        print(f"[ExamGenerator]  无知识点，跳过")
        return {"generated_resources": []}

    print(f"\n[ExamGenerator]  开始生成试卷: {topic}")

    # ── RAG 检索题库（骨架）──
    rag_context = _retrieve_exam_context(topic)
    difficulty = _estimate_difficulty(profile)

    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        ("user", (
            f"请为知识点「{topic}」生成一份试卷。\n"
            f"难度级别：{difficulty}\n"
            f"包含选择题、填空题和简答题。"
        )),
    ])

    chain = prompt | chat_llm

    try:
        result = chain.invoke({})
        content = result.content.strip()

        # 尝试清理：去掉可能的 markdown 代码块标记
        if content.startswith("```"):
            # 找到第一个换行后的内容和最后一个 ```
            content = content.split("\n", 1)[1] if "\n" in content else content
            content = content.rsplit("```", 1)[0].strip()
            # 去掉开头的 json 标记
            if content.startswith("json"):
                content = content[4:].strip()

        # 验证是合法 JSON
        json.loads(content)

        resource = Resource(
            id=f"exam_{int(time.time())}",
            type="exam",
            title=f"{topic} 试卷",
            content=content,
            knowledge_point=knowledge_point or topic,
            difficulty=difficulty,
        )
        question_count = content.count('"question"')
        print(f"[ExamGenerator]  试卷生成完成 ({question_count} 道题)")
        return {"generated_resources": [resource]}

    except json.JSONDecodeError as e:
        print(f"[ExamGenerator]  JSON 解析失败: {e}")
        # 兜底：把结果当作内容，标记为 document 类型
        resource = Resource(
            id=f"exam_fallback_{int(time.time())}",
            type="exam",
            title=f"{topic} 试卷（格式异常）",
            content=result.content if 'result' in dir() else "生成失败",
            knowledge_point=knowledge_point or topic,
            difficulty=difficulty,
        )
        return {"generated_resources": [resource]}
    except Exception as e:
        print(f"[ExamGenerator]  生成失败: {e}")
        return {"generated_resources": []}


# ── 内部辅助 ────────────────────────────────────────────

def _retrieve_exam_context(topic: str) -> str:
    """RAG 检索题库。"""
    # TODO: 接入 ChromaDB，检索与 topic 相关的题目作为参考
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
