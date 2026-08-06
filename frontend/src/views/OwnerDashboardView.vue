<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import {
  downloadCandidateResume,
  fetchCandidate,
  fetchCandidateResumeBlob,
} from '@/api/candidates'
import {
  approveSubmission,
  downloadApprovedClientSubmissions,
  downloadSubmission,
  fetchOwnerDashboard,
} from '@/api/submissions'
import {
  fetchEmailStatus,
  shareApprovedProfiles,
  shortlistApplications,
} from '@/api/pipeline'
import ResumePreview from '@/components/candidates/ResumePreview.vue'
import HrmsAlert from '@/components/ui/HrmsAlert.vue'
import HrmsModal from '@/components/ui/HrmsModal.vue'
import type { Candidate } from '@/types/candidate'
import type {
  CandidateSubmission,
  OwnerDashboardClient,
  OwnerDashboardJob,
  OwnerStatusType,
} from '@/types/jobRequirement'
import {
  avatarHue,
  EMPTY,
  formatInr,
  initials,
  orEmpty,
} from '@/utils/format'

type StatusFilter = 'all' | OwnerStatusType
type DetailTab = 'job' | 'overview' | 'experience' | 'education' | 'submission'

const dashboard = ref<OwnerDashboardClient[]>([])
const selected = ref<OwnerDashboardClient | null>(null)
const selectedJobId = ref<string | null>(null)
const loading = ref(true)
const error = ref('')
const success = ref('')
const actioning = ref<string | null>(null)
const downloadingClient = ref(false)
const searchQuery = ref('')
const statusFilter = ref<StatusFilter>('all')

const viewingSubmission = ref<CandidateSubmission | null>(null)
const candidateDetail = ref<Candidate | null>(null)
const loadingCandidate = ref(false)
const detailTab = ref<DetailTab>('overview')
const downloadingResume = ref(false)
const showResumePreview = ref(false)
const previewResumeUrl = ref<string | null>(null)
const previewResumeLoading = ref(false)
const previewResumeError = ref<string | null>(null)
const sharingEmail = ref(false)
const shortlisting = ref(false)
const emailConfigured = ref(false)
const showShareModal = ref(false)
const shareEmails = ref('')
const shareMessage = ref('')

function revokePreviewResumeUrl() {
  if (previewResumeUrl.value) {
    URL.revokeObjectURL(previewResumeUrl.value)
    previewResumeUrl.value = null
  }
}

async function openResumePreview() {
  if (!candidateDetail.value?.resume_url) return
  showResumePreview.value = true
  revokePreviewResumeUrl()
  previewResumeError.value = null
  previewResumeLoading.value = true
  try {
    const blob = await fetchCandidateResumeBlob(candidateDetail.value.id)
    previewResumeUrl.value = URL.createObjectURL(
      new Blob([blob], { type: 'application/pdf' }),
    )
  } catch (err) {
    previewResumeError.value =
      err instanceof Error ? err.message : 'Failed to load resume preview'
  } finally {
    previewResumeLoading.value = false
  }
}

function closeResumePreview() {
  showResumePreview.value = false
  revokePreviewResumeUrl()
  previewResumeError.value = null
}

watch(showResumePreview, (open) => {
  if (!open) {
    revokePreviewResumeUrl()
    previewResumeError.value = null
  }
})

onBeforeUnmount(revokePreviewResumeUrl)

const statusMeta: Record<string, { label: string; color: string }> = {
  active: { label: 'Active', color: '#22c55e' },
  pending_approval: { label: 'Pending', color: '#f59e0b' },
  interviewing: { label: 'Interviewing', color: '#3b82f6' },
  offered: { label: 'Offered', color: '#a855f7' },
  on_hold: { label: 'On Hold', color: '#f59e0b' },
  rejected: { label: 'Rejected', color: '#ef4444' },
  hired: { label: 'Hired', color: '#14b8a6' },
}

const proficiencyMeta: Record<string, string> = {
  Beginner: '#94a3b8',
  Intermediate: '#60a5fa',
  Advanced: '#818cf8',
  Expert: '#a78bfa',
}

const getCandidateStatus = (s: string) =>
  statusMeta[s] ?? { label: s.replace(/_/g, ' '), color: '#94a3b8' }

async function load() {
  loading.value = true
  error.value = ''
  try {
    const [dash, mail] = await Promise.all([
      fetchOwnerDashboard(),
      fetchEmailStatus().catch(() => ({ configured: false })),
    ])
    dashboard.value = dash
    emailConfigured.value = mail.configured
    if (selected.value) {
      const refreshed = dashboard.value.find((c) => c.client_id === selected.value!.client_id)
      selected.value = refreshed ?? null
      if (selected.value && selectedJobId.value) {
        const jobExists = selected.value.jobs.some((j) => j.job_requirement_id === selectedJobId.value)
        if (!jobExists) selectedJobId.value = null
      }
      if (viewingSubmission.value && selected.value) {
        const found = selected.value.jobs
          .flatMap((j) => j.submissions)
          .find((s) => s.id === viewingSubmission.value!.id)
        viewingSubmission.value = found ?? null
        if (!found) {
          candidateDetail.value = null
        }
      }
    }
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Failed to load submissions'
  } finally {
    loading.value = false
  }
}

onMounted(load)

const filteredClients = computed(() => {
  const q = searchQuery.value.trim().toLowerCase()
  if (!q) return dashboard.value
  return dashboard.value.filter(
    (client) =>
      client.company_name.toLowerCase().includes(q) ||
      client.jobs.some(
        (job) =>
          job.job_title.toLowerCase().includes(q) ||
          job.submissions.some(
            (s) =>
              s.candidate_name.toLowerCase().includes(q) ||
              s.candidate_email.toLowerCase().includes(q),
          ),
      ),
  )
})

const totalSubmissions = (client: OwnerDashboardClient) =>
  client.jobs.reduce((sum, j) => sum + j.submissions.length, 0)

const approvedCount = (client: OwnerDashboardClient) =>
  client.jobs.reduce(
    (sum, j) => sum + j.submissions.filter((s) => s.owner_status === 'approved').length,
    0,
  )

const pendingCount = (client: OwnerDashboardClient) =>
  client.jobs.reduce(
    (sum, j) => sum + j.submissions.filter((s) => s.owner_status === 'pending_review').length,
    0,
  )

function selectClient(client: OwnerDashboardClient) {
  selected.value = client
  selectedJobId.value = client.jobs[0]?.job_requirement_id ?? null
  statusFilter.value = 'all'
  closeCandidateDetail()
}

function closePanel() {
  selected.value = null
  selectedJobId.value = null
  closeCandidateDetail()
}

function closeCandidateDetail() {
  viewingSubmission.value = null
  candidateDetail.value = null
  detailTab.value = 'job'
}

const selectedJob = computed<OwnerDashboardJob | null>(() => {
  if (!selected.value || !selectedJobId.value) return null
  return selected.value.jobs.find((j) => j.job_requirement_id === selectedJobId.value) ?? null
})

const viewingJob = computed<OwnerDashboardJob | null>(() => {
  if (!selected.value || !viewingSubmission.value) return selectedJob.value
  return (
    selected.value.jobs.find(
      (j) => j.job_requirement_id === viewingSubmission.value!.job_requirement_id,
    ) ?? selectedJob.value
  )
})

const filteredSubmissions = computed(() => {
  const subs = selectedJob.value?.submissions ?? []
  if (statusFilter.value === 'all') return subs
  return subs.filter((s) => s.owner_status === statusFilter.value)
})

const submissionDataEntries = computed(() => {
  const data = viewingSubmission.value?.submission_data
  if (!data) return []
  return Object.entries(data).filter(([, v]) => v != null && String(v).trim() !== '')
})

async function openCandidate(sub: CandidateSubmission) {
  viewingSubmission.value = sub
  selectedJobId.value = sub.job_requirement_id
  candidateDetail.value = null
  detailTab.value = 'job'
  loadingCandidate.value = true
  error.value = ''
  try {
    candidateDetail.value = await fetchCandidate(sub.candidate_id)
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Failed to load candidate'
    viewingSubmission.value = null
  } finally {
    loadingCandidate.value = false
  }
}

function patchSubmission(updated: CandidateSubmission) {
  for (const client of dashboard.value) {
    for (const job of client.jobs) {
      const idx = job.submissions.findIndex((s) => s.id === updated.id)
      if (idx !== -1) {
        job.submissions[idx] = updated
        if (selected.value?.client_id === client.client_id) {
          selected.value = client
        }
        if (viewingSubmission.value?.id === updated.id) {
          viewingSubmission.value = updated
        }
        return
      }
    }
  }
}

async function handleApprove(sub: CandidateSubmission) {
  actioning.value = sub.id
  error.value = ''
  try {
    const updated = await approveSubmission(sub.id, 'approved')
    patchSubmission(updated)
    success.value = `${sub.candidate_name} approved`
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Failed to approve'
  } finally {
    actioning.value = null
  }
}

async function handleReject(sub: CandidateSubmission) {
  actioning.value = sub.id
  error.value = ''
  try {
    const updated = await approveSubmission(sub.id, 'rejected')
    patchSubmission(updated)
    success.value = `${sub.candidate_name} rejected`
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Failed to reject'
  } finally {
    actioning.value = null
  }
}

async function handleDownload(sub: CandidateSubmission) {
  actioning.value = `dl-${sub.id}`
  error.value = ''
  try {
    const filename = `${sub.candidate_name.replace(/\s+/g, '_')}_${sub.client_name.replace(/\s+/g, '_')}_profile.xlsx`
    await downloadSubmission(sub.id, filename)
    success.value = `Downloaded profile for ${sub.candidate_name}`
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Download failed'
  } finally {
    actioning.value = null
  }
}

async function handleDownloadApprovedClient() {
  if (!selected.value) return
  downloadingClient.value = true
  error.value = ''
  try {
    const safeName = selected.value.company_name.replace(/\s+/g, '_')
    await downloadApprovedClientSubmissions(
      selected.value.client_id,
      `${safeName}_approved_profiles.xlsx`,
    )
    success.value = `Downloaded approved profiles for ${selected.value.company_name}`
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Download failed'
  } finally {
    downloadingClient.value = false
  }
}

function openShareModal() {
  shareEmails.value = ''
  shareMessage.value = ''
  showShareModal.value = true
}

async function handleShareApproved() {
  if (!selected.value) return
  sharingEmail.value = true
  error.value = ''
  try {
    const emails = shareEmails.value
      .split(/[,;\s]+/)
      .map((e) => e.trim())
      .filter(Boolean)
    const result = await shareApprovedProfiles(selected.value.client_id, {
      to_emails: emails.length ? emails : undefined,
      message: shareMessage.value.trim() || undefined,
    })
    success.value = `Shared ${result.candidate_count} profile(s) to ${result.sent_to.join(', ')}`
    showShareModal.value = false
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Failed to share by email'
  } finally {
    sharingEmail.value = false
  }
}

async function handleAddToPipeline(sub?: CandidateSubmission) {
  if (!selected.value) return
  const targets = sub
    ? [sub]
    : selected.value.jobs.flatMap((j) => j.submissions).filter((s) => s.owner_status === 'approved')
  if (!targets.length) {
    error.value = 'No approved candidates to add to pipeline'
    return
  }
  shortlisting.value = true
  error.value = ''
  try {
    await shortlistApplications(
      targets.map((t) => t.id),
      'Added to hiring pipeline (Applied)',
    )
    success.value =
      targets.length === 1
        ? `${targets[0]!.candidate_name} added to pipeline (Applied)`
        : `${targets.length} candidates added to pipeline (Applied)`
    await load()
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Failed to add to pipeline'
  } finally {
    shortlisting.value = false
  }
}

function isInPipeline(sub: CandidateSubmission) {
  return sub.owner_status === 'approved' && !!sub.in_pipeline
}

async function handleDownloadResume() {
  if (!candidateDetail.value?.resume_url) return
  downloadingResume.value = true
  error.value = ''
  try {
    await downloadCandidateResume(candidateDetail.value)
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Resume download failed'
  } finally {
    downloadingResume.value = false
  }
}

const ownerStatusColor = (s: string) => {
  if (s === 'approved') return 'var(--hrms-success)'
  if (s === 'rejected') return '#ef4444'
  return 'var(--hrms-warning, #d97706)'
}

const ownerStatusLabel = (s: string) => {
  if (s === 'approved') return 'Approved'
  if (s === 'rejected') return 'Rejected'
  return 'Pending Review'
}

const jobStatusColor = (s: string) => {
  if (s === 'open') return 'var(--hrms-success)'
  if (s === 'on_hold') return 'var(--hrms-warning, #d97706)'
  if (s === 'filled') return 'var(--hrms-primary)'
  return 'var(--hrms-text-muted)'
}

const formatDate = (d: string | null | undefined) =>
  d ? new Date(d).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' }) : EMPTY

const formatExpDate = (d: string | null | undefined) => {
  if (!d) return 'Present'
  return new Date(d).toLocaleDateString('en-IN', { month: 'short', year: 'numeric' })
}

const formatEnum = (value: string | null | undefined) => {
  if (!value) return EMPTY
  return value.replace(/_/g, ' ')
}

const experienceLabel = (job: OwnerDashboardJob | null | undefined) => {
  if (!job) return EMPTY
  if (job.experience_min == null && job.experience_max == null) return EMPTY
  if (job.experience_min != null && job.experience_max != null) {
    return `${job.experience_min}–${job.experience_max} yrs`
  }
  if (job.experience_min != null) return `${job.experience_min}+ yrs`
  return `Up to ${job.experience_max} yrs`
}

const salaryRangeLabel = (job: OwnerDashboardJob | null | undefined) => {
  if (!job) return EMPTY
  if (job.salary_min == null && job.salary_max == null) return EMPTY
  if (job.salary_min != null && job.salary_max != null) {
    return `${formatInr(job.salary_min)} – ${formatInr(job.salary_max)}`
  }
  if (job.salary_min != null) return `From ${formatInr(job.salary_min)}`
  return `Up to ${formatInr(job.salary_max)}`
}
</script>

<template>
  <div class="hrms-split">
    <div class="hrms-split__main" :class="{ 'hrms-split__main--narrow': selected }">
      <div class="hrms-split__header">
        <div class="hrms-page-header hrms-page-header--compact">
          <div>
            <h1 class="hrms-page-title hrms-page-title--sm">Submissions</h1>
            <span class="hrms-page-count">{{ filteredClients.length }} clients</span>
          </div>
          <button type="button" class="hrms-btn hrms-btn--sm" @click="load">Refresh</button>
        </div>

        <div class="hrms-controls">
          <input
            v-model="searchQuery"
            class="hrms-input hrms-search-input"
            type="search"
            placeholder="Search by client, job, or candidate…"
          />
        </div>
      </div>

      <HrmsAlert v-if="error" type="error" dismissible @dismiss="error = ''">{{ error }}</HrmsAlert>
      <HrmsAlert v-if="success" type="success" dismissible @dismiss="success = ''">{{ success }}</HrmsAlert>

      <div v-if="loading" class="hrms-loading">Loading submissions…</div>

      <div v-else class="hrms-split__list hrms-scroll">
        <div
          v-for="client in filteredClients"
          :key="client.client_id"
          class="hrms-card hrms-card--interactive hrms-entity-card"
          :class="{ 'hrms-card--selected': selected?.client_id === client.client_id }"
          @click="selectClient(client)"
        >
          <div class="hrms-avatar" :style="`--hue: ${avatarHue(client.client_id)}`">
            {{ initials(client.company_name.split(' ')[0] ?? '', client.company_name.split(' ')[1] ?? '') }}
          </div>
          <div class="hrms-entity-card__body">
            <div class="hrms-entity-card__name-row">
              <span class="hrms-entity-card__name">{{ client.company_name }}</span>
              <span
                v-if="pendingCount(client) > 0"
                class="hrms-status-badge"
                :style="`--sc: ${ownerStatusColor('pending_review')}`"
              >
                {{ pendingCount(client) }} pending
              </span>
            </div>
            <div class="hrms-entity-card__role">
              {{ client.jobs.length }} job{{ client.jobs.length !== 1 ? 's' : '' }}
            </div>
            <div class="hrms-entity-card__meta">
              <span>{{ totalSubmissions(client) }} submissions</span>
              <span>{{ approvedCount(client) }} approved</span>
            </div>
          </div>
        </div>

        <div v-if="filteredClients.length === 0" class="hrms-empty">
          <p v-if="searchQuery">No clients match your search.</p>
          <p v-else>No candidate submissions yet.</p>
        </div>
      </div>
    </div>

    <Transition name="panel">
      <div v-if="selected" class="hrms-split__aside">
        <!-- Candidate detail -->
        <template v-if="viewingSubmission">
          <div class="hrms-panel-header">
            <button class="hrms-btn hrms-btn--icon" style="margin-bottom: 16px" @click="closeCandidateDetail">
              <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
                <path d="M11.5 3.5L6 9l5.5 5.5" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            </button>

            <div v-if="loadingCandidate" class="hrms-loading" style="padding: 24px 0">Loading candidate…</div>

            <template v-else-if="candidateDetail">
              <div class="hrms-panel-hero">
                <div
                  class="hrms-avatar hrms-avatar--lg"
                  :style="`--hue: ${avatarHue(candidateDetail.id)}`"
                >
                  {{ initials(candidateDetail.first_name, candidateDetail.last_name) }}
                </div>
                <div>
                  <h2 class="hrms-panel-name">
                    {{ candidateDetail.first_name }} {{ candidateDetail.last_name }}
                  </h2>
                  <p class="hrms-panel-role">
                    {{ viewingSubmission.job_title }}
                    <span> · {{ viewingSubmission.client_name }}</span>
                  </p>
                  <div class="submissions-badges">
                    <span
                      class="hrms-status-badge"
                      :style="`--sc: ${ownerStatusColor(viewingSubmission.owner_status)}`"
                    >
                      {{ ownerStatusLabel(viewingSubmission.owner_status) }}
                    </span>
                    <span
                      class="hrms-status-badge"
                      :style="`--sc: ${getCandidateStatus(candidateDetail.candidate_status).color}`"
                    >
                      {{ getCandidateStatus(candidateDetail.candidate_status).label }}
                    </span>
                  </div>
                </div>
              </div>

              <div class="hrms-actions hrms-actions--inline" style="padding-bottom: 16px">
                <button
                  v-if="viewingSubmission.owner_status !== 'approved'"
                  type="button"
                  class="hrms-btn hrms-btn--sm hrms-btn--success"
                  :disabled="actioning === viewingSubmission.id"
                  @click="handleApprove(viewingSubmission)"
                >
                  Approve
                </button>
                <button
                  v-if="viewingSubmission.owner_status !== 'rejected'"
                  type="button"
                  class="hrms-btn hrms-btn--sm hrms-btn--danger"
                  :disabled="actioning === viewingSubmission.id"
                  @click="handleReject(viewingSubmission)"
                >
                  Reject
                </button>
                <button
                  v-if="viewingSubmission.owner_status === 'approved'"
                  type="button"
                  class="hrms-btn hrms-btn--primary hrms-btn--sm"
                  :disabled="actioning === `dl-${viewingSubmission.id}`"
                  @click="handleDownload(viewingSubmission)"
                >
                  {{ actioning === `dl-${viewingSubmission.id}` ? 'Downloading…' : 'Download Excel' }}
                </button>
                <button
                  v-if="viewingSubmission.owner_status === 'approved' && !isInPipeline(viewingSubmission)"
                  type="button"
                  class="hrms-btn hrms-btn--sm hrms-btn--success"
                  :disabled="shortlisting"
                  @click="handleAddToPipeline(viewingSubmission)"
                >
                  {{ shortlisting ? 'Adding…' : 'Add to Pipeline' }}
                </button>
                <RouterLink
                  v-if="viewingSubmission.owner_status === 'approved' && isInPipeline(viewingSubmission)"
                  class="hrms-btn hrms-btn--sm"
                  to="/pipeline"
                >
                  View in Pipeline
                </RouterLink>
                <button
                  v-if="candidateDetail.resume_url"
                  type="button"
                  class="hrms-btn hrms-btn--sm"
                  @click="openResumePreview"
                >
                  Resume
                </button>
                <a
                  v-if="candidateDetail.linkedin_url"
                  :href="candidateDetail.linkedin_url"
                  target="_blank"
                  rel="noopener"
                  class="hrms-btn hrms-btn--sm"
                >
                  LinkedIn
                </a>
                <a :href="`mailto:${candidateDetail.email}`" class="hrms-btn hrms-btn--sm">
                  Email
                </a>
              </div>

              <div class="hrms-tabs">
                <button
                  type="button"
                  class="hrms-tab"
                  :class="{ 'hrms-tab--active': detailTab === 'job' }"
                  @click="detailTab = 'job'"
                >
                  Job Requirement
                </button>
                <button
                  type="button"
                  class="hrms-tab"
                  :class="{ 'hrms-tab--active': detailTab === 'overview' }"
                  @click="detailTab = 'overview'"
                >
                  Candidate
                </button>
                <button
                  type="button"
                  class="hrms-tab"
                  :class="{ 'hrms-tab--active': detailTab === 'experience' }"
                  @click="detailTab = 'experience'"
                >
                  Experience
                </button>
                <button
                  type="button"
                  class="hrms-tab"
                  :class="{ 'hrms-tab--active': detailTab === 'education' }"
                  @click="detailTab = 'education'"
                >
                  Education
                </button>
                <button
                  v-if="submissionDataEntries.length"
                  type="button"
                  class="hrms-tab"
                  :class="{ 'hrms-tab--active': detailTab === 'submission' }"
                  @click="detailTab = 'submission'"
                >
                  Submitted
                </button>
              </div>
            </template>
          </div>

          <div v-if="candidateDetail && !loadingCandidate" class="hrms-panel-body hrms-scroll">
            <template v-if="detailTab === 'job'">
              <section class="hrms-section">
                <div class="submissions-job-meta">
                  <h3 class="hrms-section-title" style="margin: 0">
                    {{ viewingJob?.job_title ?? viewingSubmission.job_title }}
                  </h3>
                  <span
                    v-if="viewingJob"
                    class="hrms-status-badge"
                    :style="`--sc: ${jobStatusColor(viewingJob.status)}`"
                  >
                    {{ formatEnum(viewingJob.status) }}
                  </span>
                </div>
                <p class="hrms-panel-role" style="margin-top: 6px">
                  {{ viewingSubmission.client_name }}
                  <span v-if="viewingJob?.location"> · {{ viewingJob.location }}</span>
                </p>
              </section>

              <section class="hrms-section">
                <h3 class="hrms-section-title">Requirement details</h3>
                <div class="hrms-info-grid">
                  <div class="hrms-info-item">
                    <span class="hrms-info-label">Assigned recruiter</span>
                    <span class="hrms-info-value">
                      {{ viewingJob?.assigned_recruiter_name ?? EMPTY }}
                    </span>
                  </div>
                  <div class="hrms-info-item">
                    <span class="hrms-info-label">Department</span>
                    <span class="hrms-info-value">{{ viewingJob?.department ?? EMPTY }}</span>
                  </div>
                  <div class="hrms-info-item">
                    <span class="hrms-info-label">Location</span>
                    <span class="hrms-info-value">{{ viewingJob?.location ?? EMPTY }}</span>
                  </div>
                  <div class="hrms-info-item">
                    <span class="hrms-info-label">Employment type</span>
                    <span class="hrms-info-value">{{ formatEnum(viewingJob?.employment_type) }}</span>
                  </div>
                  <div class="hrms-info-item">
                    <span class="hrms-info-label">Work mode</span>
                    <span class="hrms-info-value">{{ formatEnum(viewingJob?.work_mode) }}</span>
                  </div>
                  <div class="hrms-info-item">
                    <span class="hrms-info-label">Experience</span>
                    <span class="hrms-info-value">{{ experienceLabel(viewingJob) }}</span>
                  </div>
                  <div class="hrms-info-item">
                    <span class="hrms-info-label">Salary range</span>
                    <span class="hrms-info-value">{{ salaryRangeLabel(viewingJob) }}</span>
                  </div>
                  <div class="hrms-info-item">
                    <span class="hrms-info-label">Open positions</span>
                    <span class="hrms-info-value">
                      {{ viewingJob?.open_positions != null ? viewingJob.open_positions : EMPTY }}
                    </span>
                  </div>
                  <div class="hrms-info-item">
                    <span class="hrms-info-label">Priority</span>
                    <span class="hrms-info-value">{{ formatEnum(viewingJob?.priority) }}</span>
                  </div>
                  <div class="hrms-info-item">
                    <span class="hrms-info-label">Requirement type</span>
                    <span class="hrms-info-value">{{ formatEnum(viewingJob?.requirement_type) }}</span>
                  </div>
                  <div class="hrms-info-item">
                    <span class="hrms-info-label">Created</span>
                    <span class="hrms-info-value">{{ formatDate(viewingJob?.created_at) }}</span>
                  </div>
                </div>
              </section>

              <section v-if="viewingJob?.job_description" class="hrms-section">
                <h3 class="hrms-section-title">Job description</h3>
                <p class="hrms-info-value submissions-job-description">
                  {{ viewingJob.job_description }}
                </p>
              </section>

              <section class="hrms-section">
                <h3 class="hrms-section-title">This submission</h3>
                <div class="hrms-info-grid">
                  <div class="hrms-info-item">
                    <span class="hrms-info-label">Candidate</span>
                    <span class="hrms-info-value">{{ viewingSubmission.candidate_name }}</span>
                  </div>
                  <div class="hrms-info-item">
                    <span class="hrms-info-label">Submitted by</span>
                    <span class="hrms-info-value">
                      {{ viewingSubmission.submitted_by_name ?? EMPTY }}
                    </span>
                  </div>
                  <div class="hrms-info-item">
                    <span class="hrms-info-label">Submitted on</span>
                    <span class="hrms-info-value">{{ formatDate(viewingSubmission.submitted_at) }}</span>
                  </div>
                  <div class="hrms-info-item">
                    <span class="hrms-info-label">Review status</span>
                    <span
                      class="hrms-status-badge"
                      :style="`--sc: ${ownerStatusColor(viewingSubmission.owner_status)}`"
                    >
                      {{ ownerStatusLabel(viewingSubmission.owner_status) }}
                    </span>
                  </div>
                </div>
              </section>
            </template>

            <template v-else-if="detailTab === 'overview'">
              <section class="hrms-section">
                <h3 class="hrms-section-title">Contact & Personal</h3>
                <div class="hrms-info-grid">
                  <div class="hrms-info-item">
                    <span class="hrms-info-label">Email</span>
                    <a :href="`mailto:${candidateDetail.email}`" class="hrms-info-value hrms-info-link">
                      {{ candidateDetail.email }}
                    </a>
                  </div>
                  <div class="hrms-info-item">
                    <span class="hrms-info-label">Phone</span>
                    <span class="hrms-info-value">{{ orEmpty(candidateDetail.phone) }}</span>
                  </div>
                  <div class="hrms-info-item">
                    <span class="hrms-info-label">Nationality</span>
                    <span class="hrms-info-value">{{ candidateDetail.nationality ?? EMPTY }}</span>
                  </div>
                  <div class="hrms-info-item">
                    <span class="hrms-info-label">Date of Birth</span>
                    <span class="hrms-info-value">
                      {{
                        candidateDetail.date_of_birth
                          ? new Date(candidateDetail.date_of_birth).toLocaleDateString('en-IN')
                          : EMPTY
                      }}
                    </span>
                  </div>
                  <div class="hrms-info-item">
                    <span class="hrms-info-label">Languages</span>
                    <span class="hrms-info-value">{{ candidateDetail.languages_known ?? EMPTY }}</span>
                  </div>
                  <div class="hrms-info-item">
                    <span class="hrms-info-label">Visa Status</span>
                    <span class="hrms-info-value">{{ candidateDetail.visa_status ?? EMPTY }}</span>
                  </div>
                  <div class="hrms-info-item">
                    <span class="hrms-info-label">Current Location</span>
                    <span class="hrms-info-value">{{ candidateDetail.current_location ?? EMPTY }}</span>
                  </div>
                  <div class="hrms-info-item">
                    <span class="hrms-info-label">Preferred Location</span>
                    <span class="hrms-info-value">{{ candidateDetail.preferred_location ?? EMPTY }}</span>
                  </div>
                  <div class="hrms-info-item">
                    <span class="hrms-info-label">Industry</span>
                    <span class="hrms-info-value">{{ candidateDetail.industry ?? EMPTY }}</span>
                  </div>
                </div>
              </section>

              <section class="hrms-section">
                <h3 class="hrms-section-title">Compensation & Availability</h3>
                <div class="hrms-metric-grid hrms-metric-grid--cols-4">
                  <div class="hrms-metric-card">
                    <div class="hrms-metric-label">Current CTC</div>
                    <div class="hrms-metric-value">{{ formatInr(candidateDetail.current_ctc) }}</div>
                  </div>
                  <div class="hrms-metric-card hrms-metric-card--accent">
                    <div class="hrms-metric-label">Expected CTC</div>
                    <div class="hrms-metric-value">{{ formatInr(candidateDetail.expected_ctc) }}</div>
                  </div>
                  <div class="hrms-metric-card">
                    <div class="hrms-metric-label">Notice Period</div>
                    <div class="hrms-metric-value">{{ candidateDetail.notice_period ?? EMPTY }}</div>
                  </div>
                  <div class="hrms-metric-card">
                    <div class="hrms-metric-label">UAE Experience</div>
                    <div class="hrms-metric-value">
                      {{
                        candidateDetail.uae_experience_years != null
                          ? `${candidateDetail.uae_experience_years}y`
                          : EMPTY
                      }}
                    </div>
                  </div>
                </div>
              </section>

              <section class="hrms-section">
                <h3 class="hrms-section-title">Skills {{ candidateDetail.skills.length }}</h3>
                <div v-if="candidateDetail.skills.length" class="hrms-data-table hrms-data-table--cols-3">
                  <div class="hrms-data-table__row hrms-data-table__row--header">
                    <span>Skill</span>
                    <span>Proficiency</span>
                    <span>Experience</span>
                  </div>
                  <div
                    v-for="sk in candidateDetail.skills"
                    :key="sk.name"
                    class="hrms-data-table__row"
                  >
                    <span style="font-weight: 550">{{ sk.name }}</span>
                    <span
                      class="hrms-proficiency-chip"
                      :style="`--pc: ${proficiencyMeta[sk.proficiency_level ?? ''] ?? '#94a3b8'}`"
                    >
                      {{ sk.proficiency_level ?? EMPTY }}
                    </span>
                    <span style="color: var(--hrms-text-secondary); font-size: 0.77rem">
                      {{ sk.years_experience ? `${sk.years_experience}y` : EMPTY }}
                    </span>
                  </div>
                </div>
                <p v-else class="hrms-empty-inline">No skills recorded.</p>
              </section>

              <section class="hrms-section">
                <h3 class="hrms-section-title">Current role</h3>
                <div class="hrms-info-grid">
                  <div class="hrms-info-item">
                    <span class="hrms-info-label">Designation</span>
                    <span class="hrms-info-value">
                      {{ candidateDetail.current_designation ?? EMPTY }}
                    </span>
                  </div>
                  <div class="hrms-info-item">
                    <span class="hrms-info-label">Company</span>
                    <span class="hrms-info-value">{{ candidateDetail.current_company ?? EMPTY }}</span>
                  </div>
                  <div class="hrms-info-item">
                    <span class="hrms-info-label">Submitted by</span>
                    <span class="hrms-info-value">{{ viewingSubmission.submitted_by_name ?? EMPTY }}</span>
                  </div>
                  <div class="hrms-info-item">
                    <span class="hrms-info-label">Submitted on</span>
                    <span class="hrms-info-value">{{ formatDate(viewingSubmission.submitted_at) }}</span>
                  </div>
                </div>
              </section>
            </template>

            <template v-else-if="detailTab === 'experience'">
              <section class="hrms-section">
                <h3 class="hrms-section-title">
                  Work Experience
                  <span
                    v-if="candidateDetail.total_experience_years"
                    class="hrms-section-badge"
                  >
                    {{ candidateDetail.total_experience_years }}y total
                  </span>
                </h3>
                <div v-if="candidateDetail.work_experiences.length" class="hrms-timeline">
                  <div
                    v-for="(exp, i) in candidateDetail.work_experiences"
                    :key="i"
                    class="hrms-timeline-item"
                  >
                    <div
                      class="hrms-timeline-dot"
                      :class="{ 'hrms-timeline-dot--current': exp.currently_working }"
                    />
                    <div class="hrms-timeline-content">
                      <div class="hrms-timeline-header">
                        <span class="hrms-timeline-title">{{ exp.company_name }}</span>
                        <span class="hrms-timeline-dates">
                          {{ formatExpDate(exp.start_date) }} –
                          {{ exp.currently_working ? 'Present' : formatExpDate(exp.end_date) }}
                        </span>
                      </div>
                      <div class="hrms-timeline-subtitle">{{ exp.designation ?? EMPTY }}</div>
                      <p v-if="exp.job_description" class="hrms-timeline-desc">
                        {{ exp.job_description }}
                      </p>
                    </div>
                  </div>
                </div>
                <p v-else class="hrms-empty-inline">No work experience recorded.</p>
              </section>
            </template>

            <template v-else-if="detailTab === 'education'">
              <section class="hrms-section">
                <h3 class="hrms-section-title">Education</h3>
                <div v-if="candidateDetail.education_records.length" class="hrms-edu-list">
                  <div
                    v-for="(ed, i) in candidateDetail.education_records"
                    :key="i"
                    class="hrms-edu-card"
                  >
                    <div class="hrms-edu-card__degree">
                      {{ ed.degree }}
                      <span v-if="ed.specialization"> · {{ ed.specialization }}</span>
                    </div>
                    <div class="hrms-edu-card__inst">{{ ed.institution ?? EMPTY }}</div>
                    <div class="hrms-edu-card__meta">
                      <span v-if="ed.start_year || ed.end_year">
                        {{ ed.start_year ?? '?' }} – {{ ed.end_year ?? 'Present' }}
                      </span>
                      <span v-if="ed.percentage" class="hrms-chip">{{ ed.percentage }}%</span>
                    </div>
                  </div>
                </div>
                <p v-else class="hrms-empty-inline">No education records found.</p>
              </section>
            </template>

            <template v-else-if="detailTab === 'submission'">
              <section class="hrms-section">
                <h3 class="hrms-section-title">Submitted form data</h3>
                <div v-if="submissionDataEntries.length" class="hrms-info-grid">
                  <div
                    v-for="[label, value] in submissionDataEntries"
                    :key="label"
                    class="hrms-info-item"
                  >
                    <span class="hrms-info-label">{{ label }}</span>
                    <span class="hrms-info-value">{{ value }}</span>
                  </div>
                </div>
                <p v-else class="hrms-empty-inline">No form data was submitted.</p>
              </section>
            </template>
          </div>
        </template>

        <!-- Client + job submissions list -->
        <template v-else>
          <div class="hrms-panel-header">
            <button class="hrms-btn hrms-btn--icon" style="margin-bottom: 16px" @click="closePanel">
              <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
                <path d="M13.5 4.5L4.5 13.5M4.5 4.5L13.5 13.5" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/>
              </svg>
            </button>

            <div class="hrms-panel-hero">
              <div class="hrms-avatar hrms-avatar--lg" :style="`--hue: ${avatarHue(selected.client_id)}`">
                {{ initials(selected.company_name.split(' ')[0] ?? '', selected.company_name.split(' ')[1] ?? '') }}
              </div>
              <div>
                <h2 class="hrms-panel-name">{{ selected.company_name }}</h2>
                <p class="hrms-panel-role">
                  {{ totalSubmissions(selected) }} submissions · {{ approvedCount(selected) }} approved
                </p>
              </div>
            </div>

            <div class="hrms-actions hrms-actions--inline" style="padding-bottom: 16px">
              <button
                v-if="approvedCount(selected) > 0"
                type="button"
                class="hrms-btn hrms-btn--primary hrms-btn--sm"
                :disabled="downloadingClient"
                @click="handleDownloadApprovedClient"
              >
                {{ downloadingClient ? 'Downloading…' : 'Download Approved' }}
              </button>
              <button
                v-if="approvedCount(selected) > 0"
                type="button"
                class="hrms-btn hrms-btn--sm"
                :disabled="sharingEmail"
                :title="
                  emailConfigured
                    ? 'Email approved profiles to client contacts'
                    : 'Configure SMTP in backend/.env, or download Excel and send manually'
                "
                @click="openShareModal"
              >
                Share by Email
              </button>
              <button
                v-if="approvedCount(selected) > 0"
                type="button"
                class="hrms-btn hrms-btn--sm hrms-btn--success"
                :disabled="shortlisting"
                @click="handleAddToPipeline()"
              >
                {{ shortlisting ? 'Adding…' : 'Add Approved to Pipeline' }}
              </button>
            </div>

            <div class="hrms-tabs">
              <button
                v-for="job in selected.jobs"
                :key="job.job_requirement_id"
                type="button"
                class="hrms-tab"
                :class="{ 'hrms-tab--active': selectedJobId === job.job_requirement_id }"
                @click="selectedJobId = job.job_requirement_id; statusFilter = 'all'"
              >
                {{ job.job_title }}
                <span class="submissions-job-count">{{ job.submissions.length }}</span>
              </button>
            </div>
          </div>

          <div class="hrms-panel-body hrms-scroll">
            <template v-if="selectedJob">
              <section class="hrms-section">
                <div class="submissions-job-meta">
                  <h3 class="hrms-section-title" style="margin: 0">{{ selectedJob.job_title }}</h3>
                  <span class="hrms-status-badge" :style="`--sc: ${jobStatusColor(selectedJob.status)}`">
                    {{ formatEnum(selectedJob.status) }}
                  </span>
                </div>

                <div class="hrms-info-grid" style="margin-top: 14px">
                  <div class="hrms-info-item">
                    <span class="hrms-info-label">Assigned recruiter</span>
                    <span class="hrms-info-value">
                      {{ selectedJob.assigned_recruiter_name ?? EMPTY }}
                    </span>
                  </div>
                  <div class="hrms-info-item">
                    <span class="hrms-info-label">Department</span>
                    <span class="hrms-info-value">{{ selectedJob.department ?? EMPTY }}</span>
                  </div>
                  <div class="hrms-info-item">
                    <span class="hrms-info-label">Location</span>
                    <span class="hrms-info-value">{{ selectedJob.location ?? EMPTY }}</span>
                  </div>
                  <div class="hrms-info-item">
                    <span class="hrms-info-label">Employment type</span>
                    <span class="hrms-info-value">{{ formatEnum(selectedJob.employment_type) }}</span>
                  </div>
                  <div class="hrms-info-item">
                    <span class="hrms-info-label">Work mode</span>
                    <span class="hrms-info-value">{{ formatEnum(selectedJob.work_mode) }}</span>
                  </div>
                  <div class="hrms-info-item">
                    <span class="hrms-info-label">Experience</span>
                    <span class="hrms-info-value">{{ experienceLabel(selectedJob) }}</span>
                  </div>
                  <div class="hrms-info-item">
                    <span class="hrms-info-label">Salary range</span>
                    <span class="hrms-info-value">{{ salaryRangeLabel(selectedJob) }}</span>
                  </div>
                  <div class="hrms-info-item">
                    <span class="hrms-info-label">Open positions</span>
                    <span class="hrms-info-value">
                      {{ selectedJob.open_positions != null ? selectedJob.open_positions : EMPTY }}
                    </span>
                  </div>
                  <div class="hrms-info-item">
                    <span class="hrms-info-label">Priority</span>
                    <span class="hrms-info-value">{{ formatEnum(selectedJob.priority) }}</span>
                  </div>
                </div>

                <div v-if="selectedJob.job_description" class="submissions-job-desc-block">
                  <span class="hrms-info-label">Job description</span>
                  <p class="hrms-info-value submissions-job-description">
                    {{ selectedJob.job_description }}
                  </p>
                </div>

                <div class="hrms-tabs" style="margin-top: 12px">
                  <button
                    type="button"
                    class="hrms-tab"
                    :class="{ 'hrms-tab--active': statusFilter === 'all' }"
                    @click="statusFilter = 'all'"
                  >
                    All
                  </button>
                  <button
                    type="button"
                    class="hrms-tab"
                    :class="{ 'hrms-tab--active': statusFilter === 'pending_review' }"
                    @click="statusFilter = 'pending_review'"
                  >
                    Pending
                  </button>
                  <button
                    type="button"
                    class="hrms-tab"
                    :class="{ 'hrms-tab--active': statusFilter === 'approved' }"
                    @click="statusFilter = 'approved'"
                  >
                    Approved
                  </button>
                  <button
                    type="button"
                    class="hrms-tab"
                    :class="{ 'hrms-tab--active': statusFilter === 'rejected' }"
                    @click="statusFilter = 'rejected'"
                  >
                    Rejected
                  </button>
                </div>
              </section>

              <div v-if="filteredSubmissions.length === 0" class="hrms-empty-inline">
                No candidates in this filter.
              </div>

              <button
                v-for="sub in filteredSubmissions"
                :key="sub.id"
                type="button"
                class="submissions-card submissions-card--clickable"
                @click="openCandidate(sub)"
              >
                <div class="submissions-card__top">
                  <div class="submissions-card__identity">
                    <div
                      class="hrms-avatar hrms-avatar--sm"
                      :style="`--hue: ${avatarHue(sub.candidate_id)}`"
                    >
                      {{
                        initials(
                          sub.candidate_name.split(' ')[0] ?? '',
                          sub.candidate_name.split(' ')[1] ?? '',
                        )
                      }}
                    </div>
                    <div>
                      <div class="submissions-card__name">{{ sub.candidate_name }}</div>
                      <div class="submissions-card__email">{{ sub.candidate_email }}</div>
                    </div>
                  </div>
                  <span class="hrms-status-badge" :style="`--sc: ${ownerStatusColor(sub.owner_status)}`">
                    {{ ownerStatusLabel(sub.owner_status) }}
                  </span>
                </div>

                <div class="hrms-info-grid" style="margin-top: 10px">
                  <div class="hrms-info-item">
                    <span class="hrms-info-label">Submitted by</span>
                    <span class="hrms-info-value">{{ sub.submitted_by_name ?? EMPTY }}</span>
                  </div>
                  <div class="hrms-info-item">
                    <span class="hrms-info-label">Submitted on</span>
                    <span class="hrms-info-value">{{ formatDate(sub.submitted_at) }}</span>
                  </div>
                  <div class="hrms-info-item">
                    <span class="hrms-info-label">Stage</span>
                    <span class="hrms-info-value">{{ sub.current_stage ?? EMPTY }}</span>
                  </div>
                </div>

                <div class="submissions-card__hint">View candidate details →</div>
              </button>
            </template>

            <div v-else class="hrms-empty-inline">No jobs for this client.</div>
          </div>
        </template>
      </div>
    </Transition>

    <HrmsModal
      v-model="showResumePreview"
      :title="
        candidateDetail
          ? `Resume — ${candidateDetail.first_name} ${candidateDetail.last_name}`
          : 'Resume preview'
      "
      size="xl"
    >
      <ResumePreview
        :src="previewResumeUrl"
        :loading="previewResumeLoading"
        :error="previewResumeError"
        :filename="
          candidateDetail
            ? `${candidateDetail.first_name}_${candidateDetail.last_name}_resume.pdf`
            : null
        "
        height="min(70vh, 760px)"
      />
      <template #footer>
        <button type="button" class="hrms-btn" @click="closeResumePreview">Close</button>
        <button
          type="button"
          class="hrms-btn hrms-btn--primary"
          :disabled="
            downloadingResume ||
            previewResumeLoading ||
            !!previewResumeError ||
            !previewResumeUrl
          "
          @click="handleDownloadResume"
        >
          {{ downloadingResume ? 'Downloading…' : 'Download' }}
        </button>
      </template>
    </HrmsModal>

    <HrmsModal v-model="showShareModal" title="Share approved profiles by email" size="md">
      <p class="hrms-page-subtitle" style="margin-bottom: 14px">
        Sends an Excel of approved candidate profiles to the client.
        <template v-if="!emailConfigured">
          SMTP is not configured — set <code>SMTP_HOST</code> / <code>SMTP_FROM</code> in
          <code>backend/.env</code>, or download Excel and email it yourself.
        </template>
        Leave recipients blank to use primary client contact emails.
      </p>
      <div class="hrms-form-stack">
        <label class="hrms-field">
          <span>Recipient emails</span>
          <input
            v-model="shareEmails"
            type="text"
            class="hrms-input"
            placeholder="hr@client.com, hiring@client.com"
          />
        </label>
        <label class="hrms-field">
          <span>Message (optional)</span>
          <textarea
            v-model="shareMessage"
            class="hrms-input"
            rows="4"
            placeholder="Please review and share shortlisted candidates…"
          />
        </label>
      </div>
      <template #footer>
        <button type="button" class="hrms-btn" @click="showShareModal = false">Cancel</button>
        <button
          type="button"
          class="hrms-btn hrms-btn--primary"
          :disabled="sharingEmail || !emailConfigured"
          @click="handleShareApproved"
        >
          {{ sharingEmail ? 'Sending…' : 'Send email' }}
        </button>
      </template>
    </HrmsModal>
  </div>
</template>

<style scoped>
.submissions-job-count {
  margin-left: 6px;
  opacity: 0.7;
  font-size: 0.75em;
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

.submissions-job-meta {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.submissions-job-desc-block {
  margin-top: 14px;
}

.submissions-job-description {
  white-space: pre-wrap;
  margin-top: 6px;
  line-height: 1.5;
  color: var(--hrms-text-secondary);
  font-size: 0.875rem;
}

.submissions-badges {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 8px;
}

.submissions-card {
  display: block;
  width: 100%;
  text-align: left;
  background: transparent;
  border: none;
  border-bottom: 1px solid var(--hrms-border);
  padding: 14px 0;
  color: inherit;
  font: inherit;
}

.submissions-card--clickable {
  cursor: pointer;
  border-radius: 8px;
  padding: 14px 10px;
  margin: 0 -10px;
  transition: background 0.12s;
}

.submissions-card--clickable:hover {
  background: var(--hrms-surface-alt, rgba(0, 0, 0, 0.03));
}

.submissions-card--clickable:focus-visible {
  outline: 2px solid var(--hrms-primary);
  outline-offset: 2px;
}

.submissions-card__top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.submissions-card__identity {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}

.submissions-card__name {
  font-weight: 600;
  font-size: 0.95rem;
}

.submissions-card__email {
  font-size: 0.8rem;
  color: var(--hrms-text-muted);
  margin-top: 2px;
}

.submissions-card__hint {
  margin-top: 10px;
  font-size: 0.75rem;
  color: var(--hrms-primary);
  font-weight: 500;
}

.hrms-btn--success {
  background: var(--hrms-success, #22c55e);
  color: #fff;
  border: none;
}

.hrms-btn--success:hover:not(:disabled) {
  opacity: 0.85;
}

.hrms-avatar--sm {
  width: 36px;
  height: 36px;
  font-size: 0.7rem;
  flex-shrink: 0;
}
</style>
