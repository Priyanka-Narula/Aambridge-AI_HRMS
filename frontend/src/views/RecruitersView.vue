<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import {
  createRecruiter,
  fetchUser,
  fetchUsers,
  updateRecruiter,
  updateUserStatus,
} from '@/api/users'
import HrmsAlert from '@/components/ui/HrmsAlert.vue'
import HrmsModal from '@/components/ui/HrmsModal.vue'
import type { RecruiterCreatePayload, RecruiterListItem, RecruiterUpdatePayload } from '@/types/auth'
import { avatarHue, EMPTY, initials, orEmpty } from '@/utils/format'

const users = ref<RecruiterListItem[]>([])
const selected = ref<RecruiterListItem | null>(null)
const activeTab = ref<'overview' | 'profile'>('overview')
const loading = ref(true)
const saving = ref(false)
const error = ref('')
const success = ref('')
const showDialog = ref(false)
const editingUser = ref<RecruiterListItem | null>(null)
const searchQuery = ref('')

type RecruiterForm = RecruiterCreatePayload

const emptyForm = (): RecruiterForm => ({
  first_name: '',
  last_name: '',
  email: '',
  personal_email: '',
  password: '',
  phone: '',
  location: '',
  languages_spoken: '',
  employee_code: '',
  designation: '',
  team: '',
  joining_date: '',
})

const form = ref<RecruiterForm>(emptyForm())

const filtered = computed(() => {
  const q = searchQuery.value.trim().toLowerCase()
  if (!q) return users.value
  return users.value.filter(
    (u) =>
      `${u.first_name} ${u.last_name}`.toLowerCase().includes(q) ||
      u.email.toLowerCase().includes(q) ||
      (u.recruiter?.employee_code ?? '').toLowerCase().includes(q) ||
      (u.recruiter?.team ?? '').toLowerCase().includes(q),
  )
})

const modalTitle = computed(() =>
  editingUser.value
    ? `Edit — ${editingUser.value.first_name} ${editingUser.value.last_name}`
    : 'Create Recruiter',
)

function userToForm(user: RecruiterListItem): RecruiterForm {
  return {
    first_name: user.first_name,
    last_name: user.last_name,
    email: user.email,
    personal_email: user.personal_email ?? '',
    password: '',
    phone: user.phone ?? '',
    location: user.location ?? '',
    languages_spoken: user.languages_spoken ?? '',
    employee_code: user.recruiter?.employee_code ?? '',
    designation: user.recruiter?.designation ?? '',
    team: user.recruiter?.team ?? '',
    joining_date: user.recruiter?.joining_date ?? '',
  }
}

function toUpdatePayload(): RecruiterUpdatePayload {
  return {
    first_name: form.value.first_name,
    last_name: form.value.last_name,
    email: form.value.email,
    personal_email: form.value.personal_email || null,
    phone: form.value.phone || null,
    location: form.value.location || null,
    languages_spoken: form.value.languages_spoken || null,
    employee_code: form.value.employee_code,
    designation: form.value.designation || null,
    team: form.value.team || null,
    joining_date: form.value.joining_date || null,
  }
}

async function loadUsers() {
  loading.value = true
  error.value = ''
  try {
    users.value = await fetchUsers()
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Failed to load recruiters'
  } finally {
    loading.value = false
  }
}

onMounted(loadUsers)

async function selectRecruiter(user: RecruiterListItem) {
  activeTab.value = 'overview'
  try {
    selected.value = await fetchUser(user.id)
  } catch {
    selected.value = user
  }
}

function closePanel() {
  selected.value = null
}

function openCreate() {
  editingUser.value = null
  form.value = emptyForm()
  showDialog.value = true
}

function openEdit(user?: RecruiterListItem) {
  const target = user ?? selected.value
  if (!target) return
  editingUser.value = target
  form.value = userToForm(target)
  showDialog.value = true
}

async function submitRecruiter() {
  saving.value = true
  error.value = ''
  success.value = ''
  try {
    if (editingUser.value) {
      const updated = await updateRecruiter(editingUser.value.id, toUpdatePayload())
      users.value = users.value.map((u) => (u.id === updated.id ? updated : u))
      if (selected.value?.id === updated.id) selected.value = updated
      success.value = `${updated.first_name} ${updated.last_name} updated`
    } else {
      const created = await createRecruiter({
        ...form.value,
        phone: form.value.phone || null,
        location: form.value.location || null,
        languages_spoken: form.value.languages_spoken || null,
        personal_email: form.value.personal_email || null,
        designation: form.value.designation || null,
        team: form.value.team || null,
        joining_date: form.value.joining_date || null,
      })
      users.value = [created, ...users.value]
      success.value = `Recruiter ${created.first_name} ${created.last_name} created. Password: ${form.value.password}`
    }
    showDialog.value = false
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Failed to save recruiter'
  } finally {
    saving.value = false
  }
}

async function toggleStatus(user: RecruiterListItem) {
  const nextStatus = user.status === 'active' ? 'inactive' : 'active'
  error.value = ''
  try {
    const updated = await updateUserStatus(user.id, nextStatus)
    users.value = users.value.map((u) => (u.id === updated.id ? updated : u))
    if (selected.value?.id === updated.id) selected.value = updated
    success.value = `Status updated to ${nextStatus}`
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Failed to update status'
  }
}

const formatDate = (d: string | null | undefined) =>
  d ? new Date(d).toLocaleDateString('en-IN') : EMPTY
</script>

<template>
  <div class="hrms-split">
    <div class="hrms-split__main" :class="{ 'hrms-split__main--narrow': selected }">
      <div class="hrms-split__header">
        <div class="hrms-page-header hrms-page-header--compact">
          <div>
            <h1 class="hrms-page-title hrms-page-title--sm">Recruiter Management</h1>
            <span class="hrms-page-count">{{ filtered.length }} recruiters</span>
          </div>
          <button type="button" class="hrms-btn hrms-btn--primary" @click="openCreate">
            Add Recruiter
          </button>
        </div>

        <div class="hrms-controls">
          <input
            v-model="searchQuery"
            class="hrms-input hrms-search-input"
            type="search"
            placeholder="Search by name, email, code or team…"
          />
        </div>
      </div>

      <HrmsAlert v-if="error" type="error" dismissible @dismiss="error = ''">{{ error }}</HrmsAlert>
      <HrmsAlert v-if="success" type="success" dismissible @dismiss="success = ''">{{ success }}</HrmsAlert>

      <div v-if="loading" class="hrms-loading">Loading recruiters…</div>

      <div v-else class="hrms-split__list hrms-scroll">
        <div
          v-for="user in filtered"
          :key="user.id"
          class="hrms-card hrms-card--interactive hrms-entity-card"
          :class="{ 'hrms-card--selected': selected?.id === user.id }"
          @click="selectRecruiter(user)"
        >
          <div class="hrms-avatar" :style="`--hue: ${avatarHue(user.id)}`">
            {{ initials(user.first_name, user.last_name) }}
          </div>

          <div class="hrms-entity-card__body">
            <div class="hrms-entity-card__name-row">
              <span class="hrms-entity-card__name">{{ user.first_name }} {{ user.last_name }}</span>
              <span
                class="hrms-status-badge"
                :style="`--sc: ${user.status === 'active' ? 'var(--hrms-success)' : 'var(--hrms-text-muted)'}`"
              >
                {{ user.status }}
              </span>
            </div>
            <div class="hrms-entity-card__role">{{ user.email }}</div>
            <div class="hrms-entity-card__meta">
              <span>{{ orEmpty(user.recruiter?.employee_code) }}</span>
              <span v-if="user.recruiter?.team">{{ user.recruiter.team }}</span>
              <span v-if="user.recruiter?.designation">{{ user.recruiter.designation }}</span>
            </div>
          </div>
        </div>

        <div v-if="filtered.length === 0" class="hrms-empty">
          <p v-if="searchQuery">No recruiters match your search.</p>
          <p v-else>No recruiters yet. Add your first recruiter account.</p>
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
            <div class="hrms-avatar hrms-avatar--lg" :style="`--hue: ${avatarHue(selected.id)}`">
              {{ initials(selected.first_name, selected.last_name) }}
            </div>
            <div>
              <h2 class="hrms-panel-name">{{ selected.first_name }} {{ selected.last_name }}</h2>
              <p class="hrms-panel-role">{{ orEmpty(selected.recruiter?.designation) }}</p>
              <span
                class="hrms-status-badge hrms-status-badge--lg"
                :style="`--sc: ${selected.status === 'active' ? 'var(--hrms-success)' : 'var(--hrms-text-muted)'}`"
              >
                {{ selected.status }}
              </span>
            </div>
          </div>

          <div class="hrms-actions hrms-actions--inline" style="padding-bottom: 16px">
            <button type="button" class="hrms-btn hrms-btn--primary hrms-btn--sm" @click="openEdit()">
              Edit
            </button>
            <button
              type="button"
              class="hrms-btn hrms-btn--sm"
              :class="selected.status === 'active' ? 'hrms-btn--danger' : 'hrms-btn--primary'"
              @click="toggleStatus(selected)"
            >
              {{ selected.status === 'active' ? 'Deactivate' : 'Activate' }}
            </button>
            <a :href="`mailto:${selected.email}`" class="hrms-btn hrms-btn--sm">Email</a>
          </div>
        </div>

        <div class="hrms-tabs">
          <button
            class="hrms-tab"
            :class="{ 'hrms-tab--active': activeTab === 'overview' }"
            @click="activeTab = 'overview'"
          >Overview</button>
          <button
            class="hrms-tab"
            :class="{ 'hrms-tab--active': activeTab === 'profile' }"
            @click="activeTab = 'profile'"
          >Profile</button>
        </div>

        <div class="hrms-panel-body hrms-scroll">
          <template v-if="activeTab === 'overview'">
            <section class="hrms-section">
              <h3 class="hrms-section-title">Account</h3>
              <div class="hrms-info-grid">
                <div class="hrms-info-item">
                  <span class="hrms-info-label">Email</span>
                  <a :href="`mailto:${selected.email}`" class="hrms-info-value hrms-info-link">{{ selected.email }}</a>
                </div>
                <div class="hrms-info-item">
                  <span class="hrms-info-label">Personal Email</span>
                  <span class="hrms-info-value">{{ orEmpty(selected.personal_email) }}</span>
                </div>
                <div class="hrms-info-item">
                  <span class="hrms-info-label">Phone</span>
                  <span class="hrms-info-value">{{ orEmpty(selected.phone) }}</span>
                </div>
                <div class="hrms-info-item">
                  <span class="hrms-info-label">Employee Code</span>
                  <span class="hrms-info-value">{{ orEmpty(selected.recruiter?.employee_code) }}</span>
                </div>
                <div class="hrms-info-item">
                  <span class="hrms-info-label">Joined</span>
                  <span class="hrms-info-value">{{ formatDate(selected.recruiter?.joining_date) }}</span>
                </div>
                <div class="hrms-info-item">
                  <span class="hrms-info-label">Created</span>
                  <span class="hrms-info-value">{{ formatDate(selected.created_at) }}</span>
                </div>
              </div>
            </section>
          </template>

          <template v-else>
            <section class="hrms-section">
              <h3 class="hrms-section-title">Work Profile</h3>
              <div class="hrms-info-grid">
                <div class="hrms-info-item">
                  <span class="hrms-info-label">Designation</span>
                  <span class="hrms-info-value">{{ orEmpty(selected.recruiter?.designation) }}</span>
                </div>
                <div class="hrms-info-item">
                  <span class="hrms-info-label">Team</span>
                  <span class="hrms-info-value">{{ orEmpty(selected.recruiter?.team) }}</span>
                </div>
                <div class="hrms-info-item">
                  <span class="hrms-info-label">Location</span>
                  <span class="hrms-info-value">{{ orEmpty(selected.location) }}</span>
                </div>
                <div class="hrms-info-item">
                  <span class="hrms-info-label">Languages</span>
                  <span class="hrms-info-value">{{ orEmpty(selected.languages_spoken) }}</span>
                </div>
              </div>
            </section>
          </template>
        </div>
      </div>
    </Transition>

    <HrmsModal v-model="showDialog" :title="modalTitle">
      <div class="hrms-form-grid">
        <label class="hrms-field">
          <span class="hrms-label">First name</span>
          <input v-model="form.first_name" class="hrms-input" type="text" required />
        </label>
        <label class="hrms-field">
          <span class="hrms-label">Last name</span>
          <input v-model="form.last_name" class="hrms-input" type="text" required />
        </label>
        <label class="hrms-field">
          <span class="hrms-label">Email</span>
          <input v-model="form.email" class="hrms-input" type="email" required placeholder="" />
        </label>
        <label class="hrms-field">
          <span class="hrms-label">Personal mail id</span>
          <input v-model="form.personal_email" class="hrms-input" type="email" placeholder="" />
        </label>
        <label v-if="!editingUser" class="hrms-field">
          <span class="hrms-label">Password</span>
          <input v-model="form.password" class="hrms-input" type="password" required placeholder="" />
        </label>
        <label class="hrms-field">
          <span class="hrms-label">Employee code</span>
          <input v-model="form.employee_code" class="hrms-input" type="text" required />
        </label>
        <label class="hrms-field">
          <span class="hrms-label">Phone</span>
          <input v-model="form.phone" class="hrms-input" type="tel" />
        </label>
        <label class="hrms-field">
          <span class="hrms-label">Designation</span>
          <input v-model="form.designation" class="hrms-input" type="text" />
        </label>
        <label class="hrms-field">
          <span class="hrms-label">Team</span>
          <input v-model="form.team" class="hrms-input" type="text" />
        </label>
        <label class="hrms-field">
          <span class="hrms-label">Location</span>
          <input v-model="form.location" class="hrms-input" type="text" />
        </label>
        <label class="hrms-field">
          <span class="hrms-label">Languages spoken</span>
          <input v-model="form.languages_spoken" class="hrms-input" type="text" placeholder="English, Arabic" />
        </label>
        <label class="hrms-field">
          <span class="hrms-label">Joining date</span>
          <input v-model="form.joining_date" class="hrms-input" type="date" />
        </label>
      </div>

      <template #footer>
        <button type="button" class="hrms-btn" @click="showDialog = false">Cancel</button>
        <button type="button" class="hrms-btn hrms-btn--primary" :disabled="saving" @click="submitRecruiter">
          {{ saving ? 'Saving…' : editingUser ? 'Save Changes' : 'Create' }}
        </button>
      </template>
    </HrmsModal>
  </div>
</template>
