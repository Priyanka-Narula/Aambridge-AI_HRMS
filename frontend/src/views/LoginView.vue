<script setup lang="ts">
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import HrmsAlert from '@/components/ui/HrmsAlert.vue'
import HrmsAuthLayout from '@/components/ui/HrmsAuthLayout.vue'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()

const email = ref('')
const password = ref('')
const showPassword = ref(false)

async function handleSubmit() {
  try {
    await auth.login(email.value, password.value)
    const redirect = typeof route.query.redirect === 'string' ? route.query.redirect : '/'
    await router.push(redirect)
  } catch {
    // error shown via auth.error
  }
}
</script>

<template>
  <HrmsAuthLayout>
    <div class="hrms-auth-brand">
      <div class="hrms-auth-logo">A</div>
      <h1 class="hrms-page-title hrms-page-title--sm">Aambridge-AI HRMS</h1>
      <p class="hrms-page-subtitle">Sign in to your account</p>
    </div>

    <HrmsAlert v-if="auth.error" type="error">{{ auth.error }}</HrmsAlert>

    <form class="hrms-form-grid" @submit.prevent="handleSubmit">
      <label class="hrms-field hrms-field--wide">
        <span class="hrms-label">Email</span>
        <input v-model="email" class="hrms-input" type="email" autocomplete="email" required />
      </label>
      <label class="hrms-field hrms-field--wide">
        <span class="hrms-label">Password</span>
        <div class="hrms-password-field">
          <input
            v-model="password"
            class="hrms-input"
            :type="showPassword ? 'text' : 'password'"
            autocomplete="current-password"
            required
          />
          <button type="button" class="hrms-btn hrms-btn--sm hrms-btn--ghost" @click="showPassword = !showPassword">
            {{ showPassword ? 'Hide' : 'Show' }}
          </button>
        </div>
      </label>
      <button type="submit" class="hrms-btn hrms-btn--primary hrms-btn--lg hrms-btn--block" :disabled="auth.loading">
        {{ auth.loading ? 'Signing in...' : 'Sign in' }}
      </button>
    </form>
  </HrmsAuthLayout>
</template>

<style scoped>
.hrms-password-field {
  display: flex;
  gap: 8px;
  align-items: center;
}

.hrms-password-field .hrms-input {
  flex: 1;
}
</style>
