import * as React from "react"
import {
  ColumnFiltersState,
  getSortedRowModel,
  SortingState,
  useReactTable,
  VisibilityState,
  getCoreRowModel,
  getFilteredRowModel,
  getPaginationRowModel,
} from "@tanstack/react-table"
import { ChevronDown, ArrowUpDown, Star, GitFork, ExternalLink, MoreHorizontal } from "lucide-react"

import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuCheckboxItem,
  DropdownMenuContent,
  DropdownMenuTrigger,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
} from "@/components/ui/dropdown-menu"
import { Input } from "@/components/ui/input"
import { useRepositoryStore, Repository } from "@/store/repository-store"

export function RepositoryTable() {
  const { repositories, isLoading } = useRepositoryStore()
  const [sorting, setSorting] = React.useState<SortingState>([])
  const [columnFilters, setColumnFilters] = React.useState<ColumnFiltersState>([])
  const [columnVisibility, setColumnVisibility] = React.useState<VisibilityState>({})

  // Define columns inline for better control
  const columns = React.useMemo(() => [
    {
      id: "full_name",
      accessorKey: "full_name",
      header: "Repository",
      size: 400,
    },
    {
      id: "language", 
      accessorKey: "language",
      header: "Language",
      size: 120,
    },
    {
      id: "stargazers_count",
      accessorKey: "stargazers_count", 
      header: "Stars",
      size: 100,
    },
    {
      id: "forks_count",
      accessorKey: "forks_count",
      header: "Forks", 
      size: 80,
    },
    {
      id: "personalized_score",
      accessorKey: "personalized_score",
      header: "Score",
      size: 80,
    },
    {
      id: "learning_level",
      accessorKey: "learning_level",
      header: "Level",
      size: 120,
    },
    {
      id: "good_first_issue_count",
      accessorKey: "good_first_issue_count",
      header: "Issues",
      size: 80,
    },
    {
      id: "actions",
      header: "",
      size: 60,
      enableSorting: false,
    }
  ], [])

  const table = useReactTable({
    data: repositories,
    columns,
    onSortingChange: setSorting,
    onColumnFiltersChange: setColumnFilters,
    getCoreRowModel: getCoreRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    onColumnVisibilityChange: setColumnVisibility,
    state: {
      sorting,
      columnFilters,
      columnVisibility,
    },
  })

  const getLanguageColor = (lang: string) => {
    if (!lang) return "bg-gray-600 text-gray-200"
    switch (lang.toLowerCase()) {
      case "javascript": return "bg-yellow-500 text-black"
      case "typescript": return "bg-blue-500 text-white"
      case "python": return "bg-green-500 text-white"
      case "go": return "bg-cyan-500 text-black"
      case "rust": return "bg-orange-500 text-white"
      case "java": return "bg-red-500 text-white"
      default: return "bg-purple-500 text-white"
    }
  }

  const getScoreColor = (score: number) => {
    if (score >= 80) return "bg-green-500 text-white"
    if (score >= 60) return "bg-yellow-500 text-black"
    return "bg-red-500 text-white"
  }

  const getLevelColor = (level: string) => {
    if (!level) return "bg-gray-600 text-gray-200"
    switch (level.toLowerCase()) {
      case "beginner": return "bg-green-500 text-white"
      case "intermediate": return "bg-yellow-500 text-black"
      case "advanced": return "bg-red-500 text-white"
      default: return "bg-purple-500 text-white"
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <Input
            placeholder="Filter repositories..."
            value={(table.getColumn("full_name")?.getFilterValue() as string) ?? ""}
            onChange={(event) =>
              table.getColumn("full_name")?.setFilterValue(event.target.value)
            }
            className="max-w-md bg-gray-800/50 border-gray-700 text-white placeholder-gray-400 focus:border-gray-600 focus:ring-gray-600"
          />
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="outline" className="bg-gray-800 text-gray-200 hover:bg-gray-700 border-gray-700">
                Columns <ChevronDown className="ml-2 h-4 w-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="bg-gray-900 border-gray-800">
              {table
                .getAllColumns()
                .filter((column) => column.getCanHide())
                .map((column) => {
                  return (
                    <DropdownMenuCheckboxItem
                      key={column.id}
                      className="capitalize"
                      checked={column.getIsVisible()}
                      onCheckedChange={(value) =>
                        column.toggleVisibility(!!value)
                      }
                    >
                      {column.id}
                    </DropdownMenuCheckboxItem>
                  )
                })}
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
        <div className="text-sm text-gray-400">
          {repositories.length} repositories found
        </div>
      </div>

      <div className="border border-gray-700 rounded-lg bg-gray-800/50 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-800 border-b border-gray-700">
              <tr>
                <th className="w-[400px] px-4 py-3 text-left font-medium text-gray-200 text-sm">
                  <Button
                    variant="ghost"
                    onClick={() => table.getColumn("full_name")?.toggleSorting()}
                    className="text-gray-200 hover:text-white p-0 h-auto font-medium"
                  >
                    Repository
                    <ArrowUpDown className="ml-2 h-4 w-4" />
                  </Button>
                </th>
                <th className="w-[120px] px-4 py-3 text-left font-medium text-gray-200 text-sm">Language</th>
                <th className="w-[100px] px-4 py-3 text-left font-medium text-gray-200 text-sm">
                  <Button
                    variant="ghost"
                    onClick={() => table.getColumn("stargazers_count")?.toggleSorting()}
                    className="text-gray-200 hover:text-white p-0 h-auto font-medium"
                  >
                    <Star className="mr-2 h-4 w-4" />
                    Stars
                    <ArrowUpDown className="ml-2 h-4 w-4" />
                  </Button>
                </th>
                <th className="w-[80px] px-4 py-3 text-left font-medium text-gray-200 text-sm">Forks</th>
                <th className="w-[80px] px-4 py-3 text-left font-medium text-gray-200 text-sm">
                  <Button
                    variant="ghost"
                    onClick={() => table.getColumn("personalized_score")?.toggleSorting()}
                    className="text-gray-200 hover:text-white p-0 h-auto font-medium"
                  >
                    Score
                    <ArrowUpDown className="ml-2 h-4 w-4" />
                  </Button>
                </th>
                <th className="w-[80px] px-4 py-3 text-left font-medium text-gray-200 text-sm">Issues</th>
                <th className="w-[60px] px-4 py-3 text-left font-medium text-gray-200 text-sm"></th>
              </tr>
            </thead>
            <tbody className="bg-gray-900/50">
              {table.getRowModel().rows?.length ? (
                table.getRowModel().rows.map((row, index) => {
                  const repo = row.original as Repository
                  return (
                    <tr
                      key={row.id}
                      className={`border-b border-gray-700/50 hover:bg-gray-800/30 transition-colors ${
                        index % 2 === 1 ? 'bg-gray-900/30' : ''
                      }`}
                    >
                      {/* Repository Column */}
                      <td className="w-[400px] px-4 py-3">
                        <div className="flex items-start gap-3">
                          <div className="w-6 h-6 rounded-full bg-gray-700 flex items-center justify-center flex-shrink-0">
                            <span className="text-xs font-medium text-gray-300">
                              {(repo.full_name || 'U').charAt(0).toUpperCase()}
                            </span>
                          </div>
                          <div className="min-w-0 flex-1">
                            <div 
                              className="font-medium text-white hover:text-blue-400 cursor-pointer truncate"
                              onClick={() => window.open(repo.html_url, '_blank')}
                            >
                              {repo.full_name || 'Unknown'}
                            </div>
                            <div className="text-sm text-gray-400 truncate mt-1 w-96">
                              {repo.description || 'No description available'}
                            </div>
                            {repo.topics && repo.topics.length > 0 && (
                              <div className="flex flex-wrap gap-1 mt-2">
                                {repo.topics.slice(0, 2).map((topic) => (
                                  <span
                                    key={topic}
                                    className="px-2 py-1 text-xs bg-gray-700 text-gray-300 rounded"
                                  >
                                    {topic}
                                  </span>
                                ))}
                                {repo.topics.length > 2 && (
                                  <span className="text-xs text-gray-500">+{repo.topics.length - 2}</span>
                                )}
                              </div>
                            )}
                          </div>
                        </div>
                      </td>
                      
                      {/* Language Column */}
                      <td className="w-[120px] px-4 py-3">
                        {repo.language ? (
                          <span className={`px-2 py-1 rounded text-xs font-medium ${getLanguageColor(repo.language)}`}>
                            {repo.language}
                          </span>
                        ) : (
                          <span className="text-gray-400 text-sm">N/A</span>
                        )}
                      </td>
                      
                      {/* Stars Column */}
                      <td className="w-[100px] px-4 py-3">
                        <div className="flex items-center space-x-2">
                          <Star className="h-4 w-4 text-yellow-400" />
                          <span className="text-gray-300 font-medium">
                            {(repo.stargazers_count || 0).toLocaleString()}
                          </span>
                        </div>
                      </td>
                      
                      {/* Forks Column */}
                      <td className="w-[80px] px-4 py-3">
                        <div className="flex items-center space-x-2">
                          <GitFork className="h-4 w-4 text-gray-400" />
                          <span className="text-gray-300 font-medium">
                            {(repo.forks_count || 0).toLocaleString()}
                          </span>
                        </div>
                      </td>
                      
                      {/* Score Column */}
                      <td className="w-[80px] px-4 py-3">
                        <span className={`px-2 py-1 rounded text-xs font-medium ${getScoreColor(repo.personalized_score || 0)}`}>
                          {(repo.personalized_score || 0).toFixed(1)}
                        </span>
                      </td>
                      
                      
                      {/* Issues Column */}
                      <td className="w-[80px] px-4 py-3">
                        <span className="text-gray-300 font-medium">
                          {repo.good_first_issue_count || 0}
                        </span>
                      </td>
                      
                      {/* Actions Column */}
                      <td className="w-[60px] px-4 py-3">
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button variant="ghost" className="h-8 w-8 p-0 text-gray-400 hover:text-white">
                              <MoreHorizontal className="h-4 w-4" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end" className="bg-gray-900 border-gray-800 text-gray-200">
                            <DropdownMenuLabel>Actions</DropdownMenuLabel>
                            <DropdownMenuItem
                              onClick={() => navigator.clipboard.writeText(repo.html_url)}
                              className="hover:bg-gray-800"
                            >
                              Copy URL
                            </DropdownMenuItem>
                            <DropdownMenuSeparator />
                            <DropdownMenuItem
                              onClick={() => window.open(repo.html_url, '_blank')}
                              className="hover:bg-gray-800"
                            >
                              <ExternalLink className="mr-2 h-4 w-4" />
                              View on GitHub
                            </DropdownMenuItem>
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </td>
                    </tr>
                  )
                })
              ) : (
                <tr>
                  <td colSpan={8} className="h-24 text-center text-gray-400 px-4 py-4">
                    {isLoading ? "Loading recommendations..." : "No repositories found. Try adjusting your filters."}
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      <div className="flex items-center justify-between space-x-2 py-4">
        <div className="flex-1 text-sm text-gray-400">
          Showing {table.getFilteredRowModel().rows.length} repositories
        </div>
        <div className="space-x-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => table.previousPage()}
            disabled={!table.getCanPreviousPage()}
            className="bg-gray-800 text-gray-200 hover:bg-gray-700 border-gray-700"
          >
            Previous
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => table.nextPage()}
            disabled={!table.getCanNextPage()}
            className="bg-gray-800 text-gray-200 hover:bg-gray-700 border-gray-700"
          >
            Next
          </Button>
        </div>
      </div>
    </div>
  )
}
