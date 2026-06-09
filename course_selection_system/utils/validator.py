"""
validator.py - 输入数据校验工具

提供系统各模块通用的输入校验函数，
每个函数返回 (bool, str) 元组，bool表示是否通过，str为错误原因。
"""

import re


def validate_student_id(student_id: str) -> tuple:
    """校验学号格式。

    规则: 非空，长度6-20位，由字母数字组成。

    Args:
        student_id: 待校验的学号字符串。

    Returns:
        tuple: (是否合法, 错误原因)
    """
    if not student_id or not student_id.strip():
        return False, "学号不能为空"
    student_id = student_id.strip()
    if len(student_id) < 6 or len(student_id) > 20:
        return False, "学号长度应为6-20位"
    if not re.match(r'^[A-Za-z0-9]+$', student_id):
        return False, "学号只能包含字母和数字"
    return True, ""


def validate_score(score) -> tuple:
    """校验成绩是否在0-100的整数范围内。

    Args:
        score: 待校验的成绩值（支持int、float、数字字符串）。

    Returns:
        tuple: (是否合法, 错误原因)
    """
    if score is None:
        return False, "成绩不能为空"
    try:
        s = int(score)
    except (ValueError, TypeError):
        return False, "成绩必须为有效整数"
    if s < 0 or s > 100:
        return False, "成绩必须在0-100之间"
    return True, ""


def validate_password(password: str) -> tuple:
    """校验密码强度。

    规则: 长度不少于6位。

    Args:
        password: 待校验的密码字符串。

    Returns:
        tuple: (是否合法, 错误原因)
    """
    if not password:
        return False, "密码不能为空"
    if len(password) < 6:
        return False, "密码长度不能少于6位"
    return True, ""


def validate_contact(contact: str) -> tuple:
    """校验联系方式格式。

    规则: 中国大陆手机号（1开头11位数字）或座机号格式。

    Args:
        contact: 待校验的联系方式字符串。

    Returns:
        tuple: (是否合法, 错误原因)
    """
    if not contact or not contact.strip():
        return False, "联系方式不能为空"
    contact = contact.strip()
    # 中国大陆手机号格式：1开头11位纯数字
    if re.match(r'^1\d{10}$', contact):
        return True, ""
    # 座机格式：区号-号码
    if re.match(r'^\d{3,4}-\d{7,8}$', contact):
        return True, ""
    return False, "联系方式格式不正确（手机号: 1开头11位数字，座机: 区号-号码）"


def validate_credit(credit) -> tuple:
    """校验学分是否在有效范围内。

    规则: 0.5-20之间，步进0.5。

    Args:
        credit: 待校验的学分值。

    Returns:
        tuple: (是否合法, 错误原因)
    """
    if credit is None:
        return False, "学分不能为空"
    try:
        c = float(credit)
    except (ValueError, TypeError):
        return False, "学分必须为有效数字"
    if c < 0.5 or c > 20:
        return False, "学分必须在0.5-20之间"
    # 校验是否为0.5的倍数
    if (c * 2) % 1 != 0:
        return False, "学分必须以0.5为步进"
    return True, ""


def validate_not_empty(value, field_name: str = "") -> tuple:
    """校验值是否非空。

    Args:
        value: 待校验的值（支持 str/list）。
        field_name: 字段名称，用于错误提示。

    Returns:
        tuple: (是否合法, 错误原因)
    """
    label = field_name or "字段"
    if value is None:
        return False, f"{label}不能为空"
    if isinstance(value, str) and not value.strip():
        return False, f"{label}不能为空"
    if isinstance(value, (list, tuple, dict)) and len(value) == 0:
        return False, f"{label}不能为空"
    return True, ""
