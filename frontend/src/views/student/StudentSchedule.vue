<template>
  <div class="page-card">
    <div class="page-header">
      <h1>个人课表</h1>
      <div style="display:flex;gap:var(--space-2)">
        <el-button @click="exportExcel">导出 Excel</el-button>
        <el-button type="primary" @click="exportPDF">导出 PDF</el-button>
      </div>
    </div>

    <div class="schedule-tags">
      <el-tag size="large" type="info">学期: {{ semester }}</el-tag>
      <el-tag size="large" type="success">总周数: {{ totalWeeks }}周</el-tag>
      <el-tag size="large" type="warning">已选: {{ myCourses.length }}门</el-tag>
      <el-tag size="large">学分: {{ totalCredits.toFixed(1) }}</el-tag>
    </div>

    <div class="schedule-wrapper" ref="scheduleRef">
      <table class="schedule-table">
        <thead>
          <tr>
            <th class="time-col">节次 / 时间</th>
            <th v-for="(name, idx) in weekdayNames" :key="idx" class="day-col">{{ name }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="p in 11" :key="p">
            <td class="time-cell">
              <div class="period-num">第{{ p }}节</div>
              <div class="period-time">{{ periodTimes[p - 1] }}</div>
            </td>
            <td v-for="d in 7" :key="d" class="slot-cell">
              <div v-for="c in getCoursesAt(d, p)" :key="c.plan_id"
                class="course-block"
                :style="blockStyle(c)">
                <div class="cb-name">{{ c.course_name }}</div>
                <div class="cb-loc">{{ c.location || '' }}</div>
                <div class="cb-weeks">{{ c.start_week }}-{{ c.end_week }}周</div>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <h4 style="margin:var(--space-6) 0 var(--space-3)">已选课程详情</h4>
    <el-table :data="myCourses" stripe border size="small">
      <el-table-column prop="course_id" label="课程代码" width="110" />
      <el-table-column prop="course_name" label="课程名称" min-width="160" />
      <el-table-column label="上课时间" min-width="220">
        <template #default="{ row }">{{ row.time_slot }}</template>
      </el-table-column>
      <el-table-column label="教学周" width="130">
        <template #default="{ row }">{{ row.start_week || 1 }}-{{ row.end_week || 20 }}周</template>
      </el-table-column>
      <el-table-column prop="location" label="地点" width="130" />
      <el-table-column prop="credit" label="学分" width="70" />
      <el-table-column prop="exam_type" label="考核" width="70" />
      <el-table-column prop="semester" label="学期" width="130" />
    </el-table>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import request from '@/utils/request'

const weekdayNames = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
const periodTimes = [
  '08:30-09:10', '09:20-10:00', '10:20-11:00', '11:10-11:50',
  '14:30-15:10', '15:20-16:00', '16:10-16:50', '17:00-17:40',
  '19:00-19:40', '19:50-20:30', '20:40-21:20',
]

const myCourses = ref([]), scheduleRef = ref(null), semester = ref(''), totalWeeks = ref(20)

const totalCredits = computed(() => {
  return myCourses.value.reduce((sum, c) => sum + (parseFloat(c.credit) || 0), 0)
})

onMounted(async () => {
  const res = await request.get('/student/my-courses')
  myCourses.value = res.data?.items || []
  if (myCourses.value.length > 0) {
    semester.value = myCourses.value[0].semester || ''
  }
})

function getCoursesAt(day, period) {
  return myCourses.value.filter(c =>
    c.weekday === day && c.period_start <= period &&
    c.period_start + c.period_count - 1 >= period && period === c.period_start
  )
}

function buildScheduleGrid() {
  const grid = []
  for (let p = 0; p < 11; p++) {
    grid[p] = []
    for (let d = 0; d < 7; d++) {
      grid[p][d] = { courses: [], rowspan: 1, covered: false }
    }
  }

  for (const c of myCourses.value) {
    const startRow = c.period_start - 1
    const endRow = startRow + c.period_count - 1
    const col = c.weekday - 1

    grid[startRow][col].courses.push(c)
    grid[startRow][col].rowspan = c.period_count

    for (let r = startRow + 1; r <= endRow; r++) {
      grid[r][col].covered = true
    }
  }

  return grid
}

function blockStyle(course) {
  const h = (course.period_count || 2) * 48
  const palette = [
    { bg: '#dbeafe', border: '#3b82f6' },
    { bg: '#dcfce7', border: '#22c55e' },
    { bg: '#fef3c7', border: '#f59e0b' },
    { bg: '#fce7f3', border: '#ec4899' },
    { bg: '#e0e7ff', border: '#6366f1' },
    { bg: '#ccfbf1', border: '#14b8a6' },
    { bg: '#fef2f2', border: '#ef4444' },
    { bg: '#f3e8ff', border: '#a855f7' },
    { bg: '#fff7ed', border: '#f97316' },
    { bg: '#ecfeff', border: '#06b6d4' },
  ]
  const idx = (course.plan_id || 0) % palette.length
  return { height: `${h}px`, background: palette[idx].bg, borderLeft: `3px solid ${palette[idx].border}` }
}

async function exportExcel() {
  try {
    const res = await request.post('/stats/export', { type: 'schedule', student_id: '' }, { responseType: 'blob' })
    const url = URL.createObjectURL(res.data)
    const a = document.createElement('a'); a.href = url; a.download = '个人课表.xlsx'; a.click()
    URL.revokeObjectURL(url)
  } catch {
    const t = [
      '08:30-09:10', '09:20-10:00', '10:20-11:00', '11:10-11:50',
      '14:30-15:10', '15:20-16:00', '16:10-16:50', '17:00-17:40',
      '19:00-19:40', '19:50-20:30', '20:40-21:20',
    ]
    const grid = buildScheduleGrid()
    let h = '<html><head><meta charset="utf-8"><title>个人课表</title></head><body>'
    h += '<h2>个人课表</h2><table border="1" cellpadding="4" cellspacing="0">'
    h += '<tr><th>节次/时间</th>' + weekdayNames.map(w => `<th>${w}</th>`).join('') + '</tr>'
    for (let p = 0; p < 11; p++) {
      h += `<tr><td>第${p + 1}节<br/>${t[p]}</td>`
      for (let d = 0; d < 7; d++) {
        const cell = grid[p][d]
        if (cell.covered) continue
        const cs = cell.courses
        const rowspan = cell.rowspan
        const rowspanAttr = rowspan > 1 ? ` rowspan="${rowspan}"` : ''
        h += `<td${rowspanAttr}>${cs.map(c => `${c.course_name}<br/>${c.location || ''}<br/>${c.start_week}-${c.end_week}周`).join('<br/>') || ''}</td>`
      }
      h += '</tr>'
    }
    h += '</table></body></html>'
    const blob = new Blob([h], { type: 'application/vnd.ms-excel' })
    const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = '个人课表.xls'; a.click()
  }
}

function exportPDF() {
  const t = [
    '08:30-09:10', '09:20-10:00', '10:20-11:00', '11:10-11:50',
    '14:30-15:10', '15:20-16:00', '16:10-16:50', '17:00-17:40',
    '19:00-19:40', '19:50-20:30', '20:40-21:20',
  ]
  const grid = buildScheduleGrid()
  const w = window.open('', '_blank')
  w.document.write(`
    <html><head><meta charset="utf-8"><title>个人课表</title>
    <style>
      @media print { @page { size: landscape; margin: 10mm; } }
      body { font-family: 'Microsoft YaHei', sans-serif; }
      h2 { text-align: center; margin-bottom: 8px; }
      .info { text-align: center; color: #666; font-size: 13px; margin-bottom: 16px; }
      table { width: 100%; border-collapse: collapse; font-size: 11px; }
      th, td { border: 1px solid #333; padding: 6px; text-align: center; vertical-align: middle; }
      th { background: #e8e8e8; font-weight: 600; }
      .time-col { width: 80px; }
      .has-course { background: #d4e6ff; font-weight: 500; }
    </style></head><body>`)
  w.document.write(`<h2>个人课表</h2>`)
  w.document.write(`<div class="info">学期: ${semester.value} | 总课程: ${myCourses.value.length}门 | 总学分: ${totalCredits.value.toFixed(1)}</div>`)
  w.document.write('<table>')
  w.document.write(`<tr><th class="time-col">节次/时间</th>${weekdayNames.map(n => `<th>${n}</th>`).join('')}</tr>`)
  for (let p = 0; p < 11; p++) {
    w.document.write(`<tr><td class="time-col">第${p + 1}节<br/><small>${t[p]}</small></td>`)
    for (let d = 0; d < 7; d++) {
      const cell = grid[p][d]
      if (cell.covered) continue
      const cs = cell.courses
      const rowspan = cell.rowspan
      const rowspanAttr = rowspan > 1 ? ` rowspan="${rowspan}"` : ''
      w.document.write(`<td${rowspanAttr} class="${cs.length > 0 ? 'has-course' : ''}">${cs.map(c => `${c.course_name}<br/>${c.location || ''}`).join('<br/>') || ''}</td>`)
    }
    w.document.write('</tr>')
  }
  w.document.write('</table></body></html>')
  w.document.close()
  setTimeout(() => w.print(), 500)
}
</script>

<style scoped>
.schedule-tags { display: flex; gap: var(--space-3); margin-bottom: var(--space-4); flex-wrap: wrap; }
.schedule-wrapper { overflow-x: auto; }
.schedule-table { width: 100%; border-collapse: collapse; min-width: 900px; }
.schedule-table th, .schedule-table td { border: 1px solid var(--neutral-200); text-align: center; vertical-align: top; }
.schedule-table th { background: var(--neutral-50); padding: var(--space-2); font-weight: var(--weight-semibold); color: var(--neutral-600); font-size: var(--text-scale-sm); }
.time-col { width: 100px; }
.time-cell { padding: 4px; font-size: var(--text-scale-sm); }
.period-num { font-weight: var(--weight-medium); color: var(--neutral-700); }
.period-time { color: var(--neutral-400); font-size: var(--text-scale-2xs); }
.slot-cell { width: calc((100% - 100px) / 7); height: 48px; position: relative; padding: 0; }
.course-block {
  position: absolute; top: 0; left: 0; right: 0;
  border-radius: 3px; padding: 3px; margin: 1px;
  display: flex; flex-direction: column; justify-content: center;
  z-index: 2; overflow: hidden;
}
.cb-name { font-size: var(--text-scale-xs); font-weight: var(--weight-medium); color: var(--neutral-700); line-height: 1.3; }
.cb-loc { font-size: var(--text-scale-2xs); color: var(--neutral-500); }
.cb-weeks { font-size: 9px; color: var(--neutral-400); }
</style>
