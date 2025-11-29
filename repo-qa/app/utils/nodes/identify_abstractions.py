# IdentifyAbstractions Node - AI-powered abstraction identification
import os
from typing import List, Dict, Any, Tuple

from app.utils.flow_engine import Node, NodeResult
from app.utils.llm_integration import call_llm, create_abstraction_context, parse_yaml_response

class IdentifyAbstractions(Node):
    """
    Uses LLM to identify core technical abstractions in the codebase
    that will form the foundation of the tutorial structure
    """
    
    def __init__(self):
        super().__init__(
            name="IdentifyAbstractions",
            description="Identify core technical abstractions and concepts for tutorial structure"
        )
    
    def prep(self, shared: Dict[str, Any]) -> NodeResult:
        """Prepare code overview for abstraction identification"""
        try:
            files = shared.get("files", [])
            if not files:
                return NodeResult(
                    success=False,
                    error="No files available for abstraction identification"
                )
            
            project_name = shared.get("project_name", "Unknown Project")
            max_abstractions = shared.get("max_abstractions", 12)
            min_abstractions = shared.get("min_abstractions", 5)
            
            # Create structured code overview
            print(f"    📊 Analyzing {len(files)} files for abstractions...")
            code_overview = self._create_code_overview(files, project_name)
            
            # Calculate overview statistics
            overview_size = len(code_overview)
            estimated_tokens = overview_size // 4  # Rough estimate
            
            prep_data = {
                "code_overview": code_overview,
                "project_name": project_name,
                "max_abstractions": max_abstractions,
                "min_abstractions": min_abstractions,
                "total_files": len(files),
                "overview_size": overview_size
            }
            
            print(f"    📄 Code overview: {overview_size:,} characters")
            print(f"    🎯 Target abstractions: {min_abstractions}-{max_abstractions}")
            print(f"    🧮 Estimated tokens: ~{estimated_tokens:,}")
            
            return NodeResult(
                success=True,
                data=prep_data,
                metadata={
                    "files_analyzed": len(files),
                    "overview_size": overview_size,
                    "estimated_tokens": estimated_tokens
                }
            )
            
        except Exception as e:
            return NodeResult(
                success=False,
                error=f"Prep phase failed: {str(e)}"
            )
    
    def exec(self, prep_result: NodeResult) -> NodeResult:
        """Execute abstraction identification using LLM"""
        try:
            prep_data = prep_result.data
            code_overview = prep_data["code_overview"]
            project_name = prep_data["project_name"]
            max_abstractions = prep_data["max_abstractions"]
            min_abstractions = prep_data["min_abstractions"]
            
            # Create LLM prompt for abstraction identification
            prompt = self._create_abstraction_prompt(
                code_overview, project_name, max_abstractions, min_abstractions
            )
            
            print(f"    🤖 Sending to LLM for abstraction analysis...")
            
            # Call LLM with appropriate context
            context = create_abstraction_context()
            llm_response = call_llm(prompt, context)
            
            if not llm_response.success:
                return NodeResult(
                    success=False,
                    error=f"LLM call failed: {llm_response.error}"
                )
            
            print(f"    📝 LLM response received ({len(llm_response.content)} characters)")
            
            # Parse YAML response
            fallback_abstractions = self._create_fallback_abstractions(prep_data)
            abstractions = parse_yaml_response(llm_response.content, fallback_abstractions)
            
            if not abstractions or not isinstance(abstractions, list):
                print("    ⚠️  Using fallback abstractions due to parsing issues")
                abstractions = fallback_abstractions
            
            # Validate and enhance abstractions
            validated_abstractions = self._validate_abstractions(abstractions, prep_data)
            
            print(f"    ✅ Identified {len(validated_abstractions)} valid abstractions")
            
            return NodeResult(
                success=True,
                data={
                    "abstractions": validated_abstractions,
                    "llm_response": llm_response.content,
                    "tokens_used": llm_response.tokens_used
                },
                metadata={
                    "abstractions_count": len(validated_abstractions),
                    "llm_cached": llm_response.cached,
                    "complexity_distribution": self._analyze_complexity_distribution(validated_abstractions)
                }
            )
            
        except Exception as e:
            return NodeResult(
                success=False,
                error=f"Execution failed: {str(e)}"
            )
    
    def post(self, shared: Dict[str, Any], prep_result: NodeResult, exec_result: NodeResult) -> NodeResult:
        """Update shared state with identified abstractions"""
        try:
            exec_data = exec_result.data
            abstractions = exec_data["abstractions"]
            
            # Update shared state
            shared["abstractions"] = abstractions
            
            # Add metadata to shared state for downstream nodes
            shared["abstraction_analysis"] = {
                "total_abstractions": len(abstractions),
                "complexity_levels": self._get_complexity_counts(abstractions),
                "types_distribution": self._get_type_distribution(abstractions),
                "tokens_used": exec_data.get("tokens_used", 0)
            }
            
            print(f"    📝 Updated shared state with {len(abstractions)} abstractions")
            self._print_abstraction_summary(abstractions)
            
            return NodeResult(
                success=True,
                data={"abstractions_added": len(abstractions)},
                metadata={
                    "summary": shared["abstraction_analysis"]
                }
            )
            
        except Exception as e:
            return NodeResult(
                success=False,
                error=f"Post phase failed: {str(e)}"
            )
    
    def _create_code_overview(self, files: List[Tuple[str, str]], project_name: str) -> str:
        """Create a comprehensive but concise code overview"""
        
        # Analyze file structure
        file_tree = {}
        file_summaries = []
        total_lines = 0
        
        for filepath, content in files:
            # Build file tree
            parts = filepath.split('/')
            current = file_tree
            for part in parts[:-1]:
                if part not in current:
                    current[part] = {}
                current = current[part]
            current[parts[-1]] = len(content.splitlines())
            
            # Create file summary
            lines = content.splitlines()
            total_lines += len(lines)
            
            # Extract key information
            imports = [line.strip() for line in lines[:20] if self._is_import_line(line)]
            classes = [line.strip() for line in lines if self._is_class_definition(line)]
            functions = [line.strip() for line in lines if self._is_function_definition(line)]
            
            file_summary = {
                "path": filepath,
                "lines": len(lines),
                "imports": imports[:5],  # Top 5 imports
                "classes": classes[:3],  # Top 3 classes
                "functions": functions[:5]  # Top 5 functions
            }
            file_summaries.append(file_summary)
        
        # Sort files by importance (more classes/functions = more important)
        file_summaries.sort(
            key=lambda f: len(f["classes"]) * 3 + len(f["functions"]) * 2 + len(f["imports"]),
            reverse=True
        )
        
        # Create overview text
        overview_parts = [
            f"# {project_name} - Code Overview",
            f"Total Files: {len(files)}",
            f"Total Lines of Code: {total_lines:,}",
            "",
            "## Directory Structure",
            self._format_file_tree(file_tree),
            "",
            "## Key Files Analysis"
        ]
        
        # Add detailed analysis for top files
        for i, file_summary in enumerate(file_summaries[:15]):  # Top 15 files
            overview_parts.append(f"\n### {file_summary['path']} ({file_summary['lines']} lines)")
            
            if file_summary["imports"]:
                overview_parts.append(f"Key imports: {', '.join(file_summary['imports'])}")
            
            if file_summary["classes"]:
                overview_parts.append(f"Classes: {', '.join(file_summary['classes'])}")
            
            if file_summary["functions"]:
                overview_parts.append(f"Functions: {', '.join(file_summary['functions'])}")
        
        # Add file listing for remaining files
        if len(file_summaries) > 15:
            overview_parts.append(f"\n## Additional Files ({len(file_summaries) - 15} more)")
            for file_summary in file_summaries[15:]:
                overview_parts.append(f"- {file_summary['path']} ({file_summary['lines']} lines)")
        
        return "\n".join(overview_parts)
    
    def _format_file_tree(self, tree: Dict, indent: int = 0) -> str:
        """Format file tree structure"""
        lines = []
        for name, subtree in sorted(tree.items()):
            prefix = "  " * indent + "- "
            if isinstance(subtree, dict):
                lines.append(f"{prefix}{name}/")
                lines.append(self._format_file_tree(subtree, indent + 1))
            else:
                lines.append(f"{prefix}{name} ({subtree} lines)")
        return "\n".join(lines)
    
    def _is_import_line(self, line: str) -> bool:
        """Check if line is an import statement"""
        stripped = line.strip()
        return (
            stripped.startswith(('import ', 'from ', '#include', 'using ', 'const ', 'let ')) or
            'require(' in stripped or 'import(' in stripped
        )
    
    def _is_class_definition(self, line: str) -> bool:
        """Check if line is a class definition"""
        stripped = line.strip()
        return (
            stripped.startswith(('class ', 'interface ', 'enum ', 'struct ')) or
            ('class' in stripped and '{' in stripped)
        )
    
    def _is_function_definition(self, line: str) -> bool:
        """Check if line is a function definition"""
        stripped = line.strip()
        return (
            stripped.startswith(('def ', 'function ', 'async def', 'async function')) or
            ('(' in stripped and ')' in stripped and '{' in stripped and not stripped.startswith('//'))
        )
    
    def _create_abstraction_prompt(self, code_overview: str, project_name: str, 
                                 max_abstractions: int, min_abstractions: int) -> str:
        """Create comprehensive prompt for abstraction identification"""
        return f"""
**ROLE**: You are a senior software architect and technical educator with 15+ years of experience analyzing codebases and designing learning curricula for developers.

**TASK**: Analyze the {project_name} codebase to identify core technical abstractions that will form the foundation of an effective beginner-friendly tutorial.

**THINK STEP BY STEP**:
1. **Architectural Analysis**: Scan for overall architecture patterns (MVC, microservices, layered, etc.)
2. **Domain Identification**: Identify key functional domains and business logic areas
3. **Technical Stack Mapping**: Map the technology stack and framework usage patterns
4. **Dependency Analysis**: Understand how components depend on each other
5. **Learning Path Planning**: Consider what concepts build naturally on others

**PROJECT ANALYSIS**:
{code_overview}

**OUTPUT REQUIREMENTS**:
- Identify {min_abstractions}-{max_abstractions} key abstractions
- Focus on concepts that directly impact daily development work
- Balance complexity: 30% Beginner, 50% Intermediate, 20% Advanced
- Each abstraction should enable hands-on learning activities

**OUTPUT FORMAT** (YAML only):
```yaml
abstractions:
  - name: "Specific, descriptive name (not generic)"
    type: "Architecture|Feature|Workflow|Integration|Data|UI|API|Config"
    description: "Clear one-sentence explanation with beginner-friendly analogy"
    complexity: "Beginner|Intermediate|Advanced"
    files_involved:
      - "exact/file/path/from/overview"
      - "another/file/path"
    prerequisites: 
      - "name of other abstraction this depends on"
    learning_value: "Why understanding this concept matters for developers"
    hands_on_activity: "Specific practical exercise beginners can do"
    key_concepts:
      - "concept 1"
      - "concept 2"
```

**QUALITY CRITERIA**:
- **Specific Names**: Use "FastAPI Route Handler with Pydantic Validation" not "API Handler"
- **Clear Descriptions**: Include analogies like "works like a restaurant order system"
- **Practical Focus**: Each abstraction should have immediate practical application
- **Learning Progression**: Consider how concepts build on each other
- **Real Files**: Reference actual file paths from the overview

**EXAMPLES**:

**GOOD ABSTRACTION**:
```yaml
- name: "React Component State Management with Hooks"
  type: "Feature"
  description: "Manages component data that changes over time, like a digital scoreboard that updates automatically"
  complexity: "Intermediate"
  files_involved:
    - "src/components/Counter.jsx"
    - "src/hooks/useCounter.js"
  prerequisites:
    - "React Component Basics"
  learning_value: "Essential for creating interactive user interfaces - every React developer uses this daily"
  hands_on_activity: "Create a simple counter component and modify its state"
  key_concepts:
    - "useState hook"
    - "state updates"
    - "component re-rendering"
```

**POOR ABSTRACTION**:
```yaml
- name: "Components"
  type: "Feature"
  description: "The UI components"
  complexity: "Beginner"
  files_involved: ["various files"]
```

**IMPORTANT**: Return ONLY the YAML format above. No other text, explanations, or markdown formatting.
"""
    
    def _create_fallback_abstractions(self, prep_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create fallback abstractions if LLM fails"""
        project_name = prep_data["project_name"]
        files = prep_data.get("files", [])
        
        # Analyze file types to infer technology stack
        file_extensions = {}
        for filepath, _ in files:
            ext = os.path.splitext(filepath)[1]
            file_extensions[ext] = file_extensions.get(ext, 0) + 1
        
        fallback_abstractions = []
        
        # Core abstractions based on file analysis
        if any(ext in file_extensions for ext in ['.py']):
            fallback_abstractions.append({
                "name": f"{project_name} Python Application Structure",
                "type": "Architecture",
                "description": "The overall organization of Python modules and packages in the project",
                "complexity": "Beginner",
                "files_involved": [fp for fp, _ in files if fp.endswith('.py')][:3],
                "prerequisites": [],
                "learning_value": "Understanding project structure helps navigate and modify the codebase",
                "hands_on_activity": "Explore the main modules and understand their purposes",
                "key_concepts": ["modules", "packages", "imports"]
            })
        
        if any(ext in file_extensions for ext in ['.js', '.jsx', '.ts', '.tsx']):
            fallback_abstractions.append({
                "name": f"{project_name} JavaScript/TypeScript Components",
                "type": "Feature",
                "description": "Reusable JavaScript components that build the user interface",
                "complexity": "Intermediate",
                "files_involved": [fp for fp, _ in files if any(fp.endswith(ext) for ext in ['.js', '.jsx', '.ts', '.tsx'])][:3],
                "prerequisites": ["Project Structure"],
                "learning_value": "Components are the building blocks of modern web applications",
                "hands_on_activity": "Examine and modify an existing component",
                "key_concepts": ["components", "props", "state"]
            })
        
        # Add configuration abstraction
        config_files = [fp for fp, _ in files if any(keyword in fp.lower() for keyword in ['config', 'setting', '.env', 'package.json'])]
        if config_files:
            fallback_abstractions.append({
                "name": f"{project_name} Configuration Management",
                "type": "Config",
                "description": "System settings and configuration that control application behavior",
                "complexity": "Beginner",
                "files_involved": config_files[:2],
                "prerequisites": [],
                "learning_value": "Understanding configuration helps customize and deploy applications",
                "hands_on_activity": "Modify a configuration setting and observe the effect",
                "key_concepts": ["environment variables", "configuration files", "settings"]
            })
        
        return fallback_abstractions[:prep_data.get("max_abstractions", 12)]
    
    def _validate_abstractions(self, abstractions: List[Dict[str, Any]], prep_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Validate and enhance abstraction data"""
        if not abstractions:
            return self._create_fallback_abstractions(prep_data)
        
        validated = []
        files = prep_data.get("files", [])
        available_files = {fp for fp, _ in files}
        
        for i, abstraction in enumerate(abstractions):
            # Ensure required fields exist
            validated_abstraction = {
                "name": abstraction.get("name", f"Abstraction {i+1}"),
                "type": abstraction.get("type", "Feature"),
                "description": abstraction.get("description", "Core concept in the system"),
                "complexity": abstraction.get("complexity", "Intermediate"),
                "files_involved": [],
                "prerequisites": abstraction.get("prerequisites", []),
                "learning_value": abstraction.get("learning_value", "Important for understanding the system"),
                "hands_on_activity": abstraction.get("hands_on_activity", "Explore this concept in the code"),
                "key_concepts": abstraction.get("key_concepts", [])
            }
            
            # Validate files_involved
            files_involved = abstraction.get("files_involved", [])
            if isinstance(files_involved, list):
                # Filter to only include files that actually exist
                valid_files = [f for f in files_involved if f in available_files]
                if not valid_files and available_files:
                    # If no valid files, assign some relevant ones
                    valid_files = list(available_files)[:2]
                validated_abstraction["files_involved"] = valid_files
            
            validated.append(validated_abstraction)
        
        return validated
    
    def _analyze_complexity_distribution(self, abstractions: List[Dict[str, Any]]) -> Dict[str, int]:
        """Analyze the distribution of complexity levels"""
        distribution = {"Beginner": 0, "Intermediate": 0, "Advanced": 0}
        for abstraction in abstractions:
            complexity = abstraction.get("complexity", "Intermediate")
            if complexity in distribution:
                distribution[complexity] += 1
        return distribution
    
    def _get_complexity_counts(self, abstractions: List[Dict[str, Any]]) -> Dict[str, int]:
        """Get count of abstractions by complexity level"""
        return self._analyze_complexity_distribution(abstractions)
    
    def _get_type_distribution(self, abstractions: List[Dict[str, Any]]) -> Dict[str, int]:
        """Get count of abstractions by type"""
        distribution = {}
        for abstraction in abstractions:
            abs_type = abstraction.get("type", "Feature")
            distribution[abs_type] = distribution.get(abs_type, 0) + 1
        return distribution
    
    def _print_abstraction_summary(self, abstractions: List[Dict[str, Any]]):
        """Print a summary of identified abstractions"""
        print(f"    📋 ABSTRACTION SUMMARY:")
        
        complexity_counts = self._get_complexity_counts(abstractions)
        type_counts = self._get_type_distribution(abstractions)
        
        print(f"      • Complexity: {complexity_counts}")
        print(f"      • Types: {type_counts}")
        
        print(f"    📝 Key Abstractions:")
        for i, abstraction in enumerate(abstractions[:5]):  # Show first 5
            name = abstraction["name"]
            complexity = abstraction["complexity"]
            abs_type = abstraction["type"]
            print(f"      {i+1}. {name} ({complexity} {abs_type})")
        
        if len(abstractions) > 5:
            print(f"      ... and {len(abstractions) - 5} more")
