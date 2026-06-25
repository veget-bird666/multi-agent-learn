"""
思维导图生成器（mindmap_generator）
职责：根据知识点 + 学生画像，LLM 生成 Mermaid 思维导图代码。
"""
import time
from langchain_core.prompts import ChatPromptTemplate

from app.core.llm import chat_llm
from app.models.resources import Resource, ResourceType
from app.resource_subgraph.state import ResourceSubState


SYSTEM_PROMPT = """你是一个思维导图设计专家，擅长将知识点整理为层级清晰的 Mermaid 思维导图。

## Mermaid 思维导图语法
使用 mindmap 语法，示例：

```mermaid
mindmap
  root((主题))
    分支1
      子分支1.1
      子分支1.2
    分支2
      子分支2.1
```

## 设计原则
1. **层级结构**：控制在 3~4 层（根→分支→子分支→叶子），不要太深
2. 防幻觉：所有节点内容必须基于学科知识，不得编造不存在的概念
3. **节点数量**：6~15 个节点为宜，覆盖核心知识点
3. **根节点**：用 `((主题))` 圆形包裹
4. **分支命名**：简洁，每节点 2~8 个字
5. **知识覆盖**：确保覆盖知识点的核心内容，同时保持结构清晰
6. **适配学生**：根据学生的认知风格调整结构
   - 举例型：多放实际应用案例作为叶子节点
   - 实践型：突出操作步骤和实操要点
   - 理论型：突出概念定义和逻辑关系

## 输出格式
只输出 Mermaid mindmap 代码，不要加额外的 Markdown 包裹或解释文字。
代码以 `mindmap` 开头，每行缩进用 2 个空格。"""


def mindmap_generator(state: ResourceSubState) -> dict:
    """
    生成 Mermaid 思维导图。
    """
    knowledge_point = state.get("knowledge_point", "")
    profile = state.get("profile")
    rewritten = state.get("rewritten_query", "")
    cleaned_topic = state.get("cleaned_topic", "")

    topic = cleaned_topic or rewritten or knowledge_point
    if not topic:
        print(f"[MindmapGenerator]  无知识点，跳过")
        return {"generated_resources": []}

    print(f"\n[MindmapGenerator]  开始生成思维导图: {topic}")

    # 构建画像摘要
    profile_summary = ""
    if profile:
        items = []
        for label, val in [
            ("认知风格", profile.cognitive_style),
            ("知识基础", profile.knowledge_base),
            ("兴趣领域", ", ".join(profile.interest_areas[:3]) if profile.interest_areas else None),
        ]:
            if val:
                items.append(f"{label}={val}")
        profile_summary = "；".join(items)

    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        ("user", (
            "请为「{topic}」生成 Mermaid mindmap 思维导图。\n\n"
            "学生画像参考：\n{profile_summary}\n\n"
            "如果学生有重写查询的额外需求，请参考：\n{rewritten}"
        )),
    ])

    chain = prompt | chat_llm
    try:
        result = chain.invoke({
            "topic": topic,
            "profile_summary": profile_summary or "（暂无）",
            "rewritten": rewritten or "（无）",
        })

        mermaid_code = result.content.strip()
        # 清理可能的 markdown 代码块包裹
        if mermaid_code.startswith("```"):
            lines = mermaid_code.split("\n")
            # 去掉第一行 ```mermaid 或 ``` 和最后一行 ```
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            mermaid_code = "\n".join(lines).strip()

        print(f"[MindmapGenerator]  思维导图生成完成 ({len(mermaid_code)} 字符)")
        print(f"---Mermaid Code---\n{mermaid_code[:200]}...\n------------------")

        resource = Resource(
            id=f"mindmap_{int(time.time())}",
            type=ResourceType.MINDMAP,
            title=f"{topic} 思维导图",
            content=mermaid_code,
            knowledge_point=knowledge_point or topic,
            difficulty=_estimate_difficulty(profile),
        )
        return {"generated_resources": [resource]}

    except Exception as e:
        print(f"[MindmapGenerator]  生成失败: {e}")
        return {"generated_resources": []}


def _estimate_difficulty(profile) -> str:
    """根据知识基础估算难度。"""
    if not profile or not profile.knowledge_base:
        return "medium"
    kb = profile.knowledge_base.lower()
    if any(k in kb for k in ["零基础", "入门", "初级", "较差"]):
        return "easy"
    if any(k in kb for k in ["高级", "深入", "熟练"]):
        return "hard"
    return "medium"
