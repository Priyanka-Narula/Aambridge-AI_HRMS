<script setup lang="ts">
import { onMounted, ref } from 'vue'
import {
  approveSubmission,
  downloadApprovedClientSubmissions,
  downloadSubmission,
  fetchOwnerDashboard,
} from '@/api/submissions'
import HrmsAlert from '@/components/ui/HrmsAlert.vue'
import type { CandidateSubmission, OwnerDashboardClient } from '@/types/jobRequirement'
import { EMPTY } from '@/utils/format'

const dashboard = ref<OwnerDashboardClient[]>([])
const loading = ref(true)
const error = ref('')
const success = ref('')
const actioning = ref<string | null>(null)
const downloadingClient = ref<string | null>(null)
const expandedClients = ref<Set<string>>(new Set())
const expandedJobs = ref<Set<string>>(new Set())

async function load() {
  loading.value = true
  error.value = ''
  try {
    dashboard.value = await fetchOwnerDashboard()
    // Auto-expand all by default
    for (const client of dashboard.value) {
      expandedClients.value.add(client.client_id)
      for (const job of client.jobs) {
        expandedJobs.value.add(job.job_requirement_id)
      }
    }
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Failed to load dashboard'
  } finally {
    loading.value = false
  }
}

onMounted(load)

function toggleClient(clientId: string) {
  if (expandedClients.value.has(clientId)) {
    expandedClients.value.delete(clientId)
  } else {
    expandedClients.value.add(clientId)
  }
}

function toggleJob(jobId: string) {
  if (expandedJobs.value.has(jobId)) {
    expandedJobs.value.delete(jobId)
  } else {
    expandedJobs.value.add(jobId)
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
  try {
    const filename = `${sub.candidate_name.replace(/\s+/g, '_')}_${sub.client_name.replace(/\s+/g, '_')}_profile.xlsx`
    await downloadSubmission(sub.id, filename)
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Download failed'
  } finally {
    actioning.value = null
  }
}

function patchSubmission(updated: CandidateSubmission) {
  for (const client of dashboard.value) {
    for (const job of client.jobs) {
      const idx = job.submissions.findIndex((s) => s.id === updated.id)
      if (idx !== -1) {
        job.submissions[idx] = updated
        return
      }
    }
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

const totalSubmissions = (client: OwnerDashboardClient) =>
  client.jobs.reduce((sum, j) => sum + j.submissions.length, 0)

const approvedCount = (client: OwnerDashboardClient) =>
  client.jobs.reduce(
    (sum, j) => sum + j.submissions.filter((s) => s.owner_status === 'approved').length,
    0,
  )

async function handleDownloadApprovedClient(client: OwnerDashboardClient) {
  downloadingClient.value = client.client_id
  error.value = ''
  try {
    const safeName = client.company_name.replace(/\s+/g, '_')
    await downloadApprovedClientSubmissions(client.client_id, `${safeName}_approved_profiles.xlsx`)
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Download failed'
  } finally {
    downloadingClient.value = null
  }
}
</script>

<template>
  <div class="od-page">
    <div class="od-header">
      <div>
        <h1 class="hrms-page-title">Submissions Dashboard</h1>
        <p class="od-subtitle">Review and approve candidate submissions by client and job</p>
      </div>
      <button class="hrms-btn hrms-btn--sm" @click="load">Refresh</button>
    </div>

    <HrmsAlert v-if="error" type="error" dismissible @dismiss="error = ''">{{ error }}</HrmsAlert>
    <HrmsAlert v-if="success" type="success" dismissible @dismiss="success = ''">{{ success }}</HrmsAlert>

    <div v-if="loading" class="hrms-loading">Loading dashboard…</div>

    <div v-else-if="dashboard.length === 0" class="hrms-empty">
      <p>No candidate submissions yet.</p>
    </div>

    <div v-else class="od-tree">
      <!-- Client level -->
      <div v-for="client in dashboard" :key="client.client_id" class="od-client">
        <div class="od-client__header hrms-card" @click="toggleClient(client.client_id)">
          <div class="od-client__info">
            <div class="od-client__chevron" :class="{ 'od-client__chevron--open': expandedClients.has(client.client_id) }">
              ▶
            </div>
            <div>
              <div class="od-client__name">{{ client.company_name }}</div>
              <div class="od-client__meta">
                {{ client.jobs.length }} job{{ client.jobs.length !== 1 ? 's' : '' }} ·
                {{ totalSubmissions(client) }} submission{{ totalSubmissions(client) !== 1 ? 's' : '' }} ·
                {{ approvedCount(client) }} approved
              </div>
            </div>
          </div>
          <button
            v-if="approvedCount(client) > 0"
            type="button"
            class="hrms-btn hrms-btn--sm od-client__dl-btn"
            :disabled="downloadingClient === client.client_id"
            @click.stop="handleDownloadApprovedClient(client)"
          >
            {{ downloadingClient === client.client_id ? 'Downloading…' : '⬇ Download Approved' }}
          </button>
        </div>

        <Transition name="collapse">
          <div v-if="expandedClients.has(client.client_id)" class="od-client__body">
            <!-- Job level -->
            <div v-for="job in client.jobs" :key="job.job_requirement_id" class="od-job">
              <div class="od-job__header" @click="toggleJob(job.job_requirement_id)">
                <div class="od-job__chevron" :class="{ 'od-job__chevron--open': expandedJobs.has(job.job_requirement_id) }">
                  ▶
                </div>
                <div class="od-job__info">
                  <span class="od-job__title">{{ job.job_title }}</span>
                  <span class="hrms-status-badge hrms-status-badge--sm" :style="`--sc: ${jobStatusColor(job.status)}`">
                    {{ job.status }}
                  </span>
                  <span class="od-job__count">{{ job.submissions.length }} candidates</span>
                </div>
              </div>

              <Transition name="collapse">
                <div v-if="expandedJobs.has(job.job_requirement_id)" class="od-submissions">
                  <div v-if="job.submissions.length === 0" class="od-empty">
                    No candidates submitted for this job yet.
                  </div>
                  <table v-else class="od-table">
                    <thead>
                      <tr>
                        <th>Candidate</th>
                        <th>Email</th>
                        <th>Submitted By</th>
                        <th>Submitted On</th>
                        <th>Stage</th>
                        <th>Status</th>
                        <th>Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr v-for="sub in job.submissions" :key="sub.id">
                        <td class="od-table__name">{{ sub.candidate_name }}</td>
                        <td class="od-table__email">{{ sub.candidate_email }}</td>
                        <td>{{ sub.submitted_by_name ?? EMPTY }}</td>
                        <td>{{ formatDate(sub.submitted_at) }}</td>
                        <td>{{ sub.current_stage ?? EMPTY }}</td>
                        <td>
                          <span
                            class="hrms-status-badge"
                            :style="`--sc: ${ownerStatusColor(sub.owner_status)}`"
                          >
                            {{ ownerStatusLabel(sub.owner_status) }}
                          </span>
                        </td>
                        <td>
                          <div class="od-actions">
                            <button
                              v-if="sub.owner_status !== 'approved'"
                              type="button"
                              class="hrms-btn hrms-btn--sm hrms-btn--success"
                              :disabled="actioning === sub.id"
                              @click="handleApprove(sub)"
                            >
                              Approve
                            </button>
                            <button
                              v-if="sub.owner_status !== 'rejected'"
                              type="button"
                              class="hrms-btn hrms-btn--sm hrms-btn--danger"
                              :disabled="actioning === sub.id"
                              @click="handleReject(sub)"
                            >
                              Reject
                            </button>
                            <button
                              v-if="sub.owner_status === 'approved'"
                              type="button"
                              class="hrms-btn hrms-btn--sm"
                              :disabled="actioning === `dl-${sub.id}`"
                              @click="handleDownload(sub)"
                            >
                              {{ actioning === `dl-${sub.id}` ? 'Downloading…' : 'Download' }}
                            </button>
                          </div>
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </Transition>
            </div>
          </div>
        </Transition>
      </div>
    </div>
  </div>
</template>

<style scoped>
.od-page {
  padding: 24px;
  max-width: 1100px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.od-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.od-subtitle {
  font-size: 0.875rem;
  color: var(--hrms-text-muted);
  margin: 4px 0 0;
}

.od-tree {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.od-client__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 18px;
  cursor: pointer;
  user-select: none;
  transition: opacity 0.12s;
}

.od-client__header:hover {
  opacity: 0.9;
}

.od-client__info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.od-client__chevron {
  font-size: 0.65rem;
  color: var(--hrms-text-muted);
  transition: transform 0.18s;
  width: 14px;
}

.od-client__chevron--open {
  transform: rotate(90deg);
}

.od-client__name {
  font-weight: 700;
  font-size: 1rem;
}

.od-client__meta {
  font-size: 0.8rem;
  color: var(--hrms-text-muted);
  margin-top: 2px;
}

.od-client__body {
  display: flex;
  flex-direction: column;
  gap: 2px;
  margin-top: 2px;
}

.od-job {
  background: var(--hrms-surface-alt, rgba(255,255,255,0.03));
  border: 1px solid var(--hrms-border);
  border-radius: 8px;
  overflow: hidden;
}

.od-job__header {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 16px;
  cursor: pointer;
  user-select: none;
}

.od-job__header:hover {
  background: rgba(255,255,255,0.04);
}

.od-job__chevron {
  font-size: 0.6rem;
  color: var(--hrms-text-muted);
  transition: transform 0.18s;
  width: 12px;
  flex-shrink: 0;
}

.od-job__chevron--open {
  transform: rotate(90deg);
}

.od-job__info {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.od-job__title {
  font-weight: 600;
  font-size: 0.9rem;
}

.od-job__count {
  font-size: 0.8rem;
  color: var(--hrms-text-muted);
}

.od-submissions {
  padding: 0 16px 12px;
}

.od-empty {
  font-size: 0.85rem;
  color: var(--hrms-text-muted);
  padding: 10px 0;
}

.od-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.85rem;
  margin-top: 8px;
}

.od-table th {
  text-align: left;
  padding: 7px 10px;
  border-bottom: 1px solid var(--hrms-border);
  color: var(--hrms-text-muted);
  font-weight: 600;
  font-size: 0.76rem;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.od-table td {
  padding: 9px 10px;
  border-bottom: 1px solid var(--hrms-border);
  vertical-align: middle;
}

.od-table tbody tr:last-child td {
  border-bottom: none;
}

.od-table__name {
  font-weight: 600;
}

.od-table__email {
  color: var(--hrms-text-muted);
  font-size: 0.82rem;
}

.od-actions {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

/* Collapse animation */
.collapse-enter-active,
.collapse-leave-active {
  transition: opacity 0.18s, max-height 0.22s;
  max-height: 2000px;
  overflow: hidden;
}

.collapse-enter-from,
.collapse-leave-to {
  opacity: 0;
  max-height: 0;
}

/* Success button variant */
.hrms-btn--success {
  background: var(--hrms-success, #22c55e);
  color: #fff;
  border: none;
}

.hrms-btn--success:hover:not(:disabled) {
  opacity: 0.85;
}

.od-client__dl-btn {
  flex-shrink: 0;
  white-space: nowrap;
}
</style>
