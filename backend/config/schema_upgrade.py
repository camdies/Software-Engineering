"""Safe, idempotent schema upgrades for existing EduMgmt installations.

The bundled database is persistent, so updating the ORM and the initialization
DDL is not enough for users who already have ``mysql-portable/data``.  This
module converges the small set of backward-compatible schema additions needed
by the running application before the first ORM query is issued.
"""

from __future__ import annotations

from collections.abc import Iterable

from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine


class SchemaUpgradeError(RuntimeError):
    """Raised when an automatic upgrade cannot be applied safely."""


_REQUIRED_TABLES = {"user_account", "semester_config", "operation_log"}

_MYSQL_OPERATION_LOG_COLUMNS = {
    "target_id": "VARCHAR(20) NULL",
    "resource_type": "VARCHAR(30) NULL",
    "semester": "VARCHAR(20) NULL",
    "reason": "VARCHAR(500) NULL",
    "request_id": "VARCHAR(64) NULL",
}

_MSSQL_OPERATION_LOG_COLUMNS = {
    "target_id": "NVARCHAR(20) NULL",
    "resource_type": "NVARCHAR(30) NULL",
    "semester": "NVARCHAR(20) NULL",
    "reason": "NVARCHAR(500) NULL",
    "request_id": "NVARCHAR(64) NULL",
}


def _names(items: Iterable[dict], key: str = "name") -> set[str]:
    return {str(item.get(key) or "").lower() for item in items}


def _column_names(engine: Engine, table: str, schema: str | None = None) -> set[str]:
    return _names(inspect(engine).get_columns(table, schema=schema))


def _execute(engine: Engine, statement: str) -> None:
    with engine.begin() as connection:
        connection.execute(text(statement))


def _assert_upgradeable_schema(engine: Engine, schema: str | None = None) -> None:
    tables = {name.lower() for name in inspect(engine).get_table_names(schema=schema)}
    missing = sorted(_REQUIRED_TABLES - tables)
    if missing:
        raise SchemaUpgradeError(
            "数据库尚未完成初始化，缺少数据表: " + ", ".join(missing)
        )

    qualified = f"{schema}.semester_config" if schema else "semester_config"
    with engine.connect() as connection:
        current_count = connection.execute(
            text(f"SELECT COUNT(*) FROM {qualified} WHERE is_current = 1")
        ).scalar_one()
    if current_count > 1:
        raise SchemaUpgradeError(
            "semester_config 存在多条当前学期，无法安全建立唯一约束；"
            "请先仅保留一条 is_current=1"
        )


def _upgrade_mysql(engine: Engine) -> None:
    _assert_upgradeable_schema(engine)

    user_columns = _column_names(engine, "user_account")
    if "token_version" not in user_columns:
        _execute(
            engine,
            "ALTER TABLE user_account ADD COLUMN token_version "
            "INT NOT NULL DEFAULT 0 AFTER login_fail_count",
        )

    semester_columns = _column_names(engine, "semester_config")
    if "current_guard" not in semester_columns:
        _execute(
            engine,
            "ALTER TABLE semester_config ADD COLUMN current_guard TINYINT "
            "GENERATED ALWAYS AS "
            "(CASE WHEN is_current = 1 THEN 1 ELSE NULL END) STORED",
        )

    semester_inspector = inspect(engine)
    unique_names = _names(
        semester_inspector.get_unique_constraints("semester_config")
    ) | _names(semester_inspector.get_indexes("semester_config"))
    if "uq_semester_single_current" not in unique_names:
        _execute(
            engine,
            "ALTER TABLE semester_config ADD CONSTRAINT "
            "UQ_semester_single_current UNIQUE (current_guard)",
        )

    operation_columns = _column_names(engine, "operation_log")
    for name, definition in _MYSQL_OPERATION_LOG_COLUMNS.items():
        if name not in operation_columns:
            _execute(
                engine,
                f"ALTER TABLE operation_log ADD COLUMN {name} {definition}",
            )

    checks = inspect(engine).get_check_constraints("operation_log")
    log_type_check = next(
        (item for item in checks if str(item.get("name") or "").lower() == "ck_log_type"),
        None,
    )
    check_sql = str((log_type_check or {}).get("sqltext") or "")
    if "导出" not in check_sql:
        if log_type_check is not None:
            _execute(engine, "ALTER TABLE operation_log DROP CHECK CK_log_type")
        _execute(
            engine,
            "ALTER TABLE operation_log ADD CONSTRAINT CK_log_type "
            "CHECK (log_type IN ('登录', '选课', '成绩', '审核', '系统', '导出'))",
        )


def _upgrade_mssql(engine: Engine) -> None:
    schema = "dbo"
    _assert_upgradeable_schema(engine, schema=schema)

    user_columns = _column_names(engine, "user_account", schema=schema)
    if "token_version" not in user_columns:
        _execute(
            engine,
            "ALTER TABLE dbo.user_account ADD token_version INT NOT NULL "
            "CONSTRAINT DF_user_token_version DEFAULT 0",
        )

    semester_inspector = inspect(engine)
    index_names = _names(
        semester_inspector.get_indexes("semester_config", schema=schema)
    )
    if "ux_semester_single_current" not in index_names:
        _execute(
            engine,
            "CREATE UNIQUE INDEX UX_semester_single_current "
            "ON dbo.semester_config(is_current) WHERE is_current = 1",
        )

    operation_columns = _column_names(engine, "operation_log", schema=schema)
    for name, definition in _MSSQL_OPERATION_LOG_COLUMNS.items():
        if name not in operation_columns:
            _execute(
                engine,
                f"ALTER TABLE dbo.operation_log ADD {name} {definition}",
            )

    checks = inspect(engine).get_check_constraints("operation_log", schema=schema)
    log_type_check = next(
        (item for item in checks if str(item.get("name") or "").lower() == "ck_log_type"),
        None,
    )
    check_sql = str((log_type_check or {}).get("sqltext") or "")
    if "导出" not in check_sql:
        if log_type_check is not None:
            _execute(
                engine,
                "ALTER TABLE dbo.operation_log DROP CONSTRAINT CK_log_type",
            )
        _execute(
            engine,
            "ALTER TABLE dbo.operation_log ADD CONSTRAINT CK_log_type "
            "CHECK (log_type IN (N'登录', N'选课', N'成绩', N'审核', N'系统', N'导出'))",
        )


def ensure_schema_current(engine: Engine, driver: str) -> None:
    """Apply required additive upgrades and safely tolerate repeated runs."""

    normalized = (driver or "").strip().lower()
    if normalized == "mysql":
        _upgrade_mysql(engine)
        return
    if normalized == "mssql":
        _upgrade_mssql(engine)
        return
    raise SchemaUpgradeError(f"不支持自动升级的数据库驱动: {driver}")


def main() -> int:
    """Upgrade the configured database from the command line."""

    from backend.models.base import DatabaseManager

    manager = DatabaseManager.get_instance()
    # DatabaseManager already runs this during initialization.  Calling it
    # again here intentionally proves that the upgrade is idempotent.
    ensure_schema_current(manager.engine, manager._driver)
    print("数据库结构已是最新版本。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
