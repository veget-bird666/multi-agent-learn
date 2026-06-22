from fastapi import APIRouter, HTTPException, Query
from sse_starlette.sse import EventSourceResponse
from app.models.user import ChatRequest
from app.graph.graph import learning_graph
from app.services.profile_service import profile_service
from app.services.resource_service import resource_service
from app.services.learning_path_service import learning_path_service
from langchain_community.chat_models import ChatTongyi
from langchain_core.messages import HumanMessage
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
    非流式运行整个 LangGraph 图，返回最终回复
    """
    try:
        # 构建完整的初始 state
        initial_state = {
            "history": [HumanMessage(content=request.message)],
            "operation": 0,
            "student_id": request.student_id,
            "message": request.message,
            "session_id": request.session_id,
            "profile": None,
            "current_agent": None,
            "next_agent": None,
            "next_reasoning": None,
            "profile_update_hint": None,
            "tool_result": None,
            "rewritten_query": None,
            "execution_plan": [],
            "current_plan_step": -1,
            "image_base64": None,
            "knowledge_point": None,
            "learning_path": None,
            "current_step": 0,
            "generated_resources": [],
            "teaching_decisions": [],
            "interaction_pattern": None,
            "response": None,
        }

        # 跑完整多智能体图
        final_state = await learning_graph.ainvoke(initial_state)

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

        return {
            "response": reply or "抱歉，我没有生成有效回复。",
            "profile": final_state.get("profile"),
            "resources": final_state.get("generated_resources", []),
            "learning_path": final_state.get("learning_path"),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"处理请求时出错: {str(e)}")


@router.get("/chat")
async def chat_stream(
    student_id: str = Query(..., description="学生 ID"),
    message: str = Query(..., description="用户消息"),
):
    """
    对话式学习入口（GET / SSE 流式）
    前端通过 EventSource 调用，直接与 LLM 对话
    """
    llm = ChatTongyi(model="qwen3-max", temperature=0.7)

    async def event_generator():
        try:
            async for chunk in llm.astream([HumanMessage(content=message)]):
                token = chunk.content
                if token:
                    yield {"event": "token", "data": json.dumps({"token": token})}

        except Exception as e:
            yield {"event": "error", "data": json.dumps({"error": str(e)})}
        finally:
            yield {"event": "end", "data": "[DONE]"}

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


@router.put("/learning-path/{path_id}/mastery/batch")
async def batch_update_mastery(path_id: int, updates: list[dict]):
    """批量更新多个阶段的掌握度"""
    result = learning_path_service.batch_update_mastery(path_id, updates)
    if result is None:
        raise HTTPException(status_code=404, detail="未找到该学习路径")
    return result


@router.delete("/learning-path/{path_id}")
async def delete_learning_path(path_id: int):
    """删除一条学习路径"""
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
