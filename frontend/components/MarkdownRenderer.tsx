"use client"

import * as React from "react"
import ReactMarkdown from "react-markdown"
import remarkGfm from "remark-gfm"
import rehypeHighlight from "rehype-highlight"
import { cn } from "@/lib/utils"

// Needs highlight.js styles
import "highlight.js/styles/github-dark.css"

import mermaid from "mermaid"

// Initialize mermaid with dark theme
mermaid.initialize({
  startOnLoad: false,
  theme: 'dark',
  securityLevel: 'loose',
  fontFamily: 'inherit',
})

import { TransformWrapper, TransformComponent } from "react-zoom-pan-pinch"
import { ZoomIn, ZoomOut, Maximize } from "lucide-react"
import { Button } from "@/components/ui/button"

const MermaidChart = ({ chart }: { chart: string }) => {
  const [svg, setSvg] = React.useState<string>('')
  const id = React.useId()

  React.useEffect(() => {
    const renderChart = async () => {
      try {
        const result = await mermaid.render(`mermaid-${id.replace(/:/g, '')}`, chart)
        setSvg(result.svg)
      } catch (e) {
        console.error("Mermaid rendering failed:", e)
        setSvg(`<div class="text-red-500 text-sm p-4 border border-red-900 rounded bg-red-950/20">Failed to render Mermaid chart</div>`)
      }
    }
    renderChart()
  }, [chart, id])

  if (!svg) return <div className="h-40 flex items-center justify-center text-muted-foreground">Rendering diagram...</div>

  return (
    <div className="relative my-8 border border-border rounded-lg bg-zinc-950 overflow-hidden group">
      <TransformWrapper
        initialScale={1}
        minScale={0.5}
        maxScale={4}
        centerOnInit={true}
        wheel={{ step: 0.1 }}
      >
        {({ zoomIn, zoomOut, resetTransform, ...rest }) => (
          <>
            <div className="absolute top-2 right-2 z-10 flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity bg-background/80 backdrop-blur-sm p-1 rounded-md border shadow-sm">
              <Button variant="ghost" size="icon" className="h-7 w-7" onClick={() => zoomIn()}>
                <ZoomIn className="h-4 w-4" />
              </Button>
              <Button variant="ghost" size="icon" className="h-7 w-7" onClick={() => zoomOut()}>
                <ZoomOut className="h-4 w-4" />
              </Button>
              <Button variant="ghost" size="icon" className="h-7 w-7" onClick={() => resetTransform()}>
                <Maximize className="h-4 w-4" />
              </Button>
            </div>
            <TransformComponent wrapperClass="!w-full !h-full min-h-[300px] cursor-grab active:cursor-grabbing">
              <div 
                className="flex items-center justify-center w-full h-full p-4" 
                dangerouslySetInnerHTML={{ __html: svg }} 
              />
            </TransformComponent>
          </>
        )}
      </TransformWrapper>
    </div>
  )
}

export function MarkdownRenderer({ content, className }: { content: string, className?: string }) {
  // Strip yaml frontmatter block if it exists
  const cleanContent = content.replace(/^---\n[\s\S]*?\n---\n/, '')

  return (
    <div className={cn("prose prose-neutral dark:prose-invert max-w-none w-full", className)}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        rehypePlugins={[rehypeHighlight]}
        components={{
          code({node, inline, className, children, ...props}: any) {
            const match = /language-(\w+)/.exec(className || '')
            const codeString = String(children).replace(/\n$/, '')
            
            if (!inline && match && match[1] === 'mermaid') {
              return <MermaidChart chart={codeString} />
            }
            
            return !inline && match ? (
              <div className="relative rounded-md overflow-hidden bg-zinc-950 border border-zinc-800 my-4">
                <div className="flex items-center justify-between px-4 py-1.5 bg-zinc-900 border-b border-zinc-800 text-xs text-zinc-400">
                  <span>{match[1]}</span>
                </div>
                <div className="p-4 overflow-x-auto text-sm">
                  <code className={className} {...props}>
                    {children}
                  </code>
                </div>
              </div>
            ) : (
              <code className={cn("bg-muted px-1.5 py-0.5 rounded-md font-mono text-sm break-words whitespace-pre-wrap break-all", className)} {...props}>
                {children}
              </code>
            )
          },
          table({children}) {
            return (
              <div className="overflow-x-auto my-6 border rounded-lg">
                <table className="w-full text-sm text-left m-0">{children}</table>
              </div>
            )
          },
          th({children}) {
            return <th className="bg-muted px-4 py-3 font-semibold text-foreground border-b">{children}</th>
          },
          td({children}) {
            return <td className="px-4 py-3 border-b border-border/50">{children}</td>
          },
          h1({children}) {
            return <h1 className="scroll-m-20 text-4xl font-extrabold tracking-tight lg:text-5xl mb-6">{children}</h1>
          },
          h2({children}) {
            return <h2 className="scroll-m-20 border-b pb-2 text-3xl font-semibold tracking-tight first:mt-0 mt-10 mb-4">{children}</h2>
          },
          h3({children}) {
            return <h3 className="scroll-m-20 text-2xl font-semibold tracking-tight mt-8 mb-4">{children}</h3>
          },
          a({href, children}) {
            return <a href={href} className="font-medium text-primary underline underline-offset-4 hover:text-primary/80">{children}</a>
          },
          blockquote({children}) {
            return <blockquote className="mt-6 border-l-2 border-primary pl-6 italic text-muted-foreground">{children}</blockquote>
          }
        }}
      >
        {cleanContent}
      </ReactMarkdown>
    </div>
  )
}
