import { create } from 'zustand'

export type IssueLabel = {
  name: string
  color: string
}

export type IssueUser = {
  login: string
}

export type Issue = {
  id: number
  title: string
  body: string
  html_url: string
  state: string
  created_at: string
  user: IssueUser
  labels: IssueLabel[]
}

export type IssueRepository = {
  owner: string
  repo: string
  fullName: string
}

export type IssueRequest = {
  repoUrl: string
  state: "open" | "closed" | "all"
  perPage: number
  page: number
  difficulty: "all" | "beginner" | "intermediate" | "advanced"
  userQuery: string
}

export type IssueResponse = {
  issues: Issue[]
  totalCount: number
  repository: IssueRepository
  difficulty: string
  execution_time: number
}

type IssueStore = {
  issues: Issue[]
  totalCount: number
  repository: IssueRepository | null
  isLoading: boolean
  error: string | null
  request: IssueRequest
  
  // Actions
  setRepoUrl: (repoUrl: string) => void
  setState: (state: "open" | "closed" | "all") => void
  setPerPage: (perPage: number) => void
  setPage: (page: number) => void
  setDifficulty: (difficulty: "all" | "beginner" | "intermediate" | "advanced") => void
  setUserQuery: (userQuery: string) => void
  fetchIssues: () => Promise<void>
  clearIssues: () => void
}

export const useIssueStore = create<IssueStore>((set, get) => ({
  issues: [],
  totalCount: 0,
  repository: null,
  isLoading: false,
  error: null,
  request: {
    repoUrl: "",
    state: "open",
    perPage: 100,
    page: 1,
    difficulty: "all",
    userQuery: ""
  },

  setRepoUrl: (repoUrl) => set((state) => ({
    request: { ...state.request, repoUrl }
  })),

  setState: (issueState) => set((state) => ({
    request: { ...state.request, state: issueState }
  })),

  setPerPage: (perPage) => set((state) => ({
    request: { ...state.request, perPage }
  })),

  setPage: (page) => set((state) => ({
    request: { ...state.request, page }
  })),

  setDifficulty: (difficulty) => set((state) => ({
    request: { ...state.request, difficulty }
  })),

  setUserQuery: (userQuery) => set((state) => ({
    request: { ...state.request, userQuery }
  })),

  fetchIssues: async () => {
    const { request } = get()
    
    if (!request.repoUrl.trim()) {
      set({ error: "Repository URL is required" })
      return
    }

    set({ isLoading: true, error: null })

    try {
      const response = await fetch('http://localhost:8000/git-helper/issues', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
      })

      if (!response.ok) {
        throw new Error(`Failed to fetch issues: ${response.statusText}`)
      }

      const data: IssueResponse = await response.json()
      
      set({
        issues: data.issues,
        totalCount: data.totalCount,
        repository: data.repository,
        isLoading: false,
        error: null
      })
    } catch (error) {
      set({
        isLoading: false,
        error: error instanceof Error ? error.message : 'An unknown error occurred'
      })
    }
  },

  clearIssues: () => set({
    issues: [],
    totalCount: 0,
    repository: null,
    error: null
  })
}))
