<pre>
  xls: 65.1
  title: LendingProtocolV1_1 Vault Changes
  description: Index of Vault changes introduced by the LendingProtocolV1_1 amendment
  author: Vytautas Vito Tumas <vtumas@ripple.com>
  proposal-from: https://github.com/XRPLF/XRPL-Standards/discussions/192
  status: Draft
  category: Amendment
  created: 2026-09-04
  updated: 2026-09-11
</pre>

# LendingProtocolV1_1 Vault Changes

## 1. Abstract

This index groups the Vault changes introduced by the `LendingProtocolV1_1` amendment.

## 2. Specifications

These specifications are introduced by the `LendingProtocolV1_1` amendment:

| Spec                                               | Description                                                                                                          |
| -------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------- |
| [Unmodifiable Vault Fields](./vault-invariants.md) | Makes `Sequence`, `OwnerNode`, `Owner`, `WithdrawalPolicy`, `Scale` and `LEVersion` immutable on the Vault once set. |
| [Vault Deletion Memo](./vault-memo.md)             | Adds an optional `MemoData` field to `VaultDelete` that, if present, must be 1–256 bytes.                            |

## 3. Rationale

The amendment covers independent Vault changes. Keeping each change in a focused specification makes its behavior and motivation explicit while this index records their shared amendment.

## 4. Security Considerations

This index introduces no additional protocol behavior. The security considerations for each change are documented in its linked specification.
