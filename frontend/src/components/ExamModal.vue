<template>
  <Teleport to="body">
    <div class="fixed inset-0 bg-black/40 z-50 flex items-center justify-center p-4" @click.self="$emit('close')">
      <div class="bg-white rounded-2xl shadow-2xl w-full max-w-2xl max-h-[85vh] flex flex-col overflow-hidden">
        <!-- 头部 -->
        <div class="flex items-center justify-between px-6 py-4 border-b border-gray-100 flex-shrink-0">
          <div>
            <h3 class="text-base font-semibold text-gray-900">{{ examTitle }}</h3>
            <p class="text-xs text-gray-400 mt-0.5">
              {{ questions.length }} 道题
              <span v-if="!submitted"> · 点击提交后自动批改并更新熟练度</span>
              <span v-else> · 答对 {{ correctCount }}/{{ gradedCount }} 题</span>
            </p>
          </div>
          <button @click="$emit('close')" class="w-7 h-7 flex items-center justify-center text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors text-sm">
            ✕
          </button>
        </div>

        <!-- 题目列表 -->
        <div class="flex-1 overflow-y-auto px-6 py-4 space-y-6 scrollbar-thin">
          <div
            v-for="(q, i) in questions"
            :key="q.id"
            class="pb-5 border-b border-gray-50 last:border-b-0"
            :class="{ 'opacity-60': submitted && !isCorrect(q) }"
          >
            <!-- 题目标题 -->
            <div class="flex items-start gap-2 mb-3">
              <span class="w-6 h-6 rounded-full bg-gray-100 text-gray-500 flex items-center justify-center text-xs font-bold flex-shrink-0 mt-0.5">{{ i + 1 }}</span>
              <div class="flex-1 min-w-0">
                <div class="flex items-center gap-2 mb-1">
                  <span class="text-xs px-1.5 py-0.5 rounded-full font-mono" :class="difficultyBadge(q.difficulty)">
                    {{ difficultyLabel(q.difficulty) }}
                  </span>
                  <span class="text-xs text-gray-400">{{ typeLabel(q.type) }}</span>
                  <span v-if="q.knowledge_point" class="text-xs text-blue-500 bg-blue-50 px-1.5 py-0.5 rounded">
                    {{ q.knowledge_point }}
                  </span>
                </div>
                <p class="text-sm text-gray-800 leading-relaxed" v-html="q.question"></p>
              </div>
            </div>

            <!-- 选择题选项 -->
            <div v-if="q.type === 'choice'" class="ml-8 space-y-2">
              <label
                v-for="(opt, oi) in q.options"
                :key="oi"
                class="flex items-start gap-3 px-4 py-3 rounded-xl border-2 cursor-pointer transition-all"
                :class="optionClass(q, opt, oi)"
              >
                <input
                  type="radio"
                  :name="'q_' + q.id"
                  :value="opt.charAt(0)"
                  v-model="answers[q.id]"
                  :disabled="submitted"
                  class="mt-0.5 accent-blue-600"
                  @change="onAnswerChange"
                />
                <span class="text-sm text-gray-700">{{ opt }}</span>
              </label>
              <!-- 提交后显示正确答案 -->
              <div v-if="submitted && q.answer" class="mt-2 text-xs" :class="isCorrect(q) ? 'text-green-600' : 'text-red-500'">
                {{ isCorrect(q) ? '✓ 回答正确' : '✗ 正确答案：' + q.answer }}
                <p v-if="q.explanation" class="text-gray-500 mt-1">{{ q.explanation }}</p>
              </div>
            </div>

            <!-- 填空题 -->
            <div v-else-if="q.type === 'fill'" class="ml-8">
              <input
                v-model="answers[q.id]"
                :disabled="submitted"
                placeholder="输入答案..."
                class="w-full px-4 py-2.5 border-2 border-gray-200 rounded-xl text-sm focus:outline-none focus:border-blue-300 disabled:bg-gray-50 disabled:text-gray-500"
              />
              <div v-if="submitted" class="mt-2 space-y-1">
                <div class="text-xs" :class="isCorrect(q) ? 'text-green-600' : 'text-red-500'">
                  {{ isCorrect(q) ? '✓ 回答正确' : '✗ 参考答案：' + q.answer }}
                </div>
                <p v-if="q.explanation" class="text-xs text-gray-500">{{ q.explanation }}</p>
              </div>
            </div>

            <!-- 简答题 -->
            <div v-else-if="q.type === 'short_answer'" class="ml-8">
              <textarea
                v-model="answers[q.id]"
                :disabled="submitted"
                placeholder="输入你的回答..."
                rows="3"
                class="w-full px-4 py-2.5 border-2 border-gray-200 rounded-xl text-sm focus:outline-none focus:border-blue-300 disabled:bg-gray-50 disabled:text-gray-500 resize-none"
              ></textarea>
              <div v-if="submitted" class="mt-2 space-y-1">
                <div class="flex items-center gap-2">
                  <span class="text-xs text-gray-500">参考答案：{{ q.answer }}</span>
                </div>
                <div v-if="!autoGraded(q)" class="flex items-center gap-2 mt-2">
                  <input
                    type="checkbox"
                    :id="'self_' + q.id"
                    v-model="selfGraded[q.id]"
                    disabled
                    class="accent-green-500"
                  />
                  <label :for="'self_' + q.id" class="text-xs" :class="selfGraded[q.id] ? 'text-green-600' : 'text-gray-400'">
                    我答对了
                  </label>
                </div>
                <p v-if="q.explanation" class="text-xs text-gray-500 mt-1">{{ q.explanation }}</p>
              </div>
            </div>
          </div>
        </div>

        <!-- 底部：提交/结果 -->
        <div class="flex-shrink-0 px-6 py-4 border-t border-gray-100 bg-gray-50/50">
          <!-- 未提交：提交按钮 -->
          <div v-if="!submitted" class="flex items-center justify-between">
            <span class="text-xs text-gray-400">{{ answeredCount }}/{{ questions.length }} 题已作答</span>
            <button
              @click="submit"
              :disabled="submitting"
              class="bg-gradient-to-r from-blue-600 to-purple-600 text-white px-6 py-2.5 rounded-xl text-sm font-medium hover:shadow-lg disabled:opacity-40 transition-all"
            >
              {{ submitting ? '提交批改中...' : '提交批改' }}
            </button>
          </div>
          <!-- 已提交：结果 + 关闭 -->
          <div v-else class="flex items-center justify-between">
            <div class="flex items-center gap-4">
              <span class="text-sm font-medium" :class="correctRate >= 70 ? 'text-green-600' : correctRate >= 30 ? 'text-yellow-600' : 'text-red-500'">
                {{ correctCount }}/{{ gradedCount }} 正确 ({{ Math.round(correctRate) }}%)
              </span>
              <span v-if="masteryUpdated" class="text-xs text-blue-600 bg-blue-50 px-2.5 py-1 rounded-full">
                🎯 熟练度已更新
              </span>
            </div>
            <button
              @click="$emit('close')"
              class="bg-gray-200 text-gray-600 px-5 py-2 rounded-xl text-sm hover:bg-gray-300 transition-colors"
            >
              关闭
            </button>
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { submitExam as apiSubmitExam } from '../api'
import { useChatStore } from '../stores/chat'

const props = defineProps({
  resource: { type: Object, required: true },
})

defineEmits(['close'])

const chatStore = useChatStore()
const questions = ref([])
const answers = ref({})
const selfGraded = ref({})
const submitted = ref(false)
const submitting = ref(false)
const gradingResults = ref([])
const masteryUpdated = ref(false)

/** 解析试卷 JSON */
function parseExam() {
  try {
    const data = JSON.parse(props.resource.content)
    examTitle.value = data.title || props.resource.title || '试卷'
    questions.value = (data.questions || []).map(q => ({
      ...q,
      // 确保每个问题有 id
      id: q.id || Math.random().toString(36).slice(2, 8),
      step_order: q.step_order || props.resource.step_order,
    }))
  } catch (e) {
    console.error('解析试卷失败:', e)
    questions.value = []
    examTitle.value = '试卷解析失败'
  }
}

const examTitle = ref('试卷加载中...')

/** 题型中文名 */
function typeLabel(type) {
  const map = { choice: '选择题', fill: '填空题', short_answer: '简答题' }
  return map[type] || type
}

/** 难度标签 */
function difficultyLabel(d) {
  const map = { easy: '基础', medium: '中等', hard: '进阶' }
  return map[d] || d
}

function difficultyBadge(d) {
  const map = {
    easy: 'bg-green-50 text-green-600',
    medium: 'bg-yellow-50 text-yellow-600',
    hard: 'bg-red-50 text-red-600',
  }
  return map[d] || 'bg-gray-100 text-gray-500'
}

/** 已回答计数 */
const answeredCount = computed(() => {
  return questions.value.filter(q => {
    const a = answers.value[q.id]
    if (q.type === 'choice') return a && a.trim().length > 0
    return a && a.trim().length > 0
  }).length
})

/** 选择题选项样式 */
function optionClass(q, opt, oi) {
  const letter = opt.charAt(0)
  const selected = answers.value[q.id] === letter

  if (!submitted.value) {
    return selected
      ? 'border-blue-300 bg-blue-50/50'
      : 'border-gray-100 hover:border-gray-200'
  }

  // 提交后：正确选项标绿，错误标红
  const isCorrectOpt = letter === q.answer
  const isWrongSelection = selected && !isCorrectOpt

  if (isWrongSelection) return 'border-red-300 bg-red-50'
  if (isCorrectOpt) return 'border-green-300 bg-green-50'
  if (selected) return 'border-green-300 bg-green-50'
  return 'border-gray-100 opacity-50'
}

/** 能否自动批改 */
function autoGraded(q) {
  return q.type === 'choice' || q.type === 'fill'
}

/** 是否正确 */
function isCorrect(q) {
  const r = gradingResults.value.find(r => r.question_id === q.id)
  return r ? r.is_correct : false
}

/** 提交批改 */
async function submit() {
  submitting.value = true

  // 批改逻辑
  const results = []
  let correctCnt = 0

  for (const q of questions.value) {
    const userAnswer = (answers.value[q.id] || '').trim()
    let correct = false

    if (q.type === 'choice') {
      correct = userAnswer.toUpperCase() === (q.answer || '').toString().toUpperCase()
    } else if (q.type === 'fill') {
      correct = userAnswer.toLowerCase() === (q.answer || '').toLowerCase()
    } else if (q.type === 'short_answer') {
      // 简答题由用户自评（在答题时已经选了 checkbox）
      correct = !!selfGraded.value[q.id]
    }

    if (correct) correctCnt++
    results.push({
      question_id: q.id,
      knowledge_point: q.knowledge_point || '',
      is_correct: correct,
      difficulty: q.difficulty || 'medium',
    })
  }

  gradingResults.value = results
  submitted.value = true

  // 提交到后端更新熟练度（如果有 path_id 和 step_order）
  const pathId = chatStore.currentPathId || props.resource.path_id
  const stepOrder = props.resource.step_order || questions.value[0]?.step_order

  if (pathId && stepOrder) {
    try {
      const apiResults = results
        .filter(r => r.knowledge_point)
        .map(r => ({
          knowledge_point: r.knowledge_point,
          is_correct: r.is_correct,
          difficulty: r.difficulty,
        }))
      if (apiResults.length > 0) {
        await apiSubmitExam(pathId, stepOrder, apiResults)
        masteryUpdated.value = true
        console.log(`[ExamModal]  熟练度已更新: 路径#{pathId} 阶段{stepOrder}`)
      }
    } catch (e) {
      console.error('更新熟练度失败:', e)
    }
  }

  submitting.value = false
}

/** 无自评的题目（choice, fill）直接用自动批改结果 */
const correctCount = computed(() => gradingResults.value.filter(r => r.is_correct).length)
const gradedCount = computed(() => gradingResults.value.length)
const correctRate = computed(() => {
  if (gradedCount.value === 0) return 0
  return (correctCount.value / gradedCount.value) * 100
})

onMounted(parseExam)
</script>

<style scoped>
.scrollbar-thin::-webkit-scrollbar { width: 4px; }
.scrollbar-thin::-webkit-scrollbar-track { background: transparent; }
.scrollbar-thin::-webkit-scrollbar-thumb { background: #e2e8f0; border-radius: 4px; }
</style>
