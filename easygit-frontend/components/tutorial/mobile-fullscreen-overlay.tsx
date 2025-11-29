import { ChapterControls } from "./chapter-controls";
import { MarkdownRenderer } from "./markdown-renderer";

interface ChapterContent {
  index: number;
  title: string;
  content: string;
}

interface MobileFullscreenOverlayProps {
  chapter: ChapterContent | null;
  isFullScreen: boolean;
  isTransitioning: boolean;
  onToggleFullScreen: () => void;
  onClose: () => void;
}

export const MobileFullscreenOverlay = ({
  chapter,
  isFullScreen,
  isTransitioning,
  onToggleFullScreen,
  onClose
}: MobileFullscreenOverlayProps) => {
  if (!isFullScreen || !chapter) return null;

  return (
    <div
      className={`fixed inset-0 z-50 bg-black lg:hidden transition-all duration-300 ease-out ${
        isTransitioning ? "opacity-0 scale-95" : "opacity-100 scale-100"
      }`}
    >
      <div className="h-full overflow-y-auto">
        <div className="p-3 sm:p-4 transition-opacity duration-300 delay-150">
          <div className="bg-slate-900/50 rounded-lg p-3 sm:p-4 border border-slate-600/30 transform transition-transform duration-300 ease-out">
            <div className="flex items-center justify-between mb-4 border-b border-slate-600 pb-3">
              <h1 className="text-lg font-bold text-white flex-1 pr-2 animate-fade-in">
                Chapter {chapter.index + 1}: {chapter.title}
              </h1>
              <div className="flex items-center gap-2 animate-fade-in">
                <button
                  onClick={onToggleFullScreen}
                  className="text-slate-400 hover:text-white transition-all duration-200 p-1 hover:bg-slate-700/30 rounded"
                  title="Back to split view"
                >
                  <svg
                    className="w-5 h-5 transition-transform duration-200 hover:scale-110"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M8 3v3a2 2 0 01-2 2H3m18 0h-3a2 2 0 01-2-2V3m0 18v-3a2 2 0 012-2h3M3 16h3a2 2 0 012 2v3"
                    />
                  </svg>
                </button>
                <button
                  onClick={onClose}
                  className="text-slate-400 hover:text-white transition-all duration-200 p-1 hover:bg-slate-700/30 rounded"
                  title="Close chapter"
                >
                  <svg
                    className="w-5 h-5 transition-transform duration-200 hover:scale-110"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M6 18L18 6M6 6l12 12"
                    />
                  </svg>
                </button>
              </div>
            </div>
            <div className="animate-slide-up">
              <MarkdownRenderer content={chapter.content} isMobile={true} />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
