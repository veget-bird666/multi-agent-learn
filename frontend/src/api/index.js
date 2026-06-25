import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
})

/**
 * 发送聊天消息（走多智能体图，非流式）
 * @param {string} studentId
 * @param {string} message
 * @param {number|null} focusedStepOrder 当前聚焦的学习阶段（可选）
 * @param {number|null} currentPathId 当前选中的路径 ID（可选）
 * @param {boolean} includePathContext 是否将路径上下文发给模型
 * @returns {Promise<object>}
 */
export async function sendChatMessage(studentId, message, focusedStepOrder = null, currentPathId = null, includePathContext = true) {
  const body = { student_id: studentId, message, include_path_context: includePathContext }
  if (focusedStepOrder !== null && includePathContext) {
    body.focused_step_order = focusedStepOrder
  }
  if (currentPathId !== null && includePathContext) {
    body.current_path_id = currentPathId
  }
  const res = await fetch(`${api.defaults.baseURL}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
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

/**
 * 更新知识点熟练度（增量累加）
 * increment 建议值：easy=5, medium=8, hard=12
 */
export async function updateKpMastery(pathId, stepOrder, kpName, increment = 5) {
  const res = await fetch(`/api/learning-path/${pathId}/kp-mastery`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ step_order: stepOrder, knowledge_point: kpName, increment }),
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

/**
 * 提交试卷作答结果，批量更新知识点熟练度
 * @param {number} pathId
 * @param {number} stepOrder
 * @param {Array<{knowledge_point: string, is_correct: boolean, difficulty: string}>} results
 * @returns {Promise<object>} 更新后的路径
 */
export async function submitExam(pathId, stepOrder, results) {
  const res = await fetch(`/api/learning-path/${pathId}/exam-submit`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ step_order: stepOrder, results }),
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

/**
 * 更新某个阶段的知识点列表
 * @param {number} pathId
 * @param {number} stepOrder
 * @param {string[]} knowledgePoints 新的知识点列表
 * @returns {Promise<object>}
 */
export async function updateStepKnowledgePoints(pathId, stepOrder, knowledgePoints) {
  const res = await fetch(`/api/learning-path/${pathId}/knowledge-points`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ step_order: stepOrder, knowledge_points: knowledgePoints }),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || `HTTP ${res.status}`)
  }
  return res.json()
}

// ═══════════════════════════════════════════════════════════
//  虚拟学伴 API
// ═══════════════════════════════════════════════════════════

/** 学伴提问：根据学习路径掌握度生成一个问题 */
export async function buddyQuestion(studentId, pathId, focusedStepOrder = null) {
  const body = { student_id: studentId, path_id: pathId }
  if (focusedStepOrder !== null) body.focused_step_order = focusedStepOrder
  const res = await fetch(`/api/buddy/question`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  return res.json()
}

/** 学伴评估：提交答案，获取角色回复 + 学习笔记，自动更新掌握度 */
export async function buddyEvaluate(studentId, pathId, stepOrder, knowledgePoint, question, answer, focusedStepOrder = null) {
  const body = {
    student_id: studentId,
    path_id: pathId,
    step_order: stepOrder,
    knowledge_point: knowledgePoint,
    question,
    answer,
  }
  if (focusedStepOrder !== null) body.focused_step_order = focusedStepOrder
  const res = await fetch(`/api/buddy/evaluate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  return res.json()
}

/** 创建一条新资源（如导出学习笔记） */
export async function createResource(studentId, title, content, knowledgePoint = '', pathId = null, stepOrder = null) {
  const res = await fetch(`/api/resources`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      student_id: studentId,
      title,
      content,
      knowledge_point: knowledgePoint,
      path_id: pathId,
      step_order: stepOrder,
    }),
  })
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  return res.json()
}

// ═══════════════════════════════════════════════════════════
//  SSE 流式对话
// ═══════════════════════════════════════════════════════════

/**
 * 流式对话（SSE），通过 EventSource 连接 GET /chat
 *
 * @param {string} studentId
 * @param {string} message
 * @param {object} callbacks - { onToken, onStatus, onMetadata, onError }
 * @returns {EventSource} 返回 EventSource 实例，可调用 .close() 取消
 */
export function sendChatMessageStream(studentId, message, callbacks = {}, focusedStepOrder = null, currentPathId = null, includePathContext = true) {
  const params = new URLSearchParams({ student_id: studentId, message, include_path_context: includePathContext })
  if (focusedStepOrder !== null && includePathContext) {
    params.append('focused_step_order', focusedStepOrder)
  }
  if (currentPathId !== null && includePathContext) {
    params.append('current_path_id', currentPathId)
  }
  const url = `/api/chat?${params.toString()}`
  const es = new EventSource(url)

  es.addEventListener('status', (e) => {
    try {
      callbacks.onStatus?.(JSON.parse(e.data))
    } catch { /* ignore parse errors */ }
  })

  es.addEventListener('token', (e) => {
    try {
      const { token } = JSON.parse(e.data)
      if (token) callbacks.onToken?.(token)
    } catch { /* ignore */ }
  })

  es.addEventListener('metadata', (e) => {
    try {
      callbacks.onMetadata?.(JSON.parse(e.data))
    } catch { /* ignore */ }
    es.close()
  })

  es.addEventListener('error', () => {
    callbacks.onError?.(new Error('SSE connection failed'))
    es.close()
  })

  return es
}

export default api
