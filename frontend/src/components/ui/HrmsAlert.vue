<script setup lang="ts">
defineProps<{
  type?: 'error' | 'success' | 'warning' | 'info'
  dismissible?: boolean
}>()

const emit = defineEmits<{ dismiss: [] }>()
</script>

<template>
  <div
    class="hrms-alert"
    :class="`hrms-alert--${type ?? 'info'}`"
    role="alert"
  >
    <div class="hrms-alert__content">
      <slot />
    </div>
    <button
      v-if="dismissible"
      type="button"
      class="hrms-alert__dismiss"
      aria-label="Dismiss"
      @click="emit('dismiss')"
    >
      x
    </button>
  </div>
</template>
