<script setup lang="ts">
import { computed } from 'vue'
import type { NamedCount } from '@/types/dashboard'

const props = withDefaults(
  defineProps<{
    items: NamedCount[]
    colors?: string[]
    compact?: boolean
  }>(),
  {
    colors: () => ['#7a3b68', '#c4a35a', '#0ea5e9', '#22c55e', '#8b5cf6', '#ef4444', '#94a3b8'],
    compact: false,
  },
)
const total = computed(() => props.items.reduce((s, i) => s + i.value, 0) || 1)

const slices = computed(() => {
  const r = 42
  const c = 2 * Math.PI * r
  let offset = 0
  return props.items.map((item, idx) => {
    const pct = item.value / total.value
    const len = pct * c
    const slice = {
      ...item,
      color: props.colors[idx % props.colors.length]!,
      dash: `${len} ${c - len}`,
      offset: -offset,
      pct: Math.round(pct * 100),
    }
    offset += len
    return slice
  })
})
</script>

<template>
  <div class="donut" :class="{ 'donut--compact': compact }">
    <svg viewBox="0 0 120 120" class="donut__svg" aria-hidden="true">
      <circle cx="60" cy="60" r="42" fill="none" stroke="rgba(0,0,0,0.06)" stroke-width="14" />
      <circle
        v-for="(s, i) in slices"
        :key="s.label + i"
        cx="60"
        cy="60"
        r="42"
        fill="none"
        :stroke="s.color"
        stroke-width="14"
        stroke-linecap="butt"
        :stroke-dasharray="s.dash"
        :stroke-dashoffset="s.offset"
        transform="rotate(-90 60 60)"
      />
      <text x="60" y="56" text-anchor="middle" class="donut__total">{{ total === 1 && items.every(i => i.value === 0) ? 0 : items.reduce((a, b) => a + b.value, 0) }}</text>
      <text x="60" y="72" text-anchor="middle" class="donut__caption">total</text>
    </svg>
    <ul class="donut__legend">
      <li v-for="(s, i) in slices" :key="s.label + i">
        <i :style="{ background: s.color }" />
        <span>{{ s.label }}</span>
        <strong>{{ s.value }}</strong>
      </li>
    </ul>
  </div>
</template>

<style scoped>
.donut {
  display: grid;
  grid-template-columns: 140px 1fr;
  gap: 16px;
  align-items: center;
}
.donut--compact {
  grid-template-columns: 96px 1fr;
  gap: 10px;
}
.donut__svg {
  width: 140px;
  height: 140px;
}
.donut--compact .donut__svg {
  width: 96px;
  height: 96px;
}
.donut__total {
  font-size: 18px;
  font-weight: 700;
  fill: var(--hrms-primary-dark);
}
.donut--compact .donut__total {
  font-size: 14px;
}
.donut__caption {
  font-size: 10px;
  fill: var(--hrms-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.06em;
}
.donut--compact .donut__caption {
  font-size: 8px;
}
.donut__legend {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.donut--compact .donut__legend {
  gap: 5px;
}
.donut__legend li {
  display: grid;
  grid-template-columns: 10px 1fr auto;
  gap: 8px;
  align-items: center;
  font-size: 0.8rem;
  color: var(--hrms-text-muted);
}
.donut--compact .donut__legend li {
  font-size: 0.72rem;
  gap: 6px;
}.donut__legend i {
  width: 10px;
  height: 10px;
  border-radius: 3px;
}
.donut__legend strong {
  color: var(--hrms-text);
  font-variant-numeric: tabular-nums;
}
@media (max-width: 560px) {
  .donut {
    grid-template-columns: 1fr;
    justify-items: center;
  }
}
</style>
