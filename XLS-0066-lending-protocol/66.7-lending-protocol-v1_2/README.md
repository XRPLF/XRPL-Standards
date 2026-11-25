<pre>
  xls: 66.7
  title: LendingProtocolV1_2 Loan Changes
  description: Index of Lending Protocol changes introduced by the LendingProtocolV1_2 amendment
  author: Vytautas Vito Tumas <vtumas@ripple.com>
  proposal-from: https://github.com/XRPLF/XRPL-Standards/discussions/190
  status: Draft
  category: Amendment
  created: 2026-11-25
  updated: 2026-11-25
</pre>

# 66.7 LendingProtocolV1_2 Loan Changes

## 1. Abstract

This index groups Lending Protocol changes introduced by the `LendingProtocolV1_2` amendment. The Vault changes of the same amendment are specified in [XLS-65.7.1](../../XLS-0065-single-asset-vault/65.7-lending-protocol-v1_2/65.7.1-fixed-precision.md).

A Vault receives the fixed-precision `LEVersion` only if `LendingProtocolV1_1`, `LendingProtocolV1_2` and `fixCleanup3_4_0` are all enabled when it is created.

## 2. Specifications

| Spec                                                                              | Description                                                                                                                                           |
| --------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------- |
| [66.7.1 Fixed-Precision Loans](./66.7.1-fixed-precision-loans.md)                 | Keeps `LoanBroker` and `Loan` amounts on the fixed precision grid of a Vault with `LEVersion` 2, and bounds new Loans and cover deposits by capacity. |
| [66.7.2 Private Loan Broker](./66.7.2-private-loan-broker.md)                     | Adds a private `LoanBroker` that only lends to members of a Permissioned Domain.                                                                      |
| [66.7.3 Lending Transactions in Batch](./66.7.3-lending-transactions-in-batch.md) | Allows the nine Lending Protocol transactions as `Batch` inner transactions.                                                                          |

## 3. Rationale

The amendment covers independent Lending Protocol changes. Keeping each change in a focused specification makes its behavior and motivation explicit while this index records their shared amendment.

## 4. Security Considerations

This index introduces no additional protocol behavior. The security considerations for each change are documented in its linked specification.
