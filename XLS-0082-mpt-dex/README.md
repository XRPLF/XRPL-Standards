<pre>
  xls: 82
  title: MPT Integration into DEX
  description: Adds Multi-purpose token support for XRPL DEX
  author: Gregory Tsipenyuk <gtsipenyuk@ripple.com>
  proposal-from: https://github.com/XRPLF/XRPL-Standards/discussions/231
  status: Final
  category: Amendment
  requires: XLS-33
  created: 2024-09-19
  updated: 2026-01-27
</pre>

# MPT Integration into DEX

## Abstract

This proposal introduces a new amendment `MPTVersion2` as an extension to [XLS-33 Multi-Purpose Tokens](https://github.com/XRPLF/XRPL-Standards/tree/master/XLS-0033-multi-purpose-tokens). `MPTVersion2` amendment enables Multi-purpose token (MPT) support on the XRPL DEX.

## 1. Overview

The integration of Multi-Purpose Tokens (MPT) into the XRP Ledger Decentralized Exchange (DEX) focuses on extending the functional reach of existing trading mechanisms without introducing new on-ledger objects or modifying core state structures. By leveraging the existing ledger primitives, this update enables standard DEX transactions to natively support MPTs as a valid asset class. This specification outlines the necessary schema updates for transaction requests and provides comprehensive JSON examples to illustrate the interoperability between MPTs, XRP, and standard IOUs. Furthermore, this document details the expanded set of failure scenarios and transaction result codes specific to MPT trading, ensuring robust error handling for cross-asset liquidity paths and order-matching logic. For a comprehensive description of all transactions refer to [XRPL documentation](https://xrpl.org/docs/references/protocol/transactions)

Current transactions, which interract with XRPL DEX are:

- `AMMCreate`: Create a new Automated Market Maker (AMM) instance for trading a pair of assets (fungible tokens or XRP).
- `AMMDeposit`: Deposit funds into an AMM instance and receive the AMM's liquidity provider tokens (LP Tokens) in exchange.
- `AMMWithdraw`: Withdraw assets from an AMM instance by returning the AMM's liquidity provider tokens (LP Tokens).
- `AMMClawback`: Enable token issuers to claw back tokens from wallets that have deposited into AMM pools.
- `AMMDelete`: Delete an empty AMM instance that could not be fully deleted automatically.
- `CheckCreate`: Create a Check object in the ledger, which is a deferred payment that can be cashed by its intended destination.
- `CheckCash`: Attempts to redeem a Check object in the ledger to receive up to the amount authorized by the corresponding CheckCreate transaction.
- `OfferCreate`: An OfferCreate transaction places an Offer in the decentralized exchange.
- `Payment`: A Payment transaction represents a transfer of value from one account to another.

MPT supports all of the above transactions. MPT can be combined with IOU and XRP tokens in the transactions. For instance, a Payment could be a cross-token payment from MPT token to IOU token; AMM can be created for XRP and MPT token-pair; an order book offer can be created to buy some MPT token and to sell another MPT token. MPT doesn't modify the transactions fields, flags, and functionality. However, the JSON of the MPT amount field differs from the JSON of the IOU amount field. Instead of `currency` and `issuer`, MPT is identified by `mpt_issuance_id`. MPT amount `value` is INT or UINT, which must be less or equal to $63^2 - 1$. Below is an example of JSON MPT amount:

```json
   "Amount": {
       "mpt_issuance_id": "00000003430427B80BD2D09D36B70B969E12801065F22308",
       "value": "110"
   }
```

Any transaction with MPT Amount has to use JSON format as described above. For any transaction, which uses MPT token, the token has to be created first by an issuer with `MPTokenIssuanceCreate` transaction and in most cases, except for `AMMCreate`, `AMMWithdraw`, `AMMClawback`, `CheckCash`, and `OfferCreate`, the token has to be authorized by the holder account with `MPTokenAuthorize` transaction as described in [XLS-33d](https://github.com/XRPLF/XRPL-Standards/tree/master/XLS-0033d-multi-purpose-tokens). In addition, MPTokenIssuanceCreate` must have the following flags set:

- `lsfMPTCanTrade`, in order for individual holders to trade their balances using the XRP Ledger DEX or AMM.
- `lsfMPTCanTransfer, in order for the tokens held by non-issuers to be transferred to other accounts.

## 3. MPT Supported Transactions

### 3.1. AMM

AMM is identified by a token pair. Any token or both tokens in AMM transactions can be MPT. I.e., in addition to the current combination of XRP/IOU and IOU/IOU token pair, AMM can have XRP/MPT, IOU/MPT, and MPT/MPT token pair. Each MPT in the pair is identified by `mpt_issuance_id`. If both tokens are MPT then each token must have a unique `mpt_issuance_id`. In case of `AMMCreate` the token pair is identified by `Amount` and `Amount2`. In case of `AMMDeposit`, `AMMWithdraw`, and `AMMDelete` the token pair is identified by `Asset` and `Asset2` with the token type corresponding to `Amount` and `Amount2` of `AMMCreate`. `Asset` and `Asset2` are `STIssue` type, which represents a token by `currency` and `issuer`. If `STIssue` type represents MPT then `mpt_issuance_id` must be used instead. `AMMDeposit` and `AMMWithdraw` have optional fields `Amount` and `Amount2`, which if present must match the type of `Asset` and `Asset2` respectively.

#### 3.1.1. Create JSON Example

```json
{
  "Account": "rffMEZLzDQPNU6VYbWNkgQBtMz6gCYnMAG",
  "Amount": {
    "mpt_issuance_id": "00000002430427B80BD2D09D36B70B969E12801065F22308",
    "value": "1000"
  },
  "Amount2": {
    "mpt_issuance_id": "00000003430427B80BD2D09D36B70B969E12801065F22308",
    "value": "1000"
  },
  "Fee": "2000000",
  "Flags": 0,
  "TradingFee": "0",
  "TransactionType": "AMMCreate"
}
```

For each MPT token `AMMCreate` creates and authorizes `MPToken` object for AMM pseudo-account.

In addition to the current failure scenarios `AMMCreate` fails if:

- `Amount` or `Amount2` hold MPT and `featureMPTokensV2` amendment is not enabled, fail with `temDISABLED`.
- `MPTokenIssuance` object doesn't exist, fail with `tecOBJECT_NOT_FOUND`.
- `MPToken` object doesn't exist and AMM creator is not the issuer of MPT, fail with `tecNO_AUTH`.
- `MPTLock` flag is set on `MPTokenIssuance`, fail for issuer and holder with `tecFROZEN`.
- `MPTLock` flag is set on `MPToken`, fail for holder with `tecFROZEN`.
- `MPTRequireAuth` flag is set and AMM creator is not authorized, fail with `tecNO_AUTH`.
- `MPTCanTransfer` flag is not set and AMM creator is not the issuer of MPT, with with `tecNO_PERMISSION`.
- `MPTCanTrade` flag is not set, fail with `tecNO_PERMISSION`.

#### 3.1.2. Deposit JSON Example

```json
{
  "Account": "rffMEZLzDQPNU6VYbWNkgQBtMz6gCYnMAG",
  "Amount": {
    "mpt_issuance_id": "00000002430427B80BD2D09D36B70B969E12801065F22308",
    "value": "100"
  },
  "Amount2": {
    "mpt_issuance_id": "00000003430427B80BD2D09D36B70B969E12801065F22308",
    "value": "100"
  },
  "Asset": {
    "mpt_issuance_id": "00000002430427B80BD2D09D36B70B969E12801065F22308"
  },
  "Asset2": {
    "mpt_issuance_id": "00000003430427B80BD2D09D36B70B969E12801065F22308"
  },
  "Fee": "10",
  "Flags": 524288,
  "TransactionType": "AMMDeposit"
}
```

In addition to the current failure scenarios `AMMDeposit` fails if:

- `Asset`, `Asset2`, `Amount`, or `Amount2` hold MPT and `featureMPTokensV2` amendment is not enabled, fail with `temDISABLED`.
- `MPTokenIssuance` object doesn't exist, fail with `terNO_AMM`.
- `MPToken` object doesn't exist and the account is not the issuer of MPT, fail with `tecNO_AUTH`.
- `MPTLock` flag is set on `MPTokenIssuance`, fail for issuer and holder with `tecFROZEN`.
- `MPTLock` flag is set on `MPToken`, fail for holder with `tecFROZEN`.
- `MPTRequireAuth` flag is set and the account is not authorized, fail with `tecNO_AUTH`.
- `MPTCanTransfer` flag is not set and the account is not the issuer of MPT, fail with `tecNO_PERMISSION`.
- `MPTCanTrade` flag is not set, fail with `tecNO_PERMISSION`.

#### 3.1.3. Withdraw JSON Example

```json
{
  "Account": "rffMEZLzDQPNU6VYbWNkgQBtMz6gCYnMAG",
  "Amount": {
    "mpt_issuance_id": "00000002430427B80BD2D09D36B70B969E12801065F22308",
    "value": "100"
  },
  "Amount2": {
    "mpt_issuance_id": "00000003430427B80BD2D09D36B70B969E12801065F22308",
    "value": "100"
  },
  "Asset": {
    "mpt_issuance_id": "00000002430427B80BD2D09D36B70B969E12801065F22308"
  },
  "Asset2": {
    "mpt_issuance_id": "00000003430427B80BD2D09D36B70B969E12801065F22308"
  },
  "Fee": "10",
  "Flags": 1048576,
  "TransactionType": "AMMWithdraw"
}
```

`AMMWithdraw` creates and authorizes `MPToken` object if Liquidity Provider doesn't own `MPToken` object for a withdrawn token.

In addition to the current failure scenarios `AMMWithdraw` fails if:

- `Asset`, `Asset2`, `Amount`, or `Amount2` hold MPT and `featureMPTokensV2` amendment is not enabled, fail with `temDISABLED`.
- `MPTokenIssuance` object doesn't exist, fail with `terNO_AMM`.
- `MPTLock` flag is set on `MPTokenIssuance`, fail for issuer and holder with `tecFROZEN`. Can withdraw another asset.
- `MPTLock` flag is set on `MPToken`, fail for holder with `tecFROZEN`. Can withdraw another asset.
- `MPTRequireAuth` flag is set and the account is not authorized, fail with `tecNO_AUTH`. Can withdraw another asset.
- `MPTCanTransfer` flag is not set and the account is not the issuer of MPT, fail with `tecNO_PERMISSION`. Can withdraw another asset.
- `MPTCanTrade` flag is not set, fail with `tecNO_PERMISSION`.

#### 3.1.4. Delete JSON Example

```json
{
  "Account": "rJVUeRqDFNs2xqA7ncVE6ZoAhPUoaJJSQm",
  "Asset": {
    "mpt_issuance_id": "00000002430427B80BD2D09D36B70B969E12801065F22308"
  },
  "Asset2": {
    "mpt_issuance_id": "00000003430427B80BD2D09D36B70B969E12801065F22308"
  },
  "Fee": "10",
  "Flags": 0,
  "Sequence": 9,
  "TransactionType": "AMMDelete"
}
```

In addition to the current failure scenarios `AMMDelete` fails if:

- `Asset` or `Asset2` hold MPT and `featureMPTokensV2` amendment is not enabled, fail with `temDISABLED`.

#### 3.1.5. Clawback JSON Example

```json
{
  "TransactionType": "AMMClawback",
  "Account": "rPdYxU9dNkbzC5Y2h4jLbVJ3rMRrk7WVRL",
  "Holder": "rvYAfWj5gh67oV6fW32ZzP3Aw4Eubs59B",
  "Asset": {
    "mpt_issuance_id": "00000002430427B80BD2D09D36B70B969E12801065F22308"
  },
  "Asset2": {
    "mpt_issuance_id": "00000003430427B80BD2D09D36B70B969E12801065F22308"
  },
  "Amount": {
    "mpt_issuance_id": "00000002430427B80BD2D09D36B70B969E12801065F22308",
    "value": "1000"
  },
  "Flags": 1
}
```

`AMMClawback` creates and authorizes `MPToken` object if Liquidity Provider doesn't own `MPToken` object for a withdrawn token.

In addition to the current failure scenarios `AMMClawback` fails if:

- `Asset`, `Asset2`, or `Amount` hold MPT and `featureMPTokensV2` amendment is not enabled, fail with `temDISABLED`.
- `MPTokenIssuance` object doesn't exist, fail with `terNO_AMM`.
- `lsfMPTCanClawback` flag is not not set, fail with `tecNO_PERMISSION`.

### 3.2. CheckCreate JSON Example

```json
{
  "TransactionType": "CheckCreate",
  "Account": "rUn84CUYbNjRoTQ6mSW7BVJPSVJNLb1QLo",
  "Destination": "rfkE1aSy9G8Upk4JssnwBxhEv5p4mn2KTy",
  "SendMax": {
    "mpt_issuance_id": "00000003430427B80BD2D09D36B70B969E12801065F22308",
    "value": "100"
  },
  "Expiration": 570113521,
  "InvoiceID": "6F1DFD1D0FE8A32E40E1F2C05CF1C15545BAB56B617F9C6C2D63A6B704BEF59B",
  "DestinationTag": 1,
  "Fee": "12"
}
```

In addition to the current failure scenarios `CheckCreate` fails if:

- `SendMax` holds MPT and `featureMPTokensV2` amendment is not enabled, fail with `temDISABLED`.
- `MPTokenIssuance` object doesn't exist, fail with `tecOBJECT_NO_FOUND`.
- `MPTLock` flag is set on `MPTokenIssuance`, fail for issuer and holder with `tecFROZEN`.
- `MPTLock` flag is set on `MPToken`, fail for holder as source and destination with `tecFROZEN`.
- `MPTCanTrade` flag is not set, fail with `tecNO_PERMISSION`.

### 3.3. CheckCash Transaction

```json
{
  "Account": "rfkE1aSy9G8Upk4JssnwBxhEv5p4mn2KTy",
  "TransactionType": "CheckCash",
  "Amount": {
    "mpt_issuance_id": "00000003430427B80BD2D09D36B70B969E12801065F22308",
    "value": "100"
  },
  "CheckID": "838766BA2B995C00744175F69A1B11E32C3DBC40E64801A4056FCBD657F57334",
  "Fee": "12"
}
```

In addition to the current failure scenarios `CheckCash` fails if:

- `MPTokenIssuance` object doesn't exist, fail with `tecNO_ENTRY`.
- `MPToken` object doesn't exist and the account is not the issuer of MPT, fail with `tecPATH_PARTIAL`.
- `MPTLock` flag is set on `MPTokenIssuance`, fail with `tecPATH_PARTIAL` if source and destination are holders.
  Fail with `tecFROZEN` if source is issuer and destination is holder.
- `MPTLock` flag is set on `MPToken`, fail for issuer and holder as destination with `tecPATH_PARTIAL`. Fail for holder as source with `tecFROZEN`.
- `MPTRequireAuth` flag is set and the account is not authorized, fail with `tecNO_AUTH`.
- `MPTCanTransfer` flag is not set and the account is not the issuer of MPT, fail with `tecPATH_PARTIAL`.
- `MPTCanTrade` flag is not set, fail with `tecNO_PERMISSION`.

### 3.4. OfferCreate Transaction

```json
{
  "Account": "rMTysmc799PzTvK228jNaua6w3b6VgYUjw",
  "Fee": "10",
  "Flags": 0,
  "TakerGets": {
    "mpt_issuance_id": "00000003430427B80BD2D09D36B70B969E12801065F22308",
    "value": "100"
  },
  "TakerPays": {
    "mpt_issuance_id": "00000002430427B80BD2D09D36B70B969E12801065F22308",
    "value": "100"
  },
  "TransactionType": "OfferCreate"
}
```

`OfferCreate` can have any token combination of `TakerGets` and `TakerPays`. I.e., in addition to the current combination of XRP/IOU and IOU/IOU tokens, `OfferCreate` can have XRP/MPT, IOU/MPT, and MPT/MPT tokens. `OfferCreate` automatically creates and authorizes `MPToken` object for the offer's owner account when the offer is consumed and `MPToken` object doesn't exist for `TakerPays`'s `mpt_issuance_id`.

In addition to the current failure scenarios `OfferCreate` fails if:

- `MPTokenIssuance` object doesn't exist, fail with `tecOBJECT_NOT_FOUND` for `TakerPays` and `tecUNFUNDED_OFFER` for `TakerGets`.
- `MPToken` object doesn't exist and the account is not the issuer of MPT, fail with `tecUNFUNDED_OFFER` for `TakerGets`.
- `MPTLock` flag is set and the account is not the issuer of MPT, fail with `tecUNFUNDED_OFFER` for `TakerGets`. Create but not cross the offer for `TakerPays`.
- `MPTRequireAuth` flag is set and the account is not authorized, fail with `tecUNFUNDED_OFFER`.
- `MPTCanTransfer` flag is not set and the account is not the issuer of MPT. `OfferCreate` succeeds but doesn't cross other offers owned by holders. It crosses offers owned by an issuer. If `MPTCanTransfer` is cleared after an offer is created then this offer is removed from the order book on offer crossing or cross-currency payment.
- `MPTCanTrade` flag is not set, fail with `tecNO_PERMISSION`. If `MPTCanTrade` is cleared after an offer is created then this offer is removed from the order book on offer crossing or cross-currency payment.

MPT tokens are not adjusted for `TickSize` in the offers.

### 3.5. Payment Transaction

```json
{
  "Account": "rJ85Mok8YRNxSo7NnxKGrPuk29uAeZQqwZ",
  "DeliverMax": {
    "mpt_issuance_id": "00000010A407AF5856CCF3C42619DAA925813FC955C72983",
    "value": "100"
  },
  "DeliverMin": {
    "mpt_issuance_id": "00000010A407AF5856CCF3C42619DAA925813FC955C72983",
    "value": "90"
  },
  "Destination": "rHKBGB4vhnnVFmfrj4sUx3F9riz2CiHgCK",
  "Fee": "10",
  "Flags": 131072,
  "Paths": [
    [
      {
        "mpt_issuance_id": "00000004A407AF5856CCF3C42619DAA925813FC955C72983"
      },
      {
        "mpt_issuance_id": "0000000AA407AF5856CCF3C42619DAA925813FC955C72983"
      },
      {
        "mpt_issuance_id": "00000010A407AF5856CCF3C42619DAA925813FC955C72983"
      }
    ]
  ],
  "SendMax": "100000000"
}
```

`Payment` can have any cross-token payment combination. I.e., in addition to the current combination of XRP/IOU and IOU/IOU cross-token payment, `Payment` can have XRP/MPT, IOU/MPT, and MPT/MPT cross-token payment. MPT can be used to specify `Paths`, in which case `mpt_issuance_id` should be used instead of `currency` and `issuer` as shown in the example above. MPT doesn't support payment rippling. `mpt_issuance_id` identifies a unique MPT and it's impossible to reference the same MPT with different issuer.

In addition to the current failure scenarios `Payment` fails if:

- `MPTokenIssuance` object doesn't exist, fail with `tecOBJECT_NO_FOUND`.
- `MPToken` object doesn't exist and the account is not the issuer of MPT, fail with `tecNO_AUTH`.
- `MPTLock` flag is set on `MPTokenIssuance`, fail with `tecPATH_DRY`.
- `MPTLock` flag is set on `MPToken`, fail with `tecPATH_DRY`.
- `MPTRequireAuth` flag is set and the account is not authorized. Any transfer between unauathorized accounts fail with `tecNO_AUTH`.
- `MPTCanTransfer` flag is not set. Any transfer between unauthorized accounts fail with `tecPATH_PARTIAL`.
- `MPTCanTrade` is not set, fail with `tecPATH_DRY`.

To ensure asset transfer consistency during offer crossing and payment, the following logic is applied.
`TakerGets` asset is transferred if:

- `MPTCanTransfer` is set
- The offer's owner is the issuer
- The asset is the delivered asset and the destination account is the issuer

`TakerPays` is transferred if:

- `MPTCanTransfer` is set
- The offer's owner is the issuer
- The asset is the source asset and the source account is the issuer
- The offer's `TakerPays` and `TakerGets` are not the source and destination assets

### 3.6. API's

To use MPT in API's, `currency` and `issuer` fields must be replaced with `mpt_issuance_id` field as shown in the examples below.

#### 3.6.1. path_find

```json
{
  "command": "path_find",
  "subcommand": "create",
  "source_account": "r9cZA1mLK5R5Am25ArfXFmqgNwjZgnfk59",
  "destination_account": "r9cZA1mLK5R5Am25ArfXFmqgNwjZgnfk59",
  "destination_amount": {
    "mpt_issuance_id": "00000002430427B80BD2D09D36B70B969E12801065F22308",
    "value": "100"
  }
}
```

#### 3.6.2. ripple_path_find

```json
{
  "command": "ripple_path_find",
  "source_account": "r9cZA1mLK5R5Am25ArfXFmqgNwjZgnfk59",
  "source_currencies": [
    {
      "mpt_issuance_id": "00000002430427B80BD2D09D36B70B969E12801065F22308"
    }
  ],
  "destination_account": "r9cZA1mLK5R5Am25ArfXFmqgNwjZgnfk59",
  "destination_amount": {
    "mpt_issuance_id": "00000002430427B80BD2D09D36B70B969E12801065F22308",
    "value": "100"
  }
}
```

#### 3.6.3. amm_info

```json
{
  "command": "amm_info",
  "Asset": {
    "mpt_issuance_id": "00000002430427B80BD2D09D36B70B969E12801065F22308"
  },
  "Asset2": {
    "mpt_issuance_id": "00000003430427B80BD2D09D36B70B969E12801065F22308"
  }
}
```

#### 3.6.4. ledger_entry

```json
{
  "command": "ledger_entry",
  "amm": {
    "Asset": {
      "mpt_issuance_id": "00000002430427B80BD2D09D36B70B969E12801065F22308"
    },
    "Asset2": {
      "mpt_issuance_id": "00000003430427B80BD2D09D36B70B969E12801065F22308"
    }
  },
  "ledger_index": "validated"
}
```

#### 3.6.5. book_offers

```json
{
  "id": 4,
  "command": "book_offers",
  "taker": "r9cZA1mLK5R5Am25ArfXFmqgNwjZgnfk59",
  "taker_gets": {
    "mpt_issuance_id": "00000002430427B80BD2D09D36B70B969E12801065F22308"
  },
  "taker_pays": {
    "currency": "USD",
    "issuer": "rvYAfWj5gh67oV6fW32ZzP3Aw4Eubs59B"
  },
  "limit": 10
}
```

## 2. Security

While Multipurpose Tokens (MPT) inherit the core security model of the XRPL (including issuer-controlled freezes and authorization), this integration acknowledges the architectural shift from RippleState to MPT objects. Security is maintained by performing real-time verification of MPT-specific flags and ensuring that DEX quality calculations account for MPT-specific decimal scaling to prevent rounding exploits. Furthermore, the DEX engine treats MPT-specific freezes as immediate execution barriers, mirroring the existing IOU freeze behavior.

# Appendices

## `STIssue` serialization

`STIssue` type defines AMM token pair used in `AMMDeposit`, `AMMWithdraw`, and `AMMDelete` transactions. However, its current serialization format presents a challenge for integrating MPT into the DEX.

Currently, `STIssue` is serialized as a 160-bit `currency` code followed by a 160-bit `account` address. This format doesn't have spare bits to indicate whether the serialized `STIssue` represents a `currency` and `account` or an `mpt_issuance_id`. I.e. reading 320 bits doesn't provide enough information to unequivocally distinguish `currency` and `account` from `mpt_issuance_id`.

### Proposed Solutions

#### Splitting `mpt_issuance_id` with black hole account flag:

- This option breaks down `mpt_issuance_id` into its sequence number and account.
- The account is serialized in the first 160 bits, followed by a dedicated black hole account in the next 160 bits.
- Finally, the sequence number (32 bits) is serialized last.
- Deserialization method reads 320-bit `currency` and `account`. If `account` is the black hole account then additional 32 bits have to be read and deserialized into a sequence number.
- This method maintains backward compatibility, doesn’t require a separate amendment, but adds 32 extra bits compared to the current format, or adds 160 bits compared to 192 bits required for serializing `mpt_issuance_id`.

| 160 bits MPT issuer account | 160 bits black-hole account | 32 bits sequence |
| --------------------------- | --------------------------- | ---------------- |
