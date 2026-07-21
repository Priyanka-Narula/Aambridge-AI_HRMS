<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount, watch } from 'vue'
import CandidateVerifyForm from '@/components/candidates/CandidateVerifyForm.vue'
import ResumePreview from '@/components/candidates/ResumePreview.vue'
import {
  deleteCandidate,
  downloadCandidateResume,
  fetchCandidate,
  fetchCandidateResumeBlob,
  fetchCandidates,
  updateCandidate,
} from '@/api/candidates'
import type { Candidate, CandidateDraft } from '@/types/candidate'
import { candidateToDraft, draftToUpdatePayload } from '@/types/candidate'
import HrmsModal from '@/components/ui/HrmsModal.vue'
import {
  avatarHue as hueFromId,
  EMPTY,
  ELLIPSIS,
  formatInr,
  initials as nameInitials,
  orEmpty,
} from '@/utils/format'


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
const downloadingResume = ref(false)
const editResumeUrl = ref<string | null>(null)
const editResumeLoading = ref(false)
const editResumeError = ref<string | null>(null)

function revokeEditResumeUrl() {
  if (editResumeUrl.value) {
    URL.revokeObjectURL(editResumeUrl.value)
    editResumeUrl.value = null
  }
}

async function loadEditResume(candidate: Candidate) {
  revokeEditResumeUrl()
  editResumeError.value = null
  if (!candidate.resume_url) {
    editResumeLoading.value = false
    return
  }
  editResumeLoading.value = true
  try {
    const blob = await fetchCandidateResumeBlob(candidate.id)
    editResumeUrl.value = URL.createObjectURL(
      new Blob([blob], { type: 'application/pdf' }),
    )
  } catch (err) {
    editResumeError.value = err instanceof Error ? err.message : 'Failed to load resume preview'
  } finally {
    editResumeLoading.value = false
  }
}

function openEdit() {
  if (!selected.value) return
  editDraft.value = candidateToDraft(selected.value)
  showEditModal.value = true
  void loadEditResume(selected.value)
}

function closeEdit() {
  showEditModal.value = false
  editDraft.value = null
  revokeEditResumeUrl()
  editResumeError.value = null
}

watch(showEditModal, (open) => {
  if (!open) {
    editDraft.value = null
    revokeEditResumeUrl()
    editResumeError.value = null
  }
})

onBeforeUnmount(revokeEditResumeUrl)

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

const formatDate = (d: string | null | undefined) => {
  if (!d) return 'Present'
  return new Date(d).toLocaleDateString('en-IN', { month: 'short', year: 'numeric' })
}

const initials = (c: Candidate) => nameInitials(c.first_name, c.last_name)
const avatarHue = (c: Candidate) => hueFromId(c.id)

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

async function handleDownloadResume() {
  if (!selected.value?.resume_url) return
  downloadingResume.value = true
  error.value = ''
  try {
    await downloadCandidateResume(selected.value)
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Failed to download resume'
  } finally {
    downloadingResume.value = false
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
  <div class="hrms-split">

    
    <div class="hrms-split__main" :class="{ 'hrms-split__main--narrow': selected }">

      <!-- Header -->
      <div class="hrms-split__header">
        <div class="hrms-page-header hrms-page-header--compact">
          <div>
            <h1 class="hrms-page-title hrms-page-title--sm">Candidates</h1>
            <span class="hrms-page-count">{{ filtered.length }} records</span>
          </div>
          <RouterLink to="/candidates/upload" class="hrms-btn hrms-btn--primary">
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
              <path d="M8 3v10M3 8h10" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
            </svg>
            Upload CV
          </RouterLink>
        </div>

        <!-- Search + Filter -->
        <div class="hrms-controls">
          <div class="hrms-search">
            <svg class="hrms-search__icon" width="16" height="16" viewBox="0 0 16 16" fill="none">
              <circle cx="7" cy="7" r="4.5" stroke="currentColor" stroke-width="1.5"/>
              <path d="M10.5 10.5L13 13" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
            </svg>
            <input
              v-model="searchQuery"
              class="hrms-input"
              placeholder="Search by name, role, skill..."
            />
          </div>
          <div class="hrms-tabs hrms-tabs--pills">
            <button
              v-for="s in statuses"
              :key="s"
              class="hrms-tab"
              :class="{ 'hrms-tab--active': statusFilter === s }"
              @click="statusFilter = s"
            >
              {{ s === 'all' ? 'All' : getStatus(s).label }}
            </button>
          </div>
        </div>
      </div>

      <div v-if="error" class="hrms-alert hrms-alert--error" style="margin: 0 24px 12px" role="alert">{{ error }}</div>
      <div v-if="loading" class="hrms-loading">Loading candidates...</div>

      <!-- Cards -->
      <div v-else class="hrms-split__scroll hrms-scroll hrms-list-stack">
        <div
          v-for="c in filtered"
          :key="c.id"
          class="hrms-card hrms-card--interactive hrms-card--flat hrms-entity-card"
          :class="{ 'hrms-card--selected': selected?.id === c.id }"
          @click="selectCandidate(c)"
        >
          <!-- Avatar -->
          <div
            class="hrms-avatar"
            :style="`--hue: ${avatarHue(c)}`"
          >{{ initials(c) }}</div>

          <!-- Main info -->
          <div class="hrms-entity-card__body">
            <div class="hrms-entity-card__name-row">
              <span class="hrms-entity-card__name">{{ c.first_name }} {{ c.last_name }}</span>
              <span
                class="hrms-status-badge"
                :style="`--sc: ${getStatus(c.candidate_status).color}`"
              >{{ getStatus(c.candidate_status).label }}</span>
            </div>
            <div class="hrms-entity-card__role">
              {{ orEmpty(c.current_designation) }}
              <span v-if="c.current_company"> {{ c.current_company }}</span>
            </div>
            <div class="hrms-entity-card__meta">
              <span v-if="c.total_experience_years">
                <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
                  <circle cx="6" cy="6" r="5" stroke="currentColor" stroke-width="1.2"/>
                  <path d="M6 3.5V6l1.5 1.5" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/>
                </svg>
                {{ c.total_experience_years }}y exp
              </span>
              <span v-if="c.uae_experience_years">
                <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
                  <circle cx="6" cy="6" r="5" stroke="currentColor" stroke-width="1.2"/>
                  <path d="M6 3.5V6l1.5 1.5" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/>
                </svg>
                {{ c.uae_experience_years }} y UAE
              </span>
              <span v-if="c.industry">
                <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
                  <rect x="1.5" y="2.5" width="9" height="7" rx="1" stroke="currentColor" stroke-width="1.2"/>
                  <path d="M4 5h4M4 7h2" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/>
                </svg>
                {{ c.industry }}
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
            <div class="hrms-entity-card__chips" v-if="c.skills.length">
              <span v-for="sk in c.skills.slice(0, 4)" :key="sk.name" class="hrms-chip">
                {{ sk.name }}
              </span>
              <span v-if="c.skills.length > 4" class="hrms-chip hrms-chip--accent">+{{ c.skills.length - 4 }}</span>
            </div>
          </div>

          <!-- CTC -->
          <div class="hrms-entity-card__aside">
            <div class="hrms-metric-label">Current</div>
            <div class="hrms-metric-value">{{ formatInr(c.current_ctc) }}</div>
            <div class="hrms-metric-label" style="margin-top: 8px">Expected</div>
            <div class="hrms-metric-value hrms-metric-value--accent">{{ formatInr(c.expected_ctc) }}</div>
          </div>
        </div>

        <!-- Empty state -->
        <div v-if="filtered.length === 0" class="hrms-empty">
          <svg width="40" height="40" viewBox="0 0 40 40" fill="none">
            <circle cx="20" cy="20" r="19" stroke="currentColor" stroke-width="1.5" stroke-dasharray="4 3"/>
            <path d="M14 27c0-3.314 2.686-6 6-6s6 2.686 6 6" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
            <circle cx="20" cy="16" r="3" stroke="currentColor" stroke-width="1.5"/>
          </svg>
          <p>No candidates match your filters.</p>
        </div>
      </div>
    </div>

    
    <Transition name="panel">
      <div v-if="selected" class="hrms-split__aside">
        <div class="hrms-panel-header">
          <button class="hrms-btn hrms-btn--icon" style="margin-bottom: 16px" @click="closePanel">
            <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
              <path d="M13.5 4.5L4.5 13.5M4.5 4.5L13.5 13.5" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/>
            </svg>
          </button>

          <div class="hrms-panel-hero">
            <div
              class="hrms-avatar hrms-avatar--lg"
              :style="`--hue: ${avatarHue(selected)}`"
            >{{ initials(selected) }}</div>
            <div>
              <h2 class="hrms-panel-name">{{ selected.first_name }} {{ selected.last_name }}</h2>
              <p class="hrms-panel-role">
                {{ selected.current_designation ?? 'No designation' }}
                <span v-if="selected.current_company"> {{ selected.current_company }}</span>
              </p>
              <span
                class="hrms-status-badge hrms-status-badge--lg"
                :style="`--sc: ${getStatus(selected.candidate_status).color}`"
              >{{ getStatus(selected.candidate_status).label }}</span>
            </div>
          </div>

          <!-- Quick actions -->
          <div class="hrms-actions hrms-actions--inline" style="padding-bottom: 16px">
            <button type="button" class="hrms-btn hrms-btn--primary hrms-btn--sm" @click="openEdit">
              Edit
            </button>
            <button type="button" class="hrms-btn hrms-btn--danger hrms-btn--sm" :disabled="deleting" @click="handleDelete">
              {{ deleting ? 'Deleting...' : 'Delete' }}
            </button>
            <button
              v-if="selected.resume_url"
              type="button"
              class="hrms-btn hrms-btn--sm"
              :disabled="downloadingResume"
              @click="handleDownloadResume"
            >
              <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                <path d="M7 1v8M4 6l3 3 3-3M2 11h10" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
              {{ downloadingResume ? 'Downloading...' : 'Resume' }}
            </button>
            <a v-if="selected.linkedin_url" :href="selected.linkedin_url" target="_blank" class="hrms-btn hrms-btn--sm">
              <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                <rect x="1" y="1" width="12" height="12" rx="2" stroke="currentColor" stroke-width="1.3"/>
                <path d="M4 6v4M4 4.5v.01M6.5 10V7.5c0-1 .5-1.5 1.5-1.5s1.5.5 1.5 1.5V10" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/>
              </svg>
              LinkedIn
            </a>
            <a :href="`mailto:${selected.email}`" class="hrms-btn hrms-btn--sm">
              <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                <rect x="1" y="3" width="12" height="8" rx="1.5" stroke="currentColor" stroke-width="1.3"/>
                <path d="M1 4.5l6 4 6-4" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/>
              </svg>
              Email
            </a>
          </div>
        </div>

        <!-- Tabs -->
        <div class="hrms-tabs">
          <button
            class="hrms-tab"
            :class="{ 'hrms-tab--active': activeTab === 'overview' }"
            @click="activeTab = 'overview'"
          >Overview</button>
          <button
            class="hrms-tab"
            :class="{ 'hrms-tab--active': activeTab === 'experience' }"
            @click="activeTab = 'experience'"
          >Experience</button>
          <button
            class="hrms-tab"
            :class="{ 'hrms-tab--active': activeTab === 'education' }"
            @click="activeTab = 'education'"
          >Education</button>
        </div>

        <div class="hrms-panel-body hrms-scroll">

          
          <template v-if="activeTab === 'overview'">

            <!-- Contact & Personal -->
            <section class="hrms-section">
              <h3 class="hrms-section-title">Contact & Personal</h3>
              <div class="hrms-info-grid">
                <div class="hrms-info-item">
                  <span class="hrms-info-label">Email</span>
                  <a :href="`mailto:${selected.email}`" class="hrms-info-value hrms-info-link">{{ selected.email }}</a>
                </div>
                <div class="hrms-info-item">
                  <span class="hrms-info-label">Phone</span>
                  <span class="hrms-info-value">{{ orEmpty(selected.phone) }}</span>
                </div>
                <div class="hrms-info-item">
                  <span class="hrms-info-label">Nationality</span>
                  <span class="hrms-info-value">{{ selected.nationality ?? EMPTY }}</span>
                </div>
                <div class="hrms-info-item">
                  <span class="hrms-info-label">Date of Birth</span>
                  <span class="hrms-info-value">{{ selected.date_of_birth ? new Date(selected.date_of_birth).toLocaleDateString('en-IN') : EMPTY }}</span>
                </div>
                <div class="hrms-info-item">
                  <span class="hrms-info-label">Languages</span>
                  <span class="hrms-info-value">{{ selected.languages_known ?? EMPTY }}</span>
                </div>
                <div class="hrms-info-item">
                  <span class="hrms-info-label">Visa Status</span>
                  <span class="hrms-info-value">{{ selected.visa_status ?? EMPTY }}</span>
                </div>
                <div class="hrms-info-item">
                  <span class="hrms-info-label">Current Location</span>
                  <span class="hrms-info-value">{{ selected.current_location ?? EMPTY }}</span>
                </div>
                <div class="hrms-info-item">
                  <span class="hrms-info-label">Preferred Location</span>
                  <span class="hrms-info-value">{{ selected.preferred_location ?? EMPTY }}</span>
                </div>
                <div class="hrms-info-item">
                  <span class="hrms-info-label">Industry</span>
                  <span class="hrms-info-value">{{ selected.industry ?? EMPTY }}</span>
                </div>
              </div>
            </section>

            <section class="hrms-section">
              <h3 class="hrms-section-title">Compensation & Availability</h3>
              <div class="hrms-metric-grid hrms-metric-grid--cols-4">
                <div class="hrms-metric-card">
                  <div class="hrms-metric-label">Current CTC</div>
                  <div class="hrms-metric-value">{{ formatInr(selected.current_ctc) }}</div>
                </div>
                <div class="hrms-metric-card hrms-metric-card--accent">
                  <div class="hrms-metric-label">Expected CTC</div>
                  <div class="hrms-metric-value">{{ formatInr(selected.expected_ctc) }}</div>
                </div>
                <div class="hrms-metric-card">
                  <div class="hrms-metric-label">Notice Period</div>
                  <div class="hrms-metric-value">{{ selected.notice_period ?? EMPTY }}</div>
                </div>
                <div class="hrms-metric-card">
                  <div class="hrms-metric-label">UAE Experience</div>
                  <div class="hrms-metric-value">{{ selected.uae_experience_years != null ? `${selected.uae_experience_years}y` : EMPTY }}</div>
                </div>
              </div>
            </section>

            <section class="hrms-section">
              <h3 class="hrms-section-title">Skills {{ selected.skills.length }}</h3>
              <div class="hrms-data-table hrms-data-table--cols-3" v-if="selected.skills.length">
                <div class="hrms-data-table__row hrms-data-table__row--header">
                  <span>Skill</span>
                  <span>Proficiency</span>
                  <span>Experience</span>
                </div>
                <div
                  v-for="sk in selected.skills"
                  :key="sk.name"
                  class="hrms-data-table__row"
                >
                  <span style="font-weight: 550">{{ sk.name }}</span>
                  <span
                    class="hrms-proficiency-chip"
                    :style="`--pc: ${proficiencyMeta[sk.proficiency_level ?? ''] ?? '#94a3b8'}`"
                  >{{ sk.proficiency_level ?? EMPTY }}</span>
                  <span style="color: var(--hrms-text-secondary); font-size: 0.77rem"> {{ sk.years_experience ? ` ${ sk.years_experience}y` : EMPTY }}</span>
                </div>
              </div>
              <p v-else class="hrms-empty-inline">No skills recorded.</p>
            </section>

            <section class="hrms-section">
              <h3 class="hrms-section-title">Source & Meta</h3>
              <div class="hrms-info-grid">
                <div class="hrms-info-item">
                  <span class="hrms-info-label">Source</span>
                  <span class="hrms-info-value">{{ selected.source ?? EMPTY }}</span>
                </div>
                <div class="hrms-info-item">
                  <span class="hrms-info-label">Added by</span>
                  <span class="hrms-info-value">{{ selected.created_by ?? EMPTY }}</span>
                </div>
              </div>
            </section>
          </template>

          
          <template v-else-if="activeTab === 'experience'">
            <section class="hrms-section">
              <h3 class="hrms-section-title">
                Work Experience
                <span class="hrms-section-badge">{{ selected.total_experience_years ? `${selected.total_experience_years}y total` : '' }}</span>
              </h3>
              <div class="hrms-timeline" v-if="selected.work_experiences.length">
                <div
                  v-for="(exp, i) in selected.work_experiences"
                  :key="i"
                  class="hrms-timeline-item"
                >
                  <div class="hrms-timeline-dot" :class="{ 'hrms-timeline-dot--current': exp.currently_working }"></div>
                  <div class="hrms-timeline-content">
                    <div class="hrms-timeline-header">
                      <span class="hrms-timeline-title">{{ exp.company_name }}</span>
                      <span class="hrms-timeline-dates">
                        {{ formatDate(exp.start_date) }} - {{ exp.currently_working ? 'Present' : formatDate(exp.end_date) }}
                      </span>
                    </div>
                    <div class="hrms-timeline-subtitle">{{ exp.designation ?? EMPTY }}</div>
                    <p v-if="exp.job_description" class="hrms-timeline-desc">{{ exp.job_description }}</p>
                  </div>
                </div>
              </div>
              <p v-else class="hrms-empty-inline">No work experience recorded.</p>
            </section>
          </template>

          <template v-else-if="activeTab === 'education'">
            <section class="hrms-section">
              <h3 class="hrms-section-title">Education</h3>
              <div class="hrms-edu-list" v-if="selected.education_records.length">
                <div
                  v-for="(ed, i) in selected.education_records"
                  :key="i"
                  class="hrms-edu-card"
                >
                  <div class="hrms-edu-card__degree">{{ ed.degree }}<span v-if="ed.specialization"> Â· {{ ed.specialization }}</span></div>
                  <div class="hrms-edu-card__inst">{{ ed.institution ?? EMPTY }}</div>
                  <div class="hrms-edu-card__meta">
                    <span v-if="ed.start_year || ed.end_year">{{ ed.start_year ?? '?' }} - {{ ed.end_year ?? 'Present' }}</span>
                    <span v-if="ed.percentage" class="hrms-chip">{{ ed.percentage }}%</span>
                  </div>
                </div>
              </div>
              <p v-else class="hrms-empty-inline">No education records found.</p>
            </section>
          </template>

        </div>
      </div>
    </Transition>

    <!-- Edit modal -->
    <HrmsModal v-model="showEditModal" title="Edit Candidate" size="xl">
      <div v-if="editDraft" class="candidates-edit-layout">
        <div class="candidates-edit-layout__form">
          <CandidateVerifyForm v-model="editDraft" />
        </div>
        <aside class="candidates-edit-layout__preview">
          <ResumePreview
            :src="editResumeUrl"
            :loading="editResumeLoading"
            :error="editResumeError"
            :filename="selected ? `${selected.first_name}_${selected.last_name}_resume.pdf` : null"
            height="min(60vh, 640px)"
          />
        </aside>
      </div>
      <template #footer>
        <button type="button" class="hrms-btn" @click="closeEdit">Cancel</button>
        <button type="button" class="hrms-btn hrms-btn--primary" :disabled="saving" @click="saveEdit">
          {{ saving ? `Saving${ELLIPSIS}` : 'Save Changes' }}
        </button>
      </template>
    </HrmsModal>

  </div>
</template>

<style scoped>
.candidates-edit-layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(280px, 0.9fr);
  gap: 20px;
  align-items: start;
}

@media (max-width: 900px) {
  .candidates-edit-layout {
    grid-template-columns: 1fr;
  }
}

.panel-enter-active,
.panel-leave-active {
  transition: transform 0.28s cubic-bezier(0.4, 0, 0.2, 1), opacity 0.2s;
}

.panel-enter-from,
.panel-leave-to {
  transform: translateX(32px);
  opacity: 0;
}
</style>
