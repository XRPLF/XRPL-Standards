<pre>
  xls: 87
  title: Token Pre-Authorization
  description: Allow MPT issuers to pre-authorize specific holders, and to block specific accounts from holding a token.
  author: Zhiyuan Wang <zhiyuanw@ripple.com>, Mayukha Vadari <mvadari@ripple.com>, Shawn Xie <shawnxie@ripple.com>, Yinyi Qian <yqian@ripple.com>
  category: Amendment
  status: Draft
  requires: XLS-33
  proposal-from: https://github.com/XRPLF/XRPL-Standards/discussions/258
  created: 2024-12-11
  updated: 2026-10-13
</pre>

# Token Pre-Authorization

## 1. Abstract

Managing who may hold a token on the XRP Ledger is either fully manual or fully reactive.

Issuers that require authorization (`lsfMPTRequireAuth` on an `MPTokenIssuance`) must sign a separate transaction for every holder they approve. This is impractical at scale, and it is at odds with keeping issuer keys in cold storage.

Issuers that do not require authorization have the opposite problem. Their token is permissionless: any account can opt in and start receiving it immediately. The controls available today (per-holder lock, global lock, and clawback) only act on a holding after it exists, so an account the issuer must not serve can opt in and receive funds in the window before the issuer reacts.

This specification lets an issuer record one of two decisions about a specific holder of a specific token, each as its own issuer-owned ledger entry:

- **`TokenPreauth` (pre-authorized):** on a token that requires authorization, the holder is authorized without a second issuer transaction.
- **`TokenBlock` (blocked):** the holder cannot obtain a holding of the token by any means, whether or not the token requires authorization. If the account already has a holding, its authorization is revoked, but the holding is not frozen: freezing it remains a separate Lock.

Each entry is managed by a transaction of the same name, `TokenPreauth` and `TokenBlock`, mirroring `DepositPreauth`.

The first release of this amendment covers MPTs and individual holder addresses only. IOUs, pre-authorization by credential or domain, and blocking for Deposit Authorization are left to later amendments (see [Section 14](#14-future-extensions)).

## 2. Motivation

### 2.1. Background: Authorized MPTs

An `MPTokenIssuance` with `lsfMPTRequireAuth` only lets an account hold the token once the issuer has authorized that account's `MPToken`. The holder first creates the `MPToken` with `MPTokenAuthorize`; the issuer then sends a second `MPTokenAuthorize` with the `Holder` field to approve it.

### 2.2. Background: Permissionless MPTs

Without `lsfMPTRequireAuth`, any account can submit `MPTokenAuthorize`, create an `MPToken`, and receive the token. Since MPTokensV2, an `MPToken` is also created implicitly when an account acquires the token through the DEX, by cashing a Check, by finishing an Escrow, or by withdrawing from an AMM.

Issuers subject to sanctions and similar regulatory regimes are expected to be able to prevent specific parties from holding their token at all. The existing controls all act on a holding that already exists:

- Lock (`lsfMPTLocked`) restricts movement of an existing balance.
- Clawback removes an existing balance.

Neither prevents a listed account from opting in and receiving funds before the issuer detects and locks it. Requiring authorization is not a substitute for permissionless tokens: it would force the issuer to approve every holder.

A preventive block closes that window. The opt-in itself fails, deterministically and verifiably on-ledger, in the same ledger that the opt-in is attempted.

### 2.3. Terminology

- **Pre-authorized:** a `TokenPreauth` entry exists for the holder and issuance. Only has an effect on issuances that require authorization.
- **Blocked:** a `TokenBlock` entry exists for the holder and issuance. Has an effect on every issuance.
- **Holding:** the `MPToken` object for a given account and issuance.

A holder is never both pre-authorized and blocked for the same issuance.

A block is scoped to one MPT issuance. It is not an account-level freeze: a blocked account can still hold and transact XRP and every other token.

### 2.4. Overview

This feature mirrors [Deposit Authorization](https://xrpl.org/docs/concepts/accounts/depositauth) in naming and shape: one issuer-owned ledger entry per counterparty, managed by a transaction of the same name. It applies to holding a token rather than to payments into the issuer's account.

We propose:

- A new `TokenPreauth` ledger entry, recording a pre-authorization.
- A new `TokenBlock` ledger entry, recording a block.
- A new `TokenPreauth` transaction to create or delete a `TokenPreauth` entry.
- A new `TokenBlock` transaction to create or delete a `TokenBlock` entry.
- Changes to `MPTokenAuthorize`.
- A rule that no transaction may create a holding for a blocked account.
- A new transaction result code, `tecTOKEN_BLOCKED`.

This feature requires an amendment, tentatively titled `TokenPreauth`.

### 2.5. Release Scope

| In this amendment                                          | Later amendments                                            |
| ---------------------------------------------------------- | ----------------------------------------------------------- |
| MPT issuances                                              | IOUs (`TrustSet` changes)                                   |
| Pre-authorizing and blocking an individual holder address  | Pre-authorization by credential (XLS-70) or domain (XLS-80) |
| Exactly one MPT issuance per entry                         | Issuer-wide pre-authorization covering all tokens           |
| Revoking an existing holding's authorization when blocking | Blocking for Deposit Authorization                          |

Blocking is never issuer-wide, in this or any later amendment (see [Section 10.3](#103-why-blocks-are-per-token)).

## 3. Ledger Entry: `TokenPreauth`

Records that an issuer has pre-authorized one holder for one MPT issuance. Like `DepositPreauth`, it has no flags: the entry's existence is the pre-authorization.

### 3.1. Object Identifier

**Key Space:** `0x0077` (`'w'`)

**Ledger Entry Type:** `ltTOKEN_PREAUTH` = `0x0092`

**ID Calculation Algorithm:**

```
SHA512-Half(0x0077 || Holder || MPTokenIssuanceID)
```

The issuer is not hashed separately: `MPTokenIssuanceID` already encodes it. Future variants that pre-authorize by something other than an address and an MPT issuance (see [Section 14](#14-future-extensions)) can use their own key space, as `DepositPreauth` does for credentials, so this key never changes.

### 3.2. Fields

| Field Name          | Constant | Required? | Internal Type | Default Value  | Description                                                                       |
| ------------------- | -------- | --------- | ------------- | -------------- | --------------------------------------------------------------------------------- |
| `LedgerEntryType`   | Yes      | Yes       | `UINT16`      | `TokenPreauth` | Identifies this as a `TokenPreauth` entry.                                        |
| `Account`           | No       | Yes       | `ACCOUNT`     | N/A            | The issuer that created the entry. This is the owner, not the holder.             |
| `Holder`            | No       | Yes       | `ACCOUNT`     | N/A            | The account that is pre-authorized.                                               |
| `MPTokenIssuanceID` | No       | Yes       | `UINT192`     | N/A            | The MPT issuance this entry applies to.                                           |
| `OwnerNode`         | No       | Yes       | `UINT64`      | N/A            | A hint indicating which page of the issuer's owner directory links to this entry. |
| `PreviousTxnID`     | No       | Yes       | `HASH256`     | N/A            | The hash of the transaction that most recently modified this entry.               |
| `PreviousTxnLgrSeq` | No       | Yes       | `UINT32`      | N/A            | The ledger index containing that transaction.                                     |

### 3.3. Flags

None.

### 3.4. Ownership

**Owner:** `Account` (the issuer)

**Directory Registration:** The entry is registered in the issuer's owner directory only.

The `Holder` does not own the entry, does not pay its reserve, and does not see it in its owner directory.

### 3.5. Reserves

**Reserve Requirement:** Standard

Each entry requires one owner reserve increment (currently 0.2 XRP, subject to Fee Voting), paid by the issuer. Reserve sponsorship is not supported for this entry.

### 3.6. Deletion

**Deletion Transactions:** `TokenPreauth` with `tfUnauthorize`, `TokenBlock` (see [Section 6.5](#65-state-changes)), `AccountDelete`

**Deletion Conditions:**

- `TokenPreauth` with `tfUnauthorize`; or
- `TokenBlock` without `tfUnblock`, which replaces the entry with a `TokenBlock`; or
- `AccountDelete` by the issuer.

An entry can be deleted after its `MPTokenIssuance` has been destroyed, so the issuer can recover the reserve.

**Account Deletion Blocker:** No

`AccountDelete` by the issuer deletes its `TokenPreauth` entries. In practice an issuer cannot delete its account while any of its issuances still exist, so the entries it deletes are always for destroyed issuances. The entry is not a deletion blocker for the `Holder` either, since the holder does not own it.

### 3.7. Invariants

- `Account` is the issuer of `MPTokenIssuanceID`, and `Holder` is not that issuer.
- No `TokenBlock` entry exists with the same `Holder` and `MPTokenIssuanceID`.

### 3.8. RPC Name

**RPC Type Name:** `token_preauth`

`ledger_entry` accepts either the entry's index or the fields that make up its ID:

```json
{
  "command": "ledger_entry",
  "token_preauth": {
    "holder": "rALICE......",
    "mpt_issuance_id": "000005F398B624EBD06822198649C920C8B20ADB8EBE745E"
  },
  "ledger_index": "validated"
}
```

`holder` and `mpt_issuance_id` are both required. If no entry exists, the result is `entryNotFound`.

`account_objects` with `"type": "token_preauth"` lists every pre-authorization an issuer owns.

### 3.9. Example JSON

```json
{
  "LedgerEntryType": "TokenPreauth",
  "Flags": 0,
  "Account": "rISSUER......",
  "Holder": "rALICE......",
  "MPTokenIssuanceID": "000005F398B624EBD06822198649C920C8B20ADB8EBE745E",
  "OwnerNode": "0000000000000000",
  "PreviousTxnID": "AA10031C6C21164E7673...17D467CEEE9",
  "PreviousTxnLgrSeq": 12345700
}
```

## 4. Ledger Entry: `TokenBlock`

Records that an issuer has blocked one account from one MPT issuance. It has the same fields and ownership as `TokenPreauth`, in a separate key space.

### 4.1. Object Identifier

**Key Space:** `0x0057` (`'W'`)

**Ledger Entry Type:** `ltTOKEN_BLOCK` = `0x0093`

**ID Calculation Algorithm:**

```
SHA512-Half(0x0057 || Holder || MPTokenIssuanceID)
```

As for `TokenPreauth`, the issuer is encoded in `MPTokenIssuanceID`.

Checking whether an account is blocked is a single existence lookup of this key. The list is not stored on the `MPTokenIssuance` or on the issuer's `AccountRoot`, so neither grows with the number of entries.

### 4.2. Fields

| Field Name          | Constant | Required? | Internal Type | Default Value | Description                                                                       |
| ------------------- | -------- | --------- | ------------- | ------------- | --------------------------------------------------------------------------------- |
| `LedgerEntryType`   | Yes      | Yes       | `UINT16`      | `TokenBlock`  | Identifies this as a `TokenBlock` entry.                                          |
| `Account`           | No       | Yes       | `ACCOUNT`     | N/A           | The issuer that created the entry. This is the owner, not the holder.             |
| `Holder`            | No       | Yes       | `ACCOUNT`     | N/A           | The account that is blocked. It does not need to exist on the ledger.             |
| `MPTokenIssuanceID` | No       | Yes       | `UINT192`     | N/A           | The MPT issuance this entry applies to.                                           |
| `OwnerNode`         | No       | Yes       | `UINT64`      | N/A           | A hint indicating which page of the issuer's owner directory links to this entry. |
| `PreviousTxnID`     | No       | Yes       | `HASH256`     | N/A           | The hash of the transaction that most recently modified this entry.               |
| `PreviousTxnLgrSeq` | No       | Yes       | `UINT32`      | N/A           | The ledger index containing that transaction.                                     |

### 4.3. Flags

None.

### 4.4. Ownership

**Owner:** `Account` (the issuer)

**Directory Registration:** The entry is registered in the issuer's owner directory only. The `Holder` does not own it.

### 4.5. Reserves

**Reserve Requirement:** Standard

Each entry requires one owner reserve increment, paid by the issuer. Replacing a `TokenPreauth` with a `TokenBlock` does not change the issuer's owner count. Reserve sponsorship is not supported for this entry.

### 4.6. Deletion

**Deletion Transactions:** `TokenBlock` with `tfUnblock`, `AccountDelete`

**Deletion Conditions:**

- `TokenBlock` with `tfUnblock`; or
- `AccountDelete` by the issuer.

The `TokenPreauth` transaction never deletes a `TokenBlock`. An entry can be deleted after its `MPTokenIssuance` has been destroyed.

**Account Deletion Blocker:** No

As with `TokenPreauth`, `AccountDelete` by the issuer deletes its `TokenBlock` entries. The entry is not a deletion blocker for the `Holder`. If the holder's account is deleted and later re-created at the same address, the block still applies.

### 4.7. Invariants

- `Account` is the issuer of `MPTokenIssuanceID`, and `Holder` is not that issuer.
- No `TokenPreauth` entry exists with the same `Holder` and `MPTokenIssuanceID`.
- No transaction creates an `MPToken` for a blocked holder, except `AMMClawback`, which creates it with `lsfMPTLocked` (see [Section 8](#8-creating-a-holding-for-a-blocked-account)).
- While the entry exists, the holder's `MPToken` for that issuance, if one exists, does not have `lsfMPTAuthorized` at the end of any transaction (see [Section 6.5.1](#651-revoking-authorization)).

### 4.8. RPC Name

**RPC Type Name:** `token_block`

`ledger_entry` accepts either the entry's index or the fields that make up its ID:

```json
{
  "command": "ledger_entry",
  "token_block": {
    "holder": "rBLOCKED......",
    "mpt_issuance_id": "000005F398B624EBD06822198649C920C8B20ADB8EBE745E"
  },
  "ledger_index": "validated"
}
```

`holder` and `mpt_issuance_id` are both required. If no entry exists, the result is `entryNotFound`. This lets anyone, including a regulator, independently verify whether a given account is blocked from a given token.

`account_objects` with `"type": "token_block"` lists an issuer's complete block list.

### 4.9. Example JSON

```json
{
  "LedgerEntryType": "TokenBlock",
  "Flags": 0,
  "Account": "rISSUER......",
  "Holder": "rBLOCKED......",
  "MPTokenIssuanceID": "000005F398B624EBD06822198649C920C8B20ADB8EBE745E",
  "OwnerNode": "0000000000000000",
  "PreviousTxnID": "DD40031C6C21164E7673...17D467CEEE9",
  "PreviousTxnLgrSeq": 12345678
}
```

## 5. Transaction: `TokenPreauth`

Pre-authorizes a holder for an MPT issuance by creating a `TokenPreauth` entry, or removes a pre-authorization by deleting it. Sent by the issuer.

### 5.1. Fields

| Field Name          | Required? | JSON Type | Internal Type | Default Value  | Description                                                         |
| ------------------- | --------- | --------- | ------------- | -------------- | ------------------------------------------------------------------- |
| `TransactionType`   | Yes       | `string`  | `UINT16`      | `TokenPreauth` | Identifies this as a `TokenPreauth` transaction.                    |
| `Holder`            | Yes       | `string`  | `ACCOUNT`     | N/A            | The account to pre-authorize, or whose pre-authorization to remove. |
| `MPTokenIssuanceID` | Yes       | `string`  | `UINT192`     | N/A            | The MPT issuance the pre-authorization applies to.                  |

### 5.2. Flags

| Flag Name       | Flag Value   | Description                                                                                  |
| --------------- | ------------ | -------------------------------------------------------------------------------------------- |
| `tfUnauthorize` | `0x00000001` | Remove the pre-authorization: delete the `TokenPreauth` entry. If not set, create the entry. |

As with `MPTokenAuthorize`, creating is the default and a flag selects removal.

### 5.3. Transaction Fee

**Fee Structure:** Standard

### 5.4. Failure Conditions

#### 5.4.1. Data Verification

1. The `TokenPreauth` amendment is not enabled (`temDISABLED`).
2. Any flag other than `tfUnauthorize` and the universal flags is set (`temINVALID_FLAG`).
3. `Holder` is the zero account (`temINVALID_ACCOUNT_ID`).
4. `Holder` is the same as `Account` (`temMALFORMED`).

#### 5.4.2. Protocol-Level Failures

In all cases:

1. `Account` is not the issuer encoded in `MPTokenIssuanceID` (`tecNO_PERMISSION`). This is read from the ID itself, so it also applies after the `MPTokenIssuance` is destroyed.

With `tfUnauthorize`:

1. No `TokenPreauth` entry exists for (`Holder`, `MPTokenIssuanceID`) (`tecNO_ENTRY`). The `MPTokenIssuance` does not need to still exist.

Without `tfUnauthorize`:

1. The `MPTokenIssuance` does not exist (`tecOBJECT_NOT_FOUND`).
2. `Holder` is a pseudo-account (AMM, Vault, or LoanBroker) (`tecPSEUDO_ACCOUNT`).
3. The `Holder` account does not exist (`tecNO_DST`).
4. `Holder` is blocked. The issuer must remove the block with `TokenBlock` and `tfUnblock` first (`tecNO_PERMISSION`).
5. `Holder` is already pre-authorized (`tecDUPLICATE`).
6. `Account` does not have enough reserve for the new entry (`tecINSUFFICIENT_RESERVE`).

### 5.5. State Changes

On success (`tesSUCCESS`):

- Without `tfUnauthorize`: create the `TokenPreauth` entry and increase the issuer's owner count by one (see also [Section 5.5.1](#551-pre-authorizing-an-existing-holder)).
- With `tfUnauthorize`: delete the `TokenPreauth` entry and decrease the issuer's owner count by one.

#### 5.5.1. Pre-Authorizing an Existing Holder

If the issuance has `lsfMPTRequireAuth` and an `MPToken` already exists for (`MPTokenIssuanceID`, `Holder`), creating the pre-authorization also sets `lsfMPTAuthorized` on it.

Otherwise the pre-authorization would never take effect for a holder that opted in before being pre-authorized: that holder has no further transaction to send, since a second `MPTokenAuthorize` fails with `tecDUPLICATE`.

`tfUnauthorize` does not clear `lsfMPTAuthorized`. Revoking a holder's authorization remains an explicit `MPTokenAuthorize` from the issuer with `tfMPTUnauthorize`.

### 5.6. Delegation

The `TokenPreauth` transaction is delegable under [XLS-75](../XLS-0075-permission-delegation/README.md) with the transaction-level permission `TokenPreauth`, which allows both creating and removing pre-authorizations. See [Section 6.6](#66-delegation) for how delegation applies to both transactions.

### 5.7. Example JSON

Pre-authorizing an account:

```json
{
  "TransactionType": "TokenPreauth",
  "Account": "rISSUER......",
  "Holder": "rALICE......",
  "MPTokenIssuanceID": "000005F398B624EBD06822198649C920C8B20ADB8EBE745E",
  "Fee": "10",
  "Sequence": 12347
}
```

Removing the pre-authorization:

```json
{
  "TransactionType": "TokenPreauth",
  "Account": "rISSUER......",
  "Flags": 1,
  "Holder": "rALICE......",
  "MPTokenIssuanceID": "000005F398B624EBD06822198649C920C8B20ADB8EBE745E",
  "Fee": "10",
  "Sequence": 12348
}
```

## 6. Transaction: `TokenBlock`

Blocks a holder from an MPT issuance by creating a `TokenBlock` entry, or removes a block by deleting it. Sent by the issuer.

### 6.1. Fields

| Field Name          | Required? | JSON Type | Internal Type | Default Value | Description                                     |
| ------------------- | --------- | --------- | ------------- | ------------- | ----------------------------------------------- |
| `TransactionType`   | Yes       | `string`  | `UINT16`      | `TokenBlock`  | Identifies this as a `TokenBlock` transaction.  |
| `Holder`            | Yes       | `string`  | `ACCOUNT`     | N/A           | The account to block, or whose block to remove. |
| `MPTokenIssuanceID` | Yes       | `string`  | `UINT192`     | N/A           | The MPT issuance the block applies to.          |

### 6.2. Flags

| Flag Name   | Flag Value   | Description                                                                    |
| ----------- | ------------ | ------------------------------------------------------------------------------ |
| `tfUnblock` | `0x00000001` | Remove the block: delete the `TokenBlock` entry. If not set, create the entry. |

### 6.3. Transaction Fee

**Fee Structure:** Standard

### 6.4. Failure Conditions

#### 6.4.1. Data Verification

1. The `TokenPreauth` amendment is not enabled (`temDISABLED`).
2. Any flag other than `tfUnblock` and the universal flags is set (`temINVALID_FLAG`).
3. `Holder` is the zero account (`temINVALID_ACCOUNT_ID`).
4. `Holder` is the same as `Account` (`temMALFORMED`).

#### 6.4.2. Protocol-Level Failures

In all cases:

1. `Account` is not the issuer encoded in `MPTokenIssuanceID` (`tecNO_PERMISSION`), as for `TokenPreauth`.

With `tfUnblock`:

1. No `TokenBlock` entry exists for (`Holder`, `MPTokenIssuanceID`) (`tecNO_ENTRY`). The `MPTokenIssuance` does not need to still exist.

Without `tfUnblock`:

1. The `MPTokenIssuance` does not exist (`tecOBJECT_NOT_FOUND`).
2. `Holder` is a pseudo-account (AMM, Vault, or LoanBroker) (`tecPSEUDO_ACCOUNT`).
3. `Holder` is already blocked (`tecDUPLICATE`).
4. A new entry would be created and `Account` does not have enough reserve for it (`tecINSUFFICIENT_RESERVE`). Replacing a pre-authorization does not need additional reserve.

An existing `TokenPreauth` entry for the same holder is not a failure condition: the block replaces it in the same transaction ([Section 6.5](#65-state-changes), [Section 13.4](#134-block-takes-precedence)). Requiring a separate `TokenPreauth` with `tfUnauthorize` first would leave a gap between the two transactions, and a delegate holding only `TokenBlockCreate` could not block a pre-authorized holder at all.

Unlike `TokenPreauth`, `TokenBlock` does not require the `Holder` account to exist. Sanctions lists routinely include addresses that have not yet been funded on the XRP Ledger. If a block could only be created after the address is funded, that address could be funded and opt in within the same ledger, which is the race this feature exists to remove.

### 6.5. State Changes

On success (`tesSUCCESS`):

- Without `tfUnblock`:
  - If a `TokenPreauth` entry exists for the same (`Holder`, `MPTokenIssuanceID`), delete it. A block takes precedence over a pre-authorization.
  - Create the `TokenBlock` entry.
  - Clear `lsfMPTAuthorized` on the holder's `MPToken`, if any (see [Section 6.5.1](#651-revoking-authorization)).
- With `tfUnblock`: delete the `TokenBlock` entry.

Creating an entry increases the issuer's owner count by one and deleting one decreases it by one, so replacing a `TokenPreauth` with a `TokenBlock` leaves it unchanged.

The two transactions together give each (`Holder`, `MPTokenIssuanceID`) at most one state:

| Transaction                      | Neither entry exists                                                        | `TokenPreauth` exists                                                                   | `TokenBlock` exists        |
| -------------------------------- | --------------------------------------------------------------------------- | --------------------------------------------------------------------------------------- | -------------------------- |
| `TokenPreauth`                   | Create `TokenPreauth`; see [5.5.1](#551-pre-authorizing-an-existing-holder) | Fails (`tecDUPLICATE`)                                                                  | Fails (`tecNO_PERMISSION`) |
| `TokenPreauth` + `tfUnauthorize` | Fails (`tecNO_ENTRY`)                                                       | Delete `TokenPreauth`                                                                   | Fails (`tecNO_ENTRY`)      |
| `TokenBlock`                     | Create `TokenBlock`; see [6.5.1](#651-revoking-authorization)               | Delete `TokenPreauth` and create `TokenBlock`; see [6.5.1](#651-revoking-authorization) | Fails (`tecDUPLICATE`)     |
| `TokenBlock` + `tfUnblock`       | Fails (`tecNO_ENTRY`)                                                       | Fails (`tecNO_ENTRY`)                                                                   | Delete `TokenBlock`        |

#### 6.5.1. Revoking Authorization

If an `MPToken` exists for (`MPTokenIssuanceID`, `Holder`), creating the block clears `lsfMPTAuthorized` on it, if set, in the same transaction. This only has an effect on an issuance with `lsfMPTRequireAuth`, where it revokes the issuer's approval of the holder. While the block exists, the holding stays unauthorized: `MPTokenAuthorize` from the issuer fails with `tecTOKEN_BLOCKED` for a blocked holder ([Section 7.2](#72-failure-conditions)).

A block does not lock the holding, and does not change its balance. A block stops a holding from being created ([Section 8](#8-creating-a-holding-for-a-blocked-account)); freezing a holding that already exists is what Lock is for (see [Section 10.4](#104-why-a-block-does-not-lock-an-existing-holding)). An issuer that needs to stop a blocked holder from moving an existing balance also sends `MPTokenIssuanceSet` with `tfMPTLock`, which it can submit in the same `Batch` as the `TokenBlock` to apply both atomically. Lock and unlock work on a blocked holder exactly as on any other holder. Removing the balance is done with the existing `Clawback` transaction, if the issuance has `lsfMPTCanClawback`.

`tfUnblock` only removes the block. It does not authorize the holding again (see [Section 10.5](#105-why-tfunblock-does-not-re-authorize)). On an issuance with `lsfMPTRequireAuth`, the issuer re-authorizes the holder explicitly, with `MPTokenAuthorize` and `Holder`, or with `TokenPreauth`, which also authorizes an existing `MPToken` ([Section 5.5.1](#551-pre-authorizing-an-existing-holder)).

### 6.6. Delegation

Both transactions are delegable under [XLS-75](../XLS-0075-permission-delegation/README.md), in the same way as the issuer's other holder controls: `Clawback` is delegable as a whole transaction, and per-holder lock and unlock are delegable through the `MPTokenIssuanceLock` and `MPTokenIssuanceUnlock` granular permissions. An issuer can therefore let a compliance account maintain its lists without holding the issuer's key.

Because pre-authorizing and blocking are separate transactions, the transaction-level permissions already keep the two directions apart: `TokenPreauth` grants access, and `TokenBlock` restricts it. An issuer can give an automated sanctions-screening account `TokenBlock` without also letting it pre-authorize holders.

Within `TokenBlock`, an issuer can also delegate creating blocks without delegating their removal, through one granular permission:

| Granular permission | Value   | Allowed flags | Allowed fields                |
| ------------------- | ------- | ------------- | ----------------------------- |
| `TokenBlockCreate`  | `65549` | none          | `MPTokenIssuanceID`, `Holder` |

So an issuer can grant only `TokenBlockCreate` to the screening account, and keep the ability to remove a block with the issuer or an account holding the transaction-level `TokenBlock` permission (see [Section 13.5](#135-delegation)).

There is no matching unblock-only permission. A granular permission lists the flags a delegated transaction may set, so one that allows `tfUnblock` would also allow the transaction without it, which creates a block. Removing a block is the more sensitive action in any case.

A delegated transaction behaves exactly like one sent by the issuer: `Account` is the issuer, the issuer's owner count and reserve change, and a block revokes an existing holding's authorization ([Section 6.5.1](#651-revoking-authorization)). As with any delegated transaction, the delegate pays the fee. The granular permission values are provisional and will be confirmed when the amendment is merged.

### 6.7. Example JSON

Blocking an account from an MPT issuance:

```json
{
  "TransactionType": "TokenBlock",
  "Account": "rISSUER......",
  "Holder": "rBLOCKED......",
  "MPTokenIssuanceID": "000005F398B624EBD06822198649C920C8B20ADB8EBE745E",
  "Fee": "10",
  "Sequence": 12346
}
```

Removing the block:

```json
{
  "TransactionType": "TokenBlock",
  "Account": "rISSUER......",
  "Flags": 1,
  "Holder": "rBLOCKED......",
  "MPTokenIssuanceID": "000005F398B624EBD06822198649C920C8B20ADB8EBE745E",
  "Fee": "10",
  "Sequence": 12349
}
```

## 7. Transaction: `MPTokenAuthorize` (Modified)

In this section, the holder is the `Account` sending the transaction when there is no `Holder` field (the holder opting in), and the `Holder` field when the issuer sends it.

### 7.1. Fields

No fields are added or changed. For the complete list of fields, see the [`MPTokenAuthorize` transaction documentation](https://xrpl.org/docs/references/protocol/transactions/types/mptokenauthorize).

### 7.2. Failure Conditions

All existing failure conditions still apply. When the amendment is enabled:

1. `tfMPTUnauthorize` is not set, and a `TokenBlock` entry exists for (holder, `MPTokenIssuanceID`) (`tecTOKEN_BLOCKED`).

This check is evaluated before every other protocol-level check, including the checks that the issuance and the holder's account exist and the existing `tecDUPLICATE` check. So:

- a blocked account trying to opt in always receives `tecTOKEN_BLOCKED`, whether or not it already has an `MPToken`; and
- an issuer cannot approve a blocked holder, including an address that has no account yet.

`tfMPTUnauthorize` is not affected:

- A blocked holder can still delete its `MPToken` to recover the reserve, subject to the existing conditions (zero balance, no escrowed amount, no confidential balance). This is allowed even if the issuer has locked the `MPToken`, which existing rules otherwise reject. It does not let the holder escape the lock, because the block prevents it from creating the `MPToken` again.
- An issuer can still send `tfMPTUnauthorize` for a blocked holder. It has no further effect, since the block already revoked the authorization ([Section 6.5.1](#651-revoking-authorization)).

### 7.3. State Changes

On success, if the holder is opting in (no `Holder` field, no `tfMPTUnauthorize`), the issuance has `lsfMPTRequireAuth`, and a `TokenPreauth` entry exists for the holder, the new `MPToken` is created with `lsfMPTAuthorized`. The holder does not wait for a second issuer transaction.

On an issuance without `lsfMPTRequireAuth`, a pre-authorization has no effect.

### 7.4. Example JSON

A blocked account attempting to opt in. This fails with `tecTOKEN_BLOCKED`, and no `MPToken` is created:

```json
{
  "TransactionType": "MPTokenAuthorize",
  "Account": "rBLOCKED......",
  "MPTokenIssuanceID": "000005F398B624EBD06822198649C920C8B20ADB8EBE745E",
  "Fee": "10",
  "Sequence": 1
}
```

## 8. Creating a Holding for a Blocked Account

`MPTokenAuthorize` is not the only way to obtain an `MPToken`. Several transactions create one implicitly for an account that receives the token. If only `MPTokenAuthorize` checked for blocks, a blocked account could obtain the token through any of these other paths.

When the amendment is enabled, no transaction may create an `MPToken` for an account that is blocked for that issuance. A transaction that checks whether an account may hold the token treats a blocked account that has no `MPToken` as not allowed to hold it, and fails with `tecTOKEN_BLOCKED`. This includes:

| Transaction                    | Effect on a blocked account with no `MPToken`                                                                                                         |
| ------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------- |
| `Payment`                      | Fails with `tecTOKEN_BLOCKED` when the blocked account is the destination.                                                                            |
| `OfferCreate`                  | Fails with `tecTOKEN_BLOCKED` when the blocked account would receive the token (`TakerPays`).                                                         |
| Offer crossing                 | A resting offer whose owner is blocked from the asset it receives is removed as unfunded instead of being crossed.                                    |
| `CheckCash`                    | Fails with `tecTOKEN_BLOCKED` when the blocked account cashes a check for the token.                                                                  |
| `EscrowCreate`, `EscrowFinish` | Fail with `tecTOKEN_BLOCKED` when the blocked account is the destination. The sender can still cancel the escrow after it expires.                    |
| `AMMWithdraw`                  | Fails with `tecTOKEN_BLOCKED` when the blocked account would withdraw the token. A blocked LP can still withdraw its share as the pool's other asset. |

`CheckCreate` does not check whether the destination can hold the token, and is unchanged. A check written to a blocked account can never be cashed.

A blocked account that already has an `MPToken` is not affected by this rule, and its balance can still move unless the issuer locks it (see [Section 6.5.1](#651-revoking-authorization)).

The one exception is `AMMClawback`. To claw back from an AMM pool, the issuer may need to recreate a holder's `MPToken` that the holder has since deleted. `AMMClawback` still does this for a blocked holder, so the issuer can recover its token, but the recreated `MPToken` is created with `lsfMPTLocked` and without `lsfMPTAuthorized`, since it only exists for the issuer to seize from.

## 9. Composition with Existing Controls

Together with the existing controls, an issuer can stop an account from opting in to, moving, or holding the token:

| Lifecycle stage            | Control                       | Effect on a blocked account                                |
| -------------------------- | ----------------------------- | ---------------------------------------------------------- |
| Opting in / acquiring      | Block (this specification)    | Cannot obtain an `MPToken` by any path.                    |
| Moving an existing balance | Lock (separate issuer action) | Cannot send or receive.                                    |
| Holding a balance          | Clawback                      | The issuer can remove the balance, if clawback is enabled. |

Before this amendment, the first stage has no control at all for a permissionless issuance.

## 10. Rationale

### 10.1. Why pre-authorizations and blocks are separate entry types and transactions

A pre-authorization and a block are opposite decisions, so they are recorded as two ledger entry types rather than as two flags on one entry, and each is managed by its own transaction:

- **Clarity for tooling and users.** An explorer, wallet, or compliance monitor can tell what an entry means from its type alone. A single entry named `TokenPreauth` that sometimes means "blocked" would be confusing.
- **Alignment with `DepositPreauth`.** `TokenPreauth` has the same shape as `DepositPreauth`: no flags, and the entry's existence is the pre-authorization. Each entry type is managed by a transaction of the same name, as `DepositPreauth` is, so a transaction never creates an entry of a different type than its name says.
- **Simpler transactions.** Each transaction only creates or deletes its own entry type, selected by a single flag, rather than one transaction choosing among four actions.
- **Delegation by direction.** Granting access and restricting it are different levels of trust. With separate transactions, the transaction-level permissions already keep them apart, so an issuer can delegate blocking without delegating pre-authorization ([Section 6.6](#66-delegation)).
- **Reuse.** A separate block entry type is a pattern that Deposit Authorization can adopt for blocking specific senders (see [Section 14.4](#144-blocking-for-deposit-authorization)).

A holder still has at most one state per token. The transactions enforce this (`TokenBlock` replaces a pre-authorization, and `TokenPreauth` fails on a blocked holder), and an invariant checks it. Replacing a pre-authorization with a block deletes one entry and creates the other in the same transaction, so the issuer's reserve does not change.

`TokenPreauth` only ever creates or deletes a `TokenPreauth` entry, and cannot overwrite a block, so a pre-authorization workflow can never accidentally remove a block.

### 10.2. Why new transactions instead of flags on `MPTokenIssuanceSet` or `MPTokenAuthorize`

Both existing transactions act on objects that already exist: `MPTokenIssuanceSet` changes an issuance or locks a holder's `MPToken`, and the issuer's `MPTokenAuthorize` approves a holder's existing `MPToken`. Pre-authorizations and blocks are made before any `MPToken` exists, often for an address that has no account yet, and each creates or deletes a separate issuer-owned entry with its own reserve. Adding them as flags would change what these transactions mean, rather than adding an option to them:

- **Existing delegations would silently widen.** Both transactions are delegable as a whole. An account already granted `MPTokenIssuanceSet` or `MPTokenAuthorize` would gain the power to block and unblock holders, or to pre-authorize them, as soon as the amendment is enabled, without the issuer having granted it. New transactions start with no delegates.
- **`MPTokenAuthorize` is sent by holders too.** The same transaction is the holder's opt-in. Mixing issuer-only list management into it makes its flags and failure conditions depend on who sends it, and it already requires the holder's account to exist (`tecNO_DST`), which a block must not.
- **Different failure conditions and state changes.** Each new action has its own preconditions (`tecDUPLICATE`, `tecNO_ENTRY`, reserve), works after the issuance is destroyed, and interacts with the other entry type ([Section 6.5](#65-state-changes)). As flags, these would be special cases inside transactions whose existing rules do not apply to them.
- **Extension to IOUs.** The same `TokenPreauth` and `TokenBlock` transactions can later cover IOUs with a `Currency` field ([Section 14.1](#141-ious)). Flags on MPT-only transactions could not, and IOUs would need a second, different interface.
- **Consistency with `DepositPreauth`,** where list management is a dedicated transaction rather than a flag on `AccountSet`.

### 10.3. Why blocks are per-token

A block names exactly one issuance. An issuer-wide block would either add a second lookup to every opt-in, or require enumerating all of the issuer's issuances to revoke existing authorizations, which is unbounded work in a single transaction. Per-issuance entries keep both the check and the revocation to one key lookup. An issuer with several tokens sends one `TokenBlock` transaction per token.

Blocks name a single address rather than a credential or domain because the primary use case, a sanctions list, is a list of addresses.

### 10.4. Why a block does not lock an existing holding

Block and Lock are separate controls with separate meanings. A block decides who may obtain a holding; Lock decides whether an existing holding may move. Keeping them separate means each has one clear effect, Lock keeps its existing semantics and flags, and an issuer can apply either one without the other. An issuer that wants both sends both, atomically if needed by placing them in one `Batch`.

Because a block does not lock, it does not depend on `lsfMPTCanLock`: an issuer can block accounts on any issuance.

A block does revoke authorization. On an issuance with `lsfMPTRequireAuth`, `lsfMPTAuthorized` is the issuer's affirmative approval of the holder, and leaving it set on a blocked, typically sanctioned, holder would be contradictory. It would also be inconsistent with replacing a pre-authorization: the block deletes the `TokenPreauth` entry, so it should not keep the authorization that entry granted. Authorization is the same decision a block makes, whether the account may hold the token, so revoking it is part of the block rather than a separate control.

### 10.5. Why `tfUnblock` does not re-authorize

Restoring access to a holder who was blocked should be a deliberate decision, so on an issuance that requires authorization the issuer re-authorizes it explicitly rather than having `tfUnblock` do it.

### 10.6. Why enforcement covers every path that creates a holding

Since MPTokensV2, an `MPToken` is created by several transactions besides `MPTokenAuthorize` (see [Section 8](#8-creating-a-holding-for-a-blocked-account)). A block that only checked `MPTokenAuthorize` could be bypassed by placing an offer to buy the token, or by having someone write a check or an escrow to the blocked address.

### 10.7. Why MPT only

The gap this addresses is specific to MPTs: an `MPToken` can only be created by the holder (or implicitly by a transaction that pays it), so an issuer has no object to act on before the holder opts in. An IOU issuer can already create a trustline to a known address and freeze it in advance. IOU support is still valuable for consistency across token standards, and is the first planned extension (see [Section 14.1](#141-ious)).

### 10.8. Why not Deposit Authorization

Deposit Authorization controls payments into the issuer's own account. Issuers may need to control who holds their token without controlling who may pay their address.

### 10.9. Why a dedicated result code: `tecTOKEN_BLOCKED`

| Code               | Value (tentative) | Meaning                                                                                                     |
| ------------------ | ----------------- | ----------------------------------------------------------------------------------------------------------- |
| `tecTOKEN_BLOCKED` | 203               | The transaction would give a token to, or authorize the holding of, an account that its issuer has blocked. |

It is returned by `MPTokenAuthorize` ([Section 7](#7-transaction-mptokenauthorize-modified)), by the transactions in [Section 8](#8-creating-a-holding-for-a-blocked-account), and never by the `TokenPreauth` or `TokenBlock` transactions themselves.

A dedicated code, rather than reusing `tecNO_PERMISSION` or `tecNO_AUTH`, makes enforcement auditable: an observer can tell from the transaction result alone that it failed because of a block, and confirm the block with a `ledger_entry` lookup.

## 11. Backwards Compatibility

- **New ledger entries and transactions:** the `TokenPreauth` and `TokenBlock` ledger entries and transactions are only recognized after the amendment is enabled.
- **Modified behavior:** the new failure conditions in [Section 7](#7-transaction-mptokenauthorize-modified) and [Section 8](#8-creating-a-holding-for-a-blocked-account) only apply when a `TokenBlock` entry exists, and entries can only exist after the amendment is enabled. No existing field is added or changed.
- **Existing authorization flows:** the issuer can still authorize holders with `MPTokenAuthorize` as before, except for holders it has blocked.

## 12. Test Plan

1. The `TokenPreauth` and `TokenBlock` transactions, with and without their flag, for every transition in [Section 6.5](#65-state-changes), including owner count and reserve, and that a holder is never both pre-authorized and blocked.
2. All failure conditions in [Section 5.4](#54-failure-conditions) and [Section 6.4](#64-failure-conditions).
3. A blocked account cannot opt in, with and without `lsfMPTRequireAuth`, and receives `tecTOKEN_BLOCKED`. Other accounts can still opt in.
4. Blocking an address before it is funded; the block applies once the account is created.
5. Blocking an existing holder does not lock it: the balance is kept and still moves both ways; lock, unlock, and clawback work as for any holder. On an issuance with `lsfMPTRequireAuth`, blocking clears `lsfMPTAuthorized` (including one granted through a pre-authorization), the issuer cannot authorize the holder while it is blocked, and after `TokenBlock` with `tfUnblock` the holder stays unauthorized until the issuer re-authorizes it.
6. `TokenBlock` succeeds on an issuance without `lsfMPTCanLock`, for an existing holder, a funded non-holder, and an unfunded address.
7. A blocked holder that the issuer has also locked can delete its `MPToken` once the balance is zero, and cannot create it again.
8. The issuer cannot approve a blocked holder, but can still revoke one's authorization.
9. Pre-authorization on a `lsfMPTRequireAuth` issuance, both before and after the holder opts in; no effect without `lsfMPTRequireAuth`.
10. Each path in [Section 8](#8-creating-a-holding-for-a-blocked-account): offers (resting and taking), `CheckCash`, `EscrowCreate`/`EscrowFinish`, `Payment`, `AMMWithdraw`, and `AMMClawback` recreating a locked, unauthorized `MPToken`.
11. Cleaning up entries after the issuance is destroyed; `AccountDelete` of the issuer and of a blocked holder.
12. `ledger_entry` by index and by `{holder, mpt_issuance_id}` for both `token_preauth` and `token_block`, and `account_objects` with each type.
13. Each invariant in [Section 3.7](#37-invariants) and [Section 4.7](#47-invariants).
14. Delegation ([Section 6.6](#66-delegation)): both transactions, with and without their flag, through their transaction-level permissions, including revoking authorization, reserve on the issuer, and fee on the delegate; permission for one transaction does not cover the other; `TokenBlockCreate` allows creating a block but not removing one, and covers neither `TokenPreauth` action; a delegate cannot act for an issuer that did not grant it permission; none of the permissions can be granted while the amendment is disabled.

## 13. Security Considerations

### 13.1. Scope of a block

A block applies only to the one issuance it names. It does not restrict XRP or any other token, and it is not an account-level freeze; no such primitive exists on the XRP Ledger. Documentation aimed at compliance teams and regulators should state this clearly.

A block also applies only to the address it names. It stops that address from holding the token, not from directing the token to another address. For example, a blocked account with shares in a vault for the token cannot `VaultWithdraw` to itself, but can withdraw with another account as the `Destination`. Likewise, a block does not stop the same party from using a new address. Linking new addresses to a blocked party is the job of the issuer's off-chain screening, which then blocks those addresses too; the block is the on-ledger enforcement of that list.

### 13.2. Reserve and spam

Only the issuer can create entries, and only the issuer pays their reserve. A blocked account cannot cause entries to be created. An issuer with a large list should expect a reserve proportional to the number of (holder, issuance) pairs.

### 13.3. Timing

A block takes effect in the ledger in which the `TokenBlock` transaction is applied, and is checked when an opt-in in that same ledger or any later one is applied. An account that obtained a holding in an earlier ledger, or earlier in the same ledger, keeps it: the block does not roll it back, and the issuer locks it if the balance must not move. Issuers should add accounts to their list promptly, and should block addresses before they are funded where possible.

### 13.4. Block takes precedence

`TokenBlock` can replace a pre-authorization with a block in one transaction; `TokenPreauth` can never remove a block. Removing a block is always an explicit `TokenBlock` with `tfUnblock`.

### 13.5. Delegation

Only a delegate with the transaction-level `TokenBlock` permission can remove a block. Issuers should grant the narrowest permission that fits each account, for example only `TokenBlockCreate` to an automated screening service, and grant `TokenBlock` only to an account they would trust to lift a sanctions block, or keep it with the issuer. Locking or unlocking a blocked holder's existing holding is not part of `TokenBlock`; it requires the separate `MPTokenIssuanceLock` or `MPTokenIssuanceUnlock` permission.

## 14. Future Extensions

These are expected to follow in later amendments. They are recorded here so that the entries and the transactions can be extended without redesign.

### 14.1. IOUs

- The `TokenPreauth` and `TokenBlock` ledger entries and transactions gain an optional `Currency` field; exactly one of `Currency` and `MPTokenIssuanceID` is present, and the ID hashes the issuer, `Holder`, and `Currency` in a key space of their own, since a `Currency` code does not identify its issuer.
- `TrustSet` fails with `tecTOKEN_BLOCKED` when a blocked account would create a trustline to the issuer for that currency, or when the issuer sets `tfSetfAuth` on a trustline with a blocked account. A blocked account can still modify or delete an existing trustline, so it can release the reserve once the balance is zero.
- As with MPTs, every other transaction that can create a trustline for the blocked account (for example, `CheckCash` and offer crossing) must also be covered.
- As with MPTs, `TokenBlock` does not freeze an existing trustline; the issuer freezes it separately if needed. Whether a block should clear `tfSetfAuth` on an existing trustline, as it clears `lsfMPTAuthorized` on an `MPToken`, is open.
- On an issuer with `lsfRequireAuth`, a pre-authorized holder's trustline is authorized when created or modified.

An IOU block should name a single `Currency`. A block covering all of an issuer's IOUs would make revoking authorization unbounded, since the holder may have a trustline to the issuer for every currency it issues (see [Section 10.3](#103-why-blocks-are-per-token)).

### 14.2. Credentials and domains

Pre-authorization (but not blocking) by credential ([XLS-70](../XLS-0070-credentials/README.md)) or domain ([XLS-80](../XLS-0080-permissioned-domains/README.md)): `TokenPreauth` gains optional `Credentials` and `DomainID` fields, with exactly one of `Holder`, `Credentials`, and `DomainID` present, and `TrustSet` / `MPTokenAuthorize` gain optional `CredentialIDs` and `DomainID` fields. A block always takes precedence over any such pre-authorization.

### 14.3. Issuer-wide pre-authorization

A `TokenPreauth` entry with no `MPTokenIssuanceID` (or `Currency`) that applies to all of the issuer's tokens. Blocks remain per-token ([Section 10.3](#103-why-blocks-are-per-token)).

### 14.4. Blocking for Deposit Authorization

Deposit Authorization could gain the same pattern: a separate block entry type, alongside `DepositPreauth`, that rejects payments from a specific sender even when the destination does not require deposit authorization. This would be a separate amendment, but it should use the same naming and semantics as `TokenBlock` so that the two features behave the same way.

## 15. Open Issues

1. **Name of the block entry and transaction.** This draft uses `TokenBlock` for both. Alternatives include `TokenDeny`, `TokenBlocklist`, and `DenyAuth`.
2. **Result code value.** The numeric value of `tecTOKEN_BLOCKED` will be assigned when the amendment is merged.

## Appendix A: FAQ

### A.1. Does the holder still send `MPTokenAuthorize` if it is pre-authorized?

Yes. Pre-authorization does not skip opt-in. On an issuance that requires authorization, that single holder transaction also authorizes the holding, so the issuer does not send a follow-up. If the holder opted in before being pre-authorized, the `TokenPreauth` transaction authorizes the existing holding.

### A.2. Can I still authorize holders the old way?

Yes. The issuer's `MPTokenAuthorize` with `Holder` still works for any holder that is not blocked.

### A.3. Does pre-authorization do anything for a token that doesn't require authorization?

No. Anyone can already hold such a token. Blocks apply whether or not the token requires authorization.

### A.4. How is blocking different from Lock and Clawback?

Lock restricts movement of a holding that already exists, and Clawback removes a balance that already exists. Blocking prevents the holding from being created at all. See [Section 9](#9-composition-with-existing-controls).

### A.5. Can a blocked account get the token some other way, for example through the DEX?

No. Every transaction that would create a holding for a blocked account fails or skips that account. See [Section 8](#8-creating-a-holding-for-a-blocked-account).

### A.6. Who owns the entries?

The issuer. `Account` is the issuer, which owns the entry and pays its reserve; `Holder` is the pre-authorized or blocked account. This matches `DepositPreauth`, not `MPToken`.

### A.7. How do I check an account's status for a token?

Look up `token_block` with `{holder, mpt_issuance_id}`: if it exists, the account is blocked. Otherwise look up `token_preauth` with the same fields: if it exists, the account is pre-authorized. At most one of the two exists.

### A.8. Why not store the blocked accounts on the `MPTokenIssuance`?

A list of thousands of addresses on one ledger entry is rewritten in full on every change and is limited by the maximum size of a ledger entry. Separate keyed entries are a single lookup to check and a single write to change.
