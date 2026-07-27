<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useNotificationsStore } from '@/stores/notifications'

const props = defineProps<{
  sidebarCollapsed?: boolean
}>()

defineEmits<{
  toggleSidebar: []
}>()

const router = useRouter()
const auth = useAuthStore()
const notifications = useNotificationsStore()
const showUserMenu = ref(false)
const showNotifications = ref(false)

const displayName = computed(() => {
  if (!auth.user) return ''
  return `${auth.user.first_name} ${auth.user.last_name}`
})

const avatarInitials = computed(() => {
  if (!auth.user) return ''
  return `${auth.user.first_name[0]}${auth.user.last_name[0]}`.toUpperCase()
})

function notificationTone(type: string) {
  if (type === 'candidate.rejected' || type === 'job.closed') return 'danger'
  if (type === 'placement.completed' || type === 'candidate.approved') return 'success'
  return 'default'
}

function formatNotifTime(iso: string | null) {
  if (!iso) return ''
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return iso
  const diffMs = Date.now() - d.getTime()
  const mins = Math.floor(diffMs / 60000)
  if (mins < 1) return 'Just now'
  if (mins < 60) return `${mins}m ago`
  const hours = Math.floor(mins / 60)
  if (hours < 24) return `${hours}h ago`
  const days = Math.floor(hours / 24)
  if (days < 7) return `${days}d ago`
  return d.toLocaleDateString('en-IN', { day: '2-digit', month: 'short' })
}

function onDateChange(field: 'start' | 'end', event: Event) {
  const value = (event.target as HTMLInputElement).value
  auth.setDateRange({ ...auth.dateRange, [field]: value })
}

function toggleUserMenu() {
  showUserMenu.value = !showUserMenu.value
  showNotifications.value = false
}

function toggleNotifications() {
  showNotifications.value = !showNotifications.value
  showUserMenu.value = false
  if (showNotifications.value && !notifications.items.length) {
    void notifications.load()
  }
}

function closeMenus() {
  showUserMenu.value = false
  showNotifications.value = false
}

function handleLogout() {
  closeMenus()
  auth.logout()
  router.push({ name: 'login' })
}

onMounted(() => {
  void notifications.load()
})
</script>

<template>
  <header class="topbar">
    <div class="topbar__left">
      <button
        type="button"
        class="topbar__menu-btn"
        :aria-label="props.sidebarCollapsed ? 'Expand navigation' : 'Toggle navigation menu'"
        :title="props.sidebarCollapsed ? 'Expand navigation' : 'Collapse navigation'"
        @click="$emit('toggleSidebar')"
      >
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M4 6h16M4 12h16M4 18h16" />
        </svg>
      </button>

      <div class="topbar__brand">
        <h1 class="topbar__title">Aambridge-AI_HRMS</h1>
        <span class="topbar__badge">{{ auth.roleLabel }}</span>
      </div>
    </div>

    <div class="topbar__center">
      <div class="topbar__date-filter" role="group" aria-label="Date range filter">
        <svg class="topbar__date-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
          <rect x="3" y="4" width="18" height="18" rx="2" />
          <path d="M16 2v4M8 2v4M3 10h18" />
        </svg>
        <label class="sr-only" for="date-start">Start date</label>
        <input
          id="date-start"
          type="date"
          class="topbar__date-input"
          :value="auth.dateRange.start"
          :max="auth.dateRange.end"
          @change="onDateChange('start', $event)"
        />
        <span class="topbar__date-sep" aria-hidden="true">to</span>
        <label class="sr-only" for="date-end">End date</label>
        <input
          id="date-end"
          type="date"
          class="topbar__date-input"
          :value="auth.dateRange.end"
          :min="auth.dateRange.start"
          @change="onDateChange('end', $event)"
        />
      </div>
    </div>

    <div class="topbar__actions">
      <div class="topbar__action-wrap">
        <button
          type="button"
          class="topbar__icon-btn"
          aria-label="Notifications"
          :aria-expanded="showNotifications"
          @click="toggleNotifications"
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75">
            <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" />
            <path d="M13.73 21a2 2 0 0 1-3.46 0" />
          </svg>
          <span v-if="notifications.unreadCount > 0" class="topbar__badge-count">
            {{ notifications.unreadCount > 9 ? '9+' : notifications.unreadCount }}
          </span>
        </button>

        <div v-if="showNotifications" class="topbar__dropdown topbar__dropdown--notifications">
          <div class="topbar__dropdown-header">
            <span>Notifications</span>
            <em v-if="notifications.unreadCount">{{ notifications.unreadCount }} new</em>
          </div>
          <div v-if="notifications.loading && !notifications.items.length" class="topbar__notif-empty">
            Loading…
          </div>
          <div v-else-if="!notifications.items.length" class="topbar__notif-empty">
            You're all caught up
          </div>
          <ul v-else class="topbar__notif-list">
            <li
              v-for="n in notifications.items"
              :key="n.id"
              class="topbar__notif-item"
              :data-tone="notificationTone(n.type)"
            >
              <i class="topbar__notif-dot" aria-hidden="true" />
              <div class="topbar__notif-body">
                <p>{{ n.title }}</p>
                <span>{{ n.description }}</span>
                <time>{{ formatNotifTime(n.created_at) }}</time>
              </div>
            </li>
          </ul>
        </div>
      </div>

      <RouterLink to="/settings" class="topbar__icon-btn" aria-label="Profile" @click="closeMenus">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75">
          <circle cx="12" cy="12" r="3" />
          <path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42" />
        </svg>
      </RouterLink>

      <div class="topbar__action-wrap">
        <button
          type="button"
          class="topbar__user-btn"
          :aria-expanded="showUserMenu"
          aria-label="User menu"
          @click="toggleUserMenu"
        >
          <span class="topbar__avatar">{{ avatarInitials }}</span>
          <span class="topbar__user-info">
            <span class="topbar__user-name">{{ displayName }}</span>
            <span class="topbar__user-role">{{ auth.roleLabel }}</span>
          </span>
          <svg class="topbar__chevron" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M6 9l6 6 6-6" />
          </svg>
        </button>

        <div v-if="showUserMenu" class="topbar__dropdown topbar__dropdown--user">
          <div class="topbar__dropdown-user-header">
            <span class="topbar__avatar topbar__avatar--lg">{{ avatarInitials }}</span>
            <div>
              <strong>{{ displayName }}</strong>
              <span>{{ auth.user?.email }}</span>
            </div>
          </div>
          <hr class="topbar__dropdown-divider" />
          <RouterLink to="/settings" class="topbar__dropdown-link" @click="closeMenus">Profile</RouterLink>
          <button type="button" class="topbar__dropdown-link topbar__dropdown-link--muted" @click="handleLogout">Sign out</button>
        </div>
      </div>
    </div>

    <div
      v-if="showUserMenu || showNotifications"
      class="topbar__overlay"
      @click="closeMenus"
    />
  </header>
</template>

<style scoped>
.topbar {
  position: sticky;
  top: 0;
  z-index: 100;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  height: var(--hrms-topbar-height);
  padding: 0 20px 0 16px;
  background: var(--hrms-surface-elevated);
  border-bottom: 1px solid var(--hrms-border);
  box-shadow: var(--hrms-shadow-sm);
}

.topbar__left {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 0;
}

.topbar__menu-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 38px;
  height: 38px;
  border: none;
  border-radius: var(--hrms-radius-sm);
  color: var(--hrms-text);
  background: transparent;
  cursor: pointer;
  transition: background var(--hrms-transition);
}

.topbar__menu-btn:hover {
  background: var(--hrms-secondary);
}

.topbar__brand {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}

.topbar__title {
  margin: 0;
  font-family: var(--hrms-font-display);
  font-size: 1.35rem;
  font-weight: 600;
  color: var(--hrms-primary-dark);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  letter-spacing: 0.01em;
}

.topbar__badge {
  display: none;
  padding: 3px 10px;
  font-size: 0.68rem;
  font-weight: 600;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--hrms-primary);
  background: var(--hrms-secondary);
  border-radius: 999px;
  white-space: nowrap;
}

.topbar__center {
  flex: 1;
  display: flex;
  justify-content: center;
  min-width: 0;
}

.topbar__date-filter {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 12px;
  background: var(--hrms-surface-muted);
  border: 1px solid var(--hrms-border);
  border-radius: var(--hrms-radius-md);
}

.topbar__date-icon {
  color: var(--hrms-primary-muted);
  flex-shrink: 0;
}

.topbar__date-input {
  border: none;
  background: transparent;
  font-family: inherit;
  font-size: 0.8rem;
  color: var(--hrms-text);
  cursor: pointer;
}

.topbar__date-input:focus {
  outline: none;
}

.topbar__date-sep {
  font-size: 0.75rem;
  color: var(--hrms-text-muted);
}

.topbar__actions {
  display: flex;
  align-items: center;
  gap: 6px;
}

.topbar__action-wrap {
  position: relative;
}

.topbar__icon-btn {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 38px;
  height: 38px;
  border: none;
  border-radius: var(--hrms-radius-sm);
  color: var(--hrms-text-muted);
  background: transparent;
  cursor: pointer;
  transition:
    background var(--hrms-transition),
    color var(--hrms-transition);
}

.topbar__icon-btn:hover {
  color: var(--hrms-primary);
  background: var(--hrms-secondary);
}

.topbar__badge-count {
  position: absolute;
  top: 4px;
  right: 4px;
  min-width: 16px;
  height: 16px;
  padding: 0 4px;
  font-size: 0.65rem;
  font-weight: 700;
  line-height: 16px;
  text-align: center;
  color: #fff;
  background: var(--hrms-primary);
  border-radius: 999px;
}

.topbar__user-btn {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 4px 8px 4px 4px;
  border: 1px solid var(--hrms-border);
  border-radius: var(--hrms-radius-md);
  background: var(--hrms-surface-elevated);
  cursor: pointer;
  transition: border-color var(--hrms-transition);
}

.topbar__user-btn:hover {
  border-color: var(--hrms-primary-muted);
}

.topbar__avatar {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  font-size: 0.75rem;
  font-weight: 700;
  color: var(--hrms-primary-dark);
  background: linear-gradient(135deg, var(--hrms-accent-soft) 0%, var(--hrms-secondary-deep) 100%);
  border-radius: 50%;
  flex-shrink: 0;
}

.topbar__avatar--lg {
  width: 40px;
  height: 40px;
  font-size: 0.85rem;
}

.topbar__user-info {
  display: none;
  flex-direction: column;
  align-items: flex-start;
  text-align: left;
}

.topbar__user-name {
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--hrms-text);
  line-height: 1.2;
}

.topbar__user-role {
  font-size: 0.7rem;
  color: var(--hrms-text-muted);
}

.topbar__chevron {
  display: none;
  color: var(--hrms-text-muted);
}

.topbar__dropdown {
  position: absolute;
  top: calc(100% + 8px);
  right: 0;
  z-index: 300;
  min-width: 280px;
  background: var(--hrms-surface-elevated);
  border: 1px solid var(--hrms-border);
  border-radius: var(--hrms-radius-lg);
  box-shadow: var(--hrms-shadow-lg);
  overflow: hidden;
}

.topbar__dropdown-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 14px 16px;
  font-weight: 600;
  font-size: 0.9rem;
  border-bottom: 1px solid var(--hrms-border);
}

.topbar__dropdown-header em {
  font-style: normal;
  font-size: 0.72rem;
  font-weight: 600;
  color: var(--hrms-primary);
  background: var(--hrms-secondary);
  padding: 2px 8px;
  border-radius: 999px;
}

.topbar__notif-empty {
  padding: 28px 16px;
  text-align: center;
  font-size: 0.85rem;
  color: var(--hrms-text-muted);
}

.topbar__notif-list {
  list-style: none;
  margin: 0;
  padding: 0;
  max-height: 320px;
  overflow-y: auto;
}

.topbar__notif-item {
  display: flex;
  gap: 10px;
  padding: 12px 16px;
  border-bottom: 1px solid var(--hrms-border);
  transition: background var(--hrms-transition);
}

.topbar__notif-item:hover {
  background: color-mix(in srgb, var(--hrms-secondary) 60%, white);
}

.topbar__notif-item:last-child {
  border-bottom: none;
}

.topbar__notif-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  margin-top: 6px;
  flex-shrink: 0;
  background: var(--hrms-primary);
}

.topbar__notif-item[data-tone='success'] .topbar__notif-dot {
  background: #22c55e;
}

.topbar__notif-item[data-tone='danger'] .topbar__notif-dot {
  background: #ef4444;
}

.topbar__notif-body p {
  margin: 0 0 2px;
  font-size: 0.84rem;
  font-weight: 600;
  line-height: 1.35;
  color: var(--hrms-text);
}

.topbar__notif-body span {
  display: block;
  font-size: 0.78rem;
  color: var(--hrms-text-muted);
  line-height: 1.35;
}

.topbar__notif-body time {
  display: block;
  margin-top: 4px;
  font-size: 0.72rem;
  color: var(--hrms-text-muted);
}

.topbar__dropdown-user-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
}

.topbar__dropdown-user-header strong {
  display: block;
  font-size: 0.9rem;
}

.topbar__dropdown-user-header span {
  font-size: 0.8rem;
  color: var(--hrms-text-muted);
}

.topbar__dropdown-divider {
  margin: 0;
  border: none;
  border-top: 1px solid var(--hrms-border);
}

.topbar__dropdown-link {
  display: block;
  width: 100%;
  padding: 12px 16px;
  border: none;
  font-family: inherit;
  font-size: 0.85rem;
  text-align: left;
  color: var(--hrms-text);
  background: transparent;
  cursor: pointer;
  transition: background var(--hrms-transition);
}

.topbar__dropdown-link:hover {
  background: var(--hrms-secondary);
}

.topbar__dropdown-link--muted {
  color: var(--hrms-text-muted);
}

.topbar__overlay {
  position: fixed;
  inset: 0;
  z-index: 50;
}

.sr-only {
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

@media (min-width: 768px) {
  .topbar__badge {
    display: inline-block;
  }

  .topbar__user-info {
    display: flex;
  }

  .topbar__chevron {
    display: block;
  }
}

@media (min-width: 1024px) {
  .topbar__menu-btn {
    display: flex;
  }
}

@media (max-width: 767px) {
  .topbar__center {
    display: none;
  }

  .topbar__title {
    font-size: 1rem;
  }
}
</style>
