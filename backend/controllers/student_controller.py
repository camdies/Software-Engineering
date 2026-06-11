"""
backend/controllers/student_controller.py - 学生业务控制器

提供学生专属业务逻辑：可选课程查询、已选课程查询、成绩查询等。
"""

from backend.models.base import DatabaseManager
from backend.models.course_plan import CoursePlan
from backend.models.course import Course
from backend.models.enrollment import Enrollment
from backend.models.grade import Grade
from backend.utils.log_util import get_logger

logger = get_logger("student_controller")


class StudentController:
    """学生业务控制器。

    提供学生角色的业务逻辑支持。
    """

    def __init__(self):
        self._db = DatabaseManager.get_instance()

    def get_available_courses(self, semester: str = None,
                              department: str = None,
                              credit_range: str = None,
                              weekday: int = None,
                              exam_type: str = None,
                              course_type: str = None) -> list:
        """获取可选课程列表。

        Args:
            semester: 学期过滤条件。
            department: 院系过滤条件。
            credit_range: 学分范围（如"0-2","2-4","4-6"）。
            weekday: 上课日过滤条件。
            exam_type: 考核方式过滤条件。
            course_type: 课程类型过滤条件。

        Returns:
            list: 课程信息字典列表（含教师姓名、余量等）。
        """
        try:
            with self._db.get_session() as session:
                from backend.models.teacher import Teacher

                query = (
                    session.query(CoursePlan, Course, Teacher)
                    .join(Course,
                          CoursePlan.course_id == Course.course_id)
                    .join(Teacher,
                          CoursePlan.teacher_id == Teacher.teacher_id)
                    .filter(CoursePlan.status == "已通过")
                )
                if semester:
                    query = query.filter(
                        CoursePlan.semester == semester)
                if department:
                    query = query.filter(
                        Course.department == department)
                if credit_range:
                    parts = credit_range.split("-")
                    if len(parts) == 2:
                        query = query.filter(
                            Course.credit >= float(parts[0]),
                            Course.credit <= float(parts[1]))
                if weekday:
                    query = query.filter(
                        CoursePlan.weekday == int(weekday))
                if exam_type:
                    query = query.filter(
                        Course.exam_type == exam_type)
                if course_type:
                    query = query.filter(
                        Course.course_type == course_type)

                results = query.all()
                courses = []
                for plan, course, teacher in results:
                    courses.append({
                        **course.to_dict(),
                        "plan_id": plan.plan_id,
                        "teacher_id": plan.teacher_id,
                        "teacher_name": teacher.name,
                        "time_slot": plan.time_slot_display,
                        "weekday": plan.weekday,
                        "period_start": plan.period_start,
                        "period_count": plan.period_count,
                        "start_week": plan.start_week,
                        "end_week": plan.end_week,
                        "location": plan.location,
                        "capacity": plan.capacity,
                        "enrolled": plan.enrolled or 0,
                        "available": (plan.capacity or 0) - (
                            plan.enrolled or 0),
                        "semester": plan.semester,
                        "prerequisite": plan.prerequisite,
                        "apply_reason": plan.apply_reason,
                        "status": plan.status,
                        "audit_comment": plan.audit_comment,
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
                        "time_slot": cp.time_slot_display,
                        "weekday": cp.weekday,
                        "period_start": cp.period_start,
                        "period_count": cp.period_count,
                        "start_week": cp.start_week,
                        "end_week": cp.end_week,
                        "semester": cp.semester,
                        "location": cp.location,
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
