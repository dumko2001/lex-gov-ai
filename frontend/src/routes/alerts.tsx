import { createRoute } from '@tanstack/react-router'
import { Route as rootRoute } from './__root'
import { useAlerts } from "@/hooks/useDashboard"
import { useUIStore } from "@/stores/ui"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Alert, AlertTitle, AlertDescription } from "@/components/ui/alert"
import { Bell, AlertTriangle, Info, CheckCircle, Clock } from "lucide-react"

function AlertsPage() {
  const department = useUIStore((s) => s.department)
  const { data: alerts, isLoading } = useAlerts(department)

  const deriveSeverity = (alertType: string) => {
    const t = alertType.toUpperCase()
    if (t.includes("OVERDUE") || t.includes("CRITICAL")) return "critical"
    if (t.includes("10_DAYS") || t.includes("15_DAYS")) return "high"
    if (t.includes("PENDING")) return "medium"
    return "low"
  }

  const prettifyTitle = (alertType: string) =>
    alertType
      .toLowerCase()
      .split("_")
      .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
      .join(" ")

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'critical':
      case 'high':
        return <AlertTriangle className="h-5 w-5 text-red-600" />
      case 'medium':
        return <Clock className="h-5 w-5 text-amber-600" />
      default:
        return <Info className="h-5 w-5 text-blue-600" />
    }
  }

  const getSeverityVariant = (severity: string) => {
    switch (severity) {
      case 'critical':
      case 'high':
        return 'destructive'
      case 'medium':
        return 'warning'
      default:
        return 'default'
    }
  }

  const getSeverityBadge = (severity: string) => {
    switch (severity) {
      case 'critical':
        return <Badge variant="danger">Critical</Badge>
      case 'high':
        return <Badge variant="danger">High</Badge>
      case 'medium':
        return <Badge variant="warning">Medium</Badge>
      default:
        return <Badge variant="secondary">Low</Badge>
    }
  }

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-slate-900">Alert Center</h2>
          <p className="text-slate-500">
            Alerts for {department} with urgent directives and deadline risks.
          </p>
        </div>
        <Bell className="h-6 w-6 text-slate-400" />
      </div>

      {isLoading ? (
        <div className="py-12 text-center text-slate-500">Loading alerts...</div>
      ) : (
        <div className="space-y-4">
          {alerts?.map((alert) => (
            <Card key={alert.id} className="overflow-hidden">
              <CardContent className="p-0">
                <Alert variant={getSeverityVariant(deriveSeverity(alert.alert_type))} className="border-0">
                  <div className="flex items-start gap-4">
                    {getSeverityIcon(deriveSeverity(alert.alert_type))}
                    <div className="flex-1">
                      <div className="flex items-center justify-between">
                        <AlertTitle className="text-base">{prettifyTitle(alert.alert_type)}</AlertTitle>
                        {getSeverityBadge(deriveSeverity(alert.alert_type))}
                      </div>
                      <AlertDescription className="mt-1">
                        {alert.message}
                      </AlertDescription>
                      <div className="mt-3 flex items-center gap-4">
                        <span className="text-xs text-slate-500">
                          {new Date(alert.created_at).toLocaleDateString()}
                        </span>
                        <span className="text-xs text-slate-500">
                          {alert.recipient_dept}
                        </span>
                        {!alert.is_read && (
                          <Badge variant="outline" className="text-xs">Unread</Badge>
                        )}
                      </div>
                    </div>
                  </div>
                </Alert>
              </CardContent>
            </Card>
          ))}

          {(!alerts || alerts.length === 0) && (
            <div className="flex flex-col items-center justify-center rounded-lg border bg-white py-16">
              <CheckCircle className="mb-4 h-12 w-12 text-green-500" />
              <p className="text-lg font-medium text-slate-900">All caught up!</p>
              <p className="text-slate-500">No alerts at this time.</p>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export const Route = createRoute({
  getParentRoute: () => rootRoute,
  path: '/alerts',
  component: AlertsPage,
})
