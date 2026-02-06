"""
Matching Models for TrustyClaw

Data models for ML-based agent-skill matching.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, List, Any
from datetime import datetime
from enum import Enum
import uuid


class ComplexityLevel(Enum):
    """Task complexity levels"""
    TRIVIAL = 1  # Very simple, quick tasks
    SIMPLE = 2   # Basic tasks
    MODERATE = 3 # Standard complexity
    COMPLEX = 4  # Complex tasks
    EXPERT = 5   # Highly specialized, complex tasks


@dataclass
class TaskRequirements:
    """Requirements for a task to be completed"""
    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = ""
    description: str = ""
    required_skills: List[str] = field(default_factory=list)
    category: str = ""
    complexity: float = 0.5  # 0.0 to 1.0
    complexity_level: ComplexityLevel = ComplexityLevel.MODERATE
    estimated_hours: int = 1
    priority: int = 1  # 1-5, higher = more urgent
    constraints: Dict[str, Any] = field(default_factory=dict)
    preferred_agent_rating: float = 0.0
    max_budget: Optional[int] = None
    deadline: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "title": self.title,
            "description": self.description,
            "required_skills": self.required_skills,
            "category": self.category,
            "complexity": self.complexity,
            "complexity_level": self.complexity_level.value,
            "estimated_hours": self.estimated_hours,
            "priority": self.priority,
            "constraints": self.constraints,
            "preferred_agent_rating": self.preferred_agent_rating,
            "max_budget": self.max_budget,
            "deadline": self.deadline.isoformat() if self.deadline else None,
            "created_at": self.created_at.isoformat(),
        }


@dataclass
class RenterHistory:
    """Historical data about a renter"""
    renter_address: str = ""
    total_tasks: int = 0
    completed_tasks: int = 0
    average_rating_given: float = 0.0
    total_spent: int = 0  # USDC lamports
    preferred_categories: List[str] = field(default_factory=list)
    average_task_complexity: float = 0.5
    last_active: Optional[datetime] = None
    repeat_hire_rate: float = 0.0  # Rate of hiring same agent multiple times
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "renter_address": self.renter_address,
            "total_tasks": self.total_tasks,
            "completed_tasks": self.completed_tasks,
            "average_rating_given": self.average_rating_given,
            "total_spent": self.total_spent,
            "preferred_categories": self.preferred_categories,
            "average_task_complexity": self.average_task_complexity,
            "last_active": self.last_active.isoformat() if self.last_active else None,
            "repeat_hire_rate": self.repeat_hire_rate,
        }


@dataclass
class SkillMatch:
    """Match between a task requirement and a skill"""
    skill_id: str = ""
    agent_address: str = ""
    skill_name: str = ""
    match_score: float = 0.0  # 0.0 to 1.0
    skill_coverage: float = 0.0  # Percentage of required skills covered
    missing_skills: List[str] = field(default_factory=list)
    rating: float = 0.0
    completed_tasks: int = 0
    price_per_task: int = 0
    estimated_duration_hours: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "skill_id": self.skill_id,
            "agent_address": self.agent_address,
            "skill_name": self.skill_name,
            "match_score": self.match_score,
            "skill_coverage": self.skill_coverage,
            "missing_skills": self.missing_skills,
            "rating": self.rating,
            "completed_tasks": self.completed_tasks,
            "price_per_task": self.price_per_task,
            "estimated_duration_hours": self.estimated_duration_hours,
        }


@dataclass
class AgentRecommendation:
    """Recommendation for an agent for a task"""
    agent_address: str = ""
    agent_name: str = ""
    overall_score: float = 0.0  # Combined match score
    skill_matches: List[SkillMatch] = field(default_factory=list)
    compatibility_score: float = 0.0  # Based on renter history
    price_prediction: float = 0.0  # Predicted price in USDC lamports
    estimated_delivery_hours: int = 0
    confidence: float = 0.0  # 0.0 to 1.0
    reasons: List[str] = field(default_factory=list)
    risk_factors: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_address": self.agent_address,
            "agent_name": self.agent_name,
            "overall_score": self.overall_score,
            "skill_matches": [m.to_dict() for m in self.skill_matches],
            "compatibility_score": self.compatibility_score,
            "price_prediction": self.price_prediction,
            "estimated_delivery_hours": self.estimated_delivery_hours,
            "confidence": self.confidence,
            "reasons": self.reasons,
            "risk_factors": self.risk_factors,
        }


@dataclass
class PricePrediction:
    """Price prediction for a task"""
    skill_id: str = ""
    predicted_price: int = 0  # USDC lamports
    price_range_low: int = 0
    price_range_high: int = 0
    confidence: float = 0.0
    factors: Dict[str, float] = field(default_factory=dict)  # Breakdown of factors
    market_average: int = 0
    recommendation: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "skill_id": self.skill_id,
            "predicted_price": self.predicted_price,
            "price_range_low": self.price_range_low,
            "price_range_high": self.price_range_high,
            "confidence": self.confidence,
            "factors": self.factors,
            "market_average": self.market_average,
            "recommendation": self.recommendation,
        }


@dataclass
class TimeEstimate:
    """Delivery time estimate"""
    agent_address: str = ""
    estimated_hours: int = 0
    earliest_hours: int = 0
    latest_hours: int = 0
    current_queue: int = 0
    confidence: float = 0.0
    factors: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_address": self.agent_address,
            "estimated_hours": self.estimated_hours,
            "earliest_hours": self.earliest_hours,
            "latest_hours": self.latest_hours,
            "current_queue": self.current_queue,
            "confidence": self.confidence,
            "factors": self.factors,
        }


@dataclass
class DemandForecast:
    """Demand forecast for a skill"""
    skill_id: str = ""
    current_demand: float = 0.0  # 0.0 to 1.0
    predicted_demand: float = 0.0
    trend: str = "stable"  # rising, stable, declining
    peak_hours: List[int] = field(default_factory=list)  # Hours of day (0-23)
    seasonal_factor: float = 1.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "skill_id": self.skill_id,
            "current_demand": self.current_demand,
            "predicted_demand": self.predicted_demand,
            "trend": self.trend,
            "peak_hours": self.peak_hours,
            "seasonal_factor": self.seasonal_factor,
        }


@dataclass
class MatchingMetrics:
    """Metrics for matching quality"""
    total_matches: int = 0
    average_score: float = 0.0
    coverage_rate: float = 0.0  # % of tasks with good matches
    price_accuracy: float = 0.0  # % of predictions within 20% of actual
    delivery_accuracy: float = 0.0  # % of estimates within 20% of actual
    user_satisfaction: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_matches": self.total_matches,
            "average_score": self.average_score,
            "coverage_rate": self.coverage_rate,
            "price_accuracy": self.price_accuracy,
            "delivery_accuracy": self.delivery_accuracy,
            "user_satisfaction": self.user_satisfaction,
        }
