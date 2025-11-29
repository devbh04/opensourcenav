# tutorial_generator.py - Enhanced with comprehensive LLM call tracking
import json
import re
import time
from typing import List, Dict, Any

from langchain_google_genai import ChatGoogleGenerativeAI
from app.utils.config import GEMINI_API_KEY
from app.utils.llm_tracker import tracked_llm_call, tracker

# Initialize the LLM
llm = ChatGoogleGenerativeAI(model="models/gemini-2.0-flash", google_api_key=GEMINI_API_KEY)

# --- Helper Functions ---

def _invoke_llm_with_json_parsing(prompt: str, attempt=1) -> Any:
    """Enhanced LLM invocation with comprehensive tracking and JSON parsing."""
    if attempt > 3:
        print("[ERROR] Failed to parse JSON after 3 attempts.")
        return None
    try:
        # Use tracked LLM call for comprehensive monitoring
        response = tracked_llm_call(
            module="tutorial_generator",
            function="_invoke_llm_with_json_parsing",
            model="models/gemini-2.0-flash",
            llm_instance=llm,
            prompt=prompt
        )
        
        content = response.content if hasattr(response, "content") else str(response)
        
        json_start = -1
        json_end = -1
        if '[' in content and ']' in content:
            json_start = content.find('[')
            json_end = content.rfind(']') + 1
        elif '{' in content and '}' in content:
            json_start = content.find('{')
            json_end = content.rfind('}') + 1

        if json_start != -1:
            json_str = content[json_start:json_end]
            return json.loads(json_str)
        else:
            print(f"[WARNING] No JSON object/array found in response on attempt {attempt}. Retrying...")
            return _invoke_llm_with_json_parsing(prompt, attempt + 1)
            
    except json.JSONDecodeError:
        print(f"[WARNING] Failed to decode JSON on attempt {attempt}. Response was:\n{content}\nRetrying...")
        return _invoke_llm_with_json_parsing(prompt, attempt + 1)
    except Exception as e:
        print(f"[ERROR] An unexpected error occurred during LLM invocation: {e}")
        return None

def _create_code_overview(chunks: List[Dict]) -> str:
    """Creates a structured, high-level overview of the repository's code."""
    file_tree = {}
    important_files = []
    
    processed_paths = set()
    for chunk in chunks:
        path = chunk.get('original_file', chunk.get('file'))
        if path in processed_paths:
            continue
        processed_paths.add(path)

        parts = path.split('/')
        current_level = file_tree
        for part in parts[:-1]:
            current_level = current_level.setdefault(part, {})
        current_level[parts[-1]] = None

        if chunk.get('importance', 0) >= 8:
            important_files.append({'path': path, 'type': chunk.get('file_type')})

    def format_tree(d, indent=0):
        lines = []
        for key, value in sorted(d.items()):
            lines.append('  ' * indent + f'- {key}')
            if isinstance(value, dict):
                lines.extend(format_tree(value, indent + 1))
        return lines

    overview = ["# Repository Overview", "## Directory Structure"]
    overview.extend(format_tree(file_tree))
    overview.append("\n## Key Files (by estimated importance)")
    for f in sorted(important_files, key=lambda x: x['path']):
        overview.append(f"- {f['path']} (type: {f['type']})")
        
    return "\n".join(overview)

def _get_mermaid_examples_and_rules() -> str:
    """Provide comprehensive Mermaid examples and syntax rules for the LLM."""
    return """
**🎯 MERMAID SYNTAX EXAMPLES & RULES - GITHUB SUPPORTED ONLY**

**✅ GITHUB-SUPPORTED DIAGRAM TYPES ONLY:**

**1. Flowchart (for architecture/workflow):**
```mermaid
flowchart TD
    A[Start] --> B{Is it working?}
    B -- Yes --> C[Great!]
    B -- No --> D[Fix it]
    D --> B
```

**2. System Architecture (flowchart LR):**
```mermaid
flowchart LR
    subgraph Frontend_Layer
        UI[User Interface]
        Components[UI Components]
    end
    subgraph Backend_Layer
        API[API Layer]
        Services[Business Services]
    end
    UI --> API
    API --> Services
    
    classDef frontend fill:#e1f5fe,stroke:#333,stroke-width:2px;
    classDef backend fill:#f3e5f5,stroke:#333,stroke-width:2px;
    class UI,Components frontend;
    class API,Services backend;
```

**3. Sequence Diagram (for interactions):**
```mermaid
sequenceDiagram
    participant User
    participant App
    participant DB
    User->>App: Sends request
    App->>DB: Queries data
    DB-->>App: Returns data
    App-->>User: Sends response
```

**4. Class Diagram (for object relationships):**
```mermaid
classDiagram
    class Component {{
        +String name
        +render()
    }}
    class Button {{
        +onClick()
    }}
    Component <|-- Button
```

**5. State Diagram (for state transitions):**
```mermaid
stateDiagram-v2
    [*] --> Idle
    Idle --> Running : Start
    Running --> Idle : Stop
    Running --> Error : Crash
    Error --> Idle : Reset
```

**6. Entity Relationship Diagram (for data models):**
```mermaid
erDiagram
    USERS ||--o{ ORDERS : places
    ORDERS ||--|{ LINE_ITEMS : contains
    PRODUCTS ||--|{ LINE_ITEMS : includes
```

**7. Gantt Chart (for project timelines):**
```mermaid
gantt
    title Project Timeline
    dateFormat  YYYY-MM-DD
    section Planning
    Requirements     :a1, 2025-07-01, 7d
    Design           :after a1, 5d
    section Development
    Implementation   :2025-07-10, 10d
    Testing          :after Implementation, 5d
```

**8. Pie Chart (for data distribution):**
```mermaid
pie title Technology Stack
    "JavaScript" : 35
    "Python" : 30
    "Java" : 15
    "C++" : 10
    "Others" : 10
```

**9. Git Graph (for version control workflows):**
```mermaid
gitGraph
   commit
   commit
   branch develop
   checkout develop
   commit
   commit
   checkout main
   merge develop
```

**🚫 CRITICAL SYNTAX RULES - MUST FOLLOW TO PREVENT PARSE ERRORS:**

**NODE SYNTAX (CRITICAL):**
- Use quotes for ALL node labels: A["Simple Label"] 
- NO parentheses in node labels: A["React Component"] NOT A["React Component (ThreeDMarquee)"]
- NO special characters in node IDs: Use A, B, C or Frontend, Backend NOT Front-end
- Clean node labels: Remove (, ), :, ;, |, special unicode

**SEQUENCE DIAGRAM SYNTAX (CRITICAL):**
- Use ->> for sequence arrows: User->>App: Message
- NO --> arrows in sequence diagrams (use ->> instead)
- NO spaces in participant names: participant User_Interface NOT participant User Interface
- Clean participant names: participant RSC NOT participant "React Server Component"

**FLOWCHART SYNTAX (CRITICAL):**
- Use --> for flowchart arrows: A --> B
- Proper spacing: A --> B NOT A-->B or A--> B
- Quote complex labels: A["Complex Label"] 
- NO parentheses: A["User Interface"] NOT A["User Interface (Main)"]

**SUBGRAPH SYNTAX:**
- Use underscores: subgraph Frontend_Layer NOT subgraph "Frontend Layer"
- NO special characters in subgraph names

**EXAMPLES OF CORRECT VS INCORRECT:**

❌ WRONG (causes parse errors):
```
A[React Component (ThreeDMarquee)] --> B
RSC --> RCC: Hydration end
participant "User Interface"
```

✅ CORRECT:
```
A["React Component ThreeDMarquee"] --> B  
RSC->>RCC: Hydration end
participant User_Interface
```

**🚫 CRITICAL SYNTAX RULES:**
- Use square brackets for node labels: A["Label"]
- NO special characters in node IDs (no spaces, parentheses, colons)
- Use underscores in subgraph names: Frontend_Layer not "Frontend Layer"
- End classDef with semicolon: classDef frontend fill:#color;
- Apply classes: class NodeA,NodeB classname;
- NO ::: syntax (INVALID)
- NO timeline diagrams (NOT supported by GitHub)
- NO mindmap diagrams (NOT supported by GitHub)

**🎯 KEEP DIAGRAMS SIMPLE:**
- Max 5-8 nodes per diagram
- Focus on key relationships only
- Use clear, descriptive labels
- Choose appropriate diagram type for content
- Avoid overly complex structures

**📋 GITHUB-SUPPORTED DIAGRAM SELECTION GUIDE:**
- **Flowchart**: Architecture, processes, decision flows (most versatile)
- **Sequence**: API calls, user interactions, data flow between components
- **Class**: Object relationships, inheritance, system structure
- **State**: Component states, workflow states, process states
- **Entity Relationship**: Database design, data models
- **Gantt**: Project timelines, learning phases, development roadmap
- **Pie**: Technology stack breakdown, component distribution
- **Git Graph**: Version control workflows, branching strategies

**⚠️ UNSUPPORTED DIAGRAMS (DO NOT USE):**
- Timeline diagrams (use Gantt instead)
- Mindmap diagrams (use Flowchart instead)
- Requirement diagrams
- Journey diagrams
- C4 diagrams

**CRITICAL**: Only use the 9 GitHub-supported diagram types listed above!
"""

def _generate_mermaid_architecture_diagram(chunks: List[Dict], abstractions: List[Dict], relationships: List[Dict]) -> str:
    """Generate a comprehensive Mermaid architecture diagram for the project."""
    mermaid_guide = _get_mermaid_examples_and_rules()
    
    prompt = f"""
**ROLE**: You are a senior software architect creating SIMPLE, FOCUSED Mermaid diagrams for learning purposes.

**TASK**: Create a HIGH-LEVEL project architecture diagram that shows main components and their relationships.

**PROJECT DATA**:
Repository Structure:
{_create_code_overview(chunks)}

Key Abstractions (limit to 3-5 most important):
{json.dumps(abstractions[:5], indent=2)}

Component Relationships:
{json.dumps(relationships[:8], indent=2)}

{mermaid_guide}

**SPECIFIC REQUIREMENTS FOR THIS DIAGRAM**:
1. Show 4-6 main architectural layers/components ONLY
2. Use flowchart TD or LR format
3. Keep it SIMPLE - focus on high-level understanding
4. Group related components into subgraphs
5. Show only the most important data flows

**EXAMPLE OUTPUT:**
```mermaid
flowchart TD
    subgraph UI_Layer
        Interface[User Interface]
        Components[UI Components]
    end
    subgraph API_Layer
        Endpoints[API Endpoints]
        Validation[Data Validation]
    end
    subgraph Data_Layer
        Storage[Data Storage]
    end
    
    Interface --> Endpoints
    Endpoints --> Validation
    Validation --> Storage
    
    classDef ui fill:#e1f5fe,stroke:#333,stroke-width:2px;
    classDef api fill:#f3e5f5,stroke:#333,stroke-width:2px;
    classDef data fill:#e8f5e8,stroke:#333,stroke-width:2px;
    
    class Interface,Components ui;
    class Endpoints,Validation api;
    class Storage data;
```

**CRITICAL**: 
- Return ONLY the mermaid code block
- Keep it SIMPLE (max 6-8 nodes)
- Use VALID syntax from examples above
- Focus on MAIN architectural components only
"""
    
    try:
        response = tracked_llm_call(
            module="tutorial_generator",
            function="_generate_mermaid_architecture_diagram",
            model="models/gemini-2.0-flash",
            llm_instance=llm,
            prompt=prompt
        )
        
        content = response.content if hasattr(response, "content") else str(response)
        
        # Extract Mermaid code block
        if "```mermaid" in content:
            start = content.find("```mermaid") + 10
            end = content.find("```", start)
            if end != -1:
                mermaid_code = content[start:end].strip()
                
                # Validate and clean up common syntax issues
                mermaid_code = _validate_and_fix_mermaid_syntax(mermaid_code)
                return mermaid_code
        
        # Fallback if extraction fails
        return _create_fallback_mermaid_diagram()
        
    except Exception as e:
        print(f"[ERROR] Failed to generate Mermaid diagram: {e}")
        return _create_fallback_mermaid_diagram()

def _validate_and_fix_mermaid_syntax(mermaid_code: str) -> str:
    """Enhanced validation and fixing of Mermaid syntax issues."""
    try:
        import re
        
        print(f"[DEBUG] Validating Mermaid syntax: {len(mermaid_code)} characters")
        
        # Remove invalid ::: syntax
        mermaid_code = mermaid_code.replace(":::", "")
        
        # Remove unsupported diagram types
        unsupported_patterns = [
            r'timeline\s*\n',
            r'mindmap\s*\n',
            r'journey\s*\n',
            r'requirement\s*\n',
            r'quadrantChart\s*\n'
        ]
        for pattern in unsupported_patterns:
            if re.search(pattern, mermaid_code, re.IGNORECASE):
                print(f"[WARNING] Unsupported diagram type found, replacing with flowchart")
                return _create_fallback_mermaid_diagram()
        
        # CRITICAL FIX: Handle problematic node labels with parentheses and special characters
        # Fix: A[React Component (ThreeDMarquee)] --> should be A["React Component ThreeDMarquee"] -->
        mermaid_code = re.sub(r'([A-Za-z0-9_]+)\[([^\]]*\([^\]]*\)[^\]]*)\]', r'\1["\2"]', mermaid_code)
        
        # CRITICAL FIX: Remove parentheses from node labels to prevent parse errors
        # Replace text in brackets that contains parentheses
        def clean_node_label(match):
            node_id = match.group(1)
            label = match.group(2)
            # Remove parentheses and clean up the label
            clean_label = label.replace('(', '').replace(')', '').strip()
            # Remove extra spaces
            clean_label = re.sub(r'\s+', ' ', clean_label)
            return f'{node_id}["{clean_label}"]'
        
        mermaid_code = re.sub(r'([A-Za-z0-9_]+)\[([^\]]+)\]', clean_node_label, mermaid_code)
        
        # CRITICAL FIX: Sequence diagram participant and message syntax
        if 'sequenceDiagram' in mermaid_code:
            # Fix participant names with special characters and spaces
            mermaid_code = re.sub(r'participant\s+([^\n]+)', lambda m: f'participant {m.group(1).replace(" ", "_").replace("(", "").replace(")", "")}', mermaid_code)
            
            # CRITICAL FIX: Sequence diagram arrow syntax - fix the specific error pattern
            # Fix: RSC --> RCC: Hydration end
            # Ensure proper spacing and no invalid characters
            lines = mermaid_code.split('\n')
            fixed_lines = []
            for line in lines:
                # Fix sequence diagram message syntax
                if '-->' in line and ':' in line:
                    # Pattern: participant1 --> participant2: message
                    # Make sure participants don't have spaces or special chars
                    if re.match(r'\s*\w+\s*-->\s*\w+\s*:', line):
                        # Clean participant names
                        line = re.sub(r'([A-Za-z0-9_]+)\s*-->\s*([A-Za-z0-9_]+)\s*:\s*(.+)', r'\1-->>\2: \3', line)
                        # Replace --> with ->> for sequence diagrams
                        line = line.replace('-->>', '->>')
                    else:
                        # If pattern doesn't match, try to fix it
                        parts = line.split('-->')
                        if len(parts) == 2 and ':' in parts[1]:
                            left = parts[0].strip().replace(' ', '_').replace('(', '').replace(')', '')
                            right_parts = parts[1].split(':', 1)
                            right_participant = right_parts[0].strip().replace(' ', '_').replace('(', '').replace(')', '')
                            message = right_parts[1].strip() if len(right_parts) > 1 else ''
                            line = f"    {left}->>{right_participant}: {message}"
                elif '->' in line and 'sequenceDiagram' not in line:
                    # Fix other arrow types in sequence diagrams
                    line = re.sub(r'([A-Za-z0-9_]+)\s*->\s*([A-Za-z0-9_]+)', r'\1->>\2', line)
                
                fixed_lines.append(line)
            mermaid_code = '\n'.join(fixed_lines)
        
        # Fix subgraph names (remove spaces and special chars)
        mermaid_code = re.sub(r'subgraph\s+"([^"]+)"', lambda m: f'subgraph {m.group(1).replace(" ", "_")}', mermaid_code)
        mermaid_code = re.sub(r'subgraph\s+([^\s\n\[]+)\s+\[([^\]]+)\]', r'subgraph \1\n        \2', mermaid_code)
        
        # Ensure classDef statements end with semicolons
        mermaid_code = re.sub(r'classDef\s+([^\n]+?)(?<!;)\s*$', r'classDef \1;', mermaid_code, flags=re.MULTILINE)
        
        # Ensure class statements end with semicolons  
        mermaid_code = re.sub(r'class\s+([^\n]+?)(?<!;)\s*$', r'class \1;', mermaid_code, flags=re.MULTILINE)
        
        # CRITICAL FIX: Standardize arrow syntax for flowcharts
        # Only for flowchart diagrams, not sequence diagrams
        if mermaid_code.strip().startswith('flowchart'):
            # Fix flowchart arrows - ensure proper spacing
            mermaid_code = re.sub(r'(\w+)\s*-->\s*(\w+)', r'\1 --> \2', mermaid_code)
            mermaid_code = re.sub(r'(\w+)\s*\.\.>\s*(\w+)', r'\1 ..> \2', mermaid_code)
            mermaid_code = re.sub(r'(\w+)\s*==>\s*(\w+)', r'\1 ==> \2', mermaid_code)
        
        # CRITICAL FIX: Remove any remaining problematic characters
        # Remove any line that might cause parse errors
        lines = mermaid_code.split('\n')
        safe_lines = []
        for line in lines:
            # Skip lines with potential problematic patterns
            if re.search(r'[^\w\s\[\]"():.>-]+', line) and not any(keyword in line for keyword in ['classDef', 'class', 'fill:', 'stroke:']):
                print(f"[WARNING] Skipping potentially problematic line: {line.strip()}")
                continue
            safe_lines.append(line)
        mermaid_code = '\n'.join(safe_lines)
        
        # Validate basic structure
        first_line = mermaid_code.split('\n')[0].strip() if mermaid_code.strip() else ""
        valid_starts = ['flowchart', 'sequenceDiagram', 'classDiagram', 'stateDiagram-v2', 'erDiagram', 'gantt', 'pie', 'gitGraph']
        
        if not any(first_line.startswith(start) for start in valid_starts):
            print(f"[WARNING] Invalid diagram type '{first_line}', using fallback flowchart")
            return _create_fallback_mermaid_diagram()
        
        print(f"[SUCCESS] Mermaid syntax validation complete")
        return mermaid_code
        
    except Exception as e:
        print(f"[WARNING] Failed to validate Mermaid syntax: {e}")
        return mermaid_code

def _create_fallback_mermaid_diagram() -> str:
    """Create a simple fallback Mermaid diagram."""
    return """flowchart TD
    subgraph Frontend_Layer
        UI["User Interface"]
        Components["UI Components"]
    end
    
    subgraph Backend_Layer
        API["API Layer"]
        Services["Business Services"]
    end
    
    subgraph Data_Layer
        Database["Data Storage"]
    end
    
    UI --> Components
    Components --> API
    API --> Services
    Services --> Database
    
    classDef frontend fill:#e1f5fe,stroke:#333,stroke-width:2px;
    classDef backend fill:#f3e5f5,stroke:#333,stroke-width:2px;
    classDef data fill:#e8f5e8,stroke:#333,stroke-width:2px;
    
    class UI,Components frontend;
    class API,Services backend;
    class Database data;"""

def _create_project_overview_chapter(chunks: List[Dict], abstractions: List[Dict], relationships: List[Dict]) -> Dict[str, Any]:
    """Create a comprehensive project overview chapter with Mermaid diagram."""
    architecture_diagram = _generate_mermaid_architecture_diagram(chunks, abstractions, relationships)
    
    # Extract project name from file paths
    project_name = "Project"
    if chunks:
        first_path = chunks[0].get('original_file', chunks[0].get('file', ''))
        if '/' in first_path:
            project_name = first_path.split('/')[0].replace('-', ' ').replace('_', ' ').title()
    
    overview_chapter = {
        "chapter": 0,
        "title": f"{project_name} Overview",
        "objective": f"Understand the overall architecture and key components of {project_name}",
        "chapter_type": "Overview",
        "estimated_time": "15-20 minutes",
        "architecture_diagram": architecture_diagram,
        "abstractions_count": len(abstractions),
        "relationships_count": len(relationships),
        "hands_on_activity": "Explore the project structure and identify key components",
        "success_criteria": "Can explain the main architectural layers and component interactions"
    }
    
    return overview_chapter

def _generate_chapter_specific_diagram(chapter_def: Dict, abstractions: List[Dict], relationships: List[Dict]) -> str:
    """Generate a Mermaid diagram specific to a chapter's content."""
    chapter_title = chapter_def.get('title', 'Chapter')
    chapter_abstractions = chapter_def.get('concepts_covered', [])
    
    # Find relevant relationships for this chapter
    relevant_relationships = []
    for rel in relationships:
        if (rel.get('from') in chapter_abstractions or 
            rel.get('to') in chapter_abstractions):
            relevant_relationships.append(rel)
    
    if not chapter_abstractions and not relevant_relationships:
        return ""  # No diagram needed
    
    mermaid_guide = _get_mermaid_examples_and_rules()
    
    prompt = f"""
**ROLE**: Educational diagram specialist creating SIMPLE, FOCUSED Mermaid diagrams for tutorial chapters.

**TASK**: Create a targeted Mermaid diagram for the chapter "{chapter_title}" that helps learners understand the key concepts.

**CHAPTER INFORMATION**:
Chapter Title: {chapter_title}
Chapter Type: {chapter_def.get('chapter_type', 'Unknown')}
Key Concepts: {chapter_abstractions}
Relevant Relationships: {json.dumps(relevant_relationships, indent=2)}

{mermaid_guide}

**CHOOSE THE BEST GITHUB-SUPPORTED DIAGRAM TYPE FOR THIS CHAPTER:**

**For Foundation/Overview chapters** → Use flowchart or state diagram:
```mermaid
flowchart TD
    Start[Foundation Concepts] --> Core[Core Understanding]
    Core --> Apply[Application]
    Apply --> Master[Mastery]
```

**For Process/Workflow chapters** → Use flowchart or sequence diagram:
```mermaid
flowchart TD
    Begin[Start Process] --> Step1[First Step]
    Step1 --> Step2[Second Step]
    Step2 --> Complete[Finish]
```

**For API/Integration chapters** → Use sequence diagram:
```mermaid
sequenceDiagram
    User->>API: Request
    API->>Service: Process
    Service-->>API: Response
    API-->>User: Result
```

**For Learning Path chapters** → Use gantt chart:
```mermaid
gantt
    title Chapter Learning Path
    dateFormat  YYYY-MM-DD
    section Learn
    Prerequisites  :2025-07-01, 2d
    Core Concepts  :2025-07-03, 3d
    section Practice
    Implementation :2025-07-06, 2d
    Testing        :2025-07-08, 1d
```

**For Object/System Structure** → Use class diagram:
```mermaid
classDiagram
    class MainConcept {{
        +property1
        +method1()
    }}
    class SubConcept {{
        +property2
        +method2()
    }}
    MainConcept <|-- SubConcept
```

**For State Management** → Use state diagram:
```mermaid
stateDiagram-v2
    [*] --> Learning
    Learning --> Understanding
    Understanding --> Applying
    Applying --> Mastery
```

**REQUIREMENTS**:
- Use ONLY GitHub-supported diagram types: flowchart, sequenceDiagram, classDiagram, stateDiagram-v2, erDiagram, gantt, pie, gitGraph
- Keep it SIMPLE (3-6 nodes max)
- Focus on THIS chapter's concepts only
- Choose appropriate diagram type for content
- Use clear, beginner-friendly labels
- Make it educational, not decorative

**CRITICAL**: Return ONLY the mermaid code block, nothing else.
"""
    
    try:
        response = tracked_llm_call(
            module="tutorial_generator",
            function="_generate_chapter_specific_diagram",
            model="models/gemini-2.0-flash",
            llm_instance=llm,
            prompt=prompt
        )
        
        content = response.content if hasattr(response, "content") else str(response)
        
        # Extract Mermaid code block
        if "```mermaid" in content:
            start = content.find("```mermaid") + 10
            end = content.find("```", start)
            if end != -1:
                mermaid_code = content[start:end].strip()
                
                # Validate and clean up common syntax issues
                mermaid_code = _validate_and_fix_mermaid_syntax(mermaid_code)
                return mermaid_code
        
        return content.strip()
        
    except Exception as e:
        print(f"[WARNING] Failed to generate chapter diagram: {e}")
        return ""

def _create_simple_chapter_diagram(title: str) -> str:
    """Create a simple fallback diagram for a chapter."""
    chapter_name = title.split(':')[0].replace(' ', '_')
    return f"""flowchart LR
    Start["📚 {chapter_name}"]
    Concepts["🧠 Key Concepts"]
    Practice["💻 Hands-on Practice"]
    Summary["✅ Summary"]
    
    Start --> Concepts
    Concepts --> Practice
    Practice --> Summary
    
    classDef chapter fill:#e1f5fe,stroke:#333,stroke-width:2px;
    class Start,Concepts,Practice,Summary chapter;"""

# --- TutorialGenerator Class ---

class TutorialGenerator:
    """
    Generates a structured, multi-chapter tutorial for a codebase
    using a 6-step, LLM-driven process.
    """
    def __init__(self, chunks: List[Dict]):
        self.chunks = chunks
        self.abstractions = []
        self.relationships = []
        self.chapter_plan = []
        self.full_tutorial_content = {}
        self.rate_limit_pause_seconds = 60 

    def generate_tutorial(self) -> Dict[str, Any]:
        """Enhanced 6-step tutorial generation with expert prompting, quality assessment, and Mermaid diagrams."""
        print("="*60)
        print("[INFO] 🚀 Starting Enhanced Tutorial Generation with Expert Prompting & Mermaid Diagrams")
        print("="*60)

        print(f"[INFO] [1/6] FetchRepo: Processing {len(self.chunks)} code chunks...")
        code_overview = _create_code_overview(self.chunks)
        print(f"    ✅ Repository overview created ({len(code_overview)} characters)")

        print(f"[INFO] [2/6] IdentifyAbstractions: Using enhanced abstraction identification...")
        self.abstractions = self._identify_abstractions(code_overview)
        if not self.abstractions: 
            raise Exception("Failed to identify any abstractions.")
        print(f"    ✅ Identified {len(self.abstractions)} key abstractions using expert prompting")

        print(f"[INFO] [3/6] AnalyzeRelationships: Enhanced relationship mapping...")
        self.relationships = self._analyze_relationships()
        if not self.relationships: 
            print("    ⚠️  WARNING: Could not determine relationships.")
        else: 
            print(f"    ✅ Analyzed {len(self.relationships)} relationships with dependency analysis")

        print(f"[INFO] [4/6] OrderChapters: Expert instructional design sequencing with overview chapter...")
        # Create project overview chapter first
        overview_chapter = _create_project_overview_chapter(self.chunks, self.abstractions, self.relationships)
        self.chapter_plan = self._order_chapters()
        if not self.chapter_plan: 
            raise Exception("Failed to create a chapter plan.")
        # Insert overview chapter at the beginning
        self.chapter_plan.insert(0, overview_chapter)
        # Renumber chapters
        for i, chapter in enumerate(self.chapter_plan):
            chapter['chapter'] = i + 1
        print(f"    ✅ Created tutorial plan with project overview + {len(self.chapter_plan)-1} chapters using pedagogical principles")
        
        print(f"[INFO] [5/6] WriteChapters: Enhanced content generation with expert prompting and Mermaid diagrams...")
        self.full_tutorial_content = self._write_all_chapters()
        print(f"    ✅ Generated comprehensive content for all {len(self.chapter_plan)} chapters with visual diagrams")

        print(f"[INFO] [6/6] CombineTutorial: Assembling enhanced tutorial structure...")
        final_tutorial = self._combine_tutorial()
        
        # Quality assessment
        self._assess_tutorial_quality(final_tutorial)
        
        print("="*60)
        print("[SUCCESS] 🎉 Enhanced Tutorial Generation Complete with Mermaid Diagrams!")
        print("="*60)
        
        return final_tutorial
    
    def _assess_tutorial_quality(self, tutorial: Dict[str, Any]) -> None:
        """Comprehensive quality assessment of generated tutorial."""
        print("\n[INFO] 📊 Performing Tutorial Quality Assessment...")
        
        # Basic metrics
        total_chapters = tutorial.get('total_chapters', 0)
        total_content_length = sum(len(content) for content in self.full_tutorial_content.values())
        
        # Chapter analysis
        foundation_chapters = len([c for c in self.chapter_plan if c.get('chapter_type') == 'Foundation'])
        core_chapters = len([c for c in self.chapter_plan if c.get('chapter_type') == 'Core'])
        advanced_chapters = len([c for c in self.chapter_plan if c.get('chapter_type') == 'Advanced'])
        
        # Content quality checks
        chapters_with_code = sum(1 for content in self.full_tutorial_content.values() if '```' in content)
        chapters_with_exercises = sum(1 for c in self.chapter_plan if c.get('hands_on_activity'))
        chapters_with_objectives = sum(1 for c in self.chapter_plan if c.get('objective'))
        
        print(f"    📈 TUTORIAL METRICS:")
        print(f"      • Total Chapters: {total_chapters}")
        print(f"      • Total Content: {total_content_length:,} characters")
        print(f"      • Chapter Distribution: {foundation_chapters} Foundation, {core_chapters} Core, {advanced_chapters} Advanced")
        print(f"      • Code Examples: {chapters_with_code}/{total_chapters} chapters")
        print(f"      • Hands-on Activities: {chapters_with_exercises}/{total_chapters} chapters")
        print(f"      • Learning Objectives: {chapters_with_objectives}/{total_chapters} chapters")
        
        # Quality scoring
        quality_score = 0
        max_score = 100
        
        # Content completeness (30 points)
        if chapters_with_code == total_chapters: quality_score += 15
        elif chapters_with_code >= total_chapters * 0.8: quality_score += 10
        elif chapters_with_code >= total_chapters * 0.6: quality_score += 5
        
        if chapters_with_exercises >= total_chapters * 0.9: quality_score += 15
        elif chapters_with_exercises >= total_chapters * 0.7: quality_score += 10
        elif chapters_with_exercises >= total_chapters * 0.5: quality_score += 5
        
        # Structure quality (25 points)
        if foundation_chapters >= 1: quality_score += 10
        if core_chapters >= 2: quality_score += 10
        if total_chapters >= 4 and total_chapters <= 12: quality_score += 5
        
        # Learning design (25 points)
        if chapters_with_objectives == total_chapters: quality_score += 15
        elif chapters_with_objectives >= total_chapters * 0.9: quality_score += 10
        elif chapters_with_objectives >= total_chapters * 0.7: quality_score += 5
        
        time_estimates = sum(1 for c in self.chapter_plan if c.get('estimated_time'))
        if time_estimates == total_chapters: quality_score += 10
        elif time_estimates >= total_chapters * 0.8: quality_score += 5
        
        # Content depth (20 points)
        avg_chapter_length = total_content_length / total_chapters if total_chapters > 0 else 0
        if avg_chapter_length >= 2000: quality_score += 20
        elif avg_chapter_length >= 1500: quality_score += 15
        elif avg_chapter_length >= 1000: quality_score += 10
        elif avg_chapter_length >= 500: quality_score += 5
        
        print(f"    🎯 QUALITY SCORE: {quality_score}/{max_score} ({quality_score/max_score*100:.1f}%)")
        
        # Quality assessment
        if quality_score >= 85:
            print(f"    ✅ EXCELLENT: Tutorial meets high-quality standards")
        elif quality_score >= 70:
            print(f"    ✅ GOOD: Tutorial meets acceptable quality standards")
        elif quality_score >= 55:
            print(f"    ⚠️  FAIR: Tutorial has room for improvement")
        else:
            print(f"    ❌ NEEDS IMPROVEMENT: Tutorial quality below standards")
        
        # Specific recommendations
        recommendations = []
        if chapters_with_code < total_chapters:
            recommendations.append(f"Add code examples to {total_chapters - chapters_with_code} chapters")
        if chapters_with_exercises < total_chapters * 0.8:
            recommendations.append(f"Add hands-on activities to more chapters")
        if avg_chapter_length < 1000:
            recommendations.append(f"Expand chapter content (current avg: {avg_chapter_length:.0f} chars)")
        if foundation_chapters == 0:
            recommendations.append(f"Add foundation chapters for better learning progression")
            
        if recommendations:
            print(f"    💡 RECOMMENDATIONS:")
            for i, rec in enumerate(recommendations, 1):
                print(f"      {i}. {rec}")
        
        print(f"    📝 Tutorial ready for review and deployment")

    def _identify_abstractions(self, code_overview: str) -> List[Dict]:
        """Step 2: Enhanced abstraction identification using expert prompt engineering."""
        print("[INFO] Using enhanced abstraction identification with expert prompting...")
        
        prompt = f"""
**ROLE**: You are a senior software architect and technical educator with 15+ years of experience analyzing codebases and teaching developers.

**TASK**: Analyze the provided repository to identify core technical abstractions that form the foundation of an effective learning curriculum.

**THINK STEP BY STEP**:
1. First, scan for architectural patterns (MVC, microservices, event-driven, etc.)
2. Next, identify key functional domains (authentication, data processing, API layers)
3. Then, map dependencies and data flow between components
4. Finally, assess complexity levels for pedagogical ordering

**CONTEXT**: 
{code_overview}

**OUTPUT FORMAT**: JSON array with this exact structure:
[
  {{
    "name": "Specific, descriptive name (not generic)",
    "type": "Architecture|Feature|Workflow|Integration|Data",
    "description": "One clear sentence explaining purpose and value",
    "files_involved": ["exact/file/paths/from/overview"],
    "complexity": "Beginner|Intermediate|Advanced",
    "prerequisites": ["other abstraction names this depends on"],
    "learning_value": "Why this matters for understanding the system",
    "hands_on_potential": "What developers can immediately try with this concept"
  }}
]

**QUALITY CRITERIA**:
- Names should be specific: "JWT Authentication Middleware" not "Authentication"
- Include 5-12 abstractions (enough for comprehensive coverage, not overwhelming)
- Balance across complexity levels (30% Beginner, 50% Intermediate, 20% Advanced)
- Focus on concepts that directly impact daily development work
- Each abstraction should have clear practical application

**EXAMPLE GOOD ABSTRACTION**:
{{
  "name": "FastAPI Request/Response Pipeline with Pydantic Validation",
  "type": "Feature",
  "description": "Handles HTTP request validation, processing, and structured response generation using FastAPI and Pydantic models.",
  "files_involved": ["app/main.py", "app/models.py"],
  "complexity": "Intermediate",
  "prerequisites": ["HTTP REST API Fundamentals"],
  "learning_value": "Core pattern for all API endpoints - understanding this enables working with any endpoint",
  "hands_on_potential": "Create new validated endpoints, test request/response flow"
}}

**EXAMPLE POOR ABSTRACTION**:
{{
  "name": "API",
  "type": "Feature", 
  "description": "The API layer",
  "files_involved": ["various files"],
  "complexity": "Beginner"
}}

CRITICAL: Return ONLY the JSON array. No other text.
"""
        
        result = _invoke_llm_with_json_parsing(prompt)
        if result:
            print(f"[SUCCESS] Enhanced abstraction identification complete - found {len(result)} abstractions")
            for i, abstraction in enumerate(result[:3]):  # Show first 3 for verification
                print(f"  {i+1}. {abstraction.get('name', 'Unknown')} ({abstraction.get('complexity', 'Unknown')} complexity)")
        return result

    def _analyze_relationships(self) -> List[Dict]:
        """Step 3: Enhanced relationship analysis using expert prompt engineering."""
        print("[INFO] Using enhanced relationship analysis with dependency mapping...")
        
        abstractions_json = json.dumps(self.abstractions, indent=2)
        prompt = f"""
**ROLE**: You are an expert instructional designer specializing in technical curriculum development for software engineering teams.

**TASK**: Analyze the relationships between technical abstractions to create optimal learning dependencies and pathways.

**THINK STEP BY STEP**:
1. Identify prerequisite knowledge relationships (what must be learned before what)
2. Map functional dependencies (what components use/depend on others)
3. Consider cognitive load (which concepts build naturally on others)
4. Evaluate practical workflow connections (what developers use together)

**ABSTRACTIONS**:
{abstractions_json}

**OUTPUT FORMAT**: JSON array with this exact structure:
[
  {{
    "from": "Exact name of source abstraction",
    "to": "Exact name of target abstraction", 
    "type": "PREREQUISITE|USES|CONFIGURES|IMPLEMENTS|EXTENDS|WORKFLOW",
    "description": "Clear explanation of the relationship and why it matters for learning",
    "strength": "Strong|Medium|Weak",
    "learning_impact": "How this relationship affects tutorial sequencing"
  }}
]

**RELATIONSHIP TYPES EXPLAINED**:
- **PREREQUISITE**: 'from' must be understood before 'to' (e.g., "HTTP Basics" PREREQUISITE "REST API Design")
- **USES**: 'from' actively utilizes 'to' in its implementation
- **CONFIGURES**: 'from' sets up or configures 'to'
- **IMPLEMENTS**: 'from' is a concrete implementation of 'to' 
- **EXTENDS**: 'from' builds upon or extends 'to'
- **WORKFLOW**: 'from' and 'to' are used together in common development workflows

**EXAMPLE GOOD RELATIONSHIP**:
{{
  "from": "FastAPI Request/Response Pipeline",
  "to": "Pydantic Data Validation",
  "type": "USES",
  "description": "The FastAPI pipeline relies on Pydantic models for automatic request validation and response serialization",
  "strength": "Strong",
  "learning_impact": "Learners need to understand Pydantic validation before they can effectively work with FastAPI endpoints"
}}

**QUALITY CRITERIA**:
- Focus on relationships that impact learning order
- Prioritize strong dependencies over weak associations
- Consider practical development workflows
- Ensure names exactly match abstraction names

CRITICAL: Return ONLY the JSON array. No other text.
"""
        
        result = _invoke_llm_with_json_parsing(prompt)
        if result:
            print(f"[SUCCESS] Enhanced relationship analysis complete - found {len(result)} relationships")
            strong_deps = [r for r in result if r.get('strength') == 'Strong']
            print(f"  Found {len(strong_deps)} strong dependencies that will drive chapter ordering")
        return result
        
    def _order_chapters(self) -> List[Dict]:
        """Step 4: Enhanced chapter ordering using expert instructional design."""
        print("[INFO] Using enhanced chapter planning with pedagogical principles...")
        
        abstractions_json = json.dumps(self.abstractions, indent=2)
        relationships_json = json.dumps(self.relationships, indent=2)
        prompt = f"""
**ROLE**: You are a master instructional designer with expertise in software engineering curriculum and cognitive learning theory.

**TASK**: Design an optimal chapter sequence that builds knowledge progressively, ensuring each chapter has clear learning objectives and practical outcomes.

**THINK STEP BY STEP**:
1. Map prerequisite relationships between abstractions
2. Group related concepts into coherent learning units
3. Order from foundational concepts to advanced applications
4. Ensure each chapter has actionable outcomes
5. Balance theoretical understanding with practical application
6. Consider cognitive load and learner motivation

**ABSTRACTIONS**:
{abstractions_json}

**RELATIONSHIPS**:
{relationships_json}

**OUTPUT FORMAT**: JSON array ordered by chapter number:
[
  {{
    "chapter": 1,
    "title": "Engaging, outcome-focused title that promises specific skills",
    "objective": "After this chapter, you will be able to [specific, measurable skill/understanding]",
    "concepts_covered": ["exact abstraction names from input"],
    "chapter_type": "Foundation|Core|Application|Integration|Advanced",
    "estimated_time": "15-30 minutes",
    "hands_on_activity": "Specific practical exercise learners will complete",
    "success_criteria": "How learners know they've mastered this chapter",
    "developer_impact": "How this knowledge immediately helps their daily work",
    "prerequisite_chapters": [chapter_numbers_that_must_come_before]
  }}
]

**PEDAGOGICAL PRINCIPLES**:
- Start with "what" and "why" before "how"
- Each chapter should build on previous knowledge
- Include hands-on activities in every chapter
- End each chapter with clear next steps
- Balance complexity progression (not too steep, not too flat)
- Ensure immediate practical value in each chapter

**CHAPTER TYPES EXPLAINED**:
- **Foundation**: Essential concepts and mental models
- **Core**: Primary functionality and patterns
- **Application**: Putting concepts together in real scenarios
- **Integration**: How components work together
- **Advanced**: Complex topics and optimization

**EXAMPLE EXCELLENT CHAPTER**:
{{
  "chapter": 1,
  "title": "Building Your First FastAPI Endpoint: From Request to Response",
  "objective": "After this chapter, you will be able to create a validated FastAPI endpoint and understand the complete request/response cycle",
  "concepts_covered": ["FastAPI Request/Response Pipeline with Pydantic Validation"],
  "chapter_type": "Foundation",
  "estimated_time": "20 minutes",
  "hands_on_activity": "Create a new /hello endpoint with input validation and test it",
  "success_criteria": "Successfully create, test, and modify a working API endpoint",
  "developer_impact": "Immediately able to add new endpoints to this codebase",
  "prerequisite_chapters": []
}}

**QUALITY CRITERIA**:
- Titles should promise specific, valuable outcomes
- Objectives must be measurable and achievable
- Activities should reinforce the learning objective
- Time estimates help learners plan their study
- Each chapter should have immediate practical value

CRITICAL: Return ONLY the JSON array. No other text.
"""
        
        result = _invoke_llm_with_json_parsing(prompt)
        if result:
            print(f"[SUCCESS] Enhanced chapter planning complete - created {len(result)} chapters")
            foundation_chapters = [c for c in result if c.get('chapter_type') == 'Foundation']
            print(f"  Foundation chapters: {len(foundation_chapters)}")
            
            # Calculate time estimates safely
            try:
                total_min_time = 0
                total_max_time = 0
                for c in result:
                    time_str = c.get('estimated_time', '20-30 minutes')
                    # Extract numbers from time string
                    import re
                    numbers = re.findall(r'\d+', time_str)
                    if len(numbers) >= 2:  # Range like "20-30 minutes"
                        total_min_time += int(numbers[0])
                        total_max_time += int(numbers[1])
                    elif len(numbers) == 1:  # Single value like "25 minutes"
                        total_min_time += int(numbers[0])
                        total_max_time += int(numbers[0])
                    else:  # Fallback
                        total_min_time += 20
                        total_max_time += 30
                
                print(f"  Estimated total time: {total_min_time}-{total_max_time} minutes ({total_min_time//60:.1f}-{total_max_time//60:.1f} hours)")
            except Exception as e:
                print(f"  Time estimation calculation skipped due to: {e}")
        return result

    def _write_all_chapters(self) -> Dict[str, str]:
        """Step 5: Enhanced chapter writing with expert prompting, Mermaid diagrams, and rate limit management."""
        print("[INFO] Starting enhanced chapter generation with expert prompting and Mermaid diagrams...")
        written_chapters = {}
        total_chapters = len(self.chapter_plan)
        
        for i, chapter_def in enumerate(self.chapter_plan):
            chapter_num = chapter_def['chapter']
            chapter_title = chapter_def.get('title', f'Chapter {chapter_num}')
            estimated_time = chapter_def.get('estimated_time', '20 minutes')
            
            print(f"  - [{i+1}/{total_chapters}] Writing: {chapter_title} (Est. {estimated_time})")
            
            # Rate limiting with enhanced feedback
            if i > 0 and i % 8 == 0:  # Reduced frequency to be more conservative
                print(f"[INFO] Rate limit pause: {self.rate_limit_pause_seconds}s after {i} chapters...")
                print(f"[INFO] Chapters completed so far: {list(written_chapters.keys())}")
                time.sleep(self.rate_limit_pause_seconds)
            
            # Special handling for overview chapter
            if chapter_def.get('chapter_type') == 'Overview':
                chapter_content = self._write_project_overview_chapter(chapter_def)
            else:
                # Enhanced chapter generation with diagrams
                context_code = self._get_context_for_chapter(chapter_def)
                
                # Generate chapter-specific diagram if relevant
                chapter_diagram = _generate_chapter_specific_diagram(chapter_def, self.abstractions, self.relationships)
                
                chapter_content = self._write_single_chapter_content_enhanced(chapter_def, context_code, chapter_diagram)
            
            written_chapters[f"chapter_{chapter_num}"] = chapter_content
            
            print(f"    ✅ Chapter {chapter_num} complete ({len(chapter_content)} characters)")
            
        print(f"[SUCCESS] All {total_chapters} chapters written using enhanced methodology with Mermaid diagrams")
        return written_chapters

    def _write_project_overview_chapter(self, chapter_def: Dict) -> str:
        """Write a comprehensive project overview chapter with architecture diagram."""
        project_name = chapter_def.get('title', 'Project Overview').replace(' Overview', '')
        architecture_diagram = chapter_def.get('architecture_diagram', '')
        abstractions_count = chapter_def.get('abstractions_count', 0)
        
        # Create structured overview content
        overview_content = f"""# {chapter_def.get('title', 'Project Overview')}

## 🎯 Chapter Objective
{chapter_def.get('objective', 'Understand the overall architecture and key components of this project')}

**Time to Complete:** {chapter_def.get('estimated_time', '15-20 minutes')}

---

## 🏗️ Project Architecture

Understanding the big picture is crucial before diving into specifics. Here's how {project_name} is structured:

```mermaid
{architecture_diagram}
```

## 📊 System Overview

This project consists of **{abstractions_count} key components** that work together to deliver its functionality. The architecture follows modern software engineering principles with clear separation of concerns and modular design.

### 🎯 Key Architectural Patterns

Based on the codebase analysis, this project demonstrates several important patterns:

- **Modular Architecture**: Components are organized into distinct, focused modules
- **Separation of Concerns**: Different aspects of functionality are cleanly separated
- **Dependency Management**: Clear relationships between components prevent circular dependencies
- **Scalable Design**: Structure supports growth and modification

## 🗺️ Navigation Guide

As you progress through this tutorial, you'll explore each component in detail:

1. **Foundation Concepts** - Essential patterns and structures
2. **Core Components** - Main functional elements
3. **Integration Patterns** - How components work together
4. **Advanced Topics** - Optimization and advanced features

## 🛠️ What You'll Build Understanding Of

By the end of this tutorial series, you'll have comprehensive knowledge of:

- **System Architecture**: How all pieces fit together
- **Component Interactions**: Data flow and dependencies
- **Development Patterns**: Coding standards and best practices
- **Extension Points**: Where and how to add new features

## 🎯 Hands-On Activity

**Exercise: Project Exploration**

{chapter_def.get('hands_on_activity', 'Explore the project structure and identify key components')}

**Steps:**
1. Clone or download the project repository
2. Explore the directory structure using your preferred file explorer or IDE
3. Identify the main entry points and configuration files
4. Map what you see to the architecture diagram above

**Success Check:** {chapter_def.get('success_criteria', 'Can explain the main architectural layers and component interactions')}

## 🔗 How This Connects

This overview chapter provides the foundation for all subsequent chapters. Each following chapter will dive deep into specific components you see in the architecture diagram above.

## ✅ Chapter Summary

- ✅ **Architecture Understanding**: You now know the high-level structure
- ✅ **Component Awareness**: You can identify the main building blocks  
- ✅ **Navigation Skills**: You know how to explore the codebase effectively
- ✅ **Learning Path**: You understand what's coming in the tutorial series

## 👉 Up Next

In the next chapter, we'll dive into the foundational components that everything else builds upon. You'll get hands-on experience with the core patterns that make this system work.

---

*Ready to dive deeper? Let's explore the building blocks that make this system tick!* 🚀
"""
        
        return overview_content

    def _get_context_for_chapter(self, chapter_def: Dict) -> str:
        """Gathers the relevant code snippets needed to write a specific chapter."""
        concepts_to_cover = chapter_def.get('concepts_covered', [])
        relevant_files = set()
        for concept_name in concepts_to_cover:
            for abstr in self.abstractions:
                if abstr['name'] == concept_name:
                    for file_path in abstr.get('files_involved', []):
                        relevant_files.add(file_path)
        
        context_parts = []
        for file_path in sorted(list(relevant_files)):
            file_content = []
            for chunk in self.chunks:
                chunk_file = chunk.get('original_file', chunk.get('file'))
                if chunk_file == file_path:
                    file_content.append(chunk['content'])
            
            if file_content:
                context_parts.append(f"--- FILE: {file_path} ---\n\n{''.join(file_content)}\n")
        
        return "\n".join(context_parts)
    
    def _write_single_chapter_content_enhanced(self, chapter_def: Dict, code_context: str, chapter_diagram: str = "") -> str:
        """Enhanced chapter content generation using expert prompt engineering methodology with Mermaid diagrams."""
        
        # Create a clean prompt for chapter generation
        title = chapter_def.get('title', 'Chapter Title')
        objective = chapter_def.get('objective', 'Learn key concepts')
        estimated_time = chapter_def.get('estimated_time', '20 minutes')
        hands_on_activity = chapter_def.get('hands_on_activity', 'Practice with the code')
        success_criteria = chapter_def.get('success_criteria', 'Validation criteria')
        chapter_type = chapter_def.get('chapter_type', 'Core')
        
        mermaid_guide = _get_mermaid_examples_and_rules()
        
        prompt = f"""You are a senior developer and technical mentor creating a tutorial chapter with visual learning aids.

**CHAPTER INFORMATION:**
Title: {title}
Type: {chapter_type}
Objective: {objective}
Time: {estimated_time}

**YOUR TASK:** Write a comprehensive chapter following this EXACT structure:

# {title}

## 🎯 Chapter Objective
{objective}

**Time to Complete:** {estimated_time}

## 💡 Why This Matters
[Explain why this concept is important for developers - be specific about real-world impact]

## 🎨 Visual Overview
{f'```mermaid\\n{chapter_diagram}\\n```' if chapter_diagram else '[Create a simple Mermaid diagram to illustrate the main concept - see examples below]'}

## 🧠 Core Concepts
[Explain the main concepts clearly with definitions and examples]

## 💻 Code Deep Dive
[Analyze the relevant code with step-by-step explanations]

## 🧑‍💻 Hands-On Practice
**Exercise: {hands_on_activity}**

**Steps:**
1. [Step-by-step instructions]
2. [Clear, actionable tasks]

**Success Check:** {success_criteria}

## ✅ Chapter Summary
[Key takeaways - what the learner now knows and can do]

## 👉 Up Next
[Preview next chapter topic]

---

**MERMAID INTEGRATION RULES:**
{mermaid_guide}

**IF NO DIAGRAM PROVIDED:** Create a simple Mermaid diagram in the Visual Overview section that illustrates the chapter's main concept. Choose from GitHub-supported types:
- Flowchart: For processes, workflows, or decision trees
- Sequence: For API interactions or step-by-step processes  
- Gantt: For learning progression or project phases
- Class: For object relationships or system structure
- State: For state transitions or process states
- ER Diagram: For data models or entity relationships
- Pie Chart: For technology stack or component distribution
- Git Graph: For version control workflows

**CONTENT REQUIREMENTS:**
- Include practical code examples from the provided context
- Use clear, beginner-friendly explanations
- Add emoji headers for visual appeal
- Keep sections focused and actionable
- Include specific examples from the codebase

**RELEVANT CODE CONTEXT:**
{code_context}

**CRITICAL:** Write the complete chapter content. Include a Mermaid diagram if none was provided. Use valid Mermaid syntax from the examples above."""
        
        try:
            # Use tracked LLM call for enhanced chapter generation
            response = tracked_llm_call(
                module="tutorial_generator",
                function="_write_single_chapter_content_enhanced",
                model="models/gemini-2.0-flash",
                llm_instance=llm,
                prompt=prompt
            )
            
            content = response.content if hasattr(response, "content") else str(response)
            
            # Validate chapter quality
            if len(content) < 500:
                print(f"    ⚠️  WARNING: Chapter content seems short ({len(content)} chars)")
            if "```" not in content:
                print(f"    ⚠️  WARNING: No code blocks found in chapter")
            if "🎯" not in content:
                print(f"    ⚠️  WARNING: Chapter structure may be incomplete")
            if "mermaid" not in content.lower():
                print(f"    💡 INFO: No Mermaid diagram found in chapter - adding simple fallback")
                # Add a simple learning flow diagram if none exists
                simple_diagram = f"""
## 🎨 Visual Overview

```mermaid
flowchart LR
    Start["📚 Start Learning"]
    Understand["🧠 Understand Concepts"]
    Practice["💻 Hands-on Practice"]
    Master["✅ Master Skills"]
    
    Start --> Understand
    Understand --> Practice
    Practice --> Master
    
    classDef learning fill:#e1f5fe,stroke:#333,stroke-width:2px;
    class Start,Understand,Practice,Master learning;
```
"""
                # Insert after "Why This Matters" section
                if "## 💡 Why This Matters" in content and "## 🎨 Visual Overview" not in content:
                    content = content.replace("## 🧠 Core Concepts", simple_diagram + "\n## 🧠 Core Concepts")
                
            return content
            
        except Exception as e:
            print(f"[ERROR] Enhanced chapter generation failed: {e}")
            # Fallback to basic generation
            return self._write_single_chapter_content(chapter_def, code_context)
    
    def _write_single_chapter_content(self, chapter_def: Dict, code_context: str) -> str:
        """Fallback: Basic chapter content generation (original method)."""
        prompt = f"""
You are a technical writer creating a chapter for a software development tutorial.

Chapter Plan:
{json.dumps(chapter_def, indent=2)}

Relevant Code Snippets from the Repository:
{code_context}
Your task is to write the full content for this chapter in Markdown format.

Instructions:
1.  **Title:** Start with a Level 2 Markdown header (`##`) for the chapter title from the plan.
2.  **Introduction:** Briefly introduce the chapter's topic and state its objective.
3.  **Explanation:** Explain the core concepts in detail.
4.  **Code Walkthrough:** Refer explicitly to the provided code snippets. Explain what the code does and how it works. Use Markdown code blocks with language identifiers.
5.  **Practical Example:** Provide a concise, practical example of how to use the feature.
6.  **Summary:** Conclude with a brief summary of the key takeaways.
7.  **Next Steps:** Mention what the next chapter will cover.

The tone should be educational, encouraging, and clear.
"""
        response = llm.invoke(prompt)
        return response.content if hasattr(response, "content") else str(response)

    def _combine_tutorial(self) -> Dict[str, Any]:
        """Step 6: Assembles the final tutorial structure and Markdown file."""
        toc_lines = ["# Table of Contents"]
        for chapter_def in self.chapter_plan:
            chapter_num = chapter_def['chapter']
            title = chapter_def['title']
            anchor = f"#chapter-{chapter_num}-{title.lower().replace(' ', '-')}"
            toc_lines.append(f"- [Chapter {chapter_num}: {title}]({anchor})")
        
        table_of_contents = "\n".join(toc_lines)
        introduction = self._create_tutorial_introduction()

        markdown_parts = [f"# Tutorial: Understanding the Repository", introduction, table_of_contents]
        for chapter_def in self.chapter_plan:
            chapter_num = chapter_def['chapter']
            title = chapter_def['title']
            anchor = f"chapter-{chapter_num}-{title.lower().replace(' ', '-')}"
            markdown_parts.append(f'<a name="{anchor}"></a>')
            markdown_parts.append(self.full_tutorial_content[f'chapter_{chapter_num}'])
        
        full_markdown = "\n\n---\n\n".join(markdown_parts)

        return {
            "title": f"Tutorial for Repository",
            "introduction": introduction,
            "table_of_contents": table_of_contents,
            "chapters_data": self.chapter_plan,
            "chapters_content": self.full_tutorial_content,
            "full_markdown": full_markdown,
            "total_chapters": len(self.chapter_plan)
        }
        
    def _create_tutorial_introduction(self) -> str:
        """Enhanced tutorial introduction using expert prompting methodology."""
        if not self.chapter_plan:
            return "Welcome to this tutorial."

        num_chapters = len(self.chapter_plan)
        first_chapter = self.chapter_plan[0]['title']
        last_chapter = self.chapter_plan[-1]['title']
        
        # Calculate total estimated time safely
        total_time_min = 0
        total_time_max = 0
        try:
            import re
            for chapter in self.chapter_plan:
                time_str = chapter.get('estimated_time', '20-30 minutes')
                # Extract numbers from time string using regex
                numbers = re.findall(r'\d+', time_str)
                if len(numbers) >= 2:  # Range like "20-30 minutes"
                    total_time_min += int(numbers[0])
                    total_time_max += int(numbers[1])
                elif len(numbers) == 1:  # Single value like "25 minutes"
                    time_val = int(numbers[0])
                    total_time_min += time_val
                    total_time_max += time_val
                else:  # Fallback if no numbers found
                    total_time_min += 20
                    total_time_max += 30
        except Exception as e:
            print(f"[WARNING] Time calculation error: {e}, using defaults")
            total_time_min = len(self.chapter_plan) * 20  # 20 min per chapter default
            total_time_max = len(self.chapter_plan) * 30  # 30 min per chapter default
        
        # Get chapter types for overview
        foundation_chapters = [c for c in self.chapter_plan if c.get('chapter_type') == 'Foundation']
        core_chapters = [c for c in self.chapter_plan if c.get('chapter_type') == 'Core']
        advanced_chapters = [c for c in self.chapter_plan if c.get('chapter_type') == 'Advanced']
        
        return f"""
# 🚀 Welcome to Your Comprehensive Codebase Tutorial!

## What You'll Achieve
By the end of this {num_chapters}-chapter journey, you'll have **deep, practical understanding** of this codebase and be ready to contribute effectively from day one. This isn't just documentation - it's your complete onboarding experience.

## ⏱️ Time Investment
**Total Time:** {total_time_min}-{total_time_max} minutes (approximately {total_time_min//60:.1f}-{total_time_max//60:.1f} hours)
**Recommended Pace:** 1-2 chapters per study session for optimal learning

## 🎯 Learning Path Overview
We've carefully designed this tutorial using proven instructional design principles:

**🏗️ Foundation ({len(foundation_chapters)} chapters):** Essential concepts and mental models
**⚙️ Core Functionality ({len(core_chapters)} chapters):** Primary features and patterns  
**🔬 Advanced Topics ({len(advanced_chapters)} chapters):** Complex integrations and optimizations

## 📚 What Makes This Tutorial Special
- **Hands-on Learning:** Every chapter includes practical exercises you can try immediately
- **Visual Learning:** Interactive Mermaid diagrams illustrate concepts, architecture, and workflows
- **Real-world Focus:** Learn patterns and practices actually used in this codebase
- **Progressive Building:** Each chapter builds naturally on previous knowledge
- **Immediate Value:** Gain practical skills you can apply right away

## 🗺️ Your Learning Journey
We'll start with **"{first_chapter}"** to build your foundation, then progressively advance through the architecture until we reach **"{last_chapter}"** where you'll see how everything integrates.

Each chapter follows a proven structure:
- 🎯 **Clear Learning Objectives** - Know exactly what you'll accomplish
- 🔍 **Real-world Context** - Understand why this matters for your work
- 🎨 **Visual Overview** - Mermaid diagrams showing concepts and relationships
- 💻 **Code Walkthroughs** - Deep dives into actual implementation
- 🚀 **Hands-on Practice** - Immediate application of concepts
- ✅ **Success Validation** - Confirm your understanding before moving on

## 💡 How to Get the Most Value
1. **Set aside focused time** - Each chapter deserves your full attention
2. **Actually try the exercises** - Passive reading won't build real skills
3. **Connect concepts** - Notice how each chapter builds on previous learning
4. **Experiment beyond the examples** - The best learning happens when you explore

## 🎯 Your Success Goal
After completing this tutorial, you'll be able to:
- Navigate the codebase confidently
- Understand the architectural decisions and patterns
- Implement new features following established conventions
- Debug issues using your deep system knowledge
- Contribute meaningfully to the project

**Ready to become an expert in this codebase? Let's dive in!** 🚀
"""