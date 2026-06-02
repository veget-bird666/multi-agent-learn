<template>
  <div class="min-h-screen flex flex-col">
    <!-- 顶部导航 -->
    <header class="bg-white border-b border-gray-200 px-6 py-3">
      <div class="max-w-6xl mx-auto flex items-center justify-between">
        <router-link to="/" class="text-lg font-semibold text-blue-600">
          AI 学习助手
        </router-link>
        <nav class="flex gap-4 text-sm">
          <router-link to="/" class="hover:text-blue-600">首页</router-link>
          <router-link to="/chat" class="hover:text-blue-600">开始学习</router-link>
        </nav>
      </div>
    </header>

    <!-- 主内容 -->
    <main class="flex-1">
      <router-view />
    </main>
  </div>
</template>
