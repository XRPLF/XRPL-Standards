<pre>
  xls: 93
  title: Token-Enabled Payment Channels
  description: Enhancement to existing Payment Channel functionality to support both Trustline-based tokens (IOUs) and Multi-Purpose Tokens (MPTs)
  author: Denis Angell (@dangell7)
  proposal-from: https://github.com/XRPLF/XRPL-Standards/discussions/287
  status: Draft
  category: Amendment
  requires: [XLS-33](../XLS-0033-multi-purpose-tokens/README.md), [XLS-39](../XLS-0039-clawback/README.md), [XLS-85](../XLS-0085-token-escrow/README.md)
  created: 2025-05-24
</pre>

> This proposal, XLS-93, extends payment channels to tokens in the same way [XLS-85](../XLS-0085-token-escrow/README.md) extends escrows, and reuses the issuer opt-in flags and locked-amount accounting introduced there.

## Abstract

The proposed `TokenPaychan` amendment to the XRP Ledger (XRPL) protocol enhances the existing `PaymentChannel` functionality by enabling support for both Trustline-based tokens (IOUs) and Multi-Purpose Tokens (MPTs). This amendment introduces changes to ledger objects, transactions, and transaction processing logic to allow payment channels to use IOU tokens and MPTs, while respecting issuer controls and maintaining ledger integrity. It also adds one new transaction, `PaymentChannelClawback`, so that an issuer whose holders can already be clawed back retains that reach over value locked in a channel.

# 1. Implementation

This amendment extends the functionality of payment channels to support both IOUs and MPTs, accounting for the specific behaviors and constraints associated with each token type. Token-denominated channels share their locking model with Token-Enabled Escrows (XLS-85): the same `lsfAllowTrustLineLocking` and `lsfMPTCanEscrow` issuer opt-in flags, and the same `sfLockedAmount` accounting fields.

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
  - Note: this is deliberately stricter than base freeze semantics, under which an individual freeze only prevents the frozen holder from sending. Opening a lock is blocked by any freeze on either party, while paying out to the destination at claim time only requires that the destination is not deep frozen (see Normal Claim). This matches the lock creation rules of [XLS-85](../XLS-0085-token-escrow/README.md).
  - The destination MAY be the issuer of the token; claims on such a channel redeem tokens back to the issuer. Because the freeze check above applies to the destination unconditionally, no channel can be created while the issuer has a global freeze in effect, including a channel whose destination is the issuer. This is intentionally stricter than direct payments, which always permit redemption to the issuer.

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
  - If the funding `Amount` is not the same asset as the channel's `Amount`, the transaction fails with `tecWRONG_ASSET`.

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
  - If the claim's `Balance` or `Amount` is not the same asset as the channel's `Amount`, the transaction fails with `tecWRONG_ASSET`.

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

A channel closes when a claim carries the `tfClose` flag (immediately if the requester is the destination or the channel is fully drained; otherwise an expiration is scheduled per `SettleDelay`), or when any claim is processed against an already-expired channel.

Closure returns the remaining channel funds (`Amount` minus `Balance`) to the source. **The failure conditions below apply only when this remainder is positive.** A fully drained channel has nothing to refund, so it closes without any source-side checks; the destination's ability to claim earned funds is never gated by the source's authorization, trustline, or freeze state.

**Failure Conditions (positive remainder only):**

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

### 1.2.4. `PaymentChannelClawback`

Locking a token into a channel moves it out of reach of the ordinary `Clawback` and `MPTokenIssuance` clawback transactions, which are both bounded by the holder's spendable balance and so cannot see locked value. `PaymentChannelClawback` gives the issuer that reach back. It requires the same opt-in the issuer already needed to claw back an ordinary holding, so it grants no new authority over a token; it removes a place the token could be kept out of reach.

Only the unclaimed remainder of the channel (`Amount` minus `Balance`) can be clawed. The destination's earned `Balance` is never touched, so a clawback cannot reverse value the payee has already claimed.

| Field     | Required? | JSON Type        | Internal Type | Description                                                                                                                                                                   |
| --------- | --------- | ---------------- | ------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `Channel` | Yes       | String           | Hash256       | The ID of the `PaymentChannel` to claw from.                                                                                                                                  |
| `Amount`  | No        | Object or String | Amount        | The amount to claw back. Must be a positive, non-XRP amount of the channel's asset. If omitted, or if it is at least the unclaimed remainder, the entire remainder is clawed. |

**Failure Conditions:**

- **Malformed `Amount`:**
  - If `Amount` is present and is XRP or is not positive, the transaction fails with `temBAD_AMOUNT`. An MPT amount above the maximum MPT value fails the same way.
  - If `Amount` is present and names XRP as an IOU currency code, the transaction fails with `temBAD_CURRENCY`.

- **Channel Does Not Exist:**
  - If no `PaymentChannel` object matches `Channel`, the transaction fails with `tecNO_TARGET`.

- **Channel Holds XRP:**
  - XRP cannot be clawed back, so a channel denominated in XRP fails with `tecNO_PERMISSION`.

- **Submitter Is Not the Issuer:**
  - If the submitting account is not the issuer of the channel's asset, the transaction fails with `tecNO_PERMISSION`.

- **Asset Mismatch:**
  - If `Amount` is present and is not the same asset as the channel's `Amount`, the transaction fails with `tecWRONG_ASSET`.

- **Issuer Does Not Allow Clawback:**
  - **IOU Tokens**: If the issuer's account lacks the `lsfAllowTrustLineClawback` flag, or has the `lsfNoFreeze` flag set, the transaction fails with `tecNO_PERMISSION`. These are the same conditions that gate the [XLS-39](../XLS-0039-clawback/README.md) `Clawback` transaction.
  - **MPTs**: If the `MPTokenIssuance` lacks the `lsfMPTCanClawback` flag, the transaction fails with `tecNO_PERMISSION`. If the `MPTokenIssuance` does not exist, the transaction fails with `tecOBJECT_NOT_FOUND`.

**State Changes:**

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

## 1.3. Key Differences Between IOU and MPT Payment Channels

| Aspect                        | IOU Tokens                                                                                                                                                                  | Multi-Purpose Tokens (MPTs)                                                                             |
| ----------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------- |
| **Trustlines**                | Required between accounts and issuer                                                                                                                                        | Not used                                                                                                |
| **Issuer Flag for Channels**  | `lsfAllowTrustLineLocking` (account flag)                                                                                                                                   | `lsfMPTCanEscrow` (issuance flag)                                                                       |
| **Transfer Flags**            | N/A                                                                                                                                                                         | `lsfMPTCanTransfer` must be enabled for payment channels                                                |
| **Require Auth**              | Applicable (`lsfRequireAuth`); accounts must be authorized prior to holding tokens                                                                                          | Applicable (`lsfMPTRequireAuth`); accounts must be authorized prior to holding tokens                   |
| **Destination Authorization** | Required at creation and at claim; cannot be granted during claim if authorization required                                                                                 | Required at creation and at claim; cannot be granted during claim if authorization required             |
| **Freeze/Lock Conditions**    | Any freeze blocks create/fund; **Deep Freeze** prevents claims, but allows closure; Global/Individual Freeze allows claims and closure                                      | Lock blocks create/fund; **Lock Conditions (Deep Freeze Equivalent)** prevent claims, but allow closure |
| **Transfer Rates/Fees**       | `TransferRate` stored at creation and applied during claims                                                                                                                 | `TransferFee` stored at creation and applied during claims                                              |
| **Clawback Opt-In**           | `lsfAllowTrustLineClawback` (account flag), and `lsfNoFreeze` must not be set                                                                                               | `lsfMPTCanClawback` (issuance flag)                                                                     |
| **Clawback Accounting**       | Channel `Amount` is reduced; no trustline changes                                                                                                                           | `sfLockedAmount` and `sfOutstandingAmount` are reduced                                                  |
| **Outstanding Amount**        | Remains unchanged during channel operations                                                                                                                                 | Remains unchanged during channel operations                                                             |
| **Account Deletion**          | Payment channels prevent account deletion                                                                                                                                   | Payment channels prevent account deletion                                                               |
| **Holding Deletion**          | Trustline deletion is NOT blocked by open channels (locked value lives in the channel object); closure refund then fails with `tecNO_LINE` until the line is re-established | `MPToken` deletion is blocked while `sfLockedAmount` is non-zero (`tecHAS_OBLIGATIONS`)                 |

## 1.4. Transfer Rates and Fees

### 1.4.1. IOU Tokens (`TransferRate`)

- **Rate Capped at Creation**: The `TransferRate` is captured at the time of `PaymentChannelCreate` and stored in the `PaymentChannel` object. At claim time, the lower of the stored rate and the issuer's current rate is applied: an increase by the issuer does not affect existing channels, while a decrease passes through to claims. This is identical to the behavior of the activated XLS-85 (Token Escrow) implementation, which uses the same shared unlock logic.
- **Fee Calculation**: The transfer fee is deducted from the claimed amount, reducing the final amount credited to the destination. No fee is applied when the issuer is the destination, or when remaining funds are returned to the source at closure.

### 1.4.2. MPTs (`TransferFee`)

- **Fee Capped at Creation**: The `TransferFee` is captured at the time of `PaymentChannelCreate` and stored in the `PaymentChannel` object, similar to IOUs, with the same lower-of-stored-and-current rule.
- **Fee Calculation**: The transfer fee is deducted from the claimed amount, reducing the final amount credited to the destination.
- **Consistent Fee Application**: Both IOUs and MPTs use the same capped-rate rule, ensuring the destination's settlement value cannot be worsened by the issuer after channel creation.

## 1.5. Ledger Object Updates

### 1.5.1 `PaymentChannel` Ledger Object

The `PaymentChannel` ledger object is updated as follows:

| Field Name     | JSON Type        | Internal Type | Description                                                                                                                                                                                  |
| -------------- | ---------------- | ------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `Amount`       | Object or String | Amount        | The total amount allocated to the payment channel. Can represent XRP, an IOU token, or an MPT. Must always be a positive value.                                                              |
| `Balance`      | Object or String | Amount        | The amount already paid out from the channel. Same asset type as `Amount`.                                                                                                                   |
| `TransferRate` | Number           | UInt32        | _(Optional)_ The transfer rate or fee at creation, used as an upper bound on the rate applied during claims. Only present when the rate at creation differs from parity.                     |
| `IssuerNode`   | Number           | UInt64        | _(Optional)_ The ledger index of the issuer's directory node associated with the `PaymentChannel`. Only present for IOU channels where the issuer is neither the source nor the destination. |

### 1.5.2 `MPToken` and `MPTokenIssuance` Ledger Objects

Token-denominated payment channels reuse the `sfLockedAmount` field introduced by [XLS-85](../XLS-0085-token-escrow/README.md) on both the `MPToken` and `MPTokenIssuance` ledger objects:

| Field Name       | JSON Type | Internal Type | Description                                                                               |
| ---------------- | --------- | ------------- | ----------------------------------------------------------------------------------------- |
| `sfLockedAmount` | String    | UInt64        | _(Optional)_ The total of all outstanding escrows and payment channels for this issuance. |

### 1.5.3 `AccountRoot` Ledger Object

No new flags are introduced. Token-denominated payment channels reuse the `lsfAllowTrustLineLocking` flag (`0x40000000`) introduced by [XLS-85](../XLS-0085-token-escrow/README.md): issuers who have enabled trust line locking for escrows have also enabled it for payment channels. See XLS-85 Section 1.6 for the corresponding `asfAllowTrustLineLocking` AccountSet flag.

## 1.6. Future Considerations

1. Issuer as Source: XLS-93 currently does not allow the issuer to be the source of the Payment Channel. If your use case requires this functionality, you should create a new account, send the MPT or IOU to that account, and then create the payment channel with that account as the source.

2. Trustline Deletion While Locked: because the locked IOU value lives in the `PaymentChannel` object rather than on the trustline, an empty trustline can be deleted while channels remain open (see Section 3). Per-trustline lock accounting that would prevent this, for both escrows and payment channels, is deliberately left to a separate future amendment so that XLS-93 stays behaviorally aligned with the activated XLS-85.

## 2. Rationale

Payment channels are the last remaining XRP-only locking primitive; XLS-85 already extended escrows to IOUs and MPTs. Reusing the XLS-85 model wholesale, the same issuer opt-in flags (`lsfAllowTrustLineLocking`, `lsfMPTCanEscrow`), the same `sfLockedAmount` accounting, and the same shared lock/unlock logic in the implementation, means issuers make one opt-in decision that covers both primitives, and both primitives fail and succeed under identical token conditions. Every place where XLS-93 is stricter than base token semantics (any freeze blocks lock creation, no channel creation during global freeze even to the issuer) is inherited from the activated XLS-85 behavior rather than newly invented, keeping the two locking primitives coherent.

`PaymentChannelClawback` is included in the same amendment for the same reason. An issuer's clawback opt-in is a property of the token, so it should hold wherever that token sits. Deferring the transaction would have meant shipping a lock that quietly suspends an issuer control the token already carries, and the alternative of closing the channel first is not open to the issuer, which is not a party to the channel and cannot close it.

## 3. Security Considerations

- **Payee protection.** The destination's earned funds are never gated by source-side state. Normal claims check only destination-side conditions, and the source-side conditions in Channel Closure apply only to refunding a positive remainder; a fully drained channel closes without them.
- **Issuer trust surface.** An issuer that uses `RequireAuth` can deauthorize the source and thereby block the refund leg of closure (`tecNO_AUTH`) until re-authorized. The channel and its locked funds remain on ledger; no funds are lost. This is the same issuer trust surface that exists for XLS-85 escrow refunds and for clawback generally.
- **Transfer rate.** The claim rate is capped at the rate stored at creation (the lower of stored and current is applied), so an issuer cannot retroactively tax funds already locked by raising `TransferRate`/`TransferFee`.
- **Trustline deletion.** The source can delete an empty trustline while a channel is open. Closure refunds then fail with `tecNO_LINE` until the source re-establishes the line; the destination's claims are unaffected. `MPToken` deletion is blocked while locked (`tecHAS_OBLIGATIONS`).
- **Signature domain.** Claim signatures bind the specific channel ID and amount, unchanged from XRP payment channels; token support does not weaken replay protection.
- **Clawback scope.** `PaymentChannelClawback` reaches only the unclaimed remainder and only for an issuer who already holds the clawback opt-in for that token. It cannot reverse a claim the destination has settled, and it cannot touch XRP or a token whose issuer never enabled clawback.
- **Clawback and pending authorizations.** An issuer clawback can invalidate a signed claim authorization the destination is holding, because the authorized balance may exceed the reduced channel `Amount`. A destination that wants to settle ahead of this should claim rather than accumulate authorizations, the same tradeoff that applies to holding an unsettled balance with any clawback-enabled issuer.
