<template>
  <div :class="['flex items-start gap-3 animate-fade-in', isUser ? 'flex-row-reverse' : 'flex-row']">
    <!-- 头像 -->
    <div
      :class="[
        'w-8 h-8 rounded-full flex items-center justify-center text-sm flex-shrink-0 shadow-sm',
        isUser ? 'bg-gradient-to-br from-blue-500 to-blue-600 text-white' : 'bg-gradient-to-br from-purple-500 to-pink-500 text-white',
      ]"
    >
      {{ isUser ? '你' : 'AI' }}
    </div>

    <!-- 消息体 -->
    <div class="max-w-[75%] space-y-1">
      <!-- 如果是 agent 报告消息 -->
      <div v-if="isAgentMessage" class="flex items-center gap-2 mb-1">
        <span class="text-xs font-medium text-purple-500 bg-purple-50 px-2 py-0.5 rounded-full">{{ agentName }}</span>
      </div>

      <!-- 气泡 -->
      <div
        :class="[
          'rounded-2xl px-4 py-3 leading-relaxed',
          isUser
            ? 'bg-gradient-to-br from-blue-600 to-blue-700 text-white rounded-tr-md'
            : isAgentMessage
              ? 'bg-purple-50/80 border border-purple-100 text-gray-700 rounded-tl-md'
              : 'bg-white border border-gray-100 text-gray-800 shadow-sm rounded-tl-md',
        ]"
      >
        <!-- 用户消息：纯文本 -->
        <p v-if="isUser" class="text-sm whitespace-pre-wrap">{{ content }}</p>
        <!-- AI 消息：渲染 Markdown -->
        <div v-else class="chat-markdown text-sm" v-html="renderedContent"></div>
      </div>

      <!-- 资源卡片 -->
      <div v-if="!isUser && resources.length > 0" class="grid grid-cols-1 sm:grid-cols-2 gap-2 pt-1">
        <ResourceCard v-for="res in resources" :key="res.id" :resource="res" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import MarkdownIt from 'markdown-it'
import ResourceCard from './ResourceCard.vue'

const md = new MarkdownIt({
  html: false,
  linkify: true,
  breaks: true,
})

const props = defineProps({
  content: { type: String, required: true },
  isUser: { type: Boolean, default: false },
  resources: { type: Array, default: () => [] },
})

const agentRegex = /^\[(\w+_agent)\]\s*/

const isAgentMessage = computed(() => {
  if (props.isUser) return false
  return agentRegex.test(props.content)
})

const agentName = computed(() => {
  if (!isAgentMessage.value) return ''
  const match = props.content.match(agentRegex)
  const names = {
    resource_agent: '资源生成',
    profile_agent: '画像更新',
    path_agent: '路径规划',
    chat_agent: '学习助手',
  }
  return names[match[1]] || match[1]
})

const displayContent = computed(() => {
  if (!isAgentMessage.value) return props.content
  return props.content.replace(agentRegex, '')
})

const renderedContent = computed(() => {
  return md.render(displayContent.value)
})
</script>
