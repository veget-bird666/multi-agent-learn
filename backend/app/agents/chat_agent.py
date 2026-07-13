"""
智能体：聊天智能体
职责：与学生进行对话（含内容安全过滤 + 教学经验记忆）
"""
from typing import Optional
from app.core.llm import chat_llm
from app.core.content_safety import content_safety_checker
from app.core.memory import teaching_memory
from app.rag.retriever import search_knowledge, format_rag_results

from app.graph.state import LearningState
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage


# ═══════════════════════════════════════════════════════════
#  教学经验记忆 — 理解信号检测
# ═══════════════════════════════════════════════════════════

_UNDERSTAND_KEYWORDS = [
    "懂了", "理解了", "明白了", "原来如此",
    "get到了", "说得很明白", "讲得清楚",
    "终于理解了", "这下清楚了", "恍然大悟",
    "我懂了", "我理解了", "我明白了",
    "讲得很清楚", "说明白了",
]


def _is_understanding_signal(text: str) -> bool:
    """快速检测用户是否表达了对某个知识点的理解。"""
    text = text.strip()
    if not text or len(text) > 60:
        return False
    for kw in _UNDERSTAND_KEYWORDS:
        if kw in text:
            return True
    return False


def _extract_last_qa(history: list) -> Optional[dict]:
    """
    从 history 提取最后一个完整的 Q&A 对（排除理解信号本身）。

    例如 history = [H("指针是什么"), A("指针是地址..."), H("还是不懂"), A("打个比方..."), H("哦我懂了")]
    → 返回 {"question": "还是不懂", "answer": "打个比方..."}
    而非返回开头的 "指针是什么" 轮次，因为最后一次教学对话最可能是学生理解的关键。
    """
    n = len(history)
    if n < 2:
        return None

    # 从末尾向前跳过理解信号消息
    i = n - 1
    while i >= 0:
        msg = history[i]
        if hasattr(msg, 'type') and msg.type == 'human' and _is_understanding_signal(getattr(msg, 'content', '')):
            i -= 1
        else:
            break

    # 从 i 位置继续向前找最后一组 Q&A
    for j in range(i, -1, -1):
        msg = history[j]
        if hasattr(msg, 'type') and msg.type == 'human':
            if j + 1 < n and hasattr(history[j + 1], 'type') and history[j + 1].type == 'ai':
                return {
                    "question": msg.content,
                    "answer": history[j + 1].content,
                }
            break

    return None


def _summarize_teaching(question: str, answer: str) -> dict:
    """用 LLM 总结教学策略和侧重点。"""
    from langchain_core.prompts import ChatPromptTemplate

    prompt = ChatPromptTemplate.from_messages([
        ("system", (
            "你是一个教学分析师。分析下面的教学对话，提取三项信息，直接返回 JSON：\n"
            '{"knowledge_point": "涉及的知识点名称，如指针概念", '
            '"teaching_approach": "使用了什么教学策略/方法，如用生活类比", '
            '"focus_points": "讲解侧重点是什么，如强调变量本质区别"}'
        )),
        ("user", "学生问题：{question}\n\n教师回答：{answer}"),
    ])

    try:
        chain = prompt | chat_llm
        response = chain.invoke({"question": question, "answer": answer})
        import json
        # 清理 markdown 代码块包裹
        text = response.content.strip().strip("```json").strip("```").strip()
        result = json.loads(text)
        return {
            "knowledge_point": (result.get("knowledge_point") or "").strip(),
            "teaching_approach": (result.get("teaching_approach") or "").strip(),
            "focus_points": (result.get("focus_points") or "").strip(),
        }
    except Exception as e:
        print(f"[ChatAgent]  LLM 教学总结失败: {e}")
        return {"knowledge_point": "", "teaching_approach": "", "focus_points": ""}


# ═══════════════════════════════════════════════════════════
#  主 prompt
# ═══════════════════════════════════════════════════════════

CHAT_PROMPT = """
你是一个Agent学习系统中专门负责对话的智能体（Chat Agent），负责与学生进行对话，更新对话历史。

## 你需要注意的信息
对话历史中可能包含以下系统消息，你需要据此回复：
- **画像更新记录**：格式为"系统：已更新学生画像..." — 据此了解学生当前画像状态
- **学习路径规划**：格式为"系统：已生成个性化学习路径..." — 如果存在，向学生展示这个路径规划，作为你的回复重点
- **资源生成记录**：格式为"[resource_agent] 已为「知识点」生成 X 项学习资源..." 或下方「本轮新生成资源」— 如果存在，向学生说明已生成的资源类型和名称，引导前往资源页面查看

## 目前学习系统具备的功能
- 回答学生的提问，提供学习建议
- 生成个性化的学习资源推荐
- 当学生请求生成学习资源时，系统会自动生成并持久化到数据库

## 资源查看提示
- 当系统生成了学习资源（文档、PPT、试卷、代码案例等）后，请提示学生前往「我的学习资源」页面查看和管理，不要在聊天中展示完整内容。
- 如果当前有刚刚生成的资源（见下方的「本轮新生成资源」），请主动告知学生生成了哪些具体资源。
- 示例回复："已为你生成 C语言指针的学习文档和PPT，请前往「我的学习资源」页面查看。"
"""


# ═══════════════════════════════════════════════════════════
#  Agent 主函数
# ═══════════════════════════════════════════════════════════

def chat_agent(state: LearningState):
    """
    处理学生消息，与学生进行对话，更新对话历史。

    额外职责：
    - 检测学生表达的"理解"信号，自动记录教学经验到 ChromaDB
    - 检索历史教学经验作为当前回复的参考上下文
    """
    print(f"\n[ChatAgent]  开始处理对话...")

    history = state.get("history", [])
    message = state.get("message", "")

    # ════════════════════════════════════════════════════════
    #  教学经验记录：检测理解信号 → 整理 → 存入 ChromaDB
    # ════════════════════════════════════════════════════════
    if message and _is_understanding_signal(message):
        qa = _extract_last_qa(history)
        if qa:
            print(f"[ChatAgent]  检测到理解信号，正在总结教学经验...")
            summary = _summarize_teaching(qa["question"], qa["answer"])
            teaching_memory.save(
                question=qa["question"],
                answer=qa["answer"],
                teaching_approach=summary["teaching_approach"],
                focus_points=summary["focus_points"],
                knowledge_point=summary["knowledge_point"],
            )
            print(f"[ChatAgent]  教学经验已存入知识库")

    # ════════════════════════════════════════════════════════
    #  教学经验检索：为当前问题寻找历史成功教学参考
    # ════════════════════════════════════════════════════════
    teaching_context = ""
    if message:
        try:
            related = teaching_memory.search(message, k=2)
            refs = []
            for r in related:
                if r["distance"] < 0.85:  # 只取相似度较高的
                    parts = [f"  类似问题：{r['question'][:120]}"]
                    if r.get("teaching_approach"):
                        parts.append(f"  教学策略：{r['teaching_approach']}")
                    if r.get("focus_points"):
                        parts.append(f"  侧重点：{r['focus_points']}")
                    if r.get("knowledge_point"):
                        parts.append(f"  知识点：{r['knowledge_point']}")
                    refs.append("\n".join(parts))
            if refs:
                teaching_context = (
                    "\n\n## 参考以往成功教学经验\n"
                    "下面是对类似问题的历史成功教学记录，供你参考其讲解角度和策略：\n"
                    + "\n---\n".join(refs)
                )
                print(f"[ChatAgent]  找到 {len(refs)} 条相关教学经验参考")
        except Exception as e:
            print(f"[ChatAgent]  教学经验检索失败: {e}")

    # ════════════════════════════════════════════════════════
    #  知识库检索：从课程知识库中检索相关上下文
    # ════════════════════════════════════════════════════════
    knowledge_context = ""
    if message:
        try:
            kb_results = search_knowledge(message, k=5)
            if kb_results:
                knowledge_context = format_rag_results(kb_results, max_chars=1500)
                if knowledge_context:
                    knowledge_context = (
                        "\n\n## 课程知识库参考\n"
                        "以下是课程知识库中与当前问题相关的内容，请据此回答：\n"
                        + knowledge_context
                    )
                    print(f"[ChatAgent]  知识库命中，提供上下文 ({len(knowledge_context)} 字)")
        except Exception as e:
            print(f"[ChatAgent]  知识库检索失败: {e}")

    # ════════════════════════════════════════════════════════
    #  本轮新生成资源上下文
    # ════════════════════════════════════════════════════════
    resource_context = ""
    new_resources = state.get("generated_resources", [])
    if new_resources:
        type_labels = {
            "document": "文档", "exam": "试卷", "code_example": "代码案例",
            "ppt": "PPT", "image": "图片", "video": "视频",
            "mindmap": "思维导图", "extra_reading": "拓展阅读",
        }
        items = []
        for r in new_resources:
            t = r.type.value if hasattr(r.type, "value") else str(r.type)
            label = type_labels.get(t, t)
            items.append(f"  - {label}：{r.title}")
        resource_context = (
            "\n\n## 本轮新生成资源\n"
            "本轮对话中新生成的学习资源列表（已保存到数据库）：\n"
            + "\n".join(items)
        )
        print(f"[ChatAgent]  检测到 {len(new_resources)} 项本轮新生成资源")

    # ════════════════════════════════════════════════════════
    #  生成回复
    # ════════════════════════════════════════════════════════
    effective_prompt = CHAT_PROMPT + teaching_context + knowledge_context + resource_context

    prompt = ChatPromptTemplate.from_messages([
        SystemMessage(content=effective_prompt),
        MessagesPlaceholder("history"),
        ("user", "{human_message}"),
    ])

    chain = prompt | chat_llm
    response = chain.invoke({"history": history, "human_message": message})

    print(f"[ChatAgent]  回复完成 ({len(response.content)} 字)")

    # ── 内容安全过滤 ────────────────────────────────────
    keyword_hits = content_safety_checker.keyword_scan(response.content)
    if keyword_hits:
        print(f"[ChatAgent]  回复命中敏感词: {keyword_hits}")
        safe_notice = "抱歉，我的回复包含敏感内容，已被系统过滤。请尝试换一种方式提问。"
        response = AIMessage(content=safe_notice)
    else:
        if len(response.content) > 50:
            passed, reason = content_safety_checker.llm_safety_check(response.content)
            if not passed:
                print(f"[ChatAgent]  回复未通过安全审查: {reason}")
                safe_notice = (
                    "抱歉，我的回复未通过安全审查，已被系统拦截。"
                    "请重新描述你的问题，我会尽力提供合规的解答。"
                )
                response = AIMessage(content=safe_notice)

    return {
        "history": history + [response],
        "message": "",  # 消息已处理，清空避免 Supervisor 重复判断
        "response": response.content,
    }



if __name__ == "__main__":

    test_state = {
        "history": [HumanMessage(content="明天星期几？"), AIMessage(content="能告诉我今天是星期几吗？")],
        "student_id": "student123",
        "message": "今天是星期三",
        "session_id": "session123",
    }

    r = chat_agent(test_state)
    print(r["history"])








