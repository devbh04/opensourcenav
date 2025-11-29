import { useRepositoryStore } from "@/store/repository-store"

export function ErrorDisplay() {
  const { error } = useRepositoryStore()

  if (!error) return null

  return (
    <div className="bg-red-900/50 border border-red-700 rounded-lg p-4">
      <p className="text-red-200">Error: {error}</p>
      <p className="text-red-300 text-sm mt-2">
        Check the console for more details. Make sure the backend server is running on http://localhost:8000
      </p>
    </div>
  )
}
