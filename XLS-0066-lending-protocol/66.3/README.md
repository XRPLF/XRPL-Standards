<pre>
  xls: 66.3
  title: LendingProtocolV1_2 Loan Changes
  description: Index of Lending Protocol changes introduced by the LendingProtocolV1_2 amendment
  author: Vytautas Vito Tumas <vtumas@ripple.com>
  proposal-from: https://github.com/XRPLF/XRPL-Standards/discussions/190
  status: Draft
  category: Amendment
  created: 2026-10-01
  updated: 2026-11-24
</pre>

# 66.3 LendingProtocolV1_2 Loan Changes

## 1. Abstract

This index groups the Lending Protocol changes introduced by the `LendingProtocolV1_2` amendment.

## 2. Specifications

These specifications are introduced by the `LendingProtocolV1_2` amendment:

| Spec                                                                      | Description                                                                                    |
| ------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------- |
| [66.3.1 Two-Step Loan Creation](./66.3.1-two-step-loan-creation.md)       | Adds a propose-and-accept Loan flow through `LoanSet` and a new `LoanAccept` transaction.      |
| [66.3.2 Conditional LoanBroker VaultID](./66.3.2-conditional-vault-id.md) | Requires `VaultID` on `LoanBrokerSet` creation and forbids it on modification.                 |
| [66.3.3 Private LoanBroker](./66.3.3-private-loan-broker.md)              | Restricts Loan origination to Borrowers holding credentials accepted by a Permissioned Domain. |

## 3. Rationale

Every change in `LendingProtocolV1_2` concerns how a Loan is originated: how a `LoanBroker` is set up (66.3.2), who may borrow from it (66.3.3), and how the `LoanBroker.Owner` and the Borrower agree on terms (66.3.1). None of them changes Loan accounting, payments, impairment, or default. Grouping them under one amendment activates the origination changes together, and leaves Loans created under earlier amendments unaffected.

The changes are otherwise independent of each other. Keeping each change in a focused specification makes its behavior and motivation explicit while this index records their shared amendment.

## 4. Security Considerations

This index introduces no additional protocol behavior. The security considerations for each change are documented in its linked specification.
