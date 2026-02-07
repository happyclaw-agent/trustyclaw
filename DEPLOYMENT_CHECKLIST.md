# TrustyClaw Deployment Checklist

## Prerequisites

### System Requirements
- [ ] Ubuntu Linux (recommended) or macOS
- [ ] At least 16GB RAM
- [ ] 10GB free disk space
- [ ] Internet connection for Solana devnet

### Required Tools
- [ ] **Rust** (exactly 1.75.0)
- [ ] **Solana CLI** (v1.18.x)
- [ ] **Anchor CLI** (exactly 0.30.1)
- [ ] **Node.js** (v18+, for TypeScript tests)
- [ ] **Yarn** (for Anchor TypeScript)

---

## Step 1: Install System Dependencies

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y build-essential pkg-config libssl-dev curl git
```

---

## Step 2: Install Rust (Exactly 1.75.0)

```bash
# Remove existing Rust
rustup self uninstall 2>/dev/null || true

# Install Rust 1.75.0
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
source ~/.cargo/env

rustup install 1.75.0
rustup default 1.75.0
rustc --version  # Should show: rustc 1.75.0 (82e1608df 2023-12-21)
```

---

## Step 3: Install Solana CLI (v1.18.x)

```bash
# Remove existing Solana CLI
rm -rf ~/.local/share/solana
rm -f ~/.cargo/bin/solana

# Install Solana v1.18.22
curl -sSfL https://release.solana.com/v1.18.22/install | sh

# Add to PATH
export PATH="$HOME/.local/share/solana/install/active_release/bin:$PATH"

# Verify
solana --version  # Should show: solana-cli 1.18.22
```

---

## Step 4: Install Anchor CLI (Exactly 0.30.1)

```bash
# Remove existing Anchor
rm -f ~/.cargo/bin/anchor

# Install Anchor 0.30.1 from git tag
cargo install --git https://github.com/coral-xyz/anchor anchor-cli --tag v0.30.1 --locked

# Verify
anchor --version  # Should show: anchor-cli 0.30.1
```

---

## Step 5: Configure Solana

```bash
# Set to devnet
solana config set --url devnet

# Create/import wallet (IMPORTANT: Save the recovery phrase!)
solana-keygen new -o ~/.config/solana/id.json

# Verify wallet
solana address  # Should show your wallet address

# Request airdrop (max 2 SOL per request)
solana airdrop 2

# Check balance
solana balance
```

---

## Step 6: Clone and Setup TrustyClaw

```bash
# Clone repository
git clone https://github.com/happyclaw-agent/trustyclaw.git
cd trustyclaw

# Checkout main branch
git checkout main

# Install Node dependencies (for TypeScript tests)
npm install  # or yarn install

# Verify Python environment
python3 --version  # Should be 3.10+
pip3 install -r requirements.txt
```

---

## Step 7: Build Anchor Programs

```bash
# Navigate to escrow program
cd programs/escrow

# Clean any previous builds
rm -rf target

# Build the program
anchor build

# Verify build
ls -la target/deploy/  # Should show escrow.so
```

**If you get "String is the wrong size" error:**
```bash
# Try these fixes:

# 1. Delete Cargo.lock and rebuild
cd /home/happyclaw/.openclaw/workspace/trustyclaw
rm -f Cargo.lock
cd programs/escrow
anchor build --skip-lint

# 2. If still failing, clear cargo cache
cargo clean
rm -rf ~/.cargo/registry/cache/*
rm -rf ~/.cargo/registry/index/*

# 3. Try Rust 1.80.0 instead
rustup install 1.80.0
rustup default 1.80.0
anchor build
```

---

## Step 8: Deploy to Devnet

```bash
# Deploy escrow program
cd programs/escrow
anchor deploy --provider.cluster devnet

# Note the program address (output will show it)
# Example: "Program address: ESCRwJwfT1XpTwzPfkQ9NyTXfHWHnhCWdK1vYhmjbUF"

# Set environment variable
export ESCROW_PROGRAM_ID=$(solana address -k target/deploy/escrow-keypair.json)
echo "Escrow Program ID: $ESCROW_PROGRAM_ID"
```

---

## Step 9: Verify Deployment

```bash
# Check program on-chain
solana account $ESCROW_PROGRAM_ID

# Should show:
# Balance: 0.0011412 SOL
# Owner: BPFLoaderUpgradeab1e11111111111111111111111
# Executable: true
```

---

## Step 10: Set Environment Variables

Create a `.env` file in the project root:

```bash
# .env
export ESCROW_PROGRAM_ID="ESCRwJwfT1XpTwzPfkQ9NyTXfHWHnhCWdK1vYhmjbUF"
export REPUTATION_PROGRAM_ID="REPW1111111111111111111111111111111111111"
export SOLANA_NETWORK="devnet"
export SOLANA_KEYPAIR_PATH="~/.config/solana/id.json"
export RPC_URL="https://api.devnet.solana.com"
```

Load it:
```bash
source .env
```

---

## Step 11: Run Tests

```bash
# Run Python tests
python3 -m pytest src/tests/unit/ -v

# Run with coverage
python3 -m pytest --cov=src src/tests/unit/ -v
```

---

## Step 12: Run Demo

### Mock Mode (Always Works)
```bash
python3 demo.py
```

### On-Chain Mode (Requires Deployment)
```bash
python3 demo.py --onchain
```

---

## Troubleshooting

### Error: "String is the wrong size"
This is a Borsh version conflict. Try:
```bash
# Clear cargo cache
rm -rf ~/.cargo/registry/cache/*
rm -rf ~/.cargo/registry/index/*
rm -rf target
rm -f Cargo.lock

# Try with Rust 1.80.0
rustup install 1.80.0
rustup default 1.80.0
anchor build
```

### Error: "Program not deployed"
```bash
# Check if program exists
solana account ESCRwJwfT1XpTwzPfkQ9NyTXfHWHnhCWdK1vYhmjbUF

# If not, redeploy
anchor deploy --provider.cluster devnet
```

### Error: "Insufficient funds"
```bash
# Request more airdrop
solana airdrop 2

# Check balance
solana balance
```

### Error: "Anchor not found"
```bash
# Verify anchor installation
which anchor
anchor --version

# Reinstall if needed
cargo install --git https://github.com/coral-xyz/anchor anchor-cli --tag v0.30.1 --locked
```

---

## Quick Reference Commands

```bash
# Start fresh
cd trustyclaw
rm -rf target Cargo.lock programs/*/Cargo.lock programs/*/target
git checkout programs/escrow/src/lib.rs
anchor build --skip-lint
anchor deploy --provider.cluster devnet

# Check status
solana cluster-version  # Should be 1.18.x
anchor --version       # Should be 0.30.1
rustc --version        # Should be 1.75.0 or 1.80.0

# Deploy and test
export ESCROW_PROGRAM_ID=$(solana address -k target/deploy/escrow-keypair.json)
python3 demo.py --onchain
```

---

## Post-Deployment

### Add Program IDs to GitHub Secrets (Optional)
For CI/CD:
- Go to: https://github.com/happyclaw-agent/trustyclaw/settings/secrets
- Add:
  - `ESCROW_PROGRAM_ID`: your deployed program address
  - `SOLANA_PRIVATE_KEY`: wallet private key (base58)

### Update Documentation
- Update `Anchor.toml` with new program IDs
- Update `demo.py` comments
- Commit and push changes

---

## Expected Output

### Successful Build:
```
Building escrow...
Build success. Completed work...
Deploying...
Deployment success. Program Id: ESCRwJwfT1XpTwzPfkQ9NyTXfHWHnhCWdK1vYhmjbUF
```

### Successful Demo (On-Chain):
```
=== TRUSTYCLAW DEMO APPLICATION ===

Mode: ON-CHAIN

=== SOLANA INTEGRATION ===
Network: devnet
Provider: GFeyFZLmvsw...
Balance: 5.0 SOL

=== ESCROW CONTRACT ===
Created: escrow_xxx...
State: created
...
```

---

## Timeline

| Step | Action | Time |
|------|--------|------|
| 1-4 | Install dependencies | 10-15 min |
| 5 | Configure Solana | 2 min |
| 6-7 | Build programs | 5-10 min |
| 8-9 | Deploy to devnet | 2 min |
| 10-12 | Run demo | 2 min |
| **Total** | | **~25 min** |

---

## Questions?

- **Repo**: https://github.com/happyclaw-agent/trustyclaw
- **Discord**: https://discord.com/invite/clawd
- **Documentation**: https://docs.openclaw.ai
