"""集中管理各 Agent 使用的 LLM 模型实例"""
from langchain_openai import ChatOpenAI
from app.config import settings
from langchain_community.chat_models import ChatTongyi

# 聊天对话模型（DeepSeek V4 Flash）
deepseek_v4_flash = ChatOpenAI(
    model="xopdeepseekv4flash",
    openai_api_key=settings.SPARK_MAAS_API_KEY,
    openai_api_base=settings.SPARK_MAAS_BASE_URL,
    temperature=0.7,
)

# 图片理解模型（混元 OCR）
hunyuan_model = ChatOpenAI(
    model="xophunyuanocr",
    openai_api_key=settings.SPARK_MAAS_API_KEY,
    openai_api_base="http://maas-api.cn-huabei-1.xf-yun.com/v1",
    temperature=0.7,
    max_tokens=8192,
)

# supervisor
free_qwen_1b7 = ChatOpenAI(
    model="xop3qwen1b7",
    openai_api_key=settings.SPARK_MAAS_API_KEY,
    openai_api_base=settings.SPARK_MAAS_BASE_URL,
    temperature=0.7,
)

# path_agent 专用（更注重规划能力）
qwen_30b = ChatOpenAI(
    model="xop3qwen30b",
    openai_api_key=settings.SPARK_MAAS_API_KEY,
    openai_api_base=settings.SPARK_MAAS_BASE_URL,
    temperature=0.7,
)

# tool_node 专用（允许 Function Calling）
deepseek_v3 = ChatOpenAI(
    model="xopdeepseekv32",
    openai_api_key=settings.SPARK_MAAS_API_KEY,
    openai_api_base=settings.SPARK_MAAS_BASE_URL,
    temperature=0.7,
)


chat_llm = deepseek_v3
vision_llm = hunyuan_model
supervisor_llm = deepseek_v3
path_llm = deepseek_v3
tool_llm = deepseek_v3


# chat_llm = ChatTongyi(model="qwen3-max", temperature=0.7)
# supervisor_llm = ChatTongyi(model="qwen3-max", temperature=0.7)
# tool_llm = ChatTongyi(model="qwen3-max", temperature=0.7)
# path_llm = ChatTongyi(model="qwen3-max", temperature=0.7)





