<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import HrmsAlert from '@/components/ui/HrmsAlert.vue'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()

const saving = computed(() => auth.loading)
const success = ref('')

const profile = ref({
  first_name: '',
  last_name: '',
  email: '',
  phone: '',
  location: '',
  languages_spoken: '',
})

const password = ref({
  current: '',
  next: '',
  confirm: '',
})

const passwordMismatch = computed(() => password.value.next !== password.value.confirm)

onMounted(async () => {
  await auth.initialize()
  if (!auth.user) return
  profile.value = {
    first_name: auth.user.first_name,
    last_name: auth.user.last_name,
    email: auth.user.email,
    phone: auth.user.phone ?? '',
    location: auth.user.location ?? '',
    languages_spoken: auth.user.languages_spoken ?? '',
  }
})

async function saveProfile() {
  success.value = ''
  await auth.updateProfile({
    first_name: profile.value.first_name.trim(),
    last_name: profile.value.last_name.trim(),
    email: profile.value.email.trim(),
    phone: profile.value.phone.trim() ? profile.value.phone.trim() : null,
    location: profile.value.location.trim() ? profile.value.location.trim() : null,
    languages_spoken: profile.value.languages_spoken.trim() ? profile.value.languages_spoken.trim() : null,
  })
  success.value = 'Profile updated'
}

async function savePassword() {
  if (passwordMismatch.value) return
  success.value = ''
  await auth.changePassword(password.value.current, password.value.next)
  password.value = { current: '', next: '', confirm: '' }
  success.value = 'Password updated'
}
</script>

<template>
  <div class="hrms-page">
    <div class="hrms-page-header hrms-page-header--compact" style="margin-bottom: 14px">
      <div>
        <h1 class="hrms-page-title hrms-page-title--sm">Settings</h1>
        <p class="hrms-page-subtitle">Manage your profile and account preferences</p>
      </div>
    </div>

    <HrmsAlert v-if="auth.error" type="error" dismissible @dismiss="auth.error = ''">
      {{ auth.error }}
    </HrmsAlert>
    <HrmsAlert v-if="success" type="success" dismissible @dismiss="success = ''">
      {{ success }}
    </HrmsAlert>

    <section class="hrms-section hrms-card" style="padding: 16px">
      <h3 class="hrms-section-title">Profile</h3>
      <div class="hrms-form-grid">
        <label class="hrms-field">
          <span class="hrms-label">First name</span>
          <input v-model="profile.first_name" class="hrms-input" type="text" required />
        </label>
        <label class="hrms-field">
          <span class="hrms-label">Last name</span>
          <input v-model="profile.last_name" class="hrms-input" type="text" required />
        </label>
        <label class="hrms-field hrms-field--wide">
          <span class="hrms-label">Email</span>
          <input v-model="profile.email" class="hrms-input" type="email" required />
        </label>
        <label class="hrms-field">
          <span class="hrms-label">Phone</span>
          <input v-model="profile.phone" class="hrms-input" type="tel" />
        </label>
        <label class="hrms-field">
          <span class="hrms-label">Location</span>
          <input v-model="profile.location" class="hrms-input" type="text" />
        </label>
        <label class="hrms-field hrms-field--wide">
          <span class="hrms-label">Languages spoken</span>
          <input v-model="profile.languages_spoken" class="hrms-input" type="text" placeholder="English, Arabic" />
        </label>
      </div>

      <div class="hrms-actions hrms-actions--inline" style="padding-top: 12px">
        <button type="button" class="hrms-btn hrms-btn--primary" :disabled="saving" @click="saveProfile">
          {{ saving ? 'Saving…' : 'Save profile' }}
        </button>
      </div>
    </section>

    <section class="hrms-section hrms-card" style="padding: 16px; margin-top: 14px">
      <h3 class="hrms-section-title">Security</h3>
      <div class="hrms-form-grid">
        <label class="hrms-field hrms-field--wide">
          <span class="hrms-label">Current password</span>
          <input v-model="password.current" class="hrms-input" type="password" autocomplete="current-password" />
        </label>
        <label class="hrms-field">
          <span class="hrms-label">New password</span>
          <input v-model="password.next" class="hrms-input" type="password" autocomplete="new-password" />
        </label>
        <label class="hrms-field">
          <span class="hrms-label">Confirm new password</span>
          <input v-model="password.confirm" class="hrms-input" type="password" autocomplete="new-password" />
        </label>
      </div>

      <HrmsAlert v-if="passwordMismatch" type="warning" style="margin-top: 10px">
        New password and confirmation do not match.
      </HrmsAlert>

      <div class="hrms-actions hrms-actions--inline" style="padding-top: 12px">
        <button
          type="button"
          class="hrms-btn hrms-btn--primary"
          :disabled="saving || passwordMismatch || !password.current || !password.next"
          @click="savePassword"
        >
          {{ saving ? 'Saving…' : 'Change password' }}
        </button>
      </div>
    </section>
  </div>
</template>

<style scoped>
.hrms-page {
  padding: 0;
}
</style>

