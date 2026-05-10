<pre>
  xls: 52
  title: NFTokenMintOffer
  description: Extension to NFTokenMint transaction to allow NFToken Sell Offer creation at the same time as minting
  author: tequ (@tequdev)
  proposal-from: https://github.com/XRPLF/XRPL-Standards/discussions/147
  status: Final
  category: Amendment
  requires: [XLS-20](../XLS-0020-non-fungible-tokens/README.md)
  created: 2023-11-21
</pre>

## Abstract

This proposal extends the minting capabilities of NFToken (XLS-20).

NFToken are not only held by the issuer, but are often distributed or sold by the issuer to others.

XRPL NFToken requires two transactions (`NFTokenMint` and `NFTokenCreateOffer`) to be sent by the issuer before the NFToken can be minted and distributed (or sold).
NFTokenOfferMint extends the existing `NFTokenMint` transaction to allow an **NFToken Sell Offer** to be created at the same time as the NFToken is minted.

NFTokenOfferMint is expected to significantly improve the experience of NFT projects and users.

## Specification

### New `NFTokenMint` Transaction Field

Add 3 new fields to the`NFTokenMint` transaction.

| Field Name    | Required? |     JSON Type     | Internal Type |
| ------------- | :-------: | :---------------: | :-----------: |
| `Amount`      |           | `Currency Amount` |   `AMOUNT`    |
| `Destination` |           |     `string`      |  `AccountID`  |
| `Expiration`  |           |     `number`      |   `UINT32`    |

These fields have the same meaning as the field of the same name used in the `NFTokenCreateOffer` transaction, but the `Amount` field is not a required field.

If the `Amount` field (and the other 2 fields) are not specified, `NFTokenMint` transaction behaves exactly like a previous `NFTokenMint` transaction.

### Creating an `NFTokenOffer`

Since NFToken issuers can only create a sell offer for their NFToken, the `Owner` field is not set and `tfSellNFToken` flag is always set in the `NFTokenOffer` created in an `NFTokenMint` transaction.

In an extended `NFTokenMint` transaction, an `NFTokenOffer` is created when

- `Amount` field is specified.

An error occurs in the following cases

- One or both of `Destination` and `Expiration` fields are specified, but the `Amount` field is not .

### Owner Reserve

The `NFTokenPage` and `NFTokenOffer` reserves will not change, but will create the possibility of up to 2 incremental reserves (NFTokenPage, NFTokenOffer) in an `NFTokenMint` transaction.
