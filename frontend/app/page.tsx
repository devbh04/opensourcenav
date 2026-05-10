"use client"

import * as React from "react"
import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { ArrowRight, GitFork, BookOpen, Loader2, Clock, CheckCircle2, AlertCircle } from "lucide-react"

import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import { Badge } from "@/components/ui/badge"
import { Navbar } from "@/components/Navbar"

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

type QueueJob = {
  job_id: string
  repo_name: string
  status: string
  progress: number
  current_phase: string
  created_at: string
}

export default function LandingPage() {
  const [repoUrl, setRepoUrl] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const [jobId, setJobId] = useState<string | null>(null)
  const [progress, setProgress] = useState(0)
  const [statusText, setStatusText] = useState("")
  const [activeJobs, setActiveJobs] = useState<QueueJob[]>([])
  const router = useRouter()

  useEffect(() => {
    // Generate or fetch guest user ID
    if (!localStorage.getItem("guest_id")) {
      const id = "guest_" + Math.random().toString(36).substring(2, 15)
      localStorage.setItem("guest_id", id)
    }
  }, [])

  // Poll queue status so any visitor can see what's happening
  useEffect(() => {
    const fetchQueue = async () => {
      try {
        const res = await fetch(`${API_URL}/queue/status`)
        if (res.ok) {
          const data = await res.json()
          const jobs: QueueJob[] = []
          if (data.current_job) jobs.push(data.current_job)
          if (data.queue) jobs.push(...data.queue)
          setActiveJobs(jobs)
        }
      } catch {
        // Backend not running — that's ok
      }
    }

    fetchQueue()
    const interval = setInterval(fetchQueue, 5000) // poll every 5s
    return () => clearInterval(interval)
  }, [])

  useEffect(() => {
    if (!jobId) return

    // Connect to WebSocket
    const wsUrl = API_URL.replace("http", "ws")
    const ws = new WebSocket(`${wsUrl}/ws/progress/${jobId}`)
    
    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        setProgress(data.progress * 100)
        setStatusText(data.current_phase || "Processing...")
        
        if (data.status === "completed") {
          ws.close()
          const urlParts = repoUrl.replace(".git", "").split("/")
          const repo = urlParts.pop()
          const owner = urlParts.pop()
          if (owner && repo) {
            router.push(`/docs/${owner}/${repo}`)
          }
        } else if (data.status === "failed") {
          ws.close()
          setStatusText(`Failed: ${data.error}`)
          setIsLoading(false)
        }
      } catch (err) {
        console.error("Failed to parse WS message", err)
      }
    }

    return () => {
      ws.close()
    }
  }, [jobId, router, repoUrl])

  const [generatedDocs, setGeneratedDocs] = useState<any[]>([])
  const [totalDocs, setTotalDocs] = useState(0)
  const [skipDocs, setSkipDocs] = useState(0)
  const [hasMoreDocs, setHasMoreDocs] = useState(true)
  const [isLoadingDocs, setIsLoadingDocs] = useState(false)

  // Load initial generated docs
  useEffect(() => {
    const loadInitialDocs = async () => {
      try {
        setIsLoadingDocs(true)
        const res = await fetch(`${API_URL}/docs?skip=0&limit=16`)
        if (res.ok) {
          const data = await res.json()
          setGeneratedDocs(data.docs)
          setTotalDocs(data.total)
          setSkipDocs(16)
          setHasMoreDocs(data.total > 16)
        }
      } catch (e) {
        console.error("Failed to load generated docs", e)
      } finally {
        setIsLoadingDocs(false)
      }
    }
    loadInitialDocs()
  }, [])

  const loadMoreDocs = async () => {
    if (!hasMoreDocs || isLoadingDocs) return
    try {
      setIsLoadingDocs(true)
      const res = await fetch(`${API_URL}/docs?skip=${skipDocs}&limit=16`)
      if (res.ok) {
        const data = await res.json()
        setGeneratedDocs(prev => [...prev, ...data.docs])
        setSkipDocs(prev => prev + 16)
        setHasMoreDocs(generatedDocs.length + data.docs.length < data.total)
      }
    } catch (e) {
      console.error("Failed to load more docs", e)
    } finally {
      setIsLoadingDocs(false)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!repoUrl) return

    setIsLoading(true)
    setProgress(0)
    setStatusText("Checking repository...")
    
    // Extract owner and repo
    const urlParts = repoUrl.replace(".git", "").replace(/\/$/, "").split("/")
    const repo = urlParts.pop()
    const owner = urlParts.pop()

    if (owner && repo) {
      try {
        // Check if docs already exist
        const checkRes = await fetch(`${API_URL}/docs/${owner}/${repo}`)
        if (checkRes.ok) {
          setStatusText("Documentation already exists! Redirecting in 3 seconds...")
          setProgress(100)
          setTimeout(() => {
            router.push(`/docs/${owner}/${repo}`)
          }, 3000)
          return
        }
      } catch (e) {
        // Continue if check fails
      }
    }

    setStatusText("Queuing...")
    
    try {
      const guestId = localStorage.getItem("guest_id") || "guest_unknown"
      const res = await fetch(`${API_URL}/generate-docs`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ repo_url: repoUrl, user_id: guestId })
      })
      
      const data = await res.json()
      if (res.ok && data.success) {
        setJobId(data.job_id)
      } else {
        setStatusText(data.detail || "Failed to start generation")
        setIsLoading(false)
      }
    } catch (err) {
      setStatusText("Network error. Is the backend running?")
      setIsLoading(false)
    }
  }

  return (
    <div className="flex flex-col min-h-screen overflow-x-hidden">
      <Navbar />
      <main className="flex-1 flex flex-col items-center justify-center p-6 bg-linear-to-b from-background to-secondary/20">
        <div className="max-w-3xl w-full text-center space-y-8">
          <div className="space-y-4">
            <h1 className="text-4xl md:text-6xl font-bold tracking-tight">
              Turn any GitHub repo into <br className="hidden sm:block" />
              <span className="text-muted-foreground">Beautiful Documentation</span>
            </h1>
            <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
              Agentic analysis that reads the code, understands the abstractions, and generates Stripe-quality docs in minutes.
            </p>
          </div>

          {!jobId && !isLoading ? (
            <Card className="w-full max-w-xl mx-auto bg-background/50 backdrop-blur">
              <CardContent className="pt-6">
                <form 
                  onSubmit={(e) => {
                    e.preventDefault()
                    if (!repoUrl.trim()) return
                    // Check if docs already exist first
                    const urlParts = repoUrl.replace(".git", "").replace(/\/$/, "").split("/")
                    const repo = urlParts.pop()
                    const owner = urlParts.pop()
                    if (owner && repo) {
                      fetch(`${API_URL}/docs/${owner}/${repo}`)
                        .then(r => {
                          if (r.ok) {
                            setIsLoading(true)
                            setStatusText("Documentation already exists! Redirecting in 3 seconds...")
                            setProgress(100)
                            setTimeout(() => router.push(`/docs/${owner}/${repo}`), 3000)
                          } else {
                            router.push(`/generate?url=${encodeURIComponent(repoUrl.trim())}`)
                          }
                        })
                        .catch(() => router.push(`/generate?url=${encodeURIComponent(repoUrl.trim())}`))
                    }
                  }} 
                  className="flex flex-col sm:flex-row gap-3"
                >
                  <Input 
                    placeholder="https://github.com/owner/repo" 
                    className="flex-1 h-12 text-base"
                    value={repoUrl}
                    onChange={(e) => setRepoUrl(e.target.value)}
                    required
                  />
                  <Button type="submit" className="h-12 px-8 text-base" disabled={isLoading}>
                    {isLoading ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
                    Generate Docs <ArrowRight className="ml-2 h-4 w-4" />
                  </Button>
                </form>
              </CardContent>
            </Card>
          ) : (
            <Card className="w-full max-w-xl mx-auto bg-background/50 backdrop-blur">
              <CardHeader>
                <CardTitle>Generating Documentation</CardTitle>
                <CardDescription>{repoUrl}</CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-muted-foreground">{statusText}</span>
                    <span className="font-medium">{Math.round(progress)}%</span>
                  </div>
                  <Progress value={progress} className="h-2" />
                </div>
                {isLoading && progress < 100 && (
                  <div className="flex items-center justify-center text-sm text-muted-foreground">
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Our agents are analyzing the codebase...
                  </div>
                )}
              </CardContent>
            </Card>
          )}

          {/* Live Queue Status — visible to any visitor */}
          {activeJobs.length > 0 && !jobId && (
            <Card className="w-full max-w-xl mx-auto border-dashed border-muted-foreground/30 bg-muted/10">
              <CardHeader className="pb-3">
                <CardTitle className="text-base flex items-center gap-2">
                  <Clock className="h-4 w-4 text-muted-foreground animate-pulse" />
                  Queue Activity
                </CardTitle>
                <CardDescription>
                  {activeJobs.length} {activeJobs.length === 1 ? 'job' : 'jobs'} currently in the pipeline
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {activeJobs.slice(0, 3).map((job) => (
                    <div key={job.job_id} className="flex items-center justify-between gap-4 text-sm">
                      <div className="flex items-center gap-2 min-w-0">
                        {job.status === "processing" ? (
                          <Loader2 className="h-3.5 w-3.5 animate-spin text-primary shrink-0" />
                        ) : job.status === "completed" ? (
                          <CheckCircle2 className="h-3.5 w-3.5 text-green-500 shrink-0" />
                        ) : job.status === "failed" ? (
                          <AlertCircle className="h-3.5 w-3.5 text-destructive shrink-0" />
                        ) : (
                          <Clock className="h-3.5 w-3.5 text-muted-foreground shrink-0" />
                        )}
                        <span className="truncate text-foreground/80 font-mono text-xs">
                          {job.repo_name}
                        </span>
                      </div>
                      <Badge
                        variant={
                          job.status === "processing" ? "default" :
                          job.status === "completed" ? "secondary" :
                          job.status === "failed" ? "destructive" :
                          "outline"
                        }
                        className="shrink-0 text-[10px]"
                      >
                        {job.status === "processing"
                          ? `${Math.round(job.progress * 100)}%`
                          : job.status}
                      </Badge>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          <div className="grid sm:grid-cols-3 gap-6 pt-12">
            <div className="flex flex-col items-center text-center space-y-2 p-4">
              <div className="p-3 bg-secondary rounded-full">
                <GitFork className="h-6 w-6" />
              </div>
              <h3 className="font-semibold">Deep Code Analysis</h3>
              <p className="text-sm text-muted-foreground">Not just summaries. We understand function boundaries, abstractions, and design patterns.</p>
            </div>
            <div className="flex flex-col items-center text-center space-y-2 p-4">
              <div className="p-3 bg-secondary rounded-full">
                <BookOpen className="h-6 w-6" />
              </div>
              <h3 className="font-semibold">Modern Output</h3>
              <p className="text-sm text-muted-foreground">Gets you API references, architecture diagrams, and getting started guides out of the box.</p>
            </div>
            <div className="flex flex-col items-center text-center space-y-2 p-4">
              <div className="p-3 bg-secondary rounded-full">
                <ArrowRight className="h-6 w-6" />
              </div>
              <h3 className="font-semibold">Contextual Chat</h3>
              <p className="text-sm text-muted-foreground">RAG-powered chat directly inside the generated documentation. Ask anything.</p>
            </div>
          </div>
        </div>

        {/* Generated Repositories Section */}
        {generatedDocs.length > 0 && (
          <div className="max-w-5xl w-full mx-auto pt-16 pb-8">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-2xl font-bold tracking-tight">Explore Documentation</h2>
              <Badge variant="outline" className="text-muted-foreground">{totalDocs} total</Badge>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
              {generatedDocs.map((doc, i) => (
                <Card 
                  key={i} 
                  className="group cursor-pointer hover:border-primary/50 transition-colors bg-card/40 backdrop-blur"
                  onClick={() => {
                    const parts = doc.repo_name.split("/")
                    if (parts.length === 2) router.push(`/docs/${parts[0]}/${parts[1]}`)
                  }}
                >
                  <CardHeader className="p-4 pb-2">
                    <CardTitle className="text-base truncate group-hover:text-primary transition-colors">
                      {doc.repo_name.split("/")[1]}
                    </CardTitle>
                    <CardDescription className="text-xs truncate">
                      {doc.repo_name.split("/")[0]}
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="p-4 pt-2 flex items-center justify-between text-muted-foreground">
                    <div className="flex items-center gap-1.5 text-xs font-medium">
                      <BookOpen className="h-3.5 w-3.5" />
                      {doc.page_count} pages
                    </div>
                    {doc.languages && doc.languages.length > 0 && (
                      <Badge variant="secondary" className="text-[10px] px-1.5 py-0">
                        {doc.languages[0]}
                      </Badge>
                    )}
                  </CardContent>
                </Card>
              ))}
            </div>
            {hasMoreDocs && (
              <div className="mt-8 flex justify-center">
                <Button 
                  variant="outline" 
                  onClick={loadMoreDocs} 
                  disabled={isLoadingDocs}
                  className="w-full max-w-xs"
                >
                  {isLoadingDocs ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
                  Load More
                </Button>
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  )
}
