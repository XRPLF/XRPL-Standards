<pre>
  xls: 87
  title: Token Pre-Authorization
  description: Allow issuers to pre-authorize token holders via accounts, credentials, or domains.
  author: Mayukha Vadari (@mvadari)
  category: Amendment
  status: Draft
  requires: XLS-70, XLS-80
  proposal-from: https://github.com/XRPLF/XRPL-Standards/discussions/258
  created: 2024-12-11
  updated: 2026-02-24
</pre>

# Token Pre-Authorization

## 1. Abstract

Managing the authorization of tokens on the XRP Ledger is a complex task. This complexity is compounded when issuers use highly secure, locked-up keys, as frequent interactions to authorize trustlines or MPT holders can undermine the security benefits of these keys. Each authorization requires deliberate action by the issuer, making it impractical at scale and creating friction for both issuers and token holders. Without a streamlined mechanism to pre-approve or manage token authorizations efficiently, issuers face a tradeoff between operational efficiency and maintaining the security and decentralization principles of the ledger. This gap underscores the need for a robust solution that streamlines and simplifies the operational overhead of token authorization while preserving the integrity of issuer keys.

This spec proposes a solution to this problem by allowing issuers to pre-authorize token holders, either by authorizing specific accounts or by authorizing certain credentials/domains (which essentially allows them to move the burden of authorization to another account). By integrating token pre-authorization into the XRPL's existing trustline and MPT frameworks, issuers can establish robust controls over token distribution while maintaining a user-friendly process for holders. This allows issuers to manage their assets more effectively without compromising on security.

## 2. Motivation

### 2.1. Background: Authorized Trustlines

[Authorized trustlines](https://xrpl.org/docs/concepts/tokens/fungible-tokens/authorized-trust-lines) allow issuers to control who can hold their issued tokens. By enabling the `RequireAuth` flag on their account, an issuer can enforce a policy where trustlines to that issuer must be explicitly authorized before any tokens can be held. Once authorized, the trustline functions as "normal" and the token holder can send, receive, or hold the issuer's tokens, subject to the usual rules of trustline limits and balances.

However, approving each trustline requires a signed `TrustSet` transaction from the issuer for each trustline to authorize.

### 2.2. Background: Authorized MPTs

Authorized MPTs function very similarly to authorized trustlines. The main differences are that the `RequireAuth` flag lives on the `MPTokenIssuance` object instead of the account object, and the `MPTokenAuthorize` transaction is used to authorize tokens instead.

### 2.3. Overview

This feature mirrors the Deposit Authorization functionality, but for token authorization instead of payments.

We propose:

- Creating a `TokenPreauth` ledger object
- Creating a `TokenPreauth` transaction type
- Modifying the `TrustSet` transaction type
- Modifying the `MPTokenAuthorize` transaction type

This feature will require an amendment, tentatively titled `TokenPreauth`. It also depends on [XLS-70, On-Chain Credentials](../XLS-0070-credentials/README.md) and [XLS-80, Permissioned Domains](../XLS-0080-permissioned-domains/README.md) (though it can be adjusted to avoid those dependencies).

## 3. Ledger Entry: `TokenPreauth`

This object mirrors the `DepositPreauth` object post-XLS-70 in fields.

### 3.1. Object Identifier

**Key Space:** `0x[TBD]`

**ID Calculation Algorithm:**
The ID of this object will be a hash of the `Account` and either the `Holder`, `Credentials`, or `DomainID` fields (whichever of those fields is included in the object), combined with the unique space key for `TokenPreauth` objects, which will be defined during implementation.

If a `Currency` or `MPTokenIssuanceID` is included, that will also be included in the hash.

### 3.2. Fields

The fields of this object mirror the fields of `DepositPreauth`, including changes made in XLS-70.

| Field Name          | Constant | Required?   | Internal Type | Default Value  | Description                                                                                                                                                                                                                                                                                  |
| ------------------- | -------- | ----------- | ------------- | -------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `LedgerEntryType`   | Yes      | Yes         | UINT16        | `TokenPreauth` | Identifies this as a `TokenPreauth` object.                                                                                                                                                                                                                                                  |
| `Account`           | No       | Yes         | ACCOUNT       | N/A            | The account that granted the preauthorization (the issuer).                                                                                                                                                                                                                                  |
| `Currency`          | No       | Conditional | CURRENCY      | N/A            | The currency code of an IOU, to apply this pre-authorization to only one token.                                                                                                                                                                                                              |
| `MPTokenIssuanceID` | No       | Conditional | UINT192       | N/A            | The ID of an MPToken issuance, to apply this pre-authorization to only one token.                                                                                                                                                                                                            |
| `Holder`            | No       | Conditional | ACCOUNT       | N/A            | The account that received the preauthorization (the other end of the trustline, or the MPToken holder).                                                                                                                                                                                      |
| `Credentials`       | No       | Conditional | STARRAY       | N/A            | The credential(s) that received the preauthorization. (Any account with these credentials can send pre-authorized payments).                                                                                                                                                                 |
| `DomainID`          | No       | Conditional | HASH256       | N/A            | The domain that received the preauthorization. (Any account that is a member of this domain can send pre-authorized payments).                                                                                                                                                               |
| `OwnerNode`         | No       | Yes         | UINT64        | N/A            | A hint indicating which page of the sender's owner directory links to this object, in case the directory consists of multiple pages. Note: The object does not contain a direct link to the owner directory containing it, since that value can be derived from the `Account.PreviousTxnID`. |
| `PreviousTxnID`     | No       | Yes         | HASH256       | N/A            | The identifying hash of the transaction that most recently modified this object.                                                                                                                                                                                                             |
| `PreviousTxnLgrSeq` | No       | Yes         | UINT32        | N/A            | The index of the ledger that contains the transaction that most recently modified this object.                                                                                                                                                                                               |

**Exactly one of** the `Holder`, `Credentials`, and `DomainID` fields must be included. **At most one of** `Currency` and `MPTokenIssuanceID` may be included.

### 3.3. Ownership

**Owner:** `Account`

**Directory Registration:** This object is registered in the owner's directory.

### 3.4. Reserves

**Reserve Requirement:** Standard

This ledger entry requires the standard owner reserve increment (currently 0.2 XRP, subject to Fee Voting changes).

### 3.5. Deletion

**Deletion Transactions:** `TokenPreauth`

**Deletion Conditions:**

- The `tfUnauthorize` flag is set on the `TokenPreauth` transaction.

**Account Deletion Blocker:** No

The `TokenPreauth` object is not a [deletion blocker](https://xrpl.org/docs/concepts/accounts/deleting-accounts/#requirements).

### 3.6. Invariants

- A `TokenPreauth` ledger object always has **exactly one** of the `Holder`, `Credentials`, and `DomainID` fields.
- A `TokenPreauth` ledger object has **at most one** of the `Currency` and `MPTokenIssuanceID` fields.
- If the `Credentials` field is included, the array contains between 1 and 10 credentials.

### 3.7. RPC Name

**RPC Type Name:** `token_preauth`

### 3.8. Example JSON

```json
{
  "LedgerEntryType": "TokenPreauth",
  "Account": "rOWAN....",
  "Credentials": [
    {
      "Credential": {
        "Issuer": "rISABEL......",
        "CredentialType": "4B5943"
      }
    }
  ],
  "OwnerNode": "0000000000000000",
  "PreviousTxnID": "DD40031C6C21164E7673...17D467CEEE9",
  "PreviousTxnLgrSeq": 12345678
}
```

## 4. Transaction: `TokenPreauth`

This transaction mirrors the `DepositPreauth` transaction post-XLS-70 in fields.

### 4.1. Fields

| Field Name          | Required?   | JSON Type | Internal Type | Default Value  | Description                                                                       |
| ------------------- | ----------- | --------- | ------------- | -------------- | --------------------------------------------------------------------------------- |
| `TransactionType`   | Yes         | string    | UINT16        | `TokenPreauth` | Identifies this as a `TokenPreauth` transaction.                                  |
| `Currency`          | Conditional | string    | CURRENCY      | N/A            | The currency code of an IOU, to apply this pre-authorization to only one token.   |
| `MPTokenIssuanceID` | Conditional | string    | UINT192       | N/A            | The ID of an MPToken issuance, to apply this pre-authorization to only one token. |
| `Holder`            | Conditional | string    | ACCOUNT       | N/A            | The XRP Ledger address of the sender to preauthorize (or un-preauthorize).        |
| `Credentials`       | Conditional | array     | STARRAY       | N/A            | The credential(s) to preauthorize (or un-preauthorize).                           |
| `DomainID`          | Conditional | string    | HASH256       | N/A            | The domain to preauthorize (or un-preauthorize).                                  |

**Exactly one of** the `Holder`, `Credentials`, and `DomainID` fields must be included.

**At most one of** `Currency` and `MPTokenIssuanceID` may be included. If either is provided, then this pre-authorization will only apply to that token.

### 4.2. Flags

| Flag Name       | Flag Value   | Description                                                                                                                                                                                        |
| --------------- | ------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `tfUnauthorize` | `0x00000001` | If set, it indicates that the issuer no longer wants to pre-authorize that holder/credential set/domain. The `TokenPreauth` object will be deleted as a result (if the transaction is successful). |

### 4.3. Transaction Fee

**Fee Structure:** Standard

This transaction uses the standard transaction fee (currently 10 drops, subject to Fee Voting changes).

### 4.4. Failure Conditions

##### 3.2.4.1. Data Verification

1. None or more than one of `Holder`, `Credentials`, and `DomainID` are included (`temMALFORMED`)
2. Both `Currency` and `MPTokenIssuanceID` are included (`temMALFORMED`)
3. The `Credentials` array is empty (`temMALFORMED`)
4. The `Credentials` array has more than 8 credentials (`temMALFORMED`)

##### 3.2.4.2. Protocol-Level Failures

1. The account doesn't have enough reserve for the new `TokenPreauth` object, if authorizing a new account/credential/domain (`tecINSUFFICIENT_RESERVE`)
2. If authorizing/unauthorizing an account:
   1. The account doesn't exist (`tecNO_DST`)
   1. If the `tfUnauthorize` flag is set, the account is not currently authorized (`tecNO_ENTRY`)
   1. If the `tfUnauthorize` flag is unset, the account to be authorized is already authorized (`tecDUPLICATE`)
   1. The account is trying to authorize itself (`tecNO_PERMISSION`)
3. If authorizing/unauthorizing a credential:
   1. The issuer of a credential doesn't exist (`tecNO_ISSUER`)
   1. If the `tfUnauthorize` flag is set, the credentials are not currently authorized (`tecNO_ENTRY`)
   1. If the `tfUnauthorize` flag is unset, the credentials are already authorized (`tecDUPLICATE`)
4. If authorizing/unauthorizing a domain:
   1. The domain doesn't exist (`tecNO_ENTRY`)
   1. If the `tfUnauthorize` flag is set, the domain is not currently authorized (`tecNO_ENTRY`)
   1. If the `tfUnauthorize` flag is unset, the domain is already authorized (`tecDUPLICATE`)
5. The MPT represented by `MPTokenIssuanceID` isn't issued by `Account` (`tecNO_PERMISSION`)

### 4.5. State Changes

**On Success (`tesSUCCESS`):**

If authorizing (no flags set):

- A new `TokenPreauth` object is created, with the provided fields.

If unauthorizing (`tfUnauthorize` flag set):

- The relevant `TokenPreauth` object is deleted.

### 4.6. Example JSON

```json
{
  "TransactionType": "TokenPreauth",
  "Account": "rOWAN....",
  "Credentials": [
    {
      "Credential": {
        "Issuer": "rISABEL......",
        "CredentialType": "4B5943"
      }
    }
  ],
  "Fee": "10",
  "Sequence": 12345
}
```

## 5. Transaction: `TrustSet` (Modified)

The [`TrustSet` transaction](https://xrpl.org/trustset.html) already exists on the XRPL. We propose a slight modification to support token pre-authorization.

### 5.1. Fields

For reference, see the [existing TrustSet fields](https://xrpl.org/docs/references/protocol/transactions/types/trustset#trustset-fields).

The following fields are added to the existing `TrustSet` transaction:

| Field Name      | Required? | JSON Type | Internal Type | Default Value | Description                                 |
| --------------- | --------- | --------- | ------------- | ------------- | ------------------------------------------- |
| `CredentialIDs` | No        | array     | VECTOR256     | N/A           | Credential(s) to attach to the transaction. |
| `DomainID`      | No        | string    | HASH256       | N/A           | A domain to attach to the transaction.      |

**At most one of** the `CredentialIDs` and `DomainID` fields may be included.

### 5.2. Failure Conditions

##### 3.3.2.1. Data Verification

1. Both `CredentialIDs` and `DomainID` are included (`temMALFORMED`)

##### 3.3.2.2. Protocol-Level Failures

All existing failure conditions for `TrustSet` still apply. Additional failure conditions:

1. If `CredentialIDs` is included:
   1. Any of the `CredentialIDs` isn't an object that exists (`tecNO_ENTRY`)
   1. Any of the `CredentialIDs` isn't a `Credential` object (`tecNO_ENTRY`)
   1. Any of the `CredentialIDs` is an expired `Credential` object (`tecEXPIRED`)
   1. Any of the `CredentialIDs` has not been accepted (`tecNO_PERMISSION`)
   1. Any of the `CredentialIDs` isn't a credential issued to the `Account` sending the transaction (`tecNO_PERMISSION`)
   1. The group of `CredentialIDs` is not authorized by the destination (or isn't authorized for this token) (`tecNO_PERMISSION`)
   1. There are duplicates in the list of `CredentialIDs` (`temMALFORMED`)
2. If `DomainID` is included:
   1. The domain doesn't exist (`tecNO_ENTRY`)
   1. The object in the `DomainID` field is not a domain (`tecNO_ENTRY`)
   1. The account is not a member of the domain (`tecNO_PERMISSION`)
   1. The `DomainID` is not authorized by the destination (or isn't authorized for this token) (`tecNO_PERMISSION`)

### 5.3. State Changes

**On Success (`tesSUCCESS`):**

If the issuer has the `lsfRequireAuth` flag set, and the user is pre-authorized in some way (either themselves or via credentials/domains), the `lsfLowAuth`/`lsfHighAuth` flag on the trustline will be enabled. This will be true even when editing an existing trustline, not just when creating a new one.

### 5.4. Example JSON

```json
{
  "TransactionType": "TrustSet",
  "Account": "rALICE......",
  "LimitAmount": {
    "currency": "RWA",
    "issuer": "rOWAN....",
    "value": "1000000000"
  },
  "CredentialIDs": ["DD40031C6C21164E7673...17D467CEEE9"],
  "Fee": "10",
  "Sequence": 12345
}
```

## 6. Transaction: `MPTokenAuthorize` (Modified)

The [`MPTokenAuthorize` transaction](https://xrpl.org/docs/references/protocol/transactions/types/mptokenauthorize) already exists on the XRPL - it is the transaction that allows an account to opt-in to holding a token, and also can be used by issuers who have authorization turned on to approve token holders.

We propose a slight modification to support token pre-authorization.

### 6.1. Fields

For reference, see the [existing MPTokenAuthorize fields](https://xrpl.org/docs/references/protocol/transactions/types/mptokenauthorize#mptokenauthorize-fields).

The following fields are added to the existing `MPTokenAuthorize` transaction:

| Field Name      | Required? | JSON Type | Internal Type | Default Value | Description                                 |
| --------------- | --------- | --------- | ------------- | ------------- | ------------------------------------------- |
| `CredentialIDs` | No        | array     | VECTOR256     | N/A           | Credential(s) to attach to the transaction. |
| `DomainID`      | No        | string    | HASH256       | N/A           | A domain to attach to the transaction.      |

**At most one of** the `CredentialIDs` and `DomainID` fields may be included.

### 6.2. Failure Conditions

##### 3.4.2.1. Data Verification

1. Both `CredentialIDs` and `DomainID` are included (`temMALFORMED`)

##### 3.4.2.2. Protocol-Level Failures

All existing failure conditions for `MPTokenAuthorize` still apply. Additional failure conditions:

1. If `CredentialIDs` is included:
   1. Any of the `CredentialIDs` isn't an object that exists (`tecNO_ENTRY`)
   1. Any of the `CredentialIDs` isn't a `Credential` object (`tecNO_ENTRY`)
   1. Any of the `CredentialIDs` is an expired `Credential` object (`tecEXPIRED`)
   1. Any of the `CredentialIDs` has not been accepted (`tecNO_PERMISSION`)
   1. Any of the `CredentialIDs` isn't a credential issued to the `Account` sending the transaction (`tecNO_PERMISSION`)
   1. The group of `CredentialIDs` is not authorized by the destination (or isn't authorized for this token) (`tecNO_PERMISSION`)
   1. There are duplicates in the list of `CredentialIDs` (`temMALFORMED`)
2. If `DomainID` is included:
   1. The domain doesn't exist (`tecNO_ENTRY`)
   1. The object in the `DomainID` field is not a domain (`tecNO_ENTRY`)
   1. The account is not a member of the domain (`tecNO_PERMISSION`)
   1. The `DomainID` is not authorized by the destination (or isn't authorized for this token) (`tecNO_PERMISSION`)

### 6.3. State Changes

**On Success (`tesSUCCESS`):**

If the issuer has the `lsfMPTRequireAuth` flag set, and the user is pre-authorized in some way (either themselves or via credentials/domains), the `lsfMPTAuthorized` flag on the `MPToken` object will be enabled. This will be true even when editing an existing `MPToken`, not just when creating a new one.

### 6.4. Example JSON

```json
{
  "TransactionType": "MPTokenAuthorize",
  "Account": "rALICE......",
  "MPTokenIssuanceID": "000005F398B624EBD06822198649C920C8B20ADB8EBE745E",
  "CredentialIDs": ["DD40031C6C21164E7673...17D467CEEE9"],
  "Fee": "10",
  "Sequence": 12345
}
```

## 7. Rationale

This feature mirrors the existing Deposit Authorization functionality, but applies it to token authorization instead of payments. This design decision was made for several reasons:

1. **Familiarity**: Developers and issuers already familiar with Deposit Authorization will find this feature intuitive.
2. **Separation of concerns**: Token authorization is distinct from payment authorization. Issuers may want to authorize token holders without allowing those holders to send funds directly to their address (for compliance reasons).
3. **Flexibility**: By supporting accounts, credentials, and domains, issuers can choose the level of delegation that fits their use case.

The decision to require exactly one of `Holder`, `Credentials`, or `DomainID` ensures clarity in the authorization model and prevents ambiguous states.

## 8. Backwards Compatibility

This proposal introduces a new ledger object type (`TokenPreauth`) and a new transaction type (`TokenPreauth`), as well as modifications to existing transactions (`TrustSet` and `MPTokenAuthorize`).

**Backwards compatibility considerations:**

1. **New ledger object**: The `TokenPreauth` ledger object is entirely new and does not affect existing ledger entries.
2. **New transaction type**: The `TokenPreauth` transaction is new and will only be recognized after the amendment is enabled.
3. **Modified transactions**: The `TrustSet` and `MPTokenAuthorize` transactions gain optional fields (`CredentialIDs` and `DomainID`). Existing transactions without these fields will continue to work as before.
4. **Existing authorization flows**: The traditional manual authorization flow (issuer sends `TrustSet` or `MPTokenAuthorize` to authorize a specific holder) remains fully functional.

No breaking changes are introduced to existing functionality.

## 9. Test Plan

Testing should include:

1. **Unit tests** for the `TokenPreauth` transaction and ledger object creation/deletion.
2. **Integration tests** for the modified `TrustSet` and `MPTokenAuthorize` transactions with credential and domain-based pre-authorization.
3. **Negative tests** for all failure conditions specified in section 3.
4. **Edge cases** including:
   - Pre-authorizing an account that is later deleted
   - Using expired credentials
   - Domain membership changes after pre-authorization
   - Concurrent authorization attempts

## 10. Reference Implementation

_To be added when implementation is available._

## 11. Security Considerations

### 11.1. Trust Assumptions

Issuers need to trust a credential issuer to only be issuing valid credentials, and to not delete a credential without a legitimate reason.

Issuers need to trust a domain issuer to only be allowing legitimate credentials into their domain.

### 11.2. Credential Expiration

Pre-authorization via credentials is checked at the time of trustline/MPToken creation or modification. If a credential expires after authorization has been granted, the authorization remains valid. Issuers who want to revoke authorization when credentials expire must do so manually.

### 11.3. Reserve Requirements

The `TokenPreauth` object requires the standard owner reserve, which prevents spam attacks where malicious actors could create many pre-authorization objects.

# Appendix

## Appendix A: FAQ

### A.1: Can I still authorize accounts that haven't been pre-authorized in any way?

Yes. The existing authorization flow will still work for those accounts.

### A.2: What will happen during existing authorization flows if a holder has been pre-authorized?

A holder will be authorized on trustline/`MPToken` creation, essentially. So attempting to re-authorize the holder will have the same effect as attempting to re-authorize a holder in existing flows.

### A.3: Why doesn't this use the existing [Deposit Auth](https://xrpl.org/docs/concepts/accounts/depositauth) flow?

This would be a problem for issuers who want to authorize token holders but don't want those token holders to be able to send funds to their address (for compliance reasons).
