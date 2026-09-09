<pre>
  xls: 65.1
  title: Vault Deletion Memo
  description: Introduces an optional MemoData field on VaultDelete for recording why a Vault was deleted
  author: Vytautas Vito Tumas <vtumas@ripple.com>
  proposal-from: https://github.com/XRPLF/XRPL-Standards/discussions/192
  status: Draft
  category: Amendment
  created: 2026-09-04
  updated: 2026-09-09
</pre>

# Vault Deletion Memo

## 1. Abstract

Under the `LendingProtocolV1_1` amendment, `VaultDelete` accepts an optional `MemoData` field in which the Owner of the Vault can record why the Vault was deleted. When present, the decoded value must be 1 to 256 bytes; omitting the field is valid, and including it empty is not. The field is opaque to the protocol and is not written to any ledger entry, because the Vault it describes ceases to exist in the same transaction.

## 2. Motivation

**Vault Deletion Memo.** Deleting a Vault removes the ledger entry, so nothing survives on the ledger to say why it was deleted. A depositor or an auditor reconstructing the history of a Vault can see that it ended, but not whether it was wound down as planned, closed because it never attracted deposits, or retired in favour of a replacement.

`MemoData` gives that statement a defined place in the transaction that deletes the Vault, so it is discoverable from the transaction history of the Vault rather than from an out-of-band announcement.

## 3. Specification

### 3.1 Transaction: `VaultDelete`

#### 3.1.1 Fields

`VaultDelete` accepts one additional field:

| Field Name | Required? | JSON Type | Internal Type | Default Value | Description                                                                                                                                 |
| ---------- | :-------: | :-------: | :-----------: | :-----------: | :------------------------------------------------------------------------------------------------------------------------------------------ |
| `MemoData` |    No     | `string`  |    `BLOB`     |     `N/A`     | Optional opaque deletion reason, encoded as hexadecimal. If present, the decoded value must be 1–256 bytes. Omitted is valid; empty is not. |

The field is not interpreted by the protocol and is not written to any ledger entry.

#### 3.1.2 Failure Conditions

##### 3.1.2.1 Data Verification

Parent check 1 is unchanged. The following checks are added:

2. `MemoData` is present and empty. (`temMALFORMED`)
3. `MemoData` is longer than 256 bytes. (`temMALFORMED`)

When the amendment is not enabled, `MemoData` is not accepted on `VaultDelete` and its presence fails with `temDISABLED`.

##### 3.1.2.2 Protocol-Level Failures

Unchanged.

#### 3.1.3 State Changes

Unchanged. `MemoData` remains in the transaction record and is not written to a ledger entry or copied into transaction metadata.

#### 3.1.4 Example JSON

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

**Vault Deletion Memo.** The standard transaction-level `Memos` array can already carry an opaque deletion reason. A dedicated top-level `MemoData` field was chosen to give this reason one predictable location and one value with a deletion-specific 256-byte bound, without requiring applications to agree on a `MemoType` convention. It reuses the existing `MemoData` serialized field rather than introducing a new field name.

A structured field, such as an enumerated reason code, was rejected: the protocol cannot verify any such code, and an enumeration fixed now would not survive contact with reasons nobody has thought of yet.

The 256-byte limit is the protocol's common maximum data-payload length and keeps the serialized transaction size bounded. Present empty is rejected: if `MemoData` is included, its decoded value must contain 1–256 bytes.

## 5. Security Considerations

**Vault Deletion Memo.** `MemoData` is unauthenticated free text written by the Owner of the Vault. It is a claim about the deletion, not evidence of one, and a consumer should not treat it as a statement that any party other than the Owner endorses.

The contents are public and permanent. An Owner should not put anything in the field that they would not publish, and in particular should not use it for information about depositors.
