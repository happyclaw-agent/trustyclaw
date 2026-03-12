"""TrustyClaw Escrow Contract client and local simulation helpers."""

from __future__ import annotations

import hashlib
import json
import os
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any

# Optional on-chain dependencies.
try:
    from anchorpy import Context, Program
    from solana.rpc.async_api import AsyncClient
    from solana.rpc.commitment import Finalized
    from solders.pubkey import Pubkey
    from solders.signature import Signature
    from spl.token.constants import ASSOCIATED_TOKEN_PROGRAM_ID, TOKEN_PROGRAM_ID

    HAS_ANCHOR = True
except ImportError:
    HAS_ANCHOR = False
    Context = None
    Program = None
    Pubkey = None
    Signature = None
    AsyncClient = None
    Finalized = None
    TOKEN_PROGRAM_ID = None
    ASSOCIATED_TOKEN_PROGRAM_ID = None


class EscrowState(Enum):
    """Escrow lifecycle states across on-chain and simulation flows."""

    CREATED = "created"
    FUNDED = "funded"
    ACTIVE = "active"
    COMPLETED = "completed"
    RELEASED = "released"
    REFUNDED = "refunded"
    DISPUTED = "disputed"


class EscrowError(Exception):
    """Escrow operation error."""


@dataclass
class EscrowTerms:
    """Terms of an escrow agreement."""

    skill_name: str
    duration_seconds: int
    price_usdc: int
    metadata_uri: str


@dataclass
class EscrowData:
    """On-chain escrow account data."""

    provider: str
    renter: str
    token_mint: str
    provider_token_account: str
    skill_name: str
    duration_seconds: int
    price_usdc: int
    metadata_uri: str
    amount: int
    state: int
    created_at: int
    funded_at: int | None
    completed_at: int | None
    disputed_at: int | None
    dispute_reason: str | None

    @classmethod
    def from_account(cls, data: dict[str, Any]) -> EscrowData:
        """Create from Anchor account-like data."""
        return cls(
            provider=str(data.get("provider", "")),
            renter=str(data.get("renter", "")),
            token_mint=str(data.get("token_mint", "")),
            provider_token_account=str(data.get("providerTokenAccount", "")),
            skill_name=str(data.get("skillName", "")),
            duration_seconds=int(data.get("durationSeconds", 0)),
            price_usdc=int(data.get("priceUsdc", 0)),
            metadata_uri=str(data.get("metadataUri", "")),
            amount=int(data.get("amount", 0)),
            state=int(data.get("state", 0)),
            created_at=int(data.get("createdAt", 0)),
            funded_at=data.get("fundedAt"),
            completed_at=data.get("completedAt"),
            disputed_at=data.get("disputedAt"),
            dispute_reason=data.get("disputeReason"),
        )


@dataclass
class SimpleTerms:
    amount: int


@dataclass
class EscrowResult:
    escrow_id: str
    state: EscrowState
    terms: SimpleTerms


@dataclass
class _SimEscrow:
    amount: int
    state: EscrowState = EscrowState.CREATED
    deliverable_hash: str | None = None


class EscrowClient:
    """Escrow contract client with on-chain methods and local simulation helpers."""

    ESCROW_SEED = b"trustyclaw-escrow"
    USDC_MINT = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"

    def __init__(self, program_id: str | None = None, network: str = "devnet"):
        self.network = network
        self.program_id = program_id or self._get_program_id()
        self._client = AsyncClient(self._get_rpc_url()) if HAS_ANCHOR else None
        self._program: Any = None
        self._escrows: dict[str, _SimEscrow] = {}
        self._payment_service: Any = None

    # ----------- Shared helpers -----------

    def _get_program_id(self) -> str:
        env_id = os.environ.get("ESCROW_PROGRAM_ID", "")
        if env_id:
            return env_id
        if self.network == "devnet":
            return "ESCRwJwfT1XpTwzPfkQ9NyTXfHWHnhCWdK1vYhmjbUF"
        if self.network == "mainnet":
            return "ESCRW1111111111111111111111111111111111111"
        return "ESCRW1111111111111111111111111111111111"

    def _get_rpc_url(self) -> str:
        urls = {
            "localnet": "http://127.0.0.1:8899",
            "devnet": "https://api.devnet.solana.com",
            "mainnet": "https://api.mainnet-beta.solana.com",
        }
        return urls.get(self.network, urls["devnet"])

    def _load_idl(self) -> dict[str, Any]:
        idl_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "..",
            "..",
            "target",
            "idl",
            "escrow.json",
        )
        if os.path.exists(idl_path):
            with open(idl_path, encoding="utf-8") as handle:
                return json.load(handle)

        return {
            "version": "0.1.0",
            "name": "escrow",
            "instructions": [],
        }

    def _require_anchor(self) -> None:
        if not HAS_ANCHOR:
            raise EscrowError("Anchor dependencies are not available")

    def _require_program(self) -> Any:
        self._require_anchor()
        if not self._program:
            raise EscrowError("Anchor program not initialized")
        return self._program

    # ----------- On-chain API (async) -----------

    def get_escrow_address(self, provider_address: str) -> tuple[str, int]:
        self._require_anchor()
        provider_pubkey = Pubkey.from_string(provider_address)
        address, bump = Pubkey.find_program_address(
            [self.ESCROW_SEED, provider_pubkey.to_bytes()],
            Pubkey.from_string(self.program_id),
        )
        return str(address), bump

    def get_token_account_address(self, mint: str, owner: str) -> str:
        self._require_anchor()
        mint_pubkey = Pubkey.from_string(mint)
        owner_pubkey = Pubkey.from_string(owner)
        address, _ = Pubkey.find_program_address(
            [owner_pubkey.to_bytes(), TOKEN_PROGRAM_ID.to_bytes(), mint_pubkey.to_bytes()],
            ASSOCIATED_TOKEN_PROGRAM_ID,
        )
        return str(address)

    async def initialize(
        self,
        provider_keypair: Any,
        skill_name: str,
        duration_seconds: int,
        price_usdc: int,
        metadata_uri: str = "",
    ) -> dict[str, Any]:
        program = self._require_program()
        escrow_pubkey, _ = self.get_escrow_address(str(provider_keypair.pubkey()))
        tx = await program.rpc["initialize"](
            skill_name,
            duration_seconds,
            price_usdc,
            metadata_uri,
            ctx=Context(accounts={}, signers=[provider_keypair]),
        )
        return {"tx": tx, "escrow": escrow_pubkey}

    async def fund(self, renter_keypair: Any, provider_address: str, amount: int) -> dict[str, Any]:
        program = self._require_program()
        escrow_pubkey, _ = self.get_escrow_address(provider_address)
        tx = await program.rpc["fund"](
            amount,
            ctx=Context(
                accounts={"escrow": Pubkey.from_string(escrow_pubkey)},
                signers=[renter_keypair],
            ),
        )
        return {"tx": tx}

    async def release(self, renter_keypair: Any, provider_address: str) -> dict[str, Any]:
        program = self._require_program()
        escrow_pubkey, _ = self.get_escrow_address(provider_address)
        tx = await program.rpc["release"](
            ctx=Context(
                accounts={"escrow": Pubkey.from_string(escrow_pubkey)},
                signers=[renter_keypair],
            ),
        )
        return {"tx": tx}

    async def refund(self, provider_keypair: Any) -> dict[str, Any]:
        program = self._require_program()
        provider_address = str(provider_keypair.pubkey())
        escrow_pubkey, _ = self.get_escrow_address(provider_address)
        tx = await program.rpc["refund"](
            ctx=Context(
                accounts={"escrow": Pubkey.from_string(escrow_pubkey)},
                signers=[provider_keypair],
            ),
        )
        return {"tx": tx}

    async def dispute(
        self,
        authority_keypair: Any,
        provider_address: str,
        reason: str,
    ) -> dict[str, Any]:
        program = self._require_program()
        escrow_pubkey, _ = self.get_escrow_address(provider_address)
        tx = await program.rpc["dispute"](
            reason,
            ctx=Context(
                accounts={"escrow": Pubkey.from_string(escrow_pubkey)},
                signers=[authority_keypair],
            ),
        )
        return {"tx": tx}

    async def resolve_dispute_release(
        self,
        resolver_keypair: Any,
        provider_address: str,
    ) -> dict[str, Any]:
        program = self._require_program()
        escrow_pubkey, _ = self.get_escrow_address(provider_address)
        tx = await program.rpc["resolve_dispute_release"](
            ctx=Context(
                accounts={"escrow": Pubkey.from_string(escrow_pubkey)},
                signers=[resolver_keypair],
            ),
        )
        return {"tx": tx}

    async def get_escrow(self, provider_address: str) -> EscrowData | None:
        program = self._require_program()
        escrow_pubkey, _ = self.get_escrow_address(provider_address)
        try:
            account = await program.account["Escrow"].fetch(Pubkey.from_string(escrow_pubkey))
            return EscrowData.from_account(account.__dict__)
        except Exception:
            return None

    async def get_balance(self, address: str) -> int:
        self._require_anchor()
        if not self._client:
            raise EscrowError("Solana client not initialized")
        response = await self._client.get_balance(Pubkey.from_string(address))
        return int(response.value)

    async def get_token_balance(self, token_account: str) -> int:
        self._require_anchor()
        if not self._client:
            raise EscrowError("Solana client not initialized")
        try:
            response = await self._client.get_token_account_balance(
                Pubkey.from_string(token_account)
            )
            return int(response.value.amount)
        except Exception:
            return 0

    async def confirm_transaction(self, tx_sig: str) -> bool:
        self._require_anchor()
        if not self._client:
            raise EscrowError("Solana client not initialized")
        try:
            result = await self._client.confirm_transaction(
                Signature.from_string(tx_sig),
                Finalized,
            )
            return result.value[0].err is None if isinstance(result.value, list) else True
        except Exception:
            return False

    # ----------- Local simulation lifecycle API -----------

    def create_escrow(
        self,
        renter: str,
        provider: str,
        skill_id: str,
        amount: int,
        duration_hours: int,
        deliverable_hash: str,
    ) -> EscrowResult:
        # Include all identifiers so simulation IDs are deterministic and unique.
        payload = f"{renter}:{provider}:{skill_id}:{duration_hours}:{deliverable_hash}".encode()
        suffix = hashlib.sha256(payload).hexdigest()[:10]
        escrow_id = f"escrow_{provider[:8]}_{skill_id}_{suffix}"
        self._escrows[escrow_id] = _SimEscrow(amount=amount)
        return EscrowResult(
            escrow_id=escrow_id,
            state=EscrowState.CREATED,
            terms=SimpleTerms(amount=amount),
        )

    def fund_escrow(self, escrow_id: str) -> EscrowResult:
        escrow = self._escrows.get(escrow_id)
        if not escrow:
            raise ValueError(f"Escrow {escrow_id} not found")
        escrow.state = EscrowState.FUNDED
        return EscrowResult(
            escrow_id=escrow_id,
            state=EscrowState.FUNDED,
            terms=SimpleTerms(amount=escrow.amount),
        )

    def activate_escrow(self, escrow_id: str) -> EscrowResult:
        escrow = self._escrows.get(escrow_id)
        if not escrow or escrow.state is not EscrowState.FUNDED:
            raise ValueError("Cannot activate unfunded escrow")
        escrow.state = EscrowState.ACTIVE
        return EscrowResult(
            escrow_id=escrow_id,
            state=EscrowState.ACTIVE,
            terms=SimpleTerms(amount=escrow.amount),
        )

    def complete_escrow(self, escrow_id: str, deliverable_hash: str) -> EscrowResult:
        escrow = self._escrows.get(escrow_id)
        if not escrow or escrow.state is not EscrowState.ACTIVE:
            raise ValueError("Cannot complete inactive escrow")
        escrow.state = EscrowState.COMPLETED
        escrow.deliverable_hash = deliverable_hash
        return EscrowResult(
            escrow_id=escrow_id,
            state=EscrowState.COMPLETED,
            terms=SimpleTerms(amount=escrow.amount),
        )

    def release_escrow(self, escrow_id: str) -> EscrowResult:
        escrow = self._escrows.get(escrow_id)
        if not escrow or escrow.state is not EscrowState.COMPLETED:
            raise ValueError("Cannot release uncompleted escrow")
        escrow.state = EscrowState.RELEASED
        return EscrowResult(
            escrow_id=escrow_id,
            state=EscrowState.RELEASED,
            terms=SimpleTerms(amount=escrow.amount),
        )

    def release_amount_for_escrow(self, escrow_id: str) -> int:
        escrow = self._escrows.get(escrow_id)
        return escrow.amount if escrow else 0

    # ----------- Payment service integration -----------

    def get_payment_service(self) -> Any:
        if self._payment_service is None:
            from .usdc_payment import USDCPaymentService

            self._payment_service = USDCPaymentService(network=self.network, usdc_client=None)
        return self._payment_service

    def create_payment_intent(
        self,
        provider: str,
        renter: str,
        amount: int,
        description: str,
        metadata: dict[str, Any] | None = None,
    ) -> Any:
        payment_service = self.get_payment_service()
        return payment_service.create_payment_intent(
            amount=amount,
            from_wallet=renter,
            to_wallet=provider,
            description=description,
            metadata={
                **(metadata or {}),
                "escrow_program_id": self.program_id,
                "network": self.network,
            },
        )

    def track_escrow_payment(self, escrow_address: str, payment_intent_id: str) -> Any:
        payment_service = self.get_payment_service()
        existing = payment_service._escrow_payments.get(escrow_address)
        if existing:
            return existing
        intent = payment_service.get_payment_intent(payment_intent_id)
        if not intent:
            raise EscrowError(f"Payment intent {payment_intent_id} not found")
        return payment_service.execute_escrow_payment(
            escrow_id=escrow_address,
            amount=intent.amount,
            from_wallet=intent.from_wallet,
            to_wallet=intent.to_wallet,
            description=intent.description,
        )

    def execute_payment_with_confirmation(
        self,
        payment_intent_id: str,
        max_retries: int = 3,
    ) -> Any:
        payment_service = self.get_payment_service()
        result = payment_service.execute_payment_intent(payment_intent_id)
        if not result.success and max_retries > 0:
            time.sleep(1)
            return self.execute_payment_with_confirmation(
                payment_intent_id,
                max_retries=max_retries - 1,
            )
        return result

    def get_escrow_payment_status(self, escrow_address: str) -> dict[str, Any]:
        result: dict[str, Any] = {"escrow_address": escrow_address}
        escrow = self._escrows.get(escrow_address)
        if escrow:
            result["escrow_state"] = escrow.state.value
            result["amount"] = escrow.amount

        payment_service = self.get_payment_service()
        escrow_payment = payment_service.get_escrow_payment(escrow_address)
        if escrow_payment:
            result["payment"] = {
                "status": escrow_payment.status.value,
                "payment_intent_id": escrow_payment.payment_intent_id,
                "funded_at": escrow_payment.funded_at,
                "released_at": escrow_payment.released_at,
                "refunded_at": escrow_payment.refunded_at,
            }
        return result

    def setup_balance_notification(
        self,
        wallet_address: str,
        threshold_usd: float = 10.0,
        callback_url: str | None = None,
        auto_reload: bool = False,
        auto_reload_amount: int | None = None,
    ) -> Any:
        payment_service = self.get_payment_service()
        return payment_service.register_balance_notification(
            wallet_address=wallet_address,
            threshold_usd=threshold_usd,
            callback_url=callback_url,
            auto_reload=auto_reload,
            auto_reload_amount=auto_reload_amount,
        )

    def check_and_reload_balance(self, wallet_address: str) -> dict[str, Any]:
        payment_service = self.get_payment_service()
        return payment_service.check_balance_and_notify(wallet_address)

    def get_payment_history(self, wallet_address: str, limit: int = 100) -> list[Any]:
        payment_service = self.get_payment_service()
        return payment_service.get_payment_history(wallet_address=wallet_address, limit=limit)


# ----------- Module helpers -----------

def get_escrow_client(program_id: str | None = None, network: str = "devnet") -> EscrowClient:
    """Get a configured EscrowClient.

    Supports historical call style `get_escrow_client("devnet")` where the first
    positional argument is the network.
    """
    if program_id in {"localnet", "devnet", "mainnet"} and network == "devnet":
        return EscrowClient(program_id=None, network=program_id)
    return EscrowClient(program_id=program_id, network=network)


def get_escrow_with_payment_service(
    program_id: str | None = None,
    network: str = "devnet",
    multisig_threshold_usd: float = 1000.0,
    recovery_wallet: str | None = None,
) -> EscrowClient:
    """Get an EscrowClient with payment-service multisig configuration."""
    client = EscrowClient(program_id=program_id, network=network)
    from .usdc_payment import MultisigConfig

    payment_service = client.get_payment_service()
    payment_service.set_multisig_config(
        MultisigConfig(
            threshold_usd=multisig_threshold_usd,
            required_signers=[],
            required_count=2,
            recovery_signer=recovery_wallet,
        )
    )
    return client


if HAS_ANCHOR:
    SYS_PROGRAM_ID = Pubkey.from_string("11111111111111111111111111111111")
else:
    SYS_PROGRAM_ID = "11111111111111111111111111111111"
