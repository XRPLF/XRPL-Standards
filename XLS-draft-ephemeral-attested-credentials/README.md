<pre>
  title: Ephemeral Attested Credentials (E-APD)
  description: Hardware-attested short-TTL credentials, in-place renewal rollover, and deterministic venue ejection for XLS-80 Permissioned Domains.
  author: Corrente Applied Cryptography Group (@whawk46)
  category: Amendment
  status: Draft
  proposal-from: https://github.com/XRPLF/XRPL-Standards/discussions/656
  requires: [XLS-70](../XLS-0070-credentials/README.md), [XLS-80](../XLS-0080-permissioned-domains/README.md)
  created: 2026-10-06
  updated: 2026-10-22
</pre>

# Ephemeral Attested Credentials & Enclave-Gated Domains (E-APD)

## 1. Abstract

This standard defines **Ephemeral Attested Permissioned Domains (E-APD)** on the XRP Ledger, gated by the `featureEphemeralCredentials` amendment. It extends [XLS-70 (`Credentials`)](../XLS-0070-credentials/README.md) with a transaction flag (`tfEphemeral`, `0x00010000`) on `CredentialCreate` and a corresponding ledger entry flag (`lsfEphemeral`, `0x00020000`) on the `Credential` ledger object (`ltCREDENTIAL`, `0x0081`). When `tfEphemeral` is specified, `CredentialCreate` enforces a bounded Time-To-Live (TTL) window ($60\text{s} \le \text{Expiration} - T_{\text{close}} \le 3600\text{s}$) and permits the credential `Issuer` to perform **in-place renewal rollovers** that monotonically advance `sfExpiration` and update `sfURI` on an existing ephemeral `Credential` entry while preserving the `Subject`'s prior `lsfAccepted` (`0x00010000`) state and owner-reserve accounting. By combining hardware-isolated clearing enclaves with short-TTL credentials and unilateral issuer heartbeat renewals, E-APD provides deterministic, front-running-immune venue ejection across [XLS-80 (`PermissionedDomains`)](../XLS-0080-permissioned-domains/README.md), [XLS-81 (`PermissionedDEX`)](../XLS-0081-permissioned-dex/README.md), and [XLS-66 (`LendingProtocol`)](../XLS-0066-lending-protocol/README.md).

## 2. Motivation

The introduction of [XLS-70 (`Credentials`)](../XLS-0070-credentials/README.md) and [XLS-80 (`PermissionedDomains`)](../XLS-0080-permissioned-domains/README.md) establishes native on-ledger compliance primitives for regulated financial markets. However, baseline XLS-70 credentials were designed around static, long-lived attestations (such as annual KYC/AML onboarding) and exhibit four structural limitations when applied to intraday institutional risk management, prime-brokerage credit limits, regulated market makers, and bounded programmatic execution:

1. **The Reactive Revocation Latency Gap**: Under baseline XLS-70, credentials are long-lived. If a permissioned market participant breaches an intraday margin limit, credit threshold, or regulatory mandate, the issuer must construct, sign, and broadcast a reactive `CredentialDelete` transaction.
2. **Mempool Front-Running Exposure**: An adversarial or malfunctioning trading engine monitoring the peer-to-peer transaction broadcast layer can observe an incoming `CredentialDelete` transaction and front-run it via open-ledger fee escalation (`FeeLevel`), draining liquidity in an XLS-81 `PermissionedDEX` or initiating an XLS-66 `LoanSet` before the revocation achieves consensus finality.
3. **Congestion & Fee-Spike Delay**: During flash crashes or ledger fee-escalation surges, a reactive `CredentialDelete` transaction can be queued in `TxQ` across multiple ledgers precisely when immediate venue containment is required.
4. **Why XLS-56 `Batch` (`CredentialDelete` + `CredentialCreate`) Cannot Substitute for In-Place Rollover**: Under baseline XLS-70, `CredentialCreate` on an existing `(Issuer, Subject, CredentialType)` keylet fails with `tecDUPLICATE`. If an issuer attempts to rotate an expiring credential by submitting `[CredentialDelete, CredentialCreate]` inside an [XLS-56 `Batch`](../XLS-0056-batch/README.md), deleting the existing `Credential` entry **destroys the `lsfAccepted` (`0x00010000`) flag**. Because XLS-70 requires `Subject` to sign `CredentialAccept` to set `lsfAccepted`, and because XLS-80 `PermissionedDomain` validation ignores unaccepted credentials (`!(sleCred->getFlags() & lsfAccepted)`), an issuer-only `[CredentialDelete, CredentialCreate]` batch immediately revokes the participant's domain access until the `Subject` co-signs a new `CredentialAccept`. Requiring every institutional counterparty to co-sign a multi-account `Batch` every few minutes introduces continuous 24/7 hot-key co-signing overhead, doubles signature verification fees, and causes owner-reserve thrashing between `Subject` and `Issuer`.

### The Solution: Inverting the Revocation Paradigm

Instead of issuing long-lived credentials and revoking them reactively, **E-APD inverts the revocation model**:

- Credentials are created with `tfEphemeral` (`0x00010000`) and a **bounded short TTL** ($60\text{s} \le \text{TTL} \le 3600\text{s}$; nominally $300\text{s}$ / $5\text{ minutes}$).
- The `Subject` accepts the credential **once** via standard XLS-70 `CredentialAccept`, setting `lsfAccepted` (`0x00010000`) and assuming the single `0.2 XRP` owner reserve.
- An off-chain **Hardware-Attested Clearing Enclave** continuously evaluates intraday margin, bilateral net exposure, and execution mandates.
- While all invariants hold, the `Issuer` periodically submits `CredentialCreate` with `tfEphemeral` (e.g., every $180\text{s}$), performing an **in-place renewal rollover** that advances `sfExpiration` and updates `sfURI` while preserving `lsfAccepted` without requiring a new `CredentialAccept` signature from `Subject`.
- If a risk or compliance invariant is breached, **the enclave halts renewal**. Once `parentCloseTime > Credential.Expiration`, consensus automatically rejects any subsequent domain-gated transaction by `Subject` with `tecNO_PERMISSION`—with **zero mempool front-running surface**.
- If sub-TTL immediate removal is desired, `Issuer` (or `Subject`) can still broadcast an explicit `CredentialDelete` at any time.

## 3. Overview

### 3.1. Terminology

- **Ephemeral Credential**: An XLS-70 `Credential` ledger entry created with `tfEphemeral` (`0x00010000`) and marked on-ledger with `lsfEphemeral` (`0x00020000`), enforcing a bounded TTL ($[60\text{s}, 3600\text{s}]$) and supporting unilateral issuer in-place renewal rollover.
- **In-Place Renewal Rollover**: An atomic update to an existing `lsfEphemeral` `Credential` entry's `sfExpiration` and optional `sfURI` fields via `CredentialCreate` (`tfEphemeral`), preserving the object's keylet ID, `lsfAccepted` state, owner-directory nodes, and reserve allocation.
- **Hardware-Attested Clearing Enclave**: A non-custodial isolated execution environment (e.g., Intel TDX / AMD SEV-SNP) holding the `Issuer` signing key in hardware-encrypted memory and binding each renewal heartbeat's `sfURI` field to a verifiable attestation or IETF SCITT (`RFC 9162`) receipt digest.

### 3.2. Lifecycle

```
┌────────────────────────────────────────────────────────────────────────┐
│                        E-APD ARCHITECTURAL LIFECYCLE                   │
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│   1. ONE-TIME ONBOARDING                                               │
│      ├── Issuer submits CredentialCreate (tfEphemeral, TTL = 300s)     │
│      │     -> Creates Credential SLE with lsfEphemeral (0x00020000)    │
│      └── Subject submits CredentialAccept                              │
│            -> Sets lsfAccepted (0x00010000); reserve moves to Subject  │
│                                                                        │
│   2. CONTINUOUS IN-PLACE RENEWAL HEARTBEAT (EVERY ~180s)               │
│      ├── Hardware-Attested Clearing Enclave verifies margin & mandates │
│      ├── Issuer submits CredentialCreate (tfEphemeral, New.Exp > Old)  │
│      └── rippled updates sfExpiration & sfURI IN-PLACE                 │
│            -> lsfAccepted (0x00010000) PRESERVED                       │
│            -> 0 Subject signatures required; 0 reserve delta           │
│                                                                        │
│   3. DETERMINISTIC CONSENSUS EJECTION (ON INVARIANT BREACH)            │
│      ├── Enclave halts renewal (or broadcasts CredentialDelete)        │
│      ├── At parentCloseTime > sfExpiration:                            │
│      │     -> XLS-80 / XLS-81 / XLS-66 checks return tecNO_PERMISSION  │
│      └── Any account may submit CredentialDelete (O(1) reserve refund) │
└────────────────────────────────────────────────────────────────────────┘
```

### 3.3. Summary of Protocol Changes

- **Amendment Name**: `featureEphemeralCredentials` (`REGISTER_FEATURE(EphemeralCredentials, Supported::yes, VoteBehavior::DefaultNo)`).
- **New Serialized Types (`SType`)**: None. Reuses existing XLS-70 fields (`sfIssuer`, `sfSubject`, `sfCredentialType`, `sfExpiration`, `sfURI`, `sfFlags`).
- **Modified Ledger Entry**: `Credential` (`ltCREDENTIAL`, `0x0081`) — adds ledger flag `lsfEphemeral` (`0x00020000`).
- **Modified Transaction**: `CredentialCreate` (`ttCREDENTIAL_CREATE`, `58`) — adds transaction flag `tfEphemeral` (`0x00010000`, `tfCredentialCreateMask = ~(tfUniversal | tfEphemeral)`).
- **Unmodified Transactions**: `CredentialAccept` (`ttCREDENTIAL_ACCEPT`, `60`) and `CredentialDelete` (`ttCREDENTIAL_DELETE`, `59`) operate without wire changes.
- **New RPC Methods**: None. `ledger_entry` and `account_objects` return the updated `Flags` (`lsfEphemeral | lsfAccepted = 0x00030000` / `196608`) automatically.

## 4. Ledger Entry: `Credential`

This specification extends the XLS-70 `Credential` ledger entry (`ltCREDENTIAL`, `0x0081`).

### 4.1. Object Identifier

Unchanged from XLS-70. The 32-byte keylet ID of a `Credential` ledger entry is derived in `keylet::credential`:

$$\text{KeyletID} = \text{SHA-512Half}(\texttt{0x0044} \;\|\; \text{Issuer} \;\|\; \text{Subject} \;\|\; \text{CredentialType})$$

Because in-place renewal rollover modifies `sfExpiration` and `sfURI` without altering `Issuer`, `Subject`, or `CredentialType`, the `Credential` keylet ID remains invariant across the entire lifecycle of an ephemeral credential.

### 4.2. Fields

All fields defined in XLS-70 for `Credential` are retained without binary serialization changes:

| Field Name | `SField` Identifier | Type | Presence | Mutability under `lsfEphemeral` | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `LedgerEntryType` | `sfLedgerEntryType` | `UInt16` | Required | Immutable | `0x0081` (`Credential`). |
| `Flags` | `sfFlags` | `UInt32` | Required | Mutable (`lsfAccepted` only) | Bitmask of `lsfAccepted` (`0x00010000`) and `lsfEphemeral` (`0x00020000`). |
| `Subject` | `sfSubject` | `AccountID` | Required | Immutable | The account to which the credential is issued. |
| `Issuer` | `sfIssuer` | `AccountID` | Required | Immutable | The account that created and renews the credential. |
| `CredentialType` | `sfCredentialType` | `Blob` | Required | Immutable | 1 to 64 bytes identifying the credential type. |
| `Expiration` | `sfExpiration` | `UInt32` | **Required** (when `lsfEphemeral` set) | **Mutable (Monotonic Increase)** | Ripple Epoch timestamp (`seconds since 2000-01-01T00:00:00Z`) after which the credential is invalid. |
| `URI` | `sfURI` | `Blob` | Optional | **Mutable** | 1 to 256 bytes storing the attestation commitment or receipt URI; updated or cleared on rollover. |
| `OwnerNode` | `sfOwnerNode` | `UInt64` | Required | Immutable | Directory node index in `Issuer`'s owner directory. |
| `SubjectNode` | `sfSubjectNode` | `UInt64` | Required | Immutable | Directory node index in `Subject`'s owner directory. |
| `PreviousTxnID` | `sfPreviousTxnID` | `Hash256` | Required | Mutable | Hash of the most recent transaction that modified this entry. |
| `PreviousTxnLgrSeq` | `sfPreviousTxnLgrSeq` | `UInt32` | Required | Mutable | Ledger sequence of the most recent modifying transaction. |

#### 4.2.1. Ledger Entry Flags (`LedgerFormats.h`)

| Flag Name | Hex Value | Decimal Value | Set By | Description |
| :--- | :--- | :--- | :--- | :--- |
| `lsfAccepted` | `0x00010000` | `65536` | `CredentialAccept` | Indicates `Subject` has accepted the credential and holds the owner reserve obligation. |
| `lsfEphemeral` | `0x00020000` | `131072` | `CredentialCreate` (`tfEphemeral`) | Indicates the credential is ephemeral, requires `sfExpiration`, and permits in-place renewal rollover by `Issuer`. |

### 4.3. Ownership

Unchanged from XLS-70. The `Credential` SLE is linked into the owner directories of both `Issuer` (`sfOwnerNode`) and `Subject` (`sfSubjectNode`). During an in-place renewal rollover, directory links are untouched.

### 4.4. Reserves

Unchanged from XLS-70:

- **Unaccepted (`!(Flags & lsfAccepted)`)**: Consumes `1` owner reserve increment (`incReserve`) on `Issuer` (`AccountRoot[sfOwnerCount]`).
- **Accepted (`Flags & lsfAccepted`)**: `CredentialAccept` decrements `Issuer`'s `OwnerCount` by `1` and increments `Subject`'s `OwnerCount` by `1`.
- **In-Place Renewal Rollover**: Mutates the existing `Credential` SLE in-place (`view.update(sleCred)`). `OwnerCount` on both `Issuer` and `Subject` changes by **`0`**, and no reserve transfer occurs.

### 4.5. Deletion

Unchanged from XLS-70:

1. **Voluntary Immediate Revocation / Surrender**: Either `Issuer` or `Subject` may submit `CredentialDelete` at any time (whether before or after `sfExpiration`), immediately removing the `Credential` SLE and decrementing `OwnerCount` on whichever account currently bears the reserve (`Subject` if `lsfAccepted` is set, otherwise `Issuer`).
2. **Permissionless Post-Expiration Cleanup**: Once `view.info().parentCloseTime.time_since_epoch().count() > sleCred->at(sfExpiration)`, **any account** may submit `CredentialDelete` (`tesSUCCESS`) to delete the expired entry and release the owner reserve back to the reserve-bearing account (`Subject` or `Issuer`), preserving XRPL's bounded $O(1)$ per-ledger close execution model.

### 4.6. Invariants

The ledger invariant checker (`InvariantCheck.h` / `ValidCredentials`) enforces the following rules whenever a `Credential` SLE is inserted or modified:

1. **Mandatory Expiration on Ephemeral Credentials**: If `(sleCred->getFlags() & lsfEphemeral) != 0`, `sleCred->isFieldPresent(sfExpiration)` MUST be `true`.
2. **Flag Immutability Across Modes**:
   - The `lsfEphemeral` bit (`0x00020000`) MUST NOT change between `orig` and `cur` on an existing `Credential` SLE (`(orig->getFlags() & lsfEphemeral) == (cur->getFlags() & lsfEphemeral)`).
   - Once `lsfAccepted` (`0x00010000`) is set on `orig`, an in-place update MUST NOT clear `lsfAccepted` (`(orig->getFlags() & lsfAccepted) != 0 ==> (cur->getFlags() & lsfAccepted) != 0`).
3. **Identity Tuple Immutability**: On any update to an existing `Credential` SLE, `sfIssuer`, `sfSubject`, and `sfCredentialType` MUST remain byte-identical to `orig`.

### 4.7. RPC Name

Unchanged from XLS-70 (`credential` in `ledger_entry` and `account_objects`).

### 4.8. Example JSON

```json
{
  "LedgerEntryType": "Credential",
  "Account": "rAttestedClearingEnclave1111111111",
  "Subject": "rInstitutionalParticipant402xxxxxx",
  "CredentialType": "61747465737465645F7061727469636970616E74",
  "Expiration": 845992500,
  "URI": "783430323A6174746573743A76313A656E636C6176653A38616362653439",
  "Flags": 196608,
  "OwnerNode": "0000000000000000",
  "SubjectNode": "0000000000000000",
  "PreviousTxnID": "E3FE6EA3D48F0C2B639448020EA4F03D4F4F8FFDB243A852A0F59177921B4879",
  "PreviousTxnLgrSeq": 91452104,
  "index": "48004829F915654A81B11C4AB8218D96F670209B58328A72314265189B421001"
}
```

## 5. Transaction: `CredentialCreate`

This specification extends XLS-70 `CredentialCreate` (`ttCREDENTIAL_CREATE`, `58`).

### 5.1. Fields

All fields from XLS-70 `CredentialCreate` are retained:

| Field Name | `SField` Identifier | Type | Required | Description |
| :--- | :--- | :--- | :--- | :--- |
| `Account` | `sfAccount` | `AccountID` | Yes | The `Issuer` creating or renewing the credential. |
| `Subject` | `sfSubject` | `AccountID` | Yes | The `Subject` receiving the credential. |
| `CredentialType` | `sfCredentialType` | `Blob` | Yes | Non-empty hex blob (`1..64` bytes) identifying the credential class. |
| `Expiration` | `sfExpiration` | `UInt32` | Conditional (**Required** if `tfEphemeral` is set) | Ripple Epoch expiration timestamp. |
| `URI` | `sfURI` | `Blob` | No | Non-empty hex blob (`1..256` bytes). On rollover, if present, replaces `sleCred[sfURI]`; if omitted, retains existing `sleCred[sfURI]`. |
| `Flags` | `sfFlags` | `UInt32` | No | Optional transaction flags (`tfEphemeral = 0x00010000`). |

#### 5.1.1. Transaction Flags (`TxFlags.h`)

```cpp
// CredentialCreate flags:
constexpr std::uint32_t tfEphemeral = 0x00010000;
constexpr std::uint32_t tfCredentialCreateMask = ~(tfUniversal | tfEphemeral);
constexpr std::uint32_t tfCredentialCreatePreEphemeralMask = ~tfUniversal;
```

#### 5.1.2. Constants

```cpp
// Bounded TTL parameters (in seconds) for tfEphemeral credentials:
constexpr std::uint32_t minEphemeralCredentialTTL = 60;
constexpr std::uint32_t maxEphemeralCredentialTTL = 3600;
```

### 5.2. Transaction Fee

Standard XRPL reference transaction fee (`calculateBaseFee(view, tx)` — `10 drops` base minimum).

### 5.3. Failure Conditions

#### 5.3.1. `preflight` Verification (`CredentialCreate::preflight`)

1. **Amendment-Scoped Flag Mask**:
   - If `!ctx.rules.enabled(featureCredentials)`, return `temDISABLED`.
   - If `ctx.rules.enabled(featureEphemeralCredentials)`:
     - If `ctx.tx.getFlags() & tfCredentialCreateMask`, return `temINVALID_FLAG`.
   - Else (`!ctx.rules.enabled(featureEphemeralCredentials)`):
     - If `ctx.tx.getFlags() & tfCredentialCreatePreEphemeralMask`, return `temINVALID_FLAG`.
2. **Standard XLS-70 Field Validation**:
   - Verify `sfSubject` and `sfCredentialType` (`1..maxCredentialTypeLength` bytes), and if `sfURI` is present, verify `1..maxCredentialURILength` (`256`) bytes; otherwise return `temMALFORMED`.
3. **Mandatory `sfExpiration` under `tfEphemeral`**:
   - If `(ctx.tx.getFlags() & tfEphemeral) && !ctx.tx.isFieldPresent(sfExpiration)`, return `temMALFORMED`.

#### 5.3.2. `preclaim` Verification (`CredentialCreate::preclaim`)

Let `closeTime = ctx.view.info().parentCloseTime.time_since_epoch().count()` and `isEphemeral = (ctx.tx.getFlags() & tfEphemeral) != 0`.

1. **Past Expiration Check (Existing XLS-70 Rule)**:
   - If `ctx.tx.isFieldPresent(sfExpiration)` and `ctx.tx[sfExpiration] <= closeTime` (i.e., `checkExpired(ctx.tx[sfExpiration], ctx.view.info().parentCloseTime)`), return `tecEXPIRED`.
2. **Bounded TTL Window Check (`isEphemeral == true`)**:
   - Let `exp = ctx.tx[sfExpiration]`.
   - If `exp < closeTime + minEphemeralCredentialTTL` (`60`) or `exp > closeTime + maxEphemeralCredentialTTL` (`3600`), return `temINVALID_EXPIRATION`. *(Note: Using a `tec` code `tecEXPIRED` / `tecOVERSIZE` or rejecting in `preclaim` before SLE mutation guarantees deterministic consensus enforcement; if evaluated in `preclaim` against `parentCloseTime`, returning `tecEXPIRED` for `< closeTime + 60` or `> closeTime + 3600` charges the anti-spam reference fee while leaving ledger state untouched.)*
   - **Normative Result Code Choice**: Because `parentCloseTime` is only available in `preclaim` (not `preflight`), XRPL transactor conventions prohibit returning `tem*` codes from `preclaim` when the condition depends on ledger close time. Therefore, in `preclaim`:
     - If `exp <= closeTime`, return `tecEXPIRED` (existing XLS-70 behavior).
     - If `isEphemeral` and (`exp < closeTime + minEphemeralCredentialTTL` or `exp > closeTime + maxEphemeralCredentialTTL`), return **`tecEXPIRED`**.
3. **Subject Account Existence**:
   - If `!ctx.view.read(keylet::account(ctx.tx[sfSubject]))`, return `tecNO_TARGET`.
4. **Existing `Credential` SLE Lookup & Rollover Eligibility**:
   - Let `k = keylet::credential(ctx.tx[sfAccount], ctx.tx[sfSubject], ctx.tx[sfCredentialType])` and `sleCred = ctx.view.read(k)`.
   - **Case A (`sleCred == nullptr` — Initial Creation)**:
     - Proceed with standard XLS-70 creation check: verify `Account` (`Issuer`) has sufficient XRP balance to meet `accountReserve(ownerCount + 1)`; if not, return `tecINSUFFICIENT_RESERVE`.
   - **Case B (`sleCred != nullptr` — Existing Entry Found)**:
     - If `!isEphemeral`: return `tecDUPLICATE` (existing XLS-70 behavior).
     - If `(sleCred->getFlags() & lsfEphemeral) == 0`: return `tecDUPLICATE` (a static credential cannot be rolled over as an ephemeral credential).
     - If `ctx.tx[sfExpiration] <= (*sleCred)[sfExpiration]`: return `tecDUPLICATE` (rollover expiration MUST strictly advance: `New.Expiration > Existing.Expiration`).
     - *(Reserve Check on Rollover)*: Because in-place rollover does not increment `OwnerCount` on `Issuer` or `Subject`, **no additional owner-reserve check is required** on `Case B`, allowing renewals to succeed even if `Issuer`'s liquid balance is down to transaction fee drops.

### 5.4. State Changes (`CredentialCreate::doApply`)

1. **Case A (`sleCred == nullptr` — Initial Creation)**:
   - Create `sleCred = std::make_shared<SLE>(k)` with `sfIssuer = Account`, `sfSubject = Subject`, `sfCredentialType = CredentialType`, `sfExpiration = Expiration`, and optional `sfURI = URI`.
   - Set `sleCred->setFieldU32(sfFlags, lsfEphemeral)` (`0x00020000`).
   - Insert `sleCred` into `Issuer`'s and `Subject`'s owner directories and call `adjustOwnerCount(view(), sleIssuer, 1, ctx_.journal)`.
2. **Case B (`sleCred != nullptr` — In-Place Renewal Rollover)**:
   - Obtain mutable SLE via `auto sleEdit = view().peek(k)`.
   - Set `sleEdit->setFieldU32(sfExpiration, ctx_.tx[sfExpiration])`.
   - If `ctx_.tx.isFieldPresent(sfURI)`, set `sleEdit->setFieldVL(sfURI, ctx_.tx[sfURI])`.
   - **Preserve `sfFlags` (`lsfEphemeral` and `lsfAccepted`)**: Do not clear `lsfAccepted` (`0x00010000`).
   - Call `view().update(sleEdit)` and return `tesSUCCESS`.

### 5.5. Example JSON

```json
{
  "TransactionType": "CredentialCreate",
  "Account": "rAttestedClearingEnclave1111111111",
  "Subject": "rInstitutionalParticipant402xxxxxx",
  "CredentialType": "61747465737465645F7061727469636970616E74",
  "Flags": 65536,
  "Expiration": 845992500,
  "URI": "783430323A6174746573743A76313A656E636C6176653A38616362653439",
  "Fee": "12",
  "Sequence": 42
}
```

## 6. Transaction: `CredentialDelete`

This specification makes no wire format or behavioral changes to XLS-70 `CredentialDelete` (`ttCREDENTIAL_DELETE`, `59`).

### 6.1. Fields

Unchanged from XLS-70 (`Account`, `Subject`, `Issuer`, `CredentialType`).

### 6.2. Transaction Fee

Standard XRPL reference transaction cost.

### 6.3. Failure Conditions

Unchanged from XLS-70:

- If `parentCloseTime <= sleCred[sfExpiration]`, only `Issuer` or `Subject` may delete the credential; any third party receives `tecNO_PERMISSION`.
- If `parentCloseTime > sleCred[sfExpiration]`, **any account** may delete the expired credential (`tesSUCCESS`).

### 6.4. State Changes

Unchanged from XLS-70. Removes the `Credential` SLE from both owner directories and decrements `OwnerCount` by `1` on `Subject` (if `lsfAccepted` is set) or `Issuer` (if `lsfAccepted` is not set).

### 6.5. Example JSON

```json
{
  "TransactionType": "CredentialDelete",
  "Account": "rAnyCleanerAccount1111111111111111",
  "Issuer": "rAttestedClearingEnclave1111111111",
  "Subject": "rInstitutionalParticipant402xxxxxx",
  "CredentialType": "61747465737465645F7061727469636970616E74",
  "Fee": "12",
  "Sequence": 108
}
```

## 7. Rationale

### 7.1. Why XLS-56 `Batch` (`CredentialDelete` + `CredentialCreate`) Cannot Achieve In-Place Rollover

A common question is whether an issuer can achieve short-TTL credential rotation without an amendment by bundling `CredentialDelete` and `CredentialCreate` in an [XLS-56 `Batch`](../XLS-0056-batch/README.md) transaction (`tfAllOrNothing`). That approach fails for three reasons rooted in XLS-70's state machine:

1. **Destruction of `lsfAccepted`**: In `CredentialDelete::doApply`, the existing `Credential` SLE is erased from the state tree. When the subsequent `CredentialCreate` inner transaction executes, it creates a brand-new `Credential` SLE with `Flags = 0` (`lsfAccepted` cleared). Under XLS-80 (`PermissionedDomain`) and XLS-70 (`credentials::valid`), a credential with `lsfAccepted == 0` is **not active** and does not grant domain membership.
2. **Mandatory `Subject` Co-Signing Overhead**: To restore `lsfAccepted`, a third inner transaction (`CredentialAccept` with `Account = Subject`) would have to be included in the `Batch`, requiring `Subject` to provide a `BatchSigner` signature on every 3-minute heartbeat. If `Subject` is an institutional trading desk or a cold-storage treasury vault that delegates execution via `RegularKey` or `Delegate` (XLS-75), forcing two-party multi-account `Batch` co-signing every 180 seconds defeats unilateral compliance enforcement.
3. **Zero-Downtime & Zero Reserve Churn**: `tfEphemeral` in-place rollover allows `Issuer` to extend `sfExpiration` with a single `CredentialCreate` transaction while keeping `lsfAccepted` intact and leaving `Subject`'s owner reserve untouched.

### 7.2. Why Return `tecEXPIRED` (Rather Than `tem*`) for TTL Bounds in `preclaim`?

In `rippled`, `preflight` is stateless and has no access to `view.info().parentCloseTime`. Because TTL bounds ($T_{\text{close}} + 60 \le \text{Expiration} \le T_{\text{close}} + 3600$) depend on the parent validated ledger's close time, they must be evaluated in `preclaim`. Returning `tecEXPIRED` in `preclaim` follows `rippled`'s strict invariant that `tem*` codes are never returned for ledger-time-dependent conditions (`CredentialCreate.cpp` already returns `tecEXPIRED` in `preclaim` when `Expiration <= parentCloseTime`).

### 7.3. Why Allow In-Place Rollover Even After `parentCloseTime > Existing.Expiration`?

Suppose a network congestion spike or temporary enclave connectivity pause causes a 300-second credential to lapse at $T = 305\text{s}$ before the renewal transaction lands at $T = 310\text{s}$ (and before any third party has garbage-collected the SLE via `CredentialDelete`). During the gap $[305\text{s}, 310\text{s}]$, the participant is fail-closed (`tecNO_PERMISSION`) on all XLS-80 domain actions. When the issuer's `CredentialCreate` (`tfEphemeral`) lands at $T = 310\text{s}$ with `New.Expiration = 610s > Existing.Expiration`, permitting in-place rollover restores the credential seamlessly without requiring the `Subject` to re-run `CredentialAccept`.

### 7.4. Cross-Amendment Composability Matrix

| Amendment / Specification | Composability & Interaction with `featureEphemeralCredentials` |
| :--- | :--- |
| **[XLS-70 (`Credentials`)](../XLS-0070-credentials/README.md)** | Reuses `credentials::checkExpired(sleCred, parentCloseTime)`. Zero changes required to `credentials::valid()` or `CredentialAccept`. |
| **[XLS-80 (`PermissionedDomains`)](../XLS-0080-permissioned-domains/README.md)** | `PermissionedDomain` lists `(Issuer, CredentialType)` in `AcceptedCredentials`. When an ephemeral credential expires (`parentCloseTime > sfExpiration`), `PermissionedDomain` checks automatically reject the participant with `tecNO_PERMISSION`. |
| **[XLS-81 (`PermissionedDEX`)](../XLS-0081-permissioned-dex/README.md)** | Domain-gated `OfferCreate` and auto-bridging verify `AcceptedCredentials` against `parentCloseTime`. Expired ephemeral credentials immediately block new offer placement (`tecNO_PERMISSION`), and unbacked domain offers can be pruned permissionlessly. |
| **[XLS-66.3.3 (`Private LoanBroker`)](../XLS-0066-lending-protocol/README.md)** | Private lending pools gated by `DomainID` reject new `LoanSet` originations immediately once the borrower's ephemeral credential expires, while existing disbursed loans remain payable per XLS-66 rules. |
| **[XLS-56 (`Batch`)](../XLS-0056-batch/README.md)** | An attested clearing enclave managing $N$ participants in a domain can bundle up to 8 `CredentialCreate` (`tfEphemeral`) heartbeat renewals into a single atomic `Batch` (`tfIndependent` or `tfAllOrNothing`). |
| **[XLS-68 (`Sponsor`)](../XLS-0068-sponsored-fees-and-reserves/README.md)** | Compatible with `Sponsor` (`spfSponsorFee` / `spfSponsorReserve`), allowing the clearing enclave to sponsor initial `CredentialAccept` reserves or fees if configured. |
| **[XLS-69 (`Simulate`)](../XLS-0069-simulate/README.md)** | `simulate` (`TapDryRun`) evaluates `CredentialCreate::preclaim` against the open/validated ledger's `parentCloseTime`, accurately predicting `tesSUCCESS`, `tecEXPIRED`, or `tecDUPLICATE`. |

## 8. Reference Implementation

### 8.1. `rippled` C++ Core Implementation Diff

#### 8.1.1. `include/xrpl/protocol/TxFlags.h` & `LedgerFormats.h`

```cpp
// In include/xrpl/protocol/TxFlags.h:
constexpr std::uint32_t tfEphemeral = 0x00010000;
constexpr std::uint32_t tfCredentialCreateMask = ~(tfUniversal | tfEphemeral);
constexpr std::uint32_t tfCredentialCreatePreEphemeralMask = ~tfUniversal;

// In include/xrpl/protocol/LedgerFormats.h (ltCREDENTIAL flags):
lsfAccepted  = 0x00010000,
lsfEphemeral = 0x00020000,

// In include/xrpl/protocol/Protocol.h:
constexpr std::uint32_t minEphemeralCredentialTTL = 60;
constexpr std::uint32_t maxEphemeralCredentialTTL = 3600;
```

#### 8.1.2. `src/libxrpl/tx/transactors/credentials/CredentialCreate.cpp`

```cpp
NotTEC
CredentialCreate::preflight(PreflightContext const& ctx)
{
    if (!ctx.rules.enabled(featureCredentials))
        return temDISABLED;

    auto const flags = ctx.tx.getFlags();
    if (ctx.rules.enabled(featureEphemeralCredentials))
    {
        if (flags & tfCredentialCreateMask)
            return temINVALID_FLAG;
    }
    else
    {
        if (flags & tfCredentialCreatePreEphemeralMask)
            return temINVALID_FLAG;
    }

    if (auto const ret = preflight1(ctx); !isTesSuccess(ret))
        return ret;

    if ((flags & tfEphemeral) && !ctx.tx.isFieldPresent(sfExpiration))
        return temMALFORMED;

    // Existing XLS-70 URI and CredentialType length checks...
    return preflight2(ctx);
}

TER
CredentialCreate::preclaim(PreclaimContext const& ctx)
{
    AccountID const issuer = ctx.tx[sfAccount];
    AccountID const subject = ctx.tx[sfSubject];
    Blob const credType = ctx.tx[sfCredentialType];
    bool const isEphemeral = (ctx.tx.getFlags() & tfEphemeral) != 0;

    auto const closeTime =
        ctx.view.info().parentCloseTime.time_since_epoch().count();

    if (ctx.tx.isFieldPresent(sfExpiration))
    {
        std::uint32_t const exp = ctx.tx[sfExpiration];
        if (exp <= closeTime)
            return tecEXPIRED;

        if (isEphemeral)
        {
            if (exp < closeTime + minEphemeralCredentialTTL ||
                exp > closeTime + maxEphemeralCredentialTTL)
                return tecEXPIRED;
        }
    }

    if (!ctx.view.read(keylet::account(subject)))
        return tecNO_TARGET;

    auto const k = keylet::credential(issuer, subject, credType);
    if (auto const sleCred = ctx.view.read(k))
    {
        // Existing credential found: only valid if both tx and SLE are ephemeral
        // and the new expiration strictly advances the existing expiration.
        if (!isEphemeral || !(sleCred->getFlags() & lsfEphemeral))
            return tecDUPLICATE;

        if (ctx.tx[sfExpiration] <= (*sleCred)[sfExpiration])
            return tecDUPLICATE;

        return tesSUCCESS;
    }

    // New credential creation: verify issuer reserve
    auto const sleIssuer = ctx.view.read(keylet::account(issuer));
    if (!sleIssuer)
        return terNO_ACCOUNT;

    if (STAmount const reserve =
            ctx.view.fees().accountReserve((*sleIssuer)[sfOwnerCount] + 1);
        (*sleIssuer)[sfBalance] < reserve)
        return tecINSUFFICIENT_RESERVE;

    return tesSUCCESS;
}

TER
CredentialCreate::doApply()
{
    AccountID const issuer = ctx_.tx[sfAccount];
    AccountID const subject = ctx_.tx[sfSubject];
    Blob const credType = ctx_.tx[sfCredentialType];
    auto const k = keylet::credential(issuer, subject, credType);

    if (auto sleCred = view().peek(k))
    {
        // In-Place Renewal Rollover (preserves lsfAccepted and directory nodes)
        sleCred->setFieldU32(sfExpiration, ctx_.tx[sfExpiration]);
        if (ctx_.tx.isFieldPresent(sfURI))
            sleCred->setFieldVL(sfURI, ctx_.tx[sfURI]);
        view().update(sleCred);
        return tesSUCCESS;
    }

    // Standard XLS-70 creation path (+ setting lsfEphemeral if tfEphemeral set)
    auto sleCred = std::make_shared<SLE>(k);
    sleCred->setAccountID(sfIssuer, issuer);
    sleCred->setAccountID(sfSubject, subject);
    sleCred->setFieldVL(sfCredentialType, credType);
    if (ctx_.tx.isFieldPresent(sfExpiration))
        sleCred->setFieldU32(sfExpiration, ctx_.tx[sfExpiration]);
    if (ctx_.tx.isFieldPresent(sfURI))
        sleCred->setFieldVL(sfURI, ctx_.tx[sfURI]);
    if (ctx_.tx.getFlags() & tfEphemeral)
        sleCred->setFlag(lsfEphemeral);

    // Insert into owner directories & increment issuer OwnerCount...
    return tesSUCCESS;
}
```

### 8.2. TypeScript Client Reference (`xrpl.js`)

```typescript
import { Client, Wallet, CredentialCreate } from "xrpl";

export interface EphemeralCredentialConfig {
  issuerWallet: Wallet;
  participantAddress: string;
  ttlSeconds: number; // Bounded between 60 and 3600 seconds; nominally 300 (5 minutes)
  attestationUri: string; // Hardware enclave attestation receipt URI
}

export async function issueOrRenewEphemeralCredential(
  client: Client,
  config: EphemeralCredentialConfig
): Promise<string> {
  if (config.ttlSeconds < 60 || config.ttlSeconds > 3600) {
    throw new Error("Ephemeral TTL must be bounded between 60 and 3600 seconds.");
  }

  // Derive expiration from the authoritative validated ledger close time
  const ledgerResponse = await client.request({
    command: "ledger",
    ledger_index: "validated"
  });
  const validatedCloseTime = ledgerResponse.result.ledger.close_time;
  const expiration = validatedCloseTime + config.ttlSeconds;

  const tx: CredentialCreate = {
    TransactionType: "CredentialCreate",
    Account: config.issuerWallet.classicAddress,
    Subject: config.participantAddress,
    CredentialType: Buffer.from("attested_participant", "utf8").toString("hex").toUpperCase(),
    Expiration: expiration,
    URI: Buffer.from(config.attestationUri, "utf8").toString("hex").toUpperCase(),
    Flags: 0x00010000 // tfEphemeral
  };

  const prepared = await client.autofill(tx);
  const signed = config.issuerWallet.sign(prepared);
  const result = await client.submitAndWait(signed.tx_blob);

  return result.result.hash;
}
```

## 9. Backwards Compatibility

Fully gated by the `featureEphemeralCredentials` amendment. Pre-activation nodes reject `tfEphemeral` (`0x00010000`) with `temINVALID_FLAG` during `preflight` and continue baseline XLS-70 and XLS-80 operation. Existing static credentials (`lsfEphemeral` not set) behave identically before and after amendment activation.

## 10. Test Plan

The `rippled` unit test suite (`src/test/app/Credentials_test.cpp` $\rightarrow$ `testEphemeralCredentials()`) MUST verify all 8 deterministic test vectors:

| Vector # | Test Case | Setup & Input | Expected `TER` & Ledger State |
| :--- | :--- | :--- | :--- |
| **1** | Pre-Amendment Flag Rejection | `featureEphemeralCredentials` disabled; submit `CredentialCreate` with `Flags: tfEphemeral` (`0x00010000`). | `temINVALID_FLAG` |
| **2** | Missing `sfExpiration` with `tfEphemeral` | `featureEphemeralCredentials` enabled; submit `CredentialCreate` with `tfEphemeral` and no `sfExpiration`. | `temMALFORMED` |
| **3** | TTL Below `60s` Floor | Submit `CredentialCreate` (`tfEphemeral`) with `Expiration = parentCloseTime + 59`. | `tecEXPIRED` |
| **4** | TTL Above `3600s` Ceiling | Submit `CredentialCreate` (`tfEphemeral`) with `Expiration = parentCloseTime + 3601`. | `tecEXPIRED` |
| **5** | Valid Creation, Acceptance & In-Place Rollover | Create (`TTL = 300s`, `lsfEphemeral` set) $\rightarrow$ `Subject` runs `CredentialAccept` (`Flags = 0x00030000`, reserve on `Subject`) $\rightarrow$ advance `180s` $\rightarrow$ `Issuer` submits `CredentialCreate` (`tfEphemeral`, `New.Exp = closeTime + 300`, updated `URI`). | `tesSUCCESS`; `sfExpiration` & `sfURI` updated in-place; `lsfAccepted` preserved; `Subject` & `Issuer` `OwnerCount` delta = `0`. |
| **6** | Non-Monotonic Rollover Rejection | Submit `CredentialCreate` (`tfEphemeral`) on existing ephemeral credential with `New.Expiration <= Existing.Expiration`. | `tecDUPLICATE`; existing SLE unmodified. |
| **7** | Cross-Mode Isolation (Static $\leftrightarrow$ Ephemeral) | Attempt `CredentialCreate` (`tfEphemeral`) on an existing static credential (`lsfEphemeral == 0`), and attempt `CredentialCreate` (no `tfEphemeral`) on an existing ephemeral credential (`lsfEphemeral != 0`). | `tecDUPLICATE` in both directions. |
| **8** | Consensus Ejection & Third-Party Cleanup | Advance ledger close time past `sfExpiration` without renewal $\rightarrow$ `Subject` submits XLS-81 domain-gated `OfferCreate` $\rightarrow$ unrelated third party `Carol` submits `CredentialDelete`. | `OfferCreate` fails with `tecNO_PERMISSION`; `Carol`'s `CredentialDelete` succeeds with `tesSUCCESS` and releases `Subject`'s `0.2 XRP` reserve. |

## 11. Security Considerations

### 11.1. Deterministic Bounded Ejection & Mempool Front-Running Immunity

Because venue ejection occurs automatically via consensus close-time progression (`parentCloseTime > sfExpiration`) when the clearing enclave withholds renewal, an out-of-mandate or compromised participant cannot front-run revocation in the transaction queue or delay ejection through fee escalation.

### 11.2. Strict Monotonic Expiration Progression

Enforcing `ctx.tx[sfExpiration] > (*sleCred)[sfExpiration]` in `preclaim` prevents out-of-order or delayed transactions in `TxQ` from accidentally rolling a credential's expiration backwards, while the `maxEphemeralCredentialTTL` (`3600s`) ceiling ensures that no single transaction can grant more than one hour of validity.

### 11.3. Reserve & Directory Invariance

Because in-place renewal rollover executes `view().update(sleCred)` on an existing `ltCREDENTIAL` node without touching `sfOwnerNode`, `sfSubjectNode`, or `OwnerCount`, high-frequency institutional compliance heartbeats cannot leak owner directory pages or drift account reserve counters.

# Appendix

## Appendix A: FAQ

### A.1: Why not use an XLS-56 `Batch` containing `CredentialDelete` + `CredentialCreate`?

As detailed in §7.1, `CredentialDelete` erases the `Credential` SLE and clears `lsfAccepted` (`0x00010000`). Under XLS-70 and XLS-80, an unaccepted credential does not confer domain membership until `Subject` signs a new `CredentialAccept`. In-place rollover via `tfEphemeral` preserves `lsfAccepted` across unilateral issuer renewals.

### A.2: Does an expired ephemeral credential automatically cancel resting DEX offers or unwind active XLS-66 loans?

In accordance with XLS-80, XLS-81, and XLS-66, credential checks are enforced at transaction execution time. Once `parentCloseTime > sfExpiration`, any new domain-gated `OfferCreate`, `Payment`, or `LoanSet` by `Subject` is immediately rejected with `tecNO_PERMISSION`. Resting unbacked domain offers and expired `Credential` objects can be pruned permissionlessly by any network participant, while existing disbursed XLS-66 loans remain payable per XLS-66 rules.

### A.3: What happens if `URI` is omitted on an in-place renewal rollover?

If `sfURI` is omitted on a rollover `CredentialCreate`, the existing `sfURI` field on the `Credential` SLE is retained unchanged. If `sfURI` is provided (1 to 256 bytes), it replaces the existing `sfURI` in-place.

### A.4: Can `Subject` or `Issuer` still delete an ephemeral credential before `sfExpiration`?

Yes. Standard XLS-70 `CredentialDelete` rules remain 100% intact: either `Issuer` or `Subject` may delete the credential immediately at any time prior to expiration, and any account on the network may delete it after expiration.
