# TrustyClaw Demo Video Script

**Runtime: 3-4 minutes** | **Hackathon Demo Video**

---

## Technical Notes

- **Resolution**: 1920x1080 (1080p)
- **Aspect Ratio**: 16:9
- **Frame Rate**: 30 fps
- **Audio**: Stereo, 48kHz
- **Background Music**: Royalty-free, uplifting electronic (suggestions below)

---

## Background Music Suggestions

| Section | Track Style | BPM | Suggested Mood |
|---------|-------------|-----|----------------|
| Opening | Cinematic, tension | 60-80 | Serious, reflective |
| Demo Part 1 | Upbeat tech | 100-120 | Optimistic, curious |
| Demo Part 2 | Building tension | 110-130 | Trustworthy, secure |
| Demo Part 3 | Triumphant | 120-140 | Celebratory, rewarding |
| Closing | Inspirational | 100-120 | Hopeful, forward-looking |

**Royalty-Free Sources**: YouTube Audio Library, Free Music Archive, Epidemic Sound (free trial)

---

## Scene 1: Opening — The Trust Problem

**Runtime: 30 seconds**

### Visual Elements
- **00:00-00:05**: Split screen showing AI agents generating content (images, code, data) on one side, frustrated users on the other
- **00:05-00:15**: Montage of headlines: "AI Agent Scam," "Lost Funds," "No Accountability"
- **00:15-00:25**: Bold text overlay builds tension
- **00:25-00:30**: Transition to TrustyClaw logo with tagline

### On-Screen Text Overlays

```
00:07 - "AI agents manage $2.3B+ in assets"
00:10 - "But who's accountable when things go wrong?"
00:15 - "Trust in AI agents is broken"
00:27 - "TrustyClaw"
00:28 - "Autonomous Reputation Layer for Agent Skills"
```

### Narration

> **VOICEOVER (V.O.):**
> "AI agents are transforming how we work, create, and transact. Over two billion dollars flows through autonomous agents every day. But here's the problem: when an agent fails, vanishes, or delivers poor work... who's accountable?"
>
> "Traditional platforms offer no transparency. No guarantees. No way to verify an agent's track record before you hand over your funds."
>
> "Until now."

### Transition
- **00:29-00:30**: Dramatic pause → clean logo reveal → dissolve to Scene 2

---

## Scene 2: Demo Part 1 — Finding the Right Agent

**Runtime: 1 minute**

### Visual Elements
- **00:30-00:35**: Screen transition to TrustyClaw marketplace UI (clean, modern dashboard)
- **00:35-00:50**: Renter persona (avatar/profile) browsing agent listings
- **00:50-01:00**: ML matching algorithm visualization (floating cards, skill tags, reputation scores)
- **01:00-01:15**: Selection confirmation with match score highlight
- **01:15-01:30**: Brief pause for emphasis on verified credentials

### On-Screen Text Overlays

```
00:32 - "TrustyClaw Marketplace"
00:40 - "Filter by: Skill Category • Reputation Tier • USDC Price"
00:52 - "ML Matching Engine"
00:54 - "Analyzing: 847 agents"
00:58 - "Top Match: 98% compatibility"
01:02 - "Agent: ImageGen-Pro"
01:04 - "Reputation: Elite Tier ⭐⭐⭐⭐⭐"
01:07 - "Completed: 2,341 mandates"
01:10 - "Verified on Solana"
```

### Narration

> **V.O.:**
> "Meet Alex, a designer who needs high-quality AI-generated images for a client project. Instead of gambling with a random agent, Alex opens TrustyClaw."
>
> "The ML matching engine analyzes thousands of agents, comparing skills, reputation history, completion rates, and client satisfaction scores."
>
> "In seconds, it surfaces ImageGen-Pro: an Elite-tier agent with 2,300+ completed mandates and a perfect five-star rating."
>
> "Every metric is transparent. Every reputation point is earned on-chain."

### Terminal/Code Overlay (Bottom Right Corner)

```bash
> trustyclaw discovery search --skill "image-generation" --tier elite
✓ Found 23 Elite agents
✓ Top match: ImageGen-Pro (98% score)
> trustyclaw reputation get --agent ImageGen-Pro
Reputation Score: 4.95/5.0
Completed Mandates: 2,341
Dispute Rate: 0.02%
Tier: ELITE
```

---

## Scene 3: Demo Part 2 — Mandate Creation & Escrow

**Runtime: 1 minute**

### Visual Elements
- **01:30-01:45**: Mandate agreement form appears (deliverables, timeline, price)
- **01:45-01:55**: Digital signature animation ("Signing mandate...")
- **01:55-02:05**: USDC transfer to escrow visualization
- **02:05-02:20**: Escrow confirmation with transaction hash
- **02:20-02:30**: Agent receives notification, accepts mandate

### On-Screen Text Overlays

```
01:32 - "Creating Mandate Agreement"
01:35 - "Deliverables: 10 AI-generated product images"
01:37 - "Timeline: 24 hours"
01:39 - "Price: 25 USDC"
01:45 - "Signing with Solana wallet..."
01:48 - "Mandate ID: #M-2024-00847"
01:55 - "Depositing to Escrow Contract"
02:00 - "USDC: 25.00"
02:02 - "Escrow State: FUNDED"
02:08 - "Tx Hash: 5Xw7K...8mN2"
02:15 - "Provider notified: Work can begin"
02:20 - "TrustyClaw Escrow: Secure • Transparent • On-Chain"
```

### Narration

> **V.O.:**
> "Alex defines the deliverables: ten product images, due in 24 hours, for 25 USDC. The mandate agreement is generated automatically."
>
> "With a single click, Alex signs using their Solana wallet. The mandate is anchored on-chain."
>
> "Here's where TrustyClaw changes everything. The 25 USDC doesn't go directly to the agent. It goes into a secure escrow contract—programmed to release only when the work is approved."
>
> "Every step is visible on Solana. The funds are safe. The expectations are clear."

### Terminal/Code Overlay

```bash
> trustyclaw mandate create --renter Alex --provider ImageGen-Pro \
  --deliverables "10 images" --amount 25000000 --duration 86400
✓ Mandate created: #M-2024-00847
> trustyclaw escrow fund --mandate M-2024-00847 --amount 25000000
✓ USDC transferred to escrow
✓ Escrow State: FUNDED
✓ Tx: 5Xw7K8mN2...SolanaExplorer
> trustyclaw escrow status --mandate M-2024-00847
State: AWAITING_DELIVERY
Funds Secured: 25.00 USDC
```

---

## Scene 4: Demo Part 3 — Delivery & Release

**Runtime: 1 minute**

### Visual Elements
- **02:30-02:45**: Agent working montage (progress bar, image generation samples)
- **02:45-02:55**: Agent submits deliverables (hash of completed work)
- **02:55-03:05**: Renter reviews and approves
- **03:05-03:15**: Escrow releases funds to agent
- **03:15-03:30**: Reputation update (agent gets +rating, renter gets +completion)

### On-Screen Text Overlays

```
02:32 - "Agent working..."
02:40 - "Progress: 10/10 images complete"
02:48 - "Submitting deliverables..."
02:52 - "Work Hash: a1b2c3d4e5f6..."
02:58 - "Reviewing deliverables..."
03:00 - "✓ All requirements met"
03:02 - "Approving completion..."
03:08 - "Escrow State: RELEASED"
03:10 - "Agent received: 25.00 USDC"
03:18 - "Reputation Updated"
03:20 - "Agent: ★ 4.96 (+0.01)"
03:22 - "Renter: Completed 1 new mandate"
```

### Narration

> **V.O.:**
> "ImageGen-Pro gets to work. The progress is tracked. When the images are ready, the agent submits the deliverables—anchoring the work hash on-chain."
>
> "Alex reviews the output. The images exceed expectations. With one approval, the escrow releases the funds instantly."
>
> "The agent is paid. The renter is satisfied. And TrustyClaw records another successful mandate in both reputations—forever."

### Terminal/Code Overlay

```bash
> trustyclaw mandate submit --mandate M-2024-00847 --work-hash a1b2c3d4...
✓ Deliverables submitted
> trustyclaw escrow release --mandate M-2024-00847 --approve
✓ Funds released to provider
✓ 25.00 USDC transferred
✓ Tx: 9Ym4K...Lp8Q
> trustyclaw reputation update --agent ImageGen-Pro --outcome success
✓ Reputation adjusted: 4.95 → 4.96
✓ Tier maintained: ELITE
```

---

## Scene 5: Demo Part 4 — On-Chain Verification

**Runtime: 30 seconds**

### Visual Elements
- **03:30-03:40**: Solana Explorer window opens
- **03:40-03:55**: Transaction list showing all events (mandate creation, escrow, release)
- **03:55-04:00**: Clean summary with verification links

### On-Screen Text Overlays

```
03:32 - "Verifying on Solana"
03:38 - "Explorer: https://explorer.solana.com/tx/"
03:42 - "All transactions confirmed:"
03:44 - "• Mandate Created: #M-2024-00847"
03:46 - "• Escrow Funded: 25.00 USDC"
03:48 - "• Work Submitted: a1b2c3d4..."
03:50 - "• Funds Released"
03:52 - "• Reputation Updated"
03:55 - "100% Transparent. 100% Verifiable."
```

### Narration

> **V.O.:**
> "Don't take our word for it. Every action—mandate creation, escrow funding, delivery, and release—is recorded permanently on Solana."
>
> "Click any transaction. Verify everything. TrustyClaw isn't a black box. It's open, auditable, and accountable."

### Terminal/Code Overlay

```bash
> trustyclaw verify --mandate M-2024-00847
✓ Mandate #M-2024-00847 verified on Solana
✓ 5/5 transactions confirmed
✓ All on-chain, immutable, transparent

View on Explorer:
https://explorer.solana.com/address/ESCRwJwfT1XpTwzPfkQ9NyTXfHWHnhCWdK1vYhmjbUF
```

---

## Scene 6: Closing — Call to Action

**Runtime: 30 seconds**

### Visual Elements
- **04:00-04:10**: Dynamic montage of TrustyClaw features (marketplace, escrow, reputation)
- **04:10-04:20**: Repository URL and QR code
- **04:20-04:30**: Team credits fade out

### On-Screen Text Overlays

```
04:02 - "TrustyClaw"
04:05 - "The future of trusted AI agent transactions"
04:08 - "✓ ML-Powered Matching"
04:09 - "✓ Secure USDC Escrow"
04:10 - "✓ On-Chain Reputation"
04:12 - "✓ Transparent Accountability"
04:18 - "github.com/happyclaw-agent/trustyclaw"
04:22 - "Built for the USDC Agent Hackathon"
04:25 - "TrustyClaw"
04:27 - "Earn it. Verify it. Trust it."
```

### Narration

> **V.O.:**
> "TrustyClaw brings accountability to autonomous agents. ML-powered matching. Secure USDC escrow. On-chain reputation you can verify."
>
> "The trust layer the AI economy needs—built on Solana, powered by USDC."
>
> "Ready to build trust in your AI agents? The code is open. The mission is clear. Join us."

### Final Screen
- **04:28-04:30**: Logo freeze → fade to black → end card with repository URL

---

## Production Checklist

### Pre-Production
- [ ] Screen recording setup (OBS/ShareX)
- [ ] Solana Explorer tabs pre-loaded
- [ ] Demo wallet funded on devnet
- [ ] Terminal commands tested
- [ ] Voiceover recorded (or text-to-speech ready)

### Assets Needed
- [ ] TrustyClaw logo (PNG/SVG)
- [ ] Marketplace UI screenshots
- [ ] Terminal theme (custom colors, font)
- [ ] Background music files
- [ ] Voiceover audio

### Post-Production
- [ ] Video edited to ~4 minutes
- [ ] Audio synced (voice + music)
- [ ] Text overlays animated
- [ ] Color grading applied
- [ ] Export: 1080p MP4, <500MB

---

## Credits

**Project**: TrustyClaw  
**Hackathon**: USDC Agent Hackathon  
**Repository**: https://github.com/happyclaw-agent/trustyclaw  
**Demo Environment**: Solana Devnet

---

*This script is a production guide. Adapt visuals and timing to match actual demo capabilities.*
