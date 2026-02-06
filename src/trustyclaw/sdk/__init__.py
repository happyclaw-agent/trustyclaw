"""
TrustyClaw SDK - Python SDK for interacting with TrustyClaw services

Modules:
- solana: Real Solana blockchain integration
- usdc: USDC SPL Token integration
- escrow_contract: Secure payment escrow
- reputation_chain: On-chain reputation storage
- cross_chain: Cross-chain bridge service
- matching: ML-based agent-skill matching engine
"""

from .solana import (
    SolanaRPCClient,
    WalletInfo,
    TransactionInfo,
    Network,
    get_client,
)
from .usdc import (
    USDCClient,
    TokenAccount,
    TransferResult,
    TokenError,
    TransferStatus,
    get_usdc_client,
)
from .escrow_contract import (
    EscrowClient,
    EscrowState,
    EscrowError,
    EscrowTerms,
    EscrowData,
    get_escrow_client,
    get_escrow_with_payment_service,
)
from .reputation_chain import (
    ReputationChainSDK,
    ReputationError,
    ReputationScoreData,
    ReviewData,
    get_reputation_chain,
)
from .cross_chain import (
    CrossChainBridge,
    Chain,
    BridgeStatus,
    BridgeError,
    BridgeTransaction,
    BridgeQuote,
    get_bridge_client,
)
from .matching import (
    MatchingEngine,
    TaskRequirements,
    AgentRecommendation,
    SkillMatch,
    PricePrediction,
    TimeEstimate,
    get_matching_engine,
)
from .keypair import (
    KeypairManager,
    KeypairError,
    WalletInfo as KeypairWalletInfo,
    get_keypair_manager,
)
from .auto_executor import (
    AutoExecutor,
    ExecutionEvent,
    ExecutionContext,
    ExecutionResult,
    ExecutionRule,
    get_auto_executor,
)
# Slashing - commented out due to merge conflicts
# from .slashing import (
#     SlashingMechanism,
#     SlashReason,
#     SlashStatus,
#     SlashProposal,
#     SlashResult,
# )

__all__ = [
    # Solana
    "SolanaRPCClient",
    "WalletInfo",
    "TransactionInfo", 
    "Network",
    "get_client",
    # USDC
    "USDCClient",
    "TokenAccount",
    "TransferResult",
    "TokenError",
    "TransferStatus",
    "get_usdc_client",
    # Escrow
    "EscrowClient",
    "EscrowState",
    "EscrowError",
    "EscrowTerms",
    "EscrowData",
    "get_escrow_client",
    "get_escrow_with_payment_service",
    # Reputation
    "ReputationChainSDK",
    "ReputationError",
    "ReputationScoreData",
    "ReviewData",
    "get_reputation_chain",
    # Cross-chain
    "CrossChainBridge",
    "Chain",
    "BridgeStatus",
    "BridgeError",
    "BridgeTransaction",
    "BridgeQuote",
    "get_bridge_client",
    # Matching
    "MatchingEngine",
    "TaskRequirements",
    "AgentRecommendation",
    "SkillMatch",
    "PricePrediction",
    "TimeEstimate",
    "get_matching_engine",
    # Keypair
    "KeypairManager",
    "KeypairError",
    "KeypairWalletInfo",
    "get_keypair_manager",
    # Auto Executor
    "AutoExecutor",
    "ExecutionEvent",
    "ExecutionContext",
    "ExecutionResult",
    "ExecutionRule",
    "get_auto_executor",
    # Slashing - commented out due to merge conflicts
# "SlashingMechanism",
# "SlashReason",  
# "SlashStatus",
# "SlashProposal",
# "SlashResult",
]
