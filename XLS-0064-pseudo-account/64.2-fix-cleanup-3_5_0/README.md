<pre>
  xls: 64.2
  title: Pseudo-Account Owned Entries
  description: Restricts the entries a pseudo-account may own to those of its own AMM, Vault or LoanBroker
  author: Vytautas Vito Tumas <vtumas@ripple.com>
  proposal-from: https://github.com/XRPLF/XRPL-Standards/discussions/191
  status: Draft
  category: Amendment
  created: 2026-11-25
  updated: 2026-11-25
</pre>

# Pseudo-Account Owned Entries

## 1. Abstract

Under the `fixCleanup3_5_0` amendment, a new invariant limits what a _pseudo-account_ may own. Every ledger entry that a transaction links into a pseudo-account's owner directory must belong to the AMM, Vault or LoanBroker that the pseudo-account was created for. A transaction that links any other entry fails the invariant.

This patch changes the parent [XLS-64](../README.md) Invariants section only. All other parent behavior is unchanged.

## 2. Motivation

A pseudo-account cannot sign transactions. An entry linked into its owner directory can therefore be removed only by the protocol that owns the pseudo-account. If a transaction links any other entry, such as a trust line or an offer that the protocol does not manage, nothing can ever remove it. The entry pins the owner directory, and the AMM, Vault or LoanBroker that owns the pseudo-account can no longer be deleted.

## 3. Specification

### 3.1. Ledger Entry: `AccountRoot`

#### 3.1.1. Invariants

When the amendment is enabled, the following invariant is added to the parent Invariants section. It is checked for every transaction.

For each entry that the transaction adds to the owner directory of an `AccountRoot` that is a _pseudo-account_, the entry must be one that the specification of the pseudo-account's owning object allows it to own. Entries already in the directory before the transaction are not checked. A pseudo-account kind whose specification lists no owned entries may own none.

Each specification lists its entries under `fixCleanup3_5_0`:

| Pseudo-account field | Owned entries specified in                                                          |
| :------------------- | :---------------------------------------------------------------------------------- |
| `AMMID`              | [XLS-30.1](../../XLS-0030-automated-market-maker/30.1-fix-cleanup-3_5_0/README.md)  |
| `VaultID`            | [XLS-65.6](../../XLS-0065-single-asset-vault/65.6-fix-cleanup-3_5_0/README.md) §3.5 |
| `LoanBrokerID`       | [XLS-66.6](../../XLS-0066-lending-protocol/66.6-fix-cleanup-3_5_0/README.md) §3.4   |

A _holding_ is the `RippleState` (for an IOU) or the `MPToken` (for an MPT) through which the pseudo-account holds the asset. XRP has no holding entry.

The invariant also fails if the directory links an entry that does not exist.

When the amendment is not enabled, the entries a pseudo-account owns are not checked.

## 4. Rationale

The invariant checks only entries added by the transaction. That makes the check cost proportional to the transaction's own changes, not to the size of the directory, and it leaves entries created before activation untouched.

The owned entries are listed in each owning object's specification rather than here, so that a later change to what an AMM, Vault or LoanBroker holds, such as a new holding type, changes only that specification.

## 5. Backwards Compatibility

The amendment adds an invariant and changes no transaction. A transaction that previously succeeded by linking a foreign entry into a pseudo-account's owner directory fails the invariant once the amendment is enabled. Entries linked before activation are not affected.

## 6. Security Considerations

Without this invariant, any path that links a foreign entry into a pseudo-account's directory would leave an entry that no account can remove, and would block deletion of the AMM, Vault or LoanBroker. The invariant turns any such path into a failed transaction instead of permanent ledger state.
