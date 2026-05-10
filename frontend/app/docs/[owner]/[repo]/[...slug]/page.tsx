import * as React from "react"
import { notFound } from "next/navigation"
import { MarkdownRenderer } from "@/components/MarkdownRenderer"

async function getDocPage(owner: string, repo: string, slugParts: string[]) {
  try {
    const slug = slugParts.join("/")
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

export default async function DocPage({
  params,
}: {
  params: Promise<{ owner: string; repo: string; slug: string[] }>
}) {
  const resolvedParams = await params
  const data = await getDocPage(resolvedParams.owner, resolvedParams.repo, resolvedParams.slug)
  
  if (!data) {
    notFound()
  }

  return (
    <div className="pb-12 pt-8">
      <div className="mb-4 text-sm text-muted-foreground flex items-center space-x-2">
        <span>{resolvedParams.owner}/{resolvedParams.repo}</span>
        <span>/</span>
        <span className="text-foreground font-medium">{data.page.title}</span>
      </div>
      <MarkdownRenderer content={data.page.content_md} />
    </div>
  )
}
