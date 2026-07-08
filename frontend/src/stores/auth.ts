import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import * as authApi from '@/api/auth'
import { getStoredToken } from '@/api/token'
import type { AuthUser, DateRange, UserRole } from '@/types/auth'

function defaultDateRange(): DateRange {
  const end = new Date()
  const start = new Date()
  start.setDate(start.getDate() - 30)
  return {
    start: start.toISOString().slice(0, 10),
    end: end.toISOString().slice(0, 10),
  }
}

export const useAuthStore = defineStore('auth', () => {
  const user = ref<AuthUser | null>(null)
  const initialized = ref(false)
  const loading = ref(false)
  const error = ref('')
  const dateRange = ref<DateRange>(defaultDateRange())
  const notificationCount = ref(0)

  const isAuthenticated = computed(() => !!user.value && !!getStoredToken())
  const role = computed<UserRole | null>(() => user.value?.role ?? null)
  const roleLabel = computed(() => {
    if (role.value === 'owner') return 'Owner'
    if (role.value === 'recruiter') return 'Recruiter'
    return ''
  })

  async function initialize() {
    if (initialized.value) return
    initialized.value = true
    if (!getStoredToken()) return
    try {
      user.value = await authApi.fetchMe()
    } catch {
      authApi.clearStoredToken()
      user.value = null
    }
  }

  async function login(email: string, password: string) {
    loading.value = true
    error.value = ''
    try {
      await authApi.login({ email, password })
      user.value = await authApi.fetchMe()
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Login failed'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function updateProfile(payload: authApi.UpdateMePayload) {
    loading.value = true
    error.value = ''
    try {
      user.value = await authApi.updateMe(payload)
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to update profile'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function changePassword(current_password: string, new_password: string) {
    loading.value = true
    error.value = ''
    try {
      await authApi.changePassword({ current_password, new_password })
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to change password'
      throw err
    } finally {
      loading.value = false
    }
  }

  function logout() {
    authApi.logout()
    user.value = null
    initialized.value = true
  }

  function setDateRange(range: DateRange) {
    dateRange.value = range
  }

  return {
    user,
    initialized,
    loading,
    error,
    isAuthenticated,
    role,
    roleLabel,
    dateRange,
    notificationCount,
    initialize,
    login,
    updateProfile,
    changePassword,
    logout,
    setDateRange,
  }
})
