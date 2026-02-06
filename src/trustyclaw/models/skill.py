"""
Skill Capability Models for TrustyClaw

Defines skill capabilities, pricing models, availability schedules, 
and quality certifications for autonomous agents.
"""

from dataclasses import dataclass, field
from datetime import datetime, time
from enum import Enum
from typing import Optional, List, Dict, Any
import uuid


class SkillCapability(Enum):
    """Enumeration of skill capabilities agents can have"""
    # Core AI capabilities
    TEXT_GENERATION = "text-generation"
    CODE_GENERATION = "code-generation"
    IMAGE_GENERATION = "image-generation"
    AUDIO_GENERATION = "audio-generation"
    VIDEO_GENERATION = "video-generation"
    TRANSLATION = "translation"
    SUMMARIZATION = "summarization"
    
    # Analysis capabilities
    DATA_ANALYSIS = "data-analysis"
    SENTIMENT_ANALYSIS = "sentiment-analysis"
    PATTERN_RECOGNITION = "pattern-recognition"
    PREDICTION = "prediction"
    
    # Research capabilities
    WEB_SEARCH = "web-search"
    DOCUMENT_ANALYSIS = "document-analysis"
    FACT_CHECKING = "fact-checking"
    
    # Specialized capabilities
    REASONING = "reasoning"
    PLANNING = "planning"
    CREATIVE_WRITING = "creative-writing"
    TECHNICAL_WRITING = "technical-writing"
    
    # Autonomous capabilities
    SELF_IMPROVEMENT = "self-improvement"
    TASK_AUTONOMY = "task-autonomy"
    MULTI_STEP_EXECUTION = "multi-step-execution"


class PricingModel(Enum):
    """Pricing models for skills"""
    PER_TASK = "per-task"
    PER_TOKEN = "per-token"
    PER_HOUR = "per-hour"
    PER_WORD = "per-word"
    SUBSCRIPTION = "subscription"
    CUSTOM = "custom"


class AvailabilityStatus(Enum):
    """Agent availability status"""
    AVAILABLE = "available"
    BUSY = "busy"
    OFFLINE = "offline"
    MAINTENANCE = "maintenance"


class QualityCertification(Enum):
    """Quality certifications agents can have"""
    VERIFIED = "verified"
    EXPERT = "expert"
    PREMIUM = "premium"
    NEW = "new"


@dataclass
class PricingConfig:
    """Pricing configuration for a skill"""
    model: PricingModel
    base_price: int  # Price in USDC lamports (1 USDC = 1,000,000 lamports)
    min_price: Optional[int] = None  # For negotiation
    max_price: Optional[int] = None  # For negotiation
    token_limit: Optional[int] = None  # For per-token pricing
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "model": self.model.value,
            "base_price": self.base_price,
            "min_price": self.min_price,
            "max_price": self.max_price,
            "token_limit": self.token_limit,
        }


@dataclass
class AvailabilitySchedule:
    """Weekly availability schedule for an agent"""
    monday_start: Optional[time] = None
    monday_end: Optional[time] = None
    tuesday_start: Optional[time] = None
    tuesday_end: Optional[time] = None
    wednesday_start: Optional[time] = None
    wednesday_end: Optional[time] = None
    thursday_start: Optional[time] = None
    thursday_end: Optional[time] = None
    friday_start: Optional[time] = None
    friday_end: Optional[time] = None
    saturday_start: Optional[time] = None
    saturday_end: Optional[time] = None
    sunday_start: Optional[time] = None
    sunday_end: Optional[time] = None
    timezone: str = "UTC"
    
    def is_available_at(self, dt: datetime) -> bool:
        """Check if agent is available at a given datetime"""
        # Get the day and time
        day_map = {
            0: ("monday_start", "monday_end"),
            1: ("tuesday_start", "tuesday_end"),
            2: ("wednesday_start", "wednesday_end"),
            3: ("thursday_start", "thursday_end"),
            4: ("friday_start", "friday_end"),
            5: ("saturday_start", "saturday_end"),
            6: ("sunday_start", "sunday_end"),
        }
        
        start_key, end_key = day_map.get(dt.weekday(), (None, None))
        if start_key is None:
            return False
        
        start_time = getattr(self, start_key)
        end_time = getattr(self, end_key)
        
        if start_time is None or end_time is None:
            return False
        
        current_time = dt.time()
        return start_time <= current_time <= end_time
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "monday": {"start": str(self.monday_start) if self.monday_start else None,
                      "end": str(self.monday_end) if self.monday_end else None},
            "tuesday": {"start": str(self.tuesday_start) if self.tuesday_start else None,
                       "end": str(self.tuesday_end) if self.tuesday_end else None},
            "wednesday": {"start": str(self.wednesday_start) if self.wednesday_start else None,
                         "end": str(self.wednesday_end) if self.wednesday_end else None},
            "thursday": {"start": str(self.thursday_start) if self.thursday_start else None,
                        "end": str(self.thursday_end) if self.thursday_end else None},
            "friday": {"start": str(self.friday_start) if self.friday_start else None,
                      "end": str(self.friday_end) if self.friday_end else None},
            "saturday": {"start": str(self.saturday_start) if self.saturday_start else None,
                        "end": str(self.saturday_end) if self.saturday_end else None},
            "sunday": {"start": str(self.sunday_start) if self.sunday_start else None,
                      "end": str(self.sunday_end) if self.sunday_end else None},
            "timezone": self.timezone,
        }


@dataclass
class QualityBadge:
    """Quality certification badge"""
    certification: QualityCertification
    issued_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    expires_at: Optional[str] = None
    issuer: str = "TrustyClaw"
    score: float = 0.0
    verified: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "certification": self.certification.value,
            "issued_at": self.issued_at,
            "expires_at": self.expires_at,
            "issuer": self.issuer,
            "score": self.score,
            "verified": self.verified,
        }


@dataclass
class SkillSpec:
    """Specification for a skill offered by an agent"""
    skill_id: str
    capability: SkillCapability
    name: str
    description: str
    pricing: PricingConfig
    estimated_duration_hours: float
    availability: Optional[AvailabilitySchedule] = None
    quality_badges: List[QualityBadge] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    examples: List[str] = field(default_factory=list)
    requirements: List[str] = field(default_factory=list)
    rating: float = 0.0
    review_count: int = 0
    completed_tasks: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "skill_id": self.skill_id,
            "capability": self.capability.value,
            "name": self.name,
            "description": self.description,
            "pricing": self.pricing.to_dict(),
            "estimated_duration_hours": self.estimated_duration_hours,
            "availability": self.availability.to_dict() if self.availability else None,
            "quality_badges": [qb.to_dict() for qb in self.quality_badges],
            "tags": self.tags,
            "examples": self.examples,
            "requirements": self.requirements,
            "rating": self.rating,
            "review_count": self.review_count,
            "completed_tasks": self.completed_tasks,
        }


@dataclass
class AgentCapabilities:
    """Complete capabilities profile for an autonomous agent"""
    agent_address: str
    name: str
    bio: str
    skills: List[SkillSpec]
    certifications: List[QualityBadge]
    auto_negotiation: bool = False
    auto_accept_mandates: bool = False
    max_mandate_value: Optional[int] = None
    preferred_mandate_duration_seconds: Optional[int] = None
    languages: List[str] = field(default_factory=lambda: ["English"])
    website: Optional[str] = None
    avatar_url: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_address": self.agent_address,
            "name": self.name,
            "bio": self.bio,
            "skills": [s.to_dict() for s in self.skills],
            "certifications": [c.to_dict() for c in self.certifications],
            "auto_negotiation": self.auto_negotiation,
            "auto_accept_mandates": self.auto_accept_mandates,
            "max_mandate_value": self.max_mandate_value,
            "preferred_mandate_duration_seconds": self.preferred_mandate_duration_seconds,
            "languages": self.languages,
            "website": self.website,
            "avatar_url": self.avatar_url,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
