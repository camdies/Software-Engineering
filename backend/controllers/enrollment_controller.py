"""Concurrency-safe enrollment and drop workflows."""

from datetime import datetime

from sqlalchemy.exc import IntegrityError, OperationalError

from backend.models.base import DatabaseManager
from backend.models.course import Course
from backend.models.course_plan import CoursePlan
from backend.models.enrollment import Enrollment
from backend.models.grade import Grade
from backend.models.operation_log import OperationLog
from backend.models.student import Student
from backend.utils.log_util import get_logger

logger = get_logger("enrollment_controller")


class EnrollmentController:
    """Serialize one student's schedule changes and one plan's capacity changes."""

    MAX_DEADLOCK_RETRIES = 2

    def __init__(self):
        self._db = DatabaseManager.get_instance()

    @staticmethod
    def _failure(message, code, status_code):
        return {
            "success": False,
            "message": message,
            "code": code,
            "status_code": status_code,
        }

    def select_course(self, student_id: str, plan_id: int) -> dict:
        for attempt in range(self.MAX_DEADLOCK_RETRIES + 1):
            try:
                return self._select_once(student_id, plan_id)
            except OperationalError as exc:
                if self._is_deadlock(exc) and attempt < self.MAX_DEADLOCK_RETRIES:
                    logger.warning("选课事务死锁，准备重试: attempt=%s", attempt + 1)
                    continue
                logger.error("选课数据库异常", exc_info=True)
                return self._failure("选课服务暂时不可用", "ENROLLMENT_DB_UNAVAILABLE", 503)
            except IntegrityError:
                logger.info("选课唯一约束冲突: student=%s plan=%s", student_id, plan_id)
                return self._failure("您已选择该课程，请勿重复提交", "ALREADY_ENROLLED", 409)
            except Exception:
                logger.error("选课操作异常", exc_info=True)
                return self._failure("选课服务暂时不可用", "ENROLLMENT_SERVICE_UNAVAILABLE", 503)

    def _select_once(self, student_id, plan_id):
        with self._db.get_session() as session:
            period_result = self._check_enrollment_period(session)
            if not period_result["valid"]:
                return self._failure(period_result["message"], "ENROLLMENT_CLOSED", 409)

            # Global lock order: Student -> CoursePlan -> Enrollment.
            student = self._locked_first(session, Student, student_id=student_id)
            if student is None:
                return self._failure("学生不存在", "STUDENT_NOT_FOUND", 404)

            plan = self._locked_first(session, CoursePlan, plan_id=plan_id)
            if plan is None or plan.status != "已通过":
                return self._failure("课程不存在或未开放选课", "PLAN_NOT_AVAILABLE", 409)

            existing = self._locked_first(
                session, Enrollment, student_id=student_id, plan_id=plan_id
            )
            if existing is not None and existing.status == "已选":
                return self._failure("您已选择该课程，请勿重复提交", "ALREADY_ENROLLED", 409)

            conflict = self._check_time_conflict(session, student_id, plan)
            if conflict["conflict"]:
                return self._failure("上课时间冲突，请重新选择", "SCHEDULE_CONFLICT", 409)

            current_enrolled = int(plan.enrolled or 0)
            capacity = int(plan.capacity or 0)
            if current_enrolled >= capacity:
                return self._failure("课程容量已满，请选择其他课程", "COURSE_FULL", 409)

            prereq = self._check_prerequisite(session, student_id, plan)
            if not prereq["passed"]:
                return self._failure(
                    f"未完成先修课要求，请先完成: {prereq['course_names']}",
                    "PREREQUISITE_NOT_MET",
                    422,
                )

            if existing is None:
                session.add(Enrollment(
                    student_id=student_id,
                    plan_id=plan_id,
                    enroll_time=datetime.now(),
                    status="已选",
                ))
            else:
                # Reactivation happens only after all validations pass.
                existing.status = "已选"
                existing.enroll_time = datetime.now()
            plan.enrolled = current_enrolled + 1
            self._write_log(
                session, student_id, "选课", f"选课成功: plan_id={plan_id}", "成功"
            )
            return {"success": True, "message": "选课成功！"}

    def drop_course(self, student_id: str, plan_id: int) -> dict:
        for attempt in range(self.MAX_DEADLOCK_RETRIES + 1):
            try:
                with self._db.get_session() as session:
                    student = self._locked_first(session, Student, student_id=student_id)
                    if student is None:
                        return self._failure("学生不存在", "STUDENT_NOT_FOUND", 404)
                    plan = self._locked_first(session, CoursePlan, plan_id=plan_id)
                    enrollment = self._locked_first(
                        session,
                        Enrollment,
                        student_id=student_id,
                        plan_id=plan_id,
                    )
                    if enrollment is None or enrollment.status != "已选":
                        return self._failure("未找到有效的选课记录", "ENROLLMENT_NOT_FOUND", 404)
                    enrollment.status = "已退"
                    if plan is not None and int(plan.enrolled or 0) > 0:
                        plan.enrolled = int(plan.enrolled) - 1
                    self._write_log(
                        session, student_id, "选课", f"退课成功: plan_id={plan_id}", "成功"
                    )
                    return {"success": True, "message": "退课成功！"}
            except OperationalError as exc:
                if self._is_deadlock(exc) and attempt < self.MAX_DEADLOCK_RETRIES:
                    continue
                return self._failure("退课服务暂时不可用", "ENROLLMENT_DB_UNAVAILABLE", 503)
            except Exception:
                logger.error("退课操作异常", exc_info=True)
                return self._failure("退课服务暂时不可用", "ENROLLMENT_SERVICE_UNAVAILABLE", 503)

    def _locked_first(self, session, model, **filters):
        query = session.query(model)
        if getattr(self._db, "is_mssql", False) is True:
            query = query.with_hint(
                model, "WITH (UPDLOCK, ROWLOCK, HOLDLOCK)", dialect_name="mssql"
            )
        else:
            query = query.with_for_update()
        return query.filter_by(**filters).first()

    @staticmethod
    def _is_deadlock(exc):
        args = getattr(getattr(exc, "orig", None), "args", ())
        joined = " ".join(str(item) for item in args)
        return "1213" in joined or "1205" in joined

    def _check_enrollment_period(self, session=None) -> dict:
        from backend.services.semester_resolver import CurrentSemesterResolver

        if session is not None:
            semester = CurrentSemesterResolver.resolve(session)
            if not semester.enrollment_open:
                return {"valid": False, "message": "当前学期选课未开放"}
            now = datetime.now()
            if semester.enroll_start and now < semester.enroll_start:
                return {"valid": False, "message": "选课尚未开始"}
            if semester.enroll_end and now > semester.enroll_end:
                return {"valid": False, "message": "选课已结束"}
            return {"valid": True, "message": ""}
        with self._db.get_session() as managed_session:
            return self._check_enrollment_period(managed_session)

    def _check_time_conflict(self, session, student_id, target_plan):
        target_end = target_plan.period_start + target_plan.period_count - 1
        target_start_week = target_plan.start_week or 1
        target_end_week = target_plan.end_week or 20
        enrolled_plans = (
            session.query(CoursePlan)
            .join(Enrollment, Enrollment.plan_id == CoursePlan.plan_id)
            .filter(
                Enrollment.student_id == student_id,
                Enrollment.status == "已选",
                CoursePlan.status == "已通过",
            )
            .all()
        )
        for plan in enrolled_plans:
            if plan.plan_id == target_plan.plan_id or plan.weekday != target_plan.weekday:
                continue
            plan_end = plan.period_start + plan.period_count - 1
            period_overlap = plan.period_start <= target_end and plan_end >= target_plan.period_start
            week_overlap = (plan.start_week or 1) <= target_end_week and (plan.end_week or 20) >= target_start_week
            if period_overlap and week_overlap:
                return {"conflict": True}
        return {"conflict": False}

    def _check_prerequisite(self, session, student_id, plan):
        course_ids = [item.strip() for item in (plan.prerequisite or "").split(",") if item.strip()]
        failed = []
        for course_id in course_ids:
            grade = (
                session.query(Grade)
                .filter(Grade.student_id == student_id, Grade.score >= 60)
                .join(CoursePlan, Grade.plan_id == CoursePlan.plan_id)
                .filter(CoursePlan.course_id == course_id)
                .first()
            )
            if grade is None:
                course = session.query(Course).filter_by(course_id=course_id).first()
                failed.append(course.course_name if course else course_id)
        return {"passed": not failed, "course_names": "、".join(failed)}

    def _write_log(self, session, user_id, log_type, operation, result, ip_address=""):
        session.add(OperationLog(
            user_id=user_id,
            log_type=log_type,
            operation=operation,
            result=result,
            log_time=datetime.now(),
            ip_address=ip_address,
        ))
