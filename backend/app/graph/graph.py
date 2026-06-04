"""
主图：Supervisor 循环图 — 所有节点执行后回到 Supervisor，由 LLM 动态决策下一步
"""
from langgraph.graph import StateGraph, END
from app.graph.state import LearningState
from app.agents.supervisor_agent import supervisor_agent
from app.agents.profile_agent import profile_agent
from app.agents.resource_agent import resource_agent
from app.agents.path_agent import path_agent
from app.agents.error_sim_agent import error_sim_agent
from app.agents.buddy_agent import buddy_agent
from app.agents.curiosity_agent import curiosity_agent
from app.agents.reflection_agent import reflection_agent
from app.agents.tool_node import tool_node
from app.agents.chat_agent import chat_agent
from app.agents.rewrite_node import rewrite_node


MAX_ITERATIONS = 10  # 最大循环轮次，防止无限循环

# 标准 Agent：注册为节点，执行完后回到 Supervisor，由它继续调度
ALL_AGENTS = [
    "chat_agent", "profile_agent", "path_agent", "resource_agent",
    "error_sim_agent", "buddy_agent", "curiosity_agent", "reflection_agent",
    "tool_node",
]

# Supervisor 条件路由范围（path_agent 不在此列——它由 rewrite_node 的硬边触发）
ROUTE_MAP = {name: name for name in ALL_AGENTS if name != "path_agent"} | {"rewrite_node": "rewrite_node", "FINISH": END}


def route_from_supervisor(state: LearningState) -> str:
    """读取 state 中的 next_agent，路由到对应节点"""
    operation = state.get("operation", 0)
    if operation >= MAX_ITERATIONS:
        print(f"[Graph]  达到最大迭代次数 {MAX_ITERATIONS}，强制结束")
        return "FINISH"

    # === 代码层硬规则：message 已被 chat_agent 处理完毕，本轮结束 ===
    if not state.get("message"):
        print(f"[Graph]  message 为空，本轮对话结束")
        return "FINISH"

    next_agent = state.get("next_agent", "FINISH")
    if next_agent not in ROUTE_MAP:
        print(f"[Graph]  未知的 next_agent: {next_agent}，兜底到 chat_agent")
        return "chat_agent"
    print(f"[Graph]   路由: supervisor → {next_agent}")
    return next_agent


def build_graph() -> StateGraph:
    workflow = StateGraph(LearningState)

    # 注册 Supervisor
    workflow.add_node("supervisor", supervisor_agent)

    # 注册标准 Agent（包含 path_agent）
    for name in ALL_AGENTS:
        workflow.add_node(name, globals()[name])

    # 注册 rewrite_node（独立注册，不放入 ALL_AGENTS 以自定义路由）
    workflow.add_node("rewrite_node", rewrite_node)

    # Supervisor 是入口
    workflow.set_entry_point("supervisor")

    # Supervisor 条件路由到各 Agent
    workflow.add_conditional_edges("supervisor", route_from_supervisor, ROUTE_MAP)

    # 标准 Agent 执行完后回到 Supervisor 继续调度
    for name in ALL_AGENTS:
        workflow.add_edge(name, "supervisor")

    # === rewrite_node 走硬边到 path_agent，不经过 Supervisor ===
    workflow.add_edge("rewrite_node", "path_agent")

    return workflow.compile()


learning_graph = build_graph()
