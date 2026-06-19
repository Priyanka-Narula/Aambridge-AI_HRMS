<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()

const pageTitle = computed(() => (route.meta.title as string) ?? 'Page')
</script>

<template>
  <div class="placeholder">
    <div class="placeholder__card">
      <h2>{{ pageTitle }}</h2>
      <p>This page is ready for content.</p>
    </div>
  </div>
</template>

<style scoped>
.placeholder__card {
  padding: 40px;
  text-align: center;
  background: var(--hrms-surface-elevated);
  border: 1px dashed var(--hrms-border-strong);
  border-radius: var(--hrms-radius-lg);
}

.placeholder__card h2 {
  margin: 0 0 12px;
  font-family: var(--hrms-font-display);
  font-size: 1.5rem;
  color: var(--hrms-primary-dark);
}

.placeholder__card p {
  margin: 0;
  max-width: 480px;
  margin-inline: auto;
  font-size: 0.9rem;
  color: var(--hrms-text-muted);
  line-height: 1.6;
}
</style>
