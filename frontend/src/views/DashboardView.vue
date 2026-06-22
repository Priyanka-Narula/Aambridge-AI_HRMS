<script setup lang="ts">
import { computed } from 'vue'
import { useAuthStore } from '@/stores/auth'

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
  <div class="dashboard">
    <header class="dashboard__header">
      <div>
        <h2 class="dashboard__greeting">{{ greeting }}, {{ auth.user.name.split(' ')[0] }}</h2>
        <p class="dashboard__subtitle">
          Here's your hiring overview for
          <strong>{{ auth.dateRange.start }}</strong> to <strong>{{ auth.dateRange.end }}</strong>
        </p>
      </div>
    </header>

    <section class="dashboard__stats" aria-label="Key metrics">
      <article v-for="stat in stats" :key="stat.label" class="dashboard__stat-card">
        <span class="dashboard__stat-label">{{ stat.label }}</span>
        <span class="dashboard__stat-value">{{ stat.value }}</span>
        <span class="dashboard__stat-trend">{{ stat.trend }}</span>
      </article>
    </section>

    <section class="dashboard__welcome">
      <div class="dashboard__welcome-card">
        <h3>Welcome to Aambridge AI HRMS</h3>
        <p>
          Your layout shell is ready. Navigation adapts to your role
          (<strong>{{ auth.roleLabel }}</strong>), and the date filter in the top bar
          applies across all pages.
        </p>
      </div>
    </section>
  </div>
</template>

<style scoped>
.dashboard__header {
  margin-bottom: 28px;
}

.dashboard__greeting {
  margin: 0 0 6px;
  font-family: var(--hrms-font-display);
  font-size: 1.75rem;
  font-weight: 600;
  color: var(--hrms-primary-dark);
}

.dashboard__subtitle {
  margin: 0;
  font-size: 0.9rem;
  color: var(--hrms-text-muted);
}

.dashboard__subtitle strong {
  color: var(--hrms-primary);
  font-weight: 600;
}

.dashboard__stats {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 16px;
  margin-bottom: 28px;
}

.dashboard__stat-card {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 20px;
  background: var(--hrms-surface-elevated);
  border: 1px solid var(--hrms-border);
  border-radius: var(--hrms-radius-lg);
  box-shadow: var(--hrms-shadow-sm);
  transition:
    box-shadow var(--hrms-transition),
    border-color var(--hrms-transition);
}

.dashboard__stat-card:hover {
  border-color: var(--hrms-primary-muted);
  box-shadow: var(--hrms-shadow-md);
}

.dashboard__stat-label {
  font-size: 0.8rem;
  font-weight: 500;
  color: var(--hrms-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.dashboard__stat-value {
  font-family: var(--hrms-font-display);
  font-size: 2rem;
  font-weight: 700;
  color: var(--hrms-primary-dark);
  line-height: 1.1;
}

.dashboard__stat-trend {
  font-size: 0.78rem;
  color: var(--hrms-accent-hover);
}

.dashboard__welcome-card {
  padding: 28px;
  background: linear-gradient(135deg, var(--hrms-secondary) 0%, var(--hrms-surface-elevated) 100%);
  border: 1px solid var(--hrms-border);
  border-radius: var(--hrms-radius-lg);
  border-left: 4px solid var(--hrms-accent);
}

.dashboard__welcome-card h3 {
  margin: 0 0 10px;
  font-family: var(--hrms-font-display);
  font-size: 1.25rem;
  color: var(--hrms-primary-dark);
}

.dashboard__welcome-card p {
  margin: 0;
  font-size: 0.9rem;
  line-height: 1.6;
  color: var(--hrms-text-muted);
}

.dashboard__welcome-card strong {
  color: var(--hrms-primary);
}
</style>
