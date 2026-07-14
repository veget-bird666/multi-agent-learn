<template>
  <div class="max-w-5xl mx-auto px-6 py-8">
    <!-- 页面标题 -->
    <div class="flex items-center justify-between mb-8">
      <div>
        <h1 class="text-2xl font-bold text-gray-100">📊 学习效果评估</h1>
        <p class="text-sm text-gray-500 mt-1">基于学习日志的多维度分析，定位薄弱环节</p>
      </div>
    </div>

    <!-- ── 路径选择 + 触发 ────────────────────────────── -->
    <div class="bg-dark-surface rounded-2xl p-5 border border-dark-border mb-8">
      <div class="flex items-end gap-4 flex-wrap">
        <div class="flex-1 min-w-[240px]">
          <label class="block text-sm text-gray-400 mb-1.5">选择学习路径</label>
          <select
            v-model="selectedPathId"
            class="w-full bg-dark-bg border border-dark-border rounded-xl px-4 py-2.5 text-gray-200 text-sm focus:outline-none focus:border-blue-500/50 transition-colors appearance-none cursor-pointer"
          >
            <option value="" disabled>-- 请选择 --</option>
            <option
              v-for="p in paths"
              :key="p.id"
              :value="p.id"
            >
              {{ p.title }} ({{ p.overall_mastery }}% · {{ p.steps?.length || 0 }}阶段)
            </option>
          </select>
        </div>
        <button
          @click="runEvaluation"
          :disabled="loading || !selectedPathId"
          class="inline-flex items-center gap-2 bg-gradient-to-r from-blue-600 to-purple-600 text-white px-6 py-2.5 rounded-xl font-medium hover:shadow-lg hover:shadow-blue-500/20 transition-all duration-300 disabled:opacity-40 disabled:cursor-not-allowed"
        >
          <span v-if="loading" class="animate-spin">⏳</span>
          <span v-else>🚀</span>
          <span>{{ loading ? '评估中...' : '开始评估' }}</span>
        </button>
      </div>
    </div>

    <!-- ── 无路径状态 ─────────────────────────────────── -->
    <div v-if="!loading && paths.length === 0 && !report" class="text-center py-20">
      <div class="text-5xl mb-4">📭</div>
      <h2 class="text-xl font-semibold text-gray-300 mb-2">暂无学习路径</h2>
      <p class="text-gray-500 mb-6">请先在对话中生成学习路径后，再进行评估。</p>
      <router-link
        to="/chat"
        class="inline-flex items-center gap-2 bg-dark-surface border border-dark-border text-gray-300 px-6 py-2.5 rounded-xl hover:border-blue-500/30 transition-all"
      >
        <span>去学习</span>
        <span>→</span>
      </router-link>
    </div>

    <!-- ── 加载中 ─────────────────────────────────────── -->
    <div v-if="loading" class="text-center py-20">
      <div class="text-4xl mb-4 animate-pulse">📊</div>
      <p class="text-gray-400">正在分析学习数据，生成评估报告...</p>
    </div>

    <!-- ── 无数据（已有路径但无学习日志） ─────────────── -->
    <div v-else-if="noData" class="text-center py-16">
      <div class="text-5xl mb-4">📭</div>
      <h2 class="text-xl font-semibold text-gray-300 mb-2">暂无评估数据</h2>
      <p class="text-gray-500">{{ noDataMessage }}</p>
    </div>

    <!-- ══════════════════════════════════════════════════ -->
    <!--  评估报告                                       -->
    <!-- ══════════════════════════════════════════════════ -->
    <div v-else-if="report" class="space-y-6">

      <!-- 综合评分 + 雷达图 两栏布局 -->
      <div class="grid grid-cols-1 md:grid-cols-5 gap-5">
        <!-- 综合评分卡片 -->
        <div class="md:col-span-2 bg-dark-surface rounded-2xl p-6 border border-dark-border flex flex-col justify-center">
          <div class="flex items-center justify-between mb-3">
            <h2 class="text-sm font-semibold text-gray-400 uppercase tracking-wide">综合评分</h2>
            <span
              class="text-lg"
              :class="trendClass"
            >{{ trendIcon }} {{ trendLabel }}</span>
          </div>
          <div class="flex items-end gap-2 mb-2">
            <span class="text-6xl font-bold" :class="overallScoreColor">{{ report.overall_score }}</span>
            <span class="text-lg text-gray-500 mb-1">/ 100</span>
          </div>
          <p class="text-sm text-gray-500 leading-relaxed">{{ report.summary }}</p>
        </div>

        <!-- 雷达图 -->
        <div class="md:col-span-3 bg-dark-surface rounded-2xl p-4 border border-dark-border flex items-center justify-center">
          <RadarChart
            v-if="report.dimension_scores && report.dimension_scores.length"
            :dimensions="report.dimension_scores"
            :size="340"
          />
          <p v-else class="text-gray-500">暂无维度数据</p>
        </div>
      </div>

      <!-- 各维度评分详情 -->
      <div class="bg-dark-surface rounded-2xl p-6 border border-dark-border">
        <h2 class="text-lg font-semibold text-gray-200 mb-5">各维度评分</h2>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-5">
          <div
            v-for="dim in report.dimension_scores"
            :key="dim.name"
            class="bg-dark-bg/40 rounded-xl p-4"
          >
            <div class="flex items-center justify-between mb-1.5">
              <span class="text-sm font-medium text-gray-200">{{ dim.name }}</span>
              <span class="text-sm font-bold" :class="scoreTextColor(dim.score)">{{ dim.score }}</span>
            </div>
            <div class="w-full h-2 bg-dark-bg rounded-full overflow-hidden mb-1.5">
              <div
                class="h-full rounded-full transition-all duration-700"
                :class="scoreBarColor(dim.score)"
                :style="{ width: dim.score + '%' }"
              ></div>
            </div>
            <p class="text-xs text-gray-500">{{ dim.detail }}</p>
          </div>
        </div>
      </div>

      <!-- 优势与薄弱点 双栏 -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-5">
        <div class="bg-dark-surface rounded-2xl p-6 border border-dark-border">
          <h2 class="text-lg font-semibold text-gray-200 mb-3">✅ 优势</h2>
          <ul class="space-y-2.5">
            <li
              v-for="(s, i) in report.strengths"
              :key="i"
              class="flex items-start gap-2 text-sm text-gray-300"
            >
              <span class="text-green-400 mt-0.5 shrink-0">✓</span>
              <span>{{ s }}</span>
            </li>
            <li v-if="!report.strengths || report.strengths.length === 0" class="text-sm text-gray-500">
              暂无明显优势
            </li>
          </ul>
        </div>

        <div class="bg-dark-surface rounded-2xl p-6 border border-dark-border">
          <h2 class="text-lg font-semibold text-gray-200 mb-3">🔴 薄弱点</h2>
          <div v-if="report.weak_points && report.weak_points.length > 0" class="space-y-3">
            <div
              v-for="(wp, i) in report.weak_points"
              :key="i"
              class="bg-dark-bg/50 rounded-xl p-3"
            >
              <div class="flex items-center justify-between mb-1">
                <span class="text-sm font-medium text-gray-200">{{ wp.knowledge_point }}</span>
                <span class="text-xs text-red-400">掌握度 {{ wp.mastery }}</span>
              </div>
              <p class="text-xs text-gray-500 mb-1">{{ wp.error_pattern }}</p>
              <p class="text-xs text-blue-400">{{ wp.suggestion }}</p>
            </div>
          </div>
          <p v-else class="text-sm text-gray-500">暂无明显的薄弱点</p>
        </div>
      </div>

      <!-- 待巩固知识点 -->
      <div
        v-if="report.at_risk_kps && report.at_risk_kps.length > 0"
        class="bg-dark-surface rounded-2xl p-6 border border-dark-border"
      >
        <h2 class="text-lg font-semibold text-gray-200 mb-3">⚠️ 需巩固的知识点</h2>
        <div class="flex flex-wrap gap-2">
          <span
            v-for="kp in report.at_risk_kps"
            :key="kp"
            class="px-3 py-1.5 bg-yellow-500/10 text-yellow-400 text-sm rounded-lg border border-yellow-500/20"
          >
            {{ kp }}
          </span>
        </div>
      </div>

      <!-- 学习建议 -->
      <div class="bg-gradient-to-r from-blue-600/8 to-purple-600/8 rounded-2xl p-6 border border-blue-500/15">
        <h2 class="text-lg font-semibold text-gray-200 mb-3">💡 学习建议</h2>
        <div class="text-sm text-gray-300 leading-relaxed whitespace-pre-wrap">{{ report.learning_suggestion }}</div>
      </div>

      <!-- 统计数据（客观，非 LLM 生成） -->
      <div
        v-if="report.statistics"
        class="bg-dark-surface/50 rounded-2xl p-5 border border-dark-border"
      >
        <h2 class="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3">📋 数据概览</h2>
        <div class="grid grid-cols-2 md:grid-cols-5 gap-4 text-center">
          <div>
            <div class="text-xl font-bold text-gray-200">{{ report.statistics.total_questions || 0 }}</div>
            <div class="text-xs text-gray-500 mt-0.5">总答题数</div>
          </div>
          <div>
            <div class="text-xl font-bold text-gray-200">{{ report.statistics.accuracy || 0 }}%</div>
            <div class="text-xs text-gray-500 mt-0.5">正确率</div>
          </div>
          <div>
            <div class="text-xl font-bold text-gray-200">{{ report.statistics.covered_kps || 0 }}/{{ report.statistics.total_kps || 0 }}</div>
            <div class="text-xs text-gray-500 mt-0.5">覆盖知识点</div>
          </div>
          <div>
            <div class="text-xl font-bold text-gray-200">{{ report.statistics.coverage || 0 }}%</div>
            <div class="text-xs text-gray-500 mt-0.5">知识广度</div>
          </div>
          <div>
            <div class="text-xl font-bold text-gray-200">{{ pathMastery }}%</div>
            <div class="text-xs text-gray-500 mt-0.5">路径掌握度</div>
          </div>
        </div>
      </div>

      <!-- 评估时间 -->
      <div class="text-center text-xs text-gray-600 pb-4">
        评估时间：{{ report.evaluated_at || '刚刚' }}
        <span v-if="selectedPathId"> · 路径 ID: {{ selectedPathId }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { listLearningPaths, triggerEvaluation, getLatestEvaluation } from '../api/index.js'
import RadarChart from '../components/RadarChart.vue'

const DEFAULT_STUDENT = 'student_001'

const paths = ref([])
const selectedPathId = ref('')
const loading = ref(false)
const noData = ref(false)
const noDataMessage = ref('')
const report = ref(null)

const pathMastery = computed(() => {
  return report.value?.statistics?.overall_mastery || 0
})

const trendClass = computed(() => {
  if (!report.value) return ''
  switch (report.value.trend) {
    case 'up': return 'text-green-400'
    case 'down': return 'text-red-400'
    default: return 'text-yellow-400'
  }
})

const trendIcon = computed(() => {
  if (!report.value) return ''
  switch (report.value.trend) {
    case 'up': return '📈'
    case 'down': return '📉'
    default: return '➡️'
  }
})

const trendLabel = computed(() => {
  if (!report.value) return ''
  switch (report.value.trend) {
    case 'up': return '上升'
    case 'down': return '下降'
    default: return '稳定'
  }
})

const overallScoreColor = computed(() => {
  if (!report.value) return 'text-gray-100'
  const s = report.value.overall_score
  if (s >= 70) return 'text-green-400'
  if (s >= 40) return 'text-yellow-400'
  return 'text-red-400'
})

function scoreTextColor(score) {
  if (score >= 70) return 'text-green-400'
  if (score >= 40) return 'text-yellow-400'
  return 'text-red-400'
}

function scoreBarColor(score) {
  if (score >= 70) return 'bg-green-500'
  if (score >= 40) return 'bg-yellow-500'
  return 'bg-red-500'
}

async function loadPaths() {
  try {
    const result = await listLearningPaths(DEFAULT_STUDENT)
    paths.value = result.paths || []
    // 自动选中第一条路径
    if (paths.value.length > 0) {
      selectedPathId.value = paths.value[0].id
    }
  } catch {
    // 静默处理
  }
}

async function runEvaluation() {
  if (!selectedPathId.value) return

  loading.value = true
  noData.value = false
  report.value = null

  try {
    const result = await triggerEvaluation(DEFAULT_STUDENT, selectedPathId.value)
    if (!result.evaluation) {
      noData.value = true
      noDataMessage.value = result.response || '暂无足够学习数据完成评估'
    } else {
      report.value = result.evaluation
    }
  } catch (err) {
    noData.value = true
    noDataMessage.value = err.message || '评估请求失败'
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadPaths()
})
</script>
