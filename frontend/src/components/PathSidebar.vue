<template>
  <aside class="w-[280px] flex-shrink-0 h-full bg-white/60 backdrop-blur-sm border-r border-gray-200/60 flex flex-col overflow-hidden">
    <!-- 标题 -->
    <div class="px-5 pt-5 pb-3 border-b border-gray-100/80">
      <div class="flex items-center justify-between">
        <h3 class="text-sm font-semibold text-gray-700">学习路径</h3>
        <button
          @click="refresh"
          :disabled="loading"
          class="text-xs text-blue-500 hover:text-blue-600 transition-colors disabled:opacity-40"
        >
          {{ loading ? '...' : '↻' }}
        </button>
      </div>
      <p class="text-[11px] text-gray-400 mt-0.5">选择一个阶段聚焦，Agent 将重点围绕它生成内容</p>
    </div>

    <!-- 路径列表（无路径时） -->
    <div v-if="!loading && paths.length === 0" class="flex-1 flex flex-col items-center justify-center px-5 text-center">
      <div class="text-2xl mb-2 opacity-30">🗺️</div>
      <p class="text-xs text-gray-400">暂无学习路径</p>
      <p class="text-[11px] text-gray-300 mt-1">开始对话后自动生成</p>
    </div>

    <!-- 加载中 -->
    <div v-if="loading" class="flex-1 flex items-center justify-center">
      <div class="w-5 h-5 border-2 border-blue-400 border-t-transparent rounded-full animate-spin"></div>
    </div>

    <!-- 路径内容 -->
    <template v-if="!loading && paths.length > 0">
      <!-- 路径选择器 -->
      <div class="px-4 pt-3 pb-2">
        <select
          v-model="selectedPathId"
          @change="onPathChange"
          class="path-select w-full text-xs bg-white border border-gray-200 rounded-lg px-3 py-2 text-gray-600 focus:outline-none focus:border-blue-300 focus:ring-1 focus:ring-blue-200 appearance-none cursor-pointer"
        >
          <option v-for="p in paths" :key="p.id" :value="p.id">{{ p.title }}</option>
        </select>
      </div>

      <!-- 阶段列表 -->
      <div class="flex-1 overflow-y-auto px-3 pb-4 space-y-2 scrollbar-thin">
        <div
          v-for="step in currentSteps"
          :key="step.order"
          @click="toggleFocus(step.order)"
          class="group relative rounded-xl border-2 p-3 cursor-pointer transition-all duration-200"
          :class="stepCardClass(step)"
        >
          <!-- 顶部行：序号 + 状态 -->
          <div class="flex items-center justify-between mb-2">
            <div class="flex items-center gap-2">
              <span
                class="w-6 h-6 rounded-full flex items-center justify-center text-[11px] font-bold text-white flex-shrink-0"
                :class="stepBadge(step.mastery)"
              >
                {{ step.order }}
              </span>
              <span class="text-[11px]" :class="stepStatusText(step.mastery)">
                {{ stepStatusLabel(step.mastery) }}
              </span>
            </div>
            <span
              v-if="focusedStep === step.order"
              class="text-[10px] px-2 py-0.5 rounded-full bg-blue-100 text-blue-600 font-medium"
            >
              ● 聚焦中
            </span>
            <span
              v-else
              class="text-[10px] text-gray-300 group-hover:text-gray-400 transition-colors"
            >
              点击聚焦
            </span>
          </div>

          <!-- 阶段名称 -->
          <h4 class="text-xs font-semibold text-gray-800 mb-1.5 leading-snug">{{ step.stage_name }}</h4>

          <!-- 知识点标签 -->
          <div v-if="step.knowledge_points && step.knowledge_points.length" class="flex flex-wrap gap-1 mb-2">
            <span
              v-for="(kp, ki) in step.knowledge_points.slice(0, 3)"
              :key="ki"
              class="text-[10px] bg-gray-100 text-gray-500 px-1.5 py-0.5 rounded"
            >
              {{ kp.length > 6 ? kp.slice(0, 6) + '…' : kp }}
            </span>
            <span v-if="step.knowledge_points.length > 3" class="text-[10px] text-gray-400">
              +{{ step.knowledge_points.length - 3 }}
            </span>
          </div>

          <!-- 掌握度条 -->
          <div class="flex items-center gap-2">
            <div class="flex-1 bg-gray-100 rounded-full h-1.5">
              <div
                class="h-1.5 rounded-full transition-all duration-500"
                :class="masteryBarColor(step.mastery)"
                :style="{ width: step.mastery + '%' }"
              ></div>
            </div>
            <span class="text-[10px] font-mono font-bold" :class="masteryTextColor(step.mastery)">
              {{ Math.round(step.mastery) }}%
            </span>
          </div>
        </div>
      </div>
    </template>
  </aside>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useChatStore } from '../stores/chat'
import { listLearningPaths, fetchActiveLearningPath } from '../api'

const chatStore = useChatStore()
const loading = ref(true)
const selectedPathId = ref(null)

// 本地路径列表，同时同步到 store 供 Chat.vue 使用
const paths = ref([])

// 当前选中的路径的阶段列表
const currentSteps = ref([])

/** 当前聚焦的阶段 */
const focusedStep = computed(() => chatStore.focusedStepOrder)

/** 加载所有路径 */
async function refresh() {
  loading.value = true
  try {
    const data = await listLearningPaths(chatStore.studentId)
    const loaded = data.paths || []
    paths.value = loaded

    // 同步到 store（供 Chat.vue 读取）
    chatStore.pathList = loaded

    if (loaded.length === 0) {
      currentSteps.value = []
      selectedPathId.value = null
      return
    }

    // 优先选中已激活的路径
    const active = loaded.find(p => p.is_active) || loaded[0]
    selectedPathId.value = active.id
    currentSteps.value = active.steps || []

    // 同步 store 中的 currentPathId
    chatStore.currentPathId = active.id
  } catch (e) {
    console.error('加载路径失败:', e)
  } finally {
    loading.value = false
  }
}

/** 切换路径 */
async function onPathChange() {
  const path = paths.value.find(p => p.id === selectedPathId.value)
  if (path) {
    currentSteps.value = path.steps || []
    chatStore.currentPathId = path.id
    // 切换路径时取消聚焦
    chatStore.clearFocus()
  }
}

// 监听 store 中的 pathList 变化（其他组件可能更新）
watch(() => chatStore.pathList, (val) => {
  if (val && val.length > 0) {
    paths.value = val
  }
})

/** 切换聚焦 */
function toggleFocus(stepOrder) {
  if (focusedStep.value === stepOrder) {
    chatStore.clearFocus()
  } else {
    chatStore.focusStep(stepOrder)
  }
}

// ── 样式工具 ──

function stepCardClass(step) {
  const isFocused = focusedStep.value === step.order
  const m = step.mastery || 0
  const base = isFocused
    ? 'border-blue-400 bg-blue-50/60 shadow-sm'
    : 'border-gray-100 bg-white hover:border-gray-200 hover:shadow-sm'
  return base
}

function stepBadge(mastery) {
  const m = mastery || 0
  if (m >= 80) return 'bg-green-500'
  if (m >= 30) return 'bg-yellow-500'
  return 'bg-red-400'
}

function masteryBarColor(mastery) {
  const m = mastery || 0
  if (m >= 80) return 'bg-green-500'
  if (m >= 30) return 'bg-yellow-500'
  return 'bg-red-400'
}

function masteryTextColor(mastery) {
  const m = mastery || 0
  if (m >= 80) return 'text-green-600'
  if (m >= 30) return 'text-yellow-600'
  return 'text-red-500'
}

function stepStatusLabel(mastery) {
  const m = mastery || 0
  if (m >= 80) return '已掌握'
  if (m > 0) return '学习中'
  return '未开始'
}

function stepStatusText(mastery) {
  const m = mastery || 0
  if (m >= 80) return 'text-green-600'
  if (m > 0) return 'text-yellow-600'
  return 'text-gray-400'
}

onMounted(refresh)
</script>

<style scoped>
.path-select {
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath fill='%23999' d='M6 8L1 3h10z'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 8px center;
  padding-right: 28px;
}

/* 滚动条 */
.scrollbar-thin::-webkit-scrollbar {
  width: 4px;
}
.scrollbar-thin::-webkit-scrollbar-track {
  background: transparent;
}
.scrollbar-thin::-webkit-scrollbar-thumb {
  background: #e2e8f0;
  border-radius: 4px;
}
</style>
