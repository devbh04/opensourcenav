"use client"

import * as React from "react"
import { useState, useMemo } from "react"
import { ChevronRight, ChevronDown, Minus } from "lucide-react"
import { cn } from "@/lib/utils"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"

export type FileNode = {
  name: string
  path: string
  type: "file" | "dir"
  size?: number
  children?: FileNode[]
}

type FileExplorerProps = {
  tree: FileNode[]
  selectedFiles: Set<string>
  allFilePaths: string[]
  onSelectFile: (path: string, checked: boolean) => void
  onSelectAll: () => void
  onClearAll: () => void
  onSelectFolder: (paths: string[], allSelected: boolean) => void
}

// ── File Icon System ───────────────────────────────────────────────────────
type IconDef = { bg: string; text: string; label: string }

const EXT_ICONS: Record<string, IconDef> = {
  // Languages
  py:    { bg: "bg-blue-500",    text: "text-white", label: "Py" },
  js:    { bg: "bg-yellow-400",  text: "text-black", label: "JS" },
  ts:    { bg: "bg-blue-600",    text: "text-white", label: "TS" },
  jsx:   { bg: "bg-cyan-400",    text: "text-black", label: "JX" },
  tsx:   { bg: "bg-cyan-600",    text: "text-white", label: "TX" },
  go:    { bg: "bg-teal-500",    text: "text-white", label: "Go" },
  rs:    { bg: "bg-orange-600",  text: "text-white", label: "Rs" },
  java:  { bg: "bg-red-600",     text: "text-white", label: "Ja" },
  cpp:   { bg: "bg-purple-600",  text: "text-white", label: "C+" },
  c:     { bg: "bg-purple-500",  text: "text-white", label: "C" },
  h:     { bg: "bg-purple-400",  text: "text-white", label: "H" },
  cs:    { bg: "bg-indigo-600",  text: "text-white", label: "C#" },
  php:   { bg: "bg-violet-600",  text: "text-white", label: "Ph" },
  rb:    { bg: "bg-red-500",     text: "text-white", label: "Rb" },
  swift: { bg: "bg-orange-500",  text: "text-white", label: "Sw" },
  kt:    { bg: "bg-purple-700",  text: "text-white", label: "Kt" },
  scala: { bg: "bg-red-700",     text: "text-white", label: "Sc" },
  // Data / Config
  json:  { bg: "bg-amber-500",   text: "text-white", label: "{}" },
  yaml:  { bg: "bg-pink-500",    text: "text-white", label: "YM" },
  yml:   { bg: "bg-pink-500",    text: "text-white", label: "YM" },
  toml:  { bg: "bg-rose-500",    text: "text-white", label: "TM" },
  xml:   { bg: "bg-orange-400",  text: "text-white", label: "XM" },
  env:   { bg: "bg-green-700",   text: "text-white", label: "En" },
  // Web
  html:  { bg: "bg-orange-500",  text: "text-white", label: "HT" },
  css:   { bg: "bg-blue-400",    text: "text-white", label: "CS" },
  scss:  { bg: "bg-pink-600",    text: "text-white", label: "SC" },
  svg:   { bg: "bg-yellow-500",  text: "text-black", label: "SV" },
  // Docs
  md:    { bg: "bg-gray-600",    text: "text-white", label: "Md" },
  txt:   { bg: "bg-gray-400",    text: "text-white", label: "Tx" },
  rst:   { bg: "bg-gray-500",    text: "text-white", label: "Rt" },
  // Shell
  sh:    { bg: "bg-green-600",   text: "text-white", label: "Sh" },
  bash:  { bg: "bg-green-600",   text: "text-white", label: "Sh" },
  zsh:   { bg: "bg-green-500",   text: "text-white", label: "Sh" },
  // Database
  sql:   { bg: "bg-sky-600",     text: "text-white", label: "Sq" },
  // Containers / Build
  dockerfile: { bg: "bg-sky-500",  text: "text-white", label: "Dk" },
  makefile:   { bg: "bg-red-400",  text: "text-white", label: "Mk" },
  // Lock / Package
  lock:  { bg: "bg-gray-400",    text: "text-white", label: "Lk" },
}

const BASE_ICONS: Record<string, IconDef> = {
  dockerfile: EXT_ICONS.dockerfile,
  makefile:   EXT_ICONS.makefile,
  ".gitignore": { bg: "bg-orange-400", text: "text-white", label: "Gi" },
  ".env":       EXT_ICONS.env,
}

const DEFAULT_ICON: IconDef = { bg: "bg-slate-400", text: "text-white", label: "F" }

function FileIcon({ name }: { name: string }) {
  const lower = name.toLowerCase()
  const ext = lower.split(".").pop() || ""
  const icon = BASE_ICONS[lower] || EXT_ICONS[ext] || DEFAULT_ICON

  return (
    <span
      className={cn(
        "inline-flex items-center justify-center rounded-sm font-bold shrink-0",
        "w-[18px] h-[14px] text-[7px] leading-none tracking-tight",
        icon.bg, icon.text
      )}
      title={name}
    >
      {icon.label}
    </span>
  )
}

// ── Checkbox ────────────────────────────────────────────────────────────────
function Checkbox({ checked, indeterminate, onClick }: {
  checked: boolean
  indeterminate?: boolean
  onClick: (e: React.MouseEvent) => void
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        "w-3.5 h-3.5 rounded-sm border flex items-center justify-center shrink-0 transition-colors",
        checked
          ? "bg-primary border-primary"
          : indeterminate
          ? "bg-primary/30 border-primary"
          : "border-muted-foreground/40 hover:border-muted-foreground"
      )}
      aria-checked={indeterminate ? "mixed" : checked}
    >
      {checked && (
        <svg viewBox="0 0 10 8" className="w-2 h-2 fill-primary-foreground">
          <path d="M1 3.5L4 6.5L9 1" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" fill="none" />
        </svg>
      )}
      {indeterminate && !checked && (
        <div className="w-2 h-0.5 bg-primary rounded-full" />
      )}
    </button>
  )
}

// ── Get all file paths in a subtree ─────────────────────────────────────────
// Filters out nodes with undefined paths (safety net for older backend responses)
function getFilePaths(node: FileNode): string[] {
  if (node.type === "file") return node.path ? [node.path] : []
  return (node.children || []).flatMap(getFilePaths)
}

// ── File node ────────────────────────────────────────────────────────────────
function FileRow({
  node, depth, selectedFiles, onSelectFile, query
}: {
  node: FileNode
  depth: number
  selectedFiles: Set<string>
  onSelectFile: (path: string, checked: boolean) => void
  query: string
}) {
  const isSelected = selectedFiles.has(node.path)
  const matches = !query || node.name.toLowerCase().includes(query.toLowerCase())
  if (!matches) return null

  return (
    <div
      className={cn(
        "flex items-center gap-2 h-7 rounded-sm cursor-pointer select-none text-xs transition-colors group",
        "hover:bg-muted/50",
        isSelected ? "bg-primary/8 text-foreground" : "text-foreground/75"
      )}
      style={{ paddingLeft: `${depth * 16 + 8}px`, paddingRight: "8px" }}
      onClick={() => onSelectFile(node.path, !isSelected)}
    >
      <Checkbox
        checked={isSelected}
        onClick={(e) => { e.stopPropagation(); onSelectFile(node.path, !isSelected) }}
      />
      <FileIcon name={node.name} />
      <span className="truncate min-w-0 flex-1">{node.name}</span>
      {node.size && (
        <span className="text-[9px] text-muted-foreground/50 shrink-0 ml-auto">
          {node.size > 1024 ? `${(node.size / 1024).toFixed(0)}k` : `${node.size}b`}
        </span>
      )}
    </div>
  )
}

// ── Folder node ──────────────────────────────────────────────────────────────
function FolderRow({
  node, depth, selectedFiles, onSelectFile, onSelectFolder, query
}: {
  node: FileNode
  depth: number
  selectedFiles: Set<string>
  onSelectFile: (path: string, checked: boolean) => void
  onSelectFolder: (paths: string[], allSelected: boolean) => void
  query: string
}) {
  const [isOpen, setIsOpen] = useState(depth < 2)
  const childPaths = useMemo(() => getFilePaths(node), [node])

  const selectedCount = childPaths.filter(p => selectedFiles.has(p)).length
  const allSelected = selectedCount === childPaths.length && childPaths.length > 0
  const someSelected = selectedCount > 0 && !allSelected

  // Show folder if it matches query or any child matches
  const hasMatch = useMemo(() => {
    if (!query) return true
    if (node.name.toLowerCase().includes(query.toLowerCase())) return true
    return childPaths.some(p => p && p.toLowerCase().includes(query.toLowerCase()))
  }, [query, node, childPaths])

  if (!hasMatch) return null

  return (
    <div>
      <div
        className="flex items-center gap-2 h-7 rounded-sm cursor-pointer select-none text-xs hover:bg-muted/50 group"
        style={{ paddingLeft: `${depth * 16 + 8}px`, paddingRight: "8px" }}
      >
        <Checkbox
          checked={allSelected}
          indeterminate={someSelected}
          onClick={(e) => {
            e.stopPropagation()
            onSelectFolder(childPaths, allSelected)
          }}
        />
        <button
          type="button"
          className="flex items-center gap-1.5 min-w-0 flex-1 text-left"
          onClick={() => setIsOpen(!isOpen)}
        >
          {isOpen
            ? <ChevronDown className="h-3 w-3 shrink-0 text-muted-foreground" />
            : <ChevronRight className="h-3 w-3 shrink-0 text-muted-foreground" />
          }
          <svg viewBox="0 0 16 16" className="w-3.5 h-3.5 shrink-0 text-yellow-400 fill-current">
            {isOpen
              ? <path d="M1.75 2.5a.25.25 0 0 0-.25.25v10.5c0 .138.112.25.25.25h12.5a.25.25 0 0 0 .25-.25V5.5a.25.25 0 0 0-.25-.25H7.414l-1.06-1.06A.25.25 0 0 0 6.18 4H1.75a.25.25 0 0 0-.25.25V4Z"/>
              : <path d="M.513 1.513A1.75 1.75 0 0 1 1.75 1h3.5c.55 0 1.07.26 1.4.7l.9 1.2h6.7A1.75 1.75 0 0 1 16 4.75v7.5A1.75 1.75 0 0 1 14.25 14H1.75A1.75 1.75 0 0 1 0 12.25V3a1.75 1.75 0 0 1 .513-1.237Z"/>
            }
          </svg>
          <span className="font-medium truncate">{node.name}</span>
          {selectedCount > 0 && (
            <Badge variant="secondary" className="text-[9px] px-1 py-0 h-3.5 ml-1 shrink-0 tabular-nums">
              {selectedCount}/{childPaths.length}
            </Badge>
          )}
        </button>
      </div>

      {isOpen && (
        <div>
          {(node.children || []).map((child, i) =>
            child.type === "file" ? (
              <FileRow
                key={i}
                node={child}
                depth={depth + 1}
                selectedFiles={selectedFiles}
                onSelectFile={onSelectFile}
                query={query}
              />
            ) : (
              <FolderRow
                key={i}
                node={child}
                depth={depth + 1}
                selectedFiles={selectedFiles}
                onSelectFile={onSelectFile}
                onSelectFolder={onSelectFolder}
                query={query}
              />
            )
          )}
        </div>
      )}
    </div>
  )
}

// ── Main Component ────────────────────────────────────────────────────────────
export function FileExplorer({
  tree, selectedFiles, allFilePaths,
  onSelectFile, onSelectAll, onClearAll, onSelectFolder
}: FileExplorerProps) {
  const [query, setQuery] = useState("")
  const allSelected = allFilePaths.length > 0 && allFilePaths.every(p => selectedFiles.has(p))

  return (
    <div className="flex flex-col h-full min-h-0">
      {/* Toolbar */}
      <div className="p-2.5 border-b space-y-2 shrink-0">
        <div className="relative">
          <svg viewBox="0 0 24 24" className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground fill-none stroke-current" strokeWidth="2">
            <circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/>
          </svg>
          <Input
            value={query}
            onChange={e => setQuery(e.target.value)}
            placeholder="Filter files..."
            className="h-7 pl-7 text-xs"
          />
        </div>
        <div className="flex items-center justify-between text-xs text-muted-foreground">
          <span>
            <span className="font-semibold text-foreground">{selectedFiles.size}</span> / {allFilePaths.length} selected
          </span>
          <div className="flex gap-3">
            <button
              type="button"
              onClick={onSelectAll}
              disabled={allSelected}
              className="hover:text-primary transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
            >
              Select all
            </button>
            <span className="opacity-30">·</span>
            <button
              type="button"
              onClick={onClearAll}
              disabled={selectedFiles.size === 0}
              className="hover:text-destructive transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
            >
              Clear
            </button>
          </div>
        </div>
      </div>

      {/* Tree */}
      <div className="flex-1 overflow-y-auto py-1 min-h-0">
        {tree.map((node, i) =>
          node.type === "file" ? (
            <FileRow
              key={i}
              node={node}
              depth={0}
              selectedFiles={selectedFiles}
              onSelectFile={onSelectFile}
              query={query}
            />
          ) : (
            <FolderRow
              key={i}
              node={node}
              depth={0}
              selectedFiles={selectedFiles}
              onSelectFile={onSelectFile}
              onSelectFolder={onSelectFolder}
              query={query}
            />
          )
        )}
      </div>
    </div>
  )
}
