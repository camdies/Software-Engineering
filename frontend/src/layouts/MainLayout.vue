<template>
  <el-container class="main-container">
    <el-aside :width="sidebarCollapsed ? '64px' : '220px'" class="main-sidebar">
      <div class="sidebar-logo" @click="sidebarCollapsed = !sidebarCollapsed">
        <span v-if="!sidebarCollapsed" class="logo-text">教务管理系统</span>
        <span v-else class="logo-icon">📚</span>
      </div>

      <el-menu
        :default-active="route.path"
        :collapse="sidebarCollapsed"
        :collapse-transition="false"
        router
        background-color="#304156"
        text-color="#bfcbd9"
        active-text-color="#409eff"
      >
        <!-- Admin menu -->
        <template v-if="auth.isAdmin">
          <el-sub-menu index="admin-people">
            <template #title><el-icon><UserFilled /></el-icon><span>人员管理</span></template>
            <el-menu-item index="/admin/students"><el-icon><User /></el-icon><span>学生管理</span></el-menu-item>
            <el-menu-item index="/admin/teachers"><el-icon><Avatar /></el-icon><span>教师管理</span></el-menu-item>
          </el-sub-menu>
          <el-sub-menu index="admin-courses">
            <template #title><el-icon><Reading /></el-icon><span>课程管理</span></template>
            <el-menu-item index="/admin/courses"><el-icon><Collection /></el-icon><span>课程信息</span></el-menu-item>
            <el-menu-item index="/admin/course-plans"><el-icon><Notebook /></el-icon><span>开课计划</span></el-menu-item>
          </el-sub-menu>
          <el-menu-item index="/admin/audit"><el-icon><Checked /></el-icon><span>审核中心</span></el-menu-item>
          <el-menu-item index="/admin/enrollment-stats"><el-icon><DataAnalysis /></el-icon><span>选课统计</span></el-menu-item>
          <el-menu-item index="/admin/logs"><el-icon><Tickets /></el-icon><span>操作日志</span></el-menu-item>
        </template>

        <!-- Teacher menu -->
        <template v-if="auth.isTeacher">
          <el-menu-item index="/teacher/plans"><el-icon><Notebook /></el-icon><span>授课计划</span></el-menu-item>
          <el-sub-menu index="teacher-grade">
            <template #title><el-icon><Document /></el-icon><span>成绩管理</span></template>
            <el-menu-item index="/teacher/grades"><el-icon><Edit /></el-icon><span>成绩录入</span></el-menu-item>
            <el-menu-item index="/teacher/grade-modify"><el-icon><Warning /></el-icon><span>修改申请</span></el-menu-item>
          </el-sub-menu>
          <el-menu-item index="/teacher/stats"><el-icon><DataAnalysis /></el-icon><span>统计分析</span></el-menu-item>
        </template>

        <!-- Student menu -->
        <template v-if="auth.isStudent">
          <el-sub-menu index="student-enrollment">
            <template #title><el-icon><Select /></el-icon><span>选课管理</span></template>
            <el-menu-item index="/student/enroll"><el-icon><CirclePlus /></el-icon><span>选课</span></el-menu-item>
            <el-menu-item index="/student/my-courses"><el-icon><List /></el-icon><span>个人课表</span></el-menu-item>
          </el-sub-menu>
          <el-menu-item index="/student/grades"><el-icon><Document /></el-icon><span>成绩查询</span></el-menu-item>
          <el-menu-item index="/student/stats"><el-icon><DataAnalysis /></el-icon><span>学业统计</span></el-menu-item>
        </template>
      </el-menu>
    </el-aside>

    <el-container>
      <el-header class="main-header">
        <div class="header-left">
          <el-button text @click="app.toggleSidebar()">
            <el-icon :size="20"><Expand v-if="sidebarCollapsed" /><Fold v-else /></el-icon>
          </el-button>
          <el-breadcrumb separator="/" class="header-breadcrumb">
            <el-breadcrumb-item :to="{ path: '/' }">首页</el-breadcrumb-item>
            <el-breadcrumb-item v-if="activeMenu">{{ activeMenu }}</el-breadcrumb-item>
          </el-breadcrumb>
        </div>
        <div class="header-right">
          <el-tag :type="roleType">{{ roleLabel }}</el-tag>
          <span class="header-user">{{ auth.userId }}</span>
          <el-button text type="primary" @click="showPwdDialog = true">修改密码</el-button>
          <el-button text type="danger" @click="handleLogout">退出登录</el-button>
        </div>
      </el-header>

      <el-main class="main-content">
        <router-view />
      </el-main>
    </el-container>
  </el-container>

  <ChangePasswordDialog v-model:visible="showPwdDialog" />
</template>

<script setup>
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useAppStore } from '@/stores/app'
import { ROLE_LABELS } from '@/utils/constants'
import ChangePasswordDialog from '@/components/ChangePasswordDialog.vue'
import {
  UserFilled, User, Avatar, Reading, Collection, Notebook, Select, Setting,
  DataAnalysis, Document, Checked, Monitor, Tickets, Edit, Warning,
  CirclePlus, List, Expand, Fold,
} from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const app = useAppStore()

const sidebarCollapsed = computed(() => app.sidebarCollapsed)
const activeMenu = computed(() => route.meta?.title || '')
const roleLabel = computed(() => ROLE_LABELS[auth.role] || auth.role)
const roleType = computed(() => {
  if (auth.isAdmin) return 'danger'
  if (auth.isTeacher) return 'warning'
  return 'success'
})

const showPwdDialog = ref(false)

async function handleLogout() {
  await auth.logout()
  router.push('/login')
}
</script>

<style scoped>
.main-container { height: 100vh; }
.main-sidebar { background-color: #304156; overflow-y: auto; transition: width 0.3s; }
.sidebar-logo { height: 60px; display: flex; align-items: center; justify-content: center; color: #fff; cursor: pointer; font-size: 18px; font-weight: bold; border-bottom: 1px solid rgba(255,255,255,0.1); }
.logo-icon { font-size: 24px; }
.main-header { display: flex; align-items: center; justify-content: space-between; background: #fff; border-bottom: 1px solid #e6e6e6; padding: 0 20px; height: 60px; }
.header-left { display: flex; align-items: center; gap: 12px; }
.header-right { display: flex; align-items: center; gap: 12px; }
.header-user { color: #333; font-weight: 500; }
.main-content { background: #f0f2f5; min-height: calc(100vh - 60px); padding: 20px; }
</style>
