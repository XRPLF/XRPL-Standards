<pre>
  xls: 99
  title: ElGamal Key Rotation for Confidential MPTs
  description: Defines ElGamal key rotation for issuer, auditor, and holder roles in the Confidential MPT protocol, with key loss recovery mechanisms.
  author: Aanchal Malhotra <amalhotra@ripple.com>, Yinyi Qian <yqian@ripple.com>
  category: Amendment
  status: Draft
  proposal-from: https://github.com/XRPLF/XRPL-Standards/discussions/599
  requires: XLS-0096, XLS-0033
  created: 2026-04-01
  updated: 2026-08-31
</pre>

# ElGamal Key Rotation for Confidential MPTs

## 1. Abstract

This amendment extends XLS-0096 (Confidential Transfers for Multi-Purpose Tokens) with ElGamal key rotation for all three participant roles: issuer, auditor, and holder. It introduces 3 new transaction types (`ConfidentialMPTMirrorUpdate`, `ConfidentialMPTHolderKeyUpdate`, `ConfidentialMPTRecoverBalance`), extends `MPTokenIssuanceSet` to permit replacement of already-registered encryption keys, adds mirror staleness validation to three existing XLS-0096 transaction types (`ConfidentialMPTSend`, `ConfidentialMPTConvert`, `ConfidentialMPTConvertBack`) together with mirror resets and epoch rewrites on `ConfidentialMPTClawback`, and adds new fields to the `MPTokenIssuance` and `MPToken` ledger objects. Key rotation is supported for both voluntary and loss-recovery scenarios. All new cryptographic constructions reuse existing primitives from XLS-0096 (compact Chaum-Pedersen equality proofs, Schnorr proofs of knowledge) and introduce no new cryptographic assumptions.

## 2. Motivation

XLS-0096 encrypts MPT balances using ElGamal keys held by issuers, holders, and auditors. These keys are independent of XRPL signing keys and currently have no rotation mechanism. This gap creates three unresolved operational risks:

First, a compromised ElGamal key - at any role - gives an attacker persistent read access to confidential balances with no remediation path.

Second, operations teams change over time. XRPL signing key rotation is handled by existing primitives (`SetRegularKey`, `SignerListSet`). No equivalent exists for ElGamal keys held by any role.

Third, auditor key loss or a change in supervisory authority breaks regulatory visibility into all holder balances with no recovery path. For regulated issuances operating under compliance obligations, the inability to rotate the auditor key is a go-live blocker.

This amendment defines the rotation and recovery mechanisms required to address all three scenarios across all three roles. It directly addresses the limitation acknowledged in XLS-0096 FAQ A.6: "If a holder loses their ElGamal private key, they will be unable to decrypt or spend their confidential balances, which will remain valid on-ledger but are effectively locked and irrecoverable by that holder."

## 3. Definitions & Terminology

Terms not defined here carry the same meaning as in XLS-0096.

- **Key Epoch**: A monotonically increasing counter on `MPTokenIssuance` that increments on each ElGamal key rotation for the issuer or auditor role.
- **Mirror Epoch**: A monotonically increasing counter on `MPToken` that tracks the last key epoch at which the holder's issuer or auditor mirror ciphertext was re-encrypted.
- **Stale Mirror**: A present issuer or auditor mirror ciphertext whose mirror epoch is less than the corresponding key epoch on `MPTokenIssuance`. A stale mirror is encrypted under an older key and cannot be combined homomorphically with new transaction deltas encrypted under the current key.
- **Current Mirror**: A holder's issuer or auditor mirror ciphertext is current when the mirror ciphertext is present and its mirror epoch equals the corresponding key epoch on MPTokenIssuance. A missing auditor mirror is not current when an auditor key is configured, even if both absent epoch fields are interpreted as epoch 0. When no auditor key is configured, no auditor mirror is required.
- **Missing Mirror**: The corresponding encryption key is configured on `MPTokenIssuance`, but the mirror ciphertext is absent from the holder's `MPToken`. This is a valid state only for an auditor mirror following late auditor registration. A missing issuer mirror on initialized confidential state is invalid.
- **Active Re-encryption**: The process by which the issuer submits `ConfidentialMPTMirrorUpdate` for each holder after a key rotation to re-encrypt mirror ciphertexts under the new key.
- **Recovery Key** (`sfRecoveryKey`): A field on `MPToken` set by the holder to authorize replacement of their ElGamal key when they have lost `sk_H`.
- **No Recovery Pending**: `RecoveryKey` is absent. The registered `HolderEncryptionKey` remains the holder's active ElGamal key.
- **Recovery Pending**: `RecoveryKey` is present. The existing `HolderEncryptionKey` and encrypted balances remain unchanged until recovery is completed or cancelled.
- **Context Hash**: The 256-bit value defined in XLS-0096 that binds a zero-knowledge proof to a specific transaction and ledger state, providing domain separation and replay protection. For proofs over a holder's own balances it incorporates the holder's `ConfidentialBalanceVersion`, so any change to the spending balance invalidates outstanding proofs. Section 4.8 gives the composition used by the proofs this amendment introduces.

## 4. Overview

### 4.1. Modified Transaction Types

- `MPTokenIssuanceSet`: Extended to allow replacement of `IssuerEncryptionKey` and `AuditorEncryptionKey` when already present, enabling issuer and auditor key rotation. See Section 5.3.
- `ConfidentialMPTConvert`: Rejected when an already-initialized holder's issuer or auditor mirror is stale; sets mirror epochs when a holder initializes confidential state. See Section 5.7.
- `ConfidentialMPTSend`: Rejected when the sender's or the destination's issuer or auditor mirror is stale. See Section 5.8.
- `ConfidentialMPTConvertBack`: Rejected when the holder's issuer or auditor mirror is stale. See Section 5.9.
- `ConfidentialMPTClawback`: Not rejected on a stale mirror; resets both mirror ciphertexts and rewrites both mirror epochs on success. See Section 5.10.

### 4.2. New Transaction Types

- `ConfidentialMPTMirrorUpdate`: Re-encrypts a single holder's issuer and/or auditor mirror ciphertext under the new key. Operates in two modes selected by `Holder` field presence:
  - Issuer mode (`Holder` present): submitted by the issuer using a Chaum-Pedersen equality proof anchored to the on-ledger issuer mirror.
  - Holder mode (`Holder` absent): submitted by the holder using a cross-key equality proof anchored to `ConfidentialBalanceSpending`. Requires `ConfidentialBalanceInbox` to be canonical zero.
- `ConfidentialMPTHolderKeyUpdate`: Rotates a holder's ElGamal key, authorizes recovery, or cancels pending recovery. Operates in three modes selected by transaction flag:
  - Rotation mode (`tfHolderKeyRotation`): holder re-encrypts `ConfidentialBalanceSpending` and `ConfidentialBalanceInbox` under the new key atomically.
  - Recovery mode (`tfHolderKeyRecovery`): holder has lost `sk_H`; registers new key as `RecoveryKey` for issuer-completed recovery.
  - Cancel mode (`tfCancelRecovery`): holder clears a pending `RecoveryKey` authorization.
- `ConfidentialMPTRecoverBalance`: Completes holder key loss recovery by re-encrypting balances under the authorized new key. Submitted by the issuer.

### 4.3. Modified Ledger Entries

- `MPTokenIssuance`: Three new fields - `IssuerKeyEpoch`, `AuditorKeyEpoch`, `InitialIssuerEncryptionKey`.
- `MPToken`: Four new fields - `IssuerKeyMirrorEpoch`, `AuditorKeyMirrorEpoch`, `IssuerMirrorEncryptionKey`, `RecoveryKey`.

### 4.4. Key Rotation Model

**Issuer key rotation** proceeds in two phases. First, the issuer submits `MPTokenIssuanceSet` with a new `IssuerEncryptionKey`, incrementing `IssuerKeyEpoch`. After this transaction is accepted, all new issuer mirror delta ciphertexts must be encrypted under the new key. Second, the issuer submits `ConfidentialMPTMirrorUpdate` once per holder to re-encrypt each holder's issuer mirror under the new key.

Until a holder's mirror is migrated, confidential transactions for that holder are rejected. The underlying reason is cryptographic: in `ConfidentialMPTSend` and other transactions, the holder correctly reads the current `IssuerEncryptionKey` (`pk_I'`) from the issuance and constructs `IssuerEncryptedAmount` under it. However, the on-ledger accumulated `IssuerEncryptedBalance` is still under the old key (`pk_I`). Adding a delta under `pk_I'` to an accumulated balance under `pk_I` is cryptographically invalid - ciphertexts under different keys cannot be combined homomorphically.

Comparing the holder's mirror epoch with the corresponding issuance key epoch makes this detectable cleanly:

- Transaction processing uses it to reject the transaction explicitly and early, before attempting an invalid homomorphic addition
- Wallet software applies the same comparison proactively, allowing it to warn the holder and block a transaction that would fail before submission

**Auditor key rotation** follows the identical pattern using `AuditorEncryptionKey` and `AuditorKeyEpoch`.

**Auditor key late-registration by issuer** allows the issuer to register auditor key after the issuer key was already registered.

- Pre-`ConfidentialMPTKeyRotation` amendment: when registering the key for the auditor first time, it has to be registered together with the issuer key in `MPTokenIssuanceSet`. The issuer is not allowed to register issuer key in one transaction and later register auditor key in another transaction.
- Now with `ConfidentialMPTKeyRotation` amendment: with the issuer key already registered, the issuer can register the auditor key in a separate `MPTokenIssuanceSet` whenever they want to enable auditor.

**Holder self-migration** is available after an issuer key rotation, an auditor key rotation, simultaneous issuer and auditor key rotation, or late auditor registration. Rather than waiting for the issuer to submit `ConfidentialMPTMirrorUpdate`, any holder may self-migrate their issuer or auditor mirror by submitting `ConfidentialMPTMirrorUpdate` without a `Holder` field, using a cross-key equality proof anchored to their `ConfidentialBalanceSpending`. Prerequisites: `ConfidentialMPTMergeInbox` must be run first (inbox must be canonical zero), and the holder must have `sk_H`. See Section 5.4.6 for what the proof establishes.

**Simultaneous issuer and auditor key rotation**: The issuer may rotate both `IssuerEncryptionKey` and `AuditorEncryptionKey` in a single `MPTokenIssuanceSet` transaction, though this is rare in practice. In this case, per-holder migration may be performed in a single `ConfidentialMPTMirrorUpdate` transaction with both `IssuerEncryptedAmount` and `AuditorEncryptedAmount` present. A single compact AND-composed Chaum-Pedersen equality proof covers both statements under one Fiat-Shamir challenge.

**Multiple successive rotations**: The issuer may rotate multiple times before completing migration. Holders with stale mirrors are blocked from transacting at the per-transaction level regardless of how many epochs behind they are. `ConfidentialMPTMirrorUpdate` bridges directly from the holder's current epoch to the latest epoch in one step. In issuer mode, this requires the issuer to retain the historical secret key corresponding to the epoch the holder is currently at - if that key has been destroyed, the holder must self-migrate by submitting `ConfidentialMPTMirrorUpdate` without a `Holder` field instead. The recommended practice is to update every holder after each rotation, which keeps every mirror one epoch behind at most and leaves the issuer needing only the most recent key.

**Holder key rotation** is self-contained via `ConfidentialMPTHolderKeyUpdate` with `tfHolderKeyRotation`. No issuer involvement required.

**Holder key loss recovery** is a two-step process: the holder registers the new key on-chain via `ConfidentialMPTHolderKeyUpdate` with `tfHolderKeyRecovery`, then the issuer completes recovery via `ConfidentialMPTRecoverBalance`.

**Issuer key loss** is handled via holder-driven mirror reconstruction for both issuer and auditor mirrors. In the issuer key loss scenario, holder self-migration is the only path for issuer mirrors since the issuer cannot decrypt old mirrors without `sk_I`. For auditor mirrors, the issuer can still perform active re-encryption via the issuer mirror (`sk_I`) even when `sk_A` is lost - holder self-migration is an alternative but not the only path. See Section 9.

### 4.5. Re-encryption Strategy

Active re-encryption is the recommended strategy: after rotating the key, the issuer submits `ConfidentialMPTMirrorUpdate` for every holder.
Prioritization for bulk migration:

1. Largest balances first - greatest value at risk if old key is compromised.
2. Most active holders next - unblocks their confidential transactions soonest.
3. Regulatory-sensitive accounts - under specific compliance obligations.
4. Remaining inactive accounts - lowest urgency, though each one left behind keeps the issuer dependent on the secret key for its epoch.

An issuer that does not keep a history of its issuer secret keys should finish migrating every holder before discarding the key it just replaced. Nothing in the protocol requires this, but a holder left at an epoch whose secret key the issuer no longer holds can no longer be migrated or clawed back by the issuer, and recovering them depends entirely on the holder self-migrating.

The issuer may rotate keys multiple times. Holders with stale mirrors are blocked from transacting at the per-transaction level regardless of how many epochs behind they are. See Section 4.6.2.

**Clawback during migration**: Clawback is not blocked by a stale mirror. Its proof is verified against the key the holder's issuer mirror is encrypted under, so the issuer retains clawback authority over an unmigrated holder for as long as they hold the secret key for that holder's epoch.

**Historical key retention**: After multiple successive rotations, both migrating and clawing back from a holder still at an old epoch require the historical secret key for that epoch to decrypt their on-ledger mirror. If the issuer has destroyed a historical key before all holders at that epoch were migrated, clawback authority over those holders is lost and they must fall back to self-migration (Section 5.4.6). Issuers should retain historical secret keys until all holders at each epoch are fully migrated.

### 4.6. Epoch Tracking and Migration Status

#### 4.6.1. Determining Mirror Status

For an `MPToken` with initialized confidential state:

- The issuer mirror is current when `IssuerEncryptedBalance` is present and `IssuerKeyMirrorEpoch` equals `IssuerKeyEpoch`.
- When an auditor key is configured, the auditor mirror is current when `AuditorEncryptedBalance` is present and `AuditorKeyMirrorEpoch` equals `AuditorKeyEpoch`. When no auditor key is configured, no auditor mirror is required.
- Migration is required whenever a required mirror is not current.

An absent epoch field is treated as epoch 0. A mirror field is current if its mirror epoch and the corresponding key epoch are equal. Ledger invariants separately ensure that a mirror epoch cannot exceed its corresponding key epoch.

#### 4.6.2. Transactions Requiring Current Mirrors

The transactions below are rejected with `tecNO_PERMISSION` when a mirror they require is not current. An auditor mirror is required only when an auditor key is configured. The normative failure conditions and state changes for each transaction are specified in its own section.

| Transaction                  | Required current mirrors                              | Specified in |
| :--------------------------- | :---------------------------------------------------- | :----------- |
| `ConfidentialMPTConvert`     | Issuer and auditor, for an already-initialized holder | Section 5.7  |
| `ConfidentialMPTSend`        | Issuer and auditor, for both sender and destination   | Section 5.8  |
| `ConfidentialMPTConvertBack` | Issuer and auditor, for the holder                    | Section 5.9  |

`ConfidentialMPTClawback` is deliberately absent from the table. Each transaction above combines a ciphertext encrypted under the currently registered key into a mirror that already exists, which is only sound when that mirror is current. Clawback instead writes both mirrors as canonical encrypted zero under the currently registered keys, so there is no ciphertext to corrupt and no reason to require a current mirror; see Section 5.10.

#### 4.6.3. Migration-Required Conditions

The required migration is determined as follows:

1. If the issuer mirror is not current, it must be migrated.
2. If an auditor key is configured but `AuditorEncryptedBalance` is absent, the auditor mirror must be initialized. This is the late-registration case. Initial auditor-key registration remains at epoch 0, so field presence must be checked separately from epoch equality.
3. If `AuditorEncryptedBalance` is present but the auditor mirror is not current, it must be migrated.
4. If both mirrors require migration, they may be updated in one `ConfidentialMPTMirrorUpdate`.

A missing `IssuerEncryptedBalance` on an initialized confidential `MPToken` is an invalid ledger state, not a migration state.

#### 4.6.4. New Holder Initialization

A holder who executes `ConfidentialMPTConvert` after key registration or rotation has their `MPToken` initialized with mirror ciphertexts under the current keys. Its mirror epoch fields are set to the corresponding current key epochs, with epoch 0 fields omitted from ledger storage. The holder therefore does not require migration.

#### 4.6.5. Issuance-Wide Migration Completion

Mirror status for a single holder can be determined on-ledger in O(1) from mirror presence and epoch equality. Determining whether migration is complete for an entire issuance requires traversing the holders off-chain through `mpt_holders` API.

### 4.7. State Transition Summary

This section is an informative summary using the states defined in Section 3. The referenced transaction sections remain normative. In the tables below, **Before** and **After** describe the abstract state before and after the transition; **Trigger** identifies the transaction or ledger event; **Preconditions** summarizes the required state and proof; **State Changes** lists the affected ledger fields; and **Reference** points to the normative rules.

#### 4.7.1. Mirror Lifecycle

| Before                             | Trigger                                                                          | Preconditions                                                                | State Changes                                                                                                                                                                                                                                                           | After                                                                                                     | Reference                  |
| :--------------------------------- | :------------------------------------------------------------------------------- | :--------------------------------------------------------------------------- | :---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | :-------------------------------------------------------------------------------------------------------- | :------------------------- |
| No auditor mirror required         | Initial auditor key registration                                                 | Issuer key is already registered                                             | `AuditorEncryptionKey` is registered; existing holder objects are unchanged                                                                                                                                                                                             | Missing auditor mirror for each initialized confidential holder                                           | Sections 4.4 and 5.3       |
| No initialized confidential state  | First `ConfidentialMPTConvert`                                                   | Current issuer key and any configured auditor key are used                   | Mirror ciphertexts are created, mirror epochs are set to the current key epochs, and `IssuerMirrorEncryptionKey` is set to `IssuerEncryptionKey`                                                                                                                        | Current mirror or mirrors                                                                                 | Section 4.6.4 and XLS-0096 |
| Current mirror                     | Corresponding issuer or auditor key rotation                                     | A different valid key is submitted                                           | The key is replaced and its key epoch increments; a first issuer key rotation also records the replaced key as `InitialIssuerEncryptionKey`; holder mirrors are unchanged                                                                                               | Stale mirror                                                                                              | Section 5.3                |
| Stale mirror                       | Another rotation of the corresponding key                                        | Successive rotation is permitted                                             | The key epoch increments again; the holder mirror remains unchanged                                                                                                                                                                                                     | Stale mirror, possibly multiple epochs behind                                                             | Sections 4.4 and 12.9      |
| Stale issuer mirror                | `ConfidentialMPTMirrorUpdate` updates the issuer mirror                          | Required issuer-mode or holder-mode proof succeeds                           | `IssuerEncryptedBalance` is replaced, `IssuerKeyMirrorEpoch` is set to `IssuerKeyEpoch`, and `IssuerMirrorEncryptionKey` is set to `IssuerEncryptionKey`                                                                                                                | Current issuer mirror                                                                                     | Section 5.4                |
| Missing or stale auditor mirror    | `ConfidentialMPTMirrorUpdate` updates the auditor mirror                         | Auditor key is configured and the required proof succeeds                    | `AuditorEncryptedBalance` is created or replaced and `AuditorKeyMirrorEpoch` is set to `AuditorKeyEpoch`                                                                                                                                                                | Current auditor mirror                                                                                    | Section 5.4                |
| Current mirrors                    | `ConfidentialMPTConvert`, `ConfidentialMPTSend`, or `ConfidentialMPTConvertBack` | Every required mirror is current                                             | Mirror ciphertexts change under the current keys; mirror epochs do not change                                                                                                                                                                                           | Current mirrors                                                                                           | Sections 5.7 through 5.9   |
| Any mirror state, current or stale | `ConfidentialMPTClawback`                                                        | Clawback proof succeeds against the key the issuer mirror is encrypted under | Mirror ciphertexts are reset to canonical encrypted zero under the current keys, their epochs are set to the current key epochs, and `IssuerMirrorEncryptionKey` is set to `IssuerEncryptionKey`; an absent auditor mirror is created when an auditor key is registered | Current issuer mirror encrypting zero, and a current auditor mirror whenever an auditor key is registered | Section 5.10               |

#### 4.7.2. Holder Key and Recovery Lifecycle

| Before              | Trigger                                           | Preconditions                                                 | State Changes                                                                                                                                                     | After               | Reference                |
| :------------------ | :------------------------------------------------ | :------------------------------------------------------------ | :---------------------------------------------------------------------------------------------------------------------------------------------------------------- | :------------------ | :----------------------- |
| No Recovery Pending | `ConfidentialMPTHolderKeyUpdate` in rotation mode | Required mirrors are current and the rotation proof succeeds  | `HolderEncryptionKey`, holder balance ciphertexts, and `ConfidentialBalanceVersion` are updated                                                                   | No Recovery Pending | Sections 5.5.4 and 5.5.5 |
| No Recovery Pending | `ConfidentialMPTHolderKeyUpdate` in recovery mode | New-key Schnorr proof succeeds                                | `RecoveryKey` is created; the existing holder key and balances are unchanged                                                                                      | Recovery Pending    | Sections 5.5.4 and 5.5.5 |
| Recovery Pending    | `ConfidentialMPTHolderKeyUpdate` in cancel mode   | Holder authorizes the transaction with their XRPL signing key | `RecoveryKey` is removed; the existing holder key and balances are unchanged                                                                                      | No Recovery Pending | Sections 5.5.4 and 5.5.5 |
| Recovery Pending    | `ConfidentialMPTRecoverBalance`                   | Issuer mirror is current and the recovery proof succeeds      | `HolderEncryptionKey` is replaced by `RecoveryKey`, the recovered balance is placed in spending, inbox is reset, version increments, and `RecoveryKey` is removed | No Recovery Pending | Section 5.6              |
| Recovery Pending    | `ConfidentialMPTHolderKeyUpdate` in rotation mode | Required mirrors are current and the rotation proof succeeds  | The holder key, holder balance ciphertexts, and version are updated; `RecoveryKey` is removed                                                                     | No Recovery Pending | Sections 5.5.4 and 5.5.5 |

### 4.8. Proof Context Hash

Every proof introduced by this amendment is bound to the transaction carrying it by a context hash:

`SHA-512Half(TransactionType ‖ Account ‖ MPTokenIssuanceID ‖ Sequence ‖ Counterparty ‖ Version)`

The last two fields carry the transaction-specific part. `Counterparty` is the other account the transaction acts on, and repeats `Account` when the transaction acts only on the submitter's own `MPToken`. `Version` is the holder's `ConfidentialBalanceVersion` when the proof anchors on a ciphertext encrypted under the holder key, and 0 otherwise.

| Transaction                      | Mode                  | `Counterparty` | `Version`                    |
| :------------------------------- | :-------------------- | :------------- | :--------------------------- |
| `ConfidentialMPTMirrorUpdate`    | Issuer                | `Holder`       | 0                            |
| `ConfidentialMPTMirrorUpdate`    | Holder self-migration | `Account`      | `ConfidentialBalanceVersion` |
| `ConfidentialMPTHolderKeyUpdate` | Rotation              | `Account`      | `ConfidentialBalanceVersion` |
| `ConfidentialMPTHolderKeyUpdate` | Recovery              | `Account`      | 0                            |
| `ConfidentialMPTRecoverBalance`  |                       | `Holder`       | 0                            |

A proof anchored on the issuer mirror does not bind `ConfidentialBalanceVersion`, because the issuer would otherwise see a migration or recovery it has already signed invalidated by any unrelated activity of the holder, which would make bulk migration impractical (Section 10.1). Staleness of the anchor itself is caught without it: the anchor ciphertext is a public input to the proof, so a proof no longer verifies once the ciphertext it was built against has changed.

`ConfidentialMPTHolderKeyUpdate` in cancel mode carries no proof and therefore no context hash.

## 5. Specification

### 5.1. Ledger Entry: `MPTokenIssuance`

The existing `MPTokenIssuance` ledger object is extended with two new fields. All other fields, flags, ownership, reserves, deletion conditions, and the object identifier are unchanged from XLS-0033.

#### 5.1.1. Fields

| Field Name                   | Constant | Required | Internal Type | Default Value | Description                                               |
| :--------------------------- | :------- | :------- | :------------ | :------------ | :-------------------------------------------------------- |
| `IssuerKeyEpoch`             | No       | No       | `UINT32`      | `0`           | Counter of issuer ElGamal key rotations.                  |
| `AuditorKeyEpoch`            | No       | No       | `UINT32`      | `0`           | Counter of auditor ElGamal key rotations.                 |
| `InitialIssuerEncryptionKey` | Yes      | No       | `BLOB`        | N/A           | The issuer ElGamal public key that was in use at epoch 0. |

**Field Details:**

##### 5.1.1.1. `IssuerKeyEpoch`

An absent field means epoch 0, and the field is not stored while at that value. Initial registration of `IssuerEncryptionKey` leaves the epoch absent rather than writing 0. This is what allows `MPTokenIssuance` objects created before this amendment, which carry a registered key but no epoch field, to be read as epoch 0 without a ledger migration.

The first successful rotation of `IssuerEncryptionKey` creates the field with value 1, and each subsequent rotation increments it by 1. The counter never decreases (I7).

##### 5.1.1.2. `AuditorKeyEpoch`

The counter follows the same rules as `IssuerKeyEpoch`: an absent field means 0 and is not stored, initial registration of `AuditorEncryptionKey` leaves it absent, the first rotation creates it with value 1, and it never decreases.

Unlike the issuer key, the auditor key is optional and may be registered at any time, including after confidential balances already exist. An epoch of 0 therefore carries two possible meanings: no auditor key is configured at all, or an auditor key is registered but has never been rotated. The two are distinguished by the presence of `AuditorEncryptionKey`, not by the epoch, and only the first removes the requirement for holders to carry an auditor mirror (Section 4.6.1).

##### 5.1.1.3. `InitialIssuerEncryptionKey`

A 33-byte compressed secp256k1 point, preserving the issuer key that was registered at epoch 0. Rotation overwrites `IssuerEncryptionKey` in place, so without this field the epoch 0 key would be unrecoverable from ledger state, and an issuer-mode migration of a mirror still at epoch 0 could not be verified.

The field is written exactly once, by the first issuer key rotation, which stores the key it is replacing. Later rotations leave it untouched. Any mirror belonging to a later epoch carries on the holder's `MPToken` as `IssuerMirrorEncryptionKey`.

#### 5.1.2. Freeze/Lock

**Lock Support:** Yes

Setting `lsfMPTLocked` on `MPTokenIssuance` locks the entire issuance. This amendment adds no new lock flag and does not change how the existing one is set, cleared, or enforced, so lock support is unchanged from XLS-0033 and XLS-0096. See Section 8 for how a lock interacts with key rotation, mirror migration, and holder key loss recovery.

#### 5.1.3. Invariants

- I1: `IssuerKeyEpoch`, if present, must be ≥ 1.
- I2: `AuditorKeyEpoch`, if present, must be ≥ 1.
- I3: `IssuerEncryptionKey` must be present if `IssuerKeyEpoch` is present.
- I4: `AuditorEncryptionKey` must be present if `AuditorKeyEpoch` is present.
- I5: On a successful issuer key rotation, `<MPTokenIssuance>'.IssuerKeyEpoch == <MPTokenIssuance>.IssuerKeyEpoch + 1`. An absent epoch is treated as 0, so the first rotation yields 1.
- I6: On a successful auditor key rotation, `<MPTokenIssuance>'.AuditorKeyEpoch == <MPTokenIssuance>.AuditorKeyEpoch + 1`. An absent epoch is treated as 0, so the first rotation yields 1.
- I7: `<MPTokenIssuance>'.IssuerKeyEpoch >= <MPTokenIssuance>.IssuerKeyEpoch AND <MPTokenIssuance>'.AuditorKeyEpoch >= <MPTokenIssuance>.AuditorKeyEpoch`. Key epochs never decrease.
- I15: `InitialIssuerEncryptionKey` is present if and only if `IssuerKeyEpoch` is present. It must be a well-formed compressed secp256k1 point (33 bytes).
- I16: `InitialIssuerEncryptionKey` is immutable once written: if it is present before a transaction, `<MPTokenIssuance>'.InitialIssuerEncryptionKey == <MPTokenIssuance>.InitialIssuerEncryptionKey`. It may differ from the current `IssuerEncryptionKey`, and may also equal it, since nothing prevents an issuer from eventually rotating back to a previously used key.

#### 5.1.4. Example JSON

After issuer and auditor key rotation:

```json
{
  "LedgerEntryType": "MPTokenIssuance",
  "Flags": 128,
  "Issuer": "rIssuerAccountAddress",
  "Sequence": 1,
  "OwnerNode": "0",
  "MaximumAmount": "1000000000",
  "OutstandingAmount": "500000000",
  "ConfidentialOutstandingAmount": "250000000",
  "IssuerEncryptionKey": "02a1b2c3d4e5f6...",
  "AuditorEncryptionKey": "02b1c2d3e4f5a6...",
  "IssuerKeyEpoch": 1,
  "AuditorKeyEpoch": 1,
  "InitialIssuerEncryptionKey": "02b7c8d9e0f1a2...",
  "PreviousTxnID": "A1B2C3D4...",
  "PreviousTxnLgrSeq": 1234567
}
```

### 5.2. Ledger Entry: `MPToken`

The existing `MPToken` ledger object is extended with four new fields. All other fields, flags, ownership, reserves, and the object identifier are unchanged from XLS-0033.

#### 5.2.1. Fields

| Field Name                  | Constant | Required | Internal Type | Default Value | Description                                                                   |
| :-------------------------- | :------- | :------- | :------------ | :------------ | :---------------------------------------------------------------------------- |
| `IssuerKeyMirrorEpoch`      | No       | No       | `UINT32`      | `0`           | The `IssuerKeyEpoch` under which this holder's issuer mirror is encrypted.    |
| `AuditorKeyMirrorEpoch`     | No       | No       | `UINT32`      | `0`           | The `AuditorKeyEpoch` under which this holder's auditor mirror is encrypted.  |
| `IssuerMirrorEncryptionKey` | No       | No       | `BLOB`        | N/A           | The issuer ElGamal public key this holder's issuer mirror is encrypted under. |
| `RecoveryKey`               | No       | No       | `BLOB`        | N/A           | A compressed ElGamal public key authorized for key loss recovery.             |

**Field Details:**

##### 5.2.1.1. `IssuerKeyMirrorEpoch`

An absent field means epoch 0, and the field is not stored while at that value. The mirror is current when the field equals the issuance's `IssuerKeyEpoch` and stale when it is less; staleness is what blocks the transactions listed in Section 4.6.2.

The field is written whenever the mirror is re-encrypted under the currently registered key: by `ConfidentialMPTMirrorUpdate`, by `ConfidentialMPTClawback`, and by the `ConfidentialMPTConvert` that initializes a holder's confidential state. It never decreases (I14) and never exceeds the issuance's key epoch (I8).

##### 5.2.1.2. `AuditorKeyMirrorEpoch`

The field is written on the same occasions as `IssuerKeyMirrorEpoch`, with one exception: when the issuance's `AuditorKeyEpoch` is 0, the field is left absent rather than written, since an absent epoch is already equivalent to 0. This arises when an auditor mirror is created before any auditor key rotation has occurred. The field never decreases (I14) and never exceeds the issuance's auditor key epoch (I9).

Epoch equality alone does not make the auditor mirror current: `AuditorEncryptedBalance` must also be present (Section 4.6.1). A holder who initialized confidential state before an auditor key was registered has no auditor mirror at all, so their absent epoch equals the issuance's epoch of 0 while the mirror is missing rather than current. Such a holder is repaired by `ConfidentialMPTMirrorUpdate` in the same way as a stale one.

##### 5.2.1.3. `IssuerMirrorEncryptionKey`

A 33-byte compressed secp256k1 point recording which issuer key the holder's `IssuerEncryptedBalance` is encrypted under. Since the issuance retains only the current key and the epoch 0 key, this is what lets an issuer-mode migration be verified however far behind the mirror is.

Three transactions write the field, each of them a transaction that writes the mirror under a key it may not already be encrypted under: the `ConfidentialMPTConvert` that initializes confidential state, `ConfidentialMPTMirrorUpdate` which migrates the mirror, and `ConfidentialMPTClawback` which resets it to encrypted zero under the currently registered key. Clawback must write the field for the same reason it advances `IssuerKeyMirrorEpoch`: it accepts a stale mirror and leaves it current, so the recorded key has to move with the epoch (I17, I19).

##### 5.2.1.4. `RecoveryKey`

A 33-byte compressed secp256k1 point. It must be a well-formed point and must differ from the holder's current `HolderEncryptionKey` (I10), and it is only meaningful on an `MPToken` that has completed confidential initialization (I11).

The field is set by `ConfidentialMPTHolderKeyUpdate` in recovery mode (`tfHolderKeyRecovery`), recording the holder's consent to issuer-completed recovery under the new key.

It is cleared by exactly three paths: `ConfidentialMPTRecoverBalance`, when the issuer completes recovery; `ConfidentialMPTHolderKeyUpdate` with `tfCancelRecovery`, when the holder revokes consent; and `ConfidentialMPTHolderKeyUpdate` with `tfHolderKeyRotation`, which proves the holder still holds sk_H and so withdraws the premise of the authorization (Section 12.6). There is no automatic expiry, so an authorization persists until one of those three transactions occurs. Section 12.7 discusses the resulting liveness concern.

#### 5.2.2. Deletion

Deletion conditions are unchanged from XLS-0033. The `MPToken` deletion question raised by `RecoveryKey` is a non-issue: per XLS-0096 Section 5.2.4, an `MPToken` cannot be deleted once confidential fields have been initialized, even if all balances contain canonical encrypted zero. Since `RecoveryKey` only appears on initialized `MPToken` objects (Invariant I11), an `MPToken` with `RecoveryKey` set can never be deleted. No new deletion concern is introduced by this amendment.

#### 5.2.3. Freeze/Lock

**Lock Support:** Yes

Setting `lsfMPTLocked` on a holder's `MPToken` locks that holder individually, independently of the issuance-level lock described in Section 5.1.2. This amendment adds no new lock flag and does not change how the existing one is set, cleared, or enforced, so lock support is unchanged from XLS-0033 and XLS-0096. See Section 8 for how a lock interacts with key rotation, mirror migration, and holder key loss recovery.

#### 5.2.4. Invariants

- I8: `IssuerKeyMirrorEpoch`, if present, must be ≤ `IssuerKeyEpoch` on the parent `MPTokenIssuance` (treated as 0 if absent).
- I9: `AuditorKeyMirrorEpoch`, if present, must be ≤ `AuditorKeyEpoch` on the parent `MPTokenIssuance` (treated as 0 if absent).
- I10: `RecoveryKey`, if present, must be a well-formed compressed secp256k1 point (33 bytes) and must differ from the current `HolderEncryptionKey`.
- I11: `RecoveryKey` must not be present on an `MPToken` that has no `HolderEncryptionKey` registered. A holder initializes confidential state via their first `ConfidentialMPTConvert` (with `HolderEncryptionKey` present, MPTAmount may be zero). `RecoveryKey` is only meaningful for holders who have completed this initialization.
- I12: On a successful transaction that rewrites `IssuerEncryptedBalance`, `<MPToken>'.IssuerKeyMirrorEpoch == <MPTokenIssuance>.IssuerKeyEpoch`.
- I13: On a successful transaction that writes `AuditorEncryptedBalance`, whether it replaces an existing mirror or creates one, `<MPToken>'.AuditorKeyMirrorEpoch == <MPTokenIssuance>.AuditorKeyEpoch`.
- I14: `<MPToken>'.IssuerKeyMirrorEpoch >= <MPToken>.IssuerKeyMirrorEpoch AND <MPToken>'.AuditorKeyMirrorEpoch >= <MPToken>.AuditorKeyMirrorEpoch`. Mirror epochs never decrease.
- I17: `IssuerMirrorEncryptionKey` is present if and only if `IssuerKeyMirrorEpoch` is present. Equivalently, a mirror with no recorded key is at epoch 0.
- I18: `IssuerMirrorEncryptionKey`, if present, must be a well-formed compressed secp256k1 point (33 bytes), and `IssuerEncryptedBalance` must also be present.
- I19: If `IssuerKeyMirrorEpoch` equals the issuance's `IssuerKeyEpoch`, `IssuerMirrorEncryptionKey` must equal the issuance's `IssuerEncryptionKey`. A current mirror is by definition encrypted under the registered key. For a stale mirror the recorded key cannot be checked against ledger state, since the key of an earlier epoch is no longer registered.
- I20: A transaction that rewrites `IssuerEncryptedBalance` without advancing `IssuerKeyMirrorEpoch` must leave `IssuerMirrorEncryptionKey` unchanged. Such a transaction combines a delta under the current key into a mirror that is already current, so the key it is encrypted under does not change.

#### 5.2.5. Example JSON

Fully migrated holder:

```json
{
  "LedgerEntryType": "MPToken",
  "Flags": 0,
  "MPTokenIssuanceID": "000000012A9F1D3C...",
  "Account": "rHolderAccountAddress",
  "HolderEncryptionKey": "02c1d2e3f4a5b6...",
  "ConfidentialBalanceSpending": "02d1e2f3a4b5c6...",
  "ConfidentialBalanceInbox": "02e1f2a3b4c5d6...",
  "ConfidentialBalanceVersion": 3,
  "IssuerEncryptedBalance": "02f1a2b3c4d5e6...",
  "IssuerKeyMirrorEpoch": 1,
  "IssuerMirrorEncryptionKey": "02a1b2c3d4e5f6...",
  "AuditorEncryptedBalance": "02a3b4c5d6e7f8...",
  "AuditorKeyMirrorEpoch": 1,
  "OwnerNode": "0",
  "PreviousTxnID": "B2C3D4E5...",
  "PreviousTxnLgrSeq": 1234568
}
```

Holder with active recovery authorization:

```json
{
  "LedgerEntryType": "MPToken",
  "Flags": 0,
  "MPTokenIssuanceID": "000000012A9F1D3C...",
  "Account": "rHolderAccountAddress",
  "HolderEncryptionKey": "02c1d2e3f4a5b6...",
  "ConfidentialBalanceSpending": "02d1e2f3a4b5c6...",
  "ConfidentialBalanceInbox": "02e1f2a3b4c5d6...",
  "ConfidentialBalanceVersion": 3,
  "IssuerEncryptedBalance": "02f1a2b3c4d5e6...",
  "IssuerKeyMirrorEpoch": 1,
  "IssuerMirrorEncryptionKey": "02a1b2c3d4e5f6...",
  "RecoveryKey": "03a9b8c7d6e5f4...",
  "OwnerNode": "0",
  "PreviousTxnID": "C3D4E5F6...",
  "PreviousTxnLgrSeq": 1234569
}
```

### 5.3. Transaction: `MPTokenIssuanceSet`

The existing `MPTokenIssuanceSet` transaction is extended to allow replacement of `IssuerEncryptionKey` and `AuditorEncryptionKey` when already present. Some existing guards in preclaim must be relaxed:

1.  Key presence guard: The current implementation rejects updates to `IssuerEncryptionKey` and `AuditorEncryptionKey` once already present on the issuance object (`tecNO_PERMISSION`). This guard is relaxed to allow replacement when the field is already present. Key rotation does not reintroduce the vulnerability this guard was introduced to prevent - when rotating, the field already exists and every holder's `MPToken` already has the corresponding ciphertext column.
2.  `sfConfidentialOutstandingAmount` > 0 guard: The current implementation unconditionally rejects any `IssuerEncryptionKey` or `AuditorEncryptionKey` update when `sfConfidentialOutstandingAmount` is already present (i.e. COA > 0). This guard must also be relaxed. Key rotation is only meaningful and necessary precisely when COA > 0 - if COA were zero, no holder would have a mirror yet and none of the migration logic would be needed. Maintaining this guard makes key rotation impossible in any real deployment.
3.  Pre-`ConfidentialMPTKeyRotation` amendment, an issuer cannot register an auditor key in `MPTokenIssuanceSet` unless the issuer key is being registered in the same transaction. This means the issuer can either register the issuer key alone or register both keys together initially. With the `ConfidentialMPTKeyRotation` amendment, the issuer can now register an auditor key at any time after the issuer key is already registered or rotated—allowing them to opt in whenever they want. The only constraint is that an auditor key cannot be registered before an issuer key.

The guard against adding `IssuerEncryptionKey` when `lsfMPTCanHoldConfidentialBalance` is not enabled remains unchanged - confidential transfers must be enabled before keys can be set or rotated. All existing `MPTokenIssuanceSet` behavior (lock/unlock, `DomainID`) is completely unaffected.

#### 5.3.1. Fields

| Field Name             | Required? | JSON Type | Internal Type | Default Value | Description                                                                                                                                                                                                   |
| ---------------------- | --------- | --------- | ------------- | ------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `IssuerEncryptionKey`  | No        | string    | BLOB          | N/A           | When present and already exists on the issuance, replaces the existing issuer ElGamal public key. Must be a well-formed compressed secp256k1 point (33 bytes). Must differ from the current on-ledger value.  |
| `AuditorEncryptionKey` | No        | string    | BLOB          | N/A           | When present and already exists on the issuance, replaces the existing auditor ElGamal public key. Must be a well-formed compressed secp256k1 point (33 bytes). Must differ from the current on-ledger value. |

#### 5.3.2. Failure Conditions

##### 5.3.2.1. Data Verification

1. `IssuerEncryptionKey`, `AuditorEncryptionKey`, or `tfMPTSetCanHoldConfidentialBalance` is present but the `ConfidentialTransfer` amendment is not enabled. (`temDISABLED`)
2. `IssuerEncryptionKey` is present but is not exactly 33 bytes or is not a well-formed compressed secp256k1 point. (`temMALFORMED`)
3. `AuditorEncryptionKey` is present but is not exactly 33 bytes or is not a well-formed compressed secp256k1 point. (`temMALFORMED`)
4. `Holder` is present together with `IssuerEncryptionKey` or `AuditorEncryptionKey`. (`temMALFORMED`)

**Note**: Pre-`ConfidentialMPTKeyRotation` amendment: `AuditorEncryptionKey` is present without `IssuerEncryptionKey` returns `temMALFORMED`; Now it is allowed in preflight and will be further verified in preclaim.

##### 5.3.2.2. Protocol-Level Failures

1. `IssuerEncryptionKey` or `AuditorEncryptionKey` is present, but the issuance does not have the `lsfMPTCanHoldConfidentialBalance` flag set and this transaction is not enabling it via `tfMPTSetCanHoldConfidentialBalance`. (`tecNO_PERMISSION`)
2. `AuditorEncryptionKey` is being registered for the first time (not present on the issuance), but the issuance has no `IssuerEncryptionKey` and the current `MPTokenIssuanceSet` transaction does not provide one. (`tecNO_PERMISSION`)
3. `IssuerEncryptionKey` matches the current on-ledger value (no-op rotation). (`tecDUPLICATE`)
4. `AuditorEncryptionKey` matches the current on-ledger value (no-op rotation). (`tecDUPLICATE`)

#### 5.3.3. State Changes

**On Success (`tesSUCCESS`):**

When `IssuerEncryptionKey` is present and valid:

1. If `IssuerEncryptionKey` already existed and `IssuerKeyEpoch` is absent, `InitialIssuerEncryptionKey` on `MPTokenIssuance` ← the key being replaced. This is the first rotation, so the replaced key is the epoch 0 key. On any later rotation the field already exists and is left untouched, and on initial registration it is not written at all.
2. `IssuerEncryptionKey` on `MPTokenIssuance` ← new key value
3. If `IssuerEncryptionKey` already existed, `IssuerKeyEpoch` on `MPTokenIssuance` ← `IssuerKeyEpoch` + 1 (field created with value 1 if previously absent); on initial registration, leave the epoch absent.

When `AuditorEncryptionKey` is present and valid:

1. `AuditorEncryptionKey` on `MPTokenIssuance` ← new key value
2. If `AuditorEncryptionKey` already existed, `AuditorKeyEpoch` on `MPTokenIssuance` ← `AuditorKeyEpoch` + 1 (field created with value 1 if previously absent); on initial registration, leave the epoch absent.

#### 5.3.4. Example JSON

Rotating the issuer key:

```json
{
  "TransactionType": "MPTokenIssuanceSet",
  "Account": "rIssuerAccountAddress",
  "MPTokenIssuanceID": "000000012A9F1D3C...",
  "IssuerEncryptionKey": "02a1b2c3d4e5f6...",
  "Fee": "10",
  "Sequence": 42
}
```

Registering an auditor key for the first time on an issuance that already has an `IssuerEncryptionKey`. This shape is rejected with `temMALFORMED` before the `ConfidentialMPTKeyRotation` amendment (Section 5.3.2.1) and leaves `AuditorKeyEpoch` absent, since it is an initial registration rather than a rotation:

```json
{
  "TransactionType": "MPTokenIssuanceSet",
  "Account": "rIssuerAccountAddress",
  "MPTokenIssuanceID": "000000012A9F1D3C...",
  "AuditorEncryptionKey": "02b3c4d5e6f7a8...",
  "Fee": "10",
  "Sequence": 43
}
```

### 5.4. Transaction: `ConfidentialMPTMirrorUpdate`

Re-encrypts a single holder's issuer and/or auditor mirror ciphertext under the new key after a key rotation. Submitted by the issuer once per holder. A holder may also self-migrate their issuer mirror, their auditor mirror, or both. Every migration re-encrypts one or both of a holder's mirror balances under a rotated key, and proves the new ciphertext still encrypts the same balance without revealing it.

- Issuer Mode (Submitted by the issuer with the `sfHolder`):

1. **Issuer Key Rotation Migration**: Re-encrypts the holder's issuer mirror `IssuerEncryptedBalance` under the new `pk_I'`.
2. **Auditor Key Rotation Migration**: Re-encrypts the holder's auditor mirror `AuditorEncryptedBalance` under the new `pk_A'`.
3. **Simultaneous Rotation Migration**: Updates both the issuer and auditor encrypted balances in a single transaction.
4. **Auditor Late-Registration Migration**: Set the auditor mirror if the auditor key is registered post-issuance.

- Holder Self-Migration Mode (Submitted by the holder without the `sfHolder` field. The holder decrypts their own `sfConfidentialBalanceSpending` with their private key and re-encrypts it under the relevant new public key(s). Require `sfConfidentialBalanceInbox` to be canonically zero, which means the holder has run `ConfidentialMPTMergeInbox` first):

5. **Holder Issuer-Mirror Self-Migration**: Re-encrypts issuer mirror.
6. **Holder Auditor-Mirror Self-Migration**: Re-encrypts the auditor mirror, or sets it for the first time if late-registered.
7. **Simultaneous Holder Self-Migration**: Updates both the issuer and auditor encrypted balances in a single transaction (used when both keys have rotated).

#### 5.4.1. Fields

Whether it is issuer mode or holder mode is determined by `Holder` field's presence. If `Holder` is present, it is issuer mode. If `Holder` is absent, it is holder self-migration mode.

| Field Name               | Required?   | JSON Type | Internal Type | Default Value                 | Description                                                                                                                                                                                                                                                  |
| :----------------------- | :---------- | :-------- | :------------ | :---------------------------- | :----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `TransactionType`        | Yes         | `string`  | `UINT16`      | `ConfidentialMPTMirrorUpdate` | `ConfidentialMPTMirrorUpdate`.                                                                                                                                                                                                                               |
| `Account`                | Yes         | `string`  | `ACCOUNTID`   | N/A                           | The issuer account in issuer mode, or the holder account in holder mode.                                                                                                                                                                                     |
| `MPTokenIssuanceID`      | Yes         | `string`  | `UINT192`     | N/A                           | The unique identifier of the MPT issuance.                                                                                                                                                                                                                   |
| `Holder`                 | Conditional | `string`  | `ACCOUNTID`   | N/A                           | **Required** in issuer mode and **must be absent** in holder mode. Identifies the holder whose mirror(s) are being re-encrypted.                                                                                                                             |
| `IssuerEncryptedAmount`  | Conditional | `string`  | `BLOB`        | N/A                           | A 66-byte ElGamal ciphertext encrypting the holder's balance under the new issuer key. Reuses `sfIssuerEncryptedAmount` from XLS-0096. Present to migrate holder's issuer mirror. At least one of this field and `AuditorEncryptedAmount` must be present.   |
| `AuditorEncryptedAmount` | Conditional | `string`  | `BLOB`        | N/A                           | A 66-byte ElGamal ciphertext encrypting the holder's balance under the new auditor key. Reuses `sfAuditorEncryptedAmount` from XLS-0096. Present to migrate holder's auditor mirror. At least one of this field and `IssuerEncryptedAmount` must be present. |
| `ZKProof`                | Yes         | `string`  | `BLOB`        | N/A                           | A single compact Chaum-Pedersen equality proof proving the new ciphertext(s) encrypt the same value as the on-ledger mirror(s). When both fields are present, the proof covers both statements under one Fiat-Shamir challenge.                              |

The key the holder's existing `sfIssuerEncryptedBalance` is encrypted under is not carried on the transaction. It is resolved from ledger state, from `IssuerMirrorEncryptionKey` on the holder's `MPToken` or, for a mirror never rewritten since this amendment activated, from `InitialIssuerEncryptionKey` on the issuance. Section 5.4.6 states the rule and Section 6.8 explains why it is resolved rather than submitted.

#### 5.4.2. Transaction Fee

**Fee Structure:** Custom

This transaction requires 10x the base fee because it carries a 128-byte zero-knowledge proof requiring elliptic curve verification, consistent with the XLS-0096 confidential transactions.

#### 5.4.3. Failure Conditions

##### 5.4.3.1. Data Verification

1. Either the `ConfidentialMPTKeyRotation` or the `ConfidentialTransfer` amendment is not enabled. (`temDISABLED`)
2. Issuer mode: `Holder` is present but `Account` is not the issuer of the `MPTokenIssuanceID`. (`temMALFORMED`)
3. Issuer mode(`Holder` is present): `Account` is the same as `Holder`. (`temMALFORMED`)
4. Holder mode(`Holder` is absent): `Account` is the issuer. (`temMALFORMED`)
5. Neither `IssuerEncryptedAmount` nor `AuditorEncryptedAmount` is present. (`temMALFORMED`)
6. Any present `IssuerEncryptedAmount` or `AuditorEncryptedAmount` has an invalid length or represents an invalid elliptic curve point. (`temBAD_CIPHERTEXT`)
7. `ZKProof` length is not exactly the expected proof size for the detected mode. (128 bytes in every mode - see Section 11) (`temMALFORMED`)

##### 5.4.3.2. Protocol-Level Failures

1. The `Account` does not exist. (`terNO_ACCOUNT`)
2. The `MPTokenIssuance` does not exist. (`tecOBJECT_NOT_FOUND`)
3. The issuance does not have the `lsfMPTCanHoldConfidentialBalance` flag set, or has no registered `sfIssuerEncryptionKey`. (`tecNO_PERMISSION`)
4. Issuer mode: the specified `Holder` account does not exist. (`tecNO_TARGET`)
5. The target holder's `MPToken` object does not exist. (`tecOBJECT_NOT_FOUND`)
6. The target holder's `MPToken` has no `sfIssuerEncryptedBalance`, there is no mirror to re-encrypt. (`tecNO_PERMISSION`)
7. `AuditorEncryptedAmount` is present but the issuance has no registered `sfAuditorEncryptionKey`. (`tecNO_PERMISSION`)
8. `IssuerEncryptedAmount` is present but `IssuerKeyMirrorEpoch` already equals `IssuerKeyEpoch`; the issuer mirror is already current. (`tecNO_PERMISSION`)
9. Issuer mode, auditor-only migration (`AuditorEncryptedAmount` present, `IssuerEncryptedAmount` absent): `IssuerKeyMirrorEpoch` does not equal `IssuerKeyEpoch`; the issuer mirror must be migrated first. (`tecNO_PERMISSION`)
10. `AuditorEncryptedAmount` is present, the holder already has an `sfAuditorEncryptedBalance`, and `AuditorKeyMirrorEpoch` already equals `AuditorKeyEpoch`; the auditor mirror is already current. First-time registration of an auditor mirror is exempt. (`tecNO_PERMISSION`)
11. Holder mode: `sfConfidentialBalanceInbox` is absent or is not the canonical encrypted zero — the holder must run `ConfidentialMPTMergeInbox` first. (`tecNO_PERMISSION`)
12. Issuer mode: `ZKProof` fails the compact Chaum-Pedersen equality proof verification. (`tecBAD_PROOF`)
13. Holder mode: `ZKProof` fails the cross-key equality proof verification. (`tecBAD_PROOF`)

#### 5.4.4. State Changes

**On Success (`tesSUCCESS`):**

If `IssuerEncryptedAmount` is present:

1. `sfIssuerEncryptedBalance` on the holder's `MPToken` is replaced by `IssuerEncryptedAmount`.
2. `sfIssuerKeyMirrorEpoch` on the `MPToken` is set to the issuance's current `sfIssuerKeyEpoch`.
3. `sfIssuerMirrorEncryptionKey` on the `MPToken` is set to the issuance's current `sfIssuerEncryptionKey`, creating the field if the holder did not previously carry it.

If `AuditorEncryptedAmount` is present:

1. `sfAuditorEncryptedBalance` on the holder's `MPToken` is set to `AuditorEncryptedAmount`, creating the field if the holder did not previously have an auditor mirror.
2. `sfAuditorKeyMirrorEpoch` on the `MPToken` is set to the issuance's current `sfAuditorKeyEpoch`, unless that epoch is 0, in which case the field is left absent. An absent mirror epoch is equivalent to 0, so this only arises on first-time registration of an auditor mirror before any auditor key rotation has occurred.

In both cases `ConfidentialBalanceVersion` is left unchanged.

#### 5.4.5. Example JSON

Which of `IssuerEncryptedAmount` and `AuditorEncryptedAmount` a transaction carries depends on the use case, at least one must be present, and both may be. The two modes differ only in the presence of `Holder`.

Issuer mode:

```json
{
  "TransactionType": "ConfidentialMPTMirrorUpdate",
  "Account": "rIssuerAccountAddress",
  "MPTokenIssuanceID": "000000012A9F1D3C...",
  "Holder": "rHolderAccountAddress",
  "IssuerEncryptedAmount": "02f3a4b5c6d7e8...",
  "AuditorEncryptedAmount": "02c3d4e5f6a7b8...",
  "ZKProof": "a7f3c1d8e2b9...",
  "Fee": "100",
  "Sequence": 44
}
```

Holder mode:

```json
{
  "TransactionType": "ConfidentialMPTMirrorUpdate",
  "Account": "rHolderAccountAddress",
  "MPTokenIssuanceID": "000000012A9F1D3C...",
  "IssuerEncryptedAmount": "02f3a4b5c6d7e8...",
  "AuditorEncryptedAmount": "02c3d4e5f6a7b8...",
  "ZKProof": "b8e4d2c9f3a1...",
  "Fee": "100",
  "Sequence": 45
}
```

#### 5.4.6. Proof Constructions

`ConfidentialMPTMirrorUpdate` has six mode combinations, determined by `Holder` presence and by which of `IssuerEncryptedAmount` / `AuditorEncryptedAmount` the transaction carries. Each is discharged by its own compact sigma protocol over secp256k1, and each is 128 bytes and bound to the transaction by the context hash of Section 4.8. This section states what each proof establishes.

Every variant proves the same thing: that the new ciphertext or ciphertexts encrypt the same balance as a ciphertext already on the ledger, without revealing it. They differ in which ledger ciphertext serves as the anchor and which secret key decrypts it. The anchor is always bound by a secret key rather than by encryption randomness, because these ciphertexts accumulate homomorphically and no party knows the aggregate randomness of its own current ciphertext.

**Issuer mode** anchors to the holder's on-ledger `IssuerEncryptedBalance`, decrypted with the issuer secret key. That mirror is the issuer's only source of the balance, which is why the issuer can migrate the auditor mirror without holding the auditor secret key.

- Issuer mirror: proves `IssuerEncryptedAmount` encrypts the balance the mirror encodes under the pre-rotation issuer key. The pre-rotation key is from the mirror's `IssuerMirrorEncryptionKey` or the issuance's `InitialIssuerEncryptionKey` (see below).
- Auditor mirror only: proves `AuditorEncryptedAmount` encrypts the balance the mirror encodes under the _current_ issuer key. Condition 9 of Section 5.4.3.2 requires the issuer mirror to be up to date for this variant, so no historical key is involved. The same relation covers auditor late registration, which differs only in the ledger precondition - the auditor mirror is absent rather than stale.
- Both mirrors: a single AND-composed proof covering both statements under one Fiat-Shamir challenge.

**Resolving the anchor key**: `ConfidentialMPTMirrorUpdate` issuer modes need the key the existing mirror ciphertext is encrypted under for the equality proof, and `ConfidentialMPTClawback` needs the same key to verify its proof (Section 5.10.3.2). It is resolved entirely from ledger state, in this order:

1. `IssuerMirrorEncryptionKey` on the holder's `MPToken`, when present. It was written by whichever transaction last moved the mirror to a new epoch, so it is the key the mirror is encrypted under regardless of how many rotations have happened since.
2. Otherwise `InitialIssuerEncryptionKey` on the `MPTokenIssuance`. An absent stamp places the mirror at epoch 0 by I17, and this field holds the epoch 0 key.
3. Otherwise the currently registered `IssuerEncryptionKey`. For migration this case only arises when the issuer key has never been rotated, in which case the mirror is current and no issuer-mirror migration is admissible in the first place. For clawback it is the ordinary case on an issuance that has never rotated.

**Holder mode** anchors to the holder's own `ConfidentialBalanceSpending`, decrypted with sk_H. Knowledge of sk_H both establishes key possession and decrypts the anchor, so a holder who cannot decrypt their spending balance cannot prove any claimed balance. The same three variants exist as in issuer mode, and the auditor-only variant is a separate relation rather than the issuer-mirror one re-parameterized. All three require `ConfidentialBalanceInbox` to be the canonical encrypted zero - see condition 11 of Section 5.4.3.2 - because the spending balance encodes only the spendable portion while the mirrors encode the total. Holder mode is what makes migration possible at all in the issuer key loss scenario, where the issuer cannot perform active re-encryption. See Section 9.

Two limits on what these proofs establish are worth stating. Holder-mode proofs never reference the mirror they overwrite, so they are equivalent to issuer mode only under the XLS-0096 invariant that a holder's issuer mirror encodes the same balance as spending plus inbox; that invariant is a hypothesis of these proofs, not a consequence. And no variant references a holder's prior auditor mirror: an auditor mirror migration is proved equal to the issuer's decryption of the issuer mirror or to the holder's spending balance, never to the auditor mirror it replaces.

**Shared randomness**: the two AND-composed variants reuse a single randomness value for both new ciphertexts, which is what keeps them at 128 bytes rather than 160. It also forces the two ciphertexts to share an identical first component, and the sigma equations do not themselves constrain the auditor one, so the transaction MUST be rejected when the two do not match. The randomness MUST be sampled freshly for every transaction and every holder; reusing one value across a migration batch exposes every pairwise balance difference on-ledger.

### 5.5. Transaction: `ConfidentialMPTHolderKeyUpdate`

Allows a holder to rotate their ElGamal key (rotation mode), authorize key replacement after key loss (recovery mode), or revoke a pending recovery authorization (cancel mode). Mode is selected by transaction flag.

- **Voluntary key rotation** (`tfHolderKeyRotation`): Holder decrypts `ConfidentialBalanceSpending` and `ConfidentialBalanceInbox`, re-encrypts both under pk_H', and submits a single AND-composed proof covering the spending balance and possession of the new key. Atomic - no issuer involvement. The holder may optionally run `ConfidentialMPTMergeInbox` before rotating, so that `ConfidentialBalanceInbox` is `EncZero` under pk_H' and publicly verifiable as such. This costs an extra transaction.
- **Key loss recovery authorization** (`tfHolderKeyRecovery`): Holder registers pk_H' as `RecoveryKey` on `MPToken`, consenting to issuer-completed recovery via `ConfidentialMPTRecoverBalance`.
- **Recovery cancellation** (`tfCancelRecovery`): Holder clears a pending `RecoveryKey` from their `MPToken`, revoking their consent to issuer-completed recovery. No cryptographic proof is required; the holder's signing key signature is sufficient authorization to cancel their own pending authorization.

#### 5.5.1. Fields

| Field Name                    | Required?   | JSON Type | Internal Type | Default Value                    | Description                                                                                                                                                                                                                                  |
| :---------------------------- | :---------- | :-------- | :------------ | :------------------------------- | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `TransactionType`             | Yes         | `string`  | `UINT16`      | `ConfidentialMPTHolderKeyUpdate` | `ConfidentialMPTHolderKeyUpdate`.                                                                                                                                                                                                            |
| `Account`                     | Yes         | `string`  | `ACCOUNTID`   | N/A                              | The holder account.                                                                                                                                                                                                                          |
| `MPTokenIssuanceID`           | Yes         | `string`  | `UINT192`     | N/A                              | The unique identifier of the MPT issuance.                                                                                                                                                                                                   |
| `Flags`                       | Yes         | `number`  | `UINT32`      | N/A                              | Exactly one of `tfHolderKeyRotation`, `tfHolderKeyRecovery`, or `tfCancelRecovery`.                                                                                                                                                          |
| `HolderEncryptionKey`         | Conditional | `string`  | `BLOB`        | N/A                              | The holder's new 33-byte compressed ElGamal public key `pk_H'`. **Required** in Rotation and Recovery modes; **must be absent** in Cancel mode. Must differ from the current value.                                                          |
| `ConfidentialBalanceSpending` | Conditional | `string`  | `BLOB`        | N/A                              | A 66-byte ElGamal ciphertext under pk_H'. **Required** in Rotation mode; **must be absent** in Recovery and Cancel modes.                                                                                                                    |
| `ConfidentialBalanceInbox`    | Conditional | `string`  | `BLOB`        | N/A                              | A 66-byte ElGamal ciphertext under pk_H'. **Required** in Rotation mode; **must be absent** in Recovery and Cancel modes.                                                                                                                    |
| `ZKProof`                     | Conditional | `string`  | `BLOB`        | N/A                              | **Required** in Rotation and Recovery modes; **must be absent** in Cancel mode. Rotation uses a single AND-composed proof covering the spending balance re-encryption and possession of the new key; Recovery uses a standalone Schnorr PoK. |

#### 5.5.2. Flags

| Flag Name             | Hex Value    | Decimal Value | Description                                                                                                                          |
| :-------------------- | :----------- | :------------ | :----------------------------------------------------------------------------------------------------------------------------------- |
| `tfHolderKeyRotation` | `0x00000001` | 1             | Rotation mode: re-encrypt the spending and inbox balances under the new key in this transaction, revoking any pending `RecoveryKey`. |
| `tfHolderKeyRecovery` | `0x00000002` | 2             | Recovery mode: register the new key as `sfRecoveryKey` for issuer-completed recovery.                                                |
| `tfCancelRecovery`    | `0x00000004` | 4             | Cancel mode: clear a pending `RecoveryKey` from the holder's `MPToken`.                                                              |

Exactly one of the three flags must be set.

#### 5.5.3. Transaction Fee

**Fee Structure:** Custom

This transaction requires 10x the base fee because rotation and recovery modes carry a zero-knowledge proof requiring elliptic curve verification, 224 bytes and 64 bytes respectively, consistent with the XLS-0096 confidential transactions. Cancel mode carries no proof but pays the same fee, because the fee is set per transaction type rather than per mode.

#### 5.5.4. Failure Conditions

##### 5.5.4.1. Data Verification

1. Either the `ConfidentialMPTKeyRotation` or the `ConfidentialTransfer` amendment is not enabled. (`temDISABLED`)
2. Neither `tfHolderKeyRotation`, `tfHolderKeyRecovery`, nor `tfCancelRecovery` is set, or more than one is set. (`temINVALID_FLAG`)
3. Account is the issuer of `MPTokenIssuanceID` - the issuer cannot hold confidential balances. (`temMALFORMED`)
4. Rotation or recovery mode: `HolderEncryptionKey` is absent, is not exactly 33 bytes, or is not a well-formed compressed secp256k1 point. (`temMALFORMED`)
5. Rotation mode: `ConfidentialBalanceSpending` or `ConfidentialBalanceInbox` is missing. (`temMALFORMED`)
6. Recovery or cancel mode: `ConfidentialBalanceSpending` or `ConfidentialBalanceInbox` is present. (`temMALFORMED`)
7. Cancel mode: `HolderEncryptionKey` or `ZKProof` is present - cancel mode requires no additional fields beyond `TransactionType`, Account, `MPTokenIssuanceID`, and Flags. (`temMALFORMED`)
8. Any present `ConfidentialBalanceSpending` or `ConfidentialBalanceInbox` has an invalid length or represents an invalid elliptic curve point. (`temBAD_CIPHERTEXT`)
9. Rotation or recovery mode: `ZKProof` is absent or its length is not exactly the expected size for the selected mode. (224 bytes in rotation mode, 64 bytes in recovery mode - see Section 11) (`temMALFORMED`)

##### 5.5.4.2. Protocol-Level Failures

1. The `MPTokenIssuance` or the holder's `MPToken` object does not exist. (`tecOBJECT_NOT_FOUND`)
2. The issuance does not have the `lsfMPTCanHoldConfidentialBalance` flag set. (`tecNO_PERMISSION`)
3. The holder's `MPToken` is missing confidential state (`HolderEncryptionKey`, `ConfidentialBalanceSpending`, or `ConfidentialBalanceInbox`). (`tecNO_PERMISSION`)
4. Rotation or recovery mode: `HolderEncryptionKey` equals the current on-ledger `HolderEncryptionKey` (no-op). (`tecNO_PERMISSION`)
5. Rotation mode: `IssuerKeyMirrorEpoch` does not equal `IssuerKeyEpoch`; the issuer mirror must be migrated before rotating. (`tecNO_PERMISSION`)
6. Rotation mode: an auditor key is configured and `AuditorEncryptedBalance` is absent or `AuditorKeyMirrorEpoch` does not equal `AuditorKeyEpoch`; the auditor mirror must be initialized or migrated before rotating. (`tecNO_PERMISSION`)
7. Recovery mode: `RecoveryKey` is already set on the `MPToken` - a pending recovery authorization exists. (`tecNO_PERMISSION`)
8. Cancel mode: `RecoveryKey` is not set on the `MPToken` - nothing to cancel. (`tecNO_PERMISSION`)
9. Recovery mode: `ZKProof` (Schnorr PoK) fails to verify against `HolderEncryptionKey`. (`tecBAD_PROOF`)
10. Rotation mode: `ZKProof` fails to verify. It is a single AND-composed proof establishing that the submitted `ConfidentialBalanceSpending` and `ConfidentialBalanceInbox` each encrypt under `HolderEncryptionKey` the same value the corresponding on-ledger ciphertext encrypts under the old key, and that the submitter possesses the secret key for `HolderEncryptionKey`. Both balances are covered because both are encrypted under the holder key, so a rotation carrying only the spending balance would leave the inbox decryptable exclusively under a key the holder is replacing. (`tecBAD_PROOF`)

#### 5.5.5. State Changes

**On Success (`tesSUCCESS`):**

**Rotation mode**:

1. `HolderEncryptionKey` on `MPToken` ← new key value
2. `ConfidentialBalanceSpending` on `MPToken` ← new ciphertext
3. `ConfidentialBalanceInbox` on `MPToken` ← new ciphertext
4. `ConfidentialBalanceVersion` on `MPToken` ← `ConfidentialBalanceVersion` + 1
5. `RecoveryKey` on `MPToken` ← cleared (field removed) if one was pending

**Recovery mode**:

1. `RecoveryKey` on `MPToken` ← `HolderEncryptionKey` (new value)
2. All other fields unchanged

**Cancel mode**:

1. `RecoveryKey` on `MPToken` ← cleared (field removed)
2. All other fields unchanged - `HolderEncryptionKey`, `ConfidentialBalanceSpending`, `ConfidentialBalanceInbox`, `ConfidentialBalanceVersion` are not modified

#### 5.5.6. Example JSON

Rotation mode:

```json
{
  "TransactionType": "ConfidentialMPTHolderKeyUpdate",
  "Account": "rHolderAccountAddress",
  "MPTokenIssuanceID": "000000012A9F1D3C...",
  "Flags": 1,
  "HolderEncryptionKey": "02c7d8e9f0a1b2...",
  "ConfidentialBalanceSpending": "02d7e8f9a0b1c2...",
  "ConfidentialBalanceInbox": "02e7f8a9b0c1d2...",
  "ZKProof": "c9f5e3d1a2b8...",
  "Fee": "100",
  "Sequence": 46
}
```

Recovery mode:

```json
{
  "TransactionType": "ConfidentialMPTHolderKeyUpdate",
  "Account": "rHolderAccountAddress",
  "MPTokenIssuanceID": "000000012A9F1D3C...",
  "Flags": 2,
  "HolderEncryptionKey": "03a9b8c7d6e5f4...",
  "ZKProof": "d1a6f4e2b3c9...",
  "Fee": "100",
  "Sequence": 47
}
```

Cancel mode:

```json
{
  "TransactionType": "ConfidentialMPTHolderKeyUpdate",
  "Account": "rHolderAccountAddress",
  "MPTokenIssuanceID": "000000012A9F1D3C...",
  "Flags": 4,
  "Fee": "100",
  "Sequence": 48
}
```

#### 5.5.7. Proof Constructions

Rotation and recovery modes each carry a proof, bound to the transaction by the context hash of Section 4.8. Cancel mode carries none.

**Rotation mode** establishes three statements under one Fiat-Shamir challenge: that the submitted `ConfidentialBalanceSpending` encrypts under the new `HolderEncryptionKey` the same value the on-ledger spending balance encrypts under the old one, that the submitted `ConfidentialBalanceInbox` does the same for the inbox, and that the submitter holds the secret key for the new `HolderEncryptionKey`. Both anchors are decrypted with the old holder secret key, so only a holder who can still read their own balances can rotate.

Both balances are covered because both are encrypted under the holder key. Migrating the spending balance alone would leave the inbox readable only under the key being abandoned, stranding any amount received but not yet merged.

The possession statement is what separates this proof from the mirror migrations of Section 5.4.6. There the new ciphertext is produced under a key already registered on the `MPTokenIssuance`, so possession is established by the registration itself. Here the target key is chosen by the submitter, and without the statement a holder could re-encrypt their balance under a key nobody holds, placing it permanently beyond reach.

**Recovery mode** establishes possession of the secret key for the `HolderEncryptionKey` being registered as `RecoveryKey`. No balance is read, re-encrypted, or referenced, which is why recovery mode leaves every balance field unchanged (Section 5.5.5).

### 5.6. Transaction: `ConfidentialMPTRecoverBalance`

Completes holder key loss recovery. The issuer re-encrypts the holder's balance under the authorized `RecoveryKey` and submits a compact Chaum-Pedersen equality proof. The transaction is rejected unless `RecoveryKey` is present - the issuer cannot act without prior holder authorization.

#### 5.6.1. Fields

| Field Name                    | Required? | JSON Type | Internal Type | Default Value                   | Description                                                                                                                                 |
| :---------------------------- | :-------- | :-------- | :------------ | :------------------------------ | :------------------------------------------------------------------------------------------------------------------------------------------ |
| `TransactionType`             | Yes       | `string`  | `UINT16`      | `ConfidentialMPTRecoverBalance` | `ConfidentialMPTRecoverBalance`.                                                                                                            |
| `Account`                     | Yes       | `string`  | `ACCOUNTID`   | N/A                             | The issuer account.                                                                                                                         |
| `MPTokenIssuanceID`           | Yes       | `string`  | `UINT192`     | N/A                             | The unique identifier of the MPT issuance.                                                                                                  |
| `Holder`                      | Yes       | `string`  | `ACCOUNTID`   | N/A                             | The holder account being recovered.                                                                                                         |
| `ConfidentialBalanceSpending` | Yes       | `string`  | `BLOB`        | N/A                             | A 66-byte ElGamal ciphertext: the holder's total confidential balance re-encrypted under `RecoveryKey`. Becomes the new spending balance.   |
| `ZKProof`                     | Yes       | `string`  | `BLOB`        | N/A                             | Compact Chaum-Pedersen equality proof that `ConfidentialBalanceSpending` encrypts the same value as the on-ledger `IssuerEncryptedBalance`. |

**Note on** `ConfidentialBalanceInbox`: After recovery, `ConfidentialBalanceInbox` is reset to `EncZero`(pk_H'). No value is lost. The issuer mirror `IssuerEncryptedBalance` always reflects the holder's total confidential balance b = b_s + b_in - guaranteed by XLS-0096's equality proof invariant on every transaction. When the issuer completes `ConfidentialMPTRecoverBalance`, they decrypt the mirror to get the full b and re-encrypt it entirely into `ConfidentialBalanceSpending` under pk_H'. The inbox is reset to zero because the full balance - including what was in the inbox - is now consolidated into spending.

Additionally, any incoming confidential transfers that arrived in the inbox during the recovery window (between the holder's Step 1 authorization and the issuer's Step 2 completion) are also captured - incoming sends update `IssuerEncryptedBalance` homomorphically, so the issuer mirror at Step 2 already reflects those transfers. The holder effectively receives a free merge as part of recovery.

#### 5.6.2. Transaction Fee

**Fee Structure:** Custom

This transaction requires 10x the base fee because it carries a 128-byte zero-knowledge proof requiring elliptic curve verification, consistent with the XLS-0096 confidential transactions.

#### 5.6.3. Failure Conditions

##### 5.6.3.1. Data Verification

1. Either the `ConfidentialMPTKeyRotation` or the `ConfidentialTransfer` amendment is not enabled. (`temDISABLED`)
2. Account is not the issuer of `MPTokenIssuanceID`. (`temMALFORMED`)
3. Account is the same as Holder. (`temMALFORMED`)
4. `ConfidentialBalanceSpending` has an invalid length or represents an invalid elliptic curve point. (`temBAD_CIPHERTEXT`)
5. `ZKProof` is absent or its length is not exactly the expected compact Chaum-Pedersen equality proof size. (128 bytes - see Section 11) (`temMALFORMED`)

##### 5.6.3.2. Protocol-Level Failures

1. The specified Holder account does not exist. (`tecNO_TARGET`)
2. The `MPTokenIssuance` or the holder's `MPToken` object does not exist. (`tecOBJECT_NOT_FOUND`)
3. The issuance does not have the `lsfMPTCanHoldConfidentialBalance` flag set. (`tecNO_PERMISSION`)
4. The holder's `MPToken` has no pending `RecoveryKey` - holder has not authorized recovery. (`tecNO_PERMISSION`)
5. `IssuerEncryptedBalance` is absent or `IssuerKeyMirrorEpoch` does not equal `IssuerKeyEpoch`; the issuer must first migrate the issuer mirror via `ConfidentialMPTMirrorUpdate` before recovery can proceed. (`tecNO_PERMISSION`)
6. `ZKProof` fails the compact Chaum-Pedersen equality verification against `IssuerEncryptedBalance` and `RecoveryKey`. (`tecBAD_PROOF`)

#### 5.6.4. State Changes

**On Success (`tesSUCCESS`):**

1. `HolderEncryptionKey` on `MPToken` ← `RecoveryKey`
2. `ConfidentialBalanceSpending` on `MPToken` ← new ciphertext
3. `ConfidentialBalanceInbox` on `MPToken` ← `EncZero` (canonical encryption of zero under pk_H')
4. `ConfidentialBalanceVersion` on `MPToken` ← `ConfidentialBalanceVersion` + 1
5. `RecoveryKey` on `MPToken` ← cleared (field removed)
6. `IssuerEncryptedBalance` and `AuditorEncryptedBalance` unchanged

#### 5.6.5. Example JSON

```json
{
  "TransactionType": "ConfidentialMPTRecoverBalance",
  "Account": "rIssuerAccountAddress",
  "MPTokenIssuanceID": "000000012A9F1D3C...",
  "Holder": "rHolderAccountAddress",
  "ConfidentialBalanceSpending": "02d9e0f1a2b3c4...",
  "ZKProof": "e2b7a5f3c4d1...",
  "Fee": "100",
  "Sequence": 45
}
```

#### 5.6.6. Proof Constructions

The proof establishes that the submitted `ConfidentialBalanceSpending` encrypts under the holder's `RecoveryKey` the same value the holder's `IssuerEncryptedBalance` encrypts under the issuance's `IssuerEncryptionKey`. It is bound to the transaction by the context hash of Section 4.8.

The anchor is the issuer mirror, decrypted with the issuer secret key. That is what lets the issuer reconstruct a balance for a holder who can no longer read their own, and it is also why recovery cannot proceed without the issuer: no other party can decrypt that ciphertext. Condition 5 of Section 5.6.3.2 requires the mirror to be at the current issuer key epoch, so the anchor is always under the registered `IssuerEncryptionKey` and no historical key resolution arises here. An issuer holding a stale mirror migrates it with `ConfidentialMPTMirrorUpdate` first.

The proof covers the spending balance only. The inbox is not proved because it is not reconstructed: the issuer mirror already encodes the holder's total balance, so writing that total into spending and setting the inbox to the canonical encrypted zero (Section 5.6.4) preserves the holder's balance without double counting.

### 5.7. Transaction: `ConfidentialMPTConvert`

`ConfidentialMPTConvert` is defined in XLS-0096. This amendment adds a mirror-staleness precondition (Section 4.6.1) for holders whose confidential state is already initialized, and specifies the mirror epochs written when a holder initializes confidential state.

#### 5.7.1. Fields

No changes from XLS-0096.

#### 5.7.2. Transaction Fee

No changes from XLS-0096.

#### 5.7.3. Failure Conditions

##### 5.7.3.1. Data Verification

This amendment introduces no new data-verification (`tem`) failures.

##### 5.7.3.2. Protocol-Level Failures

1. The holder's confidential state is already initialized and the holder's issuer mirror is not current. (`tecNO_PERMISSION`)
2. The holder's confidential state is already initialized, an auditor key is configured, and the holder's auditor mirror is not current. (`tecNO_PERMISSION`)

A holder initializing confidential state for the first time cannot be stale, because the mirrors are created under the current keys in the same transaction. These conditions therefore apply only to already-initialized holders.

#### 5.7.4. State Changes

**On Success (`tesSUCCESS`):**

All state changes specified in XLS-0096 §7.5 apply unchanged. This amendment adds the following:

- When confidential state is initialized for the first time, the mirror epochs are set to the corresponding key epochs: `IssuerKeyMirrorEpoch` ← `IssuerKeyEpoch`, and `AuditorKeyMirrorEpoch` ← `AuditorKeyEpoch` when an auditor key is configured. An epoch of 0 is omitted from ledger storage rather than written explicitly.
- For an already-initialized holder, `IssuerKeyMirrorEpoch` and `AuditorKeyMirrorEpoch` retain their existing values, since both mirrors are current as a precondition of success.
- On first-time initialization, `IssuerMirrorEncryptionKey` ← `IssuerEncryptionKey`, alongside the mirror epochs and under the same convention: the field is omitted when `IssuerKeyEpoch` is 0. A holder initializing after a rotation is therefore stamped at the current epoch, not left to be read as epoch 0.
- For an already-initialized holder, `IssuerMirrorEncryptionKey` retains its existing value. The mirror is current as a precondition of success, so the delta is under the key the mirror already carries and the ciphertext does not change keys.

#### 5.7.5. Example JSON

No changes from XLS-0096.

### 5.8. Transaction: `ConfidentialMPTSend`

`ConfidentialMPTSend` is defined in XLS-0096. This amendment adds a mirror-staleness precondition (Section 4.6.1) for both parties.

#### 5.8.1. Fields

No changes from XLS-0096.

#### 5.8.2. Transaction Fee

No changes from XLS-0096.

#### 5.8.3. Failure Conditions

##### 5.8.3.1. Data Verification

This amendment introduces no new data-verification (`tem`) failures.

##### 5.8.3.2. Protocol-Level Failures

1. The sender's issuer mirror is not current. (`tecNO_PERMISSION`)
2. An auditor key is configured and the sender's auditor mirror is not current. (`tecNO_PERMISSION`)
3. The destination's issuer mirror is not current. (`tecNO_PERMISSION`)
4. An auditor key is configured and the destination's auditor mirror is not current. (`tecNO_PERMISSION`)

#### 5.8.4. State Changes

**On Success (`tesSUCCESS`):**

All state changes specified in XLS-0096 §8.4 apply unchanged. No field introduced by this amendment changes: both parties' mirrors are current as a precondition of success, so `IssuerKeyMirrorEpoch`, `AuditorKeyMirrorEpoch`, and `IssuerMirrorEncryptionKey` retain their existing values on both the sender's and the destination's `MPToken`.

#### 5.8.5. Example JSON

No changes from XLS-0096.

### 5.9. Transaction: `ConfidentialMPTConvertBack`

`ConfidentialMPTConvertBack` is defined in XLS-0096. This amendment adds a mirror-staleness precondition (Section 4.6.1).

#### 5.9.1. Fields

No changes from XLS-0096.

#### 5.9.2. Transaction Fee

No changes from XLS-0096.

#### 5.9.3. Failure Conditions

##### 5.9.3.1. Data Verification

This amendment introduces no new data-verification (`tem`) failures.

##### 5.9.3.2. Protocol-Level Failures

1. The holder's issuer mirror is not current. (`tecNO_PERMISSION`)
2. An auditor key is configured and the holder's auditor mirror is not current. (`tecNO_PERMISSION`)

#### 5.9.4. State Changes

**On Success (`tesSUCCESS`):**

All state changes specified in XLS-0096 §10.5 apply unchanged. No field introduced by this amendment changes: the holder's mirrors are current as a precondition of success, so `IssuerKeyMirrorEpoch`, `AuditorKeyMirrorEpoch`, and `IssuerMirrorEncryptionKey` retain their existing values.

#### 5.9.5. Example JSON

No changes from XLS-0096.

### 5.10. Transaction: `ConfidentialMPTClawback`

`ConfidentialMPTClawback` is defined in XLS-0096. This amendment adds no mirror-staleness precondition. The key against which the clawback proof is verified is resolved from the holder's mirror rather than the currently registered key, and both mirror epochs are rewritten on success.

#### 5.10.1. Fields

No changes from XLS-0096.

#### 5.10.2. Transaction Fee

No changes from XLS-0096.

#### 5.10.3. Failure Conditions

##### 5.10.3.1. Data Verification

This amendment introduces no new data-verification (`tem`) failures.

##### 5.10.3.2. Protocol-Level Failures

This amendment introduces no new protocol-level (`tec`) failures.

Clawback is not blocked by a stale issuer mirror, nor by an auditor mirror that is stale or absent. An `IssuerEncryptedBalance` must still be present, as XLS-0096 §12.4.2 requires, since the proof has no anchor without it. The clawback proof is verified against the key that mirror is encrypted under, resolved as in Section 5.4.6 rather than taken from the transaction, so a holder who is any number of epochs behind can still be clawed back. Producing the clawed-back amount requires decrypting that mirror, so the issuer needs the secret key for the resolved key, not for the currently registered one; Section 12.9 covers historical key retention and Section 9 the issuer key loss case. Whichever mirrors were stale or absent are repaired by the state changes below.

#### 5.10.4. State Changes

**On Success (`tesSUCCESS`):**

All state changes specified in XLS-0096 §11.4 apply unchanged. This amendment adds the following:

- `IssuerEncryptedBalance` ← canonical encrypted zero under the currently registered `IssuerEncryptionKey`, `IssuerKeyMirrorEpoch` ← `IssuerKeyEpoch`, and `IssuerMirrorEncryptionKey` ← `IssuerEncryptionKey`. As elsewhere, an epoch of 0 is omitted from ledger storage rather than written explicitly, and the recorded key is omitted with it.
- When the issuance has a registered `AuditorEncryptionKey`, `AuditorEncryptedBalance` ← canonical encrypted zero under that key, creating the field if the holder did not previously have an auditor mirror, and `AuditorKeyMirrorEpoch` ← `AuditorKeyEpoch` under the same epoch 0 omission convention. Clawback rebuilds the mirrors from a canonical zero rather than combining into them, so it can write one under the registered auditor key whatever state the holder was in. A holder whose confidential balance predates the auditor key registration therefore leaves clawback with an auditor mirror rather than still needing `ConfidentialMPTMirrorUpdate` to obtain one. When the issuance has no auditor key, no auditor mirror is written, since none is required.
- Because the mirrors it writes are encryptions of zero under the current keys, a clawed-back holder is left current on every mirror the issuance requires, even if the issuer mirror was stale and the auditor mirror stale or absent beforehand. No `ConfidentialMPTMirrorUpdate` is required afterwards.

#### 5.10.5. Example JSON

No changes from XLS-0096.

### 5.11. Permission: `ConfidentialMPTMirrorUpdate`

Per XLS-75 permission delegation, an account can grant another account permission to submit specific transaction types on its behalf. This amendment introduces **no new granular permissions**. The transaction-level permissions it introduces or modifies are specified in Sections 5.11 through 5.14.

#### 5.11.1. Permission Description

Grants the ability to submit `ConfidentialMPTMirrorUpdate` on behalf of the granting account, in both issuer mode and holder mode. Delegation is safe here because the transaction carries no encryption key at all: it re-encrypts a balance already on the ledger under a key already registered on `MPTokenIssuance`, the key the existing mirror is under is resolved from ledger state rather than submitted (Section 5.4.6), and the equality proof binds the result to that existing balance. A delegate can advance migration but can neither read nor move funds.

#### 5.11.2. Transaction Types Affected

`ConfidentialMPTMirrorUpdate`

#### 5.11.3. Permission Value

93, derived from transaction type 92.

### 5.12. Permission: `ConfidentialMPTHolderKeyUpdate`

#### 5.12.1. Permission Description

**Not delegable**, so this permission can never be granted. Rotation and recovery modes both register a submitter-chosen holder key, which would let a delegate take over the holder's confidential balance. Cancel mode carries no key, but delegability is set per transaction type and cannot be scoped to a single mode. This matches `ConfidentialMPTConvert`, which XLS-0096 makes non-delegable for the same reason.

#### 5.12.2. Transaction Types Affected

`ConfidentialMPTHolderKeyUpdate`

#### 5.12.3. Permission Value

94, derived from transaction type 93. The value is reserved but can never be granted.

### 5.13. Permission: `ConfidentialMPTRecoverBalance`

#### 5.13.1. Permission Description

Grants the ability to submit `ConfidentialMPTRecoverBalance` on behalf of the issuer, completing a recovery the holder has already authorized. Delegation is safe here because the delegate does not choose the destination key: the transaction is rejected unless `RecoveryKey` is already present on the holder's `MPToken` (Section 5.6.3), and only the holder can set that field. The worst a delegate can do is complete an authorized recovery, or decline to.

#### 5.13.2. Transaction Types Affected

`ConfidentialMPTRecoverBalance`

#### 5.13.3. Permission Value

95, derived from transaction type 94.

### 5.14. Permission: `MPTokenIssuanceSet`

#### 5.14.1. Permission Description

Unchanged by this amendment. It continues to grant the ability to send `MPTokenIssuanceSet` on behalf of delegator, but a delegated submission **MUST NOT** carry `IssuerEncryptionKey` or `AuditorEncryptionKey`, so a delegate cannot rotate or register an issuer or auditor key.

#### 5.14.2. Transaction Types Affected

`MPTokenIssuanceSet`

#### 5.14.3. Permission Value

57, derived from transaction type 56, which predates this amendment.

## 6. Rationale

### 6.1. Decrypt-then-Re-encrypt over Proxy Re-encryption

Standard PRE constructions require bilinear pairings, incompatible with secp256k1. PRE also introduces new trust assumptions. Decrypt-then-re-encrypt uses existing primitives and the issuer already has visibility by design.

### 6.2. Migration Completeness Not Enforced

A rotation is accepted while holders are still on earlier epochs, and a holder any number of epochs behind is migrated in one step. The protocol does not force the issuer to update every holder after each rotation.

Migrating a holder from an older epoch requires the key of that epoch, so an issuer that lets holders fall behind has to manage a history of its issuer keys. An issuer that updates every holder after each rotation only ever needs the most recent one. The rule is deliberately flexible. Updating every holder after each rotation is the recommended practice, and enforcing it belongs to the application layer rather than the protocol.

### 6.3. Per-Holder Migration Transactions

`ConfidentialMPTMirrorUpdate` migrates a single holder, and the issuer traverses the holders list off-chain. A single on-ledger bulk migration was rejected because it would require unbounded computational work without reducing the payload size—the issuer must still provide a fresh ciphertext and equality proof for every holder. Additionally, per-holder transactions offer better fault isolation, preventing a single failure from reverting the entire migration list.

### 6.4. Issuer On-Chain Involvement in Holder Key Loss Recovery

A holder who has lost sk_H can no longer decrypt their own balances, so the only ciphertext left to anchor a proof on is the issuer mirror, and proving against it requires sk_I. Learning b in plaintext does not substitute for that, and it does not matter who supplies b off-chain, so the issuer cannot simply disclose the balance and let the holder act alone. Recovery therefore completes on-chain through `ConfidentialMPTRecoverBalance`.

A holder who still holds sk_H needs none of this: holder self-migration anchors on their own spending balance and never touches sk_I (Section 5.4.6).

### 6.5. Mode Detection

`ConfidentialMPTMirrorUpdate` needs no flag, because `Holder` is a natural discriminator. It identifies the account whose mirrors are migrated, which is meaningful only when someone other than that account submits the transaction, so if `Holder` is present, the issuer is migrating the holder's mirrors (issuer mode); if it's absent, the submitter is migrating their own mirrors (holder self-migration mode).

`ConfidentialMPTHolderKeyUpdate` selects its mode with explicit flags (`tfHolderKeyRotation` / `tfHolderKeyRecovery` / `tfCancelRecovery`) because no field could serve as the discriminator: rotation and recovery both carry `HolderEncryptionKey`, and cancel mode carries no additional field at all.

### 6.6. Staleness Rejected in Preclaim

`ConfidentialMPTConvert`, `ConfidentialMPTSend` and `ConfidentialMPTConvertBack` reject a stale mirror during preclaim, before running proof verification. The proof check alone is insufficient because it validates ciphertexts against issuance keys without taking the holder's on-ledger mirror as input, meaning a stale mirror passes verification just like a current one. If applied, the transaction would homomorphically add a delta encrypted under the current key to a mirror encrypted under an older key, producing a corrupted ciphertext that no key can decrypt. Downstream invariant checks will not catch this because they only verify balance conservation and field consistency, not ciphertext validity. Checking the epoch early also short-circuits heavy elliptic curve operations on invalid transactions.

### 6.7. Clawback Unblocked on a Stale Mirror

Clawback succeeds against a holder whose mirrors are stale or whose auditor mirror is missing, provided its proof is built against the key the stale mirror is encrypted under. Blocking it would only add a step, since the issuer would migrate the holder first and then claw back, and clawback rewrites both mirrors as canonical encrypted zero under the current keys, so the holder ends up current either way.

What clawback depends on is not a current mirror but the secret key for the epoch the mirror sits at, which the issuer needs to decrypt it and produce the proof. An issuer that retained that key claws back directly. An issuer that discarded it can neither claw back nor migrate that holder, and the mirror has to be migrated by the holder first, after which it sits under the currently registered key and clawback works again (Section 12.9). Section 4.6.2 covers why a stale mirror is no obstacle mechanically.

### 6.8. Anchor Keys Stored Rather Than Submitted

Rotation overwrites `IssuerEncryptionKey` in place, so the key a stale mirror is encrypted under is no longer on the ledger, and both issuer-mode migration and clawback need that key to verify their proof. Carrying it in the transaction is not viable because it would let the submitter choose the public key its own proof is checked against, which defeats the verification. Keeping a full key history on the issuance would grow without bound, and keeping only the epoch 0 key is insufficient, since a mirror can sit at epoch 3 while the issuance has reached epoch 5. `IssuerMirrorEncryptionKey` on each `MPToken` therefore records the key that holder's mirror is actually encrypted under and is rewritten whenever the mirror is, which is one field per holder and always exact. `InitialIssuerEncryptionKey` on the `MPTokenIssuance` covers the remaining case, a mirror not rewritten since this amendment activated and so carrying no per-holder stamp, where reading the absent stamp as epoch 0 requires the epoch 0 key to still be recoverable.

### 6.9. In-flight Proofs Left to Fail

A rotation replaces the holder's encryption key and re-encrypts both balances under it, so any in-flight transaction built against the old key or the old balances fails once the rotation lands, and the rotation itself fails if the holder's state changes first. The holder cannot avoid this by waiting for their own transactions to clear, because an incoming transfer changes their inbox, and the rotation proof covers the inbox too.

The protocol does not try to prevent it. The rejected transaction costs a fee and has to be rebuilt and resubmitted, and nothing else happens: no funds move and no field is left half updated. Clawback keeps working throughout, because it reads the issuer mirror rather than the holder's balances.

### 6.10. No Rotation Cooldown

Key rotation is deliberately unconstrained by rate limits, even though a malicious issuer could rotate every ledger to keep holders stale and block confidential transfers or conversions. We accept this capability because rotating maliciously is simply an issuer degrading their own token—a self-defeating scenario that a cooldown period wouldn't fix anyway. More importantly, rotation must remain unconstrained to handle emergency key compromises, where an issuer needs the flexibility to rotate immediately (or even twice in quick succession) without being blocked by a cooldown limit.

## 7. Backwards Compatibility

All new fields and transaction types are gated on the `ConfidentialMPTKeyRotation` amendment. Every new field is optional and an epoch of 0 is omitted from storage, so existing `MPTokenIssuance` and `MPToken` objects are unchanged and no state migration is required.

No transaction that is valid under the current rules becomes invalid when the amendment activates. The staleness failures added to three of the existing confidential transactions (Sections 5.7 through 5.9) cannot trigger on pre-amendment state, because rotation is impossible before activation and every mirror is therefore current. `ConfidentialMPTClawback` gains no staleness failure at all (Section 4.6.2).

Two changes are visible to existing clients:

- `MPTokenIssuanceSet` carrying `AuditorEncryptionKey` without `IssuerEncryptionKey` previously failed in preflight with `temMALFORMED`. It is now resolved in preclaim (Section 5.3.2.2), so the same submission may succeed, or consume a fee and return `tecNO_PERMISSION`.
- `MPTokenIssuanceSet` is delegable, so grants made before this amendment would otherwise gain key rotation authority on activation. Section 5.14.1 forbids key fields in a delegated submission, leaving the scope of existing grants unchanged.

Owner reserves, existing transaction fees, and RPC methods are unchanged.

## 8. Freeze Interactions with Key Rotation

This amendment does not change the lock behavior defined by XLS-0096. A holder-level or issuance-level lock does not prevent key rotation through `MPTokenIssuanceSet` or any transaction introduced by this amendment, because these operations only rotate keys, migrate mirrors, manage recovery authorization, or re-encrypt balances without moving value. They do not clear or otherwise modify the lock, so the holder remains unable to spend while the lock is set. Specifically, holders are allowed to rotate their keys while locked, as a locked account remains vulnerable to key compromise.

## 9. Issuer Key Loss

### 9.1. Problem

The issuer has irrecoverably lost sk_I. They can no longer decrypt any holder's issuer mirror, execute clawbacks, or perform active mirror re-encryption. The XRPL signing key is unaffected.

### 9.2. Impact

- Clawback authority is lost for all holders. The clawback ZKP is verified against the key each holder's mirror is encrypted under, and every mirror is encrypted under the lost pk_I, so the issuer cannot produce a proof for any of them. Registering a new pk_I' does not help, because it does not change what the existing mirrors are encrypted under, and without sk_I the issuer cannot perform `ConfidentialMPTMirrorUpdate` to migrate them either. Authority returns only as holders self-migrate their mirrors under pk_I'.
- Active re-encryption of issuer mirrors is impossible because the issuer cannot decrypt old issuer mirrors without sk_I. Auditor mirror re-encryption is also blocked until each holder self-migrates the issuer mirror under pk_I'; after that migration, the issuer can decrypt the reconstructed issuer mirror with sk_I' and use it to re-encrypt that holder's auditor mirror.
- Auditor key rotation is blocked - the issuer re-encrypts auditor mirrors via the issuer mirror, which they can no longer decrypt.

### 9.3. Recommended Approach: Loss Prevention

The primary recommendation is loss prevention through institutional key management:

- HSMs for key storage
- Shamir secret sharing of sk_I across custody providers
- Backup and recovery playbooks
- Same rigor applied to XRPL signing keys

### 9.4. Recovery Path: Holder-Driven Mirror Reconstruction

Issuer key loss creates an asymmetric situation analogous to holder key loss - the party who cannot act cryptographically requires the other party to complete the migration. The key difference from normal rotation is:

**Normal rotation (issuer driven)**:

- Issuer has sk_I and can decrypt all holder mirrors
- Issuer submits `ConfidentialMPTMirrorUpdate` (with Holder field) for each holder
- Holders are passive - no action required from them

**Issuer key loss (holder driven)**:

- Issuer has lost sk_I and cannot decrypt holder issuer mirrors
- Each holder must submit `ConfidentialMPTMirrorUpdate` (without Holder field) themselves
- Issuer is passive for issuer mirrors - only the holder can act
- Holders know b from decrypting `ConfidentialBalanceSpending` via sk_H and re-encrypt it under the new pk_I' using the cross-key equality proof (Section 5.4.6)

This is a one-step process per holder - unlike holder key loss recovery which requires two steps (holder authorizes, issuer completes). Here the holder acts alone with no issuer involvement needed for their mirror.

**How it works**:

1. Issuer registers new pk_I' via `MPTokenIssuanceSet` (they still have their XRPL signing key).
2. `IssuerKeyEpoch` increments.
3. Holder confidential transactions that require an issuer mirror fail if `IssuerKeyMirrorEpoch` does not equal `IssuerKeyEpoch`.
4. Each holder runs `ConfidentialMPTMergeInbox` first, then submits `ConfidentialMPTMirrorUpdate` without a Holder field with the cross-key equality proof to self-migrate their issuer mirror. Merge is required because the cross-key equality proof anchors to `ConfidentialBalanceSpending` which encodes only b_s - if `ConfidentialBalanceInbox` is non-zero, the new issuer mirror would encode b_s instead of the full b = b_s + b_in, producing a mirror that doesn't match the holder's actual total balance and breaking clawback correctness. Holders may also self-migrate their auditor mirror in the same transaction if needed.
5. Issuer regains clawback authority over each holder as their mirror is reconstructed.

**Limitation**: Inactive holders. Holders who do not transact will not self-migrate their issuer mirrors. The issuer cannot force-migrate issuer mirrors without sk_I, so clawback authority remains suspended until they act. Their auditor mirrors also cannot be actively migrated from the stale issuer mirror: `sk_I'` can decrypt only an issuer mirror that the holder has already reconstructed under `pk_I'`. Auditor visibility therefore remains blocked unless the holder self-migrates an appropriate mirror.

**Limitation**: Historical decryption. The issuer cannot decrypt historical ciphertexts from before the key loss.

### 9.5. Counterparty Dependency and Recovery Limitations

Holder key recovery is not unilateral. It requires an active issuer that retains `sk_I` and completes `ConfidentialMPTRecoverBalance`. If the issuer is inactive or unavailable, a holder's pending key recovery cannot complete even after `RecoveryKey` has been registered.

Issuer key-loss recovery is likewise not unilateral. It requires an active holder that retains `sk_H` and self-migrates the issuer mirror. If the issuer loses `sk_I` while a holder is inactive or unavailable, that holder's issuer mirror cannot be reconstructed and the issuer's clawback authority over that holder remains suspended. The protocol provides no on-chain fallback without participation from a party that can decrypt an equivalent mirror.

An inactive holder cannot self-migrate their issuer mirror. The issuer may wait for the holder to return or contact them through off-chain channels, but until the holder participates, confidential transactions and clawback remain unavailable for that holder. If the holder never participates, the suspension is permanent. This combined situation is expected to be rare under the issuer key-management practices recommended in Section 9.3, but it is an explicit limitation of the recovery model.

## 10. Operational Considerations

### 10.1. Migration Throughput

Each `ConfidentialMPTMirrorUpdate` carries a new mirror ciphertext (66 bytes) and a 128-byte compact Chaum-Pedersen equality proof. Fees are 10x base fee. Traversing the entire holders list is done off-chain.

### 10.2. Issuer Recovery Request Detection

After a holder submits `ConfidentialMPTHolderKeyUpdate` with `tfHolderKeyRecovery`, `RecoveryKey` is set on their `MPToken`. The issuer needs to detect this to submit `ConfidentialMPTRecoverBalance` promptly. Two complementary mechanisms are recommended:

**Option 1: Real-time WebSocket subscription**

The issuer subscribes to the XRPL WebSocket API and listens for `ConfidentialMPTHolderKeyUpdate` transactions with `tfHolderKeyRecovery` flag set. When one arrives, the issuer is notified in real-time and can immediately prepare and submit `ConfidentialMPTRecoverBalance`.

**Option 2: Periodic Clio query (catch-up mechanism)**

As a reliability backstop for missed WebSocket events (e.g. connection drops), the issuer periodically pages through Clio's `mpt_holders` method. Each result supplies an `mptoken_index`; the issuer then queries that ledger entry and filters the returned `MPToken` objects for `RecoveryKey`.

```json
{
  "command": "mpt_holders",
  "mpt_issuance_id": "000000012A9F1D3C...",
  "ledger_index": "validated"
}
```

For each returned `mptoken_index`, the issuer retrieves the corresponding `MPToken` ledger entry and checks whether `RecoveryKey` is present.

**Recommended approach**: Both mechanisms together. Option 1 provides real-time processing of recovery requests; Option 2 provides periodic catch-up for events missed during WebSocket downtime. The polling interval for Option 2 can be tuned based on the issuer's SLA for recovery completion.

**No API changes required**. Both mechanisms use existing XRPL and Clio infrastructure exactly as it is today. This is purely an operational implementation concern for issuers.

## 11. Cryptographic Proof Summary

The table below lists the zero-knowledge proof carried by each transaction.

| Transaction                      | Mode                                  | Proof Type                                                                                                                                | Size      |
| :------------------------------- | :------------------------------------ | :---------------------------------------------------------------------------------------------------------------------------------------- | :-------- |
| `MPTokenIssuanceSet` (rotation)  |                                       | None                                                                                                                                      | 0 bytes   |
| `ConfidentialMPTMirrorUpdate`    | Issuer, issuer mirror                 | Chaum-Pedersen cross-key plaintext equality, anchored on the issuer mirror                                                                | 128 bytes |
| `ConfidentialMPTMirrorUpdate`    | Issuer, auditor mirror                | Chaum-Pedersen cross-key plaintext equality, anchored on the issuer mirror                                                                | 128 bytes |
| `ConfidentialMPTMirrorUpdate`    | Issuer, both mirrors                  | AND-composed Chaum-Pedersen plaintext equality with shared randomness, anchored on the issuer mirror                                      | 128 bytes |
| `ConfidentialMPTMirrorUpdate`    | Holder self-migration, issuer mirror  | Chaum-Pedersen cross-key plaintext equality, anchored on the spending balance                                                             | 128 bytes |
| `ConfidentialMPTMirrorUpdate`    | Holder self-migration, auditor mirror | Chaum-Pedersen cross-key plaintext equality, anchored on the spending balance                                                             | 128 bytes |
| `ConfidentialMPTMirrorUpdate`    | Holder self-migration, both mirrors   | AND-composed Chaum-Pedersen plaintext equality with shared randomness, anchored on the spending balance                                   | 128 bytes |
| `ConfidentialMPTHolderKeyUpdate` | Rotation                              | AND-composed Chaum-Pedersen plaintext equality over the spending balance and the inbox, with a Schnorr proof of possession of the new key | 224 bytes |
| `ConfidentialMPTHolderKeyUpdate` | Recovery                              | Schnorr proof of possession                                                                                                               | 64 bytes  |
| `ConfidentialMPTRecoverBalance`  |                                       | Chaum-Pedersen cross-key plaintext equality, anchored on the issuer mirror                                                                | 128 bytes |

## 12. Security Considerations

### 12.1. Key Compromise vs. Key Loss

**Key compromise** - attacker has the key, legitimate holder still does. Attacker retains read access until re-encryption is complete. Rotation is the remediation.

**Key loss** - legitimate holder no longer has the key. Recovery paths require counterparty involvement. Loss prevention is the primary recommendation.

### 12.2. No New Cryptographic Assumptions

The proofs introduced here are new relations over the primitives XLS-0096 already uses, compact Chaum-Pedersen equality proofs and Schnorr proofs of knowledge, and rest on the same discrete logarithm assumption over secp256k1, so no new cryptographic assumption is introduced. Each relation carries its own domain separation, so a proof for one is never accepted for another. No range proofs are required, because no key rotation or recovery transaction changes a balance, each only re-encrypts an existing value under a different key.

### 12.3. Issuer Visibility During Re-encryption

The decrypt-then-re-encrypt approach requires the issuer to learn b. This is inherent and consistent with the issuer's existing visibility via the mirror ciphertext in XLS-0096. No new privacy exposure introduced.

### 12.4. No Schnorr PoK for Issuer and Auditor Key Rotation

Neither rotation carries a proof of possession, matching XLS-0096 when these keys are first registered. An issuer key whose secret nobody holds costs the issuer its own ability to read mirrors, claw back, and migrate holders later, and leaves holders unaffected once migrated. A proof of possession would not protect the auditor from the same mistake on the auditor key, since the submitter is the issuer, so it would establish only that the issuer holds the secret.

### 12.5. `ConfidentialBalanceVersion` Increments

A transaction increments a holder's `ConfidentialBalanceVersion` when it changes that holder's existing `ConfidentialBalanceSpending`, and leaves it alone otherwise. Of the transactions this amendment introduces, `ConfidentialMPTHolderKeyUpdate` in rotation mode and `ConfidentialMPTRecoverBalance` increment it, because both rewrite the spending balance; `ConfidentialMPTMirrorUpdate` and the recovery and cancel modes of `ConfidentialMPTHolderKeyUpdate` do not, because they rewrite mirrors or recovery state and leave the holder's own balances untouched.

The counter exists to stop proof replay. Without it, a holder could bring their spending balance back to a ciphertext it held earlier, and an old proof would verify a second time. Rotation invalidates any in-flight `ConfidentialMPTSend` proof; Section 6.9 covers why that is left to fail.

### 12.6. Two-Step Recovery Authorization

The holder's authorization (`tfHolderKeyRecovery`) is signed by the holder's XRPL signing key. `ConfidentialMPTRecoverBalance` is rejected unless `RecoveryKey` is present. The issuer cannot act unilaterally.

A successful rotation clears `RecoveryKey`, because rotation proves what the recovery request denies: the prover decrypted the holder's own balances with sk_H, so the key was not lost. This also gives a holder whose XRPL signing key is compromised a remedy the attacker cannot match, since cancelling a recovery needs only that signing key while rotating needs sk_H as well.

### 12.7. `RecoveryKey` Liveness Concern

If the issuer never completes recovery, the holder remains locked out indefinitely. The protocol defines no automatic expiry for `RecoveryKey` - forcing expiry would penalize a holder already in a degraded state without any ledger health benefit. Per XLS-0096, clawback burns tokens rather than returning them - this is not a viable workaround.

### 12.8. Issuer Key Loss and Clawback Authority

The clawback ZKP is verified against the key the holder's issuer mirror is encrypted under, resolved from ledger state and not selectable by the caller. Rotation therefore does not by itself suspend clawback: an unmigrated holder can still be clawed back, provided the issuer retained the secret key for that holder's epoch (Section 12.9). What suspends clawback is losing a secret key, which suspends it for every holder whose mirror is encrypted under that key. Loss of sk_I is the extreme case and reaches all holders at once, since without sk_I the issuer can neither prove against the existing mirrors nor migrate them; authority is restored progressively as holders self-migrate under pk_I'. Discarding a superseded key has the same effect, bounded to the holders left at that epoch.

### 12.9. Successive Rotations and Historical Issuer-Key Retention

The protocol does not enforce a global gate preventing successive rotations before migration is complete. Per-transaction mirror checks enforce correctness at the point of use for each individual holder, regardless of how many epochs behind they are. The recommended practice is to update every holder after each rotation, which confines the retention question below to a single key.

Historical issuer secret-key retention is optional and depends on the issuer's migration strategy. If the issuer intends to actively migrate, or to retain clawback authority over, any holder whose `IssuerEncryptedBalance` remains encrypted under an older issuer key, the issuer MUST retain the corresponding historical secret key until those holder mirrors have been migrated. Both operations decrypt the mirror as it sits on the ledger, so both are gated on the key of the holder's epoch rather than the currently registered one.

Once an issuance-wide holder traversal confirms that no issuer mirror remains at the corresponding epoch, the historical secret key is no longer required and may be destroyed. An issuer may instead destroy the old secret key earlier and rely on the remaining holders to self-migrate using `sk_H`. Doing so does not affect ledger correctness, but permanently removes the issuer-driven migration path for those holders and, until they self-migrate, the issuer's clawback authority over them.

Historical auditor secret keys are not required for mirror migration because auditor mirrors are reconstructed from a current issuer mirror or through holder self-migration.

### 12.10. Holder Self-Migration Security

Holder self-migration anchors the equality proof to the holder's own `ConfidentialBalanceSpending`, decrypted with `sk_H`. Knowledge of `sk_H` both establishes possession of the holder key and supplies the balance being re-encrypted, so only a holder who can decrypt their spending balance can migrate their own mirrors. Condition 11 of Section 5.4.3.2 requires `ConfidentialBalanceInbox` to be the canonical encrypted zero, so the spending balance equals the holder's total balance, which is the quantity a mirror encodes; the new mirror therefore carries that full balance under the newly registered key, matching what the replaced mirror encoded under the XLS-0096 invariant that an issuer mirror encodes spending plus inbox.

### 12.11. Seed-Derived ElGamal Keys

Wallets may derive ElGamal keys from the XRPL account seed. This eliminates key loss for standard single-signature accounts but does not solve key compromise. Multi-sig accounts cannot use seed derivation. See Appendix A.

# Appendix

## Appendix A: Seed-Derived ElGamal Keys

A wallet-level convention can eliminate ElGamal key loss as a concern by deriving keys deterministically from the XRPL account seed:

For holders:

```
sk_H = HashToScalar(SHA-512Half("CMPT_ELGAMAL_HOLDER" || seed))
pk_H = sk_H · G
```

For issuers:

```
sk_I = HashToScalar(SHA-512Half("CMPT_ELGAMAL_ISSUER" || seed))
pk_I = sk_I · G
```

This requires zero protocol changes. The protocol registers the public key on-chain and does not know or care how it was derived.

**What this solves**: Key loss becomes impossible as long as the seed exists. Simplifies custody - backing up the seed covers both signing and ElGamal keys.

**Limitations**:

- Seed compromise also compromises confidential balance privacy - expansion of impact from the same attack, not a new attack vector.
- Seed compromise cannot be remediated without an account move.
- Seed rotation forces ElGamal key rotation.
- Multi-sig / SignerList accounts cannot use seed derivation.
- Convention, not enforcement.

**Recommendation**: Default wallet convention for standard single-signature accounts. Protocol-level recovery mechanisms remain available as fallbacks.

## Appendix B: FAQ

### B.1: Why can't I use my XRPL signing key to recover my ElGamal key?

The keys are cryptographically independent - no derivation path exists from one to the other. See Appendix A for a wallet convention that eliminates this problem for standard single-signature accounts.

### B.2: What happens if I lose my ElGamal key?

You cannot decrypt or spend your confidential balances, but your XRPL signing key is unaffected. Submit `ConfidentialMPTHolderKeyUpdate` with `tfHolderKeyRecovery` to register a new key, then wait for the issuer to complete recovery. This directly addresses XLS-0096 FAQ A.6.

### B.3: Can I rotate my key while I have pending confidential sends?

Yes, but one of the two will be rejected and has to be rebuilt and resubmitted. Nothing is lost when that happens, see Section 6.9.

### B.4: What happens to my inbox balance during key loss recovery?

It is reset to canonical encrypted zero. Any value in the inbox is consolidated into the spending balance via the issuer mirror. No value is lost.

### B.5: Can the issuer rotate my key without my consent?

No. `ConfidentialMPTRecoverBalance` is rejected if `RecoveryKey` is not set on your `MPToken`. The issuer cannot act without your prior on-chain authorization.

### B.6: How long does bulk mirror re-encryption take at scale?

Each `ConfidentialMPTMirrorUpdate` carries a new mirror ciphertext and compact Chaum-Pedersen equality proof. Fees are 10x base fee. Traversing the entire holders list is done off-chain.

### B.7: Can the issuer rotate keys multiple times in quick succession?

Yes - the protocol does not enforce a global gate blocking successive rotations. Holders with stale mirrors are blocked from transacting at the per-transaction level regardless of how many epochs behind they are. `ConfidentialMPTMirrorUpdate` bridges directly from any old epoch to the current epoch in one step. The recommended practice is still to update every holder after each rotation, so that no historical key has to be kept.

### B.8: How can I verify that all mirrors have been migrated?

Compare `IssuerKeyEpoch` on `MPTokenIssuance` against `IssuerKeyMirrorEpoch` on each `MPToken`. Whether a mirror is stale is trivially known on-ledger in O(1).

### B.9: Does ledger replay break after key rotation?

No. Each XRPL ledger version is a complete, immutable snapshot preserving the `IssuerEncryptionKey` that was active at that moment. Replaying a historical transaction uses the `MPTokenIssuance` state from that exact ledger version. This is identical to how signing key rotation works on XRPL.
