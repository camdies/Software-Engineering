-- Existing MySQL 8 installations: token revocation and one-current-semester guard.
-- Preferred command (safe to repeat): python -m backend.config.schema_upgrade
-- This SQL file is intended for a one-time manual migration only.
ALTER TABLE user_account
    ADD COLUMN token_version INT NOT NULL DEFAULT 0 AFTER login_fail_count;

ALTER TABLE semester_config
    ADD COLUMN current_guard TINYINT
        GENERATED ALWAYS AS (CASE WHEN is_current = 1 THEN 1 ELSE NULL END) STORED,
    ADD CONSTRAINT UQ_semester_single_current UNIQUE (current_guard);

ALTER TABLE operation_log
    ADD COLUMN target_id VARCHAR(20) NULL,
    ADD COLUMN resource_type VARCHAR(30) NULL,
    ADD COLUMN semester VARCHAR(20) NULL,
    ADD COLUMN reason VARCHAR(500) NULL,
    ADD COLUMN request_id VARCHAR(64) NULL;

ALTER TABLE operation_log DROP CHECK CK_log_type;
ALTER TABLE operation_log
    ADD CONSTRAINT CK_log_type
    CHECK (log_type IN ('登录', '选课', '成绩', '审核', '系统', '导出'));
