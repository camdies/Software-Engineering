# CLAUDE.md — 高校教务管理系统

> SCNU 软件工程小组 v3.0 · Claude 协作开发指引

## 项目身份

- **项目名称**: 高校教务管理系统 (EduMgmt System v3.0)
- **仓库**: 本地 Git，当前分支主分支 `main`
- **平台**: Windows 11 + PyCharm

## 规则索引

本项目使用 Claude Code Rules 体系管理开发约定。规则文件位于 `.claude/rules/` 目录：

| 规则文件 | 触发条件 | 内容 |
|----------|----------|------|
| `00-project-identity.md` | 始终加载 | 项目身份、文档索引 |
| `01-tech-stack.md` | 始终加载 | 技术栈速查、角色体系 |
| `02-common-commands.md` | 手动触发 | 启动、测试、数据库命令 |
| `03-backend-architecture.md` | `backend/**/*.py` | 后端分层、API规范、关键决策 |
| `04-frontend-architecture.md` | `frontend/**/*.{vue,js,scss}` | Vue组件、Pinia、路由规范 |
| `05-database.md` | `backend/models/**/*.py`, `*.sql` | 11张表结构、新增表流程 |
| `06-security.md` | 始终加载 | 6条不可违反的安全约束 |
| `07-development-scenarios.md` | 手动触发 | 选课逻辑、导出、调试指南 |
| `08-testing.md` | `tests/**/*.py` | Mock架构要点、测试约定 |

## 核心文档

- [ARCHITECTURE.md](ARCHITECTURE.md) — 124文件、48 API端点、11张表
- [API.md](API.md) — 完整 API 文档
- [DEBUG.md](DEBUG.md) — 调试指南
- [FRONTEND_GUIDE.md](FRONTEND_GUIDE.md) — 前端运行时说明
- [DEVELOPMENT.md](DEVELOPMENT.md) — 开发介绍
