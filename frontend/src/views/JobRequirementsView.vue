<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { fetchClients } from '@/api/clients'
import {
  createJobRequirement,
  fetchJobRequirement,
  fetchJobRequirements,
  updateJobRequirement,
  updateJobRequirementStatus,
} from '@/api/jobRequirements'
import { fetchUsers } from '@/api/users'
import HrmsAlert from '@/components/ui/HrmsAlert.vue'
import HrmsModal from '@/components/ui/HrmsModal.vue'
import { useAuthStore } from '@/stores/auth'
import type { RecruiterListItem } from '@/types/auth'
import type { ClientListItem } from '@/types/clients'
import type {
  JobRequirementCreatePayload,
  JobRequirementListItem,
  JobRequirementStatus,
} from '@/types/jobRequirement'
import { EMPTY, orEmpty } from '@/utils/format'

const router = useRouter()

const auth = useAuthStore()
const isOwner = computed(() => auth.role === 'owner')

const requirements = ref<JobRequirementListItem[]>([])
const clients = ref<ClientListItem[]>([])
const recruiters = ref<RecruiterListItem[]>([])
const selected = ref<JobRequirementListItem | null>(null)
const loading = ref(true)
const saving = ref(false)
const error = ref('')
const success = ref('')
const showDialog = ref(false)
const editing = ref<JobRequirementListItem | null>(null)
const searchQuery = ref('')

type FormState = {
  client_id: string
  assigned_to: string
  job_title: string
  department: string
  employment_type: string
  work_mode: string
  experience_min: string
  salary_min: string
  salary_max: string
  open_positions: string
  job_description: string
  location: string
  priority: string
  requirement_type: string
}

const emptyForm = (): FormState => ({
  client_id: '',
  assigned_to: '',
  job_title: '',
  department: '',
  employment_type: '',
  work_mode: '',
  experience_min: '',
  salary_min: '',
  salary_max: '',
  open_positions: '',
  job_description: '',
  location: '',
  priority: '',
  requirement_type: '',
})

const form = ref<FormState>(emptyForm())

const filtered = computed(() => {
  const q = searchQuery.value.trim().toLowerCase()
  if (!q) return requirements.value
  return requirements.value.filter(
    (item) =>
      item.job_title.toLowerCase().includes(q) ||
      item.client_name.toLowerCase().includes(q) ||
      (item.assigned_recruiter_name ?? '').toLowerCase().includes(q) ||
      (item.location ?? '').toLowerCase().includes(q) ||
      item.status.toLowerCase().includes(q),
  )
})

const modalTitle = computed(() =>
  editing.value ? `Edit — ${editing.value.job_title}` : 'Post Job Requirement',
)

const activeRecruiters = computed(() =>
  recruiters.value.filter((user) => user.status === 'active' && user.role === 'recruiter'),
)

function toNumberOrNull(value: string | number | null | undefined): number | null {
  if (value == null || value === '') return null
  const trimmed = String(value).trim()
  if (!trimmed) return null
  const parsed = Number(trimmed)
  return Number.isFinite(parsed) ? parsed : null
}

function optionalText(value: string | number | null | undefined): string | null {
  const trimmed = String(value ?? '').trim()
  return trimmed || null
}

function toPayload(): JobRequirementCreatePayload {
  return {
    client_id: form.value.client_id,
    assigned_to: form.value.assigned_to,
    job_title: String(form.value.job_title ?? '').trim(),
    department: optionalText(form.value.department),
    employment_type: optionalText(form.value.employment_type),
    work_mode: optionalText(form.value.work_mode),
    experience_min: toNumberOrNull(form.value.experience_min),
    salary_min: toNumberOrNull(form.value.salary_min),
    salary_max: toNumberOrNull(form.value.salary_max),
    open_positions: toNumberOrNull(form.value.open_positions),
    job_description: optionalText(form.value.job_description),
    location: optionalText(form.value.location),
    priority: optionalText(form.value.priority),
    requirement_type: optionalText(form.value.requirement_type),
  }
}

function itemToForm(item: JobRequirementListItem): FormState {
  return {
    client_id: item.client_id,
    assigned_to: item.assigned_to ?? '',
    job_title: item.job_title,
    department: item.department ?? '',
    employment_type: item.employment_type ?? '',
    work_mode: item.work_mode ?? '',
    experience_min: item.experience_min != null ? String(item.experience_min) : '',
    salary_min: item.salary_min != null ? String(item.salary_min) : '',
    salary_max: item.salary_max != null ? String(item.salary_max) : '',
    open_positions: item.open_positions != null ? String(item.open_positions) : '',
    job_description: item.job_description ?? '',
    location: item.location ?? '',
    priority: item.priority ?? '',
    requirement_type: item.requirement_type ?? '',
  }
}

async function loadRequirements() {
  loading.value = true
  error.value = ''
  try {
    requirements.value = await fetchJobRequirements()
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Failed to load job requirements'
  } finally {
    loading.value = false
  }
}

async function loadOwnerOptions() {
  if (!isOwner.value) return
  const [clientList, userList] = await Promise.all([fetchClients(), fetchUsers()])
  clients.value = clientList.filter((c) => c.status === 'active')
  recruiters.value = userList
}

onMounted(async () => {
  await Promise.all([loadRequirements(), loadOwnerOptions().catch(() => undefined)])
})

async function selectRequirement(item: JobRequirementListItem) {
  try {
    selected.value = await fetchJobRequirement(item.id)
  } catch {
    selected.value = item
  }
}

function closePanel() {
  selected.value = null
}

function openCreate() {
  editing.value = null
  form.value = emptyForm()
  if (clients.value.length === 1) form.value.client_id = clients.value[0]!.id
  if (activeRecruiters.value.length === 1) form.value.assigned_to = activeRecruiters.value[0]!.id
  showDialog.value = true
}

function openEdit(item?: JobRequirementListItem) {
  const target = item ?? selected.value
  if (!target) return
  editing.value = target
  form.value = itemToForm(target)
  showDialog.value = true
}

async function submitRequirement() {
  if (!String(form.value.job_title ?? '').trim()) {
    error.value = 'Job title is required'
    return
  }
  if (!form.value.client_id) {
    error.value = 'Please select a client'
    return
  }
  if (!form.value.assigned_to) {
    error.value = 'Please assign a recruiter'
    return
  }

  saving.value = true
  error.value = ''
  success.value = ''
  try {
    const payload = toPayload()
    if (editing.value) {
      const updated = await updateJobRequirement(editing.value.id, payload)
      requirements.value = requirements.value.map((item) =>
        item.id === updated.id ? updated : item,
      )
      if (selected.value?.id === updated.id) selected.value = updated
      success.value = `${updated.job_title} updated`
    } else {
      const created = await createJobRequirement(payload)
      requirements.value = [created, ...requirements.value]
      success.value = `${created.job_title} posted`
    }
    showDialog.value = false
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Failed to save job requirement'
  } finally {
    saving.value = false
  }
}

async function setStatus(status: JobRequirementStatus) {
  if (!selected.value || !isOwner.value) return
  error.value = ''
  try {
    const updated = await updateJobRequirementStatus(selected.value.id, status)
    requirements.value = requirements.value.map((item) =>
      item.id === updated.id ? updated : item,
    )
    selected.value = updated
    success.value = `Status updated to ${status}`
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Failed to update status'
  }
}

function statusColor(status: string): string {
  if (status === 'open') return 'var(--hrms-success)'
  if (status === 'on_hold') return 'var(--hrms-warning, #d97706)'
  if (status === 'filled') return 'var(--hrms-primary)'
  return 'var(--hrms-text-muted)'
}

const formatDate = (d: string | null | undefined) =>
  d ? new Date(d).toLocaleDateString('en-IN') : EMPTY

function experienceLabel(item: JobRequirementListItem): string {
  if (item.experience_min == null && item.experience_max == null) return EMPTY
  if (item.experience_min != null && item.experience_max != null) {
    return `${item.experience_min}–${item.experience_max} yrs`
  }
  if (item.experience_min != null) return `${item.experience_min}+ yrs`
  return `Up to ${item.experience_max} yrs`
}
</script>

<template>
  <div class="hrms-split">
    <div class="hrms-split__main" :class="{ 'hrms-split__main--narrow': selected }">
      <div class="hrms-split__header">
        <div class="hrms-page-header hrms-page-header--compact">
          <div>
            <h1 class="hrms-page-title hrms-page-title--sm">Job Requirements</h1>
            <span class="hrms-page-count">
              {{ filtered.length }}
              {{ isOwner ? 'requirements' : 'assigned to you' }}
            </span>
          </div>
          <button
            v-if="isOwner"
            type="button"
            class="hrms-btn hrms-btn--primary"
            @click="openCreate"
          >
            Post Requirement
          </button>
        </div>

        <div class="hrms-controls">
          <input
            v-model="searchQuery"
            class="hrms-input hrms-search-input"
            type="search"
            placeholder="Search by title, client, recruiter…"
          />
        </div>
      </div>

      <HrmsAlert v-if="error" type="error" dismissible @dismiss="error = ''">{{ error }}</HrmsAlert>
      <HrmsAlert v-if="success" type="success" dismissible @dismiss="success = ''">{{ success }}</HrmsAlert>

      <div v-if="loading" class="hrms-loading">Loading job requirements…</div>

      <div v-else class="hrms-split__list hrms-scroll">
        <div
          v-for="item in filtered"
          :key="item.id"
          class="hrms-card hrms-card--interactive hrms-entity-card"
          :class="{ 'hrms-card--selected': selected?.id === item.id }"
          @click="selectRequirement(item)"
        >
          <div class="hrms-entity-card__body">
            <div class="hrms-entity-card__name-row">
              <span class="hrms-entity-card__name">{{ item.job_title }}</span>
              <span class="hrms-status-badge" :style="`--sc: ${statusColor(item.status)}`">
                {{ item.status }}
              </span>
            </div>
            <div class="hrms-entity-card__role">{{ item.client_name }}</div>
            <div class="hrms-entity-card__meta">
              <span v-if="item.assigned_recruiter_name">{{ item.assigned_recruiter_name }}</span>
              <span v-if="item.location">{{ item.location }}</span>
              <span v-if="item.priority">{{ item.priority }}</span>
            </div>
            <div class="job-pipeline-metrics">
              <span><strong>{{ item.pipeline_candidates }}</strong> in pipeline</span>
              <span><strong>{{ item.joined_candidates }}</strong> joined</span>
              <span>
                <strong>{{ item.remaining_positions ?? EMPTY }}</strong> remaining
              </span>
            </div>
            <button
              type="button"
              class="hrms-btn hrms-btn--sm hrms-btn--primary"
              style="margin-top: 10px"
              @click.stop="router.push({ name: 'job-requirement-detail', params: { id: item.id } })"
            >
              {{ item.submissions_enabled ? 'View / Submit Candidates' : 'View Candidates' }}
            </button>
          </div>
        </div>

        <div v-if="filtered.length === 0" class="hrms-empty">
          <p v-if="searchQuery">No job requirements match your search.</p>
          <p v-else-if="isOwner">No job requirements yet. Post your first requirement.</p>
          <p v-else>No job requirements assigned to you yet.</p>
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
            <div>
              <h2 class="hrms-panel-name">{{ selected.job_title }}</h2>
              <p class="hrms-panel-role">{{ selected.client_name }}</p>
              <span
                class="hrms-status-badge hrms-status-badge--lg"
                :style="`--sc: ${statusColor(selected.status)}`"
              >
                {{ selected.status }}
              </span>
            </div>
          </div>

          <div v-if="isOwner" class="hrms-actions hrms-actions--inline" style="padding-bottom: 16px">
            <button type="button" class="hrms-btn hrms-btn--primary hrms-btn--sm" @click="openEdit()">
              Edit
            </button>
            <button
              v-if="selected.status !== 'open'"
              type="button"
              class="hrms-btn hrms-btn--sm"
              @click="setStatus('open')"
            >
              Reopen
            </button>
            <button
              v-if="selected.status === 'open'"
              type="button"
              class="hrms-btn hrms-btn--sm"
              @click="setStatus('on_hold')"
            >
              Hold
            </button>
            <button
              v-if="selected.status !== 'closed'"
              type="button"
              class="hrms-btn hrms-btn--sm hrms-btn--danger"
              @click="setStatus('closed')"
            >
              Close
            </button>
          </div>
        </div>

        <div class="hrms-panel-body hrms-scroll">
          <section class="hrms-section">
            <h3 class="hrms-section-title">Details</h3>
            <div class="hrms-info-grid">
              <div class="hrms-info-item">
                <span class="hrms-info-label">Client</span>
                <span class="hrms-info-value">{{ selected.client_name }}</span>
              </div>
              <div class="hrms-info-item">
                <span class="hrms-info-label">Assigned recruiter</span>
                <span class="hrms-info-value">{{ orEmpty(selected.assigned_recruiter_name) }}</span>
              </div>
              <div class="hrms-info-item">
                <span class="hrms-info-label">Department</span>
                <span class="hrms-info-value">{{ orEmpty(selected.department) }}</span>
              </div>
              <div class="hrms-info-item">
                <span class="hrms-info-label">Employment type</span>
                <span class="hrms-info-value">{{ orEmpty(selected.employment_type) }}</span>
              </div>
              <div class="hrms-info-item">
                <span class="hrms-info-label">Work mode</span>
                <span class="hrms-info-value">{{ orEmpty(selected.work_mode) }}</span>
              </div>
              <div class="hrms-info-item">
                <span class="hrms-info-label">Location</span>
                <span class="hrms-info-value">{{ orEmpty(selected.location) }}</span>
              </div>
              <div class="hrms-info-item">
                <span class="hrms-info-label">Experience</span>
                <span class="hrms-info-value">{{ experienceLabel(selected) }}</span>
              </div>
              <div class="hrms-info-item">
                <span class="hrms-info-label">Open positions</span>
                <span class="hrms-info-value">{{ orEmpty(selected.open_positions?.toString()) }}</span>
              </div>
              <div class="hrms-info-item">
                <span class="hrms-info-label">Candidates in pipeline</span>
                <span class="hrms-info-value">{{ selected.pipeline_candidates }}</span>
              </div>
              <div class="hrms-info-item">
                <span class="hrms-info-label">Joined candidates</span>
                <span class="hrms-info-value">
                  {{ selected.joined_candidates }} / {{ selected.open_positions ?? EMPTY }}
                </span>
              </div>
              <div class="hrms-info-item">
                <span class="hrms-info-label">Positions remaining</span>
                <span class="hrms-info-value">{{ selected.remaining_positions ?? EMPTY }}</span>
              </div>
              <div class="hrms-info-item">
                <span class="hrms-info-label">Priority</span>
                <span class="hrms-info-value">{{ orEmpty(selected.priority) }}</span>
              </div>
              <div class="hrms-info-item">
                <span class="hrms-info-label">Created</span>
                <span class="hrms-info-value">{{ formatDate(selected.created_at) }}</span>
              </div>
            </div>
          </section>

          <section v-if="selected.job_description" class="hrms-section">
            <h3 class="hrms-section-title">Description</h3>
            <p class="hrms-info-value" style="white-space: pre-wrap">{{ selected.job_description }}</p>
          </section>
        </div>
      </div>
    </Transition>

    <HrmsModal v-if="isOwner" v-model="showDialog" :title="modalTitle" size="lg">
      <form id="job-requirement-form" class="hrms-form-grid" @submit.prevent="submitRequirement">
        <label class="hrms-field hrms-field--wide">
          <span class="hrms-label">Job title *</span>
          <input v-model="form.job_title" class="hrms-input" type="text" required />
        </label>
        <label class="hrms-field">
          <span class="hrms-label">Client *</span>
          <select v-model="form.client_id" class="hrms-input hrms-select" required>
            <option value="" disabled>Select client</option>
            <option v-for="client in clients" :key="client.id" :value="client.id">
              {{ client.company_name }}
            </option>
          </select>
        </label>
        <label class="hrms-field">
          <span class="hrms-label">Assign recruiter *</span>
          <select v-model="form.assigned_to" class="hrms-input hrms-select" required>
            <option value="" disabled>Select recruiter</option>
            <option v-for="user in activeRecruiters" :key="user.id" :value="user.id">
              {{ user.first_name }} {{ user.last_name }}
            </option>
          </select>
        </label>
        <label class="hrms-field">
          <span class="hrms-label">Department</span>
          <input v-model="form.department" class="hrms-input" type="text" />
        </label>
        <label class="hrms-field">
          <span class="hrms-label">Location</span>
          <input v-model="form.location" class="hrms-input" type="text" />
        </label>
        <label class="hrms-field">
          <span class="hrms-label">Employment type</span>
          <select v-model="form.employment_type" class="hrms-input hrms-select">
            <option value="">Select</option>
            <option value="full_time">Full time</option>
            <option value="contract">Contract</option>
            <option value="part_time">Part time</option>
          </select>
        </label>
        <label class="hrms-field">
          <span class="hrms-label">Work mode</span>
          <select v-model="form.work_mode" class="hrms-input hrms-select">
            <option value="">Select</option>
            <option value="onsite">Onsite</option>
            <option value="hybrid">Hybrid</option>
            <option value="remote">Remote</option>
          </select>
        </label>
        <label class="hrms-field">
          <span class="hrms-label">Experience min (yrs)</span>
          <input v-model="form.experience_min" class="hrms-input" type="number" min="0" step="0.5" />
        </label>
        <label class="hrms-field">
          <span class="hrms-label">Open positions</span>
          <input v-model="form.open_positions" class="hrms-input" type="number" min="1" step="1" />
        </label>
        <label class="hrms-field">
          <span class="hrms-label">Priority</span>
          <select v-model="form.priority" class="hrms-input hrms-select">
            <option value="">Select</option>
            <option value="high">High</option>
            <option value="medium">Medium</option>
            <option value="low">Low</option>
          </select>
        </label>
        <label class="hrms-field hrms-field--wide">
          <span class="hrms-label">Job description</span>
          <textarea v-model="form.job_description" class="hrms-input hrms-textarea" rows="4" />
        </label>
      </form>

      <template #footer>
        <button type="button" class="hrms-btn" @click="showDialog = false">Cancel</button>
        <button
          type="submit"
          form="job-requirement-form"
          class="hrms-btn hrms-btn--primary"
          :disabled="saving"
        >
          {{ saving ? 'Saving…' : editing ? 'Save Changes' : 'Post' }}
        </button>
      </template>
    </HrmsModal>
  </div>
</template>

<style scoped>
.job-pipeline-metrics {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 10px;
}

.job-pipeline-metrics span {
  padding: 4px 8px;
  border: 1px solid var(--hrms-border);
  border-radius: 999px;
  font-size: 0.72rem;
  color: var(--hrms-text-muted);
  background: var(--hrms-surface-muted);
}

.job-pipeline-metrics strong {
  color: var(--hrms-text);
}
</style>
