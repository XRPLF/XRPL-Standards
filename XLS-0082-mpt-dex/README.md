<pre>
  xls: 82
  title: MPT Integration into DEX
  description: Adds Multi-purpose token support for XRPL DEX
  author: Gregory Tsipenyuk <gtsipenyuk@ripple.com>
  proposal-from: https://github.com/XRPLF/XRPL-Standards/discussions/231
  status: Final
  category: Amendment
  requires: XLS-33, XLS-30
  created: 2024-09-19
  updated: 2026-02-10
</pre>

# MPT Integration into DEX

## Abstract

This proposal introduces a new amendment `MPTVersion2` as an extension to [XLS-33 Multi-Purpose Tokens](../XLS-0033-multi-purpose-tokens/README.md). `MPTVersion2` amendment enables Multi-purpose token (MPT) support on the XRPL DEX.

## 1. Overview

The integration of Multi-Purpose Tokens (MPT) into the XRP Ledger Decentralized Exchange (DEX) focuses on extending the functional reach of existing trading mechanisms without introducing new on-ledger objects or modifying core state structures. By leveraging the existing ledger primitives, this update enables standard DEX transactions to natively support MPTs as a valid asset class. This specification outlines the necessary schema updates for transaction requests and provides comprehensive JSON examples to illustrate the interoperability between MPTs, XRP, and standard IOUs. Furthermore, this document details the expanded set of failure scenarios and transaction result codes specific to MPT trading, ensuring robust error handling for cross-asset liquidity paths and order-matching logic. For a comprehensive description of all transactions refer to [XRPL documentation](https://xrpl.org/docs/references/protocol/transactions)

Current transactions, which interact with XRPL DEX are:

- `AMMCreate`: Create a new Automated Market Maker (AMM) instance for trading a pair of assets (fungible tokens or XRP).
- `AMMDeposit`: Deposit funds into an AMM instance and receive the AMM's liquidity provider tokens (LP Tokens) in exchange.
- `AMMWithdraw`: Withdraw assets from an AMM instance by returning the AMM's liquidity provider tokens (LP Tokens).
- `AMMClawback`: Enable token issuers to claw back tokens from wallets that have deposited into AMM pools.
- `AMMDelete`: Delete an empty AMM instance that could not be fully deleted automatically.
- `CheckCreate`: Create a Check object in the ledger, which is a deferred payment that can be cashed by its intended destination.
- `CheckCash`: Attempts to redeem a Check object in the ledger to receive up to the amount authorized by the corresponding CheckCreate transaction.
- `OfferCreate`: An OfferCreate transaction places an Offer in the decentralized exchange.
- `Payment`: A Payment transaction represents a transfer of value from one account to another.

MPT supports all of the above transactions. MPT can be combined with IOU and XRP tokens in the transactions. For instance, a Payment could be a cross-token payment from MPT token to IOU token; AMM can be created for XRP and MPT token-pair; an order book offer can be created to buy some MPT token and to sell another MPT token. MPT doesn't modify the transactions fields, flags, and functionality. However, the JSON of the MPT amount field differs from the JSON of the IOU amount field. Instead of `currency` and `issuer`, MPT is identified by `mpt_issuance_id`. MPT amount `value` is INT or UINT, which must be less or equal to $63^2 - 1$. Below are the examples of JSON MPT amount and JSON MPT asset:

```json
{
  "Amount": {
    "mpt_issuance_id": "00000003430427B80BD2D09D36B70B969E12801065F22308",
    "value": "110"
  },
  "Asset": {
    "mpt_issuance_id": "00000002430427B80BD2D09D36B70B969E12801065F22308"
  }
}
```

Any transaction with MPT `Amount` or `Asset` have to use JSON format as described above. For any transaction, which uses MPT token, the token has to be created first by an issuer with `MPTokenIssuanceCreate` transaction and in most cases, except for `AMMCreate`, `AMMWithdraw`, `AMMClawback`, `CheckCash`, and `OfferCreate`, the token has to be authorized by the holder account with `MPTokenAuthorize` transaction as described in [XLS-33d](../XLS-0033d-multi-purpose-tokens/README.md). `MPTokenAuthorize` creates `MPToken` object, owned by a holder account. In addition, `MPTokenIssuanceCreate` must have the following flags set:

- `lsfMPTCanTrade`, in order for individual holders to trade their balances using the XRP Ledger DEX or AMM.
- `lsfMPTCanTransfer`, in order for the tokens held by non-issuers to be transferred to other accounts.

## 2. Transaction: AMMCreate

Any token or both tokens in `AMMCreate` transaction can be MPT. I.e., in addition to the current combination of XRP/IOU and IOU/IOU token pair, `AMMCreate` can have XRP/MPT, IOU/MPT, and MPT/MPT token pair. Each MPT in the pair is identified by `mpt_issuance_id`. If both tokens are MPT then each token must have a unique `mpt_issuance_id`. In case of `AMMCreate` the token pair is identified by `Amount` and `Amount2`.

### 2.1. Fields

We do not introduce new fields.

### 2.2. Failure Conditions

We extend the `AMMCreate` with the following failure conditions, where `MPTokenIssuance` refers to the ledger object defining the specific MPT type identified in the transaction's `Amount` or `Amount2` fields; `MPToken` refers to the ledger object representing the specific MPT balance of the account executing the transaction (if that account is not the issuer); and flags refer to those set on the `MPTokenIssuance` object unless explicitly stated as being set on the individual `MPToken` object:

1. `Amount` or `Amount2` hold MPT and `featureMPTokensV2` amendment is not enabled, fail with `temDISABLED`.
2. `MPTokenIssuance` object doesn't exist, fail with `tecOBJECT_NOT_FOUND`.
3. `MPToken` object doesn't exist and AMM creator is not the issuer of MPT, fail with `tecNO_AUTH`.
4. `MPTLock` flag is set on `MPTokenIssuance`, fail for issuer and holder with `tecFROZEN`.
5. `MPTLock` flag is set on `MPToken`, fail for holder with `tecFROZEN`.
6. `MPTRequireAuth` flag is set and AMM creator is not authorized, fail with `tecNO_AUTH`.
7. `MPTCanTransfer` flag is not set and AMM creator is not the issuer of MPT, with `tecNO_PERMISSION`.
8. `MPTCanTrade` flag is not set, fail with `tecNO_PERMISSION`.

### 2.3. State Changes

On success `AMMCreate` creates and authorizes `MPToken` object for each MPT token for AMM pseudo-account.

### 2.4. Example JSON

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

## 3. Transaction: AMMDeposit

`AMMDeposit` is identified by `Asset` and `Asset2` with the token type corresponding to `Amount` and `Amount2` of `AMMCreate`. `Asset` and `Asset2` are `STIssue` type, which represents a token by `currency` and `issuer`. If `STIssue` type represents MPT then `mpt_issuance_id` must be used instead. `AMMDeposit` has optional fields `Amount` and `Amount2`, which if present must match the type of `Asset` and `Asset2` respectively.

### 3.1. Fields

We do not introduce new fields.

### 3.2. Failure Conditions

We extend the `AMMDeposit` with the following failure conditions, where `MPTokenIssuance` refers to the ledger object defining the specific MPT type identified in the transaction's `Amount` or `Amount2` fields; `MPToken` refers to the ledger object representing the specific MPT balance of the account executing the transaction (if that account is not the issuer); and flags refer to those set on the `MPTokenIssuance` object unless explicitly stated as being set on the individual `MPToken` object:

1. `Asset`, `Asset2`, `Amount`, or `Amount2` hold MPT and `featureMPTokensV2` amendment is not enabled, fail with `temDISABLED`.
2. `MPTokenIssuance` object doesn't exist, fail with `terNO_AMM`.
3. `MPToken` object doesn't exist and the account is not the issuer of MPT, fail with `tecNO_AUTH`.
4. `MPTLock` flag is set on `MPTokenIssuance`, fail for issuer and holder with `tecFROZEN`.
5. `MPTLock` flag is set on `MPToken`, fail for holder with `tecFROZEN`.
6. `MPTRequireAuth` flag is set and the account is not authorized, fail with `tecNO_AUTH`.
7. `MPTCanTransfer` flag is not set and the account is not the issuer of MPT, fail with `tecNO_PERMISSION`.
8. `MPTCanTrade` flag is not set, fail with `tecNO_PERMISSION`.

### 3.3. State Changes

We do not introduce new state changes.

### 3.4. Example JSON

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

## 4. Transaction: AMMWithdraw

`AMMWithdraw` is identified by `Asset` and `Asset2` with the token type corresponding to `Amount` and `Amount2` of `AMMCreate`. `Asset` and `Asset2` are `STIssue` type, which represents a token by `currency` and `issuer`. If `STIssue` type represents MPT then `mpt_issuance_id` must be used instead. `AMMWithdraw` has optional fields `Amount` and `Amount2`, which if present must match the type of `Asset` and `Asset2` respectively.

### 4.1. Fields

We do not introduce new fields.

### 4.2. Failure Conditions

We extend the `AMMWithdraw` with the following failure conditions, where `MPTokenIssuance` refers to the ledger object defining the specific MPT type identified in the transaction's `Amount` or `Amount2` fields; `MPToken` refers to the ledger object representing the specific MPT balance of the account executing the transaction (if that account is not the issuer); and flags refer to those set on the `MPTokenIssuance` object unless explicitly stated as being set on the individual `MPToken` object:

1. `Asset`, `Asset2`, `Amount`, or `Amount2` hold MPT and `featureMPTokensV2` amendment is not enabled, fail with `temDISABLED`.
2. `MPTokenIssuance` object doesn't exist, fail with `terNO_AMM`.
3. `MPTLock` flag is set on `MPTokenIssuance`, fail for issuer and holder with `tecFROZEN`. Can withdraw another asset.
4. `MPTLock` flag is set on `MPToken`, fail for holder with `tecFROZEN`. Can withdraw another asset.
5. `MPTRequireAuth` flag is set and the account is not authorized, fail with `tecNO_AUTH`. Can withdraw another asset.
6. `MPTCanTransfer` flag is not set and the account is not the issuer of MPT, fail with `tecNO_PERMISSION`. Can withdraw another asset.
7. `MPTCanTrade` flag is not set, fail with `tecNO_PERMISSION`.

### 4.3. State Changes

On success `AMMWithdraw` creates and authorizes `MPToken` object if Liquidity Provider doesn't own `MPToken` object for a withdrawn token.

### 4.4. Example JSON

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

## 5. Transaction: AMMDelete

`AMMDelete` is identified by `Asset` and `Asset2` with the token type corresponding to `Amount` and `Amount2` of `AMMCreate`. `Asset` and `Asset2` are `STIssue` type, which represents a token by `currency` and `issuer`. If `STIssue` type represents MPT then `mpt_issuance_id` must be used instead.

### 5.1. Fields

We do not introduce new fields.

### 5.2. Failure Conditions

We extend the `AMMDelete` transaction with the following failure conditions:

- `Asset` or `Asset2` hold MPT and `featureMPTokensV2` amendment is not enabled, fail with `temDISABLED`.

### 5.3. State Changes

We do not introduce new state changes.

### 5.4. Example JSON

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

## 6. Transaction: AMMClawback

`AMMClawback` is identified by `Asset` and `Asset2` with the token type corresponding to `Amount` and `Amount2` of `AMMCreate`. `Asset` and `Asset2` are `STIssue` type, which represents a token by `currency` and `issuer`. If `STIssue` type represents MPT then `mpt_issuance_id` must be used instead. `AMMClawback` has optional field `Amount`, which if present must match the type of `Asset`.

### 6.1. Fields

We do not introduce new fields.

### 6.2. Failure Conditions

We extend the `AMMClawback` transaction with the following failure conditions, where `MPTokenIssuance` refers to the ledger object defining the specific MPT type identified in the transaction's `Amount`:

1. `Asset`, `Asset2`, or `Amount` hold MPT and `featureMPTokensV2` amendment is not enabled, fail with `temDISABLED`.
2. `MPTokenIssuance` object doesn't exist, fail with `terNO_AMM`.
3. `lsfMPTCanClawback` flag is not set on `MPTokenIssuance`, fail with `tecNO_PERMISSION`.

### 6.3. State Changes

On success `AMMClawback` creates and authorizes `MPToken` object if Liquidity Provider doesn't own `MPToken` object for a clawbacked token.

### 6.4. Example JSON

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

## 7. Transaction: CheckCreate

If `SendMax` field is MPT then it is identified by `mpt_issuance_id`.

### 7.1. Fields

We do not introduce new fields.

### 7.2. Failure Conditions

We extend the `CheckCreate` with the following failure conditions, where `MPTokenIssuance` refers to the ledger object defining the specific MPT type identified in the transaction's `SendMax`; and flags refer to those set on the `MPTokenIssuance` object unless explicitly stated as being set on the individual `MPToken` object:

1. `SendMax` holds MPT and `featureMPTokensV2` amendment is not enabled, fail with `temDISABLED`.
2. `MPTokenIssuance` object doesn't exist, fail with `tecOBJECT_NO_FOUND`.
3. `MPTLock` flag is set on `MPTokenIssuance`, fail for issuer and holder with `tecFROZEN`.
4. `MPTLock` flag is set on `MPToken`, fail for holder as source and destination with `tecFROZEN`.
5. `MPTCanTrade` flag is not set, fail with `tecNO_PERMISSION`.

### 7.3. State Changes

We do not introduce new state changes.

### 7.4. Example JSON

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

## 8. Transaction: CheckCash

If `Amount` or `DeliverMin` fields are MPT then they are identified by `mpt_issuance_id`. `mpt_issuance_id` of `DeliverMin` and `Amount` must match.

### 8.1. Fields

We do not introduce new fields.

### 8.2. Failure Conditions

We extend the `CheckCash` with the following failure conditions, where `MPTokenIssuance` refers to the ledger object defining the specific MPT type identified in the transaction's `Amount` or `DeliverMin` fields; `MPToken` refers to the ledger object representing the specific MPT balance of the account executing the transaction (if that account is not the issuer); and flags refer to those set on the `MPTokenIssuance` object unless explicitly stated as being set on the individual `MPToken` object:

1. `MPTokenIssuance` object doesn't exist, fail with `tecNO_ENTRY`.
2. `MPToken` object doesn't exist and the account is not the issuer of MPT, fail with `tecPATH_PARTIAL`.
3. `MPTLock` flag is set on `MPTokenIssuance`, fail with `tecPATH_PARTIAL` if source and destination are holders.
   Fail with `tecFROZEN` if source is issuer and destination is holder.
4. `MPTLock` flag is set on `MPToken`, fail for issuer and holder as destination with `tecPATH_PARTIAL`. Fail for holder as source with `tecFROZEN`.
5. `MPTRequireAuth` flag is set and the account is not authorized, fail with `tecNO_AUTH`.
6. `MPTCanTransfer` flag is not set and the account is not the issuer of MPT, fail with `tecPATH_PARTIAL`.
7. `MPTCanTrade` flag is not set, fail with `tecNO_PERMISSION`.

### 8.3. State Changes

On success `CheckCash` creates and authorizes `MPToken` object if the account doesn't own `MPToken` object.

### 8.4. Example JSON

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

## 9. Transaction: OfferCreate

`OfferCreate` can have any token combination of `TakerGets` and `TakerPays`. I.e., in addition to the current combination of XRP/IOU and IOU/IOU tokens, `OfferCreate` can have XRP/MPT, IOU/MPT, and MPT/MPT tokens. If `TakerPays` or `TakerGets` fields are MPT then they are identified by mpt_issuance_id.

To ensure asset transfer consistency on offer crossing, the following logic is applied to the offer's assets transfer between the accounts.

`TakerGets` asset is transferred if:

- `MPTCanTransfer` is set
- The offer's owner is the issuer
- The asset is the delivered asset and the destination account is the issuer

`TakerPays` is transferred if:

- `MPTCanTransfer` is set
- The offer's owner is the issuer
- The asset is the source asset and the source account is the issuer
- The offer's `TakerPays` and `TakerGets` are not the source and destination assets

MPT tokens are not adjusted for `TickSize` in the offers.

### 9.1. Fields

We do not introduce new fields.

### 9.2. Failure Conditions

We extend the `OfferCreate` with the following failure conditions, where `MPTokenIssuance` refers to the ledger object defining the specific MPT type identified in the transaction's `TakerPays` or `TakerGets` fields; `MPToken` refers to the ledger object representing the specific MPT balance of the account executing the transaction (if that account is not the issuer); and flags refer to those set on the `MPTokenIssuance` object unless explicitly stated as being set on the individual `MPToken` object:

1. `MPTokenIssuance` object doesn't exist, fail with `tecOBJECT_NOT_FOUND` for `TakerPays` and `tecUNFUNDED_OFFER` for `TakerGets`.
2. `MPToken` object doesn't exist and the account is not the issuer of MPT, fail with `tecUNFUNDED_OFFER` for `TakerGets`.
3. `MPTLock` flag is set and the account is not the issuer of MPT, fail with `tecUNFUNDED_OFFER` for `TakerGets`. Create but not cross the offer for `TakerPays`.
4. `MPTRequireAuth` flag is set and the account is not authorized, fail with `tecUNFUNDED_OFFER`.
5. `MPTCanTransfer` flag is not set and the account is not the issuer of MPT. `OfferCreate` succeeds but doesn't cross other offers owned by holders. It crosses offers owned by an issuer. If `MPTCanTransfer` is cleared after an offer is created then this offer is removed from the order book on offer crossing or cross-currency payment.
6. `MPTCanTrade` flag is not set, fail with `tecNO_PERMISSION`. If `MPTCanTrade` is cleared after an offer is created then this offer is removed from the order book on offer crossing or cross-currency payment.

### 9.3. State Changes

On success `OfferCreate` creates and authorizes `MPToken` object for the offer's owner account if the offer is consumed and `MPToken` object doesn't exist for `TakerPays`'s `mpt_issuance_id`.

### 9.4. Example JSON

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

## 10. Transaction: Payment

`Payment` can have any cross-token payment combination. I.e., in addition to the current combination of XRP/IOU and IOU/IOU cross-token payment, `Payment` can have XRP/MPT, IOU/MPT, and MPT/MPT cross-token payment. MPT can be used to specify `Paths`, in which case `mpt_issuance_id` should be used instead of `currency` and `issuer` as shown in the `JSON` example below. MPT doesn't support payment rippling. `mpt_issuance_id` identifies a unique MPT. It's impossible to reference the same MPT with different issuer. If `Amount`, `DeliverMax`, `DeliverMin`, or `SendMax` fields are MPT then they are identified by `mpt_issuance_id`.

### 10.1. Fields

We do not introduce new fields.

### 10.2. Failure Conditions

We extend the `Payment` with the following failure conditions, where `MPTokenIssuance` refers to the ledger object defining the specific MPT type identified in the transaction's `Amount` or `SendMax` fields; `MPToken` refers to the ledger object representing the specific MPT balance of the account executing the transaction (if that account is not the issuer); and flags refer to those set on the `MPTokenIssuance` object unless explicitly stated as being set on the individual `MPToken` object:

1. `MPTokenIssuance` object doesn't exist, fail with `tecOBJECT_NO_FOUND`.
2. `MPToken` object doesn't exist and the account is not the issuer of MPT, fail with `tecNO_AUTH`.
3. `MPTLock` flag is set on `MPTokenIssuance`, fail with `tecPATH_DRY`.
4. `MPTLock` flag is set on `MPToken`, fail with `tecPATH_DRY`.
5. `MPTRequireAuth` flag is set and the account is not authorized. Any transfer between unauthorized accounts fail with `tecNO_AUTH`.
6. `MPTCanTransfer` flag is not set. Any transfer between unauthorized accounts fail with `tecPATH_PARTIAL`.
7. `MPTCanTrade` is not set, fail with `tecPATH_DRY`.

### 10.3 State Changes

We do not introduce new state changes.

### 10.4. Example JSON

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

## 11. RPC path_find

### 11.1. Request Fields

We do not introduce new fields.

### 11.2 Response Fields

We do not introduce new fields.

### 11.3 Example Request

```json
{
  "command": "path_find",
  "subcommand": "create",
  "destination_account": "rPMh7Pi9ct699iZUTWaytJUoHcJ7cgyziK",
  "destination_amount": {
    "mpt_issuance_id": "000000045C488AAC5813270850685FFD89F4A4A8F4CD4C83",
    "value": "-1"
  },
  "send_max": "100000000000000",
  "source_account": "rG1QQv2nh2gr7RCZ1P8YYcBUKCCN633jCn"
}
```

### 11.4 Example Response

```json
{
  "alternatives": [
    {
      "destination_amount": {
        "mpt_issuance_id": "000000045C488AAC5813270850685FFD89F4A4A8F4CD4C83",
        "value": "100"
      },
      "paths_canonical": [],
      "paths_computed": [
        [
          {
            "issuer": "r9QxhA9RghPZBbUchA9HkrmLKaWvkLXU29",
            "mpt_issuance_id": "000000045C488AAC5813270850685FFD89F4A4A8F4CD4C83",
            "type": 96
          }
        ]
      ],
      "source_amount": "100000000"
    }
  ],
  "destination_account": "rPMh7Pi9ct699iZUTWaytJUoHcJ7cgyziK",
  "destination_amount": {
    "mpt_issuance_id": "000000045C488AAC5813270850685FFD89F4A4A8F4CD4C83",
    "value": "-1"
  },
  "destination_currencies": [
    "000000045C488AAC5813270850685FFD89F4A4A8F4CD4C83",
    "XRP"
  ],
  "full_reply": true,
  "ledger_current_index": 8,
  "source_account": "rG1QQv2nh2gr7RCZ1P8YYcBUKCCN633jCn",
  "validated": false
}
```

## 12. RPC ripple_path_find

### 12.1. Request Fields

We do not introduce new fields.

### 12.2 Response Fields

We do not introduce new fields.

### 12.3 Example Request

```json
{
  "command": "ripple_path_find",
  "destination_account": "rPMh7Pi9ct699iZUTWaytJUoHcJ7cgyziK",
  "destination_amount": {
    "mpt_issuance_id": "000000045C488AAC5813270850685FFD89F4A4A8F4CD4C83",
    "value": "-1"
  },
  "send_max": "100000000000000",
  "source_account": "rG1QQv2nh2gr7RCZ1P8YYcBUKCCN633jCn"
}
```

### 12.4 Example Response

```json
{
  "alternatives": [
    {
      "destination_amount": {
        "mpt_issuance_id": "000000045C488AAC5813270850685FFD89F4A4A8F4CD4C83",
        "value": "100"
      },
      "paths_canonical": [],
      "paths_computed": [
        [
          {
            "issuer": "r9QxhA9RghPZBbUchA9HkrmLKaWvkLXU29",
            "mpt_issuance_id": "000000045C488AAC5813270850685FFD89F4A4A8F4CD4C83",
            "type": 96
          }
        ]
      ],
      "source_amount": "100000000"
    }
  ],
  "destination_account": "rPMh7Pi9ct699iZUTWaytJUoHcJ7cgyziK",
  "destination_amount": {
    "mpt_issuance_id": "000000045C488AAC5813270850685FFD89F4A4A8F4CD4C83",
    "value": "-1"
  },
  "destination_currencies": [
    "000000045C488AAC5813270850685FFD89F4A4A8F4CD4C83",
    "XRP"
  ],
  "full_reply": true,
  "ledger_current_index": 8,
  "source_account": "rG1QQv2nh2gr7RCZ1P8YYcBUKCCN633jCn",
  "validated": false
}
```

## 13. RPC amm_info

### 13.1. Request Fields

We do not introduce new fields.

### 13.2 Response Fields

We do not introduce new fields.

### 13.3 Example Request

```json
{
  "command": "amm_info",
  "asset": {
    "mpt_issuance_id": "000000045C488AAC5813270850685FFD89F4A4A8F4CD4C83"
  },
  "asset2": {
    "mpt_issuance_id": "000000055C488AAC5813270850685FFD89F4A4A8F4CD4C83"
  }
}
```

### 13.4 Example Response

```json
{
  "result": {
    "amm": {
      "account": "rKM4AJ3JkgmdhKkJLpBcRUSZo7Prq13BYS",
      "amount": {
        "mpt_issuance_id": "000000045C488AAC5813270850685FFD89F4A4A8F4CD4C83",
        "value": "100"
      },
      "amount2": {
        "mpt_issuance_id": "000000055C488AAC5813270850685FFD89F4A4A8F4CD4C83",
        "value": "100"
      },
      "asset2_frozen": false,
      "asset_frozen": false,
      "auction_slot": {
        "account": "r9QxhA9RghPZBbUchA9HkrmLKaWvkLXU29",
        "discounted_fee": 0,
        "expiration": "2000-01-02T00:00:40+0000",
        "price": {
          "currency": "033EE62589A944E08A96DC309D6ADBD2FBCFBD11",
          "issuer": "rKM4AJ3JkgmdhKkJLpBcRUSZo7Prq13BYS",
          "value": "0"
        },
        "time_interval": 0
      },
      "lp_token": {
        "currency": "033EE62589A944E08A96DC309D6ADBD2FBCFBD11",
        "issuer": "rKM4AJ3JkgmdhKkJLpBcRUSZo7Prq13BYS",
        "value": "100"
      },
      "trading_fee": 0,
      "vote_slots": [
        {
          "account": "r9QxhA9RghPZBbUchA9HkrmLKaWvkLXU29",
          "trading_fee": 0,
          "vote_weight": 100000
        }
      ]
    },
    "ledger_current_index": 8,
    "status": "success",
    "validated": false
  }
}
```

## 14. RPC ledger_entry

### 14.1. Request Fields

We do not introduce new fields.

### 14.2 Response Fields

We do not introduce new fields.

### 14.3 Example Request

```json
{
  "command": "ledger_entry",
  "amm": {
    "asset": {
      "mpt_issuance_id": "000000045C488AAC5813270850685FFD89F4A4A8F4CD4C83"
    },
    "asset2": {
      "mpt_issuance_id": "000000055C488AAC5813270850685FFD89F4A4A8F4CD4C83"
    }
  }
}
```

### 14.4 Example Response

```json
{
  "index": "3B391EB8C901D850E698B80C13C98A937A8F9DF30F826D6CEB26F5616902EAF4",
  "ledger_current_index": 8,
  "node": {
    "Account": "rKM4AJ3JkgmdhKkJLpBcRUSZo7Prq13BYS",
    "Asset": {
      "mpt_issuance_id": "000000045C488AAC5813270850685FFD89F4A4A8F4CD4C83"
    },
    "Asset2": {
      "mpt_issuance_id": "000000055C488AAC5813270850685FFD89F4A4A8F4CD4C83"
    },
    "AuctionSlot": {
      "Account": "r9QxhA9RghPZBbUchA9HkrmLKaWvkLXU29",
      "Expiration": 86440,
      "Price": {
        "currency": "033EE62589A944E08A96DC309D6ADBD2FBCFBD11",
        "issuer": "rKM4AJ3JkgmdhKkJLpBcRUSZo7Prq13BYS",
        "value": "0"
      }
    },
    "Flags": 0,
    "LPTokenBalance": {
      "currency": "033EE62589A944E08A96DC309D6ADBD2FBCFBD11",
      "issuer": "rKM4AJ3JkgmdhKkJLpBcRUSZo7Prq13BYS",
      "value": "100"
    },
    "LedgerEntryType": "AMM",
    "OwnerNode": "0",
    "PreviousTxnID": "C12736E829EBF9C16BB7C827D71B398232051D53A584CDFA6384AE13311BA399",
    "PreviousTxnLgrSeq": 7,
    "VoteSlots": [
      {
        "VoteEntry": {
          "Account": "r9QxhA9RghPZBbUchA9HkrmLKaWvkLXU29",
          "VoteWeight": 100000
        }
      }
    ],
    "index": "3B391EB8C901D850E698B80C13C98A937A8F9DF30F826D6CEB26F5616902EAF4"
  },
  "status": "success",
  "validated": false
}
```

## 15. RPC book_offers

### 15.1. Request Fields

We do not introduce new fields.

### 15.2 Response Fields

We do not introduce new fields.

### 15.3 Example Request

```json
{
  "command": "book_offers",
  "ledger_index": "current",
  "taker": "rG1QQv2nh2gr7RCZ1P8YYcBUKCCN633jCn",
  "taker_gets": {
    "mpt_issuance_id": "000000065C488AAC5813270850685FFD89F4A4A8F4CD4C83"
  },
  "taker_pays": {
    "mpt_issuance_id": "000000045C488AAC5813270850685FFD89F4A4A8F4CD4C83"
  }
}
```

### 15.4 Example Response

```json
{
  "result": {
    "ledger_current_index": 12,
    "offers": [
      {
        "Account": "rG1QQv2nh2gr7RCZ1P8YYcBUKCCN633jCn",
        "BookDirectory": "55795BD0628C360A24D3163A2A1EDD66AA9F715E94E9C1D954232CE5E5C6B16D",
        "BookNode": "0",
        "Flags": 0,
        "LedgerEntryType": "Offer",
        "OwnerNode": "0",
        "PreviousTxnID": "1177EC0BC778D39306481F6D2E33C267DB783800A58EE2F90C91AE38F1B023AD",
        "PreviousTxnLgrSeq": 11,
        "Sequence": 6,
        "TakerGets": {
          "mpt_issuance_id": "000000065C488AAC5813270850685FFD89F4A4A8F4CD4C83",
          "value": "101"
        },
        "TakerPays": {
          "mpt_issuance_id": "000000045C488AAC5813270850685FFD89F4A4A8F4CD4C83",
          "value": "100"
        },
        "index": "F4715C7C5957FE81246F259315494C671AF12C8B180BB32398DE5148B82ADD93",
        "owner_funds": "1000",
        "quality": "0.9900990099009901"
      }
    ],
    "status": "success",
    "validated": false
  }
}
```

## 16. Security

While Multipurpose Tokens (MPT) inherit the core security model of the XRPL (including issuer-controlled freezes and authorization), this integration acknowledges the architectural shift from RippleState to MPT objects. Security is maintained by performing real-time verification of MPT-specific flags and ensuring that DEX quality calculations account for MPT-specific decimal scaling to prevent rounding exploits. Furthermore, the DEX engine treats MPT-specific freezes as immediate execution barriers, mirroring the existing IOU freeze behavior.

# Appendix

## A: `STIssue` serialization

`STIssue` type is extended to support MPT as follows:

- Break down `mpt_issuance_id` into its sequence number and account.
- The account is serialized in the first 160 bits, followed by a dedicated black hole account in the next 160 bits.
- Finally, the sequence number (32 bits) is serialized last.
- Deserialization method reads 320-bit `currency` and `account`. If `account` is the black hole account then additional 32 bits have to be read and deserialized into a sequence number.
- This method maintains backward compatibility, doesn’t require a separate amendment, but adds 32 extra bits compared to the current format, or adds 160 bits compared to 192 bits required for serializing `mpt_issuance_id`.

| 160 bits MPT issuer account | 160 bits black-hole account | 32 bits sequence |
| --------------------------- | --------------------------- | ---------------- |
