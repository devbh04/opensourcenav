"use client"

import * as React from "react"
import { useState, useRef, useEffect } from "react"
import { MessageSquare, X, Send, Bot, User, Loader2, Maximize2, Minimize2 } from "lucide-react"

import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Card } from "@/components/ui/card"
import { MarkdownRenderer } from "@/components/MarkdownRenderer"

type Message = {
  id: string
  role: "user" | "assistant"
  content: string
  sources?: any[]
}

export function Chatbot({ repoName }: { repoName: string }) {
  const [isOpen, setIsOpen] = useState(false)
  const [isExpanded, setIsExpanded] = useState(false)
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "1",
      role: "assistant",
      content: `Hi! I'm the AI assistant for **${repoName}**. Ask me anything about the codebase, architecture, or how to use it.`,
    }
  ])
  const [input, setInput] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const [sessionId, setSessionId] = useState("")
  const scrollRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollIntoView({ behavior: "smooth" })
    }
  }, [messages])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || isLoading) return

    const userMessage: Message = { id: Date.now().toString(), role: "user", content: input }
    setMessages(prev => [...prev, userMessage])
    setInput("")
    setIsLoading(true)

    try {
      const guestId = localStorage.getItem("guest_id") || "guest_unknown"
      const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const res = await fetch(`${API_URL}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          question: userMessage.content,
          repo_name: repoName,
          user_id: guestId,
          session_id: sessionId
        })
      })

      const data = await res.json()
      if (data.session_id && !sessionId) {
        setSessionId(data.session_id)
      }

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: data.answer || "Sorry, I couldn't generate an answer.",
        sources: data.sources
      }

      setMessages(prev => [...prev, assistantMessage])
    } catch (err) {
      setMessages(prev => [...prev, {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: "Network error connecting to the chat service."
      }])
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <>
      <Button
        onClick={() => setIsOpen(true)}
        className={cn(
          "fixed bottom-6 right-6 h-14 w-14 rounded-full shadow-lg transition-transform hover:scale-105",
          isOpen && "scale-0 opacity-0"
        )}
      >
        <MessageSquare className="h-6 w-6" />
      </Button>

      {/* Backdrop for expanded mode */}
      {isOpen && isExpanded && (
        <div
          className="fixed inset-0 z-40 bg-background/80 backdrop-blur-sm transition-opacity"
          onClick={() => setIsExpanded(false)}
        />
      )}

      <Card
        className={cn(
          "fixed z-50 flex flex-col shadow-2xl transition-all duration-300 ease-in-out border-border/60 bg-background/95 backdrop-blur supports-backdrop-filter:bg-background/80",
          isOpen ? "scale-100 opacity-100" : "scale-95 opacity-0 pointer-events-none",
          !isOpen && !isExpanded ? "translate-y-8" : "",
          isExpanded
            ? "left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-[95vw] sm:w-[90vw] h-[90vh] sm:h-[85vh] max-w-5xl rounded-xl"
            : "bottom-4 right-4 left-4 sm:left-auto sm:bottom-6 sm:right-6 h-[500px] sm:h-[600px] sm:w-[400px] rounded-xl"
        )}
      >
        <div className="flex items-center justify-between border-b px-4 py-3 bg-muted/30">
          <div className="flex items-center gap-2">
            <div className="p-1.5 bg-primary/10 rounded-md">
              <Bot className="h-4 w-4 text-primary" />
            </div>
            <div>
              <h3 className="font-semibold text-sm">EasyGit Chat</h3>
              <p className="text-xs text-muted-foreground">Ask about {repoName}</p>
            </div>
          </div>
          <div className="flex items-center gap-1">
            <Button variant="ghost" size="icon" className="h-8 w-8" onClick={() => setIsExpanded(!isExpanded)}>
              {isExpanded ? <Minimize2 className="h-4 w-4" /> : <Maximize2 className="h-4 w-4" />}
            </Button>
            <Button variant="ghost" size="icon" className="h-8 w-8" onClick={() => { setIsOpen(false); setIsExpanded(false); }}>
              <X className="h-4 w-4" />
            </Button>
          </div>
        </div>

        <ScrollArea className="flex-1 p-4 w-full overflow-x-hidden">
          <div className="flex flex-col gap-4 pb-4 w-full max-w-full overflow-x-hidden">
            {messages.map((msg) => (
              <div
                key={msg.id}
                className={cn(
                  "flex gap-3 w-full",
                  isExpanded ? "max-w-[70%]" : "max-w-[85%]",
                  msg.role === "user" ? "self-end flex-row-reverse" : "self-start"
                )}
              >
                <div className={cn(
                  "h-8 w-8 rounded-full flex items-center justify-center shrink-0",
                  msg.role === "user" ? "bg-primary text-primary-foreground" : "bg-secondary text-secondary-foreground"
                )}>
                  {msg.role === "user" ? <User className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
                </div>
                <div className={cn(
                  "rounded-2xl px-4 py-2.5 text-sm min-w-0 overflow-hidden shadow-sm",
                  msg.role === "user"
                    ? "bg-primary text-primary-foreground rounded-tr-sm"
                    : "bg-muted rounded-tl-sm border"
                )}>
                  <div className="prose prose-sm dark:prose-invert max-w-full min-w-0 w-full break-words prose-pre:max-w-full prose-pre:overflow-x-auto">
                    {msg.role === "user" ? (
                      <p className="whitespace-pre-wrap">{msg.content}</p>
                    ) : (
                      <MarkdownRenderer content={msg.content} />
                    )}
                  </div>
                  {msg.sources && msg.sources.length > 0 && (
                    <div className="mt-3 pt-2 border-t border-border/50">
                      <p className="text-[10px] uppercase font-semibold opacity-70 mb-1.5">Sources</p>
                      <div className="flex flex-wrap gap-1.5">
                        {msg.sources.slice(0, 3).map((s, i) => (
                          <span key={i} className="text-[10px] bg-background/50 px-1.5 py-0.5 rounded border truncate max-w-[150px]" title={s.file_path}>
                            {s.file_path.split('/').pop()}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            ))}
            {isLoading && (
              <div className={cn(
                "flex gap-3 self-start",
                isExpanded ? "max-w-[70%]" : "max-w-[85%]"
              )}>
                <div className="h-8 w-8 rounded-full bg-secondary flex items-center justify-center shrink-0">
                  <Bot className="h-4 w-4" />
                </div>
                <div className="rounded-2xl rounded-tl-sm bg-muted px-4 py-3 flex items-center gap-2 border">
                  <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
                  <span className="text-xs text-muted-foreground">Thinking...</span>
                </div>
              </div>
            )}
            <div ref={scrollRef} />
          </div>
        </ScrollArea>

        <div className="p-4 bg-background border-t shrink-0">
          <form onSubmit={handleSubmit} className="flex gap-2">
            <Input
              placeholder="Ask anything..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              className="flex-1 focus-visible:ring-1 focus-visible:ring-offset-0 bg-muted/50 border-transparent focus:border-border"
              disabled={isLoading}
            />
            <Button type="submit" size="icon" disabled={!input.trim() || isLoading} className="shrink-0 transition-all">
              <Send className="h-4 w-4" />
            </Button>
          </form>
        </div>
      </Card>
    </>
  )
}
