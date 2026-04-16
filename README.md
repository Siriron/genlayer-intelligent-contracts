# GenLayer Intelligent Contracts

A collection of Intelligent Contracts built for the GenLayer testnet,
demonstrating web access, LLM reasoning, and on-chain AI consensus.

## Contracts

### 1. News Sentiment Oracle
Fetches live news about any topic and uses an LLM to determine
overall sentiment (positive/negative/neutral). Result stored on-chain
after validator consensus.

**Deploy params:** `topic` (string, e.g. "artificial intelligence")

### 2. GitHub Reputation Registry
On-chain registry of developer reputation scores. Submit any GitHub
username — the contract fetches the public profile, scores activity
via LLM, and stores the result trustlessly.

**Deploy params:** none (registry is open after deploy)
**Key methods:** `analyze_profile(username)`, `get_profile(username)`

### 3. DAO Proposal Evaluator
Governance contract that stores a DAO constitution and evaluates
proposals against it using AI consensus. Verdicts are trustless —
multiple validators run the same LLM prompt and must agree.

**Deploy params:** `dao_name`, `constitution` (the rules text)
**Key methods:** `submit_proposal(title, description)`, `evaluate_proposal(id)`

## Deployment

All contracts deploy via [GenLayer Studio](https://studio.genlayer.com).
See [docs/deployment.md](docs/deployment.md) for step-by-step instructions.

## Tech

- Language: Python (GenVM)
- Network: GenLayer Testnet (Asimov/Bradbury)
- Features used: `gl.nondet.web.get`, `gl.nondet.exec_prompt`,
  `gl.eq_principle.strict_eq`, on-chain storage, multi-function contracts
# GenLayer Intelligent Contracts — Batch 2

Three Intelligent Contracts built for [GenLayer Studio](https://studio.genlayer.com) and the [GenLayer Foundation Portal](https://portal.genlayer.foundation). Each contract uses GenLayer-native features: live web access (`gl.nondet.web.get`), LLM reasoning (`gl.nondet.exec_prompt`), and the equivalence principle (`gl.eq_principle.strict_eq`) for decentralized consensus on non-deterministic outputs.

-----

## Contracts

### 1. WeatherCropAdvisor

**File:** `contracts/WeatherCropAdvisor.py`

Fetches real-time weather data for a given region and uses an LLM to assess whether current conditions are suitable for growing a specified crop. Returns a suitability rating (`suitable`, `marginal`, `unsuitable`) and a one-sentence farming recommendation.

**Constructor params:** `region: str`, `crop: str`
**Example:** `region = "Dhaka"`, `crop = "rice"`

-----

### 2. JobMarketPulse

**File:** `contracts/JobMarketPulse.py`

Reads a live remote job board and assesses current demand level for a given technical skill. Returns demand classification (`high`, `medium`, `low`) and the top job titles where that skill appears.

**Constructor params:** `skill: str`
**Example:** `skill = "Solidity"`

-----

### 3. CountryRegulatoryTracker

**File:** `contracts/CountryRegulatoryTracker.py`

Queries recent news for a country’s current regulatory stance on a given topic (e.g. AI, crypto, data privacy). Returns a stance classification (`permissive`, `restrictive`, `neutral`, `unclear`) and a one-sentence summary.

**Constructor params:** `country: str`, `topic: str`
**Example:** `country = "United States"`, `topic = "AI regulation"`

-----

## Technical Approach

All three contracts follow the same proven architecture:

- Class-level annotations use only `str` and `bool` — GenVM-safe types
- No `dict`, `int`, or `list` at class level (crashes the schema parser)
- Integer-style state tracked via `bool` flags
- `__init__` handles all mutable state initialization
- `gl.eq_principle.strict_eq` wraps all non-deterministic calls for validator consensus
- Write functions are one-shot: guarded by a `has_*` boolean to prevent double execution
- All view functions return simple primitives

-----

## Repository

**GitHub:** [siriron/genlayer-intelligent-contracts](https://github.com/siriron/genlayer-intelligent-contracts)

See `docs/deployment.md` for full deployment instructions.
