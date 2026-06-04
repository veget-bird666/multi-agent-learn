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
            <!-- 试卷类型：格式化显示 -->
            <div v-else-if="modalType === 'exam'" class="text-sm">
              <div v-if="examData">
                <div class="mb-4 text-gray-500 text-xs">总分：{{ examData.total_score || '未标注' }} | 共 {{ examData.questions?.length || 0 }} 题</div>
                <div v-for="(q, i) in examData.questions" :key="i" class="mb-5 pb-4 border-b border-gray-100 last:border-0">
                  <div class="flex items-start gap-2">
                    <span class="text-gray-400 font-mono text-xs mt-0.5">{{ i + 1 }}.</span>
                    <div class="flex-1">
                      <p class="text-gray-900 mb-2">{{ q.question }}</p>
                      <div v-if="q.options" class="space-y-1 mb-2">
                        <p v-for="(opt, oi) in q.options" :key="oi" class="text-gray-600 text-xs">{{ opt }}</p>
                      </div>
                      <div class="flex items-center gap-2 text-xs">
                        <span :class="difficultyBadge(q.difficulty)">{{ difficultyLabelFor(q.difficulty) }}</span>
                        <span class="text-gray-300">|</span>
                        <span class="text-green-600">答案：{{ q.answer }}</span>
                      </div>
                      <p v-if="q.explanation" class="text-gray-500 text-xs mt-1">解析：{{ q.explanation }}</p>
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
import { computed, ref } from 'vue'
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
