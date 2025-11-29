import { create } from 'zustand';
import { persist } from 'zustand/middleware';

// Define interfaces for repository data
export interface RepositoryMetadata {
  owner: string;
  repository: string;
  requestedRef: string;
  resolvedCommit: string;
  path: string;
  maxSize: string;
}

export interface FileTreeItem {
  name: string;
  path: string;
  type: 'file' | 'folder';
  size?: number;
  children?: FileTreeItem[];
}

export interface TutorialResponse {
  success?: boolean;
  message?: string;
  data?: any;
  tutorialId?: string;
  repositoryUrl?: string;
  generatedAt?: string;
}

interface TutorialState {
  // Existing URL and config
  url: string;
  setUrl: (url: string) => void;
  advConfig: boolean;
  setAdvConfig: (advConfig: boolean) => void;
  includeFileTypes: string;
  setIncludeFileTypes: (types: string) => void;
  excludeFileTypes: string;
  setExcludeFileTypes: (types: string) => void;
  selectedFiles: string[];
  addSelectedFile: (filePath: string) => void;
  removeSelectedFile: (filePath: string) => void;
  toggleSelectedFile: (filePath: string) => void;
  clearSelectedFiles: () => void;

  // New repository data
  repositoryMetadata: RepositoryMetadata | null;
  setRepositoryMetadata: (metadata: RepositoryMetadata | null) => void;
  fileTreeData: FileTreeItem[];
  setFileTreeData: (data: FileTreeItem[]) => void;
  
  // Loading and error states
  loading: boolean;
  setLoading: (loading: boolean) => void;
  error: string | null;
  setError: (error: string | null) => void;
  
  // Tutorial generation state
  isGenerating: boolean;
  setIsGenerating: (isGenerating: boolean) => void;
  tutorialResponse: TutorialResponse | null;
  setTutorialResponse: (response: TutorialResponse | null) => void;
  
  // Clear all data
  clearAll: () => void;
}

const useTutorialStore = create<TutorialState>()(
  persist(
    (set) => ({
      // Existing URL and config
      url: '',
      setUrl: (url: string) => set({ url }),
      advConfig: false,
      setAdvConfig: (advConfig: boolean) => set({ advConfig }),
      includeFileTypes: '"*.css", "*.py", "*.js", "*.jsx", "*.ts", "*.tsx", "*.go", "*.java", "*.pyi", "*.pyx", "*.c", "*.cc", "*.cpp", "*.h", "*.hpp", "*.cs", "*.php", "*.rb", "*.swift","*.kt", "*.scala", "*.sh", "*.bash", "*.zsh", "*.fish","*.md", "*.rst", "*.txt", "*.rs", "*.toml", "*.ini", "*.cfg", "*.conf","Dockerfile", "Makefile", "*.yaml", "*.yml", "*.json", "*.xml","requirements.txt", "package.json", "Cargo.toml", "go.mod", "pom.xml","*.sql", "*.graphql", "*.proto"',
      setIncludeFileTypes: (types: string) => set({ includeFileTypes: types }),
      excludeFileTypes: '"assets/*", "data/*", "examples/*", "images/*", "public/*", "static/*", ,"venv/*", ".venv/*", "env/*", ".env/*", "virtualenv/*","*test*", "tests/*", "test/*", "__test__/*", "spec/*","v1/*", "v2/*", "version/*", "dist/*", "build/*", "target/*", "out/*","experimental/*", "deprecated/*", "misc/*", "legacy/*", "archive/*",".git/*", ".github/*", ".gitlab/*", ".svn/*", ".hg/*",".next/*", ".vscode/*", ".idea/*", ".vs/*","obj/*", "bin/*", "node_modules/*", "bower_components/*", "vendor/*","*.log", "*.tmp", "*.temp", "*.cache", "*.bak", "*.swp", "*.swo","*.min.js", "*.min.css", "bundle.*", "*.bundle.*",".pytest_cache/*", "__pycache__/*", "*.pyc", "*.pyo", "*.pyd",".mypy_cache/*", ".coverage", "coverage/*","migrations/*", "locale/*", "locales/*", "i18n/*"',
      setExcludeFileTypes: (types: string) => set({ excludeFileTypes: types }),
      selectedFiles: [],
      addSelectedFile: (filePath: string) => set((state) => ({
        selectedFiles: [...state.selectedFiles, filePath]
      })),
      removeSelectedFile: (filePath: string) => set((state) => ({
        selectedFiles: state.selectedFiles.filter(file => file !== filePath)
      })),
      toggleSelectedFile: (filePath: string) => set((state) => ({
        selectedFiles: state.selectedFiles.includes(filePath)
          ? state.selectedFiles.filter(file => file !== filePath)
          : [...state.selectedFiles, filePath]
      })),
      clearSelectedFiles: () => set({ selectedFiles: [] }),

      // New repository data
      repositoryMetadata: null,
      setRepositoryMetadata: (metadata: RepositoryMetadata | null) => set({ repositoryMetadata: metadata }),
      fileTreeData: [],
      setFileTreeData: (data: FileTreeItem[]) => set({ fileTreeData: data }),
      
      // Loading and error states
      loading: false,
      setLoading: (loading: boolean) => set({ loading }),
      error: null,
      setError: (error: string | null) => set({ error }),
      
      // Tutorial generation state
      isGenerating: false,
      setIsGenerating: (isGenerating: boolean) => set({ isGenerating }),
      tutorialResponse: null,
      setTutorialResponse: (response: TutorialResponse | null) => set({ tutorialResponse: response }),
      
      // Clear all data
      clearAll: () => set({
        url: '',
        advConfig: false,
        selectedFiles: [],
        repositoryMetadata: null,
        fileTreeData: [],
        loading: false,
        error: null,
        isGenerating: false,
        tutorialResponse: null,
      }),
    }),
    {
      name: 'tutorial-storage', // unique name for localStorage key
      // Only persist certain fields to avoid storing large file tree data unnecessarily
      partialize: (state) => ({
        url: state.url,
        advConfig: state.advConfig,
        includeFileTypes: state.includeFileTypes,
        excludeFileTypes: state.excludeFileTypes,
        selectedFiles: state.selectedFiles,
        repositoryMetadata: state.repositoryMetadata,
        fileTreeData: state.fileTreeData, // Include file tree data for persistence
        tutorialResponse: state.tutorialResponse, // Include tutorial response for persistence
      }),
    }
  )
);

export default useTutorialStore;