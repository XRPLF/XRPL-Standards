# XLS-65.2 — `fixCleanup3_4_0`

Not yet live. When vault spec PRs merge, they land in **this** patch or in [XLS-65.1](../65.1/README.md) (`LendingProtocolV1_1`), not as a new XLS-65.N per PR.

## Why

`fixCleanup3_4_0` tightens VaultClawback and vault ledger invariants without waiting on `LendingProtocolV1_1`.

## What changed

- `VaultClawback`: reject a pseudo-account `Holder` (`tecPSEUDO_ACCOUNT`); keep ambiguous Amount and wrong-asset failures; distinguish zero-share vs dust `tecPRECISION_LOSS`; overflow → `tecPATH_DRY`.
- Invariants: `LossUnrealized` may be one asset-scale ULP over unavailable assets; `LossUnrealized >= 0`; `AssetsTotal` may exceed `AssetsMaximum` when the excess is interest, except VaultSet changing the cap.
- Wording-only VaultSet DomainID-zero clarification (#448) also folds here so it does not get its own patch number.

## Merge bucket

PRs that fold into XLS-65.2: #554 (VaultClawback), #555 (invariants), #448 (DomainID zero).

The consolidated spec is the top-level `README.md`. Commit SHA for the changelog is recorded when this patch is merged.
