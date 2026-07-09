import { defineStore } from 'pinia'
import { ref } from 'vue'
import { listSessions as apiListSessions, deleteSession as apiDeleteSession, getSessionMessages, updateSessionTitle as apiUpdateTitle } from '../api'
import { useChatStore } from './chat'

export const useSessionsStore = defineStore('sessions', () => {
  const sessions = ref([])
  const loading = ref(false)

  /** 从后端加载会话列表（loading 守卫防重复请求） */
  async function loadSessions(studentId) {
    if (loading.value) return
    loading.value = true
    try {
      const data = await apiListSessions(studentId)
      sessions.value = data.sessions || []
    } catch (e) {
      console.error('加载会话列表失败:', e)
    } finally {
      loading.value = false
    }
  }

  /** 强制刷新（忽略 loading 守卫） */
  async function refreshSessions(studentId) {
    loading.value = true
    try {
      const data = await apiListSessions(studentId)
      sessions.value = data.sessions || []
    } catch (e) {
      console.error('刷新会话列表失败:', e)
    } finally {
      loading.value = false
    }
  }

  /** 创建新会话（生成 UUID，切到新会话并清空消息） */
  function createSession() {
    const chatStore = useChatStore()
    const newId = crypto.randomUUID ? crypto.randomUUID() : 'session_' + Date.now()
    chatStore.setSessionId(newId)
    chatStore.loadMessages([])
    // 本地插入，避免等待后端刷新
    sessions.value.unshift({
      session_id: newId,
      title: '新对话',
      updated_at: new Date().toISOString(),
    })
    return newId
  }

  /** 切换到指定会话：加载历史消息 */
  async function switchSession(sessionId) {
    const chatStore = useChatStore()
    chatStore.setSessionId(sessionId)
    chatStore.loadMessages([])   // 先清空，显示 loading
    try {
      const data = await getSessionMessages(sessionId)
      const msgs = (data.messages || []).map(m => ({
        role: m.role,
        content: m.content,
        resources: [],
      }))
      chatStore.loadMessages(msgs)
    } catch (e) {
      console.error('加载会话消息失败:', e)
    }
  }

  /** 删除会话 */
  async function deleteSession(sessionId) {
    try {
      await apiDeleteSession(sessionId)
      sessions.value = sessions.value.filter(s => s.session_id !== sessionId)
      const chatStore = useChatStore()
      if (chatStore.sessionId === sessionId) {
        // 删了当前会话 → 切到新会话
        createSession()
      }
    } catch (e) {
      console.error('删除会话失败:', e)
    }
  }

  /** 更新会话标题（本地 + 后端） */
  async function updateTitle(sessionId, newTitle) {
    // 立即更新本地
    const s = sessions.value.find(s => s.session_id === sessionId)
    if (s) s.title = newTitle
    try {
      await apiUpdateTitle(sessionId, newTitle)
    } catch (e) {
      console.error('更新标题失败:', e)
    }
  }

  return {
    sessions,
    loading,
    loadSessions,
    refreshSessions,
    createSession,
    switchSession,
    deleteSession,
    updateTitle,
  }
})
