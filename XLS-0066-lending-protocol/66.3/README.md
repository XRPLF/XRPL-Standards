<pre>
  xls: 66.3
  title: LendingProtocolV1_2 Loan Changes
  description: Index of Lending Protocol changes introduced by the LendingProtocolV1_2 amendment
  author: Vytautas Vito Tumas <vtumas@ripple.com>
  proposal-from: https://github.com/XRPLF/XRPL-Standards/discussions/190
  status: Draft
  category: Amendment
  created: 2026-10-01
  updated: 2026-10-01
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

The amendment covers independent Lending Protocol changes. Keeping each change in a focused specification makes its behavior and motivation explicit while this index records their shared amendment.

## 4. Security Considerations

This index introduces no additional protocol behavior. The security considerations for each change are documented in its linked specification.
