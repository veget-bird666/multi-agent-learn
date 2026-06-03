<template>
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
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  resource: { type: Object, required: true },
})

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

const typeStyle = computed(() => {
  const t = props.resource.type
  // 兼容 ResourceType enum 或字符串
  const key = typeof t === 'string' ? t : (t.value || 'document')
  return typeMap[key] || { icon: '📄', label: key, bg: 'bg-gray-50', badge: 'bg-gray-50 text-gray-600' }
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

function openResource() {
  // document 类型直接展示内容，其他类型（如 ppt）可能是链接
  const content = props.resource.content
  if (content && (content.startsWith('http://') || content.startsWith('https://'))) {
    window.open(content, '_blank')
  }
}
</script>
