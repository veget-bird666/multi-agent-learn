<template>
  <div class="max-w-6xl mx-auto px-4 py-6">
    <!-- 顶部导航 -->
    <div class="flex items-center justify-between mb-6">
      <div>
        <h2 class="text-xl font-bold text-gray-900">
          {{ pathTitle || '学习路径' }}
        </h2>
        <p class="text-sm text-gray-400 mt-0.5">
          {{ path ? '各阶段卡片颜色反映当前掌握度' : '开始对话学习后自动生成' }}
        </p>
      </div>
      <div class="flex items-center gap-3">
        <!-- 刷新按钮 -->
        <button
          @click="loadPath"
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
    <div v-else-if="!path" class="bg-white rounded-2xl border border-gray-100 p-16 text-center">
      <div class="text-5xl mb-4">🗺️</div>
      <h3 class="text-lg font-semibold text-gray-700 mb-2">暂无学习路径</h3>
      <p class="text-sm text-gray-400 mb-6">开始对话学习后，系统将自动为你规划个性化的学习路径</p>
      <router-link
        to="/chat"
        class="inline-flex items-center gap-2 bg-gradient-to-r from-blue-600 to-purple-600 text-white px-6 py-2.5 rounded-lg text-sm font-medium hover:shadow-lg transition-all"
      >
        开始学习
        <span>→</span>
      </router-link>
    </div>

    <!-- 看板主体 -->
    <template v-else>
      <!-- 掌握度一览 -->
      <div class="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-6">
        <div class="bg-white rounded-xl border border-gray-100 p-4 text-center">
          <div class="text-2xl font-bold text-gray-900">{{ path.steps.length }}</div>
          <div class="text-xs text-gray-400 mt-1">总阶段数</div>
        </div>
        <div class="bg-white rounded-xl border border-gray-100 p-4 text-center">
          <div class="text-2xl font-bold" :class="overallColor">{{ path.overall_mastery }}%</div>
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
          <span class="text-xs text-gray-400">{{ completedCount }} / {{ path.steps.length }} 阶段</span>
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
          v-for="(step, i) in path.steps"
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
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useChatStore } from '../stores/chat'
import { fetchLearningPath } from '../api'

const chatStore = useChatStore()
const loading = ref(true)
const path = ref(null)
const expandedSteps = ref({})

/** 学习路径标题 */
const pathTitle = computed(() => path.value?.title || '')

/** 已完成阶段数（mastery >= 80） */
const completedCount = computed(() =>
  path.value?.steps.filter(s => s.mastery >= 80).length || 0
)

/** 进行中阶段数（0 < mastery < 80） */
const inProgressCount = computed(() =>
  path.value?.steps.filter(s => s.mastery > 0 && s.mastery < 80).length || 0
)

/** 进度百分比 */
const progressPercent = computed(() => {
  if (!path.value?.steps?.length) return 0
  return Math.round(completedCount.value / path.value.steps.length * 100)
})

/** 总体掌握度颜色 */
const overallColor = computed(() => {
  const m = path.value?.overall_mastery || 0
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

async function loadPath() {
  loading.value = true
  try {
    const data = await fetchLearningPath(chatStore.studentId)
    path.value = data.path || null
  } catch (e) {
    console.error('加载学习路径失败:', e)
  } finally {
    loading.value = false
  }
}

onMounted(loadPath)
</script>
