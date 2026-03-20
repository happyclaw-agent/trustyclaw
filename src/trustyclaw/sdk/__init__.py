"""TrustyClaw SDK public exports.

Keep package import lightweight so smoke tests and basic consumers can import
`trustyclaw.sdk.*` without requiring every optional blockchain dependency.
"""

from .escrow import EscrowClient, EscrowState, EscrowTerms, create_escrow_terms
from .identity import AgentIdentity, IdentityManager, IdentityStatus
from .reputation import ReputationEngine, ReputationScore, Review
from .reputation_chain import (
    ReputationChainSDK,
    ReputationError,
    ReputationScoreData,
    ReviewData,
    get_reputation_chain,
)

__all__ = [
    "AgentIdentity",
    "IdentityManager",
    "IdentityStatus",
    "ReputationEngine",
    "ReputationScore",
    "Review",
    "ReputationChainSDK",
    "ReputationError",
    "ReputationScoreData",
    "ReviewData",
    "get_reputation_chain",
    "EscrowClient",
    "EscrowState",
    "EscrowTerms",
    "create_escrow_terms",
]

try:
    from .keypair import WalletInfo as _KeypairWalletInfo
except Exception:
    pass
else:
    KeypairWalletInfo = _KeypairWalletInfo
    __all__.append("KeypairWalletInfo")
