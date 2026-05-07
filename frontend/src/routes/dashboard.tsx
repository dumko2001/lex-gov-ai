import * as React from "react"
import { createRoute } from '@tanstack/react-router'
import { Route as rootRoute } from './__root'
import { useDashboard, useDashboardSummary, type DashboardItem } from "@/hooks/useDashboard"
import { useUIStore } from "@/stores/ui"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { cn } from "@/lib/utils"
import {
  AlertTriangle,
  ArrowRight,
  BadgeCheck,
  Building2,
  CalendarClock,
  CheckCircle2,
  ClipboardCheck,
  FileSearch,
  Gavel,
  Highlighter,
  RotateCcw,
  ShieldCheck,
  SlidersHorizontal,
} from "lucide-react"

type WorkspaceMode = "operator" | "department"

type ReviewItem = {
  id: string
  caseId: string
  title: string
  parties: string
  orderDate: string
  actionType: string
  department: string
  deadline: string
  confidence: number
  sourcePage: number
  paragraph: string
  resolvedDirective: string
  status: string
}

type TrustedRecord = DashboardItem & {
  directive_text: string
  parties: string
  order_date: string
}

const reviewQueueSeed: ReviewItem[] = [
  {
    id: "op-1",
    caseId: "WP 18422/2025",
    title: "Revenue mutation to be reconsidered",
    parties: "Smt. Kavitha R. vs State of Karnataka",
    orderDate: "2026-04-30",
    actionType: "COMPLY",
    department: "Revenue",
    deadline: "2026-05-30",
    confidence: 0.87,
    sourcePage: 48,
    paragraph: "Respondent No. 3 shall consider the representation within thirty days from receipt of this order.",
    resolvedDirective: "The Tahsildar, Bengaluru East Taluk, must consider Kavitha R.'s representation and pass a reasoned order within thirty days of receiving the judgement.",
    status: "Pending officer sign-off",
  },
  {
    id: "op-2",
    caseId: "WA 992/2025",
    title: "Appeal decision required before limitation expires",
    parties: "Urban Development Authority vs M. Raghavendra",
    orderDate: "2026-04-22",
    actionType: "CONSIDER_APPEAL",
    department: "Law",
    deadline: "2026-06-21",
    confidence: 0.74,
    sourcePage: 5,
    paragraph: "The appealable finding turns on acquisition notice service and limitation is to be calculated from the date of order.",
    resolvedDirective: "The Law Department must decide whether to file an appeal for the Urban Development Authority before the sixty-day limitation window closes.",
    status: "Needs close review",
  },
  {
    id: "op-3",
    caseId: "WP 21109/2025",
    title: "Police protection request routed to Home",
    parties: "Nagaraj S. vs Commissioner of Police",
    orderDate: "2026-04-18",
    actionType: "COMPLY",
    department: "Home",
    deadline: "2026-05-18",
    confidence: 0.91,
    sourcePage: 52,
    paragraph: "The jurisdictional police shall examine the complaint and take action in accordance with law.",
    resolvedDirective: "The Commissioner of Police, Bengaluru, must assign the jurisdictional station to examine Nagaraj S.'s protection complaint and record action taken.",
    status: "Ready to approve",
  },
]

const trustedRecords: TrustedRecord[] = [
  {
    id: "dept-1",
    case_id: "WP 18422/2025",
    judgment_id: "judgment-revenue-18422",
    directive_number: 1,
    action_type: "COMPLY",
    responsible_dept: "Revenue",
    deadline_explicit: "2026-05-30",
    status: "verified",
    days_remaining: 23,
    source_page: 48,
    parties: "Smt. Kavitha R. vs State of Karnataka",
    order_date: "2026-04-30",
    directive_text: "The Tahsildar, Bengaluru East Taluk, must consider Kavitha R.'s representation and pass a reasoned order within thirty days.",
  },
  {
    id: "dept-2",
    case_id: "WP 21109/2025",
    judgment_id: "judgment-home-21109",
    directive_number: 1,
    action_type: "COMPLY",
    responsible_dept: "Home",
    deadline_explicit: "2026-05-18",
    status: "verified",
    days_remaining: 11,
    source_page: 52,
    parties: "Nagaraj S. vs Commissioner of Police",
    order_date: "2026-04-18",
    directive_text: "The Commissioner of Police, Bengaluru, must assign the jurisdictional station to examine Nagaraj S.'s protection complaint and record action taken.",
  },
  {
    id: "dept-3",
    case_id: "WA 992/2025",
    judgment_id: "judgment-law-992",
    directive_number: 2,
    action_type: "CONSIDER_APPEAL",
    responsible_dept: "Law",
    deadline_inferred: "2026-06-21",
    status: "verified",
    days_remaining: 45,
    source_page: 5,
    parties: "Urban Development Authority vs M. Raghavendra",
    order_date: "2026-04-22",
    directive_text: "The Law Department must decide whether to file an appeal for the Urban Development Authority before the sixty-day limitation period expires.",
  },
  {
    id: "dept-4",
    case_id: "WP 16008/2025",
    judgment_id: "judgment-revenue-16008",
    directive_number: 1,
    action_type: "COMPLY",
    responsible_dept: "Revenue",
    deadline_explicit: "2026-05-15",
    status: "verified",
    days_remaining: 8,
    source_page: 63,
    parties: "R. Prakash vs Deputy Commissioner",
    order_date: "2026-04-15",
    directive_text: "The Deputy Commissioner, Revenue, must complete the land records correction and submit compliance before the listed deadline.",
  },
]

function urgency(days = 9999, status = "") {
  if (status === "actioned") return { label: "Actioned", badge: "success" as const, className: "border-emerald-200 bg-emerald-50 text-emerald-700" }
  if (days < 0) return { label: "Overdue", badge: "danger" as const, className: "border-red-200 bg-red-50 text-red-700" }
  if (days <= 10) return { label: "Red", badge: "danger" as const, className: "border-red-200 bg-red-50 text-red-700" }
  if (days <= 30) return { label: "Amber", badge: "warning" as const, className: "border-amber-200 bg-amber-50 text-amber-800" }
  return { label: "Green", badge: "success" as const, className: "border-emerald-200 bg-emerald-50 text-emerald-700" }
}

function formatDeadline(item: DashboardItem) {
  return item.deadline_explicit || item.deadline_inferred || "Not found"
}

function DashboardPage() {
  const [mode, setMode] = React.useState<WorkspaceMode>("operator")
  const [reviewQueue, setReviewQueue] = React.useState<ReviewItem[]>(reviewQueueSeed)
  const [selectedReviewId, setSelectedReviewId] = React.useState(reviewQueueSeed[0].id)
  const [editingReview, setEditingReview] = React.useState<ReviewItem | null>(null)
  const [redoReview, setRedoReview] = React.useState<ReviewItem | null>(null)
  const [redoNote, setRedoNote] = React.useState("")
  const [openRecord, setOpenRecord] = React.useState<TrustedRecord | null>(null)
  const department = useUIStore((s) => s.department)
  const { data: liveItems, isLoading, isError } = useDashboard(department)
  const { data: summary } = useDashboardSummary(department)

  const selectedReview = reviewQueue.find((item) => item.id === selectedReviewId) ?? reviewQueue[0]
  const demoItems = trustedRecords.filter((item) => item.responsible_dept === department)
  const departmentItems = liveItems?.length ? liveItems : demoItems
  const usingDemoDepartmentData = !liveItems?.length
  const reviewCounts = {
    pending: reviewQueue.length,
    lowConfidence: reviewQueue.filter((item) => item.confidence < 0.8).length,
    reruns: 1,
    verifiedToday: 7,
  }
  const dashboardSummary = summary ?? {
    total: departmentItems.length,
    urgent: departmentItems.filter((item) => (item.days_remaining ?? 9999) <= 10).length,
    upcoming: departmentItems.filter((item) => {
      const days = item.days_remaining ?? 9999
      return days > 10 && days <= 30
    }).length,
    actioned: departmentItems.filter((item) => item.status === "actioned").length,
  }
  const selectedDepartmentRecords = departmentItems.map((item) => ({
    ...item,
    directive_text:
      "directive_text" in item
        ? item.directive_text
        : `${item.action_type} directive verified from page ${item.source_page ?? "-"}.`,
    parties: "parties" in item ? item.parties : "Case parties from verified action plan",
    order_date: "order_date" in item ? item.order_date : "Order date in verified record",
  })) as TrustedRecord[]

  const updateReview = (updated: ReviewItem) => {
    setReviewQueue((items) => items.map((item) => (item.id === updated.id ? updated : item)))
    setSelectedReviewId(updated.id)
  }

  const approveSelectedReview = () => {
    updateReview({ ...selectedReview, status: "Approved by nodal officer" })
  }

  const submitRedo = () => {
    if (!redoReview) return
    updateReview({
      ...redoReview,
      status: redoNote.trim() ? `Redo requested: ${redoNote.trim()}` : "Redo requested",
    })
    setRedoReview(null)
    setRedoNote("")
  }

  return (
    <div className="min-h-full bg-[#f6f3ec] text-stone-950">
      <section className="border-b border-stone-200 bg-[#fffdf7] px-6 py-5">
        <div className="flex flex-col gap-5 xl:flex-row xl:items-end xl:justify-between">
          <div className="max-w-4xl">
            <div className="mb-3 flex flex-wrap items-center gap-2">
              <Badge variant="outline" className="border-stone-300 bg-white text-stone-700">
                CCMS judgement intake
              </Badge>
              <Badge variant="outline" className="border-emerald-300 bg-emerald-50 text-emerald-800">
                Verified records only reach departments
              </Badge>
            </div>
            <h2 className="font-serif text-3xl font-semibold leading-tight text-stone-950 md:text-4xl">
              Lex-Gov AI turns High Court PDFs into officer-verified action plans.
            </h2>
            <p className="mt-3 max-w-3xl text-sm leading-6 text-stone-600">
              Use the officer screen to verify AI extraction against cited source pages. Switch to the department screen to see the trusted workload after sign-off.
            </p>
          </div>

          <div className="flex w-full rounded-md border border-stone-300 bg-stone-100 p-1 shadow-sm xl:w-auto" role="tablist" aria-label="Workspace mode">
            <button
              type="button"
              role="tab"
              aria-selected={mode === "operator"}
              onClick={() => setMode("operator")}
              className={cn(
                "flex flex-1 items-center justify-center gap-2 rounded px-4 py-2 text-sm font-semibold transition xl:flex-none",
                mode === "operator" ? "bg-stone-950 text-white shadow" : "text-stone-600 hover:bg-white"
              )}
            >
              <FileSearch className="h-4 w-4" />
              Nodal officer review
            </button>
            <button
              type="button"
              role="tab"
              aria-selected={mode === "department"}
              onClick={() => setMode("department")}
              className={cn(
                "flex flex-1 items-center justify-center gap-2 rounded px-4 py-2 text-sm font-semibold transition xl:flex-none",
                mode === "department" ? "bg-stone-950 text-white shadow" : "text-stone-600 hover:bg-white"
              )}
            >
              <Building2 className="h-4 w-4" />
              Department board
            </button>
          </div>
        </div>
      </section>

      {mode === "operator" ? (
        <section className="grid gap-0 xl:grid-cols-[360px_minmax(0,1fr)]">
          <aside className="border-b border-stone-200 bg-white xl:border-b-0 xl:border-r">
            <div className="grid grid-cols-2 gap-3 border-b border-stone-200 p-4">
              <Metric icon={ClipboardCheck} label="Awaiting sign-off" value={reviewCounts.pending} />
              <Metric icon={AlertTriangle} label="Low confidence" value={reviewCounts.lowConfidence} tone="amber" />
              <Metric icon={RotateCcw} label="Rerun notes" value={reviewCounts.reruns} tone="red" />
              <Metric icon={BadgeCheck} label="Verified today" value={reviewCounts.verifiedToday} tone="green" />
            </div>
            <div className="space-y-3 p-4">
              {reviewQueue.map((item) => (
                <button
                  key={item.id}
                  type="button"
                  onClick={() => setSelectedReviewId(item.id)}
                  className={cn(
                    "w-full rounded-lg border p-4 text-left transition",
                    selectedReview.id === item.id
                      ? "border-stone-950 bg-stone-950 text-white shadow-lg"
                      : "border-stone-200 bg-[#fffdf7] hover:border-stone-400"
                  )}
                >
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <p className="text-xs font-semibold uppercase tracking-wide opacity-70">{item.caseId}</p>
                      <p className="mt-1 text-sm font-semibold leading-5">{item.title}</p>
                    </div>
                    <Badge variant={item.confidence >= 0.8 ? "success" : "warning"}>
                      {Math.round(item.confidence * 100)}%
                    </Badge>
                  </div>
                  <div className="mt-3 flex flex-wrap gap-2">
                    <span className="rounded-full bg-white/15 px-2 py-1 text-xs">{item.department}</span>
                    <span className="rounded-full bg-white/15 px-2 py-1 text-xs">{item.actionType}</span>
                  </div>
                </button>
              ))}
            </div>
          </aside>

          <div className="grid min-h-[680px] gap-0 bg-[#f6f3ec] lg:grid-cols-[minmax(0,0.95fr)_minmax(420px,1.05fr)]">
            <div className="border-b border-stone-200 bg-[#fffdf7] p-6 lg:border-b-0 lg:border-r">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <p className="text-xs font-semibold uppercase tracking-wide text-stone-500">AI extracted action plan</p>
                  <h3 className="mt-2 font-serif text-2xl font-semibold text-stone-950">{selectedReview.title}</h3>
                  <p className="mt-2 text-sm text-stone-600">{selectedReview.parties}</p>
                </div>
                <Badge variant={selectedReview.actionType === "COMPLY" ? "danger" : "warning"}>
                  {selectedReview.actionType}
                </Badge>
              </div>

              <div className="mt-6 grid gap-3 sm:grid-cols-2">
                <Field label="Responsible department" value={selectedReview.department} />
                <Field label="Order date" value={selectedReview.orderDate} />
                <Field label="Deadline" value={selectedReview.deadline} />
                <Field label="Source page" value={`Page ${selectedReview.sourcePage}`} />
              </div>

              <div className="mt-4 rounded-lg border border-emerald-200 bg-emerald-50 p-4">
                <p className="text-xs font-semibold uppercase tracking-wide text-emerald-800">Resolved directive</p>
                <p className="mt-2 text-sm leading-6 text-stone-800">{selectedReview.resolvedDirective}</p>
              </div>

              <div className="mt-6 rounded-lg border border-stone-200 bg-white p-4 shadow-sm">
                <div className="flex items-center justify-between gap-4">
                  <div className="flex items-center gap-2">
                    <ShieldCheck className="h-4 w-4 text-emerald-700" />
                    <span className="text-sm font-semibold text-stone-900">Officer decision</span>
                  </div>
                  <span className="text-xs text-stone-500">{selectedReview.status}</span>
                </div>
                <p className="mt-4 text-sm leading-6 text-stone-700">
                  Verify the department assignment, action type, deadline, and paragraph citation before publishing. Edit records are audit-logged; redo sends the correction note back into Pass 1.
                </p>
                <div className="mt-5 flex flex-wrap gap-2">
                  <Button className="bg-emerald-700 hover:bg-emerald-800" onClick={approveSelectedReview}>
                    <CheckCircle2 className="h-4 w-4" />
                    Approve directive
                  </Button>
                  <Button variant="outline" onClick={() => setEditingReview(selectedReview)}>
                    <SlidersHorizontal className="h-4 w-4" />
                    Edit fields
                  </Button>
                  <Button
                    variant="outline"
                    className="border-red-200 text-red-700 hover:bg-red-50"
                    onClick={() => {
                      setRedoReview(selectedReview)
                      setRedoNote("")
                    }}
                  >
                    <RotateCcw className="h-4 w-4" />
                    Redo extraction
                  </Button>
                </div>
              </div>
            </div>

            <div className="bg-stone-900 p-5 text-white">
              <div className="flex items-center justify-between gap-4 border-b border-white/10 pb-4">
                <div>
                  <p className="text-xs font-semibold uppercase tracking-wide text-stone-400">Click-to-cite PDF pane</p>
                  <h3 className="mt-1 text-lg font-semibold">Original judgement source</h3>
                </div>
                <Badge variant="outline" className="border-amber-300 bg-amber-200 text-stone-950">
                  Page {selectedReview.sourcePage}
                </Badge>
              </div>
              <div className="mt-5 rounded-md border border-white/10 bg-[#f7f1e2] p-6 text-stone-950 shadow-2xl">
                <div className="mb-4 flex items-center justify-between border-b border-stone-300 pb-3">
                  <div className="flex items-center gap-2 text-sm font-semibold">
                    <Gavel className="h-4 w-4" />
                    High Court of Karnataka
                  </div>
                  <span className="text-xs text-stone-500">Extracted slice: pages 1-5, 47-53</span>
                </div>
                <div className="space-y-4 font-serif text-sm leading-7 text-stone-800">
                  <p>
                    Having heard learned counsel for the parties and perused the material on record, the writ petition is disposed of with the following directions.
                  </p>
                  <p className="rounded-md border-l-4 border-amber-500 bg-amber-100/80 p-4 shadow-inner">
                    <Highlighter className="mr-2 inline h-4 w-4 text-amber-700" />
                    {selectedReview.paragraph}
                  </p>
                  <p>
                    Compliance report, where required, shall be placed before the competent authority. All other content in the judgement remains available for audit reference.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </section>
      ) : (
        <section className="p-6">
          <div className="grid gap-4 md:grid-cols-4">
            <DepartmentMetric icon={Building2} label={`${department} verified`} value={dashboardSummary.total} />
            <DepartmentMetric icon={AlertTriangle} label="Red urgency" value={dashboardSummary.urgent} tone="red" />
            <DepartmentMetric icon={CalendarClock} label="Amber window" value={dashboardSummary.upcoming} tone="amber" />
            <DepartmentMetric icon={CheckCircle2} label="Actioned" value={dashboardSummary.actioned} tone="green" />
          </div>

          <div className="mt-6 rounded-lg border border-stone-200 bg-white shadow-sm">
            <div className="flex flex-col gap-3 border-b border-stone-200 p-5 md:flex-row md:items-center md:justify-between">
              <div>
                <h3 className="font-serif text-2xl font-semibold text-stone-950">Trusted department workload</h3>
                <p className="mt-1 text-sm text-stone-500">
                  Only nodal officer-approved directives appear here. Unverified AI output stays in the review screen.
                </p>
              </div>
              <Badge variant={usingDemoDepartmentData || isError ? "warning" : "success"}>
                {usingDemoDepartmentData || isError ? "Demo verified records" : "Live verified feed"}
              </Badge>
            </div>

            <div className="divide-y divide-stone-100">
              {isLoading && !departmentItems.length ? (
                <div className="p-8 text-center text-sm text-stone-500">Loading verified directives...</div>
              ) : selectedDepartmentRecords.length ? (
                selectedDepartmentRecords.map((item) => {
                  const state = urgency(item.days_remaining, item.status)
                  return (
                    <div key={item.id} className="grid gap-4 p-5 transition hover:bg-stone-50 lg:grid-cols-[1fr_170px_140px_110px] lg:items-center">
                      <div>
                        <div className="flex flex-wrap items-center gap-2">
                          <p className="font-semibold text-stone-950">{item.case_id}</p>
                          <Badge variant={item.action_type === "COMPLY" ? "danger" : "warning"}>
                            {item.action_type}
                          </Badge>
                          <Badge variant="outline">Directive #{item.directive_number}</Badge>
                        </div>
                        <p className="mt-2 text-sm leading-6 text-stone-600">
                          {item.directive_text}
                        </p>
                        <p className="mt-1 text-xs text-stone-500">
                          Page {item.source_page ?? "-"} citation verified. Record is ready for department action and limitation tracking.
                        </p>
                      </div>
                      <div>
                        <p className="text-xs font-semibold uppercase tracking-wide text-stone-400">Deadline</p>
                        <p className="mt-1 text-sm font-semibold text-stone-900">{formatDeadline(item)}</p>
                      </div>
                      <div>
                        <p className="text-xs font-semibold uppercase tracking-wide text-stone-400">Urgency</p>
                        <span className={cn("mt-1 inline-flex rounded-full border px-3 py-1 text-xs font-semibold", state.className)}>
                          {state.label}
                        </span>
                      </div>
                      <Button variant="outline" size="sm" onClick={() => setOpenRecord(item)}>
                        Open record
                        <ArrowRight className="h-4 w-4" />
                      </Button>
                    </div>
                  )
                })
              ) : (
                <div className="p-8 text-center text-sm text-stone-500">
                  No verified directives for {department}.
                </div>
              )}
            </div>
          </div>
        </section>
      )}

      <Dialog open={Boolean(editingReview)} onOpenChange={(open) => !open && setEditingReview(null)}>
        <DialogContent className="max-w-2xl bg-[#fffdf7]">
          <DialogHeader>
            <DialogTitle>Edit extracted directive</DialogTitle>
            <DialogDescription>
              Update the resolved department-facing action and keep the source paragraph for citation.
            </DialogDescription>
          </DialogHeader>
          {editingReview && (
            <div className="grid gap-4 py-2">
              <div className="grid gap-3 md:grid-cols-2">
                <label className="space-y-2 text-sm font-medium text-stone-700">
                  Case ID
                  <Input
                    value={editingReview.caseId}
                    onChange={(event) => setEditingReview({ ...editingReview, caseId: event.target.value })}
                  />
                </label>
                <label className="space-y-2 text-sm font-medium text-stone-700">
                  Responsible department
                  <Input
                    value={editingReview.department}
                    onChange={(event) => setEditingReview({ ...editingReview, department: event.target.value })}
                  />
                </label>
                <label className="space-y-2 text-sm font-medium text-stone-700">
                  Action type
                  <Input
                    value={editingReview.actionType}
                    onChange={(event) => setEditingReview({ ...editingReview, actionType: event.target.value })}
                  />
                </label>
                <label className="space-y-2 text-sm font-medium text-stone-700">
                  Deadline
                  <Input
                    type="date"
                    value={editingReview.deadline}
                    onChange={(event) => setEditingReview({ ...editingReview, deadline: event.target.value })}
                  />
                </label>
              </div>
              <label className="space-y-2 text-sm font-medium text-stone-700">
                Directive title
                <Input
                  value={editingReview.title}
                  onChange={(event) => setEditingReview({ ...editingReview, title: event.target.value })}
                />
              </label>
              <label className="space-y-2 text-sm font-medium text-stone-700">
                Resolved directive shown to department
                <Textarea
                  rows={4}
                  value={editingReview.resolvedDirective}
                  onChange={(event) => setEditingReview({ ...editingReview, resolvedDirective: event.target.value })}
                />
              </label>
              <label className="space-y-2 text-sm font-medium text-stone-700">
                Source paragraph from judgement
                <Textarea
                  rows={5}
                  value={editingReview.paragraph}
                  onChange={(event) => setEditingReview({ ...editingReview, paragraph: event.target.value })}
                />
              </label>
            </div>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={() => setEditingReview(null)}>
              Cancel
            </Button>
            <Button
              className="bg-stone-950 hover:bg-stone-800"
              onClick={() => {
                if (!editingReview) return
                updateReview({ ...editingReview, status: "Edited and approved by nodal officer" })
                setEditingReview(null)
              }}
            >
              Save edited directive
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={Boolean(redoReview)} onOpenChange={(open) => !open && setRedoReview(null)}>
        <DialogContent className="max-w-xl bg-[#fffdf7]">
          <DialogHeader>
            <DialogTitle>Request extraction redo</DialogTitle>
            <DialogDescription>
              Send a correction note back to the extraction pipeline before anything is published.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-3 py-2">
            <p className="text-sm leading-6 text-stone-600">
              Add the officer correction note that should be sent back into Pass 1, for example a missed paragraph or wrong department assignment.
            </p>
            <Textarea
              rows={5}
              value={redoNote}
              onChange={(event) => setRedoNote(event.target.value)}
              placeholder="Example: paragraph 34 direction was missed; this should route to Revenue, not Law."
            />
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setRedoReview(null)}>
              Cancel
            </Button>
            <Button className="bg-red-700 hover:bg-red-800" onClick={submitRedo}>
              Send redo note
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={Boolean(openRecord)} onOpenChange={(open) => !open && setOpenRecord(null)}>
        <DialogContent className="max-w-2xl bg-[#fffdf7]">
          <DialogHeader>
            <DialogTitle>Verified department record</DialogTitle>
            <DialogDescription>
              Review the approved directive, responsible department, deadline, and source citation.
            </DialogDescription>
          </DialogHeader>
          {openRecord && (
            <div className="space-y-5 py-2">
              <div className="rounded-lg border border-stone-200 bg-white p-4">
                <div className="flex flex-wrap items-center gap-2">
                  <Badge variant="outline">{openRecord.case_id}</Badge>
                  <Badge variant={openRecord.action_type === "COMPLY" ? "danger" : "warning"}>
                    {openRecord.action_type}
                  </Badge>
                  <Badge variant="success">Verified</Badge>
                </div>
                <h4 className="mt-4 font-serif text-2xl font-semibold text-stone-950">
                  Directive #{openRecord.directive_number}
                </h4>
                <p className="mt-2 text-sm leading-6 text-stone-700">{openRecord.directive_text}</p>
              </div>

              <div className="grid gap-3 md:grid-cols-2">
                <Field label="Parties" value={openRecord.parties} />
                <Field label="Department" value={openRecord.responsible_dept} />
                <Field label="Order date" value={openRecord.order_date} />
                <Field label="Deadline" value={formatDeadline(openRecord)} />
                <Field label="Source page" value={`Page ${openRecord.source_page ?? "-"}`} />
                <Field label="Urgency" value={urgency(openRecord.days_remaining, openRecord.status).label} />
              </div>
            </div>
          )}
          <DialogFooter>
            <Button onClick={() => setOpenRecord(null)}>Done</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}

function Metric({
  icon: Icon,
  label,
  value,
  tone = "stone",
}: {
  icon: React.ElementType
  label: string
  value: number
  tone?: "stone" | "amber" | "red" | "green"
}) {
  const tones = {
    stone: "bg-stone-100 text-stone-800",
    amber: "bg-amber-100 text-amber-900",
    red: "bg-red-100 text-red-800",
    green: "bg-emerald-100 text-emerald-800",
  }

  return (
    <div className="rounded-lg border border-stone-200 bg-white p-3 shadow-sm">
      <div className={cn("mb-3 flex h-8 w-8 items-center justify-center rounded-md", tones[tone])}>
        <Icon className="h-4 w-4" />
      </div>
      <p className="text-2xl font-semibold text-stone-950">{value}</p>
      <p className="mt-1 text-xs leading-4 text-stone-500">{label}</p>
    </div>
  )
}

function Field({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-stone-200 bg-white p-4 shadow-sm">
      <p className="text-xs font-semibold uppercase tracking-wide text-stone-400">{label}</p>
      <p className="mt-2 text-sm font-semibold text-stone-950">{value}</p>
    </div>
  )
}

function DepartmentMetric({
  icon: Icon,
  label,
  value,
  tone = "stone",
}: {
  icon: React.ElementType
  label: string
  value: number
  tone?: "stone" | "amber" | "red" | "green"
}) {
  const toneClass = {
    stone: "border-stone-200 bg-white text-stone-900",
    amber: "border-amber-200 bg-amber-50 text-amber-900",
    red: "border-red-200 bg-red-50 text-red-800",
    green: "border-emerald-200 bg-emerald-50 text-emerald-800",
  }

  return (
    <div className={cn("rounded-lg border p-4 shadow-sm", toneClass[tone])}>
      <div className="flex items-center justify-between">
        <p className="text-sm font-semibold">{label}</p>
        <Icon className="h-4 w-4" />
      </div>
      <p className="mt-4 text-3xl font-semibold">{value}</p>
    </div>
  )
}

export const Route = createRoute({
  getParentRoute: () => rootRoute,
  path: '/dashboard',
  component: DashboardPage,
})
