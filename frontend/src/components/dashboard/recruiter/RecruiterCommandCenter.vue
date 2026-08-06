<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { fetchRecruiterCommand } from '@/api/dashboard'
import MultiSeriesLineChart from '@/components/dashboard/command/MultiSeriesLineChart.vue'
import type { ExecutiveKpi, FunnelStage } from '@/types/commandCenter'
import type { RecruiterCommandData } from '@/types/dashboard'

const props = defineProps<{
  start?: string
  end?: string
  refreshKey?: number
}>()

const data = ref<RecruiterCommandData | null>(null)
const loading = ref(true)
const error = ref('')

const visiblePeers = computed(() => {
  const peers = data.value?.standing.peers ?? []
  const me = data.value?.standing.me
  const top = peers.slice(0, 5)
  if (me && !top.some((row) => row.user_id === me.user_id)) return [...top, me]
  return top
})

async function load() {
  loading.value = true
  error.value = ''
  try {
    data.value = await fetchRecruiterCommand({ start: props.start, end: props.end })
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Failed to load recruiter insights'
  } finally {
    loading.value = false
  }
}

function formatValue(kpi: ExecutiveKpi) {
  if (kpi.value == null) return '—'
  if (kpi.unit === 'percent') return `${kpi.value}%`
  if (kpi.unit === 'days') return `${kpi.value}d`
  return new Intl.NumberFormat('en-IN').format(kpi.value)
}

function deltaLabel(kpi: ExecutiveKpi) {
  if (kpi.delta_pct == null) return 'No prior-period comparison'
  const sign = kpi.delta_pct > 0 ? '+' : ''
  return `${sign}${kpi.delta_pct}% vs prior period`
}

function stageWidth(stage: FunnelStage) {
  const max = Math.max(...(data.value?.hiring_funnel.stages.map((item) => item.count) ?? [1]), 1)
  return `${Math.max((stage.count / max) * 100, stage.count ? 8 : 2)}%`
}

watch(() => [props.start, props.end, props.refreshKey], load)
onMounted(load)
</script>

<template>
  <section class="recruiter-command">
    <div v-if="loading && !data" class="state">Loading your performance cockpit…</div>
    <div v-else-if="error && !data" class="state state--error">
      {{ error }}
      <button type="button" @click="load">Try again</button>
    </div>

    <template v-else-if="data">
      <section class="focus" aria-labelledby="today-focus-title">
        <header class="section-head">
          <div>
            <span class="eyebrow">Today</span>
            <h2 id="today-focus-title">Your focus</h2>
          </div>
          <span class="section-note">Clear what moves hiring forward</span>
        </header>
        <div class="focus__grid">
          <RouterLink
            v-for="item in data.today_focus"
            :key="item.key"
            :to="item.action_href"
            class="focus-card"
            :class="`focus-card--${item.tone}`"
          >
            <strong>{{ item.value }}</strong>
            <span>{{ item.label }}</span>
            <i aria-hidden="true">→</i>
          </RouterLink>
        </div>
      </section>

      <section class="kpi-grid" aria-label="Personal performance">
        <article v-for="kpi in data.kpis" :key="kpi.key" class="kpi-card">
          <div class="kpi-card__top">
            <span>{{ kpi.label }}</span>
            <i :title="kpi.tooltip">i</i>
          </div>
          <strong>{{ formatValue(kpi) }}</strong>
          <small
            :class="{
              positive: kpi.delta_pct != null && kpi.delta_pct > 0,
              negative: kpi.delta_pct != null && kpi.delta_pct < 0,
            }"
          >
            {{ deltaLabel(kpi) }}
          </small>
        </article>
      </section>

      <section class="two-col">
        <article class="panel standing">
          <header class="section-head">
            <div>
              <span class="eyebrow">Healthy competition</span>
              <h2>Team standing</h2>
            </div>
            <span class="section-note">Outcomes, quality and speed</span>
          </header>
          <div class="standing__summary">
            <div>
              <span>My rank</span>
              <strong>
                {{ data.standing.rank ? `#${data.standing.rank}` : '—' }}
                <small>of {{ data.standing.total_recruiters }}</small>
              </strong>
            </div>
            <div>
              <span>My score</span>
              <strong>{{ data.standing.me?.productivity_score ?? '—' }}</strong>
            </div>
            <div>
              <span>Team median</span>
              <strong>{{ data.standing.team_median_score }}</strong>
            </div>
          </div>
          <div class="standing__explain">
            60% placements · 20% interviews · 15% offer acceptance · 5% hiring speed
          </div>
          <ol class="leaderboard">
            <li
              v-for="peer in visiblePeers"
              :key="peer.user_id"
              :class="{ 'is-me': peer.user_id === data.standing.me?.user_id }"
            >
              <span class="rank">
                {{ data.standing.peers.findIndex((row) => row.user_id === peer.user_id) + 1 }}
              </span>
              <span class="avatar">{{ peer.initials }}</span>
              <span class="person">
                <strong>{{ peer.name }}</strong>
                <small>{{ peer.placements }} placements · {{ peer.interviews_scheduled }} interviews</small>
              </span>
              <strong class="score">{{ peer.productivity_score }}</strong>
            </li>
          </ol>
          <p class="standing__note">
            Upload volume and attendance are deliberately excluded from ranking.
          </p>
        </article>

        <article class="panel funnel">
          <header class="section-head">
            <div>
              <span class="eyebrow">Conversion</span>
              <h2>My hiring funnel</h2>
            </div>
          </header>
          <div class="funnel__stages">
            <div
              v-for="stage in data.hiring_funnel.stages"
              :key="stage.name"
              class="funnel-stage"
              :class="{ 'is-dropoff': stage.is_highest_dropoff }"
            >
              <div class="funnel-stage__label">
                <span>{{ stage.name }}</span>
                <strong>{{ stage.count }}</strong>
              </div>
              <div class="funnel-stage__track">
                <i :style="{ width: stageWidth(stage) }" />
              </div>
              <small v-if="stage.conversion_pct != null">
                {{ stage.conversion_pct }}% from prior stage
              </small>
            </div>
          </div>
          <p class="insight">{{ data.hiring_funnel.insight }}</p>
        </article>
      </section>

      <section class="two-col two-col--actions">
        <article class="panel">
          <header class="section-head">
            <div>
              <span class="eyebrow">Next best action</span>
              <h2>Action queue</h2>
            </div>
            <span class="section-note">{{ data.action_queue.length }} priorities</span>
          </header>
          <div v-if="!data.action_queue.length" class="empty">
            You are all caught up. Keep the pipeline moving.
          </div>
          <ul v-else class="action-list">
            <li v-for="item in data.action_queue" :key="item.key">
              <span class="priority" :class="`priority--${item.priority}`">{{ item.count }}</span>
              <div>
                <strong>{{ item.title }}</strong>
                <small>{{ item.description }}</small>
              </div>
              <RouterLink :to="item.action_href">{{ item.action_label }} →</RouterLink>
            </li>
          </ul>
        </article>

        <article class="panel">
          <header class="section-head">
            <div>
              <span class="eyebrow">Risk watch</span>
              <h2>My job health</h2>
            </div>
            <span class="section-note">Only jobs needing attention</span>
          </header>
          <div v-if="!data.job_health.length" class="empty">All assigned jobs look healthy.</div>
          <ul v-else class="job-list">
            <li v-for="job in data.job_health" :key="job.job_id">
              <div>
                <strong>{{ job.job_title }}</strong>
                <small>{{ job.client_name }} · {{ job.days_open }} days open</small>
              </div>
              <span>{{ job.candidates }} in pipeline</span>
              <em :class="`health--${job.status}`">{{ job.candidates ? job.status : 'empty' }}</em>
            </li>
          </ul>
        </article>
      </section>

      <article class="panel trend">
        <header class="section-head">
          <div>
            <span class="eyebrow">Momentum</span>
            <h2>My six-month hiring trend</h2>
          </div>
          <span class="section-note">Improve against your own baseline</span>
        </header>
        <MultiSeriesLineChart :series="data.personal_trend.series" />
      </article>
    </template>
  </section>
</template>

<style scoped>
.recruiter-command { display: grid; gap: 18px; }
.state, .empty {
  padding: 36px; text-align: center; color: var(--hrms-text-muted);
  border: 1px dashed var(--hrms-border); border-radius: 14px;
}
.state button { margin-left: 10px; }
.state--error { color: #b91c1c; }
.focus, .panel, .kpi-card {
  border: 1px solid var(--hrms-border); border-radius: 16px;
  background: var(--hrms-surface, #fff); box-shadow: var(--hrms-shadow-sm);
}
.focus, .panel { padding: 18px; }
.section-head {
  display: flex; align-items: flex-start; justify-content: space-between;
  gap: 12px; margin-bottom: 14px;
}
.section-head h2 { margin: 2px 0 0; font-size: 1rem; color: var(--hrms-primary-dark); }
.eyebrow {
  font-size: .66rem; font-weight: 800; letter-spacing: .09em;
  text-transform: uppercase; color: #6366f1;
}
.section-note { font-size: .72rem; color: var(--hrms-text-muted); }
.focus__grid { display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: 10px; }
.focus-card {
  position: relative; display: grid; gap: 3px; min-height: 78px; padding: 12px;
  border: 1px solid var(--hrms-border); border-radius: 12px; color: inherit;
  text-decoration: none; background: #f8fafc;
}
.focus-card strong { font-size: 1.45rem; color: var(--hrms-primary-dark); }
.focus-card span { font-size: .72rem; color: var(--hrms-text-muted); }
.focus-card i { position: absolute; right: 10px; top: 10px; font-style: normal; }
.focus-card--urgent { background: #fff1f2; border-color: #fecdd3; }
.focus-card--attention { background: #fffbeb; border-color: #fde68a; }
.focus-card--positive { background: #f0fdf4; border-color: #bbf7d0; }
.kpi-grid { display: grid; grid-template-columns: repeat(7, minmax(0, 1fr)); gap: 10px; }
.kpi-card { display: grid; gap: 10px; min-height: 118px; padding: 14px; }
.kpi-card__top { display: flex; justify-content: space-between; gap: 8px; }
.kpi-card__top span { font-size: .73rem; color: var(--hrms-text-muted); }
.kpi-card__top i {
  display: grid; place-items: center; width: 17px; height: 17px;
  border-radius: 50%; background: #eef2ff; color: #4f46e5; font-size: .66rem;
}
.kpi-card > strong { font-size: 1.55rem; color: var(--hrms-primary-dark); }
.kpi-card small { font-size: .66rem; color: var(--hrms-text-muted); }
.positive { color: #15803d !important; } .negative { color: #b91c1c !important; }
.two-col { display: grid; grid-template-columns: 1.05fr .95fr; gap: 18px; }
.two-col--actions { grid-template-columns: 1fr 1fr; }
.standing__summary {
  display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; margin-bottom: 10px;
}
.standing__summary > div { padding: 12px; border-radius: 10px; background: #f8fafc; }
.standing__summary span { display: block; font-size: .68rem; color: var(--hrms-text-muted); }
.standing__summary strong { display: block; margin-top: 4px; font-size: 1.35rem; color: #312e81; }
.standing__summary small { font-size: .68rem; font-weight: 500; color: var(--hrms-text-muted); }
.standing__explain, .standing__note, .insight {
  padding: 9px 11px; border-radius: 9px; background: #f5f3ff;
  color: #5b21b6; font-size: .68rem;
}
.leaderboard, .action-list, .job-list { list-style: none; padding: 0; margin: 12px 0 0; }
.leaderboard li {
  display: grid; grid-template-columns: 24px 34px 1fr auto;
  gap: 9px; align-items: center; padding: 8px; border-radius: 10px;
}
.leaderboard li + li { border-top: 1px solid var(--hrms-border); }
.leaderboard li.is-me { background: #eef2ff; border-color: transparent; }
.rank { text-align: center; font-weight: 700; color: var(--hrms-text-muted); }
.avatar {
  display: grid; place-items: center; width: 32px; height: 32px;
  border-radius: 50%; background: #e0e7ff; color: #3730a3; font-size: .68rem; font-weight: 800;
}
.person, .person strong, .person small { min-width: 0; display: block; }
.person strong { font-size: .76rem; color: var(--hrms-primary-dark); }
.person small { margin-top: 2px; font-size: .64rem; color: var(--hrms-text-muted); }
.score { color: #4f46e5; }
.standing__note { margin: 12px 0 0; color: var(--hrms-text-muted); background: #f8fafc; }
.funnel__stages { display: grid; gap: 11px; }
.funnel-stage__label { display: flex; justify-content: space-between; font-size: .75rem; }
.funnel-stage__track { height: 8px; margin: 5px 0; border-radius: 999px; background: #eef2f7; overflow: hidden; }
.funnel-stage__track i { display: block; height: 100%; border-radius: inherit; background: #6366f1; }
.funnel-stage small { font-size: .63rem; color: var(--hrms-text-muted); }
.funnel-stage.is-dropoff .funnel-stage__track i { background: #f59e0b; }
.insight { margin: 14px 0 0; }
.action-list li, .job-list li {
  display: grid; align-items: center; gap: 10px; padding: 11px 0;
  border-top: 1px solid var(--hrms-border);
}
.action-list li { grid-template-columns: 32px 1fr auto; }
.action-list li:first-child, .job-list li:first-child { border-top: 0; }
.action-list strong, .action-list small, .job-list strong, .job-list small { display: block; }
.action-list strong, .job-list strong { font-size: .76rem; color: var(--hrms-primary-dark); }
.action-list small, .job-list small { margin-top: 3px; font-size: .65rem; color: var(--hrms-text-muted); }
.action-list a { color: #4f46e5; font-size: .68rem; font-weight: 700; text-decoration: none; }
.priority {
  display: grid; place-items: center; width: 30px; height: 30px;
  border-radius: 9px; font-size: .7rem; font-weight: 800;
}
.priority--high { background: #fee2e2; color: #b91c1c; }
.priority--medium { background: #fef3c7; color: #a16207; }
.priority--low { background: #dcfce7; color: #15803d; }
.job-list li { grid-template-columns: 1fr auto auto; }
.job-list > li > span { font-size: .68rem; color: var(--hrms-text-muted); }
.job-list em {
  padding: 4px 7px; border-radius: 999px; font-size: .61rem;
  font-style: normal; text-transform: capitalize;
}
.health--urgent, .health--empty { background: #fef3c7; color: #a16207; }
.health--overdue { background: #fee2e2; color: #b91c1c; }
.health--frozen { background: #e2e8f0; color: #475569; }
.trend { min-width: 0; }
@media (max-width: 1100px) {
  .focus__grid, .kpi-grid { grid-template-columns: repeat(3, minmax(0, 1fr)); }
}
@media (max-width: 760px) {
  .focus__grid, .kpi-grid, .two-col, .two-col--actions { grid-template-columns: 1fr; }
  .standing__summary { grid-template-columns: repeat(3, 1fr); }
  .action-list li { grid-template-columns: 32px 1fr; }
  .action-list a { grid-column: 2; }
  .job-list li { grid-template-columns: 1fr auto; }
  .job-list em { grid-column: 2; grid-row: 1; }
}
</style>
