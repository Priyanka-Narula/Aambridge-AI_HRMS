<script setup lang="ts">
import { computed, nextTick, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { fetchCandidates } from '@/api/candidates'
import { fetchJobRequirement } from '@/api/jobRequirements'
import { downloadAllSubmissions, fetchSubmissions, submitCandidate } from '@/api/submissions'
import HrmsAlert from '@/components/ui/HrmsAlert.vue'
import HrmsModal from '@/components/ui/HrmsModal.vue'
import { useAuthStore } from '@/stores/auth'
import type { Candidate } from '@/types/candidate'
import type { CandidateSubmission, JobRequirementListItem, SubmissionField } from '@/types/jobRequirement'
import { EMPTY, orEmpty } from '@/utils/format'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const isOwner = computed(() => auth.role === 'owner')
const jobId = computed(() => route.params.id as string)

const job = ref<JobRequirementListItem | null>(null)
const submissions = ref<CandidateSubmission[]>([])
const allCandidates = ref<Candidate[]>([])
const loading = ref(true)
const loadingSubmissions = ref(false)
const error = ref('')
const success = ref('')
const activeTab = ref<'details' | 'submissions'>('details')

// ── Submit modal state ─────────────────────────────────────────────────────
const showSubmitModal = ref(false)
// Step 1: pick candidate | Step 2: fill verification form
type SubmitStep = 'pick' | 'form'
const submitStep = ref<SubmitStep>('pick')
const candidateSearch = ref('')
const selectedCandidate = ref<Candidate | null>(null)
const submitting = ref(false)
const submitError = ref('')
// Template ref for the modal body element (used to scroll to top on step change)
const modalBodyRef = ref<HTMLElement | null>(null)
const downloadingAll = ref(false)

// Submission form values keyed by field label
const formValues = ref<Record<string, string>>({})

// ── Candidate field pre-fill mapping ──────────────────────────────────────
// Keys are common field labels that owners might enter, values are Candidate attr names.
// Case-insensitive lookup is used at pre-fill time.
const LABEL_TO_ATTR: Record<string, keyof Candidate> = {
  'first name': 'first_name',
  'last name': 'last_name',
  'email': 'email',
  'email address': 'email',
  'phone': 'phone',
  'phone number': 'phone',
  'mobile': 'phone',
  'nationality': 'nationality',
  'date of birth': 'date_of_birth',
  'dob': 'date_of_birth',
  'languages': 'languages_known',
  'languages known': 'languages_known',
  'visa status': 'visa_status',
  'visa': 'visa_status',
  'linkedin': 'linkedin_url',
  'linkedin url': 'linkedin_url',
  'current location': 'current_location',
  'location': 'current_location',
  'preferred location': 'preferred_location',
  'total experience': 'total_experience_years',
  'total experience (years)': 'total_experience_years',
  'experience': 'total_experience_years',
  'years of experience': 'total_experience_years',
  'uae experience': 'uae_experience_years',
  'uae experience (years)': 'uae_experience_years',
  'current company': 'current_company',
  'company': 'current_company',
  'current designation': 'current_designation',
  'designation': 'current_designation',
  'current title': 'current_designation',
  'current ctc': 'current_ctc',
  'current salary': 'current_ctc',
  'expected ctc': 'expected_ctc',
  'expected salary': 'expected_ctc',
  'notice period': 'notice_period',
  'industry': 'industry',
  'resume / cv': 'resume_url',
  'resume': 'resume_url',
  'cv': 'resume_url',
  'resume url': 'resume_url',
}

// Fields that aggregate related data for display in the form
const COMPOSITE_FIELDS: Record<string, (c: Candidate) => string> = {
  'education details': (c) =>
    c.education_records
      .map((e) => `${e.degree}${e.specialization ? ` (${e.specialization})` : ''} — ${e.institution ?? ''}`)
      .join('; ') || '',
  'education': (c) =>
    c.education_records
      .map((e) => `${e.degree} — ${e.institution ?? ''}`)
      .join('; ') || '',
  'work experience': (c) =>
    c.work_experiences
      .map((w) => `${w.designation ?? ''} at ${w.company_name}`)
      .join('; ') || '',
  'experience details': (c) =>
    c.work_experiences
      .map((w) => `${w.designation ?? ''} at ${w.company_name}`)
      .join('; ') || '',
}

function preFillFromCandidate(candidate: Candidate, fields: SubmissionField[]): Record<string, string> {
  const result: Record<string, string> = {}
  for (const f of fields) {
    const labelLower = f.field.toLowerCase()
    // Try composite builders first
    const composite = COMPOSITE_FIELDS[labelLower]
    if (composite) {
      result[f.field] = composite(candidate)
      continue
    }
    // Try direct attribute mapping
    const attr = LABEL_TO_ATTR[labelLower]
    if (attr) {
      const val = candidate[attr]
      result[f.field] = val != null ? String(val) : ''
    } else {
      result[f.field] = ''
    }
  }
  return result
}

// ── Computed ───────────────────────────────────────────────────────────────
const clientFields = computed<SubmissionField[]>(() => job.value?.client_submission_format ?? [])
const requiredFields = computed(() => clientFields.value.filter((f) => f.required))
const hasSubmissionTemplate = computed(() => clientFields.value.length > 0)

const filteredCandidates = computed(() => {
  const q = candidateSearch.value.trim().toLowerCase()
  if (!q) return allCandidates.value.slice(0, 20)
  return allCandidates.value
    .filter(
      (c) =>
        `${c.first_name} ${c.last_name}`.toLowerCase().includes(q) ||
        c.email.toLowerCase().includes(q) ||
        (c.current_company ?? '').toLowerCase().includes(q),
    )
    .slice(0, 20)
})

const missingRequired = computed(() =>
  requiredFields.value.filter((f) => {
    const v = formValues.value[f.field]
    return !v || !v.trim()
  }),
)

const canSubmit = computed(() => missingRequired.value.length === 0)

// ── Load ───────────────────────────────────────────────────────────────────
async function load() {
  loading.value = true
  error.value = ''
  try {
    const [jobData, subData] = await Promise.all([
      fetchJobRequirement(jobId.value),
      fetchSubmissions(jobId.value),
    ])
    job.value = jobData
    submissions.value = subData
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Failed to load job requirement'
  } finally {
    loading.value = false
  }
}

async function loadCandidates() {
  try {
    allCandidates.value = await fetchCandidates()
  } catch {
    /* non-critical */
  }
}

onMounted(() => Promise.all([load(), loadCandidates()]))

async function refreshSubmissions() {
  loadingSubmissions.value = true
  try {
    submissions.value = await fetchSubmissions(jobId.value)
  } finally {
    loadingSubmissions.value = false
  }
}

// ── Modal flow ─────────────────────────────────────────────────────────────
function openSubmitModal() {
  selectedCandidate.value = null
  candidateSearch.value = ''
  submitError.value = ''
  formValues.value = {}
  submitStep.value = 'pick'
  showSubmitModal.value = true
  // Refresh the candidate list so pre-fill always uses the latest profile data
  loadCandidates()
}

function pickCandidate(c: Candidate) {
  selectedCandidate.value = c
  // Pre-fill form from candidate data
  formValues.value = preFillFromCandidate(c, clientFields.value)
  // If client has no template, skip straight to submit (no form needed)
  if (!hasSubmissionTemplate.value) {
    doSubmit()
    return
  }
  submitStep.value = 'form'
  submitError.value = ''
  // Scroll modal body to top so the missing-fields warning is immediately visible
  nextTick(() => {
    const parent = modalBodyRef.value?.parentElement
    if (parent) parent.scrollTop = 0
  })
}

function backToPick() {
  submitStep.value = 'pick'
  selectedCandidate.value = null
  candidateSearch.value = ''
  submitError.value = ''
}

async function doSubmit() {
  if (!selectedCandidate.value) return
  // If there are still empty required fields, scroll the first one into view
  if (missingRequired.value.length > 0) {
    const firstMissing = missingRequired.value[0]
    const el = modalBodyRef.value?.querySelector<HTMLElement>(
      `[data-field="${CSS.escape(firstMissing.field)}"]`,
    )
    el?.scrollIntoView({ behavior: 'smooth', block: 'center' })
    el?.focus()
    return
  }
  submitting.value = true
  submitError.value = ''
  try {
    const sub = await submitCandidate(
      jobId.value,
      selectedCandidate.value.id,
      formValues.value,
    )
    submissions.value = [sub, ...submissions.value]
    showSubmitModal.value = false
    success.value = `${selectedCandidate.value.first_name} ${selectedCandidate.value.last_name} submitted successfully`
    activeTab.value = 'submissions'
  } catch (err) {
    submitError.value = err instanceof Error ? err.message : 'Submission failed'
  } finally {
    submitting.value = false
  }
}

async function handleDownloadAll() {
  downloadingAll.value = true
  error.value = ''
  try {
    const clientName = (job.value?.client_name ?? 'Client').replace(/\s+/g, '_')
    const jobTitle = (job.value?.job_title ?? 'Job').replace(/\s+/g, '_')
    await downloadAllSubmissions(jobId.value, `${clientName}_${jobTitle}_candidates.xlsx`)
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Download failed'
  } finally {
    downloadingAll.value = false
  }
}

// ── Utilities ──────────────────────────────────────────────────────────────
const statusColor = (s: string) => {
  if (s === 'open') return 'var(--hrms-success)'
  if (s === 'on_hold') return 'var(--hrms-warning, #d97706)'
  if (s === 'filled') return 'var(--hrms-primary)'
  return 'var(--hrms-text-muted)'
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

const formatDate = (d: string | null | undefined) =>
  d
    ? new Date(d).toLocaleDateString('en-IN', {
        day: '2-digit',
        month: 'short',
        year: 'numeric',
      })
    : EMPTY

const experienceLabel = (item: JobRequirementListItem) => {
  if (item.experience_min == null && item.experience_max == null) return EMPTY
  if (item.experience_min != null && item.experience_max != null)
    return `${item.experience_min}–${item.experience_max} yrs`
  if (item.experience_min != null) return `${item.experience_min}+ yrs`
  return `Up to ${item.experience_max} yrs`
}

const fieldInputType = (f: SubmissionField): string => {
  const t = (f.type || '').toLowerCase()
  if (t === 'date') return 'date'
  if (t === 'email') return 'email'
  // number/numeric → text so browsers don't silently discard non-numeric chars
  // (e.g. "80,000 AED", "negotiable") which would make v-model write back ""
  return 'text'
}

const fieldInputMode = (f: SubmissionField): string | undefined => {
  const t = (f.type || '').toLowerCase()
  return t === 'number' || t === 'numeric' ? 'decimal' : undefined
}

const isLongText = (f: SubmissionField): boolean => {
  const label = f.field.toLowerCase()
  return (
    label.includes('experience') ||
    label.includes('education') ||
    label.includes('description') ||
    label.includes('notes') ||
    label.includes('comments') ||
    (f.type || '').toLowerCase() === 'textarea'
  )
}
</script>

<template>
  <div class="jrd-page">
    <div class="jrd-topbar">
      <button class="hrms-btn hrms-btn--sm" @click="router.back()">← Back</button>
      <span class="jrd-breadcrumb">Job Requirements / Detail</span>
    </div>

    <HrmsAlert v-if="error" type="error" dismissible @dismiss="error = ''">{{ error }}</HrmsAlert>
    <HrmsAlert v-if="success" type="success" dismissible @dismiss="success = ''">{{ success }}</HrmsAlert>

    <div v-if="loading" class="hrms-loading">Loading…</div>

    <template v-else-if="job">
      <!-- Hero -->
      <div class="jrd-hero hrms-card">
        <div class="jrd-hero__left">
          <h1 class="jrd-hero__title">{{ job.job_title }}</h1>
          <p class="jrd-hero__client">{{ job.client_name }}</p>
          <div class="jrd-hero__badges">
            <span
              class="hrms-status-badge hrms-status-badge--lg"
              :style="`--sc: ${statusColor(job.status)}`"
            >
              {{ job.status }}
            </span>
            <span v-if="job.priority" class="hrms-status-badge" style="--sc: var(--hrms-text-muted)">
              {{ job.priority }}
            </span>
          </div>
        </div>
        <div class="jrd-hero__actions">
          <button type="button" class="hrms-btn hrms-btn--primary" @click="openSubmitModal">
            Submit Candidate
          </button>
        </div>
      </div>

      <!-- Tabs -->
      <div class="jrd-tabs">
        <button
          class="jrd-tab"
          :class="{ 'jrd-tab--active': activeTab === 'details' }"
          @click="activeTab = 'details'"
        >
          Details
        </button>
        <button
          class="jrd-tab"
          :class="{ 'jrd-tab--active': activeTab === 'submissions' }"
          @click="activeTab = 'submissions'; refreshSubmissions()"
        >
          Submitted Candidates
          <span class="jrd-tab__count">{{ submissions.length }}</span>
        </button>
      </div>

      <!-- Details tab -->
      <div v-if="activeTab === 'details'" class="hrms-card jrd-section">
        <div class="hrms-info-grid">
          <div class="hrms-info-item">
            <span class="hrms-info-label">Client</span>
            <span class="hrms-info-value">{{ job.client_name }}</span>
          </div>
          <div class="hrms-info-item">
            <span class="hrms-info-label">Assigned Recruiter</span>
            <span class="hrms-info-value">{{ orEmpty(job.assigned_recruiter_name) }}</span>
          </div>
          <div class="hrms-info-item">
            <span class="hrms-info-label">Department</span>
            <span class="hrms-info-value">{{ orEmpty(job.department) }}</span>
          </div>
          <div class="hrms-info-item">
            <span class="hrms-info-label">Location</span>
            <span class="hrms-info-value">{{ orEmpty(job.location) }}</span>
          </div>
          <div class="hrms-info-item">
            <span class="hrms-info-label">Employment Type</span>
            <span class="hrms-info-value">{{ orEmpty(job.employment_type) }}</span>
          </div>
          <div class="hrms-info-item">
            <span class="hrms-info-label">Work Mode</span>
            <span class="hrms-info-value">{{ orEmpty(job.work_mode) }}</span>
          </div>
          <div class="hrms-info-item">
            <span class="hrms-info-label">Experience</span>
            <span class="hrms-info-value">{{ experienceLabel(job) }}</span>
          </div>
          <div class="hrms-info-item">
            <span class="hrms-info-label">Open Positions</span>
            <span class="hrms-info-value">{{ orEmpty(job.open_positions?.toString()) }}</span>
          </div>
          <div class="hrms-info-item">
            <span class="hrms-info-label">Priority</span>
            <span class="hrms-info-value">{{ orEmpty(job.priority) }}</span>
          </div>
          <div class="hrms-info-item">
            <span class="hrms-info-label">Created</span>
            <span class="hrms-info-value">{{ formatDate(job.created_at) }}</span>
          </div>
        </div>
        <div v-if="job.job_description" class="jrd-desc">
          <p class="hrms-info-label">Description</p>
          <p class="hrms-info-value" style="white-space: pre-wrap; margin-top: 6px">
            {{ job.job_description }}
          </p>
        </div>

        <!-- Client submission template info -->
        <div v-if="hasSubmissionTemplate" class="jrd-template-info">
          <p class="hrms-info-label" style="margin-bottom: 8px">
            Client Submission Template
            <span class="jrd-template-tag">{{ clientFields.length }} fields</span>
          </p>
          <div class="jrd-template-fields">
            <span
              v-for="f in clientFields"
              :key="f.field"
              class="jrd-template-field"
              :class="{ 'jrd-template-field--required': f.required }"
            >
              {{ f.field }}<span v-if="f.required" class="jrd-required-star">*</span>
            </span>
          </div>
        </div>
      </div>

      <!-- Submissions tab -->
      <div v-if="activeTab === 'submissions'" class="hrms-card jrd-section">
        <!-- Download all button — owner only, only when there are submissions -->
        <div v-if="isOwner && submissions.length > 0" class="jrd-submissions-header">
          <button
            class="hrms-btn hrms-btn--sm hrms-btn--primary"
            :disabled="downloadingAll"
            @click="handleDownloadAll"
          >
            {{ downloadingAll ? 'Downloading…' : `Download All (${submissions.length})` }}
          </button>
        </div>

        <div v-if="loadingSubmissions" class="hrms-loading">Loading submissions…</div>
        <div v-else-if="submissions.length === 0" class="hrms-empty">
          <p>No candidates submitted yet.</p>
        </div>
        <table v-else class="jrd-table">
          <thead>
            <tr>
              <th>Candidate</th>
              <th>Email</th>
              <th>Stage</th>
              <th>Submitted By</th>
              <th>Submitted On</th>
              <th>Owner Status</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="sub in submissions" :key="sub.id">
              <td class="jrd-table__name">{{ sub.candidate_name }}</td>
              <td>{{ sub.candidate_email }}</td>
              <td>{{ sub.current_stage ?? EMPTY }}</td>
              <td>{{ sub.submitted_by_name ?? EMPTY }}</td>
              <td>{{ formatDate(sub.submitted_at) }}</td>
              <td>
                <span
                  class="hrms-status-badge"
                  :style="`--sc: ${ownerStatusColor(sub.owner_status)}`"
                >
                  {{ ownerStatusLabel(sub.owner_status) }}
                </span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </template>

    <!-- ── Submit Candidate Modal ──────────────────────────────────────────── -->
    <HrmsModal
      v-model="showSubmitModal"
      :title="submitStep === 'pick' ? 'Submit Candidate — Select' : `Submission Form — ${selectedCandidate?.first_name} ${selectedCandidate?.last_name}`"
      size="lg"
    >
      <!-- Step 1: Pick candidate -->
      <div v-if="submitStep === 'pick'" class="jrd-submit-step">
        <p class="jrd-step-hint">
          Search by name, email or company. After selecting, you will fill in the client's
          required submission fields.
        </p>

        <HrmsAlert v-if="submitError" type="error" dismissible @dismiss="submitError = ''">
          {{ submitError }}
        </HrmsAlert>

        <label class="hrms-field hrms-field--wide">
          <span class="hrms-label">Search Candidate</span>
          <input
            v-model="candidateSearch"
            class="hrms-input"
            type="text"
            placeholder="Name, email or company…"
            autofocus
          />
        </label>

        <div v-if="filteredCandidates.length > 0" class="jrd-candidate-list">
          <div
            v-for="c in filteredCandidates"
            :key="c.id"
            class="jrd-candidate-item"
            @click="pickCandidate(c)"
          >
            <div class="jrd-candidate-item__name">{{ c.first_name }} {{ c.last_name }}</div>
            <div class="jrd-candidate-item__meta">
              {{ c.email }}
              <span v-if="c.current_company"> · {{ c.current_company }}</span>
              <span v-if="c.current_designation"> · {{ c.current_designation }}</span>
              <span v-if="c.total_experience_years"> · {{ c.total_experience_years }} yrs exp</span>
            </div>
          </div>
        </div>
        <p v-else-if="candidateSearch" class="jrd-no-results">No candidates match your search.</p>
        <p v-else class="jrd-no-results">Start typing to search candidates…</p>
      </div>

      <!-- Step 2: Verification form -->
      <div v-else-if="submitStep === 'form'" ref="modalBodyRef" class="jrd-submit-step">
        <!-- Candidate summary card -->
        <div class="jrd-selected-banner">
          <div>
            <div class="jrd-selected-banner__name">
              {{ selectedCandidate?.first_name }} {{ selectedCandidate?.last_name }}
            </div>
            <div class="jrd-selected-banner__meta">
              {{ selectedCandidate?.email }}
              <span v-if="selectedCandidate?.current_company">
                · {{ selectedCandidate.current_company }}
              </span>
            </div>
          </div>
          <button class="hrms-btn hrms-btn--sm" @click="backToPick">Change</button>
        </div>

        <HrmsAlert v-if="submitError" type="error" dismissible @dismiss="submitError = ''">
          {{ submitError }}
        </HrmsAlert>

        <!-- Missing required fields warning -->
        <div v-if="missingRequired.length > 0" class="jrd-missing-warning">
          <strong>{{ missingRequired.length }} required field{{ missingRequired.length > 1 ? 's' : '' }} still empty:</strong>
          {{ missingRequired.map((f) => f.field).join(', ') }}
        </div>

        <!-- Applied-for job title — non-editable -->
        <div class="jrd-applied-for">
          <span class="hrms-label">Applied For</span>
          <span class="jrd-applied-for__value">{{ job?.job_title }}</span>
        </div>

        <p class="jrd-step-hint">
          Fields marked <span class="jrd-required-star">*</span> are required by
          <strong>{{ job?.client_name }}</strong>. Pre-filled values from the candidate profile
          — review and correct if needed.
        </p>

        <div class="jrd-form-grid">
          <div
            v-for="f in clientFields"
            :key="f.field"
            class="jrd-form-field"
            :class="{ 'jrd-form-field--wide': isLongText(f) }"
          >
            <label class="hrms-label">
              {{ f.field }}
              <span v-if="f.required" class="jrd-required-star">*</span>
            </label>
            <textarea
              v-if="isLongText(f)"
              v-model="formValues[f.field]"
              class="hrms-input hrms-textarea"
              rows="3"
              :data-field="f.field"
              :placeholder="f.required ? 'Required' : 'Optional'"
              :class="{ 'jrd-input--missing': f.required && !formValues[f.field]?.trim() }"
            />
            <input
              v-else
              v-model="formValues[f.field]"
              class="hrms-input"
              :type="fieldInputType(f)"
              :inputmode="fieldInputMode(f)"
              :data-field="f.field"
              :placeholder="f.required ? 'Required' : 'Optional'"
              :class="{ 'jrd-input--missing': f.required && !formValues[f.field]?.trim() }"
            />
          </div>
        </div>
      </div>

      <template #footer>
        <template v-if="submitStep === 'pick'">
          <button type="button" class="hrms-btn" @click="showSubmitModal = false">Cancel</button>
        </template>
        <template v-else>
          <button type="button" class="hrms-btn" @click="backToPick">← Back</button>
          <div style="display: flex; align-items: center; gap: 8px; margin-left: auto">
            <span v-if="missingRequired.length > 0" class="jrd-footer-warn">
              {{ missingRequired.length }} required field{{ missingRequired.length > 1 ? 's' : '' }} missing
            </span>
            <button
              type="button"
              class="hrms-btn hrms-btn--primary"
              :disabled="submitting"
              @click="doSubmit"
            >
              {{ submitting ? 'Submitting…' : 'Submit Candidate' }}
            </button>
          </div>
        </template>
      </template>
    </HrmsModal>
  </div>
</template>

<style scoped>
.jrd-page {
  padding: 24px;
  max-width: 960px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.jrd-topbar {
  display: flex;
  align-items: center;
  gap: 12px;
}

.jrd-breadcrumb {
  font-size: 0.85rem;
  color: var(--hrms-text-muted);
}

.jrd-hero {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  padding: 20px 24px;
}

.jrd-hero__title {
  font-size: 1.4rem;
  font-weight: 700;
  margin: 0 0 4px;
}

.jrd-hero__client {
  font-size: 0.95rem;
  color: var(--hrms-text-muted);
  margin: 0 0 10px;
}

.jrd-hero__badges {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.jrd-tabs {
  display: flex;
  gap: 4px;
  border-bottom: 1px solid var(--hrms-border);
}

.jrd-tab {
  padding: 10px 18px;
  background: none;
  border: none;
  border-bottom: 2px solid transparent;
  cursor: pointer;
  color: var(--hrms-text-muted);
  font-size: 0.9rem;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 6px;
  transition: color 0.15s, border-color 0.15s;
}

.jrd-tab--active {
  color: var(--hrms-primary);
  border-bottom-color: var(--hrms-primary);
}

.jrd-tab__count {
  background: var(--hrms-surface-alt, rgba(255, 255, 255, 0.08));
  border-radius: 10px;
  padding: 1px 7px;
  font-size: 0.78rem;
}

.jrd-section {
  padding: 20px 24px;
}

.jrd-desc {
  margin-top: 20px;
  padding-top: 16px;
  border-top: 1px solid var(--hrms-border);
}

.jrd-template-info {
  margin-top: 20px;
  padding-top: 16px;
  border-top: 1px solid var(--hrms-border);
}

.jrd-template-tag {
  background: var(--hrms-primary);
  color: #fff;
  font-size: 0.72rem;
  border-radius: 10px;
  padding: 1px 8px;
  margin-left: 8px;
  font-weight: 600;
}

.jrd-template-fields {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 6px;
}

.jrd-template-field {
  background: var(--hrms-surface-alt, rgba(255, 255, 255, 0.06));
  border: 1px solid var(--hrms-border);
  border-radius: 6px;
  padding: 3px 10px;
  font-size: 0.8rem;
}

.jrd-template-field--required {
  border-color: rgba(239, 68, 68, 0.4);
}

.jrd-required-star {
  color: #ef4444;
  margin-left: 2px;
  font-weight: 700;
}

/* Submissions table */
.jrd-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.875rem;
}

.jrd-table th {
  text-align: left;
  padding: 8px 12px;
  border-bottom: 1px solid var(--hrms-border);
  color: var(--hrms-text-muted);
  font-weight: 600;
  font-size: 0.78rem;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.jrd-table td {
  padding: 10px 12px;
  border-bottom: 1px solid var(--hrms-border);
  vertical-align: middle;
}

.jrd-table tbody tr:last-child td {
  border-bottom: none;
}

.jrd-table__name {
  font-weight: 600;
}

/* Modal steps */
.jrd-submit-step {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.jrd-step-hint {
  font-size: 0.85rem;
  color: var(--hrms-text-muted);
  margin: 0;
  line-height: 1.5;
}

/* Candidate list */
.jrd-candidate-list {
  border: 1px solid var(--hrms-border);
  border-radius: 8px;
  max-height: 280px;
  overflow-y: auto;
}

.jrd-candidate-item {
  padding: 10px 14px;
  cursor: pointer;
  transition: background 0.12s;
}

.jrd-candidate-item:not(:last-child) {
  border-bottom: 1px solid var(--hrms-border);
}

.jrd-candidate-item:hover {
  background: var(--hrms-surface-alt, rgba(255, 255, 255, 0.05));
}

.jrd-candidate-item__name {
  font-weight: 600;
  font-size: 0.9rem;
}

.jrd-candidate-item__meta {
  font-size: 0.8rem;
  color: var(--hrms-text-muted);
  margin-top: 2px;
}

.jrd-no-results {
  font-size: 0.85rem;
  color: var(--hrms-text-muted);
  margin: 0;
  padding: 8px 0;
}

/* Selected candidate banner */
.jrd-selected-banner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: rgba(124, 58, 237, 0.1);
  border: 1px solid rgba(124, 58, 237, 0.35);
  border-radius: 8px;
  padding: 12px 16px;
}

.jrd-selected-banner__name {
  font-weight: 700;
  font-size: 0.95rem;
}

.jrd-selected-banner__meta {
  font-size: 0.82rem;
  color: var(--hrms-text-muted);
  margin-top: 2px;
}

/* Missing warning */
.jrd-missing-warning {
  background: rgba(239, 68, 68, 0.08);
  border: 1px solid rgba(239, 68, 68, 0.3);
  border-radius: 6px;
  padding: 10px 14px;
  font-size: 0.84rem;
  color: #fca5a5;
  line-height: 1.5;
}

/* Applied-for job title banner */
.jrd-applied-for {
  display: flex;
  align-items: center;
  gap: 10px;
  background: rgba(124, 58, 237, 0.06);
  border: 1px solid rgba(124, 58, 237, 0.2);
  border-radius: 6px;
  padding: 10px 14px;
}

.jrd-applied-for .hrms-label {
  margin-bottom: 0;
  white-space: nowrap;
  flex-shrink: 0;
}

.jrd-applied-for__value {
  font-weight: 600;
  font-size: 0.9rem;
  color: var(--hrms-text);
}

/* Verification form grid */
.jrd-form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.jrd-form-field {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.jrd-form-field--wide {
  grid-column: 1 / -1;
}

.jrd-input--missing {
  border-color: rgba(239, 68, 68, 0.6) !important;
}

.jrd-footer-warn {
  font-size: 0.82rem;
  color: #fca5a5;
}

.jrd-submissions-header {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 12px;
}
</style>
