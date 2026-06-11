"""
backend/controllers/teacher_controller.py - 教师业务控制器

提供教师专属业务逻辑：授课信息查询、成绩录入等。
"""

from datetime import datetime

from backend.models.base import DatabaseManager
from backend.models.course_plan import CoursePlan
from backend.models.enrollment import Enrollment
from backend.models.student import Student
from backend.models.operation_log import OperationLog
from backend.utils.log_util import get_logger

logger = get_logger("teacher_controller")


class TeacherController:
    """教师业务控制器。

    提供教师角色的业务逻辑支持。
    """

    def __init__(self):
        self._db = DatabaseManager.get_instance()

    def get_teaching_plans(self, teacher_id: str,
                           semester: str = None) -> list:
        """获取教师的开课计划列表。

        Args:
            teacher_id: 教师工号。
            semester: 学期过滤条件。

        Returns:
            list: 开课计划字典列表。
        """
        try:
            with self._db.get_session() as session:
                query = session.query(CoursePlan).filter_by(
                    teacher_id=teacher_id)
                if semester:
                    query = query.filter(CoursePlan.semester == semester)
                plans = query.all()
                return [p.to_dict() for p in plans]
        except Exception as e:
            logger.error(f"查询教师授课计划异常: {e}", exc_info=True)
            return []

    def get_enrolled_students(self, plan_id: int) -> list:
        """获取某课程的选课学生列表。

        Args:
            plan_id: 开课计划ID。

        Returns:
            list: 学生信息字典列表。
        """
        try:
            with self._db.get_session() as session:
                results = (
                    session.query(Student, Enrollment)
                    .join(Enrollment, Student.student_id == Enrollment.student_id)
                    .filter(
                        Enrollment.plan_id == plan_id,
                        Enrollment.status == "已选"
                    )
                    .all()
                )
                return [
                    {**s.to_dict(), "enroll_id": e.enroll_id}
                    for s, e in results
                ]
        except Exception as e:
            logger.error(f"查询选课学生列表异常: {e}", exc_info=True)
            return []
