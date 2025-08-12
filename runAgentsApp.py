"""
Playbook Prioritizer Agent - Main Orchestrator App

This is the main Streamlit application that demonstrates the multi-agent system
with real-time progress visualization, portfolio optimization, and stunning UI.
"""

import streamlit as st
import time
import json
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
from typing import Dict, List, Any
import pandas as pd

from agents.orchestrator import AgentOrchestrator, OrchestrationConfig
from agents.mock_intelligence import get_mock_intelligence_engine
from agents.integration_layer import get_integration_manager
from agents.backup_demo_mode import get_backup_demo
from models.play_models import SubjectArea, Play, Portfolio, WorkflowPhase

# Page configuration
st.set_page_config(
    page_title="AI Agent Orchestration System",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for stunning visuals
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
        padding: 2.5rem;
        border-radius: 20px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        animation: gradientShift 3s ease-in-out infinite;
    }
    
    @keyframes gradientShift {
        0%, 100% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
    }
    
    .agent-card {
        background: white;
        border: 2px solid #e0e0e0;
        border-radius: 20px;
        padding: 2rem;
        margin: 1rem 0;
        box-shadow: 0 8px 25px rgba(0,0,0,0.1);
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: hidden;
    }
    
    .agent-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.4), transparent);
        transition: left 0.5s;
    }
    
    .agent-card:hover::before {
        left: 100%;
    }
    
    .agent-card:hover {
        transform: translateY(-5px) scale(1.02);
        box-shadow: 0 20px 40px rgba(0,0,0,0.15);
        border-color: #667eea;
    }
    
    .agent-working {
        border-color: #ff6b6b;
        background: linear-gradient(135deg, #fff5f5 0%, #ffe8e8 100%);
        animation: pulse 2s infinite;
    }
    
    .agent-completed {
        border-color: #51cf66;
        background: linear-gradient(135deg, #f8fff9 0%, #ebfbee 100%);
        animation: successGlow 1s ease-out;
    }
    
    .agent-failed {
        border-color: #ff4757;
        background: linear-gradient(135deg, #fff5f5 0%, #ffe8e8 100%);
        animation: errorPulse 2s infinite;
    }
    
    .fallback-mode {
        border-color: #ffa502;
        background: linear-gradient(135deg, #fff8e1 0%, #fff3e0 100%);
        animation: fallbackGlow 2s ease-in-out infinite;
    }
    
    .circuit-breaker-open {
        border-color: #ff4757;
        background: linear-gradient(135deg, #fff5f5 0%, #ffe8e8 100%);
        animation: circuitBreakerPulse 1s ease-in-out infinite;
    }
    
    @keyframes pulse {
        0% { box-shadow: 0 0 0 0 rgba(255, 107, 107, 0.7); }
        70% { box-shadow: 0 0 0 10px rgba(255, 107, 107, 0); }
        100% { box-shadow: 0 0 0 0 rgba(255, 107, 107, 0); }
    }
    
    @keyframes successGlow {
        0% { box-shadow: 0 0 0 0 rgba(81, 207, 102, 0.7); }
        100% { box-shadow: 0 0 0 20px rgba(81, 207, 102, 0); }
    }
    
    @keyframes errorPulse {
        0% { box-shadow: 0 0 0 0 rgba(255, 71, 87, 0.7); }
        70% { box-shadow: 0 0 0 10px rgba(255, 71, 87, 0); }
        100% { box-shadow: 0 0 0 0 rgba(255, 71, 87, 0); }
    }
    
    @keyframes fallbackGlow {
        0%, 100% { box-shadow: 0 0 0 0 rgba(255, 165, 2, 0.3); }
        50% { box-shadow: 0 0 0 10px rgba(255, 165, 2, 0.1); }
    }
    
    @keyframes circuitBreakerPulse {
        0%, 100% { box-shadow: 0 0 0 0 rgba(255, 71, 87, 0.7); }
        50% { box-shadow: 0 0 0 15px rgba(255, 71, 87, 0.3); }
    }
    
    .status-indicator {
        display: inline-block;
        width: 12px;
        height: 12px;
        border-radius: 50%;
        margin-right: 8px;
        animation: statusPulse 2s infinite;
    }
    
    .status-healthy { background-color: #51cf66; }
    .status-degraded { background-color: #ffa502; }
    .status-unhealthy { background-color: #ff4757; }
    .status-unknown { background-color: #95a5a6; }
    
    @keyframes statusPulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }
    
    .integration-panel {
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        border-radius: 15px;
        padding: 1.5rem;
        margin: 1rem 0;
        border-left: 5px solid #667eea;
    }
    
    .manual-override-panel {
        background: linear-gradient(135deg, #fff3cd 0%, #ffeaa7 100%);
        border-radius: 15px;
        padding: 1.5rem;
        margin: 1rem 0;
        border-left: 5px solid #ffa502;
    }
    
    .metric-card {
        background: white;
        border-radius: 15px;
        padding: 1.5rem;
        margin: 0.5rem;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        text-align: center;
        transition: transform 0.3s ease;
    }
    
    .metric-card:hover {
        transform: translateY(-2px);
    }
    
    .metric-value {
        font-size: 2rem;
        font-weight: bold;
        color: #667eea;
        margin-bottom: 0.5rem;
    }
    
    .metric-label {
        color: #6c757d;
        font-size: 0.9rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
def initialize_session_state():
    """Initialize session state variables"""
    if 'orchestrator' not in st.session_state:
        st.session_state.orchestrator = None
    if 'orchestration_started' not in st.session_state:
        st.session_state.orchestration_started = False
    if 'current_status' not in st.session_state:
        st.session_state.current_status = None
    if 'integration_status' not in st.session_state:
        st.session_state.integration_status = None
    if 'manual_override_result' not in st.session_state:
        st.session_state.manual_override_result = None

# Create orchestrator
def create_orchestrator():
    """Create and configure the agent orchestrator"""
    config = OrchestrationConfig(
        max_concurrent_agents=5,
        agent_timeout_seconds=30,
        optimization_iterations=3,
        portfolio_size_target=15,
        min_roi_threshold=7.0,
        max_risk_threshold=6.0,
        enable_parallel_execution=True,
        progress_update_interval=0.5,
        enable_circuit_breaker=True,
        max_failures_before_fallback=3,
        fallback_timeout_seconds=60
    )
    
    orchestrator = AgentOrchestrator(config)
    
    def progress_callback(progress: float, message: str):
        st.session_state.current_progress = progress
        st.session_state.current_message = message
    
    def status_callback(message: str):
        st.session_state.current_status = message
    
    orchestrator.add_progress_callback(progress_callback)
    orchestrator.add_status_callback(status_callback)
    
    return orchestrator

# Display header
def display_header():
    """Display the main header"""
    st.markdown("""
    <div class="main-header">
        <h1>🤖 AI Agent Orchestration System</h1>
        <p>Enterprise-Grade Multi-Agent Portfolio Optimization</p>
    </div>
    """, unsafe_allow_html=True)

# Display workflow phases
def display_workflow_phases():
    """Display workflow phase indicators"""
    st.subheader("🔄 Workflow Phases")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.markdown("**1. Initialization**")
        st.markdown("System setup & agent preparation")
    
    with col2:
        st.markdown("**2. Agent Execution**")
        st.markdown("Parallel analysis across subject areas")
    
    with col3:
        st.markdown("**3. Portfolio Creation**")
        st.markdown("Initial portfolio assembly")
    
    with col4:
        st.markdown("**4. Optimization**")
        st.markdown("Advanced portfolio optimization")
    
    with col5:
        st.markdown("**5. Completion**")
        st.markdown("Results & executive summary")

# Display workflow diagram
def display_workflow_diagram():
    """Display interactive workflow diagram"""
    st.subheader("📊 Workflow Visualization")
    
    # Create workflow diagram using columns
    col1, col2, col3, col4, col5, col6, col7, col8 = st.columns(8)
    
    with col1:
        st.markdown("**Acquisition**<br>Agent", unsafe_allow_html=True)
        st.markdown("🔍", help="Analyzing customer acquisition opportunities")
    
    with col2:
        st.markdown("→")
    
    with col3:
        st.markdown("**Retention**<br>Agent", unsafe_allow_html=True)
        st.markdown("🔍", help="Analyzing customer retention strategies")
    
    with col4:
        st.markdown("→")
    
    with col5:
        st.markdown("**Network QoE**<br>Agent", unsafe_allow_html=True)
        st.markdown("🔍", help="Analyzing network quality of experience")
    
    with col6:
        st.markdown("→")
    
    with col7:
        st.markdown("**Support**<br>Agent", unsafe_allow_html=True)
        st.markdown("🔍", help="Analyzing support optimization")
    
    with col8:
        st.markdown("→")
    
    # Second row
    col1, col2, col3, col4, col5, col6, col7, col8 = st.columns(8)
    
    with col1:
        st.markdown("")
    
    with col2:
        st.markdown("")
    
    with col3:
        st.markdown("")
    
    with col4:
        st.markdown("**Portfolio**<br>Optimization", unsafe_allow_html=True)
        st.markdown("⚡", help="Advanced portfolio selection and optimization")
    
    with col5:
        st.markdown("")
    
    with col6:
        st.markdown("")
    
    with col7:
        st.markdown("")
    
    with col8:
        st.markdown("**Executive**<br>Summary", unsafe_allow_html=True)
        st.markdown("📋", help="Final recommendations and implementation roadmap")

# Display agent status
def display_agent_status(orchestrator):
    """Display real-time agent status"""
    st.subheader("🤖 Agent Status")
    
    if not orchestrator:
        st.warning("No orchestrator available")
        return
    
    status = orchestrator.get_status()
    
    # Display integration health
    if 'integration_status' in status:
        integration_health = status['integration_status'].get('overall_health', 'unknown')
        health_color = {
            'healthy': 'status-healthy',
            'degraded': 'status-degraded', 
            'unhealthy': 'status-unhealthy',
            'unknown': 'status-unknown'
        }.get(integration_health, 'status-unknown')
        
        st.markdown(f"""
        <div class="integration-panel">
            <h4>🔗 Integration Status</h4>
            <p><span class="status-indicator {health_color}"></span>
            <strong>Overall Health:</strong> {integration_health.title()}</p>
            <p><strong>Fallback Mode:</strong> {'🟡 Active' if status.get('metrics', {}).get('fallback_mode') else '🟢 Normal'}</p>
            <p><strong>Circuit Breaker Trips:</strong> {status.get('metrics', {}).get('circuit_breaker_trips', 0)}</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Display agent cards
    if 'agent_status' in status:
        agent_status = status['agent_status']
        
        for area_name, agent_state in agent_status.items():
            # Determine card styling based on status
            card_class = "agent-card"
            if agent_state == "completed":
                card_class += " agent-completed"
            elif agent_state == "analyzing":
                card_class += " agent-working"
            elif agent_state == "failed":
                card_class += " agent-failed"
            
            # Add fallback mode styling if applicable
            if status.get('metrics', {}).get('fallback_mode'):
                card_class += " fallback-mode"
            
            st.markdown(f"""
            <div class="{card_class}">
                <h4>{area_name.replace('_', ' ').title()} Agent</h4>
                <p><strong>Status:</strong> {agent_state.title()}</p>
                <p><strong>Area:</strong> {area_name}</p>
            </div>
            """, unsafe_allow_html=True)

# Display workflow progress
def display_workflow_progress(orchestrator):
    """Display workflow progress and metrics"""
    st.subheader("📈 Workflow Progress")
    
    if not orchestrator:
        st.warning("No orchestrator available")
        return
    
    status = orchestrator.get_status()
    metrics = status.get('metrics', {})
    
    # Display progress metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{metrics.get('successful_agents', 0)}</div>
            <div class="metric-label">Successful Agents</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{metrics.get('total_plays', 0)}</div>
            <div class="metric-label">Total Plays</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{metrics.get('portfolio_size', 0)}</div>
            <div class="metric-label">Portfolio Size</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        execution_time = metrics.get('execution_time', 0)
        if execution_time > 0:
            time_str = f"{execution_time:.1f}s"
        else:
            time_str = "N/A"
        
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{time_str}</div>
            <div class="metric-label">Execution Time</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Display current status message
    if hasattr(st.session_state, 'current_message') and st.session_state.current_message:
        st.info(f"🔄 **Current Status:** {st.session_state.current_message}")
    
    # Display workflow phase
    workflow_phase = status.get('workflow_phase', 'unknown')
    st.markdown(f"**Current Phase:** {workflow_phase.replace('_', ' ').title()}")

# Display portfolio results
def display_portfolio_results(portfolio):
    """Display portfolio optimization results"""
    if not portfolio:
        st.warning("No portfolio results available")
        return
    
    st.subheader("💼 Portfolio Results")
    
    # Portfolio overview
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Effort", f"{portfolio.total_effort} points")
    
    with col2:
        st.metric("ROI Score", f"{portfolio.roi_score:.1f}")
    
    with col3:
        st.metric("Risk Score", f"{portfolio.risk_score:.1f}")
    
    # Portfolio plays table
    if hasattr(portfolio, 'plays') and portfolio.plays:
        st.subheader("📋 Selected Plays")
        
        plays_data = []
        for i, play in enumerate(portfolio.plays):
            plays_data.append({
                "Rank": i + 1,
                "Title": play.title,
                "Area": play.area.value if hasattr(play.area, 'value') else str(play.area),
                "Effort": play.effort_points,
                "Impact": play.impact_score,
                "Confidence": f"{play.confidence:.1%}",
                "ROI": f"{play.impact_score / play.effort_points:.2f}"
            })
        
        df = pd.DataFrame(plays_data)
        st.dataframe(df, use_container_width=True)
        
        # Expected effects
        if hasattr(portfolio, 'expected_effect') and portfolio.expected_effect:
            st.subheader("🎯 Expected Effects")
            
            effects_data = []
            for kpi, effect in portfolio.expected_effect.items():
                effects_data.append({
                    "KPI": kpi,
                    "Expected Change": f"{effect:+.1%}" if isinstance(effect, (int, float)) else str(effect)
                })
            
            effects_df = pd.DataFrame(effects_data)
            st.dataframe(effects_df, use_container_width=True)
    
    # Portfolio visualization
    if hasattr(portfolio, 'plays') and portfolio.plays:
        st.subheader("📊 Portfolio Distribution")
        
        # Effort distribution by area
        area_effort = {}
        for play in portfolio.plays:
            area = play.area.value if hasattr(play.area, 'value') else str(play.area)
            if area not in area_effort:
                area_effort[area] = 0
            area_effort[area] += play.effort_points
        
        if area_effort:
            fig = px.pie(
                values=list(area_effort.values()),
                names=list(area_effort.keys()),
                title="Effort Distribution by Subject Area"
            )
            st.plotly_chart(fig, use_container_width=True)

# Display executive summary
def display_executive_summary(portfolio):
    """Display executive summary and recommendations"""
    if not portfolio:
        st.warning("No executive summary available")
        return
    
    st.subheader("📋 Executive Summary")
    
    # Summary text
    st.markdown("""
    **Strategic Portfolio Recommendation**
    
    Based on our AI agent analysis across all subject areas, we recommend the following 
    high-impact initiatives that deliver maximum value within your resource constraints.
    """)
    
    # Key highlights
    if hasattr(portfolio, 'plays') and portfolio.plays:
        st.markdown("**🎯 Key Highlights:**")
        
        # Top 3 plays
        top_plays = sorted(portfolio.plays, key=lambda p: p.impact_score / p.effort_points, reverse=True)[:3]
        
        for i, play in enumerate(top_plays):
            roi = play.impact_score / play.effort_points
            st.markdown(f"""
            **{i+1}. {play.title}**
            - **Area:** {play.area.value if hasattr(play.area, 'value') else str(play.area)}
            - **Effort:** {play.effort_points} points
            - **Impact:** {play.impact_score}/5
            - **ROI:** {roi:.2f}
            - **Confidence:** {play.confidence:.1%}
            """)
    
    # Implementation roadmap
    st.markdown("**🚀 Implementation Roadmap:**")
    
    if hasattr(portfolio, 'plays') and portfolio.plays:
        # Sort by effort for implementation order
        sorted_plays = sorted(portfolio.plays, key=lambda p: p.effort_points)
        
        for i, play in enumerate(sorted_plays):
            st.markdown(f"""
            **Phase {i+1}:** {play.title} ({play.effort_points} points)
            - Estimated duration: {play.effort_points * 2} weeks
            - Dependencies: {', '.join(play.dependencies) if play.dependencies else 'None'}
            """)
    
    # Risk assessment
    if hasattr(portfolio, 'risk_score'):
        risk_level = "Low" if portfolio.risk_score < 4 else "Medium" if portfolio.risk_score < 7 else "High"
        st.markdown(f"""
        **⚠️ Risk Assessment:**
        - **Overall Risk Level:** {risk_level} ({portfolio.risk_score:.1f}/10)
        - **Risk Mitigation:** Implement plays sequentially to minimize operational disruption
        """)

# Display control panel
def display_control_panel():
    """Display orchestration control panel"""
    st.subheader("🎛️ Control Panel")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🚀 Start Orchestration", type="primary", use_container_width=True):
            if not st.session_state.orchestrator:
                st.session_state.orchestrator = create_orchestrator()
            
            if st.session_state.orchestrator.start_orchestration():
                st.session_state.orchestration_started = True
                st.success("Orchestration started successfully!")
                st.rerun()
            else:
                st.error("Failed to start orchestration")
    
    with col2:
        if st.button("⏹️ Stop Orchestration", use_container_width=True):
            if st.session_state.orchestrator:
                if st.session_state.orchestrator.stop_orchestration():
                    st.success("Orchestration stopped")
                    st.rerun()
                else:
                    st.error("Failed to stop orchestration")
    
    with col3:
        if st.button("🔄 Reset System", use_container_width=True):
            st.session_state.orchestrator = None
            st.session_state.orchestration_started = False
            st.session_state.current_status = None
            st.success("System reset successfully!")
            st.rerun()
    
    # Manual override panel
    st.markdown("""
    <div class="manual-override-panel">
        <h4>🔧 Manual Override Controls</h4>
        <p>Use these controls to manually override agent behavior or force completion.</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        agent_name = st.selectbox(
            "Select Agent",
            ["Network QoE Agent", "Customer Agent", "Revenue Agent", "Operations Agent", "Usage Agent"]
        )
    
    with col2:
        action = st.selectbox(
            "Select Action",
            ["force_complete", "generate_plays", "reset_status"]
        )
    
    with col3:
        if st.button("Execute Override", use_container_width=True):
            if st.session_state.orchestrator:
                result = st.session_state.orchestrator.manual_override_agent(agent_name, action)
                st.session_state.manual_override_result = result
                
                if result.get('success'):
                    st.success(f"Override executed: {action}")
                else:
                    st.error(f"Override failed: {result.get('error', 'Unknown error')}")
    
    # Display override result
    if st.session_state.manual_override_result:
        result = st.session_state.manual_override_result
        if result.get('success'):
            st.success(f"✅ Override Result: {result.get('message', 'Action completed')}")
        else:
            st.error(f"❌ Override Failed: {result.get('error', 'Unknown error')}")

# Main application
def main():
    """Main application function"""
    initialize_session_state()
    
    # Display header
    display_header()
    
    # Sidebar
    with st.sidebar:
        st.header("🎯 System Overview")
        
        if st.session_state.orchestrator:
            status = st.session_state.orchestrator.get_status()
            
            st.markdown(f"""
            **Status:** {status.get('status', 'unknown').title()}
            **Phase:** {status.get('workflow_phase', 'unknown').replace('_', ' ').title()}
            **Agents:** {status.get('metrics', {}).get('successful_agents', 0)}/{status.get('metrics', {}).get('total_agents', 0)} successful
            """)
            
            # Integration health indicator
            integration_health = status.get('integration_status', {}).get('overall_health', 'unknown')
            health_emoji = {
                'healthy': '🟢',
                'degraded': '🟡', 
                'unhealthy': '🔴',
                'unknown': '⚪'
            }.get(integration_health, '⚪')
            
            st.markdown(f"**Integration Health:** {health_emoji} {integration_health.title()}")
            
            # Circuit breaker status
            circuit_trips = status.get('metrics', {}).get('circuit_breaker_trips', 0)
            if circuit_trips > 0:
                st.warning(f"⚠️ Circuit Breaker Trips: {circuit_trips}")
            
            # Fallback mode indicator
            if status.get('metrics', {}).get('fallback_mode'):
                st.info("🟡 Fallback Mode Active")
        
        st.markdown("---")
        st.markdown("**Quick Actions**")
        
        if st.button("📊 View Status", use_container_width=True):
            st.rerun()
        
        if st.button("🔍 Check Integration", use_container_width=True):
            if st.session_state.orchestrator:
                integration_status = st.session_state.orchestrator.get_integration_status()
                st.session_state.integration_status = integration_status
                st.rerun()
    
    # Main content
    tab1, tab2, tab3, tab4 = st.tabs([
        "🎬 Orchestration", 
        "📊 Status & Metrics", 
        "💼 Portfolio Results", 
        "🔧 Controls"
    ])
    
    with tab1:
        st.header("🎬 Agent Orchestration")
        
        # Display workflow phases
        display_workflow_phases()
        
        # Display workflow diagram
        display_workflow_diagram()
        
        # Control panel
        display_control_panel()
        
        # Status updates
        if st.session_state.orchestration_started and st.session_state.orchestrator:
            st.info("🔄 Orchestration is running... Check the Status & Metrics tab for real-time updates.")
    
    with tab2:
        st.header("📊 Status & Metrics")
        
        if st.session_state.orchestrator:
            # Display agent status
            display_agent_status(st.session_state.orchestrator)
            
            # Display workflow progress
            display_workflow_progress(st.session_state.orchestrator)
            
            # Integration status details
            if st.session_state.integration_status:
                st.subheader("🔗 Detailed Integration Status")
                
                integration_data = []
                for component, status in st.session_state.integration_status.items():
                    if component != 'overall_health':
                        status_emoji = "✅" if status else "❌"
                        integration_data.append({
                            "Component": component.replace('_', ' ').title(),
                            "Status": f"{status_emoji} {'Available' if status else 'Unavailable'}"
                        })
                
                if integration_data:
                    integration_df = pd.DataFrame(integration_data)
                    st.dataframe(integration_df, use_container_width=True)
        else:
            st.info("No orchestrator available. Start orchestration from the Orchestration tab.")
    
    with tab3:
        st.header("💼 Portfolio Results")
        
        if (st.session_state.orchestrator and 
            st.session_state.orchestrator.status.value == "completed"):
            
            results = st.session_state.orchestrator.get_results()
            
            if 'optimized_portfolio' in results and results['optimized_portfolio']:
                # Convert dict back to Portfolio object for display
                portfolio_data = results['optimized_portfolio']
                portfolio = Portfolio(
                    plays=[],
                    total_effort=portfolio_data.get('total_effort', 0),
                    expected_effect=portfolio_data.get('expected_effect', {}),
                    roi_score=portfolio_data.get('roi_score', 0),
                    risk_score=portfolio_data.get('risk_score', 0)
                )
                
                # Display portfolio results
                display_portfolio_results(portfolio)
                
                # Display executive summary
                display_executive_summary(portfolio)
            else:
                st.warning("No portfolio results available yet.")
        else:
            st.info("Complete orchestration to view portfolio results.")
    
    with tab4:
        st.header("🔧 System Controls")
        
        # System health check
        if st.button("🏥 Run System Health Check", type="primary"):
            if st.session_state.orchestrator:
                health_status = st.session_state.orchestrator.get_integration_status()
                st.session_state.integration_status = health_status
                st.success("Health check completed!")
                st.rerun()
        
        # Display current system status
        if st.session_state.orchestrator:
            st.subheader("📊 Current System Status")
            
            status = st.session_state.orchestrator.get_status()
            
            # System metrics
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total Agents", status.get('metrics', {}).get('total_agents', 0))
            
            with col2:
                st.metric("Successful Agents", status.get('metrics', {}).get('successful_agents', 0))
            
            with col3:
                st.metric("Failed Agents", status.get('metrics', {}).get('failed_agents', 0))
            
            # Detailed status
            st.json(status)
        else:
            st.info("No orchestrator available. Create one to view system status.")

if __name__ == "__main__":
    main()
