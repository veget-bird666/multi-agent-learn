import { defineStore } from 'pinia'
import { ref } from 'vue'
import { sendChatMessage as apiSendMessage } from '../api'

export const useChatStore = defineStore('chat', () => {
  const messages = ref([])
  const isStreaming = ref(false)
  const studentId = ref('student_001')

  // ── 学习路径上下文 ──
  const currentPathId = ref(null)      // 当前选中的路径 ID
  const focusedStepOrder = ref(null)   // 聚焦的学习阶段序号
  const pathList = ref([])             // 所有路径的摘要列表
  const includePathContext = ref(true) // 是否将路径上下文发给模型

  function addMessage(role, content, resources = []) {
    messages.value.push({ role, content, resources })
  }

  function appendToLastMessage(token) {
    const last = messages.value[messages.value.length - 1]
    if (last && last.role === 'assistant') {
      last.content += token
    }
  }

  function clearMessages() {
    messages.value = []
  }

  /** 切换路径上下文开关 */
  function togglePathContext() {
    includePathContext.value = !includePathContext.value
    if (!includePathContext.value) {
      // 关闭开关时自动取消聚焦
      focusedStepOrder.value = null
    }
  }

  /** 发送消息，携带当前路径上下文 */
  async function sendMessage(text) {
    if (!text.trim() || isStreaming.value) return null

    addMessage('user', text)
    isStreaming.value = true

    try {
      const data = await apiSendMessage(
        studentId.value,
        text,
        focusedStepOrder.value,
        currentPathId.value,
        includePathContext.value,
      )
      addMessage('assistant', data.response)

      // 更新路径上下文（如果后端返回了新路径）
      if (data.current_path_id) {
        currentPathId.value = data.current_path_id
      }

      return data
    } catch (e) {
      addMessage('assistant', '抱歉，请求处理时出现错误：' + e.message)
      return null
    } finally {
      isStreaming.value = false
    }
  }

  /** 聚焦某个学习阶段 */
  function focusStep(stepOrder) {
    focusedStepOrder.value = stepOrder
  }

  /** 取消聚焦 */
  function clearFocus() {
    focusedStepOrder.value = null
  }

  return {
    messages,
    isStreaming,
    studentId,
    currentPathId,
    focusedStepOrder,
    pathList,
    includePathContext,
    addMessage,
    appendToLastMessage,
    clearMessages,
    sendMessage,
    togglePathContext,
    focusStep,
    clearFocus,
  }
})
