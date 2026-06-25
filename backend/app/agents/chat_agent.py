"""
智能体：聊天智能体
职责：与学生进行对话（含内容安全过滤）
"""
from app.models.user import StudentProfile
from app.services.profile_service import profile_service
from app.core.llm import chat_llm
from app.core.content_safety import content_safety_checker

from app.graph.state import LearningState
from langchain_community.chat_models import ChatTongyi
from langchain_core.prompts import ChatPromptTemplate,MessagesPlaceholder
from langchain_core.messages import HumanMessage, SystemMessage,AIMessage

CHAT_PROMPT = """
你是一个Agent学习系统中专门负责对话的智能体（Chat Agent），负责与学生进行对话，更新对话历史。

## 你需要注意的信息
对话历史中可能包含以下系统消息，你需要据此回复：
- **画像更新记录**：格式为"系统：已更新学生画像..." — 据此了解学生当前画像状态
- **学习路径规划**：格式为"系统：已生成个性化学习路径..." — 如果存在，向学生展示这个路径规划，作为你的回复重点
- 如果没有以上信息，正常回答学生的问题即可

## 目前学习系统具备的功能
- 回答学生的提问，提供学习建议
- 生成个性化的学习资源推荐

## 资源查看提示
- 当系统生成了学习资源（文档、PPT、试卷等）后，请提示学生前往「我的学习资源」页面查看和管理，不要在聊天中展示完整内容。
- 示例回复："已为你生成 C语言指针的学习文档和PPT，请前往「我的学习资源」页面查看。"
"""

def chat_agent(state: LearningState):

    """
    处理学生消息，与学生进行对话，更新对话历史
    """
    print(f"\n[ChatAgent]  开始处理对话...")

    history = state.get("history")
    message = state.get("message")
    model = chat_llm

    prompt = ChatPromptTemplate.from_messages([
        SystemMessage(content=CHAT_PROMPT),
        MessagesPlaceholder("history"),
        ("user", "{human_message}"),
      ])

    chain = prompt | model
    response = chain.invoke({"history": history, "human_message": message})

    print(f"[ChatAgent]  回复完成 ({len(response.content)} 字)")

    # ── 内容安全过滤 ────────────────────────────────────
    keyword_hits = content_safety_checker.keyword_scan(response.content)
    if keyword_hits:
        print(f"[ChatAgent]  回复命中敏感词: {keyword_hits}")
        # 替换回复为安全提示
        safe_notice = "抱歉，我的回复包含敏感内容，已被系统过滤。请尝试换一种方式提问。"
        response = AIMessage(content=safe_notice)
    else:
        # LLM 安全审查（仅对较长回复做抽查以节省 token）
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








