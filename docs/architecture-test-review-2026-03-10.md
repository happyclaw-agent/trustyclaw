# TrustyClaw Architecture + Test Coverage Review

Date: 2026-03-10
Reviewer: Nullius

## Executive summary
TrustyClaw’s highest-risk gaps are dependency/tooling drift and escrow SDK boundary correctness. The immediate path to reduce delivery and security risk is: (1) finish uv-first packaging + CI standardization, (2) split and harden escrow modules with clear interfaces, and (3) enforce reliability/security CI gates with coverage and failure-path tests. These three actions are sequenced to first stabilize the build surface, then reduce core payment-path complexity, then lock quality with automated gates.

## Scope
- Reviewed project structure, packaging metadata, CI workflow, and core SDK modules.
- Attempted local test run with `uv run`.

## Baseline Observations
- Repo currently mixes packaging approaches (`pyproject.toml` with Poetry schema + `requirements.txt` + CI pip install path).
- CI uses `python -m venv` + `pip install -r requirements.txt`; local agent standard is `uv`.
- Test collection currently fails under `uv run --with pytest pytest src/tests/unit -vv` due to missing runtime dependencies (`solana`, `pydantic`) in the uv environment, indicating dependency metadata/tooling drift.
- Core SDK modules show signs of merge debt and correctness risk (duplicate class/function blocks, mixed sync/async semantics, broad `except`, simulation + on-chain responsibilities combined).

## Top 3 Reliability/Security Improvements

### 1) Stabilize build/dependency system around one source of truth (P0)
**Problem**
- `pyproject.toml` is Poetry-style and lacks `project.requires-python`; uv defaults to Python 3.13.
- CI and local runs can diverge because dependencies are declared in more than one place.

**Risk**
- Non-reproducible environments, flaky tests, hidden dependency breakage, and security patch lag.

**Action**
- Migrate to PEP 621 `pyproject.toml` and `uv.lock` as canonical source.
- Add `requires-python` (target likely 3.11/3.12 based on SDK deps).
- Keep `requirements.txt` generated from lock (or remove entirely).
- Update CI to `uv sync --frozen` + `uv run pytest`.

**Success criteria**
- Same lockfile and interpreter constraints used by local + CI.
- Fresh clone passes tests with one documented command path.

---

### 2) Refactor SDK import boundaries + escrow module correctness (P0)
**Problem**
- `src/trustyclaw/sdk/__init__.py` eagerly imports all submodules, forcing heavy optional deps on any import path.
- `escrow_contract.py` contains duplicate class/function definitions and mixed simulation/on-chain logic in one class.
- Potential undefined/fragile runtime references in on-chain paths (e.g., context helpers imported conditionally).

**Risk**
- Import-time failures, inconsistent behavior across environments, and high chance of silent logic bugs in payment flow.

**Action**
- Split `EscrowClient` into clear modules (`escrow_onchain.py`, `escrow_sim.py`) behind a thin facade.
- Remove duplicate method/class definitions and enforce one canonical escrow state model.
- Convert SDK top-level exports to lazy imports or feature-gated optional extras.
- Add strict typed interfaces for escrow operations and explicit error taxonomy.

**Success criteria**
- `import trustyclaw` works without requiring all optional blockchain deps.
- Escrow code has no duplicate definitions and clear sync/async boundaries.

---

### 3) Add security/reliability test gates (coverage + failure-path tests) (P1)
**Problem**
- Existing tests are broad in count but not consistently gated by coverage threshold or mutation-resistant failure scenarios.
- Current workflow does not enforce lint/type/security checks in CI.

**Risk**
- Regression risk in payment/dispute logic and accidental shipping of insecure defaults.

**Action**
- Enable CI gates for:
  - `ruff check`
  - `mypy` on `src/trustyclaw`
  - `pytest --cov=src/trustyclaw --cov-report=term-missing --cov-fail-under=80`
- Add targeted tests for:
  - invalid/missing `ESCROW_PROGRAM_ID`
  - signer/authority mismatch and dispute resolution edge paths
  - network/RPC transient failures and retry semantics
  - serialization/deserialization safety for escrow account data

**Success criteria**
- CI fails fast on lint/type/coverage/security regressions.
- Critical escrow/payment paths covered with deterministic failure-case tests.

## Evidence (commands + result)
```bash
uv run --with pytest pytest src/tests/unit -vv
```
Result: collection interrupted with missing dependencies (`solana`, `pydantic`) under uv-run context; confirms dependency/tooling drift.

## Suggested follow-up tasks (with owners)
1. `P0` — **Owner: Nullius**: Migrate packaging + CI to uv (`pyproject` PEP 621 + lockfile + requires-python).
2. `P0` — **Owner: Nullius**: Refactor escrow SDK boundaries and remove duplicate definitions.
3. `P1` — **Owner: Nullius**: Add CI quality/security gates and failure-path tests for escrow/reputation modules.
