import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import { fetchDashboardNotifications } from '@/api/dashboard'
import type { DashboardNotification } from '@/types/dashboard'

export const useNotificationsStore = defineStore('notifications', () => {
  const items = ref<DashboardNotification[]>([])
  const loading = ref(false)
  const error = ref('')
  const lastLoadedAt = ref<number | null>(null)

  const unreadCount = computed(() => items.value.length)

  async function load() {
    loading.value = true
    error.value = ''
    try {
      const data = await fetchDashboardNotifications()
      items.value = data.items
      lastLoadedAt.value = Date.now()
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to load notifications'
    } finally {
      loading.value = false
    }
  }

  function refreshIfNeeded(widgets?: string[]) {
    if (!widgets?.length || widgets.includes('notifications')) {
      void load()
    }
  }

  return {
    items,
    loading,
    error,
    unreadCount,
    lastLoadedAt,
    load,
    refreshIfNeeded,
  }
})
