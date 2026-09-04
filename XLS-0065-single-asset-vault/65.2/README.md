<pre>
  xls: 65.2
  title: Vault Loss and Cap Invariants
  description: Allows one unit of rounding slack in the unrealised loss invariant and restricts cap enforcement to transactions that change the cap
  author: Vytautas Vito Tumas <vtumas@ripple.com>, Aanchal Malhotra <amalhotra@ripple.com>
  proposal-from: https://github.com/XRPLF/XRPL-Standards/discussions/192
  status: Draft
  category: Amendment
  requires: [XLS-65](../README.md)
  created: 2026-09-04
  updated: 2026-09-04
</pre>

# Vault Loss and Cap Invariants

## 1. Abstract

This patch of [XLS-65](../README.md) records the changes the `fixCleanup3_4_0` amendment makes to the invariants of the `Vault` ledger entry. `LossUnrealized` may exceed the unavailable assets of the Vault by at most one unit at the scale of the Vault asset, and must not be negative. The cap invariant no longer requires `AssetsTotal <= AssetsMaximum` at all times; it is enforced against the transaction that sets the cap.

The consolidated specification is the top-level [README.md](../README.md).

## 2. Motivation

Both changes come from the same source: the invariants as written are stricter than the arithmetic of the Vault can honour.

`LossUnrealized` is derived from loan balances that are rounded at the scale of the Vault asset. Comparing it to `AssetsTotal - AssetsAvailable` with a strict inequality fails when the two sides round in opposite directions, which is a rounding artefact and not a solvency problem. The invariant needs a tolerance of exactly one unit at that scale, and needs to say that the value is non-negative, which the original inequality does not.

The cap invariant fails for a legitimate state. `AssetsTotal` grows with interest, and interest is not a deposit, so a Vault whose depositors have stayed inside `AssetsMaximum` can still exceed it. Enforcing the cap continuously would make an interest payment fail. What the cap is for is bounding new deposits and preventing an Owner from lowering the cap below the current total.

## 3. Specification

### 3.1 Ledger Entry: `Vault`

#### 3.1.1 Fields

No fields are added or removed by this patch.

#### 3.1.2 Invariants

The unrealised loss invariant becomes, at the scale of `Vault.Asset`:

- `Vault.LossUnrealized <= (Vault.AssetsTotal - Vault.AssetsAvailable) + 1 unit`
- `Vault.LossUnrealized >= 0`

The single unit of slack is a tolerance for rounding at the asset scale, not spare capacity: an implementation must not rely on it to absorb an accounting error.

The cap invariant becomes:

- `Vault.AssetsTotal` is not required to be less than or equal to `Vault.AssetsMaximum` at all times, because the excess may be interest that the Vault has recognised.
- A transaction that sets `Vault.AssetsMaximum` to a non-zero value below `Vault.AssetsTotal` fails.

Before the amendment, the loss inequality is strict and admits no slack, and the cap is required to hold on every modification of the entry.

#### 3.1.3 Example JSON

```json
{
  "LedgerEntryType": "Vault",
  "Asset": { "currency": "USD", "issuer": "rf1BiGeXwwQoi8Z2ueFYTEXSwuJYfV2Jpn" },
  "AssetsTotal": "1010",
  "AssetsAvailable": "10",
  "AssetsMaximum": "1000",
  "LossUnrealized": "1000"
}
```

## 4. Rationale

The tolerance is one unit at the scale of the Vault asset rather than a relative epsilon. A relative tolerance would grow with the size of the Vault and would eventually be large enough to hide a real discrepancy, whereas one unit at the asset scale is the smallest representable difference and cannot hide anything.

For the cap, the alternative was to exclude recognised interest from `AssetsTotal` so that the original invariant could stand. That was rejected because `AssetsTotal` is the basis of the share exchange rate; excluding interest from it would understate the value of a share.

Enforcing the cap on the transaction that changes it, rather than on every modification of the entry, puts the failure where the submitter can act on it.

## 5. Security Considerations

Relaxing an invariant weakens a check that exists to catch implementation errors. Both relaxations are bounded so that they cannot mask a loss: the loss tolerance is one unit at the asset scale, and the cap remains enforced against the transaction that sets it.

Adding `LossUnrealized >= 0` closes a gap in the original invariant. A negative unrealised loss would otherwise pass the inequality and inflate the assets of the Vault relative to its shares.
