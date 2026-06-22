import { computed } from 'vue'
import { navigationItems } from '@/config/navigation'
import { useAuthStore } from '@/stores/auth'
import type { NavItem } from '@/types/navigation'

export function useNavigation() {
  const auth = useAuthStore()

  const visibleNavItems = computed<NavItem[]>(() =>
    navigationItems.filter((item) => item.roles.includes(auth.role)),
  )

  return { visibleNavItems }
}
