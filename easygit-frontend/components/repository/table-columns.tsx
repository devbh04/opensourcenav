import { ColumnDef } from "@tanstack/react-table"
import { ArrowUpDown, MoreHorizontal, Star, GitFork, ExternalLink } from "lucide-react"
import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { Repository } from "@/store/repository-store"

export const columns: ColumnDef<Repository>[] = [
  {
    accessorKey: "full_name",
    header: ({ column }) => {
      return (
        <Button
          variant="ghost"
          onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
        >
          Repository
          <ArrowUpDown className="ml-2 h-4 w-4" />
        </Button>
      )
    },
    cell: ({ row }) => {
      const repo = row.original
      return (
        <div className="flex items-start gap-2 py-1 w-full overflow-hidden">
          <div className="w-5 h-5 rounded-full flex-shrink-0 bg-gray-700 flex items-center justify-center">
            <span className="text-xs font-medium text-gray-300">
              {(repo.full_name || 'U').charAt(0).toUpperCase()}
            </span>
          </div>
          <div className="space-y-1 min-w-0 flex-1 overflow-hidden">
            <div 
              className="font-medium text-white hover:text-blue-400 transition-colors cursor-pointer truncate text-sm"
              onClick={() => window.open(repo.html_url, '_blank')}
            >
              {repo.full_name || 'Unknown'}
            </div>
            <div className="text-xs text-gray-400 leading-tight line-clamp-1">
              {repo.description || 'No description available'}
            </div>
            <div className="flex flex-wrap gap-1 overflow-hidden">
              {(repo.topics || []).slice(0, 2).map((topic) => (
                <span
                  key={topic}
                  className="inline-flex items-center px-1.5 py-0.5 rounded text-xs bg-gray-800 text-gray-300 border border-gray-700 flex-shrink-0"
                >
                  {topic}
                </span>
              ))}
              {(repo.topics || []).length > 2 && (
                <span className="text-xs text-gray-500">
                  +{(repo.topics || []).length - 2}
                </span>
              )}
            </div>
          </div>
        </div>
      )
    },
  },
  {
    accessorKey: "language",
    header: "Language",
    cell: ({ row }) => {
      const language = row.getValue("language") as string
      const getLanguageColor = (lang: string) => {
        if (!lang) return "bg-gray-800/50 text-gray-300 border-gray-700/50"
        switch (lang.toLowerCase()) {
          case "javascript":
            return "bg-yellow-500/10 text-yellow-400 border border-yellow-500/20"
          case "typescript":
            return "bg-blue-500/10 text-blue-400 border border-blue-500/20"
          case "python":
            return "bg-green-500/10 text-green-400 border border-green-500/20"
          case "go":
            return "bg-cyan-500/10 text-cyan-400 border border-cyan-500/20"
          case "rust":
            return "bg-orange-500/10 text-orange-400 border border-orange-500/20"
          case "java":
            return "bg-red-500/10 text-red-400 border border-red-500/20"
          default:
            return "bg-purple-500/10 text-purple-400 border border-purple-500/20"
        }
      }
      
      return language ? (
        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getLanguageColor(language)}`}>
          {language}
        </span>
      ) : (
        <span className="text-gray-400 text-sm">N/A</span>
      )
    },
  },
  {
    accessorKey: "stargazers_count",
    header: ({ column }) => {
      return (
        <Button
          variant="ghost"
          onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
        >
          <Star className="mr-2 h-4 w-4" />
          Stars
          <ArrowUpDown className="ml-2 h-4 w-4" />
        </Button>
      )
    },
    cell: ({ row }) => {
      const stars = row.getValue("stargazers_count") as number
      return (
        <div className="flex items-center justify-end space-x-2">
          <Star className="h-4 w-4 text-yellow-400" />
          <span className="text-gray-300 font-medium tabular-nums">{(stars || 0).toLocaleString()}</span>
        </div>
      )
    },
  },
  {
    accessorKey: "forks_count",
    header: "Forks",
    cell: ({ row }) => {
      const forks = row.getValue("forks_count") as number
      return (
        <div className="flex items-center justify-end space-x-2">
          <GitFork className="h-4 w-4 text-gray-400" />
          <span className="text-gray-300 font-medium tabular-nums">{(forks || 0).toLocaleString()}</span>
        </div>
      )
    },
  },
  {
    accessorKey: "personalized_score",
    header: ({ column }) => {
      return (
        <Button
          variant="ghost"
          onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
        >
          Score
          <ArrowUpDown className="ml-2 h-4 w-4" />
        </Button>
      )
    },
    cell: ({ row }) => {
      const score = row.getValue("personalized_score") as number
      const getScoreVariant = (score: number) => {
        if (score >= 80) return "bg-green-500/10 text-green-400 border border-green-500/20"
        if (score >= 60) return "bg-yellow-500/10 text-yellow-400 border border-yellow-500/20"
        return "bg-red-500/10 text-red-400 border border-red-500/20"
      }
      return (
        <div className="text-right">
          <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getScoreVariant(score || 0)}`}>
            {(score || 0).toFixed(1)}
          </span>
        </div>
      )
    },
  },
  {
    accessorKey: "learning_level",
    header: "Level",
    cell: ({ row }) => {
      const level = row.getValue("learning_level") as string
      const getLevelVariant = (level: string) => {
        if (!level) return "bg-gray-800/50 text-gray-300 border border-gray-700/50"
        switch (level.toLowerCase()) {
          case "beginner": return "bg-green-500/10 text-green-400 border border-green-500/20"
          case "intermediate": return "bg-yellow-500/10 text-yellow-400 border border-yellow-500/20"
          case "advanced": return "bg-red-500/10 text-red-400 border border-red-500/20"
          default: return "bg-purple-500/10 text-purple-400 border border-purple-500/20"
        }
      }
      return (
        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getLevelVariant(level)}`}>
          {level || "Unknown"}
        </span>
      )
    },
  },
  {
    accessorKey: "has_good_first_issues",
    header: "Good First Issues",
    cell: ({ row }) => {
      const hasGoodFirstIssues = row.getValue("has_good_first_issues") as boolean
      return (
        <div className="flex items-center justify-center space-x-2">
          <div className={`w-2 h-2 rounded-full ${hasGoodFirstIssues ? 'bg-green-400' : 'bg-gray-500'}`} />
          <span className={`text-sm font-medium ${hasGoodFirstIssues ? 'text-green-400' : 'text-gray-400'}`}>
            {hasGoodFirstIssues ? 'Yes' : 'No'}
          </span>
        </div>
      )
    },
  },
  {
    id: "actions",
    enableHiding: false,
    cell: ({ row }) => {
      const repo = row.original

      return (
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" className="h-8 w-8 p-0 text-gray-400 hover:text-white hover:bg-gray-800/50 transition-colors">
              <span className="sr-only">Open menu</span>
              <MoreHorizontal className="h-4 w-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="bg-gray-900 border-gray-800 text-gray-200">
            <DropdownMenuLabel className="text-gray-300">Actions</DropdownMenuLabel>
            <DropdownMenuItem
              onClick={() => navigator.clipboard.writeText(repo.html_url)}
              className="hover:bg-gray-800 text-gray-200 hover:text-white focus:bg-gray-800"
            >
              Copy repository URL
            </DropdownMenuItem>
            <DropdownMenuSeparator className="bg-gray-800" />
            <DropdownMenuItem
              onClick={() => window.open(repo.html_url, '_blank')}
              className="hover:bg-gray-800 text-gray-200 hover:text-white focus:bg-gray-800"
            >
              <ExternalLink className="mr-2 h-4 w-4" />
              View on GitHub
            </DropdownMenuItem>
            <DropdownMenuItem className="hover:bg-gray-800 text-gray-200 hover:text-white focus:bg-gray-800">
              Generate Tutorial
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      )
    },
  },
]
