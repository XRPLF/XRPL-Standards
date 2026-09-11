<pre>
  xls: 65.1
  title: Vault Immutability and Deletion Memo
  description: Makes identity and configuration fields immutable on the Vault once set, and adds an optional MemoData field on VaultDelete
  author: Vytautas Vito Tumas <vtumas@ripple.com>
  proposal-from: https://github.com/XRPLF/XRPL-Standards/discussions/192
  status: Draft
  category: Amendment
  created: 2026-09-04
  updated: 2026-09-11
</pre>

# Vault Immutability and Deletion Memo

## 1. Abstract

Under the `LendingProtocolV1_1` amendment, `Sequence`, `OwnerNode`, `Owner`, `WithdrawalPolicy`, `Scale` and `LEVersion` are immutable on a `Vault` once set, in addition to `Asset`, `Account` and `ShareMPTID`. The same amendment also lets `VaultDelete` accept an optional `MemoData` field in which the Owner of the Vault can record why the Vault was deleted. When present, the decoded value must be 1 to 256 bytes; omitting the field is valid, and including it empty is not. The field is opaque to the protocol and is not written to any ledger entry, because the Vault it describes ceases to exist in the same transaction.

## 2. Motivation

The version field determines how the Vault values its shares. Changing `LEVersion` after creation would reprice every share in issue.

The identity and configuration fields are in the same position. `Sequence` and `OwnerNode` locate the entry and its directory page, `Owner` names the account that controls it, and `WithdrawalPolicy` and `Scale` fix how shares are redeemed and how finely the asset is denominated. None of them has a legitimate reason to change after creation.

Stating this as a ledger invariant means it holds for every transaction that touches the entry.

Deleting a Vault removes the ledger entry, so nothing survives on the ledger to say why it was deleted. A depositor or an auditor reconstructing the history of a Vault can see that it ended, but not whether it was wound down as planned, closed because it never attracted deposits, or retired in favour of a replacement.

`MemoData` gives that statement a defined place in the transaction that deletes the Vault, so it is discoverable from the transaction history of the Vault rather than from an out-of-band announcement.

## 3. Specification

### 3.1 Ledger Entry: `Vault`

#### 3.1.1 Invariants

Before the amendment: `Vault.Asset == Vault'.Asset`, `Vault.Account == Vault'.Account`, and `Vault.ShareMPTID == Vault'.ShareMPTID`.

When the amendment is enabled: `Vault.Sequence == Vault'.Sequence`, `Vault.OwnerNode == Vault'.OwnerNode`, `Vault.Owner == Vault'.Owner`, `Vault.WithdrawalPolicy == Vault'.WithdrawalPolicy`, `Vault.Scale == Vault'.Scale`, `Vault.Asset == Vault'.Asset`, `Vault.Account == Vault'.Account`, and `Vault.ShareMPTID == Vault'.ShareMPTID`. If `Vault.LEVersion` is present, `Vault.LEVersion == Vault'.LEVersion`; if it is absent, it remains absent, except when the transaction creates the entry.

#### 3.1.2 Example JSON

```json
{
  "LedgerEntryType": "Vault",
  "Sequence": 5,
  "OwnerNode": "0",
  "Owner": "rwhaYGnJMexktjhxAKzRwoCcQ2g6hvBDWu",
  "WithdrawalPolicy": 1,
  "Scale": 6,
  "LEVersion": 1,
  "Asset": {
    "currency": "USD",
    "issuer": "rf1BiGeXwwQoi8Z2ueFYTEXSwuJYfV2Jpn"
  },
  "Account": "rHXuEaRYnnJHbDeuBH5w8yPh5uwNVh5zAg",
  "ShareMPTID": "00000001C752C42A1EBD6BF2403134F7CFD2F1D835AFD26E"
}
```

### 3.2 Transaction: `VaultDelete`

#### 3.2.1 Fields

`VaultDelete` accepts one additional field:

| Field Name | Required? | JSON Type | Internal Type | Default Value | Description                                                                                                                                 |
| ---------- | :-------: | :-------: | :-----------: | :-----------: | :------------------------------------------------------------------------------------------------------------------------------------------ |
| `MemoData` |    No     | `string`  |    `BLOB`     |     `N/A`     | Optional opaque deletion reason, encoded as hexadecimal. If present, the decoded value must be 1–256 bytes. Omitted is valid; empty is not. |

The field is not interpreted by the protocol and is not written to any ledger entry.

#### 3.2.2 Failure Conditions

##### 3.2.2.1 Data Verification

Parent check 1 is unchanged. The following checks are added:

2. `MemoData` is present and empty. (`temMALFORMED`)
3. `MemoData` is longer than 256 bytes. (`temMALFORMED`)

When the amendment is not enabled, `MemoData` is not accepted on `VaultDelete` and its presence fails with `temDISABLED`.

##### 3.2.2.2 Protocol-Level Failures

Unchanged.

#### 3.2.3 State Changes

Unchanged. `MemoData` remains in the transaction record and is not written to a ledger entry or copied into transaction metadata.

#### 3.2.4 Example JSON

```json
{
  "TransactionType": "VaultDelete",
  "Account": "rf1BiGeXwwQoi8Z2ueFYTEXSwuJYfV2Jpn",
  "Fee": "10",
  "Sequence": 12345,
  "VaultID": "9CD5F03A9D0F4F7C0B8B4C5F5A4D3E2B1A0F9E8D7C6B5A493827160504030201",
  "MemoData": "77696E642D646F776E20636F6D706C65746564"
}
```

## 4. Rationale

Treating these fields as immutable rather than mutable-with-conditions avoids introducing transaction-specific exceptions into a ledger-wide invariant.

The standard transaction-level `Memos` array can already carry an opaque deletion reason. A dedicated top-level `MemoData` field was chosen to give this reason one predictable location and one value with a deletion-specific 256-byte bound, without requiring applications to agree on a `MemoType` convention. It reuses the existing `MemoData` serialized field rather than introducing a new field name.

A structured field, such as an enumerated reason code, was rejected: the protocol cannot verify any such code, and an enumeration fixed now would not survive contact with reasons nobody has thought of yet.

The 256-byte limit is the protocol's common maximum data-payload length and keeps the serialized transaction size bounded. Present empty is rejected: if `MemoData` is included, its decoded value must contain 1–256 bytes.

## 5. Security Considerations

The invariant is what allows a reader to cache the version and denomination of a Vault. Without it, every consumer would have to re-read the entry before valuing shares.

A field added to the `Vault` later is mutable unless it is included in this set.

`MemoData` is unauthenticated free text written by the Owner of the Vault. It is a claim about the deletion, not evidence of one, and a consumer should not treat it as a statement that any party other than the Owner endorses.

The contents are public and permanent. An Owner should not put anything in the field that they would not publish, and in particular should not use it for information about depositors.
