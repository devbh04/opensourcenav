interface ChapterControlsProps {
  chapterIndex: number;
  chapterTitle: string;
  onToggleFullScreen?: () => void;
  onClose: () => void;
  isTransitioning: boolean;
  showFullScreenButton?: boolean;
}

export const ChapterControls = ({
  chapterIndex,
  chapterTitle,
  onToggleFullScreen,
  onClose,
  isTransitioning,
  showFullScreenButton = false
}: ChapterControlsProps) => {
  return (
    <div className="flex flex-col sm:flex-row sm:items-center justify-between mb-4 lg:mb-6 border-b border-slate-600 pb-3 lg:pb-4">
      <h1
        className={`text-lg sm:text-xl lg:text-2xl font-bold text-white mb-2 sm:mb-0 flex-1 pr-2 transition-all duration-300 delay-200 ${
          isTransitioning
            ? "opacity-0 translate-x-4"
            : "opacity-100 translate-x-0"
        }`}
      >
        Chapter {chapterIndex + 1}: {chapterTitle}
      </h1>
      <div
        className={`flex items-center gap-2 transition-all duration-300 delay-300 ${
          isTransitioning
            ? "opacity-0 translate-x-4"
            : "opacity-100 translate-x-0"
        }`}
      >
        {/* Mobile Full Screen Button */}
        {showFullScreenButton && onToggleFullScreen && (
          <button
            onClick={onToggleFullScreen}
            className="lg:hidden text-slate-400 hover:text-white transition-all duration-200 p-1 hover:bg-slate-700/30 rounded"
            title="Full screen view"
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
                d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4"
              />
            </svg>
          </button>
        )}
        <button
          onClick={onClose}
          className="text-slate-400 hover:text-white transition-all duration-200 p-1 hover:bg-slate-700/30 rounded"
          title="Close chapter"
        >
          <svg
            className="w-5 h-5 sm:w-6 sm:h-6 transition-transform duration-200 hover:scale-110"
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
  );
};
