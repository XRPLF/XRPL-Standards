# XLS-66.1 — `LendingProtocolV1_1`

Not yet live. When lending spec PRs merge, they land in **this** patch or in [XLS-66.2](../66.2/README.md) (`fixCleanup3_4_0`), not as a new XLS-66.N per PR.

## Why

`LendingProtocolV1_1` changes LoanBroker attachment and principal-only vault/broker totals. Pre-amendment text stays the production default until the amendment is live.

## What changed

- For `LEVersion = 1` Vaults, `Vault.AssetsTotal` and `LoanBroker.DebtTotal` track principal only.
- Creating a LoanBroker while the amendment is enabled requires a closed-ended Vault (`tecNO_PERMISSION` otherwise).
- First-Loss Capital still uses `CoverRateLiquidation` (two-rate formula). Field removal does not ship under this patch (#494 alignment).
- Optional `VaultID` on `LoanBrokerSet` modify (#497) is intended to merge here if it ships; amendment vs `tem`/`tec` is still open.

## Merge bucket

PRs that fold into XLS-66.1: #582 (cash-basis + closed-ended broker), #494 (keep CoverRateLiquidation), #497 (optional VaultID, pending design).

The consolidated spec is the top-level `README.md`. Commit SHA for the changelog is recorded when this patch is merged.
