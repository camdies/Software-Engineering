<template>
  <div class="page-card">
    <div class="page-header">
      <h1>统计分析</h1>
      <div class="search-group">
        <el-select v-model="selectedPlan" placeholder="选择课程" @change="fetchData">
          <el-option v-for="p in plans" :key="p.plan_id" :label="`${p.course_id} - ${p.course_name} (${p.semester})`" :value="p.plan_id" />
        </el-select>
        <el-button type="success" :disabled="!selectedPlan" @click="exportExcel" plain>导出 Excel</el-button>
      </div>
    </div>

    <div v-if="stats.rank_list?.length">
      <div class="stat-cards">
        <div class="stat-card">
          <div class="stat-value">{{ stats.avg_score ?? '--' }}</div>
          <div class="stat-label">平均分</div>
        </div>
        <div class="stat-card success">
          <div class="stat-value">{{ stats.max_score ?? '--' }}</div>
          <div class="stat-label">最高分</div>
        </div>
        <div class="stat-card warning">
          <div class="stat-value">{{ stats.min_score ?? '--' }}</div>
          <div class="stat-label">最低分</div>
        </div>
        <div class="stat-card" :class="passRateClass">
          <div class="stat-value">{{ passRateStr }}</div>
          <div class="stat-label">及格率</div>
        </div>
      </div>

      <div class="charts-row">
        <div class="chart-card">
          <h3 class="chart-title">成绩分布</h3>
          <v-chart :option="distPieOpt" :autoresize="true" style="height:320px" class="chart-instance" />
        </div>
        <div class="chart-card">
          <h3 class="chart-title">成绩排名 (Top 10)</h3>
          <v-chart :option="rankBarOpt" :autoresize="true" style="height:320px" class="chart-instance" />
        </div>
      </div>

      <h4 style="margin:var(--space-6) 0 var(--space-3)">全部排名</h4>
      <el-table :data="stats.rank_list" stripe size="small" max-height="400">
        <el-table-column type="index" label="排名" width="60" />
        <el-table-column prop="student_id" label="学号" width="130" />
        <el-table-column prop="name" label="姓名" width="100" />
        <el-table-column label="成绩" width="90">
          <template #default="{ row }">
            <el-tag :type="scoreTagType(row.score)" effect="dark" size="small">{{ row.score }}</el-tag>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <div v-else class="empty-state">
      <div class="empty-icon">&#128200;</div>
      <div class="empty-title">选择课程查看统计</div>
      <div class="empty-desc">选择一门课程后将展示成绩分布图、排名柱状图及详细排名表</div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import request from '@/utils/request'
import { chartBaseOpts, GRADE_BAND_COLORS, GRADE_BAND_LABELS } from '@/utils/chart-setup'

const plans = ref([]), selectedPlan = ref(null)
const stats = ref({ avg_score: 0, max_score: 0, min_score: 0, pass_rate: 0, rank_list: [] })
const dist = ref({ total: 0, excellent: {}, good: {}, medium: {}, fail: {} })

onMounted(async () => {
  const res = await request.get('/teacher/plans')
  plans.value = res.data?.items || []
})

async function fetchData() {
  if (!selectedPlan.value) return
  const [sRes, dRes] = await Promise.all([
    request.get(`/stats/class/${selectedPlan.value}`),
    request.get(`/stats/distribution/${selectedPlan.value}`),
  ])
  stats.value = sRes.data || stats.value
  dist.value = dRes.data || dist.value
}

const passRateStr = computed(() => {
  const r = stats.value.pass_rate
  return r != null ? `${(r * 100).toFixed(1)}%` : '--'
})
const passRateClass = computed(() => {
  const r = stats.value.pass_rate
  if (r == null) return ''
  if (r >= 0.9) return 'success'
  if (r >= 0.7) return 'warning'
  return 'danger'
})

function scoreTagType(s) {
  if (s >= 90) return 'success'
  if (s >= 60) return ''
  return 'danger'
}

const distPieOpt = computed(() => ({
  ...chartBaseOpts({ grid: null }),
  legend: {
    orient: 'vertical',
    right: 12,
    top: 'center',
    textStyle: { color: '#6b7280', fontSize: 11, fontFamily: "var(--font-body)" },
    itemGap: 14,
  },
  series: [{
    type: 'pie',
    radius: ['55%', '80%'],
    center: ['38%', '50%'],
    avoidLabelOverlap: false,
    itemStyle: { borderRadius: 4, borderColor: '#fff', borderWidth: 2 },
    label: { show: false },
    emphasis: {
      label: { show: true, fontSize: 14, fontWeight: 'bold' },
      scaleSize: 8,
    },
    data: [
      { value: dist.value.excellent?.count || 0, name: GRADE_BAND_LABELS[0], itemStyle: { color: GRADE_BAND_COLORS[0] } },
      { value: dist.value.good?.count || 0, name: GRADE_BAND_LABELS[1], itemStyle: { color: GRADE_BAND_COLORS[1] } },
      { value: dist.value.medium?.count || 0, name: GRADE_BAND_LABELS[2], itemStyle: { color: GRADE_BAND_COLORS[2] } },
      { value: dist.value.fail?.count || 0, name: GRADE_BAND_LABELS[3], itemStyle: { color: GRADE_BAND_COLORS[3] } },
    ].filter(d => d.value > 0),
  }],
  tooltip: {
    ...chartBaseOpts().tooltip,
    formatter: '{b}: {c} 人 ({d}%)',
  },
}))

const rankBarOpt = computed(() => {
  const top10 = (stats.value.rank_list || []).slice(0, 10)
  const names = top10.map(r => r.name)
  const scores = top10.map(r => r.score)
  return {
    ...chartBaseOpts(),
    xAxis: {
      type: 'value',
      max: 100,
      axisLabel: { color: '#6b7280', fontSize: 11 },
      splitLine: { lineStyle: { color: '#f1f3f6', type: 'dashed' } },
    },
    yAxis: {
      type: 'category',
      data: names.reverse(),
      axisLine: { lineStyle: { color: '#cdd2d9' } },
      axisTick: { show: false },
      axisLabel: { color: '#6b7280', fontSize: 11 },
      inverse: true,
    },
    series: [{
      type: 'bar',
      data: scores.reverse().map(v => ({
        value: v,
        itemStyle: {
          borderRadius: [0, 4, 4, 0],
          color: v >= 90 ? GRADE_BAND_COLORS[0]
                : v >= 75 ? GRADE_BAND_COLORS[1]
                : v >= 60 ? GRADE_BAND_COLORS[2]
                : GRADE_BAND_COLORS[3],
        },
      })),
      barWidth: 16,
      label: { show: true, position: 'right', color: '#4b5563', fontSize: 11 },
    }],
    grid: { top: 8, right: 38, bottom: 8, left: 8, containLabel: true },
    tooltip: {
      ...chartBaseOpts().tooltip,
      formatter: (p) => `<div style="font-weight:600;margin-bottom:4px">${p[0].name}</div>成绩 <b>${p[0].value}</b> 分`,
    },
  }
})

async function exportExcel() {
  const res = await request.post('/stats/export', { type: 'class', plan_id: selectedPlan.value }, { responseType: 'blob' })
  const url = URL.createObjectURL(res)
  const a = document.createElement('a')
  a.href = url; a.download = '成绩统计.xlsx'; a.click()
  URL.revokeObjectURL(url)
}
</script>

<style scoped>
.charts-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-5);
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
