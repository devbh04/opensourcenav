# CombineTutorial Node - Comprehensive tutorial assembly and organization
import os
import json
from pathlib import Path
from typing import List, Dict, Any

from app.utils.flow_engine import Node, NodeResult
from app.utils.mermaid_generator import MermaidChartGenerator, create_tutorial_charts

class CombineTutorial(Node):
    """
    Assembles final tutorial with index, navigation, visual overview,
    and properly organized chapter files
    """
    
    def __init__(self):
        super().__init__(
            name="CombineTutorial",
            description="Assemble complete tutorial with navigation and visual overview"
        )
    
    def prep(self, shared: Dict[str, Any]) -> NodeResult:
        """Prepare tutorial data for final assembly"""
        try:
            chapters = shared.get("chapters", [])
            chapter_order = shared.get("chapter_order", {})
            abstractions = shared.get("abstractions", [])
            relationships = shared.get("relationships", {})
            
            if not chapters:
                return NodeResult(
                    success=False,
                    error="No chapters available for tutorial assembly"
                )
            
            project_name = shared.get("project_name", "Unknown Project")
            output_dir = shared.get("output_dir", "tutorial_output")
            
            # Prepare tutorial metadata
            tutorial_overview = chapter_order.get("tutorial_overview", {})
            
            prep_data = {
                "chapters": chapters,
                "tutorial_overview": tutorial_overview,
                "abstractions": abstractions,
                "relationships": relationships,
                "project_name": project_name,
                "output_dir": output_dir,
                "total_content_size": sum(len(ch["content"]) for ch in chapters)
            }
            
            print(f"    📂 Preparing tutorial assembly for {len(chapters)} chapters")
            print(f"    📁 Output directory: {output_dir}")
            print(f"    📊 Total content size: {prep_data['total_content_size']:,} characters")
            
            return NodeResult(
                success=True,
                data=prep_data,
                metadata={
                    "chapters_count": len(chapters),
                    "output_directory": output_dir,
                    "content_size": prep_data["total_content_size"]
                }
            )
            
        except Exception as e:
            return NodeResult(
                success=False,
                error=f"Prep phase failed: {str(e)}"
            )
    
    def exec(self, prep_result: NodeResult) -> NodeResult:
        """Execute tutorial assembly and content generation (no file creation)"""
        try:
            prep_data = prep_result.data
            chapters = prep_data["chapters"]
            tutorial_overview = prep_data["tutorial_overview"]
            abstractions = prep_data["abstractions"]
            relationships = prep_data["relationships"]
            project_name = prep_data["project_name"]
            
            print(f"    📄 Generating tutorial content (no files will be created)...")
            
            # Generate all tutorial content
            generated_content = {}
            
            # 1. Create main index content
            print(f"    📄 Creating main index content...")
            index_content = self._create_main_index(
                tutorial_overview, chapters, abstractions, relationships, project_name
            )
            generated_content["index_content"] = index_content
            
            # 2. Create individual chapter content with navigation
            print(f"    📚 Enhancing chapter content...")
            enhanced_chapters = []
            for chapter in chapters:
                # Add navigation to chapter content
                enhanced_content = self._add_chapter_navigation(
                    chapter, chapters, chapter['content']
                )
                
                enhanced_chapter = chapter.copy()
                enhanced_chapter['enhanced_content'] = enhanced_content
                enhanced_chapter['filename'] = f"{chapter['chapter_number']:02d}_{self._sanitize_filename(chapter['title'])}.md"
                enhanced_chapters.append(enhanced_chapter)
            
            generated_content["enhanced_chapters"] = enhanced_chapters
            
            # 3. Create tutorial metadata
            print(f"    📋 Creating metadata...")
            metadata = self._create_tutorial_metadata(
                tutorial_overview, chapters, abstractions, relationships, project_name
            )
            generated_content["metadata"] = metadata
            
            # 4. Create README content
            print(f"    📖 Creating README content...")
            readme_content = self._create_readme(tutorial_overview, chapters, project_name)
            generated_content["readme_content"] = readme_content
            
            # 5. Create quick reference content
            print(f"    📚 Creating quick reference content...")
            reference_content = self._create_quick_reference(abstractions, relationships)
            generated_content["quick_reference_content"] = reference_content
            
            # 6. Create combined tutorial content
            print(f"    📝 Creating combined tutorial content...")
            tutorial_content = self._create_combined_tutorial_content(
                tutorial_overview, enhanced_chapters, abstractions, relationships, project_name
            )
            generated_content["tutorial_content"] = tutorial_content
            
            print(f"    ✅ Tutorial content generation complete: {len(generated_content)} content types created")
            
            return NodeResult(
                success=True,
                data=generated_content,
                metadata={
                    "content_types": list(generated_content.keys()),
                    "content_count": len(generated_content),
                    "chapters_enhanced": len(enhanced_chapters)
                }
            )
            
        except Exception as e:
            return NodeResult(
                success=False,
                error=f"Execution failed: {str(e)}"
            )
    
    def post(self, shared: Dict[str, Any], prep_result: NodeResult, exec_result: NodeResult) -> NodeResult:
        """Update shared state with generated content"""
        try:
            exec_data = exec_result.data
            
            # Update shared state with generated content
            shared["tutorial_content"] = exec_data.get("tutorial_content", "")
            shared["index_content"] = exec_data.get("index_content", "")
            shared["readme_content"] = exec_data.get("readme_content", "")
            shared["quick_reference_content"] = exec_data.get("quick_reference_content", "")
            shared["enhanced_chapters"] = exec_data.get("enhanced_chapters", [])
            shared["tutorial_metadata"] = exec_data.get("metadata", {})
            
            # Add final tutorial metadata
            shared["tutorial_complete"] = {
                "content_generated": True,
                "content_types": len(exec_data),
                "chapters_count": len(shared.get("chapters", [])),
                "abstractions_count": len(shared.get("abstractions", [])),
                "success": True
            }
            
            print(f"    📝 Updated shared state with generated content")
            print(f"    🎉 Tutorial content successfully generated with {len(exec_data)} content types")
            self._print_tutorial_summary(shared)
            
            return NodeResult(
                success=True,
                data={"tutorial_completed": True},
                metadata={
                    "content_types": list(exec_data.keys()),
                    "completion_summary": shared["tutorial_complete"]
                }
            )
            
        except Exception as e:
            return NodeResult(
                success=False,
                error=f"Post phase failed: {str(e)}"
            )
    
    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for filesystem compatibility"""
        # Remove/replace problematic characters
        sanitized = filename.lower()
        sanitized = "".join(c if c.isalnum() or c in "._- " else "_" for c in sanitized)
        sanitized = "_".join(sanitized.split())  # Replace spaces with underscores
        return sanitized[:50]  # Limit length
    
    def _create_main_index(self, tutorial_overview: Dict[str, Any], chapters: List[Dict[str, Any]],
                          abstractions: List[Dict[str, Any]], relationships: Dict[str, Any],
                          project_name: str) -> str:
        """Create comprehensive main index file with enhanced Mermaid charts"""
        
        # Generate multiple types of charts using the enhanced generator
        shared_state = {
            'abstractions': abstractions,
            'relationships': relationships,
            'chapters': chapters,
            'project_name': project_name
        }
        
        charts = create_tutorial_charts(shared_state)
        
        # Calculate tutorial statistics
        total_chapters = len(chapters)
        estimated_duration = tutorial_overview.get("estimated_duration", "Several hours")
        foundation_chapters = len([c for c in chapters if c.get("type") == "Foundation"])
        core_chapters = len([c for c in chapters if c.get("type") == "Core"])
        advanced_chapters = len([c for c in chapters if c.get("type") == "Advanced"])
        
        index_content = f"""# {tutorial_overview.get('title', f'{project_name} Complete Tutorial')}

{tutorial_overview.get('description', f'A comprehensive tutorial for understanding and working with {project_name}.')}

## 🎯 Learning Objectives

By completing this tutorial, you will:

"""
        
        # Add learning objectives from abstractions
        for abstraction in abstractions[:8]:  # Show top 8 objectives
            learning_value = abstraction.get("learning_value", "")
            if learning_value:
                index_content += f"- {learning_value}\n"
        
        index_content += f"""
## 📊 Tutorial Overview

- **Target Audience**: {tutorial_overview.get('target_audience', 'Developers')}
- **Estimated Duration**: {estimated_duration}
- **Prerequisites**: {tutorial_overview.get('prerequisites', 'Basic programming knowledge')}
- **Total Chapters**: {total_chapters} ({foundation_chapters} Foundation, {core_chapters} Core, {advanced_chapters} Advanced)

## 🗺️ Project Architecture Overview

Understanding the relationships between key concepts will help you navigate this tutorial effectively:

{charts.get('architecture', '')}

## 📈 Learning Journey

Follow this structured path through the tutorial:

{charts.get('timeline', '')}

## 🏗️ Component Relationships

See how different components interact with each other:

{charts.get('components', '')}

## 📚 Tutorial Chapters

"""
        
        # Add chapter listing with descriptions
        for chapter in chapters:
            num = chapter.get("chapter_number", "?")
            title = chapter.get("title", "Unknown")
            chapter_type = chapter.get("type", "Core")
            complexity = chapter.get("complexity", "Intermediate")
            estimated_time = chapter.get("estimated_time", "20-30 minutes")
            description = chapter.get("description", "Learn important concepts")
            
            # Create chapter filename
            chapter_filename = f"{num:02d}_{self._sanitize_filename(title)}.md"
            
            index_content += f"""### [{num}. {title}]({chapter_filename})

**Type**: {chapter_type} | **Complexity**: {complexity} | **Time**: {estimated_time}

{description}

"""
        
        # Add project insights
        key_insights = relationships.get("key_insights", [])
        if key_insights:
            index_content += f"""## 🔍 Key Project Insights

"""
            for insight in key_insights:
                index_content += f"- {insight}\n"
        
        index_content += f"""
## 🚀 Getting Started

1. **Prerequisites**: Ensure you have {tutorial_overview.get('prerequisites', 'the necessary tools installed')}
2. **Setup**: Follow the instructions in [README.md](README.md) to set up your environment
3. **Learning Path**: Start with Chapter 1 and work through sequentially
4. **Hands-On Practice**: Each chapter includes practical exercises - don't skip them!
5. **Reference**: Use [Quick Reference](quick_reference.md) for concept summaries

## 📖 How to Use This Tutorial

- **Read Actively**: Don't just read - try the examples and exercises
- **Take Notes**: Keep track of key concepts and personal insights
- **Experiment**: Modify examples to deepen your understanding
- **Ask Questions**: Research unfamiliar concepts as you encounter them
- **Practice**: The hands-on activities are crucial for retention

## 🛠️ Additional Resources

- **Quick Reference**: [quick_reference.md](quick_reference.md) - Key concepts at a glance
- **Tutorial Metadata**: [tutorial_metadata.json](tutorial_metadata.json) - Structured data about this tutorial
- **Project Documentation**: Check the original project documentation for detailed API references

## 📝 Tutorial Structure

This tutorial follows a carefully designed learning progression:

1. **Foundation Chapters**: Build essential understanding
2. **Core Chapters**: Learn primary functionality and patterns  
3. **Advanced Chapters**: Master complex topics and integrations

Each chapter includes:
- Clear learning objectives
- Practical code examples
- Hands-on exercises
- Success criteria
- Smooth transitions to next topics

---

**Happy Learning!** 🎉

*This tutorial was generated using an intelligent analysis of the {project_name} codebase, ensuring you learn the most important concepts in the optimal sequence.*
"""
        
        return index_content
    
    def _create_relationship_diagram(self, abstractions: List[Dict[str, Any]], 
                                   relationships: Dict[str, Any]) -> str:
        """Create Mermaid diagram showing abstraction relationships"""
        
        # Create simplified node names for the diagram
        node_map = {}
        for i, abstraction in enumerate(abstractions):
            name = abstraction["name"]
            # Create short node ID
            node_id = f"A{i+1}"
            # Create display name (shortened)
            display_name = name[:20] + "..." if len(name) > 20 else name
            node_map[name] = {"id": node_id, "display": display_name, "type": abstraction.get("type", "Feature")}
        
        # Build diagram
        diagram = """```mermaid
flowchart TD
"""
        
        # Add nodes with styling based on type
        for name, node_info in node_map.items():
            node_id = node_info["id"]
            display = node_info["display"]
            node_type = node_info["type"]
            
            # Style based on type
            if node_type in ["Architecture", "Foundation"]:
                diagram += f'    {node_id}["{display}"]:::foundation\n'
            elif node_type in ["Feature", "Core"]:
                diagram += f'    {node_id}["{display}"]:::core\n'
            else:
                diagram += f'    {node_id}["{display}"]:::advanced\n'
        
        # Add relationships
        relationship_list = relationships.get("relationships", [])
        strong_relationships = [r for r in relationship_list if r.get("strength") in ["Strong", "Medium"]]
        
        for rel in strong_relationships[:10]:  # Limit to avoid cluttered diagram
            from_name = rel.get("from", "")
            to_name = rel.get("to", "")
            rel_type = rel.get("type", "")
            
            if from_name in node_map and to_name in node_map:
                from_id = node_map[from_name]["id"]
                to_id = node_map[to_name]["id"]
                
                # Different arrow styles for different relationship types
                if rel_type == "PREREQUISITE":
                    diagram += f"    {from_id} --> {to_id}\n"
                elif rel_type == "USES":
                    diagram += f"    {from_id} -.-> {to_id}\n"
                else:
                    diagram += f"    {from_id} --- {to_id}\n"
        
        # Add styling
        diagram += """
    classDef foundation fill:#e1f5fe,stroke:#01579b,stroke-width:2px
    classDef core fill:#f3e5f5,stroke:#4a148c,stroke-width:2px
    classDef advanced fill:#fff3e0,stroke:#e65100,stroke-width:2px
```"""
        
        return diagram
    
    def _add_chapter_navigation(self, current_chapter: Dict[str, Any], 
                              all_chapters: List[Dict[str, Any]], content: str) -> str:
        """Add navigation links to chapter content"""
        
        current_num = current_chapter.get("chapter_number", 1)
        
        # Find previous and next chapters
        prev_chapter = None
        next_chapter = None
        
        for chapter in all_chapters:
            if chapter.get("chapter_number", 0) == current_num - 1:
                prev_chapter = chapter
            elif chapter.get("chapter_number", 0) == current_num + 1:
                next_chapter = chapter
        
        # Create navigation header
        nav_header = f"""---
# Chapter {current_num}: {current_chapter.get('title', 'Unknown')}

"""
        
        # Add breadcrumb navigation
        nav_header += "**Navigation**: [🏠 Home](index.md)"
        if prev_chapter:
            prev_filename = f"{prev_chapter['chapter_number']:02d}_{self._sanitize_filename(prev_chapter['title'])}.md"
            nav_header += f" | [⬅️ Previous]({prev_filename})"
        if next_chapter:
            next_filename = f"{next_chapter['chapter_number']:02d}_{self._sanitize_filename(next_chapter['title'])}.md"
            nav_header += f" | [➡️ Next]({next_filename})"
        
        nav_header += "\n\n---\n\n"
        
        # Create navigation footer
        nav_footer = f"""

---

## 🎯 Chapter Summary

You've completed Chapter {current_num}! Here's what you accomplished:

- ✅ {current_chapter.get('success_criteria', 'Completed chapter objectives')}

"""
        
        # Add navigation footer
        nav_footer += "### What's Next?\n\n"
        if next_chapter:
            next_title = next_chapter.get('title', 'Next Chapter')
            next_description = next_chapter.get('description', 'Continue your learning journey')
            next_filename = f"{next_chapter['chapter_number']:02d}_{self._sanitize_filename(next_chapter['title'])}.md"
            nav_footer += f"Continue to **[{next_title}]({next_filename})** - {next_description}\n\n"
        else:
            nav_footer += "🎉 **Congratulations!** You've completed the entire tutorial! Check out the [Quick Reference](quick_reference.md) for a summary of all concepts.\n\n"
        
        nav_footer += """---

**Tutorial Navigation**:
- [🏠 Back to Home](index.md)
- [📚 Quick Reference](quick_reference.md)
- [📖 README](README.md)
"""
        
        # Combine all parts
        return nav_header + content + nav_footer
    
    def _create_tutorial_metadata(self, tutorial_overview: Dict[str, Any], chapters: List[Dict[str, Any]],
                                 abstractions: List[Dict[str, Any]], relationships: Dict[str, Any],
                                 project_name: str) -> Dict[str, Any]:
        """Create comprehensive tutorial metadata"""
        
        return {
            "tutorial_info": {
                "title": tutorial_overview.get("title", f"{project_name} Tutorial"),
                "description": tutorial_overview.get("description", "Comprehensive tutorial"),
                "project_name": project_name,
                "target_audience": tutorial_overview.get("target_audience", "Developers"),
                "estimated_duration": tutorial_overview.get("estimated_duration", "Several hours"),
                "prerequisites": tutorial_overview.get("prerequisites", "Basic programming knowledge"),
                "creation_date": "Generated by Intelligent Tutorial Generator"
            },
            "chapters": [
                {
                    "number": ch.get("chapter_number", 0),
                    "title": ch.get("title", "Unknown"),
                    "type": ch.get("type", "Core"),
                    "complexity": ch.get("complexity", "Intermediate"),
                    "estimated_time": ch.get("estimated_time", "20-30 minutes"),
                    "abstraction": ch.get("abstraction", ""),
                    "content_length": len(ch.get("content", "")),
                    "generated_successfully": ch.get("generated_successfully", False)
                }
                for ch in chapters
            ],
            "abstractions": [
                {
                    "name": abs.get("name", "Unknown"),
                    "type": abs.get("type", "Feature"),
                    "complexity": abs.get("complexity", "Intermediate"),
                    "description": abs.get("description", ""),
                    "files_involved": abs.get("files_involved", []),
                    "learning_value": abs.get("learning_value", ""),
                    "key_concepts": abs.get("key_concepts", [])
                }
                for abs in abstractions
            ],
            "statistics": {
                "total_chapters": len(chapters),
                "successful_generations": sum(1 for ch in chapters if ch.get("generated_successfully", False)),
                "total_abstractions": len(abstractions),
                "total_relationships": len(relationships.get("relationships", [])),
                "complexity_distribution": self._get_complexity_distribution(abstractions),
                "chapter_type_distribution": self._get_chapter_type_distribution(chapters),
                "total_content_length": sum(len(ch.get("content", "")) for ch in chapters),
                "average_chapter_length": sum(len(ch.get("content", "")) for ch in chapters) // len(chapters) if chapters else 0
            },
            "project_analysis": {
                "project_summary": relationships.get("project_summary", ""),
                "key_insights": relationships.get("key_insights", []),
                "learning_paths": relationships.get("learning_paths", {}),
                "strong_relationships": [
                    r for r in relationships.get("relationships", []) 
                    if r.get("strength") == "Strong"
                ]
            }
        }
    
    def _create_readme(self, tutorial_overview: Dict[str, Any], chapters: List[Dict[str, Any]], project_name: str) -> str:
        """Create README with setup and usage instructions"""
        
        total_chapters = len(chapters)
        estimated_duration = tutorial_overview.get("estimated_duration", "Several hours")
        
        return f"""# {project_name} Tutorial

{tutorial_overview.get('description', f'A comprehensive tutorial for understanding and working with {project_name}.')}

## 🚀 Quick Start

1. **Start Here**: Open [index.md](index.md) for the complete tutorial overview
2. **Follow the Path**: Work through chapters sequentially starting with Chapter 1
3. **Practice**: Complete all hands-on exercises for best results
4. **Reference**: Use [quick_reference.md](quick_reference.md) for quick concept lookups

## 📋 What You'll Learn

This tutorial covers {len(set(ch.get('abstraction', '') for ch in chapters))} key concepts across {total_chapters} structured chapters.

**Estimated Time**: {estimated_duration}

**Prerequisites**: {tutorial_overview.get('prerequisites', 'Basic programming knowledge')}

## 📁 Tutorial Structure

```
tutorial/
├── index.md              # Main tutorial overview and navigation
├── README.md             # This file - setup and usage
├── quick_reference.md    # Concept reference guide
├── tutorial_metadata.json # Structured tutorial data
"""
        
        # Add chapter file listing
        for chapter in chapters:
            num = chapter.get("chapter_number", "?")
            title = chapter.get("title", "Unknown")
            filename = f"{num:02d}_{self._sanitize_filename(title)}.md"
            readme_content = f"├── {filename}    # Chapter {num}: {title}\n"
        
        readme_content += f"""└── ...
```

## 🎯 Learning Approach

This tutorial is designed for:
- **Progressive Learning**: Each chapter builds on previous knowledge
- **Hands-On Practice**: Every chapter includes practical exercises
- **Real-World Application**: Examples come directly from the actual codebase
- **Flexible Pacing**: Estimated times help you plan your learning

## 📖 How to Use

### For Beginners
1. Start with the foundation chapters
2. Take your time with hands-on exercises
3. Don't skip the practice activities
4. Use the quick reference for concept reviews

### For Experienced Developers
1. Review the tutorial overview in [index.md](index.md)
2. Jump to chapters covering unfamiliar concepts
3. Focus on the architecture overview diagram
4. Use metadata file for structured information

## 🔧 Setup Requirements

- Text editor or IDE for viewing Markdown files
- Basic understanding of the project's programming language
- Access to the project codebase (for hands-on exercises)

## 📚 Additional Resources

- **Quick Reference**: [quick_reference.md](quick_reference.md) - All concepts at a glance
- **Metadata**: [tutorial_metadata.json](tutorial_metadata.json) - Machine-readable tutorial structure
- **Project Documentation**: Refer to original project docs for API details

## 🤝 Contributing

This tutorial was generated automatically by analyzing the codebase. If you find areas for improvement:

1. Check the original project documentation
2. Verify examples against the current codebase
3. Suggest updates based on project changes

## 📄 License

This tutorial follows the same license as the original {project_name} project.

---

**Happy Learning!** 🎉

Start your journey: [Open Tutorial Index](index.md)
"""
        
        return readme_content
    
    def _create_quick_reference(self, abstractions: List[Dict[str, Any]], relationships: Dict[str, Any]) -> str:
        """Create quick reference guide for all concepts"""
        
        reference_content = f"""# Quick Reference Guide

A condensed overview of all key concepts covered in this tutorial.

## 🏗️ Architecture Overview

{relationships.get('project_summary', 'Project contains multiple interconnected components.')}

## 📋 Key Concepts

"""
        
        # Group abstractions by complexity
        beginner_abs = [a for a in abstractions if a.get("complexity") == "Beginner"]
        intermediate_abs = [a for a in abstractions if a.get("complexity") == "Intermediate"]
        advanced_abs = [a for a in abstractions if a.get("complexity") == "Advanced"]
        
        if beginner_abs:
            reference_content += "### 🟢 Foundation Concepts (Beginner)\n\n"
            for abs in beginner_abs:
                reference_content += f"**{abs['name']}** ({abs.get('type', 'Feature')})\n"
                reference_content += f"- {abs.get('description', 'Core concept')}\n"
                if abs.get('key_concepts'):
                    reference_content += f"- Key points: {', '.join(abs['key_concepts'])}\n"
                reference_content += "\n"
        
        if intermediate_abs:
            reference_content += "### 🟡 Core Concepts (Intermediate)\n\n"
            for abs in intermediate_abs:
                reference_content += f"**{abs['name']}** ({abs.get('type', 'Feature')})\n"
                reference_content += f"- {abs.get('description', 'Core concept')}\n"
                if abs.get('key_concepts'):
                    reference_content += f"- Key points: {', '.join(abs['key_concepts'])}\n"
                reference_content += "\n"
        
        if advanced_abs:
            reference_content += "### 🔴 Advanced Concepts\n\n"
            for abs in advanced_abs:
                reference_content += f"**{abs['name']}** ({abs.get('type', 'Feature')})\n"
                reference_content += f"- {abs.get('description', 'Core concept')}\n"
                if abs.get('key_concepts'):
                    reference_content += f"- Key points: {', '.join(abs['key_concepts'])}\n"
                reference_content += "\n"
        
        # Add learning paths
        learning_paths = relationships.get("learning_paths", {})
        if learning_paths:
            reference_content += "## 🛤️ Learning Paths\n\n"
            
            for path_type, concepts in learning_paths.items():
                if concepts:
                    reference_content += f"**{path_type.title()}**: {' → '.join(concepts)}\n\n"
        
        # Add key insights
        key_insights = relationships.get("key_insights", [])
        if key_insights:
            reference_content += "## 💡 Key Project Insights\n\n"
            for insight in key_insights:
                reference_content += f"- {insight}\n"
            reference_content += "\n"
        
        # Add relationship summary
        relationship_list = relationships.get("relationships", [])
        if relationship_list:
            strong_relationships = [r for r in relationship_list if r.get("strength") == "Strong"]
            if strong_relationships:
                reference_content += "## 🔗 Critical Dependencies\n\n"
                reference_content += "*Understanding these relationships is essential for system comprehension:*\n\n"
                for rel in strong_relationships:
                    reference_content += f"- **{rel['from']}** → **{rel['to']}**: {rel.get('description', 'Important relationship')}\n"
                reference_content += "\n"
        
        reference_content += """## 📖 How to Use This Reference

- **Quick Lookup**: Find concepts by complexity level
- **Dependency Checking**: Use the relationships section to understand prerequisites
- **Learning Planning**: Follow the suggested learning paths
- **Concept Review**: Refresh your understanding of key points

## 🔄 Back to Tutorial

- [🏠 Tutorial Home](index.md)
- [📖 README](README.md)
- [📊 Tutorial Metadata](tutorial_metadata.json)

---

*This reference was generated from the complete codebase analysis.*
"""
        
        return reference_content
    
    def _get_complexity_distribution(self, abstractions: List[Dict[str, Any]]) -> Dict[str, int]:
        """Get distribution of complexity levels"""
        distribution = {"Beginner": 0, "Intermediate": 0, "Advanced": 0}
        for abstraction in abstractions:
            complexity = abstraction.get("complexity", "Intermediate")
            if complexity in distribution:
                distribution[complexity] += 1
        return distribution
    
    def _get_chapter_type_distribution(self, chapters: List[Dict[str, Any]]) -> Dict[str, int]:
        """Get distribution of chapter types"""
        distribution = {}
        for chapter in chapters:
            chapter_type = chapter.get("type", "Core")
            distribution[chapter_type] = distribution.get(chapter_type, 0) + 1
        return distribution
    
    def _create_combined_tutorial_content(self, tutorial_overview: Dict[str, Any], 
                                        enhanced_chapters: List[Dict[str, Any]],
                                        abstractions: List[Dict[str, Any]], 
                                        relationships: Dict[str, Any], 
                                        project_name: str) -> str:
        """Create a combined tutorial content with all chapters"""
        content_parts = []
        
        # Main title and overview
        content_parts.append(f"# {tutorial_overview.get('title', f'{project_name} Complete Tutorial')}")
        content_parts.append(f"{tutorial_overview.get('description', f'A comprehensive tutorial for understanding and working with {project_name}.')}")
        content_parts.append("---\n")
        
        # Table of contents
        content_parts.append("## 📚 Table of Contents\n")
        for chapter in enhanced_chapters:
            chapter_num = chapter.get('chapter_number', 0)
            title = chapter.get('title', f'Chapter {chapter_num}')
            content_parts.append(f"{chapter_num}. [{title}](#chapter-{chapter_num})")
        content_parts.append("\n---\n")
        
        # Project overview
        content_parts.append("## 🎯 Project Overview\n")
        content_parts.append(f"This tutorial covers {len(abstractions)} key concepts:")
        for abstraction in abstractions:
            name = abstraction.get('name', 'Unknown')
            description = abstraction.get('description', 'No description available')
            content_parts.append(f"- **{name}**: {description}")
        content_parts.append("\n---\n")
        
        # All chapters
        for chapter in enhanced_chapters:
            chapter_num = chapter.get('chapter_number', 0)
            title = chapter.get('title', f'Chapter {chapter_num}')
            content = chapter.get('enhanced_content', chapter.get('content', ''))
            
            # Add chapter anchor
            content_parts.append(f"## Chapter {chapter_num}: {title} {{#chapter-{chapter_num}}}")
            content_parts.append(content)
            content_parts.append("\n---\n")
        
        # Appendix with relationships
        if relationships:
            content_parts.append("## 🔗 Code Relationships\n")
            content_parts.append("The following relationships were identified in the codebase:\n")
            
            relationship_list = relationships.get("relationships", [])
            for rel in relationship_list:
                if isinstance(rel, dict):
                    source = rel.get('source', 'Unknown')
                    target = rel.get('target', 'Unknown')
                    rel_type = rel.get('type', 'related to')
                    content_parts.append(f"- **{source}** {rel_type} **{target}**")
                else:
                    content_parts.append(f"- {str(rel)}")
            content_parts.append("")
        
        return "\n".join(content_parts)
    
    def _print_tutorial_summary(self, shared: Dict[str, Any]):
        """Print comprehensive tutorial completion summary"""
        tutorial_complete = shared.get("tutorial_complete", {})
        chapters = shared.get("chapters", [])
        abstractions = shared.get("abstractions", [])
        
        print(f"    🎊 TUTORIAL CONTENT GENERATION COMPLETE!")
        print(f"      • Content Types Generated: {tutorial_complete.get('content_types', 0)}")
        print(f"      • Chapters Created: {len(chapters)}")
        print(f"      • Abstractions Covered: {len(abstractions)}")
        print(f"      • Success Rate: {sum(1 for ch in chapters if ch.get('generated_successfully', False))}/{len(chapters)} chapters")
        
        # Content statistics
        total_content = sum(len(ch.get('content', '')) for ch in chapters)
        avg_content = total_content // len(chapters) if chapters else 0
        print(f"      • Total Content: {total_content:,} characters")
        print(f"      • Average Chapter: {avg_content:,} characters")
        
        # Content types available
        content_types = []
        if shared.get("tutorial_content"):
            content_types.append("Combined Tutorial")
        if shared.get("index_content"):
            content_types.append("Index")
        if shared.get("readme_content"):
            content_types.append("README")
        if shared.get("quick_reference_content"):
            content_types.append("Quick Reference")
        
        print(f"      • Available Content: {', '.join(content_types)}")
        print(f"    🚀 Content ready for frontend consumption!")
