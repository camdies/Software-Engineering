# 选课系统 Course Selection System

> SCNU 软件工程小组项目

## 技术栈

| 层级 | 技术 |
|------|------|
| 应用层 | Python / PySide6 / Tkinter |
| 数据访问 | SQLAlchemy / pyodbc / pymssql |
| 数据库 | SQL Server |

---

## 环境要求

- Python 3.11+
- pip
- SQL Server（配置见 [SQL_SERVER_SETUP_GUIDE.md](./SQL_SERVER_SETUP_GUIDE.md)）

---

## 快速开始

### 1. 克隆仓库

```powershell
git clone https://github.com/camdies/Software-Engineering.git
cd Software-Engineering\course_selection_system
```

### 2. 配置数据库

请先参考 [SQL_SERVER_SETUP_GUIDE.md](./SQL_SERVER_SETUP_GUIDE.md) 完成 SQL Server 配置。

### 3. 一键安装并启动

```powershell
.\start.ps1
```

> 若提示执行策略限制，先运行一次：
> ```powershell
> Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
> ```

### 4. 手动启动（可选）

```powershell
# 安装依赖
pip install -r requirements.txt

# 启动 PySide6 界面
python run_pyside6.py

# 或启动 Tkinter 界面
python run_tkinter.py
```

---

## 前端界面

本项目提供两种桌面前端，**任选其一**运行即可：

### PySide6（推荐）

```powershell
python run_pyside6.py
```

### Tkinter

```powershell
python run_tkinter.py
```

---

## 项目结构

```
course_selection_system/
├── backend/              # Django 后端
├── frontend_pyside6/     # PySide6 桌面前端
├── frontend_tkinter/     # Tkinter 桌面前端
├── docs/                 # 项目文档
├── tests/                # 测试用例
├── requirements.txt      # Python 依赖
├── run_pyside6.py        # PySide6 启动入口
├── run_tkinter.py        # Tkinter 启动入口
├── start.ps1             # 一键启动脚本
└── SQL_SERVER_SETUP_GUIDE.md  # 数据库配置指南
```

---

## 常见问题

**Q: `requirements.txt` 报编码错误？**

```powershell
git checkout HEAD -- requirements.txt
```

**Q: SQL Server 连接失败？**

请检查 `backend` 目录下的数据库配置文件，确认连接字符串与本地 SQL Server 实例名一致。

---

## 许可证

[AGPL-3.0](../LICENSE)