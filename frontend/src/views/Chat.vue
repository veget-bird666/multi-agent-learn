<template>
  <div class="max-w-4xl mx-auto px-6 py-8">
    <h2 class="text-2xl font-bold mb-6">对话式学习</h2>

    <!-- 消息列表 -->
    <div class="bg-white rounded-xl shadow-sm border border-gray-100 p-6 mb-6 h-[500px] overflow-y-auto space-y-4">
      <div v-if="chatStore.messages.length === 0" class="text-center text-gray-400 py-16">
        开始对话，系统将为你构建个性化学习方案
      </div>

      <div
        v-for="(msg, i) in chatStore.messages"
        :key="i"
        :class="['flex', msg.role === 'user' ? 'justify-end' : 'justify-start']"
      >
        <div
          :class="[
            'max-w-[80%] rounded-2xl px-4 py-3 text-sm leading-relaxed',
            msg.role === 'user'
              ? 'bg-blue-600 text-white rounded-br-md'
              : 'bg-gray-100 text-gray-800 rounded-bl-md',
          ]"
        >
          {{ msg.content }}
        </div>
      </div>

      <!-- 加载指示 -->
      <div v-if="chatStore.isStreaming" class="flex justify-start">
        <div class="bg-gray-100 rounded-2xl px-4 py-3 text-sm text-gray-500">
          <span class="animate-pulse">思考中...</span>
        </div>
      </div>
    </div>

    <!-- 输入框 -->
    <div class="flex gap-3">
      <input
        v-model="inputMessage"
        class="flex-1 border border-gray-200 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        placeholder="输入你想学的内容..."
        @keydown.enter="sendMessage"
        :disabled="chatStore.isStreaming"
      />
      <button
        @click="sendMessage"
        :disabled="chatStore.isStreaming || !inputMessage.trim()"
        class="bg-blue-600 text-white px-6 py-3 rounded-xl text-sm font-medium hover:bg-blue-700 disabled:opacity-50 transition"
      >
        发送
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useChatStore } from '../stores/chat'
import { sendChatMessage } from '../api'

const chatStore = useChatStore()
const inputMessage = ref('')

async function sendMessage() {
  const text = inputMessage.value.trim()
  if (!text || chatStore.isStreaming) return

  chatStore.addMessage('user', text)
  chatStore.isStreaming = true
  inputMessage.value = ''

  try {
    const data = await sendChatMessage(chatStore.studentId, text)
    chatStore.addMessage('assistant', data.response)
  } catch (e) {
    chatStore.addMessage('assistant', '请求失败: ' + e.message)
  } finally {
    chatStore.isStreaming = false
  }
}
</script>
