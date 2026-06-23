<template>
  <div class="h-full">
    <div class="h-[calc(100vh-3.5rem)] flex flex-col max-w-5xl mx-auto px-4 md:px-6">
      <!-- ═══ 顶部栏：路径选择 + 提问按钮 ═══ -->
      <div class="flex-shrink-0 flex flex-wrap items-center gap-3 py-4 border-b border-dark-border/60">
      <!-- 路径选择 -->
      <div class="flex items-center gap-2">
        <span class="text-xs text-gray-500 flex-shrink-0">学习路径</span>
        <select
          :value="buddyStore.currentPathId"
          @change="onPathChange"
          :disabled="buddyStore.loadingPaths || buddyStore.waitingForAnswer"
          class="text-xs bg-dark-surface border border-dark-border rounded-lg px-3 py-2 text-gray-300 focus:outline-none focus:border-blue-500 min-w-[180px] appearance-none cursor-pointer disabled:opacity-40"
        >
          <option value="" disabled>选择一条路径</option>
          <option v-for="p in buddyStore.pathList" :key="p.id" :value="p.id">
            {{ p.title }}
          </option>
        </select>
      </div>

      <!-- 总体掌握度 -->
      <div
        v-if="buddyStore.currentPath"
        class="flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-full"
        :class="masteryBadgeClass(buddyStore.overallMastery)"
      >
        <span>掌握度 {{ Math.round(buddyStore.overallMastery) }}%</span>
      </div>

      <!-- 导出学习笔记 -->
      <button
        v-if="buddyStore.messages.some(m => m.type === 'note')"
        @click="handleExportNotes"
        :disabled="exportLoading"
        class="flex items-center gap-1.5 text-xs font-medium px-3 py-2 rounded-xl transition-all disabled:opacity-40 disabled:cursor-not-allowed bg-dark-surface border border-dark-border text-gray-400 hover:text-gray-200 hover:border-gray-500"
      >
        <span v-if="exportLoading" class="w-3.5 h-3.5 border-2 border-gray-500 border-t-gray-300 rounded-full animate-spin"></span>
        <span v-else>📥</span>
        导出笔记
      </button>

      <!-- 学伴提问 / 换个知识点 按钮（始终可点） -->
      <button
        @click="handleRequestQuestion"
        :disabled="!buddyStore.currentPathId || !buddyStore.hasKnowledgePoints || buddyStore.isThinking"
        class="ml-auto flex items-center gap-1.5 text-xs font-medium px-4 py-2 rounded-xl transition-all disabled:opacity-40 disabled:cursor-not-allowed"
        :class="buddyStore.isThinking
          ? 'bg-dark-surface border border-dark-border text-gray-500'
          : 'bg-gradient-to-r from-blue-600 to-purple-600 text-white hover:shadow-lg hover:shadow-blue-500/20'"
      >
        <span v-if="buddyStore.isThinking" class="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></span>
        <span v-else-if="buddyStore.messages.length > 0">🔄 换个知识点</span>
        <span v-else>🤖 学伴提问</span>
      </button>
    </div>

    <!-- ═══ 阶段聚焦条 ═══ -->
    <div
      v-if="buddyStore.currentPath?.steps?.length"
      class="flex-shrink-0 flex items-center gap-1.5 py-2.5 overflow-x-auto scrollbar-thin border-b border-dark-border/40"
    >
      <span class="text-[10px] text-gray-500 flex-shrink-0 mr-1">聚焦：</span>
      <button
        v-for="step in buddyStore.currentPath.steps"
        :key="step.order"
        @click="buddyStore.focusStep(step.order)"
        @mouseenter="showTooltip(step, $event)"
        @mouseleave="hideTooltip"
        class="flex-shrink-0 flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[11px] font-medium transition-all border"
        :class="stagePillClass(step)"
      >
        <span class="w-2 h-2 rounded-full" :class="stageDotClass(step.mastery)"></span>
        <span>{{ step.stage_name }}</span>
        <span class="opacity-60 font-mono">{{ Math.round(step.mastery) }}%</span>
      </button>
      <button
        v-if="buddyStore.focusedStepOrder !== null"
        @click="buddyStore.clearFocus()"
        class="flex-shrink-0 text-[10px] text-gray-500 hover:text-gray-300 px-2 py-1 rounded transition-colors"
      >
        取消聚焦 ✕
      </button>
    </div>

    <!-- ═══ 消息区 ═══ -->
    <div ref="messageListRef" class="flex-1 overflow-y-auto py-6 space-y-5 scrollbar-thin">
      <!-- 空状态 -->
      <div v-if="buddyStore.messages.length === 0" class="flex flex-col items-center justify-center h-full text-center px-4">
        <div class="text-5xl mb-4 opacity-60">🤖</div>
        <h3 class="text-base font-semibold text-gray-300 mb-2">虚拟学伴 — 小问</h3>
        <p class="text-sm text-gray-500 max-w-md leading-relaxed mb-2">
          我是你的学习伙伴，水平比你略低。
          通过"教你"来巩固你的理解吧！
        </p>
        <p class="text-xs text-gray-600 mb-6">
          选择一条学习路径，点击「学伴提问」开始
        </p>
        <!-- 无路径提示 -->
        <div
          v-if="buddyStore.pathList.length === 0"
          class="bg-dark-surface rounded-xl border border-dark-border px-5 py-4 text-sm text-gray-500"
        >
          暂无学习路径，请先在主对话中生成一条学习路径
          <router-link to="/chat" class="text-blue-400 hover:text-blue-300 ml-1">去生成 →</router-link>
        </div>
      </div>

      <!-- 消息列表 -->
      <template v-for="(msg, i) in buddyStore.messages" :key="i">
        <!-- 学伴提问 -->
        <div v-if="msg.type === 'question'" class="flex items-start gap-3">
          <div class="w-9 h-9 rounded-full bg-gradient-to-br from-blue-500 to-cyan-500 text-white flex items-center justify-center text-sm shadow-sm flex-shrink-0">
            问
          </div>
          <div class="flex-1 min-w-0">
            <div class="flex items-center gap-2 mb-1">
              <span class="text-xs font-medium text-blue-300">小问</span>
              <span v-if="msg.meta" class="text-[10px] text-gray-500 bg-dark-surface-alt px-1.5 py-0.5 rounded">
                {{ msg.meta.kp }} · 掌握度 {{ Math.round(msg.meta.masteryBefore) }}%
              </span>
            </div>
            <div class="bg-blue-500/10 border border-blue-500/20 rounded-2xl rounded-tl-md px-5 py-3.5">
              <p class="text-sm text-gray-200 leading-relaxed">{{ msg.content }}</p>
            </div>
          </div>
        </div>

        <!-- 用户回答 -->
        <div v-else-if="msg.type === 'answer'" class="flex items-start gap-3 flex-row-reverse">
          <div class="w-9 h-9 rounded-full bg-gradient-to-br from-gray-500 to-gray-600 text-white flex items-center justify-center text-sm shadow-sm flex-shrink-0">
            我
          </div>
          <div class="flex-1 min-w-0 max-w-[75%]">
            <div class="text-right mb-1">
              <span class="text-xs text-gray-500">我</span>
            </div>
            <div class="bg-dark-surface border border-dark-border rounded-2xl rounded-tr-md px-5 py-3.5">
              <p class="text-sm text-gray-300 leading-relaxed">{{ msg.content }}</p>
            </div>
          </div>
        </div>

        <!-- 学伴角色回复 -->
        <div v-else-if="msg.type === 'response'" class="flex items-start gap-3">
          <div class="w-9 h-9 rounded-full bg-gradient-to-br from-blue-500 to-cyan-500 text-white flex items-center justify-center text-sm shadow-sm flex-shrink-0">
            问
          </div>
          <div class="flex-1 min-w-0">
            <div class="flex items-center gap-2 mb-1">
              <span class="text-xs font-medium text-blue-300">小问</span>
              <span
                v-if="msg.meta"
                class="text-[10px] px-1.5 py-0.5 rounded"
                :class="msg.meta.isCorrect ? 'bg-green-500/10 text-green-400' : 'bg-red-500/10 text-red-400'"
              >
                {{ msg.meta.isCorrect ? '✅ 答对了' : '❌ 未答对' }}
              </span>
            </div>
            <div class="bg-blue-500/5 border border-blue-500/10 rounded-2xl rounded-tl-md px-5 py-3.5">
              <p class="text-sm text-gray-300 italic leading-relaxed">{{ msg.content }}</p>
            </div>
          </div>
        </div>

        <!-- 学习笔记 -->
        <div v-else-if="msg.type === 'note'" class="flex justify-center">
          <div class="w-full max-w-2xl bg-dark-surface-alt/80 border border-dark-border rounded-xl overflow-hidden">
            <!-- 笔记头 -->
            <div
              class="flex items-center justify-between px-4 py-2.5 cursor-pointer select-none"
              :class="noteHeaderClass(msg.meta?.isCorrect)"
              @click="toggleNote(i)"
            >
              <div class="flex items-center gap-2">
                <span class="text-sm">📌</span>
                <span class="text-xs font-medium" :class="noteHeaderClass(msg.meta?.isCorrect)">
                  学习笔记 · {{ msg.meta?.kp || '知识点' }}
                </span>
              </div>
              <div class="flex items-center gap-3">
                <!-- 掌握度变化 -->
                <span
                  v-if="msg.meta"
                  class="text-[10px] font-mono"
                  :class="msg.meta.isCorrect ? 'text-green-400' : 'text-gray-500'"
                >
                  {{ Math.round(msg.meta.masteryBefore) }}%
                  <template v-if="msg.meta.isCorrect">
                    → {{ Math.round(msg.meta.masteryAfter) }}% (+{{ msg.meta.increment }})
                  </template>
                </span>
                <span class="text-gray-500 text-xs">{{ expandedNotes[i] ? '收起 ▲' : '展开 ▼' }}</span>
              </div>
            </div>
            <!-- 笔记内容 -->
            <div v-if="expandedNotes[i]" class="px-4 pb-4">
              <div
                v-if="msg.meta && !msg.meta.isCorrect"
                class="mb-3 flex items-center gap-2 text-xs text-red-400 bg-red-500/10 px-3 py-2 rounded-lg"
              >
                <span>💡</span>
                <span>答错了不要紧，看看下面的正确知识点巩固一下吧！</span>
              </div>
              <div class="text-xs text-gray-400 leading-relaxed learning-note" v-html="renderMarkdown(msg.content)"></div>
            </div>
          </div>
        </div>

        <!-- 系统消息 -->
        <div v-else-if="msg.type === 'system'" class="text-center">
          <span class="text-xs text-gray-600 bg-dark-surface-alt px-3 py-1 rounded-full">{{ msg.content }}</span>
        </div>
      </template>

      <!-- 加载指示 -->
      <div v-if="buddyStore.isThinking" class="flex items-start gap-3">
        <div class="w-9 h-9 rounded-full bg-gradient-to-br from-blue-500 to-cyan-500 text-white flex items-center justify-center text-sm shadow-sm flex-shrink-0">
          问
        </div>
        <div class="bg-dark-surface border border-dark-border rounded-2xl rounded-tl-md px-5 py-4">
          <div class="flex gap-1.5">
            <span class="typing-dot"></span>
            <span class="typing-dot"></span>
            <span class="typing-dot"></span>
          </div>
        </div>
      </div>
    </div>

    <!-- ═══ 输入区 ═══ -->
    <div class="flex-shrink-0 pb-4 pt-2">
      <!-- 等待作答提示 -->
      <div
        v-if="buddyStore.waitingForAnswer && activeQuestionText"
        class="flex items-center gap-2 mb-2 px-4 py-2 bg-blue-500/10 border border-blue-500/20 rounded-xl"
      >
        <span class="text-xs text-blue-300">💬 当前问题：</span>
        <span class="text-xs text-gray-400 truncate flex-1">{{ activeQuestionText }}</span>
      </div>

      <div class="flex items-end gap-2 bg-dark-surface rounded-2xl border border-dark-border/80 p-2 shadow-sm focus-within:border-blue-500/50 transition-all">
        <textarea
          ref="inputRef"
          v-model="inputMessage"
          class="flex-1 border-0 bg-transparent px-3 py-2 text-sm resize-none focus:outline-none focus:ring-0 text-gray-100 placeholder:text-gray-500 max-h-32"
          :placeholder="inputPlaceholder"
          rows="1"
          :disabled="!buddyStore.currentPathId || buddyStore.isThinking"
          @keydown.enter.exact="handleSubmit"
          @input="autoResize"
        />
        <button
          @click="handleSubmit"
          :disabled="!canSubmit"
          class="bg-gradient-to-r from-blue-600 to-purple-600 text-white px-5 py-2.5 rounded-xl text-sm font-medium hover:shadow-lg hover:shadow-blue-500/20 disabled:opacity-40 disabled:hover:shadow-none transition-all duration-200 flex-shrink-0"
        >
          {{ buddyStore.isThinking ? '思考中...' : '发送' }}
        </button>
      </div>
    </div>
  </div>

  <!-- ═══ 阶段悬浮卡片 ═══ -->
  <div
    v-if="hoveredStep"
    class="fixed z-50 bg-dark-surface-alt border border-dark-border rounded-xl shadow-2xl px-4 py-3 text-xs w-72 pointer-events-none"
    :style="tooltipStyle"
  >
    <div class="flex items-center justify-between gap-2 mb-2">
      <span class="font-medium text-gray-200 truncate">{{ hoveredStep.stage_name }}</span>
      <span
        class="text-[10px] px-2 py-0.5 rounded-full font-mono flex-shrink-0"
        :class="masteryBadgeClass(hoveredStep.mastery)"
      >
        {{ Math.round(hoveredStep.mastery) }}%
      </span>
    </div>
    <p v-if="hoveredStep.description" class="text-gray-500 leading-relaxed mb-2">
      {{ hoveredStep.description }}
    </p>
    <div v-if="hoveredStep.knowledge_points?.length" class="border-t border-dark-border pt-2 mt-1">
      <div class="text-gray-500 mb-1.5">知识点掌握度：</div>
      <div
        v-for="kp in hoveredStep.knowledge_points"
        :key="kp"
        class="flex items-center justify-between py-0.5"
      >
        <span class="text-gray-400 truncate mr-2">{{ kp }}</span>
        <span class="font-mono flex-shrink-0" :class="kpMasteryColor(hoveredStep.knowledge_point_mastery?.[kp])">
          {{ Math.round(hoveredStep.knowledge_point_mastery?.[kp] || 0) }}%
        </span>
      </div>
    </div>
  </div>
</div>
</template>

<script setup>
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import { useBuddyStore } from '../stores/buddy'
import { createResource } from '../api'

const buddyStore = useBuddyStore()
const inputMessage = ref('')
const inputRef = ref(null)
const messageListRef = ref(null)
const expandedNotes = ref({})
const hoveredStep = ref(null)
const tooltipStyle = ref({})
const exportLoading = ref(false)

// ── 计算属性 ──

const activeQuestionText = computed(() => {
  return buddyStore.activeQuestion?.question || ''
})

const canSubmit = computed(() => {
  return buddyStore.currentPathId && inputMessage.value.trim() && !buddyStore.isThinking
})

const inputPlaceholder = computed(() => {
  if (!buddyStore.currentPathId) return '请先选择学习路径'
  if (buddyStore.isThinking) return '学伴思考中...'
  if (buddyStore.waitingForAnswer) return `回答「${buddyStore.activeQuestion?.knowledge_point || ''}」的问题...`
  return '输入想学的内容，或点击「学伴提问」...'
})


// ── 方法 ──

function autoResize() {
  const el = inputRef.value
  if (el) {
    el.style.height = 'auto'
    el.style.height = Math.min(el.scrollHeight, 128) + 'px'
  }
}

function scrollToBottom() {
  nextTick(() => {
    if (messageListRef.value) {
      messageListRef.value.scrollTop = messageListRef.value.scrollHeight
    }
  })
}

/** 切换学习笔记展开/收起 */
function toggleNote(index) {
  expandedNotes.value[index] = !expandedNotes.value[index]
}

/** 悬浮卡片：显示 / 隐藏 */
function showTooltip(step, event) {
  const rect = event.currentTarget.getBoundingClientRect()
  hoveredStep.value = step
  tooltipStyle.value = {
    left: Math.max(8, Math.min(rect.left, window.innerWidth - 296)) + 'px',
    top: (rect.bottom + 6) + 'px',
  }
}
function hideTooltip() {
  hoveredStep.value = null
}

/** 简单的 Markdown 渲染（粗体、换行、列表） */
function renderMarkdown(text) {
  if (!text) return ''
  let html = text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    // 标题
    .replace(/^### (.+)$/gm, '<strong class="text-gray-300 block mt-2 mb-1">$1</strong>')
    .replace(/^## (.+)$/gm, '<strong class="text-gray-200 text-sm block mt-3 mb-1">$1</strong>')
    .replace(/^# (.+)$/gm, '<strong class="text-gray-100 text-base block mt-3 mb-1">$1</strong>')
    // 粗体
    .replace(/\*\*(.+?)\*\*/g, '<strong class="text-gray-300">$1</strong>')
    // 列表
    .replace(/^- (.+)$/gm, '<span class="block ml-2">• $1</span>')
    // 换行
    .replace(/\n/g, '<br>')
  return html
}

// ── 事件处理 ──

async function handleRequestQuestion() {
  // 如果有活跃问题，先放弃当前问题再换新题
  if (buddyStore.waitingForAnswer) {
    buddyStore.activeQuestion = null
  }
  await buddyStore.requestQuestion()
  scrollToBottom()
}

async function handleSubmit() {
  const text = inputMessage.value.trim()
  if (!canSubmit.value || !text) return

  inputMessage.value = ''
  autoResize()

  if (buddyStore.waitingForAnswer) {
    // 有活跃问题 → 作为答案提交
    await buddyStore.submitAnswer(text)
  } else {
    // 无活跃问题 → 提示用户先点"学伴提问"
    buddyStore.messages.push({
      type: 'system',
      content: '💡 请先点击「学伴提问」或「换个知识点」，让学伴出题后再回答',
    })
  }
  scrollToBottom()
}

async function onPathChange(event) {
  const pathId = Number(event.target.value)
  await buddyStore.selectPath(pathId)
  buddyStore.resetSession()
  expandedNotes.value = {}
  scrollToBottom()
}

/** 导出学习笔记至「我的资源」 */
async function handleExportNotes() {
  const notes = buddyStore.messages.filter(m => m.type === 'note')
  if (notes.length === 0) return

  exportLoading.value = true
  try {
    const pathTitle = buddyStore.currentPath?.title || '通用'
    const now = new Date().toLocaleString('zh-CN', { hour12: false })
    const sections = notes.map((msg, i) => {
      const kp = msg.meta?.kp || '知识点'
      const isCorrect = msg.meta?.isCorrect
      const before = msg.meta?.masteryBefore
      const after = msg.meta?.masteryAfter
      const increment = msg.meta?.increment

      let s = `## ${i + 1}. ${kp}\n\n`
      if (isCorrect !== undefined) {
        s += `- **掌握度变化**：${Math.round(before)}% → ${Math.round(after)}%（+${increment}）\n`
        s += `- **答题结果**：${isCorrect ? '✅ 正确' : '❌ 未答对'}\n\n`
      }
      s += `${msg.content}\n`
      return s
    })

    const content = `# 学习笔记 — ${pathTitle}\n\n> 导出时间：${now}\n\n---\n\n${sections.join('\n---\n\n')}`

    await createResource(
      buddyStore.studentId,
      `学习笔记 - ${pathTitle}`,
      content,
      '',
      buddyStore.currentPathId,
      null,
    )

    buddyStore.messages.push({
      type: 'system',
      content: '✅ 学习笔记已导出至「我的资源」',
    })
    scrollToBottom()
  } catch (e) {
    console.error('[BuddyChat] 导出笔记失败:', e)
    buddyStore.messages.push({
      type: 'system',
      content: `❌ 导出失败：${e.message}`,
    })
    scrollToBottom()
  } finally {
    exportLoading.value = false
  }
}

// ── 样式工具 ──

function stagePillClass(step) {
  const isFocused = buddyStore.focusedStepOrder === step.order
  const m = step.mastery || 0
  let borderColor, bgColor, textColor
  if (m >= 70) { borderColor = 'border-green-500/30'; bgColor = 'bg-green-500/10'; textColor = 'text-green-300' }
  else if (m >= 30) { borderColor = 'border-yellow-500/30'; bgColor = 'bg-yellow-500/10'; textColor = 'text-yellow-300' }
  else if (m > 0) { borderColor = 'border-red-500/30'; bgColor = 'bg-red-500/10'; textColor = 'text-red-300' }
  else { borderColor = 'border-dark-border'; bgColor = 'bg-dark-surface'; textColor = 'text-gray-500' }
  if (isFocused) { borderColor = 'border-blue-500/50'; bgColor = 'bg-blue-500/15' }
  return `${borderColor} ${bgColor} ${textColor}`
}

function stageDotClass(mastery) {
  const m = mastery || 0
  if (m >= 70) return 'bg-green-400'
  if (m >= 30) return 'bg-yellow-400'
  if (m > 0) return 'bg-red-400'
  return 'bg-gray-500'
}

function masteryBadgeClass(mastery) {
  const m = mastery || 0
  if (m >= 70) return 'bg-green-500/10 text-green-400 border border-green-500/20'
  if (m >= 30) return 'bg-yellow-500/10 text-yellow-400 border border-yellow-500/20'
  return 'bg-red-500/10 text-red-400 border border-red-500/20'
}

function kpMasteryColor(mastery) {
  const m = mastery || 0
  if (m >= 70) return 'text-green-400'
  if (m >= 30) return 'text-yellow-400'
  if (m > 0) return 'text-red-400'
  return 'text-gray-500'
}

function noteHeaderClass(isCorrect) {
  return isCorrect ? 'text-green-400' : 'text-gray-300'
}

// ── 自动滚动 ──
watch(() => buddyStore.messages.length, scrollToBottom)
watch(() => buddyStore.isThinking, (v) => { if (!v) scrollToBottom() })

onMounted(() => {
  buddyStore.loadPaths()
})
</script>

<style scoped>
.scrollbar-thin::-webkit-scrollbar {
  width: 5px;
}
.scrollbar-thin::-webkit-scrollbar-track {
  background: transparent;
}
.scrollbar-thin::-webkit-scrollbar-thumb {
  background: #3E3E4E;
  border-radius: 4px;
}

.typing-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #94a3b8;
  animation: typing-bounce 1.4s infinite both;
}
.typing-dot:nth-child(2) { animation-delay: 0.2s; }
.typing-dot:nth-child(3) { animation-delay: 0.4s; }
@keyframes typing-bounce {
  0%, 80%, 100% { transform: scale(0.6); opacity: 0.4; }
  40% { transform: scale(1); opacity: 1; }
}

/* 学习笔记 Markdown 样式 */
:deep(.learning-note) br { content: ''; display: block; margin: 4px 0; }
:deep(.learning-note) strong { color: #e2e8f0; }
</style>
