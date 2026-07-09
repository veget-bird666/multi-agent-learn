from fastapi import APIRouter, HTTPException, Query
from sse_starlette.sse import EventSourceResponse
from app.models.user import ChatRequest
from app.graph.graph import learning_graph
from app.services.profile_service import profile_service
from app.services.resource_service import resource_service
from app.services.learning_path_service import learning_path_service
from langchain_core.messages import HumanMessage
from app.services.session_service import session_service
import json
import asyncio

router = APIRouter()


@router.get("/health")
async def health_check():
    return {"status": "ok", "message": "AI 个性化学习多智能体系统运行中"}


@router.post("/chat")
async def chat(request: ChatRequest):
    """
    对话式学习入口：学生发送消息，触发多智能体协同处理
    支持多轮对话状态持久化。
    """
    try:
        # ── 会话持久化：确定 session_id ──
        session_id = request.session_id or f"session_{request.student_id}"
        previous_state = session_service.load(session_id) or {}

        # ── 构建历史记录（历史 + 新消息） ──
        history = list(previous_state.get("history", []) or [])
        history.append(HumanMessage(content=request.message))

        # ── 加载学习路径上下文（开关关闭时跳过） ──
        current_path_id = request.current_path_id
        learning_path_data = None

        if request.include_path_context:
            if current_path_id is not None:
                path = learning_path_service.get_by_id(current_path_id)
                if path:
                    learning_path_data = path.get("steps")
                else:
                    current_path_id = None  # 路径不存在则回退

            # 兜底：查 DB active 路径
            if current_path_id is None:
                active_path = learning_path_service.get_active(request.student_id)
                current_path_id = active_path["id"] if active_path else None
                learning_path_data = active_path["steps"] if active_path else None
        else:
            # 开关关闭 → 不传任何路径上下文
            current_path_id = None
            learning_path_data = None
            request.focused_step_order = None

        # ── 合并 state：持久化字段 + 新请求覆盖 ──
        state = dict(previous_state)
        state.update({
            "history": history,
            "operation": 0,  # 每次图执行重置轮次计数
            "student_id": request.student_id,
            "message": request.message,
            "session_id": session_id,
            # 重置临时运行态
            "current_agent": None,
            "next_agent": None,
            "next_reasoning": None,
            "profile_update_hint": None,
            "tool_result": None,
            "rewritten_query": None,
            "execution_plan": [],
            "current_plan_step": -1,
            "image_base64": None,
            "response": None,
        })
        # 学习路径用最新 DB 数据覆盖持久化值
        if request.include_path_context:
            state["learning_path"] = learning_path_data
            state["current_path_id"] = current_path_id
            state["focused_step_order"] = request.focused_step_order
        else:
            state["learning_path"] = None
            state["current_path_id"] = None
            state["focused_step_order"] = None
            state["current_step"] = 0

        # 用户开关：控制是否允许生成路径/资源
        state["enable_path_planning"] = request.enable_path_planning
        state["enable_resource_generation"] = request.enable_resource_generation

        # 跑完整多智能体图
        final_state = await learning_graph.ainvoke(state)

        # 持久化当前轮次状态
        session_service.save(session_id, request.student_id, final_state)

        # 调试信息
        resp_field = final_state.get("response", "")
        hist_len = len(final_state.get("history", []))
        print(f"[Routes] response字段: {'空' if not resp_field else f'长度{len(resp_field)}'}")
        print(f"[Routes] history长度: {hist_len}")
        if hist_len > 0:
            last_role = type(final_state["history"][-1]).__name__
            last_content = final_state["history"][-1].content[:80]
            print(f"[Routes] 最后一条history: {last_role} -> {last_content}")

        # 提取回复：优先 response 字段，其次 history 最后一条
        reply = final_state.get("response")
        if not reply and final_state.get("history"):
            last_msg = final_state["history"][-1]
            reply = last_msg.content

        # 获取标题（刚保存完，从 DB 取）
        session_title = session_service.get_title(session_id) or ""

        return {
            "session_id": session_id,
            "title": session_title,
            "response": reply or "抱歉，我没有生成有效回复。",
            "profile": final_state.get("profile"),
            "resources": final_state.get("generated_resources", []),
            "learning_path": final_state.get("learning_path"),
            "current_path_id": final_state.get("current_path_id"),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"处理请求时出错: {str(e)}")


# ── 多会话管理 ──────────────────────────────────────────


@router.get("/sessions/{student_id}")
async def list_sessions(student_id: str):
    """获取某学生的全部会话摘要列表"""
    sessions = session_service.list_by_student(student_id)
    return {"sessions": sessions}


@router.get("/sessions/{session_id}/messages")
async def get_session_messages(session_id: str):
    """获取某会话的历史消息列表"""
    messages = session_service.get_messages(session_id)
    # BaseMessage → dict for JSON serialization
    serialized = []
    for msg in messages:
        serialized.append({
            "role": "user" if msg.type == "human" else "assistant",
            "content": msg.content,
        })
    return {"messages": serialized}


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    """删除某个会话"""
    ok = session_service.delete(session_id)
    if not ok:
        raise HTTPException(status_code=404, detail="会话不存在")
    return {"message": "删除成功"}


@router.put("/sessions/{session_id}/title")
async def update_session_title(session_id: str, body: dict):
    """手动修改某个会话的标题"""
    title = body.get("title", "").strip()
    if not title:
        raise HTTPException(status_code=400, detail="标题不能为空")
    ok = session_service.update_title(session_id, title)
    if not ok:
        raise HTTPException(status_code=404, detail="会话不存在")
    return {"message": "标题更新成功", "session_id": session_id, "title": title}


@router.get("/chat")
async def chat_stream(
    student_id: str = Query(..., description="学生 ID"),
    message: str = Query(..., description="用户消息"),
    session_id: str = Query(None, description="会话 ID"),
    focused_step_order: int = Query(None, description="当前聚焦的学习阶段序号"),
    current_path_id: int = Query(None, description="当前选中的路径 ID"),
    include_path_context: bool = Query(True, description="是否将学习路径上下文发给模型"),
    enable_path_planning: bool = Query(True, description="是否允许生成学习路径"),
    enable_resource_generation: bool = Query(True, description="是否允许生成资源"),
):
    """
    SSE 流式对话入口 — 运行多智能体图，流式输出回复

    事件类型：
      - status:  Agent 执行状态更新
      - token:   回复文本片段
      - metadata: 最终状态（画像/资源/路径）
      - error:   错误信息
    """
    # ── 加载学习路径上下文（与 POST 保持一致） ──
    current_path_id_val = current_path_id
    learning_path_data = None

    if include_path_context:
        if current_path_id_val is not None:
            path = learning_path_service.get_by_id(current_path_id_val)
            if path:
                learning_path_data = path.get("steps")
            else:
                current_path_id_val = None
        if current_path_id_val is None:
            active_path = learning_path_service.get_active(student_id)
            current_path_id_val = active_path["id"] if active_path else None
            learning_path_data = active_path["steps"] if active_path else None
    else:
        current_path_id_val = None
        learning_path_data = None
        focused_step_order = None

    AGENT_LABELS = {
        "profile_agent": "👤 画像分析",
        "path_agent": "🗺️ 路径规划",
        "resource_agent": "📦 资源生成",
        "rewrite_node": "✏️ 查询重写",
        "tool_node": "🔧 工具调用",
        "chat_agent": "💬 生成回答",
    }

    async def event_generator():
        try:
            # 立即发送开始状态，触发浏览器建立 SSE 连接
            yield {"event": "status", "data": json.dumps({"agent": "start", "label": "🤔 分析中..."})}

            # ── 会话持久化 ──
            session_id_val = session_id or f"session_{student_id}"
            previous_state = session_service.load(session_id_val) or {}

            # ── 构建历史记录（历史 + 新消息） ──
            history = list(previous_state.get("history", []) or [])
            history.append(HumanMessage(content=message))

            # ── 合并 state ──
            state = dict(previous_state)
            state.update({
                "history": history,
                "operation": 0,
                "student_id": student_id,
                "message": message,
                "session_id": session_id_val,
                "current_agent": None,
                "next_agent": None,
                "next_reasoning": None,
                "profile_update_hint": None,
                "tool_result": None,
                "rewritten_query": None,
                "execution_plan": [],
                "current_plan_step": -1,
                "image_base64": None,
                "response": None,
            })
            if include_path_context:
                state["learning_path"] = learning_path_data
                state["current_path_id"] = current_path_id_val
                state["focused_step_order"] = focused_step_order
            else:
                state["learning_path"] = None
                state["current_path_id"] = None
                state["focused_step_order"] = None
                state["current_step"] = 0

            # 用户开关：控制是否允许生成路径/资源
            state["enable_path_planning"] = enable_path_planning
            state["enable_resource_generation"] = enable_resource_generation

            # ── 运行完整的 LangGraph ──
            final_state = await learning_graph.ainvoke(state)

            # 持久化当前轮次状态
            session_service.save(session_id_val, student_id, final_state)

            # ── 从 history 中提取 Agent 执行顺序 ──
            history = final_state.get("history", [])
            detected = set()
            for msg in history:
                content = msg.content if hasattr(msg, "content") else str(msg)
                for agent_name, label in AGENT_LABELS.items():
                    if agent_name not in detected and f"[{agent_name}]" in content:
                        detected.add(agent_name)
                        yield {"event": "status", "data": json.dumps({
                            "agent": agent_name,
                            "label": label,
                        })}

            if "chat_agent" not in detected:
                yield {"event": "status", "data": json.dumps({
                    "agent": "chat_agent",
                    "label": "💬 生成回答",
                })}

            # ── 流式输出回复文本 ──
            response = final_state.get("response", "") or ""
            CHUNK_SIZE = 3
            for i in range(0, len(response), CHUNK_SIZE):
                chunk = response[i:i + CHUNK_SIZE]
                yield {"event": "token", "data": json.dumps({"token": chunk})}
                await asyncio.sleep(0.008)  # 8ms 间隔，营造流式效果

            # ── 发送最终元数据 ──
            profile = final_state.get("profile")
            resources = final_state.get("generated_resources", [])
            # 刚保存完，从 DB 取最新的 title
            session_title = session_service.get_title(session_id_val) or ""
            yield {"event": "metadata", "data": json.dumps({
                "session_id": session_id_val,
                "title": session_title,
                "response": response,
                "profile": profile.model_dump() if profile and hasattr(profile, "model_dump") else profile,
                "resources": [
                    r.model_dump() if hasattr(r, "model_dump") else r
                    for r in resources
                ],
                "learning_path": final_state.get("learning_path"),
                "current_path_id": final_state.get("current_path_id"),
            })}

        except Exception as e:
            import traceback
            traceback.print_exc()
            yield {"event": "error", "data": json.dumps({"error": str(e)})}

    return EventSourceResponse(event_generator())


@router.get("/profile/{student_id}")
async def get_profile(student_id: str):
    """获取学生画像"""
    profile = profile_service.get(student_id)
    if profile is None:
        return {"student_id": student_id, "profile": None, "message": "暂无画像数据"}
    return {"student_id": student_id, "profile": profile.model_dump()}


# ── 多学习路径 ──────────────────────────────────────

@router.get("/learning-path/list/{student_id}")
async def list_learning_paths(student_id: str):
    """获取某学生的全部学习路径"""
    paths = learning_path_service.list_by_student(student_id)
    return {"student_id": student_id, "paths": paths}


@router.get("/learning-path/active/{student_id}")
async def get_active_learning_path(student_id: str):
    """获取学生当前选中的学习路径"""
    path = learning_path_service.get_active(student_id)
    if path is None:
        return {"student_id": student_id, "path": None, "message": "暂无学习路径"}
    return path


@router.put("/learning-path/active/{student_id}")
async def set_active_learning_path(student_id: str, body: dict):
    """切换当前学习的路径"""
    path_id = body.get("path_id")
    if not path_id:
        raise HTTPException(status_code=400, detail="需要提供 path_id")
    result = learning_path_service.set_active(path_id, student_id)
    if result is None:
        raise HTTPException(status_code=404, detail="未找到该学习路径")
    return result


@router.post("/learning-path/{student_id}")
async def create_learning_path(student_id: str, body: dict):
    """手动创建一条新学习路径"""
    title = body.get("title", "未命名路径")
    steps = body.get("steps", [])
    if not steps:
        raise HTTPException(status_code=400, detail="学习路径至少需要一个阶段")
    from app.models.resources import LearningPathStep
    parsed_steps = [LearningPathStep(**s) for s in steps]
    path = learning_path_service.create(student_id, title, parsed_steps)
    return path


@router.get("/learning-path/{path_id}")
async def get_learning_path(path_id: int):
    """根据路径 ID 获取单条学习路径"""
    path = learning_path_service.get_by_id(path_id)
    if path is None:
        raise HTTPException(status_code=404, detail="未找到该学习路径")
    return path


@router.put("/learning-path/{path_id}/mastery")
async def update_mastery(path_id: int, step_order: int, mastery: float):
    """更新某个学习阶段的掌握度"""
    if mastery < 0 or mastery > 100:
        raise HTTPException(status_code=400, detail="掌握度必须在 0~100 之间")
    result = learning_path_service.update_step_mastery(path_id, step_order, mastery)
    if result is None:
        raise HTTPException(status_code=404, detail="未找到该学习路径")
    return result


@router.put("/learning-path/{path_id}/kp-mastery")
async def update_kp_mastery(path_id: int, body: dict):
    """
    更新某个知识点的熟练度（增量累加）。
    body: {"step_order": 1, "knowledge_point": "指针概念", "increment": 8}
    mastery_increment 建议值：easy=5, medium=8, hard=12
    """
    step_order = body.get("step_order")
    kp_name = body.get("knowledge_point")
    increment = body.get("increment", 5)

    if step_order is None or not kp_name:
        raise HTTPException(status_code=400, detail="需要提供 step_order 和 knowledge_point")
    if increment < 0 or increment > 100:
        raise HTTPException(status_code=400, detail="increment 必须在 0~100 之间")

    result = learning_path_service.update_kp_mastery(path_id, step_order, kp_name, increment)
    if result is None:
        raise HTTPException(status_code=404, detail="未找到该学习路径")
    return result


@router.post("/learning-path/{path_id}/exam-submit")
async def submit_exam(path_id: int, body: dict):
    """
    提交试卷作答结果，批量更新知识点熟练度。
    body: {
        "step_order": 1,
        "results": [
            {"knowledge_point": "变量", "is_correct": true, "difficulty": "easy"},
            {"knowledge_point": "数据类型", "is_correct": false, "difficulty": "medium"}
        ]
    }
    熟练度增量规则：easy=5, medium=8, hard=12（答对加分，答错不加）
    """
    DIFFICULTY_MAP = {"easy": 5, "medium": 8, "hard": 12}
    step_order = body.get("step_order")
    results = body.get("results", [])

    if step_order is None:
        raise HTTPException(status_code=400, detail="需要提供 step_order")
    if not results:
        raise HTTPException(status_code=400, detail="results 不能为空")

    updated_count = 0
    for r in results:
        kp = r.get("knowledge_point")
        is_correct = r.get("is_correct", False)
        difficulty = r.get("difficulty", "medium")
        if kp and is_correct:
            increment = DIFFICULTY_MAP.get(difficulty, 5)
            learning_path_service.update_kp_mastery(path_id, step_order, kp, increment)
            updated_count += 1

    # 返回更新后的路径
    path = learning_path_service.get_by_id(path_id)
    print(f"[ExamSubmit]  试卷提交完成 - 路径#{path_id} 阶段{step_order}: {updated_count}/{len(results)} 题正确")
    return path or {"message": "提交完成但路径已不存在"}


@router.put("/learning-path/{path_id}/mastery/batch")
async def batch_update_mastery(path_id: int, updates: list[dict]):
    """批量更新多个阶段的掌握度"""
    result = learning_path_service.batch_update_mastery(path_id, updates)
    if result is None:
        raise HTTPException(status_code=404, detail="未找到该学习路径")
    return result


@router.put("/learning-path/{path_id}/knowledge-points")
async def update_knowledge_points(path_id: int, body: dict):
    """
    更新某个阶段的知识点列表。

    锁定规则：路径中任一阶段掌握度 > 0 时禁止编辑。
    只能修改知识点标签，不能修改阶段主结构。
    body: {"step_order": 1, "knowledge_points": ["指针概念", "指针运算"]}
    """
    step_order = body.get("step_order")
    knowledge_points = body.get("knowledge_points", [])

    if step_order is None:
        raise HTTPException(status_code=400, detail="需要提供 step_order")
    if not knowledge_points:
        raise HTTPException(status_code=400, detail="知识列表不能为空")
    if len(knowledge_points) > 20:
        raise HTTPException(status_code=400, detail="单阶段知识点不能超过 20 个")

    result = learning_path_service.update_step_knowledge_points(
        path_id, step_order, knowledge_points
    )
    if result is None:
        raise HTTPException(status_code=404, detail="未找到该学习路径")

    if result.get("_locked"):
        raise HTTPException(
            status_code=403,
            detail="该学习路径已开始学习（掌握度已上升），无法修改知识点",
        )

    return result


@router.delete("/learning-path/{path_id}")
async def delete_learning_path(path_id: int):
    """删除一条学习路径（同时删除关联的所有资源）"""
    ok = learning_path_service.delete(path_id)
    if not ok:
        raise HTTPException(status_code=404, detail="未找到该学习路径")
    return {"message": "删除成功"}


@router.get("/resources/{student_id}")
async def list_resources(student_id: str):
    """获取某学生的全部已生成资源"""
    items = resource_service.list_with_orm_ids(student_id)
    return {"resources": items}


@router.delete("/resources/{orm_id}")
async def delete_resource(orm_id: int):
    """删除一条资源记录"""
    ok = resource_service.delete(orm_id)
    if not ok:
        raise HTTPException(status_code=404, detail="资源不存在")
    return {"message": "删除成功"}


@router.post("/resources")
async def create_resource(body: dict):
    """创建一条新资源（如导出学习笔记）"""
    from app.models.resources import Resource, ResourceType
    import uuid

    student_id = body.get("student_id")
    if not student_id:
        raise HTTPException(status_code=400, detail="缺少 student_id")

    resource = Resource(
        id=str(uuid.uuid4()),
        type=ResourceType.DOCUMENT,
        title=body.get("title", ""),
        content=body.get("content", ""),
        knowledge_point=body.get("knowledge_point", ""),
        difficulty=body.get("difficulty", "medium"),
        path_id=body.get("path_id"),
        step_order=body.get("step_order"),
    )
    resource_service.save(resource, student_id)
    return {"message": "保存成功", "resource_id": resource.id}


# ═══════════════════════════════════════════════════════════
#  虚拟学伴（独立于主图的双层输出聊天）
# ═══════════════════════════════════════════════════════════

from app.buddy import buddy_service
from app.buddy.schemas import QuestionRequest, EvaluateRequest


@router.post("/buddy/question")
async def buddy_question(body: QuestionRequest):
    """学伴提问：根据学习路径掌握度生成一个问题"""
    result = buddy_service.generate_question(
        student_id=body.student_id,
        path_id=body.path_id,
        focused_step_order=body.focused_step_order,
    )
    if result is None:
        raise HTTPException(status_code=400, detail="无法生成问题，请确保已选择包含知识点的学习路径")
    return result


@router.post("/buddy/evaluate")
async def buddy_evaluate(body: EvaluateRequest):
    """学伴评估：评估学生的回答，返回角色回复 + 学习笔记，并更新掌握度"""
    result = buddy_service.evaluate_answer(
        student_id=body.student_id,
        path_id=body.path_id,
        step_order=body.step_order,
        knowledge_point=body.knowledge_point,
        question=body.question,
        answer=body.answer,
        focused_step_order=body.focused_step_order,
    )
    if result is None:
        raise HTTPException(status_code=404, detail="未找到该学习路径")
    return result
