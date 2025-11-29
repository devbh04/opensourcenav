"use client";

import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { MermaidDiagram } from "./mermaid-diagram";
import { CodeBlock } from "./code-block";

interface MarkdownRendererProps {
  content: string;
  isMobile?: boolean;
}

export const MarkdownRenderer = ({ content, isMobile = false }: MarkdownRendererProps) => {
  return (
    <div className="prose prose-slate prose-invert max-w-none prose-headings:text-white prose-p:text-slate-300 prose-strong:text-slate-200 prose-code:text-slate-200 prose-code:bg-slate-800 prose-pre:bg-slate-900 prose-pre:border prose-pre:border-slate-700">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          h1: ({ children }) => (
            <h1 className={`font-semibold text-white ${
              isMobile 
                ? "text-lg mt-4 mb-2" 
                : "text-lg sm:text-xl mt-4 lg:mt-6 mb-2 lg:mb-3"
            }`}>
              {children}
            </h1>
          ),
          h2: ({ children }) => (
            <h2 className={`font-semibold text-white ${
              isMobile 
                ? "text-base mt-3 mb-2" 
                : "text-base sm:text-lg mt-3 lg:mt-5 mb-2"
            }`}>
              {children}
            </h2>
          ),
          h3: ({ children }) => (
            <h3 className={`font-semibold text-slate-200 ${
              isMobile 
                ? "text-sm mt-2 mb-2" 
                : "text-sm sm:text-base mt-2 lg:mt-4 mb-2"
            }`}>
              {children}
            </h3>
          ),
          p: ({ children }) => (
            <p className={`text-slate-300 leading-relaxed ${
              isMobile 
                ? "text-sm mb-3" 
                : "text-sm sm:text-base mb-3 lg:mb-4"
            }`}>
              {children}
            </p>
          ),
          code: ({ className, children, ...props }) => {
            const match = /language-(\w+)/.exec(className || "");
            const language = match ? match[1] : "";

            // Handle Mermaid diagrams
            if (language === "mermaid") {
              return <MermaidDiagram chart={String(children)} />;
            }

            // If it's a code block (not inline code)
            if (className && language) {
              return (
                <CodeBlock 
                  language={language} 
                  isMobile={isMobile}
                >
                  {String(children)}
                </CodeBlock>
              );
            }

            // Inline code
            return (
              <code
                className={`bg-slate-800 text-slate-200 py-0.5 rounded font-mono ${
                  isMobile 
                    ? "px-1 text-xs" 
                    : "px-1 sm:px-1.5 text-xs sm:text-sm"
                }`}
                {...props}
              >
                {children}
              </code>
            );
          },
          pre: ({ children, ...props }) => {
            return (
              <pre
                className={`bg-black border border-slate-700 rounded-lg overflow-x-auto ${
                  isMobile 
                    ? "p-2 text-xs" 
                    : "p-2 sm:p-4 text-xs sm:text-sm"
                }`}
                {...props}
              >
                {children}
              </pre>
            );
          },
          ul: ({ children }) => (
            <ul className={`list-disc list-inside text-slate-300 space-y-1 ${
              isMobile 
                ? "mb-3 text-sm" 
                : "mb-3 lg:mb-4 text-sm sm:text-base"
            }`}>
              {children}
            </ul>
          ),
          ol: ({ children }) => (
            <ol className={`list-decimal list-inside text-slate-300 space-y-1 ${
              isMobile 
                ? "mb-3 text-sm" 
                : "mb-3 lg:mb-4 text-sm sm:text-base"
            }`}>
              {children}
            </ol>
          ),
          li: ({ children }) => (
            <li className={`text-slate-300 ${
              isMobile ? "text-sm" : "text-sm sm:text-base"
            }`}>
              {children}
            </li>
          ),
        }}
      >
        {content.slice(12, -3)}
      </ReactMarkdown>
    </div>
  );
};
