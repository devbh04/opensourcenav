"use client";
import { ArrowRight } from "lucide-react";
import React, { useState, useMemo, useCallback, memo } from "react";

interface AccordionItemData {
  title: string;
  content: string;
}

interface TutorialData {
  chapters?: Array<{
    title: string;
    content: string;
    chapter_number: number;
  }>;
  abstractions?: Array<{
    name: string;
    description: string;
    complexity: string;
    type: string;
    hands_on_activity?: string;
    key_concepts?: string[];
    learning_value?: string;
    prerequisites?: string[];
    files_involved?: string[];
  }>;
}

interface AccordionProps {
  items: AccordionItemData[] | TutorialData;
  onArrowClick?: (index: number, content: string, title: string) => void;
  selectedIndex?: number;
}

interface AccordionItemProps {
  title: string;
  content: string;
  abstractionData?: {
    name?: string;
    description?: string;
    complexity: string;
    type: string;
    hands_on_activity?: string;
    key_concepts?: string[];
    learning_value?: string;
    prerequisites?: string[];
    files_involved?: string[];
  };
  isOpen: boolean;
  onClick: () => void;
  isLast: boolean;
  onArrowClick?: () => void;
  index: number;
  isSelected?: boolean;
}

const AccordionItem = memo(function AccordionItem({
  title,
  content,
  abstractionData,
  isOpen,
  onClick,
  isLast,
  onArrowClick,
  index,
  isSelected,
}: AccordionItemProps) {
  const uniqueId = useMemo(() => title.replace(/\s+/g, "-"), [title]);

  const containerClasses = useMemo(
    () => {
      let classes = !isLast ? "border-b border-slate-700" : "";
      if (isSelected) {
        classes += " bg-blue-900/20 border-blue-500/30 transition-all duration-300";
      }
      return classes;
    },
    [isLast, isSelected]
  );

  const buttonClasses = useMemo(
    () =>
      "w-full flex justify-between items-center p-3 text-left font-medium text-slate-200 hover:bg-slate-700/50 focus:outline-none focus-visible:ring focus-visible:ring-indigo-500 focus-visible:ring-opacity-75 transition-colors duration-300",
    []
  );

  const iconClasses = useMemo(
    () =>
      `w-5 h-5 text-slate-400 transition-transform duration-300 ${
        isOpen ? "rotate-45" : ""
      }`,
    [isOpen]
  );

  const contentClasses = useMemo(
    () =>
      `grid overflow-hidden transition-all duration-500 ease-in-out ${
        isOpen ? "grid-rows-[1fr] opacity-100" : "grid-rows-[0fr] opacity-0"
      }`,
    [isOpen]
  );

  const getComplexityColor = (complexity: string) => {
    switch (complexity?.toLowerCase()) {
      case "beginner":
        return "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300";
      case "intermediate":
        return "bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-300";
      case "advanced":
        return "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300";
      default:
        return "bg-gray-100 text-gray-800 dark:bg-gray-700/30 dark:text-gray-300";
    }
  };

  const getTypeColor = (type: string) => {
    switch (type?.toLowerCase()) {
      case "api":
        return "bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300";
      case "data":
        return "bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-300";
      case "security":
        return "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300";
      case "workflow":
        return "bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-300";
      default:
        return "bg-gray-100 text-gray-800 dark:bg-gray-700/30 dark:text-gray-300";
    }
  };

  return (
    <div className={containerClasses}>
      <div className="flex items-stretch group relative">
        {/* Arrow Button */}
        <button
          onClick={onArrowClick}
          className={`flex-shrink-0 w-10 sm:w-8 h-auto flex items-center justify-center border-r border-slate-700 transition-all duration-300 ${
            isSelected 
              ? 'bg-blue-600/40 hover:bg-blue-600/60' 
              : 'bg-slate-800/50 hover:bg-blue-600/20 group-hover:bg-blue-600/10'
          }`}
          title="View chapter content"
        >
          <ArrowRight className={`w-4 h-4 sm:w-3.5 sm:h-3.5 transition-all duration-300 ${
            isSelected 
              ? 'text-blue-300 translate-x-0.5' 
              : 'text-slate-400 group-hover:text-blue-400 group-hover:translate-x-0.5'
          }`} />
        </button>
        
        {/* Accordion Button */}
        <button
          type="button"
          className={`flex-1 flex justify-between items-center p-3 sm:p-4 text-left font-medium text-slate-200 focus:outline-none focus-visible:ring focus-visible:ring-indigo-500 focus-visible:ring-opacity-75 transition-all duration-300 ${
            isSelected 
              ? 'bg-blue-900/30 hover:bg-blue-900/40' 
              : 'hover:bg-slate-700/50 group-hover:bg-slate-700/30'
          }`}
          onClick={onClick}
          aria-expanded={isOpen}
          aria-controls={`accordion-content-${uniqueId}`}
          id={`accordion-header-${uniqueId}`}
        >
          <span className={`transition-all duration-300 text-sm sm:text-base ${
            isSelected 
              ? 'text-blue-200 translate-x-1' 
              : 'group-hover:translate-x-1'
          }`}>{title}</span>
          <div className="w-5 h-5 sm:w-6 sm:h-6 flex-shrink-0 flex items-center justify-center">
            <svg
              className={iconClasses}
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
              strokeWidth={2}
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M12 4.5v15m7.5-7.5h-15"
              />
            </svg>
          </div>
        </button>
      </div>

      <div
        id={`accordion-content-${uniqueId}`}
        role="region"
        aria-labelledby={`accordion-header-${uniqueId}`}
        className={contentClasses}
      >
        <div className="overflow-hidden">
          <div className="p-4 sm:p-5 pt-3 text-slate-400 space-y-3 sm:space-y-4">
            {/* Description - Show abstraction description in accordion dropdown */}
            {abstractionData && (
              <div className="text-slate-300 text-xs sm:text-sm leading-relaxed">
                {abstractionData.name}: {abstractionData.description || content}
              </div>
            )}
            {!abstractionData && (
              <div className="text-slate-300 text-xs sm:text-sm leading-relaxed">
                {content}
              </div>
            )}

            {/* Badges for Complexity and Type */}
            {abstractionData && (
              <div className="flex flex-wrap gap-1.5 sm:gap-2">
                {abstractionData.complexity && (
                  <span
                    className={`inline-flex items-center px-2 sm:px-2.5 py-0.5 rounded-full text-xs font-medium ${getComplexityColor(
                      abstractionData.complexity
                    )}`}
                  >
                    {abstractionData.complexity}
                  </span>
                )}
                {abstractionData.type && (
                  <span
                    className={`inline-flex items-center px-2 sm:px-2.5 py-0.5 rounded-full text-xs font-medium ${getTypeColor(
                      abstractionData.type
                    )}`}
                  >
                    {abstractionData.type}
                  </span>
                )}
              </div>
            )}

            {/* Key Concepts */}
            {abstractionData?.key_concepts &&
              abstractionData.key_concepts.length > 0 && (
                <div className="bg-slate-800/40 rounded-lg p-2.5 sm:p-3 border border-slate-600/30">
                  <h4 className="text-xs sm:text-sm font-semibold text-slate-200 mb-2 flex items-center">
                    <svg
                      className="w-3.5 h-3.5 sm:w-4 sm:h-4 mr-1.5 sm:mr-2 text-blue-400"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"
                      />
                    </svg>
                    Key Concepts
                  </h4>
                  <ul className="space-y-1">
                    {abstractionData.key_concepts.map((concept, idx) => (
                      <li
                        key={idx}
                        className="flex items-start text-xs sm:text-sm text-slate-300"
                      >
                        <span className="w-1.5 h-1.5 bg-blue-400 rounded-full mt-1.5 sm:mt-2 mr-2 flex-shrink-0"></span>
                        {concept}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

            {/* Hands-on Activity */}
            {abstractionData?.hands_on_activity && (
              <div className="bg-slate-800/40 rounded-lg p-2.5 sm:p-3 border border-slate-600/30">
                <h4 className="text-xs sm:text-sm font-semibold text-slate-200 mb-2 flex items-center">
                  <svg
                    className="w-3.5 h-3.5 sm:w-4 sm:h-4 mr-1.5 sm:mr-2 text-green-400"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M14.828 14.828a4 4 0 01-5.656 0M9 10h1.586a1 1 0 01.707.293l2.414 2.414a1 1 0 00.707.293H15M13 16h-1m-1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                    />
                  </svg>
                  Hands-on Activity
                </h4>
                <p className="text-xs sm:text-sm text-slate-300 leading-relaxed">
                  {abstractionData.hands_on_activity}
                </p>
              </div>
            )}

            {/* Learning Value */}
            {abstractionData?.learning_value && (
              <div className="bg-slate-800/40 rounded-lg p-3 border border-slate-600/30">
                <h4 className="text-sm font-semibold text-slate-200 mb-2 flex items-center">
                  <svg
                    className="w-4 h-4 mr-2 text-yellow-400"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z"
                    />
                  </svg>
                  Learning Value
                </h4>
                <p className="text-sm text-slate-300 leading-relaxed">
                  {abstractionData.learning_value}
                </p>
              </div>
            )}

            {/* Prerequisites */}
            {abstractionData?.prerequisites &&
              abstractionData.prerequisites.length > 0 && (
                <div className="bg-slate-800/40 rounded-lg p-3 border border-slate-600/30">
                  <h4 className="text-sm font-semibold text-slate-200 mb-2 flex items-center">
                    <svg
                      className="w-4 h-4 mr-2 text-purple-400"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                      />
                    </svg>
                    Prerequisites
                  </h4>
                  <ul className="space-y-1">
                    {abstractionData.prerequisites.map((prereq, idx) => (
                      <li
                        key={idx}
                        className="flex items-start text-sm text-slate-300"
                      >
                        <span className="w-1.5 h-1.5 bg-purple-400 rounded-full mt-2 mr-2 flex-shrink-0"></span>
                        {prereq}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

            {/* Files Involved */}
            {abstractionData?.files_involved &&
              abstractionData.files_involved.length > 0 && (
                <div className="bg-slate-800/40 rounded-lg p-3 border border-slate-600/30">
                  <h4 className="text-sm font-semibold text-slate-200 mb-2 flex items-center">
                    <svg
                      className="w-4 h-4 mr-2 text-orange-400"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                      />
                    </svg>
                    Files Involved
                  </h4>
                  <ul className="space-y-1">
                    {abstractionData.files_involved.map((file, idx) => (
                      <li
                        key={idx}
                        className="flex items-start text-sm text-slate-300 font-mono"
                      >
                        <span className="w-1.5 h-1.5 bg-orange-400 rounded-full mt-2 mr-2 flex-shrink-0"></span>
                        {file}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
          </div>
        </div>
      </div>
    </div>
  );
});

export default function Accordion({ items, onArrowClick, selectedIndex }: AccordionProps) {
  const [openIndex, setOpenIndex] = useState<number | null>(null);

  const handleClick = useCallback((index: number) => {
    setOpenIndex((prevIndex) => (prevIndex === index ? null : index));
  }, []);

  const handleArrowClick = useCallback((index: number, content: string, title: string) => {
    if (onArrowClick) {
      onArrowClick(index, content, title);
    }
  }, [onArrowClick]);

  const containerClasses = useMemo(
    () => "shadow-lg border-r border-slate-800 backdrop-blur-sm",
    []
  );

  // Process items to create accordion data with abstraction details
  const accordionData = useMemo(() => {
    // Check if items is a simple array
    if (Array.isArray(items)) {
      return items.map((item) => ({ ...item, abstractionData: undefined }));
    }

    // Check if items has tutorial structure
    const tutorialData = items as TutorialData;
    const chapters = tutorialData.chapters || [];
    const abstractions = tutorialData.abstractions || [];

    // If we have chapters, use them with abstractions
    if (chapters.length > 0) {
      return chapters.map((chapter, index) => {
        const abstraction = abstractions[index];
        return {
          title: chapter.title,
          content: chapter.content || 'No content available',
          abstractionData: abstraction ? {
            name: abstraction.name,
            description: abstraction.description,
            complexity: abstraction.complexity,
            type: abstraction.type,
            hands_on_activity: abstraction.hands_on_activity,
            key_concepts: abstraction.key_concepts,
            learning_value: abstraction.learning_value,
            prerequisites: abstraction.prerequisites,
            files_involved: abstraction.files_involved,
          } : undefined
        };
      });
    }

    // If no chapters, create them from abstractions
    return abstractions.map((abstraction, index) => {
      // Create detailed markdown content from abstraction
      const markdownContent = createMarkdownFromAbstraction(abstraction);
      
      return {
        title: abstraction.name,
        content: markdownContent,
        abstractionData: {
          name: abstraction.name,
          description: abstraction.description,
          complexity: abstraction.complexity,
          type: abstraction.type,
          hands_on_activity: abstraction.hands_on_activity,
          key_concepts: abstraction.key_concepts,
          learning_value: abstraction.learning_value,
          prerequisites: abstraction.prerequisites,
          files_involved: abstraction.files_involved,
        }
      };
    });

    // Helper function to create markdown content from abstraction
    function createMarkdownFromAbstraction(abstraction: any): string {
      let content = `# ${abstraction.name}\n\n`;
      
      if (abstraction.description) {
        content += `## Overview\n\n${abstraction.description}\n\n`;
      }
      
      if (abstraction.key_concepts && abstraction.key_concepts.length > 0) {
        content += `## Key Concepts\n\n`;
        abstraction.key_concepts.forEach((concept: string) => {
          content += `- **${concept}**\n`;
        });
        content += `\n`;
      }
      
      if (abstraction.hands_on_activity) {
        content += `## Hands-on Activity\n\n${abstraction.hands_on_activity}\n\n`;
      }
      
      if (abstraction.learning_value) {
        content += `## Learning Value\n\n${abstraction.learning_value}\n\n`;
      }
      
      if (abstraction.prerequisites && abstraction.prerequisites.length > 0) {
        content += `## Prerequisites\n\n`;
        abstraction.prerequisites.forEach((prereq: string) => {
          content += `- ${prereq}\n`;
        });
        content += `\n`;
      }
      
      if (abstraction.files_involved && abstraction.files_involved.length > 0) {
        content += `## Files Involved\n\n`;
        abstraction.files_involved.forEach((file: string) => {
          content += `- \`${file}\`\n`;
        });
        content += `\n`;
      }
      
      content += `## Complexity Level\n\n**${abstraction.complexity}** - This concept is suitable for ${abstraction.complexity.toLowerCase()} level learners.\n\n`;
      content += `## Type\n\n**${abstraction.type}** - This falls under the ${abstraction.type.toLowerCase()} category.`;
      
      return content;
    }
  }, [items]);

  return (
    <div className={containerClasses}>
      {accordionData.map((item, index) => (
        <AccordionItem
          key={`${item.title}-${index}`}
          title={item.title}
          content={item.content}
          abstractionData={item.abstractionData}
          isOpen={openIndex === index}
          onClick={() => handleClick(index)}
          onArrowClick={() => handleArrowClick(index, item.content, item.title)}
          isLast={index === accordionData.length - 1}
          isSelected={selectedIndex === index}
          index={index}
        />
      ))}
    </div>
  );
}
