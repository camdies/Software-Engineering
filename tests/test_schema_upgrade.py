import unittest
from unittest.mock import MagicMock, patch


class TestSchemaUpgrade(unittest.TestCase):
    def test_mysql_old_schema_adds_token_version_and_related_columns(self):
        from backend.config import schema_upgrade

        engine = MagicMock()
        inspector = MagicMock()
        inspector.get_unique_constraints.return_value = []
        inspector.get_indexes.return_value = []
        inspector.get_check_constraints.return_value = [
            {"name": "CK_log_type", "sqltext": "log_type IN ('登录', '系统')"}
        ]

        with patch.object(schema_upgrade, "_assert_upgradeable_schema"), patch.object(
            schema_upgrade,
            "_column_names",
            side_effect=[set(), set(), set()],
        ), patch.object(schema_upgrade, "inspect", return_value=inspector), patch.object(
            schema_upgrade, "_execute"
        ) as execute:
            schema_upgrade.ensure_schema_current(engine, "mysql")

        statements = [item.args[1] for item in execute.call_args_list]
        self.assertTrue(any("ADD COLUMN token_version" in sql for sql in statements))
        self.assertTrue(any("ADD COLUMN current_guard" in sql for sql in statements))
        self.assertTrue(any("ADD COLUMN request_id" in sql for sql in statements))
        self.assertTrue(any("UQ_semester_single_current" in sql for sql in statements))
        self.assertTrue(any("DROP CHECK CK_log_type" in sql for sql in statements))
        self.assertTrue(any("导出" in sql for sql in statements))

    def test_mysql_current_schema_is_idempotent(self):
        from backend.config import schema_upgrade

        engine = MagicMock()
        inspector = MagicMock()
        inspector.get_unique_constraints.return_value = [
            {"name": "UQ_semester_single_current"}
        ]
        inspector.get_indexes.return_value = []
        inspector.get_check_constraints.return_value = [
            {"name": "CK_log_type", "sqltext": "log_type IN ('系统', '导出')"}
        ]
        operation_columns = set(schema_upgrade._MYSQL_OPERATION_LOG_COLUMNS)

        with patch.object(schema_upgrade, "_assert_upgradeable_schema"), patch.object(
            schema_upgrade,
            "_column_names",
            side_effect=[{"token_version"}, {"current_guard"}, operation_columns],
        ), patch.object(schema_upgrade, "inspect", return_value=inspector), patch.object(
            schema_upgrade, "_execute"
        ) as execute:
            schema_upgrade.ensure_schema_current(engine, "mysql")

        execute.assert_not_called()

    def test_multiple_current_semesters_fail_before_alter(self):
        from backend.config import schema_upgrade

        engine = MagicMock()
        inspector = MagicMock()
        inspector.get_table_names.return_value = list(schema_upgrade._REQUIRED_TABLES)
        engine.connect.return_value.__enter__.return_value.execute.return_value.scalar_one.return_value = 2

        with patch.object(schema_upgrade, "inspect", return_value=inspector), patch.object(
            schema_upgrade, "_execute"
        ) as execute:
            with self.assertRaises(schema_upgrade.SchemaUpgradeError):
                schema_upgrade.ensure_schema_current(engine, "mysql")

        execute.assert_not_called()


if __name__ == "__main__":
    unittest.main()
