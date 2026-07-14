<template>
  <div class="radar-wrapper" :style="{ width: size + 'px', height: size + 'px' }">
    <svg
      :viewBox="`0 0 ${viewBox} ${viewBox}`"
      class="w-full h-full"
    >
      <!-- 网格同心多边形 -->
      <polygon
        v-for="level in gridLevels"
        :key="level"
        :points="gridPoints(level / 100 * radius)"
        fill="none"
        stroke="currentColor"
        :class="level === 100 ? 'stroke-white/20' : 'stroke-white/8'"
        :stroke-width="level === 100 ? 1 : 0.5"
      />

      <!-- 径向轴线 -->
      <line
        v-for="(_, i) in dimensions"
        :key="'axis-' + i"
        :x1="cx"
        :y1="cy"
        :x2="axisEnd(i, radius)"
        :y2="axisEndY(i, radius)"
        stroke="currentColor"
        class="stroke-white/10"
        stroke-width="0.5"
      />

      <!-- 数据多边形 -->
      <polygon
        :points="dataPoints"
        fill="url(#radarGradient)"
        class="opacity-80"
        stroke="url(#radarStrokeGradient)"
        stroke-width="2"
      />

      <!-- 数据点 -->
      <circle
        v-for="(_, i) in dimensions"
        :key="'dot-' + i"
        :cx="dataPointX(i)"
        :cy="dataPointY(i)"
        r="3.5"
        class="fill-blue-300"
        stroke="#1e293b"
        stroke-width="1.5"
      />

      <!-- 标注 -->
      <text
        v-for="(dim, i) in dimensions"
        :key="'label-' + i"
        :x="labelX(i)"
        :y="labelY(i)"
        class="fill-gray-300 text-center select-none"
        font-size="11"
        :text-anchor="textAnchor(i)"
        :dominant-baseline="dominantBaseline(i)"
      >
        {{ dim.name }}
      </text>

      <!-- 刻度值 -->
      <text
        v-for="(v, i) in [20, 40, 60, 80]"
        :key="'tick-' + v"
        :x="cx + 4"
        :y="cy - (v / 100 * radius) + 3"
        class="fill-gray-600 select-none"
        font-size="8"
      >
        {{ v }}
      </text>

      <!-- 渐变定义 -->
      <defs>
        <linearGradient id="radarGradient" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stop-color="#3b82f6" stop-opacity="0.5" />
          <stop offset="100%" stop-color="#8b5cf6" stop-opacity="0.35" />
        </linearGradient>
        <linearGradient id="radarStrokeGradient" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stop-color="#60a5fa" />
          <stop offset="100%" stop-color="#a78bfa" />
        </linearGradient>
      </defs>
    </svg>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  dimensions: {
    type: Array,
    required: true,
    // [{ name: string, score: number }]  score: 0~100
  },
  size: {
    type: Number,
    default: 360,
  },
})

const viewBox = 400
const cx = viewBox / 2
const cy = viewBox / 2
const radius = 140
const labelOffset = 22
const gridLevels = [20, 40, 60, 80, 100]
const count = computed(() => props.dimensions.length)
const angleStep = computed(() => (2 * Math.PI) / count.value)

function axisAngle(i) {
  // 从正上方（-π/2）开始顺时针排列
  return -Math.PI / 2 + i * angleStep.value
}

function axisEnd(i, r) {
  return cx + r * Math.cos(axisAngle(i))
}
function axisEndY(i, r) {
  return cy + r * Math.sin(axisAngle(i))
}

function gridPoints(r) {
  const pts = []
  for (let i = 0; i < count.value; i++) {
    const angle = axisAngle(i)
    pts.push(`${cx + r * Math.cos(angle)},${cy + r * Math.sin(angle)}`)
  }
  return pts.join(' ')
}

function scoreRadius(i) {
  const score = props.dimensions[i]?.score || 0
  return (score / 100) * radius
}

function dataPointX(i) {
  return cx + scoreRadius(i) * Math.cos(axisAngle(i))
}
function dataPointY(i) {
  return cy + scoreRadius(i) * Math.sin(axisAngle(i))
}

const dataPoints = computed(() => {
  const pts = []
  for (let i = 0; i < count.value; i++) {
    pts.push(`${dataPointX(i)},${dataPointY(i)}`)
  }
  return pts.join(' ')
})

function labelX(i) {
  return cx + (radius + labelOffset) * Math.cos(axisAngle(i))
}
function labelY(i) {
  return cy + (radius + labelOffset) * Math.sin(axisAngle(i))
}

function textAnchor(i) {
  const a = axisAngle(i)
  // 在 x 轴附近用 middle，左边用 end，右边用 start
  if (Math.abs(Math.cos(a)) < 0.1) return 'middle'
  return Math.cos(a) > 0 ? 'start' : 'end'
}

function dominantBaseline(i) {
  const a = axisAngle(i)
  if (Math.abs(Math.sin(a)) < 0.1) return 'middle'
  return Math.sin(a) > 0 ? 'top' : 'bottom'
}
</script>

<style scoped>
.radar-wrapper {
  margin: 0 auto;
}
</style>
