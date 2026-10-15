import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute('/_authed/dashboard/users/')({
  component: RouteComponent,
})

function RouteComponent() {
  return <div>Hello "/_authed/dashboard/users/"!</div>
}
