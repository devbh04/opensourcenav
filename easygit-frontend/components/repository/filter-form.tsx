"use client"

import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Badge } from "@/components/ui/badge"
import { useRepositoryStore } from "@/store/repository-store"
import { Plus } from "lucide-react"

export function FilterForm() {
  const {
    filters,
    techInput,
    skillInput,
    setFilters,
    setTechInput,
    setSkillInput,
    addTechnology,
    removeTechnology,
    addSkill,
    removeSkill,
    fetchRecommendations,
    isLoading
  } = useRepositoryStore()

  return (
    <div className="bg-black  backdrop-blur-sm rounded-lg p-6 space-y-4 border border-gray-800">
      <h2 className="text-xl font-semibold mb-4">Filter Preferences</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {/* Technologies */}
        <div className="space-y-2">
          <label className="text-sm font-medium">Technologies</label>
          <div className="flex space-x-2 items-center">
            <Input
              placeholder="Add technology..."
              value={techInput}
              onChange={(e) => setTechInput(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && techInput.trim() && addTechnology(techInput)}
              className="bg-gray-800/50 border-gray-700 text-white placeholder-gray-400 focus:border-gray-600 focus:ring-gray-600"
            />
            <Button 
              onClick={() => techInput.trim() && addTechnology(techInput)} 
              variant="outline" 
              size="sm"
              className="bg-green-900 text-white"
            >
              <Plus className="" />
            </Button>
          </div>
          <div className="flex flex-wrap gap-2">
            {filters.selected_tech.map((tech) => (
              <Badge key={tech} variant="secondary" className="bg-blue-600 text-white">
                {tech}
                <button
                  onClick={() => removeTechnology(tech)}
                  className="ml-2 text-blue-200 hover:text-white"
                >
                  ×
                </button>
              </Badge>
            ))}
          </div>
        </div>

        {/* Primary Language */}
        <div className="space-y-2">
          <label className="text-sm font-medium">Primary Language</label>
          <Input
            placeholder="e.g., JavaScript, Python..."
            value={filters.primary_language}
            onChange={(e) => setFilters({ primary_language: e.target.value })}
            className="bg-gray-800/50 border-gray-700 text-white placeholder-gray-400 focus:border-gray-600 focus:ring-gray-600"
          />
        </div>

        {/* Experience Level */}
        <div className="space-y-2">
          <label className="text-sm font-medium">Experience Level</label>
          <Select value={filters.experience_level} onValueChange={(value) => setFilters({ experience_level: value })}>
            <SelectTrigger className="bg-gray-800 border-gray-700 text-gray-100">
              <SelectValue />
            </SelectTrigger>
            <SelectContent className="bg-gray-800 border-gray-700">
              <SelectItem value="beginner">Beginner</SelectItem>
              <SelectItem value="intermediate">Intermediate</SelectItem>
              <SelectItem value="advanced">Advanced</SelectItem>
              <SelectItem value="expert">Expert</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* Min Stars */}
        <div className="space-y-2">
          <label className="text-sm font-medium">Minimum Stars</label>
          <Input
            type="number"
            value={filters.min_stars}
            onChange={(e) => setFilters({ min_stars: parseInt(e.target.value) || 0 })}
            className="bg-gray-800/50 border-gray-700 text-white placeholder-gray-400 focus:border-gray-600 focus:ring-gray-600"
          />
        </div>

        {/* Max Stars */}
        <div className="space-y-2">
          <label className="text-sm font-medium">Maximum Stars (0 = no limit)</label>
          <Input
            type="number"
            value={filters.max_stars}
            onChange={(e) => setFilters({ max_stars: parseInt(e.target.value) || 0 })}
            className="bg-gray-800/50 border-gray-700 text-white placeholder-gray-400 focus:border-gray-600 focus:ring-gray-600"
          />
        </div>

        {/* Min Forks */}
        <div className="space-y-2">
          <label className="text-sm font-medium">Minimum Forks</label>
          <Input
            type="number"
            value={filters.min_forks}
            onChange={(e) => setFilters({ min_forks: parseInt(e.target.value) || 0 })}
            className="bg-gray-800/50 border-gray-700 text-white placeholder-gray-400 focus:border-gray-600 focus:ring-gray-600"
          />
        </div>

        {/* Activity Preference */}
        <div className="space-y-2">
          <label className="text-sm font-medium">Activity Preference</label>
          <Select value={filters.activity_preference} onValueChange={(value) => setFilters({ activity_preference: value })}>
            <SelectTrigger className="bg-gray-800 border-gray-700 text-gray-100">
              <SelectValue />
            </SelectTrigger>
            <SelectContent className="bg-gray-800 border-gray-700">
              <SelectItem value="very_active">Very Active</SelectItem>
              <SelectItem value="active">Active</SelectItem>
              <SelectItem value="moderate">Moderate</SelectItem>
              <SelectItem value="any">Any</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* Issue Complexity */}
        <div className="space-y-2">
          <label className="text-sm font-medium">Issue Complexity</label>
          <Select value={filters.issue_complexity} onValueChange={(value) => setFilters({ issue_complexity: value })}>
            <SelectTrigger className="bg-gray-800 border-gray-700 text-gray-100">
              <SelectValue />
            </SelectTrigger>
            <SelectContent className="bg-gray-800 border-gray-700">
              <SelectItem value="easy">Easy</SelectItem>
              <SelectItem value="medium">Medium</SelectItem>
              <SelectItem value="hard">Hard</SelectItem>
              <SelectItem value="any">Any</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* Learning Style */}
        <div className="space-y-2">
          <label className="text-sm font-medium">Learning Style</label>
          <Select value={filters.learning_style} onValueChange={(value) => setFilters({ learning_style: value })}>
            <SelectTrigger className="bg-gray-800 border-gray-700 text-gray-100">
              <SelectValue />
            </SelectTrigger>
            <SelectContent className="bg-gray-800 border-gray-700">
              <SelectItem value="hands_on">Hands On</SelectItem>
              <SelectItem value="reading">Reading Documentation</SelectItem>
              <SelectItem value="video">Video Tutorials</SelectItem>
              <SelectItem value="mentorship">Mentorship</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* GitHub Username */}
        <div className="space-y-2">
          <label className="text-sm font-medium">GitHub Username</label>
          <Input
            placeholder="Your GitHub username..."
            value={filters.github_username}
            onChange={(e) => setFilters({ github_username: e.target.value })}
            className="bg-gray-800/50 border-gray-700 text-white placeholder-gray-400 focus:border-gray-600 focus:ring-gray-600"
          />
        </div>
      </div>

      {/* Current Skills */}
      <div className="space-y-2">
        <label className="text-sm font-medium">Current Skills</label>
        <div className="flex space-x-2">
          <Input
            placeholder="Add current skill..."
            value={skillInput}
            onChange={(e) => setSkillInput(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && skillInput.trim() && addSkill(skillInput, 'current')}
            className="bg-gray-800/50 border-gray-700 text-white placeholder-gray-400 focus:border-gray-600 focus:ring-gray-600"
          />
          <Button 
            onClick={() => skillInput.trim() && addSkill(skillInput, 'current')} 
            variant="outline" 
            size="sm"
            className="bg-green-900 text-white"
          >
            Add Current
          </Button>
        </div>
        <div className="flex flex-wrap gap-2">
          {filters.current_skills.map((skill) => (
            <Badge key={skill} variant="secondary" className="bg-green-600 text-white">
              {skill}
              <button
                onClick={() => removeSkill(skill, 'current')}
                className="ml-2 text-green-200 hover:text-white"
              >
                ×
              </button>
            </Badge>
          ))}
        </div>
      </div>

      {/* Wanted Skills */}
      <div className="space-y-2">
        <label className="text-sm font-medium">Skills to Learn</label>
        <div className="flex space-x-2">
          <Input
            placeholder="Add skill to learn..."
            value={skillInput}
            onChange={(e) => setSkillInput(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && skillInput.trim() && addSkill(skillInput, 'wanted')}
            className="bg-gray-800/50 border-gray-700 text-white placeholder-gray-400 focus:border-gray-600 focus:ring-gray-600"
          />
          <Button 
            onClick={() => skillInput.trim() && addSkill(skillInput, 'wanted')} 
            variant="outline" 
            size="sm"
            className="bg-green-900 text-white"
          >
            Add Wanted
          </Button>
        </div>
        <div className="flex flex-wrap gap-2">
          {filters.wanted_skills.map((skill) => (
            <Badge key={skill} variant="secondary" className="bg-purple-600 text-white">
              {skill}
              <button
                onClick={() => removeSkill(skill, 'wanted')}
                className="ml-2 text-purple-200 hover:text-white"
              >
                ×
              </button>
            </Badge>
          ))}
        </div>
      </div>

      <div className="flex justify-end pt-4">
        <Button onClick={fetchRecommendations} disabled={isLoading} className="bg-blue-600 hover:blue-700">
          {isLoading ? "Loading..." : "Get Recommendations"}
        </Button>
      </div>
    </div>
  )
}
