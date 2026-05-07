import { createRootRoute, Outlet } from '@tanstack/react-router'
import { Layout } from "@/components/layout"

function RootComponent() {
  return (
    <Layout>
      <Outlet />
    </Layout>
  )
}

export const Route = createRootRoute({
  component: RootComponent,
})
