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
    current_guard   TINYINT       GENERATED ALWAYS AS
                    (CASE WHEN is_current = 1 THEN 1 ELSE NULL END) STORED,
    enrollment_open TINYINT       NOT NULL DEFAULT 0,
    enroll_start    DATETIME      NULL,
    enroll_end      DATETIME      NULL,
    created_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (config_id),
    CONSTRAINT CK_semester_total_weeks CHECK (total_weeks BETWEEN 1 AND 30),
    CONSTRAINT UQ_semester_single_current UNIQUE (current_guard)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 多学期配置: 当前学期选课开放，历史学期用于查询
INSERT INTO semester_config (semester, total_weeks, start_date, end_date, is_current, enrollment_open, enroll_start, enroll_end) VALUES
('2025-2026-2', 20, '2026-02-17', '2026-07-04', 0, 0, NULL, NULL),
('2026-2027-1', 20, '2026-09-01', '2027-01-17', 1, 1, '2026-06-18 09:00:00', '2026-12-31 23:59:59'),
('2026-2027-2', 20, '2027-02-22', '2027-07-10', 0, 0, NULL, NULL);

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
    token_version   INT            NOT NULL DEFAULT 0,
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
    target_id   VARCHAR(20)    NULL,
    resource_type VARCHAR(30)  NULL,
    semester    VARCHAR(20)    NULL,
    reason      VARCHAR(500)   NULL,
    request_id  VARCHAR(64)    NULL,
    created_at  DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (log_id),
    CONSTRAINT CK_log_type CHECK (log_type IN ('登录', '选课', '成绩', '审核', '系统', '导出')),
    CONSTRAINT CK_log_result CHECK (result IN ('成功', '失败')),
    INDEX IX_log_user_time (user_id, log_time)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ================================================================
-- 9. password_reset_request — 密码重置申请表
-- ================================================================
CREATE TABLE password_reset_request (
    request_id   INT            NOT NULL AUTO_INCREMENT,
    user_id      VARCHAR(20)    NOT NULL,
    new_password VARCHAR(255)   NULL        COMMENT '申请的新密码哈希（NULL=重置为默认密码）',
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
-- 测试数据
-- 密码均为 123456（bcrypt hash，12轮）
-- ================================================================

-- ── 管理员（2人）──
INSERT INTO user_account (user_id, password_hash, role) VALUES
('admin',  '$2b$12$s5HpyxikPbsP1kT39vrQxuX5EcyLNBkYIXzzoOulQUuQIaOOxwR5C', 'admin'),
('admin2', '$2b$12$epxNrr6WsNLMyxqkVJphZOrrjunIhpiuXCwp5NKLTW6FTlNCS2T12', 'admin');

-- ── 教师账号（T001-T008，8人）──
INSERT INTO user_account (user_id, password_hash, role) VALUES
('T001', '$2b$12$Ne8fl8RGydkrP.2gr76/IeUP.Xr.NyJakhFIZEC1Mt8gG77TigXym', 'teacher'),
('T002', '$2b$12$sdeKcFDdyaVMI.PE/ehibO/Tor.9UxNe4duV4J0Mn8kcZX.2DK2bC', 'teacher'),
('T003', '$2b$12$UHPUnknqLjYjIV6U1RLwP.k6mJ8s1Iv1SlqgIGoJqWOGNJ6E0pPWq', 'teacher'),
('T004', '$2b$12$iln/9CNZaINEW/hbaiQRzuZNS7jKWL2kO9.Tg7CZyF3VPuxkbd5nq', 'teacher'),
('T005', '$2b$12$3nO1SDGN3NkjgJrOBx8XcON9s6A8gbYeLrhV9ubkdycNL1XMCa25O', 'teacher'),
('T006', '$2b$12$e/0BB2/m5b812z21DiSz6eN5yLZiSWeOp.9AqssDxT9ehwkmhjz9i', 'teacher'),
('T007', '$2b$12$iRuyfXjJy9ku3pBwC.z8NuW85I/2niWWt50Ym87xSWU71Khm5AZXu', 'teacher'),
('T008', '$2b$12$WrMmfqY1h7bO1p.q3JMdJO/2nEzV30bFvGNz16kOI9ofNsLfXb4rG', 'teacher');

INSERT INTO teacher (teacher_id, name, title, college, email, contact) VALUES
('T001', '张教授',    '教授',     '计算机科学与技术学院', 'zhang@univ.edu.cn', '13800001001'),
('T002', '李副教授',  '副教授',   '数学与统计学院',      'li@univ.edu.cn',    '13800001002'),
('T003', '王讲师',    '讲师',     '计算机科学与技术学院', 'wang@univ.edu.cn',  '13800001003'),
('T004', '陈教授',    '教授',     '计算机科学与技术学院', 'chen@univ.edu.cn',  '13800001004'),
('T005', '刘副教授',  '副教授',   '数学与统计学院',      'liu2@univ.edu.cn',  '13800001005'),
('T006', '黄讲师',    '讲师',     '外国语学院',          'huang@univ.edu.cn', '13800001006'),
('T007', '孙教授',    '教授',     '电子信息工程学院',    'sun@univ.edu.cn',   '13800001007'),
('T008', '林副教授',  '副教授',   '软件学院',            'lin@univ.edu.cn',   '13800001008');

-- ── 学生账号（STU001-STU025，25人）──
INSERT INTO user_account (user_id, password_hash, role) VALUES
('STU001',  '$2b$12$xmQpX8MRBWTePLxfyVRmS.Uh0I2d11vBixGKy4WTTkLRfpN04419a', 'student'),
('STU002',  '$2b$12$0w1I.r//8gcxOW7Lo6uZ5OAtldnIJBn39LhsnLbfbAi2.asG58QAO', 'student'),
('STU003',  '$2b$12$bGYCqeEK7HRZbh4WcW/QYeoWZDsrJWJSS5juejYiVzn/WeqjAg8B6', 'student'),
('STU004',  '$2b$12$gNeaOsawnzbWD9AkrbmFxum43YojiqhEa.gwyCRkej5/P5.wk8ZbG', 'student'),
('STU005',  '$2b$12$L9m6.ndTvHddToFF3NNdW.6i5erDHNG8dp6I5QjLomfHXOKu6./G.', 'student'),
('STU006',  '$2b$12$Tt6wkdlr17B8PzRHAPs/euCXAuSed6YhNVYDWi9qOT/qaB2UPetLW', 'student'),
('STU007',  '$2b$12$MbnSeSrLqDCVZk1x9uDhneK9NrG1IhBFnazIihBB1t9PviZx3yjl2', 'student'),
('STU008',  '$2b$12$ftrc6WqqoLKUeWztfJ3Aluqo0G3L1DhgcyGT3YBKmzemCndbVy/M.', 'student'),
('STU009',  '$2b$12$iUsovBZbb4jHmnHfyUcmdOum.SPtq.Ojc3n8B4Xb9t3xvwdmV1RaW', 'student'),
('STU010',  '$2b$12$9nvg1PW2r91k1BS0t74X2OKVqutS9xPDSSoo2/EBjPrey8ALdlUvK', 'student'),
('STU011',  '$2b$12$UOqW2YQBgfCCWjZBKh.7tepLy5FYayE.8/uKk9lpUamrVbl.3.AD2', 'student'),
('STU012',  '$2b$12$Zmocji2YArqjoAqNgXqqJemoqg0zKi/TiAidoVG8cR9gGjHB9B1NW', 'student'),
('STU013',  '$2b$12$cMXow/2msx47ikusoiRdyO8xEkf7.nrXx0J.sipyoY9E2lIXelsu2', 'student'),
('STU014',  '$2b$12$IbXtdxqU3EJ69u.8a.JBTuTnXiigOEcyKx4ixCw3KBGTdIJKcpf/C', 'student'),
('STU015',  '$2b$12$b6nEWqrkBm6.NpaJrjCzrO5B.Bqog.2RlgY/zovDkXytZdERgILNK', 'student'),
('STU016',  '$2b$12$QAEudefxpJILEV1E7DT.xeu8B8PRhEkwX6bZNtIDlecIRDcWZoRTe', 'student'),
('STU017',  '$2b$12$lq4jKoAHBfVulfVpc.DrzeDOlbMnXU9ouBjGvW1M54aPh67JVbHWS', 'student'),
('STU018',  '$2b$12$Oz.tcQgs0a6macNt/4ecOeD7x/tiwvga2rtwR6SajRJZs8e/aWYwi', 'student'),
('STU019',  '$2b$12$srNae8sTcyA3QGdUbGxIyu2ytky7h/6rMB26EdGRuon9Q4Git/UlW', 'student'),
('STU020',  '$2b$12$vzptMGkRLDof0AMgom9g7.XdFB9wZi295hCnQF8g95Kp1pPPmrYXu', 'student'),
('STU021',  '$2b$12$qON7SFllaoWaRQOcU.xtX.3Y/rTZ8BF5s455aTBFFwNOlzv4TOm6q', 'student'),
('STU022',  '$2b$12$3QRtEtYMMQSHIaIwF58Soe2y6hYigPP/Jh2CDjKTDy8hTOiGAQB/C', 'student'),
('STU023',  '$2b$12$8cTCH3GpSi8qcRWkiULm1.0mLmySfrhGHW61qGWp3YCVb.eJEEVN2', 'student'),
('STU024',  '$2b$12$OCPJ29o2ZZIb6ej4qz4/veq09LKvh2rn/KK1PlDzHg0YOdjcSf6/.', 'student'),
('STU025',  '$2b$12$YyiklMMRtX.16RXhY40Yke9zEv.yUJn6gQGsmSoEngzs2BHUUsrkq', 'student');

INSERT INTO student (student_id, name, major, class_name, grade, email, contact) VALUES
-- 计科2101（2024级）—— 原班 + 扩增
('STU001', '王小明', '计算机科学与技术', '计科2101', '2024', 'stu001@univ.edu.cn', '13900002001'),
('STU004', '陈小华', '计算机科学与技术', '计科2101', '2024', 'stu004@univ.edu.cn', '13900002004'),
('STU006', '李大勇', '计算机科学与技术', '计科2101', '2024', 'stu006@univ.edu.cn', '13900002006'),
('STU007', '周小雪', '计算机科学与技术', '计科2101', '2024', 'stu007@univ.edu.cn', '13900002007'),
('STU008', '马小天', '计算机科学与技术', '计科2101', '2024', 'stu008@univ.edu.cn', '13900002008'),
-- 软工2102（2024级）
('STU002', '赵小红', '软件工程',         '软工2102', '2024', 'stu002@univ.edu.cn', '13900002002'),
('STU005', '周小丽', '软件工程',         '软工2102', '2024', 'stu005@univ.edu.cn', '13900002005'),
('STU009', '吴小龙', '软件工程',         '软工2102', '2024', 'stu009@univ.edu.cn', '13900002009'),
('STU010', '郑小花', '软件工程',         '软工2102', '2024', 'stu010@univ.edu.cn', '13900002010'),
('STU011', '孙小虎', '软件工程',         '软工2102', '2024', 'stu011@univ.edu.cn', '13900002011'),
-- 数据2101（2024级）
('STU003', '刘小刚', '数据科学',         '数据2101', '2024', 'stu003@univ.edu.cn', '13900002003'),
('STU012', '黄小燕', '数据科学',         '数据2101', '2024', 'stu012@univ.edu.cn', '13900002012'),
('STU013', '钱小鹏', '数据科学',         '数据2101', '2024', 'stu013@univ.edu.cn', '13900002013'),
-- 计科2201（2025级）
('STU014', '张子涵', '计算机科学与技术', '计科2201', '2025', 'stu014@univ.edu.cn', '13900002014'),
('STU015', '刘子轩', '计算机科学与技术', '计科2201', '2025', 'stu015@univ.edu.cn', '13900002015'),
('STU016', '陈子怡', '计算机科学与技术', '计科2201', '2025', 'stu016@univ.edu.cn', '13900002016'),
-- 软工2202（2025级）
('STU017', '王子墨', '软件工程',         '软工2202', '2025', 'stu017@univ.edu.cn', '13900002017'),
('STU018', '李雨桐', '软件工程',         '软工2202', '2025', 'stu018@univ.edu.cn', '13900002018'),
('STU019', '赵宇航', '软件工程',         '软工2202', '2025', 'stu019@univ.edu.cn', '13900002019'),
-- 数据2301（2026级新生）
('STU020', '孙一凡', '数据科学',         '数据2301', '2026', 'stu020@univ.edu.cn', '13900002020'),
('STU021', '吴一鸣', '数据科学',         '数据2301', '2026', 'stu021@univ.edu.cn', '13900002021'),
('STU022', '郑一诺', '数据科学',         '数据2301', '2026', 'stu022@univ.edu.cn', '13900002022'),
-- 电子2101（跨学院）
('STU023', '马思远', '电子信息工程',     '电子2101', '2024', 'stu023@univ.edu.cn', '13900002023'),
('STU024', '黄思源', '电子信息工程',     '电子2101', '2024', 'stu024@univ.edu.cn', '13900002024'),
('STU025', '钱思宇', '电子信息工程',     '电子2101', '2024', 'stu025@univ.edu.cn', '13900002025');

-- ── 课程信息（11门，覆盖4个类型+3个学院）──
INSERT INTO course (course_id, course_name, credit, hours, exam_type, department, course_type, target_major, description, textbook, syllabus, instructor_intro) VALUES
-- 必修
('CS100', '程序设计基础', 4.0, 64, '考试', '计算机科学与技术学院', '必修',
 '计算机科学与技术,软件工程,数据科学',
 '讲授C语言程序设计的基本概念、语法结构和算法设计方法。',
 '《C程序设计（第五版）》谭浩强 著，清华大学出版社',
 '第1-2周: 程序设计概述与C语言基础\n第3-5周: 数据类型与表达式\n第6-9周: 控制结构与程序设计方法\n第10-13周: 数组与函数\n第14-16周: 指针、结构体与文件操作\n第17-18周: 综合案例实训\n第19-20周: 复习与考试',
 '张教授，计算机科学与技术学院博士生导师，从事程序设计教学20余年。'),

('CS101', '数据结构', 4.0, 64, '考试', '计算机科学与技术学院', '必修',
 '计算机科学与技术,软件工程,数据科学',
 '讲授线性表、栈与队列、树与二叉树、图、查找和排序算法等核心内容。先修: CS100。',
 '《数据结构（C语言版）》严蔚敏 著，清华大学出版社',
 '第1-3周: 绪论与线性表\n第4-6周: 栈与队列\n第7-10周: 树与二叉树\n第11-14周: 图\n第15-17周: 查找与排序\n第18-20周: 综合复习',
 '张教授长期讲授数据结构课程，教学经验丰富。'),

('CS201', '数据库原理', 3.0, 48, '考试', '计算机科学与技术学院', '必修',
 '计算机科学与技术,软件工程',
 '系统讲授关系模型、SQL语言、规范化和事务管理等核心内容。',
 '《数据库系统概论（第5版）》王珊、萨师煊 著，高等教育出版社',
 '第1-3周: 数据库系统概述\n第4-7周: 关系模型与SQL\n第8-11周: 关系规范化理论\n第12-15周: 数据库设计方法\n第16-18周: 事务管理与并发控制',
 '张教授在数据库领域有深入研究。'),

('CS301', '软件工程', 3.0, 48, '考查', '计算机科学与技术学院', '必修',
 '计算机科学与技术,软件工程',
 '介绍软件生命周期、需求分析、系统设计、测试方法和项目管理。先修: CS100, CS201。',
 '《软件工程导论（第6版）》张海藩 著，清华大学出版社',
 '第1-3周: 概论\n第4-7周: 需求分析\n第8-11周: 系统设计\n第12-15周: 实现与测试\n第16-18周: 项目管理',
 '张教授主持过多项大型信息系统建设项目。'),

-- 选修
('CS202', '操作系统原理', 3.5, 56, '考试', '计算机科学与技术学院', '选修',
 '计算机科学与技术,软件工程',
 '讲授进程管理、内存管理、文件系统、设备管理等操作系统核心内容。先修: CS100。',
 '《计算机操作系统（第4版）》汤小丹 著，西安电子科技大学出版社',
 '第1-3周: 操作系统引论\n第4-7周: 进程管理\n第8-11周: 内存管理\n第12-15周: 文件系统\n第16-18周: 设备管理与安全',
 '王讲师专注操作系统教学与研究。'),

-- 新增课程
('CS302', '计算机网络', 3.0, 48, '考试', '计算机科学与技术学院', '选修',
 '计算机科学与技术,软件工程',
 '讲解TCP/IP协议栈、网络分层、路由算法、网络安全等基础内容。先修: CS100。',
 '《计算机网络（第8版）》谢希仁 著，电子工业出版社',
 '第1-4周: 网络体系结构\n第5-8周: 物理层与数据链路层\n第9-12周: 网络层\n第13-16周: 传输层与应用层\n第17-18周: 网络安全与复习',
 '陈教授从事网络技术研究20年。'),

('CS303', '人工智能导论', 2.5, 40, '考查', '计算机科学与技术学院', '选修',
 '计算机科学与技术,软件工程,数据科学',
 '介绍AI概述、搜索、知识表示、机器学习初步和简单应用。',
 '《人工智能：一种现代方法（第4版）》Stuart Russell 著，人民邮电出版社',
 '第1-3周: AI概述\n第4-7周: 搜索与约束满足\n第8-11周: 知识与推理\n第12-15周: 机器学习初步\n第16-18周: 应用与伦理',
 '林副教授专注人工智能教育。'),

-- 公共必修
('MATH101', '高等数学A', 5.0, 80, '考试', '数学与统计学院', '公共必修',
 '计算机科学与技术,软件工程,数据科学,电子信息工程',
 '讲授函数与极限、微积分、向量代数、级数和微分方程。',
 '《高等数学（第七版）》同济大学数学系 编，高等教育出版社',
 '第1-4周: 函数与极限\n第5-8周: 导数与微分\n第9-12周: 不定积分与定积分\n第13-16周: 多元函数微积分\n第17-20周: 级数与微分方程',
 '李副教授从事高等数学教学15年。'),

('MATH201', '线性代数', 3.0, 48, '考试', '数学与统计学院', '公共必修',
 '计算机科学与技术,软件工程,数据科学,电子信息工程',
 '讲授行列式、矩阵、向量空间、线性变换、特征值与特征向量。',
 '《工程数学：线性代数（第六版）》同济大学数学系 编，高等教育出版社',
 '第1-4周: 行列式与矩阵\n第5-8周: 向量与线性方程组\n第9-12周: 向量空间与线性变换\n第13-16周: 特征值与特征向量\n第17-18周: 二次型与应用',
 '刘副教授，多次获评校级教学名师。'),

('ENG101', '大学英语', 2.0, 32, '考查', '外国语学院', '公共必修',
 '计算机科学与技术,软件工程,数据科学,电子信息工程',
 '提高英语综合应用，重点培养阅读、写作和学术交流能力。',
 '《新视野大学英语（第三版）》郑树棠 主编，外语教学与研究出版社',
 '第1-5周: 阅读技巧训练\n第6-10周: 写作技巧训练\n第11-15周: 听说综合训练\n第16-20周: 学术英语与复习',
 '黄讲师持有TESOL国际认证。'),

-- 公共选修
('ELEC101', '物联网概论', 2.0, 32, '考查', '电子信息工程学院', '公共选修',
 '计算机科学与技术,软件工程,数据科学,电子信息工程',
 '介绍物联网架构、传感器技术、无线通信和典型应用场景。',
 '《物联网导论（第3版）》刘云浩 著，清华大学出版社',
 '第1-4周: 物联网概述\n第5-8周: 感知层技术\n第9-12周: 网络层技术\n第13-16周: 应用层与案例\n第17-18周: 总结与展示',
 '孙教授主持多项国家物联网重大专项课题。');

-- ── 开课计划（15条，覆盖3个状态+已驳回+历史学期）──
INSERT INTO course_plan (course_id, teacher_id, semester, weekday, period_start, period_count, start_week, end_week, location, capacity, enrolled, prerequisite, apply_reason, status) VALUES
-- 已通过（10条）
('CS100',   'T001', '2026-2027-1', 1, 1, 2, 1,  18, '教学楼A101', 35, 20, NULL,              '专业基础课，覆盖1-18周。', '已通过'),
('CS101',   'T001', '2026-2027-1', 1, 3, 2, 1,  16, '教学楼A201', 35, 12, 'CS100',            '需多媒体教室算法演示教学。', '已通过'),
('CS201',   'T001', '2026-2027-1', 2, 1, 2, 3,  18, '教学楼B101', 30, 10, 'CS100',            '配套实验课在实验室进行。', '已通过'),
('MATH101', 'T002', '2026-2027-1', 3, 1, 2, 1,  20, '教学楼C301', 80, 25, NULL,              '大班教学，需阶梯教室。', '已通过'),
('MATH201', 'T005', '2026-2027-1', 2, 5, 2, 1,  18, '教学楼C201', 60, 0,  NULL,              '新开公共必修课，数学基础课。', '已通过'),
('CS202',   'T003', '2026-2027-1', 4, 1, 2, 5,  18, '教学楼D201', 40, 5,  'CS100',           '操作系统是计算机核心课程。', '已通过'),
('ENG101',  'T006', '2026-2027-1', 5, 3, 2, 1,  16, '教学楼E101', 50, 15, NULL,              '英语小班教学效果更佳。', '已通过'),
('CS302',   'T004', '2026-2027-1', 3, 3, 2, 1,  18, '教学楼B301', 40, 0,  'CS100',           '新开计算机网络课程。', '已通过'),
('CS303',   'T008', '2026-2027-1', 5, 5, 2, 1,  16, '教学楼D301', 50, 0,  NULL,              '人工智能入门普及课程。', '已通过'),
('ELEC101', 'T007', '2026-2027-1', 4, 5, 2, 1,  18, '教学楼E201', 60, 0,  NULL,              '物联网科普公选课。', '已通过'),
-- 待审核（3条）
('CS301',   'T001', '2026-2027-1', 5, 5, 3, 5,  18, '教学楼D101', 25, 0,  'CS101,CS201',      '需三节连排。', '待审核'),
('CS100',   'T003', '2026-2027-1', 2, 3, 2, 1,  18, '教学楼A102', 35, 0,  NULL,              '申请平行班，分流选课压力。', '待审核'),
('MATH101', 'T005', '2026-2027-1', 5, 1, 2, 1,  20, '教学楼C302', 80, 0,  NULL,              '申请平行班。', '待审核'),
-- 已驳回（2条，用于查看驳回历史）
('CS202',   'T003', '2025-2026-2', 3, 5, 3, 1,  18, '教学楼D202', 30, 0,  'CS100',           '三节连排实验。', '已驳回'),
('ELEC101', 'T007', '2025-2026-2', 5, 7, 2, 1,  16, '教学楼E202', 40, 0,  NULL,              '公选课申请。', '已驳回');

-- ── 选课记录（模拟完整选课场景：有人在容量内、有人已退课再选、跨班级选课、满员课程）──
INSERT INTO enrollment (student_id, plan_id, status) VALUES
-- plan=1 CS100 程序设计基础（各班分散选课，体现大课特点）
('STU001', 1, '已选'), ('STU004', 1, '已选'), ('STU006', 1, '已选'),
('STU007', 1, '已选'), ('STU008', 1, '已选'), ('STU002', 1, '已选'),
('STU005', 1, '已选'), ('STU009', 1, '已选'), ('STU010', 1, '已选'),
('STU011', 1, '已选'), ('STU003', 1, '已选'), ('STU012', 1, '已选'),
('STU013', 1, '已选'), ('STU014', 1, '已选'), ('STU015', 1, '已选'),
('STU016', 1, '已选'), ('STU017', 1, '已选'), ('STU018', 1, '已选'),
('STU019', 1, '已选'), ('STU020', 1, '已选'),
-- plan=1 退课记录（STU025选过又退了）
('STU025', 1, '已退'),
-- plan=2 CS101 数据结构（需先修CS100，部分学生选）
('STU001', 2, '已选'), ('STU004', 2, '已选'), ('STU006', 2, '已选'),
('STU002', 2, '已选'), ('STU005', 2, '已选'), ('STU009', 2, '已选'),
('STU003', 2, '已选'), ('STU012', 2, '已选'), ('STU014', 2, '已选'),
('STU015', 2, '已选'), ('STU017', 2, '已选'), ('STU018', 2, '已选'),
-- plan=3 CS201 数据库原理
('STU001', 3, '已选'), ('STU004', 3, '已选'), ('STU006', 3, '已选'),
('STU002', 3, '已选'), ('STU005', 3, '已选'), ('STU003', 3, '已选'),
('STU012', 3, '已选'), ('STU014', 3, '已选'), ('STU017', 3, '已选'),
('STU018', 3, '已选'),
-- plan=4 MATH101 高等数学A（大班，跨专业选课）
('STU001', 4, '已选'), ('STU004', 4, '已选'), ('STU006', 4, '已选'),
('STU007', 4, '已选'), ('STU008', 4, '已选'),
('STU002', 4, '已选'), ('STU005', 4, '已选'), ('STU009', 4, '已选'),
('STU010', 4, '已选'), ('STU011', 4, '已选'),
('STU003', 4, '已选'), ('STU012', 4, '已选'), ('STU013', 4, '已选'),
('STU014', 4, '已选'), ('STU015', 4, '已选'), ('STU016', 4, '已选'),
('STU017', 4, '已选'), ('STU018', 4, '已选'), ('STU019', 4, '已选'),
('STU020', 4, '已选'), ('STU021', 4, '已选'), ('STU022', 4, '已选'),
('STU023', 4, '已选'), ('STU024', 4, '已选'), ('STU025', 4, '已选'),
-- plan=5 MATH201 线性代数（新开，仅少数人选）
('STU014', 5, '已选'), ('STU015', 5, '已选'), ('STU016', 5, '已选'),
-- plan=6 CS202 操作系统（选修，5人选）
('STU001', 6, '已选'), ('STU004', 6, '已选'),
('STU002', 6, '已选'), ('STU005', 6, '已选'),
('STU003', 6, '已选'),
-- plan=7 ENG101 大学英语（跨班级选课）
('STU001', 7, '已选'), ('STU006', 7, '已选'), ('STU007', 7, '已选'),
('STU002', 7, '已选'), ('STU009', 7, '已选'), ('STU010', 7, '已选'),
('STU003', 7, '已选'), ('STU012', 7, '已选'),
('STU014', 7, '已选'), ('STU015', 7, '已选'), ('STU016', 7, '已选'),
('STU017', 7, '已选'), ('STU018', 7, '已选'), ('STU019', 7, '已选'),
('STU020', 7, '已选');

-- ── 成绩记录（40+条，覆盖多状态、多分数段、审核流程数据）──
INSERT INTO grade (student_id, plan_id, score, gpa_point, status) VALUES
-- CS100 高分群体（92-98，A档）
('STU001', 1, 92, 4.0, '正常'),
('STU004', 1, 95, 4.0, '正常'),
('STU002', 1, 88, 3.7, '正常'),
('STU005', 1, 82, 3.3, '正常'),
('STU003', 1, 78, 3.0, '正常'),
-- 新增更多成绩分布
('STU006', 1, 71, 2.7, '正常'),
('STU007', 1, 65, 2.3, '正常'),
('STU008', 1, 61, 2.0, '正常'),
('STU009', 1, 55, 0.0, '正常'),  -- 不及格
('STU010', 1, 48, 0.0, '正常'),  -- 不及格
-- CS101 数据结构
('STU001', 2, 90, 4.0, '正常'),
('STU004', 2, 85, 3.7, '正常'),
('STU002', 2, 76, 3.0, '正常'),
('STU005', 2, 68, 2.3, '正常'),
('STU003', 2, 59, 0.0, '正常'),  -- 边界不及格
-- CS201 数据库原理
('STU001', 3, 88, 3.7, '正常'),
('STU004', 3, 91, 4.0, '正常'),
('STU002', 3, 73, 2.7, '正常'),
('STU005', 3, 66, 2.3, '正常'),
('STU003', 3, 52, 0.0, '正常'),
-- MATH101 高等数学（大班，混合分数分布）
('STU001', 4, 81, 3.3, '正常'),
('STU004', 4, 74, 2.7, '正常'),
('STU002', 4, 69, 2.3, '正常'),
('STU005', 4, 62, 2.0, '正常'),
('STU003', 4, 45, 0.0, '正常'),
('STU006', 4, 93, 4.0, '正常'),
('STU007', 4, 57, 0.0, '正常'),  -- 边界不及格
('STU014', 4, 77, 3.0, '正常'),
('STU015', 4, 83, 3.3, '正常'),
('STU016', 4, 58, 0.0, '正常'),
-- CS202 操作系统（选修，部分还未录入）
('STU001', 6, 86, 3.7, '正常'),
('STU004', 6, 79, 3.0, '正常'),
('STU002', 6, 60, 2.0, '正常'),  -- 及格线
('STU005', 6, 42, 0.0, '正常'),  -- 选修挂科
-- ENG101 大学英语（考查课，已录部分学生）
('STU001', 7, 85, 3.7, '正常'),
('STU002', 7, 72, 2.7, '正常'),
('STU003', 7, 91, 4.0, '正常'),
('STU006', 7, 68, 2.3, '正常'),
('STU009', 7, 55, 0.0, '正常'),
-- 待审核成绩（模拟教师提交修改申请后等待管理员审核）
('STU002', 1, 78, 2.7, '待审核'),   -- 原分数，申请修改
-- 已更正成绩（审核通过后的状态）
('STU005', 1, 85, 3.3, '已更正'),   -- 从原分更正为85
-- 退课学生的成绩（之前选了 MENG101，后值退课，现在已是其他课的成绩）
('STU025', 4, 63, 2.0, '正常');

-- ── 密码重置申请（模拟审核工作流）──
INSERT INTO password_reset_request (user_id, reason, status, admin_id, request_time, process_time, comment) VALUES
('STU003', '忘记密码，需要重置', '待审核', NULL, '2026-06-15 14:30:00', NULL, NULL),
('STU007', '连续输入错误多次，密码锁定', '待审核', NULL, '2026-06-17 09:15:00', NULL, NULL),
('T002',  '更换设备后忘记保存密码', '已通过', 'admin', '2026-06-10 10:00:00', '2026-06-10 15:30:00', '已核实身份'),
('STU010', '原密码无法登录', '已驳回', 'admin', '2026-06-12 16:20:00', '2026-06-13 08:45:00', '身份信息不匹配'),
('STU025', '多次尝试登录失败，账户被锁定', '待审核', NULL, '2026-06-18 08:00:00', NULL, NULL);

-- ── 操作日志（模拟最近一周主要操作）──
INSERT INTO operation_log (user_id, log_type, operation, result, log_time, ip_address) VALUES
('admin',  '登录', '管理员登录系统', '成功', '2026-06-18 08:30:00', '127.0.0.1'),
('T001',   '登录', '教师登录系统', '成功', '2026-06-18 08:35:00', '127.0.0.1'),
('STU001', '登录', '学生登录系统', '成功', '2026-06-18 08:40:00', '127.0.0.1'),
('STU025', '登录', '学生登录系统', '失败', '2026-06-18 08:42:00', '127.0.0.1'),
('STU002', '选课', '选课成功: plan_id=7', '成功', '2026-06-18 09:00:00', '127.0.0.1'),
('STU015', '选课', '选课失败(时段): 当前学期选课未开放', '失败', '2026-06-18 09:05:00', '127.0.0.1'),
('STU003', '选课', '选课失败: 课程容量已满', '失败', '2026-06-17 10:30:00', '127.0.0.1'),
('T001',   '成绩', '录入成绩: plan_id=1, 5条', '成功', '2026-06-17 14:00:00', '127.0.0.1'),
('T001',   '成绩', '成绩修改申请: STU002, 78→?, plan_id=1', '成功', '2026-06-17 15:00:00', '127.0.0.1'),
('admin',  '审核', '审核通过: 密码重置 STU010', '成功', '2026-06-13 08:45:00', '127.0.0.1'),
('admin',  '审核', '审核驳回: 成绩修改 T003 plan_id=6', '成功', '2026-06-16 11:00:00', '127.0.0.1'),
('admin',  '系统', '创建学期配置: 2026-2027-2', '成功', '2026-06-15 09:00:00', '127.0.0.1'),
('STU020', '选课', '选课成功: plan_id=4', '成功', '2026-06-14 14:20:00', '127.0.0.1'),
('STU022', '选课', '选课失败: 时间冲突', '失败', '2026-06-14 14:25:00', '127.0.0.1'),
('STU019', '选课', '退课成功: plan_id=5', '成功', '2026-06-13 16:10:00', '127.0.0.1'),
('T005',   '登录', '教师登录系统', '成功', '2026-06-12 08:00:00', '127.0.0.1'),
('admin',  '系统', '创建课程: CS303 人工智能导论', '成功', '2026-06-11 10:00:00', '127.0.0.1'),
('admin',  '系统', '创建教师: T008 林副教授', '成功', '2026-06-11 10:15:00', '127.0.0.1'),
('admin',  '系统', '创建学生: STU020-STU025', '成功', '2026-06-11 10:30:00', '127.0.0.1');

SELECT '===== 数据库 course_management_db v3.0 MySQL 版初始化完成 =====' AS message;
