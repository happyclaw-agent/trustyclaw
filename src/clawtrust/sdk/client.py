"""
Solana RPC Client Wrapper

Provides a simple interface for Solana blockchain interactions.
"""

import asyncio
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Any
import os


class Network(Enum):
    """Solana network types"""
    MAINNET = "mainnet"
    TESTNET = "testnet"
    DEVNET = "devnet"


@dataclass
class ClientConfig:
    """Configuration for Solana client"""
    network: Network = Network.DEVNET
    rpc_url: Optional[str] = None
    ws_url: Optional[str] = None
    commitment: str = "confirmed"


class SolanaClient:
    """
    Simple Solana RPC client wrapper.
    
    Provides basic blockchain interactions for ClawTrust.
    """
    
    # Default RPC URLs
    RPC_URLS = {
        Network.MAINNET: "https://api.mainnet-beta.solana.com",
        Network.TESTNET: "https://api.testnet.solana.com",
        Network.DEVNET: "https://api.devnet.solana.com",
    }
    
    def __init__(self, config: Optional[ClientConfig] = None):
        self.config = config or ClientConfig()
        
        # Set RPC URL
        if self.config.rpc_url:
            self.rpc_url = self.config.rpc_url
        else:
            self.rpc_url = self.RPC_URLS.get(
                self.config.network,
                self.RPC_URLS[Network.DEVNET]
            )
        
        self.commitment = self.config.commitment
    
    async def get_balance(self, address: str) -> int:
        """
        Get the balance of a Solana address.
        
        Args:
            address: Base58 encoded public key
            
        Returns:
            Balance in lamports (1 SOL = 1e9 lamports)
        """
        # Mock implementation for MVP
        if address.startswith("Mock"):
            return 1_000_000_000  # 1 SOL mock balance
        
        # In real implementation:
        # async with httpx.AsyncClient() as client:
        #     response = await client.post(
        #         self.rpc_url,
        #         json={
        #             "jsonrpc": "2.0",
        #             "id": 1,
        #             "method": "getBalance",
        #             "params": [address],
        #         },
        #     )
        #     return response.json()["result"]["value"]
        
        return 0
    
    async def get_account_info(self, address: str) -> Optional[dict]:
        """
        Get account info for a Solana address.
        
        Args:
            address: Base58 encoded public key
            
        Returns:
            Account info dict or None
        """
        # Mock implementation
        if address.startswith("Mock"):
            return {
                "lamports": 1_000_000_000,
                "data": {},
                "owner": "MockProgram111111111111111111111111111111",
                "executable": False,
                "rentEpoch": 100,
            }
        
        return None
    
    async def get_latest_blockhash(self) -> str:
        """
        Get the latest blockhash.
        
        Returns:
            Blockhash as base58 string
        """
        # Mock
        return "mockblockhash123456789abcdefghijklmnopqrstuvwxyz"
    
    async def send_transaction(
        self,
        transaction: bytes,
        signatures: list[str],
    ) -> str:
        """
        Send a signed transaction.
        
        Args:
            transaction: Signed transaction bytes
            signatures: List of base58 signatures
            
        Returns:
            Transaction signature (tx id)
        """
        # Mock implementation
        return f"mocktx{hash(transaction) % 1_000_000}"
    
    async def get_token_balance(
        self,
        token_account: str,
        mint: str,
    ) -> int:
        """
        Get token balance for a token account.
        
        Args:
            token_account: Token account address
            mint: Token mint address
            
        Returns:
            Token balance (raw, not decimals)
        """
        # Mock for USDC
        if mint.startswith("EPj"):  # USDC mint
            return 1_000_000  # 1 USDC mock
        
        return 0
    
    async def get_token_accounts_by_owner(
        self,
        owner: str,
        mint: Optional[str] = None,
    ) -> list[dict]:
        """
        Get all token accounts owned by an address.
        
        Args:
            owner: Owner's public key
            mint: Optional token mint to filter
            
        Returns:
            List of token account dicts
        """
        # Mock
        return []
    
    async def get_recent_blockhash(self) -> str:
        """Alias for get_latest_blockhash"""
        return await self.get_latest_blockhash()
    
    def derive_pda(
        self,
        seeds: list[bytes],
        program_id: str,
    ) -> tuple[str, int]:
        """
        Derive a PDA (Program Derived Address).
        
        Args:
            seeds: List of seed bytes
            program_id: Program's public key
            
        Returns:
            Tuple of (address, bump)
        """
        # Mock implementation
        # In real: use solders.pubkey.Pubkey.find_program_address()
        import hashlib
        combined = b"".join(seeds) + program_id.encode()
        hash_digest = hashlib.sha256(combined).digest()
        
        # Take first 32 bytes as address
        address_bytes = hash_digest[:32]
        address = "".join(f"{b:02x}" for b in address_bytes)
        
        return (address, 255)
    
    def get_rpc_url(self) -> str:
        """Get the configured RPC URL"""
        return self.rpc_url
    
    def get_network(self) -> Network:
        """Get the configured network"""
        return self.config.network


# ============ Mock Wallet ============

class MockWallet:
    """Mock wallet for testing"""
    
    def __init__(self, private_key: str = None):
        self.private_key = private_key or "mockprivatekey123"
        self.public_key = f"MockPublicKey{hash(self.private_key) % 1000:04d}"
        self.address = f"MockAddress{hash(self.public_key) % 1000:04d}"
    
    async def get_balance(self) -> int:
        """Get SOL balance"""
        return 1_000_000_000  # 1 SOL
    
    async def get_usdc_balance(self) -> int:
        """Get USDC balance"""
        return 1_000_000  # 1 USDC


# ============ CLI Helpers ============

def get_client(network: str = "devnet") -> SolanaClient:
    """Get a Solana client for the given network"""
    network_enum = Network.DEVNET
    if network == "mainnet":
        network_enum = Network.MAINNET
    elif network == "testnet":
        network_enum = Network.TESTNET
    
    return SolanaClient(ClientConfig(network=network_enum))


# ============ Tests ============

if __name__ == "__main__":
    import asyncio
    
    async def test_client():
        client = SolanaClient(ClientConfig(network=Network.DEVNET))
        
        # Test get balance
        balance = await client.get_balance("MockWallet123")
        print(f"Mock wallet balance: {balance} lamports")
        
        # Test PDA derivation
        addr, bump = client.derive_pda(
            [b"escrow", b"provider123"],
            "ESCRW1111111111111111111111111111111111111",
        )
        print(f"PDA derived: {addr} (bump: {bump})")
    
    asyncio.run(test_client())
