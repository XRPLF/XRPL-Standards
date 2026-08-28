<pre>
  xls: ??
  title: ElGamal Key Rotation for Confidential MPTs
  description: Defines ElGamal key rotation for issuer, auditor, and holder roles in the Confidential MPT protocol, with key loss recovery mechanisms.
  author: Aanchal Malhotra <amalhotra@ripple.com>, Yinyi Qian <yqian@ripple.com>
  category: Amendment
  status: Draft
  requires: XLS-0096, XLS-0033
  proposal-from: https://github.com/XRPLF/XRPL-Standards/discussions/599
  created: 2026-04-01
  updated: 2026-07-22
</pre>

# ElGamal Key Rotation for Confidential MPTs

## 1. Abstract

This amendment extends XLS-0096 (Confidential Transfers for Multi-Purpose Tokens) with ElGamal key rotation for all three participant roles: issuer, auditor, and holder. It introduces 3 new transaction types (`ConfidentialMPTMirrorUpdate`, `ConfidentialMPTHolderKeyUpdate`, `ConfidentialMPTRecoverBalance`), extends `MPTokenIssuanceSet` to permit replacement of already-registered encryption keys, adds mirror staleness validation to four existing XLS-0096 transaction types (`ConfidentialMPTSend`, `ConfidentialMPTConvert`, `ConfidentialMPTConvertBack`, `ConfidentialMPTClawback`) together with mirror resets and epoch rewrites on clawback, and adds new fields to the `MPTokenIssuance` and `MPToken` ledger objects. Key rotation is supported for both voluntary and loss-recovery scenarios. All new cryptographic constructions reuse existing primitives from XLS-0096 (compact Chaum-Pedersen equality proofs, Schnorr proofs of knowledge) and introduce no new cryptographic assumptions.

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
- **Context Hash**: The 256-bit value defined in XLS-0096 that binds a zero-knowledge proof to a specific transaction and ledger state, providing domain separation and replay protection. For proofs over a holder's own balances it incorporates the holder's `ConfidentialBalanceVersion`, so any change to the spending balance invalidates outstanding proofs.

## 4. Overview

### 4.1. Modified Transaction Types

- `MPTokenIssuanceSet`: Extended to allow replacement of `IssuerEncryptionKey` and `AuditorEncryptionKey` when already present, enabling issuer and auditor key rotation. See Section 5.3.
- `ConfidentialMPTConvert`: Rejected when an already-initialized holder's issuer or auditor mirror is stale; sets mirror epochs when a holder initializes confidential state. See Section 5.7.
- `ConfidentialMPTSend`: Rejected when the sender's or the destination's issuer or auditor mirror is stale. See Section 5.8.
- `ConfidentialMPTConvertBack`: Rejected when the holder's issuer or auditor mirror is stale. See Section 5.9.
- `ConfidentialMPTClawback`: Rejected when the holder's issuer mirror is stale; resets both mirror ciphertexts and rewrites both mirror epochs on success. See Section 5.10.

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

- `MPTokenIssuance`: Two new fields - `IssuerKeyEpoch`, `AuditorKeyEpoch`.
- `MPToken`: Three new fields - `IssuerKeyMirrorEpoch`, `AuditorKeyMirrorEpoch`, `RecoveryKey`.

### 4.4. Key Rotation Model

**Issuer key rotation** proceeds in two phases. First, the issuer submits `MPTokenIssuanceSet` with a new `IssuerEncryptionKey`, incrementing `IssuerKeyEpoch`. After this transaction is accepted, all new issuer mirror delta ciphertexts must be encrypted under the new key. Second, the issuer submits `ConfidentialMPTMirrorUpdate` once per holder to re-encrypt each holder's issuer mirror under the new key.

Until a holder's mirror is migrated, confidential transactions for that holder are rejected. The underlying reason is cryptographic: in `ConfidentialMPTSend` and other transactions, the holder correctly reads the current `IssuerEncryptionKey` (`pk_I'`) from the issuance and constructs `IssuerEncryptedAmount` under it. However, the on-ledger accumulated `IssuerEncryptedBalance` is still under the old key (`pk_I`). Adding a delta under `pk_I'` to an accumulated balance under `pk_I` is cryptographically invalid - ciphertexts under different keys cannot be combined homomorphically.

Comparing the holder's mirror epoch with the corresponding issuance key epoch makes this detectable cleanly:

- Validators use it to reject the transaction explicitly and early, before attempting an invalid homomorphic addition
- Wallet software applies the same comparison proactively, allowing it to warn the holder and block a transaction that would fail before submission

**Auditor key rotation** follows the identical pattern using `AuditorEncryptionKey` and `AuditorKeyEpoch`.

**Auditor key late-registration by issuer** allows the issuer to register auditor key after the issuer key was already registered.

- Pre-`ConfidentialMPTKeyRotation` amendment: when registering the key for the auditor first time, it has to be registered together with the issuer key in `MPTokenIssuanceSet`. The issuer is not allowed to register issuer key in one transaction and later register auditor key in another transaction.
- Now with `ConfidentialMPTKeyRotation` amendment: with the issuer key already registered, the issuer can register the auditor key in a separate `MPTokenIssuanceSet` whenever they want to enable auditor.

**Holder self-migration** is available after an issuer key rotation, an auditor key rotation, simultaneous issuer and auditor key rotation, or late auditor registration. Rather than waiting for the issuer to submit `ConfidentialMPTMirrorUpdate`, any holder may self-migrate their issuer or auditor mirror by submitting `ConfidentialMPTMirrorUpdate` without a `Holder` field, using a cross-key equality proof anchored to their `ConfidentialBalanceSpending`. Prerequisites: `ConfidentialMPTMergeInbox` must be run first (inbox must be canonical zero), and the holder must have `sk_H`. See Section 5.4.7 for what the proof establishes.

**Simultaneous issuer and auditor key rotation**: The issuer may rotate both `IssuerEncryptionKey` and `AuditorEncryptionKey` in a single `MPTokenIssuanceSet` transaction, though this is rare in practice. In this case, per-holder migration may be performed in a single `ConfidentialMPTMirrorUpdate` transaction with both `IssuerEncryptedAmount` and `AuditorEncryptedAmount` present. A single compact AND-composed Chaum-Pedersen equality proof covers both statements under one Fiat-Shamir challenge.

**Multiple successive rotations**: The issuer may rotate multiple times before completing migration. Holders with stale mirrors are blocked from transacting at the per-transaction level regardless of how many epochs behind they are. `ConfidentialMPTMirrorUpdate` bridges directly from the holder's current epoch to the latest epoch in one step. In issuer mode, this requires the issuer to retain the historical secret key corresponding to the epoch the holder is currently at - if that key has been destroyed, the holder must self-migrate by submitting `ConfidentialMPTMirrorUpdate` without a `Holder` field instead.

**Holder key rotation** is self-contained via `ConfidentialMPTHolderKeyUpdate` with `tfHolderKeyRotation`. No issuer involvement required.

**Holder key loss recovery** is a two-step process: the holder registers the new key on-chain via `ConfidentialMPTHolderKeyUpdate` with `tfHolderKeyRecovery`, then the issuer completes recovery via `ConfidentialMPTRecoverBalance`.

**Issuer key loss** is handled via holder-driven mirror reconstruction for both issuer and auditor mirrors. In the issuer key loss scenario, holder self-migration is the only path for issuer mirrors since the issuer cannot decrypt old mirrors without `sk_I`. For auditor mirrors, the issuer can still perform active re-encryption via the issuer mirror (`sk_I`) even when `sk_A` is lost - holder self-migration is an alternative but not the only path. See Section 7.

### 4.5. Re-encryption Strategy

Active re-encryption is the recommended strategy. The issuer submits `ConfidentialMPTMirrorUpdate` for all holders after rotating the key. The issuer is recommended to lock each holder's `MPToken` before submitting `ConfidentialMPTMirrorUpdate` and unlock after success. Note: this is a recommendation, not a requirement. The epoch staleness check already prevents the holder from successfully transacting with a stale mirror - the lock only prevents the holder from wasting fees on transactions that will be rejected. However, lock + `ConfidentialMPTMirrorUpdate` + unlock = 3 transactions per holder, tripling migration transaction volume at large holder counts. Issuers should weigh this cost against the UX benefit.

Prioritization for bulk migration:

1. Largest balances first - greatest value at risk if old key is compromised, and clawback is blocked until migrated.
2. Most active holders next - unblocks their confidential transactions soonest.
3. Regulatory-sensitive accounts - under specific compliance obligations.
4. Remaining inactive accounts - clawback remains blocked for these holders until migrated.

The issuer may rotate keys multiple times. Holders with stale mirrors are blocked from transacting at the per-transaction level regardless of how many epochs behind they are. See Section 4.6.2.

**Clawback and migration urgency**: Clawback is blocked for any unmigrated holder after key rotation - the issuer must complete `ConfidentialMPTMirrorUpdate` before executing `ConfidentialMPTClawback` for that holder.

**Historical key retention**: After multiple successive rotations, migrating a holder still at an old epoch requires the historical secret key for that epoch to decrypt their on-ledger mirror. If the issuer has destroyed a historical key before all holders at that epoch were migrated, those holders must fall back to self-migration (Section 5.4.7). Issuers should retain historical secret keys until all holders at each epoch are fully migrated.

### 4.6. Epoch Tracking and Migration Status

#### 4.6.1. Determining Mirror Status

For an `MPToken` with initialized confidential state:

- The issuer mirror is current when `IssuerEncryptedBalance` is present and
  `IssuerKeyMirrorEpoch` equals `IssuerKeyEpoch`.
- When an auditor key is configured, the auditor mirror is current when
  `AuditorEncryptedBalance` is present and `AuditorKeyMirrorEpoch` equals
  `AuditorKeyEpoch`. When no auditor key is configured, no auditor mirror is required.
- Migration is required whenever a required mirror is not current.

An absent epoch field is treated as epoch 0. Validators determine whether a
mirror is current by requiring equality between its mirror epoch and the
corresponding key epoch. Ledger invariants separately ensure that a mirror
epoch cannot exceed its corresponding key epoch.

#### 4.6.2. Transactions Requiring Current Mirrors

The transactions below are rejected with `tecNO_PERMISSION` when a mirror they
require is not current. An auditor mirror is required only when an auditor key
is configured. The normative failure conditions and state changes for each
transaction are specified in its own section.

| Transaction                  | Required current mirrors                              | Specified in |
| :--------------------------- | :---------------------------------------------------- | :----------- |
| `ConfidentialMPTConvert`     | Issuer and auditor, for an already-initialized holder | Section 5.7  |
| `ConfidentialMPTSend`        | Issuer and auditor, for both sender and destination   | Section 5.8  |
| `ConfidentialMPTConvertBack` | Issuer and auditor, for the holder                    | Section 5.9  |
| `ConfidentialMPTClawback`    | Issuer only, for the holder                           | Section 5.10 |

#### 4.6.3. Migration-Required Conditions

The required migration is determined as follows:

1. If the issuer mirror is not current, it must be migrated.
2. If an auditor key is configured but `AuditorEncryptedBalance` is absent, the
   auditor mirror must be initialized. This is the late-registration case.
   Initial auditor-key registration remains at epoch 0, so field presence must
   be checked separately from epoch equality.
3. If `AuditorEncryptedBalance` is present but the auditor mirror is not
   current, it must be migrated.
4. If both mirrors require migration, they may be updated in one
   `ConfidentialMPTMirrorUpdate`.

A missing `IssuerEncryptedBalance` on an initialized confidential `MPToken` is
an invalid ledger state, not a migration state.

#### 4.6.4. New Holder Initialization

A holder who executes `ConfidentialMPTConvert` after key registration or
rotation has their `MPToken` initialized with mirror ciphertexts under the
current keys. Its mirror epoch fields are set to the corresponding current key
epochs, with epoch 0 fields omitted from ledger storage. The holder therefore
does not require migration.

#### 4.6.5. Issuance-Wide Migration Completion

Mirror status for a single holder can be determined on-ledger in O(1) from
mirror presence and epoch equality. Determining whether migration is complete
for an entire issuance requires traversing the holders off-chain through `mpt_holders` API.

### 4.7. State Transition Summary

This section is an informative summary using the states defined in Section 3.
The referenced transaction sections remain normative. In the tables below,
**Before** and **After** describe the abstract state before and after the
transition; **Trigger** identifies the transaction or ledger event;
**Preconditions** summarizes the required state and proof; **State Changes**
lists the affected ledger fields; and **Reference** points to the normative
rules.

#### 4.7.1. Mirror Lifecycle

| Before                                                        | Trigger                                                                          | Preconditions                                              | State Changes                                                                                               | After                                                           | Reference                  |
| :------------------------------------------------------------ | :------------------------------------------------------------------------------- | :--------------------------------------------------------- | :---------------------------------------------------------------------------------------------------------- | :-------------------------------------------------------------- | :------------------------- |
| No auditor mirror required                                    | Initial auditor key registration                                                 | Issuer key is already registered                           | `AuditorEncryptionKey` is registered; existing holder objects are unchanged                                 | Missing auditor mirror for each initialized confidential holder | Sections 4.4 and 5.3       |
| No initialized confidential state                             | First `ConfidentialMPTConvert`                                                   | Current issuer key and any configured auditor key are used | Mirror ciphertexts are created and mirror epochs are set to the current key epochs                          | Current mirror or mirrors                                       | Section 4.6.4 and XLS-0096 |
| Current mirror                                                | Corresponding issuer or auditor key rotation                                     | A different valid key is submitted                         | The key is replaced and its key epoch increments; holder mirrors are unchanged                              | Stale mirror                                                    | Section 5.3                |
| Stale mirror                                                  | Another rotation of the corresponding key                                        | Successive rotation is permitted                           | The key epoch increments again; the holder mirror remains unchanged                                         | Stale mirror, possibly multiple epochs behind                   | Sections 4.4 and 9.9       |
| Stale issuer mirror                                           | `ConfidentialMPTMirrorUpdate` updates the issuer mirror                          | Required issuer-mode or holder-mode proof succeeds         | `IssuerEncryptedBalance` is replaced and `IssuerKeyMirrorEpoch` is set to `IssuerKeyEpoch`                  | Current issuer mirror                                           | Section 5.4                |
| Missing or stale auditor mirror                               | `ConfidentialMPTMirrorUpdate` updates the auditor mirror                         | Auditor key is configured and the required proof succeeds  | `AuditorEncryptedBalance` is created or replaced and `AuditorKeyMirrorEpoch` is set to `AuditorKeyEpoch`    | Current auditor mirror                                          | Section 5.4                |
| Current mirrors                                               | `ConfidentialMPTConvert`, `ConfidentialMPTSend`, or `ConfidentialMPTConvertBack` | Every required mirror is current                           | Mirror ciphertexts change under the current keys; mirror epochs do not change                               | Current mirrors                                                 | Sections 5.7 through 5.9   |
| Current issuer mirror and any configured auditor-mirror state | `ConfidentialMPTClawback`                                                        | Clawback proof succeeds against the current issuer mirror  | Mirror ciphertexts are reset to canonical encrypted zero and their epochs are set to the current key epochs | Current mirrors encrypting zero                                 | Section 5.10               |

#### 4.7.2. Holder Key and Recovery Lifecycle

| Before              | Trigger                                           | Preconditions                                                 | State Changes                                                                                                                                                     | After               | Reference                |
| :------------------ | :------------------------------------------------ | :------------------------------------------------------------ | :---------------------------------------------------------------------------------------------------------------------------------------------------------------- | :------------------ | :----------------------- |
| No Recovery Pending | `ConfidentialMPTHolderKeyUpdate` in rotation mode | Required mirrors are current and the rotation proof succeeds  | `HolderEncryptionKey`, holder balance ciphertexts, and `ConfidentialBalanceVersion` are updated                                                                   | No Recovery Pending | Sections 5.5.5 and 5.5.6 |
| No Recovery Pending | `ConfidentialMPTHolderKeyUpdate` in recovery mode | New-key Schnorr proof succeeds                                | `RecoveryKey` is created; the existing holder key and balances are unchanged                                                                                      | Recovery Pending    | Sections 5.5.5 and 5.5.6 |
| Recovery Pending    | `ConfidentialMPTHolderKeyUpdate` in cancel mode   | Holder authorizes the transaction with their XRPL signing key | `RecoveryKey` is removed; the existing holder key and balances are unchanged                                                                                      | No Recovery Pending | Sections 5.5.5 and 5.5.6 |
| Recovery Pending    | `ConfidentialMPTRecoverBalance`                   | Issuer mirror is current and the recovery proof succeeds      | `HolderEncryptionKey` is replaced by `RecoveryKey`, the recovered balance is placed in spending, inbox is reset, version increments, and `RecoveryKey` is removed | No Recovery Pending | Section 5.6              |
| Recovery Pending    | `ConfidentialMPTHolderKeyUpdate` in rotation mode | Required mirrors are current and the rotation proof succeeds  | The holder key, holder balance ciphertexts, and version are updated; `RecoveryKey` remains unchanged                                                              | Recovery Pending    | Sections 5.5.5 and 5.5.6 |

## 5. Specification

### 5.1. Ledger Entry: `MPTokenIssuance`

The existing `MPTokenIssuance` ledger object is extended with two new fields. All other fields, flags, ownership, reserves, deletion conditions, and the object identifier are unchanged from XLS-0033.

#### 5.1.1. Fields

| Field Name        | Constant | Required | Internal Type | Default Value | Description                                                                                                                                                           |
| :---------------- | :------- | :------- | :------------ | :------------ | :-------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `IssuerKeyEpoch`  | No       | No       | `UINT32`      | `0`           | Monotonically increasing counter incremented on each issuer ElGamal key rotation. Not stored when at its default value; validators treat an absent field as epoch 0.  |
| `AuditorKeyEpoch` | No       | No       | `UINT32`      | `0`           | Monotonically increasing counter incremented on each auditor ElGamal key rotation. Not stored when at its default value; validators treat an absent field as epoch 0. |

**Note**: To accommodate existing `MPTokenIssuance` ledger objects that lack epoch fields even when keys are registered, the epoch value should remain absent after initial registration. It is set to 1 only when rotating a key for the first time successfully, and then increments with each subsequent rotation.

#### 5.1.2. Freeze/Lock

**Lock Support:** Yes

Setting `lsfMPTLocked` on `MPTokenIssuance` locks the entire issuance. This
amendment adds no new lock flag and does not change how the existing one is set,
cleared, or enforced, so lock support is unchanged from XLS-0033 and XLS-0096.
See Section 6 for how a lock interacts with key rotation, mirror migration, and
holder key loss recovery.

#### 5.1.3. Invariants

- I1: `IssuerKeyEpoch`, if present, must be ≥ 1.
- I2: `AuditorKeyEpoch`, if present, must be ≥ 1.
- I3: `IssuerEncryptionKey` must be present if `IssuerKeyEpoch` is present.
- I4: `AuditorEncryptionKey` must be present if `AuditorKeyEpoch` is present.

#### 5.1.4. Example JSON

After issuer and auditor key rotation:

```json
{
  "LedgerEntryType": "MPTokenIssuance",
  "Flags": 128,
  "Issuer": "rIssuerAccountAddress",
  "MPTokenIssuanceID": "000000012A9F1D3C...",
  "MaximumAmount": "1000000000",
  "OutstandingAmount": "500000000",
  "ConfidentialOutstandingAmount": "250000000",
  "IssuerEncryptionKey": "02a1b2c3d4e5f6...",
  "AuditorEncryptionKey": "02b1c2d3e4f5a6...",
  "IssuerKeyEpoch": 1,
  "AuditorKeyEpoch": 1,
  "PreviousTxnID": "A1B2C3D4...",
  "PreviousTxnLgrSeq": 1234567
}
```

### 5.2. Ledger Entry: `MPToken`

The existing `MPToken` ledger object is extended with three new fields. All other fields, flags, ownership, reserves, and the object identifier are unchanged from XLS-0033.

#### 5.2.1. Fields

| Field Name              | Constant | Required | Internal Type | Default Value | Description                                                                                                                                                                                                                                                                                                                                                                                 |
| :---------------------- | :------- | :------- | :------------ | :------------ | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `IssuerKeyMirrorEpoch`  | No       | No       | `UINT32`      | `0`           | The `IssuerKeyEpoch` at which this holder's issuer mirror was last re-encrypted. The mirror is stale when this value is less than the current `IssuerKeyEpoch`. Not stored when at its default value.                                                                                                                                                                                       |
| `AuditorKeyMirrorEpoch` | No       | No       | `UINT32`      | `0`           | The `AuditorKeyEpoch` at which this holder's auditor mirror was last re-encrypted. The mirror is stale when this value is less than the current `AuditorKeyEpoch`. Not stored when at its default value.                                                                                                                                                                                    |
| `RecoveryKey`           | No       | No       | `BLOB`        | N/A           | A 33-byte compressed ElGamal public key authorized for key loss recovery. Set by `ConfidentialMPTHolderKeyUpdate` in recovery mode (`tfHolderKeyRecovery`). Cleared by exactly two paths: (1) `ConfidentialMPTRecoverBalance` when the issuer completes recovery; (2) `ConfidentialMPTHolderKeyUpdate` with `tfCancelRecovery` when the holder explicitly cancels. Has no automatic expiry. |

#### 5.2.2. Deletion

Deletion conditions are unchanged from XLS-0033. The `MPToken` deletion question raised by `RecoveryKey` is a non-issue: per XLS-0096 Section 5.2.4, an `MPToken` cannot be deleted once confidential fields have been initialized, even if all balances contain canonical encrypted zero. Since `RecoveryKey` only appears on initialized `MPToken` objects (Invariant I8), an `MPToken` with `RecoveryKey` set can never be deleted. No new deletion concern is introduced by this amendment.

#### 5.2.3. Freeze/Lock

**Lock Support:** Yes

Setting `lsfMPTLocked` on a holder's `MPToken` locks that holder individually,
independently of the issuance-level lock described in Section 5.1.2. This
amendment adds no new lock flag and does not change how the existing one is set,
cleared, or enforced, so lock support is unchanged from XLS-0033 and XLS-0096.
See Section 6 for how a lock interacts with key rotation, mirror migration, and
holder key loss recovery.

#### 5.2.4. Invariants

- I5: `IssuerKeyMirrorEpoch`, if present, must be ≤ `IssuerKeyEpoch` on the parent `MPTokenIssuance` (treated as 0 if absent).
- I6: `AuditorKeyMirrorEpoch`, if present, must be ≤ `AuditorKeyEpoch` on the parent `MPTokenIssuance` (treated as 0 if absent).
- I7: `RecoveryKey`, if present, must be a well-formed compressed secp256k1 point (33 bytes) and must differ from the current `HolderEncryptionKey`.
- I8: `RecoveryKey` must not be present on an `MPToken` that has no `HolderEncryptionKey` registered. A holder initializes confidential state via their first `ConfidentialMPTConvert` (with `HolderEncryptionKey` present, MPTAmount may be zero). `RecoveryKey` is only meaningful for holders who have completed this initialization.

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
  "AuditorEncryptedBalance": "02a1b2c3d4e5f6...",
  "AuditorKeyMirrorEpoch": 1,
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
  "RecoveryKey": "02g1h2i3j4k5l6...",
  "PreviousTxnID": "C3D4E5F6...",
  "PreviousTxnLgrSeq": 1234569
}
```

### 5.3. Transaction: `MPTokenIssuanceSet`

The existing `MPTokenIssuanceSet` transaction is extended to allow replacement of `IssuerEncryptionKey` and `AuditorEncryptionKey` when already present. Some existing guards in preclaim must be relaxed:

1.  Key presence guard: The current implementation rejects updates to `IssuerEncryptionKey` and `AuditorEncryptionKey` once already present on the issuance object (`tecNO_PERMISSION`). This guard is relaxed to allow replacement when the field is already present. Key rotation does not reintroduce the vulnerability this guard was introduced to prevent - when rotating, the field already exists and every holder's `MPToken` already has the corresponding ciphertext column.
2.  `sfConfidentialOutstandingAmount` > 0 guard: The current implementation unconditionally rejects any `IssuerEncryptionKey` or `AuditorEncryptionKey` update when `sfConfidentialOutstandingAmount` is already present (i.e. COA > 0). This guard must also be relaxed. Key rotation is only meaningful and necessary precisely when COA > 0 - if COA were zero, no holder would have a mirror yet and none of the migration logic would be needed. Maintaining this guard makes key rotation impossible in any real deployment.
3.  Pre-`ConfidentialMPTKeyRotation` amendment, an issuer cannot register an auditor key in `MPTokenIssuanceSet` unless the issuer key is being registered in the same transaction. This means
    the issuer can either register the issuer key alone or register both keys together initially. With the `ConfidentialMPTKeyRotation` amendment, the issuer can now register an auditor key at any time after the issuer key is already registered or rotated—allowing them to opt in whenever they want. The only constraint is that an auditor key cannot be registered before an issuer key.

The guard against adding `IssuerEncryptionKey` when `lsfMPTCanHoldConfidentialBalance` is not enabled remains unchanged - confidential transfers must be enabled before keys can be set or rotated.
All existing `MPTokenIssuanceSet` behavior (lock/unlock, `DomainID`) is completely unaffected.

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

1. `IssuerEncryptionKey` on `MPTokenIssuance` ← new key value
2. If `IssuerEncryptionKey` already existed, `IssuerKeyEpoch` on `MPTokenIssuance` ← `IssuerKeyEpoch` + 1 (field created with value 1 if previously absent); on initial registration, leave the epoch absent.

When `AuditorEncryptionKey` is present and valid:

1. `AuditorEncryptionKey` on `MPTokenIssuance` ← new key value
2. If `AuditorEncryptionKey` already existed, `AuditorKeyEpoch` on `MPTokenIssuance` ← `AuditorKeyEpoch` + 1 (field created with value 1 if previously absent); on initial registration, leave the epoch absent.

#### 5.3.4. Example JSON

```json
{
  "TransactionType": "MPTokenIssuanceSet",
  "Account": "rIssuerAccountAddress",
  "MPTokenIssuanceID": "000000012A9F1D3C...",
  "IssuerEncryptionKey": "02a1b2c3d4e5f6...",
  "Fee": "120",
  "Sequence": 42
}
```

### 5.4. Transaction: `ConfidentialMPTMirrorUpdate`

Re-encrypts a single holder's issuer and/or auditor mirror ciphertext under the new key after a key rotation. Submitted by the issuer once per holder. A holder may also self-migrate their issuer mirror, their auditor mirror, or both. Every migration re-encrypts one or both of a holder's mirror balances under a rotated key, and proves the new ciphertext still encrypts the same balance without revealing it.

#### 5.4.1. Use Cases

- Issuer Mode (Submitted by the issuer with the `sfHolder`):

1. **Issuer Key Rotation Migration**: Re-encrypts the holder's issuer mirror `IssuerEncryptedBalance` under the new `pk_I'`.
2. **Auditor Key Rotation Migration**: Re-encrypts the holder's auditor mirror `AuditorEncryptedBalance` under the new `pk_A'`.
3. **Simultaneous Rotation Migration**: Updates both the issuer and auditor encrypted balances in a single transaction.
4. **Auditor Late-Registration Migration**: Set the auditor mirror if the auditor key is registered post-issuance.

- Holder Self-Migration Mode (Submitted by the holder without the `sfHolder` field. The holder decrypts their own `sfConfidentialBalanceSpending` with their private key and re-encrypts it under the relevant new public key(s). Require `sfConfidentialBalanceInbox` to be canonically zero, which means the holder has run `ConfidentialMPTMergeInbox` first):

5. **Holder Issuer-Mirror Self-Migration**: Re-encrypts issuer mirror.
6. **Holder Auditor-Mirror Self-Migration**: Re-encrypts the auditor mirror, or sets it for the first time if late-registered.
7. **Simultaneous Holder Self-Migration**: Updates both the issuer and auditor encrypted balances in a single transaction (used when both keys have rotated).

#### 5.4.2. Fields

Whether it is issuer mode or holder mode is determined by `Holder` field's presence. If `Holder` is present, it is issuer mode. If `Holder` is absent, it is holder self-migration mode.

| Field Name                    | Required?   | JSON Type | Internal Type | Default Value                 | Description                                                                                                                                                                                                                                                  |
| :---------------------------- | :---------- | :-------- | :------------ | :---------------------------- | :----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `TransactionType`             | Yes         | `string`  | `UINT16`      | `ConfidentialMPTMirrorUpdate` | `ConfidentialMPTMirrorUpdate`.                                                                                                                                                                                                                               |
| `Account`                     | Yes         | `string`  | `ACCOUNTID`   | N/A                           | The issuer account in issuer mode, or the holder account in holder mode.                                                                                                                                                                                     |
| `MPTokenIssuanceID`           | Yes         | `string`  | `UINT192`     | N/A                           | The unique identifier of the MPT issuance.                                                                                                                                                                                                                   |
| `Holder`                      | Conditional | `string`  | `ACCOUNTID`   | N/A                           | **Required** in issuer mode and **must be absent** in holder mode. Identifies the holder whose mirror(s) are being re-encrypted.                                                                                                                             |
| `IssuerEncryptedAmount`       | Conditional | `string`  | `BLOB`        | N/A                           | A 66-byte ElGamal ciphertext encrypting the holder's balance under the new issuer key. Reuses `sfIssuerEncryptedAmount` from XLS-0096. Present to migrate holder's issuer mirror. At least one of this field and `AuditorEncryptedAmount` must be present.   |
| `AuditorEncryptedAmount`      | Conditional | `string`  | `BLOB`        | N/A                           | A 66-byte ElGamal ciphertext encrypting the holder's balance under the new auditor key. Reuses `sfAuditorEncryptedAmount` from XLS-0096. Present to migrate holder's auditor mirror. At least one of this field and `IssuerEncryptedAmount` must be present. |
| `PreviousIssuerEncryptionKey` | Conditional | `string`  | `BLOB`        | N/A                           | A 33-byte compressed ElGamal public key: the issuer key the holder's existing `sfIssuerEncryptedBalance` was encrypted under. **Required** when `Holder` and `IssuerEncryptedAmount` are both present, and **forbidden** otherwise.                          |
| `ZKProof`                     | Yes         | `string`  | `BLOB`        | N/A                           | A single compact Chaum-Pedersen equality proof proving the new ciphertext(s) encrypt the same value as the on-ledger mirror(s). When both fields are present, the proof covers both statements under one Fiat-Shamir challenge.                              |

#### 5.4.3. Transaction Fee

10x base fee, consistent with XLS-0096 confidential transactions.

#### 5.4.4. Failure Conditions

##### 5.4.4.1. Data Verification

1. Either the `ConfidentialMPTKeyRotation` or the `ConfidentialTransfer` amendment is not enabled. (`temDISABLED`)
2. Issuer mode: `Holder` is present but `Account` is not the issuer of the `MPTokenIssuanceID`. (`temMALFORMED`)
3. Issuer mode(`Holder` is present): `Account` is the same as `Holder`. (`temMALFORMED`)
4. Holder mode(`Holder` is absent): `Account` is the issuer. (`temMALFORMED`)
5. Neither `IssuerEncryptedAmount` nor `AuditorEncryptedAmount` is present. (`temMALFORMED`)
6. Any present `IssuerEncryptedAmount` or `AuditorEncryptedAmount` has an invalid length or represents an invalid elliptic curve point. (`temBAD_CIPHERTEXT`)
7. `PreviousIssuerEncryptionKey` is present but is not a valid 33-byte compressed elliptic curve point. (`temMALFORMED`)
8. `PreviousIssuerEncryptionKey` does not follow the presence rule: the field is required only when `Holder` and `IssuerEncryptedAmount` are both present, and must be absent in every other case. (`temMALFORMED`)
9. `ZKProof` length is not exactly the expected proof size for the detected mode. (128 bytes in every mode - see Section 10) (`temMALFORMED`)

##### 5.4.4.2. Protocol-Level Failures

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

#### 5.4.5. State Changes

**On Success (`tesSUCCESS`):**

If `IssuerEncryptedAmount` is present:

1. `sfIssuerEncryptedBalance` on the holder's `MPToken` is replaced by `IssuerEncryptedAmount`.
2. `sfIssuerKeyMirrorEpoch` on the `MPToken` is set to the issuance's current `sfIssuerKeyEpoch`.

If `AuditorEncryptedAmount` is present:

1. `sfAuditorEncryptedBalance` on the holder's `MPToken` is set to `AuditorEncryptedAmount`, creating the field if the holder did not previously have an auditor mirror.
2. `sfAuditorKeyMirrorEpoch` on the `MPToken` is set to the issuance's current `sfAuditorKeyEpoch`, unless that epoch is 0, in which case the field is left absent. An absent mirror epoch is equivalent to 0, so this only arises on first-time registration of an auditor mirror before any auditor key rotation has occurred.

#### 5.4.6. Example JSON

Which of `IssuerEncryptedAmount` and `AuditorEncryptedAmount` a transaction
carries depends on the use case, at least one must be present, and both may be.
`PreviousIssuerEncryptionKey` follows from that: it is required whenever the
transaction is in issuer mode and carries `IssuerEncryptedAmount`, and must be
absent in every other case.

Issuer mode:

```json
{
  "TransactionType": "ConfidentialMPTMirrorUpdate",
  "Account": "rIssuerAccountAddress",
  "MPTokenIssuanceID": "000000012A9F1D3C...",
  "Holder": "rHolderAccountAddress",
  "IssuerEncryptedAmount": "02a1b2c3d4e5f6...",
  "AuditorEncryptedAmount": "02c3d4e5f6a7b8...",
  "PreviousIssuerEncryptionKey": "02b7c8d9e0f1a2...",
  "ZKProof": "03f1e2d3c4b5a6..."
}
```

Holder mode:

```json
{
  "TransactionType": "ConfidentialMPTMirrorUpdate",
  "Account": "rHolderAccountAddress",
  "MPTokenIssuanceID": "000000012A9F1D3C...",
  "IssuerEncryptedAmount": "02a1b2c3d4e5f6...",
  "AuditorEncryptedAmount": "02c3d4e5f6a7b8...",
  "ZKProof": "03a1b2c3d4e5f6..."
}
```

#### 5.4.7. Proof Constructions

`ConfidentialMPTMirrorUpdate` has six mode combinations, determined by `Holder` presence and by which of `IssuerEncryptedAmount` / `AuditorEncryptedAmount` the transaction carries. Each is discharged by its own compact sigma protocol over secp256k1, and each is 128 bytes. The relations and the prover and verifier algorithms are specified in the companion proof specification, except that the holder both-mirrors variant is given there in outline only and the two auditor-only variants are not yet covered. This section states only what each proof establishes.

Every variant proves the same thing: that the new ciphertext or ciphertexts encrypt the same balance as a ciphertext already on the ledger, without revealing it. They differ in which ledger ciphertext serves as the anchor and which secret key decrypts it. The anchor is always bound by a secret key rather than by encryption randomness, because these ciphertexts accumulate homomorphically and no party knows the aggregate randomness of its own current ciphertext.

**Issuer mode** anchors to the holder's on-ledger `IssuerEncryptedBalance`, decrypted with the issuer secret key. That mirror is the issuer's only source of the balance, which is why the issuer can migrate the auditor mirror without holding the auditor secret key.

- Issuer mirror: proves `IssuerEncryptedAmount` encrypts the balance the mirror encodes under the pre-rotation issuer key. Because rotation overwrites `sfIssuerEncryptionKey` in place, that key is not recoverable from ledger state at verification time and is carried on the transaction as `PreviousIssuerEncryptionKey` (Section 5.4.2).
- Auditor mirror only: proves `AuditorEncryptedAmount` encrypts the balance the mirror encodes under the _current_ issuer key. Condition 9 of Section 5.4.4.2 requires the issuer mirror to be up to date for this variant, so no historical key is involved. The same relation covers auditor late registration, which differs only in the ledger precondition - the auditor mirror is absent rather than stale.
- Both mirrors: a single AND-composed proof covering both statements under one Fiat-Shamir challenge.

**Holder mode** anchors to the holder's own `ConfidentialBalanceSpending`, decrypted with sk_H. Knowledge of sk_H both establishes key possession and decrypts the anchor, so a holder who cannot decrypt their spending balance cannot prove any claimed balance. The same three variants exist as in issuer mode, and the auditor-only variant is a separate relation rather than the issuer-mirror one re-parameterized. All three require `ConfidentialBalanceInbox` to be the canonical encrypted zero - see condition 11 of Section 5.4.4.2 - because the spending balance encodes only the spendable portion while the mirrors encode the total. Holder mode is what makes migration possible at all in the issuer key loss scenario, where the issuer cannot perform active re-encryption. See Section 7.

Two limits on what these proofs establish are worth stating. Holder-mode proofs never reference the mirror they overwrite, so they are equivalent to issuer mode only under the XLS-0096 invariant that a holder's issuer mirror encodes the same balance as spending plus inbox; that invariant is a hypothesis of these proofs, not a consequence. And no variant references a holder's prior auditor mirror: an auditor mirror migration is proved equal to the issuer's decryption of the issuer mirror or to the holder's spending balance, never to the auditor mirror it replaces.

**Shared randomness**: the two AND-composed variants reuse a single randomness value for both new ciphertexts, which is what keeps them at 128 bytes rather than 160. It also forces the two ciphertexts to share an identical first component, and the sigma equations do not themselves constrain the auditor one, so validators MUST reject the transaction when the two do not match. The randomness MUST be sampled freshly for every transaction and every holder; reusing one value across a migration batch exposes every pairwise balance difference on-ledger.

### 5.5. Transaction: `ConfidentialMPTHolderKeyUpdate`

Allows a holder to rotate their ElGamal key (rotation mode), authorize key replacement after key loss (recovery mode), or revoke a pending recovery authorization (cancel mode). Mode is selected by transaction flag.

#### 5.5.1. Use Cases

- **Voluntary key rotation** (`tfHolderKeyRotation`): Holder decrypts `ConfidentialBalanceSpending` and `ConfidentialBalanceInbox`, re-encrypts both under pk_H', and submits a single AND-composed proof covering the spending balance and possession of the new key. Atomic - no issuer involvement. The holder may optionally run `ConfidentialMPTMergeInbox` before rotating, so that `ConfidentialBalanceInbox` is `EncZero` under pk_H' and publicly verifiable as such. This costs an extra transaction.
- **Key loss recovery authorization** (`tfHolderKeyRecovery`): Holder registers pk_H' as `RecoveryKey` on `MPToken`, consenting to issuer-completed recovery via `ConfidentialMPTRecoverBalance`.
- **Recovery cancellation** (`tfCancelRecovery`): Holder clears a pending `RecoveryKey` from their `MPToken`, revoking their consent to issuer-completed recovery. No cryptographic proof is required; the holder's signing key signature is sufficient authorization to cancel their own pending authorization.

#### 5.5.2. Fields

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

#### 5.5.3. Flags

| Flag Name             | Hex Value    | Decimal Value | Description                                                                                      |
| :-------------------- | :----------- | :------------ | :----------------------------------------------------------------------------------------------- |
| `tfHolderKeyRotation` | `0x00000001` | 1             | Rotation mode: re-encrypt the spending and inbox balances under the new key in this transaction. |
| `tfHolderKeyRecovery` | `0x00000002` | 2             | Recovery mode: register the new key as `sfRecoveryKey` for issuer-completed recovery.            |
| `tfCancelRecovery`    | `0x00000004` | 4             | Cancel mode: clear a pending `RecoveryKey` from the holder's `MPToken`.                          |

Exactly one of the three flags must be set.

#### 5.5.4. Transaction Fee

10x base fee, consistent with XLS-0096 confidential transactions.

#### 5.5.5. Failure Conditions

##### 5.5.5.1. Data Verification

1. Either the `ConfidentialMPTKeyRotation` or the `ConfidentialTransfer` amendment is not enabled. (`temDISABLED`)
2. Neither `tfHolderKeyRotation`, `tfHolderKeyRecovery`, nor `tfCancelRecovery` is set, or more than one is set. (`temINVALID_FLAG`)
3. Account is the issuer of `MPTokenIssuanceID` - the issuer cannot hold confidential balances. (`temMALFORMED`)
4. Rotation or recovery mode: `HolderEncryptionKey` is absent, is not exactly 33 bytes, or is not a well-formed compressed secp256k1 point. (`temMALFORMED`)
5. Rotation mode: `ConfidentialBalanceSpending` or `ConfidentialBalanceInbox` is missing. (`temMALFORMED`)
6. Recovery or cancel mode: `ConfidentialBalanceSpending` or `ConfidentialBalanceInbox` is present. (`temMALFORMED`)
7. Cancel mode: `HolderEncryptionKey` or `ZKProof` is present - cancel mode requires no additional fields beyond `TransactionType`, Account, `MPTokenIssuanceID`, and Flags. (`temMALFORMED`)
8. Any present `ConfidentialBalanceSpending` or `ConfidentialBalanceInbox` has an invalid length or represents an invalid elliptic curve point. (`temBAD_CIPHERTEXT`)
9. Rotation or recovery mode: `ZKProof` is absent or its length is not exactly the expected size for the selected mode. (160 bytes in rotation mode, 64 bytes in recovery mode - see Section 10) (`temMALFORMED`)

##### 5.5.5.2. Protocol-Level Failures

1. The `MPTokenIssuance` or the holder's `MPToken` object does not exist. (`tecOBJECT_NOT_FOUND`)
2. The issuance does not have the `lsfMPTCanHoldConfidentialBalance` flag set. (`tecNO_PERMISSION`)
3. The holder's `MPToken` is missing confidential state (`HolderEncryptionKey`, `ConfidentialBalanceSpending`, or `ConfidentialBalanceInbox`). (`tecNO_PERMISSION`)
4. Rotation or recovery mode: `HolderEncryptionKey` equals the current on-ledger `HolderEncryptionKey` (no-op). (`tecNO_PERMISSION`)
5. Rotation mode: `IssuerKeyMirrorEpoch` does not equal `IssuerKeyEpoch`; the issuer mirror must be migrated before rotating. (`tecNO_PERMISSION`)
6. Rotation mode: an auditor key is configured and `AuditorEncryptedBalance` is absent or `AuditorKeyMirrorEpoch` does not equal `AuditorKeyEpoch`; the auditor mirror must be initialized or migrated before rotating. (`tecNO_PERMISSION`)
7. Recovery mode: `RecoveryKey` is already set on the `MPToken` - a pending recovery authorization exists. (`tecNO_PERMISSION`)
8. Cancel mode: `RecoveryKey` is not set on the `MPToken` - nothing to cancel. (`tecNO_PERMISSION`)
9. Recovery mode: `ZKProof` (Schnorr PoK) fails to verify against `HolderEncryptionKey`. (`tecBAD_PROOF`)
10. Rotation mode: `ZKProof` fails to verify. It is a single AND-composed proof establishing both that the submitted `ConfidentialBalanceSpending` encrypts under `HolderEncryptionKey` the same value the on-ledger `ConfidentialBalanceSpending` encrypts under the old key, and that the submitter possesses the secret key for `HolderEncryptionKey`. (`tecBAD_PROOF`)

**Cancel mode** (`tfCancelRecovery`): No additional fields are required beyond `TransactionType`, Account, `MPTokenIssuanceID`, and Flags. The transaction must be signed by the holder's XRPL signing key. No cryptographic proof is required - the holder's signing key signature is sufficient authorization to cancel their own pending recovery.

**Operational note**: This is a wallet-level concern - validators cannot detect in-flight transactions. When a `ConfidentialMPTSend` and a `ConfidentialMPTHolderKeyUpdate` (rotation) are submitted close together, both proofs are bound to `ConfidentialBalanceVersion` via the context hash. Whichever transaction lands second will find the version has already incremented and will be rejected with `tecBAD_PROOF`. No funds are lost - just a rejected transaction requiring resubmission. To avoid this, wallet software should:

1. Check for pending (submitted but unconfirmed) `ConfidentialMPTSend` transactions before initiating rotation.
2. Queue rotation until all pending sends are confirmed in a closed ledger.
3. If using Tickets: cancel or consume all outstanding Tickets that would submit `ConfidentialMPTSend` before submitting the rotation Ticket. Standard Sequence numbers enforce ordering naturally; Tickets break this ordering and can cause sends and rotation to land in unpredictable order.

#### 5.5.6. State Changes

**On Success (`tesSUCCESS`):**

**Rotation mode**:

1. `HolderEncryptionKey` on `MPToken` ← new key value
2. `ConfidentialBalanceSpending` on `MPToken` ← new ciphertext
3. `ConfidentialBalanceInbox` on `MPToken` ← new ciphertext
4. `ConfidentialBalanceVersion` on `MPToken` ← `ConfidentialBalanceVersion` + 1

**Recovery mode**:

1. `RecoveryKey` on `MPToken` ← `HolderEncryptionKey` (new value)
2. All other fields unchanged

**Cancel mode**:

1. `RecoveryKey` on `MPToken` ← cleared (field removed)
2. All other fields unchanged - `HolderEncryptionKey`, `ConfidentialBalanceSpending`, `ConfidentialBalanceInbox`, `ConfidentialBalanceVersion` are not modified

#### 5.5.7. Example JSON

Rotation mode:

```json
{
  "TransactionType": "ConfidentialMPTHolderKeyUpdate",
  "Account": "rHolderAccountAddress",
  "MPTokenIssuanceID": "000000012A9F1D3C...",
  "Flags": 1,
  "HolderEncryptionKey": "02a1b2c3d4e5f6...",
  "ConfidentialBalanceSpending": "02b1c2d3e4f5a6...",
  "ConfidentialBalanceInbox": "02c1d2e3f4a5b6...",
  "ZKProof": "03d1e2f3a4b5c6...",
  "Fee": "120",
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
  "HolderEncryptionKey": "02a1b2c3d4e5f6...",
  "ZKProof": "03f1e2d3c4b5a6...",
  "Fee": "120",
  "Sequence": 47
}
```

### 5.6. Transaction: `ConfidentialMPTRecoverBalance`

Completes holder key loss recovery. The issuer re-encrypts the holder's balance under the authorized `RecoveryKey` and submits a compact Chaum-Pedersen equality proof. Validators enforce that `RecoveryKey` is present - the issuer cannot act without prior holder authorization.

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

10x base fee, consistent with XLS-0096 confidential transactions.

#### 5.6.3. Failure Conditions

##### 5.6.3.1. Data Verification

1. Either the `ConfidentialMPTKeyRotation` or the `ConfidentialTransfer` amendment is not enabled. (`temDISABLED`)
2. Account is not the issuer of `MPTokenIssuanceID`. (`temMALFORMED`)
3. Account is the same as Holder. (`temMALFORMED`)
4. `ConfidentialBalanceSpending` has an invalid length or represents an invalid elliptic curve point. (`temBAD_CIPHERTEXT`)
5. `ZKProof` is absent or its length is not exactly the expected compact Chaum-Pedersen equality proof size. (128 bytes - see Section 10) (`temMALFORMED`)

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
  "ConfidentialBalanceSpending": "02a1b2c3d4e5f6...",
  "ZKProof": "03f1e2d3c4b5a6..."
}
```

### 5.7. Transaction: `ConfidentialMPTConvert`

`ConfidentialMPTConvert` is defined in XLS-0096. This amendment adds a mirror-staleness precondition for holders whose confidential state is already initialized, and specifies the mirror epochs written when a holder initializes confidential state. Its fields, flags, and fee are unchanged.

#### 5.7.1. Failure Conditions

This amendment introduces no new data-verification (`tem`) failures. It adds the following protocol-level failures, using the definition of a current mirror in Section 4.6.1:

1. The holder's confidential state is already initialized and the holder's issuer mirror is not current. (`tecNO_PERMISSION`)
2. The holder's confidential state is already initialized, an auditor key is configured, and the holder's auditor mirror is not current. (`tecNO_PERMISSION`)

A holder initializing confidential state for the first time cannot be stale, because the mirrors are created under the current keys in the same transaction. These conditions therefore apply only to already-initialized holders.

#### 5.7.2. State Changes

**On Success (`tesSUCCESS`):**

All state changes specified in XLS-0096 §7.5 apply unchanged. This amendment adds the following:

- When confidential state is initialized for the first time, the mirror epochs are set to the corresponding key epochs: `IssuerKeyMirrorEpoch` ← `IssuerKeyEpoch`, and `AuditorKeyMirrorEpoch` ← `AuditorKeyEpoch` when an auditor key is configured. An epoch of 0 is omitted from ledger storage rather than written explicitly.
- For an already-initialized holder, `IssuerKeyMirrorEpoch` and `AuditorKeyMirrorEpoch` retain their existing values, since both mirrors are current as a precondition of success.

### 5.8. Transaction: `ConfidentialMPTSend`

`ConfidentialMPTSend` is defined in XLS-0096. This amendment adds a mirror-staleness precondition for both parties. Its fields, flags, and fee are unchanged.

#### 5.8.1. Failure Conditions

This amendment introduces no new data-verification (`tem`) failures. It adds the following protocol-level failures, using the definition of a current mirror in Section 4.6.1:

1. The sender's issuer mirror is not current. (`tecNO_PERMISSION`)
2. An auditor key is configured and the sender's auditor mirror is not current. (`tecNO_PERMISSION`)
3. The destination's issuer mirror is not current. (`tecNO_PERMISSION`)
4. An auditor key is configured and the destination's auditor mirror is not current. (`tecNO_PERMISSION`)

#### 5.8.2. State Changes

**On Success (`tesSUCCESS`):**

All state changes specified in XLS-0096 §8.4 apply unchanged. No field introduced by this amendment changes: both parties' mirrors are current as a precondition of success, so `IssuerKeyMirrorEpoch` and `AuditorKeyMirrorEpoch` retain their existing values.

### 5.9. Transaction: `ConfidentialMPTConvertBack`

`ConfidentialMPTConvertBack` is defined in XLS-0096. This amendment adds a mirror-staleness precondition. Its fields, flags, and fee are unchanged.

#### 5.9.1. Failure Conditions

This amendment introduces no new data-verification (`tem`) failures. It adds the following protocol-level failures, using the definition of a current mirror in Section 4.6.1:

1. The holder's issuer mirror is not current. (`tecNO_PERMISSION`)
2. An auditor key is configured and the holder's auditor mirror is not current. (`tecNO_PERMISSION`)

#### 5.9.2. State Changes

**On Success (`tesSUCCESS`):**

All state changes specified in XLS-0096 §10.5 apply unchanged. No field introduced by this amendment changes: the holder's mirrors are current as a precondition of success, so `IssuerKeyMirrorEpoch` and `AuditorKeyMirrorEpoch` retain their existing values.

### 5.10. Transaction: `ConfidentialMPTClawback`

`ConfidentialMPTClawback` is defined in XLS-0096. This amendment adds a mirror-staleness precondition on the issuer mirror and rewrites both mirror epochs on success. Its fields, flags, and fee are unchanged.

#### 5.10.1. Failure Conditions

This amendment introduces no new data-verification (`tem`) failures. It adds the following protocol-level failure, using the definition of a current mirror in Section 4.6.1:

1. The holder's issuer mirror is not current. (`tecNO_PERMISSION`)

Only the issuer mirror is required to be current, because the clawback proof is verified against `IssuerEncryptedBalance`. Producing the clawed-back amount therefore requires decrypting that mirror, so the issuer needs the secret key for the currently registered `IssuerEncryptionKey`; see Section 7 for the issuer key loss case. A stale or missing auditor mirror does not block clawback; it is repaired by the state changes below.

#### 5.10.2. State Changes

**On Success (`tesSUCCESS`):**

All state changes specified in XLS-0096 §11.4 apply unchanged. This amendment adds the following:

- `IssuerEncryptedBalance` ← canonical encrypted zero under the currently registered `IssuerEncryptionKey`, and `IssuerKeyMirrorEpoch` ← `IssuerKeyEpoch`.
- When an auditor key is configured, `AuditorEncryptedBalance` ← canonical encrypted zero under the currently registered `AuditorEncryptionKey`, and `AuditorKeyMirrorEpoch` ← `AuditorKeyEpoch`.
- Because both mirrors are rewritten as encryptions of zero under the current keys, a clawed-back holder is left with current mirrors even if a mirror was stale or missing beforehand. No `ConfidentialMPTMirrorUpdate` is required for that holder afterwards.

## 6. Freeze Interactions with Key Rotation

This amendment does not change the lock behavior defined by XLS-0096. A
holder-level or issuance-level lock does not prevent key rotation through
`MPTokenIssuanceSet` or any transaction introduced by this amendment, because
these operations only rotate keys, migrate mirrors, manage recovery
authorization, or re-encrypt balances without moving value. They do not clear
or otherwise modify the lock, so the holder remains unable to spend while the
lock is set. Specifically, holders are allowed to rotate their keys while locked, as a locked account remains vulnerable to key compromise

## 7. Issuer Key Loss

### 7.1. Problem

The issuer has irrecoverably lost sk_I. They can no longer decrypt any holder's issuer mirror, execute clawbacks, or perform active mirror re-encryption. The XRPL signing key is unaffected.

### 7.2. Impact

- Clawback authority is lost for all holders. Per XLS-0096, `ConfidentialMPTClawback` verifies the ZKP against the current `sfIssuerEncryptionKey` on `MPTokenIssuance`. After registering a new pk_I', all holder mirrors are stale - clawback is blocked for every holder until their mirror is migrated. Without sk_I, the issuer cannot perform `ConfidentialMPTMirrorUpdate` to migrate mirrors, so clawback authority is suspended across the board.
- Active re-encryption of issuer mirrors is impossible because the issuer cannot decrypt old issuer mirrors without sk_I. Auditor mirror re-encryption is also blocked until each holder self-migrates the issuer mirror under pk_I'; after that migration, the issuer can decrypt the reconstructed issuer mirror with sk_I' and use it to re-encrypt that holder's auditor mirror.
- Auditor key rotation is blocked - the issuer re-encrypts auditor mirrors via the issuer mirror, which they can no longer decrypt.

### 7.3. Recommended Approach: Loss Prevention

The primary recommendation is loss prevention through institutional key management:

- HSMs for key storage
- Shamir secret sharing of sk_I across custody providers
- Backup and recovery playbooks
- Same rigor applied to XRPL signing keys

### 7.4. Recovery Path: Holder-Driven Mirror Reconstruction

Issuer key loss creates an asymmetric situation analogous to holder key loss - the party who cannot act cryptographically requires the other party to complete the migration. The key difference from normal rotation is:

**Normal rotation (issuer driven)**:

- Issuer has sk_I and can decrypt all holder mirrors
- Issuer submits `ConfidentialMPTMirrorUpdate` (with Holder field) for each holder
- Holders are passive - no action required from them

**Issuer key loss (holder driven)**:

- Issuer has lost sk_I and cannot decrypt holder issuer mirrors
- Each holder must submit `ConfidentialMPTMirrorUpdate` (without Holder field) themselves
- Issuer is passive for issuer mirrors - only the holder can act
- Holders know b from decrypting `ConfidentialBalanceSpending` via sk_H and re-encrypt it under the new pk_I' using the cross-key equality proof (Section 5.4.7)

This is a one-step process per holder - unlike holder key loss recovery which requires two steps (holder authorizes, issuer completes). Here the holder acts alone with no issuer involvement needed for their mirror.

**How it works**:

1. Issuer registers new pk_I' via `MPTokenIssuanceSet` (they still have their XRPL signing key).
2. `IssuerKeyEpoch` increments.
3. Validators reject holder confidential transactions that require an issuer mirror while `IssuerKeyMirrorEpoch` does not equal `IssuerKeyEpoch`.
4. Each holder runs `ConfidentialMPTMergeInbox` first, then submits `ConfidentialMPTMirrorUpdate` without a Holder field with the cross-key equality proof to self-migrate their issuer mirror. Merge is required because the cross-key equality proof anchors to `ConfidentialBalanceSpending` which encodes only b_s - if `ConfidentialBalanceInbox` is non-zero, the new issuer mirror would encode b_s instead of the full b = b_s + b_in, producing a mirror that doesn't match the holder's actual total balance and breaking clawback correctness. Holders may also self-migrate their auditor mirror in the same transaction if needed.
5. Issuer regains clawback authority over each holder as their mirror is reconstructed.

**Limitation**: Inactive holders. Holders who do not transact will not self-migrate their issuer mirrors. The issuer cannot force-migrate issuer mirrors without sk_I, so clawback authority remains suspended until they act. Their auditor mirrors also cannot be actively migrated from the stale issuer mirror: `sk_I'` can decrypt only an issuer mirror that the holder has already reconstructed under `pk_I'`. Auditor visibility therefore remains blocked unless the holder self-migrates an appropriate mirror.

**Limitation**: Historical decryption. The issuer cannot decrypt historical ciphertexts from before the key loss.

### 7.5. Counterparty Dependency and Recovery Limitations

Holder key recovery is not unilateral. It requires an active issuer that
retains `sk_I` and completes `ConfidentialMPTRecoverBalance`. If the issuer is
inactive or unavailable, a holder's pending key recovery cannot complete even
after `RecoveryKey` has been registered.

Issuer key-loss recovery is likewise not unilateral. It requires an active
holder that retains `sk_H` and self-migrates the issuer mirror. If the issuer
loses `sk_I` while a holder is inactive or unavailable, that holder's issuer
mirror cannot be reconstructed and the issuer's clawback authority over that
holder remains suspended. The protocol provides no on-chain fallback without
participation from a party that can decrypt an equivalent mirror.

An inactive holder cannot self-migrate their issuer mirror. The issuer may wait
for the holder to return or contact them through off-chain channels, but until
the holder participates, confidential transactions and clawback remain
unavailable for that holder. If the holder never participates, the suspension
is permanent. This combined situation is expected to be rare under the issuer
key-management practices recommended in Section 7.3, but it is an explicit
limitation of the recovery model.

## 8. Operational Considerations

### 8.1. Migration Throughput

Each `ConfidentialMPTMirrorUpdate` carries a new mirror ciphertext (66 bytes) and a 128-byte compact Chaum-Pedersen equality proof. Fees are 10x base fee. Traversing the entire holders list is done off-chain.

### 8.2. Wallet Implementation Guidance

Wallet software implementing `ConfidentialMPTHolderKeyUpdate` in rotation mode must:

1. Verify no `ConfidentialMPTSend` transactions are pending before initiating rotation.
2. Surface a warning if pending sends exist - the `ConfidentialBalanceVersion` bump will invalidate their proofs.
3. Queue rotation until all pending sends are confirmed in a closed ledger.
4. Ensure all outstanding Tickets referencing `ConfidentialBalanceSpending` are consumed or cancelled before submitting rotation.

**If this check is missed**: There is no ambiguous state and no funds are at risk. The outcome depends on which transaction lands first:

- **Rotation lands first**: The in-flight send's proof is bound to the old `ConfidentialBalanceVersion` and is rejected with `tecBAD_PROOF`. The holder's full balance is intact under pk_H'. The holder reconstructs the send proof under the new key and resubmits.
- **Send lands first**: `ConfidentialBalanceVersion` bumps and `ConfidentialBalanceSpending` is debited normally. The rotation proof - constructed against the old version - is rejected with `tecBAD_PROOF`. The holder reconstructs the rotation proof against the updated state and resubmits.

In both cases the result is a cleanly rejected transaction requiring resubmission - not a partial or ambiguous state. Clawback is unaffected in either scenario: `ConfidentialMPTClawback` uses `IssuerEncryptedBalance` (the issuer mirror), not `ConfidentialBalanceSpending` or `ConfidentialBalanceVersion`. The operational note is a UX concern, not a safety concern.

### 8.3. Issuer Recovery Request Detection

After a holder submits `ConfidentialMPTHolderKeyUpdate` with `tfHolderKeyRecovery`, `RecoveryKey` is set on their `MPToken`. The issuer needs to detect this to submit `ConfidentialMPTRecoverBalance` promptly. Two complementary mechanisms are recommended:

**Option 1: Real-time WebSocket subscription**

The issuer subscribes to the XRPL WebSocket API and listens for `ConfidentialMPTHolderKeyUpdate` transactions with `tfHolderKeyRecovery` flag set. When one arrives, the issuer is notified in real-time and can immediately prepare and submit `ConfidentialMPTRecoverBalance`. Clio is optimized for WebSocket API calls for validated ledger data and supports transaction stream subscriptions.

**Option 2: Periodic Clio query (catch-up mechanism)**

As a reliability backstop for missed WebSocket events (e.g. connection drops), the issuer periodically pages through Clio's `mpt_holders` method. Each result supplies an `mptoken_index`; the issuer then queries that ledger entry and filters the returned `MPToken` objects for `RecoveryKey`. This requires per-holder lookups unless `mpt_holders` is extended to return `RecoveryKey`.

```json
{
  "command": "mpt_holders",
  "mpt_issuance_id": "000000012A9F1D3C...",
  "ledger_index": "validated"
}
```

For each returned `mptoken_index`, the issuer retrieves the corresponding `MPToken` ledger entry and checks whether `RecoveryKey` is present.

**Recommended approach**: Both mechanisms together. Option 1 provides real-time processing of recovery requests; Option 2 provides periodic catch-up for events missed during WebSocket downtime. The polling interval for Option 2 can be tuned based on the issuer's SLA for recovery completion.

**No protocol changes required**. Both mechanisms use existing XRPL and Clio infrastructure. This is purely an operational implementation concern for issuers.

## 9. Security Considerations

### 9.1. Key Compromise vs. Key Loss

**Key compromise** - attacker has the key, legitimate holder still does. Attacker retains read access until re-encryption is complete. Rotation is the remediation.

**Key loss** - legitimate holder no longer has the key. Recovery paths require counterparty involvement. Loss prevention is the primary recommendation.

### 9.2. No New Cryptographic Assumptions

All constructions reuse existing XLS-0096 primitives: compact Chaum-Pedersen equality proofs and Schnorr proofs of knowledge. No new cryptographic assumptions introduced. No range proofs are required, because no key rotation or recovery transaction changes a balance - each only re-encrypts an existing value under a different key.

### 9.3. Issuer Visibility During Re-encryption

The decrypt-then-re-encrypt approach requires the issuer to learn b. This is inherent and consistent with the issuer's existing visibility via the mirror ciphertext in XLS-0096. No new privacy exposure introduced.

### 9.4. No Schnorr PoK for Issuer and Auditor Key Rotation

Consistent with XLS-0096's existing behavior for initial key setting. A rogue issuer key only harms the issuer's own mirror and clawback capability.

### 9.5. `ConfidentialBalanceVersion` Increment on Holder Key Rotation

`ConfidentialMPTHolderKeyUpdate` in rotation mode increments `ConfidentialBalanceVersion`, invalidating in-flight `ConfidentialMPTSend` proofs. See Section 8.2.

### 9.6. Two-Step Recovery Authorization

The holder's authorization (`tfHolderKeyRecovery`) is signed by the holder's XRPL signing key. Validators enforce that `RecoveryKey` is present before accepting `ConfidentialMPTRecoverBalance`. The issuer cannot act unilaterally.

### 9.7. `RecoveryKey` Liveness Concern

If the issuer never completes recovery, the holder remains locked out indefinitely. The protocol defines no automatic expiry for `RecoveryKey` - forcing expiry would penalize a holder already in a degraded state without any ledger health benefit. Per XLS-0096, clawback burns tokens rather than returning them - this is not a viable workaround.

### 9.8. Issuer Key Loss and Clawback Authority

After key rotation, clawback is blocked until the holder's `IssuerKeyMirrorEpoch` equals `IssuerKeyEpoch` - the ZKP is verified against the current `sfIssuerEncryptionKey`, not a caller-selectable key. Loss of sk_I therefore suspends clawback authority for all holders - without sk_I the issuer cannot migrate mirrors, and without migrated mirrors clawback cannot proceed. Authority is restored progressively as holders self-migrate their mirrors under pk_I'.

### 9.9. Successive Rotations and Historical Issuer-Key Retention

The protocol does not enforce a global gate preventing successive rotations before migration is complete. Per-transaction mirror checks enforce correctness at the point of use for each individual holder, regardless of how many epochs behind they are.

Historical issuer secret-key retention is optional and depends on the issuer's
migration strategy. If the issuer intends to actively migrate any holder whose
`IssuerEncryptedBalance` remains encrypted under an older issuer key, the
issuer MUST retain the corresponding historical secret key until those holder
mirrors have been migrated.

Once an issuance-wide holder traversal confirms that no issuer mirror remains
at the corresponding epoch, the historical secret key is no longer required
and may be destroyed. An issuer may instead destroy the old secret key earlier
and rely on the remaining holders to self-migrate using `sk_H`. Doing so does
not affect ledger correctness, but permanently removes the issuer-driven
migration path for those holders.

Historical auditor secret keys are not required for mirror migration because
auditor mirrors are reconstructed from a current issuer mirror or through
holder self-migration.

### 9.10. Holder Self-Migration Security

For holder self-migration (Section 5.4.7), validators must enforce:

- `ConfidentialBalanceInbox` equals canonical encrypted zero before accepting the transaction.
- Proof is bound to the current `ConfidentialBalanceVersion` via the context hash.
- `IssuerEncryptedAmount` is verifiable under the current `IssuerEncryptionKey` from `MPTokenIssuance`.

### 9.11. Seed-Derived ElGamal Keys

Wallets may derive ElGamal keys from the XRPL account seed. This eliminates key loss for standard single-signature accounts but does not solve key compromise. Multi-sig accounts cannot use seed derivation. See Appendix A.

## 10. Analysis of Transaction Cost and Performance

### 10.1. Cryptographic Proof Summary

| Transaction                      | Mode                  | Proof Type                                                     | Size      |
| :------------------------------- | :-------------------- | :------------------------------------------------------------- | :-------- |
| `MPTokenIssuanceSet` (rotation)  |                       | None                                                           | 0 bytes   |
| `ConfidentialMPTMirrorUpdate`    | Issuer, one mirror    | Compact Chaum-Pedersen equality                                | 128 bytes |
| `ConfidentialMPTMirrorUpdate`    | Issuer, both mirrors  | Compact Chaum-Pedersen (AND-composed)                          | 128 bytes |
| `ConfidentialMPTMirrorUpdate`    | Holder self-migration | Cross-key equality proof                                       | 128 bytes |
| `ConfidentialMPTHolderKeyUpdate` | Rotation              | Compact equality (spending) + new-key possession, AND-composed | 160 bytes |
| `ConfidentialMPTHolderKeyUpdate` | Recovery              | Schnorr PoK                                                    | 64 bytes  |
| `ConfidentialMPTRecoverBalance`  |                       | Compact Chaum-Pedersen equality                                | 128 bytes |

All new transactions are charged 10x the base fee, consistent with XLS-0096.

## 11. Permissions

Per XLS-75 permission delegation, an account can grant another account permission to submit specific transaction types on its behalf.

In this amendment, when interacting with permission delegation, a delegate must never be able to introduce an ElGamal encryption key of its own choosing:

- `ConfidentialMPTHolderKeyUpdate` is not delegable. Rotation and recovery modes both register a submitter-chosen holder key, and cancel mode is covered as well because delegability is set per transaction type. This matches `ConfidentialMPTConvert`, which XLS-0096 makes non-delegable for the same reason.
- `MPTokenIssuanceSet` remains delegable, but a delegated submission **MUST NOT** carry `IssuerEncryptionKey` or `AuditorEncryptionKey`, meaning the delegated account cannot rotate the issuer or auditor key.
- `ConfidentialMPTMirrorUpdate` and `ConfidentialMPTRecoverBalance` are delegable.

## 12. Rationale

### 12.1. Decrypt-then-Re-encrypt over Proxy Re-encryption

Standard PRE constructions require bilinear pairings, incompatible with secp256k1. PRE also introduces new trust assumptions. Decrypt-then-re-encrypt uses existing primitives and the issuer already has visibility by design.

### 12.2. Active Re-encryption over Lazy Re-encryption

After issuer key rotation, two capabilities are blocked for unmigrated holders: confidential transactions (old and new key ciphertexts cannot be combined homomorphically) and clawback (ZKP verified against current `sfIssuerEncryptionKey`, not a caller-selectable key). Active re-encryption keeps restoration of both capabilities entirely under the issuer's control. The issuer may rotate multiple times without waiting for full migration - per-transaction staleness checks enforce correctness at the point of use.

### 12.3. Per-Holder Migration Transactions

`ConfidentialMPTMirrorUpdate` migrates a single holder, and the issuer traverses the holders list off-chain. A single on-ledger bulk migration was rejected because it would require unbounded computational work without reducing the payload size—the issuer must still provide a fresh ciphertext and equality proof for every holder. Additionally, per-holder transactions offer better fault isolation, preventing a single failure from reverting the entire migration list.

### 12.4. Issuer On-Chain Involvement in Holder Key Loss Recovery

The holder cannot re-encrypt balances without sk_I. Knowing b in plaintext is not sufficient - the ZKP requires sk_I to produce a proof anchored to `IssuerEncryptedBalance`. The source of b off-chain (issuer, auditor, or anyone else) does not matter - the cryptographic constraint is the same. This is why recovery completes through `ConfidentialMPTRecoverBalance` rather than the issuer disclosing the balance off-chain and letting the holder act alone.

### 12.5. Explicit Flags over Field Presence for Mode Detection

`ConfidentialMPTHolderKeyUpdate` selects its mode with explicit flags (`tfHolderKeyRotation` / `tfHolderKeyRecovery` / `tfCancelRecovery`) rather than inferring it from field presence. Flags make validator logic unambiguous and eliminate edge cases with partial field sets - rotation and recovery both carry `HolderEncryptionKey`, and cancel mode carries no additional field at all, so there is no field whose presence could serve as the discriminator.

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

No. Rotation increments `ConfidentialBalanceVersion`, invalidating in-flight send proofs. Queue rotation until all pending sends are confirmed.

### B.4: What happens to my inbox balance during key loss recovery?

It is reset to canonical encrypted zero. Any value in the inbox is consolidated into the spending balance via the issuer mirror. No value is lost.

### B.5: Can the issuer rotate my key without my consent?

No. `ConfidentialMPTRecoverBalance` is rejected if `RecoveryKey` is not set on your `MPToken`. The issuer cannot act without your prior on-chain authorization.

### B.6: How long does bulk mirror re-encryption take at scale?

Each `ConfidentialMPTMirrorUpdate` carries a new mirror ciphertext and compact Chaum-Pedersen equality proof. Fees are 10x base fee. Traversing the entire holders list is done off-chain.

### B.7: Can the issuer rotate keys multiple times in quick succession?

Yes - the protocol does not enforce a global gate blocking successive rotations. Holders with stale mirrors are blocked from transacting at the per-transaction level regardless of how many epochs behind they are. `ConfidentialMPTMirrorUpdate` bridges directly from any old epoch to the current epoch in one step.

### B.8: How can I verify that all mirrors have been migrated?

Compare `IssuerKeyEpoch` on `MPTokenIssuance` against `IssuerKeyMirrorEpoch` on each `MPToken`. Whether a mirror is stale is trivially known on-ledger in O(1).

### B.9: Does ledger replay break after key rotation?

No. Each XRPL ledger version is a complete, immutable snapshot preserving the `IssuerEncryptionKey` that was active at that moment. Replaying a historical transaction uses the `MPTokenIssuance` state from that exact ledger version. This is identical to how signing key rotation works on XRPL.
