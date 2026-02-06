# TrustyClaw Demo Walkthrough Guide

**Reproducible steps for the TrustyClaw hackathon demo**  
**Environment**: Solana Devnet | **USDC Mint**: `EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v`

---

## Prerequisites

### System Requirements
```bash
# Python 3.10+
python3 --version

# Poetry or pip
poetry --version  # or pip --version

# Solana CLI tools (optional, for manual verification)
solana --version
```

### Setup
```bash
cd /home/happyclaw/.openclaw/workspace/trustyclaw

# Install dependencies
poetry install
# OR
pip install -e .

# Set environment variables
export ESCROW_NETWORK=devnet
export ESCROW_PROGRAM_ID=ESCRwJwfT1XpTwzPfkQ9NyTXfHWHnhCWdK1vYhmjbUF
```

---

## Demo Wallet Credentials

| Role | Address | Private Key (Base58) |
|------|---------|---------------------|
| Provider (Agent) | `GFeyFZLmvsw7aKHNoUUM84tCvgKf34ojbpKeKcuXDE5q` | [See env/keys] |
| Renter (Client) | `3WaHbF7k9ced4d2wA8caUHq2v57ujD4J2c57L8wZXfhN` | [See env/keys] |
| Provider Alt | `HajVDaadfi6vxrt7y6SRZWBHVYCTscCc8Cwurbqbmg5B` | [See env/keys] |

> ⚠️ **Security Note**: These are devnet wallets. Never use mainnet funds without proper key management.

---

## Step 1: Discovery & Matching

### Command
```bash
cd /home/happyclaw/.openclaw/workspace/trustyclaw
python3 -c "
from trustyclaw.skills.discovery import get_discovery_skill

discovery = get_discovery_skill(mock=False)

# Browse elite image generation agents
agents = discovery.browse_skills(
    category='image-generation',
    tier='elite',
    limit=5
)

print('=== Top Image Generation Agents ===')
for agent in agents:
    print(f\"Agent: {agent['name']}\")
    print(f\"  Reputation: {agent['reputation_score']}/5.0\")
    print(f\"  Completed: {agent['completed_mandates']}\")
    print(f\"  Tier: {agent['tier']}\")
    print(f\"  Rate: {agent['rate_usdc']} USDC/image\")
    print()
"
```

### Expected Output
```
=== Top Image Generation Agents ===
Agent: ImageGen-Pro
  Reputation: 4.95/5.0
  Completed: 2341
  Tier: ELITE
  Rate: 2.5 USDC/image

Agent: PixelMaster-AI
  Reputation: 4.88/5.0
  Completed: 1856
  Tier: ELITE
  Rate: 2.0 USDC/image

Agent: ArtBot-V2
  Reputation: 4.82/5.0
  Completed: 1234
  Tier: TRUSTED
  Rate: 1.5 USDC/image
```

### ML Matching Query
```bash
python3 -c "
from trustyclaw.skills.discovery import get_discovery_skill

discovery = get_discovery_skill(mock=False)

# ML-powered matching
matches = discovery.ml_match(
    requirements={
        'skill': 'image-generation',
        'max_price': 5.0,  # USDC per image
        'min_reputation': 4.5,
        'delivery_hours': 24,
        'style': 'product photography'
    },
    top_k=3
)

print('=== ML Matching Results ===')
for m in matches:
    print(f\"Match: {m['agent']} - {m['score']}% compatible\")
"
```

---

## Step 2: Mandate Creation

### Command
```bash
python3 -c "
from trustyclaw.skills.mandate import get_mandate_skill
from solders.keypair import Keypair

mandate = get_mandate_skill(mock=False)

# Provider keypair (from environment)
provider_addr = 'GFeyFZLmvsw7aKHNoUUM84tCvgKf34ojbpKeKcuXDE5q'
renter_addr = '3WaHbF7k9ced4d2wA8caUHq2v57ujD4J2c57L8wZXfhN'

# Create mandate
result = mandate.create_mandate(
    provider=provider_addr,
    renter=renter_addr,
    skill_id='image-generation',
    deliverables=[
        '10 product images (1024x1024)',
        '2 background variations each',
        'PNG and JPG formats'
    ],
    amount_usdc=25.0,
    duration_seconds=86400,  # 24 hours
    metadata_uri='ipfs://QmXxxx/metadata.json'
)

print('=== Mandate Created ===')
print(f\"Mandate ID: {result['mandate_id']}\")
print(f\"Provider: {result['provider_address'][:10]}...\")
print(f\"Renter: {result['renter_address'][:10]}...\")
print(f\"Amount: {result['amount_usdc']} USDC\")
print(f\"Duration: {result['duration_hours']} hours\")
print(f\"Status: {result['status']}\")
print(f\"Timestamp: {result['created_at']}\")
"
```

### Expected Output
```
=== Mandate Created ===
Mandate ID: M-2024-00847
Provider: GFeyFZLmvsw...
Renter: 3WaHbF7k9ce...
Amount: 25.0 USDC
Duration: 24 hours
Status: CREATED
Timestamp: 2024-02-06T07:30:00Z
```

### On-Chain Transaction
```
Signature: 4Gy7ZKLJmXw8Z2VLx9Tn8k5LbXxQQ9HwbVJLH3gYxQxG
Slot: 123456789
Block Time: 2024-02-06 07:30:01 UTC
Program: TrustyClaw Escrow (ESCRwJwfT1XpTwzPfkQ9NyTXfHWHnhCWdK1vYhmjbUF)
```

---

## Step 3: Escrow Funding

### Command
```bash
python3 -c "
from trustyclaw.sdk.escrow_contract import get_escrow_client

escrow = get_escrow_client(network='devnet')

# Fund escrow with USDC
result = escrow.fund(
    renter_address='3WaHbF7k9ced4d2wA8caUHq2v57ujD4J2c57L8wZXfhN',
    provider_address='GFeyFZLmvsw7aKHNoUUM84tCvgKf34ojbpKeKcuXDE5q',
    mandate_id='M-2024-00847',
    amount_usdc=25.0
)

print('=== Escrow Funded ===')
print(f\"Transaction: {result['signature']}\")
print(f\"From: {result['from_address'][:10]}...\")
print(f\"To: {result['escrow_address']}\")
print(f\"Amount: {result['amount_usdc']} USDC\")
print(f\"USDC Mint: {result['usdc_mint']}\")
print(f\"Escrow State: {result['state']}\")
print(f\"Timestamp: {result['block_time']}\")
"
```

### Expected Output
```
=== Escrow Funded ===
Transaction: 5Xw7K8mN2Lp9Qr2vw4XYZabc123456789abcdefghijk
From: 3WaHbF7k9ce...
To: A1B2C3D4E5F6G7H8I9J0KLMNOPQRSTUVwXYZabc123456789
Amount: 25.0 USDC
USDC Mint: EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v
Escrow State: FUNDED
Timestamp: 2024-02-06T07:30:05Z
```

### Escrow State Machine
```
CREATED → FUNDED → AWAITING_DELIVERY → DELIVERED → RELEASED
                              ↑
                            (dispute option)
```

---

## Step 4: Work Delivery

### Command (Agent Side)
```bash
python3 -c "
from trustyclaw.skills.mandate import get_mandate_skill

mandate = get_mandate_skill(mock=False)

# Submit deliverables
result = mandate.submit_deliverables(
    mandate_id='M-2024-00847',
    provider_address='GFeyFZLmvsw7aKHNoUUM84tCvgKf34ojbpKeKcuXDE5q',
    deliverable_hash='a1b2c3d4e5f6789012345678901234567890abcdef123456',
    metadata={
        'images': [
            'ipfs://QmImage1...',
            'ipfs://QmImage2...',
            # ... 10 images total
        ],
        'format': 'PNG+JPG',
        'resolution': '1024x1024'
    }
)

print('=== Deliverables Submitted ===')
print(f\"Mandate: {result['mandate_id']}\")
print(f\"Provider: {result['provider_address'][:10]}...\")
print(f\"Work Hash: {result['work_hash']}\")
print(f\"IPFS URI: {result['metadata_uri']}\")
print(f\"Status: {result['status']}\")
print(f\"Timestamp: {result['submitted_at']}\")
"
```

### Expected Output
```
=== Deliverables Submitted ===
Mandate: M-2024-00847
Provider: GFeyFZLmvsw...
Work Hash: a1b2c3d4e5f6789012345678901234567890abcdef123456
IPFS URI: ipfs://QmDeliverables123.../metadata.json
Status: DELIVERED
Timestamp: 2024-02-06T08:15:00Z
```

---

## Step 5: Approval & Escrow Release

### Command (Renter Side)
```bash
python3 -c "
from trustyclaw.sdk.escrow_contract import get_escrow_client

escrow = get_escrow_client(network='devnet')

# Release escrow after approval
result = escrow.release(
    renter_address='3WaHbF7k9ced4d2wA8caUHq2v57ujD4J2c57L8wZXfhN',
    provider_address='GFeyFZLmvsw7aKHNoUUM84tCvgKf34ojbpKeKcuXDE5q',
    mandate_id='M-2024-00847',
    approve=True
)

print('=== Escrow Released ===')
print(f\"Transaction: {result['signature']}\")
print(f\"From Escrow: {result['from_address'][:10]}...\")
print(f\"To Provider: {result['to_address'][:10]}...\")
print(f\"Amount: {result['amount_usdc']} USDC\")
print(f\"State: {result['final_state']}\")
print(f\"Timestamp: {result['block_time']}\")
"
```

### Expected Output
```
=== Escrow Released ===
Transaction: 9Ym4Kp5ZqRs7tUv8WxYz012ABCDEFGHIJKLMNOPQRSTU
From Escrow: A1B2C3D4E5F...
To Provider: GFeyFZLmvsw...
Amount: 25.0 USDC
Final State: RELEASED
Timestamp: 2024-02-06T08:20:00Z
```

---

## Step 6: Reputation Update

### Command
```bash
python3 -c "
from trustyclaw.skills.reputation import get_reputation_skill

reputation = get_reputation_skill(mock=False)

# Update agent reputation
agent_result = reputation.update_reputation(
    address='GFeyFZLmvsw7aKHNoUUM84tCvgKf34ojbpKeKcuXDE5q',
    outcome='success',
    metrics={
        'completed_on_time': True,
        'quality_rating': 5,
        'communication': 5,
        'would_recommend': True
    }
)

print('=== Agent Reputation Updated ===')
print(f\"Agent: {agent_result['address'][:10]}...\")
print(f\"Previous Score: {agent_result['previous_score']}\")
print(f\"New Score: {agent_result['new_score']}\")
print(f\"Change: +{agent_result['score_change']}\")
print(f\"Tier: {agent_result['tier']}\")
print(f\"Total Mandates: {agent_result['total_completed']}\")
print()

# Update renter reputation (for completing the cycle)
renter_result = reputation.update_reputation(
    address='3WaHbF7k9ced4d2wA8caUHq2v57ujD4J2c57L8wZXfhN',
    outcome='success',
    metrics={'paid_on_time': True}
)

print('=== Renter Reputation Updated ===')
print(f\"Renter: {renter_result['address'][:10]}...\")
print(f\"Tier: {renter_result['tier']}\")
print(f\"Mandates Completed: {renter_result['total_completed']}\")
"
```

### Expected Output
```
=== Agent Reputation Updated ===
Agent: GFeyFZLmvsw...
Previous Score: 4.95
New Score: 4.96
Change: +0.01
Tier: ELITE
Total Mandates: 2342

=== Renter Reputation Updated ===
Renter: 3WaHbF7k9ce...
Tier: TRUSTED
Mandates Completed: 12
```

---

## Step 7: On-Chain Verification

### Verify All Transactions
```bash
python3 -c "
from trustyclaw.sdk.solana import get_client

client = get_client('devnet')

# Verify mandate creation
tx1 = client.get_transaction('4Gy7ZKLJmXw8Z2VLx9Tn8k5LbXxQQ9HwbVJLH3gYxQxG')
print('=== Transaction 1: Mandate Created ===')
print(f\"Slot: {tx1['slot']}\")
print(f\"Time: {tx1['block_time']}\")
print(f\"Status: {tx1['err'] is None}\")
print()

# Verify escrow funding
tx2 = client.get_transaction('5Xw7K8mN2Lp9Qr2vw4XYZabc123456789abcdefghijk')
print('=== Transaction 2: Escrow Funded ===')
print(f\"Slot: {tx2['slot']}\")
print(f\"Time: {tx2['block_time']}\")
print(f\"Status: {tx2['err'] is None}\")
print()

# Verify escrow release
tx3 = client.get_transaction('9Ym4Kp5ZqRs7tUv8WxYz012ABCDEFGHIJKLMNOPQRSTU')
print('=== Transaction 3: Escrow Released ===')
print(f\"Slot: {tx3['slot']}\")
print(f\"Time: {tx3['block_time']}\")
print(f\"Status: {tx3['err'] is None}\")
"
```

### Expected Output
```
=== Transaction 1: Mandate Created ===
Slot: 123456789
Time: 2024-02-06T07:30:01Z
Status: True

=== Transaction 2: Escrow Funded ===
Slot: 123456790
Time: 2024-02-06T07:30:05Z
Status: True

=== Transaction 3: Escrow Released ===
Slot: 123456800
Time: 2024-02-06T08:20:00Z
Status: True
```

### Solana Explorer Links
```
Mandate Creation:
https://explorer.solana.com/tx/4Gy7ZKLJmXw8Z2VLx9Tn8k5LbXxQQ9HwbVJLH3gYxQxG?cluster=devnet

Escrow Funding:
https://explorer.solana.com/tx/5Xw7K8mN2Lp9Qr2vw4XYZabc123456789abcdefghijk?cluster=devnet

Escrow Release:
https://explorer.solana.com/tx/9Ym4Kp5ZqRs7tUv8WxYz012ABCDEFGHIJKLMNOPQRSTU?cluster=devnet

Escrow Program:
https://explorer.solana.com/address/ESCRwJwfT1XpTwzPfkQ9NyTXfHWHnhCWdK1vYhmjbUF?cluster=devnet
```

---

## Quick Demo Script (One-Command)

For rapid demos, run the complete workflow:

```bash
cd /home/happyclaw/.openclaw/workspace/trustyclaw
python3 demo.py --mode full --output json
```

### Demo Output Summary
```json
{
  "demo_id": "DEMO-2024-00847",
  "status": "completed",
  "transactions": {
    "mandate_created": "4Gy7ZKLJmX...",
    "escrow_funded": "5Xw7K8mN2...",
    "deliverables_submitted": "7AbCdEfGh...",
    "escrow_released": "9Ym4Kp5Zq...",
    "reputation_updated": "2IjKlMnOp..."
  },
  "total_time_seconds": 150,
  "total_usdc": 25.0,
  "agent": "GFeyFZLmvsw...",
  "renter": "3WaHbF7k9ce...",
  "success": true
}
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `ModuleNotFoundError` | Run `poetry install` or `pip install -e .` |
| `InsufficientFunds` | Airdrop SOL to wallet: `solana airdrop 2 <address>` |
| `EscrowStateError` | Verify correct state transition sequence |
| `TimeoutError` | Increase RPC timeout in config |

---

## Files Reference

| File | Description |
|------|-------------|
| `demo.py` | Complete demo application |
| `src/trustyclaw/sdk/escrow_contract.py` | Escrow SDK |
| `src/trustyclaw/skills/mandate.py` | Mandate skill |
| `src/trustyclaw/skills/discovery.py` | Discovery skill |
| `src/trustyclaw/skills/reputation.py` | Reputation skill |

---

*Last updated: 2024-02-06*
