<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import AppIcon from '@/components/layout/AppIcon.vue'
import AppLogo from '@/components/layout/AppLogo.vue'
import { useNavigation } from '@/composables/useNavigation'
import { useAuthStore } from '@/stores/auth'
import type { UserRole } from '@/types/auth'

defineProps<{
  open: boolean
  collapsed: boolean
}>()

const emit = defineEmits<{
  close: []
  toggleCollapse: []
}>()

const route = useRoute()
const auth = useAuthStore()
const { visibleNavItems } = useNavigation()

const currentYear = new Date().getFullYear()

const isActive = (path: string) => {
  if (path === '/') return route.path === '/'
  return route.path.startsWith(path)
}

const sidebarTagline = computed(() => {
  const taglines: Record<UserRole, string> = {
    owner: 'Lead with clarity',
    recruiter: 'Find exceptional talent',
  }
  return auth.role ? taglines[auth.role] : ''
})
</script>

<template>
  <aside
    class="sidebar"
    :class="{
      'sidebar--open': open,
      'sidebar--collapsed': collapsed,
    }"
    aria-label="Main navigation"
  >
    <div class="sidebar__brand">
      <div class="sidebar__logo">
        <AppLogo variant="sidebar" />
      </div>
      <button
        type="button"
        class="sidebar__collapse-btn sidebar__collapse-btn--desktop"
        :aria-label="collapsed ? 'Expand navigation' : 'Collapse navigation'"
        :title="collapsed ? 'Expand' : 'Collapse'"
        @click="emit('toggleCollapse')"
      >
        <svg width="18" height="18" viewBox="0 0 18 18" fill="none" aria-hidden="true">
          <path
            v-if="collapsed"
            d="M7 4.5L11.5 9L7 13.5"
            stroke="currentColor"
            stroke-width="1.8"
            stroke-linecap="round"
            stroke-linejoin="round"
          />
          <path
            v-else
            d="M11 4.5L6.5 9L11 13.5"
            stroke="currentColor"
            stroke-width="1.8"
            stroke-linecap="round"
            stroke-linejoin="round"
          />
        </svg>
      </button>
    </div>

    <p v-if="sidebarTagline && !collapsed" class="sidebar__tagline">{{ sidebarTagline }}</p>

    <nav class="sidebar__nav">
      <RouterLink
        v-for="item in visibleNavItems"
        :key="item.id"
        :to="item.route"
        class="sidebar__link"
        :class="{ 'sidebar__link--active': isActive(item.route) }"
        :title="collapsed ? item.label : undefined"
        :aria-label="collapsed ? item.label : undefined"
        @click="emit('close')"
      >
        <AppIcon :name="item.icon" :size="18" />
        <span class="sidebar__link-label">{{ item.label }}</span>
      </RouterLink>
    </nav>

    <div class="sidebar__footer">
      <p v-if="!collapsed" class="sidebar__copyright">&copy; {{ currentYear }} Aambridge AI</p>
      <button
        type="button"
        class="sidebar__collapse-btn sidebar__collapse-btn--footer"
        :aria-label="collapsed ? 'Expand navigation' : 'Collapse navigation'"
        :title="collapsed ? 'Expand' : 'Collapse'"
        @click="emit('toggleCollapse')"
      >
        <svg width="18" height="18" viewBox="0 0 18 18" fill="none" aria-hidden="true">
          <path
            v-if="collapsed"
            d="M7 4.5L11.5 9L7 13.5"
            stroke="currentColor"
            stroke-width="1.8"
            stroke-linecap="round"
            stroke-linejoin="round"
          />
          <path
            v-else
            d="M11 4.5L6.5 9L11 13.5"
            stroke="currentColor"
            stroke-width="1.8"
            stroke-linecap="round"
            stroke-linejoin="round"
          />
        </svg>
      </button>
    </div>
  </aside>

  <div
    v-if="open"
    class="sidebar__backdrop"
    aria-hidden="true"
    @click="emit('close')"
  />
</template>

<style scoped>
.sidebar {
  position: fixed;
  top: 0;
  left: 0;
  z-index: 200;
  display: flex;
  flex-direction: column;
  width: var(--hrms-sidebar-width);
  height: 100vh;
  background: var(--hrms-sidebar-gradient);
  color: var(--hrms-text-on-sidebar);
  transform: translateX(-100%);
  transition:
    transform var(--hrms-transition),
    width var(--hrms-transition);
  box-shadow: var(--hrms-shadow-lg);
}

.sidebar--open {
  transform: translateX(0);
}

.sidebar__backdrop {
  position: fixed;
  inset: 0;
  z-index: 150;
  background: rgba(45, 36, 48, 0.45);
  backdrop-filter: blur(2px);
}

.sidebar__brand {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 10px;
  padding: 24px 20px 16px;
  position: relative;
}

.sidebar__logo {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  padding: 8px 10px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.96);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.12);
  overflow: hidden;
  transition: padding var(--hrms-transition);
}

.sidebar__brand-sub {
  font-size: 0.7rem;
  font-weight: 600;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  opacity: 0.75;
  padding-left: 2px;
}

.sidebar__tagline {
  margin: 0 20px 20px;
  padding: 10px 14px;
  font-size: 0.8rem;
  font-style: italic;
  line-height: 1.4;
  color: rgba(255, 255, 255, 0.7);
  background: rgba(255, 255, 255, 0.06);
  border-left: 3px solid var(--hrms-accent);
  border-radius: 0 var(--hrms-radius-sm) var(--hrms-radius-sm) 0;
}

.sidebar__nav {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  padding: 0 12px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.sidebar__link {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 11px 14px;
  border-radius: var(--hrms-radius-md);
  font-size: 0.9rem;
  font-weight: 500;
  color: rgba(255, 255, 255, 0.78);
  text-decoration: none;
  transition:
    background var(--hrms-transition),
    color var(--hrms-transition),
    padding var(--hrms-transition);
}

.sidebar__link:hover {
  color: #fff;
  background: rgba(255, 255, 255, 0.1);
}

.sidebar__link--active {
  color: #fff;
  background: linear-gradient(90deg, rgba(196, 163, 90, 0.28) 0%, rgba(255, 255, 255, 0.08) 100%);
  box-shadow: inset 3px 0 0 var(--hrms-accent);
}

.sidebar__link-label {
  white-space: nowrap;
  overflow: hidden;
}

.sidebar__footer {
  display: flex;
  flex-direction: column;
  align-items: stretch;
  gap: 8px;
  padding: 16px 12px 20px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}

.sidebar__copyright {
  margin: 0;
  padding: 0 8px;
  font-size: 0.7rem;
  opacity: 0.45;
  text-align: center;
}

.sidebar__collapse-btn {
  display: none;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 36px;
  border: 1px solid rgba(255, 255, 255, 0.14);
  border-radius: var(--hrms-radius-md);
  color: rgba(255, 255, 255, 0.78);
  background: rgba(255, 255, 255, 0.06);
  cursor: pointer;
  transition:
    background var(--hrms-transition),
    color var(--hrms-transition);
}

.sidebar__collapse-btn:hover {
  color: #fff;
  background: rgba(255, 255, 255, 0.12);
}

.sidebar__collapse-btn--desktop {
  display: none;
  position: absolute;
  top: 18px;
  right: 12px;
  width: 32px;
  height: 32px;
  padding: 0;
}

@media (min-width: 1024px) {
  .sidebar {
    transform: translateX(0);
  }

  .sidebar__backdrop {
    display: none;
  }

  .sidebar__collapse-btn--footer {
    display: flex;
  }

  .sidebar--collapsed {
    width: var(--hrms-sidebar-collapsed-width);
  }

  .sidebar--collapsed .sidebar__brand {
    padding: 16px 10px 12px;
    align-items: center;
  }

  .sidebar--collapsed .sidebar__logo {
    padding: 6px;
  }

  .sidebar--collapsed .sidebar__logo :deep(.app-logo--sidebar) {
    max-width: 40px;
  }

  .sidebar--collapsed .sidebar__nav {
    padding: 0 8px;
    align-items: center;
  }

  .sidebar--collapsed .sidebar__link {
    justify-content: center;
    width: 44px;
    padding: 11px 0;
    gap: 0;
  }

  .sidebar--collapsed .sidebar__link--active {
    box-shadow: none;
    background: rgba(196, 163, 90, 0.28);
  }

  .sidebar--collapsed .sidebar__link-label {
    position: absolute;
    width: 1px;
    height: 1px;
    padding: 0;
    margin: -1px;
    overflow: hidden;
    clip: rect(0, 0, 0, 0);
    white-space: nowrap;
    border: 0;
  }

  .sidebar--collapsed .sidebar__footer {
    padding: 12px 8px 16px;
    align-items: center;
  }

  .sidebar--collapsed .sidebar__collapse-btn--footer {
    width: 44px;
  }
}
</style>
