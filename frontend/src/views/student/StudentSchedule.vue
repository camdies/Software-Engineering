<template>
  <div class="page-card">
    <div class="page-toolbar">
      <h3 style="margin:0">个人课表查询</h3>
      <div style="display:flex;gap:8px">
        <el-button @click="exportExcel" icon="Download">导出 Excel</el-button>
        <el-button type="primary" @click="exportPDF" icon="Printer">导出 PDF</el-button>
      </div>
    </div>

    <!-- 学期和统计信息 -->
    <div style="display:flex;gap:16px;margin-bottom:16px;flex-wrap:wrap">
      <el-tag size="large" type="info">学期: {{ semester }}</el-tag>
      <el-tag size="large" type="success">总周数: {{ totalWeeks }}周</el-tag>
      <el-tag size="large" type="warning">已选课程: {{ myCourses.length }}门</el-tag>
      <el-tag size="large">总学分: {{ totalCredits.toFixed(1) }}</el-tag>
    </div>

    <!-- 周课表表格 -->
    <div class="schedule-wrapper" ref="scheduleRef">
      <table class="schedule-table">
        <thead>
          <tr>
            <th class="time-col">节次/时间</th>
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

    <!-- 课程详情列表（表格形式） -->
    <h4 style="margin:20px 0 12px">已选课程详情</h4>
    <el-table :data="myCourses" stripe border size="small" style="width:100%">
      <el-table-column prop="course_id" label="课程代码" width="100" />
      <el-table-column prop="course_name" label="课程名称" min-width="150" />
      <el-table-column label="上课时间" width="200">
        <template #default="{ row }">{{ row.time_slot }}</template>
      </el-table-column>
      <el-table-column label="教学周" width="120">
        <template #default="{ row }">{{ row.start_week || 1 }}-{{ row.end_week || 20 }}周</template>
      </el-table-column>
      <el-table-column prop="location" label="地点" width="120" />
      <el-table-column prop="credit" label="学分" width="70" />
      <el-table-column prop="exam_type" label="考核" width="70" />
      <el-table-column prop="semester" label="学期" width="120" />
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

const myCourses = ref([])
const scheduleRef = ref(null)
const semester = ref('')
const totalWeeks = ref(20)

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
    c.weekday === day &&
    c.period_start <= period &&
    c.period_start + c.period_count - 1 >= period &&
    period === c.period_start
  )
}

function blockStyle(course) {
  const h = (course.period_count || 2) * 48
  return {
    height: `${h}px`,
    background: `hsl(${(parseInt(course.course_id?.replace(/\D/g, '') || '0') % 360)}, 70%, 85%)`,
  }
}

async function exportExcel() {
  try {
    const res = await request.post('/stats/export', {
      type: 'schedule',
      student_id: '',
    }, { responseType: 'blob' })
    const url = URL.createObjectURL(res)
    const a = document.createElement('a')
    a.href = url
    a.download = '个人课表.xlsx'
    a.click()
    URL.revokeObjectURL(url)
  } catch {
    // Fallback: build HTML table
    let html = '<html><head><meta charset="utf-8"><title>个人课表</title></head><body>'
    html += '<h2>个人课表</h2><table border="1" cellpadding="4" cellspacing="0">'
    html += '<tr><th>节次/时间</th>' + weekdayNames.map(w => `<th>${w}</th>`).join('') + '</tr>'
    for (let p = 1; p <= 11; p++) {
      html += `<tr><td>第${p}节<br/>${periodTimes[p - 1]}</td>`
      for (let d = 1; d <= 7; d++) {
        const courses = getCoursesAt(d, p)
        html += `<td>${courses.map(c => `${c.course_name}<br/>${c.location || ''}<br/>${c.start_week}-${c.end_week}周`).join('<br/>') || ''}</td>`
      }
      html += '</tr>'
    }
    html += '</table></body></html>'
    const blob = new Blob([html], { type: 'application/vnd.ms-excel' })
    const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = '个人课表.xls'; a.click()
  }
}

function exportPDF() {
  const w = window.open('', '_blank')
  w.document.write(`
    <html><head><meta charset="utf-8"><title>个人课表</title>
    <style>
      @media print { @page { size: landscape; margin: 10mm; } }
      body { font-family: 'Microsoft YaHei', sans-serif; }
      h2 { text-align: center; margin-bottom: 8px; }
      .info { text-align: center; color: #666; font-size: 13px; margin-bottom: 16px; }
      table { width: 100%; border-collapse: collapse; font-size: 11px; }
      th, td { border: 1px solid #333; padding: 6px; text-align: center; vertical-align: top; }
      th { background: #e8e8e8; font-weight: 600; }
      .time-col { width: 80px; }
      .has-course { background: #d4e6ff; font-weight: 500; }
    </style></head><body>`)
  w.document.write(`<h2>个人课表</h2>`)
  w.document.write(`<div class="info">学期: ${semester.value} | 总课程: ${myCourses.value.length}门 | 总学分: ${totalCredits.value.toFixed(1)}</div>`)
  w.document.write('<table>')
  w.document.write(`<tr><th class="time-col">节次/时间</th>${weekdayNames.map(n => `<th>${n}</th>`).join('')}</tr>`)
  for (let p = 1; p <= 11; p++) {
    w.document.write(`<tr><td class="time-col">第${p}节<br/><small>${periodTimes[p - 1]}</small></td>`)
    for (let d = 1; d <= 7; d++) {
      const courses = getCoursesAt(d, p)
      const cells = courses.map(c => `${c.course_name}<br/>${c.location || ''}`).join('<br/>') || ''
      w.document.write(`<td class="${courses.length > 0 ? 'has-course' : ''}">${cells}</td>`)
    }
    w.document.write('</tr>')
  }
  w.document.write('</table>')
  w.document.write('</body></html>')
  w.document.close()
  setTimeout(() => w.print(), 500)
}
</script>

<style scoped>
.schedule-wrapper { overflow-x: auto; }
.schedule-table { width: 100%; border-collapse: collapse; min-width: 900px; }
.schedule-table th, .schedule-table td {
  border: 1px solid #e4e7ed; text-align: center; vertical-align: top;
}
.schedule-table th { background: #f5f7fa; padding: 8px; font-weight: 500; color: #606266; }
.time-col { width: 100px; }
.time-cell { padding: 4px; font-size: 12px; }
.period-num { font-weight: 500; color: #303133; }
.period-time { color: #909399; font-size: 11px; }
.slot-cell { width: calc((100% - 100px) / 7); height: 48px; position: relative; padding: 0; }
.course-block {
  position: absolute; top: 0; left: 0; right: 0;
  border-radius: 3px; padding: 3px; margin: 1px;
  display: flex; flex-direction: column; justify-content: center;
  z-index: 2; overflow: hidden;
}
.cb-name { font-size: 12px; font-weight: 500; color: #303133; line-height: 1.3; }
.cb-loc { font-size: 10px; color: #606266; }
.cb-weeks { font-size: 9px; color: #909399; }
</style>
