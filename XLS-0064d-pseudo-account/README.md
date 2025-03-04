<pre>    
Title:        <b>Pseudo-Account</b>
Type:         <b>draft</b>
Revision:     <b>1</b> (2025-03-04)

<hr> Authors:    
  <a href="mailto:vtumas@ripple.com">Vytautas Vito Tumas</a>

Affiliation: 
  <a href="https://ripple.com">Ripple</a>
</pre>

# Pseudo-Account

## _Abstract_

In this document, we propose a standard for a _pseudo-account_, an `AccountRoot` object that can be associated with one or more other ledger entries to hold and/or issue assets on behalf of the associated entries.

## 1. Introduction

The XRP Ledger is an account-based blockchain in which assets—such as XRP, IOUs, or MPT—can only be held by an account represented by an `AccountRoot` ledger entry. However, certain use cases, such as Automated Market Makers (AMM), Single Asset Vaults, and the Lending Protocol—require assets to be transferable to and from an object.

The [XLS-30](https://github.com/XRPLF/XRPL-Standards/tree/master/XLS-0030-automated-market-maker#readme) specification introduced the `AMMID` field in the `AccountRoot` ledger entry. This field associates a _pseudo-account_ with an `AMM` instance, allowing it to track XRP and token balances in the pool and issue `LPTokens` on behalf of the `AMM` instance.

This specification formalises the requirements for an `AccountRoot` when used as a _pseudo-account_. Specifically, it defines:

- A set of flags that must be enabled.
- A naming convention for the field identifying the object the `AccountRoot` is associated with.
- Minimum requirements for any protocol implementing a _pseudo-account_.

## 2. Ledger Entries

### 2.1. `AccountRoot` Ledger Entry

#### 2.1.1. Object Identifier

The address of the `AccountRoot` must be randomised to prevent users from identifying and funding the address before its creation. The protocol that creates an `AccountRoot` must ensure the account address is unoccupied.

The unique ID of the **`AccountRoot`** object, a.k.a. **`AccountRootID`** is computed as follows:

- for (i = 0; i <= 256; i--)
  - Compute `AccountRootID` = `SHA512-Half`(i || [Parent Ledger Hash](https://xrpl.org/ledgerhashes.html) || `<Object>ID>`)
  - If the computed `AccountRootID` exists, repeat
    - else, return `AccountRootID`

#### 2.1.2. Fields

| Field Name   | Modifiable? | Required? | JSON Type | Internal Type | Default Value | Description                                                                                                 |
| ------------ | :---------: | :-------: | :-------: | :-----------: | :-----------: | :---------------------------------------------------------------------------------------------------------- |
| `<Object>ID` |    `N/A` |   `no` | `string` |   `HASH256` |     `N/A` | The object identifier the `pseudo-account` is associated with.                                              |
| `Flags` |    `no` |   `yes` | `number` |   `UINT32` |     `N/A` | A set of flags that must be set for a `pseudo-account`.                                                     |
| `Sequence` |    `no` |   `yes` | `number` |   `UINT32` |      `0` | The sequence number of the `pseudo-account`.                                                                |
| `RegularKey` |    `no` |   `yes` | `string` |  `ACCOUNTID` |     `N/A` | The address of a key pair that can be used to sign transactions for this account instead of the master key. |

##### 2.1.2.1. `<Object>ID`

The `<Object>ID` field uniquely identifies the ledger entry associated with an account. Any protocol introducing a `pseudo-account` must include a new, optional `<Object>ID` field.

The naming convention for this field follows these rules:

- `<Object>` represents the name of the related object:
  - All letters must be capitalised if the name is an acronym (e.g., `AMM`).
  - Otherwise, capitalise the first letter of each noun (e.g., `Vault` or `LoanBroker`).
- `ID` must always be appended as a suffix.

##### 2.1.2.2. `Flags`

The following flags must be set for a `pseudo-account`:

| Flag Name          | Flag Value | Modifiable? |                                        Description                                        |
| ------------------ | :--------: | :---------: | :---------------------------------------------------------------------------------------: |
| `lsfDisableMaster` |   `0x01` |    `No` | Ensure that no one can control the account directly and send transactions on its behalf.  |
| `lsfDepositAuth` |  `0x001` |    `No` | Ensure that the only way to add funds to the account is by using a `deposit` transaction. |



##### 2.1.2.3. `Sequence`  
The `Sequence` number of a` _pseudo-account_` **must** be `0`. A _pseudo-account_ cannot submit valid transactions.  

##### 2.1.2.4. `RegularKey`  
A _pseudo-account_ **must not** have a `RegularKey` set.  

#### 2.1.3. Cost  

A transaction that creates a `pseudo-account` must incur a higher-than-usual transaction fee to deter ledger spam. Additionally, the transaction must destroy at least the incremental owner reserve amount, currently `2 XRP`.  

#### 2.1.4. Invariant  

The following invariants **must** hold for a _pseudo-account_:  
- The object identified by `<Object>ID` **must** exist on the ledger.  
- Exactly one `<Object>ID` **must** be set (e.g., a _pseudo-account_ cannot have both `AMMID` and `VaultID` at the same time).  
- The `lsfDepositAuth` and `lsfDisableMaster` flags **must** be set.  
- The `Sequence` number **must** be `0`.  
- The `RegularKey` **must not** be set.  
