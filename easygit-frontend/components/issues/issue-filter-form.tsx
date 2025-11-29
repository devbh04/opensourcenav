import * as React from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Badge } from "@/components/ui/badge"
import { useIssueStore } from "@/store/issue-store"
import { Search, X } from "lucide-react"

export function IssueFilterForm() {
  const {
    request,
    setRepoUrl,
    setState,
    setPerPage,
    setDifficulty,
    setUserQuery,
    fetchIssues,
    clearIssues,
    isLoading
  } = useIssueStore()

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    fetchIssues()
  }

  const handleClear = () => {
    setRepoUrl("")
    setState("open")
    setPerPage(100)
    setDifficulty("all")
    setUserQuery("")
    clearIssues()
  }

  return (
    <div className="space-y-6 p-6 bg-gray-800/30 rounded-lg border border-gray-700">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold text-white">Issue Analyzer</h2>
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
              value={request.repoUrl}
              onChange={(e) => setRepoUrl(e.target.value)}
              className="bg-gray-800/50 border-gray-700 text-white placeholder-gray-400"
              required
            />
          </div>

          {/* Issue State */}
          <div className="space-y-2">
            <label className="text-sm font-medium text-gray-200">Issue State</label>
            <Select 
              value={request.state} 
              onValueChange={(value: "open" | "closed" | "all") => setState(value)}
            >
              <SelectTrigger className="bg-gray-800/50 border-gray-700 text-white">
                <SelectValue />
              </SelectTrigger>
              <SelectContent className="bg-gray-800 border-gray-700">
                <SelectItem value="open">Open</SelectItem>
                <SelectItem value="closed">Closed</SelectItem>
                <SelectItem value="all">All</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Difficulty Level */}
          <div className="space-y-2">
            <label className="text-sm font-medium text-gray-200">Difficulty Level</label>
            <Select 
              value={request.difficulty} 
              onValueChange={(value: "all" | "beginner" | "intermediate" | "advanced") => setDifficulty(value)}
            >
              <SelectTrigger className="bg-gray-800/50 border-gray-700 text-white">
                <SelectValue />
              </SelectTrigger>
              <SelectContent className="bg-gray-800 border-gray-700">
                <SelectItem value="all">All Levels</SelectItem>
                <SelectItem value="beginner">Beginner</SelectItem>
                <SelectItem value="intermediate">Intermediate</SelectItem>
                <SelectItem value="advanced">Advanced</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Per Page */}
          <div className="space-y-2">
            <label className="text-sm font-medium text-gray-200">Results Per Page</label>
            <Select 
              value={request.perPage.toString()} 
              onValueChange={(value) => setPerPage(parseInt(value))}
            >
              <SelectTrigger className="bg-gray-800/50 border-gray-700 text-white">
                <SelectValue />
              </SelectTrigger>
              <SelectContent className="bg-gray-800 border-gray-700">
                <SelectItem value="25">25</SelectItem>
                <SelectItem value="50">50</SelectItem>
                <SelectItem value="100">100</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>

        {/* User Query */}
        <div className="space-y-2">
          <label className="text-sm font-medium text-gray-200">Search Query</label>
          <Input
            type="text"
            placeholder="Search issues by title, body, or labels..."
            value={request.userQuery}
            onChange={(e) => setUserQuery(e.target.value)}
            className="bg-gray-800/50 border-gray-700 text-white placeholder-gray-400"
          />
        </div>

        <div className="flex justify-center items-center space-x-4">
          <Button
            type="submit"
            disabled={isLoading || !request.repoUrl.trim()}
            className="bg-black border border-gray-700 hover:border-none hover:shadow-2xs hover:shadow-white hover:bg-black text-white"
          >
            {isLoading ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                Analyzing Issues...
              </>
            ) : (
              <>
                <Search className="w-4 h-4 mr-2" />
                Analyze Issues
              </>
            )}
          </Button>
        </div>
      </form>
    </div>
  )
}
