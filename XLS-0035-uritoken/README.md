<pre>
  xls: 35
  title: URITokens
  description: Lightweight first-class NFTs for XRPL Protocol Chains
  author: Richard Holland (@RichardAH), Wietse Wind (@WietseWind)
  proposal-from: https://github.com/XRPLF/XRPL-Standards/discussions/89
  status: Draft
  category: Amendment
  created: 2023-02-09
</pre>

# XLS-35 URITokens — Lightweight first-class NFTs for XRPL Protocol Chains

# Problem Statement

XLS-20 is a Non-Fungible Token standard that is currently active and in-use on the XRP Ledger main-net. Despite this, many developers and users of the XRPL remain unsatisfied by its complexity, unusual edge-cases, lack of first-class object NFTs, and general difficulty to understand and write integrations for. We therefore propose a light-weight alternative: _URIToken_.

# Amendment

The URIToken Amendment provides a lightweight alternative to XLS20 suitable for both main-net and side-chains.

The amendment adds:

A new type of ledger object: `ltURI_TOKEN`
A new serialized field: `URITokenID`
Five new transaction types:

- `URITokenMint`
- `URITokenBurn`
- `URITokenBuy`
- `URITokenCreateSellOffer`
- `URITokenCancelSellOffer`

## New Ledger Object Type: `URIToken`

The `ltURI_TOKEN` object is an owned first-class on-ledger object which lives in its owner's directory. It is uniquely identified by the combined hash of its `Issuer` (minter) and the `URI`. Therefore an issuer can only issue one `URIToken` per URI. Upon creation (minting) the Issuer is the object's first Owner. You cannot mint on behalf of a third party. As with other first class objects, each URIToken locks up an owner reserve on the account that currently owns it. Disposing of a URIToken frees up these reserved funds.

The object has the following fields:

| Field         | Type      | Required | Description                                                                                              |
| ------------- | --------- | -------- | -------------------------------------------------------------------------------------------------------- |
| sfIssuer      | AccountID | ✔️       | The minter who issued the token.                                                                         |
| sfOwner       | AccountID | ✔️       | The current owner of the token.                                                                          |
| sfURI         | VL blob   | ✔️       | The URI the token points to.                                                                             |
| sfFlags       | UInt32    | ✔️       | A flag indicating whether or not the URIToken is burnable, and whether or not it is for sale.            |
| sfDigest      | Hash256   | ❌       | An sha512half integrity digest of the contents pointed to by the URI                                     |
| sfAmount      | Amount    | ❌       | If the URIToken is for sale, then this is the amount the seller is asking for.                           |
| sfDestination | AccountID | ❌       | If the URIToken is for sale and this field has been set then only this AccountID may purchase the token. |

Example URIToken object:

```json
{
  "Flags": 0,
  "Issuer": "rN38hTretqygfgcvADnJwZzHu5rawAvmkX",
  "LedgerEntryType": "URIToken",
  "Owner": "rN38hTretqygfgcvADnJwZzHu5rawAvmkX",
  "URI": "68747470733A2F2F6D656469612E74656E6F722E636F6D2F666752755A7A662D374B5541414141642F6465616C2D776974682D69742D73756E676C61737365732E676966"
}
```

## New Transaction Type: `URITokenMint`

| Field    | Type    | Required | Description                                                           |
| -------- | ------- | -------- | --------------------------------------------------------------------- |
| sfURI    | VL blob | ✔️       | The URI the token points to.                                          |
| sfDigest | Hash256 | ❌       | An SHA512-Half integrity digest of the contents pointed to by the URI |
| sfFlags  | UInt32  | ❌       | tfBurnable (0x00000001) or 0 or absent                                |

If `sfDigest` is specified then the minted token will contain the hash specified by this field. For the end user this means they can verify the content served at the URI against this immutable hash, to ensure, for example that the properties of the NFT are not maliciously altered by changing the content at the URI. It may also be desirable to have a dynamic NFT where the content is intended to be altered, in which case simply omit `sfDigest` during minting, and the resulting URIToken will not contain this field.

‼️ If `sfFlags` is present and set to tfBurnable then the URIToken may be later burned by the Issuer. If the Hooks amendment is active on the chain this flag also indicates that the Issuer is a _strong transactional stakeholder_. In this event the Issuer's hooks will be executed whenever an attempt to buy or sell this URIToken occurs, and those hooks may reject the transaction and prevent it from happening if their own internal logic is not satisfied. It is therefore highly advisable to check whether or not a URIToken has `tfBurnable` set before purchasing or accepting it in trade.

Example Mint:

```json
{
  "Account": "raKG2uCwu71ohFGo1BJr7xqeGfWfYWZeh3",
  "Digest": "894E3B7ECDC9F6D00EE1D892F86E9BF0098F86BBD6CBB94D6ABFD78030EB5B9B",
  "TransactionType": "URITokenMint",
  "URI": "68747470733A2F2F6D656469612E74656E6F722E636F6D2F666752755A7A662D374B5541414141642F6465616C2D776974682D69742D73756E676C61737365732E6A736F6E"
}
```

## New Transaction Type: `URITokenBurn`

| Field        | Type    | Required | Description                                        |
| ------------ | ------- | -------- | -------------------------------------------------- |
| sfURITokenID | Hash256 | ✔️       | The Keylet for the URIToken object being destroyed |

The current owner of the URIToken can burn it at any time.

The Issuer of the token may also burn it at any time but only if `tfBurnable` was set during minting.

Burning a URIToken removes the specified `ltURI_TOKEN` object from the ledger and from the owner’s directory.

Example Burn:

```json
{
  "Account": "r9XAC6zP5Db4qZBgRbweKUPtroxYnydTEQ",
  "TransactionType": "URITokenBurn",
  "URITokenID": "0FAC3CD45FCB800BB9CCCF907775E7D4FB167847D8999FF05CE7456D6C3A70FA"
}
```

## New Transaction Type: `URITokenCreateSellOffer`

A user may offer to sell their URIToken for a preset amount. A given URIToken may have at most one current sell offer. There are no buy offers. If a user executes a URITokenBuy then it must immediately cross an existing sell offer.

To offer the URIToken for sale: specify its `URITokenID`, an `Amount` to sell for, and optionally a `Destination`. If Destination is set then only the specified account may purchase the URIToken. If the Amount is 0 then a Destination must be set. (This prevents an accidental "transfer to anyone" scenario.)

If a previous sell offer was present on the URIToken then it is simply replaced with the new offer.

| Field         | Type      | Required | Description                                                                          |
| ------------- | --------- | -------- | ------------------------------------------------------------------------------------ |
| sfURITokenID  | Hash256   | ✔️       | The Keylet for the URIToken object being offered for sale                            |
| sfAmount      | Amount    | ✔️       | The minimum amount a buyer must pay to purchase this URIToken. May be an IOU or XRP. |
| sfDestination | AccountID | ❌       | If provided then only this account may purchase the URIToken.                        |

Example Sell:

```json
{
  "Account": "r9XAC6zP5Db4qZBgRbweKUPtroxYnydTEQ",
  "Amount": "100000",
  "Flags": 524288,
  "TransactionType": "URITokenCreateSellOffer",
  "URITokenID": "0FAC3CD45FCB800BB9CCCF907775E7D4FB167847D8999FF05CE7456D6C3A70FA"
}
```

## New Transaction Type: `URITokenBuy`

A user may purchase a URIToken from another user if that URIToken has an active sell offer on it.

Whether a URIToken is for sale is indicated by the presence of the `Amount` field in the `lt_URI_TOKEN` object. If a `Destination` is also present in the object then only that AccountID may perform the purchase.

To purchase the URIToken, a user specifies its `URITokenID` and a purchase `Amount`. The purchase amount must be at least the amount specified in the sell offer (but may also exceed if the user wishes to tip the seller.) The purchase amount must be the same currency as the amount in the sell offer. No pathing is allowed in this transaction. The user must have sufficient currency available to cover the purchase.

| Field        | Type    | Required | Description                                                                                                                         |
| ------------ | ------- | -------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| sfURITokenID | Hash256 | ✔️       | The Keylet for the URIToken object being purchased.                                                                                 |
| sfAmount     | Amount  | ✔️       | The purchase price the buyer is willing to send. Must be the same currency as the sell offer. May not be less than the sale amount. |

Example Buy:

```json
{
  "Account": "rpiLN1C94hGKGpLUbhsadVHzdSXtB2Ldra",
  "Amount": "100001",
  "TransactionType": "URITokenBuy",
  "URITokenID": "0FAC3CD45FCB800BB9CCCF907775E7D4FB167847D8999FF05CE7456D6C3A70FA"
}
```

## New Transaction Type: `URITokenCancelSellOffer`

When a user has offered their URIToken for sale and later changes their mind, they may perform a clear operation. A clear operation simply clears the current sell offer from the URIToken.

| Field        | Type    | Required | Description                                                                |
| ------------ | ------- | -------- | -------------------------------------------------------------------------- |
| sfURITokenID | Hash256 | ✔️       | The Keylet for the URIToken object being cleared of any active sell offer. |

Example Clear

```json
{
  "Account": "rpiLN1C94hGKGpLUbhsadVHzdSXtB2Ldra",
  "TransactionType": "URITokenCancelSellOffer",
  "URITokenID": "0FAC3CD45FCB800BB9CCCF907775E7D4FB167847D8999FF05CE7456D6C3A70FA"
}
```

# Schema / Metadata Content

The URI pointed to by a URIToken should resolve to a JSON document that follows the below schema.

This schema may be extended over time as additional categories and use-cases present themselves.

‼️ Note that the `Digest`, if provided during Minting, is the hash of this JSON document **not** the content pointed to by the JSON document. The `Digest` is calculated by taking the SHA-512 Half of the stringified, whitespace trimmed content JSON.

- Schema gist: https://gist.github.com/WietseWind/83cd89906ed79fb510ec1eae3fc70bb6
- Sample digest generator gist: https://gist.github.com/WietseWind/d5072777814b6f239c3baba5cbe29e39

## JSON Schema

```js
export interface xls35category {
  code: string
  description: string
}

// EXAMPLES (!)
export const xls35categories: xls35category[] = [
  { code: '0000',      description: 'Testing-purpose token' },

  { code: '0001',      description: 'Art' },
  { code: '0001.0001', description: 'Physical art' },
  { code: '0001.0002', description: 'Digital art' },

  { code: '0002',      description: 'Licenses' },
  { code: '0002.0001', description: 'Software licenses' },

  { code: '0003',      description: 'Admission tickets' },

  { code: '0004',      description: 'Ownership (physical)' },
  { code: '0004.0001', description: 'Land (plots)' },
  { code: '0004.0002', description: 'Time shares' },
]

export interface xls35attachment {
  description?: string
  filename: string
  url: string
}

export interface xls35schema {
  // Custom schema for additional information
  schema?: {
    url: string
    digest?: string
  }

  // Custom external information, to match your own specified schema (^^)
  content?: {
    url: string
    digest?: string
  }

  // Basic information: to allow instant rendering, ...
  details: {
    title: string
    categories?: xls35category[]
    publisher?: {
      name: string
      url?: string
      email?: string
    }
    previewUrl?: {
      thumbnail: string
      regular?: string
      highres?: string
    }
    group?: {
      code?: string
      title: string
    }
    attachments?: xls35attachment[]
  }
}
```

## Example JSON document

```json
{
  "content": {
    "url": "https://someuri"
  },
  "details": {
    "title": "Some URIToken",
    "categories": ["0000"],
    "publisher": {
      "name": "XRPL-Labs"
    }
  }
}
```

## Computing the `Digest` over your JSON document

Pseudo-code:

```js
metadata = {
  details: {
    title: "Some Title",
  },
};

jsonstring = json_encode(metadata);
whitespaceremoved = trim(jsonstring);
hash = sha512(whitespaceremoved);
sha512half = slice(hash, 0, 64);

digest = sha512half;
```
