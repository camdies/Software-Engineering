"""
tests - 单元测试目录

使用unittest框架，包含：
- test_auth: 登录认证测试
- test_enrollment: 选课核心逻辑测试（含并发测试）
- test_grade: 成绩管理测试（含边界值、绩点计算测试）

测试使用unittest.mock模拟数据库连接，测试数据与生产数据严格隔离。
"""
