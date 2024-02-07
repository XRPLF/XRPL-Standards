<pre>
Title:       <b>Multi-Purpose Tokens (MPTs)</b>
Type:        <b>draft</b>

Author:  
             <a href="mailto:fuelling@ripple.com">David Fuelling</a>
             <a href="mailto:nikb@bougalis.net">Nikolaos Bougalis</a>
             <a href="mailto:gweisbrod@ripple.com">Greg Weisbrod</a>
Affiliation: <a href="https://ripple.com">Ripple</a>
</pre>

# 1. Multi-Purpose Tokens (MPTs)

## 1.1. Abstract

[Trust lines](https://xrpl.org/trust-lines-and-issuing.html#trust-lines-and-issuing) are a fundamental building block for many XRP Ledger tokenization features, including [CBDCs](https://en.wikipedia.org/wiki/Central_bank_digital_currency) and [fiat-collateralized stablecoins](https://www.investopedia.com/terms/s/stablecoin.asp). However, as more and more token issuers embrace the XRP Ledger, the current size of each trust line will become an impediment to ledger stability and scalability.

This proposal introduces extensions to the XRP Ledger to support a more multi-purpose token (i.e., MPT) type, along with operations to enumerate, purchase, sell and hold such tokens. 

Unlike trust lines, MPTs do not represent bidirectional debt relationships. Instead, MPTs function more like a unidirectional trust line with only one balance, making it simpler to support common tokenization requirements, including even non-monetery use cases such as tracking reputation points in an online game. 

Perhaps as important, however, MPTs require significantly less space than trust lines: ~52 bytes for each MPT held by a token holder, as compared to _at least_ 234 bytes for every new trust line (see Appendix 1 for a more detailed comparison).

### 1.1.1. Advantages and Disadvantages

**Advantages**

* Uses a fixed-point balance representation instead of a floating-point representation, yielding the following benefits:
  * MPT balance amounts can easily be added to other ledger objects like escrows, checks, payment channels, and AMMs.
  * Enables reliable and easy enforcement of invariant checks and straightforward tracking of fees.
  * Eliminates edge case floating-point math involving very small amounts violating expected equality conditions (e.g., MPTs will never have to deal with cases where `A+B=A` for non-zero `B` or `(A+B)+C != A+(B+C)`). 
* Simpler conceptual model (trust lines and rippling make it harder for developers to reason about the system, which increases the risk of errors or value loss).
* Reduces trust line storage requirements which allows more accounts to hold more tokens, for less cost.
* Reduces long-term infrastructure and storage burdens on node operators, increasing network resiliency.
* Improves node performance when processing large volumes of MPT transactions.

**Disadvantages**

* MPTs would introduce a third asset type on the ledger after XRP and IOUs, which complicates the Payment Engine implementation.
* New transaction and data types require new implementation code from client libraries and wallets to read, display, and transact.
* MPTs will represent a smaller overall balance amount as compared to trust lines (Trustlines can represent an enormous range, roughly between 10^-96 to 10^80). 

### 1.1.2. Assumptions
This proposal makes a variety of assumptions, based upon observations of existing trust line usage in order to produce the most compact representations of data. These assumptions include:

1. **Only Unidirectional**. This proposal does not support bidirectional trust line constructions, on the assumption that _most_ token issuers leave their trust line limit set to the default value of 0 (i.e., issuers don't allow debt relationships with token holders, by default). Thus, MPTs do not have the same "balance netting" functionality found in trust lines because MPTs have only a single balance as opposed to the two balances used by trust lines.
2. **Few Issuances per Issuer**. The most common examples of fungible token issuance involve regulatory overhead, which makes it less common for issuers to issue _many_ fungible tokens, in the general case. In addition, existing [guidance on xrpl.org](https://xrpl.org/freezes.html#global-freeze) advises token issuers to use different addresses for each token issuance in order to better accomodate [global freeze](https://xrpl.org/enact-global-freeze.html) activities. Because of this, we assume that any individual issuer will not issue many different fungible tokens using the same address. In particular, this specification limits the number of unique MPT issuances to 32 per issuing account. If an issuer wishes to support more than this number of MPTs, additional addresses can still be used.
3. **No Trust Limits**. Unlike current Trustline functionality where trust amount limits can be set by either party, this proposal eliminates this feature under the assumption that token holders will not acquire a MPT without first making an off-ledger trust decision. For example, a common use-case for a MPT is a fiat-backed stablecoin, where a token holder wouldn't purchase more stablecoin than they would feel comfortable holding.
4. **No Rippling**. Unlike some existing capabilities of the ledger, MPTs are not eligible for [rippling](https://xrpl.org/rippling.html#rippling), and thus do not have any configurability settings related to that functionality.

### 1.1.3 Release Timeline and Scope

XLS-33 will only cover the addition of the new data structures for MPTs, integration with the **`Payment`** transaction such that users can make MPT to MPT payments (IE no cross currency payments), and several other incidental additions like new requirements for account deletion (discussed below). Later amendments will integrate MPTs with other features of the XRPL such as the DEX.

## 1.2. Creating Multi-Purpose Tokens

### 1.2.1. On-Ledger Data Structures

We propose two new objects and one new ledger structure:

1. A **`MPTokenIssuance`** is a new object that describes a fungible token issuance created by an issuer.
1. A **`MPToken`** is a new object that describes a single account's holdings of an issued token.

#### 1.2.1.1. The **`MPTokenIssuance`** object

The **`MPTokenIssuance`** object represents a single MPT issuance and holds data associated with the issuance itself. Token issuances are created using the **`MPTokenIssuanceCreate`** transaction and can, optionally, be destroyed by the **`MPTokenIssuanceDestroy`** transaction.

##### 1.2.1.1.1. **`MPTokenIssuance`** Ledger Identifier

The key of a `MPTokenIssuance` object, is the result of SHA512-Half of the following values, concatenated in order:

* The MPTokenIssuance space key (0x007E).
* The transaction sequence number.
* The AccountID of the issuer.


The ID of a `MPTokenIssuance` object, a.k.a. `MPTokenIssuanceID`, is a 192-bit integer, concatenated in order:

* The transaction sequence number.
* The AccountID of the issuer.

```
┌──────────────────────────┐┌──────────────────────────┐
│                          ││                          │
│      Sequence            ││     Issuer AccountID     │
│      (32 bits)           ││        (160 bits)        │
│                          ││                          │
└──────────────────────────┘└──────────────────────────┘
```

**Note: The `MPTokenIssuanceID` is utilized to specify a unique `MPTokenIssuance` object in JSON parameters for transactions and APIs. Internally, the ledger splits the `MPTokenIssuanceID` into two components: `sequence` and `issuer` address.**

##### 1.2.1.1.2. Fields

**`MPTokenIssuance`** objects are stored in the ledger and tracked in an [Owner Directory](https://xrpl.org/directorynode.html) owned by the issuer. Issuances have the following required and optional fields:

| Field Name          | Required?           | JSON Type | Internal Type |
|---------------------|---------------------|-----------|---------------|
| `LedgerEntryType`   | :heavy_check_mark:  | `number`  | `UINT16`      |
| `Flags`             | :heavy_check_mark:  | `number`  | `UINT32`      |
| `Issuer`            | :heavy_check_mark:  | `string`  | `ACCOUNTID`   |
| `AssetScale`        | (default)           | `number`  | `UINT8`       |
| `MaximumAmount`     | :heavy_check_mark:  | `string`  | `UINT64`      |
| `OutstandingAmount` | :heavy_check_mark:  | `string`  | `UINT64`      |
| `LockedAmount`      | ️(default)          | `string`  | `UINT64`      |
| `TransferFee`       | ️(default)          | `number`  | `UINT16`      |
| `MPTokenMetadata`   |                     | `string`  | `BLOB`        |
| `PreviousTxnID`     | :heavy_check_mark:  | `string`  | `HASH256`     |
| `PreviousTxnLgrSeq` | ️:heavy_check_mark: | `number`  | `UINT32`      |
| `OwnerNode`         | (default)           | `number`  | `UINT64`      |
| `Sequence`          | :heavy_check_mark:  | `number`  | `UINT32`      |

###### 1.2.1.1.2.1. `LedgerEntryType`

The value 0x007E, mapped to the string `MPTokenIssuance`, indicates that this object describes a Multi-Purpose Token (MPT).

###### 1.2.1.1.2.2. `Flags`

A set of flags indicating properties or other options associated with this **`MPTokenIssuance`** object. The type specific flags proposed  are:

| Flag Name           | Flag Value | Description                                                                                                                                                                                                                               |
|---------------------|------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `lsfMPTLocked`      | ️`0x0001`  | If set, indicates that all balances are locked.                                                                                                                                                                                           |
| `lsfMPTCanLock`     | ️`0x0002`  | If set, indicates that the issuer can lock an individual balance or all balances of this MPT.  If not set, the MPT cannot be locked in any way.                                                                                           |
| `lsfMPTRequireAuth` | ️`0x0004`  | If set, indicates that _individual_ holders must be authorized. This enables issuers to limit who can hold their assets.                                                                                                                  |
| `lsfMPTCanEscrow`   | `0x0008`   | If set, indicates that _individual_ holders can place their balances into an escrow.                                                                                                                                                      |
| `lsfMPTCanTrade`    | `0x0010`   | If set, indicates that _individual_ holders can trade their balances using the XRP Ledger DEX or AMM.                                                                                                                                     |
| `lsfMPTCanTransfer` | ️`0x0020`  | If set, indicates that tokens held by non-issuers may be transferred to other accounts. If not set, indicates that tokens held by non-issuers may not be transferred except back to the issuer; this enables use-cases like store credit. |
| `lsfMPTCanClawback` | ️`0x0040`  | If set, indicates that the issuer may use the `Clawback` transaction to clawback value from _individual_ holders.                                                                                                                         |

Except for `lsfMPTLocked`, which can be mutated via the `**MPTokenIssuanceSet**` transactions, these flags are **immutable**: they can only be set during the **`MPTokenIssuanceCreate`** transaction and cannot be changed later.

###### 1.2.1.1.2.3. `Issuer`

The address of the account that controls both the issuance amounts and characteristics of a particular fungible token.

###### 1.2.1.1.2.4. `AssetScale`

An asset scale is the difference, in orders of magnitude, between a standard unit and a corresponding fractional unit. More formally, the asset scale is a non-negative integer (0, 1, 2, …) such that one standard unit equals 10^(-scale) of a corresponding fractional unit. If the fractional unit equals the standard unit, then the asset scale is 0.

###### 1.2.1.1.2.5. `MaximumAmount`

This value is an unsigned number that specifies the maximum number of MPTs that can be distributed to non-issuing accounts (i.e., `minted`). For issuances that do not have a maximum limit, this value should be set to 0xFFFFFFFFFFFFFFFF.

###### 1.2.1.1.2.6. `OutstandingAmount`

Specifies the sum of all token amounts that have been minted to all token holders. This value can be stored on ledger as a `default` type so that when its value is 0, it takes up less space on ledger. This value is increased whenever an issuer pays MPTs to a non-issuer account, and decreased whenever a non-issuer pays MPTs into the issuing account.

###### 1.2.1.1.2.7. `TransferFee`

This value specifies the fee, in tenths of a [basis point](https://en.wikipedia.org/wiki/Basis_point), charged by the issuer for secondary sales of the token, if such sales are allowed at all. Valid values for this field are between 0 and 50,000 inclusive. A value of 1 is equivalent to 1/10 of a basis point or 0.001%, allowing transfer rates between 0% and 50%. A `TransferFee` of 50,000 corresponds to 50%. The default value for this field is 0. Any decimals in the transfer fee will be rounded down, hence the fee can be rounded down to zero if the payment is small. Issuer should make sure that their MPT's `AssetScale` is large enough.

###### 1.2.1.1.2.8. `PreviousTxnID`

Identifies the transaction ID of the transaction that most recently modified this object.

###### 1.2.1.1.2.9. `PreviousTxnLgrSeq`

The sequence of the ledger that contains the transaction that most recently modified this object.

###### 1.2.1.1.2.10. `OwnerNode`

Identifies the page in the owner's directory where this item is referenced.

###### 1.2.1.1.2.11. `Sequence`

A 32-bit unsigned integer that is used to ensure issuances from a given sender may only ever exist once, even if an issuance is later deleted. Whenever a new issuance is created, this value must match the account's current Sequence number.

[Tickets](https://xrpl.org/tickets.html) make some exceptions from these rules so that it is possible to send transactions out of the normal order. Tickets represent sequence numbers reserved for later use; a transaction can use a Ticket instead of a normal account Sequence number.

Whenever a transaction to create an MPT is included in a ledger, it uses up a sequence number (or Ticket) regardless of whether the transaction executed successfully or failed with a [tec-class error code](https://xrpl.org/tec-codes.html). Other transaction failures don't get included in ledgers, so they don't change the sender's sequence number (or have any other effects).

It is possible for multiple unconfirmed MPT-creation transactions to have the same `Issuer` and sequence number. Such transactions are mutually exclusive, and at most one of them can be included in a validated ledger. (Any others ultimately have no effect.)

##### 1.2.1.1.3. Example **`MPTokenIssuance`** JSON

 ```json
 {
     "LedgerEntryType": "MPTokenIssuance",
     "Flags": 131072,
     "Issuer": "rsA2LpzuawewSBQXkiju3YQTMzW13pAAdW",
     "AssetScale": "2",
     "MaximumAmount": "100000000",
     "OutstandingAmount": "5",
     "TransferFee": 50000,     
     "MPTokenMetadata": "",
     "OwnerNode": "74"
 }
 ```

##### 1.2.1.1.4. How do **`MPTokenIssuance`** objects work?

Any account may issue any number of Multi-Purpose Tokens.

###### 1.2.1.1.4.1. Searching for a **`MPTokenIssuance`** object

MPTokenIssuance objects are uniquely identified by a combination of a type-specific prefix, the issuer address and a transaction sequence number. To locate a specific **`MPTokenIssuance`**, the first step is to locate the owner directory for the issuer. Then, find the directory that holds `MPTokenIssuance` ledger objects and iterate through each entry to find the instance with the desired key. If that entry does not exist then the **`MPTokenIssuance`** does not exist for the given account.

###### 1.2.1.1.4.2. Adding a **`MPTokenIssuance`** object

A **`MPTokenIssuance`** object can be added by using the same approach to find the **`MPTokenIssuance`**, and adding it to that directory. If, after addition, the number of MPTs in the directory would exceed 32, then the operation must fail.

###### 1.2.1.1.4.3. Removing a **`MPTokenIssuance`** object

An **`MPTokenIssuance`** can be removed by locating the issuance using the approach in [Searching for an MPTokenIssuance](#121141-searching-for-a-mptokenissuance-object). If found, the object can be deleted, but only if the **`OutstandingAmount`** is equal to 0.

###### 1.2.1.1.4.4. Reserve for **`MPTokenIssuance`** object

Each **`MPTokenIssuance`** costs an incremental reserve to the owner account.

#### 1.2.1.2. The **`MPToken`** object

The **`MPToken`** object represents an amount of a token held by an account that is **not** the token issuer. MPTs are acquired via ordinary Payment or DEX transactions, and can optionally be redeemed or exchanged using these same types of transactions. The object key of the `MPToken` is derived from hashing the space key, holder's address and the `MPTokenIssuanceID`.

##### 1.2.1.2.1. **`MPToken`** Ledger Identifier

The ID of a MPToken object, a.k.a `MPTokenID` is the result of SHA512-Half of the following values, concatenated in order:

* The MPToken space key (0x0074).
* The `MPTokenIssuanceID` for the issuance being held.
* The AccountID of the token holder. 

##### 1.2.1.2.2. Fields

A **`MPToken`** object can have the following fields. The key of each MPToken is stored in the Owner Directory for the account that holds the `MPToken`.

| Field Name          | Required?          | JSON Type | Internal Type |
|---------------------|--------------------|-----------|---------------|
| `LedgerEntryType`   | :heavy_check_mark: | `number`  | `UINT16`      |
| `Account`           | :heavy_check_mark: | `string`  | `ACCOUNTID`   |
| `MPTokenIssuanceID` | :heavy_check_mark: | `string`  | `UINT192`     |
| `MPTAmount`         | :heavy_check_mark: | `string`  | `UINT64`      |
| `LockedAmount`      | default            | `string`  | `UINT64`      |
| `Flags`             | default            | `number`  | `UINT32`      |
| `PreviousTxnID`     | :heavy_check_mark: | `string`  | `HASH256`     |
| `PreviousTxnLgrSeq` | :heavy_check_mark: | `number`  | `UINT32`      |
| `OwnerNode`         | default            | `number`  | `UINT64`      |
| `MPTokenNode`       | default            | `number`  | `UINT64`      |

###### 1.2.1.2.2.1. `LedgerEntryType`

The value 0x007F, mapped to the string `MPToken`, indicates that this object describes an individual account's holding of a MPT.

###### 1.2.1.2.2.2. `Account`

The owner of the `MPToken`.

###### 1.2.1.2.2.3. `MPTokenIssuanceID`

The `MPTokenIssuance` identifier.

###### 1.2.1.2.2.4. `MPTAmount`

This value specifies a positive amount of tokens currently held by the owner. Valid values for this field are between 0x0 and 0xFFFFFFFFFFFFFFFF.

###### 1.2.1.2.2.5. `LockedAmount`

This value specifies a positive amount of tokens that are currently held in a token holder's account but that are unavailable to be used by the token holder. Locked tokens might, for example, represent value currently being held in escrow, or value that is otherwise inaccessible to the token holder. 

This value is stored as a `default` value such that it's initial value is `0`, in order to save space on the ledger for a an empty MPT holding.

###### 1.2.1.2.2.6. `Flags`

A set of flags indicating properties or other options associated with this **`MPTokenIssuance`** object. The type specific flags proposed  are:

| Flag Name          | Flag Value | Description                                                                                                                                                                                                                                                                      |
|--------------------|------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `lsfMPTLocked`     | `0x0001`   | If set, indicates that the MPT owned by this account is currently locked and cannot be used in any XRP transactions other than sending value back to the issuer. When this flag is set, the `LockedAmount` must equal the `MPTAmount` value.                                     |
| `lsfMPTAuthorized` | `0x0002`   | (Only applicable for allow-listing) If set, indicates that the issuer has authorized the holder for the MPT. This flag can be set using a `MPTokenAuthorize` transaction; it can also be "un-set" using a `MPTokenAuthorize` transaction specifying the `tfMPTUnauthorize` flag. |

###### 1.2.1.2.2.7. `PreviousTxnID`

Identifies the transaction ID of the transaction that most recently modified this object.

###### 1.2.1.2.2.8. `PreviousTxnLgrSeq`

The sequence of the ledger that contains the transaction that most recently modified this object.

###### 1.2.1.2.2.9. `OwnerNode`

Identifies the page in the owner's directory where this item is referenced.

###### 1.2.1.2.2.10. `MPTokenNode`

The MPT directory has exactly the same structure as an [Owner Directory](https://xrpl.org/directorynode.html), except this is a new type of directory that only indexes `MPTokens` for a single `MPTokenIssuance`. Ownership of this directory is still up for debate per [MPTokenNode Directories](#223-mptokennode-directories).

##### 1.2.1.2.3. Example MPToken JSON

 ```json
 {
     "LedgerEntryType": "MPToken",
     "Account": "rajgkBmMxmz161r8bWYH7CQAFZP5bA9oSG",
     "MPTokenIssuanceID": "000004C463C52827307480341125DA0577DEFC38405B0E3E",
     "Flags": 0,
     "MPTAmount": "100000000",
     "LockedAmount": "0",
     "OwnerNode": 1,
     "MPTokenNode": 1
 }
 ```

##### 1.2.1.2.4. Reserve for **`MPToken`** object

Each **`MPToken`** costs an incremental reserve to the owner account.

## 1.3 Transactions

This proposal introduces several new transactions to allow for the creation and deletion of MPT issuances. Likewise, this proposal introduce several new transactions for minting and redeeming discrete instances of MPTs. All transactions introduced by this proposal incorporate the [common transaction fields](https://xrpl.org/transaction-common-fields.html) that are shared by all transactions. Common fields are not documented in this proposal unless needed because this proposal introduces new possible values for such fields.

### 1.3.1 Transactions for Creating and Destroying Multi-Purpose Token Issuances on XRPL
We define three transactions related to MPT Issuances: **`MPTokenIssuanceCreate`** and **`MPTokenIssuanceDestroy`** and  **`MPTokenIssuanceSet`** for minting, destroying, and updating MPT _Issuances_ respectively on XRPL.

#### 1.3.1.1 The **`MPTokenIssuanceCreate`** transaction

The **`MPTokenIssuanceCreate`** transaction creates a **`MPTokenIssuance`** object and adds it to the relevant directory node of the creator account. This transaction is the only opportunity an `issuer` has to specify any token fields that are defined as immutable (e.g., MPT Flags).

If the transaction is successful, the newly created token will be owned by the account (the creator account) which executed the transaction.

##### 1.3.1.1.1 Transaction-specific Fields
| Field Name         | Required? | JSON Type | Internal Type |
| ------------------ | --------- | --------- |---------------|
| `TransactionType`  | ️ ✔        | `object`  | `UINT16`      |

Indicates the new transaction type **`MPTokenIssuanceCreate`**. The integer value is `25 (TODO)`.

| Field Name         | Required?    | JSON Type | Internal Type |
| ------------------ | ------------ | --------- |---------------|
| `AssetScale`       | ️           | `number`  | `UINT8`       |

An asset scale is the difference, in orders of magnitude, between a standard unit and a corresponding fractional unit. More formally, the asset scale is a non-negative integer (0, 1, 2, …) such that one standard unit equals 10^(-scale) of a corresponding fractional unit. If the fractional unit equals the standard unit, then the asset scale is 0. Note that this value is optional, and will default to `0` if not supplied.

| Field Name  | Required? | JSON Type | Internal Type |
| ----------- | --------- | --------- |---------------|
| `Flags`     | ️          | `number`  | `UINT16`      |

Specifies the flags for this transaction. In addition to the universal transaction flags that are applicable to all transactions (e.g., `tfFullyCanonicalSig`), the following transaction-specific flags are defined and used to set the appropriate fields in the Fungible Token:

| Flag Name         | Flag Value | Description |
|-------------------|------------|-------------|
| `tfMPTLocked`                | ️`0x0001`  | If set, indicates that all balances should be locked. This is a global lock that locks up all of holders' funds for this MPToken.|
| `tfMPTCanLock`  | ️`0x0002`  | If set, indicates that the MPT can be locked both individually and globally. If not set, the MPT cannot be locked in any way.|
| `tfMPTRequireAuth` | ️`0x0004`  | If set, indicates that _individual_ holders must be authorized. This enables issuers to limit who can hold their assets.  |
| `tfMPTCanEscrow`             | `0x0008`  | If set, indicates that _individual_ holders can place their balances into an escrow. |
| `tfMPTCanTrade`              | `0x0010`  | If set, indicates that _individual_ holders can trade their balances using the XRP Ledger DEX. |
| `tfMPTCanTransfer`          | ️`0x0020`  | If set, indicates that tokens may be transferred to other accounts that are not the issuer. |
| `tfMPTCanClawback`          | ️`0x0040`  | If set, indicates that the issuer may use the `Clawback` transaction to clawback value from _individual_ holders.|

| Field Name    | Required? | JSON Type | Internal Type |
| ------------- | --------- | --------- | ------------- |
| `TransferFee` |           | `number`  | `UINT16`      | 

The value specifies the fee to charged by the issuer for secondary sales of the Token, if such sales are allowed. Valid values for this field are between 0 and 50,000 inclusive, allowing transfer rates of between 0.000% and 50.000% in increments of 0.001.

The field MUST NOT be present if the `tfMPTCanTransfer` flag is not set. If it is, the transaction should fail and a fee should be claimed.

| Field Name      | Required?          | JSON Type | Internal Type |
| --------------- | ------------------ | --------- | ------------- |
| `MaximumAmount` |  | `string`  | `UINT64`      | 

The maximum asset amount of this token that should ever be issued.

| Field Name        | Required?          | JSON Type | Internal Type |
| ------------------| ------------------ | --------- | ------------- |
| `MPTokenMetadata` |  | `string`  | `BLOB`        | 

Arbitrary metadata about this issuance, in hex format. The limit for this field is 1024 bytes.

##### 1.3.1.1.2 Example **`MPTokenIssuanceCreate`** transaction

```json
{
  "TransactionType": "MPTokenIssuanceCreate",
  "Account": "rajgkBmMxmz161r8bWYH7CQAFZP5bA9oSG",
  "AssetScale": "2",
  "TransferFee": 314,
  "MaxAmount": "50000000",
  "Flags": 83659,
  "MPTokenMetadata": "FOO",
  "Fee": 10
}
```

This transaction assumes that the issuer of the token is the signer of the transaction.

### 1.3.2 The **`MPTokenIssuanceDestroy`** transaction

The **`MPTokenIssuanceDestroy`** transaction is used to remove an **`MPTokenIssuance`** object from the directory node in which it is being held, effectively removing the token from the ledger ("destroying" it).

If this operation succeeds, the corresponding **`MPTokenIssuance`** is removed and the owner’s reserve requirement is reduced by one. This operation must fail if there are any holders of the MPT in question.

#### 1.3.2.1 Transaction-specific Fields

| Field Name        | Required? | JSON Type | Internal Type |
| ----------        | --------- | --------- | ------------- |
| `TransactionType` |  ✔️        | `string`  | `UINT16`      | 

Indicates the new transaction type **`MPTokenIssuanceDestroy`**. The integer value is `26` (TODO).

| Field Name  | Required? | JSON Type | Internal Type |
| ----------- | --------- | --------- | ------------- |
| `MPTokenIssuanceID` |  ✔️        | `string`  | `UINT192`     | 

Identifies the **`MPTokenIssuance`** object to be removed by the transaction.

#### 1.3.2.2 Example **`MPTokenIssuanceDestroy`** JSON

 ```json
 {
       "TransactionType": "MPTokenIssuanceDestroy",
       "Fee": 10,
       "MPTokenIssuanceID": "000004C463C52827307480341125DA0577DEFC38405B0E3E"
 }
 ```
 
### 1.3.3 The **`MPTokenIssuanceSet`** Transaction

#### 1.3.3.1 MPTokenIssuanceSet
| Field Name         | Required? | JSON Type | Internal Type |
| ------------------ | --------- | --------- |---------------|
| `TransactionType`  | ️ ✔        | `object`  | `UINT16`      |

Indicates the new transaction type **`MPTokenIssuanceSet`**. The integer value is `28 (TODO)`.

| Field Name  | Required? | JSON Type | Internal Type |
| ----------- | --------- | --------- | ------------- |
| `MPTokenIssuanceID` |  ✔️  | `string`  | `UINT192`     | 

The `MPTokenIssuance` identifier.

| Field Name      | Required?          | JSON Type | Internal Type |
| --------------- | ------------------ | --------- | ------------- |
| `MPTokenHolder`       | | `string`  | `ACCOUNTID`   | 

An optional XRPL Address of an individual token holder balance to lock/unlock. If omitted, this transaction will apply to all any accounts holding MPTs.

| Field Name      | Required?          | JSON Type | Internal Type |
| --------------- | ------------------ | --------- | ------------- |
| `Flag`          | :heavy_check_mark: | `string`  | `UINT64`      | 

#### 1.3.3.2 Example **`MPTokenIssuanceSet`** JSON

 ```json
 {
       "TransactionType": "MPTokenIssuanceSet",
       "Fee": 10,
       "MPTokenIssuanceID": "000004C463C52827307480341125DA0577DEFC38405B0E3E",
       "Flags": 1
 }
 ```
 
#### 1.3.3.1.1 MPTokenIssuanceSet Flags
Transactions of the `MPTokenLock` type support additional values in the Flags field, as follows:

| Flag Name         | Flag Value | Description |
|-------------------|------------|-------------|
| `tfMPTLock`     | ️`0x0001`  | If set, indicates that all MPT balances for this asset should be locked. |
| `tfMPTUnlock`   | ️`0x0002`  | If set, indicates that all MPT balances for this asset should be unlocked. |

### 1.3.4 The **`Payment`** Transaction
The existing `Payment` transaction will not have any new top-level fields or flags added. However, we will extend the existing `amount` field to accommodate MPT amounts.

#### 1.3.4.1 The `amount` field
Currently, the amount field takes one of two forms. The below indicates an amount of 1 drop of XRP::

```json
"amount": "1"
```

The below indicates an amount of USD $1 issued by the indicated amount::

```json
"amount": {
  "issuer": "rf1BiGeXwwQoi8Z2ueFYTEXSwuJYfV2Jpn",
  "currency": "USD",
  "value": "1"
}
```

We propose using the following format for MPT amounts::

```json
"amount": {
  "mpt_issuance_id": "0000012FFD9EE5DA93AC614B4DB94D7E0FCE415CA51BED47",
  "value": "1"
}
```

Note: The `MPTokenIssuanceID` will be used to uniquely identify the MPT during a Payment transaction.

### 1.3.5 The **`MPTokenAuthorize`** Transaction

This transaction enables an account to hold an amount of a particular MPT issuance. When applied successfully, it will create a new `MPToken` object with an initial zero balance, owned by the holder account.

If the issuer has set `lsfMPTRequireAuth` (allow-listing) on the `MPTokenIssuance`, then the issuer must submit a `MPTokenAuthorize` transaction as well in order to give permission to the holder. If `lsfMPTRequireAuth` is not set and the issuer attempts to submit this transaction, it will fail.

#### 1.3.5.1 MPTokenAuthorize

| Field Name      | Required?          | JSON Type | Internal Type |
| --------------- | ------------------ | --------- | ------------- |
| `Account`       | :heavy_check_mark: | `string`  | `ACCOUNTID`   | 

This address can indicate either an issuer or a potential holder of a MPT.

| Field Name         | Required? | JSON Type | Internal Type |
| ------------------ | --------- | --------- |---------------|
| `TransactionType`  | ️ ✔        | `object`  | `UINT16`      |

Indicates the new transaction type **`MPTokenAuthorize`**. The integer value is `29 (TODO)`.

| Field Name  | Required? | JSON Type | Internal Type |
| ----------- | --------- | --------- | ------------- |
| `MPTokenIssuanceID` |  ✔️  | `string`  | `UINT192`     | 

Indicates the ID of the MPT involved. 

| Field Name  | Required? | JSON Type | Internal Type |
| ----------- | --------- | --------- | ------------- |
| `MPTokenHolder` |    | `string`  | `ACCOUNTID`     | 

Specifies the holders address that the issuer wants to authorize. Only used for authorization/allow-listing; must be empty if submitted by the holder.

| Field Name      | Required?          | JSON Type | Internal Type |
| --------------- | ------------------ | --------- | ------------- |
| `Flag`          | :heavy_check_mark: | `string`  | `UINT64`      | 

 
#### 1.3.3.5.12 MPTokenAuthorize Flags

Transactions of the `MPTokenAuthorize` type support additional values in the Flags field, as follows:

| Flag Name         | Flag Value | Description |
|-------------------|------------|-------------|
| `tfMPTUnauthorize`     | ️`0x0001`  | If set and transaction is submitted by a holder, it indicates that the holder no longer wants to hold the `MPToken`, which will be deleted as a result. If the the holder's `MPToken` has non-zero balance while trying to set this flag, the transaction will fail. On the other hand, if set and transaction is submitted by an issuer, it would mean that the issuer wants to unauthorize the holder (only applicable for allow-listing), which would unset the `lsfMPTAuthorized` flag on the `MPToken`.|


### 1.3.6 The **`AccountDelete`** Transaction

We propose no changes to the `AccountDelete` transaction in terms of structure. However, accounts that have `MPTokenIssuance`s may not be deleted. These accounts will need to destroy each of their `MPTokenIssuances` using `MPTokenIssuanceDestroy` first before being able to delete their account. Without this restriction (or a similar one), issuers could render MPT balances useless/unstable for any holders.

### 1.3.7 The **`Clawback`** Transaction
The existing `Clawback` transaction will extend the existing `amount` field to accommodate MPT amounts. In addition, the `Clawback` transaction will introduce a new optional field, `MPTokenHolder`, to allow the issuer clawback `MPTokens` from holders' if and only if `lsfMPTAllowClawback` is set on the `MPTokenIssuance`.

#### 1.3.7.1 New `MPTokenHolder` field

| Field Name  | Required? | JSON Type | Internal Type |
| ----------- | --------- | --------- | ------------- |
| `MPTokenHolder` |    | `string`  | `ACCOUNTID`     | 

Specifies the holders address that the issuer wants to clawback from. Th holder must already own a `MPToken` object with a non-zero balance.

#### 1.3.7.2 Example

```json
{
    "TransactionType": "Clawback",
    "Account": "rf1BiGeXwwQoi8Z2ueFYTEXSwuJYfV2Jpn",
    "Amount": {
      "value": 10,
      "mpt_issuance_id": "0000012FFD9EE5DA93AC614B4DB94D7E0FCE415CA51BED47",
    },
    "MPTokenHolder": "rajgkBmMxmz161r8bWYH7CQAFZP5bA9oSG"
}
```
### 1.4.0 Details on Locking MPTs

#### 1.4.0.1 Locking individual balances

To lock an individual balance of an individual MPT an issuer will submit the `MPTokenIssuanceSet` transaction, indicate the MPT and holder account that they wish to lock, and set the `tfMPTLock` flag. This operation will fail if::

* The MPT has the `lsfMPTCanLock` flag _not_ set

Issuers can unlock the balance by submitting another `MPTokenIssuanceSet` transaction with the `tfMPTUnlock` flag set.

#### 1.4.0.2 Locking entire MPTs

This operation works the same as above, except that the holder account is not specified in the `MPTokenIssuanceSet` transaction when locking or unlocking. This operation will fail if::

* The MPT issuer has the `lsfMPTCanLock` flag _not_ set on their account

Locking an entire MPT without locking other assets issued by an issuer is a new feature of MPTs.

### 1.5.0 Details on Clawing-Back MPTs

To clawback funds from a MPT holder, the issuer must have specified that the MPT allows clawback by setting the `tfMPTCanClawback` flag when creating the MPT using the `MPTokenIssuanceCreate` transaction. Assuming a MPT was created with this flag set, clawbacks will be allowed using the `Clawback` transaction (more details to follow on how this transaction will change to accomodate the new values).

### 1.6.0 APIs

In general, existing RPC functionality can be used to interact with MPTs. For example, the `type` field of the  `account_objects` or `ledger_data` command can filter results by either `mpt_issuance` or `mptoken` values. In addition, the `ledger_entry` command can be used to query a specific `MPTokenIssuance` or `MPToken` object.

A new Clio RPC is proposed.

#### 1.6.0.1 `ledger_entry` API Updates
`ledger_entry` API is updated to query `MPTokenIssuance` and `MPToken` objects.

#### 1.6.0.1.1 `mpt_issuance` Field
A `MPTokenIssuance` object can be queried by specifying the the `mpt_issuance` field.

| Field Name           | Type| Description                                                                                                                                                                                                                               |
|---------------------|------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `mpt_issuance`      | ️String  | The 192-bit `MPTokenIssuanceID` that's associated with the `MPTokenIssuance`.|

#### 1.6.0.1.1 `mptoken` Field
A `MPToken` object can be queried by specifying the the `mptoken` field.

| Field Name           | Type| Description                                                                                                                                                                                                                               |
|---------------------|------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `mptoken`      | ️Object or String  | If string, interpret as ledger entry ID of the `MPToken` to retrieve. If an object, requires the sub-fields `account` and `mpt_issuance_id` to unique identify the `MPToken`.|
| `mptoken.mpt_issuance_id`      | ️String  | (Required if `mptoken` is specified as an object) The 192-bit `MPTokenIssuanceID` that's associated with the `MPTokenIssuance`.|
| `mptoken.account`      | ️String  | (Required if `mptoken` is specified as an object) The account that owns the `MPToken`.|

#### 1.6.0.2 `mpt_holders` API (Clio-only)
For a given `MPTokenIssuanceID`, `mpt_holders` will return all holders of that MPT and their balance. This RPC might return very large data sets, so users should handle result paging using the `marker` field.

##### 1.6.0.3.1 Request fields

```json
{
  "command": "mpt_holders",
  "mpt_issuance_id": "0000012FFD9EE5DA93AC614B4DB94D7E0FCE415CA51BED47",
  "ledger_index": "validated"
}
```

| Field Name        | Required?             | JSON Type |
|-------------------|:---------------------:|:---------:|
| `mpt_issuance_id`          |:heavy_check_mark:     | `string`  |

Indicates the MPTokenIssuance we wish to query.

| Field Name        | Required?             | JSON Type |
|-------------------|:---------------------:|:---------:|
| `ledger_index`    |                       | `string` or `number` (positive integer) |

The ledger index of the max ledger to use, or a shortcut string to choose a ledger automatically. Either `ledger_index` or `ledger_hash` must be specified.

| Field Name        | Required?             | JSON Type |
|-------------------|:---------------------:|:---------:|
| `ledger_hash`    |                       | `string`   |

A 20-byte hex string for the  max ledger version to use. Either `ledger_index` or `ledger_hash` must be specified.

| Field Name        | Required?             | JSON Type |
|-------------------|:---------------------:|:---------:|
| `marker`          |                       | `string`  |

Used to continue querying where we left off when paginating.

| Field Name        | Required?             | JSON Type |
|-------------------|:---------------------:|:---------:|
| `limit`           |                       | `number` (positive integer) |

Specify a limit to the number of MPTs returned.

##### 1.6.0.3.2 Response fields

| Field Name        | JSON Type | Description |
|-------------------|:---------:| --------- |
| `mpt_issuance_id` | `string`  | Indicates the `MPTokenIssuance` we queried. |
| `mptokens`   | `array`   | An array of `mptoken`s. Includes all relevant fields in the underlying `MPToken` object. |
| `marker`          | `string`  | Used to continue querying where we left off when paginating. Omitted if there are no more entries after this result. |
| `limit`          | `number`  | The limit, as specified in the request|
| `ledger_index`     | `number`  | The index of the ledger used.|

A `mptoken` object has the following parameters:
| Field Name          | JSON Type | Description |
| ------------------- |:---------:| ----------- |
| `account`           | `string`  | The account address of the holder who owns the `MPToken`. |
| `flags`             | `number`  | The flags of the MPToken objects.|
| `mpt_amount`        | `string`  | Hex-encoded amount of the holder's balance. |
| `locked_amount`     | `string`  | Hex-encoded amount of the locked balance. (May be discarded if the value is 0) |
| `mptoken_index`     | `string`  | Key of the `MPToken` object. |

###### 1.6.0.3.2.1 Example
```json
{
    "mpt_issuance_id": "000004C463C52827307480341125DA0577DEFC38405B0E3E",
    "limit":50,
    "ledger_index": 2,
    "mptokens": [{
        "account": "rEiNkzogdHEzUxPfsri5XSMqtXUixf2Yx",
        "flags": 0,
        "mpt_amount": "20",
        "locked_amount": "1",
        "mptoken_index": "36D91DEE5EFE4A93119A8B84C944A528F2B444329F3846E49FE921040DE17E65"
    },
    {
        "account": "rrnAZCqMahreZrKMcZU3t2DZ6yUndT4ubN",
        "flags": 0,
        "mpt_amount": "1",
        "mptoken_index": "D137F2E5A5767A06CB7A8F060ADE442A30CFF95028E1AF4B8767E3A56877205A"
    }],
    "validated": true
}
```

#### 1.6.0.3 Synthetic `mpt_issuance_id` field
`MPTokenIssuanceID` is an identifier that allows user to specify a `MPTokenIssuance` in RPCs. Therefore, a synthetically parsed `mpt_issuance_id` field is added into API responses to avoid the need for client-side parsing of the `MPTokenIssuanceID`.

##### 1.6.0.3.1 Transaction Metadata
 A `mpt_issuance_id` field is provided in JSON transaction metadata (not available for binary) for all successful `MPTokenIssuanceCreate` transactions. The following APIs are impacted: `tx`, `account_tx`, `subscribe` and `ledger`.

 ###### 1.6.0.3.1.1 Example
 Example of a `tx` response:
```json
{
   "result": {
      "Account": "rBT9cUqK6UvpvZhPFNQ2qpUTin8rDokBeL",
      "AssetScale": 2,
      "Fee": "10",
      "Flags": 64,
      "Sequence": 303,
      "SigningPubKey": "ED39955DEA2D083C6CBE459951A0A84DB337925389ACA057645EE6E6BA99D4B2AE",
      "TransactionType": "MPTokenIssuanceCreate",
      "TxnSignature": "80D7B7409980BE9854F7217BB8E836C8A2A191E766F24B5EF2EA7609E1420AABE6A1FDB3038468679081A45563B4D0B49C08F4F70F64E41B578F288A208E4206",
      "ctid": "C000013100000000",
      "date": 760643692,
      "hash": "E563D7942E3E4A79AD73EC12E9E4C44B7C9950DF7BF5FDB75FAD0F5CE0554DB3",
      "inLedger": 305,
      "ledger_index": 305,
      "meta": {
         "AffectedNodes": [...],
         "TransactionIndex": 0,
         "TransactionResult": "tesSUCCESS",
         "mpt_issuance_id": "0000012F72A341F09A988CDAEA4FF5BE31F25B402C550ABE"
      },
      "status": "success",
      "validated": true
   }
}
```

##### 1.6.0.3.2 Object
A `mpt_issuance_id` field is provided in JSON `MPTokenIssuance` objects (not available for binary). The following APIs are impacted: `ledger_data` and `account_objects`.

###### 1.6.0.3.2.1 Example
Example of an `account_objects` response:

```json
{
   "result": {
      "account": "rBT9cUqK6UvpvZhPFNQ2qpUTin8rDokBeL",
      "account_objects": [
         {
            "AssetScale": 2,
            "Flags": 64,
            "Issuer": "rBT9cUqK6UvpvZhPFNQ2qpUTin8rDokBeL",
            "LedgerEntryType": "MPTokenIssuance",
            "OutstandingAmount": "5a",
            "OwnerNode": "0",
            "PreviousTxnID": "BDC5ECA6B115C74BF4DA83E36325A2F55DF9E2C968A5CC15EB4D009D87D5C7CA",
            "PreviousTxnLgrSeq": 308,
            "Sequence": 303,
            "index": "75EC6F2939ED6C5798A5F369A0221BC4F6DDC50F8614ECF72E3B976351057A63",
            "mpt_issuance_id": "0000012F72A341F09A988CDAEA4FF5BE31F25B402C550ABE"
         }
      ],
      "ledger_current_index": 309,
      "status": "success",
      "validated": false
   }
}
```

# 2. Appendices

## 2.1 Appendix: FAQs

### 2.1.1. Are MPTs different from Trustlines?

Yes, MPTs are different from Trustlines. Read more in [section 1.1.2](#112-assumptions).

That said, there is some overlap in functionality between the two. For example, both MPTs and Trustlines can be used to issue a stablecoin. However, the original intent behind MPTs and Trustlines is subtly different, which impacts the on-ledger design of each. For clarity, Trustlines were invented primarily to service the idea of "community credit" and also to enhance liquidity on the ledger by making the same types of currency fungible amongst differing issuers (see [rippling](https://xrpl.org/rippling.html#rippling) for an example of each). MPTs, on the other hand, have three primary design motivations that are subtly different from Trustlines: (1) to enable tokenization using as little space (in bytes) on ledger as possible; (2) to eliminate floating point numbers and floating point math from the tokenization primitive; and (3) to make payment implementation simpler by, for example, removing [rippling](https://xrpl.org/rippling.html#rippling) and allowing MPT usage in places like [escrows](https://xrpl.org/escrow.html#escrow) or [payment channels](https://xrpl.org/payment-channels.html) in more natural ways.

### 2.1.2. Are MPTs meant to replace Trustlines?

No, replacing Trustlines is not the intent behind MPTs. Instead, it's likely that MPTs and Trustline can and will coexist because they enable subtly different use-cases (see [FAQ 2.1.1.](#211-are-mpts-different-from-trustlines), in particular the part about rippling).

### 2.1.3 Instead of MPTs, why not just make Trustlines smaller/better?

While it's true there are some proposals to make Trustlines more efficient (e.g., [optimize Trustline storage](https://github.com/XRPLF/rippled/issues/3866) and even (eliminate Custom Math)[https://github.com/XRPLF/rippled/issues/4120) from Trustlines), both of these are reasonably large changes that would change important aspect of the RippleState implementation. Any time we make changes like this, the risk is that these changes impact existing functionality in potentially unforeseen ways. The choice to build and implement MPT is ultimately a choice that balances this risk/reward tradeoff towards introducing somethign new to avoid breaking any existing functionality.

### 2.1.4. Are MPTs targeted for Mainnet or a Sidechain?

This is still being considered and debated, but is ultimately up to Validators to decide. On the one hand, MPTs on Mainnet would enable some new tokenization use-cases that could be problematic if Trustlines were to be used (see [FAQ 2.1.7](#217-an-early-draft-of-this-mpt-proposal-stored-mptoken-objects-in-a-paging-structure-similar-to-that-used-by-nfts-why-was-that-design-abandoned) for more details). On the other hand, adding MPTs introduces a new payment type into the payment engine, which complicates both the implementation of rippled itself, and XRPL tooling. 

In any event, we will first preview MPTs in a MPT-Devnet, and depending on what we learn there, revisit this issue then.

### 2.1.5. Will MPTs be encoded into an STAmount, or is a new C++ object type required?

MPTs will be able to be encoded in an `STAmount`. See [this gist](https://gist.github.com/sappenin/2c923bb249d4e9dd153e2e5f32f96d92) for more details.

### 2.1.6. Is there a limit to the number of `MPTokenIssuance` or `MPToken` objects that a single account can hold?

Practically speaking, no. The number of MPToken objects or MPTokenIssuance object that any account can hold is limited by the number of objects that can be stored in an owner directory, which is a very large number.

### 2.1.7. An early draft of this MPT proposal stored `MPToken` objects in a paging structure similar to that used by NFTs. Why was that design abandoned?

The original design was optimized for on-ledger space savings, but it came with a tradeoff of increased complexity, both in terms of this specification and the implementation. Another consideration is the datapoint that many NFT developers struggled with the mechanism used to identify NFTs, some of which is a result of the NFT paging structure.

After analyzing on-ledger space requirements for (a) Trustlines, (b) `MPTokenPages`, (c) and simply storing `MPToken` objects in an Owner Directory, we determined that for a typical user (i.e., one holding ~10 different MPTs), the overall space required by the simpler design strikes a nice balance between the more complicated design and Trustlines. For example, the simpler design regquires ~3.2x more bytes on-ledger than  more complicated design. However, the simpler design requires about 30% fewer bytes on-ledger than Trustlines.

With all that said, this decision is still open for debate. For example, in early 2024 the Ripple team plans to perform limit testing around Trustlines and the simpler MPT design to see how increased numbers of both types of ledger objects affect ledger performance. Once that data is complete, we'll likely revisit this design choice to either validate it or change it.

### 2.1.8. Why is there no `MPTRedeem` Transaction?

This is because holders of a MPT can use a normal payment transaction to send MPT back to the issuer, thus "redeeming" it and removing it from circulation. Note that one consequence of this design choice is that MPT issuer accounts may not also hold `MPToken` objects because, if the issuer could do such a thing, it would be ambiguous where incoming MPT payments should go (i.e., should that payment be a redemption and reduce the total amount of outstanding issuance, or should that payment go into an issuer's `MPToken` amount, and still be considered as "in circulation." For simplicity, we chose the former design, restricting MPT issuers from having `MPToken` objects at all.

### 2.1.9. Why can't MPToken Issuers also hold their own balances of MPT in a MPToken object?

See the question above. This design also helps enforce a security best practice where an issuing account should not also be used as an issuer's transactional account. Instead, any issuer should use a different XRPL account for non-issuance activity of their MPTs.

### 2.1.10. Why not use the `DepositPreauth` transaction for Authorized MPT Functionality?

For MPTokenIssuances that have the `lsfMPTRequireAuth` flag set, it is envisioned that a [DepositPreauth](https://xrpl.org/depositpreauth.html) transaction could be used with minor adaptations to distinguish between pre-authorized trust lines and pre-authorized MPTs. Alternatively, we might consider `deposit_preauth` objects might apply to both, under the assumption that a single issuer restricting trust lines will want to make the same restrictions around MPTs emanating from the same issuer account.

That said, this design is still TBD.

### 2.1.11. Why was the name Compact Fungible Token renamed to Multi-Purpose Token?

The initial name, "Compact Fungible Token", did not effectively convey the flexibility and versatility of this token standard. Therefore, we introduced a new name, "Multi-Purpose Token", to better reflect its capacity to accommodate user customization, catering towards fungible, semi-fungible, and potentially even non-fungible token use cases. This renaming aims to highlight the extensive capabilities available via MPTs.

For example, MPTs might be better suited than NFTs for certain semi-fungible use-cases (especially ones where each token might have a quantity greater than 1). In addition, some NFT issuers today issue multiple copies of the same NFT in order to make them semi-fungible. This technically violates the intent of the NFT spec, and may not work well in all NFT use-cases.

That said, we'll need to consider any future requirements and tradeoffs here before choosing between NFT or MPT for any particular use-case. For example, NFTs have the ability to link to off-ledger meta-data via the `URI` field, and likely require fewer storage bytes on-ledger than an MPT (though this deserves future research). 

## 2.2. Appendix: Outstanding Issues

This section describes any outstanding or debatable issues that have not yet been resolved in this proposal.

### 2.2.1. `MPTokenIssuanceID` options

There are a variety of ways to construct a `MPTokenIssuanceID`. This section outlines three that are currently up for debate:

#### 2.2.1.1. Hash issuer address and currency code

This is the conventional way of constructing an identifier, as the token holder can directly submit the transaction after knowing the issuer and the currency they want to use. However, if this is implemented, it means that after the issuer destroys an entire `MPTokenIssuance` (i.e., once nobody else holds any of it), the issuer can re-issue the same token with the same currency, resulting in the same `MPTokenIssuanceID`. This behavior can be misleading to token holders who have held onto the first iteration of the token rather than the re-issued one (since both iterations have the same `MPTokenIssuanceID`). In real world use cases(especially finance), after a fungible token is burned, it should not be possible to re-create it, and absolutely not with the same identifier.

#### 2.2.1.2. Option A: Currency array and limit the number of MPT issuances

This approach still constructs `MPTokenIssuanceID` by hashing the issuer address and currency code. But in an effort to solve the re-creatable `MPTokenIssuanceID` problem, the issuer stores an array of MPT currency codes that have been issued out. In this way, every time the issuer issues a new MPT, the ledger checks whether the currency code has already be used, and if so, the transaction fails. However, the problem with this approach is that the ledger would need to iterate through the currency array everytime the account attempts to issue a MPT, which would be unsustainable if the issuer can issue up to an unbounded number of MPTs. Hence, we impose a limit on the total number of MPTs that an account can issue(proposed limit is 32 MPTs).

But, this approach is not very clean in solving the problem, and there is a limit on the number of MPTs that the account can issue, which is not ideal since we would want the issuer to issue as many MPTs as they want.

#### 2.2.1.3. Option B: Construct MPTokenIssuance without currency code (current approach)

We realized that the problem with re-creatable MPTs is due to the account/currency pair where the currency can be re-used many times after the MPT has been burned. To solve this problem, the `MPTokenIssuanceID` is now constructed from two parameters: the issuer address and transaction sequence. Since the transaction sequence is an increasing index, `MPTokenIssuanceID` will never be re-created. And thus, the AssetCode/currency can be made as an optional field that's going to be used purely for metadata purposes.

Although using this approach would mean that MPT payment transactions would no longer involve the currency code, making it inconvenient for users, it is still an acceptable compromise. The ledger already has something similar - NFToken has a random identifier and uses clio for API services.

### 2.2.2. Allow-Listing

In certain use cases, issuers may want the option to only allow specific accounts to hold their MPT, similar to how authorization works for TrustLines.

#### 2.2.2.1. Without Allow-Listing

Let's first explore how the flow looks like without allow-listing:

1. Alice holds a MPT with asset-code `USD`.
2. Bob wants to hold it, and therefore submits a `MPTokenAuthorize` transaction specifying the `MPTokenIssuanceID`, and does not specify any flag. This will create a `MPToken` object with zero balance, and potentially taking up extra reserve.
3. Bob can now receive and send payments from/to anyone using `USD`.
4. Bob no longer wants to use the MPT, meaning that he needs to return his entire amount of `USD` back to the issuer through a `Payment` transaction. Resulting in a zero-balance `MPToken` object again.
5. Bob then submits a `MPTokenAuthorize` transaction that has set the `tfMPTUnauthorize` flag, which will successfully delete `MPToken` object.

#### 2.2.2.2. With Allow-Listing

The issuer needs to enable allow-listing for the MPT by setting the `lsfMPTRequireAuth` on the `MPTokenIssuance`.

With allow-listing, there needs to be a bidirectional trust between the holder and the issuer. Let's explore the flow and compare the difference with above:

1. Alice has a MPT of currency `USD` (same as above)
2. Bob wants to hold it, and therefore submits a `MPTokenAuthorize` transaction specifying the `MPTokenIssuanceID`, and does not specify any flag. This will create a `MPToken` object with zero balance, and potentially taking up extra reserve. (same as above)
**However at this point, Bob still does not have the permission to use `USD`!**
3. Alice needs to send a `MPTokenAuthorize` transaction specifying Bob's address in the `MPTokenHolder` field, and if successful, it will set the `lsfMPTAuthorized` flag on Bob's `MPToken` object. This will now finally enable Bob to use `USD`.
4. Same as step 4 above
6. 5. Same as step 5 above

**It is important to note that the holder always must first submit the `MPTokenAuthorize` transaction before the issuer.** This means that in the example above, steps 2 and 3 cannot be reversed where Alice submits the `MPTokenAuthorize` before Bob.

Issuer also has the ability to de-authorize a holder. In that case, if the holder still has outstanding funds, then it's the issuer's responsibility to clawback these funds.

### 2.2.3. `MPTokenNode` Directories?

The original intent of the `MPTokenNode` object is that it would be a sort of "directory" (i.e., an index) that stores a list of `MPTokenID` values (each 32 bytes) that exist for a single `MPTokenIssuance`. This would allow rippled to contain an RPC endpoint that could return a paged collection of `MPToken` objects for a given issuance, or somethign similar like an RPC called `mpt_holder_balances`. In theory, this could also enable rippled to operate a sort of "clean-up" operation that could remove dangling MPTokens that still live on a ledger after a corresponding `MPTokenIssuance` has been deleted (and thus return ledger reserves back to token holders).

#### 2.2.3.1 Should We Have `MPTokenNode` Directories?

While the introduction of a `MPTokenNode` server a particular use-case, we should debate further if we actually want to be solving that use-case, both for MPTs and more generally. For example, some in the community believe that many (most?) RPCs should be removed from rippled itself, especially ones that exist primarily for indexing purposes. That is, we should avoid storing data in the ledger that is not used by actual transactors, but instead only exists to service external processes via RPC. For example, we might consider moving these RPCs into Clio or some other service so that data indexing and more expensive indexing responsibility can be removed from the ledger itself, and thus removed as a burden for certain infrastructure operators. 

On the topic of removing dangling `MPTokenObjects`, this solution would introduce a background thread into rippled that might have unintended consequences on actual node operation. In addition, the pre-exising way for ledger cleanup to occur is for account holders to issue delete transactions; for example, we've seen very many of these types of transactions deleting both trustlines and accounts. 

#### 2.2.3.2 How Should We Design `MPTokenNode` Directories?

The proposed design of a new "MPT-only" directory structure introduces a new pattern that should be considered more. For example, in the XRP Ledger there are currently two types of "Directory" -- an "Owner Directory" and an "Offer Directory." The proposal of a new type of MPT directory suggests that we create a new type of owner-less directory specifically for MPTs (similar to `NFTokenOfferNode`). This directory would indeed be similar to an "Offer Directory" in the sense that there would be no owner; but the design otherwise diverges from that concept in the sense that these new MPT directories would not be aimed at DEX or exchange operations as is the case for DEX offers and `NFTokenOfferNode` objects.

As an alternative design, we might also (and instead) consider a new type of "Owner Directory" for MPTs that are (1) owned by the issuer yet (2) only holds `MPTokenID` values. In this way, this new type of directory would be more similar to an "Owner Directory" (because there's an owner), yet different because only `MPTokenID` values would be stored in this type of directory.

Both proposals entail somewhat of a divergence in architecture from what exists, so each should be debated and discussed further to explore tradeoffs and implications.

## 2.3. Appendix: Supplemental Information

### 2.3.1 On-Ledger Storage Requirements

#### 2.3.1.1. `RippleState` Object (Size in Bytes)

As described in issue [#3866](https://github.com/ripple/rippled/issues/3866#issue-919201191), the size of a [RippleState](https://xrpl.org/ripplestate.html#ripplestate) object is anywhere from 202 to 218 bytes plus a minimum of 32 bytes for object owner tracking. In addition, each trustline actually requires entries in both participant's Owner Directories, among other bytes.

This section attempts to catalog expected size, in bytes, for both Trustlines and MPTs, in an effort to predict expected space savings.

**Required Fields**

|        FIELD NAME | SIZE (BITS) | SIZE (BYTES) | NOTE                                                                                                                                                          | 
|------------------:|:-----------:|:------------:|:--------------------------------------------------------------------------------------------------------------------------------------------------------------|
|   LedgerEntryType |     16      |      2       |                                                                                                                                                               |
|             Flags |     32      |      4       | ("optional" but present in > 99.99% of cases)                                                                                                                 |
|           Balance |     384     |      48      | (160–224 wasted)                                                                                                                                              |
|          LowLimit |     384     |      48      | (160–224 wasted)                                                                                                                                              |
|         HighLimit |     384     |      48      | (160–224 wasted)                                                                                                                                              |
|           LowNode |     64      |      8       | (often has value 0)                                                                                                                                           |
|          HighNode |     64      |      8       | (often has value 0)                                                                                                                                           |
|     PreviousTxnID |     256     |      32      |                                                                                                                                                               |
| PreviousTxnLgrSeq |     32      |      4       |                                                                                                                                                               | 
|  Field+Type Codes |     144     |      18      | For every field, there is a `FieldCode` and a `TypeCode`, taking 2 bytes in total (e.g., if there are 4 fields, we'll use 8 bytes). Here we have nine fields. |
|               --- |     --      |     ---      |                                                                                                                                                               |
|         SUB-TOTAL |    1760     |     220      |                                                                                                                                                               |
|               --- |     --      |     ---      |                                                                                                                                                               |
|      LowQualityIn |     32      |      4       |                                                                                                                                                               |   
|     LowQualityOut |     32      |      4       | ("optional" but present in > 99.99% of cases)                                                                                                                 |   
|     HighQualityIn |     32      |      4       | (160–224 wasted)                                                                                                                                              |   
|    HighQualityOut |     32      |      4       | (160–224 wasted)                                                                                                                                              |
|  Field+Type Codes |     64      |      8       | For every field, there is a `FieldCode` and a `TypeCode`, taking 2 bytes in total (e.g., if there are 4 fields, we'll use 8 bytes). Here we have four fields. |
|               --- |     --      |     ---      |                                                                                                                                                               |
|         SUB-TOTAL |     192     |      24      |                                                                                                                                                               |
|               --- |     --      |     ---      |                                                                                                                                                               |                    
|             TOTAL |    1952     |     244      |                                                                                                                                                               |                    

#### 2.3.1.2. `MPToken` Object (Size in Bytes)

|        FIELD NAME | SIZE (BITS) | SIZE (BYTES) | NOTE                                                                                                                                                       |
|------------------:|:-----------:|:------------:|:-----------------------------------------------------------------------------------------------------------------------------------------------------------|
|   LedgerEntryType |     16      |      2       |                                                                                                                                                            |
| MPTokenIssuanceID |     192     |      24      |                                                                                                                                                            |
|         MPTAmount |     64      |      8       |                                                                                                                                                            |
|      LockedAmount |     64      |      8       |                                                                                                                                                            |
|             Flags |     32      |      4       |                                                                                                                                                            |
|     PreviousTxnID |     256     |      32      |                                                                                                                                                            |
| PreviousTxnLgrSeq |     32      |      4       |                                                                                                                                                            |
|  Field+Type Codes |     112     |      14      | For every field, there is a `FieldCode` and a `TypeCode`, taking 2 bytes in total (e.g., if there are 4 fields, we'll use 8 bytes). Here we have 7 fields. |
|               --- |     --      |     ---      |                                                                                                                                                            |
|             TOTAL |     768     |     96      |                                                                                                                                                            |

#### 2.3.1.3. Size Comparison

As can be seen from the following size comparison table, Trustlines take up approximately 2.2x as much space on ledger, in bytes, as MPTs would.

|                 Description | # MPT Directories | Total Bytes (MPT) | # Trustline Directories	 | Total Bytes (Trustline) | Trustlines are X-times Larger | 
|----------------------------:|:-----------------:|:-----------------:|:------------------------:|:-----------------------:|:-----------------------------:|
|  Bytes for holding 1 Tokens |         1         |        226        |            2             |           488           |             2.2x              |
| Bytes for holding 10 Tokens |         1         |       1,450       |            2             |          3,260          |             2.2x              |
| Bytes for holding 32 Tokens |         2         |       5,556       |            4             |         12,264          |             2.2x              |
| Bytes for holding 64 Tokens |         3         |      13,070       |            6             |         28,444          |             2.2x              |

### 2.3.2. `STAmount` serialization
Referenced from https://gist.github.com/sappenin/2c923bb249d4e9dd153e2e5f32f96d92 with some modifications:

#### Binary Encoding
To support this idea, we first need a way to leverage the current [STAmount](https://xrpl.org/serialization.html#amount-fields) binary encoding. To accomplish this, we notice that for XRP amounts, the maximum amount of XRP (10^17 drops) only requires 57 bits. However, in the current `XRP` STAmount encoding, there are 62 bits available. So, so we can repurpose one of these bits to indicate if an amount is indeed a MPT or not (and still have 4 bits left over for future use, if needed). 

This enables MPT amounts to be represented in the current `STAmount` binary encoding.  he rules for reading the binary amount fields would be backward compatible, as follows:

1. Parse off the Field ID with a type_code (`STI_AMOUNT`). This indicates the following bytes are an `STAmount`.
2. Inspect the next bit. If its value is `1`, then continue to the next step. If not, then this `STAmount` does **not** represent an MPT nor XRP (instead this is a regular IOU token amount, and can be parsed according to existing rules for those amounts). 
3. Ignore (for now) the 2nd bit (this is the sign-bit, and is always 1 for both XRP and MPT).
4. Inspect the 3rd bit. If `0`, then parse as an XRP value per usual. However, if `1`, then parse the remaining `STAmount` bytes as an MPT.

#### Encoding for XRP Values (backward compatible)

```
┌───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│ ┌──────────────────┐ ┌──────────────────────┐ ┌──────────────────┐ ┌──────────────────┐ ┌───────────────────────────────────────────┐ │
│ |        0         | |          1           | |        0         | |                  | |                                           | │
│ |                  | |                      | |                  | |     Reserved     | |                XRP Amount                 | │
│ |  "Not XRP" bit   | | Sign bit (always 1;  | |   "IsMPT" bit    | |     (4 bits)     | |                 (57 bits)                 | │
│ | 0=XRP/MPT; 1=IOU | |      positive)       | |   0=XRP; 1=MPT   | |                  | |                                           | │
│ └──────────────────┘ └──────────────────────┘ └──────────────────┘ └──────────────────┘ └───────────────────────────────────────────┘ │
└───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

#### Encoding for MPT Values (backward compatible)

This encoding focuses on the first 3 bits of a MPT:

```
┌────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│ ┌─────────────────┐┌────────────────────────┐┌────────────┐┌─────────────────────────────────────────────┐ │
│ │        0        ││           1            ││     1      ││                                             │ │
│ │                 ││                        ││            ││             Remaining MPT Bytes             │ │
│ │  "Not XRP" bit  ││  Sign bit (always 1;   ││"IsMPT" bit ││                 (261 bits)                  │ │
│ │0=XRP/MPT; 1=IOU ││       positive)        ││0=XRP; 1=MPT││                                             │ │
│ └─────────────────┘└────────────────────────┘└────────────┘└─────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

This encoding focuses on the rest of the bytes of a MPT (264 bits):

```
┌────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│ ┌─────────────────┐┌──────────────────┐┌──────────────────────┐┌──────────────────────────┐┌──────────────────────────┐│
│ │    [0][1][1]    ││                  ││                      ││                          ││                          ││
│ │                 ││     Reserved     ││   MPT Amount Value   ││      Sequence            ││     Issuer AcountID      ││
│ │   IsMPT=true    ││     (5 bits)     ││      (64 bits)       ││      (32 bits)           ││        (160 bits)        ││
│ │                 ││                  ││                      ││                          ││                          ││
│ └─────────────────┘└──────────────────┘└──────────────────────┘└──────────────────────────┘└──────────────────────────┘│
└────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

Note: MPT introduces an extra leading byte in front of the MPT value. However, despite the MPT value being 64-bit, only 63 bits can be used. This limitation arises because internally, rippled needs to convert the value to `int64`, which has a smaller positive range compared to `uint64`.