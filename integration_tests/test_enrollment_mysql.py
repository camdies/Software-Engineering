"""Real MySQL row-lock gate; run only in CI with EDUMGMT_TEST_MYSQL_URL."""

import os
import threading
import unittest
from contextlib import contextmanager

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker


class _IntegrationDatabase:
    is_mssql = False

    def __init__(self, url):
        self.engine = create_engine(url, pool_pre_ping=True)
        self.Session = sessionmaker(bind=self.engine)

    @contextmanager
    def get_session(self):
        session = self.Session()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()


class TestEnrollmentMySQL(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        url = os.environ["EDUMGMT_TEST_MYSQL_URL"]
        cls.db = _IntegrationDatabase(url)

    def setUp(self):
        password_hash = "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6Ttx9YJK5x2Kp7f3Q6s7u8v9w0xyz"
        with self.db.engine.begin() as connection:
            connection.execute(text("DELETE FROM operation_log"))
            connection.execute(text("DELETE FROM grade"))
            connection.execute(text("DELETE FROM enrollment"))
            connection.execute(text("DELETE FROM course_plan"))
            connection.execute(text("DELETE FROM course"))
            connection.execute(text("DELETE FROM teacher"))
            connection.execute(text("DELETE FROM student"))
            connection.execute(text("DELETE FROM user_account WHERE user_id IN ('T_LOCK','S_LOCK_1','S_LOCK_2')"))
            for user_id, role in (("T_LOCK", "teacher"), ("S_LOCK_1", "student"), ("S_LOCK_2", "student")):
                connection.execute(text(
                    "INSERT INTO user_account(user_id,password_hash,role,token_version) "
                    "VALUES (:id,:password,:role,0)"
                ), {"id": user_id, "password": password_hash, "role": role})
            connection.execute(text("INSERT INTO teacher(teacher_id,name) VALUES ('T_LOCK','并发教师')"))
            connection.execute(text("INSERT INTO student(student_id,name) VALUES ('S_LOCK_1','学生一'),('S_LOCK_2','学生二')"))
            connection.execute(text("INSERT INTO course(course_id,course_name,credit) VALUES ('LOCK101','并发课程',2)"))
            result = connection.execute(text(
                "INSERT INTO course_plan(course_id,teacher_id,semester,weekday,period_start,period_count,start_week,end_week,capacity,enrolled,status) "
                "VALUES ('LOCK101','T_LOCK','2026-2027-1',1,1,2,1,18,1,0,'已通过')"
            ))
            self.plan_id = result.lastrowid

    def test_capacity_one_race_has_exactly_one_winner(self):
        import backend.models.user_account  # noqa: F401
        import backend.models.teacher  # noqa: F401
        from backend.controllers.enrollment_controller import EnrollmentController

        barrier = threading.Barrier(2)
        results = []

        def attempt(student_id):
            controller = EnrollmentController.__new__(EnrollmentController)
            controller._db = self.db
            controller._check_enrollment_period = lambda session=None: {"valid": True, "message": ""}
            barrier.wait()
            results.append(controller.select_course(student_id, self.plan_id))

        threads = [
            threading.Thread(target=attempt, args=("S_LOCK_1",)),
            threading.Thread(target=attempt, args=("S_LOCK_2",)),
        ]
        for thread in threads: thread.start()
        for thread in threads: thread.join()

        self.assertEqual(sum(item["success"] for item in results), 1)
        with self.db.engine.connect() as connection:
            enrolled = connection.execute(text(
                "SELECT enrolled FROM course_plan WHERE plan_id=:id"
            ), {"id": self.plan_id}).scalar_one()
            rows = connection.execute(text(
                "SELECT COUNT(*) FROM enrollment WHERE plan_id=:id AND status='已选'"
            ), {"id": self.plan_id}).scalar_one()
        self.assertEqual(enrolled, 1)
        self.assertEqual(rows, 1)


if __name__ == "__main__":
    unittest.main()
