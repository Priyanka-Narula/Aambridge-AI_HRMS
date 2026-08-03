<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import {
  fetchPipelineBoard,
  fetchPipelineHistory,
  movePipelineStage,
  updatePipelineInterview,
} from '@/api/pipeline'
import HrmsAlert from '@/components/ui/HrmsAlert.vue'
import HrmsModal from '@/components/ui/HrmsModal.vue'
import PageLayout from '@/components/ui/PageLayout.vue'
import { useAuthStore } from '@/stores/auth'
import type {
  InterviewAction,
  PipelineCard,
  PipelineStage,
  StageHistoryItem,
} from '@/types/pipeline'
import {
  allowedStageTargets,
  nextForwardStage,
  resumeStageFromHistory,
} from '@/types/pipeline'
import { avatarHue, EMPTY, formatInr, initials, orEmpty } from '@/utils/format'

const auth = useAuthStore()
const loading = ref(true)
const error = ref('')
const success = ref('')
const searchQuery = ref('')
const stageFilter = ref<string>('all')
const stages = ref<PipelineStage[]>([])
const cards = ref<PipelineCard[]>([])

const selected = ref<PipelineCard | null>(null)
const panelCollapsed = ref(false)
const showMoveModal = ref(false)
const showInterviewPicker = ref(false)
const showStagePicker = ref(false)
const showMoreMenu = ref(false)
const pickedInterviewAction = ref<InterviewAction | null>(null)
const pickedStage = ref('')
const targetStage = ref('')
const interviewAction = ref<InterviewAction | null>(null)
const moveRemarks = ref('')
const offeredCtc = ref('')
const joiningDate = ref('')
const joinedDate = ref('')
const interviewScheduledAt = ref('')
const interviewerName = ref('')
const interviewMode = ref('online')
const moving = ref(false)
const history = ref<StageHistoryItem[]>([])
const historyLoading = ref(false)
const now = ref(Date.now())

const STAGE_COLORS: Record<string, string> = {
  Applied: '#64748b',
  Shortlisted: '#6366f1',
  Interview: '#8b5cf6',
  Offer: '#f59e0b',
  Joined: '#22c55e',
  'On Hold': '#94a3b8',
  Rejected: '#ef4444',
}

const isOwner = computed(() => auth.role === 'owner')

const stageOrder = computed(() => {
  const map = new Map<string, number>()
  for (const stage of stages.value) map.set(stage.name, stage.order_no)
  return map
})

const stageCounts = computed(() => {
  const counts: Record<string, number> = { all: cards.value.length }
  for (const stage of stages.value) counts[stage.name] = 0
  for (const card of cards.value) {
    const key = card.current_stage ?? ''
    counts[key] = (counts[key] ?? 0) + 1
  }
  return counts
})

const filteredRows = computed(() => {
  let rows = [...cards.value]
  if (stageFilter.value !== 'all') {
    rows = rows.filter((c) => c.current_stage === stageFilter.value)
  }
  rows.sort((a, b) => {
    const ao = stageOrder.value.get(a.current_stage ?? '') ?? 999
    const bo = stageOrder.value.get(b.current_stage ?? '') ?? 999
    if (ao !== bo) return ao - bo
    return a.candidate_name.localeCompare(b.candidate_name)
  })
  return rows
})

const nextStages = computed(() => {
  if (!selected.value?.current_stage) return []
  return allowedStageTargets(selected.value.current_stage, resumeStage.value)
})

const resumeStage = computed(() => resumeStageFromHistory(history.value))
const isInterviewStage = computed(() => selected.value?.current_stage === 'Interview')
const isScheduledInterview = computed(
  () => selected.value?.interview_status === 'scheduled',
)
const interviewIsFuture = computed(() => {
  const scheduledAt = selected.value?.interview_scheduled_at
  return Boolean(scheduledAt && new Date(scheduledAt).getTime() > now.value)
})
const canAdvanceInterview = computed(() => {
  if (!isInterviewStage.value) return true
  const interviewStatus = selected.value?.interview_status
  if (!interviewStatus || interviewStatus === 'cancelled') return true
  return interviewStatus === 'scheduled' && !interviewIsFuture.value
})
const canCancelInterview = computed(
  () => isScheduledInterview.value && interviewIsFuture.value,
)
const canChangeInterviewDate = computed(
  () => isScheduledInterview.value && interviewIsFuture.value,
)
const canMarkNoShow = computed(
  () => isScheduledInterview.value && !interviewIsFuture.value,
)
const canRescheduleInterview = computed(() =>
  ['cancelled', 'no_show'].includes(selected.value?.interview_status ?? ''),
)
const hasInterviewManagement = computed(
  () =>
    canCancelInterview.value ||
    canChangeInterviewDate.value ||
    canMarkNoShow.value ||
    canRescheduleInterview.value,
)
const requiresInterviewSchedule = computed(
  () =>
    targetStage.value === 'Interview' ||
    interviewAction.value === 'change_date' ||
    interviewAction.value === 'reschedule',
)

const primaryStage = computed(() => {
  const currentStage = selected.value?.current_stage
  if (!currentStage) return null
  if (currentStage === 'On Hold') return resumeStage.value
  if (currentStage === 'Interview') return 'Interview'
  return nextForwardStage(currentStage)
})

function actionLabel(stage: string) {
  if (stage === 'Interview' && selected.value?.current_stage === 'Interview') {
    return 'Next Round'
  }
  if (stage === 'Offer' && selected.value?.current_stage === 'Interview') {
    return 'Move to Offer'
  }
  if (selected.value?.current_stage === 'On Hold') return `Resume: ${stage}`
  return `${stage}`
}

const moveModalTitle = computed(() => actionLabel(targetStage.value) || 'Update pipeline stage')
const confirmMoveLabel = computed(() => {
  if (interviewAction.value === 'cancel') return 'Cancel interview'
  if (interviewAction.value === 'change_date') return 'Change interview date'
  if (interviewAction.value === 'no_show') return 'Mark no show'
  if (interviewAction.value === 'reschedule') return 'Reschedule interview'
  if (targetStage.value === 'Interview' && selected.value?.current_stage === 'Interview') {
    return 'Schedule next round'
  }
  return actionLabel(targetStage.value) || 'Update stage'
})

const modalTitle = computed(() => {
  if (interviewAction.value === 'cancel') return 'Cancel interview'
  if (interviewAction.value === 'change_date') return 'Change interview date'
  if (interviewAction.value === 'no_show') return 'Mark interview no show'
  if (interviewAction.value === 'reschedule') return 'Reschedule interview'
  return moveModalTitle.value
})
const canConfirmMove = computed(
  () =>
    Boolean(targetStage.value || interviewAction.value) &&
    !(
      ['change_date', 'reschedule'].includes(interviewAction.value ?? '') &&
      !interviewScheduledAt.value
    ),
)

async function loadBoard() {
  loading.value = true
  error.value = ''
  try {
    const board = await fetchPipelineBoard({
      search: searchQuery.value.trim() || undefined,
    })
    stages.value = board.stages
    cards.value = board.cards
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Failed to load pipeline'
  } finally {
    loading.value = false
  }
}

let searchTimer: ReturnType<typeof setTimeout> | null = null
watch(searchQuery, () => {
  if (searchTimer) clearTimeout(searchTimer)
  searchTimer = setTimeout(() => {
    void loadBoard()
  }, 300)
})

let nowTimer: ReturnType<typeof setInterval> | null = null
onMounted(() => {
  void loadBoard()
  nowTimer = setInterval(() => {
    now.value = Date.now()
  }, 30_000)
})

onBeforeUnmount(() => {
  if (nowTimer) clearInterval(nowTimer)
})

async function openCard(card: PipelineCard) {
  selected.value = card
  panelCollapsed.value = false
  history.value = []
  historyLoading.value = true
  try {
    history.value = await fetchPipelineHistory(card.id)
  } catch {
    history.value = []
  } finally {
    historyLoading.value = false
  }
}

function closeCard() {
  selected.value = null
  panelCollapsed.value = false
  showMoveModal.value = false
  showInterviewPicker.value = false
  showStagePicker.value = false
  showMoreMenu.value = false
  resetMoveForm()
}

function togglePanelCollapse() {
  panelCollapsed.value = !panelCollapsed.value
}

function resetMoveForm() {
  targetStage.value = ''
  interviewAction.value = null
  moveRemarks.value = ''
  offeredCtc.value = ''
  joiningDate.value = ''
  joinedDate.value = ''
  interviewScheduledAt.value = ''
  interviewerName.value = ''
  interviewMode.value = 'online'
}

function openMoveModal(stage: string) {
  resetMoveForm()
  targetStage.value = stage
  showMoveModal.value = true
}

function openInterviewActionModal(action: InterviewAction) {
  resetMoveForm()
  interviewAction.value = action
  showMoveModal.value = true
}

function openInterviewPicker() {
  pickedInterviewAction.value = null
  showInterviewPicker.value = true
}

function continueInterview() {
  pickedStage.value = 'Interview'
  showStagePicker.value = true
}

function confirmInterviewActionPick() {
  if (!pickedInterviewAction.value) return
  showInterviewPicker.value = false
  openInterviewActionModal(pickedInterviewAction.value)
}

function confirmStagePick() {
  if (!pickedStage.value) return
  showStagePicker.value = false
  openMoveModal(pickedStage.value)
}

function toggleMoreMenu() {
  showMoreMenu.value = !showMoreMenu.value
}

function openMoreMove(stage: string) {
  showMoreMenu.value = false
  openMoveModal(stage)
}

async function confirmMove() {
  if (!selected.value || (!targetStage.value && !interviewAction.value)) return
  moving.value = true
  error.value = ''
  try {
    const updated = interviewAction.value
      ? await updatePipelineInterview(selected.value.id, {
          action: interviewAction.value,
          remarks: moveRemarks.value.trim() || null,
          interview_scheduled_at: interviewScheduledAt.value
            ? new Date(interviewScheduledAt.value).toISOString()
            : null,
          interviewer_name: interviewerName.value.trim() || null,
          interview_mode: interviewMode.value.trim() || null,
        })
      : await movePipelineStage(selected.value.id, {
          stage_name: targetStage.value,
          remarks: moveRemarks.value.trim() || null,
          offered_ctc: offeredCtc.value ? Number(offeredCtc.value) : null,
          joining_date: joiningDate.value || null,
          joined_date: joinedDate.value || null,
          interview_scheduled_at: interviewScheduledAt.value
            ? new Date(interviewScheduledAt.value).toISOString()
            : null,
          interviewer_name: interviewerName.value.trim() || null,
          interview_mode: interviewMode.value.trim() || null,
        })
    const idx = cards.value.findIndex((c) => c.id === updated.id)
    if (idx !== -1) cards.value[idx] = updated
    else cards.value.unshift(updated)
    selected.value = updated
    success.value = interviewAction.value
      ? `${updated.candidate_name}'s interview was updated`
      : `${updated.candidate_name} moved to ${updated.current_stage}`
    showMoveModal.value = false
    history.value = await fetchPipelineHistory(updated.id)
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Failed to update stage'
  } finally {
    moving.value = false
  }
}

function stageColor(name: string | null | undefined) {
  if (!name) return '#94a3b8'
  return STAGE_COLORS[name] ?? '#94a3b8'
}

function formatWhen(iso: string | null | undefined) {
  if (!iso) return EMPTY
  return new Date(iso).toLocaleDateString('en-IN', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  })
}

function formatDateTime(iso: string | null | undefined) {
  if (!iso) return EMPTY
  return new Date(iso).toLocaleString('en-IN', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

function formatExp(years: number | null | undefined) {
  if (years == null) return EMPTY
  return `${years}y`
}
</script>

<template>
  <PageLayout variant="full">
    <div class="hrms-split pipeline-split">
      <div
        class="hrms-split__main pipeline-main"
        :class="{
          'hrms-split__main--narrow': selected && !panelCollapsed,
          'pipeline-main--rail': selected && panelCollapsed,
        }"
      >
        <div class="pipeline-page">
          <header class="hrms-page-header hrms-page-header--compact">
            <div>
              <h1 class="hrms-page-title">Hiring Pipeline</h1>
              <p class="hrms-page-subtitle">
                Track approved candidates from Applied through Shortlisted to joining.
                {{ isOwner ? 'Owners see all jobs; recruiters see assigned jobs only.' : 'Showing candidates on your assigned jobs.' }}
              </p>
              <span class="hrms-page-count">{{ cards.length }} in pipeline</span>
            </div>
            <div class="hrms-page-header__actions">
              <input
                v-model="searchQuery"
                type="search"
                class="hrms-input"
                placeholder="Search candidate, job, client…"
                style="min-width: 220px"
              />
              <button type="button" class="hrms-btn" :disabled="loading" @click="loadBoard">
                Refresh
              </button>
            </div>
          </header>

          <HrmsAlert v-if="error" type="error" dismissible @dismiss="error = ''">{{ error }}</HrmsAlert>
          <HrmsAlert v-if="success" type="success" dismissible @dismiss="success = ''">{{ success }}</HrmsAlert>

          <div class="pipeline-filters">
            <button
              type="button"
              class="pipeline-filter"
              :class="{ 'pipeline-filter--active': stageFilter === 'all' }"
              @click="stageFilter = 'all'"
            >
              All
              <span>{{ stageCounts.all ?? 0 }}</span>
            </button>
            <button
              v-for="stage in stages"
              :key="stage.id"
              type="button"
              class="pipeline-filter"
              :class="{ 'pipeline-filter--active': stageFilter === stage.name }"
              @click="stageFilter = stage.name"
            >
              <i class="pipeline-filter__dot" :style="{ background: stageColor(stage.name) }" />
              {{ stage.name }}
              <span>{{ stageCounts[stage.name] ?? 0 }}</span>
            </button>
          </div>

          <div v-if="loading" class="hrms-empty-inline">Loading pipeline…</div>

          <div v-else-if="!filteredRows.length" class="hrms-empty-inline">
            No candidates in this view.
          </div>

          <div v-else class="pipeline-table-wrap hrms-scroll">
            <table class="pipeline-table">
              <thead>
                <tr>
                  <th>Candidate</th>
                  <th>Stage</th>
                  <th>Job / Client</th>
                  <th>Experience</th>
                  <th>Recruiter</th>
                  <th>Contact</th>
                  <th>Submitted</th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="row in filteredRows"
                  :key="row.id"
                  class="pipeline-table__row"
                  :class="{ 'pipeline-table__row--active': selected?.id === row.id }"
                  @click="openCard(row)"
                >
                  <td>
                    <div class="pipeline-table__person">
                      <div
                        class="hrms-avatar hrms-avatar--sm"
                        :style="`--hue: ${avatarHue(row.candidate_id)}`"
                      >
                        {{
                          initials(
                            row.candidate_name.split(' ')[0] ?? '',
                            row.candidate_name.split(' ')[1] ?? '',
                          )
                        }}
                      </div>
                      <div class="pipeline-table__person-text">
                        <strong>{{ row.candidate_name }}</strong>
                        <span>
                          {{ orEmpty(row.current_designation) }}
                          <template v-if="row.current_company"> · {{ row.current_company }}</template>
                        </span>
                      </div>
                    </div>
                  </td>
                  <td>
                    <span
                      class="hrms-status-badge"
                      :style="`--sc: ${stageColor(row.current_stage)}`"
                    >
                      {{ row.current_stage ?? EMPTY }}
                    </span>
                  </td>
                  <td>
                    <div class="pipeline-table__stack">
                      <strong>{{ row.job_title }}</strong>
                      <span>{{ row.client_name }}</span>
                    </div>
                  </td>
                  <td>{{ formatExp(row.total_experience_years) }}</td>
                  <td>{{ row.job_assignee_name || EMPTY }}</td>
                  <td>
                    <div class="pipeline-table__stack">
                      <span class="pipeline-table__email">{{ row.candidate_email || EMPTY }}</span>
                      <span>{{ row.candidate_phone || EMPTY }}</span>
                    </div>
                  </td>
                  <td>{{ formatWhen(row.submitted_at) }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <Transition name="panel">
        <aside
          v-if="selected"
          class="hrms-split__aside pipeline-aside"
          :class="{ 'pipeline-aside--collapsed': panelCollapsed }"
          :aria-label="`Candidate ${selected.candidate_name}`"
        >
          <header class="pipeline-aside__header">
            <button
              type="button"
              class="hrms-btn hrms-btn--icon"
              :aria-label="panelCollapsed ? 'Expand details' : 'Collapse details'"
              :title="panelCollapsed ? 'Expand' : 'Collapse'"
              @click="togglePanelCollapse"
            >
              <svg width="18" height="18" viewBox="0 0 18 18" fill="none" aria-hidden="true">
                <path
                  v-if="panelCollapsed"
                  d="M7 4.5L11.5 9L7 13.5"
                  stroke="currentColor"
                  stroke-width="1.8"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                />
                <path
                  v-else
                  d="M11 4.5L6.5 9L11 13.5"
                  stroke="currentColor"
                  stroke-width="1.8"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                />
              </svg>
            </button>
            <h2 v-if="!panelCollapsed" class="pipeline-aside__heading">Candidate details</h2>
            <button
              type="button"
              class="hrms-btn hrms-btn--icon"
              aria-label="Close details"
              title="Close"
              @click="closeCard"
            >
              <svg width="18" height="18" viewBox="0 0 18 18" fill="none" aria-hidden="true">
                <path
                  d="M13.5 4.5L4.5 13.5M4.5 4.5L13.5 13.5"
                  stroke="currentColor"
                  stroke-width="1.8"
                  stroke-linecap="round"
                />
              </svg>
            </button>
          </header>

          <div v-if="panelCollapsed" class="pipeline-aside__rail" @click="togglePanelCollapse">
            <div
              class="hrms-avatar hrms-avatar--sm"
              :style="`--hue: ${avatarHue(selected.candidate_id)}`"
            >
              {{
                initials(
                  selected.candidate_name.split(' ')[0] ?? '',
                  selected.candidate_name.split(' ')[1] ?? '',
                )
              }}
            </div>
            <span class="pipeline-aside__rail-name">{{ selected.candidate_name }}</span>
            <span
              class="pipeline-aside__rail-stage"
              :style="{ background: stageColor(selected.current_stage) }"
            />
          </div>

          <div v-else class="pipeline-aside__body hrms-scroll">
            <div class="hrms-panel-hero">
              <div
                class="hrms-avatar hrms-avatar--lg"
                :style="`--hue: ${avatarHue(selected.candidate_id)}`"
              >
                {{
                  initials(
                    selected.candidate_name.split(' ')[0] ?? '',
                    selected.candidate_name.split(' ')[1] ?? '',
                  )
                }}
              </div>
              <div class="pipeline-aside__identity">
                <h2 class="hrms-panel-name">{{ selected.candidate_name }}</h2>
                <p class="hrms-panel-role">
                  {{ orEmpty(selected.current_designation) }}
                  <span v-if="selected.current_company"> · {{ selected.current_company }}</span>
                </p>
                <span
                  class="hrms-status-badge"
                  :style="`--sc: ${stageColor(selected.current_stage ?? '')}`"
                >
                  {{ selected.current_stage }}
                </span>
              </div>
            </div>

            <div class="hrms-info-grid pipeline-aside__info">
              <div class="hrms-info-item">
                <span class="hrms-info-label">Job</span>
                <span class="hrms-info-value">{{ selected.job_title }}</span>
              </div>
              <div class="hrms-info-item">
                <span class="hrms-info-label">Client</span>
                <span class="hrms-info-value">{{ selected.client_name }}</span>
              </div>
              <div class="hrms-info-item">
                <span class="hrms-info-label">Email</span>
                <span class="hrms-info-value pipeline-aside__break">{{ selected.candidate_email || EMPTY }}</span>
              </div>
              <div class="hrms-info-item">
                <span class="hrms-info-label">Phone</span>
                <span class="hrms-info-value">{{ selected.candidate_phone || EMPTY }}</span>
              </div>
              <div class="hrms-info-item">
                <span class="hrms-info-label">Experience</span>
                <span class="hrms-info-value">
                  {{
                    selected.total_experience_years != null
                      ? `${selected.total_experience_years} yrs`
                      : EMPTY
                  }}
                </span>
              </div>
              <div class="hrms-info-item">
                <span class="hrms-info-label">Recruiter</span>
                <span class="hrms-info-value">{{ selected.job_assignee_name || EMPTY }}</span>
              </div>
            </div>

            <h3 class="pipeline-aside__section">Timeline</h3>
            <div class="hrms-info-grid pipeline-aside__info">
              <div class="hrms-info-item">
                <span class="hrms-info-label">Applied</span>
                <span class="hrms-info-value">{{ formatWhen(selected.applied_date) }}</span>
              </div>
              <div class="hrms-info-item">
                <span class="hrms-info-label">Submitted</span>
                <span class="hrms-info-value">{{ formatWhen(selected.submitted_at) }}</span>
              </div>
            </div>

            <template
              v-if="
                selected.current_stage === 'Offer' ||
                selected.current_stage === 'Joined' ||
                selected.offer_date ||
                selected.offer_ctc != null
              "
            >
              <h3 class="pipeline-aside__section">Offer details</h3>
              <div class="hrms-info-grid pipeline-aside__info">
              <div class="hrms-info-item">
                <span class="hrms-info-label">Offer date</span>
                <span class="hrms-info-value">{{ formatWhen(selected.offer_date) }}</span>
              </div>
              <div class="hrms-info-item">
                <span class="hrms-info-label">Offer CTC</span>
                <span class="hrms-info-value">
                  {{ selected.offer_ctc != null ? formatInr(selected.offer_ctc) : EMPTY }}
                </span>
              </div>
              <div class="hrms-info-item">
                <span class="hrms-info-label">Expected joining</span>
                <span class="hrms-info-value">{{ formatWhen(selected.offer_joining_date) }}</span>
              </div>
              <div class="hrms-info-item">
                <span class="hrms-info-label">Offer status</span>
                <span class="hrms-info-value">{{ selected.offer_status || EMPTY }}</span>
              </div>
              </div>
            </template>

            <template v-if="selected.current_stage === 'Joined' || selected.joined_date">
              <h3 class="pipeline-aside__section">Joining</h3>
              <div class="hrms-info-grid pipeline-aside__info">
              <div class="hrms-info-item">
                <span class="hrms-info-label">Joined date</span>
                <span class="hrms-info-value">{{ formatWhen(selected.joined_date) }}</span>
              </div>
              </div>
            </template>

            <h3 class="pipeline-aside__section">Interview rounds</h3>
            <ol v-if="selected.interviews.length" class="pipeline-interviews">
              <li
                v-for="interview in selected.interviews"
                :key="interview.id"
                :class="{ 'pipeline-interviews__item--latest': interview.id === selected.interviews.at(-1)?.id }"
              >
                <div class="pipeline-interviews__summary">
                  <strong>Round {{ interview.interview_round }}</strong>
                  <span class="pipeline-interviews__status">{{ interview.status }}</span>
                </div>
                <span>{{ formatDateTime(interview.scheduled_datetime) }}</span>
                <span>
                  {{ interview.interviewer_name || 'Interviewer not assigned' }}
                  <template v-if="interview.mode"> · {{ interview.mode }}</template>
                </span>
                <button
                  v-if="interview.id === selected.interviews.at(-1)?.id && hasInterviewManagement"
                  type="button"
                  class="hrms-btn hrms-btn--ghost hrms-btn--sm pipeline-interviews__manage"
                  @click="openInterviewPicker"
                >
                  Manage interview
                </button>
              </li>
            </ol>
            <p v-else class="hrms-empty-inline">No interviews scheduled yet.</p>

            <h3 class="pipeline-aside__section">Stage history</h3>
            <div v-if="historyLoading" class="hrms-empty-inline">Loading history…</div>
            <ol v-else-if="history.length" class="pipeline-history">
              <li v-for="item in history" :key="item.id">
                <strong>{{ item.stage_name }}</strong>
                <span>{{ item.moved_by_name || 'System' }} · {{ formatWhen(item.created_at) }}</span>
                <p v-if="item.remarks">{{ item.remarks }}</p>
              </li>
            </ol>
            <p v-else class="hrms-empty-inline">No stage history yet.</p>
          </div>

          <footer v-if="!panelCollapsed" class="pipeline-aside__footer">
            <div
              v-if="primaryStage || isInterviewStage || nextStages.length"
              class="pipeline-aside__footer-actions"
            >
              <button
                v-if="isInterviewStage"
                type="button"
                class="hrms-btn hrms-btn--primary"
                :disabled="!canAdvanceInterview"
                :title="
                  !canAdvanceInterview
                    ? 'Interview must finish or be cancelled before advancing'
                    : undefined
                "
                @click="continueInterview"
              >
                Continue
              </button>
              <button
                v-else-if="primaryStage"
                type="button"
                class="hrms-btn hrms-btn--primary"
                @click="openMoveModal(primaryStage)"
              >
                {{ actionLabel(primaryStage) }}
              </button>
              <div class="pipeline-aside__more">
                <button
                  v-if="nextStages.includes('On Hold') || nextStages.includes('Rejected')"
                  type="button"
                  class="hrms-btn"
                  :aria-expanded="showMoreMenu"
                  @click="toggleMoreMenu"
                >
                  More
                </button>
                <div v-if="showMoreMenu" class="pipeline-aside__more-menu">
                  <button
                    v-if="nextStages.includes('On Hold')"
                    type="button"
                    @click="openMoreMove('On Hold')"
                  >
                    Put on hold
                  </button>
                  <button
                    v-if="nextStages.includes('Rejected')"
                    type="button"
                    class="pipeline-aside__more-danger"
                    @click="openMoreMove('Rejected')"
                  >
                    Reject candidate
                  </button>
                </div>
              </div>
            </div>
            <p
              v-if="isInterviewStage && !canAdvanceInterview"
              class="pipeline-aside__footer-hint"
            >
              Continue unlocks after the scheduled interview time.
            </p>
            <p v-if="!primaryStage && !isInterviewStage && !nextStages.length" class="pipeline-aside__terminal">
              No further stage changes (terminal stage).
            </p>
          </footer>
        </aside>
      </Transition>
    </div>

    <HrmsModal v-model="showMoveModal" :title="modalTitle" size="md">
      <div class="hrms-form-stack">
        <label class="hrms-field">
          <span>{{ interviewAction ? 'Interview action' : 'New stage' }}</span>
          <div class="hrms-input">
            {{ interviewAction ? confirmMoveLabel : targetStage }}
          </div>
        </label>
        <label class="hrms-field">
          <span>Remarks</span>
          <textarea
            v-model="moveRemarks"
            class="hrms-input"
            rows="3"
            placeholder="Interview feedback, client notes…"
          />
        </label>
        <template v-if="requiresInterviewSchedule">
          <label class="hrms-field">
            <span>Interview scheduled</span>
            <input v-model="interviewScheduledAt" type="datetime-local" class="hrms-input" />
          </label>
          <label class="hrms-field">
            <span>Interviewer</span>
            <input
              v-model="interviewerName"
              type="text"
              class="hrms-input"
              placeholder="Name of interviewer"
            />
          </label>
          <label class="hrms-field">
            <span>Mode</span>
            <select v-model="interviewMode" class="hrms-input">
              <option value="online">Online</option>
              <option value="offline">Offline</option>
              <option value="phone">Phone</option>
            </select>
          </label>
        </template>
        <template v-if="targetStage === 'Offer'">
          <label class="hrms-field">
            <span>Offered CTC</span>
            <input v-model="offeredCtc" type="number" class="hrms-input" min="0" step="0.01" />
          </label>
          <label class="hrms-field">
            <span>Expected joining date</span>
            <input v-model="joiningDate" type="date" class="hrms-input" />
          </label>
        </template>
        <template v-if="targetStage === 'Joined'">
          <label class="hrms-field">
            <span>Joined date</span>
            <input v-model="joinedDate" type="date" class="hrms-input" />
          </label>
        </template>
      </div>
      <template #footer>
        <button type="button" class="hrms-btn" @click="showMoveModal = false">Cancel</button>
        <button
          type="button"
          class="hrms-btn hrms-btn--primary"
          :disabled="moving || !canConfirmMove"
          @click="confirmMove"
        >
          {{ moving ? 'Updating…' : confirmMoveLabel }}
        </button>
      </template>
    </HrmsModal>

    <HrmsModal v-model="showInterviewPicker" title="Manage interview" size="md">
      <div class="pipeline-picker">
        <button
          v-if="canChangeInterviewDate"
          type="button"
          :class="{ 'pipeline-picker__option--selected': pickedInterviewAction === 'change_date' }"
          class="pipeline-picker__option"
          @click="pickedInterviewAction = 'change_date'"
        >
          <strong>Change date</strong>
          <span>Update the upcoming interview schedule.</span>
        </button>
        <button
          v-if="canCancelInterview"
          type="button"
          :class="{ 'pipeline-picker__option--selected': pickedInterviewAction === 'cancel' }"
          class="pipeline-picker__option"
          @click="pickedInterviewAction = 'cancel'"
        >
          <strong>Cancel interview</strong>
          <span>Keep the candidate in Interview and allow the next stage.</span>
        </button>
        <button
          v-if="canMarkNoShow"
          type="button"
          :class="{ 'pipeline-picker__option--selected': pickedInterviewAction === 'no_show' }"
          class="pipeline-picker__option"
          @click="pickedInterviewAction = 'no_show'"
        >
          <strong>Mark no show</strong>
          <span>Record that the candidate did not attend.</span>
        </button>
        <button
          v-if="canRescheduleInterview"
          type="button"
          :class="{ 'pipeline-picker__option--selected': pickedInterviewAction === 'reschedule' }"
          class="pipeline-picker__option"
          @click="pickedInterviewAction = 'reschedule'"
        >
          <strong>Reschedule interview</strong>
          <span>Set a new time for the latest round.</span>
        </button>
      </div>
      <template #footer>
        <button type="button" class="hrms-btn" @click="showInterviewPicker = false">Cancel</button>
        <button
          type="button"
          class="hrms-btn hrms-btn--primary"
          :disabled="!pickedInterviewAction"
          @click="confirmInterviewActionPick"
        >
          Continue
        </button>
      </template>
    </HrmsModal>

    <HrmsModal v-model="showStagePicker" title="Continue candidate" size="md">
      <div class="pipeline-picker">
        <button
          type="button"
          :class="{ 'pipeline-picker__option--selected': pickedStage === 'Interview' }"
          class="pipeline-picker__option"
          @click="pickedStage = 'Interview'"
        >
          <strong>Next interview round</strong>
          <span>Schedule another interview round.</span>
        </button>
        <button
          type="button"
          :class="{ 'pipeline-picker__option--selected': pickedStage === 'Offer' }"
          class="pipeline-picker__option"
          @click="pickedStage = 'Offer'"
        >
          <strong>Move to offer</strong>
          <span>Prepare the candidate’s offer details.</span>
        </button>
      </div>
      <template #footer>
        <button type="button" class="hrms-btn" @click="showStagePicker = false">Cancel</button>
        <button
          type="button"
          class="hrms-btn hrms-btn--primary"
          :disabled="!pickedStage"
          @click="confirmStagePick"
        >
          Continue
        </button>
      </template>
    </HrmsModal>
  </PageLayout>
</template>

<style scoped>
.pipeline-split {
  height: 100%;
  min-height: 0;
}

.pipeline-main {
  padding: 0 4px;
}

.pipeline-main--rail {
  flex: 1;
}

.pipeline-page {
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 0;
  gap: 12px;
  padding: 16px 20px 20px;
}

.pipeline-filters {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.pipeline-filter {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  border: 1px solid var(--hrms-border);
  background: var(--hrms-surface, #fff);
  border-radius: 999px;
  padding: 5px 10px;
  font-size: 0.75rem;
  font-weight: 550;
  color: var(--hrms-text-muted);
  cursor: pointer;
}

.pipeline-filter span {
  min-width: 1.25rem;
  text-align: center;
  border-radius: 999px;
  background: var(--hrms-surface-muted, rgba(15, 23, 42, 0.05));
  padding: 0 6px;
  font-variant-numeric: tabular-nums;
}

.pipeline-filter__dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  display: inline-block;
}

.pipeline-filter--active {
  border-color: var(--hrms-primary);
  color: var(--hrms-primary-dark, var(--hrms-primary));
  background: color-mix(in srgb, var(--hrms-primary) 8%, white);
}

.pipeline-table-wrap {
  flex: 1;
  min-height: 0;
  overflow: auto;
  border: 1px solid var(--hrms-border);
  border-radius: 12px;
  background: var(--hrms-surface, #fff);
}

.pipeline-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.8rem;
  min-width: 900px;
}

.pipeline-table th {
  position: sticky;
  top: 0;
  z-index: 1;
  text-align: left;
  font-size: 0.67rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--hrms-text-muted);
  background: var(--hrms-surface-muted, #f8fafc);
  padding: 10px 12px;
  border-bottom: 1px solid var(--hrms-border);
  white-space: nowrap;
}

.pipeline-table td {
  padding: 10px 12px;
  border-bottom: 1px solid var(--hrms-border);
  vertical-align: middle;
}

.pipeline-table__row {
  cursor: pointer;
  transition: background 0.12s ease;
}

.pipeline-table__row:hover,
.pipeline-table__row--active {
  background: color-mix(in srgb, var(--hrms-primary) 5%, white);
}

.pipeline-table__person {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 160px;
}

.pipeline-table__person-text,
.pipeline-table__stack {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.pipeline-table__person-text strong,
.pipeline-table__stack strong {
  font-size: 0.84rem;
  font-weight: 650;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.pipeline-table__person-text span,
.pipeline-table__stack span {
  font-size: 0.72rem;
  color: var(--hrms-text-muted);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.pipeline-table__email {
  max-width: 140px;
}

.pipeline-table__actions {
  display: flex;
  gap: 6px;
  justify-content: flex-end;
  white-space: nowrap;
}

.pipeline-aside {
  display: flex;
  flex-direction: column;
  min-height: 0;
  transition: width 0.25s ease, min-width 0.25s ease, max-width 0.25s ease;
}

.pipeline-aside--collapsed {
  width: 56px;
  min-width: 56px;
  max-width: 56px;
}

.pipeline-aside__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 12px 12px 8px;
  flex-shrink: 0;
}

.pipeline-aside--collapsed .pipeline-aside__header {
  flex-direction: column;
  padding: 10px 6px;
}

.pipeline-aside__heading {
  margin: 0;
  flex: 1;
  font-size: 0.95rem;
  font-weight: 650;
}

.pipeline-aside__body {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding: 8px 18px 20px;
}

.pipeline-aside__identity {
  min-width: 0;
  flex: 1;
}

.pipeline-aside__info {
  margin: 16px 0;
}

.pipeline-aside__footer {
  position: relative;
  padding: 12px 18px 16px;
  border-top: 1px solid var(--hrms-border);
  background: var(--hrms-surface, #fff);
  flex-shrink: 0;
}

.pipeline-aside__footer-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.pipeline-aside__footer-hint {
  margin: 8px 0 0;
  font-size: 0.76rem;
  color: var(--hrms-text-muted);
}

.pipeline-aside__more {
  position: relative;
}

.pipeline-aside__more-menu {
  position: absolute;
  right: 0;
  bottom: calc(100% + 8px);
  z-index: 3;
  min-width: 148px;
  padding: 5px;
  border: 1px solid var(--hrms-border);
  border-radius: 10px;
  background: var(--hrms-surface, #fff);
  box-shadow: 0 8px 22px rgba(15, 23, 42, 0.14);
}

.pipeline-aside__more-menu button {
  width: 100%;
  padding: 8px 10px;
  border: 0;
  border-radius: 7px;
  background: transparent;
  color: var(--hrms-text);
  text-align: left;
  font: inherit;
  font-size: 0.8rem;
  cursor: pointer;
}

.pipeline-aside__more-menu button:hover {
  background: var(--hrms-surface-muted, #f8fafc);
}

.pipeline-aside__more-menu .pipeline-aside__more-danger {
  color: var(--hrms-danger, #dc2626);
}

.pipeline-aside__break {
  overflow-wrap: anywhere;
  word-break: break-word;
}

.pipeline-aside__terminal {
  margin: 0;
  font-size: 0.8rem;
  color: var(--hrms-text-muted);
}

.pipeline-aside__section {
  margin: 0 0 10px;
  font-size: 0.9rem;
}

.pipeline-interviews {
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin: 0 0 20px;
  padding: 0;
}

.pipeline-interviews li {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 4px 10px;
  padding: 10px 12px;
  border: 1px solid var(--hrms-border);
  border-radius: 10px;
  color: var(--hrms-text-muted);
  font-size: 0.78rem;
}

.pipeline-interviews__item--latest {
  border-color: color-mix(in srgb, var(--hrms-primary) 40%, var(--hrms-border));
  background: color-mix(in srgb, var(--hrms-primary) 5%, var(--hrms-surface, #fff));
}

.pipeline-interviews__summary {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--hrms-text);
}

.pipeline-interviews__status {
  padding: 2px 7px;
  border-radius: 999px;
  background: var(--hrms-surface-muted, #f1f5f9);
  color: var(--hrms-text-muted);
  font-size: 0.68rem;
  font-weight: 650;
  text-transform: capitalize;
}

.pipeline-interviews__manage {
  grid-column: 2;
  grid-row: 1 / span 2;
  align-self: center;
}

.pipeline-picker {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.pipeline-picker__option {
  display: flex;
  flex-direction: column;
  gap: 3px;
  width: 100%;
  padding: 12px;
  border: 1px solid var(--hrms-border);
  border-radius: 10px;
  background: var(--hrms-surface, #fff);
  color: var(--hrms-text);
  text-align: left;
  cursor: pointer;
}

.pipeline-picker__option span {
  color: var(--hrms-text-muted);
  font-size: 0.8rem;
}

.pipeline-picker__option--selected {
  border-color: var(--hrms-primary);
  background: color-mix(in srgb, var(--hrms-primary) 7%, var(--hrms-surface, #fff));
}

.pipeline-aside__rail {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 8px 6px 16px;
  cursor: pointer;
}

.pipeline-aside__rail-name {
  writing-mode: vertical-rl;
  transform: rotate(180deg);
  font-size: 0.78rem;
  font-weight: 600;
  color: var(--hrms-text);
  max-height: 220px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.pipeline-aside__rail-stage {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.pipeline-history {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.pipeline-history li {
  padding-left: 14px;
  border-left: 2px solid var(--hrms-border);
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.pipeline-history strong {
  font-size: 0.875rem;
}

.pipeline-history span {
  font-size: 0.75rem;
  color: var(--hrms-text-muted);
}

.pipeline-history p {
  margin: 4px 0 0;
  font-size: 0.8rem;
}

.hrms-form-stack {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.hrms-field {
  display: flex;
  flex-direction: column;
  gap: 6px;
  font-size: 0.85rem;
  font-weight: 500;
}

.panel-enter-active,
.panel-leave-active {
  transition: opacity 0.2s ease, transform 0.25s ease;
}

.panel-enter-from,
.panel-leave-to {
  opacity: 0;
  transform: translateX(16px);
}

@media (max-width: 900px) {
  .pipeline-aside:not(.pipeline-aside--collapsed) {
    position: absolute;
    right: 0;
    top: 0;
    bottom: 0;
    z-index: 20;
    width: min(420px, 92vw);
    max-width: none;
    box-shadow: -8px 0 24px rgba(15, 23, 42, 0.12);
  }

  .pipeline-split {
    position: relative;
  }
}

@media (max-width: 720px) {
  .pipeline-aside .hrms-panel-hero {
    flex-wrap: wrap;
  }

  .pipeline-aside .hrms-info-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 480px) {
  .hrms-page-header {
    flex-direction: column;
    align-items: stretch;
  }

  .hrms-page-header__actions {
    width: 100%;
  }

  .hrms-page-header__actions .hrms-input {
    flex: 1;
    min-width: 0 !important;
    width: 100%;
  }
}
</style>
