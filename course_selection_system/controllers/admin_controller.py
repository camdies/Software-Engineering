"""
controllers/admin_controller.py - 管理员业务控制器

提供管理员专属业务逻辑：用户管理、课程管理、开课计划管理、
选课时段控制、数据备份等。
"""

from datetime import datetime
from sqlalchemy import text

from models.base import DatabaseManager
from models.user_account import UserAccount
from models.student import Student
from models.teacher import Teacher
from models.course import Course
from models.course_plan import CoursePlan
from models.operation_log import OperationLog
from utils.log_util import get_logger

logger = get_logger("admin_controller")


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
                students = query.offset(offset).limit(page_size).all()

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
                       contact: str = None) -> dict:
        """创建学生信息。

        同时在user_account表中创建对应账号（默认密码123456）。
        """
        try:
            from utils.auth_util import hash_password
            with self._db.get_session() as session:
                # 检查是否已存在
                existing = session.query(UserAccount).filter_by(
                    user_id=student_id).first()
                if existing:
                    return {"success": False, "message": "该学号已存在"}

                # 创建user_account
                account = UserAccount(
                    user_id=student_id,
                    password_hash=hash_password("123456"),
                    role="student",
                    is_locked=0,
                    login_fail_count=0,
                )
                session.add(account)

                # 创建student
                student = Student(
                    student_id=student_id,
                    name=name,
                    major=major,
                    class_name=class_name,
                    contact=contact,
                )
                session.add(student)

                self._write_log(session, "admin", "系统",
                                f"创建学生: {student_id}", "成功", "")
                logger.info(f"创建学生: {student_id}")
                return {"success": True, "message": "学生创建成功"}

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
        """删除学生（级联删除user_account）。"""
        try:
            with self._db.get_session() as session:
                student = session.query(Student).filter_by(
                    student_id=student_id).first()
                if student is None:
                    return {"success": False, "message": "学生不存在"}
                session.delete(student)
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
        except Exception as e:
            logger.warning(f"操作日志写入失败: {e}")
