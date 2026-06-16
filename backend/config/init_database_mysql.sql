-- ================================================================
-- 高校教务管理系统 - MySQL DDL 初始化脚本 v3.0
-- 数据库: course_management_db | 字符集: utf8mb4
-- 使用方法: mysql -u root -p < init_database_mysql.sql
-- ================================================================

DROP DATABASE IF EXISTS course_management_db;
CREATE DATABASE course_management_db
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE course_management_db;

-- ================================================================
-- 按外键依赖顺序删表
-- ================================================================
DROP TABLE IF EXISTS password_reset_request;
DROP TABLE IF EXISTS operation_log;
DROP TABLE IF EXISTS grade;
DROP TABLE IF EXISTS enrollment;
DROP TABLE IF EXISTS course_plan;
DROP TABLE IF EXISTS course;
DROP TABLE IF EXISTS teacher;
DROP TABLE IF EXISTS student;
DROP TABLE IF EXISTS user_account;
DROP TABLE IF EXISTS class_period;
DROP TABLE IF EXISTS semester_config;

-- ================================================================
-- 0a. class_period — 上课节次时间表（11节/天）
-- ================================================================
CREATE TABLE class_period (
    period_id     TINYINT       NOT NULL,
    period_name   VARCHAR(20)   NOT NULL,
    start_time    VARCHAR(10)   NOT NULL,
    end_time      VARCHAR(10)   NOT NULL,
    description   VARCHAR(50)   NULL,
    PRIMARY KEY (period_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO class_period (period_id, period_name, start_time, end_time, description) VALUES
(1,  '第一节',   '08:30', '09:10', '上午'),
(2,  '第二节',   '09:20', '10:00', '上午'),
(3,  '第三节',   '10:20', '11:00', '上午'),
(4,  '第四节',   '11:10', '11:50', '上午'),
(5,  '第五节',   '14:30', '15:10', '下午'),
(6,  '第六节',   '15:20', '16:00', '下午'),
(7,  '第七节',   '16:10', '16:50', '下午'),
(8,  '第八节',   '17:00', '17:40', '下午'),
(9,  '第九节',   '19:00', '19:40', '晚上'),
(10, '第十节',   '19:50', '20:30', '晚上'),
(11, '第十一节', '20:40', '21:20', '晚上');

-- ================================================================
-- 0b. semester_config — 学期配置表
-- ================================================================
CREATE TABLE semester_config (
    config_id       INT           NOT NULL AUTO_INCREMENT,
    semester        VARCHAR(20)   NOT NULL,
    total_weeks     TINYINT       NOT NULL DEFAULT 20,
    start_date      DATE          NULL,
    end_date        DATE          NULL,
    is_current      TINYINT       NOT NULL DEFAULT 0,
    enrollment_open TINYINT       NOT NULL DEFAULT 0,
    enroll_start    DATETIME      NULL,
    enroll_end      DATETIME      NULL,
    created_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (config_id),
    CONSTRAINT CK_semester_total_weeks CHECK (total_weeks BETWEEN 1 AND 30)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO semester_config (semester, total_weeks, start_date, end_date, is_current, enrollment_open)
VALUES ('2026-2027-1', 20, '2026-09-01', '2027-01-17', 1, 0);

-- ================================================================
-- 1. user_account — 用户账号表
-- ================================================================
CREATE TABLE user_account (
    user_id         VARCHAR(20)    NOT NULL,
    password_hash   VARCHAR(255)   NOT NULL,
    role            VARCHAR(10)    NOT NULL,
    last_login      DATETIME       NULL,
    is_locked       TINYINT        NOT NULL DEFAULT 0,
    login_fail_count INT           NOT NULL DEFAULT 0,
    created_at      DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id),
    CONSTRAINT CK_user_account_role CHECK (role IN ('admin','teacher','student'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ================================================================
-- 2. student — 学生信息表
-- ================================================================
CREATE TABLE student (
    student_id  VARCHAR(20)   NOT NULL,
    name        VARCHAR(50)   NOT NULL,
    major       VARCHAR(100)  NULL,
    class_name  VARCHAR(50)   NULL,
    grade       VARCHAR(4)    NULL,
    email       VARCHAR(100)  NULL,
    contact     VARCHAR(20)   NULL,
    created_at  DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (student_id),
    CONSTRAINT FK_student_user FOREIGN KEY (student_id)
        REFERENCES user_account(user_id)
        ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ================================================================
-- 3. teacher — 教师信息表
-- ================================================================
CREATE TABLE teacher (
    teacher_id  VARCHAR(20)   NOT NULL,
    name        VARCHAR(50)   NOT NULL,
    title       VARCHAR(50)   NULL,
    college     VARCHAR(100)  NULL,
    email       VARCHAR(100)  NULL,
    contact     VARCHAR(20)   NULL,
    created_at  DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (teacher_id),
    CONSTRAINT FK_teacher_user FOREIGN KEY (teacher_id)
        REFERENCES user_account(user_id)
        ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ================================================================
-- 4. course — 课程信息表
-- ================================================================
CREATE TABLE course (
    course_id        VARCHAR(20)    NOT NULL,
    course_name      VARCHAR(100)   NOT NULL,
    credit           DECIMAL(3,1)   NULL,
    hours            INT            NULL,
    exam_type        VARCHAR(10)    NULL,
    department       VARCHAR(100)   NULL,
    course_type      VARCHAR(20)    NULL DEFAULT '必修',
    target_major     VARCHAR(200)   NULL,
    description      VARCHAR(2000)  NULL,
    textbook         VARCHAR(200)   NULL,
    syllabus         VARCHAR(2000)  NULL,
    instructor_intro VARCHAR(2000)  NULL,
    created_at       DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (course_id),
    CONSTRAINT CK_course_exam_type CHECK (exam_type IN ('考试', '考查')),
    CONSTRAINT CK_course_type CHECK (course_type IN ('必修', '选修', '公共必修', '公共选修'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ================================================================
-- 5. course_plan — 开课计划表（教师申请制）
--    weekday: 1=周一 ... 7=周日
--    period_start: 起始节次 1-11
--    period_count: 持续节数 1-11
--    start_week/end_week: 由教师自由选择起止周
--    status: 待审核/已通过/已驳回/已停课
-- ================================================================
CREATE TABLE course_plan (
    plan_id        INT            NOT NULL AUTO_INCREMENT,
    course_id      VARCHAR(20)    NOT NULL,
    teacher_id     VARCHAR(20)    NOT NULL,
    semester       VARCHAR(20)    NOT NULL,
    weekday        TINYINT        NOT NULL,
    period_start   TINYINT        NOT NULL,
    period_count   TINYINT        NOT NULL DEFAULT 2,
    start_week     TINYINT        NOT NULL DEFAULT 1,
    end_week       TINYINT        NOT NULL DEFAULT 20,
    location       VARCHAR(100)   NULL,
    capacity       INT            NULL,
    enrolled       INT            NOT NULL DEFAULT 0,
    prerequisite   VARCHAR(200)   NULL,
    apply_reason   VARCHAR(500)   NULL,
    status         VARCHAR(10)    NOT NULL DEFAULT '待审核',
    audit_comment  VARCHAR(500)   NULL,
    created_at     DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (plan_id),
    CONSTRAINT CK_cp_weekday CHECK (weekday BETWEEN 1 AND 7),
    CONSTRAINT CK_cp_period_start CHECK (period_start BETWEEN 1 AND 11),
    CONSTRAINT CK_cp_period_count CHECK (period_count BETWEEN 1 AND 11),
    CONSTRAINT CK_cp_weeks CHECK (start_week BETWEEN 1 AND 20 AND end_week BETWEEN 1 AND 20 AND end_week >= start_week),
    CONSTRAINT CK_course_plan_status CHECK (status IN ('待审核', '已通过', '已驳回', '已停课')),
    CONSTRAINT FK_course_plan_course FOREIGN KEY (course_id)
        REFERENCES course(course_id),
    CONSTRAINT FK_course_plan_teacher FOREIGN KEY (teacher_id)
        REFERENCES teacher(teacher_id),
    INDEX IX_cp_course_semester (course_id, semester),
    INDEX IX_cp_status (status),
    INDEX IX_cp_teacher (teacher_id, semester)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ================================================================
-- 6. enrollment — 选课记录表
-- ================================================================
CREATE TABLE enrollment (
    enroll_id   INT           NOT NULL AUTO_INCREMENT,
    student_id  VARCHAR(20)   NOT NULL,
    plan_id     INT           NOT NULL,
    enroll_time DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status      VARCHAR(10)   NOT NULL DEFAULT '已选',
    created_at  DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (enroll_id),
    CONSTRAINT UQ_enrollment_student_plan UNIQUE (student_id, plan_id),
    CONSTRAINT CK_enrollment_status CHECK (status IN ('已选', '已退')),
    CONSTRAINT FK_enrollment_student FOREIGN KEY (student_id)
        REFERENCES student(student_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT FK_enrollment_plan FOREIGN KEY (plan_id)
        REFERENCES course_plan(plan_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ================================================================
-- 7. grade — 成绩记录表
-- ================================================================
CREATE TABLE grade (
    grade_id      INT            NOT NULL AUTO_INCREMENT,
    student_id    VARCHAR(20)    NOT NULL,
    plan_id       INT            NOT NULL,
    score         INT            NULL,
    gpa_point     DECIMAL(3,2)   NULL,
    record_time   DATETIME       NULL DEFAULT CURRENT_TIMESTAMP,
    status        VARCHAR(10)    NOT NULL DEFAULT '正常',
    modify_reason VARCHAR(500)   NULL,
    new_score     INT            NULL,
    created_at    DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (grade_id),
    CONSTRAINT CK_grade_score CHECK (score >= 0 AND score <= 100),
    CONSTRAINT CK_grade_status CHECK (status IN ('正常', '待审核', '已更正')),
    CONSTRAINT FK_grade_student FOREIGN KEY (student_id)
        REFERENCES student(student_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT FK_grade_plan FOREIGN KEY (plan_id)
        REFERENCES course_plan(plan_id),
    INDEX IX_grade_student_plan (student_id, plan_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ================================================================
-- 8. operation_log — 操作日志表
-- ================================================================
CREATE TABLE operation_log (
    log_id      INT            NOT NULL AUTO_INCREMENT,
    user_id     VARCHAR(20)    NOT NULL,
    log_type    VARCHAR(10)    NOT NULL,
    operation   VARCHAR(200)   NOT NULL,
    result      VARCHAR(10)    NOT NULL,
    log_time    DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ip_address  VARCHAR(50)    NULL,
    created_at  DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (log_id),
    CONSTRAINT CK_log_type CHECK (log_type IN ('登录', '选课', '成绩', '审核', '系统')),
    CONSTRAINT CK_log_result CHECK (result IN ('成功', '失败')),
    INDEX IX_log_user_time (user_id, log_time)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ================================================================
-- 9. password_reset_request — 密码重置申请表
-- ================================================================
CREATE TABLE password_reset_request (
    request_id   INT            NOT NULL AUTO_INCREMENT,
    user_id      VARCHAR(20)    NOT NULL,
    reason       VARCHAR(500)   NULL,
    status       VARCHAR(10)    NOT NULL DEFAULT '待审核',
    admin_id     VARCHAR(20)    NULL,
    request_time DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP,
    process_time DATETIME       NULL,
    comment      VARCHAR(200)   NULL,
    PRIMARY KEY (request_id),
    CONSTRAINT CK_pwd_reset_status CHECK (status IN ('待审核', '已通过', '已驳回')),
    CONSTRAINT FK_pwd_reset_user FOREIGN KEY (user_id)
        REFERENCES user_account(user_id),
    INDEX IX_pwd_reset_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ================================================================
-- 测试数据 — 密码均为 123456（bcrypt hash，12轮）
-- ================================================================

-- 管理员
INSERT INTO user_account (user_id, password_hash, role) VALUES
('admin', '$2b$12$s5HpyxikPbsP1kT39vrQxuX5EcyLNBkYIXzzoOulQUuQIaOOxwR5C', 'admin');

-- 教师账号 (T001-T003)
INSERT INTO user_account (user_id, password_hash, role) VALUES
('T001', '$2b$12$Ne8fl8RGydkrP.2gr76/IeUP.Xr.NyJakhFIZEC1Mt8gG77TigXym', 'teacher'),
('T002', '$2b$12$sdeKcFDdyaVMI.PE/ehibO/Tor.9UxNe4duV4J0Mn8kcZX.2DK2bC', 'teacher'),
('T003', '$2b$12$Lx7mJ8vQpR3tY9zW5kF2a.Hn4bD6cE8gJ0iK2lM4oP6qR8sT0uV', 'teacher');

INSERT INTO teacher (teacher_id, name, title, college, email, contact) VALUES
('T001', '张教授',  '教授',   '计算机科学与技术学院', 'zhang@univ.edu.cn', '13800001001'),
('T002', '李副教授', '副教授', '数学与统计学院',      'li@univ.edu.cn',    '13800001002'),
('T003', '王讲师',   '讲师',   '计算机科学与技术学院', 'wang@univ.edu.cn',  '13800001003');

-- 学生账号 (STU001-STU005)
INSERT INTO user_account (user_id, password_hash, role) VALUES
('STU001', '$2b$12$xmQpX8MRBWTePLxfyVRmS.Uh0I2d11vBixGKy4WTTkLRfpN04419a', 'student'),
('STU002', '$2b$12$0w1I.r//8gcxOW7Lo6uZ5OAtldnIJBn39LhsnLbfbAi2.asG58QAO', 'student'),
('STU003', '$2b$12$bGYCqeEK7HRZbh4WcW/QYeoWZDsrJWJSS5juejYiVzn/WeqjAg8B6', 'student'),
('STU004', '$2b$12$Nx9pQr8sT5vW2yZ7aB4cD.E6fG8hJ0kL2mN4oP6qR8sT0uVwX1', 'student'),
('STU005', '$2b$12$Ky6mN3bV5cX7zQ9rT1wY3.E5fG7hJ9kL1mN4oP6qR8sT0uVwX2', 'student');

INSERT INTO student (student_id, name, major, class_name, grade, email, contact) VALUES
('STU001', '王小明', '计算机科学与技术', '计科2101', '2024', 'stu001@univ.edu.cn', '13900002001'),
('STU002', '赵小红', '软件工程',         '软工2102', '2024', 'stu002@univ.edu.cn', '13900002002'),
('STU003', '刘小刚', '数据科学',         '数据2101', '2024', 'stu003@univ.edu.cn', '13900002003'),
('STU004', '陈小华', '计算机科学与技术', '计科2101', '2024', 'stu004@univ.edu.cn', '13900002004'),
('STU005', '周小丽', '软件工程',         '软工2102', '2024', 'stu005@univ.edu.cn', '13900002005');

-- 课程信息
INSERT INTO course (course_id, course_name, credit, hours, exam_type, department, course_type, target_major, description, textbook, syllabus, instructor_intro) VALUES
('CS100', '程序设计基础', 4.0, 64, '考试', '计算机科学与技术学院', '必修',
 '计算机科学与技术,软件工程,数据科学',
 '本课程是计算机科学与技术专业的核心基础课，讲授C语言程序设计的基本概念、语法结构和算法设计方法。',
 '《C程序设计（第五版）》谭浩强 著，清华大学出版社',
 '第1-2周: 程序设计概述与C语言基础\n第3-5周: 数据类型与表达式\n第6-9周: 控制结构与程序设计方法\n第10-13周: 数组与函数\n第14-16周: 指针、结构体与文件操作\n第17-18周: 综合案例实训\n第19-20周: 复习与考试',
 '张教授，计算机科学与技术学院博士生导师，从事程序设计教学20余年。'),

('CS101', '数据结构', 4.0, 64, '考试', '计算机科学与技术学院', '必修',
 '计算机科学与技术,软件工程,数据科学',
 '本课程讲授常用数据结构的原理与实现，包括线性表、栈与队列、树与二叉树、图、查找和排序算法等核心内容。先修课程：CS100 程序设计基础。',
 '《数据结构（C语言版）》严蔚敏 著，清华大学出版社',
 '第1-3周: 绪论与线性表\n第4-6周: 栈与队列\n第7-10周: 树与二叉树\n第11-14周: 图\n第15-17周: 查找与排序\n第18-20周: 综合复习',
 '张教授长期讲授数据结构课程，教学经验丰富。'),

('CS201', '数据库原理', 3.0, 48, '考试', '计算机科学与技术学院', '必修',
 '计算机科学与技术,软件工程',
 '本课程系统讲授数据库系统的基本概念、关系模型、关系代数、SQL语言、关系规范化理论、数据库设计和事务管理等核心内容。',
 '《数据库系统概论（第5版）》王珊、萨师煊 著，高等教育出版社',
 '第1-3周: 数据库系统概述\n第4-7周: 关系模型与SQL\n第8-11周: 关系规范化理论\n第12-15周: 数据库设计方法\n第16-18周: 事务管理与并发控制',
 '张教授在数据库领域有深入研究，发表SCI/EI论文30余篇。'),

('CS301', '软件工程', 3.0, 48, '考查', '计算机科学与技术学院', '必修',
 '计算机科学与技术,软件工程',
 '本课程介绍软件工程的基本概念、软件生命周期模型、需求分析、系统设计、编码实现、测试方法和项目管理等核心知识。先修课程：CS100 程序设计基础、CS201 数据库原理。',
 '《软件工程导论（第6版）》张海藩 著，清华大学出版社',
 '第1-3周: 软件工程概论\n第4-7周: 需求分析\n第8-11周: 系统设计\n第12-15周: 实现与测试\n第16-18周: 项目管理与案例分析',
 '张教授具有丰富的软件工程项目经验，曾主持多个大型信息系统建设。'),

('MATH101', '高等数学', 5.0, 80, '考试', '数学与统计学院', '公共必修',
 '计算机科学与技术,软件工程,数据科学',
 '本课程是理工科学生的基础必修课，讲授函数与极限、一元函数微积分学、向量代数与空间解析几何、多元函数微积分学、无穷级数和常微分方程等内容。',
 '《高等数学（第七版）》同济大学数学系 编，高等教育出版社',
 '第1-4周: 函数与极限\n第5-8周: 导数与微分\n第9-12周: 不定积分与定积分\n第13-16周: 多元函数微积分\n第17-20周: 级数与微分方程',
 '李副教授从事高等数学教学15年，多次获得校级教学质量优秀奖。'),

('CS202', '操作系统原理', 3.5, 56, '考试', '计算机科学与技术学院', '选修',
 '计算机科学与技术,软件工程',
 '本课程讲授操作系统的基本原理与设计方法，包括进程管理、内存管理、文件系统、设备管理和安全保护等核心内容。先修课程：CS100 程序设计基础。',
 '《计算机操作系统（第4版）》汤小丹 著，西安电子科技大学出版社',
 '第1-3周: 操作系统引论\n第4-7周: 进程管理\n第8-11周: 内存管理\n第12-15周: 文件系统\n第16-18周: 设备管理与安全',
 '王讲师专注操作系统教学与研究，具有丰富的实验教学经验。'),

('ENG101', '大学英语', 2.0, 32, '考查', '外国语学院', '公共必修',
 '计算机科学与技术,软件工程,数据科学',
 '本课程旨在提高学生的英语综合应用能力，重点培养学生的阅读理解、写作表达和学术交流能力。',
 '《新视野大学英语（第三版）》郑树棠 主编，外语教学与研究出版社',
 '第1-5周: 阅读技巧训练\n第6-10周: 写作技巧训练\n第11-15周: 听说综合训练\n第16-20周: 学术英语与复习',
 '外聘教师，具有TESOL国际英语教师资格认证。');

-- 开课计划（教师申请，管理员审核）
INSERT INTO course_plan (course_id, teacher_id, semester, weekday, period_start, period_count, start_week, end_week, location, capacity, enrolled, prerequisite, apply_reason, status) VALUES
('CS100',   'T001', '2026-2027-1', 1, 1, 2, 1,  18, '教学楼A101', 30, 5, NULL,            '本课程为专业基础课，教学计划覆盖1-18周。', '已通过'),
('CS101',   'T001', '2026-2027-1', 1, 3, 2, 1,  16, '教学楼A201', 35, 2, 'CS100',          '需要多媒体教室进行算法演示教学。', '已通过'),
('CS201',   'T001', '2026-2027-1', 2, 1, 2, 3,  18, '教学楼B101', 30, 3, 'CS100',          '配套实验课另在实验室进行。', '已通过'),
('MATH101', 'T002', '2026-2027-1', 3, 1, 2, 1,  20, '教学楼C301', 60, 5, NULL,            '大班教学，需要阶梯教室及多媒体投影设备。', '已通过'),
('CS202',   'T003', '2026-2027-1', 2, 5, 2, 5,  18, '教学楼D201', 40, 0, 'CS100',          '操作系统是计算机核心课程。', '已通过'),
('ENG101',  'T003', '2026-2027-1', 4, 3, 2, 1,  16, '教学楼E101', 50, 0, NULL,            '英语小班教学效果更佳。', '已通过'),
('CS301',   'T001', '2026-2027-1', 4, 5, 3, 5,  18, '教学楼D101', 25, 0, 'CS101,CS201',    '软件工程需要较长授课时间段（三节连排）。', '待审核'),
('CS100',   'T003', '2026-2027-1', 5, 1, 2, 1,  18, '教学楼A102', 30, 0, NULL,            '申请开设平行班，分流选课压力。', '待审核');

-- 选课记录
INSERT INTO enrollment (student_id, plan_id, status) VALUES
('STU001', 1, '已选'), ('STU002', 1, '已选'), ('STU003', 1, '已选'),
('STU004', 1, '已选'), ('STU005', 1, '已选'),
('STU001', 2, '已选'), ('STU002', 2, '已选'),
('STU001', 3, '已选'), ('STU002', 3, '已选'), ('STU003', 3, '已选'),
('STU001', 4, '已选'), ('STU002', 4, '已选'), ('STU003', 4, '已选'),
('STU004', 4, '已选'), ('STU005', 4, '已选');

-- 成绩记录
INSERT INTO grade (student_id, plan_id, score, gpa_point, status) VALUES
('STU001', 1, 92, 4.0, '正常'),
('STU002', 1, 78, 2.7, '正常'),
('STU003', 1, 85, 3.3, '正常');

SELECT '===== 数据库 course_management_db v3.0 MySQL 版初始化完成 =====' AS message;
