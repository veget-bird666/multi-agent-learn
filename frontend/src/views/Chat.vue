<template>
  <div class="max-w-5xl mx-auto px-4 py-6 h-[calc(100vh-3.5rem-4rem)] flex flex-col gap-4">
    <!-- 顶部信息栏 -->
    <div class="flex items-center justify-between">
      <h2 class="text-xl font-bold text-gray-900">对话式学习</h2>
      <div class="flex items-center gap-3">
        <router-link
          to="/learning-path"
          class="text-xs text-blue-600 hover:text-blue-700 bg-blue-50 px-3 py-1.5 rounded-lg transition-colors"
        >
          查看学习路径 →
        </router-link>
        <button
          v-if="chatStore.messages.length > 0"
          @click="clearConversation"
          class="text-xs text-gray-400 hover:text-red-500 transition-colors"
        >
          清空对话
        </button>
      </div>
    </div>

    <!-- 消息列表 -->
    <div
      ref="messageListRef"
      class="flex-1 bg-white/70 backdrop-blur-sm rounded-2xl border border-gray-200/60 p-4 md:p-6 overflow-y-auto scrollbar-thin space-y-5"
    >
      <!-- 空状态 -->
      <div v-if="chatStore.messages.length === 0" class="flex flex-col items-center justify-center h-full text-center">
        <div class="text-6xl mb-6">💡</div>
        <h3 class="text-lg font-semibold text-gray-700 mb-2">开始你的学习之旅</h3>
        <p class="text-sm text-gray-400 max-w-md leading-relaxed">
          告诉我你想学习什么内容，系统将为你构建个性化学习方案，<br>生成专属的学习资源
        </p>
        <div class="mt-8 grid grid-cols-1 sm:grid-cols-2 gap-3 w-full max-w-lg">
          <button
            v-for="suggestion in suggestions"
            :key="suggestion.text"
            @click="useSuggestion(suggestion.text)"
            class="text-left bg-white border border-gray-200 rounded-xl px-4 py-3 hover:border-blue-300 hover:shadow-sm transition-all text-sm text-gray-600 hover:text-gray-900"
          >
            <span class="mr-2">{{ suggestion.icon }}</span>
            {{ suggestion.text }}
          </button>
        </div>
      </div>

      <!-- 消息 -->
      <ChatMessage
        v-for="(msg, i) in chatStore.messages"
        :key="i"
        :content="msg.content"
        :is-user="msg.role === 'user'"
      />

      <!-- 加载指示 -->
      <div v-if="chatStore.isStreaming" class="flex items-start gap-3">
        <div class="w-8 h-8 rounded-full bg-gradient-to-br from-purple-500 to-pink-500 text-white flex items-center justify-center text-sm shadow-sm flex-shrink-0">
          AI
        </div>
        <div class="bg-white border border-gray-100 rounded-2xl rounded-tl-md px-5 py-4 shadow-sm">
          <div class="flex gap-1.5">
            <span class="typing-dot"></span>
            <span class="typing-dot"></span>
            <span class="typing-dot"></span>
          </div>
        </div>
      </div>
    </div>

    <!-- 输入区 -->
    <div class="bg-white rounded-2xl border border-gray-200/60 p-2 flex items-end gap-2 shadow-sm">
      <textarea
        ref="inputRef"
        v-model="inputMessage"
        class="flex-1 border-0 bg-transparent px-3 py-2 text-sm resize-none focus:outline-none focus:ring-0 placeholder:text-gray-400 max-h-32"
        placeholder="输入你想学的内容，按 Enter 发送..."
        rows="1"
        @keydown.enter.exact="sendMessage"
        @input="autoResize"
      />
      <button
        @click="sendMessage"
        :disabled="chatStore.isStreaming || !inputMessage.trim()"
        class="bg-gradient-to-r from-blue-600 to-purple-600 text-white px-5 py-2.5 rounded-xl text-sm font-medium hover:shadow-lg hover:shadow-blue-200 disabled:opacity-40 disabled:hover:shadow-none transition-all duration-200 flex-shrink-0"
      >
        <span class="hidden sm:inline">发送</span>
        <span class="sm:hidden">→</span>
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick, watch, onMounted } from 'vue'
import { useChatStore } from '../stores/chat'
import { sendChatMessage } from '../api'
import ChatMessage from '../components/ChatMessage.vue'

const chatStore = useChatStore()
const inputMessage = ref('')
const messageListRef = ref(null)
const inputRef = ref(null)

const suggestions = [
  { icon: '🅲', text: '我想学习C语言，从零基础开始' },
  { icon: '🐍', text: '帮我讲解Python装饰器的原理' },
  { icon: '📊', text: '能帮我生成一份数据结构PPT吗？' },
  { icon: '🧮', text: '我想练习高等数学的微积分题目' },
]

function autoResize() {
  const el = inputRef.value
  if (el) {
    el.style.height = 'auto'
    el.style.height = Math.min(el.scrollHeight, 128) + 'px'
  }
}

function scrollToBottom() {
  nextTick(() => {
    if (messageListRef.value) {
      messageListRef.value.scrollTop = messageListRef.value.scrollHeight
    }
  })
}

function useSuggestion(text) {
  inputMessage.value = text
  sendMessage()
}

async function sendMessage() {
  const text = inputMessage.value.trim()
  if (!text || chatStore.isStreaming) return

  chatStore.addMessage('user', text)
  chatStore.isStreaming = true
  inputMessage.value = ''
  autoResize()
  scrollToBottom()

  try {
    const data = await sendChatMessage(chatStore.studentId, text)
    chatStore.addMessage('assistant', data.response)
  } catch (e) {
    chatStore.addMessage('assistant', '抱歉，请求处理时出现错误：' + e.message)
  } finally {
    chatStore.isStreaming = false
    scrollToBottom()
  }
}

function clearConversation() {
  chatStore.clearMessages()
}

// 消息变化时自动滚动到底部
watch(() => chatStore.messages.length, scrollToBottom)

// 加载时聚焦输入框
onMounted(() => {
  inputRef.value?.focus()
})
</script>
