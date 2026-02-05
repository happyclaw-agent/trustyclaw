"""
Reputation Engine

Simple reputation scoring for ClawTrust agents.
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class Rating(Enum):
    """Rating values"""
    ONE_STAR = 1
    TWO_STARS = 2
    THREE_STARS = 3
    FOUR_STARS = 4
    FIVE_STARS = 5


@dataclass
class Review:
    """A review from a rental"""
    id: str = field(default_factory=lambda: f"review-{uuid.uuid4().hex[:8]}")
    provider: str = ""  # Wallet or name
    renter: str = ""
    skill: str = ""
    rating: int = 5
    completed_on_time: bool = True
    output_quality: str = "excellent"
    comment: str = ""
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    def validate(self) -> bool:
        """Validate review data"""
        if not self.provider:
            return False
        if not 1 <= self.rating <= 5:
            return False
        return True


@dataclass
class ReputationScore:
    """Reputation score for an agent"""
    agent_id: str
    total_reviews: int = 0
    average_rating: float = 0.0
    on_time_percentage: float = 100.0
    reputation_score: float = 85.0  # Final calculated score
    last_updated: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    reviews: list[Review] = field(default_factory=list)
    
    def calculate_score(self) -> float:
        """Calculate final reputation score"""
        if self.total_reviews == 0:
            return 50.0  # Default for new agents
        
        # Weighted formula
        rating_weight = 0.6
        ontime_weight = 0.3
        volume_weight = 0.1
        
        # Normalize rating (1-5 to 0-100)
        rating_score = (self.average_rating / 5.0) * 100
        
        # Volume bonus (cap at 100 reviews)
        volume_bonus = min(self.total_reviews / 100.0, 1.0) * 10
        
        # Calculate
        score = (
            rating_score * rating_weight +
            self.on_time_percentage * ontime_weight +
            volume_bonus * volume_weight
        )
        
        self.reputation_score = round(score, 1)
        self.last_updated = datetime.utcnow().isoformat()
        
        return self.reputation_score


class ReputationEngine:
    """
    Manages reputation scores for ClawTrust agents.
    
    For MVP: In-memory storage with simple formulas.
    Future: On-chain storage with ZK proofs.
    """
    
    def __init__(self):
        self._scores: dict[str, ReputationScore] = {}
        self._reviews: dict[str, list[Review]] = {}
        self._init_demo_scores()
    
    def _init_demo_scores(self):
        """Initialize demo reputation scores"""
        demos = [
            ("happyclaw-agent", 47, 4.7, 95.0),
            ("agent-alpha", 32, 4.4, 88.0),
            ("agent-beta", 28, 4.6, 91.0),
            ("agent-gamma", 15, 4.2, 85.0),
        ]
        
        for name, reviews, avg, ontime in demos:
            self._scores[name] = ReputationScore(
                agent_id=name,
                total_reviews=reviews,
                average_rating=avg,
                on_time_percentage=ontime,
            )
    
    def get_score(self, agent_id: str) -> Optional[ReputationScore]:
        """Get reputation score for an agent"""
        return self._scores.get(agent_id)
    
    def get_score_value(self, agent_id: str) -> float:
        """Get just the score value (0-100)"""
        score = self.get_score(agent_id)
        return score.reputation_score if score else 50.0
    
    def add_review(self, agent_id: str, review: Review) -> ReputationScore:
        """Add a review and update score"""
        # Get or create score
        if agent_id not in self._scores:
            self._scores[agent_id] = ReputationScore(agent_id=agent_id)
        
        score = self._scores[agent_id]
        
        # Add review
        if agent_id not in self._reviews:
            self._reviews[agent_id] = []
        self._reviews[agent_id].append(review)
        score.reviews.append(review)
        
        # Update counts
        score.total_reviews = len(score.reviews)
        
        # Calculate average rating
        if score.reviews:
            ratings = [r.rating for r in score.reviews]
            score.average_rating = sum(ratings) / len(ratings)
        
        # Calculate on-time percentage
        completed = [r for r in score.reviews if r.completed_on_time]
        if score.reviews:
            score.on_time_percentage = (len(completed) / len(score.reviews)) * 100
        
        # Recalculate final score
        score.calculate_score()
        
        return score
    
    def get_reviews(self, agent_id: str) -> list[Review]:
        """Get all reviews for an agent"""
        return self._reviews.get(agent_id, [])
    
    def get_top_agents(self, n: int = 10) -> list[tuple[str, float]]:
        """Get top N agents by reputation"""
        sorted_agents = sorted(
            self._scores.items(),
            key=lambda x: x[1].reputation_score,
            reverse=True
        )
        return [(agent, score.reputation_score) for agent, score in sorted_agents[:n]]
    
    def format_score(self, agent_id: str) -> str:
        """Format reputation for display"""
        score = self.get_score(agent_id)
        if not score:
            return f"@{agent_id}: No reputation yet (50/100)"
        
        # Create score bar
        bar_length = 20
        filled = int(score.reputation_score / 100 * bar_length)
        bar = "█" * filled + "░" * (bar_length - filled)
        
        stars = "⭐" * int(score.average_rating)
        
        return f"""
**@{agent_id}** Reputation

{bar} {score.reputation_score:.0f}/100

📊 Stats:
   Reviews: {score.total_reviews}
   Average Rating: {score.average_rating:.1f} {stars}
   On-Time Delivery: {score.on_time_percentage:.0f}%

📝 Recent Reviews:
{self._format_recent_reviews(score)}
""".strip()
    
    def _format_recent_reviews(self, score: ReputationScore, n: int = 3) -> str:
        """Format recent reviews"""
        if not score.reviews:
            return "   (No reviews yet)"
        
        recent = sorted(
            score.reviews,
            key=lambda r: r.created_at,
            reverse=True
        )[:n]
        
        lines = []
        for r in recent:
            lines.append(f"   • \"{r.comment[:50]}\" - ⭐{r.rating}")
        
        return "\n".join(lines)


# ============ Factory Functions ============

def get_reputation(agent_id: str) -> float:
    """Get reputation score for an agent"""
    engine = ReputationEngine()
    return engine.get_score_value(agent_id)


def add_review(agent_id: str, review: Review) -> float:
    """Add a review and return new score"""
    engine = ReputationEngine()
    return engine.add_review(agent_id, review).reputation_score


# ============ CLI ============

def demo():
    """Demo the reputation engine"""
    engine = ReputationEngine()
    
    print("Top Agents:")
    for agent, score in engine.get_top_agents():
        print(f"  @{agent}: {score:.0f}/100")
    
    print("\n" + engine.format_score("happyclaw-agent"))
    
    # Add a review
    review = Review(
        provider="happyclaw-agent",
        renter="agent-alpha",
        skill="image-generation",
        rating=5,
        completed_on_time=True,
        output_quality="excellent",
        comment="Amazing images! Fast delivery.",
    )
    engine.add_review("agent-alpha", review)
    
    print("\nAfter new review:")
    print(engine.format_score("agent-alpha"))


if __name__ == "__main__":
    demo()
