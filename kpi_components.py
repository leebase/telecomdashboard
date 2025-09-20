import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
from datetime import datetime, timedelta
from typing import Union, Optional

def render_metric_card(
    label: str, 
    value: Union[str, int, float], 
    delta: str, 
    metric_type: str = "default"
) -> None:
    """
    Render a metric card with value, delta, and optional tooltip.
    
    Creates a visually appealing metric card that displays a KPI value with
    trend indicator and optional tooltip for additional context.
    
    Args:
        label: The display label for the metric (e.g., "Network Uptime")
        value: The metric value - can be string, int, or float (e.g., "99.9%", 42.5)
        delta: Change indicator with sign (e.g., "+5.2%", "-1.1%", "0.0%")
        metric_type: Card styling type - "default", "warning", "success", "error"
        
    Returns:
        None: Renders directly to Streamlit interface
        
    Example:
        >>> render_metric_card("Network Uptime", "99.9%", "+0.1%", "success")
        >>> render_metric_card("Response Time", "45ms", "-2ms", "default")
        
    Note:
        Delta colors are automatically determined:
        - Green (▲) for positive changes starting with '+'
        - Red (▼) for negative changes starting with '-'
        - Blue (●) for neutral or unchanged values
    """
    # Determine delta color and icon
    if delta.startswith('+'):
        delta_color = "green"
        delta_icon = "▲"
    elif delta.startswith('-'):
        delta_color = "red"
        delta_icon = "▼"
    else:
        delta_color = "blue"
        delta_icon = "●"
    
    # Create tooltip content
    tooltip_content = get_kpi_tooltip_content(label)
    
    # Render the metric card with tooltip
    with st.container():
        col1, col2 = st.columns([4, 1])
        
        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <div style="font-size: 0.9rem; opacity: 0.8;">{label}</div>
                <div class="metric-value">{value}</div>
                <div class="metric-delta" style="color: {delta_color};">{delta_icon} {delta}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            if tooltip_content:
                st.markdown(f'<div title="{tooltip_content}" style="cursor: help; font-size: 1.2rem;">ℹ️</div>', unsafe_allow_html=True)

def render_kpi_tooltip(label, definition):
    """
    Render a tooltip for KPI definitions
    """
    st.markdown(f'<div title="{definition}" style="cursor: help; font-size: 1.2rem;">ℹ️ {label}</div>', unsafe_allow_html=True)

def render_info_icon(kpi_name, detailed_help):
    """
    Render an info icon with detailed help popup
    """
    st.markdown(f'<div title="{detailed_help}" style="cursor: help; font-size: 1.2rem;">ℹ️ {kpi_name}</div>', unsafe_allow_html=True)

def render_line_chart(
    df: Optional[pd.DataFrame], 
    title: str, 
    y_label: str = "Value"
) -> None:
    """
    Render a theme-appropriate line chart using Altair.
    
    Creates an interactive line chart that automatically adapts to the current theme
    and displays time-series data with proper formatting and styling.
    
    Args:
        df: DataFrame containing the data to plot. Must have 'date' and 'value' columns.
            Can be None or empty, in which case a warning is displayed.
        title: Chart title displayed above the visualization
        y_label: Y-axis label describing the metric units (default: "Value")
        
    Returns:
        None: Renders chart directly to Streamlit interface
        
    Example:
        >>> data = pd.DataFrame({
        ...     'date': pd.date_range('2023-01-01', periods=30),
        ...     'value': np.random.normal(100, 10, 30)
        ... })
        >>> render_line_chart(data, "Daily Metrics", "Count")
        
    Note:
        Chart automatically includes:
        - Interactive tooltips
        - Theme-appropriate colors
        - Responsive sizing
        - Proper date formatting
    """
    if df is None or df.empty:
        st.warning(f"No data available for {title}")
        return
    
    # Get current theme to determine colors
    try:
        from theme_manager import get_current_theme
        current_theme = get_current_theme()
    except:
        current_theme = "cognizant"  # Default fallback
    
    # Set color based on theme
    if current_theme == "verizon":
        stroke_color = '#cd040b'  # Verizon red
    else:
        stroke_color = 'cyan'  # Cognizant cyan
    
    chart = alt.Chart(df).mark_line(
        point=True,
        strokeWidth=3,
        stroke=stroke_color
    ).encode(
        x=alt.X('date:T', title='Date', axis=alt.Axis(
            titleColor='#a7b3c7',
            labelColor='#a7b3c7',
            gridColor='rgba(167, 179, 199, 0.2)'
        )),
        y=alt.Y('value:Q', title=y_label, axis=alt.Axis(
            titleColor='#a7b3c7',
            labelColor='#a7b3c7',
            gridColor='rgba(167, 179, 199, 0.2)'
        ))
    ).properties(
        title=alt.TitleParams(
            text=title,
            color='#e6effa',
            fontSize=16,
            fontWeight='bold'
        ),
        width=400,
        height=250
    ).configure_axis(
        gridOpacity=0.3
    ).configure_view(
        strokeOpacity=0,
        stroke='#13223d'
    ).configure_legend(
        titleColor='#a7b3c7',
        labelColor='#a7b3c7'
    ).configure(
        background='#13223d'
    )
    
    # Wrap in Cognizant-style container
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    st.altair_chart(chart, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

def render_bar_chart(df, title, y_label="Value", horizontal=False):
    """
    Render a theme-appropriate bar chart using Altair
    """
    # Altair requires text-based titles; coerce and fall back when metadata omits them
    if isinstance(title, str):
        title_text = title.strip() or "Bar Chart"
    elif title is None:
        title_text = "Bar Chart"
    else:
        title_text = str(title)

    if isinstance(y_label, str):
        y_axis_title = y_label.strip() or "Value"
    elif y_label is None:
        y_axis_title = "Value"
    else:
        y_axis_title = str(y_label)

    if df is None or df.empty:
        st.warning(f"No data available for {title_text}")
        return

    # Get current theme to determine colors
    try:
        from theme_manager import get_current_theme
        current_theme = get_current_theme()
    except:
        current_theme = "cognizant"  # Default fallback
    
    # Set color based on theme
    if current_theme == "verizon":
        bar_color = '#cd040b'  # Verizon red
    else:
        bar_color = 'cyan'  # Cognizant cyan
    
    if horizontal:
        # Horizontal bar chart for "by region" charts
        chart = alt.Chart(df).mark_bar(
            cornerRadiusTopLeft=3,
            cornerRadiusTopRight=3,
            color=bar_color
        ).encode(
            x=alt.X('value:Q', title=y_axis_title, axis=alt.Axis(
                titleColor='#a7b3c7',
                labelColor='#a7b3c7',
                gridColor='rgba(167, 179, 199, 0.2)'
            )),
            y=alt.Y('category:N', title='Region', sort='-x', axis=alt.Axis(
                titleColor='#a7b3c7',
                labelColor='#a7b3c7'
            ))
        ).properties(
            title=alt.TitleParams(
                text=title_text,
                color='#e6effa',
                fontSize=16,
                fontWeight='bold'
            ),
            width=400,
            height=250
        ).configure_axis(
            gridOpacity=0.3
        ).configure_view(
            strokeOpacity=0,
            stroke='#13223d'
        ).configure(
            background='#13223d'
        )
    else:
        # Vertical bar chart for regular charts
        chart = alt.Chart(df).mark_bar(
            cornerRadiusTopLeft=3,
            cornerRadiusTopRight=3,
            color=bar_color
        ).encode(
            x=alt.X('category:N', title='Category', axis=alt.Axis(
                titleColor='#a7b3c7',
                labelColor='#a7b3c7'
            )),
            y=alt.Y('value:Q', title=y_axis_title, axis=alt.Axis(
                titleColor='#a7b3c7',
                labelColor='#a7b3c7',
                gridColor='rgba(167, 179, 199, 0.2)'
            ))
        ).properties(
            title=alt.TitleParams(
                text=title_text,
                color='#e6effa',
                fontSize=16,
                fontWeight='bold'
            ),
            width=400,
            height=250
        ).configure_axis(
            gridOpacity=0.3
        ).configure_view(
            strokeOpacity=0,
            stroke='#13223d'
        ).configure(
            background='#13223d'
        )
    
    # Wrap in Cognizant-style container
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    st.altair_chart(chart, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

def render_area_chart(df, title, y_label="Value"):
    """
    Render a theme-appropriate area chart using Altair
    """
    if isinstance(title, str):
        title_text = title.strip() or "Area Chart"
    elif title is None:
        title_text = "Area Chart"
    else:
        title_text = str(title)

    if isinstance(y_label, str):
        y_axis_title = y_label.strip() or "Value"
    elif y_label is None:
        y_axis_title = "Value"
    else:
        y_axis_title = str(y_label)

    if df is None or df.empty:
        st.warning(f"No data available for {title_text}")
        return
    
    # Get current theme to determine colors
    try:
        from theme_manager import get_current_theme
        current_theme = get_current_theme()
    except:
        current_theme = "cognizant"  # Default fallback
    
    # Set color based on theme
    if current_theme == "verizon":
        area_color = '#cd040b'  # Verizon red
    else:
        area_color = 'cyan'  # Cognizant cyan
    
    chart = alt.Chart(df).mark_area(
        opacity=0.6,
        color=area_color
    ).encode(
        x=alt.X('date:T', title='Date', axis=alt.Axis(
            titleColor='#a7b3c7',
            labelColor='#a7b3c7',
            gridColor='rgba(167, 179, 199, 0.2)'
        )),
        y=alt.Y('value:Q', title=y_axis_title, axis=alt.Axis(
            titleColor='#a7b3c7',
            labelColor='#a7b3c7',
            gridColor='rgba(167, 179, 199, 0.2)'
        ))
    ).properties(
        title=alt.TitleParams(
            text=title_text,
            color='#e6effa',
            fontSize=16,
            fontWeight='bold'
        ),
        width=400,
        height=250
    ).configure_axis(
        gridOpacity=0.3
    ).configure_view(
        strokeOpacity=0,
        stroke='#13223d'
    ).configure(
        background='#13223d'
    )
    
    # Wrap in Cognizant-style container
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    st.altair_chart(chart, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

def render_distribution(df, title, x_label="Value"):
    """
    Render a theme-appropriate histogram/distribution chart using Altair
    """
    if df is None or df.empty:
        st.warning(f"No data available for {title}")
        return
    
    # Get current theme to determine colors
    try:
        from theme_manager import get_current_theme
        current_theme = get_current_theme()
    except:
        current_theme = "cognizant"  # Default fallback
    
    # Set color based on theme
    if current_theme == "verizon":
        dist_color = '#cd040b'  # Verizon red
    else:
        dist_color = 'cyan'  # Cognizant cyan
    
    chart = alt.Chart(df).mark_bar(
        opacity=0.7,
        color=dist_color
    ).encode(
        x=alt.X('value:Q', bin=alt.Bin(maxbins=20), title=x_label, axis=alt.Axis(
            titleColor='#a7b3c7',
            labelColor='#a7b3c7',
            gridColor='rgba(167, 179, 199, 0.2)'
        )),
        y=alt.Y('count():Q', title='Frequency', axis=alt.Axis(
            titleColor='#a7b3c7',
            labelColor='#a7b3c7',
            gridColor='rgba(167, 179, 199, 0.2)'
        ))
    ).properties(
        title=alt.TitleParams(
            text=title,
            color='#e6effa',
            fontSize=16,
            fontWeight='bold'
        ),
        width=400,
        height=250
    ).configure_axis(
        gridOpacity=0.3
    ).configure_view(
        strokeOpacity=0,
        stroke='#13223d'
    ).configure(
        background='#13223d'
    )
    
    # Wrap in Cognizant-style container
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    st.altair_chart(chart, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

def render_kpi_expander(name, definition, chart_fn):
    """
    Render an expandable KPI section with definition and chart
    """
    with st.expander(f"📊 {name}"):
        st.markdown(f"**Definition:** {definition}")
        
        # Add formula if available
        formula = get_kpi_formula(name)
        if formula:
            st.markdown(f"**Formula:** {formula}")
        
        # Add business impact
        impact = get_kpi_business_impact(name)
        if impact:
            st.markdown(f"**Business Impact:** {impact}")
        
        # Render the chart
        chart_fn()

def get_kpi_tooltip_content(kpi_name: str) -> str:
    """
    Get tooltip content for KPIs
    """
    tooltips = {
        "uptime": "Percentage of time the network is operational. Critical for SLA compliance.",
        "latency": "Average round-trip time for data packets (ms). Critical for real-time applications.",
        "bandwidth": "Percentage of total network capacity being used. Indicates congestion risk.",
        "dcr": "Dropped Call Rate - Percentage of calls terminated unexpectedly.",
        "packet_loss": "Percentage of packets lost in transmission. Impacts streaming quality.",
        "mttr": "Mean Time to Repair - Average time to resolve network outages.",
        "csat": "Customer Satisfaction - Post-interaction score (1-5 scale).",
        "nps": "Net Promoter Score - % Promoters - % Detractors (0-10 scale).",
        "churn": "Customer Churn Rate - Percentage of customers who cancel service.",
        "aht": "Average Handling Time - Average duration of customer support interactions.",
        "fcr": "First Contact Resolution - Percentage of issues resolved in one interaction.",
        "clv": "Customer Lifetime Value - Total expected profit per user over time.",
        "arpu": "Average Revenue Per User - Average monthly revenue per subscriber.",
        "cac": "Customer Acquisition Cost - Average cost to acquire a new customer.",
        "growth": "Subscriber Growth Rate - Net percentage increase in subscriber base.",
        "ebitda": "EBITDA Margin - Profitability before non-cash expenses.",
        "mrr": "Monthly Recurring Revenue - Predictable monthly revenue stream.",
        "data_usage": "Data Usage per Subscriber - Average GB/month per user.",
        "throughput": "Average Data Throughput - Average data speed (Mbps).",
        "adoption": "Feature Adoption Rate - Percentage of users adopting new features.",
        "5g_adoption": "5G Adoption Rate - Percentage of subscribers using 5G services.",
        "active_subs": "Active Subscribers - Number of currently active subscribers.",
        "peak_time": "Peak Usage Time - Time period with highest network usage.",
        "response_time": "Service Response Time - Time from issue reported to first action.",
        "compliance": "Regulatory Compliance Rate - Percentage of audits passed successfully.",
        "capex_ratio": "Capex to Revenue Ratio - Percentage of revenue reinvested in infrastructure.",
        "efficiency": "Network Efficiency Score - Overall operational efficiency metric.",
        "resolution": "Support Ticket Resolution - Percentage of support tickets resolved successfully.",
        "system_uptime": "System Uptime - Overall system availability percentage."
    }
    
    return tooltips.get(kpi_name.lower(), f"Quick definition for {kpi_name}")

def get_kpi_formula(kpi_name):
    """
    Get formula for KPIs
    """
    formulas = {
        "Network Availability": "Uptime = (Total Time - Downtime) / Total Time × 100%",
        "Latency": "Average RTT = Σ(Round Trip Times) / Number of Measurements",
        "Dropped Call Rate": "DCR = (Dropped Calls / Total Calls) × 100%",
        "Customer Satisfaction": "CSAT = (Satisfied Responses / Total Responses) × 100%",
        "Net Promoter Score": "NPS = % Promoters - % Detractors",
        "Customer Churn Rate": "Churn Rate = (Churned Customers / Total Customers) × 100%",
        "Average Revenue Per User": "ARPU = Total Revenue / Number of Subscribers",
        "Customer Lifetime Value": "CLV = ARPU × Average Customer Lifespan",
        "Customer Acquisition Cost": "CAC = Total Acquisition Costs / Number of New Customers",
        "EBITDA Margin": "EBITDA Margin = EBITDA / Revenue × 100%",
        "Data Usage per Subscriber": "Average Usage = Total Data Usage / Number of Subscribers",
        "5G Adoption Rate": "5G Adoption = (5G Subscribers / Total Subscribers) × 100%"
    }
    
    return formulas.get(kpi_name, "")

def get_kpi_business_impact(kpi_name):
    """
    Get business impact description for KPIs
    """
    impacts = {
        "Network Availability": "Directly affects customer satisfaction and SLA compliance. Higher uptime reduces churn.",
        "Latency": "Critical for real-time applications like VoIP and gaming. Lower latency improves user experience.",
        "Dropped Call Rate": "Measures call stability and voice quality. Lower DCR improves customer satisfaction.",
        "Customer Satisfaction": "Short-term measure of service quality. Higher CSAT correlates with lower churn.",
        "Net Promoter Score": "Predicts customer loyalty and referral potential. Higher NPS drives organic growth.",
        "Customer Churn Rate": "Indicates dissatisfaction and financial risk. Lower churn improves profitability.",
        "Average Revenue Per User": "Core monetization metric. Higher ARPU increases profitability.",
        "Customer Lifetime Value": "Guides acquisition and retention spend. Higher CLV justifies higher CAC.",
        "Customer Acquisition Cost": "Measures marketing efficiency. Lower CAC improves profitability.",
        "EBITDA Margin": "Key financial health metric watched by investors. Higher margin indicates efficiency.",
        "Data Usage per Subscriber": "Helps with pricing strategy and capacity planning. Higher usage may indicate premium plan potential.",
        "5G Adoption Rate": "Tracks modernization and premium plan uptake. Higher adoption indicates competitive advantage."
    }
    
    return impacts.get(kpi_name, "") 
