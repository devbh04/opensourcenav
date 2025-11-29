interface TransitionOverlayProps {
  isVisible: boolean;
}

export const TransitionOverlay = ({ isVisible }: TransitionOverlayProps) => {
  if (!isVisible) return null;

  return (
    <div className="fixed inset-0 z-40 bg-black/50 backdrop-blur-sm transition-opacity duration-300 ease-out">
      <div className="flex items-center justify-center h-full">
        <div className="flex flex-col items-center space-y-3">
          <div className="animate-spin rounded-full h-8 w-8 border-2 border-blue-400 border-t-transparent"></div>
          <div className="text-slate-300 text-sm animate-pulse">
            Loading...
          </div>
        </div>
      </div>
    </div>
  );
};
