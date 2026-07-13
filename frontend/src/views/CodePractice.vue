<template>
  <div class="flex-1 flex flex-col bg-dark-bg min-h-0">
    <!-- ═══ 顶部导航栏 ═══ -->
    <header class="flex-shrink-0 bg-dark-surface/80 backdrop-blur-md border-b border-dark-border/60 px-6 h-14 flex items-center justify-between">
      <div class="flex items-center gap-3">
        <router-link
          to="/resources"
          class="flex items-center gap-1.5 text-gray-400 hover:text-gray-200 bg-dark-surface-hover px-3 py-1.5 rounded-lg text-xs transition-colors"
        >
          ← 返回资源
        </router-link>
        <span class="text-gray-600">|</span>
        <h1 class="text-sm font-semibold text-gray-100 truncate max-w-[300px]">{{ exercise?.title || '代码实操' }}</h1>
      </div>
      <div class="flex items-center gap-2">
        <span v-if="exercise" class="text-xs text-gray-500 bg-dark-surface-hover px-2 py-1 rounded font-mono">{{ exercise.language }}</span>
        <span v-if="exercise" :class="['text-xs px-2 py-0.5 rounded-full', difficultyBadge]">{{ difficultyLabel }}</span>
        <button
          v-if="exercise"
          @click="resetCode"
          class="text-xs text-gray-500 hover:text-gray-300 px-3 py-1.5 rounded-lg transition-colors"
        >重置代码</button>
      </div>
    </header>

    <!-- 加载态 -->
    <div v-if="loading" class="flex-1 flex items-center justify-center">
      <div class="flex flex-col items-center gap-3">
        <div class="w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin"></div>
        <span class="text-sm text-gray-400">加载代码练习...</span>
      </div>
    </div>

    <!-- 错误态 -->
    <div v-else-if="error" class="flex-1 flex items-center justify-center">
      <div class="bg-dark-surface rounded-2xl border border-dark-border p-16 text-center">
        <div class="text-5xl mb-4">⚠️</div>
        <h3 class="text-lg font-semibold text-gray-300 mb-2">加载失败</h3>
        <p class="text-sm text-gray-500 mb-6">{{ error }}</p>
        <router-link
          to="/resources"
          class="inline-flex items-center gap-2 bg-gradient-to-r from-indigo-600 to-purple-600 text-white px-6 py-2.5 rounded-lg text-sm font-medium hover:shadow-lg transition-all"
        >
          返回资源列表
        </router-link>
      </div>
    </div>

    <!-- ═══ 主体：左右两栏 ═══ -->
    <template v-else-if="exercise">
      <div class="flex-1 flex gap-0 px-4 pb-4 overflow-hidden min-h-0">
        <!-- 左栏 -->
        <div class="flex-1 flex flex-col min-w-0 bg-dark-surface rounded-xl border border-dark-border overflow-hidden mr-2 min-h-0">
          <!-- 左栏 Tab 切换 -->
          <div class="flex-shrink-0 flex border-b border-dark-border bg-dark-surface-hover/50">
            <button
              v-for="tab in leftTabs"
              :key="tab.key"
              @click="activeTab = tab.key"
              class="px-4 py-2.5 text-xs font-medium transition-colors border-b-2"
              :class="activeTab === tab.key
                ? 'text-indigo-400 border-indigo-500 bg-indigo-500/5'
                : 'text-gray-500 border-transparent hover:text-gray-300 hover:bg-dark-surface-hover'"
            >
              {{ tab.label }}
            </button>
          </div>

          <!-- 左栏内容（独立滚动） -->
          <div class="flex-1 overflow-y-auto p-5">
            <!-- 题目描述 -->
            <div v-if="activeTab === 'description'" class="prose prose-invert prose-sm max-w-none text-gray-300" v-html="renderedDescription"></div>

            <!-- 测试用例 -->
            <div v-if="activeTab === 'testcases'">
              <h4 class="text-sm font-semibold text-gray-300 mb-3">测试用例 ({{ exercise.test_cases?.length || 0 }})</h4>
              <div class="space-y-2">
                <div
                  v-for="(tc, i) in exercise.test_cases"
                  :key="i"
                  class="bg-dark-surface-alt rounded-lg p-3 border border-dark-border text-xs font-mono"
                >
                  <div class="flex items-center justify-between mb-1">
                    <span class="text-gray-500">用例 #{{ i + 1 }}</span>
                    <span
                      v-if="testResults[i] !== undefined"
                      class="text-xs font-medium"
                      :class="testResults[i] ? 'text-green-400' : 'text-red-400'"
                    >
                      {{ testResults[i] ? '✓ 通过' : '✗ 未通过' }}
                    </span>
                  </div>
                  <div class="text-gray-400">
                    <span class="text-gray-500">参数：</span><code class="text-gray-300">{{ formatArgs(tc.args) }}</code>
                  </div>
                  <div class="text-gray-400">
                    <span class="text-gray-500">期望输出：</span><code class="text-gray-300">{{ formatExpected(tc.expected) }}</code>
                  </div>
                  <div v-if="testActual[i] !== undefined" class="text-gray-400">
                    <span class="text-gray-500">实际输出：</span><code class="text-gray-300">{{ testActual[i] }}</code>
                  </div>
                  <div v-if="testErrors[i]" class="text-red-400 mt-1">
                    ⚠ {{ testErrors[i] }}
                  </div>
                </div>
              </div>
              <button
                v-if="userCode"
                @click="runTests"
                :disabled="running"
                class="mt-3 w-full px-4 py-2 bg-indigo-600 hover:bg-indigo-500 disabled:bg-indigo-600/40 text-white rounded-lg text-xs font-medium transition-colors"
              >
                {{ running ? '运行中...' : '运行全部测试用例' }}
              </button>
            </div>

            <!-- 提示 -->
            <div v-if="activeTab === 'hints'">
              <p v-if="!exercise.hints?.length" class="text-sm text-gray-500">暂无提示</p>
              <div class="space-y-2">
                <div
                  v-for="(hint, i) in exercise.hints"
                  :key="i"
                  class="text-sm text-gray-400 bg-dark-surface-alt rounded-lg p-3 border border-dark-border"
                >
                  <span class="text-gray-500 font-mono mr-2">#{{ i + 1 }}</span>{{ hint }}
                </div>
              </div>
            </div>

            <!-- 参考答案 -->
            <div v-if="activeTab === 'solution'">
              <pre class="bg-dark-surface-alt rounded-lg p-4 overflow-x-auto text-sm text-gray-300 border border-dark-border font-mono leading-relaxed"><code>{{ exercise.solution }}</code></pre>
              <div v-if="exercise.explanation" class="mt-3 text-sm text-gray-400 bg-dark-surface-alt rounded-lg p-3 border border-dark-border">
                <span class="text-gray-300 font-medium">解题思路：</span>{{ exercise.explanation }}
              </div>
            </div>
          </div>
        </div>

        <!-- 右栏 -->
        <div class="flex-1 flex flex-col min-w-0 bg-dark-surface rounded-xl border border-dark-border overflow-hidden ml-2 min-h-0">
          <!-- 右栏头部 -->
          <div class="flex-shrink-0 flex items-center justify-between px-5 py-3 border-b border-dark-border bg-dark-surface-hover/50">
            <label class="text-sm font-medium text-gray-300">
              代码编辑区
              <span class="text-xs text-gray-500 ml-2">补全 <code class="text-indigo-400">{{ exercise.function_name }}</code> 的函数体</span>
            </label>
            <div class="flex items-center gap-2">
              <button
                @click="runCode"
                :disabled="running"
                class="flex items-center gap-1.5 bg-indigo-600 hover:bg-indigo-500 disabled:bg-indigo-600/40 text-white px-4 py-1.5 rounded-lg text-xs font-medium transition-colors"
              >
                <svg v-if="!running" class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z"/>
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
                </svg>
                <svg v-else class="w-3.5 h-3.5 animate-spin" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
                </svg>
                {{ running ? '运行中...' : '运行代码' }}
              </button>
            </div>
          </div>

          <!-- 代码编辑器（填满剩余高度） -->
          <div class="flex-1 overflow-hidden">
            <Codemirror
              v-model="userCode"
              :extensions="editorExtensions"
              :disabled="running"
              :style="{ height: '100%' }"
              class="codemirror-wrap h-full"
            />
          </div>

          <!-- 运行结果输出（底部折叠） -->
          <div v-if="runResult" class="flex-shrink-0 border-t border-dark-border bg-dark-surface-hover/30">
            <div class="flex items-center justify-between px-5 py-2 border-b border-dark-border">
              <span class="text-xs text-gray-500">
                运行结果 · 退出码: {{ runResult.exit_code }}
                <span v-if="runResult.timed_out" class="text-yellow-400 ml-2">⏱ 超时</span>
              </span>
              <button @click="runResult = null" class="text-xs text-gray-500 hover:text-gray-300 transition-colors">关闭</button>
            </div>
            <div class="max-h-[160px] overflow-y-auto p-3">
              <div v-if="runResult.stdout" class="mb-2">
                <pre class="text-sm text-green-400 font-mono leading-relaxed whitespace-pre-wrap"><code>{{ runResult.stdout }}</code></pre>
              </div>
              <div v-if="runResult.stderr">
                <pre class="text-sm text-red-400 font-mono leading-relaxed whitespace-pre-wrap"><code>{{ runResult.stderr }}</code></pre>
              </div>
              <div v-if="!runResult.stdout && !runResult.stderr" class="text-sm text-gray-500">
                {{ runResult.exit_code === 0 ? '✓ 代码语法正确，无输出' : '程序无输出' }}
              </div>
            </div>
          </div>

          <!-- 测试进度提示（非折叠，显示在底部） -->
          <div v-if="!runResult && Object.keys(testResults).length > 0" class="flex-shrink-0 border-t border-dark-border px-5 py-2">
            <div class="flex items-center justify-between text-xs">
              <span class="text-gray-500">
                测试结果：
                <span class="text-green-400">{{ passedCount }} 通过</span>
                <span class="text-gray-600 mx-1">/</span>
                <span class="text-red-400">{{ failedCount }} 未通过</span>
                <span class="text-gray-600 mx-1">/</span>
                <span class="text-gray-500">共 {{ totalCount }} 组</span>
              </span>
              <button @click="switchToTestCases" class="text-indigo-400 hover:text-indigo-300 transition-colors">查看详情</button>
            </div>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { fetchResourceDetail, runCode as apiRunCode } from '../api'
import MarkdownIt from 'markdown-it'
import { Codemirror } from 'vue-codemirror'
import { python } from '@codemirror/lang-python'
import { oneDark } from '@codemirror/theme-one-dark'
import { keymap } from '@codemirror/view'

const md = new MarkdownIt({ html: false, linkify: true, breaks: true })
const route = useRoute()

// ── 状态 ──
const loading = ref(true)
const error = ref('')
const resource = ref(null)
const exercise = ref(null)
const userCode = ref('')
const running = ref(false)
const runResult = ref(null)
const testResults = ref({})
const testActual = ref({})
const testErrors = ref({})
const activeTab = ref('description')

const leftTabs = [
  { key: 'description', label: '📄 题目描述' },
  { key: 'testcases', label: '🧪 测试用例' },
  { key: 'hints', label: '💡 提示' },
  { key: 'solution', label: '🔑 参考答案' },
]

// ── 计算属性 ──
const editorExtensions = computed(() => [
  python(),
  oneDark,
  keymap.of([
    { key: 'Ctrl-Enter', run: () => { runCode(); return true; } },
    { key: 'Shift-Enter', run: () => { runTests(); return true; } },
  ]),
])

const difficultyBadge = computed(() => {
  const d = exercise.value?.difficulty
  if (d === 'easy') return 'bg-green-500/10 text-green-400'
  if (d === 'hard') return 'bg-red-500/10 text-red-400'
  return 'bg-yellow-500/10 text-yellow-400'
})

const difficultyLabel = computed(() => {
  const d = exercise.value?.difficulty
  if (d === 'easy') return '基础'
  if (d === 'hard') return '进阶'
  return '中等'
})

const renderedDescription = computed(() => {
  return md.render(exercise.value?.description || '')
})

const totalCount = computed(() => Object.keys(testResults.value).length)
const passedCount = computed(() => Object.values(testResults.value).filter(Boolean).length)
const failedCount = computed(() => Object.values(testResults.value).filter(v => !v).length)

// ── 方法 ──
function formatArgs(args) {
  if (args === undefined || args === null) return '(无参数)'
  try { return JSON.stringify(args) } catch { return String(args) }
}

function formatExpected(expected) {
  try { return JSON.stringify(expected) } catch { return String(expected) }
}

function switchToTestCases() {
  activeTab.value = 'testcases'
}

async function loadExercise() {
  loading.value = true
  error.value = ''
  try {
    const ormId = route.params.orm_id
    const data = await fetchResourceDetail(ormId)
    resource.value = data
    let parsed
    try { parsed = JSON.parse(data.content) } catch { throw new Error('代码案例数据格式异常') }

    exercise.value = {
      language: parsed.language || 'python',
      function_name: parsed.function_name || 'solution',
      title: parsed.title || data.title || '代码练习',
      difficulty: parsed.difficulty || 'medium',
      description: parsed.description || '',
      starter_code: parsed.starter_code || '',
      test_cases: parsed.test_cases || [],
      hints: parsed.hints || [],
      solution: parsed.solution || '',
      explanation: parsed.explanation || '',
    }
    userCode.value = exercise.value.starter_code
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}

async function runCode() {
  if (!userCode.value || running.value) return
  running.value = true
  runResult.value = null
  try {
    const result = await apiRunCode('python', userCode.value, '')
    runResult.value = result
  } catch (e) {
    runResult.value = { exit_code: -1, stdout: '', stderr: '', error: e.message }
  } finally {
    running.value = false
  }
}

function buildTestHarness(funcName, testCases, userFuncCode) {
  const casesJson = JSON.stringify(testCases)
  return `${userFuncCode}

# === 自动生成的测试桩 ===
import json

_test_cases_json = r'''${casesJson}'''
_test_cases = json.loads(_test_cases_json)
_results = []

for _i, _tc in enumerate(_test_cases):
    try:
        _args = _tc.get("args", [])
        _result = ${funcName}(*_args)
        _expected = _tc.get("expected")
        _passed = json.dumps(_result, sort_keys=True, default=str) == json.dumps(_expected, sort_keys=True, default=str)
        _results.append({
            "index": _i,
            "passed": _passed,
            "actual": _result if isinstance(_result, (list, dict, int, float, str, bool)) or _result is None else repr(_result),
            "expected": _expected
        })
    except Exception as _e:
        _results.append({
            "index": _i,
            "passed": False,
            "error": str(_e)
        })

print("__TEST_RESULTS__")
print(json.dumps(_results, ensure_ascii=False, default=str))
print("__END__")
`
}

function parseTestResults(stdout) {
  const match = stdout.match(/__TEST_RESULTS__\s*([\s\S]*?)\s*__END__/)
  if (!match) return null
  try { return JSON.parse(match[1]) } catch { return null }
}

async function runTests() {
  if (!userCode.value || running.value) return
  const funcName = exercise.value?.function_name || 'solution'
  const cases = exercise.value?.test_cases || []
  if (!cases.length) return

  testResults.value = {}
  testActual.value = {}
  testErrors.value = {}
  runResult.value = null

  const harness = buildTestHarness(funcName, cases, userCode.value)
  running.value = true
  try {
    const result = await apiRunCode('python', harness, '')
    runResult.value = result
    if (result.stderr) return

    const parsed = parseTestResults(result.stdout || '')
    if (!parsed || !Array.isArray(parsed) || parsed.length === 0) {
      testErrors.value[0] = '无法解析测试结果'
      return
    }
    for (const item of parsed) {
      const idx = item.index
      testResults.value[idx] = item.passed
      if (item.actual !== undefined) testActual.value[idx] = formatExpected(item.actual)
      if (item.error) testErrors.value[idx] = item.error
    }
    // 自动切到测试用例 tab
    activeTab.value = 'testcases'
  } catch (e) {
    runResult.value = { exit_code: -1, stdout: '', stderr: '', error: e.message }
  } finally {
    running.value = false
  }
}

function resetCode() {
  userCode.value = exercise.value?.starter_code || ''
  runResult.value = null
  testResults.value = {}
  testActual.value = {}
  testErrors.value = {}
}

onMounted(loadExercise)
</script>

<style>
/* CodeMirror 暗色样式 */
.codemirror-wrap {
  border-radius: 0;
}
.codemirror-wrap .cm-editor {
  font-size: 13px;
  line-height: 1.6;
  height: 100%;
}
.codemirror-wrap .cm-editor .cm-scroller {
  font-family: 'Fira Code', 'JetBrains Mono', 'Cascadia Code', 'Consolas', monospace;
  overflow: auto;
}
.codemirror-wrap .cm-editor.cm-focused {
  outline: none;
}
.codemirror-wrap .cm-editor .cm-gutters {
  border-right: 1px solid rgba(255, 255, 255, 0.05);
}

/* 滚动条美化 */
.overflow-y-auto::-webkit-scrollbar,
.overflow-y-auto::-webkit-scrollbar {
  width: 6px;
}
.overflow-y-auto::-webkit-scrollbar-track {
  background: transparent;
}
.overflow-y-auto::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.08);
  border-radius: 3px;
}
.overflow-y-auto::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.15);
}
</style>
