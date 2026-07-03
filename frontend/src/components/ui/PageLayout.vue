<script setup lang="ts">
withDefaults(
  defineProps<{
    variant?: 'default' | 'wide' | 'full'
  }>(),
  { variant: 'default' },
)
</script>

<template>
  <div
    class="hrms-page"
    :class="{
      'hrms-page--wide': variant === 'wide',
      'hrms-page--full': variant === 'full',
    }"
  >
    <slot />
  </div>
</template>
