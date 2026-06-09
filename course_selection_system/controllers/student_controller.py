"""
controllers/student_controller.py - 学生业务控制器

提供学生专属业务逻辑：可选课程查询、已选课程查询、成绩查询等。
"""

from models.base import DatabaseManager
from models.course_plan import CoursePlan
from models.course import Course
from models.enrollment import Enrollment
from models.grade import Grade
from utils.log_util import get_logger

logger = get_logger("student_controller")


class StudentController:
    """学生业务控制器。

    提供学生角色的业务逻辑支持。
    """

    def __init__(self):
        self._db = DatabaseManager.get_instance()

    def get_available_courses(self, semester: str = None) -> list:
        """获取可选课程列表。

        Args:
            semester: 学期过滤条件。

        Returns:
            list: 课程信息字典列表（含教师姓名、余量等）。
        """
        try:
            with self._db.get_session() as session:
                query = (
                    session.query(CoursePlan, Course)
                    .join(Course,
                          CoursePlan.course_id == Course.course_id)
                    .filter(CoursePlan.status == "开课")
                )
                if semester:
                    query = query.filter(
                        CoursePlan.semester == semester)

                results = query.all()
                courses = []
                for plan, course in results:
                    courses.append({
                        **course.to_dict(),
                        "plan_id": plan.plan_id,
                        "teacher_id": plan.teacher_id,
                        "time_slot": plan.time_slot,
                        "location": plan.location,
                        "capacity": plan.capacity,
                        "enrolled": plan.enrolled or 0,
                        "available": (plan.capacity or 0) - (
                            plan.enrolled or 0),
                    })
                return courses
        except Exception as e:
            logger.error(f"查询可选课程异常: {e}", exc_info=True)
            return []

    def get_my_courses(self, student_id: str) -> list:
        """获取学生已选课程列表。

        Args:
            student_id: 学生学号。

        Returns:
            list: 已选课程字典列表。
        """
        try:
            with self._db.get_session() as session:
                results = (
                    session.query(Enrollment, CoursePlan, Course)
                    .join(CoursePlan,
                          Enrollment.plan_id == CoursePlan.plan_id)
                    .join(Course,
                          CoursePlan.course_id == Course.course_id)
                    .filter(
                        Enrollment.student_id == student_id,
                        Enrollment.status == "已选",
                    )
                    .all()
                )
                return [
                    {
                        **c.to_dict(),
                        "plan_id": cp.plan_id,
                        "time_slot": cp.time_slot,
                        "enroll_time": e.enroll_time.isoformat()
                        if e.enroll_time else None,
                    }
                    for e, cp, c in results
                ]
        except Exception as e:
            logger.error(f"查询已选课程异常: {e}", exc_info=True)
            return []

    def get_my_grades(self, student_id: str) -> list:
        """获取学生成绩列表。

        Args:
            student_id: 学生学号。

        Returns:
            list: 成绩字典列表（含课程名、学分等）。
        """
        try:
            with self._db.get_session() as session:
                results = (
                    session.query(Grade, CoursePlan, Course)
                    .join(CoursePlan,
                          Grade.plan_id == CoursePlan.plan_id)
                    .join(Course,
                          CoursePlan.course_id == Course.course_id)
                    .filter(Grade.student_id == student_id)
                    .all()
                )
                return [
                    {
                        **g.to_dict(),
                        "course_name": c.course_name,
                        "credit": float(c.credit) if c.credit else 0,
                        "semester": cp.semester,
                    }
                    for g, cp, c in results
                ]
        except Exception as e:
            logger.error(f"查询成绩列表异常: {e}", exc_info=True)
            return []
