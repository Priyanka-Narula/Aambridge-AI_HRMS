<script setup lang="ts">
import { computed, ref } from 'vue'
import type { TrendSeries } from '@/types/commandCenter'

const props = defineProps<{ series: TrendSeries[] }>()

const hover = ref<{ label: string; values: Array<{ label: string; value: number; color: string }> } | null>(
  null,
)

const labels = computed(() => props.series.find((series) => series.points.length)?.points.map((p) => p.label) ?? [])
const hasMeaningfulData = computed(() =>
  props.series.some((series) => series.points.some((point) => point.value !== 0)),
)
const max = computed(() => {
  const values = props.series.flatMap((s) => s.points.map((p) => p.value))
  return Math.max(...values, 1)
})

function y(value: number) {
  return 100 - (value / max.value) * 88 - 4
}

function x(index: number, total: number) {
  if (total <= 1) return 50
  return (index / (total - 1)) * 100
}

function seriesPath(series: TrendSeries) {
  return series.points
    .map((point, index) => {
      const px = x(index, series.points.length)
      const py = y(point.value)
      return `${index === 0 ? 'M' : 'L'}${px},${py}`
    })
    .join(' ')
}

function onMove(index: number) {
  const label = labels.value[index]
  if (!label) return
  hover.value = {
    label,
    values: props.series.flatMap((series) => {
      const point = series.points[index]
      return point
        ? [{ label: series.label, value: point.value, color: series.color }]
        : []
    }),
  }
}
</script>

<template>
  <div class="multi" @mouseleave="hover = null">
    <svg
      v-if="labels.length && hasMeaningfulData"
      class="multi__svg"
      viewBox="0 0 100 100"
      preserveAspectRatio="none"
    >
      <line
        v-for="tick in 4"
        :key="tick"
        x1="0"
        :y1="y((max / 3) * (tick - 1))"
        x2="100"
        :y2="y((max / 3) * (tick - 1))"
        class="multi__grid"
      />
      <path
        v-for="item in series"
        :key="item.key"
        :d="seriesPath(item)"
        fill="none"
        :stroke="item.color"
        stroke-width="1.8"
        stroke-linecap="round"
        stroke-linejoin="round"
      />
      <g v-for="(label, index) in labels" :key="label">
        <rect
          :x="x(index, labels.length) - 3"
          y="0"
          width="6"
          height="100"
          fill="transparent"
          @mousemove="onMove(index)"
        />
      </g>
    </svg>
    <p v-else class="multi__empty">Insufficient data.</p>
    <div v-if="labels.length && hasMeaningfulData" class="multi__labels">
      <span v-for="label in labels" :key="label">{{ label }}</span>
    </div>
    <div v-if="labels.length && hasMeaningfulData" class="multi__legend">
      <span v-for="item in series" :key="item.key">
        <i :style="{ background: item.color }" />
        {{ item.label }}
      </span>
    </div>
    <div v-if="hover" class="multi__tooltip" role="tooltip">
      <strong>{{ hover.label }}</strong>
      <p v-for="row in hover.values" :key="row.label">
        <i :style="{ background: row.color }" />
        {{ row.label }}: {{ row.value }}
      </p>
    </div>
  </div>
</template>

<style scoped>
.multi {
  position: relative;
  display: grid;
  gap: 10px;
}
.multi__svg {
  width: 100%;
  height: 260px;
}
.multi__grid {
  stroke: rgba(148, 163, 184, 0.22);
  stroke-width: 0.4;
}
.multi__labels {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(48px, 1fr));
  gap: 4px;
  font-size: 0.68rem;
  color: var(--hrms-text-muted);
}
.multi__labels span {
  text-align: center;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.multi__legend {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  font-size: 0.74rem;
  color: var(--hrms-text-muted);
}
.multi__legend span,
.multi__tooltip p {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}
.multi__legend i,
.multi__tooltip i {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}
.multi__tooltip {
  position: absolute;
  top: 12px;
  right: 12px;
  min-width: 150px;
  padding: 10px 12px;
  border: 1px solid var(--hrms-border);
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.96);
  box-shadow: var(--hrms-shadow-sm);
  font-size: 0.74rem;
}
.multi__tooltip strong {
  display: block;
  margin-bottom: 6px;
  color: var(--hrms-primary-dark);
}
.multi__tooltip p {
  margin: 4px 0 0;
}
.multi__empty {
  margin: 48px 0;
  text-align: center;
  color: var(--hrms-text-muted);
}
</style>
