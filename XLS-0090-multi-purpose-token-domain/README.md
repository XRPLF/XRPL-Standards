<pre>
Title:       <b>PermissionedDomain for Multi-Purpose Token</b>
Type:        <b>draft</b>
State:       <b>Updates: XLS-33</b>
Requires:   <b>XLS-80</b>

Authors:  
             <a href="mailto:vtumas@ripple.com">Vito Tumas</a>
Affiliation: <a href="https://ripple.com">Ripple</a>
</pre>

# Multi-Purpose Token DomainID

## _Abstract_

The issuer of a Multi-Purpose Token may require explicit authorization for individuals to hold the token. This is done through the issuer submitting an `MPTokenAuthorize` transaction, which authorizes each account individually.

The (XLS-80)[https://github.com/XRPLF/XRPL-Standards/tree/master/XLS-0080-permissioned-domains] specification introduces a new mechanism for broader authorization. The Permissioned Domain specifies a list of accepted `(Issuer, Type)` credential pairs within the domain. Any holder of valid credentials can interact with the protocols in this Permissioned Domain.

This specification adds `PermissionedDomain` support to the Multi-Purpose Token. By allowing the issuer to set a `DomainID`, we provide a more unified and efficient mechanism for controlling who may hold or receive the asset.

## 1. Introduction

## 2. Ledger Entries

### 2.1. `MPTokenIssuance` Ledger Entry

This section outlines the changes made to the `MPTokenIssuance` object. In summary, the XLS adds a new `DomainID` field to the `MPTokenIssuance` object.

#### 2.1.1. Fields

| Field Name | Change Type | Modifiable? | Required? | JSON Type | Internal Type | Default Value | Description                                                               |
| ---------- | :---------: | :---------: | :-------: | :-------: | :-----------: | :-----------: | :------------------------------------------------------------------------ |
| `DomainID` |    `New`    |    `Yes`    |    No     | `string`  |   `HASH256`   |     None      | The `PermissionedDomain` object ID associated with the `MPTokenIssuance`. |

##### 2.1.1.1. DomainID

An optional identifier for the `PermissionedDomain` object linked to the `MPTokenIssuance`. If `DomainID` is specified, the account must possess credentials approved by the `PermissionedDomain` to hold the `MPT`.

### 2.2. `MPToken` Ledger Entry

This section outlines the changes made to the `MPToken` object. In summary, the XLS adds a new `Flags` value, `lsfMPTDomainCheck`.

#### 2.2.1. Fields

| Field Name | Change Type | Modifiable? | Required? | JSON Type | Internal Type | Default Value | Description                                                                                             |
| ---------- | :---------: | :---------: | :-------: | :-------: | :-----------: | :-----------: | :------------------------------------------------------------------------------------------------------ |
| `Flags`    |  `Update`   |    `Yes`    |    No     | `number`  |   `UINT16`    |       0       | A set of flags indicating properties or other options associated with the **`MPTokenIssuance`** object. |

#### 2.2.1.1. Flags

The `Vault` object supports the following flags:

| Flag Name           | Change Type | Flag Value | Modifiable? | Description                                                                                                                                                                                                               |
| ------------------- | :---------: | :--------: | :---------: | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `lsfMPTDomainCheck` |    `New`    |  `0x0004`  |    `No`     | If set, indicates that _individual_ holders must have credentials in the `PermissionedDomain` of the `MPTokenIssuance`. This flag is set automatically when the associated `MPTokenIssuance` object has a `DomainID` set. |

## 3. Transactions

## 3.1. `MPTokenIssuance` Transactions

#### 3.1.1. `MPTokenIssuaceCreate` Transaction

This section outlines changes made to the `MPTokenIssuanceCreate` transaction. In summary, the specification adds a new `DomainID` field to the transaction.

#### 3.1.1.1. Fields

| Field Name | Change Type | Required? | JSON Type | Internal Type | Default Value | Description                                |
| ---------- | :---------: | :-------: | :-------: | :-----------: | :-----------: | :----------------------------------------- |
| `DomainID` |    `New`    |   `No`    | `string`  |   `HASH256`   |     None      | The ID of the `PermissionedDomain` object. |

#### 3.1.1.2. Failure Conditions

- The `PermissionedDomain(DomainID)` object does not exist on the ledger.

#### 3.1.1.3. State Changes

- No additional state changes are made to the ledger.

#### 3.1.1.4. Example

```js
{
  "TransactionType": "MPTokenIssuanceCreate",
  "Account": "rajgkBmMxmz161r8bWYH7CQAFZP5bA9oSG",
  "AssetScale": "2", // <-- Divisible into 100 units / 10^2
  "MaximumAmount": "100000000", //  <-- 100,000,000
  "Flags": 66, // <-- tfMPTCanLock and tfMPTCanClawback
  "MPTokenMetadata": "464F4F", // <-- "FOO" (HEX)
  "Fee": 10,
  "DomainID": "ASOHFiufiuewfviwuisdvubiuwb"
}
```

### 3.1.2. `MPTokenIssuanceSet` Transaction

This section outlines changes made to the `MPTokenIssuanceSet` transaction. In summary, the specification adds a new `DomainID` field to the transaction.

#### 3.1.2.1. Fields

| Field Name | Change Type | Required? | JSON Type | Internal Type | Default Value | Description                                |
| ---------- | :---------: | :-------: | :-------: | :-----------: | :-----------: | :----------------------------------------- |
| `DomainID` |    `New`    |   `No`    | `string`  |   `HASH256`   |     None      | The ID of the `PermissionedDomain` object. |

#### 3.1.2.2. Failure Conditions

- The `PermissionedDomain(DomainID)` object does not exist on the ledger.
- If the ` MPTokenIssuance.lsfMPTRequireAuth` flag is NOT set and `DomainID` is provided (a Domain cannot be added to a public Multi-Purpose Token). 

#### 3.1.2.3. State Changes

- Update the `MPTokenIssuance.DomainID` field.

#### 3.1.1.4. Example

```js
{
  "TransactionType": "MPTokenIssuanceSet",
  "Fee": 10,
  "MPTokenIssuanceID": "000004C463C52827307480341125DA0577DEFC38405B0E3E",
  "Flags": 1,
  "DomainID": "ASOHFiufiuewfviwuisdvubiuwb"
}
```


## 3.2. `MPToken` Transactions

### 3.2.1.`MPTokenAuthorize` Transaction

#### 3.2.1.1. Fields

This change does not introduce additional fields.

#### 3.2.1.2. Failure Conditions

This change does not introduce additional failure conditions.

#### 3.2.1.3. State Changes

- If the `MPTokenIssuance(MPTokenIssuanceID).DomainID` field is set:
  - Set the `lsftMPTDomainCheck` flag to the newly created `MPToken` object.

## 3.3. Other Transactions

### 3.3.1. `Payment` Transaction

The following changes are made to the payment transaction.

#### 3.3.1.1. Fields

This change does not introduce additional fields.

#### 3.3.1.2. Failure Conditions

- If `Payment.Amount` is an `MPT` and `MPTokenIssuance(Amount.MPTIssuanceID).DomainID` is set:
  - The `PermissionedDomain(MPTokenIssuance(Amount.MPTIssuanceID).DomainID)` object does not exist (the PermissionedDomain was deleted).
  - The `Payment.Account` account does not have Credentials accepted by the `PermissionedDomain` and:
    - The `MPToken` object of the `Payment.Account` account does not have the `lsfMPTAuthorized` flag set.
  - The `Payment.Destination` account does not have Credentials accepted by the `PermissionedDomain` and:
    - The `MPToken` object of the `Payment.Destination` account does not have the `lsfMPTAuthorized` flag set.

#### 3.3.1.3. State Changes

This change does not introduce additional state changes.

# Appendix

## A-1 F.A.Q

### A-1.1. Why does `MPTokenIssuance` use `PermissionedDomain`?

`PermissionedDomain` provides a less granular authorization mechanism to hold the `MPT`. Any account can hold the `MPT` as long as it has credentials issued by an Issuer accepted in the `PermissionedDomain`; in case the credentials expire or are revoked by the Credential Issuer, the holder can only transfer them back to the `MPT` Issuer and may not receive `MPTs`.

#### A-1.2. What happens when `MPTokenIssuace` uses `PermissionedDomain` and explicit authorization to hold an asset in the `MPToken` object?

Authorization is treated as a union. I.e. as long as the account has permission (either via `PermissionedDomain` of explicit authorization captured by the `MPToken.lsfMPTAuthorized` flag), it will be able to send and receive the `MPT`.
