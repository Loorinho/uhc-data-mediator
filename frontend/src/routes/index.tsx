import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute('/')({ component: Home })

function Home() {
  return (
    <div className="p-8">
      <h1 className="text-4xl font-bold">Welcome to the UHC Data mediator</h1>
      <p className="mt-4 text-lg">
        This platform allows you to manage and visualize UHC data efficiently.
      </p>
    </div>
  )
}
