# OrderChapters Node - Intelligent chapter sequencing for optimal learning
from typing import List, Dict, Any, Set, Tuple

from app.utils.flow_engine import Node, NodeResult
from app.utils.llm_integration import call_llm, create_ordering_context, parse_yaml_response

class OrderChapters(Node):
    """
    Determines optimal chapter sequence based on abstraction relationships,
    complexity progression, and pedagogical principles
    """
    
    def __init__(self):
        super().__init__(
            name="OrderChapters",
            description="Determine optimal chapter ordering based on dependencies and learning progression"
        )
    
    def prep(self, shared: Dict[str, Any]) -> NodeResult:
        """Prepare data for chapter ordering analysis"""
        try:
            abstractions = shared.get("abstractions", [])
            relationships = shared.get("relationships", {})
            
            if not abstractions:
                return NodeResult(
                    success=False,
                    error="No abstractions available for chapter ordering"
                )
            
            if not relationships:
                return NodeResult(
                    success=False,
                    error="No relationship analysis available for chapter ordering"
                )
            
            project_name = shared.get("project_name", "Unknown Project")
            
            # Create learning context
            learning_context = self._create_learning_context(abstractions, relationships)
            
            # Analyze dependency graph
            dependency_analysis = self._analyze_dependencies(abstractions, relationships)
            
            prep_data = {
                "abstractions": abstractions,
                "relationships": relationships,
                "project_name": project_name,
                "learning_context": learning_context,
                "dependency_analysis": dependency_analysis,
                "total_abstractions": len(abstractions)
            }
            
            print(f"    📚 Analyzing optimal sequence for {len(abstractions)} abstractions")
            print(f"    🔗 Using {len(relationships.get('relationships', []))} relationships")
            print(f"    🧠 Dependency chains: {dependency_analysis['max_chain_depth']} levels deep")
            
            return NodeResult(
                success=True,
                data=prep_data,
                metadata={
                    "abstractions_count": len(abstractions),
                    "relationships_count": len(relationships.get("relationships", [])),
                    "dependency_depth": dependency_analysis["max_chain_depth"]
                }
            )
            
        except Exception as e:
            return NodeResult(
                success=False,
                error=f"Prep phase failed: {str(e)}"
            )
    
    def exec(self, prep_result: NodeResult) -> NodeResult:
        """Execute chapter ordering using LLM with dependency analysis"""
        try:
            prep_data = prep_result.data
            abstractions = prep_data["abstractions"]
            relationships = prep_data["relationships"]
            learning_context = prep_data["learning_context"]
            dependency_analysis = prep_data["dependency_analysis"]
            project_name = prep_data["project_name"]
            
            # Create comprehensive ordering prompt
            prompt = self._create_ordering_prompt(
                abstractions, relationships, learning_context, dependency_analysis, project_name
            )
            
            print(f"    🤖 Sending to LLM for chapter sequencing...")
            
            # Call LLM with ordering context
            context = create_ordering_context()
            llm_response = call_llm(prompt, context)
            
            if not llm_response.success:
                return NodeResult(
                    success=False,
                    error=f"LLM call failed: {llm_response.error}"
                )
            
            print(f"    📝 LLM response received ({len(llm_response.content)} characters)")
            
            # Parse YAML response
            fallback_ordering = self._create_fallback_ordering(abstractions, dependency_analysis)
            ordering_result = parse_yaml_response(llm_response.content, fallback_ordering)
            
            if not ordering_result:
                print("    ⚠️  Using fallback ordering due to parsing issues")
                ordering_result = fallback_ordering
            
            # Validate and enhance the ordering
            validated_ordering = self._validate_ordering(ordering_result, abstractions, relationships)
            
            # Calculate ordering metrics
            chapters = validated_ordering.get("chapters", [])
            foundation_chapters = len([c for c in chapters if c.get("type") == "Foundation"])
            
            print(f"    ✅ Created {len(chapters)} chapters ({foundation_chapters} foundation chapters)")
            
            return NodeResult(
                success=True,
                data={
                    "chapter_order": validated_ordering,
                    "llm_response": llm_response.content,
                    "tokens_used": llm_response.tokens_used
                },
                metadata={
                    "total_chapters": len(chapters),
                    "foundation_chapters": foundation_chapters,
                    "llm_cached": llm_response.cached,
                    "ordering_quality": self._assess_ordering_quality(validated_ordering, dependency_analysis)
                }
            )
            
        except Exception as e:
            return NodeResult(
                success=False,
                error=f"Execution failed: {str(e)}"
            )
    
    def post(self, shared: Dict[str, Any], prep_result: NodeResult, exec_result: NodeResult) -> NodeResult:
        """Update shared state with chapter ordering"""
        try:
            exec_data = exec_result.data
            chapter_order = exec_data["chapter_order"]
            
            # Update shared state
            shared["chapter_order"] = chapter_order
            
            # Add ordering metadata for downstream nodes
            chapters = chapter_order.get("chapters", [])
            shared["chapter_analysis"] = {
                "total_chapters": len(chapters),
                "chapter_types": self._get_chapter_type_distribution(chapters),
                "estimated_duration": self._calculate_total_duration(chapters),
                "complexity_progression": self._analyze_complexity_progression(chapters),
                "tokens_used": exec_data.get("tokens_used", 0)
            }
            
            print(f"    📝 Updated shared state with {len(chapters)} ordered chapters")
            self._print_chapter_summary(chapter_order)
            
            return NodeResult(
                success=True,
                data={"chapters_ordered": len(chapters)},
                metadata={
                    "summary": shared["chapter_analysis"]
                }
            )
            
        except Exception as e:
            return NodeResult(
                success=False,
                error=f"Post phase failed: {str(e)}"
            )
    
    def _create_learning_context(self, abstractions: List[Dict[str, Any]], relationships: Dict[str, Any]) -> str:
        """Create comprehensive learning context for ordering"""
        context_parts = ["# Learning Context for Chapter Ordering", ""]
        
        # Abstraction complexity distribution
        complexity_dist = {}
        for abstraction in abstractions:
            complexity = abstraction.get("complexity", "Intermediate")
            complexity_dist[complexity] = complexity_dist.get(complexity, 0) + 1
        
        context_parts.extend([
            "## Complexity Distribution",
            f"- Beginner: {complexity_dist.get('Beginner', 0)} abstractions",
            f"- Intermediate: {complexity_dist.get('Intermediate', 0)} abstractions", 
            f"- Advanced: {complexity_dist.get('Advanced', 0)} abstractions",
            ""
        ])
        
        # Learning paths from relationship analysis
        learning_paths = relationships.get("learning_paths", {})
        if learning_paths:
            context_parts.extend([
                "## Suggested Learning Paths",
                f"Foundation concepts: {', '.join(learning_paths.get('foundation', []))}",
                f"Core concepts: {', '.join(learning_paths.get('core', []))}",
                f"Advanced concepts: {', '.join(learning_paths.get('advanced', []))}",
                ""
            ])
        
        # Key insights from project analysis
        key_insights = relationships.get("key_insights", [])
        if key_insights:
            context_parts.extend([
                "## Key Project Insights",
            ])
            for insight in key_insights:
                context_parts.append(f"- {insight}")
            context_parts.append("")
        
        # Relationship strength analysis
        relationship_list = relationships.get("relationships", [])
        strong_deps = [r for r in relationship_list if r.get("strength") == "Strong" and r.get("type") == "PREREQUISITE"]
        if strong_deps:
            context_parts.extend([
                "## Critical Dependencies (Must Be Respected)",
            ])
            for dep in strong_deps:
                context_parts.append(f"- {dep['from']} must come before {dep['to']}")
            context_parts.append("")
        
        return "\n".join(context_parts)
    
    def _analyze_dependencies(self, abstractions: List[Dict[str, Any]], relationships: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze dependency structure for ordering constraints"""
        relationship_list = relationships.get("relationships", [])
        
        # Build dependency graph
        dependencies = {}  # concept -> list of prerequisites
        dependents = {}    # concept -> list of concepts that depend on this
        
        for rel in relationship_list:
            if rel.get("type") == "PREREQUISITE":
                from_concept = rel["from"]
                to_concept = rel["to"]
                
                if to_concept not in dependencies:
                    dependencies[to_concept] = []
                dependencies[to_concept].append(from_concept)
                
                if from_concept not in dependents:
                    dependents[from_concept] = []
                dependents[from_concept].append(to_concept)
        
        # Find concepts with no prerequisites (starting points)
        all_concepts = {a["name"] for a in abstractions}
        starting_concepts = [concept for concept in all_concepts if concept not in dependencies]
        
        # Calculate dependency depth for each concept
        concept_depths = {}
        for concept in all_concepts:
            concept_depths[concept] = self._calculate_dependency_depth(concept, dependencies)
        
        max_chain_depth = max(concept_depths.values()) if concept_depths else 0
        
        # Group concepts by dependency level
        depth_groups = {}
        for concept, depth in concept_depths.items():
            if depth not in depth_groups:
                depth_groups[depth] = []
            depth_groups[depth].append(concept)
        
        return {
            "dependencies": dependencies,
            "dependents": dependents,
            "starting_concepts": starting_concepts,
            "concept_depths": concept_depths,
            "max_chain_depth": max_chain_depth,
            "depth_groups": depth_groups
        }
    
    def _calculate_dependency_depth(self, concept: str, dependencies: Dict[str, List[str]]) -> int:
        """Calculate the maximum depth of dependencies for a concept"""
        if concept not in dependencies:
            return 0
        
        max_depth = 0
        for prerequisite in dependencies[concept]:
            depth = 1 + self._calculate_dependency_depth(prerequisite, dependencies)
            max_depth = max(max_depth, depth)
        
        return max_depth
    
    def _create_ordering_prompt(self, abstractions: List[Dict[str, Any]], relationships: Dict[str, Any],
                              learning_context: str, dependency_analysis: Dict[str, Any], project_name: str) -> str:
        """Create comprehensive prompt for chapter ordering"""
        
        # Format abstractions for the prompt
        abstractions_text = ""
        for i, abstraction in enumerate(abstractions, 1):
            abstractions_text += f"""
{i}. **{abstraction['name']}**
   - Type: {abstraction.get('type', 'Unknown')}
   - Complexity: {abstraction.get('complexity', 'Intermediate')}
   - Description: {abstraction.get('description', 'No description')}
   - Files: {', '.join(abstraction.get('files_involved', []))}
   - Prerequisites: {', '.join(abstraction.get('prerequisites', []))}
   - Learning Value: {abstraction.get('learning_value', 'Important concept')}
   - Hands-on Activity: {abstraction.get('hands_on_activity', 'Explore the concept')}
"""
        
        # Format key relationships
        relationship_list = relationships.get("relationships", [])
        strong_relationships = [r for r in relationship_list if r.get("strength") == "Strong"]
        relationships_text = ""
        for rel in strong_relationships:
            relationships_text += f"- {rel['from']} → {rel['to']} ({rel['type']}): {rel['description']}\n"
        
        return f"""
**ROLE**: You are a master instructional designer and software education expert with expertise in cognitive learning theory, curriculum development, and technical training.

**TASK**: Design the optimal chapter sequence for a {project_name} tutorial that maximizes learning effectiveness through proper dependency ordering, complexity progression, and pedagogical best practices.

**THINK STEP BY STEP**:
1. **Dependency Analysis**: Respect all prerequisite relationships - never teach a concept before its dependencies
2. **Cognitive Load Management**: Progress from simple to complex, building confidence with early wins
3. **Practical Value**: Ensure each chapter provides immediate, actionable value to learners
4. **Flow and Motivation**: Create natural transitions and maintain learner engagement
5. **Hands-on Learning**: Every chapter should enable practical experimentation

**PROJECT CONTEXT**:
{learning_context}

**ABSTRACTIONS TO ORGANIZE**:
{abstractions_text}

**CRITICAL RELATIONSHIPS TO RESPECT**:
{relationships_text}

**DEPENDENCY CONSTRAINTS**:
- Maximum dependency chain depth: {dependency_analysis['max_chain_depth']}
- Starting concepts (no dependencies): {', '.join(dependency_analysis['starting_concepts'])}
- Concepts grouped by dependency level: {dependency_analysis['depth_groups']}

**OUTPUT FORMAT** (YAML only):
```yaml
tutorial_overview:
  title: "Engaging tutorial title that promises specific outcomes"
  description: "2-3 sentence description of what learners will accomplish"
  target_audience: "Specific description of intended learners"
  estimated_duration: "Total time estimate (e.g., '3-4 hours')"
  prerequisites: "What learners should know before starting"

chapters:
  - number: 1
    title: "Specific, outcome-focused chapter title"
    abstraction: "Exact abstraction name from the list above"
    type: "Foundation|Core|Application|Integration|Advanced"
    description: "What learners will accomplish in this chapter"
    objectives:
      - "After this chapter, you will be able to..."
      - "You will understand how to..."
    estimated_time: "15-45 minutes"
    complexity: "Beginner|Intermediate|Advanced"
    hands_on_activity: "Specific exercise learners will complete"
    success_criteria: "How learners know they've mastered this chapter"
    prerequisites: 
      - "chapter number that must come before this one"
    transitions:
      from_previous: "How this builds on the previous chapter"
      to_next: "How this prepares for the next chapter"
```

**PEDAGOGICAL PRINCIPLES**:
- **Start with Value**: Chapter 1 should provide immediate, practical value
- **Build Progressively**: Each chapter should build naturally on previous knowledge
- **Respect Dependencies**: Never introduce a concept before its prerequisites
- **Maintain Engagement**: Balance theory with practice throughout
- **Enable Success**: Ensure each chapter has clear, achievable outcomes
- **Create Flow**: Smooth transitions between chapters maintain momentum

**CHAPTER TYPE GUIDELINES**:
- **Foundation**: Essential concepts that everything else builds on (typically beginner)
- **Core**: Main functionality and patterns (typically intermediate)
- **Application**: Putting concepts together in real scenarios
- **Integration**: How components work together
- **Advanced**: Complex topics, optimization, and specialized use cases

**QUALITY CRITERIA**:
- Dependency order is strictly respected (no concept before its prerequisites)
- Complexity progression is smooth (avoid sudden difficulty spikes)
- Each chapter has clear learning objectives and success criteria
- Hands-on activities are specific and doable
- Transitions create a coherent learning narrative
- Total estimated time is reasonable for the scope

**EXAMPLE EXCELLENT CHAPTER**:
```yaml
- number: 1
  title: "Your First API Endpoint: From Request to Response"
  abstraction: "FastAPI Request/Response Pipeline"
  type: "Foundation"
  description: "Build and test a working API endpoint to understand the fundamental request/response cycle"
  objectives:
    - "After this chapter, you will be able to create a new API endpoint"
    - "You will understand how request validation and response formatting work"
  estimated_time: "25 minutes"
  complexity: "Beginner"
  hands_on_activity: "Create a /hello endpoint with input validation and test it with curl"
  success_criteria: "Successfully create, modify, and test a working API endpoint"
  prerequisites: []
  transitions:
    from_previous: "Starting point - no prerequisites"
    to_next: "Understanding basic endpoints prepares you for more complex data handling"
```

**IMPORTANT**: Return ONLY the YAML format above. No other text, explanations, or markdown formatting.
"""
    
    def _create_fallback_ordering(self, abstractions: List[Dict[str, Any]], dependency_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Create fallback chapter ordering if LLM fails"""
        
        # Use dependency analysis to create a logical ordering
        depth_groups = dependency_analysis["depth_groups"]
        ordered_abstractions = []
        
        # Order by dependency depth (0 first, then 1, 2, etc.)
        for depth in sorted(depth_groups.keys()):
            concepts_at_depth = depth_groups[depth]
            
            # Within each depth level, order by complexity
            depth_abstractions = [a for a in abstractions if a["name"] in concepts_at_depth]
            complexity_order = {"Beginner": 1, "Intermediate": 2, "Advanced": 3}
            depth_abstractions.sort(key=lambda a: complexity_order.get(a.get("complexity", "Intermediate"), 2))
            
            ordered_abstractions.extend(depth_abstractions)
        
        # Create chapters
        chapters = []
        for i, abstraction in enumerate(ordered_abstractions, 1):
            # Determine chapter type based on complexity and position
            if abstraction.get("complexity") == "Beginner" or i <= 2:
                chapter_type = "Foundation"
            elif abstraction.get("complexity") == "Advanced" or i > len(ordered_abstractions) * 0.8:
                chapter_type = "Advanced"
            else:
                chapter_type = "Core"
            
            # Calculate prerequisites (previous chapters that this depends on)
            prerequisites = []
            abstraction_deps = dependency_analysis["dependencies"].get(abstraction["name"], [])
            for j, prev_abstraction in enumerate(ordered_abstractions[:i-1], 1):
                if prev_abstraction["name"] in abstraction_deps:
                    prerequisites.append(j)
            
            chapter = {
                "number": i,
                "title": f"Understanding {abstraction['name']}",
                "abstraction": abstraction["name"],
                "type": chapter_type,
                "description": abstraction.get("description", "Learn about this important concept"),
                "objectives": [
                    f"After this chapter, you will understand {abstraction['name']}",
                    f"You will be able to work with {abstraction.get('type', 'this concept').lower()}"
                ],
                "estimated_time": "20-30 minutes",
                "complexity": abstraction.get("complexity", "Intermediate"),
                "hands_on_activity": abstraction.get("hands_on_activity", "Explore this concept in the code"),
                "success_criteria": f"Successfully understand and apply {abstraction['name']}",
                "prerequisites": prerequisites,
                "transitions": {
                    "from_previous": "Building on previous concepts" if i > 1 else "Starting point",
                    "to_next": "Prepares for next concept" if i < len(ordered_abstractions) else "Completes the learning journey"
                }
            }
            chapters.append(chapter)
        
        # Calculate total duration
        chapter_count = len(chapters)
        estimated_duration = f"{chapter_count * 25 // 60 + 1}-{chapter_count * 35 // 60 + 1} hours"
        
        return {
            "tutorial_overview": {
                "title": f"Complete Guide to {ordered_abstractions[0]['name'].split()[0] if ordered_abstractions else 'Project'} Development",
                "description": f"A comprehensive tutorial covering {len(chapters)} key concepts in a logical learning sequence.",
                "target_audience": "Developers who want to understand the project architecture and implementation",
                "estimated_duration": estimated_duration,
                "prerequisites": "Basic programming knowledge and familiarity with the technology stack"
            },
            "chapters": chapters
        }
    
    def _validate_ordering(self, ordering: Dict[str, Any], abstractions: List[Dict[str, Any]], 
                          relationships: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and enhance the chapter ordering"""
        if not ordering:
            dependency_analysis = self._analyze_dependencies(abstractions, relationships)
            return self._create_fallback_ordering(abstractions, dependency_analysis)
        
        # Validate chapters
        chapters = ordering.get("chapters", [])
        if not chapters:
            dependency_analysis = self._analyze_dependencies(abstractions, relationships)
            return self._create_fallback_ordering(abstractions, dependency_analysis)
        
        # Ensure all abstractions are covered
        abstraction_names = {a["name"] for a in abstractions}
        covered_abstractions = {c.get("abstraction", "") for c in chapters}
        
        if not covered_abstractions.issubset(abstraction_names):
            print("    ⚠️  Some chapters reference unknown abstractions, falling back to safe ordering")
            dependency_analysis = self._analyze_dependencies(abstractions, relationships)
            return self._create_fallback_ordering(abstractions, dependency_analysis)
        
        # Validate chapter numbering
        validated_chapters = []
        for i, chapter in enumerate(chapters, 1):
            validated_chapter = {
                "number": i,
                "title": chapter.get("title", f"Chapter {i}"),
                "abstraction": chapter.get("abstraction", ""),
                "type": chapter.get("type", "Core"),
                "description": chapter.get("description", "Learn important concepts"),
                "objectives": chapter.get("objectives", [f"Understand the concepts in chapter {i}"]),
                "estimated_time": chapter.get("estimated_time", "20-30 minutes"),
                "complexity": chapter.get("complexity", "Intermediate"),
                "hands_on_activity": chapter.get("hands_on_activity", "Practice with the concepts"),
                "success_criteria": chapter.get("success_criteria", "Complete the chapter objectives"),
                "prerequisites": chapter.get("prerequisites", []),
                "transitions": chapter.get("transitions", {
                    "from_previous": "Builds on previous knowledge",
                    "to_next": "Prepares for next concepts"
                })
            }
            validated_chapters.append(validated_chapter)
        
        # Validate tutorial overview
        tutorial_overview = ordering.get("tutorial_overview", {})
        validated_overview = {
            "title": tutorial_overview.get("title", f"Complete Tutorial Guide"),
            "description": tutorial_overview.get("description", f"Comprehensive tutorial with {len(validated_chapters)} chapters"),
            "target_audience": tutorial_overview.get("target_audience", "Developers"),
            "estimated_duration": tutorial_overview.get("estimated_duration", f"{len(validated_chapters) // 2 + 1}-{len(validated_chapters) // 2 + 2} hours"),
            "prerequisites": tutorial_overview.get("prerequisites", "Basic programming knowledge")
        }
        
        return {
            "tutorial_overview": validated_overview,
            "chapters": validated_chapters
        }
    
    def _assess_ordering_quality(self, ordering: Dict[str, Any], dependency_analysis: Dict[str, Any]) -> Dict[str, str]:
        """Assess the quality of the chapter ordering"""
        chapters = ordering.get("chapters", [])
        
        # Check dependency respect
        dependencies_respected = True
        dependency_violations = []
        
        chapter_positions = {c.get("abstraction", ""): c.get("number", 0) for c in chapters}
        dependencies = dependency_analysis["dependencies"]
        
        for concept, prereqs in dependencies.items():
            concept_pos = chapter_positions.get(concept, float('inf'))
            for prereq in prereqs:
                prereq_pos = chapter_positions.get(prereq, 0)
                if prereq_pos >= concept_pos:
                    dependencies_respected = False
                    dependency_violations.append(f"{prereq} should come before {concept}")
        
        # Check complexity progression
        complexities = [c.get("complexity", "Intermediate") for c in chapters]
        complexity_levels = {"Beginner": 1, "Intermediate": 2, "Advanced": 3}
        complexity_scores = [complexity_levels.get(c, 2) for c in complexities]
        
        smooth_progression = True
        for i in range(1, len(complexity_scores)):
            if complexity_scores[i] < complexity_scores[i-1] - 1:  # Drop by more than 1 level
                smooth_progression = False
                break
        
        # Assess chapter distribution
        foundation_count = len([c for c in chapters if c.get("type") == "Foundation"])
        core_count = len([c for c in chapters if c.get("type") == "Core"])
        advanced_count = len([c for c in chapters if c.get("type") == "Advanced"])
        
        good_distribution = foundation_count >= 1 and core_count >= 1
        
        return {
            "dependencies_respected": "Yes" if dependencies_respected else f"No - {len(dependency_violations)} violations",
            "complexity_progression": "Smooth" if smooth_progression else "Has jumps",
            "chapter_distribution": f"{foundation_count}F/{core_count}C/{advanced_count}A",
            "overall_quality": "Good" if dependencies_respected and smooth_progression and good_distribution else "Needs improvement"
        }
    
    def _get_chapter_type_distribution(self, chapters: List[Dict[str, Any]]) -> Dict[str, int]:
        """Get distribution of chapter types"""
        distribution = {}
        for chapter in chapters:
            chapter_type = chapter.get("type", "Core")
            distribution[chapter_type] = distribution.get(chapter_type, 0) + 1
        return distribution
    
    def _calculate_total_duration(self, chapters: List[Dict[str, Any]]) -> str:
        """Calculate total estimated duration"""
        total_min_minutes = 0
        total_max_minutes = 0
        
        for chapter in chapters:
            time_str = chapter.get("estimated_time", "20-30 minutes")
            # Extract numbers from time string
            import re
            numbers = re.findall(r'\d+', time_str)
            
            if len(numbers) >= 2:  # Range like "20-30 minutes"
                total_min_minutes += int(numbers[0])
                total_max_minutes += int(numbers[1])
            elif len(numbers) == 1:  # Single value like "25 minutes"
                time_val = int(numbers[0])
                total_min_minutes += time_val
                total_max_minutes += time_val
            else:  # Fallback
                total_min_minutes += 20
                total_max_minutes += 30
        
        min_hours = total_min_minutes / 60
        max_hours = total_max_minutes / 60
        
        return f"{min_hours:.1f}-{max_hours:.1f} hours ({total_min_minutes}-{total_max_minutes} minutes)"
    
    def _analyze_complexity_progression(self, chapters: List[Dict[str, Any]]) -> List[str]:
        """Analyze complexity progression through chapters"""
        complexity_progression = []
        for chapter in chapters:
            complexity = chapter.get("complexity", "Intermediate")
            chapter_num = chapter.get("number", 0)
            complexity_progression.append(f"Ch{chapter_num}: {complexity}")
        return complexity_progression
    
    def _print_chapter_summary(self, chapter_order: Dict[str, Any]):
        """Print a summary of the chapter ordering"""
        tutorial_overview = chapter_order.get("tutorial_overview", {})
        chapters = chapter_order.get("chapters", [])
        
        print(f"    📚 CHAPTER ORDERING SUMMARY:")
        print(f"      • Tutorial: {tutorial_overview.get('title', 'Unknown')}")
        print(f"      • Total Chapters: {len(chapters)}")
        print(f"      • Estimated Duration: {tutorial_overview.get('estimated_duration', 'Unknown')}")
        
        # Chapter type distribution
        type_dist = self._get_chapter_type_distribution(chapters)
        print(f"      • Chapter Types: {type_dist}")
        
        # Show first few chapters
        print(f"    📖 Chapter Sequence:")
        for chapter in chapters[:5]:  # Show first 5
            num = chapter.get("number", "?")
            title = chapter.get("title", "Unknown")
            chapter_type = chapter.get("type", "?")
            complexity = chapter.get("complexity", "?")
            print(f"      {num}. {title} ({chapter_type}, {complexity})")
        
        if len(chapters) > 5:
            print(f"      ... and {len(chapters) - 5} more chapters")
