import type { NavItem } from '@/types/navigation'

export const navigationItems: NavItem[] = [
  {
    id: 'dashboard',
    label: 'Dashboard',
    icon: 'dashboard',
    route: '/',
    roles: ['owner', 'recruiter'],
  },
  {
    id: 'users',
    label: 'Recruiters',
    icon: 'users',
    route: '/users',
    roles: ['owner'],
  },
  {
    id: 'clients',
    label: 'Clients',
    icon: 'clients',
    route: '/clients',
    roles: ['owner'],
  },
  {
    id: 'candidates',
    label: 'Candidates',
    icon: 'candidates',
    route: '/candidates',
    roles: ['owner', 'recruiter'],
  },
  {
    id: 'pipeline',
    label: 'Pipeline',
    icon: 'pipeline',
    route: '/pipeline',
    roles: ['owner', 'recruiter'],
  },
  {
    id: 'recruitment',
    label: 'Recruitment',
    icon: 'recruitment',
    route: '/recruitment',
    roles: ['owner', 'recruiter'],
  },
  {
    id: 'reports',
    label: 'Reports',
    icon: 'reports',
    route: '/reports',
    roles: ['owner'],
  },
  {
    id: 'settings',
    label: 'Settings',
    icon: 'settings',
    route: '/settings',
    roles: ['owner', 'recruiter'],
  },
]
