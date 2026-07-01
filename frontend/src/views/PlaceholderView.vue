<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import PageLayout from '@/components/ui/PageLayout.vue'

const route = useRoute()

const pageTitle = computed(() => (route.meta.title as string) ?? 'Page')
</script>

<template>
  <PageLayout>
    <div class="hrms-card hrms-card--dashed hrms-placeholder">
      <h2>{{ pageTitle }}</h2>
      <p>This page is ready for content.</p>
    </div>
  </PageLayout>
</template>
