import { Link, useLocation } from "@tanstack/react-router"
import { cn } from "@/lib/utils"
import { useUIStore } from "@/stores/ui"
import {
  LayoutDashboard,
  Upload,
  Bell,
  Scale,
} from "lucide-react"

const navItems = [
  {
    name: "Workspace",
    href: "/dashboard",
    icon: LayoutDashboard,
  },
  {
    name: "Upload",
    href: "/upload",
    icon: Upload,
  },
  {
    name: "Alerts",
    href: "/alerts",
    icon: Bell,
  },
]

export function Sidebar() {
  const location = useLocation()
  const department = useUIStore((s) => s.department)

  return (
    <aside className="hidden h-screen w-64 flex-col border-r border-stone-200 bg-[#17140f] text-white lg:flex">
      <div className="flex h-16 items-center gap-2 border-b border-white/10 px-6">
        <Scale className="h-6 w-6 text-amber-300" />
        <span className="text-lg font-bold text-white">Lex-Gov AI</span>
      </div>

      <nav className="flex-1 space-y-1 px-3 py-4">
        {navItems.map((item) => {
          const isActive = location.pathname === item.href || location.pathname.startsWith(item.href + '/')
          return (
            <Link
              key={item.name}
              to={item.href}
              className={cn(
                "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                isActive
                  ? "bg-amber-300 text-stone-950"
                  : "text-stone-300 hover:bg-white/10 hover:text-white"
              )}
            >
              <item.icon className={cn("h-5 w-5", isActive ? "text-stone-950" : "text-stone-500")} />
              {item.name}
            </Link>
          )
        })}
      </nav>

      <div className="border-t border-white/10 p-4">
        <div className="rounded-md border border-white/10 bg-white/5 p-3">
          <p className="text-xs font-medium text-stone-400">Active department</p>
          <p className="text-sm font-semibold text-white">{department}</p>
        </div>
      </div>
    </aside>
  )
}
