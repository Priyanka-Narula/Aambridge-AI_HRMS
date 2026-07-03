<script setup lang="ts">
import { useRouter } from 'vue-router'
import HrmsAuthLayout from '@/components/ui/HrmsAuthLayout.vue'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const auth = useAuthStore()

function goBack() {
  router.push({ name: 'dashboard' })
}

function logout() {
  auth.logout()
  router.push({ name: 'login' })
}
</script>

<template>
  <HrmsAuthLayout>
    <div class="hrms-auth-brand">
      <div class="hrms-auth-logo">!</div>
      <h1 class="hrms-page-title hrms-page-title--sm">Access Denied</h1>
      <p class="hrms-page-subtitle">You do not have permission to view this page.</p>
    </div>
    <div class="hrms-actions hrms-actions--inline" style="justify-content: center">
      <button type="button" class="hrms-btn hrms-btn--primary" @click="goBack">Go to Dashboard</button>
      <button type="button" class="hrms-btn hrms-btn--ghost" @click="logout">Sign out</button>
    </div>
  </HrmsAuthLayout>
</template>
