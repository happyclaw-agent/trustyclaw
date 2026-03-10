"""Unit tests for escrow_contract simulation lifecycle and failure paths."""

import pytest

from trustyclaw.sdk.escrow_contract import EscrowClient, EscrowState, EscrowTerms


class TestEscrowTerms:
    """Tests for EscrowTerms dataclass."""

    def test_creation(self) -> None:
        terms = EscrowTerms(
            skill_name="image-generation",
            duration_seconds=86400,
            price_usdc=1000000,
            metadata_uri="https://example.com/metadata.json",
        )

        assert terms.skill_name == "image-generation"
        assert terms.price_usdc == 1000000


class TestEscrowClientSimulation:
    """Tests for EscrowClient simulation lifecycle methods."""

    @pytest.fixture
    def client(self) -> EscrowClient:
        return EscrowClient(network="devnet")

    def test_initialization(self, client: EscrowClient) -> None:
        assert client is not None

    def test_full_simulated_lifecycle(self, client: EscrowClient) -> None:
        created = client.create_escrow(
            renter="renter_wallet",
            provider="provider_wallet",
            skill_id="skill-1",
            amount=2500000,
            duration_hours=24,
            deliverable_hash="abc123",
        )
        assert created.state == EscrowState.CREATED

        funded = client.fund_escrow(created.escrow_id)
        assert funded.state == EscrowState.FUNDED

        active = client.activate_escrow(created.escrow_id)
        assert active.state.value == "active"

        completed = client.complete_escrow(created.escrow_id, "deliverable_hash")
        assert completed.state.value == "completed"

        released = client.release_escrow(created.escrow_id)
        assert released.state == EscrowState.RELEASED
        assert client.release_amount_for_escrow(created.escrow_id) == 2500000

    def test_fund_missing_escrow_raises(self, client: EscrowClient) -> None:
        with pytest.raises(ValueError, match="not found"):
            client.fund_escrow("missing")

    def test_activate_unfunded_escrow_raises(self, client: EscrowClient) -> None:
        created = client.create_escrow(
            renter="renter_wallet",
            provider="provider_wallet",
            skill_id="skill-2",
            amount=100,
            duration_hours=1,
            deliverable_hash="hash-1",
        )

        with pytest.raises(ValueError, match="unfunded"):
            client.activate_escrow(created.escrow_id)

    def test_complete_inactive_escrow_raises(self, client: EscrowClient) -> None:
        created = client.create_escrow(
            renter="renter_wallet",
            provider="provider_wallet",
            skill_id="skill-3",
            amount=100,
            duration_hours=1,
            deliverable_hash="hash-2",
        )

        with pytest.raises(ValueError, match="inactive"):
            client.complete_escrow(created.escrow_id, "deliverable")

    def test_release_uncompleted_escrow_raises(self, client: EscrowClient) -> None:
        created = client.create_escrow(
            renter="renter_wallet",
            provider="provider_wallet",
            skill_id="skill-4",
            amount=100,
            duration_hours=1,
            deliverable_hash="hash-3",
        )
        client.fund_escrow(created.escrow_id)

        with pytest.raises(ValueError, match="uncompleted"):
            client.release_escrow(created.escrow_id)

    def test_release_amount_missing_returns_zero(self, client: EscrowClient) -> None:
        assert client.release_amount_for_escrow("missing") == 0
