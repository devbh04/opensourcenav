import Accordion from "@/components/ui/accordion-sera";
import {
  BluetoothConnected,
  Brain,
  Calendar,
  Github,
  Globe,
  Hash,
  Pipette,
  BookOpen,
  Users,
  Target,
  Lightbulb,
  Activity,
  Code,
  FileText,
  GitBranch,
  Database,
  Shield,
  Zap,
} from "lucide-react";

// --- The Page Component ---
interface TutorialMetadata {
  abstractions_identified?: number;
  chapters_generated?: number;
  files_processed?: number;
  project_name?: string;
  relationships_found?: number;
  selected_files_used?: number;
}

interface TutorialPageAccordionProps {
  repo: string;
  onChapterSelect?: (index: number, content: string, title: string) => void;
  selectedChapterIndex?: number;
  tutorialData?: any; // Tutorial response data
  tutorialMetadata?: TutorialMetadata;
  repositoryMetadata?: any; // Repository metadata
}

export default function TutorialPageAccordion({
  repo,
  onChapterSelect,
  selectedChapterIndex,
  tutorialData,
  tutorialMetadata,
  repositoryMetadata,
}: TutorialPageAccordionProps) {
  const [owner, reponame] = repo.split("/");

  // Use provided tutorial metadata or extract from tutorialData.metadata, or fallback to default
  const metadata = tutorialMetadata || {
    abstractions_identified: tutorialData?.metadata?.abstractions_identified || tutorialData?.abstractions_identified || tutorialData?.concepts_identified || 0,
    chapters_generated: tutorialData?.metadata?.chapters_generated || tutorialData?.chapters_generated || tutorialData?.chapters?.length || 0,
    files_processed: tutorialData?.metadata?.files_processed || tutorialData?.files_processed || tutorialData?.total_files || 0,
    project_name: tutorialData?.metadata?.project_name || tutorialData?.project_name || repositoryMetadata?.repository || reponame || "Repository",
    relationships_found: tutorialData?.metadata?.relationships_found || tutorialData?.relationships_found || tutorialData?.connections_found || 0,
    selected_files_used: tutorialData?.metadata?.selected_files_used || tutorialData?.selected_files_used || tutorialData?.files_analyzed || 0,
  };

  // Use tutorial data chapters or fallback to empty array
  const chapters = tutorialData?.chapters || [];
  
  // Prepare the full tutorial data structure for the accordion
  const accordionData = {
    chapters: tutorialData?.chapters || [],
    abstractions: tutorialData?.abstractions || []
  };

  return (
    <div className="flex flex-col items-center justify-center font-sans transition-colors duration-500 space-y-4 sm:space-y-6">
      <div className="w-full max-w-4xl mx-auto">
        {/* Main Header Section */}
        <div className="text-center p-4 sm:p-6 lg:p-8 bg-gradient-to-br from-slate-800/40 to-slate-900/40 rounded-sm border border-slate-700/50 backdrop-blur-sm shadow-2xl">
          <div className="flex flex-col items-center">
            <img
              src="/logo/logo-96.png"
              alt="logo"
              className="h-12 w-12 sm:h-16 sm:w-16 mb-4 sm:mb-6 rounded-lg shadow-lg"
            />
            <h1 className="text-2xl sm:text-3xl lg:text-4xl font-bold font-mono mb-3 bg-gradient-to-r from-red-500 via-yellow-500 to-blue-500 bg-clip-text text-transparent animate-pulse">
              {reponame || "Repository"}
            </h1>
            <div className="flex items-center text-slate-300 text-xs sm:text-sm font-mono hover:text-white transition-colors mb-4 sm:mb-6">
              <Github className="h-3.5 w-3.5 sm:h-4 sm:w-4 mr-1.5 sm:mr-2" />
              <a
                href={`https://github.com/${owner}/${reponame}`}
                target="_blank"
                rel="noopener noreferrer"
                className="hover:underline"
              >
                github.com/{owner}/{reponame}
              </a>
            </div>

            {/* Tutorial Metadata Stats */}
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-2 sm:gap-4 w-full mb-4 sm:mb-6">
              <div className="bg-slate-800/50 rounded-lg p-2 sm:p-3 border border-slate-600/30 text-center">
                <div className="flex items-center justify-center mb-1">
                  <BookOpen className="h-3.5 w-3.5 sm:h-4 sm:w-4 text-green-400" />
                </div>
                <div className="text-base sm:text-lg font-bold text-white">
                  {metadata.abstractions_identified}
                </div>
                <div className="text-xs text-slate-400">Concepts</div>
              </div>
              <div className="bg-slate-800/50 rounded-lg p-2 sm:p-3 border border-slate-600/30 text-center">
                <div className="flex items-center justify-center mb-1">
                  <Code className="h-3.5 w-3.5 sm:h-4 sm:w-4 text-blue-400" />
                </div>
                <div className="text-base sm:text-lg font-bold text-white">
                  {metadata.chapters_generated}
                </div>
                <div className="text-xs text-slate-400">Chapters</div>
              </div>
              <div className="bg-slate-800/50 rounded-lg p-2 sm:p-3 border border-slate-600/30 text-center">
                <div className="flex items-center justify-center mb-1">
                  <FileText className="h-3.5 w-3.5 sm:h-4 sm:w-4 text-purple-400" />
                </div>
                <div className="text-base sm:text-lg font-bold text-white">
                  {metadata.selected_files_used}
                </div>
                <div className="text-xs text-slate-400">Files</div>
              </div>
              <div className="bg-slate-800/50 rounded-lg p-2 sm:p-3 border border-slate-600/30 text-center">
                <div className="flex items-center justify-center mb-1">
                  <GitBranch className="h-3.5 w-3.5 sm:h-4 sm:w-4 text-orange-400" />
                </div>
                <div className="text-base sm:text-lg font-bold text-white">
                  {metadata.relationships_found}
                </div>
                <div className="text-xs text-slate-400">Relations</div>
              </div>
            </div>

            {/* Generation Metadata */}
            <div className="grid grid-cols-2 gap-2 sm:gap-4 justify-center w-full">
              <div className="space-y-1 sm:space-y-2">
                <div className="flex items-center justify-center sm:justify-start">
                  <p className="flex text-white items-center text-xs sm:text-sm">
                    <Globe className="inline-block mr-1.5 sm:mr-2 h-3.5 w-3.5 sm:h-4 sm:w-4 text-gray-400" />
                    English
                  </p>
                </div>
                <div className="flex items-center justify-center sm:justify-start">
                  <p className="text-green-400 flex items-center text-xs sm:text-sm">
                    <Brain className="inline-block text-gray-400 mr-1.5 sm:mr-2 h-3.5 w-3.5 sm:h-4 sm:w-4" />
                    Gemini-2.0-flash
                  </p>
                </div>
              </div>
              <div className="space-y-1 sm:space-y-2">
                <div className="flex items-center justify-center sm:justify-end">
                  <p className="text-purple-400 flex items-center text-xs sm:text-sm">
                    <Hash className="inline-block text-gray-400 mr-1.5 sm:mr-2 h-3.5 w-3.5 sm:h-4 sm:w-4" />
                    commit
                  </p>
                </div>
                <div className="flex items-center justify-center sm:justify-end">
                  <p className="text-red-400 flex items-center text-xs sm:text-sm">
                    <Calendar className="inline-block text-gray-400 mr-1.5 sm:mr-2 h-3.5 w-3.5 sm:h-4 sm:w-4" />
                    {new Date().toLocaleDateString("en-US", {
                      year: "numeric",
                      month: "short",
                      day: "numeric",
                    })}
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>

        <Accordion 
          items={accordionData} 
          onArrowClick={onChapterSelect} 
          selectedIndex={selectedChapterIndex} 
        />
      </div>
    </div>
  );
}
