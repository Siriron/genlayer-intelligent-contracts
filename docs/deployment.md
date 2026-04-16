
# Deployment Guide

## Prerequisites
- MetaMask wallet installed
- GenLayer testnet added to MetaMask
- Testnet tokens from GenLayer faucet

## Network Configuration
- Network Name: GenLayer Testnet
- Studio URL: https://studio.genlayer.com

## How to Deploy

1. Go to https://studio.genlayer.com
2. Connect your MetaMask wallet
3. Click "New Contract" and upload the contract .py file
4. Fill in the constructor parameters shown by the Studio
5. Click Deploy and confirm the transaction in MetaMask
6. Wait for status to show FINALIZED + SUCCESS
7. Copy the transaction hash from the explorer

## Constructor Parameters

### NewsSentimentOracle
- `topic` (string) — the news topic to analyze, e.g. "artificial intelligence"

### GitHubReputationRegistry
- No parameters needed — deploy as is

### DAOProposalEvaluator
- `dao_name` (string) — name of your DAO, e.g. "BuildersDAO"
- `constitution` (string) — the rules text, e.g. "We support open source, transparency, and ethical development"

## Explorer
View all transactions at:
https://explorer-studio.genlayer.com
# Deployment Guide — GenLayer Intelligent Contracts Batch 2

## Prerequisites

- Account on [studio.genlayer.com](https://studio.genlayer.com)
- Account on [portal.genlayer.foundation](https://portal.genlayer.foundation)
- GitHub account (username: siriron)

-----

## Step 1: Open GenLayer Studio

Go to [studio.genlayer.com](https://studio.genlayer.com) and sign in.

-----

## Step 2: Deploy WeatherCropAdvisor

1. In the Studio file explorer, create a new file: `WeatherCropAdvisor.py`
1. Paste the full contents of `contracts/WeatherCropAdvisor.py`
1. Click **Deploy**
1. In the constructor fields enter:
- `region`: e.g. `Dhaka`
- `crop`: e.g. `rice`
1. Confirm deployment and wait for the transaction to confirm
1. Call `evaluate()` — this triggers web fetch + LLM analysis
1. Call `get_suitability()` and `get_advice()` to read results
1. Copy the deployed contract address

-----

## Step 3: Deploy JobMarketPulse

1. Create a new file: `JobMarketPulse.py`
1. Paste the full contents of `contracts/JobMarketPulse.py`
1. Click **Deploy**
1. Constructor field:
- `skill`: e.g. `Solidity`
1. Confirm deployment
1. Call `analyze()`
1. Call `get_demand_level()` and `get_top_roles()` to read results
1. Copy the deployed contract address

-----

## Step 4: Deploy CountryRegulatoryTracker

1. Create a new file: `CountryRegulatoryTracker.py`
1. Paste the full contents of `contracts/CountryRegulatoryTracker.py`
1. Click **Deploy**
1. Constructor fields:
- `country`: e.g. `United States`
- `topic`: e.g. `AI regulation`
1. Confirm deployment
1. Call `evaluate()`
1. Call `get_stance()` and `get_summary()` to read results
1. Copy the deployed contract address

-----

## Step 5: Update GitHub Repository

Push all three contract files plus this documentation to your repo:

```
genlayer-intelligent-contracts/
├── contracts/
│   ├── WeatherCropAdvisor.py
│   ├── JobMarketPulse.py
│   └── CountryRegulatoryTracker.py
├── docs/
│   └── deployment.md
└── README.md
```

Commit message suggestion:

```
Add Batch 2: WeatherCropAdvisor, JobMarketPulse, CountryRegulatoryTracker
```

-----

## Step 6: Submit to Portal — Projects & Milestones (3 submissions)

Go to [portal.genlayer.foundation](https://portal.genlayer.foundation) → **Submit** → **Projects & Milestones**

**Submission 1 — WeatherCropAdvisor**

- Title: `WeatherCropAdvisor — Real-time crop suitability using live weather data`
- Description: Intelligent contract that fetches live weather data for any region and uses LLM reasoning to assess crop suitability. Returns structured output (suitable / marginal / unsuitable) plus actionable farming advice.
- Link: Paste deployed contract address or GitHub file link
- Category: Projects & Milestones

**Submission 2 — JobMarketPulse**

- Title: `JobMarketPulse — Live job market demand classifier for technical skills`
- Description: Intelligent contract that reads a live remote job board and classifies current demand for a given skill as high, medium, or low. Returns top job titles that require the skill.
- Link: Paste deployed contract address or GitHub file link
- Category: Projects & Milestones

**Submission 3 — CountryRegulatoryTracker**

- Title: `CountryRegulatoryTracker — Country-level regulatory stance tracker using live news`
- Description: Intelligent contract that queries current news to classify a country’s regulatory stance on any topic as permissive, restrictive, neutral, or unclear. Includes a one-sentence policy summary.
- Link: Paste deployed contract address or GitHub file link
- Category: Projects & Milestones

-----

## Step 7: Submit to Portal — Tools & Infrastructure (1 submission)

**Submission — GitHub Repository**

- Title: `GenLayer Intelligent Contracts Repository — Batch 2`
- Description: GitHub repo containing 3 production-ready Intelligent Contracts with full documentation. Each contract demonstrates real-world use of GenLayer’s web access, LLM inference, and equivalence principle for decentralized consensus.
- Link: `https://github.com/siriron/genlayer-intelligent-contracts`
- Category: Tools & Infrastructure

-----

## Step 8: Submit to Portal — Documentation (2 submissions)

**Submission 1 — README**

- Title: `README — GenLayer Intelligent Contracts Batch 2`
- Description: Repository README covering contract purpose, technical architecture, constructor params, and usage examples for all 3 contracts.
- Link: `https://github.com/siriron/genlayer-intelligent-contracts/blob/main/README.md`
- Category: Documentation

**Submission 2 — Deployment Guide**

- Title: `Deployment Guide — Batch 2 Intelligent Contracts`
- Description: Step-by-step deployment guide for deploying all 3 contracts in GenLayer Studio, verifying execution, and updating the GitHub repo.
- Link: `https://github.com/siriron/genlayer-intelligent-contracts/blob/main/docs/deployment.md`
- Category: Documentation

-----

## Notes

- Check portal.genlayer.foundation for any active bonus missions before submitting — complete those first if they align with this batch.
- Total submissions this batch: 6 (3 Projects, 1 Tools, 2 Documentation)
- Article submission will be done separately after this batch is complete.
