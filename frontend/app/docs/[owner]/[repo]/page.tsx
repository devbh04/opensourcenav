import * as React from "react"
import { notFound } from "next/navigation"
import { MarkdownRenderer } from "@/components/MarkdownRenderer"

async function getDocPage(owner: string, repo: string, slug: string) {
  try {
    const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    const res = await fetch(`${API_URL}/docs/${owner}/${repo}/${slug}`, {
      next: { revalidate: 60 }
    })
    if (!res.ok) return null
    return await res.json()
  } catch (e) {
    return null
  }
}

export default async function DocsIndexPage({
  params,
}: {
  params: Promise<{ owner: string; repo: string }>
}) {
  const resolvedParams = await params
  const data = await getDocPage(resolvedParams.owner, resolvedParams.repo, "index")
  
  if (!data) {
    notFound()
  }

  return (
    <div className="pb-12 pt-8">
      <MarkdownRenderer content={data.page.content_md} />
    </div>
  )
}
