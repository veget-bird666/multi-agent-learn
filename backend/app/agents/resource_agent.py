"""
智能体2：多智能体协同资源生成（子图入口）
从原来包含所有生成逻辑的函数，重构为子图包装器。

职责：
  1. 从主图 LearningState 提取子图所需字段
  2. 调用 resource_subgraph 运行完整的生成流程
  3. 将结果持久化到数据库，写简短摘要回 history

子图内部（resource_subgraph/）：
  planner → Send() → doc_generator / exam_generator / ppt_generator / image_retriever / video_retriever → collector
"""
import time

from app.graph.state import LearningState
from app.resource_subgraph.subgraph import resource_subgraph
from app.services.resource_service import resource_service
from langchain_core.messages import AIMessage


def resource_agent(state: LearningState) -> dict:
    """
    资源生成智能体 — 子图包装器。

    从主图 state 中提取字段，调用子图，将结果持久化到数据库。
    """
    knowledge_point = state.get("knowledge_point", "")
    rewritten_query = state.get("rewritten_query", "")
    raw_message = state.get("message", "")

    # 主题提取：rewritten_query > knowledge_point > 原始消息
    topic = rewritten_query or knowledge_point
    if not topic:
        topic = _extract_topic_from_message(raw_message)

    if not topic:
        print(f"[ResourceAgent]  未指定知识点，跳过资源生成")
        return {
            "generated_resources": [],
            "response": "请先指定要学习的内容或知识点。",
        }

    print(f"\n{'='*60}")
    print(f"[ResourceAgent]  启动资源生成子图")
    print(f"[ResourceAgent]   知识点: {knowledge_point}")
    print(f"[ResourceAgent]   重写查询: {rewritten_query}")
    print(f"[ResourceAgent]   提取主题: {topic}")
    print(f"{'='*60}")

    # ── 提取学习路径上下文 ─────────────────────────
    path_id = state.get("current_path_id")
    focused_step = state.get("focused_step_order")
    step_kps: list[str] = []
    focused_step_name = ""
    if path_id and focused_step is not None:
        learning_path = state.get("learning_path") or []
        for step in learning_path:
            if step.get("order") == focused_step:
                step_kps = step.get("knowledge_points", [])
                focused_step_name = step.get("stage_name", "")
                break
    if step_kps:
        print(f"[ResourceAgent]  绑定到路径#{path_id} 阶段{focused_step}，知识点: {step_kps}")
        # ★ 核心修复：有聚焦阶段时，用阶段信息覆盖 topic
        #    让 LLM 聚焦该阶段的知识点而非从用户消息中猜测
        kp_str = "、".join(step_kps)
        topic = f"{focused_step_name}（{kp_str}）"
        print(f"[ResourceAgent]   topic 已覆盖为聚焦阶段内容: {topic}")

    # ── 1. 准备子图输入 ──────────────────────────────
    sub_state = {
        "knowledge_point": topic,
        "cleaned_topic": topic,
        "profile": state.get("profile"),
        "message": state.get("message", ""),
        "rewritten_query": rewritten_query,
        "path_id": path_id,
        "step_order": focused_step,
        "step_knowledge_points": step_kps,
        "resource_plan": [],
        "generated_resources": [],
        "response": None,
    }

    # ── 2. 运行子图 ──────────────────────────────────
    try:
        result = resource_subgraph.invoke(sub_state)
    except Exception as e:
        print(f"[ResourceAgent]  子图运行异常: {e}")
        return {
            "generated_resources": [],
            "response": f"资源生成过程出现异常：{str(e)}",
        }

    # ── 3. 结果持久化到数据库 ─────────────────────────
    new_resources = result.get("generated_resources", [])
    sub_response = result.get("response")

    # 给所有资源补上路径上下文（方便后续按路径/阶段筛选）
    if path_id is not None:
        for r in new_resources:
            if r.path_id is None:
                r.path_id = path_id
            if r.step_order is None and focused_step is not None:
                r.step_order = focused_step

    print(f"\n[ResourceAgent]  子图完成，共生成 {len(new_resources)} 项资源")
    for r in new_resources:
        print(f"   - {r.type}: {r.title} [path={r.path_id}, step={r.step_order}]")

    # 为每个资源补上 timestamp 后缀避免 id 冲突
    timestamp_suffix = str(int(time.time()))
    for r in new_resources:
        if not r.id.endswith(timestamp_suffix):
            r.id = f"{r.id}_{timestamp_suffix}"

    # 保存到数据库
    student_id = state.get("student_id", "")
    if new_resources and student_id:
        resource_service.save_batch(new_resources, student_id)
        print(f"[ResourceAgent]  已持久化 {len(new_resources)} 项资源到数据库")

    # ── 4. 写简短摘要到 history（替代原来的完整资源列表）──
    type_labels = {
        "document": "文档", "exam": "试卷", "ppt": "PPT",
        "image": "图片", "video": "视频",
    }
    if new_resources:
        # 按类型去重统计
        type_counts: dict[str, int] = {}
        for r in new_resources:
            t = r.type.value if hasattr(r.type, "value") else str(r.type)
            label = type_labels.get(t, t)
            type_counts[label] = type_counts.get(label, 0) + 1
        types_str = "、".join(f"{k}{v}份" if v > 1 else k for k, v in type_counts.items())

        summary = (
            f"[resource_agent] 已为「{topic}」生成 {len(new_resources)} 项学习资源"
            f"（{types_str}），请前往「我的学习资源」页面查看。"
        )
        agent_msg = AIMessage(content=summary)
        updated_history = list(state.get("history") or []) + [agent_msg]
    else:
        updated_history = state.get("history") or []

    return {
        "generated_resources": new_resources,
        "history": updated_history,
        "response": sub_response or (
            f"已为「{topic}」生成 {len(new_resources)} 项学习资源，"
            f"可前往「我的学习资源」页面查看。"
        ),
    }


def _extract_topic_from_message(message: str) -> str:
    """从原始消息中提取学习主题。"""
    if not message or len(message.strip()) < 3:
        return ""
    import re
    cleaned = re.sub(r"[，。！？、；：""''【】《》（）\-\+\.,\/\\#!?~]", "", message)
    return cleaned.strip()[:20]
