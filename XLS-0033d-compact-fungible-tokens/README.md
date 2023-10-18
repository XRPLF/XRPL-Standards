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
4. **No TrustSet Transactions**. CFTs may be held by any account, and therefore do not require any sort of [TrustSet](https://xrpl.org/trustset.html#trustset) transaction in order to enable holding a CFT. However, in order to disallow an arbitrary CFT sender from consuming recipient account reserves, payment _senders_ have to commit 1 incremental reserve (i.e., currently 2 XRP) when sending a token to any recipient who doesn't currently hold any CFTs (or to any recipient where sending the token would incur a new CFTokenPage). 
5. **No Rippling**. Unlike some existing capabilities of the ledger, CFTs are not eligible for [rippling](https://xrpl.org/rippling.html#rippling), and thus do not have any configurability settings related to that functionality.

### 1.1.3 Release Timeline and Scope

XLS-33 will only cover the addition of the new data structures for CFTs, integration with the **`Payment`** transaction such that users can make CFT to CFT payments (IE no cross currency payments), and several other incidental additions like new requirements for account deletion (discussed below). Later amendments will integrate CFTs with other features of the XRPL such as the DEX.

## 1.2. Creating Compact Fungible Tokens

### 1.2.1. On-Ledger Data Structures

We propose two new objects and one new ledger structure:

1. A **`CFTokenIssuance`** is a new object that describes a fungible token issuance created by an issuer.
1. A **`CFToken`** is a new object that describes a single account's holdings of an issued token.
1. A **`CFTokenPage`** is a ledger structure that contains a set of **`CFToken`** objects owned by the same token holder.

#### 1.2.1.1. The **`CFTokenIssuance`** object

The **`CFTokenIssuance`** object represents a single CFT issuance and holds data associated with the issuance itself. Token issuances are created using the **`CFTokenIssuanceCreate`** transaction and can, optionally, be destroyed by the **`CFTokenIssuanceDestroy`** transaction.

##### 1.2.1.1.1. **`CFTokenIssuance`** Ledger Identifier
The ID of an CFTokenIssuance object, a.k.a `CFTokenIssuanceID` is the result of SHA512-Half of the following values, concatenated in order:

* The CFTokenIssuance space key (0x007E).
* The AccountID of the issuer.
* The AssetCode of the issuance.

##### 1.2.1.1.2. Fields

**`CFTokenIssuance`** objects are stored in the ledger and tracked in an [Owner Directory](https://xrpl.org/directorynode.html) owned by the issuer. Issuances have the following required and optional fields:

| Field Name          | Required?          | JSON Type | Internal Type |
| ------------------- |--------------------|-----------|---------------|
| `LedgerEntryType`   | :heavy_check_mark: | `number`  | `UINT16`      |
| `Flags`             | :heavy_check_mark: | `number`  | `UINT32`      |
| `Issuer`            | :heavy_check_mark: | `string`  | `ACCOUNTID`   |
| `AssetCode`         | :heavy_check_mark: | `string`  | `UINT160`     |
| `AssetScale`        | (default)          | `number`  | `UINT8`       |
| `MaximumAmount`     | :heavy_check_mark: | `string`  | `UINT64`      |
| `OutstandingAmount` | :heavy_check_mark: | `string`  | `UINT64`      |
| `LockedAmount`      | ️(default)          | `string`  | `UINT64`      |
| `TransferFee`       | ️(default)          | `number`  | `UINT16`      |
| `CFTokenMetadata`   |                    | `string`  | `BLOB`        |
| `OwnerNode`         | (default)          | `number`  | `UINT64`      |

###### 1.2.1.1.2.1. `LedgerEntryType`

The value 0x007E, mapped to the string `CFTokenIssuance`, indicates that this object describes a Compact Fungible Token (CFT).

###### 1.2.1.1.2.2. `Flags`

A set of flags indicating properties or other options associated with this **`CFTokenIssuance`** object. The type specific flags proposed  are:

| Flag Name         | Flag Value | Description |
|-------------------|------------|-------------|
| `lsfFrozen`                | ️`0x0001`  | If set, indicates that all balances should be frozen. |
| `lsfCannotFreezeBalances`  | ️`0x0002`  | If set, indicates that _individual_ balances cannot be frozen. This has no effect on the issuers ability to globally freeze, yet provides token holders with more assurance that individual token holders will not be frozen on an ad-hoc basis, but instead all tokens will only ever be frozen or unfrozen together. |
| `lsfRequiresAuthorization` | ️`0x0004`  | If set, indicates that _individual_ holders must be authorized. This enables issuers to limit who can hold their assets.  |
| `lsfCanEscrow`             | `0x0008`  | If set, indicates that _individual_ holders can place their balances into an escrow. |
| `lsfCanTrade`              | `0x0010`  | If set, indicates that _individual_ holders can trade their balances using the XRP Ledger DEX or AMM.
| `lsfTransferable`          | ️`0x0020`  | If set, indicates that tokens held by non-issuers may be transferred to other accounts. If not set, indicates that tokens held by non-issuers may not be transferred except back to the issuer; this enables use-cases like store credit. |
| `lsfAllowClawback`         | ️`0x0040`  | If set, indicates that the issuer may use the `Clawback` transaction to clawback value from _individual_ holders.|

With the exception of the `lsfFrozen` flag, which can be mutated via the `**CFTokenIssuanceSet**` transactions, these flags are **immutable**: they can only be set during the **`CFTokenIssuanceCreate`** transaction and cannot be changed later.

###### 1.2.1.1.2.3. `Issuer`

The address of the account that controls both the issuance amounts and characteristics of a particular fungible token.

###### 1.2.1.1.2.4. `AssetCode`

A 160-bit blob of data. We recommend using only upper-case ASCII letters, ASCII digits 0 through 9, the dot (`.`) character, and the dash (`-`) character. Dots and dashes should never be the first character of an asset code, and should not be repeated sequentially.

While it is possible to store any arbitrary data in this field, implementations that detect the above recommended character conformance can and should display them as human-readable text, allowing issuers to support well-known ISO-4207 currency codes in addition to custom codes. This also helps prevents spoofing attacks where a [homoglyph](https://en.wikipedia.org/wiki/Homoglyph) might be used to trick a person into using the wrong asset code.

###### 1.2.1.1.2.5. `AssetScale`

An asset scale is the difference, in orders of magnitude, between a standard unit and a corresponding fractional unit. More formally, the asset scale is a non-negative integer (0, 1, 2, …) such that one standard unit equals 10^(-scale) of a corresponding fractional unit. If the fractional unit equals the standard unit, then the asset scale is 0.

###### 1.2.1.1.2.6. `MaximumAmount`

This value is an unsigned number that specifies the maximum number of CFTs that can be distributed to non-issuing accounts (i.e., `minted`). For issuances that do not have a maximum limit, this value should be set to 0xFFFFFFFFFFFFFFFF.

###### 1.2.1.1.2.7. `OutstandingAmount`

Specifies the sum of all token amounts that have been minted to all token holders. This value can be stored on ledger as a `default` type so that when its value is 0, it takes up less space on ledger. This value is increased whenever an issuer pays CFTs to a non-issuer account, and decreased whenever a non-issuer pays CFTs into the issuing account.

###### 1.2.1.1.2.8. `TransferFee`

This value specifies the fee, in tenths of a [basis point](https://en.wikipedia.org/wiki/Basis_point), charged by the issuer for secondary sales of the token, if such sales are allowed at all. Valid values for this field are between 0 and 50,000 inclusive. A value of 1 is equivalent to 1/10 of a basis point or 0.001%, allowing transfer rates between 0% and 50%. A `TransferFee` of 50,000 corresponds to 50%. The default value for this field is 0.

###### 1.2.1.1.2.9. `OwnerNode`

Identifies the page in the owner's directory where this item is referenced.

##### 1.2.1.1.2. Example **`CFTokenIssuance`** JSON

 ```json
 {
     "LedgerEntryType": "CFTokenIssuance",
     "Flags": 131072,
     "Issuer": "rsA2LpzuawewSBQXkiju3YQTMzW13pAAdW",
     "AssetCode": "0000000000000000000000005553440000000000",
     "AssetScale": "2",
     "MaximumAmount": "100000000",
     "OutstandingAmount": "5",
     "TransferFee": 50000,     
     "CFTokenMetadata": "",
     "OwnerNode": "74"
 }
 ```
 
##### 1.2.1.1.3. How do **`CFTokenIssuance`** objects work?

Any account may issue up to 32 Compact Fungible Tokens, but each issuance must have a different **`AssetCode`**.

###### 1.2.1.1.3.1. Searching for a **`CFTokenIssuance`** object

CFT Issuances are uniquely identified by a combination of a type-specific prefix, the isser address and an asset code. To locate a specific **`CFTokenIssuance`**, the first step is to locate the owner directory for the issuer. Then, find the directory that holds `CFTokenIssuance` ledger objects and iterate through each entry to find the instance with the desired **`AssetCode`**. If that entry does not exist then the **`CFTokenIssuance`** does not exist for the given account.

###### 1.2.1.1.3.2. Adding a **`CFTokenIssuance`** object

A **`CFTokenIssuance`** object can be added by using the same approach to find the **`CFTokenIssuance`**, and adding it to that directory. If, after addition, the number of CFTs in the directory would exceed 32, then the operation must fail.

###### 1.2.1.1.3.3. Removing a **`CFTokenIssuance`** object

A **`CFTokenIssuance`** can be removed using the same approach, but only if the **`CurMintedAmount`** is equal to 0.

###### 1.2.1.1.3.4. Reserve for **`CFTokenIssuance`** object

Each **`CFTokenIssuance`** costs an incremental reserve to the owner account. This specification allows up to 32 **`CFTokenIssuance`** entries per account.

#### 1.2.1.2. The **`CFToken`** object
The **`CFToken`** object represents an amount of a token held by an account that is **not** the token issuer. CFTs are acquired via ordinary Payment or DEX transactions, and can optionally be redeemed or exchanged using these same types of transactions.

##### 1.2.1.2.1 Fields
A **`CFToken`** object can have the following required and optional fields. Notice that, unlike other objects, no field is needed to identify the object type or current owner of the object, because CFT holdings are grouped into pages that implicitly define the object type and identify the holder.

| Field Name            | Required?          | JSON Type | Internal Type |
| --------------------- |--------------------|-----------|---------------|
| `CFTokenIssuanceID`   | :heavy_check_mark: |  `string` | `UINT256`     |
| `Amount`              | :heavy_check_mark: |  `string` | `UINT64`      |
| `LockedAmount`        | default            |  `string` | `UINT64`      |
| `Flags`               | default            |  `number` | `UINT32`      |

###### 1.2.1.2.1.1. `CFTokenIssuanceID`

The `CFTokenIssuance` identifier.

###### 1.2.1.2.1.2. `Amount`

This value specifies a positive amount of tokens currently held by the owner. Valid values for this field are between 0x0 and 0xFFFFFFFFFFFFFFFF.

###### 1.2.1.2.1.3. `LockedAmount`

This value specifies a positive amount of tokens that are currently held in a token holder's account but that are unavailable to be used by the token holder. Locked tokens might, for example, represent value currently being held in escrow, or value that is otherwise inaccessible to the token holder for some other reason, such as an account freeze. 

This value is stored as a `default` value such that it's initial value is `0`, in order to save space on the ledger for a an empty CFT holding.

###### 1.2.1.2.1.4. `Flags`

A set of flags indicating properties or other options associated with this **`CFTokenIssuance`** object. The type specific flags proposed  are:

| Flag Name         | Flag Value | Description                                                             |
|-------------------|------------|-------------------------------------------------------------------------|
| `lsfFrozen`       | `0x0001`   | If set, indicates that the CFT owned by this account is currently frozen and cannot be used in any XRP transactions other than sending value back to the issuer. When this flag is set, the `LockedAmount` must equal the `Amount` value. |

##### 1.2.1.2.2. Example CFToken JSON

 ```json
 {
     "TokenID": "00070C4495F14B0E44F78A264E41713C64B5F89242540EE255534400000000000000",
     "Flags": 0,
     "Amount": "100000000",
     "LockedAmount": "0"
 }
 ```

#### 1.2.1.3. The **`CFTokenPage`** ledger entry

This object represents a collection of **`CFToken`** objects owned by the same account. It is important to note that the **`CFToken`** objects themselves reside within this page, instead of in a dedicated object entry in the `SHAMap`. An account can have multiple **`CFTokenPage`** ledger objects, which form a doubly-linked list (DLL).

In the interest of minimizing the size of a page and optimizing storage, the `Owner` field is not present since it is encoded as part of the object's ledger identifier (more details in the **`CFTokenPageID`** discussion below).

##### 1.2.1.3.1 Fields

A **`CFTokenPage`** object may have the following required and optional fields:

| Field Name          | Required? | JSON Type | Internal Type |
| ------------------- |-----------| --------- |---------------|
| `LedgerEntryType`   | ✔️         | `string`  | `UINT16`      |
| `PreviousPageMin`   | ️          | `string`  | `UINT256`     |
| `NextPageMin`       | ️          | `string`  | `UINT256`     |
| `PreviousTxnID`     | ️          | `string`  | `HASH256`     |
| `PreviousTxnLgrSeq` | ️          | `number`  | `UINT32`      |
| `CFTokens`          | ️✔         | `object`   | `TOKEN`      |

###### 1.2.1.3.1.1. `**LedgerEntryType**` 

Identifies the type of ledger object. This proposal recommends the value `0x007F` as the reserved ledger entry type.

###### 1.2.1.3.1.2. `**PreviousPageMin**` 

The locator of the previous page, if any. Details about this field and how it should be used are outlined below, after the construction of the **`CFTokenPageID`** is explained.

###### 1.2.1.3.1.3. `**NextPageMin**` 

The locator of the next page, if any. Details about this field and how it should be used are outlined below, after the construction of the **`CFTokenPageID`** is explained.

###### 1.2.1.3.1.4. `**PreviousTxnID**` 

Identifies the transaction ID of the transaction that most recently modified this **`CFTokenPage`** object.

###### 1.2.1.3.1.5. `**PreviousTxnLgrSeq**` 

The sequence of the ledger that contains the transaction that most recently modified this **`CFTokenPage`** object.

###### 1.2.1.3.1.6. `**CFTokens**` 

The collection of **`CFToken`** objects contained in this **`CFTokenPage`** object. This specification places an upper bound of 32 **`CFToken`** objects per page. Objects should be stored in sorted order, from low to high with the low order 96 bits of the `TokenID` used as the sorting parameter.

##### 1.2.1.3.2. CFTokenPage ID Format

Unlike other object identifiers on the XRP Ledger, which are derived by hashing a collection of data using `SHA512-Half`, **`CFTokenPage`** identifiers are constructed so as to specfically allow for the adoption of a more efficient paging structure, designed to enable user accounts to efficiently hold many CFTs at the same time.

To that end, a unique CFTokenPage ID (a.k.a., `CFTokenPageID`) is derived by concatenating a 196-bit value that uniquely identifies a particular account's holdings of CFT, followed by a 64-bit value that uniquely identifies a particular CFT issuance. Using this construction enables efficient lookups of individual `CFTokenPage` objects without requiring iteration of the doubly-linked list of all CFTokenPages.

More formally, we assume:

- The function `high196(x)` returns the "high" 196 bits of a 256-bit value.
- The function `low64(x)` returns the "low" 64-bits of a 256-bit value. 
- A `CFTokenIssuanceID` uniqely identifies a CFT Issuance as defined above in ["CFTokenIssuance Ledger Identifier"].
- A `CFTokenHolderID` uniquely identifies a holder of some amount of CFT (as opposed to other token types such as an NFT) and is defined as the result of SHA512-Half of the following values, concatenated in order:
  - The `CFTokenIssuance` ledger identifier key (0x007E).
  - The `AccountID` of the CFT holder.

Therefore:

- Let `CFTokenPageID` equal `high196(CFTokenHolderId)` concatenated with `low64(CFTokenIssuanceId)`.
- Let `CFTokenIssuanceID` `A` only be included in a page with `CFTokenPageId` `B` if and only if `low64(A) >= low64(B)`.

This scheme is similar to the existing scheme for organizing `NFToken` objects into `NFTokenPage`s.

##### 1.2.1.3.3. Example CFTokenPage JSON

 ```json
 {
     "LedgerEntryType": "CFTokenPage",
     "PreviousTokenPage": "598EDFD7CF73460FB8C695d6a9397E907378C8A841F7204C793DCBEF5406",
     "PreviousTokenNext": "598EDFD7CF73460FB8C695d6a9397E9073781BA3B78198904F659AAA252A",
     "PreviousTxnID": "95C8761B22894E328646F7A70035E9DFBECC90EDD83E43B7B973F626D21A0822",
     "PreviousTxnLgrSeq": 42891441,
     "CFTokens": {
             {
                 "CFTokenID": "00070C4495F14B0E44F78A264E41713C64B5F89242540EE255534400000000000000",
                 "Amount": 50000
             },
             ...
      }
 }
 ```
 
##### 1.2.1.3.4. How do **`CFTokenPage`** objects work?

The page within which a **`CFToken`** entry is stored will be formed as described above. This is needed to find the correct starting point in the doubly-linked list of **`CFTokenPage`** objects if that list is large. This is because it is inefficient to have to traverse the list from the beginning if an account holds thousands of **`CFToken`** objects in hundreds of **`CFTokenPage`** objects.

###### 1.2.1.3.4.1. Searching a **`CFToken`** object

To search for a specific **`CFToken`**, the first step is to locate the **`CFTokenPage`**, if any, that should contain that **`CFToken`**. For that do the following:

Compute the **`CFTokenPageID`** using the account of the owner and the **`CFTokenIssuanceID`** of the token, as described above. Then search for the ledger entry whose identifier is less than or equal to that value. If that entry does not exist or is not a **`CFTokenPage`**, the **`CFToken`** is not held by the given account.

###### 1.2.1.3.4.2. Adding a **`CFToken`** object

A **`CFToken`** object can be added by using the same approach to find the **`CFTokenPage`** it should be in and adding it to that page. If after addition the page overflows, find the `next` and `previous` pages (if any) and balance those three pages, inserting a new page as/if needed.

###### 1.2.1.3.4.2. Removing a **`CFToken`** object

A **`CFToken`** can be removed by using the same approach. If the number of **`CFToken`** in the page goes below a certain threshhold, an attempt will be made to consolidate the page with a `previous` or subsequent page and recover the reserve.

###### 1.2.1.3.4.3. Reserve for **`CFTokenPage`** object

Each **`CFTokenPage`** costs an incremental reserve to the owner account. This specification allows up to 32 **`CFToken`** entries per page, which means that for accounts that hold multiple CFTs the _effective_ reserve cost per Fungible Token can be as low as _R_/32 where _R_ is the incremental reserve.

## 1.3 Transactions

This proposal introduces several new transactions to allow for the creation and deletion of CFT issuances. Likewise, this proposal introduce several new transactions for minting and redeeming discrete instances of CFTs. All transactions introduced by this proposal incorporate the [common transaction fields](https://xrpl.org/transaction-common-fields.html) that are shared by all transactions. Common fields are not documented in this proposal unless needed because this proposal introduces new possible values for such fields.

### 1.3.1 Transactions for Creating and Destroying Compact Fungible Token Issuances on XRPL
We define three transactions related to CFT Issuances: **`CFTokenIssuanceCreate`** and **`CFTokenIssuanceDestroy`** and  **`CFTokenIssuanceSet`** for minting, destroying, and updating CFT _Issuances_ respectively on XRPL.

#### 1.3.1.1 The **`CFTokenIssuanceCreate`** transaction
The **`CFTokenIssuanceCreate`** transaction creates an **`CFTokenIssuance`** object and adds it to the relevant directory node of the `creator`. This transaction is the only opportunity an `issuer` has to specify any token fields that are defined as immutable (e.g., CFT Flags).

If the transaction is successful, the newly created token will be owned by the account (the `creator` account) which executed the transaction.

##### 1.3.1.1.1 Transaction-specific Fields
| Field Name         | Required? | JSON Type | Internal Type |
| ------------------ | --------- | --------- |---------------|
| `TransactionType`  | ️ ✔        | `object`  | `UINT16`      |

Indicates the new transaction type **`CFTokenIssuanceCreate`**. The integer value is `25 (TODO)`.

| Field Name         | Required? | JSON Type | Internal Type |
| ------------------ | --------- | --------- |---------------|
| `AssetCode`        | ️ ✔        | `string`  | `BLOB`        |

A 160-bit blob of data. It is reccommended to use only upper-case ASCII letters in addition to the ASCII digits 0 through 9. While it's possible to store any arbitrary data in this field, implementations that detect the above reccommended characters should display them as ASCII for human readability. This also helps prevents spoofing attacks where a [homoglyph](https://en.wikipedia.org/wiki/Homoglyph) might be used to trick a person into using the wrong asset code.

| Field Name         | Required?    | JSON Type | Internal Type |
| ------------------ | ------------ | --------- |---------------|
| `AssetScale`       | ️ ✔           | `number`  | `UINT8`       |

An asset scale is the difference, in orders of magnitude, between a standard unit and a corresponding fractional unit. More formally, the asset scale is a non-negative integer (0, 1, 2, …) such that one standard unit equals 10^(-scale) of a corresponding fractional unit. If the fractional unit equals the standard unit, then the asset scale is 0.

| Field Name  | Required? | JSON Type | Internal Type |
| ----------- | --------- | --------- |---------------|
| `Flags`     | ️          | `number`  | `UINT16`      |

Specifies the flags for this transaction. In addition to the universal transaction flags that are applicable to all transactions (e.g., `tfFullyCanonicalSig`), the following transaction-specific flags are defined and used to set the appropriate fields in the Fungible Token:

| Flag Name         | Flag Value | Description |
|-------------------|------------|-------------|
| `lsfFrozen`                | ️`0x0001`  | If set, indicates that all balances should be frozen. |
| `lsfCannotFreezeBalances`  | ️`0x0002`  | If set, indicates that _individual_ balances cannot be frozen. This has no effect on the issuers ability to globally freeze. |
| `lsfRequiresAuthorization` | ️`0x0004`  | If set, indicates that _individual_ holders must be authorized. This enables issuers to limit who can hold their assets.  |
| `lsfCanEscrow`             | `0x0008`  | If set, indicates that _individual_ holders can place their balances into an escrow. |
| `lsfCanTrade`              | `0x0010`  | If set, indicates that _individual_ holders can trade their balances using the XRP Ledger DEX. |
| `lsfTransferable`          | ️`0x0020`  | If set, indicates that tokens may be transferred to other accounts that are not the issuer. |
| `lsfAllowClawback`         | ️`0x0040`  | If set, indicates that the issuer may use the `Clawback` transaction to clawback value from _individual_ holders.|

| Field Name    | Required? | JSON Type | Internal Type |
| ------------- | --------- | --------- | ------------- |
| `TransferFee` |           | `number`  | `UINT16`      | 

The value specifies the fee to charged by the issuer for secondary sales of the Token, if such sales are allowed. Valid values for this field are between 0 and 50,000 inclusive, allowing transfer rates of between 0.000% and 50.000% in increments of 0.001.

The field MUST NOT be present if the `tfTransferable` flag is not set. If it is, the transaction should fail and a fee should be claimed.

| Field Name      | Required?          | JSON Type | Internal Type |
| --------------- | ------------------ | --------- | ------------- |
| `MaximumAmount` | :heavy_check_mark: | `string`  | `UINT64`      | 

The maximum asset amount of this token that should ever be issued.

| Field Name        | Required?          | JSON Type | Internal Type |
| ------------------| ------------------ | --------- | ------------- |
| `CFTokenMetadata` | :heavy_check_mark: | `string`  | `BLOB`        | 

Arbitrary metadata about this issuance, in hex format. The limit for this field is 1024 bytes.

##### 1.3.1.1.2 Example **`CFTokenIssuanceCreate`** transaction

```json
{
  "TransactionType": "CFTokenIssuanceCreate",
  "Account": "rajgkBmMxmz161r8bWYH7CQAFZP5bA9oSG",
  "AssetCode": "1234567",
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
| `Account`       | :heavy_check_mark: | `string`  | `ACCOUNTID`   | 

An optional XRPL Address of an individual token holder balance to freeze/unfreeze. If omitted, this transaction will apply to all any accounts holding CFTs.

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
 
#### 1.3.3.1.1 CFTokenSet Flags
Transactions of the `CFTokenFreeze` type support additional values in the Flags field, as follows:

| Flag Name         | Flag Value | Description |
|-------------------|------------|-------------|
| `tfSetFreeze`     | ️`0x0001`  | If set, indicates that all CFT balances for this asset should be frozen. |
| `tfClearFreeze`   | ️`0x0002`  | If set, indicates that all CFT balances for this asset should be unfrozen. |

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
  "issuer": "rf1BiGeXwwQoi8Z2ueFYTEXSwuJYfV2Jpn",
  "cft_asset": "USD",
  "value": "1"
}
```

The idea behind this format is that it adds only one new subfield to the `amount` field, but still distinguishes between itself and Issued Currency amounts. Using the CFT ID directly would not allow us to easily find the underlying `CFTokenIssuance` object because we would still need the `issuer` to know where to look for it.

### 1.3.5 The **`AccountDelete`** Transaction
We propose no changes to the `AccountDelete` transaction in terms of structure. However, accounts that have `CFTokenIssuance`s may not be deleted. These accounts will need to destroy each of their `CFTokenIssuances` using `CFTokenIssuanceDestroy` first before being able to delete their account. Without this restriction (or a similar one), issuers could render CFT balances useless/unstable for any holders.

### 1.4.0 Details on Freezing CFTs
#### 1.4.0.1 Freezing individual balances
To freeze an individual balance of an individual CFT an issuer will submit the `CFTokenIssuanceSet` transaction, indicate the CFT and holder account that they wish to freeze, and set the `tfSetFreeze` flag. This operation will fail if::

* The CFT has the `lsfCannotFreezeBalances` flag set or,
* The CFT issuer has the `asfNoFreeze` flag set on their account

Issuers can unfreeze the balance by submitting another `CFTokenIssuanceSet` transaction with the `tfClearFreeze` flag set.

#### 1.4.0.2 Freezing entire CFTs
This operation works the same as above, except that the holder account is not specified in the `CFTokenIssuanceSet` transaction when freezing or unfreezing. This operation will fail if::

* The CFT issuer has the `asfNoFreeze` flag set on their account

Freezing an entire CFT without freezing other assets issued by an issuer is a new feature of CFTs.

#### 1.4.0.3 Freezing all CFTs and Trust Lines (Global Freeze)
When accounts enact a global freeze, which is currently used to freeze all trust lines, it will also freeze all CFTs issued by the account.

### 1.5.0 Details on Clawing-Back CFTs
To clawback funds from a CFT holder, the issuer must have specified that the CFT allows clawback by setting the `tfAllowClawback` flag when creating the CFT using the `CFTokenIssuanceCreate` transaction. Assuming a CFT was created with this flag set, clawbacks will be allowed using the `Clawback` transaction (more details to follow on how this transaction will change to accomodate the new values).

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
             "AssetCode": .....,
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
             "Amount": "1000",
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
             "Amount": "1000",
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


 
# Appendix 1: Current Trust line Storage Requirements
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
 
# Implementation Notes
1. At present, there is no `CFTRedeem` transaction because holders of a CFT can use a normal payment transaction to send CFT back to the issuer, thus "redeeming" CFT and removing it from circulation. Note that in order for this to work, issuer accounts may not hold CFT.

1. For CFTokenIssuances that have the `lsfRequiresAuthorization` flag set, it is envisioned that a [DepositPreauth](https://xrpl.org/depositpreauth.html) transaction could be used with minor adaptations to distinguish between pre-authorized trust lines and pre-authorized CFTs. Alternatively, we might consider deposit_preauth objects might apply to both, under the assumption that a single issuer restricting trust lines will want to make the same restrictions around CFTs emanating from the same issuer account.

_Originally posted by @sappenin in https://github.com/XRPLF/XRPL-Standards/discussions/82_
