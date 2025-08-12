"""
Playbook Prioritizer Agent - Core Data Models

This module defines the core data structures for the multi-agent system:
- Play: Individual business initiatives with scoring
- Portfolio: Collection of selected plays with optimization
- Agent: Base agent class with state management
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from enum import Enum
from datetime import datetime
import uuid


class PlayCategory(str, Enum):
    """Business initiative categories"""
    PERFORMANCE_OPTIMIZATION = "performance_optimization"
    SECURITY_ENHANCEMENT = "security_enhancement"
    CUSTOMER_RETENTION = "customer_retention"
    REVENUE_GROWTH = "revenue_growth"
    OPERATIONAL_EFFICIENCY = "operational_efficiency"
    INFRASTRUCTURE_UPGRADE = "infrastructure_upgrade"
    COMPLIANCE_IMPROVEMENT = "compliance_improvement"
    INNOVATION_INITIATIVE = "innovation_initiative"


class SubjectArea(str, Enum):
    """Business subject areas for analysis"""
    NETWORK = "network"
    NETWORK_QOE = "network_qoe"
    CUSTOMER = "customer"
    REVENUE = "revenue"
    USAGE = "usage"
    OPERATIONS = "operations"


class AgentStatus(str, Enum):
    """Agent execution status"""
    IDLE = "idle"
    ANALYZING = "analyzing"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"


@dataclass
class Play:
    """Individual business initiative with scoring"""
    
    # Core identification
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = ""
    description: str = ""
    category: PlayCategory = field(default=PlayCategory.PERFORMANCE_OPTIMIZATION)
    subject_area: SubjectArea = field(default=SubjectArea.NETWORK)
    
    # Scoring metrics (0-10 scale)
    impact_score: float = 0.0
    effort_score: float = 0.0
    roi_score: float = 0.0
    risk_score: float = 0.0
    
    # Portfolio optimization scores
    score: float = 0.0
    rank: int = 0
    
    # Business context
    estimated_cost: float = 0.0
    estimated_duration_months: int = 0
    priority_level: int = 0
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    tags: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Validate and compute derived fields"""
        # Ensure scores are within valid range
        self.impact_score = max(0.0, min(10.0, self.impact_score))
        self.effort_score = max(0.0, min(10.0, self.effort_score))
        self.roi_score = max(0.0, min(10.0, self.roi_score))
        self.risk_score = max(0.0, min(10.0, self.risk_score))
        
        # Compute priority level based on scoring
        self.priority_level = self._calculate_priority()
    
    def _calculate_priority(self) -> int:
        """Calculate priority level (1-5) based on scoring"""
        # High impact, low effort, high ROI, low risk = high priority
        priority_score = (
            (self.impact_score * 0.3) +
            ((10 - self.effort_score) * 0.2) +
            (self.roi_score * 0.3) +
            ((10 - self.risk_score) * 0.2)
        )
        
        if priority_score >= 8.0:
            return 1  # Critical
        elif priority_score >= 6.5:
            return 2  # High
        elif priority_score >= 5.0:
            return 3  # Medium
        elif priority_score >= 3.5:
            return 4  # Low
        else:
            return 5  # Minimal
    
    def get_priority_label(self) -> str:
        """Get human-readable priority label"""
        labels = {
            1: "Critical",
            2: "High", 
            3: "Medium",
            4: "Low",
            5: "Minimal"
        }
        return labels.get(self.priority_level, "Unknown")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "category": self.category.value,
            "subject_area": self.subject_area.value,
            "impact_score": self.impact_score,
            "effort_score": self.effort_score,
            "roi_score": self.roi_score,
            "risk_score": self.risk_score,
            "score": self.score,
            "rank": self.rank,
            "estimated_cost": self.estimated_cost,
            "estimated_duration_months": self.estimated_duration_months,
            "priority_level": self.priority_level,
            "priority_label": self.get_priority_label(),
            "created_at": self.created_at.isoformat(),
            "tags": self.tags
        }


@dataclass
class Portfolio:
    """Collection of selected plays with optimization metrics"""
    
    # Core data
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = "Optimized Portfolio"
    description: str = "AI-optimized portfolio of business initiatives"
    
    # Plays
    selected_plays: List[Play] = field(default_factory=list)
    rejected_plays: List[Play] = field(default_factory=list)
    
    # Portfolio metrics
    total_investment: float = 0.0
    total_roi: float = 0.0
    average_priority: float = 0.0
    risk_distribution: Dict[str, int] = field(default_factory=dict)
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    optimization_parameters: Dict[str, Any] = field(default_factory=dict)
    executive_summary: str = ""
    
    def __post_init__(self):
        """Calculate portfolio metrics"""
        self._calculate_portfolio_metrics()
        if not self.executive_summary:
            self.executive_summary = "AI-optimized portfolio summary will be generated during optimization."
    
    def _calculate_portfolio_metrics(self):
        """Calculate portfolio-level metrics"""
        if not self.selected_plays:
            return
        
        # Total investment
        self.total_investment = sum(play.estimated_cost for play in self.selected_plays)
        
        # Total ROI (weighted by cost)
        total_cost = sum(play.estimated_cost for play in self.selected_plays)
        if total_cost > 0:
            self.total_roi = sum(
                (play.roi_score * play.estimated_cost) for play in self.selected_plays
            ) / total_cost
        else:
            self.total_roi = 0.0
        
        # Average priority
        self.average_priority = sum(play.priority_level for play in self.selected_plays) / len(self.selected_plays)
        
        # Risk distribution
        self.risk_distribution = {}
        for play in self.selected_plays:
            risk_level = self._get_risk_level(play.risk_score)
            self.risk_distribution[risk_level] = self.risk_distribution.get(risk_level, 0) + 1

    def calculate_metrics(self):
        """Public method to (re)calculate portfolio metrics.

        Exposes metric recomputation for callers that need to update metrics after
        mutating the underlying plays. Delegates to the internal implementation to
        preserve a single source of truth.
        """
        self._calculate_portfolio_metrics()
    
    def _get_risk_level(self, risk_score: float) -> str:
        """Convert risk score to risk level"""
        if risk_score <= 3.0:
            return "Low"
        elif risk_score <= 6.0:
            return "Medium"
        else:
            return "High"
    
    def add_play(self, play: Play, selected: bool = True):
        """Add a play to the portfolio"""
        if selected:
            self.selected_plays.append(play)
        else:
            self.rejected_plays.append(play)
        self._calculate_portfolio_metrics()
    
    def remove_play(self, play_id: str, selected: bool = True):
        """Remove a play from the portfolio"""
        if selected:
            self.selected_plays = [p for p in self.selected_plays if p.id != play_id]
        else:
            self.rejected_plays = [p for p in self.rejected_plays if p.id != play_id]
        self._calculate_portfolio_metrics()
    
    def get_plays_by_priority(self, priority_level: int) -> List[Play]:
        """Get plays by priority level"""
        return [play for play in self.selected_plays if play.priority_level == priority_level]
    
    def get_plays_by_category(self, category: PlayCategory) -> List[Play]:
        """Get plays by category"""
        return [play for play in self.selected_plays if play.category == category]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "selected_plays": [play.to_dict() for play in self.selected_plays],
            "rejected_plays": [play.to_dict() for play in self.rejected_plays],
            "total_investment": self.total_investment,
            "total_roi": self.total_roi,
            "average_priority": self.average_priority,
            "risk_distribution": self.risk_distribution,
            "created_at": self.created_at.isoformat(),
            "optimization_parameters": self.optimization_parameters,
            "executive_summary": self.executive_summary
        }


@dataclass
class AgentState:
    """Agent execution state and progress"""
    
    status: AgentStatus = field(default=AgentStatus.IDLE)
    progress: float = 0.0  # 0.0 to 1.0
    current_task: Optional[str] = None
    start_time: Optional[datetime] = None
    completion_time: Optional[datetime] = None
    error_message: Optional[str] = None
    
    def start_execution(self, task: str):
        """Start agent execution"""
        self.status = AgentStatus.ANALYZING
        self.progress = 0.0
        self.current_task = task
        self.start_time = datetime.now()
        self.error_message = None
    
    def update_progress(self, progress: float, task: str = None):
        """Update execution progress"""
        self.progress = max(0.0, min(1.0, progress))
        if task:
            self.current_task = task
    
    def complete_execution(self):
        """Mark execution as complete"""
        self.status = AgentStatus.COMPLETED
        self.progress = 1.0
        self.completion_time = datetime.now()
        self.current_task = None
    
    def fail_execution(self, error: str):
        """Mark execution as failed"""
        self.status = AgentStatus.FAILED
        self.error_message = error
        self.completion_time = datetime.now()
    
    def reset(self):
        """Reset agent state"""
        self.status = AgentStatus.IDLE
        self.progress = 0.0
        self.current_task = None
        self.start_time = None
        self.completion_time = None
        self.error_message = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "status": self.status.value,
            "progress": self.progress,
            "current_task": self.current_task,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "completion_time": self.completion_time.isoformat() if self.completion_time else None,
            "error_message": self.error_message
        }


class WorkflowPhase(str, Enum):
    """Workflow execution phases"""
    INITIALIZATION = "initialization"
    AGENT_ANALYSIS = "agent_analysis"
    PORTFOLIO_OPTIMIZATION = "portfolio_optimization"
    RESULTS_PRESENTATION = "results_presentation"
    COMPLETED = "completed"


@dataclass
class WorkflowStatus:
    """Overall workflow status and progress"""
    
    current_phase: WorkflowPhase = field(default=WorkflowPhase.INITIALIZATION)
    phase_progress: float = 0.0
    total_progress: float = 0.0
    start_time: datetime = field(default_factory=datetime.now)
    estimated_completion: Optional[datetime] = None
    phase_details: Dict[str, Any] = field(default_factory=dict)
    
    def advance_phase(self, new_phase: WorkflowPhase):
        """Advance to next workflow phase"""
        self.current_phase = new_phase
        self.phase_progress = 0.0
    
    def update_phase_progress(self, progress: float):
        """Update current phase progress"""
        self.phase_progress = max(0.0, min(1.0, progress))
    
    def update_total_progress(self, progress: float):
        """Update overall workflow progress"""
        self.total_progress = max(0.0, min(1.0, progress))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "current_phase": self.current_phase.value,
            "phase_progress": self.phase_progress,
            "total_progress": self.total_progress,
            "start_time": self.start_time.isoformat(),
            "estimated_completion": self.estimated_completion.isoformat() if self.estimated_completion else None,
            "phase_details": self.phase_details
        }
