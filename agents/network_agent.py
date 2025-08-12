"""
NetworkAgent: Real network analysis agent using database-backed metrics

Generates actionable plays based on recent network KPIs (availability, latency,
packet loss, bandwidth utilization, DCR, MTTR). Progress is updated incrementally
to provide real-time UI feedback during execution.
"""

from typing import List, Dict
import time

from models.play_models import (
    Play,
    PlayCategory,
    SubjectArea,
)
from agents.base_agent import SubjectAreaAgent
from database_connection import db


class NetworkAgent(SubjectAreaAgent):
    """Specialized agent that analyzes network KPIs and produces real plays."""

    def __init__(self):
        super().__init__(subject_area=SubjectArea.NETWORK, agent_id="network_agent", name="Network Analysis Agent")
        # Tune for production later
        self.max_plays_per_area = 6

    def _execute_agent_logic(self, task: str):
        """Pull real KPI data and generate plays with incremental progress."""
        # Step 1: Fetch summary metrics
        self._update_progress(0.05, "Fetching network metrics (30d)")
        summary = db.get_network_metrics(days=30)
        time.sleep(0.02)
        self._update_progress(0.10, "Fetching latency/availability trends")

        # Step 2: Trends and regional data
        latency_trend = db.get_trend_data("avg_latency_ms", days=30)
        availability_trend = db.get_trend_data("availability_percent", days=30)
        time.sleep(0.02)
        self._update_progress(0.20, "Fetching regional bandwidth/packet loss")
        bandwidth_by_region = db.get_region_data("avg_bandwidth_utilization_percent", days=30)
        packet_loss_by_region = db.get_region_data("avg_packet_loss_percent", days=30)
        time.sleep(0.02)
        self._update_progress(0.30, "Analyzing hotspots and trends")

        plays: List[Play] = []
        try:
            # Defensive conversions
            avg_availability = float(summary.get("avg_availability", 99.9)) if summary is not None else 99.9
            avg_latency = float(summary.get("avg_latency", 45.0)) if summary is not None else 45.0
            avg_packet_loss = float(summary.get("avg_packet_loss", 0.1)) if summary is not None else 0.1
            avg_bandwidth_util = float(summary.get("avg_bandwidth_util", 70.0)) if summary is not None else 70.0
            avg_mttr = float(summary.get("avg_mttr", 2.5)) if summary is not None else 2.5
            avg_dcr = float(summary.get("avg_dropped_call_rate", 1.0)) if summary is not None else 1.0

            # Step 3: Build candidate plays from high-level metrics
            # Availability improvement
            if avg_availability < 99.9:
                plays.append(Play(
                    title="Increase Network Availability",
                    description="Targeted reliability improvements to push availability above 99.9% with redundancy and proactive maintenance.",
                    category=PlayCategory.OPERATIONAL_EFFICIENCY,
                    subject_area=SubjectArea.NETWORK,
                    impact_score=8.5,
                    effort_score=6.0,
                    roi_score=7.8,
                    risk_score=3.0,
                    estimated_cost=850000.0,
                    estimated_duration_months=9,
                    tags=["availability", "reliability", "redundancy"]
                ))

            # Latency reduction
            if avg_latency > 50:
                plays.append(Play(
                    title="Latency Reduction Initiative",
                    description="Optimize routing, deploy edge nodes, and tune QoS to reduce average latency below 50ms.",
                    category=PlayCategory.PERFORMANCE_OPTIMIZATION,
                    subject_area=SubjectArea.NETWORK,
                    impact_score=8.0,
                    effort_score=7.0,
                    roi_score=7.5,
                    risk_score=3.8,
                    estimated_cost=1200000.0,
                    estimated_duration_months=10,
                    tags=["latency", "qos", "edge"]
                ))

            # MTTR improvement
            if avg_mttr > 2.0:
                plays.append(Play(
                    title="Reduce MTTR via Automation",
                    description="Automate triage and remediation to bring MTTR under 2 hours across regions.",
                    category=PlayCategory.OPERATIONAL_EFFICIENCY,
                    subject_area=SubjectArea.NETWORK,
                    impact_score=7.5,
                    effort_score=5.5,
                    roi_score=7.8,
                    risk_score=2.5,
                    estimated_cost=600000.0,
                    estimated_duration_months=6,
                    tags=["mttr", "automation", "runbooks"]
                ))

            # DCR improvement
            if avg_dcr > 1.2:
                plays.append(Play(
                    title="Dropped Call Rate Mitigation",
                    description="Target radio optimizations and backhaul upgrades to cut DCR below 1%.",
                    category=PlayCategory.PERFORMANCE_OPTIMIZATION,
                    subject_area=SubjectArea.NETWORK,
                    impact_score=7.8,
                    effort_score=6.5,
                    roi_score=7.2,
                    risk_score=3.2,
                    estimated_cost=950000.0,
                    estimated_duration_months=8,
                    tags=["dcr", "radio", "backhaul"]
                ))

            self._update_progress(0.45, "Analyzing regional hotspots")
            time.sleep(0.02)

            # Step 4: Regional hotspots for bandwidth utilization
            try:
                if bandwidth_by_region is not None and not bandwidth_by_region.empty:
                    top_bw = bandwidth_by_region.sort_values("value", ascending=False).head(3)
                    for _, row in top_bw.iterrows():
                        region = str(row.get("region_name") or row.get("category") or "Unknown")
                        val = float(row.get("value", 0.0))
                        if val >= 80.0:
                            plays.append(Play(
                                title=f"Capacity Upgrade - {region}",
                                description=f"Utilization at {val:.1f}% in {region}. Upgrade capacity and optimize traffic to avoid congestion.",
                                category=PlayCategory.INFRASTRUCTURE_UPGRADE,
                                subject_area=SubjectArea.NETWORK,
                                impact_score=8.2,
                                effort_score=7.8,
                                roi_score=7.9,
                                risk_score=4.0,
                                estimated_cost=1400000.0,
                                estimated_duration_months=12,
                                tags=["capacity", region]
                            ))
                        # Progress tick per region processed
                        self._update_progress(min(0.80, self.workflow_status.total_progress + 0.05))
                        time.sleep(0.02)
            except Exception:
                pass

            # Step 5: Packet loss hotspots
            try:
                if packet_loss_by_region is not None and not packet_loss_by_region.empty:
                    top_pl = packet_loss_by_region.sort_values("value", ascending=False).head(3)
                    for _, row in top_pl.iterrows():
                        region = str(row.get("region_name") or row.get("category") or "Unknown")
                        val = float(row.get("value", 0.0))
                        if val >= 0.2:
                            plays.append(Play(
                                title=f"Packet Loss Remediation - {region}",
                                description=f"Packet loss at {val:.2f}% in {region}. Improve routing, repair links, and tune buffers.",
                                category=PlayCategory.PERFORMANCE_OPTIMIZATION,
                                subject_area=SubjectArea.NETWORK,
                                impact_score=7.4,
                                effort_score=5.8,
                                roi_score=7.1,
                                risk_score=3.0,
                                estimated_cost=450000.0,
                                estimated_duration_months=5,
                                tags=["packet-loss", region]
                            ))
                        self._update_progress(min(0.90, self.workflow_status.total_progress + 0.03))
                        time.sleep(0.02)
            except Exception:
                pass

        finally:
            # Add generated plays (cap to max)
            for play in plays[: self.max_plays_per_area]:
                self._add_play(play)
            # Final progress before completion
            self._update_progress(0.98, "Finalizing network analysis")
            time.sleep(0.05)


