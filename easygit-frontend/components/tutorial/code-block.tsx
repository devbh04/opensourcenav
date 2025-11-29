"use client";

import { useState } from "react";
import { Check, Copy } from "lucide-react";
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism';

interface CodeBlockProps {
  language: string;
  children: string;
  isMobile?: boolean;
}

export const CodeBlock = ({ language, children, isMobile = false }: CodeBlockProps) => {
  const [copied, setCopied] = useState(false);
  const codeContent = String(children).replace(/\n$/, '');

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(codeContent);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  };

  return (
    <div className="relative my-4">
      <div className={`flex items-center justify-between bg-slate-800 border border-slate-700 rounded-t-lg ${
        isMobile ? 'px-4 py-2' : 'px-3 sm:px-4 py-2'
      }`}>
        <div className="flex items-center gap-2">
          <div className="bg-blue-600/20 text-blue-400 rounded px-2 py-1 text-xs font-medium uppercase">
            {language}
          </div>
        </div>
        <button
          onClick={handleCopy}
          className="flex items-center gap-1 px-2 py-1 text-xs text-slate-400 hover:text-white transition-colors rounded hover:bg-slate-700"
        >
          {copied ? (
            <>
              <Check className="h-3 w-3 text-green-500" />
              <span className="text-green-500">Copied!</span>
            </>
          ) : (
            <>
              <Copy className="h-3 w-3" />
              <span>Copy</span>
            </>
          )}
        </button>
      </div>
      <div className="bg-slate-900 border border-slate-700 border-t-0 rounded-b-lg overflow-hidden">
        <SyntaxHighlighter
          language={language}
          style={oneDark}
          customStyle={{
            margin: 0,
            padding: isMobile ? '12px' : '12px 16px',
            background: '#0f172a',
            fontSize: isMobile ? '12px' : (typeof window !== 'undefined' && window.innerWidth < 640 ? '12px' : '14px'),
            lineHeight: '1.5',
          }}
          codeTagProps={{
            style: {
              fontFamily: 'ui-monospace, SFMono-Regular, "SF Mono", Monaco, "Cascadia Code", "Roboto Mono", Menlo, monospace',
            }
          }}
        >
          {codeContent}
        </SyntaxHighlighter>
      </div>
    </div>
  );
};
