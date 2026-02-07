#!/bin/bash
# TrustyClaw Deployment Script
# Run this on your LOCAL machine to deploy the escrow program

set -e

echo "=== TrustyClaw Escrow Program Deployment ==="
echo ""

# Step 1: Install Rust nightly (for edition2024 support)
echo "Step 1: Installing Rust nightly..."
rustup install nightly
rustup default nightly

# Step 2: Install Anchor CLI v0.30.1
echo "Step 2: Installing Anchor CLI v0.30.1..."
cargo install --git https://github.com/coral-xyz/anchor anchor-cli --tag v0.30.1 --locked

# Step 3: Pull latest code
echo "Step 3: Pulling latest code..."
git pull origin main

# Step 4: Build the program
echo "Step 4: Building escrow program..."
cd programs/escrow
anchor build

# Step 5: Deploy to devnet
echo "Step 5: Deploying to devnet..."
anchor deploy --provider.cluster devnet

echo ""
echo "=== Deployment Complete! ==="
echo ""
echo "Program ID (save this):"
grep 'declare_id!' src/lib.rs | grep -o '"[^"]*"' | tr -d '"'
echo ""
echo "Next: Update demo.py with the deployed program ID and test!"
