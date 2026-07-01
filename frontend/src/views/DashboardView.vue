<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useAttendanceStore } from '@/stores/attendance'

const auth = useAuthStore()
const attendance = useAttendanceStore()

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

// ── Live clock ────────────────────────────────────────────────────────────────
const now = ref(new Date())
let clockTimer: ReturnType<typeof setInterval>

onMounted(async () => {
  clockTimer = setInterval(() => { now.value = new Date() }, 1000)
  await attendance.fetchMyToday()
  if (auth.role === 'owner') {
    await attendance.fetchAllToday()
  }
})

onUnmounted(() => clearInterval(clockTimer))

const currentTime = computed(() =>
  now.value.toLocaleTimeString('en-AE', { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
)

// ── Attendance helpers ────────────────────────────────────────────────────────
const checkedIn = computed(() => !!attendance.myRecord?.check_in)
const checkedOut = computed(() => !!attendance.myRecord?.check_out)

function formatTime(iso: string | null | undefined): string {
  if (!iso) return '—'
  return new Date(iso).toLocaleTimeString('en-AE', { hour: '2-digit', minute: '2-digit' })
}

async function handleCheckIn() {
  await attendance.checkIn()
  if (auth.role === 'owner') await attendance.fetchAllToday()
}

async function handleCheckOut() {
  await attendance.checkOut()
  if (auth.role === 'owner') await attendance.fetchAllToday()
}

// ── Owner table helpers ───────────────────────────────────────────────────────
const statusLabel: Record<string, string> = {
  on_time: 'On Time',
  late: 'Late',
  absent: 'Absent',
}
const statusClass: Record<string, string> = {
  on_time: 'chip--green',
  late: 'chip--orange',
  absent: 'chip--red',
}

const attendanceSummary = computed(() => {
  const rows = attendance.allRecords
  return {
    present: rows.filter((r) => r.status !== 'absent').length,
    late: rows.filter((r) => r.status === 'late').length,
    absent: rows.filter((r) => r.status === 'absent').length,
    total: rows.length,
  }
})
</script>

<template>
  <div class="dashboard">

    <!-- ── Top row: greeting (left) + check-in card (right, recruiters only) ── -->
    <div class="dashboard__top" :class="{ 'dashboard__top--full': auth.role !== 'recruiter' }">
      <header class="dashboard__header">
        <h2 class="dashboard__greeting">{{ greeting }}, {{ auth.user?.first_name }}</h2>
        <p class="dashboard__subtitle">
          Here's your hiring overview for
          <strong>{{ auth.dateRange.start }}</strong> to <strong>{{ auth.dateRange.end }}</strong>
        </p>
      </header>

      <!-- Check-in card pinned top-right — recruiters only -->
      <div v-if="auth.role === 'recruiter'" class="checkin-card">
        <div class="checkin-card__header">
          <span class="checkin-card__title">Today's Attendance</span>
          <span class="checkin-card__clock">{{ currentTime }}</span>
        </div>

        <div class="checkin-card__schedule">
          <span>In: <strong>9:30 AM</strong></span>
          <span class="sep">·</span>
          <span>Out: <strong>6:30 PM</strong></span>
          <span class="sep">·</span>
          <span>Late after: <strong>10:00 AM</strong></span>
        </div>

        <!-- Not yet checked in: show Check In button -->
        <div v-if="!checkedIn" class="checkin-card__actions">
          <button
            class="btn btn--checkin"
            :disabled="attendance.loading"
            @click="handleCheckIn"
          >
            {{ attendance.loading ? 'Checking in…' : 'Check In' }}
          </button>
        </div>

        <!-- Already checked in: show confirmation badge + checkout button -->
        <div v-else class="checkin-card__confirmed">
          <div class="confirmed-badge">
            <span class="confirmed-badge__icon">✓</span>
            <div>
              <span class="confirmed-badge__label">Checked in at</span>
              <span class="confirmed-badge__time">{{ formatTime(attendance.myRecord?.check_in) }}</span>
            </div>
            <span
              v-if="attendance.myRecord?.status"
              class="chip"
              :class="statusClass[attendance.myRecord.status]"
            >
              {{ statusLabel[attendance.myRecord.status] }}
            </span>
          </div>
          <button
            class="btn btn--checkout"
            :disabled="checkedOut || attendance.loading"
            @click="handleCheckOut"
          >
            {{ attendance.loading ? 'Checking out…' : checkedOut ? '✓ Checked Out' : 'Check Out' }}
          </button>
        </div>

        <p v-if="attendance.error" class="checkin-card__error">{{ attendance.error }}</p>
      </div>
    </div>

    <!-- KPI stat cards -->
    <section class="dashboard__stats" aria-label="Key metrics">
      <article v-for="stat in stats" :key="stat.label" class="dashboard__stat-card">
        <span class="dashboard__stat-label">{{ stat.label }}</span>
        <span class="dashboard__stat-value">{{ stat.value }}</span>
        <span class="dashboard__stat-trend">{{ stat.trend }}</span>
      </article>
    </section>

    <!-- Owner: team attendance table -->
    <section v-if="auth.role === 'owner'" class="attendance-table-card" aria-label="Team attendance">
      <div class="attendance-table-card__header">
        <span class="attendance-table-card__title">Team Attendance — Today</span>
        <div class="attendance-table-card__summary">
          <span class="chip chip--green">Present {{ attendanceSummary.present }}</span>
          <span class="chip chip--orange">Late {{ attendanceSummary.late }}</span>
          <span class="chip chip--red">Absent {{ attendanceSummary.absent }}</span>
          <span class="chip chip--neutral">Total {{ attendanceSummary.total }}</span>
        </div>
      </div>

      <div v-if="attendance.allLoading" class="attendance-table-card__loading">Loading…</div>
      <table v-else class="att-table">
        <thead>
          <tr>
            <th>Recruiter</th>
            <th>Code</th>
            <th>Designation</th>
            <th>Check In</th>
            <th>Check Out</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="row in attendance.allRecords" :key="row.user_id">
            <td>{{ row.first_name }} {{ row.last_name }}</td>
            <td class="att-table__code">{{ row.employee_code ?? '—' }}</td>
            <td>{{ row.designation ?? '—' }}</td>
            <td>{{ formatTime(row.check_in) }}</td>
            <td>{{ formatTime(row.check_out) }}</td>
            <td>
              <span class="chip" :class="statusClass[row.status]">
                {{ statusLabel[row.status] }}
              </span>
            </td>
          </tr>
          <tr v-if="attendance.allRecords.length === 0">
            <td colspan="6" class="att-table__empty">No recruiters found</td>
          </tr>
        </tbody>
      </table>
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
/* ── Top row layout ─────────────────────────────────────────────────────── */
.dashboard__top {
  display: grid;
  grid-template-columns: 1fr 380px;
  gap: 24px;
  align-items: start;
  margin-bottom: 28px;
}

.dashboard__top--full {
  grid-template-columns: 1fr;
}

@media (max-width: 860px) {
  .dashboard__top {
    grid-template-columns: 1fr;
  }
}

.dashboard__header {
  padding-top: 4px;
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

/* ── KPI cards ──────────────────────────────────────────────────────────── */
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

/* ── Check-in card ──────────────────────────────────────────────────────── */
.checkin-card {
  padding: 22px 24px;
  background: var(--hrms-surface-elevated);
  border: 1px solid var(--hrms-border);
  border-radius: var(--hrms-radius-lg);
  box-shadow: var(--hrms-shadow-sm);
  border-top: 3px solid var(--hrms-accent);
}

.checkin-card__header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.checkin-card__title {
  font-size: 0.8rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.07em;
  color: var(--hrms-text-muted);
}

.checkin-card__clock {
  font-family: var(--hrms-font-display);
  font-size: 1.15rem;
  font-weight: 700;
  color: var(--hrms-primary-dark);
  letter-spacing: 0.04em;
}

.checkin-card__schedule {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  align-items: center;
  font-size: 0.78rem;
  color: var(--hrms-text-muted);
  margin-bottom: 16px;
}

.checkin-card__schedule strong {
  color: var(--hrms-primary);
}

.sep {
  color: var(--hrms-border);
}

.checkin-card__actions {
  display: flex;
}

.btn {
  flex: 1;
  padding: 11px 14px;
  border: none;
  border-radius: var(--hrms-radius-md, 8px);
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
  transition: opacity 0.15s, background 0.15s;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn--checkin {
  background: #16a34a;
  color: #fff;
}

.btn--checkin:not(:disabled):hover {
  background: #15803d;
}

.btn--checkout {
  width: 100%;
  margin-top: 10px;
  background: #dc2626;
  color: #fff;
}

.btn--checkout:not(:disabled):hover {
  background: #b91c1c;
}

/* Confirmed state */
.checkin-card__confirmed {
  margin-top: 2px;
}

.confirmed-badge {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background: #f0fdf4;
  border: 1px solid #bbf7d0;
  border-radius: var(--hrms-radius-md, 8px);
}

.confirmed-badge__icon {
  font-size: 1.1rem;
  color: #16a34a;
  font-weight: 700;
  flex-shrink: 0;
}

.confirmed-badge__label {
  display: block;
  font-size: 0.7rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: #16a34a;
}

.confirmed-badge__time {
  display: block;
  font-family: var(--hrms-font-display);
  font-size: 1.15rem;
  font-weight: 700;
  color: #15803d;
}

.confirmed-badge .chip {
  margin-left: auto;
  flex-shrink: 0;
}

.checkin-card__error {
  margin: 10px 0 0;
  font-size: 0.8rem;
  color: #dc2626;
}

/* ── Status chips ───────────────────────────────────────────────────────── */
.chip {
  display: inline-block;
  padding: 3px 10px;
  border-radius: 999px;
  font-size: 0.75rem;
  font-weight: 600;
  white-space: nowrap;
}

.chip--green  { background: #dcfce7; color: #15803d; }
.chip--orange { background: #ffedd5; color: #c2410c; }
.chip--red    { background: #fee2e2; color: #b91c1c; }
.chip--neutral {
  background: var(--hrms-secondary, #f1f5f9);
  color: var(--hrms-text-muted, #64748b);
}

/* ── Team attendance table ──────────────────────────────────────────────── */
.attendance-table-card {
  background: var(--hrms-surface-elevated);
  border: 1px solid var(--hrms-border);
  border-radius: var(--hrms-radius-lg);
  box-shadow: var(--hrms-shadow-sm);
  overflow: hidden;
  margin-bottom: 28px;
}

.attendance-table-card__header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
  padding: 16px 20px;
  border-bottom: 1px solid var(--hrms-border);
}

.attendance-table-card__title {
  font-size: 0.82rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--hrms-text-muted);
}

.attendance-table-card__summary {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.attendance-table-card__loading {
  padding: 32px;
  text-align: center;
  font-size: 0.875rem;
  color: var(--hrms-text-muted);
}

.att-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.875rem;
}

.att-table thead tr {
  background: var(--hrms-secondary, #f8fafc);
}

.att-table th {
  padding: 10px 16px;
  text-align: left;
  font-size: 0.72rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--hrms-text-muted);
  border-bottom: 1px solid var(--hrms-border);
}

.att-table td {
  padding: 12px 16px;
  border-bottom: 1px solid var(--hrms-border);
  color: var(--hrms-primary-dark);
}

.att-table tbody tr:last-child td {
  border-bottom: none;
}

.att-table tbody tr:hover td {
  background: var(--hrms-secondary, #f8fafc);
}

.att-table__code {
  font-family: var(--hrms-font-mono, monospace);
  font-size: 0.8rem;
  color: var(--hrms-text-muted);
}

.att-table__empty {
  text-align: center;
  color: var(--hrms-text-muted);
  padding: 32px;
}

/* ── Welcome card ───────────────────────────────────────────────────────── */
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
