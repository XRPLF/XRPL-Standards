<pre>
  xls: 65.5
  title: Vault Precision and Redemption Fixes
  description: Rounds deposits to the Vault precision, completes full redemptions, waives unrealized loss for a sole shareholder, and records the share issuance's backing holding
  author: Vytautas Vito Tumas <vtumas@ripple.com>
  proposal-from: https://github.com/XRPLF/XRPL-Standards/discussions/192
  status: Final
  category: Amendment
  created: 2026-11-25
  updated: 2026-11-25
</pre>

# 65.5 Vault Precision and Redemption Fixes

## 1. Abstract

The `fixCleanup3_2_0` amendment corrects how the Single Asset Vault handles precision and full redemption:

- **Deposit rounding.** `VaultDeposit` rounds the deposited amount toward zero at the precision the Vault will hold after the deposit. It rejects a deposit that rounds to zero at that precision, or at the precision of the depositor's own balance.
- **Withdrawal recovery path.** `VaultWithdraw` no longer requires an `MPT` asset to be transferable.
- **Sole-shareholder waiver.** A sole shareholder withdraws at a price that ignores `LossUnrealized`.
- **Full redemption.** A withdrawal that redeems every outstanding share empties the Vault exactly.
- **Backing holding.** `VaultCreate` records, on the share `MPTokenIssuance`, which ledger entry holds the Vault's assets.
- **Invariants.** The Vault invariants compare amounts at the posterior `AssetsTotal` precision. They tolerate a destination `IOU` balance that cannot represent the last digits of a withdrawal.

## 2. Motivation

`IOU` amounts carry 16 significant digits, so the precision of `Vault.AssetsTotal` falls as the Vault grows. A deposit with more digits than the Vault can hold was credited to the Vault at one precision and debited from the depositor at another. Shares could then be minted for value the Vault never recorded.

A full redemption computed the payout from the share price. Rounding could leave a residue in `AssetsTotal` or `AssetsAvailable` after the last share was burned. The result was a Vault with no shares and non-zero assets, which the invariants reject.

A depositor who holds every share is entitled to the whole Vault, including the value currently marked as unrealized loss. Pricing their withdrawal net of `LossUnrealized` left that value in a Vault nobody else owns.

An issuer that clears `lsfMPTCanTransfer` on its `MPT` blocked every withdrawal, trapping depositor funds in the Vault.

## 3. Specification

### 3.1 Ledger Entry: `Vault`

#### 3.1.1 Fields

No fields are added or removed.

#### 3.1.2 Invariants

##### 3.1.2.1 Comparison scale

The invariants for `VaultDeposit`, `VaultWithdraw` and `VaultClawback` round the deltas they compare to a common scale:

- `SingleAssetVault`: the coarsest scale of three deltas: the Vault pseudo-account's asset balance, `Vault.AssetsTotal`, and `Vault.AssetsAvailable`. Each delta's scale is the coarser of its before and after `STAmount` exponents.
- `fixCleanup3_2_0`: the `STAmount` exponent of the posterior `Vault.AssetsTotal`, computed with round-to-nearest.

##### 3.1.2.2 `VaultWithdraw` destination

This changes parent [§3.6.4](../README.md#364-invariants) items 2 and 3 for a destination that is not the asset issuer:

- `SingleAssetVault`: the destination's asset balance must increase. The rounded vault outflow and destination inflow must be equal.
- `fixCleanup3_2_0`: for an `IOU`, the rounded destination increase may be zero. The comparison also passes when the vault outflow minus the destination inflow, rounded down at the destination's scale, is zero; that difference is an unrepresentable sub-ULP remainder at the destination. `XRP` and `MPT` keep the `SingleAssetVault` rule.

[XLS-65.2](../65.2-fix-cleanup-3_4_0/README.md) later adds a one-unit tolerance as an alternative to this remainder. [XLS-65.7](../65.7-fix-cleanup-3_5_0/README.md) removes the remainder exception when a transfer fee is charged.

### 3.2 Ledger Entry: `MPTokenIssuance`

#### 3.2.1 Fields

`VaultCreate` sets one more field on the share `MPTokenIssuance` (parent [§3.1.6.2.1](../README.md#31621-mptokenissuance-values)):

| Field Name         | Required | JSON Type | Internal Type | Default Value | Description                                                                                                                                                                                                            |
| ------------------ | :------: | :-------: | :-----------: | :-----------: | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `ReferenceHolding` |    No    | `string`  |   `UINT256`   |     `N/A`     | The ledger entry ID of the Vault pseudo-account's holding of `Vault.Asset`. For an `MPT`, the pseudo-account's `MPToken`. For an `IOU`, the `RippleState` between the pseudo-account and the issuer. Absent for `XRP`. |

#### 3.2.2 Share transferability and tradability

Under `fixCleanup3_2_0`, a vault share whose `MPTokenIssuance` has `ReferenceHolding` inherits the checks of the underlying asset. The underlying asset is the asset of the holding that `ReferenceHolding` names.

- **Transfer.** A share transfer between two accounts, neither of which is the share issuer, must first pass the share's own checks, including `lsfMPTCanTransfer`. It must then also pass the transferability check for the underlying asset between the same two accounts. A transfer to or from the share issuer, or a protocol path that waives `lsfMPTCanTransfer`, passes without either check. When the underlying asset's check is reached, it is never waived.
- **Trading.** A share with `lsfMPTCanTrade` set can be traded only if the underlying asset can also be traded. An `MPT` underlying asset needs `lsfMPTCanTrade`; an `IOU` underlying asset adds no condition.

Before the amendment, neither check looks at the underlying asset.

#### 3.2.3 Invariants

Under `fixCleanup3_2_0`:

1. `ReferenceHolding` is set only by `VaultCreate`, when it creates the share `MPTokenIssuance`.
2. `ReferenceHolding` never changes on an existing `MPTokenIssuance`: it is not added, removed or replaced.
3. An `MPToken` or `RippleState` held by a Vault _pseudo-account_ is deleted only by `VaultDelete`.

### 3.3 Transaction: `VaultCreate`

#### 3.3.1 State Changes

Extend parent [§3.2.6](../README.md#326-state-changes) step 2:

- `SingleAssetVault`: the share `MPTokenIssuance` has no `ReferenceHolding`.
- `fixCleanup3_2_0`: if `Vault.Asset` is an `IOU` or `MPT`, set `ReferenceHolding` on the share `MPTokenIssuance` as in §3.2.1.

### 3.4 Transaction: `VaultDeposit`

#### 3.4.1 Failure Conditions

Parent [§3.5.2.2](../README.md#3522-protocol-level-failures) gains two checks under `fixCleanup3_2_0`. Let $A'$ be `Amount` rounded toward zero at the scale of the posterior `Vault.AssetsTotal`, that is the `STAmount` exponent of `Vault.AssetsTotal + Amount` computed with round-to-nearest. For `XRP` and `MPT`, $A' =$ `Amount`.

1. $A'$ is zero. (`tecPRECISION_LOSS`)
2. `Vault.Asset` is an `IOU`, the depositor is not its issuer, and `Amount` is zero at the scale of the depositor's balance of the asset. (`tecPRECISION_LOSS`)

The insufficient-funds check compares the depositor's balance with $A'$ instead of `Amount`.

#### 3.4.2 State Changes

- `SingleAssetVault`: the exchange of parent [§3.1.7.2.1](../README.md#31721-deposit) starts from `Amount`. After the transfer, a negative asset balance for the depositor fails the transaction with `tefINTERNAL`.
- `fixCleanup3_2_0`: the exchange starts from $A'$. The post-transfer balance check is removed. It only fired when an `IOU` deposit drew the depositor's trust line below zero, which the insufficient-funds check permits.

### 3.5 Transaction: `VaultWithdraw`

#### 3.5.1 Failure Conditions

The transferability check of parent [§3.6.2.2](../README.md#3622-protocol-level-failures), from the Vault pseudo-account to the destination:

- `SingleAssetVault`: includes the `MPT` `lsfMPTCanTransfer` flag (`tecNO_AUTH`).
- `fixCleanup3_2_0`: ignores `lsfMPTCanTransfer`. Every other transferability check still applies.

#### 3.5.2 Exchange

A **sole shareholder** is an account whose share `MPToken.MPTAmount` equals the non-zero `OutstandingAmount` of the share issuance.

- `SingleAssetVault`: $\Gamma_{asset}$ in parent [§3.6.1](../README.md#361-fields) is always `Vault.AssetsTotal - Vault.LossUnrealized`.
- `fixCleanup3_2_0`: when the submitter is a sole shareholder, $\Gamma_{asset}$ is `Vault.AssetsTotal`. The waiver applies both to the conversion and to the preclaim checks of [XLS-65.4](../65.4-fix-cleanup-3_1_3/README.md).

#### 3.5.3 State Changes

A **final withdrawal** redeems every outstanding share.

- `SingleAssetVault`: a final withdrawal pays out the computed $\Delta_{asset}$ and decreases `Vault.AssetsTotal` and `Vault.AssetsAvailable` by it.
- `fixCleanup3_2_0`: a final withdrawal pays out `Vault.AssetsAvailable` and sets `Vault.AssetsTotal` and `Vault.AssetsAvailable` to zero.
  - `Vault.LossUnrealized` is necessarily zero here. A non-zero `LossUnrealized` makes `Vault.AssetsTotal` exceed `Vault.AssetsAvailable`, and the withdrawal has already failed with `tecINSUFFICIENT_FUNDS`.
  - A Vault created under [XLS-65.3.1](../65.3-lending-protocol-v1_2/65.3.1-fixed-precision.md) is not zeroed. Its balances change through that patch's balance writer.

## 4. Rationale

Rounding the deposit to the posterior Vault precision, rather than the current one, matches the precision the Vault will actually store. It is also the scale the invariants compare at. Checking the depositor's precision separately catches a deposit the Vault can represent but the depositor's trust line cannot.

Setting the final payout to `AssetsAvailable` resolves a full redemption from the Vault's own state rather than from a rounded share price. It cannot leave a residue behind.

`ReferenceHolding` lets code that holds only the share `MPTokenIssuance` find the Vault's underlying asset without reading the Vault. Share transferability and tradability checks use it to apply the underlying asset's own checks to the shares (§3.2.2). The invariants of §3.2.3 keep the pointer valid: the holding it names cannot change, and cannot be deleted while the Vault exists.

## 5. Security Considerations

Rounding a deposit toward zero means the Vault never credits more than the depositor pays. Rejecting zero-precision deposits stops shares being minted for nothing.

Waiving `LossUnrealized` for a sole shareholder cannot harm another shareholder, because there is none.

Ignoring `lsfMPTCanTransfer` on withdrawal keeps depositors able to recover their assets. Freeze, lock and authorization checks still apply, so an issuer's compliance controls are unchanged.

The sub-ULP tolerance applies only to `IOU` assets and only to a difference that the destination cannot represent. It cannot hide a representable discrepancy.
