"""
Base Agent Class for Playbook Prioritizer Agent System

This module provides the foundation for all specialized agents with:
- State machine management (idle → analyzing → completed)
- Progress tracking and status updates
- Error handling and recovery
- Communication interfaces
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import time
import threading
from datetime import datetime

from models.play_models import (
    Play, 
    AgentState, 
    AgentStatus, 
    SubjectArea,
    WorkflowStatus
)
from agents.network_agent import NetworkAgent


class BaseAgent(ABC):
    """Base class for all specialized agents"""
    
    def __init__(self, agent_id: str, name: str, subject_area: SubjectArea):
        """Initialize base agent"""
        self.agent_id = agent_id
        self.name = name
        self.subject_area = subject_area
        
        # State management
        self.state = AgentState()
        self.workflow_status = WorkflowStatus()
        
        # Execution control
        self._execution_thread: Optional[threading.Thread] = None
        self._stop_execution = threading.Event()
        self._lock = threading.Lock()
        
        # Results storage
        self.generated_plays: List[Play] = []
        self.execution_log: List[Dict[str, Any]] = []
        
        # Configuration
        self.max_execution_time = 300  # 5 minutes
        self.progress_update_interval = 0.5  # seconds
        
    def start_execution(self, task_description: str = None) -> bool:
        """Start agent execution in a separate thread"""
        with self._lock:
            if self.state.status == AgentStatus.ANALYZING:
                return False  # Already running
            
            # Reset state
            self.state.reset()
            self._stop_execution.clear()
            
            # Start execution
            task = task_description or f"Analyzing {self.subject_area.value} area"
            self.state.start_execution(task)
            
            # Create and start execution thread
            self._execution_thread = threading.Thread(
                target=self._execute_with_progress,
                args=(task,),
                daemon=True
            )
            self._execution_thread.start()
            
            return True
    
    def stop_execution(self) -> bool:
        """Stop agent execution gracefully"""
        with self._lock:
            if self.state.status != AgentStatus.ANALYZING:
                return False
            
            self._stop_execution.set()
            return True
    
    def wait_for_completion(self, timeout: float = None) -> bool:
        """Wait for agent execution to complete"""
        if not self._execution_thread:
            return False
        
        if timeout:
            self._execution_thread.join(timeout=timeout)
            return not self._execution_thread.is_alive()
        else:
            self._execution_thread.join()
            return True
    
    def get_status(self) -> Dict[str, Any]:
        """Get current agent status"""
        with self._lock:
            return {
                "agent_id": self.agent_id,
                "name": self.name,
                "subject_area": self.subject_area.value,
                "state": self.state.to_dict(),
                "workflow_status": self.workflow_status.to_dict(),
                "plays_count": len(self.generated_plays),
                "is_running": self.state.status == AgentStatus.ANALYZING
            }
    
    def get_plays(self) -> List[Play]:
        """Get generated plays from this agent"""
        with self._lock:
            return self.generated_plays.copy()
    
    def clear_results(self):
        """Clear all results and reset to initial state"""
        with self._lock:
            self.generated_plays.clear()
            self.execution_log.clear()
            self.state.reset()
            self.workflow_status = WorkflowStatus()
    
    def _execute_with_progress(self, task: str):
        """Execute agent logic with progress updates"""
        try:
            # Update workflow status
            self.workflow_status.advance_phase(self.workflow_status.current_phase)
            
            # Execute the main logic
            self._execute_agent_logic(task)
            
            # Mark as completed
            self.state.complete_execution()
            self.workflow_status.advance_phase(self.workflow_status.current_phase)
            
        except Exception as e:
            # Handle execution errors
            error_msg = f"Execution failed: {str(e)}"
            self.state.fail_execution(error_msg)
            self._log_error(error_msg, e)
    
    @abstractmethod
    def _execute_agent_logic(self, task: str):
        """Execute the specific agent logic - must be implemented by subclasses"""
        pass
    
    def _update_progress(self, progress: float, task: str = None):
        """Update execution progress"""
        with self._lock:
            self.state.update_progress(progress, task)
            self.workflow_status.update_phase_progress(progress)
            
            # Calculate total progress
            total_progress = progress  # Simplified for now
            self.workflow_status.update_total_progress(total_progress)
    
    def _add_play(self, play: Play):
        """Add a generated play to the agent's results"""
        with self._lock:
            self.generated_plays.append(play)
    
    def _log_execution(self, message: str, level: str = "INFO", data: Dict[str, Any] = None):
        """Log execution information"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "level": level,
            "message": message,
            "data": data or {}
        }
        
        with self._lock:
            self.execution_log.append(log_entry)
    
    def _log_error(self, message: str, error: Exception):
        """Log error information"""
        self._log_execution(
            message=message,
            level="ERROR",
            data={
                "error_type": type(error).__name__,
                "error_details": str(error)
            }
        )
    
    def _should_stop_execution(self) -> bool:
        """Check if execution should be stopped"""
        return self._stop_execution.is_set()
    
    def _simulate_work(self, duration: float, task: str, progress_steps: int = 10):
        """Simulate work with progress updates (useful for mock agents)"""
        step_duration = duration / progress_steps
        
        for i in range(progress_steps + 1):
            if self._should_stop_execution():
                return False
            
            progress = i / progress_steps
            self._update_progress(progress, task)
            
            if i < progress_steps:
                time.sleep(step_duration)
        
        return True


class SubjectAreaAgent(BaseAgent):
    """Specialized agent for analyzing specific subject areas"""
    
    def __init__(self, subject_area: SubjectArea, agent_id: str = None, name: str = None):
        """Initialize subject area agent"""
        if agent_id is None:
            agent_id = f"{subject_area.value}_agent"
        
        if name is None:
            name = f"{subject_area.value.title()} Analysis Agent"
        
        super().__init__(agent_id, name, subject_area)
        
        # Subject area specific configuration
        self.analysis_depth = "comprehensive"  # basic, standard, comprehensive
        self.max_plays_per_area = 5
        self.min_confidence_score = 0.7
    
    def _execute_agent_logic(self, task: str):
        """Execute subject area analysis logic using mock intelligence"""
        # Explicit start marker for stub agents
        self._log_execution("START: Subject area analysis", "INFO")
        
        # Simulate work and generate plays using the mock intelligence engine
        # Extend duration and steps to provide smoother, visible progress in the UI
        self._simulate_work(10.0, "Analyzing business data", 100)
        self._generate_intelligent_plays()
        
        # Explicit finish marker for stub agents
        self._log_execution("FINISH: Subject area analysis", "INFO")
    
    def _generate_intelligent_plays(self):
        """Generate intelligent plays using the mock intelligence engine"""
        try:
            from agents.mock_intelligence import generate_plays_for_area
            
            # Generate intelligent plays for this subject area
            intelligent_plays = generate_plays_for_area(self.subject_area, count=self.max_plays_per_area)
            
            for play in intelligent_plays:
                self._add_play(play)
                
            self._log_execution(f"Generated {len(intelligent_plays)} intelligent plays", "INFO")
            
        except ImportError:
            # Fallback to basic mock plays if mock intelligence is not available
            self._log_execution("Mock intelligence not available, using fallback", "WARNING")
            self._generate_fallback_plays()
    
    def _generate_fallback_plays(self):
        """Generate fallback mock plays if mock intelligence is not available"""
        from models.play_models import Play, PlayCategory
        
        fallback_plays = [
            Play(
                title=f"{self.subject_area.value.title()} Optimization Initiative",
                description=f"Strategic optimization of {self.subject_area.value} operations",
                category=PlayCategory.PERFORMANCE_OPTIMIZATION,
                subject_area=self.subject_area,
                impact_score=7.5,
                effort_score=6.0,
                roi_score=7.8,
                risk_score=3.5,
                estimated_cost=1000000.0,
                estimated_duration_months=12,
                tags=[self.subject_area.value, "optimization", "strategic"]
            ),
            Play(
                title=f"{self.subject_area.value.title()} Security Enhancement",
                description=f"Comprehensive security improvements for {self.subject_area.value}",
                category=PlayCategory.SECURITY_ENHANCEMENT,
                subject_area=self.subject_area,
                impact_score=8.2,
                effort_score=7.5,
                roi_score=8.5,
                risk_score=2.8,
                estimated_cost=1500000.0,
                estimated_duration_months=15,
                tags=[self.subject_area.value, "security", "compliance"]
            )
        ]
        
        for play in fallback_plays:
            self._add_play(play)
    
    def analyze_subject_area(self) -> List[Play]:
        """Analyze the subject area and generate plays"""
        if self.state.status != AgentStatus.IDLE:
            raise RuntimeError("Agent is not in idle state")
        
        # Start execution
        self.start_execution(f"Analyzing {self.subject_area.value} area")
        
        # Wait for completion
        self.wait_for_completion()
        
        # Return results
        return self.get_plays()
    
    def get_analysis_summary(self) -> Dict[str, Any]:
        """Get summary of analysis results"""
        plays = self.get_plays()
        
        if not plays:
            return {
                "status": "no_plays_generated",
                "message": "No plays were generated during analysis"
            }
        
        # Calculate summary statistics
        total_cost = sum(play.estimated_cost for play in plays)
        avg_priority = sum(play.priority_level for play in plays) / len(plays)
        priority_distribution = {}
        
        for play in plays:
            priority = play.get_priority_label()
            priority_distribution[priority] = priority_distribution.get(priority, 0) + 1
        
        return {
            "status": "analysis_complete",
            "plays_generated": len(plays),
            "total_investment": total_cost,
            "average_priority": avg_priority,
            "priority_distribution": priority_distribution,
            "subject_area": self.subject_area.value,
            "analysis_depth": self.analysis_depth
        }


class AgentFactory:
    """Factory for creating specialized agents"""
    
    @staticmethod
    def create_subject_area_agent(subject_area: SubjectArea) -> SubjectAreaAgent:
        """Create a subject area agent"""
        if subject_area == SubjectArea.NETWORK:
            return NetworkAgent()
        return SubjectAreaAgent(subject_area)
    
    @staticmethod
    def create_all_subject_area_agents() -> Dict[str, SubjectAreaAgent]:
        """Create agents for all subject areas"""
        agents = {}
        for area in SubjectArea:
            agents[area.value] = AgentFactory.create_subject_area_agent(area)
        return agents
