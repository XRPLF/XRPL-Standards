<pre>
  title: On-Chain Cosigner
  description: Native on-ledger proposal and multi-signature collection for XRPL transactions.
  author: Shawn Xie, Zhiyuan Wang, Chenna Keshava B S, Mayukha Vadari
  category: Amendment
  status: Draft
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
- **Signer**: An account ID on the target account's applicable `SignerList` that can append its signature to the proposal, contributing its weight toward quorum. For multi-signing, this may be an unfunded AccountID derived from a public key, matching existing XRPL multi-sign behavior.
- **Quorum**: The `SignerQuorum` value of the target account's applicable `SignerList`. Weights and quorum are **inherited unchanged** from the account's existing multi-sign configuration; this feature does not define its own quorum mechanics.
- **Complete**: A proposal is complete when the collected signatures satisfy all of the proposed transaction's signing requirements — the target account's quorum, plus any auxiliary co-signature the transaction requires (the `Counterparty` of a `LoanSet`, the `Sponsor` of a sponsored transaction; §6.1) — or, for a `Batch`, the outer account's quorum plus a satisfied authorization for every participant account. Its `ProposedTransaction` field is then a valid signed transaction that anyone can copy and submit.

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
                                        validation); consuming the target account's
                                        TicketSequence auto-deletes the now-stale proposal
                                        and refunds its reserve (§4.5)
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
ProposalID = hash( <TransactionProposal space key>, Account, TicketSequence )
```

where `Account` and `TicketSequence` are taken from the **proposed transaction**: `Account` is the target account, and `TicketSequence` is the ticket it spends. **Nothing else contributes to the ID** — not the rest of the payload, and not any signature field — so the ID is fixed at creation and never changes as signatures accumulate. This value is the `ProposalID` referenced by `TransactionProposalSign` and `TransactionProposalCancel`.

Since the ID depends only on the target account and its `TicketSequence`, any transaction that consumes that ticket lets the ledger rebuild the ID and delete the stale proposal (§4.5).

The trade-off: only **one** live proposal can exist per `(target account, ticket)`. A second `TransactionProposalCreate` for the same pair fails with `tecDUPLICATE` (§5.3.2), whatever its payload or proposer. Only one of them could ever execute anyway, so this costs nothing in practice — and a proposer wanting several concurrent proposals just uses a different `TicketSequence` for each (§9.2).

### 4.2. Fields

| Field Name            | Constant | Required | Internal Type | Default Value         | Description                                                                                                                                                                                                                                          |
| --------------------- | -------- | -------- | ------------- | --------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `LedgerEntryType`     | Yes      | Yes      | UINT16        | `TransactionProposal` | Identifies this as a `TransactionProposal` object.                                                                                                                                                                                                   |
| `Flags`               | No       | Yes      | UINT32        | `0`                   | Flag values associated with this object. No flags are currently defined.                                                                                                                                                                             |
| `Owner`               | Yes      | Yes      | ACCOUNT       | N/A                   | The proposer — the account that created and owns this object and pays its reserve.                                                                                                                                                                   |
| `ProposedTransaction` | No       | Yes      | STOBJECT      | N/A                   | The proposed transaction. Immutable except for its signature fields (`Signers`; `CounterpartySignature`/`SponsorSignature` for a type that requires one; and `BatchSigners` for a `Batch`), into which collected signatures accumulate (see §4.2.1). |
| `Expiration`          | Yes      | Yes      | UINT32        | N/A                   | Ledger close-time (seconds since the Ripple Epoch) after which the proposal stops accepting signatures and becomes terminal.                                                                                                                         |
| `OwnerNode`           | Yes      | Yes      | UINT64        | N/A                   | Hint for which page this object appears on in the owner directory.                                                                                                                                                                                   |
| `PreviousTxnID`       | No       | Yes      | HASH256       | N/A                   | Hash of the previous transaction that modified this object.                                                                                                                                                                                          |
| `PreviousTxnLgrSeq`   | No       | Yes      | UINT32        | N/A                   | Ledger sequence of the previous transaction that modified this object.                                                                                                                                                                               |

**Field Details:**

#### 4.2.1. `ProposedTransaction`

`ProposedTransaction` is the proposed transaction the proposal collects signatures for. Every field of it is **immutable** for the life of the proposal **except its signature fields** — the top-level `SigningPubKey`/`TxnSignature` (filled only when the target account signs with its own key, §6.1.2); `Signers`; the auxiliary co-signature field(s) a type requires (`CounterpartySignature`, `SponsorSignature`); and, for a `Batch`, `BatchSigners` — into which the ledger inserts each validated signature (see §4.2.2). Because the XRPL signing payloads exclude these signature fields, appending a signature never changes what any signer signed over, so previously-collected signatures stay valid and later signers sign the same canonical payload.

The proposed transaction:

- **Must** be submitted unsigned: at creation its `SigningPubKey` field must be an empty string (`""`), and its `TxnSignature`, `Signers`, `CounterpartySignature`, `SponsorSignature`, and (for a `Batch`) `BatchSigners` fields must be omitted. (Fields that _define_ an auxiliary party — e.g. `Counterparty`, or `Sponsor`/`SponsorFlags` — are ordinary payload fields and must be present at creation if used; only the signature containers are collected on-chain.) This is the exact canonical form over which signers produce their signatures; the ledger populates the signature fields as they arrive. If it is a `Batch`, its `RawTransactions` must follow the XLS-56 rules for inner transactions (each unsigned, with the `tfInnerBatchTxn` flag).
- **Must** specify a `TicketSequence` for its target account and **must not** specify `Sequence`. Requiring a ticket decouples the proposed transaction from the target account's live sequence, so unrelated target-account activity cannot invalidate the proposal while signatures are being collected (see §9.2). For as long as the proposal exists, that ticket is reserved: a transaction may consume it only if its payload matches `ProposedTransaction`; otherwise, it is rejected.
- **Must** carry a `Fee`. The proposed transaction's fee is paid by the **target account** (the proposed transaction's `Account`) when the completed transaction is submitted.
- **Must** be a transaction that can be independently multi-signed and submitted through the ordinary path. In particular it **must not** be:
  - a `TransactionProposalCreate`, `TransactionProposalSign`, or `TransactionProposalCancel` (no nesting of proposals);
  - a pseudo-transaction (`EnableAmendment`, `SetFee`, `UNLModify`), which no account originates or signs; or
  - a transaction carrying the `tfInnerBatchTxn` flag, which is only valid inside a `Batch`'s `RawTransactions` and is never submittable standalone (a proposed `Batch`'s _inner_ transactions still carry it, per the rule above; the proposed transaction itself must not).
- **May** include a `LastLedgerSequence`. If present, it bounds the window during which the completed transaction can be submitted, and it acts as a second termination bound for the proposal (see §4.5): once the current ledger sequence exceeds it, the proposed transaction can never be applied (it would fail with `tefMAX_LEDGER`), so the proposal becomes terminal and permissionlessly cleanable.

The target account is the proposed transaction's `Account` field. It may differ from the proposer.

#### 4.2.2. Collected signatures

Signatures are stored directly in the proposed transaction's own native signature fields — there is no separate signatures field on the proposal object. This means a **complete** proposal requires no assembly at all: the `ProposedTransaction` field is already a valid, fully-signed transaction that can be copied verbatim and submitted. Where a signature lands depends on the proposed transaction type:

- **Ordinary transaction:** into `ProposedTransaction.Signers`, the [standard multi-sign `Signers` array](https://xrpl.org/docs/references/protocol/transactions/common-fields/#signers-field), authorizing the target account (the transaction's `Account`) — or, if that account signs with its own key, directly into the proposed transaction's top-level `SigningPubKey`/`TxnSignature` (§6.1.2).
- **`Batch` (XLS-56):** authorization of the **outer account** (the Batch's `Account`) goes into `ProposedTransaction.Signers`; each **other participant account** (an account with inner transactions in `RawTransactions`) is authorized by an entry in `ProposedTransaction.BatchSigners`, which holds at most 24 entries. A single-signature participant's entry carries `SigningPubKey`/`TxnSignature` directly; a multi-signing participant's entry carries a nested `Signers` array. This mirrors [XLS-56 §2.1.3](../XLS-0056-batch/README.md).
- **Auxiliary co-signature (e.g. [`LoanSet`, XLS-66](../XLS-0066-lending-protocol/README.md); sponsored transactions, [XLS-68](../XLS-0068-sponsored-fees-and-reserves/README.md)):** a transaction that requires a second party to co-authorize carries a dedicated signature field for that party — `CounterpartySignature` for the `Counterparty`, `SponsorSignature` for the `Sponsor`. Each party's signature goes into its own field (`SigningPubKey`/`TxnSignature` for a single-signature party, or a nested `Signers` array for a multi-signing one), while the transaction's own `Account` is authorized through `ProposedTransaction.Signers` as above. A transaction may require more than one. See §6.1.

Every `Signers` array (top-level or nested in a `BatchSigner`) is kept sorted by `Account` and holds at most 32 entries (the maximum `SignerList` size). `BatchSigners` is also sorted by `Account` and holds at most 24 entries. **Weights are not stored**: a signer's weight and the relevant quorum are always read from the applicable account's `SignerList`, both when a signature is added and when the transaction is finally submitted (see §9.3). Clients compute "remaining weight to quorum" by joining the collected signatures against the relevant `SignerList`(s). §6.1 describes how `TransactionProposalSign` routes a signature from its `SigningFor` account and `ProposalSignature.Account`.

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

**Deletion Transactions:** `TransactionProposalCancel`, `TransactionProposalSign`, and — implicitly — **any transaction of the target account that consumes the proposed transaction's `TicketSequence`** (see below).

**Deletion Conditions:** The object is deleted when any one of the following occurs:

- **Owner cancellation (non-terminal):** while the proposal is not terminal, the **`Owner`** (the proposer) may delete it via `TransactionProposalCancel` (result `tesSUCCESS`).
- **Target-account cancellation (any time):** the **target account** may delete any proposal made for it via `TransactionProposalCancel`, whether or not it is terminal and no matter how many signatures have been collected (result `tesSUCCESS`). See §7.2.
- **Permissionless cleanup (terminal):** once the proposal is terminal, **any** account may delete it via `TransactionProposalCancel` (result `tesSUCCESS`, since deletion is that transaction's intended action).
- **Incidental cleanup by a late signer:** a `TransactionProposalSign` submitted against a terminal proposal **fails** with `tecEXPIRED` — its intended action (recording a signature) cannot happen — but, as a side effect of that claimed-fee result, it deletes the terminal proposal and releases the reserve (see §6.4).
- **Automatic cleanup when the proposed transaction executes:** the reserved `TicketSequence` can only be consumed by the proposal's own proposed transaction (§4.2.1), so this is the only way a ticket consumption deletes a proposal — running the completed transaction spends the ticket, and the ledger looks up `hash(<space key>, Account, <consumed ticket>)` (§4.1) and deletes the matching proposal, refunding the `Owner`'s reserve.

This removes only the leftover object. Signatures already copied off-ledger stay valid and submittable until the `TicketSequence` is consumed (§13.4).

**Account Deletion Blocker:** Yes. A `TransactionProposal` object must be deleted before its owner account can be deleted.

### 4.6. Invariants

- `Expiration` is always present and non-zero.
- Every entry in `ProposedTransaction.Signers` is unique by `Account`, and the array is sorted by `Account` with at most 32 entries.
- Every entry in `ProposedTransaction.BatchSigners`, if present, is unique by `Account`, and the array is sorted by `Account` with at most 24 entries.
- Every entry in `ProposedTransaction.Signers` is a signature that was cryptographically valid over the proposed transaction (excluding its `Signers` field) at the time it was added.
- Only the proposed transaction's signature fields change over the life of the proposal — its top-level `SigningPubKey`/`TxnSignature` (empty at creation; filled only when the target account signs with its own key, §6.1.2), `Signers`, `CounterpartySignature`, `SponsorSignature`, and `BatchSigners`. Every non-signature field is fixed at creation.

### 4.7. Example JSON

```json
{
  "LedgerEntryType": "TransactionProposal",
  "Flags": 0,
  "Owner": "rPROPOSER........................",
  "Expiration": 800000000,
  "ProposedTransaction": {
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

| Field Name            | Required? | JSON Type | Internal Type | Default Value               | Description                                                            |
| --------------------- | --------- | --------- | ------------- | --------------------------- | ---------------------------------------------------------------------- |
| `TransactionType`     | ✔️        | string    | UINT16        | `TransactionProposalCreate` | Identifies this as a `TransactionProposalCreate` transaction.          |
| `Account`             | ✔️        | string    | ACCOUNT       | N/A                         | The proposer submitting the proposal.                                  |
| `ProposedTransaction` | ✔️        | object    | STOBJECT      | N/A                         | The unsigned proposed transaction (see §4.2.1).                        |
| `Expiration`          | ✔️        | number    | UINT32        | N/A                         | Ledger close-time after which the proposal stops accepting signatures. |

Standard common fields (`Fee`, `Sequence`, `Flags`, `Memos`, `SourceTag`, signing fields) apply. `Memos` and `SourceTag` MAY be used to attach a reason code or reconciliation identifier to the proposal.

### 5.2. Transaction Fee

**Fee Structure:** Standard. This transaction uses the standard transaction fee (currently 10 drops, subject to Fee Voting changes). Note that the proposed transaction's own `Fee` is not charged here; it is charged to the target account when the completed transaction is submitted.

### 5.3. Failure Conditions

#### 5.3.1. Data Verification

All Data Verification failures return a `tem`-level error.

1. `ProposedTransaction` is missing or is not a well-formed transaction of a known type (`temMALFORMED`).
2. The proposed transaction fails the **stateless format checks (preflight) for its own transaction type**. These are the same checks it would receive if submitted directly, except for signature-presence and signature-verification checks because the payload is intentionally unsigned (§4.2.1). If any check fails, the proposal returns the `tem` code from that transaction type's preflight. Running these checks at creation is cheap and rejects malformed payloads immediately, instead of letting an invalid proposal gather signatures only to fail later. State-dependent (preclaim) checks are **not** run here; they are evaluated when the completed transaction is submitted.
3. The proposed transaction has a non-empty `SigningPubKey` or includes a `TxnSignature`, `Signers`, `CounterpartySignature`, `SponsorSignature`, or `BatchSigners` field (`temBAD_SIGNER`).
4. The proposed transaction cannot be independently submitted through the ordinary multi-sign path — it is itself a `TransactionProposalCreate`, `TransactionProposalSign`, or `TransactionProposalCancel`; a pseudo-transaction (`EnableAmendment`, `SetFee`, `UNLModify`); or carries the `tfInnerBatchTxn` flag (`temINVALID`).
5. The proposed transaction does not specify `TicketSequence`, or specifies `Sequence` instead of or in addition to `TicketSequence` (`temSEQ_AND_TICKET`).
6. `Expiration` is missing or zero (`temMALFORMED`).

#### 5.3.2. Protocol-Level Failures

1. `Expiration` is already at or before the parent ledger's close time (`tecEXPIRED`).
2. The proposed transaction includes a `LastLedgerSequence` that is already at or before the current ledger sequence (`tecEXPIRED`).
3. The proposer has insufficient reserve to own the new `TransactionProposal` object (`tecINSUFFICIENT_RESERVE`).
4. The target account (the proposed transaction's `Account`) does not exist (`tecNO_TARGET`).
5. The target account is a pseudo-account (e.g. an AMM, Vault, or LoanBroker pseudo-account) and therefore cannot authorize a transaction through a `SignerList` (`tecNO_PERMISSION`).
6. A `TransactionProposal` with the same `ProposalID` already exists — i.e. a live proposal (owned by anyone) already targets the same account with the same `TicketSequence` (`tecDUPLICATE`, §4.1).
7. The proposed transaction's `TicketSequence` is not a valid `Ticket` of the target account (`tefNO_TICKET`).

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
  "ProposedTransaction": {
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

Appends one signature toward the proposed transaction to the proposal. A single, uniform contribution — `SigningFor` + `ProposalSignature` — supplies a signature for one account the proposed transaction requires authorization from. The ledger derives everything else from the proposed transaction and from `ProposalSignature.Account`: **where** the signature is recorded, and **whether** it is a single- or multi-signature. The contributed signature is nested in `ProposalSignature` so it does not conflict with the standard `SigningPubKey`/`TxnSignature` fields that authorize the `TransactionProposalSign` transaction itself. The outer `Account` only submits and pays for `TransactionProposalSign`; it does not identify the signer. If the proposal is already terminal, this transaction cannot record a signature and instead **fails with `tecEXPIRED`**, deleting the terminal proposal as a side effect (see §6.4).

### 6.1. Fields

| Field Name          | Required? | JSON Type | Internal Type | Default Value             | Description                                                                                                                          |
| ------------------- | --------- | --------- | ------------- | ------------------------- | ------------------------------------------------------------------------------------------------------------------------------------ |
| `TransactionType`   | ✔️        | string    | UINT16        | `TransactionProposalSign` | Identifies this as a `TransactionProposalSign` transaction.                                                                          |
| `Account`           | ✔️        | string    | ACCOUNT       | N/A                       | The account submitting and paying for this transaction. It does not need to be the signer identified by `ProposalSignature.Account`. |
| `ProposalID`        | ✔️        | string    | HASH256       | N/A                       | The ID of the `TransactionProposal` being signed.                                                                                    |
| `SigningFor`        | ✔️        | string    | ACCOUNT       | N/A                       | An account **in the proposed transaction** that requires a signature for it to be valid — i.e. any of its signature slots (§6.1.1).  |
| `ProposalSignature` | ✔️        | object    | STOBJECT      | N/A                       | The contributed signature: `Account`, `SigningPubKey`, and `TxnSignature` over `SigningFor`'s signing data (§6.1.2).                 |

`ProposalSignature` contains three required fields: `Account`, `SigningPubKey`, and `TxnSignature`. `ProposalSignature.Account` is the signer account ID used for authorization checks and for the stored signature entry. The outer transaction `Account` can be any funded account willing to submit and pay the fee.

#### 6.1.1. `SigningFor` — which account is being authorized, and where the signature lands

`SigningFor` answers the question: **whose approval is this signature providing?** It must name an account that the **proposed transaction** needs a signature from. In other words, `SigningFor` must point to one of the proposed transaction's signature slots:

- the proposed transaction's own `Account`, or its `Delegate` if permission delegation is used;
- the `Counterparty`, if that transaction type has one (for example, a [`LoanSet` (XLS-66)](../XLS-0066-lending-protocol/README.md) lender; if omitted, this defaults to the `LoanBroker.Owner`, XLS-66 §3.8);
- the `Sponsor`, if the transaction is sponsored ([XLS-68](../XLS-0068-sponsored-fees-and-reserves/README.md));
- for a `Batch`, any account whose signature is needed for the batch, including each inner transaction's account and any additional account required by an inner transaction, such as its `Delegate`, `Counterparty`, or `Sponsor`. Each of these accounts is a batch **participant**.

If `SigningFor` does not match one of these required accounts, the transaction fails with `tecNO_PERMISSION`. When it does match, the ledger records the signature in the location that corresponds to that account's role:

| If `SigningFor` is the transaction's… | The signature is recorded in…                            |
| ------------------------------------- | -------------------------------------------------------- |
| `Account` / `Delegate`                | `ProposedTransaction.Signers` (or top-level, see §6.1.2) |
| `Counterparty`                        | `ProposedTransaction.CounterpartySignature`              |
| `Sponsor`                             | `ProposedTransaction.SponsorSignature`                   |
| `Batch` participant                   | `ProposedTransaction.BatchSigners[SigningFor]`           |

If the same account fills **more than one** role, such as being both the `Counterparty` and the `Sponsor`, the same contribution is recorded in **every** matching slot. Each slot is still validated independently. In most cases these roles are different accounts, so one contribution fills one slot.

#### 6.1.2. Single- vs multi-signature — derived from `ProposalSignature.Account`

The transaction does not include a flag that says whether the contribution is a single-signature or a multi-signature share. The ledger determines that from the relationship between `ProposalSignature.Account` and `SigningFor`:

- **`ProposalSignature.Account` == `SigningFor` → single-signature.** The account is signing for itself using its master key or regular key. `ProposalSignature.SigningPubKey` must be a valid key for `SigningFor`. This one signature fully authorizes `SigningFor`. The ledger stores it directly as `SigningPubKey`/`TxnSignature`: at the proposed transaction's **top level** for the main `Account` or `Delegate`, or inside the relevant `Counterparty`, `Sponsor`, or `Batch` participant signature slot.
- **`ProposalSignature.Account` != `SigningFor` → multi-signature share.** `ProposalSignature.Account` is contributing one multi-signature share for `SigningFor`. It must be in `SigningFor`'s applicable `SignerList`. The ledger stores the contribution as a standard `Signer` entry (`{Account, SigningPubKey, TxnSignature}`) in the relevant `Signers` array: `ProposedTransaction.Signers` for the main account, or the nested `Signers` array inside the `CounterpartySignature`, `SponsorSignature`, or participant `BatchSigner` slot. These entries are kept sorted and deduplicated by `Account`. More shares may be added until `SigningFor`'s quorum is reached.

### 6.2. Transaction Fee

**Fee Structure:** Standard. The submitter pays the standard fee for this transaction. The proposed transaction's own `Fee` is not charged here; it is charged to the target account when the completed transaction is submitted.

### 6.3. Failure Conditions

#### 6.3.1. Data Verification

All Data Verification failures return a `tem`-level error.

1. `ProposalID` is missing or malformed (`temMALFORMED`).
2. `SigningFor`, `ProposalSignature`, `ProposalSignature.Account`, `ProposalSignature.SigningPubKey`, or `ProposalSignature.TxnSignature` is missing (`temMALFORMED`).
3. `ProposalSignature.TxnSignature` is not valid over `SigningFor`'s signing data for the proposed transaction (§6.1.2) (`temBAD_SIGNATURE`).

#### 6.3.2. Protocol-Level Failures

1. No `TransactionProposal` object exists with the given `ProposalID` (`tecNO_ENTRY`).
2. The proposal is terminal — its `Expiration` has passed, or the proposed transaction's `LastLedgerSequence` has passed (`tecEXPIRED`). This is a claimed-fee failure: no signature is recorded, but the terminal proposal is deleted as a side effect (see §6.4). This condition is checked before the authorization conditions below.
3. `SigningFor` is not an account the proposed transaction requires a signature from — it is not the transaction's `Account`/`Delegate`, its `Counterparty`, its `Sponsor`, or (for a `Batch`) an account owning an inner transaction in `RawTransactions` (`tecNO_PERMISSION`).
4. The signer is not authorized: for single-signing, `ProposalSignature.SigningPubKey` is not `SigningFor`'s master or regular key; for multi-signing, `ProposalSignature.Account` is not on `SigningFor`'s applicable `SignerList`, or `ProposalSignature.SigningPubKey` is not valid for `ProposalSignature.Account` under standard multi-sign rules (`tecNO_PERMISSION`).
5. The contribution is already recorded — `ProposalSignature.Account` is already present in that destination, or a single-signature entry for `SigningFor` already exists (`tecDUPLICATE`). (The same `ProposalSignature.Account` may still sign for a different `SigningFor`.)
6. The contribution conflicts with the existing authorization mode for `SigningFor` — a multi-signature share when a single-signature entry is already recorded, or vice versa (`tecNO_PERMISSION`).
7. Adding the share would exceed the maximum of 32 entries in the destination `Signers` array, or would add a `BatchSigner` past the 24-entry `BatchSigners` limit (`tecOVERSIZE`).

### 6.4. State Changes

**On Success (`tesSUCCESS`):**

- Validates the contribution and records it into the destination for `SigningFor`'s role and mode (§6.1.1, §6.1.2): a single-signature is written directly (top-level for the main account, or that slot's `SigningPubKey`/`TxnSignature`), and a multi-signature share is appended as a `Signer` entry into the relevant `Signers` array. Any `Signers` array is kept sorted by `Account`.
- No execution occurs. Once the collected signatures satisfy every signing requirement for the proposed transaction — the target account's quorum, plus a satisfied signature for each `Counterparty`/`Sponsor` the transaction requires, or, for a `Batch`, the outer account's quorum plus a satisfied authorization for every participant account — the proposal is **complete**: the `ProposedTransaction` field is a valid signed transaction that anyone can copy and submit (see §6.5).

**On failure against a terminal proposal (`tecEXPIRED`):**

- No signature is recorded. Because a `tec` result is still applied to the ledger, the terminal proposal object is deleted and the `Owner`'s `OwnerCount` is decremented (releasing the reserve) as a side effect. This mirrors how transactions like `EscrowFinish` and `CheckCash` report a claimed-fee failure while cleaning up an expired object. A signer whose `TransactionProposalSign` arrives after the proposal has expired therefore both fails and cleans up in one step.

### 6.5. Submitting the completed transaction

This specification introduces no on-ledger execution step, and no assembly is required. Once a proposal is complete, any observer simply:

1. Reads the `TransactionProposal` by `ProposalID`.
2. Copies the `ProposedTransaction` verbatim — it already contains the collected `Signers` (and, for a `Batch`, `BatchSigners`), sorted, and is a fully-formed signed transaction.
3. Submits it through the ordinary transaction path (e.g. the `submit` API).

The existing multi-sign (and, for a `Batch`, `BatchSigners`) validation then checks the signatures against the applicable accounts' current `SignerList`(s) and applies the transaction, charging its `Fee` to the target account. No field of On-Chain Cosigner appears on the submitted transaction — it is an ordinary transaction. Applying it consumes the target account's `TicketSequence`, which auto-deletes the proposal and refunds its reserve (§4.5).

### 6.6. Example JSON

The `TransactionProposalSign` transaction is trivial — `SigningFor` plus one signature. What matters is how it mutates the `TransactionProposal` object, so §6.6.1 walks through one case with the full object shown **before** and **after** every signature. The remaining variants (§6.6.2–§6.6.4) show only the `TransactionProposalSign` JSON and the resulting fragment of `ProposedTransaction`, since the routing rules are already covered by §6.1.1's table.

#### 6.6.1. Ordinary transaction — multi-sign shares accumulate to quorum

**Setup.** A `Payment` proposal for target account `rTARGET`, whose applicable `SignerList` is `{ rCEO: 4, rCFO: 3 }` with `SignerQuorum` 6. Freshly created, it holds no signatures:

```json
// TransactionProposal — before any signature   ·   status: pending · signed_weight 0 / quorum 6
{
  "LedgerEntryType": "TransactionProposal",
  "Flags": 0,
  "Owner": "rPROPOSER........................",
  "Expiration": 800000000,
  "ProposedTransaction": {
    "TransactionType": "Payment",
    "Account": "rTARGET..........................",
    "Destination": "rDEST............................",
    "Amount": "5000000000",
    "TicketSequence": 1201,
    "Fee": "10",
    "SigningPubKey": ""
  },
  "OwnerNode": "0000000000000000",
  "PreviousTxnID": "F3B1000000000000000000000000000000000000000000000000000000000000",
  "PreviousTxnLgrSeq": 12345678
}
```

**`rCEO` signs.** `ProposalSignature.Account` (`rCEO`) ≠ `SigningFor` (`rTARGET`) → **multi-sign**:

```json
// TransactionProposalSign carrying rCEO's proposal signature
{
  "TransactionType": "TransactionProposalSign",
  "Account": "rCEO............................",
  "Fee": "10",
  "Sequence": 7,
  "ProposalID": "C1A2B3D4E5F6...............................",
  "SigningFor": "rTARGET..........................",
  "ProposalSignature": {
    "Account": "rCEO............................",
    "SigningPubKey": "03AB...",
    "TxnSignature": "3045..."
  }
}
```

The object gains one `ProposedTransaction.Signers` entry. Weight 4 < quorum 6, so it stays pending:

```json
// TransactionProposal — after rCEO   ·   status: pending · signed_weight 4 / quorum 6
{
  "LedgerEntryType": "TransactionProposal",
  "Flags": 0,
  "Owner": "rPROPOSER........................",
  "Expiration": 800000000,
  "ProposedTransaction": {
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
  "PreviousTxnID": "A1A1000000000000000000000000000000000000000000000000000000000000",
  "PreviousTxnLgrSeq": 12345690
}
```

**`rCFO` signs** (same shape, `SigningFor: rTARGET`, `ProposalSignature.Account: rCFO`). The new share is inserted **sorted by `Account`**, and weight 4 + 3 = 7 ≥ 6 → **complete**:

```json
// TransactionProposal — after rCFO   ·   status: complete
{
  "LedgerEntryType": "TransactionProposal",
  "Flags": 0,
  "Owner": "rPROPOSER........................",
  "Expiration": 800000000,
  "ProposedTransaction": {
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
      },
      {
        "Signer": {
          "Account": "rCFO............................",
          "SigningPubKey": "02DE...",
          "TxnSignature": "3044..."
        }
      }
    ]
  },
  "OwnerNode": "0000000000000000",
  "PreviousTxnID": "B2B2000000000000000000000000000000000000000000000000000000000000",
  "PreviousTxnLgrSeq": 12345702
}
```

The `ProposedTransaction` field is now a valid multi-signed `Payment`; anyone can copy it and submit it (§6.5).

#### 6.6.2. Ordinary transaction — single-sign with the account's own key

If `rTARGET` instead authorizes with its **own** key — `ProposalSignature.Account` == `SigningFor` (`rTARGET`) → **single-sign** — the signature fills the proposed transaction's **top-level** `SigningPubKey`/`TxnSignature` (no `Signers` array), and alone completes it:

```json
// TransactionProposalSign carrying rTARGET's proposal signature
{
  "TransactionType": "TransactionProposalSign",
  "Account": "rTARGET..........................",
  "Fee": "10",
  "Sequence": 4,
  "ProposalID": "C1A2B3D4E5F6...............................",
  "SigningFor": "rTARGET..........................",
  "ProposalSignature": {
    "Account": "rTARGET..........................",
    "SigningPubKey": "02FF...",
    "TxnSignature": "3046..."
  }
}
```

The proposed transaction's top level gains just the two signature fields — no `Signers` array is used:

```json
// ProposedTransaction fragment — after rTARGET signs for itself   ·   status: complete
{
  "SigningPubKey": "02FF...",
  "TxnSignature": "3046..."
}
```

#### 6.6.3. Auxiliary co-signature — a `LoanSet` counterparty

**Setup.** A `LoanSet` proposal: borrower `rBORROWER` (target account) with the lender `rLENDER` as `Counterparty`. The borrower's account is collected into `ProposedTransaction.Signers`; the lender co-signs into `ProposedTransaction.CounterpartySignature`. Suppose the borrower's quorum is already met and only the lender is outstanding:

```json
// TransactionProposal — before the lender signs   ·   status: pending (CounterpartySignature missing)
{
  "LedgerEntryType": "TransactionProposal",
  "Flags": 0,
  "Owner": "rBORROWER.......................",
  "Expiration": 800000000,
  "ProposedTransaction": {
    "TransactionType": "LoanSet",
    "Account": "rBORROWER.......................",
    "Counterparty": "rLENDER.........................",
    "LoanBrokerID": "9F1E...",
    "TicketSequence": 77,
    "Fee": "10",
    "SigningPubKey": "",
    "Signers": [
      {
        "Signer": {
          "Account": "rBORROWERKEY....................",
          "SigningPubKey": "03BB...",
          "TxnSignature": "3045..."
        }
      }
    ]
  },
  "OwnerNode": "0000000000000000",
  "PreviousTxnID": "D4D4000000000000000000000000000000000000000000000000000000000000",
  "PreviousTxnLgrSeq": 12345710
}
```

**The lender single-signs** (`SigningFor: rLENDER`, `ProposalSignature.Account: rLENDER`). A new `CounterpartySignature` field appears, and every slot is now satisfied → **complete**:

```json
// TransactionProposalSign carrying rLENDER's proposal signature
{
  "TransactionType": "TransactionProposalSign",
  "Account": "rLENDER.........................",
  "Fee": "10",
  "Sequence": 5,
  "ProposalID": "E5E6...............................",
  "SigningFor": "rLENDER.........................",
  "ProposalSignature": {
    "Account": "rLENDER.........................",
    "SigningPubKey": "03CD...",
    "TxnSignature": "3047..."
  }
}
```

The proposed transaction gains a new top-level field for the auxiliary signature, alongside the borrower's existing `Signers`:

```json
// ProposedTransaction fragment — after the lender signs   ·   status: complete
{
  "CounterpartySignature": {
    "SigningPubKey": "03CD...",
    "TxnSignature": "3047..."
  }
}
```

A **multi-sign** lender would instead accumulate into `CounterpartySignature.Signers` — a nested array filling until the lender's own quorum is met, exactly like `ProposedTransaction.Signers` in §6.6.1. A `SponsorSignature` (for a sponsored transaction) behaves identically.

#### 6.6.4. `Batch` — outer account plus participants

**Setup.** A multi-account `Batch` by outer account `rOUTER`, with inner transactions for `rOUTER`, `rBOB`, and `rCAROL`. Authorizations: the outer account `rOUTER` into `ProposedTransaction.Signers`; each other participant into `ProposedTransaction.BatchSigners[account]`. `SignerList`s: `rOUTER = { rOUTERKEY: 1 }` quorum 1; `rBOB` signs with its own key; `rCAROL = { rCAROLKEY: 1 }` quorum 1.

```json
// TransactionProposal — before any signature   ·   status: pending
{
  "LedgerEntryType": "TransactionProposal",
  "Flags": 0,
  "Owner": "rPROPOSER2......................",
  "Expiration": 800000000,
  "ProposedTransaction": {
    "TransactionType": "Batch",
    "Account": "rOUTER..........................",
    "Flags": 65536,
    "TicketSequence": 500,
    "Fee": "60",
    "SigningPubKey": "",
    "RawTransactions": [
      {
        "RawTransaction": {
          "TransactionType": "Payment",
          "Account": "rOUTER..........................",
          "Destination": "rX..............................",
          "Amount": "1000000",
          "Flags": 1073741824,
          "Sequence": 501,
          "Fee": "0",
          "SigningPubKey": ""
        }
      },
      {
        "RawTransaction": {
          "TransactionType": "Payment",
          "Account": "rBOB............................",
          "Destination": "rY..............................",
          "Amount": "2000000",
          "Flags": 1073741824,
          "Sequence": 88,
          "Fee": "0",
          "SigningPubKey": ""
        }
      },
      {
        "RawTransaction": {
          "TransactionType": "Payment",
          "Account": "rCAROL..........................",
          "Destination": "rZ..............................",
          "Amount": "3000000",
          "Flags": 1073741824,
          "Sequence": 12,
          "Fee": "0",
          "SigningPubKey": ""
        }
      }
    ]
  },
  "OwnerNode": "0000000000000000",
  "PreviousTxnID": "A9C7000000000000000000000000000000000000000000000000000000000000",
  "PreviousTxnLgrSeq": 12345700
}
```

Three signatures arrive — one per account that must authorize:

```json
// 1) rOUTERKEY signs for the outer account rOUTER (multi-sign) → ProposedTransaction.Signers
{
  "TransactionType": "TransactionProposalSign",
  "Account": "rOUTERKEY.......................",
  "Fee": "10",
  "Sequence": 3,
  "ProposalID": "F0F0...............................",
  "SigningFor": "rOUTER..........................",
  "ProposalSignature": {
    "Account": "rOUTERKEY.......................",
    "SigningPubKey": "03A1...",
    "TxnSignature": "3045..."
  }
}
```

```json
// 2) rBOB signs for itself (single-sign) → BatchSigners[rBOB]
{
  "TransactionType": "TransactionProposalSign",
  "Account": "rBOB............................",
  "Fee": "10",
  "Sequence": 9,
  "ProposalID": "F0F0...............................",
  "SigningFor": "rBOB............................",
  "ProposalSignature": {
    "Account": "rBOB............................",
    "SigningPubKey": "02B2...",
    "TxnSignature": "3044..."
  }
}
```

```json
// 3) rCAROLKEY signs for rCAROL (multi-sign) → BatchSigners[rCAROL].Signers
{
  "TransactionType": "TransactionProposalSign",
  "Account": "rCAROLKEY.......................",
  "Fee": "10",
  "Sequence": 4,
  "ProposalID": "F0F0...............................",
  "SigningFor": "rCAROL..........................",
  "ProposalSignature": {
    "Account": "rCAROLKEY.......................",
    "SigningPubKey": "03C3...",
    "TxnSignature": "3046..."
  }
}
```

After all three, the outer account's quorum is met **and** every participant is authorized → **complete**. `BatchSigners` is sorted by `Account`; `rBOB` is a single-signature entry, `rCAROL` a nested multi-sign one. `RawTransactions` is unchanged from the setup above, so only the new signature fields are shown:

```json
// ProposedTransaction fragment — after all three   ·   status: complete
{
  "Signers": [
    {
      "Signer": {
        "Account": "rOUTERKEY.......................",
        "SigningPubKey": "03A1...",
        "TxnSignature": "3045..."
      }
    }
  ],
  "BatchSigners": [
    {
      "BatchSigner": {
        "Account": "rBOB............................",
        "SigningPubKey": "02B2...",
        "TxnSignature": "3044..."
      }
    },
    {
      "BatchSigner": {
        "Account": "rCAROL..........................",
        "Signers": [
          {
            "Signer": {
              "Account": "rCAROLKEY.......................",
              "SigningPubKey": "03C3...",
              "TxnSignature": "3046..."
            }
          }
        ]
      }
    }
  ]
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

- **Non-terminal proposal:** the **owner** (the proposal's `Owner`, i.e. the proposer) or the **target account** (the proposed transaction's `Account` or `Delegate`) may cancel.
- **Terminal proposal:** **Any** account may cancel, to clean up the object and release the owner's reserve.

The target account can cancel at any point in the lifecycle — even after the proposal is complete — without owning the object. Since anyone can create a proposal against any account, and doing so reserves one of that account's tickets (§5.4), the target account needs a way to refuse; cancelling clears the proposal and frees the ticket.

Cancellation is only fully effective before a proposal is complete. If a quorum-weight of valid signatures has already been collected, an observer may have copied them and can still submit the completed transaction even after the proposal object is gone; see §13.4.

### 7.3. Failure Conditions

#### 7.3.1. Data Verification

1. `ProposalID` is missing or malformed (`temMALFORMED`).

#### 7.3.2. Protocol-Level Failures

1. No `TransactionProposal` object exists with the given `ProposalID` (`tecNO_ENTRY`).
2. The proposal is not terminal and `Account` is neither the `Owner` nor the target account (`tecNO_PERMISSION`).

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

## 8. API

To use a proposal, a signer or wallet has to fetch it and see how far along it is. This proposal introduces a new `transaction_proposal` RPC for retrieving one `TransactionProposal` and its computed status. (Listing the proposals an account owns is already covered by [`account_objects`](https://xrpl.org/docs/references/http-websocket-apis/public-api-methods/account-methods/account_objects) with a `TransactionProposal` type filter; no dedicated listing method is introduced.)

### 8.1. RPC: `transaction_proposal`

Returns a `TransactionProposal` by ID, or by the target account and proposed transaction ticket, together with a computed, per-account view of how far the proposal is from a submittable transaction.

#### 8.1.1. Request Fields

| Field          | Type             | Required | Description                                                                                                                                                           |
| -------------- | ---------------- | -------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `proposal_id`  | string           | No       | The `ProposalID` (§4.1). Required unless `account` and `ticket_seq` are provided.                                                                                     |
| `account`      | string           | No       | The target account. Used with `ticket_seq` to derive the `ProposalID`. Required unless `proposal_id` is provided.                                                     |
| `ticket_seq`   | number           | No       | The proposed transaction's `TicketSequence`. Used with `account` to derive the `ProposalID`. Required unless `proposal_id` is provided. Numeric strings are accepted. |
| `ledger_hash`  | string           | No       | A 32-byte hex string identifying the ledger to query.                                                                                                                 |
| `ledger_index` | string or number | No       | The ledger index, or a shortcut such as `"validated"`.                                                                                                                |

`account` + `ticket_seq` is the same addressing `ledger_entry` accepts for a `transaction_proposal` object; the two methods accept identical field types and return identical error codes for malformed addressing.

#### 8.1.2. Response Fields

The response returns the raw ledger object plus **computed convenience fields** so a client does not have to join the collected signatures against live `SignerList`s itself:

| Field             | Type   | Description                                                                                                                                                                                                                              |
| ----------------- | ------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `proposal_id`     | string | The ID of the `TransactionProposal`.                                                                                                                                                                                                     |
| `proposal`        | object | The raw `TransactionProposal` ledger object.                                                                                                                                                                                             |
| `proposal_status` | string | Where the proposal is in its lifecycle: `"pending"`, `"complete"`, or `"expired"` (see below).                                                                                                                                           |
| `signing_status`  | array  | One entry per required authorization (§8.1.3.1), in a stable order: the initiator first, then auxiliary co-signers, then batch participants.                                                                                             |
| `tx_blob`         | string | Present only when `proposal_status` is `"complete"`: the stored `ProposedTransaction` serialized in submit-ready binary form, so a client does not have to reassemble and re-serialize it. Providing it implies nothing beyond §8.1.3.4. |

> The field is named `proposal_status`, not `status`, because `status` is already the RPC envelope's success/error indicator and the two would collide in the same JSON object.

Each `signing_status` entry:

| Field           | Type    | Description                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    |
| --------------- | ------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `account`       | string  | The account whose authorization is required.                                                                                                                                                                                                                                                                                                                                                                                                                                                   |
| `signed`        | boolean | Whether the signature material collected so far currently authorizes this account on the queried ledger (§8.1.3.2).                                                                                                                                                                                                                                                                                                                                                                            |
| `reason`        | string  | Present only when `signed` is `false`: why (see below).                                                                                                                                                                                                                                                                                                                                                                                                                                        |
| `signed_weight` | number  | (Optional, present on Accounts with SignerList only) Present only when a `Signers` array has been collected for this row: its weight against the account's live `SignerList`.                                                                                                                                                                                                                                                                                                                  |
| `quorum`        | number  | (Optional, present on Accounts with SignerList only) Present only when the account has a live `SignerList`: its `SignerQuorum`.                                                                                                                                                                                                                                                                                                                                                                |
| `signers`       | array   | (Optional, present on Accounts with SignerList only) Present only when the account has a live `SignerList`: one entry per list member — `{account, weight, signed}` — where `signed` is whether a currently-valid signature from that member has been collected. This is the list a wallet chases: every member with `signed: false` is a candidate next signer. Collected signatures from accounts _not_ on the live list do not appear here; they surface as `reason: "invalid_signer_set"`. |

Rows are keyed by the pair (`account`, `role`), not by `account` alone. The same account can owe two independent authorizations through different signature slots — for example, the fee sponsor of a proposed `Batch` who is also an inner participant signs once through `SponsorSignature` and once through `BatchSigners` — and each slot succeeds or fails on its own.

`reason` values:

| Value                            | Meaning                                                                                                                                                                                                                       |
| -------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `inadequate_signatures`          | `bool`                                                                                                                                                                                                                        | In the case of Single-Sign configuration, the account has not received any signatures. In the case of Multi-Sign configuration, the received signatures do not yet satisfy the requisite quorum |
| `invalid_signer_set`             | The collected `Signers` array contains an entry the live `SignerList` does not authorize; submission rejects the set wholesale. This occurs when the Account has removed a Signer from its erstwhile SignerList configuration |
| `no_signer_list`                 | A `Signers` array is collected but the account has no `SignerList` on the queried ledger. This error occurs when the Account had a SignerList but has since deleted it and switched to a SingleSign configuration             |
| `master_disabled`                | The collected signature is by the master key, and the master key has since been disabled. This is caused by the updated ledger-state since the collection of this signature.                                                  |
| `not_authorized`                 | The signing key does not currently authorize the account (e.g. a rotated regular key).                                                                                                                                        |
| `account_not_found`              | The account does not exist on the queried ledger (and is not one an earlier inner transaction of the proposed `Batch` would create).                                                                                          |
| `awaiting_sponsorship_signature` | Sponsor rows only: an on-ledger `Sponsorship` entry exists, but its flags require a co-signature for what this transaction sponsors.                                                                                          |
| `malformed`                      | The stored signature material is not usable (defensive; should be unreachable through `TransactionProposalSign`).                                                                                                             |

`proposal_status` is the single field a client switches on:

- **`pending`** — still collecting: at least one `signing_status` row is unsatisfied.
- **`complete`** — every `signing_status` row is satisfied, so the stored `ProposedTransaction` is ready to copy and submit (§6.5). See §8.1.3.4 for what `complete` does **not** guarantee.
- **`expired`** — the proposal is terminal (§4.5): its `Expiration` has passed, or the proposed transaction's `LastLedgerSequence` has passed (§8.1.3.3). It no longer accepts signatures and can be cleaned up by anyone.

`proposal_status` is evaluated terminal-first: a proposal that is terminal reports `expired` even if every authorization is satisfied (the proposal object is dead and cleanable, though its already-collected signatures may still be independently submittable — see §13.4). Otherwise it reports `complete` if the requirements are met, else `pending`.

The computed fields are derived from live ledger state at the queried ledger and are not stored on the object. Querying the same proposal at different ledgers can give different answers — that is the point.

#### 8.1.3. Completeness Evaluation

##### 8.1.3.1. Required Authorizations

The server derives the set of required authorizations from the stored `ProposedTransaction`, mirroring exactly what submission-time validation will demand:

| Role                | Required when                                                                                                                                                                                                                                                    | Signature slot                                                        |
| ------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------- |
| `account`           | Always: the transaction's initiator — its `Account`, or its `Delegate` when present.                                                                                                                                                                             | Top-level `SigningPubKey`/`TxnSignature`, or `Signers`                |
| `counterparty`      | The transaction carries a `Counterparty`; or it is a `LoanSet` (XLS-0066) without one, in which case the required co-signer is the owner of the `LoanBroker` it names.                                                                                           | `CounterpartySignature`                                               |
| `sponsor`           | The transaction carries a `Sponsor` (XLS-0068).                                                                                                                                                                                                                  | `SponsorSignature`, or exemption via a `Sponsorship` entry (§8.1.3.2) |
| `batch_participant` | The transaction is a `Batch` (XLS-0056): one row per distinct inner-transaction initiator other than the outer account. Inner counterparties and inner co-signing sponsors (other than the outer account) are likewise required, reported under their own roles. | That account's `BatchSigners` entry                                   |

An inner transaction initiated by the outer account adds no row: the outer account authorizes all of its inners by signing the batch itself.

##### 8.1.3.2. Authorization, Not Cryptography

Each signature was cryptographically verified when `TransactionProposalSign` appended it (§6.3.2), and ledger data cannot change after that. What _can_ change is whether the signature still **authorizes** the account, so `signed` is computed by re-applying the standard authorization rules against the queried ledger — the same rules submission applies:

- A single signature must be by the account's current regular key, or by its master key while the master key is enabled.
- A collected `Signers` array is validated against the account's **live** `SignerList`, and it fails **as a whole** if _any_ collected entry is not currently authorized: an entry absent from the list, one whose master key has since been disabled, one whose regular key has since rotated, or a non-phantom entry whose account no longer exists each void the entire set at submission (`tefBAD_SIGNATURE` / `tefMASTER_DISABLED`). Otherwise the set's weight must meet the live `SignerQuorum`. Because signatures only ever accumulate on a proposal, a voided set cannot be repaired by further signing — the practical remedy is `TransactionProposalCancel` and a fresh proposal.
- A `BatchSigners` entry for an account that does not exist yet is authorized only by that account's own master key (an earlier inner transaction may create the account).
- A sponsor row is satisfied by a valid `SponsorSignature`, or — only while no `SponsorSignature` field has been collected at all — by an on-ledger `Sponsorship` entry between the sponsor and the initiator whose flags do not require a co-signature for what this transaction sponsors. A collected-but-no-longer-authorizing `SponsorSignature` is **not** rescued by the exemption, because submission validates a present `SponsorSignature` unconditionally.

Consequently a signature that counted yesterday may not count today (disabled master key, rotated regular key, replaced `SignerList`), and `signed_weight` can even meet `quorum` while `signed` is `false` (`invalid_signer_set`). Clients must treat `signed` as authoritative and the numbers as progress detail.

##### 8.1.3.3. Expiry Bounds

`expired` is reported when either terminal condition of §4.5 holds at the queried ledger:

- `Expiration`: the queried ledger's parent close time has reached or passed the proposal's `Expiration`.
- `LastLedgerSequence`: the proposed transaction can no longer be included in any ledger. The earliest ledger it could still enter is the queried ledger itself when that ledger is open, and the next ledger otherwise — so the proposal is expired when `LastLedgerSequence` is below that bound. (A transaction with `LastLedgerSequence` equal to the current open ledger's sequence is still submittable and reports `pending`/`complete`, not `expired`.)

##### 8.1.3.4. `complete` Is an Authorization Verdict

`complete` asserts that every required authorization is satisfied on the queried ledger — no more. It does not re-validate everything submission will: the ticket the proposal is keyed on may never have been created (`tefNO_TICKET`), the target account may since have been deleted, the fixed `Fee` may be unfundable, or an amendment the transaction needs may have been disabled. Clients should treat `complete` as "assemble and submit now, and expect success under normal conditions", not as a guarantee of `tesSUCCESS`.

`complete` is also only as fresh as the ledger it was computed against. Signatures are immutable once collected, but the ledger state they are judged against is not, and submission applies gates beyond signature authorization that this RPC does not model. Examples of state changes that can silently invalidate a `complete` verdict:

- **Deleting the `LoanBroker`** an implicit counterparty was resolved from: the completed `LoanSet` then fails `temBAD_SIGNER` at submission, because the counterparty is re-resolved from the live broker at that time.
- **Revoking or narrowing a delegation** (`DelegateSet`): a delegate's on-ledger _permission_ for the proposed transaction type is a submission-time gate separate from — and not attested by — the delegate's signature.
- **The exact-set rule for a proposed `Batch`**: submission requires the stored `BatchSigners` array to correspond exactly to the required signer set (sorted, unique, no extras, never the outer account), and rejects any mismatch wholesale (`temBAD_SIGNER`); this structural property is likewise not attested by the per-row verdicts.

For the most accurate result, invoke this RPC against the **most recent validated ledger** and treat the verdict as point-in-time: re-evaluate immediately before assembling and submitting the completed transaction, since any intervening ledger may have changed the answer.

#### 8.1.4. Failure Conditions

- Neither `proposal_id` nor both `account` and `ticket_seq` are present, or `proposal_id` is combined with them (`invalidParams`).
- `proposal_id` is not a 256-bit hex string (`malformedRequest`).
- `account` is not a valid account address (`malformedAddress`).
- `ticket_seq` is not a number or numeric string (`malformedRequest`).
- No `TransactionProposal` exists at the derived ID in the queried ledger — including when the index names a ledger entry of a different type (`entryNotFound`).
- The requested ledger is not available (`lgrNotFound`).

#### 8.1.5. Example Request

```json
{
  "command": "transaction_proposal",
  "account": "rTARGET..........................",
  "ticket_seq": 1201,
  "ledger_index": "validated"
}
```

#### 8.1.6. Example Responses

An ordinary (non-batch) proposal mid-collection — the target multi-signs, two of six weight collected:

```json
{
  "proposal_id": "C1A2B3D4E5F6...............................",
  "proposal": {
    "LedgerEntryType": "TransactionProposal",
    "Owner": "rPROPOSER........................",
    "Expiration": 800000000,
    "ProposedTransaction": {
      "TransactionType": "Payment",
      "Account": "rTARGET..........................",
      "TicketSequence": 1201,
      "...": "..."
    }
  },
  "proposal_status": "pending",
  "signing_status": [
    {
      "account": "rTARGET..........................",
      "role": "account",
      "signed": false,
      "reason": "below_quorum",
      "signed_weight": 2,
      "quorum": 6,
      "signers": [
        {
          "account": "rSIGNER1.........................",
          "weight": 2,
          "signed": true
        },
        {
          "account": "rSIGNER2.........................",
          "weight": 2,
          "signed": false
        },
        {
          "account": "rSIGNER3.........................",
          "weight": 2,
          "signed": false
        }
      ]
    }
  ],
  "ledger_index": 12345678,
  "validated": true
}
```

A proposed `Batch` — the motivating case for this design. The outer account has signed; one participant authorizes through its own `SignerList` and is below quorum; an inner `LoanSet`'s counterparty has not signed at all:

```json
{
  "proposal_id": "D4E5F6A1B2C3...............................",
  "proposal": { "...": "..." },
  "proposal_status": "pending",
  "signing_status": [
    {
      "account": "rOUTER...........................",
      "role": "account",
      "signed": true
    },
    {
      "account": "rLENDER..........................",
      "role": "counterparty",
      "signed": false,
      "reason": "no_signature"
    },
    {
      "account": "rPARTICIPANT.....................",
      "role": "batch_participant",
      "signed": false,
      "reason": "below_quorum",
      "signed_weight": 1,
      "quorum": 2,
      "signers": [
        {
          "account": "rPCOSIGNER1......................",
          "weight": 1,
          "signed": true
        },
        {
          "account": "rPCOSIGNER2......................",
          "weight": 1,
          "signed": false
        }
      ]
    }
  ],
  "ledger_index": 12345679,
  "validated": true
}
```

## 9. Rationale

### 9.1. Why collect signatures on-ledger

The problem multi-sign users actually face is not the cryptography of signing — it is coordination: sharing the exact payload, gathering signatures, and getting them submitted without a trusted middleman. On-Chain Cosigner keeps the standard multi-sign signatures but moves their collection point from a coordinator's inbox to an immutable ledger object. Every signer signs the same immutable payload; every signature is validated on arrival; and the collected set is always available to everyone. This removes the coordinator as a single point of failure — there is no blob to lose, no blob to swap, and, because the collected set is a standard multi-signed transaction, anyone can submit it.

### 9.2. Avoiding sequence invalidation with Tickets

Standard multi-sign forces every field to be fixed before the first signature. If a proposal used the target account's live `Sequence`, unrelated activity by that account could advance the sequence and invalidate the proposal while signatures were still being collected. On-Chain Cosigner therefore requires the proposed transaction to use `TicketSequence`. The collection window is bounded by the proposal's own `Expiration`; the proposed transaction's `LastLedgerSequence` (optional) separately bounds the _submission_ window.

### 9.3. How quorum is enforced

Quorum is never evaluated by a bespoke rule in this feature. Each signature is validated against the target account's `SignerList` when it is added (so garbage cannot accumulate), and the completed transaction is validated again by the existing multi-sign machinery when it is finally submitted. Both checks use the account's live `SignerList`, so the executed action always reflects the account's **current** authority model — including per-transaction-type lists resolved from the proposed transaction's type, exactly as in ordinary multi-sign under [XLS-49 (Multiple Signer Lists)](../XLS-0049-multiple-signer-lists/README.md).

### 9.4. Why there is no execution transaction

Because signatures are collected directly into the proposed transaction's own `Signers` field, a complete proposal _is_ a fully-signed multi-sign transaction waiting to be submitted — no assembly step exists to get wrong. Adding a dedicated on-ledger execute step (a fourth transaction, or auto-execution inside `TransactionProposalSign`) would duplicate logic the ledger already has and would couple execution to a specific submitter or to the moment a particular signature lands. Instead, execution reuses the ordinary submission path and any account may perform it. Proposal and execution stay decoupled — deleting the proposal does not revoke already-collected signatures (§13.4) — but the object is not left stranded: running the completed transaction consumes the target account's `TicketSequence`, which auto-deletes the proposal (§4.5).

## 10. Composability

- **Batch (XLS-56):** The proposed transaction may be a `Batch`, enabling multi-account, atomic, multi-signed settlement (e.g. end-of-day repo netting, flash-style capital operations). The outer account is authorized by `SigningFor` = the outer account (into `ProposedTransaction.Signers`); each participant account by `SigningFor` = that participant — single-signature (its own key) or multi-sign (§6.1). A signer authorized on several of the batch's accounts produces one `ProposalSignature` per account, since each signature is bound to its owning account. Once every participant's requirement is met the completed batch executes atomically. This is the primary motivating case for On-Chain Cosigner, since multi-account Batches otherwise require the most off-chain signature coordination.
- **Lending protocols:** A borrower can post a `LoanSet` (or equivalent) as a proposal; the lender signs on-chain as counterparty (`SigningFor` = the lender, §6.1) — single-key or multi-signed — which the ledger records in the proposed transaction's own `CounterpartySignature` field, while the borrower's account is authorized through `ProposedTransaction.Signers`. This turns loan origination into a trustless, asynchronous flow with no synchronous coordination.
- **Sponsored fees & reserves (XLS-68):** A user posts a transaction carrying `Sponsor`/`SponsorFlags`; the sponsor signs on-chain (`SigningFor` = the sponsor, §6.1) — single-key or multi-signed — which the ledger records in the proposed transaction's own `SponsorSignature` field, co-authorizing the fee/reserve sponsorship. This is the same auxiliary-co-signature mechanism used for a `LoanSet` counterparty, and the two can be collected on the same proposal (e.g. a sponsored `LoanSet`).
- **Multiple Signer Lists (XLS-49):** Per-transaction-type signer lists are honored automatically, since both the per-signature check and the final submission use standard multi-sign resolution for the proposed transaction's type.

## 11. Backwards Compatibility

This proposal is purely additive: it introduces one new ledger entry type and three new transaction types, all gated behind the `Cosigner` amendment. Existing multi-sign, `SignerListSet`, and off-chain signing workflows are unaffected and continue to function. Because a completed proposal is submitted through the ordinary multi-sign path, the multi-sign validation rules are unchanged. The one addition to the common path is a cleanup check: when any account consumes a `TicketSequence`, the ledger removes a matching `TransactionProposal` if one exists (§4.5). Accounts that do not use On-Chain Cosigner are not impacted.

## 12. Open Questions

- **Reducing the initial construction burden:** Can the initial proposed-transaction construction be simplified further, beyond the ticket-based approach in §9.2?
- **Revocation:** Should there be a first-class way to revoke a completed proposal's signatures on-ledger (beyond consuming the `TicketSequence`), given that cancellation alone does not prevent submission of already-collected signatures (§13.4)?
- **Recurring / standing orders:** Use Case 7 (recurring allowances and treasury stipends) suggests a proposal could activate a long-lived standing order rather than a one-shot transaction, potentially composing with a Subscriptions primitive. This is out of scope for this spec but noted as a future extension.

## 13. Security Considerations

### 13.1. Authority derives solely from the collected signatures

The completed transaction is authorized entirely by the collected signatures validated against the applicable key or `SignerList`(s) — never by the identity of the account that finally submits it. Submission grants no authority the collected signatures did not already confer, so anyone may submit. Likewise, `TransactionProposalSign` may be submitted by any funded account; authorization comes from `ProposalSignature.Account`, `ProposalSignature.SigningPubKey`, and `ProposalSignature.TxnSignature`.

### 13.2. Immutable payload

The proposed transaction is fixed at creation and cannot be altered by any subsequent transaction. Signers therefore always sign exactly what is stored, eliminating the manipulation risk of a coordinator presenting different payloads to different signers.

### 13.3. Every collected signature is pre-validated

Each `TransactionProposalSign` is rejected unless `ProposalSignature.TxnSignature` is cryptographically valid over the immutable proposed transaction and `ProposalSignature.Account` is authorized for the `SigningFor` account (the same account for single-signing, or a member of its applicable `SignerList`). This prevents an attacker from polluting a proposal with junk entries and guarantees that a complete proposal will pass standard signature validation at submission.

### 13.4. Cancellation does not revoke already-collected signatures

This is the central security consideration of the copy-and-submit model. The proposal object is a bulletin board, not an execution gate: once a quorum-weight of valid signatures has been collected, any observer may have copied them, and those signatures remain valid regardless of whether the proposal object still exists. Cancelling or expiring the proposal frees the reserve but does **not** guarantee the transaction will not execute. To positively prevent execution of a completed (or nearly-completed) proposal, the target account must consume the proposed transaction's `TicketSequence` with another transaction and/or rely on its `LastLedgerSequence` window elapsing. Architects and wallets should surface this clearly.

### 13.5. Stale signatures under SignerList changes

Because both the per-signature check and the final submission validate against the live `SignerList`, changing a `SignerList` while a proposal is pending is honored — but asymmetrically. Lowering the quorum can make a previously-incomplete set sufficient. Removing a collected signer (or a collected signer disabling their master key or rotating their regular key) does **not** merely subtract their weight: submission rejects the entire collected set (`tefBAD_SIGNATURE`), and since signatures only accumulate on a proposal, the proposal becomes permanently unsatisfiable and must be cancelled and re-proposed (§8.1.3.2). Modifying an account's `SignerList` therefore affects all pending proposals against that account.

### 13.6. Denial-of-service and reserve pressure

Each proposal consumes an elevated flat owner reserve (§4.4) held against the `Owner` — higher than a typical ledger entry, and higher still for a `Batch` — pricing the larger state burden and disincentivizing spam. Because every appended signature must be valid, an attacker cannot inflate a proposal with junk. Built-in expiry ensures abandoned proposals can always be cleaned up (by anyone, once terminal) so they do not accumulate indefinitely in ledger state.

Because anyone may propose against any account and there is one slot per `(target account, ticket)` (§4.1), an attacker could **squat** a slot the real proposer wanted, blocking it with `tecDUPLICATE`. Each attempt costs a full reserve, and tickets give the honest proposer far more slots than an attacker could block. The target account is also never stuck with an unwanted proposal: it may delete any proposal made for it via `TransactionProposalCancel` at any time (§7.2), clearing the slot and the reserved ticket regardless of who created the proposal or how far along it is.

### 13.7. Fee accountability

The proposed transaction's fee is paid by the target account when the completed transaction is submitted, consistent with the target account being the party that authorized the action via its signers. Each `TransactionProposalCreate`, `TransactionProposalSign`, and `TransactionProposalCancel` pays its own fee from its submitter.

# Appendix

## Appendix A: FAQ

### A.1: Who can create a proposal?

Any account. The proposer need not be a signer on the target account nor the target account itself. The proposer owns the object and pays its reserve.

### A.2: Can the target account be different from the proposer?

Yes. The target account is the `Account` of the proposed transaction; the proposer is the account that submits `TransactionProposalCreate`. This is what enables flows like a borrower proposing a `LoanSet` that a lender then signs.

### A.3: How does a signer know what they are signing?

The full proposed transaction is stored, immutable, in the `ProposedTransaction` field of the on-ledger object. A signer (or their wallet) reads the object by `ProposalID`, inspects the payload, signs exactly that payload, and includes it in `ProposalSignature`. The signer or any relayer can submit it via `TransactionProposalSign`.

### A.4: How is the proposed transaction actually executed?

There is no on-ledger execute step. Signatures accumulate inside the proposed transaction's own `Signers` field, so once quorum weight is reached the `ProposedTransaction` field is already a valid multi-signed transaction: any observer copies it verbatim and submits it through the normal transaction path. The existing multi-sign machinery validates and applies it. See §6.5.

### A.5: Does cancelling a proposal guarantee it won't execute?

Only if a quorum-weight of valid signatures has not yet been collected. Once enough signatures exist on-ledger, someone may have copied them and can still submit the completed transaction. To positively block execution, consume the proposed transaction's `TicketSequence` with another transaction or let its `LastLedgerSequence` elapse. See §13.4.

### A.6: What happens if quorum is never reached before expiry?

The proposal becomes terminal at `Expiration`, stops accepting signatures, and any account may submit `TransactionProposalCancel` to delete it and release the proposer's reserve. The full signing history remains in transaction metadata.

### A.7: Can there be multiple pending proposals against the same target account?

Yes, as long as each uses a distinct `TicketSequence`. A proposal's ID is derived from the target account and the proposed transaction's `TicketSequence` only (§4.1), so there is exactly one proposal slot per `(target account, ticket)`, shared across all proposers. Giving each proposed transaction a distinct `TicketSequence` lets many concurrent proposals coexist against the same target account without collisions.

### A.8: Why is the proposed transaction's fee paid by the target account and not the submitter?

The proposed transaction acts on behalf of the target account, authorized by that account's signers. Charging its fee to the target account keeps fee accountability with the party that authorized the action — it is, after all, an ordinary multi-signed transaction of the target account.

### A.9: How does signing work when the proposed transaction is a multi-account Batch?

As described in §6.1.1/§6.1.2, plus one Batch-specific wrinkle: an XLS-56 batch signature binds the owning account (`message = <batch data> + <owning account> + <signer account>`), so a signer authorized on several participant accounts must submit one `TransactionProposalSign` per account — a distinct signature and `SigningFor` each time. The same signer key can therefore appear across several participants' `BatchSigners`.

### A.10: How is a transaction with a second signer — a `LoanSet` counterparty or a sponsor — handled?

As described in §6.1.1/§4.2.2: each required party is named in its own `TransactionProposalSign` via `SigningFor`. Because the auxiliary signature fields are excluded from every party's signing data, the parties can sign in any order, and a transaction needing several (e.g. a sponsored `LoanSet`) collects them independently.

### A.11: Does this replace off-chain multi-sign?

No. Off-chain multi-sign and standard `SignerListSet` continue to work unchanged. On-Chain Cosigner is an additive, opt-in coordination layer for accounts that want the ledger to be the meeting room.
