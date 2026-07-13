<pre>
  xls: 93
  title: Token-Enabled Payment Channels
  description: Enhancement to existing Payment Channel functionality to support both Trustline-based tokens (IOUs) and Multi-Purpose Tokens (MPTs)
  author: Denis Angell (@dangell7)
  proposal-from: https://github.com/XRPLF/XRPL-Standards/discussions/287
  status: Draft
  category: Amendment
  requires: [XLS-33](../XLS-0033-multi-purpose-tokens/README.md), [XLS-85](../XLS-0085-token-escrow/README.md)
  created: 2025-05-24
</pre>

> This proposal, XLS-93, extends payment channels to tokens in the same way [XLS-85](../XLS-0085-token-escrow/README.md) extends escrows, and reuses the issuer opt-in flags and locked-amount accounting introduced there.

The proposed `TokenPaychan` amendment to the XRP Ledger (XRPL) protocol enhances the existing `PaymentChannel` functionality by enabling support for both Trustline-based tokens (IOUs) and Multi-Purpose Tokens (MPTs). This amendment introduces changes to ledger objects, transactions, and transaction processing logic to allow payment channels to use IOU tokens and MPTs, while respecting issuer controls and maintaining ledger integrity.

# 1. Implementation

This amendment extends the functionality of payment channels to support both IOUs and MPTs, accounting for the specific behaviors and constraints associated with each token type. Token-denominated channels share their locking model — the `lsfAllowTrustLineLocking` / `lsfMPTCanEscrow` issuer opt-in flags and the `sfLockedAmount` accounting fields — with Token-Enabled Escrows (XLS-85).

## 1.1. Overview of Token Types

### 1.1.1. IOU Tokens

- **Trustlines**: IOUs rely on trustlines between accounts.
- **Issuer Controls**:
  - **Require Authorization (`lsfRequireAuth`)**: Issuers may require accounts to be authorized to hold their tokens.
  - **Freeze Conditions (global, individual, and deep freeze)**: Issuers can freeze tokens, affecting their transferability.
- **Transfer Mechanics**: Transfers occur via adjustments to trustline balances.
- **Transfer Rates**: Issuers can set a `TransferRate` that affects transfers involving their tokens.

### 1.1.2. Multi-Purpose Tokens (MPTs)

- **No Trustlines**: MPTs do not utilize trustlines.
- **Issuer Controls**:
  - **Transfer Flags (`lsfMPTCanTransfer`)**: Tokens must have this flag enabled to be transferable and to participate in transactions like payment channels.
  - **Require Authorization (`lsfMPTRequireAuth`)**: Issuers may require authorization for accounts to hold their tokens.
  - **Lock Conditions (`lsfMPTLocked`)**: Tokens can be locked by the issuer, affecting their transferability.
- **Transfer Mechanics**: Transfers occur by moving token balances directly between accounts.
- **Transfer Fees**: Issuers can set a `TransferFee` (analogous to `TransferRate` for IOUs) that affects transfers involving their tokens.

## 1.2. Payment Channel Transactions and Logic

### 1.2.1. `PaymentChannelCreate`

The `PaymentChannelCreate` transaction is modified as follows:

| Field    | Required? | JSON Type        | Internal Type | Description                                                                                                                                                                                                                                                                                                                                                                                |
| -------- | --------- | ---------------- | ------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `Amount` | Yes       | Object or String | Amount        | The amount to fund the payment channel. Can represent [XRP, in drops](https://xrpl.org/docs/references/protocol/data-types/basic-data-types#specifying-currency-amounts), an [IOU](https://xrpl.org/docs/concepts/tokens/fungible-tokens#fungible-tokens) token, or an [MPT](https://xrpl.org/docs/concepts/tokens/fungible-tokens/multi-purpose-tokens). Must always be a positive value. |

**Failure Conditions:**

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

- **Source Account's Token Holding Issues:**
  - **IOU Tokens**: If the source lacks a trustline with the issuer, the transaction fails with `tecNO_LINE`.
  - **MPTs**: If the source does not hold the MPT, the transaction fails with `tecOBJECT_NOT_FOUND`.

- **Source or Destination is Frozen or Token is Locked:**
  - **IOU Tokens**: If the token is frozen (global/individual/deepfreeze) for the source or the destination, the transaction fails with `tecFROZEN`.
  - **MPTs**: If the token is locked for the source or the destination, the transaction fails with `tecLOCKED`.

- **Insufficient Spendable Balance:**
  - If the source account lacks sufficient spendable balance, the transaction fails with `tecINSUFFICIENT_FUNDS`.

- **Precision Loss (IOU only):**
  - If the channel `Amount` cannot be represented without loss of precision, the transaction fails with `tecPRECISION_LOSS`.

**State Changes:**

- **Adjustment from Source to Issuer:**
  - **IOU Tokens**: The channel `Amount` is deducted from the source's trustline balance.
  - **MPTs**: The channel `Amount` is deducted from the source's MPT balance. The `sfOutstandingAmount` of the MPT issuance remains unchanged. The `sfLockedAmount` is increased on both the source's MPT and the MPT issuance.
- **Payment Channel Object Creation:**
  - The `PaymentChannel` ledger object includes:
    - `Amount`: Tokens held in the channel.
    - `Balance`: Amount already paid out (starts at zero).
    - `TransferRate`: `TransferRate` (IOUs) or `TransferFee` (MPTs) at creation. Only stored when it differs from parity (no fee).
    - `IssuerNode`: Reference to the issuer's ledger node. Only present for IOU channels where the issuer is neither the source nor the destination.

### 1.2.2. `PaymentChannelFund`

The `PaymentChannelFund` transaction is modified to support token amounts.

**Failure Conditions:**

- **Asset Mismatch:**
  - If the funding `Amount` is not the same asset as the channel's `Amount`, the transaction fails with `temBAD_AMOUNT`.

- **Same conditions as `PaymentChannelCreate`** for validating the funding amount and token permissions (issuer opt-in, authorization, freeze/lock, transferability, spendable balance).

- **Precision Loss (IOU only):**
  - If the funding `Amount` would be rounded away when added to the channel's `Amount`, the transaction fails with `tecPRECISION_LOSS`.

**State Changes:**

- **Adjustment from Source:**
  - **IOU Tokens**: The funding `Amount` is deducted from the source's trustline balance.
  - **MPTs**: The funding `Amount` is deducted from the source's MPT balance. The `sfLockedAmount` is increased accordingly.
- **Payment Channel Object Update:**
  - The channel's `Amount` field is increased by the funding amount. The stored `TransferRate` is not updated by funding.

### 1.2.3. `PaymentChannelClaim`

#### Normal Claim (Balance Update)

When claiming without closing the channel:

**Failure Conditions:**

- **Asset Mismatch:**
  - If the claim's `Balance` or `Amount` is not the same asset as the channel's `Amount`, the transaction fails with `temBAD_AMOUNT`.

- **Destination Not Authorized to Hold Token:**
  - If authorization is required and the destination is not authorized, the transaction fails with `tecNO_AUTH`.

- **Destination Lacks Trustline or MPT Holding:**
  - **IOU Tokens**: If the destination lacks a trustline with the issuer, the transaction fails with `tecNO_LINE`.
  - **MPTs**: If the destination does not hold the MPT, the transaction fails with `tecNO_PERMISSION`.
  - A new trustline or MPT holding may be created during `PaymentChannelClaim` if the destination submits the transaction and authorization is not required.

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

**State Changes:**

- **Auto create Trustline or MPToken:**
  - **IOU Tokens**: If the IOU does not require authorization and the account submitting the transaction is the recipient, then a trustline will be created.
  - **MPTs**: If the MPT does not require authorization and the account submitting the transaction is the recipient, then the MPT will be created.
- **Adjustment from Issuer to Destination:**
  - **IOU Tokens**: The claimed amount, less any transfer fee (see Section 1.4), is added to the destination's trustline balance. If the destination is the issuer, the claimed amount is simply redeemed.
  - **MPTs**:
    - If the destination is the issuer of the asset held in the channel, then:
      1. The `LockedAmount` on the `MPTokenIssuance` and the source's `MPToken` is decreased by the claimed amount.
      2. No destination `MPToken` object is changed because MPT issuers may not hold MPTokens.
      3. The `OutstandingAmount` on the `MPTokenIssuance` is decreased by the claimed amount (i.e., this claim is a "redemption").
    - If the destination is not the issuer of the asset held in the channel, then:
      1. The `LockedAmount` on the `MPTokenIssuance` and the source's `MPToken` is decreased by the claimed amount.
      2. The `Amount` on the destination's `MPToken` is increased by the claimed amount, less any transfer fee.
      3. The `OutstandingAmount` on the `MPTokenIssuance` is unchanged.
- **Channel Balance Update:**
  - The channel's `Balance` field is updated to reflect the total amount claimed.

#### Channel Closure

When closing the channel (either explicitly with the close flag, or automatically when fully drained or expired):

**Failure Conditions:**

- **Source Not Authorized to Hold Token:**
  - If authorization is required and the source is not authorized, the transaction fails with `tecNO_AUTH`.

- **Source Lacks Trustline or MPT Holding:**
  - **IOU Tokens**: If the source lacks a trustline with the issuer, the transaction fails with `tecNO_LINE`.
  - **MPTs**: If the source does not hold the MPT, the transaction fails with `tecNO_PERMISSION`.
  - A new trustline or MPT holding may be created during channel closure if the source submits the transaction and authorization is not required.

- **Cannot Create Trustline or MPT Holding:**
  - If unable to create due to lack of reserves, the transaction fails with `tecNO_LINE_INSUF_RESERVE` (IOU) or `tecINSUFFICIENT_RESERVE` (MPT).

- **Source Account is Frozen or Token is Locked:**
  - **IOU Tokens**:
    - **Deep Freeze**: The transaction succeeds, allowing the channel to be closed.
    - **Global/Individual Freeze**: The transaction succeeds, allowing the channel to be closed.
  - **MPTs**:
    - **Lock Conditions (Deep Freeze Equivalent)**: The transaction succeeds, allowing the channel to be closed.

**State Changes:**

- **Auto create Trustline or MPToken:**
  - **IOU Tokens**: If the IOU does not require authorization and the account submitting the transaction is the source, then a trustline will be created.
  - **MPTs**: If the MPT does not require authorization and the account submitting the transaction is the source, then the MPT will be created.
- **Adjustment from Issuer to Source:**
  - No transfer fee is applied when returning remaining funds to the source.
  - **IOU Tokens**: Any remaining channel funds are added to the source's trustline balance.
  - **MPTs**: Any remaining channel funds are added to the source's MPT balance. The `sfOutstandingAmount` of the MPT issuance remains unchanged. The `sfLockedAmount` is decreased on both the source's MPT and the MPT issuance.
- **Deletion of Payment Channel Object:**
  - The `PaymentChannel` object is deleted after successful closure.

## 1.3. Key Differences Between IOU and MPT Payment Channels

| Aspect                        | IOU Tokens                                                                                                                | Multi-Purpose Tokens (MPTs)                                                                                               |
| ----------------------------- | --------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------- |
| **Trustlines**                | Required between accounts and issuer                                                                                     | Not used                                                                                                                  |
| **Issuer Flag for Channels**  | `lsfAllowTrustLineLocking` (account flag)                                                                                 | `lsfMPTCanEscrow` (issuance flag)                                                                                         |
| **Transfer Flags**            | N/A                                                                                                                       | `lsfMPTCanTransfer` must be enabled for payment channels                                                                  |
| **Require Auth**              | Applicable (`lsfRequireAuth`); accounts must be authorized prior to holding tokens                                        | Applicable (`lsfMPTRequireAuth`); accounts must be authorized prior to holding tokens                                     |
| **Destination Authorization** | Required at creation and at claim; cannot be granted during claim if authorization required                               | Required at creation and at claim; cannot be granted during claim if authorization required                               |
| **Freeze/Lock Conditions**    | Any freeze blocks create/fund; **Deep Freeze** prevents claims, but allows closure; Global/Individual Freeze allows claims and closure | Lock blocks create/fund; **Lock Conditions (Deep Freeze Equivalent)** prevent claims, but allow closure |
| **Transfer Rates/Fees**       | `TransferRate` stored at creation and applied during claims                                                               | `TransferFee` stored at creation and applied during claims                                                                |
| **Outstanding Amount**        | Remains unchanged during channel operations                                                                               | Remains unchanged during channel operations                                                                               |
| **Account Deletion**          | Payment channels prevent account deletion                                                                                 | Payment channels prevent account deletion                                                                                 |

## 1.4. Transfer Rates and Fees

### 1.4.1. IOU Tokens (`TransferRate`)

- **Rate Capped at Creation**: The `TransferRate` is captured at the time of `PaymentChannelCreate` and stored in the `PaymentChannel` object. At claim time, the lower of the stored rate and the issuer's current rate is applied: an increase by the issuer does not affect existing channels, while a decrease passes through to claims.
- **Fee Calculation**: The transfer fee is deducted from the claimed amount, reducing the final amount credited to the destination. No fee is applied when the issuer is the destination, or when remaining funds are returned to the source at closure.

### 1.4.2. MPTs (`TransferFee`)

- **Fee Capped at Creation**: The `TransferFee` is captured at the time of `PaymentChannelCreate` and stored in the `PaymentChannel` object, similar to IOUs, with the same lower-of-stored-and-current rule.
- **Fee Calculation**: The transfer fee is deducted from the claimed amount, reducing the final amount credited to the destination.
- **Consistent Fee Application**: Both IOUs and MPTs use the same capped-rate rule, ensuring the destination's settlement value cannot be worsened by the issuer after channel creation.

## 1.5. Ledger Object Updates

### 1.5.1 `PaymentChannel` Ledger Object

The `PaymentChannel` ledger object is updated as follows:

| Field Name     | JSON Type        | Internal Type | Description                                                                                                                                                                                  |
| -------------- | ---------------- | ------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `Amount`       | Object or String | Amount        | The total amount allocated to the payment channel. Can represent XRP, an IOU token, or an MPT. Must always be a positive value.                                                              |
| `Balance`      | Object or String | Amount        | The amount already paid out from the channel. Same asset type as `Amount`.                                                                                                                   |
| `TransferRate` | Number           | UInt32        | _(Optional)_ The transfer rate or fee at creation, used as an upper bound on the rate applied during claims. Only present when the rate at creation differs from parity.                     |
| `IssuerNode`   | Number           | UInt64        | _(Optional)_ The ledger index of the issuer's directory node associated with the `PaymentChannel`. Only present for IOU channels where the issuer is neither the source nor the destination. |

### 1.5.2 `MPToken` and `MPTokenIssuance` Ledger Objects

Token-denominated payment channels reuse the `sfLockedAmount` field introduced by [XLS-85](../XLS-0085-token-escrow/README.md) on both the `MPToken` and `MPTokenIssuance` ledger objects:

| Field Name       | JSON Type | Internal Type | Description                                                                                |
| ---------------- | --------- | ------------- | -------------------------------------------------------------------------------------------- |
| `sfLockedAmount` | String    | UInt64        | _(Optional)_ The total of all outstanding escrows and payment channels for this issuance. |

### 1.5.3 `AccountRoot` Ledger Object

No new flags are introduced. Token-denominated payment channels reuse the `lsfAllowTrustLineLocking` flag (`0x40000000`) introduced by [XLS-85](../XLS-0085-token-escrow/README.md): issuers who have enabled trust line locking for escrows have also enabled it for payment channels. See XLS-85 Section 1.6 for the corresponding `asfAllowTrustLineLocking` AccountSet flag.

## 1.6. Future Considerations

1. Clawback: XLS-93 currently does not provide a direct "clawback" mechanism within an active Payment Channel. If your use case requires clawback, you can close the channel and then perform a clawback of the funds outside of the payment channel context. In other words, once the token amount returns to the source account, the existing clawback features for IOUs or MPTs can be used on those returned funds.

2. Issuer as Source: XLS-93 currently does not allow the issuer to be the source of the Payment Channel. If your use case requires this functionality, you should create a new account, send the MPT or IOU to that account, and then create the payment channel with that account as the source.
