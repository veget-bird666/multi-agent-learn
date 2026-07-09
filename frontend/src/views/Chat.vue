<template>
  <div class="h-[calc(100vh-3.5rem)] flex">
    <!-- 侧边栏：路径 / 对话切换 -->
    <div class="w-[280px] flex-shrink-0 h-full flex flex-col bg-dark-surface/60 backdrop-blur-sm border-r border-dark-border/60 overflow-hidden">
      <!-- 切换标签 -->
      <div class="flex-shrink-0 flex border-b border-dark-border/60">
        <button
          @click="sidebarTab = 'paths'"
          class="flex-1 text-xs py-3 font-medium transition-all duration-200 relative"
          :class="sidebarTab === 'paths'
            ? 'text-blue-300'
            : 'text-gray-500 hover:text-gray-300'"
        >
          🗺️ 学习路径
          <span
            v-if="sidebarTab === 'paths'"
            class="absolute bottom-0 left-1/4 right-1/4 h-0.5 bg-blue-500 rounded-full"
          ></span>
        </button>
        <button
          @click="sidebarTab = 'sessions'"
          class="flex-1 text-xs py-3 font-medium transition-all duration-200 relative"
          :class="sidebarTab === 'sessions'
            ? 'text-blue-300'
            : 'text-gray-500 hover:text-gray-300'"
        >
          💬 对话历史
          <span
            v-if="sidebarTab === 'sessions'"
            class="absolute bottom-0 left-1/4 right-1/4 h-0.5 bg-blue-500 rounded-full"
          ></span>
        </button>
      </div>

      <!-- 标签内容 -->
      <div class="flex-1 overflow-hidden">
        <PathSidebar v-show="sidebarTab === 'paths'" />
        <SessionSidebar v-show="sidebarTab === 'sessions'" />
      </div>
    </div>

    <!-- 主对话区 -->
    <div class="flex-1 flex flex-col min-w-0 bg-dark-bg">
      <!-- 顶部栏 -->
      <div class="flex-shrink-0 flex items-center justify-between px-6 py-3 border-b border-dark-border/60 bg-dark-surface/40 backdrop-blur-sm">
        <div class="flex items-center gap-3">
          <h2 class="text-sm font-semibold text-gray-300">对话式学习</h2>
          <!-- 功能开关 -->
          <div class="flex items-center gap-3 ml-2 pl-3 border-l border-dark-border/60">
            <label class="flex items-center gap-1.5 cursor-pointer" title="允许生成学习路径">
              <span class="text-[11px] text-gray-400 select-none">🗺️ 路径</span>
              <button
                @click="chatStore.enablePathPlanning = !chatStore.enablePathPlanning"
                class="relative w-8 h-4 rounded-full transition-all duration-200"
                :class="chatStore.enablePathPlanning ? 'bg-blue-500/60' : 'bg-gray-600/50'"
              >
                <span
                  class="absolute top-0.5 w-3 h-3 rounded-full bg-white shadow-sm transition-all duration-200"
                  :class="chatStore.enablePathPlanning ? 'left-[18px]' : 'left-[2px]'"
                ></span>
              </button>
            </label>
            <label class="flex items-center gap-1.5 cursor-pointer" title="允许生成学习资源（PPT/文档/试卷等）">
              <span class="text-[11px] text-gray-400 select-none">📦 资源</span>
              <button
                @click="chatStore.enableResourceGeneration = !chatStore.enableResourceGeneration"
                class="relative w-8 h-4 rounded-full transition-all duration-200"
                :class="chatStore.enableResourceGeneration ? 'bg-blue-500/60' : 'bg-gray-600/50'"
              >
                <span
                  class="absolute top-0.5 w-3 h-3 rounded-full bg-white shadow-sm transition-all duration-200"
                  :class="chatStore.enableResourceGeneration ? 'left-[18px]' : 'left-[2px]'"
                ></span>
              </button>
            </label>
          </div>
          <!-- 聚焦状态指示 -->
          <div
            v-if="chatStore.focusedStepOrder !== null && activePathName"
            class="flex items-center gap-1.5 text-[11px] bg-blue-500/20 text-blue-300 px-2.5 py-1 rounded-full"
          >
            <span>🎯</span>
            <span>聚焦：{{ activePathName }} 第{{ chatStore.focusedStepOrder }}阶段</span>
            <button
              @click="chatStore.clearFocus()"
              class="ml-1 text-blue-400 hover:text-blue-200 transition-colors"
              title="取消聚焦"
            >✕</button>
          </div>
        </div>
        <div class="flex items-center gap-2">
          <router-link
            to="/learning-path"
            class="text-[11px] text-blue-400 hover:text-blue-300 bg-blue-500/10 px-2.5 py-1.5 rounded-lg transition-colors"
          >
            路径看板 →
          </router-link>
          <button
            v-if="chatStore.messages.length > 0"
            @click="clearConversation"
            class="text-[11px] text-gray-500 hover:text-red-400 transition-colors"
          >
            清空对话
          </button>
        </div>
      </div>

      <!-- 消息列表 -->
      <div
        ref="messageListRef"
        class="flex-1 overflow-y-auto px-4 md:px-8 py-6 space-y-5 scrollbar-thin"
      >
        <!-- 空状态 -->
        <div v-if="chatStore.messages.length === 0" class="flex flex-col items-center justify-center h-full text-center">
          <h3 class="text-lg font-semibold text-gray-200 mb-2">开始你的学习之旅</h3>
          <p class="text-sm text-gray-500 max-w-md leading-relaxed mb-8">
            在左侧侧边栏选择一个学习阶段聚焦，<br>
            或直接输入你想学的内容
          </p>
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-3 w-full max-w-xl">
            <button
              v-for="suggestion in suggestions"
              :key="suggestion.text"
              @click="useSuggestion(suggestion.text)"
              class="text-left bg-dark-surface border border-dark-border rounded-xl px-4 py-3.5 hover:border-blue-500/40 hover:shadow-sm hover:shadow-blue-500/10 transition-all text-sm text-gray-400 hover:text-gray-200"
            >
              <span class="text-base mr-2">{{ suggestion.icon }}</span>
              {{ suggestion.text }}
            </button>
          </div>
        </div>

        <!-- 消息 -->
        <template v-for="(msg, i) in chatStore.messages" :key="i">
          <ChatMessage
            :content="msg.content"
            :is-user="msg.role === 'user'"
            :resources="msg.resources || []"
          />
        </template>

        <!-- 流式输出指示 -->
        <div v-if="chatStore.isStreaming" class="flex items-start gap-3">
          <img
            src="/ai_avatar.png"
            alt="AI"
            class="w-8 h-8 rounded-full flex-shrink-0 shadow-sm object-cover"
          />
          <div class="bg-dark-surface border border-dark-border rounded-2xl rounded-tl-md px-5 py-4 shadow-sm min-w-[160px]">
            <!-- 状态标签 -->
            <div v-if="chatStore.streamStatus" class="text-[11px] text-blue-400 mb-2 font-medium">
              {{ chatStore.streamStatus }}
            </div>
            <!-- 等待中显示三点动画，有内容后隐藏 -->
            <div v-if="!hasStreamingContent" class="flex gap-1.5">
              <span class="typing-dot"></span>
              <span class="typing-dot"></span>
              <span class="typing-dot"></span>
            </div>
          </div>
        </div>
      </div>

      <!-- 流式状态条 -->
      <div
        v-if="chatStore.isStreaming && chatStore.streamStatus"
        class="flex-shrink-0 px-4 md:px-8 pt-2 bg-dark-surface/40 backdrop-blur-sm"
      >
        <div class="flex items-center gap-2 px-4 py-1.5 bg-blue-500/10 border border-blue-500/20 rounded-xl">
          <div class="w-2 h-2 bg-blue-400 rounded-full animate-pulse"></div>
          <span class="text-[11px] text-blue-300">{{ chatStore.streamStatus }}</span>
        </div>
      </div>

      <!-- 输入区 -->
      <div class="flex-shrink-0 px-4 md:px-8 pb-4 pt-2 bg-dark-surface/40 backdrop-blur-sm border-t border-dark-border/60">
        <!-- 聚焦上下文提示 -->
        <div
          v-if="chatStore.focusedStepOrder !== null && currentFocusedStep"
          class="flex items-center gap-2 mb-2 px-4 py-2 bg-blue-500/10 border border-blue-500/20 rounded-xl text-xs text-blue-300"
        >
          <span>🎯</span>
          <span class="font-medium">聚焦阶段：{{ currentFocusedStep.stage_name }}</span>
          <span class="text-blue-400">|</span>
          <span class="text-blue-500">知识点：{{ kpPreview }}</span>
        </div>

        <div class="bg-dark-surface rounded-2xl border border-dark-border/80 p-2 flex items-end gap-2 shadow-sm focus-within:border-blue-500/50 focus-within:shadow-blue-500/10 focus-within:shadow-sm transition-all">
          <textarea
            ref="inputRef"
            v-model="inputMessage"
            class="flex-1 border-0 bg-transparent px-3 py-2 text-sm resize-none focus:outline-none focus:ring-0 text-gray-100 placeholder:text-gray-500 max-h-32"
            placeholder="输入你想学的内容，按 Enter 发送..."
            rows="1"
            @keydown.enter.exact="sendMessage"
            @input="autoResize"
          />
          <button
            @click="sendMessage"
            :disabled="chatStore.isStreaming || !inputMessage.trim()"
            class="bg-gradient-to-r from-blue-600 to-purple-600 text-white px-5 py-2.5 rounded-xl text-sm font-medium hover:shadow-lg hover:shadow-blue-500/20 disabled:opacity-40 disabled:hover:shadow-none transition-all duration-200 flex-shrink-0"
          >
            <span class="hidden sm:inline">发送</span>
            <span class="sm:hidden">→</span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, nextTick } from 'vue'
import { useChatStore } from '../stores/chat'
import { useSessionsStore } from '../stores/sessions'
import ChatMessage from '../components/ChatMessage.vue'
import PathSidebar from '../components/PathSidebar.vue'
import SessionSidebar from '../components/SessionSidebar.vue'

const chatStore = useChatStore()
const sessionsStore = useSessionsStore()

const sidebarTab = ref('paths')  // 'paths' | 'sessions'
const inputMessage = ref('')
const messageListRef = ref(null)
const inputRef = ref(null)

const suggestions = [
  { icon: '🅲', text: '我想学习C语言，从零基础开始' },
  { icon: '🐍', text: '帮我讲解Python装饰器的原理' },
  { icon: '📊', text: '能帮我生成一份数据结构PPT吗？' },
  { icon: '🧮', text: '我想练习高等数学的微积分题目' },
]

/** 当前聚焦阶段的名称 */
const activePathName = computed(() => {
  const path = chatStore.pathList.find(p => p.id === chatStore.currentPathId)
  return path?.title || ''
})

/** 流式输出是否已有内容（有内容则隐藏加载动画） */
const hasStreamingContent = computed(() => {
  if (!chatStore.isStreaming) return false
  const msgs = chatStore.messages
  const last = msgs[msgs.length - 1]
  return last && last.role === 'assistant' && last.content.length > 0
})

/** 当前聚焦阶段的详细信息 */
const currentFocusedStep = computed(() => {
  if (chatStore.focusedStepOrder === null) return null
  const path = chatStore.pathList.find(p => p.id === chatStore.currentPathId)
  if (!path) return null
  return path.steps?.find(s => s.order === chatStore.focusedStepOrder) || null
})

/** 知识点预览 */
const kpPreview = computed(() => {
  if (!currentFocusedStep.value) return ''
  const kps = currentFocusedStep.value.knowledge_points || []
  return kps.join('、')
})

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

  inputMessage.value = ''
  autoResize()

  await chatStore.streamMessage(text)
  scrollToBottom()
}

function clearConversation() {
  chatStore.clearMessages()
}

// 消息数量变化时滚动到底部
watch(() => chatStore.messages.length, scrollToBottom)

// 流式输出时持续滚动
watch(() => {
  const msgs = chatStore.messages
  return msgs[msgs.length - 1]?.content
}, () => {
  if (chatStore.isStreaming) {
    nextTick(scrollToBottom)
  }
})

onMounted(() => {
  inputRef.value?.focus()
  // 加载会话列表（SessionSidebar 的 onMounted 也会触发，但 loading 守卫防重）
  sessionsStore.loadSessions(chatStore.studentId)
  // 无当前会话时自动创建一个
  if (!chatStore.sessionId) {
    sessionsStore.createSession()
  }
})
</script>

<style scoped>
/* 滚动条 */
.scrollbar-thin::-webkit-scrollbar {
  width: 5px;
}
.scrollbar-thin::-webkit-scrollbar-track {
  background: transparent;
}
.scrollbar-thin::-webkit-scrollbar-thumb {
  background: #e2e8f0;
  border-radius: 4px;
}

.typing-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #94a3b8;
  animation: typing-bounce 1.4s infinite both;
}
.typing-dot:nth-child(2) { animation-delay: 0.2s; }
.typing-dot:nth-child(3) { animation-delay: 0.4s; }
@keyframes typing-bounce {
  0%, 80%, 100% { transform: scale(0.6); opacity: 0.4; }
  40% { transform: scale(1); opacity: 1; }
}
</style>
