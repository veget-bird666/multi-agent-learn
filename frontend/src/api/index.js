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

/** ── 学习路径（多路径支持）── */

/** 获取学生的所有学习路径 */
export async function listLearningPaths(studentId) {
  const res = await fetch(`/api/learning-path/list/${studentId}`)
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  return res.json()
}

/** 获取单条学习路径详情（按 id） */
export async function fetchLearningPath(pathId) {
  const res = await fetch(`/api/learning-path/${pathId}`)
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  return res.json()
}

/** 获取当前选中的学习路径 */
export async function fetchActiveLearningPath(studentId) {
  const res = await fetch(`/api/learning-path/active/${studentId}`)
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  return res.json()
}

/** 切换当前学习的路径 */
export async function setActivePath(studentId, pathId) {
  const res = await fetch(`/api/learning-path/active/${studentId}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ path_id: pathId }),
  })
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  return res.json()
}

/** 更新某个阶段的掌握度 */
export async function updateMastery(pathId, stepOrder, mastery) {
  const res = await fetch(`/api/learning-path/${pathId}/mastery?step_order=${stepOrder}&mastery=${mastery}`, {
    method: 'PUT',
  })
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  return res.json()
}

/** 批量更新掌握度 */
export async function batchUpdateMastery(pathId, updates) {
  const res = await fetch(`/api/learning-path/${pathId}/mastery/batch`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(updates),
  })
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  return res.json()
}

/** 删除一条学习路径 */
export async function deleteLearningPath(pathId) {
  const res = await fetch(`/api/learning-path/${pathId}`, {
    method: 'DELETE',
  })
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  return res.json()
}

export default api
