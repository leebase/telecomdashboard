import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import altair as alt
# Explicit imports for better maintainability and IDE support
from kpi_components import (
    render_metric_card,
    render_line_chart,
    render_bar_chart, 
    render_area_chart,
    render_distribution,
    render_kpi_expander,
    get_kpi_tooltip_content,
    get_kpi_formula,
    get_kpi_business_impact
)
from generate_test_data import (
    generate_network_data,
    generate_customer_data,
    generate_revenue_data,
    generate_usage_data,
    generate_operations_data,
    generate_all_data
)
from improved_metric_cards import (
    create_metric_card,
    render_metric_grid,
    create_time_period_selector,
    get_network_metrics,
    get_customer_metrics,
    get_revenue_metrics,
    get_usage_metrics,
    get_operations_metrics
)
from theme_manager import get_current_theme_css, get_current_theme_header, get_current_theme_page_header
from theme_switcher import create_theme_switcher
from ai_insights_data_bundler import create_ai_insights_button, preview_llm_prompt
from ai_insights_ui import render_ai_insights_panel
from benchmark_manager import create_benchmark_tab
from agents.orchestrator import AgentOrchestrator, OrchestrationConfig
from agents.mock_intelligence import get_mock_intelligence_engine
from agents.integration_layer import get_integration_manager
from agents.backup_demo_mode import get_backup_demo
from models.play_models import SubjectArea, Play, Portfolio, WorkflowPhase
from security_manager import security_manager, get_security_headers, sanitize_streamlit_output
from database_connection import TelecomDatabase
from config_manager import get_config, get_ui_config, get_database_config
from health_check import health_checker, feature_flags
from logging_config import configure_app_logging, get_logger
import time

# Configure logging
configure_app_logging()
logger = get_logger('application')

# Import version information
from __version__ import APP_VERSION

# Load configuration
ui_config = get_ui_config()
logger.info("Application starting with configuration loaded")

# Page configuration
st.set_page_config(
    page_title=ui_config.page_title,
    page_icon=ui_config.page_icon,
    layout=ui_config.layout,
    initial_sidebar_state=ui_config.sidebar_state
)

# Apply security headers (if running in a web context)
try:
    # This will work in production deployments with web server integration
    headers = get_security_headers()
    for header, value in headers.items():
        st.session_state[f"security_header_{header}"] = value
except Exception:
    # Gracefully handle when not in web server context
    pass

# Apply current theme
st.markdown(get_current_theme_css(), unsafe_allow_html=True)

# Add print-specific CSS to show all tabs when printing
print_css = """
<style>
@media print {
    /* Hide the tab navigation completely */
    [data-testid="stTabs"] > div:first-child {
        display: none !important;
    }
    
    /* Force all tab content to be visible */
    [data-testid="stTabs"] > div:not(:first-child) {
        display: block !important;
        page-break-inside: avoid;
        margin-bottom: 30px;
    }
    
    /* Add page breaks between each tab content */
    [data-testid="stTabs"] > div:not(:first-child):not(:last-child) {
        page-break-after: always;
    }
    
    /* Hide sidebar when printing */
    [data-testid="stSidebar"] {
        display: none !important;
    }
    
    /* Ensure proper spacing */
    .main .block-container {
        padding: 0 !important;
        max-width: none !important;
    }
    
    /* Make sure all content is visible */
    * {
        visibility: visible !important;
    }
    
    /* Override any hidden elements */
    [style*="display: none"] {
        display: block !important;
    }
    
    /* Force all content to be visible in print mode */
    .print-mode * {
        display: block !important;
        visibility: visible !important;
    }
    
    /* Ensure charts are visible */
    .vega-embed {
        display: block !important;
        visibility: visible !important;
    }
    
    /* Force all containers to be visible */
    [data-testid="stVerticalBlock"] {
        display: block !important;
        visibility: visible !important;
    }
}
</style>
"""
st.markdown(print_css, unsafe_allow_html=True)

# Add theme header
st.markdown(get_current_theme_header(), unsafe_allow_html=True)

# Render functions for each section
def render_network_performance(network_data):
    # Header with AI Insights button
    # Header with AI Insights button
    col1, col2 = st.columns([5, 1])
    with col1:
        st.header("📡 Network Performance & Reliability", divider=False)
    with col2:
        st.markdown('<div style="height: 3.3rem; display: flex; align-items: flex-end; justify-content: flex-end;">', unsafe_allow_html=True)
        if st.button("🤖 AI Insights", key="ai_insights_btn_network", type="secondary", use_container_width=True):
            # When button is clicked, both show the panel and trigger analysis
            st.session_state.show_ai_insights_network = True
            st.session_state.trigger_analysis_network = True
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Time period selector
    time_period = create_time_period_selector("network")
    
    # Convert time period to days
    time_period_days = {
        "Last 30 Days": 30,
        "QTD": 90,
        "YTD": 365,
        "Last 12 Months": 365
    }.get(time_period, 30)
    
    # Show AI Insights in a dialog if button was clicked
    if st.session_state.get('show_ai_insights_network', False):
        with st.expander("🤖 AI Insights Analysis", expanded=True):
            render_ai_insights_panel("network", time_period_days)
            if st.button("✖️ Close AI Insights", key="close_ai_insights_network", type="secondary"):
                st.session_state.show_ai_insights_network = False
    
    # Render improved metric grid
    network_metrics = get_network_metrics(time_period_days)
    render_metric_grid(network_metrics, "network")
    
    # Charts section
    st.subheader("📈 Network Performance Trends")
    
    col1, col2 = st.columns(2)
    
    with col1:
        render_line_chart(network_data['latency_trend'], "Network Latency Trend (30 days)", "ms")
        render_line_chart(network_data['uptime_trend'], "Network Availability Trend", "%")
    
    with col2:
        render_bar_chart(network_data['bandwidth_by_region'], "Bandwidth Utilization by Region", "%")
        render_area_chart(network_data['packet_loss_trend'], "Packet Loss Rate Trend", "%")
    
    # KPI Expanders
    st.subheader("📘 Detailed KPI Information")
    render_kpi_expander("Network Availability", 
                       "Percentage of time the network is operational", 
                       lambda: render_line_chart(network_data['uptime_trend'], "Network Availability", "%"))
    
    render_kpi_expander("Dropped Call Rate (DCR)", 
                       "Percentage of calls terminated unexpectedly", 
                       lambda: render_line_chart(network_data['dcr_trend'], "Dropped Call Rate", "%"))

def render_customer_experience(customer_data, db):
    # Header with AI Insights button
    # Header with AI Insights button
    col1, col2 = st.columns([5, 1])
    with col1:
        st.header("😊 Customer Experience & Retention", divider=False)
    with col2:
        st.markdown('<div style="height: 3.3rem; display: flex; align-items: flex-end; justify-content: flex-end;">', unsafe_allow_html=True)
        if st.button("🤖 AI Insights", key="ai_insights_btn_customer", type="secondary", use_container_width=True):
            st.session_state.show_ai_insights_customer = True
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Time period selector
    time_period = create_time_period_selector("customer")
    
    # Convert time period to days
    time_period_days = {
        "Last 30 Days": 30,
        "QTD": 90,
        "YTD": 365,
        "Last 12 Months": 365
    }.get(time_period, 30)
    
    # Show AI Insights in a dialog if button was clicked
    if st.session_state.get('show_ai_insights_customer', False):
        with st.expander("🤖 AI Insights Analysis", expanded=True):
            render_ai_insights_panel("customer", time_period_days)
            if st.button("✖️ Close AI Insights", key="close_ai_insights_customer", type="secondary"):
                st.session_state.show_ai_insights_customer = False
    
    # Render improved metric grid
    customer_metrics = get_customer_metrics(time_period_days)
    render_metric_grid(customer_metrics, "customer")
    
    # Get real customer experience data for charts
    customer_trend_data = db.get_customer_trend_data(time_period_days)
    
    # Charts
    st.subheader("📈 Customer Experience Trends")
    
    col1, col2 = st.columns(2)
    
    with col1:
            if not customer_trend_data.empty:
                # Create satisfaction by region chart (aggregated by region)
                satisfaction_data = customer_trend_data.groupby('region_name')['satisfaction'].mean().reset_index()
                satisfaction_data['category'] = satisfaction_data['region_name']
                satisfaction_data['value'] = satisfaction_data['satisfaction']
                render_bar_chart(satisfaction_data, "Customer Satisfaction by Region", "Score")
                
                # Create NPS by region chart (aggregated by region)
                nps_data = customer_trend_data.groupby('region_name')['nps'].mean().reset_index()
                nps_data['category'] = nps_data['region_name']
                nps_data['value'] = nps_data['nps']
                render_bar_chart(nps_data, "Net Promoter Score by Region", "Score")
            else:
                st.warning("No customer trend data available")
        
    with col2:
            if not customer_trend_data.empty:
                # Create churn rate by region chart (aggregated by region)
                churn_data = customer_trend_data.groupby('region_name')['churn'].mean().reset_index()
                churn_data['category'] = churn_data['region_name']
                churn_data['value'] = churn_data['churn']
                render_bar_chart(churn_data, "Churn Rate by Region", "%")
                
                # Create support duration by region chart (aggregated by region)
                duration_data = customer_trend_data.groupby('region_name')['handling_time'].mean().reset_index()
                duration_data['category'] = duration_data['region_name']
                duration_data['value'] = duration_data['handling_time']
                render_bar_chart(duration_data, "Support Call Duration by Region", "Minutes")
            else:
                st.warning("No customer trend data available")
    
    # KPI Expanders
    st.subheader("📘 Detailed KPI Information")
    if not customer_trend_data.empty:
        render_kpi_expander("Customer Satisfaction", 
                           "Average satisfaction score from customer surveys", 
                           lambda: render_bar_chart(satisfaction_data, "Customer Satisfaction by Region", "Score"))
        
        render_kpi_expander("Net Promoter Score (NPS)", 
                           "Likelihood of customers recommending the service", 
                           lambda: render_bar_chart(nps_data, "NPS by Region", "Score"))
    else:
        st.warning("No customer trend data available for detailed analysis")

def render_revenue_monetization(revenue_data, db):
    # Header with AI Insights button
    # Header with AI Insights button
    col1, col2 = st.columns([5, 1])
    with col1:
        st.header("💰 Revenue & Monetization", divider=False)
    with col2:
        st.markdown('<div style="height: 3.3rem; display: flex; align-items: flex-end; justify-content: flex-end;">', unsafe_allow_html=True)
        if st.button("🤖 AI Insights", key="ai_insights_btn_revenue", type="secondary", use_container_width=True):
            st.session_state.show_ai_insights_revenue = True
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Time period selector
    time_period = create_time_period_selector("revenue")
    
    # Convert time period to days
    time_period_days = {
        "Last 30 Days": 30,
        "QTD": 90,
        "YTD": 365,
        "Last 12 Months": 365
    }.get(time_period, 30)
    
    # Show AI Insights in a dialog if button was clicked
    if st.session_state.get('show_ai_insights_revenue', False):
        with st.expander("🤖 AI Insights Analysis", expanded=True):
            render_ai_insights_panel("revenue", time_period_days)
            if st.button("✖️ Close AI Insights", key="close_ai_insights_revenue", type="secondary"):
                st.session_state.show_ai_insights_revenue = False
    
    # Render improved metric grid
    revenue_metrics = get_revenue_metrics(time_period_days)
    render_metric_grid(revenue_metrics, "revenue")
    
    # Get real revenue data for charts
    revenue_trend_data = db.get_revenue_trend_data(time_period_days)
    
    # Charts
    st.subheader("📈 Revenue Trends")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if not revenue_trend_data.empty:
            # Create ARPU by region chart (aggregated by region)
            arpu_data = revenue_trend_data.groupby('region_name')['avg_arpu'].mean().reset_index()
            arpu_data['category'] = arpu_data['region_name']
            arpu_data['value'] = arpu_data['avg_arpu']
            render_bar_chart(arpu_data, "ARPU by Region", "$")
            
            # Create subscribers by region chart (aggregated by region)
            subscribers_data = revenue_trend_data.groupby('region_name')['total_subscribers'].mean().reset_index()
            subscribers_data['category'] = subscribers_data['region_name']
            subscribers_data['value'] = subscribers_data['total_subscribers']
            render_bar_chart(subscribers_data, "Subscribers by Region", "Count")
        else:
            st.warning("No revenue trend data available")
    
    with col2:
        if not revenue_trend_data.empty:
            # Create EBITDA margin by region chart (aggregated by region)
            ebitda_data = revenue_trend_data.groupby('region_name')['avg_ebitda_margin'].mean().reset_index()
            ebitda_data['category'] = ebitda_data['region_name']
            ebitda_data['value'] = ebitda_data['avg_ebitda_margin']
            render_bar_chart(ebitda_data, "EBITDA Margin by Region", "%")
            
            # Create customer lifetime value by region chart (aggregated by region)
            clv_data = revenue_trend_data.groupby('region_name')['avg_clv'].mean().reset_index()
            clv_data['category'] = clv_data['region_name']
            clv_data['value'] = clv_data['avg_clv']
            render_bar_chart(clv_data, "Customer Lifetime Value by Region", "$")
        else:
            st.warning("No revenue trend data available")
    
    # KPI Expanders
    st.subheader("📘 Detailed KPI Information")
    if not revenue_trend_data.empty:
        render_kpi_expander("Average Revenue Per User (ARPU)", 
                           "Monthly revenue per active subscriber", 
                           lambda: render_bar_chart(arpu_data, "ARPU by Region", "$"))
        
        render_kpi_expander("EBITDA Margin", 
                           "Earnings before interest, taxes, depreciation, and amortization", 
                           lambda: render_bar_chart(ebitda_data, "EBITDA Margin by Region", "%"))
    else:
        st.warning("No revenue trend data available for detailed analysis")

def render_usage_adoption(usage_data, db):
    # Header with AI Insights button
    # Header with AI Insights button
    col1, col2 = st.columns([5, 1])
    with col1:
        st.header("📶 Usage & Service Adoption", divider=False)
    with col2:
        st.markdown('<div style="height: 3.3rem; display: flex; align-items: flex-end; justify-content: flex-end;">', unsafe_allow_html=True)
        if st.button("🤖 AI Insights", key="ai_insights_btn_usage", type="secondary", use_container_width=True):
            st.session_state.show_ai_insights_usage = True
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Time period selector
    time_period = create_time_period_selector("usage")
    
    # Convert time period to days
    time_period_days = {
        "Last 30 Days": 30,
        "QTD": 90,
        "YTD": 365,
        "Last 12 Months": 365
    }.get(time_period, 30)
    
    # Show AI Insights in a dialog if button was clicked
    if st.session_state.get('show_ai_insights_usage', False):
        with st.expander("🤖 AI Insights Analysis", expanded=True):
            render_ai_insights_panel("usage", time_period_days)
            if st.button("✖️ Close AI Insights", key="close_ai_insights_usage", type="secondary"):
                st.session_state.show_ai_insights_usage = False
    
    # Render improved metric grid
    usage_metrics = get_usage_metrics(time_period_days)
    render_metric_grid(usage_metrics, "usage")
    
    # Get real usage data for charts
    usage_trend_data = db.get_usage_trend_data(time_period_days)
    
    # Charts
    st.subheader("📈 Usage Trends")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if not usage_trend_data.empty:
            # Create data usage by region chart (aggregated by region)
            data_usage_data = usage_trend_data.groupby('region_name')['avg_data_usage'].mean().reset_index()
            data_usage_data['category'] = data_usage_data['region_name']
            data_usage_data['value'] = data_usage_data['avg_data_usage']
            render_bar_chart(data_usage_data, "Data Usage by Region", "GB")
            
            # Create 5G adoption by region chart (aggregated by region)
            five_g_data = usage_trend_data.groupby('region_name')['avg_five_g_adoption'].mean().reset_index()
            five_g_data['category'] = five_g_data['region_name']
            five_g_data['value'] = five_g_data['avg_five_g_adoption']
            render_bar_chart(five_g_data, "5G Adoption by Region", "%")
        else:
            st.warning("No usage trend data available")
    
    with col2:
        if not usage_trend_data.empty:
            # Create service penetration by region chart (aggregated by region)
            penetration_data = usage_trend_data.groupby('region_name')['avg_service_penetration'].mean().reset_index()
            penetration_data['category'] = penetration_data['region_name']
            penetration_data['value'] = penetration_data['avg_service_penetration']
            render_bar_chart(penetration_data, "Service Penetration by Region", "%")
            
            # Create app usage by region chart (aggregated by region)
            app_usage_data = usage_trend_data.groupby('region_name')['avg_app_usage'].mean().reset_index()
            app_usage_data['category'] = app_usage_data['region_name']
            app_usage_data['value'] = app_usage_data['avg_app_usage']
            render_bar_chart(app_usage_data, "App Usage by Region", "%")
        else:
            st.warning("No usage trend data available")
    
    # KPI Expanders
    st.subheader("📘 Detailed KPI Information")
    if not usage_trend_data.empty:
        render_kpi_expander("Data Usage per Subscriber", 
                           "Average GB/month per user", 
                           lambda: render_bar_chart(data_usage_data, "Data Usage by Region", "GB"))
        
        render_kpi_expander("5G Adoption Rate", 
                           "Percentage of subscribers using 5G services", 
                           lambda: render_bar_chart(five_g_data, "5G Adoption by Region", "%"))
    else:
        st.warning("No usage trend data available for detailed analysis")

def render_operational_efficiency(operations_data, db):
    # Header with AI Insights button
    # Header with AI Insights button
    col1, col2 = st.columns([5, 1])
    with col1:
        st.header("🛠️ Operational Efficiency", divider=False)
    with col2:
        st.markdown('<div style="height: 3.3rem; display: flex; align-items: flex-end; justify-content: flex-end;">', unsafe_allow_html=True)
        if st.button("🤖 AI Insights", key="ai_insights_btn_operations", type="secondary", use_container_width=True):
            st.session_state.show_ai_insights_operations = True
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Time period selector
    time_period = create_time_period_selector("operations")
    
    # Convert time period to days
    time_period_days = {
        "Last 30 Days": 30,
        "QTD": 90,
        "YTD": 365,
        "Last 12 Months": 365
    }.get(time_period, 30)
    
    # Show AI Insights in a dialog if button was clicked
    if st.session_state.get('show_ai_insights_operations', False):
        with st.expander("🤖 AI Insights Analysis", expanded=True):
            render_ai_insights_panel("operations", time_period_days)
            if st.button("✖️ Close AI Insights", key="close_ai_insights_operations", type="secondary"):
                st.session_state.show_ai_insights_operations = False
    
    # Render improved metric grid
    operations_metrics = get_operations_metrics(time_period_days)
    render_metric_grid(operations_metrics, "operations")
    
    # Get real operations data for charts
    operations_trend_data = db.get_operations_trend_data(time_period_days)
    
    # Charts
    st.subheader("📈 Operational Trends")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if not operations_trend_data.empty:
            # Create response time by region chart (aggregated by region)
            response_data = operations_trend_data.groupby('region_name')['avg_response_time'].mean().reset_index()
            response_data['category'] = response_data['region_name']
            response_data['value'] = response_data['avg_response_time']
            render_bar_chart(response_data, "Service Response Time by Region", "Hours")
            
            # Create compliance rate chart
            compliance_data = operations_trend_data[['region_name', 'avg_compliance_rate']].copy()
            compliance_data['category'] = compliance_data['region_name']
            compliance_data['value'] = compliance_data['avg_compliance_rate']
            render_bar_chart(compliance_data, "Compliance Rate by Region", "%")
        else:
            st.warning("No operations trend data available")
    
    with col2:
        if not operations_trend_data.empty:
            # Create efficiency score by region chart (aggregated by region)
            efficiency_data = operations_trend_data.groupby('region_name')['avg_efficiency_score'].mean().reset_index()
            efficiency_data['category'] = efficiency_data['region_name']
            efficiency_data['value'] = efficiency_data['avg_efficiency_score']
            render_bar_chart(efficiency_data, "Operational Efficiency by Region", "Score")
            
            # Create capex ratio by region chart (aggregated by region)
            capex_data = operations_trend_data.groupby('region_name')['avg_capex_ratio'].mean().reset_index()
            capex_data['category'] = capex_data['region_name']
            capex_data['value'] = capex_data['avg_capex_ratio']
            render_bar_chart(capex_data, "Capex to Revenue Ratio by Region", "%")
        else:
            st.warning("No operations trend data available")
    
    # KPI Expanders
    st.subheader("📘 Detailed KPI Information")
    if not operations_trend_data.empty:
        render_kpi_expander("Service Response Time", 
                           "Time from issue reported to first action taken", 
                           lambda: render_bar_chart(response_data, "Service Response Time by Region", "Hours"))
        
        render_kpi_expander("Regulatory Compliance Rate", 
                           "Percentage of audits or checks passed successfully", 
                           lambda: render_bar_chart(compliance_data, "Compliance Rate by Region", "%"))
    else:
        st.warning("No operations trend data available for detailed analysis")

def main():
    # Load configuration
    config = get_config()
    
    # Initialize database connection with config
    db = TelecomDatabase(config.database.path)
    
    # Initialize session state for tab management
    if 'main_tab' not in st.session_state:
        st.session_state.main_tab = "network"
    if 'management_tab' not in st.session_state:
        st.session_state.management_tab = None
    
    # Print mode disabled for now
    print_mode = False
    
    # Theme switcher in sidebar
    create_theme_switcher()
    
    # Print button in sidebar - Coming soon
    if st.sidebar.button("🖨️ Print All Tabs"):
        st.sidebar.info("🚧 Print functionality coming soon!")
    
    # Direct link to print mode for testing
    st.sidebar.markdown("---")
    st.sidebar.markdown("**Quick Print Links:**")
    if st.sidebar.button("📄 Open Print Mode"):
        st.sidebar.info("🚧 Print functionality coming soon!")
    

    
    # Page header with current theme styling
    st.markdown(get_current_theme_page_header(
        "Network Performance & Reliability",
        "Select a time period and explore KPIs across Network Performance, Customer Experience, Revenue & Monetization, Usage & Adoption, and Operational Efficiency."
    ), unsafe_allow_html=True)
    
    # Add compact spacing CSS
    st.markdown("""
    <style>
    .main .block-container {
        padding-top: 1rem !important;
        padding-bottom: 1rem !important;
    }
    .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
        margin-top: 0.5rem !important;
        margin-bottom: 0.5rem !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Generate test data
    network_data = generate_network_data()
    customer_data = generate_customer_data()
    revenue_data = generate_revenue_data()
    usage_data = generate_usage_data()
    operations_data = generate_operations_data()
    
    # Create a custom two-row tab system
    if not print_mode:
        # Initialize session state for tab management
        if 'main_tab' not in st.session_state:
            st.session_state.main_tab = "network"
        if 'management_tab' not in st.session_state:
            st.session_state.management_tab = None
        
        # Single row with all tabs and horizontal scrolling
        st.markdown("**📊 Dashboard Navigation:**")
        
        # Add custom CSS for compact tab styling
        st.markdown("""
        <style>
        .stButton > button {
            border-radius: 6px 6px 0px 0px !important;
            border-bottom: none !important;
            margin-bottom: 0px !important;
            padding: 6px 8px !important;
            font-weight: 500 !important;
            font-size: 13px !important;
            white-space: nowrap !important;
            min-width: 80px !important;
        }
        .stButton > button[data-baseweb="button"] {
            border-radius: 6px 6px 0px 0px !important;
        }
        .stMarkdown {
            margin-bottom: 0.5rem !important;
        }
        .stMarkdown p {
            margin-bottom: 0.25rem !important;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Create horizontal scrolling tab row with container
        with st.container():
            tab_col1, tab_col2, tab_col3, tab_col4, tab_col5, tab_col6, tab_col7 = st.columns(7)
            
            with tab_col1:
                if st.button("📡 Network", 
                            type="primary" if st.session_state.main_tab == "network" else "secondary"):
                    st.session_state.main_tab = "network"
                    st.session_state.management_tab = None
                    st.rerun()
            
            with tab_col2:
                if st.button("😊 Customer",
                            type="primary" if st.session_state.main_tab == "customer" else "secondary"):
                    st.session_state.main_tab = "customer"
                    st.session_state.management_tab = None
                    st.rerun()
            
            with tab_col3:
                if st.button("💰 Revenue",
                            type="primary" if st.session_state.main_tab == "revenue" else "secondary"):
                    st.session_state.main_tab = "revenue"
                    st.session_state.management_tab = None
                    st.rerun()
            
            with tab_col4:
                if st.button("📶 Usage",
                            type="primary" if st.session_state.main_tab == "usage" else "secondary"):
                    st.session_state.main_tab = "usage"
                    st.session_state.management_tab = None
                    st.rerun()
            
            with tab_col5:
                if st.button("🛠️ Operations",
                            type="primary" if st.session_state.main_tab == "operations" else "secondary"):
                    st.session_state.main_tab = "operations"
                    st.session_state.management_tab = None
                    st.rerun()
            
            with tab_col6:
                if st.button("🎯 Benchmark",
                            type="primary" if st.session_state.management_tab == "benchmark" else "secondary"):
                    st.session_state.management_tab = "benchmark"
                    st.rerun()
            
            with tab_col7:
                if st.button("🤖 AI Agents",
                            type="primary" if st.session_state.management_tab == "ai_agents" else "secondary"):
                    st.session_state.management_tab = "ai_agents"
                    st.rerun()
        
        # Render content based on selected tabs
        if st.session_state.management_tab == "benchmark":
            st.markdown("<div style='margin: 16px 0;'></div>", unsafe_allow_html=True)
            st.markdown("## 🎯 Benchmark Management")
            st.info("📊 Currently viewing: **Benchmark Management** - [Click any main tab above to return to KPI views]")
            create_benchmark_tab()
        elif st.session_state.management_tab == "ai_agents":
            st.markdown("<div style='margin: 16px 0;'></div>", unsafe_allow_html=True)
            st.markdown("## 🤖 AI Agent Orchestration")
            st.info("🤖 Currently viewing: **AI Agent Orchestration** - [Click any main tab above to return to KPI views]")
            render_ai_agent_orchestration()
        else:
            # Render main KPI content based on selected main tab
            if st.session_state.main_tab == "network":
                render_network_performance(network_data)
            elif st.session_state.main_tab == "customer":
                render_customer_experience(customer_data, db)
            elif st.session_state.main_tab == "revenue":
                render_revenue_monetization(revenue_data, db)
            elif st.session_state.main_tab == "usage":
                render_usage_adoption(usage_data, db)
            elif st.session_state.main_tab == "operations":
                render_operational_efficiency(operations_data, db)
    else:
        # In print mode, render all content directly with print-specific styling
        st.markdown('<div class="print-mode">', unsafe_allow_html=True)
        
        st.markdown("## 📡 Network Performance")
        render_network_performance(network_data)
        st.markdown("---")
        
        st.markdown("## 😊 Customer Experience")
        render_customer_experience(customer_data, db)
        st.markdown("---")
        
        st.markdown("## 💰 Revenue & Monetization")
        render_revenue_monetization(revenue_data, db)
        st.markdown("---")
        
        st.markdown("## 📶 Usage & Adoption")
        render_usage_adoption(usage_data, db)
        st.markdown("---")
        
        st.markdown("## 🛠️ Operational Efficiency")
        render_operational_efficiency(operations_data, db)
        st.markdown("---")
        
        st.markdown("## 🎯 Benchmark Management")
        create_benchmark_tab()
        st.markdown("---")
        
        st.markdown("## 🤖 AI Agent Orchestration")
        render_ai_agent_orchestration()
        
        st.markdown('</div>', unsafe_allow_html=True)

def render_ai_agent_orchestration():
    """Render the AI Agent Orchestration tab with integrated agent system"""
    
    st.markdown("""
    ## 🤖 AI Agent Orchestration System
    
    Our intelligent agent system analyzes your business data across 5 key areas and provides 
    optimized portfolio recommendations for maximum impact.
    """)
    
    # Initialize session state for agent system
    if 'agent_orchestrator' not in st.session_state:
        st.session_state.agent_orchestrator = None
        st.session_state.agent_results = None
        st.session_state.agent_status = 'idle'
        st.session_state.agent_progress = 0.0
        st.session_state.agent_message = "Ready to launch analysis"
        st.session_state.last_refresh = time.time()
        st.session_state.agent_start_time = None
        st.session_state.agent_phase = "Initialization"
        st.session_state.agent_activity = {
            "Acquisition": {"status": "waiting", "progress": 0.0, "message": "⏳ Waiting..."},
            "Retention": {"status": "waiting", "progress": 0.0, "message": "⏳ Waiting..."},
            "Network QoE": {"status": "waiting", "progress": 0.0, "message": "⏳ Waiting..."},
            "Support": {"status": "waiting", "progress": 0.0, "message": "⏳ Waiting..."},
            "Revenue": {"status": "waiting", "progress": 0.0, "message": "⏳ Waiting..."}
        }
        # Live event stream buffers
        st.session_state.agent_events = []  # list of {ts, kind, message}
        st.session_state._last_event_message = ""
        st.session_state._last_event_progress = 0.0
        st.session_state._prev_agent_states = {}
        st.session_state._seen_toasts = set()
        st.session_state._agent_last_percent = {}
    
    # Auto-refresh mechanism for real-time updates and completion polling
    # Initialize refresh counter if not exists
    if 'refresh_counter' not in st.session_state:
        st.session_state.refresh_counter = 0
    
    # If an orchestrator exists and status is running, poll its status and finalize when done
    if st.session_state.agent_status == 'running':
        orchestrator_instance = st.session_state.get('agent_orchestrator')
        if orchestrator_instance is not None:
            try:
                status_enum = getattr(orchestrator_instance, 'status', None)
                status_value = getattr(status_enum, 'value', None)
                if status_value == 'completed':
                    st.session_state.agent_status = 'completed'
                    st.session_state.agent_results = orchestrator_instance.get_results()
                    st.session_state.agent_message = 'Analysis complete - results ready'
                    st.session_state.agent_progress = 1.0
                    st.session_state.agent_phase = 'Completion'
                elif status_value == 'failed':
                    st.session_state.agent_status = 'failed'
                    st.session_state.agent_message = 'Agent orchestration failed'
            except Exception:
                pass

            # Robust live polling: update message/progress and agent statuses
            try:
                live = orchestrator_instance.get_live_update()
                if isinstance(live, dict):
                    # Update progress/message from live snapshot (monotonic progress)
                    live_progress = float(live.get('progress', 0.0) or 0.0)
                    if live_progress > st.session_state.get('agent_progress', 0.0):
                        st.session_state.agent_progress = live_progress
                        # Record progress event
                        st.session_state.agent_events.append({
                            "ts": time.time(),
                            "kind": "progress",
                            "message": f"Progress {int(live_progress*100)}%"
                        })
                        st.session_state._last_event_progress = live_progress
                    live_message = live.get('message')
                    if isinstance(live_message, str) and live_message:
                        st.session_state.agent_message = live_message
                        if live_message != st.session_state.get('_last_event_message', ""):
                            st.session_state.agent_events.append({
                                "ts": time.time(),
                                "kind": "status",
                                "message": live_message
                            })
                            st.session_state._last_event_message = live_message

                    # Update phase label from workflow phase
                    phase = str(live.get('workflow_phase', '') or '')
                    phase_map = {
                        'initialization': 'Initialization',
                        'agent_analysis': 'Agent Execution',
                        'portfolio_optimization': 'Optimization',
                        'results_presentation': 'Completion',
                        'completed': 'Completion'
                    }
                    if phase in phase_map:
                        st.session_state.agent_phase = phase_map[phase]

                # Reflect agent-specific status updates into the grid
                status_full = orchestrator_instance.get_status()
                agent_states = status_full.get('agent_status', {}) if isinstance(status_full, dict) else {}
                agent_progress_map = status_full.get('agent_progress', {}) if isinstance(status_full, dict) else {}
                if agent_states:
                    # Map orchestrator areas to UI labels
                    area_label_map = {
                        'network': 'Acquisition',
                        'customer': 'Retention',
                        'network_qoe': 'Network QoE',
                        'operations': 'Support',
                        'revenue': 'Revenue',
                        'usage': 'Usage'
                    }
                    # Emit events for state transitions
                    prev_states = st.session_state.get('_prev_agent_states', {}) or {}
                    for area_key, state in agent_states.items():
                        ui_label = area_label_map.get(area_key, area_key.title())
                        if ui_label not in st.session_state.agent_activity:
                            st.session_state.agent_activity[ui_label] = {"status": "waiting", "progress": 0.0, "message": "⏳ Waiting..."}
                        # Map agent status to UI status/message
                        if state == 'analyzing':
                            st.session_state.agent_activity[ui_label]["status"] = 'active'
                            st.session_state.agent_activity[ui_label]["message"] = '🔍 Running analysis...'
                            # Update per-agent progress if provided
                            if ui_label in st.session_state.agent_activity:
                                area_key_lookup = area_key
                                st.session_state.agent_activity[ui_label]["progress"] = float(agent_progress_map.get(area_key_lookup, 0.0) or 0.0)
                                # Emit event on integer percent change
                                try:
                                    pct = int(float(agent_progress_map.get(area_key_lookup, 0.0) or 0.0) * 100)
                                    last_pct = st.session_state._agent_last_percent.get(area_key_lookup, -1)
                                    if pct != last_pct:
                                        st.session_state.agent_events.append({
                                            "ts": time.time(),
                                            "kind": "agent",
                                            "message": f"{ui_label}: {pct}%"
                                        })
                                        st.session_state._agent_last_percent[area_key_lookup] = pct
                                except Exception:
                                    pass
                            if prev_states.get(area_key) != state:
                                st.session_state.agent_events.append({
                                    "ts": time.time(),
                                    "kind": "agent",
                                    "message": f"{ui_label}: analysis started"
                                })
                        elif state == 'completed':
                            st.session_state.agent_activity[ui_label]["status"] = 'completed'
                            st.session_state.agent_activity[ui_label]["progress"] = 1.0
                            st.session_state.agent_activity[ui_label]["message"] = '✅ Complete!'
                            if prev_states.get(area_key) != state:
                                st.session_state.agent_events.append({
                                    "ts": time.time(),
                                    "kind": "agent",
                                    "message": f"{ui_label}: completed"
                                })
                        elif state == 'failed':
                            st.session_state.agent_activity[ui_label]["status"] = 'failed'
                            st.session_state.agent_activity[ui_label]["message"] = '❌ Failed'
                            if prev_states.get(area_key) != state:
                                st.session_state.agent_events.append({
                                    "ts": time.time(),
                                    "kind": "agent",
                                    "message": f"{ui_label}: failed"
                                })
                        else:
                            st.session_state.agent_activity[ui_label]["status"] = 'waiting'
                            st.session_state.agent_activity[ui_label]["message"] = '⏳ Waiting...'
                    st.session_state._prev_agent_states = agent_states.copy()

            except Exception:
                pass
    
    # Force immediate UI refresh when status changes - moved outside the running check
    # This ensures the UI continues to refresh even after completion
    if st.session_state.agent_status in ['running', 'completed']:
        current_time = time.time()
        if current_time - st.session_state.last_refresh > 0.5:  # Refresh every 0.5 seconds for smoother updates
            st.session_state.last_refresh = current_time
            st.session_state.refresh_counter += 1
            st.rerun()
    
    # Control panel
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        if st.button("🚀 Launch Agent Analysis", type="primary"):
            st.session_state.agent_status = 'running'
            st.session_state.agent_results = None
            st.session_state.agent_progress = 0.0
            st.session_state.agent_message = "Initializing agents..."
            st.session_state.last_refresh = time.time()
            st.session_state.agent_start_time = time.time()
            st.session_state.agent_phase = "Initialization"
            # Reset live event buffers
            st.session_state.agent_events = []
            st.session_state._last_event_message = ""
            st.session_state._last_event_progress = 0.0
            st.session_state._prev_agent_states = {}
            st.session_state._seen_toasts = set()
            
            # Reset agent activity
            for area in st.session_state.agent_activity:
                st.session_state.agent_activity[area] = {
                    "status": "waiting", 
                    "progress": 0.0, 
                    "message": "⏳ Waiting..."
                }
            
            # Initialize orchestrator with proper configuration
            config = OrchestrationConfig(
                max_concurrent_agents=1,
                agent_timeout_seconds=15,
                optimization_iterations=3,
                portfolio_size_target=15,
                min_roi_threshold=7.0,
                max_risk_threshold=6.0,
                enable_parallel_execution=False,
                progress_update_interval=0.3,  # Faster updates for better UX
                enable_circuit_breaker=True,
                max_failures_before_fallback=3,
                fallback_timeout_seconds=60
            )
            
            orchestrator = AgentOrchestrator(config)
            # Note: We rely on UI polling (get_live_update/get_status) instead of background-thread callbacks

            st.session_state.agent_orchestrator = orchestrator
            
            # Start orchestration (non-blocking)
            if orchestrator.start_orchestration():
                st.success("✅ Agent orchestration started successfully!")
                st.session_state.agent_events.append({
                    "ts": time.time(),
                    "kind": "status",
                    "message": "Agent orchestration started"
                })
                
                # Ultra-fast completion guard: immediately poll for up to ~750ms to catch fast progress/completion
                try:
                    import time as _t
                    start_guard = _t.time()
                    initial_progress = st.session_state.get('agent_progress', 0.0) or 0.0
                    while (_t.time() - start_guard) < 0.75:
                        status_enum = getattr(orchestrator, 'status', None)
                        status_value = getattr(status_enum, 'value', None)
                        if status_value == 'completed':
                            # Transition to completed immediately
                            st.session_state.agent_status = 'completed'
                            st.session_state.agent_results = orchestrator.get_results()
                            st.session_state.agent_message = 'Analysis complete - results ready'
                            st.session_state.agent_progress = 1.0
                            st.session_state.agent_phase = 'Completion'
                            st.rerun()
                        
                        # Check for first meaningful live update
                        live = orchestrator.get_live_update()
                        if isinstance(live, dict):
                            live_progress = float(live.get('progress', 0.0) or 0.0)
                            live_message = live.get('message')
                            if live_progress > initial_progress or (isinstance(live_message, str) and live_message):
                                st.session_state.agent_progress = max(initial_progress, live_progress)
                                if isinstance(live_message, str) and live_message:
                                    st.session_state.agent_message = live_message
                                # Break once we have something to show beyond the initial state
                                break
                        _t.sleep(0.05)  # 50ms micro-wait
                except Exception:
                    pass

                st.rerun()
            else:
                st.error("❌ Failed to start agent orchestration")
                st.session_state.agent_status = 'failed'
    
    with col2:
        if st.button("🔄 Reset Analysis"):
            st.session_state.agent_orchestrator = None
            st.session_state.agent_results = None
            st.session_state.agent_status = 'idle'
            st.session_state.agent_progress = 0.0
            st.session_state.agent_message = "Ready to launch analysis"
            st.rerun()
    
    with col3:
        if st.button("📊 Demo Mode"):
            # Load backup demo data
            backup_demo = get_backup_demo()
            st.session_state.agent_results = backup_demo
            st.session_state.agent_status = 'demo'
            st.info("🎭 Demo mode activated with sample data")
    
    st.markdown("---")
    
    # Display agent status and progress
    if st.session_state.agent_status == 'running':
        st.info(f"🔄 **Status:** {st.session_state.agent_message}")
        
        # Safety timeout: if stuck in initialization too long, fail gracefully
        try:
            if st.session_state.get('agent_start_time'):
                elapsed_sec = time.time() - st.session_state.agent_start_time
                if elapsed_sec > 60 and st.session_state.get('agent_progress', 0.0) < 0.15:
                    st.session_state.agent_status = 'failed'
                    st.session_state.agent_message = 'Timeout during initialization. Please try again or use Demo Mode.'
        except Exception:
            pass
        
        # Progress bar
        st.progress(st.session_state.agent_progress)
        
        # Real-time status display
        status_container = st.container()
        with status_container:
            col1, col2 = st.columns([3, 1])
            with col1:
                st.info(f"🔄 **Current Status:** {st.session_state.agent_message}")
            with col2:
                # Show elapsed time
                if st.session_state.agent_start_time:
                    elapsed = int(time.time() - st.session_state.agent_start_time)
                    st.metric("⏱️ Elapsed Time", f"{elapsed}s")

        # Live event stream (append-only view)
        with st.expander("📜 Live event stream", expanded=True):
            # Keep only the latest 200 events to avoid unbounded growth
            if len(st.session_state.agent_events) > 200:
                st.session_state.agent_events = st.session_state.agent_events[-200:]
            for evt in st.session_state.agent_events[-50:]:
                # Format timestamp and message
                try:
                    ts = time.strftime('%H:%M:%S', time.localtime(evt.get('ts', time.time())))
                except Exception:
                    ts = "--:--:--"
                st.markdown(f"- {ts} — {evt.get('message','')}")

            # Toast key milestones once
            for evt in st.session_state.agent_events[-5:]:
                msg = evt.get('message', '')
                if not msg:
                    continue
                if any(k in msg.lower() for k in ["completed", "failed", "started"]):
                    key = f"{int(evt.get('ts',0))}:{msg}"
                    if key not in st.session_state._seen_toasts:
                        st.toast(msg)
                        st.session_state._seen_toasts.add(key)
        
        # Phase indicator
        st.info(f"📋 **Current Phase:** {st.session_state.agent_phase}")
        
        # Agent activity grid
        st.subheader("🤖 Agent Activity")
        
        # Create a grid layout for agent status
        cols = st.columns(3)
        for i, (area, activity) in enumerate(st.session_state.agent_activity.items()):
            col_idx = i % 3
            with cols[col_idx]:
                # Status indicator
                if activity["status"] == "waiting":
                    st.info(f"⏳ **{area.title()}**\n{activity['message']}")
                elif activity["status"] == "active":
                    st.success(f"🔄 **{area.title()}**\n{activity['message']}")
                    st.progress(activity["progress"])
                elif activity["status"] == "completed":
                    st.success(f"✅ **{area.title()}**\n{activity['message']}")
                    st.progress(1.0)
                else:
                    st.error(f"❌ **{area.title()}**\n{activity['message']}")
        
        # Note: Auto-refresh is handled by the main refresh mechanism above (lines 874-879)
        # This duplicate refresh logic has been removed to prevent conflicts

        # Optional debug details
        with st.expander("🔍 Debug details (orchestrator status)", expanded=False):
            orchestrator_instance = st.session_state.get('agent_orchestrator')
            if orchestrator_instance is not None:
                try:
                    st.json(orchestrator_instance.get_status())
                except Exception as e:
                    st.warning(f"Unable to fetch orchestrator status: {e}")

        # Activity log tail (helps when UI appears stuck)
        with st.expander("📜 Agent activity log (last 100 lines)", expanded=False):
            try:
                import os
                log_path = os.path.join('logs', 'agent_activity.log')
                if os.path.exists(log_path):
                    with open(log_path, 'r', encoding='utf-8') as lf:
                        lines = lf.readlines()
                        tail = ''.join(lines[-100:]) if lines else '(empty)'
                        st.code(tail)
                else:
                    st.info("Log file not found yet.")
            except Exception as e:
                st.warning(f"Unable to read activity log: {e}")
    
    elif st.session_state.agent_status == 'completed':
        st.success("✅ Agent analysis completed successfully!")
        # Final toast once
        if 'completed_toast_shown' not in st.session_state:
            st.toast("Analysis complete - results ready")
            st.session_state.completed_toast_shown = True
        
        # Display results (support both dict results and legacy object-like placeholders)
        results_obj = st.session_state.get('agent_results')
        if results_obj:
            st.markdown("## 📊 Analysis Results")
            
            # Handle dict-shaped results from orchestrator.get_results()
            if isinstance(results_obj, dict):
                optimized_portfolio = (results_obj.get('optimized_portfolio')
                                       if isinstance(results_obj.get('optimized_portfolio'), dict)
                                       else None)
                if optimized_portfolio:
                    selected_plays = optimized_portfolio.get('selected_plays', [])
                    metrics = results_obj.get('metrics', {})
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Selected Plays", len(selected_plays))
                    with col2:
                        st.metric("Total ROI", f"{optimized_portfolio.get('total_roi', 0):.2f}")
                    with col3:
                        st.metric("Avg Priority", f"{optimized_portfolio.get('average_priority', 0):.2f}")
                    
                    if selected_plays:
                        st.markdown("### 🎯 Selected Plays")
                        plays_data = []
                        for play in selected_plays:
                            plays_data.append({
                                'Title': play.get('title', 'N/A'),
                                'Area': play.get('subject_area', 'N/A'),
                                'Impact': play.get('impact_score', 0),
                                'Effort': play.get('effort_score', 0),
                                'ROI': play.get('roi_score', 0),
                                'Risk': play.get('risk_score', 0)
                            })
                        df = pd.DataFrame(plays_data)
                        st.dataframe(df, use_container_width=True)
                
                # Executive summary if present in portfolio
                if optimized_portfolio and optimized_portfolio.get('executive_summary'):
                    st.markdown("### 📋 Executive Summary")
                    st.info(optimized_portfolio.get('executive_summary'))
            else:
                # Legacy object path (no-op visualization placeholder)
                st.info("Results available.")
    
    elif st.session_state.agent_status == 'failed':
        st.error("❌ Agent analysis failed. Please check the system and try again.")
    
    elif st.session_state.agent_status == 'demo':
        st.info("🎭 Demo mode active - showing sample results")
        
        # Display demo results
        if st.session_state.agent_results:
            st.markdown("## 📊 Demo Results")
            
            # Portfolio summary
            if hasattr(st.session_state.agent_results, 'portfolio_pick'):
                portfolio = st.session_state.agent_results.portfolio_pick
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Effort Points", portfolio.get('total_effort', 'N/A'))
                with col2:
                    st.metric("Selected Plays", len(portfolio.get('selected', [])))
                with col3:
                    st.metric("Expected Impact", "High" if portfolio.get('total_effort', 0) > 5 else "Medium")
            
            # Prioritized plays table
            if hasattr(st.session_state.agent_results, 'prioritized_plays'):
                plays = st.session_state.agent_results.prioritized_plays
                
                if plays:
                    st.markdown("### 🎯 Prioritized Plays")
                    
                    # Convert to DataFrame for better display
                    plays_data = []
                    for play in plays:
                        plays_data.append({
                            'Rank': play.get('rank', 'N/A'),
                            'Title': play.get('title', 'N/A'),
                            'Area': play.get('area', 'N/A'),
                            'Score': f"{play.get('score', 0):.2f}",
                            'Effort': play.get('effort_points', 'N/A'),
                            'Impact': play.get('impact_score', 'N/A'),
                            'Confidence': f"{play.get('confidence', 0):.1%}"
                        })
                    
                    df = pd.DataFrame(plays_data)
                    st.dataframe(df, use_container_width=True)
            
            # Executive summary
            if hasattr(st.session_state.agent_results, 'exec_summary'):
                st.markdown("### 📋 Executive Summary")
                st.info(st.session_state.agent_results.exec_summary)
    
    else:
        st.info("🚀 Click 'Launch Agent Analysis' to begin the intelligent analysis process")
        
        # Show workflow overview
        st.markdown("### 🔄 Workflow Overview")
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


def handle_health_check():
    """Handle health check requests from URL parameters with proper API responses"""
    try:
        query_params = st.query_params
        
        if 'health' in query_params:
            health_type = query_params.get('health', 'simple')
            
            if health_type == 'simple':
                # Simple health check for load balancers
                health_data = health_checker.get_simple_health()
                
                # Set HTTP status code based on health status
                if health_data.get('status') == 'unhealthy':
                    st.error("Service Unavailable")
                
                # Return properly formatted JSON response
                st.json(health_data)
                st.stop()
                
            elif health_type == 'detailed':
                # Comprehensive health check
                health_data = health_checker.get_comprehensive_health()
                
                # Set HTTP status code based on health status
                if health_data.get('status') in ['unhealthy', 'degraded']:
                    st.error("Service Unavailable" if health_data.get('status') == 'unhealthy' else "Service Degraded")
                
                # Return properly formatted JSON response
                st.json(health_data)
                st.stop()
                
            elif health_type == 'features':
                # Feature flags status
                flags = feature_flags.get_all_flags()
                feature_response = {
                    "status": "healthy",
                    "feature_flags": flags,
                    "total_flags": len(flags),
                    "enabled_flags": sum(1 for flag in flags.values() if flag),
                    "timestamp": datetime.now().isoformat(),
                    "version": APP_VERSION
                }
                
                st.json(feature_response)
                st.stop()
                
            else:
                # Invalid health check type
                error_response = {
                    "status": "error",
                    "error": f"Invalid health check type: {health_type}",
                    "valid_types": ["simple", "detailed", "features"],
                    "timestamp": datetime.now().isoformat(),
                    "version": APP_VERSION
                }
                st.error("Bad Request")
                st.json(error_response)
                st.stop()
                
    except Exception as e:
        logger.error(f"Health check error: {e}")
        error_response = {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
            "version": APP_VERSION
        }
        st.error("Internal Server Error")
        st.json(error_response)
        st.stop()

if __name__ == "__main__":
    # Handle health check requests first
    handle_health_check()
    main() 