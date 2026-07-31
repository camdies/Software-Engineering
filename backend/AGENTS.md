# Backend-specific instructions

These instructions apply to files under `backend` and supplement the repository root `AGENTS.md`.

## Layering

Keep the dependency direction:

```text
Blueprint: parse and validate transport input, authenticate, authorize, call controller
  -> Controller: business rules, resource ownership, transactions
    -> Model: SQLAlchemy mapping and database constraints
```

- Obtain sessions through `DatabaseManager.get_instance().get_session()` and do not access the database at module import time.
- Keep utilities focused on reusable concerns such as authentication, validation, logging, GPA calculation, and export formatting.
- API responses use `{ "success": bool, "data": any, "message": string }` through the shared response helpers.

The current domain model is centered on `class_period`, `semester_config`, `user_account`, `student`, `teacher`, `course`, `course_plan`, `enrollment`, `grade`, `operation_log`, and `password_reset_request`. Verify the ORM and both DDL files before relying on this list because schema documentation can drift.

## Database and transaction rules

- Preserve MySQL and SQL Server compatibility. Status columns remain `String(10)` rather than database-specific enums.
- Enrollment writes use one lock order everywhere: `Student(student_id)` first, `CoursePlan(plan_id)` second, then `Enrollment(student_id, plan_id)`. MySQL uses `FOR UPDATE`; SQL Server uses explicit update/row/serializable-equivalent hints. Do not assume SQL Server `READ COMMITTED` makes `with_for_update()` equivalent.
- Enrollment capacity must be guarded by the course-plan lock in the same transaction as the capacity check and enrollment write. The student lock serializes concurrent schedule changes for one student.
- Every path that creates or reactivates an enrollment must run the same period, duplicate, conflict, capacity, and prerequisite validations. Do not create a shortcut around the locked path.
- Preserve the database unique constraint on `(student_id, plan_id)` in the ORM and both DDLs as the final race-condition guard.
- Add database constraints for invariants that must survive all callers, and mirror those constraints in both DDL files.
- Do not swallow database exceptions into empty successful data. Return or raise a typed failure that the blueprint maps to an appropriate HTTP status.

## Authorization

- Verify resource ownership in addition to roles. In particular, a teacher may read or change grades, rosters, plans, and statistics only for plans they own; a student may read or export only their own schedule, grades, GPA, and academic statistics.
- Admin-only cross-user access must be explicit and auditable. Never accept a client-provided `student_id`, `teacher_id`, or `plan_id` as authorization proof.
- All plan-scoped routes use the shared `require_plan_access` decorator backed by `authorize_plan_access`. Keep a tested access-policy manifest covering every non-public API route plus reasoned exemptions; any new route not classified by access mode/capability must fail the route-closure test. Also flag route code that reads `plan_id` without declaring plan access.
- Public controller write methods also take an actor context and enforce the same policy so non-HTTP callers cannot bypass authorization.
- Student self-export schemas do not accept a target `student_id`; admin delegated export uses a separate audited path with actor, target, reason, semester, result, IP, time, and request id.

## Authentication and error semantics

- Without Redis, use `user_account.token_version` plus an account lookup on every authenticated request. Locking, logout, password reset/change, or role changes invalidate prior tokens by incrementing the version. Do not add a parallel jti blacklist until single-device revocation is required.
- Production must refuse to start without a strong configured JWT secret.
- Errors use stable machine codes. State conflicts are 409, semantically invalid input is 422, forbidden resource access is 403, unexpected failures are 500, and database/required-configuration outages are 503. Never return a successful empty payload for a failure.

## Excel schedule export

- Worksheet row 1 is the header and period data starts at row 2. For zero-based period index `p` and span `n`, the merged range is from row `p + 2` through `p + 1 + n`.
- Prefer structured merge coordinates over preformatted A1 strings and convert with openpyxl utilities in the export layer.
- Validate weekday, start period, span, end period, teaching weeks, semester, and overlap before indexing the schedule grid.
- Filter a schedule export by an explicit semester. Never mix multiple semesters in one seven-day grid without an intentional multi-sheet design.
- If courses sharing a cell have different spans, do not vertically merge or add rows. Render the fixed 11 atomic period rows and list every course covering each period. Only identical coverage sets and spans may merge; frontend, print, and Excel must use the same rule.
- After merging, apply alignment, border, fill, wrapping, row height, column width, print area, and freeze panes deliberately. Reopen the saved workbook in tests and assert merged ranges and cell placement.
- The shared tabular Excel helper is `utils/export_util.py`; schedule data originates in `StatsController.get_schedule_data`. Grade batch import uses openpyxl in `GradeController.batch_record_grade`.
- Export success requires a valid ZIP/XLSX container that openpyxl can reopen and whose sheet, headers, representative cells, and merge ranges match the export model. Use a temporary directory with unconditional cleanup; never return a boolean-only success or an unvalidated empty file.

## Semester source of truth

- Resolve the default semester through one shared resolver. It must find exactly one current semester; zero or multiple rows are configuration failures returned as 503, never a reason to use a hard-coded semester.
- Enforce at most one current semester in each database dialect and switch it transactionally. Frontend defaults and export defaults must use the same resolver.

## Schema changes

When adding or changing a table: update the ORM model, `config/init_database_mysql.sql`, `config/init_database.sql`, and `ARCHITECTURE.md`, then add migration or upgrade instructions for existing installations.
