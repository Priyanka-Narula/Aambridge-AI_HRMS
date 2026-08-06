import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import { fetchDashboardNotifications } from '@/api/dashboard'
import type { DashboardNotification, DashboardWsEvent } from '@/types/dashboard'

export const useNotificationsStore = defineStore('notifications', () => {
  const items = ref<DashboardNotification[]>([])
  const loading = ref(false)
  const error = ref('')
  const lastLoadedAt = ref<number | null>(null)
  const clearedAt = ref<number | null>(null)

  const unreadCount = computed(() => items.value.length)

  function isAfterClear(createdAt: string | null | undefined) {
    if (!clearedAt.value) return true
    if (!createdAt) return false
    const ts = new Date(createdAt).getTime()
    return Number.isFinite(ts) && ts > clearedAt.value
  }

  async function load() {
    loading.value = true
    error.value = ''
    try {
      const data = await fetchDashboardNotifications()
      items.value = data.items.filter((item) => isAfterClear(item.created_at))
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

  function clear() {
    items.value = []
    clearedAt.value = Date.now()
    lastLoadedAt.value = Date.now()
  }

  function ingestEvent(event: DashboardWsEvent) {
    if (event.type === 'connected') return

    const detail = event.detail ?? {}
    const actorName = (detail.actor_name as string | undefined) || (detail.actor_email as string | undefined)
    const item: DashboardNotification = {
      id: `live-${Date.now()}-${event.type}`,
      type: event.type,
      title: event.type.replace('.', ' ').replace(/\b\w/g, (c) => c.toUpperCase()),
      description:
        (detail.name as string | undefined) ||
        (detail.company_name as string | undefined) ||
        (detail.action as string | undefined) ||
        'Activity updated',
      created_at: new Date().toISOString(),
      actor: actorName ?? null,
    }

    items.value = [item, ...items.value].slice(0, 20)
    lastLoadedAt.value = Date.now()
  }

  return {
    items,
    loading,
    error,
    unreadCount,
    lastLoadedAt,
    load,
    clear,
    refreshIfNeeded,
    ingestEvent,
  }
})
