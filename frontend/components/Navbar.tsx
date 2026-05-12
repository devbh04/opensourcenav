"use client"

import * as React from "react"
import Link from "next/link"
import { useTheme } from "next-themes"
import { BookOpen, Moon, Sun, GitFork } from "lucide-react"

import { Button } from "@/components/ui/button"

export function Navbar() {
  const { setTheme, theme } = useTheme()

  const [isMobileMenuOpen, setIsMobileMenuOpen] = React.useState(false)

  return (
    <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-backdrop-filter:bg-background/60">
      <div className="container flex h-14 items-center px-4 md:px-8 max-w-7xl mx-auto justify-between">
        <div className="flex items-center gap-4">
          <Link href="/" className="flex items-center space-x-2">
            <span className="font-bold sm:inline-block">
              EasyGit
            </span>
          </Link>
          <nav className="hidden md:flex items-center space-x-6 text-sm font-medium ml-6">
            <Link href="/" className="transition-colors hover:text-foreground/80 text-foreground">Home</Link>
            <Link href="/generate" className="transition-colors hover:text-foreground/80 text-foreground/60">Generate</Link>
            <Link href="/find-repos" className="transition-colors hover:text-foreground/80 text-foreground/60">Find Repos</Link>
          </nav>
        </div>
        
        <div className="flex items-center space-x-2">
          <Link href="https://github.com/devbh04/opensourcenav.git" target="_blank" rel="noreferrer">
            <Button variant="ghost" size="icon" className="w-9 px-0">
              <GitFork className="h-4 w-4" />
              <span className="sr-only">GitHub</span>
            </Button>
          </Link>
          <Button
            variant="ghost"
            size="icon"
            className="w-9 px-0"
            onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
          >
            <Sun className="h-4 w-4 rotate-0 scale-100 transition-all dark:-rotate-90 dark:scale-0" />
            <Moon className="absolute h-4 w-4 rotate-90 scale-0 transition-all dark:rotate-0 dark:scale-100" />
            <span className="sr-only">Toggle theme</span>
          </Button>

          {/* Mobile Menu Toggle */}
          <Button
            variant="ghost"
            size="icon"
            className="w-9 px-0 md:hidden"
            onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
          >
            <svg strokeWidth="1.5" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" className="h-5 w-5">
              <path d="M3 5H11" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"></path>
              <path d="M3 12H16" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"></path>
              <path d="M3 19H21" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"></path>
            </svg>
            <span className="sr-only">Toggle mobile menu</span>
          </Button>
        </div>
      </div>

      {/* Mobile Menu Dropdown */}
      {isMobileMenuOpen && (
        <div className="md:hidden border-b bg-background px-4 py-4 space-y-4">
          <nav className="flex flex-col space-y-3 text-sm font-medium">
            <Link href="/" onClick={() => setIsMobileMenuOpen(false)} className="transition-colors hover:text-foreground/80 text-foreground">Home</Link>
            <Link href="/generate" onClick={() => setIsMobileMenuOpen(false)} className="transition-colors hover:text-foreground/80 text-foreground/60">Generate</Link>
            <Link href="/find-repos" onClick={() => setIsMobileMenuOpen(false)} className="transition-colors hover:text-foreground/80 text-foreground/60">Find Repos</Link>
          </nav>
        </div>
      )}
    </header>
  )
}
