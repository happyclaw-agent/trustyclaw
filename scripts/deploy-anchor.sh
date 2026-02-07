#!/bin/bash
# TrustyClaw Anchor Deployment Script
# Run this to deploy escrow program to devnet

set -e

echo "=== TrustyClaw Anchor Deployment ==="
echo ""

# Check if Anchor is installed
if ! command -v anchor &> /dev/null; then
    echo "❌ Anchor not installed. Install with:"
    echo "   cargo install --git https://github.com/coral-xyz/anchor anchor-cli --locked"
    exit 1
fi

# Check Anchor version
anchor --version

# Set up Solana config
echo ""
echo "=== Setting up Solana config ==="
solana config get

# Check wallet balance
echo ""
echo "=== Wallet Balance ==="
solana balance

# Build the program
echo ""
echo "=== Building Escrow Program ==="
cd programs/escrow
anchor build

# Deploy to devnet
echo ""
echo "=== Deploying to Devnet ==="
anchor deploy --provider.cluster devnet

# Get the new program ID
echo ""
echo "=== Program Deployed ==="
echo "Program ID: $(grep 'declare_id' src/lib.rs | grep -o '"[^"]*"' | tr -d '\"')"

# Update Anchor.toml if needed
echo ""
echo "=== Done! ==="
echo "Run: anchor deploy --provider.cluster devnet"
