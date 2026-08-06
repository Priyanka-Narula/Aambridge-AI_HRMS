<script setup lang="ts">
import { computed } from 'vue'
import type { NamedCount } from '@/types/dashboard'

const props = withDefaults(
  defineProps<{
    items: NamedCount[]
    color?: string
    horizontal?: boolean
    compact?: boolean
  }>(),
  {
    color: '#7a3b68',
    horizontal: false,
    compact: false,
  },
)
const max = computed(() => Math.max(...props.items.map((i) => i.value), 1))
</script>

<template>
  <div v-if="horizontal" class="hbar" :class="{ 'hbar--compact': compact }">
    <div v-for="item in items" :key="item.label" class="hbar__row">
      <span class="hbar__label" :title="item.label">{{ item.label }}</span>
      <div class="hbar__track">
        <div
          class="hbar__fill"
          :style="{ width: `${(item.value / max) * 100}%`, background: color }"
        />
      </div>
      <strong class="hbar__value">{{ item.value }}</strong>
    </div>
    <p v-if="!items.length" class="chart-empty">No data yet</p>
  </div>
  <div v-else class="vbar" :class="{ 'vbar--compact': compact }">
    <div v-for="item in items" :key="item.label" class="vbar__col" :title="`${item.label}: ${item.value}`">
      <span class="vbar__value">{{ item.value }}</span>
      <div class="vbar__track">
        <div
          class="vbar__fill"
          :style="{
            height: `${Math.max((item.value / max) * 100, item.value > 0 ? 6 : 0)}%`,
            background: color,
          }"
        />
      </div>
      <span class="vbar__label">{{ item.label }}</span>
    </div>
    <p v-if="!items.length" class="chart-empty">No data yet</p>
  </div>
</template>

<style scoped>
.hbar {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.hbar--compact {
  gap: 7px;
}
.hbar__row {
  display: grid;
  grid-template-columns: minmax(72px, 120px) 1fr 36px;
  gap: 10px;
  align-items: center;
}
.hbar--compact .hbar__row {
  grid-template-columns: minmax(56px, 96px) 1fr 28px;
  gap: 8px;
}
.hbar__label {
  font-size: 0.78rem;
  color: var(--hrms-text-muted);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.hbar--compact .hbar__label {
  font-size: 0.72rem;
}
.hbar__track {
  height: 10px;
  border-radius: 999px;
  background: color-mix(in srgb, var(--hrms-surface-muted) 85%, white);
  overflow: hidden;
}
.hbar--compact .hbar__track {
  height: 8px;
}.hbar__fill {
  height: 100%;
  border-radius: 999px;
  transition: width 0.35s ease;
}
.hbar__value {
  font-size: 0.8rem;
  text-align: right;
  font-variant-numeric: tabular-nums;
}
.vbar {
  display: flex;
  align-items: flex-end;
  gap: 10px;
  min-height: 180px;
  overflow-x: auto;
  padding-top: 8px;
}
.vbar--compact {
  min-height: 120px;
  gap: 6px;
  padding-top: 4px;
}.vbar__col {
  flex: 1 1 0;
  min-width: 48px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
}
.vbar--compact .vbar__col {
  min-width: 36px;
  gap: 4px;
}.vbar__value {
  font-size: 0.72rem;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
}
.vbar__track {
  width: 100%;
  max-width: 36px;
  height: 120px;
  display: flex;
  align-items: flex-end;
  border-radius: 8px 8px 3px 3px;
  background: color-mix(in srgb, var(--hrms-surface-muted) 85%, white);
}
.vbar--compact .vbar__track {
  max-width: 28px;
  height: 76px;
}.vbar__fill {
  width: 100%;
  border-radius: 8px 8px 2px 2px;
  transition: height 0.35s ease;
}
.vbar__label {
  font-size: 0.65rem;
  text-align: center;
  color: var(--hrms-text-muted);
  line-height: 1.2;
  max-width: 64px;
}
.chart-empty {
  margin: 24px 0;
  text-align: center;
  color: var(--hrms-text-muted);
  font-size: 0.85rem;
}
</style>
