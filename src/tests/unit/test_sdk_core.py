"""
Unit Tests for SDK Core Modules

Tests for client.py, identity.py, and reputation.py
"""

import pytest
import asyncio
from datetime import datetime

from src.clawtrust.sdk.client import SolanaClient, ClientConfig, Network, MockWallet
from src.clawtrust.sdk.identity import AgentIdentity, IdentityManager, IdentityStatus
from src.clawtrust.sdk.reputation import ReputationEngine, Review, ReputationScore


# ============ Client Tests ============

class TestSolanaClient:
    """Tests for SolanaClient"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        return SolanaClient(ClientConfig(network=Network.DEVNET))
    
    @pytest.mark.asyncio
    async def test_get_balance_mock(self, client):
        """Test getting mock balance"""
        balance = await client.get_balance("MockWallet123")
        assert balance == 1_000_000_000  # 1 SOL in lamports
    
    @pytest.mark.asyncio
    async def test_get_account_info_mock(self, client):
        """Test getting mock account info"""
        info = await client.get_account_info("MockAddress123")
        assert info is not None
        assert "lamports" in info
        assert info["lamports"] == 1_000_000_000
    
    @pytest.mark.asyncio
    async def test_get_latest_blockhash(self, client):
        """Test getting blockhash"""
        blockhash = await client.get_latest_blockhash()
        assert blockhash is not None
        assert len(blockhash) > 0
    
    def test_derive_pda(self, client):
        """Test PDA derivation"""
        address, bump = client.derive_pda(
            [b"escrow", b"provider123"],
            "ESCRW1111111111111111111111111111111111111",
        )
        assert address is not None
        assert bump >= 0
    
    def test_get_rpc_url(self, client):
        """Test getting RPC URL"""
        url = client.get_rpc_url()
        assert "devnet" in url or "solana.com" in url
    
    def test_get_network(self, client):
        """Test getting network"""
        network = client.get_network()
        assert network == Network.DEVNET


class TestMockWallet:
    """Tests for MockWallet"""
    
    @pytest.mark.asyncio
    async def test_get_balance(self):
        """Test mock wallet balance"""
        wallet = MockWallet()
        balance = await wallet.get_balance()
        assert balance == 1_000_000_000
    
    @pytest.mark.asyncio
    async def test_get_usdc_balance(self):
        """Test mock USDC balance"""
        wallet = MockWallet()
        balance = await wallet.get_usdc_balance()
        assert balance == 1_000_000


# ============ Identity Tests ============

class TestAgentIdentity:
    """Tests for AgentIdentity"""
    
    def test_create_identity(self):
        """Test creating an identity"""
        identity = AgentIdentity(
            name="TestAgent",
            wallet_address="test-wallet",
            public_key="test-pubkey",
        )
        
        assert identity.name == "TestAgent"
        assert identity.wallet_address == "test-wallet"
        assert identity.status == IdentityStatus.ACTIVE
        assert identity.reputation_score == 0.0
    
    def test_to_dict(self):
        """Test serialization"""
        identity = AgentIdentity(
            name="TestAgent",
            wallet_address="test-wallet",
            public_key="test-pubkey",
            reputation_score=85.0,
        )
        
        data = identity.to_dict()
        
        assert data["name"] == "TestAgent"
        assert data["reputation_score"] == 85.0
        assert "created_at" in data
    
    def test_from_dict(self):
        """Test deserialization"""
        data = {
            "id": "test-id",
            "name": "TestAgent",
            "wallet_address": "test-wallet",
            "public_key": "test-pubkey",
            "reputation_score": 90.0,
            "total_rentals": 10,
        }
        
        identity = AgentIdentity.from_dict(data)
        
        assert identity.id == "test-id"
        assert identity.reputation_score == 90.0
        assert identity.total_rentals == 10
    
    def test_update_reputation(self):
        """Test reputation update"""
        identity = AgentIdentity(
            name="TestAgent",
            wallet_address="test-wallet",
            public_key="test-pubkey",
        )
        
        identity.update_reputation(95.0)
        
        assert identity.reputation_score == 95.0
    
    def test_increment_rentals(self):
        """Test rental count increment"""
        identity = AgentIdentity(
            name="TestAgent",
            wallet_address="test-wallet",
            public_key="test-pubkey",
        )
        
        identity.increment_rentals(completed=True)
        assert identity.total_rentals == 1
        assert identity.completed_rentals == 1
        
        identity.increment_rentals(completed=False)
        assert identity.total_rentals == 2
        assert identity.completed_rentals == 1
    
    def test_to_short_str(self):
        """Test short string representation"""
        identity = AgentIdentity(
            name="TestAgent",
            wallet_address="test-wallet",
            public_key="test-pubkey",
            reputation_score=85.0,
        )
        
        short = identity.to_short_str()
        
        assert "@TestAgent" in short
        assert "85" in short


class TestIdentityManager:
    """Tests for IdentityManager"""
    
    @pytest.fixture
    def manager(self):
        """Create test manager"""
        return IdentityManager()
    
    def test_list_identities(self, manager):
        """Test listing all identities"""
        identities = manager.list_identities()
        assert len(identities) >= 4  # Demo identities
    
    def test_get_by_wallet(self, manager):
        """Test getting by wallet"""
        identity = manager.get_by_wallet("happyclaw-agent.sol")
        assert identity is not None
        assert identity.name == "happyclaw-agent"
    
    def test_get_by_name(self, manager):
        """Test getting by name"""
        identity = manager.get_by_name("agent-alpha")
        assert identity is not None
        assert identity.wallet_address == "alpha.sol"
    
    def test_update_reputation(self, manager):
        """Test reputation update"""
        score = manager.update_reputation("alpha.sol", 95.0)
        assert score is not None
        assert score.reputation_score == 95.0
    
    def test_check_exists(self, manager):
        """Test checking if identity exists"""
        assert manager.check_exists("happyclaw-agent.sol") is True
        assert manager.check_exists("nonexistent.sol") is False


# ============ Reputation Tests ============

class TestReview:
    """Tests for Review"""
    
    def test_create_review(self):
        """Test creating a review"""
        review = Review(
            provider="agent-alpha",
            renter="agent-beta",
            skill="image-generation",
            rating=5,
            completed_on_time=True,
            comment="Great work!",
        )
        
        assert review.provider == "agent-alpha"
        assert review.rating == 5
        assert review.validate() is True
    
    def test_validate_invalid(self):
        """Test validation failure"""
        review = Review(
            provider="",  # Invalid
            renter="agent-beta",
            rating=5,
        )
        assert review.validate() is False


class TestReputationScore:
    """Tests for ReputationScore"""
    
    def test_calculate_new(self):
        """Test calculating score for new agent"""
        score = ReputationScore(agent_id="new-agent")
        calculated = score.calculate_score()
        
        assert calculated == 50.0  # Default for no reviews
    
    def test_calculate_with_reviews(self):
        """Test calculating score with reviews"""
        score = ReputationScore(
            agent_id="test-agent",
            total_reviews=5,
            average_rating=4.5,
            on_time_percentage=90.0,
        )
        
        calculated = score.calculate_score()
        
        assert calculated > 0
        assert calculated <= 100
    
    def test_calculate_perfect_score(self):
        """Test perfect score calculation"""
        score = ReputationScore(
            agent_id="perfect-agent",
            total_reviews=100,
            average_rating=5.0,
            on_time_percentage=100.0,
        )
        
        calculated = score.calculate_score()
        
        # Should be close to 100
        assert calculated >= 90


class TestReputationEngine:
    """Tests for ReputationEngine"""
    
    @pytest.fixture
    def engine(self):
        """Create test engine"""
        return ReputationEngine()
    
    def test_get_score(self, engine):
        """Test getting score"""
        score = engine.get_score("happyclaw-agent")
        assert score is not None
        assert score.reputation_score > 0
    
    def test_get_score_value(self, engine):
        """Test getting score value"""
        value = engine.get_score_value("happyclaw-agent")
        assert value == 85.0  # Demo value
    
    def test_add_review(self, engine):
        """Test adding a review"""
        review = Review(
            provider="new-agent",
            renter="test-renter",
            skill="test-skill",
            rating=5,
            completed_on_time=True,
            comment="Excellent!",
        )
        
        new_score = engine.add_review("new-agent", review)
        
        assert new_score.total_reviews == 1
        assert new_score.average_rating == 5.0
    
    def test_get_top_agents(self, engine):
        """Test getting top agents"""
        top = engine.get_top_agents(n=3)
        
        assert len(top) <= 3
        assert len(top) > 0
        # Should be sorted by score descending
        if len(top) >= 2:
            assert top[0][1] >= top[1][1]
    
    def test_get_reviews(self, engine):
        """Test getting reviews"""
        reviews = engine.get_reviews("happyclaw-agent")
        assert reviews is not None
        assert isinstance(reviews, list)


# ========== Pytest Configuration ==========

@pytest.fixture
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# ========== Run Tests ==========

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
