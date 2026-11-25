<pre>
  xls: 65.2
  title: Vault Accounting and Cap Invariants
  description: Admits one unit of rounding slack for IOU accounting invariants, requires LossUnrealized to be non-negative, narrows VaultSet cap enforcement, and tightens VaultDeposit, VaultWithdraw and VaultClawback checks
  author: Vytautas Vito Tumas <vtumas@ripple.com>
  proposal-from: https://github.com/XRPLF/XRPL-Standards/discussions/192
  status: Final
  category: Amendment
  created: 2026-09-04
  updated: 2026-11-25
</pre>

# 65.2 Vault Accounting and Cap Invariants

## 1. Abstract

Under the `fixCleanup3_4_0` amendment, when the Vault asset is not integral — that is, an `IOU` — the `LossUnrealized` bound and the accounting-delta comparisons made by `VaultDeposit`, `VaultWithdraw` and `VaultClawback` admit one unit of rounding tolerance at their comparison scale; for `XRP` and `MPT` the comparisons stay strict. `LossUnrealized` must also not be negative, for every asset type, and a fully impaired fixed-share withdrawal may redeem shares for zero assets. Separately, `VaultSet` no longer fails the cap check when the transaction omits `AssetsMaximum` and does not otherwise change the cap, so a Vault whose total has grown past its cap through interest can still be updated.

The amendment also tightens the transactions themselves:

- `VaultWithdraw` and `VaultClawback` truncate the shares they burn instead of rounding to nearest.
- `VaultClawback` waives `LossUnrealized` for a sole shareholder.
- `VaultDeposit` rejects a deposit that would leave the depositor's stored balance unchanged.
- `VaultWithdraw` and `VaultClawback` refuse a pseudo-account as destination or holder.
- `VaultWithdraw` gains an optional `CredentialIDs` field. It checks that a self-withdrawal can create the holding it needs. It applies a private Vault's permissioned domain to withdrawals paid to a third party.

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

For `VaultWithdraw`, the existing `fixCleanup3_2_0` exception ([XLS-65.5](../65.5-fix-cleanup-3_2_0/README.md)) that an unrepresentable sub-ULP IOU remainder may remain between vault outflow and destination inflow is an alternative to this one-unit bound, not an addition to it: the comparison is satisfied by either, and this amendment leaves that exception unchanged.

These are checks on persisted state; they do not give an implementation a choice of delta. The parent state transitions in [XLS-65](../README.md) §3.5.3, §3.6.3 and §3.7.3 still apply, and they are not the same for every operation:

- `VaultDeposit` and `VaultWithdraw` each derive a single $\Delta_{asset}$ and apply that one value to `Vault.AssetsTotal`, to `Vault.AssetsAvailable`, to the vault's asset balance and to the depositor's or destination's asset balance. Where that party is the issuer of a non-`XRP` `Vault.Asset`, it holds no balance of the asset — the transfer creates or destroys the asset at the issuer instead — so the value is applied only to the vault accounting fields and the vault's asset balance, and the comparison against a party delta above does not apply. This is the issuer exception of [XLS-65](../README.md) §3.5.4 item 2 and §3.6.4 item 2, which this amendment leaves unchanged.
- `VaultClawback` derives a single $\Delta_{asset}$ and applies that one value to `Vault.AssetsTotal`, to `Vault.AssetsAvailable` and to the vault's asset balance. The holder change is shares via $\Delta_{share}$ (§3.7.3); there is no holder underlying-asset transfer. When $\Delta_{asset} > 0$, the recovered assets are sent from the vault to the submitter (the asset issuer), not to the holder.

The `fixCleanup3_2_0` full-redemption path in `VaultWithdraw`, which zeroes both accounting fields and pays out the prior `Vault.AssetsAvailable`, is the one exception to the single-$\Delta_{asset}$ rule for withdraw, and this amendment does not change it.

##### 3.1.2.3 Deterministic delta

`fixCleanup3_4_0` adds one deterministic step to that transition, applied before any state change and only to the delta:

1. Take the posterior scale $s$ — the `STAmount` exponent of `Vault.AssetsTotal` $\pm \Delta_{asset}$ evaluated with round-to-nearest, the same scale the invariant compares at.
2. Round the magnitude of $\Delta_{asset}$ down at $s$. For a debit (`VaultWithdraw`, `VaultClawback`) that is $\lfloor |\Delta_{asset}| \rfloor_s$, so the vault debit never exceeds the value of the redeemed shares. For a credit (`VaultDeposit`) it is $\lfloor \text{AssetsTotal} + \Delta_{asset} \rfloor_s - \text{AssetsTotal}$, so the vault is never credited more than the depositor paid.
3. If the rounded delta is zero while shares would still move, fail with `tecPRECISION_LOSS`. Steps 1 to 3 apply only where $\Delta_{asset}$ is non-zero to begin with, so they do not disturb the two paths on which shares legitimately move for zero assets: the `VaultWithdraw` fixed-share exception below, and a `VaultClawback` against an already-empty vault, which decreases the holder's shares while the vault asset balance stays unchanged ([XLS-65](../README.md) §3.7.4 items 1 and 3). Both remain as they are.

   A `VaultWithdraw` that redeems every outstanding share is exempt from steps 1 to 3. It is also exempt from the zero-asset check and the dust check of §3.3.2.2. Its payout is set to `Vault.AssetsAvailable` by the `fixCleanup3_2_0` full-redemption path ([XLS-65.5](../65.5-fix-cleanup-3_2_0/README.md)).

4. Do not re-derive $\Delta_{share}$ from the rounded delta; the shares are burned or minted at their pre-rounding value. Where the trimmed sub-unit ends up depends on the direction:
   - On a debit (`VaultWithdraw`, `VaultClawback`) it stays in the vault for the remaining shareholders: the shares are burned for their pre-rounding value while the vault pays out the smaller rounded amount.
   - On a credit (`VaultDeposit`) it stays with the depositor, who is debited the rounded delta but receives shares priced before the rounding. Re-deriving the share count here would mint fewer shares while still charging for the pre-rounding amount.

For `XRP` and `MPT` the step is a no-op: $\Delta_{asset}$ is already integral.

The rounded $\Delta_{asset}$ is then applied as in the parent transitions above. The persisted results may still disagree, because each written field is quantised independently: `Vault.AssetsTotal` and `Vault.AssetsAvailable` are `STNumber` fields quantised to the asset on write, and each `STAmount` balance sits on its own grid, so one delta can land differently on each. For an `IOU` the persisted deltas may therefore differ from each other by at most one unit at the comparison scale above; for `XRP` and `MPT` they remain equal. That bound is the invariant check on the residue, not a licence to choose per-field deltas: an implementation that persists anything other than the single rounded $\Delta_{asset}$ does not conform, even where the result passes the check. Before the amendment, the $\Delta_{asset}$ derived from the shares is not rounded at the posterior scale. `fixCleanup3_2_0` ([XLS-65.5](../65.5-fix-cleanup-3_2_0/README.md)) already rounds the requested deposit `Amount` toward zero at that scale, but not the amount recomputed from the minted shares. Without this amendment the comparisons are exact for every asset type. The one exception is the `fixCleanup3_2_0` `VaultWithdraw` rule that an unrepresentable sub-ULP IOU remainder may remain between vault outflow and destination inflow.

For `VaultWithdraw`, a fixed-share withdrawal whose pre-transaction `AssetsTotal == LossUnrealized` may redeem shares while moving zero assets. Before the amendment, the missing vault and destination balance deltas cause the invariant to fail.

##### 3.1.2.4 Cap enforcement

Cap enforcement becomes:

- `Vault.AssetsTotal` is not required to be less than or equal to `Vault.AssetsMaximum` on every modification of the entry, and no invariant imposes that, because the excess may be interest that the Vault has recognised.
- `VaultSet` fails when `Vault.AssetsMaximum` is non-zero, `Vault.AssetsTotal` exceeds it, and the transaction either supplies `AssetsMaximum` or otherwise changes the cap. A `VaultSet` that omits `AssetsMaximum` and does not otherwise change the cap is no longer failed by this check.

Before the amendment, the loss inequality is strict for every asset type and admits no slack, `LossUnrealized` is not checked for sign, and the cap is required to hold on every `VaultSet` regardless of whether the transaction touches the cap.

##### 3.1.2.5 `XRP` fee correction

When `Vault.Asset` is `XRP`, the invariants add the transaction fee back to an account's balance change before comparing it with the Vault's.

- Before the amendment, the fee is added back only to the submitting `Account`, and only when that account paid the fee. A zero result is treated as no change only when the fee was added back.
- Under the amendment, the fee is added back to whichever account paid it: the submitter, a delegate, or a co-signing fee sponsor. It is never added back for a pre-funded sponsorship, whose fee is not drawn from an account balance. A resulting zero is treated as no change in every case. An account touched only for sequence or ticket processing is therefore never mistaken for a payout recipient.

### 3.2 Transaction: `VaultDeposit`

#### 3.2.1 Fields

No fields are added or removed.

#### 3.2.2 Failure Conditions

Add to parent [§3.5.2.2](../README.md#3522-protocol-level-failures), after the posterior-scale rounding of §3.1.2.3:

1. `Vault.Asset` is an `IOU`, and debiting the rounded $\Delta_{asset}$ would leave the depositor's stored balance of the asset unchanged. (`tecPRECISION_LOSS`)

### 3.3 Transaction: `VaultWithdraw`

#### 3.3.1 Fields

Add to parent [§3.6.1](../README.md#361-fields):

| Field Name      | Required | JSON Type | Internal Type | Default Value | Description                                                                                                                                            |
| --------------- | :------: | :-------: | :-----------: | :-----------: | ------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `CredentialIDs` |    No    |  `array`  |  `VECTOR256`  |     `N/A`     | Credentials of the submitter, as defined by [XLS-70](../../XLS-0070-credentials/README.md), used where the destination requires deposit authorization. |

#### 3.3.2 Failure Conditions

##### 3.3.2.1 Data Verification

Add to parent [§3.6.2.1](../README.md#3621-data-verification):

1. `CredentialIDs` is present and either the `Credentials` amendment or `fixCleanup3_4_0` is not enabled. (`temDISABLED`)
2. `CredentialIDs` is empty, has more entries than the [XLS-70](../../XLS-0070-credentials/README.md) maximum, contains a zero ID, or contains a duplicate. (`temMALFORMED`)

##### 3.3.2.2 Protocol-Level Failures

Add to parent [§3.6.2.2](../README.md#3622-protocol-level-failures), in this order after the transferability check:

1. `CredentialIDs` is present and a listed credential does not exist, does not have the submitter as its subject, or has not been accepted ([XLS-70](../../XLS-0070-credentials/README.md)). (`tecBAD_CREDENTIALS`)
2. The destination is a _pseudo-account_. (`tecPSEUDO_ACCOUNT`)
3. The destination is the submitter, the submitter has no holding of `Vault.Asset`, and a holding cannot be added. For an `IOU`, the issuer account does not exist (`terNO_ACCOUNT`) or lacks `lsfDefaultRipple` (`terNO_RIPPLE`). For an `MPT`, the `MPTokenIssuance` does not exist (`tecOBJECT_NOT_FOUND`) or `lsfMPTCanTransfer` is not set (`tecNO_AUTH`).
4. The Vault has `lsfVaultPrivate` set, the destination is neither the submitter nor the issuer of `Vault.Asset`, and either the submitter or the destination is not a member of the permissioned domain on `MPTokenIssuance(Vault.ShareMPTID)`. This is the same membership check as `VaultDeposit`, but an expired credential is a failure here, not tolerated. (`tecNO_AUTH`, or the credential failure code)

In `doApply`, when the withdrawal does not redeem every outstanding share:

5. `Amount` is in shares, the computed $\Delta_{asset}$ is zero, and $\Gamma_{asset}$ is non-zero. (`tecPRECISION_LOSS`)
6. $\Delta_{asset}$ is non-zero but subtracting it would leave the stored balance unchanged at its precision. On a Vault with `LEVersion` below `2` that balance is `Vault.AssetsTotal`. (`tecPRECISION_LOSS`)
7. `Vault.AssetsAvailable` is less than $\Delta_{asset}$ before the rounding of §3.1.2.3. (`tecINSUFFICIENT_FUNDS`) This check runs before the rounding, so a withdrawal that is both too large and too small to represent reports `tecINSUFFICIENT_FUNDS`.

#### 3.3.3 Exchange

This changes the withdraw formula of parent [§3.1.7.2.3](../README.md#31723-withdraw) when `Amount` is in the Vault asset:

- `SingleAssetVault`: $\Delta_{share}$ is rounded to the nearest whole share. The redeemed value can then exceed `Amount`.
- `fixCleanup3_4_0`: $\Delta_{share}$ is truncated to whole shares, so the payout never exceeds `Amount`. A truncation to zero fails with `tecPRECISION_LOSS`.

### 3.4 Transaction: `VaultClawback`

#### 3.4.1 Fields

No fields are added or removed.

#### 3.4.2 Failure Conditions

Add to parent [§3.7.2.2](../README.md#3722-protocol-level-failures), before the checks on `Amount`:

1. `Holder` is a _pseudo-account_. (`tecPSEUDO_ACCOUNT`)

#### 3.4.3 Exchange

When the asset issuer claws back assets:

- `SingleAssetVault`: $\Gamma_{asset}$ is `Vault.AssetsTotal - Vault.LossUnrealized`. For a non-zero `Amount`, $\Delta_{share}$ is rounded to the nearest whole share.
- `fixCleanup3_4_0`:
  - When `Holder` is a sole shareholder (as defined in [XLS-65.5](../65.5-fix-cleanup-3_2_0/README.md)), $\Gamma_{asset}$ is `Vault.AssetsTotal`. With a zero `Amount`, $\Delta_{share}$ is the whole `OutstandingAmount`.
  - For a non-zero `Amount`, $\Delta_{share}$ is truncated to whole shares.
  - A recovered $\Delta_{asset}$ that is non-zero but would leave the stored balance unchanged fails with `tecPRECISION_LOSS`. This is the same check as for `VaultWithdraw`.

## 4. Rationale

Each tolerance is one unit at the comparison scale rather than a relative epsilon. A relative tolerance would grow with the size of the Vault and would eventually be large enough to hide a real discrepancy. One unit at the comparison scale is the smallest representable difference on that grid; it can still mask a genuine one-unit accounting error, which is the bounded trade-off stated in Security Considerations. The numeric rule is unchanged: the comparison still admits at most that single unit.

Restricting the tolerance to non-integral assets, rather than granting it uniformly, was deliberate. The alternative of keying the tolerance off the sign of the scale would have been wrong: an `IOU` amount at or above `1e15` has a non-negative exponent yet still quantises, so it needs the tolerance, while a drop of `XRP` has scale zero and must not get it. Integrality of the asset is the property that actually distinguishes the two cases.

For the cap, the alternative was to exclude recognised interest from `AssetsTotal` so that the original invariant could stand. That was rejected because `AssetsTotal` is the basis of the share exchange rate; excluding interest from it would understate the value of a share.

Enforcing the cap on a `VaultSet` that supplies `AssetsMaximum` or otherwise changes the cap, rather than on every `VaultSet`, puts the failure where the submitter can act on it. Resubmitting the existing cap still runs the check. The `VaultDeposit` check is left alone because a deposit is exactly the event the cap exists to bound.

Truncating the shares burned by an asset-denominated withdrawal or clawback, rather than rounding to nearest, keeps the payout at or below the requested `Amount`. The destination checks were evaluated against that amount, so the payout must not exceed it.

A pseudo-account belongs to a ledger object, not a person, and never holds vault shares. Refusing it as a withdrawal destination or clawback holder reports the real reason, instead of failing later on deposit authorization or on the shares-must-move invariant.

## 5. Security Considerations

Relaxing an invariant weakens a check that exists to catch implementation errors. The rounding tolerances are bounded to one unit at the applicable comparison scale and apply only to assets that quantise, while the cap remains enforced on every `VaultDeposit` and on any `VaultSet` that supplies `AssetsMaximum` or otherwise changes the cap.

Rounding the delta without re-deriving the share count moves a sub-unit of value in a direction that depends on the operation. On `VaultWithdraw` and `VaultClawback` it favours the remaining shareholders, since the vault pays out less than the burned shares were worth. On `VaultDeposit` it favours the depositor, who pays the rounded amount but receives shares priced before the rounding, diluting existing shareholders by less than one unit at the posterior `AssetsTotal` scale. The bound is per transaction, so a depositor can repeat it across many deposits; each repetition gains at most that one unit, which is the smallest representable amount at that scale, and costs a transaction fee. The alternative of re-deriving the shares from the rounded delta does not remove the asymmetry, it reverses it, charging the depositor for shares that are never minted.

Adding `LossUnrealized >= 0` closes a gap in the original invariant. A negative unrealised loss would otherwise pass the inequality and inflate the assets of the Vault relative to its shares.

Applying the permissioned domain to third-party withdrawals of a private Vault stops a shareholder who lost access paying the Vault's assets out to another account outside the domain. Withdrawing to oneself, and paying the asset back to its issuer, stay open, so a depositor cannot be locked out of their own funds.
