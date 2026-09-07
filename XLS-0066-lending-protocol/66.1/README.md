# XLS-66.1 — `LendingProtocolV1_1`

Not yet live. This patch of [XLS-66](../README.md) records the lending changes made by `LendingProtocolV1_1`. The consolidated specification is the top-level [README.md](../README.md).

## Why

`LendingProtocolV1_1` changes LoanBroker attachment and principal-only vault/broker totals. Pre-amendment text stays the production default until the amendment is live.

## What changed

- For `LEVersion = 1` Vaults, `Vault.AssetsTotal` and `LoanBroker.DebtTotal` track principal only.
- Creating a LoanBroker while the amendment is enabled requires a closed-ended Vault (`tecNO_PERMISSION` otherwise).
- First-Loss Capital still uses `CoverRateLiquidation` (two-rate formula).
