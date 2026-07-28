# Deployment Guide

This guide applies to any contract in [`contracts/updated/`](../contracts/updated/). It does not name a specific contract, so it never needs updating when the active contract changes — only the file being deployed changes.

---

## Prerequisites

- A wallet extension (e.g. MetaMask) configured for GenLayer networks
- Testnet GEN from the [GenLayer faucet](https://testnet-faucet.genlayer.foundation)
- The single `.py` file currently in `contracts/updated/`

---

## Step 1 — Verify before deploying

Before uploading anything, confirm the contract satisfies GenVM's structural requirements:

- Line 1 is a pinned `# { "Depends": "py-genlayer:<hash>" }` comment — never `"py-genlayer:test"`, which fails schema load on current Studio.
- Every `run_nondet_unsafe` call is positional: `run_nondet_unsafe(leader_fn, validator_fn)`, never keyword arguments.
- `leader_fn`/`validator_fn` are nested functions declared inside the write method that calls them — never bound instance methods, never referencing `self` in either body.
- Any storage-backed record used inside consensus logic has been copied via `gl.storage.copy_to_memory(...)` **before** the `run_nondet_unsafe` call — never read directly inside `leader_fn`/`validator_fn`.
- No class-body attribute carries a type annotation unless it is genuinely meant to be mutable, per-instance storage. Real constants live at module level.
- No `.send(` on any `get_contract_at(...)` result — value transfers use `.emit_transfer(value=...)`.
- No `float(` anywhere reachable from consensus-sensitive code, even as a transient parsing step.

## Step 2 — Deploy via GenLayer Studio

1. Go to [studio.genlayer.com](https://studio.genlayer.com) and connect your wallet.
2. Select **Run and Debug**, then upload the `.py` file directly — never paste code into an editor field, and never deploy via a raw EVM wallet transaction (both are rejected).
3. Fill in constructor parameters as prompted by Studio, based on the contract's own `__init__` signature.
4. Deploy and wait for the transaction to reach **`FINALIZED` / `SUCCESS`**.
5. Copy the deployed contract address and the deploy transaction hash from Studio.

## Step 3 — Exercise every write path before treating the contract as proven

A clean deploy only proves the constructor ran. Before citing this contract as working evidence anywhere, run each of its public write functions at least once through Studio's Run and Debug panel and confirm:

- `execution_result` shows `SUCCESS`, not `ERROR`, for every call.
- Stderr is empty — no pickling warnings, no unhandled exceptions.
- Any function that transfers value produces a balance change matching the expected settlement math exactly, confirmed on-chain — not merely "no error was thrown."

A contract that deploys cleanly can still fail deep inside a write function the deploy step never touches. Test the full lifecycle, not just the constructor.

## Step 4 — Confirm on the Explorer

View the deployed contract and its transaction history at:
[explorer-studio.genlayer.com](https://explorer-studio.genlayer.com) (StudioNet) or [explorer-bradbury.genlayer.com](https://explorer-bradbury.genlayer.com) (Bradbury)

The contract's address page shows its full transaction history, each call's status, and its GenVM/consensus result — this is the page to link as evidence that the contract both deployed and executed successfully.

## Step 5 — Update this repository

Replace the single file in `contracts/updated/` with the new contract. Nothing else in this repository needs to change — not this guide, not the README, not the license. The new contract's own module docstring carries its concept, its consensus-necessity argument, and its validator design.

---

## Network reference

| | Bradbury (testnet) | StudioNet |
|---|---|---|
| RPC | `https://rpc-bradbury.genlayer.com` | `https://studio.genlayer.com/api` |
| Chain ID | 4221 (`0x107D`) | 61999 (`0xF22F`) |
| Explorer | `explorer-bradbury.genlayer.com` | `explorer-studio.genlayer.com` |

Faucet: [testnet-faucet.genlayer.foundation](https://testnet-faucet.genlayer.foundation)
