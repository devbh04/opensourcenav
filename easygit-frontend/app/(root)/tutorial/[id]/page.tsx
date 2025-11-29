"use client";

import TutorialPageAccordion from "@/components/shared/tutorial-page-accordion";
import { useParams, useRouter } from "next/navigation";
import { useState, useEffect } from "react";
import { 
  TransitionOverlay, 
  MobileFullscreenOverlay,
  ChapterContentView,
  EmptyState
} from "@/components/tutorial";
import useTutorialStore from "@/store/tutorialstore";
import { toast } from "sonner";
import { ChatQABox } from "@/components/chat/chat-qa-box";

interface ChapterContent {
  index: number;
  title: string;
  content: string;
}

export default function TutorialPage() {
  const { id } = useParams();
  const router = useRouter();
  const { tutorialResponse, repositoryMetadata, clearAll } = useTutorialStore();
  
  const [selectedChapter, setSelectedChapter] = useState<ChapterContent | null>(
    null
  );
  const [isFullScreen, setIsFullScreen] = useState(false);
  const [isTransitioning, setIsTransitioning] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [hasCheckedData, setHasCheckedData] = useState(false);

  // Effect to wait for Zustand store hydration
  useEffect(() => {
    // Check if we're in browser environment
    if (typeof window !== 'undefined') {
      // Give Zustand persist middleware time to hydrate
      const hydrateTimeout = setTimeout(() => {
        setIsLoading(false);
      }, 500);

      return () => clearTimeout(hydrateTimeout);
    } else {
      setIsLoading(false);
    }
  }, []);

  const linkify = (id: string) => {
    if (!id) return "No repository selected";
    return id.replace("--", "/");
  };
  const repo = linkify(id as string);

  // Check if we have tutorial data after hydration
  useEffect(() => {
    // Only run this check after the store has had time to hydrate
    if (!isLoading) {
      const checkDataTimeout = setTimeout(() => {
        setHasCheckedData(true);

        console.log("Tutorial page data check:", {
          id,
          repo,
          hasTutorialResponse: !!tutorialResponse,
          tutorialSuccess: tutorialResponse?.success,
          hasData: !!tutorialResponse?.data,
          hasChapters: !!tutorialResponse?.data?.chapters,
          chaptersLength: tutorialResponse?.data?.chapters?.length,
          repositoryMetadata: repositoryMetadata,
        });

        // Log the structure of tutorial data to help with debugging
        if (tutorialResponse?.data) {
          console.log("Tutorial data structure:", {
            keys: Object.keys(tutorialResponse.data),
            sampleData: {
              abstractions_identified: tutorialResponse.data.abstractions_identified,
              chapters_generated: tutorialResponse.data.chapters_generated,
              files_processed: tutorialResponse.data.files_processed,
              project_name: tutorialResponse.data.project_name,
              relationships_found: tutorialResponse.data.relationships_found,
              selected_files_used: tutorialResponse.data.selected_files_used,
              chapters_count: tutorialResponse.data.chapters?.length,
              chapters_preview: tutorialResponse.data.chapters?.slice(0, 2)?.map((ch: any) => ({
                title: ch.title || ch.name,
                hasContent: !!ch.content,
              })),
            }
          });
        }

        // Only redirect if we've waited and still no data
        if (!tutorialResponse || !tutorialResponse.success || !tutorialResponse.data) {
          console.log("No valid tutorial data found after hydration, redirecting to repository page");
          toast.error("No tutorial data found. Please generate a tutorial first.");
          
          // Small delay to allow the toast to show
          setTimeout(() => {
            router.push(`/tutorial/repo/${id}`);
          }, 1500);
          return;
        }

        // If tutorial data doesn't match the current repo, show warning
        const expectedRepo = `https://github.com/${repo}`;
        if (tutorialResponse.repositoryUrl && tutorialResponse.repositoryUrl !== expectedRepo) {
          console.warn("Tutorial data mismatch:", {
            expected: expectedRepo,
            actual: tutorialResponse.repositoryUrl
          });
          toast.warning("Tutorial data might be for a different repository.");
        }
      }, 500); // Additional small delay after hydration

      return () => clearTimeout(checkDataTimeout);
    }
  }, [isLoading, id, repo, tutorialResponse, repositoryMetadata, router]);

  // Show loading state while checking for data or redirecting
  if (isLoading || (!tutorialResponse && !hasCheckedData) || (!tutorialResponse?.success && !hasCheckedData) || (!tutorialResponse?.data && !hasCheckedData)) {
    return (
      <div className="w-full h-screen flex flex-col items-center justify-center bg-black text-white">
        <div className="text-center space-y-4">
          <div className="animate-spin rounded-full h-12 w-12 border-2 border-blue-400 border-t-transparent mx-auto"></div>
          <h2 className="text-xl font-semibold">Loading Tutorial...</h2>
          <p className="text-slate-400">
            {isLoading 
              ? "Checking for tutorial data..." 
              : !tutorialResponse 
                ? "No tutorial data found. Redirecting to generate tutorial..." 
                : "Processing tutorial data..."}
          </p>
        </div>
      </div>
    );
  }

  // If we've checked and still no valid data, show error (this shouldn't happen due to redirect)
  if (hasCheckedData && (!tutorialResponse || !tutorialResponse.success || !tutorialResponse.data)) {
    return (
      <div className="w-full h-screen flex flex-col items-center justify-center bg-black text-white">
        <div className="text-center space-y-4">
          <h2 className="text-xl font-semibold text-red-400">Tutorial Not Found</h2>
          <p className="text-slate-400">
            No tutorial data available for this repository.
          </p>
          <button 
            onClick={() => router.push(`/tutorial/repo/${id}`)}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors"
          >
            Generate Tutorial
          </button>
        </div>
      </div>
    );
  }

  const handleChapterSelect = (
    index: number,
    content: string,
    title: string
  ) => {
    // Always show transition when selecting a new chapter
    setIsTransitioning(true);

    setTimeout(() => {
      setSelectedChapter({ index, title, content });

      // On mobile, automatically go to full screen when chapter is selected
      if (window.innerWidth < 1024) {
        setTimeout(() => {
          setIsFullScreen(true);
          setTimeout(() => {
            setIsTransitioning(false);
          }, 100);
        }, 100);
      } else {
        // Desktop - just finish transition
        setTimeout(() => {
          setIsTransitioning(false);
        }, 100);
      }
    }, 150);
  };

  const toggleFullScreen = () => {
    setIsTransitioning(true);
    setTimeout(() => {
      setIsFullScreen(!isFullScreen);
      setTimeout(() => {
        setIsTransitioning(false);
      }, 100);
    }, 200);
  };

  const closeChapter = () => {
    setIsTransitioning(true);
    setTimeout(() => {
      setSelectedChapter(null);
      setIsFullScreen(false);
      setTimeout(() => {
        setIsTransitioning(false);
      }, 100);
    }, 200);
  };

  return (
    <div className="w-full h-screen flex flex-col">
      <TransitionOverlay isVisible={isTransitioning} />

      <MobileFullscreenOverlay
        chapter={selectedChapter}
        isFullScreen={isFullScreen}
        isTransitioning={isTransitioning}
        onToggleFullScreen={toggleFullScreen}
        onClose={closeChapter}
      />

      <div className="flex-1 flex flex-col lg:flex-row overflow-hidden">
        {/* Mobile: Stack vertically, Desktop: Side by side */}
        <div
          className={`w-full lg:w-1/4 h-1/2 lg:h-full overflow-y-auto border-b lg:border-b-0 lg:border-r border-slate-700 transition-all duration-300 ease-out ${
            isFullScreen ? "hidden lg:block" : ""
          } ${
            isTransitioning ? "opacity-50 scale-95" : "opacity-100 scale-100"
          }`}
        >
          <TutorialPageAccordion
            repo={repo as string}
            onChapterSelect={handleChapterSelect}
            selectedChapterIndex={selectedChapter?.index}
            tutorialData={tutorialResponse?.data}
            repositoryMetadata={repositoryMetadata}
            tutorialMetadata={tutorialResponse?.data?.metadata ? {
              abstractions_identified: tutorialResponse.data.metadata.abstractions_identified,
              chapters_generated: tutorialResponse.data.metadata.chapters_generated,
              files_processed: tutorialResponse.data.metadata.files_processed,
              project_name: tutorialResponse.data.metadata.project_name,
              relationships_found: tutorialResponse.data.metadata.relationships_found,
              selected_files_used: tutorialResponse.data.metadata.selected_files_used,
            } : tutorialResponse?.data ? {
              abstractions_identified: tutorialResponse.data.abstractions_identified,
              chapters_generated: tutorialResponse.data.chapters_generated || tutorialResponse.data.chapters?.length,
              files_processed: tutorialResponse.data.files_processed,
              project_name: repositoryMetadata?.repository || repo.split('/')[1],
              relationships_found: tutorialResponse.data.relationships_found,
              selected_files_used: tutorialResponse.data.selected_files_used,
            } : undefined}
          />
          
          {/* Show message if no chapters available */}
          {tutorialResponse?.data && (!tutorialResponse.data.chapters || tutorialResponse.data.chapters.length === 0) && (
            <div className="bg-slate-800/50 rounded-lg p-6 border border-slate-600/30 text-center">
              <h3 className="text-xl font-semibold text-yellow-400 mb-2">No Chapters Available</h3>
              <p className="text-slate-300">
                The tutorial was generated successfully but no chapters were found in the response data.
              </p>
              <p className="text-slate-400 text-sm mt-2">
                Please check the API response format or try generating the tutorial again.
              </p>
            </div>
          )}
        </div>
        <div
          className={`w-full lg:w-3/4 h-1/2 lg:h-full bg-black overflow-y-auto transition-all duration-300 ease-out ${
            isFullScreen ? "hidden lg:block" : ""
          } ${
            isTransitioning ? "opacity-50 scale-95" : "opacity-100 scale-100"
          }`}
        >
          {selectedChapter ? (
            <ChapterContentView
              chapter={selectedChapter}
              onToggleFullScreen={toggleFullScreen}
              onClose={closeChapter}
              isTransitioning={isTransitioning}
            />
          ) : (
            <EmptyState />
          )}
        </div>
      </div>
      
      <ChatQABox image={"/qa-logo.png"}/>
    </div>
  );
}
