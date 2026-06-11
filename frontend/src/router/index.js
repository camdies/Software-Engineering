import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/LoginView.vue'),
    meta: { public: true },
  },
  {
    path: '/',
    component: () => import('@/layouts/MainLayout.vue'),
    redirect: () => {
      const auth = useAuthStore()
      if (auth.isAdmin) return '/admin/students'
      if (auth.isTeacher) return '/teacher/plans'
      if (auth.isStudent) return '/student/enroll'
      return '/login'
    },
    children: [
      // ── Admin routes ──
      { path: 'admin/students', name: 'AdminStudents', component: () => import('@/views/admin/AdminStudents.vue'), meta: { role: 'admin', title: '学生管理' } },
      { path: 'admin/teachers', name: 'AdminTeachers', component: () => import('@/views/admin/AdminTeachers.vue'), meta: { role: 'admin', title: '教师管理' } },
      { path: 'admin/courses', name: 'AdminCourses', component: () => import('@/views/admin/AdminCourses.vue'), meta: { role: 'admin', title: '课程管理' } },
      { path: 'admin/course-plans', name: 'AdminCoursePlans', component: () => import('@/views/admin/AdminCoursePlans.vue'), meta: { role: 'admin', title: '开课计划' } },
      { path: 'admin/audit', name: 'AdminAudit', component: () => import('@/views/admin/AdminAudit.vue'), meta: { role: 'admin', title: '审核中心' } },
      { path: 'admin/enrollment-stats', name: 'AdminEnrollmentStats', component: () => import('@/views/admin/AdminEnrollmentStats.vue'), meta: { role: 'admin', title: '选课统计' } },
      { path: 'admin/logs', name: 'AdminLogs', component: () => import('@/views/admin/AdminLogs.vue'), meta: { role: 'admin', title: '操作日志' } },

      // ── Teacher routes ──
      { path: 'teacher/plans', name: 'TeacherPlans', component: () => import('@/views/teacher/TeacherPlans.vue'), meta: { role: 'teacher', title: '授课计划' } },
      { path: 'teacher/grades', name: 'TeacherGrades', component: () => import('@/views/teacher/TeacherGrades.vue'), meta: { role: 'teacher', title: '成绩录入' } },
      { path: 'teacher/grade-modify', name: 'TeacherGradeModify', component: () => import('@/views/teacher/TeacherGradeModify.vue'), meta: { role: 'teacher', title: '成绩修改' } },
      { path: 'teacher/stats', name: 'TeacherStats', component: () => import('@/views/teacher/TeacherStats.vue'), meta: { role: 'teacher', title: '统计分析' } },

      // ── Student routes ──
      { path: 'student/enroll', name: 'StudentEnroll', component: () => import('@/views/student/StudentEnroll.vue'), meta: { role: 'student', title: '选课' } },
      { path: 'student/my-courses', name: 'StudentSchedule', component: () => import('@/views/student/StudentSchedule.vue'), meta: { role: 'student', title: '个人课表' } },
      { path: 'student/grades', name: 'StudentGrades', component: () => import('@/views/student/StudentGrades.vue'), meta: { role: 'student', title: '成绩查询' } },
      { path: 'student/stats', name: 'StudentStats', component: () => import('@/views/student/StudentStats.vue'), meta: { role: 'student', title: '学业统计' } },
    ],
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to, _from, next) => {
  const auth = useAuthStore()

  if (to.meta.public) {
    if (auth.isLoggedIn && to.path === '/login') {
      if (auth.isAdmin) return next('/admin/students')
      if (auth.isTeacher) return next('/teacher/plans')
      if (auth.isStudent) return next('/student/enroll')
    }
    return next()
  }

  if (!auth.isLoggedIn) {
    return next('/login')
  }

  if (to.meta.role && to.meta.role !== auth.role) {
    return next('/login')
  }

  next()
})

export default router
