<div align="center">

<img src="https://raw.githubusercontent.com/genlayerlabs/brand-assets/main/logo/genlayer-mark.svg" width="72" alt="GenLayer" onerror="this.style.display='none'" />

# GenLayer Intelligent Contracts

**Consensus-native Python contracts for the GenLayer network.**
Live web evidence, LLM-adjudicated verdicts, independent multi-validator re-derivation — verified on-chain, not asserted.

[![GenVM](https://img.shields.io/badge/runtime-GenVM-6C5CE7?style=flat-square)](https://docs.genlayer.com)
[![Python](https://img.shields.io/badge/language-Python-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org)
[![License: MIT](https://img.shields.io/badge/license-MIT-2ECC71?style=flat-square)](./LICENSE)
[![Network](https://img.shields.io/badge/networks-StudioNet%20%7C%20Bradbury-orange?style=flat-square)](https://studio.genlayer.com)

</div>

---

## What lives here

This repository holds Intelligent Contracts deployed to the GenLayer network — Python programs that run on GenVM, fetch live evidence from the open web, ask an LLM to judge that evidence against a fixed standard, and finalize a verdict only once independent validators agree.

The current, actively maintained contract sits in **[`contracts/updated/`](./contracts/updated/)**. That folder is replaced wholesale each time a new contract goes live — always exactly one file, always the latest. Everything in the top-level `contracts/` folder is retained history from earlier submissions and is not part of the active build.

**Every contract in this repository — past or present — is built against the same non-negotiable rule set below.** That rule set is what this README documents, so that adding a new contract never requires touching this file again.

---

## The rule set every contract here follows

### Consensus is structural, not decorative

A contract only belongs on GenLayer if it judges a **genuinely contested claim** — one where a real, adversarial party benefits from a false verdict. If no one benefits from the LLM being wrong, there's no dispute to arbitrate, and multi-validator consensus is theater bolted onto an ordinary API call. Every contract here can name, in one sentence, who benefits from a false "yes" and who benefits from a false "no."

### Evidence is fetched, never trusted

No contract judges a claim from a party's own description of it. Evidence is retrieved live, inside the same consensus round that produces the verdict, via GenVM's native web-access primitive — and at least one evidence source is fixed and independently authoritative, chosen by neither party to the dispute. A caller-selected page proves only that the page exists; it never substitutes for a standard neither side controls.

### Validators independently re-derive, they don't rubber-stamp

A validator that only checks "the leader returned something" proves nothing — it would pass on any plausible-sounding, adversarially-crafted text. Every write function that produces an LLM judgment has its validator logic independently re-run the leader's own reasoning and compare the *actual result*, not merely confirm a response arrived in the expected shape.

### Reasoning has to touch the evidence, not just describe it

A sufficiently long, fluent explanation is not the same thing as a correct one. Where a contract's validator checks the LLM's stated reasoning, it checks for concrete engagement with what was actually fetched — not a length threshold, not generic confidence in prose.

### Determinism is enforced at the type level

Non-deterministic language-model output crosses into deterministic on-chain state only through integer types. Floating-point values never appear anywhere reachable from a consensus-sensitive code path, including as a transient parsing step. Confidence and scoring values are always fixed-point integers.

### Settlement is a consequence, never a wager

Where a contract moves value, that movement is the deterministic output of a judged, evidence-based verdict — a security-deposit pattern, not a game of chance. No contract here has, or could be repurposed as, an odds-based or speculative payout mechanism.

---

## Architecture

```
Party submits a claim, locking terms that neither party can retroactively edit
                              │
                              ▼
        Contract fetches live evidence (gl.nondet.web.get)
                              │
                              ▼
     Leader validator produces a structured verdict + reasoning
                              │
                              ▼
   Independent validators re-derive the verdict from the same evidence
                    and require it to agree
                              │
                              ▼
        Consensus-finalized verdict triggers on-chain settlement
```

Every contract in `contracts/updated/` implements this shape using GenVM's confirmed-correct primitives:

| Concern | Primitive |
|---|---|
| Non-deterministic judgment | `gl.vm.run_nondet_unsafe(leader_fn, validator_fn)` — called positionally |
| Live evidence | `gl.nondet.web.get(url)` → `Response` object (`.body`, `.status_code`) |
| LLM inference | `gl.nondet.exec_prompt(prompt, response_format="json")` |
| Key-value storage | `TreeMap`, never `DynArray` for lookups |
| Structured records | `@allow_storage @dataclass`, never `gl.Record` |
| Cross-contract value transfer | `.emit_transfer(value=...)`, never `.send(` |
| Storage inside a consensus block | `gl.storage.copy_to_memory(...)` before entering `run_nondet_unsafe` — storage is never read directly inside leader/validator logic |
| View functions | Always return `str` via `json.dumps()` |

Every contract's own module docstring contains its specific concept, its consensus-necessity argument, and its validator design — that explanation travels with the file itself rather than living here, which is exactly why this document doesn't need to change when a new contract is added.

---

## Deploying a contract from this repository

See **[`docs/deployment.md`](./docs/deployment.md)** for the full, contract-agnostic deployment walkthrough — it works identically for anything placed in `contracts/updated/`.

---

## License

Released under the [MIT License](./LICENSE).

---

<div align="center">
<sub>Built on <a href="https://genlayer.com">GenLayer</a> — the intelligence layer of the internet.</sub>
</div>
