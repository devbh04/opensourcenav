"use client"
import * as React from "react"
import { Menu, X } from "lucide-react"
import { Button } from "./ui/button"
import { DocsSidebar } from "./DocsSidebar"

export function MobileDocsNav({ 
  navigation, 
  repoName, 
  owner, 
  repo 
}: { 
  navigation: any[]
  repoName: string
  owner: string
  repo: string
}) {
  const [open, setOpen] = React.useState(false)

  return (
    <div className="md:hidden sticky top-14 z-40 w-full border-b bg-background/95 backdrop-blur px-4 py-2 flex items-center justify-between">
       <span className="font-semibold text-sm truncate">{repoName} Docs</span>
       <Button variant="ghost" size="sm" onClick={() => setOpen(!open)} className="px-2">
         {open ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
         <span className="sr-only">Toggle Docs Menu</span>
       </Button>
       
       {open && (
         <div className="absolute top-full left-0 w-full bg-background border-b shadow-lg p-4 max-h-[70vh] overflow-y-auto">
           <DocsSidebar 
             navigation={navigation} 
             repoName={repoName} 
             owner={owner} 
             repo={repo} 
             className="block relative top-0 h-auto w-full md:hidden" 
             onLinkClick={() => setOpen(false)}
           />
         </div>
       )}
    </div>
  )
}
