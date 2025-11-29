# LLM Integration System - Cached, logged, and rate-limited LLM calls
import os
import json
import time
import hashlib
import yaml
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path

from langchain_google_genai import ChatGoogleGenerativeAI
from app.utils.config import GEMINI_API_KEY
from app.utils.llm_tracker import tracked_llm_call, tracker

# Initialize the LLM
llm = ChatGoogleGenerativeAI(model="models/gemini-2.0-flash", google_api_key=GEMINI_API_KEY)

@dataclass
class LLMCallContext:
    """Context information for LLM calls"""
    node_name: str
    function_name: str
    purpose: str
    expected_format: str = "text"
    max_retries: int = 3
    cache_enabled: bool = True
    rate_limit_pause: float = 1.0

@dataclass
class LLMResponse:
    """Standardized LLM response with metadata"""
    content: str
    success: bool
    cached: bool = False
    retry_count: int = 0
    execution_time: float = 0.0
    error: Optional[str] = None
    tokens_used: int = 0
    cache_key: Optional[str] = None

class LLMCache:
    """Persistent caching system for LLM responses"""
    
    def __init__(self, cache_file: str = "llm_cache.json"):
        self.cache_file = cache_file
        self.cache: Dict[str, Dict[str, Any]] = self._load_cache()
        self.cache_hits = 0
        self.cache_misses = 0
    
    def _load_cache(self) -> Dict[str, Dict[str, Any]]:
        """Load cache from disk"""
        try:
            if Path(self.cache_file).exists():
                with open(self.cache_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"[WARNING] Failed to load cache: {e}")
        return {}
    
    def _save_cache(self):
        """Save cache to disk"""
        try:
            with open(self.cache_file, 'w') as f:
                json.dump(self.cache, f, indent=2)
        except Exception as e:
            print(f"[WARNING] Failed to save cache: {e}")
    
    def _generate_key(self, prompt: str, context: LLMCallContext) -> str:
        """Generate unique cache key for prompt and context"""
        key_data = f"{prompt}|{context.node_name}|{context.function_name}|{context.expected_format}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def get(self, prompt: str, context: LLMCallContext) -> Optional[LLMResponse]:
        """Retrieve cached response"""
        if not context.cache_enabled:
            return None
        
        cache_key = self._generate_key(prompt, context)
        if cache_key in self.cache:
            cached_data = self.cache[cache_key]
            self.cache_hits += 1
            print(f"[CACHE HIT] Using cached response for {context.node_name}.{context.function_name}")
            return LLMResponse(
                content=cached_data["content"],
                success=cached_data["success"],
                cached=True,
                execution_time=0.0,
                tokens_used=cached_data.get("tokens_used", 0),
                cache_key=cache_key
            )
        
        self.cache_misses += 1
        return None
    
    def set(self, prompt: str, context: LLMCallContext, response: LLMResponse):
        """Store response in cache"""
        if not context.cache_enabled or not response.success:
            return
        
        cache_key = self._generate_key(prompt, context)
        self.cache[cache_key] = {
            "content": response.content,
            "success": response.success,
            "timestamp": datetime.now().isoformat(),
            "node_name": context.node_name,
            "function_name": context.function_name,
            "tokens_used": response.tokens_used,
            "execution_time": response.execution_time
        }
        
        response.cache_key = cache_key
        self._save_cache()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_requests = self.cache_hits + self.cache_misses
        hit_rate = (self.cache_hits / total_requests * 100) if total_requests > 0 else 0
        
        return {
            "total_cached_responses": len(self.cache),
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "hit_rate_percent": round(hit_rate, 2),
            "cache_file_size": Path(self.cache_file).stat().st_size if Path(self.cache_file).exists() else 0
        }

# Global cache instance
llm_cache = LLMCache()

def call_llm(prompt: str, context: LLMCallContext) -> LLMResponse:
    """
    Enhanced LLM call with caching, logging, retries, and rate limiting
    """
    start_time = time.time()
    
    # Check cache first
    cached_response = llm_cache.get(prompt, context)
    if cached_response:
        return cached_response
    
    # Rate limiting pause
    if context.rate_limit_pause > 0:
        time.sleep(context.rate_limit_pause)
    
    retry_count = 0
    last_error = None
    
    while retry_count <= context.max_retries:
        try:
            print(f"[LLM CALL] {context.node_name}.{context.function_name} (attempt {retry_count + 1})")
            
            # Make tracked LLM call
            response = tracked_llm_call(
                module=f"flow_node_{context.node_name}",
                function=context.function_name,
                model="models/gemini-2.0-flash",
                llm_instance=llm,
                prompt=prompt
            )
            
            content = response.content if hasattr(response, "content") else str(response)
            execution_time = time.time() - start_time
            
            # Validate response format if specified
            if context.expected_format == "yaml":
                try:
                    # Use the same extraction logic as parse_yaml_response
                    yaml_content = content
                    if "```yaml" in yaml_content:
                        yaml_start = yaml_content.find("```yaml") + 7
                        yaml_end = yaml_content.find("```", yaml_start)
                        if yaml_end != -1:
                            yaml_content = yaml_content[yaml_start:yaml_end].strip()
                    elif "```" in yaml_content:
                        yaml_start = yaml_content.find("```") + 3
                        yaml_end = yaml_content.find("```", yaml_start)
                        if yaml_end != -1:
                            yaml_content = yaml_content[yaml_start:yaml_end].strip()
                    
                    yaml.safe_load(yaml_content)
                except yaml.YAMLError as e:
                    raise ValueError(f"Invalid YAML format: {e}")
            elif context.expected_format == "json":
                try:
                    # Use the same extraction logic as parse_json_response
                    json_content = content
                    if "```json" in json_content:
                        json_start = json_content.find("```json") + 7
                        json_end = json_content.find("```", json_start)
                        if json_end != -1:
                            json_content = json_content[json_start:json_end].strip()
                    elif "```" in json_content:
                        json_start = json_content.find("```") + 3
                        json_end = json_content.find("```", json_start)
                        if json_end != -1:
                            json_content = json_content[json_start:json_end].strip()
                    
                    json.loads(json_content)
                except json.JSONDecodeError as e:
                    raise ValueError(f"Invalid JSON format: {e}")
            
            # Create successful response
            llm_response = LLMResponse(
                content=content,
                success=True,
                retry_count=retry_count,
                execution_time=execution_time,
                tokens_used=len(content.split())  # Rough estimate
            )
            
            # Cache the response
            llm_cache.set(prompt, context, llm_response)
            
            print(f"[LLM SUCCESS] {context.node_name}.{context.function_name} ({execution_time:.2f}s)")
            return llm_response
            
        except Exception as e:
            retry_count += 1
            last_error = str(e)
            
            print(f"[LLM ERROR] Attempt {retry_count} failed: {last_error}")
            
            if retry_count <= context.max_retries:
                wait_time = 2 ** retry_count  # Exponential backoff
                print(f"[LLM RETRY] Waiting {wait_time}s before retry...")
                time.sleep(wait_time)
    
    # All retries failed
    execution_time = time.time() - start_time
    return LLMResponse(
        content="",
        success=False,
        retry_count=retry_count - 1,
        execution_time=execution_time,
        error=f"Failed after {context.max_retries} retries. Last error: {last_error}"
    )

def parse_yaml_response(content: str, fallback_data: Any = None) -> Any:
    """
    Parse YAML response with comprehensive error handling
    """
    if not content.strip():
        print("[WARNING] Empty LLM response, using fallback")
        return fallback_data
    
    print(f"[DEBUG] Raw LLM response length: {len(content)}")
    print(f"[DEBUG] Response preview: {content[:200]}...")
    
    # Try to extract YAML from markdown code blocks
    if "```yaml" in content:
        yaml_start = content.find("```yaml") + 7
        yaml_end = content.find("```", yaml_start)
        if yaml_end != -1:
            content = content[yaml_start:yaml_end].strip()
            print(f"[DEBUG] Extracted YAML from ```yaml block, length: {len(content)}")
    elif "```" in content:
        # Generic code block
        yaml_start = content.find("```") + 3
        yaml_end = content.find("```", yaml_start)
        if yaml_end != -1:
            content = content[yaml_start:yaml_end].strip()
            print(f"[DEBUG] Extracted YAML from generic code block, length: {len(content)}")
    
    print(f"[DEBUG] Final YAML content preview: {content[:300]}...")
    
    try:
        parsed_data = yaml.safe_load(content)
        print(f"[DEBUG] YAML parsed successfully, type: {type(parsed_data)}")
        if isinstance(parsed_data, dict) and 'abstractions' in parsed_data:
            abstractions = parsed_data['abstractions']
            print(f"[DEBUG] Found {len(abstractions)} abstractions in parsed data")
            return abstractions
        elif isinstance(parsed_data, list):
            print(f"[DEBUG] Parsed data is a list with {len(parsed_data)} items")
            return parsed_data
        else:
            print(f"[DEBUG] Parsed data is not expected format: {parsed_data}")
            if parsed_data is None:
                print("[WARNING] YAML parsed to None, using fallback")
                return fallback_data
            return parsed_data
    except yaml.YAMLError as e:
        print(f"[ERROR] YAML parsing failed: {e}")
        print(f"[DEBUG] Content: {content[:500]}...")
        return fallback_data

def parse_json_response(content: str, fallback_data: Any = None) -> Any:
    """
    Parse JSON response with comprehensive error handling
    """
    if not content.strip():
        print("[WARNING] Empty LLM response, using fallback")
        return fallback_data
    
    # Try to extract JSON from markdown code blocks
    if "```json" in content:
        json_start = content.find("```json") + 7
        json_end = content.find("```", json_start)
        if json_end != -1:
            content = content[json_start:json_end].strip()
    elif "```" in content:
        # Generic code block
        json_start = content.find("```") + 3
        json_end = content.find("```", json_start)
        if json_end != -1:
            content = content[json_start:json_end].strip()
    
    # Try to find JSON object/array boundaries
    if not content.startswith(('[', '{')):
        # Look for JSON start
        for i, char in enumerate(content):
            if char in '[{':
                content = content[i:]
                break
    
    try:
        parsed_data = json.loads(content)
        return parsed_data
    except json.JSONDecodeError as e:
        print(f"[ERROR] JSON parsing failed: {e}")
        print(f"[DEBUG] Content: {content[:500]}...")
        return fallback_data

def get_llm_stats() -> Dict[str, Any]:
    """Get comprehensive LLM usage statistics"""
    cache_stats = llm_cache.get_stats()
    tracker_stats = {
        "total_calls": tracker.session_stats["total_calls"],
        "total_tokens": tracker.session_stats["total_tokens"],
        "total_cost_estimate": tracker.session_stats["total_cost_estimate"],
        "errors": tracker.session_stats["errors"],
        "retries": tracker.session_stats["retries"]
    }
    
    return {
        "cache": cache_stats,
        "tracker": tracker_stats,
        "combined_efficiency": {
            "cache_hit_rate": cache_stats["hit_rate_percent"],
            "error_rate": (tracker_stats["errors"] / max(tracker_stats["total_calls"], 1)) * 100,
            "average_retries": tracker_stats["retries"] / max(tracker_stats["total_calls"], 1)
        }
    }

def export_llm_logs(filename: str = "llm_comprehensive_log.json"):
    """Export comprehensive LLM usage logs"""
    stats = get_llm_stats()
    log_data = {
        "timestamp": datetime.now().isoformat(),
        "statistics": stats,
        "cache_data": llm_cache.cache,
        "tracker_calls": [asdict(call) for call in tracker.calls]
    }
    
    with open(filename, "w") as f:
        json.dump(log_data, f, indent=2, default=str)
    
    print(f"[INFO] Comprehensive LLM logs exported to {filename}")

# Example usage context creators for different nodes
def create_abstraction_context() -> LLMCallContext:
    return LLMCallContext(
        node_name="IdentifyAbstractions",
        function_name="identify_core_concepts",
        purpose="Identify key abstractions in codebase for tutorial structure",
        expected_format="yaml",
        max_retries=3,
        cache_enabled=True,
        rate_limit_pause=2.0
    )

def create_relationship_context() -> LLMCallContext:
    return LLMCallContext(
        node_name="AnalyzeRelationships", 
        function_name="analyze_dependencies",
        purpose="Analyze relationships between abstractions",
        expected_format="yaml",
        max_retries=3,
        cache_enabled=True,
        rate_limit_pause=2.0
    )

def create_ordering_context() -> LLMCallContext:
    return LLMCallContext(
        node_name="OrderChapters",
        function_name="sequence_learning_path",
        purpose="Determine optimal chapter ordering for learning",
        expected_format="yaml",
        max_retries=3,
        cache_enabled=True,
        rate_limit_pause=2.0
    )

def create_writing_context() -> LLMCallContext:
    return LLMCallContext(
        node_name="WriteChapters",
        function_name="generate_chapter_content",
        purpose="Generate tutorial chapter content",
        expected_format="text",
        max_retries=2,
        cache_enabled=True,
        rate_limit_pause=3.0  # Longer pause for content generation
    )
