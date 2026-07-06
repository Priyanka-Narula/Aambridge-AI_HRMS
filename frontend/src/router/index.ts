import { createRouter, createWebHistory } from 'vue-router'
import DashboardLayout from '@/layouts/DashboardLayout.vue'
import { useAuthStore } from '@/stores/auth'
import type { UserRole } from '@/types/auth'

declare module 'vue-router' {
  interface RouteMeta {
    title?: string
    requiresAuth?: boolean
    roles?: UserRole[]
    guestOnly?: boolean
  }
}

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: () => import('@/views/LoginView.vue'),
      meta: { title: 'Login', guestOnly: true },
    },
    {
      path: '/unauthorized',
      name: 'unauthorized',
      component: () => import('@/views/UnauthorizedView.vue'),
      meta: { title: 'Unauthorized', requiresAuth: true },
    },
    {
      path: '/',
      component: DashboardLayout,
      meta: { requiresAuth: true },
      children: [
        {
          path: '',
          name: 'dashboard',
          component: () => import('@/views/DashboardView.vue'),
          meta: { title: 'Dashboard' },
        },
        {
          path: 'users',
          name: 'users',
          component: () => import('@/views/RecruitersView.vue'),
          meta: { title: 'Recruiters', roles: ['owner'] },
        },
        {
          path: 'clients',
          name: 'clients',
          component: () => import('@/views/ClientsView.vue'),
          meta: { title: 'Clients', roles: ['owner'] },
        },
        {
          path: 'candidates',
          name: 'candidates',
          component: () => import('@/views/CandidatesView.vue'),
          meta: { title: 'Candidates', roles: ['owner', 'recruiter'] },
        },
        {
          path: 'candidates/upload',
          name: 'cv-upload',
          component: () => import('@/views/CvUploadView.vue'),
          meta: { title: 'Upload CV', roles: ['owner', 'recruiter'] },
        },
        {
          path: 'candidates/verify',
          name: 'cv-verify',
          component: () => import('@/views/CvVerifyView.vue'),
          meta: { title: 'Verify Candidate', roles: ['owner', 'recruiter'] },
        },
        {
          path: 'pipeline',
          name: 'pipeline',
          component: () => import('@/views/PlaceholderView.vue'),
          meta: { title: 'Pipeline', roles: ['owner', 'recruiter'] },
        },
        {
          path: 'recruitment',
          name: 'recruitment',
          component: () => import('@/views/PlaceholderView.vue'),
          meta: { title: 'Recruitment', roles: ['owner', 'recruiter'] },
        },
        {
          path: 'reports',
          name: 'reports',
          component: () => import('@/views/PlaceholderView.vue'),
          meta: { title: 'Reports', roles: ['owner'] },
        },
        {
          path: 'settings',
          name: 'settings',
          component: () => import('@/views/PlaceholderView.vue'),
          meta: { title: 'Settings', roles: ['owner', 'recruiter'] },
        },
      ],
    },
  ],
})

router.beforeEach(async (to) => {
  const auth = useAuthStore()
  await auth.initialize()

  if (to.meta.guestOnly && auth.isAuthenticated) {
    return { name: 'dashboard' }
  }

  if (to.meta.requiresAuth && !auth.isAuthenticated) {
    return { name: 'login', query: { redirect: to.fullPath } }
  }

  const requiredRoles = to.matched.flatMap((record) => record.meta.roles ?? [])
  if (requiredRoles.length && auth.role && !requiredRoles.includes(auth.role)) {
    return { name: 'unauthorized' }
  }
})

router.afterEach((to) => {
  const title = to.meta.title ?? 'Aambridge AI HRMS'
  document.title = `${title} | Aambridge-AI_HRMS`
})

export default router
