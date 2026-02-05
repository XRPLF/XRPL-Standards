<pre>
  xls: 81
  title: Permissioned DEXes
  description: A permissioned DEX system for the XRPL to enable regulated financial institutions to participate while adhering to compliance requirements
  author: Mayukha Vadari <mvadari@ripple.com>, Shawn Xie <shawnxie@ripple.com>
  proposal-from: https://github.com/XRPLF/XRPL-Standards/discussions/229
  status: Final
  category: Amendment
  requires: [XLS-70](../XLS-0070-credentials/README.md), [XLS-80](../XLS-0080-permissioned-domains/README.md)
  created: 2024-09-12
</pre>

# Permissioned DEXes

## Abstract

Decentralized Exchanges (DEXes) are revolutionizing finance due to their ability to offer significant benefits such as intermediary elimination, lower transaction costs, enhanced security, and user asset custody. These advantages align perfectly with the growing demand for efficient financial systems. However, a major hurdle hinders wider adoption by traditional institutions: the anonymity of a DEX makes it difficult to comply with Anti-Money Laundering (AML) and Know Your Customer (KYC) regulations.

This challenge highlights a critical need for the development of a permissioned system within DEXes. Such a system would allow institutions to adhere to regulations while still benefiting from the core advantages of blockchain technology.

This proposal introduces a permissioned DEX system for the XRPL. By integrating permissioning features directly within the DEX protocol, regulated financial institutions gain the ability to participate in the XRPL's DEX while still adhering to their compliance requirements. This approach avoids the drawbacks of isolated, permissioned tokens or private blockchains, ensuring a vibrant and liquid marketplace that facilitates seamless arbitrage opportunities. Ultimately, this permissioned DEX system paves the way for wider institutional adoption of XRPL, fostering a more inclusive and efficient financial landscape.

## 1. Overview

This proposal builds on top of [XLS-80, Permissioned Domains](https://github.com/XRPLF/XRPL-Standards/tree/master/XLS-0080-permissioned-domains), as Permissioned Domains are needed to handle the permissioning aspect.

We propose:

- Modifying the `Offer` ledger object.
- Modifying the `OfferCreate` transaction.
- Modifying the `Payment` transaction.

This feature will require an amendment, tentatively titled `featurePermissionedDEX`. The the orderbook and pathing-related RPCs will also need to be updated.

### 1.1. Background: The Current State of Permissioning and Compliance on the XRPL

The XRPL has made significant strides toward a compliance-by-design framework, incorporating several features to enhance transparency and control. These tools aim to facilitate regulatory adherence while preserving the platform's decentralized ethos.

They include:

- **Deposit Auth:** Offers granular control over incoming funds, allowing issuers to define specific conditions for accepting deposits.
- **Authorized Trustlines:** Enables precise management of asset trustlines, providing issuers with greater oversight over asset distribution.
- **Clawback:** Provides a mechanism for issuers to reclaim issued assets under specific circumstances, enhancing control and risk mitigation.
- **Freezing:** Allows accounts to be restricted from sending or receiving funds, aiding in compliance with regulatory requirements.
- **Multisign:** Introduces additional layers of authorization, enhancing security and compliance for sensitive transactions.
- **Payment Paths:** Offers flexible transaction routing, which can be leveraged for compliance purposes, such as ensuring funds pass through specific intermediaries.

While these features provide an excellent foundation for compliance, they fall short in one crucial area: the use of the DEX.

### 1.2. Terminology

- **Offer Crossing**: Two offers **cross** if one is selling a token at a price that's actually lower than or equal to the price the other is offering to buy it at.
- **Offer Filling**: Two offers **fill** each other if the trade executes and the sale goes through. Offers can be partially filled, based on the flags (settings) of the offers.
- **Permissioned DEX**: The subset of the DEX that operates within the rules of a specific domain.
- **Open DEX**: The un-permissioned DEX that has no restrictions.
- **Permissioned Orderbook**: An orderbook that operates within the rules of a specific domain.
- **Open Orderbook**: An un-permissioned orderbook that has no restrictions.
- **Permissioned Offer/Payment** or **Closed Offer/Payment**: An offer/cross-currency payment that can only be filled by offers that are a part of a specific domain.
- **Open Offer/Payment** or **Unpermissioned Offer/Payment**: An offer/cross-currency payment that is able to trade on the open DEX or potentially in permissioned DEXes, but doesn't have any restrictions itself.
- **Valid Domain Offer/Payment**: An offer/cross-currency payment that satisfies the rules of a domain (i.e. the account is a domain member). This must be a permissioned offer.

### 1.3. Basic Flow

#### 1.3.1. Initial Setup

- Owen, a domain owner, creates his domain with a set of KYC credentials.
- Tracy, a trader, is operating in Owen's regulatory environment and has strict regulatory requirements - she cannot receive liquidity from non-KYCed accounts. She has one of Owen's accepted KYC credentials, and will only be placing permissioned offers.
- Marko, a market maker, wants to arbitrage offers in Owen's domain, as there is often a significant price difference inside and outside. He obtains one of the KYC credentials that Owen's domain accepts. He will be placing both permissioned _and_ open offers.

#### 1.3.2. Trading Scenario 1

- Tracy places a permissioned offer on the XRP-USD orderbook. There are no other offers on that orderbook that are a part of the domain.
- Marko notices that there is a significant price difference between Tracy's offer and the rest of the orderbook. He now submits a permissioned offer to cross and fill Tracy's offer.

#### 1.3.3. Trading Scenario 2

- Marko has placed open offers on the XRP-EUR orderbook.
- Tracy places an offer on the XRP-EUR orderbook that crosses one of Marko's offers. Her offer cannot be filled by his, since hers is a permissioned offer and his is an open offer.

### 1.4. How Domains Work

A permissioned offer will only be filled by valid domain offers.

An open offer can be filled by any open offer on the open DEX, but cannot be filled by a permissioned offer. Likewise, any permissioned offer cannot be filled by an open offer.

## 2. On-Ledger Object: `Offer`

The `Offer` object tracks an offer placed on the CLOB DEX. This object type already exists on the XRPL, but is being extended as a part of this spec to also support permissioned DEX domains.

### 2.1. Fields

<details>
<summary>

As a reference, [here](https://xrpl.org/docs/references/protocol/ledger-data/ledger-entry-types/offer) are the existing fields for the `Offer` object.

</summary>

| Field Name          | Required? | JSON Type | Internal Type | Description                                                                                                                                   |
| ------------------- | --------- | --------- | ------------- | --------------------------------------------------------------------------------------------------------------------------------------------- |
| `Account`           | ✔️        | `string`  | `AccountID`   | The address of the account that owns this offer.                                                                                              |
| `BookDirectory`     | ✔️        | `string`  | `Hash256`     | The ID of the offer directory that links to this offer.                                                                                       |
| `BookNode`          | ✔️        | `string`  | `UInt64`      | A hint indicating which page of the offer directory links to this entry, in case the directory consists of multiple pages.                    |
| `Expiration`        |           | `number`  | `UInt32`      | Indicates the time after which this offer is considered unfunded.                                                                             |
| `LedgerEntryType`   | ✔️        | `string`  | `UInt16`      | The value `0x006F`, mapped to the string `Offer`, indicates that this is an offer entry.                                                      |
| `OwnerNode`         | ✔️        | `string`  | `UInt64`      | A hint indicating which page of the owner directory links to this entry, in case the directory consists of multiple pages.                    |
| `PreviousTxnID`     | ✔️        | `string`  | `Hash256`     | The identifying hash of the transaction that most recently modified this entry.                                                               |
| `PreviousTxnLgrSeq` | ✔️        | `number`  | `UInt32`      | The ledger index that contains the transaction that most recently modified this object.                                                       |
| `Sequence`          | ✔️        | `number`  | `UInt32`      | The `Sequence` value of the `OfferCreate` transaction that created this offer. Used in combination with the `Account` to identify this offer. |
| `TakerPays`         | ✔️        | `object`  | `Amount`      | The remaining amount and type of currency requested by the offer creator.                                                                     |
| `TakerGets`         | ✔️        | `object`  | `Amount`      | The remaining amount and type of currency being provided by the offer creator.                                                                |

</details>

This spec proposes adding the following fields:

| Field Name        | Required? | JSON Type | Internal Type | Description                                                                                                                     |
| ----------------- | --------- | --------- | ------------- | ------------------------------------------------------------------------------------------------------------------------------- |
| `DomainID`        |           | `string`  | `Hash256`     | The domain that the offer must be a part of.                                                                                    |
| `AdditionalBooks` |           | `array`   | `STArray`     | An additional list of order book directories that this offer belongs to. Currently this field only applicable to hybrid offers. |

One new flag `lsfHybrid` is introduced:

> |  Flag Name  |  Flag Value  | Description                                                                              |
> | :---------: | :----------: | :--------------------------------------------------------------------------------------- |
> | `lsfHybrid` | `0x00040000` | Indicates the offer is hybrid. (meaning it is part of both a domain and open order book) |

#### 2.1.1. `DomainID`

A permissioned offer has a `DomainID` field included.

An open offer does not include a `DomainID` field.

#### 2.1.2. `AdditionalBooks`

This is an array of inner objects referencing a specific page of an offer directory, and is currently only used if the offer is hybrid (which links to two directories).

> Note: For a hybrid offer, its domain directory is stored in the outer `BookDirectory` and `BookNode`, and its open directory is stored in `AdditionalBooks`.

| Field Name      | Required? | JSON Type | Internal Type | Description                                                                                                                |
| --------------- | --------- | --------- | ------------- | -------------------------------------------------------------------------------------------------------------------------- |
| `BookDirectory` | ✔️        | `string`  | `Hash256`     | The ID of the offer directory that links to this offer.                                                                    |
| `BookNode`      | ✔️        | `string`  | `UInt64`      | A hint indicating which page of the offer directory links to this entry, in case the directory consists of multiple pages. |

### 2.2. Offer Invalidity

A permissioned offer on the orderbook can become invalid if:

- The domain specified by the `DomainID` field is deleted.
- The credential that allows the offer's owner to be a member of the domain expires or is deleted.

An invalid offer will be processed similarly to an unfunded offer, where it is deleted if and when processed/crossed.

## 3. On-Ledger Object: `DirectoryNode`

The `Offer` object tracks an offer placed on the CLOB DEX.

The `DirectoryNode` ledger entry type provides a list of links to other entries in the ledger's state data. A single conceptual _Directory_ takes the form of a doubly linked list, with one or more `DirectoryNode` entries each containing up to 32 [IDs of other entries](https://xrpl.org/docs/references/protocol/ledger-data/common-fields/). The first `DirectoryNode` entry is called the root of the directory, and all entries other than the root can be added or deleted as necessary.

This object type already exists on the XRPL, but is being extended as a part of this spec to also support permissioned DEX domains.

There are three types of [directories](https://xrpl.org/docs/references/protocol/ledger-data/ledger-entry-types/directorynode): owner directories (for the objects an account owns), offer directories (for offers in the orderbook), and NFT offer directories (for NFT offers). The proposed modifications only concern offer directories.

### 3.1. Fields

<details>
<summary>

As a reference, [here](https://xrpl.org/docs/references/protocol/ledger-data/ledger-entry-types/directorynode#directorynode-fields) are the existing fields for the `DirectoryNode` object.

</summary>

| Field Name          | Required? | JSON Type | Internal Type | Description                                                                                                                                        |
| ------------------- | --------- | --------- | ------------- | -------------------------------------------------------------------------------------------------------------------------------------------------- |
| `Flags`             | ✔️        | `number`  | `UInt32`      | A bit-map of boolean flags enabled for this object. Currently, the protocol defines no flags for `DirectoryNode` objects. The value is always `0`. |
| `Indexes`           | ✔️        | `array`   | `Vector256`   | The contents of this directory: an array of IDs of other objects.                                                                                  |
| `IndexNext`         |           | `number`  | `UInt64`      | If this directory consists of multiple pages, this ID links to the next object in the chain, wrapping around at the end.                           |
| `IndexPrevious`     |           | `number`  | `UInt64`      | If this directory consists of multiple pages, this ID links to the previous object in the chain, wrapping around at the beginning.                 |
| `LedgerEntryType`   | ✔️        | `string`  | `UInt16`      | The value `0x0064`, mapped to the string `DirectoryNode`, indicates that this object is part of a directory.                                       |
| `RootIndex`         | ✔️        | `string`  | `Hash256`     | The ID of root object for this directory.                                                                                                          |
| `TakerGetsCurrency` | ✔️        | `string`  | `Hash160`     | The currency code of the `TakerGets` amount from the offers in this directory.                                                                     |
| `TakerGetsIssuer`   | ✔️        | `string`  | `Hash160`     | The issuer of the `TakerGets` amount from the offers in this directory.                                                                            |
| `TakerPaysCurrency` | ✔️        | `string`  | `Hash160`     | The currency code of the `TakerPays` amount from the offers in this directory.                                                                     |
| `TakerPaysIssuer`   | ✔️        | `string`  | `Hash160`     | The issuer of the `TakerPays` amount from the offers in this directory.                                                                            |

</details>

This spec proposes these additions:

| Field Name | Required? | JSON Type | Internal Type | Description                                       |
| ---------- | --------- | --------- | ------------- | ------------------------------------------------- |
| `DomainID` |           | `string`  | `Hash256`     | The domain that the offer directory is a part of. |

#### 3.1.1. `DomainID`

A domain has its own set of orderbooks.

### 3.2. Object ID

_The proposed modification is in bold._

There are three different formulas for creating the ID of a DirectoryNode, depending on which of the following the DirectoryNode represents:

- The first page (also called the root) of an Owner or NFT Offer directory
- The first page of an Offer directory
- Later pages of either type

The first page of an Offer directory has a special ID: the higher 192 bits define the order book, and the remaining 64 bits define the exchange rate of the offers in that directory. (The ID is big-endian, so the book is in the more significant bits, which come first, and the quality is in the less significant bits which come last.) This provides a way to iterate through an order book from best offers to worst. Specifically: the first 192 bits are the first 192 bits of the [SHA-512Half](https://xrpl.org/docs/references/protocol/data-types/basic-data-types#hashes) of the following values, concatenated in order:

- The Book directory space key (`0x0042`)
- The 160-bit currency code from the `TakerPaysCurrency`
- The 160-bit currency code from the `TakerGetsCurrency`
- The AccountID from the `TakerPaysIssuer`
- The AccountID from the `TakerGetsIssuer`
- **The `DomainID` of the orderbook, if applicable**

The lower 64 bits of an Offer directory's ID represent the `TakerPays` amount divided by `TakerGets` amount from the offer(s) in that directory as a 64-bit number in the XRP Ledger's internal amount format.

If the DirectoryNode is not the first page in the directory, it has an ID that is the [SHA-512Half](https://xrpl.org/docs/references/protocol/data-types/basic-data-types#hashes) of the following values, concatenated in order:

- The DirectoryNode space key (`0x0064`)
- The ID of the root DirectoryNode
- The page number of this object. (Since 0 is the root DirectoryNode, this value is an integer 1 or higher.)

## 4. Transaction: `OfferCreate`

The `OfferCreate` transaction creates an offer on the CLOB DEX. This transaction type already exists on the XRPL, but is being extended as a part of this spec to also support permissioned DEX domains.

### 4.1. Fields

<details>
<summary>

As a reference, [here](https://xrpl.org/docs/references/protocol/transactions/types/offercreate) are the existing fields for the `OfferCreate` transaction.

</summary>

| Field Name      | Required? | JSON Type | Internal Type | Description                                                                        |
| --------------- | --------- | --------- | ------------- | ---------------------------------------------------------------------------------- |
| `Expiration`    |           | `number`  | `UInt32`      | Time after which the offer is no longer active, in seconds since the Ripple Epoch. |
| `OfferSequence` |           | `number`  | `UInt32`      | An offer to delete first, specified in the same way as `OfferCancel`.              |
| `TakerGets`     | ✔️        | `string`  | `Amount`      | The amount and type of currency being sold.                                        |
| `TakerPays`     | ✔️        | `string`  | `Amount`      | The amount and type of currency being bought.                                      |

</details>

We propose a new field:

| Field Name | Required? | JSON Type | Internal Type | Description                                  |
| ---------- | --------- | --------- | ------------- | -------------------------------------------- |
| `DomainID` |           | `string`  | `Hash256`     | The domain that the offer must be a part of. |

#### 4.1.1. `Flags`

This spec proposes an additional flag, `tfHybrid` , to indicate whether the offer should consider only the `DomainID`'s Permissioned DEX or also include the open DEX.

> | Flag Name  |  Flag Value  | Description                                                                                   |
> | :--------: | :----------: | :-------------------------------------------------------------------------------------------- |
> | `tfHybrid` | `0x00100000` | Indicates the offer is hybrid. This flag cannot be set if the offer doesn't have a `DomainID` |

### 4.2. Failure Conditions

The existing set of failure conditions for `OfferCreate` will continue to exist.

The following will be added:

- The domain doesn't exist.
- The domain offer creater is neither part of the domain or the domain owner.
- A hybrid offer with flag `tfHybrid` is attempted to be created without specifying the `DomainID`.

### 4.3. State Changes

The existing set of state changes for `OfferCreate` will continue to exist.

If the `DomainID` is included in the `OfferCreate` transaction, the DEX will use the domain-specific orderbook to process the offer. This applies to hybrid offers as well - hybrid offers will only use the domain-specific order book by default for offer crossing in the execution of that transaction (it can be crossed by open offers later).

If the offer owner is no longer part of the domain, the offer will be treated as "unfunded" whenever it is attempted to be crossed. Like existing unfunded offers, it will be automatically removed.

## 5. Transaction: `Payment`

A `Payment` transaction represents a transfer of value from one account to another, and can involve currency conversions and crossing the orderbook. This transaction type already exists on the XRPL, but is being extended as a part of this spec to also support permissioned DEX domains.

### 5.1. Fields

<details>
<summary>

As a reference, [here](https://xrpl.org/docs/references/protocol/transactions/types/payment) are the existing fields for the `Payment` transaction.

</summary>

| Field Name       | Required? | JSON Type            | Internal Type | Description                                                                                                                                                                                                                                                                                                                                                                                                                          |
| ---------------- | --------- | -------------------- | ------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `Amount`         | ✔️        | `string`             | `Amount`      | The maximum amount of currency to deliver. For non-XRP amounts, the nested field names MUST be lower-case. If the `tfPartialPayment` flag is set, deliver _up to_ this amount instead.                                                                                                                                                                                                                                               |
| `DeliverMin`     |           | `string`             | `Amount`      | The minimum amount of destination currency this transaction should deliver. Only valid if this is a partial payment. For non-XRP amounts, the nested field names are lower-case.                                                                                                                                                                                                                                                     |
| `Destination`    | ✔️        | `string`             | `AccountID`   | The unique address of the account receiving the payment.                                                                                                                                                                                                                                                                                                                                                                             |
| `DestinationTag` |           | `number`             | `UInt32`      | An arbitrary tag that identifies the reason for the payment to the destination, or a hosted recipient to pay.                                                                                                                                                                                                                                                                                                                        |
| `InvoiceID`      |           | `string`             | `Hash256`     | An arbitrary 256-bit hash representing a specific reason or identifier for this payment.                                                                                                                                                                                                                                                                                                                                             |
| `Paths`          |           | `array`              | `PathSet`     | Array of payment paths to be used for this transaction. Must be omitted for XRP-to-XRP transactions.                                                                                                                                                                                                                                                                                                                                 |
| `SendMax`        |           | `string` or `object` | `Amount`      | Highest amount of source currency this transaction is allowed to cost, including transfer fees, exchange rates, and [slippage](http://en.wikipedia.org/wiki/Slippage_%28finance%29). Does not include the XRP destroyed as a cost for submitting the transaction. For non-XRP amounts, the nested field names MUST be lower-case. Must be supplied for cross-currency/cross-issue payments. Must be omitted for XRP-to-XRP payments. |

</details>

We propose these additions:

| Field Name | Required? | JSON Type | Internal Type | Description                                                                                        |
| ---------- | --------- | --------- | ------------- | -------------------------------------------------------------------------------------------------- |
| `DomainID` |           | `string`  | `Hash256`     | The domain the sender intends to use. Both the sender and destination must be part of this domain. |

#### 5.1.1. `DomainID`

The `DomainID` can be included if the sender intends it to be a cross-currency payment (i.e. if the payment is going to interact with the DEX). The domain will only play it's role if there is a path that crossing an orderbook.

> Note: it's still possible that `DomainID` is included but the payment does not interact with DEX, it simply means that the `DomainID` will be ignored during payment paths.

#### 5.2. Consuming Hybrid offers

An existing hybrid offer can be consumed like a regular offer on the ledger. To consume a hybrid offer using the open orderbook, omit the `DomainID` from `Payment` and include a valid `path` involving the hybrid offer. To consume a hybrid offer using domain orderbook, include the `DomainID` in `Payment`.

### 5.3. Failure Conditions

The existing set of failure conditions for `Payment` will continue to exist.

There will also be the following in addition, if the `DomainID` is included:

- The domain doesn't exist.
- The `Account` or `Destination` is not a domain member.
- The offer owner during a payment path is no longer part of the domain (if there are no other valid offers).
- The paths do not satisfy the domain's rules (e.g. a path includes an account that isn't a part of the domain).

### 5.4. State Changes

The existing set of state changes for a successful `Payment` transaction will continue to exist. Also, this transaction will not delete expired credentials as it traverses offers on the permissioned order book.

## 6. RPC: `book_offers`

The [`book_offers` RPC method](https://xrpl.org/book_offers.html) already exists on the XRPL. This proposal suggests some modifications to also support permissioned DEX domains.

### 6.1. Request Fields

As a reference, here are the fields that `book_offers` currently accepts:

| Field Name     | Required? | JSON Type            | Description                                                                                                                                                                                                 |
| -------------- | --------- | -------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `taker_gets`   | ✔️        | `object`             | The asset the account taking the Offer would receive, as a currency without an amount.                                                                                                                      |
| `taker_pays`   | ✔️        | `object`             | The asset the account taking the Offer would pay, as a currency without an amount.                                                                                                                          |
| `ledger_hash`  |           | `string`             | A 20-byte hex string for the ledger version to use.                                                                                                                                                         |
| `ledger_index` |           | `number` or `string` | The ledger index of the ledger to use, or a shortcut string to choose a ledger automatically.                                                                                                               |
| `limit`        |           | `number`             | The maximum number of Offers to return. The response may include fewer results.                                                                                                                             |
| `taker`        |           | `string`             | The address of an account to use as a perspective. The response includes this account's offers even if they are unfunded. (You can use this to see what offers are above or below yours in the order book.) |

This proposal puts forward the following addition:

| Field Name | Required? | JSON Type | Description                                                                                                                                                                                                                                                                                       |
| ---------- | --------- | --------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `domain`   |           | `string`  | The object ID of a `PermissionedDomain` object. If this field is provided, the response will include only valid domain offers associated with that specific domain. If omitted, the response will include only hybrid and open offers for the trading pair, excluding all domain-specific offers. |

### 6.2. Response Fields

This proposal does not suggest any changes to the response fields. As a reference, here are the fields that `book_offers` currently returns:

| Field Name             | Always Present? | JSON Type            | Description                                                                                              |
| ---------------------- | --------------- | -------------------- | -------------------------------------------------------------------------------------------------------- |
| `ledger_current_index` |                 | `number` or `string` | The ledger index of the current in-progress ledger version, which was used to retrieve this information. |
| `ledger_index`         |                 | `number` or `string` | The ledger index of the ledger version that was used when retrieving this data, as requested.            |
| `ledger_hash`          |                 | `string`             | The identifying hash of the ledger version that was used when retrieving this data, as requested.        |
| `offers`               | ✔️              | `array`              | Array of offer objects, each of which has the fields of an Offer object.                                 |

## 7. RPC: `path_find`

The [`path_find` RPC method](https://xrpl.org/path_find.html) already exists on the XRPL. This proposal suggests some modifications to also support permissioned DEX domains.

Only the `create` subcommand will be affected.

### 7.1. Request Fields

As a reference, here are the fields that the `path_find` `create` subcommand currently accepts:

| Field Name            | Required? | JSON Type            | Description                                                                                                                                                                                                                   |
| --------------------- | --------- | -------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `subcommand`          | ✔️        | `string`             | Use `"create"` to send the create sub-command                                                                                                                                                                                 |
| `source_account`      | ✔️        | `string`             | The address of the account to find a path from. (In other words, the account that would be sending a payment.)                                                                                                                |
| `destination_account` | ✔️        | `string`             | The address of the account to find a path to. (In other words, the account that would receive a payment.)                                                                                                                     |
| `destination_amount`  | ✔️        | `string` or `object` | The currency amount that the destination account would receive in a transaction.                                                                                                                                              |
| `send_max`            |           | `string` or `object` | The currency amount that would be spent in the transaction.                                                                                                                                                                   |
| `paths`               |           | `array`              | Array of arrays of objects, representing payment paths to check. You can use this to keep updated on changes to particular paths you already know about, or to check the overall cost to make a payment along a certain path. |

This proposal puts forward the following addition:

| Field Name | Required? | JSON Type | Description                                                                                                                        |
| ---------- | --------- | --------- | ---------------------------------------------------------------------------------------------------------------------------------- |
| `domain`   |           | `string`  | The object ID of a `PermissionedDomain` object. If this field is included, then only valid paths for this domain will be returned. |

### 7.2. Response Fields

As a reference, here are the fields that `path_find` currently returns:

| Field Name            | Always Present? | JSON Type            | Description                                                                                                                                                                                                                                                                                                                                              |
| --------------------- | --------------- | -------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `alternatives`        | ✔️              | `array`              | An array of objects with suggested paths to take, as described below. If empty, then no paths were found connecting the source and destination accounts.                                                                                                                                                                                                 |
| `destination_account` | ✔️              | `string`             | The address of the account that would receive a transaction.                                                                                                                                                                                                                                                                                             |
| `destination_amount`  | ✔️              | `string` or `object` | The currency amount that the destination would receive in a transaction.                                                                                                                                                                                                                                                                                 |
| `source_account`      | ✔️              | `string`             | The address that would send a transaction.                                                                                                                                                                                                                                                                                                               |
| `full_reply`          | ✔️              | `boolean`            | If `false`, this is the result of an incomplete search. A later reply may have a better path. If `true`, then this is the best path found. (It is still theoretically possible that a better path could exist, but `rippled` won't find it.) Until you close the pathfinding request, `rippled` continues to send updates each time a new ledger closes. |

This proposal puts forward the following addition:

| Field Name | Required? | JSON Type | Description                                                                                      |
| ---------- | --------- | --------- | ------------------------------------------------------------------------------------------------ |
| `domain`   |           | `string`  | The object ID of a `PermissionedDomain` object, if the orderbook shown is for a specific domain. |

## 8. RPC: `ripple_path_find`

The [`ripple_path_find` RPC method](https://xrpl.org/ripple_path_find.html) already exists on the XRPL. This proposal suggests some modifications to also support permissioned DEX domains.

### 8.1. Request Fields

As a reference, here are the fields that `ripple_path_find` currently accepts:

| Field Name            | Required? | JSON Type            | Description                                                                                                                                                                                                                 |
| --------------------- | --------- | -------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `source_account`      | ✔️        | `string`             | The address of the account that would send funds in a transaction                                                                                                                                                           |
| `destination_account` | ✔️        | `string`             | The address of the account that would receive funds in a transaction                                                                                                                                                        |
| `destination_amount`  | ✔️        | `string` or `object` | The currency amount that the destination account would receive in a transaction.                                                                                                                                            |
| `send_max`            |           | `string` or `object` | The currency amount that would be spent in the transaction. Cannot be used with `source_currencies`.                                                                                                                        |
| `source_currencies`   |           | `array`              | An array of currencies that the source account might want to spend. Each entry in the array should be a JSON object with a mandatory `currency` field and optional `issuer` field, like how currency amounts are specified. |
| `ledger_hash`         |           | `string`             | A 20-byte hex string for the ledger version to use.                                                                                                                                                                         |
| `ledger_index`        |           | `string` or `number` | The ledger index of the ledger to use, or a shortcut string to choose a ledger automatically.                                                                                                                               |

This proposal puts forward the following addition:

| Field Name | Required? | JSON Type | Description                                                                                                                        |
| ---------- | --------- | --------- | ---------------------------------------------------------------------------------------------------------------------------------- |
| `domain`   |           | `string`  | The object ID of a `PermissionedDomain` object. If this field is included, then only valid paths for this domain will be returned. |

### 8.2. Response Fields

This proposal does not suggest any changes to the response fields. As a reference, here are the fields that `ripple_path_find` currently returns:

| Field Name               | Always Present? | JSON Type | Description                                                                                                                                            |
| ------------------------ | --------------- | --------- | ------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `alternatives`           | ✔️              | `array`   | An array of objects with possible paths to take, as described below. If empty, then there are no paths connecting the source and destination accounts. |
| `destination_account`    | ✔️              | `string`  | The address of the account that would receive a payment transaction.                                                                                   |
| `destination_currencies` | ✔️              | `array`   | Array of strings representing the currencies that the destination accepts.                                                                             |

## 9. RPC: `books` Subscription

The [`books` subscription option](https://xrpl.org/docs/references/http-websocket-apis/public-api-methods/subscription-methods/subscribe#request-format) already exists on the XRPL. This proposal suggests some modifications to also support permissioned DEX domains.

### 9.1. Request Fields

As a reference, here are the fields that `books` currently accepts:

| Field Name   | Required? | JSON Type | Description                                                                                                                   |
| ------------ | --------- | --------- | ----------------------------------------------------------------------------------------------------------------------------- |
| `taker_gets` | ✔️        | `object`  | Specification of which currency the account taking the Offer would receive.                                                   |
| `taker_pays` | ✔️        | `object`  | Specification of which currency the account taking the Offer would pay.                                                       |
| `taker`      | ✔️        | `string`  | Unique account address to use as a perspective for viewing offers. (This affects the funding status and fees of Offers.)      |
| `snapshot`   |           | `boolean` | If `true`, return the current state of the order book once when you subscribe before sending updates. The default is `false`. |
| `both`       |           | `boolean` | If `true`, return both sides of the order book. The default is `false`.                                                       |

This proposal puts forward the following addition:

| Field Name | Required? | JSON Type | Description                                                                                                                                                       |
| ---------- | --------- | --------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `domain`   |           | `string`  | The object ID of a `PermissionedDomain` object. If this field is included, then the offers will be filtered to only show the valid domain offers for that domain. |

### 9.2. Response Fields

This proposal does not suggest any changes to the response fields. As a reference, here are the fields that the [`books` subscription currently returns](https://xrpl.org/docs/references/http-websocket-apis/public-api-methods/subscription-methods/subscribe#order-book-streams) (as an array):

| Field Name              | Required? | JSON Type | Description                                                                                                                                                 |
| ----------------------- | --------- | --------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `type`                  | ✔️        | `string`  | `transaction` indicates this is the notification of a transaction stream, which could come from several possible streams.                                   |
| `engine_result`         | ✔️        | `string`  | String transaction result code.                                                                                                                             |
| `engine_result_code`    | ✔️        | `number`  | Numeric transaction response code, if applicable.                                                                                                           |
| `engine_result_message` | ✔️        | `string`  | Human-readable explanation for the transaction response.                                                                                                    |
| `ledger_hash`           | ✔️        | `string`  | The identifying hash of the ledger version that includes this transaction.                                                                                  |
| `ledger_index`          | ✔️        | `number`  | The ledger index of the ledger version that includes this transaction.                                                                                      |
| `meta`                  | ✔️        | `object`  | The transaction metadata, which shows the exact outcome of the transaction in detail.                                                                       |
| `transaction`           | ✔️        | `object`  | The definition of the transaction in JSON format.                                                                                                           |
| `validated`             | ✔️        | `boolean` | If `true`, this transaction is included in a validated ledger and its outcome is final. Responses from the `transaction` stream should always be validated. |

## 10. RPC: `book_changes`

The [`book_changes` RPC method](https://xrpl.org/docs/references/http-websocket-apis/public-api-methods/path-and-order-book-methods/book_changes) already exists on the XRPL. This proposal suggests some modifications to also support permissioned DEX domains.

These changes also apply to the [`book_changes` subscription stream](https://xrpl.org/docs/references/http-websocket-apis/public-api-methods/subscription-methods/subscribe#book-changes-stream).

### 10.1. Request Fields

This proposal does not suggest any changes to the request fields. As a reference, here are the fields that `book_changes` currently accepts:

| Field Name     | Required? | JSON Type | Description                                                                                                               |
| -------------- | --------- | --------- | ------------------------------------------------------------------------------------------------------------------------- |
| `ledger_hash`  |           | `string`  | A 32-byte hex string for the ledger version to use.                                                                       |
| `ledger_index` |           | `string`  | The ledger index of the ledger to use, or a shortcut string to choose a ledger automatically. The default is `validated`. |

### 10.2. Response Fields

As a reference, here are the fields that the [`book_changes` subscription currently returns](https://xrpl.org/docs/references/http-websocket-apis/public-api-methods/subscription-methods/subscribe#book-changes-stream):

This proposal puts forward the following addition:

| Field Name | Required? | JSON Type | Description                                                                                         |
| ---------- | --------- | --------- | --------------------------------------------------------------------------------------------------- |
| `domain`   |           | `string`  | The object ID of a `PermissionedDomain` object, if the orderbook changes are for a specific domain. |

## 11. Examples

These examples will be using the following domain:

```typescript
{
  Owner: "rOWEN......",
  Sequence: 5,
  AcceptedCredentials: [
    Credential: {
      Issuer: "rISABEL......",
      CredentialType: "123ABC"
    }
  ]
}
```

The domain ID will be `ABCDEF1234567890`.

Both Tracy and Marko have a `123ABC` credential from Isabel.

### 11.1. Placing a Permissioned Offer

In this sample `OfferCreate` transaction, Tracy is trading USD for EUR within Owen's domain.

```typescript
{
  TransactionType: "OfferCreate",
  Account: "rTRACY......",
  TakerGets: {
    currency: "USD",
    issuer: "rUSDISSUER.......",
    value: "11"
  },
  TakerPays: {
    currency: "EUR",
    issuer: "rEURISSUER......."
    value: "10"
  },
  DomainID: "ABCDEF1234567890",
  Fee: "12",
  Sequence: 8
}
```

### 11.2. Placing an Unpermissioned Offer

In this sample `OfferCreate` transaction, Marko is trading EUR for USD on the open USD-EUR orderbook. This offer **will not cross** Tracy's offer, since Tracy's offer is inside the domain.

```typescript
{
  TransactionType: "OfferCreate",
  Account: "rMARKO......",
  TakerGets: {
    currency: "EUR",
    issuer: "rEURISSUER.......",
    value: "10"
  },
  TakerPays: {
    currency: "USD",
    issuer: "rUSDISSUER......."
    value: "11"
  },
  Fee: "12",
  Sequence: 3
}
```

## 12. Invariants

No permissioned offer with a `DomainID` field will be filled by:

- An invalid domain offer.
- An offer from a different domain.
- An open offer.

No permissioned offer will be placed in:

- An orderbook for a different domain.
- The open orderbook.

No open offer will be placed in a permissioned orderbook.

No open offer will be filled by a permissioned offer.

## 13. Security

The trust assumptions are the same as with [permissioned domains](https://github.com/XRPLF/XRPL-Standards/tree/master/XLS-0080-permissioned-domains#7-security).

# Appendix

## Appendix A: FAQ

### A.1: How are AMMs handled?

AMMs are not explicitly supported within permissioned DEXes in this proposal. They could be added to permissioned DEXes in a future proposal.

### A.2: How will performance/TPS be affected from all these additional checks?

Performance tests will need to be conducted once the implementation is done. The spec may be modified if such tests show serious performance reduction.

### A.3: Why do you need a domain? Why not just indicate what credentials you accept on the offer itself?

It's much easier to specify a single domain instead of a list of credentials every time, especially since using an incorrect list of credentials would result in accessing a different orderbook.

### A.4: Will an account with Deposit Authorization enabled be forced to use Permissioned DEXes?

No.

### A.5: Can NFT offers use domains?

This proposal does not include support for NFT offers in domains. However, that could be added later.

### A.6: Can an offer be part of multiple domains?

No, multiple offers would need to be placed for it to be in multiple domains.

### A.7: Can direct IOU payments be permissioned?

No, because they don't go through the DEX. The issuer and destination can be directly verified for compliance and trust.

### A.8: Why doesn't Payment transaction delete expired credentials?

Each domain can have up to 10 credentials. This means that when a payment traverses the order book, it could potentially delete up to 10 credential objects for each offer. This would substantially increase the transaction metadata size and could impact ledger throughput. Adding this functionality would require additional performance evaluation.

## Appendix B: Alternate Designs

The Platonic ideal design would involve one orderbook per pair of assets. The trader indicates what domain they want to participate in, and the DEX automatically figures out what offers are okay for that domain to accept and what offers are not, based on the contents of the offer and the account that placed it.

This was essentially one design considered, which involved all of the offers staying in one orderbook. If an offer needed to be in a domain, each offer that crossed it would be checked for offer membership individually (in the same way that offers are checked on whether they're funded). This idea was scrapped due to performance concerns - a permissioned offer might have to iterate through the whole orderbook before finding a matching offer (if one exists).
