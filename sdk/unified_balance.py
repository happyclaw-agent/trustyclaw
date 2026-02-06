"""
Unified Balance API for TrustyClaw

Provides aggregated balance viewing across multiple chains.
Supports Solana, Ethereum, Polygon, and Arbitrum.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Union
from datetime import datetime
import os


class Chain(Enum):
    """Supported blockchain networks"""
    SOLANA = "solana"
    ETHEREUM = "ethereum"
    POLYGON = "polygon"
    ARBITRUM = "arbitrum"


class Token(Enum):
    """Supported tokens"""
    USDC = "USDC"
    SOL = "SOL"
    ETH = "ETH"
    MATIC = "MATIC"


@dataclass
class UnionWallet:
    """Unified wallet across chains"""
    solana: Optional[str] = None
    ethereum: Optional[str] = None
    polygon: Optional[str] = None
    arbitrum: Optional[str] = None
    
    def get_address(self, chain: Chain) -> Optional[str]:
        """Get address for a specific chain"""
        if chain == Chain.SOLANA:
            return self.solana
        elif chain == Chain.ETHEREUM:
            return self.ethereum
        elif chain == Chain.POLYGON:
            return self.polygon
        elif chain == Chain.ARBITRUM:
            return self.arbitrum
        return None
    
    def get_chains(self) -> List[Chain]:
        """Get list of chains with addresses"""
        chains = []
        if self.solana:
            chains.append(Chain.SOLANA)
        if self.ethereum:
            chains.append(Chain.ETHEREUM)
        if self.polygon:
            chains.append(Chain.POLYGON)
        if self.arbitrum:
            chains.append(Chain.ARBITRUM)
        return chains


@dataclass
class ChainBalance:
    """Balance for a specific chain"""
    chain: Chain
    token: Token
    balance: float
    balance_raw: int
    usd_value: float
    last_updated: datetime


@dataclass
class AggregatedBalance:
    """Aggregated balance across all chains"""
    total_usd_value: float
    balances: Dict[str, ChainBalance]  # chain -> balance
    breakdown: Dict[str, float]  # chain -> percentage
    last_updated: datetime


class UnifiedBalance:
    """
    Unified balance aggregator for multi-chain wallets.
    
    Provides:
    - View balances across all chains
    - Get total portfolio value
    - Track allocation percentages
    
    Usage:
        wallet = UnionWallet(
            solana="...",
            ethereum="0x...",
            polygon="0x...",
        )
        
        balances = unified.get_all_balances([wallet])
        total = unified.get_total_value(wallet, prices)
    """
    
    # Token decimals
    DECIMALS = {
        Token.USDC: 6,
        Token.SOL: 9,
        Token.ETH: 18,
        Token.MATIC: 18,
    }
    
    # Mock balances for devnet
    MOCK_BALANCES = {
        Chain.SOLANA: {
            Token.USDC: 5000.0,
            Token.SOL: 10.5,
        },
        Chain.ETHEREUM: {
            Token.USDC: 2500.0,
            Token.ETH: 2.5,
        },
        Chain.POLYGON: {
            Token.USDC: 1000.0,
            Token.MATIC: 500.0,
        },
        Chain.ARBITRUM: {
            Token.USDC: 750.0,
            Token.ETH: 1.0,
        },
    }
    
    def __init__(self, network: str = "devnet"):
        """
        Initialize unified balance client.
        
        Args:
            network: Network mode ('devnet', 'testnet', 'mainnet')
        """
        self.network = network
    
    def _get_mock_balance(
        self,
        chain: Chain,
        token: Token,
        wallet_address: str,
    ) -> float:
        """Get mock balance for devnet/testnet"""
        if chain in self.MOCK_BALANCES:
            if token in self.MOCK_BALANCES[chain]:
                return self.MOCK_BALANCES[chain][token]
        
        # Return a consistent mock based on address
        if wallet_address:
            return float(len(wallet_address) * 10)
        return 0.0
    
    def _get_real_balance(
        self,
        chain: Chain,
        token: Token,
        wallet_address: str,
    ) -> float:
        """
        Get real balance from blockchain.
        
        This is a placeholder for actual blockchain queries.
        """
        # In mainnet, would query actual RPC endpoints
        return self._get_mock_balance(chain, token, wallet_address)
    
    def get_balance(
        self,
        chain: Chain,
        token: Token,
        wallet_address: str,
    ) -> float:
        """
        Get balance for a specific chain and token.
        
        Args:
            chain: Blockchain network
            token: Token type
            wallet_address: Wallet address
            
        Returns:
            Balance in token units
        """
        if self.network == "mainnet":
            return self._get_real_balance(chain, token, wallet_address)
        else:
            return self._get_mock_balance(chain, token, wallet_address)
    
    def get_all_balances(
        self,
        wallets: List[UnionWallet],
    ) -> Dict[str, float]:
        """
        Get all USDC balances across all chains.
        
        Args:
            wallets: List of unified wallets
            
        Returns:
            Dict mapping chain name to total balance
        """
        balances: Dict[str, float] = {
            Chain.SOLANA.value: 0.0,
            Chain.ETHEREUM.value: 0.0,
            Chain.POLYGON.value: 0.0,
            Chain.ARBITRUM.value: 0.0,
        }
        
        for wallet in wallets:
            for chain in wallet.get_chains():
                address = wallet.get_address(chain)
                if address:
                    balance = self.get_balance(chain, Token.USDC, address)
                    balances[chain.value] += balance
        
        return balances
    
    def get_chain_balances(
        self,
        wallet: UnionWallet,
        tokens: List[Token] = None,
    ) -> Dict[str, ChainBalance]:
        """
        Get detailed balances for all chains and tokens.
        
        Args:
            wallet: Unified wallet
            tokens: List of tokens to check (defaults to all)
            
        Returns:
            Dict mapping chain to ChainBalance
        """
        if tokens is None:
            tokens = [Token.USDC]
        
        balances: Dict[str, ChainBalance] = {}
        
        for chain in wallet.get_chains():
            address = wallet.get_address(chain)
            if not address:
                continue
            
            for token in tokens:
                balance = self.get_balance(chain, token, address)
                raw_balance = int(balance * (10 ** self.DECIMALS[token]))
                
                balances[chain.value] = ChainBalance(
                    chain=chain,
                    token=token,
                    balance=balance,
                    balance_raw=raw_balance,
                    usd_value=balance,  # USDC is 1:1 with USD
                    last_updated=datetime.utcnow(),
                )
        
        return balances
    
    def get_total_value(
        self,
        wallets: List[UnionWallet],
        prices: Dict[str, float] = None,
    ) -> float:
        """
        Get total portfolio value in USD.
        
        Args:
            wallets: List of unified wallets
            prices: Dict of token -> USD price (optional)
            
        Returns:
            Total value in USD
        """
        if prices is None:
            # Default prices
            prices = {
                "USDC": 1.0,
                "SOL": 100.0,
                "ETH": 2500.0,
                "MATIC": 0.8,
            }
        
        total = 0.0
        
        for wallet in wallets:
            for chain in wallet.get_chains():
                address = wallet.get_address(chain)
                if not address:
                    continue
                
                # Get USDC balance (1:1 with USD)
                usdc_balance = self.get_balance(chain, Token.USDC, address)
                total += usdc_balance * prices.get("USDC", 1.0)
                
                # Get native token balance
                if chain == Chain.SOLANA:
                    native_balance = self.get_balance(chain, Token.SOL, address)
                    total += native_balance * prices.get("SOL", 100.0)
                elif chain == Chain.ETHEREUM:
                    native_balance = self.get_balance(chain, Token.ETH, address)
                    total += native_balance * prices.get("ETH", 2500.0)
                elif chain == Chain.POLYGON:
                    native_balance = self.get_balance(chain, Token.MATIC, address)
                    total += native_balance * prices.get("MATIC", 0.8)
                elif chain == Chain.ARBITRUM:
                    native_balance = self.get_balance(chain, Token.ETH, address)
                    total += native_balance * prices.get("ETH", 2500.0)
        
        return total
    
    def get_allocation(
        self,
        wallets: List[UnionWallet],
        prices: Dict[str, float] = None,
    ) -> Dict[str, float]:
        """
        Get portfolio allocation percentages.
        
        Args:
            wallets: List of unified wallets
            prices: Dict of token -> USD price (optional)
            
        Returns:
            Dict mapping chain to percentage of total
        """
        total_value = self.get_total_value(wallets, prices)
        
        if total_value == 0:
            return {
                Chain.SOLANA.value: 0.0,
                Chain.ETHEREUM.value: 0.0,
                Chain.POLYGON.value: 0.0,
                Chain.ARBITRUM.value: 0.0,
            }
        
        balances = self.get_all_balances(wallets)
        
        allocation: Dict[str, float] = {}
        for chain, balance in balances.items():
            allocation[chain] = (balance / total_value) * 100
        
        return allocation
    
    def get_aggregated_balance(
        self,
        wallets: List[UnionWallet],
        prices: Dict[str, float] = None,
    ) -> AggregatedBalance:
        """
        Get complete aggregated balance view.
        
        Args:
            wallets: List of unified wallets
            prices: Dict of token -> USD price (optional)
            
        Returns:
            AggregatedBalance with all details
        """
        balances = self.get_all_balances(wallets)
        total_value = self.get_total_value(wallets, prices)
        allocation = self.get_allocation(wallets, prices)
        
        chain_balances: Dict[str, ChainBalance] = {}
        for wallet in wallets:
            chain_details = self.get_chain_balances(wallet)
            for chain, cb in chain_details.items():
                if chain not in chain_balances:
                    chain_balances[chain] = cb
        
        return AggregatedBalance(
            total_usd_value=total_value,
            balances=chain_balances,
            breakdown=allocation,
            last_updated=datetime.utcnow(),
        )
    
    def compare_wallets(
        self,
        wallets: List[UnionWallet],
    ) -> Dict[str, Dict[str, float]]:
        """
        Compare balances across multiple wallets.
        
        Args:
            wallets: List of wallets to compare
            
        Returns:
            Dict of wallet index -> chain balances
        """
        results: Dict[str, Dict[str, float]] = {}
        
        for i, wallet in enumerate(wallets):
            balances = self.get_all_balances([wallet])
            results[f"wallet_{i}"] = balances
        
        return results
    
    def get_supported_chains(self) -> List[Chain]:
        """Get list of supported chains"""
        return [
            Chain.SOLANA,
            Chain.ETHEREUM,
            Chain.POLYGON,
            Chain.ARBITRUM,
        ]


def get_unified_balance(network: str = "devnet") -> UnifiedBalance:
    """
    Get unified balance client.
    
    Args:
        network: Network mode ('devnet', 'testnet', 'mainnet')
        
    Returns:
        Configured UnifiedBalance instance
    """
    return UnifiedBalance(network=network)
