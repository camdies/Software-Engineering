import unittest
from pathlib import Path


class TestSchemaContract(unittest.TestCase):
    def test_mysql_and_mssql_security_constraints_are_synchronized(self):
        root = Path(__file__).resolve().parents[1]
        mysql = (root / "backend/config/init_database_mysql.sql").read_text(encoding="utf-8")
        mssql = (root / "backend/config/init_database.sql").read_text(encoding="utf-8")
        for ddl in (mysql, mssql):
            with self.subTest(dialect="mysql" if ddl is mysql else "mssql"):
                self.assertIn("token_version", ddl)
                self.assertIn("UQ_enrollment_student_plan", ddl)
                self.assertIn("request_id", ddl)
                self.assertIn("resource_type", ddl)
        self.assertIn("UQ_semester_single_current", mysql)
        self.assertIn("UX_semester_single_current", mssql)
        self.assertIn("WHERE is_current = 1", mssql)


if __name__ == "__main__":
    unittest.main()
