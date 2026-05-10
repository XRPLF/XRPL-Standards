<pre>
  xls: 80
  title: Permissioned Domains
  description: Creation of controlled environments with specific rules and restrictions to bridge decentralized blockchain and regulatory requirements
  author: Mayukha Vadari <mvadari@ripple.com>
  proposal-from: https://github.com/XRPLF/XRPL-Standards/discussions/228
  status: Final
  category: Amendment
  requires: [XLS-70](../XLS-0070-credentials/README.md)
  created: 2024-09-12
</pre>

# Permissioned Domains

## Abstract

This proposal introduces the concept of permissioned domains. Permissioned domains enable the creation of controlled environments within a broader system where specific rules and restrictions can be applied to user interactions and asset flow. This approach aims to bridge the gap between the transparency and security benefits of decentralized blockchain technology and the regulatory requirements of traditional financial institutions.

## 1. Overview

This proposal builds on top of [XLS-70 (Credentials)](../XLS-0070-credentials/README.md), as credentials are needed for permissioning.

We propose:

- Creating a `PermissionedDomain` ledger object.
- Creating a `PermissionedDomainSet` transaction.
- Creating a `PermissionedDomainDelete` transaction.

This feature will require an amendment. Since this feature doesn't bring any functionality to the XRPL by itself, it will be gated by other amendments that use it instead.

### 1.1. Terminology

- **Domain**: A collection of rules indicating what accounts may be a part of it. This spec includes credential-gating, but more options could be added in the future. A domain is focused on "who can participate". The "how they can participate" (e.g. what tokens they may use) aspect can be done in other ways in the primitives they're used.
- **Domain Rules**: The set of rules that govern a domain, i.e. the credentials it accepts.
- **Domain Owner**: The account that created a domain, and is the only one that can modify its rules or delete it.
- **Domain Member**: An account that satisfies the rules of the domain (i.e. has one of the credentials that are accepted by the domain). There is no explicit joining step; as long as the account has a valid credential, it is a member.

## 2. On-Ledger Object: `PermissionedDomain`

This object represents a permissioned domain.

### 2.1. Fields

| Field Name            | Required? | JSON Type | Internal Type | Description                                                                                                                                               |
| --------------------- | --------- | --------- | ------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `LedgerIndex`         | ✔️        | `string`  | `Hash256`     | The unique ID of the ledger object.                                                                                                                       |
| `Flags`               | ✔️        | `number`  | `UInt32`      | Flag values associated with this object.                                                                                                                  |
| `LedgerEntryType`     | ✔️        | `string`  | `UInt16`      | The ledger object's type (`PermissionedDomain`).                                                                                                          |
| `Owner`               | ✔️        | `string`  | `AccountID`   | The account that controls the settings of the domain.                                                                                                     |
| `OwnerNode`           | ✔️        | `string`  | `UInt64`      | A hint indicating which page of the sender's owner directory links to this object, in case the directory consists of multiple pages.                      |
| `Sequence`            | ✔️        | `number`  | `UInt32`      | The `Sequence` value of the `PermissionedDomainSet` transaction that created this domain. Used in combination with the `Account` to identify this domain. |
| `AcceptedCredentials` | ✔️        | `array`   | `STArray`     | The credentials that are accepted by the domain. Ownership of one of these credentials automatically makes you a member of the domain.                    |
| `PreviousTxnID`       | ✔️        | `string`  | `Hash256`     | The identifying hash of the transaction that most recently modified this entry.                                                                           |
| `PreviousTxnLgrSeq`   | ✔️        | `number`  | `UInt32`      | The ledger index that contains the transaction that most recently modified this object.                                                                   |

#### 2.1.1. `LedgerIndex`

The ID of this object will be a hash that incorporates the `Owner` and `Sequence` fields, combined with a unique space key for `PermissionedDomain` objects, which will be defined during implementation.

This value will be used wherever a `DomainID` is required.

#### 2.1.2. `AcceptedCredentials`

This is an array of inner objects referencing a type of credential. The maximum length of this array is 10.

The array will be sorted by `Issuer`, so that searching it for a match is more performant.

| Field Name       | Required? | JSON Type | Internal Type | Description                                                                                                               |
| ---------------- | --------- | --------- | ------------- | ------------------------------------------------------------------------------------------------------------------------- |
| `Issuer`         | ✔️        | `string`  | `AccountID`   | The issuer of the credential.                                                                                             |
| `CredentialType` | ✔️        | `string`  | `Blob`        | A (hex-encoded) value to identify the type of credential from the issuer. The maximum length is 64 bytes (as per XLS-70). |

### 2.2. Account Deletion

The `PermissionedDomain` object is a [deletion blocker](https://xrpl.org/docs/concepts/accounts/deleting-accounts/#requirements).

## 3. Transaction: `PermissionedDomainSet`

This transaction creates or modifies a `PermissionedDomain` object.

### 3.1. Fields

| Field Name            | Required? | JSON Type | Internal Type | Description                                                                                                                                                                     |
| --------------------- | --------- | --------- | ------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `TransactionType`     | ✔️        | `string`  | `UInt16`      | The transaction type (`PermissionedDomainSet`).                                                                                                                                 |
| `Account`             | ✔️        | `string`  | `AccountID`   | The account sending the transaction.                                                                                                                                            |
| `DomainID`            |           | `string`  | `Hash256`     | The domain to modify. Must be included if modifying an existing domain.                                                                                                         |
| `AcceptedCredentials` | ✔️        | `array`   | `STArray`     | The credentials that are accepted by the domain. Ownership of one of these credentials automatically makes you a member of the domain. An empty array means deleting the field. |

### 3.2. Failure Conditions

- `Issuer` doesn't exist on one or more of the credentials in `AcceptedCredentials`.
- The `AcceptedCredentials` array is empty or too long (limit 10).
- Any credential in `AcceptedCredentials` has an empty `CredentialType` or a `CredentialType` longer than 64 bytes (as per XLS-70).
- If `DomainID` is included:
  - That domain doesn't exist.
  - The `Account` isn't the domain owner.

### 3.3. State Changes

If the transaction is successful:

- It creates or modifies a `PermissionedDomain` object.

## 4. Transaction: `PermissionedDomainDelete`

This transaction deletes a `PermissionedDomain` object.

### 4.1. Fields

| Field Name        | Required? | JSON Type | Internal Type | Description                                        |
| ----------------- | --------- | --------- | ------------- | -------------------------------------------------- |
| `TransactionType` | ✔️        | `string`  | `UInt16`      | The transaction type (`PermissionedDomainDelete`). |
| `Account`         | ✔️        | `string`  | `AccountID`   | The account sending the transaction.               |
| `DomainID`        | ✔️        | `string`  | `Hash256`     | The domain to delete.                              |

### 4.2. Failure Conditions

- The domain specified in `DomainID` doesn't exist.
- The account isn't the owner of the domain.

### 4.3. State Changes

If the transaction is successful:

- It deletes a `PermissionedDomain` object.

## 5. Examples

A sample domain object may look like this (ignoring common fields):

```typescript
{
  Owner: "rOWEN......",
  Sequence: 5,
  AcceptedCredentials: [
    {
      Credential: {
        Issuer: "rISABEL......",
        CredentialType: "123ABC"
      }
    }
  ]
}
```

## 6. Invariants

- You cannot have a domain with no rules.
- The `AcceptedCredentials` array must have length between 1 and 10, if included.

## 7. Security

### 7.1. Issuer Trust

Relying on external issuers for credentials requires a degree of trust. If issuer credentials are compromised or forged, the system will be vulnerable.

### 7.2. Domain Creator Trust

While users can create their own domains, trust in the domain creator remains crucial. Malicious domain creators (or hackers) could potentially expose domain users to illegal liquidity.

# Appendix

## Appendix A: FAQ

### A.1: Why is the name `PermissionedDomain` so long? Why not shorten it to just `Domain`?

The term `Domain` is already used in the [account settings](https://xrpl.org/docs/references/protocol/transactions/types/accountset/#domain), so it would be confusing to use just the term `Domain` for this.

### A.2: Can a domain owner also be a credential issuer?

Yes.

### A.3: Can other rule types be added to domains?

Yes, if there is a need (though they must be focused on "who can participate" rather than other aspects of participation, like tokens). If you have any in mind, please mention them below.

### A.5: Can I AND credentials together?

No, because it is difficult to make a clean design for that capability.

### A.6: Does the domain owner have any special powers over the accepted credentials?

No, unless they are also the issuer of said credential.

### A.7: Does the domain owner need to hold the credentials?

No.

### A.8: Why not have a ledger object for each domain rule, instead of having it all in one object? Then you wouldn't have any limitations on how many rules a domain could have.

This won't work.

The ledger needs to be able to iterate through the domain rules to ensure that all of them are being adhered to. If a domain owner has millions of objects (or millions of rules), then iterating through all of those objects becomes prohibitively expensive from a performance standpoint.
