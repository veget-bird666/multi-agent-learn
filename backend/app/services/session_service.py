"""
多轮对话状态持久化服务 — 将跨轮次的关键 state 字段存到 SQLite。

每次对话完成后调用 save()，下次请求时 load() 恢复，保证 Agent
能拿到完整的对话历史、画像、路径等上下文。

序列化说明：
  - history:       LangChain BaseMessage → list[{"role", "content"}]
  - profile:       StudentProfile → dict（Pydantic model_dump）
  - resources:     List[Resource] → list[dict]
  - decisions:     List[TeachingDecision] → list[dict]
  - 其余字段:       JSON 原生类型，直接存储
"""
import json
from datetime import datetime
from typing import Optional

from app.database.base import get_session
from app.database.models import SessionStateORM
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage

# ── 工具函数：LangChain Message 序列化 ─────────────────────

ROLE_MAP = {
    "human": HumanMessage,
    "ai": AIMessage,
    "system": SystemMessage,
}


def _serialize_history(history: list) -> list[dict]:
    """BaseMessage → list[{"role": str, "content": str}]"""
    if not history:
        return []
    return [{"role": msg.type, "content": msg.content} for msg in history]


def _deserialize_history(data: list) -> list[BaseMessage]:
    """list[dict] → BaseMessage 列表"""
    if not data:
        return []
    result = []
    for item in data:
        role = item.get("role", "human")
        content = item.get("content", "")
        cls = ROLE_MAP.get(role, HumanMessage)
        result.append(cls(content=content))
    return result


# ── 哪些字段需要跨轮次持久化 ──────────────────────────────

PERSIST_FIELDS = [
    "history",              # 对话历史
    "profile",              # 学生画像（StudentProfile 对象）
    "knowledge_point",      # 当前知识点
    "learning_path",        # 学习路径（list[dict]）
    "current_path_id",      # 当前路径 ID
    "current_step",         # 当前步骤
    "focused_step_order",   # 聚焦阶段
    "generated_resources",  # 已生成的资源列表
    "teaching_decisions",   # 教学决策记录
    "interaction_pattern",  # 交互模式分析
]

# 非持久化字段：每次请求都重新初始化的临时运行态
EPHEMERAL_DEFAULTS = {
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
}


# ── Service ────────────────────────────────────────────────

class SessionService:
    """多轮对话状态持久化"""

    # ── 公开接口 ───────────────────────────────────────────

    def save(self, session_id: str, student_id: str, state: dict) -> None:
        """
        将 state 中的持久化字段序列化后存入 SQLite。

        调用时机：每次图执行完毕后。
        新会话自动生成标题（LLM 摘要）。
        """
        payload = {}
        for field in PERSIST_FIELDS:
            val = state.get(field)
            if val is None:
                continue
            payload[field] = self._serialize(field, val)

        now = datetime.now().isoformat(timespec="seconds")
        state_json = json.dumps(payload, ensure_ascii=False, default=str)

        with get_session() as session:
            orm = session.query(SessionStateORM).filter_by(
                session_id=session_id
            ).first()
            if orm:
                orm.state_json = state_json
                orm.updated_at = now
                # 空标题时自动生成
                if not orm.title:
                    title = self._auto_generate_title(state, orm.state_json)
                    if title:
                        orm.title = title
            else:
                # 初次保存：自动生成标题
                title = self._auto_generate_title(state, state_json)
                session.add(SessionStateORM(
                    session_id=session_id,
                    student_id=student_id,
                    state_json=state_json,
                    title=title or "",
                    created_at=now,
                    updated_at=now,
                ))
            session.commit()

    def load(self, session_id: str) -> Optional[dict]:
        """
        从 SQLite 恢复持久化的 state 字段。

        返回 dict（包含反序列化后的 PERSIST_FIELDS），
        或 None（该 session 不存在）。
        """
        with get_session() as session:
            orm = session.query(SessionStateORM).filter_by(
                session_id=session_id
            ).first()
            if not orm:
                return None

        payload = json.loads(orm.state_json)
        state = {}
        for field in PERSIST_FIELDS:
            val = payload.get(field)
            if val is not None:
                state[field] = self._deserialize(field, val)
        return state

    def list_by_student(self, student_id: str) -> list[dict]:
        """
        查询某个学生全部会话的摘要列表。

        返回按 updated_at 降序排列的列表：
          [{session_id, title, created_at, updated_at}, ...]
        """
        with get_session() as session:
            orms = session.query(SessionStateORM).filter_by(
                student_id=student_id
            ).order_by(SessionStateORM.updated_at.desc()).all()

        result = []
        for orm in orms:
            title = orm.title or self._extract_title(orm.state_json)
            result.append({
                "session_id": orm.session_id,
                "title": title,
                "created_at": orm.created_at,
                "updated_at": orm.updated_at,
            })
        return result

    def get_title(self, session_id: str) -> Optional[str]:
        """获取某个会话的标题（如有）。"""
        with get_session() as session:
            orm = session.query(SessionStateORM).filter_by(
                session_id=session_id
            ).first()
            if not orm:
                return None
            return orm.title or self._extract_title(orm.state_json)

    def update_title(self, session_id: str, title: str) -> bool:
        """
        手动更新某个会话的标题。
        返回 True 表示更新成功，False 表示会话不存在。
        """
        if len(title) > 256:
            title = title[:256]
        with get_session() as session:
            orm = session.query(SessionStateORM).filter_by(
                session_id=session_id
            ).first()
            if not orm:
                return False
            orm.title = title
            orm.updated_at = datetime.now().isoformat(timespec="seconds")
            session.commit()
            return True

    def get_messages(self, session_id: str) -> list:
        """
        获取某个会话的历史消息列表（用于前端展示）。
        返回 list[BaseMessage]（由路由层做 JSON 序列化）。
        """
        with get_session() as session:
            orm = session.query(SessionStateORM).filter_by(
                session_id=session_id
            ).first()
            if not orm:
                return []

        try:
            payload = json.loads(orm.state_json)
            history = payload.get("history", [])
            return _deserialize_history(history) if history else []
        except Exception:
            return []

    def delete(self, session_id: str) -> bool:
        """删除某个会话的历史状态。"""
        with get_session() as session:
            orm = session.query(SessionStateORM).filter_by(
                session_id=session_id
            ).first()
            if not orm:
                return False
            session.delete(orm)
            session.commit()
            return True

    # ── 序列化 / 反序列化 ──────────────────────────────────

    @staticmethod
    def _auto_generate_title(state: dict, state_json: str) -> str:
        """
        根据对话历史自动生成简洁标题（利用 LLM）。
        返回空字符串表示生成失败。
        """
        try:
            payload = json.loads(state_json)
            history = payload.get("history", [])
            if not history:
                return ""

            # 取前两轮对话（用户首条 + AI 首条回复）作为摘要素材
            user_msgs = [h for h in history if h.get("role") == "human"]
            if not user_msgs:
                return ""
            first_user = user_msgs[0].get("content", "")[:200]

            # 如果只有一句话，直接用前 30 字
            if len(first_user) < 15:
                return first_user

            # 用 LLM 生成简洁标题
            try:
                from app.core.llm import chat_llm
                from langchain_core.prompts import ChatPromptTemplate

                prompt = ChatPromptTemplate.from_messages([
                    ("system", "你是一个对话标题生成器。根据用户的第一条消息，生成一个简洁的对话标题（5-20字），直接返回标题，不要任何解释。"),
                    ("user", "{message}"),
                ])
                chain = prompt | chat_llm
                response = chain.invoke({"message": first_user})
                title = response.content.strip().strip('"').strip("'").strip("《》")

                # 限制长度
                if 2 <= len(title) <= 60:
                    return title
            except Exception:
                pass

            # 兜底：取首条消息前 40 字
            return first_user[:40]
        except Exception:
            return ""

    @staticmethod
    def _extract_title(state_json: str) -> str:
        """从持久化的 state_json 中提取会话标题（第一条用户消息）。"""
        try:
            payload = json.loads(state_json)
            history = payload.get("history", [])
            if history:
                first = history[0]
                if isinstance(first, dict) and first.get("role") == "human":
                    content = first.get("content", "")
                    return content[:60] if content else "新对话"
        except Exception:
            pass
        return "新对话"

    @staticmethod
    def _serialize(field: str, val):
        if field == "history":
            return _serialize_history(val)
        if field == "profile":
            return val.model_dump() if hasattr(val, "model_dump") else val
        if field in ("generated_resources", "teaching_decisions"):
            if val and hasattr(val[0], "model_dump"):
                return [v.model_dump() for v in val]
            return val
        return val

    @staticmethod
    def _deserialize(field: str, val):
        if field == "history":
            return _deserialize_history(val)
        if field == "profile":
            if val:
                from app.models.user import StudentProfile
                return StudentProfile(**val)
            return None
        if field == "generated_resources":
            if val:
                from app.models.resources import Resource
                return [Resource(**v) for v in val]
            return []
        if field == "teaching_decisions":
            if val:
                from app.models.resources import TeachingDecision
                return [TeachingDecision(**v) for v in val]
            return []
        return val


# 全局单例
session_service = SessionService()
