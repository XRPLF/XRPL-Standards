<pre>
  xls: 30.1
  title: AMM Pseudo-Account Owned Entries
  description: Lists the entries an AMM pseudo-account may own under the XLS-64.2 ownership invariant
  author: Vytautas Vito Tumas <vtumas@ripple.com>
  proposal-from: https://github.com/XRPLF/XRPL-Standards/discussions/78
  status: Draft
  category: Amendment
  created: 2026-11-25
  updated: 2026-11-25
</pre>

# 30.1 AMM Pseudo-Account Owned Entries

## 1. Abstract

Under the `fixCleanup3_5_0` amendment, [XLS-64.2](../../XLS-0064-pseudo-account/64.2-fix-cleanup-3_5_0/README.md) requires every entry a transaction adds to a _pseudo-account_'s owner directory to be one that the owning object's specification allows. This patch lists the entries an AMM _pseudo-account_ may own.

This patch changes the parent [XLS-30](../README.md) `AccountRoot` ledger entry only. All other parent behavior is unchanged.

## 2. Motivation

An AMM _pseudo-account_ cannot sign transactions, so an entry linked into its owner directory that the AMM does not manage could never be removed, and would block deletion of the AMM. Listing the entries the AMM manages lets the invariant reject any other entry.

## 3. Specification

### 3.1. Ledger Entry: `AccountRoot`

#### 3.1.1. Invariants

When the amendment is enabled, the AMM _pseudo-account_ (the `AccountRoot` with `AMMID`) may own only:

- the `AMM` entry identified by `AMMID`;
- its holding of `AMM.Asset` or `AMM.Asset2`: the `RippleState` for an IOU or the `MPToken` for an MPT. XRP has no holding entry;
- a `RippleState` for the AMM's LP token in which the _pseudo-account_ is one side.

When the amendment is not enabled, the entries the AMM _pseudo-account_ owns are not checked.

## 4. Rationale

These are the entries that `AMMCreate`, `AMMDeposit`, `AMMWithdraw` and `AMMDelete` create and remove. Liquidity providers' LP token trust lines are linked into the AMM _pseudo-account_'s directory because it issues the LP token.

## 5. Security Considerations

The list must include every entry the AMM transactions link into the _pseudo-account_'s directory. An entry missing from it would make a valid AMM transaction fail the invariant.
