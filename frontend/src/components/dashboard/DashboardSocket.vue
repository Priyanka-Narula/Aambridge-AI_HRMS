<script setup lang="ts">
import { onMounted, onUnmounted, ref } from 'vue'
import { buildDashboardWsUrl } from '@/api/dashboard'
import { useDashboardLiveStore } from '@/stores/dashboardLive'
import type { DashboardWsEvent } from '@/types/dashboard'

const emit = defineEmits<{
  event: [DashboardWsEvent]
}>()

const live = useDashboardLiveStore()
const connected = ref(false)
let socket: WebSocket | null = null
let retryTimer: ReturnType<typeof setTimeout> | null = null
let pingTimer: ReturnType<typeof setInterval> | null = null
let closedByUs = false
let retryAttempt = 0
let connecting = false

const MAX_FAST_RETRIES = 8

function clearTimers() {
  if (retryTimer) {
    clearTimeout(retryTimer)
    retryTimer = null
  }
  if (pingTimer) {
    clearInterval(pingTimer)
    pingTimer = null
  }
}

function closeSocket() {
  const current = socket
  socket = null
  if (!current) return
  current.onopen = null
  current.onmessage = null
  current.onerror = null
  current.onclose = null
  try {
    if (current.readyState === WebSocket.OPEN || current.readyState === WebSocket.CONNECTING) {
      current.close(1000, 'client_close')
    }
  } catch {
    /* ignore */
  }
}

function startPing() {
  if (pingTimer) clearInterval(pingTimer)
  pingTimer = setInterval(() => {
    if (socket?.readyState === WebSocket.OPEN) {
      try {
        socket.send('ping')
      } catch {
        /* ignore */
      }
    }
  }, 25_000)
}

function connect() {
  if (closedByUs || connecting) return
  if (typeof document !== 'undefined' && document.visibilityState === 'hidden') return
  if (!getTokenPresent()) return
  if (socket && (socket.readyState === WebSocket.OPEN || socket.readyState === WebSocket.CONNECTING)) {
    return
  }

  closeSocket()
  connecting = true
  try {
    socket = new WebSocket(buildDashboardWsUrl())
  } catch {
    connecting = false
    scheduleRetry()
    return
  }

  socket.onopen = () => {
    connecting = false
    connected.value = true
    retryAttempt = 0
    startPing()
  }
  socket.onmessage = (msg) => {
    try {
      const data = JSON.parse(msg.data) as DashboardWsEvent
      live.publish(data)
      emit('event', data)
    } catch {
      /* ignore malformed / ping replies */
    }
  }
  socket.onclose = () => {
    connecting = false
    connected.value = false
    if (pingTimer) {
      clearInterval(pingTimer)
      pingTimer = null
    }
    socket = null
    if (!closedByUs) scheduleRetry()
  }
  socket.onerror = () => {
    connecting = false
  }
}

function getTokenPresent() {
  try {
    return !!localStorage.getItem('hrms_access_token') || !!sessionStorage.getItem('hrms_access_token')
  } catch {
    return true
  }
}

function scheduleRetry() {
  if (closedByUs || retryTimer) return
  if (typeof document !== 'undefined' && document.visibilityState === 'hidden') return

  // Backoff: 2s → 4s → … → 30s, then hold at 60s after many failures
  const delay =
    retryAttempt >= MAX_FAST_RETRIES
      ? 60_000
      : Math.min(30_000, 2000 * 2 ** Math.min(retryAttempt, 4))
  retryAttempt += 1
  retryTimer = setTimeout(() => {
    retryTimer = null
    connect()
  }, delay)
}

function onVisibilityChange() {
  if (document.visibilityState === 'hidden') {
    clearTimers()
    return
  }
  if (!connected.value && !closedByUs) {
    retryAttempt = Math.min(retryAttempt, 2)
    connect()
  }
}

onMounted(() => {
  connect()
  document.addEventListener('visibilitychange', onVisibilityChange)
})

onUnmounted(() => {
  closedByUs = true
  document.removeEventListener('visibilitychange', onVisibilityChange)
  clearTimers()
  closeSocket()
  connected.value = false
})

defineExpose({ connected })
</script>

<template>
  <span class="ws-dot" :class="{ 'ws-dot--on': connected }" :title="connected ? 'Live' : 'Reconnecting…'" />
</template>

<style scoped>
.ws-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #94a3b8;
  display: inline-block;
}
.ws-dot--on {
  background: #22c55e;
  box-shadow: 0 0 0 3px rgba(34, 197, 94, 0.2);
}
</style>
