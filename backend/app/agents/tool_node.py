"""
工具执行节点：通过 bind_tools 让 LLM 自主选择并调用工具
实现 Function Calling 能力
"""
from app.graph.state import LearningState
from app.core.llm import chat_llm
from app.tools.vision_tool import analyze_image
from langchain_core.messages import HumanMessage


def tool_node(state: LearningState) -> dict:
    """
    LLM 自主判断是否调用工具、调用哪个工具。
    当前可用工具：
    - analyze_image：分析图片内容
    """
    message = state.get("message", "")
    image_base64 = state.get("image_base64")

    # 如果有图片，在 prompt 里提示 LLM 图片已就绪
    img_hint = ""
    if image_base64:
        img_hint = "\n（用户上传了一张图片，已准备好 base64 数据。如需分析请调用 analyze_image）"

    llm = chat_llm.bind_tools([analyze_image])
    response = llm.invoke([HumanMessage(content=message + img_hint)])

    # 检查 LLM 是否决定调工具
    if response.tool_calls:
        for tc in response.tool_calls:
            if tc["name"] == "analyze_image":
                args = tc["args"]
                # 注入真实的图片数据（LLM 无法知道 base64 内容）
                if image_base64:
                    args["image_base64"] = image_base64
                result = analyze_image.invoke(args)
                return {
                    "tool_result": result,
                    "next_agent": "supervisor",
                }


    # LLM 认为不需要调工具，直接返回文本回复
    return {
        "tool_result": response.content,
        "next_agent": "supervisor",
    }
