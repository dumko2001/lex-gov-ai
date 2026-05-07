import * as React from "react"
import { createRoute } from '@tanstack/react-router'
import { Route as rootRoute } from './__root'
import { useActionPlanByJudgment } from "@/hooks/useActionPlans"
import { useJob } from "@/hooks/useJobs"
import { useVerifyDirective, usePublishActionPlan } from "@/hooks/useActionPlans"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent } from "@/components/ui/card"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { BASE_URL } from "@/lib/api"

import { Document, Page, pdfjs } from "react-pdf"
import { CheckCircle, Edit2, RotateCcw, ChevronLeft, ChevronRight, FileText, AlertCircle } from "lucide-react"
import "react-pdf/dist/esm/Page/AnnotationLayer.css"
import "react-pdf/dist/esm/Page/TextLayer.css"

pdfjs.GlobalWorkerOptions.workerSrc = `https://cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjs.version}/pdf.worker.min.mjs`

interface DirectiveCardProps {
  directive: {
    id: string
    action_type: string
    department: string
    deadline?: string
    description: string
    confidence: number
    source_page?: number
    status: string
  }
  onSelect: () => void
  onApprove: () => void
  onEdit: () => void
  onRedo: () => void
  isSelected: boolean
}

function DirectiveCard({ directive, onSelect, onApprove, onEdit, onRedo, isSelected }: DirectiveCardProps) {
  const confidencePct = Math.round(directive.confidence * 100)

  return (
    <Card
      onClick={onSelect}
      className={`cursor-pointer transition-all hover:shadow-md ${
        isSelected ? 'border-indigo-500 ring-1 ring-indigo-500' : ''
      }`}
    >
      <CardContent className="p-4">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className="mb-2 flex items-center gap-2">
              <Badge variant="outline">{directive.action_type}</Badge>
              <span className="text-xs text-slate-500">{directive.department}</span>
              {directive.status === 'approved' && (
                <Badge variant="success" className="text-xs">Approved</Badge>
              )}
            </div>
            <p className="text-sm text-slate-900">{directive.description}</p>
            {directive.deadline && (
              <p className="mt-1 text-xs text-slate-500">Deadline: {directive.deadline}</p>
            )}
            {directive.source_page && (
              <p className="text-xs text-indigo-600">Page {directive.source_page}</p>
            )}
          </div>
        </div>

        <div className="mt-3">
          <div className="mb-1 flex items-center justify-between text-xs">
            <span className="text-slate-500">Confidence</span>
            <span className={confidencePct >= 80 ? 'text-green-600' : confidencePct >= 50 ? 'text-amber-600' : 'text-red-600'}>
              {confidencePct}%
            </span>
          </div>
          <div className="h-2 w-full overflow-hidden rounded-full bg-slate-100">
            <div
              className={`h-full rounded-full transition-all ${
                confidencePct >= 80
                  ? 'bg-green-500'
                  : confidencePct >= 50
                  ? 'bg-amber-500'
                  : 'bg-red-500'
              }`}
              style={{ width: `${confidencePct}%` }}
            />
          </div>
        </div>

        <div className="mt-3 flex items-center gap-2">
          <Button
            size="sm"
            variant="outline"
            className="h-7 text-xs border-green-200 text-green-700 hover:bg-green-50"
            onClick={(e) => {
              e.stopPropagation()
              onApprove()
            }}
          >
            <CheckCircle className="mr-1 h-3 w-3" />
            Approve
          </Button>
          <Button
            size="sm"
            variant="outline"
            className="h-7 text-xs"
            onClick={(e) => {
              e.stopPropagation()
              onEdit()
            }}
          >
            <Edit2 className="mr-1 h-3 w-3" />
            Edit
          </Button>
          <Button
            size="sm"
            variant="outline"
            className="h-7 text-xs border-red-200 text-red-700 hover:bg-red-50"
            onClick={(e) => {
              e.stopPropagation()
              onRedo()
            }}
          >
            <RotateCcw className="mr-1 h-3 w-3" />
            Redo
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}

function VerifyPage() {
  const { jobId } = Route.useParams()
  const { data: job } = useJob(jobId)
  const { data: actionPlan } = useActionPlanByJudgment(job?.judgment_id || '')

  const [selectedDirectiveId, setSelectedDirectiveId] = React.useState<string | null>(null)
  const [pdfPage, setPdfPage] = React.useState(1)
  const [numPages, setNumPages] = React.useState(0)
  const [editModalOpen, setEditModalOpen] = React.useState(false)
  const [redoModalOpen, setRedoModalOpen] = React.useState(false)
  const [editingDirective, setEditingDirective] = React.useState<any>(null)
  const [editForm, setEditForm] = React.useState({ action_type: '', department: '', deadline: '', description: '' })
  const [redoNote, setRedoNote] = React.useState('')

  const verifyMutation = useVerifyDirective()
  const publishMutation = usePublishActionPlan()

  const selectedDirective = actionPlan?.directives.find((d) => d.id === selectedDirectiveId)

  const handleSelectDirective = (directive: any) => {
    setSelectedDirectiveId(directive.id)
    if (directive.source_page) {
      setPdfPage(directive.source_page)
    }
  }

  const handleApprove = (directiveId: string) => {
    if (!actionPlan) return
    verifyMutation.mutate({
      actionPlanId: actionPlan.id,
      directiveId,
      data: { status: 'approved' },
    })
  }

  const handleApproveAll = () => {
    if (!actionPlan) return
    actionPlan.directives.forEach((d) => {
      if (d.status === 'pending') {
        verifyMutation.mutate({
          actionPlanId: actionPlan.id,
          directiveId: d.id,
          data: { status: 'approved' },
        })
      }
    })
  }

  const openEdit = (directive: any) => {
    setEditingDirective(directive)
    setEditForm({
      action_type: directive.action_type,
      department: directive.department,
      deadline: directive.deadline || '',
      description: directive.description,
    })
    setEditModalOpen(true)
  }

  const handleEditSave = () => {
    if (!actionPlan || !editingDirective) return
    verifyMutation.mutate(
      {
        actionPlanId: actionPlan.id,
        directiveId: editingDirective.id,
        data: {
          status: 'approved',
          corrections: editForm,
        },
      },
      {
        onSuccess: () => setEditModalOpen(false),
      }
    )
  }

  const openRedo = (directive: any) => {
    setEditingDirective(directive)
    setRedoNote('')
    setRedoModalOpen(true)
  }

  const handleRedoSave = () => {
    if (!actionPlan || !editingDirective) return
    verifyMutation.mutate(
      {
        actionPlanId: actionPlan.id,
        directiveId: editingDirective.id,
        data: {
          status: 'rejected',
          note: redoNote,
        },
      },
      {
        onSuccess: () => setRedoModalOpen(false),
      }
    )
  }

  const overallConfidence = actionPlan
    && actionPlan.directives.length > 0
    ? Math.round(
        (actionPlan.directives.reduce((sum, d) => sum + d.confidence, 0) /
          actionPlan.directives.length) *
          100
      )
    : 0

  const pdfUrl = job?.judgment_id
    ? `${BASE_URL}/judgments/${job.judgment_id}/pdf`
    : null

  return (
    <div className="flex h-[calc(100vh-4rem)] flex-col">
      {/* Top Bar */}
      <div className="flex items-center justify-between border-b bg-white px-6 py-3">
        <div className="flex items-center gap-4">
          <FileText className="h-5 w-5 text-indigo-600" />
          <div>
            <h2 className="text-sm font-semibold text-slate-900">
              Verification: {job?.judgment_id?.slice(0, 8) || jobId}
            </h2>
            <p className="text-xs text-slate-500">
              {actionPlan?.directives.length ?? 0} directives found
            </p>
          </div>
        </div>

        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <span className="text-xs text-slate-500">Overall Confidence</span>
            <div className="h-2 w-24 overflow-hidden rounded-full bg-slate-100">
              <div
                className={`h-full rounded-full ${
                  overallConfidence >= 80
                    ? 'bg-green-500'
                    : overallConfidence >= 50
                    ? 'bg-amber-500'
                    : 'bg-red-500'
                }`}
                style={{ width: `${overallConfidence}%` }}
              />
            </div>
            <span className="text-xs font-medium">{overallConfidence}%</span>
          </div>
          <Button
            size="sm"
            className="bg-indigo-600 hover:bg-indigo-700"
            onClick={handleApproveAll}
            disabled={verifyMutation.isPending}
          >
            <CheckCircle className="mr-1 h-4 w-4" />
            Approve All
          </Button>
          <Button
            size="sm"
            variant="outline"
            onClick={() => actionPlan && publishMutation.mutate(actionPlan.id)}
            disabled={publishMutation.isPending}
          >
            Publish
          </Button>
        </div>
      </div>

      {/* Split Screen */}
      <div className="flex flex-1 overflow-hidden">
        {/* Left Panel - Directives */}
        <div className="flex w-1/2 flex-col border-r bg-slate-50">
          <div className="flex-1 overflow-y-auto p-4">
            <div className="space-y-3">
              {actionPlan?.directives.map((directive) => (
                <DirectiveCard
                  key={directive.id}
                  directive={directive}
                  isSelected={selectedDirectiveId === directive.id}
                  onSelect={() => handleSelectDirective(directive)}
                  onApprove={() => handleApprove(directive.id)}
                  onEdit={() => openEdit(directive)}
                  onRedo={() => openRedo(directive)}
                />
              ))}
              {!actionPlan && (
                <div className="flex flex-col items-center justify-center py-12 text-slate-500">
                  <AlertCircle className="mb-2 h-8 w-8" />
                  <p>Loading action plan...</p>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Right Panel - PDF */}
        <div className="flex w-1/2 flex-col bg-white">
          <div className="flex items-center justify-between border-b px-4 py-2">
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="icon"
                className="h-8 w-8"
                onClick={() => setPdfPage((p) => Math.max(1, p - 1))}
                disabled={pdfPage <= 1}
              >
                <ChevronLeft className="h-4 w-4" />
              </Button>
              <span className="text-sm text-slate-600">
                Page {pdfPage} of {numPages}
              </span>
              <Button
                variant="outline"
                size="icon"
                className="h-8 w-8"
                onClick={() => setPdfPage((p) => Math.min(numPages, p + 1))}
                disabled={pdfPage >= numPages}
              >
                <ChevronRight className="h-4 w-4" />
              </Button>
            </div>
            {selectedDirective?.source_page && (
              <Badge variant="secondary" className="text-xs">
                Source: Page {selectedDirective.source_page}
              </Badge>
            )}
          </div>

          <div className="flex-1 overflow-auto p-4">
            {pdfUrl ? (
              <Document
                file={pdfUrl}
                onLoadSuccess={({ numPages }) => setNumPages(numPages)}
                loading={
                  <div className="flex h-96 items-center justify-center text-slate-500">
                    Loading PDF...
                  </div>
                }
                error={
                  <div className="flex h-96 items-center justify-center text-slate-500">
                    Failed to load PDF.
                  </div>
                }
              >
                <Page
                  pageNumber={pdfPage}
                  width={600}
                  renderTextLayer
                  renderAnnotationLayer
                />
              </Document>
            ) : (
              <div className="flex h-96 items-center justify-center text-slate-500">
                No PDF available.
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Edit Modal */}
      <Dialog open={editModalOpen} onOpenChange={setEditModalOpen}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>Edit Directive</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">Action Type</label>
              <Input
                value={editForm.action_type}
                onChange={(e) => setEditForm((f) => ({ ...f, action_type: e.target.value }))}
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">Department</label>
              <Input
                value={editForm.department}
                onChange={(e) => setEditForm((f) => ({ ...f, department: e.target.value }))}
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">Deadline</label>
              <Input
                type="date"
                value={editForm.deadline}
                onChange={(e) => setEditForm((f) => ({ ...f, deadline: e.target.value }))}
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">Description</label>
              <Textarea
                value={editForm.description}
                onChange={(e) => setEditForm((f) => ({ ...f, description: e.target.value }))}
                rows={4}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setEditModalOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleEditSave} disabled={verifyMutation.isPending}>
              Save Changes
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Redo Modal */}
      <Dialog open={redoModalOpen} onOpenChange={setRedoModalOpen}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>Request Redo</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <p className="text-sm text-slate-500">
              Provide a correction note to help the AI regenerate this directive.
            </p>
            <Textarea
              value={redoNote}
              onChange={(e) => setRedoNote(e.target.value)}
              placeholder="e.g., Wrong department assigned, deadline should be 30 days..."
              rows={5}
            />
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setRedoModalOpen(false)}>
              Cancel
            </Button>
            <Button
              variant="destructive"
              onClick={handleRedoSave}
              disabled={verifyMutation.isPending || !redoNote.trim()}
            >
              Submit Redo
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}

export const Route = createRoute({
  getParentRoute: () => rootRoute,
  path: '/verify/$jobId',
  component: VerifyPage,
})
