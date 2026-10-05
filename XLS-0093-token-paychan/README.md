<pre>
  xls: 93
  title: Token-Enabled Payment Channels
  description: Enhancement to existing Payment Channel functionality to support both Trustline-based tokens (IOUs) and Multi-Purpose Tokens (MPTs)
  implementation: https://github.com/XRPLF/rippled/pull/7935; https://github.com/XRPLF/rippled/pull/7936
  author: Denis Angell (@dangell7)
  proposal-from: https://github.com/XRPLF/XRPL-Standards/discussions/287
  status: Draft
  category: Amendment
  requires: XLS-33, XLS-39, XLS-85
  created: 2025-05-24
  updated: 2026-10-05
</pre>

# Token-Enabled Payment Channels

> This proposal, XLS-93, extends payment channels to tokens in the same way [XLS-85](../XLS-0085-token-escrow/README.md) extends escrows, and reuses the issuer opt-in flags and locked-amount accounting introduced there. It builds on [XLS-33](../XLS-0033-multi-purpose-tokens/README.md) for MPTs and on [XLS-39](../XLS-0039-clawback/README.md) for the clawback opt-in.

## 1. Abstract

The proposed `TokenPaychan` amendment to the XRP Ledger (XRPL) protocol enhances the existing `PayChannel` functionality by enabling support for both Trustline-based tokens (IOUs) and Multi-Purpose Tokens (MPTs). This amendment introduces changes to ledger objects, transactions, and transaction processing logic to allow payment channels to use IOU tokens and MPTs, while respecting issuer controls and maintaining ledger integrity. It also adds one new transaction, `PaymentChannelClawback`, so that an issuer whose holders can already be clawed back retains that reach over value locked in a channel.

## 2. Motivation

Payment channels accept XRP only. XLS-85 extended escrows to IOUs and MPTs, so an issuer who has opted in to token locking there still cannot have that token used in a channel, and off-ledger settlement of a token has no on-ledger lock to settle against. Locking a token also moves it out of reach of the ordinary `Clawback` transaction, which is bounded by the holder's spendable balance, so an issuer that relies on clawback would lose that control the moment a holder opened a channel.

## 3. Specification

This amendment extends the functionality of payment channels to support both IOUs and MPTs, accounting for the specific behaviors and constraints associated with each token type. Token-denominated channels share their locking model with Token-Enabled Escrows (XLS-85): the same `lsfAllowTrustLineLocking` and `lsfMPTCanEscrow` issuer opt-in flags, and the same `sfLockedAmount` accounting fields.

## 3.1. Overview of Token Types

### 3.1.1. IOU Tokens

- **Trustlines**: IOUs rely on trustlines between accounts.
- **Issuer Controls**:
  - **Require Authorization (`lsfRequireAuth`)**: Issuers may require accounts to be authorized to hold their tokens.
  - **Freeze Conditions (global, individual, and deep freeze)**: Issuers can freeze tokens, affecting their transferability.
- **Transfer Mechanics**: Transfers occur via adjustments to trustline balances.
- **Transfer Rates**: Issuers can set a `TransferRate` that affects transfers involving their tokens.

### 3.1.2. Multi-Purpose Tokens (MPTs)

- **No Trustlines**: MPTs do not utilize trustlines.
- **Issuer Controls**:
  - **Transfer Flags (`lsfMPTCanTransfer`)**: Tokens must have this flag enabled to be transferable and to participate in transactions like payment channels, unless the destination address of the Payment Channel is the issuer of the MPT.
  - **Require Authorization (`lsfMPTRequireAuth`)**: Issuers may require authorization for accounts to hold their tokens.
  - **Lock Conditions (`lsfMPTLocked`)**: Tokens can be locked by the issuer, affecting their transferability.
- **Transfer Mechanics**: Transfers occur by moving token balances directly between accounts.
- **Transfer Fees**: Issuers can set a `TransferFee` (analogous to `TransferRate` for IOUs) that affects transfers involving their tokens.

## 3.2. Ledger Entry: `PayChannel`

The `PayChannel` ledger object is updated as follows: `Amount` and `Balance` may hold a token, and the optional `TransferRate` and `IssuerNode` fields are added. Unchanged fields are included below so that the example is self-contained.

### 3.2.1. Fields

| Field Name          | Constant | Required | Internal Type | Default Value | Description                                                                                                                                                                 |
| ------------------- | -------- | -------- | ------------- | ------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `LedgerEntryType`   | Yes      | Yes      | UINT16        | `0x0078`      | Identifies this as a `PayChannel` object.                                                                                                                                   |
| `Account`           | Yes      | Yes      | ACCOUNT       | N/A           | The source address that owns this payment channel.                                                                                                                          |
| `Destination`       | Yes      | Yes      | ACCOUNT       | N/A           | The destination address for this payment channel. While the channel is open, this address is the only one that can receive funds from the channel.                          |
| `Sequence`          | Yes      | No       | UINT32        | N/A           | The sequence number or ticket of the transaction that created the channel.                                                                                                  |
| `Amount`            | No       | Yes      | AMOUNT        | N/A           | The total amount allocated to the payment channel. Can represent XRP, an IOU token, or an MPT. Must always be a positive value.                                             |
| `Balance`           | No       | Yes      | AMOUNT        | N/A           | The amount already paid out from the channel. Same asset type as `Amount`.                                                                                                  |
| `PublicKey`         | Yes      | Yes      | BLOB          | N/A           | Public key of the key pair that can be used to sign claims against this channel.                                                                                            |
| `SettleDelay`       | Yes      | Yes      | UINT32        | N/A           | Number of seconds the source address must wait to close the channel if it still has funds in it.                                                                            |
| `Expiration`        | No       | No       | UINT32        | N/A           | The mutable expiration time for this payment channel, in seconds since the Ripple Epoch.                                                                                    |
| `CancelAfter`       | Yes      | No       | UINT32        | N/A           | The immutable expiration time for this payment channel, in seconds since the Ripple Epoch.                                                                                  |
| `SourceTag`         | Yes      | No       | UINT32        | N/A           | An arbitrary tag to further specify the source for this payment channel.                                                                                                    |
| `DestinationTag`    | Yes      | No       | UINT32        | N/A           | An arbitrary tag to further specify the destination for this payment channel.                                                                                               |
| `TransferRate`      | Yes      | No       | UINT32        | N/A           | The transfer rate or fee at creation, used as an upper bound on the rate applied during claims. Only present when the rate at creation differs from parity.                 |
| `OwnerNode`         | No       | Yes      | UINT64        | N/A           | A hint indicating which page of the source address's owner directory links to this entry.                                                                                   |
| `DestinationNode`   | No       | No       | UINT64        | N/A           | A hint indicating which page of the destination's owner directory links to this entry.                                                                                      |
| `IssuerNode`        | No       | No       | UINT64        | N/A           | The ledger index of the issuer's directory node associated with the `PayChannel`. Only present for IOU channels where the issuer is neither the source nor the destination. |
| `PreviousTxnID`     | No       | Yes      | HASH256       | N/A           | The identifying hash of the transaction that most recently modified this entry.                                                                                             |
| `PreviousTxnLgrSeq` | No       | Yes      | UINT32        | N/A           | The index of the ledger that contains the transaction that most recently modified this entry.                                                                               |

### 3.2.2. Invariants

- `<PayChannel>'.Balance` and `<PayChannel>'.Amount` are the same asset, and that asset is the asset of `<PayChannel>.Amount`: the asset of a channel never changes after creation.
- `0 <= <PayChannel>'.Balance <= <PayChannel>'.Amount`.
- `<PayChannel>.Balance <= <PayChannel>'.Balance`: the paid-out balance only increases.
- `TransferRate` is present only if `Amount` is not XRP, and `<PayChannel>'.TransferRate == <PayChannel>.TransferRate`: it is set at creation and never updated.
- `IssuerNode` is present only if `Amount` is an IOU whose issuer is neither `Account` nor `Destination`.

### 3.2.3. Example JSON

```json
{
  "LedgerEntryType": "PayChannel",
  "Flags": 0,
  "Account": "rf1BiGeXwwQoi8Z2ueFYTEXSwuJYfV2Jpn",
  "Destination": "ra5nK24KXen9AHvsdFTKHSANinZseWnPcX",
  "Sequence": 12,
  "Amount": {
    "currency": "USD",
    "issuer": "rHb9CJAWyB4rj91VRWn96DkukG4bwdtyTh",
    "value": "1000"
  },
  "Balance": {
    "currency": "USD",
    "issuer": "rHb9CJAWyB4rj91VRWn96DkukG4bwdtyTh",
    "value": "250"
  },
  "PublicKey": "032D2B4A9D4B0C1C7D5E0B6E5F9A8C7B6D5E4F3A2B1C0D9E8F7A6B5C4D3E2F1A0B",
  "SettleDelay": 3600,
  "TransferRate": 1005000000,
  "OwnerNode": "0000000000000000",
  "DestinationNode": "0000000000000000",
  "IssuerNode": "0000000000000000",
  "PreviousTxnID": "F0AB71E777B2DA54B86231E19B82554EF1F8211F92ECA473121C655BFC5329BF",
  "PreviousTxnLgrSeq": 14661788
}
```

## 3.3. Reused XLS-85 Fields and Flags

### 3.3.1. `MPToken` and `MPTokenIssuance` Ledger Objects

Token-denominated payment channels reuse the `sfLockedAmount` field introduced by [XLS-85](../XLS-0085-token-escrow/README.md) on both the `MPToken` and `MPTokenIssuance` ledger objects:

| Object            | Field Name       | JSON Type | Internal Type | Description                                                                                                                                          |
| ----------------- | ---------------- | --------- | ------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------- |
| `MPToken`         | `sfLockedAmount` | String    | UInt64        | _(Optional)_ The total this holder has locked for this issuance: its outstanding escrows plus the unclaimed remainder of its payment channels.       |
| `MPTokenIssuance` | `sfLockedAmount` | String    | UInt64        | _(Optional)_ The total locked across all holders of this issuance: their outstanding escrows plus the unclaimed remainder of their payment channels. |

### 3.3.2. `AccountRoot` Ledger Object

No new flags are introduced. Token-denominated payment channels reuse the `lsfAllowTrustLineLocking` flag (`0x40000000`) introduced by [XLS-85](../XLS-0085-token-escrow/README.md): issuers who have enabled trust line locking for escrows have also enabled it for payment channels. See XLS-85 Section 1.6 for the corresponding `asfAllowTrustLineLocking` AccountSet flag.

## 3.4. Transaction: `PaymentChannelCreate`

The `PaymentChannelCreate` transaction is modified as follows:

### 3.4.1. Fields

| Field    | Required? | JSON Type        | Internal Type | Default Value | Description                                                                                                                                                                                                                                                                                                                                                                                |
| -------- | --------- | ---------------- | ------------- | ------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `Amount` | Yes       | Object or String | Amount        | N/A           | The amount to fund the payment channel. Can represent [XRP, in drops](https://xrpl.org/docs/references/protocol/data-types/basic-data-types#specifying-currency-amounts), an [IOU](https://xrpl.org/docs/concepts/tokens/fungible-tokens#fungible-tokens) token, or an [MPT](https://xrpl.org/docs/concepts/tokens/fungible-tokens/multi-purpose-tokens). Must always be a positive value. |

### 3.4.2. Failure Conditions

#### 3.4.2.1. Data Verification

1. `Amount` is a token and the `TokenPaychan` amendment is not enabled. (`temBAD_AMOUNT`)
2. `Amount` is an IOU that is not positive. (`temBAD_AMOUNT`)
3. `Amount` is an IOU whose currency code is XRP. (`temBAD_CURRENCY`)
4. `Amount` is an MPT and the `MPTokensV1` amendment is not enabled. (`temDISABLED`)
5. `Amount` is an MPT that is not positive or exceeds the maximum MPT amount. (`temBAD_AMOUNT`)

#### 3.4.2.2. Protocol-Level Failures

- **Issuer is the Source:**
  - If the source account is the issuer of the token, the transaction fails with `tecNO_PERMISSION`.

- **Issuer Does Not Allow Token Locking or Transfer:**
  - **IOU Tokens**: If the issuer's account does not have the `lsfAllowTrustLineLocking` flag set, the transaction fails with `tecNO_PERMISSION`. If the issuer's account does not exist, the transaction fails with `tecNO_ISSUER`.
  - **MPTs**:
    - If the `MPTokenIssuance` of the token being used does not exist, the transaction fails with `tecOBJECT_NOT_FOUND`.
    - If the `MPTokenIssuance` of the token being used lacks the `lsfMPTCanEscrow` flag, the transaction fails with `tecNO_PERMISSION`.
    - If the `MPTokenIssuance` of the token being used lacks the `lsfMPTCanTransfer` flag, the transaction fails with `tecNO_AUTH` unless the destination address of the Payment Channel is the issuer of the MPT.

- **Source or Destination Not Authorized to Hold Token:**
  - If the issuer requires authorization and either the source or the destination is not authorized, the transaction fails with `tecNO_AUTH`.
  - The issuer is always authorized for its own token, so a destination that is the issuer never fails this check.

- **Source Account's Token Holding Issues:**
  - **IOU Tokens**: If the source lacks a trustline with the issuer, the transaction fails with `tecNO_LINE`.
  - **MPTs**: If the source does not hold the MPT, the transaction fails with `tecOBJECT_NOT_FOUND`.

- **Source or Destination is Frozen or Token is Locked:**
  - **IOU Tokens**: If the token is frozen (global/individual/deepfreeze) for the source or the destination, the transaction fails with `tecFROZEN`.
  - **MPTs**: If the token is locked for the source or the destination, the transaction fails with `tecLOCKED`.
  - Note: this is deliberately stricter than base freeze semantics, under which an individual freeze only prevents the frozen holder from sending. Opening a lock is blocked by any freeze on either party, while paying out to the destination at claim time only requires that the destination is not deep frozen (see Normal Claim). This matches the lock creation rules of [XLS-85](../XLS-0085-token-escrow/README.md).
  - The destination MAY be the issuer of the token; claims on such a channel redeem tokens back to the issuer. Because the freeze check above applies to the destination unconditionally, no channel can be created while the issuer has a global freeze in effect, including a channel whose destination is the issuer. This is intentionally stricter than direct payments, which always permit redemption to the issuer.

- **Insufficient Spendable Balance:**
  - If the source account lacks sufficient spendable balance, the transaction fails with `tecINSUFFICIENT_FUNDS`.

### 3.4.3. State Changes

- **Adjustment from Source to Issuer:**
  - **IOU Tokens**: The channel `Amount` is deducted from the source's trustline balance.
  - **MPTs**: The channel `Amount` is deducted from the source's MPT balance. The `sfOutstandingAmount` of the MPT issuance remains unchanged. The `sfLockedAmount` is increased on both the source's MPT and the MPT issuance.
- **Payment Channel Object Creation:**
  - The `PayChannel` ledger object includes:
    - `Amount`: Tokens held in the channel.
    - `Balance`: Amount already paid out (starts at zero).
    - `TransferRate`: `TransferRate` (IOUs) or `TransferFee` (MPTs) at creation. Only stored when it differs from parity (no fee).
    - `IssuerNode`: Reference to the issuer's ledger node. Only present for IOU channels where the issuer is neither the source nor the destination.

### 3.4.4. Example JSON

```json
{
  "TransactionType": "PaymentChannelCreate",
  "Account": "rf1BiGeXwwQoi8Z2ueFYTEXSwuJYfV2Jpn",
  "Destination": "ra5nK24KXen9AHvsdFTKHSANinZseWnPcX",
  "Amount": {
    "currency": "USD",
    "issuer": "rHb9CJAWyB4rj91VRWn96DkukG4bwdtyTh",
    "value": "1000"
  },
  "SettleDelay": 3600,
  "PublicKey": "032D2B4A9D4B0C1C7D5E0B6E5F9A8C7B6D5E4F3A2B1C0D9E8F7A6B5C4D3E2F1A0B",
  "Fee": "10",
  "Sequence": 12
}
```

## 3.5. Transaction: `PaymentChannelFund`

The `PaymentChannelFund` transaction is modified to support token amounts.

### 3.5.1. Fields

| Field    | Required? | JSON Type        | Internal Type | Default Value | Description                                                                                              |
| -------- | --------- | ---------------- | ------------- | ------------- | -------------------------------------------------------------------------------------------------------- |
| `Amount` | Yes       | Object or String | Amount        | N/A           | The amount to add to the channel. Must be the same asset as the channel's `Amount` and a positive value. |

### 3.5.2. Failure Conditions

#### 3.5.2.1. Data Verification

1. `Amount` is a token and the `TokenPaychan` amendment is not enabled. (`temBAD_AMOUNT`)
2. `Amount` is an IOU that is not positive. (`temBAD_AMOUNT`)
3. `Amount` is an IOU whose currency code is XRP. (`temBAD_CURRENCY`)
4. `Amount` is an MPT and the `MPTokensV1` amendment is not enabled. (`temDISABLED`)
5. `Amount` is an MPT that is not positive or exceeds the maximum MPT amount. (`temBAD_AMOUNT`)

#### 3.5.2.2. Protocol-Level Failures

- **Asset Mismatch:**
  - If the funding `Amount` is not the same asset as the channel's `Amount`, the transaction fails with `tecWRONG_ASSET`.

- **Same conditions as `PaymentChannelCreate`** for validating the funding amount and token permissions (issuer opt-in, authorization, freeze/lock, transferability, spendable balance).

- **Inexact Sum:**
  - The channel's new `Amount` must equal its old `Amount` plus the funding `Amount` exactly. An IOU sum is rounded to the mantissa width and is exact only if subtracting each operand from the sum gives back the other; an MPT sum is exact only if it does not overflow. Otherwise the transaction fails with `tecPRECISION_LOSS`.

### 3.5.3. State Changes

- **Adjustment from Source:**
  - **IOU Tokens**: The funding `Amount` is deducted from the source's trustline balance.
  - **MPTs**: The funding `Amount` is deducted from the source's MPT balance. The `sfLockedAmount` is increased accordingly.
- **Payment Channel Object Update:**
  - The channel's `Amount` field is increased by the funding amount. The stored `TransferRate` is not updated by funding.

### 3.5.4. Example JSON

```json
{
  "TransactionType": "PaymentChannelFund",
  "Account": "rf1BiGeXwwQoi8Z2ueFYTEXSwuJYfV2Jpn",
  "Channel": "C1AE6DDDEEC05CF2978C0BAD6FE302948E9533691DC749DCDD3B9E5992CA6198",
  "Amount": {
    "currency": "USD",
    "issuer": "rHb9CJAWyB4rj91VRWn96DkukG4bwdtyTh",
    "value": "500"
  },
  "Fee": "10",
  "Sequence": 13
}
```

## 3.6. Transaction: `PaymentChannelClaim`

### 3.6.1. Fields

| Field       | Required? | JSON Type        | Internal Type | Default Value | Description                                                                                                                                                          |
| ----------- | --------- | ---------------- | ------------- | ------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `Balance`   | No        | Object or String | Amount        | N/A           | The total amount delivered by this channel after processing this claim. Same asset as the channel's `Amount`.                                                        |
| `Amount`    | No        | Object or String | Amount        | N/A           | The amount authorized by the `Signature`. Same asset as the channel's `Amount`; must be at least `Balance`.                                                          |
| `Signature` | No        | String           | Blob          | N/A           | The signature of the authorization message in Claim Authorization, made with the key whose `PublicKey` is stored in the channel. Required unless the source submits. |
| `PublicKey` | No        | String           | Blob          | N/A           | The public key used for `Signature`; must match the channel's `PublicKey`. Required when `Signature` is present.                                                     |

#### 3.6.1.1. Claim Authorization

The `Signature` on a `PaymentChannelClaim` is over the following message, signed with the key whose `PublicKey` is stored in the channel. Fields are concatenated in order with no field headers or length prefixes; integers are big-endian.

1. The 4-byte prefix `0x434C4D00` (`HashPrefix::PaymentChannelClaim`).
2. The 32-byte channel ID.
3. The authorized amount. For an XRP channel, the drops as an unsigned 64-bit integer, unchanged from today. For a token channel, the amount serialized as an `Amount` field value without its field header, the same bytes the binary codec writes for the transaction `Amount` field after its field ID:
   - **IOU**: the 64-bit value word (a zero amount is `0x8000000000000000`; otherwise bit 63 is set, bit 62 is set for a positive amount, bits 54 to 61 hold the exponent plus 97, and bits 0 to 53 hold the mantissa), then the 20-byte currency code, then the 20-byte issuer `AccountID`.
   - **MPT**: one type byte (`0x60` for a positive amount: the MPT bit `0x20` and the positive bit `0x40`), then the value as an unsigned 64-bit integer, then the 24-byte `MPTokenIssuanceID`.

The message is 44 bytes for an XRP channel, 84 bytes for an IOU channel and 69 bytes for an MPT channel. The `MPTokenIssuanceID` already contains the issuer's `AccountID`, so nothing follows it.

### 3.6.2. Failure Conditions

#### 3.6.2.1. Data Verification

1. `Balance` or `Amount` is a token and the `TokenPaychan` amendment is not enabled. (`temBAD_AMOUNT`)
2. `Balance` or `Amount` is an MPT and the `MPTokensV1` amendment is not enabled. (`temDISABLED`)
3. `Balance` and `Amount` are both present and are not the same asset. (`temBAD_AMOUNT`)
4. `Signature` does not verify against the message in Claim Authorization for the authorized amount (`Amount`, or `Balance` when `Amount` is absent). (`temBAD_SIGNATURE`)

#### 3.6.2.2. Protocol-Level Failures

**Normal Claim (Balance Update)**, when claiming without closing the channel:

When the destination is the issuer of the channel's token, none of the authorization, holding, trustline limit or freeze conditions below apply: the issuer has no trustline to itself and holds no `MPToken`, and the claim redeems the tokens to the issuer (see State Changes).

- **Asset Mismatch:**
  - If the claim's `Balance` or `Amount` is not the same asset as the channel's `Amount`, the transaction fails with `tecWRONG_ASSET`.

- **Destination Not Authorized to Hold Token:**
  - If authorization is required and the destination is not authorized, the transaction fails with `tecNO_AUTH`.

- **Destination Lacks Trustline or MPT Holding:**
  - The destination's trustline or `MPToken` is created during the claim only when the destination itself submits the transaction (and authorization is not required). No other submitter can create a holding for the destination, since holding a token requires the holder's consent.
  - **IOU Tokens**: If the destination lacks a trustline with the issuer and did not submit the transaction, the transaction fails with `tecNO_LINE`.
  - **MPTs**: If the destination does not hold the MPT and did not submit the transaction, the transaction fails with `tecNO_PERMISSION`.

- **Cannot Create Trustline or MPT Holding:**
  - If unable to create due to lack of reserves, the transaction fails with `tecNO_LINE_INSUF_RESERVE` (IOU) or `tecINSUFFICIENT_RESERVE` (MPT).

- **Trustline Limit Exceeded (IOU only):**
  - If the transaction is not submitted by the destination and the claimed amount would push the destination's trustline balance above its limit, the transaction fails with `tecLIMIT_EXCEEDED`.

- **Destination Account is Frozen or Token is Locked:**
  - **IOU Tokens**:
    - **Deep Freeze**: If the token is deep frozen, the transaction fails with `tecFROZEN`.
    - **Global/Individual Freeze**: The transaction succeeds despite the token being globally or individually frozen.
  - **MPTs**:
    - **Lock Conditions (Equivalent to Deep Freeze)**: The transaction fails with `tecLOCKED`.

**Channel Closure**

A channel closes when a claim carries the `tfClose` flag (immediately if the requester is the destination or the channel is fully drained; otherwise an expiration is scheduled per `SettleDelay`), or when any claim is processed against an already-expired channel.

Closure returns the remaining channel funds (`Amount` minus `Balance`) to the source. **The failure conditions below apply only when this remainder is positive.** A fully drained channel has nothing to refund, so it closes without any source-side checks; the destination's ability to claim earned funds is never gated by the source's authorization, trustline, or freeze state.

**Failure Conditions (positive remainder only):**

- **Source Not Authorized to Hold Token:**
  - If authorization is required and the source is not authorized, the transaction fails with `tecNO_AUTH`.

- **Source Lacks Trustline or MPT Holding:**
  - The source's trustline or `MPToken` is created during closure only when the source itself submits the transaction (and authorization is not required), for the same reason as on a claim.
  - **IOU Tokens**: If the source lacks a trustline with the issuer and did not submit the transaction, the transaction fails with `tecNO_LINE`.
  - **MPTs**: If the source does not hold the MPT and did not submit the transaction, the transaction fails with `tecNO_PERMISSION`.

- **Cannot Create Trustline or MPT Holding:**
  - If unable to create due to lack of reserves, the transaction fails with `tecNO_LINE_INSUF_RESERVE` (IOU) or `tecINSUFFICIENT_RESERVE` (MPT).

- **Source Account is Frozen or Token is Locked:**
  - **IOU Tokens**:
    - **Deep Freeze**: The transaction succeeds, allowing the channel to be closed.
    - **Global/Individual Freeze**: The transaction succeeds, allowing the channel to be closed.
  - **MPTs**:
    - **Lock Conditions (Deep Freeze Equivalent)**: The transaction succeeds, allowing the channel to be closed.

### 3.6.3. State Changes

**Normal Claim (Balance Update)**

- **Auto create Trustline or MPToken:**
  - **IOU Tokens**: If the IOU does not require authorization and the account submitting the transaction is the destination, a trustline is created for it.
  - **MPTs**: If the MPT does not require authorization and the account submitting the transaction is the destination, an `MPToken` is created for it.
- **Adjustment from Issuer to Destination:**
  - **IOU Tokens**: The claimed amount, less any transfer fee (see Section 3.11), is added to the destination's trustline balance. If the destination is the issuer, the claimed amount is simply redeemed.
  - **MPTs**:
    - If the destination is the issuer of the asset held in the channel, then:
      1. The `LockedAmount` on the `MPTokenIssuance` and the source's `MPToken` is decreased by the claimed amount.
      2. No destination `MPToken` object is changed because MPT issuers may not hold MPTokens.
      3. The `OutstandingAmount` on the `MPTokenIssuance` is decreased by the claimed amount (i.e., this claim is a "redemption").
    - If the destination is not the issuer of the asset held in the channel, then:
      1. The `LockedAmount` on the `MPTokenIssuance` and the source's `MPToken` is decreased by the claimed amount.
      2. The `MPTAmount` on the destination's `MPToken` is increased by the claimed amount, less any transfer fee.
      3. The `OutstandingAmount` on the `MPTokenIssuance` is decreased by the transfer fee, the claimed amount less the amount credited to the destination; the fee is credited to no holder, so it leaves the outstanding supply.
- **Channel Balance Update:**
  - The channel's `Balance` field is updated to reflect the total amount claimed.

**Channel Closure**

- **Auto create Trustline or MPToken:**
  - **IOU Tokens**: If the IOU does not require authorization and the account submitting the transaction is the source, a trustline is created for it.
  - **MPTs**: If the MPT does not require authorization and the account submitting the transaction is the source, an `MPToken` is created for it.
- **Adjustment from Issuer to Source:**
  - No transfer fee is applied when returning remaining funds to the source.
  - **IOU Tokens**: Any remaining channel funds are added to the source's trustline balance.
  - **MPTs**: Any remaining channel funds are added to the source's MPT balance. The `sfOutstandingAmount` of the MPT issuance remains unchanged. The `sfLockedAmount` is decreased on both the source's MPT and the MPT issuance.
- **Deletion of Payment Channel Object:**
  - The `PayChannel` object is deleted after successful closure.

### 3.6.4. Example JSON

```json
{
  "TransactionType": "PaymentChannelClaim",
  "Account": "ra5nK24KXen9AHvsdFTKHSANinZseWnPcX",
  "Channel": "C1AE6DDDEEC05CF2978C0BAD6FE302948E9533691DC749DCDD3B9E5992CA6198",
  "Balance": {
    "currency": "USD",
    "issuer": "rHb9CJAWyB4rj91VRWn96DkukG4bwdtyTh",
    "value": "400"
  },
  "Amount": {
    "currency": "USD",
    "issuer": "rHb9CJAWyB4rj91VRWn96DkukG4bwdtyTh",
    "value": "400"
  },
  "Signature": "30440220718D264EF05CAED7C781FF6DE298DCAC68D002562C9BF3A07C1E721B420C0DAB02203A5A4779EF4D2CCC7BC3EF886676D803A9981B928D3B8ACA483B80ECA3CD7B9B",
  "PublicKey": "032D2B4A9D4B0C1C7D5E0B6E5F9A8C7B6D5E4F3A2B1C0D9E8F7A6B5C4D3E2F1A0B",
  "Fee": "10",
  "Sequence": 7
}
```

## 3.7. Transaction: `PaymentChannelClawback`

Locking a token into a channel moves it out of reach of the ordinary `Clawback` transaction (for an MPT, `Clawback` with the `MPTokenHolder` field defined in [XLS-33](../XLS-0033-multi-purpose-tokens/README.md)), which is bounded by the holder's spendable balance and so cannot see locked value. `PaymentChannelClawback` gives the issuer that reach back. It requires the same opt-in the issuer already needed to claw back an ordinary holding, so it grants no new authority over a token; it removes a place the token could be kept out of reach.

Only the unclaimed remainder of the channel (`Amount` minus `Balance`) can be clawed. The destination's earned `Balance` is never touched, so a clawback cannot reverse value the payee has already claimed.

### 3.7.1. Fields

| Field             | Required? | JSON Type        | Internal Type | Default Value | Description                                                                                                                                                                   |
| ----------------- | --------- | ---------------- | ------------- | ------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `TransactionType` | Yes       | String           | UInt16        | N/A           | The transaction type, `PaymentChannelClawback` (`ttPAYCHAN_CLAWBACK`, value `94`).                                                                                            |
| `Channel`         | Yes       | String           | Hash256       | N/A           | The ID of the `PayChannel` to claw from.                                                                                                                                      |
| `Amount`          | No        | Object or String | Amount        | N/A           | The amount to claw back. Must be a positive, non-XRP amount of the channel's asset. If omitted, or if it is at least the unclaimed remainder, the entire remainder is clawed. |

The transaction is not delegable under [XLS-75](../XLS-0075-permission-delegation/README.md): it is registered as `Delegation::NotDelegable`, so a delegate cannot submit it on the issuer's behalf, in line with XLS-75 Section 8 for new transaction types.

### 3.7.2. Transaction Fee

**Fee Structure:** Standard

This transaction uses the standard transaction fee (currently 10 drops, subject to Fee Voting changes).

### 3.7.3. Failure Conditions

#### 3.7.3.1. Data Verification

- **Malformed `Amount`:**
  - If `Amount` is present and is XRP or is not positive, the transaction fails with `temBAD_AMOUNT`. An MPT amount above the maximum MPT value fails the same way.
  - If `Amount` is present and names XRP as an IOU currency code, the transaction fails with `temBAD_CURRENCY`.

#### 3.7.3.2. Protocol-Level Failures

- **Channel Does Not Exist:**
  - If no `PayChannel` object matches `Channel`, the transaction fails with `tecNO_TARGET`.

- **Channel Holds XRP:**
  - XRP cannot be clawed back, so a channel denominated in XRP fails with `tecNO_PERMISSION`.

- **Submitter Is Not the Issuer:**
  - If the submitting account is not the issuer of the channel's asset, the transaction fails with `tecNO_PERMISSION`.

- **Asset Mismatch:**
  - If `Amount` is present and is not the same asset as the channel's `Amount`, the transaction fails with `tecWRONG_ASSET`.

- **Inexact Difference (partial clawback only):**
  - For a partial clawback the channel's new `Amount` must equal its old `Amount` minus the clawed `Amount` exactly. If the IOU subtraction rounds, so that the stored decrease differs from the amount clawed (including a decrease rounded away entirely), the transaction fails with `tecPRECISION_LOSS`. A full clawback is not subject to this check: it sets `Amount` equal to `Balance` directly and claws the exact remainder (see State Changes).

- **Issuer Does Not Allow Clawback:**
  - **IOU Tokens**: If the issuer's account lacks the `lsfAllowTrustLineClawback` flag, or has the `lsfNoFreeze` flag set, the transaction fails with `tecNO_PERMISSION`. These are the same conditions that gate the [XLS-39](../XLS-0039-clawback/README.md) `Clawback` transaction.
  - **MPTs**: If the `MPTokenIssuance` lacks the `lsfMPTCanClawback` flag, the transaction fails with `tecNO_PERMISSION`. If the `MPTokenIssuance` does not exist, the transaction fails with `tecOBJECT_NOT_FOUND`.

### 3.7.4. State Changes

- **Nothing to Claw:**
  - If the channel's `Balance` already equals its `Amount`, there is no remainder and the transaction succeeds without changing the channel. A claim that draws the channel down to its full `Amount` without `tfClose` leaves the channel open in exactly this state.

- **Adjustment to the Issuer:**
  - No transfer fee is applied. A clawback is a redemption rather than a transfer between holders.
  - **IOU Tokens**: No trustline is modified. The locked value was already removed from the source's trustline balance when the channel was created or funded, so retiring the channel's obligation is the whole of the clawback.
  - **MPTs**: The clawed amount is deducted from the `sfLockedAmount` on both the source's `MPToken` and the `MPTokenIssuance`, and from the `sfOutstandingAmount` on the `MPTokenIssuance`. No `MPToken` is created for the issuer, since MPT issuers do not hold their own `MPToken`.

- **Payment Channel Object Update:**
  - For a partial clawback, the channel's `Amount` is reduced by the clawed amount and the channel remains open.
  - For a full clawback, the channel's `Amount` is set equal to its `Balance`, leaving no remainder, and the channel is closed and deleted as described in Channel Closure. Because the remainder is zero, no refund is made to the source and no source-side authorization, holding, or freeze condition applies.

**Effect on Outstanding Claims:**

A clawback lowers the channel's `Amount`, which is the ceiling on what the destination can claim. Any authorization the source has already signed for a balance above the new `Amount` becomes unusable, and a claim presenting it fails with `tecUNFUNDED_PAYMENT`; the destination needs a fresh signature from the source for a balance at or below the new `Amount`. This is a consequence of the issuer's authority over the token rather than of the channel mechanics, and it mirrors what an ordinary clawback does to a holder's pending obligations.

An expired channel can still be clawed. Expiry entitles the source to a refund but does not perform one until some account submits a transaction against the channel, so an issuer clawback and the source's refund race for the remainder.

### 3.7.5. Example JSON

```json
{
  "TransactionType": "PaymentChannelClawback",
  "Account": "rHb9CJAWyB4rj91VRWn96DkukG4bwdtyTh",
  "Channel": "C1AE6DDDEEC05CF2978C0BAD6FE302948E9533691DC749DCDD3B9E5992CA6198",
  "Amount": {
    "currency": "USD",
    "issuer": "rHb9CJAWyB4rj91VRWn96DkukG4bwdtyTh",
    "value": "100"
  },
  "Fee": "10",
  "Sequence": 31
}
```

## 3.8. RPC: `channel_authorize`

The `channel_authorize` and `channel_verify` RPC methods take the authorized amount in `amount`. For an XRP channel it is a string of drops. For a token channel it is the same JSON object used for a transaction `Amount` (`currency`, `issuer` and `value` for an IOU; `mpt_issuance_id` and `value` for an MPT), and the server builds the message in Claim Authorization from it.

### 3.8.1. Request Fields

| Field Name   | Required? | JSON Type        | Description                                                                                                           |
| ------------ | --------- | ---------------- | --------------------------------------------------------------------------------------------------------------------- |
| `command`    | Yes       | string           | Must be `"channel_authorize"`                                                                                         |
| `channel_id` | Yes       | string           | The 256-bit channel ID, in hexadecimal.                                                                               |
| `amount`     | Yes       | string or object | The authorized amount: a string of drops for an XRP channel, or an `Amount` object for a token channel.               |
| `secret`     | No        | string           | The secret key of the channel's `PublicKey`. Exactly one of `secret`, `seed`, `seed_hex` or `passphrase` is required. |
| `key_type`   | No        | string           | The signing algorithm of the key, `secp256k1` or `ed25519`.                                                           |

### 3.8.2. Response Fields

| Field Name  | Always Present? | JSON Type | Description                                                       |
| ----------- | --------------- | --------- | ----------------------------------------------------------------- |
| `status`    | Yes             | string    | `"success"` if the request succeeded                              |
| `signature` | Yes             | string    | The signature of the Claim Authorization message, in hexadecimal. |

### 3.8.3. Failure Conditions

1. Signing is not supported by this server. (`notSupported`)
2. `channel_id` or `amount` is missing, or no signing key field is present. (`invalidParams`)
3. `channel_id` is not a 256-bit hexadecimal string. (`channelMalformed`)
4. `amount` is neither a string of drops nor an `Amount` object for a token amount that is not negative. (`channelAmtMalformed`)

### 3.8.4. Example Request

```json
{
  "command": "channel_authorize",
  "channel_id": "C1AE6DDDEEC05CF2978C0BAD6FE302948E9533691DC749DCDD3B9E5992CA6198",
  "amount": {
    "currency": "USD",
    "issuer": "rHb9CJAWyB4rj91VRWn96DkukG4bwdtyTh",
    "value": "400"
  },
  "seed": "snoPBrXtMeMyMHUVTgbuqAfg1SUTb",
  "key_type": "secp256k1"
}
```

### 3.8.5. Example Response

```json
{
  "status": "success",
  "signature": "30440220718D264EF05CAED7C781FF6DE298DCAC68D002562C9BF3A07C1E721B420C0DAB02203A5A4779EF4D2CCC7BC3EF886676D803A9981B928D3B8ACA483B80ECA3CD7B9B"
}
```

## 3.9. RPC: `channel_verify`

### 3.9.1. Request Fields

| Field Name   | Required? | JSON Type        | Description                                                         |
| ------------ | --------- | ---------------- | ------------------------------------------------------------------- |
| `command`    | Yes       | string           | Must be `"channel_verify"`                                          |
| `channel_id` | Yes       | string           | The 256-bit channel ID, in hexadecimal.                             |
| `amount`     | Yes       | string or object | The authorized amount, in the same form as for `channel_authorize`. |
| `public_key` | Yes       | string           | The channel's `PublicKey`, in hexadecimal or base58.                |
| `signature`  | Yes       | string           | The signature to verify, in hexadecimal.                            |

### 3.9.2. Response Fields

| Field Name           | Always Present? | JSON Type | Description                                                                                            |
| -------------------- | --------------- | --------- | ------------------------------------------------------------------------------------------------------ |
| `status`             | Yes             | string    | `"success"` if the request succeeded                                                                   |
| `signature_verified` | Yes             | boolean   | Whether `signature` is valid for the Claim Authorization message built from `channel_id` and `amount`. |

### 3.9.3. Failure Conditions

1. `public_key`, `channel_id`, `amount` or `signature` is missing, or `signature` is not a non-empty hexadecimal string. (`invalidParams`)
2. `public_key` is not a valid public key. (`publicMalformed`)
3. `channel_id` is not a 256-bit hexadecimal string. (`channelMalformed`)
4. `amount` is neither a string of drops nor an `Amount` object for a token amount that is not negative. (`channelAmtMalformed`)

### 3.9.4. Example Request

```json
{
  "command": "channel_verify",
  "channel_id": "C1AE6DDDEEC05CF2978C0BAD6FE302948E9533691DC749DCDD3B9E5992CA6198",
  "amount": {
    "currency": "USD",
    "issuer": "rHb9CJAWyB4rj91VRWn96DkukG4bwdtyTh",
    "value": "400"
  },
  "public_key": "032D2B4A9D4B0C1C7D5E0B6E5F9A8C7B6D5E4F3A2B1C0D9E8F7A6B5C4D3E2F1A0B",
  "signature": "30440220718D264EF05CAED7C781FF6DE298DCAC68D002562C9BF3A07C1E721B420C0DAB02203A5A4779EF4D2CCC7BC3EF886676D803A9981B928D3B8ACA483B80ECA3CD7B9B"
}
```

### 3.9.5. Example Response

```json
{
  "status": "success",
  "signature_verified": true
}
```

## 3.10. Key Differences Between IOU and MPT Payment Channels

| Aspect                        | IOU Tokens                                                                                                                                                                  | Multi-Purpose Tokens (MPTs)                                                                                                                                                  |
| ----------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Trustlines**                | Required between accounts and issuer                                                                                                                                        | Not used                                                                                                                                                                     |
| **Issuer Flag for Channels**  | `lsfAllowTrustLineLocking` (account flag)                                                                                                                                   | `lsfMPTCanEscrow` (issuance flag)                                                                                                                                            |
| **Transfer Flags**            | N/A                                                                                                                                                                         | `lsfMPTCanTransfer` must be enabled for payment channels unless the destination is the issuer                                                                                |
| **Require Auth**              | Applicable (`lsfRequireAuth`); accounts must be authorized prior to holding tokens                                                                                          | Applicable (`lsfMPTRequireAuth`); accounts must be authorized prior to holding tokens                                                                                        |
| **Destination Authorization** | Required at creation and at claim unless the destination is the issuer; cannot be granted during claim if authorization required                                            | Required at creation and at claim unless the destination is the issuer; cannot be granted during claim if authorization required                                             |
| **Freeze/Lock Conditions**    | Any freeze blocks create/fund; **Deep Freeze** prevents claims, but allows closure; Global/Individual Freeze allows claims and closure                                      | Lock blocks create/fund; **Lock Conditions (Deep Freeze Equivalent)** prevent claims, but allow closure                                                                      |
| **Transfer Rates/Fees**       | `TransferRate` stored at creation and applied during claims                                                                                                                 | `TransferFee` stored at creation and applied during claims                                                                                                                   |
| **Clawback Opt-In**           | `lsfAllowTrustLineClawback` (account flag), and `lsfNoFreeze` must not be set                                                                                               | `lsfMPTCanClawback` (issuance flag)                                                                                                                                          |
| **Clawback Accounting**       | Channel `Amount` is reduced; no trustline changes                                                                                                                           | `sfLockedAmount` and `sfOutstandingAmount` are reduced                                                                                                                       |
| **Outstanding Amount**        | N/A                                                                                                                                                                         | Unchanged by create, fund and closure refund; decreased by the transfer fee on a claim, by the claimed amount on a claim to the issuer, and by the clawed amount on clawback |
| **Account Deletion**          | Payment channels prevent account deletion                                                                                                                                   | Payment channels prevent account deletion                                                                                                                                    |
| **Holding Deletion**          | Trustline deletion is NOT blocked by open channels (locked value lives in the channel object); closure refund then fails with `tecNO_LINE` until the line is re-established | `MPToken` deletion is blocked while `sfLockedAmount` is non-zero (`tecHAS_OBLIGATIONS`)                                                                                      |

## 3.11. Transfer Rates and Fees

### 3.11.1. IOU Tokens (`TransferRate`)

- **Rate Capped at Creation**: The `TransferRate` is captured at the time of `PaymentChannelCreate` and stored in the `PayChannel` object. At claim time, the lower of the stored rate and the issuer's current rate is applied: an increase by the issuer does not affect existing channels, while a decrease passes through to claims. This is identical to the behavior of the activated XLS-85 (Token Escrow) implementation, which uses the same shared unlock logic.
- **Fee Calculation**: The transfer fee is deducted from the claimed amount, reducing the final amount credited to the destination. No fee is applied when the issuer is the destination, or when remaining funds are returned to the source at closure.

### 3.11.2. MPTs (`TransferFee`)

- **Fee Capped at Creation**: The `TransferFee` is captured at the time of `PaymentChannelCreate` and stored in the `PayChannel` object, similar to IOUs, with the same lower-of-stored-and-current rule.
- **Fee Calculation**: The transfer fee is deducted from the claimed amount, reducing the final amount credited to the destination.
- **Consistent Fee Application**: Both IOUs and MPTs use the same capped-rate rule, ensuring the destination's settlement value cannot be worsened by the issuer after channel creation.

## 3.12. Future Considerations

1. Issuer as Source: XLS-93 currently does not allow the issuer to be the source of the Payment Channel. If your use case requires this functionality, you should create a new account, send the MPT or IOU to that account, and then create the payment channel with that account as the source.

2. Trustline Deletion While Locked: because the locked IOU value lives in the `PayChannel` object rather than on the trustline, an empty trustline can be deleted while channels remain open (see Section 8). Per-trustline lock accounting that would prevent this, for both escrows and payment channels, is deliberately left to a separate future amendment so that XLS-93 stays behaviorally aligned with the activated XLS-85.

## 4. Rationale

Payment channels are the last remaining XRP-only locking primitive; XLS-85 already extended escrows to IOUs and MPTs. Reusing the XLS-85 model wholesale, the same issuer opt-in flags (`lsfAllowTrustLineLocking`, `lsfMPTCanEscrow`), the same `sfLockedAmount` accounting, and the same shared lock/unlock logic in the implementation, means issuers make one opt-in decision that covers both primitives, and both primitives fail and succeed under identical token conditions. Every place where XLS-93 is stricter than base token semantics (any freeze blocks lock creation, no channel creation during global freeze even to the issuer) is inherited from the activated XLS-85 behavior rather than newly invented, keeping the two locking primitives coherent.

`PaymentChannelClawback` is included in the same amendment for the same reason. An issuer's clawback opt-in is a property of the token, so it should hold wherever that token sits. Deferring the transaction would have meant shipping a lock that quietly suspends an issuer control the token already carries, and the alternative of closing the channel first is not open to the issuer, which is not a party to the channel and cannot close it.

## 5. Backwards Compatibility

The change is amendment-gated. Before `TokenPaychan` is enabled, a token `Amount` on `PaymentChannelCreate` or `PaymentChannelFund`, and a token `Balance` or `Amount` on `PaymentChannelClaim`, are rejected with `temBAD_AMOUNT`, and `PaymentChannelClawback` is rejected with `temDISABLED`.

XRP channels are unchanged: the Claim Authorization message for an XRP channel keeps its 44-byte layout, existing `PayChannel` entries gain no fields (`TransferRate` and `IssuerNode` are only ever set on token channels), and `channel_authorize` and `channel_verify` continue to accept `amount` as a string of drops.

## 6. Test Plan

The reference implementation adds the `PayChanToken` test suite (`src/test/app/PayChanToken_test.cpp`), which covers, for IOUs and MPTs separately: amendment enablement, the issuer opt-in flags, preflight, preclaim and apply of `PaymentChannelCreate`, `PaymentChannelFund` and `PaymentChannelClaim`, closure, auto-creation of the destination's holding, balances and metadata, the locked transfer rate, require-auth, freeze and lock, trustline limits, precision loss, the interaction with ordinary `Clawback`, `PaymentChannelClawback` for both asset types, the `channel_authorize` and `channel_verify` methods, and the byte layout of the Claim Authorization message.

## 7. Reference Implementation

[XRPLF/rippled#7935](https://github.com/XRPLF/rippled/pull/7935) (token-denominated channels) and [XRPLF/rippled#7936](https://github.com/XRPLF/rippled/pull/7936) (`PaymentChannelClawback`).

## 8. Security Considerations

- **Payee protection.** The destination's earned funds are never gated by source-side state. Normal claims check only destination-side conditions, and the source-side conditions in Channel Closure apply only to refunding a positive remainder; a fully drained channel closes without them.
- **Issuer trust surface.** An issuer that uses `RequireAuth` can deauthorize the source and thereby block the refund leg of closure (`tecNO_AUTH`) until re-authorized. The channel and its locked funds remain on ledger; no funds are lost. This is the same issuer trust surface that exists for XLS-85 escrow refunds and for clawback generally.
- **Transfer rate.** The claim rate is capped at the rate stored at creation (the lower of stored and current is applied), so an issuer cannot retroactively tax funds already locked by raising `TransferRate`/`TransferFee`.
- **Trustline deletion.** The source can delete an empty trustline while a channel is open. Closure refunds then fail with `tecNO_LINE` until the source re-establishes the line; the destination's claims are unaffected. `MPToken` deletion is blocked while locked (`tecHAS_OBLIGATIONS`).
- **Signature domain.** Claim signatures bind the specific channel ID and amount, unchanged from XRP payment channels; the token layouts in Claim Authorization also bind the currency and issuer or the `MPTokenIssuanceID`, so a signature for one asset cannot be presented against a channel holding another.
- **Clawback scope.** `PaymentChannelClawback` reaches only the unclaimed remainder and only for an issuer who already holds the clawback opt-in for that token. It cannot reverse a claim the destination has settled, and it cannot touch XRP or a token whose issuer never enabled clawback.
- **Clawback and pending authorizations.** An issuer clawback can invalidate a signed claim authorization the destination is holding, because the authorized balance may exceed the reduced channel `Amount`. A destination that wants to settle ahead of this should claim rather than accumulate authorizations, the same tradeoff that applies to holding an unsettled balance with any clawback-enabled issuer.
