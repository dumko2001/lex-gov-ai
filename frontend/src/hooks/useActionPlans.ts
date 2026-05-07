import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import api from '@/lib/api'

export interface Directive {
  id: string
  action_type: string
  department: string
  deadline?: string
  description: string
  confidence: number
  source_page?: number
  status: 'pending' | 'approved' | 'rejected' | 'actioned'
}

export interface ActionPlan {
  id: string
  job_id: string
  judgment_id: string
  status: string
  directives: Directive[]
  created_at: string
}

interface RawDirective {
  id: string
  action_type: string
  responsible_dept: string
  deadline_explicit?: string
  deadline_inferred?: string
  source_page?: number
  source_text?: string
  confidence_score?: number
  status: string
}

interface RawActionPlan {
  id: string
  job_id: string
  judgment_id: string
  status: string
  directives: RawDirective[]
  created_at: string
}

function normalizeDirectiveStatus(status: string): Directive['status'] {
  if (status === 'VERIFIED') return 'approved'
  if (status === 'REJECTED') return 'rejected'
  if (status === 'ACTIONED') return 'actioned'
  return 'pending'
}

function mapActionPlan(raw: RawActionPlan): ActionPlan {
  return {
    id: raw.id,
    job_id: raw.job_id,
    judgment_id: raw.judgment_id,
    status: raw.status,
    created_at: raw.created_at,
    directives: raw.directives.map((d) => ({
      id: d.id,
      action_type: d.action_type,
      department: d.responsible_dept,
      deadline: d.deadline_explicit || d.deadline_inferred,
      description: d.source_text || `${d.action_type} directive`,
      confidence: d.confidence_score ?? 0,
      source_page: d.source_page,
      status: normalizeDirectiveStatus(d.status),
    })),
  }
}

export function useActionPlan(id: string) {
  return useQuery({
    queryKey: ['action-plans', id],
    queryFn: async () => {
      const raw = await api.get<RawActionPlan>(`/action-plans/${id}`)
      return mapActionPlan(raw)
    },
    enabled: !!id,
  })
}

export function useActionPlanByJudgment(judgmentId: string) {
  return useQuery({
    queryKey: ['action-plans', 'judgment', judgmentId],
    queryFn: async () => {
      const raw = await api.get<RawActionPlan>(`/action-plans/judgment/${judgmentId}`)
      return mapActionPlan(raw)
    },
    enabled: !!judgmentId,
  })
}

export function useVerifyDirective() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({
      actionPlanId,
      directiveId,
      data,
    }: {
      actionPlanId: string
      directiveId: string
      data: {
        status: string
        corrections?: Record<string, unknown>
        note?: string
      }
    }) => {
      const actionType = data.status === 'approved' ? 'APPROVE' : data.status === 'rejected' ? 'REDO' : 'EDIT'
      return api.post(`/action-plans/${actionPlanId}/directives/${directiveId}/verify`, {
        action_type: actionType,
        edited_value: data.corrections,
        correction_note: data.note,
      })
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['action-plans', variables.actionPlanId] })
      queryClient.invalidateQueries({ queryKey: ['action-plans', 'judgment'] })
    },
  })
}

export function usePublishActionPlan() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (actionPlanId: string) =>
      api.post(`/action-plans/${actionPlanId}/publish`, {}),
    onSuccess: (_, actionPlanId) => {
      queryClient.invalidateQueries({ queryKey: ['action-plans', actionPlanId] })
      queryClient.invalidateQueries({ queryKey: ['dashboard'] })
    },
  })
}
