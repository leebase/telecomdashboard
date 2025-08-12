"""
Backup Demo Mode for Agent System

This module provides offline demo capabilities and manual override functionality
for agent failures, ensuring the demo can continue even if systems are down.
"""

import json
import time
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from pathlib import Path

from models.play_models import Play, Portfolio, SubjectArea, AgentStatus, WorkflowPhase
from agents.mock_intelligence import get_mock_intelligence_engine


class BackupDemoMode:
    """
    Provides backup demo functionality when live systems are unavailable
    """
    
    def __init__(self):
        self.mock_engine = get_mock_intelligence_engine()
        self.backup_data_path = Path("mock_data/backup_demo_data.json")
        self._load_backup_data()
    
    def _load_backup_data(self):
        """Load pre-generated backup demo data"""
        try:
            if self.backup_data_path.exists():
                with open(self.backup_data_path, 'r') as f:
                    self.backup_data = json.load(f)
                logging.info("✅ Backup demo data loaded successfully")
            else:
                self.backup_data = self._generate_backup_data()
                self._save_backup_data()
                logging.info("✅ Generated new backup demo data")
        except Exception as e:
            logging.warning(f"Could not load backup data: {e}")
            self.backup_data = self._generate_backup_data()
    
    def _save_backup_data(self):
        """Save backup demo data to file"""
        try:
            self.backup_data_path.parent.mkdir(exist_ok=True)
            with open(self.backup_data_path, 'w') as f:
                json.dump(self.backup_data, f, indent=2, default=str)
        except Exception as e:
            logging.error(f"Could not save backup data: {e}")
    
    def _generate_backup_data(self) -> Dict[str, Any]:
        """Generate comprehensive backup demo data"""
        backup_data = {
            "generated_at": datetime.now().isoformat(),
            "scenarios": {
                "network_optimization": {
                    "description": "Network QoE improvement scenario",
                    "plays": self._generate_network_plays(),
                    "expected_outcome": "15% improvement in network performance metrics"
                },
                "customer_retention": {
                    "description": "Customer churn reduction scenario", 
                    "plays": self._generate_customer_plays(),
                    "expected_outcome": "8% reduction in customer churn rate"
                },
                "revenue_growth": {
                    "description": "Revenue optimization scenario",
                    "plays": self._generate_revenue_plays(),
                    "expected_outcome": "12% increase in ARPU and service adoption"
                },
                "operational_efficiency": {
                    "description": "Operational cost reduction scenario",
                    "plays": self._generate_operations_plays(),
                    "expected_outcome": "20% reduction in operational costs"
                },
                "usage_optimization": {
                    "description": "Network usage optimization scenario",
                    "plays": self._generate_usage_plays(),
                    "expected_outcome": "25% improvement in network utilization"
                }
            },
            "portfolio_optimizations": {
                "budget_8_points": self._generate_portfolio_8_points(),
                "budget_12_points": self._generate_portfolio_12_points(),
                "budget_16_points": self._generate_portfolio_16_points()
            },
            "executive_summaries": {
                "conservative": self._generate_executive_summary("conservative"),
                "balanced": self._generate_executive_summary("balanced"),
                "aggressive": self._generate_executive_summary("aggressive")
            }
        }
        return backup_data
    
    def _generate_network_plays(self) -> List[Dict[str, Any]]:
        """Generate network optimization plays"""
        return [
            {
                "title": "Overnight capacity tune (MW)",
                "area": "Network QoE",
                "effort_points": 2,
                "impact_score": 4,
                "confidence": 0.80,
                "kpi_targets": {"QoE_MOS": 0.2, "Network_Availability": 0.5},
                "dependencies": [],
                "notes": "Largest negative mover linked to churn; peer gap present"
            },
            {
                "title": "Peak hour load balancing",
                "area": "Network QoE", 
                "effort_points": 3,
                "impact_score": 5,
                "confidence": 0.75,
                "kpi_targets": {"Peak_Capacity": 0.3, "User_Experience": 0.4},
                "dependencies": ["Overnight capacity tune (MW)"],
                "notes": "Addresses peak congestion during business hours"
            },
            {
                "title": "Edge caching optimization",
                "area": "Network QoE",
                "effort_points": 4,
                "impact_score": 4,
                "confidence": 0.70,
                "kpi_targets": {"Content_Delivery_Speed": 0.25, "Bandwidth_Usage": -0.15},
                "dependencies": [],
                "notes": "Improves content delivery and reduces bandwidth costs"
            }
        ]
    
    def _generate_customer_plays(self) -> List[Dict[str, Any]]:
        """Generate customer retention plays"""
        return [
            {
                "title": "Proactive churn prevention",
                "area": "Customer",
                "effort_points": 3,
                "impact_score": 5,
                "confidence": 0.85,
                "kpi_targets": {"Churn_Rate": -0.3, "Customer_Satisfaction": 0.4},
                "dependencies": [],
                "notes": "AI-driven early warning system for at-risk customers"
            },
            {
                "title": "Loyalty program enhancement",
                "area": "Customer",
                "effort_points": 2,
                "impact_score": 3,
                "confidence": 0.80,
                "kpi_targets": {"Customer_Lifetime_Value": 0.2, "Retention_Rate": 0.15},
                "dependencies": [],
                "notes": "Enhanced rewards and personalized offers"
            }
        ]
    
    def _generate_revenue_plays(self) -> List[Dict[str, Any]]:
        """Generate revenue optimization plays"""
        return [
            {
                "title": "Upsell campaign optimization",
                "area": "Revenue",
                "effort_points": 2,
                "impact_score": 4,
                "confidence": 0.75,
                "kpi_targets": {"ARPU": 0.25, "Service_Adoption": 0.3},
                "dependencies": [],
                "notes": "Targeted campaigns based on usage patterns"
            },
            {
                "title": "Pricing strategy refinement",
                "area": "Revenue",
                "effort_points": 4,
                "impact_score": 5,
                "confidence": 0.70,
                "kpi_targets": {"Revenue_Growth": 0.35, "Market_Share": 0.2},
                "dependencies": [],
                "notes": "Competitive pricing analysis and optimization"
            }
        ]
    
    def _generate_operations_plays(self) -> List[Dict[str, Any]]:
        """Generate operational efficiency plays"""
        return [
            {
                "title": "Automated ticket resolution",
                "area": "Operations",
                "effort_points": 5,
                "impact_score": 4,
                "confidence": 0.65,
                "kpi_targets": {"Resolution_Time": -0.4, "Operational_Costs": -0.25},
                "dependencies": [],
                "notes": "AI-powered ticket classification and routing"
            },
            {
                "title": "Predictive maintenance",
                "area": "Operations",
                "effort_points": 3,
                "impact_score": 4,
                "confidence": 0.80,
                "kpi_targets": {"Equipment_Uptime": 0.3, "Maintenance_Costs": -0.2},
                "dependencies": [],
                "notes": "IoT sensors and ML for equipment health monitoring"
            }
        ]
    
    def _generate_usage_plays(self) -> List[Dict[str, Any]]:
        """Generate usage optimization plays"""
        return [
            {
                "title": "Data usage analytics",
                "area": "Usage",
                "effort_points": 2,
                "impact_score": 3,
                "confidence": 0.85,
                "kpi_targets": {"Data_Efficiency": 0.25, "User_Insights": 0.4},
                "dependencies": [],
                "notes": "Advanced analytics for usage pattern optimization"
            },
            {
                "title": "Bandwidth optimization",
                "area": "Usage",
                "effort_points": 3,
                "impact_score": 4,
                "confidence": 0.75,
                "kpi_targets": {"Network_Efficiency": 0.3, "Cost_Per_GB": -0.2},
                "dependencies": [],
                "notes": "Dynamic bandwidth allocation based on demand"
            }
        ]
    
    def _generate_portfolio_8_points(self) -> Dict[str, Any]:
        """Generate portfolio for 8-point budget"""
        return {
            "selected_plays": [
                "Overnight capacity tune (MW)",
                "Proactive churn prevention", 
                "Upsell campaign optimization"
            ],
            "total_effort": 7,
            "expected_effect": {
                "QoE_MOS": 0.2,
                "Churn_Rate": -0.3,
                "ARPU": 0.25
            },
            "roi_score": 8.5,
            "risk_score": 3.2
        }
    
    def _generate_portfolio_12_points(self) -> Dict[str, Any]:
        """Generate portfolio for 12-point budget"""
        return {
            "selected_plays": [
                "Overnight capacity tune (MW)",
                "Peak hour load balancing",
                "Proactive churn prevention",
                "Upsell campaign optimization",
                "Loyalty program enhancement"
            ],
            "total_effort": 12,
            "expected_effect": {
                "QoE_MOS": 0.4,
                "Peak_Capacity": 0.3,
                "Churn_Rate": -0.3,
                "ARPU": 0.25,
                "Customer_Lifetime_Value": 0.2
            },
            "roi_score": 9.2,
            "risk_score": 4.1
        }
    
    def _generate_portfolio_16_points(self) -> Dict[str, Any]:
        """Generate portfolio for 16-point budget"""
        return {
            "selected_plays": [
                "Overnight capacity tune (MW)",
                "Peak hour load balancing", 
                "Edge caching optimization",
                "Proactive churn prevention",
                "Upsell campaign optimization",
                "Loyalty program enhancement",
                "Data usage analytics"
            ],
            "total_effort": 16,
            "expected_effect": {
                "QoE_MOS": 0.6,
                "Peak_Capacity": 0.3,
                "Content_Delivery_Speed": 0.25,
                "Churn_Rate": -0.3,
                "ARPU": 0.25,
                "Customer_Lifetime_Value": 0.2,
                "Data_Efficiency": 0.25
            },
            "roi_score": 9.8,
            "risk_score": 5.3
        }
    
    def _generate_executive_summary(self, strategy: str) -> str:
        """Generate executive summary for different strategies"""
        summaries = {
            "conservative": """
            **Conservative Strategy (8 Points)**
            
            Focus on high-confidence, low-risk plays that deliver immediate impact:
            • Network capacity optimization to improve QoE and reduce churn
            • Proactive customer retention to protect revenue base
            • Targeted upselling to increase ARPU without major investment
            
            Expected outcomes: 15% network improvement, 8% churn reduction, 25% ARPU increase
            Risk level: Low (3.2/10)
            """,
            
            "balanced": """
            **Balanced Strategy (12 Points)**
            
            Balanced approach combining quick wins with strategic initiatives:
            • Enhanced network optimization including peak hour management
            • Comprehensive customer retention and loyalty enhancement
            • Revenue optimization through targeted campaigns
            
            Expected outcomes: 25% network improvement, 10% churn reduction, 30% revenue growth
            Risk level: Medium (4.1/10)
            """,
            
            "aggressive": """
            **Aggressive Strategy (16 Points)**
            
            Comprehensive transformation addressing all major areas:
            • Full network optimization including edge caching
            • Complete customer lifecycle management
            • Advanced analytics and operational efficiency
            • Revenue maximization across all channels
            
            Expected outcomes: 35% network improvement, 15% churn reduction, 40% revenue growth
            Risk level: Medium-High (5.3/10)
            """
        }
        return summaries.get(strategy, summaries["balanced"])
    
    def get_backup_scenario(self, scenario_name: str) -> Dict[str, Any]:
        """Get a specific backup scenario"""
        return self.backup_data.get("scenarios", {}).get(scenario_name, {})
    
    def get_backup_portfolio(self, budget_points: int) -> Dict[str, Any]:
        """Get backup portfolio for specific budget"""
        budget_key = f"budget_{budget_points}_points"
        return self.backup_data.get("portfolio_optimizations", {}).get(budget_key, {})
    
    def get_backup_executive_summary(self, strategy: str = "balanced") -> str:
        """Get backup executive summary"""
        return self.backup_data.get("executive_summaries", {}).get(strategy, "")
    
    def run_backup_demo(self, duration_seconds: int = 30) -> Dict[str, Any]:
        """
        Run a complete backup demo simulation
        
        Args:
            duration_seconds: Duration of the demo simulation
            
        Returns:
            Demo results and timing information
        """
        start_time = time.time()
        
        # Simulate agent execution phases
        demo_results = {
            "start_time": datetime.now().isoformat(),
            "duration_seconds": duration_seconds,
            "phases": [],
            "final_portfolio": None,
            "executive_summary": ""
        }
        
        # Phase 1: Agent Analysis (0-40% of demo)
        phase1_duration = duration_seconds * 0.4
        demo_results["phases"].append({
            "name": "Agent Analysis",
            "duration": phase1_duration,
            "status": "completed",
            "agents": [
                {"name": "Network QoE Agent", "status": "completed", "plays_generated": 3},
                {"name": "Customer Agent", "status": "completed", "plays_generated": 2},
                {"name": "Revenue Agent", "status": "completed", "plays_generated": 2},
                {"name": "Operations Agent", "status": "completed", "plays_generated": 2},
                {"name": "Usage Agent", "status": "completed", "plays_generated": 2}
            ]
        })
        
        time.sleep(phase1_duration)
        
        # Phase 2: Portfolio Optimization (40-80% of demo)
        phase2_duration = duration_seconds * 0.4
        demo_results["phases"].append({
            "name": "Portfolio Optimization",
            "duration": phase2_duration,
            "status": "completed",
            "optimization_steps": [
                "Initial portfolio creation",
                "ROI scoring and ranking",
                "Dependency resolution",
                "Budget optimization",
                "Risk assessment"
            ]
        })
        
        time.sleep(phase2_duration)
        
        # Phase 3: Results Generation (80-100% of demo)
        phase3_duration = duration_seconds * 0.2
        demo_results["phases"].append({
            "name": "Results Generation",
            "duration": phase3_duration,
            "status": "completed",
            "outputs": [
                "Prioritized play list",
                "Portfolio selection",
                "Executive summary",
                "Implementation roadmap"
            ]
        })
        
        time.sleep(phase3_duration)
        
        # Generate final results
        demo_results["final_portfolio"] = self.get_backup_portfolio(12)  # Default to 12 points
        demo_results["executive_summary"] = self.get_backup_executive_summary("balanced")
        demo_results["end_time"] = datetime.now().isoformat()
        demo_results["actual_duration"] = time.time() - start_time
        
        return demo_results
    
    def manual_override_agent(self, agent_name: str, action: str, **kwargs) -> Dict[str, Any]:
        """
        Manual override for agent actions
        
        Args:
            agent_name: Name of the agent to override
            action: Action to perform
            **kwargs: Additional parameters
            
        Returns:
            Override result
        """
        try:
            if action == "force_complete":
                return {
                    "success": True,
                    "agent": agent_name,
                    "action": action,
                    "status": "forced_completion",
                    "message": f"Agent {agent_name} manually forced to complete",
                    "timestamp": datetime.now().isoformat()
                }
            
            elif action == "generate_plays":
                area_mapping = {
                    "Network QoE Agent": SubjectArea.NETWORK_QOE,
                    "Customer Agent": SubjectArea.CUSTOMER,
                    "Revenue Agent": SubjectArea.REVENUE,
                    "Operations Agent": SubjectArea.OPERATIONS,
                    "Usage Agent": SubjectArea.USAGE
                }
                
                area = area_mapping.get(agent_name, SubjectArea.NETWORK_QOE)
                plays = self.mock_engine.generate_plays_for_area(area, num_plays=3)
                
                return {
                    "success": True,
                    "agent": agent_name,
                    "action": action,
                    "plays_generated": len(plays),
                    "plays": [play.to_dict() for play in plays],
                    "timestamp": datetime.now().isoformat()
                }
            
            elif action == "reset_status":
                return {
                    "success": True,
                    "agent": agent_name,
                    "action": action,
                    "status": "reset",
                    "message": f"Agent {agent_name} status reset",
                    "timestamp": datetime.now().isoformat()
                }
            
            else:
                return {
                    "success": False,
                    "error": f"Unknown action: {action}",
                    "timestamp": datetime.now().isoformat()
                }
                
        except Exception as e:
                    return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
    
    def generate_demo_plays(self, subject_area: SubjectArea, count: int = 5) -> List[Dict[str, Any]]:
        """Generate demo plays for a specific subject area"""
        try:
            from agents.mock_intelligence import MockIntelligenceEngine
            
            mock_engine = MockIntelligenceEngine()
            plays = mock_engine.generate_plays_for_area(subject_area, count)
            
            return [play.to_dict() for play in plays]
            
        except Exception as e:
            logging.error(f"Error generating demo plays: {e}")
            # Fallback to basic plays
            return self._generate_basic_plays(subject_area, count)
    
    def _generate_basic_plays(self, subject_area: SubjectArea, count: int = 5) -> List[Dict[str, Any]]:
        """Generate basic plays as fallback"""
        basic_plays = []
        
        for i in range(count):
            play = {
                "id": f"demo_play_{subject_area.value}_{i+1}",
                "title": f"Demo {subject_area.value.title()} Initiative {i+1}",
                "description": f"Basic demo initiative for {subject_area.value} area",
                "category": "performance_optimization",
                "subject_area": subject_area.value,
                "impact_score": 7.0 + (i * 0.5),
                "effort_score": 6.0 + (i * 0.3),
                "roi_score": 7.5 + (i * 0.4),
                "risk_score": 4.0 + (i * 0.2),
                "score": 0.0,
                "rank": i + 1,
                "estimated_cost": 500000.0 + (i * 100000),
                "estimated_duration_months": 6 + i,
                "priority_level": 3,
                "priority_label": "Medium",
                "created_at": datetime.now().isoformat(),
                "tags": ["demo", subject_area.value, "basic"]
            }
            basic_plays.append(play)
        
        return basic_plays
    
    def is_available(self) -> bool:
        """Check if backup demo mode is available"""
        try:
            # Check if we can generate demo data
            test_plays = self.generate_demo_plays(SubjectArea.NETWORK_QOE, 1)
            return len(test_plays) > 0
        except Exception as e:
            logging.error(f"Backup demo availability check failed: {e}")
            return False


# Global backup demo instance
backup_demo = BackupDemoMode()


def get_backup_demo() -> BackupDemoMode:
    """Get the global backup demo instance"""
    return backup_demo


def test_backup_demo() -> Dict[str, Any]:
    """Test the backup demo functionality"""
    try:
        demo = get_backup_demo()
        
        # Test scenario retrieval
        network_scenario = demo.get_backup_scenario("network_optimization")
        
        # Test portfolio retrieval
        portfolio_8 = demo.get_backup_portfolio(8)
        
        # Test executive summary
        summary = demo.get_backup_executive_summary("balanced")
        
        # Test manual override
        override_result = demo.manual_override_agent("Network QoE Agent", "force_complete")
        
        return {
            "success": True,
            "scenario_retrieved": bool(network_scenario),
            "portfolio_retrieved": bool(portfolio_8),
            "summary_generated": bool(summary),
            "override_working": override_result["success"],
            "backup_demo_ready": True
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "backup_demo_ready": False
        }
