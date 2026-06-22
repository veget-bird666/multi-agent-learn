"""
查询重写模块：将用户自然语言问题重写为适合 RAG 检索的搜索查询
使用轻量模型，免费高效
"""
from app.core.llm import supervisor_llm
from langchain_core.prompts import ChatPromptTemplate

REWRITE_PROMPT = """你是一个查询重写助手。你的任务是将用户的原始问题重写为更清晰、更利于搜索的查询语句。

## 输入
- **原始消息**：用户说的话
- **上下文**：对话背景、已知画像等

## 输出要求
- 提取核心搜索意图，去除口语化表达
- 补充关键术语，使查询更完整
- 保留技术术语和专有名词
- **如果用户提到"生成/制作/创建PPT/文档/资料/试卷"等资源类指令，忽略这些词，只提取知识点部分**
- 输出形式：简洁的关键词组合或短句（10-40 字）
- 不要输出完整句子，不要加解释

## 示例

原始：我想学C语言编程，但是完全零基础
输出：C语言编程 零基础入门 学习路线

原始：这个for循环嵌套把我绕晕了
输出：C语言 for循环嵌套 执行流程 典型例题

原始：帮我解释一下指针和数组的区别
输出：C语言 指针与数组 区别 联系 用法对比

原始：帮我生成C语言指针的教学PPT
输出：C语言指针 教学

原始：你好，今天天气不错
输出：（输出空字符串，不需要搜索）

原始：我正在学习python字典，你能帮我生成教学的ppt吗？
输出：Python字典 学习 详解"""


async def rewrite_query(message: str, context: str = "") -> str:
    """
    将用户消息重写为搜索查询。

    Args:
        message: 用户原始消息
        context: 上下文信息（画像摘要、对话历史摘要等）

    Returns:
        重写后的搜索查询。如果无需搜索则返回空字符串。
    """
    if not message or len(message.strip()) < 3:
        return ""

    prompt = ChatPromptTemplate.from_messages([
        ("system", REWRITE_PROMPT),
        ("user", "原始消息：{message}\n上下文：{context}"),
    ])

    chain = prompt | supervisor_llm
    result = await chain.ainvoke({
        "message": message,
        "context": context or "无额外上下文",
    })

    query = result.content.strip()
    print(f"[QueryRewrite] 原始: {message[:40]}... → 重写: {query[:60]}...")
    return query


if __name__ == "__main__":
    # 简单测试
    test_cases = [
        "我想学C语言编程，但是完全零基础",
        "这个for循环嵌套把我绕晕了",
        "你好，今天天气不错",
    ]
    for msg in test_cases:
        q = rewrite_query(msg)
        print(f"  -> '{q}'")
