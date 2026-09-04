<pre>
  xls: 65.1
  title: Vault Deletion Memo
  description: Adds an optional MemoData field to VaultDelete, recording why a Vault was deleted
  author: Vytautas Vito Tumas <vtumas@ripple.com>, Aanchal Malhotra <amalhotra@ripple.com>
  proposal-from: https://github.com/XRPLF/XRPL-Standards/discussions/192
  status: Draft
  category: Amendment
  requires: [XLS-65](../README.md)
  created: 2026-09-04
  updated: 2026-09-04
</pre>

# Vault Deletion Memo

## 1. Abstract

This patch of [XLS-65](../README.md) records the change the `LendingProtocolV1_1` amendment makes to the `VaultDelete` transaction. The transaction gains an optional `MemoData` field that, if present, must be 1–256 bytes, in which the Owner of the Vault can record a reason for the deletion. The field is rejected while the amendment is disabled.

The consolidated specification is the top-level [README.md](../README.md).

## 2. Motivation

Deleting a Vault removes the ledger entry, so nothing survives on the ledger to say why it was deleted. A depositor or an auditor reconstructing the history of a Vault can see that it ended, but not whether it was wound down as planned, closed because it never attracted deposits, or retired in favour of a replacement.

`MemoData` gives that statement a defined place in the transaction that deletes the Vault, so it is discoverable from the transaction history of the Vault rather than from an out-of-band announcement.

## 3. Transaction: `VaultDelete`

### 3.1. Fields

| Field Name | Required? | JSON Type | Internal Type | Default Value | Description                                                                                       |
| ---------- | :-------: | :-------: | :-----------: | :-----------: | :------------------------------------------------------------------------------------------------ |
| `MemoData` |    No     | `string`  |    `BLOB`     |     `N/A`     | Optional opaque deletion reason. If present, must be 1–256 bytes. Omitted is valid; empty is not. |

The field is not interpreted by the protocol and is not written to any ledger entry; the Vault it describes ceases to exist in the same transaction.

### 3.2. Failure Conditions

#### 3.2.1. Data Verification

1. `MemoData` is present and the `LendingProtocolV1_1` amendment is not enabled. (`temDISABLED`)
2. `MemoData` is present and empty. (`temMALFORMED`)
3. `MemoData` is longer than 256 bytes. (`temMALFORMED`)

#### 3.2.2. Protocol-Level Failures

Unchanged.

### 3.3. State Changes

Unchanged. `MemoData` appears in the transaction and its metadata only.

### 3.4. Example JSON

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

The field is named `MemoData` to match the existing `Memos` field of a transaction, whose contents are likewise opaque to the protocol. A structured field, such as an enumerated reason code, was rejected: the protocol cannot verify any such code, and an enumeration fixed now would not survive contact with reasons nobody has thought of yet.

The 256-byte limit matches the limit on comparable arbitrary-data fields and keeps the cost of the field bounded, since it is charged at the standard transaction fee. Present empty is rejected: if `MemoData` is included, it must contain 1–256 bytes.

## 5. Security Considerations

`MemoData` is unauthenticated free text written by the Owner of the Vault. It is a claim about the deletion, not evidence of one, and a consumer should not treat it as a statement that any party other than the Owner endorses.

The contents are public and permanent. An Owner should not put anything in the field that they would not publish, and in particular should not use it for information about depositors.
