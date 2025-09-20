from pathlib import Path
import sys

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import altair as alt

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
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
from security_manager import security_manager, get_security_headers, sanitize_streamlit_output
from database_connection import TelecomDatabase
from config_manager import get_config, get_ui_config, get_database_config
from health_check import health_checker, feature_flags
from logging_config import configure_app_logging, get_logger
from ui.runtime_switch import is_metadata_enabled

# Configure logging
configure_app_logging()
logger = get_logger('application')

if is_metadata_enabled():
    from ui.metadata_runtime_app import render_metadata_dashboard

    logger.info("USE_METADATA flag enabled; rendering metadata runtime")
    render_metadata_dashboard()
    st.stop()


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
    
    # Generate test data
    network_data = generate_network_data()
    customer_data = generate_customer_data()
    revenue_data = generate_revenue_data()
    usage_data = generate_usage_data()
    operations_data = generate_operations_data()
    
    # Create tabs for each KPI pillar
    if not print_mode:
        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
            "📡 Network Performance", 
            "😊 Customer Experience", 
            "💰 Revenue & Monetization", 
            "📶 Usage & Adoption", 
            "🛠️ Operational Efficiency",
            "🎯 Benchmark Management"
        ])
        
        # Tab 1: Network Performance
        with tab1:
            render_network_performance(network_data)
        
        # Tab 2: Customer Experience
        with tab2:
            render_customer_experience(customer_data, db)
        
        # Tab 3: Revenue & Monetization
        with tab3:
            render_revenue_monetization(revenue_data, db)
        
        # Tab 4: Usage & Adoption
        with tab4:
            render_usage_adoption(usage_data, db)
        
        # Tab 5: Operational Efficiency
        with tab5:
            render_operational_efficiency(operations_data, db)
        
        # Tab 6: Benchmark Management
        with tab6:
            create_benchmark_tab()
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
        
        st.markdown('</div>', unsafe_allow_html=True)

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
