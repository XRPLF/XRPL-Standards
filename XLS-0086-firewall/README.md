<pre>
  xls: 86
  title: Firewall
  description: Destination-based security through whitelisted recipients with counterparty authorization and rule-based safeguards
  author: Kris Dangerfield (@krisdangerfield), Denis Angell (@angell_denis)
  proposal-from: https://github.com/XRPLF/XRPL-Standards/discussions/255
  status: Draft
  category: Amendment
  created: 2024-11-29
  updated: 2025-09-19
</pre>

# Amendment XLS: Firewall

## Index

1. [Abstract](#1-abstract)
2. [Motivation](#2-motivation)
3. [Introduction](#3-introduction)
4. [Specification](#4-specification)
   - 4.1. [Ledger Entries](#41-ledger-entries)
   - 4.2. [Transactions](#42-transactions)
   - 4.3. [Firewall Check Implementation](#43-firewall-check-implementation)
   - 4.4. [Transaction Firewall Actions](#44-transaction-firewall-actions)
5. [Rationale](#5-rationale)
6. [Backwards Compatibility](#6-backwards-compatibility)
7. [Security Considerations](#7-security-considerations)
8. [Appendix](#8-appendix)

## 1. Abstract

This amendment introduces a comprehensive Firewall framework for the XRP Ledger, providing destination-based security through whitelisted recipients (WithdrawPreauth) with counterparty authorization. The system provides multi-layered protection through:

1. A whitelist that restricts outgoing payments to pre-approved recipients
2. A counterparty authorization system that adds an additional security layer, preventing single points of failure in account security
3. A transaction classification system that determines which transactions are subject to firewall checks
4. Fee drain protection that prevents account draining through excessive transaction fees

## 2. Motivation

The XRPL protocol currently lacks native mechanisms to prevent compromised accounts from being instantly drained. While multi-signature functionality exists, its complexity and limited wallet support have prevented widespread adoption.

Current security options are insufficient:

- Single-key accounts provide no protection against key compromise
- Multisig requires complex coordination and lacks widespread wallet support
- No native mechanism exists to restrict outgoing payments to trusted addresses
- Zero protection against malicious account draining
- No defense against fee-based drain attacks

This amendment addresses these gaps by providing:

- Simple whitelist-based protection accessible to all users
- Dual-control security without multisig complexity
- Protection against unauthorized withdrawal
- Transaction-level control over which operations require authorization
- Fee drain protection through maximum fee limits

## 3. Introduction

The Firewall system introduces a new security paradigm for the XRP Ledger based on destination whitelisting and fee protection. Once enabled, an account can only send value to pre-authorized recipients for transactions that are subject to firewall checks, and all transactions are subject to maximum fee limits.

### 3.1. Terminology

**Core Components:**

- **Firewall**: A ledger object that enables destination-based restrictions and fee limits on an account
- **Counterparty**: A trusted account that must co-sign changes to firewall settings
- **Backup**: A mandatory preauthorized account where assets can be sent without restriction, in the event of key compromise
- **MaxFee**: Optional maximum transaction fee limit to prevent fee-based drain attacks

**WithdrawPreauth Features:**

- **WithdrawPreauth**: Authorization for a specific account to receive assets from a firewall protected account
- **DestinationTag**: Optional tag that can be required for preauthorized transfers

**Transaction Control:**

- **FirewallAction**: Classification of how each transaction type interacts with the firewall (allow, check, or block)

### 3.2. Summary

**Ledger Objects:**

- `Firewall`: Stores the counterparty relationship, security configuration, and fee limits
- `WithdrawPreauth`: Represents authorization for specific recipients with optional destination tag

**Transactions:**

- `FirewallSet`: Creates or Updates a firewall configuration including fee limits (update requires counterparty approval)
- `FirewallDelete`: Removes a firewall (requires counterparty approval)
- `WithdrawPreauth`: Adds or removes authorized recipients with optional destination tags (requires counterparty approval)

## 4. Specification

### 4.1. Ledger Entries

#### 4.1.1. Firewall

##### 4.1.1.1. Object Identifier

**Key Space**: `0x0046` (hex representation)

The Firewall object ID is calculated as:

```
SHA512Half(KeySpace || AccountID)
```

Where:

- `KeySpace` = `0x0046`
- `AccountID` = The account that owns the firewall

##### 4.1.1.2. Fields

| Field Name        | Constant | Required | Internal Type | Default Value | Description                                                |
| ----------------- | -------- | -------- | ------------- | ------------- | ---------------------------------------------------------- |
| LedgerEntryType   | Yes      | Yes      | UINT16        | 0x0085        | Identifies this as a Firewall object                       |
| Flags             | No       | Yes      | UINT32        | 0             | Reserved for future use                                    |
| Owner             | Yes      | Yes      | ACCOUNT       | N/A           | Account that owns this firewall                            |
| Counterparty      | No       | Yes      | ACCOUNT       | N/A           | Account authorized to countersign firewall updates         |
| MaxFee            | No       | No       | AMOUNT        | N/A           | Maximum transaction fee allowed (in drops)                 |
| OwnerNode         | Yes      | Yes      | UINT64        | N/A           | Directory page storing this object                         |
| PreviousTxnID     | Yes      | Yes      | HASH256       | N/A           | Hash of the previous transaction that modified this object |
| PreviousTxnLgrSeq | Yes      | Yes      | UINT32        | N/A           | Ledger sequence of the previous transaction                |

##### 4.1.1.3. Ownership

The Firewall object is owned by the account specified in the `Owner` field and is linked in that account's OwnerDirectory.

##### 4.1.1.4. Reserves

Creating a Firewall increments the owner's reserve by one unit.

##### 4.1.1.5. Deletion

The Firewall can only be deleted via the FirewallDelete transaction when:

- The deletion transaction includes a valid counterparty signature
- This is a blocker for deleting the owner AccountRoot

##### 4.1.1.6. Example JSON

```json
{
  "LedgerEntryType": "Firewall",
  "Flags": 0,
  "Owner": "rU9XRmcZiJXp5J1LDJq8iZFujU6Wwn9cV9",
  "Counterparty": "raKG2uCwu71ohFGo1BJr7xqeGfWfYWZeh3",
  "MaxFee": "100000",
  "OwnerNode": "0000000000000000",
  "PreviousTxnID": "ABC123DEF456789ABC123DEF456789ABC123DEF456789ABC123DEF456789AB",
  "PreviousTxnLgrSeq": 1234567
}
```

#### 4.1.2. WithdrawPreauth

##### 4.1.2.1. Object Identifier

**Key Space**: `0x0047` (hex representation)

The WithdrawPreauth object ID is calculated as:

```
SHA512Half(KeySpace || OwnerAccountID || AuthorizedAccountID || DestinationTag)
```

##### 4.1.2.2. Fields

| Field Name        | Constant | Required | Internal Type | Default Value | Description                                 |
| ----------------- | -------- | -------- | ------------- | ------------- | ------------------------------------------- |
| LedgerEntryType   | Yes      | Yes      | UINT16        | 0x0856        | Identifies as WithdrawPreauth               |
| Flags             | No       | Yes      | UINT32        | 0             | Reserved for future use                     |
| Account           | Yes      | Yes      | ACCOUNT       | N/A           | Account that owns this preauth              |
| Authorize         | Yes      | Yes      | ACCOUNT       | N/A           | Account authorized to receive assets        |
| DestinationTag    | No       | No       | UINT32        | N/A           | Optional destination tag                    |
| OwnerNode         | Yes      | Yes      | UINT64        | N/A           | Directory page storing this                 |
| PreviousTxnID     | Yes      | Yes      | HASH256       | N/A           | Hash of the previous transaction            |
| PreviousTxnLgrSeq | Yes      | Yes      | UINT32        | N/A           | Ledger sequence of the previous transaction |

##### 4.1.2.3. Ownership

Owned by the `Account` field and linked in that account's OwnerDirectory.

##### 4.1.2.4. Reserves

Each WithdrawPreauth entry increments the owner's reserve by one unit.

##### 4.1.2.5. Deletion

Can be deleted via WithdrawPreauth transaction with counterparty signature.

##### 4.1.2.6. Example JSON

```json
{
  "LedgerEntryType": "WithdrawPreauth",
  "Flags": 0,
  "Account": "rU9XRmcZiJXp5J1LDJq8iZFujU6Wwn9cV9",
  "Authorize": "rVendorAddress123456789",
  "DestinationTag": 42,
  "OwnerNode": "0000000000000001",
  "PreviousTxnID": "DEF456789ABC123DEF456789ABC123DEF456789ABC123DEF456789ABC123DE",
  "PreviousTxnLgrSeq": 1234568
}
```

### 4.2. Transactions

#### 4.2.1. FirewallSet

##### 4.2.1.1. Fields

| Field Name            | Required?   | JSON Type | Internal Type | Default Value | Description                                 |
| --------------------- | ----------- | --------- | ------------- | ------------- | ------------------------------------------- |
| TransactionType       | Yes         | string    | BLOB          | N/A           | Value: "FirewallSet"                        |
| Counterparty          | Conditional | string    | ACCOUNT       | N/A           | Required for creation, Optional for updates |
| Backup                | Conditional | string    | ACCOUNT       | N/A           | Required for creation                       |
| MaxFee                | No          | string    | AMOUNT        | N/A           | Maximum transaction fee allowed (in drops)  |
| DestinationTag        | No          | number    | UINT32        | N/A           | Tag for backup preauth                      |
| FirewallID            | Conditional | string    | HASH256       | N/A           | Required for updates                        |
| CounterpartySignature | Conditional | array     | ARRAY         | N/A           | Required for updates                        |

**Conditional Requirements:**

- For creation: `Counterparty` and `Backup` are required, `FirewallID` and `CounterpartySignature` must be absent
- For updates: `FirewallID` and `CounterpartySignature` are required
- `MaxFee` can be set on creation or updated later (update requires counterparty approval)

##### 4.2.1.2. Failure Conditions

**For Creation (when sfFirewallID is absent):**

1. `temDISABLED`: Amendment not enabled
2. `temINVALID_FLAG`: Invalid transaction flags set
3. `temMALFORMED`: Missing sfCounterparty field
4. `temMALFORMED`: Missing sfBackup field
5. `temMALFORMED`: sfCounterparty same as Account
6. `temMALFORMED`: sfBackup same as Account
7. `temMALFORMED`: sfCounterpartySignature present (forbidden for creation)
8. `temMALFORMED`: Invalid MaxFee amount (if present)
9. `temMALFORMED`: Invalid fee amount
10. `tecDUPLICATE`: Firewall already exists for account
11. `tecNO_DST`: Counterparty account doesn't exist
12. `tecNO_DST`: Backup account doesn't exist
13. `tecINSUFFICIENT_RESERVE`: Insufficient XRP for reserve (needs 2 objects worth)
14. `tecDIR_FULL`: Owner directory full

**For Updates (when sfFirewallID is present):**

1. `temDISABLED`: Amendment not enabled
2. `temINVALID_FLAG`: Invalid transaction flags set
3. `temMALFORMED`: Missing sfCounterpartySignature field
4. `temMALFORMED`: Invalid MaxFee amount (if present)
5. `tecNO_DST`: New Counterparty account doesn't exist (if changing)
6. `tecDUPLICATE`: New Counterparty same as existing Counterparty
7. `temMALFORMED`: sfBackup present (forbidden for updates)
8. `temMALFORMED`: sfCounterparty same as Account
9. `temMALFORMED`: CounterpartySignature includes the outer Account
10. `temBAD_SIGNATURE`: Invalid counterparty signature in CounterpartySignature
11. `tecNO_TARGET`: Referenced firewall not found
12. `tecNO_PERMISSION`: Account not the firewall owner

##### 4.2.1.3. State Changes

**On Creation:**

1. Create Firewall ledger entry with specified Counterparty
2. Set MaxFee if provided
3. Create WithdrawPreauth entry for Backup account with optional DestinationTag
4. Increment owner's reserve count by 2
5. Add both objects to owner's directory
6. Prevent future master key disable

**On Update:**

1. Verify counterparty signature
2. Update Counterparty if specified
3. Update MaxFee if specified (or remove if set to 0)

##### 4.2.1.4. Example JSON

**Creation:**

```json
{
  "TransactionType": "FirewallSet",
  "Account": "rU9XRmcZiJXp5J1LDJq8iZFujU6Wwn9cV9",
  "Counterparty": "raKG2uCwu71ohFGo1BJr7xqeGfWfYWZeh3",
  "Backup": "rBackupAccount123456789",
  "MaxFee": "100000",
  "DestinationTag": 12345,
  "Fee": "36",
  "Sequence": 10
}
```

**Update:**

```json
{
  "TransactionType": "FirewallSet",
  "Account": "rU9XRmcZiJXp5J1LDJq8iZFujU6Wwn9cV9",
  "Counterparty": "rNewCounterparty123456",
  "MaxFee": "50000",
  "FirewallID": "ABC123DEF456789",
  "CounterpartySignature": {
    "SigningPubKey": "ED74D4036C6591A4BDF9C54CEFA39B996A5DCE5F86D11FDA1874481CE9D5A1CDC1",
    "TxnSignature": "C3646313B08EED6AF4392261A31B961F10C66CB733DB7F6CD9EAB079857834C8B0E1DDC877E39D96A18223B985D9F75DDD2D2AB5B2D0A26E8A87B6D0A716D607"
  },
  "Fee": "36",
  "Sequence": 11
}
```

#### 4.2.2. FirewallDelete

##### 4.2.2.1. Fields

| Field Name            | Required? | JSON Type | Internal Type | Default Value | Description             |
| --------------------- | --------- | --------- | ------------- | ------------- | ----------------------- |
| TransactionType       | Yes       | string    | BLOB          | N/A           | Value: "FirewallDelete" |
| FirewallID            | Yes       | string    | HASH256       | N/A           | Firewall to delete      |
| CounterpartySignature | Yes       | array     | ARRAY         | N/A           | Counterparty signatures |

##### 4.2.2.2. Failure Conditions

1. `temDISABLED`: Amendment not enabled
2. `temINVALID_FLAG`: Invalid transaction flags set
3. `temMALFORMED`: Missing sfFirewallID field
4. `temMALFORMED`: Missing sfCounterpartySignature field
5. `temMALFORMED`: CounterpartySignature includes the outer Account
6. `temBAD_SIGNATURE`: Invalid counterparty signature
7. `tecNO_TARGET`: Firewall doesn't exist
8. `tecNO_PERMISSION`: Account not the firewall owner

##### 4.2.2.3. State Changes

1. Remove all WithdrawPreauth entries for the account
2. Remove Firewall ledger entry
3. Remove from owner's directory
4. Decrement owner's reserve count

##### 4.2.2.4. Example JSON

```json
{
  "TransactionType": "FirewallDelete",
  "Account": "rU9XRmcZiJXp5J1LDJq8iZFujU6Wwn9cV9",
  "FirewallID": "ABC123DEF456789",
  "CounterpartySignature": {
    "SigningPubKey": "ED74D4036C6591A4BDF9C54CEFA39B996A5DCE5F86D11FDA1874481CE9D5A1CDC1",
    "TxnSignature": "C3646313B08EED6AF4392261A31B961F10C66CB733DB7F6CD9EAB079857834C8B0E1DDC877E39D96A18223B985D9F75DDD2D2AB5B2D0A26E8A87B6D0A716D607"
  },
  "Fee": "36",
  "Sequence": 10
}
```

#### 4.2.3. WithdrawPreauth

##### 4.2.3.1. Fields

| Field Name            | Required?   | JSON Type | Internal Type | Default Value | Description              |
| --------------------- | ----------- | --------- | ------------- | ------------- | ------------------------ |
| TransactionType       | Yes         | string    | BLOB          | N/A           | Value: "WithdrawPreauth" |
| Authorize             | Conditional | string    | ACCOUNT       | N/A           | Account to authorize     |
| Unauthorize           | Conditional | string    | ACCOUNT       | N/A           | Account to unauthorize   |
| DestinationTag        | No          | number    | UINT32        | N/A           | Optional destination tag |
| FirewallID            | Yes         | string    | HASH256       | N/A           | Associated firewall      |
| CounterpartySignature | Yes         | array     | ARRAY         | N/A           | Counterparty signatures  |

**Conditional Requirements:**

- Exactly one of `Authorize` or `Unauthorize` must be present

##### 4.2.3.2. Failure Conditions

1. `temDISABLED`: Amendment not enabled
2. `temINVALID_FLAG`: Invalid transaction flags set
3. `temMALFORMED`: Both sfAuthorize and sfUnauthorize present
4. `temMALFORMED`: Neither sfAuthorize nor sfUnauthorize present
5. `temMALFORMED`: Missing sfFirewallID field
6. `temMALFORMED`: Missing sfCounterpartySignature field
7. `temMALFORMED`: CounterpartySignature includes the outer Account
8. `temINVALID_ACCOUNT_ID`: Zero account in Authorize/Unauthorize field
9. `temCANNOT_PREAUTH_SELF`: Attempting to authorize own account
10. `temBAD_SIGNATURE`: Invalid counterparty signature
11. `tecNO_TARGET`: Firewall doesn't exist
12. `tecNO_TARGET`: Authorize account doesn't exist (for authorize operation)
13. `tecDUPLICATE`: Preauth already exists (for authorize operation)
14. `tecNO_ENTRY`: Preauth doesn't exist (for unauthorize operation)
15. `tecNO_PERMISSION`: Account not the firewall owner
16. `tecINSUFFICIENT_RESERVE`: Insufficient reserve (for authorize operation)
17. `tecDIR_FULL`: Owner directory full (for authorize operation)

##### 4.2.3.3. State Changes

**On Authorize:**

1. Verify counterparty signature
2. Create WithdrawPreauth entry with optional DestinationTag
3. Add to owner's directory
4. Increment owner's reserve count

**On Unauthorize:**

1. Verify counterparty signature
2. Remove WithdrawPreauth entry
3. Remove from owner's directory
4. Decrement owner's reserve count

##### 4.2.3.4. Example JSON

```json
{
  "TransactionType": "WithdrawPreauth",
  "Account": "rU9XRmcZiJXp5J1LDJq8iZFujU6Wwn9cV9",
  "Authorize": "rNewVendorAddress123456",
  "DestinationTag": 555,
  "FirewallID": "ABC123DEF456789",
  "CounterpartySignature": {
    "SigningPubKey": "ED74D4036C6591A4BDF9C54CEFA39B996A5DCE5F86D11FDA1874481CE9D5A1CDC1",
    "TxnSignature": "C3646313B08EED6AF4392261A31B961F10C66CB733DB7F6CD9EAB079857834C8B0E1DDC877E39D96A18223B985D9F75DDD2D2AB5B2D0A26E8A87B6D0A716D607"
  },
  "Fee": "36",
  "Sequence": 11
}
```

### 4.3. Firewall Check Implementation

The firewall system integrates into the transaction processing pipeline through a preclaim check that validates transactions against the firewall configuration before they are applied.

#### 4.3.1. Architecture

The firewall check is implemented in the `Transactor::checkFirewall` method which is called during the preclaim phase of transaction processing.

#### 4.3.2. Check Flow

```cpp
NotTEC
Transactor::checkFirewall(PreclaimContext const& ctx)
{
    // Get the account (handle delegation)
    auto const account = ctx.tx.isFieldPresent(sfDelegate)
        ? ctx.tx.getAccountID(sfDelegate)
        : ctx.tx.getAccountID(sfAccount);

    // Check if firewall exists
    auto const sleFirewall = ctx.view.read(keylet::firewall(account));
    if (!sleFirewall)
        return tesSUCCESS;  // No firewall, proceed normally

    // Check fee limit if MaxFee is set (most efficient check first)
    if (sleFirewall.isFieldPresent(sfMaxFee) &&
        ctx.tx.getFieldAmount(sfFee) > sleFirewall.getFieldAmount(sfMaxFee))
        return tefFIREWALL_BLOCK;  // Fee exceeds maximum allowed

    // Check transaction classification
    auto const txType = ctx.tx.getFieldU16(sfTransactionType);

    if (Firewall::getInstance().isAllowed(txType))
        return tesSUCCESS;  // Transaction type is allowed

    if (Firewall::getInstance().isBlocked(txType))
        return tefFIREWALL_BLOCK;  // Transaction type is blocked

    // Transaction requires check
    // Special handling for Payment transactions
    if (ctx.tx.getTxnType() == ttPAYMENT)
    {
        // Block self-payments and payments with paths
        if (ctx.tx.getAccountID(sfDestination) == account ||
            ctx.tx.isFieldPresent(sfPaths))
            return tefFIREWALL_BLOCK;
    }

    // Verify destination is present
    if (!ctx.tx.isFieldPresent(sfDestination))
        return tefFIREWALL_BLOCK;

    // Check WithdrawPreauth
    auto const destination = ctx.tx.getAccountID(sfDestination);
    auto const destinationTag = ctx.tx.isFieldPresent(sfDestinationTag)
        ? ctx.tx.getFieldU32(sfDestinationTag)
        : 0;

    if (!ctx.view.exists(keylet::withdrawPreauth(account, destination, destinationTag)))
        return tefFIREWALL_BLOCK;

    return tesSUCCESS;
}
```

#### 4.3.3. Integration Points

The `checkFirewall` function is called in the transaction processing pipeline:

1. After signature validation (`checkSign`)
2. Before the transaction-specific preclaim checks
3. Returns `tefFIREWALL_BLOCK` if the transaction violates firewall rules or exceeds fee limits

### 4.4. Transaction Firewall Actions

Each transaction type is classified with a `FirewallAction` enum value that determines how it interacts with the firewall system:

```cpp
enum FirewallAction { check, allow, block };
```

The classification is embedded in the transaction definition macro system:

| Transaction Type            | FirewallAction | Rationale                                          |
| --------------------------- | -------------- | -------------------------------------------------- |
| **Payment**                 | check          | Must validate destination is preauthorized         |
| **EscrowCreate**            | check          | Creates future payment obligation                  |
| **EscrowFinish**            | check          | Releases funds to destination                      |
| **EscrowCancel**            | check          | Returns funds (may have different destination)     |
| **AccountSet**              | allow          | Only modifies account settings                     |
| **SetRegularKey**           | allow          | Key management (requires counterparty for changes) |
| **OfferCreate**             | block          | Could result in uncontrolled asset exchange        |
| **OfferCancel**             | allow          | Only cancels existing offers                       |
| **TicketCreate**            | allow          | Only reserves sequence numbers                     |
| **SignerListSet**           | allow          | Signer management (requires counterparty)          |
| **PaymentChannelCreate**    | check          | Creates payment channel to destination             |
| **PaymentChannelFund**      | block          | Adds funds to existing channel                     |
| **PaymentChannelClaim**     | allow          | Claims from existing channel                       |
| **CheckCreate**             | check          | Creates check for destination                      |
| **CheckCash**               | allow          | Cashes existing check                              |
| **CheckCancel**             | allow          | Cancels existing check                             |
| **DepositPreauth**          | allow          | Manages incoming payment authorization             |
| **TrustSet**                | allow          | Trust line management                              |
| **AccountDelete**           | allow          | Account deletion (significant action)              |
| **NFTokenMint**             | check          | May have destination                               |
| **NFTokenBurn**             | allow          | Destroys token                                     |
| **NFTokenCreateOffer**      | check          | Creates offer with potential destination           |
| **NFTokenCancelOffer**      | allow          | Cancels existing offer                             |
| **NFTokenAcceptOffer**      | allow          | Accepts existing offer                             |
| **Clawback**                | allow          | Issuer right (cannot be blocked)                   |
| **AMMClawback**             | allow          | Issuer right for AMM                               |
| **AMMCreate**               | block          | Creates AMM with uncontrolled trading              |
| **AMMDeposit**              | block          | Adds liquidity to AMM                              |
| **AMMWithdraw**             | block          | Removes liquidity from AMM                         |
| **AMMVote**                 | block          | Participates in AMM governance                     |
| **AMMBid**                  | block          | Bids for AMM auction slot                          |
| **AMMDelete**               | block          | Deletes empty AMM                                  |
| **XChain\*** (all)          | block          | Cross-chain operations too complex to validate     |
| **DIDSet/Delete**           | allow          | DID management                                     |
| **OracleSet/Delete**        | allow          | Oracle management                                  |
| **LedgerStateFix**          | allow          | System operation                                   |
| **MPTokenIssuance\***       | allow          | Token issuance management                          |
| **MPTokenAuthorize**        | allow          | Token authorization                                |
| **Credential\***            | allow          | Credential management                              |
| **NFTokenModify**           | allow          | Modifies existing NFT                              |
| **PermissionedDomain\***    | allow          | Domain management                                  |
| **DelegateSet**             | allow          | Delegation management                              |
| **VaultCreate/Set/Delete**  | block          | Vault management                                   |
| **VaultDeposit**            | block          | Adds assets to vault                               |
| **VaultWithdraw**           | block          | Withdraws to destination                           |
| **VaultClawback**           | block          | Issuer right                                       |
| **Batch**                   | allow          | Batch processing (individual txns checked)         |
| **WithdrawPreauth**         | allow          | Firewall preauth management                        |
| **FirewallSet/Delete**      | allow          | Firewall management                                |
| **Amendment/Fee/UNLModify** | allow          | System transactions                                |

## 5. Rationale

**Simplified Architecture**: The removal of the complex rule system and post-application checking in favor of preclaim validation significantly reduces implementation complexity while maintaining security guarantees. The invariant-style checker pattern was eliminated because:

- Preclaim checking is more efficient
- Simpler to reason about and audit
- Prevents wasted computation on invalid transactions

**Fee Drain Protection**: The MaxFee field provides critical protection against fee-based drain attacks where a compromised key could execute many high-fee transactions to drain an account. This feature:

- Prevents rapid draining through excessive fees
- Is configurable based on user needs
- Requires counterparty approval to change
- Applies uniformly to all transactions
- Is checked first for maximum efficiency

**Transaction Classification**: The three-tier classification system (allow/check/block) provides clear semantics for how each transaction type interacts with the firewall:

- **allow**: Transaction poses no risk of unauthorized value transfer
- **check**: Transaction may transfer value and requires destination validation
- **block**: Transaction involves complex operations that could bypass simple checks

**Preclaim Validation**: Checking firewall constraints during the preclaim phase:

- Prevents invalid transactions from consuming computational resources
- Provides clear, early feedback on transaction validity
- Integrates cleanly with existing validation pipeline

**Whitelist Model**: Chosen over blacklist as it's more secure by default - new threats are automatically blocked rather than requiring updates to block them.

**Counterparty System**: Provides a second layer of security for firewall changes, preventing single points of failure. Even with master key compromise, an attacker cannot disable protections.

**Enforced Backup Account**: Ensures users cannot lock themselves out during initial setup, addressing common security configuration errors.

**Destination Tag Support**: Allows fine-grained control over authorized destinations, supporting exchange accounts and service providers that require specific tags.

**Path Payment Blocking**: Payments with paths are blocked because path-finding could route through intermediate accounts, making destination validation complex and potentially bypassable.

**Self-Payment Blocking**: Self-payments are blocked to prevent potential bypass scenarios and maintain consistent security semantics.

**AMM and Cross-Chain Blocking**: These complex multi-party operations are blocked entirely rather than attempting partial validation that could miss edge cases.

## 6. Backwards Compatibility

This amendment introduces no backwards incompatibilities:

- Accounts without firewalls continue operating normally
- All existing transaction types remain functional
- The feature is entirely opt-in
- No changes to existing ledger entries or transaction formats
- Existing destination tag functionality is preserved and enhanced
- Delegated transactions are properly handled
- Fee limits are optional and do not affect accounts without firewalls

## 7. Security Considerations

### 7.1. Key Compromise Protection

Even with full key compromise, attackers cannot:

- Send assets to unauthorized addresses
- Disable the firewall without counterparty approval
- Add or remove existing preauthorizations without counterparty approval
- Exceed the maximum fee limit set on the firewall
- Disable master key while firewall is active
- Set a new regular key or signers list without counterparty approval
- Bypass destination tag requirements
- Use complex transactions (AMM, cross-chain) to bypass restrictions
- Drain the account through excessive transaction fees

Attackers can only:

- Send assets to already-authorized addresses with matching tags
- Perform allowed account management operations within fee limits
- Cancel existing obligations
- Submit transactions with fees up to the MaxFee limit

### 7.2. Counterparty Risk

A compromised counterparty cannot change anything alone. Both master key and counterparty signatures are required for:

- Adding/removing preauthorizations
- Changing counterparty
- Modifying fee limits
- Deleting firewall

Mitigation: Choose counterparty carefully, consider using a second account you control with separated key hygiene.

### 7.3. Denial of Service

A malicious counterparty cannot:

- Prevent transfers to already-authorized addresses
- Lock the account permanently
- Delete the firewall unilaterally
- Change firewall settings unilaterally
- Modify destination tag requirements without authorization
- Change fee limits without authorization

The worst a malicious counterparty can do is refuse to sign legitimate changes, preventing new authorizations or fee limit adjustments.

### 7.4. Transaction Type Coverage

The transaction classification system ensures:

- Value-transferring transactions are appropriately restricted
- Account management operations remain available
- Complex transactions that could bypass simple checks are blocked
- Cancellation and cleanup operations are generally allowed
- Issuer rights (clawback) cannot be blocked
- All transactions respect fee limits when set

### 7.5. Fee Drain Attack Prevention

The MaxFee protection prevents several attack vectors:

**Attack Scenarios Prevented:**

1. **Rapid small-fee drain**: Attacker submits thousands of minimum-value transactions with maximum fees
2. **Network congestion exploit**: Attacker uses high fees during network congestion to accelerate draining
3. **Failed transaction drain**: Attacker submits deliberately failing transactions with high fees
4. **Batch fee attacks**: Multiple high-fee transactions submitted simultaneously

**Protection Characteristics:**

- Fee limit applies to ALL transactions from the protected account
- Cannot be bypassed even with valid destinations
- Cannot be changed without counterparty approval
- Provides predictable maximum loss rate
- Checked before any other validation for efficiency

**Recommended Settings:**

- Regular users: 10,000-100,000 drops (0.01-0.1 XRP)
- High-volume users: 1,000,000 drops (1 XRP)
- Payment processors: 5,000,000 drops (5 XRP)
- During network congestion: Temporary increase with counterparty approval

### 7.6. Implementation Security

- Preclaim checking prevents resource exhaustion attacks
- Clear error codes (`tefFIREWALL_BLOCK`) for debugging
- No complex state tracking or accumulation
- Deterministic validation across all validators
- No external dependencies or oracle requirements
- Fee checks occur first to minimize computation on invalid transactions

## 8. Appendix

### 8.1. FAQ

**Q: Can incoming payments be blocked?**
A: No, this system only restricts outgoing payments. Incoming payments are always allowed.

**Q: What if my counterparty becomes unavailable?**
A: Existing preauthorized addresses continue working. You cannot add new ones or change fee limits without counterparty cooperation.

**Q: Can I remove the firewall?**
A: Yes, with counterparty approval using FirewallDelete transaction. All WithdrawPreauth entries are automatically removed.

**Q: How many addresses can I preauthorize?**
A: Limited only by reserve requirements and directory size limits.

**Q: Can I use destination tags with the firewall?**
A: Yes, WithdrawPreauth entries can specify required destination tags, providing fine-grained control over authorized destinations.

**Q: What happens if network fees exceed my MaxFee limit?**
A: All transactions will be blocked until you increase the limit with counterparty approval. Plan for network congestion by setting reasonable buffers.

**Q: Can I remove the fee limit after setting it?**
A: Yes, set MaxFee to 0 or omit it in an update transaction (requires counterparty signature).

**Q: What's a reasonable MaxFee setting?**
A: For most users, 100,000 drops (0.1 XRP) provides good protection while allowing for moderate network congestion. High-volume users may need 1,000,000 drops (1 XRP).

**Q: Does MaxFee affect incoming transactions?**
A: No, it only limits fees on outgoing transactions from your account.

**Q: Can different transaction types have different fee limits?**
A: No, MaxFee applies uniformly to all transactions. For granular control, use separate accounts.

**Q: Why are AMM operations blocked?**
A: AMM operations involve complex multi-party trading that could potentially bypass simple destination checks. They are blocked entirely for security.

**Q: Can complex DEX trades bypass the firewall?**
A: No, OfferCreate is blocked entirely to prevent any DEX trading that could result in unauthorized asset transfers.

**Q: Can I use my own account as counterparty?**
A: Yes, but it must be a different account than the one being protected. This provides security through key separation.

**Q: What happens to existing Escrows or Payment Channels?**
A: Existing obligations created before firewall activation continue to function. The firewall only affects new transactions.

**Q: Why are path payments blocked?**
A: Path payments can route through multiple intermediate accounts, making destination validation complex and potentially bypassable.

**Q: Can I pay myself with a firewall enabled?**
A: No, self-payments are blocked to maintain consistent security semantics and prevent potential bypass scenarios.

**Q: What's the difference between check, allow, and block?**
A:

- **allow**: Transaction proceeds without firewall checks
- **check**: Transaction must have an authorized destination
- **block**: Transaction is always rejected if firewall is active

**Q: Are batch transactions affected?**
A: The Batch transaction itself is allowed, but each inner transaction is evaluated according to its own FirewallAction classification.

**Q: Can I still use regular keys with a firewall?**
A: Yes, but changes to regular keys require counterparty approval once a firewall is active.

**Q: What if my counterparty is unavailable during network congestion?**
A: You cannot increase the fee limit without counterparty approval. This is by design - security over convenience. Maintain appropriate buffers.

**Q: Are reserve fees affected by MaxFee?**
A: No, MaxFee only applies to transaction fees, not reserve requirements.

**Q: Can I set MaxFee without setting up full firewall protection?**
A: No, MaxFee is part of the Firewall object. You must enable the full firewall system.

### 8.3. Reference Implementation

The reference implementation will be provided as a pull request to the rippled repository upon advancement to Final status.
