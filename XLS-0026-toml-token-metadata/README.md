<pre>
Title:       <b>TOML Token Metadata</b>
Revision:    <b>5</b> (2025-06-06)
Author:      <a href="https://github.com/Mwni">Marc-Emanuel Otto</a>
Contributor: <a href="https://ripple.com">Ripple</a>
</pre>


# Token Metadata Extensions to xrp-ledger.toml

A set of additional fields for the existing [xrp-ledger.toml standard](https://xrpl.org/xrp-ledger-toml.html). The goal is to

1. Make it easier for token issuers to publish metadata about their tokens.
2. Make it easier for developers to access this metadata.

## Motivation

It can be difficult to get your token properly represented in the XRPL ecosystem. To get your token's icon to be shown, you need to personally reach out to all wallet and platform vendors. These include Xaman, Bithomp, XRP Scan, XPMarket, XRPL Coins. All vendors rely on manual management of the metadata, so for any updates, _you have to do the same roundtrip again_.

For developers, it's not any different. There is no standardized way of obtaining asset metadata. This standard aims to change that.

## How it works

We utilize the already established [xrp-ledger.toml standard](https://xrpl.org/docs/references/xrp-ledger-toml) as foundation. Hereby issuers host an xrp-ledger.toml file on their website under the URL `https://YOUR_DOMAIN_HERE/.well-known/xrp-ledger.toml` and link to it by setting the `Domain` field of the issuing account to `YOUR_DOMAIN_HERE`.

![Schematic Diagram](https://github.com/user-attachments/assets/0baeed15-747f-44e4-b020-496eeec9f606)



## The Extensions

###  `[[ISSUERS]]`
Defines an XRPL account that acts as an issuer of token(s).

| Key | Type | Description
|--|--|--|
| `address` | `string` | The public address of the issuer, encoded in the base58 format.
| `name` 	| `string` | The display name of the issuer.
| `desc` 	| `string` | A description of the issuer.
| `icon` 	| `string` | A URL pointing to an icon image representing the issuer. Must start with the protocol, generally _https://_ or _ipfs://_.


###  `[[ISSUERS.URLS]]`
Defines a web link associated with an issuing account. Must follow directly after the issuers stanza it belongs to.
| Key | Type | Description
|--|--|--|
| `url` 	| `string` | The URL of the hyper-link. Must start with the protocol, generally _https://_
| `type` 	| `string` | The type of the content that the link is pointing to. Possible values are: `website`, `social`, `support`, `whitepaper`, `legal`.
| `title` 	| `string` | A descriptive title for the link. Should be used to clear ambiguities.



###  `[[TOKENS]]`
Defines an issued currency on the XRPL. Currency code and issuing address must be specified.
| Key | Type | Description
|--|--|--|
| `currency` 	| `string` | The currency code of the token. This can be a three-digit code, a 40-character hex code, or a custom format.
| `issuer` 		| `string` | The public address of the issuer, encoded in the base58 format.
| `name` 		| `string` | A display name for the token.
| `desc` 		| `string` | A description of the token and the project associated with it.
| `icon` 		| `string` | A URL pointing to an icon image representing the token. Must start with the protocol, generally _https://_ or _ipfs://_.
| `asset_class` | `string` | Top-level classification of token purpose. See the **Asset Class Definitions** table below.
| `asset_subclass` | `string` | Optional subcategory, required if `asset_class = rwa`. See the **Asset Class Definitions** table below.


###  `[[TOKENS.URLS]]`
Defines a web link associated with a token. Must follow directly after the tokens stanza it belongs to.
| Key | Type | Description
|--|--|--|
| `url` 	| `string` | The URL of the hyper-link. Must start with the protocol, generally `https://`
| `type` 	| `string` | The type of the content that the link is pointing to. Possible values are: `website`, `social`, `support`, `whitepaper`, `legal`.
| `title` 	| `string` | A descriptive title for the link. Should be used to clear ambiguities.


## Asset Class Definitions
| `asset_class` | Definition
|--|--|
| `rwa` 	| Tokens representing real-world assets (RWAs), which derive value from legally enforceable claims on physical or off-chain financial assets.
| `memes` 	| Tokens primarily driven by community, internet culture, or speculation, without intrinsic backing or utility claims.
| `wrapped` | Tokens that represent assets from other blockchains, typically backed 1:1 and issued by bridges or custodians.
| `gaming` 	| Tokens native to or used within decentralized finance protocols, including governance tokens, DEX tokens, and lending assets.
| `defi` 	| Tokens representing real-world assets (RWAs), which derive value from legally enforceable claims on physical or off-chain financial assets.
| `other` 	| Tokens that do not clearly fit into the defined categories. This may include experimental, test, or those with unique use cases not covered elsewhere.

For tokens of class `rwa`, the `asset_subclass` field is required.

| `asset_class` |`asset_subclass` | Definition
|--|--|--|
| `rwa` | `stablecoin` 		| Tokens pegged to a stable value (typically fiat currencies like USD), backed by reserves such as cash, treasuries, or crypto collateral.
| `rwa` | `commodity` 		| Tokens representing physical commodities like gold, silver, or oil, often redeemable or legally linked to off-chain reserves.
| `rwa` | `real_estate` 	| Tokens representing ownership or claims on real estate, including fractionalized property shares or REIT-like instruments.
| `rwa` | `private_credit` 	| Tokens representing debt obligations from private entities, such as loans, invoices, or receivables.
| `rwa` | `equity` 			| Tokens representing ownership shares in companies, similar to traditional stock or equity instruments.
| `rwa` | `treasury` 		| Tokens backed by or referencing government debt instruments, such as U.S. Treasury bills or bonds.
| `rwa` | `other` 			| Tokens that do not fit into the predefined categories above, including experimental, hybrid, or emerging real-world asset types.


## Example
The example .toml file below defines the metadata of the RLUSD stablecoin.
The file should be placed at [https://ripple.com/.well-known/xrp-ledger.toml](https://ripple.com/.well-known/xrp-ledger.toml), while the issuing account [rMxCKbEDwqr76QuheSUMdEGf4B9xJ8m5De](https://livenet.xrpl.org/accounts/rMxCKbEDwqr76QuheSUMdEGf4B9xJ8m5De) should have its `Domain` field set to `ripple.com`.
```toml
[[ISSUERS]]
address = "rMxCKbEDwqr76QuheSUMdEGf4B9xJ8m5De"
name = "Ripple"

[[ISSUERS.URLS]]
url = "https://ripple.com"
type = "website"
title = "Official Website"

[[TOKENS]]
issuer = "rMxCKbEDwqr76QuheSUMdEGf4B9xJ8m5De"
currency = "RLUSD"
name = "Ripple USD"
desc = "Ripple USD (RLUSD) is natively issued on the XRP Ledger and Ethereum blockchains and is enabled with a number of features to ensure strict adherence to compliance standards, flexibility for developers, and security for holders."
icon = "https://ripple.com/assets/rlusd-logo.png"
asset_class = "rwa"
asset_subclass = "stablecoin"

[[TOKENS.URLS]]
url = "https://ripple.com/solutions/stablecoin/"
type = "website"

[[TOKENS.URLS]]
url = "https://x.com/ripple"
type = "social"
```

## Implementations

### Parsing Library

The [@xrplkit/xls26](https://www.npmjs.com/package/@xrplkit/xls26) package is a Javascript implementation of this standard. It parses the string of a .toml file into a Javascript object (JSON). 

### Crawler + API

The project **XRPL Meta** ([Repo](https://github.com/xrplmeta/node), [Website](https://xrplmeta.org)) automatically scans the entire ledger for issuing `AccountRoot`s with defined `Domain` fields. It fetches and parses their xrp-ledger.toml file, if published. The obtained data is stored, enriched and made available through a REST or WebSocket API.

Given the example above, this is the metadata collected for RLUSD:

https://livenet.xrplmeta.org/token/RLUSD:rMxCKbEDwqr76QuheSUMdEGf4B9xJ8m5De