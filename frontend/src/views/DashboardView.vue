<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { fetchAnalyticsDashboard } from '@/api/dashboard'
import BarChart from '@/components/dashboard/BarChart.vue'
import DonutChart from '@/components/dashboard/DonutChart.vue'
import HeatmapChart from '@/components/dashboard/HeatmapChart.vue'
import HrmsAlert from '@/components/ui/HrmsAlert.vue'
import { useAttendanceStore } from '@/stores/attendance'
import { useAuthStore } from '@/stores/auth'
import { useDashboardLiveStore } from '@/stores/dashboardLive'
import type { AnalyticsDashboard, DashboardWsEvent } from '@/types/dashboard'
import { formatOfficeTime } from '@/utils/format'

const auth = useAuthStore()
const attendance = useAttendanceStore()
const live = useDashboardLiveStore()

const loading = ref(true)
const error = ref('')
const data = ref<AnalyticsDashboard | null>(null)
const flash = ref<Set<string>>(new Set())

const isOwner = computed(() => data.value?.role === 'owner' || auth.role === 'owner')

const greeting = computed(() => {
  const hour = new Date().getHours()
  if (hour < 12) return 'Good morning'
  if (hour < 17) return 'Good afternoon'
  return 'Good evening'
})

const STAGE_COLORS: Record<string, string> = {
  Applied: '#64748b',
  Shortlisted: '#6366f1',
  Screening: '#0ea5e9',
  Interview: '#8b5cf6',
  Offer: '#f59e0b',
  Joined: '#22c55e',
  'On Hold': '#94a3b8',
  Rejected: '#ef4444',
}

const ownerCards = computed(() => {
  const k = data.value?.kpis
  if (!k) return []
  return [
    { key: 'kpis', label: 'Total Candidates', value: k.total_candidates },
    { key: 'kpis', label: 'Active', value: k.active_candidates },
    { key: 'kpis', label: 'Inactive', value: k.inactive_candidates },
    { key: 'kpis', label: 'Pending Approval', value: k.pending_approval },
    { key: 'kpis', label: 'Approved', value: k.approved_candidates },
    { key: 'kpis', label: 'Rejected', value: k.rejected_candidates },
    { key: 'kpis', label: 'Total Recruiters', value: k.total_recruiters },
    { key: 'kpis', label: 'Active Recruiters', value: k.active_recruiters },
    { key: 'kpis', label: 'Clients', value: k.total_clients },
    { key: 'kpis', label: 'Open Jobs', value: k.open_jobs },
    { key: 'kpis', label: 'Closed Jobs', value: k.closed_jobs },
    { key: 'kpis', label: 'Placements', value: k.placements },
    { key: 'kpis', label: 'Monthly Placements', value: k.monthly_placements },
    { key: 'kpis', label: 'Revenue', value: formatMoney(k.revenue) },
    {
      key: 'kpis',
      label: 'Avg Time to Hire',
      value: k.average_time_to_hire_days != null ? `${k.average_time_to_hire_days}d` : '—',
    },
  ]
})

const recruiterCards = computed(() => {
  const k = data.value?.kpis
  if (!k) return []
  return [
    { key: 'kpis', label: 'My Candidates', value: k.my_candidates },
    { key: 'kpis', label: 'Pending Approval', value: k.pending_approval },
    { key: 'kpis', label: 'Approved', value: k.approved },
    { key: 'kpis', label: 'Rejected', value: k.rejected },
    { key: 'kpis', label: 'Interviews', value: k.interviews_scheduled },
    { key: 'kpis', label: 'Offers', value: k.offers },
    { key: 'kpis', label: 'Placements', value: k.placements },
    { key: 'kpis', label: 'Clients Assigned', value: k.clients_assigned },
    { key: 'kpis', label: 'Jobs Assigned', value: k.jobs_assigned },
  ]
})

const cards = computed(() => (isOwner.value ? ownerCards.value : recruiterCards.value))

const pipelineMax = computed(() =>
  Math.max(...(data.value?.charts.pipeline_stages ?? []).map((s) => s.count), 1),
)

function dayKey(d: Date) {
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${y}-${m}-${day}`
}

const calendarDays = computed(() => {
  const start = new Date()
  start.setHours(0, 0, 0, 0)
  const todayKey = dayKey(new Date())
  const days = Array.from({ length: 14 }, (_, i) => {
    const d = new Date(start)
    d.setDate(start.getDate() + i)
    return d
  })
  const byDay = new Map<string, Array<Record<string, unknown>>>()
  for (const row of data.value?.tables.upcoming_interviews ?? []) {
    const iso = row.scheduled_at
    if (typeof iso !== 'string') continue
    const key = dayKey(new Date(iso))
    const list = byDay.get(key) ?? []
    list.push(row)
    byDay.set(key, list)
  }
  return days.map((d) => {
    const key = dayKey(d)
    return {
      key,
      label: d.toLocaleDateString('en-IN', { weekday: 'short', day: '2-digit', month: 'short' }),
      isToday: key === todayKey,
      items: byDay.get(key) ?? [],
    }
  })
})

function formatMoney(n: number) {
  if (!n) return '—'
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 0,
  }).format(n)
}

function formatWhen(iso: unknown) {
  if (!iso || typeof iso !== 'string') return '—'
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return iso
  return d.toLocaleString('en-IN', {
    day: '2-digit',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
  })
}

function str(v: unknown) {
  return v == null ? '—' : String(v)
}

async function load(widgets?: string[]) {
  if (!widgets?.length) loading.value = true
  error.value = ''
  try {
    data.value = await fetchAnalyticsDashboard({
      start: auth.dateRange.start || undefined,
      end: auth.dateRange.end || undefined,
    })
    if (widgets?.length) {
      flash.value = new Set(widgets)
      setTimeout(() => {
        flash.value = new Set()
      }, 900)
    }
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Failed to load analytics'
  } finally {
    loading.value = false
  }
}

function onSocketEvent(event: DashboardWsEvent) {
  if (event.type === 'connected') return
  void load(event.widgets)
}

let unsubscribeLive: (() => void) | undefined

watch(
  () => [auth.dateRange.start, auth.dateRange.end],
  () => {
    void load()
  },
)

const now = ref(new Date())
let clockTimer: ReturnType<typeof setInterval>
onMounted(async () => {
  clockTimer = setInterval(() => {
    now.value = new Date()
  }, 1000)
  unsubscribeLive = live.subscribe(onSocketEvent)
  await Promise.all([
    load(),
    attendance.fetchMyToday(),
    attendance.fetchPolicy(),
    auth.role === 'owner' ? attendance.fetchAllToday() : Promise.resolve(),
  ])
})
onUnmounted(() => {
  clearInterval(clockTimer)
  unsubscribeLive?.()
})

const checkedIn = computed(() => !!attendance.myRecord?.check_in)
const checkedOut = computed(() => !!attendance.myRecord?.check_out)
const currentTime = computed(() =>
  now.value.toLocaleTimeString('en-AE', { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
)

async function handleCheckIn() {
  await attendance.checkIn()
}
async function handleCheckOut() {
  await attendance.checkOut()
}

const statusLabel: Record<string, string> = {
  on_time: 'On Time',
  late: 'Late',
  absent: 'Absent',
}
const statusClass: Record<string, string> = {
  on_time: 'pill--green',
  late: 'pill--amber',
  absent: 'pill--red',
}
</script>

<template>
  <div class="analytics">
    <header class="analytics__hero">
      <div>
        <p class="analytics__eyebrow">
          Analytics
          <span class="analytics__live-dot" aria-hidden="true" />
          <span class="analytics__live-label">Live</span>
        </p>
        <h1 class="analytics__title">{{ greeting }}, {{ auth.user?.first_name }}</h1>
        <p class="analytics__sub">
          {{ isOwner ? 'Company-wide hiring intelligence' : 'Your personal hiring workspace' }}
          · {{ auth.dateRange.start }} → {{ auth.dateRange.end }}
        </p>
      </div>
      <div v-if="auth.role === 'recruiter'" class="checkin">
        <div class="checkin__meta">
          <span>Attendance</span>
          <strong>{{ currentTime }}</strong>
        </div>
        <button
          v-if="!checkedIn"
          class="checkin__btn checkin__btn--in"
          :disabled="attendance.loading"
          @click="handleCheckIn"
        >
          Check in
        </button>
        <button
          v-else
          class="checkin__btn checkin__btn--out"
          :disabled="checkedOut || attendance.loading"
          @click="handleCheckOut"
        >
          {{ checkedOut ? 'Checked out' : 'Check out' }}
        </button>
        <p v-if="attendance.policy" class="checkin__hint">
          Late after {{ formatOfficeTime(attendance.policy.late_threshold) }}
        </p>
      </div>
    </header>

    <HrmsAlert v-if="error" type="error" dismissible @dismiss="error = ''">{{ error }}</HrmsAlert>

    <section v-if="loading && !data" class="analytics__loading">Loading analytics…</section>

    <template v-else-if="data">
      <section class="kpi-grid" :class="{ 'is-flash': flash.has('kpis') }">
        <article v-for="card in cards" :key="card.label" class="kpi">
          <span class="kpi__label">{{ card.label }}</span>
          <strong class="kpi__value">{{ card.value }}</strong>
        </article>
      </section>

      <section class="chart-grid">
        <article class="chart-card chart-card--wide" :class="{ 'is-flash': flash.has('pipeline_stages') }">
          <header class="chart-card__head">
            <h2>Pipeline stages</h2>
            <span>{{ data.kpis.in_pipeline }} active</span>
          </header>
          <div class="pipeline-bars">
            <div
              v-for="stage in data.charts.pipeline_stages"
              :key="stage.name"
              class="pipeline-bars__col"
            >
              <span class="pipeline-bars__n">{{ stage.count }}</span>
              <div class="pipeline-bars__track">
                <div
                  class="pipeline-bars__fill"
                  :style="{
                    height: `${Math.max((stage.count / pipelineMax) * 100, stage.count ? 8 : 0)}%`,
                    background: STAGE_COLORS[stage.name] || '#94a3b8',
                  }"
                />
              </div>
              <span class="pipeline-bars__label">{{ stage.name }}</span>
            </div>
          </div>
        </article>

        <article class="chart-card" :class="{ 'is-flash': flash.has('candidate_status') }">
          <header class="chart-card__head"><h2>Candidate status</h2></header>
          <DonutChart compact :items="data.charts.candidate_status" />
        </article>

        <article
          v-if="isOwner"
          class="chart-card"
          :class="{ 'is-flash': flash.has('recruiter_performance') }"
        >
          <header class="chart-card__head"><h2>Recruiter performance</h2></header>
          <BarChart compact :items="data.charts.recruiter_performance" horizontal color="#7a3b68" />
        </article>

        <article
          v-else
          class="chart-card"
          :class="{ 'is-flash': flash.has('candidate_uploads_monthly') }"
        >
          <header class="chart-card__head"><h2>My candidate uploads</h2></header>
          <BarChart compact :items="data.charts.candidate_uploads_monthly" color="#0ea5e9" />
        </article>

        <article class="chart-card" :class="{ 'is-flash': flash.has('placements_monthly') }">
          <header class="chart-card__head"><h2>Placements</h2></header>
          <BarChart compact :items="data.charts.placements_monthly" color="#22c55e" />
        </article>

        <article
          v-if="isOwner"
          class="chart-card"
          :class="{ 'is-flash': flash.has('client_placements') }"
        >
          <header class="chart-card__head"><h2>Client-wise placements</h2></header>
          <BarChart compact :items="data.charts.client_placements" color="#c4a35a" />
        </article>

        <article
          v-else
          class="chart-card"
          :class="{ 'is-flash': flash.has('interviews_vs_offers') }"
        >
          <header class="chart-card__head"><h2>Interviews vs offers</h2></header>
          <BarChart compact :items="data.charts.interviews_vs_offers" horizontal color="#8b5cf6" />
        </article>

        <article
          v-if="isOwner"
          class="chart-card chart-card--wide"
          :class="{ 'is-flash': flash.has('recruiter_activity_heatmap') }"
        >
          <header class="chart-card__head"><h2>Recruiter activity</h2></header>
          <HeatmapChart compact :cells="data.charts.recruiter_activity_heatmap" />
        </article>

        <article
          v-else
          class="chart-card chart-card--wide"
          :class="{ 'is-flash': flash.has('todays_interviews') }"
        >
          <header class="chart-card__head"><h2>Upcoming interviews</h2></header>
          <div class="cal">
            <div
              v-for="day in calendarDays"
              :key="day.key"
              class="cal__day"
              :class="{ 'cal__day--today': day.isToday, 'cal__day--busy': day.items.length }"
            >
              <span class="cal__label">{{ day.label }}</span>
              <div v-if="!day.items.length" class="cal__empty">—</div>
              <ul v-else class="cal__list">
                <li v-for="row in day.items" :key="str(row.id)">
                  <strong>{{ str(row.candidate_name) }}</strong>
                  <span>{{ formatWhen(row.scheduled_at) }}</span>
                </li>
              </ul>
            </div>
          </div>
        </article>
      </section>

      <section class="table-grid">
        <article class="panel" :class="{ 'is-flash': flash.has('recent_placements') }">
          <header class="panel__head"><h2>Recent placements</h2></header>
          <div v-if="!data.tables.recent_placements.length" class="empty">No placements yet</div>
          <ul v-else class="list">
            <li v-for="row in data.tables.recent_placements" :key="str(row.id)">
              <div>
                <strong>{{ str(row.candidate_name) }}</strong>
                <span>{{ str(row.client_name) }} · {{ str(row.job_title) }}</span>
              </div>
              <em>{{ formatWhen(row.joined_date) }}</em>
            </li>
          </ul>
        </article>

        <article class="panel" :class="{ 'is-flash': flash.has('recent_activities') }">
          <header class="panel__head"><h2>Recent activity</h2></header>
          <ul class="list">
            <li v-for="row in data.tables.recent_activities" :key="str(row.id)">
              <div>
                <strong>{{ str(row.title) }}</strong>
                <span>{{ str(row.description) }}</span>
              </div>
              <em>{{ formatWhen(row.created_at) }}</em>
            </li>
          </ul>
        </article>

        <article
          v-if="!isOwner"
          class="panel"
          :class="{ 'is-flash': flash.has('recent_candidates') }"
        >
          <header class="panel__head"><h2>Recently uploaded</h2></header>
          <ul class="list">
            <li v-for="row in data.tables.recent_candidates" :key="str(row.id)">
              <div>
                <strong>{{ str(row.name) }}</strong>
                <span>{{ str(row.email) }}</span>
              </div>
              <em>{{ str(row.status) }}</em>
            </li>
          </ul>
        </article>

        <article class="panel" :class="{ 'is-flash': flash.has('pending_tasks') }">
          <header class="panel__head"><h2>{{ isOwner ? 'Pending reviews' : 'My pending tasks' }}</h2></header>
          <div v-if="!data.tables.pending_tasks.length" class="empty">All caught up</div>
          <ul v-else class="list">
            <li v-for="row in data.tables.pending_tasks" :key="str(row.id)">
              <div>
                <strong>{{ str(row.title) }}</strong>
                <span>{{ str(row.subtitle) }}</span>
              </div>
              <em>{{ formatWhen(row.created_at) }}</em>
            </li>
          </ul>
        </article>

        <article
          v-if="!isOwner"
          class="panel"
          :class="{ 'is-flash': flash.has('todays_interviews') }"
        >
          <header class="panel__head"><h2>Today's interviews</h2></header>
          <div v-if="!data.tables.todays_interviews.length" class="empty">No interviews today</div>
          <ul v-else class="list">
            <li v-for="row in data.tables.todays_interviews" :key="str(row.id)">
              <div>
                <strong>{{ str(row.candidate_name) }}</strong>
                <span>{{ str(row.job_title) }}</span>
              </div>
              <em>{{ formatWhen(row.scheduled_at) }}</em>
            </li>
          </ul>
        </article>

        <article
          v-if="!isOwner"
          class="panel"
          :class="{ 'is-flash': flash.has('recent_feedback') }"
        >
          <header class="panel__head"><h2>Recent feedback</h2></header>
          <div v-if="!data.tables.recent_feedback.length" class="empty">No feedback yet</div>
          <ul v-else class="list">
            <li v-for="row in data.tables.recent_feedback" :key="str(row.id)">
              <div>
                <strong>{{ str(row.candidate_name) }}</strong>
                <span>{{ str(row.feedback) }}</span>
              </div>
            </li>
          </ul>
        </article>

        <article v-if="isOwner && auth.role === 'owner'" class="panel panel--wide">
          <header class="panel__head"><h2>Team attendance — today</h2></header>
          <div v-if="attendance.allLoading" class="empty">Loading…</div>
          <table v-else class="mini-table">
            <thead>
              <tr>
                <th>Recruiter</th>
                <th>Check in</th>
                <th>Check out</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in attendance.allRecords" :key="row.user_id">
                <td>{{ row.first_name }} {{ row.last_name }}</td>
                <td>{{ row.check_in ? new Date(row.check_in).toLocaleTimeString('en-AE', { hour: '2-digit', minute: '2-digit' }) : '—' }}</td>
                <td>{{ row.check_out ? new Date(row.check_out).toLocaleTimeString('en-AE', { hour: '2-digit', minute: '2-digit' }) : '—' }}</td>
                <td><span class="pill" :class="statusClass[row.status]">{{ statusLabel[row.status] }}</span></td>
              </tr>
            </tbody>
          </table>
        </article>
      </section>
    </template>
  </div>
</template>

<style scoped>
.analytics {
  display: flex;
  flex-direction: column;
  gap: 22px;
  max-width: 1280px;
  margin: 0 auto;
}

.analytics__hero {
  display: flex;
  justify-content: space-between;
  gap: 20px;
  align-items: flex-start;
  flex-wrap: wrap;
}

.analytics__eyebrow {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  margin: 0 0 6px;
  font-size: 0.72rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--hrms-text-muted);
}

.analytics__live-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #22c55e;
  box-shadow: 0 0 0 3px rgba(34, 197, 94, 0.2);
}

.analytics__live-label {
  font-size: 0.68rem;
  font-weight: 600;
  color: #16a34a;
  text-transform: none;
  letter-spacing: 0;
}

.analytics__title {
  margin: 0 0 6px;
  font-family: var(--hrms-font-display);
  font-size: clamp(1.6rem, 2vw, 2rem);
  font-weight: 600;
  color: var(--hrms-primary-dark);
}

.analytics__sub {
  margin: 0;
  color: var(--hrms-text-muted);
  font-size: 0.9rem;
}

.analytics__loading {
  padding: 48px;
  text-align: center;
  color: var(--hrms-text-muted);
}

.checkin {
  display: flex;
  flex-direction: column;
  gap: 8px;
  min-width: 180px;
  padding: 14px 16px;
  border: 1px solid var(--hrms-border);
  border-radius: 14px;
  background: var(--hrms-surface-elevated);
}

.checkin__meta {
  display: flex;
  justify-content: space-between;
  font-size: 0.75rem;
  color: var(--hrms-text-muted);
}

.checkin__btn {
  border: 0;
  border-radius: 10px;
  padding: 10px 12px;
  font-weight: 600;
  cursor: pointer;
  color: #fff;
}

.checkin__btn--in { background: #16a34a; }
.checkin__btn--out { background: #dc2626; }
.checkin__btn:disabled { opacity: 0.55; cursor: not-allowed; }
.checkin__hint { margin: 0; font-size: 0.72rem; color: var(--hrms-text-muted); }

.kpi-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  gap: 12px;
}

.kpi {
  padding: 16px;
  border: 1px solid var(--hrms-border);
  border-radius: 14px;
  background: var(--hrms-surface-elevated);
  box-shadow: var(--hrms-shadow-sm);
  display: flex;
  flex-direction: column;
  gap: 8px;
  transition: border-color 0.2s ease, transform 0.2s ease;
}

.kpi__label {
  font-size: 0.7rem;
  font-weight: 600;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  color: var(--hrms-text-muted);
}

.kpi__value {
  font-family: var(--hrms-font-display);
  font-size: 1.55rem;
  color: var(--hrms-primary-dark);
  line-height: 1;
}

.chart-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 16px;
}

.chart-card {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 14px 16px;
  min-height: 168px;
  border: 1px solid var(--hrms-border);
  border-radius: 14px;
  background: var(--hrms-surface-elevated);
  box-shadow: var(--hrms-shadow-sm);
}

.chart-card--wide {
  grid-column: 1 / -1;
}

.chart-card__head {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  gap: 10px;
}

.chart-card__head h2 {
  margin: 0;
  font-size: 0.82rem;
  font-weight: 650;
  color: var(--hrms-primary-dark);
}

.chart-card__head span {
  font-size: 0.72rem;
  color: var(--hrms-text-muted);
}

.table-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}

.panel {
  padding: 16px;
  border: 1px solid var(--hrms-border);
  border-radius: 14px;
  background: var(--hrms-surface-elevated);
  box-shadow: var(--hrms-shadow-sm);
  min-height: 180px;
}

.panel--wide {
  grid-column: 1 / -1;
}

.panel__head {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  gap: 12px;
  margin-bottom: 14px;
}

.panel__head h2 {
  margin: 0;
  font-size: 0.95rem;
  font-weight: 650;
  color: var(--hrms-primary-dark);
}

.panel__head span {
  font-size: 0.75rem;
  color: var(--hrms-text-muted);
}

.is-flash {
  animation: pulse 0.9s ease;
}

@keyframes pulse {
  0% { box-shadow: 0 0 0 0 rgba(122, 59, 104, 0.25); }
  100% { box-shadow: var(--hrms-shadow-sm); }
}

.pipeline-bars {
  display: flex;
  align-items: flex-end;
  gap: 8px;
  min-height: 132px;
  overflow-x: auto;
}

.pipeline-bars__col {
  flex: 1 1 0;
  min-width: 56px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
}

.pipeline-bars__n {
  font-size: 0.75rem;
  font-weight: 700;
}

.pipeline-bars__track {
  width: 100%;
  max-width: 34px;
  height: 88px;
  display: flex;
  align-items: flex-end;
  border-radius: 8px 8px 3px 3px;
  background: color-mix(in srgb, var(--hrms-surface-muted) 85%, white);
}

.pipeline-bars__fill {
  width: 100%;
  border-radius: 8px 8px 2px 2px;
  transition: height 0.35s ease;
}

.pipeline-bars__label {
  font-size: 0.65rem;
  text-align: center;
  color: var(--hrms-text-muted);
}

.list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.list li {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  padding-bottom: 10px;
  border-bottom: 1px solid var(--hrms-border);
}

.list li:last-child {
  border-bottom: 0;
  padding-bottom: 0;
}

.list strong {
  display: block;
  font-size: 0.86rem;
  color: var(--hrms-text);
}

.list span {
  display: block;
  font-size: 0.75rem;
  color: var(--hrms-text-muted);
  margin-top: 2px;
}

.list em {
  font-style: normal;
  font-size: 0.72rem;
  color: var(--hrms-text-muted);
  white-space: nowrap;
}

.list--notify li {
  align-items: flex-start;
  justify-content: flex-start;
}

.list--notify i {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  margin-top: 6px;
  background: var(--hrms-primary);
  flex-shrink: 0;
}

.list--notify i[data-type='candidate.rejected'],
.list--notify i[data-type='job.closed'] {
  background: #ef4444;
}

.list--notify i[data-type='placement.completed'],
.list--notify i[data-type='candidate.approved'] {
  background: #22c55e;
}

.cal {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
  gap: 10px;
}

.cal__day {
  min-height: 96px;
  padding: 10px;
  border: 1px solid var(--hrms-border);
  border-radius: 12px;
  background: color-mix(in srgb, var(--hrms-surface-muted) 70%, white);
}

.cal__day--today {
  border-color: color-mix(in srgb, var(--hrms-primary) 55%, var(--hrms-border));
  background: color-mix(in srgb, var(--hrms-primary) 8%, white);
}

.cal__day--busy {
  background: var(--hrms-surface-elevated);
}

.cal__label {
  display: block;
  margin-bottom: 8px;
  font-size: 0.7rem;
  font-weight: 650;
  color: var(--hrms-text-muted);
}

.cal__empty {
  color: var(--hrms-text-muted);
  font-size: 0.85rem;
}

.cal__list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.cal__list strong {
  display: block;
  font-size: 0.75rem;
  color: var(--hrms-text);
}

.cal__list span {
  font-size: 0.68rem;
  color: var(--hrms-text-muted);
}

.empty {
  padding: 28px 8px;
  text-align: center;
  color: var(--hrms-text-muted);
  font-size: 0.85rem;
}

.mini-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.84rem;
}

.mini-table th,
.mini-table td {
  text-align: left;
  padding: 10px 8px;
  border-bottom: 1px solid var(--hrms-border);
}

.mini-table th {
  font-size: 0.7rem;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: var(--hrms-text-muted);
}

.pill {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 999px;
  font-size: 0.72rem;
  font-weight: 600;
}

.pill--green { background: #dcfce7; color: #15803d; }
.pill--amber { background: #ffedd5; color: #c2410c; }
.pill--red { background: #fee2e2; color: #b91c1c; }

@media (max-width: 1100px) {
  .chart-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 900px) {
  .chart-grid,
  .table-grid {
    grid-template-columns: 1fr;
  }
  .chart-card--wide,
  .panel--wide {
    grid-column: auto;
  }
}
</style>
