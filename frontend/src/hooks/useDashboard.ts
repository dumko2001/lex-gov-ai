import { useQuery } from '@tanstack/react-query'
import api from '@/lib/api'

export interface DashboardItem {
  id: string
  case_id: string
  judgment_id: string
  directive_number: number
  action_type: string
  responsible_dept: string
  deadline_explicit?: string
  deadline_inferred?: string
  status: string
  days_remaining?: number
  source_page?: number
}

export interface DashboardSummary {
  total: number
  urgent: number
  upcoming: number
  actioned: number
}

export interface Alert {
  id: string
  alert_type: string
  message: string
  recipient_dept: string
  created_at: string
  is_read: boolean
}

interface DashboardResponse {
  summary: DashboardSummary
  directives: DashboardItem[]
}

export function useDashboard(department?: string) {
  const dept = department || 'Revenue'
  return useQuery({
    queryKey: ['dashboard', dept],
    queryFn: async () => {
      const res = await api.get<DashboardResponse>(`/dashboard/?department=${encodeURIComponent(dept)}`)
      return res.directives
    },
  })
}

export function useDashboardSummary(department?: string) {
  const dept = department || 'Revenue'
  return useQuery({
    queryKey: ['dashboard', 'summary', dept],
    queryFn: async () => {
      const res = await api.get<DashboardResponse>(`/dashboard/?department=${encodeURIComponent(dept)}`)
      return res.summary
    },
  })
}

export function useAlerts(department?: string) {
  const dept = department || 'Revenue'
  return useQuery({
    queryKey: ['dashboard', 'alerts', dept],
    queryFn: () => api.get<Alert[]>(`/dashboard/alerts?department=${encodeURIComponent(dept)}`),
  })
}
