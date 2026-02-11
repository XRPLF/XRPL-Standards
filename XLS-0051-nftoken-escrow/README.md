<pre>
  xls: 51
  title: NFToken Escrows
  description: Extension to Escrow functionality to support escrowing NFTokens
  author: Mayukha Vadari (@mvadari)
  proposal-from: https://github.com/XRPLF/XRPL-Standards/discussions/146
  status: Stagnant
  category: Amendment
  created: 2023-11-17
</pre>

# NFToken Escrows

## Abstract

The XRP Ledger currently only supports escrows for one type of token: XRP. Now that XLS-20 is live on the network and there are almost 4 million NFTs on the ledger, users may want to also be able to put their NFTs in an escrow, just as they would with their funds.

## 1. Overview

This spec proposes modifications to one existing on-ledger object and one existing transaction:

- `Escrow` ledger object
- `EscrowCreate` transaction

This change will require an amendment, tentatively called `featureNFTokenEscrow`.

## 2. On-Ledger Object: `Escrow`

The [`Escrow` object](https://xrpl.org/escrow-object.html) already exists on the XRPL. We propose a slight modification to support NFT escrows.

### 2.1. Fields

As a reference, these are the existing escrow object fields.

| Field Name               | Required? | JSON Type | Internal Type |
| ------------------------ | --------- | --------- | ------------- |
| `LedgerIndex`            | ✔️        | `string`  | `HASH256`     |
| `LedgerEntryType`        | ✔️        | `string`  | `UINT16`      |
| `Owner`                  | ✔️        | `string`  | `AccountID`   |
| `OwnerNode`              | ✔️        | `string`  | `UInt32`      |
| `Amount`                 | ✔️        | `Amount`  | `Amount`      |
| `Condition`              |           | `string`  | `Blob`        |
| `CancelAfter`            |           | `number`  | `UInt32`      |
| `FinishAfter`            |           | `number`  | `UInt32`      |
| `Destination`            | ✔️        | `string`  | `AccountID`   |
| `DestinationNode`        | ✔️        | `string`  | `UInt32`      |
| `DestinationTag`         |           | `number`  | `UInt32`      |
| `PreviousTxnId`          | ✔️        | `string`  | `HASH256`     |
| `PreviousLedgerSequence` | ✔️        | `number`  | `UInt32`      |
| `SourceTag`              |           | `number`  | `UInt32`      |

We propose these modifications:

| Field Name | Required? | JSON Type | Internal Type |
| ---------- | --------- | --------- | ------------- |
| `Amount`   |           | `Amount`  | `Amount`      |
| `NFTokens` |           | `array`   | `STArray`     |

#### 2.1.1. `Amount`

The `Amount` field is still used as it currently is, but it is now optional, to support escrows that only hold NFTs. An `Escrow` object must have an `Amount` field and/or an `NFTokens` field.

#### 2.1.2. `NFTokens`

The NFTs that are in the escrow. One escrow can hold up to 32 NFTs, equivalent to one `NFTokenPage`.

NFTs stored in an escrow cannot be burned or [modified](../XLS-0046-dynamic-non-fungible-tokens/README.md).

## 3. Transaction: `EscrowCreate`

The [`EscrowCreate` transaction](https://xrpl.org/escrowcreate.html) already exists on the XRPL. We propose a slight modification to support NFT escrows.

### 3.1. Fields

As a reference, these are the existing `EscrowCreate` fields:

| Field Name        | Required? | JSON Type | Internal Type |
| ----------------- | --------- | --------- | ------------- |
| `TransactionType` | ✔️        | `string`  | `UInt16`      |
| `Account`         | ✔️        | `string`  | `AccountID`   |
| `Amount`          | ✔️        | `Amount`  | `Amount`      |
| `Destination`     | ✔️        | `string`  | `AccountID`   |
| `Condition`       |           | `string`  | `Blob`        |
| `CancelAfter`     |           | `number`  | `UInt32`      |
| `FinishAfter`     |           | `number`  | `UInt32`      |
| `SourceTag`       |           | `number`  | `UInt32`      |
| `DestinationTag`  |           | `number`  | `UInt32`      |

We propose these modifications:
| Field Name | Required? | JSON Type | Internal Type |
|------------|-----------|-----------|---------------|
|`Amount`| |`Amount`|`Amount`|
|`NFTokenIDs`| |`array`|`STArray`|

#### 3.1.1. `Amount`

The `Amount` field is still used as it currently is, but it is now optional, to support escrows that only hold NFTs. An `EscrowCreate` transaction must have an `Amount` field and/or an `NFTokens` field.

#### 3.1.2. `NFTokenIDs`

This field contains the `NFTokenID`s of the `NFToken`s that the user wants to put in an escrow. There can be up to 32 NFTs in an escrow.

# Appendix

## Appendix A: FAQ

### A.1: Why not use a separate `NFTokenEscrow` object?

That felt like an unnecessary complication and would involve a lot of repeated code.

[//]: # "Also, I didn't want to rewrite out every part of the current escrow implementation in the spec"

### A.2: Can I put XRP and NFTs in the same escrow?

Yes.

### A.3: Why is this so much simpler than for issued currency escrows?

The complication with issued currencies is that they must be held by accounts in [trustlines](https://xrpl.org/trust-lines-and-issuing.html). There is currently no way for a ledger object (such as an escrow) to own another ledger object (such as a trustline).

NFTs have no such requirement - all that defines an NFT is the `NFTokenID` and the `URI`, which can easily be held by an object instead of an account.
