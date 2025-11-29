import { create } from 'zustand'

export type Repository = {
  id: number
  full_name: string
  description: string
  html_url: string
  stargazers_count: number
  forks_count: number
  language: string
  topics: string[]
  created_at: string
  updated_at: string
  pushed_at: string
  license: string
  personalized_score: number
  relevance_reasons: string[]
  learning_level: string
  contributor_count: number
  has_good_first_issues: boolean
  good_first_issue_count: number
  activity_score: number
}

export type RecommendationRequest = {
  selected_tech: string[]
  primary_language: string
  experience_level: string
  min_stars: number
  max_stars: number
  min_forks: number
  activity_preference: string
  license_preferences: string[]
  contribution_types: string[]
  issue_complexity: string
  learning_style: string
  github_username: string
  current_skills: string[]
  wanted_skills: string[]
}

export type RecommendationResponse = {
  repositories: Repository[]
  total_found: number
  search_strategies_used: string[]
  personalization_factors: Record<string, any>
  cache_info: Record<string, any>
}

interface RepositoryStore {
  // State
  repositories: Repository[]
  isLoading: boolean
  error: string | null
  filters: RecommendationRequest
  
  // Input states
  techInput: string
  skillInput: string
  
  // Actions
  setRepositories: (repositories: Repository[]) => void
  setLoading: (loading: boolean) => void
  setError: (error: string | null) => void
  setFilters: (filters: Partial<RecommendationRequest>) => void
  resetFilters: () => void
  
  // Input actions
  setTechInput: (input: string) => void
  setSkillInput: (input: string) => void
  
  // Complex actions
  addTechnology: (tech: string) => void
  removeTechnology: (tech: string) => void
  addSkill: (skill: string, type: 'current' | 'wanted') => void
  removeSkill: (skill: string, type: 'current' | 'wanted') => void
  
  // API actions
  fetchRecommendations: () => Promise<void>
}

const defaultFilters: RecommendationRequest = {
  selected_tech: [],
  primary_language: "",
  experience_level: "intermediate",
  min_stars: 100,
  max_stars: 0,
  min_forks: 10,
  activity_preference: "active",
  license_preferences: [],
  contribution_types: [],
  issue_complexity: "medium",
  learning_style: "hands_on",
  github_username: "",
  current_skills: [],
  wanted_skills: []
}

export const useRepositoryStore = create<RepositoryStore>((set, get) => ({
  // Initial state
  repositories: [],
  isLoading: false,
  error: null,
  filters: defaultFilters,
  techInput: "",
  skillInput: "",
  
  // Basic setters
  setRepositories: (repositories) => set({ repositories }),
  setLoading: (isLoading) => set({ isLoading }),
  setError: (error) => set({ error }),
  setFilters: (newFilters) => set((state) => ({ 
    filters: { ...state.filters, ...newFilters } 
  })),
  resetFilters: () => set({ filters: defaultFilters }),
  
  // Input setters
  setTechInput: (techInput) => set({ techInput }),
  setSkillInput: (skillInput) => set({ skillInput }),
  
  // Technology management
  addTechnology: (tech) => {
    const { filters, techInput } = get()
    if (tech.trim() && !filters.selected_tech.includes(tech.trim())) {
      set({
        filters: {
          ...filters,
          selected_tech: [...filters.selected_tech, tech.trim()]
        },
        techInput: ""
      })
    }
  },
  
  removeTechnology: (tech) => {
    const { filters } = get()
    set({
      filters: {
        ...filters,
        selected_tech: filters.selected_tech.filter(t => t !== tech)
      }
    })
  },
  
  // Skill management
  addSkill: (skill, type) => {
    const { filters } = get()
    if (skill.trim()) {
      const skillArray = type === 'current' ? filters.current_skills : filters.wanted_skills
      if (!skillArray.includes(skill.trim())) {
        set({
          filters: {
            ...filters,
            [type === 'current' ? 'current_skills' : 'wanted_skills']: [...skillArray, skill.trim()]
          },
          skillInput: ""
        })
      }
    }
  },
  
  removeSkill: (skill, type) => {
    const { filters } = get()
    set({
      filters: {
        ...filters,
        [type === 'current' ? 'current_skills' : 'wanted_skills']: 
          (type === 'current' ? filters.current_skills : filters.wanted_skills).filter(s => s !== skill)
      }
    })
  },
  
  // API call
  fetchRecommendations: async () => {
    const { filters } = get()
    set({ isLoading: true, error: null })
    
    try {
      console.log('Sending request with filters:', filters)
      
      const response = await fetch('http://localhost:8000/git-helper/intelligent-recommendations', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(filters),
      })

      console.log('Response status:', response.status)
      
      if (!response.ok) {
        const errorText = await response.text()
        console.error('Error response:', errorText)
        throw new Error(`HTTP error! status: ${response.status}. ${errorText}`)
      }

      const data: RecommendationResponse = await response.json()
      console.log('Response data:', data)
      set({ repositories: data.repositories || [] })
    } catch (error) {
      console.error('Error fetching recommendations:', error)
      set({ error: error instanceof Error ? error.message : 'Failed to fetch recommendations' })
    } finally {
      set({ isLoading: false })
    }
  }
}))
