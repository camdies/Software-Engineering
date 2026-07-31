# EduMgmt Codex project instructions

## Project identity

- Project: EduMgmt System v3.0, a university academic administration system maintained by the SCNU software engineering team.
- Primary platform: Windows 11 and PyCharm. The primary branch is `main`.
- Repository author context in the source rules is `camdies`; do not change global Git identity as part of normal project work.
- Read `ARCHITECTURE.md`, `API.md`, `DEBUG.md`, `FRONTEND_GUIDE.md`, and `DEVELOPMENT.md` when the task touches their subject area. Treat counts and snapshots in those documents as potentially stale and verify them against the code before repeating them.

## Stack and repository map

- Frontend: Vue 3 Composition API, Element Plus, Pinia, ECharts, Vite. Source is under `frontend/src`; production output is `frontend/dist`.
- Backend: Flask application factory, JWT bearer authentication, SQLAlchemy, PyMySQL, with MySQL as the default database and SQL Server compatibility retained.
- Export: openpyxl and pandas for Excel; browser print/reportlab paths may be used for PDF depending on the feature.
- Tests: pytest runner with `unittest.TestCase` and `unittest.mock` test style under `tests`.
- Distribution: embedded Python and portable MySQL are bundled for Windows; NSIS packaging lives under `develop tool`.

Role boundaries are: administrators manage people, courses, plans, audits, enrollment configuration/statistics, and logs; teachers manage only their own teaching plans, grades, and statistics; students manage only their own enrollment, schedule, grades, and academic statistics.

## Working rules

- Preserve the existing framework and layered architecture. Prefer small, reviewable changes over rewrites.
- Inspect the relevant implementation and its callers before editing. Do not trust a comment that claims a bug is fixed unless the current code and a regression test confirm it.
- Do not edit generated or bundled trees such as `frontend/dist`, `dist-bundle`, `python-embed`, `mysql-portable`, or `frontend/node_modules` unless the task explicitly targets packaging or generated artifacts.
- Keep API behavior and `API.md` synchronized when endpoints, parameters, permissions, or response shapes change.
- Keep both MySQL and SQL Server DDL synchronized when the schema changes, then update `ARCHITECTURE.md`.
- Preserve unrelated user changes in the worktree. Never commit `backend/config/config.ini`.

## Security and data integrity

- Never hard-code JWT secrets or database passwords in frontend or committed configuration.
- Every protected route must use `@require_auth` and the narrowest valid `@require_role` set.
- Role checks are not resource-ownership checks. Controllers and routes must also verify that the current teacher owns the plan and that a student can access only their own records unless an explicit admin workflow authorizes otherwise.
- Use SQLAlchemy expressions or parameterized SQL; never build SQL by concatenating user input.
- Do not render user-controlled HTML. Treat any `v-html`, `document.write`, or equivalent HTML sink as security-sensitive and escape dynamic values.
- Passwords must use the shared bcrypt helper with the configured cost. Production startup must fail closed when a secure JWT secret or other required security configuration is missing.
- Business validation and authorization failures must fail closed. A database or validation exception must not silently become “allowed”, “no conflict”, an empty successful result, or a downloadable empty file.

## Common verification commands

Run commands from the project root unless a command explicitly changes directory.

```powershell
python -m pytest tests/ -v
python -m compileall -q backend run.py run_prod.py
cd frontend
npm.cmd run build
```

For development, run `python run.py` for Flask and `npm.cmd run dev` from `frontend` for Vite. On Windows PowerShell, prefer `npm.cmd` when script execution policy blocks `npm.ps1`.

For the bundled setup, `start_all.bat` option 2 checks dependencies, rebuilds the frontend, and starts services. The portable database can be started with `mysql-portable\start_mysql.bat`; initialization DDL is `backend/config/init_database_mysql.sql`.

## Definition of done

- Add or update regression tests for every bug fix, including a test that fails against the old behavior.
- Run the narrowest relevant tests first, then the full backend suite and frontend production build for cross-cutting changes.
- For exported files, reopen the generated artifact and assert its structure and representative cell values; a successful save alone is insufficient.
- Report any verification that could not be run and why.
