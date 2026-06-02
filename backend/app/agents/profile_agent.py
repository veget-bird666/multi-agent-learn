"""
智能体1：对话式学习画像构建
职责：通过自然语言对话，自动抽取学生特征，构建6+维度动态画像
"""
from app.models.user import StudentProfile
from app.services.profile_service import profile_service
from app.graph.state import LearningState
from app.core.llm import tool_llm
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage


def profile_agent(state: LearningState):
    """
    处理学生消息，抽取画像维度：
    - 知识基础、认知风格、学习节奏、兴趣领域、易错点偏好、学习目标
    """
    print(f"\n[ProfileAgent] 🔍 开始构建/更新画像...")
    if state.get("profile_update_hint"):
        print(f"[ProfileAgent]   update_hint: {state['profile_update_hint']}")
    history = list(state.get("history") or [])
    student_id = state.get("student_id")
    pre_profile = profile_service.get(student_id)

    pre_profile_prompt = ""
    if pre_profile:
        pre_profile_prompt = f"学生的现有画像信息：{pre_profile.model_dump_json()}\n"

    # 如果 Supervisor 指定了更新重点，加入提示
    update_hint = state.get("profile_update_hint")
    hint_prompt = ""
    if update_hint:
        hint_prompt = f"本次重点关注的画像维度：{update_hint}\n"

    prompt = ChatPromptTemplate.from_messages([
        ("system", "你是一个学习画像构建助手，负责从学生的对话中抽取特征，"
                    "构建动态画像。字段包括：知识基础、认知风格、学习节奏、"
                    "兴趣领域、易错点偏好、学习目标等。"
                    "{pre_profile_prompt}"
                    "{hint_prompt}"
                    "如果对话不足以提取特征，则相关字段可以留空。"),
        MessagesPlaceholder("history"),
        ("user", "请根据以上对话，帮我抽取学生的特征，构建画像。"),
      ])

    chain = prompt | tool_llm.with_structured_output(StudentProfile)
    res_profile = chain.invoke({"history": history, "pre_profile_prompt": pre_profile_prompt, "hint_prompt": hint_prompt})
    res_profile.student_id = state.get("student_id")

    profile_service.save_or_update(res_profile)

    print(f"[ProfileAgent] ✅ 画像已保存: 认知风格={res_profile.cognitive_style}, 知识基础={res_profile.knowledge_base}, 兴趣={res_profile.interest_areas}")

    detail = f"系统：已更新学生画像（认知风格={res_profile.cognitive_style}，知识基础={res_profile.knowledge_base}）"
    system_message = SystemMessage(content=detail)

    return {
      "profile": res_profile,
      "history": history + [system_message],
      "profile_update_hint": None,  # 更新后清空提示，等待 Supervisor 下一轮判断是否需要新的提示
    }


if __name__ == "__main__":
      test_state = {
          "history": [HumanMessage(content="我喜欢实践操作，学习新知识比较慢，容易在公式推导上出错。")],
          "student_id": "student123",
          "message": "我喜欢实践操作，学习新知识比较慢，容易在公式推导上出错。",
          "session_id": "session123",
          "profile": None,
          "current_agent": None,
          "next_agent": None,
          "knowledge_point": None,
          "learning_path": None,
          "current_step": 0,
          "generated_resources": [],
          "teaching_decisions": [],
          "interaction_pattern": None,
          "response": None,
      }
      result = profile_agent(test_state)
      print(result["profile"])
