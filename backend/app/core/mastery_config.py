"""
熟练度更新配置 — 集中管理所有场景的增量得分规则

用法：
    from app.core.mastery_config import get_buddy_increment, get_exam_increment

修改这里即可全局生效，无需改业务代码。
"""

# ═══════════════════════════════════════════════════════════
#  全局系数 —— 最终分数 = 原始分数 × 该系数
#  设为 2.0 则所有得分翻倍，设为 0.5 则减半
# ═══════════════════════════════════════════════════════════
MASTERY_MULTIPLIER = 3.0

# ═══════════════════════════════════════════════════════════
#  学伴问答：按当前掌握度分档
#  掌握度越低答对奖励越高，帮助学生快速补弱
# ═══════════════════════════════════════════════════════════
# 格式：(最低掌握度, 最高掌握度, 答对增量)
BUDDY_MASTERY_BRACKETS = [
    (0, 20, 12),     # 基础薄弱 → 答对 +12（大幅提升）
    (20, 50, 8),     # 有一定了解 → +8
    (50, 70, 5),     # 较好掌握 → +5
    (70, 101, 3),    # 熟练掌握 → +3（挑战）
]

# ═══════════════════════════════════════════════════════════
#  试卷答题：按题目难度分档
# ═══════════════════════════════════════════════════════════
EXAM_DIFFICULTY_MAP = {
    "easy": 5,
    "medium": 8,
    "hard": 12,
}

# ═══════════════════════════════════════════════════════════
#  代码实操练习：按题目难度分档
# ═══════════════════════════════════════════════════════════
CODE_PRACTICE_DIFFICULTY_MAP = {
    "easy": 5,
    "medium": 8,
    "hard": 12,
}


# ═══════════════════════════════════════════════════════════
#  辅助函数
# ═══════════════════════════════════════════════════════════


def get_buddy_increment(mastery: float) -> int:
    """根据当前掌握度返回答对后的学伴增量（已乘全局系数）"""
    for lo, hi, inc in BUDDY_MASTERY_BRACKETS:
        if lo <= mastery < hi:
            return max(1, round(inc * MASTERY_MULTIPLIER))
    return max(1, round(5 * MASTERY_MULTIPLIER))  # 兜底


def get_exam_increment(difficulty: str) -> int:
    """根据题目难度返回试卷答对增量（已乘全局系数）"""
    base = EXAM_DIFFICULTY_MAP.get(difficulty, 5)
    return max(1, round(base * MASTERY_MULTIPLIER))


def get_code_increment(difficulty: str) -> int:
    """根据题目难度返回代码练习答对增量（已乘全局系数）"""
    base = CODE_PRACTICE_DIFFICULTY_MAP.get(difficulty, 5)
    return max(1, round(base * MASTERY_MULTIPLIER))
