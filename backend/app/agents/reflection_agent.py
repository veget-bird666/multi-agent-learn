"""
智能体7：学习效果评估
职责：读取学习路径中的 learning_logs，LLM 分析生成多维评估报告
（独立于主图使用，由评估页面手动触发）
"""
from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime
from langchain_core.prompts import ChatPromptTemplate
from app.graph.state import LearningState
from app.core.llm import chat_llm
from app.services.learning_path_service import learning_path_service


# ── 评估报告结构化输出 ─────────────────────────────────

class DimensionScore(BaseModel):
    """单个维度的评分 — 对应雷达图的一个轴"""
    name: str = Field(description="维度名称")
    score: float = Field(description="得分 0~100")
    detail: str = Field(description="该维度的具体分析（一两句话）")


class WeakPoint(BaseModel):
    """薄弱点"""
    knowledge_point: str = Field(description="知识点名称")
    stage_order: int = Field(description="所属阶段序号")
    mastery: float = Field(description="当前掌握度")
    error_pattern: str = Field(description="常见错误模式分析")
    suggestion: str = Field(description="巩固建议")


class EvaluationReport(BaseModel):
    """LLM 生成的评估报告（用于雷达图展示）"""

    # 雷达图 6 维度（同向 0~100，越高越好）
    overall_score: float = Field(description="综合评分 0~100（雷达图6维度的加权均值）")
    trend: str = Field(description="学习趋势：up/stable/down")
    dimension_scores: list[DimensionScore] = Field(
        description=(
            "雷达图6维度评分（name 必须为以下之一）：\n"
            "1. 知识掌握度 — 各知识点熟练度的加权均值\n"
            "2. 答题准确率 — 总体正确率\n"
            "3. 学习广度 — 已练习知识点占总知识点比例\n"
            "4. 掌握均衡度 — 各知识点间掌握度差异（差异越小分越高）\n"
            "5. 学习稳定性 — 正确率波动情况\n"
            "6. 挑战意愿 — 难题/挑战题目的参与度和表现"
        )
    )

    # 文本分析部分
    strengths: list[str] = Field(description="优势项列表（2~4条，每条约15字）")
    weak_points: list[WeakPoint] = Field(description="薄弱点列表（按严重程度排序）")
    at_risk_kps: list[str] = Field(description="需巩固的知识点（遗忘风险，每条约10字）")
    summary: str = Field(description="评估总结（2~3句话，约100字）")
    learning_suggestion: str = Field(description="针对性学习建议（含资源推荐和学习计划调整建议，约200字）")


# ── Prompt ────────────────────────────────────────────

SYSTEM_PROMPT = """你是一名 AI 学习分析师，负责评估学生的学习效果。

## 评估维度（雷达图6轴，每项 0~100 分，分值越高越好）

1. **知识掌握度** — 各知识点的熟练程度总体评价
   - 参考 signal: knowledge_point_mastery 综合值、阶段 mastery 均值
2. **答题准确率** — 总体正确率
   - 参考 signal: learning_logs 中 is_correct 占比
3. **学习广度** — 已练习知识点占路径总知识点的比例
   - 参考 signal: logs 覆盖的 kp 数 / 总 kp 数
4. **掌握均衡度** — 各知识点之间掌握度的差异程度
   - 参考 signal: knowledge_point_mastery 极差/方差，差异越小分数越高
5. **学习稳定性** — 正确率波动情况
   - 参考 signal: logs 按时间排序，连续答对/答错模式
6. **挑战意愿** — 对中高难度题目的参与度和表现
   - 参考 signal: 难题(difficulty=medium/hard) 的作答比例和正确率

## 评分要求
- 每个维度独立评分，基于数据
- 综合评分 = 6 维度均值（LLM 自行估算）
- 如果某个维度数据不足（如尚无难题作答记录），给一个保守分（40~60 之间）并说明

## 输出说明
- dimension_scores.name 必须使用上面6个中文名称
- weak_points 列出具体的薄弱知识点，指出错误模式
- at_risk_kps 列出掌握度不高或已有遗忘风险的 kp
- learning_suggestion 要具体可操作"""

USER_PROMPT = """请对以下学生的数据进行评估：

## 学习路径
名称：{path_title}
总体掌握度：{overall_mastery}%

## 各阶段详情
{stage_details}

## 学习日志明细
{learning_logs}

请生成评估报告。"""


# ── 日志格式化 ────────────────────────────────────────

def _format_logs(steps: list[dict]) -> str:
    """将 learning_logs 格式化为 LLM 易读的文本"""
    lines = []
    for step in steps:
        logs = step.get("learning_logs") or []
        if not logs:
            continue
        stage = step.get("stage_name", f"阶段{step.get('order')}")
        lines.append(f"\n【{stage}】")
        for log in logs:
            kp = log.get("kp", "")
            source = log.get("source", "")
            q = log.get("question", "")
            a = log.get("user_answer", "")
            correct = log.get("is_correct", False)
            inc = log.get("increment", 0)
            mb = log.get("mastery_before", 0)
            ma = log.get("mastery_after", 0)
            diff = log.get("difficulty", "?")
            icon = "✅" if correct else "❌"
            diff_label = {"easy": "简单", "medium": "中等", "hard": "困难"}.get(diff, diff)
            lines.append(f"  {icon} [{source}/{diff_label}] {kp} ({mb}→{ma}, +{inc})")
            if q:
                lines.append(f"    题: {q[:120]}")
            if a:
                lines.append(f"    答: {a[:120]}")
    return "\n".join(lines) if lines else "（暂无学习日志）"


def _format_stages(steps: list[dict]) -> str:
    """格式化各阶段掌握度"""
    lines = []
    for step in steps:
        order = step.get("order", "?")
        stage = step.get("stage_name", "")
        mastery = step.get("mastery", 0)
        kp_mastery: dict = step.get("knowledge_point_mastery") or {}
        kps: list = step.get("knowledge_points", [])
        kp_lines = []
        for kp in kps:
            m = kp_mastery.get(kp, 0)
            icon = "✅" if m >= 70 else ("🟡" if m >= 30 else "🔴")
            kp_lines.append(f"      {icon} {kp}: {round(m)}/120")
        lines.append(f"  阶段{order} {stage} — 掌握度 {round(mastery)}%")
        lines.extend(kp_lines)
    return "\n".join(lines)


# ── 统计数据（辅助 LLM，不依赖 LLM 计算） ─────────────

def _compute_statistics(steps: list[dict]) -> dict:
    """从 steps 中提取统计数据，供前端直接使用（不依赖 LLM）"""
    all_logs = []
    total_kps = set()
    covered_kps = set()

    for step in steps:
        for kp in step.get("knowledge_points", []):
            total_kps.add(kp)
        for log in step.get("learning_logs", []):
            all_logs.append(log)
            if log.get("kp"):
                covered_kps.add(log.get("kp"))

    total_questions = len(all_logs)
    correct_count = sum(1 for log in all_logs if log.get("is_correct"))

    # 按知识点统计
    kp_stats = {}
    for log in all_logs:
        kp = log.get("kp", "")
        if kp not in kp_stats:
            kp_stats[kp] = {"correct": 0, "total": 0, "mastery_values": []}
        kp_stats[kp]["total"] += 1
        if log.get("is_correct"):
            kp_stats[kp]["correct"] += 1

    # 各知识点当前掌握度
    kp_current_mastery = {}
    for step in steps:
        kp_m = step.get("knowledge_point_mastery") or {}
        for kp, m in kp_m.items():
            kp_current_mastery[kp] = m

    # 难度分布
    difficulty_stats = {"easy": {"total": 0, "correct": 0},
                        "medium": {"total": 0, "correct": 0},
                        "hard": {"total": 0, "correct": 0}}
    for log in all_logs:
        d = log.get("difficulty", "medium")
        if d not in difficulty_stats:
            difficulty_stats[d] = {"total": 0, "correct": 0}
        difficulty_stats[d]["total"] += 1
        if log.get("is_correct"):
            difficulty_stats[d]["correct"] += 1

    return {
        "total_questions": total_questions,
        "correct_count": correct_count,
        "accuracy": round(correct_count / total_questions * 100, 1) if total_questions > 0 else 0,
        "total_kps": len(total_kps),
        "covered_kps": len(covered_kps),
        "coverage": round(len(covered_kps) / len(total_kps) * 100, 1) if total_kps else 0,
        "kp_stats": kp_stats,
        "kp_current_mastery": kp_current_mastery,
        "difficulty_stats": difficulty_stats,
    }


# ── Agent 主函数 ─────────────────────────────────────

def reflection_agent(state: LearningState) -> dict:
    """
    评估学习效果，生成多维评估报告。
    读取指定学习路径的 learning_logs，用 LLM 分析并生成评估报告。
    """
    # 1. 获取学习路径
    current_path_id = state.get("current_path_id")
    if not current_path_id:
        return {
            "evaluation": None,
            "response": "请先选择一条学习路径。",
        }

    path = learning_path_service.get_by_id(current_path_id)
    if not path:
        return {
            "evaluation": None,
            "response": "学习路径不存在，无法进行评估。",
        }

    steps = path.get("steps", [])
    overall_mastery = path.get("overall_mastery", 0)
    title = path.get("title", "未命名路径")

    # 2. 检查是否有学习日志
    has_logs = any(step.get("learning_logs") for step in steps)

    if not has_logs:
        return {
            "evaluation": None,
            "response": "尚无足够的学习数据来进行评估。请先通过学伴答题或完成试卷来积累学习记录。",
        }

    # 3. 格式化数据
    stage_details = _format_stages(steps)
    learning_logs = _format_logs(steps)

    # 4. 调用 LLM 评估
    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        ("user", USER_PROMPT),
    ])
    chain = prompt | chat_llm.with_structured_output(EvaluationReport)

    try:
        report = chain.invoke({
            "path_title": title,
            "overall_mastery": overall_mastery,
            "stage_details": stage_details,
            "learning_logs": learning_logs,
        })
    except Exception as e:
        print(f"[Reflection]  LLM 评估出错: {e}")
        return {
            "evaluation": None,
            "response": f"评估过程出现错误: {str(e)[:100]}",
        }

    # 5. 统计数据（前端雷达图的数据锚点 + LLM 评分的交叉验证）
    stats = _compute_statistics(steps)
    stats["overall_mastery"] = overall_mastery

    # 6. 拼装结果
    report_dict = report.model_dump() if hasattr(report, "model_dump") else dict(report)
    report_dict["evaluated_at"] = datetime.now().isoformat(timespec="seconds")
    report_dict["path_id"] = current_path_id
    report_dict["statistics"] = stats  # 附带客观统计数据

    # 生成文本回复
    response_parts = [
        f"📊 **学习评估报告**\n",
        f"综合评分：{report.overall_score}/100 | 趋势：{'📈' if report.trend == 'up' else '📉' if report.trend == 'down' else '➡️'}",
        f"\n**各维度评分：**",
    ]
    for ds in report.dimension_scores:
        response_parts.append(f"- {ds.name}：{ds.score}/100 — {ds.detail}")

    response_parts.append(f"\n**优势：**")
    for s in report.strengths:
        response_parts.append(f"- ✅ {s}")

    if report.weak_points:
        response_parts.append(f"\n**薄弱点（需加强）：**")
        for wp in report.weak_points:
            response_parts.append(f"- 🔴 {wp.knowledge_point}（掌握度 {wp.mastery}%）")
            response_parts.append(f"  常见错误：{wp.error_pattern}")
            response_parts.append(f"  建议：{wp.suggestion}")

    if report.at_risk_kps:
        response_parts.append(f"\n**需巩固的知识点：**")
        for kp in report.at_risk_kps:
            response_parts.append(f"- ⚠️ {kp}")

    response_parts.append(f"\n**总结：**\n{report.summary}")
    response_parts.append(f"\n**学习建议：**\n{report.learning_suggestion}")

    print(f"[Reflection]  评估完成: 综合评分={report.overall_score}/100, 趋势={report.trend}")

    return {
        "evaluation": report_dict,
        "response": "\n".join(response_parts),
    }
