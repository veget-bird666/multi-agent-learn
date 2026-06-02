import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
})

/**
 * 发送聊天消息（走多智能体图，非流式）
 * @param {string} studentId
 * @param {string} message
 * @returns {Promise<{response: string, profile: object|null}>}
 */
export async function sendChatMessage(studentId, message) {
  const res = await fetch(`${api.defaults.baseURL}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ student_id: studentId, message }),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || `HTTP ${res.status}`)
  }
  return res.json()
}

/** 获取学生画像 */
export function getProfile(studentId) {
  return api.get(`/profile/${studentId}`)
}

/** 获取学习路径 */
export function getLearningPath(studentId) {
  return api.get(`/learning-path/${studentId}`)
}

export default api
