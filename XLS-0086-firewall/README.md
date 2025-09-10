<pre>
  xls: 86
  title: Firewall
  description: Destination-based security through whitelisted recipients with counterparty authorization and rule-based safeguards
  author: Kris Dangerfield (@krisdangerfield), Denis Angell (@angell_denis)
  discussion-from: https://github.com/XRPLF/XRPL-Standards/discussions/255
  status: Draft
  category: Amendment
  created: 2024-11-29
  updated: 2025-09-04
</pre>

# Amendment XLS: Firewall

## Index

1. [Abstract](#1-abstract)
2. [Motivation](#2-motivation)
3. [Introduction](#3-introduction)
4. [Specification](#4-specification)
   - 4.1. [Field Types](#41-field-types)
   - 4.2. [Ledger Entries](#42-ledger-entries)
   - 4.3. [Transactions](#43-transactions)
   - 4.4. [Firewall Check Implementation](#44-firewall-check-implementation)
   - 4.5. [Firewall Macro System](#45-firewall-macro-system)
5. [Rationale](#5-rationale)
6. [Backwards Compatibility](#6-backwards-compatibility)
7. [Security Considerations](#7-security-considerations)
8. [Appendix](#8-appendix)

## 1. Abstract

This amendment introduces a comprehensive Firewall framework for the XRP Ledger, combining destination-based security through whitelisted recipients (WithdrawPreauth) with configurable rule-based safeguards.
The system provides multi-layered protection through:

1. A whitelist that restricts outgoing payments to pre-approved recipients
2. A counterparty authorization system adds an additional security layer, preventing single points of failure in account security
3. Configurable rules that enforce field-specific limits, time-based restrictions, and complex conditional logic
4. A flexible STData type for storing comparison values and a post-application checker pattern to validate all balance changes

## 2. Motivation

The XRPL protocol currently lacks native mechanisms to prevent compromised accounts from being instantly drained and sophisticated security policies. While multi-signature functionality exists, its complexity and limited wallet support have prevented widespread adoption.

Current security options are insufficient:

**Basic Security Gaps:**

- Single-key accounts provide no protection against key compromise
- Multisig requires complex coordination and lacks widespread wallet support
- No native mechanism exists to restrict outgoing payments to trusted addresses

**Advanced Security Gaps:**

- No mechanism for rate limiting or amount restrictions beyond destination control
- Inability to enforce time-based security policies
- No support for field-specific monitoring of ledger changes
- Zero protection against malicious account draining via fees

This amendment addresses these gaps by providing:

**Foundation Features:**

- Simple whitelist-based protection accessible to all users
- Dual-control security without multisig complexity
- Protection against unauthorized withdrawl

**Advanced Features:**

- Flexible rule engine supporting multiple comparison operators
- Time-based accumulation tracking for rate limiting
- Field-specific monitoring across different ledger entry types
- STData type for storing heterogeneous comparison values

## 3. Introduction

The Firewall system introduces a new security paradigm for the XRP Ledger based on both destination whitelisting and configurable rules. Once enabled, an account can only send assets to pre-authorized recipients and must comply with user-defined rules.

### 3.1. Terminology

**Core Components:**

- **Firewall**: A ledger object that enables destination-based restrictions and rules on an account
- **Counterparty**: A trusted account that must co-sign changes to firewall settings
- **Backup**: A mandatory preauthorized account where assets can be sent without restriction, in the event of key compromise

**WithdrawPreauth Features:**

- **WithdrawPreauth**: Authorization for a specific account to receive assets from a firewall protected account
- **DestinationTag**: Optional tag that can be required for preauthorized transfers

**Rule Features:**

- **Firewall Rule**: A condition that monitors specific ledger entry fields
- **STData**: Flexible container type for storing comparison values of different types
- **Comparison Operator**: Mathematical operator used in rule evaluation (<, ≤, =, ≥, >)
- **Time Period**: Duration for accumulating values in time-based rules
- **Field Code**: Numeric identifier for a specific ledger entry field

### 3.2. Summary

**Field Types:**

- `STData`: Flexible container for heterogeneous value storage

**Ledger Objects:**

- `Firewall`: Stores the counterparty relationship, security configuration, and rules
- `WithdrawPreauth`: Represents authorization for specific recipients with optional destination tag

**Transactions:**

- `FirewallSet`: Creates or Updates a firewall configuration including rules (update requires counterparty approval)
- `FirewallDelete`: Removes a firewall (requires counterparty approval)
- `WithdrawPreauth`: Adds or removes authorized recipients with optional destination tags (requires counterparty approval)

## 4. Specification

### 4.1. Field Types

#### 4.1.1. STData

A flexible container type that can hold various serialized types within a single field.

##### 4.1.1.1. Supported Inner Types

- `UINT8`, `UINT16`, `UINT32`, `UINT64`
- `UINT128`, `UINT160`, `UINT192`, `UINT256`
- `VL` (Variable Length data)
- `AMOUNT`
- `ACCOUNT`
- `ISSUE`
- `CURRENCY`

##### 4.1.1.2. Serialization Format

The STData type serializes as:

1. 16-bit type identifier
2. Serialized inner value according to its type

##### 4.1.1.3. JSON Representation

```json
{
  "type": "AMOUNT",
  "value": "10000000"
}
```

### 4.2. Ledger Entries

#### 4.2.1. Firewall

##### 4.2.1.1. Object Identifier

**Key Space**: `0x0046` (hex representation)

The Firewall object ID is calculated as:

```
SHA512Half(KeySpace || AccountID)
```

Where:

- `KeySpace` = `0x0046`
- `AccountID` = The account that owns the firewall

##### 4.2.1.2. Fields

| Field Name      | Constant | Required | Internal Type | Default Value | Description                                        |
| --------------- | -------- | -------- | ------------- | ------------- | -------------------------------------------------- |
| LedgerEntryType | Yes      | Yes      | UINT16        | 0x0085        | Identifies this as a Firewall object               |
| Flags           | No       | Yes      | UINT32        | 0             | Reserved for future use                            |
| Owner           | Yes      | Yes      | ACCOUNT       | N/A           | Account that owns this firewall                    |
| Counterparty    | No       | Yes      | ACCOUNT       | N/A           | Account authorized to countersign firewall updates |
| FirewallRules   | No       | No       | ARRAY         | Empty         | Array of firewall rules                            |
| OwnerNode       | Yes      | Yes      | UINT64        | N/A           | Directory page storing this object                 |

##### 4.2.1.3. FirewallRule Object

Each rule in the FirewallRules array contains:

| Field Name         | Constant | Required | Internal Type | Default Value | Description                     |
| ------------------ | -------- | -------- | ------------- | ------------- | ------------------------------- |
| LedgerEntryType    | Yes      | Yes      | UINT16        | N/A           | Type of ledger entry to monitor |
| FieldCode          | Yes      | Yes      | UINT32        | N/A           | Field code being monitored      |
| ComparisonOperator | Yes      | Yes      | UINT16        | N/A           | Comparison operator (1-5)       |
| FirewallValue      | Yes      | Yes      | DATA          | N/A           | Value to compare against        |
| TimePeriod         | No       | No       | UINT32        | N/A           | Time period in seconds          |
| TimeStart          | No       | No       | UINT32        | N/A           | Start time of current period    |
| TimeValue          | No       | No       | DATA          | N/A           | Accumulated value in period     |

##### 4.2.1.4. Comparison Operators

| Value | Operator              | Symbol |
| ----- | --------------------- | ------ |
| 1     | Less Than             | <      |
| 2     | Less Than or Equal    | ≤      |
| 3     | Equal                 | =      |
| 4     | Greater Than or Equal | ≥      |
| 5     | Greater Than          | >      |

##### 4.2.1.5. Ownership

The Firewall object is owned by the account specified in the `Owner` field and is linked in that account's OwnerDirectory.

##### 4.2.1.6. Reserves

Creating a Firewall increments the owner's reserve by one unit.

##### 4.2.1.7. Deletion

The Firewall can only be deleted via the FirewallDelete transaction when:

- The deletion transaction includes a valid counterparty signature
- This is a blocker for deleting the owner AccountRoot

##### 4.2.1.8. Example JSON

```json
{
  "LedgerEntryType": "Firewall",
  "Flags": 0,
  "Owner": "rU9XRmcZiJXp5J1LDJq8iZFujU6Wwn9cV9",
  "Counterparty": "raKG2uCwu71ohFGo1BJr7xqeGfWfYWZeh3",
  "FirewallRules": [
    {
      "FirewallRule": {
        "LedgerEntryType": 97,
        "FieldCode": 6,
        "ComparisonOperator": 5,
        "FirewallValue": {
          "type": "AMOUNT",
          "value": "100000000"
        },
        "TimePeriod": 86400,
        "TimeStart": 1737000000,
        "TimeValue": {
          "type": "AMOUNT",
          "value": "5000000"
        }
      }
    }
  ],
  "OwnerNode": "0000000000000000"
}
```

#### 4.2.2. WithdrawPreauth

##### 4.2.2.1. Object Identifier

**Key Space**: `0x0047` (hex representation)

The WithdrawPreauth object ID is calculated as:

```
SHA512Half(KeySpace || OwnerAccountID || AuthorizedAccountID || DestinationTag)
```

##### 4.2.2.2. Fields

| Field Name      | Constant | Required | Internal Type | Default Value | Description                          |
| --------------- | -------- | -------- | ------------- | ------------- | ------------------------------------ |
| LedgerEntryType | Yes      | Yes      | UINT16        | 0x0856        | Identifies as WithdrawPreauth        |
| Flags           | No       | Yes      | UINT32        | 0             | Reserved for future use              |
| Account         | Yes      | Yes      | ACCOUNT       | N/A           | Account that owns this preauth       |
| Authorize       | Yes      | Yes      | ACCOUNT       | N/A           | Account authorized to receive assets |
| DestinationTag  | No       | No       | UINT32        | N/A           | Optional destination tag             |
| OwnerNode       | Yes      | Yes      | UINT64        | N/A           | Directory page storing this          |

##### 4.2.2.3. Ownership

Owned by the `Account` field and linked in that account's OwnerDirectory.

##### 4.2.2.4. Reserves

Each WithdrawPreauth entry increments the owner's reserve by one unit.

##### 4.2.2.5. Deletion

Can be deleted via WithdrawPreauth transaction with counterparty signature.

##### 4.2.2.6. Example JSON

```json
{
  "LedgerEntryType": "WithdrawPreauth",
  "Flags": 0,
  "Account": "rU9XRmcZiJXp5J1LDJq8iZFujU6Wwn9cV9",
  "Authorize": "rVendorAddress123456789",
  "DestinationTag": 42,
  "OwnerNode": "0000000000000001"
}
```

### 4.3. Transactions

#### 4.3.1. FirewallSet

##### 4.3.1.1. Fields

| Field Name            | Required?   | JSON Type | Internal Type | Default Value | Description                                 |
| --------------------- | ----------- | --------- | ------------- | ------------- | ------------------------------------------- |
| TransactionType       | Yes         | string    | BLOB          | N/A           | Value: "FirewallSet"                        |
| Counterparty          | Conditional | string    | ACCOUNT       | N/A           | Required for creation, Optional for updates |
| Backup                | Conditional | string    | ACCOUNT       | N/A           | Required for creation                       |
| DestinationTag        | No          | number    | UINT32        | N/A           | Tag for backup preauth                      |
| FirewallID            | Conditional | string    | HASH256       | N/A           | Required for updates                        |
| CounterpartySignature | Conditional | array     | ARRAY         | N/A           | Required for updates                        |
| FirewallRules         | No          | array     | ARRAY         | N/A           | Array of firewall rules                     |

**Conditional Requirements:**

- For creation: `Counterparty` and `Backup` are required, `FirewallID` and `CounterpartySignature` must be absent
- For updates: `FirewallID` and `CounterpartySignature` are required

##### 4.3.1.2. Rule Validation

**For Creation and Updates:**

- Rules array must not be empty if present
- Maximum 8 rules allowed
- Each rule must specify valid:
  - LedgerEntryType (must be supported)
  - FieldCode (must be valid for the ledger type)
  - ComparisonOperator (must be 1-5)
  - FirewallValue (must match field type)

##### 4.3.1.3. Failure Conditions

**For Creation (when sfFirewallID is absent):**

1. `temDISABLED`: Amendment not enabled
2. `temINVALID_FLAG`: Invalid transaction flags set
3. `temMALFORMED`: Missing sfCounterparty field
4. `temMALFORMED`: Missing sfBackup field
5. `temMALFORMED`: sfCounterparty same as Account
6. `temMALFORMED`: sfBackup same as Account
7. `temMALFORMED`: sfCounterpartySignature present (forbidden for creation)
8. `temBAD_FEE`: Invalid fee amount
9. `tecDUPLICATE`: Firewall already exists for account
10. `tecNO_DST`: Counterparty account doesn't exist
11. `tecNO_DST`: Backup account doesn't exist
12. `tecINSUFFICIENT_RESERVE`: Insufficient XRP for reserve (needs 2 objects worth)
13. `tecDIR_FULL`: Owner directory full

**For Updates (when sfFirewallID is present):**

1. `temDISABLED`: Amendment not enabled
2. `temINVALID_FLAG`: Invalid transaction flags set
3. `temMALFORMED`: Missing sfCounterpartySignature field
4. `tecNO_DST`: New Counterparty account doesn't exist (if changing)
5. `tecDUPLICATE`: New Counterparty same as existing Counterparty
6. `temMALFORMED`: sfBackup present (forbidden for updates)
7. `temMALFORMED`: sfCounterparty same as Account
8. `temMALFORMED`: CounterpartySignature includes the outer Account
9. `temBAD_SIGNATURE`: Invalid counterparty signature in CounterpartySignature
10. `tecNO_TARGET`: Referenced firewall not found
11. `tecNO_PERMISSION`: Account not the firewall owner

**Additional for Rules:**

13. `temMALFORMED`: Empty FirewallRules array
14. `temMALFORMED`: More than 8 rules
15. `temMALFORMED`: Unsupported LedgerEntryType
16. `temMALFORMED`: Invalid FieldCode for LedgerEntryType
17. `temMALFORMED`: Invalid ComparisonOperator

##### 4.3.1.4. State Changes

**On Creation:**

1. Create Firewall ledger entry with specified Counterparty
2. Create WithdrawPreauth entry for Backup account with optional DestinationTag
3. Increment owner's reserve count by 2
4. Add both objects to owner's directory
5. Prevent future master key disable

**On Update:**

1. Verify counterparty signature
2. Update Counterparty if specified

**On Rule Creation/Update:**

1. Validate all rules according to specifications
2. Store rules in Firewall object
3. Initialize TimeStart to 0 for time-based rules
4. Initialize TimeValue to zero for time-based rules

##### 4.3.1.5. Example JSON

```json
{
  "TransactionType": "FirewallSet",
  "Account": "rU9XRmcZiJXp5J1LDJq8iZFujU6Wwn9cV9",
  "Counterparty": "raKG2uCwu71ohFGo1BJr7xqeGfWfYWZeh3",
  "Backup": "rBackupAccount123456789",
  "DestinationTag": 12345,
  "FirewallRules": [
    {
      "FirewallRule": {
        "LedgerEntryType": 97,
        "FieldCode": 6,
        "ComparisonOperator": 5,
        "FirewallValue": {
          "type": "AMOUNT",
          "value": "100000000"
        },
        "TimePeriod": 86400
      }
    }
  ],
  "Fee": "36",
  "Sequence": 10
}
```

#### 4.3.2. FirewallDelete

##### 4.3.2.1. Fields

| Field Name            | Required? | JSON Type | Internal Type | Default Value | Description             |
| --------------------- | --------- | --------- | ------------- | ------------- | ----------------------- |
| TransactionType       | Yes       | string    | BLOB          | N/A           | Value: "FirewallDelete" |
| FirewallID            | Yes       | string    | HASH256       | N/A           | Firewall to delete      |
| CounterpartySignature | Yes       | array     | ARRAY         | N/A           | Counterparty signatures |

##### 4.3.2.2. Failure Conditions

1. `temDISABLED`: Amendment not enabled
2. `temINVALID_FLAG`: Invalid transaction flags set
3. `temMALFORMED`: Missing sfFirewallID field
4. `temMALFORMED`: Missing sfCounterpartySignature field
5. `temMALFORMED`: CounterpartySignature includes the outer Account
6. `temBAD_SIGNATURE`: Invalid counterparty signature
7. `tecNO_TARGET`: Firewall doesn't exist
8. `tecNO_PERMISSION`: Account not the firewall owner

##### 4.3.2.3. State Changes

1. Remove all WithdrawPreauth entries for the account
2. Remove Firewall ledger entry
3. Remove from owner's directory
4. Decrement owner's reserve count

##### 4.3.2.4. Example JSON

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

#### 4.3.3. WithdrawPreauth

##### 4.3.3.1. Fields

| Field Name            | Required?   | JSON Type | Internal Type | Default Value | Description              |
| --------------------- | ----------- | --------- | ------------- | ------------- | ------------------------ |
| TransactionType       | Yes         | string    | BLOB          | N/A           | Value: "WithdrawPreauth" |
| Authorize             | Conditional | string    | ACCOUNT       | N/A           | Account to authorize     |
| Unauthorize           | Conditional | string    | ACCOUNT       | N/A           | Account to unauthorize   |
| DestinationTag        | No          | number    | UINT32        | N/A           | Optional destination tag |
| FirewallID            | Yes         | string    | HASH256       | N/A           | Associated firewall      |
| CounterpartySignature | Yes         | object    | OBJECT        | N/A           | Counterparty signatures  |

**Conditional Requirements:**

- Exactly one of `Authorize` or `Unauthorize` must be present

##### 4.3.3.2. Failure Conditions

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

##### 4.3.3.3. State Changes

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

##### 4.3.3.4. Example JSON

```json
{
  "TransactionType": "WithdrawPreauth",
  "Account": "rU9XRmcZiJXp5J1LDJq8iZFujU6Wwn9cV9",
  "Authorize": "rNewVendorAddress123456",
  "DestinationTag": 555,
  "FirewallID": "ABC123DEF456789",
  "CounterpartySignature": {
    "SigningPubKey": "ED74D4036C6591A4BDF9C54CEFA39B996A5DCE5F86D11FDA1874481CE9D5A1CDC1",
    "TxnSignature": "D7234C42F7E1B2CDDCBB08EED6AF4392261A31B961F10C66CB733DB7F6CD9EA"
  },
  "Fee": "36",
  "Sequence": 11
}
```

### 4.4. Firewall Check Implementation

The firewall system integrates into the transaction processing pipeline using a checker pattern similar to invariant checking. The checker runs after transaction application to validate all balance changes against both whitelists and rules.

#### 4.4.1. Architecture

```cpp
using FirewallChecks = std::tuple<AccountRootBalance, ValidWithdraw>;
```

#### 4.4.2. ValidWithdraw Checker

The ValidWithdraw checker tracks all balance changes during transaction processing and validates them against firewall whitelists in the finalize phase. The implementation handles multiple asset types and transaction patterns.

##### 4.4.2.1. Supported Ledger Entry Types

The checker validates balance changes for:

- **AccountRoot**: XRP balance changes
- **RippleState**: IOU balance changes between accounts
- **Escrow**: XRP locked in escrows for future release
- **PayChannel**: XRP in payment channels
- **NFTokenPage**: NFT ownership changes (special handling)
- **NFTokenOffer**: NFT transfer offers
- **MPToken**: Multi-Purpose Token transfers

##### 4.4.2.2. Operation Flow

1. **visitEntry()**: Called for each modified ledger entry
   - Identifies entries that affect balances
   - Calculates balance changes (before vs after)
   - Groups changes by asset type (XRP, IOUs, MPTokens, NFTs)
   - Categorizes accounts as senders (negative changes) or receivers (positive changes)

2. **finalize()**: Called after all modifications
   - For each asset type with transfers
   - Checks if any sender has a firewall
   - Validates all receivers are preauthorized with matching optional destination tags
   - Returns false (triggering tecFIREWALL_BLOCK) if unauthorized

##### 4.4.2.3. Balance Change Calculation

The implementation handles different balance field types:

- `sfBalance`: For AccountRoot and RippleState
- `sfAmount`: For Escrow and PayChannel objects
- `sfMPTAmount`: For MPToken balances
- NFT transfers: Tracked using special currency markers

##### 4.4.2.4. NFT Transfer Handling

NFTs require special handling since they don't have traditional balance fields:

- NFTokenPage changes indicate token ownership transfers
- Uses a special currency marker to distinguish NFT transfers
- Tracks sender when pages are deleted or modified
- Tracks receiver when pages are created or modified

##### 4.4.2.5. Multi-Asset Support

The checker groups balance changes by asset:

- XRP (native asset)
- IOUs (grouped by currency and issuer)
- MPTokens (grouped by MPTokenIssuanceID)
- NFTs (special marker currency)

##### 4.4.2.6. Destination Tag Validation

When checking WithdrawPreauth entries:

- If the transaction includes a DestinationTag, the preauth must match the destination tag
- If the transaction has no DestinationTag, the preauth must not specify a destination tag
- Ensures precise control over authorized payment destinations

##### 4.4.2.7. Clawback

An exception in blocking transactions will be made for tokens that have clawback enabled, to ensure firewall cannot be used to prevent clawback.

#### 4.4.3. AccountRootBalance Checker

##### 4.4.3.1. Overview

Monitors balance changes in AccountRoot entries and validates them against configured rules.

##### 4.4.3.2. Operation Flow

1. **visitEntry()**:
   - Detects AccountRoot modifications
   - Calculates balance changes
   - Records changes for validation

2. **finalize()**:
   - Retrieves firewall rules for the account
   - Evaluates each rule against balance changes
   - Handles time-based accumulation if specified
   - Returns false (triggering tecFIREWALL_BLOCK) if rules violated

##### 4.4.3.3. Time-Based Rule Algorithm

```
IF current_time - start_time > time_period THEN
    // Reset tracking period
    start_time = current_time
    total_amount = current_change
ELSE
    // Add to ongoing total
    total_amount += current_change
END IF

IF evaluateComparison(total_amount, rule_limit, operator) THEN
    // Rule passes, update stored total
    updateRuleTotal(firewall, rule, total_amount)
ELSE
    // Rule fails, block transaction
    BLOCK transaction
END IF
```

##### 4.4.3.4. Rule Persistence

Time-based rules maintain state across transactions:

- `TimeStart`: Timestamp of period start
- `TimeValue`: Accumulated value in current period
- These fields are updated in the Firewall object when rules are evaluated

### 4.5. Firewall Macro System

The firewall system uses a macro-based architecture similar to invariant checking for registering and managing firewall handlers. This system provides compile-time registration of firewall rules and runtime dispatch to appropriate handlers.

#### 4.5.1. Firewall Registration Macro

The core firewall functionality is defined using the `FIREWALL_ENTRY` macro in `firewall.macro`:

```cpp
/**
 * FIREWALL_ENTRY(name, ledgerType, fields, value)
 *
 * This macro defines a firewall registration:
 * name: the name of the firewall handler.
 * ledgerType: the LedgerEntryType this firewall handles.
 * fields: array of SField types this firewall monitors.
 * value: the uint32 numeric value for the firewall type.
 */

/** This firewall checks account root modifications for balance and sequence limits. */
FIREWALL_ENTRY(AccountRootFirewall, ltACCOUNT_ROOT, {&sfBalance}, 1)
```

#### 4.5.2. Firewall Type Registration

The macro system automatically generates:

- FirewallType enum values
- Type-to-name mappings
- Ledger type associations
- Field monitoring configurations

```cpp
enum FirewallType : std::uint32_t {
    AccountRootFirewall = 1,
    // Additional types added via macro
};
```

#### 4.5.3. Compile-Time Registration

The Firewall singleton class initializes mappings at compile time:

```cpp
class Firewall {
private:
    std::unordered_map<std::string, FirewallType> firewallNameMap_;
    std::unordered_map<FirewallType, LedgerEntryType> firewallLedgerTypeMap_;
    std::unordered_map<FirewallType, std::vector<SField const*>> firewallFieldsMap_;
public:
    static Firewall const& getInstance();
    bool hasFirewall(LedgerEntryType const& ledgerType) const;
    bool handlesField(LedgerEntryType const& ledgerType, SField const& field) const;
};
```

#### 4.5.4. Adding New Firewall Types

To add a new firewall type:

1. **Update firewall.macro:**

```cpp
FIREWALL_ENTRY(TrustLineFirewall, ltRIPPLE_STATE, {&sfBalance, &sfLimit}, 2)
```

2. **Add Checker Class:**

```cpp
class TrustLineChecker {
public:
    void visitEntry(bool isDelete,
                   std::shared_ptr<SLE const> const& before,
                   std::shared_ptr<SLE const> const& after);
    bool finalize(STTx const& tx, TER const result,
                 XRPAmount const fee, ApplyView& view,
                 beast::Journal const& j);
};
```

3. **Update FirewallChecks Tuple:**

```cpp
using FirewallChecks = std::tuple<AccountRootBalance, ValidWithdraw, TrustLineChecker>;
```

## 5. Rationale

**Whitelist Model**: Chosen over blacklist as it's more secure by default - new threats are automatically blocked rather than requiring updates to block them.

**Counterparty System**: Provides 2nd layer of security to firewall changes, preventing single points of failure.

**Enforced Backup Account**: Ensures users cannot lock themselves out during initial setup, addressing common security configuration errors.

**Destination Tag Support**: Allows fine-grained control over authorized destinations, supporting exchange accounts and service providers that require specific tags.

**STData Type**: Provides flexibility to store different value types in rules without requiring separate fields for each type. This enables comparison of amounts, accounts, and other data types using a single rule structure.

**Rule Limits**: Maximum of 8 rules balances flexibility with performance and storage considerations. This limit prevents abuse while allowing sophisticated security policies.

**Time-Based Tracking**: Storing accumulation state in the ledger ensures consistent enforcement across all validators without requiring external state or synchronization.

**Comparison Operators**: Five operators (< ≤ = ≥ >) provide sufficient expressiveness for most security policies while keeping implementation simple.

**Field-Specific Monitoring**: Using numeric FieldCode allows monitoring any serialized field without hard-coding specific fields in the protocol.

**Checker Architecture**: Reuses existing invariant checker pattern, minimizing code changes and leveraging proven infrastructure.

**Post-Application Checking**: Firewall validation occurs after transaction application to accurately capture all balance changes, including complex multi-hop payments, DEX trades, and NFT transfers.

**Multi-Asset Support**: Unified approach across all XRPL asset types ensures consistent security model regardless of transaction complexity.

**Master Key Protection**: Preventing master key disable while firewall is active ensures account recovery remains possible even with master key compromise.

**Regular Key & Signerlist Protection**: To account for users who have already disabled their master key and use a regular key or signerlist - changes to these (once firewall is enabled) will require counterparty signature.

**Macro System**: Compile-time registration eliminates runtime overhead while providing extensibility. Similar to invariant checking, this allows new firewall types to be added without modifying core logic.

## 6. Backwards Compatibility

This amendment introduces no backwards incompatibilities:

- Accounts without firewalls continue operating normally
- All existing transaction types remain functional
- The feature is entirely opt-in
- No changes to existing ledger entries or transaction formats
- Existing destination tag functionality is preserved and enhanced
- FirewallRules field is optional
- Rules only affect transactions after activation
- Existing escrows and payment channels continue to function
- Automated market makers operate independently of firewall rules

## 7. Security Considerations

### 7.1. Key Compromise Protection

Even with full key compromise, attackers cannot:

- Send assets to unauthorized addresses
- Disable the firewall without counterparty approval
- Add or Remove existing preauthorizations without counterparty approval
- Disable master key while firewall is active
- Set a new regular key or signers list without counterparty approval - guarding those who have already disabled the master key and use a regular key for signing
- Bypass destination tag requirements
- Bypass configured rules and limits

Attackers can only send assets to already-authorized addresses with matching tags and within rule limits, significantly limiting potential damage.

### 7.2. Counterparty Risk

A compromised counterparty cannot change anything alone.
All a counterparty can do is countersign.
Both master key and counterparty would need to be compromised to initiate a change which could result in loss of assets.

A compromised counterparty can approve any requested change.

Mitigation: Choose counterparty carefully, consider using a second account you control with separated key hygiene.

### 7.3. Denial of Service

A malicious counterparty cannot:

- Prevent transfers to already-authorized addresses
- Lock the account permanently
- Delete the firewall unilaterally
- Change firewall setting unilaterally
- Modify destination tag requirements without authorization
- Alter rules without authorization

### 7.4. Implementation Security

- Checker pattern ensures all balance changes are validated
- Post-application checking prevents bypass through complex transactions
- Invariant checking ensures ledger consistency
- All asset types follow consistent authorization model
- Rules are evaluated post-transaction application, capturing all balance effects
- Complex transactions (payments, offers) cannot bypass rules through indirect paths
- Time-based rules maintain state across transactions to prevent reset attacks

### 7.5. Multi-Asset Protection

The firewall provides consistent protection across all asset types on the XRPL:

- Native XRP transfers
- Issued currencies (IOUs)
- Non-Fungible Tokens (NFTs)
- Multi-Purpose Tokens (MPTs)

All asset types follow the same authorization model through WithdrawPreauth entries.

### 7.6. Transaction Type Coverage

The post-application checking ensures that complex, multi-step transactions cannot bypass firewall rules:

- Cross-currency payments with path-finding
- Automatic order matching in the DEX
- Multi-party transactions
- Indirect transfers through object creation/deletion
- NFT transfers through page modifications

### 7.7. Rule Security

- TimeStart and TimeValue fields can only be modified by the protocol during rule evaluation
- Counterparty cannot manipulate rule state directly
- Rule evaluation is deterministic across all validators
- 8-rule limit prevents excessive computational overhead
- STData size limits prevent storage attacks
- Rule evaluation has O(n) complexity where n ≤ 8
- Zero-value comparisons are supported
- Overflow protection in accumulation logic
- Time period transitions are atomic
- Rules cannot reference external state

## 8. Appendix

### 8.1. FAQ

**Q: Can incoming payments be blocked?**
A: No, this system only restricts outgoing payments. Incoming payments are always allowed.

**Q: What if my counterparty becomes unavailable?**
A: Existing preauthorized addresses continue working. You cannot add new ones without counterparty cooperation.

**Q: Can I remove the firewall?**
A: Yes, with counterparty approval using FirewallDelete transaction. All WithdrawPreauth entries are automatically removed.

**Q: How many addresses can I preauthorize?**
A: Limited only by reserve requirements and directory size limits.

**Q: Can I use destination tags with the firewall?**
A: Yes, WithdrawPreauth entries can specify required destination tags, providing fine-grained control over authorized destinations.

**Q: Does the firewall work with NFTs?**
A: Yes, NFT transfers are fully supported. The system tracks NFTokenPage changes to detect token movements and blocks unauthorized transfers.

**Q: What about new token types like MPTokens?**
A: MPTokens are fully supported. The firewall tracks MPToken balance changes and enforces the same authorization rules.

**Q: Can complex DEX trades bypass the firewall?**
A: No, the post-application checking captures all balance changes regardless of transaction complexity, including auto-bridging and path-finding.

**Q: Can I use my own account as counterparty?**
A: Yes, you can use any account (other than the one being protected) as the counterparty, including one you control. This provides security through separation - an attacker would need to compromise both accounts.

**Q: What happens to existing transactions like Escrow or Payment Channels?**
A: Existing obligations continue to function. The firewall only affects new outgoing transfers initiated after activation.

**Q: Are there any transaction types that bypass the firewall?**
A: The firewall only restricts outgoing value transfers. Non-payment transactions (like AccountSet, SignerListSet) and transactions that don't transfer value are not restricted. Incoming payments are always allowed.

**Q: Can rules be temporarily disabled?**
A: No, rules are always enforced once set. They can only be removed or modified with counterparty approval.

**Q: What happens if the time period expires mid-transaction?**
A: Time periods are evaluated atomically at transaction application time. The entire transaction uses a consistent time value.

**Q: Can different rules monitor the same field?**
A: Yes, multiple rules can monitor the same field with different operators or time periods.

**Q: Are rule evaluations visible in transaction metadata?**
A: Rule evaluations don't produce explicit metadata, but blocked transactions return tecFIREWALL_BLOCK.

**Q: Can rules reference other accounts' balances?**
A: No, rules only monitor changes to the firewall owner's ledger entries.

### 8.2. Supported Ledger Types and Fields

Initially supported:

- `ltACCOUNT_ROOT`:
  - `sfBalance`: Monitor XRP balance changes

Future extensions may add:

- `ltRIPPLE_STATE`: IOU balance monitoring
- `ltNFTOKEN_PAGE`: NFT transfer limits
- Custom ledger types as they are added

### 8.3. Example Use Cases

#### 8.3.1. Daily Spending Limit

```json
{
  "FirewallRule": {
    "LedgerEntryType": 97,
    "FieldCode": 6,
    "ComparisonOperator": 5,
    "FirewallValue": {
      "type": "AMOUNT",
      "value": "100000000"
    },
    "TimePeriod": 86400
  }
}
```

#### 8.3.2. Minimum Balance Maintenance

```json
{
  "FirewallRule": {
    "LedgerEntryType": 97,
    "FieldCode": 6,
    "ComparisonOperator": 4,
    "FirewallValue": {
      "type": "AMOUNT",
      "value": "20000000"
    }
  }
}
```

### 8.4. Reference Implementation

The reference implementation will be provided as a pull request to the rippled repository upon advancement to Final status.
