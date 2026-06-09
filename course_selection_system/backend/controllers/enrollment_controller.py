"""
backend/controllers/enrollment_controller.py - 选课核心控制器

负责选课/退课的核心业务逻辑，是本系统最关键的模块。
严格保证并发安全：使用数据库行级锁（SELECT ... FOR UPDATE）
防止选课超额，所有写操作在同一事务中执行。
"""

from datetime import datetime
from sqlalchemy import text

from backend.models.base import DatabaseManager
from backend.models.course_plan import CoursePlan
from backend.models.enrollment import Enrollment
from backend.models.grade import Grade
from backend.models.operation_log import OperationLog
from backend.models.course import Course
from backend.utils.log_util import get_logger

logger = get_logger("enrollment_controller")


class EnrollmentController:
    """选课核心控制器。

    提供选课、退课功能。
    选课流程包含5项严格校验，所有校验通过后在同一事务中完成数据写入。
    选课操作使用 SELECT ... FOR UPDATE 行级锁防止超额选课。
    """

    def __init__(self):
        self._db = DatabaseManager.get_instance()

    def select_course(self, student_id: str, plan_id: int) -> dict:
        """学生选课操作。

        按顺序执行5项校验，任一失败立即返回对应错误信息：
        1. 选课时段校验 — 当前时间是否在选课开放时段内
        2. 重复选课校验 — 是否已选择该课程且状态为"已选"
        3. 时间冲突校验 — 与已选课程时间是否冲突
        4. 容量校验 — 课程是否还有余量（使用行级锁）
        5. 先修课校验 — 是否已完成先修课程要求

        所有校验通过后，在同一事务中：
        - 插入 enrollment 记录
        - 更新 course_plan 的 enrolled 计数
        - 写入 operation_log

        Args:
            student_id: 学生学号。
            plan_id: 开课计划ID。

        Returns:
            dict: {'success': bool, 'message': str}
        """
        try:
            with self._db.get_session() as session:
                # --- 校验1: 选课时段校验 ---
                period_result = self._check_enrollment_period()
                if not period_result["valid"]:
                    msg = period_result["message"]
                    self._write_log(session, student_id, "选课",
                                    f"选课失败(时段): {msg}", "失败", "")
                    logger.info(f"学生{student_id}选课plan_id={plan_id}失败"
                                f"(时段校验): {msg}")
                    return {"success": False, "message": msg}

                # 获取开课计划信息
                plan = session.query(CoursePlan).filter_by(
                    plan_id=plan_id, status="开课"
                ).first()
                if plan is None:
                    self._write_log(session, student_id, "选课",
                                    f"选课失败: 开课计划{plan_id}不存在或已停课",
                                    "失败", "")
                    return {"success": False,
                            "message": "课程不存在或已停课"}

                # --- 校验2: 重复选课校验 ---
                existing = session.query(Enrollment).filter_by(
                    student_id=student_id, plan_id=plan_id, status="已选"
                ).first()
                if existing:
                    self._write_log(session, student_id, "选课",
                                    f"重复选课: plan_id={plan_id}", "失败", "")
                    logger.info(f"学生{student_id}重复选课plan_id={plan_id}")
                    return {"success": False,
                            "message": "您已选择该课程，请勿重复提交"}

                # --- 校验3: 时间冲突校验 ---
                conflict_result = self._check_time_conflict(
                    session, student_id, plan
                )
                if conflict_result["conflict"]:
                    self._write_log(session, student_id, "选课",
                                    f"时间冲突: plan_id={plan_id}", "失败", "")
                    return {"success": False,
                            "message": "上课时间冲突，请重新选择"}

                # --- 校验4: 容量校验（使用行级锁） ---
                # 使用 SELECT ... FOR UPDATE 锁定course_plan行，
                # 防止并发选课时的超额问题。
                # 事务边界: 从锁定操作开始到session.commit()为止。
                capacity_result = self._check_and_lock_capacity(
                    session, plan
                )
                if not capacity_result["available"]:
                    self._write_log(session, student_id, "选课",
                                    f"容量已满: plan_id={plan_id}", "失败", "")
                    return {"success": False,
                            "message": "课程容量已满，请选择其他课程"}

                # --- 校验5: 先修课校验 ---
                prereq_result = self._check_prerequisite(
                    session, student_id, plan
                )
                if not prereq_result["passed"]:
                    self._write_log(session, student_id, "选课",
                                    f"先修课未通过: plan_id={plan_id}",
                                    "失败", "")
                    return {
                        "success": False,
                        "message": (
                            "未完成先修课要求，请先完成: "
                            f"{prereq_result['course_names']}"
                        ),
                    }

                # --- 所有校验通过，执行数据写入 ---
                # 插入选课记录
                enrollment = Enrollment(
                    student_id=student_id,
                    plan_id=plan_id,
                    enroll_time=datetime.now(),
                    status="已选",
                )
                session.add(enrollment)

                # 更新已选人数（course_plan行已通过FOR UPDATE锁定）
                plan.enrolled = (plan.enrolled or 0) + 1

                # 写入操作日志
                self._write_log(session, student_id, "选课",
                                f"选课成功: plan_id={plan_id}", "成功", "")
                logger.info(
                    f"学生{student_id}选课成功: plan_id={plan_id}"
                )

                # 事务在此自动提交（由 get_session 上下文管理器处理）
                return {"success": True, "message": "选课成功！"}

        except Exception as e:
            logger.error(f"选课操作异常: {e}", exc_info=True)
            return {"success": False, "message": "操作失败，请重试"}

    def drop_course(self, student_id: str, plan_id: int) -> dict:
        """学生退课操作。

        验证选课记录存在后，在事务中：
        - UPDATE enrollment SET status='已退'
        - UPDATE course_plan SET enrolled = enrolled - 1
        - 写入退课日志

        Args:
            student_id: 学生学号。
            plan_id: 开课计划ID。

        Returns:
            dict: {'success': bool, 'message': str}
        """
        try:
            with self._db.get_session() as session:
                enrollment = session.query(Enrollment).filter_by(
                    student_id=student_id, plan_id=plan_id, status="已选"
                ).first()
                if enrollment is None:
                    return {"success": False,
                            "message": "未找到有效的选课记录"}

                enrollment.status = "已退"

                plan = session.query(CoursePlan).filter_by(
                    plan_id=plan_id
                ).first()
                if plan and (plan.enrolled or 0) > 0:
                    plan.enrolled = plan.enrolled - 1

                self._write_log(session, student_id, "选课",
                                f"退课成功: plan_id={plan_id}", "成功", "")
                logger.info(
                    f"学生{student_id}退课成功: plan_id={plan_id}"
                )

                return {"success": True, "message": "退课成功！"}

        except Exception as e:
            logger.error(f"退课操作异常: {e}", exc_info=True)
            return {"success": False, "message": "操作失败，请重试"}

    # ---- 内部校验方法 ----

    def _check_enrollment_period(self) -> dict:
        """校验当前时间是否在选课开放时段内。

        Returns:
            dict: {'valid': bool, 'message': str}
        """
        try:
            from backend.config.settings import Settings

            settings = Settings.get_instance()
            if not settings.enrollment_is_open:
                return {"valid": False,
                        "message": "当前不在选课时段，无法提交选课"}
            open_time_str = settings.enrollment_open_time
            close_time_str = settings.enrollment_close_time
            if open_time_str and close_time_str:
                open_time = datetime.strptime(
                    open_time_str, "%Y-%m-%d %H:%M:%S"
                )
                close_time = datetime.strptime(
                    close_time_str, "%Y-%m-%d %H:%M:%S"
                )
                now = datetime.now()
                if now < open_time or now > close_time:
                    return {"valid": False,
                            "message": "当前不在选课时段，无法提交选课"}
            return {"valid": True, "message": ""}
        except Exception as e:
            logger.error(f"选课时段校验异常: {e}")
            return {"valid": False,
                    "message": "当前不在选课时段，无法提交选课"}

    def _check_time_conflict(self, session, student_id: str,
                             target_plan: CoursePlan) -> dict:
        """校验学生已选课程与目标课程是否存在时间冲突。

        解析time_slot字段（格式：'周一1-2节'）并比对。

        Args:
            session: 数据库会话。
            student_id: 学生学号。
            target_plan: 目标课程开课计划。

        Returns:
            dict: {'conflict': bool}
        """
        try:
            target_slot = target_plan.time_slot
            if not target_slot:
                return {"conflict": False}

            # 查询学生已选所有课程的时间段
            enrolled_plans = (
                session.query(CoursePlan.time_slot)
                .join(Enrollment,
                      Enrollment.plan_id == CoursePlan.plan_id)
                .filter(
                    Enrollment.student_id == student_id,
                    Enrollment.status == "已选",
                )
                .all()
            )

            target_parsed = self._parse_time_slot(target_slot)
            if target_parsed is None:
                return {"conflict": False}

            for (slot,) in enrolled_plans:
                if not slot:
                    continue
                parsed = self._parse_time_slot(slot)
                if parsed is None:
                    continue
                if target_parsed == parsed:
                    return {"conflict": True}

            return {"conflict": False}
        except Exception as e:
            logger.error(f"时间冲突校验异常: {e}")
            return {"conflict": False}

    def _parse_time_slot(self, time_slot: str) -> tuple:
        """解析时间槽字符串为可比较的元组。

        Args:
            time_slot: 时间字符串，如 '周一1-2节'。

        Returns:
            tuple: (星期, 起始节, 结束节) 或 None
        """
        import re

        match = re.match(
            r'(周[一二三四五六日天])(\d+)-(\d+)节', time_slot
        )
        if not match:
            return None
        return (match.group(1), int(match.group(2)), int(match.group(3)))

    def _check_and_lock_capacity(self, session,
                                 plan: CoursePlan) -> dict:
        """检查课程容量并使用行级锁防止超额。

        使用 SELECT ... FOR UPDATE 锁定 course_plan 行，
        在事务提交前阻止其他事务修改该行，确保 enrolled < capacity
        的校验和 enrolled 更新是原子操作。

        Args:
            session: 数据库会话。
            plan: 目标开课计划对象（已加载）。

        Returns:
            dict: {'available': bool}
        """
        try:
            # 刷新plan对象并从数据库锁定该行
            # FOR UPDATE 行级锁：锁定plan_id对应的行，其他并发事务的
            # SELECT FOR UPDATE 将等待当前事务提交后才能读取，
            # 确保 capacity 校验和 enrolled+1 的原子性。
            locked_plan = (
                session.query(CoursePlan)
                .filter(CoursePlan.plan_id == plan.plan_id)
                .with_for_update()
                .first()
            )
            if locked_plan is None:
                return {"available": False}

            current_enrolled = locked_plan.enrolled or 0
            capacity = locked_plan.capacity or 0

            if current_enrolled >= capacity:
                logger.warning(
                    f"课程plan_id={plan.plan_id}容量已满 "
                    f"({current_enrolled}/{capacity})"
                )
                return {"available": False}

            # 更新plan引用为锁定后的对象
            plan.enrolled = locked_plan.enrolled
            return {"available": True}

        except Exception as e:
            logger.error(f"容量校验异常: {e}", exc_info=True)
            return {"available": False}

    def _check_prerequisite(self, session, student_id: str,
                            plan: CoursePlan) -> dict:
        """校验学生是否完成先修课程要求。

        查询 course_plan.prerequisite 字段（逗号分隔的课程代码列表），
        确认每门先修课在 grade 表中 score >= 60。

        Args:
            session: 数据库会话。
            student_id: 学生学号。
            plan: 目标开课计划。

        Returns:
            dict: {'passed': bool, 'course_names': str}
        """
        try:
            prereq_str = plan.prerequisite
            if not prereq_str or not prereq_str.strip():
                return {"passed": True, "course_names": ""}

            prereq_course_ids = [
                c.strip() for c in prereq_str.split(",") if c.strip()
            ]
            if not prereq_course_ids:
                return {"passed": True, "course_names": ""}

            failed_courses = []
            for course_id in prereq_course_ids:
                grade = (
                    session.query(Grade)
                    .filter(
                        Grade.student_id == student_id,
                        Grade.score >= 60,
                    )
                    .join(CoursePlan,
                          Grade.plan_id == CoursePlan.plan_id)
                    .filter(CoursePlan.course_id == course_id)
                    .first()
                )
                if grade is None:
                    # 获取课程名称用于友好提示
                    course = session.query(Course).filter_by(
                        course_id=course_id
                    ).first()
                    course_name = (
                        course.course_name if course else course_id
                    )
                    failed_courses.append(course_name)

            if failed_courses:
                return {
                    "passed": False,
                    "course_names": "、".join(failed_courses),
                }

            return {"passed": True, "course_names": ""}

        except Exception as e:
            logger.error(f"先修课校验异常: {e}", exc_info=True)
            return {"passed": False, "course_names": "未知课程"}

    def _write_log(self, session, user_id: str, log_type: str,
                   operation: str, result: str, ip_address: str = ""
                   ) -> None:
        """写入操作日志。

        Args:
            session: 数据库会话。
            user_id: 操作用户ID。
            log_type: 操作类型。
            operation: 操作描述。
            result: 操作结果（成功/失败）。
            ip_address: 操作IP地址。
        """
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
