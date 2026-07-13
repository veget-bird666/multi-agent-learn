"""
代码案例生成器（code_generator）
职责：LLM 生成 JSON 格式的代码实操案例（LeetCode 函数补全模式）。
      学生只需补全函数体，测试系统通过调用函数 + 对比返回值自动评判。

生成的 JSON 结构：
{
  "language": "python",
  "function_name": "two_sum",
  "description": "实现一个函数...",
  "starter_code": "def two_sum(nums, target):\\n    pass",
  "test_cases": [
    {"args": [[2,7,11,15], 9], "expected": [0, 1]},
    {"args": [[3,2,4], 6], "expected": [1, 2]}
  ],
  "hints": ["提示1", "提示2"],
  "solution": "def two_sum(nums, target):\\n    ...",
  "explanation": "解题思路讲解..."
}
"""
import json
import time
from langchain_core.prompts import ChatPromptTemplate

from app.core.llm import chat_llm
from app.models.resources import Resource
from app.resource_subgraph.state import ResourceSubState


SYSTEM_PROMPT = """
你是一个专业的编程教学专家，擅长针对知识点设计 LeetCode 风格的函数补全练习题。

## 模式说明
采用「函数补全」模式，与 LeetCode 一致：
- 学生看到的是**函数签名 + 空实现**，只需补全函数体
- 测试系统通过调用函数、传参、对比返回值来评判
- **不需要** stdin/stdout 交互，一切通过函数参数和返回值完成

## 语言约定
使用 Python 语言，函数签名风格：
- Python: `def two_sum(nums, target):`

## JSON 输出格式
```json
{{"language": "python",
  "function_name": "two_sum",
  "title": "两数之和",
  "difficulty": "medium",
  "description": "题目描述（支持 Markdown）",
  "starter_code": "函数签名 + TODO 注释（学生在此基础上补全函数体）",
  "test_cases": [
    {{"args": [参数1, 参数2, ...], "expected": 期望返回值}},
    {{"args": [参数1, 参数2], "expected": 期望返回值}}
  ],
  "hints": ["渐进式提示1", "提示2"],
  "solution": "完整函数实现（包含函数签名 + 完整函数体）",
  "explanation": "解题思路讲解"}}
```

## 字段详解

### starter_code（模板代码）
- **只包含函数签名和空函数体**，不要包含 main、输入读取等额外代码
- 用 `# TODO` / `pass` / `// TODO` 标记让学生补全的部分
- 示例：`def reverse_string(s: str) -> str: ...`

### solution（参考答案）
- **只包含完整的函数实现**（函数签名 + 函数体），不要包含 main 或测试代码
- 必须是**可运行**的实现，能正确处理所有 test_cases
- 需与 starter_code 的函数签名完全一致

### test_cases（测试用例）
每个用例是一个对象：
- `args`: 数组，每个元素对应一个函数参数（按位置传参）
- `expected`: 该用例的期望返回值

示例：
```json
[
  {{"args": [[2, 7, 11, 15], 9], "expected": [0, 1]}},
  {{"args": [[3, 2, 4], 6], "expected": [1, 2]}},
  {{"args": [[3, 3], 6], "expected": [0, 1]}}
]
```

测试运行方式：测试系统将 args 解包传给函数，再对比返回值。

## 设计要求
1. 案例有实际意义，能体现知识点的核心应用
2. 难度适中：easy=基础语法，medium=综合运用，hard=算法/设计
3. 测试用例至少 2 组，覆盖正常输入 + 边界情况
4. 防幻觉：代码必须可运行，不要使用不存在的库或函数
5. 函数名使用 snake_case，见名知意
"""


def code_generator(state: ResourceSubState) -> dict:
    """生成 JSON 格式的 LeetCode 风格函数补全案例。"""
    import time
    _start = time.time()

    knowledge_point = state.get("knowledge_point", "")
    profile = state.get("profile")
    rewritten = state.get("rewritten_query", "")
    cleaned_topic = state.get("cleaned_topic", "")

    # ── 学习路径上下文 ──
    path_id = state.get("path_id")
    step_order = state.get("step_order")
    step_kps = state.get("step_knowledge_points", [])

    topic = cleaned_topic or rewritten or knowledge_point
    if not topic:
        print(f"[CodeGenerator]  无知识点，跳过")
        return {"generated_resources": []}

    print(f"\n[CodeGenerator]  开始生成代码案例: {topic}")
    if step_order is not None:
        print(f"[CodeGenerator]   绑定路径阶段: step={step_order}, KPs={step_kps}")

    # ── 接收反思重试的反馈 ──
    error_feedback = state.get("code_error_feedback", "")
    if error_feedback:
        print(f"[CodeGenerator]  收到反思反馈，重试生成: {error_feedback}")

    # ── 难度估计 ──
    difficulty = _estimate_difficulty(profile)

    # ── 构建 prompt ──
    if step_order is not None and step_kps:
        kp_list = "、".join(step_kps)
        user_prompt = (
            f"请严格围绕以下学习阶段的内容生成代码实操案例：\n"
            f"阶段：第{step_order}阶段 — {topic}\n"
            f"知识点范围：{kp_list}\n"
            f"难度级别：{difficulty}\n"
            f"请生成一个函数补全模式的代码案例 JSON。"
        )
    else:
        user_prompt = (
            f"请为知识点「{topic}」生成一个函数补全模式的代码案例。\n"
            f"难度级别：{difficulty}\n"
        )

    if error_feedback:
        user_prompt += (
            f"\n\n上次生成存在以下问题，请修正：\n{error_feedback}"
        )

    # ── 直接发消息，绕过模板解析 ──
    from langchain_core.messages import SystemMessage, HumanMessage
    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=user_prompt),
    ]

    print(f"[CodeGenerator]  准备调用 LLM (已耗时 {time.time()-_start:.1f}s)...")
    try:
        _t0 = time.time()
        result = chat_llm.invoke(messages)
        _t1 = time.time()
        print(f"[CodeGenerator]  LLM 返回 (耗时 {_t1-_t0:.1f}s), content 长度={len(result.content)}")
        content = result.content.strip()

        # 清理可能的 markdown 代码块标记
        if content.startswith("```"):
            content = content.split("\n", 1)[1] if "\n" in content else content
            content = content.rsplit("```", 1)[0].strip()
            if content.startswith("json"):
                content = content[4:].strip()

        # 验证合法 JSON
        parsed = json.loads(content)

        # 补全缺少的字段
        if "title" not in parsed:
            parsed["title"] = f"{topic} 代码练习"
        if "language" not in parsed:
            parsed["language"] = "python"  # 固定 Python
        if "function_name" not in parsed:
            parsed["function_name"] = "solution"
        if "test_cases" not in parsed or not parsed["test_cases"]:
            parsed["test_cases"] = [{"args": [], "expected": None}]
        if "hints" not in parsed:
            parsed["hints"] = []
        if "explanation" not in parsed:
            parsed["explanation"] = ""
        content = json.dumps(parsed, ensure_ascii=False, indent=2)

        resource = Resource(
            id=f"code_{int(time.time())}",
            type="code_example",
            title=parsed.get("title", f"{topic} 代码练习"),
            content=content,
            knowledge_point=knowledge_point or topic,
            difficulty=difficulty,
            path_id=path_id,
            step_order=step_order,
        )
        print(f"[CodeGenerator]  代码案例生成完成: {parsed.get('title')} ({parsed.get('language')})")
        return {"generated_resources": [resource]}

    except json.JSONDecodeError as e:
        print(f"[CodeGenerator]  JSON 解析失败: {e}")
        resource = Resource(
            id=f"code_fallback_{int(time.time())}",
            type="code_example",
            title=f"{topic} 代码练习",
            content=result.content,
            knowledge_point=knowledge_point or topic,
            difficulty=difficulty,
            path_id=path_id,
            step_order=step_order,
        )
        return {"generated_resources": [resource]}
    except Exception as e:
        print(f"[CodeGenerator]  生成失败: {e}")
        return {"generated_resources": []}


def _estimate_difficulty(profile) -> str:
    """根据知识基础估算案例难度。"""
    if not profile or not profile.knowledge_base:
        return "medium"
    kb = profile.knowledge_base.lower()
    if any(k in kb for k in ["零基础", "入门", "初级", "较差"]):
        return "easy"
    if any(k in kb for k in ["高级", "深入", "熟练"]):
        return "hard"
    return "medium"
