# XLS-65.1 — `LendingProtocolV1_1`

Not yet live. When vault spec PRs merge, they land in **this** patch or in [XLS-65.2](../65.2/README.md) (`fixCleanup3_4_0`), not as a new XLS-65.N per PR.

## Why

`LendingProtocolV1_1` changes Vault create/delete and ledger-entry shape. Until the amendment is enabled on mainnet, the top-level README keeps pre-amendment behavior as the default and records the amended behavior in labeled subsections. This folder is the reviewable record of that patch.

## What changed

- New Vaults created while the amendment is enabled get `LEVersion = 1` (cash-basis `AssetsTotal`).
- Optional closed-ended lifecycle: `VaultKind`, `SubscriptionDate`, `RedemptionDate`, with `temMALFORMED` / `tecEXPIRED` checks matching `VaultCreate`.
- Those fields (and `LEVersion`) are immutable once set.
- `VaultDelete` may carry optional `MemoData` only when this amendment is enabled (`temDISABLED` otherwise).

## Merge bucket

PRs that fold into XLS-65.1: #582 (LEVersion), #549 (VaultCreate kind/dates), #470 (`MemoData`), #555 (immutability in §3.1.10).

The consolidated spec is the top-level `README.md`. Commit SHA for the changelog is recorded when this patch is merged.
