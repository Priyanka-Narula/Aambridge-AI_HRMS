<script setup lang="ts">
import { useRouter } from 'vue-router'
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
  <v-container class="fill-height" fluid>
    <v-row align="center" justify="center">
      <v-col cols="12" sm="8" md="6" class="text-center">
        <v-icon icon="mdi-shield-lock-outline" size="72" color="primary" class="mb-4" />
        <h1 class="text-h4 font-weight-bold mb-2">Access Denied</h1>
        <p class="text-body-1 text-medium-emphasis mb-6">
          You don't have permission to view this page.
        </p>
        <div class="d-flex ga-3 justify-center flex-wrap">
          <v-btn color="primary" @click="goBack">Go to Dashboard</v-btn>
          <v-btn variant="outlined" @click="logout">Sign out</v-btn>
        </div>
      </v-col>
    </v-row>
  </v-container>
</template>
