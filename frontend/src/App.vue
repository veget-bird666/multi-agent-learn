<template>
  <div class="min-h-screen flex flex-col bg-dark-bg">
    <!-- 顶部导航 -->
    <header class="bg-dark-surface/80 backdrop-blur-md border-b border-dark-border/60 sticky top-0 z-50">
      <div class="max-w-6xl mx-auto px-6 h-14 flex items-center justify-between">
        <router-link to="/" class="flex items-center gap-2 text-lg font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
          <span class="text-2xl">📚</span>
          AI 学习助手
        </router-link>
        <nav class="flex items-center gap-1 text-sm">
          <router-link
            v-for="item in navItems"
            :key="item.path"
            :to="item.path"
            class="px-4 py-2 rounded-lg transition-all duration-200"
            :class="isActive(item.path) ? 'bg-blue-500/20 text-blue-300 font-medium' : 'text-gray-400 hover:text-gray-200 hover:bg-dark-surface-hover'"
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
    <footer class="text-center text-xs text-gray-600 py-4 border-t border-dark-border/40">
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
  { path: '/resources', label: '我的资源' },
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
