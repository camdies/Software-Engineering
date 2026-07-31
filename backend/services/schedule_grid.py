"""Canonical eleven-period schedule grid shared by API and XLSX exports."""

from openpyxl.utils import get_column_letter

from backend.api.errors import ApiError


PERIOD_TIMES = [
    "08:30-09:10", "09:20-10:00", "10:20-11:00", "11:10-11:50",
    "14:30-15:10", "15:20-16:00", "16:10-16:50", "17:00-17:40",
    "19:00-19:40", "19:50-20:30", "20:40-21:20",
]


def _course_text(course):
    name = course.get("course_name") or course.get("course_id") or "未命名课程"
    location = course.get("location") or ""
    weeks = f"第{course['start_week']}-{course['end_week']}周"
    return "\n".join(part for part in (name, location, weeks) if part)


def build_schedule_grid(courses, semester):
    """Build fixed rows and safe merge coordinates from validated course spans."""
    cells = [[[] for _ in range(7)] for _ in range(11)]
    normalized = []
    for index, course in enumerate(courses):
        if course.get("semester") != semester:
            continue
        try:
            weekday = int(course["weekday"])
            start = int(course["period_start"])
            count = int(course["period_count"])
            start_week = int(course["start_week"])
            end_week = int(course["end_week"])
        except (KeyError, TypeError, ValueError) as exc:
            raise ApiError(
                "课表数据字段无效", code="SCHEDULE_DATA_INVALID", status_code=422
            ) from exc
        if not 1 <= weekday <= 7 or not 1 <= start <= 11 or count < 1:
            raise ApiError("课表节次越界", code="SCHEDULE_RANGE_INVALID", status_code=422)
        if start + count - 1 > 11 or start_week < 1 or end_week < start_week:
            raise ApiError("课表跨度无效", code="SCHEDULE_RANGE_INVALID", status_code=422)

        item = dict(course)
        item.update({
            "_key": str(course.get("plan_id", index)),
            "weekday": weekday,
            "period_start": start,
            "period_count": count,
            "start_week": start_week,
            "end_week": end_week,
        })
        normalized.append(item)
        for period in range(start - 1, start + count - 1):
            cells[period][weekday - 1].append(item)

    rows = []
    for period in range(11):
        row = [f"第{period + 1}节", PERIOD_TIMES[period]]
        for weekday in range(7):
            row.append("\n\n".join(_course_text(c) for c in cells[period][weekday]))
        rows.append(row)

    merge_ranges = []
    for weekday in range(7):
        period = 0
        while period < 11:
            group = cells[period][weekday]
            signature = tuple(sorted(c["_key"] for c in group))
            end = period + 1
            while end < 11 and tuple(sorted(c["_key"] for c in cells[end][weekday])) == signature:
                end += 1
            span = end - period
            may_merge = (
                bool(group)
                and span > 1
                and all(
                    c["period_start"] == period + 1 and c["period_count"] == span
                    for c in group
                )
            )
            if may_merge:
                col = get_column_letter(weekday + 3)
                start_row = period + 2
                end_row = end + 1
                merge_ranges.append(f"{col}{start_row}:{col}{end_row}")
                for covered in range(period + 1, end):
                    rows[covered][weekday + 2] = ""
            period = end

    return {
        "semester": semester,
        "schedule": rows,
        "merge_ranges": merge_ranges,
        "cells": [[[
            {key: value for key, value in course.items() if not key.startswith("_")}
            for course in cell
        ] for cell in row] for row in cells],
    }
