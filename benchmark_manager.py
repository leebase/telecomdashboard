import streamlit as st
import pandas as pd
from database_connection import db
from setup_benchmark_tables import export_benchmarks_to_csv, import_benchmarks_from_csv

def render_benchmark_manager():
    """Render the benchmark management interface"""
    st.header("🎯 Benchmark Management")
    st.write("Manage peer and industry benchmark targets for AI Insights")
    
    # Get current benchmarks
    try:
        benchmarks_df = db.get_benchmark_targets()
        
        if benchmarks_df.empty:
            st.warning("No benchmark data found. Please run setup_benchmark_tables.py first.")
            return
        
        # Display current benchmarks
        st.subheader("📊 Current Benchmark Targets")
        
        # Create editable dataframe
        edited_df = st.data_editor(
            benchmarks_df[['kpi_name', 'peer_avg', 'industry_avg', 'unit', 'direction', 'threshold_low', 'threshold_high']],
            num_rows="dynamic",
            width="stretch"
        )
        
        # Save changes button
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("💾 Save Changes", type="primary"):
                save_benchmark_changes(edited_df)
        
        with col2:
            if st.button("📤 Export to CSV"):
                export_benchmarks_to_csv()
                st.success("✅ Benchmarks exported to data/benchmark_targets.csv")
        
        with col3:
            if st.button("📥 Import from CSV"):
                import_benchmarks_from_csv()
                st.success("✅ Benchmarks imported from data/benchmark_targets.csv")
                st.rerun()
        
        # Show benchmark history
        st.subheader("📈 Benchmark Change History")
        history_df = db.get_benchmark_history(limit=20)
        
        if not history_df.empty:
            st.dataframe(
                history_df[['kpi_name', 'old_peer_avg', 'new_peer_avg', 'old_industry_avg', 'new_industry_avg', 'changed_by', 'changed_at']],
                width="stretch"
            )
        else:
            st.info("No benchmark changes recorded yet.")
        
        # Individual KPI editor
        st.subheader("✏️ Edit Individual KPI")
        kpi_names = benchmarks_df['kpi_name'].tolist()
        selected_kpi = st.selectbox("Select KPI to edit:", kpi_names)
        
        if selected_kpi:
            kpi_data = benchmarks_df[benchmarks_df['kpi_name'] == selected_kpi].iloc[0]
            
            col1, col2 = st.columns(2)
            
            with col1:
                new_peer = st.number_input(
                    "Peer Average:",
                    value=float(kpi_data['peer_avg']),
                    step=0.1,
                    format="%.2f"
                )
                
                new_industry = st.number_input(
                    "Industry Average:",
                    value=float(kpi_data['industry_avg']),
                    step=0.1,
                    format="%.2f"
                )
            
            with col2:
                new_threshold_low = st.number_input(
                    "Threshold Low:",
                    value=float(kpi_data['threshold_low']) if pd.notna(kpi_data['threshold_low']) else 0.0,
                    step=0.1,
                    format="%.2f"
                )
                
                new_threshold_high = st.number_input(
                    "Threshold High:",
                    value=float(kpi_data['threshold_high']) if pd.notna(kpi_data['threshold_high']) else 100.0,
                    step=0.1,
                    format="%.2f"
                )
            
            direction_options = ['higher_is_better', 'lower_is_better', 'neutral']
            new_direction = st.selectbox(
                "Direction:",
                options=direction_options,
                index=direction_options.index(kpi_data['direction'])
            )
            
            if st.button("💾 Update KPI", type="primary"):
                db.update_benchmark_target(
                    kpi_name=selected_kpi,
                    peer_avg=new_peer,
                    industry_avg=new_industry,
                    threshold_low=new_threshold_low,
                    threshold_high=new_threshold_high,
                    direction=new_direction,
                    changed_by="user"
                )
                st.success(f"✅ Updated {selected_kpi}")
                st.rerun()
    
    except Exception as e:
        st.error(f"Error loading benchmarks: {e}")
        st.info("Please ensure the benchmark tables are set up correctly.")

def save_benchmark_changes(edited_df):
    """Save changes from the edited dataframe"""
    try:
        for _, row in edited_df.iterrows():
            db.update_benchmark_target(
                kpi_name=row['kpi_name'],
                peer_avg=row['peer_avg'],
                industry_avg=row['industry_avg'],
                threshold_low=row['threshold_low'],
                threshold_high=row['threshold_high'],
                direction=row['direction'],
                changed_by="user"
            )
        st.success("✅ All benchmark changes saved successfully!")
    except Exception as e:
        st.error(f"Error saving changes: {e}")

def create_benchmark_tab():
    """Create a tab for benchmark management"""
    render_benchmark_manager()
