"""
Agent Identity Management

Provides wallet-based identity for ClawTrust agents.
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class IdentityStatus(Enum):
    """Status of an agent identity"""
    ACTIVE = "active"
    SUSPENDED = "suspended"
    REVOKED = "revoked"
    PENDING = "pending"


@dataclass
class AgentIdentity:
    """
    Represents an agent's identity in ClawTrust.
    
    Uses wallet-based identification for MVP.
    """
    name: str
    wallet_address: str
    public_key: str
    id: str = field(default_factory=lambda: f"agent-{uuid.uuid4().hex[:8]}")
    email: Optional[str] = None
    reputation_score: float = 0.0
    total_rentals: int = 0
    completed_rentals: int = 0
    status: IdentityStatus = IdentityStatus.ACTIVE
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    metadata: dict = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "wallet_address": self.wallet_address,
            "public_key": self.public_key,
            "email": self.email,
            "reputation_score": self.reputation_score,
            "total_rentals": self.total_rentals,
            "completed_rentals": self.completed_rentals,
            "status": self.status.value,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "AgentIdentity":
        """Create from dictionary"""
        status = IdentityStatus(data.get("status", "active"))
        return cls(
            id=data.get("id", f"agent-{uuid.uuid4().hex[:8]}"),
            name=data["name"],
            wallet_address=data["wallet_address"],
            public_key=data["public_key"],
            email=data.get("email"),
            reputation_score=data.get("reputation_score", 0.0),
            total_rentals=data.get("total_rentals", 0),
            completed_rentals=data.get("completed_rentals", 0),
            status=status,
            created_at=data.get("created_at", datetime.utcnow().isoformat()),
            updated_at=data.get("updated_at", datetime.utcnow().isoformat()),
            metadata=data.get("metadata", {}),
        )
    
    def update_reputation(self, score: float):
        """Update reputation score"""
        self.reputation_score = score
        self.updated_at = datetime.utcnow().isoformat()
    
    def increment_rentals(self, completed: bool = False):
        """Increment rental count"""
        self.total_rentals += 1
        if completed:
            self.completed_rentals += 1
        self.updated_at = datetime.utcnow().isoformat()
    
    def to_short_str(self) -> str:
        """Short string representation"""
        return f"@{self.name} ({self.reputation_score:.0f}/100)"


class IdentityManager:
    """
    Manages agent identities.
    
    For MVP: In-memory storage with mock data.
    Future: On-chain registry or database.
    """
    
    def __init__(self):
        self._identities: dict[str, AgentIdentity] = {}
        self._wallets: dict[str, AgentIdentity] = {}
        self._init_demo_identities()
    
    def _init_demo_identities(self):
        """Initialize demo identities"""
        demos = [
            ("happyclaw-agent", "happyclaw.sol", "happyclaw-pubkey"),
            ("agent-alpha", "alpha.sol", "alpha-pubkey"),
            ("agent-beta", "beta.sol", "beta-pubkey"),
            ("agent-gamma", "gamma.sol", "gamma-pubkey"),
        ]
        
        for name, wallet, pubkey in demos:
            identity = AgentIdentity(
                name=name,
                wallet_address=wallet,
                public_key=pubkey,
                reputation_score=85.0,
                total_rentals=10,
                completed_rentals=9,
            )
            self.register(identity)
    
    def register(self, identity: AgentIdentity) -> AgentIdentity:
        """Register a new identity"""
        self._identities[identity.id] = identity
        self._wallets[identity.wallet_address.lower()] = identity
        return identity
    
    def get_by_id(self, id: str) -> Optional[AgentIdentity]:
        """Get identity by ID"""
        return self._identities.get(id)
    
    def get_by_wallet(self, wallet: str) -> Optional[AgentIdentity]:
        """Get identity by wallet address"""
        return self._wallets.get(wallet.lower())
    
    def get_by_name(self, name: str) -> Optional[AgentIdentity]:
        """Get identity by name"""
        for identity in self._identities.values():
            if identity.name.lower() == name.lower():
                return identity
        return None
    
    def list_identities(
        self,
        status: Optional[IdentityStatus] = None,
        min_reputation: Optional[float] = None,
    ) -> list[AgentIdentity]:
        """List all identities with optional filters"""
        identities = list(self._identities.values())
        
        if status:
            identities = [i for i in identities if i.status == status]
        
        if min_reputation is not None:
            identities = [
                i for i in identities
                if i.reputation_score >= min_reputation
            ]
        
        return identities
    
    def update_reputation(
        self,
        wallet: str,
        score: float,
    ) -> Optional[AgentIdentity]:
        """Update reputation for an identity"""
        identity = self.get_by_wallet(wallet)
        if identity:
            identity.update_reputation(score)
        return identity
    
    def check_exists(self, wallet: str) -> bool:
        """Check if identity exists for wallet"""
        return wallet.lower() in self._wallets


# ============ Factory Functions ============

def create_identity(
    name: str,
    wallet_address: str,
    public_key: str,
    email: str = None,
) -> AgentIdentity:
    """Create a new agent identity"""
    return AgentIdentity(
        name=name,
        wallet_address=wallet_address,
        public_key=public_key,
        email=email,
    )


def load_identity(wallet: str) -> Optional[AgentIdentity]:
    """Load identity from storage"""
    manager = IdentityManager()
    return manager.get_by_wallet(wallet)


# ============ CLI ============

def demo():
    """Demo the identity manager"""
    manager = IdentityManager()
    
    # List all
    print("Demo Identities:")
    for identity in manager.list_identities():
        print(f"  {identity.to_short_str()}")
    
    # Get specific
    agent = manager.get_by_name("happyclaw-agent")
    if agent:
        print(f"\nHappy Claw Details:")
        print(f"  ID: {agent.id}")
        print(f"  Wallet: {agent.wallet_address}")
        print(f"  Reputation: {agent.reputation_score}")
        print(f"  Rentals: {agent.total_rentals}/{agent.completed_rentals}")


if __name__ == "__main__":
    demo()
