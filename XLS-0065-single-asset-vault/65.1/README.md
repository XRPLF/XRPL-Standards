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

These specifications are introduced by the `LendingProtocolV1_1` amendment:

| Spec                                               | Description                                                                                                          |
| -------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------- |
| [Unmodifiable Vault Fields](./vault-invariants.md) | Makes `Sequence`, `OwnerNode`, `Owner`, `WithdrawalPolicy`, `Scale` and `LEVersion` immutable on the Vault once set. |
| [Vault Deletion Memo](./vault-memo.md)             | Adds an optional `MemoData` field to `VaultDelete` that, if present, must be 1–256 bytes.                            |
