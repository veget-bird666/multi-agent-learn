import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useChatStore = defineStore('chat', () => {
  const messages = ref([])
  const isStreaming = ref(false)
  const studentId = ref('student_001')

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

  return { messages, isStreaming, studentId, addMessage, appendToLastMessage, clearMessages }
})
