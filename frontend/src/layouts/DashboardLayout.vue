<script setup lang="ts">
import { ref } from 'vue'
import AppFooter from '@/components/layout/AppFooter.vue'
import AppSidebar from '@/components/layout/AppSidebar.vue'
import AppTopBar from '@/components/layout/AppTopBar.vue'

const sidebarOpen = ref(false)

function toggleSidebar() {
  sidebarOpen.value = !sidebarOpen.value
}

function closeSidebar() {
  sidebarOpen.value = false
}
</script>

<template>
  <div class="dashboard-layout">
    <AppSidebar :open="sidebarOpen" @close="closeSidebar" />

    <div class="dashboard-layout__main">
      <AppTopBar @toggle-sidebar="toggleSidebar" />

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
}
</style>
