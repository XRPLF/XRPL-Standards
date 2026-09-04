# XLS-64.1 — `fixCleanup3_4_0`

Not yet live on the vault/lending fix amendment. When this spec PR merges, it lands in **this** patch (not a new XLS-64.N per comment). There is no separate `LendingProtocolV1_1` patch for XLS-64.

## Why

Document freeze handling for pseudo-accounts so implementers match `checkDepositFreeze` / `checkWithdrawFreeze`: issuer destination bypass, local vs global freeze, and the depositor issuer exemption.

## What changed

- Withdrawal reject list is ordered; the asset issuer can always receive its own token.
- "Locally frozen" covers individual freeze plus vault pseudo-account freeze for MPT shares where that applies.
- Deposits skip the depositor individual freeze when the depositor is the asset issuer.

## Merge bucket

PRs that fold into XLS-64.1: #568.

The consolidated spec is the top-level `README.md`. Commit SHA for the changelog is recorded when this patch is merged.
