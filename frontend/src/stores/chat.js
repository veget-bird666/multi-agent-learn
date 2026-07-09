import { defineStore } from 'pinia'
import { ref } from 'vue'
import { sendChatMessage as apiSendMessage, sendChatMessageStream } from '../api'
import { useSessionsStore } from './sessions'

export const useChatStore = defineStore('chat', () => {
  const messages = ref([])
  const isStreaming = ref(false)
  const studentId = ref('student_001')
  const sessionId = ref(null)       // 当前会话 ID
  const streamStatus = ref('')      // 当前流式状态：如 "画像分析"、"路径规划" 等

  // ── 学习路径上下文 ──
  const currentPathId = ref(null)      // 当前选中的路径 ID
  const focusedStepOrder = ref(null)   // 聚焦的学习阶段序号
  const pathList = ref([])             // 所有路径的摘要列表
  const includePathContext = ref(true) // 是否将路径上下文发给模型

  // ── 功能开关 ──
  const enablePathPlanning = ref(true)       // 是否允许生成学习路径
  const enableResourceGeneration = ref(true)  // 是否允许生成资源

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
      focusedStepOrder.value = null
    }
  }

  /** 发送消息（非流式，保持向后兼容） */
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
        sessionId.value,
        enablePathPlanning.value,
        enableResourceGeneration.value,
      )
      addMessage('assistant', data.response)

      if (data.session_id) {
        sessionId.value = data.session_id
      }
      if (data.title) {
        const ss = useSessionsStore()
        const found = ss.sessions.find(item => item.session_id === (data.session_id || sessionId.value))
        if (found) found.title = data.title
      }
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

  /** 发送消息（流式），通过 SSE 逐字接收回复 */
  async function streamMessage(text) {
    if (!text.trim() || isStreaming.value) return null

    addMessage('user', text)
    isStreaming.value = true
    addMessage('assistant', '')  // 占位，后续逐字追加
    streamStatus.value = '连接中...'

    return new Promise((resolve) => {
      sendChatMessageStream(
        studentId.value,
        text,
        {
          onStatus(status) {
            if (status.label) {
              streamStatus.value = status.label
            }
          },
          onToken(token) {
            appendToLastMessage(token)
          },
          onMetadata(metadata) {
            // 同步会话 ID 和标题
            if (metadata.session_id) {
              sessionId.value = metadata.session_id
            }
            if (metadata.title) {
              const sessionsStore = useSessionsStore()
              const found = sessionsStore.sessions.find(item => item.session_id === (metadata.session_id || sessionId.value))
              if (found) found.title = metadata.title
            }
            if (metadata.current_path_id) {
              currentPathId.value = metadata.current_path_id
            }
            streamStatus.value = ''
            isStreaming.value = false
            resolve(metadata)
          },
          onError() {
            const last = messages.value[messages.value.length - 1]
            if (last && last.role === 'assistant' && !last.content) {
              last.content = '抱歉，请求处理时出现错误，请重试。'
            } else if (last && last.role === 'assistant') {
              last.content += '\n\n（连接中断，请重试）'
            }
            streamStatus.value = ''
            isStreaming.value = false
            resolve(null)
          },
        },
        focusedStepOrder.value,
        currentPathId.value,
        includePathContext.value,
        sessionId.value,
        enablePathPlanning.value,
        enableResourceGeneration.value,
      )
    })
  }

  /** 聚焦某个学习阶段 */
  function focusStep(stepOrder) {
    focusedStepOrder.value = stepOrder
  }

  /** 取消聚焦 */
  function clearFocus() {
    focusedStepOrder.value = null
  }

  /** 设置当前会话 ID */
  function setSessionId(id) {
    sessionId.value = id
  }

  /** 直接替换消息列表（用于切换会话时加载历史） */
  function loadMessages(msgs) {
    messages.value = msgs
  }

  return {
    messages,
    isStreaming,
    studentId,
    sessionId,
    streamStatus,
    currentPathId,
    focusedStepOrder,
    pathList,
    includePathContext,
    addMessage,
    appendToLastMessage,
    clearMessages,
    sendMessage,
    streamMessage,
    togglePathContext,
    focusStep,
    clearFocus,
    setSessionId,
    loadMessages,
    enablePathPlanning,
    enableResourceGeneration,
  }
})
