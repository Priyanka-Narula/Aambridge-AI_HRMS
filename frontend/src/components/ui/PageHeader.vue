<script setup lang="ts">
defineProps<{
  title: string
  subtitle?: string
  count?: string | number
  compact?: boolean
  size?: 'default' | 'lg'
}>()
</script>

<template>
  <header
    class="hrms-page-header"
    :class="{ 'hrms-page-header--compact': compact }"
  >
    <div>
      <h1
        class="hrms-page-title"
        :class="{ 'hrms-page-title--sm': size === 'default' }"
      >
        {{ title }}
      </h1>
      <p v-if="subtitle" class="hrms-page-subtitle">{{ subtitle }}</p>
      <span v-if="count !== undefined" class="hrms-page-count">{{ count }}</span>
    </div>
    <div v-if="$slots.actions" class="hrms-page-header__actions">
      <slot name="actions" />
    </div>
    <slot />
  </header>
</template>
