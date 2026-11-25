<pre>
  xls: 65.6
  title: Vault Withdrawal Transfer Fee and Input Range Checks
  description: Applies the asset transfer fee to third-party vault withdrawals, rejects out-of-range AssetsMaximum values, and refuses clawback from a missing holder
  author: Vytautas Vito Tumas <vtumas@ripple.com>
  proposal-from: https://github.com/XRPLF/XRPL-Standards/discussions/192
  status: Draft
  category: Amendment
  created: 2026-11-25
  updated: 2026-11-25
</pre>

# 65.6 Vault Withdrawal Transfer Fee and Input Range Checks

## 1. Abstract

The `fixCleanup3_5_0` amendment makes three changes to the Single Asset Vault:

1. `VaultWithdraw` charges the asset's transfer fee when a holder withdraws to a different account and neither account is the asset issuer.
2. `VaultCreate` and `VaultSet` reject an `AssetsMaximum` that cannot be represented as an amount of the Vault asset.
3. `VaultClawback` fails early when the `Holder` account does not exist.

## 2. Motivation

A withdrawal to a third party moves the asset from one holder to another through the Vault. Without the fee, depositing and then withdrawing to another account transferred an `IOU` or `MPT` without paying its transfer fee.

An `AssetsMaximum` outside the range of the asset, for example an `XRP` amount above the maximum number of drops, could not be rounded to the asset. Processing it raised an error instead of a clean failure.

A clawback naming a `Holder` that does not exist failed later in the transaction, after the fee had been charged, rather than being refused in preclaim as the other clawback transactions are.

## 3. Specification

### 3.1 Transaction: `VaultCreate`

#### 3.1.1 Failure Conditions

Add to parent [§3.2.5.1](../README.md#3251-data-verification):

- `SingleAssetVault`: The check does not apply.
- `fixCleanup3_5_0`: `AssetsMaximum` is present and cannot be represented as an amount of `Asset`. (`temMALFORMED`)

### 3.2 Transaction: `VaultSet`

#### 3.2.1 Failure Conditions

Add to parent [§3.3.2.2](../README.md#3322-protocol-level-failures):

- `SingleAssetVault`: The check does not apply.
- `fixCleanup3_5_0`: `AssetsMaximum` is present and cannot be represented as an amount of `Vault.Asset`. (`tecPRECISION_LOSS`)

### 3.3 Transaction: `VaultWithdraw`

#### 3.3.1 Transfer fee

Let the destination be `Destination` if present, otherwise the submitter. Let $r$ be the transfer rate of `Vault.Asset`, as defined for `IOU` and `MPT` transfers.

- `SingleAssetVault`: no transfer fee is charged.
- `fixCleanup3_5_0`: the fee is charged at rate $r$ unless one of these holds:
  - `Vault.Asset` is `XRP`;
  - the destination is the submitter;
  - the submitter is the issuer of `Vault.Asset`;
  - the destination is the issuer of `Vault.Asset`.

When the fee is charged:

1. If `Amount` is in the Vault asset, the shares to burn are computed from the grossed-up amount $Amount \times r$, rounded up, rather than from `Amount`. The parent withdraw formula (parent [§3.1.7.2.3](../README.md#31723-withdraw)) is applied to that grossed-up amount.
2. $\Delta_{asset}$ is computed from the burned shares as in the parent. The Vault, `Vault.AssetsTotal` and `Vault.AssetsAvailable` decrease by $\Delta_{asset}$.
3. The destination receives $\Delta_{asset} / r$, rounded down. The difference is the transfer fee.

#### 3.3.2 Failure Conditions

Add to parent [§3.6.2.2](../README.md#3622-protocol-level-failures):

- `fixCleanup3_5_0`: $\Delta_{asset}$ is greater than zero, and the amount the destination receives after the transfer fee is zero. (`tecPRECISION_LOSS`)

The destination checks of [XLS-65.1](../65.1-fix-cleanup-3_1_3/README.md) use the amount after the fee.

#### 3.3.3 Invariants

This changes parent [§3.6.4](../README.md#364-invariants) item 3 when the fee is charged. The submitter is not the issuer, the destination differs from the submitter, and the transfer rate is not parity. In that case:

- the expected destination increase is the vault outflow divided by $r$, rounded down;
- the sub-ULP remainder exception of [XLS-65.2](../65.2-fix-cleanup-3_2_0/README.md) does not apply. The one-unit tolerance of [XLS-65.5](../65.5-fix-cleanup-3_4_0/README.md) still does.

### 3.4 Transaction: `VaultClawback`

#### 3.4.1 Failure Conditions

Add to parent [§3.7.2.2](../README.md#3722-protocol-level-failures), immediately after the Vault existence check:

- `SingleAssetVault`: The check does not apply. A missing `Holder` fails later in the transaction.
- `fixCleanup3_5_0`: The `Holder` account does not exist. (`terNO_ACCOUNT`)

### 3.5 Ledger Entry: `AccountRoot` (Vault _pseudo-account_)

#### 3.5.1 Owned Entries

[XLS-64.2](../../XLS-0064-pseudo-account/64.2-fix-cleanup-3_5_0/README.md) requires every entry a transaction adds to a _pseudo-account_'s owner directory to be one that the owning object's specification allows. The Vault _pseudo-account_ (the `AccountRoot` with `VaultID`) may own only:

- the share `MPTokenIssuance` identified by `Vault.ShareMPTID`;
- its holding of `Vault.Asset`: the `RippleState` for an `IOU` or the `MPToken` for an `MPT`. `XRP` has no holding entry;
- a `LoanBroker` whose `VaultID` is this Vault.

This changes parent [§3.1.3](../README.md#313-pseudo-account).

## 4. Rationale

The fee is waived wherever an ordinary payment would not charge it: for `XRP`, for a payment to oneself, and for payments from or to the issuer. Grossing up an asset-denominated withdrawal keeps the destination's receipt equal to the requested `Amount`, as a payment with a transfer fee would. The submitter's shares cover the fee.

Checking that `AssetsMaximum` is representable turns an internal error into an ordinary failure code. `VaultCreate` can check it in preflight because the asset is in the transaction. `VaultSet` reads the asset from the Vault, so the check happens in preclaim.

## 5. Security Considerations

Charging the fee closes a way to move a fee-bearing asset between two holders without paying the issuer's fee. Withdrawals to oneself and to the issuer are unaffected, so no holder pays a fee to recover their own funds.

The fee-adjusted invariant keeps the one-unit tolerance but drops the sub-ULP remainder exception. The fee is the only allowed difference between vault outflow and destination inflow beyond that unit.
