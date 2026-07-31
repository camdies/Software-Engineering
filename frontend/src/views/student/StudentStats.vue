<template>
  <div>
    <div class="stat-cards">
      <div class="stat-card">
        <div class="stat-value">{{ stats.total_credits ?? 0 }}</div>
        <div class="stat-label">已修学分</div>
      </div>
      <div class="stat-card success">
        <div class="stat-value">{{ stats.cumulative_gpa ?? '0.00' }}</div>
        <div class="stat-label">累计 GPA</div>
      </div>
      <div class="stat-card" :class="{ danger: (stats.failed_courses?.length || 0) > 0 }">
        <div class="stat-value">{{ stats.failed_courses?.length ?? 0 }}</div>
        <div class="stat-label">未通过课程</div>
      </div>
    </div>

    <div class="charts-row" v-if="trend.semesters?.length">
      <div class="chart-card">
        <h3 class="chart-title">GPA 学期趋势</h3>
        <v-chart :option="gpaTrendOpt" :autoresize="true" style="height:300px" class="chart-instance" />
      </div>
      <div class="chart-card">
        <h3 class="chart-title">学分修读</h3>
        <v-chart :option="creditBarOpt" :autoresize="true" style="height:300px" class="chart-instance" />
      </div>
    </div>

    <div class="page-card" v-if="stats.failed_courses?.length">
      <h4 style="margin:0 0 var(--space-3)">未通过课程详情</h4>
      <el-table :data="stats.failed_courses" stripe size="small">
        <el-table-column prop="course_name" label="课程名称" min-width="180" />
        <el-table-column label="成绩" width="80">
          <template #default="{ row }"><el-tag type="danger" size="small">{{ row.score }}</el-tag></template>
        </el-table-column>
        <el-table-column prop="semester" label="学期" width="120" />
      </el-table>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import request from '@/utils/request'
import { chartBaseOpts, CHART_COLORS } from '@/utils/chart-setup'

const stats = ref({ total_credits: 0, cumulative_gpa: 0, failed_courses: [] })
const trend = ref({ semesters: [], overall_gpa: 0 })

onMounted(async () => {
  const [sRes, tRes] = await Promise.all([
    request.get('/student/stats'),
    request.get('/stats/gpa-trend'),
  ])
  stats.value = sRes.data || stats.value
  trend.value = tRes.data || trend.value
})

const gpaTrendOpt = computed(() => ({
  ...chartBaseOpts(),
  xAxis: {
    type: 'category',
    data: trend.value.semesters.map(s => s.semester),
    axisLine: { lineStyle: { color: '#cdd2d9' } },
    axisTick: { show: false },
    axisLabel: { color: '#6b7280', fontSize: 11 },
  },
  yAxis: {
    type: 'value',
    min: 0,
    max: 4,
    interval: 1,
    axisLabel: { color: '#6b7280', fontSize: 11 },
    splitLine: { lineStyle: { color: '#f1f3f6', type: 'dashed' } },
  },
  series: [{
    type: 'line',
    data: trend.value.semesters.map(s => s.gpa),
    smooth: 0.4,
    symbol: 'circle',
    symbolSize: 9,
    lineStyle: { width: 3, color: CHART_COLORS.primary, shadowBlur: 8, shadowColor: 'rgba(99,102,241,0.35)' },
    itemStyle: { color: CHART_COLORS.primary, borderColor: '#fff', borderWidth: 2 },
    areaStyle: {
      color: {
        type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
        colorStops: [
          { offset: 0, color: 'rgba(99,102,241,0.18)' },
          { offset: 1, color: 'rgba(99,102,241,0.01)' },
        ],
      },
    },
    label: { show: true, color: '#4b5563', fontSize: 11, formatter: '{c}' },
  }],
  tooltip: {
    ...chartBaseOpts().tooltip,
    formatter: (p) => {
      const d = p[0]
      return `${d.name}\nGPA ${d.value}`
    },
  },
}))

const creditBarOpt = computed(() => ({
  ...chartBaseOpts(),
  xAxis: {
    type: 'category',
    data: trend.value.semesters.map(s => s.semester),
    axisLine: { lineStyle: { color: '#cdd2d9' } },
    axisTick: { show: false },
    axisLabel: { color: '#6b7280', fontSize: 11 },
  },
  yAxis: {
    type: 'value',
    axisLabel: { color: '#6b7280', fontSize: 11 },
    splitLine: { lineStyle: { color: '#f1f3f6', type: 'dashed' } },
  },
  series: [
    {
      type: 'bar',
      name: '学分',
      data: trend.value.semesters.map(s => s.credits),
      barWidth: 28,
      itemStyle: {
        borderRadius: [6, 6, 0, 0],
        color: {
          type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
          colorStops: [
            { offset: 0, color: CHART_COLORS.mint },
            { offset: 1, color: CHART_COLORS.emerald },
          ],
        },
      },
      label: { show: true, position: 'top', color: '#4b5563', fontSize: 11 },
    },
  ],
  tooltip: {
    ...chartBaseOpts().tooltip,
    formatter: (p) => {
      const d = p[0]
      return `${d.name}\n修读 ${d.value} 学分`
    },
  },
}))
</script>

<style scoped>
.charts-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-5);
  margin-top: var(--space-5);
}
.chart-card {
  background: var(--surface-card);
  border-radius: var(--radius-lg);
  padding: var(--space-5);
  border: var(--border-light);
  box-shadow: var(--shadow-xs);
}
.chart-title {
  font-family: var(--font-display);
  font-size: var(--text-scale-base);
  font-weight: var(--weight-semibold);
  color: var(--neutral-700);
  margin: 0 0 var(--space-4);
}
.chart-instance { width: 100%; }

@media (max-width: 768px) {
  .charts-row { grid-template-columns: 1fr; }
}
</style>
