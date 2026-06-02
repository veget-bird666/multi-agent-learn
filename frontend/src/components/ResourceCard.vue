<template>
  <div class="bg-white rounded-xl shadow-sm border border-gray-100 p-4 hover:shadow-md transition">
    <div class="flex items-center gap-2 mb-2">
      <span class="text-lg">{{ typeIcon }}</span>
      <span class="text-xs text-gray-400 uppercase">{{ resource.type }}</span>
    </div>
    <h4 class="font-medium text-sm mb-1">{{ resource.title }}</h4>
    <p class="text-xs text-gray-500">{{ resource.knowledge_point }}</p>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  resource: { type: Object, required: true },
})

const typeIcon = computed(() => {
  const icons = {
    document: '📄',
    mindmap: '🧠',
    exercise: '✏️',
    video: '🎬',
    code_example: '💻',
    extra_reading: '📚',
  }
  return icons[props.resource.type] || '📄'
})
</script>
