<script setup lang="ts">
import { computed } from 'vue'
import type { SparkPoint } from '@/types/commandCenter'

const props = withDefaults(
  defineProps<{
    points: SparkPoint[]
    color?: string
  }>(),
  { color: '#7c3aed' },
)

const path = computed(() => {
  if (!props.points.length) return ''
  const max = Math.max(...props.points.map((p) => p.value), 1)
  const min = Math.min(...props.points.map((p) => p.value), 0)
  const span = Math.max(max - min, 1)
  return props.points
    .map((point, index) => {
      const x = props.points.length === 1 ? 50 : (index / (props.points.length - 1)) * 100
      const y = 28 - ((point.value - min) / span) * 24
      return `${index === 0 ? 'M' : 'L'}${x.toFixed(1)},${y.toFixed(1)}`
    })
    .join(' ')
})
</script>

<template>
  <svg class="spark" viewBox="0 0 100 32" preserveAspectRatio="none" aria-hidden="true">
    <path v-if="path" :d="path" fill="none" :stroke="color" stroke-width="2" stroke-linecap="round" />
  </svg>
</template>

<style scoped>
.spark {
  width: 100%;
  height: 28px;
  display: block;
}
</style>
