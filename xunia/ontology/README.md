# XUNIA XRPL Standards Ontology

Command: **`/glass xrpl standards`**

This directory adds a machine-readable XUNIA integration layer around the XRPL Standards repository. It does not change the meaning, lifecycle status, ownership, or authority of any XLS document.

## Authority boundary

- `XRPLF/XRPL-Standards` remains the authoritative upstream.
- Status and category must be read from each standard's own preamble.
- A XUNIA graph entry does not promote an Idea, Proposal, or Draft to Final.
- XUNIA integration does not imply XRPLF or Ripple sponsorship, endorsement, partnership, or ownership.

## Ontology

```text
STANDARD
  -> CATEGORY
  -> STATUS
  -> PROTOCOL FEATURE
  -> TRANSACTION / LEDGER OBJECT / RPC
  -> TOKEN MODEL / WALLET CAPABILITY
  -> CLIENT OR NODE IMPLEMENTATION
  -> TEST EVIDENCE
  -> GOVERNANCE DECISION
```

The ontology supports three executable pathway descriptions:

1. Standards to validated-ledger reads.
2. Standards to governed wallet transactions.
3. Issued-token and trust-line lifecycle operations.

Mutation pathways require explicit human approval and an external wallet signer. Wallet seeds, private keys, automatic fund movement, and automatic token issuance are prohibited by the contract.

## Files

- [`catalog.json`](catalog.json): ontology objects, links, repositories, pathways, and controls.
- [`schema.json`](schema.json): JSON Schema for the machine contract.
- [`../../scripts/validate-xunia-ontology.cjs`](../../scripts/validate-xunia-ontology.cjs): dependency-free invariant validator.

## Validate

```bash
node scripts/validate-xunia-ontology.cjs
```

This layer can be consumed by `sonoxo/xuniadao` through `/glass xrpl pathways` and used to connect standards evidence to `sonoxo/xrpl.jsXUNIA` and `sonoxo/rippledXUNIA`.
