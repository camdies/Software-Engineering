-- Existing SQL Server installations: token revocation and one-current-semester guard.
-- Preferred command (safe to repeat): python -m backend.config.schema_upgrade
-- This SQL file is intended for a one-time manual migration only.
ALTER TABLE dbo.user_account
    ADD token_version INT NOT NULL CONSTRAINT DF_user_token_version DEFAULT 0;
GO

CREATE UNIQUE INDEX UX_semester_single_current
ON dbo.semester_config(is_current)
WHERE is_current = 1;
GO

ALTER TABLE dbo.operation_log ADD
    target_id NVARCHAR(20) NULL,
    resource_type NVARCHAR(30) NULL,
    semester NVARCHAR(20) NULL,
    reason NVARCHAR(500) NULL,
    request_id NVARCHAR(64) NULL;
GO

ALTER TABLE dbo.operation_log DROP CONSTRAINT CK_log_type;
ALTER TABLE dbo.operation_log ADD CONSTRAINT CK_log_type
CHECK (log_type IN (N'登录', N'选课', N'成绩', N'审核', N'系统', N'导出'));
GO
