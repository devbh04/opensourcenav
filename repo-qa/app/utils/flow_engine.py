# Flow Engine - Core orchestration system for tutorial generation
import time
import json
import traceback
from typing import Dict, Any, List, Optional, Callable
from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict
from datetime import datetime

@dataclass
class NodeResult:
    """Standard result format for all node operations"""
    success: bool
    data: Any = None
    error: Optional[str] = None
    execution_time: float = 0.0
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

class Node(ABC):
    """Base class for all tutorial generation nodes"""
    
    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self.next_nodes: List['Node'] = []
        self.execution_log: List[Dict[str, Any]] = []
    
    def __rshift__(self, other: 'Node') -> 'Node':
        """Enable >> operator for chaining nodes"""
        self.next_nodes.append(other)
        return other
    
    @abstractmethod
    def prep(self, shared: Dict[str, Any]) -> NodeResult:
        """Prepare data for execution by reading from shared state"""
        pass
    
    @abstractmethod
    def exec(self, prep_result: NodeResult) -> NodeResult:
        """Execute the main node logic"""
        pass
    
    @abstractmethod
    def post(self, shared: Dict[str, Any], prep_result: NodeResult, exec_result: NodeResult) -> NodeResult:
        """Update shared state with execution results"""
        pass
    
    def run(self, shared: Dict[str, Any]) -> NodeResult:
        """Execute the complete node lifecycle with comprehensive logging"""
        start_time = time.time()
        
        try:
            print(f"\n{'='*60}")
            print(f"🚀 EXECUTING NODE: {self.name}")
            print(f"{'='*60}")
            print(f"Description: {self.description}")
            print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Step 1: Prep
            print(f"\n[1/3] 📋 PREP Phase...")
            prep_result = self.prep(shared)
            if not prep_result.success:
                return self._log_failure("PREP", prep_result.error, start_time)
            print(f"    ✅ Prep completed successfully")
            
            # Step 2: Exec
            print(f"\n[2/3] ⚡ EXEC Phase...")
            exec_result = self.exec(prep_result)
            if not exec_result.success:
                return self._log_failure("EXEC", exec_result.error, start_time)
            print(f"    ✅ Execution completed successfully")
            
            # Step 3: Post
            print(f"\n[3/3] 📝 POST Phase...")
            post_result = self.post(shared, prep_result, exec_result)
            if not post_result.success:
                return self._log_failure("POST", post_result.error, start_time)
            print(f"    ✅ Post-processing completed successfully")
            
            execution_time = time.time() - start_time
            
            # Log successful execution
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "node": self.name,
                "success": True,
                "execution_time": execution_time,
                "prep_metadata": prep_result.metadata,
                "exec_metadata": exec_result.metadata,
                "post_metadata": post_result.metadata
            }
            self.execution_log.append(log_entry)
            
            print(f"\n🎉 NODE COMPLETED: {self.name}")
            print(f"⏱️  Total Execution Time: {execution_time:.2f}s")
            print(f"{'='*60}")
            
            return NodeResult(
                success=True,
                data=post_result.data,
                execution_time=execution_time,
                metadata={"log_entry": log_entry}
            )
            
        except Exception as e:
            error_msg = f"Unexpected error in {self.name}: {str(e)}\n{traceback.format_exc()}"
            return self._log_failure("EXCEPTION", error_msg, start_time)
    
    def _log_failure(self, phase: str, error: str, start_time: float) -> NodeResult:
        """Log node failure with details"""
        execution_time = time.time() - start_time
        
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "node": self.name,
            "success": False,
            "phase": phase,
            "error": error,
            "execution_time": execution_time
        }
        self.execution_log.append(log_entry)
        
        print(f"\n❌ NODE FAILED: {self.name}")
        print(f"💥 Phase: {phase}")
        print(f"🚨 Error: {error}")
        print(f"⏱️  Execution Time: {execution_time:.2f}s")
        print(f"{'='*60}")
        
        return NodeResult(
            success=False,
            error=error,
            execution_time=execution_time,
            metadata={"log_entry": log_entry}
        )

class Flow:
    """Orchestrates the execution of connected nodes"""
    
    def __init__(self, start_node: Node, name: str = "Tutorial Generation Flow"):
        self.start_node = start_node
        self.name = name
        self.execution_history: List[Dict[str, Any]] = []
        self.shared_state_snapshots: List[Dict[str, Any]] = []
    
    def run(self, shared: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the complete flow with comprehensive tracking"""
        flow_start_time = time.time()
        
        print(f"\n🌟 STARTING FLOW: {self.name}")
        print(f"🕐 Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📊 Initial Shared State Keys: {list(shared.keys())}")
        
        # Save initial state snapshot
        self._save_state_snapshot(shared, "INITIAL")
        
        try:
            # Execute nodes in sequence
            current_node = self.start_node
            visited_nodes = []
            
            while current_node:
                # Check for circular dependencies
                if current_node.name in visited_nodes:
                    raise RuntimeError(f"Circular dependency detected: {current_node.name}")
                
                visited_nodes.append(current_node.name)
                
                # Execute current node
                result = current_node.run(shared)
                
                # Save state snapshot after each node
                self._save_state_snapshot(shared, f"AFTER_{current_node.name}")
                
                if not result.success:
                    raise RuntimeError(f"Node {current_node.name} failed: {result.error}")
                
                # Move to next node (if any)
                current_node = current_node.next_nodes[0] if current_node.next_nodes else None
            
            flow_execution_time = time.time() - flow_start_time
            
            # Log successful flow completion
            flow_log = {
                "timestamp": datetime.now().isoformat(),
                "flow_name": self.name,
                "success": True,
                "nodes_executed": visited_nodes,
                "total_execution_time": flow_execution_time,
                "final_shared_keys": list(shared.keys())
            }
            self.execution_history.append(flow_log)
            
            print(f"\n🎊 FLOW COMPLETED SUCCESSFULLY: {self.name}")
            print(f"✅ Nodes Executed: {' → '.join(visited_nodes)}")
            print(f"⏱️  Total Flow Time: {flow_execution_time:.2f}s")
            print(f"📈 Final Shared State Keys: {list(shared.keys())}")
            
            return {
                "success": True,
                "shared_state": shared,
                "execution_log": flow_log,
                "node_details": [node.execution_log for node in self._get_all_nodes()]
            }
            
        except Exception as e:
            flow_execution_time = time.time() - flow_start_time
            
            flow_log = {
                "timestamp": datetime.now().isoformat(),
                "flow_name": self.name,
                "success": False,
                "error": str(e),
                "nodes_executed": visited_nodes,
                "total_execution_time": flow_execution_time
            }
            self.execution_history.append(flow_log)
            
            print(f"\n💥 FLOW FAILED: {self.name}")
            print(f"🚨 Error: {str(e)}")
            print(f"⏱️  Flow Time: {flow_execution_time:.2f}s")
            print(f"📊 Nodes Completed: {visited_nodes}")
            
            return {
                "success": False,
                "error": str(e),
                "shared_state": shared,
                "execution_log": flow_log,
                "node_details": [node.execution_log for node in self._get_all_nodes()]
            }
    
    def _save_state_snapshot(self, shared: Dict[str, Any], stage: str):
        """Save a snapshot of shared state for debugging"""
        snapshot = {
            "stage": stage,
            "timestamp": datetime.now().isoformat(),
            "keys": list(shared.keys()),
            "data_sizes": {k: len(str(v)) for k, v in shared.items()},
            # Store a limited sample for debugging (not full data)
            "sample_data": {k: str(v)[:200] + "..." if len(str(v)) > 200 else str(v) 
                          for k, v in shared.items() if k in ["project_name", "language", "repo_url"]}
        }
        self.shared_state_snapshots.append(snapshot)
    
    def _get_all_nodes(self) -> List[Node]:
        """Get all nodes in the flow for logging purposes"""
        nodes = []
        visited = set()
        
        def collect_nodes(node):
            if node and node.name not in visited:
                visited.add(node.name)
                nodes.append(node)
                for next_node in node.next_nodes:
                    collect_nodes(next_node)
        
        collect_nodes(self.start_node)
        return nodes
    
    def export_logs(self, filename: str = "flow_execution_log.json"):
        """Export comprehensive execution logs"""
        log_data = {
            "flow_name": self.name,
            "execution_history": self.execution_history,
            "state_snapshots": self.shared_state_snapshots,
            "node_logs": {node.name: node.execution_log for node in self._get_all_nodes()}
        }
        
        with open(filename, "w") as f:
            json.dump(log_data, f, indent=2, default=str)
        
        print(f"[INFO] Flow execution logs exported to {filename}")

def create_shared_state(repo_url: str = "", local_dir: str = "", project_name: str = "", 
                       output_dir: str = "tutorial_output", language: str = "english") -> Dict[str, Any]:
    """Create initial shared state dictionary"""
    return {
        # Initial inputs
        "repo_url": repo_url,
        "local_dir": local_dir, 
        "project_name": project_name or "Unknown Project",
        "output_dir": output_dir,
        "language": language,
        
        # Processing configuration
        "include_patterns": ["*.py", "*.js", "*.ts", "*.jsx", "*.tsx", "*.java", "*.cpp", "*.c", "*.h", "*.md", "*.txt"],
        "exclude_patterns": ["node_modules/*", ".git/*", "__pycache__/*", "*.pyc", "dist/*", "build/*"],
        "max_file_size": 100000,  # 100KB per file
        "max_abstractions": 12,
        "min_abstractions": 5,
        
        # Node outputs (populated during flow execution)
        "files": [],           # From FetchRepo: [(filepath, content), ...]
        "abstractions": [],    # From IdentifyAbstractions: [abstraction_objects]
        "relationships": {},   # From AnalyzeRelationships: {summary, relationships}
        "chapter_order": [],   # From OrderChapters: [abstraction_indices]
        "chapters": [],        # From WriteChapters: [chapter_content]
        "final_output_dir": "", # From CombineTutorial: actual output path
        
        # Execution metadata
        "start_time": datetime.now().isoformat(),
        "total_files_processed": 0,
        "total_content_size": 0,
        "errors": [],
        "warnings": []
    }
