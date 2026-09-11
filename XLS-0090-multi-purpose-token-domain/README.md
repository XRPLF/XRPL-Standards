<pre>
  xls: 90
  title: Permissioned Domains for MPTs
  description: Allow MPT issuers to authorize holders through credentials accepted by a permissioned domain.
  implementation: https://github.com/XRPLF/rippled/pull/5509
  author: Vito Tumas <vtumas@ripple.com>
  category: Amendment
  status: Draft
  proposal-from: https://github.com/XRPLF/XRPL-Standards/discussions/267
  requires: [XLS-33](../XLS-0033-multi-purpose-tokens/README.md), [XLS-65](../XLS-0065-single-asset-vault/README.md), [XLS-80](../XLS-0080-permissioned-domains/README.md)
  created: 2025-02-18
  updated: 2026-09-07
</pre>

# Permissioned Domains for MPTs

## 1. Abstract

An issuer can require explicit authorization for accounts to hold a Multi-Purpose Token (MPT). This proposal additionally lets the issuer associate the issuance with an [XLS-80 Permissioned Domain](../XLS-0080-permissioned-domains/README.md). An account is then authorized if it has credentials accepted by the domain or has explicit authorization from the MPT issuer.

## 2. Motivation

Authorizing every holder individually requires the MPT issuer to submit and maintain one authorization per account. A permissioned domain lets the issuer define accepted credential issuer-and-type pairs once and lets accounts prove eligibility with accepted credentials.

## 3. Specification

The `DomainID` functionality described by this specification is available only when both the `SingleAssetVault` and `PermissionedDomains` amendments are enabled. Before then, a transaction that includes `DomainID` in `MPTokenIssuanceCreate` or `MPTokenIssuanceSet` fails with `temDISABLED`.

An `MPTokenIssuance` with a `DomainID` must also have `lsfMPTRequireAuth` set. When authorization for such an issuance is checked, an account is authorized if any of the following is true:

1. The account is the MPT issuer.
2. The account has a valid, accepted credential matching the referenced permissioned domain.
3. The account has an `MPToken` object with `lsfMPTAuthorized` set.

Permissioned-domain and explicit issuer authorization therefore form a union. Authorization is evaluated against the current `MPTokenIssuance.DomainID`; no domain-related flag is added to individual `MPToken` objects.

## 3.1. Ledger Entry: `MPTokenIssuance`

### 3.1.1. Fields

This proposal adds the optional `DomainID` field to the existing `MPTokenIssuance` ledger entry. Unchanged fields are included below so that the example is self-contained.

| Field Name          | Constant | Required | Internal Type | Default Value | Description                                                               |
| ------------------- | -------- | -------- | ------------- | ------------- | ------------------------------------------------------------------------- |
| `LedgerEntryType`   | Yes      | Yes      | `UINT16`      | `0x007e`      | Identifies this as an `MPTokenIssuance` object.                           |
| `Flags`             | No       | Yes      | `UINT32`      | `0`           | A set of flags controlling the issuance.                                  |
| `Issuer`            | No       | Yes      | `ACCOUNT`     | N/A           | The account that issued the MPT.                                          |
| `Sequence`          | No       | Yes      | `UINT32`      | N/A           | The issuer sequence used to derive the issuance ID.                       |
| `OwnerNode`         | No       | Yes      | `UINT64`      | N/A           | A hint to the issuance's page in the issuer's owner directory.            |
| `OutstandingAmount` | No       | Yes      | `UINT64`      | `0`           | The total amount of this MPT currently held by non-issuer accounts.       |
| `PreviousTxnID`     | No       | Yes      | `HASH256`     | N/A           | The transaction that most recently modified this entry.                   |
| `PreviousTxnLgrSeq` | No       | Yes      | `UINT32`      | N/A           | The ledger index of the most recent transaction that modified this entry. |
| `DomainID`          | No       | No       | `HASH256`     | N/A           | The associated `PermissionedDomain` object ID.                            |

#### 3.1.1.1. `DomainID`

If present, `DomainID` identifies the permissioned domain used to authorize MPT holders. The field is mutable and can be added, replaced, or removed with `MPTokenIssuanceSet`.

### 3.1.2. Flags

This proposal does not add a ledger-entry flag. An issuance with `DomainID` uses the existing `lsfMPTRequireAuth` flag (`0x00000004`).

### 3.1.3. Invariants

- If `<MPTokenIssuance>.DomainID` is present, `<MPTokenIssuance>.Flags & lsfMPTRequireAuth != 0`.

### 3.1.4. Example JSON

```json
{
  "LedgerEntryType": "MPTokenIssuance",
  "Flags": 4,
  "Issuer": "rHb9CJAWyB4rj91VRWn96DkukG4bwdtyTh",
  "Sequence": 42,
  "OwnerNode": "0000000000000000",
  "OutstandingAmount": "0",
  "PreviousTxnID": "C4B1A16F1DF4E2B3D5A8D061C2A30DAB8E84D1B0A7B5F6F4DE2EA1D2E1C113A0",
  "PreviousTxnLgrSeq": 1000000,
  "DomainID": "3B61A239626565A3FBEFC32863AFBF1AD3325BD1669C2C9BC92954197842B564"
}
```

## 3.2. Transaction: `MPTokenIssuanceCreate`

### 3.2.1. Fields

This proposal adds `DomainID` to the existing transaction. Other fields shown are used by the example.

| Field Name        | Required? | JSON Type | Internal Type | Default Value           | Description                                               |
| ----------------- | --------- | --------- | ------------- | ----------------------- | --------------------------------------------------------- |
| `TransactionType` | Yes       | `string`  | `UINT16`      | `MPTokenIssuanceCreate` | Identifies the transaction.                               |
| `Account`         | Yes       | `string`  | `ACCOUNT`     | N/A                     | The MPT issuer.                                           |
| `Flags`           | No        | `number`  | `UINT32`      | `0`                     | Must include `tfMPTRequireAuth` when `DomainID` is set.   |
| `Fee`             | No        | `string`  | `AMOUNT`      | N/A                     | The transaction fee in drops.                             |
| `DomainID`        | No        | `string`  | `HASH256`     | N/A                     | The ID of the permissioned domain used for authorization. |

### 3.2.2. Failure Conditions

#### 3.2.2.1. Data Verification

1. `DomainID` is present but either `SingleAssetVault` or `PermissionedDomains` is disabled. (`temDISABLED`)
2. `DomainID` is zero. (`temMALFORMED`)
3. `DomainID` is present but `tfMPTRequireAuth` is not set. (`temMALFORMED`)

`MPTokenIssuanceCreate` does not require the referenced permissioned domain to exist when the issuance is created.

#### 3.2.2.2. Protocol-Level Failures

This proposal adds no protocol-level failure conditions to `MPTokenIssuanceCreate`.

### 3.2.3. State Changes

**On Success (`tesSUCCESS`):**

- Create the `MPTokenIssuance` with its `DomainID` set to the transaction's `DomainID`, if provided.

### 3.2.4. Example JSON

```json
{
  "TransactionType": "MPTokenIssuanceCreate",
  "Account": "rHb9CJAWyB4rj91VRWn96DkukG4bwdtyTh",
  "Flags": 4,
  "Fee": "10",
  "DomainID": "3B61A239626565A3FBEFC32863AFBF1AD3325BD1669C2C9BC92954197842B564"
}
```

## 3.3. Transaction: `MPTokenIssuanceSet`

### 3.3.1. Fields

This proposal adds `DomainID` to the existing transaction. Other fields shown are used by the example.

| Field Name          | Required? | JSON Type | Internal Type | Default Value        | Description                                                               |
| ------------------- | --------- | --------- | ------------- | -------------------- | ------------------------------------------------------------------------- |
| `TransactionType`   | Yes       | `string`  | `UINT16`      | `MPTokenIssuanceSet` | Identifies the transaction.                                               |
| `Account`           | Yes       | `string`  | `ACCOUNT`     | N/A                  | The MPT issuer.                                                           |
| `MPTokenIssuanceID` | Yes       | `string`  | `UINT192`     | N/A                  | Identifies the issuance to modify.                                        |
| `Fee`               | No        | `string`  | `AMOUNT`      | N/A                  | The transaction fee in drops.                                             |
| `DomainID`          | No        | `string`  | `HASH256`     | N/A                  | A domain ID to set, or all zeroes to remove the current `DomainID` field. |

### 3.3.2. Failure Conditions

#### 3.3.2.1. Data Verification

1. `DomainID` is present but either `SingleAssetVault` or `PermissionedDomains` is disabled. (`temDISABLED`)
2. Both `DomainID` and `Holder` are present. (`temMALFORMED`)

#### 3.3.2.2. Protocol-Level Failures

1. The `MPTokenIssuance` does not exist. (`tecOBJECT_NOT_FOUND`)
2. `Account` is not the issuance's `Issuer`. (`tecNO_PERMISSION`)
3. The issuance does not have `lsfMPTRequireAuth` set. (`tecNO_PERMISSION`)
4. `DomainID` is non-zero and the referenced `PermissionedDomain` does not exist. (`tecOBJECT_NOT_FOUND`)

### 3.3.3. State Changes

**On Success (`tesSUCCESS`):**

- If `DomainID` is non-zero, add or replace `MPTokenIssuance.DomainID`.
- If `DomainID` is zero, remove `MPTokenIssuance.DomainID` if it is present.

### 3.3.4. Example JSON

```json
{
  "TransactionType": "MPTokenIssuanceSet",
  "Account": "rHb9CJAWyB4rj91VRWn96DkukG4bwdtyTh",
  "MPTokenIssuanceID": "0000002A9F14C21D846D8D06E7B3C3275A0C288442D6E5C5",
  "Fee": "10",
  "DomainID": "3B61A239626565A3FBEFC32863AFBF1AD3325BD1669C2C9BC92954197842B564"
}
```

## 3.4. Transaction: `Payment`

### 3.4.1. Fields

This proposal adds no fields to `Payment`. The relevant existing fields are shown for the example.

| Field Name        | Required? | JSON Type | Internal Type | Default Value | Description                   |
| ----------------- | --------- | --------- | ------------- | ------------- | ----------------------------- |
| `TransactionType` | Yes       | `string`  | `UINT16`      | `Payment`     | Identifies the transaction.   |
| `Account`         | Yes       | `string`  | `ACCOUNT`     | N/A           | The sending account.          |
| `Destination`     | Yes       | `string`  | `ACCOUNT`     | N/A           | The receiving account.        |
| `Amount`          | Yes       | `object`  | `AMOUNT`      | N/A           | The MPT amount to deliver.    |
| `Fee`             | No        | `string`  | `AMOUNT`      | N/A           | The transaction fee in drops. |

### 3.4.2. Failure Conditions

#### 3.4.2.1. Data Verification

This proposal adds no data-verification failures to `Payment`.

#### 3.4.2.2. Protocol-Level Failures

For an MPT whose issuance has `DomainID`, authorization is checked for both `Account` and `Destination`, except that the MPT issuer is always authorized.

1. An account has neither a valid credential accepted by the domain nor an `MPToken` with `lsfMPTAuthorized` set. (`tecNO_AUTH`, or `tecEXPIRED` if its matching credentials are expired)
2. The referenced `PermissionedDomain` does not exist and the account does not have an `MPToken` with `lsfMPTAuthorized` set. (`tecOBJECT_NOT_FOUND`)

### 3.4.3. State Changes

This proposal adds no state changes to `Payment`.

### 3.4.4. Example JSON

```json
{
  "TransactionType": "Payment",
  "Account": "rHb9CJAWyB4rj91VRWn96DkukG4bwdtyTh",
  "Destination": "rG1QQv2nh2gr7RCZ1P8YYcBUKCCN633jCn",
  "Amount": {
    "mpt_issuance_id": "0000002A9F14C21D846D8D06E7B3C3275A0C288442D6E5C5",
    "value": "100"
  },
  "Fee": "10"
}
```

## 4. Rationale

A permissioned domain complements explicit per-account authorization: credential policy can be maintained in one domain while the issuer can still authorize exceptional accounts individually. Evaluating the current issuance-level `DomainID` at authorization time avoids adding a redundant domain flag to every `MPToken` object and lets the issuer change or remove a domain without rewriting all holder objects.

The alternative is to use only `MPTokenAuthorize`. That provides finer-grained control but requires an issuer transaction for every account and does not automatically react to credential acceptance, expiration, or deletion.

## 5. Backwards Compatibility

The change is amendment-gated. Before both required amendments are active, the new transaction field is rejected. Existing issuances without `DomainID` retain their prior authorization behavior.

Changing or removing an issuance's domain can immediately change which accounts may transfer or receive the MPT. Existing balances and `MPToken` objects are not rewritten.

## 6. Test Plan

Implementation tests cover amendment gating, zero and missing domain identifiers, the `lsfMPTRequireAuth` requirement, adding, replacing, and removing a domain, issuer authorization, explicit authorization fallback, credential-based payments, and credential deletion.

## 7. Reference Implementation

[XRPLF/rippled#5509](https://github.com/XRPLF/rippled/pull/5509)

## 8. Security Considerations

Issuers must treat a `DomainID` update as an access-control policy change. Replacing or removing it takes effect on subsequent authorization checks and may immediately prevent existing holders from transferring or receiving the MPT.

Credential expiration or deletion removes domain-based authorization. Explicit authorization is independent: an account whose `MPToken` has `lsfMPTAuthorized` set remains authorized even if its credential is invalid or the referenced domain has been deleted.

`MPTokenIssuanceCreate` does not verify that a non-zero `DomainID` identifies an existing object. An issuer that supplies an incorrect or not-yet-created domain can make domain-based authorization fail until the issuer uses `MPTokenIssuanceSet` to select an existing domain or remove the field. `MPTokenIssuanceSet` verifies non-zero domain identifiers before applying them.
