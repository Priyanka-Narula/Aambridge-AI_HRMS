import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import type { DateRange, User, UserRole } from '@/types/auth'

const DEMO_USERS: Record<UserRole, User> = {
  admin: {
    id: '1',
    name: 'Amara Chen',
    email: 'amara@aambridge.ai',
    role: 'admin',
    avatarInitials: 'AC',
  },
  recruiter: {
    id: '2',
    name: 'Priya Narula',
    email: 'priya@aambridge.ai',
    role: 'recruiter',
    avatarInitials: 'PN',
  },
  manager: {
    id: '3',
    name: 'Sofia Martinez',
    email: 'sofia@aambridge.ai',
    role: 'manager',
    avatarInitials: 'SM',
  },
  client: {
    id: '4',
    name: 'Elena Brooks',
    email: 'elena@clientcorp.com',
    role: 'client',
    avatarInitials: 'EB',
  },
}

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
  const user = ref<User>({ ...DEMO_USERS.admin })
  const dateRange = ref<DateRange>(defaultDateRange())
  const notificationCount = ref(3)

  const role = computed(() => user.value.role)
  const roleLabel = computed(() => {
    const labels: Record<UserRole, string> = {
      admin: 'Administrator',
      recruiter: 'Recruiter',
      manager: 'Hiring Manager',
      client: 'Client',
    }
    return labels[user.value.role]
  })

  function setRole(role: UserRole) {
    user.value = { ...DEMO_USERS[role] }
  }

  function setDateRange(range: DateRange) {
    dateRange.value = range
  }

  return {
    user,
    role,
    roleLabel,
    dateRange,
    notificationCount,
    setRole,
    setDateRange,
  }
})
