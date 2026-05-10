"use client"

import * as React from "react"
import { useState } from "react"
import { Search, Star, GitFork, AlertCircle, Loader2, Code2 } from "lucide-react"

import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Navbar } from "@/components/Navbar"

type RepoResult = {
  full_name: string
  description: string
  html_url: string
  stargazers_count: number
  forks_count: number
  language: string
  topics: string[]
  open_issues_count: number
  relevance_score: number
  relevance_reasons: string[]
}

export default function FindReposPage() {
  const [query, setQuery] = useState("")
  
  const [isLoading, setIsLoading] = useState(false)
  const [results, setResults] = useState<RepoResult[]>([])
  const [hasSearched, setHasSearched] = useState(false)

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!query.trim()) return

    setIsLoading(true)
    setHasSearched(true)
    
    try {
      const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const res = await fetch(`${API_URL}/find-repos`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          query: query.trim()
        })
      })
      
      const data = await res.json()
      if (res.ok) {
        setResults(data.repositories || [])
      } else {
        setResults([])
      }
    } catch (err) {
      console.error("Failed to search repos", err)
      setResults([])
    } finally {
      setIsLoading(false)
    }
  }

  const sampleQueries = [
    "A repo that isn't that famous but people actively contribute to",
    "Agent skills repos with good first issues",
    "The best open-source repository for my React and Next.js tech stack"
  ]

  return (
    <div className="flex min-h-screen flex-col bg-background">
      <Navbar />
      <main className="flex-1 container max-w-5xl mx-auto px-4 md:px-8 py-12">
        
        {/* Header & Search Section */}
        <div className="flex flex-col items-center text-center space-y-6 mb-12">
          <div className="space-y-2">
            <h1 className="text-4xl font-bold tracking-tight">Find Repos</h1>
            <p className="text-lg text-muted-foreground max-w-2xl">
              Describe exactly what you're looking for. Our AI agents will translate your intent into optimal GitHub search strategies and find the perfect match.
            </p>
          </div>

          <Card className="w-full max-w-3xl border-muted/60 bg-card/50 backdrop-blur shadow-sm">
            <CardContent className="pt-6">
              <form onSubmit={handleSearch} className="flex flex-col gap-4">
                <div className="space-y-2 text-left w-full">
                  <label className="text-sm font-medium text-muted-foreground uppercase tracking-wider pl-1">Describe Your Ideal Repository</label>
                  <textarea 
                    placeholder="e.g. A repo that isn't that famous but people contribute in..." 
                    value={query}
                    onChange={e => setQuery(e.target.value)}
                    required
                    className="flex w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm shadow-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50 min-h-[100px] resize-y"
                  />
                </div>
                <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                  <div className="flex flex-wrap gap-2">
                    {sampleQueries.map((sample, i) => (
                      <Badge 
                        key={i} 
                        variant="secondary" 
                        className="cursor-pointer hover:bg-secondary/80 text-[10px] font-normal px-2 py-0.5"
                        onClick={() => setQuery(sample)}
                      >
                        {sample}
                      </Badge>
                    ))}
                  </div>
                  <Button type="submit" size="lg" className="h-11 w-full md:w-32 shrink-0" disabled={isLoading || !query.trim()}>
                    {isLoading ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Search className="mr-2 h-4 w-4" />}
                    Search
                  </Button>
                </div>
              </form>
            </CardContent>
          </Card>
        </div>

        {/* Results Section */}
        <div className="w-full">
          {isLoading ? (
            <div className="flex flex-col items-center justify-center py-20 space-y-4 text-muted-foreground">
              <Loader2 className="h-10 w-10 animate-spin text-primary/50" />
              <p className="animate-pulse">Agents are analyzing GitHub repositories for you...</p>
            </div>
          ) : hasSearched && results.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-20 space-y-4 text-muted-foreground text-center bg-muted/20 rounded-xl border border-dashed">
              <AlertCircle className="h-12 w-12 text-muted" />
              <p>No repositories found matching your criteria. Try broadening your search.</p>
            </div>
          ) : (
            <div className="grid gap-6 md:grid-cols-2">
              {results.map((repo, i) => (
                <Card key={i} className="flex flex-col hover:border-primary/50 transition-colors shadow-sm bg-card/60 backdrop-blur">
                  <CardHeader className="pb-3">
                    <div className="flex justify-between items-start gap-4">
                      <CardTitle className="text-xl leading-tight">
                        <a href={repo.html_url} target="_blank" rel="noreferrer" className="hover:text-primary transition-colors hover:underline underline-offset-4">
                          {repo.full_name}
                        </a>
                      </CardTitle>
                      {repo.language && (
                        <Badge variant="secondary" className="shrink-0 flex items-center gap-1 font-medium bg-primary/10 text-primary border-primary/20">
                          <Code2 className="h-3 w-3" />
                          {repo.language}
                        </Badge>
                      )}
                    </div>
                    <CardDescription className="line-clamp-2 min-h-10 mt-2 text-sm text-foreground/70">
                      {repo.description || "No description provided."}
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="flex-1 pb-4">
                    <div className="flex flex-wrap gap-4 text-sm font-medium text-muted-foreground mb-5">
                      <div className="flex items-center gap-1.5 bg-muted/40 px-2 py-1 rounded-md">
                        <Star className="h-4 w-4 text-yellow-500" /> {repo.stargazers_count.toLocaleString()}
                      </div>
                      <div className="flex items-center gap-1.5 bg-muted/40 px-2 py-1 rounded-md">
                        <GitFork className="h-4 w-4" /> {repo.forks_count.toLocaleString()}
                      </div>
                      <div className="flex items-center gap-1.5 bg-muted/40 px-2 py-1 rounded-md">
                        <AlertCircle className="h-4 w-4" /> {repo.open_issues_count} issues
                      </div>
                    </div>
                    <div className="bg-secondary/40 rounded-lg p-3.5 text-sm border border-border/50">
                      <span className="font-semibold text-xs uppercase text-primary/80 mb-2 block tracking-wider">Why it's a match</span>
                      <ul className="space-y-1.5 text-foreground/80">
                        {repo.relevance_reasons.slice(0, 2).map((reason, j) => (
                          <li key={j} className="flex items-start gap-2">
                            <span className="text-primary mt-0.5">•</span>
                            <span className="line-clamp-2 leading-tight">{reason}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  </CardContent>
                  <CardFooter className="pt-0 pb-5">
                    <div className="flex flex-wrap gap-1.5">
                      {repo.topics.slice(0, 4).map((topic, j) => (
                        <Badge key={j} variant="outline" className="text-[10px] uppercase font-medium bg-background/50 hover:bg-muted transition-colors">
                          {topic}
                        </Badge>
                      ))}
                    </div>
                  </CardFooter>
                </Card>
              ))}
            </div>
          )}
        </div>
      </main>
    </div>
  )
}
