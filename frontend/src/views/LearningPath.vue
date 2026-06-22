<template>
  <div class="max-w-6xl mx-auto px-4 py-6">
    <!-- 顶部导航 -->
    <div class="flex items-center justify-between mb-6">
      <div>
        <h2 class="text-xl font-bold text-gray-900">学习路径</h2>
        <p class="text-sm text-gray-400 mt-0.5">
          你可以有多条学习路径，选择一条开始学习
        </p>
      </div>
      <div class="flex items-center gap-3">
        <button
          @click="loadAll"
          :disabled="loading"
          class="text-xs text-blue-600 hover:text-blue-700 bg-blue-50 px-3 py-1.5 rounded-lg transition-colors disabled:opacity-40"
        >
          {{ loading ? '加载中...' : '刷新' }}
        </button>
        <router-link
          to="/chat"
          class="text-xs text-gray-500 hover:text-gray-700 bg-gray-100 px-3 py-1.5 rounded-lg transition-colors"
        >
          ← 返回对话
        </router-link>
      </div>
    </div>

    <!-- 加载态 -->
    <div v-if="loading" class="flex items-center justify-center py-24">
      <div class="flex flex-col items-center gap-3">
        <div class="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
        <span class="text-sm text-gray-400">加载学习路径...</span>
      </div>
    </div>

    <!-- 空态 -->
    <div v-else-if="pathList.length === 0" class="bg-white rounded-2xl border border-gray-100 p-16 text-center">
      <div class="text-5xl mb-4">🗺️</div>
      <h3 class="text-lg font-semibold text-gray-700 mb-2">暂无学习路径</h3>
      <p class="text-sm text-gray-400 mb-6">开始对话学习后，系统将自动为你规划多条个性化的学习路径</p>
      <router-link
        to="/chat"
        class="inline-flex items-center gap-2 bg-gradient-to-r from-blue-600 to-purple-600 text-white px-6 py-2.5 rounded-lg text-sm font-medium hover:shadow-lg transition-all"
      >
        开始学习
        <span>→</span>
      </router-link>
    </div>

    <!-- 有路径 → 路径选择器 + 看板 -->
    <template v-else>
      <!-- 路径选择器 -->
      <div class="flex flex-wrap items-center gap-2 mb-6">
        <span class="text-xs text-gray-400 mr-1">我的路径：</span>
        <button
          v-for="p in pathList"
          :key="p.id"
          @click="switchPath(p.id)"
          class="group relative flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium transition-all"
          :class="selectedPathId === p.id
            ? 'bg-gradient-to-r from-blue-600 to-purple-600 text-white shadow-md'
            : 'bg-white border border-gray-200 text-gray-600 hover:border-blue-300 hover:text-blue-600'"
        >
          <span class="truncate max-w-[180px]">{{ p.title }}</span>
          <span
            class="text-xs px-1.5 py-0.5 rounded-full"
            :class="selectedPathId === p.id ? 'bg-white/20' : 'bg-gray-100 text-gray-400'"
          >
            {{ p.steps.length }}阶
          </span>
          <!-- 删除按钮（hover 显示，选中时不显示） -->
          <button
            v-if="selectedPathId !== p.id"
            @click.stop="confirmDeletePath(p)"
            class="absolute -top-1.5 -right-1.5 w-5 h-5 bg-white border border-gray-200 rounded-full text-gray-400 hover:text-red-500 hover:border-red-200 opacity-0 group-hover:opacity-100 transition-all flex items-center justify-center text-xs shadow-sm"
            title="删除此路径"
          >
            ✕
          </button>
        </button>
      </div>

      <!-- 当前路径看板 -->
      <template v-if="currentPath">
        <!-- 掌握度一览 -->
        <div class="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-6">
          <div class="bg-white rounded-xl border border-gray-100 p-4 text-center">
            <div class="text-2xl font-bold text-gray-900">{{ currentPath.steps.length }}</div>
            <div class="text-xs text-gray-400 mt-1">总阶段数</div>
          </div>
          <div class="bg-white rounded-xl border border-gray-100 p-4 text-center">
            <div class="text-2xl font-bold" :class="overallColor">{{ currentPath.overall_mastery }}%</div>
            <div class="text-xs text-gray-400 mt-1">总体掌握度</div>
          </div>
          <div class="bg-white rounded-xl border border-gray-100 p-4 text-center">
            <div class="text-2xl font-bold text-green-600">{{ completedCount }}</div>
            <div class="text-xs text-gray-400 mt-1">已完成</div>
          </div>
          <div class="bg-white rounded-xl border border-gray-100 p-4 text-center">
            <div class="text-2xl font-bold text-blue-600">{{ inProgressCount }}</div>
            <div class="text-xs text-gray-400 mt-1">进行中</div>
          </div>
        </div>

        <!-- 进度条 -->
        <div class="bg-white rounded-xl border border-gray-100 p-4 mb-6">
          <div class="flex items-center justify-between mb-2">
            <span class="text-sm font-medium text-gray-700">学习进度</span>
            <span class="text-xs text-gray-400">{{ completedCount }} / {{ currentPath.steps.length }} 阶段</span>
          </div>
          <div class="w-full bg-gray-100 rounded-full h-3">
            <div
              class="h-3 rounded-full transition-all duration-700"
              :class="progressBarColor"
              :style="{ width: progressPercent + '%' }"
            ></div>
          </div>
        </div>

        <!-- 掌握度图例 -->
        <div class="flex items-center gap-4 mb-4 text-xs text-gray-500">
          <span class="flex items-center gap-1.5">
            <span class="w-3 h-3 rounded-sm bg-red-400"></span> 待加强 (&lt;30%)
          </span>
          <span class="flex items-center gap-1.5">
            <span class="w-3 h-3 rounded-sm bg-yellow-400"></span> 学习中 (30-70%)
          </span>
          <span class="flex items-center gap-1.5">
            <span class="w-3 h-3 rounded-sm bg-green-400"></span> 已掌握 (&gt;70%)
          </span>
        </div>

        <!-- 卡片网格 -->
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          <div
            v-for="(step, i) in currentPath.steps"
            :key="step.order"
            class="rounded-xl border-2 p-5 transition-all duration-300 hover:shadow-lg cursor-pointer"
            :class="cardBorder(step.mastery)"
            @click="toggleExpand(step.order)"
          >
            <!-- 卡片头部 -->
            <div class="flex items-start justify-between mb-3">
              <div class="flex items-center gap-2">
                <span
                  class="w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold text-white"
                  :class="stepBadge(step.mastery)"
                >
                  {{ step.order }}
                </span>
                <div>
                  <span class="text-xs" :class="stepStatusText(step.mastery)">
                    {{ stepStatusLabel(step.mastery) }}
                  </span>
                </div>
              </div>
              <span class="text-xs px-2 py-0.5 rounded-full bg-gray-100 text-gray-500 font-mono">
                {{ difficultyLabel(step.difficulty) }}
              </span>
            </div>

            <!-- 阶段名称 -->
            <h4 class="font-semibold text-gray-900 mb-2 leading-snug">{{ step.stage_name }}</h4>

            <!-- 进度条（小） -->
            <div class="flex items-center gap-2 mb-2">
              <div class="flex-1 bg-gray-100 rounded-full h-1.5">
                <div
                  class="h-1.5 rounded-full transition-all duration-500"
                  :class="masteryBarColor(step.mastery)"
                  :style="{ width: step.mastery + '%' }"
                ></div>
              </div>
              <span class="text-xs font-mono font-bold" :class="masteryTextColor(step.mastery)">
                {{ Math.round(step.mastery) }}%
              </span>
            </div>

            <!-- 描述（展开时显示） -->
            <div
              v-if="expandedSteps[step.order]"
              class="mt-3 pt-3 border-t border-gray-100 space-y-2"
            >
              <p class="text-sm text-gray-600 leading-relaxed">{{ step.description }}</p>
              <div v-if="step.knowledge_points && step.knowledge_points.length" class="flex flex-wrap gap-1.5">
                <span
                  v-for="(kp, ki) in step.knowledge_points"
                  :key="ki"
                  class="text-xs bg-blue-50 text-blue-700 px-2 py-0.5 rounded-md"
                >
                  {{ kp }}
                </span>
              </div>
              <p v-if="step.duration_estimate" class="text-xs text-gray-400 mt-1">
                ⏱ {{ step.duration_estimate }}
              </p>

              <!-- 关联资源列表 -->
              <div v-if="getStepResources(step.order).length" class="mt-3 pt-3 border-t border-gray-100">
                <p class="text-xs text-gray-400 mb-2">📎 关联资源（{{ getStepResources(step.order).length }}）</p>
                <div class="space-y-1">
                  <div
                    v-for="res in getStepResources(step.order)"
                    :key="res.orm_id || res.id"
                    class="flex items-center gap-2 px-3 py-2 rounded-lg bg-gray-50 hover:bg-gray-100 cursor-pointer transition-colors"
                    @click.stop="openResource(res)"
                  >
                    <span>{{ typeIconMap[res.type] || '📄' }}</span>
                    <span class="text-xs text-gray-700 truncate flex-1">{{ res.title }}</span>
                    <span class="text-xs text-gray-400 flex-shrink-0">{{ typeLabelMap[res.type] || res.type }}</span>
                  </div>
                </div>
              </div>
            </div>

            <!-- 展开/收起 -->
            <div class="mt-2 text-center">
              <span class="text-xs text-gray-400">
                {{ expandedSteps[step.order] ? '收起详情 ▲' : '展开详情 ▼' }}
              </span>
            </div>
          </div>
        </div>
      </template>
    </template>

    <!-- 试卷作答弹窗 -->
    <ExamModal
      v-if="examTaking"
      :resource="examTaking"
      @close="examTaking = null"
    />

    <!-- 删除确认弹窗 -->
    <Teleport to="body">
      <div
        v-if="deleteTarget"
        class="fixed inset-0 bg-black/40 z-50 flex items-center justify-center p-4"
        @click.self="deleteTarget = null"
      >
        <div class="bg-white rounded-2xl p-6 max-w-sm w-full shadow-2xl">
          <div class="text-center mb-4">
            <div class="text-3xl mb-3">🗑️</div>
            <h3 class="font-semibold text-gray-900 mb-1">确认删除</h3>
            <p class="text-sm text-gray-500">删除「{{ deleteTarget.title }}」后将无法恢复，确认删除吗？</p>
          </div>
          <div class="flex gap-3">
            <button
              @click="deleteTarget = null"
              class="flex-1 px-4 py-2.5 border border-gray-200 rounded-xl text-sm text-gray-600 hover:bg-gray-50 transition-colors"
            >取消</button>
            <button
              @click="doDeletePath"
              class="flex-1 px-4 py-2.5 bg-red-500 text-white rounded-xl text-sm hover:bg-red-600 transition-colors"
            >确认删除</button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useChatStore } from '../stores/chat'
import { listLearningPaths, fetchLearningPath, setActivePath, deleteLearningPath, fetchResources } from '../api'
import ExamModal from '../components/ExamModal.vue'

const chatStore = useChatStore()
const loading = ref(true)
const pathList = ref([])           // 全部路径摘要列表
const selectedPathId = ref(null)   // 当前选中的路径 ID
const currentPath = ref(null)      // 当前选中路径的完整数据
const expandedSteps = ref({})
const deleteTarget = ref(null)
const allResources = ref([])
const examTaking = ref(null)

/** 资源类型图标 */
const typeIconMap = {
  document: '📄', exam: '📝', ppt: '📊', image: '🖼️',
  video: '🎬', exercise: '✏️', mindmap: '🧠', code_example: '💻', extra_reading: '📚',
}

/** 资源类型中文名 */
const typeLabelMap = {
  document: '文档', exam: '试卷', ppt: 'PPT', image: '图片',
  video: '视频', exercise: '练习', mindmap: '思维导图', code_example: '代码', extra_reading: '拓展',
}

/** 获取某个阶段关联的资源 */
function getStepResources(stepOrder) {
  if (!currentPath.value) return []
  return allResources.value.filter(r => {
    const so = r.step_order
    return so !== null && so !== undefined && Number(so) === Number(stepOrder)
  })
}

/** 点击资源后的行为 */
function openResource(res) {
  if (res.type === 'exam') {
    examTaking.value = res
  } else {
    // 非试卷资源跳转到资源页面
    window.location.hash = '#/resources'
  }
}

/** 已完成阶段数（mastery >= 80） */
const completedCount = computed(() =>
  currentPath.value?.steps.filter(s => s.mastery >= 80).length || 0
)

/** 进行中阶段数（0 < mastery < 80） */
const inProgressCount = computed(() =>
  currentPath.value?.steps.filter(s => s.mastery > 0 && s.mastery < 80).length || 0
)

/** 进度百分比 */
const progressPercent = computed(() => {
  if (!currentPath.value?.steps?.length) return 0
  return Math.round(completedCount.value / currentPath.value.steps.length * 100)
})

/** 总体掌握度颜色 */
const overallColor = computed(() => {
  const m = currentPath.value?.overall_mastery || 0
  if (m >= 70) return 'text-green-600'
  if (m >= 30) return 'text-yellow-600'
  return 'text-red-500'
})

/** 进度条颜色 */
const progressBarColor = computed(() => {
  const p = progressPercent.value
  if (p >= 70) return 'bg-gradient-to-r from-green-400 to-green-500'
  if (p >= 30) return 'bg-gradient-to-r from-yellow-400 to-orange-400'
  return 'bg-gradient-to-r from-red-400 to-orange-400'
})

/** 卡片边框颜色 */
function cardBorder(mastery) {
  const m = mastery || 0
  if (m >= 80) return 'border-green-300 bg-green-50/30 hover:border-green-400'
  if (m >= 30) return 'border-yellow-300 bg-yellow-50/30 hover:border-yellow-400'
  return 'border-red-200 bg-red-50/20 hover:border-red-300'
}

/** 阶段徽章颜色 */
function stepBadge(mastery) {
  const m = mastery || 0
  if (m >= 80) return 'bg-green-500'
  if (m >= 30) return 'bg-yellow-500'
  return 'bg-red-400'
}

/** 掌握度进度条颜色 */
function masteryBarColor(mastery) {
  const m = mastery || 0
  if (m >= 80) return 'bg-green-500'
  if (m >= 30) return 'bg-yellow-500'
  return 'bg-red-400'
}

/** 掌握度文字颜色 */
function masteryTextColor(mastery) {
  const m = mastery || 0
  if (m >= 80) return 'text-green-600'
  if (m >= 30) return 'text-yellow-600'
  return 'text-red-500'
}

/** 阶段状态文字 */
function stepStatusLabel(mastery) {
  const m = mastery || 0
  if (m >= 80) return '已掌握'
  if (m > 0) return '学习中'
  return '未开始'
}

/** 阶段状态文字颜色 */
function stepStatusText(mastery) {
  const m = mastery || 0
  if (m >= 80) return 'text-green-600'
  if (m > 0) return 'text-yellow-600'
  return 'text-gray-400'
}

/** 难度标签 */
function difficultyLabel(d) {
  if (d === 'easy') return '基础'
  if (d === 'hard') return '进阶'
  return '中等'
}

/** 展开/收起某阶段详情 */
function toggleExpand(order) {
  expandedSteps.value[order] = !expandedSteps.value[order]
}

/** 切换查看的路径 */
async function switchPath(pathId) {
  if (pathId === selectedPathId.value) return
  selectedPathId.value = pathId
  await loadPathDetail(pathId)
  // 设为当前选中
  try {
    await setActivePath(chatStore.studentId, pathId)
    // 更新 pathList 中的 is_active
    pathList.value.forEach(p => { p.is_active = (p.id === pathId) })
  } catch (e) {
    console.error('激活路径失败:', e)
  }
}

/** 加载路径详情 */
async function loadPathDetail(pathId) {
  try {
    const [detail, resData] = await Promise.all([
      fetchLearningPath(pathId),
      fetchResources(chatStore.studentId),
    ])
    currentPath.value = detail
    expandedSteps.value = {}
    allResources.value = (resData.resources || []).filter(r =>
      r.path_id && Number(r.path_id) === Number(pathId)
    )
  } catch (e) {
    console.error('加载路径详情失败:', e)
  }
}

/** 确认删除 */
function confirmDeletePath(p) {
  deleteTarget.value = p
}

/** 执行删除 */
async function doDeletePath() {
  if (!deleteTarget.value) return
  const targetId = deleteTarget.value.id
  try {
    await deleteLearningPath(targetId)
    // 从列表中移除
    pathList.value = pathList.value.filter(p => p.id !== targetId)
    // 如果删除的是当前选中的，切换到第一条
    if (selectedPathId.value === targetId) {
      if (pathList.value.length > 0) {
        await switchPath(pathList.value[0].id)
      } else {
        selectedPathId.value = null
        currentPath.value = null
      }
    }
    deleteTarget.value = null
  } catch (e) {
    console.error('删除失败:', e)
  }
}

/** 加载全部路径 + 激活的路径 */
async function loadAll() {
  loading.value = true
  try {
    // 获取路径列表
    const data = await listLearningPaths(chatStore.studentId)
    pathList.value = data.paths || []

    if (pathList.value.length === 0) {
      currentPath.value = null
      selectedPathId.value = null
      return
    }

    // 优先选 active 的路径，否则取最新一条
    const active = pathList.value.find(p => p.is_active)
    const target = active || pathList.value[0]
    selectedPathId.value = target.id
    await loadPathDetail(target.id)
  } catch (e) {
    console.error('加载学习路径失败:', e)
  } finally {
    loading.value = false
  }
}

onMounted(loadAll)
</script>
