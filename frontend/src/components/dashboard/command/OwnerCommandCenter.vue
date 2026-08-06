<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { RouterLink } from 'vue-router'
import { fetchCommandCenter } from '@/api/dashboard'
import MultiSeriesLineChart from '@/components/dashboard/command/MultiSeriesLineChart.vue'
import Sparkline from '@/components/dashboard/command/Sparkline.vue'
import HrmsModal from '@/components/ui/HrmsModal.vue'
import type {
  ActivityItem,
  ClientBadge,
  CommandCenterData,
  CommandCenterFilters,
  RecruiterLeaderboardRow,
  TrendGrain,
} from '@/types/commandCenter'

const props = defineProps<{
  start?: string
  end?: string
  refreshKey?: number
}>()

const loading = ref(true)
const error = ref('')
const data = ref<CommandCenterData | null>(null)

const trendGrain = ref<TrendGrain>('monthly')
const recruiterId = ref('')
const clientId = ref('')
const department = ref('')
const jobStatus = ref('')
const location = ref('')

const leaderboardSort = ref<'productivity_score' | 'placements' | 'avg_time_to_hire_days' | 'active_candidates'>(
  'productivity_score',
)
const selectedRecruiterId = ref<string | null>(null)
const clientFilter = ref<'active' | 'inactive' | 'all'>('active')
const clientSort = ref<'placements' | 'open_positions' | 'jobs_pending_too_long'>('placements')
const allActivities = ref<ActivityItem[]>([])
const showAllActivities = ref(false)
const loadingAllActivities = ref(false)
const allActivitiesError = ref('')
const activityHistoryPeriod = ref<'day' | 'week' | 'month'>('month')

const filters = computed<CommandCenterFilters>(() => ({
  start: props.start,
  end: props.end,
  trend_grain: trendGrain.value,
  recruiter_id: recruiterId.value || undefined,
  client_id: clientId.value || undefined,
  department: department.value || undefined,
  job_status: jobStatus.value || undefined,
  location: location.value || undefined,
}))

const sortedLeaderboard = computed(() => {
  const rows = [...(data.value?.recruiter_leaderboard ?? [])]
  rows.sort((a, b) => {
    if (leaderboardSort.value === 'avg_time_to_hire_days') {
      return (a.avg_time_to_hire_days ?? 999) - (b.avg_time_to_hire_days ?? 999)
    }
    return Number(b[leaderboardSort.value] ?? 0) - Number(a[leaderboardSort.value] ?? 0)
  })
  return rows
})

const selectedRecruiter = computed(
  () =>
    sortedLeaderboard.value.find((row) => row.recruiter_id === selectedRecruiterId.value) ?? null,
)

const filteredClients = computed(() => {
  let rows = [...(data.value?.client_health ?? [])]
  if (clientFilter.value === 'active') rows = rows.filter((c) => c.client_status === 'active')
  if (clientFilter.value === 'inactive') rows = rows.filter((c) => c.client_status !== 'active')
  rows.sort((a, b) => Number(b[clientSort.value] ?? 0) - Number(a[clientSort.value] ?? 0))
  return rows
})

const maxWorkload = computed(() =>
  Math.max(...(data.value?.recruiter_workload.map((r) => r.assigned_jobs) ?? [1]), 1),
)

const maxFunnel = computed(() =>
  Math.max(...(data.value?.hiring_funnel.stages.map((s) => s.count) ?? [1]), 1),
)

function dateAtStart(value: string) {
  const [year = 1970, month = 1, day = 1] = value.split('-').map(Number)
  return new Date(year, month - 1, day)
}

function startOfDay(date: Date) {
  const result = new Date(date)
  result.setHours(0, 0, 0, 0)
  return result
}

function endOfDay(date: Date) {
  const result = new Date(date)
  result.setHours(23, 59, 59, 999)
  return result
}

const activityHistoryRange = computed(() => {
  const today = new Date()
  const selectedStart = props.start ? startOfDay(dateAtStart(props.start)) : startOfDay(new Date(today.getFullYear(), today.getMonth(), today.getDate() - 30))
  const selectedEnd = props.end ? endOfDay(dateAtStart(props.end)) : endOfDay(today)

  let periodStart: Date
  let periodEnd: Date
  if (activityHistoryPeriod.value === 'day') {
    periodStart = startOfDay(today)
    periodEnd = endOfDay(today)
  } else if (activityHistoryPeriod.value === 'week') {
    const daysSinceSunday = today.getDay()
    periodStart = startOfDay(new Date(today.getFullYear(), today.getMonth(), today.getDate() - daysSinceSunday))
    periodEnd = endOfDay(new Date(periodStart.getFullYear(), periodStart.getMonth(), periodStart.getDate() + 6))
  } else {
    periodStart = startOfDay(new Date(today.getFullYear(), today.getMonth(), 1))
    periodEnd = endOfDay(new Date(today.getFullYear(), today.getMonth() + 1, 0))
  }

  return {
    start: new Date(Math.max(selectedStart.getTime(), periodStart.getTime())),
    end: new Date(Math.min(selectedEnd.getTime(), periodEnd.getTime())),
  }
})

const visibleActivities = computed(() => {
  const { start, end } = activityHistoryRange.value
  if (start > end) return []
  return allActivities.value.filter((item) => {
    if (!item.time) return false
    const time = new Date(item.time)
    return !Number.isNaN(time.getTime()) && time >= start && time <= end
  })
})

async function load() {
  loading.value = true
  error.value = ''
  try {
    data.value = await fetchCommandCenter(filters.value)
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Failed to load command center'
  } finally {
    loading.value = false
  }
}

async function openAllActivities() {
  showAllActivities.value = true
  activityHistoryPeriod.value = 'month'
  await loadAllActivities()
}

async function loadAllActivities() {
  loadingAllActivities.value = true
  allActivitiesError.value = ''
  try {
    const response = await fetchCommandCenter({ ...filters.value, activity_limit: 500 })
    allActivities.value = response.activity_feed
  } catch (err) {
    allActivitiesError.value =
      err instanceof Error ? err.message : 'Failed to load activity history'
  } finally {
    loadingAllActivities.value = false
  }
}

function clearFilters() {
  recruiterId.value = ''
  clientId.value = ''
  department.value = ''
  jobStatus.value = ''
  location.value = ''
  trendGrain.value = 'monthly'
}

function formatValue(value: number | null, unit: string) {
  if (value == null) return 'No data'
  if (unit === 'percent') return `${value.toFixed(1)}%`
  if (unit === 'days') return `${value.toFixed(1)}d`
  return new Intl.NumberFormat('en-IN').format(value)
}

function formatDelta(delta: number | null) {
  if (delta == null) return '—'
  const sign = delta > 0 ? '+' : ''
  return `${sign}${delta.toFixed(1)}%`
}

function formatDays(value: number | null) {
  return value == null ? 'No data' : `${value.toFixed(1)}d`
}

function formatWhen(iso: string | null) {
  if (!iso) return 'No activity recorded'
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return iso
  return d.toLocaleString('en-IN', {
    hour: '2-digit',
    minute: '2-digit',
    day: '2-digit',
    month: 'short',
  })
}

function badgeClass(badge: ClientBadge) {
  if (badge === 'Healthy') return 'badge--green'
  if (badge === 'Needs Attention') return 'badge--amber'
  return 'badge--muted'
}

function workloadClass(level: RecruiterLeaderboardRow['workload_level']) {
  if (level === 'overloaded') return 'pill--red'
  if (level === 'heavy') return 'pill--amber'
  if (level === 'light') return 'pill--green'
  return 'pill--muted'
}

function formatPercent(value: number | null) {
  return value == null ? 'No data' : `${value.toFixed(1)}%`
}

function jobStatusClass(status: string) {
  if (status === 'overdue') return 'pill--red'
  if (status === 'urgent') return 'pill--amber'
  if (status === 'frozen') return 'pill--muted'
  return 'pill--green'
}

let loadTimer: ReturnType<typeof setTimeout> | null = null
function scheduleLoad() {
  if (loadTimer) clearTimeout(loadTimer)
  loadTimer = setTimeout(() => {
    loadTimer = null
    void load()
    if (showAllActivities.value) void loadAllActivities()
  }, 150)
}

watch(
  () => [
    props.start,
    props.end,
    props.refreshKey,
    trendGrain.value,
    recruiterId.value,
    clientId.value,
    department.value,
    jobStatus.value,
    location.value,
  ],
  () => scheduleLoad(),
  { immediate: true },
)
</script>

<template>
  <div class="cc">
    <div class="cc__filters" role="region" aria-label="Command center filters">
      <label>
        <span>Recruiter</span>
        <select v-model="recruiterId">
          <option value="">All recruiters</option>
          <option
            v-for="item in data?.filter_options.recruiters ?? []"
            :key="item.id"
            :value="item.id"
          >
            {{ item.name }}
          </option>
        </select>
      </label>
      <label>
        <span>Client</span>
        <select v-model="clientId">
          <option value="">All clients</option>
          <option v-for="item in data?.filter_options.clients ?? []" :key="item.id" :value="item.id">
            {{ item.name }}
          </option>
        </select>
      </label>
      <label>
        <span>Department</span>
        <select v-model="department">
          <option value="">All departments</option>
          <option v-for="item in data?.filter_options.departments ?? []" :key="item" :value="item">
            {{ item }}
          </option>
        </select>
      </label>
      <label>
        <span>Job status</span>
        <select v-model="jobStatus">
          <option value="">All statuses</option>
          <option v-for="item in data?.filter_options.job_statuses ?? []" :key="item" :value="item">
            {{ item }}
          </option>
        </select>
      </label>
      <label>
        <span>Location</span>
        <select v-model="location">
          <option value="">All locations</option>
          <option v-for="item in data?.filter_options.locations ?? []" :key="item" :value="item">
            {{ item }}
          </option>
        </select>
      </label>
      <button type="button" class="cc__clear" @click="clearFilters">Clear filters</button>
    </div>

    <p v-if="loading && !data" class="cc__empty">Loading executive command center…</p>
    <p v-else-if="error" class="cc__error">{{ error }}</p>

    <template v-else-if="data">
      <!-- Section 1: KPI Overview -->
      <section class="section">
        <header class="section__head">
          <h2>Executive overview</h2>
          <p>Business health at a glance</p>
        </header>
        <p v-if="!data.kpis.length" class="cc__empty">No executive metrics are available for this filter.</p>
        <div v-else class="kpi-grid">
          <article
            v-for="kpi in data.kpis"
            :key="kpi.key"
            class="kpi-card"
            :title="kpi.tooltip"
            tabindex="0"
          >
            <div class="kpi-card__top">
              <span>{{ kpi.label }}</span>
              <em
                class="delta"
                :class="{
                  'delta--up': kpi.trend === 'up',
                  'delta--down': kpi.trend === 'down',
                }"
              >
                {{ formatDelta(kpi.delta_pct) }}
              </em>
            </div>
            <strong>{{ formatValue(kpi.value, kpi.unit) }}</strong>
            <Sparkline v-if="kpi.sparkline.length" :points="kpi.sparkline" />
            <span v-else class="muted">No history</span>
            <small>{{ kpi.tooltip }}</small>
          </article>
        </div>
      </section>

      <!-- Section 2 + 3 -->
      <section class="grid-12">
        <article class="panel span-8">
          <header class="panel__head">
            <div>
              <h2>Business trend</h2>
              <p>Hiring activity over time</p>
            </div>
            <div class="segmented" role="group" aria-label="Trend grain">
              <button
                v-for="grain in (['weekly', 'monthly', 'quarterly', 'yearly'] as TrendGrain[])"
                :key="grain"
                type="button"
                :class="{ 'is-active': trendGrain === grain }"
                @click="trendGrain = grain"
              >
                {{ grain }}
              </button>
            </div>
          </header>
          <MultiSeriesLineChart :series="data.business_trend.series" />
        </article>

        <article class="panel span-4">
          <header class="panel__head">
            <div>
              <h2>Hiring funnel</h2>
              <p>Conversion and drop-off</p>
            </div>
          </header>
          <div v-if="!data.hiring_funnel.stages.some((s) => s.count)" class="cc__empty">
            No candidates currently in the funnel.
          </div>
          <div v-else class="funnel">
            <div
              v-for="stage in data.hiring_funnel.stages"
              :key="stage.name"
              class="funnel__row"
              :class="{ 'is-drop': stage.is_highest_dropoff }"
            >
              <div class="funnel__meta">
                <strong>{{ stage.name }}</strong>
                <span>{{ stage.count }}</span>
              </div>
              <div class="funnel__track">
                <div
                  class="funnel__fill"
                  :style="{ width: `${(stage.count / maxFunnel) * 100}%` }"
                />
              </div>
              <small v-if="stage.dropoff_pct != null">
                {{ stage.conversion_pct }}% of prior-stage count
              </small>
            </div>
          </div>
          <p v-if="data.hiring_funnel.insight" class="insight">{{ data.hiring_funnel.insight }}</p>
        </article>
      </section>

      <!-- Section 4 + 5 -->
      <section class="grid-12">
        <article class="panel span-6">
          <header class="panel__head">
            <div>
              <h2>Recruiter performance</h2>
              <p>Leaderboard ranked for decisions</p>
            </div>
            <label class="inline-select">
              Sort by
              <select v-model="leaderboardSort">
                <option value="productivity_score">Performance score</option>
                <option value="placements">Placements</option>
                <option value="avg_time_to_hire_days">Time to hire</option>
                <option value="active_candidates">Active candidates</option>
              </select>
            </label>
          </header>
          <div v-if="!sortedLeaderboard.length" class="cc__empty">No active recruiters found.</div>
          <div v-else class="leaderboard">
            <button
              v-for="row in sortedLeaderboard"
              :key="row.recruiter_id"
              type="button"
              class="leaderboard__row"
              :class="{ 'is-selected': selectedRecruiterId === row.recruiter_id }"
              @click="selectedRecruiterId = row.recruiter_id"
            >
              <span class="avatar" aria-hidden="true">{{ row.initials }}</span>
              <span class="leaderboard__main">
                <strong>{{ row.name }}</strong>
                <small>
                  {{ row.placements }} placements · {{ row.active_candidates }} active ·
                  {{ row.interviews_scheduled }} interviews
                </small>
              </span>
              <span class="pill" :class="workloadClass(row.workload_level)">{{ row.workload_level }}</span>
              <strong class="score">{{ row.productivity_score.toFixed(1) }}</strong>
            </button>
          </div>
          <div v-if="selectedRecruiter" class="detail-card">
            <h3>{{ selectedRecruiter.name }}</h3>
            <div class="detail-grid">
              <div><span>Placements</span><strong>{{ selectedRecruiter.placements }}</strong></div>
              <div><span>Active candidates</span><strong>{{ selectedRecruiter.active_candidates }}</strong></div>
              <div><span>Interviews</span><strong>{{ selectedRecruiter.interviews_scheduled }}</strong></div>
              <div><span>Avg time to hire</span><strong>{{ formatDays(selectedRecruiter.avg_time_to_hire_days) }}</strong></div>
              <div><span>Offer acceptance</span><strong>{{ formatPercent(selectedRecruiter.offer_acceptance_rate) }}</strong></div>
              <div><span>Assigned jobs</span><strong>{{ selectedRecruiter.assigned_jobs }}</strong></div>
            </div>
          </div>
        </article>

        <article class="panel span-6">
          <header class="panel__head">
            <div>
              <h2>Recruiter workload</h2>
              <p>Assigned open job requirements</p>
            </div>
          </header>
          <div v-if="!data.recruiter_workload.length" class="cc__empty">No workload data yet.</div>
          <div v-else class="workload">
            <div
              v-for="row in data.recruiter_workload"
              :key="row.recruiter_id"
              class="workload__row"
              :class="{ 'is-over': row.overloaded }"
            >
              <span>{{ row.name }}</span>
              <div class="workload__track">
                <div
                  class="workload__fill"
                  :style="{ width: `${(row.assigned_jobs / maxWorkload) * 100}%` }"
                />
              </div>
              <strong>{{ row.assigned_jobs }}</strong>
            </div>
          </div>
          <p v-if="data.workload_insight" class="insight">{{ data.workload_insight }}</p>
        </article>
      </section>

      <!-- Section 6: Client health -->
      <section class="section">
        <header class="section__head row">
          <div>
            <h2>Client health</h2>
            <p>Which accounts need attention</p>
          </div>
          <div class="controls">
            <div class="segmented">
              <button type="button" :class="{ 'is-active': clientFilter === 'active' }" @click="clientFilter = 'active'">Active</button>
              <button type="button" :class="{ 'is-active': clientFilter === 'inactive' }" @click="clientFilter = 'inactive'">Inactive</button>
              <button type="button" :class="{ 'is-active': clientFilter === 'all' }" @click="clientFilter = 'all'">All</button>
            </div>
            <label class="inline-select">
              Sort
              <select v-model="clientSort">
                <option value="placements">Most placements</option>
                <option value="open_positions">Most open jobs</option>
                <option value="jobs_pending_too_long">Longest pending jobs</option>
              </select>
            </label>
          </div>
        </header>
        <div v-if="!filteredClients.length" class="cc__empty">No clients match this filter.</div>
        <div v-else class="client-grid">
          <article v-for="client in filteredClients" :key="client.client_id" class="client-card">
            <header>
              <h3>{{ client.name }}</h3>
              <span class="badge" :class="badgeClass(client.status_badge)">{{ client.status_badge }}</span>
            </header>
            <div class="client-card__metrics">
              <div><span>Open positions</span><strong>{{ client.open_positions }}</strong></div>
              <div><span>Placements</span><strong>{{ client.placements }}</strong></div>
              <div><span>In pipeline</span><strong>{{ client.candidates_in_pipeline }}</strong></div>
              <div><span>Avg hiring time</span><strong>{{ formatDays(client.avg_hiring_time_days) }}</strong></div>
              <div><span>Pending too long</span><strong>{{ client.jobs_pending_too_long }}</strong></div>
              <div><span>Last activity</span><strong>{{ formatWhen(client.last_activity) }}</strong></div>
            </div>
          </article>
        </div>
      </section>

      <!-- Section 7: Open job health -->
      <section class="section">
        <header class="section__head">
          <h2>Open job health</h2>
          <p>SLA and urgency across requisitions</p>
        </header>
        <div class="status-cards">
          <article><span>Healthy jobs</span><strong>{{ data.job_health_counts.healthy }}</strong></article>
          <article class="is-amber"><span>Urgent jobs</span><strong>{{ data.job_health_counts.urgent }}</strong></article>
          <article class="is-red"><span>Overdue jobs</span><strong>{{ data.job_health_counts.overdue }}</strong></article>
          <article class="is-muted"><span>Frozen jobs</span><strong>{{ data.job_health_counts.frozen }}</strong></article>
        </div>
        <div class="table-wrap">
          <table v-if="data.open_jobs.length" class="jobs-table">
            <thead>
              <tr>
                <th>Job title</th>
                <th>Client</th>
                <th>Recruiter</th>
                <th>Days open</th>
                <th>Candidates</th>
                <th>Current stage</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="job in data.open_jobs"
                :key="job.job_id"
                :class="{ 'is-sla': job.exceeds_sla }"
              >
                <td>{{ job.job_title }}</td>
                <td>{{ job.client_name }}</td>
                <td>{{ job.recruiter_name || 'Unassigned' }}</td>
                <td>{{ job.days_open }}</td>
                <td>{{ job.candidates }}</td>
                <td>{{ job.current_stage || '—' }}</td>
                <td><span class="pill" :class="jobStatusClass(job.status)">{{ job.status }}</span></td>
              </tr>
            </tbody>
          </table>
          <p v-else class="cc__empty">No open jobs in this filter.</p>
        </div>
      </section>

      <!-- Section 8: Pipeline summary -->
      <section class="section">
        <header class="section__head">
          <h2>Candidate pipeline summary</h2>
          <p>Today’s operational pulse</p>
        </header>
        <p v-if="!data.pipeline_summary.length" class="cc__empty">No pipeline metrics are available for this filter.</p>
        <div v-else class="pipeline-grid">
          <article v-for="card in data.pipeline_summary" :key="card.key" class="pipeline-card">
            <span>{{ card.label }}</span>
            <strong>{{ card.value }}</strong>
            <em v-if="card.delta != null" :class="{ 'delta--up': card.delta > 0, 'delta--down': card.delta < 0 }">
              {{ card.delta > 0 ? '+' : '' }}{{ card.delta }} {{ card.delta_label || 'vs yesterday' }}
            </em>
            <em v-else class="muted">Current total</em>
          </article>
        </div>
      </section>

      <!-- Section 9 + 10 -->
      <section class="grid-12">
        <article class="panel span-6">
          <header class="panel__head">
            <div>
              <h2>Recruiter activity feed</h2>
              <p>Newest actions first</p>
            </div>
            <button type="button" class="cc__view-all" @click="void openAllActivities()">
              View all
            </button>
          </header>
          <ol v-if="data.activity_feed.length" class="timeline">
            <li v-for="item in data.activity_feed" :key="item.id">
              <time>{{ formatWhen(item.time) }}</time>
              <div>
                <strong>{{ item.actor || 'Team' }} · {{ item.title }}</strong>
                <span>{{ item.description }}</span>
              </div>
            </li>
          </ol>
          <p v-else class="cc__empty">No recent recruiter activity.</p>
        </article>

        <article class="panel span-6">
          <header class="panel__head">
            <div>
              <h2>Alerts & action center</h2>
              <p>What needs attention today</p>
            </div>
          </header>
          <div v-if="!data.alerts.length" class="cc__empty">No active alerts. Operations look clear.</div>
          <div v-else class="alerts">
            <article
              v-for="alert in data.alerts"
              :key="alert.id"
              class="alert-card"
              :class="alert.severity === 'red' ? 'alert-card--red' : 'alert-card--amber'"
            >
              <div>
                <strong>{{ alert.title }}</strong>
                <p>{{ alert.description }}</p>
              </div>
              <RouterLink class="alert-card__action" :to="alert.action_href">
                {{ alert.action_label }}
              </RouterLink>
            </article>
          </div>
        </article>
      </section>
    </template>

    <HrmsModal v-model="showAllActivities" title="Recruiter activity history" size="lg">
      <p v-if="loadingAllActivities" class="cc__empty">Loading activity history…</p>
      <p v-else-if="allActivitiesError" class="cc__error">{{ allActivitiesError }}</p>
      <template v-else>
        <div class="activity-history__periods" role="group" aria-label="Activity history period">
          <button
            v-for="period in (['day', 'week', 'month'] as const)"
            :key="period"
            type="button"
            :class="{ 'is-active': activityHistoryPeriod === period }"
            @click="activityHistoryPeriod = period"
          >
            {{ period }}
          </button>
        </div>
        <ol v-if="visibleActivities.length" class="timeline activity-history">
          <li v-for="item in visibleActivities" :key="item.id">
            <time>{{ formatWhen(item.time) }}</time>
            <div>
              <strong>{{ item.actor || 'Team' }} · {{ item.title }}</strong>
              <span>{{ item.description }}</span>
            </div>
          </li>
        </ol>
        <p v-else class="cc__empty">No recruiter activity in this period within the selected date range.</p>
      </template>
    </HrmsModal>
  </div>
</template>

<style scoped>
.cc {
  display: grid;
  gap: 20px;
  max-width: 1400px;
  margin: 0 auto;
}
.cc__filters {
  position: sticky;
  top: 0;
  z-index: 5;
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr)) auto;
  gap: 10px;
  padding: 12px;
  border: 1px solid var(--hrms-border);
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.92);
  backdrop-filter: blur(8px);
  box-shadow: var(--hrms-shadow-sm);
}
.cc__filters label {
  display: grid;
  gap: 4px;
  font-size: 0.7rem;
  font-weight: 650;
  color: var(--hrms-text-muted);
}
.cc__filters select,
.inline-select select {
  width: 100%;
  padding: 8px 10px;
  border: 1px solid var(--hrms-border);
  border-radius: 8px;
  background: #fff;
  color: var(--hrms-text);
}
.cc__clear,
.cc__view-all,
.segmented button,
.alert-card__action,
.leaderboard__row {
  cursor: pointer;
}
.cc__clear {
  align-self: end;
  padding: 8px 12px;
  border: 1px solid var(--hrms-border);
  border-radius: 8px;
  background: #fff;
  color: var(--hrms-text);
  font-weight: 600;
}
.cc__view-all {
  border: 0;
  padding: 6px 0;
  background: transparent;
  color: var(--hrms-primary);
  font-size: 0.76rem;
  font-weight: 700;
}
.section,
.panel {
  padding: 18px;
  border: 1px solid var(--hrms-border);
  border-radius: 16px;
  background: linear-gradient(180deg, #fff 0%, #fcfbff 100%);
  box-shadow: var(--hrms-shadow-sm);
}
.section__head,
.panel__head,
.section__head.row,
.controls,
.client-card header,
.kpi-card__top {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: flex-start;
}
.section__head h2,
.panel__head h2,
.client-card h3,
.detail-card h3 {
  margin: 0;
  color: var(--hrms-primary-dark);
}
.section__head p,
.panel__head p,
.insight,
.cc__empty,
.muted {
  margin: 4px 0 0;
  color: var(--hrms-text-muted);
  font-size: 0.8rem;
}
.insight {
  margin-top: 12px;
  padding: 10px 12px;
  border-radius: 10px;
  background: #f5f3ff;
  color: #5b21b6;
}
.grid-12 {
  display: grid;
  grid-template-columns: repeat(12, minmax(0, 1fr));
  gap: 16px;
}
.span-8 { grid-column: span 8; }
.span-6 { grid-column: span 6; }
.span-4 { grid-column: span 4; }
.kpi-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
  margin-top: 14px;
}
.kpi-card,
.client-card,
.pipeline-card,
.status-cards article,
.alert-card {
  border: 1px solid var(--hrms-border);
  border-radius: 14px;
  background: #fff;
  transition: transform 0.18s ease, box-shadow 0.18s ease, border-color 0.18s ease;
}
.kpi-card:hover,
.client-card:hover,
.leaderboard__row:hover,
.alert-card:hover {
  transform: translateY(-1px);
  box-shadow: var(--hrms-shadow-sm);
  border-color: color-mix(in srgb, #7c3aed 35%, var(--hrms-border));
}
.kpi-card {
  display: grid;
  gap: 8px;
  padding: 14px;
}
.kpi-card span,
.pipeline-card span,
.status-cards span,
.client-card__metrics span,
.detail-grid span {
  font-size: 0.72rem;
  color: var(--hrms-text-muted);
}
.kpi-card strong,
.pipeline-card strong,
.status-cards strong,
.score {
  color: var(--hrms-primary-dark);
  font-size: 1.35rem;
}
.kpi-card small {
  font-size: 0.68rem;
  color: var(--hrms-text-muted);
}
.delta { font-style: normal; font-size: 0.72rem; font-weight: 700; }
.delta--up { color: #15803d; }
.delta--down { color: #b91c1c; }
.segmented {
  display: inline-flex;
  padding: 3px;
  border: 1px solid var(--hrms-border);
  border-radius: 10px;
  background: #f8fafc;
}
.segmented button {
  border: 0;
  border-radius: 8px;
  padding: 6px 10px;
  background: transparent;
  color: var(--hrms-text-muted);
  font-size: 0.72rem;
  font-weight: 650;
  text-transform: capitalize;
}
.segmented button.is-active {
  background: #7c3aed;
  color: #fff;
}
.inline-select {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-size: 0.74rem;
  color: var(--hrms-text-muted);
}
.funnel { display: grid; gap: 10px; }
.funnel__row { display: grid; gap: 4px; }
.funnel__row.is-drop .funnel__fill { background: #ef4444; }
.funnel__meta { display: flex; justify-content: space-between; font-size: 0.8rem; }
.funnel__track, .workload__track {
  height: 10px;
  border-radius: 999px;
  background: #f1f5f9;
  overflow: hidden;
}
.funnel__fill, .workload__fill {
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(90deg, #7c3aed, #a78bfa);
}
.leaderboard, .workload, .alerts { display: grid; gap: 8px; }
.leaderboard__row {
  display: grid;
  grid-template-columns: 36px 1fr auto auto;
  gap: 10px;
  align-items: center;
  width: 100%;
  padding: 10px;
  border: 1px solid transparent;
  border-radius: 12px;
  background: transparent;
  text-align: left;
  color: inherit;
}
.leaderboard__row.is-selected {
  border-color: color-mix(in srgb, #7c3aed 40%, var(--hrms-border));
  background: #faf5ff;
}
.avatar {
  width: 36px;
  height: 36px;
  display: grid;
  place-items: center;
  border-radius: 50%;
  background: #ede9fe;
  color: #6d28d9;
  font-size: 0.72rem;
  font-weight: 700;
}
.leaderboard__main { display: grid; gap: 2px; min-width: 0; }
.leaderboard__main strong { font-size: 0.86rem; }
.leaderboard__main small { color: var(--hrms-text-muted); font-size: 0.7rem; }
.workload__row {
  display: grid;
  grid-template-columns: 120px 1fr 36px;
  gap: 10px;
  align-items: center;
}
.workload__row.is-over .workload__fill { background: linear-gradient(90deg, #dc2626, #f97316); }
.detail-card {
  margin-top: 12px;
  padding: 12px;
  border: 1px solid #ddd6fe;
  border-radius: 12px;
  background: #faf5ff;
}
.detail-grid,
.client-card__metrics,
.pipeline-grid,
.status-cards,
.client-grid {
  display: grid;
  gap: 10px;
}
.detail-grid { grid-template-columns: repeat(3, minmax(0, 1fr)); margin-top: 10px; }
.detail-grid div,
.client-card__metrics div {
  display: grid;
  gap: 3px;
  padding: 8px;
  border-radius: 8px;
  background: #fff;
  border: 1px solid var(--hrms-border);
}
.client-grid { grid-template-columns: repeat(3, minmax(0, 1fr)); margin-top: 14px; }
.client-card { padding: 14px; display: grid; gap: 12px; }
.client-card__metrics { grid-template-columns: repeat(2, minmax(0, 1fr)); }
.status-cards {
  grid-template-columns: repeat(4, minmax(0, 1fr));
  margin: 14px 0;
}
.status-cards article {
  padding: 14px;
  display: grid;
  gap: 6px;
}
.status-cards .is-amber { background: #fffbeb; }
.status-cards .is-red { background: #fef2f2; }
.status-cards .is-muted { background: #f8fafc; }
.table-wrap { overflow: auto; }
.jobs-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.82rem;
}
.jobs-table th,
.jobs-table td {
  padding: 10px 8px;
  border-bottom: 1px solid var(--hrms-border);
  text-align: left;
}
.jobs-table th {
  font-size: 0.7rem;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: var(--hrms-text-muted);
}
.jobs-table tr.is-sla { background: #fef2f2; }
.pipeline-grid { grid-template-columns: repeat(6, minmax(0, 1fr)); margin-top: 14px; }
.pipeline-card { padding: 14px; display: grid; gap: 6px; }
.timeline {
  list-style: none;
  margin: 0;
  padding: 0;
  display: grid;
  gap: 12px;
}
.timeline li {
  display: grid;
  grid-template-columns: 110px 1fr;
  gap: 12px;
}
.timeline time {
  font-size: 0.72rem;
  color: var(--hrms-text-muted);
}
.timeline strong { display: block; font-size: 0.84rem; }
.timeline span { color: var(--hrms-text-muted); font-size: 0.74rem; }
.activity-history__periods {
  display: inline-flex;
  margin-bottom: 14px;
  padding: 3px;
  border: 1px solid var(--hrms-border);
  border-radius: 10px;
  background: #f8fafc;
}
.activity-history__periods button {
  border: 0;
  border-radius: 8px;
  padding: 6px 10px;
  background: transparent;
  color: var(--hrms-text-muted);
  cursor: pointer;
  font-size: 0.72rem;
  font-weight: 650;
  text-transform: capitalize;
}
.activity-history__periods button.is-active {
  background: #7c3aed;
  color: #fff;
}
.activity-history { max-height: 65vh; overflow: auto; padding-right: 6px; }
.alert-card {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: center;
  padding: 12px 14px;
}
.alert-card--red { background: #fef2f2; border-color: #fecaca; }
.alert-card--amber { background: #fffbeb; border-color: #fde68a; }
.alert-card strong { display: block; margin-bottom: 4px; }
.alert-card p { margin: 0; font-size: 0.78rem; color: var(--hrms-text-muted); }
.alert-card__action {
  flex-shrink: 0;
  padding: 8px 10px;
  border-radius: 8px;
  background: #7c3aed;
  color: #fff;
  text-decoration: none;
  font-size: 0.74rem;
  font-weight: 650;
}
.badge, .pill {
  display: inline-flex;
  align-items: center;
  padding: 2px 8px;
  border-radius: 999px;
  font-size: 0.68rem;
  font-weight: 700;
  text-transform: capitalize;
}
.badge--green, .pill--green { background: #dcfce7; color: #15803d; }
.badge--amber, .pill--amber { background: #ffedd5; color: #c2410c; }
.badge--muted, .pill--muted { background: #f1f5f9; color: #475569; }
.pill--red { background: #fee2e2; color: #b91c1c; }
.cc__error { color: #b91c1c; text-align: center; }
@media (max-width: 1100px) {
  .kpi-grid, .client-grid, .pipeline-grid, .status-cards { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .span-8, .span-6, .span-4 { grid-column: 1 / -1; }
  .cc__filters { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}
@media (max-width: 720px) {
  .kpi-grid, .client-grid, .pipeline-grid, .status-cards, .detail-grid { grid-template-columns: 1fr; }
  .timeline li { grid-template-columns: 1fr; }
  .workload__row { grid-template-columns: 1fr; }
}
</style>
