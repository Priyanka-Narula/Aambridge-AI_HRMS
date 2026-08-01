<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { fetchRecruiterPerformance } from '@/api/dashboard'
import LineChart from '@/components/dashboard/LineChart.vue'
import type { RecruiterMetrics, RecruiterPerformancePeriod } from '@/types/dashboard'

const props = defineProps<{ refreshKey?: number }>()

const recruiters = ref<RecruiterMetrics[]>([])
const industries = ref<string[]>([])
const industry = ref('')
const period = ref<RecruiterPerformancePeriod>('monthly')
const selectedRecruiterId = ref<string | null>(null)
const loading = ref(true)
const error = ref('')

const selectedRecruiter = computed(
  () => recruiters.value.find((recruiter) => recruiter.recruiter_id === selectedRecruiterId.value) ?? null,
)
const summary = computed(() => {
  const placements = recruiters.value.reduce(
    (total, recruiter) => total + recruiter.positions_closed_total,
    0,
  )
  const averageScore = recruiters.value.length
    ? recruiters.value.reduce((total, recruiter) => total + recruiter.productivity_score, 0)
      / recruiters.value.length
    : 0
  return { placements, averageScore }
})
const periodLabel = computed(() => (period.value === 'monthly' ? 'this month' : 'so far'))
const scoreComponents = computed(() => {
  if (!selectedRecruiter.value) return []
  const breakdown = selectedRecruiter.value.score_breakdown
  return [
    { label: 'Placements', weight: '35%', value: breakdown.placements },
    { label: 'Interviews', weight: '25%', value: breakdown.interviews },
    { label: 'Submission quality', weight: '15%', value: breakdown.submission_quality },
    { label: 'Offer acceptance', weight: '15%', value: breakdown.offer_acceptance },
    { label: 'Response time', weight: '10%', value: breakdown.response_time },
  ]
})

function formatRate(value: number) {
  return `${value.toFixed(1)}%`
}

function formatDays(value: number | null) {
  return value == null ? '—' : `${value.toFixed(1)} days`
}

function selectRecruiter(recruiterId: string) {
  selectedRecruiterId.value = recruiterId
}

async function load() {
  loading.value = true
  error.value = ''
  try {
    const response = await fetchRecruiterPerformance({
      period: period.value,
      industry: industry.value || undefined,
    })
    recruiters.value = response.recruiters
    industries.value = response.industries
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Failed to load recruiter performance'
  } finally {
    loading.value = false
  }
}

watch(() => props.refreshKey, () => void load(), { immediate: true })
watch([period, industry], () => {
  selectedRecruiterId.value = null
  void load()
})
</script>

<template>
  <section class="performance">
    <header class="performance__head">
      <div>
        <h2>Recruiter productivity</h2>
        <p>Ranked by placements, interviews, quality, offer acceptance, and response time.</p>
      </div>
      <div class="performance__controls">
        <div class="period-toggle" role="group" aria-label="Recruiter performance period">
          <button
            type="button"
            :class="{ 'is-active': period === 'monthly' }"
            @click="period = 'monthly'"
          >
            Monthly
          </button>
          <button
            type="button"
            :class="{ 'is-active': period === 'till_date' }"
            @click="period = 'till_date'"
          >
            Till date
          </button>
        </div>
        <label class="performance__filter">
          <span>Industry</span>
          <select v-model="industry" aria-label="Filter recruiter performance by industry">
            <option value="">All industries</option>
            <option v-for="item in industries" :key="item" :value="item">{{ item }}</option>
          </select>
        </label>
      </div>
    </header>

    <div class="performance__summary">
      <div>
        <span>Positions closed {{ periodLabel }}</span>
        <strong>{{ summary.placements }}</strong>
      </div>
      <div>
        <span>Average productivity score</span>
        <strong>{{ formatRate(summary.averageScore) }}</strong>
      </div>
      <div>
        <span>Active recruiters</span>
        <strong>{{ recruiters.length }}</strong>
      </div>
    </div>

    <p v-if="loading" class="performance__empty">Loading recruiter productivity…</p>
    <p v-else-if="error" class="performance__error">{{ error }}</p>
    <p v-else-if="!recruiters.length" class="performance__empty">
      No active recruiters found for this filter.
    </p>

    <div v-else class="leaderboard">
      <p class="leaderboard__hint">Select a bar to inspect the score and hiring metrics.</p>
      <button
        v-for="(recruiter, index) in recruiters"
        :key="recruiter.recruiter_id"
        type="button"
        class="leaderboard__row"
        :class="{ 'is-selected': selectedRecruiterId === recruiter.recruiter_id }"
        :aria-pressed="selectedRecruiterId === recruiter.recruiter_id"
        @click="selectRecruiter(recruiter.recruiter_id)"
      >
        <span class="leaderboard__rank">{{ index + 1 }}</span>
        <span class="leaderboard__name">{{ recruiter.name }}</span>
        <span class="leaderboard__track" aria-hidden="true">
          <span class="leaderboard__fill" :style="{ width: `${recruiter.productivity_score}%` }" />
        </span>
        <strong class="leaderboard__score">{{ formatRate(recruiter.productivity_score) }}</strong>
      </button>
    </div>

    <section v-if="selectedRecruiter" class="detail" aria-live="polite">
      <header class="detail__head">
        <div>
          <p>Recruiter detail</p>
          <h3>{{ selectedRecruiter.name }}</h3>
        </div>
        <div class="detail__score">
          <span>Productivity score</span>
          <strong>{{ formatRate(selectedRecruiter.productivity_score) }}</strong>
        </div>
      </header>

      <div class="detail__breakdown">
        <div v-for="component in scoreComponents" :key="component.label" class="component">
          <div>
            <span>{{ component.label }}</span>
            <small>{{ component.weight }} weight</small>
          </div>
          <span class="component__track">
            <span class="component__fill" :style="{ width: `${component.value}%` }" />
          </span>
          <strong>{{ formatRate(component.value) }}</strong>
        </div>
      </div>

      <div class="detail__body">
        <div class="detail__metrics">
          <div><span>Positions closed</span><strong>{{ selectedRecruiter.positions_closed_total }}</strong></div>
          <div><span>Closed this month</span><strong>{{ selectedRecruiter.positions_closed_this_month }}</strong></div>
          <div><span>Submissions</span><strong>{{ selectedRecruiter.submissions_total }}</strong></div>
          <div><span>Submission quality</span><strong>{{ formatRate(selectedRecruiter.submission_quality) }}</strong><small>{{ selectedRecruiter.approved_submissions }} approved</small></div>
          <div><span>Interviews</span><strong>{{ selectedRecruiter.interviews_total }}</strong></div>
          <div><span>Offers</span><strong>{{ selectedRecruiter.offers_total }}</strong><small>{{ selectedRecruiter.accepted_offers }} accepted</small></div>
          <div><span>Offer acceptance</span><strong>{{ formatRate(selectedRecruiter.offer_acceptance_rate) }}</strong></div>
          <div><span>Avg. response time</span><strong>{{ formatDays(selectedRecruiter.avg_response_days) }}</strong></div>
          <div><span>Avg. time to hire</span><strong>{{ formatDays(selectedRecruiter.avg_time_to_hire_days) }}</strong></div>
        </div>
        <div class="detail__trend">
          <h4>Placement trend</h4>
          <LineChart compact :items="selectedRecruiter.placements_monthly" color="#8b5cf6" />
        </div>
      </div>
    </section>
  </section>
</template>

<style scoped>
.performance {
  grid-column: 1 / -1;
  padding: 18px;
  border: 1px solid var(--hrms-border);
  border-radius: 16px;
  background: linear-gradient(180deg, #ffffff 0%, #fdfbff 100%);
  box-shadow: var(--hrms-shadow-sm);
}
.performance__head, .performance__controls, .performance__summary, .detail__head, .component { display: flex; align-items: center; }
.performance__head { justify-content: space-between; gap: 16px; margin-bottom: 16px; }
.performance__head h2, .detail__head h3, .detail__trend h4 { margin: 0; color: var(--hrms-primary-dark); }
.performance__head h2 { font-size: 1rem; }
.performance__head p { margin: 4px 0 0; font-size: 0.78rem; color: var(--hrms-text-muted); }
.performance__controls { gap: 10px; }
.period-toggle { display: inline-flex; padding: 3px; border: 1px solid var(--hrms-border); border-radius: 9px; background: var(--hrms-surface-muted); }
.period-toggle button { padding: 6px 9px; border: 0; border-radius: 6px; color: var(--hrms-text-muted); background: transparent; font-size: 0.73rem; font-weight: 650; cursor: pointer; }
.period-toggle button.is-active { color: #fff; background: var(--hrms-primary); }
.performance__filter { display: grid; gap: 3px; min-width: 150px; font-size: 0.7rem; font-weight: 600; color: var(--hrms-text-muted); }
.performance__filter select { width: 100%; padding: 6px 8px; border: 1px solid var(--hrms-border); border-radius: 8px; color: var(--hrms-text); background: var(--hrms-surface); }
.performance__summary { margin-bottom: 16px; overflow: hidden; border: 1px solid var(--hrms-border); border-radius: 12px; }
.performance__summary div { flex: 1; display: grid; gap: 3px; padding: 12px 14px; border-right: 1px solid var(--hrms-border); }
.performance__summary div:last-child { border-right: 0; }
.performance__summary span, .detail__score span, .detail__metrics span, .detail__metrics small, .component small { font-size: 0.7rem; color: var(--hrms-text-muted); }
.performance__summary strong { font-size: 1.12rem; color: var(--hrms-primary-dark); }
.leaderboard { display: grid; gap: 6px; }
.leaderboard__hint { margin: 0 0 4px; font-size: 0.75rem; color: var(--hrms-text-muted); }
.leaderboard__row { display: grid; grid-template-columns: 24px minmax(110px, 180px) 1fr 48px; gap: 10px; align-items: center; width: 100%; padding: 9px 10px; border: 1px solid transparent; border-radius: 10px; color: inherit; background: transparent; text-align: left; cursor: pointer; }
.leaderboard__row:hover, .leaderboard__row.is-selected { border-color: color-mix(in srgb, var(--hrms-primary) 40%, var(--hrms-border)); background: color-mix(in srgb, var(--hrms-primary) 5%, white); }
.leaderboard__rank { font-size: 0.72rem; color: var(--hrms-text-muted); font-variant-numeric: tabular-nums; }
.leaderboard__name { overflow: hidden; color: var(--hrms-text); font-size: 0.84rem; font-weight: 650; text-overflow: ellipsis; white-space: nowrap; }
.leaderboard__track, .component__track { display: block; overflow: hidden; background: color-mix(in srgb, var(--hrms-surface-muted) 85%, white); }
.leaderboard__track { height: 10px; border-radius: 999px; }
.leaderboard__fill, .component__fill { display: block; height: 100%; border-radius: inherit; background: linear-gradient(90deg, var(--hrms-primary), #a78bfa); transition: width 0.35s ease; }
.leaderboard__score { color: var(--hrms-primary-dark); font-size: 0.8rem; text-align: right; font-variant-numeric: tabular-nums; }
.detail { margin-top: 18px; padding: 16px; border: 1px solid color-mix(in srgb, var(--hrms-primary) 40%, var(--hrms-border)); border-radius: 12px; background: color-mix(in srgb, var(--hrms-primary) 4%, white); }
.detail__head { justify-content: space-between; gap: 16px; margin-bottom: 14px; }
.detail__head p { margin: 0 0 3px; color: var(--hrms-text-muted); font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.05em; }
.detail__head h3 { font-size: 1rem; }
.detail__score { display: grid; gap: 3px; text-align: right; }
.detail__score strong { color: var(--hrms-primary-dark); font-size: 1.25rem; }
.detail__breakdown { display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: 8px; margin-bottom: 16px; }
.component { display: grid; grid-template-columns: 1fr; gap: 5px; padding: 9px; border: 1px solid var(--hrms-border); border-radius: 8px; background: var(--hrms-surface); }
.component > div { display: flex; justify-content: space-between; gap: 6px; }
.component > div span { font-size: 0.7rem; color: var(--hrms-text); }
.component__track { height: 6px; border-radius: 999px; }
.component strong { color: var(--hrms-primary-dark); font-size: 0.78rem; }
.detail__body { display: grid; grid-template-columns: minmax(0, 1.25fr) minmax(240px, 1fr); gap: 18px; }
.detail__metrics { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 8px; align-content: start; }
.detail__metrics div { display: grid; gap: 3px; min-height: 64px; padding: 9px; border: 1px solid var(--hrms-border); border-radius: 8px; background: var(--hrms-surface); }
.detail__metrics strong { color: var(--hrms-primary-dark); font-size: 0.92rem; }
.detail__trend h4 { margin-bottom: 5px; font-size: 0.78rem; }
.performance__empty, .performance__error { margin: 18px 0; color: var(--hrms-text-muted); font-size: 0.84rem; text-align: center; }
.performance__error { color: #b91c1c; }
@media (max-width: 850px) { .performance__head, .detail__body { display: grid; grid-template-columns: 1fr; } .performance__controls { flex-wrap: wrap; } .detail__breakdown { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
@media (max-width: 600px) { .performance__summary { display: grid; grid-template-columns: 1fr; } .performance__summary div { border-right: 0; border-bottom: 1px solid var(--hrms-border); } .performance__summary div:last-child { border-bottom: 0; } .leaderboard__row { grid-template-columns: 18px minmax(80px, 110px) 1fr 42px; gap: 7px; padding: 9px 5px; } .detail__metrics { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
</style>
