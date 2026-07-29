"""
backend/controllers/stats_controller.py - 统计分析控制器

提供成绩统计分析、学业统计、成绩分布统计等功能。
所有SQL查询使用参数化查询防止注入。
"""

from sqlalchemy import func, text

from backend.models.base import DatabaseManager
from backend.models.grade import Grade
from backend.models.enrollment import Enrollment
from backend.models.course_plan import CoursePlan
from backend.models.course import Course
from backend.models.student import Student
from backend.utils.gpa_calculator import calculate_cumulative_gpa
from backend.utils.log_util import get_logger

logger = get_logger("stats_controller")


class StatsController:
    """统计分析控制器。

    提供班级成绩统计、学生学业统计、成绩分布分析等功能，
    数据查询使用参数化查询防止SQL注入。
    """

    def __init__(self):
        self._db = DatabaseManager.get_instance()

    def get_class_stats(self, teacher_id: str, plan_id: int,
                        class_name: str = None) -> dict:
        """获取班级/课程的成绩统计数据。

        使用SQL聚合函数计算: 平均分、最高分、最低分、及格率、排名列表。

        Args:
            teacher_id: 教师工号（用于权限验证）。
            plan_id: 开课计划ID。
            class_name: 可选的班级过滤条件。

        Returns:
            dict: {'avg_score': float, 'max_score': int, 'min_score': int,
                   'pass_rate': float, 'rank_list': list}
        """
        try:
            with self._db.get_session() as session:
                # 构建基础查询
                query = session.query(Grade).join(
                    Student, Grade.student_id == Student.student_id
                )

                if class_name:
                    query = query.filter(
                        Student.class_name == class_name
                    )
                query = query.filter(Grade.plan_id == plan_id)

                grades_with_student = query.all()

                if not grades_with_student:
                    return {
                        "avg_score": 0.0,
                        "max_score": 0,
                        "min_score": 0,
                        "pass_rate": 0.0,
                        "rank_list": [],
                    }

                scores = [g.score for g in grades_with_student]
                total = len(scores)
                passed = sum(1 for s in scores if s >= 60)

                avg_score = round(sum(scores) / total, 2)
                max_score = max(scores)
                min_score = min(scores)
                pass_rate = round(passed / total, 2) if total > 0 else 0.0

                # 生成排名列表
                sorted_grades = sorted(
                    grades_with_student,
                    key=lambda g: g.score,
                    reverse=True,
                )
                rank_list = []
                for rank, grade in enumerate(sorted_grades, 1):
                    student = session.query(Student).filter_by(
                        student_id=grade.student_id
                    ).first()
                    rank_list.append({
                        "student_id": grade.student_id,
                        "name": student.name if student else "",
                        "score": grade.score,
                        "rank": rank,
                    })

                result = {
                    "avg_score": avg_score,
                    "max_score": max_score,
                    "min_score": min_score,
                    "pass_rate": pass_rate,
                    "rank_list": rank_list,
                }
                return result

        except Exception as e:
            logger.error(f"班级统计异常: {e}", exc_info=True)
            return {
                "avg_score": 0.0,
                "max_score": 0,
                "min_score": 0,
                "pass_rate": 0.0,
                "rank_list": [],
            }

    def get_academic_stats(self, student_id: str) -> dict:
        """获取学生个人学业统计。

        计算: 已修学分、累计GPA、未通过课程列表。

        Args:
            student_id: 学生学号。

        Returns:
            dict: {'total_credits': float, 'cumulative_gpa': float,
                   'failed_courses': list}
        """
        try:
            with self._db.get_session() as session:
                # 查询所有成绩记录（含课程学分信息）
                grades = (
                    session.query(Grade, CoursePlan, Course)
                    .join(CoursePlan, Grade.plan_id == CoursePlan.plan_id)
                    .join(Course, CoursePlan.course_id == Course.course_id)
                    .filter(Grade.student_id == student_id)
                    .all()
                )

                if not grades:
                    return {
                        "total_credits": 0.0,
                        "cumulative_gpa": 0.0,
                        "failed_courses": [],
                    }

                # 已修学分（score >= 60）
                total_credits = 0.0
                failed_courses = []
                gpa_items = []

                for grade, plan, course in grades:
                    credit = float(course.credit) if course.credit else 0.0
                    gpa = float(grade.gpa_point) if grade.gpa_point else 0.0

                    if grade.score is not None and grade.score >= 60:
                        total_credits += credit
                        gpa_items.append({
                            "gpa_point": gpa,
                            "credit": credit,
                        })
                    else:
                        failed_courses.append({
                            "course_name": course.course_name,
                            "score": grade.score or 0,
                            "semester": plan.semester,
                        })

                cumulative_gpa = calculate_cumulative_gpa(gpa_items)

                return {
                    "total_credits": round(total_credits, 1),
                    "cumulative_gpa": cumulative_gpa,
                    "failed_courses": failed_courses,
                }

        except Exception as e:
            logger.error(f"学业统计异常: {e}", exc_info=True)
            return {
                "total_credits": 0.0,
                "cumulative_gpa": 0.0,
                "failed_courses": [],
            }

    def get_score_distribution(self, plan_id: int) -> dict:
        """统计某课程各分数段人数及占比。

        分段: 优秀(90-100), 良好(75-89), 中等(60-74), 不及格(0-59)

        Args:
            plan_id: 开课计划ID。

        Returns:
            dict: 各分数段人数及占比。
        """
        try:
            with self._db.get_session() as session:
                grades = session.query(Grade).filter_by(
                    plan_id=plan_id
                ).all()

                total = len(grades)
                if total == 0:
                    return {
                        "total": 0,
                        "excellent": {"count": 0, "ratio": 0.0},
                        "good": {"count": 0, "ratio": 0.0},
                        "medium": {"count": 0, "ratio": 0.0},
                        "fail": {"count": 0, "ratio": 0.0},
                    }

                excellent = sum(1 for g in grades if 90 <= g.score <= 100)
                good = sum(1 for g in grades if 75 <= g.score <= 89)
                medium = sum(1 for g in grades if 60 <= g.score <= 74)
                fail = sum(1 for g in grades if 0 <= g.score <= 59)

                return {
                    "total": total,
                    "excellent": {
                        "count": excellent,
                        "ratio": round(excellent / total, 2),
                    },
                    "good": {
                        "count": good,
                        "ratio": round(good / total, 2),
                    },
                    "medium": {
                        "count": medium,
                        "ratio": round(medium / total, 2),
                    },
                    "fail": {
                        "count": fail,
                        "ratio": round(fail / total, 2),
                    },
                }

        except Exception as e:
            logger.error(f"成绩分布统计异常: {e}", exc_info=True)
            return {
                "total": 0,
                "excellent": {"count": 0, "ratio": 0.0},
                "good": {"count": 0, "ratio": 0.0},
                "medium": {"count": 0, "ratio": 0.0},
                "fail": {"count": 0, "ratio": 0.0},
            }

    def export_stats_to_excel(self, stats_data: dict,
                              file_path: str) -> bool:
        """将统计数据导出为Excel报表。"""
        try:
            from backend.utils.export_util import export_to_excel

            if "rank_list" in stats_data:
                headers = ["排名", "学号", "姓名", "成绩"]
                rows = [[r["rank"], r["student_id"], r["name"],
                         r["score"]] for r in stats_data["rank_list"]]
                summary = {
                    "排名": "汇总",
                    "学号": "",
                    "姓名": "",
                    "成绩": f"均分: {stats_data.get('avg_score', 0)}, "
                           f"及格率: {stats_data.get('pass_rate', 0)}",
                }
                return export_to_excel(headers, rows, file_path,
                                       sheet_name="成绩排名", summary_row=summary)
            elif "failed_courses" in stats_data:
                headers = ["课程名称", "成绩", "学期"]
                rows = [[f["course_name"], f["score"], f["semester"]]
                        for f in stats_data["failed_courses"]]
                summary = {
                    "课程名称": (
                        f"已修学分: {stats_data.get('total_credits', 0)}, "
                        f"GPA: {stats_data.get('cumulative_gpa', 0)}"
                    ),
                    "成绩": "",
                    "学期": "",
                }
                return export_to_excel(headers, rows, file_path,
                                       sheet_name="学业统计", summary_row=summary)
            elif "schedule" in stats_data:
                from backend.utils.export_util import export_schedule_to_excel

                headers = ["节次", "时间", "周一", "周二", "周三", "周四", "周五", "周六", "周日"]
                rows = stats_data["schedule"]
                merge_ranges = stats_data.get("merge_ranges", [])
                return export_schedule_to_excel(
                    headers, rows, merge_ranges, file_path,
                    sheet_name="个人课表")
            else:
                logger.warning("stats_data格式不支持Excel导出")
                return False

        except Exception as e:
            logger.error(f"统计导出Excel异常: {e}", exc_info=True)
            return False

    def get_schedule_data(self, student_id: str) -> dict:
        """获取学生课表数据（含rowspan信息用于导出）。

        Args:
            student_id: 学生学号。

        Returns:
            dict: 包含schedule二维数组和merge_ranges的字典。
        """
        try:
            from backend.controllers.student_controller import StudentController
            sc = StudentController()
            my_courses = sc.get_my_courses(student_id)

            period_times = [
                "08:30-09:10", "09:20-10:00", "10:20-11:00", "11:10-11:50",
                "14:30-15:10", "15:20-16:00", "16:10-16:50", "17:00-17:40",
                "19:00-19:40", "19:50-20:30", "20:40-21:20",
            ]

            grid = []
            for p in range(11):
                row = []
                for d in range(7):
                    row.append({"text": "", "rowspan": 1, "covered": False})
                grid.append(row)

            for c in my_courses:
                start_row = c["period_start"] - 1
                end_row = start_row + c["period_count"] - 1
                col = c["weekday"] - 1

                name = c.get("course_name", "")
                loc = c.get("location", "")
                display_text = f"{name}\n{loc}" if loc else name

                grid[start_row][col]["text"] = display_text
                grid[start_row][col]["rowspan"] = c["period_count"]

                for r in range(start_row + 1, end_row + 1):
                    grid[r][col]["covered"] = True

            schedule = []
            merge_ranges = []

            for p in range(11):
                row = [f"第{p + 1}节", period_times[p]]
                for d in range(7):
                    cell = grid[p][d]
                    if cell["covered"]:
                        row.append("")
                    else:
                        row.append(cell["text"])
                        if cell["rowspan"] > 1:
                            col_letter = chr(ord("C") + d)
                            merge_ranges.append(
                                f"{col_letter}{p + 2}:"
                                f"{col_letter}{p + 1 + cell['rowspan']}"
                            )
                schedule.append(row)

            return {"schedule": schedule, "merge_ranges": merge_ranges}

        except Exception as e:
            logger.error(f"获取课表数据异常: {e}", exc_info=True)
            return {"schedule": [], "merge_ranges": []}

    def get_gpa_trend(self, student_id: str) -> dict:
        try:
            from backend.utils.gpa_calculator import calculate_cumulative_gpa

            with self._db.get_session() as session:
                grades = (
                    session.query(Grade, CoursePlan, Course)
                    .join(CoursePlan, Grade.plan_id == CoursePlan.plan_id)
                    .join(Course, CoursePlan.course_id == Course.course_id)
                    .filter(Grade.student_id == student_id)
                    .order_by(CoursePlan.semester)
                    .all()
                )

                if not grades:
                    return {"semesters": [], "overall_gpa": 0.0}

                semester_map = {}
                for grade, plan, course in grades:
                    sem = plan.semester or "未知学期"
                    if sem not in semester_map:
                        semester_map[sem] = []
                    semester_map[sem].append({
                        "gpa_point": float(grade.gpa_point or 0),
                        "credit": float(course.credit or 0),
                    })

                semesters = []
                all_items = []
                for sem, items in semester_map.items():
                    sem_gpa = calculate_cumulative_gpa(items)
                    semesters.append({
                        "semester": sem,
                        "gpa": sem_gpa,
                        "credits": round(sum(i["credit"] for i in items), 1),
                        "course_count": len(items),
                    })
                    all_items.extend(items)

                overall_gpa = calculate_cumulative_gpa(all_items)

                return {
                    "semesters": semesters,
                    "overall_gpa": overall_gpa,
                }

        except Exception as e:
            logger.error(f"GPA趋势异常: {e}", exc_info=True)
            return {"semesters": [], "overall_gpa": 0.0}
