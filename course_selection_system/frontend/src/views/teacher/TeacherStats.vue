<template>
  <div class="page-card">
    <div class="page-toolbar">
      <h3 style="margin:0">统计分析</h3>
      <div class="search-group">
        <el-select v-model="selectedPlan" placeholder="选择课程" style="width:280px" @change="fetchData">
          <el-option v-for="p in plans" :key="p.plan_id" :label="`${p.course_id} - ${p.semester}`" :value="p.plan_id" />
        </el-select>
        <el-button type="success" :disabled="!selectedPlan" @click="exportExcel">导出 Excel</el-button>
      </div>
    </div>

    <div v-if="stats.rank_list?.length">
      <div class="stat-cards">
        <div class="stat-card"><div class="stat-value">{{ stats.avg_score }}</div><div class="stat-label">平均分</div></div>
        <div class="stat-card success"><div class="stat-value">{{ stats.max_score }}</div><div class="stat-label">最高分</div></div>
        <div class="stat-card warning"><div class="stat-value">{{ stats.min_score }}</div><div class="stat-label">最低分</div></div>
        <div class="stat-card"><div class="stat-value">{{ (stats.pass_rate * 100).toFixed(1) }}%</div><div class="stat-label">及格率</div></div>
      </div>

      <h4 style="margin:16px 0 8px">成绩排名</h4>
      <el-table :data="stats.rank_list" stripe size="small" max-height="400">
        <el-table-column type="index" label="排名" width="60" />
        <el-table-column prop="student_id" label="学号" width="130" />
        <el-table-column prop="name" label="姓名" width="100" />
        <el-table-column label="成绩" width="90">
          <template #default="{ row }">
            <el-tag :type="row.score >= 90 ? 'success' : row.score >= 60 ? '' : 'danger'" effect="dark">{{ row.score }}</el-tag>
          </template>
        </el-table-column>
      </el-table>

      <h4 style="margin:16px 0 8px">成绩分布</h4>
      <el-table :data="distData" stripe size="small">
        <el-table-column prop="label" label="分数段" width="120" />
        <el-table-column prop="count" label="人数" width="80" />
        <el-table-column prop="ratio" label="占比" width="80">
          <template #default="{ row }">{{ (row.ratio * 100).toFixed(1) }}%</template>
        </el-table-column>
      </el-table>
    </div>

    <el-empty v-else description="请选择课程查看统计" />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import request from '@/utils/request'

const plans = ref([])
const selectedPlan = ref(null)
const stats = ref({ avg_score: 0, max_score: 0, min_score: 0, pass_rate: 0, rank_list: [] })
const dist = ref({})

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

const distData = computed(() => [
  { label: '优秀 (90-100)', count: dist.value.excellent?.count ?? 0, ratio: dist.value.excellent?.ratio ?? 0 },
  { label: '良好 (75-89)', count: dist.value.good?.count ?? 0, ratio: dist.value.good?.ratio ?? 0 },
  { label: '中等 (60-74)', count: dist.value.medium?.count ?? 0, ratio: dist.value.medium?.ratio ?? 0 },
  { label: '不及格 (0-59)', count: dist.value.fail?.count ?? 0, ratio: dist.value.fail?.ratio ?? 0 },
])

async function exportExcel() {
  const res = await request.post('/stats/export', {
    type: 'class',
    plan_id: selectedPlan.value,
  }, { responseType: 'blob' })
  const url = URL.createObjectURL(res)
  const a = document.createElement('a')
  a.href = url; a.download = '成绩统计.xlsx'; a.click()
  URL.revokeObjectURL(url)
}
</script>
