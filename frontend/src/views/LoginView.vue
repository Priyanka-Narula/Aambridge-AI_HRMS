<script setup lang="ts">
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
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
  <v-container class="login-page fill-height" fluid>
    <v-row align="center" justify="center">
      <v-col cols="12" sm="8" md="5" lg="4">
        <v-card class="pa-8" elevation="4" rounded="lg">
          <div class="text-center mb-6">
            <div class="login-logo mb-3">A</div>
            <h1 class="text-h5 font-weight-bold">Aambridge-AI HRMS</h1>
            <p class="text-body-2 text-medium-emphasis mt-1">Sign in to your account</p>
          </div>

          <v-alert v-if="auth.error" type="error" variant="tonal" class="mb-4" density="compact">
            {{ auth.error }}
          </v-alert>

          <v-form @submit.prevent="handleSubmit">
            <v-text-field
              v-model="email"
              label="Email"
              type="email"
              autocomplete="email"
              prepend-inner-icon="mdi-email-outline"
              variant="outlined"
              required
              class="mb-2"
            />
            <v-text-field
              v-model="password"
              label="Password"
              :type="showPassword ? 'text' : 'password'"
              autocomplete="current-password"
              prepend-inner-icon="mdi-lock-outline"
              :append-inner-icon="showPassword ? 'mdi-eye-off' : 'mdi-eye'"
              variant="outlined"
              required
              class="mb-4"
              @click:append-inner="showPassword = !showPassword"
            />
            <v-btn
              type="submit"
              color="primary"
              size="large"
              block
              :loading="auth.loading"
            >
              Sign in
            </v-btn>
          </v-form>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<style scoped>
.login-page {
  min-height: 100vh;
  background: linear-gradient(135deg, #f8f0f4 0%, #fffbfa 50%, #f0e6d4 100%);
}

.login-logo {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 56px;
  height: 56px;
  border-radius: 14px;
  background: linear-gradient(135deg, #c4a35a 0%, #d4b87a 100%);
  font-family: var(--hrms-font-display, serif);
  font-size: 1.75rem;
  font-weight: 700;
  color: #4f2645;
}
</style>
