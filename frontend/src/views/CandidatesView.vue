<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import CandidateVerifyForm from '@/components/candidates/CandidateVerifyForm.vue'
import { deleteCandidate, fetchCandidate, fetchCandidates, updateCandidate } from '@/api/candidates'
import type { Candidate, CandidateDraft } from '@/types/candidate'
import { candidateToDraft, draftToUpdatePayload } from '@/types/candidate'

// ── State ─────────────────────────────────────────────────────────────────────
const candidates = ref<Candidate[]>([])
const selected = ref<Candidate | null>(null)
const searchQuery = ref('')
const statusFilter = ref('all')
const activeTab = ref<'overview' | 'experience' | 'education'>('overview')
const loading = ref(true)
const error = ref('')
const showEditModal = ref(false)
const editDraft = ref<CandidateDraft | null>(null)
const saving = ref(false)
const deleting = ref(false)

// ── Data loading ──────────────────────────────────────────────────────────────
async function loadCandidates() {
  loading.value = true
  error.value = ''
  try {
    candidates.value = await fetchCandidates()
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Failed to load candidates'
  } finally {
    loading.value = false
  }
}

onMounted(loadCandidates)

// ── Computed ──────────────────────────────────────────────────────────────────
const filtered = computed(() => {
  return candidates.value.filter(c => {
    const q = searchQuery.value.toLowerCase()
    const matchesSearch =
      !q ||
      `${c.first_name} ${c.last_name}`.toLowerCase().includes(q) ||
      (c.current_designation ?? '').toLowerCase().includes(q) ||
      (c.current_company ?? '').toLowerCase().includes(q) ||
      c.skills.some(s => s.name.toLowerCase().includes(q))
    const matchesStatus =
      statusFilter.value === 'all' || c.candidate_status === statusFilter.value
    return matchesSearch && matchesStatus
  })
})

// ── Helpers ───────────────────────────────────────────────────────────────────
const statusMeta: Record<string, { label: string; color: string }> = {
  active:            { label: 'Active',            color: '#22c55e' },
  pending_approval:  { label: 'Pending',           color: '#f59e0b' },
  interviewing:        { label: 'Interviewing',      color: '#3b82f6' },
  offered:             { label: 'Offered',           color: '#a855f7' },
  on_hold:             { label: 'On Hold',           color: '#f59e0b' },
  rejected:            { label: 'Rejected',          color: '#ef4444' },
  hired:               { label: 'Hired',             color: '#14b8a6' },
}

const proficiencyMeta: Record<string, string> = {
  Beginner:     '#94a3b8',
  Intermediate: '#60a5fa',
  Advanced:     '#818cf8',
  Expert:       '#a78bfa',
}

const getStatus = (s: string) => statusMeta[s] ?? { label: s.replace(/_/g, ' '), color: '#94a3b8' }

const formatCtc = (v: number | null | undefined) => {
  if (v === null || v === undefined) return '—'
  if (v >= 100000) return `₹${(v / 100000).toFixed(1)}L`
  return `₹${v.toLocaleString('en-IN')}`
}

const formatDate = (d: string | null | undefined) => {
  if (!d) return 'Present'
  return new Date(d).toLocaleDateString('en-IN', { month: 'short', year: 'numeric' })
}

const initials = (c: Candidate) =>
  `${c.first_name[0]}${c.last_name[0]}`.toUpperCase()

const avatarHue = (c: Candidate) => {
  let hash = 0
  for (const ch of c.id) hash = ch.charCodeAt(0) + ((hash << 5) - hash)
  return Math.abs(hash) % 360
}

async function selectCandidate(c: Candidate) {
  activeTab.value = 'overview'
  try {
    selected.value = await fetchCandidate(c.id)
  } catch {
    selected.value = c
  }
}

const closePanel = () => {
  selected.value = null
}

function openEdit() {
  if (!selected.value) return
  editDraft.value = candidateToDraft(selected.value)
  showEditModal.value = true
}

function closeEdit() {
  showEditModal.value = false
  editDraft.value = null
}

async function saveEdit() {
  if (!selected.value || !editDraft.value) return
  saving.value = true
  error.value = ''
  try {
    const updated = await updateCandidate(
      selected.value.id,
      draftToUpdatePayload(editDraft.value, selected.value.created_by),
    )
    const idx = candidates.value.findIndex((c) => c.id === updated.id)
    if (idx !== -1) candidates.value[idx] = updated
    selected.value = updated
    closeEdit()
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Failed to update candidate'
  } finally {
    saving.value = false
  }
}

async function handleDelete() {
  if (!selected.value) return
  const name = `${selected.value.first_name} ${selected.value.last_name}`
  if (!confirm(`Delete candidate "${name}"? This cannot be undone.`)) return

  deleting.value = true
  error.value = ''
  try {
    await deleteCandidate(selected.value.id)
    candidates.value = candidates.value.filter((c) => c.id !== selected.value!.id)
    selected.value = null
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Failed to delete candidate'
  } finally {
    deleting.value = false
  }
}

const statuses = ['all', 'active', 'pending_approval', 'interviewing', 'offered', 'on_hold', 'hired', 'rejected']
</script>

<template>
  <div class="candidates-root">

    <!-- ── Left: List pane ─────────────────────────────────────────────────── -->
    <div class="list-pane" :class="{ 'panel-open': selected }">

      <!-- Header -->
      <div class="list-header">
        <div class="list-header__top">
          <div>
            <h1 class="list-title">Candidates</h1>
            <span class="list-count">{{ filtered.length }} records</span>
          </div>
          <RouterLink to="/candidates/upload" class="btn-add">
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
              <path d="M8 3v10M3 8h10" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
            </svg>
            Upload CV
          </RouterLink>
        </div>

        <!-- Search + Filter -->
        <div class="list-controls">
          <div class="search-wrap">
            <svg class="search-icon" width="16" height="16" viewBox="0 0 16 16" fill="none">
              <circle cx="7" cy="7" r="4.5" stroke="currentColor" stroke-width="1.5"/>
              <path d="M10.5 10.5L13 13" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
            </svg>
            <input
              v-model="searchQuery"
              class="search-input"
              placeholder="Search by name, role, skill…"
            />
          </div>
          <div class="status-tabs">
            <button
              v-for="s in statuses"
              :key="s"
              class="status-tab"
              :class="{ active: statusFilter === s }"
              @click="statusFilter = s"
            >
              {{ s === 'all' ? 'All' : getStatus(s).label }}
            </button>
          </div>
        </div>
      </div>

      <div v-if="error" class="list-error" role="alert">{{ error }}</div>
      <div v-if="loading" class="list-loading">Loading candidates…</div>

      <!-- Cards -->
      <div v-else class="card-list">
        <div
          v-for="c in filtered"
          :key="c.id"
          class="candidate-card"
          :class="{ selected: selected?.id === c.id }"
          @click="selectCandidate(c)"
        >
          <!-- Avatar -->
          <div
            class="avatar"
            :style="`--hue: ${avatarHue(c)}`"
          >{{ initials(c) }}</div>

          <!-- Main info -->
          <div class="card-body">
            <div class="card-name-row">
              <span class="card-name">{{ c.first_name }} {{ c.last_name }}</span>
              <span
                class="status-badge"
                :style="`--sc: ${getStatus(c.candidate_status).color}`"
              >{{ getStatus(c.candidate_status).label }}</span>
            </div>
            <div class="card-role">
              {{ c.current_designation ?? '—' }}
              <span v-if="c.current_company"> · {{ c.current_company }}</span>
            </div>
            <div class="card-meta">
              <span v-if="c.total_experience_years">
                <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
                  <circle cx="6" cy="6" r="5" stroke="currentColor" stroke-width="1.2"/>
                  <path d="M6 3.5V6l1.5 1.5" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/>
                </svg>
                {{ c.total_experience_years }}y exp
              </span>
              <span v-if="c.current_location">
                <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
                  <path d="M6 1C4.067 1 2.5 2.567 2.5 4.5C2.5 7.125 6 11 6 11C6 11 9.5 7.125 9.5 4.5C9.5 2.567 7.933 1 6 1Z" stroke="currentColor" stroke-width="1.2"/>
                  <circle cx="6" cy="4.5" r="1" fill="currentColor"/>
                </svg>
                {{ c.current_location }}
              </span>
              <span v-if="c.notice_period">
                <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
                  <rect x="1" y="2" width="10" height="9" rx="1.5" stroke="currentColor" stroke-width="1.2"/>
                  <path d="M4 1v2M8 1v2M1 5h10" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/>
                </svg>
                {{ c.notice_period }}
              </span>
            </div>
            <!-- Skills -->
            <div class="card-skills" v-if="c.skills.length">
              <span v-for="sk in c.skills.slice(0, 4)" :key="sk.name" class="skill-chip">
                {{ sk.name }}
              </span>
              <span v-if="c.skills.length > 4" class="skill-more">+{{ c.skills.length - 4 }}</span>
            </div>
          </div>

          <!-- CTC -->
          <div class="card-ctc">
            <div class="ctc-label">Current</div>
            <div class="ctc-value">{{ formatCtc(c.current_ctc) }}</div>
            <div class="ctc-label" style="margin-top: 8px">Expected</div>
            <div class="ctc-value expected">{{ formatCtc(c.expected_ctc) }}</div>
          </div>
        </div>

        <!-- Empty state -->
        <div v-if="filtered.length === 0" class="empty-state">
          <svg width="40" height="40" viewBox="0 0 40 40" fill="none">
            <circle cx="20" cy="20" r="19" stroke="currentColor" stroke-width="1.5" stroke-dasharray="4 3"/>
            <path d="M14 27c0-3.314 2.686-6 6-6s6 2.686 6 6" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
            <circle cx="20" cy="16" r="3" stroke="currentColor" stroke-width="1.5"/>
          </svg>
          <p>No candidates match your filters.</p>
        </div>
      </div>
    </div>

    <!-- ── Right: Detail panel ─────────────────────────────────────────────── -->
    <Transition name="panel">
      <div v-if="selected" class="detail-panel">

        <!-- Panel header -->
        <div class="panel-header">
          <button class="panel-close" @click="closePanel">
            <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
              <path d="M13.5 4.5L4.5 13.5M4.5 4.5L13.5 13.5" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/>
            </svg>
          </button>

          <div class="panel-hero">
            <div
              class="avatar avatar--lg"
              :style="`--hue: ${avatarHue(selected)}`"
            >{{ initials(selected) }}</div>
            <div>
              <h2 class="panel-name">{{ selected.first_name }} {{ selected.last_name }}</h2>
              <p class="panel-role">
                {{ selected.current_designation ?? 'No designation' }}
                <span v-if="selected.current_company"> · {{ selected.current_company }}</span>
              </p>
              <span
                class="status-badge status-badge--lg"
                :style="`--sc: ${getStatus(selected.candidate_status).color}`"
              >{{ getStatus(selected.candidate_status).label }}</span>
            </div>
          </div>

          <!-- Quick actions -->
          <div class="panel-actions">
            <button type="button" class="action-btn action-btn--primary" @click="openEdit">
              Edit
            </button>
            <button type="button" class="action-btn action-btn--danger" :disabled="deleting" @click="handleDelete">
              {{ deleting ? 'Deleting…' : 'Delete' }}
            </button>
            <a v-if="selected.resume_url" :href="selected.resume_url" class="action-btn" target="_blank" rel="noopener">
              <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                <path d="M7 1v8M4 6l3 3 3-3M2 11h10" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
              Resume
            </a>
            <a v-if="selected.linkedin_url" :href="selected.linkedin_url" target="_blank" class="action-btn">
              <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                <rect x="1" y="1" width="12" height="12" rx="2" stroke="currentColor" stroke-width="1.3"/>
                <path d="M4 6v4M4 4.5v.01M6.5 10V7.5c0-1 .5-1.5 1.5-1.5s1.5.5 1.5 1.5V10" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/>
              </svg>
              LinkedIn
            </a>
            <a :href="`mailto:${selected.email}`" class="action-btn">
              <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                <rect x="1" y="3" width="12" height="8" rx="1.5" stroke="currentColor" stroke-width="1.3"/>
                <path d="M1 4.5l6 4 6-4" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/>
              </svg>
              Email
            </a>
          </div>
        </div>

        <!-- Tabs -->
        <div class="panel-tabs">
          <button
            class="panel-tab"
            :class="{ active: activeTab === 'overview' }"
            @click="activeTab = 'overview'"
          >Overview</button>
          <button
            class="panel-tab"
            :class="{ active: activeTab === 'experience' }"
            @click="activeTab = 'experience'"
          >Experience</button>
          <button
            class="panel-tab"
            :class="{ active: activeTab === 'education' }"
            @click="activeTab = 'education'"
          >Education</button>
        </div>

        <div class="panel-body">

          <!-- ── Overview tab ───────────────────────────────────────────────── -->
          <template v-if="activeTab === 'overview'">

            <!-- Contact & Personal -->
            <section class="info-section">
              <h3 class="section-title">Contact & Personal</h3>
              <div class="info-grid">
                <div class="info-item">
                  <span class="info-label">Email</span>
                  <a :href="`mailto:${selected.email}`" class="info-value info-link">{{ selected.email }}</a>
                </div>
                <div class="info-item">
                  <span class="info-label">Phone</span>
                  <span class="info-value">{{ selected.phone ?? '—' }}</span>
                </div>
                <div class="info-item">
                  <span class="info-label">Nationality</span>
                  <span class="info-value">{{ selected.nationality ?? '—' }}</span>
                </div>
                <div class="info-item">
                  <span class="info-label">Date of Birth</span>
                  <span class="info-value">{{ selected.date_of_birth ? new Date(selected.date_of_birth).toLocaleDateString('en-IN') : '—' }}</span>
                </div>
                <div class="info-item">
                  <span class="info-label">Languages</span>
                  <span class="info-value">{{ selected.languages_known ?? '—' }}</span>
                </div>
                <div class="info-item">
                  <span class="info-label">Visa Status</span>
                  <span class="info-value">{{ selected.visa_status ?? '—' }}</span>
                </div>
                <div class="info-item">
                  <span class="info-label">Current Location</span>
                  <span class="info-value">{{ selected.current_location ?? '—' }}</span>
                </div>
                <div class="info-item">
                  <span class="info-label">Preferred Location</span>
                  <span class="info-value">{{ selected.preferred_location ?? '—' }}</span>
                </div>
              </div>
            </section>

            <!-- Compensation & Availability -->
            <section class="info-section">
              <h3 class="section-title">Compensation & Availability</h3>
              <div class="ctc-cards">
                <div class="ctc-card">
                  <div class="ctc-card__label">Current CTC</div>
                  <div class="ctc-card__value">{{ formatCtc(selected.current_ctc) }}</div>
                </div>
                <div class="ctc-card ctc-card--accent">
                  <div class="ctc-card__label">Expected CTC</div>
                  <div class="ctc-card__value">{{ formatCtc(selected.expected_ctc) }}</div>
                </div>
                <div class="ctc-card">
                  <div class="ctc-card__label">Notice Period</div>
                  <div class="ctc-card__value">{{ selected.notice_period ?? '—' }}</div>
                </div>
              </div>
            </section>

            <!-- Skills -->
            <section class="info-section">
              <h3 class="section-title">Skills · {{ selected.skills.length }}</h3>
              <div class="skills-table" v-if="selected.skills.length">
                <div class="skills-table__row skills-table__row--header">
                  <span>Skill</span>
                  <span>Proficiency</span>
                  <span>Experience</span>
                </div>
                <div
                  v-for="sk in selected.skills"
                  :key="sk.name"
                  class="skills-table__row"
                >
                  <span class="skill-name">{{ sk.name }}</span>
                  <span
                    class="proficiency-chip"
                    :style="`--pc: ${proficiencyMeta[sk.proficiency_level ?? ''] ?? '#94a3b8'}`"
                  >{{ sk.proficiency_level ?? '—' }}</span>
                  <span class="skill-yrs">{{ sk.years_experience ? `${sk.years_experience}y` : '—' }}</span>
                </div>
              </div>
              <p v-else class="empty-inline">No skills recorded.</p>
            </section>

            <!-- Source & Meta -->
            <section class="info-section">
              <h3 class="section-title">Source & Meta</h3>
              <div class="info-grid">
                <div class="info-item">
                  <span class="info-label">Source</span>
                  <span class="info-value">{{ selected.source ?? '—' }}</span>
                </div>
                <div class="info-item">
                  <span class="info-label">Added by</span>
                  <span class="info-value">{{ selected.created_by ?? '—' }}</span>
                </div>
              </div>
            </section>
          </template>

          <!-- ── Experience tab ─────────────────────────────────────────────── -->
          <template v-else-if="activeTab === 'experience'">
            <section class="info-section">
              <h3 class="section-title">
                Work Experience
                <span class="section-badge">{{ selected.total_experience_years ? `${selected.total_experience_years}y total` : '' }}</span>
              </h3>
              <div class="timeline" v-if="selected.work_experiences.length">
                <div
                  v-for="(exp, i) in selected.work_experiences"
                  :key="i"
                  class="timeline-item"
                >
                  <div class="timeline-dot" :class="{ current: exp.currently_working }"></div>
                  <div class="timeline-content">
                    <div class="timeline-header">
                      <span class="timeline-company">{{ exp.company_name }}</span>
                      <span class="timeline-dates">
                        {{ formatDate(exp.start_date) }} – {{ exp.currently_working ? 'Present' : formatDate(exp.end_date) }}
                      </span>
                    </div>
                    <div class="timeline-role">{{ exp.designation ?? '—' }}</div>
                    <p v-if="exp.job_description" class="timeline-desc">{{ exp.job_description }}</p>
                  </div>
                </div>
              </div>
              <p v-else class="empty-inline">No work experience recorded.</p>
            </section>
          </template>

          <!-- ── Education tab ──────────────────────────────────────────────── -->
          <template v-else-if="activeTab === 'education'">
            <section class="info-section">
              <h3 class="section-title">Education</h3>
              <div class="edu-list" v-if="selected.education_records.length">
                <div
                  v-for="(ed, i) in selected.education_records"
                  :key="i"
                  class="edu-card"
                >
                  <div class="edu-card__degree">{{ ed.degree }}<span v-if="ed.specialization"> · {{ ed.specialization }}</span></div>
                  <div class="edu-card__inst">{{ ed.institution ?? '—' }}</div>
                  <div class="edu-card__meta">
                    <span v-if="ed.start_year || ed.end_year">{{ ed.start_year ?? '?' }} – {{ ed.end_year ?? 'Present' }}</span>
                    <span v-if="ed.percentage" class="edu-pct">{{ ed.percentage }}%</span>
                  </div>
                </div>
              </div>
              <p v-else class="empty-inline">No education records found.</p>
            </section>
          </template>

        </div>
      </div>
    </Transition>

    <!-- Edit modal -->
    <div v-if="showEditModal && editDraft" class="modal-overlay" @click.self="closeEdit">
      <div class="modal">
        <header class="modal__header">
          <h2>Edit Candidate</h2>
          <button type="button" class="modal__close" @click="closeEdit">×</button>
        </header>
        <div class="modal__body">
          <CandidateVerifyForm v-model="editDraft" />
        </div>
        <footer class="modal__footer">
          <button type="button" class="action-btn" @click="closeEdit">Cancel</button>
          <button type="button" class="action-btn action-btn--primary" :disabled="saving" @click="saveEdit">
            {{ saving ? 'Saving…' : 'Save Changes' }}
          </button>
        </footer>
      </div>
    </div>

  </div>
</template>

<style scoped>
/* ── Root layout ─────────────────────────────────────────────────────────────*/
.candidates-root {
  display: flex;
  height: 100%;
  min-height: 0;
  gap: 0;
  background: var(--hrms-bg, #f1f5f9);
  font-family: 'Inter', system-ui, sans-serif;
}

/* ── List pane ───────────────────────────────────────────────────────────────*/
.list-pane {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
  transition: flex 0.3s ease;
  overflow: hidden;
}
.list-pane.panel-open {
  flex: 0 0 55%;
}

.list-header {
  padding: 24px 24px 0;
  background: var(--hrms-bg, #f1f5f9);
  flex-shrink: 0;
}

.list-header__top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 16px;
}

.list-title {
  font-size: 1.375rem;
  font-weight: 700;
  color: var(--hrms-text-primary, #0f172a);
  letter-spacing: -0.02em;
  margin: 0 0 2px;
}

.list-count {
  font-size: 0.75rem;
  color: var(--hrms-text-muted, #94a3b8);
  font-weight: 500;
}

.btn-add {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 9px 16px;
  font-size: 0.8125rem;
  font-weight: 600;
  color: #fff;
  text-decoration: none;
  background: var(--hrms-primary, #6366f1);
  border: none;
  border-radius: 8px;
  cursor: pointer;
  flex-shrink: 0;
  transition: background 0.15s;
}
.btn-add:hover { background: var(--hrms-primary-dark, #4f46e5); }

.list-error {
  margin: 0 24px 12px;
  padding: 12px 16px;
  font-size: 0.85rem;
  color: #9b3d5c;
  background: #fce8ef;
  border-radius: 8px;
}

.list-loading {
  padding: 40px 24px;
  text-align: center;
  font-size: 0.9rem;
  color: var(--hrms-text-muted, #94a3b8);
}

/* Search */
.list-controls { display: flex; flex-direction: column; gap: 12px; margin-bottom: 16px; }

.search-wrap {
  position: relative;
}
.search-icon {
  position: absolute;
  left: 12px;
  top: 50%;
  transform: translateY(-50%);
  color: var(--hrms-text-muted, #94a3b8);
}
.search-input {
  width: 100%;
  padding: 9px 12px 9px 36px;
  font-size: 0.8125rem;
  background: var(--hrms-surface, #fff);
  border: 1px solid var(--hrms-border, #e2e8f0);
  border-radius: 8px;
  color: var(--hrms-text-primary, #0f172a);
  box-sizing: border-box;
  outline: none;
  transition: border-color 0.15s;
}
.search-input:focus { border-color: var(--hrms-primary, #6366f1); }
.search-input::placeholder { color: var(--hrms-text-muted, #94a3b8); }

/* Status tab strip */
.status-tabs {
  display: flex;
  gap: 4px;
  flex-wrap: wrap;
}
.status-tab {
  padding: 5px 12px;
  font-size: 0.75rem;
  font-weight: 500;
  border: 1px solid var(--hrms-border, #e2e8f0);
  border-radius: 20px;
  background: transparent;
  color: var(--hrms-text-secondary, #64748b);
  cursor: pointer;
  transition: all 0.15s;
}
.status-tab:hover {
  background: var(--hrms-surface, #fff);
}
.status-tab.active {
  background: var(--hrms-primary, #6366f1);
  color: #fff;
  border-color: var(--hrms-primary, #6366f1);
}

/* ── Card list ───────────────────────────────────────────────────────────────*/
.card-list {
  flex: 1;
  overflow-y: auto;
  padding: 0 24px 24px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.candidate-card {
  display: flex;
  align-items: flex-start;
  gap: 14px;
  padding: 16px;
  background: var(--hrms-surface, #fff);
  border: 1px solid var(--hrms-border, #e2e8f0);
  border-radius: 12px;
  cursor: pointer;
  transition: border-color 0.15s, box-shadow 0.15s;
}
.candidate-card:hover {
  border-color: var(--hrms-primary, #6366f1);
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--hrms-primary, #6366f1) 10%, transparent);
}
.candidate-card.selected {
  border-color: var(--hrms-primary, #6366f1);
  background: color-mix(in srgb, var(--hrms-primary, #6366f1) 4%, white);
}

/* Avatar */
.avatar {
  width: 44px;
  height: 44px;
  border-radius: 10px;
  background: hsl(var(--hue, 250) 60% 88%);
  color: hsl(var(--hue, 250) 50% 35%);
  font-size: 0.875rem;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  letter-spacing: 0.02em;
}
.avatar--lg {
  width: 56px;
  height: 56px;
  font-size: 1.1rem;
  border-radius: 14px;
}

/* Card body */
.card-body { flex: 1; min-width: 0; }

.card-name-row {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  margin-bottom: 3px;
}
.card-name {
  font-size: 0.9rem;
  font-weight: 650;
  color: var(--hrms-text-primary, #0f172a);
}

.card-role {
  font-size: 0.78rem;
  color: var(--hrms-text-secondary, #64748b);
  margin-bottom: 6px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.card-meta {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
  margin-bottom: 8px;
}
.card-meta span {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 0.72rem;
  color: var(--hrms-text-muted, #94a3b8);
}

.card-skills {
  display: flex;
  gap: 5px;
  flex-wrap: wrap;
}
.skill-chip {
  padding: 2px 8px;
  font-size: 0.68rem;
  font-weight: 500;
  background: var(--hrms-surface-elevated, #f8fafc);
  border: 1px solid var(--hrms-border, #e2e8f0);
  border-radius: 4px;
  color: var(--hrms-text-secondary, #475569);
}
.skill-more {
  padding: 2px 8px;
  font-size: 0.68rem;
  font-weight: 600;
  color: var(--hrms-primary, #6366f1);
  background: color-mix(in srgb, var(--hrms-primary, #6366f1) 8%, white);
  border-radius: 4px;
}

/* CTC */
.card-ctc {
  flex-shrink: 0;
  text-align: right;
}
.ctc-label {
  font-size: 0.65rem;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--hrms-text-muted, #94a3b8);
  font-weight: 600;
}
.ctc-value {
  font-size: 0.82rem;
  font-weight: 700;
  color: var(--hrms-text-primary, #0f172a);
}
.ctc-value.expected {
  color: var(--hrms-primary, #6366f1);
}

/* Status badge */
.status-badge {
  display: inline-flex;
  align-items: center;
  padding: 2px 8px;
  font-size: 0.66rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  border-radius: 20px;
  color: var(--sc, #22c55e);
  background: color-mix(in srgb, var(--sc, #22c55e) 12%, transparent);
  border: 1px solid color-mix(in srgb, var(--sc, #22c55e) 25%, transparent);
}
.status-badge--lg {
  font-size: 0.72rem;
  padding: 3px 10px;
}

/* Empty state */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 60px 0;
  color: var(--hrms-text-muted, #94a3b8);
  font-size: 0.85rem;
}

/* ── Detail panel ────────────────────────────────────────────────────────────*/
.detail-panel {
  width: 45%;
  min-width: 380px;
  max-width: 520px;
  background: var(--hrms-surface, #fff);
  border-left: 1px solid var(--hrms-border, #e2e8f0);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.panel-enter-active,
.panel-leave-active { transition: transform 0.28s cubic-bezier(0.4, 0, 0.2, 1), opacity 0.2s; }
.panel-enter-from,
.panel-leave-to { transform: translateX(32px); opacity: 0; }

.panel-header {
  padding: 20px 20px 0;
  background: var(--hrms-surface, #fff);
  border-bottom: 1px solid var(--hrms-border, #e2e8f0);
  flex-shrink: 0;
}

.panel-close {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border: none;
  background: var(--hrms-surface-elevated, #f8fafc);
  border-radius: 6px;
  cursor: pointer;
  color: var(--hrms-text-muted, #94a3b8);
  margin-bottom: 16px;
  transition: background 0.15s;
}
.panel-close:hover { background: var(--hrms-border, #e2e8f0); }

.panel-hero {
  display: flex;
  align-items: flex-start;
  gap: 14px;
  margin-bottom: 16px;
}

.panel-name {
  font-size: 1.1rem;
  font-weight: 700;
  color: var(--hrms-text-primary, #0f172a);
  letter-spacing: -0.02em;
  margin: 0 0 4px;
}
.panel-role {
  font-size: 0.8rem;
  color: var(--hrms-text-secondary, #64748b);
  margin: 0 0 8px;
}

.panel-actions {
  display: flex;
  gap: 8px;
  padding-bottom: 16px;
}

.action-btn {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 6px 12px;
  font-size: 0.75rem;
  font-weight: 600;
  border-radius: 6px;
  border: 1px solid var(--hrms-border, #e2e8f0);
  color: var(--hrms-text-secondary, #475569);
  background: var(--hrms-surface-elevated, #f8fafc);
  text-decoration: none;
  cursor: pointer;
  transition: background 0.15s;
}
.action-btn:hover { background: var(--hrms-border, #e2e8f0); }
.action-btn--primary {
  background: var(--hrms-primary, #6366f1);
  color: #fff;
  border-color: var(--hrms-primary, #6366f1);
}
.action-btn--primary:hover { background: var(--hrms-primary-dark, #4f46e5); }
.action-btn--danger {
  color: #9b3d5c;
  border-color: #e8b4c4;
  background: #fce8ef;
}
.action-btn--danger:hover { background: #f9d5e3; }

/* Modal */
.modal-overlay {
  position: fixed;
  inset: 0;
  z-index: 500;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  background: rgba(45, 36, 48, 0.45);
  backdrop-filter: blur(2px);
}

.modal {
  width: 100%;
  max-width: 900px;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  background: var(--hrms-surface, #fff);
  border-radius: 14px;
  box-shadow: 0 24px 48px rgba(0, 0, 0, 0.15);
  overflow: hidden;
}

.modal__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 24px;
  border-bottom: 1px solid var(--hrms-border, #e2e8f0);
}

.modal__header h2 {
  margin: 0;
  font-family: var(--hrms-font-display);
  font-size: 1.25rem;
  color: var(--hrms-primary-dark);
}

.modal__close {
  border: none;
  background: none;
  font-size: 1.5rem;
  line-height: 1;
  color: var(--hrms-text-muted);
  cursor: pointer;
}

.modal__body {
  flex: 1;
  overflow-y: auto;
  padding: 20px 24px;
}

.modal__footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  padding: 16px 24px;
  border-top: 1px solid var(--hrms-border, #e2e8f0);
}

/* Tabs */
.panel-tabs {
  display: flex;
  padding: 0 20px;
  background: var(--hrms-surface, #fff);
  border-bottom: 1px solid var(--hrms-border, #e2e8f0);
  flex-shrink: 0;
}
.panel-tab {
  padding: 12px 16px;
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--hrms-text-secondary, #64748b);
  border: none;
  background: none;
  cursor: pointer;
  border-bottom: 2px solid transparent;
  margin-bottom: -1px;
  transition: color 0.15s, border-color 0.15s;
}
.panel-tab.active {
  color: var(--hrms-primary, #6366f1);
  border-bottom-color: var(--hrms-primary, #6366f1);
}

/* Panel body */
.panel-body {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
}

/* Info sections */
.info-section { margin-bottom: 28px; }

.section-title {
  font-size: 0.72rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--hrms-text-muted, #94a3b8);
  margin: 0 0 12px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.section-badge {
  font-size: 0.68rem;
  font-weight: 600;
  background: color-mix(in srgb, var(--hrms-primary, #6366f1) 10%, transparent);
  color: var(--hrms-primary, #6366f1);
  padding: 1px 7px;
  border-radius: 10px;
  text-transform: none;
  letter-spacing: 0;
}

.info-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}
.info-item { display: flex; flex-direction: column; gap: 3px; }
.info-label {
  font-size: 0.68rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  font-weight: 600;
  color: var(--hrms-text-muted, #94a3b8);
}
.info-value {
  font-size: 0.82rem;
  font-weight: 500;
  color: var(--hrms-text-primary, #0f172a);
}
.info-link { color: var(--hrms-primary, #6366f1); text-decoration: none; }
.info-link:hover { text-decoration: underline; }

/* CTC cards */
.ctc-cards { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 10px; }

.ctc-card {
  background: var(--hrms-surface-elevated, #f8fafc);
  border: 1px solid var(--hrms-border, #e2e8f0);
  border-radius: 10px;
  padding: 14px;
}
.ctc-card--accent {
  background: color-mix(in srgb, var(--hrms-primary, #6366f1) 6%, white);
  border-color: color-mix(in srgb, var(--hrms-primary, #6366f1) 20%, transparent);
}
.ctc-card--accent .ctc-card__value { color: var(--hrms-primary, #6366f1); }
.ctc-card__label {
  font-size: 0.66rem;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  font-weight: 600;
  color: var(--hrms-text-muted, #94a3b8);
  margin-bottom: 6px;
}
.ctc-card__value {
  font-size: 1rem;
  font-weight: 700;
  color: var(--hrms-text-primary, #0f172a);
}

/* Skills table */
.skills-table { border: 1px solid var(--hrms-border, #e2e8f0); border-radius: 10px; overflow: hidden; }

.skills-table__row {
  display: grid;
  grid-template-columns: 1fr 120px 60px;
  padding: 10px 14px;
  align-items: center;
  border-bottom: 1px solid var(--hrms-border, #e2e8f0);
  font-size: 0.8rem;
}
.skills-table__row:last-child { border-bottom: none; }
.skills-table__row--header {
  font-size: 0.67rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--hrms-text-muted, #94a3b8);
  background: var(--hrms-surface-elevated, #f8fafc);
}

.skill-name { font-weight: 550; color: var(--hrms-text-primary, #0f172a); }
.skill-yrs { color: var(--hrms-text-secondary, #64748b); font-size: 0.77rem; }

.proficiency-chip {
  display: inline-flex;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 0.68rem;
  font-weight: 600;
  background: color-mix(in srgb, var(--pc, #94a3b8) 12%, transparent);
  color: color-mix(in srgb, var(--pc, #94a3b8) 80%, #000);
  border: 1px solid color-mix(in srgb, var(--pc, #94a3b8) 25%, transparent);
}

/* Timeline */
.timeline { display: flex; flex-direction: column; gap: 0; }
.timeline-item {
  display: flex;
  gap: 14px;
  position: relative;
}
.timeline-item:not(:last-child)::before {
  content: '';
  position: absolute;
  left: 7px;
  top: 18px;
  bottom: -12px;
  width: 1px;
  background: var(--hrms-border, #e2e8f0);
}

.timeline-dot {
  width: 14px;
  height: 14px;
  border-radius: 50%;
  border: 2px solid var(--hrms-border, #e2e8f0);
  background: var(--hrms-surface, #fff);
  flex-shrink: 0;
  margin-top: 3px;
}
.timeline-dot.current {
  border-color: var(--hrms-primary, #6366f1);
  background: var(--hrms-primary, #6366f1);
}

.timeline-content {
  flex: 1;
  padding-bottom: 20px;
}
.timeline-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 8px;
  flex-wrap: wrap;
  margin-bottom: 3px;
}
.timeline-company {
  font-size: 0.875rem;
  font-weight: 650;
  color: var(--hrms-text-primary, #0f172a);
}
.timeline-dates {
  font-size: 0.72rem;
  color: var(--hrms-text-muted, #94a3b8);
  white-space: nowrap;
}
.timeline-role {
  font-size: 0.78rem;
  color: var(--hrms-text-secondary, #64748b);
  margin-bottom: 6px;
}
.timeline-desc {
  font-size: 0.78rem;
  color: var(--hrms-text-secondary, #64748b);
  line-height: 1.55;
  margin: 0;
}

/* Education */
.edu-list { display: flex; flex-direction: column; gap: 10px; }
.edu-card {
  background: var(--hrms-surface-elevated, #f8fafc);
  border: 1px solid var(--hrms-border, #e2e8f0);
  border-radius: 10px;
  padding: 14px 16px;
}
.edu-card__degree {
  font-size: 0.875rem;
  font-weight: 650;
  color: var(--hrms-text-primary, #0f172a);
  margin-bottom: 4px;
}
.edu-card__inst {
  font-size: 0.8rem;
  color: var(--hrms-text-secondary, #64748b);
  margin-bottom: 8px;
}
.edu-card__meta {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 0.75rem;
  color: var(--hrms-text-muted, #94a3b8);
}
.edu-pct {
  background: color-mix(in srgb, #22c55e 12%, transparent);
  color: #16a34a;
  padding: 1px 8px;
  border-radius: 4px;
  font-weight: 600;
  font-size: 0.72rem;
}

.empty-inline {
  font-size: 0.82rem;
  color: var(--hrms-text-muted, #94a3b8);
  margin: 0;
}

/* ── Scrollbar ───────────────────────────────────────────────────────────────*/
.card-list::-webkit-scrollbar,
.panel-body::-webkit-scrollbar { width: 4px; }
.card-list::-webkit-scrollbar-track,
.panel-body::-webkit-scrollbar-track { background: transparent; }
.card-list::-webkit-scrollbar-thumb,
.panel-body::-webkit-scrollbar-thumb {
  background: var(--hrms-border, #e2e8f0);
  border-radius: 4px;
}
</style>