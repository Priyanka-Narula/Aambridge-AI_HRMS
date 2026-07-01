<script setup lang="ts">
import { computed } from 'vue'
import { useAuthStore } from '@/stores/auth'
import PageHeader from '@/components/ui/PageHeader.vue'
import PageLayout from '@/components/ui/PageLayout.vue'

const auth = useAuthStore()

const greeting = computed(() => {
  const hour = new Date().getHours()
  if (hour < 12) return 'Good morning'
  if (hour < 17) return 'Good afternoon'
  return 'Good evening'
})

const stats = [
  { label: 'Open Roles', value: '12', trend: '+2 this week' },
  { label: 'Active Candidates', value: '48', trend: '+8 this week' },
  { label: 'Interviews Today', value: '5', trend: '2 pending' },
  { label: 'Offers Extended', value: '3', trend: '1 accepted' },
]
</script>

<template>
  <PageLayout>
    <PageHeader
      :title="`${greeting}, ${auth.user?.first_name}`"
      :subtitle="`Here's your hiring overview for ${auth.dateRange.start} to ${auth.dateRange.end}`"
    />

    <section class="hrms-stats" aria-label="Key metrics">
      <article v-for="stat in stats" :key="stat.label" class="hrms-stat-card">
        <span class="hrms-stat-card__label">{{ stat.label }}</span>
        <span class="hrms-stat-card__value">{{ stat.value }}</span>
        <span class="hrms-stat-card__meta">{{ stat.trend }}</span>
      </article>
    </section>

    <section class="hrms-card hrms-card--highlight">
      <div class="hrms-card__body">
        <h3 class="hrms-form-section__title">Welcome to Aambridge AI HRMS</h3>
        <p class="hrms-page-subtitle">
          Your layout shell is ready. Navigation adapts to your role
          (<strong>{{ auth.roleLabel }}</strong>), and the date filter in the top bar
          applies across all pages.
        </p>
      </div>
    </section>
  </PageLayout>
</template>

<style scoped>
.hrms-page-subtitle strong {
  color: var(--hrms-primary);
  font-weight: 600;
}
</style>
