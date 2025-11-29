# LLM Call Tracker and Rate Limit Monitor

import time
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from transformers import GPT2TokenizerFast

tokenizer = GPT2TokenizerFast.from_pretrained("gpt2")

@dataclass
class LLMCallMetrics:
    """Track metrics for each LLM call"""
    timestamp: float
    module: str
    function: str
    call_id: str
    model: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    response_time: float
    success: bool
    error_message: Optional[str] = None
    retry_count: int = 0
    rate_limit_pause: float = 0.0

class LLMCallTracker:
    """Global tracker for all LLM calls across the project"""
    
    def __init__(self):
        self.calls: List[LLMCallMetrics] = []
        self.rate_limits = {
            "gemini-2.0-flash": {
                "requests_per_minute": 60,
                "tokens_per_minute": 100000,
                "requests_per_day": 1500,
                "tokens_per_day": 1000000
            },
            "embedding-001": {
                "requests_per_minute": 1500,
                "tokens_per_minute": 500000
            }
        }
        self.session_stats = {
            "total_calls": 0,
            "total_tokens": 0,
            "total_cost_estimate": 0.0,
            "errors": 0,
            "retries": 0
        }
    
    def should_pause_for_rate_limit(self, model: str, tokens: int) -> float:
        """Calculate if we need to pause for rate limiting"""
        now = time.time()
        recent_calls = [c for c in self.calls if c.model == model and now - c.timestamp < 60]
        
        if model not in self.rate_limits:
            return 0.0
        
        limits = self.rate_limits[model]
        
        # Check requests per minute
        if len(recent_calls) >= limits["requests_per_minute"]:
            return 60.0
        
        # Check tokens per minute
        recent_tokens = sum(c.total_tokens for c in recent_calls)
        if recent_tokens + tokens > limits["tokens_per_minute"]:
            return 60.0
        
        return 0.0
    
    def log_call(self, metrics: LLMCallMetrics):
        """Log an LLM call with full metrics"""
        self.calls.append(metrics)
        self.session_stats["total_calls"] += 1
        self.session_stats["total_tokens"] += metrics.total_tokens
        
        if not metrics.success:
            self.session_stats["errors"] += 1
        if metrics.retry_count > 0:
            self.session_stats["retries"] += metrics.retry_count
        
        # Estimate cost (rough estimates for Gemini)
        if "gemini-2.0-flash" in metrics.model:
            # Rough estimate: $0.0015 per 1K tokens for input, $0.006 per 1K tokens for output
            input_cost = (metrics.input_tokens / 1000) * 0.0015
            output_cost = (metrics.output_tokens / 1000) * 0.006
            self.session_stats["total_cost_estimate"] += input_cost + output_cost
        
        # Print real-time tracking
        self._print_call_summary(metrics)
    
    def _print_call_summary(self, metrics: LLMCallMetrics):
        """Print a summary of the LLM call"""
        status = "✅ SUCCESS" if metrics.success else "❌ FAILED"
        print(f"\n{'='*60}")
        print(f"LLM CALL TRACKING - {status}")
        print(f"{'='*60}")
        print(f"Module: {metrics.module}")
        print(f"Function: {metrics.function}")
        print(f"Model: {metrics.model}")
        print(f"Call ID: {metrics.call_id}")
        print(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(metrics.timestamp))}")
        print(f"Input Tokens: {metrics.input_tokens:,}")
        print(f"Output Tokens: {metrics.output_tokens:,}")
        print(f"Total Tokens: {metrics.total_tokens:,}")
        print(f"Response Time: {metrics.response_time:.2f}s")
        if metrics.retry_count > 0:
            print(f"Retries: {metrics.retry_count}")
        if metrics.rate_limit_pause > 0:
            print(f"Rate Limit Pause: {metrics.rate_limit_pause:.1f}s")
        if metrics.error_message:
            print(f"Error: {metrics.error_message}")
        
        # Session summary
        print(f"\n📊 SESSION SUMMARY:")
        print(f"Total Calls: {self.session_stats['total_calls']}")
        print(f"Total Tokens: {self.session_stats['total_tokens']:,}")
        print(f"Estimated Cost: ${self.session_stats['total_cost_estimate']:.4f}")
        print(f"Errors: {self.session_stats['errors']}")
        print(f"Retries: {self.session_stats['retries']}")
        print(f"{'='*60}\n")
    
    def get_rate_limit_status(self) -> Dict[str, Any]:
        """Get current rate limit status for all models"""
        now = time.time()
        status = {}
        
        for model, limits in self.rate_limits.items():
            recent_calls = [c for c in self.calls if c.model == model and now - c.timestamp < 60]
            recent_tokens = sum(c.total_tokens for c in recent_calls)
            
            status[model] = {
                "requests_last_minute": len(recent_calls),
                "tokens_last_minute": recent_tokens,
                "requests_limit": limits["requests_per_minute"],
                "tokens_limit": limits["tokens_per_minute"],
                "requests_remaining": limits["requests_per_minute"] - len(recent_calls),
                "tokens_remaining": limits["tokens_per_minute"] - recent_tokens,
                "next_reset": now + 60 - (now % 60)
            }
        
        return status
    
    def export_metrics(self, filename: str = "llm_call_metrics.json"):
        """Export all metrics to JSON file"""
        data = {
            "session_stats": self.session_stats,
            "rate_limit_status": self.get_rate_limit_status(),
            "all_calls": [asdict(call) for call in self.calls]
        }
        
        with open(filename, "w") as f:
            json.dump(data, f, indent=2, default=str)
        
        print(f"[INFO] LLM metrics exported to {filename}")

# Global tracker instance
tracker = LLMCallTracker()

def count_tokens(text: str) -> int:
    """Count tokens in text"""
    return len(tokenizer.encode(str(text)))

def tracked_llm_call(module: str, function: str, model: str, llm_instance, prompt: str, **kwargs) -> Any:
    """Wrapper function to track all LLM calls with comprehensive metrics"""
    call_id = f"{module}_{function}_{int(time.time())}_{len(tracker.calls)}"
    start_time = time.time()
    
    input_tokens = count_tokens(prompt)
    
    # Check rate limits
    pause_time = tracker.should_pause_for_rate_limit(model, input_tokens)
    if pause_time > 0:
        print(f"[RATE LIMIT] Pausing {pause_time:.1f}s for {model}")
        time.sleep(pause_time)
    
    try:
        # Make the actual LLM call
        response = llm_instance.invoke(prompt, **kwargs)
        
        # Extract response content
        content = response.content if hasattr(response, "content") else str(response)
        output_tokens = count_tokens(content)
        total_tokens = input_tokens + output_tokens
        response_time = time.time() - start_time
        
        # Log successful call
        metrics = LLMCallMetrics(
            timestamp=start_time,
            module=module,
            function=function,
            call_id=call_id,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            response_time=response_time,
            success=True,
            rate_limit_pause=pause_time
        )
        
        tracker.log_call(metrics)
        return response
        
    except Exception as e:
        # Log failed call
        response_time = time.time() - start_time
        metrics = LLMCallMetrics(
            timestamp=start_time,
            module=module,
            function=function,
            call_id=call_id,
            model=model,
            input_tokens=input_tokens,
            output_tokens=0,
            total_tokens=input_tokens,
            response_time=response_time,
            success=False,
            error_message=str(e),
            rate_limit_pause=pause_time
        )
        
        tracker.log_call(metrics)
        raise e
