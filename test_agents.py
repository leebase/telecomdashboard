#!/usr/bin/env python3
"""
Test script to verify agent functionality works correctly
"""

import sys
import time
from agents.orchestrator import AgentOrchestrator, OrchestrationConfig

def test_agent_orchestration():
    """Test the agent orchestration system"""
    print("🔧 Testing Agent Orchestration System...")
    
    # Create configuration
    config = OrchestrationConfig(
        max_concurrent_agents=1,
        agent_timeout_seconds=15,
        optimization_iterations=3,
        portfolio_size_target=15,
        min_roi_threshold=7.0,
        max_risk_threshold=6.0,
        enable_parallel_execution=False,
        progress_update_interval=0.3,
        enable_circuit_breaker=True,
        max_failures_before_fallback=3,
        fallback_timeout_seconds=60
    )
    
    # Create orchestrator
    orchestrator = AgentOrchestrator(config)
    
    # Add progress callback
    def progress_callback(progress: float, message: str):
        print(f"Progress: {progress:.1%} - {message}")
    
    orchestrator.add_progress_callback(progress_callback)
    
    # Start orchestration
    print("🚀 Starting orchestration...")
    if orchestrator.start_orchestration():
        print("✅ Orchestration started successfully!")
        
        # Monitor progress
        start_time = time.time()
        while orchestrator.status.value not in ['completed', 'failed']:
            # Get live update
            live_update = orchestrator.get_live_update()
            print(f"Status: {live_update.get('status')} - Progress: {live_update.get('progress', 0):.1%} - {live_update.get('message', 'No message')}")
            
            # Check for timeout
            if time.time() - start_time > 60:
                print("⏰ Timeout reached")
                break
                
            time.sleep(2)
        
        # Get final results
        results = orchestrator.get_results()
        print(f"🎯 Final Status: {results.get('status')}")
        
        if results.get('optimized_portfolio'):
            portfolio = results['optimized_portfolio']
            print(f"📊 Portfolio Results:")
            print(f"  - Selected Plays: {len(portfolio.get('selected_plays', []))}")
            print(f"  - Total ROI: {portfolio.get('total_roi', 0):.2f}")
            print(f"  - Average Priority: {portfolio.get('average_priority', 0):.2f}")
        
        return True
    else:
        print("❌ Failed to start orchestration")
        return False

if __name__ == "__main__":
    success = test_agent_orchestration()
    sys.exit(0 if success else 1)