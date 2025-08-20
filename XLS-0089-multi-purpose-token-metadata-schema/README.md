<pre>
xls: 89
title: Multi-Purpose Token Metadata Schema
description: Standardized metadata schema for Multi-Purpose Tokens to improve discoverability, comparability, and interoperability
author: Nathan Nichols <nnichols@ripple.com>
discussion-from: https://github.com/XRPLF/XRPL-Standards/discussions/264
status: Draft
category: Community
requires: XLS-33
created: 2023-03-01
</pre>

---

# XLS-89 Multi-Purpose Token Metadata Schema

## 1. Abstract

Multipurpose Tokens (MPTs) on the XRP Ledger allow issuers to attach arbitrary metadata to their tokens. While this flexibility is powerful, it also creates challenges for discoverability, comparability, and interoperability — both across MPTs and with existing IOUs on XRPL.

This document proposes a minimally standardized metadata format for MPTs to address those challenges. The goal is not to restrict expressiveness, but to define a baseline set of fields that support reliable parsing and integration across services like block explorers, indexers, wallets, and cross-chain applications. These common fields will make it easier to surface and compare MPTs, enabling better user experiences and broader ecosystem support.

This proposal is complementary to [PR #290](https://github.com/XRPLF/XRPL-Standards/pull/290), which defines metadata for IOUs on XRPL. While some elements differ to accommodate token-specific needs, both efforts aim to promote consistency and interoperability across the ecosystem.

This standard is optional, but MPTs that follow it will be more readily integrated into the XRPL ecosystem.

---

## 1.1. Approach

MPTs include a 1024-byte field for arbitrary metadata. The metadata field is part of a hybrid approach of storing essential information on the ledger, while additional information can be stored off the ledger using an external URI in the metadata field. Advantages to this approach include:

- Metadata can be accessed and verified on the ledger without having to fetch data from an external URI.
- Provides increased reliability while decreasing dependency on external systems. Relying solely on external sources for metadata would introduce a dependency where services might become unavailable or unreliable, disrupting token operations and the user experience.
- Avoids the risk of a centralized hosting service provider becoming compromised or unavailable.

---

## 2. Base Metadata Schema

| Field             | Description                                                                                          | Example                                                                                                   | Allowed Values                                                              | Type                  | Required? |
| ----------------- | ---------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------- | --------------------- | --------- |
| `ticker`          | Ticker symbol used to represent the token                                                            | EXMPL                                                                                                     | Uppercase letters (A-Z) and digits (0-9) only. Max 6 characters recommended | string                | ✔️        |
| `name`            | Display name of the token                                                                            | Example Token                                                                                             | Any UTF-8 string                                                            | string                | ✔️        |
| `desc`            | Short description of the token                                                                       | A sample token used for demonstration                                                                     | Any UTF-8 string                                                            | string                |           |
| `icon`            | URL to the token icon                                                                                | https://example.org/token-icon.png                                                                        | HTTPS URL that links to an image                                            | string                | ✔️        |
| `asset_class`     | Top-level classification of token purpose                                                            | rwa                                                                                                       | rwa, memes, wrapped, gaming, defi, other                                    | string                | ✔️        |
| `asset_subclass`  | Optional subcategory, required if `asset_class = rwa`                                                | See 2.2 _asset_subclass_                                                                                  | See 2.2 _asset_subclass_                                                    | string                |           |
| `issuer_name`     | The name of the issuer account                                                                       | Example Issuer                                                                                            | Any UTF-8 string                                                            | string                | ✔️        |
| `urls`            | List of related URLs (site, dashboard, social media, etc.)                                           | See 2.3 _urls_                                                                                            | See 2.3 _urls_                                                              | array                 |           |
| `additional_info` | Freeform field for key token details like interest rate, maturity date, term, or other relevant info | `{ "interest_rate": "4.75%", "maturity_date": "2030-06-30", "term": "10Y", "issuer_type": "government" }` | Any valid JSON object or UTF-8 string                                       | JSON object or string |           |

---

### 2.1 asset_class

| Category  | Definition                                                                                                                                            |
| --------- | ----------------------------------------------------------------------------------------------------------------------------------------------------- |
| `rwa`     | Tokens representing real-world assets (RWAs), which derive value from legally enforceable claims on physical or off-chain financial assets            |
| `memes`   | Tokens primarily driven by community, internet culture, or speculation, without intrinsic backing or utility claims                                   |
| `wrapped` | Tokens that represent assets from other blockchains, typically backed 1:1 and issued by bridges or custodians                                         |
| `gaming`  | Tokens used in games or virtual worlds, often representing in-game currency, assets, or rewards                                                       |
| `defi`    | Tokens native to or used within decentralized finance protocols, including governance tokens, DEX tokens, and lending assets                          |
| `other`   | Tokens that do not clearly fit into the defined categories. This may include experimental, test, or those with unique use cases not covered elsewhere |

---

### 2.2 asset_subclass

| asset_type       | Description                                                                                                                             |
| ---------------- | --------------------------------------------------------------------------------------------------------------------------------------- |
| `stablecoin`     | Tokens pegged to a stable value (typically fiat currencies like USD), backed by reserves such as cash, treasuries, or crypto collateral |
| `commodity`      | Tokens representing physical commodities like gold, silver, or oil, often redeemable or legally linked to off-chain reserves            |
| `real_estate`    | Tokens representing ownership or claims on real estate, including fractionalized property shares or REIT-like instruments               |
| `private_credit` | Tokens representing debt obligations from private entities, such as loans, invoices, or receivables                                     |
| `equity`         | Tokens representing ownership shares in companies, similar to traditional stock or equity instruments                                   |
| `treasury`       | Tokens backed by or referencing government debt instruments, such as U.S. Treasury bills or bonds                                       |
| `other`          | Tokens that do not fit into the predefined categories above, including experimental, hybrid, or emerging real-world asset types         |

---

### 2.3 urls

| Field   | Description                           | Example                       | Allowed Values                   | Required |
| ------- | ------------------------------------- | ----------------------------- | -------------------------------- | -------- |
| `url`   | The full link to the related resource | https://exampleyield.co/tbill | A valid HTTPS URL                | ✔️       |
| `type`  | The category of the link              | website                       | website, social, document, other | ✔️       |
| `title` | A human-readable label for the link   | Product Page                  | Any UTF-8 string                 | ✔️       |

---

### JSON Metadata example

```json
{
  "ticker": "TBILL",
  "name": "T-Bill Yield Token",
  "desc": "A yield-bearing stablecoin backed by short-term U.S. Treasuries and money market instruments.",
  "icon": "https://example.org/tbill-icon.png",
  "asset_class": "rwa",
  "asset_subclass": "treasury",
  "issuer_name": "Example Yield Co.",
  "urls": [
    {
      "url": "https://exampleyield.co/tbill",
      "type": "website",
      "title": "Product Page"
    },
    {
      "url": "https://exampleyield.co/docs",
      "type": "docs",
      "title": "Yield Token Docs"
    }
  ],
  "additional_info": {
    "interest_rate": "5.00%",
    "interest_type": "variable",
    "yield_source": "U.S. Treasury Bills",
    "maturity_date": "2045-06-30",
    "cusip": "912796RX0"
  }
}
```
