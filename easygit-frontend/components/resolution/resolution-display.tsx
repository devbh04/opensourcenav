import * as React from "react"
import { useResolutionStore } from "@/store/resolution-store"
import { MarkdownRenderer } from "@/components/tutorial/markdown-renderer"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { 
  Clock, 
  Star, 
  Code, 
  FileText, 
  ExternalLink, 
  CheckCircle,
  AlertCircle,
  Info,
  GitBranch,
  Terminal,
  Folder
} from "lucide-react"

export function ResolutionDisplay() {
  const { response, comprehensiveResponse, isLoading, isLoadingComprehensive } = useResolutionStore()

  if (isLoading || isLoadingComprehensive) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <p className="text-gray-400">
            {isLoading ? "Generating resolution steps..." : "Generating comprehensive detailed resolution..."}
          </p>
        </div>
      </div>
    )
  }

  if (!response && !comprehensiveResponse) {
    return (
      <div className="text-center py-12 text-gray-400">
        <Info className="w-12 h-12 mx-auto mb-4 text-gray-500" />
        <p>Submit the form above to get AI-powered resolution steps for your issue.</p>
      </div>
    )
  }

  const getDifficultyColor = (difficulty: string) => {
    switch (difficulty.toLowerCase()) {
      case 'easy': return 'bg-green-500 text-white'
      case 'medium': return 'bg-yellow-500 text-black'
      case 'hard': return 'bg-red-500 text-white'
      default: return 'bg-gray-500 text-white'
    }
  }

  return (
    <div className="space-y-8">
      {/* Show Comprehensive Response if available */}
      {comprehensiveResponse && (
        <div className="bg-gray-800/30 rounded-lg border border-gray-700 p-6">
          <h3 className="text-xl font-semibold text-white mb-6 flex items-center">
            <CheckCircle className="w-5 h-5 mr-2 text-purple-500" />
            Comprehensive Detailed Resolution
          </h3>
          <div className="prose prose-slate prose-invert max-w-none">
            <MarkdownRenderer content={comprehensiveResponse} />
          </div>
        </div>
      )}

      {/* Show Regular Response if available */}
      {response && (
        <>
          {/* Issue Details Header */}
          <div className="bg-gray-800/30 rounded-lg border border-gray-700 p-6">
            <div className="flex items-start justify-between mb-4">
              <div className="flex-1">
                <h2 className="text-2xl font-bold text-white mb-2">
                  {response.issue_details.title}
                </h2>
                <div className="flex items-center space-x-4 text-sm text-gray-400">
                  <span>#{response.issue_details.number}</span>
                  <span>by {response.issue_details.author}</span>
                  <span>{new Date(response.issue_details.created_at).toLocaleDateString()}</span>
                  <Badge variant={response.issue_details.state === 'open' ? 'default' : 'secondary'}>
                    {response.issue_details.state}
                  </Badge>
                </div>
              </div>
              <Button
                variant="outline"
                size="sm"
                onClick={() => window.open(response.issue_details.html_url, '_blank')}
                className="bg-gray-700 hover:bg-gray-600 border-gray-600 text-gray-200"
              >
                <ExternalLink className="w-4 h-4 mr-2" />
                View on GitHub
              </Button>
            </div>
            
            {/* Labels */}
            {response.issue_details.labels.length > 0 && (
              <div className="flex flex-wrap gap-2 mb-4">
                {response.issue_details.labels.map((label) => (
                  <Badge key={label} variant="outline" className="text-xs">
                    {label}
                  </Badge>
                ))}
              </div>
            )}

            {/* Resolution Summary */}
            <div className="bg-gray-900/50 rounded-lg p-4 border border-gray-700">
              <h3 className="font-semibold text-white mb-2 flex items-center">
                <CheckCircle className="w-5 h-5 mr-2 text-green-500" />
                Resolution Summary
              </h3>
              <MarkdownRenderer content={response.resolution_summary} />
            </div>
          </div>

          {/* Quick Info Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-gray-800/30 rounded-lg border border-gray-700 p-4">
              <div className="flex items-center text-blue-400 mb-2">
                <Clock className="w-5 h-5 mr-2" />
                <span className="font-medium">Estimated Time</span>
              </div>
              <p className="text-white text-lg font-semibold">{response.estimated_total_time}</p>
            </div>
            
            <div className="bg-gray-800/30 rounded-lg border border-gray-700 p-4">
              <div className="flex items-center text-yellow-400 mb-2">
                <Star className="w-5 h-5 mr-2" />
                <span className="font-medium">Difficulty Level</span>
              </div>
              <Badge className={getDifficultyColor(response.difficulty_level)}>
                {response.difficulty_level}
              </Badge>
            </div>
            
            <div className="bg-gray-800/30 rounded-lg border border-gray-700 p-4">
              <div className="flex items-center text-purple-400 mb-2">
                <Code className="w-5 h-5 mr-2" />
                <span className="font-medium">Skills Required</span>
              </div>
              <div className="flex flex-wrap gap-1">
                {response.skills_required.slice(0, 3).map((skill) => (
                  <Badge key={skill} variant="outline" className="text-xs">
                    {skill}
                  </Badge>
                ))}
                {response.skills_required.length > 3 && (
                  <span className="text-xs text-gray-500">+{response.skills_required.length - 3}</span>
                )}
              </div>
            </div>
          </div>

          {/* Repository Analysis */}
          <div className="bg-gray-800/30 rounded-lg border border-gray-700 p-6">
            <h3 className="text-xl font-semibold text-white mb-4 flex items-center">
              <Folder className="w-5 h-5 mr-2" />
              Repository Analysis
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <h4 className="font-medium text-gray-200 mb-2">Tech Stack</h4>
                <div className="flex flex-wrap gap-1 mb-4">
                  {response.repository_analysis.tech_stack.map((tech) => (
                    <Badge key={tech} variant="outline" className="text-xs">
                      {tech}
                    </Badge>
                  ))}
                </div>
              </div>
              
              <div>
                <h4 className="font-medium text-gray-200 mb-2">Build System</h4>
                <p className="text-gray-400 text-sm">{response.repository_analysis.build_system}</p>
              </div>
              
              <div>
                <h4 className="font-medium text-gray-200 mb-2">Testing Setup</h4>
                <p className="text-gray-400 text-sm">{response.repository_analysis.testing_setup}</p>
              </div>
              
              <div>
                <h4 className="font-medium text-gray-200 mb-2">Documentation Quality</h4>
                <p className="text-gray-400 text-sm">{response.repository_analysis.documentation_quality}</p>
              </div>
            </div>
          </div>

          {/* Resolution Steps */}
          <div className="bg-gray-800/30 rounded-lg border border-gray-700 p-6">
            <h3 className="text-xl font-semibold text-white mb-6 flex items-center">
              <CheckCircle className="w-5 h-5 mr-2 text-green-500" />
              Step-by-Step Resolution
            </h3>
            
            <div className="space-y-6">
              {response.resolution_steps.map((step, index) => (
                <div key={step.step_number} className="relative">
                  {/* Step connector line */}
                  {index < response.resolution_steps.length - 1 && (
                    <div className="absolute left-4 top-10 w-0.5 h-full bg-gray-600 -z-10"></div>
                  )}
                  
                  <div className="flex items-start space-x-4">
                    <div className="flex-shrink-0 w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center text-white font-semibold text-sm">
                      {step.step_number}
                    </div>
                    
                    <div className="flex-1 bg-gray-900/50 rounded-lg p-4 border border-gray-700">
                      <div className="flex items-center justify-between mb-3">
                        <h4 className="font-semibold text-white">{step.title}</h4>
                        <div className="flex items-center space-x-2">
                          <Badge className={getDifficultyColor(step.difficulty)}>
                            {step.difficulty}
                          </Badge>
                          <Badge variant="outline">
                            <Clock className="w-3 h-3 mr-1" />
                            {step.estimated_time}
                          </Badge>
                        </div>
                      </div>
                      
                      <MarkdownRenderer content={step.description} />
                      
                      {step.commands.length > 0 && (
                        <div className="mt-4">
                          <h5 className="font-medium text-gray-200 mb-2 flex items-center">
                            <Terminal className="w-4 h-4 mr-2" />
                            Commands
                          </h5>
                          <div className="bg-gray-800 rounded p-3 font-mono text-sm">
                            {step.commands.map((command, i) => (
                              <div key={i} className="text-green-400">
                                $ {command}
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                      
                      {step.code_changes.length > 0 && (
                        <div className="mt-4">
                          <h5 className="font-medium text-gray-200 mb-2 flex items-center">
                            <Code className="w-4 h-4 mr-2" />
                            Code Changes
                          </h5>
                          <div className="space-y-2">
                            {step.code_changes.map((change, i) => (
                              <MarkdownRenderer key={i} content={change} />
                            ))}
                          </div>
                        </div>
                      )}
                      
                      {step.files_to_check.length > 0 && (
                        <div className="mt-4">
                          <h5 className="font-medium text-gray-200 mb-2 flex items-center">
                            <FileText className="w-4 h-4 mr-2" />
                            Files to Check
                          </h5>
                          <div className="flex flex-wrap gap-1">
                            {step.files_to_check.map((file) => (
                              <Badge key={file} variant="outline" className="text-xs font-mono">
                                {file}
                              </Badge>
                            ))}
                          </div>
                        </div>
                      )}
                      
                      {step.prerequisites.length > 0 && (
                        <div className="mt-4">
                          <h5 className="font-medium text-gray-200 mb-2 flex items-center">
                            <AlertCircle className="w-4 h-4 mr-2" />
                            Prerequisites
                          </h5>
                          <ul className="list-disc list-inside text-gray-400 text-sm">
                            {step.prerequisites.map((prereq, i) => (
                              <li key={i}>{prereq}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Alternative Approaches */}
          {response.alternative_approaches.length > 0 && (
            <div className="bg-gray-800/30 rounded-lg border border-gray-700 p-6">
              <h3 className="text-xl font-semibold text-white mb-4 flex items-center">
                <GitBranch className="w-5 h-5 mr-2" />
                Alternative Approaches
              </h3>
              <div className="space-y-4">
                {response.alternative_approaches.map((approach, index) => (
                  <div key={index} className="bg-gray-900/50 rounded-lg p-4 border border-gray-700">
                    <MarkdownRenderer content={approach} />
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Helpful Resources */}
          {response.helpful_resources.length > 0 && (
            <div className="bg-gray-800/30 rounded-lg border border-gray-700 p-6">
              <h3 className="text-xl font-semibold text-white mb-4 flex items-center">
                <ExternalLink className="w-5 h-5 mr-2" />
                Helpful Resources
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {response.helpful_resources.map((resource, index) => (
                  <a
                    key={index}
                    href={resource}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="block p-3 bg-gray-900/50 rounded border border-gray-700 hover:border-gray-600 transition-colors"
                  >
                    <div className="flex items-center text-blue-400 hover:text-blue-300">
                      <ExternalLink className="w-4 h-4 mr-2" />
                      <span className="text-sm truncate">{resource}</span>
                    </div>
                  </a>
                ))}
              </div>
            </div>
          )}

          {/* Related Issues */}
          {response.related_issues.length > 0 && (
            <div className="bg-gray-800/30 rounded-lg border border-gray-700 p-6">
              <h3 className="text-xl font-semibold text-white mb-4 flex items-center">
                <GitBranch className="w-5 h-5 mr-2" />
                Related Issues
              </h3>
              <div className="space-y-2">
                {response.related_issues.map((issue, index) => (
                  <div key={index} className="text-gray-400 text-sm">
                    {issue}
                  </div>
                ))}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  )
}
