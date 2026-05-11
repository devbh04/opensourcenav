"use client"

import * as React from "react"
import Link from "next/link"
import { useTheme } from "next-themes"
import { BookOpen, Moon, Sun, GitFork } from "lucide-react"

import { Button } from "@/components/ui/button"

export function Navbar() {
  const { setTheme, theme } = useTheme()

  return (
    <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-backdrop-filter:bg-background/60">
      <div className="container flex h-14 items-center px-4 md:px-8 max-w-7xl mx-auto">
        <div className="mr-4 hidden md:flex">
          <Link href="/" className="mr-6 flex items-center space-x-2">
            <span className="hidden font-bold sm:inline-block">
              EasyGit
            </span>
          </Link>
          <nav className="flex items-center space-x-6 text-sm font-medium">
            <Link
              href="/"
              className="transition-colors hover:text-foreground/80 text-foreground"
            >
              Home
            </Link>
            <Link
              href="/generate"
              className="transition-colors hover:text-foreground/80 text-foreground/60"
            >
              Generate
            </Link>
            <Link
              href="/find-repos"
              className="transition-colors hover:text-foreground/80 text-foreground/60"
            >
              Find Repos
            </Link>
          </nav>
        </div>
        <div className="flex flex-1 items-center justify-between space-x-2 md:justify-end">
          <div className="w-full flex-1 md:w-auto md:flex-none">
            {/* Search can go here later */}
          </div>
          <nav className="flex items-center space-x-2">
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
          </nav>
        </div>
      </div>
    </header>
  )
}
