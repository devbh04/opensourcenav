# qa.py - Enhanced with LLM tracking and comprehensive metrics
import os
import json
import time
import numpy as np
import faiss
import pickle
from typing import List, Dict, Any, Tuple
from app.utils.config import GEMINI_API_KEY
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from transformers import GPT2TokenizerFast
from app.utils.llm_tracker import tracked_llm_call, tracker

llm = ChatGoogleGenerativeAI(model="models/gemini-2.0-flash", google_api_key=GEMINI_API_KEY)
embedder = GoogleGenerativeAIEmbeddings(model="models/embedding-001", google_api_key=GEMINI_API_KEY)
tokenizer = GPT2TokenizerFast.from_pretrained("gpt2")

# Load FAISS index and documents if they exist
if os.path.exists("vector.index") and os.path.exists("doc_map.pkl"):
    index = faiss.read_index("vector.index")
    with open("doc_map.pkl", "rb") as f:
        doc_map = pickle.load(f)
else:
    index, doc_map = None, None

chat_history = []
MAX_CONTEXT_TOKENS = 8000
MAX_HISTORY_TOKENS = 2000

def count_tokens(text: str) -> int: return len(tokenizer.encode(text))

def check_chat_history_relevance(current_question: str, chat_history: List[Dict[str, str]]) -> bool:
    """Use LLM to determine if chat history is relevant to current question"""
    if not chat_history:
        return False
    
    # Get last 3 conversations for relevance check
    recent_history = chat_history[-3:] if len(chat_history) >= 3 else chat_history
    
    # Format history for relevance check
    history_summary = ""
    for i, entry in enumerate(recent_history, 1):
        history_summary += f"Previous Q{i}: {entry['question']}\nPrevious A{i}: {entry['answer'][:200]}...\n\n"
    
    relevance_prompt = f"""Analyze if the chat history is relevant to the current question. Only return "RELEVANT" if the chat history provides meaningful context that would help answer the current question better.

Current Question: {current_question}

Chat History:
{history_summary}

Rules:
1. Return "RELEVANT" ONLY if the chat history contains information that directly relates to or helps answer the current question
2. Return "NOT_RELEVANT" if the chat history is about different topics, different files, or unrelated concepts
3. Be very strict - only consider it relevant if there's a clear connection

Response (RELEVANT or NOT_RELEVANT):"""

    try:
        response = tracked_llm_call(
            llm, 
            relevance_prompt, 
            temperature=0.1,
            operation_type="relevance_check"
        )
        
        result = response.content.strip().upper()
        is_relevant = "RELEVANT" in result
        
        print(f"[INFO] Chat history relevance check: {'RELEVANT' if is_relevant else 'NOT_RELEVANT'}")
        return is_relevant
        
    except Exception as e:
        print(f"[WARNING] Error in relevance check, defaulting to not using history: {e}")
        return False

def get_repository_structure() -> str:
    """Generate a concise repository structure overview"""
    if not doc_map: return "No repository data available."
    file_types, file_tree, processed_paths = {}, {}, set()
    
    # Handle both old format (list) and new format (dict with chunks)
    if isinstance(doc_map, dict):
        docs = doc_map.get('chunks', [])
    else:
        docs = doc_map
    
    for doc in docs:
        file_path = doc.get('original_file', doc.get('file', ''))
        if file_path in processed_paths: continue
        processed_paths.add(file_path)
        file_type = doc.get('file_type', 'unknown')
        file_types.setdefault(file_type, []).append(file_path)
        parts = file_path.split('/')
        current = file_tree
        for part in parts[:-1]: current = current.setdefault(part, {})
        current[parts[-1]] = None

    lines = ["Repository Structure Overview:", "=" * 40, "\nFile Types Available:"]
    for ft, files in sorted(file_types.items()):
        lines.append(f"  {ft}: {len(files)} files")
    lines.append("\nMain Directories:")
    for key in sorted(file_tree.keys()):
        lines.append(f"  {key}{'/' if isinstance(file_tree[key], dict) else ''}")
    return "\n".join(lines)

def analyze_user_intent(question: str, repo_structure: str) -> Dict[str, Any]:
    """Enhanced LLM-based intent analysis with query expansion and tracking"""
    prompt = f"""
Analyze this developer question about a codebase and expand it for optimal code search.

Repository Structure:
{repo_structure}

User Question: "{question}"

Provide a comprehensive JSON analysis:
{{
    "intent_type": "specific_file|code_analysis|general_info|debugging|architecture|implementation",
    "primary_keywords": ["main technical terms from the question"],
    "synonyms": ["alternative terms, abbreviations, related concepts"],
    "target_files": ["specific file paths if mentioned or implied"],
    "file_patterns": ["file patterns like '*.py', 'main.*', '*config*'"],
    "file_type_hints": ["likely file types: source/config/docs/test/package"],
    "language_hints": ["programming languages likely involved"],
    "architectural_patterns": ["API/CLI/web/database/etc if relevant"],
    "complexity_level": "beginner|intermediate|advanced",
    "search_strategy": "exact_match|broad_exploration|dependency_trace|pattern_search",
    "exclude_types": ["file types to avoid"],
    "context_priority": "high_level_overview|detailed_implementation|configuration|examples"
}}

Guidelines:
- Extract ALL relevant technical terms, including abbreviations
- Consider implied concepts (e.g., "authentication" implies users, tokens, middleware)
- Identify the user's skill level from question complexity
- Determine if they need broad understanding or specific implementation details
Respond ONLY with valid JSON.
"""
    try:
        # Use tracked LLM call for monitoring
        response = tracked_llm_call(
            module="qa",
            function="analyze_user_intent",
            model="models/gemini-2.0-flash",
            llm_instance=llm,
            prompt=prompt
        )
        
        intent_text = response.content if hasattr(response, "content") else str(response)
        json_start = intent_text.find('{'); json_end = intent_text.rfind('}') + 1
        if json_start != -1:
            return json.loads(intent_text[json_start:json_end])
    except Exception as e:
        print(f"[ERROR] Enhanced intent analysis failed: {e}")
    
    # Enhanced fallback with better keyword extraction
    keywords = question.lower().split()
    return {
        "intent_type": "general_info", 
        "primary_keywords": keywords,
        "synonyms": [],
        "file_patterns": ["*"], 
        "file_type_hints": ["source"],
        "complexity_level": "intermediate",
        "search_strategy": "broad_exploration",
        "context_priority": "detailed_implementation"
    }

def find_files_by_intent(intent: Dict[str, Any]) -> List[Tuple[int, float, str]]:
    """Enhanced file matching using improved intent analysis"""
    matches = []
    all_keywords = intent.get('primary_keywords', []) + intent.get('synonyms', [])
    
    # Handle both old format (list) and new format (dict with chunks)
    if isinstance(doc_map, dict):
        docs = doc_map.get('chunks', [])
    else:
        docs = doc_map
    
    for i, doc in enumerate(docs):
        path = doc.get('original_file', doc.get('file', ''))
        file_type = doc.get('file_type', 'unknown')
        content = doc.get('content', '')
        importance = doc.get('importance', 5)
        
        score = 0.0
        reasoning = []
        
        # Skip excluded file types
        if file_type in intent.get('exclude_types', []): 
            continue
            
        # Exact file matches (highest priority)
        if any(t.lower() in path.lower() for t in intent.get('target_files', [])):
            score += 2.0
            reasoning.append("Exact file match")
            
        # File pattern matches
        if any(p.lower() in path.lower() or path.endswith(p.strip("*")) for p in intent.get('file_patterns', [])):
            score += 1.5
            reasoning.append("File pattern match")
            
        # File type hints
        if file_type in intent.get('file_type_hints', []):
            score += 1.0
            reasoning.append("File type match")
            
        # Primary keyword matches in content (higher weight)
        primary_matches = sum(1 for k in intent.get('primary_keywords', []) if k.lower() in content.lower())
        if primary_matches > 0:
            score += primary_matches * 0.8
            reasoning.append(f"Primary keywords: {primary_matches}")
            
        # Synonym matches in content
        synonym_matches = sum(1 for k in intent.get('synonyms', []) if k.lower() in content.lower())
        if synonym_matches > 0:
            score += synonym_matches * 0.4
            reasoning.append(f"Synonym matches: {synonym_matches}")
            
        # Language hints
        if any(lang.lower() in path.lower() or lang.lower() in content.lower() 
               for lang in intent.get('language_hints', [])):
            score += 0.6
            reasoning.append("Language match")
            
        # Importance boost (high-importance files get priority)
        if importance >= 8:
            score += 0.8
            reasoning.append("High importance")
        elif importance >= 6:
            score += 0.4
            reasoning.append("Medium importance")
            
        # Architectural pattern matches
        if any(pattern.lower() in content.lower() 
               for pattern in intent.get('architectural_patterns', [])):
            score += 0.7
            reasoning.append("Architecture pattern")
            
        if score > 0:
            matches.append((i, score, " | ".join(reasoning)))
    
    matches.sort(key=lambda x: x[1], reverse=True)
    return matches

def get_enhanced_semantic_matches(question: str, intent: Dict[str, Any], max_results: int = 10) -> List[Tuple[int, float, str]]:
    """Enhanced semantic search with intelligent ranking and metadata filtering"""
    if not index or not doc_map:
        return []
    
    try:
        # Import the enhanced embedder for query processing
        from app.utils.embedder import embed_query
        
        # Use enhanced query embedding
        q_embedding = embed_query(question)
        
        # Search with higher k for re-ranking
        k = min(max_results * 3, len(doc_map.get('chunks', [])) if isinstance(doc_map, dict) else len(doc_map))
        distances, indices = index.search(q_embedding, k)
        
        # Get metadata if available (enhanced format)
        if isinstance(doc_map, dict) and 'metadata' in doc_map:
            metadata_list = doc_map.get('metadata', [])
            chunks = doc_map.get('chunks', [])
        else:
            # Fallback to old format
            metadata_list = []
            chunks = doc_map if isinstance(doc_map, list) else []
        
        # Enhanced ranking with multiple factors
        enhanced_matches = []
        
        for i, (distance, idx) in enumerate(zip(distances[0], indices[0])):
            if idx >= len(chunks):
                continue
                
            chunk = chunks[idx]
            metadata = metadata_list[idx] if idx < len(metadata_list) else {}
            
            # Convert distance to similarity score (higher is better)
            similarity = 1.0 / (1.0 + float(distance))
            
            # Apply intelligent boosting
            boosted_score = similarity
            reasoning_parts = [f"Base: {similarity:.3f}"]
            
            # 1. File importance boost
            importance = metadata.get('importance_score', 0.5)
            if importance >= 0.8:
                boosted_score *= 1.4
                reasoning_parts.append("Critical importance")
            elif importance >= 0.6:
                boosted_score *= 1.3
                reasoning_parts.append("High importance")
            elif importance >= 0.4:
                boosted_score *= 1.1
                reasoning_parts.append("Medium importance")
            
            # 2. Language relevance boost
            detected_lang = _detect_query_language(question)
            file_lang = metadata.get('language', _detect_file_language(chunk.get('file', '')))
            if detected_lang and detected_lang == file_lang:
                boosted_score *= 1.25
                reasoning_parts.append(f"{detected_lang} match")
            
            # 3. Content type boost based on query intent
            if any(term in question.lower() for term in ['function', 'method', 'def']):
                if metadata.get('has_functions', 'def ' in chunk.get('content', '')):
                    boosted_score *= 1.2
                    reasoning_parts.append("Contains functions")
            
            if any(term in question.lower() for term in ['class', 'object', 'interface']):
                if metadata.get('has_classes', 'class ' in chunk.get('content', '')):
                    boosted_score *= 1.2
                    reasoning_parts.append("Contains classes")
            
            # 4. File category relevance
            if any(term in question.lower() for term in ['config', 'settings', 'environment']):
                if metadata.get('is_config', _is_config_file(chunk.get('file', ''))):
                    boosted_score *= 1.3
                    reasoning_parts.append("Configuration file")
            
            if any(term in question.lower() for term in ['test', 'testing', 'spec']):
                if metadata.get('is_test', _is_test_file(chunk.get('file', ''))):
                    boosted_score *= 1.25
                    reasoning_parts.append("Test file")
            
            if any(term in question.lower() for term in ['api', 'endpoint', 'route']):
                if metadata.get('is_api', _is_api_file(chunk.get('file', ''))):
                    boosted_score *= 1.3
                    reasoning_parts.append("API file")
            
            if any(term in question.lower() for term in ['component', 'ui', 'interface']):
                if metadata.get('is_component', _is_component_file(chunk.get('file', ''))):
                    boosted_score *= 1.25
                    reasoning_parts.append("Component file")
            
            # 5. Keyword matching boost
            content = chunk.get('content', '').lower()
            query_words = set(question.lower().split())
            
            # Extract stored keywords if available
            stored_keywords = metadata.get('keywords', [])
            keyword_matches = sum(1 for kw in stored_keywords if any(word in kw.lower() for word in query_words))
            
            # Content keyword overlap
            content_words = set(content.split())
            content_overlap = len(query_words.intersection(content_words))
            
            total_keyword_matches = keyword_matches + content_overlap
            if total_keyword_matches > 0:
                keyword_boost = 1 + (total_keyword_matches * 0.05)  # 5% boost per matching word
                boosted_score *= min(keyword_boost, 1.4)  # Cap at 40% boost
                reasoning_parts.append(f"{total_keyword_matches} keyword matches")
            
            # 6. File path relevance
            file_path = chunk.get('original_file', chunk.get('file', '')).lower()
            if any(word in file_path for word in question.lower().split() if len(word) > 3):
                boosted_score *= 1.15
                reasoning_parts.append("Path relevance")
            
            # 7. Complexity score consideration for implementation questions
            if any(term in question.lower() for term in ['how', 'implement', 'create', 'build']):
                complexity = metadata.get('complexity_score', 0)
                if complexity > 5:  # High complexity files for implementation questions
                    boosted_score *= 1.1
                    reasoning_parts.append("Complex implementation")
            
            # 8. Main file boost
            if metadata.get('is_main', _is_main_file(chunk.get('file', ''))):
                boosted_score *= 1.2
                reasoning_parts.append("Main file")
            
            reasoning = " | ".join(reasoning_parts)
            enhanced_matches.append((int(idx), boosted_score, reasoning))
        
        # Sort by enhanced score and return top results
        enhanced_matches.sort(key=lambda x: x[1], reverse=True)
        return enhanced_matches[:max_results]
        
    except Exception as e:
        print(f"❌ Error in enhanced semantic search: {e}")
        # Fallback to simple semantic search
        return get_semantic_matches(question, intent, max_results)

def _detect_query_language(query: str) -> str:
    """Detect programming language mentioned in query"""
    query_lower = query.lower()
    languages = {
        'python': ['python', 'py', 'django', 'flask', 'fastapi', 'pandas', 'numpy'],
        'javascript': ['javascript', 'js', 'node', 'express', 'react', 'vue', 'angular'],
        'typescript': ['typescript', 'ts', 'tsx'],
        'java': ['java', 'spring', 'maven', 'gradle'],
        'cpp': ['c++', 'cpp', 'cxx'],
        'go': ['golang', 'go'],
        'rust': ['rust', 'rs', 'cargo'],
        'php': ['php', 'laravel', 'symfony'],
        'ruby': ['ruby', 'rails', 'gem'],
        'css': ['css', 'scss', 'sass', 'tailwind'],
        'html': ['html', 'htm'],
        'sql': ['sql', 'database', 'postgres', 'mysql']
    }
    
    for lang, keywords in languages.items():
        if any(keyword in query_lower for keyword in keywords):
            return lang
    
    return None

def _detect_file_language(file_path: str) -> str:
    """Detect programming language from file extension"""
    if not file_path:
        return 'unknown'
    ext = file_path.lower().split('.')[-1]
    language_map = {
        'py': 'python', 'js': 'javascript', 'ts': 'typescript',
        'jsx': 'javascript', 'tsx': 'typescript', 'java': 'java',
        'cpp': 'cpp', 'c': 'cpp', 'go': 'go', 'rs': 'rust',
        'php': 'php', 'rb': 'ruby', 'md': 'markdown',
        'yml': 'yaml', 'yaml': 'yaml', 'json': 'json',
        'html': 'html', 'css': 'css', 'scss': 'css'
    }
    return language_map.get(ext, 'unknown')

def _is_config_file(file_path: str) -> bool:
    """Check if file is a configuration file"""
    if not file_path:
        return False
    return any(term in file_path.lower() for term in ['config', 'settings', '.env', 'dockerfile', 'makefile'])

def _is_test_file(file_path: str) -> bool:
    """Check if file is a test file"""
    if not file_path:
        return False
    return any(term in file_path.lower() for term in ['test', 'spec', '__test__', '.test.', '.spec.'])

def _is_api_file(file_path: str) -> bool:
    """Check if file is an API/route file"""
    if not file_path:
        return False
    return any(term in file_path.lower() for term in ['api', 'route', 'endpoint', 'controller', 'handler'])

def _is_component_file(file_path: str) -> bool:
    """Check if file is a component file"""
    if not file_path:
        return False
    return any(term in file_path.lower() for term in ['component', 'widget', 'view', 'ui'])

def _is_main_file(file_path: str) -> bool:
    """Check if file is a main/entry file"""
    if not file_path:
        return False
    return any(term in file_path.lower() for term in ['main', 'index', 'app', 'entry'])

def get_semantic_matches(question: str, intent: Dict[str, Any], max_results: int = 10) -> List[Tuple[int, float, str]]:
    """
    Basic semantic search as fallback when enhanced search fails
    """
    try:
        if not index or not doc_map:
            return []
            
        q_embedding = np.array(embedder.embed_query(question)).astype('float32').reshape(1, -1)
        D, I = index.search(q_embedding, k=max_results * 2)
        
        # Handle both old and new doc_map formats
        if isinstance(doc_map, dict):
            chunks = doc_map.get('chunks', [])
        else:
            chunks = doc_map
            
        return [(int(idx), 1.0 / (1.0 + D[0][i]), "Semantic match") for i, idx in enumerate(I[0]) if idx < len(chunks)]
    except Exception as e:
        print(f"[ERROR] Basic semantic search failed: {e}")
        return []

def get_intelligent_context(question: str, max_tokens: int) -> Dict[str, Any]:
    """Enhanced context retrieval with structured organization"""
    print(f"[INFO] Using enhanced intelligent context retrieval for: {question}")
    repo_structure = get_repository_structure()
    intent = analyze_user_intent(question, repo_structure)
    
    # Get matches from both strategies - using enhanced semantic search
    intent_matches = find_files_by_intent(intent)
    semantic_matches = get_enhanced_semantic_matches(question, intent)
    
    # Combine and deduplicate, keeping highest scores
    all_matches = intent_matches + semantic_matches
    unique_matches = {}
    for idx, score, reasoning in all_matches:
        if idx not in unique_matches or unique_matches[idx][1] < score:
            unique_matches[idx] = (idx, score, reasoning)
    
    # Sort by score and organize by context priority
    sorted_matches = sorted(unique_matches.values(), key=lambda x: x[1], reverse=True)
    
    # Organize context based on intent and priority
    context_sections = create_structured_context(sorted_matches, intent, max_tokens)
    
    if not context_sections['sections']:
        return {"context": "No relevant files found in the repository.", "chunks_used": 0}
    
    # Build final context with clear structure
    final_context = build_final_context(context_sections, intent)
    
    print(f"[INFO] Enhanced context: {context_sections['total_tokens']} tokens from {context_sections['chunks_used']} chunks")
    return {
        "context": final_context, 
        "chunks_used": context_sections['chunks_used'],
        "context_strategy": intent.get('search_strategy', 'broad_exploration'),
        "intent_type": intent.get('intent_type', 'general_info')
    }

def create_structured_context(matches: List[Tuple[int, float, str]], intent: Dict, max_tokens: int) -> Dict:
    """Organize context into logical sections based on intent"""
    sections = {
        'high_priority': [],
        'main_implementation': [],
        'supporting_files': [],
        'configuration': [],
        'examples': []
    }
    
    current_tokens = 0
    chunks_used = 0
    used_indices = set()
    
    # Reserve tokens for section headers and organization
    header_tokens = 200
    available_tokens = max_tokens - header_tokens
    
    # Allocate tokens based on context priority
    priority = intent.get('context_priority', 'detailed_implementation')
    if priority == 'high_level_overview':
        token_allocation = {'high_priority': 0.6, 'main_implementation': 0.3, 'supporting_files': 0.1}
    elif priority == 'detailed_implementation':
        token_allocation = {'high_priority': 0.3, 'main_implementation': 0.5, 'supporting_files': 0.2}
    elif priority == 'configuration':
        token_allocation = {'configuration': 0.6, 'main_implementation': 0.3, 'supporting_files': 0.1}
    else:  # examples
        token_allocation = {'examples': 0.4, 'main_implementation': 0.4, 'supporting_files': 0.2}
    
    # Categorize and add chunks to appropriate sections
    chunks = doc_map.get('chunks', []) if isinstance(doc_map, dict) else doc_map
    
    for idx, score, reasoning in matches:
        if idx in used_indices or current_tokens >= available_tokens:
            continue
            
        if idx >= len(chunks):
            continue
            
        chunk = chunks[idx]
        file_type = chunk.get('file_type', 'unknown')
        importance = chunk.get('importance', 5)
        
        # Determine section for this chunk
        section = categorize_chunk(chunk, intent, importance)
        max_section_tokens = int(available_tokens * token_allocation.get(section, 0.1))
        
        # Calculate current section tokens
        section_tokens = sum(count_tokens(c['content']) for c in sections[section])
        
        chunk_content = chunk['content']
        chunk_tokens = count_tokens(chunk_content)
        
        if section_tokens + chunk_tokens <= max_section_tokens:
            sections[section].append({
                'file': chunk.get('original_file', chunk.get('file')),
                'content': chunk_content,
                'reasoning': reasoning,
                'score': score,
                'type': file_type,
                'importance': importance
            })
            current_tokens += chunk_tokens
            chunks_used += 1
            used_indices.add(idx)
    
    return {
        'sections': sections,
        'total_tokens': current_tokens,
        'chunks_used': chunks_used,
        'intent': intent
    }

def categorize_chunk(chunk: Dict, intent: Dict, importance: int) -> str:
    """Categorize chunk into appropriate context section"""
    file_type = chunk.get('file_type', 'unknown')
    file_path = chunk.get('original_file', chunk.get('file', ''))
    
    # High priority: main files, high importance, exact matches
    if importance >= 9 or 'main' in file_path.lower() or any(
        target.lower() in file_path.lower() for target in intent.get('target_files', [])
    ):
        return 'high_priority'
    
    # Configuration files
    if file_type in ['config', 'package'] or any(
        pattern in file_path.lower() for pattern in ['config', 'settings', 'env', 'dockerfile', 'makefile']
    ):
        return 'configuration'
    
    # Examples and tests
    if file_type in ['docs'] or any(
        pattern in file_path.lower() for pattern in ['example', 'demo', 'sample', 'tutorial']
    ):
        return 'examples'
    
    # Main implementation
    if file_type == 'source' and importance >= 7:
        return 'main_implementation'
    
    # Everything else is supporting
    return 'supporting_files'

def build_final_context(context_sections: Dict, intent: Dict) -> str:
    """Build the final structured context string"""
    parts = []
    sections = context_sections['sections']
    
    # Add intent summary
    parts.append("=== CONTEXT ANALYSIS ===")
    parts.append(f"Query Intent: {intent.get('intent_type', 'general_info')}")
    parts.append(f"Complexity Level: {intent.get('complexity_level', 'intermediate')}")
    parts.append(f"Search Strategy: {intent.get('search_strategy', 'broad_exploration')}")
    parts.append("")
    
    # Add sections in logical order
    section_order = [
        ('high_priority', 'HIGH PRIORITY FILES'),
        ('main_implementation', 'MAIN IMPLEMENTATION'),
        ('configuration', 'CONFIGURATION'),
        ('supporting_files', 'SUPPORTING FILES'),
        ('examples', 'EXAMPLES & DOCUMENTATION')
    ]
    
    for section_key, section_title in section_order:
        if sections[section_key]:
            parts.append(f"=== {section_title} ===")
            for item in sections[section_key]:
                parts.append(f"File: {item['file']} (Score: {item['score']:.2f}, {item['reasoning']})")
                parts.append(item['content'])
                parts.append("")
    
    return "\n".join(parts)

def format_chat_history(current_question: str, max_tokens: int) -> str:
    """Format last 3 conversations within token limit, but only if relevant to current question"""
    if not chat_history: 
        return ""
    
    # Check if chat history is relevant to current question using LLM
    if not check_chat_history_relevance(current_question, chat_history):
        print(f"[INFO] Chat history not relevant to current question, proceeding without history context")
        return ""
    
    print(f"[INFO] Chat history is relevant, including in context")
    
    # Get last 3 conversations only
    recent_history = chat_history[-3:] if len(chat_history) >= 3 else chat_history
    
    history_parts = []
    current_tokens = 0
    
    for i, entry in enumerate(recent_history):
        conversation_text = f"Previous Question {i+1}: {entry['question']}\nPrevious Answer {i+1}: {entry['answer']}\n\n"
        tokens = count_tokens(conversation_text)
        
        if current_tokens + tokens <= max_tokens:
            history_parts.append(conversation_text)
            current_tokens += tokens
        else:
            # If even one conversation exceeds limit, truncate it
            available_tokens = max_tokens - current_tokens
            if available_tokens > 100:  # Only add if we have reasonable space
                truncated_answer = entry['answer'][:available_tokens//2]  # Rough truncation
                conversation_text = f"Previous Question {i+1}: {entry['question']}\nPrevious Answer {i+1}: {truncated_answer}...[truncated]\n\n"
                history_parts.append(conversation_text)
            break
    
    if history_parts:
        return "=== RECENT CONVERSATION HISTORY (Last 3 conversations) ===\n" + "".join(history_parts) + "="*60 + "\n\n"
    return ""

def answer_question(question: str) -> Dict[str, Any]:
    """Enhanced question answering with relevant conversation history and improved context"""
    print(f"[INFO] Processing question with enhanced context: {question}")
    try:
        # Format last 3 conversations (with relevance check)
        history_context = format_chat_history(question, MAX_HISTORY_TOKENS)
        context_tokens_limit = MAX_CONTEXT_TOKENS - count_tokens(history_context)
        context_result = get_intelligent_context(question, context_tokens_limit)

        # Enhanced prompt with specific instructions about chat history usage
        prompt = f"""You are an expert software developer and code analyst. You have access to a well-organized view of a software repository and recent conversation history.

{history_context}

{context_result['context']}

CURRENT QUESTION: {question}

CRITICAL INSTRUCTIONS:
- ONLY use the conversation history above if it is directly relevant to the current question
- If the previous conversations are about different topics or unrelated code, IGNORE them completely
- Do not mix or confuse information from previous conversations with the current question
- Base your answer primarily on the repository context provided above
- If previous conversations ARE relevant (same feature, same files, related concepts), you may reference them to provide continuity

ANSWER GUIDELINES:
- Provide a comprehensive, detailed, and direct answer to the user's question
- Reference specific files, code sections, and implementation details when relevant
- If the context shows configuration or implementation details, explain how they work together and provide practical examples
- Include code snippets from the repository when they help illustrate your answer
- Use code examples from the context when helpful and explain what they do
- Be thorough and educational - help the user understand both the "what" and the "how"
- If you notice any patterns, best practices, or architectural decisions in the code, mention them
- Only mention previous conversations if they directly relate to the current question
- Focus on giving the user actionable, complete information

ANSWER:"""
        
        # Use tracked LLM call for monitoring
        response = tracked_llm_call(
            module="qa",
            function="answer_question", 
            model="models/gemini-2.0-flash",
            llm_instance=llm,
            prompt=prompt
        )
        
        answer = response.content if hasattr(response, "content") else str(response)
        total_tokens = count_tokens(prompt)

        print(f"[INFO] Enhanced prompt tokens: {total_tokens}")
        print(f"[INFO] Context strategy: {context_result.get('context_strategy', 'unknown')}")
        print(f"[INFO] Intent type: {context_result.get('intent_type', 'unknown')}")
        print(f"[INFO] Chat history included: {'Yes' if history_context else 'No'}")

        # Enhanced response metadata with conversation tracking
        chat_history.append({
            "question": question, 
            "answer": answer,
            "context_strategy": context_result.get('context_strategy'),
            "intent_type": context_result.get('intent_type'),
            "used_history": bool(history_context),
            "timestamp": time.time()
        })
        
        # Keep only last 10 conversations to prevent memory bloat
        if len(chat_history) > 10: 
            chat_history.pop(0)

        return {
            "answer": answer, 
            "context_chunks_used": context_result['chunks_used'], 
            "total_tokens_used": total_tokens,
            "context_strategy": context_result.get('context_strategy', 'broad_exploration'),
            "intent_type": context_result.get('intent_type', 'general_info'),
            "context_quality": "enhanced" if context_result['chunks_used'] > 0 else "limited",
            "history_used": bool(history_context),
            "conversations_referenced": len(chat_history[-3:]) if chat_history else 0
        }
    except Exception as e:
        print(f"[ERROR] Failed to answer question: {e}")
        return {
            "answer": f"Sorry, an error occurred: {e}", 
            "context_chunks_used": 0, 
            "total_tokens_used": 0,
            "context_strategy": "error",
            "intent_type": "error",
            "context_quality": "failed",
            "history_used": False,
            "conversations_referenced": 0
        }

def clear_chat_history():
    global chat_history
    chat_history = []
    print("[INFO] Chat history cleared")

def get_chat_history() -> List[Dict[str, str]]:
    return chat_history.copy()