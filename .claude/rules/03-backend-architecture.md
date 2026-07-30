---
description: 后端分层架构、API规范、关键设计决策——修改后端 Python 代码时必须遵守
alwaysApply: false
globs:
  - "backend/**/*.py"
  - "run.py"
version: 1.0.0
---

# 后端架构约定

## 分层（严格遵守）

```
Blueprint (路由，只做参数提取+调用Controller)
  → Controller (业务逻辑，不要处理request直接量)
    → Model (SQLAlchemy ORM，通过 DatabaseManager.get_session() 获取会话)
```

- **路由层**: `backend/api/blueprints/` — 9个蓝图，48个端点，只做参数提取和调用 controller
- **业务层**: `backend/controllers/` — 7个控制器，每个负责一个领域的业务逻辑
- **数据层**: `backend/models/` — 11个 ORM 模型 + `base.py` DatabaseManager 单例
- **工具层**: `backend/utils/` — 密码哈希、Excel导出、GPA计算、日志、校验

## 关键架构决策（不要违背）

1. **延迟数据库初始化**: `app_factory.py` 用 `@before_request` 懒初始化，不要在模块顶层访问 DB
2. **JWT 固定密钥**: `auth.py` 优先读 `config.ini` 中的 `jwt_secret`，否则 SHA256 生成
3. **选课并发**: 使用 `SELECT ... FOR UPDATE` 行级锁，不要用应用层锁
4. **状态列用 String(10)** 而非 SAEnum（兼容 SQL Server 无原生 ENUM）

## API 规范

- **URL 前缀**: `/api/<角色或模块>/`
- **鉴权**: JWT Bearer token（`Authorization: Bearer <token>`）
- **响应格式**: `{ "success": bool, "data": any, "message": "..." }`
- **装饰器**: `@require_auth` + `@require_role('admin'|'teacher'|'student')`
- **详细文档**: 见 [API.md](API.md)

## 新增 API 端点流程

1. 在对应 Blueprint 文件添加路由函数 → 调用 Controller 方法
2. 在对应 Controller 添加业务方法 → 返回字典
3. 更新 [API.md](API.md) 文档
4. 如需鉴权变更，在 `auth.py` 确认角色
