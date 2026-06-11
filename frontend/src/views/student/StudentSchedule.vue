<template>
  <div class="page-card">
    <div class="page-toolbar">
      <h3 style="margin:0">个人课表</h3>
      <div>
        <el-button @click="exportExcel">导出 Excel</el-button>
        <el-button type="primary" @click="exportPDF">导出 PDF</el-button>
      </div>
    </div>

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
                :style="blockStyle(c, d, p)">
                <div class="cb-name">{{ c.course_name }}</div>
                <div class="cb-loc">{{ c.location || '' }}</div>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import request from '@/utils/request'

const weekdayNames = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
const periodTimes = [
  '08:30-09:10', '09:20-10:00', '10:20-11:00', '11:10-11:50',
  '14:30-15:10', '15:20-16:00', '16:10-16:50', '17:00-17:40',
  '19:00-19:40', '19:50-20:30', '20:40-21:20',
]

const myCourses = ref([])
const scheduleRef = ref(null)

onMounted(async () => {
  const res = await request.get('/student/my-courses')
  myCourses.value = res.data?.items || []
})

function getCoursesAt(day, period) {
  return myCourses.value.filter(c =>
    c.weekday === day &&
    c.period_start <= period &&
    c.period_start + c.period_count - 1 >= period &&
    period === c.period_start  // only render at the starting cell
  )
}

function blockStyle(course, day, period) {
  const rowSpan = (course.period_count || 2) * 48  // each period ~48px
  return {
    height: `${rowSpan}px`,
    background: `hsl(${(parseInt(course.course_id?.replace(/\D/g, '') || '0') % 360)}, 70%, 85%)`,
  }
}

function exportExcel() {
  // Build a simple CSV-like schedule
  let html = '<html><head><meta charset="utf-8"><title>个人课表</title></head><body>'
  html += '<h2>个人课表</h2><table border="1" cellpadding="4" cellspacing="0">'
  html += '<tr><th>节次</th>' + weekdayNames.map(w => `<th>${w}</th>`).join('') + '</tr>'
  for (let p = 1; p <= 11; p++) {
    html += `<tr><td>第${p}节<br/>${periodTimes[p - 1]}</td>`
    for (let d = 1; d <= 7; d++) {
      const c = myCourses.value.find(c => c.weekday === d && c.period_start === p)
      html += `<td>${c ? `${c.course_name}\n${c.location || ''}\n${c.time_slot}` : ''}</td>`
    }
    html += '</tr>'
  }
  html += '</table></body></html>'
  const blob = new Blob([html], { type: 'application/vnd.ms-excel' })
  const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = '个人课表.xls'; a.click()
}

function exportPDF() {
  // Use browser print for PDF export
  const w = window.open('', '_blank')
  w.document.write(`
    <html><head><meta charset="utf-8"><title>个人课表</title>
    <style>
      body { font-family: 'Microsoft YaHei', sans-serif; }
      h2 { text-align: center; }
      table { width: 100%; border-collapse: collapse; }
      th, td { border: 1px solid #333; padding: 8px; text-align: center; font-size: 12px; }
      th { background: #f0f0f0; }
      .has-course { background: #d4e6ff; }
    </style></head><body>`)
  w.document.write('<h2>个人课表</h2><table>')
  w.document.write(`<tr><th>节次</th>${weekdayNames.map(n => `<th>${n}</th>`).join('')}</tr>`)
  for (let p = 1; p <= 11; p++) {
    w.document.write(`<tr><td>第${p}节<br/><small>${periodTimes[p - 1]}</small></td>`)
    for (let d = 1; d <= 7; d++) {
      const c = myCourses.value.find(c => c.weekday === d && c.period_start === p)
      w.document.write(`<td class="${c ? 'has-course' : ''}">${c ? `${c.course_name}<br/>${c.location || ''}` : ''}</td>`)
    }
    w.document.write('</tr>')
  }
  w.document.write('</table></body></html>')
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
  border-radius: 3px; padding: 4px; margin: 1px;
  display: flex; flex-direction: column; justify-content: center;
  z-index: 2; overflow: hidden;
}
.cb-name { font-size: 12px; font-weight: 500; color: #303133; line-height: 1.3; }
.cb-loc { font-size: 11px; color: #606266; }
</style>
