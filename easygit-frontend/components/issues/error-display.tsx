import { AlertCircle } from "lucide-react"

interface ErrorDisplayProps {
  message: string
}

export function ErrorDisplay({ message }: ErrorDisplayProps) {
  return (
    <div className="rounded-lg border border-red-800/50 bg-red-900/20 p-4">
      <div className="flex">
        <div className="flex-shrink-0">
          <AlertCircle className="h-5 w-5 text-red-400" aria-hidden="true" />
        </div>
        <div className="ml-3">
          <h3 className="text-sm font-medium text-red-200">
            Error
          </h3>
          <div className="mt-2 text-sm text-red-300">
            <p>{message}</p>
          </div>
        </div>
      </div>
    </div>
  )
}
