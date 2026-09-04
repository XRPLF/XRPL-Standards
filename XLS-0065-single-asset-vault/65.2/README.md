<pre>
  xls: 65.2
  title: Single Asset Vault under fixCleanup3_4_0
  description: Records the changes the fixCleanup3_4_0 amendment makes to XLS-65
  author: Vytautas Vito Tumas <vtumas@ripple.com>, Aanchal Malhotra <amalhotra@ripple.com>
  proposal-from: https://github.com/XRPLF/XRPL-Standards/discussions/192
  status: Draft
  category: Amendment
  requires: [XLS-65](../README.md)
  created: 2026-09-04
  updated: 2026-09-04
</pre>

# Single Asset Vault under `fixCleanup3_4_0`

## 1. Abstract

This patch of [XLS-65](../README.md) records the changes the `fixCleanup3_4_0` amendment makes to the Single Asset Vault. The amendment is not yet live. The consolidated specification is the top-level [README.md](../README.md).

The amendment makes the following changes to XLS-65:

- **Vault Loss and Cap Invariants** — When the Vault asset is not integral — that is, an `IOU` — `LossUnrealized` may exceed the unavailable assets of the Vault by at most one unit at the scale of `AssetsTotal`; for `XRP` and `MPT` the comparison stays strict. `LossUnrealized` must also not be negative, for every asset type. Separately, `VaultSet` no longer fails the cap check when the cap is left alone, so a Vault whose total has grown past its cap through interest can still be updated.

## 2. Motivation

**Vault Loss and Cap Invariants.** Both changes come from the same source: the invariants as written are stricter than the arithmetic of the Vault can honour.

`LossUnrealized`, `AssetsTotal` and `AssetsAvailable` are each quantised independently when the Vault asset is an `IOU`, because they are written through `STAmount` and land on a decimal grid whose step depends on the magnitude of the value. Comparing `LossUnrealized` to `AssetsTotal - AssetsAvailable` with a strict inequality fails when the three values round in opposite directions, which is a quantisation artefact and not a solvency problem. The invariant needs a tolerance of exactly one unit at the coarsest of those grids, which is the one `AssetsTotal` sits on.

`XRP` and `MPT` are integral: a drop and a single MPT unit are the smallest representable quantities and there is no sub-unit rounding to absorb. Granting a unit of tolerance there would not paper over a rounding artefact, it would hide a whole drop or a whole MPT of real discrepancy, so the comparison must stay strict for those assets.

The original inequality also says nothing about the sign of `LossUnrealized`. A negative value passes it trivially, so the non-negativity check is added separately, and unlike the tolerance it applies to every asset type.

The cap check fails for a legitimate state. `AssetsTotal` grows with interest, and interest is not a deposit, so a Vault whose depositors have stayed inside `AssetsMaximum` can still exceed it. A `VaultSet` submitted after that point — to change `Data`, say — would fail on a cap the transaction never touched. What the cap is for is bounding new deposits and preventing an Owner from lowering the cap below the current total.

## 3. Specification

### 3.1 Vault Loss and Cap Invariants

#### 3.1.1 Ledger Entry: `Vault`

##### 3.1.1.1 Fields

No fields are added or removed by this patch.

##### 3.1.1.2 Invariants

The unrealised loss invariant becomes:

- If `Vault.Asset` is not integral, i.e. an `IOU`: `Vault.LossUnrealized <= (Vault.AssetsTotal - Vault.AssetsAvailable) + 1 unit`, where the unit is one step of the grid on which `Vault.AssetsTotal` is quantised.
- If `Vault.Asset` is integral, i.e. `XRP` or an `MPT`: `Vault.LossUnrealized <= (Vault.AssetsTotal - Vault.AssetsAvailable)`, unchanged.
- For every asset type: `Vault.LossUnrealized >= 0`.

The single unit of slack is a tolerance for quantisation at the asset scale, not spare capacity: an implementation must not rely on it to absorb an accounting error.

Cap enforcement becomes:

- `Vault.AssetsTotal` is not required to be less than or equal to `Vault.AssetsMaximum` on every modification of the entry, and no invariant imposes that, because the excess may be interest that the Vault has recognised.
- `VaultDeposit` fails when `Vault.AssetsMaximum` is non-zero and the post-deposit `Vault.AssetsTotal` exceeds it. The amendment does not change this.
- `VaultSet` fails when `Vault.AssetsMaximum` is non-zero, `Vault.AssetsTotal` exceeds it, and the transaction either supplies `AssetsMaximum` or otherwise changes the cap. A `VaultSet` that leaves the cap alone is no longer failed by this check.

Before the amendment, the loss inequality is strict for every asset type and admits no slack, `LossUnrealized` is not checked for sign, and the cap is required to hold on every `VaultSet` regardless of whether the transaction touches the cap.

##### 3.1.1.3 Example JSON

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

**Vault Loss and Cap Invariants.** The tolerance is one unit at the scale of the Vault asset rather than a relative epsilon. A relative tolerance would grow with the size of the Vault and would eventually be large enough to hide a real discrepancy, whereas one unit at the asset scale is the smallest representable difference and cannot hide anything.

Restricting the tolerance to non-integral assets, rather than granting it uniformly, was deliberate. The alternative of keying the tolerance off the sign of the scale would have been wrong: an `IOU` amount at or above `1e15` has a non-negative exponent yet still quantises, so it needs the tolerance, while a drop of `XRP` has scale zero and must not get it. Integrality of the asset is the property that actually distinguishes the two cases.

For the cap, the alternative was to exclude recognised interest from `AssetsTotal` so that the original invariant could stand. That was rejected because `AssetsTotal` is the basis of the share exchange rate; excluding interest from it would understate the value of a share.

Enforcing the cap on the `VaultSet` that changes it, rather than on every `VaultSet`, puts the failure where the submitter can act on it. The `VaultDeposit` check is left alone because a deposit is exactly the event the cap exists to bound.

## 5. Security Considerations

**Vault Loss and Cap Invariants.** Relaxing an invariant weakens a check that exists to catch implementation errors. Both relaxations are bounded so that they cannot mask a loss: the loss tolerance is one unit at the asset scale and applies only to assets that quantise, and the cap remains enforced on every `VaultDeposit` and on any `VaultSet` that changes it.

Adding `LossUnrealized >= 0` closes a gap in the original invariant. A negative unrealised loss would otherwise pass the inequality and inflate the assets of the Vault relative to its shares.
