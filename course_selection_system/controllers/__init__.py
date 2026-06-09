"""
controllers - 业务逻辑控制层（C层）

负责系统核心业务逻辑处理，包括：
- auth_controller: 登录认证与会话管理
- admin_controller: 管理员业务（用户管理、课程管理等）
- teacher_controller: 教师业务（成绩录入、统计分析）
- student_controller: 学生业务（选课、查成绩）
- enrollment_controller: 选课核心逻辑（含并发控制）
- grade_controller: 成绩管理（录入、审核、修正）
- stats_controller: 统计分析（成绩统计、报表导出）

所有控制器方法的数据库操作均使用事务控制与异常处理。
"""
