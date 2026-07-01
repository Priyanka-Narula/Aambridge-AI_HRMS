<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { createRecruiter, fetchUsers, updateUserStatus } from '@/api/users'
import type { RecruiterCreatePayload, RecruiterListItem } from '@/types/auth'

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

const headers = [
  { title: 'Name', key: 'name' },
  { title: 'Email', key: 'email' },
  { title: 'Employee Code', key: 'employee_code' },
  { title: 'Team', key: 'team' },
  { title: 'Status', key: 'status' },
  { title: 'Actions', key: 'actions', sortable: false },
]

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
  <div class="recruiters-page">
    <div class="d-flex align-center justify-space-between mb-6 flex-wrap ga-3">
      <div>
        <h1 class="text-h5 font-weight-bold">Recruiter Management</h1>
        <p class="text-body-2 text-medium-emphasis">Create and manage recruiter accounts</p>
      </div>
      <v-btn color="primary" prepend-icon="mdi-account-plus" @click="openDialog">
        Add Recruiter
      </v-btn>
    </div>

    <v-alert v-if="error" type="error" variant="tonal" class="mb-4" closable @click:close="error = ''">
      {{ error }}
    </v-alert>
    <v-alert v-if="success" type="success" variant="tonal" class="mb-4" closable @click:close="success = ''">
      {{ success }}
    </v-alert>

    <v-card>
      <v-data-table
        :headers="headers"
        :items="users"
        :loading="loading"
        item-value="id"
        class="elevation-0"
      >
        <template #item.name="{ item }">
          {{ item.first_name }} {{ item.last_name }}
        </template>
        <template #item.employee_code="{ item }">
          {{ item.recruiter?.employee_code ?? '—' }}
        </template>
        <template #item.team="{ item }">
          {{ item.recruiter?.team ?? '—' }}
        </template>
        <template #item.status="{ item }">
          <v-chip
            :color="item.status === 'active' ? 'success' : 'default'"
            size="small"
            variant="tonal"
          >
            {{ item.status }}
          </v-chip>
        </template>
        <template #item.actions="{ item }">
          <v-btn
            size="small"
            variant="text"
            :color="item.status === 'active' ? 'error' : 'success'"
            @click="toggleStatus(item)"
          >
            {{ item.status === 'active' ? 'Deactivate' : 'Activate' }}
          </v-btn>
        </template>
      </v-data-table>
    </v-card>

    <v-dialog v-model="showDialog" max-width="640" persistent>
      <v-card>
        <v-card-title class="text-h6">Create Recruiter</v-card-title>
        <v-card-text>
          <v-row dense>
            <v-col cols="12" sm="6">
              <v-text-field v-model="form.first_name" label="First name" variant="outlined" required />
            </v-col>
            <v-col cols="12" sm="6">
              <v-text-field v-model="form.last_name" label="Last name" variant="outlined" required />
            </v-col>
            <v-col cols="12" sm="6">
              <v-text-field v-model="form.email" label="Email" type="email" variant="outlined" required />
            </v-col>
            <v-col cols="12" sm="6">
              <v-text-field v-model="form.password" label="Password" type="password" variant="outlined" required />
            </v-col>
            <v-col cols="12" sm="6">
              <v-text-field v-model="form.employee_code" label="Employee code" variant="outlined" required />
            </v-col>
            <v-col cols="12" sm="6">
              <v-text-field v-model="form.phone" label="Phone" variant="outlined" />
            </v-col>
            <v-col cols="12" sm="6">
              <v-text-field v-model="form.designation" label="Designation" variant="outlined" />
            </v-col>
            <v-col cols="12" sm="6">
              <v-text-field v-model="form.team" label="Team" variant="outlined" />
            </v-col>
            <v-col cols="12" sm="6">
              <v-text-field v-model="form.joining_date" label="Joining date" type="date" variant="outlined" />
            </v-col>
          </v-row>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="showDialog = false">Cancel</v-btn>
          <v-btn color="primary" :loading="saving" @click="submitRecruiter">Create</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<style scoped>
.recruiters-page {
  max-width: 1200px;
}
</style>
