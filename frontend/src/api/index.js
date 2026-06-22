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

/** 获取学生全部资源 */
export async function fetchResources(studentId) {
  const res = await fetch(`/api/resources/${studentId}`)
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  return res.json()
}

/** 删除一条资源 */
export async function deleteResource(ormId) {
  const res = await fetch(`/api/resources/${ormId}`, { method: 'DELETE' })
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  return res.json()
}

/** ── 学习路径 ── */

/** 获取学习路径（含掌握度） */
export async function fetchLearningPath(studentId) {
  const res = await fetch(`/api/learning-path/${studentId}`)
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  return res.json()
}

/** 更新某个阶段的掌握度 */
export async function updateMastery(studentId, stepOrder, mastery) {
  const res = await fetch(`/api/learning-path/${studentId}/mastery?step_order=${stepOrder}&mastery=${mastery}`, {
    method: 'PUT',
  })
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  return res.json()
}

/** 批量更新掌握度 */
export async function batchUpdateMastery(studentId, updates) {
  const res = await fetch(`/api/learning-path/${studentId}/mastery/batch`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(updates),
  })
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  return res.json()
}

export default api
