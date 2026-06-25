"""
试卷反思节点（exam_reflector）
职责：验证生成的试卷是否符合规范，有格式错误则路由回 exam_generator 重试。
"""
import json
from app.models.resources import Resource
from app.resource_subgraph.state import ResourceSubState

MAX_RETRIES = 2


def exam_reflector(state: ResourceSubState) -> dict:
    """
    验证试卷质量，返回验证结果。
    如果验证失败且未达重试上限，清空无效试卷并设置反馈，让路由回到 exam_generator。
    """
    resources = state.get("generated_resources", [])
    retry_count = state.get("exam_retry_count", 0)
    error_feedback = state.get("exam_error_feedback", "")

    print(f"\n[ExamReflector]  开始验证试卷...")

    # 本轮是否有新生成的 exam 资源
    exam_resources = [r for r in resources if _get_type(r) == "exam"]
    if not exam_resources:
        print(f"[ExamReflector]  无试卷资源，跳过验证")
        return {}

    latest_exam = exam_resources[-1]
    exam_content = latest_exam.content
    errors = _validate_exam(exam_content)

    if not errors:
        print(f"[ExamReflector]  试卷验证通过 ✓")
        return {
            "exam_error_feedback": "",
            "exam_invalid_resource_id": None,
        }

    # 验证失败
    if retry_count >= MAX_RETRIES:
        print(f"[ExamReflector]  已重试{retry_count}次，达到上限，接受当前结果")
        return {
            "exam_error_feedback": "",
            "exam_invalid_resource_id": None,
        }

    # 需要重试
    new_count = retry_count + 1
    feedback_str = "；".join(errors[:3])  # 最多反馈3个问题
    print(f"[ExamReflector]  验证失败 (第{new_count}次重试): {feedback_str}")

    return {
        "exam_retry_count": new_count,
        "exam_error_feedback": feedback_str,
        "exam_invalid_resource_id": latest_exam.id,
    }


def _validate_exam(content: str) -> list[str]:
    """
    验证试卷 JSON 格式，返回错误列表。
    空列表 = 验证通过。
    """
    errors = []

    if not content or not content.strip():
        errors.append("试卷内容为空")
        return errors

    # 1. 解析 JSON
    try:
        data = json.loads(content)
    except json.JSONDecodeError as e:
        errors.append(f"JSON 解析失败: {e.msg}")
        return errors

    # 2. 必须有 questions 数组
    questions = data.get("questions")
    if not isinstance(questions, list):
        errors.append("缺少 questions 数组")
        return errors

    if len(questions) == 0:
        errors.append("questions 数组为空")
        return errors

    # 3. 检查每道题
    for i, q in enumerate(questions):
        prefix = f"第{i+1}题"
        if not isinstance(q, dict):
            errors.append(f"{prefix}不是 JSON 对象")
            continue

        q_type = q.get("type")
        if q_type not in ("choice", "fill", "short_answer"):
            errors.append(f"{prefix}无效的 type: '{q_type}'")

        if not q.get("question"):
            errors.append(f"{prefix}缺少 question 字段")

        if not q.get("answer"):
            errors.append(f"{prefix}缺少 answer 字段")

        difficulty = q.get("difficulty")
        if difficulty not in ("easy", "medium", "hard"):
            errors.append(f"{prefix}无效的 difficulty: '{difficulty}'")

        # 选择题必须有 options
        if q_type == "choice":
            options = q.get("options")
            if not isinstance(options, list) or len(options) < 2:
                errors.append(f"{prefix}选择题至少需要2个选项")

    # 限制返回错误数量，避免反馈信息过长
    return errors[:5]


def _get_type(r) -> str:
    """获取资源类型的字符串表示"""
    if hasattr(r, "type"):
        t = r.type
        return t.value if hasattr(t, "value") else str(t)
    return ""


def route_from_exam_reflector(state: ResourceSubState) -> str:
    """路由决策：有 error_feedback 则重试，否则进 collector"""
    if state.get("exam_error_feedback") and state.get("exam_retry_count", 0) <= MAX_RETRIES:
        print(f"[Subgraph]   路由: exam_reflector → exam_generator (重试第{state['exam_retry_count']}次)")
        return "exam_generator"
    print(f"[Subgraph]   路由: exam_reflector → safety_filter")
    return "safety_filter"
