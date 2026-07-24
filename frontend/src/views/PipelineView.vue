<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import {
  fetchPipelineBoard,
  fetchPipelineHistory,
  movePipelineStage,
} from '@/api/pipeline'
import HrmsAlert from '@/components/ui/HrmsAlert.vue'
import HrmsModal from '@/components/ui/HrmsModal.vue'
import PageLayout from '@/components/ui/PageLayout.vue'
import { useAuthStore } from '@/stores/auth'
import type { PipelineCard, PipelineStage, StageHistoryItem } from '@/types/pipeline'
import { allowedStageTargets } from '@/types/pipeline'
import { avatarHue, EMPTY, initials, orEmpty } from '@/utils/format'

const auth = useAuthStore()
const loading = ref(true)
const error = ref('')
const success = ref('')
const searchQuery = ref('')
const stages = ref<PipelineStage[]>([])
const cards = ref<PipelineCard[]>([])

const selected = ref<PipelineCard | null>(null)
const showMoveModal = ref(false)
const targetStage = ref('')
const moveRemarks = ref('')
const offeredCtc = ref('')
const joiningDate = ref('')
const joinedDate = ref('')
const moving = ref(false)
const history = ref<StageHistoryItem[]>([])
const historyLoading = ref(false)

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

const isOwner = computed(() => auth.role === 'owner')

const cardsByStage = computed(() => {
  const map: Record<string, PipelineCard[]> = {}
  for (const stage of stages.value) {
    map[stage.name] = []
  }
  for (const card of cards.value) {
    const key = card.current_stage ?? ''
    if (!map[key]) map[key] = []
    map[key].push(card)
  }
  return map
})

const nextStages = computed(() => {
  if (!selected.value?.current_stage) return []
  return allowedStageTargets(selected.value.current_stage)
})

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

onMounted(loadBoard)

async function openCard(card: PipelineCard) {
  selected.value = card
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
  showMoveModal.value = false
  resetMoveForm()
}

function resetMoveForm() {
  targetStage.value = ''
  moveRemarks.value = ''
  offeredCtc.value = ''
  joiningDate.value = ''
  joinedDate.value = ''
}

function openMoveModal(stage?: string) {
  resetMoveForm()
  targetStage.value = stage ?? nextStages.value[0] ?? ''
  showMoveModal.value = true
}

async function confirmMove() {
  if (!selected.value || !targetStage.value) return
  moving.value = true
  error.value = ''
  try {
    const updated = await movePipelineStage(selected.value.id, {
      stage_name: targetStage.value,
      remarks: moveRemarks.value.trim() || null,
      offered_ctc: offeredCtc.value ? Number(offeredCtc.value) : null,
      joining_date: joiningDate.value || null,
      joined_date: joinedDate.value || null,
    })
    const idx = cards.value.findIndex((c) => c.id === updated.id)
    if (idx !== -1) cards.value[idx] = updated
    else cards.value.unshift(updated)
    selected.value = updated
    success.value = `${updated.candidate_name} moved to ${updated.current_stage}`
    showMoveModal.value = false
    history.value = await fetchPipelineHistory(updated.id)
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Failed to update stage'
  } finally {
    moving.value = false
  }
}

function stageColor(name: string) {
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
</script>

<template>
  <PageLayout variant="full">
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
            style="min-width: 240px"
          />
          <button type="button" class="hrms-btn" :disabled="loading" @click="loadBoard">
            Refresh
          </button>
        </div>
      </header>

      <HrmsAlert v-if="error" type="error" dismissible @dismiss="error = ''">{{ error }}</HrmsAlert>
      <HrmsAlert v-if="success" type="success" dismissible @dismiss="success = ''">{{ success }}</HrmsAlert>

      <div v-if="loading" class="hrms-empty-inline">Loading pipeline…</div>

      <div v-else class="pipeline-board hrms-scroll">
        <section
          v-for="stage in stages"
          :key="stage.id"
          class="pipeline-column"
        >
          <header class="pipeline-column__header">
            <span
              class="pipeline-column__dot"
              :style="{ background: stageColor(stage.name) }"
            />
            <h2 class="pipeline-column__title">{{ stage.name }}</h2>
            <span class="pipeline-column__count">
              {{ (cardsByStage[stage.name] ?? []).length }}
            </span>
          </header>

          <div class="pipeline-column__body">
            <button
              v-for="card in cardsByStage[stage.name] ?? []"
              :key="card.id"
              type="button"
              class="pipeline-card"
              :class="{ 'pipeline-card--active': selected?.id === card.id }"
              @click="openCard(card)"
            >
              <div class="pipeline-card__top">
                <div
                  class="hrms-avatar hrms-avatar--sm"
                  :style="`--hue: ${avatarHue(card.candidate_id)}`"
                >
                  {{ initials(card.candidate_name.split(' ')[0] ?? '', card.candidate_name.split(' ')[1] ?? '') }}
                </div>
                <div class="pipeline-card__identity">
                  <strong>{{ card.candidate_name }}</strong>
                  <span>{{ orEmpty(card.current_designation) }}</span>
                </div>
              </div>
              <div class="pipeline-card__meta">
                <span>{{ card.job_title }}</span>
                <span>{{ card.client_name }}</span>
              </div>
              <div v-if="card.job_assignee_name" class="pipeline-card__recruiter">
                {{ card.job_assignee_name }}
              </div>
            </button>

            <p
              v-if="!(cardsByStage[stage.name] ?? []).length"
              class="pipeline-column__empty"
            >
              No candidates
            </p>
          </div>
        </section>
      </div>
    </div>

    <!-- Detail drawer -->
    <Teleport to="body">
      <Transition name="panel">
        <div
          v-if="selected"
          class="pipeline-drawer-root"
          role="dialog"
          aria-modal="true"
          :aria-label="`Candidate ${selected.candidate_name}`"
        >
          <button
            type="button"
            class="pipeline-drawer__backdrop"
            aria-label="Close candidate details"
            @click="closeCard"
          />
          <aside class="pipeline-drawer hrms-scroll">
            <header class="pipeline-drawer__header">
              <h2 class="pipeline-drawer__heading">Candidate details</h2>
              <button type="button" class="hrms-btn hrms-btn--icon" aria-label="Close" @click="closeCard">
                ×
              </button>
            </header>

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
              <div class="pipeline-drawer__identity">
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

            <div class="hrms-info-grid pipeline-drawer__info">
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
                <span class="hrms-info-value pipeline-drawer__break">{{ selected.candidate_email || EMPTY }}</span>
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
              <div v-if="selected.offer_ctc != null" class="hrms-info-item">
                <span class="hrms-info-label">Offer CTC</span>
                <span class="hrms-info-value">{{ selected.offer_ctc }}</span>
              </div>
              <div v-if="selected.joined_date" class="hrms-info-item">
                <span class="hrms-info-label">Joined</span>
                <span class="hrms-info-value">{{ formatWhen(selected.joined_date) }}</span>
              </div>
            </div>

            <div class="hrms-actions hrms-actions--inline pipeline-drawer__actions">
              <button
                v-if="nextStages.length"
                type="button"
                class="hrms-btn hrms-btn--primary hrms-btn--sm"
                @click="openMoveModal()"
              >
                Change stage
              </button>
              <button
                v-for="stage in nextStages.slice(0, 3)"
                :key="stage"
                type="button"
                class="hrms-btn hrms-btn--sm"
                @click="openMoveModal(stage)"
              >
                → {{ stage }}
              </button>
              <p v-if="!nextStages.length" class="pipeline-drawer__terminal">
                No further stage changes (terminal stage).
              </p>
            </div>

            <h3 class="pipeline-drawer__section">Stage history</h3>
            <div v-if="historyLoading" class="hrms-empty-inline">Loading history…</div>
            <ol v-else-if="history.length" class="pipeline-history">
              <li v-for="item in history" :key="item.id">
                <strong>{{ item.stage_name }}</strong>
                <span>{{ item.moved_by_name || 'System' }} · {{ formatWhen(item.created_at) }}</span>
                <p v-if="item.remarks">{{ item.remarks }}</p>
              </li>
            </ol>
            <p v-else class="hrms-empty-inline">No stage history yet.</p>
          </aside>
        </div>
      </Transition>
    </Teleport>

    <HrmsModal v-model="showMoveModal" title="Update pipeline stage" size="md">
      <div class="hrms-form-stack">
        <label class="hrms-field">
          <span>New stage</span>
          <select v-model="targetStage" class="hrms-input">
            <option disabled value="">Select stage</option>
            <option v-for="name in nextStages" :key="name" :value="name">{{ name }}</option>
          </select>
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
          :disabled="moving || !targetStage"
          @click="confirmMove"
        >
          {{ moving ? 'Updating…' : 'Update stage' }}
        </button>
      </template>
    </HrmsModal>
  </PageLayout>
</template>

<style scoped>
.pipeline-page {
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 0;
  gap: 12px;
}

.pipeline-board {
  display: flex;
  gap: 12px;
  align-items: stretch;
  overflow-x: auto;
  padding-bottom: 12px;
  flex: 1;
  min-height: 0;
}

.pipeline-column {
  flex: 0 0 280px;
  display: flex;
  flex-direction: column;
  background: var(--hrms-surface-muted, rgba(15, 23, 42, 0.03));
  border: 1px solid var(--hrms-border);
  border-radius: 12px;
  min-height: 420px;
  max-height: calc(100vh - 220px);
}

.pipeline-column__header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 14px;
  border-bottom: 1px solid var(--hrms-border);
}

.pipeline-column__dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.pipeline-column__title {
  margin: 0;
  font-size: 0.85rem;
  font-weight: 650;
  flex: 1;
}

.pipeline-column__count {
  font-size: 0.75rem;
  color: var(--hrms-text-muted);
  background: var(--hrms-surface, #fff);
  border-radius: 999px;
  padding: 2px 8px;
}

.pipeline-column__body {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 10px;
  overflow-y: auto;
  flex: 1;
}

.pipeline-column__empty {
  margin: 24px 8px;
  text-align: center;
  font-size: 0.8rem;
  color: var(--hrms-text-muted);
}

.pipeline-card {
  text-align: left;
  border: 1px solid var(--hrms-border);
  background: var(--hrms-surface, #fff);
  border-radius: 10px;
  padding: 10px 12px;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  gap: 8px;
  transition: border-color 0.15s, box-shadow 0.15s;
}

.pipeline-card:hover,
.pipeline-card--active {
  border-color: var(--hrms-primary);
  box-shadow: 0 1px 4px rgba(15, 23, 42, 0.08);
}

.pipeline-card__top {
  display: flex;
  gap: 10px;
  align-items: center;
}

.pipeline-card__identity {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.pipeline-card__identity strong {
  font-size: 0.875rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.pipeline-card__identity span {
  font-size: 0.75rem;
  color: var(--hrms-text-muted);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.pipeline-card__meta {
  display: flex;
  flex-direction: column;
  gap: 2px;
  font-size: 0.72rem;
  color: var(--hrms-text-muted);
}

.pipeline-card__recruiter {
  font-size: 0.7rem;
  color: var(--hrms-primary);
  font-weight: 500;
}

.pipeline-drawer-root {
  position: fixed;
  inset: 0;
  z-index: 50;
  display: flex;
  justify-content: flex-end;
  pointer-events: none;
}

.pipeline-drawer__backdrop {
  position: absolute;
  inset: 0;
  border: 0;
  padding: 0;
  margin: 0;
  background: rgba(15, 23, 42, 0.45);
  cursor: pointer;
  pointer-events: auto;
}

.pipeline-drawer {
  position: relative;
  width: min(420px, 100%);
  height: 100%;
  max-height: 100dvh;
  background: var(--hrms-surface, #fff);
  border-left: 1px solid var(--hrms-border);
  padding: 16px 20px 28px;
  z-index: 1;
  box-shadow: -8px 0 24px rgba(15, 23, 42, 0.12);
  pointer-events: auto;
  overflow-y: auto;
  -webkit-overflow-scrolling: touch;
}

.pipeline-drawer__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 16px;
}

.pipeline-drawer__heading {
  margin: 0;
  font-size: 0.95rem;
  font-weight: 650;
}

.pipeline-drawer__identity {
  min-width: 0;
  flex: 1;
}

.pipeline-drawer__info {
  margin: 16px 0;
}

.pipeline-drawer__actions {
  margin-bottom: 20px;
  flex-wrap: wrap;
}

.pipeline-drawer__break {
  overflow-wrap: anywhere;
  word-break: break-word;
}

.pipeline-drawer__terminal {
  margin: 0;
  font-size: 0.8rem;
  color: var(--hrms-text-muted);
}

.pipeline-drawer__section {
  margin: 0 0 10px;
  font-size: 0.9rem;
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
  transition: opacity 0.2s ease;
}

.panel-enter-active .pipeline-drawer,
.panel-leave-active .pipeline-drawer {
  transition: transform 0.25s ease;
}

.panel-enter-from,
.panel-leave-to {
  opacity: 0;
}

.panel-enter-from .pipeline-drawer,
.panel-leave-to .pipeline-drawer {
  transform: translateX(24px);
}

@media (max-width: 720px) {
  .pipeline-drawer-root {
    align-items: flex-end;
  }

  .pipeline-drawer {
    width: 100%;
    height: min(92dvh, 100%);
    max-height: 92dvh;
    border-left: none;
    border-radius: 16px 16px 0 0;
    padding: 12px 16px 28px;
    box-shadow: 0 -8px 28px rgba(15, 23, 42, 0.18);
  }

  .panel-enter-from .pipeline-drawer,
  .panel-leave-to .pipeline-drawer {
    transform: translateY(28px);
  }

  .pipeline-drawer .hrms-panel-hero {
    flex-wrap: wrap;
  }

  .pipeline-drawer .hrms-info-grid {
    grid-template-columns: 1fr;
  }

  .pipeline-column {
    flex: 0 0 min(260px, 78vw);
    min-height: 360px;
    max-height: calc(100dvh - 200px);
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
