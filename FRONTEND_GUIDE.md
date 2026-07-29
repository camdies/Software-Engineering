# Frontend Architecture & Communication Guide

## 1. Frontend Runtime Logic

### 1.1 Startup Sequence

```
User opens http://localhost:5000
        │
        ▼
Flask serves frontend/dist/index.html   (SPA fallback, app_factory.py:113-123)
        │
        ▼
main.js executes:
  1. createApp(App)                    # Vue 3 app instance
  2. createPinia() → app.use(pinia)    # State management (MUST be before router)
  3. app.use(router)                   # Vue Router
  4. app.use(ElementPlus)              # UI component library
  5. app.mount('#app')                 # Mount to DOM
        │
        ▼
App.vue renders <router-view>          # Displays current route component
        │
        ▼
router.beforeEach fires               # Guard checks authentication
  ┌─ Path has meta.public=true? ──→ Allow (e.g. /login)
  └─ Otherwise:
       ├─ No token? ──→ Redirect to /login
       └─ Has token, wrong role? ──→ Redirect to /login
        │
        ▼
LoginView.vue renders                  # User sees login page
```

Key files:

| File | Role |
|------|------|
| `src/main.js` | Entry point. Installs Pinia → Router → ElementPlus → mounts App |
| `src/App.vue` | Root component. Contains `<router-view>` with fade transition |
| `src/router/index.js` | Route definitions + `beforeEach` auth guard |
| `src/stores/auth.js` | Pinia store for token, role, login/logout actions |
| `src/stores/app.js` | Pinia store for sidebar collapse state |
| `src/utils/request.js` | Axios instance with interceptors (token injection, 401 handling) |

### 1.2 Route → Component Mapping

```
/login                    → LoginView.vue         (public, no auth required)
/                         → MainLayout.vue        (wrapper, requires auth)
  /admin/students           → AdminStudents.vue     (role: admin)
  /admin/teachers           → AdminTeachers.vue
  /admin/courses            → AdminCourses.vue
  /admin/course-plans       → AdminCoursePlans.vue
  /admin/audit              → AdminAudit.vue
  /admin/enrollment-control → AdminEnrollmentControl.vue
  /admin/enrollment-stats   → AdminEnrollmentStats.vue
  /admin/logs               → AdminLogs.vue
  /teacher/plans            → TeacherPlans.vue      (role: teacher)
  /teacher/grades           → TeacherGrades.vue
  /teacher/grade-modify     → TeacherGradeModify.vue
  /teacher/stats            → TeacherStats.vue
  /student/enroll           → StudentEnroll.vue     (role: student)
  /student/my-courses       → StudentSchedule.vue
  /student/grades           → StudentGrades.vue
  /student/stats            → StudentStats.vue
```

All routes use **lazy loading** (`() => import(...)`) — each page component is loaded only when the user navigates to it.

### 1.3 Sidebar Navigation

`MainLayout.vue` renders an Element Plus `<el-menu>` with `router` mode. The menu items have `index` attributes matching route paths, so clicking them triggers `router.push()` automatically.

The sidebar is role-based:
- `auth.isAdmin` → shows admin menu items
- `auth.isTeacher` → shows teacher menu items
- `auth.isStudent` → shows student menu items

---

## 2. Frontend–Backend Communication

### 2.1 Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│  Browser                                                 │
│  ┌──────────────────┐    ┌────────────────────────────┐ │
│  │  Vue 3 SPA        │    │  Flask (run.py)             │ │
│  │  (Element Plus)    │    │                            │ │
│  │                    │    │  /api/*    → Blueprint APIs │ │
│  │  axios request ───┼───→│  /assets/* → Static files   │ │
│  │       ←───────────┼────│  /*        → index.html     │ │
│  └──────────────────┘    └────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

Flask serves **both** the REST API and the Vue frontend from a single process:
- API routes: `/api/auth/login`, `/api/admin/students`, etc. (handled by Blueprints)
- Static assets: `/assets/*` → `frontend/dist/assets/`
- SPA fallback: any other path → `frontend/dist/index.html`

### 2.2 Development vs Production Mode

**Development mode** (two servers):

```
Vite dev server  :5173  → Serves Vue with HMR
Flask            :5000  → Serves REST API only

Vite proxies /api/* → localhost:5000  (see vite.config.js:37-42)
```

When a developer runs `npm run dev` in `frontend/`, the browser opens `localhost:5173`. API calls go through Vite's proxy to Flask.

**Production mode** (single server):

```
Flask            :5000  → Serves API + Vue dist files
```

When the installer runs `run.bat`, Flask serves everything. The frontend is pre-built in `frontend/dist/`.

### 2.3 API Request Flow (step by step)

**Example: Student clicks "Enroll in Course"**

```
1. StudentEnroll.vue calls:
     await request.post('/enrollment/enroll', { plan_id: 42 })

2. request.js interceptor fires (request):
     Adds header: Authorization: Bearer <jwt_token>

3. HTTP POST /api/enrollment/enroll reaches Flask

4. Flask routes to enrollment_bp.py:
     @enrollment_bp.route('/enroll', methods=['POST'])
     @require_auth              ← decodes JWT, sets g.current_user
     @require_role("student")   ← checks g.current_user.role == "student"
     def enroll():
         ...

5. enrollment_controller.enroll() runs:
     - Reads g.current_user["user_id"]
     - Checks enrollment window (semester_config table)
     - Inserts row into enrollment table (database write)
     - Calls _write_log() to record operation

6. Returns JSON response:
     { "success": true, "message": "选课成功", "data": { ... } }

7. request.js response interceptor fires:
     - success=true → returns response.data to caller
     - success=false → shows ElMessage.error(message)
     - 401 status → clears token, redirects to /login
     - 403 status → shows "权限不足"
```

### 2.4 API Endpoint Summary

All endpoints are prefixed with `/api`:

| Blueprint | Prefix | Purpose |
|-----------|--------|---------|
| `auth_bp` | `/api/auth` | Login, logout, change password |
| `admin_bp` | `/api/admin` | CRUD students, teachers, courses, plans, enrollment control |
| `student_bp` | `/api/student` | Own schedule, grades, stats |
| `teacher_bp` | `/api/teacher` | Plans, grade entry, grade modify, own stats |
| `enrollment_bp` | `/api/enrollment` | Student course enrollment / withdrawal |
| `grade_bp` | `/api/grade` | Grade entry, modify, export |
| `stats_bp` | `/api/stats` | Dashboard statistics |
| `audit_bp` | `/api/audit` | Admin audit (password reset, grade modify, course review) |
| `password_reset_bp` | `/api/password-reset` | Password reset request flow |

### 2.5 Authentication Mechanism

```
Login:
  POST /api/auth/login { user_id, password }
    → bcrypt.verify(password, stored_hash)
    → JWT created with { user_id, role, iat, exp }
    → Response: { token, role, user_id }

Every subsequent request:
  Header: Authorization: Bearer <token>
    → require_auth decorator decodes JWT
    → Sets g.current_user = { user_id, role }
    → require_role decorator checks role permission

Token stored in: localStorage['token']
Token expires:  24 hours (configurable in config.ini)
```

### 2.6 Error Handling

The Axios response interceptor (`request.js:49-87`) handles all errors centrally:

| HTTP Status | Handler Behavior |
|-------------|-----------------|
| 401 | Clear localStorage, redirect to /login, show "登录已过期" |
| 403 | Show "权限不足" |
| other 4xx/5xx | Show server error message or "服务器错误" |
| Network error | Show "网络异常" |

---

## 3. Viewing the Frontend Independently (without Flask)

You can run the Vue dev server standalone. This is useful for UI development without needing MySQL or Python running.

### 3.1 Prerequisites

- Node.js 18+ installed (`node --version`)

### 3.2 Steps

```bash
# 1. Navigate to frontend directory
cd frontend

# 2. Install dependencies (first time only)
npm install

# 3. Start dev server
npm run dev
```

Vite starts at http://localhost:5173 with hot module replacement (HMR).

### 3.3 Making API calls work without Flask

By default, the Vite dev server **proxies** `/api/*` requests to `http://localhost:5000` (defined in `vite.config.js:37-42`). So you need Flask running on port 5000 for API functionality.

To point at a **different** backend (e.g. a remote server):

```bash
# Windows PowerShell:
$env:VITE_API_TARGET="http://192.168.1.100:5000"
npm run dev

# Or on Linux/macOS:
VITE_API_TARGET=http://192.168.1.100:5000 npm run dev
```

To run the dev server with **no backend** (for pure UI work):

```bash
npm run dev
# You'll see the login page. API calls will fail (network error),
# but you can inspect the UI, tweak styles, and check layout.
```

### 3.4 Building the Production Dist

```bash
cd frontend
npm run build
# Output: frontend/dist/index.html + frontend/dist/assets/
```

To build targeting a specific API base URL (for deployment to a different server):

```bash
# Windows:
$env:VITE_API_TARGET="https://api.example.com"; npm run build

# Linux/macOS:
VITE_API_TARGET=https://api.example.com npm run build
```

This injects `__API_BASE__` as a global constant in the built JS, so all API calls go to the specified server instead of same-origin `/api`.

### 3.5 Previewing the Built Dist

```bash
cd frontend
npx vite preview --port 4173
# Opens static file server at localhost:4173
# API calls will go to /api on the same origin
```
