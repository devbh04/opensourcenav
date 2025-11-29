import { create } from 'zustand'

export type ResolutionRequest = {
  repo_url: string
  issue_url: string
  user_context: string
  include_related_issues: boolean
  difficulty_preference: 'simple' | 'detailed'
}

export type ResolutionStep = {
  step_number: number
  title: string
  description: string
  commands: string[]
  code_changes: string[]
  files_to_check: string[]
  estimated_time: string
  difficulty: 'easy' | 'medium' | 'hard'
  prerequisites: string[]
}

export type IssueDetails = {
  number: number
  title: string
  body: string
  state: string
  labels: string[]
  assignees: string[]
  author: string
  created_at: string
  updated_at: string
  comments_count: number
  html_url: string
}

export type RepositoryAnalysis = {
  tech_stack: string[]
  main_directories: string[]
  key_files: string[]
  testing_setup: string
  build_system: string
  documentation_quality: string
  contributor_guidelines: string
}

export type ResolutionResponse = {
  issue_details: IssueDetails
  repository_analysis: RepositoryAnalysis
  resolution_summary: string
  resolution_steps: ResolutionStep[]
  alternative_approaches: string[]
  related_issues: string[]
  helpful_resources: string[]
  estimated_total_time: string
  difficulty_level: string
  skills_required: string[]
  context_used: Record<string, any>
  execution_time: number
}

type ResolutionStore = {
  request: ResolutionRequest
  response: ResolutionResponse | null
  comprehensiveResponse: string | null
  isLoading: boolean
  isLoadingComprehensive: boolean
  error: string | null
  
  // Actions
  setRepoUrl: (url: string) => void
  setIssueUrl: (url: string) => void
  setUserContext: (context: string) => void
  setIncludeRelatedIssues: (include: boolean) => void
  setDifficultyPreference: (preference: 'simple' | 'detailed') => void
  fetchResolution: () => Promise<void>
  fetchComprehensiveResolution: () => Promise<void>
  clearResolution: () => void
  setError: (error: string | null) => void
}

export const useResolutionStore = create<ResolutionStore>((set, get) => ({
  request: {
    repo_url: '',
    issue_url: '',
    user_context: '',
    include_related_issues: true,
    difficulty_preference: 'detailed'
  },
  response: null,
  comprehensiveResponse: null,
  isLoading: false,
  isLoadingComprehensive: false,
  error: null,
  
  setRepoUrl: (url) => set((state) => ({ 
    request: { ...state.request, repo_url: url }
  })),
  
  setIssueUrl: (url) => set((state) => ({ 
    request: { ...state.request, issue_url: url }
  })),
  
  setUserContext: (context) => set((state) => ({ 
    request: { ...state.request, user_context: context }
  })),
  
  setIncludeRelatedIssues: (include) => set((state) => ({ 
    request: { ...state.request, include_related_issues: include }
  })),
  
  setDifficultyPreference: (preference) => set((state) => ({ 
    request: { ...state.request, difficulty_preference: preference }
  })),
  
  fetchResolution: async () => {
    const { request } = get()
    
    if (!request.repo_url || !request.issue_url) {
      set({ error: 'Repository URL and Issue URL are required' })
      return
    }
    
    set({ isLoading: true, error: null })
    
    try {
      const response = await fetch('http://localhost:8000/resolve-issue', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
      })
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      const data = await response.json()
      set({ response: data, isLoading: false })
    } catch (error) {
      console.error('Error fetching resolution:', error)
      set({ 
        error: error instanceof Error ? error.message : 'Failed to fetch resolution',
        isLoading: false 
      })
    }
  },

  fetchComprehensiveResolution: async () => {
    const { request } = get()
    
    if (!request.repo_url || !request.issue_url) {
      set({ error: 'Repository URL and Issue URL are required' })
      return
    }
    
    set({ isLoadingComprehensive: true, error: null })
    
    try {
      const response = await fetch('http://localhost:8000/resolve-issue-comprehensive', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
      })
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      const data = await response.json() // Parse as JSON instead of text
      // Extract the resolution_markdown from the response
      const markdownContent = data.resolution_markdown || 'No resolution content available'
      set({ comprehensiveResponse: markdownContent, isLoadingComprehensive: false })
    } catch (error) {
      console.error('Error fetching comprehensive resolution:', error)
      set({ 
        error: error instanceof Error ? error.message : 'Failed to fetch comprehensive resolution',
        isLoadingComprehensive: false 
      })
    }
  },
  
  clearResolution: () => set({ 
    response: null, 
    comprehensiveResponse: null,
    error: null,
    request: {
      repo_url: '',
      issue_url: '',
      user_context: '',
      include_related_issues: true,
      difficulty_preference: 'detailed'
    }
  }),
  
  setError: (error) => set({ error })
}))
