# PR #3: Deploy Real On-Chain Reputation Program

## Summary
Implements a real Solana Anchor program for on-chain reputation storage using PDAs.

## Changes

### 1. Anchor Reputation Program
- **Reputation PDA**: `[REPUTATION_SEED, agent_address]`
- **Review PDA**: `[REVIEW_SEED, review_id]`
- **Instructions**: `initialize_reputation`, `submit_review`, `update_score`, `vote_review`

### 2. Reputation SDK
- Removed all mock fallbacks
- Program ID: `REPUT1111111111111111111111111111111111111`
- CPI calls to Anchor program
- Proper account parsing

### 3. Reputation Skill
- Removed `mock` parameter
- Real on-chain data via SDK
- 30-second TTL cache

### 4. Integration Tests
- Reputation account creation
- Review submission
- Score calculation
- Voting mechanism

## Constraints
- MiniMax model
- Clean, production-quality code
- No mocks in production code
