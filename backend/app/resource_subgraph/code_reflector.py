"""
代码案例反思节点（code_reflector）
职责：验证生成的代码案例是否规范（JSON 格式 + 必要字段 + test_cases 格式），
      有格式错误则路由回 code_generator 重试。

验证规则面向 LeetCode 函数补全模式：
  - test_cases 使用 args/expected 格式
  - 必填字段：description, starter_code, solution, function_name
  - test_cases 至少 2 组，每组必须包含 expected
"""
import json
from app.resource_subgraph.state import ResourceSubState

MAX_RETRIES = 2


def code_reflector(state: ResourceSubState) -> dict:
    """验证代码案例质量，返回验证结果。"""
    resources = state.get("generated_resources", [])
    retry_count = state.get("code_retry_count", 0)

    print(f"\n[CodeReflector]  开始验证代码案例...")

    # 本轮是否有新生成的 code_example 资源
    code_resources = [r for r in resources if _get_type(r) == "code_example"]
    if not code_resources:
        print(f"[CodeReflector]  无代码案例资源，跳过验证")
        return {}

    latest = code_resources[-1]
    errors = _validate_code_example(latest.content)

    if not errors:
        print(f"[CodeReflector]  代码案例验证通过 ✓")
        return {
            "code_error_feedback": "",
            "code_invalid_resource_id": None,
        }

    # 验证失败
    if retry_count >= MAX_RETRIES:
        print(f"[CodeReflector]  已重试{retry_count}次，达到上限，接受当前结果")
        return {
            "code_error_feedback": "",
            "code_invalid_resource_id": None,
        }

    new_count = retry_count + 1
    feedback_str = "；".join(errors[:3])
    print(f"[CodeReflector]  验证失败 (第{new_count}次重试): {feedback_str}")

    return {
        "code_retry_count": new_count,
        "code_error_feedback": feedback_str,
        "code_invalid_resource_id": latest.id,
    }


def _validate_code_example(content: str) -> list[str]:
    """
    验证代码案例 JSON 格式（LeetCode 函数补全模式），返回错误列表。
    空列表 = 验证通过。
    """
    errors = []

    if not content or not content.strip():
        errors.append("代码案例内容为空")
        return errors

    try:
        data = json.loads(content)
    except json.JSONDecodeError as e:
        errors.append(f"JSON 解析失败: {e.msg}")
        return errors

    # 必填字段检查
    if not data.get("description"):
        errors.append("缺少 description（题目描述）")

    if not data.get("starter_code"):
        errors.append("缺少 starter_code（模板代码，函数签名 + 空函数体）")

    if not data.get("solution"):
        errors.append("缺少 solution（完整函数实现）")

    if not data.get("function_name"):
        errors.append("缺少 function_name（函数名）")

    # test_cases 验证（LeetCode 模式：args/expected 格式）
    test_cases = data.get("test_cases", [])
    if not isinstance(test_cases, list) or len(test_cases) == 0:
        errors.append("test_cases 至少需要 1 组测试用例")
    else:
        for i, tc in enumerate(test_cases):
            if not isinstance(tc, dict):
                errors.append(f"测试用例第{i+1}组不是 JSON 对象")
                continue
            # expected 是必填
            if "expected" not in tc:
                errors.append(f"测试用例第{i+1}组缺少 expected（期望返回值）")
            # args 应为数组，但单参数时可省略数组包裹
            if "args" in tc and not isinstance(tc["args"], list):
                errors.append(f"测试用例第{i+1}组的 args 必须是数组")

    hints = data.get("hints", [])
    if not isinstance(hints, list):
        errors.append("hints 必须是数组")

    lang = data.get("language", "")
    if lang and lang not in ("python",):
        errors.append(f"暂不支持的语言: {lang}（系统目前仅支持 Python）")

    return errors[:5]


def _get_type(r) -> str:
    """获取资源类型的字符串表示"""
    if hasattr(r, "type"):
        t = r.type
        return t.value if hasattr(t, "value") else str(t)
    return ""


def route_from_code_reflector(state: ResourceSubState) -> str:
    """路由决策：有 error_feedback 则重试，否则进 collector"""
    if state.get("code_error_feedback") and state.get("code_retry_count", 0) <= MAX_RETRIES:
        print(f"[Subgraph]   路由: code_reflector → code_generator (重试第{state['code_retry_count']}次)")
        return "code_generator"
    print(f"[Subgraph]   路由: code_reflector → safety_filter")
    return "safety_filter"
