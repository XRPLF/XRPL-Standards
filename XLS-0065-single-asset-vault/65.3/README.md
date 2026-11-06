<pre>
  xls: 65.3
  title: LendingProtocolV1_2 Vault Changes
  description: Index of Vault changes introduced by the LendingProtocolV1_2 amendment
  author: Vytautas Vito Tumas <vtumas@ripple.com>
  proposal-from: https://github.com/XRPLF/XRPL-Standards/discussions/192
  status: Draft
  category: Amendment
  created: 2026-10-01
  updated: 2026-10-01
</pre>

# 65.3 LendingProtocolV1_2 Vault Changes

## 1. Abstract

This index groups the Vault changes introduced by the `LendingProtocolV1_2` amendment.

## 2. Specifications

These specifications are introduced by the `LendingProtocolV1_2` amendment:

| Spec                                                                   | Description                                                                                   |
| ---------------------------------------------------------------------- | --------------------------------------------------------------------------------------------- |
| [65.3.1 Fixed Precision](./65.3.1-fixed-precision.md)                  | Fixes one precision grid per Vault for the life of the Vault, its LoanBrokers, and its Loans. |
| [65.3.2 Closed-Ended Vault Early-Exit Fee](./65.3.2-early-exit-fee.md) | Adds an optional immutable `EarlyExitFeeRate` that allows fee-bearing Investment-phase exits. |
| [65.3.3 Vault Assets Reserved](./65.3.3-vault-assets-reserved.md)      | Adds `Vault.AssetsReserved` to track assets reserved for pending Loans.                       |
| [65.3.4 Vault Deposit Block](./65.3.4-vault-deposit-block.md)          | Lets an opted-in Vault Owner block and unblock deposits.                                      |

## 3. Rationale

The amendment covers independent Vault changes. Keeping each change in a focused specification makes its behavior and motivation explicit while this index records their shared amendment.

## 4. Security Considerations

This index introduces no additional protocol behavior. The security considerations for each change are documented in its linked specification.
