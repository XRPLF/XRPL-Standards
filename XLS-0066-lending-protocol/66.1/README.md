<pre>
  xls: 66.1
  title: LendingProtocolV1_1 Loan Changes
  description: Index of Lending Protocol changes introduced by the LendingProtocolV1_1 amendment
  author: Jingchen Wu (@a1q123456), Vito Tumas (@Tapanito), Gregory Tsipenyuk (@gtsipenyuk)
  proposal-from: https://github.com/XRPLF/XRPL-Standards/discussions/590
  status: Draft
  category: Amendment
  created: 2026-07-21
  updated: 2026-09-15
</pre>

# 66.1 LendingProtocolV1_1 Loan Changes

## 1. Abstract

This index groups Lending Protocol changes introduced by the `LendingProtocolV1_1` amendment.

## 2. Specifications

| Spec                                                                  | Description                                                                          |
| --------------------------------------------------------------------- | ------------------------------------------------------------------------------------ |
| [66.1.2 Closed-Ended Loan Gates](./66.1.2-closed-ended-loan-gates.md) | Restricts loan origination and broker creation for the closed-ended Vault lifecycle. |

The `66.1.1` number is reserved for the cash-basis lending patch and is not defined in this tree.

## 3. Rationale

The amendment covers independent Lending Protocol changes. Keeping each change in a focused specification makes its behavior and motivation explicit while this index records their shared amendment.

## 4. Security Considerations

This index introduces no additional protocol behavior. The security considerations for each change are documented in its linked specification.
