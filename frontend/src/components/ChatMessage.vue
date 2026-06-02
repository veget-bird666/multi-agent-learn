<template>
  <div :class="['flex', isUser ? 'justify-end' : 'justify-start']">
    <div
      :class="[
        'max-w-[80%] rounded-2xl px-4 py-3 text-sm leading-relaxed',
        isUser
          ? 'bg-blue-600 text-white rounded-br-md'
          : 'bg-gray-100 text-gray-800 rounded-bl-md',
      ]"
    >
      <slot />
    </div>
  </div>
</template>

<script setup>
defineProps({
  isUser: { type: Boolean, default: false },
})
</script>
