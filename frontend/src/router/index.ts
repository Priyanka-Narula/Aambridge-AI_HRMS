import { createRouter, createWebHistory } from 'vue-router'
import DashboardLayout from '@/layouts/DashboardLayout.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      component: DashboardLayout,
      children: [
        {
          path: '',
          name: 'dashboard',
          component: () => import('@/views/DashboardView.vue'),
          meta: { title: 'Dashboard' },
        },
        {
          path: 'employees',
          name: 'employees',
          component: () => import('@/views/PlaceholderView.vue'),
          meta: { title: 'Employees' },
        },
        {
          path: 'users',
          name: 'users',
          component: () => import('@/views/PlaceholderView.vue'),
          meta: { title: 'User Management' },
        },
        {
          path: 'organizations',
          name: 'organizations',
          component: () => import('@/views/PlaceholderView.vue'),
          meta: { title: 'Organizations' },
        },
        {
          path: 'recruitment',
          name: 'recruitment',
          component: () => import('@/views/PlaceholderView.vue'),
          meta: { title: 'Recruitment' },
        },
        {
          path: 'candidates',
          name: 'candidates',
          component: () => import('@/views/CandidatesView.vue'),
          meta: { title: 'Candidates' },
        },
        {
          path: 'pipeline',
          name: 'pipeline',
          component: () => import('@/views/PlaceholderView.vue'),
          meta: { title: 'Pipeline' },
        },
        {
          path: 'interviews',
          name: 'interviews',
          component: () => import('@/views/PlaceholderView.vue'),
          meta: { title: 'Interviews' },
        },
        {
          path: 'job-postings',
          name: 'job-postings',
          component: () => import('@/views/PlaceholderView.vue'),
          meta: { title: 'Job Postings' },
        },
        {
          path: 'team',
          name: 'team',
          component: () => import('@/views/PlaceholderView.vue'),
          meta: { title: 'My Team' },
        },
        {
          path: 'approvals',
          name: 'approvals',
          component: () => import('@/views/PlaceholderView.vue'),
          meta: { title: 'Approvals' },
        },
        {
          path: 'reports',
          name: 'reports',
          component: () => import('@/views/PlaceholderView.vue'),
          meta: { title: 'Reports' },
        },
        {
          path: 'settings',
          name: 'settings',
          component: () => import('@/views/PlaceholderView.vue'),
          meta: { title: 'Settings' },
        },
      ],
    },
  ],
})

router.afterEach((to) => {
  const title = (to.meta.title as string) ?? 'Aambridge AI HRMS'
  document.title = `${title} | Aambridge-AI_HRMS`
})

export default router
