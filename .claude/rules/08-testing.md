---
description: 测试约定和 Mock 架构要点——编写或修改测试代码时必须遵守
alwaysApply: false
globs:
  - "tests/**/*.py"
version: 1.0.0
---

# 测试约定

所有测试使用 `unittest.TestCase` + `unittest.mock`，不使用 pytest 特有语法。

## Mock 架构要点（新增或修改测试时务必遵守）

1. `Settings` 必须在 **源定义位置** `backend.config.settings.Settings` 处 mock（不能 mock `enrollment_controller.Settings`，因为 Settings 已改为方法内延迟导入）
2. Mock `Settings` 时必须提供 `log_level="ERROR"` + `log_dir="logs"`，否则 `get_logger()` 在模块导入时崩溃
3. `Grade`, `Enrollment`, `OperationLog` 等 ORM 类必须在对应 controller 模块中 mock，防止 `__init__` 触发 SQLAlchemy mapper 配置
4. `_check_enrollment_period` 通过 `patch.object` 直接 mock，因为其内部有局部 DatabaseManager 导入，不经过模块级 mock
5. `session.query.return_value.filter_by.return_value.first` 用于 mock `query().filter_by().first()` 链；`session.query.return_value.filter.return_value.join.return_value.filter.return_value.first/all` 用于 mock `query().filter().join().filter()` 链（两者是不同的调用路径）
6. 并发测试中每个线程需独立创建 session mock，通过 `self._mock_session()` 复用 setUp 的 DatabaseManager mock
