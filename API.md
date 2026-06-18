# EduMgmt System v3.0 — Complete API Documentation

> 总端点: 48
> **Auth**: JWT Bearer token (HS256, 24h expiry)  
> **Content-Type**: `application/json` (except file uploads)  
> **Charset**: UTF-8  

---

## 1. Authentication

All endpoints except `/api/auth/login` and `/api/auth/forgot-password` require a JWT token sent as:

```
Authorization: Bearer <token>
```

### Response Format

**Success** (HTTP 200):
```json
{ "success": true, "data": <any>, "message": "操作成功" }
```

**Error** (HTTP 4xx):
```json
{ "success": false, "data": null, "message": "error description" }
```

### HTTP Status Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 400 | Bad request (validation error) |
| 401 | Missing or expired token |
| 403 | Account locked or insufficient role |
| 404 | Resource not found |
| 500 | Internal server error |

---

## 2. Roles

| Role | Description |
|------|-------------|
| `admin` | Administrator — full system access |
| `teacher` | Teacher — manage courses, grades |
| `student` | Student — browse courses, enroll |

---

## 3. Endpoints

### 3.1 Auth (`/api/auth`)

---

#### POST `/api/auth/login`
Login and receive a JWT token.

**Auth**: None

**Request Body**:
```json
{
  "user_id": "admin",
  "password": "123456"
}
```

**Response** (200):
```json
{
  "success": true,
  "data": {
    "token": "eyJhbGciOi...",
    "role": "admin",
    "user_id": "admin"
  },
  "message": "登录成功"
}
```

**Errors**: `"请输入账号和密码"` / `"用户不存在"` / `"账号已锁定"` / `"密码错误"`

---

#### POST `/api/auth/logout`
Logout current user.

**Auth**: JWT (any role)

**Request Body**: none

**Response** (200):
```json
{ "success": true, "data": null, "message": "已退出登录" }
```

---

#### POST `/api/auth/change-password`
Change own password.

**Auth**: JWT (any role)

**Request Body**:
```json
{
  "old_password": "123456",
  "new_password": "newpass123"
}
```

**Response** (200):
```json
{ "success": true, "data": null, "message": "密码修改成功" }
```

**Errors**: `"原密码错误"` / `"新密码不能与原密码相同"` / `"新密码长度不能少于6位"`

---

#### POST `/api/auth/reset-password`
Admin resets a user's password to default (123456).

**Auth**: JWT (admin)

**Request Body**:
```json
{ "user_id": "STU001" }
```

**Response** (200):
```json
{ "success": true, "data": null, "message": "密码已重置为默认密码: 123456" }
```

---

#### POST `/api/auth/forgot-password`
Submit a password reset request (no login required).

**Auth**: None

**Request Body**:
```json
{
  "user_id": "STU001",
  "reason": "I forgot my password"
}
```

**Response** (200):
```json
{ "success": true, "data": null, "message": "密码重置申请已提交，请等待管理员审核" }
```

**Errors**: `"请输入账号"` / `"账号不存在"` / `"您已有待审核的密码重置申请"`

---

### 3.2 Admin — Students (`/api/admin`)

All require JWT (admin).

---

#### GET `/api/admin/students`
Paginated student list.

**Query params**:

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `page` | int | 1 | Page number |
| `page_size` | int | 20 | Items per page |
| `student_id` | string | — | Filter by student ID (LIKE) |
| `name` | string | — | Filter by name (LIKE) |
| `class_name` | string | — | Filter by class (exact) |

**Response** (200):
```json
{
  "success": true,
  "data": {
    "total": 5,
    "page": 1,
    "page_size": 20,
    "data": [
      {
        "student_id": "STU001",
        "name": "王小明",
        "major": "计算机科学与技术",
        "class_name": "计科2101",
        "grade": "2024",
        "email": "stu001@univ.edu.cn",
        "contact": "13900002001",
        "created_at": "2026-06-15T..."
      }
    ]
  }
}
```

---

#### POST `/api/admin/students`
Create a new student (auto-creates user account).

**Request Body**:
```json
{
  "student_id": "STU006",
  "name": "新学生",
  "major": "软件工程",
  "class_name": "软工2201",
  "grade": "2025",
  "email": "new@univ.edu.cn",
  "contact": "13800000000",
  "password": "custompass"
}
```
- `student_id` and `name` are required
- `password` defaults to `123456` if omitted

**Response** (200):
```json
{ "success": true, "data": null, "message": "学生创建成功，默认密码: 123456" }
```

---

#### PUT `/api/admin/students/<student_id>`
Update a student. Body: any subset of updatable fields.

```json
{ "major": "数据科学", "class_name": "数据2201" }
```

**Response** (200):
```json
{ "success": true, "data": null, "message": "学生信息更新成功" }
```

---

#### DELETE `/api/admin/students/<student_id>`
Delete a student and their user account.

**Response** (200):
```json
{ "success": true, "data": null, "message": "学生删除成功" }
```

---

### 3.3 Admin — Teachers (`/api/admin`)

Identical CRUD pattern to students.

#### GET `/api/admin/teachers`
Query: `page`, `page_size`, `teacher_id`, `name`, `college`

#### POST `/api/admin/teachers`
```json
{
  "teacher_id": "T004",
  "name": "新教师",
  "college": "计算机学院",
  "title": "讲师",
  "email": "t004@univ.edu.cn",
  "contact": "13800000000",
  "password": "custompass"
}
```

#### PUT `/api/admin/teachers/<teacher_id>`
#### DELETE `/api/admin/teachers/<teacher_id>`

---

### 3.4 Admin — Courses (`/api/admin`)

#### GET `/api/admin/courses`
Query: `page`, `page_size`, `course_id`, `course_name`

#### POST `/api/admin/courses`
```json
{
  "course_id": "CS401",
  "course_name": "人工智能导论",
  "credit": 3.0,
  "hours": 48,
  "exam_type": "考试",
  "department": "计算机科学与技术学院",
  "course_type": "选修",
  "target_major": "计算机科学与技术,软件工程",
  "description": "本课程讲授...",
  "textbook": "《人工智能...》",
  "syllabus": "第1-3周: ...",
  "instructor_intro": "某教授..."
}
```

#### PUT `/api/admin/courses/<course_id>`
#### DELETE `/api/admin/courses/<course_id>`

---

### 3.5 Admin — Other (`/api/admin`)

#### GET `/api/admin/course-plans`
List all course plans. Query: `semester` (optional).

#### GET `/api/admin/enrollment-control`
Get enrollment period settings. (Legacy — backed by semester_config.)

#### GET `/api/admin/semester-configs`
List all semester configs. **Auth**: JWT (admin).

**Response**: Array of `{ config_id, semester, total_weeks, start_date, end_date, is_current, enrollment_open, enroll_start, enroll_end }`.

#### POST `/api/admin/semester-configs`
Create a new semester config. **Auth**: JWT (admin).
```json
{
  "semester": "2027-2028-1",
  "total_weeks": 20,
  "start_date": "2027-09-01",
  "end_date": "2028-01-16",
  "is_current": false,
  "enrollment_open": false,
  "enroll_start": null,
  "enroll_end": null
}
```
When `is_current=true`, all other semester configs are automatically unset.

#### PUT `/api/admin/semester-configs/<config_id>`
Update a semester config. **Auth**: JWT (admin). Body: any subset of the creation fields.

#### DELETE `/api/admin/semester-configs/<config_id>`
Delete a semester config. **Auth**: JWT (admin).

---

#### GET `/api/admin/enrollment-stats`
Enrollment statistics per course plan. Query: `semester` (optional).

#### GET `/api/admin/grades/pending`
Grades pending audit review.

#### GET `/api/admin/logs`
Paginated operation logs. Query: `page`, `page_size` (default 50), `user_id`, `log_type`.

---

### 3.6 Student (`/api/student`)

All require JWT (student).

---

#### GET `/api/student/courses`
Available courses for enrollment.

**Query params**:

| Param | Type | Description |
|-------|------|-------------|
| `semester` | string | e.g. `"2026-2027-1"` |
| `department` | string | Filter by department |
| `credit_range` | string | e.g. `"0-2"`, `"2-4"`, `"4-6"` |
| `weekday` | int | 1=Mon … 7=Sun |
| `exam_type` | string | `"考试"` or `"考查"` |
| `course_type` | string | `"必修"`, `"选修"`, `"公共必修"`, `"公共选修"` |

**Response**: Array of course objects with `plan_id`, `course_id`, `course_name`, `credit`, `hours`, `exam_type`, `department`, `course_type`, `teacher_id`, `teacher_name`, `time_slot`, `weekday`, `period_start`, `period_count`, `start_week`, `end_week`, `location`, `capacity`, `enrolled`, `available`, `prerequisite`, `description`, `textbook`, `syllabus`, `instructor_intro`.

---

#### GET `/api/student/my-courses`
Currently enrolled courses.

**Response**: Array with `plan_id`, `course_id`, `course_name`, `credit`, `weekday`, `period_start`, `period_count`, `start_week`, `end_week`, `time_slot`, `location`, `semester`, `enroll_time`.

---

#### GET `/api/student/grades`
All grade records.

**Response**: Array with `grade_id`, `student_id`, `plan_id`, `course_name`, `credit`, `score`, `gpa_point`, `semester`, `status`, `modify_reason`, `new_score`.

---

#### GET `/api/student/stats`
Academic statistics.

**Response**:
```json
{
  "success": true,
  "data": {
    "total_credits": 12.0,
    "cumulative_gpa": 3.33,
    "failed_courses": []
  }
}
```

---

### 3.7 Teacher (`/api/teacher`)

All require JWT (teacher).

---

#### GET `/api/teacher/plans`
Teacher's teaching plans. Query: `semester` (optional).

**Response**: Array with `plan_id`, `course_id`, `course_name`, `time_slot`, `weekday`, `period_start`, `period_count`, `start_week`, `end_week`, `location`, `capacity`, `enrolled`, `status`, `audit_comment`, `apply_reason`.

---

#### GET `/api/teacher/plans/<plan_id>/students`
Enrolled students for a plan.

**Response**: Array with `student_id`, `name`, `major`, `class_name`, `enroll_id`.

---

#### GET `/api/teacher/grades`
Get grades for a course. Query: `plan_id` (required).

**Response**: Array with `student_id`, `name`, `score`, `gpa_point`, `grade_id`, `grade_status`.

---

#### POST `/api/teacher/course-plan`
Submit a new teaching plan (status: 待审核).

```json
{
  "course_id": "CS401",
  "semester": "2026-2027-1",
  "weekday": 1,
  "period_start": 3,
  "period_count": 2,
  "start_week": 1,
  "end_week": 18,
  "location": "教学楼A301",
  "capacity": 40,
  "prerequisite": "CS100",
  "apply_reason": "开设此课程..."
}
```

---

#### PUT `/api/teacher/course-plan/<plan_id>`
Update a pending plan (only if status=待审核).

---

### 3.8 Enrollment (`/api/enrollment`)

All require JWT (student).

---

#### POST `/api/enrollment/select`
Enroll in a course.

```json
{ "plan_id": 1 }
```

**Success** (200):
```json
{ "success": true, "data": null, "message": "选课成功！" }
```

**Errors**: `"当前不在选课时段"` / `"您已选择该课程"` / `"上课时间冲突"` / `"课程容量已满"` / `"未完成先修课要求"`

---

#### POST `/api/enrollment/drop`
Drop a course (requires confirmation in UI).

```json
{ "plan_id": 1 }
```

**Response** (200):
```json
{ "success": true, "data": null, "message": "退课成功！" }
```

---

### 3.9 Grade (`/api/grade`)

---

#### POST `/api/grade/record`
Record a single grade. **Auth**: JWT (teacher).

```json
{
  "student_id": "STU001",
  "plan_id": 1,
  "score": 85
}
```

---

#### POST `/api/grade/batch`
Batch import from Excel. **Auth**: JWT (teacher).

Form data: `plan_id` (int) + `file` (Excel upload).

**Response**:
```json
{
  "success": true,
  "data": {
    "success_count": 25,
    "fail_count": 3,
    "fail_list": [{ "row": 5, "student_id": "STU099", "reason": "未选此课" }]
  }
}
```

---

#### POST `/api/grade/modify`
Apply for a grade change. **Auth**: JWT (teacher).

```json
{
  "grade_id": 42,
  "new_score": 90,
  "reason": "录入错误，实际成绩为90分"
}
```

---

#### POST `/api/grade/audit/<grade_id>`
Audit a grade change request. **Auth**: JWT (admin).

```json
{
  "action": "approve",
  "comment": "审核通过"
}
```
- `action`: `"approve"` or `"reject"`

---

### 3.10 Stats (`/api/stats`)

---

#### GET `/api/stats/class/<plan_id>`
Class statistics. **Auth**: JWT (teacher, admin). Query: `class_name` (optional).

**Response**:
```json
{
  "success": true,
  "data": {
    "avg_score": 78.5,
    "max_score": 95,
    "min_score": 42,
    "pass_rate": 0.85,
    "rank_list": [
      { "rank": 1, "student_id": "STU001", "name": "王小明", "score": 95 }
    ]
  }
}
```

---

#### GET `/api/stats/distribution/<plan_id>`
Score distribution. **Auth**: JWT (teacher, admin).

**Response**:
```json
{
  "success": true,
  "data": {
    "total": 30,
    "excellent": { "count": 5, "ratio": 0.17 },
    "good": { "count": 12, "ratio": 0.40 },
    "medium": { "count": 10, "ratio": 0.33 },
    "fail": { "count": 3, "ratio": 0.10 }
  }
}
```

---

#### POST `/api/stats/export`
Export stats as Excel. **Auth**: JWT (any role).

```json
{ "type": "class", "plan_id": 1 }
```
```json
{ "type": "academic", "student_id": "STU001" }
```
```json
{ "type": "schedule" }
```

**Response**: File download (`.xlsx`).

---

### 3.11 Audit (`/api/audit`)

All require JWT (admin).

---

#### GET `/api/audit/overview`
Pending counts for all audit types.

**Response**:
```json
{
  "success": true,
  "data": {
    "password_resets": 2,
    "grade_modifications": 1,
    "course_plans": 3
  }
}
```

---

#### GET `/api/audit/password-resets`
List password reset requests. Query: `status` (default `"待审核"`).

#### POST `/api/audit/password-resets/<request_id>`
Process a password reset request.
```json
{ "action": "approve", "comment": "confirmed" }
```

---

#### GET `/api/audit/course-plans`
List course plans pending audit. Query: `status` (default `"待审核"`).

#### POST `/api/audit/course-plans/<plan_id>`
Approve/reject a course plan.
```json
{ "action": "approve", "comment": "approved" }
```

---

## 4. Default Accounts

All passwords are **123456**.

| Role | Username |
|------|----------|
| Admin | `admin`, `admin2` |
| Teacher (计科院) | `T001`, `T003`, `T004` |
| Teacher (数统院) | `T002`, `T005` |
| Teacher (其他学院) | `T006`, `T007`, `T008` |
| Student | `STU001` … `STU025` (4个专业, 3个年级) |

---

## 5. Quick Reference (All 48 Endpoints)

| # | Method | URL | Auth |
|---|--------|-----|------|
| 1 | POST | `/api/auth/login` | None |
| 2 | POST | `/api/auth/logout` | JWT |
| 3 | POST | `/api/auth/change-password` | JWT |
| 4 | POST | `/api/auth/reset-password` | JWT admin |
| 5 | GET | `/api/admin/students` | JWT admin |
| 6 | POST | `/api/admin/students` | JWT admin |
| 7 | PUT | `/api/admin/students/<id>` | JWT admin |
| 8 | DELETE | `/api/admin/students/<id>` | JWT admin |
| 9 | GET | `/api/admin/teachers` | JWT admin |
| 10 | POST | `/api/admin/teachers` | JWT admin |
| 11 | PUT | `/api/admin/teachers/<id>` | JWT admin |
| 12 | DELETE | `/api/admin/teachers/<id>` | JWT admin |
| 13 | GET | `/api/admin/courses` | JWT admin |
| 14 | POST | `/api/admin/courses` | JWT admin |
| 15 | PUT | `/api/admin/courses/<id>` | JWT admin |
| 16 | DELETE | `/api/admin/courses/<id>` | JWT admin |
| 17 | GET | `/api/admin/course-plans` | JWT admin |
| 18 | GET | `/api/admin/semester-configs` | JWT admin |
| 19 | POST | `/api/admin/semester-configs` | JWT admin |
| 20 | PUT | `/api/admin/semester-configs/<id>` | JWT admin |
| 21 | DELETE | `/api/admin/semester-configs/<id>` | JWT admin |
| 22 | GET | `/api/admin/enrollment-stats` | JWT admin |
| 23 | GET | `/api/admin/grades/pending` | JWT admin |
| 24 | GET | `/api/admin/logs` | JWT admin |
| 25 | GET | `/api/student/courses` | JWT student |
| 26 | GET | `/api/student/my-courses` | JWT student |
| 27 | GET | `/api/student/grades` | JWT student |
| 28 | GET | `/api/student/stats` | JWT student |
| 29 | GET | `/api/teacher/plans` | JWT teacher |
| 30 | GET | `/api/teacher/plans/<id>/students` | JWT teacher |
| 31 | GET | `/api/teacher/grades` | JWT teacher |
| 32 | POST | `/api/teacher/course-plan` | JWT teacher |
| 33 | PUT | `/api/teacher/course-plan/<id>` | JWT teacher |
| 34 | POST | `/api/enrollment/select` | JWT student |
| 35 | POST | `/api/enrollment/drop` | JWT student |
| 36 | POST | `/api/grade/record` | JWT teacher |
| 37 | POST | `/api/grade/batch` | JWT teacher |
| 38 | POST | `/api/grade/modify` | JWT teacher |
| 39 | POST | `/api/grade/audit/<id>` | JWT admin |
| 40 | GET | `/api/stats/class/<id>` | JWT teacher/admin |
| 41 | GET | `/api/stats/distribution/<id>` | JWT teacher/admin |
| 42 | POST | `/api/stats/export` | JWT any |
| 43 | GET | `/api/audit/overview` | JWT admin |
| 44 | GET | `/api/audit/password-resets` | JWT admin |
| 45 | POST | `/api/audit/password-resets/<id>` | JWT admin |
| 46 | GET | `/api/audit/course-plans` | JWT admin |
| 47 | POST | `/api/audit/course-plans/<id>` | JWT admin |
| 48 | POST | `/api/auth/forgot-password` | None |
