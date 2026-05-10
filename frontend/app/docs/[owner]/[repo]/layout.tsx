import * as React from "react"
import { notFound } from "next/navigation"

import { Navbar } from "@/components/Navbar"
import { DocsSidebar } from "@/components/DocsSidebar"
import { Chatbot } from "@/components/Chatbot"

async function getDocMeta(owner: string, repo: string) {
  try {
    const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    const res = await fetch(`${API_URL}/docs/${owner}/${repo}`, {
      next: { revalidate: 60 } // Cache for 60s
    })
    if (!res.ok) return null
    return await res.json()
  } catch (e) {
    return null
  }
}

export default async function DocsLayout({
  children,
  params,
}: {
  children: React.ReactNode
  params: Promise<{ owner: string; repo: string }>
}) {
  const resolvedParams = await params
  const meta = await getDocMeta(resolvedParams.owner, resolvedParams.repo)
  
  if (!meta) {
    notFound()
  }

  const navigation = meta.meta?.navigation || []

  return (
    <div className="flex min-h-screen flex-col">
      <Navbar />
      <div className="container flex-1 items-start md:grid md:grid-cols-[220px_minmax(0,1fr)] md:gap-6 lg:grid-cols-[240px_minmax(0,1fr)] lg:gap-10 max-w-7xl mx-auto px-4 md:px-8">
        <DocsSidebar 
          navigation={navigation} 
          repoName={`${resolvedParams.owner}/${resolvedParams.repo}`}
          owner={resolvedParams.owner}
          repo={resolvedParams.repo}
        />
        <main className="relative py-6 lg:gap-10 lg:py-8 xl:grid xl:grid-cols-[1fr_200px]">
          <div className="mx-auto w-full min-w-0">
            {children}
          </div>
          {/* Optional Right Table of Contents could go here in the xl grid */}
        </main>
      </div>
      <Chatbot repoName={`${resolvedParams.owner}/${resolvedParams.repo}`} />
    </div>
  )
}
