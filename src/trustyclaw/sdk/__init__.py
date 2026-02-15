"""
TrustyClaw SDK - Python SDK for interacting with TrustyClaw services

Modules:
- client: Solana RPC client wrapper
- identity: Agent identity management
- reputation: Reputation scoring engine
- escrow: Escrow contract interface
- solana: Real Solana blockchain integration
- usdc: USDC SPL Token integration
- reputation_chain: On-chain reputation storage
- review_system: Full review lifecycle management
- escrow_contract: Secure payment escrow
"""

from .client import SolanaClient
from .escrow import EscrowClient, EscrowState, EscrowTerms
from .escrow_contract import (
    Escrow,
    EscrowState,
    EscrowTerms,
    get_escrow_client,
)
from .escrow_contract import (
    EscrowClient as EscrowContractClient,
)
from .identity import AgentIdentity, IdentityManager
from .reputation import ReputationEngine, ReputationScore, Review
from .reputation_chain import (
    ReputationPDAProgram,
    ReputationScoreData,
    ReviewData,
    get_reputation_program,
)
from .review_system import (
    Review,
    ReviewDispute,
    ReviewService,
    ReviewStatus,
    ReviewVote,
    get_review_service,
)
from .solana import SolanaRPCClient, TransactionInfo, WalletInfo, get_client
from .usdc import TokenAccount, TransferResult, USDCClient, get_usdc_client

__all__ = [
    "SolanaClient",
    "AgentIdentity",
    "IdentityManager",
    "ReputationEngine",
    "Review",
    "ReputationScore",
    "EscrowClient",
    "EscrowTerms",
    "EscrowState",
    "SolanaRPCClient",
    "WalletInfo",
    "TransactionInfo",
    "get_client",
    "USDCClient",
    "TokenAccount",
    "TransferResult",
    "get_usdc_client",
    "ReputationPDAProgram",
    "ReputationScoreData",
    "ReviewData",
    "get_reputation_program",
    "ReviewService",
    "Review",
    "ReviewStatus",
    "ReviewDispute",
    "ReviewVote",
    "get_review_service",
    "EscrowContractClient",
    "Escrow",
    "EscrowTerms",
    "EscrowState",
    "get_escrow_client",
]

__version__ = "0.1.0"
