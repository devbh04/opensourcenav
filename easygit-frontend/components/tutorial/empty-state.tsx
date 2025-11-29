export const EmptyState = () => {
  return (
    <div className="flex items-center justify-center h-full p-4">
      <div className="text-center text-slate-400">
        <div className="mb-4">
          <svg
            className="w-12 h-12 sm:w-16 sm:h-16 mx-auto text-slate-500"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={1}
              d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
            />
          </svg>
        </div>
        <h2 className="text-lg sm:text-xl font-semibold text-slate-300 mb-2">
          Select a Chapter
        </h2>
        <p className="text-sm sm:text-base px-4">
          Click the arrow button next to any chapter title to view its
          content here
        </p>
      </div>
    </div>
  );
};
