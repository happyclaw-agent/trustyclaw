"""
Slashing Mechanism for TrustyClaw

Purpose:
    Handles reputation slashing for contract violations.
    Supports automatic and community-voted slashing.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional
import uuid


class SlashReason(Enum):
    """Reasons for slashing"""
    NON_DELIVERY = "non_delivery"
    LATE_DELIVERY = "late_delivery"
    LOW_QUALITY = "low_quality"
    NON_PAYMENT = "non_payment"
    BAD_FAITH = "bad_faith"
    FRAUD = "fraud"
    SPAM = "spam"


class SlashStatus(Enum):
    """Status of a slash proposal"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXECUTED = "executed"
    EXPIRED = "expired"


@dataclass
class SlashProposal:
    """A proposal to slash a participant's reputation."""
    proposal_id: str
    mandate_id: str
    target: str
    slash_type: str
    reason: SlashReason
    slash_percentage: float
    proposer: str
    votes_for: int = 0
    votes_against: int = 0
    status: SlashStatus = SlashStatus.PENDING
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    expires_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    evidence: List[str] = field(default_factory=list)
    voters: Dict[str, bool] = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        return {
            "proposal_id": self.proposal_id,
            "mandate_id": self.mandate_id,
            "target": self.target,
            "slash_type": self.slash_type,
            "reason": self.reason.value,
            "slash_percentage": self.slash_percentage,
            "proposer": self.proposer,
            "votes_for": self.votes_for,
            "votes_against": self.votes_against,
            "status": self.status.value,
            "created_at": self.created_at,
            "expires_at": self.expires_at,
            "evidence": self.evidence,
        }
    
    def is_expired(self) -> bool:
        """Check if voting period has expired"""
        return datetime.utcnow() > datetime.fromisoformat(self.expires_at)


@dataclass
class SlashResult:
    """Result of executing a slash."""
    success: bool
    reputation_loss: float
    stake_loss: float
    message: str
    proposal_id: str = ""


class SlashingMechanism:
    """
    Manages reputation slashing for TrustyClaw.
    
    Features:
    - Create slash proposals
    - Community voting on proposals
    - Automatic slashing for clear violations
    """
    
    VOTING_PERIOD_HOURS = 48
    QUORUM = 5
    SUPERMJORITY = 0.6
    
    def __init__(self):
        """Initialize slashing mechanism"""
        self._proposals: Dict[str, SlashProposal] = {}
        self._slash_history: List[dict] = []
    
    def create_proposal(
        self,
        mandate_id: str,
        target: str,
        slash_type: str,
        reason: SlashReason,
        slash_percentage: float,
        proposer: str,
        evidence: List[str] = None,
        voting_period_hours: int = None,
    ) -> SlashProposal:
        """Create a new slash proposal."""
        proposal_id = f"slash-{uuid.uuid4().hex[:12]}"
        
        hours = voting_period_hours or self.VOTING_PERIOD_HOURS
        expires_at = datetime.utcnow() + datetime.timedelta(hours=hours)
        
        proposal = SlashProposal(
            proposal_id=proposal_id,
            mandate_id=mandate_id,
            target=target,
            slash_type=slash_type,
            reason=reason,
            slash_percentage=min(slash_percentage, 0.5),
            proposer=proposer,
            evidence=evidence or [],
            expires_at=expires_at.isoformat(),
        )
        
        self._proposals[proposal_id] = proposal
        return proposal
    
    def vote(
        self,
        proposal_id: str,
        voter: str,
        support: bool,
    ) -> SlashProposal:
        """Vote on a slash proposal."""
        proposal = self._get_proposal(proposal_id)
        
        if proposal.is_expired():
            raise ValueError(f"Proposal {proposal_id} has expired")
        
        if voter == proposal.target:
            raise ValueError("Cannot vote on your own slash proposal")
        
        proposal.voters[voter] = support
        
        proposal.votes_for = sum(1 for v in proposal.voters.values() if v)
        proposal.votes_against = sum(1 for v in proposal.voters.values() if not v)
        
        return proposal
    
    def get_proposal_status(self, proposal_id: str) -> SlashStatus:
        """Get current status of a proposal"""
        proposal = self._get_proposal(proposal_id)
        
        if proposal.is_expired():
            proposal.status = SlashStatus.EXPIRED
            return SlashStatus.EXPIRED
        
        total_votes = proposal.votes_for + proposal.votes_against
        if total_votes < self.QUORUM:
            return SlashStatus.PENDING
        
        if proposal.votes_for / total_votes >= self.SUPERMJORITY:
            proposal.status = SlashStatus.APPROVED
        else:
            proposal.status = SlashStatus.REJECTED
        
        return proposal.status
    
    def slash_provider(
        self,
        mandate_id: str,
        percentage: float,
        reason: SlashReason = SlashReason.NON_DELIVERY,
        evidence: List[str] = None,
    ) -> SlashResult:
        """Slash a provider's reputation."""
        proposal = self.create_proposal(
            mandate_id=mandate_id,
            target="",
            slash_type="provider",
            reason=reason,
            slash_percentage=percentage,
            proposer="auto",
            evidence=evidence,
        )
        
        return SlashResult(
            success=True,
            reputation_loss=percentage * 30,
            stake_loss=percentage * 1000,
            message=f"Provider slashed {percentage*100}% for {reason.value}",
            proposal_id=proposal.proposal_id,
        )
    
    def slash_renter(
        self,
        mandate_id: str,
        percentage: float,
        reason: SlashReason = SlashReason.NON_PAYMENT,
        evidence: List[str] = None,
    ) -> SlashResult:
        """Slash a renter's reputation."""
        return SlashResult(
            success=True,
            reputation_loss=percentage * 20,
            stake_loss=percentage * 500,
            message=f"Renter slashed {percentage*100}% for {reason.value}",
            proposal_id="",
        )
    
    def execute_slash(self, proposal_id: str) -> SlashResult:
        """Execute an approved slash proposal."""
        proposal = self._get_proposal(proposal_id)
        
        if proposal.status != SlashStatus.APPROVED:
            raise ValueError(f"Proposal {proposal_id} is not approved")
        
        reputation_loss = proposal.slash_percentage * 25
        stake_loss = proposal.slash_percentage * 750
        
        slash_record = {
            "proposal_id": proposal_id,
            "target": proposal.target,
            "slash_type": proposal.slash_type,
            "reason": proposal.reason.value,
            "percentage": proposal.slash_percentage,
            "reputation_loss": reputation_loss,
            "stake_loss": stake_loss,
            "executed_at": datetime.utcnow().isoformat(),
        }
        self._slash_history.append(slash_record)
        
        proposal.status = SlashStatus.EXECUTED
        
        return SlashResult(
            success=True,
            reputation_loss=reputation_loss,
            stake_loss=stake_loss,
            message=f"Slash executed: {proposal.target} lost {reputation_loss:.1f} reputation",
            proposal_id=proposal_id,
        )
    
    def get_proposal(self, proposal_id: str) -> Optional[SlashProposal]:
        """Get proposal by ID"""
        return self._proposals.get(proposal_id)
    
    def get_pending_proposals(self) -> List[SlashProposal]:
        """Get all pending proposals"""
        return [
            p for p in self._proposals.values()
            if p.status == SlashStatus.PENDING
            and not p.is_expired()
        ]
    
    def _get_proposal(self, proposal_id: str) -> SlashProposal:
        """Get proposal or raise error"""
        if proposal_id not in self._proposals:
            raise ValueError(f"Proposal {proposal_id} not found")
        return self._proposals[proposal_id]
    
    def get_slash_history(self, target: str = None) -> List[dict]:
        """Get slash history."""
        if target:
            return [s for s in self._slash_history if s["target"] == target]
        return self._slash_history
    
    def calculate_recovery(
        self,
        current_score: float,
        days_since_slash: int,
    ) -> float:
        """Calculate reputation recovery over time."""
        recovery = min(days_since_slash, 30)
        recovered = recovery * 1.0
        return min(current_score + recovered, 50.0)


def create_auto_slash(
    mandate_id: str,
    target: str,
    slash_type: str,
    reason: SlashReason,
    severity: str = "medium",
) -> SlashProposal:
    """Create an automatic slash proposal based on severity."""
    percentages = {"low": 0.1, "medium": 0.2, "high": 0.3}
    percentage = percentages.get(severity, 0.2)
    
    slashing = SlashingMechanism()
    return slashing.create_proposal(
        mandate_id=mandate_id,
        target=target,
        slash_type=slash_type,
        reason=reason,
        slash_percentage=percentage,
        proposer="auto-system",
    )
