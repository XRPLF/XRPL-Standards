<pre>
  xls: 66.3
  title: LendingProtocolV1_2 Loan Changes
  description: Index of Lending Protocol changes introduced by the LendingProtocolV1_2 amendment
  author: Denis Angell (@dangell7)
  proposal-from: https://github.com/XRPLF/XRPL-Standards/discussions/190
  status: Draft
  category: Amendment
  created: 2026-11-03
  updated: 2026-11-03
</pre>

# 66.3 LendingProtocolV1_2 Loan Changes

## 1. Abstract

This index groups the Lending Protocol changes introduced by the `LendingProtocolV1_2` amendment.

## 2. Specifications

These specifications are introduced by the `LendingProtocolV1_2` amendment:

| Spec                                      | Description                                                      |
| ----------------------------------------- | ---------------------------------------------------------------- |
| [66.3.4 Loan Data](./66.3.4-loan-data.md) | Stores the `Data` field of `LoanSet` on the `Loan` ledger entry. |

## 3. Rationale

The amendment covers independent Lending Protocol changes. Keeping each change in a focused specification makes its behavior and motivation explicit while this index records their shared amendment.

## 4. Security Considerations

This index introduces no additional protocol behavior. The security considerations for each change are documented in its linked specification.
