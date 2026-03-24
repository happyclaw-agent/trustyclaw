import os

from trustyclaw.sdk.solana import Network, SolanaRPCClient, get_client


def test_get_client_defaults_to_devnet_for_unknown_network(monkeypatch):
    monkeypatch.delenv("SOLANA_KEYPAIR_PATH", raising=False)

    client = get_client("not-a-network")

    assert client.network == Network.DEVNET


def test_get_client_is_case_insensitive(monkeypatch):
    monkeypatch.delenv("SOLANA_KEYPAIR_PATH", raising=False)

    client = get_client("MAINNET")

    assert client.network == Network.MAINNET


def test_missing_keypair_path_keeps_address_none(tmp_path):
    missing_keypair = tmp_path / "does-not-exist.json"
    assert not os.path.exists(missing_keypair)

    client = SolanaRPCClient(network=Network.DEVNET, keypair_path=str(missing_keypair))

    assert client.address is None
