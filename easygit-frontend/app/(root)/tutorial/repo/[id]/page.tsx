'use client';
import { InteractiveHoverButton } from "@/components/magicui/interactive-hover-button";
import FileTree from "@/components/shared/file-tree";
import RepoPageAccordion from "@/components/shared/repo-page-accordion";
import { Github, Loader2 } from "lucide-react";
import { useParams, useRouter } from "next/navigation";
import { useEffect } from "react";
import { githubAPI } from "@/lib/github-api";
import useTutorialStore, { RepositoryMetadata, TutorialResponse } from "@/store/tutorialstore";
import axios from "axios";
import { toast } from "sonner";

export default function Repo() {
    const {id} = useParams();
    const router = useRouter();
    const { 
        selectedFiles, 
        includeFileTypes, 
        excludeFileTypes,
        repositoryMetadata,
        setRepositoryMetadata,
        fileTreeData,
        setFileTreeData,
        loading,
        setLoading,
        error,
        setError,
        isGenerating,
        setIsGenerating,
        tutorialResponse,
        setTutorialResponse,
    } = useTutorialStore();

    const linkify = (id: string) => {
        if (!id) return "No repository selected";
        return id.replace('--', '/');
    }
    const repo = linkify(id as string);
    const [owner, repoName] = repo.split('/');

    useEffect(() => {
        console.log("Repository page loaded with state:", {
            repositoryMetadata,
            fileTreeDataLength: fileTreeData.length,
            selectedFilesCount: selectedFiles.length,
            loading,
            error,
        });
    }, [repositoryMetadata, fileTreeData, selectedFiles, loading, error]);

    useEffect(() => {
        const fetchRepositoryData = async () => {
            if (!owner || !repoName) return;
            
            // Check if we already have data for this repository
            const currentRepo = repositoryMetadata?.owner === owner && repositoryMetadata?.repository === repoName;
            if (currentRepo && fileTreeData.length > 0) {
                console.log("Repository data already loaded from store");
                return;
            }
            
            setLoading(true);
            setError(null);
            
            try {
                console.log("Fetching repository data from GitHub API...");
                // Fetch repository information from GitHub API
                const repoInfo = await githubAPI.getRepositoryInfo(owner, repoName);
                const tree = await githubAPI.buildFileTree(owner, repoName);
                
                // Set the repository metadata
                const metadata: RepositoryMetadata = {
                    owner: owner,
                    repository: repoName,
                    requestedRef: repoInfo.default_branch || "main",
                    resolvedCommit: repoInfo.sha || "latest",
                    path: "Repository Root",
                    maxSize: "100 KB"
                };
                
                console.log("Storing repository data in Zustand state...", {
                    metadata,
                    treeLength: tree.length
                });
                
                setRepositoryMetadata(metadata);
                setFileTreeData(tree);
            } catch (err) {
                const errorMessage = err instanceof Error ? err.message : 'Failed to fetch repository data';
                setError(errorMessage);
                console.error('Error fetching repository:', err);
            } finally {
                setLoading(false);
            }
        };

        fetchRepositoryData();
    }, [owner, repoName, repositoryMetadata, fileTreeData, setRepositoryMetadata, setFileTreeData, setLoading, setError]);

    const handleGenerateTutorial = async () => {
        try {
            if (selectedFiles.length === 0) {
                console.warn("No files selected for tutorial generation");
                toast("Please select at least one file to generate a tutorial.");
                return;
            }
            
            setIsGenerating(true);
            
            // Construct the GitHub URL from the repo info
            const githubUrl = `https://github.com/${repo}`;
            
            console.log("Generating tutorial for:", githubUrl);
            console.log("Selected files:", selectedFiles);
            console.log("Include file types:", includeFileTypes);
            console.log("Exclude file types:", excludeFileTypes);

            const payload = {
                url: githubUrl,
                selectedFiles: selectedFiles,
                includeFileTypes: includeFileTypes,
                excludeFileTypes: excludeFileTypes,
            };

            console.log("Sending payload:", payload);

            const response = await axios.post(
                "http://localhost:8000/generate-tutorial-frontend",
                payload,
                {
                    headers: {
                        "Content-Type": "application/json",
                    },
                }
            );

            console.log("Tutorial generation response:", response.data);
            
            // Store the response in Zustand state with proper typing
            const tutorialResponse: TutorialResponse = {
                success: true,
                message: "Tutorial generated successfully",
                data: response.data,
                tutorialId: response.data?.tutorial_id || response.data?.id || repo.replace('/', '--'),
                repositoryUrl: githubUrl,
                generatedAt: new Date().toISOString(),
            };
            
            setTutorialResponse(tutorialResponse);
            
            // Show success message
            toast.success("Tutorial generated successfully!");
            
            // Navigate to the tutorial page
            const tutorialId = tutorialResponse.tutorialId || repo.replace('/', '--');
            console.log("Navigating to tutorial page:", `/tutorial/${tutorialId}`);
            
            // Small delay to allow the toast to show
            setTimeout(() => {
                router.push(`/tutorial/${tutorialId}`);
            }, 1000); 
            
        } catch (error) {
            console.error("Error generating tutorial:", error);
            
            // Construct the GitHub URL from the repo info
            const githubUrl = `https://github.com/${repo}`;
            
            // Store error response
            const errorResponse: TutorialResponse = {
                success: false,
                message: error instanceof Error ? error.message : "Unknown error occurred",
                repositoryUrl: githubUrl,
                generatedAt: new Date().toISOString(),
            };
            
            setTutorialResponse(errorResponse);
            
            // Show error message using toast
            toast.error("Error generating tutorial. Please try again.");
        } finally {
            setIsGenerating(false);
        }
    };

    if (error) {
        return (
            <div className="max-w-5xl mt-8 gap-4 flex flex-col bg-slate-950 justify-center items-center mx-auto p-4 border border-slate-600 rounded-xl">
                <h1 className="text-2xl font-bold text-red-400">Error Loading Repository</h1>
                <p className="text-gray-400 text-center">{error}</p>
                <p className="text-sm text-gray-500">Please check if the repository exists and is accessible</p>
            </div>
        );
    }

    return(
        <div className="max-w-5xl mt-8 gap-4 flex flex-col bg-slate-950 justify-center items-center mx-auto p-4 border border-slate-600 rounded-xl">
            <h1 className="text-lg sm:text-2xl font-bold text-center">Select Your Desired files to Generate Tutorial</h1>
            <p className="mt-2 text-white flex items-center text-center font-mono text-sm sm:text-base"><Github className="inline-block mr-2 h-5 w-5"/>{repo}</p>
            <p className="mt-2 text-gray-400 text-center text-sm sm:text-base px-2">This page shows the files for your tutorial. <b className="text-slate-200">Usually, you don't need to change anything unless too many files are selected </b> or <b className="text-slate-200">important ones are missing.</b></p>
            <RepoPageAccordion 
                owner={owner} 
                repoName={repoName} 
                repositoryMetadata={repositoryMetadata || undefined}
            />
            {loading ? (
                <>
                <div className="flex items-center gap-3">
                    <Loader2 className="h-6 w-6 animate-spin" />
                    <h1 className="text-2xl font-bold">Loading Repository...</h1>
                </div>
                <p className="text-gray-400 text-center">Fetching file structure from GitHub</p>
                </>
            ):
            <FileTree fileTreeData={fileTreeData} />
            }
            <InteractiveHoverButton 
                onClick={() => {handleGenerateTutorial()}}
                disabled={isGenerating || selectedFiles.length === 0}
                className={`${
                    isGenerating || selectedFiles.length === 0 
                        ? "opacity-50 cursor-not-allowed" 
                        : "cursor-pointer"
                }`}
            >
                {isGenerating ? "Generating..." : "Generate Tutorial"}
                {selectedFiles.length === 0 && !isGenerating && (
                    <span className="text-xs block text-gray-400">Select files first</span>
                )}
            </InteractiveHoverButton>
        </div>
    )
}