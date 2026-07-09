"""
资源生成子图（Subgraph）
结构：
  planner → Send() ─┬→ doc_generator ──────────┐
                     ├→ exam_generator → exam_reflector ─┬→ exam_generator (重试)
                     ├→ ppt_generator  ─────────────────┤
                     ├→ image_retriever ────────────────┤
                     ├→ video_retriever ────────────────┤
                     ├→ mindmap_generator ──────────────┤
                     └→ reading_retriever ──────────────┘
                         → safety_filter → collector → END

exam_generator 单独走"生成→反思"链路，exam_reflector 验证不通过则重试，最多 2 次。
safety_filter 对所有生成资源做内容安全审查和事实准确性检查（防幻觉），
            未通过的资源被标记并从最终结果中移除。
"""
from langgraph.graph import StateGraph, END
from langgraph.types import Send

from app.resource_subgraph.state import ResourceSubState
from app.resource_subgraph.planner import resource_planner
from app.resource_subgraph.doc_generator import doc_generator
from app.resource_subgraph.exam_generator import exam_generator
from app.resource_subgraph.ppt_generator import ppt_generator
from app.resource_subgraph.image_retriever import image_retriever
from app.resource_subgraph.video_retriever import video_retriever
from app.resource_subgraph.mindmap_generator import mindmap_generator
from app.resource_subgraph.reading_retriever import reading_retriever
from app.resource_subgraph.exam_reflector import exam_reflector, route_from_exam_reflector
from app.resource_subgraph.safety_filter import safety_filter

# ── 生成器节点映射 ──────────────────────────────────────
# planner 输出的 resource_type → 子图节点名称
GENERATOR_MAP = {
    "document": "doc_generator",
    "exam": "exam_generator",
    "ppt": "ppt_generator",
    "image": "image_retriever",
    "video": "video_retriever",
    "mindmap": "mindmap_generator",
    "extra_reading": "reading_retriever",
}

ALL_GENERATORS = list(GENERATOR_MAP.values())


# ── 路由函数 ────────────────────────────────────────────

def route_to_generators(state: ResourceSubState) -> list[Send] | str:
    """
    条件路由：从 resource_plan 生成 Send() 列表，并行派发。
    - 如果 plan 为空 → 返回 "collector"，直接走汇总节点
    - 否则为每个资源类型创建一个 Send(target_node, state)
    """
    plan = state.get("resource_plan", [])

    if not plan:
        print(f"[Subgraph]  resource_plan 为空，跳过生成")
        return "collector"

    sends = []
    for resource_type in plan:
        node_name = GENERATOR_MAP.get(resource_type)
        if node_name:
            sends.append(Send(node_name, state))
        else:
            print(f"[Subgraph]  未知资源类型: {resource_type}，已跳过")

    if not sends:
        print(f"[Subgraph]  无有效的资源类型，跳过生成")
        return "collector"

    print(f"[Subgraph] Send 并行派发: {', '.join(s.node for s in sends)}")
    return sends


# ── 汇总节点 ────────────────────────────────────────────

def resource_collector(state: ResourceSubState) -> dict:
    """
    汇总节点：收集所有生成器的成果，构建汇总回复。
    当 Send() 的所有分支都执行完毕后，collector 被调用一次。
    """
    resources = state.get("generated_resources", [])
    plan = state.get("resource_plan", [])

    # 过滤掉已被反射节点标记为无效的资源（如格式错误的试卷）
    invalid_id = state.get("exam_invalid_resource_id")
    if invalid_id:
        resources = [r for r in resources if r.id != invalid_id]

    # 过滤掉被 safety_filter 标记为不安全的资源
    unsafe_ids = state.get("unsafe_resource_ids", [])
    if unsafe_ids:
        before = len(resources)
        resources = [r for r in resources if r.id not in unsafe_ids]
        filtered = before - len(resources)
        if filtered > 0:
            print(f"[ResourceCollector]  安全过滤移除 {filtered} 项不安全资源")

    print(f"\n[ResourceCollector]  汇总资源生成结果...")

    if not resources:
        print(f"[ResourceCollector]  无资源生成")
        return {"response": "本次未生成学习资源。"}

    # 按类型统计
    type_counts: dict[str, int] = {}
    for r in resources:
        type_counts[r.type] = type_counts.get(r.type, 0) + 1

    # 构建汇总信息
    type_labels = {
        "document": " 学习文档",
        "exam": " 试卷",
        "ppt": " PPT 课件",
        "image": " 图片",
        "video": " 视频",
        "mindmap": " 思维导图",
        "extra_reading": " 拓展阅读",
    }

    lines = [f"已为当前知识点生成 {len(resources)} 项学习资源：\n"]
    for r in resources:
        label = type_labels.get(r.type, " " + r.type)
        lines.append(f"- {label}：**{r.title}**")

    response = "\n".join(lines)

    # 记录详细日志
    for r in resources:
        print(f"   {r.type}: {r.title}")

    return {"response": response}


# ── 构建子图 ────────────────────────────────────────────

def build_resource_subgraph() -> StateGraph:
    """
    构建并编译资源生成子图。
    """
    builder = StateGraph(ResourceSubState)

    # 注册节点
    builder.add_node("planner", resource_planner)
    builder.add_node("doc_generator", doc_generator)
    builder.add_node("exam_generator", exam_generator)
    builder.add_node("ppt_generator", ppt_generator)
    builder.add_node("image_retriever", image_retriever)
    builder.add_node("video_retriever", video_retriever)
    builder.add_node("mindmap_generator", mindmap_generator)
    builder.add_node("reading_retriever", reading_retriever)
    builder.add_node("exam_reflector", exam_reflector)
    builder.add_node("safety_filter", safety_filter)
    builder.add_node("collector", resource_collector)

    # 入口：planner
    builder.set_entry_point("planner")

    # planner → 条件路由
    #   - plan 有值 → Send() 并行派发到各生成器
    #   - plan 为空 → 返回 "collector" 走汇总节点
    builder.add_conditional_edges(
        "planner",
        route_to_generators,
        ALL_GENERATORS + ["collector"],   # path_map 包含所有可能目的地
    )

    # 普通生成器 → safety_filter（exam_generator 不走这里，它走反思链路）
    for gen_node in ALL_GENERATORS:
        if gen_node == "exam_generator":
            continue
        builder.add_edge(gen_node, "safety_filter")

    # exam_generator → exam_reflector（固定路由）
    builder.add_edge("exam_generator", "exam_reflector")

    # exam_reflector → exam_generator（重试）或 safety_filter（通过）
    builder.add_conditional_edges(
        "exam_reflector",
        route_from_exam_reflector,
        {"exam_generator": "exam_generator", "safety_filter": "safety_filter"},
    )

    # collector → END
    # safety_filter → collector
    builder.add_edge("safety_filter", "collector")

    builder.add_edge("collector", END)

    return builder.compile()


# 编译单例（模块加载时构造，供外部 import）
resource_subgraph = build_resource_subgraph()
