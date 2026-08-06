<script setup lang="ts">
import { computed } from 'vue'
import type { HeatmapCell } from '@/types/dashboard'

const props = withDefaults(
  defineProps<{
    cells: HeatmapCell[]
    compact?: boolean
  }>(),
  { compact: false },
)

const days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
const hours = [9, 10, 11, 12, 13, 14, 15, 16, 17, 18]

const max = computed(() => Math.max(...props.cells.map((c) => c.value), 1))

const matrix = computed(() => {
  const map = new Map(props.cells.map((c) => [`${c.dow}-${c.hour}`, c.value]))
  return days.map((_, dow) =>
    hours.map((hour) => ({
      dow,
      hour,
      value: map.get(`${dow}-${hour}`) ?? 0,
    })),
  )
})

function intensity(value: number) {
  if (!value) return 'transparent'
  const t = value / max.value
  return `color-mix(in srgb, #7a3b68 ${Math.round(18 + t * 82)}%, white)`
}
</script>

<template>
  <div class="heat" :class="{ 'heat--compact': compact }">
    <div class="heat__hours">
      <span />
      <span v-for="h in hours" :key="h">{{ h }}</span>
    </div>
    <div v-for="(row, dow) in matrix" :key="days[dow]" class="heat__row">
      <span class="heat__day">{{ days[dow] }}</span>
      <div
        v-for="cell in row"
        :key="`${cell.dow}-${cell.hour}`"
        class="heat__cell"
        :style="{ background: intensity(cell.value) }"
        :title="`${days[dow]} ${cell.hour}:00 · ${cell.value}`"
      />
    </div>
  </div>
</template>

<style scoped>
.heat {
  display: flex;
  flex-direction: column;
  gap: 4px;
  overflow-x: auto;
}
.heat__hours,
.heat__row {
  display: grid;
  grid-template-columns: 40px repeat(10, minmax(22px, 1fr));
  gap: 4px;
  align-items: center;
}
.heat__hours span {
  font-size: 0.65rem;
  color: var(--hrms-text-muted);
  text-align: center;
}
.heat__day {
  font-size: 0.7rem;
  color: var(--hrms-text-muted);
}
.heat__cell {
  aspect-ratio: 1;
  border-radius: 4px;
  border: 1px solid var(--hrms-border);
  min-height: 18px;
}
.heat--compact .heat__cell {
  min-height: 14px;
  border-radius: 3px;
}
.heat--compact .heat__hours span,
.heat--compact .heat__day {
  font-size: 0.6rem;
}</style>
