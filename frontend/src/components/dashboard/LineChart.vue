<script setup lang="ts">
import { computed } from 'vue'
import type { NamedCount } from '@/types/dashboard'

const props = withDefaults(
  defineProps<{
    items: NamedCount[]
    color?: string
    compact?: boolean
  }>(),
  {
    color: '#7c3aed',
    compact: false,
  },
)

const max = computed(() => Math.max(...props.items.map((i) => i.value), 1))
const min = computed(() => 0)
const chartHeight = 40
const yTicksCount = 3

function shortLabel(label: string) {
  const d = new Date(label)
  if (!Number.isNaN(d.getTime())) {
    const month = d.toLocaleString('en-IN', { month: 'short' }).toLowerCase()
    const year2 = String(d.getFullYear()).slice(-2)
    return `${month} ${year2}`
  }

  const m = label.match(/([A-Za-z]{3,9})\s*[-/]?\s*(20\d{2}|\d{2})/)
  if (m) {
    const month = m[1]!.slice(0, 3).toLowerCase()
    const year = m[2]!
    const year2 = year.length === 4 ? year.slice(-2) : year
    return `${month} ${year2}`
  }

  return label.length > 6 ? label.slice(0, 6).toLowerCase() : label.toLowerCase()
}

function fmt(n: number) {
  return new Intl.NumberFormat('en-IN', { notation: 'compact', maximumFractionDigits: 1 }).format(n)
}

const yTicks = computed(() => {
  const span = max.value - min.value
  return Array.from({ length: yTicksCount + 1 }, (_, i) => {
    const ratio = i / yTicksCount
    const value = max.value - span * ratio
    return {
      value,
      label: fmt(value),
      y: ratio * chartHeight,
    }
  })
})

const series = computed(() => {
  const items = props.items
  if (!items.length) return []
  const step = items.length > 1 ? 100 / (items.length - 1) : 0
  return items.map((item, idx) => {
    const x = items.length > 1 ? idx * step : 50
    const y = chartHeight - ((item.value - min.value) / Math.max(max.value - min.value, 1)) * chartHeight
    return {
      ...item,
      x,
      y: Number.isFinite(y) ? y : chartHeight,
      short: shortLabel(item.label),
      displayValue: fmt(item.value),
      isLast: idx === items.length - 1,
    }
  })
})

const points = computed(() => {
  return series.value.map((p) => `${p.x},${p.y}`).join(' ')
})

const areaPoints = computed(() => {
  const s = series.value
  if (!s.length) return ''
  const first = s[0]
  const last = s[s.length - 1]
  if (!first || !last) return ''
  return `${first.x},${chartHeight} ${points.value} ${last.x},${chartHeight}`
})
</script>

<template>
  <div class="line" :class="{ 'line--compact': compact }">
    <svg v-if="items.length" class="line__svg" viewBox="-10 -2 115 48" preserveAspectRatio="none" aria-hidden="true">
      <g class="line__grid">
        <line v-for="tick in yTicks" :key="`grid-${tick.y}`" x1="0" :y1="tick.y" x2="100" :y2="tick.y" />
      </g>
      <g class="line__y-axis">
        <text v-for="tick in yTicks" :key="`label-${tick.y}`" x="-1.5" :y="tick.y + 1" text-anchor="end">
          {{ tick.label }}
        </text>
      </g>
      <polygon class="line__area" :points="areaPoints" :style="{ fill: color }" />
      <polyline class="line__path line__path--bg" :points="points" />
      <polyline class="line__path" :points="points" :style="{ stroke: color }" />
      <g v-for="point in series" :key="point.label">
        <circle
          class="line__dot"
          :class="{ 'line__dot--last': point.isLast }"
          :cx="point.x"
          :cy="point.y"
          :r="point.isLast ? 2.2 : 1.4"
          :style="{ fill: color }"
        />
        <text
          v-if="point.isLast"
          class="line__value"
          :x="point.x"
          :y="point.y - 3.2"
          text-anchor="middle"
        >
          {{ point.displayValue }}
        </text>
      </g>
    </svg>
    <p v-else class="line__empty">No data yet</p>
    <div class="line__labels">
      <span v-for="point in series" :key="point.label" :title="`${point.label}: ${point.value}`">
        {{ point.short }}
      </span>
    </div>
  </div>
</template>

<style scoped>
.line {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.line__svg {
  width: 100%;
  height: 170px;
}

.line--compact .line__svg {
  height: 142px;
}

.line__grid line {
  stroke: rgba(148, 163, 184, 0.22);
  stroke-width: 0.35;
}

.line__grid line:nth-child(2),
.line__grid line:nth-child(3) {
  stroke: rgba(148, 163, 184, 0.14);
}

.line__y-axis text {
  fill: var(--hrms-text-muted);
  font-size: 2.5px;
}

.line__area {
  opacity: 0.14;
}

.line__path {
  fill: none;
  stroke-width: 1.25;
  stroke-linecap: round;
  stroke-linejoin: round;
}

.line__path--bg {
  stroke: rgba(148, 163, 184, 0.35);
  stroke-width: 1.65;
}

.line__dot {
  stroke: #fff;
  stroke-width: 0.5;
  opacity: 0.7;
}

.line__dot--last {
  opacity: 1;
  stroke-width: 0.7;
}

.line__value {
  fill: var(--hrms-primary-dark);
  font-size: 2.8px;
  font-weight: 600;
  paint-order: stroke;
  stroke: #fff;
  stroke-width: 0.55;
}

.line__labels {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(28px, 1fr));
  gap: 4px;
  font-size: 0.7rem;
  color: var(--hrms-text-muted);
}

.line__labels span {
  text-align: center;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.line__empty {
  margin: 18px 0;
  text-align: center;
  color: var(--hrms-text-muted);
  font-size: 0.8rem;
}
</style>
