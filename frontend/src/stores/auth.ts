import { create } from 'zustand'

interface User {
  id: string
  email: string
  name: string
  department?: string
  role?: string
}

interface AuthState {
  token: string | null
  user: User | null
  isAuthenticated: boolean
  setAuth: (token: string, user: User) => void
  logout: () => void
  restoreAuth: () => void
}

export const useAuthStore = create<AuthState>((set) => ({
  token: null,
  user: null,
  isAuthenticated: false,

  setAuth: (token, user) => {
    localStorage.setItem('token', token)
    localStorage.setItem('user', JSON.stringify(user))
    set({ token, user, isAuthenticated: true })
  },

  logout: () => {
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    set({ token: null, user: null, isAuthenticated: false })
  },

  restoreAuth: () => {
    const token = localStorage.getItem('token')
    const rawUser = localStorage.getItem('user')
    const user = rawUser ? (JSON.parse(rawUser) as User) : null
    if (token) {
      set({ token, user, isAuthenticated: true })
    }
  },
}))
