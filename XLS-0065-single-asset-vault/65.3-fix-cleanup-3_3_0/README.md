<pre>
  xls: 65.3
  title: Vault Freeze Checks
  description: Replaces the VaultDeposit and VaultWithdraw freeze checks with checks on every account the asset moves through
  author: Vytautas Vito Tumas <vtumas@ripple.com>
  proposal-from: https://github.com/XRPLF/XRPL-Standards/discussions/192
  status: Final
  category: Amendment
  created: 2026-11-25
  updated: 2026-11-25
</pre>

# 65.3 Vault Freeze Checks

## 1. Abstract

The `fixCleanup3_3_0` amendment replaces the freeze checks of `VaultDeposit` and `VaultWithdraw`. The new checks look at every account the asset passes through: the depositor or submitter, the Vault pseudo-account, and the destination. They no longer check the vault shares, which are frozen only through the underlying asset. A regular freeze no longer blocks a holder from withdrawing to themselves, and a deposit is refused if the Vault pseudo-account's own holding is frozen.

## 2. Motivation

The original checks looked at the depositor and at the vault shares. They ignored the Vault pseudo-account. An issuer could freeze the pseudo-account's trust line, and deposits would still succeed into a holding that could never be withdrawn.

On withdrawal, the original checks treated a regular freeze on the submitter's shares the same as a deep freeze. A regular freeze is meant to stop a holder sending an asset to others, not to stop them recovering their own funds.

## 3. Specification

The checks below fail with `tecFROZEN` for an `IOU` and `tecLOCKED` for an `MPT`. For an `MPT`, "frozen" means locked, and "deep frozen" is the same as locked.

### 3.1 Transaction: `VaultDeposit`

#### 3.1.1 Fields

No fields are added or removed.

#### 3.1.2 Failure Conditions

This replaces the freeze checks of parent [§3.5.2.2](../README.md#3522-protocol-level-failures):

- `SingleAssetVault`:
  1. `Vault.Asset` is frozen for the depositor, including a global freeze or lock. (`tecFROZEN` / `tecLOCKED`)
  2. The vault shares are frozen for the depositor. (`tecLOCKED`)
- `fixCleanup3_3_0`, checked in order:
  1. `Vault.Asset` is globally frozen or locked.
  2. The depositor is individually frozen for `Vault.Asset`, unless the depositor is its issuer.
  3. The Vault pseudo-account is individually frozen for `Vault.Asset`.

  The vault shares are not checked.

### 3.2 Transaction: `VaultWithdraw`

#### 3.2.1 Fields

No fields are added or removed.

#### 3.2.2 Failure Conditions

This replaces the freeze checks of parent [§3.6.2.2](../README.md#3622-protocol-level-failures). "Destination" is `Destination` if present, otherwise the submitter.

- `SingleAssetVault`:
  1. `Vault.Asset` is frozen for the destination, including a global freeze or lock. (`tecFROZEN` / `tecLOCKED`)
  2. The vault shares are frozen for the submitter. (`tecLOCKED`)
- `fixCleanup3_3_0`: if the destination is the issuer of `Vault.Asset`, the checks pass. Otherwise, in order:
  1. `Vault.Asset` is globally frozen or locked.
  2. The Vault pseudo-account is individually frozen for `Vault.Asset`.
  3. The submitter is individually frozen for `Vault.Asset`. This check is skipped when the destination is the submitter.
  4. The destination is deep frozen for `Vault.Asset`.

  The vault shares are not checked.

#### 3.2.3 State Changes

When `VaultWithdraw` reads the submitter's share balance to check it covers $\Delta_{share}$:

- `SingleAssetVault`: a frozen share balance reads as zero, and the check fails with `tecINSUFFICIENT_FUNDS`.
- `fixCleanup3_3_0`: the balance is read ignoring freeze. The preclaim checks above have already decided whether a freeze blocks the withdrawal.

## 4. Rationale

Vault shares are issued by the Vault pseudo-account, which cannot submit a transaction to lock a holder's shares. Shares become frozen only through the underlying asset. Checking the asset on each account it passes through covers that case directly, so a separate share check is redundant.

Withdrawals to the issuer always pass because they return the asset to its issuer, which is the path a frozen holder is expected to use. A deep freeze still blocks receipt, as it does elsewhere on the ledger.

## 5. Security Considerations

Refusing deposits into a frozen pseudo-account holding stops funds entering a Vault from which they could not be withdrawn.

Allowing a self-withdrawal under a regular freeze lets a holder recover their own funds. The asset stays frozen in the holder's account, so the freeze still prevents it being sent to others. A deep freeze on the destination still blocks the withdrawal.
