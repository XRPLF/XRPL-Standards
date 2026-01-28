<pre>
  xls: 26
  title: IOU Token Metadata via xrp-ledger.toml
  description: A unified solution for IOU token metadata by adding optional fields to the existing xrp-ledger.toml standard
  author: Marc-Emanuel Otto (@Mwni)
  proposal-from: https://github.com/XRPLF/XRPL-Standards/discussions/71
  status: Draft
  category: Ecosystem
  created: 2022-04-04
</pre>

# IOU Token Metadata via xrp-ledger.toml

IOU ([fungible](https://xrpl.org/docs/concepts/tokens/fungible-tokens)) tokens on the XRP Ledger lack a native spot for metadata. This has led to fragmented metadata solutions. To display a token’s icon or details, issuers must contact every wallet or explorer (Xaman, Bithomp, XRP Scan, XPMarket, XRPL Coins) and repeat the process for every update. Developers also lack a single, reliable source for asset data.

This standard provides a unified solution by adding optional fields to the existing [xrp-ledger.toml standard](https://xrpl.org/xrp-ledger-toml.html), letting issuers publish:

- Icons
- Descriptions
- Clear names
- Asset Classes
- Links to relevant sites or documents

## Approach

Issuers host an xrp-ledger.toml file on their website under the URL `https://YOUR_DOMAIN_HERE/.well-known/xrp-ledger.toml` and link to it by setting the `Domain` field of the issuing account to `YOUR_DOMAIN_HERE`.

![Example Diagram](./schematic-diagram.svg)

## Extensions to xrp-ledger.toml

### `[[ISSUERS]]`

Defines an XRPL account that acts as an issuer of token(s).

| Key       | Type     | Description                                                                                                               | Required |
| --------- | -------- | ------------------------------------------------------------------------------------------------------------------------- | -------- |
| `address` | `string` | The public address of the issuer, encoded in the base58 format.                                                           | Yes      |
| `name`    | `string` | The display name of the issuer.                                                                                           | No       |
| `desc`    | `string` | A description of the issuer.                                                                                              | No       |
| `icon`    | `string` | A URL pointing to an icon image representing the issuer. Must start with the protocol, generally _https://_ or _ipfs://_. | No       |

### `[[TOKENS]]`

Defines an issued currency on the XRPL. Currency code and issuing address must be specified.
| Key | Type | Description | Required
|--|--|--|--|
| `currency` | `string` | The currency code of the token. This can be a three-digit code, a 40-character hex code, or a custom format. | Yes
| `issuer` | `string` | The public address of the issuer, encoded in the base58 format. | Yes
| `name` | `string` | A display name for the token. | No
| `desc` | `string` | A description of the token and the project associated with it. | No
| `icon` | `string` | A URL pointing to an icon image representing the token. Must start with the protocol, generally _https://_ or _ipfs://_. | No
| `asset_class` | `string` | Top-level classification of token purpose. See the **Asset Class Definitions** table below. | No
| `asset_subclass` | `string` | Optional subcategory. See the **Asset Class Definitions** table below. | If `rwa`

### `[[TOKENS.URLS]]`

Defines a web URL associated with a token. **Must follow directly after the TOKENS stanza it belongs to.**
| Key | Type | Description | Required
|--|--|--|--|
| `url` | `string` | The URL of the hyperlink. Must start with the protocol, generally `https://`. | Yes
| `type` | `string` | The type of the content that the link is pointing to. Possible values are: `website`, `social`, `document`. | No
| `title` | `string` | A descriptive title for the link. Should be used to clear ambiguities. | No

## Asset Class Definitions

| `asset_class` | Definition                                                                                                                                             |
| ------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `rwa`         | Tokens representing real-world assets (RWAs), which derive value from legally enforceable claims on physical or off-chain financial assets.            |
| `memes`       | Tokens primarily driven by community, internet culture, or speculation, without intrinsic backing or utility claims.                                   |
| `wrapped`     | Tokens that represent assets from other blockchains, typically backed 1:1 and issued by bridges or custodians.                                         |
| `gaming`      | Tokens used in games or virtual worlds, often representing in-game currency, assets, or rewards.                                                       |
| `defi`        | Tokens native to or used within decentralized finance protocols, including governance tokens, DEX tokens, and lending assets.                          |
| `other`       | Tokens that do not clearly fit into the defined categories. This may include experimental, test, or those with unique use cases not covered elsewhere. |

For tokens of class `rwa`, the `asset_subclass` field is required.

| `asset_class` | `asset_subclass` | Definition                                                                                                                               |
| ------------- | ---------------- | ---------------------------------------------------------------------------------------------------------------------------------------- |
| `rwa`         | `stablecoin`     | Tokens pegged to a stable value (typically fiat currencies like USD), backed by reserves such as cash, treasuries, or crypto collateral. |
| `rwa`         | `commodity`      | Tokens representing physical commodities like gold, silver, or oil, often redeemable or legally linked to off-chain reserves.            |
| `rwa`         | `real_estate`    | Tokens representing ownership or claims on real estate, including fractionalized property shares or REIT-like instruments.               |
| `rwa`         | `private_credit` | Tokens representing debt obligations from private entities, such as loans, invoices, or receivables.                                     |
| `rwa`         | `equity`         | Tokens representing ownership shares in companies, similar to traditional stock or equity instruments.                                   |
| `rwa`         | `treasury`       | Tokens backed by or referencing government debt instruments, such as U.S. Treasury bills or bonds.                                       |
| `rwa`         | `other`          | Tokens that do not fit into the predefined categories above, including experimental, hybrid, or emerging real-world asset types.         |

## Example

The example .toml file below defines the metadata of the RLUSD stablecoin.
The file should be placed at [https://ripple.com/.well-known/xrp-ledger.toml](https://ripple.com/.well-known/xrp-ledger.toml), while the issuing account [rMxCKbEDwqr76QuheSUMdEGf4B9xJ8m5De](https://livenet.xrpl.org/accounts/rMxCKbEDwqr76QuheSUMdEGf4B9xJ8m5De) should have its `Domain` field set to `ripple.com`.

```toml
[[ISSUERS]]
address = "rMxCKbEDwqr76QuheSUMdEGf4B9xJ8m5De"
name = "Ripple"
desc = "We're building the Internet of Value."

[[TOKENS]]
issuer = "rMxCKbEDwqr76QuheSUMdEGf4B9xJ8m5De"
currency = "RLUSD"
name = "Ripple USD"
desc = "Ripple USD (RLUSD) is natively issued on the XRP Ledger and Ethereum blockchains and is enabled with a number of features to ensure strict adherence to compliance standards, flexibility for developers, and security for holders."
icon = "https://ripple.com/assets/rlusd-logo.png"
asset_class = "rwa"
asset_subclass = "stablecoin"

[[TOKENS.URLS]]
url = "https://ripple.com"
type = "website"
title = "Official Website"

[[TOKENS.URLS]]
url = "https://x.com/ripple"
type = "social"
```

## Implementations

### Parsing Library

The [@xrplkit/xls26](https://www.npmjs.com/package/@xrplkit/xls26) package is a Javascript implementation of this standard. It parses the string of a .toml file into a Javascript object (JSON).

### Crawler + API

The project **XRPL Meta** ([Repo](https://github.com/xrplmeta/node), [Website](https://xrplmeta.org)) automatically scans the entire ledger for issuing `AccountRoot` objects with defined `Domain` fields. It fetches and parses their xrp-ledger.toml file, if published. The obtained data is stored, enriched and made available through a REST or WebSocket API.

Given the example above, this is the metadata collected for RLUSD:

https://livenet.xrplmeta.org/token/RLUSD:rMxCKbEDwqr76QuheSUMdEGf4B9xJ8m5De

## Early Adopters

### [Xaman](https://xaman.app)

Xaman uses XRPL Meta for [displaying token icons and names](https://help.xaman.app/app/learning-more-about-xaman/adding-an-icon-logo-to-a-trust-line-in-xumm) in the wallet app.

### [First Ledger](https://firstledger.net)

First Ledger publishes XLS-26 compliant xrp-ledger.toml files for every issued token.

### [Unhosted Exchange](https://unhosted.exchange)

Unhosted Exchange aka Xaman DEX xApp uses XRPL Meta for displaying a full list of all tradable tokens.

### [Crossmark](https://crossmark.io)

Crossmark uses XRPL Meta for displaying names, icons and market data for held tokens in the wallet app.

### [GemWallet](https://gemwallet.app)

GemWallet uses XRPL Meta for displaying token icons, names and trust levels.

### [Ledger.meme](https://ledger.meme)

Ledger.meme publishes XLS-26 compliant xrp-ledger.toml files for every issued token.

### [XRP Toolkit](https://www.xrptoolkit.com)

XRP Toolkit uses XRPL Meta for displaying token icons.
