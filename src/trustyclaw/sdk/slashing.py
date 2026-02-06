"""
Slashing Mechanism for TrustyClaw

Purpose:
    Handles reputation slashing for contract violations.
    Supports automatic and community-voted slashing.

@dataclass
class SlashProposal:

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

        hours = voting_period_hours or self.VOTING_PERIOD_HOURS
        expires_at = datetime.utcnow() + datetime.timedelta(hours=hours)
        
        proposal = SlashProposal(
            proposal_id=proposal_id,
            mandate_id=mandate_id,
            target=target,
            slash_type=slash_type,
            reason=reason,

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

        return proposal
    
    def get_proposal_status(self, proposal_id: str) -> SlashStatus:
        """Get current status of a proposal"""
        proposal = self._get_proposal(proposal_id)
        

        total_votes = proposal.votes_for + proposal.votes_against
        if total_votes < self.QUORUM:
            return SlashStatus.PENDING
        

            slash_type="provider",
            reason=reason,
            slash_percentage=percentage,
            proposer="auto",
            evidence=evidence,
        )
        

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

            message=f"Renter slashed {percentage*100}% for {reason.value}",
            proposal_id="",
        )
    
    def execute_slash(self, proposal_id: str) -> SlashResult:

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
        

        if target:
            return [s for s in self._slash_history if s["target"] == target]
        return self._slash_history
    

        self,
        current_score: float,
        days_since_slash: int,
    ) -> float:

def create_auto_slash(
    mandate_id: str,
    target: str,
    slash_type: str,
    reason: SlashReason,
    severity: str = "medium",
) -> SlashProposal:

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

# ============ CLI Demo =====
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
