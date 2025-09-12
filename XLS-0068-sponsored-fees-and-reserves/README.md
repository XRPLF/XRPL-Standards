
<pre>
  xls: 68
  title: Sponsored Fees and Reserves
  description: Allow an account to fund fees and reserves on behalf of another account
  author: Mayukha Vadari (@mvadari)
  proposal-from: https://github.com/XRPLF/XRPL-Standards/discussions/196
  created: 2024-05-02
  updated: 2025-09-08
  status: Draft
  category: Amendment
  requires: 74
</pre>

# Sponsored Fees and Reserves

## 1. Abstract

As the blockchain industry grows, many projects want to be able to build on the blockchain, but abstract away the complexities of using the blockchain - users don't need to submit transactions or deal with transaction fees themselves, they can just pay the platform to handle all that complexity (though, of course, the users still control their own keys).

Some projects also want to onboard users more easily, allowing users to create accounts without needing to pay for their own account reserve or needing to gift accounts free XRP to cover the reserve (this could get rather expensive if it is exploited).

In order to handle these sorts of use-cases, this proposal adds a process for users to maintain control over their keys and account, but to have another account (e.g. a platform) submit the transaction and pay the transaction fee and/or reserves on their behalf. This proposal supports both account and object reserves.

Similar features on other chains are often called "sponsored transactions", "meta-transactions", or "relays".

## 2. Overview

Accounts can include signatures from sponsors in their transactions that will allow the sponsors to pay the transaction fee for the transaction, and/or the reserve for any accounts/objects created in the transaction.

Sponsors can also pre-fund fees or reserves, if they do not want to deal with the burden of co-signing every sponsored transaction.

We propose:

- Creating the `Sponsorship` ledger entry
- Modifying the `AccountRoot` ledger entry
- Creating the `SponsorshipSet` transaction type
- Creating the `SponsorshipTransfer` transaction type
- Modifying the `AccountDelete` transaction type (behavior only, not fields)
- Adding two additional granular permissions (`SponsorFee`, `SponsorReserve`)

The common fields for all ledger objects and all transactions will also be modified.

In addition, there will be a modification to the `account_objects` RPC method, and a new RPC method called `account_sponsoring`.

This feature will require an amendment, tentatively titled `Sponsor`.

### 2.1. Terminology

- **Sponsor**: The account that is covering the reserve or paying the transaction fee on behalf of another account.
- **Sponsee**: The account that the sponsor is paying a transaction fee or reserve on behalf of.
- **Owner**: The account that owns a given object (or the account itself). This is often the same as the sponsee.
- **Sponsored account**: An account that a sponsor is covering the reserve for (currently priced at 1 XRP).
- **Sponsored object**: A non-account ledger object that a sponsor is covering the reserve for (currently priced at 0.2 XRP).
- **Sponsor relationship**: The relationship between a sponsor and sponsee.
- **Sponsorship type**: The "type" of sponsorship - sponsoring transaction fees vs. sponsoring reserves.

### 2.2. The Sponsorship Flow (Not Pre-Funded)

In this scenario, the sponsor, Spencer, wants to pay the transaction fee and/or reserve for the sponsee Alice's transaction.

- Alice constructs her transaction and autofills it (so that all fields, including the fee and sequence number, are included in the transaction). She adds Spencer's account and sponsorship type to the transaction as well.
- Spencer signs the transaction and provides his signature to Alice.
- Alice adds Spencer's public key and signature to her transaction.
- Alice signs and submits her transaction as normal.

### 2.3. The Sponsorship Flow (Pre-Funded)

In this scenario, the sponsor, Spencer, wants to pay the transaction fee and/or reserve for the sponsee Alice's transaction, but would prefer to pre-fund the XRP necessary, so that he does not have to co-sign every single one of Alice's transactions.

- Spencer submits a transaction to initialize the sponsorship relationship and pre-fund Alice's sponsorship (note: these funds are not sent directly to Alice. She may only use the allocated funds for fees and reserves, and these are separate buckets).
  - Alice does not need to do anything to accept this.
- Alice constructs her transaction and autofills it (so that all fields, including the fee and sequence number, are included in the transaction). She adds Spencer's account and sponsorship type to the transaction as well.
- Alice signs and submits her transaction as normal.

_Note that Spencer does not need to be a part of Alice's signing and submission flow in this example._

### 2.4. Recouping a Sponsored Object Reserve

In this scenario, the sponsor, Spencer, would like to re-obtain the reserve that is currently trapped due to his sponsorship of Alice's object.

Spencer can submit a `SponsorshipTransfer` transaction, which allows him to pass the onus of the reserve back to Alice, or pass it onto another sponsor.

### 2.5. Recouping a Sponsored Account Reserve

In this scenario, the sponsor, Spencer, would like to retrieve his reserve from sponsoring Alice's account.

There are two ways in which he could do this:

- If Alice is done using her account, she can submit an `AccountDelete` transaction, which will send all remaining funds in the account back to Spencer.
- If Alice would like to keep using her account, or would like to switch to a different provider, she (or Spencer) can submit a `SponsorshipTransfer` transaction to either remove sponsorship or transfer it to the new provider.

## 3. Ledger Entries: Common Fields

### 3.1. Fields

As a reference, here are the fields that all ledger objects currently have:

| Field Name | Constant? | Required? | Default Value | JSON Type | Internal Type | Description |
| ---------- | --------- | --------- | ------------- | ---------- | ------------- | ----------- |
| `LedgerEntryType` | ✔️ | ✔️ | N/A | `string`  | `UInt16`  |
| `Flags` | ✔️ | ✔️ | N/A | `number`  | `UInt16`  |

We propose this additional field:
| Field Name | Constant? | Required? | Default Value | JSON Type | Internal Type | Description |
|------------|-----------|-----------|---------------|------------|---------------|-------------|
|`SponsorAccount`| | |N/A|`string`|`AccountID`| The sponsor that is paying the reserve for this ledger object. |

## 4. Ledger Entry: `Sponsorship`

`Sponsorship` is an object that reflects a sponsoring relationship between two accounts, `SponsorAccount` and `Sponsee`. This allows sponsors to "pre-fund" sponsees, if they so desire.

_Note: this object does not need to be created in order to sponsor accounts. It is an offered convenience, so that sponsors do not have to co-sign every sponsored transaction if they don't want to, especially for transaction fees. It also allows them to set a maximum balance even if they still want to co-sign transactions._

### 4.1. Object ID

The key of the `Sponsorship` object is the result of [`SHA512-Half`](https://xrpl.org/docs/references/protocol/data-types/basic-data-types/#hashes) of the following values concatenated in order:

- The `Sponsorship` space key (defined during implementation)
- The `AccountID` of the `Sponsor`
- The `AccountID` of the `Sponsee`

### 4.2. Fields

| Field Name | Constant? | Required? | Default Value | JSON Type | Internal Type | Description |
| ---------- | --------- | --------- | ------------- | --------- | ------------- | ------------ |
| `Owner` | ✔️ | ✔️ | N/A | `string`  | `AccountID` | The sponsor associated with this relationship. This account also pays for the reserve of this object. |
| `Sponsee` | ✔️ | ✔️ | N/A | `string`  | `AccountID` | The sponsee associated with this relationship. |
| `OwnerNode`  | ✔️ | ✔️ | N/A | `string`  | `UInt64`  | A hint indicating which page of the sponsor's owner directory links to this object, in case the directory consists of multiple pages. |
| `SponseeNode`  | ✔️ | ✔️ | N/A | `string`  | `UInt64`  | A hint indicating which page of the sponsee's owner directory links to this object, in case the directory consists of multiple pages. |
| `FeeAmount`  | | | `0` | `string`  | `Amount`  | The (remaining) amount of XRP that the sponsor has provided for the sponsee to use for fees.  |
| `ReserveCount` | | | `0` | `string`  | `UInt32`  | The (remaining) number of `OwnerCount` that the sponsor has provided for the sponsee to use for reserves.  |

### 4.3. Flags

There are two flags on this object:

| Flag Name |  Flag Value  | Modifiable? | Description |
| --------- | ------------ | ----------- | ----------- |
| `lsfSponsorshipRequireSignForFee` | `0x00010000` | Yes | If set, indicates that every use of this sponsor for sponsoring fees requires a signature from the sponsor. |
| `lsfSponsorshipRequireSignForReserve` | `0x00020000` | Yes | If set, indicates that every use of this sponsor for sponsoring fees requires a signature from the sponsor. |

### 4.4. Ownership

The object is owned by `Sponsor`, who also pays the reserve.

### 4.5. Reserve

This object charges 1 reserve.

### 4.6. Deletion

This object will be deleted any time the `FeeAmount` and `ReserveCount` are both `0`. This can be done directly via `SponsorshipSet`, or can occur in the regular flow of transactions, if the sponsorship runs out.

### 4.7. Invariant Checks

- `FeeAmount` >= 0 || `ReserveCount` >= 0
- `SponsorAccount` != `Sponsee`
- `FeeAmount` is nonnegative and denominated in XRP

### 4.8. RPC Name

The `snake_case` form of the ledger object name is `sponsorship`.

## 5. Ledger Entry: `AccountRoot`

### 5.1. Fields

<details>
<summary>

As a reference, [here](https://xrpl.org/docs/references/protocol/ledger-data/ledger-entry-types/accountroot/#accountroot-fields) are the fields that the `AccountRoot` ledger object currently has.

</summary>

| Field Name | Constant? | Required? | Default Value | JSON Type | Internal Type | Description |
| ---------- | --------- | --------- | ------------- | --------- | ------------- | ------------ |
| `Account` | ✔️ | ✔️ | N/A | `string`  | `AccountID` | The identifying (classic) address of this account.  |
| `AccountTxnID` | | | N/A | `string`  | `Hash256` | The identifying hash of the transaction most recently sent by this account. |
| `AMMID` | ✔️ | | N/A | `string`  | `Hash256` | The ledger entry ID of the corresponding AMM ledger entry, if this is an AMM pseudo-account. |
| `Balance` | | | N/A | `string`  | `Amount`  | The account's current XRP balance. |
| `BurnedNFTokens` | | | `0` | `number`  | `UInt32`  | How many total of this account's issued NFTs have been burned.  |
| `Domain`  | | | N/A | `string`  | `Blob` | A domain associated with this account. |
| `EmailHash`  | | | N/A | `string`  | `Hash128` | The md5 hash of an email address.  |
| `FirstNFTokenSequence` | ✔️ | | N/A | `number`  | `UInt32`  | The account's Sequence Number at the time it minted its first non-fungible-token.  |
| `LedgerEntryType`  | ✔️ | ✔️ | N/A | `string`  | `UInt16`  | The value `0x0061`, mapped to the string `AccountRoot`, indicates that this is an `AccountRoot `object. |
| `MessageKey` | | | N/A | `string`  | `Blob` | A public key that may be used to send encrypted messages to this account. |
| `MintedNFTokens` | | | `0` | `number`  | `UInt32`  | How many total non-fungible tokens have been minted by/on behalf of this account.  |
| `NFTokenMinter` | | | N/A | `string`  | `AccountID` | Another account that can mint NFTs on behalf of this account. |
| `OwnerCount` | | ✔️ | N/A | `number`  | `UInt32`  | The number of objects this account owns in the ledger, which contributes to its owner reserve. |
| `PreviousTxnID` | | ✔️ | N/A | `string`  | `Hash256` | The identifying hash of the transaction that most recently modified this object. |
| `PreviousTxnLgrSeq`  | | ✔️ | N/A | `number`  | `UInt32`  | The ledger index that contains the transaction that most recently modified this object.  |
| `RegularKey` | | | N/A | `string`  | `AccountID` | The address of a key pair that can be used to sign transactions for this account instead of the master key. |
| `Sequence` | | ✔️ | N/A | `number`  | `UInt32`  | The [sequence number](https://xrpl.org/docs/references/protocol/data-types/basic-data-types/#account-sequence) of the next valid transaction for this account. |
| `TicketCount`  | | | N/A | `number`  | `UInt32`  | How many Tickets this account owns in the ledger. |
| `TickSize` | | | N/A | `number`  | `UInt8` | [How many significant digits to use for exchange rates of Offers involving currencies issued by this address.](https://xrpl.org/resources/known-amendments/#ticksize) |
| `TransferRate` | | | N/A | `number`  | `UInt32`  | A [transfer fee](https://xrpl.org/docs/concepts/tokens/transfer-fees/) to charge other users for sending currency issued by this account to each other.  |
| `WalletLocator` | | | N/A | `string`  | `Hash256` | An arbitrary 256-bit value that users can set. |
| `WalletSize` | | | N/A | `number`  | `UInt32`  | Unused. |

</details>

We propose these additional fields:
| Field Name | Constant? | Required? | Default Value | JSON Type | Internal Type | Description |
|------------|-----------|-----------|---------------|-----------|---------------|-------------|
|`SponsorAccount`| | |N/A|`string`|`AccountID`| The sponsor that is paying the account reserve for this account. |
|`SponsoredOwnerCount`| | |`0`|`number`|`UInt32`|The number of objects the account owns that are being sponsored by a sponsor.
|`SponsoringOwnerCount`| | |`0`|`number`|`UInt32`|The number of objects the account is sponsoring the reserve for.|
|`SponsoringAccountCount`| | |`0`|`number`|`UInt32`|The number of accounts that the account is sponsoring the reserve for.|

#### 5.1.1. `SponsorAccount`

The `SponsorAccount` field is already added in the ledger common fields (see section [3.1.1](#311-sponsoraccount)), but it has some additional rules associated with it on the `AccountRoot` object.

This field is included if the account was created with a sponsor paying its account reserve. If this sponsored account is deleted, the destination of the `AccountDelete` transaction must equal `SponsorAccount`, so that the sponsor can recoup their fees.

_Note: The `Destination` field of `AccountDelete` will still work as-is if the account is not sponsored, where it can be set to any account._

### 5.2. Account Reserve Calculation

The existing reserve calculation is:

$$ acctReserve + objReserve \* acct.OwnerCount $$

The total account reserve should now be calculated as:

$$
\displaylines{
(acct.SponsorAccount \text{ ? } 0 : acctReserve) + \\
objReserve * (acct.OwnerCount + acct.SponsoringOwnerCount - acct.SponsoredOwnerCount) + \\
acctReserve * acct.SponsoringAccountCount
}
$$

## 6. Transactions: Common Fields

### 6.1. Fields

As a reference, [here](https://xrpl.org/docs/references/protocol/transactions/common-fields/) are the fields that all transactions currently have.

<!--There are too many and I didn't want to list them all, it cluttered up the spec - but maybe it can be a collapsed section?-->

We propose these modifications:

| Field Name | Required? | JSON Type | Internal Type | Description |
| ---------- | --------- | --------- | ------------- | ------------ |
| `Sponsor`  | | `object`  | `STObject`  | This field contains all the information for the sponsorship happening in the transaction. It is included if the transaction is fee- and/or reserve-sponsored. |

#### 6.1.1. `Sponsor`

The `Sponsor` inner object contains all of the information for the sponsorship happening in the transaction.

The fields contained in this object are:

| Field Name | Required? | JSON Type | Internal Type | Description |
| ---------- | --------- | --------- | ------------- | ------------ |
| `SponsorAccount` | ✔️ | `string`  | `AccountID` | The sponsoring account. |
| `Flags`  | ✔️ | `number`  | `UInt16`  | Flags on the sponsorship, indicating what type of sponsorship this is (fee vs. reserve). |
| `SigningPubKey`  | | `string`  | `STBlob`  | The `SigningPubKey` for `SponsorAccount`, if single-signing.  |
| `Signature`  | | `string`  | `STBlob`  | A signature of the transaction from the sponsor, to indicate their approval of this transaction, if single-signing. All signing fields must be included in the signature, including `Sponsor.SponsorAccount` and `Sponsor.Flags`. |
| `Signers` | | `array` | `STArray` | An array of signatures of the transaction from the sponsor's signers to indicate their approval of this transaction, if the sponsor is multi-signing. All signing fields must be included, including `Sponsor.SponsorAccount` and `Sponsor.Flags`. |

##### 6.1.1.1. `Account`

The `Sponsor.Account` field represents the sponsor.

This field **will** be a signing field (it will be included in transaction signatures).

##### 6.1.1.2. `Flags`

The `Flags` field allows the user to specify which sponsorship type(s) they wish to participate in. At least one flag **must** be specified if the `Sponsor` field is included in a transaction.

There are two flag values that are supported:

| Flag Name  |  Flag Value  | Description  |
| ---------- | ------------ | ------------ |
| `tfSponsorFee` | `0x00000001` | Sponsoring (paying for) the fee of the transaction. |
| `tfSponsorReserve` | `0x00000002` | Sponsoring the reserve for any objects created in the transaction. |

This field **will** be a signing field (it will be included in transaction signatures).

##### 6.1.1.3. `SigningPubKey`, `Signature` and `Signers`

Either `Signature` or `Signers` must be included in the final transaction.

There will be no additional transaction fee required for the use of the `Signature` field.

If the `Signers` field is necessary, then the total fee of the transaction will be increased, due to the extra signatures that need to be processed. This is similar to the additional fees for [multisigning](https://xrpl.org/docs/concepts/accounts/multi-signing/). The minimum fee will be $(\\#signatures+1)*base\textunderscore fee$.

The total fee calculation for signatures will now be $( 1+\\# tx.Signers + \\# tx.Sponsor.Signers) * base\textunderscore fee$.

`Signature` and `Signers` **will not** be signing fields (they will not be included in transaction signatures, though they will still be included in the stored transaction).

Either `SigningPubKey`+`Signature` or `Signers` must be included in the transaction. There is one exception to this: if `lsfRequireSignatureForFee`/`lsfRequireSignatureForReserve` are not enabled for the type(s) of sponsorship in the transaction.

### 6.2. Transaction Fee

### 6.3. Failure Conditions

#### 6.3.1. General Failures

- `Sponsor.Signature` is invalid.
- `Sponsor.Signers` is invalid (the signer list isn't on the account, quorum isn't reached, or signature(s) are invalid).
- The `SponsorAccount` doesn't exist on the ledger.
- An invalid sponsorship flag is used.
- `Sponsor.SigningPubKey`, `Sponsor.Signature`, and `Sponsor.Signers` are all included (or other incorrect combinations of signing fields).

#### 6.3.2. Fee Sponsorship Failures

- The sponsor does not have enough XRP to cover the sponsored transaction fee (`telINSUF_FEE_P`)

If a `Sponsorship` object exists:

- The `lsfRequireSignatureForFee` flag is enabled and there is no sponsor signature included.
- There is not enough XRP in the `FeeAmount` to pay for the transaction.

If a `Sponsorship` object does not exist:

- There is no sponsor signature included.

Note: if a transaction doesn't charge a fee (such as an account's first `SetRegularKey` transaction), the transaction will still succeed.

#### 6.3.3. Reserve Sponsorship Failures

- The sponsor does not have enough XRP to cover the reserve (`tecINSUFFICIENT_RESERVE`)
- The transaction does not support reserve sponsorship (see section 6.3.4)

If a `Sponsorship` object exists:

- The `lsfRequireSignatureForReserve` flag is enabled and there is no sponsor signature included.
- There is not enough remaining count in the `ReserveCount` to pay for the transaction.

If a `Sponsorship` object does not exist:

- There is no sponsor signature included.

Note: if a transaction doesn't charge a reserve (such as `AccountSet`), the transaction will still succeed.

#### 6.3.4. Transactions that cannot be sponsored

All transactions (other than pseudo-transactions) may use the `tfSponsorFee` flag, since they all have a fee.

However, some transactions will not support the `tfSponsorReserve` flag.

- [`Batch` transactions](https://github.com/XRPLF/XRPL-Standards/tree/master/XLS-0056-batch)
  - `Batch` does not create any objects on its own, and therefore its use in the outer transaction would be confusing, as users may think that that means that all inner transactions are sponsored. The inner transactions should use `tfSponsorReserve` instead.
- All [pseudo-transactions](https://xrpl.org/docs/references/protocol/transactions/pseudo-transaction-types/pseudo-transaction-types) (currently `EnableAmendment`, `SetFee`, and `UNLModify`)
  - The fees and reserves for those objects are covered by the network, not by any one account.

Also, many transactions, such as `AccountSet`, will have no change in output when using the `tfSponsorReserve` flag, if they do not create any new objects or accounts.

### 6.4. State Changes

#### 6.4.1. Fee Sponsorship State Changes

If a `Sponsorship` object exists, the `tx.Fee` value is decremented from the `Sponsorship.FeeAmount`.

If a `Sponsorship` object does not exist, the `tx.Fee` value is decremented from the sponsor's `AccountRoot.Balance`.

#### 6.4.2. Reserve Sponsorship State Changes

Any account/object that is created as a part of the transaction will have a `Sponsor` field.

The sponsor's `SponsoringOwnerCount` field will be incremented by the number of objects that are sponsored as a part of the transaction, and the `SponsoringAccountCount` field will be incremented by the number of new accounts that are sponsored as a part of the transaction.

The sponsee's `SponsoredOwnerCount` field will be incremented by the number of objects that are sponsored as a part of the transaction.

The `SponsoredOwnerCount`, `SponsoringOwnerCount`, and `SponsoringAccountCount` fields will be decremented when those objects/accounts are deleted.

## 7. Transaction: `SponsorshipSet`

This transaction creates and updates the `Sponsorship` object.

### 7.1. Fields

| Field Name | Required? | JSON Type | Internal Type | Description |
| ---------- | --------- | --------- | ------------- | ------------ |
| `SponsorAccount` | ✔️ | `string`  | `AccountID` | The sponsor associated with this relationship. This account also pays for the reserve of this object. |
| `Sponsee` | ✔️ | `string`  | `AccountID` | The sponsee associated with this relationship. |
| `FeeAmount`  | | `string`  | `Amount`  | The (remaining) amount of XRP that the sponsor has provided for the sponsee to use for fees.  |
| `ReserveCount` | | `number`  | `UInt32`  | The (remaining) amount of reserves that the sponsor has provided for the sponsee to use. |

### 7.2. Flags

| Flag Name | Flag Value | Description |
| --------- | ---------- | ----------- |
| `tfSponsorshipSetRequireSignForFee` | `0x00010000` | Adds the restriction that every use of this sponsor for sponsoring fees requires a signature from the sponsor.  |
| `tfSponsorshipClearRequireSignForFee` | `0x00020000` | Removes the restriction that every use of this sponsor for sponsoring fees requires a signature from the sponsor. |
| `tfSponsorshipSetRequireSignForReserve` | `0x00040000` | Adds the restriction every use of this sponsor for sponsoring fees requires a signature from the sponsor. |
| `tfSponsorshipClearRequireSignForReserve` | `0x00080000` | Removes the restriction every use of this sponsor for sponsoring fees requires a signature from the sponsor.  |
| `tfDeleteObject` | `0x00100000` | Removes the ledger object. |

### 7.2. Failure Conditions

- `tx.Account` is not equal to either `tx.SponsorAccount` or `tx.Sponsee`
- If `tfDeleteObject` is provided:
  - `FeeAmount` is specified
  - `ReserveCount` is specified
  - `tfSponsorshipSetRequireSignForFee` is enabled
  - `tfSponsorshipSetRequireSignForReserve` is enabled

### 7.3. State Changes

- If the object already exists, `Sponsorship.Amount += tx.FeeAmount` and `Sponsorship.ReserveCount += tx.ReserveCount`.
- If the object doesn't exist, it will be created.
- If the `tfDeleteObject` flag is used, it will delete the object. All funds remaining in the object will be sent back to the `SponsorAccount`.
  - Both sponsor and sponsee can delete the object.
  - Existing sponsored objects/accounts will need to go through the `SponsorshipTransfer` process.

## 8. Transaction: `SponsorshipTransfer`

This transaction transfers a sponsor relationship for a particular ledger object's object reserve. The sponsor relationship can either be passed on to a new sponsor, or dissolved entirely (with the sponsee taking on the reserve). Either the sponsor or sponsee may submit this transaction at any point in time.

### 8.1. Fields

| Field Name | Required? | JSON Type | Internal Type | Description |
| ---------- | --------- | --------- | ------------- | ------------ |
| `TransactionType` | ✔️ | `string`  | `UInt16`  |
| `Account` | ✔️ | `string`  | `AccountID` |
| `ObjectID` | | `string`  | `UInt256` |
| `Sponsor` | | `object`  | `STObject`  |

#### 8.1.1. `ObjectID`

This field should be included if this transaction is dealing with sponsored object, rather than on a sponsored account. This field indicates which object the relationship is changing for.

If it is not included, then it refers to the account sending the transaction.

#### 8.1.2. `Sponsor`

The `Sponsor` field is already added in the ledger common fields (see section [5.1.1](#511-sponsor)), but it has some additional rules associated with it on the `SponsorshipTransfer` transaction.

In this case, if `Sponsor` is included with the `tfSponsorReserve` flag, then the reserve sponsorship for the provided object will be transferred to the `Sponsor.Account` instead of passing back to the ledger object's owner.

If there is no `Sponsor` field, or if the `tfSponsorReserve` flag is not included, then the burden of the reserve will be passed back to the ledger object's owner (the former sponsee).

### 8.2. Ending the Sponsorship for a Sponsored Ledger Object

A sponsored ledger object will have the `Sponsor` field attached to it. Ending the sponsor relationship for a sponsored ledger object requires the `ObjectID` parameter, to specify which ledger object.

Two accounts are allowed to submit a `SponsorshipTransfer` relationship to end the sponsor relationship for a sponsored ledger object: either the sponsor for that object or the owner of that object (the sponsee).

### 8.3. Migrating a Sponsorship to a New Account

A sponsorship can be migrated to a new account by including the `Sponsor` field with the `tfSponsorReserve` flag. This can be done for either a sponsored account or a sponsored ledger object.

Two accounts are allowed to submit a `SponsorshipTransfer` relationship to migrate the sponsor relationship: the sponsor or the sponsee.

The sponsor will likely only rarely want to do this (such as if they are transferring accounts), but the sponsee may want to migrate if they change providers.

### 8.4. Failure Conditions

- If transferring the sponsorship, the new sponsor does not have enough reserve for this object/account.
- If dissolving the sponsorship, the owner does not have enough reserve for this object/account.
- The new sponsor does not exist.
- The `tx.Account` neither the sponsor nor the owner of `ObjectID`.

### 8.5. State Changes

- The `Sponsor` field on the object is changed or deleted.
- The old sponsor has its `SponsoringOwnerCount`/`SponsoringAccountCount` decremented by one.
- The new sponsor (if applicable) has its `SponsoringOwnerCount`/`SponsoringAccountCount` incremented by one.
- If there is no new sponsor, then the owner's `SponsoredOwnerCount` will be decremented by one.

## 9. Transaction: `Payment`

A Payment transaction represents a transfer of value from one account to another. (Depending on the path taken, this can involve additional exchanges of value, which occur atomically.) This transaction type can be used for several  [types of payments](https://xrpl.org/docs/references/protocol/transactions/types/payment#types-of-payments).

Payments are also the only way to  [create accounts](https://xrpl.org/docs/references/protocol/transactions/types/payment#creating-accounts).

As a reference, [here](https://xrpl.org/docs/references/protocol/transactions/types/payment) are the fields that `Payment` currently has. This amendment proposes no changes to the fields, only to the flags and behavior.

### 9.1. Flags

As a reference, [here](https://xrpl.org/docs/references/protocol/transactions/types/payment#payment-flags) are the flags that `Payment` currently has:

| Flag Name | Flag Value | Description |
|-----------|------------|-------------|
| `tfNoRippleDirect` | `0x00010000` | Do not use the default path; only use paths included in the `Paths` field. This is intended to force the transaction to take arbitrage opportunities. Most clients do not need this. |
| `tfPartialPayment` | `0x00020000` | If the specified `Amount` cannot be sent without spending more than `SendMax`, reduce the received amount instead of failing outright. See [Partial Payments](#partial-payments) for more details. |
| `tfLimitQuality`   | `0x00040000` | Only take paths where all the conversions have an input:output ratio that is equal or better than the ratio of `Amount`:`SendMax`. See [Limit Quality](#limit-quality) for details. |

This spec proposes the following additions:

| Flag Name | Flag Value | Description |
|-----------|------------|-------------|
| `tfSponsorCreatedAccount` | `0x00080000` | This flag is only valid if the `Payment` is used to create an account. If it is enabled, the created account will be sponsored by the `tx.Account`. |

## 10. Transaction: `AccountDelete`

This transaction deletes an account.

As a reference, [here](https://xrpl.org/docs/references/protocol/transactions/types/accountdelete) are the fields that `AccountDelete` currently has. This amendment proposes no changes to the fields, only to the behavior.

### 10.1. Failure Conditions

Existing failure conditions still apply.

If the `AccountRoot` associated with the `tx.Account` has a `SponsorAccount` field:

- The `Destination` is not equal to `AccountRoot.SponsorAccount`.

If the `AccountRoot` associated with the `tx.Account` has a `SponsoringOwnerCount` or `SponsoringAccountCount` field, the transaction will fail with `tecHAS_OBLIGATIONS`.

### 10.2. State Changes

Existing state changes still apply, including rules around deletion blockers.

If the `AccountRoot` associated with the `tx.Account` has a `SponsorAccount` field, the `SponsorAccount`'s `AccountRoot.SponsoringAccountCount` is decremented by 1.

If the `AccountRoot` associated with the `tx.Account` has a `SponsoredOwnerCount` field, the `SponsorAccount`'s `SponsoringOwnerCount` is decremented by the `tx.Account`'s `SponsoredOwnerCount`.

## 11. Permission: `SponsorFee`

This delegatable granular permission allows an account to sponsor fees on behalf of another account.

## 12. Permission: `SponsorReserve`

This delegatable granular permission allows an account to sponsor reserves on behalf of another account.

## 13. RPC: `account_objects`

### 13.1. Request Fields

The [`account_objects` RPC method](https://xrpl.org/account_objects.html) already exists on the XRPL. As a reference, here are the fields that `account_objects` currently accepts:

| Field Name  | Required? | JSON Type  | Description |
| ----------- | --------- | ---------- | ----------- |
| `account` | ✔️ | `string` | Get ledger entries associated with this account. |
| `deletion_blockers_only` | | `boolean`  | If `true`, only return ledger entries that would block this account from being deleted. The default is `false`.  |
| `ledger_hash`  | | `string` | The unique hash of the ledger version to use. |
| `ledger_index` | | `number` or `string` | The ledger index of the ledger to use, or a shortcut string to choose a ledger automatically.  |
| `limit` | | `number` | The maximum number of ledger entries to include in the results. Must be within the inclusive range `10` to `400` on non-admin connections. The default is `200`. |
| `marker`  | | `any` | Value from a previous paginated response. Resume retrieving data where that response left off. |
| `type`  | | `string` | Filter results to a specific type of ledger entry. This field accepts canonical names of ledger entry types (case insensitive) or short names. Ledger entry types that can't appear in an owner directory are not allowed. If omitted, return ledger entries of all types. |

We propose this additional field:

| Field Name  | Required? | JSON Type | Description |
| ----------- | --------- | --------- | ----------- |
| `sponsored` | | `boolean` | If `true`, only return ledger entries that are sponsored. If `false`, only return ledger entries that are not sponsored. If omitted, return all objects. |

### 13.2. Response Fields

The response fields remain the same.

## 14. RPC: `account_sponsoring`

The `account_sponsoring` RPC method is used to fetch a list of objects that an account is sponsoring; namely, a list of objects where the `SponsorAccount` is the given account. It has a very similar API to the [`account_objects` method](https://xrpl.org/account_objects.html).

### 14.1. Request Fields

| Field Name  | Required? | JSON Type  | Description  |
| ----------- | --------- | ---------- | ------------ |
| `account` | ✔️ | `string` | The sponsor in question.  |
| `deletion_blockers_only` | | `boolean`  | If `true`, the response only includes objects that would block this account from being deleted. The default is `false`. |
| `ledger_hash`  | | `string` | A hash representing the ledger version to use. |
| `ledger_index` | | `number` or `string` | The ledger index of the ledger to use, or a shortcut string to choose a ledger automatically. |
| `limit` | | `number` | The maximum number of objects to include in the results. |
| `marker`  | | `any` | Value from a previous paginated response. Resume retrieving data where that response left off. |
| `type`  | | `string` | Filter results by a ledger entry type. Some examples are `offer` and `escrow`.  |

### 14.2. Response Fields

The response fields are nearly identical to `account_objects`.

| Field Name | Always Present? | JSON Type | Description |
| ---------- | --------------- | --------- | ----------- |
| `account` | ✔️ | `string`  | The account this request corresponds to. |
| `sponsored_objects`  | ✔️ | `array` | Array of ledger entries in this account's owner directory. This includes entries that are owned by this account and entries that are linked to this account but owned by someone else, such as escrows where this account is the destination. Each member is a ledger entry in its raw ledger format. This may contain fewer entries than the maximum specified in the `limit` field. |
| `ledger_hash`  |  | `string`  | The identifying hash of the ledger that was used to generate this response.  |
| `ledger_index` |  | `number`  | The ledger index of the ledger that was used to generate this response.  |
| `ledger_current_index` |  | `number`  | The ledger index of the open ledger that was used to generate this response. |
| `limit` |  | `number`  | The limit that was used in this request, if any. |
| `marker`  |  | `any` | Server-defined value indicating the response is paginated. Pass this to the next call to resume where this call left off. Omitted when there are no additional pages after this one. |
| `validated`  |  | `boolean` | If `true`, the information in this response comes from a validated ledger version. Otherwise, the information is subject to change.  |

## 15. Security

### 15.1. Security Axioms

Both the sponsee _and_ the sponsor must agree to enter into a sponsor relationship. The sponsee must actively consent to the sponsor handling the reserve, and the sponsor must be willing to take on that reserve. A signature from both parties ensures that this is the case.

A sponsor will never be stuck sponsoring an sponsee's account or object it no longer wants to support, because it can submit a `SponsorshipTransfer` transaction at any point.

The sponsor's signature must _always_ include the `Account` and `Sequence` fields, to prevent signature replay attacks (where the sponsor's signature can be reused to sponsor an object or account that they did not want to sponsor).

When sponsoring transaction fees, the sponsor must approve of the `Fee` value of the transaction, since that is the amount that they will be paying.

When sponsoring reserves, the sponsor's signature must include any aspects of the transaction that involve a potential account/object reserve. This would include the `Destination` field of a `Payment` transaction (and whether it is a new account) and the `TicketSequence` field of a `TicketCreate` transaction (since that dictates how many `Ticket` objects are created, each of which results in one object reserve).

A sponsee cannot take advantage of the generosity of their sponsor, since the sponsor must sign every transaction it wants to sponsor the ledger objects for. A sponsee also must not be able to change the sponsorship type that the sponsor is willing to engage in, as this could lock up to 500 of the sponsor's XRP (in the case of 250 tickets being created in one `TicketCreate` transaction).

An axiom that is out of scope: the sponsee may not have any control over a sponsorship transfer (the sponsor may transfer a sponsorship without the sponsee's consent). This is akin to a loanee having no control over a bank selling their mortgage to some other company, or a lender selling debt to a debt collection agency.

### 15.2. Signatures

Since a fee sponsorship must approve of the `Fee` field, and a reserve sponsorship must approve of a broad set of transaction fields, the sponsor must always sign the whole transaction. This also avoids needing to have different sponsorship processes for different sponsorship types. This includes the non-signature parts of the `Sponsor` object (`Sponsor.Account` and `Sponsor.Flags`). The same is true for the sponsee's transaction signature; the sponsee must approve of the sponsor and sponsorship type.

A sponsor's `Signature` cannot be replayed or attached to a different transaction, since the whole transaction (including the `Account` and `Sequence` values) must be signed.

## 16. Invariants

An [invariant](https://xrpl.org/docs/concepts/consensus-protocol/invariant-checking/) is a statement, usually an equation, that must always be true for every valid ledger state on the XRPL. Invariant checks serve as a last line of defense against bugs; the `tecINVARIANT_FAILED` error is thrown if an invariant is violated (which ideally should never happen).

### 16.1. Tracking Owner Counts

A transaction that creates a ledger object either increments an account's `OwnerCount` by 1 or increments two separate accounts' `SponsoringOwnerCount` and `SponsoredOwnerCount` by 1. The opposite happens when a ledger object is deleted.

The equivalent also should happen with `SponsoringAccountCount`.

### 16.2. Balancing `SponsoredOwnerCount` and `SponsoringOwnerCount`

$$ \sum*{accounts} Account.SponsoredOwnerCount = \sum*{accounts} Account.SponsoringOwnerCount $$

In other words, the sum of all accounts' `SponsoredOwnerCount`s must be equal to the sum of all accounts' `SponsoringOwnerCount`s. This ensures that every sponsored object is logged as being sponsored and also has a sponsor.

## 17. Example Flows

Each example will show what the transaction will look like before **and** after both the sponsor and sponsee sign the transaction.

The unsigned transaction must be autofilled before it is passed to the sponsor to sign. Tooling can be updated to handle combining the sponsor and sponsee signatures, similar to helper functions that already exist for multisigning.

### 17.1. Fee Sponsorship

#### 17.1.1. The Unsigned Transaction

<details open>

```typescript
{
  TransactionType: "Payment",
  Account: "rOldB3E44wS6SM7KL3T3b6nHX3Jjua62wg",
  Destination: "rNewfcu9RJa5W1ncAuEgLH1Xpi4j1vzXjr",
  Amount: "20000000",
  Sequence: 3,
  Fee: "10",
  Sponsor: {
    Account: "rSponsor1VktvzBz8JF2oJC6qaww6RZ7Lw",
    Flags: 1
  }
}
```

</details>

#### 17.1.2. The Signed Transaction

<details open>

```typescript
{
  TransactionType: "Payment",
  Account: "rSender7NwD9vmNf5dvTbW4FQDNSRsfPv6",
  Destination: "rDestinationT6N5fJdaHnRqLpW1D8oFrZ",
  Amount: "20000000",
  Sequence: 3,
  Fee: "10",
  Sponsor: {
    Account: "rSponsor1VktvzBz8JF2oJC6qaww6RZ7Lw",
    Flags: 1,
    SigningPubKey: "03072BBE5F93D4906FC31A690A2C269F2B9A56D60DA9C2C6C0D88FB51B644C6F94", // rSponsor's public key
    Signature: "3045022100C15AFB7C0C4F5EDFEC4667B292DAB165B96DAF3FFA6C7BBB3361E9EE19E04BC70220106C04B90185B67DB2C67864EB0A11AE6FB62280588954C6E4D9C1EF3710904D"
  },
  SigningPubKey: "03A8D0093B0CD730F25E978BF414CA93084B3A2CBB290D5E0E312021ED2D2C1C8B", // rAccount's public key
  TxnSignature: "3045022100F2AAF90D8F9BB6C94C0C95BA31E320FC601C7BAFFF536CC07076A2833CB4C7FF02203F3C76EB34ABAD61A71CEBD42307169CDA65D9B3CA0EEE871210BEAB824E524B"
}
```

</details>

### 17.2. Account Sponsorship

The only way an account can be created is via a `Payment` transaction. So the sponsor relationship must be initiated on the `Payment` transaction.

#### 17.2.1. The Unsigned Transaction

<details open>

```typescript
{
  TransactionType: "Payment",
  Account: "rOldB3E44wS6SM7KL3T3b6nHX3Jjua62wg",
  Destination: "rNewfcu9RJa5W1ncAuEgLH1Xpi4j1vzXjr",
  Amount: "20000000",
  Sequence: 3,
  Fee: "10",
  Sponsor: {
    Account: "rSponsor1VktvzBz8JF2oJC6qaww6RZ7Lw",
    Flags: 2
  }
}
```

</details>

#### 17.2.2. The Signed Transaction

<details open>

```typescript
{
  TransactionType: "Payment",
  Account: "rOldB3E44wS6SM7KL3T3b6nHX3Jjua62wg",
  Destination: "rNewfcu9RJa5W1ncAuEgLH1Xpi4j1vzXjr",
  Amount: "20000000",
  Sequence: 3,
  Fee: "10",
  Sponsor: {
    Account: "rSponsor1VktvzBz8JF2oJC6qaww6RZ7Lw",
    Flags: 2,
    SigningPubKey: "03072BBE5F93D4906FC31A690A2C269F2B9A56D60DA9C2C6C0D88FB51B644C6F94", // rSponsor's public key
    Signature: "30440220702ABC11419AD4940969CC32EB4D1BFDBFCA651F064F30D6E1646D74FBFC493902204E5B451B447B0F69904127F04FE71634BD825A8970B9467871DA89EEC4B021F8"
  },
  SigningPubKey: "03BC74CA0B765281E31E342017D97B3F6743A05FBA23D2114B98FC8AD26D92856C", // rAccount's public key
  TxnSignature: "30440220245217F931FDA0C5E68B935ABB4920211D5B6182878583124DE4663B19F00BEC022070BE036264760551CF40E9DAFC8B84036FA70E7EE7257BB7E39AEB7354B2EB86"
}
```

</details>

### 17.3. Object Sponsorship

#### 17.3.1. The Unsigned Transaction

<details open>

```typescript
{
  TransactionType: "TicketCreate",
  Account: "rAccount4yjv1j2x79wXxRVXnFbwsjUWXo",
  TicketCount: 100,
  Sequence: 3,
  Fee: "10",
  Sponsor: {
    Account: "rSponsor1VktvzBz8JF2oJC6qaww6RZ7Lw",
    Flags: 2
  }
}
```

</details>

#### 17.3.2. The Signed Transaction

<details open>

```typescript
{
  TransactionType: "TicketCreate",
  Account: "rAccount4yjv1j2x79wXxRVXnFbwsjUWXo",
  TicketCount: 100,
  Sequence: 3,
  Fee: "10",
  Sponsor: {
    Account: "rSponsor1VktvzBz8JF2oJC6qaww6RZ7Lw",
    Flags: 2,
    SigningPubKey: "03072BBE5F93D4906FC31A690A2C269F2B9A56D60DA9C2C6C0D88FB51B644C6F94", // rSponsor's public key
    Signature: "30450221009878F3A321250341886FE344E0B50700C8020ABAA25301925BD84DDB5421D432022002A3C72C54BACB5E7DAEC48E2A1D75DCBB8BA3B2212C7FC22F070CCABAF76EC1"
  },
  SigningPubKey: "03BC74CA0B765281E31E342017D97B3F6743A05FBA23D2114B98FC8AD26D92856C", // rAccount's public key
  TxnSignature: "3044022047CB72DA297B067C0E69045B7828AD660F8198A6FA03982E31CB6D27F0946DDE022055844EB63E3BFF7D9ABFB26645AA4D2502E143F4ABEE2DE57EB87A1E5426E010"
}
```

</details>

## 18. Rationale

The primary motivation for this design is to enable companies, token issuers, and other entities to reduce onboarding friction for end users by covering transaction fees and reserve requirements on their behalf. Today, users must self-fund both, or companies must essentially donate XRP to users with no controls over how they use it, before interacting with the XRPL. This creates a barrier to entry for use cases such as token distribution, NFT minting, or enterprise onboarding. Sponsorship provides a mechanism for entities with established XRP balances to subsidize these costs while maintaining strong on-chain accountability.

## n+1. Remaining TODOs/Open Questions

- How will this work for objects like trustlines, where multiple accounts might be holding reserves for it?
  - Maybe a second `Sponsor` field or something?
- How do we handle account creation? The actual account owner's signing keys aren't involved in that at all... Maybe just a new flag on the payment saying you'll pay the reserve for the account?
- Should fee sponsorship allow for the existing fee paradigm that allows users to dip below the reserve?
- Should we allow sponsorship of creating another account? e.g. Account A is sponsored by Sponsor, A creates B, does Sponsor also sponsor B or does this fail if A doesn't have the funds to create B? No
- Should `account_sponsoring` be Clio-only?
- Should a sponsored account be prevented from sponsoring other accounts? By default the answer is no, so unless there's a reason to do so, we should leave it as is.

### Answered and TODO

- Should there be a "max XRP per transaction" field in `Sponsorship`? Yes, TODO
- Should the `Sponsorship` hold the XRP or pull from the `SponsorAccount`'s account? Pull from the `SponsorAccount`'s account, TODO
- 

# Appendix

## Appendix A: FAQ

### A.1: Does the sponsee receive any XRP for the reserve?

No, there is no XRP transfer in a sponsorship relationship - the XRP stays in the sponsor's account. The burden of the reserve for that object/account is just transferred to the sponsor.

### A.2: What happens if you try to delete your account and you have sponsored objects?

If the account itself is sponsored, then it can be deleted, but the destination of the `AccountDelete` transaction (in other words, where the leftover XRP goes) **must** be the sponsor's account. This ensures that the sponsor gets their reserve back, and the sponsee cannot run away with those funds.

If the sponsee still has sponsored objects, those objects will follow the same rules of [deletion blockers](https://xrpl.org/docs/concepts/accounts/deleting-accounts/#requirements). Whether or not they are sponsored is irrelevant.

If a sponsored object is deleted (either due to normal object deletion processes or, in the case of objects that aren't deletion blockers, because the owner account is deleted), the sponsor's reserve becomes available again.

### A.3: What if a sponsor that is sponsoring a few objects wants to delete their account?

An account cannot be deleted if it is sponsoring **any** existing accounts or objects. They will need to either delete those objects (by asking the owner to do so, as they cannot do so directly) or use the `SponsorshipTransfer` transaction to relinquish control of them.

### A.4: Does a sponsor have any powers over an object they pay the reserve for? I.e. can they delete the object?

No. If a sponsor no longer wants to support an object, they can always use the `SponsorshipTransfer` transaction instead to transfer the reserve burden back to the sponsee.

### A.5: What if a sponsee refuses to delete their account when a sponsor wants to stop supporting their account?

The sponsor will have the standard problem of trying to get ahold of a debtor to make them pay. They may use the `SponsorshipTransfer` transaction to put the onus on the sponsee. If the sponsee does not have enough XRP to cover the reserve for those objects, they will not be able to create any more objects until they do so.

### A.6: What happens if the sponsor tries to `SponsorshipTransfer` but the sponsee doesn't have enough funds to cover the reserve?

If the sponsor really needs to get out of the sponsor relationship ASAP without recouping the value of the reserve, they can pay the sponsee the amount of XRP they need to cover the reserve. These steps can be executed atomically via a [Batch transaction](https://github.com/XRPLF/XRPL-Standards/tree/master/XLS-0056-batch), to ensure that the sponsee can't do something else with the funds before the `SponsorshipTransfer` transaction is validated.

### A.7: Would sponsored accounts carry a lower reserve?

No, they would still carry a reserve of 1 XRP at current levels.

### A.8: Can an existing unsponsored ledger object/account be sponsored?

Yes, with the `SponsorshipTransfer` transaction.

### A.9: Can a sponsored account be a sponsor for other accounts/objects?

Yes, though they will have to use their own XRP for this (not from another sponsor).

### A.10: Can a sponsored account hold unsponsored objects, or objects sponsored by a different sponsor?

Yes, and yes.

### A.11: What if I want different sponsors to sponsor the transaction fee vs. the reserve for the same transaction?

That will not be supported by this proposal. If you have a need for this, please provide example use-cases.

### A.12: Won't it be difficult to add two signatures to a transaction?

This is something that good tooling can solve. It could work similarly to how multisigning is supported in various tools.

### A.13. Why not instead do [insert some other design]?

See Appendix B for the alternate designs that were considered and why this one was preferred. If you have another one in mind, please describe it in the comments and we can discuss.

### A.14: How is this account sponsorship model different from/better than [XLS-23d, Lite Accounts](https://github.com/XRPLF/XRPL-Standards/tree/master/XLS-0023-lite-accounts)?

- Sponsored accounts do not have any restrictions, and can hold objects.
- Sponsored accounts require the same reserve as a normal account (this was one of the objections to the Lite Account proposal).
- Lite accounts can be deleted by their sponsor.

### A.15: How will this work for objects like trustlines, where multiple accounts might be holding reserves for it?

The answer to this question is still being explored. One possible solution is to add a second field, `Sponsor2`, to handle the other reserve.

### A.16: How does this proposal work in conjunction with [XLS-49d](https://github.com/XRPLF/XRPL-Standards/tree/master/XLS-0049-multiple-signer-lists)? What signer list(s) have the power to sponsor fees or reserves?

Currently, only the global signer list is supported. Another `SignerListID` value could be added to support sponsorship. Transaction values can only go up to $2^{16}$, since the `TransactionType` field is a `UInt16`, but the `SignerListID` field goes up to $2^{32}$, so there is room in the design for additional values that do not correlate to a specific transaction type.

## Appendix B: Alternate Designs

### B.1: Add a `Sponsor` to the account

This design involved updating `AccountSet` to allow users to add a `Sponsor` to their account (with a signature from the sponsor as well). The sponsor would then sponsor every object from that account while the field was active, and either the sponsor or the account could remove the sponsorship at any time.

This was a previous version of the spec, but it made more sense for the relationship to be specific to a specific transaction(s), to prevent abuse (the sponsor should decide what objects they want to support and what objects they don't want to support).

The current design also supports having different sponsors for different objects, which allows users to use a broad set of services and platforms, instead of being locked into one.

<!--Stellar uses this philosophy ("the relationship should be ephemeral to prevent abuse") for their sponsored reserves design, which I like.-->

### B.2: A Wrapper Transaction

There would be a wrapper transaction (tentatively named `Relay`), similar to `Batch` in [XLS-56d](https://github.com/XRPLF/XRPL-Standards/discussions/162), that the sponsor would sign. It would contain a sub-transaction from the sponsee.

It would look something like this:
|FieldName | Required? | JSON Type | Internal Type |
|----------|------------|----------|---------------|
|`TransactionType`|✔️|`string`|`UInt16`|
|`Account`|✔️|`string`|`STAccount`|
|`Fee`|✔️|`string`|`STAmount`|
|`Transaction`|✔️|`object`|`STTx`|

This was a part of a previous version of the spec (inspired by Stellar's [sandwich transaction design](https://developers.stellar.org/docs/learn/encyclopedia/sponsored-reserves#begin-and-end-sponsorships) for their implementation of sponsored reserves), but the existing design felt cleaner. From an implementation perspective, it's easier to have the fee payer as a part of the existing transaction rather than as a part of a wrapper transaction, since that info needs to somehow get passed down the stack. Also, while the wrapper transaction paradigm will be used in XLS-56d, they should be used sparingly in designs - only when necessary - as their flow is rather complicated in the `rippled` code.

In addition, the signing process becomes complicated (as discovered in the process of developing XLS-56d). You have to somehow prevent the sponsor from submitting the as-is signed transaction to the network, without including it in the wrapper transaction.

### B.3: A Create-Accept-Cancel Flow

The rough idea of this design was to have a new set of transactions (e.g. `SponsorCreate`/`SponsorAccept`/`SponsorCancel`/`SponsorFinish`) where a sponsor could take on the reserve for an existing object.

This design was never seriously considered, as it felt too complicated and introduced several new transactions. It also doesn't support adding a sponsor to the object at object creation time, which is a much smoother UX and never requires the owner/sponsee to hold enough XRP for the reserve.
