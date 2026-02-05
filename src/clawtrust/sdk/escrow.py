"""
Escrow Contract Interface

Python bindings for the ClawTrust USDC escrow contract on Solana.
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class EscrowState(Enum):
    """State of an escrow"""
    CREATED = "created"      # Initialized, not funded
    FUNDED = "funded"       # Renter deposited, awaiting completion
    COMPLETED = "completed"  # Task done, funds released
    CANCELLED = "cancelled"  # Cancelled, funds refunded


@dataclass
class EscrowTerms:
    """Terms of an escrow"""
    skill_name: str
    duration_seconds: int
    price_usdc: int  # microUSDC (10,000 = 0.01 USDC)
    metadata_uri: str = ""
    
    def to_dict(self) -> dict:
        return {
            "skill_name": self.skill_name,
            "duration_seconds": self.duration_seconds,
            "price_usdc": self.price_usdc,
            "metadata_uri": self.metadata_uri,
        }


@dataclass
class EscrowAccount:
    """State of an escrow account"""
    address: str
    provider: str
    renter: str
    terms: EscrowTerms
    state: EscrowState
    amount: int  # microUSDC
    created_at: str
    completed_at: Optional[str] = None
    cancelled_at: Optional[str] = None
    
    def is_expired(self) -> bool:
        """Check if escrow has timed out"""
        created = datetime.fromisoformat(self.created_at)
        now = datetime.utcnow()
        elapsed = (now - created).total_seconds()
        return elapsed > self.terms.duration_seconds
    
    def to_dict(self) -> dict:
        return {
            "address": self.address,
            "provider": self.provider,
            "renter": self.renter,
            "terms": self.terms.to_dict(),
            "state": self.state.value,
            "amount": self.amount,
            "created_at": self.created_at,
            "completed_at": self.completed_at,
            "cancelled_at": self.cancelled_at,
        }


@dataclass
class EscrowTransaction:
    """Result of an escrow transaction"""
    tx_signature: str
    escrow_address: Optional[str] = None
    success: bool = True
    error: Optional[str] = None
    
    def to_dict(self) -> dict:
        return {
            "tx_signature": self.tx_signature,
            "escrow_address": self.escrow_address,
            "success": self.success,
            "error": self.error,
        }


# Mock program ID for MVP
ESCROW_PROGRAM_ID = "ESCRW1111111111111111111111111111111111111"
USDC_MINT = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"


class EscrowClient:
    """
    Python client for the ClawTrust Escrow contract.
    
    Provides simple interface for escrow operations.
    """
    
    PROGRAM_ID = ESCROW_PROGRAM_ID
    USDC_MINT = USDC_MINT
    
    def __init__(
        self,
        network: str = "devnet",
        mock: bool = True,
    ):
        self.network = network
        self.mock = mock
        self._escrows: dict[str, EscrowAccount] = {}
        self._init_demo_escrows()
    
    def _init_demo_escrows(self):
        """Initialize demo escrows"""
        self._escrows["demo-escrow-1"] = EscrowAccount(
            address="demo-escrow-1",
            provider="happyclaw-agent",
            renter="agent-alpha",
            terms=EscrowTerms(
                skill_name="image-generation",
                duration_seconds=3600,
                price_usdc=10000,
            ),
            state=EscrowState.FUNDED,
            amount=10000,
            created_at=datetime.utcnow().isoformat(),
        )
    
    async def initialize(
        self,
        provider: str,
        mint: str,
        terms: EscrowTerms,
    ) -> EscrowTransaction:
        """
        Initialize a new escrow.
        
        Args:
            provider: Provider's wallet address
            mint: Token mint (e.g., USDC)
            terms: Escrow terms
            
        Returns:
            EscrowTransaction with address and tx signature
        """
        if self.mock:
            # Generate mock escrow address
            import hashlib
            seed = f"escrow-{provider}-{datetime.utcnow().isoformat()}"
            address = hashlib.sha256(seed.encode()).hexdigest()[:32]
            
            escrow = EscrowAccount(
                address=address,
                provider=provider,
                renter="",  # Not set yet
                terms=terms,
                state=EscrowState.CREATED,
                amount=0,
                created_at=datetime.utcnow().isoformat(),
            )
            self._escrows[address] = escrow
            
            return EscrowTransaction(
                tx_signature=f"mock-init-{hash(address) % 100000}",
                escrow_address=address,
                success=True,
            )
        
        # Real implementation would:
        # 1. Build Initialize instruction
        # 2. Sign and send transaction
        # 3. Return tx signature
        
        return EscrowTransaction(
            tx_signature="real-tx-placeholder",
            success=True,
        )
    
    async def accept(
        self,
        escrow_address: str,
        renter: str,
        amount: int,
    ) -> EscrowTransaction:
        """
        Accept escrow and fund it.
        
        Args:
            escrow_address: Address of escrow to fund
            renter: Renter's wallet address
            amount: Amount to fund (microUSDC)
            
        Returns:
            EscrowTransaction with tx signature
        """
        escrow = self._escrows.get(escrow_address)
        if not escrow:
            return EscrowTransaction(
                tx_signature="",
                success=False,
                error=f"Escrow {escrow_address} not found",
            )
        
        if escrow.state != EscrowState.CREATED:
            return EscrowTransaction(
                tx_signature="",
                success=False,
                error=f"Escrow is {escrow.state.value}, not created",
            )
        
        if self.mock:
            escrow.renter = renter
            escrow.amount = amount
            escrow.state = EscrowState.FUNDED
            
            return EscrowTransaction(
                tx_signature=f"mock-accept-{hash(escrow_address) % 100000}",
                escrow_address=escrow_address,
                success=True,
            )
        
        return EscrowTransaction(
            tx_signature="real-tx-placeholder",
            success=True,
        )
    
    async def complete(
        self,
        escrow_address: str,
        authority: str,
    ) -> EscrowTransaction:
        """
        Complete task and release funds to provider.
        
        Args:
            escrow_address: Address of escrow
            authority: Caller's wallet (provider or renter)
            
        Returns:
            EscrowTransaction with tx signature
        """
        escrow = self._escrows.get(escrow_address)
        if not escrow:
            return EscrowTransaction(
                tx_signature="",
                success=False,
                error=f"Escrow {escrow_address} not found",
            )
        
        if escrow.state != EscrowState.FUNDED:
            return EscrowTransaction(
                tx_signature="",
                success=False,
                error=f"Escrow is {escrow.state.value}, not funded",
            )
        
        if self.mock:
            escrow.state = EscrowState.COMPLETED
            escrow.completed_at = datetime.utcnow().isoformat()
            
            return EscrowTransaction(
                tx_signature=f"mock-complete-{hash(escrow_address) % 100000}",
                escrow_address=escrow_address,
                success=True,
            )
        
        return EscrowTransaction(
            tx_signature="real-tx-placeholder",
            success=True,
        )
    
    async def cancel(
        self,
        escrow_address: str,
        authority: str,
    ) -> EscrowTransaction:
        """
        Cancel escrow and refund to renter.
        
        Args:
            escrow_address: Address of escrow
            authority: Caller's wallet
            
        Returns:
            EscrowTransaction with tx signature
        """
        escrow = self._escrows.get(escrow_address)
        if not escrow:
            return EscrowTransaction(
                tx_signature="",
                success=False,
                error=f"Escrow {escrow_address} not found",
            )
        
        if escrow.state != EscrowState.FUNDED:
            return EscrowTransaction(
                tx_signature="",
                success=False,
                error=f"Escrow is {escrow.state.value}, not funded",
            )
        
        if self.mock:
            escrow.state = EscrowState.CANCELLED
            escrow.cancelled_at = datetime.utcnow().isoformat()
            
            return EscrowTransaction(
                tx_signature=f"mock-cancel-{hash(escrow_address) % 100000}",
                escrow_address=escrow_address,
                success=True,
            )
        
        return EscrowTransaction(
            tx_signature="real-tx-placeholder",
            success=True,
        )
    
    async def get_state(self, escrow_address: str) -> Optional[EscrowState]:
        """Get the current state of an escrow"""
        escrow = self._escrows.get(escrow_address)
        return escrow.state if escrow else None
    
    async def check_timeout(self, escrow_address: str) -> bool:
        """Check if escrow has timed out"""
        escrow = self._escrows.get(escrow_address)
        if not escrow:
            return False
        return escrow.is_expired()
    
    def get_escrow(self, escrow_address: str) -> Optional[EscrowAccount]:
        """Get escrow account details"""
        return self._escrows.get(escrow_address)
    
    def format_escrow(self, escrow: EscrowAccount) -> str:
        """Format escrow for display"""
        status_emoji = {
            EscrowState.CREATED: "⏳",
            EscrowState.FUNDED: "💰",
            EscrowState.COMPLETED: "✅",
            EscrowState.CANCELLED: "❌",
        }
        
        price_usd = escrow.terms.price_usdc / 1_000_000
        
        return f"""
{status_emoji.get(escrow.state, "")} **Escrow** #{escrow.address[:16]}

Provider: @{escrow.provider}
Renter: @{escrow.renter or "Not set"}
Skill: {escrow.terms.skill_name}
Amount: ${price_usd:.2f} USDC ({escrow.terms.price_usdc:,} microUSDC)
State: {escrow.state.value}
Created: {escrow.created_at}
""".strip()


# ============ Helper Functions ============

def create_escrow_terms(
    skill_name: str,
    price_usdc: float,
    duration_seconds: int = 3600,
) -> EscrowTerms:
    """
    Create escrow terms.
    
    Args:
        skill_name: Name of the skill
        price_usdc: Price in USDC (e.g., 0.01)
        duration_seconds: Max duration in seconds
        
    Returns:
        EscrowTerms object
    """
    return EscrowTerms(
        skill_name=skill_name,
        price_usdc=int(price_usdc * 1_000_000),  # Convert to microUSDC
        duration_seconds=duration_seconds,
    )


# ============ CLI Demo ============

async def demo():
    """Demo the escrow client"""
    client = EscrowClient(mock=True)
    
    print("=== Escrow Demo ===\n")
    
    # Create terms
    terms = create_escrow_terms(
        skill_name="image-generation",
        price_usdc=0.01,
        duration_seconds=3600,
    )
    print(f"Created terms: {terms.price_usdc} microUSDC")
    
    # Initialize escrow
    print("\n1. Initializing escrow...")
    tx = await client.initialize(
        provider="happyclaw-agent",
        mint=client.USDC_MINT,
        terms=terms,
    )
    print(f"   Escrow: {tx.escrow_address}")
    print(f"   TX: {tx.tx_signature}")
    
    # Accept escrow
    print("\n2. Accepting and funding...")
    tx = await client.accept(
        escrow_address=tx.escrow_address,
        renter="agent-alpha",
        amount=10000,
    )
    print(f"   TX: {tx.tx_signature}")
    print(f"   State: {await client.get_state(tx.escrow_address)}")
    
    # Check timeout
    print(f"\n3. Timeout check: {await client.check_timeout(tx.escrow_address)}")
    
    # Complete
    print("\n4. Completing task...")
    tx = await client.complete(
        escrow_address=tx.escrow_address,
        authority="agent-alpha",
    )
    print(f"   TX: {tx.tx_signature}")
    print(f"   State: {await client.get_state(tx.escrow_address)}")
    
    # Show final state
    escrow = client.get_escrow(tx.escrow_address)
    if escrow:
        print("\n" + client.format_escrow(escrow))


if __name__ == "__main__":
    asyncio.run(demo())
