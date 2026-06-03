<template>
  <div v-if="profile" class="bg-white rounded-xl border border-gray-100 p-5 animate-fade-in">
    <div class="flex items-center gap-2 mb-4">
      <span class="text-lg">🎯</span>
      <h3 class="font-semibold text-gray-900">学习画像</h3>
    </div>
    <div class="space-y-3">
      <div
        v-for="item in profileFields"
        :key="item.key"
        class="flex items-start gap-3"
      >
        <span class="text-base flex-shrink-0 mt-0.5">{{ item.icon }}</span>
        <div class="flex-1 min-w-0">
          <div class="text-xs text-gray-400 mb-0.5">{{ item.label }}</div>
          <div v-if="getValue(item.key)" class="text-sm text-gray-700">
            <span
              v-for="(tag, ti) in formatValue(item.key)"
              :key="ti"
              class="inline-block bg-gray-50 text-gray-600 text-xs px-2 py-0.5 rounded-md mr-1 mb-1"
            >
              {{ tag }}
            </span>
          </div>
          <div v-else class="text-sm text-gray-300 italic">待分析</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  profile: { type: Object, default: null },
})

const profileFields = [
  { key: 'knowledge_base', label: '知识基础', icon: '📖' },
  { key: 'cognitive_style', label: '认知风格', icon: '🧠' },
  { key: 'learning_pace', label: '学习节奏', icon: '⏱️' },
  { key: 'interest_areas', label: '兴趣领域', icon: '⭐' },
  { key: 'goal', label: '学习目标', icon: '🎯' },
  { key: 'common_mistakes', label: '易错点', icon: '⚠️' },
]

function getValue(key) {
  if (!props.profile) return null
  const v = props.profile[key]
  if (!v) return null
  if (Array.isArray(v) && v.length === 0) return null
  if (typeof v === 'string' && !v.trim()) return null
  return v
}

function formatValue(key) {
  const v = getValue(key)
  if (!v) return []
  if (Array.isArray(v)) return v
  // 对于长字符串（如认知风格的描述），截短
  if (v.length > 30) return [v.slice(0, 30) + '...']
  return [v]
}
</script>
