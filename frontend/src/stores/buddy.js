import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import {
  listLearningPaths,
  fetchLearningPath,
  buddyQuestion as apiBuddyQuestion,
  buddyEvaluate as apiBuddyEvaluate,
} from '../api'

export const useBuddyStore = defineStore('buddy', () => {
  // ── 消息列表 ──
  // 每条消息结构：
  // { type: 'question'|'answer'|'response'|'note'|'system',
  //   content: string,
  //   meta?: { kp, stepOrder, isCorrect, masteryBefore, masteryAfter, increment } }
  const messages = ref([])
  const isThinking = ref(false)
  const error = ref('')

  // ── 路径相关 ──
  const studentId = ref('student_001')
  const pathList = ref([])
  const currentPathId = ref(null)
  const currentPath = ref(null)
  const loadingPaths = ref(false)

  // ── 当前活跃的问题（等待用户回答） ──
  const activeQuestion = ref(null)
  // activeQuestion: { question, knowledge_point, step_order, difficulty, mastery_before }

  // ── 阶段聚焦 ──
  const focusedStepOrder = ref(null)

  /** 当前路径是否有知识点可练 */
  const hasKnowledgePoints = computed(() => {
    if (!currentPath.value?.steps) return false
    return currentPath.value.steps.some(s => s.knowledge_points?.length > 0)
  })

  /** 当前路径总体掌握度 */
  const overallMastery = computed(() => {
    return currentPath.value?.overall_mastery ?? 0
  })

  /** 是否处于"等待作答"状态 */
  const waitingForAnswer = computed(() => activeQuestion.value !== null)

  // ── 加载学习路径列表 ──
  async function loadPaths() {
    loadingPaths.value = true
    try {
      const data = await listLearningPaths(studentId.value)
      pathList.value = data.paths || []

      if (pathList.value.length > 0) {
        // 优先选已激活的路径
        const active = pathList.value.find(p => p.is_active) || pathList.value[0]
        await selectPath(active.id)
      } else {
        currentPath.value = null
        currentPathId.value = null
      }
    } catch (e) {
      console.error('[BuddyStore] 加载路径失败:', e)
      error.value = '加载学习路径失败'
    } finally {
      loadingPaths.value = false
    }
  }

  /** 切换选中的路径 */
  async function selectPath(pathId) {
    if (pathId === currentPathId.value) return
    currentPathId.value = pathId
    activeQuestion.value = null
    try {
      currentPath.value = await fetchLearningPath(pathId)
    } catch (e) {
      console.error('[BuddyStore] 加载路径详情失败:', e)
    }
  }

  // ── 请求学伴提问 ──
  async function requestQuestion() {
    if (!currentPathId.value) {
      error.value = '请先选择学习路径'
      return null
    }
    if (isThinking.value) return null

    isThinking.value = true
    error.value = ''
    // 清空当前问题
    activeQuestion.value = null

    try {
      const result = await apiBuddyQuestion(studentId.value, currentPathId.value, focusedStepOrder.value)

      activeQuestion.value = {
        question: result.question,
        knowledge_point: result.knowledge_point,
        step_order: result.step_order,
        difficulty: result.difficulty,
        mastery_before: result.mastery_before,
        is_follow_up: false,
      }

      // 添加学伴提问消息
      messages.value.push({
        type: 'question',
        content: result.question,
        meta: {
          kp: result.knowledge_point,
          stepOrder: result.step_order,
          difficulty: result.difficulty,
          masteryBefore: result.mastery_before,
        },
      })

      return result
    } catch (e) {
      console.error('[BuddyStore] 提问失败:', e)
      error.value = '学伴提问失败：' + e.message
      return null
    } finally {
      isThinking.value = false
    }
  }

  // ── 提交回答 ──
  async function submitAnswer(answer) {
    if (!answer.trim()) return null
    if (isThinking.value) return null

    isThinking.value = true
    error.value = ''

    // 优先取 activeQuestion，没有则从历史消息中找最后一个问题
    let q = activeQuestion.value
    if (!q) {
      const lastQuestion = [...messages.value].reverse().find(m => m.type === 'question')
      if (lastQuestion?.meta) {
        q = {
          question: lastQuestion.content,
          knowledge_point: lastQuestion.meta.kp || '',
          step_order: lastQuestion.meta.stepOrder || null,
          is_fallback: true,
        }
      }
    }
    if (!q) {
      isThinking.value = false
      return null
    }

    try {
      // 1. 添加用户回答消息
      messages.value.push({
        type: 'answer',
        content: answer,
        meta: { kp: q.knowledge_point, stepOrder: q.step_order },
      })

      // 2. 请求评估
      const result = await apiBuddyEvaluate(
        studentId.value,
        currentPathId.value,
        q.step_order,
        q.knowledge_point,
        q.question,
        answer,
        focusedStepOrder.value,
      )

      // 3. 添加学伴回复消息
      messages.value.push({
        type: 'response',
        content: result.response,
        meta: {
          kp: q.knowledge_point,
          stepOrder: q.step_order,
          isCorrect: result.is_correct,
          masteryBefore: result.mastery_before,
          masteryAfter: result.mastery_after,
          increment: result.increment,
          difficulty: result.difficulty,
        },
      })

      // 4. 添加学习笔记消息
      messages.value.push({
        type: 'note',
        content: result.learning_note,
        meta: {
          kp: q.knowledge_point,
          isCorrect: result.is_correct,
          masteryBefore: result.mastery_before,
          masteryAfter: result.mastery_after,
          increment: result.increment,
        },
      })

      // 5. 处理跟进问题（学伴自动追问）
      if (result.follow_up) {
        const f = result.follow_up
        activeQuestion.value = {
          question: f.question,
          knowledge_point: f.knowledge_point,
          step_order: f.step_order,
          difficulty: result.difficulty,
          mastery_before: f.mastery_before,
          is_follow_up: true,
        }
        // 自动追加一条学伴提问消息
        messages.value.push({
          type: 'question',
          content: f.question,
          meta: {
            kp: f.knowledge_point,
            stepOrder: f.step_order,
            difficulty: result.difficulty,
            masteryBefore: f.mastery_before,
            isFollowUp: true,
          },
        })
      } else {
        // 没有跟进问题 → 清空当前问题，用户可点击"换个知识点"
        activeQuestion.value = null
      }

      // 6. 刷新路径数据（获取最新掌握度）
      try {
        currentPath.value = await fetchLearningPath(currentPathId.value)
      } catch (_) {}

      return result
    } catch (e) {
      console.error('[BuddyStore] 评估失败:', e)
      error.value = '评估失败：' + e.message
      // 出错时不清除 activeQuestion，允许重试
      return null
    } finally {
      isThinking.value = false
    }
  }

  // ── 聚焦阶段 ──
  function focusStep(order) {
    focusedStepOrder.value = (focusedStepOrder.value === order) ? null : order
    // 切换聚焦时清空当前活跃问题，让用户重新提问
    activeQuestion.value = null
  }

  function clearFocus() {
    focusedStepOrder.value = null
    activeQuestion.value = null
  }

  // ── 重置会话 ──
  function resetSession() {
    messages.value = []
    activeQuestion.value = null
    error.value = ''
  }

  return {
    messages,
    isThinking,
    error,
    studentId,
    pathList,
    currentPathId,
    currentPath,
    loadingPaths,
    activeQuestion,
    focusedStepOrder,
    hasKnowledgePoints,
    overallMastery,
    waitingForAnswer,
    loadPaths,
    selectPath,
    requestQuestion,
    submitAnswer,
    focusStep,
    clearFocus,
    resetSession,
  }
})
