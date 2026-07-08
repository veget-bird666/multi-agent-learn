<template>
  <div class="flex-1 flex flex-col overflow-hidden">
    <!-- 标题 + 新建按钮 -->
    <div class="px-5 pt-5 pb-3 border-b border-dark-border/60">
      <div class="flex items-center justify-between mb-2">
        <h3 class="text-sm font-semibold text-gray-300">对话历史</h3>
        <div class="flex items-center gap-1">
          <button
            @click="handleRefresh"
            :disabled="sessionsStore.loading"
            class="text-xs text-blue-400 hover:text-blue-300 transition-colors disabled:opacity-40 px-1.5 py-1"
          >
            ↻
          </button>
          <button
            @click="handleNew"
            class="text-[11px] bg-blue-500/20 text-blue-300 hover:bg-blue-500/30 px-3 py-1.5 rounded-lg transition-colors font-medium"
          >
            ＋ 新建
          </button>
        </div>
      </div>
      <p class="text-[11px] text-gray-500">切换对话可继续之前的交流</p>
    </div>

    <!-- 加载中 -->
    <div v-if="sessionsStore.loading" class="flex-1 flex items-center justify-center">
      <div class="w-5 h-5 border-2 border-blue-400 border-t-transparent rounded-full animate-spin"></div>
    </div>

    <!-- 空状态 -->
    <div v-else-if="sessionsStore.sessions.length === 0" class="flex-1 flex flex-col items-center justify-center px-5 text-center">
      <div class="text-2xl mb-2 opacity-20">💬</div>
      <p class="text-xs text-gray-500">暂无对话记录</p>
      <p class="text-[11px] text-gray-600 mt-1">新建对话开始学习</p>
    </div>

    <!-- 会话列表 -->
    <div v-else class="flex-1 overflow-y-auto px-3 pb-4 space-y-1 scrollbar-thin">
      <div
        v-for="s in sessionsStore.sessions"
        :key="s.session_id"
        @click="handleSwitch(s.session_id)"
        class="group flex items-center gap-3 px-3 py-2.5 rounded-xl cursor-pointer transition-all duration-200"
        :class="isActive(s.session_id)
          ? 'bg-blue-500/15 border border-blue-500/25'
          : 'hover:bg-dark-surface-hover border border-transparent'"
      >
        <!-- 会话信息 -->
        <div class="flex-1 min-w-0">
          <p class="text-xs font-medium truncate"
            :class="isActive(s.session_id) ? 'text-blue-200' : 'text-gray-300'"
          >
            {{ s.title }}
          </p>
          <p class="text-[10px] text-gray-500 mt-0.5">{{ formatTime(s.updated_at) }}</p>
        </div>

        <!-- 删除按钮 -->
        <button
          @click.stop="handleDelete(s.session_id)"
          class="opacity-0 group-hover:opacity-100 text-gray-500 hover:text-red-400 transition-all text-[13px] px-1"
          title="删除对话"
        >
          ✕
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useChatStore } from '../stores/chat'
import { useSessionsStore } from '../stores/sessions'

const chatStore = useChatStore()
const sessionsStore = useSessionsStore()

function isActive(sessionId) {
  return chatStore.sessionId === sessionId
}

function formatTime(isoStr) {
  if (!isoStr) return ''
  try {
    const d = new Date(isoStr)
    const now = new Date()
    const diffDays = Math.floor((now - d) / (1000 * 60 * 60 * 24))
    if (diffDays === 0) {
      return d.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
    }
    if (diffDays === 1) return '昨天'
    if (diffDays < 7) return `${diffDays}天前`
    return d.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })
  } catch {
    return isoStr
  }
}

function handleNew() {
  sessionsStore.createSession()
}

function handleRefresh() {
  sessionsStore.refreshSessions(chatStore.studentId)
}

async function handleSwitch(sessionId) {
  if (isActive(sessionId)) return
  await sessionsStore.switchSession(sessionId)
}

async function handleDelete(sessionId) {
  await sessionsStore.deleteSession(sessionId)
}

onMounted(() => {
  // 在 PathSidebar 中也调用了这个，这里防止重复加载
  if (chatStore.studentId && sessionsStore.sessions.length === 0) {
    sessionsStore.loadSessions(chatStore.studentId)
  }
})
</script>

<style scoped>
.scrollbar-thin::-webkit-scrollbar {
  width: 4px;
}
.scrollbar-thin::-webkit-scrollbar-track {
  background: transparent;
}
.scrollbar-thin::-webkit-scrollbar-thumb {
  background: #e2e8f0;
  border-radius: 4px;
}
</style>
