# AnalyzeRelationships Node - Dependency and relationship analysis
from typing import List, Dict, Any

from app.utils.flow_engine import Node, NodeResult
from app.utils.llm_integration import call_llm, create_relationship_context, parse_yaml_response

class AnalyzeRelationships(Node):
    """
    Analyzes relationships and dependencies between abstractions
    to determine optimal learning sequences and chapter ordering
    """
    
    def __init__(self):
        super().__init__(
            name="AnalyzeRelationships",
            description="Analyze relationships and dependencies between abstractions"
        )
    
    def prep(self, shared: Dict[str, Any]) -> NodeResult:
        """Prepare abstractions data for relationship analysis"""
        try:
            abstractions = shared.get("abstractions", [])
            if not abstractions:
                return NodeResult(
                    success=False,
                    error="No abstractions available for relationship analysis"
                )
            
            project_name = shared.get("project_name", "Unknown Project")
            files = shared.get("files", [])
            
            # Create abstractions summary for analysis
            abstractions_summary = self._create_abstractions_summary(abstractions)
            
            # Create project context
            project_context = self._create_project_context(files, project_name)
            
            prep_data = {
                "abstractions": abstractions,
                "abstractions_summary": abstractions_summary,
                "project_context": project_context,
                "project_name": project_name,
                "total_abstractions": len(abstractions)
            }
            
            print(f"    🔗 Analyzing relationships between {len(abstractions)} abstractions")
            print(f"    📊 Project context: {len(project_context)} characters")
            
            return NodeResult(
                success=True,
                data=prep_data,
                metadata={
                    "abstractions_count": len(abstractions),
                    "context_size": len(project_context)
                }
            )
            
        except Exception as e:
            return NodeResult(
                success=False,
                error=f"Prep phase failed: {str(e)}"
            )
    
    def exec(self, prep_result: NodeResult) -> NodeResult:
        """Execute relationship analysis using LLM"""
        try:
            prep_data = prep_result.data
            abstractions_summary = prep_data["abstractions_summary"]
            project_context = prep_data["project_context"]
            project_name = prep_data["project_name"]
            abstractions = prep_data["abstractions"]
            
            # Create comprehensive relationship analysis prompt
            prompt = self._create_relationship_prompt(
                abstractions_summary, project_context, project_name
            )
            
            print(f"    🤖 Sending to LLM for relationship analysis...")
            
            # Call LLM with relationship context
            context = create_relationship_context()
            llm_response = call_llm(prompt, context)
            
            if not llm_response.success:
                return NodeResult(
                    success=False,
                    error=f"LLM call failed: {llm_response.error}"
                )
            
            print(f"    📝 LLM response received ({len(llm_response.content)} characters)")
            
            # Parse YAML response
            fallback_analysis = self._create_fallback_analysis(abstractions, project_name)
            analysis_result = parse_yaml_response(llm_response.content, fallback_analysis)
            
            if not analysis_result:
                print("    ⚠️  Using fallback analysis due to parsing issues")
                analysis_result = fallback_analysis
            
            # Validate and enhance the analysis
            validated_analysis = self._validate_analysis(analysis_result, abstractions)
            
            # Calculate analysis metrics
            relationships = validated_analysis.get("relationships", [])
            strong_relationships = [r for r in relationships if r.get("strength") == "Strong"]
            
            print(f"    ✅ Found {len(relationships)} relationships ({len(strong_relationships)} strong)")
            
            return NodeResult(
                success=True,
                data={
                    "analysis": validated_analysis,
                    "llm_response": llm_response.content,
                    "tokens_used": llm_response.tokens_used
                },
                metadata={
                    "total_relationships": len(relationships),
                    "strong_relationships": len(strong_relationships),
                    "llm_cached": llm_response.cached
                }
            )
            
        except Exception as e:
            return NodeResult(
                success=False,
                error=f"Execution failed: {str(e)}"
            )
    
    def post(self, shared: Dict[str, Any], prep_result: NodeResult, exec_result: NodeResult) -> NodeResult:
        """Update shared state with relationship analysis"""
        try:
            exec_data = exec_result.data
            analysis = exec_data["analysis"]
            
            # Update shared state
            shared["relationships"] = analysis
            
            # Add relationship metadata for downstream nodes
            relationships = analysis.get("relationships", [])
            shared["relationship_analysis"] = {
                "total_relationships": len(relationships),
                "strong_dependencies": len([r for r in relationships if r.get("strength") == "Strong"]),
                "prerequisite_chains": self._analyze_prerequisite_chains(relationships),
                "complexity_flow": self._analyze_complexity_flow(relationships, shared["abstractions"]),
                "tokens_used": exec_data.get("tokens_used", 0)
            }
            
            print(f"    📝 Updated shared state with relationship analysis")
            self._print_relationship_summary(analysis, shared["abstractions"])
            
            return NodeResult(
                success=True,
                data={"relationships_added": len(relationships)},
                metadata={
                    "summary": shared["relationship_analysis"]
                }
            )
            
        except Exception as e:
            return NodeResult(
                success=False,
                error=f"Post phase failed: {str(e)}"
            )
    
    def _create_abstractions_summary(self, abstractions: List[Dict[str, Any]]) -> str:
        """Create a structured summary of abstractions for analysis"""
        summary_parts = ["# Abstractions Summary", ""]
        
        for i, abstraction in enumerate(abstractions, 1):
            summary_parts.extend([
                f"## {i}. {abstraction['name']}",
                f"**Type**: {abstraction.get('type', 'Unknown')}",
                f"**Complexity**: {abstraction.get('complexity', 'Unknown')}",
                f"**Description**: {abstraction.get('description', 'No description')}",
                f"**Files**: {', '.join(abstraction.get('files_involved', []))}",
                f"**Key Concepts**: {', '.join(abstraction.get('key_concepts', []))}",
                f"**Current Prerequisites**: {', '.join(abstraction.get('prerequisites', []))}",
                ""
            ])
        
        return "\n".join(summary_parts)
    
    def _create_project_context(self, files: List[tuple], project_name: str) -> str:
        """Create project context for relationship analysis"""
        context_parts = [
            f"# {project_name} - Project Context",
            f"Total Files: {len(files)}",
            ""
        ]
        
        # Analyze technology stack
        tech_stack = self._analyze_tech_stack(files)
        if tech_stack:
            context_parts.extend([
                "## Technology Stack",
                ", ".join(tech_stack),
                ""
            ])
        
        # Analyze file organization
        directories = self._analyze_directory_structure(files)
        if directories:
            context_parts.extend([
                "## Project Structure",
                "Key directories and their purposes:",
            ])
            for directory, purpose in directories.items():
                context_parts.append(f"- {directory}: {purpose}")
            context_parts.append("")
        
        # Key file analysis
        important_files = self._identify_important_files(files)
        if important_files:
            context_parts.extend([
                "## Key Files",
            ])
            for filepath, analysis in important_files[:10]:  # Top 10
                context_parts.append(f"- {filepath}: {analysis}")
        
        return "\n".join(context_parts)
    
    def _analyze_tech_stack(self, files: List[tuple]) -> List[str]:
        """Analyze technology stack from file extensions and content"""
        tech_indicators = {
            '.py': 'Python',
            '.js': 'JavaScript',
            '.jsx': 'React',
            '.ts': 'TypeScript',
            '.tsx': 'React with TypeScript',
            '.java': 'Java',
            '.cpp': 'C++',
            '.c': 'C',
            '.html': 'HTML',
            '.css': 'CSS',
            '.scss': 'Sass/SCSS',
            '.php': 'PHP',
            '.rb': 'Ruby',
            '.go': 'Go',
            '.rs': 'Rust',
            '.swift': 'Swift',
            '.kt': 'Kotlin'
        }
        
        detected_tech = set()
        
        for filepath, content in files:
            # Check file extension
            for ext, tech in tech_indicators.items():
                if filepath.endswith(ext):
                    detected_tech.add(tech)
            
            # Check for framework indicators in content
            if any(keyword in content.lower() for keyword in ['import react', 'from react']):
                detected_tech.add('React')
            if any(keyword in content.lower() for keyword in ['import vue', 'from vue']):
                detected_tech.add('Vue.js')
            if any(keyword in content.lower() for keyword in ['@angular', 'angular/']):
                detected_tech.add('Angular')
            if any(keyword in content.lower() for keyword in ['flask', 'from flask']):
                detected_tech.add('Flask')
            if any(keyword in content.lower() for keyword in ['django', 'from django']):
                detected_tech.add('Django')
            if any(keyword in content.lower() for keyword in ['express', 'require("express")']):
                detected_tech.add('Express.js')
        
        return sorted(list(detected_tech))
    
    def _analyze_directory_structure(self, files: List[tuple]) -> Dict[str, str]:
        """Analyze directory structure and infer purposes"""
        directory_purposes = {
            'src': 'Source code',
            'lib': 'Library code',
            'app': 'Application code',
            'components': 'UI components',
            'utils': 'Utility functions',
            'helpers': 'Helper functions',
            'models': 'Data models',
            'views': 'View layer',
            'controllers': 'Controller layer',
            'services': 'Service layer',
            'api': 'API endpoints',
            'routes': 'Route definitions',
            'middleware': 'Middleware functions',
            'config': 'Configuration files',
            'tests': 'Test files',
            'docs': 'Documentation',
            'public': 'Public assets',
            'static': 'Static files',
            'assets': 'Asset files',
            'styles': 'Stylesheets',
            'css': 'CSS files',
            'js': 'JavaScript files',
            'images': 'Image files'
        }
        
        found_directories = {}
        
        for filepath, _ in files:
            parts = filepath.split('/')
            if len(parts) > 1:
                top_dir = parts[0]
                if top_dir in directory_purposes:
                    found_directories[top_dir] = directory_purposes[top_dir]
        
        return found_directories
    
    def _identify_important_files(self, files: List[tuple]) -> List[tuple]:
        """Identify and analyze important files"""
        important_files = []
        
        for filepath, content in files:
            importance_score = 0
            analysis_parts = []
            
            filename = filepath.split('/')[-1].lower()
            
            # Score based on filename
            if filename in ['main.py', 'app.py', 'index.js', 'app.js', 'main.js']:
                importance_score += 10
                analysis_parts.append("main entry point")
            
            if filename in ['config.py', 'settings.py', 'package.json', 'requirements.txt']:
                importance_score += 8
                analysis_parts.append("configuration file")
            
            if 'test' in filename:
                importance_score += 3
                analysis_parts.append("test file")
            
            # Score based on content
            lines = content.splitlines()
            for line in lines[:50]:  # Check first 50 lines
                if any(keyword in line.lower() for keyword in ['class ', 'def ', 'function']):
                    importance_score += 1
                if any(keyword in line.lower() for keyword in ['import', 'from', 'require']):
                    importance_score += 0.5
            
            if importance_score > 3:
                if not analysis_parts:
                    analysis_parts.append("contains core functionality")
                important_files.append((filepath, "; ".join(analysis_parts)))
        
        # Sort by importance and return top files
        return sorted(important_files, key=lambda x: len(x[1]), reverse=True)
    
    def _create_relationship_prompt(self, abstractions_summary: str, project_context: str, project_name: str) -> str:
        """Create comprehensive prompt for relationship analysis"""
        return f"""
**ROLE**: You are an expert instructional designer and software architect specializing in creating optimal learning pathways for technical concepts.

**TASK**: Analyze the relationships between abstractions in {project_name} to create a comprehensive understanding of dependencies, interactions, and optimal learning sequences.

**THINK STEP BY STEP**:
1. **Dependency Mapping**: Identify which abstractions depend on others (prerequisite relationships)
2. **Functional Relationships**: Map how abstractions work together in the system
3. **Learning Sequence**: Consider cognitive load and natural learning progression
4. **Interaction Patterns**: Identify common usage patterns and workflows
5. **Complexity Progression**: Ensure concepts build from simple to complex

**PROJECT CONTEXT**:
{project_context}

**ABSTRACTIONS TO ANALYZE**:
{abstractions_summary}

**OUTPUT FORMAT** (YAML only):
```yaml
project_summary: "A 2-3 sentence overview of the project's main purpose and architecture"

key_insights:
  - "Important insight about the project architecture"
  - "Key pattern or design principle used"
  - "Notable technology choice or implementation detail"

relationships:
  - from: "Exact name of source abstraction"
    to: "Exact name of target abstraction"
    type: "PREREQUISITE|USES|CONFIGURES|IMPLEMENTS|EXTENDS|COLLABORATES|WORKFLOW"
    description: "Clear explanation of how these abstractions relate"
    strength: "Strong|Medium|Weak"
    learning_impact: "How this relationship affects tutorial sequencing"
    example_interaction: "Specific example of how they work together"

learning_paths:
  foundation:
    - "abstraction name that should be learned first"
    - "next foundational concept"
  core:
    - "main functionality concepts"
    - "core feature abstractions"
  advanced:
    - "complex or specialized concepts"
    - "integration and optimization topics"
```

**RELATIONSHIP TYPES EXPLAINED**:
- **PREREQUISITE**: Must understand 'from' before 'to' (e.g., "Basic Components" before "State Management")
- **USES**: 'from' actively utilizes 'to' in its implementation
- **CONFIGURES**: 'from' sets up or configures 'to'
- **IMPLEMENTS**: 'from' is a concrete implementation of 'to'
- **EXTENDS**: 'from' builds upon or extends 'to'
- **COLLABORATES**: 'from' and 'to' work together as peers
- **WORKFLOW**: 'from' and 'to' are used together in common development tasks

**QUALITY CRITERIA**:
- Focus on relationships that impact learning order and understanding
- Prioritize strong dependencies that are essential for comprehension
- Consider practical development workflows and common usage patterns
- Ensure every abstraction has at least one connection (no orphans)
- Balance complexity progression from beginner to advanced concepts

**LEARNING PATH GUIDELINES**:
- **Foundation**: Concepts that don't depend on others, basic building blocks
- **Core**: Main functionality that builds on foundation concepts
- **Advanced**: Complex topics that require understanding of core concepts

**EXAMPLE GOOD RELATIONSHIP**:
```yaml
- from: "React Component State Management"
  to: "React Hook System"
  type: "USES"
  description: "State management relies heavily on React hooks like useState and useEffect"
  strength: "Strong"
  learning_impact: "Students must understand hooks before they can effectively manage component state"
  example_interaction: "Counter component uses useState hook to track and update count value"
```

**IMPORTANT**: Return ONLY the YAML format above. No other text, explanations, or markdown formatting.
"""
    
    def _create_fallback_analysis(self, abstractions: List[Dict[str, Any]], project_name: str) -> Dict[str, Any]:
        """Create fallback relationship analysis if LLM fails"""
        
        # Basic project summary
        abstraction_count = len(abstractions)
        complexity_distribution = {}
        for abstraction in abstractions:
            complexity = abstraction.get("complexity", "Intermediate")
            complexity_distribution[complexity] = complexity_distribution.get(complexity, 0) + 1
        
        project_summary = f"{project_name} contains {abstraction_count} key abstractions with complexity levels: {complexity_distribution}"
        
        # Create basic relationships based on complexity and dependencies
        relationships = []
        
        # Group abstractions by complexity
        beginner_abstractions = [a for a in abstractions if a.get("complexity") == "Beginner"]
        intermediate_abstractions = [a for a in abstractions if a.get("complexity") == "Intermediate"]
        advanced_abstractions = [a for a in abstractions if a.get("complexity") == "Advanced"]
        
        # Create prerequisite relationships: Beginner -> Intermediate -> Advanced
        for intermediate in intermediate_abstractions:
            if beginner_abstractions:
                relationships.append({
                    "from": beginner_abstractions[0]["name"],
                    "to": intermediate["name"],
                    "type": "PREREQUISITE",
                    "description": "Foundation concepts must be understood before intermediate topics",
                    "strength": "Medium",
                    "learning_impact": "Establishes necessary background knowledge",
                    "example_interaction": "Basic concepts provide context for more complex implementations"
                })
        
        for advanced in advanced_abstractions:
            if intermediate_abstractions:
                relationships.append({
                    "from": intermediate_abstractions[0]["name"],
                    "to": advanced["name"],
                    "type": "PREREQUISITE",
                    "description": "Core concepts must be mastered before advanced topics",
                    "strength": "Strong",
                    "learning_impact": "Ensures solid foundation before complex concepts",
                    "example_interaction": "Core functionality understanding enables advanced feature comprehension"
                })
        
        # Create collaboration relationships between abstractions of the same complexity
        for i in range(len(intermediate_abstractions) - 1):
            relationships.append({
                "from": intermediate_abstractions[i]["name"],
                "to": intermediate_abstractions[i + 1]["name"],
                "type": "COLLABORATES",
                "description": "These concepts work together in the system",
                "strength": "Medium",
                "learning_impact": "Understanding both concepts provides complete picture",
                "example_interaction": "Both concepts are used together in typical development tasks"
            })
        
        # Create learning paths
        learning_paths = {
            "foundation": [a["name"] for a in beginner_abstractions],
            "core": [a["name"] for a in intermediate_abstractions],
            "advanced": [a["name"] for a in advanced_abstractions]
        }
        
        # Ensure all sections have at least one item
        if not learning_paths["foundation"] and abstractions:
            learning_paths["foundation"] = [abstractions[0]["name"]]
        if not learning_paths["core"] and len(abstractions) > 1:
            learning_paths["core"] = [abstractions[1]["name"]]
        if not learning_paths["advanced"] and len(abstractions) > 2:
            learning_paths["advanced"] = [abstractions[-1]["name"]]
        
        return {
            "project_summary": project_summary,
            "key_insights": [
                f"Project has {abstraction_count} key abstractions",
                f"Complexity distribution: {complexity_distribution}",
                "Architecture follows standard patterns for maintainability"
            ],
            "relationships": relationships,
            "learning_paths": learning_paths
        }
    
    def _validate_analysis(self, analysis: Dict[str, Any], abstractions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate and enhance the relationship analysis"""
        if not analysis:
            return self._create_fallback_analysis(abstractions, "Unknown Project")
        
        # Get valid abstraction names
        valid_names = {a["name"] for a in abstractions}
        
        # Validate relationships
        relationships = analysis.get("relationships", [])
        validated_relationships = []
        
        for relationship in relationships:
            from_name = relationship.get("from", "")
            to_name = relationship.get("to", "")
            
            # Only include relationships where both abstractions exist
            if from_name in valid_names and to_name in valid_names:
                validated_relationship = {
                    "from": from_name,
                    "to": to_name,
                    "type": relationship.get("type", "COLLABORATES"),
                    "description": relationship.get("description", "These concepts are related"),
                    "strength": relationship.get("strength", "Medium"),
                    "learning_impact": relationship.get("learning_impact", "Understanding both concepts is beneficial"),
                    "example_interaction": relationship.get("example_interaction", "These concepts work together in the system")
                }
                validated_relationships.append(validated_relationship)
        
        # Ensure we have some relationships
        if not validated_relationships and len(abstractions) > 1:
            # Create minimal relationships
            for i in range(len(abstractions) - 1):
                validated_relationships.append({
                    "from": abstractions[i]["name"],
                    "to": abstractions[i + 1]["name"],
                    "type": "PREREQUISITE",
                    "description": "Sequential learning relationship",
                    "strength": "Medium",
                    "learning_impact": "Builds understanding progressively",
                    "example_interaction": "Previous concept provides foundation for next concept"
                })
        
        # Validate learning paths
        learning_paths = analysis.get("learning_paths", {})
        if not learning_paths:
            learning_paths = {
                "foundation": [abstractions[0]["name"]] if abstractions else [],
                "core": [a["name"] for a in abstractions[1:3]] if len(abstractions) > 1 else [],
                "advanced": [a["name"] for a in abstractions[3:]] if len(abstractions) > 3 else []
            }
        
        return {
            "project_summary": analysis.get("project_summary", "Software project with multiple technical abstractions"),
            "key_insights": analysis.get("key_insights", ["Project contains multiple interrelated components"]),
            "relationships": validated_relationships,
            "learning_paths": learning_paths
        }
    
    def _analyze_prerequisite_chains(self, relationships: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze prerequisite chains to understand learning dependencies"""
        prerequisite_relationships = [r for r in relationships if r.get("type") == "PREREQUISITE"]
        
        # Build dependency graph
        dependencies = {}
        for rel in prerequisite_relationships:
            from_concept = rel["from"]
            to_concept = rel["to"]
            
            if to_concept not in dependencies:
                dependencies[to_concept] = []
            dependencies[to_concept].append(from_concept)
        
        # Find concepts with no dependencies (starting points)
        all_concepts = set()
        for rel in relationships:
            all_concepts.add(rel["from"])
            all_concepts.add(rel["to"])
        
        starting_concepts = [concept for concept in all_concepts if concept not in dependencies]
        
        # Calculate maximum chain lengths
        max_chain_length = 0
        for concept in all_concepts:
            chain_length = self._calculate_chain_length(concept, dependencies)
            max_chain_length = max(max_chain_length, chain_length)
        
        return {
            "total_prerequisites": len(prerequisite_relationships),
            "starting_concepts": starting_concepts,
            "max_chain_length": max_chain_length,
            "dependency_count": len(dependencies)
        }
    
    def _calculate_chain_length(self, concept: str, dependencies: Dict[str, List[str]]) -> int:
        """Calculate the length of the longest prerequisite chain for a concept"""
        if concept not in dependencies:
            return 0
        
        max_length = 0
        for prerequisite in dependencies[concept]:
            length = 1 + self._calculate_chain_length(prerequisite, dependencies)
            max_length = max(max_length, length)
        
        return max_length
    
    def _analyze_complexity_flow(self, relationships: List[Dict[str, Any]], abstractions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze how complexity flows through the relationship graph"""
        complexity_map = {a["name"]: a.get("complexity", "Intermediate") for a in abstractions}
        
        complexity_transitions = {
            "Beginner_to_Intermediate": 0,
            "Intermediate_to_Advanced": 0,
            "Same_Level": 0,
            "Reverse_Flow": 0  # Advanced to Beginner (potentially problematic)
        }
        
        complexity_levels = {"Beginner": 1, "Intermediate": 2, "Advanced": 3}
        
        for rel in relationships:
            from_complexity = complexity_map.get(rel["from"], "Intermediate")
            to_complexity = complexity_map.get(rel["to"], "Intermediate")
            
            from_level = complexity_levels.get(from_complexity, 2)
            to_level = complexity_levels.get(to_complexity, 2)
            
            if from_level == to_level:
                complexity_transitions["Same_Level"] += 1
            elif from_level == 1 and to_level == 2:
                complexity_transitions["Beginner_to_Intermediate"] += 1
            elif from_level == 2 and to_level == 3:
                complexity_transitions["Intermediate_to_Advanced"] += 1
            elif from_level > to_level:
                complexity_transitions["Reverse_Flow"] += 1
        
        return complexity_transitions
    
    def _print_relationship_summary(self, analysis: Dict[str, Any], abstractions: List[Dict[str, Any]]):
        """Print a summary of the relationship analysis"""
        relationships = analysis.get("relationships", [])
        learning_paths = analysis.get("learning_paths", {})
        
        print(f"    📊 RELATIONSHIP ANALYSIS SUMMARY:")
        print(f"      • Total Relationships: {len(relationships)}")
        
        # Count by type
        type_counts = {}
        for rel in relationships:
            rel_type = rel.get("type", "Unknown")
            type_counts[rel_type] = type_counts.get(rel_type, 0) + 1
        print(f"      • Relationship Types: {type_counts}")
        
        # Count by strength
        strength_counts = {}
        for rel in relationships:
            strength = rel.get("strength", "Medium")
            strength_counts[strength] = strength_counts.get(strength, 0) + 1
        print(f"      • Relationship Strength: {strength_counts}")
        
        # Learning path summary
        foundation_count = len(learning_paths.get("foundation", []))
        core_count = len(learning_paths.get("core", []))
        advanced_count = len(learning_paths.get("advanced", []))
        
        print(f"      • Learning Path: {foundation_count} Foundation, {core_count} Core, {advanced_count} Advanced")
        
        # Show key relationships
        strong_relationships = [r for r in relationships if r.get("strength") == "Strong"]
        if strong_relationships:
            print(f"    🔗 Key Strong Relationships:")
            for rel in strong_relationships[:3]:  # Show top 3
                print(f"      • {rel['from']} → {rel['to']} ({rel['type']})")
        
        print(f"    📝 Project Summary: {analysis.get('project_summary', 'Analysis completed')[:100]}...")
