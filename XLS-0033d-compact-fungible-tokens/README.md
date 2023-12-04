<pre>
Title:       <b>Compact Fungible Tokens (CFTs)</b>
Type:        <b>draft</b>

Author:  
             <a href="mailto:fuelling@ripple.com">David Fuelling</a>
             <a href="mailto:nikb@bougalis.net">Nikolaos Bougalis</a>
             <a href="mailto:gweisbrod@ripple.com">Greg Weisbrod</a>
Affiliation: <a href="https://ripple.com">Ripple</a>
</pre>

# 1. Compact Fungible Tokens (CFTs)

## 1.1. Abstract

[Trust lines](https://xrpl.org/trust-lines-and-issuing.html#trust-lines-and-issuing) are a fundamental building block for many XRP Ledger tokenization features, including [CBDCs](https://en.wikipedia.org/wiki/Central_bank_digital_currency) and [fiat-collateralized stablecoins](https://www.investopedia.com/terms/s/stablecoin.asp). However, as more and more token issuers embrace the XRP Ledger, the current size of each trust line will become an impediment to ledger stability and scalability.

This proposal introduces extensions to the XRP Ledger to support a more compact fungible token (i.e., CFT) type, along with operations to enumerate, purchase, sell and hold such tokens. 

Unlike trust lines, CFTs do not represent bidirectional debt relationships. Instead, CFTs function more like a unidirectional trust line with only one balance, making it simpler to support common tokenization requirements, including even non-monetery use cases such as tracking reputation points in an online game. 

Perhaps as important, however, CFTs require significantly less space than trust lines: ~52 bytes for each CFT held by a token holder, as compared to _at least_ 234 bytes for every new trust line (see Appendix 1 for a more detailed comparison).

### 1.1.1. Advantages and Disadvantages

**Advantages**

* Uses a fixed-point balance representation instead of a floating-point representation, yielding the following benefits:
  * CFT balance amounts can easily be added to other ledger objects like escrows, checks, payment channels, and AMMs.
  * Enables reliable and easy enforcement of invariant checks and straightforward tracking of fees.
  * Eliminates edge case floating-point math involving very small amounts violating expected equality conditions (e.g., CFTs will never have to deal with cases where `A+B=A` for non-zero `B` or `(A+B)+C != A+(B+C)`). 
* Simpler conceptual model (trust lines and rippling make it harder for developers to reason about the system, which increases the risk of errors or value loss).
* Reduces trust line storage requirements which allows more accounts to hold more tokens, for less cost.
* Reduces long-term infrastructure and storage burdens on node operators, increasing network resiliency.
* Improves node performance when processing large volumes of CFT transactions.

**Disadvantages**

* CFTs would introduce a third asset type on the ledger after XRP and IOUs, which complicates the Payment Engine implementation.
* New transaction and data types require new implementation code from client libraries and wallets to read, display, and transact.
* CFTs will represent a smaller overall balance amount as compared to trust lines (Trustlines can represent an enormous range, roughly between 10^-96 to 10^80). 

### 1.1.2. Assumptions
This proposal makes a variety of assumptions, based upon observations of existing trust line usage in order to produce the most compact representations of data. These assumptions include:

1. **Only Unidirectional**. This proposal does not support bidirectional trust line constructions, on the assumption that _most_ token issuers leave their trust line limit set to the default value of 0 (i.e., issuers don't allow debt relationships with token holders, by default). Thus, CFTs do not have the same "balance netting" functionality found in trust lines because CFTs have only a single balance as opposed to the two balances used by trust lines.
2. **Few Issuances per Issuer**. The most common examples of fungible token issuance involve regulatory overhead, which makes it less common for issuers to issue _many_ fungible tokens, in the general case. In addition, existing [guidance on xrpl.org](https://xrpl.org/freezes.html#global-freeze) advises token issuers to use different addresses for each token issuance in order to better accomodate [global freeze](https://xrpl.org/enact-global-freeze.html) activities. Because of this, we assume that any individual issuer will not issue many different fungible tokens using the same address. In particular, this specification limits the number of unique CFT issuances to 32 per issuing account. If an issuer wishes to support more than this number of CFTs, additional addresses can still be used.
3. **No Trust Limits**. Unlike current Trustline functionality where trust amount limits can be set by either party, this proposal eliminates this feature under the assumption that token holders will not acquire a CFT without first making an off-ledger trust decision. For example, a common use-case for a CFT is a fiat-backed stablecoin, where a token holder wouldn't purchase more stablecoin than they would feel comfortable holding.
4. **No Rippling**. Unlike some existing capabilities of the ledger, CFTs are not eligible for [rippling](https://xrpl.org/rippling.html#rippling), and thus do not have any configurability settings related to that functionality.

### 1.1.3 Release Timeline and Scope

XLS-33 will only cover the addition of the new data structures for CFTs, integration with the **`Payment`** transaction such that users can make CFT to CFT payments (IE no cross currency payments), and several other incidental additions like new requirements for account deletion (discussed below). Later amendments will integrate CFTs with other features of the XRPL such as the DEX.

## 1.2. Creating Compact Fungible Tokens

### 1.2.1. On-Ledger Data Structures

We propose two new objects and one new ledger structure:

1. A **`CFTokenIssuance`** is a new object that describes a fungible token issuance created by an issuer.
1. A **`CFToken`** is a new object that describes a single account's holdings of an issued token.

#### 1.2.1.1. The **`CFTokenIssuance`** object

The **`CFTokenIssuance`** object represents a single CFT issuance and holds data associated with the issuance itself. Token issuances are created using the **`CFTokenIssuanceCreate`** transaction and can, optionally, be destroyed by the **`CFTokenIssuanceDestroy`** transaction.

##### 1.2.1.1.1. **`CFTokenIssuance`** Ledger Identifier
The ID of an CFTokenIssuance object, a.k.a `CFTokenIssuanceID` is the result of SHA512-Half of the following values, concatenated in order:

* The CFTokenIssuance space key (0x007E).
* The AccountID of the issuer.
* The transaction sequence number

##### 1.2.1.1.2. Fields

**`CFTokenIssuance`** objects are stored in the ledger and tracked in an [Owner Directory](https://xrpl.org/directorynode.html) owned by the issuer. Issuances have the following required and optional fields:

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
| `CFTokenMetadata`   |                     | `string`  | `BLOB`        |
| `PreviousTxnID`     | :heavy_check_mark:  | `string`  | `HASH256`     |
| `PreviousTxnLgrSeq` | ️:heavy_check_mark: | `number`  | `UINT32`      |
| `OwnerNode`         | (default)           | `number`  | `UINT64`      |

###### 1.2.1.1.2.1. `LedgerEntryType`

The value 0x007E, mapped to the string `CFTokenIssuance`, indicates that this object describes a Compact Fungible Token (CFT).

###### 1.2.1.1.2.2. `Flags`

A set of flags indicating properties or other options associated with this **`CFTokenIssuance`** object. The type specific flags proposed  are:

| Flag Name           | Flag Value | Description                                                                                                                                                                                                                               |
|---------------------|------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `lsfCFTLocked`      | ️`0x0001`  | If set, indicates that all balances are locked.                                                                                                                                                                                           |
| `lsfCFTCanLock`     | ️`0x0002`  | If set, indicates that the issuer can lock an individual balance or all balances of this CFT.  If not set, the CFT cannot be locked in any way.                                                                                           |
| `lsfCFTRequireAuth` | ️`0x0004`  | If set, indicates that _individual_ holders must be authorized. This enables issuers to limit who can hold their assets.                                                                                                                  |
| `lsfCFTCanEscrow`   | `0x0008`   | If set, indicates that _individual_ holders can place their balances into an escrow.                                                                                                                                                      |
| `lsfCFTCanTrade`    | `0x0010`   | If set, indicates that _individual_ holders can trade their balances using the XRP Ledger DEX or AMM.                                                                                                                                     |
| `lsfCFTCanTransfer` | ️`0x0020`  | If set, indicates that tokens held by non-issuers may be transferred to other accounts. If not set, indicates that tokens held by non-issuers may not be transferred except back to the issuer; this enables use-cases like store credit. |
| `lsfCFTCanClawback` | ️`0x0040`  | If set, indicates that the issuer may use the `Clawback` transaction to clawback value from _individual_ holders.                                                                                                                         |

Except for `lsfCFTLocked`, which can be mutated via the `**CFTokenIssuanceSet**` transactions, these flags are **immutable**: they can only be set during the **`CFTokenIssuanceCreate`** transaction and cannot be changed later.

###### 1.2.1.1.2.3. `Issuer`

The address of the account that controls both the issuance amounts and characteristics of a particular fungible token.

###### 1.2.1.1.2.4. `AssetScale`

An asset scale is the difference, in orders of magnitude, between a standard unit and a corresponding fractional unit. More formally, the asset scale is a non-negative integer (0, 1, 2, …) such that one standard unit equals 10^(-scale) of a corresponding fractional unit. If the fractional unit equals the standard unit, then the asset scale is 0.

###### 1.2.1.1.2.5. `MaximumAmount`

This value is an unsigned number that specifies the maximum number of CFTs that can be distributed to non-issuing accounts (i.e., `minted`). For issuances that do not have a maximum limit, this value should be set to 0xFFFFFFFFFFFFFFFF.

###### 1.2.1.1.2.6. `OutstandingAmount`

Specifies the sum of all token amounts that have been minted to all token holders. This value can be stored on ledger as a `default` type so that when its value is 0, it takes up less space on ledger. This value is increased whenever an issuer pays CFTs to a non-issuer account, and decreased whenever a non-issuer pays CFTs into the issuing account.

###### 1.2.1.1.2.7. `TransferFee`

This value specifies the fee, in tenths of a [basis point](https://en.wikipedia.org/wiki/Basis_point), charged by the issuer for secondary sales of the token, if such sales are allowed at all. Valid values for this field are between 0 and 50,000 inclusive. A value of 1 is equivalent to 1/10 of a basis point or 0.001%, allowing transfer rates between 0% and 50%. A `TransferFee` of 50,000 corresponds to 50%. The default value for this field is 0. Any decimals in the transfer fee will be rounded down, hence the fee can be rounded down to zero if the payment is small. Issuer should make sure that their CFT's `AssetScale` is large enough.

###### 1.2.1.1.2.8. `PreviousTxnID`

Identifies the transaction ID of the transaction that most recently modified this object.

###### 1.2.1.1.2.9. `PreviousTxnLgrSeq`

The sequence of the ledger that contains the transaction that most recently modified this object.

###### 1.2.1.1.2.10. `OwnerNode`

Identifies the page in the owner's directory where this item is referenced.

##### 1.2.1.1.3. Example **`CFTokenIssuance`** JSON

 ```json
 {
     "LedgerEntryType": "CFTokenIssuance",
     "Flags": 131072,
     "Issuer": "rsA2LpzuawewSBQXkiju3YQTMzW13pAAdW",
     "AssetScale": "2",
     "MaximumAmount": "100000000",
     "OutstandingAmount": "5",
     "TransferFee": 50000,     
     "CFTokenMetadata": "",
     "OwnerNode": "74"
 }
 ```

##### 1.2.1.1.4. How do **`CFTokenIssuance`** objects work?

Any account may issue any number of Compact Fungible Tokens.

###### 1.2.1.1.4.1. Searching for a **`CFTokenIssuance`** object

CFT Issuances are uniquely identified by a combination of a type-specific prefix, the issuer address and a transaction sequence number. To locate a specific **`CFTokenIssuance`**, the first step is to locate the owner directory for the issuer. Then, find the directory that holds `CFTokenIssuance` ledger objects and iterate through each entry to find the instance with the desired key. If that entry does not exist then the **`CFTokenIssuance`** does not exist for the given account.

###### 1.2.1.1.4.2. Adding a **`CFTokenIssuance`** object

A **`CFTokenIssuance`** object can be added by using the same approach to find the **`CFTokenIssuance`**, and adding it to that directory. If, after addition, the number of CFTs in the directory would exceed 32, then the operation must fail.

###### 1.2.1.1.4.3. Removing a **`CFTokenIssuance`** object

A **`CFTokenIssuance`** can be removed using the same approach, but only if the **`CurMintedAmount`** is equal to 0.

###### 1.2.1.1.4.4. Reserve for **`CFTokenIssuance`** object

Each **`CFTokenIssuance`** costs an incremental reserve to the owner account.

#### 1.2.1.2. The **`CFToken`** object
The **`CFToken`** object represents an amount of a token held by an account that is **not** the token issuer. CFTs are acquired via ordinary Payment or DEX transactions, and can optionally be redeemed or exchanged using these same types of transactions. The object key of the `CFToken` is derived from hashing the space key, holder's address and the `CFTokenIssuanceID`.

##### 1.2.1.2.1 Fields
A **`CFToken`** object can have the following fields. The key of each CFToken is stored in the Owner Directory for the account that holds the `CFToken`.

| Field Name          | Required?          | JSON Type | Internal Type |
|---------------------|--------------------|-----------|---------------|
| `LedgerEntryType`   | :heavy_check_mark: | `number`  | `UINT16`      |
| `Account`           | :heavy_check_mark: | `string`  | `ACCOUNTID`   |
| `CFTokenIssuanceID` | :heavy_check_mark: | `string`  | `UINT256`     |
| `CFTAmount`         | :heavy_check_mark: | `string`  | `UINT64`      |
| `LockedAmount`      | default            | `string`  | `UINT64`      |
| `Flags`             | default            | `number`  | `UINT32`      |
| `PreviousTxnID`     | :heavy_check_mark: | `string`  | `HASH256`     |
| `PreviousTxnLgrSeq` | :heavy_check_mark: | `number`  | `UINT32`      |
| `OwnerNode`         | default            | `number`  | `UINT64`      |
| `CFTokenNode`       | default            | `number`  | `UINT64`      |

###### 1.2.1.2.1.1. `LedgerEntryType`

The value 0x007F, mapped to the string `CFToken`, indicates that this object describes an individual account's holding of a CFT.

###### 1.2.1.2.1.2. `Account`

The owner of the `CFToken`.

###### 1.2.1.2.1.3. `CFTokenIssuanceID`

The `CFTokenIssuance` identifier.

###### 1.2.1.2.1.4. `CFTAmount`

This value specifies a positive amount of tokens currently held by the owner. Valid values for this field are between 0x0 and 0xFFFFFFFFFFFFFFFF.

###### 1.2.1.2.1.5. `LockedAmount`

This value specifies a positive amount of tokens that are currently held in a token holder's account but that are unavailable to be used by the token holder. Locked tokens might, for example, represent value currently being held in escrow, or value that is otherwise inaccessible to the token holder. 

This value is stored as a `default` value such that it's initial value is `0`, in order to save space on the ledger for a an empty CFT holding.

###### 1.2.1.2.1.6. `Flags`

A set of flags indicating properties or other options associated with this **`CFTokenIssuance`** object. The type specific flags proposed  are:

| Flag Name          | Flag Value | Description                                                                                                                                                                                                                                                                      |
|--------------------|------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `lsfCFTLocked`     | `0x0001`   | If set, indicates that the CFT owned by this account is currently locked and cannot be used in any XRP transactions other than sending value back to the issuer. When this flag is set, the `LockedAmount` must equal the `CFTAmount` value.                                     |
| `lsfCFTAuthorized` | `0x0002`   | (Only applicable for allow-listing) If set, indicates that the issuer has authorized the holder for the CFT. This flag can be set using a `CFTokenAuthorize` transaction; it can also be "un-set" using a `CFTokenAuthorize` transaction specifying the `tfCFTUnauthorize` flag. |

###### 1.2.1.1.2.7. `PreviousTxnID`

Identifies the transaction ID of the transaction that most recently modified this object.

###### 1.2.1.1.2.8. `PreviousTxnLgrSeq`

The sequence of the ledger that contains the transaction that most recently modified this object.

###### 1.2.1.1.2.9. `OwnerNode`

Identifies the page in the owner's directory where this item is referenced.

###### 1.2.1.1.2.10. `CFTokenNode`

The CFT directory has exactly the same structure as an [Owner Directory]([Owner Directory](https://xrpl.org/directorynode.html)), except this is a new type of directory that only indexes `CFTokens` for a single `CFTokenIssuance`. Ownership of this directory is still up for debate per [CFTokenNode Directories](#223-cftokennode-directories).

##### 1.2.1.2.2. Example CFToken JSON

 ```json
 {
     "LedgerEntryType": "CFToken",
     "Account": "rajgkBmMxmz161r8bWYH7CQAFZP5bA9oSG",
     "CFTokenIssuanceID": "00070C4495F14B0E44F78A264E41713C64B5F89242540EE255534400000000000000",
     "Flags": 0,
     "CFTAmount": "100000000",
     "LockedAmount": "0",
     "OwnerNode": 1
 }
 ```

##### 1.2.1.2.3. Reserve for **`CFToken`** object

Each **`CFToken`** costs an incremental reserve to the owner account.

## 1.3 Transactions

This proposal introduces several new transactions to allow for the creation and deletion of CFT issuances. Likewise, this proposal introduce several new transactions for minting and redeeming discrete instances of CFTs. All transactions introduced by this proposal incorporate the [common transaction fields](https://xrpl.org/transaction-common-fields.html) that are shared by all transactions. Common fields are not documented in this proposal unless needed because this proposal introduces new possible values for such fields.

### 1.3.1 Transactions for Creating and Destroying Compact Fungible Token Issuances on XRPL
We define three transactions related to CFT Issuances: **`CFTokenIssuanceCreate`** and **`CFTokenIssuanceDestroy`** and  **`CFTokenIssuanceSet`** for minting, destroying, and updating CFT _Issuances_ respectively on XRPL.

#### 1.3.1.1 The **`CFTokenIssuanceCreate`** transaction

The **`CFTokenIssuanceCreate`** transaction creates a **`CFTokenIssuance`** object and adds it to the relevant directory node of the creator account. This transaction is the only opportunity an `issuer` has to specify any token fields that are defined as immutable (e.g., CFT Flags).

If the transaction is successful, the newly created token will be owned by the account (the creator account) which executed the transaction.

##### 1.3.1.1.1 Transaction-specific Fields
| Field Name         | Required? | JSON Type | Internal Type |
| ------------------ | --------- | --------- |---------------|
| `TransactionType`  | ️ ✔        | `object`  | `UINT16`      |

Indicates the new transaction type **`CFTokenIssuanceCreate`**. The integer value is `25 (TODO)`.

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
| `tfCFTLocked`                | ️`0x0001`  | If set, indicates that all balances should be locked. This is a global lock that locks up all of holders' funds for this CFToken.|
| `tfCFTCanLock`  | ️`0x0002`  | If set, indicates that the CFT can be locked both individually and globally. If not set, the CFT cannot be locked in any way.|
| `tfCFTRequireAuth` | ️`0x0004`  | If set, indicates that _individual_ holders must be authorized. This enables issuers to limit who can hold their assets.  |
| `tfCFTCanEscrow`             | `0x0008`  | If set, indicates that _individual_ holders can place their balances into an escrow. |
| `tfCFTCanTrade`              | `0x0010`  | If set, indicates that _individual_ holders can trade their balances using the XRP Ledger DEX. |
| `tfCFTCanTransfer`          | ️`0x0020`  | If set, indicates that tokens may be transferred to other accounts that are not the issuer. |
| `tfCFTCanClawback`          | ️`0x0040`  | If set, indicates that the issuer may use the `Clawback` transaction to clawback value from _individual_ holders.|

| Field Name    | Required? | JSON Type | Internal Type |
| ------------- | --------- | --------- | ------------- |
| `TransferFee` |           | `number`  | `UINT16`      | 

The value specifies the fee to charged by the issuer for secondary sales of the Token, if such sales are allowed. Valid values for this field are between 0 and 50,000 inclusive, allowing transfer rates of between 0.000% and 50.000% in increments of 0.001.

The field MUST NOT be present if the `tfCFTCanTransfer` flag is not set. If it is, the transaction should fail and a fee should be claimed.

| Field Name      | Required?          | JSON Type | Internal Type |
| --------------- | ------------------ | --------- | ------------- |
| `MaximumAmount` |  | `string`  | `UINT64`      | 

The maximum asset amount of this token that should ever be issued.

| Field Name        | Required?          | JSON Type | Internal Type |
| ------------------| ------------------ | --------- | ------------- |
| `CFTokenMetadata` |  | `string`  | `BLOB`        | 

Arbitrary metadata about this issuance, in hex format. The limit for this field is 1024 bytes.

##### 1.3.1.1.2 Example **`CFTokenIssuanceCreate`** transaction

```json
{
  "TransactionType": "CFTokenIssuanceCreate",
  "Account": "rajgkBmMxmz161r8bWYH7CQAFZP5bA9oSG",
  "AssetScale": "2",
  "TransferFee": 314,
  "MaxAmount": "50000000",
  "Flags": 83659,
  "CFTokenMetadata": "FOO",
  "Fee": 10
}
```

This transaction assumes that the issuer of the token is the signer of the transaction.

### 1.3.2 The **`CFTokenIssuanceDestroy`** transaction

The **`CFTokenIssuanceDestroy`** transaction is used to remove an **`CFTokenIssuance`** object from the directory node in which it is being held, effectively removing the token from the ledger ("destroying" it).

If this operation succeeds, the corresponding **`CFTokenIssuance`** is removed and the owner’s reserve requirement is reduced by one. This operation must fail if there are any holders of the CFT in question.

#### 1.3.2.1 Transaction-specific Fields

| Field Name        | Required? | JSON Type | Internal Type |
| ----------        | --------- | --------- | ------------- |
| `TransactionType` |  ✔️        | `string`  | `UINT16`      | 

Indicates the new transaction type **`CFTokenIssuanceDestroy`**. The integer value is `26` (TODO).

| Field Name  | Required? | JSON Type | Internal Type |
| ----------- | --------- | --------- | ------------- |
| `CFTokenIssuanceID` |  ✔️        | `string`  | `UINT256`     | 

Identifies the **`CFTokenIssuance`** object to be removed by the transaction.

#### 1.3.2.2 Example **`CFTokenIssuanceDestroy`** JSON

 ```json
 {
       "TransactionType": "CFTokenIssuanceDestroy",
       "Fee": 10,
       "CFTokenIssuanceID": "00070C4495F14B0E44F78A264E41713C64B5F89242540EE255534400000000000000"
 }
 ```
 
### 1.3.3 The **`CFTokenIssuanceSet`** Transaction

#### 1.3.3.1 CFTokenIssuanceSet
| Field Name         | Required? | JSON Type | Internal Type |
| ------------------ | --------- | --------- |---------------|
| `TransactionType`  | ️ ✔        | `object`  | `UINT16`      |

Indicates the new transaction type **`CFTokenIssuanceSet`**. The integer value is `28 (TODO)`.

| Field Name  | Required? | JSON Type | Internal Type |
| ----------- | --------- | --------- | ------------- |
| `CFTokenIssuanceID` |  ✔️  | `string`  | `UINT256`     | 

The `CFTokenIssuance` identifier.

| Field Name      | Required?          | JSON Type | Internal Type |
| --------------- | ------------------ | --------- | ------------- |
| `CFTokenHolder`       | | `string`  | `ACCOUNTID`   | 

An optional XRPL Address of an individual token holder balance to lock/unlock. If omitted, this transaction will apply to all any accounts holding CFTs.

| Field Name      | Required?          | JSON Type | Internal Type |
| --------------- | ------------------ | --------- | ------------- |
| `Flag`          | :heavy_check_mark: | `string`  | `UINT64`      | 

#### 1.3.3.2 Example **`CFTokenIssuanceSet`** JSON

 ```json
 {
       "TransactionType": "CFTokenIssuanceSet",
       "Fee": 10,
       "CFTokenIssuanceID": "00070C4495F14B0E44F78A264E41713C64B5F89242540EE255534400000000000000",
       "Flags": 1
 }
 ```
 
#### 1.3.3.1.1 CFTokenIssuanceSet Flags
Transactions of the `CFTokenLock` type support additional values in the Flags field, as follows:

| Flag Name         | Flag Value | Description |
|-------------------|------------|-------------|
| `tfCFTLock`     | ️`0x0001`  | If set, indicates that all CFT balances for this asset should be locked. |
| `tfCFTUnlock`   | ️`0x0002`  | If set, indicates that all CFT balances for this asset should be unlocked. |

### 1.3.4 The **`Payment`** Transaction
The existing `Payment` transaction will not have any new top-level fields or flags added. However, we will extend the existing `amount` field to accommodate CFT amounts.

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

We propose using the following format for CFT amounts::

```json
"amount": {
  "cft_issuance_id": "00070C4495F14B0E44F78A264E41713C64B5F89242540EE255534400000000000000",
  "value": "1"
}
```

Note: The `CFTokenIssuanceID` will be used to uniquely identify the CFT during a Payment transaction.

### 1.3.5 The **`CFTokenAuthorize`** Transaction

This transaction enables an account to hold an amount of a particular CFT issuance. When applied successfully, it will create a new `CFToken` object with an initial zero balance, owned by the holder account.

If the issuer has set `lsfCFTRequireAuth` (allow-listing) on the `CFTokenIssuance`, then the issuer must submit a `CFTokenAuthorize` transaction as well in order to give permission to the holder. If `lsfCFTRequireAuth` is not set and the issuer attempts to submit this transaction, it will fail.

#### 1.3.5.1 CFTokenAuthorize

| Field Name      | Required?          | JSON Type | Internal Type |
| --------------- | ------------------ | --------- | ------------- |
| `Account`       | :heavy_check_mark: | `string`  | `ACCOUNTID`   | 

This address can indicate either an issuer or a potential holder of a CFT.

| Field Name         | Required? | JSON Type | Internal Type |
| ------------------ | --------- | --------- |---------------|
| `TransactionType`  | ️ ✔        | `object`  | `UINT16`      |

Indicates the new transaction type **`CFTokenAuthorize`**. The integer value is `29 (TODO)`.

| Field Name  | Required? | JSON Type | Internal Type |
| ----------- | --------- | --------- | ------------- |
| `CFTokenIssuanceID` |  ✔️  | `string`  | `UINT256`     | 

Indicates the ID of the CFT involved. 

| Field Name  | Required? | JSON Type | Internal Type |
| ----------- | --------- | --------- | ------------- |
| `CFTokenHolder` |    | `string`  | `ACCOUNTID`     | 

Specifies the holders address that the issuer wants to authorize. Only used for authorization/allow-listing; must be empty if submitted by the holder.

| Field Name      | Required?          | JSON Type | Internal Type |
| --------------- | ------------------ | --------- | ------------- |
| `Flag`          | :heavy_check_mark: | `string`  | `UINT64`      | 

 
#### 1.3.3.5.12 CFTokenAuthorize Flags

Transactions of the `CFTokenAuthorize` type support additional values in the Flags field, as follows:

| Flag Name         | Flag Value | Description |
|-------------------|------------|-------------|
| `tfCFTUnauthorize`     | ️`0x0001`  | If set and transaction is submitted by a holder, it indicates that the holder no longer wants to hold the `CFToken`, which will be deleted as a result. If the the holder's `CFToken` has non-zero balance while trying to set this flag, the transaction will fail. On the other hand, if set and transaction is submitted by an issuer, it would mean that the issuer wants to unauthorize the holder (only applicable for allow-listing), which would unset the `lsfCFTAuthorized` flag on the `CFToken`.|


### 1.3.6 The **`AccountDelete`** Transaction

We propose no changes to the `AccountDelete` transaction in terms of structure. However, accounts that have `CFTokenIssuance`s may not be deleted. These accounts will need to destroy each of their `CFTokenIssuances` using `CFTokenIssuanceDestroy` first before being able to delete their account. Without this restriction (or a similar one), issuers could render CFT balances useless/unstable for any holders.

### 1.4.0 Details on Locking CFTs

#### 1.4.0.1 Locking individual balances

To lock an individual balance of an individual CFT an issuer will submit the `CFTokenIssuanceSet` transaction, indicate the CFT and holder account that they wish to lock, and set the `tfCFTLock` flag. This operation will fail if::

* The CFT has the `lsfCFTCanLock` flag _not_ set

Issuers can unlock the balance by submitting another `CFTokenIssuanceSet` transaction with the `tfCFTUnlock` flag set.

#### 1.4.0.2 Locking entire CFTs

This operation works the same as above, except that the holder account is not specified in the `CFTokenIssuanceSet` transaction when locking or unlocking. This operation will fail if::

* The CFT issuer has the `lsfCFTCanLock` flag _not_ set on their account

Locking an entire CFT without locking other assets issued by an issuer is a new feature of CFTs.

### 1.5.0 Details on Clawing-Back CFTs

To clawback funds from a CFT holder, the issuer must have specified that the CFT allows clawback by setting the `tfCFTCanClawback` flag when creating the CFT using the `CFTokenIssuanceCreate` transaction. Assuming a CFT was created with this flag set, clawbacks will be allowed using the `Clawback` transaction (more details to follow on how this transaction will change to accomodate the new values).

### 1.6.0 APIs

We propose several new APIs for this feature. All new APIs will be available only in `clio`.

#### 1.6.0.1 `cfts_by_issuer`

For a given account and ledger, it will show all `CFTokenIssuances` created by this account, including any deleted `CFTokenIssuances`. Deleted CFTokenIssuance may have the same ID as new CFTokenIssuances.

##### 1.6.0.1.1 Request fields

```json
{
  "command": "cfts_by_isssuer",
  "issuer": "rf1BiGeXwwQoi8Z2ueFYTEXSwuJYfV2Jpn",
  "ledger_index": "validated",
  "include_deleted": true
}
```

| Field Name        | Required?             | JSON Type |
|-------------------|:---------------------:|:---------:|
| `issuer`          |:heavy_check_mark:     | `string`  |

Indicates the CFT issuer whose CFTs we wish to query.

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
| `include_deleted` |                       | `boolean` |

Default `false`. If `true`, will included deleted CFTs as well.

| Field Name        | Required?             | JSON Type |
|-------------------|:---------------------:|:---------:|
| `marker`          |                       | `string`  |

Used to continue querying where we left off when paginating.

| Field Name        | Required?             | JSON Type |
|-------------------|:---------------------:|:---------:|
| `limit`           |                       | `number` (positive integer) |

Specify a limit to the number of CFTs returned.

##### 1.6.0.1.2 Response fields

```json
{
    "id": 5,
    "status": "success",
    "type": "response",
    "result": {
        "cft_issuances": [
           {
             "CFTokenIssuanceID": "00070C4495F14B0E44F78A264E41713C64B5F89242540EE255534400000000000000",
             "Flags": 83659,
             "Issuer": ......,
             "AssetScale": .....,
             "MaximumAmount": .....,
             "OutstandingAmount": ....,
             "LockedAmount": .....,
             "TransferFee": .....,
             "CFTokenMetadata": ....,
             "ledger_index": 11231
           }
        ],
        "validated": true
    }
}
```

| Field Name        | JSON Type |
|-------------------|:---------:|
| `cft_issuances`   | `array`   |

An array of CFTokenIssuance objects created by the specified account. Includes all fields in the existing underlying object, `ledger_index` for the index at which this CFT was last modified.  For a deleted object, only `CFTokenIssuanceID` and `deleted_ledger_index` for the index at which this CFT was deleted are shown.

| Field Name        | JSON Type |
|-------------------|:---------:|
| `marker`          | `string`  |

Used to continue querying where we left off when paginating. Omitted if there are no more entries after this result.

#### 1.6.0.2 `account_cfts`
For a given account and ledger, `account_cfts` will return all CFT balances held by this account.

##### 1.6.0.2.1 Request fields

```json
{
  "command": "account_cfts",
  "account": "rf1BiGeXwwQoi8Z2ueFYTEXSwuJYfV2Jpn",
  "ledger_index": "validated"
}
```

| Field Name        | Required?             | JSON Type |
|-------------------|:---------------------:|:---------:|
| `account`         |:heavy_check_mark:     | `string`  |

Indicates the account whose CFT balances we wish to query.

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

Specify a limit to the number of CFT balances returned.


##### 1.6.0.2.2 Response fields

```json
{
    "id": 5,
    "status": "success",
    "type": "response",
    "result": {
        "account": "rf1BiGeXwwQoi8Z2ueFYTEXSwuJYfV2Jpn",
        "cfts": [
           {
             "CFTokenIssuanceID": "00070C4495F14B0E44F78A264E41713C64B5F89242540EE255534400000000000000",
             "Flags": 83659,
             "CFTAmount": "1000",
             "LockedAmount": "0"
           }
        ],
        "validated": true
    }
}
```

| Field Name        | JSON Type |
|-------------------|:---------:|
| `cfts`   | `array`   |

An array of CFToken objects owned by the specified account. Includes all fields in the underlying object.

| Field Name        | JSON Type |
|-------------------|:---------:|
| `marker`          | `string`  |

Used to continue querying where we left off when paginating. Omitted if there are no more entries after this result.

#### 1.6.0.3 `cft_holders`
For a given CFTokenIssuanceID and ledger sequence, `cft_holders` will return all holders of that CFT and their balance. This API is likely return very large data sets, so users should expect to implement paging via the `marker` field.

##### 1.6.0.3.1 Request fields

```json
{
  "command": "cft_holders",
  "cft_id": "00070C4495F14B0E44F78A264E41713C64B5F89242540EE255534400000000000000",
  "ledger_index": "validated"
}
```

| Field Name        | Required?             | JSON Type |
|-------------------|:---------------------:|:---------:|
| `cft_id`          |:heavy_check_mark:     | `string`  |

Indicates the CFTokenIssuance we wish to query.

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

Specify a limit to the number of CFTs returned.

##### 1.6.0.3.2 Response fields

```json
{
    "id": 5,
    "status": "success",
    "type": "response",
    "result": {
        "cft_id": "00070C4495F14B0E44F78A264E41713C64B5F89242540EE255534400000000000000",
        "cft_holders": {
          "rf1BiGeXwwQoi8Z2ueFYTEXSwuJYfV2Jpn": {
             "CFTokenIssuanceID": "00070C4495F14B0E44F78A264E41713C64B5F89242540EE255534400000000000000",
             "Flags": 83659,
             "CFTAmount": "1000",
             "LockedAmount": "0"
          }
        },
        "validated": true
    }
}
```

| Field Name        | JSON Type |
|-------------------|:---------:|
| `cft_id`          | `string`  |

Indicates the CFTokenIssuance we queried.

| Field Name        | JSON Type |
|-------------------|:---------:|
| `cft_holders`   | `object`   |

A JSON object representing a dictionary of accounts to CFToken objects. Includes all fields in the underlying CFToken object.

| Field Name        | JSON Type |
|-------------------|:---------:|
| `marker`          | `string`  |

Used to continue querying where we left off when paginating. Omitted if there are no more entries after this result.

# 2. Appendices

## 2.1 Appendix: FAQs

### 2.1.1. Are CFTs different from Trustlines?

Yes, CFTs are different from Trustlines. Read more in [section 1.1.2](#112-assumptions).

That said, there is some overlap in functionality between the two. For example, both CFTs and Trustlines can be used to issue a stablecoin. However, the original intent behind CFTs and Trustlines is subtly different, which impacts the on-ledger design of each. For clarity, Trustlines were invented primarily to service the idea of "community credit" and also to enhance liquidity on the ledger by making the same types of currency fungible amongst differing issuers (see [rippling](https://xrpl.org/rippling.html#rippling) for an example of each). CFTs, on the other hand, have three primary design motivations that are subtly different from Trustlines: (1) to enable tokenization using as little space (in bytes) on ledger as possible; (2) to eliminate floating point numbers and floating point math from the tokenization primitive; and (3) to make payment implementation simpler by, for example, removing [rippling](https://xrpl.org/rippling.html#rippling) and allowing CFT usage in places like [escrows](https://xrpl.org/escrow.html#escrow) or [payment channels](https://xrpl.org/payment-channels.html) in more natural ways.

### 2.1.2. Are CFTs meant to replace Trustlines?

No, replacing Trustlines is not the intent behind CFTs. Instead, it's likely that CFTs and Trustline can and will coexist because they enable subtly different use-cases (see [FAQ 4.1](#41-are-cfts-different-from-trustlines), in particular the part about "rippling.").

### 2.1.3 Instead of CFTs, why not just make Trustlines smaller/better?

While it's true there are some proposals to make Trustlines more efficient (e.g., [optimize Trustline storage](https://github.com/XRPLF/rippled/issues/3866) and even (eliminate Custom Math)[https://github.com/XRPLF/rippled/issues/4120) from Trustlines), both of these are reasonably large changes that would change important aspect of the RippleState implementation. Any time we make changes like this, the risk is that these changes impact existing functionality in potentially unforeseen ways. The choice to build and implement CFT is ultimately a choice that balances this risk/reward tradeoff towards introducing somethign new to avoid breaking any existing functionality.

### 2.1.4. Are CFTs targeted for Mainnet or a Sidechain?

This is still being considered and debated, but is ultimately up to Validators to decide. On the one hand, CFTs on Mainnet would enable some new tokenization use-cases that could be problematic if Trustlines were to be used (see [FAQ 2.1.7](#217-an-early-draft-of-this-cft-proposal-stored-cftokens-in-a-paging-structure-similar-to-that-used-by-nfts-why-was-that-design-abandoned) for more details). On the other hand, adding CFTs introduces a new payment type into the payment engine, which complicates both the implementation of rippled itself, and XRPL tooling. 

In any event, we will first preview CFTs in a CFT-Devnet, and depending on what we learn there, revisit this issue then.

### 2.1.5. Will CFTs be encoded into an STAmount, or is a new C++ object type required?

CFTs will be able to be encoded in an `STAmount`. See [this gist](https://gist.github.com/sappenin/2c923bb249d4e9dd153e2e5f32f96d92) for more details.

### 2.1.6. Is there a limit to the number of `CFTokenIssuance` or `CFToken` objects that a single account can hold?

Practically speaking, no. The number of CFToken objects or CFTokenIssuance object that any account can hold is limited by the number of objects that can be stored in an owner directory, which is a very large number.

### 2.1.7. An early draft of this CFT proposal stored `CFToken` objects in a paging structure similar to that used by NFTs. Why was that design abandoned?

The original design was optimized for on-ledger space savings, but it came with a tradeoff of increased complexity, both in terms of this specification and the implementation. Another consideration is the datapoint that many NFT developers struggled with the mechanism used to identify NFTs, some of which is a result of the NFT paging structure.

After analyzing on-ledger space requirements for (a) Trustlines, (b) `CFTokenPages`, (c) and simply storing `CFToken` objects in an Owner Directory, we determined that for a typical user (i.e., one holding ~10 different CFTs), the overall space required by the simpler design strikes a nice balance between the more complicated design and Trustlines. For example, the simpler design regquires ~3.2x more bytes on-ledger than  more complicated design. However, the simpler design requires about 30% fewer bytes on-ledger than Trustlines.

With all that said, this decision is still open for debate. For example, in early 2024 the Ripple team plans to perform limit testing around Trustlines and the simpler CFT design to see how increased numbers of both types of ledger objects affect ledger performance. Once that data is complete, we'll likely revisit this design choice to either validate it or change it.

### 2.1.8. Why is there no `CFTRedeem` Transaction?

This is because holders of a CFT can use a normal payment transaction to send CFT back to the issuer, thus "redeeming" it and removing it from circulation. Note that one consequence of this design choice is that CFT issuer accounts may not also hold `CFToken` objects because, if the issuer could do such a thing, it would be ambiguous where incoming CFT payments should go (i.e., should that payment be a redemption and reduce the total amount of outstanding issuance, or should that payment go into an issuer's `CFToken` amount, and still be considered as "in circulation." For simplicity, we chose the former design, restricting CFT issuers from having `CFToken` objects at all.

### 2.1.9. Why can't CFToken Issuers also hold their own balances of CFT in a CFToken object?

See the question above. This design also helps enforce a security best practice where an issuing account should not also be used as an issuer's transactional account. Instead, any issuer should use a different XRPL account for non-issuance activity of their CFTs.

### 2.1.10. Why not use the `DepositPreauth` transaction for Authorized CFT Functionality?

For CFTokenIssuances that have the `lsfCFTRequireAuth` flag set, it is envisioned that a [DepositPreauth](https://xrpl.org/depositpreauth.html) transaction could be used with minor adaptations to distinguish between pre-authorized trust lines and pre-authorized CFTs. Alternatively, we might consider `deposit_preauth` objects might apply to both, under the assumption that a single issuer restricting trust lines will want to make the same restrictions around CFTs emanating from the same issuer account.

That said, this design is still TBD.

## 2.2. Appendix: Outstanding Issues

This section describes any outstanding or debatable issues that have not yet been resolved in this proposal.

### 2.2.1. `CFTokenIssuanceID` options

There are a variety of ways to construct a `CFTokenIssuanceID`. This section outlines three that are currently up for debate:

#### 2.2.1.1. Hash issuer address and currency code

This is the conventional way of constructing an identifier, as the token holder can directly submit the transaction after knowing the issuer and the currency they want to use. However, if this is implemented, it means that after the issuer destroys an entire `CFTokenIssuance` (i.e., once nobody else holds any of it), the issuer can re-issue the same token with the same currency, resulting in the same `CFTokenIssuanceID`. This behavior can be misleading to token holders who have held onto the first iteration of the token rather than the re-issued one (since both iterations have the same `CFTokenIssuanceID`). In real world use cases(especially finance), after a fungible token is burned, it should not be possible to re-create it, and absolutely not with the same identifier.

#### 2.2.1.2. Option A: Currency array and limit the number of CFT issuances

This approach still constructs `CFTokenIssuanceID` by hashing the issuer address and currency code. But in an effort to solve the re-creatable `CFTokenIssuanceID` problem, the issuer stores an array of CFT currency codes that have been issued out. In this way, every time the issuer issues a new CFT, the ledger checks whether the currency code has already be used, and if so, the transaction fails. However, the problem with this approach is that the ledger would need to iterate through the currency array everytime the account attempts to issue a CFT, which would be unsustainable if the issuer can issue up to an unbounded number of CFTs. Hence, we impose a limit on the total number of CFTs that an account can issue(proposed limit is 32 CFTs).

But, this approach is not very clean in solving the problem, and there is a limit on the number of CFTs that the account can issue, which is not ideal since we would want the issuer to issue as many CFTs as they want.

#### 2.2.1.3. Option B: Construct CFTokenIssuance without currency code (current approach)

We realized that the problem with re-creatable CFTs is due to the account/currency pair where the currency can be re-used many times after the CFT has been burned. To solve this problem, the `CFTokenIssuanceID` is now constructed from two parameters: the issuer address and transaction sequence. Since the transaction sequence is an increasing index, `CFTokenIssuanceID` will never be re-created. And thus, the AssetCode/currency can be made as an optional field that's going to be used purely for metadata purposes.

Although using this approach would mean that CFT payment transactions would no longer involve the currency code, making it inconvenient for users, it is still an acceptable compromise. The ledger already has something similar - NFToken has a random identifier and uses clio for API services.

### 2.2.2. Allow-Listing

In certain use cases, issuers may want the option to only allow specific accounts to hold their CFT, similar to how authorization works for TrustLines.

#### 2.2.2.1. Without Allow-Listing

Let's first explore how the flow looks like without allow-listing:

1. Alice holds a CFT with asset-code `USD`.
2. Bob wants to hold it, and therefore submits a `CFTokenAuthorize` transaction specifying the `CFTokenIssuanceID`, and does not specify any flag. This will create a `CFToken` object with zero balance, and potentially taking up extra reserve.
3. Bob can now receive and send payments from/to anyone using `USD`.
4. Bob no longer wants to use the CFT, meaning that he needs to return his entire amount of `USD` back to the issuer through a `Payment` transaction. Resulting in a zero-balance `CFToken` object again.
5. Bob then submits a `CFTokenAuthorize` transaction that has set the `tfCFTUnauthorize` flag, which will successfully delete `CFToken` object.

#### 2.2.2.2. With Allow-Listing

The issuer needs to enable allow-listing for the CFT by setting the `lsfCFTRequireAuth` on the `CFTokenIssuance`.

With allow-listing, there needs to be a bidirectional trust between the holder and the issuer. Let's explore the flow and compare the difference with above:

1. Alice has a CFT of currency `USD` (same as above)
2. Bob wants to hold it, and therefore submits a `CFTokenAuthorize` transaction specifying the `CFTokenIssuanceID`, and does not specify any flag. This will create a `CFToken` object with zero balance, and potentially taking up extra reserve. (same as above)
**However at this point, Bob still does not have the permission to use `USD`!**
3. Alice needs to send a `CFTokenAuthorize` transaction specifying Bob's address in the `CFTokenHolder` field, and if successful, it will set the `lsfCFTAuthorized` flag on Bob's `CFToken` object. This will now finally enable Bob to use `USD`.
4. Same as step 4 above
6. 5. Same as step 5 above

**It is important to note that the holder always must first submit the `CFTokenAuthorize` transaction before the issuer.** This means that in the example above, steps 2 and 3 cannot be reversed where Alice submits the `CFTokenAuthorize` before Bob.

Issuer also has the ability to de-authorize a holder. In that case, if the holder still has outstanding funds, then it's the issuer's responsibility to clawback these funds.

### 2.2.3. `CFTokenNode` Directories?

The original intent of the `CFTokenNode` object is that it would be a sort of "directory" (i.e., an index) that stores a list of `CFTokenID` values (each 32 bytes) that exist for a single `CFTokenIssuance`. This would allow rippled to contain an RPC endpoint that could return a paged collection of `CFToken` objects for a given issuance, or somethign similar like an RPC called `cft_holder_balances`. In theory, this could also enable rippled to operate a sort of "clean-up" operation that could remove dangling CFTokens that still live on a ledger after a corresponding `CFTokenIssuance` has been deleted (and thus return ledger reserves back to token holders).

#### 2.2.3.1 Should We Have `CFTokenNode` Directories?

While the introduction of a `CFTokenNode` server a particular use-case, we should debate further if we actually want to be solving that use-case, both for CFTs and more generally. For example, some in the community believe that many (most?) RPCs should be removed from rippled itself, especially ones that exist primarily for indexing purposes. That is, we should avoid storing data in the ledger that is not used by actual transactors, but instead only exists to service external processes via RPC. For example, we might consider moving these RPCs into Clio or some other service so that data indexing and more expensive indexing responsibility can be removed from the ledger itself, and thus removed as a burden for certain infrastructure operators. 

On the topic of removing dangling `CFTokenObjects`, this solution would introduce a background thread into rippled that might have unintended consequences on actual node operation. In addition, the pre-exising way for ledger cleanup to occur is for account holders to issue delete transactions; for example, we've seen very many of these types of transactions deleting both trustlines and accounts. 

#### 2.2.3.1 How Should We Design `CFTokenNode` Directories?

The proposed design of a new "CFT-only" directory structure introduces a new pattern that should be considered more. For example, in the XRP Ledger there are currently two types of "Directory" -- an "Owner Directory" and an "Offer Directory." The proposal of a new type of CFT directory suggests that we create a new type of owner-less directory specifically for CFTs (similar to `NFTokenOfferNode`). This directory would indeed be similar to an "Offer Directory" in the sense that there would be no owner; but the design otherwise diverges from that concept in the sense that these new CFT directories would not be aimed at DEX or exchange operations as is the case for DEX offers and `NFTokenOfferNode` objects.

As an alternative design, we might also (and instead) consider a new type of "Owner Directory" for CFTs that are (1) owned by the issuer yet (2) only holds `CFTokenID` values. In this way, this new type of directory would be more similar to an "Owner Directory" (because there's an owner), yet different because only `CFTokenID` values would be stored in this type of directory.

Both proposal entail a divergence in architecture from today, so each should be debated and discussed further to explore tradeoffs and impliciations.

## 2.3. Appendix: Supplemental Information

### 2.3.1 Current Trust line Storage Requirements

As described in issue [#3866](https://github.com/ripple/rippled/issues/3866#issue-919201191), the size of a [RippleState](https://xrpl.org/ripplestate.html#ripplestate) object is anywhere from 234 to 250 bytes plus a minimum of 32 bytes for object owner tracking, described in more detail here:

```
FIELD NAME          SIZE IN BITS
================================
LedgerEntryType               16
Flags                         32 ("optional" but present in > 99.99% of cases)
Balance                      384 (160–224 wasted)
LowLimit                     384 (160–224 wasted)
HighLimit                    384 (160–224 wasted)
PreviousTxnID                256
PreviousTxnLgrSeq             32
LowNode                       64 (often has value 0)
HighNode                      64 (often has value 0)
--------------------------------
REQUIRED SUBTOTAL:          1872 (234 bytes)

OPTIONAL FIELDS
--------------------------------
LowQualityIn                  32
LowQualityOut                 32
HighQualityIn                 32
HighQualityOut                32
--------------------------------
MAXIMUM TOTAL SIZE:         2000 (250 bytes)
```

TODO: Validate these numbers as they may be slightly low for trust lines. For example, in addition to the above data, trust lines require two directory entries for low/high nodes that get created for each trust line (i.e., for each RippleState object). This creates two root objects, each 98 bytes, adding 196 bytes in total per unique issuer/holder. Conversely, for CFTs, the page structure allows for up to 32 issuances to be held by a single token holder while only incurring around 102 bytes for a CFTokenPage. Thus, every time an account wants to hold a new token, the current Trustline implementation would require _at least_ 430 bytes every time. If we imagine a single account holding 20 tokens, CFTs would require ~1040 bytes, whereas trust lines would require ~8,600 bytes!