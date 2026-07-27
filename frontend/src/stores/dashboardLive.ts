import { defineStore } from 'pinia'
import type { DashboardWsEvent } from '@/types/dashboard'

type Listener = (event: DashboardWsEvent) => void

export const useDashboardLiveStore = defineStore('dashboardLive', () => {
  const listeners = new Set<Listener>()

  function subscribe(listener: Listener) {
    listeners.add(listener)
    return () => listeners.delete(listener)
  }

  function publish(event: DashboardWsEvent) {
    listeners.forEach((listener) => listener(event))
  }

  return { subscribe, publish }
})
