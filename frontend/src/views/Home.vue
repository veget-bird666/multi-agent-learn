<template>
  <div class="max-w-4xl mx-auto px-6 py-16 text-center">
    <h1 class="text-4xl font-bold mb-4">AI 个性化学习系统</h1>
    <p class="text-lg text-gray-600 mb-8">
      基于大模型的个性化资源生成与学习多智能体系统
    </p>

    <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12 text-left">
      <div class="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
        <div class="text-blue-500 text-2xl mb-2">🎯</div>
        <h3 class="font-semibold mb-2">个性化画像</h3>
        <p class="text-sm text-gray-500">通过对话自动构建你的专属学习画像</p>
      </div>
      <div class="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
        <div class="text-green-500 text-2xl mb-2">🤖</div>
        <h3 class="font-semibold mb-2">多智能体协同</h3>
        <p class="text-sm text-gray-500">7 个智能体协同为你生成最优学习资源</p>
      </div>
      <div class="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
        <div class="text-purple-500 text-2xl mb-2">🔄</div>
        <h3 class="font-semibold mb-2">动态路径规划</h3>
        <p class="text-sm text-gray-500">根据学习情况动态调整，支持路径回滚</p>
      </div>
    </div>

    <router-link
      to="/chat"
      class="inline-block bg-blue-600 text-white px-8 py-3 rounded-lg text-lg font-medium hover:bg-blue-700 transition"
    >
      开始学习
    </router-link>
  </div>
</template>
