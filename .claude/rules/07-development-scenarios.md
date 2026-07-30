---
description: 常见开发场景操作指南（选课逻辑、Excel/PDF导出、调试）——手动触发
alwaysApply: false
version: 1.0.0
---

# 常见开发场景

## 修改选课逻辑

1. 核心逻辑在 `backend/controllers/enrollment_controller.py`（选课/退课、5项校验、行级锁）
2. 前端在 `views/student/StudentEnroll.vue`（最复杂的页面，~600行）
3. 测试在 `tests/test_enrollment.py`（含并发测试）

## Excel/PDF 导出

- **Excel 导出基础**: `backend/utils/export_util.py`（`export_to_excel` 通用函数）
- **课表 Excel 导出**: 使用 `export_schedule_to_excel`，数据由 `stats_controller.get_schedule_data` 提供（含 `merge_ranges` 用于 rowspan 合并）
- **PDF 导出**: 仅学生端课表，前端 `StudentSchedule.vue` 通过 `buildScheduleGrid()` 构建 rowspan 网格 → `window.print()`
- **Excel 批量导入**: `grade_controller.batch_record_grade` 使用 openpyxl 读取

## 调试

- 后端日志在 `logs/` 目录，使用 `RotatingFileHandler`（10MB 切割、保留 30 个文件）
- PyCharm 调试配置: Script path=`run.py`, Working directory=`<项目根目录>`
- 前端: `npm run dev` 启动 Vite 热更新，API 代理到 `:5000`
- 详见 [DEBUG.md](DEBUG.md)
