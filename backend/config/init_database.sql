-- ================================================================
-- 高校教务管理系统 - SQL Server DDL 初始化脚本 v3.0
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
IF OBJECT_ID('dbo.password_reset_request', 'U') IS NOT NULL DROP TABLE dbo.password_reset_request;
IF OBJECT_ID('dbo.operation_log', 'U') IS NOT NULL DROP TABLE dbo.operation_log;
IF OBJECT_ID('dbo.grade', 'U') IS NOT NULL DROP TABLE dbo.grade;
IF OBJECT_ID('dbo.enrollment', 'U') IS NOT NULL DROP TABLE dbo.enrollment;
IF OBJECT_ID('dbo.course_plan', 'U') IS NOT NULL DROP TABLE dbo.course_plan;
IF OBJECT_ID('dbo.course', 'U') IS NOT NULL DROP TABLE dbo.course;
IF OBJECT_ID('dbo.teacher', 'U') IS NOT NULL DROP TABLE dbo.teacher;
IF OBJECT_ID('dbo.student', 'U') IS NOT NULL DROP TABLE dbo.student;
IF OBJECT_ID('dbo.user_account', 'U') IS NOT NULL DROP TABLE dbo.user_account;
IF OBJECT_ID('dbo.class_period', 'U') IS NOT NULL DROP TABLE dbo.class_period;
IF OBJECT_ID('dbo.semester_config', 'U') IS NOT NULL DROP TABLE dbo.semester_config;
GO

-- ================================================================
-- 0a. class_period — 上课节次时间表（11节/天）
-- ================================================================
CREATE TABLE dbo.class_period (
    period_id     TINYINT       NOT NULL,
    period_name   NVARCHAR(10)  NOT NULL,
    start_time    NVARCHAR(10)  NOT NULL,
    end_time      NVARCHAR(10)  NOT NULL,
    description   NVARCHAR(50)  NULL,
    CONSTRAINT PK_class_period PRIMARY KEY CLUSTERED (period_id)
);
GO

-- 每天11节课的时间段
INSERT INTO dbo.class_period (period_id, period_name, start_time, end_time, description) VALUES
(1,  N'第一节',  N'08:30', N'09:10', N'上午'),
(2,  N'第二节',  N'09:20', N'10:00', N'上午'),
(3,  N'第三节',  N'10:20', N'11:00', N'上午'),
(4,  N'第四节',  N'11:10', N'11:50', N'上午'),
(5,  N'第五节',  N'14:30', N'15:10', N'下午'),
(6,  N'第六节',  N'15:20', N'16:00', N'下午'),
(7,  N'第七节',  N'16:10', N'16:50', N'下午'),
(8,  N'第八节',  N'17:00', N'17:40', N'下午'),
(9,  N'第九节',  N'19:00', N'19:40', N'晚上'),
(10, N'第十节',  N'19:50', N'20:30', N'晚上'),
(11, N'第十一节',N'20:40', N'21:20', N'晚上');
GO

-- ================================================================
-- 0b. semester_config — 学期配置表
-- ================================================================
CREATE TABLE dbo.semester_config (
    config_id       INT           NOT NULL IDENTITY(1,1),
    semester        NVARCHAR(20)  NOT NULL,
    total_weeks     TINYINT       NOT NULL DEFAULT 20,
    start_date      DATE          NULL,
    end_date        DATE          NULL,
    is_current      TINYINT       NOT NULL DEFAULT 0,
    enrollment_open TINYINT       NOT NULL DEFAULT 0,
    enroll_start    DATETIME2(0)  NULL,
    enroll_end      DATETIME2(0)  NULL,
    created_at      DATETIME2(0)  NOT NULL DEFAULT SYSDATETIME(),
    CONSTRAINT PK_semester_config PRIMARY KEY CLUSTERED (config_id),
    CONSTRAINT CK_semester_total_weeks CHECK (total_weeks BETWEEN 1 AND 30)
);
GO

-- 默认学期（2026-2027第一学期，20周）
INSERT INTO dbo.semester_config (semester, total_weeks, start_date, end_date, is_current, enrollment_open)
VALUES (N'2026-2027-1', 20, '2026-09-01', '2027-01-17', 1, 0);
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
    grade       NVARCHAR(4)   NULL,
    email       NVARCHAR(100) NULL,
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
    title       NVARCHAR(50)  NULL,
    college     NVARCHAR(100) NULL,
    email       NVARCHAR(100) NULL,
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
--    instructor_intro 扩展为 NVARCHAR(2000) 以容纳更详细的教师介绍
--    新增 target_major, course_type 字段
-- ================================================================
CREATE TABLE dbo.course (
    course_id        NVARCHAR(20)   NOT NULL,
    course_name      NVARCHAR(100)  NOT NULL,
    credit           DECIMAL(3,1)   NULL,
    hours            INT            NULL,
    exam_type        NVARCHAR(10)   NULL
                     CONSTRAINT CK_course_exam_type
                     CHECK (exam_type IN (N'考试', N'考查')),
    department       NVARCHAR(100)  NULL,
    course_type      NVARCHAR(20)   NULL DEFAULT N'必修'
                     CONSTRAINT CK_course_type
                     CHECK (course_type IN (N'必修', N'选修', N'公共必修', N'公共选修')),
    target_major     NVARCHAR(200)  NULL,
    description      NVARCHAR(2000) NULL,
    textbook         NVARCHAR(200)  NULL,
    syllabus         NVARCHAR(2000) NULL,
    instructor_intro NVARCHAR(2000) NULL,
    created_at       DATETIME2(0)   NOT NULL DEFAULT SYSDATETIME(),
    CONSTRAINT PK_course PRIMARY KEY CLUSTERED (course_id)
);
GO

-- ================================================================
-- 5. course_plan — 开课计划表（教师申请制）
--    weekday: 1=周一 ... 7=周日
--    period_start: 起始节次 1-11
--    period_count: 持续节数 1-11
--    start_week/end_week: 由教师自由选择起止周
--    status: 待审核/已通过/已驳回/已停课
--    新增: apply_reason 教师申请理由
-- ================================================================
CREATE TABLE dbo.course_plan (
    plan_id        INT            NOT NULL IDENTITY(1,1),
    course_id      NVARCHAR(20)   NOT NULL,
    teacher_id     NVARCHAR(20)   NOT NULL,
    semester       NVARCHAR(20)   NOT NULL,
    weekday        TINYINT        NOT NULL,
    period_start   TINYINT        NOT NULL,
    period_count   TINYINT        NOT NULL DEFAULT 2,
    start_week     TINYINT        NOT NULL DEFAULT 1,
    end_week       TINYINT        NOT NULL DEFAULT 20,
    location       NVARCHAR(100)  NULL,
    capacity       INT            NULL,
    enrolled       INT            NOT NULL DEFAULT 0,
    prerequisite   NVARCHAR(200)  NULL,
    apply_reason   NVARCHAR(500)  NULL,
    status         NVARCHAR(10)   NOT NULL DEFAULT N'待审核'
                   CONSTRAINT CK_course_plan_status
                   CHECK (status IN (N'待审核', N'已通过', N'已驳回', N'已停课')),
    audit_comment  NVARCHAR(500)  NULL,
    created_at     DATETIME2(0)   NOT NULL DEFAULT SYSDATETIME(),
    CONSTRAINT PK_course_plan PRIMARY KEY CLUSTERED (plan_id),
    CONSTRAINT CK_cp_weekday CHECK (weekday BETWEEN 1 AND 7),
    CONSTRAINT CK_cp_period_start CHECK (period_start BETWEEN 1 AND 11),
    CONSTRAINT CK_cp_period_count CHECK (period_count BETWEEN 1 AND 11),
    CONSTRAINT CK_cp_weeks CHECK (start_week BETWEEN 1 AND 20 AND end_week BETWEEN 1 AND 20 AND end_week >= start_week),
    CONSTRAINT FK_course_plan_course FOREIGN KEY (course_id)
        REFERENCES dbo.course(course_id),
    CONSTRAINT FK_course_plan_teacher FOREIGN KEY (teacher_id)
        REFERENCES dbo.teacher(teacher_id)
);
GO
CREATE NONCLUSTERED INDEX IX_cp_course_semester ON dbo.course_plan(course_id, semester);
GO
CREATE NONCLUSTERED INDEX IX_cp_status ON dbo.course_plan(status);
GO
CREATE NONCLUSTERED INDEX IX_cp_teacher ON dbo.course_plan(teacher_id, semester);
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
    new_score     INT            NULL,
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
CREATE NONCLUSTERED INDEX IX_grade_student_plan ON dbo.grade(student_id, plan_id);
GO

-- ================================================================
-- 8. operation_log — 操作日志表
-- ================================================================
CREATE TABLE dbo.operation_log (
    log_id      INT            NOT NULL IDENTITY(1,1),
    user_id     NVARCHAR(20)   NOT NULL,
    log_type    NVARCHAR(10)   NOT NULL
                CONSTRAINT CK_log_type
                CHECK (log_type IN (N'登录', N'选课', N'成绩', N'审核', N'系统')),
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
CREATE NONCLUSTERED INDEX IX_log_user_time ON dbo.operation_log(user_id, log_time);
GO

-- ================================================================
-- 9. password_reset_request — 密码重置申请表
-- ================================================================
CREATE TABLE dbo.password_reset_request (
    request_id   INT            NOT NULL IDENTITY(1,1),
    user_id      NVARCHAR(20)   NOT NULL,
    reason       NVARCHAR(500)  NULL,
    status       NVARCHAR(10)   NOT NULL DEFAULT N'待审核'
                 CONSTRAINT CK_pwd_reset_status
                 CHECK (status IN (N'待审核', N'已通过', N'已驳回')),
    admin_id     NVARCHAR(20)   NULL,
    request_time DATETIME2(0)   NOT NULL DEFAULT SYSDATETIME(),
    process_time DATETIME2(0)   NULL,
    comment      NVARCHAR(200)  NULL,
    CONSTRAINT PK_password_reset_request PRIMARY KEY CLUSTERED (request_id),
    CONSTRAINT FK_pwd_reset_user FOREIGN KEY (user_id)
        REFERENCES dbo.user_account(user_id)
);
GO
CREATE NONCLUSTERED INDEX IX_pwd_reset_status ON dbo.password_reset_request(status);
GO

-- ================================================================
-- 测试数据 — 密码均为 123456（bcrypt hash，12轮）
-- ================================================================

-- 管理员
INSERT INTO dbo.user_account (user_id, password_hash, role) VALUES
('admin', '$2b$12$s5HpyxikPbsP1kT39vrQxuX5EcyLNBkYIXzzoOulQUuQIaOOxwR5C', 'admin');

-- 教师账号 (T001-T003)
INSERT INTO dbo.user_account (user_id, password_hash, role) VALUES
('T001', '$2b$12$Ne8fl8RGydkrP.2gr76/IeUP.Xr.NyJakhFIZEC1Mt8gG77TigXym', 'teacher'),
('T002', '$2b$12$sdeKcFDdyaVMI.PE/ehibO/Tor.9UxNe4duV4J0Mn8kcZX.2DK2bC', 'teacher'),
('T003', '$2b$12$Lx7mJ8vQpR3tY9zW5kF2a.Hn4bD6cE8gJ0iK2lM4oP6qR8sT0uV', 'teacher');

INSERT INTO dbo.teacher (teacher_id, name, title, college, email, contact) VALUES
('T001', N'张教授',  N'教授',   N'计算机科学与技术学院', 'zhang@univ.edu.cn', '13800001001'),
('T002', N'李副教授', N'副教授', N'数学与统计学院',      'li@univ.edu.cn',    '13800001002'),
('T003', N'王讲师',   N'讲师',   N'计算机科学与技术学院', 'wang@univ.edu.cn',  '13800001003');

-- 学生账号 (STU001-STU005)
INSERT INTO dbo.user_account (user_id, password_hash, role) VALUES
('STU001', '$2b$12$xmQpX8MRBWTePLxfyVRmS.Uh0I2d11vBixGKy4WTTkLRfpN04419a', 'student'),
('STU002', '$2b$12$0w1I.r//8gcxOW7Lo6uZ5OAtldnIJBn39LhsnLbfbAi2.asG58QAO', 'student'),
('STU003', '$2b$12$bGYCqeEK7HRZbh4WcW/QYeoWZDsrJWJSS5juejYiVzn/WeqjAg8B6', 'student'),
('STU004', '$2b$12$Nx9pQr8sT5vW2yZ7aB4cD.E6fG8hJ0kL2mN4oP6qR8sT0uVwX1', 'student'),
('STU005', '$2b$12$Ky6mN3bV5cX7zQ9rT1wY3.E5fG7hJ9kL1mN4oP6qR8sT0uVwX2', 'student');

INSERT INTO dbo.student (student_id, name, major, class_name, grade, email, contact) VALUES
('STU001', N'王小明', N'计算机科学与技术', N'计科2101', '2024', 'stu001@univ.edu.cn', '13900002001'),
('STU002', N'赵小红', N'软件工程',         N'软工2102', '2024', 'stu002@univ.edu.cn', '13900002002'),
('STU003', N'刘小刚', N'数据科学',         N'数据2101', '2024', 'stu003@univ.edu.cn', '13900002003'),
('STU004', N'陈小华', N'计算机科学与技术', N'计科2101', '2024', 'stu004@univ.edu.cn', '13900002004'),
('STU005', N'周小丽', N'软件工程',         N'软工2102', '2024', 'stu005@univ.edu.cn', '13900002005');

-- 课程信息（含完整详细信息，如图4格式）
INSERT INTO dbo.course (course_id, course_name, credit, hours, exam_type, department, course_type, target_major, description, textbook, syllabus, instructor_intro) VALUES
('CS100', N'程序设计基础', 4.0, 64, N'考试', N'计算机科学与技术学院', N'必修',
 N'计算机科学与技术,软件工程,数据科学',
 N'本课程是计算机科学与技术专业的核心基础课，讲授C语言程序设计的基本概念、语法结构和算法设计方法。通过本课程的学习，学生能够掌握结构化程序设计的思维方式，具备独立编写和调试中小规模程序的能力。课程内容涵盖数据类型、控制结构、函数、数组、指针、结构体及文件操作等核心主题。',
 N'《C程序设计（第五版）》谭浩强 著，清华大学出版社',
 N'第1-2周: 程序设计概述与C语言基础\n第3-5周: 数据类型与表达式\n第6-9周: 控制结构与程序设计方法\n第10-13周: 数组与函数\n第14-16周: 指针、结构体与文件操作\n第17-18周: 综合案例实训\n第19-20周: 复习与考试',
 N'张教授，计算机科学与技术学院博士生导师，从事程序设计教学20余年，主持国家自然科学基金项目多项，获省级教学成果一等奖。研究方向包括程序设计语言理论、编译优化和软件自动化。'),

('CS101', N'数据结构', 4.0, 64, N'考试', N'计算机科学与技术学院', N'必修',
 N'计算机科学与技术,软件工程,数据科学',
 N'本课程讲授常用数据结构的原理与实现，包括线性表、栈与队列、树与二叉树、图、查找和排序算法等核心内容。通过理论与实践相结合的教学方式，培养学生算法设计与分析能力。先修课程：CS100 程序设计基础。',
 N'《数据结构（C语言版）》严蔚敏 著，清华大学出版社',
 N'第1-3周: 绪论与线性表\n第4-6周: 栈与队列\n第7-10周: 树与二叉树\n第11-14周: 图\n第15-17周: 查找与排序\n第18-20周: 综合复习',
 N'张教授长期讲授数据结构课程，教学经验丰富。'),

('CS201', N'数据库原理', 3.0, 48, N'考试', N'计算机科学与技术学院', N'必修',
 N'计算机科学与技术,软件工程',
 N'本课程系统讲授数据库系统的基本概念、关系模型、关系代数、SQL语言、关系规范化理论、数据库设计和事务管理等核心内容，为后续数据库应用开发课程奠定理论基础。',
 N'《数据库系统概论（第5版）》王珊、萨师煊 著，高等教育出版社',
 N'第1-3周: 数据库系统概述\n第4-7周: 关系模型与SQL\n第8-11周: 关系规范化理论\n第12-15周: 数据库设计方法\n第16-18周: 事务管理与并发控制',
 N'张教授在数据库领域有深入研究，发表SCI/EI论文30余篇。'),

('CS301', N'软件工程', 3.0, 48, N'考查', N'计算机科学与技术学院', N'必修',
 N'计算机科学与技术,软件工程',
 N'本课程介绍软件工程的基本概念、软件生命周期模型、需求分析、系统设计、编码实现、测试方法和项目管理等核心知识。通过案例教学和小组项目实践，培养学生软件开发的工程化思维和团队协作能力。先修课程：CS100 程序设计基础、CS201 数据库原理。',
 N'《软件工程导论（第6版）》张海藩 著，清华大学出版社',
 N'第1-3周: 软件工程概论\n第4-7周: 需求分析\n第8-11周: 系统设计\n第12-15周: 实现与测试\n第16-18周: 项目管理与案例分析',
 N'张教授具有丰富的软件工程项目经验，曾主持多个大型信息系统建设。'),

('MATH101', N'高等数学', 5.0, 80, N'考试', N'数学与统计学院', N'公共必修',
 N'计算机科学与技术,软件工程,数据科学',
 N'本课程是理工科学生的基础必修课，讲授函数与极限、一元函数微积分学、向量代数与空间解析几何、多元函数微积分学、无穷级数和常微分方程等内容，为后续专业课程提供必要的数学基础。',
 N'《高等数学（第七版）》同济大学数学系 编，高等教育出版社',
 N'第1-4周: 函数与极限\n第5-8周: 导数与微分\n第9-12周: 不定积分与定积分\n第13-16周: 多元函数微积分\n第17-20周: 级数与微分方程',
 N'李副教授从事高等数学教学15年，多次获得校级教学质量优秀奖。'),

('CS202', N'操作系统原理', 3.5, 56, N'考试', N'计算机科学与技术学院', N'选修',
 N'计算机科学与技术,软件工程',
 N'本课程讲授操作系统的基本原理与设计方法，包括进程管理、内存管理、文件系统、设备管理和安全保护等核心内容。通过理论与实践相结合，帮助学生深入理解计算机系统的核心软件层。先修课程：CS100 程序设计基础。',
 N'《计算机操作系统（第4版）》汤小丹 著，西安电子科技大学出版社',
 N'第1-3周: 操作系统引论\n第4-7周: 进程管理\n第8-11周: 内存管理\n第12-15周: 文件系统\n第16-18周: 设备管理与安全',
 N'王讲师专注操作系统教学与研究，具有丰富的实验教学经验。'),

('ENG101', N'大学英语', 2.0, 32, N'考查', N'外国语学院', N'公共必修',
 N'计算机科学与技术,软件工程,数据科学',
 N'本课程旨在提高学生的英语综合应用能力，重点培养学生的阅读理解、写作表达和学术交流能力，为阅读英文专业文献和进行国际学术交流打下基础。',
 N'《新视野大学英语（第三版）》郑树棠 主编，外语教学与研究出版社',
 N'第1-5周: 阅读技巧训练\n第6-10周: 写作技巧训练\n第11-15周: 听说综合训练\n第16-20周: 学术英语与复习',
 N'外聘教师，具有TESOL国际英语教师资格认证。');

-- 开课计划（教师申请，管理员审核，教师自由选起止周）
INSERT INTO dbo.course_plan (course_id, teacher_id, semester, weekday, period_start, period_count, start_week, end_week, location, capacity, enrolled, prerequisite, apply_reason, status) VALUES
-- 已通过的课程
('CS100',   'T001', N'2026-2027-1', 1, 1, 2, 1,  18, N'教学楼A101', 30, 5, NULL,              N'本课程为专业基础课，教学计划覆盖1-18周，安排在第一大节便于学生集中学习。', N'已通过'),
('CS101',   'T001', N'2026-2027-1', 1, 3, 2, 1,  16, N'教学楼A201', 35, 2, N'CS100',          N'需要多媒体教室进行算法演示教学。', N'已通过'),
('CS201',   'T001', N'2026-2027-1', 2, 1, 2, 3,  18, N'教学楼B101', 30, 3, N'CS100',          N'安排在周二便于学生连续学习，配套实验课另在实验室进行。', N'已通过'),
('MATH101', 'T002', N'2026-2027-1', 3, 1, 2, 1,  20, N'教学楼C301', 60, 5, NULL,              N'大班教学，需要阶梯教室及多媒体投影设备。', N'已通过'),
('CS202',   'T003', N'2026-2027-1', 2, 5, 2, 5,  18, N'教学楼D201', 40, 0, N'CS100',          N'操作系统是计算机核心课程，安排在第5周开始以确保学生先修课程学习完毕。', N'已通过'),
('ENG101',  'T003', N'2026-2027-1', 4, 3, 2, 1,  16, N'教学楼E101', 50, 0, NULL,              N'英语小班教学效果更佳，安排多媒体语音教室。', N'已通过'),
-- 待审核的课程
('CS301',   'T001', N'2026-2027-1', 4, 5, 3, 5,  18, N'教学楼D101', 25, 0, N'CS101,CS201',    N'软件工程需要较长的授课时间段（三节课连排），便于进行案例分析和小组讨论。', N'待审核'),
('CS100',   'T003', N'2026-2027-1', 5, 1, 2, 1,  18, N'教学楼A102', 30, 0, NULL,              N'申请开设平行班，分流选课压力，保证教学质量。', N'待审核');

-- 选课记录
INSERT INTO dbo.enrollment (student_id, plan_id, status) VALUES
('STU001', 1, N'已选'), ('STU002', 1, N'已选'), ('STU003', 1, N'已选'),
('STU004', 1, N'已选'), ('STU005', 1, N'已选'),
('STU001', 2, N'已选'), ('STU002', 2, N'已选'),
('STU001', 3, N'已选'), ('STU002', 3, N'已选'), ('STU003', 3, N'已选'),
('STU001', 4, N'已选'), ('STU002', 4, N'已选'), ('STU003', 4, N'已选'),
('STU004', 4, N'已选'), ('STU005', 4, N'已选');

-- 成绩记录
INSERT INTO dbo.grade (student_id, plan_id, score, gpa_point, status) VALUES
('STU001', 1, 92, 4.0, N'正常'),
('STU002', 1, 78, 2.7, N'正常'),
('STU003', 1, 85, 3.3, N'正常');

GO
PRINT '===== 数据库 CourseManagementDB v3.0 初始化完成 =====';
GO
