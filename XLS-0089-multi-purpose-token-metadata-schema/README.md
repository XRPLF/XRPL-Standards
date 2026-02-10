<pre>
  xls: 89
  title: Multi-Purpose Token Metadata Schema
  description: Standardized metadata schema for Multi-Purpose Tokens to improve discoverability, comparability, and interoperability
  author: Shawn Xie <shawnxie@ripple.com>, Greg Tsipenyuk <gtsipenyuk@ripple.com>, Shashwat Mittal <smittal@ripple.com>, Julian Berridi <jberridi@ripple.com>, Kuan Lin <klin@ripple.com>
  proposal-from: https://github.com/XRPLF/XRPL-Standards/discussions/264
  status: Final
  category: Ecosystem
  requires: XLS-33
  created: 2025-01-27
  updated: 2025-10-29
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

| Field             | Key  | Description                                                                                          | Example                                                                                               | Allowed Values                                                  | Type                  | Required? |
| ----------------- | ---- | ---------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------- | --------------------------------------------------------------- | --------------------- | --------- |
| `ticker`          | `t`  | Ticker symbol used to represent the token                                                            | EXMPL                                                                                                 | Uppercase letters (A-Z) and digits (0-9) only. Max 6 chars      | string                | ✔️        |
| `name`            | `n`  | Display name of the token                                                                            | Example Token                                                                                         | Any UTF-8 string                                                | string                | ✔️        |
| `desc`            | `d`  | Short description of the token                                                                       | A sample token used for demonstration                                                                 | Any UTF-8 string                                                | string                |           |
| `icon`            | `i`  | URI to the token icon                                                                                | example.org/token-icon, ipfs://token-icon.png                                                         | `hostname/path` (HTTPS assumed) or full URI for other protocols | string                | ✔️        |
| `asset_class`     | `ac` | Top-level classification of token purpose                                                            | rwa                                                                                                   | rwa, memes, wrapped, gaming, defi, other                        | string                | ✔️        |
| `asset_subclass`  | `as` | Optional subcategory, required if `asset_class = rwa`                                                | See 2.2 _asset_subclass_                                                                              | See 2.2 _asset_subclass_                                        | string                |           |
| `issuer_name`     | `in` | The name of the issuer account                                                                       | Example Issuer                                                                                        | Any UTF-8 string                                                | string                | ✔️        |
| `uris`            | `us` | List of related URIs (site, dashboard, social media, etc.)                                           | See 2.3 _uris_                                                                                        | See 2.3 _uris_                                                  | array                 |           |
| `additional_info` | `ai` | Freeform field for key token details like interest rate, maturity date, term, or other relevant info | {"interest_rate": "4.75%", "maturity_date": "2030-06-30", "term": "10Y", "issuer_type": "government"} | Any valid JSON object or UTF-8 string                           | JSON object or string |           |

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

| Asset Type       | Description                                                                                                                             |
| ---------------- | --------------------------------------------------------------------------------------------------------------------------------------- |
| `stablecoin`     | Tokens pegged to a stable value (typically fiat currencies like USD), backed by reserves such as cash, treasuries, or crypto collateral |
| `commodity`      | Tokens representing physical commodities like gold, silver, or oil, often redeemable or legally linked to off-chain reserves            |
| `real_estate`    | Tokens representing ownership or claims on real estate, including fractionalized property shares or REIT-like instruments               |
| `private_credit` | Tokens representing debt obligations from private entities, such as loans, invoices, or receivables                                     |
| `equity`         | Tokens representing ownership shares in companies, similar to traditional stock or equity instruments                                   |
| `treasury`       | Tokens backed by or referencing government debt instruments, such as U.S. Treasury bills or bonds                                       |
| `other`          | Tokens that do not fit into the predefined categories above, including experimental, hybrid, or emerging real-world asset types         |

---

### 2.3 uris

| Field      | Key | Description                         | Example                                  | Allowed Values                                                  | Required |
| ---------- | --- | ----------------------------------- | ---------------------------------------- | --------------------------------------------------------------- | -------- |
| `uri`      | `u` | URI to the related resource         | exampleyield.com/tbill, ipfs://abc123... | `hostname/path` (HTTPS assumed) or full URI for other protocols | ✔️       |
| `category` | `c` | The category of the link            | website                                  | website, social, docs, other                                    | ✔️       |
| `title`    | `t` | A human-readable label for the link | Product Page                             | Any UTF-8 string                                                | ✔️       |

---

## 3. Field Name Format

The metadata schema supports JSON objects with both long field names (e.g., `ticker`, `name`, `desc`) and short key names (e.g., `t`, `n`, `d`). However, it is recommended to use short key names to reduce storage requirements of the ledger. The MPT metadata field has a 1024-byte limit, and using compact keys can reduce the metadata size and allow more information to be stored within the available space.

### 3.1 Client Library Support

XRPL client libraries will provide utility functions to facilitate working with metadata in both formats:

- **Encoding utility**: Converts JSON metadata to hexadecimal format for on-ledger storage. If long field names are provided, the utility will automatically shorten them to their compact key equivalents before encoding.
- **Decoding utility**: Converts hexadecimal metadata from the ledger back to JSON format. The utility will expand short keys back to their full field names for improved readability.

This approach provides flexibility for developers while ensuring efficient on-ledger storage. Developers can work with human-readable long field names in their applications, and the client libraries will handle the conversion to compact format automatically.

---

### 3.2 JSON Metadata Example

The example below demonstrates the recommended format using short key names. Note that the **Key** values from the tables in Section 2 are used as the property names in the JSON metadata object.

```json
{
  "t": "TBILL",
  "n": "T-Bill Yield Token",
  "d": "A yield-bearing stablecoin backed by short-term U.S. Treasuries and money market instruments.",
  "i": "example.org/tbill-icon.png",
  "ac": "rwa",
  "as": "treasury",
  "in": "Example Yield Co.",
  "us": [
    {
      "u": "exampleyield.co/tbill",
      "c": "website",
      "t": "Product Page"
    },
    {
      "u": "exampleyield.co/docs",
      "c": "docs",
      "t": "Yield Token Docs"
    }
  ],
  "ai": {
    "interest_rate": "5.00%",
    "interest_type": "variable",
    "yield_source": "U.S. Treasury Bills",
    "maturity_date": "2045-06-30",
    "cusip": "912796RX0"
  }
}
```
