"""
gpa_calculator.py - 绩点计算工具

提供百分制成绩到绩点(GPA)的转换，以及累计平均绩点的计算。
严格按照绩点映射规则：90-100→4.0, 85-89→3.7, 80-84→3.3, ... 0-59→0.0
"""

from utils.log_util import get_logger

logger = get_logger("gpa_calculator")

# 绩点映射表：(最低分, 最高分, 绩点)
_GPA_RULES = [
    (90, 100, 4.0),
    (85, 89, 3.7),
    (80, 84, 3.3),
    (75, 79, 3.0),
    (70, 74, 2.7),
    (65, 69, 2.3),
    (60, 64, 2.0),
    (0, 59, 0.0),
]


def calculate_gpa(score: int) -> float:
    """根据百分制成绩计算对应绩点。

    Args:
        score: 百分制成绩（0-100的整数）。

    Returns:
        float: 对应绩点值。

    Raises:
        ValueError: score不在0-100范围内时抛出。
    """
    if not isinstance(score, int) or score < 0 or score > 100:
        logger.error(f"无效的成绩值: {score}")
        raise ValueError(f"成绩必须在0-100之间，收到: {score}")
    for low, high, gpa in _GPA_RULES:
        if low <= score <= high:
            return gpa
    return 0.0


def calculate_cumulative_gpa(grade_list: list) -> float:
    """计算累计平均绩点。

    公式: Σ(gpa × credit) / Σ(credit)

    Args:
        grade_list: 成绩列表，每项为dict，需包含 'gpa_point' 和 'credit' 键。

    Returns:
        float: 累计平均绩点，保留2位小数。若无有效学分则返回0.0。
    """
    if not grade_list:
        logger.warning("grade_list为空，返回累计绩点0.0")
        return 0.0
    total_weighted = 0.0
    total_credits = 0.0
    for item in grade_list:
        gpa = item.get("gpa_point", 0.0)
        credit = item.get("credit", 0.0)
        try:
            gpa = float(gpa)
            credit = float(credit)
        except (ValueError, TypeError):
            logger.warning(f"无效的绩点/学分数据: {item}")
            continue
        total_weighted += gpa * credit
        total_credits += credit
    if total_credits == 0:
        return 0.0
    return round(total_weighted / total_credits, 2)
