import * as React from "react"
import { useRouter } from "next/navigation"
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
import { ChevronDown, ArrowUpDown, ExternalLink, MoreHorizontal, Calendar, User, Wrench } from "lucide-react"

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
import { useIssueStore, Issue } from "@/store/issue-store"

export function IssueTable() {
  const { issues, isLoading, totalCount, repository } = useIssueStore()
  const router = useRouter()
  const [sorting, setSorting] = React.useState<SortingState>([])
  const [columnFilters, setColumnFilters] = React.useState<ColumnFiltersState>([])
  const [columnVisibility, setColumnVisibility] = React.useState<VisibilityState>({})

  // Define columns inline for better control
  const columns = React.useMemo(() => [
    {
      id: "title",
      accessorKey: "title",
      header: "Issue",
      size: 400,
    },
    {
      id: "state", 
      accessorKey: "state",
      header: "State",
      size: 100,
    },
    {
      id: "user",
      accessorKey: "user",
      header: "Author",
      size: 120,
    },
    {
      id: "labels",
      accessorKey: "labels",
      header: "Labels",
      size: 200,
    },
    {
      id: "created_at",
      accessorKey: "created_at",
      header: "Created",
      size: 120,
    },
    {
      id: "actions",
      header: "",
      size: 60,
      enableSorting: false,
    }
  ], [])

  const table = useReactTable({
    data: issues,
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

  const getStateColor = (state: string) => {
    switch (state.toLowerCase()) {
      case "open": return "bg-green-500 text-white"
      case "closed": return "bg-red-500 text-white"
      default: return "bg-gray-500 text-white"
    }
  }

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    })
  }

  if (!issues.length && !isLoading) {
    return (
      <div className="text-center py-12 text-gray-400">
        <p>No issues to display. Use the form above to analyze repository issues.</p>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {repository && (
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <h3 className="text-lg font-medium text-white">
              Issues from {repository.fullName}
            </h3>
            <Input
              placeholder="Filter issues..."
              value={(table.getColumn("title")?.getFilterValue() as string) ?? ""}
              onChange={(event) =>
                table.getColumn("title")?.setFilterValue(event.target.value)
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
            {totalCount} total issues
          </div>
        </div>
      )}

      <div className="border border-gray-700 rounded-lg bg-gray-800/50 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-black/20 border-b border-gray-700">
              <tr>
                <th className="w-[400px] px-4 py-3 text-left font-medium text-gray-200 text-sm">
                  <Button
                    variant="ghost"
                    onClick={() => table.getColumn("title")?.toggleSorting()}
                    className="text-gray-200 hover:text-white p-0 h-auto font-medium"
                  >
                    Issue
                    <ArrowUpDown className="ml-2 h-4 w-4" />
                  </Button>
                </th>
                <th className="w-[100px] px-4 py-3 text-left font-medium text-gray-200 text-sm">State</th>
                <th className="w-[120px] px-4 py-3 text-left font-medium text-gray-200 text-sm">Author</th>
                <th className="w-[200px] px-4 py-3 text-left font-medium text-gray-200 text-sm">Labels</th>
                <th className="w-[120px] px-4 py-3 text-left font-medium text-gray-200 text-sm">
                  <Button
                    variant="ghost"
                    onClick={() => table.getColumn("created_at")?.toggleSorting()}
                    className="text-gray-200 hover:text-white p-0 h-auto font-medium"
                  >
                    <Calendar className="mr-2 h-4 w-4" />
                    Created
                    <ArrowUpDown className="ml-2 h-4 w-4" />
                  </Button>
                </th>
                <th className="w-[60px] px-4 py-3 text-left font-medium text-gray-200 text-sm"></th>
              </tr>
            </thead>
            <tbody className="bg-black">
              {table.getRowModel().rows?.length ? (
                table.getRowModel().rows.map((row, index) => {
                  const issue = row.original as Issue
                  return (
                    <tr
                      key={row.id}
                      className={`border-b border-gray-700/50 hover:bg-gray-800/30 transition-colors bg-black`}
                    >
                      {/* Issue Column */}
                      <td className="w-[400px] px-4 py-3">
                        <div className="space-y-1">
                          <div 
                            className="font-medium text-white hover:text-blue-400 cursor-pointer line-clamp-2"
                            onClick={() => window.open(issue.html_url, '_blank')}
                          >
                            {issue.title}
                          </div>
                          {issue.body && (
                            <div className="text-sm text-gray-400 line-clamp-2">
                              {issue.body.substring(0, 150)}...
                            </div>
                          )}
                        </div>
                      </td>
                      
                      {/* State Column */}
                      <td className="w-[100px] px-4 py-3">
                        <span className={`px-2 py-1 rounded text-xs font-medium ${getStateColor(issue.state)}`}>
                          {issue.state}
                        </span>
                      </td>
                      
                      {/* Author Column */}
                      <td className="w-[120px] px-4 py-3">
                        <div className="flex items-center space-x-2">
                          <User className="h-4 w-4 text-gray-400" />
                          <span className="text-gray-300 text-sm truncate">
                            {issue.user.login}
                          </span>
                        </div>
                      </td>
                      
                      {/* Labels Column */}
                      <td className="w-[200px] px-4 py-3">
                        <div className="flex flex-wrap gap-1">
                          {issue.labels.slice(0, 3).map((label) => (
                            <span
                              key={label.name}
                              className="px-2 py-1 text-xs rounded"
                              style={{ 
                                backgroundColor: `#${label.color}`,
                                color: parseInt(label.color, 16) > 0xffffff/2 ? '#000' : '#fff'
                              }}
                            >
                              {label.name}
                            </span>
                          ))}
                          {issue.labels.length > 3 && (
                            <span className="text-xs text-gray-500">
                              +{issue.labels.length - 3}
                            </span>
                          )}
                        </div>
                      </td>
                      
                      {/* Created Column */}
                      <td className="w-[120px] px-4 py-3">
                        <div className="flex items-center space-x-2">
                          <Calendar className="h-4 w-4 text-gray-400" />
                          <span className="text-gray-300 text-sm">
                            {formatDate(issue.created_at)}
                          </span>
                        </div>
                      </td>
                      
                      {/* Actions Column */}
                      <td className="w-[60px] px-4 py-3">
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button variant="ghost" className="h-8 w-8 p-0 hover:bg-black hover:border text-gray-400 hover:text-white">
                              <MoreHorizontal className="h-4 w-4" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end" className="bg-gray-900 border-gray-800 text-gray-200">
                            <DropdownMenuLabel>Actions</DropdownMenuLabel>
                            <DropdownMenuItem
                              onClick={() => {
                                const repoUrl = repository ? `https://github.com/${repository.owner}/${repository.repo}` : ''
                                const issueUrl = issue.html_url
                                const params = new URLSearchParams({
                                  repo_url: repoUrl,
                                  issue_url: issueUrl
                                })
                                router.push(`/issues/resolution?${params.toString()}`)
                              }}
                              className="hover:bg-gray-800"
                            >
                              <Wrench className="mr-2 h-4 w-4" />
                              Resolve Issue
                            </DropdownMenuItem>
                            <DropdownMenuSeparator />
                            <DropdownMenuItem
                              onClick={() => navigator.clipboard.writeText(issue.html_url)}
                              className="hover:bg-gray-800"
                            >
                              Copy URL
                            </DropdownMenuItem>
                            <DropdownMenuItem
                              onClick={() => window.open(issue.html_url, '_blank')}
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
                  <td colSpan={6} className="h-24 text-center text-gray-400 px-4 py-4">
                    {isLoading ? "Loading issues..." : "No issues found. Try adjusting your filters."}
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {issues.length > 0 && (
        <div className="flex items-center justify-between space-x-2 py-4">
          <div className="flex-1 text-sm text-gray-400">
            Showing {table.getFilteredRowModel().rows.length} of {totalCount} issues
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
      )}
    </div>
  )
}
