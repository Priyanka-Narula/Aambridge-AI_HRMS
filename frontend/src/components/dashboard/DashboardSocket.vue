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
let closedByUs = false
let retryAttempt = 0
let connecting = false

function connect() {
  if (closedByUs || connecting) return
  if (!getTokenPresent()) return
  if (socket && (socket.readyState === WebSocket.OPEN || socket.readyState === WebSocket.CONNECTING)) {
    return
  }

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
  }
  socket.onmessage = (msg) => {
    try {
      const data = JSON.parse(msg.data) as DashboardWsEvent
      live.publish(data)
      emit('event', data)
    } catch {
      /* ignore malformed */
    }
  }
  socket.onclose = () => {
    connecting = false
    connected.value = false
    socket = null
    if (!closedByUs) scheduleRetry()
  }
  socket.onerror = () => {
    connecting = false
    // onclose will run after onerror; avoid double close storms
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
  // Exponential backoff: 2s, 4s, 8s… capped at 30s
  const delay = Math.min(30_000, 2000 * 2 ** Math.min(retryAttempt, 4))
  retryAttempt += 1
  retryTimer = setTimeout(() => {
    retryTimer = null
    connect()
  }, delay)
}

onMounted(connect)
onUnmounted(() => {
  closedByUs = true
  if (retryTimer) clearTimeout(retryTimer)
  retryTimer = null
  try {
    socket?.close()
  } catch {
    /* ignore */
  }
  socket = null
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
