import * as React from "react"
import { notFound } from "next/navigation"
import { MarkdownRenderer } from "@/components/MarkdownRenderer"

import clientPromise from "@/lib/mongodb"

async function getDocPage(owner: string, repo: string, slugParts: string[]) {
  try {
    const target_slug = slugParts.join("/").replace(/^\/|\/$/g, "");
    const repo_name = `${owner}/${repo}`;
    
    const client = await clientPromise;
    const db = client.db(process.env.MONGODB_DB_NAME || "repodocify");
    const col = db.collection("docs");
    
    const doc = await col.findOne({ repo_name }, { projection: { _id: 0 } });
    if (!doc) return null;
    
    const pages = doc.pages || [];
    let foundPage = null;
    for (const page of pages) {
      if (page.slug.replace(/^\/|\/$/g, "") === target_slug) {
        foundPage = page;
        break;
      }
    }
    
    if (!foundPage) return null;
    
    return {
      page: foundPage,
      meta: doc.meta || {},
      repo_name
    };
  } catch (e) {
    console.error("Error fetching doc page:", e);
    return null;
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
