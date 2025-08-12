#!/usr/bin/env python3
"""
Test script to verify the agent orchestration UI fix
"""

import time
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents.orchestrator import AgentOrchestrator, OrchestrationConfig

def test_orchestrator_ui_simulation():
    """Simulate the UI polling mechanism to test the fix"""
    print("🧪 Testing Agent Orchestration UI Fix...")
    print("=" * 50)
    
    # Create orchestrator with same config as UI
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
    
    orchestrator = AgentOrchestrator(config)
    
    # Simulate UI session state
    ui_state = {
        'agent_status': 'idle',
        'agent_progress': 0.0,
        'agent_message': "Ready to launch analysis",
        'agent_phase': "Initialization",
        'last_refresh': time.time()
    }
    
    print("🚀 Starting orchestration...")
    if orchestrator.start_orchestration():
        ui_state['agent_status'] = 'running'
        ui_state['agent_message'] = "Initializing agents..."
        print("✅ Orchestration started successfully!")
    else:
        print("❌ Failed to start orchestration")
        return False
    
    # Simulate UI polling loop
    max_iterations = 80  # 40 seconds with 0.5s intervals (agents now take ~5s each x6)
    iteration = 0
    
    while ui_state['agent_status'] == 'running' and iteration < max_iterations:
        iteration += 1
        
        # Simulate the UI polling logic (same as in app.py)
        try:
            status_enum = getattr(orchestrator, 'status', None)
            status_value = getattr(status_enum, 'value', None)
            
            if status_value == 'completed':
                ui_state['agent_status'] = 'completed'
                ui_state['agent_results'] = orchestrator.get_results()
                ui_state['agent_message'] = 'Analysis complete - results ready'
                ui_state['agent_progress'] = 1.0
                ui_state['agent_phase'] = 'Completion'
                print("🎉 UI detected completion!")
                break
            elif status_value == 'failed':
                ui_state['agent_status'] = 'failed'
                ui_state['agent_message'] = 'Agent orchestration failed'
                print("❌ UI detected failure!")
                break
        except Exception as e:
            print(f"⚠️ Error checking status: {e}")
        
        # Get live updates
        try:
            live = orchestrator.get_live_update()
            if isinstance(live, dict):
                live_progress = float(live.get('progress', 0.0) or 0.0)
                if live_progress > ui_state.get('agent_progress', 0.0):
                    ui_state['agent_progress'] = live_progress
                
                live_message = live.get('message')
                if isinstance(live_message, str) and live_message:
                    ui_state['agent_message'] = live_message
                
                # Update phase
                phase = str(live.get('workflow_phase', '') or '')
                phase_map = {
                    'initialization': 'Initialization',
                    'agent_analysis': 'Agent Execution',
                    'portfolio_optimization': 'Optimization',
                    'results_presentation': 'Completion',
                    'completed': 'Completion'
                }
                if phase in phase_map:
                    ui_state['agent_phase'] = phase_map[phase]
        except Exception as e:
            print(f"⚠️ Error getting live update: {e}")
        
        # Print current status
        progress_pct = ui_state['agent_progress'] * 100
        print(f"[{iteration:2d}] Status: {ui_state['agent_status']} | Progress: {progress_pct:5.1f}% | Phase: {ui_state['agent_phase']} | Message: {ui_state['agent_message']}")
        
        # Simulate UI refresh interval
        time.sleep(0.5)
    
    # Final status
    print("\n" + "=" * 50)
    print(f"🏁 Final Status: {ui_state['agent_status']}")
    print(f"📊 Final Progress: {ui_state['agent_progress'] * 100:.1f}%")
    print(f"📋 Final Phase: {ui_state['agent_phase']}")
    print(f"💬 Final Message: {ui_state['agent_message']}")
    
    if ui_state['agent_status'] == 'completed':
        print("✅ UI FIX SUCCESSFUL - Orchestration completed and UI detected it!")
        return True
    elif ui_state['agent_status'] == 'running':
        print("⏰ UI FIX PARTIAL - Orchestration still running (may need more time)")
        return False
    else:
        print("❌ UI FIX FAILED - Orchestration failed or UI didn't detect completion")
        return False

if __name__ == "__main__":
    success = test_orchestrator_ui_simulation()
    sys.exit(0 if success else 1)