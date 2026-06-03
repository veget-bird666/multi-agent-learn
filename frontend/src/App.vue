<template>
  <div class="min-h-screen flex flex-col bg-gradient-to-br from-gray-50 to-blue-50">
    <!-- 顶部导航 -->
    <header class="bg-white/80 backdrop-blur-md border-b border-gray-200/60 sticky top-0 z-50">
      <div class="max-w-6xl mx-auto px-6 h-14 flex items-center justify-between">
        <router-link to="/" class="flex items-center gap-2 text-lg font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
          <span class="text-2xl">📚</span>
          AI 学习助手
        </router-link>
        <nav class="flex items-center gap-1 text-sm">
          <router-link
            v-for="item in navItems"
            :key="item.path"
            :to="item.path"
            class="px-4 py-2 rounded-lg transition-all duration-200"
            :class="isActive(item.path) ? 'bg-blue-50 text-blue-700 font-medium' : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'"
          >
            {{ item.label }}
          </router-link>
        </nav>
      </div>
    </header>

    <!-- 主内容 -->
    <main class="flex-1">
      <router-view v-slot="{ Component }">
        <transition name="page" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </main>

    <!-- 底部 -->
    <footer class="text-center text-xs text-gray-400 py-4">
      AI 个性化学习多智能体系统 &copy; 2026
    </footer>
  </div>
</template>

<script setup>
import { useRoute } from 'vue-router'

const route = useRoute()
const navItems = [
  { path: '/', label: '首页' },
  { path: '/chat', label: '开始学习' },
  { path: '/learning-path', label: '学习路径' },
]

function isActive(path) {
  return route.path === path
}
</script>

<style scoped>
.page-enter-active,
.page-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}
.page-enter-from {
  opacity: 0;
  transform: translateY(8px);
}
.page-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}
</style>
