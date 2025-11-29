# enhanced_qa.py - Claude 4 Copilot-style enhanced Q&A system
import ast
import os
import json
import difflib
import subprocess
import time
from typing import List, Dict, Any, Tuple, Optional, Union
from dataclasses import dataclass, asdict
from app.utils.qa import *  # Import all existing functionality
from app.utils.llm_tracker import tracked_llm_call

@dataclass
class CodeTask:
    """Represents a decomposed coding task"""
    task_id: str
    description: str
    target_files: List[str]
    dependencies: List[str]
    action_type: str  # 'create', 'modify', 'delete', 'analyze'
    priority: int
    estimated_complexity: str
    file_patterns: List[str] = None

@dataclass
class CodeChange:
    """Represents a specific code modification"""
    file_path: str
    change_type: str  # 'create', 'modify', 'delete'
    original_content: str
    new_content: str
    diff: str
    validation_status: str
    reasoning: str = ""

@dataclass
class AnalysisResult:
    """Structured analysis result"""
    file_path: str
    functions: List[Dict[str, Any]]
    classes: List[Dict[str, Any]]
    imports: List[str]
    dependencies: List[str]
    complexity_score: float
    main_purpose: str

class AdvancedCodeAnalyzer:
    """Enhanced code analysis using AST and dependency mapping"""
    
    def __init__(self, doc_map: List[Dict]):
        self.doc_map = doc_map or []
        self.ast_cache = {}
        self.dependency_graph = {}
        self.function_map = {}
        self.class_map = {}
        self.file_analysis = {}
        if self.doc_map:
            self._build_code_maps()
    
    def _build_code_maps(self):
        """Build AST and dependency maps for all Python files"""
        print("[INFO] Building advanced code analysis maps...")
        
        # Handle both old format (list) and new format (dict with chunks)
        if isinstance(self.doc_map, dict):
            docs = self.doc_map.get('chunks', [])
        else:
            docs = self.doc_map
        
        for doc in docs:
            file_path = doc.get('original_file', doc.get('file', ''))
            content = doc.get('content', '')
            
            if file_path.endswith('.py') and content.strip():
                try:
                    # Parse AST
                    tree = ast.parse(content)
                    self.ast_cache[file_path] = tree
                    
                    # Extract comprehensive analysis
                    analysis = self._analyze_python_file(tree, file_path, content)
                    self.file_analysis[file_path] = analysis
                    
                    # Build maps
                    self._extract_definitions(tree, file_path)
                    self._extract_dependencies(tree, file_path)
                    
                except SyntaxError as e:
                    print(f"[WARNING] Could not parse {file_path}: {e}")
                except Exception as e:
                    print(f"[WARNING] Error analyzing {file_path}: {e}")
    
    def _analyze_python_file(self, tree: ast.AST, file_path: str, content: str) -> AnalysisResult:
        """Comprehensive file analysis"""
        functions = []
        classes = []
        imports = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                functions.append({
                    'name': node.name,
                    'line_start': node.lineno,
                    'args': [arg.arg for arg in node.args.args],
                    'docstring': ast.get_docstring(node),
                    'is_async': isinstance(node, ast.AsyncFunctionDef),
                    'decorators': [self._get_decorator_name(d) for d in node.decorator_list]
                })
            elif isinstance(node, ast.ClassDef):
                methods = [n.name for n in node.body if isinstance(n, ast.FunctionDef)]
                classes.append({
                    'name': node.name,
                    'line_start': node.lineno,
                    'methods': methods,
                    'docstring': ast.get_docstring(node),
                    'bases': [self._get_node_name(base) for base in node.bases]
                })
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                imports.extend(self._extract_import_names(node))
        
        # Calculate complexity (rough estimate)
        complexity = len(functions) * 2 + len(classes) * 3 + content.count('if ') + content.count('for ') + content.count('while ')
        
        # Determine main purpose
        purpose = self._determine_file_purpose(file_path, functions, classes, content)
        
        return AnalysisResult(
            file_path=file_path,
            functions=functions,
            classes=classes,
            imports=imports,
            dependencies=[],  # Will be filled by dependency analysis
            complexity_score=complexity / 100.0,  # Normalize
            main_purpose=purpose
        )
    
    def _get_decorator_name(self, decorator) -> str:
        """Extract decorator name"""
        if isinstance(decorator, ast.Name):
            return decorator.id
        elif isinstance(decorator, ast.Attribute):
            return f"{self._get_node_name(decorator.value)}.{decorator.attr}"
        return str(decorator)
    
    def _get_node_name(self, node) -> str:
        """Extract name from AST node"""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_node_name(node.value)}.{node.attr}"
        return str(node)
    
    def _extract_import_names(self, node) -> List[str]:
        """Extract import names from import node"""
        imports = []
        if isinstance(node, ast.Import):
            imports.extend([alias.name for alias in node.names])
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ''
            for alias in node.names:
                if alias.name == '*':
                    imports.append(f"{module}.*")
                else:
                    imports.append(f"{module}.{alias.name}" if module else alias.name)
        return imports
    
    def _determine_file_purpose(self, file_path: str, functions: List, classes: List, content: str) -> str:
        """Determine the main purpose of a file"""
        filename = os.path.basename(file_path).lower()
        
        if 'test' in filename:
            return 'testing'
        elif 'config' in filename or 'settings' in filename:
            return 'configuration'
        elif 'main' in filename or 'app' in filename:
            return 'application_entry'
        elif 'api' in filename or 'routes' in filename or 'endpoints' in filename:
            return 'api_routes'
        elif 'model' in filename or 'schema' in filename:
            return 'data_models'
        elif 'util' in filename or 'helper' in filename:
            return 'utilities'
        elif 'database' in filename or 'db' in filename:
            return 'database'
        elif len(classes) > len(functions):
            return 'class_definitions'
        elif len(functions) > 3:
            return 'function_library'
        else:
            return 'general_code'
    
    def _extract_definitions(self, tree: ast.AST, file_path: str):
        """Extract function and class definitions"""
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                key = f"{file_path}::{node.name}"
                self.function_map[key] = {
                    'file': file_path,
                    'name': node.name,
                    'line_start': node.lineno,
                    'args': [arg.arg for arg in node.args.args],
                    'docstring': ast.get_docstring(node),
                    'type': 'function'
                }
            elif isinstance(node, ast.ClassDef):
                key = f"{file_path}::{node.name}"
                self.class_map[key] = {
                    'file': file_path,
                    'name': node.name,
                    'line_start': node.lineno,
                    'methods': [n.name for n in node.body if isinstance(n, ast.FunctionDef)],
                    'docstring': ast.get_docstring(node),
                    'type': 'class'
                }
    
    def _extract_dependencies(self, tree: ast.AST, file_path: str):
        """Extract import dependencies"""
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend([alias.name for alias in node.names])
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ''
                imports.extend([f"{module}.{alias.name}" for alias in node.names])
        
        self.dependency_graph[file_path] = imports
    
    def find_related_files(self, target_file: str) -> List[str]:
        """Find files related to the target file"""
        related = []
        target_module = target_file.replace('/', '.').replace('.py', '')
        
        for file, imports in self.dependency_graph.items():
            if any(target_module in imp for imp in imports):
                related.append(file)
        
        return related
    
    def get_file_analysis(self, file_path: str) -> Optional[AnalysisResult]:
        """Get comprehensive analysis for a specific file"""
        return self.file_analysis.get(file_path)
    
    def search_functions(self, pattern: str) -> List[Dict]:
        """Search for functions matching a pattern"""
        matches = []
        pattern_lower = pattern.lower()
        
        for key, func_info in self.function_map.items():
            if (pattern_lower in func_info['name'].lower() or 
                (func_info['docstring'] and pattern_lower in func_info['docstring'].lower())):
                matches.append(func_info)
        
        return matches

class TaskDecomposer:
    """Breaks down complex coding tasks into manageable subtasks"""
    
    def __init__(self, analyzer: AdvancedCodeAnalyzer):
        self.analyzer = analyzer
    
    def decompose_task(self, user_request: str, context: Dict) -> List[CodeTask]:
        """Break down user request into actionable tasks"""
        
        # Analyze if this is a coding task
        if not self._is_coding_task(user_request):
            return []
        
        decomposition_prompt = f"""
You are an expert software architect. Break down this coding request into specific, actionable subtasks.

User Request: "{user_request}"

Repository Context Summary:
- Available files: {len(self.analyzer.doc_map)} files
- Python files analyzed: {len(self.analyzer.file_analysis)}
- Key functions: {list(self.analyzer.function_map.keys())[:10]}

Available File Purposes:
{json.dumps({f: a.main_purpose for f, a in self.analyzer.file_analysis.items()}, indent=2)}

Create a JSON array of tasks with this structure:
[
  {{
    "task_id": "unique_id",
    "description": "specific action to take",
    "target_files": ["file1.py", "file2.py"],
    "dependencies": ["task_id_that_must_complete_first"],
    "action_type": "create|modify|delete|analyze",
    "priority": 1-10,
    "estimated_complexity": "low|medium|high",
    "file_patterns": ["*.py", "config/*"]
  }}
]

Guidelines:
- Break complex requests into 3-7 subtasks maximum
- Consider file dependencies and modification order
- Start with analysis, then imports/config, then core logic, then tests
- Each task should be completable independently
- Prioritize based on dependencies (1=highest priority)
- Use "analyze" action for understanding existing code
- Use "modify" for changing existing files
- Use "create" for new files

CRITICAL: Respond with ONLY the JSON array, no other text.
"""
        
        try:
            response = tracked_llm_call(
                module="enhanced_qa",
                function="decompose_task",
                model="models/gemini-2.0-flash",
                llm_instance=llm,
                prompt=decomposition_prompt
            )
            
            tasks_json = response.content if hasattr(response, "content") else str(response)
            json_start = tasks_json.find('[')
            json_end = tasks_json.rfind(']') + 1
            
            if json_start != -1 and json_end > json_start:
                try:
                    json_content = tasks_json[json_start:json_end]
                    print(f"[DEBUG] Attempting to parse JSON: {json_content[:200]}...")
                    tasks_data = json.loads(json_content)
                    
                    # Validate that each task has required fields
                    valid_tasks = []
                    for i, task in enumerate(tasks_data):
                        if isinstance(task, dict) and all(key in task for key in ['task_id', 'description', 'action_type']):
                            # Set defaults for missing optional fields
                            task.setdefault('target_files', [])
                            task.setdefault('dependencies', [])
                            task.setdefault('priority', 5)
                            task.setdefault('estimated_complexity', 'medium')
                            task.setdefault('file_patterns', [])
                            valid_tasks.append(CodeTask(**task))
                        else:
                            print(f"[WARNING] Skipping invalid task {i}: {task}")
                    
                    if valid_tasks:
                        return valid_tasks
                        
                except json.JSONDecodeError as json_err:
                    print(f"[ERROR] JSON parsing failed: {json_err}")
                    print(f"[DEBUG] Problematic JSON content: {json_content}")
                except Exception as task_err:
                    print(f"[ERROR] Task creation failed: {task_err}")
                    
        except Exception as e:
            print(f"[ERROR] Task decomposition failed: {e}")
        
        # Fallback: create single generic task
        return [CodeTask(
            task_id="generic_task",
            description=user_request,
            target_files=[],
            dependencies=[],
            action_type="analyze",
            priority=5,
            estimated_complexity="medium"
        )]
    
    def _is_coding_task(self, request: str) -> bool:
        """Determine if request involves coding/modification"""
        coding_keywords = [
            'add', 'create', 'implement', 'modify', 'change', 'update', 
            'fix', 'refactor', 'build', 'make', 'write', 'generate',
            'delete', 'remove', 'replace', 'optimize', 'improve'
        ]
        return any(keyword in request.lower() for keyword in coding_keywords)

class CodeGenerator:
    """Generates and modifies code with validation"""
    
    def __init__(self, analyzer: AdvancedCodeAnalyzer):
        self.analyzer = analyzer
        self.change_history = []
    
    def execute_task(self, task: CodeTask, context: Dict) -> CodeChange:
        """Execute a specific coding task"""
        
        # Get relevant context for this specific task
        task_context = self._get_task_context(task)
        
        generation_prompt = f"""
You are an expert Python developer. Execute this specific coding task:

Task: {task.description}
Action Type: {task.action_type}
Target Files: {task.target_files}
Complexity: {task.estimated_complexity}

Relevant Code Context:
{task_context}

File Analysis Available:
{json.dumps({f: a.main_purpose for f, a in self.analyzer.file_analysis.items() 
            if any(tf in f for tf in task.target_files)}, indent=2)}

INSTRUCTIONS:
1. If action_type is "analyze": Provide detailed analysis of existing code
2. If action_type is "create": Generate complete new file content
3. If action_type is "modify": Provide specific modifications to existing code
4. If action_type is "delete": Specify what to remove

REQUIREMENTS:
- Follow existing code patterns and style
- Add proper error handling and documentation
- Ensure compatibility with existing codebase
- Consider edge cases and validation
- Maintain existing functionality

Provide your response in this JSON format:
{{
    "file_path": "path/to/file.py",
    "action": "analyze|create|modify|delete",
    "new_content": "complete file content or modification or analysis",
    "explanation": "what this code does and why",
    "potential_issues": ["any concerns or dependencies"],
    "test_suggestions": ["how to test this change"],
    "dependencies": ["files that might be affected"]
}}

CRITICAL: Respond with ONLY the JSON object, no other text.
"""
        
        try:
            response = tracked_llm_call(
                module="enhanced_qa",
                function="execute_task",
                model="models/gemini-2.0-flash",
                llm_instance=llm,
                prompt=generation_prompt
            )
            
            result_json = response.content if hasattr(response, "content") else str(response)
            json_start = result_json.find('{')
            json_end = result_json.rfind('}') + 1
            
            if json_start != -1 and json_end > json_start:
                result_data = json.loads(result_json[json_start:json_end])
                
                # Create code change object
                change = CodeChange(
                    file_path=result_data.get('file_path', task.target_files[0] if task.target_files else ''),
                    change_type=task.action_type,
                    original_content=self._get_file_content(result_data.get('file_path', '')),
                    new_content=result_data.get('new_content', ''),
                    diff="",
                    validation_status="pending",
                    reasoning=result_data.get('explanation', '')
                )
                
                # Generate diff if modifying existing file
                if change.change_type == 'modify' and change.original_content:
                    change.diff = self._generate_diff(change.original_content, change.new_content)
                
                # Validate the generated code
                change.validation_status = self._validate_code(change)
                self.change_history.append(change)
                
                return change
                
        except Exception as e:
            print(f"[ERROR] Code generation failed: {e}")
            return CodeChange("", "error", "", "", "", "failed", f"Generation failed: {e}")
            
        return CodeChange("", "error", "", "", "", "failed", "Generation failed: Unknown error")
    
    def _get_task_context(self, task: CodeTask) -> str:
        """Get relevant context for a specific task"""
        context_parts = []
        
        # Add relevant file analysis
        for file_path in task.target_files:
            analysis = self.analyzer.get_file_analysis(file_path)
            if analysis:
                context_parts.append(f"=== {file_path} Analysis ===")
                context_parts.append(f"Purpose: {analysis.main_purpose}")
                context_parts.append(f"Functions: {[f['name'] for f in analysis.functions]}")
                context_parts.append(f"Classes: {[c['name'] for c in analysis.classes]}")
                context_parts.append("")
        
        # Add file contents if available
        # Handle both old format (list) and new format (dict with chunks)
        if isinstance(self.analyzer.doc_map, dict):
            docs = self.analyzer.doc_map.get('chunks', [])
        else:
            docs = self.analyzer.doc_map
            
        for doc in docs:
            file_path = doc.get('original_file', doc.get('file', ''))
            if any(target in file_path for target in task.target_files):
                context_parts.append(f"=== {file_path} Content ===")
                context_parts.append(doc.get('content', ''))
                context_parts.append("")
        
        return "\n".join(context_parts)
    
    def _get_file_content(self, file_path: str) -> str:
        """Get content of a file from doc_map"""
        # Handle both old format (list) and new format (dict with chunks)
        if isinstance(self.analyzer.doc_map, dict):
            docs = self.analyzer.doc_map.get('chunks', [])
        else:
            docs = self.analyzer.doc_map
            
        for doc in docs:
            if doc.get('original_file') == file_path or doc.get('file') == file_path:
                return doc.get('content', '')
        return ""
    
    def _generate_diff(self, original: str, new: str) -> str:
        """Generate diff between original and new content"""
        diff_lines = list(difflib.unified_diff(
            original.splitlines(keepends=True),
            new.splitlines(keepends=True),
            fromfile='original',
            tofile='modified'
        ))
        return ''.join(diff_lines)
    
    def _validate_code(self, change: CodeChange) -> str:
        """Validate generated code for syntax and basic correctness"""
        if not change.new_content.strip():
            return "empty"
        
        if change.file_path.endswith('.py'):
            try:
                ast.parse(change.new_content)
                return "valid"
            except SyntaxError as e:
                return f"syntax_error: {e}"
        
        return "not_validated"

class EnhancedQASystem:
    """Claude 4 Copilot-style Q&A system with advanced capabilities"""
    
    def __init__(self):
        global doc_map
        if not doc_map:
            print("[WARNING] No document map available for enhanced features")
            self.analyzer = None
            self.decomposer = None
            self.generator = None
        else:
            print("[INFO] Initializing enhanced Q&A system...")
            self.analyzer = AdvancedCodeAnalyzer(doc_map)
            self.decomposer = TaskDecomposer(self.analyzer)
            self.generator = CodeGenerator(self.analyzer)
        
        self.execution_history = []
    
    def handle_request(self, user_request: str) -> Dict[str, Any]:
        """Main entry point - provides direct, comprehensive answers without task decomposition"""
        
        print(f"[INFO] Enhanced Q&A: Processing request directly (no task decomposition): {user_request[:100]}...")
        
        # If no enhanced features available, fall back to standard Q&A
        if not self.analyzer:
            return answer_question(user_request)
        
        # Always use enhanced Q&A with code understanding - no task decomposition
        return self._handle_enhanced_question(user_request)

    def _handle_enhanced_question(self, user_request: str) -> Dict[str, Any]:
        """Handle questions with enhanced code understanding - direct comprehensive answers"""
        
        # Get standard Q&A response as the foundation
        standard_response = answer_question(user_request)
        
        # Enhance the answer with additional context and insights
        try:
            # Get enhanced context based on the question
            enhanced_context = self._get_enhanced_context(user_request)
            
            if enhanced_context:
                # Create a more comprehensive answer using enhanced context
                enhanced_prompt = f"""Based on the user's question and the enhanced code analysis, provide a comprehensive answer.

User Question: {user_request}

Standard Answer: {standard_response['answer']}

Enhanced Context: {enhanced_context}

Please provide a more detailed and comprehensive answer that incorporates both the standard response and the enhanced context. Focus on:
1. Direct answer to the user's question
2. Relevant code examples and explanations
3. Practical insights from the codebase
4. Any additional helpful information

Comprehensive Answer:"""

                enhanced_response = tracked_llm_call(
                    llm, 
                    enhanced_prompt, 
                    temperature=0.3,
                    operation_type="enhanced_answer"
                )
                
                standard_response['answer'] = enhanced_response.content
                standard_response['context_quality'] = "enhanced_comprehensive"
                
        except Exception as e:
            print(f"[INFO] Using standard answer: {e}")
        
        return standard_response
    
    def _get_enhanced_context(self, question: str) -> str:
        """Get enhanced context for the question without task decomposition"""
        
        context_parts = []
        question_lower = question.lower()
        
        # Find relevant files mentioned or implied in the question
        relevant_files = []
        for file_path, analysis in self.analyzer.file_analysis.items():
            # Check if file is mentioned directly
            file_name = file_path.split('/')[-1].lower()
            if (file_name in question_lower or 
                any(keyword in question_lower for keyword in ['component', 'about', 'section', 'page']) and 
                any(keyword in file_name for keyword in ['about', 'component', 'section'])):
                relevant_files.append((file_path, analysis))
        
        # Add relevant file information
        if relevant_files:
            context_parts.append("Relevant Files Analysis:")
            for file_path, analysis in relevant_files[:3]:  # Limit to top 3 files
                context_parts.append(f"\n📁 {file_path}:")
                context_parts.append(f"   Purpose: {analysis.main_purpose}")
                context_parts.append(f"   Functions: {len(analysis.functions)} functions")
                context_parts.append(f"   Classes: {len(analysis.classes)} classes")
                if analysis.functions:
                    context_parts.append(f"   Key Functions: {', '.join([f['name'] for f in analysis.functions[:3]])}")
        
        # Find relevant functions mentioned
        mentioned_functions = []
        for func_key, func_info in self.analyzer.function_map.items():
            if func_info['name'].lower() in question_lower:
                mentioned_functions.append(func_info)
        
        if mentioned_functions:
            context_parts.append("\nRelevant Functions:")
            for func in mentioned_functions[:3]:  # Limit to top 3 functions
                context_parts.append(f"\n🔧 {func['name']} in {func['file_path']}:")
                context_parts.append(f"   Parameters: {len(func.get('parameters', []))}")
                context_parts.append(f"   Complexity: {func.get('complexity', 'Unknown')}")
        
        # Add code patterns and insights if relevant
        if any(keyword in question_lower for keyword in ['styling', 'css', 'tailwind', 'class']):
            context_parts.append("\n🎨 Styling Context: Project uses Tailwind CSS with utility classes")
        
        if any(keyword in question_lower for keyword in ['react', 'component', 'jsx', 'tsx']):
            context_parts.append("\n⚛️ React Context: Project uses React with TypeScript and functional components")
        
        return "\n".join(context_parts) if context_parts else ""

    def _get_code_insights(self, question: str) -> str:
        """Get additional code insights based on the question"""
        
        # Find relevant functions/classes mentioned in question
        mentioned_functions = []
        mentioned_files = []
        
        question_lower = question.lower()
        
        # Search for mentioned functions
        for func_key, func_info in self.analyzer.function_map.items():
            if func_info['name'].lower() in question_lower:
                mentioned_functions.append(func_info)
        
        # Search for mentioned files
        for file_path in self.analyzer.file_analysis.keys():
            filename = os.path.basename(file_path).lower()
            if filename.replace('.py', '') in question_lower:
                mentioned_files.append(file_path)
        
        insights = []
        
        if mentioned_functions:
            insights.append("🔍 **Function Analysis:**")
            for func in mentioned_functions[:3]:  # Limit to 3
                insights.append(f"- `{func['name']}` in {func['file']} (line {func['line_start']})")
                if func['docstring']:
                    insights.append(f"  Purpose: {func['docstring'][:100]}...")
        
        if mentioned_files:
            insights.append("📁 **File Analysis:**")
            for file_path in mentioned_files[:3]:  # Limit to 3
                analysis = self.analyzer.get_file_analysis(file_path)
                if analysis:
                    insights.append(f"- `{os.path.basename(file_path)}`: {analysis.main_purpose}")
                    insights.append(f"  Complexity: {analysis.complexity_score:.1f}, Functions: {len(analysis.functions)}, Classes: {len(analysis.classes)}")
        
        return "\n".join(insights) if insights else ""
    
    def _handle_coding_task(self, user_request: str) -> Dict[str, Any]:
        """Handle requests that involve code generation/modification"""
        print(f"[INFO] Processing coding task: {user_request}")
        
        # Get enhanced context
        context_result = get_intelligent_context(user_request, MAX_CONTEXT_TOKENS // 2)
        
        # Decompose the task
        tasks = self.decomposer.decompose_task(user_request, context_result)
        
        if not tasks:
            # Fall back to enhanced Q&A if no tasks identified
            return self._handle_enhanced_question(user_request)
        
        # Execute tasks in priority order
        completed_tasks = []
        generated_changes = []
        
        for task in sorted(tasks, key=lambda t: t.priority):
            print(f"[INFO] Executing task: {task.description}")
            
            # Execute the task
            change = self.generator.execute_task(task, context_result)
            
            completed_tasks.append({
                'task_id': task.task_id,
                'description': task.description,
                'action_type': task.action_type,
                'status': 'completed' if change.validation_status.startswith('valid') else 'failed',
                'file': change.file_path,
                'validation': change.validation_status,
                'reasoning': change.reasoning
            })
            
            generated_changes.append(change)
        
        # Compile comprehensive response
        response = self._compile_task_response(user_request, completed_tasks, generated_changes)
        
        # Track in execution history
        self.execution_history.append({
            'request': user_request,
            'tasks': completed_tasks,
            'timestamp': time.time(),
            'success_rate': len([t for t in completed_tasks if t['status'] == 'completed']) / len(completed_tasks)
        })
        
        return response
    
    def _compile_task_response(self, original_request: str, tasks: List[Dict], changes: List[CodeChange]) -> Dict[str, Any]:
        """Compile a comprehensive response for coding tasks"""
        
        # Create a structured summary
        summary_parts = []
        summary_parts.append(f"## 🎯 Task Completion Summary")
        summary_parts.append(f"**Original Request:** {original_request}")
        summary_parts.append(f"**Tasks Executed:** {len(tasks)}")
        summary_parts.append(f"**Files Affected:** {len(set(c.file_path for c in changes))}")
        summary_parts.append("")
        
        # Task breakdown
        summary_parts.append("### 📋 Task Breakdown:")
        for i, task in enumerate(tasks, 1):
            status_emoji = "✅" if task['status'] == 'completed' else "❌"
            summary_parts.append(f"{i}. {status_emoji} **{task['action_type'].title()}**: {task['description']}")
            if task['file']:
                summary_parts.append(f"   - File: `{task['file']}`")
            if task['validation'] != 'valid':
                summary_parts.append(f"   - Status: {task['validation']}")
            summary_parts.append("")
        
        # Generated changes
        if changes:
            summary_parts.append("### 🔧 Generated Changes:")
            for change in changes:
                if change.change_type != 'error':
                    summary_parts.append(f"**{change.file_path}** ({change.change_type})")
                    if change.reasoning:
                        summary_parts.append(f"- {change.reasoning}")
                    if change.diff:
                        summary_parts.append("```diff")
                        summary_parts.append(change.diff[:500] + "..." if len(change.diff) > 500 else change.diff)
                        summary_parts.append("```")
                    summary_parts.append("")
        
        # Next steps
        summary_parts.append("### 🚀 Next Steps:")
        summary_parts.append("1. Review the generated code changes above")
        summary_parts.append("2. Test the implementations in your development environment")
        summary_parts.append("3. Make any necessary adjustments based on your specific requirements")
        summary_parts.append("4. Run your existing tests to ensure compatibility")
        
        summary = "\n".join(summary_parts)
        
        return {
            "answer": summary,
            "task_type": "coding_task",
            "tasks_completed": len(tasks),
            "tasks_successful": len([t for t in tasks if t['status'] == 'completed']),
            "files_modified": len(changes),
            "changes": [
                {
                    "file": change.file_path,
                    "type": change.change_type,
                    "status": change.validation_status,
                    "preview": change.new_content[:200] + "..." if len(change.new_content) > 200 else change.new_content,
                    "reasoning": change.reasoning
                } 
                for change in changes
            ],
            "validation_summary": {
                "valid": len([c for c in changes if c.validation_status.startswith("valid")]),
                "failed": len([c for c in changes if "error" in c.validation_status]),
                "total": len(changes)
            },
            "context_chunks_used": len(tasks) * 3,  # Approximate
            "total_tokens_used": sum(count_tokens(c.new_content) for c in changes if c.new_content),
            "context_strategy": "task_decomposition",
            "intent_type": "coding_task",
            "context_quality": "enhanced",
            "history_used": False,
            "conversations_referenced": 0
        }
    
    def get_execution_history(self) -> List[Dict]:
        """Get history of executed coding tasks"""
        return self.execution_history.copy()
    
    def get_code_analysis(self, file_path: str = None) -> Dict[str, Any]:
        """Get code analysis for specific file or entire repository"""
        if not self.analyzer:
            return {"error": "Code analysis not available"}
        
        if file_path:
            analysis = self.analyzer.get_file_analysis(file_path)
            return asdict(analysis) if analysis else {"error": f"File {file_path} not found"}
        else:
            return {
                "total_files": len(self.analyzer.file_analysis),
                "total_functions": len(self.analyzer.function_map),
                "total_classes": len(self.analyzer.class_map),
                "file_purposes": {f: a.main_purpose for f, a in self.analyzer.file_analysis.items()},
                "complexity_scores": {f: a.complexity_score for f, a in self.analyzer.file_analysis.items()}
            }

# Initialize enhanced system
enhanced_qa_system = None

def initialize_enhanced_qa():
    """Initialize the enhanced Q&A system"""
    global enhanced_qa_system
    if enhanced_qa_system is None:
        enhanced_qa_system = EnhancedQASystem()
    return enhanced_qa_system

def handle_request(user_request: str) -> Dict[str, Any]:
    """Main entry point that routes to appropriate handler"""
    system = initialize_enhanced_qa()
    return system.handle_request(user_request)

def get_execution_history() -> List[Dict]:
    """Get history of executed coding tasks"""
    system = initialize_enhanced_qa()
    return system.get_execution_history()

def get_code_analysis(file_path: str = None) -> Dict[str, Any]:
    """Get code analysis for repository or specific file"""
    system = initialize_enhanced_qa()
    return system.get_code_analysis(file_path)
