-- ========================================================
-- 学生选课及成绩管理系统 - 数据库DDL脚本
-- 数据库: course_management_db
-- 字符集: utf8mb4 | 排序规则: utf8mb4_unicode_ci
-- ========================================================

-- 创建数据库
CREATE DATABASE IF NOT EXISTS course_management_db
    DEFAULT CHARACTER SET utf8mb4
    DEFAULT COLLATE utf8mb4_unicode_ci;

USE course_management_db;

-- ========================================================
-- 1. user_account - 用户账号表
-- ========================================================
DROP TABLE IF EXISTS operation_log;
DROP TABLE IF EXISTS grade;
DROP TABLE IF EXISTS enrollment;
DROP TABLE IF EXISTS course_plan;
DROP TABLE IF EXISTS course;
DROP TABLE IF EXISTS teacher;
DROP TABLE IF EXISTS student;
DROP TABLE IF EXISTS user_account;

CREATE TABLE user_account (
    user_id         VARCHAR(20)     NOT NULL COMMENT '用户账号（主键）',
    password_hash   VARCHAR(255)    NOT NULL COMMENT 'bcrypt密码哈希',
    role            ENUM('admin','teacher','student') NOT NULL COMMENT '用户角色',
    last_login      DATETIME        COMMENT '最后登录时间',
    is_locked       TINYINT(1)      DEFAULT 0 COMMENT '账户锁定: 0未锁定 1已锁定',
    login_fail_count INT            DEFAULT 0 COMMENT '连续登录失败次数',
    created_at      DATETIME        DEFAULT CURRENT_TIMESTAMP COMMENT '记录创建时间',
    PRIMARY KEY (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    COMMENT='用户账号表';

-- ========================================================
-- 2. student - 学生信息表
-- ========================================================
CREATE TABLE student (
    student_id      VARCHAR(20)     NOT NULL COMMENT '学生学号（主键）',
    name            VARCHAR(50)     NOT NULL COMMENT '学生姓名',
    major           VARCHAR(100)    COMMENT '主修专业',
    class_name      VARCHAR(50)     COMMENT '所在班级',
    contact         VARCHAR(20)     COMMENT '联系方式',
    created_at      DATETIME        DEFAULT CURRENT_TIMESTAMP COMMENT '记录创建时间',
    PRIMARY KEY (student_id),
    CONSTRAINT fk_student_user FOREIGN KEY (student_id)
        REFERENCES user_account(user_id) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    COMMENT='学生信息表';

-- ========================================================
-- 3. teacher - 教师信息表
-- ========================================================
CREATE TABLE teacher (
    teacher_id      VARCHAR(20)     NOT NULL COMMENT '教师工号（主键）',
    name            VARCHAR(50)     NOT NULL COMMENT '教师姓名',
    college         VARCHAR(100)    COMMENT '所属学院',
    contact         VARCHAR(20)     COMMENT '联系方式',
    created_at      DATETIME        DEFAULT CURRENT_TIMESTAMP COMMENT '记录创建时间',
    PRIMARY KEY (teacher_id),
    CONSTRAINT fk_teacher_user FOREIGN KEY (teacher_id)
        REFERENCES user_account(user_id) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    COMMENT='教师信息表';

-- ========================================================
-- 4. course - 课程计划表
-- ========================================================
CREATE TABLE course (
    course_id       VARCHAR(20)     NOT NULL COMMENT '课程代码（主键）',
    course_name     VARCHAR(100)    NOT NULL COMMENT '课程名称',
    credit          DECIMAL(3,1)    COMMENT '学分数（0.5-20，0.5步进）',
    hours           INT             COMMENT '学时数',
    exam_type       ENUM('考试','考查') COMMENT '考核方式',
    created_at      DATETIME        DEFAULT CURRENT_TIMESTAMP COMMENT '记录创建时间',
    PRIMARY KEY (course_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    COMMENT='课程计划表';

-- ========================================================
-- 5. course_plan - 开课记录表
-- ========================================================
CREATE TABLE course_plan (
    plan_id         INT             NOT NULL AUTO_INCREMENT COMMENT '开课计划ID（主键，自增）',
    course_id       VARCHAR(20)     NOT NULL COMMENT '课程代码（外键）',
    teacher_id      VARCHAR(20)     NOT NULL COMMENT '教师工号（外键）',
    semester        VARCHAR(20)     NOT NULL COMMENT '开课学期，如2026-2027-1',
    time_slot       VARCHAR(50)     COMMENT '上课时间，如周一1-2节',
    location        VARCHAR(100)    COMMENT '上课地点',
    capacity        INT             COMMENT '课程容量上限',
    enrolled        INT             DEFAULT 0 COMMENT '已选人数',
    prerequisite    VARCHAR(200)    COMMENT '先修课程代码，多个以逗号分隔',
    status          ENUM('开课','停课') DEFAULT '开课' COMMENT '开课状态',
    created_at      DATETIME        DEFAULT CURRENT_TIMESTAMP COMMENT '记录创建时间',
    PRIMARY KEY (plan_id),
    INDEX idx_course_semester (course_id, semester),
    CONSTRAINT fk_course_plan_course FOREIGN KEY (course_id)
        REFERENCES course(course_id) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_course_plan_teacher FOREIGN KEY (teacher_id)
        REFERENCES teacher(teacher_id) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    COMMENT='开课记录表';

-- ========================================================
-- 6. enrollment - 选课记录表
-- ========================================================
CREATE TABLE enrollment (
    enroll_id       INT             NOT NULL AUTO_INCREMENT COMMENT '选课记录ID（主键，自增）',
    student_id      VARCHAR(20)     NOT NULL COMMENT '学生学号（外键）',
    plan_id         INT             NOT NULL COMMENT '开课计划ID（外键）',
    enroll_time     DATETIME        NOT NULL COMMENT '选课时间',
    status          ENUM('已选','已退') DEFAULT '已选' COMMENT '选课状态',
    created_at      DATETIME        DEFAULT CURRENT_TIMESTAMP COMMENT '记录创建时间',
    PRIMARY KEY (enroll_id),
    UNIQUE INDEX idx_enrollment_student_plan (student_id, plan_id),
    CONSTRAINT fk_enrollment_student FOREIGN KEY (student_id)
        REFERENCES student(student_id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_enrollment_plan FOREIGN KEY (plan_id)
        REFERENCES course_plan(plan_id) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    COMMENT='选课记录表';

-- ========================================================
-- 7. grade - 成绩记录表
-- ========================================================
CREATE TABLE grade (
    grade_id        INT             NOT NULL AUTO_INCREMENT COMMENT '成绩记录ID（主键，自增）',
    student_id      VARCHAR(20)     NOT NULL COMMENT '学生学号（外键）',
    plan_id         INT             NOT NULL COMMENT '开课计划ID（外键）',
    score           INT             COMMENT '百分制成绩（0-100）',
    gpa_point       DECIMAL(3,2)    COMMENT '对应绩点（0.00-4.00）',
    record_time     DATETIME        COMMENT '成绩录入时间',
    status          ENUM('正常','待审核','已更正') DEFAULT '正常' COMMENT '成绩状态',
    modify_reason   VARCHAR(500)    COMMENT '成绩修改原因',
    created_at      DATETIME        DEFAULT CURRENT_TIMESTAMP COMMENT '记录创建时间',
    PRIMARY KEY (grade_id),
    INDEX idx_grade_student_plan (student_id, plan_id),
    CONSTRAINT fk_grade_student FOREIGN KEY (student_id)
        REFERENCES student(student_id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_grade_plan FOREIGN KEY (plan_id)
        REFERENCES course_plan(plan_id) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT chk_score CHECK (score >= 0 AND score <= 100)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    COMMENT='成绩记录表';

-- ========================================================
-- 8. operation_log - 操作日志表
-- ========================================================
CREATE TABLE operation_log (
    log_id          INT             NOT NULL AUTO_INCREMENT COMMENT '日志ID（主键，自增）',
    user_id         VARCHAR(20)     NOT NULL COMMENT '操作用户ID',
    log_type        ENUM('登录','选课','成绩','系统') NOT NULL COMMENT '操作类型',
    operation       VARCHAR(200)    NOT NULL COMMENT '操作描述',
    result          ENUM('成功','失败') NOT NULL COMMENT '操作结果',
    log_time        DATETIME        NOT NULL COMMENT '操作时间',
    ip_address      VARCHAR(50)     COMMENT '操作IP地址',
    created_at      DATETIME        DEFAULT CURRENT_TIMESTAMP COMMENT '记录创建时间',
    PRIMARY KEY (log_id),
    INDEX idx_log_user_time (user_id, log_time)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    COMMENT='操作日志表';

-- ========================================================
-- 测试数据插入
-- ========================================================

-- 管理员账号（密码: admin123 的bcrypt哈希）
INSERT INTO user_account (user_id, password_hash, role, is_locked, login_fail_count)
VALUES ('admin', '$2b$12$LJ3m4ys3Lk0TSwBCmBfO7OWCPNpLVKpDGS5yXhBXJBBx8sGLLtJQm',
        'admin', 0, 0);

-- 教师账号（密码: 123456）
INSERT INTO user_account (user_id, password_hash, role, is_locked, login_fail_count)
VALUES
('T001', '$2b$12$LJ3m4ys3Lk0TSwBCmBfO7OWCPNpLVKpDGS5yXhBXJBBx8sGLLtJQm',
 'teacher', 0, 0),
('T002', '$2b$12$LJ3m4ys3Lk0TSwBCmBfO7OWCPNpLVKpDGS5yXhBXJBBx8sGLLtJQm',
 'teacher', 0, 0);

INSERT INTO teacher (teacher_id, name, college, contact)
VALUES
('T001', '张教授', '计算机科学与技术学院', '13800001001'),
('T002', '李副教授', '数学与统计学院', '13800001002');

-- 学生账号
INSERT INTO user_account (user_id, password_hash, role, is_locked, login_fail_count)
VALUES
('STU001', '$2b$12$LJ3m4ys3Lk0TSwBCmBfO7OWCPNpLVKpDGS5yXhBXJBBx8sGLLtJQm',
 'student', 0, 0),
('STU002', '$2b$12$LJ3m4ys3Lk0TSwBCmBfO7OWCPNpLVKpDGS5yXhBXJBBx8sGLLtJQm',
 'student', 0, 0),
('STU003', '$2b$12$LJ3m4ys3Lk0TSwBCmBfO7OWCPNpLVKpDGS5yXhBXJBBx8sGLLtJQm',
 'student', 0, 0);

INSERT INTO student (student_id, name, major, class_name, contact)
VALUES
('STU001', '王小明', '计算机科学与技术', '计科2101', '13900002001'),
('STU002', '赵小红', '软件工程', '软工2102', '13900002002'),
('STU003', '刘小刚', '数据科学', '数据2101', '13900002003');

-- 课程
INSERT INTO course (course_id, course_name, credit, hours, exam_type)
VALUES
('CS100', '程序设计基础', 4.0, 64, '考试'),
('CS101', '数据结构', 4.0, 64, '考试'),
('CS201', '数据库原理', 3.0, 48, '考试'),
('CS301', '软件工程', 3.0, 48, '考查'),
('MATH101', '高等数学', 5.0, 80, '考试');

-- 开课计划
INSERT INTO course_plan (course_id, teacher_id, semester, time_slot,
                         location, capacity, enrolled, prerequisite, status)
VALUES
('CS100', 'T001', '2026-2027-1', '周一1-2节', '教学楼A101', 30, 3, NULL, '开课'),
('CS101', 'T001', '2026-2027-1', '周一3-4节', '教学楼A201', 35, 0, 'CS100', '开课'),
('CS201', 'T001', '2026-2027-1', '周二1-2节', '教学楼B101', 30, 2, 'CS100', '开课'),
('MATH101', 'T002', '2026-2027-1', '周三1-2节', '教学楼C301', 50, 3, NULL, '开课'),
('CS301', 'T001', '2026-2027-1', '周四5-6节', '教学楼D101', 25, 0, 'CS101,CS201', '开课');

-- 选课记录
INSERT INTO enrollment (student_id, plan_id, enroll_time, status)
VALUES
('STU001', 1, NOW(), '已选'),
('STU002', 1, NOW(), '已选'),
('STU003', 1, NOW(), '已选'),
('STU001', 3, NOW(), '已选'),
('STU002', 3, NOW(), '已选'),
('STU001', 4, NOW(), '已选'),
('STU002', 4, NOW(), '已选'),
('STU003', 4, NOW(), '已选');
