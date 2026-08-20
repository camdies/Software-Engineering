# EduMgmt v3.0 修复与设计审阅方案

日期：2026-07-31  
范围：当前 `main` 分支的前端、后端、导出链路、权限、测试与界面设计静态审计  
本轮边界：只新增 Codex 规则与本审阅文档，未修改业务代码或数据库。

## 一、结论与建议

当前应用可以构建，现有 22 个后端单元测试全部通过，但不建议直接发布当前版本。建议按以下顺序修复：

1. **阻断越权与选课数据破坏**：补齐资源归属校验，修复退课后重选绕过校验及异常时 fail-open。
2. **修复课表 Excel 正确性**：修正行号偏移，并统一学期、周次、合并坐标和同一时段多课程的数据模型。
3. **统一页面刷新策略**：先修内部页签和课表刷新，再建立轻量的数据失效机制，避免靠全量组件重建。
4. **补齐回归测试**：至少覆盖 Flask 权限、真实 openpyxl 文件、选课重入路径和前端页面生命周期。
5. **最后做界面与性能优化**：移动端导航、离线字体、颜色收敛、状态设计和主包拆分。

仓库历史中的 `b0029979` 提交只修了 Excel 行号、合并后样式和一个课表路由 watcher，**不建议原样 cherry-pick**：它没有测试；`onActivated` 被导入但未使用；当前 `router-view` 已按 `fullPath` 设置 key，普通跨路由返回本来会重新挂载；它也没有解决跨学期混排、同一时段不同教学周课程被覆盖、越权导出和导出失败仍返回文件的问题。

## 二、两个已报告问题

### 2.1 网页内切换页签后数据不自动刷新

#### 已确认现状

- 路由页面在 [`frontend/src/layouts/MainLayout.vue`](frontend/src/layouts/MainLayout.vue) 中以 `resolved.fullPath` 作为组件 key，正常从一个菜单路由切到另一个菜单路由时会重新创建页面，页面的 `onMounted` 会再执行。
- 学生课表仍把请求直接写在 [`frontend/src/views/student/StudentSchedule.vue`](frontend/src/views/student/StudentSchedule.vue) 的 `onMounted` 内，没有统一的 `loadData`，也没有加载、错误或并发保护。
- 审核中心的内部 Element Plus 页签在 [`frontend/src/views/admin/AdminAudit.vue`](frontend/src/views/admin/AdminAudit.vue) 中切换时，`onTabChange()` 只刷新角标，不刷新当前页签列表。这是一个明确的内部页签陈旧数据问题。
- 生产运行由 Flask 服务 `frontend/dist`；使用快速启动会直接使用已有构建。如果只改 `frontend/src` 而没有重新构建，用户看到的仍是旧行为。

#### 立即修复方案（低风险）

1. 把每个数据页的初始请求抽成命名函数 `loadData()`。
2. 审核中心按 `activeTab` 在 `tab-change` 时调用对应的 `fetchPwd/fetchGrade/fetchPlan`，并同步刷新角标。
3. 学生课表的 `loadData()` 在开始时设置 loading，在空结果时同时清空 `semester`，用递增请求号或 `AbortController` 防止旧请求覆盖新请求。
4. 保留当前正常跨路由 remount 行为；不要仅为“看起来保险”给每页添加无法在卸载后触发的 `watch(route.path)`。
5. 修复后执行 `npm.cmd run build`，并确认实际启动的是新 `frontend/dist`。

#### 最佳方案（推荐）

在现有 Pinia 中增加轻量的“数据域失效标记”，而不是引入新状态库：

- 数据域示例：`enrollment`、`schedule`、`academicStats`、`auditPassword`、`auditGrade`、`auditPlan`。
- 选课/退课成功后失效 `enrollment + schedule + academicStats`。
- 审核操作成功后失效对应审核列表和角标。
- 页面进入、同页签再次点击、内部页签切换或窗口重新获得焦点时，只在数据失效或超过短 TTL 时刷新。
- 保留筛选条件，不用 `window.location.reload()`，也不依赖强制销毁整页组件。

验收：从“选课”选一门课后进入“个人课表”立即出现；退课后返回立即消失；审核页三个内部页签切换均重新读取当前列表；快速连续切换不会出现旧响应覆盖新响应。

### 2.2 学生导出 Excel 课程错位

#### 根因一：合并行号整体下移一行（已实证）

[`backend/utils/export_util.py`](backend/utils/export_util.py) 从 Excel 第 2 行开始写数据，但 [`backend/controllers/stats_controller.py`](backend/controllers/stats_controller.py) 当前使用 `p + 3` 作为合并起点。第 1–2 节周一课程应合并 `C2:C3`，实际生成 `C3:C4`，课程文字留在 `C2`，空白单元格却在下方合并，造成肉眼可见的错位。

正确公式：

```python
start_excel_row = period_index + 2
end_excel_row = start_excel_row + period_count - 1
```

#### 根因二：课表没有学期边界

[`backend/controllers/student_controller.py`](backend/controllers/student_controller.py) 的 `get_my_courses` 返回该学生所有学期的“已选”记录；前端只取第一门课程的学期文本，后端导出也把全部记录塞进一个 7×11 网格。跨学期同一时间的课程会覆盖或混排。

#### 根因三：允许的“同时间、不同教学周”会被导出覆盖

选课冲突逻辑允许相同星期和节次、但教学周不重叠的两门课。前端格子保存 `courses[]`，后端 Excel 网格却只有一个 `text` 字段，后写课程覆盖先写课程；导出文本也没有教学周，无法区分单双周或前后半学期课程。

#### 立即修复方案（低风险）

1. 将合并范围改为 `p + 2` 到 `p + 1 + rowspan`。
2. 导出 API 必须接收并验证 `semester`；学生只能导出自己的数据。
3. `get_my_courses(student_id, semester)` 按学期查询并稳定排序。
4. Excel 单元格保存课程列表，输出“课程名 / 地点 / 第 x-y 周”，同格多门课程用空行分隔。
5. 合并后显式设置 `wrap_text=True`、垂直居中、边框、行高、列宽、打印区域、横向打印和冻结首行。
6. 导出函数返回 `False` 时 API 返回 500 JSON 错误，不能读取并下载 `mkstemp` 创建的空文件。

#### 最佳方案（推荐）

移除 Controller 生成 A1 字符串的职责。Controller 返回结构化课表：

```text
semester
periods[]
days[]
cells[{ weekday, start_period, period_count, courses[] }]
```

Excel、网页和打印视图都消费同一结构；合并坐标只由 Excel 导出层用 `get_column_letter()` 计算。最终规则定为：若同一格课程的 `period_count` 不一致，该影响区域在三端都不做纵向合并，也不插入额外课表行；按固定 11 个原子节次格逐格列出覆盖该节次的课程及教学周。只有课程集合、起止节次和跨度完全一致时才允许合并。

必需回归测试：生成临时 `.xlsx` 后重新打开，断言 `C2:C3` 存在、`C2` 为课程文字、`C3` 为合并单元格；测试第 10–11 节边界、周日、单节课、跨学期、同时间不同教学周两门课、空课表和非法节次。

## 三、按优先级排列的其他问题

### P0：发布前必须修复

| 问题 | 证据与影响 | 具体修复 |
|---|---|---|
| 教师与学生数据存在 IDOR/资源越权 | [`backend/api/blueprints/teacher_bp.py`](backend/api/blueprints/teacher_bp.py) 的名单和成绩接口只校验“教师”角色，不校验计划归属；[`backend/api/blueprints/stats_bp.py`](backend/api/blueprints/stats_bp.py) 接受任意 `plan_id/student_id`，导出端点甚至只有 `require_auth`。教师可读取其他教师课程名单/成绩，学生可尝试导出其他学生信息。 | 新建共享 `authorize_plan_access(session, actor, plan_id)`；所有名单、成绩录入/批量录入/修改、分布、班级统计和导出统一调用。学生端忽略客户端 `student_id`，强制使用 token 中本人 ID；管理员跨用户访问单列为显式分支并写审计日志。 |
| 退课后重选绕过关键校验 | [`backend/controllers/enrollment_controller.py`](backend/controllers/enrollment_controller.py) 在发现“已退”记录后立即改回“已选”并增加人数，发生在冲突、容量锁和先修课校验之前，可超容量、制造冲突或绕过先修课。 | 只把“新建还是恢复”作为最终写入方式；所有路径先完成相同校验并取得行锁，最后再 insert 或 re-activate。增加真实数据库/事务回归测试。 |
| 选课校验异常时 fail-open | 同一控制器的选课时段异常返回 `valid=True`，冲突查询异常返回 `conflict=False`；数据库故障会放行本应拒绝的选课。 | 校验异常抛出领域错误或返回不可继续状态，API 返回 503/500；写操作 fail-closed，读取可以提供明确的“暂时不可用”状态。 |
| JWT 默认密钥可预测，锁定/登出不撤销 token | [`backend/api/auth.py`](backend/api/auth.py) 在未配置密钥时仅对固定前缀和主机名做 SHA256；主机名不是秘密。JWT 携带角色并在 24 小时内不查账号状态；`AuthController` 的内存 session store 每次实例化都重建，不能撤销 JWT。 | 当前阶段明确选择 `token_version`，不引入 Redis/jti blacklist。生产环境缺少强随机 `jwt_secret` 时拒绝启动；每次鉴权读取账号锁定状态、当前角色和 token_version；登出、改密、重置、锁定或角色变化递增版本。 |

### P1：本轮功能修复一起完成

| 问题 | 影响 | 具体修复 |
|---|---|---|
| 登出顺序反了 | [`frontend/src/stores/auth.js`](frontend/src/stores/auth.js) 先清 token，再调用需要 token 的 `/auth/logout`，必然产生 401、过期提示和重复跳转。 | 若保留服务端撤销，先带 token 调 logout，`finally` 再清本地；若 JWT 暂无撤销能力，删除无意义的服务端调用并只清本地。 |
| 导出失败仍返回 Excel 下载 | `export_stats_to_excel()` 的布尔结果被忽略，临时空文件仍会以 XLSX MIME 返回。 | 导出层失败时抛出类型化异常；返回前同时验证 ZIP/XLSX 签名、最低非零大小、可被 openpyxl 重开、目标 sheet/表头/关键合并范围存在。失败时返回 JSON 500；临时目录始终在 `finally` 清理。 |
| 课程计划输入缺少边界验证和数据库约束 | 教师可提交 `weekday=9`、起始节次越界、负容量、结束周早于开始周等数据，随后网页和导出会数组越界或产生错误统计。 | Blueprint 做类型/范围校验；Controller 做领域校验；数据库增加 weekday、period、week、capacity、enrolled 的 check constraint，并同步两套 DDL。 |
| 学期、总周数和节次时间多处硬编码 | 多个页面固定 `2026-2027-1`、20 周和 11 个时间字符串，但数据库已有 `semester_config` 与 `class_period`，配置变化后页面、冲突提示和导出不一致。 | 提供只读学期/节次配置 API，Pinia 缓存；所有页面和导出从同一来源读取。默认选择 `is_current=1` 的学期。 |
| 打印课表存在 HTML 注入面 | [`frontend/src/views/student/StudentSchedule.vue`](frontend/src/views/student/StudentSchedule.vue) 把课程名和地点拼进 `document.write`，若字段含 HTML 会进入新窗口 DOM。 | 建立 Vue 打印组件或使用 `textContent` 创建节点；最少也要对 `&<>"'` 完整转义。 |
| 登录/找回密码泄露账号存在性且无速率限制 | “用户不存在”和“密码错误”返回不同消息，公开找回接口也返回“账号不存在”；登录锁定可被恶意触发。 | 对外统一模糊消息；按 IP+账号做速率限制和渐进延迟；找回接口无论账号是否存在都返回相同结果；保留详细服务端审计。 |

### P2：质量与设计优化

| 问题 | 影响 | 具体修复 |
|---|---|---|
| Controller 广泛把异常吞成空列表/零统计 | 用户看到“暂无数据”而不是系统故障，监控和测试也难以发现真实问题。 | 使用领域异常；Blueprint 统一映射 4xx/5xx；空数据仅用于成功查询确实为空。 |
| 成绩和名单存在 N+1 查询 | 班级排名逐条查学生，教师成绩列表逐条查学生和成绩，数据量上升后明显变慢。 | 用一次 join/selectinload 返回所需字段，补充查询次数或性能基线测试。 |
| 成绩分布没有过滤空成绩 | `g.score is None` 时区间比较会抛异常，最终整个接口返回全零。 | 查询过滤 `Grade.score.isnot(None)`；`total` 明确定义为“已录入成绩数”，另返回未录入数。 |
| 移动端导航不完整 | 主布局和登录使用 `100vh`；仅压缩内容 padding，没有抽屉式侧栏与紧凑顶栏，账号和操作区在窄屏易溢出。 | 改 `100dvh`；768px 以下使用遮罩抽屉/顶部菜单，用户操作收进下拉菜单；增加真实 360/768/1440px 视觉测试。 |
| 视觉语言自相矛盾 | 设计变量声称单一蓝色强调，却同时定义珊瑚、薄荷、薰衣草与三种角色色；侧栏和登录页使用多色渐变、装饰圆点/浮动 blob，业务界面显得模板化。整个 `.page-card` hover 时抬升也把非交互容器伪装成可点击。 | 以学术蓝为唯一品牌强调，状态色只表达语义；删除无信息装饰与整页 hover，层级主要靠留白、分组和标题，不靠每块都加边框阴影。 |
| 字体不适合离线分发 | `Outfit` 从 Google Fonts 在线导入，`Satoshi` 未引入；便携离线部署会回退且产生不一致。 | 本地打包许可允许的 WOFF2，或明确采用系统中文字体栈；不要依赖生产网络字体。 |
| 可访问性与动效偏好未完整覆盖 | 图标/折叠按钮主要依赖 `title`，无 skip link；未处理 `prefers-reduced-motion`；加载多依赖遮罩 spinner。 | 为图标按钮加 `aria-label`，增加跳转主内容链接，禁用/简化减弱动效环境下的动画，用表格/卡片骨架匹配内容形状。 |
| 首屏包过大 | 本次 Vite 构建主 JS 约 2.38 MB，gzip 约 787 KB；ECharts、Element Plus 全局注册和所有图标全量注册是主要嫌疑。 | Element Plus 与图标按需引入，ECharts 仅注册所需图表/组件，配置 `manualChunks`，记录首屏预算。 |
| 测试覆盖偏科 | 22 个测试只覆盖认证、选课、成绩 controller 的 mock 路径；没有前端测试、Flask 权限集成、Excel、真实约束或构建验收。 | 新增 export、authorization、re-enroll、failure-mode、route/tab refresh 测试；前端使用 Vitest + Vue Test Utils（若同意新增开发依赖），关键流程再加浏览器 E2E。 |

## 四、建议实施批次

### 批次 A：安全与数据完整性

- 补所有资源归属校验与权限集成测试。
- 合并新选/重选写入流程，所有路径走行锁和五项校验。
- 校验失败改为 fail-closed。
- 生产 JWT 配置门禁、撤销策略、登录/找回限流。

验收门槛：跨教师、跨学生请求均得到 403；并发重选不超容量；数据库故障时选课不被放行。

### 批次 B：课表与刷新

- 结构化课表数据、学期过滤、合并坐标修复和真实 XLSX 回归测试。
- 页面 loader 标准化，审核内部页签按需刷新，跨页面 mutation 做数据域失效。
- 修正导出错误响应、登出顺序和打印 HTML 安全。

验收门槛：所有课表边界用例正确；切换页签得到新数据；失败下载不会产生空或伪装的 Excel。

### 批次 C：设计、可访问性与性能

- 移动端导航和 `100dvh`。
- 字体本地化、颜色/阴影/装饰收敛、非交互容器去 hover。
- Element Plus、图标、ECharts 按需引入并设置包体预算。
- 补 loading/empty/error/retry 与 reduced-motion。

验收门槛：360、768、1440px 无遮挡和横向页面溢出；键盘可完成核心流程；首屏主包显著下降且构建无大 chunk 警告。

## 五、本轮验证记录

- `python -m pytest tests/ -v`：22 passed；pytest 缓存目录因本机权限产生 1 个非业务 warning。
- `python -m compileall -q backend run.py run_prod.py`：通过。
- `npm.cmd run build`：通过；存在 Sass legacy API、router 静态/动态重复导入和大 chunk 警告。
- openpyxl 最小复现实验：课程文字位于 `C2`，当前合并范围为 `C3:C4`，确认 Excel 错位根因。
- 未执行登录后的全流程视觉走查；本轮没有使用或修改真实用户数据。

## 六、需要审阅的决策

建议批准以下默认选择：

1. 先实施批次 A，再实施批次 B，最后批次 C。
2. 不直接 cherry-pick `b0029979`，而是在当前 `main` 上按本方案重做并补测试。
3. 学生课表强制按单学期展示/导出；多学期采用选择器或每学期单独工作表，不混在一个网格。
4. 刷新采用 Pinia 数据域失效 + 页面 loader，不使用全浏览器 reload。
5. 权限统一放在共享资源授权函数，Blueprint 与 Controller 均不能只凭客户端 ID。

## 七、针对本轮审阅问题的架构定案

### 7.1 授权函数如何做到“遗漏即失败”

不能依赖开发者在每个 endpoint 手写一行 `authorize_plan_access(...)`。采用三层强制机制：

1. **声明式装饰器**：提供 `@require_plan_access(capability, source)`，在鉴权与角色检查之后调用唯一的 `authorize_plan_access(session, actor, plan_id, capability)`。`source` 明确 plan_id 来自 path、query、JSON body 或 form。授权成功后只把经过验证的 plan_id/actor context 传入业务层。
2. **路由清单闭包测试**：维护覆盖全部非公开 API 的 `ACCESS_POLICY_MANIFEST`，每个 endpoint 必须分类为 `self/plan/admin/role-only/public` 并声明 capability；plan 类型再进入 `PLAN_SCOPED_ENDPOINTS`，豁免必须写原因。测试比较 `app.url_map` 与 manifest 的集合完全相等，并要求敏感 view 带授权装饰器写入的 capability 元数据。任何蓝图新增路由但未分类时测试直接失败；另用 AST/源码检查标记“读取 plan_id 却未声明 plan policy”的路由。
3. **黑盒越权参数化测试**：不能只检查装饰器标记。对名单、成绩查询/录入/批量录入/修改、班级统计、分布及导出逐个使用“教师 A + 教师 B 的 plan_id”，强制断言 403；学生跨账号导出同样断言拒绝或忽略目标参数后只返回本人数据。

Controller 的公共写方法仍接收 `ActorContext` 并再次调用 policy，防止脚本、后台任务或未来非 HTTP 调用绕过 Blueprint。测试清单是合并阻断项，不允许通过 broad exemption 绕过。

### 7.2 重选并发、锁顺序与死锁规避

现有 `UNIQUE(student_id, plan_id)` 已存在于 ORM、MySQL DDL 和 SQL Server DDL，保留为最终一致性兜底。事务统一使用以下锁序：

1. 按 `student_id` 锁定 `student` 行，串行化同一学生的选课/退课，防止同时选择两门互相冲突课程时各自读到旧快照。
2. 按 `plan_id` 锁定目标 `course_plan` 行，串行化容量检查与人数更新。
3. 按 `(student_id, plan_id)` 锁定已有 `enrollment` 行；不存在时依赖唯一约束处理插入竞态。
4. 在持锁事务内执行时段、重复、冲突、容量、先修课校验；最后才 insert 或把“已退”恢复为“已选”，并写操作日志。

所有选课、重选、退课和管理员相关写路径必须使用同一顺序；批量操作按 student_id、plan_id 排序后加锁。事务内不做文件、网络或前端通知。MySQL 使用 `SELECT ... FOR UPDATE`；SQL Server 使用 `UPDLOCK + ROWLOCK + HOLDLOCK` 等等价提示，不能把普通 `READ COMMITTED` 当作行锁。仅对 MySQL 1213 / SQL Server 1205 做最多 2 次带抖动重试，其他异常立即失败。唯一约束冲突转换为幂等的 409，而不是 500。

### 7.3 fail-open 改造后的统一错误语义

API 错误增加稳定的机器码：`{ success:false, code, message, data?, request_id }`。

| HTTP | 语义 | 示例 code |
|---|---|---|
| 400 | 请求结构/类型错误 | `INVALID_REQUEST` |
| 401 | token 缺失、过期、撤销或账号锁定导致认证失效 | `TOKEN_EXPIRED`, `TOKEN_REVOKED`, `ACCOUNT_LOCKED` |
| 403 | 已认证但无角色或资源权限 | `PLAN_ACCESS_DENIED` |
| 404 | 当前主体可安全获知但资源不存在 | `PLAN_NOT_FOUND` |
| 409 | 当前状态冲突 | `ENROLLMENT_CLOSED`, `ALREADY_ENROLLED`, `COURSE_FULL`, `TIME_CONFLICT` |
| 422 | 数据语义不合法 | `PREREQUISITE_NOT_MET`, `INVALID_SCHEDULE`, `INVALID_SCORE` |
| 500 | 未预期代码/导出故障 | `INTERNAL_ERROR`, `EXPORT_FAILED` |
| 503 | 数据库或必需系统配置不可用 | `DATABASE_UNAVAILABLE`, `SEMESTER_NOT_CONFIGURED` |

前端请求层抛出包含 status/code/request_id 的 `ApiError`。数据页状态严格区分 `loading`、`success-empty`、`success-data`、`error`；只有成功响应且 items 为空才能显示“暂无数据”。5xx/503 显示错误面板、request_id 和重试按钮。Blob 下载失败时根据响应 Content-Type 解析 JSON Blob，不能把错误内容当 Excel 下载。

### 7.4 JWT 撤销策略

当前阶段选择 **token_version + 每次鉴权查账号状态**：

- `user_account` 增加 `token_version NOT NULL DEFAULT 0`，JWT 带 version；角色以数据库当前值为准，不只信 token 中的 role。
- `require_auth` 每次请求读取用户，检查存在、未锁定、token_version 相等；数据库不可用返回 503并拒绝业务请求。
- 登出、修改密码、管理员重置、账号锁定/解锁和角色变更递增 token_version，使该账号所有旧 token 立即失效。
- 此选择会撤销该用户所有设备会话；这是当前无 Redis 方案的明确产品取舍。以后需要“只退出当前设备”时，再引入带 TTL 的 jti denylist；现在不同时维护两套撤销状态。

### 7.5 导出权限边界与审计

- 学生 schedule/academic export 的 schema 不接收 `student_id`；目标账号只能取 `g.current_user.user_id`。即使客户端偷偷发送该字段，也不得影响查询，建议返回 422 `UNEXPECTED_TARGET_ID` 以暴露错误调用。
- 教师只可导出自己 plan 的班级/成绩统计，必须走 plan access policy。
- 管理员代导出使用单独 endpoint/schema，必须提供 `target_student_id`、`semester`、`reason`。审计日志记录 actor、target、export_type、semester、reason、IP、时间、结果和 request_id；日志与授权检查不能被普通学生/教师路径复用绕过。

### 7.6 Excel 同格多课程三端一致规则

最终采用“不合并”，不采用动态拆行：

- 课表始终保留 11 个原子节次行，网页、打印和 Excel 使用同一结构化 grid builder。
- 同一起点课程跨度完全相同，可合并并在一个格内按“课程 / 地点 / 周次”逐条展示。
- 同一起点或覆盖区域存在不同 period_count 时，该区域全部不纵向合并；每个节次格列出覆盖该节次的所有课程及周次。
- 三端共用同一组 fixture/snapshot，分别断言 cell coverage、打印 DOM 和 Excel merge ranges，避免视觉规则漂移。

### 7.7 学期单一真源与异常状态

短期保留 `semester_config.is_current`，但增加数据库“最多一条 current”的约束：MySQL 使用可空 generated guard + unique index，SQL Server 使用 `WHERE is_current = 1` 的 filtered unique index。管理员切换当前学期时在一个事务内锁定配置集合、清零旧值、设置目标并断言结果恰好一条。

唯一的 `CurrentSemesterResolver` 要求查询结果**恰好一条**：0 条或多条都是配置故障，返回 503 `SEMESTER_NOT_CONFIGURED/SEMESTER_CONFIG_CONFLICT` 并记录高优先级日志，禁止回退到硬编码学期。前端默认学期 API、选课默认条件、课表页面与导出默认学期全部调用该 resolver；显式查看历史学期仍需验证学期存在。

### 7.8 导出成功判定与临时文件清理

导出函数不再返回布尔值，成功返回已验证的 bytes/路径，失败抛 `ExportError`。判定标准同时包括：

1. 文件存在且大小超过最小 sanity 阈值（仅辅助，不作为唯一依据）。
2. `zipfile.is_zipfile(path)` 为真，文件头符合 XLSX ZIP 容器。
3. `openpyxl.load_workbook(path)` 可重开。
4. 目标 sheet、固定表头、代表性单元格和期望 merge ranges 符合本次 export model。

使用 `TemporaryDirectory()` 生成目录和目标文件，导出、验证、读取 bytes 都在 `try` 中，目录在 `finally/context manager` 无条件清理；读取成功后再构造响应。任何阶段失败都返回 JSON `EXPORT_FAILED`，不发送空文件。

### 7.9 TTL 与窗口聚焦刷新

TTL 放在 `frontend/src/config/refresh-policy.js`，允许通过 `VITE_*` 环境变量覆盖：

- enrollment、schedule、audit 列表/角标：30 秒。
- grades、academic/enrollment stats、logs：60 秒。
- semester/class-period 等参考配置：300 秒。

mutation 成功立即失效相关域，所以 TTL 只控制被动刷新。全局只监听一种可见性恢复事件；仅当页面隐藏超过 15 秒且数据已过 TTL 才刷新，focus/visibility 触发至少间隔 10 秒，同一数据域复用 in-flight promise，并用请求序号防止旧响应覆盖新响应。

### 7.10 最低回归门槛与 CI 阻断条件

以下不是“建议用例”，而是合并硬门槛：

1. **授权**：路由清单闭包测试；teacher roster/grades/record/batch/modify/class/distribution/export 的跨 plan 参数化 403；student schedule/academic export 跨账号不能生效；admin 代导出审计字段完整。
2. **并发**：MySQL 8 真实数据库上覆盖容量为 1 的双学生并发、同一学生并发选择冲突课程、已退记录并发重选、重选满课、唯一约束竞态和死锁重试。Mock/SQLite 结果不能替代这些用例。
3. **JWT**：锁定账号、token_version 不匹配、登出、改密、重置和角色变更后旧 token 全部失效。
4. **错误语义**：业务冲突返回指定 409/422 code；数据库故障为 503；前端 5xx 显示 error 而非 empty；Blob JSON 错误不触发下载。
5. **Excel**：`C2:C3`、`C2` 课程文字和 `C3` merged-cell 是固定断言；另覆盖周日、第 10–11 节、单节、空表、非法边界、学期隔离、同格同跨度合并、同格不同跨度不合并及多课程文本周次。
6. **刷新**：内部 tab 每次过期切换只触发一次正确 loader；mutation 立即失效；focus 刷新符合 TTL/节流；旧响应不覆盖新响应。
7. **学期**：0 current 返回 503，多 current 被 DB/启动检查阻断，前端默认与导出默认解析为同一 semester id。

CI 必须全部通过现有 22 项及上述关键套件，关键测试不得 skip/xfail；执行 `compileall`、后端 unit/integration、MySQL 并发、Excel reopen assertions、前端组件测试和 `npm.cmd run build`。新增/修改核心文件采用至少 90% diff coverage；授权 policy、锁序 helper、current-semester resolver 和 export validator 要求分支全覆盖。`C2:C3` 断言单独标为 critical，失败直接阻断合并。SQL Server 至少执行 DDL/约束兼容检查，锁语义集成测试纳入发布前或定时流水线。
