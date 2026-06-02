<template>
  <div v-if="profile" class="bg-white rounded-xl shadow-sm border border-gray-100 p-4">
    <h3 class="font-semibold text-sm mb-3">学习画像</h3>
    <div class="space-y-2 text-sm">
      <div v-for="(value, key) in profile" :key="key" class="flex justify-between">
        <span class="text-gray-500">{{ key }}</span>
        <span class="text-gray-800">{{ value || '待分析' }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  profile: { type: Object, default: null },
})
</script>
