<template>
  <div class="app-shell">
    <!-- Sidebar — light fresh academic style -->
    <aside class="sidebar" :class="{ collapsed: sidebarCollapsed }">
      <!-- Decorative top gradient bar -->
      <div class="sidebar-accent-bar"></div>

      <div class="sidebar-brand" @click="sidebarCollapsed = !sidebarCollapsed">
        <span class="brand-mark">E</span>
        <transition name="fade-slide">
          <span v-if="!sidebarCollapsed" class="brand-text">教务管理</span>
        </transition>
      </div>

      <el-menu
        :default-active="route.path"
        :collapse="sidebarCollapsed"
        :collapse-transition="false"
        router
        class="sidebar-menu"
      >
        <template v-if="auth.isAdmin">
          <el-sub-menu index="admin-people">
            <template #title><el-icon><UserFilled /></el-icon><span>人员管理</span></template>
            <el-menu-item index="/admin/students"><span>学生管理</span></el-menu-item>
            <el-menu-item index="/admin/teachers"><span>教师管理</span></el-menu-item>
          </el-sub-menu>
          <el-sub-menu index="admin-courses">
            <template #title><el-icon><Reading /></el-icon><span>课程管理</span></template>
            <el-menu-item index="/admin/courses"><span>课程信息</span></el-menu-item>
            <el-menu-item index="/admin/course-plans"><span>开课计划</span></el-menu-item>
          </el-sub-menu>
          <el-menu-item index="/admin/audit"><el-icon><Checked /></el-icon><span>审核中心</span></el-menu-item>
          <el-menu-item index="/admin/enrollment-control"><el-icon><Timer /></el-icon><span>选课控制</span></el-menu-item>
          <el-menu-item index="/admin/enrollment-stats"><el-icon><DataAnalysis /></el-icon><span>选课统计</span></el-menu-item>
          <el-menu-item index="/admin/logs"><el-icon><Tickets /></el-icon><span>操作日志</span></el-menu-item>
        </template>

        <template v-if="auth.isTeacher">
          <el-menu-item index="/teacher/plans"><el-icon><Notebook /></el-icon><span>授课计划</span></el-menu-item>
          <el-sub-menu index="teacher-grade">
            <template #title><el-icon><Document /></el-icon><span>成绩管理</span></template>
            <el-menu-item index="/teacher/grades"><span>成绩录入</span></el-menu-item>
            <el-menu-item index="/teacher/grade-modify"><span>修改申请</span></el-menu-item>
          </el-sub-menu>
          <el-menu-item index="/teacher/stats"><el-icon><DataAnalysis /></el-icon><span>统计分析</span></el-menu-item>
        </template>

        <template v-if="auth.isStudent">
          <el-sub-menu index="student-enrollment">
            <template #title><el-icon><Select /></el-icon><span>选课管理</span></template>
            <el-menu-item index="/student/enroll"><span>选课</span></el-menu-item>
            <el-menu-item index="/student/my-courses"><span>个人课表</span></el-menu-item>
          </el-sub-menu>
          <el-menu-item index="/student/grades"><el-icon><Document /></el-icon><span>成绩查询</span></el-menu-item>
          <el-menu-item index="/student/stats"><el-icon><DataAnalysis /></el-icon><span>学业统计</span></el-menu-item>
        </template>
      </el-menu>

      <!-- Decorative bottom illustration -->
      <div v-if="!sidebarCollapsed" class="sidebar-illustration">
        <div class="illustration-dot dot-1"></div>
        <div class="illustration-dot dot-2"></div>
        <div class="illustration-dot dot-3"></div>
        <span class="version-tag">v3.0</span>
      </div>
    </aside>

    <!-- Main area -->
    <div class="main-area">
      <header class="topbar">
        <div class="topbar-left">
          <button class="collapse-btn" @click="app.toggleSidebar()" :title="sidebarCollapsed ? '展开菜单' : '收起菜单'">
            <el-icon :size="18"><Expand v-if="sidebarCollapsed" /><Fold v-else /></el-icon>
          </button>
          <el-breadcrumb separator="/" class="topbar-breadcrumb">
            <el-breadcrumb-item :to="{ path: '/' }">首页</el-breadcrumb-item>
            <el-breadcrumb-item v-if="activeMenu">{{ activeMenu }}</el-breadcrumb-item>
          </el-breadcrumb>
        </div>
        <div class="topbar-right">
          <span class="role-badge" :class="`role-${auth.role}`">{{ roleLabel }}</span>
          <span class="user-name">{{ auth.userId }}</span>
          <button class="text-btn" @click="showPwdDialog = true">修改密码</button>
          <button class="text-btn danger" @click="handleLogout">退出</button>
        </div>
      </header>

      <main class="content-area">
        <router-view v-slot="{ Component, route: resolved }">
          <transition name="fade-slide" mode="out-in">
            <component :is="Component" :key="resolved.fullPath" />
          </transition>
        </router-view>
      </main>
    </div>
  </div>

  <ChangePasswordDialog v-model:visible="showPwdDialog" />
</template>

<script setup>
import { computed, ref, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useAppStore } from '@/stores/app'
import { ROLE_LABELS } from '@/utils/constants'
import ChangePasswordDialog from '@/components/ChangePasswordDialog.vue'
import {
  UserFilled, Reading, Collection, Notebook, Select,
  DataAnalysis, Document, Checked, Tickets, Edit, Warning,
  CirclePlus, List, Expand, Fold, Timer,
} from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const app = useAppStore()

const sidebarCollapsed = computed(() => app.sidebarCollapsed)
const activeMenu = computed(() => route.meta?.title || '')
const roleLabel = computed(() => ROLE_LABELS[auth.role] || auth.role)

const showPwdDialog = ref(false)

async function handleLogout() {
  await auth.logout()
  await nextTick()
  try {
    await router.push('/login')
  } catch (_) {
    window.location.href = '/login'
  }
}
</script>

<style scoped>
/* ── Shell ───────────────────────────────────────────────────── */
.app-shell {
  display: flex;
  height: 100vh;
  overflow: hidden;
}

/* ── Sidebar — Light Fresh Academic ──────────────────────────── */
.sidebar {
  width: var(--sidebar-width);
  background: var(--surface-sidebar);
  display: flex;
  flex-direction: column;
  transition: width var(--duration-normal) var(--ease-out);
  flex-shrink: 0;
  position: relative;
  border-right: 1px solid rgba(99, 102, 241, 0.08);
}
.sidebar.collapsed { width: var(--sidebar-collapsed); }

/* Decorative top accent bar */
.sidebar-accent-bar {
  position: absolute;
  top: 0; left: 0; right: 0;
  height: 3px;
  background: linear-gradient(90deg, var(--role-admin), var(--accent-500), var(--mint-400), var(--coral-400));
}

.sidebar-brand {
  height: var(--header-height);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-3);
  cursor: pointer;
  user-select: none;
  flex-shrink: 0;
}
.brand-mark {
  width: 38px; height: 38px;
  border-radius: var(--radius-md);
  background: linear-gradient(135deg, var(--accent-500), var(--role-admin));
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: var(--font-display);
  font-weight: var(--weight-bold);
  font-size: 1.3rem;
  flex-shrink: 0;
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.25);
}
.brand-text {
  font-family: var(--font-display);
  font-size: 1.1rem;
  font-weight: var(--weight-semibold);
  color: var(--neutral-800);
  letter-spacing: var(--tracking-tight);
  white-space: nowrap;
}

/* ── Sidebar Menu (light version) ────────────────────────────── */
.sidebar-menu {
  flex: 1;
  overflow-y: auto;
  padding: var(--space-2) var(--space-2);
  background: transparent;
  border-right: none;
}

.sidebar-menu :deep(.el-menu) { background: transparent; }
.sidebar-menu :deep(.el-sub-menu__title),
.sidebar-menu :deep(.el-menu-item) {
  height: 42px;
  line-height: 42px;
  margin: 2px 4px;
  border-radius: var(--radius-md);
  color: var(--neutral-600);
  font-size: var(--text-scale-sm);
  transition: all var(--duration-fast) var(--ease-out);
}
.sidebar-menu :deep(.el-sub-menu__title:hover),
.sidebar-menu :deep(.el-menu-item:hover) {
  background: var(--surface-sidebar-hover);
  color: var(--neutral-800);
}
.sidebar-menu :deep(.el-menu-item.is-active) {
  background: var(--surface-sidebar-active);
  color: var(--accent-700);
  font-weight: var(--weight-semibold);
  box-shadow: inset 3px 0 0 var(--accent-500);
}
.sidebar-menu :deep(.el-sub-menu .el-menu) {
  background: transparent;
}
.sidebar-menu :deep(.el-sub-menu .el-menu-item) {
  padding-left: 56px !important;
  font-size: var(--text-scale-xs);
}

.sidebar-menu :deep(.el-sub-menu__icon-arrow) { color: var(--neutral-400); }
.sidebar-menu :deep(.el-icon) { color: var(--neutral-400); }
.sidebar-menu :deep(.el-menu-item.is-active .el-icon) { color: var(--accent-500); }

/* ── Sidebar bottom illustration ─────────────────────────────── */
.sidebar-illustration {
  padding: var(--space-4) var(--space-4) var(--space-5);
  text-align: center;
  position: relative;
}
.illustration-dot {
  display: inline-block;
  border-radius: 50%;
  margin: 0 3px;
  opacity: 0.35;
}
.illustration-dot.dot-1 { width: 8px; height: 8px; background: var(--role-admin); }
.illustration-dot.dot-2 { width: 10px; height: 10px; background: var(--accent-500); }
.illustration-dot.dot-3 { width: 6px; height: 6px; background: var(--mint-400); }
.version-tag {
  display: block;
  margin-top: var(--space-2);
  font-size: var(--text-scale-2xs);
  color: var(--neutral-300);
  font-family: var(--font-mono);
  letter-spacing: 0.06em;
}

/* ── Topbar — Light glass ────────────────────────────────────── */
.main-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.topbar {
  height: var(--header-height);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 var(--space-5);
  background: var(--surface-header);
  backdrop-filter: blur(12px) saturate(180%);
  -webkit-backdrop-filter: blur(12px) saturate(180%);
  border-bottom: var(--border-light);
  flex-shrink: 0;
  z-index: var(--z-header);
}
.topbar-left { display: flex; align-items: center; gap: var(--space-3); }
.topbar-right { display: flex; align-items: center; gap: var(--space-3); }

.collapse-btn {
  width: 32px; height: 32px;
  display: flex; align-items: center; justify-content: center;
  border: none; background: transparent;
  border-radius: var(--radius-md);
  color: var(--neutral-400);
  cursor: pointer;
  transition: all var(--duration-fast) var(--ease-out);
}
.collapse-btn:hover { background: var(--neutral-100); color: var(--neutral-600); }

.topbar-breadcrumb { font-size: var(--text-scale-sm); }

/* Role badge */
.role-badge {
  font-size: var(--text-scale-xs);
  font-weight: var(--weight-semibold);
  padding: 2px 10px;
  border-radius: var(--radius-full);
  letter-spacing: 0.03em;
}
.role-badge.role-admin   { background: rgba(99,102,241,0.10); color: var(--role-admin); }
.role-badge.role-teacher { background: rgba(5,150,105,0.10); color: var(--role-teacher); }
.role-badge.role-student { background: rgba(217,119,6,0.10); color: var(--role-student); }

.user-name {
  font-size: var(--text-scale-sm);
  font-weight: var(--weight-medium);
  color: var(--neutral-600);
}

.text-btn {
  border: none; background: none;
  font-family: var(--font-body);
  font-size: var(--text-scale-sm);
  color: var(--accent-600);
  cursor: pointer;
  padding: var(--space-1) var(--space-2);
  border-radius: var(--radius-sm);
  transition: all var(--duration-fast) var(--ease-out);
}
.text-btn:hover { background: var(--accent-50); }
.text-btn.danger { color: var(--semantic-danger); }
.text-btn.danger:hover { background: var(--semantic-danger-bg); }

/* ── Content ─────────────────────────────────────────────────── */
.content-area {
  flex: 1;
  overflow-y: auto;
  padding: var(--content-padding);
}
</style>
