<pre>    
Title:        <b>Single Asset Tokenized Vault</b>
Revision:     <b>1</b> (2024-10-18)

<hr>Authors:    
  <a href="mailto:vtumas@ripple.com">Vytautas Vito Tumas</a>
  <a href="mailto:amalhotra@ripple.com">Aanchal Malhotra</a>

Affiliation:
  <a href="https://ripple.com">Ripple</a>
</pre>

# Single Asset Vault

## _Abstract_

A Single Asset Vault is a new on-chain primitive for aggregating assets from one or more depositors, and making the assets available for other on-chain protocols. The Single Asset Vault uses [Multi-Purpose-Token](https://github.com/XRPLF/XRPL-Standards/tree/master/XLS-0033d-multi-purpose-tokens) to represent ownership shares of the Vault. The Vault serves diverse purposes, such as lending markets, aggregators, yield-bearing tokens, asset management, etc. The Single Asset Vault decouples the liquidity provision functionality from the specific protocol logic.

## Index

- [**1. Introduction**](#1-introduction)
  - [**1.1. Feature Overview**](#11-overview)
  - [**1.2. Terminology**](#12-terminology)
  - [**1.3. Actors**](#13-actors)
  - [**1.4 Connecting to the Vault**](#14-connecting-to-the-vault)
- [**2. Ledger Entires**](#2-ledger-entries)
  - [**2.1. `Vault` Ledger Entry**](#21-vault-ledger-entry)
    - [**2.1.1. Object Identifier**](#211-object-identifier)
    - [**2.1.2. Fields**](#212-fields)
    - [**2.1.3. Vault _pseudo-account_**](#213-vault-_pseudo-account_)
    - [**2.1.4. Ownership**](#214-ownership)
    - [**2.1.5. Owner Reserve**](#215-owner-reserve)
    - [**2.1.6. Vault Shares**](#216-vault-shares)
    - [**2.1.7. Exchange Algorithm**](#217-exchange-algorithm)
- [**3. Transactions**](#3-transactions)
  - [**3.1. VaultCreate, VaultSet & VaultDelete Transactions**](#31-vaultcreate-vaultset-vaultdelete-transactions)
    - [**3.1.1. VaultCreate Transaction**](#311-vaultcreate-transaction)
    - [**3.1.2. VaultSet Transaction**](#312-vaultset-transaction)
    - [**3.1.3. VaultDelete Transaction**](#313-vaultdelete-transaction)
  - [**3.2. VaultDeposit & VaultWithdraw Transactions**](#32-vaultdeposit-and-vaultwithdraw-transactions)
    - [**3.2.1. VaultDeposit Transaction**](#321-vaultdeposit-transaction)
    - [**3.2.2. VaultWithdraw Transaction**](#322-vaultwithdraw-transaction)
  - [**3.3. VaultClawback Transaction**](#33-vaultclawback-transaction)
- [**4. API**](#4-api)
- [Appendix](#appendix)

## 1. Introduction

### 1.1 Overview

The **Single Asset Vault** is an on-chain object that aggregates assets from one or more depositors and represents ownership through shares. Other protocols, such as the [Lending Protocol](https://github.com/XRPLF/XRPL-Standards/discussions/190), can access these assets via the vault, whether or not they generate yield. Currently, other protocols must be created by the same Account that created the Vault. However, this may change in the future.

The specification introduces a new `Vault` ledger entry, which contains key details such as available assets, shares, total value, and other relevant information.

The specification includes the following transactions:

**Vault Management**:

- **`VaultCreate`**: Creates a new Vault object.
- **`VaultSet`**: Updates an existing Vault object.
- **`VaultDelete`**: Deletes an existing Vault object.

**Asset Management**:

- **`VaultDeposit`**: Deposits a specified number of assets into the Vault in exchange for shares.
- **`VaultWithdraw`**: Withdraws a specified number of assets from the Vault in exchange for shares.

Additionally, an issuer can perform a **Clawback** operation:

- **`VaultClawback`**: Allows the issuer of an IOU or MPT to claw back funds from the vault, as outlined in the [Clawback documentation](https://xrpl.org/docs/use-cases/tokenization/stablecoin-issuer#clawback).

#### 1.1.1 Vault Ownership and Management

A Single Asset Vault is owned and managed by an account called the **Vault Owner**. The account is reponsible for creating, updating and deleting the Vault object.

#### 1.1.2 Access Control

A Single Asset Vault can be either public or private. Any depositor can deposit and redeem liquidity from a public vault, provided they own sufficient shares. In contrast, access to private shares is controlled via [Permissioned Domains](https://github.com/XRPLF/XRPL-Standards/discussions/228), which use on-chain [Credentials](https://github.com/XRPLF/XRPL-Standards/tree/master/XLS-0070d-credentials) to manage access to the vault. Only depositors with the necessary credentials can deposit assets to a private vault. To prevent Vault Owner from locking away depositor funds, any shareholder can withdraw funds.

#### 1.1.3 Yield Bearing Shares

Shares represent the ownership of a portion of the vault's assets. On-chain shares are represented by a [Multi-Purpose Token](https://github.com/XRPLF/XRPL-Standards/tree/master/XLS-0033d-multi-purpose-tokens). When creating the vault, the Vault Owner can configure the shares to be non-transferable. Non-transferable shares cannot be transferred to any other account -- they can only be redeemed. If the vault is private, shares can be transferred and used in other DeFi protocols as long as the receiving account is authorized to hold the shares. The vault's shares may be yield-bearing, depending on the protocol connected to the vault, meaning that a holder may be able to withdraw more (or less) liquidity than they initially deposited.

### 1.2 Terminology

- **Vault**: A ledger entry for aggregating liquidity and providing this liquidity to one or more accessors.
- **Asset**: The currency of a vault. It is either XRP, a [Fungible Token](https://xrpl.org/docs/concepts/tokens/fungible-tokens/) or a [Multi-Purpose Token](https://github.com/XRPLF/XRPL-Standards/tree/master/XLS-0033d-multi-purpose-tokens).
- **Share**: Shares represent the depositors' portion of the vault's assets. Shares are a [Multi-Purpose Token](https://github.com/XRPLF/XRPL-Standards/tree/master/XLS-0033d-multi-purpose-tokens) created by the _pseudo-account_ of the vault.
  **Protocol Instance**: A separate XRP Ledger protocol requiring access to aggregated liquidity.

### 1.3 Actors

- **Vault Owner**: An account responsible for creating and deleting The Vault.
- **Depositor**: An entity that deposits and withdraws assets to and from the vault.

### 1.4 Connecting to the Vault

A protocol connecting to a Vault must track its debt. Furthermore, the updates to the Vault state when funds are removed or added back must be handled in the transactors of the protocol. For an example, please refer to the [Lending Protocol](https://github.com/XRPLF/XRPL-Standards/discussions/190) specification.

[**Return to Index**](#index)

## 2. Ledger Entries

### 2.1 `Vault` Ledger Entry

The **`Vault`** ledger entry describes the state of the tokenized vault.

#### 2.1.1 Object Identifier

The key of the `Vault` object is the result of [`SHA512-Half`](https://xrpl.org/docs/references/protocol/data-types/basic-data-types/#hashes) of the following values concatenated in order:

- The `Vault` space key `0x0056` (capital V)
- The `AccountID`(https://xrpl.org/docs/references/protocol/binary-format/#accountid-fields) of the account submitting the `VaultSet`transaction, i.e.`VaultOwner`.
- The transaction `Sequence` number. If the transaction used a [Ticket](https://xrpl.org/docs/concepts/accounts/tickets/), use the `TicketSequence` value.

#### 2.1.2 Fields

A vault has the following fields:

| Field Name             | Modifiable? |     Required?      |     JSON Type      | Internal Type | Default Value | Description                                                                                       |
| ---------------------- | :---------: | :----------------: | :----------------: | :-----------: | :-----------: | :------------------------------------------------------------------------------------------------ |
| `LedgerEntryType`      |    `N/A`    | :heavy_check_mark: |      `string`      |   `UINT16`    |   `0x0081`    | Ledger object type.                                                                               |
| `LedgerIndex`          |    `N/A`    | :heavy_check_mark: |      `string`      |   `UINT16`    |     `N/A`     | Ledger object identifier.                                                                         |
| `Flags`                |    `Yes`    | :heavy_check_mark: |      `string`      |   `UINT32`    |       0       | Ledger object flags.                                                                              |
| `PreviousTxnID`        |    `N/A`    | :heavy_check_mark: |      `string`      |   `HASH256`   |     `N/A`     | Identifies the transaction ID that most recently modified this object.                            |
| `PreviousTxnLgrSeq`    |    `N/A`    | :heavy_check_mark: |      `number`      |   `UINT32`    |     `N/A`     | The sequence of the ledger that contains the transaction that most recently modified this object. |
| `Sequence`             |    `N/A`    | :heavy_check_mark: |      `number`      |   `UINT32`    |     `N/A`     | The transaction sequence number that created the vault.                                           |
| `OwnerNode`            |    `N/A`    | :heavy_check_mark: |      `number`      |   `UINT64`    |     `N/A`     | Identifies the page where this item is referenced in the owner's directory.                       |
| `Owner`                |    `No`     | :heavy_check_mark: |      `string`      |  `AccountID`  |     `N/A`     | The account address of the Vault Owner.                                                           |
| `Account`              |    `N/A`    | :heavy_check_mark: |      `string`      |  `ACCOUNTID`  |     `N/A`     | The address of the Vaults _pseudo-account_.                                                       |
| `Data`                 |    `Yes`    |                    |      `string`      |    `BLOB`     |     None      | Arbitrary metadata about the Vault. Limited to 256 bytes.                                         |
| `Asset`                |    `No`     | :heavy_check_mark: | `string or object` |    `ISSUE`    |     `N/A`     | The asset of the vault. The vault supports `XRP`, `IOU` and `MPT`.                                |
| `AssetsTotal`          |    `N/A`    | :heavy_check_mark: |      `number`      |   `NUMBER`    |       0       | The total value of the vault.                                                                     |
| `AssetsAvailable`      |    `N/A`    | :heavy_check_mark: |      `number`      |   `NUMBER`    |       0       | The asset amount that is available in the vault.                                                  |
| `LossUnrealized`       |    `N/A`    | :heavy_check_mark: |      `number`      |   `NUMBER`    |       0       | The potential loss amount that is not yet realized expressed as the vaults asset.                 |
| `AssetsMaximum`        |    `Yes`    |                    |      `number`      |   `NUMBER`    |       0       | The maximum asset amount that can be held in the vault. Zero value `0` indicates there is no cap. |
| `Share`                |    `N/A`    | :heavy_check_mark: |      `object`      |     `MPT`     |       0       | The identifier of the share MPTokenIssuance object.                                               |
| `WithdrawalPolicy`     |    `No`     | :heavy_check_mark: |      `string`      |    `UINT8`    |     `N/A`     | Indicates the withdrawal strategy used by the Vault.                                              |
| `PermissionedDomainID` |    `No`     |                    |      `string`      |   `HASH256`   |     None      | The permissioned domain identifier of the Vault. This value is ignored if the vault is public.    |

##### 2.1.2.1 Flags

The `Vault` object supports the following flags:

| Flag Name         | Flag Value | Modifiable? |                 Description                  |
| ----------------- | :--------: | :---------: | :------------------------------------------: |
| `lsfVaultPrivate` |  `0x0001`  |    `No`     | If set, indicates that the vault is private. |

#### 2.1.3 Vault `_pseudo-account_`

An AccountRoot entry holds the XRP, IOU or MPT deposited into the vault. It also acts as the issuer of the vault's shares. The _pseudo-account_ follows the XLS-64d specification for pseudo accounts. The `AccountRoot` object is created when creating the `Vault` object.

#### 2.1.4 Ownership

The `Vault` objects are stored in the ledger and tracked in an [Owner Directory](https://xrpl.org/docs/references/protocol/ledger-data/ledger-entry-types/directorynode) owned by the account submitting the `VaultSet` transaction. Furthermore, to facilitate `Vault` object lookup from the vault shares, the object is also tracked in the `OwnerDirectory` of the _`pseudo-account`_.

#### 2.1.5 Owner Reserve

The `Vault` object costs one reserve fee per object created:

- The `Vault` object itself.
- The `MPTokenIssuance` associated with the shares of the Vault.

#### 2.1.6 Vault Shares

Shares represent the portion of the Vault assets a depositor owns. Vault Owners set the currency code of the share and whether the token is transferable during the vault's creation. These two values are immutable. The share is represented by a [Multi-Purpose Token](https://github.com/XRPLF/XRPL-Standards/tree/master/XLS-0033d-multi-purpose-tokens). The MPT is issued by the vault's pseudo-account.

##### 2.1.6.1 `MPTokenIssuance`

The `MPTokenIssuance` object represents the share on the ledger. It is created and deleted together with the `Vault` object.

###### 2.1.6.1.1 `MPTokenIssuance` Values

Here’s the table with the headings "Field," "Description," and "Value":

| **Field**         | **Description**                                        | **Value**            |
| ----------------- | ------------------------------------------------------ | -------------------- |
| `Issuer`          | The AccountID of the Vault's _pseudo-account_.         | _pseudo-account_ ID  |
| `MaximumAmount`   | No limit to the number of shares that can be issued.   | `0xFFFFFFFFFFFFFFFF` |
| `TransferFee`     | The fee paid to transfer the shares.                   | 0                    |
| `MPTokenMetadata` | Arbitrary metadata about the share MPT, in hex format. | -                    |

**Flags**

The following flags are set based on whether the shares are transferable and if the vault is public or private.
| **Condition** | **Transferable** | **Non-Transferable** |
| ----------------- | -------------------------------------------------------------------------------------- | ------------------- |
| **Public Vault** | `lsfMPTCanEscrow` <br> `lsfMPTCanTrade`<br> `lsfMPTCanTransfer` | No Flags |
| **Private Vault** | `lsfMPTCanEscrow`<br> `lsfMPTCanTrade`<br> `lsfMPTCanTransfer`<br> `lsfMPTRequireAuth` | `lsfMPTRequireAuth` |

##### 2.1.6.2 `MPToken`

The `MPToken` object represents the amount of shares held by a depositor. It is created when the account deposits liquidity into the vault and is deleted when a depositor redeems (or transfers) all shares.

###### 2.1.6.2.1 `MPToken` Values

The `MPToken` values should be set as per the `MPT` [specification](https://github.com/XRPLF/XRPL-Standards/tree/master/XLS-0033d-multi-purpose-tokens#2122-fields).

| **Condition**     | **Transferable**   | **Non-Transferable** |
| ----------------- | ------------------ | -------------------- |
| **Public Vault**  | No Flags           | `lsfMPTAuthorized`   |
| **Private Vault** | `lsfMPTAuthorized` | `lsfMPTAuthorized`   |

#### 2.1.7 Exchange Algorithm

Exchange Algorithm refers to the logic that is used to exchange assets into shares and shares into assets. This logic is executed when depositing or redeeming liquidity. A Vault comes with the default exchange algorithm, which is detailed below.

##### 2.1.7.1 Unrealized Loss

A well-informed depositor may learn of an incoming loss and redeem their shares early, causing the remaining depositors to bear the full loss. To discourage such behaviour, we introduce a concept of "paper loss," captured by the `Vault` object's `LossUnrealized` attribute. The "paper loss" captures a potential loss the vault may experience and thus temporarily decreases the vault value. Only a protocol connected to the `Vault` may increase or decrease the `LossUnrealized` attribute.

The "paper loss" temporarily decreases the vault value. A malicious depositor may take advantage of this to deposit assets at a lowered price and withdraw them once the price increases.

Consider a vault with a total value of $1.0m and total shares of $1.0m. Assume the "paper loss" for the vault is $900k. The new exchange rate is as follows:

$$
exchangeRate = \frac{AssetsTotal - LossUnrealized}{SharesTotal}
$$

$$
exchangeRate = \frac{1,000,000 - 900,000}{1,000,000} = 0.1
$$

After the "paper loss" is cleared, the new effective exchange rate would be as follows:

$$
exchangeRate = \frac{AssetsTotal}{SharesTotal}
$$

$$
exchangeRate = \frac{1,000,000}{1,000,000} = 1.0
$$

A depositor could deposit $100k assets at a 0.1 exchange rate and get 1.0m shares. Once the "paper loss" is cleared, their shares would be worth $1.0m.

To account for this problem, the Vault must use two different exchange rate models: one for depositing assets and one for withdrawing them.

##### 2.1.7.2 Exchange Rate Algorithms

**Variables**

The following variables define the Vault balance:

- $\Gamma_{share}$ - the total number of shares issued by the vault.
- $\Gamma_{asset}$ - the total assets in the vault, including any future yield.

- $\Delta_{asset}$ - the change in the total amount of assets after a deposit, withdrawal, or redemption.
- $\Delta_{share}$ - che change in the total amount of shares after a deposit, withdrawal, or redemption.

- $\iota$ - the unrealized loss of the vault.

###### 2.1.7.2.1 **Deposit**

We compute the number of shares ($\Delta_{share}$) a depositor will receive as follows:

$$\Delta_{share} = \Delta_{asset} \times \frac{\Gamma_{share}}{\Gamma_{asset} + 0^{\Gamma_{asset}}} $$

The following equations govern the updated vault composition after a successful deposit:

- $\Gamma_{asset} = \Gamma_{asset} + \Delta_{asset}$ New balance of assets in the vault.
- $\Gamma_{share} = \Gamma_{share} + \Delta_{share}$ New share balance in the vault.

###### 2.1.7.2.2 **Redeem**

We compute the number of assets ($\Delta_{asset}$) returned by burning $\Delta_{share}$ as follows:

$$\Delta_{asset} = \Delta_{share} \times \frac{\Gamma_{asset} - \iota}{\Gamma_{share} + 0^{\Gamma_{share}}} $$

The following equations govern the updated vault composition after a successful redemption:

- $\Gamma_{asset} = \Gamma_{asset} - \Delta_{asset}$ New balance of assets in the vault.
- $\Gamma_{share} = \Gamma_{share} - \Delta_{share}$ New share balance in the vault.

###### 2.1.7.2.3 **Withdraw**

We compute the number of shares to burn to withdraw $\Delta_{asset}$ as follows:

$$\Delta_{share} = \Delta_{asset} \times \frac{\Gamma_{share}}{\Gamma_{asset} - \iota + 0^{\Gamma_{asset}}} $$

The following equations govern the updated vault composition after a successful withdrawal:

- $\Gamma_{asset} = \Gamma_{asset} - \Delta_{asset}$ New balance of assets in the vault.
- $\Gamma_{share} = \Gamma_{share} - \Delta_{share}$ New share balance in the vault.

##### 2.1.7.2 Withdrawal Policy

Withdrawal policy controls the logic used when removing liquidity from a vault. Each strategy has its own implementation, but it can be used in multiple vaults once implemented. Therefore, different vaults may have different withdrawal policies. The specification introduces the following options:

###### 2.1.7.2.1 `first-come-first-serve`

The First Come, First Serve strategy treats all requests equally, allowing a depositor to redeem any amount of assets provided they have a sufficient number of shares.

#### 2.1.7 Frozen Assets

The issuer of the Vaults asset may enact a freeze either through a [Global Freeze](https://xrpl.org/docs/concepts/tokens/fungible-tokens/freezes/#global-freeze) for IOUs or [locking MPT](https://github.com/XRPLF/XRPL-Standards/tree/master/XLS-0033d-multi-purpose-tokens#21122-flags). When the vaults asset is frozen, it can only be withdrawn by specifying the `Destination` account as the `Issuer` of the asset. Similarly, a frozen asset _may not_ be deposited into a vault. Furthermore, when the asset of a vault is frozen, the shares corresponding to the asset may not be transferred.

[**Return to Index**](#index)

## 3. Transactions

All transactions introduced by this proposal incorporate the [common transaction fields](https://xrpl.org/docs/references/protocol/transactions/common-fields) that are shared by all transactions. Standard fields are only documented in this proposal if needed because this proposal introduces new possible values for such fields.

### 3.1 `VaultCreate`, `VaultSet`, `VaultDelete` transactions

The `Vault` object is managed with `VaultCreate`, `VaultSet` and `VaultDelete` transactions.

#### 3.1.1 `VaultCreate` Transaction

The `VaultCreate` transaction creates a new `Vault` object.

| Field Name             |     Required?      |     JSON Type      | Internal Type |      Default Value       | Description                                                                     |
| ---------------------- | :----------------: | :----------------: | :-----------: | :----------------------: | :------------------------------------------------------------------------------ |
| `TransactionType`      | :heavy_check_mark: |      `string`      |   `Uint16`    |           `58`           | The transaction type.                                                           |
| `Flags`                | :heavy_check_mark: |      `string`      |   `Uint32`    |            0             | Specifies the flags for the Vault.                                              |
| `Data`                 |                    |      `string`      |    `Blob`     |                          | Arbitrary Vault metadata, limited to 256 bytes.                                 |
| `Asset`                | :heavy_check_mark: | `string or object` |    `Issue`    |          `N/A`           | The asset (`XRP`, `IOU` or `MPT`) of the Vault.                                 |
| `AssetsMaximum`        |                    |      `number`      |   `Uint64`    |            0             | The maximum asset amount that can be held in a vault.                           |
| `MPTokenMetadata`      |                    |      `string`      |    `Blob`     |                          | Arbitrary metadata about the share `MPT`, in hex format, limited to 1024 bytes. |
| `WithdrawalPolicy`     |                    |      `string`      |    `UINT8`    | `strFirstComeFirstServe` | Indicates the withdrawal strategy used by the Vault.                            |
| `PermissionedDomainID` |                    |      `string`      |   `Hash256`   |                          | The `PermissionedDomain` object ID associated with this Vault object.           |

##### 3.1.1.1 Flags

| Flag Name                     | Flag Value | Description                                                                              |
| ----------------------------- | :--------: | :--------------------------------------------------------------------------------------- |
| `tfVaultPrivate`              |  `0x0001`  | Indicates that the vault is private. It can only be set during Vault creation.           |
| `tfVaultShareNonTransferable` |  `0x0002`  | Indicates the vault share is non-transferable. It can only be set during Vault creation. |

###### 3.1.1.2 WithdrawalPolicy

The type indicates the withdrawal strategy supported by the vault. The following values are supported:

| Strategy Name            |  Value   |                        Description                        |
| ------------------------ | :------: | :-------------------------------------------------------: |
| `strFirstComeFirstServe` | `0x0001` | Requests are processed on a first-come-first-serve basis. |

##### 3.1.1.3 Transaction Fees

The transaction creates an `AccountRoot` object for the `_pseudo-account_`. Therefore, the transaction [must destroy](https://github.com/XRPLF/XRPL-Standards/discussions/191) one incremental owner reserve amount.

##### 3.1.1.4 Failure Conditions

- The `Asset` is `MPT`:

  - The `lsfMPTCanTransfer` is not set in the `MPTokenIssuance` object. (the asset is not transferable).
  - The `lsfMPTLocked` flag is set in the `MPTokenIssuance` object. (the asset is locked).

- The `Asset` is an `IOU`:

  - The `lsfGlobalFreeze` flag is set on the issuing account (the asset is frozen).

- The `Data` field is larger than 256 bytes.
- The account submiting the transaction has insufficient `AccountRoot.Balance` for the Owner Reserve.

##### 3.1.1.5 State Changes

- Create a new `Vault` ledger object.
- Create a new `MPTokenIssuance` ledger object for the vault shares.
- Create a new `AccountRoot`[_pseudo-account_](https://github.com/XRPLF/XRPL-Standards/discussions/191) object setting the `PseudoOwner` to `VaultID`.

- If `Vault.Asset` is an `IOU`:

  - Create a `RippleState` object between the _pseudo-account_ `AccountRoot` and `Issuer` `AccountRoot`.

- If `Vault.Asset` is an `MPT`:

  - Create `MPToken` object for the _pseudo-account_ for the `Asset.MPTokenIssuance`.

##### 3.1.1.6 Invariants

**TBD**

[**Return to Index**](#index)

#### 3.1.2 `VaultSet` Transaction

The `VaultSet` updates an existing `Vault` ledger object.

| Field Name        |     Required?      | JSON Type | Internal Type | Default Value | Description                                                                                                                                          |
| ----------------- | :----------------: | :-------: | :-----------: | :-----------: | :--------------------------------------------------------------------------------------------------------------------------------------------------- |
| `TransactionType` | :heavy_check_mark: | `string`  |   `Uint16`    |     `59`      | The transaction type.                                                                                                                                |
| `VaultID`         | :heavy_check_mark: | `string`  |   `Hash256`   |     `N/A`     | The ID of the Vault to be modified. Must be included when updating the Vault.                                                                        |
| `Data`            |                    | `string`  |    `Blob`     |               | Arbitrary Vault metadata, limited to 256 bytes.                                                                                                      |
| `AssetsMaximum`   |                    | `number`  |   `Uint64`    |       0       | The maximum asset amount that can be held in a vault. The value cannot be lower than the current `AssetsTotal` of the Vault unless the value is `0`. |

##### 3.1.2.1 Failure Conditions

- `Vault` object with the specified `VaultID` does not exist on the ledger.
- The submitting account is not the `Owner` of the vault.
- The `Data` field is larger than 256 bytes.
- If `Vault.AssetsMaximum` > `0` AND `AssetsMaximum` > 0 AND:
  - The `AssetsMaximum` < `Vault.AssetsTotal` (new `AssetsMaximum` cannot be lower than the current `AssetsTotal`).
- The transaction is attempting to modify an immutable field.

##### 3.1.2.2 State Changes

- Update mutable fields in the `Vault` ledger object.

##### 3.1.2.3 Invariants

**TBD**

[**Return to Index**](#index)

#### 3.1.3 `VaultDelete` Transaction

The `VaultDelete` transaction deletes an existing vault object.

| Field Name        |     Required?      | JSON Type | Internal Type | Default Value |            Description             |
| ----------------- | :----------------: | :-------: | :-----------: | :-----------: | :--------------------------------: |
| `TransactionType` | :heavy_check_mark: | `string`  |   `Uint16`    |     `60`      |         Transaction type.          |
| `VaultID`         | :heavy_check_mark: | `string`  |   `Hash256`   |     `N/A`     | The ID of the vault to be deleted. |

##### 3.1.3.1 Failure Conditions

- `Vault` object with the `VaultID` does not exist on the ledger.
- The submitting account is not the `Owner` of the vault.
- `AssetsTotal`, `AssetsAvailable`, or `MPTokenIssuance(Vault.Share).OutstandingAmount` are greater than zero.
- The `OwnerDirectory` of the Vault _pseudo-account_ contains pointers to objects other than the `Vault`, the `MPTokenIssuance` for its shares, or an `MPToken` or trust line for its asset.

##### 3.1.3.2 State Changes

- Delete the `MPTokenIssuance` object for the vault shares.
- Delete the `MPToken` or `RippleState` object corresponding to the vault's holding of the asset, if one exists.
- Delete the `AccountRoot` object of the _pseudo-account_, and its `DirectoryNode` objects.
- Release the Owner Reserve to the `Vault.Owner` account.
- Delete the `Vault` object.

##### 3.1.3.3 Invariants

**TBD**

[**Return to Index**](#index)

### 3.2 `VaultDeposit` and `VaultWithdraw` transactions

Depositors call the `VaultDeposit` and `VaultWithdraw` transactions to add or remove assets from the Tokenized Vault.

[**Return to Index**](#index)

#### 3.2.1 `VaultDeposit` transaction

The `VaultDeposit` transaction adds Liqudity in exchange for vault shares.

| Field Name        |     Required?      |      JSON Type       | Internal Type | Default Value | Description                                            |
| ----------------- | :----------------: | :------------------: | :-----------: | :-----------: | :----------------------------------------------------- |
| `TransactionType` | :heavy_check_mark: |       `string`       |   `UINT16`    |     `61`      | Transaction type.                                      |
| `VaultID`         | :heavy_check_mark: |       `string`       |   `HASH256`   |     `N/A`     | The ID of the vault to which the assets are deposited. |
| `Amount`          | :heavy_check_mark: | `string` or `object` |   `AMOUNT`    |     `N/A`     | Asset amount to deposit.                               |

##### 3.2.1.1 Failure conditions

- `Vault` object with the `VaultID` does not exist on the ledger.
- The asset type of the vault does not match the asset type the depositor is depositing.
- The depositor does not have sufficient funds to make a deposit.
- Adding the `Amount` to the `AssetsTotal` of the vault would exceed the `AssetsMaximum`.
- The `Vault` `lsfPrivate` flag is set and the `Account` depositing the assets does not have credentials in the permissioned domain.

- The `Vault.Asset` is `MPT`:

  - `MPTokenIssuance.lsfMPTCanTransfer` is not set (the asset is not transferable).
  - `MPTokenIssuance.lsfMPTLocked` flag is set (the asset is globally locked).
  - `MPToken(MPTokenIssuanceID, AccountID).lsfMPTLocked` flag is set (the asset is locked for the depositor).
  - `MPToken(MPTokenIssuanceID, AccountID).MPTAmount` < `Amount` (insufficient balance).

- The `Asset` is an `IOU`:

  - The `lsfGlobalFreeze` flag is set on the issuing account (the asset is frozen).
  - The `lsfHighFreeze` or `lsfLowFreeze` flag is set on the `RippleState` object between the Asset `Issuer` and the depositor.
  - The `RippleState` object `Balance` < `Amount` (insufficient balance).

##### 3.2.1.2 State Changes

If no `MPToken` object exists for the depositor, create one. For object details, see [3.4.2 `MPToken`](#3.4.2-MPToken).

- Increase the `MPTAmount` field of the share `MPToken` object of the `Account` by $\Delta_{share}$.
- Increase the `OutstandingAmount` field of the share `MPTokenIssuance` object by $\Delta_{share}$.
- Increase the `AssetsTotal` and `AssetsAvailable` of the `Vault` by `Amount`.

- If the `Vault.Asset` is `XRP`:

  - Increase the `Balance` field of _pseudo-account_ `AccountRoot` by `Amount`.
  - Decrease the `Balance` field of the depositor `AccountRoot` by `Amount`.

- If the `Vault.Asset` is an `IOU`:

  - Increase the `RippleState` balance between the _pseudo-account_ `AccountRoot` and the `Issuer` `AccountRoot` by `Amount`.
  - Decrease the `RippleState` balance between the depositor `AccountRoot` and the `Issuer` `AccountRoot` by `Amount`.

- If the `Vault.Asset` is an `MPT`:

  - Increase the `MPToken.MPTAmount` by `Amount` of the _pseudo-account_ `MPToken` object for the `Vault.Asset`.
  - Decrease the `MPToken.MPTAmount` by `Amount` of the depositor `MPToken` object for the `Vault.Asset`.

##### 3.2.1.3 Invariants

**TBD**

[**Return to Index**](#index)

#### 3.2.2 `VaultWithdraw` transaction

The `VaultWithdraw` transaction withdraws assets in exchange for the vault's shares.

| Field Name        |     Required?      | JSON Type | Internal Type | Default Value | Description                                                             |
| ----------------- | :----------------: | :-------: | :-----------: | :-----------: | :---------------------------------------------------------------------- |
| `TransactionType` | :heavy_check_mark: | `string`  |   `UINT16`    |     `62`      | Transaction type.                                                       |
| `VaultID`         | :heavy_check_mark: | `string`  |   `HASH256`   |     `N/A`     | The ID of the vault from which assets are withdrawn.                    |
| `Amount`          | :heavy_check_mark: | `number`  |  `STAmount`   |       0       | The exact amount of Vault asset to withdraw.                            |
| `Destination`     |                    | `string`  |  `AccountID`  |     Empty     | An account to receive the assets. It must be able to receive the asset. |

If `Amount` is the Vaults asset, calculate the share cost using the [**Withdraw formula**](#21713-withdraw).
If `Amount` is the Vaults share, calculate the assets amount using the [**Redeem formula**](#21712-redeem).

In sections below assume the following variables:

- $\Gamma_{share}$ - the total number of shares issued by the vault.
- $\Gamma_{asset}$ - the total assets in the vault, including any future yield.

- $\Delta_{asset}$ - the change in the total amount of assets after a deposit, withdrawal, or redemption.
- $\Delta_{share}$ - che change in the total amount of shares after a deposit, withdrawal, or redemption.

##### 3.2.2.1 Failure conditions

- `Vault` object with the `VaultID` does not exist on the ledger.

- The `Vault.Asset` is `MPT`:

  - `MPTokenIssuance.lsfMPTCanTransfer` is not set (the asset is not transferable).
  - `MPTokenIssuance.lsfMPTLocked` flag is set (the asset is globally locked).
  - `MPToken(MPTokenIssuanceID, AccountID).lsfMPTLocked` flag is set (the asset is locked for the depositor)

- The `Asset` is an `IOU`:

  - The `lsfGlobalFreeze` flag is set on the issuing account (the asset is frozen).
  - The `lsfHighFreeze` or `lsfLowFreeze` flag is set on the `RippleState` object between the Asset `Issuer` and the depositor.

- The unit of `Amount` is not shares of the vault.
- The unit of `Amount` is not asset of the vault.

- There is insufficient liquidity in the vault to fill the request:

  - If `Amount` is the vaults share:

    - `MPTokenIssuance(Vault.Share).OutstandingAmount` < `Amount` (attempt to withdraw more shares than there are in total).
    - The shares `MPToken.MPTAmount` of the `Account` is less than `Amount` (attempt to withdraw more shares than owned).
    - `Vault.AssetsAvailable` < $\Delta_{asset}$ (the vault has insufficient assets).

  - If `Amount` is the vaults asset:

    - The shares `MPToken.MPTAmount` of the `Account` is less than $\Delta_{share}$ (attempt to withdraw more shares than owned).
    - `Vault.AssetsAvailable` < `Amount` (the vault has insufficient assets).

- The `Destination` account is specified and it does not have permission to receive the asset.

##### 3.2.2.2 State Changes

- If the `Vault.Asset` is XRP:

  - Decrease the `Balance` field of _pseudo-account_ `AccountRoot` by $\Delta_{asset}$.
  - Increase the `Balance` field of the depositor `AccountRoot` by $\Delta_{asset}$.

- If the `Vault.Asset` is an `IOU`:

  - Decrease the `RippleState` balance between the _pseudo-account_ `AccountRoot` and the `Issuer` `AccountRoot` by $\Delta_{asset}$.
  - Increase the `RippleState` balance between the depositor `AccountRoot` and the `Issuer` `AccountRoot` by $\Delta_{asset}$.

- If the `Vault.Asset` is an `MPT`:

  - Decrease the `MPToken.MPTAmount` by $\Delta_{asset}$ of the _pseudo-account_ `MPToken` object for the `Vault.Asset`.
  - Increase the `MPToken.MPTAmount` by $\Delta_{asset}$ of the depositor `MPToken` object for the `Vault.Asset`.

- Update the `MPToken` object for the `Vault.Share` of the depositor `AccountRoot`:

  - Decrease the `MPToken.MPTAmount` by $\Delta_{share}$.
  - If `MPToken.MPTAmount == 0`, delete the object.

- Update the `MPTokenIssuance` object for the `Vault.Share`:

  - Decrease the `OutstandingAmount` field of the share `MPTokenIssuance` object by $\Delta_{share}$.

- Decrease the `AssetsTotal` and `AssetsAvailable` by $\Delta_{asset}$

##### 3.2.2.3 Invariants

**TBD**

[**Return to Index**](#index)

## 3.3 VaultClawback Transaction

#### 3.3.1 `VaultClawback` transaction

The `VaultClawback` transaction performs a Clawback from the Vault, exchanging the shares of an account. Conceptually, the transaction performs `VaultWithdraw` on behalf of the `Holder`, sending the funds to the `Issuer` account of the asset. In case there are insufficient funds for the entire `Amount` the transaction will perform a partial Clawback, up to the `Vault.AssetsAvailable`. The Clawback transaction must respect any future fees or penalties.

| Field Name        |     Required?      | JSON Type | Internal Type | Default Value | Description                                                                                                    |
| ----------------- | :----------------: | :-------: | :-----------: | :-----------: | :------------------------------------------------------------------------------------------------------------- |
| `TransactionType` | :heavy_check_mark: | `string`  |   `UINT16`    |     `63`      | Transaction type.                                                                                              |
| `VaultID`         | :heavy_check_mark: | `string`  |   `HASH256`   |     `N/A`     | The ID of the vault from which assets are withdrawn.                                                           |
| `Holder`          | :heavy_check_mark: | `string`  |  `AccountID`  |     `N/A`     | The account ID from which to clawback the assets.                                                              |
| `Amount`          |                    | `number`  |   `NUMBER`    |       0       | The asset amount to clawback. When Amount is `0` clawback all funds, up to the total shares the `Holder` owns. |

##### 3.3.1.1 Failure conditions

- `Vault` object with the `VaultID` does not exist on the ledger.

- If `Vault.Asset` is `XRP`.

- If `Vault.Asset` is an `IOU` and:

  - The `Issuer` account is not the submitter of the transaction.

- If `Vault.Asset` is an `MPT` and:
  - `MPTokenIssuance.Issuer` is not the submitter of the transaction.
  - The `MPToken` object for the `Vault.Share` of the `Holder` `AccountRoot` does not exist OR `MPToken.MPTAmount == 0`.

##### 3.3.1.2 State Changes

- If the `Vault.Asset` is an `IOU`:

  - Decrease the `RippleState` balance between the _pseudo-account_ `AccountRoot` and the `Issuer` `AccountRoot` by `min(Vault.AssetsAvailable`, $\Delta_{asset}$`)`.

- If the `Vault.Asset` is an `MPT`:

  - Decrease the `MPToken.MPTAmount` by `min(Vault.AssetsAvailable`, $\Delta_{asset}$`)` of the _pseudo-account_ `MPToken` object for the `Vault.Asset`.

- Update the `MPToken` object for the `Vault.Share` of the depositor `AccountRoot`:

  - Decrease the `MPToken.MPTAmount` by $\Delta_{share}$.
  - If `MPToken.MPTAmount == 0`, delete the object.

- Update the `MPTokenIssuance` object for the `Vault.Share`:

  - Decrease the `OutstandingAmount` field of the share `MPTokenIssuance` object by $\Delta_{share}$.

- Decrease the `AssetsTotal` and `AssetsAvailable` by `min(Vault.AssetsAvailable`, $\Delta_{asset}$`)`

##### 3.3.1.3 Invariants

**TBD**

[**Return to Index**](#index)

## 4. API

### 4.1 RPC `ledger_entry`

This method retrieves ledger object. In particular, it retrieves a Vault object by its ID. The specification purposefully ommits general fields. These can be found [here](https://xrpl.org/docs/references/http-websocket-apis/public-api-methods/ledger-methods/ledger_entry#general-fields).

#### 4.1.1 Request Fields

We propose adding the following fields to the `ledger_entry` method:

| Field Name |     Required?      | JSON Type |                Description                 |
| ---------- | :----------------: | :-------: | :----------------------------------------: |
| `vault_id` | :heavy_check_mark: | `string`  | The object ID of the Vault to be returned. |

#### 4.1.2 Response

| Field Name             |     Required?      |     JSON Type      | Description                                                                                       |
| ---------------------- | :----------------: | :----------------: | :------------------------------------------------------------------------------------------------ |
| `LedgerEntryType`      | :heavy_check_mark: |      `string`      | Ledger object type.                                                                               |
| `LedgerIndex`          | :heavy_check_mark: |      `string`      | Ledger object identifier.                                                                         |
| `Flags`                | :heavy_check_mark: |      `string`      | Ledger object flags.                                                                              |
| `PreviousTxnID`        | :heavy_check_mark: |      `string`      | Identifies the transaction ID that most recently modified this object.                            |
| `PreviousTxnLgrSeq`    | :heavy_check_mark: |      `number`      | The sequence of the ledger that contains the transaction that most recently modified this object. |
| `Sequence`             | :heavy_check_mark: |      `number`      | The transaction sequence number that created the vault.                                           |
| `OwnerNode`            | :heavy_check_mark: |      `number`      | Identifies the page where this item is referenced in the owner's directory.                       |
| `Owner`                | :heavy_check_mark: |      `string`      | The account address of the Vault Owner.                                                           |
| `Account`              | :heavy_check_mark: |      `string`      | The address of the Vaults _pseudo-account_.                                                       |
| `Data`                 | :heavy_check_mark: |      `string`      | Arbitrary metadata about the Vault. Limited to 256 bytes.                                         |
| `Asset`                | :heavy_check_mark: | `string or object` | The asset of the vault. The vault supports `XRP`, `IOU` and `MPT`.                                |
| `AssetsTotal`          | :heavy_check_mark: |      `number`      | The total value of the vault.                                                                     |
| `AssetsAvailable`      | :heavy_check_mark: |      `number`      | The asset amount that is available in the vault.                                                  |
| `LossUnrealized`       | :heavy_check_mark: |      `number`      | The potential loss amount that is not yet realized expressed as the vaults asset.                 |
| `AssetsMaximum`        | :heavy_check_mark: |      `number`      | The maximum asset amount that can be held in the vault. Zero value `0` indicates there is no cap. |
| `Share`                | :heavy_check_mark: |      `object`      | The identifier of the share MPTokenIssuance object.                                               |
| `SharesTotal`          | :heavy_check_mark: |      `number`      | The total amount of shares issued by the vault.                                                   |
| `WithdrawalPolicy`     | :heavy_check_mark: |      `string`      | Indicates the withdrawal strategy used by the Vault.                                              |
| `PermissionedDomainID` | :heavy_check_mark: |      `string`      | The permissioned domain identifier of the Vault. This value is ignored if the vault is public.    |

#### 4.1.2.1 Example

```type-script
{
  "LedgerEntryType": "Vault",
  "LedgerIndex": "E123F4567890ABCDE123F4567890ABCDEF1234567890ABCDEF1234567890ABCD",
  "Flags": "0",
  "PreviousTxnID": "9A8765B4321CDE987654321CDE987654321CDE987654321CDE987654321CDE98",
  "PreviousTxnLgrSeq": 12345678,
  "Sequence": 1,
  "OwnerNode": 2,
  "Owner": "rEXAMPLE9AbCdEfGhIjKlMnOpQrStUvWxYz",
  "Account": "rPseudoAcc1234567890abcdef1234567890abcdef",
  "Data": "This is arbitrary metadata about the vault.",
  "Asset": {
    "currency": "USD",
    "issuer": "rIssuer1234567890abcdef1234567890abcdef",
    "value": "1000"
  },
  "AssetsTotal": 1000000,
  "AssetsAvailable": 800000,
  "LossUnrealized": 200000,
  "AssetsMaximum": 0,
  "Share": {
    "TokenID": "ABCDEF1234567890ABCDEF1234567890ABCDEF1234567890ABCDEF1234567890",
    "Issuer": "rShareIssuer1234567890abcdef1234567890abcdef"
  },
  "SharesTotal": 5000,
  "WithdrawalPolicy": "FIFO",
  "PermissionedDomainID": "example-domain-id"
}
```

[**Return to Index**](#index)

# Appendix

[**Return to Index**](#index)

## A-1 F.A.Q.

### A-1.1 Why does the specification allow both `Withdraw` and `Redeem` and not just one of them?

We chose this design in order to reduce the amount of off-chain math required to be implemented by XRPL users and/or developers

### A-1.2 Why can any account that holds Vaults shares submit a `VaultWithdraw` transaction?

The `VaultWithdraw` transaction does not respect the permissioned domain rules. In other words, any account that holds the shares of the Vault can withdraw them.

The decision was made to avoid a situation where a depositor deposits assets to a private vault to then have their access revoked by invalidating their credentials, and thus loosing access to their funds.
