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

function connect() {
  if (!getTokenPresent()) return
  try {
    socket = new WebSocket(buildDashboardWsUrl())
  } catch {
    scheduleRetry()
    return
  }

  socket.onopen = () => {
    connected.value = true
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
    connected.value = false
    socket = null
    if (!closedByUs) scheduleRetry()
  }
  socket.onerror = () => {
    socket?.close()
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
  if (retryTimer) clearTimeout(retryTimer)
  retryTimer = setTimeout(connect, 4000)
}

onMounted(connect)
onUnmounted(() => {
  closedByUs = true
  if (retryTimer) clearTimeout(retryTimer)
  socket?.close()
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
