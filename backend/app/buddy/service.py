"""
虚拟学伴核心服务 — 掌握度驱动的自适应提问 + 双层输出评估

设计理念：
  - 学伴角色扮演"水平略低的同学"，对话回复可含糊，不直接说对错
  - 学习笔记提供精准知识点，保证学习效果不打折
  - 掌握度越低答对奖励越高，帮助学生快速补弱
"""
from typing import Optional

from langchain_core.prompts import ChatPromptTemplate

from app.core.llm import chat_llm
from app.core.mastery_config import get_buddy_increment
from app.services.learning_path_service import learning_path_service
from app.buddy.schemas import BuddyQuestion, BuddyEvaluation


# ── 路径上下文格式化 ─────────────────────────────────

def _mastery_icon(m: float) -> str:
    if m >= 70: return "✅"
    if m >= 30: return "🟡"
    if m >= 1:  return "🔴"
    return "⚪"


def _format_path_context(path: dict, current_step_order: Optional[int] = None) -> str:
    """
    生成完整的路径上下文文本，包含路径概览和当前阶段详情。

    Args:
        path: 学习路径 dict
        current_step_order: 当前所在阶段序号（可为 None）

    Returns:
        格式化后的上下文文本，供 LLM prompt 使用
    """
    steps = path.get("steps", [])
    title = path.get("title", "未命名路径")
    overall = path.get("overall_mastery", 0)

    lines = []
    lines.append(f"📚 路径名称：{title}（{len(steps)} 个阶段，总体掌握度 {overall}%）")
    lines.append("")

    # 路径概览
    for step in steps:
        order = step.get("order", "?")
        name = step.get("stage_name", "")
        m = step.get("mastery", 0)
        marker = " ← 当前" if order == current_step_order else ""
        lines.append(f"  阶段{order}：{name}  掌握度 {round(m)}%  {_mastery_icon(m)}{marker}")

    lines.append("")

    # 当前阶段详情
    for step in steps:
        if step.get("order") != current_step_order:
            continue
        name = step.get("stage_name", "")
        desc = step.get("description", "")
        kp_mastery: dict = step.get("knowledge_point_mastery") or {}
        kps: list = step.get("knowledge_points", [])

        lines.append(f"📖 当前阶段：{name}")
        if desc:
            lines.append(f"  描述：{desc}")
        if kps:
            lines.append("  知识点掌握度：")
            for kp in kps:
                m = kp_mastery.get(kp, 0)
                lines.append(f"    - {kp}：{round(m)}/100  {_mastery_icon(m)}")
        break

    return "\n".join(lines)


# ── Prompt 模板 ──

QUESTION_SYSTEM_PROMPT = """你是一个虚拟学习伙伴，名叫"小问"。你的知识水平比学生略低，经常需要向学生请教问题。

## 你的任务
根据学生当前对某个知识点的掌握程度，提出一个合适的问题，让学生"教你"。

## 掌握度与提问策略
- **低于20%（基础薄弱）**：问最基础的概念性问题，如"能给我讲讲XX是什么吗？我从零开始不太懂"
- **20%-50%（有一定了解）**：问理解应用类问题，如"XX和YY有什么区别？"或"XX在实际中怎么用？"
- **50%-70%（较好掌握）**：问综合/深度问题，如"为什么XX是这样工作的？能深入讲讲吗？"
- **高于70%（基本掌握）**：问进阶挑战问题，如"我听说XX还有一种高级用法，你知道吗？"

## 输出要求
- question：以"小问"的口吻提问，语气谦虚、好奇
- knowledge_point：对应的知识点名称
- difficulty：easy / medium / hard"""

QUESTION_USER_PROMPT = """当前知识点：{knowledge_point}
当前掌握度：{mastery}/100
所属阶段：{stage_name}
阶段描述：{stage_description}
该阶段知识点：{all_kps}

{path_context}

请根据以上信息，以小问的身份提出一个适当难度的问题。"""


EVALUATE_SYSTEM_PROMPT = """你是一个虚拟学习伙伴，名叫"小问"。你的知识水平比学生略低。

## 你的任务
学生正在"教你"一个知识点。你需要做以下几件事：

### 1. response（角色扮演回复）
以小问的身份回复学生，角色扮演"似懂非懂"的感觉。
- 答对时：说"好像明白了"、"原来是这样"等，但不直接说"你对"
- 答错时：说"感觉有点怪怪的"、"我还是不太明白"等，不直接说"你错了"
- 保持谦虚、好奇的口吻

### 2. learning_note（学习笔记）
生成一份精准的学习笔记（Markdown格式），包含：
- 📌 知识点概述
- ✅ 正确理解（核心概念）
- ❌ 常见误区（如果适用）
- 💡 关键要点 / 记忆技巧

### 3. is_correct（对错判断）
判断学生回答是否正确（宽松标准，核心概念对了就算对）。

### 4. follow_up_question（跟进追问 — 重要：默认不留！）
**默认不留空，只有极少数情况才需要追问。**

✅ 需要追问的唯一场景：
- 学生答错了，而且你知道一个**更基础的角度**可以帮助 TA 理解

❌ 不需要追问的场景（即 follow_up_question 必须留空）：
- 学生答对了 → 不论掌握度多低，都不追问
- 学生答对了一半 → 不追问
- 可以深入讲解 → 不追问，学习笔记里写清楚即可
- 掌握度偏低 → 不追问，用户下次会再练到

记住：**追问是例外，不是常态**。大部分情况下 follow_up_question 应该留空。

### 5. follow_up_kp（跟进知识点）
跟进问题对应的知识点名称，默认和当前知识点相同。"""

EVALUATE_USER_PROMPT = """背景信息：
问题：{question}
知识点：{knowledge_point}
当前掌握度：{mastery_before}/100
所属阶段：{stage_name}
阶段描述：{stage_description}

{path_context}

学生回答：{answer}

请评估学生的回答，生成学伴回复和学习笔记。需要继续追问时填写 follow_up_question。"""


class BuddyService:
    """虚拟学伴服务"""

    # ── 问题生成 ────────────────────────────────────────

    def generate_question(
        self,
        student_id: str,
        path_id: int,
        focused_step_order: Optional[int] = None,
    ) -> Optional[dict]:
        """
        根据学习路径掌握度，生成学伴提问。

        参数:
            focused_step_order: 聚焦的步骤序号，None 则从全部阶段中选

        返回:
            { question, knowledge_point, step_order, difficulty, mastery_before }
            或 None（无可用知识点时）
        """
        # 1. 获取学习路径数据
        path = learning_path_service.get_by_id(path_id)
        if not path:
            return None

        steps = path.get("steps", [])
        if not steps:
            return None

        # 2. 收集知识点
        candidates = []
        for step in steps:
            # 如果聚焦了某个阶段，只取该阶段的
            if focused_step_order is not None and step.get("order") != focused_step_order:
                continue
            kp_mastery: dict = step.get("knowledge_point_mastery") or {}
            kps: list = step.get("knowledge_points", [])
            for kp in kps:
                mastery = kp_mastery.get(kp, 0.0)
                candidates.append({
                    "kp": kp,
                    "mastery": mastery,
                    "step_order": step.get("order"),
                    "stage_name": step.get("stage_name", ""),
                    "stage_description": step.get("description", ""),
                    "all_kps": ", ".join(kps),
                })

        if not candidates:
            return None

        # 按掌握度升序排列，挑最薄弱的
        candidates.sort(key=lambda c: c["mastery"])
        target = candidates[0]

        # 构建路径上下文
        path_context = _format_path_context(path, target["step_order"])

        # 3. LLM 生成问题
        prompt = ChatPromptTemplate.from_messages([
            ("system", QUESTION_SYSTEM_PROMPT),
            ("user", QUESTION_USER_PROMPT),
        ])
        chain = prompt | chat_llm.with_structured_output(BuddyQuestion)
        result = chain.invoke({
            "knowledge_point": target["kp"],
            "mastery": round(target["mastery"]),
            "stage_name": target["stage_name"],
            "stage_description": target["stage_description"],
            "all_kps": target["all_kps"],
            "path_context": path_context,
        })

        print(f"[Buddy]  提问: [{target['kp']}](阶段{target['step_order']}, 掌握度{round(target['mastery'])}) → {result.question[:60]}")

        # result.kp 在 with_structured_output 下可能不存在
        kp_out = getattr(result, 'kp', None) or target["kp"]

        return {
            "question": result.question,
            "knowledge_point": kp_out,
            "step_order": target["step_order"],
            "difficulty": result.difficulty,
            "mastery_before": round(target["mastery"], 1),
        }

    # ── 答案评估 ────────────────────────────────────────

    def evaluate_answer(
        self,
        student_id: str,
        path_id: int,
        step_order: Optional[int] = None,
        knowledge_point: str = "",
        question: str = "",
        answer: str = "",
        focused_step_order: Optional[int] = None,
    ) -> Optional[dict]:
        """
        评估学生答案，更新掌握度。

        返回:
            { response, learning_note, is_correct, difficulty, mastery_before, mastery_after, increment }
            或 None（路径不存在时）
        """
        # 1. 获取路径数据，查当前掌握度
        path = learning_path_service.get_by_id(path_id)
        if not path:
            return None

        steps = path.get("steps", [])
        mastery_before = 0.0
        stage_name = ""
        stage_description = ""

        # 如果没传 step_order，从所有步骤中找包含该知识点的阶段
        if step_order is None and knowledge_point:
            for step in steps:
                kps = step.get("knowledge_points", [])
                if knowledge_point in kps:
                    step_order = step.get("order")
                    break

        current_step_order = focused_step_order or step_order

        for step in steps:
            if step.get("order") == step_order:
                kp_mastery: dict = step.get("knowledge_point_mastery") or {}
                mastery_before = kp_mastery.get(knowledge_point, 0.0)
                stage_name = step.get("stage_name", "")
                stage_description = step.get("description", "")
                break

        # 构建路径上下文
        path_context = _format_path_context(path, current_step_order)

        # 2. LLM 评估
        prompt = ChatPromptTemplate.from_messages([
            ("system", EVALUATE_SYSTEM_PROMPT),
            ("user", EVALUATE_USER_PROMPT),
        ])
        chain = prompt | chat_llm.with_structured_output(BuddyEvaluation)
        result = chain.invoke({
            "question": question,
            "knowledge_point": knowledge_point,
            "mastery_before": round(mastery_before),
            "stage_name": stage_name,
            "stage_description": stage_description,
            "path_context": path_context,
            "answer": answer,
        })

        # 3. 更新掌握度 + 记录学习日志
        from datetime import datetime
        increment = 0
        if result.is_correct:
            increment = get_buddy_increment(mastery_before)

        mastery_after = mastery_before + increment
        if mastery_after > 120:
            mastery_after = 120.0

        log_entry = {
            "kp": knowledge_point,
            "source": "buddy",
            "difficulty": result.difficulty or "medium",
            "question": question,
            "user_answer": answer,
            "is_correct": result.is_correct,
            "increment": increment,
            "mastery_before": round(mastery_before, 1),
            "mastery_after": round(mastery_after, 1),
            "timestamp": datetime.now().isoformat(timespec="seconds"),
        }
        if not result.is_correct:
            log_entry["error_detail"] = ""  # LLM 评估结果中可后续提取具体错误

        learning_path_service.update_kp_mastery(
            path_id, step_order, knowledge_point, increment, log_entry=log_entry,
        )

        # 4. 处理跟进问题
        follow_up = None
        if result.follow_up_question:
            follow_up_kp = result.follow_up_kp or knowledge_point
            follow_mastery = mastery_before
            if follow_up_kp != knowledge_point:
                for step in steps:
                    kp_m = (step.get("knowledge_point_mastery") or {}).get(follow_up_kp, 0.0)
                    if kp_m:
                        follow_mastery = kp_m
                        break
            follow_up = {
                "question": result.follow_up_question,
                "knowledge_point": follow_up_kp,
                "step_order": step_order,
                "mastery_before": round(follow_mastery, 1),
            }
            print(f"[Buddy]  跟进追问: [{follow_up_kp}] → {result.follow_up_question[:60]}")
        else:
            print(f"[Buddy]  话题结束，可点击'换个知识点'")

        print(
            f"[Buddy]  评估: [{knowledge_point}] "
            f"{'✅' if result.is_correct else '❌'} "
            f"{mastery_before} → {mastery_after} (增量+{increment})"
        )

        return {
            "response": result.response,
            "learning_note": result.learning_note,
            "is_correct": result.is_correct,
            "difficulty": result.difficulty,
            "mastery_before": round(mastery_before, 1),
            "mastery_after": round(mastery_after, 1),
            "increment": increment,
            "follow_up": follow_up,
        }
