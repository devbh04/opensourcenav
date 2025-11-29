# WriteChapters Node - Comprehensive chapter content generation
import re
from typing import List, Dict, Any, Tuple

from app.utils.flow_engine import Node, NodeResult
from app.utils.llm_integration import call_llm, create_writing_context
from app.utils.mermaid_generator import MermaidChartGenerator

class WriteChapters(Node):
    """
    Generates comprehensive tutorial content for each chapter
    with code examples, explanations, and hands-on activities
    """
    
    def __init__(self):
        super().__init__(
            name="WriteChapters",
            description="Generate comprehensive tutorial content for all chapters"
        )
    
    def prep(self, shared: Dict[str, Any]) -> NodeResult:
        """Prepare chapter definitions and code context for content generation"""
        try:
            chapter_order = shared.get("chapter_order", {})
            abstractions = shared.get("abstractions", [])
            files = shared.get("files", [])
            relationships = shared.get("relationships", {})
            
            chapters = chapter_order.get("chapters", [])
            if not chapters:
                return NodeResult(
                    success=False,
                    error="No chapter order available for content generation"
                )
            
            if not abstractions:
                return NodeResult(
                    success=False,
                    error="No abstractions available for content generation"
                )
            
            project_name = shared.get("project_name", "Unknown Project")
            
            # Create abstraction lookup for easy access
            abstraction_map = {a["name"]: a for a in abstractions}
            
            # Prepare code context for each chapter
            chapter_contexts = []
            for chapter in chapters:
                abstraction_name = chapter.get("abstraction", "")
                abstraction = abstraction_map.get(abstraction_name, {})
                
                # Get relevant code files for this chapter
                code_context = self._get_code_context_for_chapter(
                    abstraction, files, project_name
                )
                
                chapter_contexts.append({
                    "chapter": chapter,
                    "abstraction": abstraction,
                    "code_context": code_context
                })
            
            # Create global tutorial context
            tutorial_context = self._create_tutorial_context(
                chapter_order, abstractions, relationships, project_name
            )
            
            prep_data = {
                "chapter_contexts": chapter_contexts,
                "tutorial_context": tutorial_context,
                "project_name": project_name,
                "total_chapters": len(chapters),
                "abstraction_map": abstraction_map
            }
            
            print(f"    📝 Preparing content generation for {len(chapters)} chapters")
            print(f"    📊 Tutorial context: {len(tutorial_context)} characters")
            
            # Calculate estimated tokens for all chapters
            estimated_tokens = sum(len(ctx["code_context"]) for ctx in chapter_contexts) // 4
            print(f"    🧮 Estimated total tokens: ~{estimated_tokens:,}")
            
            return NodeResult(
                success=True,
                data=prep_data,
                metadata={
                    "chapters_to_write": len(chapters),
                    "context_size": len(tutorial_context),
                    "estimated_tokens": estimated_tokens
                }
            )
            
        except Exception as e:
            return NodeResult(
                success=False,
                error=f"Prep phase failed: {str(e)}"
            )
    
    def exec(self, prep_result: NodeResult) -> NodeResult:
        """Execute chapter content generation with rate limiting and progress tracking"""
        try:
            prep_data = prep_result.data
            chapter_contexts = prep_data["chapter_contexts"]
            tutorial_context = prep_data["tutorial_context"]
            project_name = prep_data["project_name"]
            
            generated_chapters = []
            total_chapters = len(chapter_contexts)
            total_tokens_used = 0
            
            print(f"    ✍️  Starting content generation for {total_chapters} chapters...")
            
            # Generate content for each chapter
            for i, chapter_context in enumerate(chapter_contexts, 1):
                chapter = chapter_context["chapter"]
                abstraction = chapter_context["abstraction"]
                code_context = chapter_context["code_context"]
                
                chapter_num = chapter.get("number", i)
                chapter_title = chapter.get("title", f"Chapter {chapter_num}")
                
                print(f"    📄 [{i}/{total_chapters}] Writing: {chapter_title}")
                
                # Rate limiting - pause between chapters to respect API limits
                if i > 1:
                    import time
                    pause_time = 3.0  # 3 second pause between chapters
                    print(f"       ⏱️  Pausing {pause_time}s for rate limiting...")
                    time.sleep(pause_time)
                
                # Generate chapter content
                chapter_content = self._generate_chapter_content(
                    chapter, abstraction, code_context, tutorial_context, 
                    generated_chapters, project_name
                )
                
                if chapter_content:
                    generated_chapters.append({
                        "chapter_number": chapter_num,
                        "title": chapter_title,
                        "content": chapter_content["content"],
                        "tokens_used": chapter_content.get("tokens_used", 0),
                        "generated_successfully": True
                    })
                    total_tokens_used += chapter_content.get("tokens_used", 0)
                    
                    content_length = len(chapter_content["content"])
                    print(f"       ✅ Generated {content_length:,} characters")
                else:
                    # Create fallback content
                    fallback_content = self._create_fallback_chapter_content(
                        chapter, abstraction, code_context
                    )
                    generated_chapters.append({
                        "chapter_number": chapter_num,
                        "title": chapter_title,
                        "content": fallback_content,
                        "tokens_used": 0,
                        "generated_successfully": False
                    })
                    print(f"       ⚠️  Used fallback content")
            
            success_count = sum(1 for ch in generated_chapters if ch["generated_successfully"])
            
            print(f"    ✅ Chapter generation complete: {success_count}/{total_chapters} successful")
            print(f"    🧮 Total tokens used: {total_tokens_used:,}")
            
            return NodeResult(
                success=True,
                data={
                    "chapters": generated_chapters,
                    "total_tokens_used": total_tokens_used,
                    "success_rate": success_count / total_chapters
                },
                metadata={
                    "chapters_generated": len(generated_chapters),
                    "successful_generations": success_count,
                    "total_tokens": total_tokens_used,
                    "average_chapter_length": sum(len(ch["content"]) for ch in generated_chapters) // len(generated_chapters) if generated_chapters else 0
                }
            )
            
        except Exception as e:
            return NodeResult(
                success=False,
                error=f"Execution failed: {str(e)}"
            )
    
    def post(self, shared: Dict[str, Any], prep_result: NodeResult, exec_result: NodeResult) -> NodeResult:
        """Update shared state with generated chapter content"""
        try:
            exec_data = exec_result.data
            chapters = exec_data["chapters"]
            
            # Update shared state
            shared["chapters"] = chapters
            
            # Add content generation metadata
            shared["content_generation"] = {
                "total_chapters": len(chapters),
                "successful_generations": sum(1 for ch in chapters if ch["generated_successfully"]),
                "total_content_length": sum(len(ch["content"]) for ch in chapters),
                "average_chapter_length": sum(len(ch["content"]) for ch in chapters) // len(chapters) if chapters else 0,
                "tokens_used": exec_data.get("total_tokens_used", 0),
                "success_rate": exec_data.get("success_rate", 0.0)
            }
            
            print(f"    📝 Updated shared state with {len(chapters)} generated chapters")
            self._print_content_summary(chapters)
            
            return NodeResult(
                success=True,
                data={"chapters_generated": len(chapters)},
                metadata={
                    "summary": shared["content_generation"]
                }
            )
            
        except Exception as e:
            return NodeResult(
                success=False,
                error=f"Post phase failed: {str(e)}"
            )
    
    def _get_code_context_for_chapter(self, abstraction: Dict[str, Any], 
                                    files: List[Tuple[str, str]], project_name: str) -> str:
        """Get relevant code context for a specific chapter"""
        files_involved = abstraction.get("files_involved", [])
        
        context_parts = [
            f"# Code Context for {abstraction.get('name', 'Unknown Abstraction')}",
            ""
        ]
        
        # Add relevant files
        relevant_files_found = 0
        for filepath, content in files:
            if filepath in files_involved or any(involved_file in filepath for involved_file in files_involved):
                relevant_files_found += 1
                
                # Limit content length to avoid token limits
                if len(content) > 3000:
                    content = content[:3000] + "\n\n... (content truncated for brevity) ..."
                
                context_parts.extend([
                    f"## File: {filepath}",
                    "```",
                    content,
                    "```",
                    ""
                ])
        
        # If no specific files found, include some general project files
        if relevant_files_found == 0:
            context_parts.append("## Related Code Examples")
            for filepath, content in files[:3]:  # Include first 3 files as examples
                if len(content) > 1000:
                    content = content[:1000] + "\n\n... (content truncated) ..."
                
                context_parts.extend([
                    f"### {filepath}",
                    "```",
                    content,
                    "```",
                    ""
                ])
        
        return "\n".join(context_parts)
    
    def _create_tutorial_context(self, chapter_order: Dict[str, Any], abstractions: List[Dict[str, Any]],
                               relationships: Dict[str, Any], project_name: str) -> str:
        """Create global tutorial context for consistent chapter generation"""
        tutorial_overview = chapter_order.get("tutorial_overview", {})
        
        context_parts = [
            f"# {project_name} Tutorial Context",
            "",
            f"**Tutorial Title**: {tutorial_overview.get('title', 'Complete Guide')}",
            f"**Description**: {tutorial_overview.get('description', 'Comprehensive tutorial')}",
            f"**Target Audience**: {tutorial_overview.get('target_audience', 'Developers')}",
            f"**Duration**: {tutorial_overview.get('estimated_duration', 'Several hours')}",
            "",
            "## Learning Objectives",
            "By the end of this tutorial, learners will:",
        ]
        
        # Add learning objectives based on abstractions
        for abstraction in abstractions:
            learning_value = abstraction.get("learning_value", "")
            if learning_value:
                context_parts.append(f"- {learning_value}")
        
        context_parts.extend([
            "",
            "## Project Overview",
            relationships.get("project_summary", "Software project with multiple components"),
            ""
        ])
        
        # Add key insights
        key_insights = relationships.get("key_insights", [])
        if key_insights:
            context_parts.extend([
                "## Key Project Insights",
            ])
            for insight in key_insights:
                context_parts.append(f"- {insight}")
            context_parts.append("")
        
        # Add chapter overview
        chapters = chapter_order.get("chapters", [])
        if chapters:
            context_parts.extend([
                "## Chapter Overview",
            ])
            for chapter in chapters:
                num = chapter.get("number", "?")
                title = chapter.get("title", "Unknown")
                chapter_type = chapter.get("type", "Core")
                context_parts.append(f"{num}. {title} ({chapter_type})")
        
        return "\n".join(context_parts)
    
    def _generate_chapter_content(self, chapter: Dict[str, Any], abstraction: Dict[str, Any],
                                code_context: str, tutorial_context: str, 
                                previous_chapters: List[Dict[str, Any]], project_name: str) -> Dict[str, Any]:
        """Generate comprehensive content for a single chapter"""
        
        try:
            # Create chapter generation prompt
            prompt = self._create_chapter_prompt(
                chapter, abstraction, code_context, tutorial_context, previous_chapters, project_name
            )
            
            # Call LLM for content generation
            context = create_writing_context()
            llm_response = call_llm(prompt, context)
            
            if llm_response.success:
                return {
                    "content": llm_response.content,
                    "tokens_used": llm_response.tokens_used,
                    "cached": llm_response.cached
                }
            else:
                print(f"       ❌ LLM generation failed: {llm_response.error}")
                return None
        except Exception as e:
            print(f"       ❌ Error in _generate_chapter_content: {e}")
            print(f"       📊 Chapter data: {chapter}")
            print(f"       📊 Abstraction data: {abstraction}")
            raise
    
    def _get_chart_suggestions(self, chapter: Dict[str, Any], abstraction: Dict[str, Any]) -> str:
        """Generate chart type suggestions based on chapter content"""
        abstraction_type = abstraction.get('type', '').lower()
        chapter_type = chapter.get('type', '').lower()
        abstraction_name = abstraction.get('name', '').lower()
        
        suggestions = []
        
        # Architecture/System related
        if any(keyword in abstraction_name for keyword in ['architecture', 'system', 'structure', 'framework']):
            suggestions.append("Consider using **Architecture Diagrams** to show system components and their relationships")
        
        # Process/Workflow related
        if any(keyword in abstraction_name for keyword in ['process', 'workflow', 'pipeline', 'flow', 'execution']):
            suggestions.append("Consider using **Flowcharts** to illustrate step-by-step processes")
        
        # Class/Object related
        if any(keyword in abstraction_name for keyword in ['class', 'object', 'model', 'entity', 'inheritance']):
            suggestions.append("Consider using **Class Diagrams** to show object relationships and hierarchies")
        
        # State/Lifecycle related
        if any(keyword in abstraction_name for keyword in ['state', 'lifecycle', 'status', 'transition']):
            suggestions.append("Consider using **State Diagrams** to show state transitions and conditions")
        
        # API/Communication related
        if any(keyword in abstraction_name for keyword in ['api', 'communication', 'interaction', 'request', 'response']):
            suggestions.append("Consider using **Sequence Diagrams** to show interactions between components")
        
        # Data/Database related
        if any(keyword in abstraction_name for keyword in ['data', 'database', 'schema', 'table', 'relationship']):
            suggestions.append("Consider using **Entity-Relationship Diagrams** to show data relationships")
        
        # Timeline/Progress related
        if any(keyword in abstraction_name for keyword in ['timeline', 'history', 'progress', 'development']):
            suggestions.append("Consider using **Timeline Diagrams** to show chronological progression")
        
        # If foundation chapter, suggest mindmaps
        if chapter_type == 'foundation':
            suggestions.append("Consider using **Mindmaps** to show concept relationships and hierarchies")
        
        # Default suggestion
        if not suggestions:
            suggestions.append("Choose appropriate Mermaid diagrams (flowchart, sequence, class, state, etc.) to visualize concepts")
        
        return "\n   - ".join(suggestions)
    
    def _create_chapter_prompt(self, chapter: Dict[str, Any], abstraction: Dict[str, Any],
                             code_context: str, tutorial_context: str,
                             previous_chapters: List[Dict[str, Any]], project_name: str) -> str:
        """Create comprehensive prompt for chapter content generation"""
        
        chapter_num = chapter.get("number", 1)
        chapter_title = chapter.get("title", "Chapter")
        abstraction_name = abstraction.get("name", "Unknown")
        
        # Create context about previous chapters
        previous_context = ""
        if previous_chapters:
            previous_context = "\n## Previous Chapters Context\n"
            for prev_ch in previous_chapters[-2:]:  # Last 2 chapters for context
                prev_title = prev_ch.get("title", "Previous Chapter")
                previous_context += f"- {prev_title}: Already covered foundational concepts\n"
        
        # Generate chart suggestions based on content
        chart_suggestions = self._get_chart_suggestions(chapter, abstraction)
        
        # Create the template using string concatenation to avoid f-string issues with + symbols
        template_part1 = f"""
**ROLE**: You are a master technical writing instructor and software development educator with expertise in creating engaging, practical programming tutorials.

**TASK**: Write comprehensive tutorial content for Chapter {chapter_num} of the {project_name} tutorial series. Create content that is beginner-friendly, practical, and immediately actionable.

**CHAPTER SPECIFICATIONS**:
- **Number**: {chapter_num}
- **Title**: {chapter_title}
- **Abstraction**: {abstraction_name}
- **Type**: {chapter.get('type', 'Core')}
- **Complexity**: {chapter.get('complexity', 'Intermediate')}
- **Estimated Time**: {chapter.get('estimated_time', '20-30 minutes')}

**CHAPTER OBJECTIVES**:
{chr(10).join(f"- {str(obj)}" for obj in chapter.get('objectives', ['Learn key concepts']))}

**HANDS-ON ACTIVITY**:
{chapter.get('hands_on_activity', 'Practice with the concepts')}

**SUCCESS CRITERIA**:
{chapter.get('success_criteria', 'Complete chapter objectives')}

**TUTORIAL CONTEXT**:
{tutorial_context}

{previous_context}

**CODE CONTEXT FOR THIS CHAPTER**:
{code_context}

**WRITING GUIDELINES**:

1. **Engaging Introduction** (100-150 words):
   - Hook the reader with practical value
   - Connect to previous learning or real-world scenarios
   - Preview what they'll accomplish

2. **Concept Explanation** (200-300 words):
   - Explain the abstraction using analogies and real-world examples
   - Break down complex ideas into digestible parts
   - Use beginner-friendly language without being condescending

3. **Code Walkthrough** (300-500 words):
   - Show relevant code examples with detailed explanations
   - Use line-by-line comments for complex parts
   - Highlight patterns and best practices
   - Keep examples under 10 lines when possible

4. **Visual Diagrams** (as appropriate):
   - Use Mermaid diagrams to illustrate concepts visually
   - {chart_suggestions}

5. **Hands-On Exercise** (200-300 words):
   - Provide step-by-step instructions for the practical activity
   - Include expected outcomes and how to verify success
   - Offer troubleshooting tips for common issues

6. **Key Takeaways** (100-150 words):
   - Summarize the most important concepts
   - Connect to broader development practices
   - Preview how this knowledge will be used in future chapters

7. **Smooth Transition** (50-100 words):
   - Connect this chapter to the next topic
   - Maintain learning momentum

**CONTENT REQUIREMENTS**:
- Use Markdown formatting with proper headers (##, ###)
- Include code blocks with appropriate syntax highlighting
- Add Mermaid diagrams where helpful for visualization
- Keep paragraphs short (2-4 sentences) for readability
- Use bullet points and numbered lists to break up content
- Include practical tips and best practices throughout

**TONE AND STYLE**:
- Conversational but professional
- Encouraging and supportive
- Practical and action-oriented
- Avoid jargon without explanation
- Use "you" to directly address the learner

**EXAMPLE CODE BLOCK FORMAT**:
```language
// Clear, descriptive comments
const example = "code with explanation";
// Highlight important patterns
```"""

        # Add Mermaid diagram examples as a separate string to avoid f-string parsing issues
        mermaid_examples = """

**MERMAID DIAGRAM OPTIONS** (use when appropriate):

**Flowchart** (for processes and workflows):
```mermaid
flowchart TD
    A[Start] --> B[Process]
    B --> C[Result]
```

**Sequence Diagram** (for interactions):
```mermaid
sequenceDiagram
    participant A as User
    participant B as System
    A->>B: Request
    B-->>A: Response
```

**Class Diagram** (for object relationships):
```mermaid
classDiagram
    class Example {
        +property: string
        +method(): void
    }
```

**State Diagram** (for state changes):
```mermaid
stateDiagram-v2
    [*] --> Idle
    Idle --> Processing: start()
    Processing --> [*]: complete()
```

**Architecture Diagram** (for system components):
```mermaid
flowchart TB
    A[Frontend]:::component --> B[Backend]:::component
    B --> C[Database]:::component
    
    classDef component fill:#85bbf0,stroke:#5d82a8,color:#000000
```

**OUTPUT FORMAT**: Return complete chapter content in Markdown format, ready for tutorial publication.

Write engaging, practical tutorial content that helps developers immediately apply what they learn.
"""
        
        return template_part1 + mermaid_examples
    
    def _create_fallback_chapter_content(self, chapter: Dict[str, Any], abstraction: Dict[str, Any],
                                       code_context: str) -> str:
        """Create fallback content when LLM generation fails"""
        chapter_num = chapter.get("number", 1)
        chapter_title = chapter.get("title", "Chapter")
        abstraction_name = abstraction.get("name", "Unknown Concept")
        
        content = f"""# Chapter {chapter_num}: {chapter_title}

## Introduction

In this chapter, we'll explore {abstraction_name}, which is a {abstraction.get('type', 'important')} component in our system. Understanding this concept is crucial for {abstraction.get('learning_value', 'working effectively with the codebase')}.

## What is {abstraction_name}?

{abstraction.get('description', 'This is a key concept in the system that helps organize and structure the code.')}

### Key Characteristics

{chr(10).join(f"- {str(concept)}" for concept in abstraction.get('key_concepts', ['Important functionality', 'Core system component']))}

## Code Examples

The following files are particularly relevant to understanding {abstraction_name}:

{chr(10).join(f"- `{file}`" for file in abstraction.get('files_involved', ['example.py']))}

```python
# Example code demonstrating {abstraction_name}
# This is a simplified example to illustrate the concept

def example_function():
    '''
    This function demonstrates the key ideas behind {abstraction_name}
    '''
    return "Understanding {abstraction_name}"
```

## Hands-On Activity

{chapter.get('hands_on_activity', f'Explore the {abstraction_name} concept in the codebase by examining the relevant files and understanding how they work together.')}

### Steps to Complete:

1. Locate the relevant files in your codebase
2. Read through the code and identify the key patterns
3. Try making a small modification to see how the system responds
4. Verify that your changes work as expected

## Key Takeaways

- {abstraction_name} is essential for {abstraction.get('learning_value', 'understanding the system')}
- The concept helps organize code in a {abstraction.get('complexity', 'structured').lower()} way
- Understanding this will prepare you for more advanced topics

## What's Next?

In the next chapter, we'll build on this foundation to explore how {abstraction_name} connects with other parts of the system.

---

*Estimated completion time: {chapter.get('estimated_time', '20-30 minutes')}*
"""
        return content
    
    def _print_content_summary(self, chapters: List[Dict[str, Any]]):
        """Print a summary of generated chapter content"""
        total_chapters = len(chapters)
        successful = sum(1 for ch in chapters if ch["generated_successfully"])
        total_length = sum(len(ch["content"]) for ch in chapters)
        avg_length = total_length // total_chapters if total_chapters > 0 else 0
        
        print(f"    📊 CONTENT GENERATION SUMMARY:")
        print(f"      • Total Chapters: {total_chapters}")
        print(f"      • Successfully Generated: {successful} ({successful/total_chapters*100:.1f}%)")
        print(f"      • Total Content: {total_length:,} characters")
        print(f"      • Average Chapter Length: {avg_length:,} characters")
        
        # Show chapter lengths
        print(f"    📄 Chapter Lengths:")
        for chapter in chapters[:5]:  # Show first 5
            num = chapter["chapter_number"]
            length = len(chapter["content"])
            status = "✅" if chapter["generated_successfully"] else "⚠️"
            print(f"      {status} Chapter {num}: {length:,} characters")
        
        if len(chapters) > 5:
            print(f"      ... and {len(chapters) - 5} more chapters")
