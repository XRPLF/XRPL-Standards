<pre>
Title:       <b>Token Pre-Authorization</b>
Revision:    <b>1</b> (2024-12-11)

Author:      <a href="mailto:mvadari@ripple.com">Mayukha Vadari</a>

Affiliation: <a href="https://ripple.com">Ripple</a>
</pre>

# Token Pre-Authorization

## Abstract

Managing the authorization of tokens on the XRP Ledger is a complex task. This complexity is compounded when issuers use highly secure, locked-up keys, as frequent interactions to authorize trustlines or MPT holders can undermine the security benefits of these keys. Each authorization requires deliberate action by the issuer, making it impractical at scale and creating friction for both issuers and token holders. Without a streamlined mechanism to pre-approve or manage token authorizations efficiently, issuers face a tradeoff between operational efficiency and maintaining the security and decentralization principles of the ledger. This gap underscores the need for a robust solution that streamlines and simplifies the operational overhead of token authorization while preserving the integrity of issuer keys.

This spec proposes a solution to this problem by allowing issuers to pre-authorize token holders, either by authorizing specific accounts or by authorizing certain credentials/domains (which essentially allows them to move the burden of authorization to another account). By integrating token pre-authorization into the XRPL's existing trustline and MPT frameworks, issuers can establish robust controls over token distribution while maintaining a user-friendly process for holders. This allows issuers to manage their assets more effectively without compromising on security.

## 1. Overview

This feature mirrors the Deposit Authorization functionality, but for token authorization instead of payments.

We propose:

- Creating a `TokenPreauth` ledger object
- Creating a `TokenPreauth` transaction type
- Modifying the `TrustSet` transaction type
- Modifying the `MPTokenAuthorize` transaction type

This feature will require an amendment, tentatively titled `TokenPreauth`. It also depends on [XLS-70d, On-Chain Credentials](https://github.com/XRPLF/XRPL-Standards/tree/master/XLS-0070d-credentials) and [XLS-80d, Permissioned Domains](https://github.com/XRPLF/XRPL-Standards/tree/master/XLS-0080d-permissioned-domains) (though it can be adjusted to avoid those dependencies).

### 1.1. Background: Authorized Trustlines

[Authorized trustlines](https://xrpl.org/docs/concepts/tokens/fungible-tokens/authorized-trust-lines) allow issuers to control who can hold their issued tokens. By enabling the `RequireAuth` flag on their account, an issuer can enforce a policy where trustlines to that issuer must be explicitly authorized before any tokens can be held. Once authorized, the trustline functions as "normal" and the token holder can send, receive, or hold the issuer's tokens, subject to the usual rules of trustline limits and balances.

However, approving each trustline requires a signed `TrustSet` transaction from the issuer for each trustline to authorize.

### 1.2. Background: Authorized MPTs

Authorized MPTs function very similarly to authorized trustlines. The main differences are that the `RequireAuth` flag lives on the `MPTokenIssuance` object instead of the account object, and the `MPTokenAuthorize` transaction is used to authorize tokens instead.

## 2. On-Ledger Object: `TokenPreauth`

This object mirrors the `DepositPreauth` object post-XLS-70d in fields.

### 2.1. Fields

The fields of this object mirror the fields of `DepositPreauth`, including changes made in XLS-70d.

| Field Name          | Required? | JSON Type | Internal Type | Description                                                                                                                                                                                                                                                                                  |
| ------------------- | --------- | --------- | ------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `LedgerEntryType`   | ✔️        | `string`  | `UInt16`      | The ledger object's type (`TokenPreauth`).                                                                                                                                                                                                                                                   |
| `Account`           | ✔️        | `string`  | `AccountID`   | The account that granted the preauthorization (the issuer).                                                                                                                                                                                                                                  |
| `Currency`          |           | `string`  | `Currency`    | The currency code of an IOU, to apply this pre-authorization to only one token.                                                                                                                                                                                                              |
| `MPTokenIssuanceID` |           | `string`  | `UInt192`     | The ID of an MPToken issuance, to apply this pre-authorization to only one token.                                                                                                                                                                                                            |
| `Holder`            |           | `string`  | `AccountID`   | The account that received the preauthorization (the other end of the trustline, or the MPToken holder).                                                                                                                                                                                      |
| `Credentials`       |           | `array`   | `STArray`     | The credential(s) that received the preauthorization. (Any account with these credentials can send pre-authorized payments).                                                                                                                                                                 |
| `DomainID`          |           | `string`  | `Hash256`     | The domain that received the preauthorization. (Any account that is a member of this domain can send pre-authorized payments).                                                                                                                                                               |
| `OwnerNode`         | ✔️        | `string`  | `UInt64`      | A hint indicating which page of the sender's owner directory links to this object, in case the directory consists of multiple pages. Note: The object does not contain a direct link to the owner directory containing it, since that value can be derived from the `Account.PreviousTxnID`. |
| `PreviousTxnID`     | ✔️        | `string`  | `Hash256`     | The identifying hash of the transaction that most recently modified this object.                                                                                                                                                                                                             |
| `PreviousTxnLgrSeq` | ✔️        | `number`  | `UInt32`      | The index of the ledger that contains the transaction that most recently modified this object.                                                                                                                                                                                               |

#### 2.1.1. Object ID

The ID of this object will be a hash of the `Account` and either the `Holder`, `Credentials`, or `DomainID` fields (whichever of those fields is included in the object), combined with the unique space key for `TokenPreauth` objects, which will be defined during implementation.

If a `Currency` or `MPTokenIssuanceID` is included, that will also be included in the hash.

### 2.2. Account Deletion

The `TokenPreauth` object is not a [deletion blocker](https://xrpl.org/docs/concepts/accounts/deleting-accounts/#requirements).

## 3. Transaction: `TokenPreauth`

This transaction mirrors the `DepositPreauth` transaction post-XLS-70d in fields.

### 3.1. Fields

| Field Name          | Required? | JSON Type | Internal Type | Description                                                                       |
| ------------------- | --------- | --------- | ------------- | --------------------------------------------------------------------------------- |
| `Flags`             |           | `number`  | `UInt32`      | The supported flags on this transaction.                                          |
| `Currency`          |           | `string`  | `Currency`    | The currency code of an IOU, to apply this pre-authorization to only one token.   |
| `MPTokenIssuanceID` |           | `string`  | `UInt192`     | The ID of an MPToken issuance, to apply this pre-authorization to only one token. |
| `Holder`            |           | `string`  | `AccountID`   | The XRP Ledger address of the sender to preauthorize (or un-preauthorize).        |
| `Credentials`       |           | `array`   | `STArray`     | The credential(s) to preauthorize (or un-preauthorize).                           |
| `DomainID`          |           | `string`  | `Hash256`     | The domain to preauthorize (or un-preauthorize).                                  |

**Exactly one of** the `Holder`, `Credentials`, and `DomainID` fields must be included.

#### 3.1.1. `Flags`

| Flag Name       | Hex Value    | Description                                                                                                                                                                                        |
| --------------- | ------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `tfUnauthorize` | `0x00000001` | If set, it indicates that the issuer no longer wants to pre-authorize that holder/credential set/domain. The `TokenPreauth` object will be deleted as a result (if the transaction is successful). |

#### 3.1.2. `Currency` and `MPTokenIssuanceID`

At most one of these fields can be provided.

If either `Currency` or `MPTokenIssuanceID` is provided, then this pre-authorization will only apply to that token.

### 3.2. Failure Conditions

- None or more than one of `Holder`, `Credentials`, and `DomainID` are included (i.e. there must be exactly one of these fields included).
- The account doesn't have enough reserve for the new `TokenPreauth` object, if authorizing a new account/credential/domain.
- If authorizing/unauthorizing an account:
  - The account doesn't exist.
  - If the `tfUnauthorize` flag is set, the account is not currently authorized.
  - If the `tfUnauthorize` flag is unset:
    - The account to be authorized is already authorized.
  - The account is trying to authorize itself.
- If authorizing/unauthorizing a credential:
  - The issuer of a credential doesn't exist.
  - The array is too long (i.e. has more than 8 credentials).
  - The array is empty (i.e. has no credentials).
  - If the `tfUnauthorize` flag is set, the credentials are not currently authorized.
  - If the `tfUnauthorize` flag is unset, the credentials are already authorized.
- If authorizing/unauthorizing a domain:
  - The domain doesn't exist.
  - If the `tfUnauthorize` flag is set, the domain is not currently authorized.
  - If the `tfUnauthorize` flag is unset, the domain is already authorized.
- The MPT represented by `MPTokenIssuanceID` isn't issued by `Account`.

### 3.3. State Changes

If authorizing:

- A new `TokenPreauth` object is created, with the provided fields.

If unauthorizing:

- The relevant `TokenPreauth` object is deleted.

## 4. Transaction: `TrustSet`

The [`TrustSet` transaction](https://xrpl.org/trustset.html) already exists on the XRPL. We propose a slight modification to support token pre-authorization.

### 4.1. Fields

<details>
<summary>

As a reference, [here](https://xrpl.org/docs/references/protocol/transactions/types/trustset#trustset-fields) are the fields that the `TrustSet` transaction currently has.

</summary>

| Field Name             | Required? | JSON Type | Internal Type       | Description                                                                                     |
| ---------------------- | --------- | --------- | ------------------- | ----------------------------------------------------------------------------------------------- |
| `LimitAmount`          | ✔️        | `object`  | `Amount`            | Object defining the trust line to create or modify.                                             |
| `LimitAmount.currency` | ✔️        | `string`  | (`Amount.currency`) | The currency to this trust line applies to.                                                     |
| `LimitAmount.value`    | ✔️        | `string`  | (`Amount.value`)    | The limit to set on this trust line.                                                            |
| `LimitAmount.issuer`   | ✔️        | `string`  | (`Amount.issuer`)   | The address of the account to extend trust to.                                                  |
| `QualityIn`            |           | `number`  | `UInt32`            | Value incoming balances on this trust line at the ratio of this number per 1,000,000,000 units. |
| `QualityOut`           |           | `number`  | `UInt32`            | Value outgoing balances on this trust line at the ratio of this number per 1,000,000,000 units. |

</details>

We propose these additions:
| Field Name | Required? | JSON Type | Internal Type | Description |
|------------|-----------|-----------|---------------|-------------|
|`CredentialIDs`| |`array`|`Vector256`|Credential(s) to attach to the transaction.|
|`DomainID`| |`string`|`Hash256`|A domain to attach to the transaction.|

**No more than one of** the `CredentialIDs` and `DomainID` fields must be included.

### 4.2. Failure Conditions

- Existing failure conditions for `TrustSet` will still be obeyed.
- Both `CredentialIDs` and `DomainID` are included.
- If `CredentialIDs` is included:
  - Any of the `CredentialIDs`:
    - Isn't an object that exists.
    - Isn't a `Credential` object.
    - Is an expired `Credential` object.
    - Has not been accepted.
    - Isn't a credential issued to the `Account` sending the transaction.
  - The group of `CredentialIDs` is not authorized by the destination (or isn't authorized for this token).
  - There are duplicates in the list of `CredentialIDs`.
- If `DomainID` is included:
  - The domain doesn't exist.
  - The object in the `DomainID` field is not a domain.
  - The account is not a member of the domain.
  - The `DomainID` is not authorized by the destination (or isn't authorized for this token).

### 4.3. State Changes

If the issuer has the `lsfRequireAuth` flag set, and the user is pre-authorizedin some way (either themselves or via credentials/domains), the `lsfLowAuth`/`lsfHighAuth` flag on the trustline will be enabled. This will be true even when editing an existing trustline, not just when creating a new one.

## 5. Transaction: `MPTokenAuthorize`

The [`MPTokenAuthorize` transaction](https://opensource.ripple.com/docs/xls-33d-multi-purpose-tokens/reference/mptokenauthorize) already exists on the XRPL - it is the transaction that allows an account to opt-in to holding a token, and also can be used by issuers who have authorization turned on to approve token holders.

We propose a slight modification to support token pre-authorization.

### 5.1. Fields

<details>
<summary>

As a reference, [here](https://opensource.ripple.com/docs/xls-33d-multi-purpose-tokens/reference/mptokenauthorize) are the fields that the `MPTokenAuthorize` transaction currently has.

</summary>

| Field Name          | Required? | JSON Type | Internal Type | Description                                                                                                                                                        |
| ------------------- | --------- | --------- | ------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `Account`           | ✔️        | `string`  | `AccountID`   | This address can indicate either an issuer or a potential holder of an MPT.                                                                                        |
| `TransactionType`   | ✔️        | `object`  | `UInt16`      | Indicates the new transaction type MPTokenAuthorize. The integer value is 29.                                                                                      |
| `MPTokenIssuanceID` | ✔️        | `string`  | `UInt256`     | Indicates the ID of the MPT involved.                                                                                                                              |
| `MPTokenHolder`     |           | `string`  | `AccountID`   | (Optional) Specifies the holder's address that the issuer wants to authorize. Only used for authorization/allow-listing; must be empty if submitted by the holder. |
| `Flags`             |           | `string`  | `UInt32`      | Transaction-specific bitwise flags.                                                                                                                                |

</details>

We propose these additions:
| Field Name | Required? | JSON Type | Internal Type | Description |
|------------|-----------|-----------|---------------|-------------|
|`CredentialIDs`| |`array`|`Vector256`|Credential(s) to attach to the transaction.|
|`DomainID`| |`string`|`Hash256`|A domain to attach to the transaction.|

**No more than one of** the `CredentialIDs` and `DomainID` fields must be included.

### 5.2. Failure Conditions

- Existing failure conditions for `MPTokenAuthorize` will still be obeyed.
- Both `CredentialIDs` and `DomainID` are included.
- If `CredentialIDs` is included:
  - Any of the `CredentialIDs`:
    - Isn't an object that exists.
    - Isn't a `Credential` object.
    - Is an expired `Credential` object.
    - Has not been accepted.
    - Isn't a credential issued to the `Account` sending the transaction.
  - The group of `CredentialIDs` is not authorized by the destination (or isn't authorized for this token).
  - There are duplicates in the list of `CredentialIDs`.
- If `DomainID` is included:
  - The domain doesn't exist.
  - The object in the `DomainID` field is not a domain.
  - The account is not a member of the domain.
  - The `DomainID` is not authorized by the destination (or isn't authorized for this token).

### 5.3. State Changes

If the issuer has the `lsfMPTRequireAuth` flag set, and the user is pre-authorized in some way (either themselves or via credentials/domains), the `lsfMPTAuthorized` flag on the `MPToken` object will be enabled. This will be true even when editing an existing `MPToken`, not just when creating a new one.

## 6. Examples

In this example, Rowan is an RWA issuer, and there are certain legal criteria that must be met before a customer can hold his token (for example, they may need to be an accredited investor). A trusted issuer, Isabel, is issuing a credential that indicates that Alice meets these criteria.

### 6.1. `TokenPreauth` Transaction

Note: Rowan already has the `lsfRequireAuth` flag set on his account and the `lsfMPTRequireAuth` flag set on his `MPTokenIssuance`.

```typescript
{
    TransactionType: "TokenPreauth",
    Account: "rOWAN....",
    Credentials: [
        {
            Credential: {
                Issuer: "rISABEL......",
                CredentialType: "4B5943"
            }
        }
    ]
}
```

### 6.2. `TokenPreauth` Ledger Object

```typescript
{
    LedgerEntryType: "TokenPreauth",
    Account: "rOWAN....",
    Credentials: [
        {
            Credential: {
                Issuer: "rISABEL......",
                CredentialType: "4B5943"
            }
        }
    ]
}
```

### 6.3. `TrustSet` Transaction

This transaction will result in Alice's trustline with Rowan automatically being authorized.

```typescript
{
    TransactionType: "TrustSet",
    Account: "rALICE......",
    LimitAmount: {
        currency: "RWA",
        issuer: "rOWAN....",
        value: "1000000000",
    }
    CredentialIDs: ["DD40031C6C21164E7673...17D467CEEE9"]
}
```

This transaction will succeed, but the trustline will remain unauthorized.

```typescript
{
    TransactionType: "TrustSet",
    Account: "rALICE......",
    LimitAmount: {
        currency: "RWA",
        issuer: "rOWAN....",
        value: "1000000000",
    }
}
```

This transaction will fail, since the attached credential isn't Bob's.

```typescript
{
    TransactionType: "TrustSet",
    Account: "rBOB......",
    LimitAmount: {
        currency: "RWA",
        issuer: "rOWAN....",
        value: "1000000000",
    }
    CredentialIDs: ["DD40031C6C21164E7673...17D467CEEE9"]
}
```

### 6.4. `MPTokenAuthorize`

This transaction will result in Alice being authorized to hold Rowan's RWA issuance.

```typescript
{
    TransactionType: "MPTokenAuthorize",
    Account: "rALICE......",
    MPTokenIssuanceID: "000005F398B624EBD06822198649C920C8B20ADB8EBE745E", // Rowan's RWA issuance
    CredentialIDs: ["DD40031C6C21164E7673...17D467CEEE9"]
}
```

This transaction will fail, since Alice didn't provide her credential. She can re-submit with the credential attached (like above).

```typescript
{
    TransactionType: "MPTokenAuthorize",
    Account: "rALICE......",
    MPTokenIssuanceID: "000005F398B624EBD06822198649C920C8B20ADB8EBE745E",
}
```

This transaction will fail, since the attached credential isn't Bob's.

```typescript
{
    TransactionType: "MPTokenAuthorize",
    Account: "rBOB......",
    MPTokenIssuanceID: "000005F398B624EBD06822198649C920C8B20ADB8EBE745E",
    CredentialIDs: ["DD40031C6C21164E7673...17D467CEEE9"]
}
```

## 7. Invariants

A `TokenPreauth` ledger object always has **exactly one** of the `Holder`, `Credentials`, and `DomainID` field, and has **at most one** of the `Currency` and `MPTokenIssuanceID` fields.

If the `Credentials` field is included, the array contains between 1 and 10 credentials.

## 8. Security

### 8.1. Trust Assumptions

Issuers need to trust a credential issuer to only be issuing valid credentials, and to not delete a credential without a legitimate reason.

Issuers need to trust a domain issuer to only be allowing legitimate credentials into their domain.

# Appendix

## Appendix A: FAQ

### A.1: Can I still authorize accounts that haven't been pre-authorized in any way?

Yes. The existing authorization flow will still work for those accounts.

### A.2: What will happen during existing authorization flows if a holder has been pre-authorized?

A holder will be authorized on trustline/`MPToken` creation, essentially. So attempting to re-authorize the holder will have the same effect as attempting to re-authorize a holder in existing flows.

### A.3: Why doesn't this use the existing [Deposit Auth](https://xrpl.org/docs/concepts/accounts/depositauth) flow?

This would be a problem for issuers who want to authorize token holders but don't want those token holders to be able to send funds to their address (for compliance reasons).
