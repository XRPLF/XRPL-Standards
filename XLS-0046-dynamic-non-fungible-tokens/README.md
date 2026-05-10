<pre>
  xls: 46
  title: Dynamic Non Fungible Tokens (dNFTs)
  description: Support for XLS-20 NFTs to modify and upgrade token properties as mutable NFTs
  author: Vet (@xVet), Mayukha Vadari (@mvadari), TeQu (@tequdev)
  proposal-from: https://github.com/XRPLF/XRPL-Standards/discussions/130
  status: Final
  category: Ecosystem
  requires: [XLS-20](../XLS-0020-non-fungible-tokens/README.md)
  created: 2023-08-18
</pre>

## Abstract

This proposal aims to provide support for XLS-20 NFTs to modify/upgrade token properties.

[XLS-20](link to spec) provides [Non-Fungible Token](link to docs) support, these tokens are immutable and don’t allow any changes. Currently NFTs can’t be modified, resulting often in new mints, which leads to ledger bloat that eat valuable resources as well as experimental approaches to use website endpoints to mimic dynamic abilities.

Apart from the use of immutable NFTs, there is a wide range of use cases around dNFTs (Dynamic Non-Fungible Tokens) which are considered mutable NFTs. The goal is to provide both options to developers and users to cover all aspects of non fungibility, while choosing the least invasive approach to achieve this functionality.

## Motivation

Usually, NFTs are typically static in nature. A static NFT refers to an NFT that possesses unchanging and immutable characteristics stored on the blockchain, rendering them unmodifiable. These static NFTs encompass various forms like images, videos, GIF files, music, and unlockable components. For instance, an illustration of a basketball player making a shot into a hoop serves as an example of a static NFT.

On the other hand, `dynamic NFTs`, often abbreviated as dNFTs, represent the next phase in the evolution of the NFT landscape. These `dynamic NFTs` seamlessly integrate the inherent uniqueness of NFTs with the inclusion of dynamic data inputs. These inputs can arise from calculations conducted either on the blockchain or off-chain.

Oracles could supply dynamic real-world data to NFTs. To illustrate, a `dynamic NFT` might showcase real-time updates of a basketball player's performance statistics as they actively play.

## Specification

### 3. New Transactors and Flags

### We will specify the following:

     New Transactor
    	- NFTokenModify

     New Flags
    	- tfMutable

### 3.1 tfMutable

New flags for `NFTokenMint`:

| Flag Name   |  Flag Value  |                               Description                               |
| ----------- | :----------: | :---------------------------------------------------------------------: |
| `tfMutable` | `0x00000010` | `Allow issuer (or an entity authorized by the issuer) to modify “URI”.` |

### 3.2 NFTokenModify

`NFTokenModify` is used to modify the URI property of a NFT:

Transaction-specific Fields

| Field Name        | Required? | JSON Type | Internal Type |
| ----------------- | :-------: | :-------: | :-----------: |
| `TransactionType` |   `✔️`    | `string`  |   `UINT16`    |

Indicates the `account` which is owning the NFT, in case of `Owner` not specified, it's implied that the submitting `account` is also the `Owner` of the NFT.

| Field Name | Required? | JSON Type | Internal Type |
| ---------- | :-------: | :-------: | :-----------: |
| `Owner`    |           | `string`  | `ACCOUNT ID`  |

Indicates the `NFToken` object to be modified.

| Field Name  | Required? | JSON Type | Internal Type |
| ----------- | :-------: | :-------: | :-----------: |
| `NFTokenID` |   `✔️`    | `string`  |   `UINT256`   |

The new `URI` that points to data and/or metadata associated with the NFT.
If a `URI` is omitted then the corresponding `URI` record in the XRP ledger, if present, is removed.

| Field Name | Required? | JSON Type | Internal Type |
| ---------- | :-------: | :-------: | :-----------: |
| `URI`      |           | `string`  |    `BLOB`     |

Example (modify URI):

    {
      "TransactionType": "NFTokenModify",
      "Account": "rHb9CJAWyB4rj91VRWn96DkukG4bwdtyTh",
      "Owner": "rogue5HnPRSszD9CWGSUz8UGHMVwSSKF6",
      "Fee": "10",
      "Sequence": 33,
      “NFTokenID”: “0008C350C182B4F213B82CCFA4C6F59AD76F0AFCFBDF04D5A048C0A300000007",
      "URI": "697066733A2F2F62616679626569636D6E73347A736F6C686C6976346C746D6E356B697062776373637134616C70736D6C6179696970666B73746B736D3472746B652F5665742E706E67",

      ...

      }

If `tfMutable` is not set, executing NFTokenModify should fail!

If `tfMutable` is set, executing NFTokenModify should fail when neither `Issuer` or an `account` authorized via `NFTokenMinter`, according to the specific flag, is executing the transaction.

This approach takes into consideration that `NFToken Flags` are part of the `NFTokenID`, mutating anything that is part of the `NFTokenID` must be avoided.
