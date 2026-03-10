"""Unit tests for escrow contract boundaries and simulation lifecycle."""

import pytest

from trustyclaw.sdk.escrow_contract import EscrowClient, EscrowState, EscrowTerms, get_escrow_client


class TestEscrowTerms:
    def test_creation(self):
        terms = EscrowTerms(
            skill_name="image-generation",
            duration_seconds=86400,
            price_usdc=1_000_000,
            metadata_uri="https://example.com/metadata.json",
        )
        assert terms.skill_name == "image-generation"
        assert terms.price_usdc == 1_000_000


class TestEscrowStateDefinition:
    def test_state_enum_contains_all_expected_unique_values(self):
        values = [state.value for state in EscrowState]
        assert len(values) == len(set(values))
        assert values == [
            "created",
            "funded",
            "active",
            "completed",
            "released",
            "refunded",
            "disputed",
        ]


class TestEscrowClientSimulationLifecycle:
    def test_full_simulation_lifecycle(self):
        client = EscrowClient()
        created = client.create_escrow(
            renter="renter",
            provider="provider",
            skill_id="skill",
            amount=500_000,
            duration_hours=12,
            deliverable_hash="d1",
        )
        assert created.state is EscrowState.CREATED

        funded = client.fund_escrow(created.escrow_id)
        assert funded.state is EscrowState.FUNDED

        active = client.activate_escrow(created.escrow_id)
        assert active.state is EscrowState.ACTIVE

        completed = client.complete_escrow(created.escrow_id, "deliverable")
        assert completed.state is EscrowState.COMPLETED

        released = client.release_escrow(created.escrow_id)
        assert released.state is EscrowState.RELEASED

    def test_guardrails_for_invalid_transitions(self):
        client = EscrowClient()
        created = client.create_escrow(
            renter="renter",
            provider="provider",
            skill_id="skill",
            amount=123,
            duration_hours=1,
            deliverable_hash="d1",
        )

        with pytest.raises(ValueError, match="Cannot activate unfunded escrow"):
            client.activate_escrow(created.escrow_id)

        with pytest.raises(ValueError, match="Cannot complete inactive escrow"):
            client.complete_escrow(created.escrow_id, "deliverable")

    def test_release_amount_for_unknown_escrow(self):
        client = EscrowClient()
        assert client.release_amount_for_escrow("missing") == 0


class TestEscrowClientFactory:
    def test_back_compat_network_positional_argument(self):
        client = get_escrow_client("devnet")
        assert client.network == "devnet"

    def test_client_initialization(self):
        assert EscrowClient() is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
