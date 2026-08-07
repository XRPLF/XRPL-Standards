<pre>
  xls: ??
  title: ElGamal Key Rotation for Confidential MPTs
  description: Defines ElGamal key rotation for issuer, auditor, and holder roles in the Confidential MPT protocol, with key loss recovery mechanisms.
  author: Aanchal Malhotra (@amalhotra-ripple)
  co-author: Yinyi Qian <yqian@ripple.com>
  category: Amendment
  status: Draft
  requires: XLS-0096
  proposal-from: TBD
  created: 2026-04-01
  updated: 2026-07-22
</pre>

# ElGamal Key Rotation for Confidential MPTs

## 1. Abstract

This amendment extends XLS-0096 (Confidential Transfers for Multi-Purpose Tokens) with ElGamal key rotation for all three participant roles: issuer, auditor, and holder. It introduces 3 new transaction types (`ConfidentialMPTMirrorUpdate`, `ConfidentialMPTHolderKeyUpdate`, `ConfidentialMPTRecoverBalance`), extends one existing transaction type (`MPTokenIssuanceSet`), and adds new fields to the `MPTokenIssuance` and `MPToken` ledger objects. Key rotation is supported for both voluntary and loss-recovery scenarios. All new cryptographic constructions reuse existing primitives from XLS-0096 (compact Chaum-Pedersen equality proofs, Schnorr proofs of knowledge) and introduce no new cryptographic assumptions.

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
- **Stale Mirror**: A holder's issuer (or auditor) mirror ciphertext is stale when its mirror epoch is less than the current key epoch on `MPTokenIssuance`. A stale mirror is encrypted under an old key and cannot be combined homomorphically with new transaction deltas encrypted under the current key. Validators enforce staleness checks on all confidential transactions that touch the issuer mirror - see Section 13.1 for the full list of affected transactions and failure conditions.
- **Active Re-encryption**: The process by which the issuer submits `ConfidentialMPTMirrorUpdate` for each holder after a key rotation to re-encrypt mirror ciphertexts under the new key.
- **Recovery Key** (`sfRecoveryKey`): A transient field on `MPToken` set by the holder to authorize replacement of their ElGamal key when they have lost `sk_H`.

## 4. Scope

### 4.1 Modified Transaction Types

- `MPTokenIssuanceSet`: Extended to allow replacement of `IssuerEncryptionKey` and `AuditorEncryptionKey` when already present, enabling issuer and auditor key rotation.

### 4.2 New Transaction Types

- `ConfidentialMPTMirrorUpdate` (transaction type 90): Re-encrypts a single holder's issuer and/or auditor mirror ciphertext under the new key. Operates in two modes selected by transaction flag:
  -Issuer mode (`tfIssuerMirrorUpdate`): submitted by the issuer using a Chaum-Pedersen equality proof anchored to the on-ledger issuer mirror.
  - Holder mode (`tfHolderMirrorUpdate`): submitted by the holder using a cross-key equality proof anchored to `ConfidentialBalanceSpending`. Requires `ConfidentialBalanceInbox` to be canonical zero.
- `ConfidentialMPTHolderKeyUpdate` (transaction type 91): Rotates a holder's ElGamal key. Operates in two modes selected by transaction flag:
  - Rotation mode (`tfHolderKeyRotation`): holder re-encrypts `ConfidentialBalanceSpending` and `ConfidentialBalanceInbox` under the new key atomically.
  - Recovery mode (`tfHolderKeyRecovery`): holder has lost `sk_H`; registers new key as `RecoveryKey` for issuer-completed recovery.
- `ConfidentialMPTRecoverBalance` (transaction type 92): Completes holder key loss recovery by re-encrypting balances under the authorized new key. Submitted by the issuer.

### 4.3 Modified Ledger Entries

- `MPTokenIssuance`: Three new fields - `IssuerKeyEpoch`, `AuditorKeyEpoch`, `HolderCount`.
- `MPToken`: Three new fields - `IssuerKeyMirrorEpoch`, `AuditorKeyMirrorEpoch`, `RecoveryKey`.

### 4.4 APIs

TBD.

No new RPCs are anticipated, but the response schemas for `account_objects` and `ledger_data` are modified to surface new fields on `MPTokenIssuance` and `MPToken`. Open question: is a dedicated query needed to check migration status for an issuance (e.g. retrieve all holders where `IssuerKeyMirrorEpoch` < `IssuerKeyEpoch`)? Or is this out of scope for this amendment?

## 5. Protocol Overview

### 5.1 Key Rotation Model

**Issuer key rotation** proceeds in two phases. First, the issuer submits `MPTokenIssuanceSet` with a new `IssuerEncryptionKey`, incrementing `IssuerKeyEpoch`. After this transaction is accepted, all new issuer mirror delta ciphertexts must be encrypted under the new key. Second, the issuer submits `ConfidentialMPTMirrorUpdate` once per holder to re-encrypt each holder's issuer mirror under the new key.

Until a holder's mirror is migrated, confidential transactions for that holder are rejected. The underlying reason is cryptographic: in `ConfidentialMPTSend` and other transactions, the holder correctly reads the current `IssuerEncryptionKey` (`pk_I'`) from the issuance and constructs `IssuerEncryptedAmount` under it. However, the on-ledger accumulated `IssuerEncryptedBalance` is still under the old key (`pk_I`). Adding a delta under `pk_I'` to an accumulated balance under `pk_I` is cryptographically invalid - ciphertexts under different keys cannot be combined homomorphically.

The epoch check (`IssuerKeyMirrorEpoch < IssuerKeyEpoch`) makes this detectable cleanly:

- Validators use it to reject the transaction explicitly and early, before attempting an invalid homomorphic addition
- Wallet software uses it proactively - by comparing `IssuerKeyMirrorEpoch` on the holder's `MPToken` against `IssuerKeyEpoch` on `MPTokenIssuance`, the wallet knows the send will fail and can warn the holder and block submission before it reaches the network

`Auditor key rotation` follows the identical pattern using `AuditorEncryptionKey` and `AuditorKeyEpoch`.

**Auditor key late-registration by issuer** allows the issuer to register auditor key after the issuer key was already registered.

- Pre-`ConfidentialMPTKeyRotation` amendment: when registering the key for the auditor first time, it has to be registered together with the issuer key in `MPTokenIssuanceSet`. The issuer is not allowed to register issuer key in one transaction and later register auditor key in another transaction.
- Now with `ConfidentialMPTKeyRotation` amendment: with the issuer key already registered, the issuer can register the auditor key in a separate `MPTokenIssuanceSet` whenever they want to enable auditor.

**Holder self-migration** is available as an alternative to issuer-driven active re-encryption in all rotation scenarios. Rather than waiting for the issuer to submit `ConfidentialMPTMirrorUpdate`, any holder may self-migrate their issuer or auditor mirror by submitting `ConfidentialMPTMirrorUpdate` without a `Holder` field, using a cross-key equality proof anchored to their `ConfidentialBalanceSpending`. Prerequisites: `ConfidentialMPTMergeInbox` must be run first (inbox must be canonical zero), and the holder must have `sk_H`. See Section 9.9 for the full proof construction.

**Simultaneous issuer and auditor key rotation**: The issuer may rotate both `IssuerEncryptionKey` and `AuditorEncryptionKey` in a single `MPTokenIssuanceSet` transaction, though this is rare in practice. In this case, per-holder migration may be performed in a single `ConfidentialMPTMirrorUpdate` transaction with both `IssuerEncryptedAmount` and `AuditorEncryptedAmount` present. A single compact AND-composed Chaum-Pedersen equality proof covers both statements under one Fiat-Shamir challenge.

**Multiple successive rotations**: The issuer may rotate multiple times before completing migration. Holders with stale mirrors are blocked from transacting at the per-transaction level regardless of how many epochs behind they are. `ConfidentialMPTMirrorUpdate` bridges directly from the holder's current epoch to the latest epoch in one step. In issuer mode, this requires the issuer to retain the historical secret key corresponding to the epoch the holder is currently at - if that key has been destroyed, the holder must self-migrate by submitting `ConfidentialMPTMirrorUpdate` without a `Holder` field instead.

**Holder key rotation** is self-contained via `ConfidentialMPTHolderKeyUpdate` with `tfHolderKeyRotation`. No issuer involvement required.

**Holder key loss recovery** is a two-step process: the holder registers the new key on-chain via `ConfidentialMPTHolderKeyUpdate` with `tfHolderKeyRecovery`, then the issuer completes recovery via `ConfidentialMPTRecoverBalance`.

**Issuer key loss** is handled via holder-driven mirror reconstruction for both issuer and auditor mirrors. In the issuer key loss scenario, holder self-migration is the only path for issuer mirrors since the issuer cannot decrypt old mirrors without `sk_I`. For auditor mirrors, the issuer can still perform active re-encryption via the issuer mirror (`sk_I`) even when `sk_A` is lost - holder self-migration is an alternative but not the only path. See Section 12.

### 5.2 Re-encryption Strategy

Active re-encryption is the recommended strategy. The issuer submits `ConfidentialMPTMirrorUpdate` for all holders after rotating the key. The issuer is recommended to lock each holder's `MPToken` before submitting `ConfidentialMPTMirrorUpdate` and unlock after success. Note: this is a recommendation, not a requirement. The epoch staleness check already prevents the holder from successfully transacting with a stale mirror - the lock only prevents the holder from wasting fees on transactions that will be rejected. However, lock + `ConfidentialMPTMirrorUpdate` + unlock = 3 transactions per holder, tripling migration transaction volume at large holder counts. Issuers should weigh this cost against the UX benefit.

Prioritization for bulk migration:

1. Largest balances first - greatest value at risk if old key is compromised, and clawback is blocked until migrated.
2. Most active holders next - unblocks their confidential transactions soonest.
3. Regulatory-sensitive accounts - under specific compliance obligations.
4. Remaining inactive accounts - clawback remains blocked for these holders until migrated.

The issuer may rotate keys multiple times. Holders with stale mirrors are blocked from transacting at the per-transaction level regardless of how many epochs behind they are. See Section 13.1.

**Clawback and migration urgency**: Clawback is blocked for any unmigrated holder after key rotation - the issuer must complete `ConfidentialMPTMirrorUpdate` before executing `ConfidentialMPTClawback` for that holder.

**Historical key retention**: After multiple successive rotations, migrating a holder still at an old epoch requires the historical secret key for that epoch to decrypt their on-ledger mirror. If the issuer has destroyed a historical key before all holders at that epoch were migrated, those holders must fall back to self-migration (Section 9.9). Issuers should retain historical secret keys until all holders at each epoch are fully migrated.

### 5.3 Epoch Tracking and Migration Attestation

`IssuerKeyEpoch` and `AuditorKeyEpoch` on `MPTokenIssuance`, together with `IssuerKeyMirrorEpoch` and `AuditorKeyMirrorEpoch` on each `MPToken`, provide complete on-chain attestation of migration progress. Whether a holder's mirror is stale is trivially known on-ledger in O(1) - no off-ledger information required.

The `HolderCount` field on `MPTokenIssuance` provides the total number of holders with active confidential state, enabling issuers to track migration progress off-chain.

A holder who executes `ConfidentialMPTConvert` after a key rotation will have their `MPToken` initialized with ciphertexts under the current key and epoch fields set to the current epoch values. These holders are never stale - they start at the current epoch with no migration needed.

## 6. Ledger Entry: `MPTokenIssuance` (Modified)

The existing `MPTokenIssuance` ledger object is extended with three new fields. All other fields, flags, ownership, reserves, deletion conditions, and the object identifier are unchanged from XLS-0033.

### 6.1 New Fields

| Field Name        | Required? | JSON Type | Internal Type | Description                                                                                                                                                                                                                                                                                                                                                                                                                                      |
| :---------------- | :-------- | :-------- | :------------ | :----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `IssuerKeyEpoch`  | No        | `number`  | `UINT32`      | Monotonically increasing counter incremented on each issuer ElGamal key rotation. Not stored when at default value 0. Validators treat an absent field as epoch 0.                                                                                                                                                                                                                                                                               |
| `AuditorKeyEpoch` | No        | `number`  | `UINT32`      | Monotonically increasing counter incremented on each auditor ElGamal key rotation. Not stored when at default value 0. Validators treat an absent field as epoch 0.                                                                                                                                                                                                                                                                              |
| `HolderCount`     | No        | `number`  | `UINT64`      | The number of holders with initialized confidential state for this issuance. A holder is considered initialized once `HolderEncryptionKey` is registered on their `MPToken` via their first `ConfidentialMPTConvert`. `HolderCount` is incremented on that first conversion and is never decremented - `HolderEncryptionKey` is not removed by any existing transaction including `ConfidentialMPTClawback`. Not stored when at default value 0. |

**Note**: To accommodate existing `MPTokenIssuance` ledger objects that lack epoch fields even when keys are registered, the epoch value should remain absent after initial registration. It is set to 1 only when rotating a key for the first time successfully, and then increments with each subsequent rotation.

### 6.2 Flags

No new flags introduced.

### 6.3 Ownership

Unchanged from XLS-0033.

### 6.4 Reserves

No reserve requirement changes.

### 6.5 Deletion

Unchanged from XLS-0033.

### 6.6 Invariants

- I1: `IssuerKeyEpoch`, if present, must be ≥ 1.
- I2: `AuditorKeyEpoch`, if present, must be ≥ 1.
- I3: `IssuerEncryptionKey` must be present if `IssuerKeyEpoch` is present.
- I4: `AuditorEncryptionKey` must be present if `AuditorKeyEpoch` is present.

### 6.7 RPC Name

Unchanged from XLS-0033: mpt_issuance.

### 6.8 Example JSON

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
  "HolderCount": 42,
  "PreviousTxnID": "A1B2C3D4...",
  "PreviousTxnLgrSeq": 1234567
}
```

Before any key rotation (epoch fields absent):

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
  "HolderCount": 42,
  "PreviousTxnID": "A1B2C3D4...",
  "PreviousTxnLgrSeq": 1234567
}
```

## 7. Ledger Entry: `MPToken` (Modified)

The existing `MPToken` ledger object is extended with three new fields. All other fields, flags, ownership, reserves, and the object identifier are unchanged from XLS-0033.

### 7.1 New Fields

| Field Name              | Required? | JSON Type | Internal Type | Description                                                                                                                                                                                                                                                                                                                                                                                 |
| :---------------------- | :-------- | :-------- | :------------ | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `IssuerKeyMirrorEpoch`  | No        | `number`  | `UINT32`      | The `IssuerKeyEpoch` at which this holder's issuer mirror was last re-encrypted. Stale when `IssuerKeyMirrorEpoch` < `IssuerKeyEpoch` on `MPTokenIssuance`. Not stored when at default value 0.                                                                                                                                                                                             |
| `AuditorKeyMirrorEpoch` | No        | `number`  | `UINT32`      | The `AuditorKeyEpoch` at which this holder's auditor mirror was last re-encrypted. Stale when `AuditorKeyMirrorEpoch` < `AuditorKeyEpoch` on `MPTokenIssuance`. Not stored when at default value 0.                                                                                                                                                                                         |
| `RecoveryKey`           | No        | `string`  | `BLOB`        | A 33-byte compressed ElGamal public key authorized for key loss recovery. Set by `ConfidentialMPTHolderKeyUpdate` in recovery mode (`tfHolderKeyRecovery`). Cleared by exactly two paths: (1) `ConfidentialMPTRecoverBalance` when the issuer completes recovery; (2) `ConfidentialMPTHolderKeyUpdate` with `tfCancelRecovery` when the holder explicitly cancels. Has no automatic expiry. |

### 7.2 Flags

No new flags introduced.

### 7.3 Ownership

Unchanged from XLS-0033.

### 7.4 Reserves

No reserve requirement changes.

### 7.5 Deletion

Deletion conditions are unchanged from XLS-0033. The `MPToken` deletion question raised by `RecoveryKey` is a non-issue: per XLS-0096 Section 7.4, an `MPToken` cannot be deleted once confidential fields have been initialized, even if all balances contain canonical encrypted zero. Since `RecoveryKey` only appears on initialized `MPToken` objects (Invariant I8), an `MPToken` with `RecoveryKey` set can never be deleted. No new deletion concern is introduced by this amendment.

### 7.6 Invariants

- I5: `IssuerKeyMirrorEpoch`, if present, must be ≤ `IssuerKeyEpoch` on the parent `MPTokenIssuance` (treated as 0 if absent).
- I6: `AuditorKeyMirrorEpoch`, if present, must be ≤ `AuditorKeyEpoch` on the parent `MPTokenIssuance` (treated as 0 if absent).
- I7: `RecoveryKey`, if present, must be a well-formed compressed secp256k1 point (33 bytes) and must differ from the current `HolderEncryptionKey`.
- I8: `RecoveryKey` must not be present on an `MPToken` that has no `HolderEncryptionKey` registered. A holder initializes confidential state via their first `ConfidentialMPTConvert` (with `HolderEncryptionKey` present, MPTAmount may be zero). `RecoveryKey` is only meaningful for holders who have completed this initialization.

### 7.7 RPC Name

Unchanged from XLS-0033: mpt.

### 7.8 Example JSON

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

## 8. Transaction: `MPTokenIssuanceSet` (Modified)

The existing `MPTokenIssuanceSet` transaction is extended to allow replacement of `IssuerEncryptionKey` and `AuditorEncryptionKey` when already present. Some existing guards in preclaim must be relaxed:

1.  Key presence guard: The current implementation rejects updates to `IssuerEncryptionKey` and `AuditorEncryptionKey` once already present on the issuance object (`tecNO_PERMISSION`). This guard is relaxed to allow replacement when the field is already present. Key rotation does not reintroduce the vulnerability this guard was introduced to prevent - when rotating, the field already exists and every holder's `MPToken` already has the corresponding ciphertext column.
2.  `sfConfidentialOutstandingAmount` > 0 guard: The current implementation unconditionally rejects updates to `IssuerEncryptionKey` when `sfConfidentialOutstandingAmount` is already present (i.e. COA > 0). This guard must also be relaxed. Key rotation is only meaningful and necessary precisely when COA > 0 - if COA were zero, no holder would have a mirror yet and none of the migration logic would be needed. Maintaining this guard makes key rotation impossible in any real deployment.
3.  Pre-`ConfidentialMPTKeyRotation` amendment, an issuer cannot register an auditor key in `MPTokenIssuanceSet` unless the issuer key is being registered in the same transaction. This means
    the issuer can either register the issuer key alone or register both keys together initially. With the `ConfidentialMPTKeyRotation` amendment, the issuer can now register an auditor key at any time after the issuer key is already registered or rotated—allowing them to opt in whenever they want. The only constraint is that an auditor key cannot be registered before an issuer key.

The guard against adding `IssuerEncryptionKey` when `lsfMPTCanHoldConfidentialBalance` is not enabled remains unchanged - confidential transfers must be enabled before keys can be set or rotated.
All existing `MPTokenIssuanceSet` behavior (lock/unlock, `DomainID`) is completely unaffected.

### 8.1 Fields (Delta Only)

| Field Name             | Required? | JSON Type | Internal Type | Description                                                                                                                                                                                                   |
| ---------------------- | --------- | --------- | ------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `IssuerEncryptionKey`  | No        | string    | BLOB          | When present and already exists on the issuance, replaces the existing issuer ElGamal public key. Must be a well-formed compressed secp256k1 point (33 bytes). Must differ from the current on-ledger value.  |
| `AuditorEncryptionKey` | No        | string    | BLOB          | When present and already exists on the issuance, replaces the existing auditor ElGamal public key. Must be a well-formed compressed secp256k1 point (33 bytes). Must differ from the current on-ledger value. |

### 8.2 Flags

No new tf flags introduced.

### 8.3 Transaction Fee

10x base fee, consistent with XLS-0096 confidential transactions.

### 8.4 Failure Conditions (Delta Only)

#### 8.4.1 Data Verification

1. `IssuerEncryptionKey` is present but is not exactly 33 bytes or is not a well-formed compressed secp256k1 point. (`temMALFORMED`)
2. `AuditorEncryptionKey` is present but is not exactly 33 bytes or is not a well-formed compressed secp256k1 point. (`temMALFORMED`)

**Note**: Pre-`ConfidentialMPTKeyRotation` amendment: `AuditorEncryptionKey` is present without `IssuerEncryptionKey` returns `temMALFORMED`; Now it is allowed in preflight and will be further verified in preclaim.

#### 8.4.2 Protocol-Level Failures

1. `AuditorEncryptionKey` is being registered for the first time (not present on the issuance), but the issuance has no `IssuerEncryptionKey` and the current `MPTokenIssuanceSet` transaction does not provide one. (`tecNO_PERMISSION`)
2. `IssuerEncryptionKey` matches the current on-ledger value (no-op rotation). (`tecNO_PERMISSION`)
3. `AuditorEncryptionKey` matches the current on-ledger value (no-op rotation). (`tecNO_PERMISSION`)

### 8.5 State Changes (Delta Only)

When `IssuerEncryptionKey` is present and valid:

1. `IssuerEncryptionKey` on` MPTokenIssuance` ← new key value
2. `IssuerKeyEpoch` on `MPTokenIssuance` ← `IssuerKeyEpoch` + 1 (field created with value 1 if previously absent)

When `AuditorEncryptionKey` is present and valid:

1. `AuditorEncryptionKey` on `MPTokenIssuance` ← new key value
2. `AuditorKeyEpoch` on `MPTokenIssuance` ← `AuditorKeyEpoch` + 1 (field created with value 1 if previously absent)

### 8.6 Metadata Fields

No new metadata fields introduced. See Notes for Discussion D4.

### 8.7 Example JSON

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

## 9. Transaction: `ConfidentialMPTMirrorUpdate`

Re-encrypts a single holder's issuer and/or auditor mirror ciphertext under the new key after a key rotation. Submitted by the issuer once per holder per rotation. A holder may also self-migrate their issuer mirror - see Section 9.9.

### 9.1 Use Cases

- **Issuer key rotation migration**: Re-encrypt each holder's `IssuerEncryptedBalance` under the new `pk_I'`, restoring clawback authority and unblocking confidential transactions.
- **Auditor key rotation migration**: Re-encrypt each holder's `AuditorEncryptedBalance` under the new `pk_A'`, restoring regulatory visibility.
- **Simultaneous issuer and auditor rotation**: Both field sets may be present in the same transaction.
- **Holder self-migration (issuer key loss recovery)**: When the issuer has lost `sk_I` and cannot perform active re-encryption, the holder submits `ConfidentialMPTMirrorUpdate` with `tfHolderMirrorUpdate`. The holder decrypts their own `ConfidentialBalanceSpending` via sk_H to recover b, re-encrypts under the new issuer key `pk_I'`, and provides a cross-key equality proof. Requires `ConfidentialBalanceInbox` to be canonical zero - holder must run `ConfidentialMPTMergeInbox` first.

### 9.2 Fields

| Field Name               | Required? | JSON Type | Internal Type | Description                                                                                                                                                                                                                     |
| :----------------------- | :-------- | :-------- | :------------ | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `TransactionType`        | Yes       | `string`  | `UINT16`      | `ConfidentialMPTMirrorUpdate`, which is 90.                                                                                                                                                                                     |
| `Account`                | Yes       | `string`  | `ACCOUNTID`   | The issuer account.                                                                                                                                                                                                             |
| `MPTokenIssuanceID`      | Yes       | `string`  | `UINT192`     | The unique identifier of the MPT issuance.                                                                                                                                                                                      |
| `Holder`                 | Yes       | `string`  | `ACCOUNTID`   | The holder whose mirror(s) are being re-encrypted.                                                                                                                                                                              |
| `IssuerEncryptedAmount`  | No        | `string`  | `BLOB`        | A 66-byte ElGamal ciphertext encrypting the holder's balance under the new issuer key. Reuses `sfIssuerEncryptedAmount` from XLS-0096. Present to migrate holder's issuer mirror.                                               |
| `AuditorEncryptedAmount` | No        | `string`  | `BLOB`        | A 66-byte ElGamal ciphertext encrypting the holder's balance under the new auditor key. Reuses `sfAuditorEncryptedAmount` from XLS-0096. Present to migrate holder's auditor mirror.                                            |
| `ZKProof`                | Yes       | `string`  | `BLOB`        | A single compact Chaum-Pedersen equality proof proving the new ciphertext(s) encrypt the same value as the on-ledger mirror(s). When both fields are present, the proof covers both statements under one Fiat-Shamir challenge. |

**Mode determination**:

- **Issuer mode**: Holder field is present and `Account` != `Holder`. Transaction signed by issuer.
- **Holder mode**: Holder field is absent. Transaction signed by holder. Requires `ConfidentialBalanceInbox` == `EncZero` (run `ConfidentialMPTMergeInbox` first). Requires `sk_H`.
- `Account` == `Holder`: rejected (`temMALFORMED`)
- Holder absent and Account is issuer: rejected (`temMALFORMED`)
- Holder present and Account is holder (not issuer): rejected (`tecNO_PERMISSION`) - holder cannot migrate another holder's mirror

**Conditional field rules**:

- At least one of `IssuerEncryptedAmount` or `AuditorEncryptedAmount` must be present.
- The old ciphertext is not included - validators read it directly from on-ledger `MPToken` state.

### 9.3 Flags

See flags table above.

### 9.4 Transaction Fee

10x base fee, consistent with XLS-0096 confidential transactions.

### 9.5 Failure Conditions

#### 9.5.1 Data Verification

1. The `ConfidentialMPTKeyRotation` amendment is not enabled. (`temDISABLED`)
2. Neither `IssuerEncryptedAmount` nor `AuditorEncryptedAmount` is present. (`temMALFORMED`)
3. Issuer mode: Account is the same as Holder. (`temMALFORMED`)
4. Holder is absent and Account is the issuer account - the issuer cannot hold confidential balances. (`temMALFORMED`)
5. Any present `IssuerEncryptedAmount` or `AuditorEncryptedAmount` has an invalid length or represents an invalid elliptic curve point. (`temBAD_CIPHERTEXT`)
6. `ZKProof` length is not exactly the expected proof size for the detected mode. (TBD bytes - see Section 16) (`temMALFORMED`)

#### 9.5.2 Protocol-Level Failures

1. Issuer mode: the transaction is not signed by the issuer account for the specified `MPTokenIssuanceID`. (`tecNO_PERMISSION`)
2. Holder mode: Holder field is present and differs from Account - a holder cannot migrate another holder's mirror. (`tecNO_PERMISSION`)
3. The specified Holder account does not exist (issuer mode only). (`tecNO_TARGET`)
4. The `MPTokenIssuance` or the holder's `MPToken` object does not exist. (`tecOBJECT_NOT_FOUND`)
5. The issuance does not have the `lsfMPTCanHoldConfidentialBalance` flag set. (`tecNO_PERMISSION`)
6. The holder's `MPToken` has no confidential state initialized (missing `HolderEncryptionKey`). (`tecNO_PERMISSION`)
7. `IssuerEncryptedAmount` is present but `IssuerKeyMirrorEpoch` already equals current `IssuerKeyEpoch` (already migrated). (`tecNO_PERMISSION` or `tecDUPLICATE` - TBD)
8. `AuditorEncryptedAmount` is present but `AuditorKeyMirrorEpoch` already equals current `AuditorKeyEpoch` (already migrated). (`tecNO_PERMISSION` or `tecDUPLICATE` - TBD)
9. Holder mode: `ConfidentialBalanceInbox` is not canonical encrypted zero - holder must run `ConfidentialMPTMergeInbox` first. (`tecNO_PERMISSION`)
10. Holder mode: `IssuerEncryptionKey` (or `AuditorEncryptionKey`) is not present on the issuance - no rotation has occurred, nothing to self-migrate. (`tecNO_PERMISSION`)
11. Issuer mode: `ZKProof` fails the compact Chaum-Pedersen equality proof verification. (`tecBAD_PROOF`)
12. Holder mode: `ZKProof` fails the cross-key equality proof verification. (`tecBAD_PROOF`)

### 9.6 State Changes

When `IssuerEncryptedAmount` is present and valid:

1. `IssuerEncryptedBalance` on `MPToken` ← `IssuerEncryptedAmount`
2. `IssuerKeyMirrorEpoch` on `MPToken` ← current `IssuerKeyEpoch` on `MPTokenIssuance`

When `AuditorEncryptedAmount` is present and valid:

1. `AuditorEncryptedBalance` on `MPToken` ← `AuditorEncryptedAmount`
2. `AuditorKeyMirrorEpoch` on `MPToken` ← current `AuditorKeyEpoch` on `MPTokenIssuance`

`ConfidentialBalanceSpending`, `ConfidentialBalanceInbox`, `ConfidentialBalanceVersion`, and `HolderEncryptionKey` are unchanged.

### 9.7 Metadata Fields

No new metadata fields introduced. See Notes for Discussion D4.

### 9.8 Example JSON

Issuer mirror migration only:

```json
{
  "TransactionType": "ConfidentialMPTMirrorUpdate",
  "Account": "rIssuerAccountAddress",
  "MPTokenIssuanceID": "000000012A9F1D3C...",
  "Holder": "rHolderAccountAddress",
  "IssuerEncryptedAmount": "02a1b2c3d4e5f6...",
  "ZKProof": "03f1e2d3c4b5a6...",
  "Fee": "120",
  "Sequence": 43
}
```

Both mirrors in one transaction:

```json
{
  "TransactionType": "ConfidentialMPTMirrorUpdate",
  "Account": "rIssuerAccountAddress",
  "MPTokenIssuanceID": "000000012A9F1D3C...",
  "Holder": "rHolderAccountAddress",
  "IssuerEncryptedAmount": "02a1b2c3d4e5f6...",
  "AuditorEncryptedAmount": "02c3d4e5f6a7b8...",
  "ZKProof": "03a1b2c3d4e5f6...",
  "Fee": "120",
  "Sequence": 44
}
```

### 9.9 Holder Self-Migration of Issuer Mirror

In addition to the issuer-submitted path, a holder may self-migrate their issuer mirror using a cross-key equality proof. This is enabled by the protocol's equality proof guarantee: `ConfidentialBalanceSpending` always encodes the same balance b as the issuer mirror. The holder knows b by decrypting `ConfidentialBalanceSpending` via sk_H, and pk_I' is public on-ledger.

**Prerequisites**:

- The holder must first submit `ConfidentialMPTMergeInbox` before self-migrating. The issuer mirror encodes total balance b = b_s + b_in. The cross-key equality proof anchors to `ConfidentialBalanceSpending` which encodes only b_s. If `ConfidentialBalanceInbox` is non-zero, the proof would produce an incorrect issuer mirror. Validators enforce that `ConfidentialBalanceInbox` equals the canonical encrypted zero before accepting a holder-submitted mirror update.
- The proof must be bound to the current `ConfidentialBalanceVersion` via `TransactionContextID`.

**ZKP construction**: The holder proves knowledge of (b, sk_H, r') such that:

- `ConfidentialBalanceSpending` = Enc\_{pk_H}(b) via sk_H (decryption anchor)
- `IssuerEncryptedAmount` = Enc\_{pk_I'}(b) via fresh randomness r'
- pk_H = sk_H · G (key consistency)

Proof size: ~228 bytes (4 group elements + 3 scalars). This is particularly useful in the issuer key loss scenario (Section 12) where the issuer cannot perform active re-encryption (TBC)

## 10. Transaction: `ConfidentialMPTHolderKeyUpdate`

Allows a holder to rotate their ElGamal key (rotation mode) or authorize key replacement after key loss (recovery mode). Mode is selected by transaction flag.

### 10.1 Use Cases

- **Voluntary key rotation** (`tfHolderKeyRotation`): Holder decrypts `ConfidentialBalanceSpending` and `ConfidentialBalanceInbox`, re-encrypts under pk_H', submits equality proofs. Atomic - no issuer involvement. The holder may optionally run `ConfidentialMPTMergeInbox` before rotating - after merge, `ConfidentialBalanceInbox` is `EncZero` which is publicly verifiable under pk_H' without a ZKP, marginally reducing the proof size. This costs an extra transaction (See D10 for discussion on this.)
- **Key loss recovery authorization** (`tfHolderKeyRecovery`): Holder registers pk_H' as `RecoveryKey` on `MPToken`, consenting to issuer-completed recovery via `ConfidentialMPTRecoverBalance`.

### 10.2 Fields

| Field Name                    | Required? | JSON Type | Internal Type | Description                                                                                                                                                                                                               |
| :---------------------------- | :-------- | :-------- | :------------ | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `TransactionType`             | Yes       | `string`  | `UINT16`      | `ConfidentialMPTHolderKeyUpdate`, which is 91.                                                                                                                                                                            |
| `Account`                     | Yes       | `string`  | `ACCOUNTID`   | The holder account.                                                                                                                                                                                                       |
| `MPTokenIssuanceID`           | Yes       | `string`  | `UINT192`     | The unique identifier of the MPT issuance.                                                                                                                                                                                |
| `Flags`                       | Yes       | `number`  | `UINT32`      | Exactly one of `tfHolderKeyRotation` or `tfHolderKeyRecovery`                                                                                                                                                             |
| `HolderEncryptionKey`         | Yes       | `string`  | `BLOB`        | The holder's new 33-byte compressed ElGamal public key `pk_H'`. Must differ from current on-ledger value.                                                                                                                 |
| `ConfidentialBalanceSpending` | No        | `string`  | `BLOB`        | A 66-byte ElGamal ciphertext under pk_H'. **Required** in Rotation mode; **must be absent** in Recovery mode.                                                                                                             |
| `ConfidentialBalanceInbox`    | No        | `string`  | `BLOB`        | A 66-byte ElGamal ciphertext under pk_H'. **Required** in Rotation mode; **must be absent** in Recovery mode.                                                                                                             |
| `ZKProof`                     | Yes       | `string`  | `BLOB`        | **Rotation mode**: compact Chaum-Pedersen equality proof AND-composing spending and inbox equality statements plus Schnorr PoK for sk_H', under one Fiat-Shamir challenge. **Recovery mode**: Schnorr PoK for sk_H' only. |

### 10.3 Flags

| Flag Name             | Hex Value    | Decimal Value | Description                                                                                      |
| :-------------------- | :----------- | :------------ | :----------------------------------------------------------------------------------------------- |
| `tfHolderKeyRotation` | `0x00000001` | 1             | Rotation mode: re-encrypt the spending and inbox balances under the new key in this transaction. |
| `tfHolderKeyRecovery` | `0x00000002` | 2             | Recovery mode: register the new key as `sfRecoveryKey` for issuer-completed recovery.            |
| `tfCancelRecovery`    | `0x00000004` | 4             | Cancel mode: clear a pending `RecoveryKey` from the holder's `MPToken`.                          |

Exactly one of the three flags must be set.

### 10.4 Transaction Fee

10x base fee, consistent with XLS-0096 confidential transactions.

### 10.5 Failure Conditions

#### 10.5.1 Data Verification

1. The `ConfidentialMPTKeyRotation` amendment is not enabled. (`temDISABLED`)
2. Neither `tfHolderKeyRotation`, `tfHolderKeyRecovery`, nor `tfCancelRecovery` is set, or more than one is set. (`temINVALID_FLAG`)
3. Account is the issuer of `MPTokenIssuanceID` - the issuer cannot hold confidential balances. (`temMALFORMED`)
4. `HolderEncryptionKey` is not exactly 33 bytes. (`temMALFORMED`)
5. Rotation mode: `ConfidentialBalanceSpending` or `ConfidentialBalanceInbox` is missing. (`temMALFORMED`)
6. Recovery mode: `ConfidentialBalanceSpending` or `ConfidentialBalanceInbox` is present. (`temMALFORMED`)
7. Cancel mode: `HolderEncryptionKey` or `ZKProof` is present - cancel mode requires no additional fields beyond `TransactionType`, Account, `MPTokenIssuanceID`, and Flags. (`temMALFORMED`)
8. Any present `ConfidentialBalanceSpending` or `ConfidentialBalanceInbox` has an invalid length or represents an invalid elliptic curve point. (`temBAD_CIPHERTEXT`)
9. `ZKProof` is absent or its length is not exactly the expected size for the selected mode. (TBD bytes - see Section 16) (`temMALFORMED`)

#### 10.5.2 Protocol-Level Failures

1. The `MPTokenIssuance` or the holder's `MPToken` object does not exist. (`tecOBJECT_NOT_FOUND`)
2. The issuance does not have the `lsfMPTCanHoldConfidentialBalance` flag set. (`tecNO_PERMISSION`)
3. The holder's `MPToken` is missing confidential state (`HolderEncryptionKey`, `ConfidentialBalanceSpending`, or `ConfidentialBalanceInbox`). (`tecNO_PERMISSION`)
4. `HolderEncryptionKey` equals the current on-ledger `HolderEncryptionKey` (no-op). (`tecNO_PERMISSION`)
5. `IssuerKeyMirrorEpoch` < `IssuerKeyEpoch` - holder's issuer mirror is stale, must migrate before rotating. (`tecNO_PERMISSION`)
6. `AuditorKeyMirrorEpoch` < `AuditorKeyEpoch` - holder's auditor mirror is stale, must migrate before rotating (if auditor configured). (`tecNO_PERMISSION`)
7. `AuditorKeyMirrorEpoch` < `AuditorKeyEpoch` - holder's auditor mirror is stale, must migrate before rotating. (`tecNO_PERMISSION`)
8. Rotation mode: holder's `MPToken` has `ConfidentialBalanceFrozen` = true. See Notes for Discussion D7. (`tecNO_PERMISSION`)
9. Recovery mode: `RecoveryKey` is already set on the `MPToken` - a pending recovery authorization exists. (`tecNO_PERMISSION`)
10. Cancel mode: `RecoveryKey` is not set on the `MPToken` - nothing to cancel. (`tecNO_PERMISSION`)
11. `ZKProof` (Schnorr PoK) fails to verify against `HolderEncryptionKey`. (`tecBAD_PROOF`)
12. Rotation mode: `ZKProof` (compact Chaum-Pedersen equality proof) fails to verify. (`tecBAD_PROOF`)

**Cancel mode** (`tfCancelRecovery`): No additional fields are required beyond `TransactionType`, Account, `MPTokenIssuanceID`, and Flags. The transaction must be signed by the holder's XRPL signing key. No cryptographic proof is required - the holder's signing key signature is sufficient authorization to cancel their own pending recovery.

**Operational note**: This is a wallet-level concern - validators cannot detect in-flight transactions. When a `ConfidentialMPTSend` and a `ConfidentialMPTHolderKeyUpdate` (rotation) are submitted close together, both proofs are bound to `ConfidentialBalanceVersion` via `TransactionContextID`. Whichever transaction lands second will find the version has already incremented and will be rejected with `tecBAD_PROOF`. No funds are lost - just a rejected transaction requiring resubmission. To avoid this, wallet software should:

1. Check for pending (submitted but unconfirmed) `ConfidentialMPTSend` transactions before initiating rotation.
2. Queue rotation until all pending sends are confirmed in a closed ledger.
3. If using Tickets: cancel or consume all outstanding Tickets that would submit `ConfidentialMPTSend` before submitting the rotation Ticket. Standard Sequence numbers enforce ordering naturally; Tickets break this ordering and can cause sends and rotation to land in unpredictable order.

### 10.6 State Changes

**Rotation mode**:

1. `HolderEncryptionKey` on `MPToken` ← new key value
2. `ConfidentialBalanceSpending` on `MPToken` ← new ciphertext
3. `ConfidentialBalanceInbox` on `MPToken` ← new ciphertext
4. `ConfidentialBalanceVersion` on `MPToken` ← `ConfidentialBalanceVersion` + 1
5. `IssuerEncryptedBalance` and `AuditorEncryptedBalance` unchanged

**Recovery mode**:

1. `RecoveryKey` on `MPToken` ← `HolderEncryptionKey` (new value)
2. All other fields unchanged

**Cancel mode**:

1. `RecoveryKey` on `MPToken` ← cleared (field removed)
2. All other fields unchanged - `HolderEncryptionKey`, `ConfidentialBalanceSpending`, `ConfidentialBalanceInbox`, `ConfidentialBalanceVersion` are not modified

### 10.7 Metadata Fields

No new metadata fields introduced. See Notes for Discussion D4.

### 10.8 Example JSON

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

## 11. Transaction: `ConfidentialMPTRecoverBalance`

Completes holder key loss recovery. The issuer re-encrypts the holder's balance under the authorized `RecoveryKey` and submits a compact Chaum-Pedersen equality proof. Validators enforce that `RecoveryKey` is present - the issuer cannot act without prior holder authorization.

### 11.1 Fields

| Field Name                    | Required? | JSON Type | Internal Type | Description                                                                                                                                 |
| :---------------------------- | :-------- | :-------- | :------------ | :------------------------------------------------------------------------------------------------------------------------------------------ |
| `TransactionType`             | Yes       | `string`  | `UINT16`      | `ConfidentialMPTRecoverBalance`, which is 92.                                                                                               |
| `Account`                     | Yes       | `string`  | `ACCOUNTID`   | The issuer account.                                                                                                                         |
| `MPTokenIssuanceID`           | Yes       | `string`  | `UINT192`     | The unique identifier of the MPT issuance.                                                                                                  |
| `Holder`                      | Yes       | `string`  | `ACCOUNTID`   | The holder account being recovered.                                                                                                         |
| `ConfidentialBalanceSpending` | Yes       | `string`  | `BLOB`        | A 66-byte ElGamal ciphertext: the holder's total confidential balance re-encrypted under `RecoveryKey`. Becomes the new spending balance.   |
| `ZKProof`                     | Yes       | `string`  | `BLOB`        | Compact Chaum-Pedersen equality proof that `ConfidentialBalanceSpending` encrypts the same value as the on-ledger `IssuerEncryptedBalance`. |

**Note on** `ConfidentialBalanceInbox`: After recovery, `ConfidentialBalanceInbox` is reset to `EncZero`(pk_H'). No value is lost. The issuer mirror `IssuerEncryptedBalance` always reflects the holder's total confidential balance b = b_s + b_in - guaranteed by XLS-0096's equality proof invariant on every transaction. When the issuer completes `ConfidentialMPTRecoverBalance`, they decrypt the mirror to get the full b and re-encrypt it entirely into `ConfidentialBalanceSpending` under pk_H'. The inbox is reset to zero because the full balance - including what was in the inbox - is now consolidated into spending.

Additionally, any incoming confidential transfers that arrived in the inbox during the recovery window (between the holder's Step 1 authorization and the issuer's Step 2 completion) are also captured - incoming sends update `IssuerEncryptedBalance` homomorphically, so the issuer mirror at Step 2 already reflects those transfers. The holder effectively receives a free merge as part of recovery.

### 11.2 Flags

No new tf flags introduced.

### 11.3 Transaction Fee

10x base fee, consistent with XLS-0096 confidential transactions.

### 11.4 Failure Conditions

#### 11.4.1 Data Verification

1. The `ConfidentialMPTKeyRotation` amendment is not enabled. (`temDISABLED`)
2. Account is not the issuer of `MPTokenIssuanceID`. (`temMALFORMED`)
3. Account is the same as Holder. (`temMALFORMED`)
4. `ConfidentialBalanceSpending` has an invalid length or represents an invalid elliptic curve point. (`temBAD_CIPHERTEXT`)
5. `ZKProof` is absent or its length is not exactly the expected compact Chaum-Pedersen equality proof size. (TBD bytes - see Section 16) (`temMALFORMED`)

#### 11.4.2 Protocol-Level Failures

1. The specified Holder account does not exist. (`tecNO_TARGET`)
2. The `MPTokenIssuance` or the holder's `MPToken` object does not exist. (`tecOBJECT_NOT_FOUND`)
3. The issuance does not have the `lsfMPTCanHoldConfidentialBalance` flag set. (`tecNO_PERMISSION`)
4. The holder's `MPToken` has no pending `RecoveryKey` - holder has not authorized recovery. (`tecNO_PERMISSION`)
5. The holder's issuer mirror is stale (`IssuerKeyMirrorEpoch` < `IssuerKeyEpoch`) - the issuer must first migrate the mirror via `ConfidentialMPTMirrorUpdate` before recovery can proceed, so the proof can be verified against the current issuer key. (`tecNO_PERMISSION`)
6. `ZKProof` fails the compact Chaum-Pedersen equality verification against `IssuerEncryptedBalance` and `RecoveryKey`. (`tecBAD_PROOF`)

### 11.5 State Changes

1. `HolderEncryptionKey` on `MPToken` ← `RecoveryKey`
2. `ConfidentialBalanceSpending` on `MPToken` ← new ciphertext
3. `ConfidentialBalanceInbox` on `MPToken` ← `EncZero` (canonical encryption of zero under pk_H')
4. `ConfidentialBalanceVersion` on `MPToken` ← `ConfidentialBalanceVersion` + 1
5. `RecoveryKey` on `MPToken` ← cleared (field removed)
6. `IssuerEncryptedBalance` and `AuditorEncryptedBalance` unchanged

### 11.6 Metadata Fields

No new metadata fields introduced. See Notes for Discussion D4.

### 11.7 Example JSON

```json
{
  "TransactionType": "ConfidentialMPTRecoverBalance",
  "Account": "rIssuerAccountAddress",
  "MPTokenIssuanceID": "000000012A9F1D3C...",
  "Holder": "rHolderAccountAddress",
  "ConfidentialBalanceSpending": "02a1b2c3d4e5f6...",
  "ZKProof": "03f1e2d3c4b5a6...",
  "Fee": "120",
  "Sequence": 49
}
```

## 12. Clawback and Freeze Interactions with Key Rotation

### 12.1 Clawback

Per XLS-0096, `ConfidentialMPTClawback` burns the holder's confidential balance - it decreases both OA and COA permanently and requires a ZKP proving the issuer mirror encrypts the revealed amount, anchored to the on-ledger `IssuerEncryptedBalance`.

After issuer key rotation, `ConfidentialMPTClawback` verifies the ZKP against `sfIssuerEncryptionKey` on `MPTokenIssuance` - whichever key is currently recorded there, not a caller-selectable key. After rotation, `sfIssuerEncryptionKey` is pk_I'. An unmigrated holder's `IssuerEncryptedBalance` is still encrypted under pk_I (the old key), so the issuer's ZKP - which must use sk_I to prove against the old mirror - will fail verification against pk_I'.

Clawback is therefore blocked for unmigrated holders after key rotation. The issuer must first migrate the holder's mirror via `ConfidentialMPTMirrorUpdate` before executing clawback. There is no path to claw back an unmigrated holder using the old key after rotation.

This adds a new failure condition to `ConfidentialMPTClawback` (existing XLS-0096 transaction):

| Code               | Condition                                                                                                                                                        |
| :----------------- | :--------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `tecNO_PERMISSION` | Holder's `IssuerKeyMirrorEpoch` < `IssuerKeyEpoch` - mirror is stale. Issuer must migrate the holder's mirror via `ConfidentialMPTMirrorUpdate` before clawback. |

**Post-clawback state**: After a successful clawback, `IssuerEncryptedBalance` is reset to canonical encrypted zero, `IssuerKeyMirrorEpoch` is updated to the current `IssuerKeyEpoch`, and `HolderCount` on `MPTokenIssuance` is decremented.

**Issuer key loss and clawback**: If the issuer has lost sk_I, clawback is impossible for all holders - the required ZKP cannot be produced against pk_I' without sk_I', and the old mirrors cannot be migrated without sk_I. Clawback authority is restored progressively as holders self-migrate their mirrors under pk_I'. See Section 13.

### 12.2 Freeze

Per XLS-0096, freezing a holder sets `lsfMPTLocked` on their `MPToken`, blocking `ConfidentialMPTSend` and `ConfidentialMPTConvertBack` but not incoming transfers or `ConfidentialMPTMergeInbox`.

The following key rotation transactions interact with freeze status:

`ConfidentialMPTMirrorUpdate` while frozen: Permitted. The issuer is re-encrypting the mirror ciphertext, not enabling spending. Freeze status is unchanged.

`ConfidentialMPTHolderKeyUpdate` in rotation mode while frozen: Open Product question. See Notes for Discussion D7.

`ConfidentialMPTHolderKeyUpdate` in recovery mode while frozen: Permitted. The holder is registering `RecoveryKey` only - no balance is modified and no spending capability is granted.

`ConfidentialMPTRecoverBalance` while frozen: Permitted. The issuer is re-encrypting the holder's balance under the new key - no value is moved and freeze status remains in effect after recovery. The holder regains the ability to decrypt their balance but cannot spend until unfrozen.

## 13. Issuer Key Loss

### 13.1 Problem

The issuer has irrecoverably lost sk_I. They can no longer decrypt any holder's issuer mirror, execute clawbacks, or perform active mirror re-encryption. The XRPL signing key is unaffected.

### 13.2 Impact

- Clawback authority is lost for all holders. Per XLS-0096, `ConfidentialMPTClawback` verifies the ZKP against the current `sfIssuerEncryptionKey` on `MPTokenIssuance`. After registering a new pk_I', all holder mirrors are stale - clawback is blocked for every holder until their mirror is migrated. Without sk_I, the issuer cannot perform `ConfidentialMPTMirrorUpdate` to migrate mirrors, so clawback authority is suspended across the board.
- Active re-encryption of issuer mirrors is impossible - the issuer cannot decrypt old issuer mirrors without sk_I. Note: auditor mirror re-encryption is still possible since the issuer decrypts via the issuer mirror (sk_I), not the auditor mirror (sk_A). After registering a new pk_I', the issuer can still submit `ConfidentialMPTMirrorUpdate` (issuer mode) with auditor fields to re-encrypt auditor mirrors.
- Auditor key rotation is blocked - the issuer re-encrypts auditor mirrors via the issuer mirror, which they can no longer decrypt.

### 13.3 Recommended Approach: Loss Prevention

The primary recommendation is loss prevention through institutional key management:

- HSMs for key storage
- Shamir secret sharing of sk_I across custody providers
- Backup and recovery playbooks
- Same rigor applied to XRPL signing keys

### 13.4 Recovery Path: Holder-Driven Mirror Reconstruction

Issuer key loss creates an asymmetric situation analogous to holder key loss - the party who cannot act cryptographically requires the other party to complete the migration. The key difference from normal rotation is:

**Normal rotation (issuer driven)**:

- Issuer has sk_I and can decrypt all holder mirrors
- Issuer submits `ConfidentialMPTMirrorUpdate` (with Holder field) for each holder
- Holders are passive - no action required from them

**Issuer key loss (holder driven)**:

- Issuer has lost sk_I and cannot decrypt holder issuer mirrors
- Each holder must submit `ConfidentialMPTMirrorUpdate` (without Holder field) themselves
- Issuer is passive for issuer mirrors - only the holder can act
- Holders know b from decrypting `ConfidentialBalanceSpending` via sk_H and re-encrypt it under the new pk_I' using the cross-key equality proof (Section 9.9)

This is a one-step process per holder - unlike holder key loss recovery which requires two steps (holder authorizes, issuer completes). Here the holder acts alone with no issuer involvement needed for their mirror.

**How it works**:

1. Issuer registers new pk_I' via `MPTokenIssuanceSet` (they still have their XRPL signing key).
2. `IssuerKeyEpoch` increments.
3. Validators reject holder confidential transactions where `IssuerKeyMirrorEpoch` < `IssuerKeyEpoch`.
4. Each holder runs `ConfidentialMPTMergeInbox` first, then submits `ConfidentialMPTMirrorUpdate` without a Holder field with the cross-key equality proof to self-migrate their issuer mirror. Merge is required because the cross-key equality proof anchors to `ConfidentialBalanceSpending` which encodes only b_s - if `ConfidentialBalanceInbox` is non-zero, the new issuer mirror would encode b_s instead of the full b = b_s + b_in, producing a mirror that doesn't match the holder's actual total balance and breaking clawback correctness. Holders may also self-migrate their auditor mirror in the same transaction if needed.
5. Issuer regains clawback authority over each holder as their mirror is reconstructed.

**Limitation**: Inactive holders. Holders who do not transact will not self-migrate their issuer mirrors. The issuer cannot force-migrate issuer mirrors without sk_I. Clawback authority for these holders remains suspended until they act. Auditor mirrors for inactive holders can still be actively migrated by the issuer via sk_I' (the new issuer key), so auditor visibility is not permanently blocked for inactive holders in the issuer key loss scenario.

**Limitation**: Historical decryption. The issuer cannot decrypt historical ciphertexts from before the key loss.

### 13.5 Fallback: Inactive Holders

There is no clean on-chain fallback for inactive holders when the issuer has lost sk_I. The options are:

**Option 1**: Wait. Inactive holders will self-migrate when they next transact confidentially - they will hit the epoch staleness check and be prompted to submit `ConfidentialMPTMirrorUpdate`. The issuer regains clawback authority progressively as holders act.

**Option 2**: Off-chain communication. The issuer contacts inactive holders off-chain to prompt them to self-migrate. No protocol changes needed.

**Option 3**: Accept permanent suspension. For holders who remain permanently inactive, the issuer's clawback authority over those specific holders is permanently suspended. The issuer can still claw back active holders whose mirrors are reconstructed.

Note: `ConfidentialMPTConvertBack` is not a viable fallback here. It requires the holder to have sk_H to produce the required ZKP - active holders with sk_H already have a better path via Section 12.4 self-migration without publicly revealing their balance. And inactive holders who will not self-migrate are equally unlikely to voluntarily convert back to public. `ConfidentialMPTClawback` is also unavailable without sk_I.

## 14. Operational Considerations

### 14.1 Epoch Staleness as a Mandatory Validation Check

Epoch consistency is a mandatory validation step for every confidential transaction that touches the issuer or auditor mirror. After key rotation, the on-ledger `IssuerEncryptedBalance` (or `AuditorEncryptedBalance`) is under the old key while any new transaction delta is under the new key. These cannot be combined homomorphically - ciphertexts under different keys cannot be added. The epoch check makes this detectable and actionable: validators reject stale-mirror transactions cleanly rather than failing at the cryptographic combination step, and wallet software can proactively detect staleness by comparing `IssuerKeyMirrorEpoch` on the holder's `MPToken` against `IssuerKeyEpoch` on `MPTokenIssuance` (and similarly for auditor) before constructing or submitting transactions.

Validators must check both `IssuerKeyMirrorEpoch` == `IssuerKeyEpoch` and `AuditorKeyMirrorEpoch` == `AuditorKeyEpoch` (treating absent as 0) before processing the following existing XLS-0096 transactions:

| Transaction                  | Failure Code       | Condition                                                                                               |
| :--------------------------- | :----------------- | :------------------------------------------------------------------------------------------------------ |
| `ConfidentialMPTSend`        | `tecNO_PERMISSION` | Sender's `IssuerKeyMirrorEpoch` < `IssuerKeyEpoch` - issuer mirror is stale.                            |
| `ConfidentialMPTSend`        | `tecNO_PERMISSION` | Sender's `AuditorKeyMirrorEpoch` < `AuditorKeyEpoch` - auditor mirror is stale (if auditor configured). |
| `ConfidentialMPTConvert`     | `tecNO_PERMISSION` | Holder's `IssuerKeyMirrorEpoch` < `IssuerKeyEpoch` - issuer mirror is stale.                            |
| `ConfidentialMPTConvert`     | `tecNO_PERMISSION` | Holder's `AuditorKeyMirrorEpoch` < `AuditorKeyEpoch` - auditor mirror is stale (if auditor configured). |
| `ConfidentialMPTConvertBack` | `tecNO_PERMISSION` | Holder's `IssuerKeyMirrorEpoch` < `IssuerKeyEpoch` - issuer mirror is stale.                            |
| `ConfidentialMPTConvertBack` | `tecNO_PERMISSION` | Holder's `AuditorKeyMirrorEpoch` < `AuditorKeyEpoch` - auditor mirror is stale (if auditor configured). |

The holder must wait for the issuer to submit `ConfidentialMPTMirrorUpdate` - or self-migrate via the cross-key equality proof (Section 9.9) - before they can transact confidentially.

### 14.2 Migration Throughput

Each `ConfidentialMPTMirrorUpdate` carries a new mirror ciphertext (~66 bytes) and a compact Chaum-Pedersen equality proof. Fees are 10x base fee. The `HolderCount` field on `MPTokenIssuance` allows issuers to determine the total migration scope off-chain.

### 14.3 Wallet Implementation Guidance

Wallet software implementing `ConfidentialMPTHolderKeyUpdate` in rotation mode must:

1. Verify no `ConfidentialMPTSend` transactions are pending before initiating rotation.
2. Surface a warning if pending sends exist - the `ConfidentialBalanceVersion` bump will invalidate their proofs.
3. Queue rotation until all pending sends are confirmed in a closed ledger.
4. Ensure all outstanding Tickets referencing `ConfidentialBalanceSpending` are consumed or cancelled before submitting rotation.

**If this check is missed**: There is no ambiguous state and no funds are at risk. The outcome depends on which transaction lands first:

- **Rotation lands first**: The in-flight send's proof is bound to the old `ConfidentialBalanceVersion` and is rejected with `tecBAD_PROOF`. The holder's full balance is intact under pk_H'. The holder reconstructs the send proof under the new key and resubmits.
- **Send lands first**: `ConfidentialBalanceVersion` bumps and `ConfidentialBalanceSpending` is debited normally. The rotation proof - constructed against the old version - is rejected with `tecBAD_PROOF`. The holder reconstructs the rotation proof against the updated state and resubmits.

In both cases the result is a cleanly rejected transaction requiring resubmission - not a partial or ambiguous state. Clawback is unaffected in either scenario: `ConfidentialMPTClawback` uses `IssuerEncryptedBalance` (the issuer mirror), not `ConfidentialBalanceSpending` or `ConfidentialBalanceVersion`. The operational note is a UX concern, not a safety concern.

### 14.4 Issuer Recovery Request Detection

After a holder submits `ConfidentialMPTHolderKeyUpdate` with `tfHolderKeyRecovery`, `RecoveryKey` is set on their `MPToken`. The issuer needs to detect this to submit `ConfidentialMPTRecoverBalance` promptly. Two complementary mechanisms are recommended:

**Option 1: Real-time WebSocket subscription**

The issuer subscribes to the XRPL WebSocket API and listens for `ConfidentialMPTHolderKeyUpdate` transactions with `tfHolderKeyRecovery` flag set. When one arrives, the issuer is notified in real-time and can immediately prepare and submit `ConfidentialMPTRecoverBalance`. Clio is optimized for WebSocket API calls for validated ledger data and supports transaction stream subscriptions.

**Option 2: Periodic Clio query (catch-up mechanism)**

As a reliability backstop for missed WebSocket events (e.g. connection drops), the issuer periodically queries Clio using the `mpt_holders` method to retrieve all the holders and their `MPToken` indexes, then filters client-side for those with `RecoveryKey` present. No new Clio API changes are required - `RecoveryKey` will be included in `MPToken` object responses once this amendment is implemented.

```json
{
  "command": "account_objects",
  "account": "rIssuerAccountAddress",
  "type": "mpt",
  "mpt_issuance_id": "000000012A9F1D3C..."
}
```

The issuer filters the response for `MPToken` objects containing a `RecoveryKey` field.

**Recommended approach**: Both mechanisms together. Option 1 for real-time processing of recovery requests; Option 3 as a periodic catch-up to handle any events missed during WebSocket downtime. The polling interval for Option 3 can be tuned based on the issuer's SLA for recovery completion.

**No protocol changes required**. Both mechanisms use existing XRPL and Clio infrastructure. This is purely an operational implementation concern for issuers.

### 14.5 Regulatory Verification

A regulator (or any observer) can verify migration completion by comparing `IssuerKeyEpoch` on `MPTokenIssuance` against `IssuerKeyMirrorEpoch` on each `MPToken`. `HolderCount` provides the total number of holders to check.

### 14.6 Ledger Replay Integrity

Each XRPL ledger version is a complete, immutable snapshot including `IssuerEncryptionKey` as it was at that moment. When replaying a historical transaction from before a key rotation, the replaying node uses the `MPTokenIssuance` state from that exact ledger version - preserving the old key. This is identical to how signing key rotation works on XRPL.

### 14.7 Interaction with Existing XLS-0096 Transactions

After issuer key rotation, `ConfidentialMPTConvert`, `ConfidentialMPTSend`, and `ConfidentialMPTConvertBack` must use the new pk_I' for issuer mirror ciphertexts. Clients that read the current key from the issuance object will naturally use the new key.

For `ConfidentialMPTClawback`: the issuer must use sk_I' for holders whose mirror has been migrated. For unmigrated holders, the issuer may use sk_I (old key) to claw back under the old mirror, or migrate first.

`ConfidentialMPTConvert` must initialize `IssuerKeyMirrorEpoch` and `AuditorKeyMirrorEpoch` to the current epoch values when creating a new `MPToken`. It must also increment `HolderCount` on `MPTokenIssuance` when `HolderEncryptionKey` is being registered for the first time - i.e. when the transaction includes `HolderEncryptionKey` and the holder's `MPToken` does not yet have one registered. Subsequent `ConfidentialMPTConvert` calls for an already-initialized holder do not affect `HolderCount`. No other existing XLS-0096 transactions modify `HolderCount`.

## 15. Security Considerations

### 15.1 Key Compromise vs. Key Loss

**Key compromise** - attacker has the key, legitimate holder still does. Attacker retains read access until re-encryption is complete. Rotation is the remediation.

**Key loss** - legitimate holder no longer has the key. Recovery paths require counterparty involvement. Loss prevention is the primary recommendation.

### 15.2 No New Cryptographic Assumptions

All constructions reuse existing XLS-0096 primitives: compact Chaum-Pedersen equality proofs, Schnorr proofs of knowledge, Bulletproofs. No new cryptographic assumptions introduced.

### 15.3 Issuer Visibility During Re-encryption

The decrypt-then-re-encrypt approach requires the issuer to learn b. This is inherent and consistent with the issuer's existing visibility via the mirror ciphertext in XLS-0096. No new privacy exposure introduced.

### 15.4 No Schnorr PoK for Issuer and Auditor Key Rotation

Consistent with XLS-0096's existing behavior for initial key setting. A rogue issuer key only harms the issuer's own mirror and clawback capability.

### 15.5 `ConfidentialBalanceVersion` Increment on Holder Key Rotation

`ConfidentialMPTHolderKeyUpdate` in rotation mode increments `ConfidentialBalanceVersion`, invalidating in-flight `ConfidentialMPTSend` proofs. See Section 13.3.

### 15.6 Two-Step Recovery Authorization

The holder's authorization (`tfHolderKeyRecovery`) is signed by the holder's XRPL signing key. Validators enforce that `RecoveryKey` is present before accepting `ConfidentialMPTRecoverBalance`. The issuer cannot act unilaterally.

### 15.7 `RecoveryKey` Liveness Concern

If the issuer never completes recovery, the holder remains locked out indefinitely. See Notes for Discussion D1. Per XLS-0096, clawback burns tokens rather than returning them - this is not a viable workaround.

### 15.8 Issuer Key Loss and Clawback Authority

After key rotation, clawback is blocked for any holder whose `IssuerKeyMirrorEpoch` < `IssuerKeyEpoch` - the ZKP is verified against the current `sfIssuerEncryptionKey`, not a caller-selectable key. Loss of sk_I therefore suspends clawback authority for all holders - without sk_I the issuer cannot migrate mirrors, and without migrated mirrors clawback cannot proceed. Authority is restored progressively as holders self-migrate their mirrors under pk_I'.

### 15.9 Successive Rotations and Historical Key Retention

The protocol does not enforce a global gate preventing successive rotations before migration is complete. Per-transaction staleness checks (`IssuerKeyMirrorEpoch` < `IssuerKeyEpoch`) enforce correctness at the point of use for each individual holder, regardless of how many epochs behind they are.

An operational security consideration: after multiple successive rotations, migrating a holder still at an old epoch requires the historical secret key for that epoch. If an issuer destroys a historical secret key before all holders at that epoch are migrated (e.g. during an emergency rotation due to compromise), those holders cannot be actively migrated and must fall back to self-migration (Section 9.9). Issuers should retain historical secret keys until all holders at each epoch are fully migrated.

### 15.10 Holder Self-Migration Security

For holder self-migration (Section 9.9), validators must enforce:

- `ConfidentialBalanceInbox` equals canonical encrypted zero before accepting the transaction.
- Proof is bound to the current `ConfidentialBalanceVersion` via `TransactionContextID`.
- `IssuerEncryptedAmount` is verifiable under the current `IssuerEncryptionKey` from `MPTokenIssuance`.

### 15.11 Seed-Derived ElGamal Keys

Wallets may derive ElGamal keys from the XRPL account seed. This eliminates key loss for standard single-signature accounts but does not solve key compromise. Multi-sig accounts cannot use seed derivation. See Appendix A.

## 16. Analysis of Transaction Cost and Performance

### 16.1 Cryptographic Proof Summary

| Transaction                      | Mode                  | Proof Type                                              | Approximate Size |
| :------------------------------- | :-------------------- | :------------------------------------------------------ | :--------------- |
| `MPTokenIssuanceSet` (rotation)  |                       | None                                                    | 0 bytes          |
| `ConfidentialMPTMirrorUpdate`    | Issuer, one mirror    | Compact Chaum-Pedersen equality                         | ~128 bytes       |
| `ConfidentialMPTMirrorUpdate`    | Issuer, both mirrors  | Compact Chaum-Pedersen (AND-composed)                   | ~196 bytes       |
| `ConfidentialMPTMirrorUpdate`    | Holder self-migration | Cross-key equality proof                                | ~228 bytes       |
| `ConfidentialMPTHolderKeyUpdate` | Rotation              | Compact Chaum-Pedersen (spending + inbox) + Schnorr PoK | ~457 bytes       |
| `ConfidentialMPTHolderKeyUpdate` | Recovery              | Schnorr PoK                                             | 65 bytes         |
| `ConfidentialMPTRecoverBalance`  |                       | Chaum-Pedersen equality                                 | ~196 bytes       |

All new transactions are charged 10x the base fee, consistent with XLS-0096.

## 17. Permissions

Per XLS-0074 (Granular Account Permissions), an account can grant another account permission to submit specific transaction types on its behalf. This amendment introduces new delegatable permissions.

### 17.1 Issuer-Side Delegation

**`ConfidentialMPTMirrorUpdate`**

At large holder counts, the issuer may want to delegate bulk mirror re-encryption to a separate operational account without granting full `MPTokenIssuanceSet` authority. A bulk migration operator should not be able to rotate keys, lock or unlock holder balances, or modify other issuance properties.

Proposed permission: `ConfidentialMPTMirrorUpdate` is independently delegatable under XLS-0074.

**`ConfidentialMPTRecoverBalance`**

The issuer may want a dedicated recovery operations account that can complete holder key loss recovery without full issuer authority.

Proposed permission: `ConfidentialMPTRecoverBalance` is independently delegatable under XLS-0074.

Whether these two permissions should be separately delegatable or combined into a single issuer operational permission is an open question. See Notes for Discussion D9.

`MPTokenIssuanceSet` (key rotation) uses the existing `MPTokenIssuanceSet` permission under XLS-0074. Key rotation must always be submitted by the primary issuer account or an account explicitly granted `MPTokenIssuanceSet` authority.

### 17.2 Holder-Side Delegation

**`ConfidentialMPTHolderKeyUpdate`** - Rotation Mode

A custody provider may want to submit key rotation on behalf of the holder. Rotation mode requires sk_H to construct the equality proofs - if the custody provider constructs the proofs, they have access to sk_H by definition. Granting them signing authority is not a meaningful additional security risk.

Proposed permission: `ConfidentialMPTHolderKeyUpdate` rotation mode is delegatable under XLS-0074.

**`ConfidentialMPTHolderKeyUpdate`** - Recovery Mode

Recovery mode is more sensitive - it sets `RecoveryKey` on the holder's `MPToken`, effectively authorizing key replacement. Unlike rotation mode, recovery mode does not require sk_H. Delegation therefore grants meaningful additional authority. Whether recovery mode should be delegatable is an open question. See Notes for Discussion D8.

### 17.3 Permission Summary

| Transaction                                      | Permission Name                          | Delegatable?                | Notes                                                                                                                         |
| :----------------------------------------------- | :--------------------------------------- | :-------------------------- | :---------------------------------------------------------------------------------------------------------------------------- |
| `MPTokenIssuanceSet` (key rotation)              | Existing `MPTokenIssuanceSet` permission | Per XLS-0074 existing rules | Key rotation uses same permission as all other `MPTokenIssuanceSet` operations                                                |
| `ConfidentialMPTMirrorUpdate` (issuer mode)      | `ConfidentialMPTMirrorUpdate`            | Yes                         | Grants bulk migration authority without `MPTokenIssuanceSet` authority                                                        |
| `ConfidentialMPTMirrorUpdate` (holder mode)      | N/A - holder self-migration              | Holder signs directly       | No delegation needed                                                                                                          |
| `ConfidentialMPTHolderKeyUpdate` (rotation mode) | `ConfidentialMPTHolderKeyUpdate`         | Yes                         | Custody provider use case                                                                                                     |
| `ConfidentialMPTHolderKeyUpdate` (recovery mode) | TBD                                      | TBD - see D8                | Sensitive operation                                                                                                           |
| `ConfidentialMPTRecoverBalance`                  | `ConfidentialMPTRecoverBalance`          | Yes                         | Grants recovery completion authority without full issuer authority; granularity vs `ConfidentialMPTMirrorUpdate` TBD - see D9 |

## 18. Rationale

### 18.1 Reuse of Existing Transaction Types for Key Rotation

Issuer and auditor key rotation reuse `MPTokenIssuanceSet`. Two existing preclaim guards must be relaxed:

- **Key presence guard**: Relaxed to allow replacement of an already-present key. Key rotation does not reintroduce the vulnerability that guard prevents - when rotating, the field already exists and every `MPToken` already has the corresponding ciphertext column.
- **`sfConfidentialOutstandingAmount` > 0 guard**: Also relaxed. This guard unconditionally rejects key updates when COA > 0. Key rotation is only meaningful precisely when COA > 0 - if COA were zero, no holder would have a mirror yet. Maintaining this guard makes key rotation impossible in any real deployment.

### 18.2 Decrypt-then-Re-encrypt over Proxy Re-encryption

Standard PRE constructions require bilinear pairings, incompatible with secp256k1. PRE also introduces new trust assumptions. Decrypt-then-re-encrypt uses existing primitives and the issuer already has visibility by design.

### 18.3 Active Re-encryption over Lazy Re-encryption

After issuer key rotation, two capabilities are blocked for unmigrated holders: confidential transactions (old and new key ciphertexts cannot be combined homomorphically) and clawback (ZKP verified against current `sfIssuerEncryptionKey`, not a caller-selectable key). Active re-encryption keeps restoration of both capabilities entirely under the issuer's control. The issuer may rotate multiple times without waiting for full migration - per-transaction staleness checks enforce correctness at the point of use.

### 18.4 Single `ConfidentialMPTMirrorUpdate` for Both Mirrors

Avoids a new transaction type while keeping fields explicitly named and independently optional.

### 18.5 Old Ciphertext Omitted

Validators read the old ciphertext directly from on-ledger `MPToken` state. Retransmitting is redundant.

### 18.6 Explicit Flags for Mode Detection in `ConfidentialMPTHolderKeyUpdate`

`tfHolderKeyRotation` / `tfHolderKeyRecovery` / `tfCancelRecovery` make validator logic unambiguous, eliminate edge cases with partial field sets, and align with XRPL's existing convention. This was chosen over inferring mode from field presence/absence.

### 18.7 Reuse of Existing SFields in `ConfidentialMPTMirrorUpdate`

`ConfidentialMPTMirrorUpdate` reuses the existing `sfIssuerEncryptedAmount` and `sfAuditorEncryptedAmount` fields from XLS-0096 rather than defining new fields. Field reuse across transaction types with context-specific semantics is standard XRPL practice - `sfAmount`, `sfDestination`, and many other fields carry transaction-type-specific meanings. No new serialized field definitions are required.

### 18.8 Mode Detection in `ConfidentialMPTMirrorUpdate`

`ConfidentialMPTMirrorUpdate` uses the `MPTokenAuthorize` pattern for mode detection - the Holder field presence distinguishes issuer mode (present) from holder mode (absent). This is consistent with XLS-0033's `MPTokenAuthorize` which uses field presence to distinguish holder vs issuer submission paths.

## 19. Backwards Compatibility

This amendment introduces no backwards incompatibilities. Existing `MPTokenIssuance` and `MPToken` objects require no migration. New fields are not stored when at their default value and their absence is well-defined. The relaxation of the `MPTokenIssuanceSet` preclaim guard is additive - previously accepted transactions continue to be accepted unchanged.

## 20. Test Plan

### 20.1 `MPTokenIssuanceSet` - Key Rotation

- Issuer successfully rotates `IssuerEncryptionKey`; `IssuerKeyEpoch` increments.
- Auditor successfully rotates `AuditorEncryptionKey`; `AuditorKeyEpoch` increments.
- Both keys rotated in the same transaction.
- Rotation rejected if new key matches current value (no-op).
- Rotation rejected if new key is malformed.
- Rotation rejected if not signed by issuer.
- Rotation rejected if field not already present (initial late addition guard unchanged).
- Multiple successive rotations supported - holders migrated directly from any old epoch to current epoch.
- `IssuerKeyEpoch` created with value 1 on first rotation (previously absent).

### 20.2 `ConfidentialMPTMirrorUpdate`

- Issuer successfully migrates holder issuer mirror; `IssuerKeyMirrorEpoch` updated.
- Issuer successfully migrates holder auditor mirror; `AuditorKeyMirrorEpoch` updated.
- Both mirrors migrated in single transaction.
- Rejected if neither field set present.
- Rejected if new ciphertext is malformed.
- Rejected if ZKP fails.
- Rejected if holder already migrated.
- Rejected if not signed by issuer.
- `ConfidentialBalanceSpending`, `ConfidentialBalanceInbox`, `ConfidentialBalanceVersion`, `HolderEncryptionKey` unchanged.
- Holder self-migration: succeeds after `ConfidentialMPTMergeInbox`; rejected if inbox is non-zero.

### 20.3 `ConfidentialMPTHolderKeyUpdate` - Rotation Mode

- Holder successfully rotates key; all balance fields updated, `ConfidentialBalanceVersion` incremented.
- Rejected if new key matches current value.
- Rejected if Schnorr PoK fails.
- Rejected if compact Chaum-Pedersen proof fails.
- Rejected if holder's `IssuerKeyMirrorEpoch` is stale.
- `IssuerEncryptedBalance` and `AuditorEncryptedBalance` unchanged.
- In-flight send proofs bound to old `ConfidentialBalanceVersion` rejected after rotation.

### 20.4 `ConfidentialMPTHolderKeyUpdate` - Recovery Mode

- Holder successfully sets `RecoveryKey`.
- Rejected if both flags set or neither set.
- Rejected if ciphertext fields present.
- Rejected if `RecoveryKey` already set.
- Rejected if Schnorr PoK fails.
- `HolderEncryptionKey`, `ConfidentialBalanceSpending`, `ConfidentialBalanceInbox`, `ConfidentialBalanceVersion` unchanged.

### 20.5 `ConfidentialMPTRecoverBalance`

- Issuer successfully completes recovery; all fields updated correctly, `RecoveryKey` cleared.
- Rejected if `RecoveryKey` not set.
- Rejected if holder's issuer mirror is stale.
- Rejected if ZKP fails.
- Rejected if not signed by issuer.
- `IssuerEncryptedBalance` and `AuditorEncryptedBalance` unchanged.

### 20.6 Epoch Staleness Checks on Existing XLS-0096 Transactions

- `ConfidentialMPTSend` rejected with `tecNO_PERMISSION` if sender's `IssuerKeyMirrorEpoch` < `IssuerKeyEpoch`.
- `ConfidentialMPTSend` rejected with `tecNO_PERMISSION` if sender's `AuditorKeyMirrorEpoch` < `AuditorKeyEpoch` (if auditor configured).
- `ConfidentialMPTConvert` rejected with `tecNO_PERMISSION` if holder's `IssuerKeyMirrorEpoch` < `IssuerKeyEpoch`.
- `ConfidentialMPTConvert` rejected with `tecNO_PERMISSION` if holder's `AuditorKeyMirrorEpoch` < `AuditorKeyEpoch` (if auditor configured).
- `ConfidentialMPTConvertBack` rejected with `tecNO_PERMISSION` if holder's `IssuerKeyMirrorEpoch` < `IssuerKeyEpoch`.
- `ConfidentialMPTConvertBack` rejected with `tecNO_PERMISSION` if holder's `AuditorKeyMirrorEpoch` < `AuditorKeyEpoch` (if auditor configured).
- All three succeed once mirrors are migrated.

### 20.7 End-to-End Scenarios

- Full issuer key rotation cycle: Rotate → migrate all holders → verify all `IssuerKeyMirrorEpoch` match `IssuerKeyEpoch` → confirm holders can transact.
- Full auditor key rotation cycle: Same pattern for auditor.
- Holder voluntary key rotation: Rotate → confirm new key decrypts → confirm holder can send.
- Holder key loss recovery: Recovery authorization → issuer completes → holder can decrypt and spend.
- Issuer key loss: Register new key → holders self-migrate → issuer regains clawback authority progressively.
- Clawback after partial migration: Both migrated and unmigrated holder scenarios.
- Simultaneous issuer and auditor rotation: Both keys rotated → both mirror sets migrated → all epoch fields consistent.

### 20.8 Regression - Existing XLS-0096 Transactions

- `ConfidentialMPTSend` after rotation uses new pk_I' automatically.
- `ConfidentialMPTConvert` for new holder after rotation initializes epoch fields to current values and increments `HolderCount`.
- Existing `MPTokenIssuanceSet` behavior unaffected.

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

## Appendix B: Design Discussion

### B.1 Lazy vs. Active Re-encryption

Rejected. After issuer key rotation, old and new key ciphertexts cannot be combined homomorphically. Holders cannot transact until their mirror is migrated, making active re-encryption the only viable path.

### B.2 Holder Self-Migration as Foundation for Issuer Key Loss Recovery

The protocol's equality proof guarantee means the holder always knows b from sk_H. This enables the cross-key equality proof construction that is the basis for both Section 9.9 and Section 12.4.

### B.3 Why Holder-Driven Recovery Requires Issuer On-Chain Involvement

The holder cannot re-encrypt balances without sk_I. Knowing b in plaintext is not sufficient - the ZKP requires sk_I to produce a proof anchored to `IssuerEncryptedBalance`. The source of b off-chain (issuer, auditor, or anyone else) does not matter - the cryptographic constraint is the same.

### B.4 Clawback Semantics Under XLS-0096

Per XLS-0096, `ConfidentialMPTClawback` burns the holder's balance (decreases both OA and COA permanently) rather than crediting the issuer's public reserve. This means clawback + re-issuance is not a symmetric recovery path - it permanently destroys tokens. The two-step recovery design is strongly preferred.

### B.5 Explicit Flags vs. Field Presence for Mode Detection

Explicit flags (`tfHolderKeyRotation` / `tfHolderKeyRecovery`) make validator logic unambiguous, eliminate edge cases with partial field sets, and align with XRPL's existing convention. This was chosen over inferring mode from field presence/absence.

## Appendix C: FAQ

### C.1: Why can't I use my XRPL signing key to recover my ElGamal key?

The keys are cryptographically independent - no derivation path exists from one to the other. See Appendix A for a wallet convention that eliminates this problem for standard single-signature accounts.

### C.2: What happens if I lose my ElGamal key?

You cannot decrypt or spend your confidential balances, but your XRPL signing key is unaffected. Submit `ConfidentialMPTHolderKeyUpdate` with `tfHolderKeyRecovery` to register a new key, then wait for the issuer to complete recovery. This directly addresses XLS-0096 FAQ A.6.

### C.3: Can I rotate my key while I have pending confidential sends?

No. Rotation increments `ConfidentialBalanceVersion`, invalidating in-flight send proofs. Queue rotation until all pending sends are confirmed.

### C.4: What happens to my inbox balance during key loss recovery?

It is reset to canonical encrypted zero. Any value in the inbox is consolidated into the spending balance via the issuer mirror. No value is lost.

### C.5: Can the issuer rotate my key without my consent?

No. `ConfidentialMPTRecoverBalance` is rejected if `RecoveryKey` is not set on your `MPToken`. The issuer cannot act without your prior on-chain authorization.

### C.6: How long does bulk mirror re-encryption take at scale?

Each `ConfidentialMPTMirrorUpdate` carries a new mirror ciphertext and compact Chaum-Pedersen equality proof. Fees are 10x base fee. `HolderCount` on `MPTokenIssuance` provides the total migration scope.

### C.7: Can the issuer rotate keys multiple times in quick succession?

Yes - the protocol does not enforce a global gate blocking successive rotations. Holders with stale mirrors are blocked from transacting at the per-transaction level regardless of how many epochs behind they are. `ConfidentialMPTMirrorUpdate` bridges directly from any old epoch to the current epoch in one step.

### C.8: How can I verify that all mirrors have been migrated?

Compare `IssuerKeyEpoch` on `MPTokenIssuance` against `IssuerKeyMirrorEpoch` on each `MPToken`. Whether a mirror is stale is trivially known on-ledger in O(1).

### C.9: Does ledger replay break after key rotation?

No. Each XRPL ledger version is a complete, immutable snapshot preserving the `IssuerEncryptionKey` that was active at that moment. Replaying a historical transaction uses the `MPTokenIssuance` state from that exact ledger version. This is identical to how signing key rotation works on XRPL.

## Notes for Discussion (Non-Normative)

This section is non-normative. It contains open questions that must be resolved before this XLS can be finalized.

### D1: `RecoveryKey` Lifecycle and Liveness

**Scenario 1**: Issuer never completes Step 2 - RESOLVED No automatic expiry. Forcing expiry penalizes a holder already in a degraded state with no ledger health benefit.

**Scenario 2**: Holder wants to abort - RESOLVED The holder cancels a pending recovery authorization by submitting `ConfidentialMPTHolderKeyUpdate` with `tfCancelRecovery`. No cryptographic proof required - the holder's XRPL signing key signature is sufficient. This works even if the holder has not recovered sk_H.

**Scenario 3**: Second `ConfidentialMPTHolderKeyUpdate` in recovery mode - open

Three sub-cases to consider:

- **Sub-case A**: Same pk_H' submitted again. Pure no-op - `RecoveryKey` is already set to this value. Should this be rejected or allowed (idempotent accept)?

- **Sub-case B**: Different pk_H' submitted. Holder wants to change their recovery key. Two options:
  - Reject (current design): Holder must cancel via `tfCancelRecovery` first, then resubmit. Two transactions, explicit intent, no race condition.
  - Allow overwrite: Convenience - one transaction. Risk: issuer may have already read the original `RecoveryKey`, constructed proof material, and submitted `ConfidentialMPTRecoverBalance`. If holder overwrites before issuer's transaction lands, issuer's recovery fails (proof is for old key) and issuer must start over. Not a safety issue - no funds at risk - but wastes issuer effort.

- **Sub-case C**: Issuer submits `ConfidentialMPTRecoverBalance` in the same ledger. If recovery lands first, `RecoveryKey` is cleared and the second authorization succeeds (no conflict). If authorization lands first, recovery fails (key mismatch). Both are safe outcomes.

Current spec rejects Sub-case A and B with `tecNO_PERMISSION`. Whether Sub-case A should be idempotent and whether Sub-case B should allow overwrite are open questions. Resolution needed before Draft can be finalized.

**Scenario 4**: `MPToken` deletion with `RecoveryKey` set - RESOLVED Non-issue. Per XLS-0096 Section 7.4, an `MPToken` cannot be deleted once confidential fields have been initialized. Since `RecoveryKey` only appears on initialized `MPToken` objects, deletion is already blocked by XLS-0096. No new protocol handling required.

### D2: Enforcing Migration Completeness Before Second Rotation - RESOLVED

No global enforcement of "no second rotation until first migration complete" is needed. The per-transaction staleness check (`IssuerKeyMirrorEpoch` < `IssuerKeyEpoch`) enforces correctness at the point of use for each individual holder. A holder with a stale mirror is blocked from transacting regardless of how many epochs behind they are. `ConfidentialMPTMirrorUpdate` bridges directly from any old epoch to the current epoch in one step.

The transactor architecture confirms this is the right approach: `ConfidentialMPTMirrorUpdate` is a per-holder transaction, so the transactor only sees one holder at a time and cannot enforce a global migration completeness check across all holders.

`HolderCount` on `MPTokenIssuance` provides the authoritative total for off-chain migration tracking. MirrorsMigrated as an on-ledger counter is not adopted - see D5.

### D3: Granular Permission Delegation

**Issuer-side**: Should `ConfidentialMPTMirrorUpdate` be delegatable to a separate bulk migration account without granting full `MPTokenIssuanceSet` authority?

**Holder-side**: Should `ConfidentialMPTHolderKeyUpdate` be delegatable to a custody provider?

Resolution needed before Draft can be finalized.

### D4: Synthetic Metadata Fields

Candidates for discussion:

- `ConfidentialMPTMirrorUpdate`: migration_complete boolean or holders_remaining counter.
- `ConfidentialMPTRecoverBalance`: recovery_complete boolean.
- `ConfidentialMPTHolderKeyUpdate`: mode field indicating rotation or recovery.

Resolution needed before Draft can be finalized.

### D5: MirrorsMigrated Counter - RESOLVED (not adopted)

MirrorsMigrated as an on-ledger counter is not adopted. See D2 for rationale. `HolderCount` on `MPTokenIssuance` is the chosen approach - it provides the authoritative total number of holders with initialized confidential state. Migration progress is tracked off-chain.

### D6: API / RPCs

No new RPCs anticipated, but response schemas for account_objects and ledger_data are modified. Open question: is a dedicated migration status query needed (e.g. retrieve all holders where `IssuerKeyMirrorEpoch` < `IssuerKeyEpoch`)? Or is this out of scope?

### D7: Freeze and Holder Key Rotation

Should `ConfidentialMPTHolderKeyUpdate` in rotation mode be permitted while `ConfidentialBalanceFrozen` = true? The holder is re-encrypting their balance without moving value, which does not inherently enable spending that was not already permitted. However, allowing key rotation on frozen accounts introduces operational complexity. Resolution needed before Draft can be finalized.

### D8: Recovery Mode Delegation

Should `ConfidentialMPTHolderKeyUpdate` in recovery mode be delegatable under XLS-0074?

**Option A**: Not delegatable - holder must sign directly. Recovery authorization is sensitive and infrequent; requiring the holder's direct XRPL signature ensures explicit on-chain consent.

**Option B**: Delegatable with a separate explicit permission distinct from rotation mode delegation, so custody providers cannot trigger recovery without being specifically authorized for it.

Resolution needed before Draft can be finalized.

### D9: Issuer-Side Permission Granularity

Should `ConfidentialMPTMirrorUpdate` and `ConfidentialMPTRecoverBalance` be separately delegatable permissions, or combined into a single issuer operational permission? Separate permissions allow finer-grained access control - a bulk migration operator does not need recovery authority and vice versa. Combined permissions simplify the permission model but grant broader authority than necessary for each use case.

Resolution needed before Draft can be finalized.

### D10: `ConfidentialBalanceSpending` and `ConfidentialBalanceInbox` in Rotation Mode

Currently `ConfidentialMPTHolderKeyUpdate` in rotation mode requires both `ConfidentialBalanceSpending` and `ConfidentialBalanceInbox` as separate fields. Three options under consideration:

**Option A**: Keep two fields (current design). Holder re-encrypts both CBS and CBIN under pk_H' and submits both. No merge required before rotation.

**Option B**: Require merge before rotation. Holder must run `ConfidentialMPTMergeInbox` first. After merge CBIN is `EncZero` - deterministic and not needed as a field. Only `ConfidentialBalanceSpending` submitted. Smaller proof, simpler transaction, but costs an extra mandatory transaction.

**Option C**: Make `ConfidentialBalanceInbox` optional. If absent, validators treat on-ledger CBIN as zero and reset to `EncZero`(pk_H') automatically. If present, equality proof covers it. New failure condition: `ConfidentialBalanceInbox` absent but on-ledger CBIN is not `EncZero`. No mandatory merge, no extra transaction cost when inbox is already empty.

Resolution needed before Draft can be finalized.
