"""
Agent Registration Skill for TrustyClaw

Provides functionality for autonomous agents to register their capabilities,
manage auto-negotiation rules, and update their service offerings.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, List, Any
import uuid

from trustyclaw.models.skill import (
    SkillCapability,
    SkillSpec,
    PricingConfig,
    PricingModel,
    AvailabilitySchedule,
    QualityBadge,
    QualityCertification,
    AgentCapabilities,
)
from trustyclaw.models.negotiation import (
    NegotiationRules,
    NegotiationStrategy,
    AutoAcceptCriteria,
    PriceNegotiationRules,
    PriceRange,
    DeliveryPreferences,
    DeliveryPreference,
    NegotiationSession,
)


@dataclass
class AgentRegistration:
    """Registration record for an agent"""
    registration_id: str
    agent_address: str
    capabilities: AgentCapabilities
    negotiation_rules: Optional[NegotiationRules]
    status: str  # pending, active, suspended, revoked
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "registration_id": self.registration_id,
            "agent_address": self.agent_address,
            "capabilities": self.capabilities.to_dict(),
            "negotiation_rules": self.negotiation_rules.to_dict() if self.negotiation_rules else None,
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


class AgentRegistrationSkill:
    """
    Skill for registering and managing autonomous agents in TrustyClaw.
    
    Features:
    - Agent registration with capabilities
    - Capability updates
    - Auto-negotiation rule configuration
    - Agent profile management
    - Negotiation session handling
    """
    
    def __init__(self):
        self._registrations: Dict[str, AgentRegistration] = {}
        self._agent_by_address: Dict[str, str] = {}  # address -> registration_id
        self._negotiations: Dict[str, NegotiationSession] = {}
        self._init_mock_data()
    
    def _init_mock_data(self):
        """Initialize with sample registrations"""
        # Create sample registration
        registration_id = f"reg_{uuid.uuid4().hex[:16]}"
        
        # Sample skills
        skills = [
            SkillSpec(
                skill_id="test-skill-1",
                capability=SkillCapability.CODE_GENERATION,
                name="Python Development",
                description="Full Python development services including APIs, scripts, and automation",
                pricing=PricingConfig(
                    model=PricingModel.PER_TASK,
                    base_price=1000000,  # 1 USDC
                    min_price=800000,
                    max_price=1500000,
                ),
                estimated_duration_hours=4.0,
                tags=["Python", "Backend", "API"],
            ),
            SkillSpec(
                skill_id="test-skill-2",
                capability=SkillCapability.DATA_ANALYSIS,
                name="Data Analysis",
                description="Statistical analysis and visualization",
                pricing=PricingConfig(
                    model=PricingModel.PER_HOUR,
                    base_price=250000,  # 0.25 USDC per hour
                ),
                estimated_duration_hours=2.0,
                tags=["Data", "Analysis", "Pandas"],
            ),
        ]
        
        capabilities = AgentCapabilities(
            agent_address="TestAgent001",
            name="Test Auto Agent",
            bio="A test autonomous agent for development and testing",
            skills=skills,
            certifications=[],
            auto_negotiation=True,
            auto_accept_mandates=False,
            max_mandate_value=10000000,  # 10 USDC max
        )
        
        negotiation_rules = NegotiationRules(
            strategy=NegotiationStrategy.PRICE_NEGOTIATE,
            auto_accept=AutoAcceptCriteria(
                min_price_usdc=100000,  # 0.1 USDC
                max_price_usdc=5000000,  # 5 USDC
                require_deposit=True,
                require_escrow=True,
            ),
            price_rules=PriceNegotiationRules(
                strategy=PriceRange.FLEXIBLE_10_PERCENT,
                min_counter_offers=1,
                max_counter_offers=3,
            ),
            delivery_preferences=DeliveryPreferences(
                preference=DeliveryPreference.STANDARD,
                preferred_duration_seconds=14400,  # 4 hours
                max_duration_seconds=86400,  # 24 hours
            ),
        )
        
        registration = AgentRegistration(
            registration_id=registration_id,
            agent_address="TestAgent001",
            capabilities=capabilities,
            negotiation_rules=negotiation_rules,
            status="active",
        )
        
        self._registrations[registration_id] = registration
        self._agent_by_address["TestAgent001"] = registration_id
    
    # ============ Agent Registration ============
    
    def register_agent(
        self,
        name: str,
        bio: str,
        capabilities: List[SkillCapability],
        pricing: Dict[str, int],  # skill_id -> price in USDC lamports
        auto_accept: bool = False,
        max_mandate_value: int = None,
        agent_address: str = None,
    ) -> AgentRegistration:
        """
        Register a new autonomous agent with capabilities.
        
        Args:
            name: Agent name
            bio: Agent description
            capabilities: List of skill capabilities
            pricing: Dict mapping capability to price (in lamports)
            auto_accept: Whether to auto-accept mandates
            max_mandate_value: Maximum mandate value to accept
            agent_address: Optional agent address (generated if not provided)
            
        Returns:
            AgentRegistration record
        """
        # Generate agent address if not provided
        if agent_address is None:
            agent_address = f"agent_{uuid.uuid4().hex[:24]}"
        
        registration_id = f"reg_{uuid.uuid4().hex[:16]}"
        
        # Create skill specs from capabilities and pricing
        skill_specs = []
        for i, capability in enumerate(capabilities):
            skill_id = f"skill_{uuid.uuid4().hex[:8]}"
            skill_name = capability.value.replace("-", " ").title()
            
            skill_pricing = pricing.get(capability.value) or pricing.get(skill_id)
            base_price = skill_pricing if skill_pricing else 1000000  # Default 1 USDC
            
            skill_spec = SkillSpec(
                skill_id=skill_id,
                capability=capability,
                name=f"{skill_name} Service",
                description=f"Professional {skill_name} services",
                pricing=PricingConfig(
                    model=PricingModel.PER_TASK,
                    base_price=base_price,
                ),
                estimated_duration_hours=2.0,
            )
            skill_specs.append(skill_spec)
        
        # Create capabilities profile
        capabilities_profile = AgentCapabilities(
            agent_address=agent_address,
            name=name,
            bio=bio,
            skills=skill_specs,
            certifications=[],
            auto_negotiation=auto_accept,
            auto_accept_mandates=auto_accept,
            max_mandate_value=max_mandate_value,
        )
        
        # Create default negotiation rules if auto_accept
        negotiation_rules = None
        if auto_accept:
            negotiation_rules = NegotiationRules(
                strategy=NegotiationStrategy.AUTO_ACCEPT if auto_accept else NegotiationStrategy.MANUAL_REVIEW,
                auto_accept=AutoAcceptCriteria(
                    min_price_usdc=0,
                    max_price_usdc=max_mandate_value,
                    require_deposit=True,
                    require_escrow=True,
                ),
            )
        
        # Create registration
        registration = AgentRegistration(
            registration_id=registration_id,
            agent_address=agent_address,
            capabilities=capabilities_profile,
            negotiation_rules=negotiation_rules,
            status="active",
        )
        
        # Store registration
        self._registrations[registration_id] = registration
        self._agent_by_address[agent_address] = registration_id
        
        return registration
    
    def get_registration(self, agent_address: str) -> Optional[AgentRegistration]:
        """Get agent registration by address"""
        registration_id = self._agent_by_address.get(agent_address)
        if registration_id:
            return self._registrations.get(registration_id)
        return None
    
    def get_registration_by_id(self, registration_id: str) -> Optional[AgentRegistration]:
        """Get agent registration by ID"""
        return self._registrations.get(registration_id)
    
    def list_registrations(
        self,
        auto_negotiating_only: bool = False,
        status: str = None,
        limit: int = 100,
    ) -> List[AgentRegistration]:
        """List agent registrations"""
        registrations = list(self._registrations.values())
        
        if auto_negotiating_only:
            registrations = [
                r for r in registrations
                if r.capabilities.auto_negotiation
            ]
        
        if status:
            registrations = [r for r in registrations if r.status == status]
        
        return registrations[:limit]
    
    # ============ Capability Management ============
    
    def update_capabilities(
        self,
        agent_address: str,
        capabilities: List[SkillCapability],
        pricing: Dict[str, int] = None,
    ) -> AgentRegistration:
        """
        Update agent capabilities.
        
        Args:
            agent_address: Agent address
            capabilities: New list of skill capabilities
            pricing: Updated pricing (capability -> price)
            
        Returns:
            Updated AgentRegistration
        """
        registration = self.get_registration(agent_address)
        if not registration:
            raise ValueError(f"Agent not found: {agent_address}")
        
        # Update skills
        skill_specs = []
        for i, capability in enumerate(capabilities):
            skill_id = f"skill_{uuid.uuid4().hex[:8]}"
            skill_name = capability.value.replace("-", " ").title()
            
            skill_pricing = pricing.get(capability.value) if pricing else None
            base_price = skill_pricing if skill_pricing else 1000000
            
            skill_spec = SkillSpec(
                skill_id=skill_id,
                capability=capability,
                name=f"{skill_name} Service",
                description=f"Professional {skill_name} services",
                pricing=PricingConfig(
                    model=PricingModel.PER_TASK,
                    base_price=base_price,
                ),
                estimated_duration_hours=2.0,
            )
            skill_specs.append(skill_spec)
        
        registration.capabilities.skills = skill_specs
        registration.updated_at = datetime.utcnow().isoformat()
        
        return registration
    
    def add_skill(
        self,
        agent_address: str,
        capability: SkillCapability,
        name: str,
        description: str,
        price_usdc: int,
        estimated_hours: float = 2.0,
    ) -> SkillSpec:
        """Add a new skill to an agent"""
        registration = self.get_registration(agent_address)
        if not registration:
            raise ValueError(f"Agent not found: {agent_address}")
        
        skill_id = f"skill_{uuid.uuid4().hex[:8]}"
        
        skill_spec = SkillSpec(
            skill_id=skill_id,
            capability=capability,
            name=name,
            description=description,
            pricing=PricingConfig(
                model=PricingModel.PER_TASK,
                base_price=price_usdc,
            ),
            estimated_duration_hours=estimated_hours,
        )
        
        registration.capabilities.skills.append(skill_spec)
        registration.updated_at = datetime.utcnow().isoformat()
        
        return skill_spec
    
    def remove_skill(self, agent_address: str, skill_id: str) -> bool:
        """Remove a skill from an agent"""
        registration = self.get_registration(agent_address)
        if not registration:
            raise ValueError(f"Agent not found: {agent_address}")
        
        skills = registration.capabilities.skills
        for i, skill in enumerate(skills):
            if skill.skill_id == skill_id:
                skills.pop(i)
                registration.updated_at = datetime.utcnow().isoformat()
                return True
        
        return False
    
    # ============ Negotiation Rules ============
    
    def set_auto_negotiation(
        self,
        agent_address: str,
        rules: NegotiationRules,
    ) -> AgentRegistration:
        """
        Set auto-negotiation rules for an agent.
        
        Args:
            agent_address: Agent address
            rules: Negotiation rules
            
        Returns:
            Updated AgentRegistration
        """
        registration = self.get_registration(agent_address)
        if not registration:
            raise ValueError(f"Agent not found: {agent_address}")
        
        registration.negotiation_rules = rules
        registration.capabilities.auto_negotiation = (
            rules.strategy != NegotiationStrategy.MANUAL_REVIEW
        )
        registration.updated_at = datetime.utcnow().isoformat()
        
        return registration
    
    def enable_auto_accept(
        self,
        agent_address: str,
        min_price_usdc: int = 0,
        max_price_usdc: int = None,
        require_escrow: bool = True,
        require_deposit: bool = True,
    ) -> AgentRegistration:
        """Enable auto-accept for an agent"""
        registration = self.get_registration(agent_address)
        if not registration:
            raise ValueError(f"Agent not found: {agent_address}")
        
        rules = NegotiationRules(
            strategy=NegotiationStrategy.AUTO_ACCEPT,
            auto_accept=AutoAcceptCriteria(
                min_price_usdc=min_price_usdc,
                max_price_usdc=max_price_usdc,
                require_escrow=require_escrow,
                require_deposit=require_deposit,
            ),
        )
        
        return self.set_auto_negotiation(agent_address, rules)
    
    def disable_auto_negotiation(self, agent_address: str) -> AgentRegistration:
        """Disable auto-negotiation, require manual review"""
        registration = self.get_registration(agent_address)
        if not registration:
            raise ValueError(f"Agent not found: {agent_address}")
        
        rules = NegotiationRules(
            strategy=NegotiationStrategy.MANUAL_REVIEW,
        )
        
        return self.set_auto_negotiation(agent_address, rules)
    
    def configure_price_negotiation(
        self,
        agent_address: str,
        strategy: PriceRange,
        min_counter_offers: int = 1,
        max_counter_offers: int = 3,
    ) -> AgentRegistration:
        """Configure price negotiation rules"""
        registration = self.get_registration(agent_address)
        if not registration:
            raise ValueError(f"Agent not found: {agent_address}")
        
        price_rules = PriceNegotiationRules(
            strategy=strategy,
            min_counter_offers=min_counter_offers,
            max_counter_offers=max_counter_offers,
        )
        
        if registration.negotiation_rules is None:
            registration.negotiation_rules = NegotiationRules(
                strategy=NegotiationStrategy.PRICE_NEGOTIATE,
            )
        
        registration.negotiation_rules.price_rules = price_rules
        registration.updated_at = datetime.utcnow().isoformat()
        
        return registration
    
    # ============ Agent Status ============
    
    def suspend_agent(self, agent_address: str) -> AgentRegistration:
        """Suspend an agent"""
        registration = self.get_registration(agent_address)
        if not registration:
            raise ValueError(f"Agent not found: {agent_address}")
        
        registration.status = "suspended"
        registration.updated_at = datetime.utcnow().isoformat()
        
        return registration
    
    def activate_agent(self, agent_address: str) -> AgentRegistration:
        """Activate a suspended agent"""
        registration = self.get_registration(agent_address)
        if not registration:
            raise ValueError(f"Agent not found: {agent_address}")
        
        registration.status = "active"
        registration.updated_at = datetime.utcnow().isoformat()
        
        return registration
    
    def delete_registration(self, agent_address: str) -> bool:
        """Delete an agent registration"""
        registration_id = self._agent_by_address.get(agent_address)
        if registration_id:
            registration = self._registrations.pop(registration_id)
            self._agent_by_address.pop(agent_address)
            return True
        return False
    
    # ============ Negotiation Sessions ============
    
    def start_negotiation(
        self,
        agent_address: str,
        client_address: str,
        skill_id: str,
        initial_price: int,
        duration_seconds: int,
    ) -> NegotiationSession:
        """Start a negotiation session"""
        registration = self.get_registration(agent_address)
        if not registration:
            raise ValueError(f"Agent not found: {agent_address}")
        
        session_id = f"neg_{uuid.uuid4().hex[:16]}"
        
        session = NegotiationSession(
            session_id=session_id,
            agent_address=agent_address,
            client_address=client_address,
            skill_id=skill_id,
            status="active",
            agent_offer=initial_price,
            agent_duration=duration_seconds,
        )
        
        self._negotiations[session_id] = session
        
        return session
    
    def get_negotiation(self, session_id: str) -> Optional[NegotiationSession]:
        """Get a negotiation session"""
        return self._negotiations.get(session_id)
    
    def accept_offer(
        self,
        session_id: str,
        offerer: str,
        price: int,
        duration: int,
    ) -> NegotiationSession:
        """Accept an offer and finalize negotiation"""
        session = self._negotiations.get(session_id)
        if not session:
            raise ValueError(f"Negotiation not found: {session_id}")
        
        session.add_counter(offerer, price, duration)
        session.status = "accepted"
        session.updated_at = datetime.utcnow().isoformat()
        
        return session
    
    def reject_negotiation(self, session_id: str) -> NegotiationSession:
        """Reject a negotiation"""
        session = self._negotiations.get(session_id)
        if not session:
            raise ValueError(f"Negotiation not found: {session_id}")
        
        session.status = "rejected"
        session.updated_at = datetime.utcnow().isoformat()
        
        return session
    
    def get_agent_negotiations(
        self,
        agent_address: str,
        status: str = None,
    ) -> List[NegotiationSession]:
        """Get all negotiations for an agent"""
        negotiations = [
            n for n in self._negotiations.values()
            if n.agent_address == agent_address
        ]
        
        if status:
            negotiations = [n for n in negotiations if n.status == status]
        
        return negotiations
    
    # ============ Statistics ============
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get registration statistics"""
        registrations = list(self._registrations.values())
        
        auto_negotiating = sum(
            1 for r in registrations
            if r.capabilities.auto_negotiation
        )
        
        active = sum(1 for r in registrations if r.status == "active")
        
        return {
            "total_registrations": len(registrations),
            "active_agents": active,
            "auto_negotiating_agents": auto_negotiating,
            "total_negotiations": len(self._negotiations),
            "active_negotiations": sum(
                1 for n in self._negotiations.values()
                if n.status == "active"
            ),
        }
    
    # ============ Export ============
    
    def export_registration_json(self, agent_address: str = None) -> str:
        """Export registration(s) as JSON"""
        import json
        
        if agent_address:
            registration = self.get_registration(agent_address)
            data = [registration.to_dict()] if registration else []
        else:
            data = [r.to_dict() for r in self._registrations.values()]
        
        return json.dumps(data, indent=2)


def get_agent_registration_skill() -> AgentRegistrationSkill:
    """
    Get an AgentRegistrationSkill instance.
    
    Returns:
        Configured AgentRegistrationSkill
    """
    return AgentRegistrationSkill()
