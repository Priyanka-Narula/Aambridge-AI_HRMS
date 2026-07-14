<script setup lang="ts">
import AambridgeLogo from '@/assets/Aambridge logo.svg'

withDefaults(
  defineProps<{
    variant?: 'sidebar' | 'auth'
  }>(),
  { variant: 'auth' },
)
</script>

<template>
  <img
    :src="AambridgeLogo"
    alt="Aambridge"
    class="app-logo"
    :class="`app-logo--${variant}`"
  />
</template>

<style scoped>
.app-logo {
  display: block;
  object-fit: contain;
}

.app-logo--auth {
  width: min(220px, 78vw);
  height: auto;
  margin: 0 auto 4px;
}

.app-logo--sidebar {
  width: 100%;
  max-width: 152px;
  height: auto;
}
</style>
