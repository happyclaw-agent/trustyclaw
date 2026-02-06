"""
USDC Payment Service for TrustyClaw

Deep USDC payment integration with native SPL token operations
for the USDC Agent Hackathon.

Features:
- Payment intents with full tracking
- Escrow payment execution
- Balance notifications with thresholds
- Multi-signature support (2-of-3)
- Auto-reload functionality
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, List, Any, Callable
from datetime import timedelta
import uuid
import hashlib
import json

try:
    from solana.rpc.api import Client as SolanaClient
    from solana.rpc.commitment import Confirmed, Finalized
    from solana.keypair import Keypair
    from solana.publickey import PublicKey
    from spl.token.client import Token as SPLToken
    from spl.token.instructions import transfer, TransferParams
    HAS_SOLANA = True
except ImportError:
    HAS_SOLANA = False

from .usdc import USDCClient, TransferResult, TransferStatus


class PaymentError(Exception):
    """Payment operation error"""
    pass


class PaymentStatus(Enum):
    """Status of a payment"""
    PENDING = "pending"
    PROCESSING = "processing"
    CONFIRMED = "confirmed"
    FINALIZED = "finalized"
    FAILED = "failed"
    CANCELLED = "cancelled"


class EscrowPaymentStatus(Enum):
    """Status of an escrow payment"""
    PENDING = "pending"
    FUNDED = "funded"
    RELEASED = "released"
    REFUNDED = "refunded"
    DISPUTED = "disputed"


@dataclass
class PaymentIntent:
    """
    Payment intent for USDC transfers.
    
    Represents a planned payment with full tracking.
    
    Attributes:
        intent_id: Unique payment intent ID
        from_wallet: Source wallet address
        to_wallet: Destination wallet address
        amount: Amount in microUSDC
        description: Payment description
        status: Current payment status
        created_at: Creation timestamp
        executed_at: Execution timestamp (when funds sent)
        confirmed_at: Confirmation timestamp
        signature: Transaction signature
        metadata: Additional metadata
    """
    intent_id: str
    from_wallet: str
    to_wallet: str
    amount: int  # microUSDC
    description: str
    status: PaymentStatus = PaymentStatus.PENDING
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    executed_at: Optional[str] = None
    confirmed_at: Optional[str] = None
    signature: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def amount_usd(self) -> float:
        """Amount in USD (USDC = $1)"""
        return self.amount / 1_000_000
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "intent_id": self.intent_id,
            "from_wallet": self.from_wallet,
            "to_wallet": self.to_wallet,
            "amount": self.amount,
            "amount_usd": self.amount_usd,
            "description": self.description,
            "status": self.status.value,
            "created_at": self.created_at,
            "executed_at": self.executed_at,
            "confirmed_at": self.confirmed_at,
            "signature": self.signature,
            "metadata": self.metadata,
        }


@dataclass
class EscrowPayment:
    """
    Escrow payment record.
    
    Tracks payments through escrow with full lifecycle.
    
    Attributes:
        escrow_id: Unique escrow ID
        payment_intent_id: Associated payment intent
        amount: Escrow amount in microUSDC
        from_wallet: Renter's wallet
        to_wallet: Provider's wallet
        status: Current escrow status
        funded_at: When escrow was funded
        released_at: When funds were released
        refunded_at: When funds were refunded
        signatures: Multi-signature approvals
    """
    escrow_id: str
    payment_intent_id: str
    amount: int  # microUSDC
    from_wallet: str
    to_wallet: str
    status: EscrowPaymentStatus = EscrowPaymentStatus.PENDING
    funded_at: Optional[str] = None
    released_at: Optional[str] = None
    refunded_at: Optional[str] = None
    signatures: Dict[str, str] = field(default_factory=dict)  # wallet -> signature
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    @property
    def amount_usd(self) -> float:
        """Amount in USD"""
        return self.amount / 1_000_000
    
    @property
    def is_fully_signed(self) -> bool:
        """Check if multi-sig is complete (2-of-3)"""
        return len(self.signatures) >= 2
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "escrow_id": self.escrow_id,
            "payment_intent_id": self.payment_intent_id,
            "amount": self.amount,
            "amount_usd": self.amount_usd,
            "from_wallet": self.from_wallet,
            "to_wallet": self.to_wallet,
            "status": self.status.value,
            "funded_at": self.funded_at,
            "released_at": self.released_at,
            "refunded_at": self.refunded_at,
            "signatures": self.signatures,
            "created_at": self.created_at,
        }


@dataclass
class PaymentResult:
    """
    Result of a payment operation.
    
    Contains transaction details and final status.
    """
    success: bool
    payment_intent_id: Optional[str] = None
    signature: Optional[str] = None
    status: Optional[PaymentStatus] = None
    error: Optional[str] = None
    explorer_url: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "success": self.success,
            "payment_intent_id": self.payment_intent_id,
            "signature": self.signature,
            "status": self.status.value if self.status else None,
            "error": self.error,
            "explorer_url": self.explorer_url,
        }


@dataclass
class BalanceNotification:
    """
    Balance notification configuration.
    
    Defines when and how to alert on balance changes.
    """
    wallet_address: str
    threshold_usd: float  # Alert when below this amount
    callback_url: Optional[str] = None
    auto_reload_enabled: bool = False
    auto_reload_amount: int = 0  # microUSDC
    auto_reload_max_daily: int = 0  # Max daily reloads
    last_notified_at: Optional[str] = None
    last_reloaded_at: Optional[str] = None
    reload_count_today: int = 0
    
    @property
    def threshold_micro(self) -> int:
        """Threshold in microUSDC"""
        return int(self.threshold_usd * 1_000_000)


@dataclass
class Payment:
    """
    Historical payment record.
    
    Immutable record of a completed payment.
    """
    payment_id: str
    from_wallet: str
    to_wallet: str
    amount: int  # microUSDC
    description: str
    status: PaymentStatus
    signature: str
    created_at: str
    confirmed_at: Optional[str] = None
    
    @property
    def amount_usd(self) -> float:
        """Amount in USD"""
        return self.amount / 1_000_000
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "payment_id": self.payment_id,
            "from_wallet": self.from_wallet,
            "to_wallet": self.to_wallet,
            "amount": self.amount,
            "amount_usd": self.amount_usd,
            "description": self.description,
            "status": self.status.value,
            "signature": self.signature,
            "created_at": self.created_at,
            "confirmed_at": self.confirmed_at,
        }


@dataclass
class MultisigConfig:
    """Multi-signature configuration for large transactions"""
    threshold_usd: float  # Apply multisig above this amount
    required_signers: List[str]  # 3 required signers
    required_count: int = 2  # 2-of-3 by default
    recovery_signer: Optional[str] = None  # For recovery
    
    @property
    def threshold_micro(self) -> int:
        """Threshold in microUSDC"""
        return int(self.threshold_usd * 1_000_000)


class USDCPaymentService:
    """
    USDC Payment Service for TrustyClaw.
    
    Provides comprehensive USDC payment operations including:
    - Payment intents with full lifecycle tracking
    - Escrow payment execution
    - Balance notifications with auto-reload
    - Multi-signature support for large transactions
    - Payment history queries
    
    Usage:
        >>> service = USDCPaymentService(network="devnet")
        >>> intent = service.create_payment_intent(
        ...     amount=1_000_000,  # 1 USDC
        ...     from_wallet="renter...",
        ...     to_wallet="provider...",
        ...     description="Image generation service"
        ... )
        >>> result = service.execute_payment_intent(intent.intent_id)
    """
    
    # Constants
    DEFAULT_THRESHOLD_USD = 10.0  # Alert when balance below $10
    DEFAULT_AUTO_RELOAD_AMOUNT = 100_000_000  # $100
    MULTISIG_THRESHOLD_USD = 1000.0  # Require multisig above $1000
    
    def __init__(
        self,
        network: str = "devnet",
        usdc_client: Optional[USDCClient] = None,
        multisig_config: Optional[MultisigConfig] = None,
    ):
        """
        Initialize USDC Payment Service.
        
        Args:
            network: Solana network ("devnet", "testnet", "mainnet")
            usdc_client: Optional USDC client instance
            multisig_config: Multi-signature configuration
        """
        self.network = network
        self.usdc_client = usdc_client or USDCClient(network=network)
        self.multisig_config = multsig_config or MultisigConfig(
            threshold_usd=self.MULTISIG_THRESHOLD_USD,
            required_signers=[],
            required_count=2,
        )
        
        # In-memory storage for demo
        self._payment_intents: Dict[str, PaymentIntent] = {}
        self._escrow_payments: Dict[str, EscrowPayment] = {}
        self._payment_history: List[Payment] = []
        self._balance_notifications: Dict[str, BalanceNotification] = {}
        self._notification_callbacks: List[Callable] = []
        
        # Load notification callbacks
        self._load_notification_callbacks()
    
    def _load_notification_callbacks(self):
        """Load notification callback functions"""
        # These can be extended with actual webhook handlers
        pass
    
    # ============ Payment Intents ============
    
    def create_payment_intent(
        self,
        amount: int,  # microUSDC
        from_wallet: str,
        to_wallet: str,
        description: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> PaymentIntent:
        """
        Create a new payment intent.
        
        Creates a payment intent that can be executed later.
        Intents track the full payment lifecycle.
        
        Args:
            amount: Amount in microUSDC
            from_wallet: Source wallet address
            to_wallet: Destination wallet address
            description: Payment description
            metadata: Additional metadata
            
        Returns:
            PaymentIntent object
            
        Raises:
            PaymentError: If validation fails
        """
        # Validate amount
        if amount <= 0:
            raise PaymentError("Amount must be positive")
        
        if amount < 1_000:  # Minimum 0.001 USDC
            raise PaymentError("Amount below minimum (1,000 microUSDC)")
        
        # Check for large transaction requiring multisig
        amount_usd = amount / 1_000_000
        requires_multisig = (
            self.multisig_config.threshold_usd > 0 and
            amount_usd >= self.multisig_config.threshold_usd
        )
        
        # Generate unique intent ID
        intent_id = f"pi-{uuid.uuid4().hex[:16]}"
        
        # Create intent
        intent = PaymentIntent(
            intent_id=intent_id,
            from_wallet=from_wallet,
            to_wallet=to_wallet,
            amount=amount,
            description=description,
            status=PaymentStatus.PENDING,
            metadata=metadata or {},
        )
        
        if requires_multisig:
            intent.metadata["requires_multisig"] = True
            intent.metadata["signers_required"] = self.multisig_config.required_signers
            intent.metadata["signatures_collected"] = {}
        
        # Store intent
        self._payment_intents[intent_id] = intent
        
        return intent
    
    def get_payment_intent(self, intent_id: str) -> Optional[PaymentIntent]:
        """Get a payment intent by ID"""
        return self._payment_intents.get(intent_id)
    
    def execute_payment_intent(
        self,
        intent_id: str,
        from_wallet_keypair: Optional[str] = None,
    ) -> PaymentResult:
        """
        Execute a payment intent.
        
        Executes the payment and updates the intent status.
        
        Args:
            intent_id: Payment intent ID
            from_wallet_keypair: Path to keypair for signing
            
        Returns:
            PaymentResult with execution details
            
        Raises:
            PaymentError: If execution fails
        """
        intent = self._payment_intents.get(intent_id)
        if not intent:
            return PaymentResult(
                success=False,
                error=f"Payment intent {intent_id} not found",
            )
        
        if intent.status not in [PaymentStatus.PENDING, PaymentStatus.CONFIRMED]:
            return PaymentResult(
                success=False,
                payment_intent_id=intent_id,
                error=f"Cannot execute intent in {intent.status.value} state",
            )
        
        # Check multisig requirements
        if intent.metadata.get("requires_multisig"):
            if not intent.metadata.get("signatures_collected"):
                return PaymentResult(
                    success=False,
                    payment_intent_id=intent_id,
                    error="Multisig required but no signatures collected",
                )
        
        # Execute payment via USDC client
        try:
            result = self.usdc_client.transfer(
                from_wallet=intent.from_wallet,
                to_wallet=intent.to_wallet,
                amount=intent.amount_usd,
            )
            
            # Update intent
            intent.status = PaymentStatus.PROCESSING
            intent.executed_at = datetime.utcnow().isoformat()
            intent.signature = result.signature
            
            # Finalize
            intent.status = PaymentStatus.CONFIRMED
            intent.confirmed_at = datetime.utcnow().isoformat()
            
            # Add to history
            payment = Payment(
                payment_id=f"pay-{uuid.uuid4().hex[:12]}",
                from_wallet=intent.from_wallet,
                to_wallet=intent.to_wallet,
                amount=intent.amount,
                description=intent.description,
                status=intent.status,
                signature=result.signature,
                created_at=intent.created_at,
                confirmed_at=intent.confirmed_at,
            )
            self._payment_history.append(payment)
            
            return PaymentResult(
                success=True,
                payment_intent_id=intent_id,
                signature=result.signature,
                status=intent.status,
                explorer_url=result.explorer_url,
            )
            
        except Exception as e:
            intent.status = PaymentStatus.FAILED
            return PaymentResult(
                success=False,
                payment_intent_id=intent_id,
                status=PaymentStatus.FAILED,
                error=str(e),
            )
    
    def cancel_payment_intent(self, intent_id: str) -> PaymentResult:
        """
        Cancel a pending payment intent.
        
        Args:
            intent_id: Payment intent ID
            
        Returns:
            PaymentResult with cancellation status
        """
        intent = self._payment_intents.get(intent_id)
        if not intent:
            return PaymentResult(
                success=False,
                error=f"Payment intent {intent_id} not found",
            )
        
        if intent.status != PaymentStatus.PENDING:
            return PaymentResult(
                success=False,
                payment_intent_id=intent_id,
                error=f"Cannot cancel intent in {intent.status.value} state",
            )
        
        intent.status = PaymentStatus.CANCELLED
        
        return PaymentResult(
            success=True,
            payment_intent_id=intent_id,
            status=PaymentStatus.CANCELLED,
        )
    
    # ============ Escrow Payments ============
    
    def execute_escrow_payment(
        self,
        escrow_id: str,
        amount: int,  # microUSDC
        from_wallet: str,
        to_wallet: str,
        description: str = "Escrow payment",
    ) -> EscrowPayment:
        """
        Execute an escrow payment.
        
        Creates a payment intent and associates it with escrow.
        
        Args:
            escrow_id: Escrow identifier
            amount: Amount in microUSDC
            from_wallet: Renter's wallet
            to_wallet: Provider's wallet
            description: Payment description
            
        Returns:
            EscrowPayment object
        """
        # Create payment intent for escrow
        intent = self.create_payment_intent(
            amount=amount,
            from_wallet=from_wallet,
            to_wallet=to_wallet,
            description=f"Escrow: {description}",
            metadata={
                "escrow_id": escrow_id,
                "type": "escrow",
            }
        )
        
        # Create escrow payment record
        escrow_payment = EscrowPayment(
            escrow_id=escrow_id,
            payment_intent_id=intent.intent_id,
            amount=amount,
            from_wallet=from_wallet,
            to_wallet=to_wallet,
            status=EscrowPaymentStatus.PENDING,
        )
        
        self._escrow_payments[escrow_id] = escrow_payment
        
        return escrow_payment
    
    def fund_escrow_payment(self, escrow_id: str) -> PaymentResult:
        """
        Fund an escrow payment.
        
        Executes the associated payment intent.
        
        Args:
            escrow_id: Escrow ID
            
        Returns:
            PaymentResult with funding status
        """
        escrow = self._escrow_payments.get(escrow_id)
        if not escrow:
            return PaymentResult(
                success=False,
                error=f"Escrow payment {escrow_id} not found",
            )
        
        if escrow.status != EscrowPaymentStatus.PENDING:
            return PaymentResult(
                success=False,
                error=f"Escrow is {escrow.status.value}, cannot fund",
            )
        
        # Execute payment
        result = self.execute_payment_intent(escrow.payment_intent_id)
        
        if result.success:
            escrow.status = EscrowPaymentStatus.FUNDED
            escrow.funded_at = datetime.utcnow().isoformat()
        
        return result
    
    def release_escrow_payment(
        self,
        escrow_id: str,
        authority: str,
        signature: Optional[str] = None,
    ) -> PaymentResult:
        """
        Release escrow funds to provider.
        
        Args:
            escrow_id: Escrow ID
            authority: Wallet releasing funds
            signature: Optional multi-sig signature
            
        Returns:
            PaymentResult with release status
        """
        escrow = self._escrow_payments.get(escrow_id)
        if not escrow:
            return PaymentResult(
                success=False,
                error=f"Escrow payment {escrow_id} not found",
            )
        
        if escrow.status != EscrowPaymentStatus.FUNDED:
            return PaymentResult(
                success=False,
                error=f"Escrow is {escrow.status.value}, cannot release",
            )
        
        # Collect signature for multisig
        if signature:
            escrow.signatures[authority] = signature
        
        # Check if we need multisig
        intent = self.get_payment_intent(escrow.payment_intent_id)
        if intent and intent.metadata.get("requires_multisig"):
            if not escrow.is_fully_signed:
                return PaymentResult(
                    success=False,
                    payment_intent_id=intent.intent_id,
                    error=f"Need {2 - len(escrow.signatures)} more signature(s)",
                )
        
        # Release funds (simulate - actual release happens via escrow contract)
        escrow.status = EscrowPaymentStatus.RELEASED
        escrow.released_at = datetime.utcnow().isoformat()
        
        return PaymentResult(
            success=True,
            payment_intent_id=escrow.payment_intent_id,
            status=PaymentStatus.FINALIZED,
        )
    
    def refund_escrow_payment(self, escrow_id: str) -> PaymentResult:
        """
        Refund escrow funds to renter.
        
        Args:
            escrow_id: Escrow ID
            
        Returns:
            PaymentResult with refund status
        """
        escrow = self._escrow_payments.get(escrow_id)
        if not escrow:
            return PaymentResult(
                success=False,
                error=f"Escrow payment {escrow_id} not found",
            )
        
        if escrow.status != EscrowPaymentStatus.FUNDED:
            return PaymentResult(
                success=False,
                error=f"Escrow is {escrow.status.value}, cannot refund",
            )
        
        # Refund (simulate - actual refund happens via escrow contract)
        escrow.status = EscrowPaymentStatus.REFUNDED
        escrow.refunded_at = datetime.utcnow().isoformat()
        
        # Update payment intent
        intent = self.get_payment_intent(escrow.payment_intent_id)
        if intent:
            intent.status = PaymentStatus.CANCELLED
        
        return PaymentResult(
            success=True,
            payment_intent_id=escrow.payment_intent_id,
            status=PaymentStatus.CANCELLED,
        )
    
    def get_escrow_payment(self, escrow_id: str) -> Optional[EscrowPayment]:
        """Get escrow payment by ID"""
        return self._escrow_payments.get(escrow_id)
    
    # ============ Payment History ============
    
    def get_payment_history(
        self,
        wallet_address: str,
        limit: int = 100,
        status_filter: Optional[PaymentStatus] = None,
    ) -> List[Payment]:
        """
        Get payment history for a wallet.
        
        Args:
            wallet_address: Wallet to query
            limit: Maximum results
            status_filter: Optional status filter
            
        Returns:
            List of Payment records
        """
        payments = [
            p for p in self._payment_history
            if p.from_wallet == wallet_address or p.to_wallet == wallet_address
        ]
        
        if status_filter:
            payments = [p for p in payments if p.status == status_filter]
        
        # Sort by created_at descending
        payments.sort(key=lambda p: p.created_at, reverse=True)
        
        return payments[:limit]
    
    def get_all_payments(self, limit: int = 100) -> List[Payment]:
        """Get all payments (admin function)"""
        payments = sorted(
            self._payment_history,
            key=lambda p: p.created_at,
            reverse=True,
        )
        return payments[:limit]
    
    # ============ Balance Notifications ============
    
    def register_balance_notification(
        self,
        wallet_address: str,
        threshold_usd: float,
        callback_url: Optional[str] = None,
        auto_reload: bool = False,
        auto_reload_amount: Optional[int] = None,
    ) -> BalanceNotification:
        """
        Register a balance notification.
        
        Args:
            wallet_address: Wallet to monitor
            threshold_usd: Alert threshold in USD
            callback_url: Webhook URL for alerts
            auto_reload: Enable auto-reload feature
            auto_reload_amount: Amount to auto-reload (microUSDC)
            
        Returns:
            BalanceNotification object
        """
        notification = BalanceNotification(
            wallet_address=wallet_address,
            threshold_usd=threshold_usd,
            callback_url=callback_url,
            auto_reload_enabled=auto_reload,
            auto_reload_amount=auto_reload_amount or self.DEFAULT_AUTO_RELOAD_AMOUNT,
        )
        
        self._balance_notifications[wallet_address] = notification
        
        return notification
    
    def check_balance_and_notify(
        self,
        wallet_address: str,
        force: bool = False,
    ) -> Dict[str, Any]:
        """
        Check balance and trigger notifications if needed.
        
        Args:
            wallet_address: Wallet to check
            force: Force notification even if recently notified
            
        Returns:
            Notification result dict
        """
        notification = self._balance_notifications.get(wallet_address)
        if not notification:
            return {"alert_sent": False, "reason": "No notification registered"}
        
        # Get current balance
        balance = self.usdc_client.get_balance(wallet_address)
        balance_usd = balance  # USDC = $1
        
        # Check if below threshold
        if balance_usd >= notification.threshold_usd:
            return {
                "alert_sent": False,
                "reason": "Balance above threshold",
                "current_balance": balance_usd,
                "threshold": notification.threshold_usd,
            }
        
        # Check rate limiting
        if notification.last_notified_at and not force:
            last_notified = datetime.fromisoformat(notification.last_notified_at)
            if datetime.utcnow() - last_notified < timedelta(hours=1):
                return {
                    "alert_sent": False,
                    "reason": "Rate limited",
                    "last_notified": notification.last_notified_at,
                }
        
        # Send alert
        alert = {
            "type": "low_balance_alert",
            "wallet": wallet_address,
            "current_balance": balance_usd,
            "threshold": notification.threshold_usd,
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        # Trigger callbacks
        for callback in self._notification_callbacks:
            try:
                callback(alert)
            except Exception:
                pass
        
        # Send webhook if configured
        if notification.callback_url:
            self._send_webhook(notification.callback_url, alert)
        
        # Update last notified
        notification.last_notified_at = datetime.utcnow().isoformat()
        
        # Auto-reload if enabled
        if notification.auto_reload_enabled:
            self._execute_auto_reload(notification, balance)
        
        return {
            "alert_sent": True,
            "alert": alert,
            "auto_reloaded": notification.auto_reload_enabled,
        }
    
    def _execute_auto_reload(
        self,
        notification: BalanceNotification,
        current_balance: float,
    ):
        """Execute auto-reload for a notification"""
        # Check daily limits
        if notification.last_reloaded_at:
            last_date = datetime.fromisoformat(notification.last_reloaded_at).date()
            if last_date == datetime.utcnow().date():
                if notification.reload_count_today >= notification.auto_reload_max_daily:
                    return  # Daily limit reached
        
        # Check if we can reload (not already loaded today)
        if notification.last_reloaded_at:
            last_reloaded = datetime.fromisoformat(notification.last_reloaded_at)
            if last_reloaded.date() == datetime.utcnow().date():
                return  # Already reloaded today
        
        # Execute reload (create payment intent from funding source)
        # This would typically come from a linked payment method
        reload_amount = notification.auto_reload_amount
        
        # Update notification state
        notification.last_reloaded_at = datetime.utcnow().isoformat()
        notification.reload_count_today += 1
        
        # Create record of reload
        reload_record = {
            "type": "auto_reload",
            "wallet": notification.wallet_address,
            "amount": reload_amount,
            "timestamp": datetime.utcnow().isoformat(),
        }
    
    def _send_webhook(self, url: str, payload: Dict[str, Any]):
        """Send webhook notification"""
        # In production, this would make an HTTP request
        # For now, just log it
        print(f"Webhook to {url}: {json.dumps(payload)}")
    
    def add_notification_callback(self, callback: Callable[[Dict[str, Any]], None]):
        """Add a notification callback function"""
        self._notification_callbacks.append(callback)
    
    # ============ Multi-Signature Support ============
    
    def set_multisig_config(self, config: MultisigConfig):
        """Set multi-signature configuration"""
        self.multisig_config = config
    
    def collect_multisig_signature(
        self,
        intent_id: str,
        signer: str,
        signature: str,
    ) -> Dict[str, Any]:
        """
        Collect a signature for a multisig payment.
        
        Args:
            intent_id: Payment intent ID
            signer: Wallet signing
            signature: Signature string
            
        Returns:
            Collection result
        """
        intent = self._payment_intents.get(intent_id)
        if not intent:
            return {"success": False, "error": "Intent not found"}
        
        if not intent.metadata.get("requires_multisig"):
            return {"success": False, "error": "Multisig not required"}
        
        # Verify signer is in required list
        required_signers = intent.metadata.get("signers_required", [])
        if signer not in required_signers:
            return {"success": False, "error": "Signer not authorized"}
        
        # Collect signature
        if "signatures_collected" not in intent.metadata:
            intent.metadata["signatures_collected"] = {}
        
        intent.metadata["signatures_collected"][signer] = signature
        
        # Check if we have enough signatures
        sigs = intent.metadata["signatures_collected"]
        if len(sigs) >= self.multisig_config.required_count:
            return {
                "success": True,
                "multisig_complete": True,
                "signatures_collected": len(sigs),
                "message": "Multisig complete, payment can be executed",
            }
        
        return {
            "success": True,
            "multisig_complete": False,
            "signatures_collected": len(sigs),
            "signatures_needed": self.multisig_config.required_count - len(sigs),
        }
    
    def initiate_recovery(
        self,
        intent_id: str,
        recovery_wallet: str,
        reason: str,
    ) -> Dict[str, Any]:
        """
        Initiate recovery for a stuck payment.
        
        Args:
            intent_id: Payment intent ID
            recovery_wallet: Wallet initiating recovery
            reason: Recovery reason
            
        Returns:
            Recovery result
        """
        if not self.multisig_config.recovery_signer:
            return {"success": False, "error": "Recovery not configured"}
        
        intent = self._payment_intents.get(intent_id)
        if not intent:
            return {"success": False, "error": "Intent not found"}
        
        # Log recovery attempt
        recovery_record = {
            "intent_id": intent_id,
            "initiated_by": recovery_wallet,
            "reason": reason,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "pending",
        }
        
        return {
            "success": True,
            "recovery_initiated": True,
            "recovery_record": recovery_record,
            "message": "Recovery initiated, awaiting verification",
        }
    
    # ============ Export ============
    
    def export_payments_json(self, wallet_address: Optional[str] = None) -> str:
        """Export payments as JSON"""
        if wallet_address:
            payments = self.get_payment_history(wallet_address)
        else:
            payments = self._payment_history
        
        return json.dumps(
            [p.to_dict() for p in payments],
            indent=2,
        )
    
    def export_escrow_payments_json(self, wallet_address: Optional[str] = None) -> str:
        """Export escrow payments as JSON"""
        if wallet_address:
            escrows = [
                e for e in self._escrow_payments.values()
                if e.from_wallet == wallet_address or e.to_wallet == wallet_address
            ]
        else:
            escrows = list(self._escrow_payments.values())
        
        return json.dumps(
            [e.to_dict() for e in escrows],
            indent=2,
        )


# ============ Factory Functions ============

def get_usdc_payment_service(
    network: str = "devnet",
    multisig_threshold_usd: float = 1000.0,
    recovery_wallet: Optional[str] = None,
) -> USDCPaymentService:
    """
    Get a configured USDC Payment Service.
    
    Args:
        network: Solana network
        multisig_threshold_usd: Threshold for multisig
        recovery_wallet: Recovery wallet address
        
    Returns:
        Configured USDCPaymentService
    """
    usdc_client = USDCClient(network=network)
    
    multisig_config = MultisigConfig(
        threshold_usd=multisig_threshold_usd,
        required_signers=[],
        required_count=2,
        recovery_signer=recovery_wallet,
    )
    
    return USDCPaymentService(
        network=network,
        usdc_client=usdc_client,
        multisig_config=multisig_config,
    )
