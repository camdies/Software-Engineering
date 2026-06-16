# 数据库修复与重建指引

> 当 `operation_log` 等表的 CHECK 约束中文被污染（表现为登录成功但 400 错误、日志报 `CK_log_result is violated`），或网页中文显示为 `???`，按以下步骤重建。

## 根因说明

PowerShell 管道输出到外部程序时默认使用 ASCII 编码（由 `$OutputEncoding` 控制）。即使 `Get-Content -Encoding UTF8` 正确读取了 UTF-8 文件，管道传给 `mysql.exe` 时字符会被 ASCII 编码截断，中文字节丢失变成 `?`。

**所有** `Get-Content ... | mysql` 命令都必须先设置 `$OutputEncoding` 并加 `--default-character-set=utf8mb4`。

## 1. 确保 MySQL 在运行

如果安装了 Windows 服务：
```powershell
net start MySQL-EduMgmt
```
否则前台启动：
```powershell
cd "<项目目录>\mysql-portable"
.\bin\mysqld.exe --defaults-file="$PWD\my.ini" --console
```

## 2. 删掉旧库并重建

```powershell
cd "<项目目录>"

# 删除旧库
.\mysql-portable\bin\mysql.exe -u root -p你的密码 -e "DROP DATABASE IF EXISTS course_management_db;"

# 设置管道输出编码为 UTF-8，然后导入 DDL（两步缺一不可）
$OutputEncoding = [System.Text.UTF8Encoding]::new()
Get-Content backend\config\init_database_mysql.sql -Encoding UTF8 | .\mysql-portable\bin\mysql.exe -u root -p你的密码 --default-character-set=utf8mb4
```

> `$OutputEncoding` 确保管道以 UTF-8 传给 mysql.exe；`--default-character-set=utf8mb4` 确保 mysql 客户端以 utf8mb4 解析输入。

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
basedir=<项目目录>/mysql-portable
datadir=<项目目录>/mysql-portable/data
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

初始化数据目录（PowerShell，管理员）：
```powershell
cd "<项目目录>\mysql-portable"
.\bin\mysqld.exe --defaults-file="$PWD\my.ini" --initialize-insecure --console
```

安装为 Windows 服务（一劳永逸，管理员）：
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
