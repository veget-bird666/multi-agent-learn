<template>
  <div class="max-w-5xl mx-auto px-4 py-6">
    <!-- 顶部 -->
    <div class="flex items-center justify-between mb-6">
      <div>
        <h2 class="text-xl font-bold text-gray-100">我的学习资源</h2>
        <p class="text-sm text-gray-500 mt-1">所有对话中生成的资源集中管理</p>
      </div>
      <button
        @click="refresh"
        :disabled="loading"
        class="text-xs text-blue-400 hover:text-blue-300 bg-blue-500/10 px-3 py-1.5 rounded-lg transition-colors disabled:opacity-40"
      >
        {{ loading ? '加载中...' : '刷新' }}
      </button>
    </div>

    <!-- 加载态 -->
    <div v-if="loading" class="flex items-center justify-center py-20">
      <div class="flex flex-col items-center gap-3">
        <div class="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
        <span class="text-sm text-gray-400">加载资源中...</span>
      </div>
    </div>

    <!-- 空态 -->
    <div v-else-if="groups.length === 0" class="bg-dark-surface rounded-2xl border border-dark-border p-16 text-center">
      <div class="text-5xl mb-4">📦</div>
      <h3 class="text-lg font-semibold text-gray-300 mb-2">暂无学习资源</h3>
      <p class="text-sm text-gray-500 mb-6">开始对话学习并生成资源后，它们会出现在这里</p>
      <router-link
        to="/chat"
        class="inline-flex items-center gap-2 bg-gradient-to-r from-blue-600 to-purple-600 text-white px-6 py-2.5 rounded-lg text-sm font-medium hover:shadow-lg hover:shadow-blue-500/20 transition-all"
      >
        开始学习
        <span>→</span>
      </router-link>
    </div>

    <!-- 资源列表 — 按知识点分组 -->
    <div v-else class="space-y-8">
      <div v-for="(group, gi) in groups" :key="gi">
        <div class="flex items-center gap-2 mb-3">
          <h3 class="font-semibold text-gray-200">{{ group.knowledge_point }}</h3>
          <span class="text-xs text-gray-500 bg-dark-surface-alt px-2 py-0.5 rounded-full">{{ group.items.length }} 项</span>
        </div>
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          <div
            v-for="item in group.items"
            :key="item.orm_id"
            class="relative group/card"
          >
            <ResourceCard :resource="item" />
            <!-- 作答按钮（仅试卷） -->
            <button
              v-if="item.type === 'exam'"
              @click.stop="examTaking = item"
              class="absolute bottom-2 right-2 bg-gradient-to-r from-blue-600 to-purple-600 text-white text-xs px-3 py-1.5 rounded-lg shadow-sm hover:shadow-md hover:shadow-blue-500/20 transition-all opacity-0 group-hover/card:opacity-100"
            >
              开始作答
            </button>
            <!-- 删除按钮（hover 显示） -->
            <button
              @click="confirmDelete(item)"
              class="absolute top-2 right-2 w-7 h-7 bg-dark-surface/80 backdrop-blur-sm rounded-full border border-dark-border text-gray-500 hover:text-red-400 hover:border-red-500/30 opacity-0 group-hover/card:opacity-100 transition-all flex items-center justify-center text-xs shadow-sm"
              title="删除此资源"
            >
              ✕
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 删除确认弹窗 -->
    <Teleport to="body">
      <div
        v-if="deleteTarget"
        class="fixed inset-0 bg-black/40 z-50 flex items-center justify-center p-4"
        @click.self="deleteTarget = null"
      >
        <div class="bg-dark-surface rounded-2xl p-6 max-w-sm w-full shadow-2xl border border-dark-border">
          <div class="text-center mb-4">
            <div class="text-3xl mb-3">⚠️</div>
            <h3 class="font-semibold text-gray-200 mb-1">确认删除</h3>
            <p class="text-sm text-gray-400">删除「{{ deleteTarget.title }}」后将无法恢复，确认删除吗？</p>
          </div>
          <div class="flex gap-3">
            <button
              @click="deleteTarget = null"
              class="flex-1 px-4 py-2.5 border border-dark-border rounded-xl text-sm text-gray-400 hover:bg-dark-surface-hover transition-colors"
            >取消</button>
            <button
              @click="doDelete"
              class="flex-1 px-4 py-2.5 bg-red-500 text-white rounded-xl text-sm hover:bg-red-400 transition-colors"
              :disabled="deleting"
            >{{ deleting ? '删除中...' : '确认删除' }}</button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- 试卷作答弹窗 -->
    <ExamModal
      v-if="examTaking"
      :resource="examTaking"
      @close="examTaking = null; refresh()"
    />

    <!-- 删除成功提示 -->
    <div
      v-if="toast"
      class="fixed bottom-6 left-1/2 -translate-x-1/2 bg-dark-surface text-gray-200 px-5 py-2.5 rounded-xl text-sm shadow-lg z-50 animate-fade-in border border-dark-border"
    >
      {{ toast }}
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useChatStore } from '../stores/chat'
import { fetchResources, deleteResource } from '../api'
import ResourceCard from '../components/ResourceCard.vue'
import ExamModal from '../components/ExamModal.vue'

const chatStore = useChatStore()
const loading = ref(true)
const resources = ref([])
const examTaking = ref(null)
const deleteTarget = ref(null)
const deleting = ref(false)
const toast = ref('')

/** 按 knowledge_point 分组 */
const groups = computed(() => {
  const map = {}
  for (const r of resources.value) {
    const kp = r.knowledge_point || '未分类'
    if (!map[kp]) map[kp] = []
    map[kp].push(r)
  }
  return Object.entries(map).map(([knowledge_point, items]) => ({ knowledge_point, items }))
})

async function refresh() {
  loading.value = true
  try {
    const data = await fetchResources(chatStore.studentId)
    resources.value = data.resources || []
  } catch (e) {
    showToast('加载失败：' + e.message)
  } finally {
    loading.value = false
  }
}

function confirmDelete(item) {
  deleteTarget.value = item
}

async function doDelete() {
  if (!deleteTarget.value) return
  deleting.value = true
  try {
    await deleteResource(deleteTarget.value.orm_id)
    resources.value = resources.value.filter(r => r.orm_id !== deleteTarget.value.orm_id)
    deleteTarget.value = null
    showToast('资源已删除')
  } catch (e) {
    showToast('删除失败：' + e.message)
  } finally {
    deleting.value = false
  }
}

function showToast(msg) {
  toast.value = msg
  setTimeout(() => { toast.value = '' }, 3000)
}

onMounted(refresh)
</script>
