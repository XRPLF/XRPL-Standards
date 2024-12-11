<pre>
Title:       <b>Account Permission Delegation</b>

Author:      <a href="mailto:mvadari@ripple.com">Mayukha Vadari</a>

Affiliation: <a href="https://ripple.com">Ripple</a>
</pre>

# Account Permission Delegation

## Abstract

This proposal introduces a delegated authorization mechanism to enhance the flexibility and usability of XRPL accounts.

Currently, critical issuer actions, such as authorizing trustlines, require direct control by the account's keys, hindering operational efficiency and complex use cases. By empowering account holders to selectively delegate specific permissions to other accounts, this proposal aims to enhance account usability without compromising security. This mechanism will unlock new possibilities for XRPL applications, such as multi-party workflows and advanced account management strategies.

## 1. Overview

We propose:
* Creating a `AccountPermission` ledger object.
* Creating a `AccountPermissionSet` transaction type.

We also propose modifying the transaction common fields.

This feature will require an amendment, tentatively titled `AccountPermission`.

### 1.1. Terminology

* **Delegating account**: The main account, which is delegating permissions to another account.
* **Delegated account**: The account that is having permissions delegated to it.

### 1.2. Basic Flow

Isaac, a token issuer, wants to set up his account to follow security best practices and separation of responsibilities. He wants Alice to manage token issuing and Bob to manage trustlines. He is also working with Kylie, a KYC provider, who he wants to be able to authorize trustlines but not have any other permissions (as she is an external party).

He can authorize:
* Alice's account for the `Payment` transaction permission.
* Bob's account for the `TrustSet` transaction permission.
* Kylie's account for the `TrustlineAuthorize` granular permission.

The full set of available permissions is listed in [XLS-74d, Account Permissions](https://github.com/XRPLF/XRPL-Standards/discussions/217)

## 2. On-Ledger Object: `AccountPermission`

This object represents a set of permissions that an account has delegated to another account, and is modeled to be similar to [`DepositPreauth` objects](https://xrpl.org/docs/references/protocol/ledger-data/ledger-entry-types/depositpreauth).

### 2.1. Fields

| Field Name | Required? | JSON Type | Internal Type | Description |
|------------|-----------|-----------|---------------|-------------|
|`LedgerIndex`| ✔️|`string`|`Hash256`|The unique ID of the ledger object.|
|`LedgerEntryType`| ✔️|`string`|`UInt16`|The ledger object's type (`AccountPermission`)|
|`Account`| ✔️|`string`|`AccountID`|The account that wants to authorize another account.|
|`Authorize`| ✔️|`string`|`AccountID`|The authorized account.|
|`Permissions`| ✔️|`string`|`STArray`|The transaction permissions that the account has access to.|
|`OwnerNode`|✔️|`string`|`UInt64`|A hint indicating which page of the sender's owner directory links to this object, in case the directory consists of multiple pages.|
|`PreviousTxnID`|✔️|`string`|`Hash256`|The identifying hash of the transaction that most recently modified this object.|
|`PreviousTxnLgrSeq`|✔️|`number`|`UInt32`|The index of the ledger that contains the transaction that most recently modified this object.|

#### 2.1.1. Object ID

The ID of this object will be a hash of the `Account` and `Authorize` fields, combined with the unique space key for `AccountPermission` objects, which will be defined during implementation.

#### 2.1.2. `Permissions`

This field is an array of permissions to delegate to the account, as listed in [XLS-74d, Account Permissions](https://github.com/XRPLF/XRPL-Standards/discussions/217). The array will have a maximum length of 10.

### 2.2. Account Deletion

The `AccountPermission` object is not a [deletion blocker](https://xrpl.org/docs/concepts/accounts/deleting-accounts/#requirements).

## 3. Transaction: `AccountPermissionSet`

This object represents a set of permissions that an account has delegated to another account, and is modeled to be similar to the [`DepositPreauth` transaction type](https://xrpl.org/docs/references/protocol/transactions/types/depositpreauth).

### 3.1. Fields

| Field Name | Required? | JSON Type | Internal Type | Description |
|------------|-----------|-----------|---------------|-------------|
|`TransactionType`| ✔️|`string`|`UInt16`|The transaction type (`AccountPermissionSet`).|
|`Account`| ✔️|`string`|`AccountID`|The account that wants to authorize another account.|
|`Authorize`|✔️|`string`|`AccountID`|The authorized account.|
|`Permissions`| ✔️|`string`|`STArray`|The transaction permissions that the account has been granted.|

### 3.1.1. `Permissions`

This transaction works slightly differently from the `DepositPreauth` transaction type. Instead of using an `Unauthorize` field, an account is unauthorized by using an empty `Permissions` list.

### 3.2. Failure Conditions

* `Permissions` is too long (the limit is 10), or includes duplicates.
* Any of the specified permissions are invalid.
* The account specified in `Authorize` doesn't exist.

### 3.3. State Changes

A `AccountPermission` object will be created, modified, or deleted based on the provided fields.

## 4. Transactions: Common Fields

### 4.1. Fields

As a reference, [here](https://xrpl.org/docs/references/protocol/transactions/common-fields/) are the fields that all transactions currently have.

<!--There are too many and I didn't want to list them all, it cluttered up the spec - but maybe it can be a collapsed section?-->

We propose these modifications:

| Field Name | Required? | JSON Type | Internal Type | Description |
|------------|-----------|-----------|---------------|-------------|
|`OnBehalfOf`| |`string`|`AccountID`|The account that the transaction is being sent on behalf of.|

### 4.2. Failure Conditions

* The `OnBehalfOf` account doesn't exist.
* The `OnBehalfOf` account hasn't authorized the transaction's `Account` to send transactions on behalf of it.
* The `OnBehalfOf` account hasn't authorized the transaction's `Account` to send this particular transaction type/granular permission on behalf of it.

### 4.3. State Changes

The transaction succeeds as if the transaction was sent by the `OnBehalfOf` account. 

## 5. Examples

### 5.1. `Payment` Permission

In this example, Isaac is delegating the `Payment` permission to Alice.

#### 5.1.1. `AccountPermissionSet` Transaction
```typescript
{
    TransactionType: "AccountPermissionSet",
    Account: "rISAAC......",
    Authorize: "rALICE......",
    Permissions: [{Permission: {PermissionValue: "Payment"}}],
}
```

_Note: the weird format of `Permissions`, with needing an internal object, is due to peculiarities in the [XRPL's Binary Format](https://xrpl.org/docs/references/protocol/binary-format). It can be cleaned up/simplified in tooling._

#### 5.1.2. `AccountPermission` Ledger Object
```typescript
{
    LedgerEntryType: "AccountPermission",
    Account: "rISAAC......",
    Authorize: "rALICE......",
    Permissions: [{Permission: {PermissionValue: "Payment"}}],
}
```

#### 5.1.3. `Payment` Transaction
```typescript
{
    Transaction: "Payment",
    Account: "rALICE......",
    Amount: "1000000000",
    Destination: "rCHARLIE......",
    OnBehalfOf: "rISAAC......"
}
```

### 5.2. `TrustSet` Permission

In this example, Isaac is delegating the `TrustSet` permission to Bob.

#### 5.2.1. `AccountPermissionSet` Transaction
```typescript
{
    TransactionType: "AccountPermissionSet",
    Account: "rISAAC......",
    Authorize: "rBOB......",
    Permissions: [{Permission: {PermissionValue: "TrustSet"}}],
}
```

#### 5.2.2. `AccountPermission` Ledger Object
```typescript
{
    LedgerEntryType: "AccountPermission",
    Account: "rISAAC......",
    Authorize: "rBOB......",
    Permissions: [{Permission: {PermissionValue: "TrustSet"}}],
}
```

#### 5.2.3. `TrustSet` Transaction

In this example, Bob is freezing a trustline from Holden, a USD.Isaac token holder.

```typescript
{
    Transaction: "TrustSet",
    Account: "rBOB......",
    LimitAmount: {
        currency: "USD",
        issuer: "rHOLDEN......",
        value: "0",
    },
    Flags: 0x00100000, // tfSetFreeze
    OnBehalfOf: "rISAAC......"
}
```

### 5.3. `TrustlineAuthorize` Permission

In this example, Isaac is delegating the `TrustlineAuthorize` permission to Kylie.

#### 5.3.1. `AccountPermissionSet` Transaction
```typescript
{
    TransactionType: "AccountPermissionSet",
    Account: "rISAAC......",
    Authorize: "rKYLIE......",
    Permissions: [{Permission: {PermissionValue: "TrustlineAuthorize"}}],
}
```

#### 5.3.2. `AccountPermission` Object
```typescript
{
    LedgerEntryType: "AccountPermission",
    Account: "rISAAC......",
    Authorize: "rKYLIE......",
    Permissions: [{Permission: {PermissionValue: "TrustlineAuthorize"}}],
}
```

#### 5.3.3. `TrustSet` Transaction

In this example, Kylie is authorizing Holden's trustline.

```typescript
{
    Transaction: "TrustSet",
    Account: "rBOB......",
    LimitAmount: {
        currency: "USD",
        issuer: "rHOLDEN......",
        value: "0",
    },
    Flags: 0x00010000, // tfSetfAuth
    OnBehalfOf: "rISAAC......"
}
```

Note that this transaction will fail if:
* The trustline with Holden doesn't exist.
* Kylie tries to change any trustline setting that isn't just the `tfSetfAuth` flag.

## 6. Invariants

An account should never be able to send a transaction on behalf of another account without a valid `AccountPermission` object.

## 7. Security

Delegating permissions to other accounts requires a high degree of trust, especially when the delegated account can potentially access funds (`Payment`s) or charge reserves (any transaction that can create objects). In addition, any account that has access to the entire `AccountSet`, `SetRegularKey`, `SignerListSet`, or `AccountPermissionSet` transactions can give themselves any permissions even if this was not originally part of the intention. Authorizing users for those transactions should have heavy warnings associated with it in tooling and UIs.

All tooling indicating whether an account has been blackholed will need to be updated to also check if `AccountSet`, `SetRegularKey`, `SignerListSet`, or `AccountPermissionSet` permissions have been delegated.

On the other hand, this mechanism also offers a granular approach to authorization, allowing accounts to selectively grant specific permissions without compromising overall account control. This approach provides a balance between security and usability, empowering account holders to manage their assets and interactions more effectively.

# Appendix

## Appendix A: Comparing with [XLS-49d](https://github.com/XRPLF/XRPL-Standards/discussions/144), Multiple Signer Lists

In XLS-49d:
* There is multisign support by default.
* The signer list is controlled by the delegating account.
* There may be at most one list per permission, with a maximum of 32 signers.
* There is a total of one reserve per signer list.
* The delegating account pays the fees.

In this proposal:
* There is no direct multisign support (though permissions can be delegated to an account with a multisign setup).
* The keys that have been delegated to are self-governed (i.e. the delegating account doesn't control the signer list on an account that has been delegated to).
* A permission may be delegated to as many accounts/signer lists as one is willing to pay reserve for.
* There is one reserve per delegated account.
* The delegated account pays the fees.

Both are useful for slightly different usecases; XLS-49d is more useful when you want multiple signatures to guard certain features, while this proposal is useful when you want certain parties to have access to certain features. This proposal does support XLS-49d-like usage, but it would cost more XRP, as a second account would need to be created.

## Appendix B: FAQ

### B.1: Who pays the transaction fees?

The account that sends the transaction pays the transaction fees (not the delegating account, but the delegated account).

### B.2: How does using an `NFTokenMint` permission compare to using the existing `NFTokenMinter` account field?

*Note that the `NFTokenMinter` field provides more permissions than just `NFTokenMint`ing; it provides permissions over offers and burning as well (though of course multiple permissions can be delegated to one account).* 

The biggest advantage to using the `NFTokenMint` field is that it's "free" (it doesn't cost any additional reserve). Delegating a permission to an account costs one object reserve (for the `AccountPermission` object).

On the other hand, with this proposal, you can have as many accounts with the `NFTokenMint` permission as you want. The minting account can also mint NFTs directly into your account, instead of into their own account.

Given the overlap in functionality, the `NFTokenMinter` field could potentially be deprecated in the future.

### B.3: Can a blackholed account have some permissions set?

Yes, in certain cases. For example, an account could still be considered "blackholed" if it has the `AccountDomainSet` permission delegated, but not if it has the `SetRegularKey` permission delegated. The definition of a blackholed account will need to be modified after this amendment.

### B.4: Can I delegate permissions to a `Batch` transaction ([XLS-56d](https://github.com/XRPLF/XRPL-Standards/discussions/162))?

No, `OnBehalfOf` will not be allowed on `Batch` transactions. Instead, the inner transactions must include the `OnBehalfOf` field.

### B.5: Why is the process of unauthorizing an account different between the `DepositPreauth` transaction and the `AccountPermissionSet` transaction?

The `DepositPreauth` transaction has an `Unauthorize` field. It seemed more confusing to use such a paradigm here, but it can be changed if there are strong objections.
