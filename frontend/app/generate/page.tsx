"use client"

import * as React from "react"
import { useState, useCallback, useEffect } from "react"
import { useRouter, useSearchParams } from "next/navigation"
import {
  ArrowRight, GitBranch, Loader2, ChevronRight, FileCode2,
  CheckCircle2, AlertCircle, Settings2, RotateCcw, Zap, Info
} from "lucide-react"
import { toast } from "sonner"

import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Navbar } from "@/components/Navbar"
import { FileExplorer, FileNode } from "@/components/FileExplorer"

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

const DEFAULT_INCLUDE = `*.py, *.js, *.ts, *.tsx, *.jsx, *.go, *.java, *.rs, *.cpp, *.c, *.h, *.rb, *.swift, *.kt, *.md, *.yaml, *.yml, *.toml, *.json, *.css, *.html, *.sh, Dockerfile, Makefile`
const DEFAULT_EXCLUDE = `node_modules/*, .git/*, __pycache__/*, *.pyc, dist/*, build/*, .next/*, .venv/*, venv/*, *.min.js, *.min.css, *.lock, *.log, *.tmp, .DS_Store`

type Step = "url" | "files" | "generating"

function GenerateContent() {
  const router = useRouter()
  const searchParams = useSearchParams()

  // Step state
  const [step, setStep] = useState<Step>("url")

  // Step 1 state
  const [repoUrl, setRepoUrl] = useState("")
  const [isFetching, setIsFetching] = useState(false)
  const [fetchError, setFetchError] = useState("")

  // Auto-trigger from homepage ?url= param
  useEffect(() => {
    const urlParam = searchParams?.get("url")
    if (urlParam && !repoUrl) {
      setRepoUrl(urlParam)
      // Auto-submit after setting URL
      setTimeout(() => {
        const fakeEvent = { preventDefault: () => {} } as React.FormEvent
        // We use a ref-based trigger below instead
      }, 100)
    }
  }, [searchParams])

  // Separate auto-fetch effect once repoUrl is set from param
  const [autoFetched, setAutoFetched] = useState(false)
  useEffect(() => {
    const urlParam = searchParams?.get("url")
    if (urlParam && !autoFetched && repoUrl === urlParam) {
      setAutoFetched(true)
      fetchRepo(urlParam)
    }
  }, [repoUrl, autoFetched, searchParams])

  // Step 2 state
  const [sessionId, setSessionId] = useState("")
  const [repoName, setRepoName] = useState("")
  const [fileTree, setFileTree] = useState<FileNode[]>([])
  const [allFilePaths, setAllFilePaths] = useState<string[]>([])
  const [selectedFiles, setSelectedFiles] = useState<Set<string>>(new Set())
  const [repoStats, setRepoStats] = useState<any>({})
  const [includePatterns, setIncludePatterns] = useState(DEFAULT_INCLUDE)
  const [excludePatterns, setExcludePatterns] = useState(DEFAULT_EXCLUDE)
  const [showPatterns, setShowPatterns] = useState(false)

  // Step 3 state
  const [jobId, setJobId] = useState<string | null>(null)
  const [progress, setProgress] = useState(0)
  const [statusText, setStatusText] = useState("")

  // ── Step 1: Fetch file tree ─────────────────────────────────────────

  const fetchRepo = async (url: string) => {
    if (!url.trim()) return

    setIsFetching(true)
    setFetchError("")

    try {
      const guestId = localStorage.getItem("guest_id") || "guest_unknown"
      const res = await fetch(`${API_URL}/prepare-repo`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ repo_url: url.trim(), user_id: guestId }),
      })

      if (!res.ok) {
        const err = await res.json()
        setFetchError(err.detail || "Failed to fetch repository")
        return
      }

      const data = await res.json()
      setSessionId(data.session_id)
      setRepoName(data.repo_name)
      setFileTree(data.file_tree)
      setAllFilePaths(data.all_files)
      setRepoStats(data.stats)

      // Pre-select files matching default include patterns
      const defaultIncludes = data.default_include || []
      const defaultExcludes = data.default_exclude || []
      const preSelected = new Set(
        (data.all_files as string[]).filter(f => {
          const ext = f.split(".").pop()?.toLowerCase() || ""
          const matchInclude = defaultIncludes.some((p: string) =>
            p.replace("*.", "") === ext || p === f.split("/").pop()
          )
          const matchExclude = defaultExcludes.some((p: string) =>
            f.startsWith(p.replace("/*", "").replace("/**", ""))
          )
          return matchInclude && !matchExclude
        })
      )
      
      const limitedPreSelected = new Set(Array.from(preSelected).slice(0, 40))
      if (preSelected.size > 40) {
        toast.warning("Only the first 40 matching files were pre-selected due to resource limits.")
      }
      setSelectedFiles(limitedPreSelected)
      setStep("files")
    } catch (err) {
      setFetchError("Network error. Is the backend running?")
    } finally {
      setIsFetching(false)
    }
  }

  const handleFetchRepo = async (e: React.FormEvent) => {
    e.preventDefault()
    await fetchRepo(repoUrl)
  }

  // ── Step 2: File selection handlers ─────────────────────────────────

  const handleSelectFile = useCallback((path: string, checked: boolean) => {
    setSelectedFiles(prev => {
      const next = new Set(prev)
      if (checked) {
        if (next.size >= 40) {
          toast.error("Maximum limit of 40 files reached.")
          return prev
        }
        next.add(path)
      } else {
        next.delete(path)
      }
      return next
    })
  }, [])

  const handleSelectAll = useCallback(() => {
    const nextFiles = allFilePaths.slice(0, 40)
    setSelectedFiles(new Set(nextFiles))
    if (allFilePaths.length > 40) {
      toast.warning("Select All applied, but limited to the maximum of 40 files.")
    }
  }, [allFilePaths])

  const handleClearAll = useCallback(() => {
    setSelectedFiles(new Set())
  }, [])

  const handleSelectFolder = useCallback((paths: string[], allSelected: boolean) => {
    setSelectedFiles(prev => {
      const next = new Set(prev)
      if (allSelected) {
        // All selected → deselect them
        paths.forEach(p => next.delete(p))
      } else {
        // Some or none selected → select all, up to 40
        let addedCount = 0
        let hitLimit = false
        for (const p of paths) {
          if (!next.has(p)) {
            if (next.size >= 40) {
              hitLimit = true
              break
            }
            next.add(p)
            addedCount++
          }
        }
        if (hitLimit) {
          toast.error("Maximum limit of 40 files reached.")
        }
      }
      return next
    })
  }, [])

  // ── Step 2 → 3: Start generation ────────────────────────────────────

  const handleGenerate = async () => {
    if (selectedFiles.size === 0) return
    setStep("generating")
    setProgress(0)
    setStatusText("Queuing job...")

    const parsePatterns = (str: string) =>
      str.split(/[,\n]/).map(s => s.trim().replace(/^["']|["']$/g, "")).filter(Boolean)

    try {
      const guestId = localStorage.getItem("guest_id") || "guest_unknown"
      const res = await fetch(`${API_URL}/generate-docs`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          repo_url: repoUrl.trim(),
          user_id: guestId,
          session_id: sessionId,
          selected_files: Array.from(selectedFiles),
          include_patterns: parsePatterns(includePatterns),
          exclude_patterns: parsePatterns(excludePatterns),
        }),
      })

      const data = await res.json()
      if (!res.ok || !data.success) {
        setStatusText(data.detail || "Failed to start generation")
        setStep("files")
        return
      }

      setJobId(data.job_id)

      // Connect to WebSocket for progress
      const wsUrl = API_URL.replace("http", "ws")
      const ws = new WebSocket(`${wsUrl}/ws/progress/${data.job_id}`)
      ws.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data)
          setProgress(msg.progress * 100)
          setStatusText(msg.current_phase || "Processing...")
          if (msg.status === "completed") {
            ws.close()
            const parts = repoUrl.replace(".git", "").split("/")
            const repo = parts.pop()
            const owner = parts.pop()
            if (owner && repo) router.push(`/docs/${owner}/${repo}`)
          } else if (msg.status === "failed") {
            ws.close()
            setStatusText(`Failed: ${msg.error}`)
          }
        } catch {}
      }
    } catch (err) {
      setStatusText("Network error.")
      setStep("files")
    }
  }

  // ── Render ──────────────────────────────────────────────────────────

  return (
    <div className="flex flex-col min-h-screen bg-background">
      <Navbar />

      <main className="flex-1 container max-w-6xl mx-auto px-4 py-10">
        
        {/* Step Indicator */}
        <div className="flex items-center gap-3 mb-8 text-sm">
          {[
            { id: "url", label: "1. Repository" },
            { id: "files", label: "2. Select Files" },
            { id: "generating", label: "3. Generating" },
          ].map((s, i) => (
            <React.Fragment key={s.id}>
              <span className={cn("font-medium transition-colors", step === s.id ? "text-primary" : "text-muted-foreground")}>
                {s.label}
              </span>
              {i < 2 && <ChevronRight className="h-4 w-4 text-muted-foreground/40 shrink-0" />}
            </React.Fragment>
          ))}
        </div>

        {/* ── Step 1: URL Entry ── */}
        {step === "url" && (
          <div className="max-w-xl mx-auto flex flex-col items-center text-center gap-8">
            <div className="space-y-2">
              <div className="p-4 bg-primary/10 rounded-full mx-auto w-fit">
                <GitBranch className="h-8 w-8 text-primary" />
              </div>
              <h1 className="text-3xl font-bold">Generate Documentation</h1>
              <p className="text-muted-foreground">Paste your GitHub repository URL to get started. We'll scan it and let you choose which files to analyze.</p>
            </div>

            <Card className="w-full">
              <CardContent className="pt-6">
                <form onSubmit={handleFetchRepo} className="flex flex-col gap-4">
                  <Input
                    placeholder="https://github.com/owner/repo"
                    value={repoUrl}
                    onChange={e => setRepoUrl(e.target.value)}
                    className="h-12 text-base"
                    required
                  />
                  {fetchError && (
                    <p className="text-sm text-destructive flex items-center gap-1.5">
                      <AlertCircle className="h-4 w-4" /> {fetchError}
                    </p>
                  )}
                  <Button type="submit" size="lg" disabled={isFetching || !repoUrl.trim()}>
                    {isFetching ? (
                      <><Loader2 className="mr-2 h-4 w-4 animate-spin" /> Cloning repository...</>
                    ) : (
                      <>Scan Repository <ArrowRight className="ml-2 h-4 w-4" /></>
                    )}
                  </Button>
                </form>
              </CardContent>
            </Card>
          </div>
        )}

        {/* ── Step 2: File Explorer ── */}
        {step === "files" && (
          <div className="flex flex-col gap-4 h-full">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-2xl font-bold">{repoName}</h1>
                <p className="text-sm text-muted-foreground mt-0.5">
                  {repoStats.total_files} files · {repoStats.total_size_mb}MB · {(repoStats.languages || []).slice(0, 3).join(", ")}
                </p>
              </div>
              <div className="flex items-center gap-2">
                <Button variant="outline" size="sm" onClick={() => { setStep("url"); setSessionId(""); }}>
                  <RotateCcw className="h-3.5 w-3.5 mr-1.5" /> Change Repo
                </Button>
                <Button size="sm" onClick={handleGenerate} disabled={selectedFiles.size === 0}>
                  <Zap className="h-3.5 w-3.5 mr-1.5" />
                  Generate Docs ({selectedFiles.size} files)
                </Button>
              </div>
            </div>

            <div className="text-amber-600 dark:text-amber-400 p-3 rounded-lg flex items-start gap-3 text-sm">
              <Info className="h-5 w-5 shrink-0 mt-0.5" />
              <div>
                <strong>Broke Engineer Alert 🚨:</strong> Due to limited cloud resources (and my shrinking bank account), you can only select a <strong>maximum of 40 files</strong> for documentation generation at a time. Choose your files wisely!
              </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-[1fr_340px] gap-4 flex-1">
              {/* File Tree */}
              <Card className="overflow-hidden flex flex-col" style={{ maxHeight: "70vh" }}>
                <CardHeader className="py-3 px-4 border-b bg-muted/30">
                  <CardTitle className="text-sm flex items-center gap-2">
                    <FileCode2 className="h-4 w-4" /> File Explorer
                    <Badge variant="secondary" className="ml-auto text-[10px]">
                      {selectedFiles.size} selected
                    </Badge>
                  </CardTitle>
                </CardHeader>
                <div className="flex-1 overflow-hidden">
                  <FileExplorer
                    tree={fileTree}
                    selectedFiles={selectedFiles}
                    allFilePaths={allFilePaths}
                    onSelectFile={handleSelectFile}
                    onSelectAll={handleSelectAll}
                    onClearAll={handleClearAll}
                    onSelectFolder={handleSelectFolder}
                  />
                </div>
              </Card>

              {/* Pattern Config */}
              <div className="flex flex-col gap-3">
                <Card>
                  <CardHeader className="py-3 px-4 border-b bg-muted/30 cursor-pointer" onClick={() => setShowPatterns(!showPatterns)}>
                    <CardTitle className="text-sm flex items-center gap-2">
                      <Settings2 className="h-4 w-4" /> Pattern Configuration
                      <ChevronRight className={cn("h-4 w-4 ml-auto text-muted-foreground transition-transform", showPatterns && "rotate-90")} />
                    </CardTitle>
                  </CardHeader>
                  {showPatterns && (
                    <CardContent className="pt-4 space-y-4">
                      <div>
                        <label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Include Patterns</label>
                        <p className="text-xs text-muted-foreground mb-1.5">Comma or newline-separated glob patterns</p>
                        <textarea
                          className="w-full rounded-md border bg-transparent px-3 py-2 text-xs min-h-[100px] resize-y focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
                          value={includePatterns}
                          onChange={e => setIncludePatterns(e.target.value)}
                        />
                      </div>
                      <div>
                        <label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Exclude Patterns</label>
                        <p className="text-xs text-muted-foreground mb-1.5">Patterns to ignore</p>
                        <textarea
                          className="w-full rounded-md border bg-transparent px-3 py-2 text-xs min-h-[100px] resize-y focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
                          value={excludePatterns}
                          onChange={e => setExcludePatterns(e.target.value)}
                        />
                      </div>
                    </CardContent>
                  )}
                </Card>

                <Card className="bg-muted/20">
                  <CardContent className="pt-4 space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Selected</span>
                      <span className="font-semibold">{selectedFiles.size} files</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Total available</span>
                      <span>{allFilePaths.length} files</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Repo size</span>
                      <span>{repoStats.total_size_mb} MB</span>
                    </div>
                  </CardContent>
                </Card>

                <Button
                  size="lg"
                  className="w-full"
                  onClick={handleGenerate}
                  disabled={selectedFiles.size === 0}
                >
                  <Zap className="mr-2 h-4 w-4" />
                  Generate Documentation
                  <span className="ml-auto text-xs opacity-70">({selectedFiles.size} files)</span>
                </Button>
              </div>
            </div>
          </div>
        )}

        {/* ── Step 3: Generating ── */}
        {step === "generating" && (
          <div className="max-w-lg mx-auto flex flex-col items-center text-center gap-8 pt-16">
            <div className="relative">
              <div className="p-6 bg-primary/10 rounded-full">
                <Loader2 className="h-12 w-12 text-primary animate-spin" />
              </div>
            </div>
            <div className="space-y-2 w-full">
              <h2 className="text-2xl font-bold">Generating Documentation</h2>
              <p className="text-muted-foreground">{repoName} · {selectedFiles.size} files selected</p>
            </div>

            <Card className="w-full">
              <CardContent className="pt-6 space-y-4">
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">{statusText || "Starting..."}</span>
                  <span className="font-semibold">{Math.round(progress)}%</span>
                </div>
                <div className="w-full bg-secondary rounded-full h-2">
                  <div
                    className="bg-primary h-2 rounded-full transition-all duration-500 ease-out"
                    style={{ width: `${progress}%` }}
                  />
                </div>
                <p className="text-xs text-muted-foreground">
                  Our AI agents are analyzing {selectedFiles.size} files. This typically takes 3–8 minutes.
                </p>
              </CardContent>
            </Card>
          </div>
        )}
      </main>
    </div>
  )
}

export default function GeneratePage() {
  return (
    <React.Suspense fallback={<div className="flex items-center justify-center min-h-screen"><Loader2 className="h-8 w-8 animate-spin" /></div>}>
      <GenerateContent />
    </React.Suspense>
  )
}

function cn(...classes: (string | boolean | undefined)[]) {
  return classes.filter(Boolean).join(" ")
}
