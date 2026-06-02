"""
视觉理解工具：分析图片内容（截图、手写题、图表等）
通过 LangChain @tool 装饰器封装，可 bind_tools 给任意 Agent
"""
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage
from app.core.llm import vision_llm


@tool
def analyze_image(image_base64: str, instruction: str = "请详细描述这张图片的内容") -> str:
    """
    分析图片内容，返回文字描述或回答图片相关的问题。

    适用场景：
    - 学生上传题目截图，识别题目内容
    - 学生上传手写笔记，识别并评价
    - 学生上传图表/数据截图，分析数据

    Args:
        image_base64: 图片的 base64 编码内容（不含 data:image/... 前缀）
        instruction: 对图片提出的问题或分析指令，如"这道题的答案是什么"
    """
    # 构造多模态消息（LangChain ChatOpenAI 原生支持）
    msg = HumanMessage(content=[
        {"type": "text", "text": instruction},
        {
            "type": "image_url",
            "image_url": {
                "url": f"data:image/png;base64,{image_base64}"
            },
        },
    ])

    response = vision_llm.invoke([msg])
    return response.content



