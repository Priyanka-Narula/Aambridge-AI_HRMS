<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import AppFooter from '@/components/layout/AppFooter.vue'
import AppSidebar from '@/components/layout/AppSidebar.vue'
import AppTopBar from '@/components/layout/AppTopBar.vue'

const SIDEBAR_COLLAPSED_KEY = 'hrms.sidebarCollapsed'

const sidebarOpen = ref(false)
const sidebarCollapsed = ref(false)

onMounted(() => {
  try {
    sidebarCollapsed.value = localStorage.getItem(SIDEBAR_COLLAPSED_KEY) === '1'
  } catch {
    sidebarCollapsed.value = false
  }
})

watch(sidebarCollapsed, (collapsed) => {
  try {
    localStorage.setItem(SIDEBAR_COLLAPSED_KEY, collapsed ? '1' : '0')
  } catch {
    /* ignore quota / private mode */
  }
})

function isDesktop() {
  return typeof window !== 'undefined' && window.matchMedia('(min-width: 1024px)').matches
}

function toggleSidebar() {
  if (isDesktop()) {
    sidebarCollapsed.value = !sidebarCollapsed.value
    return
  }
  sidebarOpen.value = !sidebarOpen.value
}

function toggleCollapse() {
  sidebarCollapsed.value = !sidebarCollapsed.value
}

function closeSidebar() {
  sidebarOpen.value = false
}
</script>

<template>
  <div
    class="dashboard-layout"
    :class="{ 'dashboard-layout--sidebar-collapsed': sidebarCollapsed }"
  >
    <AppSidebar
      :open="sidebarOpen"
      :collapsed="sidebarCollapsed"
      @close="closeSidebar"
      @toggle-collapse="toggleCollapse"
    />

    <div class="dashboard-layout__main">
      <AppTopBar
        :sidebar-collapsed="sidebarCollapsed"
        @toggle-sidebar="toggleSidebar"
      />

      <main class="dashboard-layout__content">
        <RouterView />
      </main>

      <AppFooter />
    </div>
  </div>
</template>

<style scoped>
.dashboard-layout {
  display: flex;
  min-height: 100vh;
  background: var(--hrms-surface);
}

.dashboard-layout__main {
  display: flex;
  flex: 1;
  flex-direction: column;
  min-width: 0;
  min-height: 100vh;
  transition: margin-left var(--hrms-transition);
}

.dashboard-layout__content {
  flex: 1;
  padding: 24px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.dashboard-layout__content:has(.hrms-split) {
  padding: 0;
  overflow: hidden;
}

@media (min-width: 1024px) {
  .dashboard-layout__main {
    margin-left: var(--hrms-sidebar-width);
  }

  .dashboard-layout--sidebar-collapsed .dashboard-layout__main {
    margin-left: var(--hrms-sidebar-collapsed-width);
  }
}
</style>
