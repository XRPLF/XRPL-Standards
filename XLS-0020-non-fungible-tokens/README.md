<pre>
  xls: 20
  title: Non-Fungible Token Support
  description: Extensions to the XRP Ledger that support a native non-fungible token type with operations to enumerate, purchase, sell and hold such tokens
  author: David J. Schwartz <david@ripple.com>, Aanchal Malhotra <amalhotra@ripple.com>, Nikolaos D. Bougalis <nikb@bougalis.net>
  proposal-from: https://github.com/XRPLF/XRPL-Standards/discussions/46
  status: Final
  category: Amendment
  created: 2021-05-24
</pre>

# 1. Non-Fungible Token Support

## 1.1. Abstract

The XRP Ledger offers support for tokens (a.k.a. IOUs or issued assets). Such assets are, primarily, fungible. They can be easily traded between users for XRP or other issued assets on the XRP Ledger's decentralized exchange. This makes them ideal for payments.

Such objects can also be used to implement non-fungible tokens (NFTokens), as seen in an example implementation by the **XRPL Labs** team.

Non-fungible tokens serve to encode ownership of physical, non-physical or purely digital goods, such as works of art and in-game items.

This proposal introduces extensions to the XRP Ledger that would support a native non-fungible token type, along with operations to enumerate, purchase, sell and hold such tokens.

While other proposals (some of which are _extremely_ interesting) have been made, the authors believe that this proposal represents a strong commitment to supporting NFTs on the XRP Ledger, and adds a rich set of flexible primitives that can be used by token issuers.

The non-fungible tokens proposed are:

- **Indivisible**;
- **Unique**; and
- **Not used for payments**.

### 1.1.1. Advantages and Disadvantages

**Advantages**

- NFT-specific configurations and options such as transfer fees and burnable/non-burnable tokens allow for flexibility.
- An efficient storage mechanism, capable of storing a large number of NFTs.

**Disadvantages**

- Requires an amendment to the XRP Ledger protocol, which increases complexity and adds more types of data that must be tracked and maintained as part of the ledger indefinitely.
- New transaction and data types require new implementation code from client libraries and wallets to read, display, and transact with NFTs.

## 1.2. Creating and Transferring Tokens on XRPL

### 1.2.1. On-Ledger Data Structures

We propose two new objects and one new ledger structure:

1. An **`NFToken`** is a new object that describes a single NFT.
2. An **`NFTokenOffer`** is a new object that describes an offer to buy or sell a single `NFToken`.
3. An **`NFTokenPage`** is a ledger structure that contains a set of **`NFToken`** objects owned by the same account.

#### 1.2.1.1. The **`NFToken`** object

The **`NFToken`** object represents a single NFT and holds data associated with the NFT itself. NFTs are created using the **`NFTokenMint`** transaction and can, optionally, be destroyed by the **`NFTokenBurn`** transaction.

##### 1.2.1.1.1. Fields

An **`NFToken`** object can have the following required and optional fields. Notice that, unlike other objects, no field is needed to identify the object type or current owner of the object, because NFTs are grouped into pages that implicitly define the object type and identify the owner.

---

| Field Name  |     Required?      | JSON Type | Internal Type |
| ----------- | :----------------: | :-------: | :-----------: |
| `NFTokenID` | :heavy_check_mark: | `string`  |   `UINT256`   |

This composite field uniquely identifiers a token; it contains:

- a set of 16 bits that identify flags or settings specific to the NFT
- 16 bits that encode the transfer fee associated with this token,
  if any
- the 160-bit account identifier of the issuer
- a 32-bit issuer-specified [taxon](https://www.merriam-webster.com/dictionary/taxon)
- an automatically generated monotonically increasing 32-bit sequence number.

The 16-bit flags and transfer fee fields, and the 32-bit taxon and sequence number fields, are stored in big-endian format.

###### 1.2.1.1.1.1 `Flags`

A set of flags indicating properties or other options associated with this **`NFToken`** object. The type-specific flags proposed at this are:

> |     Flag Name     | Flag Value | Description                                                                                                                                         |
> | :---------------: | :--------: | :-------------------------------------------------------------------------------------------------------------------------------------------------- |
> |   `lsfBurnable`   |  `0x0001`  | If set, indicates that the issuer (or an entity authorized by the issuer) can destroy the object. The object's owner can _always_ do so.            |
> |   `lsfOnlyXRP`    |  `0x0002`  | If set, indicates that the tokens can only be offered or sold for XRP.                                                                              |
> |  `lsfTrustLine`   |  `0x0004`  | (**DEPRECATED**) If set, indicates that the issuer wants a trustline to be automatically created.                                                   |
> | `lsfTransferable` |  `0x0008`  | If set, indicates that this NFT can be transferred. This flag has no effect if the token is being transferred _from_ the issuer or _to_ the issuer. |
> | `lsfReservedFlag` |  `0x8000`  | This proposal reserves this flag for future use. Attempts to set this flag should fail.                                                             |

These flags are **immutable**: they can only be set during the **`NFTokenMint`** transaction and cannot be changed later.

:memo: (**DEPRECATED**) The `lsfTrustLine` field is useful when the token can be offered for sale for assets other than **XRP** and the issuer charges a `TransferFee`. If this flag is set, then a trust line will be automatically created, when needed, to allow the issuer to receive the appropriate transfer fee. If this flag is not set, then an attempt to transfer for token for an asset that the issuer does not have a trustline for will fail.

###### 1.2.1.1.1.2 `TransferFee`

The value specifies the fee, in tenths of a [basis point](https://en.wikipedia.org/wiki/Basis_point), charged by the issuer for secondary sales of the token, if such sales are allowed at all. Valid values for this field are between 0 and 50,000 inclusive. A value of 1 is equivalent to 1/10 of a basis point or 0.001%, allowing transfer rates between 0% and 50%. A `TransferFee` of 50,000 corresponds to 50%.

###### 1.2.1.1.1.3 Taxon Scrambling

An issuer may issue several NFTs with the same taxon. To ensure that NFTs are spread across multiple pages, we lightly mix the taxon up by using the sequence (which is not under the issuer's direct control) as the seed for a simple linear congruential generator.

From the [Hull-Dobell theorem](https://en.wikipedia.org/wiki/Linear_congruential_generator) we know that **`f(x)=(m*x+c) mod n`** yields a permutation of **`[0, n)`** when **`n`** is a power of 2 if **`m`** is congruent to **`1 mod 4`** and **`c`** is odd.

This proposal fixes **`m = 384160001`** and **`c = 2459`**. **Changing these numbers after this proposal is implemented and deployed would be a breaking change requiring, at a minimum, an amendment and a way to distinguish token IDs that were generated with the old code.**

###### 1.2.1.1.1.4 Example

For example, the `NFTokenID` `000B013A95F14B0E44F78A264E41713C64B5F89242540EE2BC8B858E00000D65` would uniquely identify the token with `Taxon` **146,999,694** and `Sequence` **3,429**, issued by `rNCFjv8Ek5oDrNiMJ3pw6eLLFtMjZLJnf2`. The `TransferFee` is **3.14%** and the `Flags` associated with the token are: **`lsfBurnable`**, **`lsfOnlyXRP`** and **`lsfTransferable`**:

```
000B 0C44 95F14B0E44F78A264E41713C64B5F89242540EE2 BC8B858E 00000D65
+--- +--- +--------------------------------------- +------- +-------
|    |    |                                        |        |
|    |    |                                        |        `---> Sequence: 3,429
|    |    |                                        |
|    |    |                                        `---> Taxon: 146,999,694
|    |    |
|    |    `---> Issuer: rNCFjv8Ek5oDrNiMJ3pw6eLLFtMjZLJnf2
|    |
|    `---> TransferFee: 314.0 bps or 3.140%
|
`---> Flags: 12 -> lsfBurnable, lsfOnlyXRP and lsfTransferable
```

:information*source: Notice that the scrambled version of the taxon is `0xBC8B858E`: the scrambled version of the taxon specified by the issuer. But the \_actual* value of the taxon is the unscrambled value.

---

| Field Name | Required? | JSON Type | Internal Type |
| ---------- | :-------: | :-------: | :-----------: |
| `URI`      |           | `string`  |    `BLOB`     |

A URI that points to the data and/or metadata associated with the NFT. This field need not be an HTTP or HTTPS URL; it could be an IPFS URI, a magnet link, immediate data encoded as an RFC2379 ["data" URL](https://datatracker.ietf.org/doc/html/rfc2397), or even an opaque issuer-specific encoding. The URI is **NOT** checked for validity, but the field is limited to a maximum length of 256 bytes.

:memo: In the interest of reducing the size of NFT objects and their impact on the ledger as a whole as well as maximizing flexibility, this implementation recommends (but does not require) that this field be avoided. Not only does this field increase the amount of data that must be stored on ledger, but it is also immutable, which means that, if specified, it commits the issuer to hosting the data and/or metadata associated with the NFT at the specified location. See the **Retrieving NFToken Data and Metadata** section below for details on alternatives.

###### 1.2.1.1.2.1. Example NFToken JSON

```
{
    "NFTokenID": "000B013A95F14B0044F78A264E41713C64B5F89242540EE208C3098E00000D65",
    "URI": "ipfs://bafybeigdyrzt5sfp7udm7hu76uh7y26nf4dfuylqabf3oclgtqy55fbzdi"
}
```

##### Retrieving NFToken Data and Metadata

In the interest of (a) minimizing the footprint of an NFT but without sacrificing utility or functionality, and (b) imposing as few restrictions as possible, this specification does not allow an NFT to hold arbitrary data fields. Instead, such data, whether structured or unstructured, is maintained separately and referenced by the NFT. This proposal recommends using one of the following two approaches to provide external references to obtain **`NFToken`** data and/or metadata.

- `URI` field: We propose an optional `URI` field in the **`NFToken`** object. Implementations MAY choose to use this field to provide an external reference to:
  - The immutable content for `Hash`.
  - Mutable metadata, if any, for the **`NFToken`** object.

The `URI` field is especially useful for referring to non-traditional Peer-to-Peer (P2P) URLs. For example, a `NFTokenMinter` wishing to store **`NFToken`** data and/or metadata using the Inter Planetary File System (IPFS) MAY use `URI` field to refer to data on IPFS in different ways, each of which is suited to different use-cases. For more context on types of IPFS links that can be used to store NFT data, see [Best Practices for NFT Data](https://docs.ipfs.io/how-to/best-practices-for-nft-data/#types-of-ipfs-links-and-when-to-use-them).

- `Domain` field: Alternative to the above approach, issuers of **`NFToken`** objects can set the `Domain` field of their issuing account to the correct domain and offer an API for clients that want to lookup the data and/or metadata associated with a particular NFT. This proposal recommends the use of DNS `TXT` records as a customization point, allowing the issuer to specify the URL to be used by providing a properly formatted TXT record.

Note that using this mechanism _requires_ the `NFTokenMinter` to acquire a domain name and set the domain name for their minting account, but does **not** require the `NFTokenMinter` to necessarily operate a server
or other service to provide the ability to query this data; instead, a `NFTokenMinter` can easily "redirect" queries to a data provider (e.g., to a marketplace, registry or other service).

Implementations should check for the presence of `URI` field first to retrieve the associated data and/or metadata. If the `URI` field does not exist, implementations should check for the presence of `Domain` field. Nothing happens, if neither of the fields exist. Implementations should be prepared to handle HTTP redirections (e.g., using HTTP responses 301, 302, 307 and 308) from the URI.

###### TXT Record Format:

```
xrpl-nft-data-token-info-v1 IN TXT "https://host.example.com/api/token-info/{:NFTokenID:}"
```

Replace the string `{:NFTokenID:}` with the requested tokens' **`NFTokenID`**, as a 64 byte hex string when attempting to query information.

Implementations should check for the presence of `TXT` records and use those query strings, if present. If no string is present, attempt to use the default URL. Assuming the domain was **example.com**, the default URL this proposal recommends would be:

`https://example.com/.well-known/xrpl-nft/{:nft_id:}`

#### The **`NFTokenPage`** ledger entry

This object represents a collection of **`NFToken`** objects owned by the same account. It is important to note that the **`NFToken`** objects themselves reside within this page, instead of in a dedicated object entry in the `SHAMap`. An account can have multiple **`NFTokenPage`** ledger objects, which form a doubly linked list (DLL).

In the interest of minimizing the size of a page and optimizing storage, the `Owner` field is not present, since it is encoded as part of the object's ledger identifier (more details in the **`NFTokenPageID`** discussion).

##### Fields

An **`NFTokenPage`** object may have the following required and optional fields:

| Field Name        |     Required?      | JSON Type | Internal Type |
| ----------------- | :----------------: | :-------: | :-----------: |
| `LedgerEntryType` | :heavy_check_mark: | `string`  |   `UINT16`    |

Identifies the type of ledger object. This proposal recommends the value `0x0050` as the reserved ledger entry type.

---

| Field Name        | Required? | JSON Type | Internal Type |
| ----------------- | :-------: | :-------: | :-----------: |
| `PreviousPageMin` |           | `string`  |   `UINT256`   |

The locator of the previous page, if any. Details about this field and how it should be used are outlined below, after the construction of the **`NFTokenPageID`** is explained.

---

| Field Name    | Required? | JSON Type | Internal Type |
| ------------- | :-------: | :-------: | :-----------: |
| `NextPageMin` |           | `string`  |   `UINT256`   |

The locator of the next page, if any. Details about this field and how it should be used are outlined below, after the construction of the **`NFTokenPageID`** is explained.

---

| Field Name      | Required? | JSON Type | Internal Type |
| --------------- | :-------: | :-------: | :-----------: |
| `PreviousTxnID` |           | `string`  |   `HASH256`   |

Identifies the transaction ID of the transaction that most recently modified this **`NFTokenPage`** object.

---

| Field Name          | Required? | JSON Type | Internal Type |
| ------------------- | :-------: | :-------: | :-----------: |
| `PreviousTxnLgrSeq` |           | `number`  |   `UINT32`    |

The sequence of the ledger that contains the transaction that most recently modified this **`NFTokenPage`** object.

---

| Field Name |     Required?      | JSON Type | Internal Type |
| ---------- | :----------------: | :-------: | :-----------: |
| `NFTokens` | :heavy_check_mark: | `object`  |    `TOKEN`    |

The collection of **`NFToken`** objects contained in this **`NFTokenPage`** object. This specification places an upper bound of 32 **`NFToken`** objects per page. Objects should be stored in sorted order, from low to high with the low order 96-bit of the `NFTokenID` used as the sorting parameter.

---

##### TokenPage ID Format

Unlike other object identifiers on the XRP Ledger, which are derived by hashing a collection of data using `SHA512-Half`, **`NFTokenPage`** identifiers are constructed so as to specfically allow for the adoption of a more efficient paging structure, ideally suited for NFTs.

The identifier of an **`NFTokenPage`** is derived by concatenating the 160-bit `AccountID` of the owner of the page, followed by a 96 bit value that indicates whether a particular **`NFTokenID`** may be contained in this page.

More specifically, and assuming that the function `low96(x)` returns the low 96 bits of a 256-bit value, an NFT with **`NFTokenID`** `A` can be included in a page with **`NFTokenPageID`** `B` if and only if `low96(A) >= low96(B)`.

For example, applying the `low96` function to the NFT described before, which had an ID of `000B013A95F14B0044F78A264E41713C64B5F89242540EE208C3098E00000D65` the function `low96` would return `42540EE208C3098E00000D65`.

This curious construct exploits the structure of the SHAMap to allow for efficient lookups of individual **`NFToken`** objects without requiring iteration of the doubly linked list of **`NFTokenPages`**.

### Example TokenPage JSON

```
{
    "LedgerEntryType": "NFTokenPage",
    "PreviousTokenPage": "598EDFD7CF73460FB8C695d6a9397E907378C8A841F7204C793DCBEF5406",
    "PreviousTokenNext": "598EDFD7CF73460FB8C695d6a9397E9073781BA3B78198904F659AAA252A",
    "PreviousTxnID": "95C8761B22894E328646F7A70035E9DFBECC90EDD83E43B7B973F626D21A0822",
    "PreviousTxnLgrSeq": 42891441,
    "Tokens":
        {
            {
                "NFTokenID": "000B013A95F14B0044F78A264E41713C64B5F89242540EE208C3098E00000D65",
                "URI": "ipfs://bafybeigdyrzt5sfp7udm7hu76uh7y26nf4dfuylqabf3oclgtqy55fbzdi"
            },
            /* potentially more objects */
       }
}
```

### How do **`NFTokenPage`** objects work?

The page within which an **`NFToken`** entry is stored is formed as described above. This is needed to find the correct starting point in the doubly linked list of **`NFTokenPage`** objects if that list is large. This is because it is inefficient to have to traverse the list from the beginning if an account holds thousands of **`NFToken`** objects in hundreds of **`NFTokenPage`** objects.

### Searching an **`NFToken`** object

To search for a specific **`NFToken`**, the first step is to locate the **`NFTokenPage`**, if any, that should contain that **`NFToken`**. For that do the following:

Compute the **`NFTokenPageID`** using the account of the owner and the **`NFTokenID`** of the token, as described above. Then search for the ledger entry whose identifier is less than or equal to that value. If that entry does not exist or is not an **`NFTokenPage`**, the **`NFToken`** is not held by the given account.

### Adding an **`NFToken`** object

An **`NFToken`** object can be added by using the same approach to find the **`NFTokenPage`** it should be in and adding it to that page. If after addition the page overflows, find the `next` and `previous` pages (if any) and balance those three pages, inserting a new page as needed.

### Removing an **`NFToken`** object

An **`NFToken`** can be removed by using the same approach. If the number of **`NFTokens`** in the page goes below a certain threshhold, an attempt will be made to consolidate the page with a `previous` or subsequent page and recover the reserve.

### Reserve for **`NFTokenPage`** object

Each **`NFTokenPage`** costs an incremental reserve to the owner account. This specification allows up to 32 **`NFToken`** entries per page, which means that for accounts that hold multiple NFTs the _effective_ reserve cost per NFT can be as low as <sup>_R_</sup>/<sub>32</sub> where _R_ is the incremental reserve.

#### The reserve in practice

The value of the incremental reserve is, as of this writing, 2 XRP. The table below shows what the _effective_ reserve per token is, if a given page contains 1, 8, 16, 32 and 64 NFTs:

| Incremental Reserve |   1 NFT   |    8 NFTs    |    16 NFTs    |    32 NFTs     |     64 NFTs     |
| :-----------------: | :-------: | :----------: | :-----------: | :------------: | :-------------: |
|        5 XRP        |   5 XRP   |  0.625 XRP   |  0.3125 XRP   |  0.15625 XRP   |   0.07812 XRP   |
|      **2 XRP**      | **2 XRP** | **0.25 XRP** | **0.125 XRP** | **0.0625 XRP** | **0.03125 XRP** |
|        1 XRP        |   1 XRP   |  0.125 XRP   |  0.0625 XRP   |  0.03125 XRP   |   0.01562 XRP   |

## Transactions

This proposal introduces several new transactions to allow for the minting, burning and trading of NFTs. All transactions introduced by this proposal incorporate the [common transaction fields](https://xrpl.org/transaction-common-fields.html)
that are shared by all transactions. Common fields are not documented in this proposal unless needed, because this proposal introduces new possible values for such fields.

## Transactions for minting and burning NFTs on XRPL

We define two transactions: **`NFTokenMint`** and **`NFTokenBurn`** for minting and burning NFTs respectively on XRPL.

### The **`NFTokenMint`** transaction

The **`NFTokenMint`** transaction creates an **`NFToken`** object and adds it to the relevant **`NFTokenPage`** object of the `NFTokenMinter`. A required parameter to this transaction is the **`Token`** field specifying the actual token. This transaction is the only opportunity the `NFTokenMinter` has to specify any token fields that are defined as immutable (e.g., the `TokenFlags`).

If the transaction is successful, the newly minted NFToken will be owned by the account (the `NFTokenMinter` account) which executed the transaction. If needed, a new **`NFTokenPage`** is created for this account and a reserve is charged as described earlier.

#### Transaction-specific Fields

| Field Name        |     Required?      | JSON Type | Internal Type |
| ----------------- | :----------------: | :-------: | :-----------: |
| `TransactionType` | :heavy_check_mark: | `string`  |   `UINT16`    |

Indicates the new transaction type **`NFTokenMint`**. The integer value is `25`.

| Field Name |     Required?      | JSON Type | Internal Type |
| ---------- | :----------------: | :-------: | :-----------: |
| `Account`  | :heavy_check_mark: | `string`  | `ACCOUNT ID`  |

Indicates the account which is minting the token. The account MUST _either_:

- match the `Issuer` field in the **`NFToken`** object; or
- match the `NFTokenMinter` field in the `AccountRoot` of the `Issuer` field in the **`NFToken`** object.

| Field Name | Required? | JSON Type | Internal Type |
| ---------- | :-------: | :-------: | :-----------: |
| `Issuer`   |           | `string`  | `ACCOUNT ID`  |

Indicates the account that should be the issuer of this token. This value is _optional_ and should only be specified if the account executing the transaction is not the `Issuer` of the **`NFToken`** object. If it is present, the `NFTokenMinter` field in the `AccountRoot` of the `Issuer` field must match the `Account`, otherwise the transaction will fail.

---

| Field Name     |     Required?      | JSON Type | Internal Type |
| -------------- | :----------------: | :-------: | :-----------: |
| `NFTokenTaxon` | :heavy_check_mark: | `number`  |   `UINT32`    |

Indicates the taxon associated with this token. The taxon is generally a value chosen by the `NFTokenMinter` of the token and a given taxon may be used for multiple tokens. Taxons have a valid range range from 0x0 to 0xFFFFFFFF.

---

| Field Name | Required? | JSON Type | Internal Type |
| ---------- | :-------: | :-------: | :-----------: |
| `Flags`    |           | `number`  |   `UINT32`    |

Specifies the flags for this transaction. In addition to the universal transaction flags that are applicable to all transactions (e.g., `tfFullyCanonicalSig`), the following transaction-specific flags are defined and used to set the appropriate fields in the NFT:

> |    Flag Name     |  Flag Value  | Description                                                                    |
> | :--------------: | :----------: | :----------------------------------------------------------------------------- |
> |   `tfBurnable`   | `0x00000001` | If set, indicates that the `lsfBurnable` flag should be set.                   |
> |   `tfOnlyXRP`    | `0x00000002` | If set, indicates that the `lsfOnlyXRP` flag should be set.                    |
> |  `tfTrustLine`   | `0x00000004` | (**DEPRECATED**) If set, indicates that the `lsfTrustLine` flag should be set. |
> | `tfTransferable` | `0x00000008` | If set, indicates that the `lsfTransferable` flag should be set.               |

---

| Field Name    | Required? | JSON Type | Internal Type |
| ------------- | :-------: | :-------: | :-----------: |
| `TransferFee` |           | `number`  |   `UINT16`    |

The value specifies the fee to charged by the issuer for secondary sales of the Token, if such sales are allowed. Valid values for this field are between 0 and 50,000 inclusive, allowing transfer rates of between 0.000% and 50.000% in increments of 0.001.

The field MUST NOT be present if the `tfTransferable` flag is not set. If it is, the transaction should fail and a fee should be claimed.

---

| Field Name | Required? | JSON Type | Internal Type |
| ---------- | :-------: | :-------: | :-----------: |
| `URI`      |           | `string`  |    `BLOB`     |

A URI that points to the data and/or metadata associated with the NFT. This field need not be an HTTP or HTTPS URL; it could be an IPFS URI, a magnet link, immediate data encoded as an RFC2379 ["data" URL](https://datatracker.ietf.org/doc/html/rfc2397), or even an opaque issuer-specific encoding. The URI is **NOT** checked for validity, but the field is limited to a maximum length of 256 bytes.

#### Embedding additional information

If `NFTokenMinters` need to specify additional information during minting (for example, details identifying a property by referencing a particular [plat](https://en.wikipedia.org/wiki/Plat), a vehicle by specifying a [VIN](https://en.wikipedia.org/wiki/Vehicle_identification_number), or other object-specific descriptions) they should use the [`memo`](https://xrpl.org/transaction-common-fields.html#memos-field) functionality that is already available on the XRP Ledger as a common field. Memos are a part of the signed transaction and are available from historical archives, but are not stored in the ledger.

---

## Example **`NFTokenMint`** transaction

```
{
  "TransactionType": "NFTokenMint",
  "Account": "rvYAfWj5gh67oV6fW32ZzP3Aw4Eubs59B",
  "Issuer": "rNCFjv8Ek5oDrNiMJ3pw6eLLFtMjZLJnf2",
  "TransferFee": 314,
  "Flags": 2147483659,
  "Fee": 10,
  "URI": "ipfs://bafybeigdyrzt5sfp7udm7hu76uh7y26nf4dfuylqabf3oclgtqy55fbzdi"
  "Memos": [
        {
            "Memo": {
                "MemoType": "687474703A2F2F6578616D706C652E636F6D2F6D656D6F2F67656E65726963",
                "MemoData": "72656E74"
            }
        }
    ],
}
```

This transaction assumes that the issuer, `rNCFjv8Ek5oDrNiMJ3pw6eLLFtMjZLJnf2`, has set the `NFTokenMinter` field in its `AccountRoot` to `rvYAfWj5gh67oV6fW32ZzP3Aw4Eubs59B`, thereby authorizing that account to mint tokens on its behalf.

#### Execution

This transaction examines the `FirstNFTokenSequence` and `MintedNFTokens` fields in the account root of the `Issuer`, and uses them to construct the `NFTokenID` for the token being minted. If `FirstNFTokenSequence` does not exist, this field is assumed to have the same value as the `Sequence` field of the `Issuer`. If `MintedNFTokens` does not exist, this field is assumed to have the value 0; the value of the field is incremented by exactly 1.

### The **`NFTokenBurn`** transaction

The **`NFTokenBurn`** transaction is used to remove an **`NFToken`** object from the **`NFTokenPage`** in which it is being held, effectively removing the token from the ledger ("burning" it).

If this operation succeeds, the corresponding **`NFToken`** is removed. If this operation empties the **`NFTokenPage`** holding the **`NFToken`** or results in the consolidation, thus removing an **`NFTokenPage`**, the owner’s reserve requirement is reduced by one. This operation would also delete up to a maximum of 500 `buy`/`sell` **`NFTokenOffer`** objects for the burnt **`NFToken`**, leaving any remaining **`NFTokenOffer`** untouched on the ledger.

#### Transaction-specific Fields

| Field Name        |     Required?      | JSON Type | Internal Type |
| ----------------- | :----------------: | :-------: | :-----------: |
| `TransactionType` | :heavy_check_mark: | `string`  |   `UINT16`    |

Indicates the new transaction type **`NFTokenBurn`**. The integer value is `26`.

---

| Field Name |     Required?      | JSON Type | Internal Type |
| ---------- | :----------------: | :-------: | :-----------: |
| `Account`  | :heavy_check_mark: | `string`  | `ACCOUNT ID`  |

Indicates the `AccountID` that submitted this transaction. The account MUST be either the present `owner` of the token or, if the **`lsfBurnable`** flag is set in the **`NFToken`**, either the `issuer` account or an account authorized by the issuer, i.e., `NFTokenMinter`.

---

| Field Name  |     Required?      | JSON Type | Internal Type |
| ----------- | :----------------: | :-------: | :-----------: |
| `NFTokenID` | :heavy_check_mark: | `string`  |   `UINT256`   |

Identifies the **`NFToken`** object to be removed by the transaction.

### Example **`NFTokenBurn`** JSON

```
{
      "TransactionType": "NFTokenBurn",
      "Account": "rvYAfWj5gh67oV6fW32ZzP3Aw4Eubs59B",
      "Fee": 10,
      "NFTokenID": "000B013A95F14B0044F78A264E41713C64B5F89242540EE208C3098E00000D65"
}

```

### 1.3. Account Root modifications

This proposal introduces 3 additional fields in an `AccountRoot`:

1. The `NFTokenMinter` field;
2. The `MintedNFTokens` field;
3. The `BurnedNFTokens` field; and the
4. The `FirstNFTokenSequence` field.

#### 1.3.1 `NFTokenMinter`

It is likely that issuers may want to issue NFTs from their well known account, while, at the same time, wanting to delegate the issuance of such NFTs to a mint or other third party. To enable this use case, this specification introduces a new, optional field in the `AccountRoot` object.

| Field Name      | Required? | JSON Type | Internal Type |
| --------------- | :-------: | :-------: | :-----------: |
| `NFTokenMinter` |           | `string`  |  `AccountID`  |

The `NFTokenMinter` field, if set, specifies an alternate account which is allowed to execute the **`NFTokenMint`** and **`NFTokenBurn`** operations on behalf of the account.

The **`AccountSet`** transaction should be augmented to allow the field to be set or cleared.

**Note:** Previous versions of this spec used the term `MintAccount` for this field.

#### 1.3.2 `MintedNFTokens`

To ensure the uniqueness of **`NFToken`** objects, this proposal introduces the `MintedNFTokens` field. This field is used during the **`NFTokenMint`** transaction and used to form the `NFTokenID` of the new object. If this field is not present, the value 0 is assumed.

### 1.3.3 `BurnedNFTokens`

To provide a convenient way to determine how many **`NFToken`** objects issued by an account are still active (i.e., not burned), this proposal introduces the `BurnedNFTokens` field. If this field is not present, the value 0 is assumed. The field is incremented whenever a token issued by this account is burned. So this field will be present and non-zero for any account that has issued at least one token and one or more of those tokens have been burned.

:memo: An account for which the difference between the number of minted and burned tokens, as stored in the `MintedNFTokens` and `BurnedNFTokens` fields respectively, is non-zero cannot be deleted.

### 1.3.4 `FirstNFTokenSequence`

To ensure the `NFTokenID` cannot be reproduced by the issuer in any way, this proposal introduces the `FirstNFTokenSequence` field. When the issuer mints their first `NFToken`, this field is set to the current `Sequence` of the issuer's account and never changes. This field is used during the `Sequence` number construct of a `NFTokenID`.

## 1.4. Transferability of Tokens (NFTs)

Tokens which have the `lsfTransferable` flag set can be transferred among users. This is achieved by way of offers.

### 1.4.1. The **`NFTokenOffer`** ledger entry

The **`NFTokenOffer`** ledger entry represents an offer to buy, sell or transfer an **`NFToken`** object. An **`NFTokenOffer`** object is created as a result of **`NFTokenCreateOffer`** transaction by the owner of the **`NFToken`**.

#### 1.4.1.1. **`NFTokenOfferID`** Format

The unique ID, a.k.a **`NFTokenOfferID`**, of the **`NFTokenOffer`** object is the result of **`SHA512-Half`** of the following values concatenated in order:

- The **`NFTokenOffer`** space key; this proposal recommends using the value `0x0074`;
- The `AccountID` of the account placing the offer; and
- The `Sequence` (or `Ticket`) of the **`NFTokenCreateOffer`** transaction that will create the **`NFTokenOffer`**.

#### Fields

| Field Name |     Required?      | JSON Type | Internal Type |
| ---------- | :----------------: | :-------: | :-----------: |
| `Owner`    | :heavy_check_mark: | `string`  |  `AccountID`  |

Indicates the `Owner` of the account that is creating and owns the offer. Only the current `Owner` of an **`NFToken`** can create an offer to **sell** an **`NFToken`**, but any account can create an offer to **buy** an **`NFToken`**.

---

| Field Name        |     Required?      | JSON Type | Internal Type |
| ----------------- | :----------------: | :-------: | :-----------: |
| `LedgerEntryType` | :heavy_check_mark: | `string`  |   `UINT16`    |

Indicates the type of ledger object. This proposal recommends using the value `0x0074`.

---

| Field Name |     Required?      | JSON Type | Internal Type |
| ---------- | :----------------: | :-------: | :-----------: |
| `Flags`    | :heavy_check_mark: | `number`  |   `UINT32`    |

A set of flags associated with this object, used to specify various options or settings. This proposal only defines one flag at this time, used to determine if this is a `Buy`
or `Sell` offer:

> |   Flag Name    |  Flag Value  | Description                                                                            |
> | :------------: | :----------: | :------------------------------------------------------------------------------------- |
> | `lsfSellToken` | `0x00000001` | If set, indicates that the offer is a sell offer. Otherwise, the offer is a buy offer. |

---

| Field Name      |     Required?      | JSON Type | Internal Type |
| --------------- | :----------------: | :-------: | :-----------: |
| `PreviousTxnID` | :heavy_check_mark: | `string`  |   `Hash256`   |

Indicates the identifying hash of the transaction that most recently modified this object.

---

| Field Name          |     Required?      | JSON Type | Internal Type |
| ------------------- | :----------------: | :-------: | :-----------: |
| `PreviousTxnLgrSeq` | :heavy_check_mark: | `number`  |   `UINT32`    |

Indicates the index of the ledger that contains the transaction that most recently modified this object.

---

| Field Name  |     Required?      | JSON Type | Internal Type |
| ----------- | :----------------: | :-------: | :-----------: |
| `NFTokenID` | :heavy_check_mark: | `string`  |   `UINT256`   |

Specifies the **`NFTokenID`** of the **`NFToken`** object being referenced by this offer.

---

| Field Name |     Required?      |      JSON Type       | Internal Type |
| ---------- | :----------------: | :------------------: | :-----------: |
| `Amount`   | :heavy_check_mark: | `object` or `string` |   `AMOUNT`    |

Indicates the amount expected or offered for the **`NFToken`**. If the token has the `lsfOnlyXRP` flag set, the amount **MUST** be specified in XRP.

Sell offers that specify assets other than XRP must specify a non-zero amount. Sell offers which specify XRP can be 'free' (i.e., the `Amount` field may be equal to `"0"`).

---

| Field Name   | Required? | JSON Type | Internal Type |
| ------------ | :-------: | :-------: | :-----------: |
| `Expiration` |           | `number`  |   `UINT32`    |

Indicates the time after which the offer is no longer active. The value is the number of seconds since the [Ripple Epoch](https://xrpl.org/basic-data-types.html#specifying-time).

---

| Field Name    | Required? | JSON Type | Internal Type |
| ------------- | :-------: | :-------: | :-----------: |
| `Destination` |           | `string`  | `Account ID`  |

Only allowed if the `lsfSellToken` flag is set. Indicates the `AccountID` that this sell offer is intended for (either a buyer or a broker). If present, only that account can accept the sell offer.

---

| Field Name  | Required? | JSON Type | Internal Type |
| ----------- | :-------: | :-------: | :-----------: |
| `OwnerNode` |           | `string`  |   `UINT64`    |

Internal bookkeeping, indicating the page inside the owner directory where this token is being tracked. This field allows of the efficient deletion of offers.

---

| Field Name         | Required? | JSON Type | Internal Type |
| ------------------ | :-------: | :-------: | :-----------: |
| `NFTokenOfferNode` |           | `string`  |   `UINT64`    |

Internal bookkeeping, indicating the page inside the token buy or sell offer directory, as appropriate, where this token is being tracked. This field allows of the efficient deletion of offers.

## 1.5. How does **`NFTokenOffer`** work?

Unlike regular offers on XRPL, which are stored sorted by quality in an order book and are automatically matched by an on-ledger mechanism, an **`NFTokenOffer`** is not stored in an order book and will never be automatically matched or executed.

A buyer must _explicitly_ choose to accept an **`NFTokenOffer`** that offers to sell an **`NFToken`**. Similarly, a seller must _explicitly_ choose to accept a specific **`NFTokenOffer`** that offers to buy an **`NFToken`** object that they own.

> **Note**: An **`NFTokenOffer`** for an **`NFToken`** _may_ be implicitly deleted during an **`NFTokenBurn`** transaction of the **`NFToken`**.

### 1.5.1. Locating **`NFTokenOffer`** objects

Each token has two directories, one containing offers to buy the token and the other containing offers to sell the token. This makes it easy to find **`NFTokenOffer`** for a particular token. It is expected that off-ledger systems will be used to retrieve, present, communicate and effectuate the creation, enumeration, acceptance or cancellation of offers. For example, a marketplace may offer intuitive web- or app-based interfaces for users.

### 1.5.2. **`NFTokenOffer`** Reserve

Each **`NFTokenOffer`** object costs the account placing the offer one incremental reserve. As of this writing the incremental reserve is 2 XRP. The reserve can be recovered by cancelling the offer. The reserve is also recovered if the offer is accepted, which removes the offer from the XRP Ledger.

It is important for an account to cancel all of their outstanding offers for a burnt **`NFToken`** to reclaim the reserves. Otherwise, these offers will be left dangling on the ledger.

### 1.5.3. **`NFTokenOffer`** Transactions

There are three defined transactions:

1. **`NFTokenCreateOffer`**
2. **`NFTokenCancelOffer`**
3. **`NFTokenOfferAccept`**

All three transactions have the generic set of transaction fields, some of which may be ommitted from this proposal for the sake of clarity.

### 1.5.4. **`NFTokenCreateOffer`** transaction

The **`NFTokenCreateOffer`** transaction creates either a new `Sell` offer for an **`NFToken`** owned by the account executing the transaction, or a new `Buy` offer for **`NFToken`** owned by another account.

Each offer costs one incremental reserve.

#### 1.5.4.1. Fields

| Field Name        |     Required?      | JSON Type | Internal Type |
| ----------------- | :----------------: | :-------: | :-----------: |
| `TransactionType` | :heavy_check_mark: | `string`  |   `UINT16`    |

Indicates the new transaction type **`NFTokenCreateOffer`**. The integer identifier is `27`.

---

| Field Name |     Required?      | JSON Type | Internal Type |
| ---------- | :----------------: | :-------: | :-----------: |
| `Account`  | :heavy_check_mark: | `string`  |  `AccountID`  |

Indicates the `AccountID` of the account that initiated the transaction.

---

| Field Name | Required? | JSON Type | Internal Type |
| ---------- | :-------: | :-------: | :-----------: |
| `Owner`    |           | `string`  |  `AccountID`  |

Indicates the `AccountID` of the account that owns the corresponding **`NFToken`**.

- If the offer is to buy a token, this field must be present and it must be different than `Account` (since an offer to buy a token one already holds is meaningless).
- If the offer is to sell a token, this field must not be present, as the owner is, implicitly, the same as `Account` (since an offer to sell a token one doesn't already hold is meaningless).

---

| Field Name |     Required?      | JSON Type | Internal Type |
| ---------- | :----------------: | :-------: | :-----------: |
| `Flags`    | :heavy_check_mark: | `number`  |   `UINT32`    |

A set of flags that specifies options or controls the behavior of the transaction. This proposal only defines one flag at this time:

> |   Flag Name   |  Flag Value  | Description                                                                     |
> | :-----------: | :----------: | :------------------------------------------------------------------------------ | --- |
> | `tfSellToken` | `0x00000001` | If set, indicates that the offer is a sell offer. Otherwise, it is a buy offer. |     |

Note that the `Flags` field includes both transaction-specific and generic flags. This proposal only specifies the transaction-specific flags; all currently valid generic flags (e.g., `tfFullyCanonicalSig`) are applicable, but not listed here.

The transactor **SHOULD NOT** allow unknown flags to be set.

---

| Field Name  |     Required?      | JSON Type | Internal Type |
| ----------- | :----------------: | :-------: | :-----------: |
| `NFTokenID` | :heavy_check_mark: | `string`  |   `Hash256`   |

Identifies the **`NFTokenID`** of the **`NFToken`** object that the offer references.

---

| Field Name |     Required?      |     JSON Type     | Internal Type |
| ---------- | :----------------: | :---------------: | :-----------: |
| `Amount`   | :heavy_check_mark: | `Currency Amount` |   `AMOUNT`    |

Indicates the amount expected or offered for the **`Token`**.

The amount must be non-zero, except where this is an offer is an offer to sell and the asset is XRP; then it is legal to specify an amount of zero, which means that the current owner of the token is giving it away, gratis, either to anyone at all, or to the account identified by the `Destination` field.

---

| Field Name   | Required? | JSON Type | Internal Type |
| ------------ | :-------: | :-------: | :-----------: |
| `Expiration` |           | `number`  |   `UINT32`    |

Indicates the time after which the offer will no longer be valid. The value is the number of seconds since the [Ripple Epoch](https://xrpl.org/basic-data-types.html#specifying-time).

---

| Field Name    | Required? | JSON Type | Internal Type |
| ------------- | :-------: | :-------: | :-----------: |
| `Destination` |           | `string`  |  `AccountID`  |

Only valid if the `tfSellToken` flag is set. If present, indicates that this offer may only be accepted by the specified account (either a broker or a buyer). Attempts by other accounts to accept this offer **MUST** fail.

If successful, the **`NFTokenCreateOffer`** transaction results in the creation of an **`NFTokenOffer`** object.

### 1.5.5. **`NFTokenCancelOffer`** transaction

The **`NFTokenCancelOffer`** transaction can be used to cancel existing token offers created using **`NFTokenCreateOffer`**.

### 1.5.5.1 Permissions

An existing offer, represented by an **`NFTokenOffer`** object, can be cancelled by:

1. The account that originally created the **`NFTokenOffer`**;
2. The account in the `Destination` field of the **`NFTokenOffer`**, if one is present; or
3. Any account if the **`NFTokenOffer`** specifies an expiration time and the close time of the parent ledger in which the **`NFTokenCancelOffer`** is included is greater than the expiration time.

This transaction removes the listed **`NFTokenOffer`** object from the ledger, if present, and adjusts the reserve requirements accordingly. It is not an error if the **`NFTokenOffer`** cannot be found, and the transaction should complete successfully if that is the case.

#### Fields

| Field Name        |     Required?      | JSON Type | Internal Type |
| ----------------- | :----------------: | :-------: | :-----------: |
| `TransactionType` | :heavy_check_mark: | `string`  |   `UINT16`    |

Indicates the new transaction type **`NFTokenCancelOffer`**. The integer identifier is `28`.

| Field Name      |     Required?      | JSON Type | Internal Type |
| --------------- | :----------------: | :-------: | :-----------: |
| `NFTokenOffers` | :heavy_check_mark: |  `array`  |  `VECTOR256`  |

An array of ledger entry IDs, each identifying an **`NFTokenOffer`** object that should be cancelled by this transaction.

It is an error if an entry in this list points to an object that is not an **`NFTokenOffer`** object. It is not an error if an entry in this list points to an object that does not exist.

---

### 1.5.6. **`NFTokenOfferAccept`** transaction

The **`NFTokenOfferAccept`** transaction is used to accept offers to `buy` or `sell` an **`NFToken`**. It can either:

1. Allow **one** offer to be accepted. This is called `direct` mode.
2. Allow **two** distinct offers, one offering to buy a given **`NFToken`** and the other offering to sell the same **`NFToken`**, to be accepted in an atomic fashion. This is called `brokered` mode.

#### 1.5.6.1. Brokered vs. Direct Mode

The mode in which the transaction operates depends on the presence of the `NFTokenSellOffer` and `NFTokenBuyOffer` fields of the transaction:

| `NFTokenSellOffer` | `NFTokenBuyOffer`  |   Mode   |
| :----------------: | :----------------: | :------: |
| :heavy_check_mark: | :heavy_check_mark: | Brokered |
| :heavy_check_mark: |        :x:         |  Direct  |
|        :x:         | :heavy_check_mark: |  Direct  |

If neither of those fields is specified, the transaction is malformed and shall produce a `tem` class error.

The semantics of `brokered` mode are slightly different than one in `direct` mode: the account executing the transaction functions as a broker, bringing the two offers together and causing them to be matched, but does not acquire ownership of the involved NFT, which will, if the transaction is successful, be transferred directly from the seller to the buyer.

#### 1.5.6.2. Execution Details

##### 1.5.6.2.1. Direct Mode

In `direct` mode, an **`NFTokenOfferAccept`** transaction **MUST** fail if:

1. The **`NFTokenOffer`** against which **`NFTokenOfferAccept`** transaction is placed is an offer to `buy`
   the **`NFToken`** and the account executing the **`NFTokenOfferAccept`** is not, at the time of execution, the current owner of the corresponding **`NFToken`**.
2. The **`NFTokenOffer`** against which **`NFTokenOfferAccept`** transaction is placed is an offer to `sell`
   the **`NFToken`** and was placed by an account which is not, at the time of execution, the current owner of the **`NFToken`**.
3. The **`NFTokenOffer`** against which **`NFTokenOfferAccept`** transaction is placed is an offer to `sell`
   the **`NFToken`** and was placed by an account which is not, at the time of execution, the `Account` in the recipient field of the **`NFTokenOffer`**, if one exists.
4. The **`NFTokenOffer`** against which **`NFTokenOfferAccept`** transaction is placed specifies an `expiration` time and the close time field of the parent of the ledger in which the transaction
   would be included has already passed.
5. The **`NFTokenOffer`** against which **`NFTokenOfferAccept`** transaction is placed to buy or sell the **`NFToken`**
   is owned by the account executing the **`NFTokenOfferAccept`**.

If the transaction is executed successfully then:

1. The relevant **`NFToken`** will change ownership, meaning that the token will be removed from the **`NFTokenPage`** of the existing `owner` and be added to the **`NFTokenPage`** of the new `owner`.
2. Funds will be transferred from the buyer to the seller, as specified in the **`NFTokenOffer`**. If the corresponding **`NFToken`** offer specifies a `TransferRate`, then the `issuer` receives the specified percentage, with the balance going to the seller of the **`NFToken`**.

##### 1.5.6.2.2. Brokered Mode

In `brokered` mode, **`NFTokenOfferAccept`** transaction **MUST** fail if:

1. The `buy` **`NFTokenOffer`** against which **`NFTokenOfferAccept`** transaction is placed is owned by the account executing the transaction.
2. The `sell` **`NFTokenOffer`** against which **`NFTokenOfferAccept`** transaction is placed is owned by the account executing the transaction.
3. The account which placed the offer to sell the **`NFToken`** is not, at the time of execution, the current owner of the corresponding **`NFToken`**.
4. Either offer (`buy` or `sell`) specifies an `expiration` time and the close time field of the parent of the ledger in which the transaction would be included has already passed.
5. The `owner` of the `sell` **`NFTokenOffer`** is the same account as the `owner` of the `buy` **`NFTokenOffer`**. In other words, the **`NFToken`** cannot be sold to the account that currently owns it.
6. The account that submitted the **`NFTokenOfferAccept`** transaction has a different address from the address specified in the `Destination` field of the `sell`/`buy` **`NFTokenOffer`**.

#### 1.5.6.3. Fields

| Field Name        |     Required?      | JSON Type | Internal Type |
| ----------------- | :----------------: | :-------: | :-----------: |
| `TransactionType` | :heavy_check_mark: | `string`  |   `UINT16`    |

Indicates the transaction type **`NFTokenOfferAccept`**. The sequence number of a previous **`NFTokenCreateOffer`** transaction. The integer identifier is `29`.

| Field Name         | Required? | JSON Type | Internal Type |
| ------------------ | :-------: | :-------: | :-----------: |
| `NFTokenSellOffer` |           | `string`  |   `UINT256`   |

Identifies the **`NFTokenOffer`** that offers to sell the **`NFToken`**.

:memo: In direct mode this field is optional, but either `NFTokenSellOffer` or `NFTokenBuyOffer` must be specified. In brokered mode, both `NFTokenSellOffer` and `NFTokenBuyOffer` MUST be specified.

| Field Name        | Required? | JSON Type | Internal Type |
| ----------------- | :-------: | :-------: | :-----------: |
| `NFTokenBuyOffer` |           | `string`  |   `UINT256`   |

Identifies the **`NFTokenOffer`** that offers to buy the **`NFToken`**.

:memo: In direct mode this field is optional, but either `NFTokenSellOffer` or `NFTokenBuyOffer` must be specified. In brokered mode, both `NFTokenSellOffer` and `NFTokenBuyOffer` MUST be specified.

|     Field Name     | Required? |      JSON Type       | Internal Type |
| :----------------: | :-------: | :------------------: | :-----------: |
| `NFTokenBrokerFee` |           | `object` or `string` |   `AMOUNT`    |

This field is only valid in brokered mode. It specifies the amount that the broker will keep as part of their fee for bringing the two offers together; the remaining amount will be sent to the seller of the **`NFToken`** being bought. If specified, the fee must be such that, prior to accounting for the transfer fee charged by the issuer, the amount that the seller would receive is at least as much as the amount indicated in the sell offer.

This functionality is intended to allow the `owner` of an **`NFToken`** to offer their token for sale to a third party broker, who may then attempt to sell the **`NFToken`** for a larger amount, without the broker having to own the **`NFToken`** or custody funds.

:memo: If both offers are for the same asset, it is possible that the order in which funds are transferred might cause a transaction that would succeed to fail due to an apparent lack of funds. To ensure deterministic transaction execution and maximimize the chances of successful execution, this proposal requires that the account attempting to buy the **`NFToken`** is debited first and that funds due to the broker are credited _before_ crediting the seller or issuer.

:note: In brokered mode, The offers referenced by `NFTokenBuyOffer` and `NFTokenSellOffer` must both specify the same `NFTokenID`; that is, both must be for the same **`NFToken`**.

## 1.6. Uniqueness property of the `NFTokenID`

The `NFTokenID` is ensured to be unique by using its `Sequence` number structure, and by imposing a restriction on deleting accounts.

### 1.6.1. NFT `Sequence` Construct

The `Sequence` of an NFT is the lowest 32-bit of its `NFTokenID`. It is computed by adding the `FirstNFTokenSequence` with `MintedNFTokens` to produce a monotonically increasing number.

Adding the `FirstNFTokenSequence` offset prevents the NFT `Sequence` from starting at 0 whenever the issuer recreates their account. This helps to ensure that the `NFTokenID` remains unique.

### 1.6.2. Account Deletion Restriction

An account can only be deleted if `FirstNFTSequence + MintedNFTokens + 256` is less than the current ledger sequence (256 was chosen as a heuristic restriction for account deletion and already exists in the account deletion constraint).

The proposal adds a restriction because simply having the `NFTokenID` is not enough to prevent the issuer from making a duplicate `NFTokenID`. There are rare cases where the authorized minting feature could still allow a duplicate to be made.

Without this restriction, the following example demonstrates how a duplicate NFTokenID can be reproduced through authorized minting:

1. Alice's account sequence is at 1.
2. Bob is Alice's authorized minter.
3. Bob mints 500 NFTs for Alice. The NFTs will have sequences 1-501, as
   NFT sequence is computed by `FirstNFTokenSequence + MintedNFTokens`).
4. Alice deletes her account at ledger 257 (as required by the existing
   `AccountDelete` amendment).
5. Alice re-creates her account at ledger 258.
6. Alice mints an NFT. `FirstNFTokenSequence` initializes to her account
   sequence (258), and `MintedNFTokens` initializes as 0. This
   newly minted NFT would have a sequence number of 258, which is a
   duplicate of what she issued through authorized minting before she
   deleted her account.

## History

This spec, at revision 10, describes XLS-20 with [the `fixNFTokenRemint` amendment](https://xrpl.org/known-amendments.html#fixnftokenremint) active. For earlier versions of this spec, please see [the commit history](https://github.com/XRPLF/XRPL-Standards/commits/master/XLS-0020-non-fungible-tokens/README.md).
