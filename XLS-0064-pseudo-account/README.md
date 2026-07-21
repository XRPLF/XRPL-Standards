<pre>
xls: 64
title: Pseudo-Account
description: A standard for a "pseudo-account" AccountRoot object to be associated with one or more ledger entries.
author: Vito Tumas (@Tapanito)
status: Draft
category: Amendment
proposal-from: https://github.com/XRPLF/XRPL-Standards/discussions/191
created: 2025-03-04
updated: 2026-06-22
</pre>

### Abstract

This document proposes a standard for a _pseudo-account_, an `AccountRoot` ledger entry that can be associated with one or more other ledger entries. A pseudo-account is designed to hold and/or issue assets on behalf of its associated entries, enabling protocol-level functionality that requires an on-ledger entity to manage funds.

### Motivation

The XRP Ledger is an account-based system where assets (XRP, IOUs, etc.) can only be held by an `AccountRoot` entry. However, several advanced protocols, such as Automated Market Makers (AMMs), lending pools, and vaults, require a ledger _object_ itself to hold and manage assets.

The [XLS-30 (AMM)](https://github.com/XRPLF/XRPL-Standards/tree/master/XLS-0030-automated-market-maker#readme) specification pioneered this concept by introducing a pseudo-account linked to each `AMM` instance. This allows the AMM to track its token balances and issue Liquidity Provider Tokens (`LPTokens`).

This specification formalizes and standardizes the requirements for an `AccountRoot` when it functions as a pseudo-account, ensuring a consistent and secure implementation across different protocols. It defines mandatory flags, a naming convention for linking fields, and the core invariants that any protocol using a pseudo-account must enforce.

### Specification

#### Ledger Entries

This specification defines a set of mandatory properties and fields for an `AccountRoot` ledger entry when it is used as a pseudo-account.

##### **`AccountRoot`**

###### **Object Identifier**

The address of the pseudo-account's `AccountRoot` must be derived deterministically and be difficult to predict before creation. This prevents malicious actors from front-running the creation transaction by pre-funding the address. The protocol creating the `AccountRoot` must ensure the derived address is unoccupied.

A nonce-based approach is used to generate the unique `AccountRoot` ID:

1. Initialize a nonce, $i$, to $0$.
2. Compute a candidate ID: `AccountID` = `SHA512-Half`($i$ || `ParentLedgerHash` || `<ObjectID>`).
3. Check if an `AccountRoot` with this `AccountID` already exists on the ledger.
4. If it exists, increment the nonce $i$ and repeat from step 2.
5. If it does not exist, the computed `AccountID` is used for the new pseudo-account.

###### **Fields**

| Field Name   | Constant | Required | Internal Type | Default Value | Description                                                                        |
| :----------- | :------: | :------: | :-----------: | :-----------: | :--------------------------------------------------------------------------------- |
| `<Object>ID` |   Yes    |   Yes    |   `HASH256`   |      N/A      | The unique identifier of the ledger object this pseudo-account is associated with. |
| `Flags`      |   Yes    |   Yes    |   `UINT32`    |      N/A      | A set of flags that must be set for a pseudo-account.                              |
| `Sequence`   |   Yes    |   Yes    |   `UINT32`    |      `0`      | The sequence number, which must be `0`.                                            |
| `RegularKey` |   Yes    |    No    |   `ACCOUNT`   |      N/A      | A regular key, which must not be set for a pseudo-account.                         |

A detailed description of these fields follows:

**`<Object>ID`**

This field links the pseudo-account to its parent ledger object. Any protocol introducing a pseudo-account must define a new, optional field on the `AccountRoot` object to store this ID. The field name must follow this convention:

- `<Object>` is the name of the associated ledger object (e.g., `AMM`, `Vault`). Names that are acronyms should be fully capitalized (`AMMID`). Otherwise, use PascalCase (`VaultID`).
- The suffix `ID` must always be appended.

**`Flags`**

The following flags must be set on a pseudo-account's `AccountRoot` and must be immutable:

| Flag Name          |  Hex Value   | Description                                                                                                                                                                        |
| :----------------- | :----------: | :--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `lsfDisableMaster` | `0x00040000` | Disables the master key pair, ensuring no entity can sign transactions directly for this account. Control is ceded entirely to protocol rules.                                     |
| `lsfDepositAuth`   | `0x01000000` | Requires authorization for deposits, typically meaning that funds can only be sent to this account via specific protocol transactions rather than standard `Payment` transactions. |

**`Sequence`**

The `Sequence` number of a pseudo-account must be initialized to `0` and must not be changed. This, combined with the disabled master key, prevents the account from ever submitting a transaction on its own behalf.

**`RegularKey`**

A `RegularKey` must not be set on a pseudo-account.

###### **Reserves**

The cost of creating a pseudo-account depends on whether it is owned and controlled by another account.

- **Owned Pseudo-Accounts:** For objects like a `Vault` where a single account owns and controls the associated pseudo-account, the transaction must increase the owner's XRP reserve by one increment. This is in addition to any other reserve requirements of the transaction (e.g., for the `Vault` object itself). The transaction fee is the standard network fee.

- **Unowned Pseudo-Accounts:** For objects like an `AMM` that are not owned by any account, the creation transaction must charge a special, higher-than-normal transaction fee. This fee must be at least the value of one incremental owner reserve (currently **2 XRP**, subject to change via Fee Voting). This amount is burned, compensating for the permanent ledger space without tying the reserve to a specific owner.

###### **Deletion**

A pseudo-account must be deleted together with the associated object.

###### **Freeze Handling**

Freeze semantics for pseudo-accounts differ from those of regular accounts, therefore protocols using a pseudo-account must enforce the following rules for any transaction that moves assets into or out of the pseudo-account.

**Deposits (external account → pseudo-account)**

A deposit must be rejected if any of the following conditions hold:

| Condition                                                                           | Code                      |
| :---------------------------------------------------------------------------------- | :------------------------ |
| The asset is globally frozen                                                        | `tecFROZEN` / `tecLOCKED` |
| If the asset is a Vault Share, the underlying asset of the share if frozen / locked | `tecLOCKED`               |
| The depositor is regularly frozen for the asset                                     | `tecFROZEN` / `tecLOCKED` |
| The pseudo-account is regularly frozen for the asset                                | `tecFROZEN` / `tecLOCKED` |

A freeze on the pseudo-account blocks deposits. Unlike regular accounts — where a frozen counterparty can still redeem to the issuer — a pseudo-account cannot initiate a redemption on its own. Allowing deposits into a frozen pseudo-account would trap the depositor's funds.

**Withdrawals (pseudo-account → destination)**

A withdrawal must be rejected if any of the following conditions hold, evaluated in order:

| Condition                                                                           | Code                                                                                                                               |
| :---------------------------------------------------------------------------------- | :--------------------------------------------------------------------------------------------------------------------------------- |
| The destination is the asset issuer                                                 | **Always allowed** — return `tesSUCCESS` immediately, bypassing all remaining checks. The issuer can always receive its own token. |
| The asset is globally frozen                                                        | `tecFROZEN` / `tecLOCKED`                                                                                                          |
| If the asset is a Vault Share, the underlying asset of the share if frozen / locked | `tecLOCKED`                                                                                                                        |
| The pseudo-account (source) is regularly frozen for the asset                       | Reject: `tecFROZEN` / `tecLOCKED`                                                                                                  |
| The submitter is frozen for the asset **and** the submitter is not the destination  | Reject: `tecFROZEN` / `tecLOCKED`                                                                                                  |
| The destination is deep frozen for the asset                                        | Reject: `tecFROZEN` / `tecLOCKED`                                                                                                  |

Rule 5 intentionally skips the submitter freeze check when the submitter and the destination are the same account (self-withdrawal). A regular freeze on the submitter must not block them from recovering their own funds from the pool.

Rule 6 uses deep freeze for the destination rather than a regular freeze, because a regular freeze on the destination does not prevent the destination from receiving; only deep freeze does.

**MPT-specific rules**

For Multi-Purpose Tokens (MPTs), the `lsfMPTLocked` flag on either the `MPTokenIssuance` or the holder's `MPToken` is equivalent to deep-frozen semantics. This affects Rule 3: for IOUs a regular individual freeze does not block self-withdrawal, but for MPTs a locked holder is always blocked from self-withdrawal because locked and deep-frozen are the same state.

Rule 1 (issuer destination) applies to MPTs in the same way as IOUs — a withdrawal to the asset issuer bypasses all lock checks.

###### **Invariants**

The following invariants must hold true for any `AccountRoot` entry functioning as a pseudo-account:

- The ledger object identified by the `<Object>ID` field must exist.
- Exactly one `<Object>ID` field must be present on the `AccountRoot` (e.g., an account cannot be linked to both an `AMMID` and a `VaultID`).
- The `lsfDisableMaster` and `lsfDepositAuth` flags must always be set.
- The `Sequence` number must always be `0`, and must never change.
  - AMM pseudo-accounts created under old rules will have a sequence number set to the index of the ledger they were created in. They still must never change.
- A `RegularKey` must not be set.

### Security Considerations

The design of pseudo-accounts includes several critical security features:

- **No Direct Control:** The mandatory `lsfDisableMaster` flag and the absence of a `RegularKey` ensure that no user can directly control the pseudo-account or its assets. All fund movements are governed exclusively by the rules of the associated protocol.
- **Transaction Prevention:** A `Sequence` of `0` makes it impossible for the account to submit transactions, preventing any misuse of the account itself.
- **Address Front-running Prevention:** The deterministic but unpredictable method for generating the account address prevents attackers from guessing the address and sending funds to it before it is officially created by the protocol.
- **Controlled Deposits:** The `lsfDepositAuth` flag prevents arbitrary `Payment` transactions from being sent to the account, ensuring that its balances can only be modified through legitimate protocol transactions.
