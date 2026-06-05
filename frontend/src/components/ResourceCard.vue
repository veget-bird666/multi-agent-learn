<template>
  <div>
    <!-- 卡片 -->
    <div
      class="bg-white rounded-xl border border-gray-100 p-4 hover:shadow-md hover:border-blue-100 transition-all duration-200 group cursor-pointer"
      @click="openResource"
    >
      <div class="flex items-start gap-3">
        <!-- 类型图标 -->
        <div :class="['w-10 h-10 rounded-lg flex items-center justify-center text-lg flex-shrink-0', typeStyle.bg]">
          {{ typeStyle.icon }}
        </div>

        <div class="flex-1 min-w-0">
          <div class="flex items-center gap-2 mb-1">
            <span :class="['text-xs font-medium px-2 py-0.5 rounded-full', typeStyle.badge]">{{ typeStyle.label }}</span>
            <span :class="['text-xs px-2 py-0.5 rounded-full', difficultyStyle]">{{ difficultyLabel }}</span>
          </div>
          <h4 class="font-medium text-sm text-gray-900 mb-1 group-hover:text-blue-600 transition-colors truncate">{{ resource.title }}</h4>
          <p class="text-xs text-gray-400 truncate">{{ resource.knowledge_point }}</p>
        </div>

        <!-- 箭头 -->
        <div class="text-gray-200 group-hover:text-blue-400 transition-colors flex-shrink-0 mt-2">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/>
          </svg>
        </div>
      </div>
    </div>

    <!-- 内容预览弹窗（文档 / 试卷） -->
    <Teleport to="body">
      <div
        v-if="showModal"
        class="fixed inset-0 bg-black/40 z-50 flex items-center justify-center p-4 md:p-8"
        @click.self="showModal = false"
      >
        <div class="bg-white rounded-2xl max-w-3xl w-full max-h-[90vh] flex flex-col shadow-2xl">
          <!-- 弹窗头部 -->
          <div class="flex items-center justify-between px-6 py-4 border-b border-gray-100 shrink-0">
            <div class="flex items-center gap-2">
              <span class="text-lg">{{ typeStyle.icon }}</span>
              <h3 class="font-semibold text-gray-900">{{ resource.title }}</h3>
              <span :class="['text-xs px-2 py-0.5 rounded-full', typeStyle.badge]">{{ typeStyle.label }}</span>
            </div>
            <button
              @click="showModal = false"
              class="text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg w-8 h-8 flex items-center justify-center transition-colors text-lg"
            >✕</button>
          </div>
          <!-- 弹窗内容 -->
          <div class="flex-1 overflow-y-auto p-6">
            <!-- 文档类型：渲染 Markdown -->
            <div v-if="modalType === 'document'" class="chat-markdown text-sm" v-html="renderedContent"></div>
            <!-- 试卷类型：交互式作答 -->
            <div v-else-if="modalType === 'exam'" class="text-sm">
              <div v-if="examData">
                <div class="mb-4 text-gray-500 text-xs">总分：{{ examData.total_score || '未标注' }} | 共 {{ examData.questions?.length || 0 }} 题</div>
                <div v-for="(q, i) in examData.questions" :key="i" class="mb-6 pb-5 border-b border-gray-100 last:border-0">
                  <div class="flex items-start gap-2">
                    <span class="text-gray-400 font-mono text-xs mt-0.5">{{ i + 1 }}.</span>
                    <div class="flex-1">
                      <!-- 题目 -->
                      <p class="text-gray-900 mb-3 font-medium">{{ q.question }}</p>

                      <!-- 选择题选项 -->
                      <div v-if="q.type === 'choice' && q.options" class="space-y-2 mb-3">
                        <div
                          v-for="(opt, oi) in q.options"
                          :key="oi"
                          class="flex items-center gap-2 px-3 py-2 rounded-lg border cursor-pointer transition-all text-xs"
                          :class="optionClass(q, i, oi)"
                          @click="selectOption(i, oi)"
                        >
                          <span class="w-4 h-4 rounded-full border-2 flex items-center justify-center flex-shrink-0"
                            :class="radioClass(q, i, oi)">
                            <span v-if="isSelected(i, oi)" class="w-2 h-2 rounded-full bg-current"></span>
                          </span>
                          <span>{{ opt }}</span>
                        </div>
                      </div>

                      <!-- 填空题输入 -->
                      <div v-if="q.type === 'fill'" class="mb-3">
                        <input
                          v-model="userAnswers[i]"
                          type="text"
                          :disabled="revealed[i]"
                          placeholder="请输入答案..."
                          class="w-full border border-gray-200 rounded-lg px-3 py-2 text-xs focus:outline-none focus:border-blue-400 disabled:bg-gray-50"
                        />
                      </div>

                      <!-- 简答题输入 -->
                      <div v-if="q.type === 'short_answer'" class="mb-3">
                        <textarea
                          v-model="userAnswers[i]"
                          :disabled="revealed[i]"
                          placeholder="请输入你的回答..."
                          rows="3"
                          class="w-full border border-gray-200 rounded-lg px-3 py-2 text-xs focus:outline-none focus:border-blue-400 resize-none disabled:bg-gray-50"
                        ></textarea>
                      </div>

                      <!-- 操作区：难度 + 按钮 -->
                      <div class="flex items-center gap-2 text-xs">
                        <span :class="difficultyBadge(q.difficulty)">{{ difficultyLabelFor(q.difficulty) }}</span>
                        <template v-if="!revealed[i]">
                          <button
                            v-if="userAnswers[i]"
                            @click="revealAnswer(i)"
                            class="bg-blue-500 text-white px-3 py-1 rounded-lg hover:bg-blue-600 transition-colors"
                          >提交答案</button>
                          <span v-else class="text-gray-300">请作答后提交</span>
                        </template>
                        <template v-else>
                          <span class="text-gray-300">|</span>
                          <span :class="isCorrect(i) ? 'text-green-600 font-medium' : 'text-red-500 font-medium'">
                            {{ isCorrect(i) ? '✓ 正确' : '✗ 回答有误' }}
                          </span>
                          <span class="text-gray-300">|</span>
                          <span class="text-green-700 font-medium">参考答案：{{ q.answer }}</span>
                          <button
                            @click="resetQuestion(i)"
                            class="text-gray-400 hover:text-gray-600 ml-1 underline"
                          >重做</button>
                        </template>
                      </div>
                      <p v-if="revealed[i] && q.explanation" class="text-gray-500 text-xs mt-2 bg-gray-50 rounded-lg p-2">解析：{{ q.explanation }}</p>
                    </div>
                  </div>
                </div>
              </div>
              <pre v-else class="bg-gray-50 rounded-lg p-4 text-xs overflow-x-auto">{{ resource.content }}</pre>
            </div>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { computed, ref, reactive, watch } from 'vue'
import MarkdownIt from 'markdown-it'

const md = new MarkdownIt({
  html: false,
  linkify: true,
  breaks: true,
})

const props = defineProps({
  resource: { type: Object, required: true },
})

const showModal = ref(false)
const modalType = ref('')

// ── 试卷交互状态 ──
const userAnswers = reactive({})     // { 题目索引: 用户答案 }
const revealed = reactive({})        // { 题目索引: true/false } 是否已提交检查
const selectedOptions = reactive({}) // { 题目索引: 选项索引 } 仅选择题用

// 关闭弹窗时重置试卷状态
watch(showModal, (val) => {
  if (!val) {
    Object.keys(userAnswers).forEach(k => { delete userAnswers[k] })
    Object.keys(revealed).forEach(k => { delete revealed[k] })
    Object.keys(selectedOptions).forEach(k => { delete selectedOptions[k] })
  }
})

function selectOption(qIdx, optIdx) {
  if (revealed[qIdx]) return
  selectedOptions[qIdx] = optIdx
  userAnswers[qIdx] = String.fromCharCode(65 + optIdx) // A, B, C, D...
}

function isSelected(qIdx, optIdx) {
  return selectedOptions[qIdx] === optIdx
}

function radioClass(q, qIdx, optIdx) {
  if (!isSelected(qIdx, optIdx)) return 'border-gray-300'
  return 'border-blue-500 text-blue-500'
}

function optionClass(q, qIdx, optIdx) {
  const base = 'border-gray-200 hover:border-blue-200 hover:bg-blue-50'
  if (!isSelected(qIdx, optIdx)) return base
  if (!revealed[qIdx]) return 'border-blue-400 bg-blue-50'
  // 已提交：判断对错
  const isCorrectOpt = isSelected(qIdx, optIdx) && isCorrect(qIdx)
  return isCorrectOpt ? 'border-green-400 bg-green-50' : 'border-red-300 bg-red-50'
}

function revealAnswer(qIdx) {
  revealed[qIdx] = true
}

function resetQuestion(qIdx) {
  delete revealed[qIdx]
  delete userAnswers[qIdx]
  delete selectedOptions[qIdx]
}

function isCorrect(qIdx) {
  const exam = examData.value
  if (!exam || !exam.questions[qIdx]) return false
  const q = exam.questions[qIdx]
  const userAns = (userAnswers[qIdx] || '').trim().toLowerCase()
  const correctAns = (q.answer || '').trim().toLowerCase()
  return userAns === correctAns
}

const typeMap = {
  document: { icon: '📄', label: '文档', bg: 'bg-blue-50', badge: 'bg-blue-50 text-blue-600' },
  exam: { icon: '📝', label: '试卷', bg: 'bg-green-50', badge: 'bg-green-50 text-green-600' },
  ppt: { icon: '📊', label: 'PPT', bg: 'bg-orange-50', badge: 'bg-orange-50 text-orange-600' },
  image: { icon: '🖼️', label: '图片', bg: 'bg-pink-50', badge: 'bg-pink-50 text-pink-600' },
  video: { icon: '🎬', label: '视频', bg: 'bg-purple-50', badge: 'bg-purple-50 text-purple-600' },
  exercise: { icon: '✏️', label: '练习', bg: 'bg-teal-50', badge: 'bg-teal-50 text-teal-600' },
  mindmap: { icon: '🧠', label: '思维导图', bg: 'bg-yellow-50', badge: 'bg-yellow-50 text-yellow-600' },
  code_example: { icon: '💻', label: '代码', bg: 'bg-indigo-50', badge: 'bg-indigo-50 text-indigo-600' },
  extra_reading: { icon: '📚', label: '拓展', bg: 'bg-rose-50', badge: 'bg-rose-50 text-rose-600' },
}

const resolvedType = computed(() => {
  const t = props.resource.type
  return typeof t === 'string' ? t : (t?.value || 'document')
})

const typeStyle = computed(() => {
  return typeMap[resolvedType.value] || { icon: '📄', label: resolvedType.value, bg: 'bg-gray-50', badge: 'bg-gray-50 text-gray-600' }
})

const difficultyStyle = computed(() => {
  const d = props.resource.difficulty
  if (d === 'easy') return 'bg-green-50 text-green-600'
  if (d === 'hard') return 'bg-red-50 text-red-600'
  return 'bg-yellow-50 text-yellow-600'
})

const difficultyLabel = computed(() => {
  const d = props.resource.difficulty
  if (d === 'easy') return '基础'
  if (d === 'hard') return '进阶'
  return '中等'
})

const difficultyLabelFor = (d) => {
  if (d === 'easy') return '基础'
  if (d === 'hard') return '进阶'
  return '中等'
}

const examData = computed(() => {
  if (resolvedType.value !== 'exam') return null
  try {
    return JSON.parse(props.resource.content)
  } catch {
    return null
  }
})

const renderedContent = computed(() => {
  return md.render(props.resource.content || '')
})

function difficultyBadge(d) {
  if (d === 'easy') return 'bg-green-50 text-green-600 px-1.5 py-0.5 rounded'
  if (d === 'hard') return 'bg-red-50 text-red-600 px-1.5 py-0.5 rounded'
  return 'bg-yellow-50 text-yellow-600 px-1.5 py-0.5 rounded'
}

function openResource() {
  const content = props.resource.content
  if (!content) return

  const type = resolvedType.value

  // 文档 / 试卷 → 弹窗展示
  if (type === 'document' || type === 'exam') {
    modalType.value = type
    showModal.value = true
    return
  }

  // URL 或本地路径 → 下载或打开
  if (content.startsWith('http://') || content.startsWith('https://') || content.startsWith('/')) {
    // PPT 等不可在浏览器中渲染的文件 → 触发下载
    if (type === 'ppt') {
      const a = document.createElement('a')
      a.href = content
      a.download = props.resource.title || 'download'
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
    } else {
      window.open(content, '_blank')
    }
  }
}
</script>
