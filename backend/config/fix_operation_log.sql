-- fix_operation_log.sql — 重建 operation_log 表修复 CHECK 约束字符集
USE course_management_db;
DROP TABLE IF EXISTS operation_log;
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
    CONSTRAINT CK_log_type CHECK (log_type IN ('登录','选课','成绩','审核','系统')),
    CONSTRAINT CK_log_result CHECK (result IN ('成功','失败')),
    INDEX IX_log_user_time (user_id, log_time)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
