
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
