<pre>
  xls: 70
  title: On-Chain Credentials
  description: Issuance, storage, and verification of credentials directly on the XRP Ledger while supporting privacy needs
  author: Mayukha Vadari <mvadari@ripple.com>
  proposal-from: https://github.com/XRPLF/XRPL-Standards/discussions/202
  status: Final
  category: Amendment
  created: 2024-06-04
</pre>

# On-Chain Credentials

## Abstract

The XRPL DID (Digital Identifier) amendment ([XLS-40](https://github.com/XRPLF/XRPL-Standards/tree/master/XLS-0040-decentralized-identity)) empowers users to manage their digital identities on the XRP Ledger. While this amendment adds support for on-chain identity management and simplifies off-chain credential usage, maximizing blockchain technology's full potential for credential handling requires on-chain solutions.

This document proposes a design to bridge this gap. It outlines the issuance, storage, and verification of credentials directly on the XRP Ledger, while still supporting the privacy needs of users.

On-chain credentialing can streamline various processes within the XRPL ecosystem. For example, financial institutions can issue credentials on the XRP Ledger, attesting to a user's identity and compliance. This eliminates the need for repeated [KYC (Know Your Customer)](https://en.wikipedia.org/wiki/Know_your_customer) checks across different platforms, fostering a smoother user experience. By enabling secure credential management, this proposal unlocks the potential for a new wave of trust-based applications within the XRPL ecosystem.

## 1. Overview

This design adds support for creating, accepting, and deleting credentials. It also extends the existing [Deposit Authorization](https://xrpl.org/docs/concepts/accounts/depositauth) feature, allowing accounts to not only allowlist specific accounts, but also allowlist accounts with specific credentials.

This proposal only supports blocking the interactions that Deposit Authorization supports, such as direct payments. However, future proposals could add support for credential-gating in other parts of the XRPL, such as AMMs or lending pools.

We propose:

- Creating a `Credential` ledger object
- Creating a `CredentialCreate` transaction type
- Creating a `CredentialAccept` transaction type
- Creating a `CredentialDelete` transaction type
- Modifying the `DepositPreauth` ledger object
- Modifying the `DepositPreauth` transaction
- Modifying other transactions that are affected by Deposit Authorization

This feature will require an amendment, tentatively titled `Credentials`.

### 1.1. Background: DIDs and Verifiable Credentials (VCs)

A [verifiable credential](https://en.wikipedia.org/wiki/Verifiable_credentials) (VC), as defined by the [W3C specification](https://www.w3.org/TR/vc-data-model-2.0/), is a secure and tamper-evident way to represent information about a subject, such as an individual, organization, or even an IoT device. These credentials are issued by a trusted entity and can be verified by third parties without directly involving the issuer at all.

For a clearer understanding of the relationship between [DIDs (Decentralized Identifiers)](https://en.wikipedia.org/wiki/Decentralized_identifier) and VCs, consider the following analogy. A DID serves as a unique identifier for an entity, similar to a fingerprint or a photo of a person (their physical characteristics). In contrast, a VC acts as a verifiable piece of information associated with that DID, much like a driver's license or passport. When a third party needs to verify an identity claim, they can examine the VC presented by the entity and ensure it aligns with the corresponding DID (such as comparing the photo on a driver's license to the physical characteristics of the person to whom it supposedly belongs).

### 1.2. Terminology

- **Credential**: A representation of one or more assertions made by an issuer. For example, a passport is a representation of the assertion that a person is a citizen of a given country.
- **Issuer**: The account that creates (issues) the credential. For example, a passport is issued by a country's government.
- **Subject**: The account that the credential is issued to. For example, a passport is issued to a specific person.
- **Allowlist**: A list of accounts that are allowed to do a given action, or (if used as a verb) the action of adding an account to said list.
- **Preauthorization**: Essentially the same thing as allowlisting.

_Note: These definitions do not directly match the definitions listed in the [W3C Verifiable Credentials spec](https://www.w3.org/TR/vc-data-model-2.0/#terminology). These terms are used in a slightly different way in the context of this spec._

### 1.3. Basic Flow

This example scenario features three parties with different roles:

- Verity is a regulated business that wants to interact only with properly KYC'd accounts, to ensure legal compliance. This makes Verity an _authorizer_ or _verifier_ because they configure which accounts are allowed (authorized) to interact with them.
- Isabel is a credential issuer that vets accounts and issues credentials on-chain attesting that the accounts are who they say they are.
- Alice is a user who wants to interact with Verity.

The authorization flow in this scenario works as follows:

1. Verity sets up her account so that only authorized accounts can interact with it. Since she trusts Isabel to properly vet accounts and issue credentials attesting to that, she configures her account to accept credentials issued by Isabel.
2. Alice submits her KYC documents to Isabel privately, off-chain.
3. Isabel examines Alice's documents and creates a credential on-chain attesting to Alice's trustworthiness.
4. Alice accepts the credential, making it valid.
5. Alice can now interact with/send funds to Verity.

Importantly, the KYC documents that Alice sends to Isabel can include personally identifiable or private information that's needed to verify Alice's identity, but this information is never published or stored on-chain and Verity never needs to see it. Also, other businesses that trust Isabel can accept the same credentials so Alice does not need to repeatedly re-verify for every party she wants to interact with.

## 2. On-Ledger Object: `Credential`

This ledger object is an on-chain representation of a credential.

This object costs one owner reserve for either the issuer or the subject of the credential, depending on whether the subject has accepted it.

The `Credential` object will live in both the `Subject` and `Issuer`'s owner directories (similar to a trustline or escrow).

### 2.1. Fields

| Field Name          | Required? | JSON Type | Internal Type | Description                                                                                                                                                               |
| ------------------- | --------- | --------- | ------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `LedgerEntryType`   | ✔️        | `string`  | `UInt16`      | The ledger object's type (`Credential`).                                                                                                                                  |
| `Flags`             | ✔️        | `number`  | `UInt32`      | Flag values associated with this object.                                                                                                                                  |
| `Subject`           | ✔️        | `string`  | `AccountID`   | The account that the credential is for.                                                                                                                                   |
| `Issuer`            | ✔️        | `string`  | `AccountID`   | The issuer of the credential.                                                                                                                                             |
| `CredentialType`    | ✔️        | `string`  | `Blob`        | A (hex-encoded) value to identify the type of credential from the issuer. This field is limited to a maximum length of 64 bytes.                                          |
| `Expiration`        |           | `number`  | `UInt32`      | Optional credential expiration.                                                                                                                                           |
| `URI`               |           | `string`  | `Blob`        | Optional additional data about the credential (such as a link to the VC document). This field isn't checked for validity and is limited to a maximum length of 256 bytes. |
| `SubjectNode`       | ✔️        | `string`  | `UInt64`      | A hint indicating which page of the subject's owner directory links to this object, in case the directory consists of multiple pages.                                     |
| `IssuerNode`        | ✔️        | `string`  | `UInt64`      | A hint indicating which page of the issuer's owner directory links to this object, in case the directory consists of multiple pages.                                      |
| `PreviousTxnID`     | ✔️        | `string`  | `Hash256`     | The identifying hash of the transaction that most recently modified this object.                                                                                          |
| `PreviousTxnLgrSeq` | ✔️        | `number`  | `UInt32`      | The index of the ledger that contains the transaction that most recently modified this object.                                                                            |

#### 2.1.1. Object ID

The ID of this object will be a hash that incorporates the `Subject`, `Issuer`, and `CredentialType` fields, combined with a unique space key for `Credential` objects (`D`).

#### 2.1.2. `Flags`

| Flag Name     | Flag Value   |
| ------------- | ------------ |
| `lsfAccepted` | `0x00010000` |

The `lsfAccepted` flag represents whether the subject of the credential has accepted the credential. If this flag is disabled, the issuer is responsible for this ledger entry's reserve; if the flag is enabled, the subject of the credential is responsible for the reserve instead. This flag is disabled by default, but is enabled as the result of a successful `CredentialAccept` transaction.

A credential should not be considered "valid" until it has been accepted.

#### 2.1.3. `CredentialType`

This value is similar to the NFT `Taxon` value, where the value's meaning will be decided by the issuer. It may be the same as a claim in a VC, but could also represent a subset of such a claim.

It has a maximum length of 64 bytes, and cannot be an empty string.

### 2.2. Account Deletion

The `Credential` object is not a [deletion blocker](https://xrpl.org/docs/concepts/accounts/deleting-accounts/#requirements).

In other words, if the `Subject` or `Issuer` deletes their account, the `Credential` object will automatically be deleted (rather than prevent them from deleting their account).

## 3. Transaction: `CredentialCreate`

This transaction creates a `Credential` object. It must be sent by the issuer.

### 3.1. Fields

| Field Name        | Required? | JSON Type | Internal Type | Description                                                                        |
| ----------------- | --------- | --------- | ------------- | ---------------------------------------------------------------------------------- |
| `TransactionType` | ✔️        | `string`  | `UInt16`      | The transaction type (`CredentialCreate`).                                         |
| `Account`         | ✔️        | `string`  | `AccountID`   | The issuer of the credential.                                                      |
| `Subject`         | ✔️        | `string`  | `AccountID`   | The subject of the credential.                                                     |
| `CredentialType`  | ✔️        | `string`  | `Blob`        | A (hex-encoded) value to identify the type of credential from the issuer.          |
| `Expiration`      |           | `number`  | `UInt32`      | Optional credential expiration.                                                    |
| `URI`             |           | `string`  | `Blob`        | Optional additional data about the credential (such as a link to the VC document). |

### 3.2. Failure Conditions

- The account in `Subject` doesn't exist.
- The time in `Expiration` is in the past.
- The `URI` field is empty or too long (limit 256 bytes).
- The `CredentialType` field is empty or too long (limit 64 bytes).
- The account doesn't have enough reserve for the object.
- A duplicate credential already exists (with the same `Subject`, `Issuer`, and `CredentialType`).

### 3.3. State Changes

If the transaction is successful:

- The `Credential` object is created.
- If `Subject` === `Account` (i.e. the subject and issuer are the same account), then the `lsfAccepted` flag is enabled.

## 4. Transaction: `CredentialAccept`

This transaction accepts a credential issued to the `Account` (i.e. the `Account` is the `Subject` of the `Credential` object). The credential is not considered valid until it has been transferred/accepted.

### 4.1. Fields

| Field Name        | Required? | JSON Type | Internal Type | Description                                                               |
| ----------------- | --------- | --------- | ------------- | ------------------------------------------------------------------------- |
| `TransactionType` | ✔️        | `string`  | `UInt16`      | The transaction type (`CredentialAccept`).                                |
| `Account`         | ✔️        | `string`  | `AccountID`   | The subject of the credential.                                            |
| `Issuer`          | ✔️        | `string`  | `AccountID`   | The issuer of the credential.                                             |
| `CredentialType`  | ✔️        | `string`  | `Blob`        | A (hex-encoded) value to identify the type of credential from the issuer. |

### 4.2. Failure Conditions

- The account in `Issuer` doesn't exist.
- There is no valid credential described by the fields of the transaction.
- The credential has already been accepted.
- The `Account` doesn't have enough reserve for the object.
- The credential has already expired.

### 4.3. State Changes

If the transaction is successful:

- The `lsfAccepted` flag is turned on in the credential.
- The burden of reserve for the `Credential` object is moved from the issuer to the subject.

If the credential has already expired, then the object will be deleted.

## 5. Transaction: `CredentialDelete`

This transaction deletes a `Credential` object.

It can be executed by:

- The issuer, anytime.
- The account, anytime.
- Anyone, after the expiration time is up.

Deleting a credential is also how a credential is un-accepted.

### 5.1. Fields

| Field Name        | Required? | JSON Type | Internal Type | Description                                                                                |
| ----------------- | --------- | --------- | ------------- | ------------------------------------------------------------------------------------------ |
| `TransactionType` | ✔️        | `string`  | `UInt16`      | The transaction type (`CredentialDelete`).                                                 |
| `Account`         | ✔️        | `string`  | `AccountID`   | The transaction submitter.                                                                 |
| `Subject`         |           | `string`  | `AccountID`   | The person that the credential is for. If omitted, `Account` is assumed to be the subject. |
| `Issuer`          |           | `string`  | `AccountID`   | The issuer of the credential. If omitted, `Account` is assumed to be the issuer.           |
| `CredentialType`  | ✔️        | `string`  | `Blob`        | A (hex-encoded) value to identify the type of credential from the issuer.                  |

_Note: If an account is deleting a credential it issued to itself, then either `Subject` or `Issuer` can be specified, but at least one must be._

### 5.2. Failure Conditions

- Neither `Subject` nor `Issuer` is specified.
- The credential described by the `Subject`, `Issuer`, and `CredentialType` fields doesn't exist.
- The `Account` isn't the issuer or subject, and the expiration hasn't passed.

### 5.3. State Changes

If the transaction is successful:

- The `Credential` object is deleted (from both owner directories).

## 6. On-Ledger Object: `DepositPreauth`

The `DepositPreauth` object tracks a preauthorization from one account to another. This object already exists on the XRPL, but is being extended as a part of this spec to also support credential preauthorization.

### 6.1. Fields

<details>
<summary>

As a reference, [here](https://xrpl.org/docs/references/protocol/ledger-data/ledger-entry-types/depositpreauth/#depositpreauth-fields) are the existing fields for the `DepositPreauth` object.

</summary>

| Field Name          | Required? | JSON Type | Internal Type | Description                                                                                                                                                                                                                                                                                  |
| ------------------- | --------- | --------- | ------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `Account`           | ✔️        | `string`  | `AccountID`   | The account that granted the preauthorization (the destination of the preauthorized payments).                                                                                                                                                                                               |
| `Authorize`         | ✔️        | `string`  | `AccountID`   | The account that received the preauthorization (the sender of the preauthorized payments).                                                                                                                                                                                                   |
| `LedgerEntryType`   | ✔️        | `string`  | `UInt16`      | The value `0x0070`, mapped to the string `"DepositPreauth"`, indicates that this is a `DepositPreauth` object.                                                                                                                                                                               |
| `OwnerNode`         | ✔️        | `string`  | `UInt64`      | A hint indicating which page of the sender's owner directory links to this object, in case the directory consists of multiple pages. Note: The object does not contain a direct link to the owner directory containing it, since that value can be derived from the `Account.PreviousTxnID`. |
| `PreviousTxnID`     | ✔️        | `string`  | `Hash256`     | The identifying hash of the transaction that most recently modified this object.                                                                                                                                                                                                             |
| `PreviousTxnLgrSeq` | ✔️        | `number`  | `UInt32`      | The index of the ledger that contains the transaction that most recently modified this object.                                                                                                                                                                                               |

</details>

We propose these modifications:

| Field Name             | Required? | JSON Type | Internal Type | Description                                                                                                                 |
| ---------------------- | --------- | --------- | ------------- | --------------------------------------------------------------------------------------------------------------------------- |
| `Authorize`            |           | `string`  | `AccountID`   | This field already exists, but is becoming optional.                                                                        |
| `AuthorizeCredentials` |           | `array`   | `STArray`     | The credential(s) that received the preauthorization. (Any account with these credentials can send preauthorized payments). |

A valid `DepositPreauth` object must have **exactly one of** the `Authorize` field or the `AuthorizeCredentials` field.

#### 6.1.1. Object ID

The ID of this object will be either a hash of the `Account` and `Authorize` fields (as it currently is), or a hash of the `Account` and the contents of `AuthorizeCredentials` fields, combined with the unique space key for `DepositPreauth` objects. This unique space key will be different for account-based `DepositPreauth` objects vs. credential-based `DepositPreauth` objects, to avoid the possibility of a hash collision.

#### 6.1.2. `AuthorizeCredentials`

This field is an array of inner objects. The contents of these inner objects determine the credential(s) that are accepted.

If more than one credential is included in the list, all of those credentials must be included (effectively ANDing them together).

The list has a minimum size of 1 and a maximum size of 8 credentials.

| Field Name       | Required? | JSON Type | Internal Type | Description                                                               |
| ---------------- | --------- | --------- | ------------- | ------------------------------------------------------------------------- |
| `Issuer`         | ✔️        | `string`  | `AccountID`   | The issuer of the credential.                                             |
| `CredentialType` | ✔️        | `string`  | `Blob`        | A (hex-encoded) value to identify the type of credential from the issuer. |

## 7. Transaction: `DepositPreauth`

This transaction currently creates and deletes `DepositPreauth` objects, thereby allowlisting and un-allowlisting accounts.

This spec extends that functionality to also support allowlisting and un-allowlisting credentials.

### 7.1. Fields

As a reference, [here](https://xrpl.org/docs/references/protocol/transactions/types/depositpreauth/#depositpreauth-fields) are the existing fields for the `DepositPreauth` transaction:

| Field Name    | Required? | JSON Type | Internal Type | Description                                                                  |
| ------------- | --------- | --------- | ------------- | ---------------------------------------------------------------------------- |
| `Authorize`   |           | `string`  | `AccountID`   | The XRP Ledger address of the sender to preauthorize.                        |
| `Unauthorize` |           | `string`  | `AccountID`   | The XRP Ledger address of a sender whose preauthorization should be revoked. |

This proposal adds two new fields:
| Field Name | Required? | JSON Type | Internal Type | Description |
|------------|-----------|-----------|---------------|-------------|
|`AuthorizeCredentials`| |`array`|`STArray`|The credential(s) to preauthorize. |
|`UnauthorizeCredentials` | |`array`|`STArray`|The credential(s) whose preauthorization should be revoked.|

**Exactly one of** the `Authorize`, `Unauthorize`, `AuthorizeCredentials`, and `UnauthorizeCredentials` fields must be included.

#### 7.1.1. `AuthorizeCredentials` and `UnauthorizeCredentials`

These fields follow the same rules outlined in section 6.1.2 for the `DepositPreauth` object's `AuthorizeCredentials` field.

### 7.2. Failure Conditions

- Existing failure conditions for `DepositPreauth` will still be obeyed.
- None or more than one of `Authorize`, `Unauthorize`, `AuthorizeCredentials`, and `UnauthorizeCredentials` are included (i.e. there must be exactly one of these fields included).
- If authorizing/unauthorizing a credential:
  - The issuer of a credential doesn't exist.
  - The array is too long (i.e. has more than 8 credentials).
  - The array is empty (i.e. has no credentials).
  - There are duplicates in the list provided.
  - If `UnauthorizeCredentials` is included in the transaction, the credentials are not currently authorized.
  - If `AuthorizeCredentials` is included in the transaction:
    - The credentials are already authorized.
  - The account doesn't have enough reserve for the object.

### 7.3. State Changes

If the transaction is successful:

- The `DepositPreauth` object is created or deleted.

The `DepositPreauth` object will store a sorted list of credentials.

## 8. Any Transaction Affected by Deposit Authorization

### 8.1. Fields

The transactions that this field will be added to are:

- `Payment`
- `EscrowFinish`
- `PaymentChannelClaim`
- `AccountDelete`

| Field Name      | Required? | JSON Type | Internal Type | Description                                 |
| --------------- | --------- | --------- | ------------- | ------------------------------------------- |
| `CredentialIDs` |           | `array`   | `Vector256`   | Credential(s) to attach to the transaction. |

#### 8.1.1. `CredentialIDs`

The credentials included must not be expired. If there are duplicates provided in the list, they will be silently de-duped.

### 8.2. Failure Conditions

- Any of the `CredentialIDs`:
  - Isn't an object that exists.
  - Isn't a `Credential` object.
  - Is an expired `Credential` object.
  - Has not been accepted.
  - Isn't a credential issued to the `Account` sending the transaction.
- The group of `CredentialIDs` is not authorized by the destination.
- There are duplicates in the list of `CredentialIDs`.

There is an [existing exception](https://xrpl.org/docs/concepts/accounts/depositauth#precise-semantics) in the Deposit Auth design to allow an XRP payment to an account with Deposit Auth enabled that has a balance less than or equal to the minimum Account Reserve requirement (currently 10 XRP). This is to prevent an account from becoming "stuck" by being unable to send transactions but also unable to receive XRP. There will be no added support for this with credentials; in other words, if a payment satisfying these criteria is sent with non-preauthorized credentials included, the transaction would fail (but would succeed if the credentials are removed).

_Note: the transaction will still fail if too many credentials are included. The exact list must be provided._

_Note: the transaction will succeed if (non-expired) credentials are included, but the account does not have Deposit Auth enabled._

### 8.3. State Changes

- If a credential isn't valid, the transaction fails.
- If a credential is expired, the credential is deleted.
- If the transaction is pre-authorized (either via account or via credential), the transaction will succeed.

## 9. RPC: `deposit_authorized`

The [`deposit_authorized` RPC method](https://xrpl.org/deposit_authorized.html) already exists on the XRPL. This proposal suggests some modifications to also support credential authorization.

### 9.1. Request Fields

| Field Name            | Required? | JSON Type            | Description                                                                                   |
| --------------------- | --------- | -------------------- | --------------------------------------------------------------------------------------------- |
| `source_account`      | ✔️        | `string`             | The sender of a possible payment.                                                             |
| `destination_account` | ✔️        | `string`             | The recipient of a possible payment.                                                          |
| `ledger_hash`         |           | `string`             | A hex string for the ledger version to use.                                                   |
| `ledger_index`        |           | `string` or `number` | The ledger index of the ledger to use, or a shortcut string to choose a ledger automatically. |

This proposal puts forward the following addition:

| Field Name    | Required? | JSON Type | Description                                                                                                                                                                            |
| ------------- | --------- | --------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `credentials` |           | `array`   | The object IDs of `Credential` objects. If this field is included, then the credential will be taken into account when analyzing whether the sender can send funds to the destination. |

### 9.2. Response Fields

| Field Name             | Always Present? | JSON Type | Description                                                                                                                                                                                                                     |
| ---------------------- | --------------- | --------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `deposit_authorized`   | ✔️              | `boolean` | Whether the specified source account is authorized to send payments directly to the destination account. If true, either the destination account does not require deposit authorization or the source account is preauthorized. |
| `destination_account`  | ✔️              | `string`  | The destination account specified in the request.                                                                                                                                                                               |
| `source_account`       | ✔️              | `string`  | The source account specified in the request.                                                                                                                                                                                    |
| `ledger_hash`          |                 | `string`  | The identifying hash of the ledger that was used to generate this response.                                                                                                                                                     |
| `ledger_index`         |                 | `number`  | The ledger index of the ledger version that was used to generate this response.                                                                                                                                                 |
| `ledger_current_index` |                 | `number`  | The ledger index of the current in-progress ledger version, which was used to generate this response.                                                                                                                           |
| `validated`            |                 | `boolean` | If true, the information comes from a validated ledger version.                                                                                                                                                                 |

This proposal puts forward the following addition:

| Field Name    | Required? | JSON Type | Description                                                                                                                                                                            |
| ------------- | --------- | --------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `credentials` |           | `array`   | The object IDs of `Credential` objects. If this field is included, then the credential will be taken into account when analyzing whether the sender can send funds to the destination. |

## 10. Compliance with W3C Spec

This proposal prioritizes interoperability with the [W3C Verifiable Credential (VC) spec](https://www.w3.org/TR/vc-data-model/). The existing verification flow for XRPL-based Verifiable Credentials remains the primary method:

1. **DID Resolution:** Verifiers access the DID document from the DID ID (e.g., `did:xrpl:r....`). This document is stored in the account's [DID object](https://xrpl.org/docs/references/protocol/ledger-data/ledger-entry-types/did).
2. **VC Access:** The DID document provides a link to the relevant Verifiable Credentials.
3. **VC Verification:** Based on access permissions, verifiers can then view and verify the retrieved VCs.

However, this proposal introduces an optional enhancement. Within the `Credential` object, the `URI` field can also point to the VC. It's important to note that this pointer is entirely optional, and the core verification process using DID resolution will still be the primary method for XRPL credential verification.

It is recommended that anyone who holds a credential also have a DID object, to increase compliance with the W3C VC spec.

Note that the issuer of the on-chain `Credential` does not have to be the same as the issuer of the VC, and the on-chain object can instead essentially serve as an on-chain attestation from the issuer for the VC.

## 11. Invariants

### 11.1. Reserves

The burden of reserve should be with the issuer, and the credential should be in the issuer's owner directory, if the `lsfAccepted` flag is off. The burden of reserve should be with the subject and the credential should be in the subject's owner directory, if the `lsfAccepted` flag is on.

### 11.2. The `DepositPreauth` Object

A `DepositPreauth` ledger object always has exactly one of the `Authorize` field and the `AuthorizeCredentials` field.

If the `AuthorizeCredentials` field is included, the array contains between 1 and 8 credentials.

## 12. Examples

In this example, a trusted issuer, Isabel, is issuing a credential that indicates that Alice is KYC'd. Verity is setting up her account to only interact with accounts that Isabel has attested to being properly KYC'd.

For ease of reading, some of the common transaction fields, such as signatures and public keys, have been left out of this example.

### 12.1. `CredentialCreate`

Isabel creates the credential for Alice, after confirming her KYC status off-chain.

```typescript
{
    TransactionType: "CredentialCreate",
    Account: "rISABEL......",
    Subject: "rALICE.......",
    CredentialType: "4B5943", // "KYC" in hex
    Expiration: 789004799, // the end of the year
    URI: "isabel.com/credentials/kyc/alice" // This will be converted into hex
}
```

### 12.2. The `Credential` Object

This is the object created by the `CredentialCreate` transaction.

```typescript
{
    LedgerEntryType: "Credential",
    Flags: 0,
    Subject: "rALICE.......",
    Issuer: "rISABEL......",
    CredentialType: "4B5943", // "KYC" in hex
    Expiration: 789004799, // the end of the year
    URI: "isabel.com/credentials/kyc/alice" // This will be converted into hex
}
```

### 12.3. `CredentialAccept`

Alice accepts the credential, thereby making it valid.

```typescript
{
    TransactionType: "CredentialAccept",
    Account: "rALICE.......",
    Issuer: "rISABEL......",
    CredentialType: "4B5943"
}
```

### 12.4. `DepositPreauth`

Verity sets up her account to only interact with accounts that Isabel has KYC'd.

```typescript
{
    TransactionType: "DepositPreauth",
    Account: "rVERITY......",
    AuthorizeCredentials: [
        {
            Credential: {
                Issuer: "rISABEL......",
                CredentialType: "4B5943"
            }
        }
    ]
}
```

### 12.5. Payments

This transaction will succeed, since Alice has attached the authorized credential from Isabel.

```typescript
{
    TransactionType: "Payment",
    Account: "rALICE......",
    Destination: "rVERITY......",
    Amount: "10000000",
    CredentialIDs: ["DD40031C6C21164E7673...17D467CEEE9"]
}
```

This transaction will fail, since Alice has not attached the authorized credential from Isabel. This is akin to trying to go through airport security without a form of ID.

```typescript
{
    TransactionType: "Payment",
    Account: "rALICE......",
    Destination: "rVERITY......",
    Amount: "10000000"
}
```

This transaction will fail, since the attached credential isn't Bob's.

```typescript
{
    TransactionType: "Payment",
    Account: "rBOB......",
    Destination: "rVERITY......",
    Amount: "10000000",
    CredentialIDs: ["DD40031C6C21164E7673...17D467CEEE9"]
}
```

This transaction will fail, since Bob doesn't have a valid credential from Isabel.

```typescript
{
    TransactionType: "Payment",
    Account: "rBOB......",
    Destination: "rVERITY......",
    Amount: "10000000"
}
```

This transaction will fail, since Bob doesn't have Deposit Authorization set up.

```typescript
{
    TransactionType: "Payment",
    Account: "rALICE......",
    Destination: "rBOB......",
    Amount: "10000000",
    CredentialIDs: ["DD40031C6C21164E7673...17D467CEEE9"]
}
```

## 13. Security

### 13.1. Trust Assumptions

You need to trust the issuer to only be issuing valid credentials, and to not delete a credential without a legitimate reason.

### 13.2. Data Privacy

No private data needs to be stored on-chain (e.g. all the KYC data). The actual VC can still be stored off-chain. It could be stored at a link in the `URI` field.

# Appendix

## Appendix A: FAQ

### A.1: Do I have to only use credentials with the Deposit Authorization feature? Can I also use them for off-chain purposes?

You can use credentials for any purpose you'd like, not just for Deposit Authorization.

### A.2: Do I need to use credentials for VCs or can I use them for other things?

You can use credentials for any purpose you'd like. The recommended usecase is VCs, but there are plenty of other usecases for them.

### A.3: Why not use NFTs instead, with a certain issuer-taxon combo and the `tfTransferable` flag unset?

Using NFTs instead wouldn't be as elegant, since it means that the NFT has to follow a specific format. It would make more sense for an off-ledger use-case, not directly on-ledger. In addition, an NFT serves different needs - e.g. NFTs don't have an expiration.

### A.4: Can an issuer issue a credential for themselves?

Yes.

### A.5: Can an issuer edit the details of a credential once it's created?

No, it would have to be deleted and recreated. This is similar to needing to get a new card if your license/passport expires. However, if the `Subject`, `Issuer`, and `CredentialType` stay the same, the object will still have the same ID as before.

### A.6: Why do I need to include the `CredentialIDs` field in my transaction? Shouldn't the XRPL be able to figure out whether I have a valid credential automatically?

There is no way for the XRPL to iterate through just the list of credentials an account has; it can only iterate through the entire list of account objects. This is an unbounded list of objects (it could be millions of objects). Even just the list of accepted credentials could theoretically be millions of objects long. It could cause serious performance issues if the system had to iterate through the whole list.

It's much faster to have the credential ID included - it's easy to make sure that that's a valid credential, and check that it's an authorized credential.

### A.7: Can a credential issuer delete their account?

Yes, though the credentials they created will be deleted.

### A.8: Does a credential issuer have to have an on-chain account?

Yes.

### A.9: How do I get a list of credentials that an issuer has issued?

The `account_objects` RPC will return a list of all `Credential` objects an account is involved in - both as `Subject` and `Issuer`. To get a list of just the ones an account has issued, just filter that list for `Credential`s that have that account as the `Issuer`.

### A.10: How do I get a list of credentials that an account has been issued?

The `account_objects` RPC will return a list of all `Credential` objects an account is involved in - both as `Subject` and `Issuer`. To get a list of just the ones an account has been issued, just filter that list for `Credential`s that have that account as the `Subject`.

### A.11: Can I edit the list of credentials stored in `AuthorizeCredentials`?

No, you have to delete the `DepositPreauth` object and recreate it with the new list.

### A.12: Does the list of credentials in `AuthorizeCredentials` _have_ to be AND-ed together? Can I instead use it as an OR list (i.e. only provide one of the credentials instead of all)? Or some complex combination?

No. You can OR credential(s) by putting them in separate `DepositPreauth` objects. For performance reasons, it is much easier to do a credential lookup if you need to have all of the credentials. Otherwise, you'd have to search the whole list. In addition, people who need to use this feature will likely not find the object reserve cost-prohibitive.

### A.13: Why are `CredentialCreate` and `CredentialDelete` separate transactions?

It's easier and clearer to have those be separate operations.
