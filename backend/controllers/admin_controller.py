"""
backend/controllers/admin_controller.py - 管理员业务控制器

提供管理员专属业务逻辑：用户管理、课程管理、开课计划管理、
选课时段控制、数据备份等。
"""

from datetime import datetime
from sqlalchemy import text

from backend.models.base import DatabaseManager
from backend.models.user_account import UserAccount
from backend.models.student import Student
from backend.models.teacher import Teacher
from backend.models.course import Course
from backend.models.course_plan import CoursePlan
from backend.models.operation_log import OperationLog
from backend.utils.log_util import get_logger

logger = get_logger("admin_controller")


def _parse_datetime(value: str, fmt: str = "%Y-%m-%d %H:%M:%S"):
    """Parse a datetime string, accepting both ISO and space-separated formats."""
    if not value:
        return None
    from datetime import datetime
    try:
        return datetime.strptime(value, fmt)
    except ValueError:
        return datetime.fromisoformat(value)


class AdminController:
    """管理员业务控制器。

    提供学生/教师/课程等信息的增删改查操作。
    """

    def __init__(self):
        self._db = DatabaseManager.get_instance()

    def get_students(self, page: int = 1, page_size: int = 20,
                     student_id: str = None, name: str = None,
                     class_name: str = None) -> dict:
        """分页查询学生列表。

        Args:
            page: 页码（从1开始）。
            page_size: 每页条数。
            student_id: 学号筛选条件。
            name: 姓名筛选条件（模糊匹配）。
            class_name: 班级筛选条件。

        Returns:
            dict: {'total': int, 'page': int, 'data': list}
        """
        try:
            with self._db.get_session() as session:
                query = session.query(Student)

                if student_id:
                    query = query.filter(Student.student_id.like(
                        f"%{student_id}%"))
                if name:
                    query = query.filter(Student.name.like(f"%{name}%"))
                if class_name:
                    query = query.filter(
                        Student.class_name == class_name)

                total = query.count()
                offset = (page - 1) * page_size
                students = query.order_by(Student.student_id).offset(offset).limit(page_size).all()

                return {
                    "total": total,
                    "page": page,
                    "page_size": page_size,
                    "data": [s.to_dict() for s in students],
                }
        except Exception as e:
            logger.error(f"查询学生列表异常: {e}", exc_info=True)
            return {"total": 0, "page": page, "page_size": page_size,
                    "data": []}

    def create_student(self, student_id: str, name: str,
                       major: str = None, class_name: str = None,
                       contact: str = None, email: str = None,
                       grade: str = None, password: str = None) -> dict:
        """创建学生信息。

        同时在user_account表中创建对应账号（默认密码123456或由管理员指定）。
        """
        try:
            from backend.utils.auth_util import hash_password
            pwd = password if password and len(password) >= 6 else "123456"
            with self._db.get_session() as session:
                existing = session.query(UserAccount).filter_by(
                    user_id=student_id).first()
                if existing:
                    return {"success": False, "message": "该学号已存在"}

                account = UserAccount(
                    user_id=student_id,
                    password_hash=hash_password(pwd),
                    role="student",
                    is_locked=0,
                    login_fail_count=0,
                )
                session.add(account)

                student = Student(
                    student_id=student_id,
                    name=name,
                    major=major,
                    class_name=class_name,
                    grade=grade,
                    email=email,
                    contact=contact,
                )
                session.add(student)

                self._write_log(session, "admin", "系统",
                                f"创建学生: {student_id} (默认密码: {pwd})", "成功", "")
                logger.info(f"创建学生: {student_id}")
                return {"success": True, "message": f"学生创建成功，默认密码: {pwd}"}

        except Exception as e:
            logger.error(f"创建学生异常: {e}", exc_info=True)
            return {"success": False, "message": "操作失败，请重试"}

    def update_student(self, student_id: str, **kwargs) -> dict:
        """更新学生信息。"""
        try:
            with self._db.get_session() as session:
                student = session.query(Student).filter_by(
                    student_id=student_id).first()
                if student is None:
                    return {"success": False, "message": "学生不存在"}
                for key, value in kwargs.items():
                    if hasattr(student, key) and key != "student_id":
                        setattr(student, key, value)
                self._write_log(session, "admin", "系统",
                                f"更新学生: {student_id}", "成功", "")
                return {"success": True, "message": "学生信息更新成功"}
        except Exception as e:
            logger.error(f"更新学生异常: {e}", exc_info=True)
            return {"success": False, "message": "操作失败，请重试"}

    def delete_student(self, student_id: str) -> dict:
        """删除学生及其所有关联数据。"""
        try:
            from backend.models.enrollment import Enrollment
            from backend.models.grade import Grade
            from backend.models.password_reset_request import PasswordResetRequest

            with self._db.get_session() as session:
                student = session.query(Student).filter_by(
                    student_id=student_id).first()
                if student is None:
                    return {"success": False, "message": "学生不存在"}

                session.query(Enrollment).filter_by(
                    student_id=student_id).delete()
                session.query(Grade).filter_by(
                    student_id=student_id).delete()
                session.query(PasswordResetRequest).filter_by(
                    user_id=student_id).delete()
                session.flush()

                account = session.query(UserAccount).filter_by(
                    user_id=student_id).first()
                if account:
                    session.delete(account)

                self._write_log(session, "admin", "系统",
                                f"删除学生: {student_id}", "成功", "")
                return {"success": True, "message": "学生删除成功"}
        except Exception as e:
            logger.error(f"删除学生异常: {e}", exc_info=True)
            return {"success": False, "message": "操作失败，请重试"}

    def _write_log(self, session, user_id: str, log_type: str,
                   operation: str, result: str, ip_address: str = ""
                   ) -> None:
        savepoint = session.begin_nested()
        try:
            log_entry = OperationLog(
                user_id=user_id,
                log_type=log_type,
                operation=operation,
                result=result,
                log_time=datetime.now(),
                ip_address=ip_address,
            )
            session.add(log_entry)
            session.flush()
        except Exception:
            savepoint.rollback()
            logger.warning(f"操作日志写入失败（已跳过）: user={user_id} {operation}")

    # ----- Teacher management -----

    def get_teachers(self, page: int = 1, page_size: int = 20,
                     teacher_id: str = None, name: str = None,
                     college: str = None) -> dict:
        """分页查询教师列表。

        Args:
            page: 页码（从1开始）。
            page_size: 每页条数。
            teacher_id: 工号筛选条件。
            name: 姓名筛选条件（模糊匹配）。
            college: 学院筛选条件。

        Returns:
            dict: {'total': int, 'page': int, 'data': list}
        """
        try:
            with self._db.get_session() as session:
                query = session.query(Teacher)
                if teacher_id:
                    query = query.filter(Teacher.teacher_id.like(
                        f"%{teacher_id}%"))
                if name:
                    query = query.filter(Teacher.name.like(f"%{name}%"))
                if college:
                    query = query.filter(Teacher.college.like(
                        f"%{college}%"))
                total = query.count()
                offset = (page - 1) * page_size
                teachers = query.order_by(Teacher.teacher_id).offset(offset).limit(page_size).all()
                return {
                    "total": total,
                    "page": page,
                    "page_size": page_size,
                    "data": [t.to_dict() for t in teachers],
                }
        except Exception as e:
            logger.error(f"查询教师列表异常: {e}", exc_info=True)
            return {"total": 0, "page": page, "page_size": page_size,
                    "data": []}

    def create_teacher(self, teacher_id: str, name: str,
                       college: str = None, title: str = None,
                       contact: str = None, email: str = None,
                       password: str = None) -> dict:
        """创建教师信息。

        同时在user_account表中创建对应账号（默认密码123456或由管理员指定）。
        """
        try:
            from backend.utils.auth_util import hash_password
            pwd = password if password and len(password) >= 6 else "123456"
            with self._db.get_session() as session:
                existing = session.query(UserAccount).filter_by(
                    user_id=teacher_id).first()
                if existing:
                    return {"success": False, "message": "该工号已存在"}
                account = UserAccount(
                    user_id=teacher_id,
                    password_hash=hash_password(pwd),
                    role="teacher",
                    is_locked=0,
                    login_fail_count=0,
                )
                session.add(account)
                teacher = Teacher(
                    teacher_id=teacher_id,
                    name=name,
                    college=college,
                    title=title,
                    email=email,
                    contact=contact,
                )
                session.add(teacher)
                self._write_log(session, "admin", "系统",
                                f"创建教师: {teacher_id} (默认密码: {pwd})", "成功", "")
                logger.info(f"创建教师: {teacher_id}")
                return {"success": True, "message": f"教师创建成功，默认密码: {pwd}"}
        except Exception as e:
            logger.error(f"创建教师异常: {e}", exc_info=True)
            return {"success": False, "message": "操作失败，请重试"}

    def delete_teacher(self, teacher_id: str) -> dict:
        """删除教师及其所有关联数据。"""
        try:
            from backend.models.enrollment import Enrollment
            from backend.models.grade import Grade
            from backend.models.password_reset_request import PasswordResetRequest

            with self._db.get_session() as session:
                teacher = session.query(Teacher).filter_by(
                    teacher_id=teacher_id).first()
                if teacher is None:
                    return {"success": False, "message": "教师不存在"}

                plans = session.query(CoursePlan).filter_by(
                    teacher_id=teacher_id).all()
                for plan in plans:
                    session.query(Enrollment).filter_by(
                        plan_id=plan.plan_id).delete()
                    session.query(Grade).filter_by(
                        plan_id=plan.plan_id).delete()
                    session.delete(plan)
                session.query(PasswordResetRequest).filter_by(
                    user_id=teacher_id).delete()
                session.flush()

                account = session.query(UserAccount).filter_by(
                    user_id=teacher_id).first()
                if account:
                    session.delete(account)

                self._write_log(session, "admin", "系统",
                                f"删除教师: {teacher_id}", "成功", "")
                return {"success": True, "message": "教师删除成功"}
        except Exception as e:
            logger.error(f"删除教师异常: {e}", exc_info=True)
            return {"success": False, "message": "操作失败，请重试"}

    def update_teacher(self, teacher_id: str, **kwargs) -> dict:
        """更新教师信息。"""
        try:
            with self._db.get_session() as session:
                teacher = session.query(Teacher).filter_by(
                    teacher_id=teacher_id).first()
                if teacher is None:
                    return {"success": False, "message": "教师不存在"}
                for key, value in kwargs.items():
                    if hasattr(teacher, key) and key != "teacher_id":
                        setattr(teacher, key, value)
                self._write_log(session, "admin", "系统",
                                f"更新教师: {teacher_id}", "成功", "")
                return {"success": True, "message": "教师信息更新成功"}
        except Exception as e:
            logger.error(f"更新教师异常: {e}", exc_info=True)
            return {"success": False, "message": "操作失败，请重试"}

    # ----- Course management -----

    def get_courses(self, page: int = 1, page_size: int = 20,
                    course_id: str = None, course_name: str = None) -> dict:
        """分页查询课程列表。

        Args:
            page: 页码（从1开始）。
            page_size: 每页条数。
            course_id: 课程代码筛选条件。
            course_name: 课程名称筛选条件（模糊匹配）。

        Returns:
            dict: {'total': int, 'page': int, 'data': list}
        """
        try:
            with self._db.get_session() as session:
                query = session.query(Course)
                if course_id:
                    query = query.filter(Course.course_id.like(
                        f"%{course_id}%"))
                if course_name:
                    query = query.filter(Course.course_name.like(
                        f"%{course_name}%"))
                total = query.count()
                offset = (page - 1) * page_size
                courses = query.order_by(Course.course_id).offset(offset).limit(page_size).all()
                return {
                    "total": total,
                    "page": page,
                    "page_size": page_size,
                    "data": [c.to_dict() for c in courses],
                }
        except Exception as e:
            logger.error(f"查询课程列表异常: {e}", exc_info=True)
            return {"total": 0, "page": page, "page_size": page_size,
                    "data": []}

    def create_course(self, course_id: str, course_name: str,
                      credit: float = None, hours: int = None,
                      exam_type: str = None, department: str = None,
                      course_type: str = None, target_major: str = None,
                      description: str = None, textbook: str = None,
                      syllabus: str = None, instructor_intro: str = None) -> dict:
        """创建课程信息。"""
        try:
            with self._db.get_session() as session:
                existing = session.query(Course).filter_by(
                    course_id=course_id).first()
                if existing:
                    return {"success": False, "message": "该课程代码已存在"}
                course = Course(
                    course_id=course_id,
                    course_name=course_name,
                    credit=credit,
                    hours=hours,
                    exam_type=exam_type,
                    department=department,
                    course_type=course_type,
                    target_major=target_major,
                    description=description,
                    textbook=textbook,
                    syllabus=syllabus,
                    instructor_intro=instructor_intro,
                )
                session.add(course)
                self._write_log(session, "admin", "系统",
                                f"创建课程: {course_id}", "成功", "")
                logger.info(f"创建课程: {course_id}")
                return {"success": True, "message": "课程创建成功"}
        except Exception as e:
            logger.error(f"创建课程异常: {e}", exc_info=True)
            return {"success": False, "message": "操作失败，请重试"}

    def update_course(self, course_id: str, **kwargs) -> dict:
        """更新课程信息。"""
        try:
            with self._db.get_session() as session:
                course = session.query(Course).filter_by(
                    course_id=course_id).first()
                if course is None:
                    return {"success": False, "message": "课程不存在"}
                for key, value in kwargs.items():
                    if hasattr(course, key) and key != "course_id":
                        setattr(course, key, value)
                self._write_log(session, "admin", "系统",
                                f"更新课程: {course_id}", "成功", "")
                return {"success": True, "message": "课程信息更新成功"}
        except Exception as e:
            logger.error(f"更新课程异常: {e}", exc_info=True)
            return {"success": False, "message": "操作失败，请重试"}

    def delete_course(self, course_id: str) -> dict:
        """删除课程及其关联开课计划。"""
        try:
            with self._db.get_session() as session:
                course = session.query(Course).filter_by(
                    course_id=course_id).first()
                if course is None:
                    return {"success": False, "message": "课程不存在"}
                from backend.models.enrollment import Enrollment
                from backend.models.grade import Grade
                course_plans = session.query(CoursePlan).filter_by(course_id=course_id).all()
                for plan in course_plans:
                    session.query(Enrollment).filter_by(plan_id=plan.plan_id).delete()
                    session.query(Grade).filter_by(plan_id=plan.plan_id).delete()
                    session.delete(plan)
                session.flush()
                session.delete(course)
                self._write_log(session, "admin", "系统",
                                f"删除课程: {course_id}", "成功", "")
                return {"success": True, "message": "课程删除成功"}
        except Exception as e:
            logger.error(f"删除课程异常: {e}", exc_info=True)
            return {"success": False, "message": "操作失败，请重试"}

    # ----- Semester Config management -----

    def get_semester_configs(self) -> dict:
        """获取所有学期配置记录。

        Returns:
            dict: {'data': list}
        """
        try:
            from backend.models.semester_config import SemesterConfig
            with self._db.get_session() as session:
                configs = session.query(SemesterConfig).order_by(
                    SemesterConfig.semester.desc()
                ).all()
                return {
                    "data": [c.to_dict() for c in configs],
                }
        except Exception as e:
            logger.error(f"查询学期配置异常: {e}", exc_info=True)
            return {"data": []}

    def create_semester_config(self, semester: str, total_weeks: int = 20,
                               start_date: str = None, end_date: str = None,
                               is_current: bool = False,
                               enrollment_open: bool = False,
                               enroll_start: str = None,
                               enroll_end: str = None) -> dict:
        """创建学期配置记录。

        Args:
            semester: 学期标识，如 2026-2027-1
            total_weeks: 学期总周数
            start_date: 学期开始日期，格式 YYYY-MM-DD
            end_date: 学期结束日期，格式 YYYY-MM-DD
            is_current: 是否为当前学期
            enrollment_open: 选课是否开放
            enroll_start: 选课开始时间，格式 YYYY-MM-DD HH:MM:SS
            enroll_end: 选课结束时间，格式 YYYY-MM-DD HH:MM:SS
        """
        try:
            from backend.models.semester_config import SemesterConfig
            from datetime import datetime, date as dt_date
            with self._db.get_session() as session:
                config = SemesterConfig(
                    semester=semester,
                    total_weeks=total_weeks,
                    start_date=dt_date.fromisoformat(start_date) if start_date else None,
                    end_date=dt_date.fromisoformat(end_date) if end_date else None,
                    is_current=1 if is_current else 0,
                    enrollment_open=1 if enrollment_open else 0,
                    enroll_start=_parse_datetime(enroll_start, "%Y-%m-%d %H:%M:%S")
                    if enroll_start else None,
                    enroll_end=_parse_datetime(enroll_end, "%Y-%m-%d %H:%M:%S")
                    if enroll_end else None,
                )
                if is_current:
                    session.query(SemesterConfig).update({"is_current": 0})
                session.add(config)
                self._write_log(session, "admin", "系统",
                                f"创建学期配置: {semester}", "成功", "")
                return {"success": True, "message": "学期配置创建成功",
                        "data": config.to_dict()}
        except Exception as e:
            logger.error(f"创建学期配置异常: {e}", exc_info=True)
            return {"success": False, "message": str(e)}

    def update_semester_config(self, config_id: int, **kwargs) -> dict:
        """更新学期配置记录。
        支持字段：semester, total_weeks, start_date, end_date,
        is_current, enrollment_open, enroll_start, enroll_end
        """
        try:
            from backend.models.semester_config import SemesterConfig
            from datetime import datetime, date as dt_date
            with self._db.get_session() as session:
                config = session.query(SemesterConfig).filter_by(
                    config_id=config_id
                ).first()
                if config is None:
                    return {"success": False, "message": "记录不存在"}

                if "semester" in kwargs:
                    config.semester = kwargs["semester"]
                if "total_weeks" in kwargs:
                    config.total_weeks = kwargs["total_weeks"]
                if "start_date" in kwargs and kwargs["start_date"]:
                    config.start_date = dt_date.fromisoformat(kwargs["start_date"])
                if "end_date" in kwargs and kwargs["end_date"]:
                    config.end_date = dt_date.fromisoformat(kwargs["end_date"])
                if "is_current" in kwargs:
                    config.is_current = 1 if kwargs["is_current"] else 0
                    # 如果设为当前学期，清除其他记录的 is_current
                    if kwargs["is_current"]:
                        session.query(SemesterConfig).filter(
                            SemesterConfig.config_id != config_id
                        ).update({"is_current": 0})
                if "enrollment_open" in kwargs:
                    config.enrollment_open = 1 if kwargs["enrollment_open"] else 0
                if "enroll_start" in kwargs and kwargs["enroll_start"]:
                    val = kwargs["enroll_start"]
                    config.enroll_start = _parse_datetime(val, "%Y-%m-%d %H:%M:%S")
                if "enroll_end" in kwargs and kwargs["enroll_end"]:
                    val = kwargs["enroll_end"]
                    config.enroll_end = _parse_datetime(val, "%Y-%m-%d %H:%M:%S")

                self._write_log(session, "admin", "系统",
                                f"更新学期配置: {config.semester}", "成功", "")
                return {"success": True, "message": "学期配置更新成功",
                        "data": config.to_dict()}
        except Exception as e:
            logger.error(f"更新学期配置异常: {e}", exc_info=True)
            return {"success": False, "message": str(e)}

    def delete_semester_config(self, config_id: int) -> dict:
        """删除学期配置记录。"""
        try:
            from backend.models.semester_config import SemesterConfig
            with self._db.get_session() as session:
                config = session.query(SemesterConfig).filter_by(
                    config_id=config_id
                ).first()
                if config is None:
                    return {"success": False, "message": "记录不存在"}
                session.delete(config)
                self._write_log(session, "admin", "系统",
                                f"删除学期配置: {config.semester}", "成功", "")
                return {"success": True, "message": "学期配置删除成功"}
        except Exception as e:
            logger.error(f"删除学期配置异常: {e}", exc_info=True)
            return {"success": False, "message": str(e)}

    # ----- Operation logs -----

    def get_logs(self, page: int = 1, page_size: int = 50,
                 user_id: str = None, log_type: str = None) -> dict:
        """分页查询操作日志。

        Args:
            page: 页码（从1开始）。
            page_size: 每页条数。
            user_id: 用户ID筛选条件。
            log_type: 日志类型筛选条件（登录/选课/成绩/系统）。

        Returns:
            dict: {'total': int, 'page': int, 'data': list}
        """
        try:
            with self._db.get_session() as session:
                query = session.query(OperationLog)
                if user_id:
                    query = query.filter(
                        OperationLog.user_id.like(f"%{user_id}%"))
                if log_type:
                    query = query.filter(
                        OperationLog.log_type == log_type)
                total = query.count()
                offset = (page - 1) * page_size
                logs = query.order_by(OperationLog.log_time.desc()).offset(offset).limit(page_size).all()
                return {
                    "total": total,
                    "page": page,
                    "page_size": page_size,
                    "data": [log.to_dict() for log in logs],
                }
        except Exception as e:
            logger.error(f"查询操作日志异常: {e}", exc_info=True)
            return {"total": 0, "page": page, "page_size": page_size,
                    "data": []}
