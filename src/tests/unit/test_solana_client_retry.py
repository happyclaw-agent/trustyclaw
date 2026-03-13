import asyncio

import httpx
import pytest

from trustyclaw.sdk.client import ClientConfig, Network, SolanaClient


class _StubResponse:
    def __init__(self, payload: dict, status_code: int = 200, url: str = "https://rpc.test"):
        self._payload = payload
        self.status_code = status_code
        self.url = url

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            request = httpx.Request("POST", self.url)
            response = httpx.Response(self.status_code, request=request)
            raise httpx.HTTPStatusError("HTTP error", request=request, response=response)

    def json(self) -> dict:
        return self._payload


def test_get_latest_blockhash_succeeds_after_retries(monkeypatch):
    attempts = {"count": 0}
    sleep_delays: list[float] = []

    async def fake_sleep(delay: float) -> None:
        sleep_delays.append(delay)

    class StubAsyncClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def post(self, url, json):
            attempts["count"] += 1
            if attempts["count"] < 3:
                raise httpx.ConnectError("temporary failure", request=httpx.Request("POST", url))
            return _StubResponse(
                {"result": {"value": {"blockhash": "test-blockhash"}}},
                url=url,
            )

    monkeypatch.setattr(httpx, "AsyncClient", StubAsyncClient)
    monkeypatch.setattr("trustyclaw.sdk.retry.asyncio.sleep", fake_sleep)

    client = SolanaClient(
        ClientConfig(
            network=Network.DEVNET,
            max_retries=3,
            backoff_base_seconds=0.01,
            backoff_max_seconds=1.0,
            backoff_jitter_seconds=0.0,
        )
    )

    result = asyncio.run(client.get_latest_blockhash())

    assert result == "test-blockhash"
    assert attempts["count"] == 3
    assert sleep_delays == [0.01, 0.02]


def test_get_balance_raises_after_max_retries(monkeypatch):
    attempts = {"count": 0}
    sleep_delays: list[float] = []

    async def fake_sleep(delay: float) -> None:
        sleep_delays.append(delay)

    class StubAsyncClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def post(self, url, json):
            attempts["count"] += 1
            raise httpx.ConnectError("still failing", request=httpx.Request("POST", url))

    monkeypatch.setattr(httpx, "AsyncClient", StubAsyncClient)
    monkeypatch.setattr("trustyclaw.sdk.retry.asyncio.sleep", fake_sleep)

    client = SolanaClient(
        ClientConfig(
            network=Network.DEVNET,
            max_retries=2,
            backoff_base_seconds=0.01,
            backoff_max_seconds=1.0,
            backoff_jitter_seconds=0.0,
        )
    )

    with pytest.raises(httpx.ConnectError):
        asyncio.run(client.get_balance("wallet-address"))

    assert attempts["count"] == 3
    assert sleep_delays == [0.01, 0.02]


def test_non_retryable_rpc_error_fails_immediately(monkeypatch):
    attempts = {"count": 0}
    sleep_delays: list[float] = []

    async def fake_sleep(delay: float) -> None:
        sleep_delays.append(delay)

    class StubAsyncClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def post(self, url, json):
            attempts["count"] += 1
            return _StubResponse(
                {"error": {"code": -32602, "message": "Invalid params"}},
                url=url,
            )

    monkeypatch.setattr(httpx, "AsyncClient", StubAsyncClient)
    monkeypatch.setattr("trustyclaw.sdk.retry.asyncio.sleep", fake_sleep)

    client = SolanaClient(
        ClientConfig(
            network=Network.DEVNET,
            max_retries=3,
            backoff_base_seconds=0.01,
            backoff_max_seconds=1.0,
            backoff_jitter_seconds=0.0,
        )
    )

    with pytest.raises(RuntimeError, match="RPC error"):
        asyncio.run(client.get_balance("wallet-address"))

    assert attempts["count"] == 1
    assert sleep_delays == []
