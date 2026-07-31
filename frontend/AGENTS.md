# Frontend-specific instructions

These instructions apply to files under `frontend` and supplement the repository root `AGENTS.md`.

## Architecture

- Use Vue 3 Composition API with `<script setup>`.
- Use Pinia stores in `src/stores` for cross-page state and the Axios instance in `src/utils/request.js` for HTTP calls.
- Keep `createPinia()` installed before the router in `src/main.js`; the route guard reads the auth store.
- Register role-aware pages in `src/router/index.js` and keep route metadata, navigation labels, and permissions aligned.
- Use Element Plus and the tokens in `src/styles/global.scss`. Do not add a styling framework or icon library without first checking existing dependencies and explaining the need.

## Data refresh contract

- Every data-backed page must expose a named async loader such as `loadData` instead of embedding the request only inside `onMounted`.
- Loading a page for the first time, re-entering its route, changing relevant route params/query, switching an internal data tab, and returning after a mutation must all show current server data.
- Use the lifecycle that matches the actual router behavior: `onMounted` for normal remounts, `onBeforeRouteUpdate` or a route watcher for reused components, and `onActivated` only when the component is inside `KeepAlive`.
- Do not add route watchers as a ritual. Confirm that they can actually fire in the current component lifecycle, and avoid duplicate concurrent requests.
- Cross-page mutations must explicitly invalidate or refresh dependent data. For example, selecting or dropping a course invalidates the personal schedule, academic statistics, and capacity displays.
- A same-tab refresh action should call the page loader rather than forcing a full browser reload. Keep filters when that is useful, and prevent stale responses from overwriting newer requests.
- Keep refresh TTLs in `src/config/refresh-policy.js`: volatile enrollment/schedule/audit data defaults to 30 seconds, grades/statistics/logs to 60 seconds, and semester/period reference data to 300 seconds. Mutations invalidate immediately.
- On visibility/focus recovery, refresh only stale data after a meaningful hidden interval; throttle triggers, deduplicate in-flight requests, and prevent an older response from replacing a newer one.

## UX and accessibility

- Provide loading, empty, error, disabled, hover, pressed, and keyboard-focus states for interactive data views.
- Treat `success-empty` and `error` as distinct states. A 5xx/503 response shows an error panel with retry and request id; it must never render as “暂无数据”. Parse JSON error blobs from failed downloads instead of saving them as spreadsheets.
- Avoid inline styles and arbitrary fixed widths when a reusable class or responsive layout token is appropriate.
- Use `min-height: 100dvh` for full-screen layouts and provide a usable mobile navigation pattern rather than leaving the desktop sidebar and top bar to overflow.
- Honor `prefers-reduced-motion`. Do not require animation for understanding or operation.
- Use semantic elements and accessible names. Icon-only controls need an accessible label; tables need meaningful headers.
- Do not use raw `document.write` with course, location, user, or other server-provided values. Build printable DOM through Vue or escape all inserted text.
- The student schedule print/PDF path currently originates in `src/views/student/StudentSchedule.vue`; keep its grid semantics consistent with the server-side Excel schedule and test both when schedule logic changes.

## Build verification

Run `npm.cmd run build` from `frontend`. Treat bundle-size warnings, Sass deprecations, missing imports, and router chunking warnings as review findings even when the build succeeds.
