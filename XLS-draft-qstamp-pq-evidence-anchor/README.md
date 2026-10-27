<pre>
  title: Qstamp Post Quantum Evidence Anchor Memo
  description: Anchors a salted commitment to an off ledger record in a transaction Memo so its integrity can be proven later
  author: Quantova Inc <Quantovaorg@gmail.com>
  category: Ecosystem
  status: Draft
  proposal-from: https://github.com/XRPLF/XRPL-Standards/discussions/663
  created: 2026-10-16
  updated: 2026-10-16
</pre>

# XLS-draft: Qstamp Post Quantum Evidence Anchor Memo

## Abstract

This standard fixes one Memo convention for anchoring a commitment to an off ledger record on the XRP Ledger. The sender computes a salted SHA3-256 fingerprint of the record, binds it under KECCAK-256 to the sending account and a declared record kind, and writes the resulting 32 byte commitment into a Memo on any validated transaction. A verifier who later holds the record, the salt, the account and the kind recomputes the commitment and matches it against the ledger. The record never reaches the ledger, and no amendment is required.

## 1. Motivation

Payment firms, banks and operators of AI agents must keep records for years and show that each one existed unaltered at a known time. The XRP Ledger already carries Memos on every transaction type, so an integrity anchor can be written today. Without a shared convention each issuer encodes its anchor differently, and wallets, explorers and auditors cannot recognise or verify them uniformly. The commitment is built only from hash functions, so it remains sound against a future quantum adversary for as long as the records must be retained.

## 2. Specification

### 2.1. Commitment

For a record `R`, a 16 byte random salt `s`, the classic address `A` of the sending account and a record kind `K`

```
fingerprint = SHA3-256(s || R)
commitment  = KECCAK-256(fingerprint || utf8(A) || 0x00 || utf8(K))
```

`||` is byte concatenation. `utf8(A)` is the classic address string, for example `rPT1Sjq2YGrBMTttX4GZHjKu9dyfzbpAYe`. The single `0x00` byte separates the address from the kind. `K` is a short ASCII label chosen by the issuer, for example `qstamp` or `payment_record`. A fresh salt MUST be drawn for every record from a cryptographically secure generator. The salt and the record MUST NOT be written to the ledger.

### 2.2. Memo

The commitment is written as one Memo in the `Memos` array of any transaction sent by `A`.

| Field        | Value                                                   |
| ------------ | ------------------------------------------------------- |
| `MemoType`   | hex of the ASCII string `qstamp/pq-evidence/1`          |
| `MemoData`   | the 32 byte commitment, as 64 uppercase hex characters  |
| `MemoFormat` | hex of the ASCII string `application/vnd.qstamp.anchor` |

A transaction MAY carry other Memos alongside this one.

### 2.3. Reading

A reader identifies an anchor by decoding `MemoType` and comparing it with `qstamp/pq-evidence/1`. A Memo with that type whose `MemoData` does not decode to exactly 32 bytes MUST be ignored.

### 2.4. Verification

A verifier holding `R`, `s`, `A` and `K` recomputes the commitment as in 2.1 and checks that a validated transaction sent by `A` carries a Memo of the type in 2.2 whose `MemoData` equals the commitment. The ledger close time of that transaction is the latest time at which the record is proven to have existed in that exact form.

## 3. Rationale

Binding the fingerprint to the sending account means the same record anchored by two accounts yields two distinct commitments, so one account cannot present another account's anchor as its own. The record kind lets one account anchor several classes of record without ambiguity. The salt prevents anyone who reads the ledger from confirming a guess about a short or predictable record. SHA3-256 and KECCAK-256 each keep about 128 bits of security against Grover search, which is why the construction uses no signature or elliptic curve primitive of its own. Memos were chosen over a new ledger entry so that the standard needs no amendment and works on every network today.

## 4. Backwards Compatibility

This standard uses only existing transaction fields and introduces no protocol change. Transactions that carry other Memos are unaffected.

## 5. Test Plan

The reference adapter tests check that a commitment round trips through a Memo, that every Memo field is uppercase hex, that two accounts anchoring the same record produce different commitments, that a Memo of a different type is ignored, and that a commitment of the wrong length is refused.

## 6. Reference Implementation

A TypeScript adapter that builds the commitment and the Memo and reads it back, with the tests above, is published at https://github.com/quantova-inc/xrpl-pq-tooling under Apache 2.0 or MIT.

## 7. Security Considerations

The anchor proves that a record existed unaltered no later than the close time of the anchoring ledger. It does not prove that the record is true or correct, that it did not exist earlier, or that the sender had authority to create it. The sender is identified only by its account, and linking an account to an organisation is a separate attestation. The salt must be stored with the record, because without it the commitment cannot be recomputed, and anyone holding both the salt and the commitment can test guesses about a low entropy record, so the salt deserves the same protection as the record itself. The time evidence ultimately rests on the integrity of the validated ledger history that contains the anchoring transaction.
