# XLS-85d Token Escrow — Token-Enabled Escrows

```markdown
Title: Token-Enabled Escrows
Revision: 7 (2025-02-17)
Type: Draft
Author:
    Denis Angell, XRPL-Labs [dangell7](https://github.com/dangell7)
Contributors:
    Richard Holland, XRPL-Labs [RichardAH](https://github.com/RichardAH)
    Ed Hennis, Ripple [ximinez](https://github.com/ximinez)
    Mayukha Vadari, Ripple [msvadari](https://github.com/msvadari)
    David Fuelling, Ripple [sappenin](https://github.com/sappenin)
Affiliation: XRPL-Labs
```

> This proposal, XLS85d, replaces [XLS34d](https://github.com/XRPLF/XRPL-Standards/discussions/88) and draws inspiration from https://github.com/XRPLF/XRPL-Standards/discussions/133

The proposed `TokenEscrow` amendment to the XRP Ledger (XRPL) protocol enhances the existing `Escrow` functionality by enabling support for both Trustline-based tokens (IOUs) and Multi-Purpose Tokens (MPTs). This amendment introduces changes to ledger objects, transactions, and transaction processing logic to allow escrows to use IOU tokens and MPTs, while respecting issuer controls and maintaining ledger integrity.

# 1. Implementation

This amendment extends the functionality of escrows to support both IOUs and MPTs, accounting for the specific behaviors and constraints associated with each token type.

## 1.1. Overview of Token Types

### 1.1.1. IOU Tokens

- **Trustlines**: IOUs rely on trustlines between accounts.
- **Issuer Controls**:
  - **Require Authorization (`lsfRequireAuth`)**: Issuers may require accounts to be authorized to hold their tokens.
  - **Freeze Conditions (`lsfGlobalFreeze`, `lsfDefaultRipple`)**: Issuers can freeze tokens, affecting their transferability.
- **Transfer Mechanics**: Transfers occur via adjustments to trustline balances.
- **Transfer Rates**: Issuers can set a `TransferRate` that affects transfers involving their tokens.

### 1.1.2. Multi-Purpose Tokens (MPTs)

- **No Trustlines**: MPTs do not utilize trustlines.
- **Issuer Controls**:
  - **Transfer Flags (`tfMPTCanTransfer`)**: Tokens must have this flag enabled to be transferable and to participate in transactions like escrows.
  - **Require Authorization (`tfMPTRequireAuth`)**: Issuers may require authorization for accounts to hold their tokens.
  - **Lock Conditions (`lsfMPTokenLock`)**: Tokens can be locked by the issuer, affecting their transferability.
- **Transfer Mechanics**: Transfers occur by moving token balances directly between accounts.
- **Transfer Fees**: Issuers can set a `TransferFee` (analogous to `TransferRate` for IOUs) that affects transfers involving their tokens.

## 1.2. Escrow Transactions and Logic

### 1.2.1. `EscrowCreate`

The `EscrowCreate` transaction is modified as follows:

| Field     | Required? | JSON Type        | Internal Type | Description                                                                                                                                        |
|-----------|-----------|------------------|---------------|----------------------------------------------------------------------------------------------------------------------------------------------------|
| `Amount`  | Yes       | Object or String | Amount        | The amount to deduct from the sender's balance and set aside in escrow. Can represent XRP, an IOU token, or an MPT. Must always be a positive value. |
| `CancelAfter`  | False       | Number | UInt32        | (Optional) The time, in seconds since the Ripple Epoch, when this escrow expires. This value is immutable; the funds can only be returned to the sender after this time. Required when creating an Escrow with IOU or MPT |

**Process Overview:**

- **Deduction from Source:**
  - **IOU Tokens**: The escrowed amount is deducted from the source account's trustline balance with the issuer.
  - **MPTs**: The escrowed amount is deducted from the source account's MPT balance.
- **Escrow Object Creation:**
  - An `Escrow` ledger object is created, holding the specified amount and associated conditions.
  - **Fields Set**:
    - `Amount` (IOU or MPT)
    - `TransferRate` (stored at the time of creation for both IOUs and MPTs)
    - `IssuerNode` (if the issuer is neither the source nor the destination)

**Failure Conditions:**

1. **Issuer Does Not Allow Token Escrow or Transfer:**
   - **IOU Tokens**: If the issuer's account does not have the `lsfAllowTokenEscrow` flag set, the transaction fails with `tecNO_PERMISSION`.
   - **MPTs**:
     - If the token lacks the `tfMPTCanEscrow` flag, the transaction fails with `tecNO_PERMISSION`.
     - If the token lacks the `tfMPTCanTransfer` flag, the transaction fails with `tecNO_PERMISSION`.

2. **Source Account Not Authorized to Hold Token:**
   - If the issuer requires authorization and the source is not authorized, the transaction fails with `tecNO_AUTH`.

3. **Source Account's Token Holding Issues:**
   - **IOU Tokens**: If the source lacks a trustline with the issuer, the transaction fails with `tecNO_LINE`.
   - **MPTs**: If the source does not hold the MPT, the transaction fails with `tecOBJECT_NOT_FOUND`.

4. **Source Account is Frozen or Token is Locked:**
   - If the token is frozen (IOU) or locked (MPT) for the source, the transaction fails with `tecFROZEN`.

5. **Insufficient Spendable Balance:**
   - If the source lacks sufficient spendable balance, the transaction fails with `tecINSUFFICIENT_FUNDS`.

**State Changes:**

- **Transfer from Source to Issuer Holding:**
  - **IOU Tokens**: Amount deducted from the source's trustline balance.
  - **MPTs**: Amount moved to a holding controlled by the issuer; the issuer's total outstanding amount remains unchanged.
- **Escrow Object Creation:**
  - The `Escrow` ledger object includes:
    - `CancelAfter`: When the Escrow Expires (Required on IOU/MPT)
    - `Amount`: Tokens held in escrow.
    - `TransferRate`: `TransferRate` (IOUs) or `TransferFee` (MPTs) at creation.
    - `IssuerNode`: Reference to the issuer’s ledger node if applicable.

### 1.2.2. `EscrowFinish`

**Process Overview:**

- **Authorization and Token Holding Checks:**
  - The destination must have an existing trustline (IOUs) or token holding (MPTs).
  - **Authorization Required**:
    - If the issuer requires authorization and the destination is not authorized, the transaction fails with `tecNO_AUTH`.
    - A new trustline or MPT holding cannot be created during `EscrowFinish` if authorization is required.
- **Freeze and Lock Conditions:**
  - **IOU Tokens**:
    - **Deep Freeze**: If the token is deep frozen, the transaction fails with `tecFROZEN`.
    - **Global/Individual Freeze**: If the token is globally or individually frozen, the transaction succeeds.
  - **MPTs**:
    - **Lock Conditions (Deep Freeze Equivalent)**: If the token is locked (frozen) for the destination, the transaction fails with `tecFROZEN`.
    - **Transfer Flags**: If `tfMPTCanTransfer` is not enabled, transaction fails with `tecNO_PERMISSION`.
- **Transfer Mechanics:**
  - **IOU Tokens**: Escrowed amount (adjusted for `TransferRate`) is transferred to the destination's trustline balance.
  - **MPTs**: Escrowed amount (adjusted for `TransferFee`) is transferred to the destination's MPT balance.

**Failure Conditions:**

1. **Destination Not Authorized to Hold Token:**
   - If authorization is required and the destination is not authorized, transaction fails with `tecNO_AUTH`.

2. **Destination Lacks Trustline or MPT Holding:**
   - **IOU Tokens**: If the destination lacks a trustline with the issuer, transaction fails with `tecNO_LINE`.
   - **MPTs**: If the destination does not hold the MPT, transaction fails with `tecNO_ENTRY`.
   - A new trustline or MPT holding cannot be created during `EscrowFinish` if authorization is required.

3. **Cannot Create Trustline or MPT Holding:**
   - If unable to create due to lack of authorization or reserves, transaction fails with `tecNO_AUTH` or `tecINSUFFICIENT_RESERVE`.

4. **Destination Account is Frozen or Token is Locked:**

   - **IOU Tokens**:
     - **Deep Freeze**: If the token is deep frozen, the transaction fails with `tecFROZEN`.
     - **Global/Individual Freeze**: The transaction succeeds despite the token being globally or individually frozen.

   - **MPTs**:
     - **Lock Conditions (Equivalent to Deep Freeze)**: Transaction fails with `tecFROZEN`.
     - **Transfer Flags**: If `tfMPTCanTransfer` is not enabled, transaction fails with `tecNO_PERMISSION`.

**State Changes:**

- **Transfer from Issuer Holding to Destination:**
  - **IOU Tokens**: Adjusted amount credited to destination's trustline balance.
  - **MPTs**: Adjusted amount credited to destination's MPT balance.
- **Deletion of Escrow Object:**
  - The `Escrow` object is deleted after successful settlement.

### 1.2.3. `EscrowCancel`

**Process Overview:**

- **Authorization and Token Holding Checks:**
  - The source must have an existing trustline (IOUs) or token holding (MPTs).
  - **Authorization Required**:
    - If the issuer requires authorization and the source is not authorized, the transaction fails with `tecNO_AUTH`.
    - A new trustline or MPT holding cannot be created during `EscrowCancel` if authorization is required.
- **Freeze and Lock Conditions:**
  - **IOU Tokens**:
    - **Deep Freeze**: The transaction succeeds regardless of freeze status.
    - **Global/Individual Freeze**: The transaction succeeds regardless of freeze status.
  - **MPTs**:
    - **Lock Conditions (Deep Freeze Equivalent)**: The transaction succeeds regardless of lock status.
    - **Transfer Flags**: If `tfMPTCanTransfer` is not enabled, transaction fails with `tecNO_PERMISSION`.
- **Transfer Mechanics:**
  - **IOU Tokens**: Escrowed amount returned to source's trustline balance.
  - **MPTs**: Escrowed amount moved back to source's MPT balance.

**Failure Conditions:**

1. **Source Not Authorized to Hold Token:**
   - If authorization is required and the source is not authorized, transaction fails with `tecNO_AUTH`.

2. **Source Lacks Trustline or MPT Holding:**
   - **IOU Tokens**: If the source lacks a trustline with the issuer, transaction fails with `tecNO_LINE`.
   - **MPTs**: If the source does not hold the MPT, transaction fails with `tecNO_ENTRY`.
   - A new trustline or MPT holding cannot be created during `EscrowCancel` if authorization is required.

3. **Cannot Create Trustline or MPT Holding:**
   - If unable to create due to lack of authorization or reserves, transaction fails with `tecNO_AUTH` or `tecINSUFFICIENT_RESERVE`.

4. **Source Account is Frozen or Token is Locked:**

   - **IOU Tokens**:
     - **Deep Freeze**: The transaction succeeds, allowing the escrow to be cancelled.
     - **Global/Individual Freeze**: The transaction succeeds, allowing the escrow to be cancelled.

   - **MPTs**:
     - **Lock Conditions (Deep Freeze Equivalent)**: The transaction succeeds, allowing the escrow to be cancelled.
     - **Transfer Flags**: If `tfMPTCanTransfer` is not enabled, transaction fails with `tecNO_PERMISSION`.

**State Changes:**

- **Return from Issuer Holding to Source:**
  - **IOU Tokens**: Amount returned to source's trustline balance.
  - **MPTs**: Amount moved back to source's MPT balance.
- **Deletion of Escrow Object:**
  - The `Escrow` object is deleted after successful cancellation.

## 1.3. Key Differences Between IOU and MPT Escrows

| Aspect                        | IOU Tokens                                                               | Multi-Purpose Tokens (MPTs)                                                |
|-------------------------------|--------------------------------------------------------------------------|----------------------------------------------------------------------------|
| **Trustlines**                | Required between accounts and issuer                                     | Not used                                                                   |
| **Issuer Flag for Escrow**    | `lsfAllowTokenEscrow` (account flag)                                       | `tfMPTCanEscrow` (token flag)                                              |
| **Transfer Flags**            | N/A                                                                      | `tfMPTCanTransfer` must be enabled for transfer and escrow                 |
| **Require Auth**              | Applicable (`lsfRequireAuth`); accounts must be authorized prior to holding tokens | Applicable (`tfMPTRequireAuth`); accounts must be authorized prior to holding tokens |
| **Destination Authorization** | Not required at creation; required at settlement; cannot be granted during `EscrowFinish` if authorization required | Not required at creation; required at settlement; cannot be granted during `EscrowFinish` if authorization required |
| **Freeze/Lock Conditions**    | **Deep Freeze** prevents `EscrowFinish`, but allows `EscrowCancel`; Global/Individual Freeze allows both operations | **Lock Conditions (Deep Freeze Equivalent)** prevent `EscrowFinish`, but allow `EscrowCancel` |
| **Transfer Rates/Fees**       | `TransferRate` stored at creation and applied during settlement          | `TransferFee` stored at creation and applied during settlement             |
| **Outstanding Amount**        | Remains unchanged during escrow                                          | Remains unchanged during escrow                                            |
| **Account Deletion**          | Escrows prevent account deletion                                         | Escrows prevent account deletion                                           |

## 1.4. Transfer Rates and Fees

### 1.4.1. IOU Tokens (`TransferRate`)

- **Locked Transfer Rate**: The `TransferRate` is captured at the time of `EscrowCreate` and stored in the `Escrow` object. It is used during `EscrowFinish`, even if the issuer changes it later.
- **Fee Calculation**: The escrowed amount is adjusted according to the `TransferRate` upon settlement, potentially reducing the final amount credited to the destination.

### 1.4.2. MPTs (`TransferFee`)

- **Locked Transfer Fee**: The `TransferFee` is captured at the time of `EscrowCreate` and stored in the `Escrow` object, similar to IOUs.
- **Fee Calculation**: The escrowed amount is adjusted according to the `TransferFee` upon settlement, potentially reducing the final amount credited to the destination.
- **Consistent Fee Application**: Both IOUs and MPTs use the transfer rate or fee stored at escrow creation, ensuring predictability for the destination.

## 1.5. Impact on Outstanding Amount (MPTs)

- **Issuer's Outstanding Amount**: When an MPT escrow is created, the amount is moved to a holding controlled by the issuer, but the issuer's total outstanding amount does not change. This design ensures the issuer does not issue more tokens than allowed.

## 1.6. `Escrow` Ledger Object

The `Escrow` ledger object is updated as follows:

| Field Name      | JSON Type        | Internal Type | Description                                                                                                                                                  |
|-----------------|------------------|---------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `Amount`        | Object or String | Amount        | The amount to be delivered by the held payment. Can represent XRP, an IOU token, or an MPT. Must always be a positive value.                                 |
| `TransferRate`  | Number           | UInt32        | The transfer rate or fee at which the funds are escrowed, stored at creation and used during settlement. Applicable to both IOUs and MPTs.                   |
| `IssuerNode`    | Number           | UInt64        | *(Optional)* The ledger index of the issuer's directory node associated with the `Escrow`. Used when the issuer is neither the source nor destination account.|
