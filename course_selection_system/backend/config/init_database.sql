-- ================================================================
-- 学生选课及成绩管理系统 - SQL Server 2025 DDL 初始化脚本
-- 数据库: CourseManagementDB | 排序规则: Chinese_PRC_CI_AS
-- 使用 SSMS 2022 连接后执行此脚本
-- ================================================================

-- 切换到 master 以创建新数据库
USE master;
GO

IF DB_ID('CourseManagementDB') IS NOT NULL
BEGIN
    ALTER DATABASE CourseManagementDB SET SINGLE_USER WITH ROLLBACK IMMEDIATE;
    DROP DATABASE CourseManagementDB;
END
GO

CREATE DATABASE CourseManagementDB COLLATE Chinese_PRC_CI_AS;
GO

USE CourseManagementDB;
GO

-- ================================================================
-- 按外键依赖顺序删表
-- ================================================================
IF OBJECT_ID('dbo.operation_log', 'U') IS NOT NULL DROP TABLE dbo.operation_log;
IF OBJECT_ID('dbo.grade', 'U') IS NOT NULL DROP TABLE dbo.grade;
IF OBJECT_ID('dbo.enrollment', 'U') IS NOT NULL DROP TABLE dbo.enrollment;
IF OBJECT_ID('dbo.course_plan', 'U') IS NOT NULL DROP TABLE dbo.course_plan;
IF OBJECT_ID('dbo.course', 'U') IS NOT NULL DROP TABLE dbo.course;
IF OBJECT_ID('dbo.teacher', 'U') IS NOT NULL DROP TABLE dbo.teacher;
IF OBJECT_ID('dbo.student', 'U') IS NOT NULL DROP TABLE dbo.student;
IF OBJECT_ID('dbo.user_account', 'U') IS NOT NULL DROP TABLE dbo.user_account;
GO

-- ================================================================
-- 1. user_account — 用户账号表
-- ================================================================
CREATE TABLE dbo.user_account (
    user_id         NVARCHAR(20)   NOT NULL,
    password_hash   NVARCHAR(255)  NOT NULL,
    role            NVARCHAR(10)   NOT NULL
                    CONSTRAINT CK_user_account_role
                    CHECK (role IN ('admin','teacher','student')),
    last_login      DATETIME2(0)   NULL,
    is_locked       TINYINT        NOT NULL DEFAULT 0,
    login_fail_count INT           NOT NULL DEFAULT 0,
    created_at      DATETIME2(0)   NOT NULL DEFAULT SYSDATETIME(),
    CONSTRAINT PK_user_account PRIMARY KEY CLUSTERED (user_id)
);
GO

-- ================================================================
-- 2. student — 学生信息表
-- ================================================================
CREATE TABLE dbo.student (
    student_id  NVARCHAR(20)  NOT NULL,
    name        NVARCHAR(50)  NOT NULL,
    major       NVARCHAR(100) NULL,
    class_name  NVARCHAR(50)  NULL,
    contact     NVARCHAR(20)  NULL,
    created_at  DATETIME2(0)  NOT NULL DEFAULT SYSDATETIME(),
    CONSTRAINT PK_student PRIMARY KEY CLUSTERED (student_id),
    CONSTRAINT FK_student_user FOREIGN KEY (student_id)
        REFERENCES dbo.user_account(user_id)
        ON DELETE CASCADE ON UPDATE CASCADE
);
GO

-- ================================================================
-- 3. teacher — 教师信息表
-- ================================================================
CREATE TABLE dbo.teacher (
    teacher_id  NVARCHAR(20)  NOT NULL,
    name        NVARCHAR(50)  NOT NULL,
    college     NVARCHAR(100) NULL,
    contact     NVARCHAR(20)  NULL,
    created_at  DATETIME2(0)  NOT NULL DEFAULT SYSDATETIME(),
    CONSTRAINT PK_teacher PRIMARY KEY CLUSTERED (teacher_id),
    CONSTRAINT FK_teacher_user FOREIGN KEY (teacher_id)
        REFERENCES dbo.user_account(user_id)
        ON DELETE CASCADE ON UPDATE CASCADE
);
GO

-- ================================================================
-- 4. course — 课程信息表
-- ================================================================
CREATE TABLE dbo.course (
    course_id   NVARCHAR(20)  NOT NULL,
    course_name NVARCHAR(100) NOT NULL,
    credit      DECIMAL(3,1)  NULL,
    hours       INT           NULL,
    exam_type   NVARCHAR(10)  NULL
                CONSTRAINT CK_course_exam_type
                CHECK (exam_type IN (N'考试', N'考查')),
    created_at  DATETIME2(0)  NOT NULL DEFAULT SYSDATETIME(),
    CONSTRAINT PK_course PRIMARY KEY CLUSTERED (course_id)
);
GO

-- ================================================================
-- 5. course_plan — 开课计划表
-- ================================================================
CREATE TABLE dbo.course_plan (
    plan_id      INT            NOT NULL IDENTITY(1,1),
    course_id    NVARCHAR(20)   NOT NULL,
    teacher_id   NVARCHAR(20)   NOT NULL,
    semester     NVARCHAR(20)   NOT NULL,
    time_slot    NVARCHAR(50)   NULL,
    location     NVARCHAR(100)  NULL,
    capacity     INT            NULL,
    enrolled     INT            NOT NULL DEFAULT 0,
    prerequisite NVARCHAR(200)  NULL,
    status       NVARCHAR(10)   NOT NULL DEFAULT N'开课'
                 CONSTRAINT CK_course_plan_status
                 CHECK (status IN (N'开课', N'停课')),
    created_at   DATETIME2(0)   NOT NULL DEFAULT SYSDATETIME(),
    CONSTRAINT PK_course_plan PRIMARY KEY CLUSTERED (plan_id),
    CONSTRAINT FK_course_plan_course FOREIGN KEY (course_id)
        REFERENCES dbo.course(course_id),
    CONSTRAINT FK_course_plan_teacher FOREIGN KEY (teacher_id)
        REFERENCES dbo.teacher(teacher_id)
);
GO
CREATE NONCLUSTERED INDEX IX_course_plan_course_semester
    ON dbo.course_plan(course_id, semester);
GO

-- ================================================================
-- 6. enrollment — 选课记录表
-- ================================================================
CREATE TABLE dbo.enrollment (
    enroll_id   INT           NOT NULL IDENTITY(1,1),
    student_id  NVARCHAR(20)  NOT NULL,
    plan_id     INT           NOT NULL,
    enroll_time DATETIME2(0)  NOT NULL DEFAULT SYSDATETIME(),
    status      NVARCHAR(10)  NOT NULL DEFAULT N'已选'
                CONSTRAINT CK_enrollment_status
                CHECK (status IN (N'已选', N'已退')),
    created_at  DATETIME2(0)  NOT NULL DEFAULT SYSDATETIME(),
    CONSTRAINT PK_enrollment PRIMARY KEY CLUSTERED (enroll_id),
    CONSTRAINT UQ_enrollment_student_plan UNIQUE (student_id, plan_id),
    CONSTRAINT FK_enrollment_student FOREIGN KEY (student_id)
        REFERENCES dbo.student(student_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT FK_enrollment_plan FOREIGN KEY (plan_id)
        REFERENCES dbo.course_plan(plan_id)
);
GO

-- ================================================================
-- 7. grade — 成绩记录表
-- ================================================================
CREATE TABLE dbo.grade (
    grade_id      INT            NOT NULL IDENTITY(1,1),
    student_id    NVARCHAR(20)   NOT NULL,
    plan_id       INT            NOT NULL,
    score         INT            NULL,
    gpa_point     DECIMAL(3,2)   NULL,
    record_time   DATETIME2(0)   NULL DEFAULT SYSDATETIME(),
    status        NVARCHAR(10)   NOT NULL DEFAULT N'正常'
                  CONSTRAINT CK_grade_status
                  CHECK (status IN (N'正常', N'待审核', N'已更正')),
    modify_reason NVARCHAR(500)  NULL,
    created_at    DATETIME2(0)   NOT NULL DEFAULT SYSDATETIME(),
    CONSTRAINT PK_grade PRIMARY KEY CLUSTERED (grade_id),
    CONSTRAINT CK_grade_score CHECK (score >= 0 AND score <= 100),
    CONSTRAINT FK_grade_student FOREIGN KEY (student_id)
        REFERENCES dbo.student(student_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT FK_grade_plan FOREIGN KEY (plan_id)
        REFERENCES dbo.course_plan(plan_id)
);
GO
CREATE NONCLUSTERED INDEX IX_grade_student_plan
    ON dbo.grade(student_id, plan_id);
GO

-- ================================================================
-- 8. operation_log — 操作日志表
-- ================================================================
CREATE TABLE dbo.operation_log (
    log_id      INT            NOT NULL IDENTITY(1,1),
    user_id     NVARCHAR(20)   NOT NULL,
    log_type    NVARCHAR(10)   NOT NULL
                CONSTRAINT CK_log_type
                CHECK (log_type IN (N'登录', N'选课', N'成绩', N'系统')),
    operation   NVARCHAR(200)  NOT NULL,
    result      NVARCHAR(10)   NOT NULL
                CONSTRAINT CK_log_result
                CHECK (result IN (N'成功', N'失败')),
    log_time    DATETIME2(0)   NOT NULL DEFAULT SYSDATETIME(),
    ip_address  NVARCHAR(50)   NULL,
    created_at  DATETIME2(0)   NOT NULL DEFAULT SYSDATETIME(),
    CONSTRAINT PK_operation_log PRIMARY KEY CLUSTERED (log_id)
);
GO
CREATE NONCLUSTERED INDEX IX_log_user_time
    ON dbo.operation_log(user_id, log_time);
GO

-- ================================================================
-- 测试数据 — 密码均为 123456（bcrypt hash）
-- ================================================================

-- 管理员
INSERT INTO dbo.user_account (user_id, password_hash, role) VALUES
('admin', '$2b$12$WTsX7QBi/h9qL6KYxwwORuwVT0AYCVmJDcZr8C0/UhQPbrR2snNnS', 'admin');

-- 教师
INSERT INTO dbo.user_account (user_id, password_hash, role) VALUES
('T001', '$2b$12$WTsX7QBi/h9qL6KYxwwORuwVT0AYCVmJDcZr8C0/UhQPbrR2snNnS', 'teacher'),
('T002', '$2b$12$WTsX7QBi/h9qL6KYxwwORuwVT0AYCVmJDcZr8C0/UhQPbrR2snNnS', 'teacher');

INSERT INTO dbo.teacher (teacher_id, name, college) VALUES
('T001', N'张教授', N'计算机科学与技术学院'),
('T002', N'李副教授', N'数学与统计学院');

-- 学生
INSERT INTO dbo.user_account (user_id, password_hash, role) VALUES
('STU001', '$2b$12$WTsX7QBi/h9qL6KYxwwORuwVT0AYCVmJDcZr8C0/UhQPbrR2snNnS', 'student'),
('STU002', '$2b$12$WTsX7QBi/h9qL6KYxwwORuwVT0AYCVmJDcZr8C0/UhQPbrR2snNnS', 'student'),
('STU003', '$2b$12$WTsX7QBi/h9qL6KYxwwORuwVT0AYCVmJDcZr8C0/UhQPbrR2snNnS', 'student');

INSERT INTO dbo.student (student_id, name, major, class_name) VALUES
('STU001', N'王小明', N'计算机科学与技术', N'计科2101'),
('STU002', N'赵小红', N'软件工程',       N'软工2102'),
('STU003', N'刘小刚', N'数据科学',       N'数据2101');

-- 课程
INSERT INTO dbo.course (course_id, course_name, credit, hours, exam_type) VALUES
('CS100',   N'程序设计基础', 4.0, 64, N'考试'),
('CS101',   N'数据结构',     4.0, 64, N'考试'),
('CS201',   N'数据库原理',   3.0, 48, N'考试'),
('CS301',   N'软件工程',     3.0, 48, N'考查'),
('MATH101', N'高等数学',     5.0, 80, N'考试');

-- 开课计划
INSERT INTO dbo.course_plan (course_id, teacher_id, semester, time_slot, location, capacity, enrolled, prerequisite) VALUES
('CS100',   'T001', N'2026-2027-1', N'周一1-2节', N'教学楼A101', 30, 3, NULL),
('CS101',   'T001', N'2026-2027-1', N'周一3-4节', N'教学楼A201', 35, 0, N'CS100'),
('CS201',   'T001', N'2026-2027-1', N'周二1-2节', N'教学楼B101', 30, 2, N'CS100'),
('MATH101', 'T002', N'2026-2027-1', N'周三1-2节', N'教学楼C301', 50, 3, NULL),
('CS301',   'T001', N'2026-2027-1', N'周四5-6节', N'教学楼D101', 25, 0, N'CS101,CS201');

-- 选课记录
INSERT INTO dbo.enrollment (student_id, plan_id, status) VALUES
('STU001', 1, N'已选'), ('STU002', 1, N'已选'), ('STU003', 1, N'已选'),
('STU001', 3, N'已选'), ('STU002', 3, N'已选'),
('STU001', 4, N'已选'), ('STU002', 4, N'已选'), ('STU003', 4, N'已选');

GO
PRINT '===== 数据库 CourseManagementDB 初始化完成 =====';
GO
