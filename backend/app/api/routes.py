from fastapi import APIRouter, HTTPException, Query
from sse_starlette.sse import EventSourceResponse
from app.models.user import ChatRequest
from app.graph.graph import learning_graph
from app.services.profile_service import profile_service
from app.services.resource_service import resource_service
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


@router.get("/learning-path/{student_id}")
async def get_learning_path(student_id: str):
    """获取学习路径"""
    # TODO: 从 PathAgent 获取
    return {"student_id": student_id, "path": None}


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
