<pre>
    title:  Confidential Transfers for Multi-Purpose Tokens
    description: This amendment introduces Confidential MPT Key Rotation on the XRP Ledger.
    author: Aanchal Malhotra <amalhotra@ripple.com>, Yinyi Qian <yqian@ripple.com>, Peter Chen <ychen@ripple.com>, Oleksandr Pidskopnyi <oleks_rip@proton.me>
    proposal-from: ???
    status: Draft
    category: Amendment
    requires: XLS-96
    created: 2026-07-22
</pre>

# Confidential MPT Key Rotation

## Abstract

This proposal introduces a new amendment `ConfidentialMPTKeyRotation` as an extension to [XLS-96 Confidential Transfers for Multi-Purpose Tokens](https://github.com/XRPLF/XRPL-Standards/blob/master/XLS-0096-confidential-mpt/README.md). It prposes a ElGamal key rotation across all three roles in the Confidential MPT protocol: issuer, auditor, and holder. It also addresses holder key loss recovery and issuer key loss recovery.

## 1. Overview

This proposal introduces：

- Update `MPTokenIssuance` ledger object:
  - Submitted by issuer.
  - Add a new field `sfIssuerKeyEpoch` and `sfAuditorKeyEpoch` to track the key rotation epoch.
  - Add a new field `sfHolderCount` to track the number of holders, which is used to coordinate the off-chain work for the issuer.

- Update `MPTokenIssuanceSet` transaction:
  - Pre-amendment: `MPTokenIssuanceSet` disallows updating the issuer / auditor ElGamal key. Once set, stay unchanged. Otherwise, return `tecNO_PERMISSION`.
  - Post-amendment: `MPTokenIssuanceSet` allows updating the issuer / auditor ElGamal key. The corresponding epoch number should be incremted by 1. It is allowed to set
    both issuer and auditor ElGamal key in the same transaction.

- Update `MPToken` ledger object:
  - Add a new field `sfRecoveryKey` to track the new ElGamal public key when the holder lost his private key.
  - Add the new fields `sfIssuerKeyMirrorEpoch` and `sfAuditorKeyMirrorEpoch` to track the last key rotation epoch that the issuer has mirrored to the holder.
  - If holder's `sfIssuerKeyMirrorEpoch` < issuer's `sfIssuerKeyEpoch`, the holder's `sfIssuerEncryptedBalance` is stale.
  - If holder's `sfAuditorKeyMirrorEpoch` < issuer's `sfAuditorKeyEpoch`, the holder's `sfAuditorEncryptedBalance` is stale.

- New transaction `ConfidentialMPTMirrorUpdate`:
  - Submitted by issuer.
  - If issuer updated a new issuer ElGamal key, then he needs to re-encrypt the `sfIssuerEncryptedBalance` using the new ElGamal key for each holder.
  - If issuer updared a new auditor ElGamal key, then he needs to re-encrypt the `sfAuditorEncryptedBalance` using the new ElGamal key for each holder.
  - It is allowed to update both `sfIssuerEncryptedBalance` and `sfAuditorEncryptedBalance` in the same transaction.
  - Please **note** that this transaction targets a single holder at a time. Traversing all the holders is off-chain.
  - We recommend the issuer to lock the `MPToken` before submitting this transaction, after the transaction succeeded, unlock the `MPToken`.
  - The issuer reveals the holder's balance (`sfIssuerEncryptedBalance`) via his ElGamal private key and re-encrypts the balance using the new ElGamal key.
  - Requires a Chaum-Pedersen equality proof to guarantee that the new ciphertext encrypts the exact same balance as the old one. And we can use Compact Chaum-Pedersen equality proof if updating both mirrors.

- New transaction `ConfidentialMPTHolderKeyUpdate`:
  - Submitted by holder.
  - If the holder wants to rotate his ElGamal key (**Rotation mode**):
    1. Use flag `tfHolderKeyRotation`.
    2. Holder provides his new ElGamal public key.
    3. Because the holder still owns the current private key, he decrypts his
       `sfConfidentialBalanceSpending` and `sfConfidentialBalanceInbox`, re-encrypts both under the
       new key, and provides the two new ciphertexts.
    4. Requires a Compact Chaum-Pedersen equality proof covering both the spending and inbox
       equality statements, plus a Schnorr PoK proving knowledge of the ElGamal private key.
  - If the holder lost his private key (**Recovery mode**):
    1. Use flag `tfHolderKeyRecovery`.
    2. Holder provides his new ElGamal public key and a Schnorr PoK proving knowledge of the
       corresponding new private key.
    3. Because the holder can no longer decrypt his own balances, he does **not** provide new
       ciphertexts or an equality proof. The new ElGamal public key is recorded as
       `sfRecoveryKey` on the holder's `MPToken`; the confidential balances are **not** modified yet.
    4. The recovery will be completed by the issuer via `ConfidentialMPTRecoverBalance`.

- New transaction `ConfidentialMPTRecoverBalance`:
  - Submitted by the issuer to complete a holder key recovery previously authorized via
    `ConfidentialMPTHolderKeyUpdate` (Recovery mode).
  - The issuer reveals the holder's balance by decrypting `sfIssuerEncryptedBalance` with his
    ElGamal private key (the mirror reflects the holder's total confidential balance), then
    re-encrypts that balance under the holder's `MPToken` object's `sfRecoveryKey` and set it as
    the new `sfConfidentialBalanceSpending`. `sfConfidentialBalanceInbox` is set to an encrypted zero.
  - Requires a Chaum-Pedersen equality proof that the new spending ciphertext
    encrypts the same value as the on-ledger `sfIssuerEncryptedBalance`.

## 2. Ledger object update

### 2.1 `MPTokenIssuance`

This proposal adds three new fields to the `MPTokenIssuance` ledger object to support and track
ElGamal key rotation.

| Field Name        | Required? | JSON Type | Internal Type | Description                                                                                   |
| :---------------- | :-------- | :-------- | :------------ | :-------------------------------------------------------------------------------------------- |
| `IssuerKeyEpoch`  | No        | `number`  | `UINT32`      | Incremented by `1` each time issuer updates the issuer ElGamal key via `MPTokenIssuanceSet`.  |
| `AuditorKeyEpoch` | No        | `number`  | `UINT32`      | Incremented by `1` each time issuer updates the auditor ElGamal key via `MPTokenIssuanceSet`. |
| `HolderCount`     | No        | `number`  | `UINT64`      | The number of holders that currently hold confidential state for this issuance.               |

All of the three fields are `soeDefault` type. Default value is `0`, if present, the field must not be `0`.

### 2.2 `MPToken`

This proposal adds three new fields to the `MPToken` ledger object.

| Field Name              | Required? | JSON Type | Internal Type | Description                                                                                                                                                                                                                                                |
| :---------------------- | :-------- | :-------- | :------------ | :--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `IssuerKeyMirrorEpoch`  | No        | `number`  | `UINT32`      | The mirror is **stale** when `IssuerKeyMirrorEpoch` < `IssuerKeyEpoch` in `MPTokenIssuance`.                                                                                                                                                               |
| `AuditorKeyMirrorEpoch` | No        | `number`  | `UINT32`      | The mirror is **stale** when `AuditorKeyMirrorEpoch` < `AuditorKeyEpoch` in `MPTokenIssuance`.                                                                                                                                                             |
| `RecoveryKey`           | No        | `string`  | `BLOB`        | A 33-byte compressed ElGamal public key that the holder has authorized as their new key for recovery. Set by `ConfidentialMPTHolderKeyUpdate` by holder in Recovery mode and cleared by `ConfidentialMPTRecoverBalance` by issuer once recovery completes. |

`IssuerKeyMirrorEpoch` and `AuditorKeyMirrorEpoch` are `soeDefault` type. Default value is `0`, if present, the field must not be `0`.
`RecoveryKey` is `soeOptional` type.

## 3. Transaction update

### 3.1 `MPTokenIssuanceSet`

No field update, the issuer provide `sfIssuerEncryptionKey` to update the issuer ElGamal key; provide `sfAuditorEncryptionKey` to update the auditor ElGamal key. The corresponding epoch number will be incremted by 1. The issuer is allowed to update both keys in the same transaction.

### 3.2 `ConfidentialMPTMirrorUpdate`

After issuer updates `sfIssuerEncryptionKey` and/or `sfAuditorEncryptionKey` via `MPTokenIssuanceSet`, the issuer needs to re-encrypt the holder's mirror balance using the new ElGamal key.
This transaction must be submitted by the issuer. It re-encrypts a single holder's issuer mirror (`sfIssuerEncryptedBalance`) and/or auditor
mirror (`sfAuditorEncryptedBalance`) under the issuance's new public ElGamal key(s).

#### 3.2.1 Fields

| Field Name               | Required? | JSON Type | Internal Type | Description                                                                                                                         |
| :----------------------- | :-------- | :-------- | :------------ | :---------------------------------------------------------------------------------------------------------------------------------- |
| `TransactionType`        | Yes       | `string`  | `UINT16`      | `ConfidentialMPTMirrorUpdate`, which is 90.                                                                                         |
| `Account`                | Yes       | `string`  | `ACCOUNTID`   | The issuer account.                                                                                                                 |
| `Holder`                 | Yes       | `string`  | `ACCOUNTID`   | The holder whose mirror(s) are being re-encrypted.                                                                                  |
| `MPTokenIssuanceID`      | Yes       | `string`  | `UINT192`     | The unique identifier of the MPT issuance.                                                                                          |
| `IssuerEncryptedAmount`  | No        | `string`  | `BLOB`        | A 66-byte ElGamal ciphertext encrypting the holder's balance under the new issuer key. Present to migrate holder's issuer mirror.   |
| `AuditorEncryptedAmount` | No        | `string`  | `BLOB`        | A 66-byte ElGamal ciphertext encrypting the holder's balance under the new auditor key. Present to migrate holder's auditor mirror. |
| `ZKProof`                | Yes       | `string`  | `BLOB`        | A single Compact Chaum-Pedersen proof to prove that the new ciphertext encrypts the same value as the old one.                      |

At least one of `IssuerEncryptedAmount` or `AuditorEncryptedAmount` must be present.
This transaction is charged the same elevated base fee as other Confidential MPT transactions. (10 x base fee)

#### 3.2.2 Failure Conditions

1. The `ConfidentialMPTKeyRotation` amendment is not enabled. (`temDISABLED`)
2. `Account` is not the issuer of `MPTokenIssuanceID`. (`temMALFORMED`)
3. `Account` is the same as `Holder`. (`temMALFORMED`)
4. Neither `IssuerEncryptedAmount` nor `AuditorEncryptedAmount` is present. (`temMALFORMED`)
5. Any present `*EncryptedAmount` has an invalid length or represents an invalid elliptic curve point. (`temBAD_CIPHERTEXT`)
6. `ZKProof` length is not exactly the fixed Compact Chaum-Pedersen proof size. (`temMALFORMED`)
7. The `Holder` account does not exist. (`tecNO_TARGET`)
8. The `MPTokenIssuance` or the holder's `MPToken` object does not exist. (`tecOBJECT_NOT_FOUND`)
9. The issuance does not have the `lsfMPTCanHoldConfidentialBalance` flag set. (`tecNO_PERMISSION`)
10. `IssuerEncryptedAmount` is present but the issuance is missing `IssuerEncryptionKey`, or the holder's `MPToken` is missing `IssuerEncryptedBalance`. (`tecNO_PERMISSION`)
11. `AuditorEncryptedAmount` is present but the issuance is missing `AuditorEncryptionKey`, or the holder's `MPToken` is missing `AuditorEncryptedBalance`. (`tecNO_PERMISSION`)
12. `IssuerEncryptedAmount` is present but the holder's issuer mirror is not stale (`IssuerKeyMirrorEpoch` == `IssuerKeyEpoch`; nothing to migrate). (`tecNO_PERMISSION`)
13. `AuditorEncryptedAmount` is present but the holder's auditor mirror is not stale (`AuditorKeyMirrorEpoch` == `AuditorKeyEpoch`). (`tecNO_PERMISSION`)
14. The `ZKProof` fails the Compact Chaum-Pedersen verification. (`tecBAD_PROOF`)

#### 3.2.3 Example JSON

```json
{
  "Account": "rIssuerAccount...",
  "TransactionType": "ConfidentialMPTMirrorUpdate",
  "Holder": "rHolderAccount...",
  "MPTokenIssuanceID": "610F33B8EBF7EC795F822A454FB852156AEFE50BE0CB8326338A81CD74801864",
  "IssuerEncryptedAmount": "BC2E...",
  "AuditorEncryptedAmount": "C1A9...",
  "ZKProof": "a1b2..."
}
```

### 3.3 `ConfidentialMPTHolderKeyUpdate`

The transaction is submitted by the holder. It operates in two modes selected by a transaction flag:

- **Rotation mode** (`tfHolderKeyRotation`): the holder still controls the current private key. They
  decrypt their `sfConfidentialBalanceSpending` (CBS) and `sfConfidentialBalanceInbox` (CBIN),
  re-encrypt both under the new key, and rotate atomically. No issuer involvement.
- **Recovery mode** (`tfHolderKeyRecovery`): the holder has lost the current private key and cannot
  decrypt their balances. They only register the new key as a pending `sfRecoveryKey`; the actual
  balance re-encryption is completed by the issuer via `ConfidentialMPTRecoverBalance` (see below 3.4)

#### 3.3.1 Fields

| Field Name                    | Required? | JSON Type | Internal Type | Description                                                                                                                                                                                                                                                                                                               |
| :---------------------------- | :-------- | :-------- | :------------ | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `TransactionType`             | Yes       | `string`  | `UINT16`      | `ConfidentialMPTHolderKeyUpdate`, which is 91.                                                                                                                                                                                                                                                                            |
| `Account`                     | Yes       | `string`  | `ACCOUNTID`   | The holder account.                                                                                                                                                                                                                                                                                                       |
| `MPTokenIssuanceID`           | Yes       | `string`  | `UINT192`     | The unique identifier of the MPT issuance.                                                                                                                                                                                                                                                                                |
| `Flags`                       | Yes       | `number`  | `UINT32`      | Exactly one of `tfHolderKeyRotation` or `tfHolderKeyRecovery`                                                                                                                                                                                                                                                             |
| `HolderEncryptionKey`         | Yes       | `string`  | `BLOB`        | The holder's new 33-byte compressed ElGamal public key.                                                                                                                                                                                                                                                                   |
| `ConfidentialBalanceSpending` | No        | `string`  | `BLOB`        | A 66-byte ElGamal ciphertext under new ElGamal public key. **Required** in Rotation mode; **must be absent** in Recovery mode.                                                                                                                                                                                            |
| `ConfidentialBalanceInbox`    | No        | `string`  | `BLOB`        | A 66-byte ElGamal ciphertext under new ElGamal public key. **Required** in Rotation mode; **must be absent** in Recovery mode.                                                                                                                                                                                            |
| `ZKProof`                     | Yes       | `string`  | `BLOB`        | **Rotation mode:** a single Compact Chaum-Pedersen equality proof AND-composing the spending and inbox equality statements, plus a Schnorr PoK proving knowledge of the new ElGamal private key, under one Fiat-Shamir challenge. **Recovery mode:** a Schnorr PoK proving knowledge of the new ElGamal private key only. |

This transaction is charged the same elevated base fee as other Confidential MPT transactions. (10 x base fee)

#### 3.3.2 Flags

| Flag Name             | Hex Value    | Decimal Value | Description                                                                                      |
| :-------------------- | :----------- | :------------ | :----------------------------------------------------------------------------------------------- |
| `tfHolderKeyRotation` | `0x00000001` | 1             | Rotation mode: re-encrypt the spending and inbox balances under the new key in this transaction. |
| `tfHolderKeyRecovery` | `0x00000002` | 2             | Recovery mode: register the new key as `sfRecoveryKey` for issuer-completed recovery.            |

Exactly one of the two flags must be set.

#### 3.3.3 Failure Conditions

1. The `featureConfidentialMPTKeyRotation` amendment is not enabled. (`temDISABLED`)
2. Neither `tfHolderKeyRotation` nor `tfHolderKeyRecovery` is set, or both are set. (`temINVALID_FLAG`)
3. `Account` is the issuer of `MPTokenIssuanceID` (the issuer cannot hold confidential balances). (`temMALFORMED`)
4. `HolderEncryptionKey` is not exactly 33 bytes. (`temMALFORMED`)
5. Rotation mode: `ConfidentialBalanceSpending` or `ConfidentialBalanceInbox` is missing. (`temMALFORMED`)
6. Recovery mode: `ConfidentialBalanceSpending` or `ConfidentialBalanceInbox` is present. (`temMALFORMED`)
7. Any present ciphertext has an invalid length or represents an invalid elliptic curve point. (`temBAD_CIPHERTEXT`)
8. `ZKProof` is absent, or its length is not exactly the fixed size expected for the selected mode. (`temMALFORMED`)
9. The `MPTokenIssuance` or the holder's `MPToken` object does not exist. (`tecOBJECT_NOT_FOUND`)
10. The issuance does not have the `lsfMPTCanHoldConfidentialBalance` flag set. (`tecNO_PERMISSION`)
11. The holder's `MPToken` is missing confidential state (`sfHolderEncryptionKey`, `sfConfidentialBalanceSpending`, or `sfConfidentialBalanceInbox`). (`tecNO_PERMISSION`)
12. `HolderEncryptionKey` equals the current on-ledger `sfHolderEncryptionKey` (no-op key change). (`tecNO_PERMISSION`)
13. The Schnorr PoK fails to verify. (`tecBAD_PROOF`)
14. Rotation mode only: the Compact Chaum-Pedersen equality proof fails to verify. (`tecBAD_PROOF`)

#### 3.3.4 Example JSON

**Rotation mode:**

```json
{
  "Account": "rHolderAccount...",
  "TransactionType": "ConfidentialMPTHolderKeyUpdate",
  "MPTokenIssuanceID": "610F33B8EBF7EC795F822A454FB852156AEFE50BE0CB8326338A81CD74801864",
  "Flags": 1,
  "HolderEncryptionKey": "039d...",
  "ConfidentialBalanceSpending": "AD3F...",
  "ConfidentialBalanceInbox": "DF4E...",
  "ZKProof": "a1b2..."
}
```

**Recovery mode:**

```json
{
  "Account": "rHolderAccount...",
  "TransactionType": "ConfidentialMPTHolderKeyUpdate",
  "MPTokenIssuanceID": "610F33B8EBF7EC795F822A454FB852156AEFE50BE0CB8326338A81CD74801864",
  "Flags": 2,
  "HolderEncryptionKey": "039d...",
  "ZKProof": "c3d4..."
}
```

### 3.4 `ConfidentialMPTRecoverBalance`

Submitted by issuer. After the holder submitted a `ConfidentialMPTHolderKeyUpdate` in Recovery mode, the issuer re-encrypts the holder's balance (decrypted from its own mirror) under the holder's
`sfRecoveryKey`, sets it as the new spending balance, and resets the inbox to encrypted zero.

#### 3.4.1 Fields

| Field Name                    | Required? | JSON Type | Internal Type | Description                                                                                                                                                      |
| :---------------------------- | :-------- | :-------- | :------------ | :--------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `TransactionType`             | Yes       | `string`  | `UINT16`      | `ConfidentialMPTRecoverBalance`, which is 92.                                                                                                                    |
| `Account`                     | Yes       | `string`  | `ACCOUNTID`   | The issuer account.                                                                                                                                              |
| `Holder`                      | Yes       | `string`  | `ACCOUNTID`   | The holder account being recovered.                                                                                                                              |
| `MPTokenIssuanceID`           | Yes       | `string`  | `UINT192`     | The unique identifier of the MPT issuance.                                                                                                                       |
| `ConfidentialBalanceSpending` | Yes       | `string`  | `BLOB`        | A 66-byte ElGamal ciphertext: the holder's total confidential balance re-encrypted under the holder's pending `sfRecoveryKey`. Becomes the new spending balance. |
| `ZKProof`                     | Yes       | `string`  | `BLOB`        | Chaum-Pedersen equality proof that `ConfidentialBalanceSpending` encrypts the same value as the on-ledger `sfIssuerEncryptedBalance`.                            |

This transaction is charged the same elevated base fee as other Confidential MPT transactions. (10 x base fee)

#### 3.4.2 Failure Conditions

1. The `featureConfidentialMPTKeyRotation` amendment is not enabled. (`temDISABLED`)
2. `Account` is not the issuer of `MPTokenIssuanceID`. (`temMALFORMED`)
3. `Account` is the same as `Holder`. (`temMALFORMED`)
4. `ConfidentialBalanceSpending` has an invalid length or represents an invalid elliptic curve point. (`temBAD_CIPHERTEXT`)
5. `ZKProof` is absent, or its length is not exactly the fixed Chaum-Pedersen equality proof size. (`temMALFORMED`)
6. The `Holder` account does not exist. (`tecNO_TARGET`)
7. The `MPTokenIssuance` or the holder's `MPToken` object does not exist. (`tecOBJECT_NOT_FOUND`)
8. The issuance does not have the `lsfMPTCanHoldConfidentialBalance` flag set. (`tecNO_PERMISSION`)
9. The issuance is missing `sfIssuerEncryptionKey`, or the holder's `MPToken` is missing `sfIssuerEncryptedBalance`. (`tecNO_PERMISSION`)
10. The holder's `MPToken` has no pending `sfRecoveryKey` (the holder has not authorized recovery). (`tecNO_PERMISSION`)
11. The holder's issuer mirror is stale (`sfIssuerKeyMirrorEpoch` < `sfIssuerKeyEpoch`); the issuer must migrate it via `ConfidentialMPTMirrorUpdate` before recovery, so the proof can be verified against the current issuer key. (`tecNO_PERMISSION`)
12. The `ZKProof` fails the Chaum-Pedersen equality verification (verified against the on-ledger `sfIssuerEncryptedBalance` and the holder's `sfRecoveryKey`). (`tecBAD_PROOF`)

#### 3.4.4 Example JSON

```json
{
  "Account": "rIssuerAccount...",
  "TransactionType": "ConfidentialMPTRecoverBalance",
  "Holder": "rHolderAccount...",
  "MPTokenIssuanceID": "610F33B8EBF7EC795F822A454FB852156AEFE50BE0CB8326338A81CD74801864",
  "ConfidentialBalanceSpending": "AD3F...",
  "ZKProof": "e5f6..."
}
```
