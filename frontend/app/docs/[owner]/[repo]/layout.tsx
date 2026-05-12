import * as React from "react"
import { notFound } from "next/navigation"

import { Navbar } from "@/components/Navbar"
import { DocsSidebar } from "@/components/DocsSidebar"
import { Chatbot } from "@/components/Chatbot"
import { MobileDocsNav } from "@/components/MobileDocsNav"

import clientPromise from "@/lib/mongodb"

async function getDocMeta(owner: string, repo: string) {
  try {
    const client = await clientPromise;
    const db = client.db(process.env.MONGODB_DB_NAME || "repodocify");
    const col = db.collection("docs");
    
    const doc = await col.findOne(
      { repo_name: `${owner}/${repo}` },
      { projection: { "pages.content_md": 0, _id: 0 } }
    );
    
    if (!doc) return null;
    
    return {
      meta: doc.meta || {},
      repo_name: doc.repo_name
    };
  } catch (e) {
    console.error("Error fetching doc meta in layout:", e);
    return null;
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
      <MobileDocsNav 
        navigation={navigation}
        repoName={`${resolvedParams.owner}/${resolvedParams.repo}`}
        owner={resolvedParams.owner}
        repo={resolvedParams.repo}
      />
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
