"""
Agent Orchestrator Engine

This module provides the central orchestration system for coordinating multiple agents,
managing workflows, and optimizing portfolio selection across all subject areas.
"""

import time
import threading
import logging
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum

from models.play_models import (
    Play, 
    Portfolio, 
    SubjectArea, 
    AgentStatus,
    WorkflowPhase,
    WorkflowStatus
)
from agents.base_agent import BaseAgent, SubjectAreaAgent, AgentFactory
from agents.integration_layer import get_integration_manager
from agents.backup_demo_mode import get_backup_demo
from logging_config import get_logger


class OrchestrationStatus(Enum):
    """Status of the orchestration process"""
    IDLE = "idle"
    INITIALIZING = "initializing"
    RUNNING = "running"
    OPTIMIZING = "optimizing"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"
    FALLBACK_MODE = "fallback_mode"


@dataclass
class OrchestrationConfig:
    """Configuration for the orchestration process"""
    max_concurrent_agents: int = 5
    agent_timeout_seconds: int = 30
    min_agent_run_seconds: float = 8.0
    optimization_iterations: int = 3
    portfolio_size_target: int = 15
    min_roi_threshold: float = 7.0
    max_risk_threshold: float = 6.0
    enable_parallel_execution: bool = True
    progress_update_interval: float = 0.5
    enable_circuit_breaker: bool = True
    max_failures_before_fallback: int = 3
    fallback_timeout_seconds: int = 60


@dataclass
class OrchestrationMetrics:
    """Metrics and statistics for the orchestration process"""
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    total_agents: int = 0
    successful_agents: int = 0
    failed_agents: int = 0
    total_plays_generated: int = 0
    total_execution_time: float = 0.0
    average_agent_execution_time: float = 0.0
    portfolio_optimization_time: float = 0.0
    final_portfolio_size: int = 0
    final_portfolio_roi: float = 0.0
    final_portfolio_risk: float = 0.0
    integration_health: str = "unknown"
    fallback_mode_activated: bool = False
    circuit_breaker_trips: int = 0


class CircuitBreaker:
    """Circuit breaker pattern for handling agent failures"""
    
    def __init__(self, failure_threshold: int = 3, timeout_seconds: int = 60):
        self.failure_threshold = failure_threshold
        self.timeout_seconds = timeout_seconds
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection"""
        if self.state == "OPEN":
            if self._should_attempt_reset():
                self.state = "HALF_OPEN"
            else:
                raise Exception("Circuit breaker is OPEN - too many failures")
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise e
    
    def _on_success(self):
        """Handle successful execution"""
        self.failure_count = 0
        self.state = "CLOSED"
    
    def _on_failure(self):
        """Handle execution failure"""
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"
    
    def _should_attempt_reset(self) -> bool:
        """Check if circuit breaker should attempt reset"""
        if not self.last_failure_time:
            return False
        
        time_since_failure = (datetime.now() - self.last_failure_time).total_seconds()
        return time_since_failure >= self.timeout_seconds


class AgentOrchestrator:
    """Main orchestrator for coordinating multiple agents and optimizing portfolios"""
    
    def __init__(self, config: OrchestrationConfig = None):
        """Initialize the agent orchestrator"""
        self.config = config or OrchestrationConfig()
        self.status = OrchestrationStatus.IDLE
        self.metrics = OrchestrationMetrics()
        self.workflow_status = WorkflowStatus()
        # Dedicated orchestrator activity logger
        self._logger = get_logger('orchestrator', level='INFO', log_file='agent_activity.log')
        
        # Agent management
        self.agents: Dict[str, SubjectAreaAgent] = {}
        self.agent_results: Dict[str, List[Play]] = {}
        self.agent_status: Dict[str, AgentStatus] = {}
        self.agent_progress: Dict[str, float] = {}
        # Live progress snapshot for UI polling (thread-safe via _lock)
        self._last_progress: float = 0.0
        self._last_message: str = ""
        
        # Portfolio management
        self.initial_portfolio: Optional[Portfolio] = None
        self.optimized_portfolio: Optional[Portfolio] = None
        
        # Execution control
        self._execution_thread: Optional[threading.Thread] = None
        self._stop_execution = threading.Event()
        self._lock = threading.Lock()
        
        # Progress callbacks
        self._progress_callbacks: List[Callable] = []
        self._status_callbacks: List[Callable] = []
        
        # Integration layer
        self.integration_manager = get_integration_manager()
        
        # Circuit breaker
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=self.config.max_failures_before_fallback,
            timeout_seconds=self.config.fallback_timeout_seconds
        )
        
        # Backup demo mode
        self.backup_demo = get_backup_demo()
        
        # Initialize agents
        self._initialize_agents()
        
        # Check integration health
        self._check_integration_health()
    
    def _check_integration_health(self):
        """Check the health of integration systems"""
        try:
            if not self.integration_manager:
                self.metrics.integration_health = "unknown"
                return
            
            health_status = self.integration_manager.check_system_health()
            overall_health = health_status.get('overall_health', 'unknown')
            
            # Only mark as unhealthy if there are critical failures
            if overall_health == 'critical':
                self.metrics.integration_health = "unhealthy"
                logging.warning("Integration system marked as unhealthy due to critical failures")
            elif overall_health in ['healthy', 'degraded']:
                self.metrics.integration_health = "healthy"
                logging.info("Integration system is healthy or degraded but functional")
            else:
                # For 'unknown' or other statuses, assume it's functional
                self.metrics.integration_health = "healthy"
                logging.info("Integration system status unknown, assuming functional")
                
        except Exception as e:
            logging.warning(f"Integration health check failed - system may be in fallback mode: {e}")
            # Don't mark as unhealthy just because health check failed
            self.metrics.integration_health = "healthy"
    
    def _initialize_agents(self):
        """Initialize all subject area agents"""
        try:
            logging.info("🔧 Starting agent initialization...")
            agent_factory = AgentFactory()
            
            # Create agents for all subject areas
            for area in SubjectArea:
                try:
                    logging.info(f"🔧 Creating agent for area: {area.value}")
                    agent = agent_factory.create_subject_area_agent(area)
                    if agent:
                        self.agents[area.value] = agent
                        self.agent_status[area.value] = AgentStatus.IDLE
                        self.agent_progress[area.value] = 0.0
                        self.metrics.total_agents += 1
                        logging.info(f"✅ Created agent for {area.value}")
                    else:
                        logging.error(f"❌ Failed to create agent for {area.value}")
                except Exception as e:
                    logging.error(f"❌ Error creating agent for {area.value}: {str(e)}")
                    # Continue with other agents
            
            # Ensure we have at least some agents
            if not self.agents:
                logging.warning("⚠️ No agents were created, using fallback mode")
                self._activate_fallback_mode()
                return False
            
            logging.info(f"🔧 Agent initialization completed. Created {len(self.agents)} agents: {list(self.agents.keys())}")
            return True
            
        except Exception as e:
            logging.error(f"❌ Critical error during agent initialization: {str(e)}")
            self._activate_fallback_mode()
            return False
    
    def _activate_fallback_mode(self):
        """Activate fallback mode when normal initialization fails"""
        try:
            self.status = OrchestrationStatus.FALLBACK_MODE
            self.metrics.fallback_mode_activated = True
            self._notify_status("Fallback mode activated - using backup demo data")
            logging.info("Fallback mode activated due to initialization failure")
            
        except Exception as e:
            logging.error(f"Error activating fallback mode: {e}")
    
    def start_orchestration(self, callback: Callable = None) -> bool:
        """Start the orchestration process"""
        try:
            with self._lock:
                if self.status in [OrchestrationStatus.RUNNING, OrchestrationStatus.OPTIMIZING]:
                    logging.warning("Orchestration already running")
                    return False
                
                # Check if we should use fallback mode - only if explicitly unhealthy
                if (self.metrics.integration_health == "unhealthy" and 
                    self.config.enable_circuit_breaker and
                    self.metrics.fallback_mode_activated):
                    logging.warning("Integration health is unhealthy, using fallback mode")
                    self._activate_fallback_mode()
                    return self._start_fallback_orchestration(callback)
                
                self.status = OrchestrationStatus.INITIALIZING
                self.metrics.start_time = datetime.now()
                self.workflow_status.current_phase = WorkflowPhase.INITIALIZATION
                self.workflow_status.total_progress = 0.0
                
                if callback:
                    self.add_progress_callback(callback)
                
                # Start execution in background thread
                self._execution_thread = threading.Thread(target=self._execute_orchestration)
                self._execution_thread.daemon = True
                self._execution_thread.start()
                
                logging.info("✅ Orchestration started successfully")
                return True
                
        except Exception as e:
            logging.error(f"Error starting orchestration: {e}")
            self.status = OrchestrationStatus.FAILED
            return False
    
    def _start_fallback_orchestration(self, callback: Callable = None) -> bool:
        """Start orchestration in fallback mode"""
        try:
            self._notify_status("Starting orchestration in fallback mode")
            
            # Run backup demo
            demo_results = self.backup_demo.run_backup_demo(duration_seconds=30)
            
            # Create portfolio from backup data
            self.optimized_portfolio = Portfolio(
                selected_plays=[],
                name="Backup Demo Portfolio",
                description="Portfolio generated from backup demo data"
            )
            
            self.status = OrchestrationStatus.COMPLETED
            self.metrics.end_time = datetime.now()
            self.workflow_status.current_phase = WorkflowPhase.COMPLETED
            self.workflow_status.total_progress = 1.0
            
            if callback:
                callback(1.0, "Fallback orchestration completed")
            
            return True
            
        except Exception as e:
            logging.error(f"Error in fallback orchestration: {e}")
            self.status = OrchestrationStatus.FAILED
            return False
    
    def _execute_orchestration(self):
        """Execute the main orchestration workflow"""
        try:
            self._notify_progress(0.05, "Starting orchestration...")
            self._notify_status("Initializing orchestration system")
            self.status = OrchestrationStatus.RUNNING
            # Move to agent analysis phase
            self.workflow_status.advance_phase(WorkflowPhase.AGENT_ANALYSIS)
            
            # Phase 1: Execute all agents
            self._notify_progress(0.1, "Initializing agents...")
            self._notify_status("Creating and initializing specialized agents")
            
            logging.info("🔧 Starting agent execution phase...")
            try:
                self._logger.info("phase=agent_execution status=starting msg=Starting agent execution phase")
            except Exception:
                pass
            if not self._execute_all_agents():
                logging.error("❌ Agent execution failed")
                try:
                    self._logger.error("phase=agent_execution status=failed msg=Agent execution failed")
                except Exception:
                    pass
                raise Exception("Agent execution failed")
            
            logging.info("✅ Agent execution completed successfully")
            try:
                self._logger.info("phase=agent_execution status=completed msg=Agent execution completed successfully")
            except Exception:
                pass
            self._notify_progress(0.6, "Agent execution completed, optimizing portfolio...")
            self._notify_status("Portfolio optimization in progress")
            
            # Phase 2: Portfolio optimization
            self.workflow_status.advance_phase(WorkflowPhase.PORTFOLIO_OPTIMIZATION)
            if not self._optimize_portfolio():
                logging.error("❌ Portfolio optimization failed")
                try:
                    self._logger.error("phase=portfolio_optimization status=failed msg=Portfolio optimization failed")
                except Exception:
                    pass
                raise Exception("Portfolio optimization failed")
            
            logging.info("✅ Portfolio optimization completed successfully")
            try:
                self._logger.info("phase=portfolio_optimization status=completed msg=Portfolio optimization completed successfully")
            except Exception:
                pass
            self._notify_progress(0.9, "Portfolio optimization completed, finalizing...")
            self._notify_status("Finalizing orchestration results")
            
            # Phase 3: Finalization
            self._finalize_orchestration()
            
            logging.info("✅ Orchestration completed successfully")
            self._notify_progress(1.0, "Orchestration completed successfully!")
            self._notify_status("Analysis complete - results ready")
            self.status = OrchestrationStatus.COMPLETED
            self.workflow_status.advance_phase(WorkflowPhase.COMPLETED)
            try:
                self._logger.info("phase=completed status=completed msg=Orchestration completed successfully")
            except Exception:
                pass
            
        except Exception as e:
            logging.error(f"❌ Orchestration failed: {str(e)}")
            self._notify_status(f"Orchestration failed: {str(e)}")
            self.status = OrchestrationStatus.FAILED
            raise
    
    def _execute_all_agents(self) -> bool:
        """Execute all agents and collect results"""
        try:
            logging.info(f"🔧 Executing {len(self.agents)} agents...")
            
            if not self.agents:
                logging.error("❌ No agents available for execution")
                return False
            
            # Execute agents based on configuration
            if self.config.enable_parallel_execution and len(self.agents) > 1:
                logging.info("🔧 Executing agents in parallel mode")
                return self._execute_agents_parallel()
            else:
                logging.info("🔧 Executing agents sequentially")
                return self._execute_agents_sequential()
                
        except Exception as e:
            logging.error(f"❌ Error during agent execution: {str(e)}")
            return False
    
    def _execute_agents_parallel(self) -> bool:
        """Execute all agents in parallel with error handling"""
        try:
            agent_threads = []
            agent_results = {}
            agent_status_updates = {}
            
            # Create a thread-safe dictionary for results
            results_lock = threading.Lock()
            total_agents = len(self.agents)
            start_time = time.time()
            timeout_seconds = self.config.agent_timeout_seconds
            
            def execute_agent(agent_name, agent_instance):
                try:
                    logging.info(f"🔧 Starting parallel execution for {agent_name}")
                    
                    # Execute the agent
                    plays = agent_instance.analyze_subject_area()
                    
                    # Store results thread-safely
                    with results_lock:
                        agent_results[agent_name] = plays
                        agent_status_updates[agent_name] = AgentStatus.COMPLETED
                        self.metrics.successful_agents += 1
                        self.metrics.total_plays_generated += len(plays)
                    
                    logging.info(f"✅ {agent_name} completed successfully with {len(plays)} plays")
                    
                except Exception as e:
                    logging.error(f"❌ Agent {agent_name} failed: {e}")
                    with results_lock:
                        agent_status_updates[agent_name] = AgentStatus.FAILED
                        self.metrics.failed_agents += 1
                        agent_results[agent_name] = []
            
            # Start all agents
            for area_name, agent in self.agents.items():
                # Mark agent as analyzing for live status updates
                self.agent_status[area_name] = AgentStatus.ANALYZING
                thread = threading.Thread(
                    target=execute_agent,
                    args=(area_name, agent),
                    name=f"AgentThread-{area_name}"
                )
                thread.daemon = True
                thread.start()
                agent_threads.append(thread)
                logging.info(f"🔧 Started thread for {area_name}")
            
            # Poll for completion with periodic progress updates (0.10 → 0.60 range)
            while True:
                alive_threads = [t for t in agent_threads if t.is_alive()]
                completed_count = total_agents - len(alive_threads)
                # Map completed agents to progress between 0.1 and 0.6
                progress = 0.1 + 0.5 * (completed_count / max(1, total_agents))
                self._notify_progress(progress, f"Agent execution in progress: {completed_count}/{total_agents} completed")
                
                if not alive_threads:
                    break
                if time.time() - start_time > timeout_seconds:
                    logging.warning("Parallel agent execution timeout reached")
                    break
                time.sleep(0.2)
            
            # Check for any remaining alive threads
            alive_threads = [t for t in agent_threads if t.is_alive()]
            if alive_threads:
                logging.warning(f"Some agents timed out: {[t.name for t in alive_threads]}")
            
            # Update agent status from parallel execution
            with results_lock:
                for area_name, status in agent_status_updates.items():
                    self.agent_status[area_name] = status
            
            # Store results
            self.agent_results = agent_results
            
            # Check if we have enough successful agents
            successful_count = sum(1 for status in self.agent_status.values() 
                                 if status == AgentStatus.COMPLETED)
            
            logging.info(f"🔧 Parallel execution completed. Success: {successful_count}/{len(self.agents)}")
            
            if successful_count < len(self.agents) * 0.6:  # At least 60% success rate
                raise Exception(f"Too many agent failures: {successful_count}/{len(self.agents)}")
            
            return True
            
        except Exception as e:
            logging.error(f"❌ Parallel agent execution failed: {e}")
            return False
    
    def _execute_agents_sequential(self) -> bool:
        """Execute agents sequentially with error handling"""
        try:
            total_agents = len(self.agents)
            logging.info(f"🔧 Executing {total_agents} agents sequentially")
            
            for i, (area_name, agent) in enumerate(self.agents.items()):
                try:
                    agent_progress_start = 0.1 + (0.4 * i / total_agents)
                    agent_progress_end = 0.1 + (0.4 * (i + 1) / total_agents)
                    
                    logging.info(f"🔧 Starting agent {i+1}/{total_agents}: {area_name}")
                    self._notify_progress(agent_progress_start, f"Starting {area_name} agent...")
                    self._notify_status(f"Executing {area_name} agent...")
                    # Reflect analyzing status in public status map
                    self.agent_status[area_name] = AgentStatus.ANALYZING
                    self.agent_progress[area_name] = 0.0
                    
                    # Execute the agent with active progress polling
                    # Start execution without blocking
                    agent.start_execution(f"Analyzing {area_name} area")
                    start_time = time.time()
                    timeout_seconds = self.config.agent_timeout_seconds
                    last_notify_time = 0.0
                    last_seen_progress = 0.0
                    last_progress_ts = time.time()
                    # Enforce a minimum visible run time for stub/demo UX
                    min_run_seconds = getattr(self.config, 'min_agent_run_seconds', 0.0)
                    while True:
                        # Periodically poll agent progress and surface to UI (use locked API)
                        status_dict = agent.get_status()
                        current_progress = float(status_dict.get('state', {}).get('progress', 0.0) or 0.0)
                        # Clamp
                        current_progress = max(0.0, min(1.0, current_progress))
                        now = time.time()
                        # Synthetic heartbeat if underlying progress appears stuck briefly (demo UX safeguard)
                        if current_progress <= last_seen_progress and (now - last_progress_ts) > max(0.6, self.config.progress_update_interval * 2):
                            # Advance a tiny synthetic step but do not exceed 0.99 to leave room for real completion
                            current_progress = min(0.99, last_seen_progress + 0.01)
                        else:
                            if current_progress > last_seen_progress:
                                last_seen_progress = current_progress
                                last_progress_ts = now
                        self.agent_progress[area_name] = current_progress
                        # Map to orchestrator overall progress range for this agent
                        mapped = agent_progress_start + (agent_progress_end - agent_progress_start) * current_progress
                        if now - last_notify_time >= self.config.progress_update_interval:
                            self._notify_progress(mapped, f"{area_name} agent {int(current_progress*100)}%")
                            # Provide a status heartbeat as well so UIs relying on messages stay lively
                            self._notify_status(f"{area_name} agent analyzing... {int(current_progress*100)}%")
                            last_notify_time = now
                        
                        # Wait a short interval; break when complete or timeout
                        if agent.wait_for_completion(timeout=0.1):
                            # Respect minimum run time: if completed too fast, idle-sleep while emitting heartbeats
                            if (time.time() - start_time) < min_run_seconds:
                                while (time.time() - start_time) < min_run_seconds:
                                    now = time.time()
                                    if now - last_notify_time >= self.config.progress_update_interval:
                                        # Keep mapped progress near end but not 100%
                                        heartbeat_progress = min(0.99, last_seen_progress + 0.01)
                                        self.agent_progress[area_name] = heartbeat_progress
                                        mapped = agent_progress_start + (agent_progress_end - agent_progress_start) * heartbeat_progress
                                        self._notify_progress(mapped, f"\n{area_name} agent {int(heartbeat_progress*100)}%")
                                        self._notify_status(f"{area_name} agent finalizing... {int(heartbeat_progress*100)}%")
                                        last_notify_time = now
                                    time.sleep(0.1)
                            break
                        if now - start_time > timeout_seconds:
                            raise TimeoutError(f"{area_name} agent execution timed out after {timeout_seconds}s")
                        # Small sleep to avoid tight loop
                        time.sleep(0.05)
                    
                    # Collect results
                    plays = agent.get_plays()
                    
                    # Update progress
                    self._notify_progress(agent_progress_end, f"{area_name} agent completed")
                    self._notify_status(f"{area_name} agent completed - {len(plays)} plays generated")
                    
                    # Store results
                    self.agent_results[area_name] = plays
                    self.agent_status[area_name] = AgentStatus.COMPLETED
                    self.agent_progress[area_name] = 1.0
                    self.metrics.successful_agents += 1
                    self.metrics.total_plays_generated += len(plays)
                    
                    logging.info(f"✅ {area_name} agent completed successfully with {len(plays)} plays")
                    
                except Exception as e:
                    logging.error(f"❌ Error executing {area_name} agent: {str(e)}")
                    self.agent_status[area_name] = AgentStatus.FAILED
                    self.agent_progress[area_name] = 0.0
                    self.metrics.failed_agents += 1
                    # Continue with other agents
                    
            logging.info(f"✅ Sequential agent execution completed. Success: {self.metrics.successful_agents}, Failed: {self.metrics.failed_agents}")
            return self.metrics.successful_agents > 0
            
        except Exception as e:
            logging.error(f"❌ Critical error in sequential execution: {str(e)}")
            return False
    
    def _create_initial_portfolio(self) -> bool:
        """Create initial portfolio from agent results"""
        try:
            all_plays = []
            
            # Collect all plays from successful agents
            for area_name, plays in self.agent_results.items():
                if self.agent_status[area_name] == AgentStatus.COMPLETED:
                    all_plays.extend(plays)
            
            if not all_plays:
                raise Exception("No plays generated by agents")
            
            # Create portfolio
            self.initial_portfolio = Portfolio(
                selected_plays=all_plays,
                name="Initial Portfolio",
                description="Portfolio created from all agent results"
            )
            
            # Calculate initial metrics
            self.initial_portfolio.calculate_metrics()
            
            logging.info(f"✅ Created initial portfolio with {len(all_plays)} plays")
            return True
            
        except Exception as e:
            logging.error(f"Error creating initial portfolio: {e}")
            return False
    
    def _optimize_portfolio(self) -> bool:
        """Optimize the portfolio using advanced algorithms"""
        try:
            start_time = time.time()
            
            if not self.agent_results:
                raise Exception("No agent results to optimize")
            
            # Use portfolio agent for optimization
            from agents.portfolio_agent import PortfolioAgent
            
            portfolio_agent = PortfolioAgent()
            
            # Convert agent results to the format expected by PortfolioAgent
            plays_by_area = {}
            for area, plays in self.agent_results.items():
                if plays:  # Only include areas with plays
                    plays_by_area[area] = plays
            
            if not plays_by_area:
                raise Exception("No plays available for portfolio optimization")
            
            self.optimized_portfolio = portfolio_agent.process_plays(plays_by_area)
            
            # Update metrics
            self.metrics.portfolio_optimization_time = time.time() - start_time
            self.metrics.final_portfolio_size = len(self.optimized_portfolio.selected_plays)
            self.metrics.final_portfolio_roi = self.optimized_portfolio.total_roi
            self.metrics.final_portfolio_risk = self.optimized_portfolio.average_priority  # Use priority as risk proxy
            
            logging.info(f"✅ Portfolio optimization completed in {self.metrics.portfolio_optimization_time:.2f}s")
            logging.info(f"✅ Final portfolio: {self.metrics.final_portfolio_size} plays, ROI: {self.metrics.final_portfolio_roi:.2f}")
            return True
            
        except Exception as e:
            logging.error(f"Error optimizing portfolio: {e}")
            # Fallback to basic optimization
            return self._basic_portfolio_optimization()
    
    def _basic_portfolio_optimization(self) -> bool:
        """Basic portfolio optimization as fallback"""
        try:
            if not self.initial_portfolio:
                return False
            
            # Simple optimization: sort by ROI and take top plays
            sorted_plays = sorted(
                self.initial_portfolio.selected_plays,
                key=lambda p: p.impact_score / p.effort_score,
                reverse=True
            )
            
            # Take top plays within effort limit
            selected_plays = []
            total_effort = 0
            
            for play in sorted_plays:
                if total_effort + play.effort_score <= self.config.portfolio_size_target:
                    selected_plays.append(play)
                    total_effort += play.effort_score
                else:
                    break
            
            self.optimized_portfolio = Portfolio(
                selected_plays=selected_plays,
                name="Basic Optimized Portfolio",
                description="Portfolio optimized using basic scoring algorithm"
            )
            
            self.optimized_portfolio.calculate_metrics()
            
            logging.info(f"✅ Basic portfolio optimization completed with {len(selected_plays)} plays")
            return True
            
        except Exception as e:
            logging.error(f"Basic portfolio optimization failed: {e}")
            return False
    
    def _finalize_orchestration(self):
        """Finalize the orchestration process"""
        try:
            self.metrics.end_time = datetime.now()
            
            if self.metrics.start_time:
                self.metrics.total_execution_time = (
                    self.metrics.end_time - self.metrics.start_time
                ).total_seconds()
                
                if self.metrics.successful_agents > 0:
                    self.metrics.average_agent_execution_time = (
                        self.metrics.total_execution_time / self.metrics.successful_agents
                    )
            
            self.status = OrchestrationStatus.COMPLETED
            self.workflow_status.current_phase = WorkflowPhase.COMPLETED
            self.workflow_status.overall_status = "completed"
            
            logging.info("✅ Orchestration finalized successfully")
            
        except Exception as e:
            logging.error(f"Error finalizing orchestration: {e}")
    
    def stop_orchestration(self) -> bool:
        """Stop the orchestration process"""
        try:
            with self._lock:
                if self.status not in [OrchestrationStatus.RUNNING, OrchestrationStatus.OPTIMIZING]:
                    return False
                
                self._stop_execution.set()
                
                # Wait for execution thread to finish
                if self._execution_thread and self._execution_thread.is_alive():
                    self._execution_thread.join(timeout=5.0)
                
                self.status = OrchestrationStatus.PAUSED
                self.workflow_status.total_progress = 0.5
                
                logging.info("✅ Orchestration stopped")
                return True
                
        except Exception as e:
            logging.error(f"Error stopping orchestration: {e}")
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """Get current orchestration status"""
        try:
            with self._lock:
                return {
                    "status": self.status.value,
                    "workflow_phase": self.workflow_status.current_phase.value,
                    "workflow_status": "running" if self.status == OrchestrationStatus.RUNNING else "completed" if self.status == OrchestrationStatus.COMPLETED else "idle",
                    "metrics": {
                        "total_agents": self.metrics.total_agents,
                        "successful_agents": self.metrics.successful_agents,
                        "failed_agents": self.metrics.failed_agents,
                        "total_plays": self.metrics.total_plays_generated,
                        "execution_time": self.metrics.total_execution_time,
                        "portfolio_size": self.metrics.final_portfolio_size,
                        "portfolio_roi": self.metrics.final_portfolio_roi,
                        "portfolio_risk": self.metrics.final_portfolio_risk,
                        "integration_health": self.metrics.integration_health,
                        "fallback_mode": self.metrics.fallback_mode_activated,
                        "circuit_breaker_trips": self.metrics.circuit_breaker_trips
                    },
                    "agent_status": {k: v.value for k, v in self.agent_status.items()},
                    "agent_progress": {k: float(v) for k, v in self.agent_progress.items()},
                    "integration_status": self.get_integration_status()
                }
                
        except Exception as e:
            logging.error(f"Error getting status: {e}")
            return {"error": str(e)}
    
    def get_results(self) -> Dict[str, Any]:
        """Get orchestration results"""
        try:
            with self._lock:
                return {
                    "status": self.status.value,
                    "initial_portfolio": self.initial_portfolio.to_dict() if self.initial_portfolio else None,
                    "optimized_portfolio": self.optimized_portfolio.to_dict() if self.optimized_portfolio else None,
                    "agent_results": {
                        area: [play.to_dict() for play in plays] 
                        for area, plays in self.agent_results.items()
                    },
                    "metrics": {
                        "total_execution_time": self.metrics.total_execution_time,
                        "total_plays_generated": self.metrics.total_plays_generated,
                        "portfolio_optimization_time": self.metrics.portfolio_optimization_time,
                        "final_portfolio_size": self.metrics.final_portfolio_size,
                        "final_portfolio_roi": self.metrics.final_portfolio_roi,
                        "final_portfolio_risk": self.metrics.final_portfolio_risk
                    },
                    "fallback_mode": self.metrics.fallback_mode_activated
                }
                
        except Exception as e:
            logging.error(f"Error getting results: {e}")
            return {"error": str(e)}
    
    def add_progress_callback(self, callback: Callable):
        """Add progress callback function"""
        if callback not in self._progress_callbacks:
            self._progress_callbacks.append(callback)
    
    def add_status_callback(self, callback: Callable):
        """Add status callback function"""
        if callback not in self._status_callbacks:
            self._status_callbacks.append(callback)
    
    def _notify_progress(self, progress: float, message: str):
        """Notify progress callbacks"""
        try:
            # Cache latest progress/message for UI polling
            with self._lock:
                self._last_progress = progress
                self._last_message = message
            for callback in self._progress_callbacks:
                try:
                    callback(progress, message)
                except Exception as e:
                    logging.error(f"Progress callback error: {e}")
            # Log progress to dedicated activity log
            try:
                self._logger.info(f"event=progress value={progress:.2f} msg={message}")
            except Exception:
                pass
        except Exception as e:
            logging.error(f"Error notifying progress: {e}")
    
    def _notify_status(self, message: str):
        """Notify status callbacks"""
        try:
            # Cache latest message for UI polling
            with self._lock:
                self._last_message = message
            for callback in self._status_callbacks:
                try:
                    callback(message)
                except Exception as e:
                    logging.error(f"Status callback error: {e}")
            # Log status message to dedicated activity log
            try:
                self._logger.info(f"event=status msg={message}")
            except Exception:
                pass
        except Exception as e:
            logging.error(f"Error notifying status: {e}")

    def get_live_update(self) -> Dict[str, Any]:
        """Get latest progress/message snapshot and orchestration status."""
        try:
            with self._lock:
                return {
                    "status": self.status.value,
                    "workflow_phase": self.workflow_status.current_phase.value,
                    "progress": self._last_progress,
                    "message": self._last_message,
                    "metrics": {
                        "total_agents": self.metrics.total_agents,
                        "successful_agents": self.metrics.successful_agents,
                        "failed_agents": self.metrics.failed_agents
                    }
                }
        except Exception as e:
            logging.error(f"Error getting live update: {e}")
            return {"status": "error", "error": str(e)}
    
    def _should_stop_execution(self) -> bool:
        """Check if execution should stop"""
        return self._stop_execution.is_set()
    
    def _log_orchestration(self, message: str, level: str = "INFO"):
        """Log orchestration events"""
        try:
            log_func = getattr(logging, level.lower(), logging.info)
            log_func(f"[Orchestrator] {message}")
        except Exception as e:
            logging.error(f"Error logging orchestration: {e}")
    
    def get_integration_status(self) -> Dict[str, Any]:
        """Get integration system status"""
        try:
            if self.integration_manager:
                return self.integration_manager.check_system_health()
            else:
                return {"overall_health": "not_available"}
        except Exception as e:
            logging.error(f"Error getting integration status: {e}")
            return {"overall_health": "error", "error": str(e)}
    
    def get_kpi_data_for_area(self, area: SubjectArea, days: int = 30) -> List[Dict[str, Any]]:
        """Get KPI data for a specific area"""
        try:
            if self.integration_manager:
                return self.integration_manager.get_kpi_data_for_area(area, days)
            else:
                return []
        except Exception as e:
            logging.error(f"Error getting KPI data: {e}")
            return []
    
    def validate_and_scrub_data(self, data: Any, data_type: str = "play") -> Any:
        """Validate and scrub data using integration layer"""
        try:
            if self.integration_manager:
                return self.integration_manager.validate_and_scrub_data(data, data_type)
            else:
                return data
        except Exception as e:
            logging.error(f"Error validating/scrubbing data: {e}")
            return data
    
    def manual_override_agent(self, agent_name: str, action: str, **kwargs) -> Dict[str, Any]:
        """Manual override for agent actions"""
        try:
            if self.backup_demo:
                return self.backup_demo.manual_override_agent(agent_name, action, **kwargs)
            else:
                return {
                    "success": False,
                    "error": "Backup demo mode not available",
                    "timestamp": datetime.now().isoformat()
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }


def create_orchestrator(config: OrchestrationConfig = None) -> AgentOrchestrator:
    """Create a new orchestrator instance"""
    return AgentOrchestrator(config)


def run_orchestration(config: OrchestrationConfig = None, timeout: int = 60) -> Dict[str, Any]:
    """Run orchestration with timeout"""
    orchestrator = create_orchestrator(config)
    
    def progress_callback(progress: float, message: str):
        print(f"Progress: {progress:.1%} - {message}")
    
    orchestrator.add_progress_callback(progress_callback)
    
    if orchestrator.start_orchestration():
        # Wait for completion or timeout
        start_time = time.time()
        while orchestrator.status not in [OrchestrationStatus.COMPLETED, OrchestrationStatus.FAILED]:
            if time.time() - start_time > timeout:
                orchestrator.stop_orchestration()
                break
            time.sleep(0.1)
        
        return orchestrator.get_results()
    else:
        return {"error": "Failed to start orchestration"}
