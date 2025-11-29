"use client";

import useTutorialStore from "@/store/tutorialstore";
import { useResolutionStore } from "@/store/resolution-store";
import { useState, useEffect, useRef } from "react";
import { Send, MessageCircle, X, Bot, User, Trash2, ArrowUp } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import ReactMarkdown from 'react-markdown';
import remarkGfm from "remark-gfm";
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism';

interface ChatMessage {
  id: string;
  text: string;
  isUser: boolean;
  timestamp: Date;
  isLoading?: boolean;
}

export const ChatQABox = ({ image }: { image: string }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [isHydrated, setIsHydrated] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputText, setInputText] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const tutorialStore = useTutorialStore();
  const resolutionStore = useResolutionStore();

  useEffect(() => {
    setIsHydrated(true);
  }, []);

  useEffect(() => {
    // Auto scroll to bottom when new messages are added
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Show if tutorial has been generated successfully OR if there's resolution content
  const shouldShowForTutorial = isHydrated && 
    tutorialStore.tutorialResponse && 
    tutorialStore.tutorialResponse.success && 
    tutorialStore.tutorialResponse.data;

  const shouldShowForResolution = isHydrated && 
    (resolutionStore.response || resolutionStore.comprehensiveResponse);

  const shouldShow = shouldShowForTutorial || shouldShowForResolution;

  // Determine the context - tutorial or resolution
  const isResolutionContext = shouldShowForResolution && !shouldShowForTutorial;

  if (!shouldShow) {
    return null;
  }

  const sendMessage = async () => {
    if (!inputText.trim() || isLoading) return;

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      text: inputText.trim(),
      isUser: true,
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInputText("");
    setIsLoading(true);

    // Add loading message
    const loadingMessage: ChatMessage = {
      id: (Date.now() + 1).toString(),
      text: "Thinking...",
      isUser: false,
      timestamp: new Date(),
      isLoading: true,
    };
    setMessages(prev => [...prev, loadingMessage]);

    try {
      // Use environment variable or fallback to a default endpoint
      const apiEndpoint = 'http://localhost:8000/chat';
      
      const response = await fetch(apiEndpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          question: userMessage.text
        }),
      });

      const data = await response.json();

      // Remove loading message and add bot response
      setMessages(prev => {
        const filtered = prev.filter(msg => !msg.isLoading);
        const botMessage: ChatMessage = {
          id: (Date.now() + 2).toString(),
          text: data.answer || data.response || "Sorry, I couldn't process your request.",
          isUser: false,
          timestamp: new Date(),
        };
        return [...filtered, botMessage];
      });
    } catch (error) {
      console.error("Chat API error:", error);
      
      // Remove loading message and add error response
      setMessages(prev => {
        const filtered = prev.filter(msg => !msg.isLoading);
        const errorMessage: ChatMessage = {
          id: (Date.now() + 3).toString(),
          text: "Sorry, I'm having trouble connecting. Please try again later.",
          isUser: false,
          timestamp: new Date(),
        };
        return [...filtered, errorMessage];
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const clearChat = () => {
    setMessages([]);
  };

  return (
    <>
      {/* Chat Toggle Button */}
      <div className="fixed -bg-conic-270 -bottom-14 -right-4 -rotate-25 z-50">
        <button
          onClick={() => setIsOpen(!isOpen)}
          className="hover:shadow-xl transition-all duration-300 hover:scale-105"
        >
          <img src={image} alt="gekko" className="w-28 h-28 md:w-40 md:h-40"/>
        </button>
      </div>

      {/* Overlay Backdrop */}
      {isOpen && (
        <div 
          className="fixed inset-0 bg-black/20 z-40"
          onClick={() => setIsOpen(false)}
        />
      )}

      {/* Chat Sidebar Overlay */}
      <div
        className={`fixed top-0 right-0 h-full w-full sm:w-96 bg-slate-900 border-l border-slate-700 shadow-2xl transform transition-transform duration-300 ease-in-out z-50 flex flex-col ${
          isOpen ? 'translate-x-0' : 'translate-x-full'
        }`}
      >
        {/* Header */}
        <div className="flex justify-between items-center p-3 sm:p-4 bg-slate-900 border-b border-neutral-600 flex-shrink-0">
          <div className="flex items-center space-x-2">
            <Bot className="w-4 h-4 sm:w-5 sm:h-5 text-blue-400" />
            <h3 className="font-semibold text-white text-sm sm:text-base">
              {isResolutionContext ? 'Resolution Assistant' : 'Tutorial Assistant'}
            </h3>
          </div>
          <div className="flex items-center space-x-1 sm:space-x-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={clearChat}
              className="text-slate-400 hover:text-white h-8 px-2"
            >
              <Trash2 className="w-3 h-3 sm:w-4 sm:h-4" />
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setIsOpen(false)}
              className="text-slate-400 hover:text-white h-8 px-2"
            >
              <X className="w-3 h-3 sm:w-4 sm:h-4" />
            </Button>
          </div>
        </div>

        {/* Messages */}
        <div className="flex-1 bg-black/50 overflow-y-auto p-3 sm:p-4 space-y-2 sm:space-y-3 h-[calc(100vh-140px)]">
          {messages.length === 0 && (
            <div className="flex items-center justify-center h-full pb-32">
              <div className="text-center text-slate-400 text-xs sm:text-sm py-6 sm:py-8">
                <Bot className="w-6 h-6 sm:w-8 sm:h-8 mx-auto mb-2 text-slate-500" />
                <p>Start a conversation...</p>
                <p className="text-xs mt-1">
                  {isResolutionContext 
                    ? 'Ask me anything about this issue resolution!' 
                    : 'Ask me anything about this tutorial!'
                  }
                </p>
              </div>
            </div>
          )}
          
          {messages.map((message) => (
            <div key={message.id} className="w-full mb-3 sm:mb-4">
              {message.isUser ? (
                // User Message
                <div className="flex justify-end">
                  <div className="max-w-[85%] sm:max-w-[80%]">
                    <div className="bg-slate-600 text-white rounded-2xl px-3 sm:px-4 py-2 sm:py-3 shadow-sm">
                      <div className="prose prose-sm max-w-none prose-invert prose-headings:text-white prose-p:text-white prose-strong:text-white prose-code:text-blue-100 prose-code:bg-blue-800/30 prose-pre:bg-blue-900/40 prose-pre:border prose-pre:border-blue-700/50">
                        <ReactMarkdown
                          remarkPlugins={[remarkGfm]}
                          components={{
                            h1: ({ children }) => (
                              <h1 className="font-semibold text-white text-sm sm:text-base mt-2 mb-1">
                                {children}
                              </h1>
                            ),
                            h2: ({ children }) => (
                              <h2 className="font-semibold text-white text-xs sm:text-sm mt-2 mb-1">
                                {children}
                              </h2>
                            ),
                            h3: ({ children }) => (
                              <h3 className="font-semibold text-blue-100 text-xs sm:text-sm mt-1 mb-1">
                                {children}
                              </h3>
                            ),
                            p: ({ children }) => (
                              <p className="text-white leading-relaxed text-xs sm:text-sm mb-2">
                                {children}
                              </p>
                            ),
                            code: ({ className, children, ...props }) => {
                              const match = /language-(\w+)/.exec(className || "");
                              const language = match ? match[1] : "";

                              // If it's a code block (not inline code)
                              if (className && language) {
                                return (
                                  <SyntaxHighlighter
                                    style={oneDark as any}
                                    language={language}
                                    PreTag="div"
                                    className="rounded-lg text-xs sm:text-sm my-2"
                                  >
                                    {String(children).replace(/\n$/, '')}
                                  </SyntaxHighlighter>
                                );
                              }

                              // Inline code
                              return (
                                <code
                                  className="bg-blue-800/30 text-blue-100 py-0.5 rounded font-mono px-1 text-xs sm:text-sm"
                                  {...props}
                                >
                                  {children}
                                </code>
                              );
                            },
                            pre: ({ children, ...props }) => (
                              <pre
                                className="bg-blue-900/40 border border-blue-700/50 rounded-lg overflow-x-auto p-2 text-xs sm:text-sm my-2"
                                {...props}
                              >
                                {children}
                              </pre>
                            ),
                            ul: ({ children }) => (
                              <ul className="list-disc list-inside text-white space-y-1 mb-2 text-xs sm:text-sm">
                                {children}
                              </ul>
                            ),
                            ol: ({ children }) => (
                              <ol className="list-decimal list-inside text-white space-y-1 mb-2 text-xs sm:text-sm">
                                {children}
                              </ol>
                            ),
                            li: ({ children }) => (
                              <li className="text-white text-xs sm:text-sm">
                                {children}
                              </li>
                            ),
                          }}
                        >
                          {message.text}
                        </ReactMarkdown>
                      </div>
                    </div>
                    <div className="flex justify-end mt-1">
                      <span className="text-xs text-slate-400">
                        {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </span>
                    </div>
                  </div>
                </div>
              ) : (
                // AI Message
                <div className="w-full">
                  <div className="w-full">
                    <div className="prose prose-sm max-w-none prose-invert prose-headings:text-slate-200 prose-p:text-slate-300 prose-strong:text-slate-200 prose-code:text-slate-200 prose-code:bg-slate-800 prose-pre:bg-slate-900 prose-pre:border prose-pre:border-slate-700">
                      {message.isLoading ? (
                        <div className="flex items-center space-x-2 p-3">
                          <Bot className="w-4 h-4 text-blue-400 flex-shrink-0" />
                          <div className="flex items-center space-x-1">
                            <div className="animate-pulse text-xs sm:text-sm">Thinking</div>
                            <div className="flex space-x-1">
                              <div className="w-1 h-1 bg-blue-400 rounded-full animate-bounce"></div>
                              <div className="w-1 h-1 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                              <div className="w-1 h-1 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                            </div>
                          </div>
                        </div>
                      ) : (
                        <ReactMarkdown
                          remarkPlugins={[remarkGfm]}
                          components={{
                            h1: ({ children }) => (
                              <h1 className="font-semibold text-slate-200 text-sm sm:text-base mt-3 mb-2">
                                {children}
                              </h1>
                            ),
                            h2: ({ children }) => (
                              <h2 className="font-semibold text-slate-200 text-xs sm:text-sm mt-3 mb-2">
                                {children}
                              </h2>
                            ),
                            h3: ({ children }) => (
                              <h3 className="font-semibold text-slate-300 text-xs sm:text-sm mt-2 mb-2">
                                {children}
                              </h3>
                            ),
                            p: ({ children }) => (
                              <p className="text-slate-300 leading-relaxed text-xs sm:text-sm mb-3">
                                {children}
                              </p>
                            ),
                            code: ({ className, children, ...props }) => {
                              const match = /language-(\w+)/.exec(className || "");
                              const language = match ? match[1] : "";

                              // If it's a code block (not inline code)
                              if (className && language) {
                                return (
                                  <SyntaxHighlighter
                                    style={oneDark as any}
                                    language={language}
                                    PreTag="div"
                                    className="rounded-lg text-xs sm:text-sm my-3"
                                  >
                                    {String(children).replace(/\n$/, '')}
                                  </SyntaxHighlighter>
                                );
                              }

                              // Inline code
                              return (
                                <code
                                  className="bg-slate-800 text-slate-200 py-0.5 rounded font-mono px-1 text-xs sm:text-sm"
                                  {...props}
                                >
                                  {children}
                                </code>
                              );
                            },
                            pre: ({ children, ...props }) => (
                              <pre
                                className="bg-slate-900 border border-slate-700 rounded-lg overflow-x-auto p-2 sm:p-3 text-xs sm:text-sm my-3"
                                {...props}
                              >
                                {children}
                              </pre>
                            ),
                            ul: ({ children }) => (
                              <ul className="list-disc list-inside text-slate-300 space-y-1 mb-3 text-xs sm:text-sm">
                                {children}
                              </ul>
                            ),
                            ol: ({ children }) => (
                              <ol className="list-decimal list-inside text-slate-300 space-y-1 mb-3 text-xs sm:text-sm">
                                {children}
                              </ol>
                            ),
                            li: ({ children }) => (
                              <li className="text-slate-300 text-xs sm:text-sm">
                                {children}
                              </li>
                            ),
                            blockquote: ({ children }) => (
                              <blockquote className="border-l-4 border-blue-500 pl-4 italic text-slate-400 my-3">
                                {children}
                              </blockquote>
                            ),
                            strong: ({ children }) => (
                              <strong className="text-slate-200 font-semibold">
                                {children}
                              </strong>
                            ),
                            em: ({ children }) => (
                              <em className="text-slate-300 italic">
                                {children}
                              </em>
                            ),
                          }}
                        >
                          {message.text}
                        </ReactMarkdown>
                      )}
                    </div>
                    <div className="flex justify-between items-center mt-2">
                      <div className="flex items-center space-x-2">
                        <Bot className="w-3 h-3 sm:w-4 sm:h-4 text-blue-400" />
                        <span className="text-xs text-slate-300 font-medium">
                          {isResolutionContext ? 'Resolution Assistant' : 'Tutorial Assistant'}
                        </span>
                      </div>
                      <span className="text-xs text-slate-400">
                        {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </span>
                    </div>
                  </div>
                </div>
              )}
            </div>
          ))}
          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <div className="p-3 sm:p-4 border-t border-slate-700 bg-slate-950 flex-shrink-0">
          <div className="flex space-x-2 items-center">
            <Textarea
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder={isResolutionContext 
                ? "Ask about the issue resolution..." 
                : "Ask about the tutorial..."
              }
              className="flex-1 bg-slate-800 border rounded-l-lg border-slate-600 px-2 sm:px-3 py-2 text-white text-xs sm:text-sm resize-none focus:outline-none focus:ring-2 focus:ring-blue-500 h-10"
              rows={1}
              disabled={isLoading}
            />
            <Button
              onClick={sendMessage}
              disabled={!inputText.trim() || isLoading}
              className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed text-white p-2 rounded-full transition-colors h-10 w-10"
            >
              <ArrowUp className="w-3 h-3 sm:w-4 sm:h-4" />
            </Button>
          </div>
        </div>
      </div>
    </>
  );
};
