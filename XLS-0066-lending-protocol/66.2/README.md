# XLS-66.2 — `fixCleanup3_4_0`

Not yet live. When lending spec PRs merge, they land in **this** patch or in [XLS-66.1](../66.1/README.md) (`LendingProtocolV1_1`), not as a new XLS-66.N per PR.

## Why

`fixCleanup3_4_0` stops early impairment and due-date rewrites on `LoanManage`. That is independent of cash-basis accounting.

## What changed

- Impair only when the payment is already overdue (`tecTOO_SOON` otherwise).
- With the amendment enabled, impair/unimpair do not rewrite `NextPaymentDueDate`.
- Without the amendment, the previous due-date moves remain the fallback.

## Merge bucket

PRs that fold into XLS-66.2: #496 (impairment).

The consolidated spec is the top-level `README.md`. Commit SHA for the changelog is recorded when this patch is merged.
