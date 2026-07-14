<pre>
  xls: 103
  title: On-Chain Cosigner
  description: Native on-ledger proposal and multi-signature collection for XRPL transactions.
  author: Shota Natenadze
  category: Amendment
  status: Draft
  proposal-from: https://github.com/XRPLF/XRPL-Standards/discussions/TBD
  requires: XLS-49
  created: 2026-07-14
</pre>

# On-Chain Cosigner

## 1. Abstract

The XRP Ledger supports multi-signature transactions, but coordination between signers happens entirely off-chain. A transaction blob must be manually shared with each signer, signatures must be collected and assembled by hand, and a single coordinator must finally submit the fully-signed transaction. This off-chain "last mile" reintroduces the very single point of failure that multi-sign is meant to remove: if the coordinator goes offline, loses the collected signatures, or assembles the wrong transaction, the signing round fails or is compromised.

This proposal introduces **On-Chain Cosigner**: a native mechanism that turns the ledger itself into the "meeting room" where multi-signatures are collected. A proposer posts an unsigned transaction on-ledger as a `TransactionProposal` object. Authorized signers append their signatures to it directly on-chain, one transaction at a time. Each signature is validated as it arrives and appended directly into the proposed transaction's own `Signers` field, so the proposal is always a well-formed transaction-in-progress. Once the accumulated signer weight reaches the account's quorum, the stored transaction is already fully signed: **anyone** can copy it verbatim and submit it through the ordinary transaction path — no assembly and no coordinator required.

We propose:

- Creating a `TransactionProposal` ledger entry.
- Creating a `TransactionProposalCreate` transaction.
- Creating a `TransactionProposalSign` transaction.
- Creating a `TransactionProposalCancel` transaction.

This feature will require an amendment, tentatively titled `Cosigner`.

## 2. Motivation

XRPL multi-sign today has three structural problems, all stemming from the absence of an on-ledger "meeting room" for signers:

1. **Manual assembly and latency.** There is no way to "send" a transaction to another signer through the ledger. The transaction blob must be passed around through external channels (email, Slack, custody tooling). Gathering signatures is slow and error-prone, which makes multi-sign unsuitable for time-sensitive operations.

2. **No auto-fill.** For a single-signer transaction, fields like `Sequence` and `LastLedgerSequence` can be auto-filled at submission time. For multi-sign, every field must be fixed before the first signer signs. If the transaction fails to reach a ledger in time (for example because `LastLedgerSequence` was set too low while waiting for signers), the entire round must be restarted from scratch with all signers.

3. **The centralized-coordinator paradox.** One party must eventually collect, sort, and submit all signatures. That party becomes a new single point of failure: if they go offline, the transaction cannot be submitted even if everyone else has signed (**inaction**); they can present different signers with different blobs (**manipulation**); and if they lose the collected signatures the round must restart (**data loss**).

On-Chain Cosigner solves all three by moving signature collection onto the ledger:

- The transaction is posted once, on-ledger, with an **immutable payload**. Every signer signs the same object, removing ambiguity.
- Signatures are **collected on the ledger itself**, not assembled by a coordinator. There is no blob to lose, no blob to swap, and the collected set is always available to everyone.
- The completed transaction derives its authority **solely from the signatures collected on-ledger**. Because the signatures accumulate into a standard multi-signed transaction, **anyone** can submit it through the normal transaction path — no coordinator can withhold or alter it.
- A built-in **expiration** prevents abandoned proposals from accumulating and bounds the collection window.

Multi-sign is inherently signature-heavy, and this feature is designed to compose with other signature-heavy XRPL features — [Batch (XLS-56)](../XLS-0056-batch/README.md), sponsored fees & reserves, and lending-protocol origination — where multiple parties across custodians or institutions must co-authorize a single ledger action.

## 3. Overview

### 3.1. Terminology

- **Proposal**: A `TransactionProposal` ledger object. It holds a single unsigned **proposed transaction** (the payload) and the set of signatures collected for it so far.
- **Proposed transaction**: The transaction that will be executed on behalf of the **target account** once enough signatures are collected. It is stored, immutable, inside the proposal. (This is a distinct concept from a Batch "inner transaction".)
- **Target account**: The account on whose behalf the proposed transaction executes — i.e. the `Account` of the proposed transaction. Its `SignerList` configuration governs the quorum.
- **Proposer**: The account that submits `TransactionProposalCreate`. It owns the proposal object and pays its reserve. The proposer need not be a signer or the target account.
- **Signer**: An account on the target account's applicable `SignerList` that can append its signature to the proposal, contributing its weight toward quorum.
- **Quorum**: The `SignerQuorum` value of the target account's applicable `SignerList`. Weights and quorum are **inherited unchanged** from the account's existing multi-sign configuration; this feature does not define its own quorum mechanics.
- **Complete**: A proposal is complete when the collected signatures satisfy the signing requirements of the proposed transaction's type — the target account's quorum for an ordinary transaction, or the outer account's quorum plus a satisfied `BatchSigner` for every participant account of a `Batch`. Its `Transaction` field is then a valid signed transaction that anyone can copy and submit.

### 3.2. Lifecycle

```
                   TransactionProposalCreate
  Proposer  ───────────────────────────────────►  [ TransactionProposal: pending ]
                                                              │
  Signer A  ── TransactionProposalSign ─────────────────────► │  (weight 3 / quorum 6)
  Signer B  ── TransactionProposalSign ─────────────────────► │  (weight 6 / quorum 6) → complete
                                                              │
                                        anyone reads the proposal, sets the proposed
                                        transaction's Signers field to the collected
                                        signatures, and submits it via the normal path
                                                              │
                                                              ▼
                                        proposed transaction executes (standard multi-sign
                                        validation); proposer cancels the now-stale proposal
                                        to reclaim the reserve (or it expires and anyone
                                        cleans it up)
```

At any point while the proposal is not terminal, the **proposer** may submit `TransactionProposalCancel` to abort it. Once the proposal is terminal (expired, or the proposed transaction's `LastLedgerSequence` has passed), it stops accepting signatures and **any** account may clean it up.

A proposal exists as a ledger object only until it is cancelled or cleaned up. Its full history — creation, each signature and the ledger it was recorded in, and the final outcome — remains permanently available in transaction metadata for compliance, audit, and reconciliation.

### 3.3. Design principles

- **The ledger is the meeting room, not the executor.** Signatures are collected and validated on-ledger; execution reuses the existing multi-sign submission path. No new execution semantics and no fourth transaction are introduced.
- **Authority derives from the collected signatures, not from any submitter.** Anyone can submit the completed transaction; the existing multi-sign machinery validates it against the target account's `SignerList`.
- **Immutable payload.** Once created, the proposed transaction cannot be modified. Signers sign exactly what they see.
- **No new quorum model.** Quorum, weights, and per-transaction-type signer lists are inherited from [XLS-49 (Multiple Signer Lists)](../XLS-0049-multiple-signer-lists/README.md) and the existing multi-sign machinery.
- **Every collected signature is pre-validated.** The ledger verifies each signature (correct key, valid over the proposed transaction, signer on the `SignerList`) as it is added, so a complete proposal is guaranteed to be a submittable transaction.

## 4. Ledger Entry: `TransactionProposal`

This object represents a pending multi-signature proposal. It holds the unsigned proposed transaction and the signatures collected for it so far.

### 4.1. Object Identifier

**Key Space:** `0x[TBD]`

**ID Calculation Algorithm:**

```
ProposalID = hash( <TransactionProposal space key>, Owner, Account, SeqOrTicket )
```

where `Account` and `SeqOrTicket` are taken from the **proposed transaction**: `Account` is the target account, and `SeqOrTicket` is its `Sequence` or `TicketSequence`. **Nothing else contributes to the ID** — not the rest of the payload, and not any signature field — so the ID is fixed at creation and never changes as signatures accumulate. This value is the `ProposalID` referenced by `TransactionProposalSign` and `TransactionProposalCancel`.

Because the ID depends only on `(Owner, target account, sequence/ticket)` and not on the payload contents, an `Owner` **cannot** hold two live proposals that target the same account with the same sequence/ticket, _even if the payloads differ_: the second `TransactionProposalCreate` produces the same `ProposalID` and fails with `tecDUPLICATE` (§5.3.2). This is intentional — both proposals would attempt to consume the same target `Sequence`/`TicketSequence`, so at most one could ever execute. Distinct owners may each hold a proposal for the same triple, since their IDs differ by `Owner`.

### 4.2. Fields

| Field Name          | Constant | Required | Internal Type | Default Value         | Description                                                                                                                                                                 |
| ------------------- | -------- | -------- | ------------- | --------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `LedgerEntryType`   | Yes      | Yes      | UINT16        | `TransactionProposal` | Identifies this as a `TransactionProposal` object.                                                                                                                          |
| `Flags`             | No       | Yes      | UINT32        | `0`                   | Flag values associated with this object. No flags are currently defined.                                                                                                    |
| `Owner`             | Yes      | Yes      | ACCOUNT       | N/A                   | The proposer — the account that created and owns this object and pays its reserve.                                                                                          |
| `Transaction`       | No       | Yes      | STOBJECT      | N/A                   | The proposed transaction. Immutable except for its signature fields (`Signers`, and `BatchSigners` for a `Batch`), into which collected signatures accumulate (see §4.2.1). |
| `Expiration`        | Yes      | Yes      | UINT32        | N/A                   | Ledger close-time (seconds since the Ripple Epoch) after which the proposal stops accepting signatures and becomes terminal.                                                |
| `OwnerNode`         | No       | Yes      | UINT64        | N/A                   | Hint for which page this object appears on in the owner directory.                                                                                                          |
| `PreviousTxnID`     | No       | Yes      | HASH256       | N/A                   | Hash of the previous transaction that modified this object.                                                                                                                 |
| `PreviousTxnLgrSeq` | No       | Yes      | UINT32        | N/A                   | Ledger sequence of the previous transaction that modified this object.                                                                                                      |

**Field Details:**

#### 4.2.1. `Transaction`

`Transaction` is the proposed transaction the proposal collects signatures for. Every field of it is **immutable** for the life of the proposal **except its signature fields** — `Signers` and, for a `Batch`, `BatchSigners` — into which the ledger inserts each validated signature (see §4.2.2). Because the XRPL signing payloads exclude these signature fields, appending a signature never changes what any signer signed over, so previously-collected signatures stay valid and later signers sign the same canonical payload.

The proposed transaction:

- **Must** be submitted unsigned: at creation its `SigningPubKey` field must be an empty string (`""`), and its `TxnSignature`, `Signers`, and (for a `Batch`) `BatchSigners` fields must be omitted. This is the exact canonical form over which signers produce their signatures; the ledger populates the signature fields as they arrive. If it is a `Batch`, its `RawTransactions` must follow the XLS-56 rules for inner transactions (each unsigned, with the `tfInnerBatchTxn` flag).
- **Must** specify either a `Sequence` or a `TicketSequence` for its target account. Using a `TicketSequence` is **RECOMMENDED**, as it decouples the proposed transaction from the target account's live sequence and avoids the "restart the round" problem (see §8.2).
- **Must** carry a `Fee`. The proposed transaction's fee is paid by the **target account** (the proposed transaction's `Account`) when the completed transaction is submitted.
- **Must not** itself be a `TransactionProposalCreate`, `TransactionProposalSign`, or `TransactionProposalCancel` transaction (no nesting of proposals).
- **May** include a `LastLedgerSequence`. If present, it bounds the window during which the completed transaction can be submitted, and it acts as a second termination bound for the proposal (see §4.5): once the current ledger sequence exceeds it, the proposed transaction can never be applied (it would fail with `tefMAX_LEDGER`), so the proposal becomes terminal and permissionlessly cleanable.

The target account is the proposed transaction's `Account` field. It may differ from the proposer.

#### 4.2.2. Collected signatures

Signatures are stored directly in the proposed transaction's own native signature fields — there is no separate signatures field on the proposal object. This means a **complete** proposal requires no assembly at all: the `Transaction` field is already a valid, fully-signed transaction that can be copied verbatim and submitted. Where a signature lands depends on the proposed transaction type:

- **Ordinary transaction:** into `Transaction.Signers`, the [standard multi-sign `Signers` array](https://xrpl.org/docs/references/protocol/transactions/common-fields/#signers-field), authorizing the target account (the transaction's `Account`).
- **`Batch` (XLS-56):** authorization of the **outer account** (the Batch's `Account`) goes into `Transaction.Signers`; each **other participant account** (an account with inner transactions in `RawTransactions`) is authorized by an entry in `Transaction.BatchSigners`. A single-signature participant's entry carries `SigningPubKey`/`TxnSignature` directly; a multi-signing participant's entry carries a nested `Signers` array. This mirrors [XLS-56 §2.1.3](../XLS-0056-batch/README.md).

Every `Signers` array (top-level or nested in a `BatchSigner`) is kept sorted by `Account` and holds at most 32 entries (the maximum `SignerList` size). **Weights are not stored**: a signer's weight and the relevant quorum are always read from the applicable account's `SignerList`, both when a signature is added and when the transaction is finally submitted (see §8.3). Clients compute "remaining weight to quorum" by joining the collected signatures against the relevant `SignerList`(s). §6.1.2 describes how `TransactionProposalSign` routes a signature to the correct location.

### 4.3. Ownership

**Owner:** `Owner` (the proposer).

**Directory Registration:** The object is registered in the `Owner`'s owner directory.

### 4.4. Reserves

**Reserve Requirement:** Custom (flat). A `TransactionProposal` holds a full transaction plus its collected signatures, so it reserves more than a typical ledger entry.

- **Ordinary proposed transaction:** 5 owner-reserve increments (currently **1 XRP**).
- **`Batch` proposed transaction:** 10 owner-reserve increments (currently **2 XRP**), reflecting its larger footprint (up to 8 inner transactions and signatures for multiple participant accounts).

Each increment is the standard owner-reserve amount (currently 0.2 XRP, subject to Fee Voting).

### 4.5. Deletion

**Terminal proposal:** A proposal is **terminal** when it can no longer be completed and submitted, i.e. when either of the following is true relative to the parent ledger:

- The parent ledger's close time is at or after `Expiration`; or
- The proposed transaction includes a `LastLedgerSequence` and the current ledger sequence is greater than it.

A terminal proposal stops accepting new signatures and exists in ledger state only until it is cleaned up.

**Deletion Transactions:** `TransactionProposalCancel`, `TransactionProposalSign`.

**Deletion Conditions:** The object is deleted when any one of the following occurs:

- **Owner cancellation (non-terminal):** while the proposal is not terminal, only the **`Owner`** (the proposer) may delete it, via `TransactionProposalCancel` (result `tesSUCCESS`).
- **Permissionless cleanup (terminal):** once the proposal is terminal, **any** account may delete it via `TransactionProposalCancel` (result `tesSUCCESS`, since deletion is that transaction's intended action).
- **Incidental cleanup by a late signer:** a `TransactionProposalSign` submitted against a terminal proposal **fails** with `tecEXPIRED` — its intended action (recording a signature) cannot happen — but, as a side effect of that claimed-fee result, it deletes the terminal proposal and releases the reserve (see §6.4).

Note that submitting the completed transaction (through the normal transaction path) does **not** delete the proposal object; the object is independent of the target account's ledger and is removed only by the conditions above. See §8.4 and §12.4.

**Account Deletion Blocker:** Yes. A `TransactionProposal` object must be deleted before its owner account can be deleted.

### 4.6. Invariants

- `Expiration` is always present and non-zero.
- Every entry in `Transaction.Signers` is unique by `Account`, and the array is sorted by `Account` with at most 32 entries.
- Every entry in `Transaction.Signers` is a signature that was cryptographically valid over the proposed `Transaction` (excluding its `Signers` field) at the time it was added.
- The proposed `Transaction` always has an empty `SigningPubKey` and no `TxnSignature`; only its `Signers` field changes over the life of the proposal.

### 4.7. Example JSON

```json
{
  "LedgerEntryType": "TransactionProposal",
  "Flags": 0,
  "Owner": "rPROPOSER........................",
  "Expiration": 800000000,
  "Transaction": {
    "TransactionType": "Payment",
    "Account": "rTARGET..........................",
    "Destination": "rDEST............................",
    "Amount": "5000000000",
    "TicketSequence": 1201,
    "Fee": "10",
    "SigningPubKey": "",
    "Signers": [
      {
        "Signer": {
          "Account": "rCEO............................",
          "SigningPubKey": "03AB...",
          "TxnSignature": "3045..."
        }
      }
    ]
  },
  "OwnerNode": "0000000000000000",
  "PreviousTxnID": "F3B1...",
  "PreviousTxnLgrSeq": 12345678
}
```

## 5. Transaction: `TransactionProposalCreate`

Creates a `TransactionProposal` object holding an unsigned proposed transaction, placing it in a pending state visible to all signers.

### 5.1. Fields

| Field Name        | Required? | JSON Type | Internal Type | Default Value               | Description                                                            |
| ----------------- | --------- | --------- | ------------- | --------------------------- | ---------------------------------------------------------------------- |
| `TransactionType` | ✔️        | string    | UINT16        | `TransactionProposalCreate` | Identifies this as a `TransactionProposalCreate` transaction.          |
| `Account`         | ✔️        | string    | ACCOUNT       | N/A                         | The proposer submitting the proposal.                                  |
| `Transaction`     | ✔️        | object    | STOBJECT      | N/A                         | The unsigned proposed transaction (see §4.2.1).                        |
| `Expiration`      | ✔️        | number    | UINT32        | N/A                         | Ledger close-time after which the proposal stops accepting signatures. |

Standard common fields (`Fee`, `Sequence`, `Flags`, `Memos`, `SourceTag`, signing fields) apply. `Memos` and `SourceTag` MAY be used to attach a reason code or reconciliation identifier to the proposal.

### 5.2. Transaction Fee

**Fee Structure:** Standard. This transaction uses the standard transaction fee (currently 10 drops, subject to Fee Voting changes). Note that the proposed transaction's own `Fee` is not charged here; it is charged to the target account when the completed transaction is submitted.

### 5.3. Failure Conditions

#### 5.3.1. Data Verification

All Data Verification failures return a `tem`-level error.

1. `Transaction` is missing or is not a well-formed transaction (`temMALFORMED`).
2. The proposed transaction has a non-empty `SigningPubKey` or includes a `TxnSignature` or `Signers` field (`temBAD_SIGNER`).
3. The proposed transaction is itself a `TransactionProposalCreate`, `TransactionProposalSign`, or `TransactionProposalCancel` (`temINVALID`).
4. The proposed transaction specifies neither `Sequence` nor `TicketSequence`, or specifies both (`temSEQ_AND_TICKET`).
5. `Expiration` is missing or zero (`temMALFORMED`).

#### 5.3.2. Protocol-Level Failures

1. `Expiration` is already at or before the parent ledger's close time (`tecEXPIRED`).
2. The proposed transaction includes a `LastLedgerSequence` that is already at or before the current ledger sequence (`tecEXPIRED`).
3. The proposer has insufficient reserve to own the new `TransactionProposal` object (`tecINSUFFICIENT_RESERVE`).
4. The target account (the proposed transaction's `Account`) does not exist (`tecNO_TARGET`).
5. A `TransactionProposal` with the same `ProposalID` already exists — i.e. the sender already owns a live proposal whose proposed transaction has the same target account and `Sequence`/`TicketSequence` (`tecDUPLICATE`).

### 5.4. State Changes

**On Success (`tesSUCCESS`):**

- Creates a new `TransactionProposal` ledger object whose `Owner` is the sending `Account`. The proposed transaction is stored with no signatures yet.
- Increments the `Owner`'s `OwnerCount`.

### 5.5. Example JSON

```json
{
  "TransactionType": "TransactionProposalCreate",
  "Account": "rPROPOSER........................",
  "Fee": "10",
  "Sequence": 42,
  "Expiration": 800000000,
  "Transaction": {
    "TransactionType": "Payment",
    "Account": "rTARGET..........................",
    "Destination": "rDEST............................",
    "Amount": "5000000000",
    "TicketSequence": 1201,
    "Fee": "10",
    "SigningPubKey": ""
  }
}
```

## 6. Transaction: `TransactionProposalSign`

Appends one signer's multi-signature for the proposed transaction to the proposal. The signature is validated exactly as it would be during standard multi-sign, guaranteeing that the collected set remains submittable. If the proposal is already terminal, this transaction cannot record a signature and instead **fails with `tecEXPIRED`**, deleting the terminal proposal as a side effect (see §6.4).

### 6.1. Fields

| Field Name        | Required? | JSON Type | Internal Type | Default Value             | Description                                                                                                                           |
| ----------------- | --------- | --------- | ------------- | ------------------------- | ------------------------------------------------------------------------------------------------------------------------------------- |
| `TransactionType` | ✔️        | string    | UINT16        | `TransactionProposalSign` | Identifies this as a `TransactionProposalSign` transaction.                                                                           |
| `Account`         | ✔️        | string    | ACCOUNT       | N/A                       | The account submitting (and paying for) this transaction. Must equal the account that produced the contributed signature (see below). |
| `ProposalID`      | ✔️        | string    | HASH256       | N/A                       | The ID of the `TransactionProposal` being signed.                                                                                     |
| `Signer`          |           | object    | STOBJECT      | N/A                       | A contribution authorizing the proposed transaction's own `Account` (see §6.1.1).                                                     |
| `BatchSigner`     |           | object    | STOBJECT      | N/A                       | A contribution authorizing a participant account of a proposed `Batch` (see §6.1.2).                                                  |

**Exactly one** of `Signer` or `BatchSigner` must be present. Use `Signer` to authorize the proposed transaction's own `Account` — an ordinary transaction's target account, or a `Batch`'s outer account. Use `BatchSigner` to authorize a _participant_ account of a proposed `Batch`.

#### 6.1.1. `Signer`

`Signer` is a standard multi-sign `Signer` inner object — `Account`, `SigningPubKey`, `TxnSignature` — authorizing the **proposed transaction's own `Account`** (an ordinary transaction's target, or a `Batch`'s outer account). `TxnSignature` is over that account's standard multi-sign signing data (the transaction serialized without its signature fields, multi-sign hash prefix, `Signer.Account` suffix), exactly as for a direct multi-signed submission. The ledger inserts it verbatim into `Transaction.Signers`.

`Signer.Account` must equal the transaction's `Account` and must be a member of the proposed transaction's `Account`'s applicable `SignerList`.

**Delegated transactions:** If the proposed transaction carries a `Delegate` field (permission delegation), it is authorized by the **`Delegate`** account rather than by the transaction's `Account`. In that case the collected signatures authorize the `Delegate` account: `Signer.Account` must be a member of the `Delegate` account's applicable `SignerList`, and both the per-signature check and the final submission validate against the `Delegate` account's authority. All other mechanics are unchanged.

#### 6.1.2. `BatchSigner`

`BatchSigner` is an [XLS-56 `BatchSigner` inner object](../XLS-0056-batch/README.md) authorizing a **participant account** of a proposed `Batch`. It contains:

- `Account` — the participant (owning) account being authorized; it must have at least one inner transaction in `RawTransactions`.
- **Either** `SigningPubKey` + `TxnSignature` — the participant authorizes with its **own key** (a single-signature `BatchSigner`; omit `Signers`) — **or** `Signers` — a nested array containing **exactly one** `Signer` entry, the submitter's multi-sign contribution toward `Account`'s quorum.

The signature is over the XLS-56 batch signing data for `Account`, which binds the owning account: `message = <batch data> + <owning account>` for the single-signature form, plus the `<signer account>` suffix for the multi-sign form (XLS-56 §2.1.3).

The ledger merges `BatchSigner` into `Transaction.BatchSigners`, keyed by `BatchSigner.Account`:

- **Single-signature:** records the `SigningPubKey`/`TxnSignature` `BatchSigner` for `Account`. This fully authorizes `Account`; only one is needed.
- **Multi-sign:** appends the single nested `Signer` into the `BatchSigner.Signers` array for `Account` (creating the `BatchSigner` entry if it does not yet exist), kept sorted and deduped by signer account.

### 6.2. Transaction Fee

**Fee Structure:** Standard. The submitter pays the standard fee for this transaction. The proposed transaction's own `Fee` is not charged here; it is charged to the target account when the completed transaction is submitted.

### 6.3. Failure Conditions

#### 6.3.1. Data Verification

All Data Verification failures return a `tem`-level error.

1. `ProposalID` is missing or malformed (`temMALFORMED`).
2. Neither or both of `Signer` and `BatchSigner` are present (`temMALFORMED`).
3. `BatchSigner` is malformed — it includes neither a `SigningPubKey`/`TxnSignature` pair nor exactly one nested `Signers` entry, or it includes both forms (`temMALFORMED`).
4. The submitting `Account` does not equal the account that produced the contributed signature — `Signer.Account`; or `BatchSigner.Account` (single-signature form); or `BatchSigner.Signers[0].Account` (multi-sign form) (`temMALFORMED`).
5. A contributed signature is not valid over its relevant signing payload (§6.1.1, §6.1.2) (`temBAD_SIGNATURE`).

#### 6.3.2. Protocol-Level Failures

1. No `TransactionProposal` object exists with the given `ProposalID` (`tecNO_ENTRY`).
2. The proposal is terminal — its `Expiration` has passed, or the proposed transaction's `LastLedgerSequence` has passed (`tecEXPIRED`). This is a claimed-fee failure: no signature is recorded, but the terminal proposal is deleted as a side effect (see §6.4). This condition is checked before the authorization conditions below.
3. `BatchSigner` is present but the proposed transaction is not a `Batch`, or `BatchSigner.Account` has no inner transaction in `RawTransactions` (`tecNO_PERMISSION`).
4. The signing account is not authorized for the account it is authorizing — not that account's own key (single-signature) and not a member of its applicable `SignerList` (multi-sign) (`tecNO_PERMISSION`).
5. The signing account is already recorded in that destination, or a single-signature `BatchSigner` already exists for that participant account (`tecDUPLICATE`). (The same signer may still appear in a different participant's destination.)
6. The contribution conflicts with the existing authorization mode for that participant account — a multi-sign contribution when a single-signature `BatchSigner` is already recorded, or vice versa (`tecNO_PERMISSION`).
7. Adding the signature would exceed the maximum of 32 entries in the destination `Signers` array (`tecOVERSIZE`).

### 6.4. State Changes

**On Success (`tesSUCCESS`):**

- Validates the contribution and records it: a `Signer` is inserted into `Transaction.Signers`; a `BatchSigner` is merged into `Transaction.BatchSigners` (single-signature entry, or its nested `Signers` array) as described in §6.1.2. Any `Signers` array is kept sorted by `Account`.
- No execution occurs. Once the collected signatures satisfy the signing requirements for the proposed transaction's type — the target account's quorum for an ordinary transaction, or the outer account's quorum plus a satisfied `BatchSigner` for every participant account of a `Batch` — the proposal is **complete**: the `Transaction` field is a valid signed transaction that anyone can copy and submit (see §6.5).

**On failure against a terminal proposal (`tecEXPIRED`):**

- No signature is recorded. Because a `tec` result is still applied to the ledger, the terminal proposal object is deleted and the `Owner`'s `OwnerCount` is decremented (releasing the reserve) as a side effect. This mirrors how transactions like `EscrowFinish` and `CheckCash` report a claimed-fee failure while cleaning up an expired object. A signer whose `TransactionProposalSign` arrives after the proposal has expired therefore both fails and cleans up in one step.

### 6.5. Submitting the completed transaction

This specification introduces no on-ledger execution step, and no assembly is required. Once a proposal is complete, any observer simply:

1. Reads the `TransactionProposal` by `ProposalID`.
2. Copies the proposed `Transaction` verbatim — it already contains the collected `Signers` (and, for a `Batch`, `BatchSigners`), sorted, and is a fully-formed signed transaction.
3. Submits it through the ordinary transaction path (e.g. the `submit` API).

The existing multi-sign (and, for a `Batch`, `BatchSigners`) validation then checks the signatures against the applicable accounts' current `SignerList`(s) and applies the transaction, charging its `Fee` to the target account. No field of On-Chain Cosigner appears on the submitted transaction — it is an ordinary transaction.

### 6.6. Example JSON

Signing an ordinary proposed transaction. The signature lands in `Transaction.Signers`:

```json
{
  "TransactionType": "TransactionProposalSign",
  "Account": "rCEO............................",
  "Fee": "10",
  "Sequence": 7,
  "ProposalID": "C1A2B3D4E5F6...............................",
  "Signer": {
    "Account": "rCEO............................",
    "SigningPubKey": "03AB...",
    "TxnSignature": "3045..."
  }
}
```

Signing for a participant account `rBOB` of a proposed multi-account `Batch`, **multi-sign** form: `rBOBSIGNER` is a member of `rBOB`'s `SignerList`, so the contribution is a `BatchSigner` for `rBOB` carrying one nested `Signer`. It merges into `rBOB`'s `BatchSigner.Signers`. (A signer authorized on another participant submits a separate `TransactionProposalSign` with a `BatchSigner` for that account and a distinct signature.)

```json
{
  "TransactionType": "TransactionProposalSign",
  "Account": "rBOBSIGNER......................",
  "Fee": "10",
  "Sequence": 3,
  "ProposalID": "C1A2B3D4E5F6...............................",
  "BatchSigner": {
    "Account": "rBOB............................",
    "Signers": [
      {
        "Signer": {
          "Account": "rBOBSIGNER......................",
          "SigningPubKey": "02CD...",
          "TxnSignature": "3044..."
        }
      }
    ]
  }
}
```

Signing for a participant account `rCAROL` with its **own key**, single-signature form (no nested `Signers`); this alone authorizes `rCAROL`:

```json
{
  "TransactionType": "TransactionProposalSign",
  "Account": "rCAROL..........................",
  "Fee": "10",
  "Sequence": 9,
  "ProposalID": "C1A2B3D4E5F6...............................",
  "BatchSigner": {
    "Account": "rCAROL..........................",
    "SigningPubKey": "03EF...",
    "TxnSignature": "3045..."
  }
}
```

## 7. Transaction: `TransactionProposalCancel`

Deletes a `TransactionProposal` object and releases the owner's reserve.

### 7.1. Fields

| Field Name        | Required? | JSON Type | Internal Type | Default Value               | Description                                                   |
| ----------------- | --------- | --------- | ------------- | --------------------------- | ------------------------------------------------------------- |
| `TransactionType` | ✔️        | string    | UINT16        | `TransactionProposalCancel` | Identifies this as a `TransactionProposalCancel` transaction. |
| `Account`         | ✔️        | string    | ACCOUNT       | N/A                         | The account requesting cancellation.                          |
| `ProposalID`      | ✔️        | string    | HASH256       | N/A                         | The ID of the `TransactionProposal` to cancel.                |

### 7.2. Authorization

- **Non-terminal proposal:** Only the **owner** (the proposal's `Owner`, i.e. the proposer) may cancel.
- **Terminal proposal:** **Any** account may cancel, to clean up the object and release the owner's reserve.

Cancellation is only fully effective before a proposal is complete. If a quorum-weight of valid signatures has already been collected, an observer may have copied them and can still submit the completed transaction even after the proposal object is gone; see §12.4.

### 7.3. Failure Conditions

#### 7.3.1. Data Verification

1. `ProposalID` is missing or malformed (`temMALFORMED`).

#### 7.3.2. Protocol-Level Failures

1. No `TransactionProposal` object exists with the given `ProposalID` (`tecNO_ENTRY`).
2. The proposal is not terminal and `Account` is not the `Owner` (`tecNO_PERMISSION`).

### 7.4. State Changes

**On Success (`tesSUCCESS`):**

- Deletes the `TransactionProposal` object.
- Decrements the proposer's `OwnerCount` (releasing the reserve).

### 7.5. Example JSON

```json
{
  "TransactionType": "TransactionProposalCancel",
  "Account": "rPROPOSER........................",
  "Fee": "10",
  "Sequence": 43,
  "ProposalID": "C1A2B3D4E5F6..............................."
}
```

## 8. Rationale

### 8.1. Why collect signatures on-ledger

The problem multi-sign users actually face is not the cryptography of signing — it is coordination: sharing the exact payload, gathering signatures, and getting them submitted without a trusted middleman. On-Chain Cosigner keeps the standard multi-sign signatures but moves their collection point from a coordinator's inbox to an immutable ledger object. Every signer signs the same immutable payload; every signature is validated on arrival; and the collected set is always available to everyone. This removes the coordinator as a single point of failure — there is no blob to lose, no blob to swap, and, because the collected set is a standard multi-signed transaction, anyone can submit it.

### 8.2. Solving the auto-fill problem with Tickets

Standard multi-sign forces every field — including `Sequence` and `LastLedgerSequence` — to be fixed before the first signature, so a slow signing round can render the transaction permanently unsubmittable and force a restart. On-Chain Cosigner addresses this in two ways. First, the collection window is bounded by the proposal's own `Expiration`, so a slow round expires cleanly instead of leaving an unusable half-signed blob in someone's inbox; the proposed transaction's `LastLedgerSequence` (optional) separately bounds the _submission_ window. Second, using a `TicketSequence` for the proposed transaction (recommended) decouples the payload from the target account's live sequence number, so other activity on the target account during the signing round does not invalidate the proposal.

### 8.3. How quorum is enforced

Quorum is never evaluated by a bespoke rule in this feature. Each signature is validated against the target account's `SignerList` when it is added (so garbage cannot accumulate), and the completed transaction is validated again by the existing multi-sign machinery when it is finally submitted. Both checks use the account's live `SignerList`, so the executed action always reflects the account's **current** authority model — including per-transaction-type lists resolved from the proposed transaction's type, exactly as in ordinary multi-sign under [XLS-49 (Multiple Signer Lists)](../XLS-0049-multiple-signer-lists/README.md).

### 8.4. Why there is no execution transaction

Because signatures are collected directly into the proposed transaction's own `Signers` field, a complete proposal _is_ a fully-signed multi-sign transaction waiting to be submitted — no assembly step exists to get wrong. Adding a dedicated on-ledger execute step (a fourth transaction, or auto-execution inside `TransactionProposalSign`) would duplicate logic the ledger already has and would couple execution to a specific submitter or to the moment a particular signature lands. Instead, execution reuses the ordinary submission path and any account may perform it. The cost of this choice is that the proposal object and the target-account execution are decoupled: submitting the completed transaction does not delete the proposal, and deleting the proposal does not revoke already-collected signatures (see §12.4).

## 9. Composability

- **Batch (XLS-56):** The proposed transaction may be a `Batch`, enabling multi-account, atomic, multi-signed settlement (e.g. end-of-day repo netting, flash-style capital operations). The outer account is authorized via a `Signer` (into `Transaction.Signers`); each participant account via a `BatchSigner` — single-signature or multi-sign (§6.1.2). A signer authorized on several of the batch's accounts submits one `TransactionProposalSign` per account, since each signature is bound to its owning account. Once every participant's requirement is met the completed batch executes atomically. This is the primary motivating case for On-Chain Cosigner, since multi-account Batches otherwise require the most off-chain signature coordination.
- **Lending protocols:** A borrower can post a `LoanSet` (or equivalent) as a proposal; the lender signs on-chain as counterparty, turning loan origination into a trustless, asynchronous flow with no synchronous coordination.
- **Sponsored fees & reserves:** A user posts a transaction that designates a sponsor; the sponsor signs on-chain, co-authorizing the fee/reserve sponsorship.
- **Multiple Signer Lists (XLS-49):** Per-transaction-type signer lists are honored automatically, since both the per-signature check and the final submission use standard multi-sign resolution for the proposed transaction's type.

## 10. Backwards Compatibility

This proposal is purely additive: it introduces one new ledger entry type and three new transaction types, all gated behind the `Cosigner` amendment. Existing multi-sign, `SignerListSet`, and off-chain signing workflows are unaffected and continue to function. Because a completed proposal is submitted through the ordinary multi-sign path, no changes to transaction application or to the multi-sign validation rules are required. Accounts that do not use On-Chain Cosigner are not impacted.

## 11. Open Questions

- **Completion signalling:** Should the ledger set a convenience flag (or expose an RPC field) marking a proposal "complete" once collected weight reaches quorum, so wallets need not join against the `SignerList` themselves?
- **Reducing the initial construction burden:** Can the initial proposed-transaction construction be simplified further, beyond the Ticket-based approach in §8.2?
- **Revocation:** Should there be a first-class way to revoke a completed proposal's signatures on-ledger (beyond invalidating the `Sequence`/`Ticket`), given that cancellation alone does not prevent submission of already-collected signatures (§12.4)?
- **Recurring / standing orders:** Use Case 7 (recurring allowances and treasury stipends) suggests a proposal could activate a long-lived standing order rather than a one-shot transaction, potentially composing with a Subscriptions primitive. This is out of scope for this spec but noted as a future extension.

## 12. Security Considerations

### 12.1. Authority derives solely from the collected signatures

The completed transaction is authorized entirely by the multi-signatures collected on-ledger and validated against the applicable `SignerList`(s) — never by the identity of the account that finally submits it. Submission grants no authority the collected signatures did not already confer, so anyone may submit. A `TransactionProposalSign`, by contrast, must be posted by the signer itself (`Signer.Account` = `Account`), which ties each collected signature to a deliberate on-ledger act by that signer.

### 12.2. Immutable payload

The proposed transaction is fixed at creation and cannot be altered by any subsequent transaction. Signers therefore always sign exactly what is stored, eliminating the manipulation risk of a coordinator presenting different payloads to different signers.

### 12.3. Every collected signature is pre-validated

Each `TransactionProposalSign` is rejected unless the supplied `Signer` is cryptographically valid over the immutable proposed transaction and belongs to the target account's applicable `SignerList`. This prevents an attacker from polluting a proposal with junk entries and guarantees that a complete proposal will pass standard multi-sign validation at submission.

### 12.4. Cancellation does not revoke already-collected signatures

This is the central security consideration of the copy-and-submit model. The proposal object is a bulletin board, not an execution gate: once a quorum-weight of valid signatures has been collected, any observer may have copied them, and those signatures remain valid regardless of whether the proposal object still exists. Cancelling or expiring the proposal frees the reserve but does **not** guarantee the transaction will not execute. To positively prevent execution of a completed (or nearly-completed) proposal, the target account must invalidate the proposed transaction's `Sequence`/`TicketSequence` (e.g. consume the `Ticket` or advance the account `Sequence`) and/or rely on its `LastLedgerSequence` window elapsing. Architects and wallets should surface this clearly.

### 12.5. Stale signatures under SignerList changes

Because both the per-signature check and the final submission validate against the live `SignerList`, removing a signer or raising the quorum while a proposal is pending is honored: a removed signer's contribution no longer counts toward quorum at submission. Conversely, lowering the quorum can make a previously-incomplete set sufficient. Modifying an account's `SignerList` therefore affects all pending proposals against that account.

### 12.6. Denial-of-service and reserve pressure

Each proposal consumes an elevated flat owner reserve (§4.4) held against the `Owner` — higher than a typical ledger entry, and higher still for a `Batch` — pricing the larger state burden and disincentivizing spam. Because every appended signature must be valid, an attacker cannot inflate a proposal with junk. Built-in expiry ensures abandoned proposals can always be cleaned up (by anyone, once terminal) so they do not accumulate indefinitely in ledger state.

### 12.7. Fee accountability

The proposed transaction's fee is paid by the target account when the completed transaction is submitted, consistent with the target account being the party that authorized the action via its signers. Each `TransactionProposalCreate`, `TransactionProposalSign`, and `TransactionProposalCancel` pays its own fee from its submitter.

# Appendix

## Appendix A: FAQ

### A.1: Who can create a proposal?

Any account. The proposer need not be a signer on the target account nor the target account itself. The proposer owns the object and pays its reserve.

### A.2: Can the target account be different from the proposer?

Yes. The target account is the `Account` of the proposed transaction; the proposer is the account that submits `TransactionProposalCreate`. This is what enables flows like a borrower proposing a `LoanSet` that a lender then signs.

### A.3: How does a signer know what they are signing?

The full proposed transaction is stored, immutable, in the `Transaction` field of the on-ledger object. A signer (or their wallet) reads the object by `ProposalID`, inspects the payload, signs exactly that payload, and submits the signature via `TransactionProposalSign`. There is nothing to pass around off-chain.

### A.4: How is the proposed transaction actually executed?

There is no on-ledger execute step. Signatures accumulate inside the proposed transaction's own `Signers` field, so once quorum weight is reached the `Transaction` field is already a valid multi-signed transaction: any observer copies it verbatim and submits it through the normal transaction path. The existing multi-sign machinery validates and applies it. See §6.5.

### A.5: Does cancelling a proposal guarantee it won't execute?

Only if a quorum-weight of valid signatures has not yet been collected. Once enough signatures exist on-ledger, someone may have copied them and can still submit the completed transaction. To positively block execution, invalidate the proposed transaction's `Sequence`/`Ticket` or let its `LastLedgerSequence` elapse. See §12.4.

### A.6: What happens if quorum is never reached before expiry?

The proposal becomes terminal at `Expiration`, stops accepting signatures, and any account may submit `TransactionProposalCancel` to delete it and release the proposer's reserve. The full signing history remains in transaction metadata.

### A.7: Can there be multiple pending proposals against the same target account?

Yes. A proposal's ID is derived from its `Owner` and the proposed transaction's target account and `Sequence`/`TicketSequence` (§4.1). Using a distinct `TicketSequence` on each proposed transaction lets one owner hold multiple concurrent proposals against the same target account without collisions.

### A.8: Why is the proposed transaction's fee paid by the target account and not the submitter?

The proposed transaction acts on behalf of the target account, authorized by that account's signers. Charging its fee to the target account keeps fee accountability with the party that authorized the action — it is, after all, an ordinary multi-signed transaction of the target account.

### A.9: How does signing work when the proposed transaction is a multi-account Batch?

The outer account is authorized with a `Signer` (into `Transaction.Signers`); each participant account with a `BatchSigner` — either single-signature (the participant's own key, nested `Signers` absent) or multi-sign (a nested `Signer` per contributing signer). The `BatchSigner.Account` field itself names the owning account, so no separate routing field is needed. Because an XLS-56 batch signature binds the owning account (`message = <batch data> + <owning account> + <signer account>`), a signer authorized on several accounts must submit one `TransactionProposalSign` per account, each with a distinct signature; the same signer key may therefore appear across several participants' `BatchSigner.Signers`. The proposal is complete once the outer account's quorum and every participant's `BatchSigner` are satisfied; the `Transaction` field is then a fully-signed Batch ready to submit. See §6.1.2.

### A.10: Does this replace off-chain multi-sign?

No. Off-chain multi-sign and standard `SignerListSet` continue to work unchanged. On-Chain Cosigner is an additive, opt-in coordination layer for accounts that want the ledger to be the meeting room.
