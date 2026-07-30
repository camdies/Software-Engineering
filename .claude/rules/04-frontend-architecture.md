---
description: 前端规范（组件、状态管理、HTTP、UI框架、路由）——修改前端 Vue/JS 代码时必须遵守
alwaysApply: false
globs:
  - "frontend/**/*.vue"
  - "frontend/**/*.js"
  - "frontend/**/*.scss"
version: 1.0.0
---

# 前端规范

- **组件**: Composition API (`<script setup>`)
- **状态管理**: Pinia (`stores/auth.js` + `stores/app.js`)
- **HTTP 客户端**: Axios 实例 (`utils/request.js`)，含 JWT 拦截器 + 401/403 自动处理
- **UI 框架**: Element Plus，全局样式覆盖在 `styles/global.scss`
- **页面组件**: 按角色分目录 `views/admin/`, `views/teacher/`, `views/student/`

## 关键规则

- **Pinia 必须在 Router 之前**: `main.js` 中 `createPinia()` → `app.use(pinia)` → `app.use(router)`，顺序不能变

## 新增前端页面流程

1. 在 `views/<角色>/` 创建 `.vue` 文件
2. 在 `router/index.js` 注册路由 + `meta.roles` 权限
3. 如需后端数据，先确认 API 端点是否已存在

## 标签页切换数据不刷新

学生端 "选课" 和 "个人课表" 等页签切换时，Vue Router 复用组件不会重新触发 `onMounted`。已在 `StudentSchedule.vue` 中通过 `watch(() => route.path, ...)` 解决。新增页面时注意同样的问题。
