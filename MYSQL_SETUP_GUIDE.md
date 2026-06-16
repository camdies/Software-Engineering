# 数据库修复与重建指引

> 当网页中文显示为 `???`、操作日志 CHECK 约束被破坏、或需要重置数据库时，按以下步骤操作。

## 根因

PowerShell 管道输出到外部程序时默认使用 ASCII 编码（由 `$OutputEncoding` 控制）。即使 `Get-Content -Encoding UTF8` 正确读取了 UTF-8 文件，管道传给 `mysql.exe` 时刻会被 ASCII 编码截断，中文变成 `?`。

**解决方案**：所有 `Get-Content ... | mysql` 命令前先设置 `$OutputEncoding` 并加 `--default-character-set=utf8mb4`。

## 1. 确保 MySQL 在运行

- **前台模式（推荐）**：`server_control.bat` → `[F]`（无需管理员）
- **服务模式**：`server_control.bat` → `[D]`（需管理员，右键→以管理员身份运行）
- **独立启动**：双击 `mysql-portable\start_mysql.bat`

## 2. 删掉旧库并重建

```powershell
cd "<项目目录>"

# 删除旧库
.\mysql-portable\bin\mysql.exe -u root -p你的密码 -e "DROP DATABASE IF EXISTS course_management_db;"

# 设置管道编码 + 导入 DDL（三步缺一不可）
$OutputEncoding = [System.Text.UTF8Encoding]::new()
Get-Content backend\config\init_database_mysql.sql -Encoding UTF8 | .\mysql-portable\bin\mysql.exe -u root -p你的密码 --default-character-set=utf8mb4
```

## 3. 验证

```powershell
.\mysql-portable\bin\mysql.exe -u root -p你的密码 -e "USE course_management_db; SHOW TABLES; SELECT student_id, name FROM student LIMIT 3;"
```

输出 11 张表 + 学生姓名正常显示中文（王小明、赵小红、刘小刚）即成功。

## 4. 后续：每次导入 SQL 务必设置管道编码

```powershell
# 正确（三步缺一不可）
$OutputEncoding = [System.Text.UTF8Encoding]::new()
Get-Content xxx.sql -Encoding UTF8 | .\mysql-portable\bin\mysql.exe -u root -p密码 --default-character-set=utf8mb4

# 错误（会毁掉中文）
Get-Content xxx.sql | .\mysql-portable\bin\mysql.exe -u root -p密码
Get-Content xxx.sql -Encoding UTF8 | .\mysql-portable\bin\mysql.exe -u root -p密码
```

## 5. 首次安装参考

MySQL 8.0 ZIP 免安装版（[下载](https://dev.mysql.com/downloads/mysql/)），解压到项目根目录命名为 `mysql-portable`。在 `mysql-portable\` 下创建 `my.ini`：

```ini
[mysqld]
basedir=CURRENT_DIR
datadir=CURRENT_DIR/data
port=3306
character-set-server=utf8mb4
collation-server=utf8mb4_unicode_ci
default-storage-engine=INNODB
max_connections=50

[client]
port=3306
default-character-set=utf8mb4

[mysql]
default-character-set=utf8mb4
```

> `CURRENT_DIR` 会被 `start_mysql.bat` 或 `server_control.bat` 自动替换为实际路径。无需手动修改。

初始化数据目录（PowerShell，管理员）：
```powershell
cd "<项目目录>\mysql-portable"
.\bin\mysqld.exe --defaults-file="$PWD\my.ini" --initialize-insecure --console
```

安装为 Windows 服务（可选，需管理员）：
```powershell
cd "<项目目录>\mysql-portable"
.\bin\mysqld.exe --install MySQL-EduMgmt --defaults-file="$PWD\my.ini"
net start MySQL-EduMgmt
sc config MySQL-EduMgmt start=auto
```

首次登录设密码：
```powershell
.\bin\mysql.exe -u root
# 在 mysql> 中执行：
# ALTER USER 'root'@'localhost' IDENTIFIED BY '你的密码';
# FLUSH PRIVILEGES;
# EXIT;
```

然后按上方第 2 步导入 DDL 即可。

## 6. 迁移到另一台电脑

1. 打包分发：`server_control.bat` → `[7]` 生成包含完整环境的 zip
2. 伙伴解压后双击 `start_all.bat` → 自动生成路径、启动 MySQL、启动 Flask
3. 如果只需迁移数据：复制 `mysql-portable\data\course_management_db\` 到目标机器的同一路径下
