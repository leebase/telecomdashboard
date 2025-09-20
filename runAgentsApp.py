"""
Playbook Prioritizer Agent - Main Orchestrator App

This is the main Streamlit application that demonstrates the multi-agent system
with real-time progress visualization, portfolio optimization, and stunning UI.
"""

from pathlib import Path
import sys

import streamlit as st
import time
import json
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
from typing import Dict, List, Any
import pandas as pd

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ui.runtime_switch import is_metadata_enabled

if is_metadata_enabled():
    from ui.metadata_runtime_app import render_metadata_dashboard

    render_metadata_dashboard()
    st.stop()

from agents.orchestrator import AgentOrchestrator, OrchestrationConfig
from agents.mock_intelligence import get_mock_intelligence_engine
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
    
    @keyframes pulse {
        0% { box-shadow: 0 0 0 0 rgba(255, 107, 107, 0.7); }
        70% { box-shadow: 0 0 0 10px rgba(255, 107, 107, 0); }
        100% { box-shadow: 0 0 0 0 rgba(255, 107, 107, 0); }
    }
    
    @keyframes successGlow {
        0% { box-shadow: 0 0 0 0 rgba(81, 207, 102, 0.7); }
        100% { box-shadow: 0 0 20px 10px rgba(81, 207, 102, 0); }
    }
    
    .progress-bar {
        height: 12px;
        border-radius: 6px;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        position: relative;
        overflow: hidden;
    }
    
    .progress-bar::after {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.6), transparent);
        animation: shimmer 2s infinite;
    }
    
    @keyframes shimmer {
        0% { left: -100%; }
        100% { left: 100%; }
    }
    
    .workflow-phase {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 15px;
        margin: 1rem 0;
        text-align: center;
        font-weight: bold;
        box-shadow: 0 8px 25px rgba(0,0,0,0.15);
        transition: all 0.3s ease;
    }
    
    .workflow-phase:hover {
        transform: translateY(-2px);
        box-shadow: 0 12px 35px rgba(0,0,0,0.2);
    }
    
    .portfolio-card {
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        border: 2px solid #dee2e6;
        border-radius: 20px;
        padding: 2.5rem;
        margin: 1.5rem 0;
        box-shadow: 0 10px 30px rgba(0,0,0,0.1);
    }
    
    .metric-highlight {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 15px;
        text-align: center;
        margin: 0.5rem;
        box-shadow: 0 5px 15px rgba(0,0,0,0.1);
    }
    
    .workflow-diagram {
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        border-radius: 20px;
        padding: 2rem;
        margin: 2rem 0;
        box-shadow: 0 10px 30px rgba(0,0,0,0.1);
    }
    
    .agent-status-indicator {
        display: inline-block;
        width: 12px;
        height: 12px;
        border-radius: 50%;
        margin-right: 8px;
        animation: statusPulse 2s infinite;
    }
    
    .status-idle { background-color: #6c757d; }
    .status-analyzing { background-color: #ffc107; }
    .status-completed { background-color: #28a745; }
    .status-failed { background-color: #dc3545; }
    
    @keyframes statusPulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }
    
    .floating-action-button {
        position: fixed;
        bottom: 2rem;
        right: 2rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 50%;
        width: 60px;
        height: 60px;
        font-size: 24px;
        cursor: pointer;
        box-shadow: 0 8px 25px rgba(0,0,0,0.2);
        transition: all 0.3s ease;
        z-index: 1000;
    }
    
    .floating-action-button:hover {
        transform: scale(1.1);
        box-shadow: 0 12px 35px rgba(0,0,0,0.3);
    }
    
    .executive-summary {
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        border-left: 5px solid #667eea;
        padding: 2rem;
        border-radius: 15px;
        margin: 2rem 0;
        box-shadow: 0 8px 25px rgba(0,0,0,0.1);
    }
    
    .play-table {
        background: white;
        border-radius: 15px;
        overflow: hidden;
        box-shadow: 0 8px 25px rgba(0,0,0,0.1);
    }
    
    .play-table th {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        font-weight: 600;
        padding: 1rem;
    }
    
    .play-table td {
        padding: 1rem;
        border-bottom: 1px solid #e9ecef;
    }
    
    .play-table tr:hover {
        background-color: #f8f9fa;
    }
</style>
""", unsafe_allow_html=True)

def initialize_session_state():
    """Initialize session state variables"""
    if 'orchestrator' not in st.session_state:
        st.session_state.orchestrator = None
    if 'orchestration_started' not in st.session_state:
        st.session_state.orchestration_started = False
    if 'current_results' not in st.session_state:
        st.session_state.current_results = None
    if 'workflow_history' not in st.session_state:
        st.session_state.workflow_history = []

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
        progress_update_interval=0.3
    )
    
    orchestrator = AgentOrchestrator(config)
    
    def progress_callback(progress: float, message: str):
        st.session_state.workflow_history.append({
            'timestamp': datetime.now(),
            'progress': progress,
            'message': message
        })
    
    def status_callback(message: str):
        st.session_state.workflow_history.append({
            'timestamp': datetime.now(),
            'progress': None,
            'message': message
        })
    
    orchestrator.add_progress_callback(progress_callback)
    orchestrator.add_status_callback(status_callback)
    
    return orchestrator

def display_header():
    """Display the main header with stunning visuals"""
    st.markdown("""
    <div class="main-header">
        <h1>🤖 AI Agent Orchestration System</h1>
        <h3>Enterprise-Grade Multi-Agent Portfolio Optimization</h3>
        <p>Watch as our intelligent agents analyze your business and optimize your investment portfolio in real-time</p>
    </div>
    """, unsafe_allow_html=True)

def display_workflow_phases():
    """Display the workflow phases with visual indicators"""
    st.markdown("### 🚀 Workflow Execution Phases")
    
    phases = [
        ("🔍", "Agent Analysis", "5 specialized agents analyzing business areas"),
        ("⚡", "Portfolio Optimization", "AI-powered portfolio selection and scoring"),
        ("📊", "Results Presentation", "Executive summary and actionable insights")
    ]
    
    cols = st.columns(len(phases))
    for i, (icon, title, description) in enumerate(phases):
        with cols[i]:
            st.markdown(f"""
            <div class="workflow-phase">
                <h4>{icon} {title}</h4>
                <p>{description}</p>
            </div>
            """, unsafe_allow_html=True)

def display_workflow_diagram():
    """Display an interactive workflow diagram"""
    st.markdown("### 🔄 Agent Workflow Architecture")
    
    # Create a visual representation of the agent workflow
    workflow_data = {
        'Phase': ['Agent Analysis', 'Data Collection', 'Portfolio Optimization', 'Results Generation'],
        'Status': ['Active', 'Active', 'Active', 'Active'],
        'Duration': [15, 10, 20, 5]
    }
    
    df = pd.DataFrame(workflow_data)
    
    # Create a Gantt-style chart
    fig = go.Figure()
    
    colors = ['#667eea', '#764ba2', '#f093fb', '#51cf66']
    
    for i, phase in enumerate(df['Phase']):
        fig.add_trace(go.Bar(
            name=phase,
            y=[phase],
            x=[df['Duration'][i]],
            orientation='h',
            marker_color=colors[i],
            hovertemplate=f'<b>{phase}</b><br>Duration: {df["Duration"][i]}s<extra></extra>'
        ))
    
    fig.update_layout(
        title="Real-Time Agent Workflow Progress",
        xaxis_title="Duration (seconds)",
        yaxis_title="Workflow Phase",
        height=300,
        showlegend=False,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)'
    )
    
    st.plotly_chart(fig, use_container_width=True)

def display_agent_status(orchestrator):
    """Display real-time agent status with stunning visuals"""
    if not orchestrator:
        return
    
    st.markdown("### 🤖 Agent Status Dashboard")
    
    # Get agent status
    agent_status = orchestrator.get_status()
    agents = agent_status.get('agents', {})
    
    # Create columns for agent cards
    cols = st.columns(5)
    
    for i, (area, status) in enumerate(agents.items()):
        with cols[i]:
            # Determine card class based on status
            card_class = "agent-card"
            if status.get('status') == 'analyzing':
                card_class += " agent-working"
            elif status.get('status') == 'completed':
                card_class += " agent-completed"
            
            # Get status indicator
            status_indicator = f"<span class='agent-status-indicator status-{status.get('status', 'idle')}'></span>"
            
            st.markdown(f"""
            <div class="{card_class}">
                <h4>{status_indicator}{area.title()} Agent</h4>
                <p><strong>Status:</strong> {status.get('status', 'idle').title()}</p>
                <p><strong>Progress:</strong> {status.get('progress', 0):.1%}</p>
                <p><strong>Task:</strong> {status.get('current_task', 'Idle')}</p>
            </div>
            """, unsafe_allow_html=True)

def display_workflow_progress(orchestrator):
    """Display workflow progress with real-time updates"""
    if not orchestrator:
        return
    
    st.markdown("### 📈 Workflow Progress")
    
    # Get workflow status
    workflow_status = orchestrator.get_status()
    current_phase = workflow_status.get('current_phase', 'initialization')
    phase_progress = workflow_status.get('phase_progress', 0.0)
    total_progress = workflow_status.get('total_progress', 0.0)
    
    # Display current phase
    st.markdown(f"**Current Phase:** {current_phase.replace('_', ' ').title()}")
    
    # Phase progress bar
    st.markdown("**Phase Progress:**")
    st.progress(phase_progress)
    
    # Total progress bar
    st.markdown("**Overall Progress:**")
    st.progress(total_progress)
    
    # Display recent workflow history
    if st.session_state.workflow_history:
        st.markdown("**Recent Activity:**")
        recent_history = st.session_state.workflow_history[-10:]  # Last 10 entries
        
        for entry in recent_history:
            timestamp = entry['timestamp'].strftime("%H:%M:%S")
            if entry['progress'] is not None:
                st.markdown(f"🕐 **{timestamp}:** {entry['message']} ({entry['progress']:.1%})")
            else:
                st.markdown(f"🕐 **{timestamp}:** {entry['message']}")

def display_portfolio_results(portfolio):
    """Display portfolio results with interactive charts"""
    if not portfolio:
        return
    
    st.markdown("### 🎯 Portfolio Optimization Results")
    
    # Portfolio overview metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="metric-highlight">
            <h4>Total Plays</h4>
            <h2>{len(portfolio.selected_plays)}</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-highlight">
            <h4>Total Investment</h4>
            <h2>${portfolio.total_investment:,.0f}</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-highlight">
            <h4>Average ROI</h4>
            <h2>{portfolio.total_roi:.1f}%</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="metric-highlight">
            <h4>Risk Level</h4>
            <h2>{portfolio.risk_distribution.get('Medium', 0)}</h2>
        </div>
        """, unsafe_allow_html=True)
    
    # Portfolio plays table
    if portfolio.selected_plays:
        st.markdown("#### 📋 Selected Plays")
        
        # Prepare data for table
        plays_data = []
        for play in portfolio.selected_plays:
            plays_data.append({
                'Rank': play.rank,
                'Title': play.title,
                'Area': play.subject_area.value.title(),
                'Impact': f"{play.impact_score:.1f}",
                'Effort': f"{play.effort_score:.1f}",
                'ROI': f"{play.roi_score:.1f}",
                'Risk': f"{play.risk_score:.1f}",
                'Score': f"{play.score:.2f}",
                'Priority': play.get_priority_label()
            })
        
        df = pd.DataFrame(plays_data)
        st.markdown('<div class="play-table">', unsafe_allow_html=True)
        st.dataframe(df, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Create scoring distribution chart
        st.markdown("#### 📊 Scoring Distribution")
        
        fig = px.scatter(
            df, 
            x='Effort', 
            y='Impact', 
            size='Score',
            color='Priority',
            hover_data=['Title', 'ROI', 'Risk'],
            title="Play Impact vs Effort Analysis"
        )
        
        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            height=500
        )
        
        st.plotly_chart(fig, use_container_width=True)

def display_executive_summary(portfolio):
    """Display executive summary with actionable insights"""
    if not portfolio:
        return
    
    st.markdown("### 📋 Executive Summary")
    
    st.markdown(f"""
    <div class="executive-summary">
        <h4>🎯 Portfolio Overview</h4>
        <p>Our AI-powered portfolio optimization has identified <strong>{len(portfolio.selected_plays)} strategic initiatives</strong> 
        that will deliver maximum impact within your investment constraints.</p>
        
        <h4>💰 Investment Summary</h4>
        <p>Total investment: <strong>${portfolio.total_investment:,.0f}</strong> | 
        Expected ROI: <strong>{portfolio.total_roi:.1f}%</strong></p>
        
        <h4>🚀 Top Recommendations</h4>
        <ul>
    """, unsafe_allow_html=True)
    
    # Display top 3 plays
    top_plays = sorted(portfolio.selected_plays, key=lambda x: x.rank)[:3]
    for play in top_plays:
        st.markdown(f"<li><strong>{play.title}</strong> - {play.description[:100]}...</li>", unsafe_allow_html=True)
    
    st.markdown("""
        </ul>
        
        <h4>⏱️ Implementation Timeline</h4>
        <p>Recommended implementation sequence prioritizes high-impact, low-effort initiatives 
        to achieve quick wins while building momentum for larger strategic projects.</p>
    </div>
    """, unsafe_allow_html=True)

def display_control_panel():
    """Display the control panel for orchestrating agents"""
    st.sidebar.markdown("### 🎮 Control Panel")
    
    # Orchestration controls
    if st.sidebar.button("🚀 Start Agent Orchestration", type="primary", use_container_width=True):
        if not st.session_state.orchestrator:
            st.session_state.orchestrator = create_orchestrator()
        
        # Start orchestration in a separate thread
        if st.session_state.orchestrator.start_orchestration():
            st.session_state.orchestration_started = True
            st.rerun()
    
    if st.sidebar.button("⏹️ Stop Orchestration", use_container_width=True):
        if st.session_state.orchestrator:
            st.session_state.orchestrator.stop_orchestration()
            st.session_state.orchestration_started = False
            st.rerun()
    
    if st.sidebar.button("🔄 Reset System", use_container_width=True):
        st.session_state.orchestrator = None
        st.session_state.orchestration_started = False
        st.session_state.current_results = None
        st.session_state.workflow_history = []
        st.rerun()
    
    # Configuration options
    st.sidebar.markdown("### ⚙️ Configuration")
    
    budget = st.sidebar.slider("Budget Points", 5, 20, 8)
    enable_parallel = st.sidebar.checkbox("Enable Parallel Execution", value=True)
    
    # Display system status
    st.sidebar.markdown("### 📊 System Status")
    
    if st.session_state.orchestrator:
        status = st.session_state.orchestrator.get_status()
        st.sidebar.metric("Status", status.get('status', 'idle').title())
        st.sidebar.metric("Active Agents", status.get('active_agents', 0))
        st.sidebar.metric("Total Progress", f"{status.get('total_progress', 0):.1%}")
    else:
        st.sidebar.metric("Status", "Not Started")
        st.sidebar.metric("Active Agents", 0)
        st.sidebar.metric("Total Progress", "0%")

def main():
    """Main application function"""
    initialize_session_state()
    
    # Display header
    display_header()
    
    # Display workflow phases
    display_workflow_phases()
    
    # Display workflow diagram
    display_workflow_diagram()
    
    # Display control panel in sidebar
    display_control_panel()
    
    # Main content area
    if st.session_state.orchestrator and st.session_state.orchestration_started:
        # Display agent status
        display_agent_status(st.session_state.orchestrator)
        
        # Display workflow progress
        display_workflow_progress(st.session_state.orchestrator)
        
        # Check if orchestration is complete
        status = st.session_state.orchestrator.get_status()
        if status.get('status') == 'completed':
            # Get results
            results = st.session_state.orchestrator.get_results()
            if results and 'portfolio' in results:
                portfolio = results['portfolio']
                st.session_state.current_results = portfolio
                
                # Display results
                display_portfolio_results(portfolio)
                display_executive_summary(portfolio)
                
                # Success message
                st.success("🎉 Agent orchestration completed successfully! Portfolio optimization results are ready.")
    
    elif st.session_state.current_results:
        # Display previous results
        st.info("📊 Displaying previous orchestration results. Start a new orchestration to generate fresh insights.")
        display_portfolio_results(st.session_state.current_results)
        display_executive_summary(st.session_state.current_results)
    
    else:
        # Welcome message
        st.markdown("""
        <div class="portfolio-card">
            <h3>🎯 Welcome to the AI Agent Orchestration System</h3>
            <p>This system demonstrates enterprise-grade multi-agent coordination for portfolio optimization:</p>
            <ul>
                <li><strong>5 Specialized Agents:</strong> Network, Customer, Revenue, Usage, and Operations analysis</li>
                <li><strong>Real-time Coordination:</strong> Watch agents work in parallel with live progress updates</li>
                <li><strong>AI Portfolio Optimization:</strong> Intelligent scoring and selection algorithms</li>
                <li><strong>Executive Insights:</strong> Actionable recommendations with business context</li>
            </ul>
            <p><strong>Click "Start Agent Orchestration" in the sidebar to begin the demo!</strong></p>
        </div>
        """, unsafe_allow_html=True)
    
    # Floating action button for quick access
    st.markdown("""
    <button class="floating-action-button" onclick="window.scrollTo({top: 0, behavior: 'smooth'})">
        ⬆️
    </button>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
