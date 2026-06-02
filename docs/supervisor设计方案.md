# Supervisor 协调模式设计方案

## 背景

当前 7 个 Agent 的调用顺序是**硬编码**在 `graph.py` 中的：

```python
profile → path → resource → error_sim → buddy → curiosity → reflection → END
```

这种"流水线"模式适合流程固定的场景。但如果想让 LLM **根据当前状态动态决策下一步该调用哪个 Agent**，就需要引入 **Supervisor 协调节点**。

---

## 架构

```
                 ┌──────────────┐
                 │  Supervisor  │ ← LLM，决定下一步
                 └──────┬───────┘
                        │
          ┌─────────────┼──────────────┐
          ▼             ▼              ▼
    profile_agent   path_agent   resource_agent  ...  (7 个 Agent)
          │             │              │
          └─────────────┼──────────────┘
                        ▼
                  Supervisor ← 再次判断
                        │
                    FINISH → END
```

**关键变化**：
- 所有 Agent 节点执行完后都回到 Supervisor
- Supervisor 读取当前 `state`，判断"下一步该做什么"
- 直到 Supervisor 输出 `FINISH`，流程结束

---

## 改动清单

### 1. 新增文件：`app/agents/supervisor_agent.py`

```python
from pydantic import BaseModel, Field
from langchain_community.chat_models import ChatTongyi
from langchain_core.prompts import ChatPromptTemplate


class SupervisorDecision(BaseModel):
    """Supervisor 的输出格式"""
    next_agent: str = Field(description="下一个要执行的智能体名称：profile_agent / path_agent / resource_agent / error_sim_agent / buddy_agent / curiosity_agent / reflection_agent / FINISH")
    reasoning: str = Field(description="选择的理由")


def supervisor_agent(state: LearningState) -> dict:
    llm = ChatTongyi(model="qwen3-max")

    prompt = ChatPromptTemplate.from_messages([
        ("system", "你是一个学习系统的调度员。根据当前进度，判断下一步应该调用哪个智能体。"),

        # 将当前 state 中的关键信息传给 LLM
        ("user", """当前学习状态：
- 学生画像：{profile_status}
- 学习路径：{path_status}
- 当前知识点：{knowledge_point}
- 已生成资源数：{resource_count}
- 交互模式：{interaction_pattern}
- 上一轮响应：{last_response}

可选决策：{agent_list}
- FINISH：结束本轮学习

请选择下一步应该调用的智能体。"""),
    ])

    agent_list = [
        "profile_agent - 构建/更新学生画像",
        "path_agent - 规划学习路径",
        "resource_agent - 生成个性化资源",
        "error_sim_agent - 模拟并纠正典型错误",
        "buddy_agent - 虚拟学伴互动",
        "curiosity_agent - 分析好奇心/卡壳状态",
        "reflection_agent - 评估学习效果",
    ]

    chain = prompt | llm.with_structured_output(SupervisorDecision)
    decision = chain.invoke({
        "profile_status": "✅ 已完成" if state.get("profile") else "❌ 未完成",
        "path_status": "✅ 已规划" if state.get("learning_path") else "❌ 未规划",
        "knowledge_point": state.get("knowledge_point") or "无",
        "resource_count": len(state.get("generated_resources", [])),
        "interaction_pattern": state.get("interaction_pattern") or "无",
        "last_response": state.get("response") or "无",
        "agent_list": "\n".join(agent_list),
    })

    return {"next_agent": decision.next_agent}
```

### 2. 修改：`app/graph/graph.py`

```python
from app.agents.supervisor_agent import supervisor_agent

def build_graph() -> StateGraph:
    workflow = StateGraph(LearningState)

    # 注册所有节点（包括 supervisor）
    ALL_AGENTS = [
        "supervisor",        # 新增
        "profile_agent",
        "resource_agent",
        "path_agent",
        "error_sim_agent",
        "buddy_agent",
        "curiosity_agent",
        "reflection_agent",
    ]

    for name in ALL_AGENTS:
        workflow.add_node(name, node_funcs[name])

    workflow.set_entry_point("supervisor")  # 从 supervisor 开始

    # 所有 agent 执行完后都回到 supervisor
    for agent in ALL_AGENTS[1:]:  # 排除 supervisor 自身
        workflow.add_edge(agent, "supervisor")

    # supervisor 判断下一步
    workflow.add_conditional_edges(
        "supervisor",
        lambda state: state.get("next_agent", "FINISH"),
        {name: name for name in ALL_AGENTS} | {"FINISH": END},
    )

    return workflow.compile()
```

### 3. 不修改：其他 7 个 Agent

所有 Agent 的代码逻辑**完全不变**，只需确保它们返回的 dict 中包含足够的信息供 Supervisor 判断即可。

---

## 对比：代码路由 vs Supervisor

| 对比项 | 当前方案（代码路由） | Supervisor 方案 |
|---|---|---|
| **路由逻辑** | if-else 写在 graph.py | LLM 动态决策 |
| **灵活性** | 固定流水线 | 可根据状态跳转 |
| **可调试性** | ✅ 一眼看懂 | ❌ 需要看 LLM 的 reasoning |
| **成本** | 无额外 token | 每次决策多一次 LLM 调用 |
| **当前是否要改** | — | **暂不改，等 7 个 Agent 都开发完再做** |

---

## 建议实施时机

**先把 7 个 Agent 全部开发完，确保每个 Agent 能独立工作**，最后再花 1-2 小时把 Supervisor 接上。原因是：

1. Supervisor 的价值在于"在多种可能性中做选择"——Agent 都没实现完，它没什么可选的
2. 流水线模式调试更简单，每个 Agent 单独验证

> **一句话**：先让流水线跑通，再让 Supervisor 变得智能。
