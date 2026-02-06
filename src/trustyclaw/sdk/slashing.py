"""
Slashing Mechanism for TrustyClaw

Purpose:
    Handles reputation slashing for contract violations.
    Supports automatic and community-voted slashing.
<<<<<<< HEAD
=======
    
Capabilities:
    - Slash provider for non-delivery
    - Slash renter for non-payment
    - Community voting on slash decisions
    - Reputation recovery mechanisms
    
Usage:
    >>> slashing = SlashingMechanism()
    >>> result = slashing.slash_provider("mandate-id", 0.2)  # 20% slash
    >>> print(result)
>>>>>>> main
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
<<<<<<< HEAD
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXECUTED = "executed"
    EXPIRED = "expired"
=======
    PENDING = "pending"      # Awaiting votes
    APPROVED = "approved"     # Votes passed
    REJECTED = "rejected"    # Votes failed
    EXECUTED = "executed"    # Slash applied
    EXPIRED = "expired"      # Voting period ended
>>>>>>> main


@dataclass
class SlashProposal:
<<<<<<< HEAD
    """A proposal to slash a participant's reputation."""
    proposal_id: str
    mandate_id: str
    target: str
    slash_type: str
=======
    """
    A proposal to slash a participant's reputation.
    
    Attributes:
        proposal_id: Unique proposal identifier
        mandate_id: Related mandate
        target: Wallet address to be slashed
        slash_type: Provider or renter
        reason: Reason for slashing
        slash_percentage: Percentage of stake to slash (0-1)
        proposer: Who proposed the slash
        votes_for: Count of supporting votes
        votes_against: Count of opposing votes
        status: Current status
        created_at: Creation timestamp
        expires_at: Voting deadline
        evidence: List of evidence hashes
    """
    proposal_id: str
    mandate_id: str
    target: str
    slash_type: str  # "provider" or "renter"
>>>>>>> main
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
<<<<<<< HEAD
    """Result of executing a slash."""
=======
    """
    Result of executing a slash.
    
    Attributes:
        success: Whether slash was applied
        reputation_loss: Points lost from reputation
        stake_loss: Amount slashed from stake
        message: Human-readable result
    """
>>>>>>> main
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
<<<<<<< HEAD
=======
    - Reputation recovery over time
    
    Voting Rules:
    - Quorum: 5 votes minimum
    - Super-majority: 60% for approval
    - Voting period: 48 hours
    - Self-voting not allowed
    
    Usage:
        >>> slashing = SlashingMechanism()
        >>> proposal = slashing.create_proposal(
        ...     mandate_id="mandate-123",
        ...     target="wallet-address",
        ...     slash_type="provider",
        ...     reason=SlashReason.NON_DELIVERY,
        ...     percentage=0.2,
        ...     proposer="voter-wallet",
        ... )
>>>>>>> main
    """
    
    VOTING_PERIOD_HOURS = 48
    QUORUM = 5
<<<<<<< HEAD
    SUPERMJORITY = 0.6
=======
    SUPERMJORITY = 0.6  # 60% required for approval
>>>>>>> main
    
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
<<<<<<< HEAD
        """Create a new slash proposal."""
        proposal_id = f"slash-{uuid.uuid4().hex[:12]}"
        
=======
        """
        Create a new slash proposal.
        
        Args:
            mandate_id: Related mandate
            target: Wallet to be slashed
            slash_type: "provider" or "renter"
            reason: Reason for slash
            slash_percentage: Percentage to slash (0-1)
            proposer: Proposer's wallet
            evidence: Evidence hashes
            voting_period_hours: Override default voting period
            
        Returns:
            Created SlashProposal
        """
        proposal_id = f"slash-{uuid.uuid4().hex[:12]}"
        
        # Calculate expiration
>>>>>>> main
        hours = voting_period_hours or self.VOTING_PERIOD_HOURS
        expires_at = datetime.utcnow() + datetime.timedelta(hours=hours)
        
        proposal = SlashProposal(
            proposal_id=proposal_id,
            mandate_id=mandate_id,
            target=target,
            slash_type=slash_type,
            reason=reason,
<<<<<<< HEAD
            slash_percentage=min(slash_percentage, 0.5),
=======
            slash_percentage=min(slash_percentage, 0.5),  # Max 50%
>>>>>>> main
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
<<<<<<< HEAD
        """Vote on a slash proposal."""
        proposal = self._get_proposal(proposal_id)
        
        if proposal.is_expired():
            raise ValueError(f"Proposal {proposal_id} has expired")
        
        if voter == proposal.target:
            raise ValueError("Cannot vote on your own slash proposal")
        
        proposal.voters[voter] = support
        
        proposal.votes_for = sum(1 for v in proposal.voters.values() if v)
        proposal.votes_against = sum(1 for v in proposal.voters.values() if not v)
        
=======
        """
        Vote on a slash proposal.
        
        Args:
            proposal_id: Proposal to vote on
            voter: Voter's wallet
            support: True for slash, False against
            
        Returns:
            Updated SlashProposal
        """
        proposal = self._get_proposal(proposal_id)
        
        # Check expiration
        if proposal.is_expired():
            raise ValueError(f"Proposal {proposal_id} has expired")
        
        # Check self-voting
        if voter == proposal.target:
            raise ValueError("Cannot vote on your own slash proposal")
        
        # Record vote
        proposal.voters[voter] = support
        
        # Update counts
        proposal.votes_for = sum(1 for v in proposal.voters.values() if v)
        proposal.votes_against = sum(1 for v in proposal.voters.values() if not v)
        
        # Check if should auto-execute (unanimous)
        if proposal.votes_for >= 3 and proposal.votes_against == 0:
            if proposal.votes_for >= self.QUORUM:
                proposal.status = SlashStatus.APPROVED
        
>>>>>>> main
        return proposal
    
    def get_proposal_status(self, proposal_id: str) -> SlashStatus:
        """Get current status of a proposal"""
        proposal = self._get_proposal(proposal_id)
        
<<<<<<< HEAD
=======
        # Check expiration
>>>>>>> main
        if proposal.is_expired():
            proposal.status = SlashStatus.EXPIRED
            return SlashStatus.EXPIRED
        
<<<<<<< HEAD
=======
        # Check for quorum
>>>>>>> main
        total_votes = proposal.votes_for + proposal.votes_against
        if total_votes < self.QUORUM:
            return SlashStatus.PENDING
        
<<<<<<< HEAD
=======
        # Check supermajority
>>>>>>> main
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
<<<<<<< HEAD
        """Slash a provider's reputation."""
        proposal = self.create_proposal(
            mandate_id=mandate_id,
            target="",
=======
        """
        Slash a provider's reputation.
        
        Args:
            mandate_id: Related mandate
            percentage: Slash percentage (0-1)
            reason: Reason for slash
            evidence: Evidence hashes
            
        Returns:
            SlashResult with outcome
        """
        # Create auto-proposal for clear violations
        proposal = self.create_proposal(
            mandate_id=mandate_id,
            target="",  # Will be set by executor
>>>>>>> main
            slash_type="provider",
            reason=reason,
            slash_percentage=percentage,
            proposer="auto",
            evidence=evidence,
        )
        
<<<<<<< HEAD
        return SlashResult(
            success=True,
            reputation_loss=percentage * 30,
            stake_loss=percentage * 1000,
=======
        # For auto-slashing, use reputation directly
        return SlashResult(
            success=True,
            reputation_loss=percentage * 30,  # Max 30 reputation points
            stake_loss=percentage * 1000,  # Mock stake amount
>>>>>>> main
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
<<<<<<< HEAD
        """Slash a renter's reputation."""
        return SlashResult(
            success=True,
            reputation_loss=percentage * 20,
            stake_loss=percentage * 500,
=======
        """
        Slash a renter's reputation.
        
        Args:
            mandate_id: Related mandate
            percentage: Slash percentage (0-1)
            reason: Reason for slash
            evidence: Evidence hashes
            
        Returns:
            SlashResult with outcome
        """
        return SlashResult(
            success=True,
            reputation_loss=percentage * 20,  # Max 20 reputation points
            stake_loss=percentage * 500,  # Mock stake amount
>>>>>>> main
            message=f"Renter slashed {percentage*100}% for {reason.value}",
            proposal_id="",
        )
    
    def execute_slash(self, proposal_id: str) -> SlashResult:
<<<<<<< HEAD
        """Execute an approved slash proposal."""
        proposal = self._get_proposal(proposal_id)
        
        if proposal.status != SlashStatus.APPROVED:
            raise ValueError(f"Proposal {proposal_id} is not approved")
        
        reputation_loss = proposal.slash_percentage * 25
        stake_loss = proposal.slash_percentage * 750
        
=======
        """
        Execute an approved slash proposal.
        
        Args:
            proposal_id: Approved proposal to execute
            
        Returns:
            SlashResult with execution details
        """
        proposal = self._get_proposal(proposal_id)
        
        # Check status
        if proposal.status != SlashStatus.APPROVED:
            raise ValueError(f"Proposal {proposal_id} is not approved")
        
        # Calculate loss
        reputation_loss = proposal.slash_percentage * 25
        stake_loss = proposal.slash_percentage * 750
        
        # Record in history
>>>>>>> main
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
        
<<<<<<< HEAD
=======
        # Mark as executed
>>>>>>> main
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
<<<<<<< HEAD
        """Get slash history."""
=======
        """
        Get slash history.
        
        Args:
            target: Optional target filter
            
        Returns:
            List of slash records
        """
>>>>>>> main
        if target:
            return [s for s in self._slash_history if s["target"] == target]
        return self._slash_history
    
<<<<<<< HEAD
    def calculate_recovery(
=======
    def calculate_reputation_recovery(
>>>>>>> main
        self,
        current_score: float,
        days_since_slash: int,
    ) -> float:
<<<<<<< HEAD
        """Calculate reputation recovery over time."""
        recovery = min(days_since_slash, 30)
        recovered = recovery * 1.0
        return min(current_score + recovered, 50.0)


=======
        """
        Calculate reputation recovery over time.
        
        Recovery rate: 1 point per day, max to 50
        
        Args:
            current_score: Current reputation score
            days_since_slash: Days since last slash
            
        Returns:
            Recovered reputation points
        """
        recovery = min(days_since_slash, 30)  # Max 30 days recovery
        recovered = recovery * 1.0  # 1 point per day
        
        return min(current_score + recovered, 50.0)


# ============ Helper Functions ============

>>>>>>> main
def create_auto_slash(
    mandate_id: str,
    target: str,
    slash_type: str,
    reason: SlashReason,
    severity: str = "medium",
) -> SlashProposal:
<<<<<<< HEAD
    """Create an automatic slash proposal based on severity."""
    percentages = {"low": 0.1, "medium": 0.2, "high": 0.3}
=======
    """
    Create an automatic slash proposal based on severity.
    
    Args:
        mandate_id: Related mandate
        target: Wallet to slash
        slash_type: "provider" or "renter"
        reason: Reason for slash
        severity: low, medium, or high
        
    Returns:
        SlashProposal ready for voting
    """
    percentages = {
        "low": 0.1,
        "medium": 0.2,
        "high": 0.3,
    }
    
>>>>>>> main
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
<<<<<<< HEAD
=======


# ============ CLI Demo ============

def demo():
    """Demo the slashing mechanism"""
    slashing = SlashingMechanism()
    
    # Create a proposal
    print("1. Creating slash proposal...")
    proposal = slashing.create_proposal(
        mandate_id="mandate-123",
        target="GFeyFZLmvsw7aKHNoUUM84tCvgKf34ojbpKeKcuXDE5q",
        slash_type="provider",
        reason=SlashReason.NON_DELIVERY,
        slash_percentage=0.2,
        proposer="3WaHbF7k9ced4d2wA8caUHq2v57ujD4J2c57L8wZXfhN",
    )
    print(f"   Proposal: {proposal.proposal_id}")
    
    # Vote
    print("\n2. Voting on proposal...")
    slashing.vote(proposal.proposal_id, "voter-1", True)
    slashing.vote(proposal.proposal_id, "voter-2", True)
    slashing.vote(proposal.proposal_id, "voter-3", False)
    print(f"   Votes: {proposal.votes_for} for, {proposal.votes_against} against")
    
    # Check status
    print("\n3. Checking proposal status...")
    status = slashing.get_proposal_status(proposal.proposal_id)
    print(f"   Status: {status.value}")
    
    # Execute
    if status == SlashStatus.APPROVED:
        print("\n4. Executing slash...")
        result = slashing.execute_slash(proposal.proposal_id)
        print(f"   Result: {result.message}")
    
    # Auto-slash example
    print("\n5. Auto-slashing provider...")
    result = slashing.slash_provider(
        mandate_id="mandate-456",
        percentage=0.15,
        reason=SlashReason.LATE_DELIVERY,
    )
    print(f"   Result: {result.message}")


if __name__ == "__main__":
    demo()
>>>>>>> main
