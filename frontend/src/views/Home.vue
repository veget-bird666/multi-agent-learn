<template>
  <div class="max-w-5xl mx-auto px-6 py-12">
    <!-- Hero -->
    <div class="text-center mb-16 animate-fade-in">
      <div class="text-6xl mb-6">🧠</div>
      <h1 class="text-4xl md:text-5xl font-bold mb-4 bg-gradient-to-r from-blue-600 via-purple-600 to-pink-500 bg-clip-text text-transparent">
        AI 个性化学习系统
      </h1>
      <p class="text-lg text-gray-500 max-w-2xl mx-auto leading-relaxed">
        基于大模型与多智能体协同技术，为你量身定制学习路径、生成个性化资源，让学习更高效
      </p>
    </div>

    <!-- 功能卡片 -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-5 mb-12">
      <div
        v-for="(feature, i) in features"
        :key="i"
        class="group bg-white rounded-2xl p-6 shadow-sm border border-gray-100 hover:shadow-lg hover:border-blue-100 transition-all duration-300 hover:-translate-y-1"
      >
        <div class="text-3xl mb-3 group-hover:scale-110 transition-transform duration-300">
          {{ feature.icon }}
        </div>
        <h3 class="font-semibold text-gray-900 mb-2">{{ feature.title }}</h3>
        <p class="text-sm text-gray-500 leading-relaxed">{{ feature.desc }}</p>
      </div>
    </div>

    <!-- 工作流程 -->
    <div class="bg-white rounded-2xl p-8 shadow-sm border border-gray-100 mb-12">
      <h2 class="text-xl font-bold text-center mb-8">系统工作流程</h2>
      <div class="flex flex-col md:flex-row items-center justify-center gap-4 md:gap-2">
        <div
          v-for="(step, i) in steps"
          :key="i"
          class="flex items-center gap-2"
        >
          <div class="flex flex-col items-center">
            <div class="w-12 h-12 rounded-full bg-gradient-to-br from-blue-500 to-purple-500 text-white flex items-center justify-center text-lg font-bold shadow-md">
              {{ step.icon }}
            </div>
            <span class="text-xs text-gray-500 mt-1.5 text-center max-w-[80px]">{{ step.label }}</span>
          </div>
          <div v-if="i < steps.length - 1" class="hidden md:block text-gray-300 text-xl mx-2">→</div>
        </div>
      </div>
    </div>

    <!-- CTA -->
    <div class="text-center">
      <router-link
        to="/chat"
        class="inline-flex items-center gap-2 bg-gradient-to-r from-blue-600 to-purple-600 text-white px-10 py-4 rounded-xl text-lg font-medium hover:shadow-lg hover:shadow-blue-200 transition-all duration-300 hover:-translate-y-0.5"
      >
        <span>开始学习</span>
        <span>→</span>
      </router-link>
    </div>
  </div>
</template>

<script setup>
const features = [
  {
    icon: '🎯',
    title: '个性化画像',
    desc: '通过自然对话自动构建你的专属学习画像，精准匹配最适合你的学习方式。',
  },
  {
    icon: '🤖',
    title: '多智能体协同',
    desc: '8 个 AI 智能体协同工作，从画像构建到资源生成，全流程智能化。',
  },
  {
    icon: '🔄',
    title: '动态路径规划',
    desc: '学习路径随你的进度动态调整，支持回滚重学，确保每个知识点都掌握。',
  },
  {
    icon: '📄',
    title: '智能文档生成',
    desc: '根据你的认知风格自动生成 Markdown 学习文档，图文并茂通俗易懂。',
  },
  {
    icon: '📊',
    title: 'PPT 课件生成',
    desc: '一键生成专业 PPT 课件，适合系统性学习和复习备考。',
  },
  {
    icon: '📝',
    title: '智能出题测验',
    desc: '自动生成分层试卷，检验你的掌握程度，定位薄弱环节。',
  },
]

const steps = [
  { icon: '💬', label: '对话交流' },
  { icon: '🎯', label: '画像构建' },
  { icon: '🗺️', label: '路径规划' },
  { icon: '📦', label: '资源生成' },
  { icon: '✅', label: '学习完成' },
]
</script>
