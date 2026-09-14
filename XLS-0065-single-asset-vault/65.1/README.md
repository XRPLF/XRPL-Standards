<pre>
  xls: 65.1
  title: LendingProtocolV1_1 Vault Changes
  description: Index of Vault changes introduced by the LendingProtocolV1_1 amendment
  author: Vytautas Vito Tumas <vtumas@ripple.com>
  proposal-from: https://github.com/XRPLF/XRPL-Standards/discussions/192
  status: Draft
  category: Amendment
  created: 2026-09-04
  updated: 2026-09-14
</pre>

# 65.1 LendingProtocolV1_1 Vault Changes

## 1. Abstract

This index groups the Vault changes introduced by the `LendingProtocolV1_1` amendment.

## 2. Specifications

These specifications are introduced by the `LendingProtocolV1_1` amendment:

| Spec                                                                            | Description                                                                                                          |
| ------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------- |
| [65.1.1 Unmodifiable Vault Fields](./65.1.1-unmodifiable-vault-fields.md)       | Makes `Sequence`, `OwnerNode`, `Owner`, `WithdrawalPolicy`, `Scale` and `LEVersion` immutable on the Vault once set. |
| [65.1.2 Vault Deletion Memo](./65.1.2-vault-deletion-memo.md)                   | Adds an optional `MemoData` field to `VaultDelete` that, if present, must be 1–256 bytes.                            |
| [65.1.3 Single Asset Vault Cash-Basis Accounting](./65.1.3-vault-cash-basis.md) | Records the accounting model in `LEVersion` so `AssetsTotal` counts interest only when a Borrower pays it.           |

## 3. Rationale

The amendment covers independent Vault changes. Keeping each change in a focused specification makes its behavior and motivation explicit while this index records their shared amendment.

## 4. Security Considerations

This index introduces no additional protocol behavior. The security considerations for each change are documented in its linked specification.
