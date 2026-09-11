<pre>
  xls: 65.2
  title: Vault Accounting and Cap Invariants
  description: Admits one unit of rounding slack for IOU accounting invariants, requires LossUnrealized to be non-negative, and narrows VaultSet cap enforcement
  author: Vytautas Vito Tumas <vtumas@ripple.com>
  proposal-from: https://github.com/XRPLF/XRPL-Standards/discussions/192
  status: Draft
  category: Amendment
  created: 2026-09-04
  updated: 2026-09-11
</pre>

# Vault Accounting and Cap Invariants

## 1. Abstract

Under the `fixCleanup3_4_0` amendment, when the Vault asset is not integral — that is, an `IOU` — the `LossUnrealized` bound and the accounting-delta comparisons made by `VaultDeposit`, `VaultWithdraw` and `VaultClawback` admit one unit of rounding tolerance at their comparison scale; for `XRP` and `MPT` the comparisons stay strict. `LossUnrealized` must also not be negative, for every asset type, and a fully impaired fixed-share withdrawal may redeem shares for zero assets. Separately, `VaultSet` no longer fails the cap check when the transaction omits `AssetsMaximum` and does not otherwise change the cap, so a Vault whose total has grown past its cap through interest can still be updated.

## 2. Motivation

These changes come from the same source: the invariants as written are stricter than the arithmetic of the Vault can honour.

`LossUnrealized`, `AssetsTotal` and `AssetsAvailable` are each quantised independently when the Vault asset is an `IOU`, because they are written through `STAmount` and land on a decimal grid whose step depends on the magnitude of the value. Comparing `LossUnrealized` to `AssetsTotal - AssetsAvailable` with a strict inequality fails when the three values round in opposite directions, which is a quantisation artefact and not a solvency problem. The invariant needs a tolerance of exactly one unit at the coarsest of those grids, which is the one `AssetsTotal` sits on.

The same quantisation can leave the vault's asset balance delta one unit away from the corresponding change in `AssetsTotal` or `AssetsAvailable`, or from the depositor's or destination's balance delta. Those comparisons need the same bounded tolerance.

`XRP` and `MPT` are integral: a drop and a single MPT unit are the smallest representable quantities and there is no sub-unit rounding to absorb. Granting a unit of tolerance there would not paper over a rounding artefact, it would hide a whole drop or a whole MPT of real discrepancy, so the comparison must stay strict for those assets.

The original inequality also says nothing about the sign of `LossUnrealized`. A negative value passes it trivially, so the non-negativity check is added separately, and unlike the tolerance it applies to every asset type.

The cap check fails for a legitimate state. `AssetsTotal` grows with interest, and interest is not a deposit, so a Vault whose depositors have stayed inside `AssetsMaximum` can still exceed it. A `VaultSet` submitted after that point — to change `Data`, say — would fail on a cap the transaction never touched. What the cap is for is bounding new deposits and preventing an Owner from lowering the cap below the current total.

## 3. Specification

### 3.1 Ledger Entry: `Vault`

#### 3.1.1 Fields

No fields are added or removed.

#### 3.1.2 Invariants

##### 3.1.2.1 `LossUnrealized`

The unrealised loss invariant becomes:

- If `Vault.Asset` is not integral, i.e. an `IOU`: `Vault.LossUnrealized <= (Vault.AssetsTotal - Vault.AssetsAvailable) + 1 unit`, where the unit is one step of the grid on which `Vault.AssetsTotal` is quantised.
- If `Vault.Asset` is integral, i.e. `XRP` or an `MPT`: `Vault.LossUnrealized <= (Vault.AssetsTotal - Vault.AssetsAvailable)`, unchanged.
- For every asset type: `Vault.LossUnrealized >= 0`.

The single unit of slack is a tolerance for quantisation at the asset scale, not spare capacity: an implementation must not rely on it to absorb an accounting error.

##### 3.1.2.2 Accounting-delta checks

The accounting-delta invariants become:

- For an `IOU`, comparisons between the vault asset balance delta and the corresponding depositor or destination balance delta, and between the vault asset balance delta and the changes in `Vault.AssetsTotal` and `Vault.AssetsAvailable`, admit an absolute difference of at most one unit. The unit is one step of the STAmount grid at exponent `scale`, i.e. `10^scale` in Number space (`agreesWithinOneUnit` in `src/libxrpl/tx/invariants/VaultInvariant.cpp`). `scale` is the exponent already passed into that helper for each comparison, not a separately chosen tolerance:
  - Versus Δ`AssetsTotal` or Δ`AssetsAvailable`: `scale` is the STAmount exponent of the posterior `Vault.AssetsTotal` (`computeVaultMinScale` once `fixCleanup3_2_0` is enabled).
  - Versus a depositor or destination asset delta: `scale` is the coarser of that posterior `AssetsTotal` exponent and the coarser of the party's before and after STAmount exponents (`std::max(computeVaultMinScale, computeCoarsestScale(partyDelta))`).
- For `XRP` and `MPT`, those comparisons remain exact (`Asset::integral()`).

For `VaultWithdraw`, the existing `SingleAssetVault` exception that an unrepresentable sub-ULP IOU remainder may remain between vault outflow and destination inflow is an alternative to this one-unit bound, not an addition to it: the comparison is satisfied by either, and this amendment leaves that exception unchanged.

These are checks on persisted state; they do not give an implementation a choice of delta. The parent state transitions in [XLS-65](../README.md) §3.5.3, §3.6.3 and §3.7.3 still apply, and they are not the same for every operation:

- `VaultDeposit` and `VaultWithdraw` each derive a single $\Delta_{asset}$ and apply that one value to `Vault.AssetsTotal`, to `Vault.AssetsAvailable`, to the vault's asset balance and to the depositor's or destination's asset balance. Where that party is the issuer of a non-`XRP` `Vault.Asset`, it holds no balance of the asset — the transfer creates or destroys the asset at the issuer instead — so the value is applied only to the vault accounting fields and the vault's asset balance, and the comparison against a party delta above does not apply. This is the issuer exception of [XLS-65](../README.md) §3.5.4 item 2 and §3.6.4 item 2, which this amendment leaves unchanged.
- `VaultClawback` derives a single $\Delta_{asset}$ and applies that one value to `Vault.AssetsTotal`, to `Vault.AssetsAvailable` and to the vault's asset balance. The holder change is shares via $\Delta_{share}$ (§3.7.3); there is no holder underlying-asset transfer. When $\Delta_{asset} > 0$, the recovered assets are sent from the vault to the submitter (the asset issuer), not to the holder.

The `fixCleanup3_2_0` full-redemption path in `VaultWithdraw`, which zeroes both accounting fields and pays out the prior `Vault.AssetsAvailable`, is the one exception to the single-$\Delta_{asset}$ rule for withdraw, and this amendment does not change it.

##### 3.1.2.3 Deterministic delta

`fixCleanup3_4_0` adds one deterministic step to that transition, applied before any state change and only to the delta:

1. Take the posterior scale $s$ — the `STAmount` exponent of `Vault.AssetsTotal` $\pm \Delta_{asset}$ evaluated with round-to-nearest, the same scale the invariant compares at.
2. Round the magnitude of $\Delta_{asset}$ down at $s$. For a debit (`VaultWithdraw`, `VaultClawback`) that is $\lfloor |\Delta_{asset}| \rfloor_s$, so the vault debit never exceeds the value of the redeemed shares. For a credit (`VaultDeposit`) it is $\lfloor \text{AssetsTotal} + \Delta_{asset} \rfloor_s - \text{AssetsTotal}$, so the vault is never credited more than the depositor paid.
3. If the rounded delta is zero while shares would still move, fail with `tecPRECISION_LOSS`. Steps 1 to 3 apply only where $\Delta_{asset}$ is non-zero to begin with, so they do not disturb the two paths on which shares legitimately move for zero assets: the `VaultWithdraw` fixed-share exception below, and a `VaultClawback` against an already-empty vault, which decreases the holder's shares while the vault asset balance stays unchanged ([XLS-65](../README.md) §3.7.4 items 1 and 3). Both remain as they are.
4. Do not re-derive $\Delta_{share}$ from the rounded delta. The shares are burned or minted at their pre-rounding value and the trimmed sub-unit residue stays in the vault for the remaining shareholders.

For `XRP` and `MPT` the step is a no-op: $\Delta_{asset}$ is already integral.

The rounded $\Delta_{asset}$ is then applied as in the parent transitions above. The persisted results may still disagree, because each written field is quantised independently: `Vault.AssetsTotal` and `Vault.AssetsAvailable` are `STNumber` fields quantised to the asset on write, and each `STAmount` balance sits on its own grid, so one delta can land differently on each. For an `IOU` the persisted deltas may therefore differ from each other by at most one unit at the comparison scale above; for `XRP` and `MPT` they remain equal. That bound is the invariant check on the residue, not a licence to choose per-field deltas: an implementation that persists anything other than the single rounded $\Delta_{asset}$ does not conform, even where the result passes the check. Before the amendment, the delta is not rounded at the posterior scale and the comparisons and state changes are exact for every asset type, except the existing `SingleAssetVault` `VaultWithdraw` exception that an unrepresentable sub-ULP IOU remainder may remain between vault outflow and destination inflow.

For `VaultWithdraw`, a fixed-share withdrawal whose pre-transaction `AssetsTotal == LossUnrealized` may redeem shares while moving zero assets. Before the amendment, the missing vault and destination balance deltas cause the invariant to fail.

##### 3.1.2.4 Cap enforcement

Cap enforcement becomes:

- `Vault.AssetsTotal` is not required to be less than or equal to `Vault.AssetsMaximum` on every modification of the entry, and no invariant imposes that, because the excess may be interest that the Vault has recognised.
- `VaultSet` fails when `Vault.AssetsMaximum` is non-zero, `Vault.AssetsTotal` exceeds it, and the transaction either supplies `AssetsMaximum` or otherwise changes the cap. A `VaultSet` that omits `AssetsMaximum` and does not otherwise change the cap is no longer failed by this check.

Before the amendment, the loss inequality is strict for every asset type and admits no slack, `LossUnrealized` is not checked for sign, and the cap is required to hold on every `VaultSet` regardless of whether the transaction touches the cap.

#### 3.1.3 Example JSON

```json
{
  "LedgerEntryType": "Vault",
  "Asset": {
    "currency": "USD",
    "issuer": "rf1BiGeXwwQoi8Z2ueFYTEXSwuJYfV2Jpn"
  },
  "AssetsTotal": "1010",
  "AssetsAvailable": "10",
  "AssetsMaximum": "1000",
  "LossUnrealized": "1000"
}
```

## 4. Rationale

Each tolerance is one unit at the comparison scale rather than a relative epsilon. A relative tolerance would grow with the size of the Vault and would eventually be large enough to hide a real discrepancy. One unit at the comparison scale is the smallest representable difference on that grid; it can still mask a genuine one-unit accounting error, which is the bounded trade-off stated in Security Considerations. The numeric rule is unchanged: the comparison still admits at most that single unit.

Restricting the tolerance to non-integral assets, rather than granting it uniformly, was deliberate. The alternative of keying the tolerance off the sign of the scale would have been wrong: an `IOU` amount at or above `1e15` has a non-negative exponent yet still quantises, so it needs the tolerance, while a drop of `XRP` has scale zero and must not get it. Integrality of the asset is the property that actually distinguishes the two cases.

For the cap, the alternative was to exclude recognised interest from `AssetsTotal` so that the original invariant could stand. That was rejected because `AssetsTotal` is the basis of the share exchange rate; excluding interest from it would understate the value of a share.

Enforcing the cap on a `VaultSet` that supplies `AssetsMaximum` or otherwise changes the cap, rather than on every `VaultSet`, puts the failure where the submitter can act on it. Resubmitting the existing cap still runs the check. The `VaultDeposit` check is left alone because a deposit is exactly the event the cap exists to bound.

## 5. Security Considerations

Relaxing an invariant weakens a check that exists to catch implementation errors. The rounding tolerances are bounded to one unit at the applicable comparison scale and apply only to assets that quantise, while the cap remains enforced on every `VaultDeposit` and on any `VaultSet` that supplies `AssetsMaximum` or otherwise changes the cap.

Adding `LossUnrealized >= 0` closes a gap in the original invariant. A negative unrealised loss would otherwise pass the inequality and inflate the assets of the Vault relative to its shares.
