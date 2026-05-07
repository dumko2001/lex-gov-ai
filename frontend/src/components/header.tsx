import { Link } from "@tanstack/react-router"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { useUIStore } from "@/stores/ui"
import { Bell } from "lucide-react"

export function Header() {
  const department = useUIStore((s) => s.department)
  const departments = useUIStore((s) => s.departments)
  const setDepartment = useUIStore((s) => s.setDepartment)

  return (
    <header className="flex h-16 items-center justify-between border-b border-stone-200 bg-[#fffdf7] px-6">
      <div className="flex items-center gap-4">
        <h1 className="font-serif text-base font-semibold leading-tight text-stone-950 md:text-lg">
          Judicial Interpretation and Verified Action Pipeline
        </h1>
      </div>

      <div className="flex items-center gap-4">
        <div className="hidden md:block w-56">
          <label className="sr-only" htmlFor="department-select">
            Department
          </label>
          <select
            id="department-select"
            value={department}
            onChange={(e) => setDepartment(e.target.value as typeof department)}
            className="h-9 w-full rounded-md border border-stone-300 bg-white px-3 text-sm text-stone-700 shadow-sm outline-none transition focus:border-amber-500 focus:ring-2 focus:ring-amber-100"
          >
            {departments.map((dept) => (
              <option key={dept} value={dept}>
                {dept}
              </option>
            ))}
          </select>
        </div>
        <Link to="/alerts" className="relative">
          <Button variant="ghost" size="icon" className="relative">
            <Bell className="h-5 w-5 text-stone-600" />
            <Badge
              variant="danger"
              className="absolute -right-1 -top-1 h-4 w-4 items-center justify-center rounded-full p-0 text-[10px]"
            >
              3
            </Badge>
          </Button>
        </Link>

        <div className="hidden rounded-full border border-amber-200 bg-amber-50 px-3 py-1 text-xs font-medium text-stone-700 md:block">
          Demo workspace
        </div>
      </div>
    </header>
  )
}
