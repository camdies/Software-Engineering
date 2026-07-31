# Test-specific instructions

These instructions apply to files under `tests` and supplement the repository root `AGENTS.md`.

- Use `unittest.TestCase` and `unittest.mock`; pytest remains the runner, but do not introduce pytest-only test structure without an explicit test-suite migration.
- Patch `Settings` at `backend.config.settings.Settings`, its source definition. The controller imports it lazily.
- Settings mocks must provide `log_level="ERROR"` and `log_dir="logs"` so logger initialization remains valid.
- Patch ORM classes such as `Grade`, `Enrollment`, and `OperationLog` in the controller module that uses them to avoid unintended mapper initialization.
- Patch `_check_enrollment_period` with `patch.object` because it performs local imports.
- Model the exact SQLAlchemy call chain used by the implementation. `query().filter_by().first()` and `query().filter().join().filter().first()/all()` are distinct mock chains.
- Concurrent enrollment tests need an independent session mock per thread.
- Do not rely only on mocks for database concurrency, constraints, authorization, or file exports. Add focused integration tests where behavior depends on real SQLAlchemy identity, row locking, Flask decorators, HTTP status codes, or openpyxl merged cells.
- Required regression coverage includes: reselecting a dropped course, ownership checks for every teacher statistics/grade/roster path, cross-student export denial, route and internal-tab refresh behavior, semester filtering, schedule boundary validation, and exact Excel merged ranges/cell values.
- Maintain an access-policy manifest covering every non-public route. The route-closure test compares it with `app.url_map`, rejects unclassified endpoints or unexplained exemptions, flags `plan_id` usage without plan policy, and black-box cross-owner requests must still return 403.
- Run enrollment concurrency tests against MySQL 8; mocks or SQLite cannot certify row-lock behavior. Cover capacity-one races, same-student conflicting plans, dropped-course reactivation, uniqueness races, and bounded deadlock retries.
- `C2:C3` for a two-period course starting in period 1, course text in `C2`, and a merged `C3` are critical non-skippable assertions. Also test same-cell courses with different spans remain unmerged in web, print, and Excel representations.
- Critical authorization, lock-order, current-semester, token-version, error-semantics, refresh, and export-validator tests may not be skipped or xfailed. New or modified core files need at least 90% diff coverage; the policy and validation branches need full branch coverage.
