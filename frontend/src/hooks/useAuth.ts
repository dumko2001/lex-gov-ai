import { useAuthStore } from '@/stores/auth'

export function useAuth() {
  const { user, isAuthenticated, setAuth, logout, restoreAuth } = useAuthStore()

  return {
    user,
    isAuthenticated,
    setAuth,
    logout,
    restoreAuth,
  }
}
