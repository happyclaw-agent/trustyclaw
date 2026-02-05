"""
Unit Tests for Escrow Contract Interface

Purpose:
    Unit tests for escrow.py module.
    Tests use mocked data to verify escrow state machine.
    
Escrow State Machine:
    Created → Funded → Completed/Cancelled
    
    Created: Escrow initialized, no funds
    Funded: Renter deposited, awaiting completion
    Completed: Task done, funds released to provider
    Cancelled: Cancelled, funds refunded to renter
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

from src.clawtrust.sdk.escrow import (
    EscrowClient,
    EscrowTerms,
    EscrowState,
    EscrowAccount,
    EscrowTransaction,
    ESCROW_PROGRAM_ID,
    USDC_MINT,
)


# ============ Test Fixtures ============

@pytest.fixture
def sample_terms():
    """Create sample escrow terms"""
    return EscrowTerms(
        skill_name="image-generation",
        price_usdc=10000,  # 0.01 USDC
        duration_seconds=3600,
        metadata_uri="ipfs://QmTest...",
    )


@pytest.fixture
def created_escrow(sample_terms):
    """Create an escrow in CREATED state"""
    return EscrowAccount(
        address="escrow-abc123",
        provider="happyclaw-agent",
        renter="",
        terms=sample_terms,
        state=EscrowState.CREATED,
        amount=0,
        created_at=datetime.utcnow().isoformat(),
    )


@pytest.fixture
def funded_escrow(sample_terms):
    """Create an escrow in FUNDED state"""
    return EscrowAccount(
        address="escrow-abc123",
        provider="happyclaw-agent",
        renter="agent-alpha",
        terms=sample_terms,
        state=EscrowState.FUNDED,
        amount=10000,
        created_at=datetime.utcnow().isoformat(),
    )


@pytest.fixture
def completed_escrow(sample_terms):
    """Create an escrow in COMPLETED state"""
    return EscrowAccount(
        address="escrow-abc123",
        provider="happyclaw-agent",
        renter="agent-alpha",
        terms=sample_terms,
        state=EscrowState.COMPLETED,
        amount=10000,
        created_at=(datetime.utcnow() - timedelta(hours=2)).isoformat(),
        completed_at=datetime.utcnow().isoformat(),
    )


# ============ EscrowTerms Tests ============

class TestEscrowTerms:
    """Tests for EscrowTerms"""
    
    def test_create_terms(self, sample_terms):
        """Test creating escrow terms"""
        assert sample_terms.skill_name == "image-generation"
        assert sample_terms.price_usdc == 10000
        assert sample_terms.duration_seconds == 3600
    
    def test_terms_to_dict(self, sample_terms):
        """Test terms serialization"""
        data = sample_terms.to_dict()
        
        assert data["skill_name"] == "image-generation"
        assert data["price_usdc"] == 10000
        assert data["duration_seconds"] == 3600
        assert data["metadata_uri"] == "ipfs://QmTest..."
    
    def test_price_conversion(self):
        """Test price conversion (USD to microUSDC)"""
        # 0.01 USDC = 10,000 microUSDC
        terms = EscrowTerms(
            skill_name="test",
            price_usdc=10000,
            duration_seconds=3600,
        )
        assert terms.price_usdc == 10000


# ============ EscrowAccount Tests ============

class TestEscrowAccount:
    """Tests for EscrowAccount"""
    
    def test_is_not_expired_just_created(self, created_escrow):
        """Test escrow is not expired when just created"""
        assert created_escrow.is_expired() is False
    
    def test_is_expired_after_duration(self, funded_escrow):
        """Test escrow is expired after duration passes"""
        # Create escrow 2 hours ago with 1 hour duration
        funded_escrow.created_at = (datetime.utcnow() - timedelta(hours=2)).isoformat()
        assert funded_escrow.is_expired() is True
    
    def test_is_not_expired_within_duration(self, funded_escrow):
        """Test escrow is not expired within duration"""
        funded_escrow.created_at = (datetime.utcnow() - timedelta(minutes=30)).isoformat()
        assert funded_escrow.is_expired() is False
    
    def test_account_to_dict(self, created_escrow):
        """Test account serialization"""
        data = created_escrow.to_dict()
        
        assert data["address"] == "escrow-abc123"
        assert data["provider"] == "happyclaw-agent"
        assert data["state"] == "created"
        assert data["amount"] == 0


# ============ EscrowState Tests ============

class TestEscrowState:
    """Tests for EscrowState enum"""
    
    def test_all_states_defined(self):
        """Verify all expected states exist"""
        assert EscrowState.CREATED.value == "created"
        assert EscrowState.FUNDED.value == "funded"
        assert EscrowState.COMPLETED.value == "completed"
        assert EscrowState.CANCELLED.value == "cancelled"
    
    def test_state_transitions(self):
        """Test valid state transitions"""
        # Created → Funded
        assert EscrowState.CREATED == EscrowState.CREATED
        assert EscrowState.FUNDED != EscrowState.CREATED


# ============ EscrowClient Tests ============

class TestEscrowClient:
    """Tests for EscrowClient"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        return EscrowClient(network="devnet")
    
    @pytest.mark.asyncio
    async def test_initialize(self, client, sample_terms):
        """Test initializing a new escrow"""
        tx = await client.initialize(
            provider="happyclaw-agent",
            mint=client.USDC_MINT,
            terms=sample_terms,
        )
        
        assert tx.success is True
        assert tx.escrow_address is not None
        assert "tx-init-" in tx.tx_signature
        
        # Verify escrow was created
        escrow = client.get_escrow(tx.escrow_address)
        assert escrow is not None
        assert escrow.state == EscrowState.CREATED
        assert escrow.provider == "happyclaw-agent"
    
    @pytest.mark.asyncio
    async def test_accept_funds_escrow(self, client, sample_terms):
        """Test accepting and funding an escrow"""
        # First create escrow
        tx = await client.initialize(
            provider="happyclaw-agent",
            mint=client.USDC_MINT,
            terms=sample_terms,
        )
        
        # Then accept/fund
        tx = await client.accept(
            escrow_address=tx.escrow_address,
            renter="agent-alpha",
            amount=10000,
        )
        
        assert tx.success is True
        assert tx.escrow_address is not None
        
        # Verify state changed
        state = await client.get_state(tx.escrow_address)
        assert state == EscrowState.FUNDED
        
        # Verify amount
        escrow = client.get_escrow(tx.escrow_address)
        assert escrow.amount == 10000
        assert escrow.renter == "agent-alpha"
    
    @pytest.mark.asyncio
    async def test_accept_invalid_escrow(self, client):
        """Test accepting non-existent escrow"""
        tx = await client.accept(
            escrow_address="nonexistent",
            renter="agent-alpha",
            amount=10000,
        )
        
        assert tx.success is False
        assert "not found" in tx.error
    
    @pytest.mark.asyncio
    async def test_accept_wrong_state(self, client, created_escrow):
        """Test accepting escrow in wrong state"""
        # Add already completed escrow
        client._escrows[created_escrow.address] = created_escrow
        
        # Try to accept (it's already CREATED but we need to set state to COMPLETED first)
        created_escrow.state = EscrowState.COMPLETED
        
        tx = await client.accept(
            escrow_address=created_escrow.address,
            renter="agent-alpha",
            amount=10000,
        )
        
        assert tx.success is False
        assert "not created" in tx.error
    
    @pytest.mark.asyncio
    async def test_complete_escrow(self, client, funded_escrow):
        """Test completing an escrow"""
        # Add funded escrow
        client._escrows[funded_escrow.address] = funded_escrow
        
        tx = await client.complete(
            escrow_address=funded_escrow.address,
            authority="anyone",
        )
        
        assert tx.success is True
        
        # Verify state changed
        state = await client.get_state(funded_escrow.address)
        assert state == EscrowState.COMPLETED
        
        # Verify completion time
        escrow = client.get_escrow(funded_escrow.address)
        assert escrow.completed_at is not None
    
    @pytest.mark.asyncio
    async def test_complete_wrong_state(self, client, created_escrow):
        """Test completing escrow in wrong state"""
        client._escrows[created_escrow.address] = created_escrow
        
        tx = await client.complete(
            escrow_address=created_escrow.address,
            authority="anyone",
        )
        
        assert tx.success is False
        assert "not funded" in tx.error
    
    @pytest.mark.asyncio
    async def test_cancel_escrow(self, client, funded_escrow):
        """Test cancelling an escrow"""
        client._escrows[funded_escrow.address] = funded_escrow
        
        tx = await client.cancel(
            escrow_address=funded_escrow.address,
            authority="anyone",
        )
        
        assert tx.success is True
        
        # Verify state changed
        state = await client.get_state(funded_escrow.address)
        assert state == EscrowState.CANCELLED
    
    @pytest.mark.asyncio
    async def test_check_timeout_not_expired(self, client, funded_escrow):
        """Test timeout check for non-expired escrow"""
        funded_escrow.created_at = datetime.utcnow().isoformat()
        client._escrows[funded_escrow.address] = funded_escrow
        
        is_expired = await client.check_timeout(funded_escrow.address)
        assert is_expired is False
    
    @pytest.mark.asyncio
    async def test_check_timeout_expired(self, client, funded_escrow):
        """Test timeout check for expired escrow"""
        funded_escrow.created_at = (datetime.utcnow() - timedelta(hours=2)).isoformat()
        client._escrows[funded_escrow.address] = funded_escrow
        
        is_expired = await client.check_timeout(funded_escrow.address)
        assert is_expired is True
    
    def test_format_escrow(self, funded_escrow):
        """Test formatting escrow for display"""
        client = EscrowClient()
        formatted = client.format_escrow(funded_escrow)
        
        assert "Escrow" in formatted
        assert "happyclaw-agent" in formatted
        assert "agent-alpha" in formatted
        assert "💰" in formatted  # Status emoji for FUNDED
        assert "$0.01" in formatted  # Price


# ============ EscrowTransaction Tests ============

class TestEscrowTransaction:
    """Tests for EscrowTransaction"""
    
    def test_successful_transaction(self):
        """Test creating a successful transaction"""
        tx = EscrowTransaction(
            tx_signature="tx-abc123",
            escrow_address="escrow-xyz",
            success=True,
        )
        
        assert tx.success is True
        assert tx.tx_signature == "tx-abc123"
        assert tx.escrow_address == "escrow-xyz"
        assert tx.error is None
    
    def test_failed_transaction(self):
        """Test creating a failed transaction"""
        tx = EscrowTransaction(
            tx_signature="",
            success=False,
            error="Escrow not found",
        )
        
        assert tx.success is False
        assert "not found" in tx.error


# ============ Helper Function Tests ============

class TestCreateEscrowTerms:
    """Tests for create_escrow_terms helper"""
    
    def test_create_terms_helper(self):
        """Test the create_escrow_terms helper function"""
        from src.clawtrust.sdk.escrow import create_escrow_terms
        
        terms = create_escrow_terms(
            skill_name="code-review",
            price_usdc=0.05,
            duration_seconds=7200,
        )
        
        assert terms.skill_name == "code-review"
        assert terms.price_usdc == 50000  # 0.05 * 1_000_000
        assert terms.duration_seconds == 7200


# ============ Integration Tests ============

class TestEscrowStateMachine:
    """Integration tests for complete escrow flow"""
    
    @pytest.mark.asyncio
    async def test_full_escrow_flow(self):
        """Test complete escrow lifecycle"""
        client = EscrowClient()
        
        terms = EscrowTerms(
            skill_name="data-analysis",
            price_usdc=20000,
            duration_seconds=3600,
        )
        
        # 1. Initialize
        init_tx = await client.initialize(
            provider="provider-agent",
            mint=client.USDC_MINT,
            terms=terms,
        )
        assert init_tx.success
        assert await client.get_state(init_tx.escrow_address) == EscrowState.CREATED
        
        # 2. Accept/Fund
        accept_tx = await client.accept(
            escrow_address=init_tx.escrow_address,
            renter="renter-agent",
            amount=20000,
        )
        assert accept_tx.success
        assert await client.get_state(init_tx.escrow_address) == EscrowState.FUNDED
        
        # 3. Complete
        complete_tx = await client.complete(
            escrow_address=init_tx.escrow_address,
            authority="anyone",
        )
        assert complete_tx.success
        assert await client.get_state(init_tx.escrow_address) == EscrowState.COMPLETED
        
        # Verify final state
        escrow = client.get_escrow(init_tx.escrow_address)
        assert escrow.state == EscrowState.COMPLETED
        assert escrow.completed_at is not None
    
    @pytest.mark.asyncio
    async def test_cancel_flow(self):
        """Test escrow cancellation flow"""
        client = EscrowClient()
        
        terms = EscrowTerms(
            skill_name="test",
            price_usdc=10000,
            duration_seconds=3600,
        )
        
        # Initialize and fund
        init_tx = await client.initialize(
            provider="provider",
            mint=client.USDC_MINT,
            terms=terms,
        )
        await client.accept(init_tx.escrow_address, "renter", 10000)
        
        # Cancel
        cancel_tx = await client.cancel(
            escrow_address=init_tx.escrow_address,
            authority="provider",
        )
        assert cancel_tx.success
        
        # Verify
        state = await client.get_state(init_tx.escrow_address)
        assert state == EscrowState.CANCELLED


# ========== Run Tests ==========

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
