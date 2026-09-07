# XLS-66.2 — `fixCleanup3_4_0`

Not yet live. This patch of [XLS-66](../README.md) records the lending changes made by `fixCleanup3_4_0`. The consolidated specification is the top-level [README.md](../README.md).

## Why

`fixCleanup3_4_0` stops early impairment and due-date rewrites on `LoanManage`. That is independent of cash-basis accounting.

## What changed

- Impair only when the payment is already overdue (`tecTOO_SOON` otherwise).
- With the amendment enabled, impair/unimpair do not rewrite `NextPaymentDueDate`.
- Without the amendment, the previous due-date moves remain the fallback.
