<pre>
  xls: 65.4
  title: Vault Withdrawal Limits and Clawback Clamp
  description: Checks share-denominated withdrawals against the destination at their asset value, and clamps full clawbacks to the assets available
  author: Vytautas Vito Tumas <vtumas@ripple.com>
  proposal-from: https://github.com/XRPLF/XRPL-Standards/discussions/192
  status: Final
  category: Amendment
  created: 2026-11-25
  updated: 2026-11-25
</pre>

# 65.4 Vault Withdrawal Limits and Clawback Clamp

## 1. Abstract

The `fixCleanup3_1_3` amendment makes two corrections to the Single Asset Vault.

1. When `VaultWithdraw.Amount` is in vault shares, the destination's trust-line limit is checked against the asset amount those shares convert to. Before the amendment, a share-denominated withdrawal was never checked against that limit.
2. A `VaultClawback` with a zero `Amount` is limited to `Vault.AssetsAvailable`, as a non-zero `Amount` already was. Before the amendment, a zero `Amount` paid out the full value of the holder's shares, even when part of that value was lent out.

## 2. Motivation

A withdrawal can be stated in assets or in shares. Both pay out assets, so both must pass the same destination checks. Before the amendment, stating the amount in shares avoided the destination's trust-line limit, which depends on the amount delivered.

A clawback with a zero `Amount` claws back every share the holder owns. When the Vault has lent part of its assets, the value of those shares can exceed the cash in the Vault. Without the clamp, the clawback could recover more than `Vault.AssetsAvailable`.

## 3. Specification

### 3.1 Transaction: `VaultWithdraw`

#### 3.1.1 Fields

No fields are added or removed.

#### 3.1.2 Failure Conditions

This changes the trust-line limit check among the destination checks of parent [§3.6.2.2](../README.md#3622-protocol-level-failures). That check applies when `Vault.Asset` is an `IOU` and the destination is neither the submitter nor the issuer. It fails with `tecNO_LINE` when the amount exceeds the room left under the destination's trust-line limit to the issuer. A destination with no trust line has no room. For `XRP` and `MPT` the check always passes.

- `SingleAssetVault`: The checks are evaluated on the transaction as submitted. When `Amount` is in shares, the check sees an `MPT` amount and always passes, so a share-denominated withdrawal is never checked against the destination's trust-line limit.
- `fixCleanup3_1_3`: When `Amount` is in shares, the shares are first converted to assets with the redeem formula of parent [§3.1.7.2.2](../README.md#31722-redeem). The trust-line limit check is then evaluated against that asset amount. If [XLS-65.7](../65.7-fix-cleanup-3_5_0/README.md) applies a transfer fee, it uses the amount after the fee. An arithmetic overflow during the conversion fails the transaction with `tecPATH_DRY`.

The other destination checks are the same before and after the amendment, for both forms of `Amount`. They reject a `Destination` that does not exist (`tecNO_DST`), requires a destination tag that is missing (`tecDST_TAG_NEEDED`), or requires deposit authorization the submitter lacks (`tecNO_PERMISSION`).

The conversion uses the same `LossUnrealized` treatment as the withdrawal itself, including the sole-shareholder exception of [XLS-65.5](../65.5-fix-cleanup-3_2_0/README.md).

#### 3.1.3 State Changes

Unchanged.

### 3.2 Transaction: `VaultClawback`

#### 3.2.1 Fields

No fields are added or removed.

#### 3.2.2 State Changes

This changes how parent [§3.7](../README.md#37-transaction-vaultclawback) derives $\Delta_{asset}$ and $\Delta_{share}$ when the asset issuer submits a clawback with a zero `Amount`:

- `SingleAssetVault`: $\Delta_{share}$ is the holder's whole share balance and $\Delta_{asset}$ is the redeem value of those shares. $\Delta_{asset}$ is not limited to `Vault.AssetsAvailable`.
- `fixCleanup3_1_3`: $\Delta_{share}$ and $\Delta_{asset}$ are derived as before. If $\Delta_{asset}$ exceeds `Vault.AssetsAvailable`, $\Delta_{asset}$ becomes `Vault.AssetsAvailable`. $\Delta_{share}$ is then recomputed from it with the withdraw formula, truncated to whole shares. $\Delta_{asset}$ is then recomputed from that $\Delta_{share}$ with the redeem formula. This is the same clamp a non-zero `Amount` already used.

## 4. Rationale

A share-denominated withdrawal delivers assets just like an asset-denominated one. Converting the shares before checking the destination gives both forms the same checks without a separate rule for each.

The clawback clamp already existed for a non-zero `Amount`. A zero `Amount` returned before reaching it. The amendment routes both through the same calculation, rather than adding a second clamp.

## 5. Security Considerations

The withdrawal change closes a way to send assets to a destination that would reject them if the amount had been stated in assets.

The clawback change stops an issuer recovering assets the Vault does not hold. Without it, a clawback against a Vault with outstanding Loans could take value that belongs to the remaining shareholders. With the clamp, the holder keeps any shares whose value is not covered by `Vault.AssetsAvailable`.
