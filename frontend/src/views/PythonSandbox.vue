<template>
  <div class="max-w-5xl mx-auto px-4 py-6">
    <!-- 顶部 -->
    <div class="flex items-center justify-between mb-6">
      <div>
        <h2 class="text-xl font-bold text-gray-100">Python 沙盒</h2>
        <p class="text-sm text-gray-500 mt-1">编写 Python 代码并在 Docker 沙箱中运行测试</p>
      </div>
      <button
        @click="resetCode"
        class="text-xs text-gray-500 hover:text-gray-300 px-3 py-1.5 rounded-lg transition-colors"
      >重置代码</button>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <!-- 左栏：代码编辑器 -->
      <div class="space-y-4">
        <div class="bg-dark-surface rounded-xl border border-dark-border overflow-hidden">
          <div class="flex items-center justify-between px-5 py-3 border-b border-dark-border">
            <label class="text-sm font-medium text-gray-300">
              Python 代码
              <span class="text-xs text-gray-500 ml-2">按 Ctrl+Enter 快速运行</span>
            </label>
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
          <Codemirror
            v-model="code"
            :extensions="extensions"
            :disabled="running"
            :style="{ height: '400px' }"
            :autofocus="true"
            class="codemirror-wrap"
          />
        </div>

        <!-- stdin 输入（可选） -->
        <div class="bg-dark-surface rounded-xl border border-dark-border overflow-hidden">
          <button
            @click="showStdin = !showStdin"
            class="w-full px-5 py-3 flex items-center justify-between text-sm text-gray-300 hover:text-gray-100 transition-colors"
          >
            <span class="font-medium">⌨️ 标准输入（可选）</span>
            <svg
              class="w-4 h-4 transition-transform"
              :class="showStdin ? 'rotate-180' : ''"
              fill="none" stroke="currentColor" viewBox="0 0 24 24"
            >
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/>
            </svg>
          </button>
          <div v-if="showStdin" class="px-5 pb-4">
            <textarea
              v-model="stdin"
              class="w-full bg-dark-bg text-gray-200 p-3 font-mono text-sm rounded-lg border border-dark-border resize-none focus:outline-none min-h-[60px]"
              placeholder="输入程序需要的 stdin 数据..."
              spellcheck="false"
            ></textarea>
          </div>
        </div>
      </div>

      <!-- 右栏：运行输出 -->
      <div class="space-y-4">
        <div class="bg-dark-surface rounded-xl border border-dark-border overflow-hidden">
          <div class="flex items-center justify-between px-5 py-3 border-b border-dark-border">
            <h4 class="text-sm font-medium text-gray-300">
              运行输出
              <span v-if="elapsed !== null" class="text-xs text-gray-500 ml-2">(耗时 {{ elapsed }}ms，退出码: {{ result?.exit_code }})</span>
            </h4>
            <button
              v-if="result"
              @click="clearResult"
              class="text-xs text-gray-500 hover:text-gray-300 transition-colors"
            >清除</button>
          </div>
          <div class="p-5 min-h-[200px]">
            <!-- 运行前提示 -->
            <div v-if="!result && !running" class="text-gray-600 text-sm">
              点击「运行代码」或按 <kbd class="bg-dark-surface-hover px-1.5 py-0.5 rounded text-xs font-mono">Ctrl+Enter</kbd> 执行
            </div>

            <!-- 加载中 -->
            <div v-if="running" class="flex items-center gap-3 text-gray-400 text-sm">
              <div class="w-4 h-4 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin"></div>
              <span>代码运行中...</span>
            </div>

            <template v-if="result">
              <!-- stdout -->
              <div v-if="result.stdout" class="mb-3">
                <div class="text-xs text-gray-500 mb-1">标准输出</div>
                <pre class="bg-dark-bg rounded-lg p-3 text-sm text-green-400 font-mono overflow-x-auto leading-relaxed border border-dark-border max-h-[300px] overflow-y-auto"><code>{{ result.stdout }}</code></pre>
              </div>

              <!-- stderr -->
              <div v-if="result.stderr">
                <div class="text-xs text-gray-500 mb-1">标准错误</div>
                <pre class="bg-dark-bg rounded-lg p-3 text-sm text-red-400 font-mono overflow-x-auto leading-relaxed border border-dark-border max-h-[200px] overflow-y-auto"><code>{{ result.stderr }}</code></pre>
              </div>

              <!-- 无输出 -->
              <div v-if="!result.stdout && !result.stderr" class="text-gray-500 text-sm">
                {{ result.exit_code === 0 ? '✓ 代码语法正确，无输出' : '程序无输出' }}
              </div>
            </template>
          </div>
        </div>

        <!-- 执行历史 -->
        <div class="bg-dark-surface rounded-xl border border-dark-border overflow-hidden">
          <button
            @click="showHistory = !showHistory"
            class="w-full px-5 py-3 flex items-center justify-between text-sm text-gray-300 hover:text-gray-100 transition-colors"
          >
            <span class="font-medium">📜 执行记录 ({{ history.length }})</span>
            <svg
              class="w-4 h-4 transition-transform"
              :class="showHistory ? 'rotate-180' : ''"
              fill="none" stroke="currentColor" viewBox="0 0 24 24"
            >
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/>
            </svg>
          </button>
          <div v-if="showHistory" class="px-5 pb-4">
            <div v-if="history.length === 0" class="text-sm text-gray-600">暂无执行记录</div>
            <div v-for="(h, i) in [...history].reverse()" :key="i" class="mb-2 last:mb-0">
              <div
                class="bg-dark-surface-alt rounded-lg p-3 border border-dark-border cursor-pointer hover:border-indigo-500/30 transition-colors"
                @click="restoreHistory(i)"
              >
                <div class="flex items-center justify-between text-xs text-gray-500 mb-1">
                  <span>{{ h.time }}</span>
                  <span :class="h.exit_code === 0 ? 'text-green-400' : 'text-red-400'">
                    exit {{ h.exit_code }} · {{ h.elapsed }}ms
                  </span>
                </div>
                <pre class="text-xs text-gray-400 font-mono truncate">{{ h.preview }}</pre>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { runCode as apiRunCode } from '../api'
import { Codemirror } from 'vue-codemirror'
import { python } from '@codemirror/lang-python'
import { oneDark } from '@codemirror/theme-one-dark'
import { keymap } from '@codemirror/view'

// 从 localStorage 初始化代码
const saved = localStorage.getItem('sandbox_code')
const code = ref(saved || `def greet(name):
    return f"你好, {name}!"


# 测试调用
print(greet("世界"))
print(greet("Python 沙盒"))

# 试试计算
print(f"1 + 2 + ... + 100 = {sum(range(1, 101))}")
`)

const stdin = ref('')
const running = ref(false)
const result = ref(null)
const elapsed = ref(null)
const showStdin = ref(false)
const showHistory = ref(false)
const history = ref([])

// CodeMirror 扩展：Python 语法 + 暗色主题 + Ctrl+Enter 快捷键
const extensions = computed(() => [
  python(),
  oneDark,
  keymap.of([
    {
      key: 'Ctrl-Enter',
      run: () => { runCode(); return true; },
    },
    {
      key: 'Shift-Enter',
      run: () => { runCode(); return true; },
    },
  ]),
])

// 自动保存代码到 localStorage
watch(code, (val) => {
  localStorage.setItem('sandbox_code', val)
})

async function runCode() {
  if (!code.value || running.value) return
  running.value = true
  result.value = null

  const t0 = performance.now()
  try {
    const res = await apiRunCode('python', code.value, stdin.value)
    elapsed.value = Math.round(performance.now() - t0)
    result.value = res

    const preview = (res.stdout || res.stderr || '').slice(0, 80).replace(/\n/g, ' ')
    history.value.push({
      time: new Date().toLocaleTimeString(),
      code: code.value,
      stdin: stdin.value,
      elapsed: elapsed.value,
      exit_code: res.exit_code,
      preview: preview || '(无输出)',
    })
  } catch (e) {
    elapsed.value = Math.round(performance.now() - t0)
    result.value = { exit_code: -1, stdout: '', stderr: e.message }
  } finally {
    running.value = false
  }
}

function clearResult() {
  result.value = null
  elapsed.value = null
}

function resetCode() {
  code.value = `def greet(name):
    return f"你好, {name}!"


print(greet("世界"))
print(greet("Python 沙盒"))

print(f"1 + 2 + ... + 100 = {sum(range(1, 101))}")
`
  stdin.value = ''
  result.value = null
  elapsed.value = null
}

function restoreHistory(idx) {
  const h = history.value[idx]
  if (h) {
    code.value = h.code
    stdin.value = h.stdin || ''
    result.value = null
    elapsed.value = null
  }
}
</script>

<style>
/* CodeMirror 在暗色背景下的样式微调 */
.codemirror-wrap .cm-editor {
  border-radius: 0 0 0.75rem 0.75rem;
  font-size: 13px;
  line-height: 1.6;
}
.codemirror-wrap .cm-editor .cm-scroller {
  font-family: 'Fira Code', 'JetBrains Mono', 'Cascadia Code', 'Consolas', monospace;
}
.codemirror-wrap .cm-editor.cm-focused {
  outline: none;
}
.codemirror-wrap .cm-editor .cm-gutters {
  border-right: 1px solid rgba(255, 255, 255, 0.05);
}
</style>
