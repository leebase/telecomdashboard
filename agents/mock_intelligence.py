"""
Mock Intelligence Engine for Playbook Prioritizer Agent

This module provides sophisticated mock intelligence for generating realistic business plays
with area-specific business logic, market-aware scoring, and dynamic play generation.
"""

import random
import time
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from models.play_models import (
    Play, 
    PlayCategory, 
    SubjectArea,
    AgentState
)


class MockIntelligenceEngine:
    """Advanced mock intelligence engine with business logic and market awareness"""
    
    def __init__(self):
        """Initialize the mock intelligence engine"""
        self.market_conditions = {
            "economic_climate": "stable",  # stable, growth, recession
            "competition_level": "high",   # low, medium, high
            "regulatory_environment": "evolving",  # stable, evolving, strict
            "technology_trends": "accelerating"  # stable, accelerating, disruptive
        }
        
        self.business_context = {
            "company_size": "enterprise",  # startup, midmarket, enterprise
            "industry_maturity": "mature",  # emerging, growing, mature
            "digital_transformation_stage": "advanced"  # early, intermediate, advanced
        }
        
        # Area-specific business logic weights
        self.area_weights = {
            SubjectArea.NETWORK: {
                "impact": 0.35,
                "effort": 0.20,
                "roi": 0.30,
                "risk": 0.15
            },
            SubjectArea.NETWORK_QOE: {
                "impact": 0.40,
                "effort": 0.25,
                "roi": 0.35,
                "risk": 0.20
            },
            SubjectArea.CUSTOMER: {
                "impact": 0.40,
                "effort": 0.15,
                "roi": 0.35,
                "risk": 0.10
            },
            SubjectArea.REVENUE: {
                "impact": 0.30,
                "effort": 0.25,
                "roi": 0.40,
                "risk": 0.05
            },
            SubjectArea.USAGE: {
                "impact": 0.25,
                "effort": 0.30,
                "roi": 0.35,
                "risk": 0.10
            },
            SubjectArea.OPERATIONS: {
                "impact": 0.35,
                "effort": 0.25,
                "roi": 0.25,
                "risk": 0.15
            }
        }
    
    def generate_plays_for_area(self, subject_area: SubjectArea, count: int = 5) -> List[Play]:
        """Generate sophisticated plays for a specific subject area"""
        
        if subject_area == SubjectArea.NETWORK:
            return self._generate_network_plays(count)
        elif subject_area == SubjectArea.NETWORK_QOE:
            return self._generate_network_qoe_plays(count)
        elif subject_area == SubjectArea.CUSTOMER:
            return self._generate_customer_plays(count)
        elif subject_area == SubjectArea.REVENUE:
            return self._generate_revenue_plays(count)
        elif subject_area == SubjectArea.USAGE:
            return self._generate_usage_plays(count)
        elif subject_area == SubjectArea.OPERATIONS:
            return self._generate_operations_plays(count)
        else:
            return []
    
    def _generate_network_plays(self, count: int) -> List[Play]:
        """Generate network-focused plays with market-aware scoring"""
        
        network_play_templates = [
            {
                "title": "5G Core Network Performance Optimization",
                "description": "Implement advanced traffic shaping algorithms and load balancing to improve 5G core network throughput by 25% and reduce latency by 40%",
                "category": PlayCategory.PERFORMANCE_OPTIMIZATION,
                "base_impact": 8.5,
                "base_effort": 6.0,
                "base_roi": 7.8,
                "base_risk": 3.2,
                "base_cost": 1250000.0,
                "base_duration": 8,
                "tags": ["5G", "performance", "core-network", "traffic-shaping"]
            },
            {
                "title": "Zero-Trust Network Security Framework",
                "description": "Deploy comprehensive zero-trust architecture with micro-segmentation, identity verification, and continuous monitoring to eliminate network-based attack vectors",
                "category": PlayCategory.SECURITY_ENHANCEMENT,
                "base_impact": 9.2,
                "base_effort": 8.5,
                "base_roi": 8.9,
                "base_risk": 2.1,
                "base_cost": 2100000.0,
                "base_duration": 12,
                "tags": ["security", "zero-trust", "micro-segmentation", "compliance"]
            },
            {
                "title": "Network Infrastructure Modernization",
                "description": "Upgrade legacy network equipment to SDN-enabled infrastructure, improving operational efficiency and enabling automated network management",
                "category": PlayCategory.INFRASTRUCTURE_UPGRADE,
                "base_impact": 7.8,
                "base_effort": 9.2,
                "base_roi": 6.5,
                "base_risk": 4.8,
                "base_cost": 3500000.0,
                "base_duration": 18,
                "tags": ["infrastructure", "SDN", "automation", "modernization"]
            },
            {
                "title": "Network Monitoring & Analytics Platform",
                "description": "Implement AI-powered network monitoring with predictive analytics to identify and resolve issues before they impact customers",
                "category": PlayCategory.OPERATIONAL_EFFICIENCY,
                "base_impact": 6.5,
                "base_effort": 5.8,
                "base_roi": 7.2,
                "base_risk": 3.5,
                "base_cost": 850000.0,
                "base_duration": 6,
                "tags": ["monitoring", "analytics", "AI", "predictive-maintenance"]
            },
            {
                "title": "Network Capacity Planning & Expansion",
                "description": "Strategic capacity planning and targeted network expansion to handle 3x traffic growth over next 24 months",
                "category": PlayCategory.PERFORMANCE_OPTIMIZATION,
                "base_impact": 8.0,
                "base_effort": 7.5,
                "base_roi": 8.2,
                "base_risk": 4.0,
                "base_cost": 2800000.0,
                "base_duration": 15,
                "tags": ["capacity-planning", "expansion", "growth", "scalability"]
            },
            {
                "title": "Edge Computing Network Deployment",
                "description": "Deploy edge computing nodes across network to reduce latency and improve user experience for latency-sensitive applications",
                "category": PlayCategory.INFRASTRUCTURE_UPGRADE,
                "base_impact": 7.5,
                "base_effort": 8.8,
                "base_roi": 7.0,
                "base_risk": 5.2,
                "base_cost": 1800000.0,
                "base_duration": 14,
                "tags": ["edge-computing", "latency", "infrastructure", "5G"]
            }
        ]
        
        return self._create_plays_from_templates(network_play_templates, SubjectArea.NETWORK, count)
    
    def _generate_network_qoe_plays(self, count: int) -> List[Play]:
        """Generate network QoE-focused plays with market-aware scoring"""
        
        network_qoe_play_templates = [
            {
                "title": "Network Quality of Experience Monitoring & Optimization",
                "description": "Implement comprehensive QoE monitoring across all network layers with real-time optimization to improve user satisfaction scores by 30%",
                "category": PlayCategory.PERFORMANCE_OPTIMIZATION,
                "base_impact": 8.8,
                "base_effort": 7.5,
                "base_roi": 8.2,
                "base_risk": 4.5,
                "base_cost": 1450000.0,
                "base_duration": 11,
                "tags": ["qoe-monitoring", "network-optimization", "user-experience", "real-time"]
            },
            {
                "title": "End-to-End Service Quality Assurance",
                "description": "Holistic service quality monitoring from network core to user device with automated issue resolution and SLA management",
                "category": PlayCategory.PERFORMANCE_OPTIMIZATION,
                "base_impact": 8.5,
                "base_effort": 8.2,
                "base_roi": 7.8,
                "base_risk": 5.0,
                "base_cost": 1850000.0,
                "base_duration": 13,
                "tags": ["service-quality", "sla-management", "automation", "end-to-end"]
            },
            {
                "title": "User Experience Analytics & Optimization",
                "description": "Advanced UX analytics with A/B testing and continuous optimization to improve customer satisfaction and reduce support tickets",
                "category": PlayCategory.PERFORMANCE_OPTIMIZATION,
                "base_impact": 7.8,
                "base_effort": 6.5,
                "base_roi": 7.5,
                "base_risk": 3.8,
                "base_cost": 950000.0,
                "base_duration": 9,
                "tags": ["ux-analytics", "ab-testing", "optimization", "customer-satisfaction"]
            },
            {
                "title": "Network Performance Benchmarking & Improvement",
                "description": "Comprehensive network performance benchmarking against industry standards with targeted improvement initiatives",
                "category": PlayCategory.PERFORMANCE_OPTIMIZATION,
                "base_impact": 7.5,
                "base_effort": 6.8,
                "base_roi": 7.2,
                "base_risk": 4.2,
                "base_cost": 780000.0,
                "base_duration": 8,
                "tags": ["benchmarking", "performance-improvement", "industry-standards", "targeted"]
            },
            {
                "title": "Predictive Network Issue Prevention",
                "description": "ML-based predictive analytics to identify and prevent network issues before they impact user experience",
                "category": PlayCategory.PERFORMANCE_OPTIMIZATION,
                "base_impact": 8.2,
                "base_effort": 7.8,
                "base_roi": 8.0,
                "base_risk": 4.8,
                "base_cost": 1250000.0,
                "base_duration": 10,
                "tags": ["predictive-analytics", "ml", "issue-prevention", "proactive"]
            }
        ]
        
        return self._create_plays_from_templates(network_qoe_play_templates, SubjectArea.NETWORK_QOE, count)
    
    def _generate_customer_plays(self, count: int) -> List[Play]:
        """Generate customer-focused plays with market-aware scoring"""
        
        customer_play_templates = [
            {
                "title": "Predictive Customer Churn Prevention",
                "description": "Implement ML-based customer behavior analysis and proactive retention strategies to reduce churn by 35% and increase customer lifetime value",
                "category": PlayCategory.CUSTOMER_RETENTION,
                "base_impact": 8.8,
                "base_effort": 7.2,
                "base_roi": 8.5,
                "base_risk": 2.8,
                "base_cost": 950000.0,
                "base_duration": 9,
                "tags": ["customer-retention", "ML", "analytics", "churn-prevention"]
            },
            {
                "title": "Omnichannel Customer Experience Platform",
                "description": "Unified customer experience across all touchpoints with personalized recommendations and seamless channel transitions",
                "category": PlayCategory.CUSTOMER_RETENTION,
                "base_impact": 8.2,
                "base_effort": 8.8,
                "base_roi": 7.8,
                "base_risk": 3.5,
                "base_cost": 1650000.0,
                "base_duration": 12,
                "tags": ["omnichannel", "customer-experience", "personalization", "unified-platform"]
            },
            {
                "title": "Customer Self-Service Portal Enhancement",
                "description": "Advanced self-service capabilities with AI-powered chatbots and knowledge base to reduce support costs by 40%",
                "category": PlayCategory.OPERATIONAL_EFFICIENCY,
                "base_impact": 6.8,
                "base_effort": 5.5,
                "base_roi": 7.5,
                "base_risk": 2.2,
                "base_cost": 650000.0,
                "base_duration": 7,
                "tags": ["self-service", "AI", "chatbots", "support-automation"]
            },
            {
                "title": "Customer Journey Analytics & Optimization",
                "description": "Comprehensive customer journey mapping with behavioral analytics to identify friction points and optimize conversion rates",
                "category": PlayCategory.CUSTOMER_RETENTION,
                "base_impact": 7.5,
                "base_effort": 6.8,
                "base_roi": 7.2,
                "base_risk": 3.0,
                "base_cost": 780000.0,
                "base_duration": 8,
                "tags": ["customer-journey", "analytics", "conversion-optimization", "behavioral-analysis"]
            },
            {
                "title": "Proactive Customer Success Program",
                "description": "Data-driven customer success initiatives with early warning systems and proactive outreach to improve satisfaction scores",
                "category": PlayCategory.CUSTOMER_RETENTION,
                "base_impact": 7.8,
                "base_effort": 6.2,
                "base_roi": 7.8,
                "base_risk": 2.5,
                "base_cost": 520000.0,
                "base_duration": 6,
                "tags": ["customer-success", "proactive-outreach", "satisfaction", "early-warning"]
            }
        ]
        
        return self._create_plays_from_templates(customer_play_templates, SubjectArea.CUSTOMER, count)
    
    def _generate_revenue_plays(self, count: int) -> List[Play]:
        """Generate revenue-focused plays with market-aware scoring"""
        
        revenue_play_templates = [
            {
                "title": "Dynamic Pricing & Revenue Optimization",
                "description": "AI-powered dynamic pricing strategies with real-time market analysis to maximize revenue while maintaining competitive positioning",
                "category": PlayCategory.REVENUE_GROWTH,
                "base_impact": 8.5,
                "base_effort": 7.8,
                "base_roi": 9.2,
                "base_risk": 4.2,
                "base_cost": 1200000.0,
                "base_duration": 10,
                "tags": ["dynamic-pricing", "revenue-optimization", "AI", "market-analysis"]
            },
            {
                "title": "New Product & Service Development",
                "description": "Strategic expansion into adjacent markets with innovative product offerings to capture new revenue streams",
                "category": PlayCategory.REVENUE_GROWTH,
                "base_impact": 9.0,
                "base_effort": 9.5,
                "base_roi": 8.8,
                "base_risk": 6.5,
                "base_cost": 2800000.0,
                "base_duration": 18,
                "tags": ["product-development", "market-expansion", "innovation", "new-revenue"]
            },
            {
                "title": "Customer Upselling & Cross-selling Automation",
                "description": "Intelligent recommendation engine for identifying upsell and cross-sell opportunities to increase average revenue per customer",
                "category": PlayCategory.REVENUE_GROWTH,
                "base_impact": 7.2,
                "base_effort": 6.5,
                "base_roi": 8.5,
                "base_risk": 3.8,
                "base_cost": 850000.0,
                "base_duration": 8,
                "tags": ["upselling", "cross-selling", "recommendations", "revenue-per-customer"]
            },
            {
                "title": "Subscription Model Optimization",
                "description": "Optimize subscription tiers, pricing, and retention strategies to improve recurring revenue and reduce churn",
                "category": PlayCategory.REVENUE_GROWTH,
                "base_impact": 7.8,
                "base_effort": 6.8,
                "base_roi": 8.2,
                "base_risk": 3.2,
                "base_cost": 720000.0,
                "base_duration": 7,
                "tags": ["subscription-optimization", "recurring-revenue", "pricing-strategy", "retention"]
            },
            {
                "title": "Market Expansion & Geographic Growth",
                "description": "Strategic expansion into new geographic markets with localized offerings and partnerships",
                "category": PlayCategory.REVENUE_GROWTH,
                "base_impact": 8.8,
                "base_effort": 9.2,
                "base_roi": 8.0,
                "base_risk": 7.5,
                "base_cost": 3200000.0,
                "base_duration": 20,
                "tags": ["market-expansion", "geographic-growth", "localization", "partnerships"]
            }
        ]
        
        return self._create_plays_from_templates(revenue_play_templates, SubjectArea.REVENUE, count)
    
    def _generate_usage_plays(self, count: int) -> List[Play]:
        """Generate usage and adoption-focused plays with market-aware scoring"""
        
        usage_play_templates = [
            {
                "title": "Digital Adoption & User Onboarding",
                "description": "Streamlined digital onboarding process with interactive tutorials and progressive feature introduction to increase user adoption by 45%",
                "category": PlayCategory.OPERATIONAL_EFFICIENCY,
                "base_impact": 7.5,
                "base_effort": 6.2,
                "base_roi": 7.8,
                "base_risk": 2.8,
                "base_cost": 680000.0,
                "base_duration": 7,
                "tags": ["digital-adoption", "onboarding", "user-experience", "feature-introduction"]
            },
            {
                "title": "Feature Usage Analytics & Optimization",
                "description": "Comprehensive feature usage analytics to identify underutilized capabilities and optimize user engagement",
                "category": PlayCategory.OPERATIONAL_EFFICIENCY,
                "base_impact": 6.8,
                "base_effort": 5.8,
                "base_roi": 7.2,
                "base_risk": 2.5,
                "base_cost": 520000.0,
                "base_duration": 6,
                "tags": ["feature-analytics", "usage-optimization", "user-engagement", "data-driven"]
            },
            {
                "title": "Mobile App Experience Enhancement",
                "description": "Mobile-first design improvements with offline capabilities and push notifications to increase mobile engagement by 60%",
                "category": PlayCategory.CUSTOMER_RETENTION,
                "base_impact": 7.2,
                "base_effort": 6.8,
                "base_roi": 7.5,
                "base_risk": 3.2,
                "base_cost": 780000.0,
                "base_duration": 8,
                "tags": ["mobile-experience", "offline-capabilities", "push-notifications", "engagement"]
            },
            {
                "title": "API Usage & Developer Experience",
                "description": "Enhanced API documentation, developer tools, and usage analytics to increase third-party integrations and platform adoption",
                "category": PlayCategory.INNOVATION_INITIATIVE,
                "base_impact": 6.5,
                "base_effort": 7.2,
                "base_roi": 7.8,
                "base_risk": 4.0,
                "base_cost": 920000.0,
                "base_duration": 9,
                "tags": ["API", "developer-experience", "third-party-integrations", "platform-adoption"]
            },
            {
                "title": "User Training & Knowledge Management",
                "description": "Comprehensive training programs and knowledge base to improve user proficiency and reduce support requests",
                "category": PlayCategory.OPERATIONAL_EFFICIENCY,
                "base_impact": 6.2,
                "base_effort": 5.5,
                "base_roi": 6.8,
                "base_risk": 2.0,
                "base_cost": 450000.0,
                "base_duration": 5,
                "tags": ["user-training", "knowledge-management", "proficiency", "support-reduction"]
            }
        ]
        
        return self._create_plays_from_templates(usage_play_templates, SubjectArea.USAGE, count)
    
    def _generate_operations_plays(self, count: int) -> List[Play]:
        """Generate operations-focused plays with market-aware scoring"""
        
        operations_play_templates = [
            {
                "title": "Process Automation & Workflow Optimization",
                "description": "End-to-end process automation with intelligent workflow management to reduce manual effort by 50% and improve efficiency",
                "category": PlayCategory.OPERATIONAL_EFFICIENCY,
                "base_impact": 8.2,
                "base_effort": 7.5,
                "base_roi": 8.5,
                "base_risk": 3.8,
                "base_cost": 1100000.0,
                "base_duration": 10,
                "tags": ["process-automation", "workflow-optimization", "efficiency", "manual-effort-reduction"]
            },
            {
                "title": "Data Quality & Master Data Management",
                "description": "Comprehensive data governance framework with automated quality checks and master data consolidation",
                "category": PlayCategory.COMPLIANCE_IMPROVEMENT,
                "base_impact": 7.8,
                "base_effort": 8.2,
                "base_roi": 7.5,
                "base_risk": 4.5,
                "base_cost": 1450000.0,
                "base_duration": 12,
                "tags": ["data-quality", "master-data-management", "governance", "compliance"]
            },
            {
                "title": "IT Service Management Modernization",
                "description": "Modern ITSM platform with AI-powered incident management and automated resolution workflows",
                "category": PlayCategory.OPERATIONAL_EFFICIENCY,
                "base_impact": 7.5,
                "base_effort": 7.8,
                "base_roi": 7.8,
                "base_risk": 4.2,
                "base_cost": 980000.0,
                "base_duration": 9,
                "tags": ["ITSM", "incident-management", "automation", "AI-powered"]
            },
            {
                "title": "Compliance & Risk Management Platform",
                "description": "Integrated compliance monitoring and risk assessment platform with automated reporting and alerting",
                "category": PlayCategory.COMPLIANCE_IMPROVEMENT,
                "base_impact": 8.5,
                "base_effort": 8.8,
                "base_roi": 8.2,
                "base_risk": 2.8,
                "base_cost": 1650000.0,
                "base_duration": 14,
                "tags": ["compliance", "risk-management", "automated-reporting", "monitoring"]
            },
            {
                "title": "Performance Monitoring & Alerting",
                "description": "Real-time performance monitoring with intelligent alerting and predictive issue detection",
                "category": PlayCategory.OPERATIONAL_EFFICIENCY,
                "base_impact": 7.2,
                "base_effort": 6.5,
                "base_roi": 7.5,
                "base_risk": 3.0,
                "base_cost": 720000.0,
                "base_duration": 7,
                "tags": ["performance-monitoring", "intelligent-alerting", "predictive-detection", "real-time"]
            }
        ]
        
        return self._create_plays_from_templates(operations_play_templates, SubjectArea.OPERATIONS, count)
    
    def _create_plays_from_templates(self, templates: List[Dict], subject_area: SubjectArea, count: int) -> List[Play]:
        """Create plays from templates with market-aware scoring variations"""
        
        # Select random templates up to count
        selected_templates = random.sample(templates, min(count, len(templates)))
        plays = []
        
        for template in selected_templates:
            # Apply market-aware scoring adjustments
            adjusted_scores = self._apply_market_adjustments(
                template["base_impact"],
                template["base_effort"], 
                template["base_roi"],
                template["base_risk"],
                subject_area
            )
            
            # Add some randomization to make plays unique
            final_scores = self._add_scoring_variations(adjusted_scores)
            
            # Create the play
            play = Play(
                title=template["title"],
                description=template["description"],
                category=template["category"],
                subject_area=subject_area,
                impact_score=final_scores["impact"],
                effort_score=final_scores["effort"],
                roi_score=final_scores["roi"],
                risk_score=final_scores["risk"],
                estimated_cost=template["base_cost"] * random.uniform(0.9, 1.1),
                estimated_duration_months=template["base_duration"] + random.randint(-1, 1),
                tags=template["tags"]
            )
            
            plays.append(play)
        
        return plays
    
    def _apply_market_adjustments(self, impact: float, effort: float, roi: float, risk: float, subject_area: SubjectArea) -> Dict[str, float]:
        """Apply market condition adjustments to base scores"""
        
        adjustments = {
            "impact": impact,
            "effort": effort,
            "roi": roi,
            "risk": risk
        }
        
        # Economic climate adjustments
        if self.market_conditions["economic_climate"] == "growth":
            adjustments["roi"] *= 1.1
            adjustments["risk"] *= 0.9
        elif self.market_conditions["economic_climate"] == "recession":
            adjustments["roi"] *= 0.9
            adjustments["risk"] *= 1.2
        
        # Competition level adjustments
        if self.market_conditions["competition_level"] == "high":
            adjustments["impact"] *= 1.15
            adjustments["effort"] *= 1.1
        elif self.market_conditions["competition_level"] == "low":
            adjustments["impact"] *= 0.95
            adjustments["effort"] *= 0.9
        
        # Regulatory environment adjustments
        if self.market_conditions["regulatory_environment"] == "strict":
            adjustments["effort"] *= 1.2
            adjustments["risk"] *= 1.1
        elif self.market_conditions["regulatory_environment"] == "stable":
            adjustments["effort"] *= 0.95
            adjustments["risk"] *= 0.9
        
        # Technology trends adjustments
        if self.market_conditions["technology_trends"] == "accelerating":
            adjustments["impact"] *= 1.1
            adjustments["roi"] *= 1.05
        elif self.market_conditions["technology_trends"] == "disruptive":
            adjustments["impact"] *= 1.2
            adjustments["risk"] *= 1.15
        
        # Ensure scores stay within valid range
        for key in adjustments:
            adjustments[key] = max(0.0, min(10.0, adjustments[key]))
        
        return adjustments
    
    def _add_scoring_variations(self, base_scores: Dict[str, float]) -> Dict[str, float]:
        """Add small random variations to make plays unique"""
        
        variations = {}
        for key, score in base_scores.items():
            # Add ±5% variation
            variation = random.uniform(0.95, 1.05)
            variations[key] = max(0.0, min(10.0, score * variation))
        
        return variations
    
    def update_market_conditions(self, new_conditions: Dict[str, str]):
        """Update market conditions for dynamic scoring"""
        self.market_conditions.update(new_conditions)
    
    def update_business_context(self, new_context: Dict[str, str]):
        """Update business context for dynamic scoring"""
        self.business_context.update(new_context)
    
    def get_market_analysis(self) -> Dict[str, Any]:
        """Get current market analysis summary"""
        return {
            "market_conditions": self.market_conditions.copy(),
            "business_context": self.business_context.copy(),
            "area_weights": self.area_weights.copy(),
            "analysis_timestamp": datetime.now().isoformat()
        }


# Convenience functions for easy access
def get_mock_intelligence_engine() -> MockIntelligenceEngine:
    """Get a configured mock intelligence engine instance"""
    return MockIntelligenceEngine()


def generate_plays_for_area(subject_area: SubjectArea, count: int = 5) -> List[Play]:
    """Generate plays for a specific subject area using the mock intelligence engine"""
    engine = get_mock_intelligence_engine()
    return engine.generate_plays_for_area(subject_area, count)


def get_all_plays_by_area(count_per_area: int = 5) -> Dict[str, List[Play]]:
    """Generate plays for all subject areas"""
    engine = get_mock_intelligence_engine()
    result = {}
    
    for area in SubjectArea:
        result[area.value] = engine.generate_plays_for_area(area, count_per_area)
    
    return result
