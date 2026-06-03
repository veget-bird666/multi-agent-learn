<template>
  <div class="max-w-4xl mx-auto px-6 py-8">
    <div class="flex items-center justify-between mb-8">
      <h2 class="text-xl font-bold text-gray-900">学习路径</h2>
      <router-link to="/chat" class="text-xs text-blue-600 hover:text-blue-700 bg-blue-50 px-3 py-1.5 rounded-lg transition-colors">
        ← 返回对话
      </router-link>
    </div>

    <!-- 空状态 -->
    <div v-if="!hasPath" class="bg-white rounded-2xl border border-gray-100 p-12 text-center">
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

    <!-- 路径时间线 -->
    <div v-else class="space-y-6">
      <!-- 进度概览 -->
      <div class="bg-white rounded-2xl border border-gray-100 p-6">
        <div class="flex items-center justify-between mb-4">
          <h3 class="font-semibold text-gray-900">学习进度</h3>
          <span class="text-sm text-gray-500">{{ completedCount }} / {{ totalCount }} 阶段</span>
        </div>
        <div class="w-full bg-gray-100 rounded-full h-2.5">
          <div
            class="bg-gradient-to-r from-blue-500 to-purple-500 h-2.5 rounded-full transition-all duration-500"
            :style="{ width: progressPercent + '%' }"
          ></div>
        </div>
      </div>

      <!-- 步骤列表 -->
      <div class="relative">
        <!-- 时间线竖线 -->
        <div class="absolute left-5 top-0 bottom-0 w-0.5 bg-gray-100"></div>

        <div
          v-for="(step, i) in steps"
          :key="i"
          class="relative pl-14 pb-8 last:pb-0"
        >
          <!-- 时间线节点 -->
          <div
            :class="[
              'absolute left-3.5 w-4 h-4 rounded-full border-2 bg-white z-10',
              step.status === 'completed' ? 'border-green-500 bg-green-50' :
              step.status === 'in_progress' ? 'border-blue-500 bg-blue-50' :
              'border-gray-300',
            ]"
          >
            <div v-if="step.status === 'completed'" class="absolute inset-0 flex items-center justify-center text-green-500 text-xs">✓</div>
            <div v-if="step.status === 'in_progress'" class="absolute inset-0 flex items-center justify-center">
              <div class="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></div>
            </div>
          </div>

          <!-- 步骤卡片 -->
          <div
            :class="[
              'rounded-xl border p-4 transition-all',
              step.status === 'completed' ? 'bg-green-50/50 border-green-100' :
              step.status === 'in_progress' ? 'bg-blue-50/50 border-blue-100 shadow-sm' :
              'bg-white border-gray-100',
            ]"
          >
            <div class="flex items-start justify-between mb-2">
              <div>
                <span class="text-xs text-gray-400 font-mono">阶段 {{ step.order }}</span>
                <h4 class="font-semibold text-gray-900 mt-0.5">{{ step.stage_name }}</h4>
              </div>
              <span :class="['text-xs px-2 py-0.5 rounded-full', difficultyClass(step.difficulty)]">
                {{ difficultyLabel(step.difficulty) }}
              </span>
            </div>
            <p class="text-sm text-gray-600 mb-2">{{ step.description }}</p>
            <div v-if="step.knowledge_points" class="flex flex-wrap gap-1">
              <span
                v-for="(kp, ki) in step.knowledge_points"
                :key="ki"
                class="text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded"
              >
                {{ kp }}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

// TODO: 从 API 获取学习路径
const hasPath = ref(false)
const steps = ref([])

const totalCount = computed(() => steps.value.length)
const completedCount = computed(() => steps.value.filter(s => s.status === 'completed').length)
const progressPercent = computed(() => totalCount.value ? Math.round(completedCount.value / totalCount.value * 100) : 0)

function difficultyClass(d) {
  if (d === 'easy') return 'bg-green-50 text-green-600'
  if (d === 'hard') return 'bg-red-50 text-red-600'
  return 'bg-yellow-50 text-yellow-600'
}

function difficultyLabel(d) {
  if (d === 'easy') return '基础'
  if (d === 'hard') return '进阶'
  return '中等'
}
</script>
