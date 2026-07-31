<template>
  <div class="page-card">
    <div class="page-header">
      <h1>个人课表</h1>
      <div class="actions">
        <el-button :loading="loading" @click="loadData({ force: true })">刷新</el-button>
        <el-button :disabled="loading || !!error" @click="exportExcel">导出 Excel</el-button>
        <el-button type="primary" :disabled="loading || !!error" @click="printSchedule">打印 / PDF</el-button>
      </div>
    </div>

    <el-alert v-if="error" type="error" :closable="false" show-icon class="state-panel">
      <template #title>课表加载失败</template>
      <div>{{ error.message }}<span v-if="error.requestId">（请求ID: {{ error.requestId }}）</span></div>
      <el-button size="small" @click="loadData({ force: true })">重试</el-button>
    </el-alert>

    <template v-else>
      <div class="schedule-tags">
        <el-tag size="large" type="info">学期: {{ semester || '--' }}</el-tag>
        <el-tag size="large" type="success">总周数: {{ totalWeeks }}周</el-tag>
        <el-tag size="large" type="warning">已选: {{ myCourses.length }}门</el-tag>
        <el-tag size="large">学分: {{ totalCredits.toFixed(1) }}</el-tag>
      </div>

      <div ref="scheduleRef" class="schedule-wrapper" v-loading="loading">
        <table class="schedule-table">
          <thead><tr>
            <th class="time-col">节次 / 时间</th>
            <th v-for="name in weekdayNames" :key="name" class="day-col">{{ name }}</th>
          </tr></thead>
          <tbody>
            <tr v-for="period in 11" :key="period">
              <th scope="row" class="time-cell">
                <div class="period-num">第{{ period }}节</div>
                <div class="period-time">{{ periodTimes[period - 1] }}</div>
              </th>
              <template v-for="day in 7" :key="day">
                <td
                  v-if="!scheduleGrid[period - 1][day - 1].covered"
                  class="slot-cell"
                  :rowspan="scheduleGrid[period - 1][day - 1].rowspan"
                >
                  <div
                    v-for="course in scheduleGrid[period - 1][day - 1].courses"
                    :key="course.plan_id"
                    class="course-block"
                    :style="blockStyle(course)"
                  >
                    <div class="cb-name">{{ course.course_name }}</div>
                    <div class="cb-loc">{{ course.location || '' }}</div>
                    <div class="cb-weeks">{{ course.start_week }}-{{ course.end_week }}周</div>
                  </div>
                </td>
              </template>
            </tr>
          </tbody>
        </table>
        <el-empty v-if="!loading && myCourses.length === 0" description="本学期暂无课程" />
      </div>
    </template>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { onBeforeRouteUpdate } from 'vue-router'
import { ElMessage } from 'element-plus'
import request from '@/utils/request'
import { REFRESH_TTL } from '@/config/refresh-policy'
import { useStaleRefresh } from '@/composables/useStaleRefresh'
import { buildScheduleGrid } from '@/utils/schedule-grid'

const weekdayNames = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
const periodTimes = [
  '08:30-09:10', '09:20-10:00', '10:20-11:00', '11:10-11:50',
  '14:30-15:10', '15:20-16:00', '16:10-16:50', '17:00-17:40',
  '19:00-19:40', '19:50-20:30', '20:40-21:20',
]
const myCourses = ref([])
const scheduleRef = ref(null)
const semester = ref('')
const totalWeeks = ref(20)
const loading = ref(false)
const error = ref(null)

const totalCredits = computed(() => myCourses.value.reduce(
  (sum, course) => sum + (Number.parseFloat(course.credit) || 0), 0,
))
const scheduleGrid = computed(() => buildScheduleGrid(myCourses.value))

async function fetchSchedule(sequence) {
  loading.value = true
  error.value = null
  try {
    const response = await request.get('/student/my-courses')
    if (sequence) {
      myCourses.value = response.data?.items || []
      semester.value = response.data?.semester || ''
      totalWeeks.value = response.data?.total_weeks || 20
    }
  } catch (cause) {
    error.value = {
      message: cause.apiError?.message || '无法获取课表，请稍后重试',
      requestId: cause.apiError?.request_id || '',
    }
    throw cause
  } finally {
    loading.value = false
  }
}

const { loadData } = useStaleRefresh(fetchSchedule, REFRESH_TTL.schedule, 'schedule')
onMounted(() => loadData({ force: true }).catch(() => {}))
onBeforeRouteUpdate(() => loadData({ force: true }).catch(() => {}))

function blockStyle(course) {
  const palette = ['#dbeafe', '#dcfce7', '#fef3c7', '#fce7f3', '#e0e7ff']
  return { background: palette[(course.plan_id || 0) % palette.length] }
}

async function exportExcel() {
  try {
    const response = await request.post(
      '/stats/export',
      { type: 'schedule', semester: semester.value },
      { responseType: 'blob' },
    )
    const url = URL.createObjectURL(response.data)
    const anchor = document.createElement('a')
    anchor.href = url
    anchor.download = `个人课表-${semester.value}.xlsx`
    anchor.click()
    URL.revokeObjectURL(url)
  } catch (cause) {
    error.value = {
      message: cause.apiError?.message || '课表导出失败',
      requestId: cause.apiError?.request_id || '',
    }
  }
}

function printSchedule() {
  const popup = window.open('', '_blank')
  if (!popup) {
    ElMessage.warning('浏览器阻止了打印窗口，请允许弹窗后重试')
    return
  }
  popup.opener = null
  const title = popup.document.createElement('h2')
  title.textContent = `个人课表 - ${semester.value}`
  const style = popup.document.createElement('style')
  style.textContent = 'body{font-family:Microsoft YaHei,sans-serif}table{width:100%;border-collapse:collapse}th,td{border:1px solid #333;padding:6px;text-align:center;vertical-align:middle}.course-block{padding:4px;margin:2px}@page{size:landscape;margin:10mm}'
  popup.document.head.appendChild(style)
  popup.document.body.appendChild(title)
  popup.document.body.appendChild(scheduleRef.value.querySelector('table').cloneNode(true))
  popup.document.close()
  popup.focus()
  setTimeout(() => popup.print(), 200)
}
</script>

<style scoped>
.actions { display: flex; gap: var(--space-2); }
.state-panel { margin-bottom: var(--space-4); }
.schedule-tags { display: flex; gap: var(--space-3); margin-bottom: var(--space-4); flex-wrap: wrap; }
.schedule-wrapper { overflow-x: auto; min-height: 240px; }
.schedule-table { width: 100%; border-collapse: collapse; min-width: 900px; }
.schedule-table th, .schedule-table td { border: 1px solid var(--neutral-200); text-align: center; vertical-align: middle; }
.schedule-table thead th { background: var(--neutral-50); padding: var(--space-2); color: var(--neutral-600); }
.time-col { width: 100px; }
.time-cell { padding: 4px; font-size: var(--text-scale-sm); background: var(--neutral-50); }
.period-num { font-weight: var(--weight-medium); color: var(--neutral-700); }
.period-time { color: var(--neutral-400); font-size: var(--text-scale-2xs); }
.slot-cell { width: calc((100% - 100px) / 7); height: 48px; padding: 1px; }
.course-block { border-left: 3px solid #3b82f6; border-radius: 3px; padding: 4px; margin: 2px; }
.cb-name { font-size: var(--text-scale-xs); font-weight: var(--weight-medium); color: var(--neutral-700); }
.cb-loc, .cb-weeks { font-size: var(--text-scale-2xs); color: var(--neutral-500); }
</style>
