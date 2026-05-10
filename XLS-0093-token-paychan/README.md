<pre>
xls: 93d
title: Token-Enabled Payment Channels
description: Extends Payment Channels to support IOU tokens and Multi-Purpose Tokens (MPTs).
author: Denis Angell (@dangell7)
discussion-from: https://github.com/XRPLF/XRPL-Standards/discussions/287
category: Amendment
status: Draft
created: 2025-05-24
updated: 2026-05-06
</pre>

# Token-Enabled Payment Channels

## 1. Abstract

This proposal introduces the `TokenPaychan` amendment to the XRP Ledger (XRPL), extending the existing `PaymentChannel` functionality to support both Trustline-based tokens (IOUs) and Multi-Purpose Tokens (MPTs) in addition to XRP. It defines updates to ledger objects, transactions, and transaction processing logic so that payment channels can hold and settle non-XRP assets while respecting issuer controls (authorization, freeze/lock, transfer rates/fees) and preserving ledger integrity. Transfer rates and fees are captured at channel creation and applied consistently at claim time, providing predictable settlement for participants.

## 2. Motivation

Payment channels on the XRPL today are limited to XRP. As issued assets (IOUs) and Multi-Purpose Tokens become increasingly used for payments, settlement, and tokenization use cases, the inability to use them in off-ledger/streamed-payment workflows blocks important applications such as token-denominated micropayments, streaming payments for stablecoins, and recurring token settlements between counterparties. Extending payment channels to support IOUs and MPTs closes this gap while keeping the existing issuer guarantees (authorization, freeze/lock, transfer fees) intact and predictable.

## 3. Specification

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be interpreted as described in RFC 2119 and RFC 8174.

This amendment extends the functionality of payment channels to support both IOUs and MPTs, accounting for the specific behaviors and constraints associated with each token type.

### 3.1. Overview of Token Types

#### 3.1.1. IOU Tokens

- **Trustlines**: IOUs rely on trustlines between accounts.
- **Issuer Controls**:
  - **Require Authorization (`lsfRequireAuth`)**: Issuers may require accounts to be authorized to hold their tokens.
  - **Freeze Conditions (`lsfGlobalFreeze`, `lsfDefaultRipple`)**: Issuers can freeze tokens, affecting their transferability.
- **Transfer Mechanics**: Transfers occur via adjustments to trustline balances.
- **Transfer Rates**: Issuers can set a `TransferRate` that affects transfers involving their tokens.

#### 3.1.2. Multi-Purpose Tokens (MPTs)

- **No Trustlines**: MPTs do not utilize trustlines.
- **Issuer Controls**:
  - **Transfer Flags (`tfMPTCanTransfer`)**: Tokens MUST have this flag enabled to be transferable and to participate in transactions like payment channels.
  - **Require Authorization (`tfMPTRequireAuth`)**: Issuers may require authorization for accounts to hold their tokens.
  - **Lock Conditions (`lsfMPTokenLock`)**: Tokens can be locked by the issuer, affecting their transferability.
- **Transfer Mechanics**: Transfers occur by moving token balances directly between accounts.
- **Transfer Fees**: Issuers can set a `TransferFee` (analogous to `TransferRate` for IOUs) that affects transfers involving their tokens.

### 3.2. Transactions

#### 3.2.1. `PaymentChannelCreate`

The `PaymentChannelCreate` transaction is modified as follows:

| Field    | Required? | JSON Type        | Internal Type | Description                                                                                                                                                                                                                                                                                                              |
|----------|-----------|------------------|---------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `Amount` | Yes       | Object or String | Amount        | The amount to fund the payment channel. Can represent [XRP, in drops](https://xrpl.org/docs/references/protocol/data-types/basic-data-types#specifying-currency-amounts), an [IOU](https://xrpl.org/docs/concepts/tokens/fungible-tokens#fungible-tokens) token, or an [MPT](https://xrpl.org/docs/concepts/tokens/fungible-tokens/multi-purpose-tokens). MUST always be a positive value. |

##### Failure Conditions

- **Issuer is the Source:**
  - If the source account is the issuer of the token, the transaction fails with `tecNO_PERMISSION`.
- **Issuer Does Not Allow Token Payment Channels:**
  - **IOU Tokens**: If the issuer's account does not have the `lsfAllowTokenEscrow` flag set, the transaction fails with `tecNO_PERMISSION`.
  - **MPTs**:
    - If the `MPTokenIssuance` of the token being used lacks the `lsfMPTCanEscrow` flag, the transaction fails with `tecNO_PERMISSION`.
    - If the `MPTokenIssuance` of the token being used lacks the `lsfMPTCanTransfer` flag, the transaction fails with `tecNO_PERMISSION` unless the destination address of the Payment Channel is the issuer of the MPT.
- **Source Account Not Authorized to Hold Token:**
  - If the issuer requires authorization and the source is not authorized, the transaction fails with `tecNO_AUTH`.
- **Source Account's Token Holding Issues:**
  - **IOU Tokens**: If the source lacks a trustline with the issuer, the transaction fails with `tecUNFUNDED`.
  - **MPTs**: If the source does not hold the MPT, the transaction fails with `tecOBJECT_NOT_FOUND`.
- **Source Account is Frozen or Token is Locked:**
  - If the token is frozen (global/individual/deepfreeze) (IOU) or locked (MPT) for the source, the transaction fails with `tecFROZEN`.
- **Insufficient Spendable Balance:**
  - If the source account lacks sufficient spendable balance, the transaction fails with `tecUNFUNDED`.

##### State Changes

- **Adjustment from Source to Issuer:**
  - **IOU Tokens**: The channel `Amount` is deducted from the source's trustline balance.
  - **MPTs**: The channel `Amount` is deducted from the source's MPT balance. The `sfOutstandingBalance` of the MPT issuance remains unchanged. The `sfEscrowAmount` is increased on both the source's MPT and the MPT issuance.
- **Payment Channel Object Creation:**
  - The `PaymentChannel` ledger object includes:
    - `Amount`: Tokens held in the channel.
    - `Balance`: Amount already paid out (starts at zero).
    - `TransferRate`: `TransferRate` (IOUs) or `TransferFee` (MPTs) at creation.
    - `IssuerNode`: Reference to the issuer's ledger node if applicable.

#### 3.2.2. `PaymentChannelFund`

The `PaymentChannelFund` transaction is modified to support token amounts.

##### Failure Conditions

- **Same conditions as `PaymentChannelCreate`** for validating the funding amount and token permissions.

##### State Changes

- **Adjustment from Source:**
  - **IOU Tokens**: The funding `Amount` is deducted from the source's trustline balance.
  - **MPTs**: The funding `Amount` is deducted from the source's MPT balance. The `sfEscrowAmount` is increased accordingly.
- **Payment Channel Object Update:**
  - The channel's `Amount` field is increased by the funding amount.

#### 3.2.3. `PaymentChannelClaim`

##### Normal Claim (Balance Update)

When claiming without closing the channel:

###### Failure Conditions

- **Destination Not Authorized to Hold Token:**
  - If authorization is required and the destination is not authorized, the transaction fails with `tecNO_AUTH`.
- **Destination Lacks Trustline or MPT Holding:**
  - **IOU Tokens**: If the destination lacks a trustline with the issuer, the transaction fails with `tecNO_LINE`.
  - **MPTs**: If the destination does not hold the MPT, the transaction fails with `tecNO_ENTRY`.
  - A new trustline or MPT holding MAY be created during `PaymentChannelClaim` if authorization is not required.
- **Cannot Create Trustline or MPT Holding:**
  - If unable to create due to lack of authorization or reserves, the transaction fails with `tecNO_AUTH` or `tecINSUFFICIENT_RESERVE`.
- **Destination Account is Frozen or Token is Locked:**
  - **IOU Tokens**:
    - **Deep Freeze**: If the token is deep frozen, the transaction fails with `tecFROZEN`.
    - **Global/Individual Freeze**: The transaction succeeds despite the token being globally or individually frozen.
  - **MPTs**:
    - **Lock Conditions (Equivalent to Deep Freeze)**: The transaction fails with `tecFROZEN`.

###### State Changes

- **Auto-create Trustline or MPToken:**
  - **IOU Tokens**: If the IOU does not require authorization and the account submitting the transaction is the recipient, then a trustline will be created.
  - **MPTs**: If the MPT does not require authorization and the account submitting the transaction is the recipient, then the MPT will be created.
- **Adjustment to Destination:**
  - **IOU Tokens**: The claimed amount is added to the destination's trustline balance.
  - **MPTs**: Similar to escrow logic for MPT balance adjustments.
- **Channel Balance Update:**
  - The channel's `Balance` field is updated to reflect the total amount claimed.

##### Channel Closure

When closing the channel (either explicitly with the close flag, or automatically when fully drained):

###### Failure Conditions

- **Source Not Authorized to Hold Token (for remaining funds):**
  - If authorization is required and the source is not authorized, the transaction fails with `tecNO_AUTH`.
- **Source Lacks Trustline or MPT Holding (for remaining funds):**
  - **IOU Tokens**: If the source lacks a trustline with the issuer, the transaction fails with `tecNO_LINE`.
  - **MPTs**: If the source does not hold the MPT, the transaction fails with `tecNO_ENTRY`.
  - A new trustline or MPT holding MAY be created during channel closure if authorization is not required.
- **Cannot Create Trustline or MPT Holding (for source):**
  - If unable to create due to lack of authorization or reserves, the transaction fails with `tecNO_AUTH` or `tecINSUFFICIENT_RESERVE`.
- **Source Account is Frozen or Token is Locked:**
  - **IOU Tokens**:
    - **Deep Freeze**: The transaction succeeds, allowing the channel to be closed.
    - **Global/Individual Freeze**: The transaction succeeds, allowing the channel to be closed.
  - **MPTs**:
    - **Lock Conditions (Deep Freeze Equivalent)**: The transaction succeeds, allowing the channel to be closed.

###### State Changes

- **Auto-create Trustline or MPToken (for source):**
  - **IOU Tokens**: If the IOU does not require authorization and the account submitting the transaction is the source, then a trustline will be created.
  - **MPTs**: If the MPT does not require authorization and the account submitting the transaction is the source, then the MPT will be created.
- **Adjustment to Destination (final claim):**
  - Any remaining claimable amount is transferred to the destination using the same logic as normal claims.
- **Adjustment to Source (remaining funds):**
  - **IOU Tokens**: Any remaining channel funds are added to the source's trustline balance.
  - **MPTs**: Any remaining channel funds are added to the source's MPT balance. The `sfOutstandingBalance` of the MPT issuance remains unchanged. The `sfEscrowAmount` is decreased on both the source's MPT and the MPT issuance.
- **Deletion of Payment Channel Object:**
  - The `PaymentChannel` object is deleted after successful closure.

### 3.3. Ledger Entries

#### 3.3.1. `PaymentChannel` Ledger Object

The `PaymentChannel` ledger object is updated as follows:

| Field Name     | JSON Type        | Internal Type | Description                                                                                                                                                          |
|----------------|------------------|---------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `Amount`       | Object or String | Amount        | The total amount allocated to the payment channel. Can represent XRP, an IOU token, or an MPT. MUST always be a positive value.                                    |
| `Balance`      | Object or String | Amount        | The amount already paid out from the channel. Same asset type as `Amount`.                                                                                           |
| `TransferRate` | Number           | UInt32        | The transfer rate or fee at which the funds are held, stored at creation and used during claims. Applicable to both IOUs and MPTs.                                  |
| `IssuerNode`   | Number           | UInt64        | *(Optional)* The ledger index of the issuer's directory node associated with the `PaymentChannel`. Used when the issuer is neither the source nor destination account. |

#### 3.3.2. `MPToken` Ledger Object

The `MPToken` ledger object is updated as follows:

| Field Name        | JSON Type | Internal Type | Description                                                                                  |
|-------------------|-----------|---------------|----------------------------------------------------------------------------------------------|
| `sfEscrowAmount`  | Object    | Amount        | *(Optional)* The total of all outstanding escrows and payment channels for this token.       |

#### 3.3.3. `MPTokenIssuance` Ledger Object

The `MPTokenIssuance` ledger object is updated as follows:

| Field Name        | JSON Type | Internal Type | Description                                                                                     |
|-------------------|-----------|---------------|-------------------------------------------------------------------------------------------------|
| `sfEscrowAmount`  | Object    | Amount        | *(Optional)* The total of all outstanding escrows and payment channels for this issuance.       |

### 3.4. Transfer Rates and Fees

#### 3.4.1. IOU Tokens (`TransferRate`)

- **Locked Transfer Rate**: The `TransferRate` is captured at the time of `PaymentChannelCreate` and stored in the `PaymentChannel` object. It is used during `PaymentChannelClaim`, even if the issuer changes it later.
- **Fee Calculation**: The claimed amount is adjusted according to the `TransferRate` upon settlement, potentially reducing the final amount credited to the destination.

#### 3.4.2. MPTs (`TransferFee`)

- **Locked Transfer Fee**: The `TransferFee` is captured at the time of `PaymentChannelCreate` and stored in the `PaymentChannel` object, similar to IOUs.
- **Fee Calculation**: The claimed amount is adjusted according to the `TransferFee` upon settlement, potentially reducing the final amount credited to the destination.
- **Consistent Fee Application**: Both IOUs and MPTs use the transfer rate or fee stored at channel creation, ensuring predictability for the destination.

### 3.5. Key Differences Between IOU and MPT Payment Channels

| Aspect                        | IOU Tokens                                                                                            | Multi-Purpose Tokens (MPTs)                                                                          |
|-------------------------------|-------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------|
| **Trustlines**                | Required between accounts and issuer                                                                  | Not used                                                                                             |
| **Issuer Flag for Channels**  | `lsfAllowTokenEscrow` (account flag)                                                                  | `tfMPTCanEscrow` (token flag)                                                                        |
| **Transfer Flags**            | N/A                                                                                                   | `tfMPTCanTransfer` must be enabled for payment channels                                              |
| **Require Auth**              | Applicable (`lsfRequireAuth`); accounts must be authorized prior to holding tokens                    | Applicable (`tfMPTRequireAuth`); accounts must be authorized prior to holding tokens                 |
| **Destination Authorization** | Not required at creation; required at claim; cannot be granted during claim if authorization required | Not required at creation; required at claim; cannot be granted during claim if authorization required|
| **Freeze/Lock Conditions**    | **Deep Freeze** prevents claims, but allows closure; Global/Individual Freeze allows both operations  | **Lock Conditions (Deep Freeze Equivalent)** prevent claims, but allow closure                       |
| **Transfer Rates/Fees**       | `TransferRate` stored at creation and applied during claims                                           | `TransferFee` stored at creation and applied during claims                                           |
| **Outstanding Amount**        | Remains unchanged during channel operations                                                           | Remains unchanged during channel operations                                                          |
| **Account Deletion**          | Payment channels prevent account deletion                                                             | Payment channels prevent account deletion                                                            |

## 4. Rationale

The amendment reuses the existing `PaymentChannel` mechanics so issuers, wallets, and tooling can extend support to non-XRP assets without learning a new construct. Key design decisions:

- **Lock the transfer rate/fee at creation.** Capturing `TransferRate`/`TransferFee` in the `PaymentChannel` object ensures that the destination has a predictable settlement value over the lifetime of the channel, regardless of issuer-side changes. This mirrors how other XRPL constructs that pre-commit value (e.g. escrow) treat issuer-controlled fees.
- **Account-level vs. token-level opt-in.** IOUs use an account flag (`lsfAllowTokenEscrow`) because IOU issuance is account-scoped, while MPTs use a token flag (`tfMPTCanEscrow`) because each issuance has its own configuration. This keeps each control surface where issuers already manage it.
- **Disallow the issuer as source.** Letting the issuer be the source account would conflate issuance with channel funding and complicate `sfOutstandingBalance` accounting. Issuers who want to fund a channel can route through a separate holding account, which is also recommended for operational hygiene. See §3.6.
- **Preserve `sfOutstandingBalance` and track `sfEscrowAmount` separately.** Funds in a channel are still in circulation from the issuer's perspective; tracking them under `sfEscrowAmount` keeps issuance accounting accurate while making channel-locked balances explicit.
- **Reuse existing freeze/deep-freeze and lock semantics.** Aligning IOU and MPT behavior to the deep-freeze / lock equivalence (claims blocked, closure allowed) keeps the model consistent with how those controls operate elsewhere on the ledger.
- **Auto-creation rules mirror direct payments.** Allowing trustline/MPToken auto-creation on claim only when authorization is not required matches existing token settlement behavior and avoids surprising the recipient with an unsolicited holding when the issuer requires authorization.

### 3.6. Future Considerations

1. **Clawback**: This specification currently does not provide a direct "clawback" mechanism within an active Payment Channel. If a use case requires clawback, the channel can be closed and existing IOU/MPT clawback features used on the returned funds.
2. **Issuer as Source**: This specification currently does not allow the issuer to be the source of the Payment Channel. If a use case requires this functionality, a new account should be created, the MPT or IOU sent to that account, and then the payment channel created with that account as the source.

## 5. Backwards Compatibility

This amendment is backwards compatible with existing XRP-only payment channels: any `PaymentChannel`, `PaymentChannelCreate`, `PaymentChannelFund`, and `PaymentChannelClaim` whose `Amount` is XRP behaves exactly as before. The only behavioral changes occur for new transactions whose `Amount` references an IOU or MPT.

The following are net-new requirements introduced by this amendment and only apply to token-denominated channels:

- New ledger fields (`TransferRate` on `PaymentChannel`; `sfEscrowAmount` on `MPToken` and `MPTokenIssuance`) are optional and ignored by pre-amendment objects.
- New issuer opt-in flags (`lsfAllowTokenEscrow` for IOUs and `tfMPTCanEscrow` for MPTs) ensure issuers must explicitly enable token-denominated channels for their assets, preventing surprise behavior on existing issuances.
- Consumers of `PaymentChannel` ledger objects (clients, indexers, channel watchers) should be updated to handle non-XRP `Amount`/`Balance` representations and the optional `TransferRate` and `IssuerNode` fields.

There are no changes to the wire format or semantics of existing XRP-denominated channels.

## 6. Test Plan

The implementation will include unit and integration tests covering, at minimum:

- XRP, IOU, and MPT variants of `PaymentChannelCreate`, `PaymentChannelFund`, and `PaymentChannelClaim`, including normal claims and channel closure.
- Issuer opt-in enforcement (`lsfAllowTokenEscrow`, `tfMPTCanEscrow`) and `tfMPTCanTransfer` requirement.
- Authorization enforcement (`lsfRequireAuth`, `tfMPTRequireAuth`) at create, claim, and closure.
- Freeze and deep-freeze behavior for IOUs and lock conditions for MPTs, for both source and destination, on claim and closure paths.
- `TransferRate` / `TransferFee` capture at creation and consistent application at claim.
- `sfEscrowAmount` accounting on `MPToken` and `MPTokenIssuance` across funding, claims, and closure.
- Auto-creation of trustlines / `MPToken` objects only when authorization is not required.
- Failure-condition matrix covering each `tec*` listed above.
- Account deletion blocking when token-denominated channels exist.

## 7. Reference Implementation

To be linked when the corresponding rippled PR is opened.

## 8. Security Considerations

- **Issuer opt-in is mandatory.** Token-denominated channels require explicit issuer opt-in (`lsfAllowTokenEscrow` for IOUs, `tfMPTCanEscrow` for MPTs). Without this, no holder can lock issuer-controlled assets in a payment channel, preserving the issuer's existing controls.
- **Issuer cannot be source.** Disallowing the issuer as the source account prevents conflation of issuance with channel funding and avoids ambiguous `sfOutstandingBalance` accounting; issuers must route through a holding account.
- **Locked transfer rate/fee.** Capturing the `TransferRate`/`TransferFee` at creation prevents an issuer from changing settlement economics mid-channel. This protects the destination from unexpected fee increases but also means a fee reduction by the issuer will not propagate to existing channels.
- **Freeze/lock semantics.** Deep freeze (IOU) and lock (MPT) block new claims but permit closure, ensuring counterparties can always recover remaining funds without enabling continued transfers when the issuer has revoked transferability.
- **Authorization at claim time.** Destinations whose holdings require authorization MUST be authorized before they can claim; auto-creation of a trustline or `MPToken` is only permitted when authorization is not required, preventing unsolicited holdings.
- **Account deletion.** Open token-denominated payment channels prevent account deletion of the source, mirroring existing XRP-channel behavior and avoiding orphaned references.
- **`sfEscrowAmount` accounting.** All funds locked in token-denominated channels are tracked via `sfEscrowAmount` on the relevant `MPToken` and `MPTokenIssuance` objects, so channel-locked balances are explicit and auditable while `sfOutstandingBalance` continues to reflect circulating supply.
- **Replay and signature behavior unchanged.** The amendment does not change the authorization model for off-ledger claim signatures (`PaymentChannelClaim` signature validation), so existing replay-protection and channel-signing analyses continue to apply.
- **Client/indexer assumptions.** Tooling that previously assumed `PaymentChannel.Amount` is always XRP must be updated; failing to do so could lead to misreporting of balances or failed settlements but cannot, by itself, cause loss of funds on-ledger.

# Appendix

## Appendix A: FAQ

### A.1: Why can't the issuer be the source of a token payment channel?

Allowing the issuer to be the source would mix issuance with channel funding and complicate the `sfOutstandingBalance` accounting on the issuance. Issuers who want this behavior can use a separate holding account as the source.

### A.2: What happens to the transfer rate or fee if the issuer changes it after the channel is created?

The `TransferRate` (IOU) or `TransferFee` (MPT) is captured at `PaymentChannelCreate` and stored on the `PaymentChannel` object. Subsequent changes by the issuer do not affect existing channels.

### A.3: Can a destination receive a token they don't already hold?

Yes, but only when the issuer does not require authorization. In that case a new trustline or `MPToken` may be auto-created during claim or closure. If authorization is required, the destination must be authorized in advance.

### A.4: How are frozen IOUs and locked MPTs treated?

Deep-frozen IOUs and locked MPTs block new claims (the transaction fails with `tecFROZEN`) but allow channel closure so that the source can recover remaining funds.

### A.5: Does this affect existing XRP payment channels?

No. XRP-denominated payment channels are fully backwards compatible and behave exactly as before this amendment.