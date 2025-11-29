import { ChapterControls } from "./chapter-controls";
import { MarkdownRenderer } from "./markdown-renderer";

interface ChapterContent {
  index: number;
  title: string;
  content: string;
}

interface ChapterContentViewProps {
  chapter: ChapterContent | null;
  onToggleFullScreen: () => void;
  onClose: () => void;
  isTransitioning: boolean;
}

export const ChapterContentView = ({
  chapter,
  onToggleFullScreen,
  onClose,
  isTransitioning
}: ChapterContentViewProps) => {
  if (!chapter) return null;

  return (
    <div
      key={chapter.index}
      className={`p-3 sm:p-4 lg:p-6 transition-all duration-500 ease-out ${
        isTransitioning
          ? "opacity-0 translate-y-4 scale-95"
          : "opacity-100 translate-y-0 scale-100"
      }`}
    >
      <div
        className={`bg-slate-900/50 rounded-lg p-3 sm:p-4 lg:p-6 border border-slate-600/30 transform transition-all duration-500 ease-out ${
          isTransitioning
            ? "opacity-0 scale-95"
            : "opacity-100 scale-100"
        }`}
      >
        <ChapterControls
          chapterIndex={chapter.index}
          chapterTitle={chapter.title}
          onToggleFullScreen={onToggleFullScreen}
          onClose={onClose}
          isTransitioning={isTransitioning}
          showFullScreenButton={true}
        />
        <div
          className={`transition-all duration-700 delay-400 ease-out ${
            isTransitioning
              ? "opacity-0 translate-y-6"
              : "opacity-100 translate-y-0"
          }`}
        >
          <MarkdownRenderer content={chapter.content} />
        </div>
      </div>
    </div>
  );
};
