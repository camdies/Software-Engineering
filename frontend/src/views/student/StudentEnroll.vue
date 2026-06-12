<template>
  <el-container class="enroll-container">
    <!-- 主体区域 -->
    <el-main class="enroll-main">
      <!-- 顶部搜索栏 -->
      <div class="search-section">
        <div class="search-bar">
          <el-input v-model="search.keyword" placeholder="搜索课程名称、教师、院系..." clearable style="width: 360px"
            @input="onSearch" :prefix-icon="Search" />
          <el-button :icon="Filter" @click="showFilters = !showFilters">
            筛选
          </el-button>
          <el-select v-model="search.semester" placeholder="学期" clearable style="width: 160px" @change="fetchData">
            <el-option label="2026-2027-1" value="2026-2027-1" />
            <el-option label="2025-2026-2" value="2025-2026-2" />
            <el-option label="2025-2026-1" value="2025-2026-1" />
          </el-select>
        </div>

        <!-- 可折叠筛选面板 -->
        <el-collapse-transition>
          <div v-show="showFilters" class="filter-panel">
            <div class="filter-row">
              <span class="filter-label">院系</span>
              <el-select v-model="search.department" placeholder="全部" clearable style="width: 200px" @change="fetchData">
                <el-option v-for="d in departments" :key="d" :label="d" :value="d" />
              </el-select>
              <span class="filter-label">学分</span>
              <el-select v-model="search.creditRange" placeholder="全部" clearable style="width: 140px" @change="fetchData">
                <el-option label="0-2分" value="0-2" />
                <el-option label="2-4分" value="2-4" />
                <el-option label="4-6分" value="4-6" />
              </el-select>
              <span class="filter-label">时间</span>
              <el-select v-model="search.weekday" placeholder="全部" clearable style="width: 120px" @change="fetchData">
                <el-option v-for="(name, idx) in weekdayNames" :key="idx" :label="name" :value="idx + 1" />
              </el-select>
              <span class="filter-label">考核</span>
              <el-select v-model="search.examType" placeholder="全部" clearable style="width: 100px" @change="fetchData">
                <el-option label="考试" value="考试" />
                <el-option label="考查" value="考查" />
              </el-select>
              <span class="filter-label">类型</span>
              <el-select v-model="search.courseType" placeholder="全部" clearable style="width: 120px" @change="fetchData">
                <el-option label="必修" value="必修" />
                <el-option label="选修" value="选修" />
                <el-option label="公共必修" value="公共必修" />
                <el-option label="公共选修" value="公共选修" />
              </el-select>
            </div>
          </div>
        </el-collapse-transition>
      </div>

      <!-- 课程卡片列表 - 缩小页签形式 -->
      <div class="course-cards" v-loading="loading">
        <div v-for="course in filteredCourses" :key="course.plan_id"
          class="course-card"
          :class="{ 'is-enrolled': enrolledPlanIds.has(course.plan_id), 'is-expanded': expandedPlanId === course.plan_id }"
          @click="toggleExpand(course)">
          <div class="card-header">
            <h4 class="card-title">
              <el-link type="primary" :underline="false" @click.stop="openDetail(course)">
                {{ course.course_name }}
              </el-link>
            </h4>
            <div class="card-meta">
              <el-tag size="small" type="info">{{ course.course_id }}</el-tag>
              <span>{{ course.teacher_name || course.teacher_id }}</span>
              <span v-if="course.department">| {{ course.department }}</span>
              <el-tag v-if="course.course_type" size="small" :type="course.course_type === '必修' ? 'danger' : 'warning'">
                {{ course.course_type }}
              </el-tag>
            </div>
            <div class="card-badges">
              <el-tag v-if="enrolledPlanIds.has(course.plan_id)" type="success" effect="dark">已选</el-tag>
              <span class="expand-arrow">{{ expandedPlanId === course.plan_id ? '▲' : '▼' }}</span>
            </div>
          </div>

          <!-- 展开的详细信息（页签形式） -->
          <el-collapse-transition>
            <div v-show="expandedPlanId === course.plan_id" class="card-detail" @click.stop>
              <el-descriptions :column="2" border size="small">
                <el-descriptions-item label="课程代码">{{ course.course_id }}</el-descriptions-item>
                <el-descriptions-item label="学分">{{ course.credit }}</el-descriptions-item>
                <el-descriptions-item label="学时">{{ course.hours }}</el-descriptions-item>
                <el-descriptions-item label="考核方式">{{ course.exam_type || '--' }}</el-descriptions-item>
                <el-descriptions-item label="院系">{{ course.department || '--' }}</el-descriptions-item>
                <el-descriptions-item label="教师">{{ course.teacher_name || course.teacher_id }}</el-descriptions-item>
                <el-descriptions-item label="上课时间">{{ course.time_slot }}</el-descriptions-item>
                <el-descriptions-item label="地点">{{ course.location || '待定' }}</el-descriptions-item>
                <el-descriptions-item label="教学周">{{ course.start_week || 1 }}-{{ course.end_week || 20 }}周</el-descriptions-item>
                <el-descriptions-item label="容量">
                  {{ course.enrolled || 0 }}/{{ course.capacity }} (余{{ course.available }})
                </el-descriptions-item>
                <el-descriptions-item v-if="course.prerequisite" label="先修课程" :span="2">
                  {{ course.prerequisite }}
                </el-descriptions-item>
              </el-descriptions>

              <div v-if="course.description" style="margin-top:12px">
                <h5 style="margin:0 0 6px;color:#303133">课程简介</h5>
                <p style="color:#606266;line-height:1.8;white-space:pre-wrap;font-size:13px">{{ course.description }}</p>
              </div>
              <div v-if="course.syllabus" style="margin-top:8px">
                <h5 style="margin:0 0 6px;color:#303133">教学大纲</h5>
                <p style="color:#606266;line-height:1.8;white-space:pre-wrap;font-size:13px">{{ course.syllabus }}</p>
              </div>
              <div v-if="course.instructor_intro" style="margin-top:8px">
                <h5 style="margin:0 0 6px;color:#303133">教师简介</h5>
                <p style="color:#606266;line-height:1.8;white-space:pre-wrap;font-size:13px">{{ course.instructor_intro }}</p>
              </div>

              <!-- 选课/退课按钮在详情最右侧 -->
              <div style="display:flex;justify-content:flex-end;margin-top:16px">
                <el-button v-if="!enrolledPlanIds.has(course.plan_id)" type="primary"
                  :disabled="(course.available || 0) <= 0" :loading="enrollingPlanId === course.plan_id"
                  @click="doEnroll(course)">
                  选课
                </el-button>
                <el-button v-else type="danger" :loading="droppingPlanId === course.plan_id"
                  @click="doDrop(course)">
                  退课
                </el-button>
              </div>
            </div>
          </el-collapse-transition>
        </div>
        <el-empty v-if="!loading && filteredCourses.length === 0" description="暂无符合条件的课程" />
      </div>
    </el-main>

    <!-- 右侧已选课程侧边栏 -->
    <div class="course-sidebar" :class="{ expanded: sidebarExpanded }" @click="sidebarExpanded = true">
      <div class="sidebar-toggle">
        <el-icon :size="20"><List /></el-icon>
        <span v-if="sidebarExpanded" class="toggle-text">已选课程</span>
        <el-badge v-if="myCourses.length > 0" :value="myCourses.length" class="sidebar-badge" />
      </div>

      <div v-if="sidebarExpanded" class="sidebar-content" @click.stop>
        <!-- 周占用表（色块：绿/黄/红） -->
        <h5 style="margin:0 0 8px;display:flex;justify-content:space-between;align-items:center">
          学习周占用表
          <el-button link size="small" @click="sidebarExpanded = false">收起</el-button>
        </h5>
        <div class="week-heatmap">
          <div class="heatmap-header">
            <span class="hm-label">日期</span>
            <span v-for="p in 11" :key="p" class="hm-header-cell">{{ p }}</span>
          </div>
          <div v-for="d in 7" :key="d" class="heatmap-row">
            <span class="hm-label">{{ weekdayNames[d - 1] }}</span>
            <span v-for="p in 11" :key="p"
              class="hm-cell"
              :class="heatmapClass(d, p)"
              :title="heatmapTitle(d, p)">
              {{ heatmapText(d, p) }}
            </span>
          </div>
        </div>
        <div class="heatmap-legend">
          <span class="legend-item"><span class="legend-dot green"></span>空余周数 = 总周数</span>
          <span class="legend-item"><span class="legend-dot yellow"></span>空余周数 &ge; 总周数/2</span>
          <span class="legend-item"><span class="legend-dot red"></span>空余周数 &lt; 总周数/2</span>
        </div>

        <!-- 已选课程列表 -->
        <h5 style="margin:12px 0 8px">已选课程 ({{ myCourses.length }})</h5>
        <div class="sidebar-courses">
          <div v-for="c in myCourses" :key="c.plan_id" class="sidebar-course-item">
            <div class="sc-name">{{ c.course_name }}</div>
            <div class="sc-time">{{ c.time_slot }}</div>
            <div class="sc-weeks">第{{ c.start_week || 1 }}-{{ c.end_week || TOTAL_WEEKS }}周</div>
          </div>
        </div>
      </div>
    </div>
  </el-container>

  <!-- 课程详情弹窗（课程名点击触发） -->
  <el-dialog v-model="detailVisible" :title="detailCourse?.course_name" width="700px" top="5vh">
    <template v-if="detailCourse">
      <el-descriptions :column="2" border size="small">
        <el-descriptions-item label="课程代码">{{ detailCourse.course_id }}</el-descriptions-item>
        <el-descriptions-item label="学分">{{ detailCourse.credit }}</el-descriptions-item>
        <el-descriptions-item label="学时">{{ detailCourse.hours }}</el-descriptions-item>
        <el-descriptions-item label="考核方式">{{ detailCourse.exam_type || '--' }}</el-descriptions-item>
        <el-descriptions-item label="院系">{{ detailCourse.department || '--' }}</el-descriptions-item>
        <el-descriptions-item label="教师">{{ detailCourse.teacher_name || detailCourse.teacher_id }}</el-descriptions-item>
        <el-descriptions-item label="教材">{{ detailCourse.textbook || '待定' }}</el-descriptions-item>
        <el-descriptions-item label="课程类型">{{ detailCourse.course_type || '必修' }}</el-descriptions-item>
        <el-descriptions-item label="上课时间">{{ detailCourse.time_slot }}</el-descriptions-item>
        <el-descriptions-item label="地点">{{ detailCourse.location || '待定' }}</el-descriptions-item>
        <el-descriptions-item label="教学周">{{ detailCourse.start_week || 1 }}-{{ detailCourse.end_week || TOTAL_WEEKS }}周</el-descriptions-item>
        <el-descriptions-item label="容量">
          {{ detailCourse.enrolled || 0 }}/{{ detailCourse.capacity }} (余{{ detailCourse.available }})
        </el-descriptions-item>
      </el-descriptions>

      <div v-if="detailCourse.description" style="margin-top:16px">
        <h4 style="margin:0 0 8px">课程简介</h4>
        <p style="color:#606266;line-height:1.8;white-space:pre-wrap">{{ detailCourse.description }}</p>
      </div>
      <div v-if="detailCourse.syllabus" style="margin-top:12px">
        <h4 style="margin:0 0 8px">教学大纲</h4>
        <p style="color:#606266;line-height:1.8;white-space:pre-wrap">{{ detailCourse.syllabus }}</p>
      </div>
      <div v-if="detailCourse.instructor_intro" style="margin-top:12px">
        <h4 style="margin:0 0 8px">教师简介</h4>
        <p style="color:#606266;line-height:1.8;white-space:pre-wrap">{{ detailCourse.instructor_intro }}</p>
      </div>
    </template>

    <template #footer>
      <div style="display:flex;justify-content:flex-end;gap:12px">
        <el-button @click="detailVisible = false">关闭</el-button>
        <el-button v-if="!enrolledPlanIds.has(detailCourse?.plan_id)" type="primary"
          :disabled="(detailCourse?.available || 0) <= 0" :loading="enrolling"
          @click="doEnroll(detailCourse)">
          选课
        </el-button>
        <el-button v-else type="danger" :loading="dropping" @click="doDrop(detailCourse)">
          退课
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Filter, List } from '@element-plus/icons-vue'
import request from '@/utils/request'

const weekdayNames = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
const TOTAL_WEEKS = 20

const loading = ref(false)
const enrolling = ref(false)
const enrollingPlanId = ref(null)
const dropping = ref(false)
const droppingPlanId = ref(null)
const courses = ref([])
const myCourses = ref([])
const enrolledPlanIds = ref(new Set())
const departments = ref([])
const showFilters = ref(false)
const sidebarExpanded = ref(false)
const expandedPlanId = ref(null)
const detailVisible = ref(false)
const detailCourse = ref(null)

const search = ref({
  keyword: '',
  semester: '2026-2027-1',
  department: '',
  creditRange: '',
  weekday: null,
  examType: '',
  courseType: '',
})

const filteredCourses = computed(() => {
  let list = courses.value
  const kw = search.value.keyword?.toLowerCase()
  if (kw) {
    list = list.filter(c =>
      (c.course_name || '').toLowerCase().includes(kw) ||
      (c.teacher_id || '').toLowerCase().includes(kw) ||
      (c.teacher_name || '').toLowerCase().includes(kw) ||
      (c.department || '').toLowerCase().includes(kw)
    )
  }
  return list
})

function getWeekOccupancy(day, period) {
  let occupiedWeeks = new Set()
  for (const mc of myCourses.value) {
    if (mc.weekday === day && mc.period_start <= period && mc.period_start + mc.period_count - 1 >= period) {
      for (let w = mc.start_week || 1; w <= (mc.end_week || TOTAL_WEEKS); w++) {
        occupiedWeeks.add(w)
      }
    }
  }
  return occupiedWeeks.size
}

function heatmapClass(day, period) {
  const free = TOTAL_WEEKS - getWeekOccupancy(day, period)
  if (free === TOTAL_WEEKS) return 'green'
  if (free >= TOTAL_WEEKS / 2) return 'yellow'
  return 'red'
}

function heatmapText(day, period) {
  const free = TOTAL_WEEKS - getWeekOccupancy(day, period)
  return free === TOTAL_WEEKS ? '空' : free
}

function heatmapTitle(day, period) {
  const free = TOTAL_WEEKS - getWeekOccupancy(day, period)
  return `${weekdayNames[day - 1]} 第${period}节: 空闲${free}/${TOTAL_WEEKS}周`
}

onMounted(async () => {
  await Promise.all([fetchData(), fetchMyCourses()])
})

async function fetchData() {
  loading.value = true
  try {
    const params = {}
    if (search.value.semester) params.semester = search.value.semester
    if (search.value.department) params.department = search.value.department
    if (search.value.creditRange) params.credit_range = search.value.creditRange
    if (search.value.weekday) params.weekday = search.value.weekday
    if (search.value.examType) params.exam_type = search.value.examType
    if (search.value.courseType) params.course_type = search.value.courseType
    const res = await request.get('/student/courses', { params })
    courses.value = res.data?.items || []
    departments.value = [...new Set(courses.value.map(c => c.department).filter(Boolean))]
  } finally { loading.value = false }
}

async function fetchMyCourses() {
  const res = await request.get('/student/my-courses')
  myCourses.value = res.data?.items || []
  enrolledPlanIds.value = new Set(myCourses.value.map(c => c.plan_id))
}

function onSearch() {}
function toggleExpand(course) {
  expandedPlanId.value = expandedPlanId.value === course.plan_id ? null : course.plan_id
}

function openDetail(course) {
  detailCourse.value = course
  detailVisible.value = true
}

async function doEnroll(course) {
  enrollingPlanId.value = course.plan_id
  try {
    const res = await request.post('/enrollment/select', { plan_id: course.plan_id })
    if (res.success) {
      ElMessage.success(res.message || '选课成功')
      detailVisible.value = false
      expandedPlanId.value = null
      await fetchMyCourses()
      await fetchData()
    }
  } finally { enrollingPlanId.value = null }
}

async function doDrop(course) {
  try {
    await ElMessageBox.confirm(`确认退选 "${course.course_name}"？`, '退课确认', { type: 'warning' })
  } catch { return }

  droppingPlanId.value = course.plan_id
  try {
    const res = await request.post('/enrollment/drop', { plan_id: course.plan_id })
    if (res.success) {
      ElMessage.success(res.message || '退课成功')
      detailVisible.value = false
      expandedPlanId.value = null
      await fetchMyCourses()
      await fetchData()
    }
  } finally { droppingPlanId.value = null }
}
</script>

<style scoped>
.enroll-container { height: calc(100vh - 100px); position: relative; }
.enroll-main { padding-right: 80px; }

.search-section { margin-bottom: 16px; }
.search-bar { display: flex; gap: 12px; align-items: center; }
.filter-panel { background: #fff; border-radius: 4px; padding: 16px; margin-top: 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.08); }
.filter-row { display: flex; gap: 12px; align-items: center; flex-wrap: wrap; }
.filter-label { font-size: 13px; color: #606266; min-width: 32px; }

.course-cards { display: flex; flex-direction: column; gap: 8px; }
.course-card {
  background: #fff; border-radius: 6px;
  border: 1px solid #e4e7ed; cursor: pointer; transition: all 0.2s;
}
.course-card:hover { border-color: #409eff; box-shadow: 0 2px 8px rgba(64,158,255,0.15); }
.course-card.is-enrolled { border-color: #67c23a; background: #f0f9eb; }
.course-card.is-expanded { border-color: #409eff; box-shadow: 0 2px 12px rgba(64,158,255,0.2); }
.card-header { display: flex; justify-content: space-between; align-items: center; padding: 10px 18px; }
.card-title { margin: 0; font-size: 15px; flex: 1; }
.card-meta { display: flex; gap: 8px; align-items: center; font-size: 12px; color: #909399; flex: 2; }
.card-badges { display: flex; gap: 8px; align-items: center; }
.expand-arrow { font-size: 12px; color: #909399; }
.card-detail { padding: 0 18px 16px; border-top: 1px solid #ebeef5; }

/* 侧边栏 */
.course-sidebar {
  position: fixed; right: 0; top: 60px; bottom: 0; width: 48px;
  background: #fff; border-left: 1px solid #e4e7ed; z-index: 100;
  transition: width 0.3s; overflow: hidden;
}
.course-sidebar.expanded { width: 360px; padding: 12px; overflow-y: auto; }
.sidebar-toggle {
  display: flex; flex-direction: column; align-items: center; gap: 4px;
  padding: 12px 0; cursor: pointer; color: #409eff;
}
.toggle-text { font-size: 12px; }
.sidebar-content { margin-top: 8px; }

.week-heatmap { font-size: 11px; }
.heatmap-header, .heatmap-row { display: grid; grid-template-columns: 42px repeat(11, 1fr); gap: 1px; margin-bottom: 1px; }
.hm-label { text-align: center; color: #909399; }
.hm-header-cell { text-align: center; font-weight: 500; color: #606266; }
.hm-cell {
  aspect-ratio: 1; display: flex; align-items: center; justify-content: center;
  border-radius: 2px; font-size: 10px; color: #fff; cursor: default;
}
.hm-cell.green { background: #67c23a; }
.hm-cell.yellow { background: #e6a23c; }
.hm-cell.red { background: #f56c6c; }

.heatmap-legend { display: flex; gap: 12px; margin-top: 4px; font-size: 11px; color: #909399; flex-wrap: wrap; }
.legend-dot { display: inline-block; width: 10px; height: 10px; border-radius: 2px; margin-right: 2px; vertical-align: middle; }
.legend-dot.green { background: #67c23a; }
.legend-dot.yellow { background: #e6a23c; }
.legend-dot.red { background: #f56c6c; }

.sidebar-courses { margin-top: 4px; }
.sidebar-course-item { padding: 8px 0; border-bottom: 1px solid #f0f0f0; }
.sc-name { font-size: 13px; color: #303133; font-weight: 500; }
.sc-time { font-size: 11px; color: #909399; }
.sc-weeks { font-size: 11px; color: #c0c4cc; }
</style>
