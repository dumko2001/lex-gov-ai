import * as React from "react"
import { cn } from "@/lib/utils"
import { Sidebar } from "./sidebar"
import { Header } from "./header"
import { useAuthStore } from "@/stores/auth"
import { useUIStore } from "@/stores/ui"

interface LayoutProps {
  children: React.ReactNode
  className?: string
}

export function Layout({ children, className }: LayoutProps) {
  const restoreAuth = useAuthStore((s) => s.restoreAuth)
  const restoreUI = useUIStore((s) => s.restore)

  React.useEffect(() => {
    restoreAuth()
    restoreUI()
  }, [restoreAuth, restoreUI])

  return (
    <div className="flex h-screen w-full bg-[#f6f3ec]">
      <Sidebar />
      <div className="flex flex-1 flex-col overflow-hidden">
        <Header />
        <main className={cn("flex-1 overflow-auto", className)}>
          {children}
        </main>
      </div>
    </div>
  )
}
