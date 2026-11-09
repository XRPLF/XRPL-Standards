<pre>
  xls: 82
  title: MPT Integration into DEX
  description: Adds Multi-Purpose Token (MPT) support for XRPL DEX
  author: Gregory Tsipenyuk <gtsipenyuk@ripple.com>
  proposal-from: https://github.com/XRPLF/XRPL-Standards/discussions/231
  status: Draft
  category: Amendment
  requires: XLS-33, XLS-30
  created: 2024-09-19
  updated: 2026-08-31
</pre>

# MPT Integration into DEX

## Abstract

This proposal introduces a new amendment `MPTokensV2` as an extension to [XLS-33 Multi-Purpose Tokens](../XLS-0033-multi-purpose-tokens/README.md). The `MPTokensV2` amendment enables Multi-purpose token (MPT) support on the XRPL DEX, including offers, cross-currency payments, checks, and AMM.

## 1. Overview

The integration of Multi-Purpose Tokens (MPT) into the XRP Ledger Decentralized Exchange (DEX) focuses on extending the functional reach of existing trading mechanisms without introducing new on-ledger objects or modifying core state structures. By leveraging the existing ledger primitives, this update enables standard DEX transactions to natively support MPTs as a valid asset class. This specification outlines the necessary schema updates for transaction requests and provides comprehensive JSON examples to illustrate the interoperability between MPTs, XRP, and standard IOUs. Furthermore, this document details the expanded set of failure scenarios and transaction result codes specific to MPT trading, ensuring robust error handling for cross-asset liquidity paths and order-matching logic. For a comprehensive description of all transactions refer to [XRPL documentation](https://xrpl.org/docs/references/protocol/transactions)

Current transactions, which interact with XRPL DEX are:

- `AMMCreate`: Create a new Automated Market Maker (AMM) instance for trading a pair of assets (fungible tokens or XRP).
- `AMMDeposit`: Deposit funds into an AMM instance and receive the AMM's liquidity provider tokens (LP Tokens) in exchange.
- `AMMWithdraw`: Withdraw assets from an AMM instance by returning the AMM's liquidity provider tokens (LP Tokens).
- `AMMVote`: Vote on an AMM instance's trading fee. Identifies the pool by `Asset` / `Asset2`; does not move MPT.
- `AMMBid`: Bid on an AMM instance's auction slot using LP Tokens. Identifies the pool by `Asset` / `Asset2`; does not move MPT.
- `AMMClawback`: Enable token issuers to claw back tokens from wallets that have deposited into AMM pools.
- `AMMDelete`: Delete an empty AMM instance that could not be fully deleted automatically.
- `CheckCreate`: Create a Check object in the ledger, which is a deferred payment that can be cashed by its intended destination.
- `CheckCash`: Attempts to redeem a Check object in the ledger to receive up to the amount authorized by the corresponding CheckCreate transaction.
- `OfferCreate`: An OfferCreate transaction places an Offer in the decentralized exchange.
- `Payment`: A Payment transaction represents a transfer of value from one account to another.

MPT supports all of the above transactions. MPT can be combined with IOU and XRP tokens in the transactions. For instance, a Payment could be a cross-token payment from MPT token to IOU token; AMM can be created for XRP and MPT token-pair; an order book offer can be created to buy some MPT token and to sell another MPT token. MPT doesn't modify the transactions fields, flags, and functionality. However, the JSON of the MPT amount field differs from the JSON of the IOU amount field. Instead of `currency` and `issuer`, MPT is identified by `mpt_issuance_id`. MPT amount `value` is INT or UINT, which must be less than or equal to $2^{63} - 1$. Below are the examples of JSON MPT amount and JSON MPT asset:

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

Any transaction with MPT `Amount` or `Asset` have to use JSON format as described above. For any transaction, which uses MPT token, the token has to be created first by an issuer with `MPTokenIssuanceCreate` transaction and in most cases, except for `AMMWithdraw`, `AMMClawback`, `CheckCash`, and `OfferCreate`, the token has to be authorized by the holder account with `MPTokenAuthorize` transaction as described in [XLS-33](../XLS-0033-multi-purpose-tokens/README.md). `AMMCreate` is not in that list: the creator must already hold an `MPToken` unless they are the issuer. `MPTokenAuthorize` creates `MPToken` object, owned by a holder account. In addition, `MPTokenIssuanceCreate` must have the following flags set for DEX and AMM participation:

- `lsfMPTCanTrade`, in order for the MPT to be used in `OfferCreate`, cross-currency `Payment` book steps, `AMMCreate`, and `AMMDeposit`. This flag has no issuer exemption: if it is not set, those transactions fail with `tecNO_PERMISSION` even when the actor is the issuer.
- `lsfMPTCanTransfer`, in order for holders to transfer the MPT to other non-issuer accounts. `canTransfer` is waived when the sender or the receiver is the MPT issuer; otherwise a holder-to-holder transfer fails with `tecNO_AUTH`.

These flags can be enabled after issuance (see [XLS-94 Dynamic MPT](../XLS-0094-dynamic-MPT/README.md)) but cannot be cleared once enabled. `AMMWithdraw` and `AMMClawback` do not require either flag, so liquidity is not trapped if an issuer never enabled `lsfMPTCanTransfer`. `AMMVote` and `AMMBid` also do not check these flags; they require only that the account holds LP Tokens.

LP Tokens of an AMM whose pool includes an MPT inherit that MPT's transferability. A Payment of those LP Tokens between two non-issuers fails with `tecNO_AUTH` if the pool MPT lacks `lsfMPTCanTransfer`. Transfers that involve the MPT issuer succeed. An `OfferCreate` that sells such LP Tokens fails with `tecUNFUNDED_OFFER`. `AMMVote`, `AMMBid`, and `AMMWithdraw` still succeed for an account that already holds the LP Tokens.

## 2. Transaction: AMMCreate

Any token or both tokens in `AMMCreate` transaction can be MPT. I.e., in addition to the current combination of XRP/IOU and IOU/IOU token pair, `AMMCreate` can have XRP/MPT, IOU/MPT, and MPT/MPT token pair. Each MPT in the pair is identified by `mpt_issuance_id`. If both tokens are MPT then each token must have a unique `mpt_issuance_id`. In case of `AMMCreate` the token pair is identified by `Amount` and `Amount2`.

### 2.1. Fields

We do not introduce new fields.

### 2.2. Failure Conditions

We extend the `AMMCreate` with the following failure conditions, where `MPTokenIssuance` refers to the ledger object defining the specific MPT type identified in the transaction's `Amount` or `Amount2` fields; `MPToken` refers to the ledger object representing the specific MPT balance of the account executing the transaction (if that account is not the issuer); and flags refer to those set on the `MPTokenIssuance` object unless explicitly stated as being set on the individual `MPToken` object:

1. `Amount` or `Amount2` hold MPT and `MPTokensV2` amendment is not enabled, fail with `temDISABLED`.
2. `MPTokenIssuance` object doesn't exist, fail with `tecOBJECT_NOT_FOUND`.
3. `MPToken` object doesn't exist and AMM creator is not the issuer of MPT, fail with `tecNO_AUTH`.
4. `lsfMPTLocked` flag is set on `MPTokenIssuance`, fail for issuer and holder with `tecLOCKED`.
5. `lsfMPTLocked` flag is set on `MPToken`, fail for holder with `tecLOCKED`.
6. `lsfMPTRequireAuth` flag is set and AMM creator is not authorized, fail with `tecNO_AUTH`.
7. `lsfMPTCanTransfer` flag is not set and AMM creator is not the issuer of MPT, fail with `tecNO_AUTH`. The issuer may create the pool without `lsfMPTCanTransfer`.
8. `lsfMPTCanTrade` flag is not set, fail with `tecNO_PERMISSION`. There is no issuer exemption.
9. An MPT whose issuer is a pseudo-account (for example a vault share) is not a valid pool asset, fail with `tecWRONG_ASSET`.

### 2.3. State Changes

On success `AMMCreate` creates and authorizes an `MPToken` object for each MPT token for the AMM pseudo-account.

### 2.4. MPToken Ledger Object

`MPToken` object is created for each asset representing `MPToken` as follows:

| Field Name  | JSON Type | Internal Type | Description                                                                                                                        |
| ----------- | --------- | ------------- | ---------------------------------------------------------------------------------------------------------------------------------- |
| `Account`   | String    | ACCOUNTID     | _(Required)_ AMM Pseudo-account.                                                                                                   |
| `MPTAmount` | String    | UINT64        | _(Required)_ AMM pool amount.                                                                                                      |
| `Flags`     | String    | UINT32        | _(Required)_ `lsfMPTAMM` (0x00000004) and `lsfMPTAuthorized` (0x00000002). The AMM pseudo-account is always implicitly authorized. |

### 2.5. Example JSON

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

Lock, `lsfMPTCanTrade`, and `lsfMPTCanTransfer` checks apply to both pool assets even on a single-asset deposit. A missing `MPToken` is tolerated for a pool asset that is not being deposited (WeakAuth). The strong existence check applies only to assets named in `Amount`/`Amount2`, or to both pool balances under `tfLPToken`. A missing AMM instance fails with `terNO_AMM`.

1. `Asset`, `Asset2`, `Amount`, or `Amount2` hold MPT and `MPTokensV2` amendment is not enabled, fail with `temDISABLED`.
2. `MPTokenIssuance` object doesn't exist, fail with `tecOBJECT_NOT_FOUND`.
3. `MPToken` object doesn't exist and the account is not the issuer of MPT, fail with `tecNO_AUTH` if that MPT is named in `Amount` or `Amount2`, or if the deposit is `tfLPToken` (both pool balances). A single-asset deposit of the other pool asset does not require an `MPToken` for the non-deposited MPT side.
4. `lsfMPTLocked` flag is set on `MPTokenIssuance`, fail for issuer and holder with `tecLOCKED`.
5. `lsfMPTLocked` flag is set on `MPToken`, fail for holder with `tecLOCKED`.
6. `lsfMPTRequireAuth` flag is set and the account is not authorized, fail with `tecNO_AUTH`.
7. `lsfMPTCanTransfer` flag is not set and the account is not the issuer of MPT, fail with `tecNO_AUTH`.
8. `lsfMPTCanTrade` flag is not set, fail with `tecNO_PERMISSION`. There is no issuer exemption.

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

Authorization and lock checks apply only to assets the account actually receives. A single-asset withdraw of the non-MPT side does not require MPT authorization. `lsfMPTCanTrade` and `lsfMPTCanTransfer` are not enforced, so an existing LP can always exit.

1. `Asset`, `Asset2`, `Amount`, or `Amount2` hold MPT and `MPTokensV2` amendment is not enabled, fail with `temDISABLED`.
2. AMM instance doesn't exist, fail with `terNO_AMM`.
3. `lsfMPTLocked` flag is set on `MPTokenIssuance`, fail with `tecLOCKED` when withdrawing that MPT, unless the withdrawing account is the MPT issuer. An issuer who is an LP may withdraw its own globally-locked MPT. The other pool asset can still be withdrawn.
4. `lsfMPTLocked` flag is set on `MPToken`, fail with `tecLOCKED` when withdrawing that MPT. The other pool asset can still be withdrawn.
5. `lsfMPTRequireAuth` flag is set and the account is not authorized, fail with `tecNO_AUTH` when withdrawing that MPT. The other pool asset can still be withdrawn.

### 4.3. State Changes

On success `AMMWithdraw` creates an `MPToken` object if the Liquidity Provider doesn't own one for a withdrawn MPT. The created object is not auto-authorized; authorization remains the issuer's to grant (except the `AMMClawback` path in §8, which may set `lsfMPTAuthorized` on the clawback issuer's own asset).

### 4.4. MPToken Ledger Object

`MPToken` object is created as follows:

| Field Name  | JSON Type | Internal Type | Description                                                                                                               |
| ----------- | --------- | ------------- | ------------------------------------------------------------------------------------------------------------------------- |
| `Account`   | String    | ACCOUNTID     | _(Required)_ Liquidity Provider account.                                                                                  |
| `MPTAmount` | String    | UINT64        | _(Required)_ Withdrawn amount.                                                                                            |
| `Flags`     | String    | UINT32        | _(Required)_ 0, unless created during `AMMClawback` of the clawback issuer's own asset, in which case `lsfMPTAuthorized`. |

### 4.5. Example JSON

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

## 5. Transaction: AMMVote

`AMMVote` identifies the pool by `Asset` and `Asset2`. If either asset is MPT then `mpt_issuance_id` must be used. The transaction moves only LP Tokens' voting weight; it does not transfer MPT.

### 5.1. Fields

We do not introduce new fields.

### 5.2. Failure Conditions

1. `Asset` or `Asset2` hold MPT and `MPTokensV2` amendment is not enabled, fail with `temDISABLED`.
2. AMM instance doesn't exist, fail with `terNO_AMM`.
3. The account holds no LP Tokens, fail with `tecAMM_INVALID_TOKENS`.

`lsfMPTCanTrade`, `lsfMPTCanTransfer`, and MPT authorization / domain credentials are not checked.

### 5.3. State Changes

We do not introduce new state changes.

### 5.4. Example JSON

```json
{
  "Account": "rffMEZLzDQPNU6VYbWNkgQBtMz6gCYnMAG",
  "Asset": {
    "mpt_issuance_id": "00000002430427B80BD2D09D36B70B969E12801065F22308"
  },
  "Asset2": {
    "mpt_issuance_id": "00000003430427B80BD2D09D36B70B969E12801065F22308"
  },
  "Fee": "10",
  "Flags": 0,
  "TradingFee": "100",
  "TransactionType": "AMMVote"
}
```

## 6. Transaction: AMMBid

`AMMBid` identifies the pool by `Asset` and `Asset2`. If either asset is MPT then `mpt_issuance_id` must be used. The bid burns and, when refunding a previous slot owner, sends LP Tokens. It does not transfer MPT.

### 6.1. Fields

We do not introduce new fields.

### 6.2. Failure Conditions

1. `Asset` or `Asset2` hold MPT and `MPTokensV2` amendment is not enabled, fail with `temDISABLED`.
2. AMM instance doesn't exist, fail with `terNO_AMM`.
3. The account holds no LP Tokens, fail with `tecAMM_INVALID_TOKENS`.

`lsfMPTCanTrade`, `lsfMPTCanTransfer`, and MPT authorization / domain credentials are not checked. LP Token spendability used by Payment and `OfferCreate` (`canTransferLPToken`) is not applied to `AMMBid`.

### 6.3. State Changes

We do not introduce new state changes.

### 6.4. Example JSON

```json
{
  "Account": "rffMEZLzDQPNU6VYbWNkgQBtMz6gCYnMAG",
  "Asset": {
    "mpt_issuance_id": "00000002430427B80BD2D09D36B70B969E12801065F22308"
  },
  "Asset2": {
    "mpt_issuance_id": "00000003430427B80BD2D09D36B70B969E12801065F22308"
  },
  "Fee": "10",
  "Flags": 0,
  "TransactionType": "AMMBid"
}
```

## 7. Transaction: AMMDelete

`AMMDelete` is identified by `Asset` and `Asset2` with the token type corresponding to `Amount` and `Amount2` of `AMMCreate`. `Asset` and `Asset2` are `STIssue` type, which represents a token by `currency` and `issuer`. If `STIssue` type represents MPT then `mpt_issuance_id` must be used instead.

### 7.1. Fields

We do not introduce new fields.

### 7.2. Failure Conditions

We extend the `AMMDelete` transaction with the following failure conditions:

- `Asset` or `Asset2` hold MPT and `MPTokensV2` amendment is not enabled, fail with `temDISABLED`.

`lsfMPTCanTrade`, `lsfMPTCanTransfer`, and MPT authorization are not checked.

### 7.3. State Changes

We do not introduce new state changes.

### 7.4. Example JSON

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

## 8. Transaction: AMMClawback

`AMMClawback` is identified by `Asset` and `Asset2` with the token type corresponding to `Amount` and `Amount2` of `AMMCreate`. `Asset` and `Asset2` are `STIssue` type, which represents a token by `currency` and `issuer`. If `STIssue` type represents MPT then `mpt_issuance_id` must be used instead. `AMMClawback` has optional field `Amount`, which if present must match the type of `Asset`.

### 8.1. Fields

We do not introduce new fields.

### 8.2. Failure Conditions

We extend the `AMMClawback` transaction with the following failure conditions, where `MPTokenIssuance` refers to the ledger object defining the specific MPT type identified in the transaction's `Asset` or `Amount`:

1. `Asset`, `Asset2`, or `Amount` hold MPT and `MPTokensV2` amendment is not enabled, fail with `temDISABLED`.
2. AMM instance doesn't exist, fail with `terNO_AMM`.
3. `MPTokenIssuance` object doesn't exist, or `lsfMPTCanClawback` is not set, or `sfAccount` is not that issuance's issuer, fail with `tecNO_PERMISSION`.
4. `tfClawTwoAssets` is set and the paired asset is an MPT that the signer may not claw back, fail with `tecNO_PERMISSION`.

`lsfMPTCanTrade` and `lsfMPTCanTransfer` are not enforced. Authorization is ignored so the issuer can recover MPT from the pool even if the holder deleted or was unauthorized for their `MPToken`.

### 8.3. State Changes

On success `AMMClawback` creates an `MPToken` object if the Liquidity Provider doesn't own one for a received token. The recreated object is auto-authorized (`lsfMPTAuthorized`) only for the clawback issuer's own asset. A paired MPT issued by a different account is recreated unauthorized.

### 8.4. MPToken Ledger Object

`MPToken` object is created as follows:

| Field Name  | JSON Type | Internal Type | Description                                                                                |
| ----------- | --------- | ------------- | ------------------------------------------------------------------------------------------ |
| `Account`   | String    | ACCOUNTID     | _(Required)_ Liquidity Provider account.                                                   |
| `MPTAmount` | String    | UINT64        | _(Required)_ Clawbacked amount.                                                            |
| `Flags`     | String    | UINT32        | _(Required)_ `lsfMPTAuthorized` if the asset's issuer is the clawback signer; otherwise 0. |

### 8.5. Example JSON

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

## 9. Transaction: CheckCreate

If `SendMax` field is MPT then it is identified by `mpt_issuance_id`. Checks are not DEX transactions: `lsfMPTCanTrade` is not required.

### 9.1. Fields

We do not introduce new fields.

### 9.2. Failure Conditions

We extend the `CheckCreate` with the following failure conditions, where `MPTokenIssuance` refers to the ledger object defining the specific MPT type identified in the transaction's `SendMax`; and flags refer to those set on the `MPTokenIssuance` object unless explicitly stated as being set on the individual `MPToken` object:

1. `SendMax` holds MPT and `MPTokensV2` amendment is not enabled, fail with `temDISABLED`.
2. `MPTokenIssuance` object doesn't exist, fail with `tecOBJECT_NOT_FOUND`.
3. `lsfMPTLocked` flag is set on `MPTokenIssuance`, fail with `tecLOCKED` for issuer and holder. There is no issuer exemption: the issuer cannot create a check for a globally-locked MPT.
4. `lsfMPTLocked` flag is set on `MPToken`, fail for that holder as source or destination with `tecLOCKED`.
5. `lsfMPTCanTransfer` flag is not set and neither source nor destination is the issuer, fail with `tecNO_AUTH`.

### 9.3. State Changes

We do not introduce new state changes.

### 9.4. Example JSON

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

## 10. Transaction: CheckCash

If `Amount` or `DeliverMin` fields are MPT then they are identified by `mpt_issuance_id`. `mpt_issuance_id` of `DeliverMin` and `Amount` must match.

### 10.1. Fields

We do not introduce new fields.

### 10.2. Failure Conditions

We extend the `CheckCash` with the following failure conditions, where `MPTokenIssuance` refers to the ledger object defining the specific MPT type identified in the transaction's `Amount` or `DeliverMin` fields; and flags refer to those set on the `MPTokenIssuance` object unless explicitly stated as being set on the individual `MPToken` object. A missing Check object fails with `tecNO_ENTRY` (unchanged). When the destination is the MPT issuer, the destination-side MPT checks (items 2, 4, 5, and 6) are skipped; an issuer can always accept their own MPT.

1. `Amount` or `DeliverMin` hold MPT and `MPTokensV2` amendment is not enabled, fail with `temDISABLED`.
2. `MPTokenIssuance` object doesn't exist, fail with `tecOBJECT_NOT_FOUND` or `tecNO_ISSUER`.
3. Source has insufficient unfrozen/unlocked funds, fail with `tecPATH_PARTIAL`.
4. Destination `MPToken` is locked, fail with `tecLOCKED`.
5. `lsfMPTRequireAuth` flag is set and the destination is not authorized, fail with `tecNO_AUTH`. A missing destination `MPToken` is allowed (WeakAuth); it is created on success.
6. `lsfMPTCanTransfer` flag is not set and neither source nor destination is the issuer, fail with `tecNO_AUTH`.

### 10.3. State Changes

On success `CheckCash` creates an `MPToken` object if the destination doesn't own one. The created object is not auto-authorized.

### 10.4. MPToken Ledger Object

`MPToken` object is created as follows:

| Field Name  | JSON Type | Internal Type | Description                       |
| ----------- | --------- | ------------- | --------------------------------- |
| `Account`   | String    | ACCOUNTID     | _(Required)_ Destination account. |
| `MPTAmount` | String    | UINT64        | _(Required)_ Cashed amount.       |
| `Flags`     | String    | UINT32        | _(Required)_ 0.                   |

### 10.5. Example JSON

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

## 11. Transaction: OfferCreate

`OfferCreate` can have any token combination of `TakerGets` and `TakerPays`. I.e., in addition to the current combination of XRP/IOU and IOU/IOU tokens, `OfferCreate` can have XRP/MPT, IOU/MPT, and MPT/MPT tokens. If `TakerPays` or `TakerGets` fields are MPT then they are identified by `mpt_issuance_id`.

To ensure asset transfer consistency on offer crossing, the following logic is applied to the offer's assets transfer between the accounts.

`TakerGets` asset is transferred if:

- `lsfMPTCanTransfer` is set
- The offer's owner is the issuer
- The asset is the delivered asset and the destination account is the issuer

`TakerPays` is transferred if:

- `lsfMPTCanTransfer` is set
- The offer's owner is the issuer
- This book step is the first step of the strand (`TakerPays` is the strand's source asset)
- The previous step is also a book step (`TakerPays` is not the strand's source asset)

`TickSize` is an IOU `AccountRoot` setting. MPT and XRP issuers are not consulted. On an IOU/MPT offer, `TickSize` is applied only to the IOU amount when that amount is the inexact side (buy: `TakerGets`; sell/`tfSell`: `TakerPays`). If the inexact side is MPT, the submitted amounts and quality are left unchanged.

An MPT offer is removed from the book during crossing, not left as a skipped entry, when:

- Transfer-rate or crossing-limit arithmetic overflows (instead of failing the taker with `tecINTERNAL`)
- The offer owner fails authorization or MPT trade/transfer checks
- The offer is found unfunded, including a non-issuer offer whose `TakerGets` MPT is globally locked
- The offer's `TakerPays` MPT is locked for the owner — globally (issuance-level, so even the issuer's own offer is removed) or individually

### 11.1. Fields

We do not introduce new fields.

### 11.2. Failure Conditions

We extend the `OfferCreate` with the following failure conditions, where `MPTokenIssuance` refers to the ledger object defining the specific MPT type identified in the transaction's `TakerPays` or `TakerGets` fields; `MPToken` refers to the ledger object representing the specific MPT balance of the account executing the transaction (if that account is not the issuer); and flags refer to those set on the `MPTokenIssuance` object unless explicitly stated as being set on the individual `MPToken` object:

1. `TakerPays` or `TakerGets` hold MPT and `MPTokensV2` amendment is not enabled, fail with `temDISABLED`.
2. `MPTokenIssuance` object doesn't exist, fail with `tecOBJECT_NOT_FOUND` for `TakerPays` and `tecUNFUNDED_OFFER` for `TakerGets`.
3. `MPToken` object doesn't exist and the account is not the issuer of MPT, fail with `tecUNFUNDED_OFFER` for `TakerGets`.
4. `lsfMPTLocked` flag is set on `MPTokenIssuance`, fail for issuer and holder with `tecLOCKED`. New `OfferCreate` transactions are rejected even for the issuer. An issuer's pre-placed offer may still be crossed during payment execution only when the locked MPT is that offer's `TakerGets` (see §12). If the locked MPT is `TakerPays`, the issuer's offer is removed from the book.
5. `lsfMPTLocked` flag is set on `MPToken` and the account is not the issuer of MPT, fail with `tecUNFUNDED_OFFER` for `TakerGets`, fail with `tecLOCKED` for `TakerPays`.
6. `lsfMPTRequireAuth` flag is set and the account is not authorized, fail with `tecUNFUNDED_OFFER` for `TakerGets`, fail with `tecNO_AUTH` for `TakerPays`.
7. `lsfMPTCanTransfer` flag is not set and the account is not the issuer of MPT. `OfferCreate` succeeds but holder-owned book offers that cannot transfer the MPT are removed from the book rather than crossed. It still crosses offers owned by an issuer.
8. `lsfMPTCanTrade` flag is not set, fail with `tecNO_PERMISSION`.

### 11.3. State Changes

On success `OfferCreate` creates an `MPToken` object for the offer's owner account if the offer is consumed, the offer's owner is not the MPT issuer, and `MPToken` object doesn't exist for `TakerPays`'s `mpt_issuance_id`. Crossing also deletes book offers that fail authorization or MPT trade/transfer checks, that overflow, or that are found unfunded, including the lock cases above.

### 11.4. MPToken Ledger Object

`MPToken` object is created as follows:

| Field Name  | JSON Type | Internal Type | Description                         |
| ----------- | --------- | ------------- | ----------------------------------- |
| `Account`   | String    | ACCOUNTID     | _(Required)_ Offer's owner account. |
| `MPTAmount` | String    | UINT64        | _(Required)_ Buy amount.            |
| `Flags`     | String    | UINT32        | _(Required)_ 0.                     |

### 11.5. Example JSON

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

## 12. Transaction: Payment

`Payment` can have any cross-token payment combination. I.e., in addition to the current combination of XRP/IOU and IOU/IOU cross-token payment, `Payment` can have XRP/MPT, IOU/MPT, and MPT/MPT cross-token payment. MPT can be used to specify `Paths`, in which case `mpt_issuance_id` should be used instead of `currency` and `issuer` as shown in the `JSON` example below. MPT doesn't support payment rippling. `mpt_issuance_id` identifies a unique MPT. It's impossible to reference the same MPT with different issuer. If `Amount`, `DeliverMax`, `DeliverMin`, or `SendMax` fields are MPT then they are identified by `mpt_issuance_id`.

### 12.1. Fields

We do not introduce new fields.

### 12.2. Failure Conditions

We extend the `Payment` with the following failure conditions, where `MPTokenIssuance` refers to the ledger object defining the specific MPT type identified in the transaction's `Amount` or `SendMax` fields; `MPToken` refers to the ledger object representing the specific MPT balance of the account executing the transaction (if that account is not the issuer); and flags refer to those set on the `MPTokenIssuance` object unless explicitly stated as being set on the individual `MPToken` object:

1. `MPTokensV2` amendment is not enabled and the payment is not a direct same-asset MPT transfer (it specifies `Paths`, or `Amount` and `SendMax` are different assets and at least one is MPT), fail with `temMALFORMED`. A direct same-asset MPT payment is allowed under `MPTokensV1`.
2. `MPTokenIssuance` object doesn't exist, fail with `tecOBJECT_NOT_FOUND`.
3. `MPToken` object doesn't exist and the account is not the issuer of MPT, fail with `tecNO_AUTH`.
4. `lsfMPTLocked` flag is set on `MPTokenIssuance`. The outcome depends on where the locked asset appears in the payment path:
   - Source holder's asset is globally locked: path validation fails with `tecPATH_DRY`.
   - Deliver or book-step asset is globally locked: affected offers are removed from the book as unfunded at execution, resulting in `tecPATH_PARTIAL`.
   - Exception: if the source is the issuer of the globally-locked asset, the issuer's outgoing transfer is not subject to the global lock check, so the path is not rejected during validation; failure is detected at execution: `tecPATH_PARTIAL`.
   - An issuer's pre-placed offer is permitted to cross during payment execution when the globally-locked MPT is that offer's `TakerGets`. When the locked MPT is `TakerPays`, the issuer's offer is removed from the book (the global lock is issuance-level). Non-issuer offers for a globally-locked `TakerGets` are removed as unfunded.
5. `lsfMPTLocked` flag is set on `MPToken`. The outcome depends on which account's token is locked and their role in the payment:
   - Source's `MPToken` is individually locked: path validation fails with `tecPATH_DRY`.
   - Destination's `MPToken` is individually locked: path validation fails with `tecPATH_DRY`. Unlike `IOU`, where a frozen trust line still allows the destination to receive, an individually locked `MPToken` blocks receiving, so the path is rejected rather than succeeding.
   - A DEX offer owner's `MPToken` is individually locked on either side: the offer is removed from the book at execution (as unfunded on the `TakerGets` side; by the `TakerPays` lock check on the other), resulting in `tecPATH_PARTIAL`. Unlike `IOU`, where a frozen holder can still receive (causing the crossing to succeed), a locked `MPToken` prevents the offer owner from receiving the locked asset.
6. `lsfMPTRequireAuth` flag is set and the account is not authorized. Any transfer between unauthorized accounts fail with `tecNO_AUTH`.
7. `lsfMPTCanTransfer` flag is not set. A holder-to-holder transfer fails with `tecNO_AUTH` (direct MPT step) or `tecPATH_PARTIAL` (DEX book step). Holder-owned book offers that fail the transfer check are removed from the book. Transfers that involve the issuer succeed.
8. `lsfMPTCanTrade` is not set on a DEX book-step asset, fail with `tecNO_PERMISSION`. Direct issuer/holder MPT payments do not require `lsfMPTCanTrade`.

### 12.3. State Changes

Crossing a payment deletes book offers that fail authorization or MPT trade/transfer checks, that overflow, or that are found unfunded, including the lock cases in §12.2.

### 12.4. Example JSON

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

## 13. RPC: path_find

### 13.1. Request Fields

We do not introduce new fields.

`mpt_issuance_id` subfield replaces `currency` and `issuer` subfields in MPT amount fields.

### 13.2. Response Fields

We do not introduce new fields.

`mpt_issuance_id` subfield replaces `currency` and `issuer` subfields in MPT amount fields, and `currency` subfield in `paths_computed` field.

### 13.3. Example Request

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

### 13.4. Example Response

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

### 13.5. Failure Conditions

There is no new failure conditions.

## 14. RPC: ripple_path_find

### 14.1. Request Fields

We do not introduce new fields.

`mpt_issuance_id` subfield replaces `currency` and `issuer` subfields in MPT amount fields.

### 14.2. Response Fields

We do not introduce new fields.

`mpt_issuance_id` subfield replaces `currency` and `issuer` subfields in MPT amount fields, and `currency` subfield in `paths_computed` field.

### 14.3. Example Request

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

### 14.4. Example Response

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

### 14.5. Failure Conditions

There is no new failure conditions.

## 15. RPC: amm_info

### 15.1. Request Fields

We do not introduce new fields.

`mpt_issuance_id` subfield replaces `currency` and `issuer` subfields in asset fields.

### 15.2. Response Fields

We do not introduce new fields.

`mpt_issuance_id` subfield replaces `currency` and `issuer` subfields in MPT amount fields.

### 15.3. Example Request

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

### 15.4. Example Response

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

### 15.5. Failure Conditions

There is no new failure conditions.

## 16. RPC: book_offers

### 16.1. Request Fields

We do not introduce new fields.

`mpt_issuance_id` subfield replaces `currency` and `issuer` subfields in `taker_gets` and `taker_pays` fields.

### 16.2. Response Fields

We do not introduce new fields.

`mpt_issuance_id` subfield replaces `currency` and `issuer` subfields in `TakerGets` and `TakerPays` fields.

### 16.3. Example Request

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

### 16.4. Example Response

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

### 16.5. Failure Conditions

There is no new failure conditions.

## 17. Rationale

The primary motivation for integrating Multi-Purpose Tokens (MPTs) into the XRPL’s Decentralized Exchange (DEX) is to ensure that the ledger’s next-generation token standard is not siloed from its existing liquidity ecosystem. While MPTs were designed to offer a more compact, scalable, and compliant alternative to traditional Trust Line-based tokens (IOUs), their utility is fundamentally capped if they cannot interact with Automated Market Makers (AMMs) or order books. By enabling MPTs as native trading assets, the ledger provides institutional issuers with a high-performance "Version 2" fungible token that retains the XRPL's core value proposition: atomic, cross-currency settlement. Unlike other blockchains that rely on smart contract standards like ERC-20, where DEX integration requires a wrapper or a complex external contract audit, the XRPL MPT/DEX integration is embedded at the protocol level. This ensures that compliance features—such as individual locks, global freezes, and clawbacks—are automatically enforced during trading without adding the latency or security risks associated with application-layer logic.

A cornerstone of this design is the high degree of transparency and parity between MPT and traditional IOU interactions within the DEX. Rather than introducing a disparate trading engine, the specification extends existing transaction types—such as OfferCreate, AMMCreate, and Payment—to support MPTs natively. This decision was driven by the need for ease of integration; by mirroring the behavior of the "Version 1" token standard, developers can leverage familiar design patterns and existing codebases. For the end user, the experience is intended to be virtually indistinguishable: an MPT functions as a first-class trading asset that can be paired with XRP or any other issued currency. This "plug-and-play" compatibility ensures that the transition to MPTs does not require a steep learning curve for the community or a costly overhaul of the ecosystem’s middleware.

Furthermore, the design prioritizes a unified liquidity model where the ledger's pathfinding logic treats MPTs and IOUs as functionally equivalent nodes. While MPTs use a unique mpt_issuance_id for technical precision, the underlying economic logic—such as cross-currency payments and order book mechanics—remains consistent. This prevents a fragmented developer experience where two different "flavors" of trading would need to be maintained. By choosing to wrap the new functionality within the ledger’s battle-tested DEX primitives, the XLS provides a robust and secure migration path, allowing institutions to adopt the more efficient MPT standard without losing access to the global liquidity and mature tooling that the XRP Ledger has cultivated over the past decade.

## 18. Security

While Multipurpose Tokens (MPT) inherit the core security model of the XRPL (including issuer-controlled freezes and authorization), this integration acknowledges the architectural shift from RippleState to MPT objects. Security is maintained by performing real-time verification of MPT-specific flags and ensuring that DEX quality calculations account for MPT-specific decimal scaling to prevent rounding exploits. Furthermore, the DEX engine enforces MPT-specific locks at both path validation and execution time. MPT lock semantics are stricter than IOU freeze semantics in one key respect: an individually locked MPToken blocks both sending and receiving, whereas an IOU frozen trust line only prevents the frozen account from sending to third parties — the frozen holder can still receive.

An MPT offer that overflows during transfer-rate or crossing-limit arithmetic, that fails authorization or MPT trade/transfer checks, that is found unfunded (including a globally-locked `TakerGets` for a non-issuer), or whose `TakerPays` MPT is locked for the owner (globally or individually) is deleted from the book instead of remaining as a skipped entry. Overflow no longer aborts the crossing transaction with `tecINTERNAL`. An issuer's pre-placed offer for a globally-locked MPT is permitted to cross only when that MPT is `TakerGets`; when it is `TakerPays` the issuer's offer is removed. `TickSize` never changes an MPT amount; it is applied only to the IOU side of an IOU/MPT offer when that side is inexact.

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
