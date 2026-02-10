<pre>
  xls: 85
  title: Token-Enabled Escrows
  description: Enhancement to existing Escrow functionality to support both Trustline-based tokens (IOUs) and Multi-Purpose Tokens (MPTs)
  author: Denis Angell (@dangell7)
  proposal-from: https://github.com/XRPLF/XRPL-Standards/discussions/248
  status: Final
  category: Amendment
  requires: [XLS-33](../XLS-0033-multi-purpose-tokens/README.md)
  created: 2024-11-07
</pre>

> This proposal, XLS-85, replaces [XLS-34](../XLS-0034-paychan-escrow-for-tokens/README.md) and draws inspiration from https://github.com/XRPLF/XRPL-Standards/discussions/133.

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

| Field    | Required? | JSON Type        | Internal Type | Description                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   |
| -------- | --------- | ---------------- | ------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `Amount` | Yes       | Object or String | Amount        | The amount to deduct from the sender's balance and and set aside in escrow. Once escrowed, this amount can either go to the Destination address (after any `Finish` times/conditions) or returned to the sender (after any cancellation times/conditions). Can represent [XRP, in drops](https://xrpl.org/docs/references/protocol/data-types/basic-data-types#specifying-currency-amounts), an [IOU](https://xrpl.org/docs/concepts/tokens/fungible-tokens#fungible-tokens) token, or an [MPT](https://xrpl.org/docs/concepts/tokens/fungible-tokens/multi-purpose-tokens). Must always be a positive value. |

**Failure Conditions:**

- **Issuer is the Source:**
  - If the source account is the issuer of the token, the transaction fails with `tecNO_PERMISSION`.

- **Issuer Does Not Allow Token Escrow or Transfer:**
  - **IOU Tokens**: If the issuer's account does not have the `lsfAllowTrustLineLocking` flag set, the transaction fails with `tecNO_PERMISSION`.
  - **MPTs**:
    - If the `MPTokenIssuance` of the token being escrowed lacks the `lsfMPTCanEscrow` flag, the transaction fails with `tecNO_PERMISSION`.
    - If the `MPTokenIssuance` of the token being escrowed lacks the `lsfMPTCanTransfer` flag, the transaction fails with `tecNO_PERMISSION` unless the destination address of the Escrow is the issuer of the MPT.

- **Source Account Not Authorized to Hold Token:**
  - If the issuer requires authorization and the source is not authorized, the transaction fails with `tecNO_AUTH`.

- **Source Account's Token Holding Issues:**
  - **IOU Tokens**: If the source lacks a trustline with the issuer, the transaction fails with `tecUNFUNDED `.
  - **MPTs**: If the source does not hold the MPT, the transaction fails with `tecOBJECT_NOT_FOUND`.

- **Source Account is Frozen or Token is Locked:**
  - If the token is frozen (global/individual/deepfreeze) (IOU) or locked (MPT) for the source, the transaction fails with `tecFROZEN`.

- **Insufficient Spendable Balance:**
  - If the source account lacks sufficient spendable balance, the transaction fails with `tecUNFUNDED`.

**State Changes:**

- **Adjustment from Source to Issuer:**
  - **IOU Tokens**: The escrow `Amount` is deducted from the source's trustline balance.
  - **MPTs**: The escrow `Amount` is deducted from the source's MPT balance. The `sfOutstandingBalance` of the MPT issuance remains unchanged. The `sfLockedAmount` is increased on both the source's MPT and the MPT issuance.
- **Escrow Object Creation:**
  - The `Escrow` ledger object includes:
    - `Amount`: Tokens held in escrow.
    - `TransferRate`: `TransferRate` (IOUs) or `TransferFee` (MPTs) at creation.
    - `IssuerNode`: Reference to the issuer’s ledger node if applicable.

### 1.2.2. `EscrowFinish`

**Failure Conditions:**

- **Destination Not Authorized to Hold Token:**
  - If authorization is required and the destination is not authorized, transaction fails with `tecNO_AUTH`.

- **Destination Lacks Trustline or MPT Holding:**
  - **IOU Tokens**: If the destination lacks a trustline with the issuer, transaction fails with `tecNO_LINE`.
  - **MPTs**: If the destination does not hold the MPT, transaction fails with `tecNO_ENTRY`.
  - A new trustline or MPT holding may be created during `EscrowFinish` if authorization is not required.

- **Cannot Create Trustline or MPT Holding:**
  - If unable to create due to lack of authorization or reserves, transaction fails with `tecNO_AUTH` or `tecINSUFFICIENT_RESERVE`.

- **Destination Account is Frozen or Token is Locked:**
  - **IOU Tokens**:
    - **Deep Freeze**: If the token is deep frozen, the transaction fails with `tecFROZEN`.
    - **Global/Individual Freeze**: The transaction succeeds despite the token being globally or individually frozen.
  - **MPTs**:
    - **Lock Conditions (Equivalent to Deep Freeze)**: Transaction fails with `tecFROZEN`.

**State Changes:**

- **Auto create Trustline or MPToken:**
  - **IOU Tokens**: If the IOU does not require authorization and the account submitting the transaction is the recipient, then a trustline will be created.
  - **MPTs**: If the MPT does not require authorization and the account submitting the transaction is the recipient, then the MPT will be created.
- **Adjustment from Issuer to Destination:**
  - **IOU Tokens**: The escrow `Amount` is added to the destination's trustline balance.
  - **MPTs**:
    - If the escrow sender is the issuer of the asset that was escrowed and the destination is not the issuer, then:
      1. The `LockedAmount` on the `MPTokenIssuance` of the asset that was held in escrow is decreased by `Amount`.
      2. The `Amount` on the destination's `MPToken` is increased by the escrow's `Amount`.
      3. The `OutstandingAmount` on the `MPTokenIssuance` of the asset that was held in escrow is unchanged.
    - If the escrow sender is not the issuer of the asset that was escrowed but the destination is the issuer of the asset, then:
      1. The `LockedAmount` on the `MPTokenIssuance` of the asset that was held in escrow is decreased by `Amount`.
      2. No `MPToken` objects are changed because MPT issuers may not hold MPTokens.
      3. The `OutstandingAmount` on the `MPTokenIssuance` of the asset that was held in escrow is decreased by `Amount` (i.e., this escrow finish is a "redemption").
    - If neither the escrow source nor destination is the issuer of the asset that was escrowed, then
      1. The `LockedAmount` on the `MPTokenIssuance` of the asset that was held in escrow is decreased by the escrow `Amount`.
      2. The `LockedAmount` on the source's `MPToken` is decreased by the escrow `Amount`.
      3. The `Amount` on the destination's `MPToken` is increased by the escrow `Amount`.
      4. The `OutstandingAmount` on the `MPTokenIssuance` of the asset that was held in escrow is unchanged.
- **Deletion of Escrow Object:**
  - The `Escrow` object is deleted after successful settlement.

### 1.2.3. `EscrowCancel`

**Failure Conditions:**

- **Source Not Authorized to Hold Token:**
  - If authorization is required and the source is not authorized, transaction fails with `tecNO_AUTH`.

- **Source Lacks Trustline or MPT Holding:**
  - **IOU Tokens**: If the source lacks a trustline with the issuer, transaction fails with `tecNO_LINE`.
  - **MPTs**: If the source does not hold the MPT, transaction fails with `tecNO_ENTRY`.
  - A new trustline or MPT holding may be created during `EscrowCancel` if authorization is not required.

- **Cannot Create Trustline or MPT Holding:**
  - If unable to create due to lack of authorization or reserves, transaction fails with `tecNO_AUTH` or `tecINSUFFICIENT_RESERVE`.

- **Source Account is Frozen or Token is Locked:**
  - **IOU Tokens**:
    - **Deep Freeze**: The transaction succeeds, allowing the escrow to be cancelled.
    - **Global/Individual Freeze**: The transaction succeeds, allowing the escrow to be cancelled.
  - **MPTs**:
    - **Lock Conditions (Deep Freeze Equivalent)**: The transaction succeeds, allowing the escrow to be cancelled.

**State Changes:**

- **Auto create Trustline or MPToken:**
  - **IOU Tokens**: If the IOU does not require authorization and the account submitting the transaction is the recipient, then a trustline will be created.
  - **MPTs**: If the MPT does not require authorization and the account submitting the transaction is the recipient, then the MPT will be created.
- **Adjustment from Issuer to Source:**
  - **IOU Tokens**: The escrow `Amount` is added to the source's trustline balance.
  - **MPTs**: The escrow `Amount` is added to the source's MPT balance. The `sfOutstandingBalance` of the MPT issuance remains unchanged. The `sfLockedAmount` is decreased on both the source's MPT and the MPT issuance.
- **Deletion of Escrow Object:**
  - The `Escrow` object is deleted after successful cancellation.

## 1.3. Key Differences Between IOU and MPT Escrows

| Aspect                        | IOU Tokens                                                                                                          | Multi-Purpose Tokens (MPTs)                                                                                         |
| ----------------------------- | ------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------- |
| **Trustlines**                | Required between accounts and issuer                                                                                | Not used                                                                                                            |
| **Issuer Flag for Escrow**    | `lsfAllowTrustLineLocking` (account flag)                                                                           | `tfMPTCanEscrow` (token flag)                                                                                       |
| **Transfer Flags**            | N/A                                                                                                                 | `tfMPTCanTransfer` must be enabled for escrow                                                                       |
| **Require Auth**              | Applicable (`lsfRequireAuth`); accounts must be authorized prior to holding tokens                                  | Applicable (`tfMPTRequireAuth`); accounts must be authorized prior to holding tokens                                |
| **Destination Authorization** | Not required at creation; required at settlement; cannot be granted during `EscrowFinish` if authorization required | Not required at creation; required at settlement; cannot be granted during `EscrowFinish` if authorization required |
| **Freeze/Lock Conditions**    | **Deep Freeze** prevents `EscrowFinish`, but allows `EscrowCancel`; Global/Individual Freeze allows both operations | **Lock Conditions (Deep Freeze Equivalent)** prevent `EscrowFinish`, but allow `EscrowCancel`                       |
| **Transfer Rates/Fees**       | `TransferRate` stored at creation and applied during settlement                                                     | `TransferFee` stored at creation and applied during settlement                                                      |
| **Outstanding Amount**        | Remains unchanged during escrow                                                                                     | Remains unchanged during escrow                                                                                     |
| **Account Deletion**          | Escrows prevent account deletion                                                                                    | Escrows prevent account deletion                                                                                    |

## 1.4. Transfer Rates and Fees

### 1.4.1. IOU Tokens (`TransferRate`)

- **Locked Transfer Rate**: The `TransferRate` is captured at the time of `EscrowCreate` and stored in the `Escrow` object. It is used during `EscrowFinish`, even if the issuer changes it later.
- **Fee Calculation**: The escrowed amount is adjusted according to the `TransferRate` upon settlement, potentially reducing the final amount credited to the destination.

### 1.4.2. MPTs (`TransferFee`)

- **Locked Transfer Fee**: The `TransferFee` is captured at the time of `EscrowCreate` and stored in the `Escrow` object, similar to IOUs.
- **Fee Calculation**: The escrowed amount is adjusted according to the `TransferFee` upon settlement, potentially reducing the final amount credited to the destination.
- **Consistent Fee Application**: Both IOUs and MPTs use the transfer rate or fee stored at escrow creation, ensuring predictability for the destination.

## 1.5. Ledger Object Updates

### 1.5.1 `Escrow` Ledger Object

The `Escrow` ledger object is updated as follows:

| Field Name     | JSON Type        | Internal Type | Description                                                                                                                                                    |
| -------------- | ---------------- | ------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `Amount`       | Object or String | Amount        | The amount to be delivered by the held payment. Can represent XRP, an IOU token, or an MPT. Must always be a positive value.                                   |
| `TransferRate` | Number           | UInt32        | The transfer rate or fee at which the funds are escrowed, stored at creation and used during settlement. Applicable to both IOUs and MPTs.                     |
| `IssuerNode`   | Number           | UInt64        | _(Optional)_ The ledger index of the issuer's directory node associated with the `Escrow`. Used when the issuer is neither the source nor destination account. |

### 1.5.2 `MPToken` Ledger Object

The `MPToken` ledger object is updated as follows:

| Field Name       | JSON Type | Internal Type | Description                                                          |
| ---------------- | --------- | ------------- | -------------------------------------------------------------------- |
| `sfLockedAmount` | String    | UInt64        | _(Optional)_ The total of all outstanding escrows for this issuance. |

### 1.5.3 `MPTokenIssuance` Ledger Object

The `MPTokenIssuance` ledger object is updated as follows:

| Field Name       | JSON Type | Internal Type | Description                                                          |
| ---------------- | --------- | ------------- | -------------------------------------------------------------------- |
| `sfLockedAmount` | String    | UInt64        | _(Optional)_ The total of all outstanding escrows for this issuance. |

### 1.5.4 `AccountRoot` Ledger Object

This proposal introduces 1 additional flag for the `Flags` field of `AccountRoot`:

|         Flag Name          |  Flag Value  |
| :------------------------: | :----------: |
| `lsfAllowTrustLineLocking` | `0x40000000` |

## 1.6. AccountSet Transaction Updates

To enable IOU tokens to be held in escrow, issuers must set the `lsfAllowTrustLineLocking` flag on their account. This is done using the AccountSet transaction with the new `asfAllowTrustLineLocking` flag.

### 1.6.1. New AccountSet Flag

The following AccountSet flag is added to enable trust line locking for escrows:

| Flag Name                  | Decimal Value | Description                                                                                                                                                                                                                                                |
| :------------------------- | :------------ | :--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `asfAllowTrustLineLocking` | 17            | Allow trust line tokens (IOUs) issued by this account to be held in escrow. _(Requires the TokenEscrow amendment.)_ Can only be enabled by the issuer account. Once enabled, holders of this account's issued tokens can create escrows with those tokens. |

### 1.6.2. Usage Example

To enable trust line locking for an issuer account:

```json
{
  "TransactionType": "AccountSet",
  "Account": "rIssuerAccountAddress...",
  "SetFlag": 17,
  "Fee": "12",
  "Sequence": 5
}
```

**Important Notes:**

- This flag must be set by the token issuer account before any escrows can be created with their IOUs
- The flag applies only to IOU tokens (trust line based tokens)
- For MPTs, escrow permissions are controlled by the `tfMPTCanEscrow` flag on the MPTokenIssuance object
- If an issuer's account does not have this flag set, attempts to create escrows with their IOUs will fail with `tecNO_PERMISSION`

## 1.7. Future Considerations

1. Clawback: XLS-85 currently does not provide a direct “clawback” mechanism within an active Escrow. If your use case requires clawback, you can either finish or cancel the Escrow (as appropriate) and then perform a clawback of the funds outside of the Escrow context. In other words, once the token amount returns to the issuer or source account, the existing clawback features for IOUs or MPTs can be used on those returned funds.

2. Issuer as Source: XLS-85 currently does not allow the issuer to be the source of the Escrow. If your use case requires this functionality, you should create a new account, send the MPT or IOU to that account, and then Escrow the token.
