<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { createRecruiter, fetchUsers, updateUserStatus } from '@/api/users'
import HrmsAlert from '@/components/ui/HrmsAlert.vue'
import HrmsModal from '@/components/ui/HrmsModal.vue'
import PageHeader from '@/components/ui/PageHeader.vue'
import PageLayout from '@/components/ui/PageLayout.vue'
import type { RecruiterCreatePayload, RecruiterListItem } from '@/types/auth'
import { avatarHue, initials, orEmpty } from '@/utils/format'

const users = ref<RecruiterListItem[]>([])
const loading = ref(true)
const saving = ref(false)
const error = ref('')
const success = ref('')
const showDialog = ref(false)

const form = ref<RecruiterCreatePayload>({
  first_name: '',
  last_name: '',
  email: '',
  password: '',
  phone: '',
  employee_code: '',
  designation: '',
  team: '',
  joining_date: '',
})

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

function openDialog() {
  form.value = {
    first_name: '',
    last_name: '',
    email: '',
    password: '',
    phone: '',
    employee_code: '',
    designation: '',
    team: '',
    joining_date: '',
  }
  showDialog.value = true
}

async function submitRecruiter() {
  saving.value = true
  error.value = ''
  success.value = ''
  try {
    const created = await createRecruiter({
      ...form.value,
      phone: form.value.phone || null,
      designation: form.value.designation || null,
      team: form.value.team || null,
      joining_date: form.value.joining_date || null,
    })
    users.value = [created, ...users.value]
    showDialog.value = false
    success.value = `Recruiter ${created.first_name} ${created.last_name} created`
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Failed to create recruiter'
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
    success.value = `Status updated to ${nextStatus}`
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Failed to update status'
  }
}
</script>

<template>
  <PageLayout>
    <PageHeader
      title="Recruiter Management"
      subtitle="Create and manage recruiter accounts"
      :count="`${users.length} recruiters`"
      size="default"
    >
      <template #actions>
        <button type="button" class="hrms-btn hrms-btn--primary" @click="openDialog">
          Add Recruiter
        </button>
      </template>
    </PageHeader>

    <HrmsAlert v-if="error" type="error" dismissible @dismiss="error = ''">
      {{ error }}
    </HrmsAlert>
    <HrmsAlert v-if="success" type="success" dismissible @dismiss="success = ''">
      {{ success }}
    </HrmsAlert>

    <div v-if="loading" class="hrms-loading">Loading recruiters...</div>

    <div v-else class="hrms-list-stack">
      <article
        v-for="user in users"
        :key="user.id"
        class="hrms-card hrms-card--flat hrms-entity-card"
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

        <div class="hrms-entity-card__aside">
          <button
            type="button"
            class="hrms-btn hrms-btn--sm"
            :class="user.status === 'active' ? 'hrms-btn--danger' : 'hrms-btn--primary'"
            @click="toggleStatus(user)"
          >
            {{ user.status === 'active' ? 'Deactivate' : 'Activate' }}
          </button>
        </div>
      </article>

      <div v-if="users.length === 0" class="hrms-empty">
        <p>No recruiters yet. Add your first recruiter account.</p>
      </div>
    </div>

    <HrmsModal v-model="showDialog" title="Create Recruiter">
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
          <input v-model="form.email" class="hrms-input" type="email" required />
        </label>
        <label class="hrms-field">
          <span class="hrms-label">Password</span>
          <input v-model="form.password" class="hrms-input" type="password" required />
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
          <span class="hrms-label">Joining date</span>
          <input v-model="form.joining_date" class="hrms-input" type="date" />
        </label>
      </div>

      <template #footer>
        <button type="button" class="hrms-btn" @click="showDialog = false">Cancel</button>
        <button type="button" class="hrms-btn hrms-btn--primary" :disabled="saving" @click="submitRecruiter">
          {{ saving ? 'Creating...' : 'Create' }}
        </button>
      </template>
    </HrmsModal>
  </PageLayout>
</template>
