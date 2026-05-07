import { useQuery } from '@tanstack/react-query'
import api from '@/lib/api'

export interface Job {
  id: string
  judgment_id: string
  status: 'pending' | 'processing' | 'completed' | 'failed'
  created_at: string
  updated_at: string
  error_message?: string
}

export function useJob(id: string) {
  return useQuery({
    queryKey: ['jobs', id],
    queryFn: async () => {
      try {
        return await api.get<Job>(`/jobs/${id}`)
      } catch {
        return await api.get<Job>(`/jobs/judgment/${id}`)
      }
    },
    enabled: !!id,
  })
}

export function useJobStatus(id: string, refetchInterval?: number) {
  return useQuery({
    queryKey: ['jobs', id, 'status'],
    queryFn: () => api.get<{ status: string; progress?: number }>(`/jobs/${id}/status`),
    enabled: !!id,
    refetchInterval: refetchInterval ?? false,
  })
}
