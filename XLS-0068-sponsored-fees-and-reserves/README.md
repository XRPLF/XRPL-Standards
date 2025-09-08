<pre>
  xls: XLS-68d
  title: Sponsored Fees and Reserves
  description: Allow an account to fund fees and reserves on behalf of another account
  author: Mayukha Vadari (@mvadari)
  created: 2024-05-02
  status: Stagnant
  category: Amendment
</pre>

# Sponsored Fees and Reserves

## Abstract

As the blockchain industry grows, many projects want to be able to build on the blockchain, but abstract away the complexities of using the blockchain - users don't need to submit transactions or deal with transaction fees themselves, they can just pay the platform to handle all that complexity (though, of course, the users still control their own keys).

Some projects also want to onboard users more easily, allowing users to create accounts without needing to pay for their own account reserve or needing to gift accounts free XRP to cover the reserve (this could get rather expensive if it is exploited).

In order to handle these sorts of use-cases, this proposal adds a process for users to maintain control over their keys and account, but to have another account (e.g. a platform) submit the transaction and pay the transaction fee and/or reserves on their behalf. This proposal supports both account and object reserves.

Similar features on other chains are often called "sponsored transactions", "meta-transactions", or "relays".

## 1. Overview

Accounts can include signatures from sponsors in their transactions that will allow the sponsors to pay the transaction fee for the transaction, and/or the reserve for any accounts/objects created in the transaction.

We propose modifying one ledger object and creating one new transaction type:

- `AccountRoot` ledger object
- `SponsorTransfer` transaction type

The common fields for all ledger objects and all transactions will also be modified.

In addition, there will be a modification to the `account_objects` RPC method, and a new RPC method called `account_sponsoring`.

This feature will require an amendment, tentatively titled `featureSponsor`.

### 1.1. Terminology

- **Sponsor**: The account that is covering the reserve or paying the transaction fee on behalf of another account.
- **Sponsee**: The account that the sponsor is paying a transaction fee or reserve on behalf of.
- **Owner**: The account that owns a given object (or the account itself). This is often the same as the sponsee.
- **Sponsored account**: An account that a sponsor is covering the reserve for (currently priced at 10 XRP).
- **Sponsored object**: A non-account ledger object that a sponsor is covering the reserve for (currently priced at 2 XRP).
- **Sponsor relationship**: The relationship between a sponsor and sponsee.
- **Sponsorship type**: The "type" of sponsorship - sponsoring transaction fees vs. sponsoring reserves.

### 1.2. The Sponsorship Flow

In this scenario, the sponsor, Spencer, wants to pay the transaction fee and/or reserve for the sponsee Alice's transaction.

- Alice constructs her transaction and autofills it (so that all fields, including the fee and sequence number, are included in the transaction). She adds Spencer's account and sponsorship type to the transaction as well.
- Spencer signs the transaction and provides his signature to Alice.
- Alice adds Spencer's public key and signature to her transaction.
- Alice signs and submits her transaction as normal.

### 1.3. Recouping a Sponsored Object Reserve

In this scenario, the sponsor, Spencer, would like to re-obtain the reserve that is currently trapped due to his sponsorship of Alice's object.

Spencer can submit a `SponsorTransfer` transaction, which allows him to pass the onus of the reserve back to Alice, or pass it onto another sponsor.

### 1.4. Recouping a Sponsored Account Reserve

In this scenario, the sponsor, Spencer, would like to retrieve his reserve from sponsoring Alice's account.

There are two ways in which he could do this:

- If Alice is done using her account, she can submit an `AccountDelete` transaction, which will send all remaining funds in the account back to Spencer.
- If Alice would like to keep using her account, or would like to switch to a different provider, she (or Spencer) can submit a `SponsorTransfer` transaction to either remove sponsorship or transfer it to the new provider.

## 2. On-Ledger Objects: Common Fields

### 2.1. Fields

As a reference, here are the fields that all ledger objects currently have:

| Field Name        | Required? | JSON Type | Internal Type |
| ----------------- | --------- | --------- | ------------- |
| `LedgerIndex`     | ✔️        | `string`  | `Hash256`     |
| `LedgerEntryType` | ✔️        | `string`  | `UInt16`      |
| `Flags`           | ✔️        | `number`  | `UInt16`      |

We propose this additional field:
| Field Name | Required? | JSON Type | Internal Type |
|------------|-----------|-----------|---------------|
|`SponsorAccount`| |`string`|`AccountID`|

#### 2.1.1. `SponsorAccount`

The `SponsorAccount` is the sponsor that is paying the reserve for this ledger object.

## 3. On-Ledger Object: `AccountRoot`

### 3.1. Fields

<details>
<summary>

As a reference, [here](https://xrpl.org/docs/references/protocol/ledger-data/ledger-entry-types/accountroot/#accountroot-fields) are the fields that the `AccountRoot` ledger object currently has.

</summary>

| Field Name             | Required? | JSON Type | Internal Type | Description                                                                                                                                                           |
| ---------------------- | --------- | --------- | ------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `Account`              | ✔️        | `string`  | `AccountID`   | The identifying (classic) address of this account.                                                                                                                    |
| `AccountTxnID`         |           | `string`  | `Hash256`     | The identifying hash of the transaction most recently sent by this account.                                                                                           |
| `AMMID`                |           | `string`  | `Hash256`     | The ledger entry ID of the corresponding AMM ledger entry, if this is an AMM pseudo-account.                                                                          |
| `Balance`              |           | `string`  | `Amount`      | The account's current XRP balance.                                                                                                                                    |
| `BurnedNFTokens`       |           | `number`  | `UInt32`      | How many total of this account's issued NFTs have been burned.                                                                                                        |
| `Domain`               |           | `string`  | `Blob`        | A domain associated with this account.                                                                                                                                |
| `EmailHash`            |           | `string`  | `Hash128`     | The md5 hash of an email address.                                                                                                                                     |
| `FirstNFTokenSequence` |           | `number`  | `UInt32`      | The account's Sequence Number at the time it minted its first non-fungible-token.                                                                                     |
| `LedgerEntryType`      | ✔️        | `string`  | `UInt16`      | The value `0x0061`, mapped to the string `AccountRoot`, indicates that this is an `AccountRoot `object.                                                               |
| `MessageKey`           |           | `string`  | `Blob`        | A public key that may be used to send encrypted messages to this account.                                                                                             |
| `MintedNFTokens`       |           | `number`  | `UInt32`      | How many total non-fungible tokens have been minted by/on behalf of this account.                                                                                     |
| `NFTokenMinter`        |           | `string`  | `AccountID`   | Another account that can mint NFTs on behalf of this account.                                                                                                         |
| `OwnerCount`           | ✔️        | `number`  | `UInt32`      | The number of objects this account owns in the ledger, which contributes to its owner reserve.                                                                        |
| `PreviousTxnID`        | ✔️        | `string`  | `Hash256`     | The identifying hash of the transaction that most recently modified this object.                                                                                      |
| `PreviousTxnLgrSeq`    | ✔️        | `number`  | `UInt32`      | The ledger index that contains the transaction that most recently modified this object.                                                                               |
| `RegularKey`           |           | `string`  | `AccountID`   | The address of a key pair that can be used to sign transactions for this account instead of the master key.                                                           |
| `Sequence`             | ✔️        | `number`  | `UInt32`      | The [sequence number](https://xrpl.org/docs/references/protocol/data-types/basic-data-types/#account-sequence) of the next valid transaction for this account.        |
| `TicketCount`          |           | `number`  | `UInt32`      | How many Tickets this account owns in the ledger.                                                                                                                     |
| `TickSize`             |           | `number`  | `UInt8`       | [How many significant digits to use for exchange rates of Offers involving currencies issued by this address.](https://xrpl.org/resources/known-amendments/#ticksize) |
| `TransferRate`         |           | `number`  | `UInt32`      | A [transfer fee](https://xrpl.org/docs/concepts/tokens/transfer-fees/) to charge other users for sending currency issued by this account to each other.               |
| `WalletLocator`        |           | `string`  | `Hash256`     | An arbitrary 256-bit value that users can set.                                                                                                                        |
| `WalletSize`           |           | `number`  | `UInt32`      | Unused.                                                                                                                                                               |

</details>

We propose these additional fields:
| Field Name | Required? | JSON Type | Internal Type |
|------------|-----------|-----------|---------------|
|`SponsorAccount`| |`string`|`AccountID`|
|`SponsoredOwnerCount`| |`number`|`UInt32`|
|`SponsoringOwnerCount`| |`number`|`UInt32`|
|`SponsoringAccountCount`| |`number`|`UInt32`|

#### 3.1.1. `SponsorAccount`

The `SponsorAccount` field is already added in the ledger common fields (see section [2.1.1](#211-sponsoraccount)), but it has some additional rules associated with it on the `AccountRoot` object.

This field is included if the account was created with a sponsor paying its account reserve. If this sponsored account is deleted, the destination of the `AccountDelete` transaction must equal `SponsorAccount`, so that the sponsor can recoup their fees.

_Note: The `Destination` field of `AccountDelete` will still work as-is if the account is not sponsored, where it can be set to any account._

#### 3.1.2. `SponsoredOwnerCount`

This is the number of objects the account owns that are being sponsored by a sponsor.

#### 3.1.3. `SponsoringOwnerCount`

This is the number of objects the account is sponsoring the reserve for.

#### 3.1.4. `SponsoringAccountCount`

This is the number of accounts that the account is sponsoring the reserve for.

### 3.2. Account Reserve Calculation

The existing reserve calculation is:

$$ acctReserve + objReserve \* acct.OwnerCount $$

The total account reserve should now be calculated as:

$$
\displaylines{
(acct.SponsorAccount \text{ ? } 0 : acctReserve)  + \\
objReserve * (acct.OwnerCount + acct.SponsoringOwnerCount - acct.SponsoredOwnerCount) + \\
acctReserve * acct.SponsoringAccountCount
}
$$

## 4. Transactions: Common Fields

### 4.1. Fields

As a reference, [here](https://xrpl.org/docs/references/protocol/transactions/common-fields/) are the fields that all transactions currently have.

<!--There are too many and I didn't want to list them all, it cluttered up the spec - but maybe it can be a collapsed section?-->

We propose these modifications:

| Field Name | Required? | JSON Type | Internal Type |
| ---------- | --------- | --------- | ------------- |
| `Sponsor`  |           | `object`  | `STObject`    |

#### 4.1.1. `Sponsor`

The `Sponsor` inner object contains all of the information for the sponsorship happening in the transaction.

The fields contained in this object are:

| Field Name      | Required? | JSON Type | Internal Type |
| --------------- | --------- | --------- | ------------- |
| `Account`       | ✔️        | `string`  | `AccountID`   |
| `Flags`         | ✔️        | `number`  | `UInt16`      |
| `SigningPubKey` |           | `string`  | `STBlob`      |
| `Signature`     |           | `string`  | `STBlob`      |
| `Signers`       |           | `array`   | `STArray`     |

##### 4.1.1.1. `Account`

The `Sponsor.Account` field represents the sponsor.

This field **will** be a signing field (it will be included in transaction signatures).

##### 4.1.1.2. `Flags`

The `Flags` field allows the user to specify which sponsorship type(s) they wish to participate in. At least one flag **must** be specified if the `Sponsor` field is included in a transaction.

There are two flag values that are supported:

- `0x00000001`: `tfSponsorFee`, sponsoring (paying for) the fee of the transaction.
- `0x00000002`: `tfSponsorReserve`, sponsoring the reserve for any objects created in the transaction.

This field **will** be a signing field (it will be included in transaction signatures).

##### 4.1.1.3. `SigningPubKey` and `Signature`

These fields are included if the sponsor is signing with a single signature (as opposed to multi-sign). This field contains a signature of the transaction from the sponsor, to indicate their approval of this transaction. All signing fields must be included in the signature, including `Sponsor.Account` and `Sponsor.Flags`.

Either `Signature` or `Signers` must be included in the final transaction.

There will be no additional transaction fee required for the use of the `Signature` field.

`Signature` **will not** be a signing field (it will not be included in transaction signatures, though it will still be included in the stored transaction).

##### 4.1.1.4. `Signers`

This field contains an array of signatures of the transaction from the sponsor,'s signers to indicate their approval of this transaction. All signing fields must be included, including `Sponsor.Account` and `Sponsor.Flags`.

Either `Signature` or `Signers` must be included in the final transaction.

If the `Signers` field is necessary, then the total fee of the transaction will be increased, due to the extra signatures that need to be processed. This is similar to the additional fees for [multisigning](https://xrpl.org/docs/concepts/accounts/multi-signing/). The minimum fee will be $(\\#signatures+1)*base\textunderscore fee$.

The total fee calculation for signatures will now be $( 1+\\# tx.Signers + \\# tx.Sponsor.Signers) * base\textunderscore fee$.

This field **will not** be a signing field (it will not be included in transaction signatures, though it will still be included in the stored transaction).

### 4.2. Failure Conditions

#### 4.2.1. General Failures

- `Sponsor.Signature` is invalid
- `Sponsor.Signers` is invalid (the signer list isn't on the account, quorum isn't reached, or signature(s) are invalid)
- The sponsor account doesn't exist on the ledger
- An invalid sponsorship flag is used

#### 4.2.2. Fee Sponsorship Failures

- The sponsor does not have enough XRP to cover the transaction fee
<!--
	* TODO: should this obey the existing fee paradigm that allows users to dip below the reserve?
-->

#### 4.2.3. Reserve Sponsorship Failures

- The sponsor does not have enough XRP to cover the reserve (`tecINSUFFICIENT_RESERVE`)
- The transaction does not support reserve sponsorship (see section 4.4)

### 4.3. State Changes

#### 4.3.1. Fee Sponsorship State Changes

The fee will be deducted from the sponsor instead of the sponsee. That's it.

#### 4.3.2. Reserve Sponsorship State Changes

Any account/object that is created as a part of the transaction will have a `Sponsor` field.

The sponsor's `SponsoringOwnerCount` field will be incremented by the number of objects that are sponsored as a part of the transaction, and the `SponsoringAccountCount` field will be incremented by the number of new accounts that are sponsored as a part of the transaction.

The sponsee's `SponsoredOwnerCount` field will be incremented by the number of objects that are sponsored as a part of the transaction.

The `SponsoredOwnerCount`, `SponsoringOwnerCount`, and `SponsoringAccountCount` fields will be decremented when those objects/accounts are deleted.

### 4.4. Transactions that cannot be sponsored

All transactions (other than pseudo-transactions) may use the `tfSponsorFee` flag, since they all have a fee.

However, some transactions will not support the `tfSponsorReserve` flag.

- `Batch` (from [XLS-56d](https://github.com/XRPLF/XRPL-Standards/discussions/162))
  - It doesn't make any sense for `Batch` to support that flag. The sub-transactions should use `tfSponsorReserve` instead.
- All pseudo-transactions (currently `EnableAmendment`, `SetFee`, and `UNLModify`)
  - The reserves for those objects are covered by the network, not by any one account.

Also, many transactions, such as `AccountSet`, will have no change in output when using the `tfSponsorReserve` flag, if they do not create any new objects or accounts.

## 5. Transaction: `SponsorTransfer`

This transaction transfers a sponsor relationship for a particular ledger object's object reserve. The sponsor relationship can either be passed on to a new sponsor, or dissolved entirely (with the sponsee taking on the reserve). Either the sponsor or sponsee may submit this transaction at any point in time.

### 5.1. Fields

| Field Name        | Required? | JSON Type | Internal Type |
| ----------------- | --------- | --------- | ------------- |
| `TransactionType` | ✔️        | `string`  | `UInt16`      |
| `Account`         | ✔️        | `string`  | `AccountID`   |
| `LedgerIndex`     |           | `string`  | `UInt256`     |
| `Sponsor`         |           | `object`  | `STObject`    |

#### 5.1.1. `LedgerIndex`

This field should be included if this transaction is dealing with sponsored object, rather than on a sponsored account. This field indicates which object the relationship is changing for.

If it is not included, then it refers to the account sending the transaction.

#### 5.1.2. `Sponsor`

The `Sponsor` field is already added in the ledger common fields (see section [4.1.1](#411-sponsor)), but it has some additional rules associated with it on the `SponsorTransfer` transaction.

In this case, if `Sponsor` is included with the `tfSponsorReserve` flag, then the reserve sponsorship for the provided object will be transferred to the `Sponsor.Account` instead of passing back to the ledger object's owner.

If there is no `Sponsor` field, or if the `tfSponsorReserve` flag is not included, then the burden of the reserve will be passed back to the ledger object's owner (the former sponsee).

### 5.2. Ending the Sponsorship for a Sponsored Ledger Object

A sponsored ledger object will have the `Sponsor` field attached to it. Ending the sponsor relationship for a sponsored ledger object requires the `LedgerIndex` parameter, to specify which ledger object.

Two accounts are allowed to submit a `SponsorTransfer` relationship to end the sponsor relationship for a sponsored ledger object: either the sponsor for that object or the owner of that object (the sponsee).

### 5.3. Migrating a Sponsorship to a New Account

A sponsorship can be migrated to a new account by including the `Sponsor` field with the `tfSponsorReserve` flag. This can be done for either a sponsored account or a sponsored ledger object.

Two accounts are allowed to submit a `SponsorTransfer` relationship to migrate the sponsor relationship: the sponsor or the sponsee.

The sponsor will likely only rarely want to do this (such as if they are transferring accounts), but the sponsee may want to migrate if they change providers.

### 5.4. Failure Conditions

- If transferring the sponsorship, the new sponsor does not have enough reserve for this object/account.
- If dissolving the sponsorship, the owner does not have enough reserve for this object/account.
- The new sponsor does not exist.

### 5.5. State Changes

- The `Sponsor` field on the object is changed or deleted.
- The old sponsor has its `SponsoringOwnerCount`/`SponsoringAccountCount` decremented by one.
- The new sponsor (if applicable) has its `SponsoringOwnerCount`/`SponsoringAccountCount` incremented by one.
- If there is no new sponsor, then the owner's `SponsoredOwnerCount` will be decremented by one.

## 6. RPC: `account_objects`

### 6.1. Fields

The [`account_objects` RPC method](https://xrpl.org/account_objects.html) already exists on the XRPL. As a reference, here are the fields that `account_objects` currently accepts:

| Field Name               | Required? | JSON Type            |
| ------------------------ | --------- | -------------------- |
| `account`                | ✔️        | `string`             |
| `deletion_blockers_only` |           | `boolean`            |
| `ledger_hash`            |           | `string`             |
| `ledger_index`           |           | `number` or `string` |
| `limit`                  |           | `number`             |
| `marker`                 |           | `any`                |
| `type`                   |           | `string`             |

We propose this additional field:

| Field Name  | Required? | JSON Type |
| ----------- | --------- | --------- |
| `sponsored` |           | `boolean` |

### 6.2. `sponsored`

If this field is excluded, all objects, sponsored or not, will be included. If `sponsored == True`, only sponsored objects will be included. If `sponsored == False`, only non-sponsored objects will be included.

## 7. RPC: `account_sponsoring`

The `account_sponsoring` RPC method is used to fetch a list of objects that an account is sponsoring; namely, a list of objects where the `SponsorAccount` is the given account. It has a very similar API to the [`account_objects` method](https://xrpl.org/account_objects.html).

| Field Name               | Required? | JSON Type            | Description                                                                                                             |
| ------------------------ | --------- | -------------------- | ----------------------------------------------------------------------------------------------------------------------- |
| `account`                | ✔️        | `string`             | The sponsor in question.                                                                                                |
| `deletion_blockers_only` |           | `boolean`            | If `true`, the response only includes objects that would block this account from being deleted. The default is `false`. |
| `ledger_hash`            |           | `string`             | A hash representing the ledger version to use.                                                                          |
| `ledger_index`           |           | `number` or `string` | The ledger index of the ledger to use, or a shortcut string to choose a ledger automatically.                           |
| `limit`                  |           | `number`             | The maximum number of objects to include in the results.                                                                |
| `marker`                 |           | `any`                | Value from a previous paginated response. Resume retrieving data where that response left off.                          |
| `type`                   |           | `string`             | Filter results by a ledger entry type. Some examples are `offer` and `escrow`.                                          |

## 8. Security

### 8.1. Security Axioms

Both the sponsee _and_ the sponsor must agree to enter into a sponsor relationship. The sponsee must be okay with the sponsor handling the reserve, and the sponsor must be willing to take on that reserve. A signature from both parties ensures that this is the case.

A sponsor will never be stuck sponsoring an sponsee's account or object it doesn't want to support anymore, because it can submit a `SponsorTransfer` transaction at any point.

The sponsor's signature must _always_ include the `Account` and `Sequence` fields, to prevent signature replay attacks (where the sponsor's signature can be reused to sponsor an object or account that they did not want to sponsor).

When sponsoring transaction fees, the sponsor must approve of the `Fee` value of the transaction, since that is the amount that they will be paying.

When sponsoring reserves, the sponsor's signature must include any aspects of the transaction that involve a potential account/object reserve. This would include the `Destination` field of a `Payment` transaction (and whether it is a new account) and the `TicketSequence` field of a `TicketCreate` transaction (since that dictates how many `Ticket` objects are created, each of which results in one object reserve).

A sponsee cannot take advantage of the generosity of their sponsor, since the sponsor must sign every transaction it wants to sponsor the ledger objects for. A sponsee also must not be able to change the sponsorship type that the sponsor is willing to engage in, as this could lock up to 500 of the sponsor's XRP (in the case of 250 tickets being created in one `TicketCreate` transaction).

An axiom that is out of scope: the sponsee _will not_ have any control over a sponsorship transfer. This is akin to a loanee having no control over a bank selling their mortgage to some other company, or a lender selling debt to a debt collection agency.

### 8.2. Signatures

Since a fee sponsorship must approve of the `Fee` field, and a reserve sponsorship must approve of a broad set of transaction fields, the sponsor must always sign the whole transaction. This also avoids needing to have different sponsorship processes for different sponsorship types. This includes the non-signature parts of the `Sponsor` object (`Sponsor.Account` and `Sponsor.Flags`). The same is true for the sponsee's transaction signature; the sponsee must approve of the sponsor and sponsorship type.

A sponsor's `Signature` cannot be replayed or attached to a different transaction, since the whole transaction (including the `Account` and `Sequence` values) must be signed.

## 9. Invariants

An [invariant](https://xrpl.org/docs/concepts/consensus-protocol/invariant-checking/) is a statement, usually an equation, that must always be true for every valid ledger state on the XRPL. Invariant checks serve as a last line of defense against bugs; the `tecINVARIANT_FAILED` error is thrown if an invariant is violated (which ideally should never happen).

### 9.1. Tracking Owner Counts

A transaction that creates a ledger object either increments an account's `OwnerCount` by 1 or increments two separate accounts' `SponsoringOwnerCount` and `SponsoredOwnerCount` by 1. The opposite happens when a ledger object is deleted.

The equivalent also should happen with `SponsoringAccountCount`.

### 9.2. Balancing `SponsoredOwnerCount` and `SponsoringOwnerCount`

$$ \sum*{accounts} Account.SponsoredOwnerCount = \sum*{accounts} Account.SponsoringOwnerCount $$

In other words, the sum of all accounts' `SponsoredOwnerCount`s must be equal to the sum of all accounts' `SponsoringOwnerCount`s. This ensures that every sponsored object is logged as being sponsored and also has a sponsor.

## 10. Example Flows

Each example will show what the transaction will look like before **and** after both the sponsor and sponsee sign the transaction.

The unsigned transaction must be autofilled before it is passed to the sponsor to sign. Tooling can be updated to handle combining the sponsor and sponsee signatures, similar to helper functions that already exist for multisigning.

### 10.1. Fee Sponsorship

#### 10.1.1. The Unsigned Transaction

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

#### 10.1.2. The Signed Transaction

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
  }
},
SigningPubKey: "03A8D0093B0CD730F25E978BF414CA93084B3A2CBB290D5E0E312021ED2D2C1C8B", // rAccount's public key
TxnSignature: "3045022100F2AAF90D8F9BB6C94C0C95BA31E320FC601C7BAFFF536CC07076A2833CB4C7FF02203F3C76EB34ABAD61A71CEBD42307169CDA65D9B3CA0EEE871210BEAB824E524B"
```

</details>

### 10.2. Account Sponsorship

The only way an account can be created is via a `Payment` transaction. So the sponsor relationship must be initiated on the `Payment` transaction.

#### 10.2.1. The Unsigned Transaction

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

#### 10.2.2. The Signed Transaction

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

### 10.3. Object Sponsorship

#### 10.3.1. The Unsigned Transaction

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

#### 10.3.2. The Signed Transaction

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

<!--
## n+1. Remaining TODOs/Open Questions

* Do I need a new type of directory nodes to keep track of sponsored objects?
	* Clio could perhaps solve this problem
* How will this work for objects like trustlines, where multiple accounts might be holding reserves for it?
	* Maybe a second `Sponsor` field or something?
* Should just fees be supported in v1, and reserves added later? Reserves are where all the complexity comes in.
* Should the sponsor provide a max amount of reserves they're willing to support in the transaction, and if it's above that then the transaction fails?
	* Seems like this could be solved by the in-discussion `simulate` RPC
-->

# Appendix

## Appendix A: FAQ

### A.1: Does the sponsee receive any XRP for the reserve?

No, there is no XRP transfer in a sponsorship relationship - the XRP stays in the sponsor's account. The burden of the reserve for that object/account is just transferred to the sponsor.

### A.2: What happens if you try to delete your account and you have sponsored objects?

If the account itself is sponsored, then it can be deleted, but the destination of the `AccountDelete` transaction (in other words, where the leftover XRP goes) **must** be the sponsor's account. This ensures that the sponsor gets their reserve back, and the sponsee cannot run away with those funds.

If the sponsee still has sponsored objects, those objects will follow the same rules of [deletion blockers](https://xrpl.org/docs/concepts/accounts/deleting-accounts/#requirements). Whether or not they are sponsored is irrelevant.

If a sponsored object is deleted (either due to normal object deletion processes or, in the case of objects that aren't deletion blockers, because the owner account is deleted), the sponsor's reserve becomes available again.

### A.3: What if a sponsor that is sponsoring a few objects wants to delete their account?

An account cannot be deleted if it is sponsoring **any** existing accounts or objects. They will need to either delete those objects (by asking the owner to do so) or use the `SponsorTransfer` transaction to relinquish control of them.

### A.4: Does a sponsor have any powers over an object they pay the reserve for? I.e. can they delete the object?

No. If a sponsor no longer wants to support an object, they can always use the `SponsorTransfer` transaction instead.

<!--
* Should the reserve payer have powers over the object? maybe they're allowed to delete it? or do they just accept that their XRP is held up until the owner deals with it?
	* They could just run a `SponsorTransfer` transaction in that case
	* The [Stellar spec](https://developers.stellar.org/docs/encyclopedia/sponsored-reserves#revoke-sponsorship) doesn't allow any additional powers over the object
-->

### A.5: What if a sponsee refuses to delete their account when a sponsor wants to stop supporting their account?

The sponsor will have the standard problem of trying to get ahold of a debtor to make them pay. They may be able to use `SponsorTransfer` transaction to put the onus on the sponsee, though the sponsee would need to have enough XRP in their account to cover the reserve.

### A.6: What happens if the sponsor tries to `SponsorTransfer` but the sponsee doesn't have enough funds to cover the reserve?

If the sponsor really needs to get out of the sponsor relationship ASAP without recouping the value of the reserve, they can pay the sponsee the amount of XRP they need to cover the reserve. These steps can be executed atomically via a [Batch transaction](https://github.com/XRPLF/XRPL-Standards/discussions/162), to ensure that the sponsee can't do something else with the funds before the `SponsorTransfer` transaction is validated.

### A.7: Would sponsored accounts carry a lower reserve?

No, they would still carry a reserve of 10 XRP at current levels.

### A.8: Can an existing unsponsored ledger object/account be sponsored?

Yes, with the `SponsorTransfer` transaction.

### A.9: Can a sponsored account be a sponsor for other accounts/objects?

No.

### A.10: Can a sponsored account hold unsponsored objects, or objects sponsored by a different sponsor?

Yes, and yes.

### A.11: What if I want different sponsors to sponsor the transaction fee vs. the reserve for the same transaction?

That will not be supported by this proposal. If you have a need for this, please provide example use-cases.

### A.12: Won't it be difficult to add two signatures to a transaction?

This is something that good tooling can solve. It could work similarly to how multisigning is supported in various tools.

### A.13. Why not instead do [insert some other design]?

See Appendix B for the alternate designs that were considered and why this one was preferred. If you have another one in mind, please describe it in the comments and we can discuss.

### A.14: How is this account sponsorship model different from/better than [XLS-23d, Lite Accounts](https://github.com/XRPLF/XRPL-Standards/discussions/56)?

- Sponsored accounts do not have any restrictions, and can hold objects.
- Sponsored accounts require the same reserve as a normal account (this was one of the objections to the Lite Account proposal).
- Lite accounts can be deleted by their sponsor.

### A.15: How will this work for objects like trustlines, where multiple accounts might be holding reserves for it?

The answer to this question is still being explored. One possible solution is to add a second field, `Sponsor2`, to handle the other reserve.

### A.16: How does this proposal work in conjunction with [XLS-49d](https://github.com/XRPLF/XRPL-Standards/discussions/144)? What signer list(s) have the power to sponsor fees or reserves?

Currently, only the global signer list is supported. Another `SignerListID` value could be added to support sponsorship. Transaction values can only go up to $2^{16}$, since the `TransactionType` field is a `UInt16`, but the `SignerListID` field goes up to $2^{32}$, so there is room in the design for additional values that do not correlate to a specific transaction type.

## Appendix B: Alternate Designs

### B.1: Add a `Sponsor` to the account

This design involved updating `AccountSet` to allow users to add a `Sponsor` to their account (with a signature from the sponsor as well). The sponsor would then sponsor every object from that account while the field was active, and either the sponsor or the account could remove the sponsorship at any time.

This was a previous version of the spec, but it made more sense for the relationship to be specific to a transaction/transactions, to prevent abuse (the sponsor should decide what objects they want to support and what objects they don't want to support).

The current design also supports having different sponsors for different objects, which allows users to use a broad set of services and platforms, instead of being locked into one.

<!--Stellar uses this philosophy ("the relationship should be ephemeral to prevent abuse") for their sponsored reserves design, which I like.-->

### B.2: A Wrapper Transaction

There would be a wrapper transaction (tentatively named `Relay`), similar to `Batch` in [XLS-56d](https://github.com/XRPLF/XRPL-Standards/discussions/162), that the sponsor would sign. It would contain a sub-transaction from the sponsee.

It would look something like this:
|FieldName | Required? | JSON Type | Internal Type |
|:---------|:-----------|:---------------|:------------|
|`TransactionType`|✔️|`string`|`UInt16`|
|`Account`|✔️|`string`|`STAccount`|
|`Fee`|✔️|`string`|`STAmount`|
|`Transaction`|✔️|`object`|`STTx`|

This was a part of a previous version of the spec (inspired by Stellar's [sandwich transaction design](https://developers.stellar.org/docs/learn/encyclopedia/sponsored-reserves#begin-and-end-sponsorships) for their implementation of sponsored reserves), but the existing design felt cleaner. From an implementation perspective, it's easier to have the fee payer as a part of the existing transaction rather than as a part of a wrapper transaction, since that info needs to somehow get passed down the stack. Also, while the wrapper transaction paradigm will be used in XLS-56d, they should be used sparingly in designs - only when necessary - as their flow is rather complicated in the `rippled` code.

In addition, the signing process becomes complicated (as discovered in the process of developing XLS-56d). You have to somehow prevent the sponsor from submitting the as-is signed transaction to the network, without including it in the wrapper transaction.

### B.3: A Create-Accept-Cancel Flow

The rough idea of this design was to have a new set of transactions (e.g. `SponsorCreate`/`SponsorAccept`/`SponsorCancel`/`SponsorFinish`) where a sponsor could take on the reserve for an existing object.

This design was never seriously considered, as it felt too complicated and introduced several new transactions. It also doesn't support adding a sponsor to the object at object creation time, which is a much smoother UX and never requires the owner/sponsee to hold enough XRP for the reserve.
