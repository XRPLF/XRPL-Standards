<pre>
  xls: 66.6
  title: Lending Protocol Cleanup 3.5.0
  description: Lending Protocol changes of the fixCleanup3_5_0 amendment to value range checks and the LoanBrokerDelete cover payout
  author: Vytautas Vito Tumas <vtumas@ripple.com>
  proposal-from: https://github.com/XRPLF/XRPL-Standards/discussions/190
  status: Draft
  category: Amendment
  created: 2026-11-25
  updated: 2026-11-25
</pre>

# 66.6 Lending Protocol Cleanup 3.5.0

## 1. Abstract

Under the `fixCleanup3_5_0` amendment, `LoanBrokerSet` and `LoanSet` reject value fields outside the range of the Vault asset with `tecPRECISION_LOSS`. `LoanBrokerDelete` checks that the remaining first-loss capital can be paid to the broker owner, frees the broker's owner reserve before the payout, and creates the owner's holding of the asset if it has none.

## 2. Motivation

A value field above the largest amount of the asset (for example, an XRP amount above the maximum number of drops) could not be converted to an amount, and the conversion failed while the transaction was being checked. `LoanBrokerDelete` paid the remaining cover to the owner without the transfer and authorization checks of `LoanBrokerCoverWithdraw`, so an owner that had removed its holding could not delete the broker.

## 3. Specification

No fields are added or removed.

### 3.1 Transaction: `LoanBrokerSet`

#### 3.1.1 Failure Conditions

When the amendment is enabled, parent §3.3.3.2 check 11 also fails if a value field is outside the range of the `Vault.Asset` type. (`tecPRECISION_LOSS`)

### 3.2 Transaction: `LoanSet`

#### 3.2.1 Failure Conditions

When the amendment is enabled, parent §3.8.5.2 check 7 also fails if a value field is outside the range of the `Vault.Asset` type. (`tecPRECISION_LOSS`)

### 3.3 Transaction: `LoanBrokerDelete`

#### 3.3.1 Failure Conditions

Parent §3.4.3.2 check 7: when the amendment is enabled and `LoanBroker.CoverAvailable > 0`, the following run before parent check 5:

- The asset cannot be transferred from the broker _pseudo-account_ to the owner. `lsfMPTCanTransfer` is not checked. (`tecNO_AUTH` for MPTs, `terNO_RIPPLE` for IOUs)
- The owner is not authorized to hold the asset.
- The owner has no holding of the asset, and a holding cannot be added.

When the amendment is not enabled, check 7 does not apply.

#### 3.3.2 State Changes

When the amendment is enabled, parent §3.4.4 changes as follows:

- Step 7 (decrement the owner's `OwnerCount` by 2) runs before step 3.
- Before step 3, if `LoanBroker.CoverAvailable > 0` and the owner has no holding of the asset, a holding is created for the owner. The owner's reserve is checked against its balance before the transaction fee.

When the amendment is not enabled, step 7 runs after the broker _pseudo-account_ is deleted, and no holding is created; a payout of an MPT to an owner without an `MPToken` fails.

### 3.4 Ledger Entry: `LoanBroker`

#### 3.4.1 Pseudo-Account

`fixCleanup3_5_0` also restricts what a `LoanBroker` _pseudo-account_ may own, as specified in [XLS-64.2](../../XLS-0064-pseudo-account/64.2-fix-cleanup-3_5_0/README.md).

## 4. Rationale

Freeing the broker's reserve first lets the reserve cover the new holding. The checks match those of a `LoanBrokerCoverWithdraw` to the owner, so an issuer cannot trap the cover by clearing `lsfMPTCanTransfer`.

## 5. Security Considerations

The range check replaces a failed conversion with a defined result code. The `LoanBrokerDelete` checks only add conditions under which the deletion fails before any state changes.
