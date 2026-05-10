"use client"

import * as React from "react"
import Link from "next/link"
import { usePathname } from "next/navigation"
import { ChevronRight } from "lucide-react"

import { cn } from "@/lib/utils"
import { ScrollArea } from "@/components/ui/scroll-area"

type NavItem = {
  title: string
  slug: string
  icon?: string
  children?: NavItem[]
}

export function DocsSidebar({ 
  navigation, 
  repoName,
  owner,
  repo
}: { 
  navigation: NavItem[]
  repoName: string
  owner: string
  repo: string
}) {
  const pathname = usePathname()
  const basePath = `/docs/${owner}/${repo}`

  const renderNavItems = (items: NavItem[], depth = 0) => {
    return (
      <ul className={cn("space-y-1", depth > 0 && "pl-4 ml-2 border-l")}>
        {items.map((item, index) => {
          const isGroup = item.children && item.children.length > 0
          const itemPath = `${basePath}/${item.slug === "index" || item.slug === "getting-started" ? item.slug : item.slug}`
          const isActive = pathname === itemPath || (item.slug === "index" && pathname === basePath)
          
          if (isGroup) {
            return (
              <li key={index} className="pt-2">
                <div className="font-semibold text-sm mb-1 text-foreground/90 flex items-center">
                  {item.title}
                </div>
                {renderNavItems(item.children || [], depth + 1)}
              </li>
            )
          }

          return (
            <li key={index}>
              <Link
                href={isActive ? "#" : itemPath}
                className={cn(
                  "block px-2 py-1.5 text-sm rounded-md transition-colors",
                  isActive 
                    ? "bg-primary/10 text-primary font-medium" 
                    : "text-muted-foreground hover:bg-muted hover:text-foreground"
                )}
              >
                {item.title}
              </Link>
            </li>
          )
        })}
      </ul>
    )
  }

  return (
    <aside className="fixed top-14 z-30 -ml-2 hidden h-[calc(100vh-3.5rem)] w-full shrink-0 md:sticky md:block md:w-64">
      <ScrollArea className="h-full py-6 pr-6 lg:py-8">
        <div className="mb-4 px-2 font-semibold tracking-tight text-lg">
          {repoName}
        </div>
        <div className="w-full">
          {renderNavItems(navigation)}
        </div>
      </ScrollArea>
    </aside>
  )
}
