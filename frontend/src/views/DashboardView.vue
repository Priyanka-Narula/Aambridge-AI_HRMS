<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { fetchAnalyticsDashboard } from '@/api/dashboard'
import BarChart from '@/components/dashboard/BarChart.vue'
import DonutChart from '@/components/dashboard/DonutChart.vue'
import LineChart from '@/components/dashboard/LineChart.vue'
import RecruiterPerformance from '@/components/dashboard/RecruiterPerformance.vue'
import HrmsAlert from '@/components/ui/HrmsAlert.vue'
import { useAttendanceStore } from '@/stores/attendance'
import { useAuthStore } from '@/stores/auth'
import { useDashboardLiveStore } from '@/stores/dashboardLive'
import type { AnalyticsDashboard, DashboardWsEvent } from '@/types/dashboard'
import { formatOfficeTime, formatUaeClock, formatUaeTime, OFFICE_TIMEZONE } from '@/utils/format'

const auth = useAuthStore()
const attendance = useAttendanceStore()
const live = useDashboardLiveStore()

const loading = ref(true)
const error = ref('')
const data = ref<AnalyticsDashboard | null>(null)
const flash = ref<Set<string>>(new Set())
const recruiterPerformanceRefreshKey = ref(0)

const isOwner = computed(() => data.value?.role === 'owner' || auth.role === 'owner')

const greeting = computed(() => {
  const hour = new Date().getHours()
  if (hour < 12) return 'Good morning'
  if (hour < 17) return 'Good afternoon'
  return 'Good evening'
})

const cards = computed(() => {
  const k = data.value?.kpis
  if (!k) return []
  if (isOwner.value) {
    return [
      { key: 'kpis', label: 'Total Candidates', value: k.total_candidates },
      { key: 'kpis', label: 'Active Jobs', value: k.open_jobs },
      { key: 'kpis', label: 'Placements', value: k.placements },
      { key: 'kpis', label: 'Total Clients', value: k.total_clients },
      { key: 'kpis', label: 'Revenue', value: formatMoney(k.revenue) },
    ]
  }
  return [
    { key: 'kpis', label: 'My Active Jobs', value: k.jobs_assigned },
    { key: 'kpis', label: 'My Candidates', value: k.my_candidates },
    { key: 'kpis', label: 'Interviews Today', value: data.value?.tables.todays_interviews.length ?? 0 },
    { key: 'kpis', label: 'Offers Sent', value: k.offers },
    { key: 'kpis', label: 'Placements', value: k.placements },
  ]
})

const heroTitle = computed(() => (isOwner.value ? 'Owner Dashboard' : 'Recruiter Dashboard'))
const heroSubtitle = computed(() =>
  isOwner.value
    ? "Welcome back. Here's what's happening with your HR operations."
    : "Here's your personal hiring snapshot for today.",
)

const kpiMeta: Record<string, { icon: string; hint: string }> = {
  'Total Candidates': { icon: '◉', hint: 'Overall talent pool' },
  'Active Jobs': { icon: '▣', hint: 'Open positions' },
  Placements: { icon: '✓', hint: 'Successful joins' },
  'Total Clients': { icon: '◍', hint: 'Client accounts' },
  Revenue: { icon: '₹', hint: 'Finance metric' },
  'My Active Jobs': { icon: '▣', hint: 'Assigned requisitions' },
  'My Candidates': { icon: '◎', hint: 'Candidates in scope' },
  'Interviews Today': { icon: '◷', hint: 'Scheduled interviews' },
  'Offers Sent': { icon: '✦', hint: 'Offers released' },
  'Monthly Avg Placements': { icon: '◎', hint: 'Placement velocity' },
  'Avg Time to Hire': { icon: '⏱', hint: 'Hiring efficiency' },
}

const pipelineBars = computed(() =>
  (data.value?.charts.pipeline_stages ?? []).map((s) => ({
    label: s.name,
    value: s.count,
  })),
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
  recruiterPerformanceRefreshKey.value += 1
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

function onVisible() {
  if (document.visibilityState === 'visible') void load()
}

onMounted(async () => {
  clockTimer = setInterval(() => {
    now.value = new Date()
  }, 1000)
  unsubscribeLive = live.subscribe(onSocketEvent)
  document.addEventListener('visibilitychange', onVisible)
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
  document.removeEventListener('visibilitychange', onVisible)
})

const checkedIn = computed(() => !!attendance.myRecord?.check_in)
const checkedOut = computed(() => !!attendance.myRecord?.check_out)
const officeTimezone = computed(
  () => attendance.policy?.timezone || OFFICE_TIMEZONE,
)
const currentTime = computed(() => formatUaeClock(now.value))

const teamAttendanceStats = computed(() => {
  const rows = attendance.allRecords
  const total = rows.length
  const onTime = rows.filter((row) => row.status === 'on_time').length
  const late = rows.filter((row) => row.status === 'late').length
  const absent = rows.filter((row) => row.status === 'absent').length
  return { total, onTime, late, absent }
})

const teamAttendancePreview = computed(() => attendance.allRecords.slice(0, 8))

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
          {{ heroTitle }}
          <span class="analytics__live-dot" aria-hidden="true" />
          <span class="analytics__live-label">Live</span>
        </p>
        <h1 class="analytics__title">{{ greeting }}, {{ auth.user?.first_name }}!</h1>
        <p class="analytics__sub">
          {{ heroSubtitle }}
          · {{ auth.dateRange.start }} → {{ auth.dateRange.end }}
        </p>
      </div>
      <div v-if="auth.role === 'recruiter'" class="checkin">
        <div class="checkin__meta">
          <span>Attendance · UAE</span>
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
        <p v-if="attendance.myRecord?.check_in" class="checkin__hint">
          In {{ formatUaeTime(attendance.myRecord.check_in) }}
          <template v-if="attendance.myRecord.check_out">
            · Out {{ formatUaeTime(attendance.myRecord.check_out) }}
          </template>
        </p>
        <p v-if="attendance.policy" class="checkin__hint">
          Late after {{ formatOfficeTime(attendance.policy.late_threshold) }}
          ({{ officeTimezone }})
        </p>
      </div>
    </header>

    <section v-if="isOwner && auth.role === 'owner'" class="attendance-compact">
      <header class="attendance-compact__head">
        <h2>Team attendance</h2>
        <span>Today · UAE</span>
      </header>
      <div class="attendance-compact__stats">
        <span><strong>{{ teamAttendanceStats.total }}</strong> Total</span>
        <span><strong>{{ teamAttendanceStats.onTime }}</strong> On time</span>
        <span><strong>{{ teamAttendanceStats.late }}</strong> Late</span>
        <span><strong>{{ teamAttendanceStats.absent }}</strong> Absent</span>
      </div>
      <div v-if="attendance.allLoading" class="attendance-compact__loading">Loading attendance…</div>
      <ul v-else class="attendance-compact__list">
        <li v-for="row in teamAttendancePreview" :key="row.user_id">
          <div class="attendance-compact__person">
            <span class="attendance-compact__name">{{ row.first_name }} {{ row.last_name }}</span>
            <span v-if="row.check_in" class="attendance-compact__time">
              {{ formatUaeTime(row.check_in) }}
            </span>
          </div>
          <span class="pill" :class="statusClass[row.status]">{{ statusLabel[row.status] }}</span>
        </li>
      </ul>
    </section>

    <HrmsAlert v-if="error" type="error" dismissible @dismiss="error = ''">{{ error }}</HrmsAlert>

    <section v-if="loading && !data" class="analytics__loading">Loading analytics…</section>

    <section v-else-if="!data" class="analytics__loading">
      {{ error || 'No analytics data available.' }}
    </section>

    <template v-else-if="data">
      <section class="kpi-grid" :class="{ 'is-flash': flash.has('kpis') }">
        <article v-for="card in cards" :key="card.label" class="kpi">
          <div class="kpi__head">
            <span class="kpi__label">{{ card.label }}</span>
            <span class="kpi__icon">{{ kpiMeta[card.label]?.icon ?? '•' }}</span>
          </div>
          <strong class="kpi__value">{{ card.value }}</strong>
          <span class="kpi__hint">{{ kpiMeta[card.label]?.hint ?? 'Live metric' }}</span>
        </article>
      </section>

      <section class="chart-grid">
        <template v-if="isOwner">
          <article class="chart-card" :class="{ 'is-flash': flash.has('candidate_status') }">
            <header class="chart-card__head"><h2>Candidates by stage</h2></header>
            <DonutChart compact :items="pipelineBars" />
          </article>
          <article class="chart-card" :class="{ 'is-flash': flash.has('placements_monthly') }">
            <header class="chart-card__head"><h2>Placements trend</h2><span>View report</span></header>
            <LineChart compact :items="data.charts.placements_monthly" color="#7c3aed" />
          </article>
          <RecruiterPerformance
            :class="{ 'is-flash': flash.has('recruiter_performance') }"
            :refresh-key="recruiterPerformanceRefreshKey"
          />
        </template>

        <template v-else>
          <article class="chart-card" :class="{ 'is-flash': flash.has('pipeline_stages') }">
            <header class="chart-card__head"><h2>My candidates by stage</h2></header>
            <BarChart compact :items="pipelineBars" color="#4f46e5" />
          </article>
          <article class="chart-card" :class="{ 'is-flash': flash.has('upcoming_interviews') }">
            <header class="chart-card__head"><h2>My upcoming interviews</h2></header>
            <ul class="list list--tight">
              <li v-for="row in data.tables.upcoming_interviews.slice(0, 4)" :key="str(row.id)">
                <div>
                  <strong>{{ str(row.job_title) }}</strong>
                  <span>{{ str(row.candidate_name) }}</span>
                </div>
                <em>{{ formatWhen(row.scheduled_at) }}</em>
              </li>
            </ul>
          </article>
          <article class="chart-card" :class="{ 'is-flash': flash.has('pending_tasks') }">
            <header class="chart-card__head"><h2>My tasks</h2></header>
            <ul class="list list--tight">
              <li v-for="row in data.tables.pending_tasks.slice(0, 4)" :key="str(row.id)">
                <div>
                  <strong>{{ str(row.title) }}</strong>
                  <span>{{ str(row.subtitle) }}</span>
                </div>
                <em>{{ formatWhen(row.created_at) }}</em>
              </li>
            </ul>
          </article>
          <article class="chart-card chart-card--wide" :class="{ 'is-flash': flash.has('recent_activities') }">
            <header class="chart-card__head"><h2>Recent activity</h2></header>
            <ul class="list list--tight">
              <li v-for="row in data.tables.recent_activities.slice(0, 5)" :key="str(row.id)">
                <div>
                  <strong>{{ str(row.title) }}</strong>
                  <span>{{ str(row.description) }}</span>
                </div>
                <em>{{ formatWhen(row.created_at) }}</em>
              </li>
            </ul>
          </article>
        </template>
      </section>

      <section class="table-grid">
        <article
          v-if="isOwner"
          class="panel"
          :class="{ 'is-flash': flash.has('client_placements') }"
        >
          <header class="panel__head"><h2>Top clients by placements</h2></header>
          <ul class="list">
            <li v-for="row in data.charts.client_placements.slice(0, 6)" :key="row.label">
              <div>
                <strong>{{ row.label }}</strong>
                <span>Client</span>
              </div>
              <em>{{ row.value }}</em>
            </li>
          </ul>
        </article>

        <article class="panel" :class="{ 'is-flash': flash.has('recent_placements') }">
          <header class="panel__head"><h2>Recent placements</h2><span>View all</span></header>
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

        <article v-if="isOwner" class="panel" :class="{ 'is-flash': flash.has('recent_activities') }">
          <header class="panel__head"><h2>Activity feed</h2><span>View all</span></header>
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
          <header class="panel__head"><h2>Recently uploaded</h2><span>Latest</span></header>
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

        <article v-if="isOwner" class="panel" :class="{ 'is-flash': flash.has('pending_tasks') }">
          <header class="panel__head"><h2>{{ isOwner ? 'Pending reviews' : 'My tasks' }}</h2></header>
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
          <header class="panel__head"><h2>Today's interviews</h2><span>Schedule</span></header>
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

      </section>
    </template>
  </div>
</template>

<style scoped>
.analytics {
  display: flex;
  flex-direction: column;
  gap: 18px;
  max-width: 1280px;
  margin: 0 auto;
  padding: 6px;
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
  font-size: clamp(1.55rem, 2vw, 1.95rem);
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

.attendance-compact {
  padding: 12px 16px;
  border: 1px solid var(--hrms-border);
  border-radius: 16px;
  background: linear-gradient(180deg, #ffffff 0%, #fcf9ff 100%);
  box-shadow: var(--hrms-shadow-sm);
  display: grid;
  gap: 10px;
}

.attendance-compact__head {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
}

.attendance-compact__head h2 {
  margin: 0;
  font-size: 0.9rem;
  color: var(--hrms-primary-dark);
}

.attendance-compact__head span {
  font-size: 0.72rem;
  color: var(--hrms-text-muted);
}

.attendance-compact__stats {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  font-size: 0.76rem;
  color: var(--hrms-text-muted);
}

.attendance-compact__stats strong {
  color: var(--hrms-text);
}

.attendance-compact__loading {
  font-size: 0.8rem;
  color: var(--hrms-text-muted);
}

.attendance-compact__list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 8px;
}

.attendance-compact__list li {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
  padding: 8px 10px;
  border: 1px solid var(--hrms-border);
  border-radius: 10px;
  background: color-mix(in srgb, var(--hrms-surface-muted) 65%, white);
}

.attendance-compact__name {
  font-size: 0.75rem;
  color: var(--hrms-text);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.attendance-compact__person {
  display: flex;
  flex-direction: column;
  min-width: 0;
  gap: 2px;
}

.attendance-compact__time {
  font-size: 0.68rem;
  color: var(--hrms-text-muted);
}

.checkin {
  display: flex;
  flex-direction: column;
  gap: 8px;
  min-width: 220px;
  padding: 14px 16px;
  border: 1px solid var(--hrms-border);
  border-radius: 16px;
  background: linear-gradient(180deg, #ffffff 0%, #faf7ff 100%);
  box-shadow: var(--hrms-shadow-sm);
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
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14px;
}

.kpi {
  padding: 14px;
  border: 1px solid var(--hrms-border);
  border-radius: 16px;
  background: linear-gradient(180deg, #ffffff 0%, #fbf8ff 100%);
  box-shadow: var(--hrms-shadow-sm);
  display: flex;
  flex-direction: column;
  gap: 6px;
  transition: border-color 0.2s ease, transform 0.2s ease;
}

.kpi__head {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.kpi__label {
  font-size: 0.68rem;
  font-weight: 600;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  color: var(--hrms-text-muted);
}

.kpi__icon {
  width: 24px;
  height: 24px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  font-size: 0.85rem;
  color: #6d28d9;
  background: #f3e8ff;
}

.kpi__value {
  font-family: var(--hrms-font-display);
  font-size: 1.45rem;
  color: var(--hrms-primary-dark);
  line-height: 1;
}

.kpi__hint {
  font-size: 0.72rem;
  color: var(--hrms-text-muted);
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
  border-radius: 16px;
  background: linear-gradient(180deg, #ffffff 0%, #fdfbff 100%);
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
  border-radius: 16px;
  background: linear-gradient(180deg, #ffffff 0%, #fdfbff 100%);
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
  padding: 8px 0;
  border-bottom: 1px dashed var(--hrms-border);
}

.list li:last-child {
  border-bottom: 0;
  padding-bottom: 0;
}

.list strong {
  display: block;
  font-size: 0.86rem;
  color: var(--hrms-text);
  font-weight: 600;
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
  .kpi-grid,
  .chart-grid,
  .table-grid {
    grid-template-columns: 1fr;
  }
  .attendance-compact__list {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
  .chart-card--wide,
  .panel--wide {
    grid-column: auto;
  }
}
</style>
