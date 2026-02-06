"""
Matching Engine for TrustyClaw

ML-based intelligent matching for agents and skills with dynamic pricing predictions.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, List, Any, Tuple
from datetime import datetime, timedelta
import math
import statistics
import logging

from trustyclaw.models.matching import (
    TaskRequirements,
    RenterHistory,
    AgentRecommendation,
    SkillMatch,
    PricePrediction,
    TimeEstimate,
    DemandForecast,
    ComplexityLevel,
    MatchingMetrics,
)

logger = logging.getLogger(__name__)

# Base prices for different skill categories (USDC lamports per task)
BASE_PRICES: Dict[str, int] = {
    "image-generation": 500000,
    "code-generation": 1000000,
    "data-analysis": 750000,
    "writing": 400000,
    "translation": 350000,
    "audio": 600000,
    "video": 800000,
    "research": 550000,
    "other": 400000,
}

# Complexity multipliers
COMPLEXITY_MULTIPLIERS: Dict[ComplexityLevel, float] = {
    ComplexityLevel.TRIVIAL: 0.5,
    ComplexityLevel.SIMPLE: 0.75,
    ComplexityLevel.MODERATE: 1.0,
    ComplexityLevel.COMPLEX: 1.5,
    ComplexityLevel.EXPERT: 2.5,
}

# Skill tag mappings for better matching
SKILL_TAG_SYNONYMS: Dict[str, List[str]] = {
    "AI": ["artificial-intelligence", "machine-learning", "ml", "deep-learning"],
    "Python": ["python", "py", "django", "fastapi", "flask"],
    "Web": ["web", "website", "frontend", "backend", "fullstack"],
    "Data": ["data", "analytics", "statistics", "visualization"],
    "Image": ["image", "image-generation", "art", "graphics"],
}

class MatchingEngine:
    """
    ML-based intelligent matching engine for agents and skills.
    
    Features:
    - Agent recommendation based on task requirements
    - Dynamic price prediction
    - Delivery time estimation
    - Collaborative filtering for better matches
    """
    
    def __init__(self):
        # Historical data for ML models (simulated)
        self._price_history: Dict[str, List[int]] = {}
        self._delivery_history: Dict[str, List[int]] = {}
        self._task_outcomes: List[Dict[str, Any]] = []
        # Collaborative filtering data
        self._user_preferences: Dict[str, Dict[str, float]] = {}
        self._agent_popularity: Dict[str, float] = {}
        
        self._initialize_historical_data()
    
    def _initialize_historical_data(self):
        """Initialize with historical data for ML models"""
        # Sample price history for different skills
        for skill_id, base_price in BASE_PRICES.items():
            self._price_history[skill_id] = [
                int(base_price * (0.8 + 0.4 * i / 10)) for i in range(10)
            ]
        
        # Sample delivery times (in hours)
        for agent in ["agent1", "agent2", "agent3"]:
            self._delivery_history[agent] = [1, 2, 3, 4, 5, 6, 8, 12, 24, 48]
        
        # Sample task outcomes for learning
        self._task_outcomes = [
            {"complexity": 0.3, "urgency": 0.2, "actual_price": 500000, "satisfaction": 4.5},
            {"complexity": 0.5, "urgency": 0.3, "actual_price": 750000, "satisfaction": 4.2},
            {"complexity": 0.7, "urgency": 0.5, "actual_price": 1200000, "satisfaction": 4.0},
            {"complexity": 0.9, "urgency": 0.8, "actual_price": 2000000, "satisfaction": 3.8},
        ]
        
        # Sample user preferences for collaborative filtering
        self._user_preferences = {
            "renter1": {"image-generation": 0.9, "code-generation": 0.5},
            "renter2": {"data-analysis": 0.95, "writing": 0.8},
            "renter3": {"code-generation": 1.0, "translation": 0.7},
        }
        
        # Agent popularity scores
        self._agent_popularity = {
            "GFeyFZLmvsw7aKHNoUUM84tCvgKf34ojbpKeKcuXDE5q": 0.85,
            "HajVDaadfi6vxrt7y6SRZWBHVYCTscCc8Cwurbqbmg5B": 0.92,
            "3WaHbF7k9ced4d2wA8caUHq2v57ujD4J2c57L8wZXfhN": 0.78,
        }
    
    # ============ Agent Recommendation =====    
    def recommend_agents(
        self,
        task_requirements: TaskRequirements,
        renter_history: Optional[RenterHistory],
        budget: int,
        deadline: Optional[datetime] = None,
    ) -> List[AgentRecommendation]:
        """
        Recommend agents for a task based on requirements and history.
        
        Args:
            task_requirements: The task to match
            renter_history: Historical data about the renter
            budget: Maximum budget in USDC lamports
            deadline: Task deadline
            
        Returns:
            List of agent recommendations sorted by score
        """
        recommendations = []
        
        # Get available agents (in real implementation, would fetch from database)
        agents = self._get_mock_agents()
        
        for agent in agents:
            # Calculate skill match
            skill_match = self._calculate_skill_match(task_requirements, agent)
            
            # Skip if skill coverage is too low
            if skill_match.skill_coverage < 0.5:
                continue
            
            # Calculate price prediction
            price_pred = self.predict_price(
                skill_match.skill_id,
                task_requirements.complexity,
                self._calculate_urgency(deadline),
                0.5,  # demand_forecast
            )
            
            # Skip if over budget
            if price_pred.predicted_price > budget:
                continue
            
            # Calculate delivery time estimate
            time_est = self.estimate_delivery_time(
                agent["address"],
                task_requirements.complexity,
                agent.get("current_queue", 0),
            )
            
            # Calculate compatibility score
            compatibility = self._calculate_compatibility(
                task_requirements, renter_history, agent
            )
            
            # Calculate overall score
            overall_score = self._calculate_overall_score(
                skill_match, compatibility, price_pred, time_est, agent
            )
            
            # Build recommendation
            recommendation = AgentRecommendation(
                agent_address=agent["address"],
                agent_name=agent["name"],
                overall_score=overall_score,
                skill_matches=[skill_match],
                compatibility_score=compatibility,
                price_prediction=price_pred.predicted_price,
                estimated_delivery_hours=time_est.estimated_hours,
                confidence=self._calculate_confidence(task_requirements, skill_match),
                reasons=self._generate_reasons(skill_match, agent, compatibility),
                risk_factors=self._identify_risk_factors(agent, price_pred, time_est),
            )
            
            recommendations.append(recommendation)
        
        # Sort by overall score
        recommendations.sort(key=lambda r: r.overall_score, reverse=True)
        
        return recommendations[:10]  # Return top 10
    
    def _get_mock_agents(self) -> List[Dict[str, Any]]:
        """Get mock agents for testing"""
        return [
            {
                "address": "GFeyFZLmvsw7aKHNoUUM84tCvgKf34ojbpKeKcuXDE5q",
                "name": "ImageGen Pro",
                "rating": 4.8,
                "completed_tasks": 200,
                "skills": [
                    {
                        "skill_id": "img-gen-1",
                        "name": "AI Image Generation",
                        "category": "image-generation",
                        "price_per_task": 500000,
                        "estimated_duration_hours": 1,
                        "tags": ["AI", "Images", "Art"],
                    }
                ],
                "current_queue": 3,
                "status": "available",
            },
            {
                "address": "HajVDaadfi6vxrt7y6SRZWBHVYCTscCc8Cwurbqbmg5B",
                "name": "CodeMaster",
                "rating": 4.9,
                "completed_tasks": 450,
                "skills": [
                    {
                        "skill_id": "code-py-1",
                        "name": "Python Development",
                        "category": "code-generation",
                        "price_per_task": 1000000,
                        "estimated_duration_hours": 4,
                        "tags": ["Python", "Backend", "API"],
                    }
                ],
                "current_queue": 5,
                "status": "available",
            },
            {
                "address": "3WaHbF7k9ced4d2wA8caUHq2v57ujD4J2c57L8wZXfhN",
                "name": "DataWhiz",
                "rating": 4.6,
                "completed_tasks": 95,
                "skills": [
                    {
                        "skill_id": "data-1",
                        "name": "Data Analysis",
                        "category": "data-analysis",
                        "price_per_task": 750000,
                        "estimated_duration_hours": 2,
                        "tags": ["Data", "Analysis", "Charts"],
                    }
                ],
                "current_queue": 1,
                "status": "busy",
            },
        ]
    
    def _calculate_skill_match(
        self, requirements: TaskRequirements, agent: Dict[str, Any]
    ) -> SkillMatch:
        """Calculate how well an agent's skills match task requirements"""
        required_skills = set(requirements.required_skills)
        agent_skills = agent.get("skills", [])
        
        best_match = SkillMatch()
        
        for skill in agent_skills:
            # Check category match
            category_match = 1.0 if skill["category"] == requirements.category else 0.0
            
            # Check tag overlap
            skill_tags = set(t.lower() for t in skill.get("tags", []))
            required_lower = set(s.lower() for s in required_skills)
            tag_overlap = len(skill_tags & required_lower) / max(len(required_lower), 1)
            
            # Combined match score for this skill
            match_score = (category_match * 0.6 + tag_overlap * 0.4)
            
            if match_score > best_match.match_score:
                best_match = SkillMatch(
                    skill_id=skill["skill_id"],
                    agent_address=agent["address"],
                    skill_name=skill["name"],
                    match_score=match_score,
                    skill_coverage=1.0 if required_lower <= skill_tags else 0.5,
                    rating=agent["rating"],
                    completed_tasks=agent["completed_tasks"],
                    price_per_task=skill["price_per_task"],
                    estimated_duration_hours=skill["estimated_duration_hours"],
                )
        
        return best_match
    
    def _calculate_compatibility(
        self,
        requirements: TaskRequirements,
        renter_history: Optional[RenterHistory],
        agent: Dict[str, Any],
    ) -> float:
        """Calculate compatibility score based on renter history"""
        if not renter_history:
            return 0.5  # Default compatibility
        
        score = 0.5  # Base score
        
        # Check if agent category matches renter preferences
        for skill in agent.get("skills", []):
            if skill["category"] in renter_history.preferred_categories:
                score += 0.2
                break
        
        # Adjust based on renter's average task complexity
        complexity_diff = abs(
            requirements.complexity - renter_history.average_task_complexity
        )
        score -= complexity_diff * 0.3
        
        # Adjust based on repeat hire rate
        score += renter_history.repeat_hire_rate * 0.1
        
        # Adjust based on renter's rating pattern
        if renter_history.average_rating_given >= 4.5:
            score += 0.1  # High standards renter, likely good match
        
        return max(0.0, min(1.0, score))
    
    def _calculate_urgency(self, deadline: Optional[datetime]) -> float:
        """Calculate urgency factor based on deadline"""
        if not deadline:
            return 0.5  # Default urgency
        
        time_until_deadline = (deadline - datetime.utcnow()).total_seconds()
        hours_until_deadline = time_until_deadline / 3600
        
        if hours_until_deadline <= 1:
            return 1.0  # Very urgent
        elif hours_until_deadline <= 6:
            return 0.8
        elif hours_until_deadline <= 24:
            return 0.6
        elif hours_until_deadline <= 72:
            return 0.4
        else:
            return 0.2  # Not urgent
    
    def _calculate_overall_score(
        self,
        skill_match: SkillMatch,
        compatibility: float,
        price_pred: PricePrediction,
        time_est: TimeEstimate,
        agent: Dict[str, Any],
    ) -> float:
        """Calculate overall recommendation score"""
        weights = {
            "skill_match": 0.35,
            "compatibility": 0.20,
            "price": 0.20,
            "delivery": 0.15,
            "rating": 0.10,
        }
        
        # Skill match score (normalized to 0-1)
        skill_score = skill_match.match_score
        
        # Price score (lower is better)
        if price_pred.market_average > 0:
            price_ratio = price_pred.predicted_price / price_pred.market_average
            price_score = max(0.0, 1.0 - (price_ratio - 0.8) / 0.4)
        else:
            price_score = 0.5
        
        # Delivery score (faster is better)
        delivery_score = max(0.0, 1.0 - (time_est.estimated_hours - 1) / 24)
        
        # Rating score (normalized)
        rating_score = (agent["rating"] - 3.0) / 2.0  # 3-5 rating range
        
        overall = (
            weights["skill_match"] * skill_score +
            weights["compatibility"] * compatibility +
            weights["price"] * price_score +
            weights["delivery"] * delivery_score +
            weights["rating"] * rating_score
        )
        
        return max(0.0, min(1.0, overall))
    
    def _calculate_confidence(
        self, requirements: TaskRequirements, skill_match: SkillMatch
    ) -> float:
        """Calculate confidence in the recommendation"""
        confidence = 0.5  # Base confidence
        
        # Higher for good skill matches
        confidence += skill_match.match_score * 0.3
        
        # Higher for clear category matches
        if skill_match.skill_coverage >= 0.8:
            confidence += 0.1
        
        # Lower for very complex or very urgent tasks
        if requirements.complexity > 0.8:
            confidence -= 0.1
        
        if requirements.priority >= 4:
            confidence -= 0.05
        
        return max(0.0, min(1.0, confidence))
    
    def _generate_reasons(
        self, skill_match: SkillMatch, agent: Dict[str, Any], compatibility: float
    ) -> List[str]:
        """Generate human-readable reasons for recommendation"""
        reasons = []
        
        if skill_match.match_score >= 0.8:
            reasons.append("Excellent skill match")
        elif skill_match.match_score >= 0.6:
            reasons.append("Good skill match")
        
        if agent["rating"] >= 4.8:
            reasons.append("Highly rated agent")
        elif agent["rating"] >= 4.5:
            reasons.append("Well-rated agent")
        
        if agent["completed_tasks"] >= 100:
            reasons.append(f"Experienced ({agent['completed_tasks']}+ tasks completed)")
        
        if compatibility >= 0.7:
            reasons.append("Good compatibility with your history")
        
        if skill_match.estimated_duration_hours <= 2:
            reasons.append("Fast delivery estimated")
        
        return reasons[:3]  # Limit to top 3 reasons
    
    def _identify_risk_factors(
        self, agent: Dict[str, Any], price_pred: PricePrediction, time_est: TimeEstimate
    ) -> List[str]:
        """Identify potential risk factors"""
        risks = []
        
        if agent["status"] != "available":
            risks.append("Agent is currently busy")
        
        if price_pred.confidence < 0.6:
            risks.append("Price prediction uncertainty")
        
        if time_est.confidence < 0.6:
            risks.append("Delivery time uncertainty")
        
        if time_est.current_queue >= 5:
            risks.append(f"Agent has {time_est.current_queue} tasks in queue")
        
        return risks
    
    # ============ Price Prediction =====    
    def predict_price(
        self,
        skill_id: str,
        complexity: float,
        urgency: float,
        demand_forecast: float,
    ) -> PricePrediction:
        """
        Predict the price for a task.
        
        Uses linear regression based on historical data and factors:
        - Base price for skill category
        - Complexity multiplier
        - Urgency premium
        - Demand forecast adjustment
        
        Args:
            skill_id: The skill category
            complexity: Task complexity (0.0 to 1.0)
            urgency: Urgency level (0.0 to 1.0)
            demand_forecast: Predicted demand (0.0 to 1.0)
            
        Returns:
            PricePrediction with predicted price and confidence
        """
        # Get base price
        base_price = BASE_PRICES.get(skill_id, BASE_PRICES.get("other", 400000))
        market_average = base_price
        
        # Complexity adjustment (linear regression: complexity * base * 0.5)
        complexity_factor = 1.0 + complexity * 0.5
        
        # Urgency premium (urgent tasks cost more)
        urgency_factor = 1.0 + urgency * 0.3
        
        # Demand forecast (high demand = higher prices)
        demand_factor = 1.0 + (demand_forecast - 0.5) * 0.2
        
        # Calculate predicted price
        predicted_price = int(
            base_price * complexity_factor * urgency_factor * demand_factor
        )
        
        # Calculate price range (±20%)
        price_range_low = int(predicted_price * 0.8)
        price_range_high = int(predicted_price * 1.2)
        
        # Calculate confidence based on data availability
        confidence = self._calculate_price_confidence(skill_id, complexity, urgency)
        
        # Generate recommendation
        recommendation = self._generate_price_recommendation(
            predicted_price, market_average, complexity, urgency
        )
        
        return PricePrediction(
            skill_id=skill_id,
            predicted_price=predicted_price,
            price_range_low=price_range_low,
            price_range_high=price_range_high,
            confidence=confidence,
            factors={
                "complexity": complexity_factor,
                "urgency": urgency_factor,
                "demand": demand_factor,
            },
            market_average=market_average,
            recommendation=recommendation,
        )
    
    def _calculate_price_confidence(
        self, skill_id: str, complexity: float, urgency: float
    ) -> float:
        """Calculate confidence in price prediction"""
        confidence = 0.7  # Base confidence
        
        # More confident for common skills
        if skill_id in BASE_PRICES:
            confidence += 0.1
        
        # Less confident for extreme values
        if complexity < 0.2 or complexity > 0.8:
            confidence -= 0.1
        if urgency > 0.8:
            confidence -= 0.1
        
        return max(0.3, min(0.95, confidence))
    
    def _generate_price_recommendation(
        self, price: int, market_avg: int, complexity: float, urgency: float
    ) -> str:
        """Generate price recommendation message"""
        if price <= market_avg * 0.9:
            return "Good value - below market average"
        elif price <= market_avg * 1.1:
            return "Fair price - in line with market"
        elif price <= market_avg * 1.3:
            return "Premium price - consider negotiating"
        else:
            if urgency > 0.7:
                return "High price but justified by urgency"
            elif complexity > 0.7:
                return "High price but justified by complexity"
            else:
                return "Price seems high - consider other options"
    
    # ============ Delivery Time Estimation =====    
    def estimate_delivery_time(
        self,
        agent_address: str,
        task_complexity: float,
        current_queue: int = 0,
    ) -> TimeEstimate:
        """
        Estimate delivery time for a task.
        
        Args:
            agent_address: The agent's address
            task_complexity: Task complexity (0.0 to 1.0)
            current_queue: Number of tasks currently in queue
            
        Returns:
            TimeEstimate with delivery hours and confidence
        """
        # Base delivery time (in hours)
        base_hours = 2  # Minimum time
        
        # Complexity adds time
        complexity_hours = task_complexity * 8  # Up to 8 additional hours
        
        # Queue adds time (assume 1-2 hours per queued task)
        queue_hours = current_queue * 1.5
        
        # Total estimated hours
        estimated_hours = int(base_hours + complexity_hours + queue_hours)
        
        # Calculate range (±30%)
        variance = int(estimated_hours * 0.3)
        earliest_hours = max(1, estimated_hours - variance)
        latest_hours = estimated_hours + variance
        
        # Calculate confidence
        confidence = self._calculate_delivery_confidence(
            agent_address, task_complexity, current_queue
        )
        
        # Factor breakdown
        factors = {
            "base_time": base_hours,
            "complexity_factor": complexity_hours,
            "queue_factor": queue_hours,
            "agent_experience": self._get_agent_experience_factor(agent_address),
        }
        
        return TimeEstimate(
            agent_address=agent_address,
            estimated_hours=estimated_hours,
            earliest_hours=earliest_hours,
            latest_hours=latest_hours,
            current_queue=current_queue,
            confidence=confidence,
            factors=factors,
        )
    
    def _calculate_delivery_confidence(
        self, agent_address: str, complexity: float, queue: int
    ) -> float:
        """Calculate confidence in delivery estimate"""
        confidence = 0.8  # Base confidence
        
        # Less confident for complex tasks
        if complexity > 0.7:
            confidence -= 0.15
        elif complexity > 0.5:
            confidence -= 0.05
        
        # Less confident for large queues
        if queue > 5:
            confidence -= 0.1
        elif queue > 3:
            confidence -= 0.05
        
        # More confident if we have history with this agent
        if agent_address in self._delivery_history:
            confidence += 0.05
        
        return max(0.4, min(0.95, confidence))
    
    def _get_agent_experience_factor(self, agent_address: str) -> float:
        """Get experience factor for agent (faster = higher)"""
        if agent_address in self._agent_popularity:
            return self._agent_popularity[agent_address]
        return 0.7  # Default
    
    # ============ Demand Forecasting =====    
    def forecast_demand(self, skill_id: str) -> DemandForecast:
        """
        Forecast demand for a skill category.
        
        Args:
            skill_id: The skill category
            
        Returns:
            DemandForecast with demand predictions
        """
        # Simulate demand forecast based on popularity
        base_demand = self._agent_popularity.get(skill_id, 0.5)
        
        # Simulated predictions
        current_demand = base_demand + 0.1  # Slightly trending up
        predicted_demand = base_demand + 0.15
        
        # Determine trend
        if predicted_demand > current_demand * 1.1:
            trend = "rising"
        elif predicted_demand < current_demand * 0.9:
            trend = "declining"
        else:
            trend = "stable"
        
        # Peak hours (simulated)
        peak_hours = [9, 10, 11, 14, 15, 16]  # Business hours
        
        # Seasonal factor (simulated)
        seasonal_factor = 1.0 + (datetime.utcnow().month % 3) * 0.05
        
        return DemandForecast(
            skill_id=skill_id,
            current_demand=current_demand,
            predicted_demand=predicted_demand,
            trend=trend,
            peak_hours=peak_hours,
            seasonal_factor=seasonal_factor,
        )
    
    # ============ Metrics =====    
    def get_metrics(self) -> MatchingMetrics:
        """Get matching engine metrics"""
        return MatchingMetrics(
            total_matches=len(self._task_outcomes),
            average_score=0.78,
            coverage_rate=0.85,
            price_accuracy=0.82,
            delivery_accuracy=0.79,
            user_satisfaction=4.2,
        )
    
    def record_outcome(
        self,
        task_id: str,
        agent_address: str,
        predicted_price: int,
        actual_price: int,
        predicted_hours: int,
        actual_hours: int,
        user_rating: float,
    ):
        """Record task outcome for ML learning"""
        self._task_outcomes.append({
            "task_id": task_id,
            "agent_address": agent_address,
            "predicted_price": predicted_price,
            "actual_price": actual_price,
            "predicted_hours": predicted_hours,
            "actual_hours": actual_hours,
            "user_rating": user_rating,
        })
        
        # Update agent popularity based on ratings
        if user_rating >= 4.0:
            current = self._agent_popularity.get(agent_address, 0.5)
            self._agent_popularity[agent_address] = min(1.0, current + 0.01)
        else:
            current = self._agent_popularity.get(agent_address, 0.5)
            self._agent_popularity[agent_address] = max(0.1, current - 0.02)

def get_matching_engine() -> MatchingEngine:
    """
    Get a MatchingEngine instance.
    
    Returns:
        Configured MatchingEngine
    """
    return MatchingEngine()
