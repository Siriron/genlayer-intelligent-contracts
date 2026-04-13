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
