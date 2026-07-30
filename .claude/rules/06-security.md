---
description: 安全约束——任何时候都必须遵守的不可违反规则
alwaysApply: true
version: 1.0.0
---

# 安全约束（绝对不要做的）

1. 不要在前端硬编码 JWT secret 或数据库密码
2. 不要跳过 `@require_auth` 或 `@require_role` 装饰器
3. 不要使用字符串拼接构造 SQL（始终用 SQLAlchemy ORM）
4. 不要在前端直接将用户输入拼接到 HTML（Vue 默认转义，但 v-html 需审查）
5. 密码必须经过 bcrypt（12轮）哈希，后端工具 `auth_util.py`
6. 配置文件 `config.ini` 不要提交到 Git
