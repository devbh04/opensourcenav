"use client"

import * as React from "react"
import { useSearchParams } from "next/navigation"
import { useResolutionStore } from "@/store/resolution-store"
import { ResolutionForm } from "@/components/resolution/resolution-form"
import { ResolutionDisplay } from "@/components/resolution/resolution-display"
import { ErrorDisplay } from "@/components/issues/error-display"
import { ChatQABox } from "@/components/chat/chat-qa-box"
import { Suspense } from "react"

function ResolutionPageContent() {
  const searchParams = useSearchParams()
  const { setRepoUrl, setIssueUrl, error, response, comprehensiveResponse } = useResolutionStore()
  
  React.useEffect(() => {
    const repoUrl = searchParams.get('repo_url')
    const issueUrl = searchParams.get('issue_url')
    
    if (repoUrl) setRepoUrl(repoUrl)
    if (issueUrl) setIssueUrl(issueUrl)
  }, [searchParams, setRepoUrl, setIssueUrl])

  // Show chatbot only when there's resolution content
  const shouldShowChatbot = response || comprehensiveResponse

  return (
    <div className="min-h-screen bg-black text-white">
      <div className="container mx-auto px-4 py-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-white mb-2">Issue Resolution</h1>
          <p className="text-gray-400">Get AI-powered step-by-step guidance to resolve GitHub issues</p>
        </div>

        <div className="space-y-8">
          <ResolutionForm />
          
          {error && (
            <ErrorDisplay message={error} />
          )}
          
          <ResolutionDisplay />
        </div>
      </div>
      
      {/* Show ChatQABox only when there's resolution content */}
      {shouldShowChatbot && <ChatQABox image={"/resolve-logo.png"}/>}
    </div>
  )
}

export default function ResolutionPage() {
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <ResolutionPageContent />
    </Suspense>
  )
}