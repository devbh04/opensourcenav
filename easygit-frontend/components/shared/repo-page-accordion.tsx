import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion"
import useTutorialStore from "@/store/tutorialstore"
import { User, Database, GitBranch, Hash, Folder, HardDrive } from "lucide-react"
import { RepositoryMetadata } from "./file-tree"

interface RepoPageAccordionProps {
  owner?: string;
  repoName?: string;
  repositoryMetadata?: RepositoryMetadata;
}

export default function RepoPageAccordion({ 
  owner = "devbh04", 
  repoName = "ind1", 
  repositoryMetadata 
}: RepoPageAccordionProps) {
  const { selectedFiles, includeFileTypes, excludeFileTypes } = useTutorialStore();

  // Use metadata if available, otherwise fall back to props
  const displayOwner = repositoryMetadata?.owner || owner;
  const displayRepo = repositoryMetadata?.repository || repoName;
  const displayRef = repositoryMetadata?.requestedRef || "Default Branch";
  const displayCommit = repositoryMetadata?.resolvedCommit || "e38be150615e395524655f9da783b969e1c45437";
  const displayPath = repositoryMetadata?.path || "Repository Root";
  const displayMaxSize = repositoryMetadata?.maxSize || "100 KB";

  return (
    <Accordion
      type="single"
      collapsible
      className="w-full border border-gray-700 p-4 rounded-xl bg-gray-900"
      defaultValue="item-1"
    >
      <AccordionItem value="item-1" className="">
        <AccordionTrigger className="text-blue-400">Repository Configuration</AccordionTrigger>
        <AccordionContent className="flex flex-col gap-4 text-balance mt-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
            <div className="space-y-3">
              <div className="flex items-center gap-2">
                <User className="w-3 h-3 text-gray-400" />
                <span className="text-gray-400 font-medium">Owner:</span>
                <span className="ml-2 text-white font-medium">{displayOwner}</span>
              </div>
              <div className="flex items-center gap-2">
                <Database className="w-3 h-3 text-gray-400" />
                <span className="text-gray-400 font-medium">Repository:</span>
                <span className="ml-2 text-white font-medium">{displayRepo}</span>
              </div>
              <div>
                <span className="text-gray-400 font-medium">
                  Included files:
                </span>
                <div className="ml-2 mt-1">
                  <div className="text-green-400 text-xs font-mono bg-green-400/10 p-2 rounded max-h-20 overflow-y-auto">
                    {includeFileTypes}
                  </div>
                </div>
              </div>
            </div>
            <div className="space-y-3">
              <div className="flex items-center gap-2">
                <Hash className="w-3 h-3 text-gray-400" />
                <span className="text-gray-400 font-medium">Commit:</span>
                <span className="ml-2 text-purple-400 font-mono text-xs">
                  {displayCommit.substring(0, 8)}...
                </span>
                <button 
                  className="text-xs text-blue-400 hover:text-blue-300 underline ml-2"
                  onClick={() => navigator.clipboard.writeText(displayCommit)}
                  title="Copy full commit hash"
                >
                  copy
                </button>
              </div>
              <div className="flex items-center gap-2">
                <GitBranch className="w-3 h-3 text-gray-400" />
                <span className="text-gray-400 font-medium">Branch/Ref:</span>
                <span className="ml-2 text-green-400 font-medium">{displayRef}</span>
              </div>
              <div>
                <span className="text-gray-400 font-medium">
                  Excluded files:
                </span>
                <div className="ml-2 mt-1">
                  <div className="text-red-400 text-xs font-mono bg-red-400/10 p-2 rounded max-h-20 overflow-y-auto">
                    {excludeFileTypes}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </AccordionContent>
      </AccordionItem>
    </Accordion>
  );
}
