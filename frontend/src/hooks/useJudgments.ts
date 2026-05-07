import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import api, { BASE_URL } from '@/lib/api'

export interface Judgment {
  id: string
  title: string
  source_url?: string
  file_path?: string
  date?: string
  status: string
  created_at: string
}

export function useJudgments() {
  return useQuery({
    queryKey: ['judgments'],
    queryFn: () => api.get<Judgment[]>('/judgments/'),
  })
}

export function useJudgment(id: string) {
  return useQuery({
    queryKey: ['judgments', id],
    queryFn: () => api.get<Judgment>(`/judgments/${id}`),
    enabled: !!id,
  })
}

export function useUploadJudgment() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (file: File) => {
      const formData = new FormData()
      formData.append('file', file)
      formData.append('ccms_case_id', file.name.replace(/\.pdf$/i, ''))

      const token = localStorage.getItem('token')
      const headers: Record<string, string> = {}
      if (token) headers.Authorization = `Bearer ${token}`
      const response = await fetch(`${BASE_URL}/judgments/upload`, { method: 'POST', headers, body: formData })

      if (!response.ok) {
        throw new Error('Upload failed')
      }

      return response.json()
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['judgments'] })
    },
  })
}
