import * as React from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Textarea } from "@/components/ui/textarea"
import { useResolutionStore } from "@/store/resolution-store"
import { Search, X } from "lucide-react"

export function ResolutionForm() {
  const {
    request,
    setRepoUrl,
    setIssueUrl,
    setUserContext,
    setIncludeRelatedIssues,
    setDifficultyPreference,
    fetchResolution,
    fetchComprehensiveResolution,
    clearResolution,
    isLoading,
    isLoadingComprehensive
  } = useResolutionStore()

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    fetchResolution()
  }

  const handleClear = () => {
    clearResolution()
  }

  return (
    <div className="space-y-6 p-6 bg-gray-800/30 rounded-lg border border-gray-700">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold text-white">Issue Resolution Request</h2>
        <Button
          type="button"
          variant="outline"
          size="sm"
          onClick={handleClear}
          className="bg-gray-700 hover:bg-gray-600 border-gray-600 text-gray-200"
        >
          <X className="w-4 h-4 mr-2" />
          Clear
        </Button>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Repository URL */}
          <div className="space-y-2">
            <label className="text-sm font-medium text-gray-200">
              Repository URL <span className="text-red-400">*</span>
            </label>
            <Input
              type="url"
              placeholder="https://github.com/owner/repo"
              value={request.repo_url}
              onChange={(e) => setRepoUrl(e.target.value)}
              className="bg-gray-800/50 border-gray-700 text-white placeholder-gray-400"
              required
            />
          </div>

          {/* Issue URL */}
          <div className="space-y-2">
            <label className="text-sm font-medium text-gray-200">
              Issue URL <span className="text-red-400">*</span>
            </label>
            <Input
              type="url"
              placeholder="https://github.com/owner/repo/issues/123"
              value={request.issue_url}
              onChange={(e) => setIssueUrl(e.target.value)}
              className="bg-gray-800/50 border-gray-700 text-white placeholder-gray-400"
              required
            />
          </div>

          {/* Difficulty Preference */}
          <div className="space-y-2">
            <label className="text-sm font-medium text-gray-200">Difficulty Preference</label>
            <Select 
              value={request.difficulty_preference} 
              onValueChange={(value: 'simple' | 'detailed') => setDifficultyPreference(value)}
            >
              <SelectTrigger className="bg-gray-800/50 border-gray-700 text-white">
                <SelectValue />
              </SelectTrigger>
              <SelectContent className="bg-gray-800 border-gray-700">
                <SelectItem value="simple">Simple</SelectItem>
                <SelectItem value="detailed">Detailed</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Include Related Issues */}
          <div className="space-y-2">
            <label className="text-sm font-medium text-gray-200">Include Related Issues</label>
            <Select 
              value={request.include_related_issues ? "true" : "false"} 
              onValueChange={(value) => setIncludeRelatedIssues(value === "true")}
            >
              <SelectTrigger className="bg-gray-800/50 border-gray-700 text-white">
                <SelectValue />
              </SelectTrigger>
              <SelectContent className="bg-gray-800 border-gray-700">
                <SelectItem value="true">Yes</SelectItem>
                <SelectItem value="false">No</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>

        {/* User Context */}
        <div className="space-y-2">
          <label className="text-sm font-medium text-gray-200">Additional Context (Optional)</label>
          <Textarea
            placeholder="Provide any additional context about your environment, constraints, or specific requirements..."
            value={request.user_context}
            onChange={(e) => setUserContext(e.target.value)}
            className="bg-gray-800/50 border-gray-700 text-white placeholder-gray-400 min-h-[100px]"
          />
        </div>

        <div className="flex items-center space-x-4">
          <Button
            type="submit"
            disabled={isLoading || !request.repo_url.trim() || !request.issue_url.trim()}
            className="bg-blue-600 hover:bg-blue-700 text-white"
          >
            {isLoading ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                Generating Resolution...
              </>
            ) : (
              <>
                <Search className="w-4 h-4 mr-2" />
                Generate Resolution
              </>
            )}
          </Button>

          <Button
            type="button"
            onClick={fetchComprehensiveResolution}
            disabled={isLoadingComprehensive || !request.repo_url.trim() || !request.issue_url.trim()}
            className="bg-purple-600 hover:bg-purple-700 text-white"
          >
            {isLoadingComprehensive ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                Generating Comprehensive...
              </>
            ) : (
              <>
                <Search className="w-4 h-4 mr-2" />
                Get Comprehensive Detailed
              </>
            )}
          </Button>
        </div>
      </form>
    </div>
  )
}
