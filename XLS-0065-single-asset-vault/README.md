<pre>
  xls: 65
  title: Single Asset Tokenized Vault
  description: On-chain primitive for aggregating assets from depositors using Multi-Purpose-Tokens for ownership shares
  author: Vytautas Vito Tumas <vtumas@ripple.com>, Aanchal Malhotra <amalhotra@ripple.com>
  proposal-from: https://github.com/XRPLF/XRPL-Standards/discussions/192
  status: Draft
  category: Amendment
  requires: [XLS-33](../XLS-0033-multi-purpose-tokens/README.md)
  created: 2024-04-12
  updated: 2025-11-17
</pre>

# Single Asset Vault

## _Abstract_

A Single Asset Vault is a new on-chain primitive for aggregating assets from one or more depositors, and making the assets available for other on-chain protocols. The Single Asset Vault uses [Multi-Purpose-Token](https://github.com/XRPLF/XRPL-Standards/tree/master/XLS-0033-multi-purpose-tokens) to represent ownership shares of the Vault. The Vault serves diverse purposes, such as lending markets, aggregators, yield-bearing tokens, asset management, etc. The Single Asset Vault decouples the liquidity provision functionality from the specific protocol logic.

## Index

- [**1. Introduction**](#1-introduction)
  - [**1.1. Feature Overview**](#11-overview)
  - [**1.2. Terminology**](#12-terminology)
  - [**1.3. Actors**](#13-actors)
  - [**1.4 Connecting to the Vault**](#14-connecting-to-the-vault)
- [**2. Ledger Entries**](#2-ledger-entries)
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
  - [**3.4. Payment Transaction**](#34-payment-transaction)
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

A Single Asset Vault can be either public or private. Any depositor can deposit and redeem liquidity from a public vault, provided they own sufficient shares. In contrast, access to private shares is controlled via [Permissioned Domains](../XLS-0080-permissioned-domains/README.md), which use on-chain [Credentials](https://github.com/XRPLF/XRPL-Standards/tree/master/XLS-0070-credentials) to manage access to the vault. Only depositors with the necessary credentials can deposit assets to a private vault. To prevent Vault Owner from locking away depositor funds, any shareholder can withdraw funds. Furthermore, the Vault Owner has an implicit permission to deposit and withdraw assets to and from the Vault. I.e. they do not have to have credentials in the Permissioned Domain.

#### 1.1.3 Yield Bearing Shares

Shares represent the ownership of a portion of the vault's assets. On-chain shares are represented by a [Multi-Purpose Token](https://github.com/XRPLF/XRPL-Standards/tree/master/XLS-0033-multi-purpose-tokens). When creating the vault, the Vault Owner can configure the shares to be non-transferable. Non-transferable shares cannot be transferred to any other account -- they can only be redeemed. If the vault is private, shares can be transferred and used in other DeFi protocols as long as the receiving account is authorized to hold the shares. The vault's shares may be yield-bearing, depending on the protocol connected to the vault, meaning that a holder may be able to withdraw more (or less) liquidity than they initially deposited.

### 1.2 Terminology

- **Vault**: A ledger entry for aggregating liquidity and providing this liquidity to one or more accessors.
- **Asset**: The currency of a vault. It is either XRP, a [Fungible Token](https://xrpl.org/docs/concepts/tokens/fungible-tokens/) or a [Multi-Purpose Token](https://github.com/XRPLF/XRPL-Standards/tree/master/XLS-0033-multi-purpose-tokens).
- **Share**: Shares represent the depositors' portion of the vault's assets. Shares are a [Multi-Purpose Token](https://github.com/XRPLF/XRPL-Standards/tree/master/XLS-0033-multi-purpose-tokens) created by the _pseudo-account_ of the vault.

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
- The [`AccountID`](https://xrpl.org/docs/references/protocol/binary-format/#accountid-fields) of the account submitting the `VaultSet`transaction, i.e.`VaultOwner`.
- The transaction `Sequence` number. If the transaction used a [Ticket](https://xrpl.org/docs/concepts/accounts/tickets/), use the `TicketSequence` value.

#### 2.1.2 Fields

A vault has the following fields:

| Field Name          | Modifiable? |     Required?      |     JSON Type      | Internal Type | Default Value | Description                                                                                                                                            |
| ------------------- | :---------: | :----------------: | :----------------: | :-----------: | :-----------: | :----------------------------------------------------------------------------------------------------------------------------------------------------- |
| `LedgerEntryType`   |    `N/A`    | :heavy_check_mark: |      `string`      |   `UINT16`    |   `0x0084`    | Ledger object type.                                                                                                                                    |
| `LedgerIndex`       |    `N/A`    | :heavy_check_mark: |      `string`      |   `UINT16`    |     `N/A`     | Ledger object identifier.                                                                                                                              |
| `Flags`             |    `Yes`    | :heavy_check_mark: |      `string`      |   `UINT32`    |       0       | Ledger object flags.                                                                                                                                   |
| `PreviousTxnID`     |    `N/A`    | :heavy_check_mark: |      `string`      |   `HASH256`   |     `N/A`     | Identifies the transaction ID that most recently modified this object.                                                                                 |
| `PreviousTxnLgrSeq` |    `N/A`    | :heavy_check_mark: |      `number`      |   `UINT32`    |     `N/A`     | The sequence of the ledger that contains the transaction that most recently modified this object.                                                      |
| `Sequence`          |    `N/A`    | :heavy_check_mark: |      `number`      |   `UINT32`    |     `N/A`     | The transaction sequence number that created the vault.                                                                                                |
| `OwnerNode`         |    `N/A`    | :heavy_check_mark: |      `number`      |   `UINT64`    |     `N/A`     | Identifies the page where this item is referenced in the owner's directory.                                                                            |
| `Owner`             |    `No`     | :heavy_check_mark: |      `string`      |  `AccountID`  |     `N/A`     | The account address of the Vault Owner.                                                                                                                |
| `Account`           |    `N/A`    | :heavy_check_mark: |      `string`      |  `ACCOUNTID`  |     `N/A`     | The address of the Vaults _pseudo-account_.                                                                                                            |
| `Data`              |    `Yes`    |                    |      `string`      |    `BLOB`     |     None      | Arbitrary metadata about the Vault. Limited to 256 bytes.                                                                                              |
| `Asset`             |    `No`     | :heavy_check_mark: | `string or object` |    `ISSUE`    |     `N/A`     | The asset of the vault. The vault supports `XRP`, `IOU` and `MPT`.                                                                                     |
| `AssetsTotal`       |    `N/A`    | :heavy_check_mark: |      `number`      |   `NUMBER`    |       0       | The total value of the vault.                                                                                                                          |
| `AssetsAvailable`   |    `N/A`    | :heavy_check_mark: |      `number`      |   `NUMBER`    |       0       | The asset amount that is available in the vault.                                                                                                       |
| `LossUnrealized`    |    `N/A`    | :heavy_check_mark: |      `number`      |   `NUMBER`    |       0       | The potential loss amount that is not yet realized expressed as the vaults asset.                                                                      |
| `AssetsMaximum`     |    `Yes`    |                    |      `number`      |   `NUMBER`    |       0       | The maximum asset amount that can be held in the vault. Zero value `0` indicates there is no cap.                                                      |
| `ShareMPTID`        |    `N/A`    | :heavy_check_mark: |      `number`      |   `UINT192`   |       0       | The identifier of the share MPTokenIssuance object.                                                                                                    |
| `WithdrawalPolicy`  |    `No`     | :heavy_check_mark: |      `string`      |    `UINT8`    |     `N/A`     | Indicates the withdrawal strategy used by the Vault.                                                                                                   |
| `Scale`             |    `No`     | :heavy_check_mark: |      `number`      |    `UINT8`    |       6       | The `Scale` specifies the power of 10 ($10^{\text{scale}}$) to multiply an asset's value by when converting it into an integer-based number of shares. |

##### 2.1.2.1 Flags

The `Vault` object supports the following flags:

| Flag Name         |  Flag Value  | Modifiable? |                 Description                  |
| ----------------- | :----------: | :---------: | :------------------------------------------: |
| `lsfVaultPrivate` | `0x00010000` |    `No`     | If set, indicates that the vault is private. |

#### 2.1.3 Vault `_pseudo-account_`

An AccountRoot entry holds the XRP, IOU or MPT deposited into the vault. It also acts as the issuer of the vault's shares. The _pseudo-account_ follows the XLS-64 specification for pseudo accounts. The `AccountRoot` object is created when creating the `Vault` object.

#### 2.1.4 Ownership

The `Vault` objects are stored in the ledger and tracked in an [Owner Directory](https://xrpl.org/docs/references/protocol/ledger-data/ledger-entry-types/directorynode) owned by the account submitting the `VaultSet` transaction. Furthermore, to facilitate `Vault` object lookup from the vault shares, the object is also tracked in the `OwnerDirectory` of the _`pseudo-account`_.

#### 2.1.5 Owner Reserve

The `Vault` object costs one reserve fee per object created:

- The `Vault` object itself.
- The `MPTokenIssuance` associated with the shares of the Vault.

#### 2.1.6 Vault Shares

Shares represent the portion of the Vault assets a depositor owns. Vault Owners set the currency code of the share and whether the token is transferable during the vault's creation. These two values are immutable. The share is represented by a [Multi-Purpose Token](https://github.com/XRPLF/XRPL-Standards/tree/master/XLS-0033-multi-purpose-tokens). The MPT is issued by the vault's pseudo-account.

##### 2.1.6.1 `Scale`

The **`Scale`** field enables the vault to accurately represent fractional asset values using integer-only MPT shares, which prevents the loss of value from decimal truncation. It defines a scaling factor, calculated as $10^{\text{Scale}}$, that converts a decimal asset amount into a corresponding whole number of shares. For example, with a `Scale` of `6`, a deposit of **20.3** assets is multiplied by $10^6$ and credited as **20,300,000** shares.

As a general rule, all calculations involving MPTs are executed with a precision of a single MPT, treating them as indivisible units. If a calculation results in a fractional amount, it will be rounded up, down or to the nearest whole number depending on the context. Crucially, the rounding direction is determined by the protocol and is not controlled by the transaction submitter, which may lead to unexpected results.

##### 2.1.6.1.1 `IOU`

When a vault holds an **`IOU`**, the `Scale` is configurable by the Vault Owner at the time of the vault's creation. The value can range from **0** to a maximum of **18**, with a default of **6**. This flexibility allows issuers to set a level of precision appropriate for their specific token.

##### 2.1.6.1.2 `XRP`

When a vault holds **`XRP`**, the `Scale` is fixed at **0**. This aligns with XRP's native structure, where one share represents one drop (the smallest unit of XRP), and one XRP equals 1,000,000 drops. Therefore, a deposit of 10 XRP to an empty Vault will result in the issuance of 10,000,000 shares ($10 \times 10^6$).

##### 2.1.6.1.3 `MPT`

When a vault holds `MPT`, its `Scale` is fixed at **0**. This creates a 1-to-1 relationship between deposited MPT units and the shares issued (for example, depositing 10 MPTs to an empty Vault issues 10 shares). The value of a single MPT is determined at the issuer's discretion. If an MPT is set to represent a large value, the vault owner and the depositor must be cautious. Since only whole MPT units are used in calculations, any value that is not a multiple of a single MPT's value may be lost due to rounding during a transaction.

##### 2.1.6.2 `MPTokenIssuance`

The `MPTokenIssuance` object represents the share on the ledger. It is created and deleted together with the `Vault` object.

###### 2.1.6.2.1 `MPTokenIssuance` Values

Here’s the table with the headings "Field," "Description," and "Value":

| **Field**         | **Description**                                                                                                                 | **Value**            |
| ----------------- | ------------------------------------------------------------------------------------------------------------------------------- | -------------------- |
| `Issuer`          | The AccountID of the Vault's _pseudo-account_.                                                                                  | _pseudo-account_ ID  |
| `MaximumAmount`   | No limit to the number of shares that can be issued.                                                                            | `0xFFFFFFFFFFFFFFFF` |
| `TransferFee`     | The fee paid to transfer the shares.                                                                                            | 0                    |
| `MPTokenMetadata` | Arbitrary metadata about the share MPT, in hex format.                                                                          | -                    |
| `AssetScale`      | Represents orders of magnitude between the standard and the MPT unit. For IOUs it is set to `Vault.Scale`, otherwise it is `0`. | `Vault.Scale`        |

###### Flags

The following flags are set based on whether the shares are transferable and if the vault is public or private.

| **Condition**     | **Transferable**                                                                       | **Non-Transferable** |
| ----------------- | -------------------------------------------------------------------------------------- | -------------------- |
| **Public Vault**  | `lsfMPTCanEscrow` <br> `lsfMPTCanTrade`<br> `lsfMPTCanTransfer`                        | No Flags             |
| **Private Vault** | `lsfMPTCanEscrow`<br> `lsfMPTCanTrade`<br> `lsfMPTCanTransfer`<br> `lsfMPTRequireAuth` | `lsfMPTRequireAuth`  |

##### 2.1.6.3 `MPToken`

The `MPToken` object represents the amount of shares held by a depositor. It is created when the account deposits liquidity into the vault and is deleted when a depositor redeems (or transfers) all shares.

###### 2.1.6.3.1 `MPToken` Values

The `MPToken` values should be set as per the `MPT` [specification](https://github.com/XRPLF/XRPL-Standards/tree/master/XLS-0033-multi-purpose-tokens#2112-fields).

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

### 2.1.7.2 Exchange Rate Algorithms

This section details the algorithms used to calculate the exchange between assets and shares for deposits, redemptions, and withdrawals.

#### Key Variables

- **$\Gamma_{assets}$**: The total balance of assets held within the vault.
- **$\Gamma_{shares}$**: The total number of shares currently issued by the vault.
- **$\Delta_{assets}$**: The amount of assets being deposited, withdrawn, or redeemed.
- **$\Delta_{shares}$**: The number of shares being issued or burned.
- **$\iota$**: The vault's total **unrealized loss**.
- **$\sigma$**: The scaling factor derived from `Scale`, used to convert fractional assets into integer shares.

### 2.1.7.2.1 Deposit

The deposit function calculates the number of shares a user receives for their assets.

**Calculation Logic**

The calculation depends on whether the vault is empty.

- **Initial Deposit**: For the first deposit into an empty vault, shares are calculated using a scaling factor, $\sigma = 10^{\text{Scale}}$, to properly represent fractional assets as whole numbers.
  $$\Delta_{shares} = \Delta_{assets} \times \sigma$$

- **Subsequent Deposits**: For all other deposits, shares are calculated proportionally. The resulting $\Delta_{shares}$ value is **rounded down** to the nearest integer.
  $$\Delta_{shares} = \frac{\Delta_{assets} \times \Gamma_{shares}}{\Gamma_{assets}}$$

Because the share amount is rounded down, the actual assets taken from the depositor ($\Delta_{assets'}$) are recalculated.

$$\Delta_{assets'} = \frac{\Delta_{shares} \times \Gamma_{assets}}{\Gamma_{shares}}$$

#### Vault State Update

The vault's totals are updated with the final calculated amounts.

- **New Total Assets**: $\Gamma_{assets} \leftarrow \Gamma_{assets} + \Delta_{assets'}$
- **New Total Shares**: $\Gamma_{shares} \leftarrow \Gamma_{shares} + \Delta_{shares}$

### 2.1.7.2.2 Redeem

The redeem function calculates the asset payout for a user burning a specific number of shares.

**Calculation Logic**

The amount of assets a user receives is calculated by finding the proportional value of their shares relative to the vault's total holdings, accounting for any unrealized loss ($\iota$).

$$\Delta_{assets} = \frac{\Delta_{shares} \times (\Gamma_{assets} - \iota)}{\Gamma_{shares}}$$

**Vault State Update**

The vault's totals are reduced after the redemption.

- **New Total Assets**: $\Gamma_{assets} \leftarrow \Gamma_{assets} - \Delta_{assets}$
- **New Total Shares**: $\Gamma_{shares} \leftarrow \Gamma_{shares} - \Delta_{shares}$

### 2.1.7.2.3 Withdraw

The withdraw function handles a request for a specific amount of assets, which involves a two-step process to determine the final payout.

First, the requested asset amount ($\Delta_{assets\_requested}$) is converted into the equivalent number of shares to burn, based on the vault's real value.

$$\Delta_{shares} = \frac{\Delta_{assets\_requested} \times \Gamma_{shares}}{(\Gamma_{assets} - \iota)}$$

This calculated $\Delta_{shares}$ amount is **rounded to the nearest whole number**.

Next, the rounded number of shares from Step 1 is used to calculate the final asset payout ($\Delta_{assets\_out}$), using the same logic as a redemption.

$$\Delta_{assets\_out} = \frac{\Delta_{shares} \times (\Gamma_{assets} - \iota)}{\Gamma_{shares}}$$

Due to the rounding in Step 1, this final payout may differ slightly from the user's requested amount.

**Vault State Update**

The vault's totals are reduced by the final calculated amounts.

- **New Total Assets**: $\Gamma_{assets} \leftarrow \Gamma_{assets} - \Delta_{assets\_out}$
- **New Total Shares**: $\Gamma_{shares} \leftarrow \Gamma_{shares} - \Delta_{shares}$

##### 2.1.7.3 Withdrawal Policy

Withdrawal policy controls the logic used when removing liquidity from a vault. Each strategy has its own implementation, but it can be used in multiple vaults once implemented. Therefore, different vaults may have different withdrawal policies. The specification introduces the following options:

###### 2.1.7.3.1 `first-come-first-serve`

The First Come, First Serve strategy treats all requests equally, allowing a depositor to redeem any amount of assets provided they have a sufficient number of shares.

#### 2.1.8 Frozen Assets

The issuer of the Vaults asset may enact a freeze either through a [Global Freeze](https://xrpl.org/docs/concepts/tokens/fungible-tokens/freezes/#global-freeze) for IOUs or [locking MPT](https://github.com/XRPLF/XRPL-Standards/tree/master/XLS-0033-multi-purpose-tokens#21122-flags). When the vaults asset is frozen, it can only be withdrawn by specifying the `Destination` account as the `Issuer` of the asset. Similarly, a frozen asset _may not_ be deposited into a vault. Furthermore, when the asset of a vault is frozen, the shares corresponding to the asset may not be transferred.

#### 2.1.9 Transfer Fees

The Vault does not apply the [Transfer Fee](https://xrpl.org/docs/concepts/tokens/transfer-fees) to `VaultDeposit` and `VaultWithdraw` transactions. Furthermore, whenever a protocol moves assets from or to a Vault, the `Transfer Fee` must not be charged.

[**Return to Index**](#index)

## 3. Transactions

All transactions introduced by this proposal incorporate the [common transaction fields](https://xrpl.org/docs/references/protocol/transactions/common-fields) that are shared by all transactions. Standard fields are only documented in this proposal if needed because this proposal introduces new possible values for such fields.

### 3.1 `VaultCreate`, `VaultSet`, `VaultDelete` transactions

The `Vault` object is managed with `VaultCreate`, `VaultSet` and `VaultDelete` transactions.

#### 3.1.1 `VaultCreate` Transaction

The `VaultCreate` transaction creates a new `Vault` object.

| Field Name         |     Required?      |     JSON Type      | Internal Type |      Default Value       | Description                                                                                                                                            |
| ------------------ | :----------------: | :----------------: | :-----------: | :----------------------: | :----------------------------------------------------------------------------------------------------------------------------------------------------- |
| `TransactionType`  | :heavy_check_mark: |      `string`      |   `UINT16`    |           `58`           | The transaction type.                                                                                                                                  |
| `Flags`            | :heavy_check_mark: |      `number`      |   `UINT32`    |            0             | Specifies the flags for the Vault.                                                                                                                     |
| `Data`             |                    |      `string`      |    `BLOB`     |                          | Arbitrary Vault metadata, limited to 256 bytes.                                                                                                        |
| `Asset`            | :heavy_check_mark: | `string or object` |    `ISSUE`    |          `N/A`           | The asset (`XRP`, `IOU` or `MPT`) of the Vault.                                                                                                        |
| `AssetsMaximum`    |                    |      `number`      |   `NUMBER`    |            0             | The maximum asset amount that can be held in a vault.                                                                                                  |
| `MPTokenMetadata`  |                    |      `string`      |    `BLOB`     |                          | Arbitrary metadata about the share `MPT`, in hex format, limited to 1024 bytes.                                                                        |
| `WithdrawalPolicy` |                    |      `number`      |    `UINT8`    | `strFirstComeFirstServe` | Indicates the withdrawal strategy used by the Vault.                                                                                                   |
| `DomainID`         |                    |      `string`      |   `HASH256`   |                          | The `PermissionedDomain` object ID associated with the shares of this Vault.                                                                           |
| `Scale`            |                    |      `number`      |    `UINT8`    |            6             | The `Scale` specifies the power of 10 ($10^{\text{scale}}$) to multiply an asset's value by when converting it into an integer-based number of shares. |

##### 3.1.1.1 Flags

| Flag Name                     |  Flag Value  | Description                                                                              |
| ----------------------------- | :----------: | :--------------------------------------------------------------------------------------- |
| `tfVaultPrivate`              | `0x00010000` | Indicates that the vault is private. It can only be set during Vault creation.           |
| `tfVaultShareNonTransferable` | `0x00020000` | Indicates the vault share is non-transferable. It can only be set during Vault creation. |

###### 3.1.1.2 WithdrawalPolicy

The type indicates the withdrawal strategy supported by the vault. The following values are supported:

| Strategy Name                      |  Value   |                        Description                        |
| ---------------------------------- | :------: | :-------------------------------------------------------: |
| `vaultStrategyFirstComeFirstServe` | `0x0001` | Requests are processed on a first-come-first-serve basis. |

##### 3.1.1.3 Transaction Fees

The transaction creates an `AccountRoot` object for the `_pseudo-account_`. Therefore, the transaction [must destroy](../XLS-0064-pseudo-account/README.md) one incremental owner reserve amount.

##### 3.1.1.4 Failure Conditions

- The `Asset` is `XRP`:
  - The `Scale` parameter is provided.

- The `Asset` is `MPT`:
  - The `Scale` parameter is provided.
  - The `lsfMPTCanTransfer` is not set in the `MPTokenIssuance` object. (the asset is not transferable).
  - The `lsfMPTLocked` flag is set in the `MPTokenIssuance` object. (the asset is locked).

- The `Asset` is an `IOU`:
  - The `lsfGlobalFreeze` flag is set on the issuing account (the asset is frozen).
  - The `Scale` parameter is provided, and is less than **0** or greater than **18**.

- The `tfVaultPrivate` flag is not set and the `DomainID` is provided. (The VaultOwner is attempting to create a public Vault with a PermissionedDomain)

- The `PermissionedDomain` object does not exist with the provided `DomainID`.

- The `Data` field is larger than 256 bytes.
- The account submiting the transaction has insufficient `AccountRoot.Balance` for the Owner Reserve.

##### 3.1.1.5 State Changes

- Create a new `Vault` ledger object.
- Create a new `MPTokenIssuance` ledger object for the vault shares.
  - If the `DomainID` is provided:
    - `MPTokenIssuance(Vault.ShareMPTID).DomainID = DomainID` (Set the Permissioned Domain ID).
  - Create an `MPToken` object for the Vault Owner to hold Vault Shares.
- Create a new `AccountRoot`[_pseudo-account_](../XLS-0064-pseudo-account/README.md) object setting the `PseudoOwner` to `VaultID`.

- If `Vault.Asset` is an `IOU`:
  - Create a `RippleState` object between the _pseudo-account_ `AccountRoot` and `Issuer` `AccountRoot`.

- If `Vault.Asset` is an `MPT`:
  - Create `MPToken` object for the _pseudo-account_ for the `Asset.MPTokenIssuance`.

##### 3.1.1.6 Invariants

**TBD**

[**Return to Index**](#index)

#### 3.1.2 `VaultSet` Transaction

The `VaultSet` updates an existing `Vault` ledger object.

| Field Name        |     Required?      | JSON Type | Internal Type | Default Value | Description                                                                                                                             |
| ----------------- | :----------------: | :-------: | :-----------: | :-----------: | :-------------------------------------------------------------------------------------------------------------------------------------- |
| `TransactionType` | :heavy_check_mark: | `string`  |   `Uint16`    |     `59`      | The transaction type.                                                                                                                   |
| `VaultID`         | :heavy_check_mark: | `string`  |   `Hash256`   |     `N/A`     | The ID of the Vault to be modified. Must be included when updating the Vault.                                                           |
| `Data`            |                    | `string`  |    `Blob`     |               | Arbitrary Vault metadata, limited to 256 bytes.                                                                                         |
| `AssetsMaximum`   |                    | `number`  |   `Number`    |               | The maximum asset amount that can be held in a vault. The value cannot be lower than the current `AssetsTotal` unless the value is `0`. |
| `DomainID`        |                    | `string`  |   `Hash256`   |               | The `PermissionedDomain` object ID associated with the shares of this Vault.                                                            |

##### 3.1.2.1 Failure Conditions

- `Vault` object with the specified `VaultID` does not exist on the ledger.
- The submitting account is not the `Owner` of the vault.
- The `Data` field is larger than 256 bytes.
- If `Vault.AssetsMaximum` > `0` AND `AssetsMaximum` > 0 AND:
  - The `AssetsMaximum` < `Vault.AssetsTotal` (new `AssetsMaximum` cannot be lower than the current `AssetsTotal`).
- The `sfVaultPrivate` flag is not set and the `DomainID` is provided (Vault Owner is attempting to set a PermissionedDomain to a public Vault).
- The `PermissionedDomain` object does not exist with the provided `DomainID`.
- The transaction is attempting to modify an immutable field.
- The transaction does not specify any of the modifiable fields.

##### 3.1.2.2 State Changes

- Update mutable fields in the `Vault` ledger object.
- If `DomainID` is provided:
  - Set `MPTokenIssuance(Vault.ShareMPTID).DomainID = DomainID` (Set the Permissioned Domain).

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
- `AssetsTotal`, `AssetsAvailable`, or `MPTokenIssuance(Vault.ShareMPTID).OutstandingAmount` are greater than zero.
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
| `Amount`          | :heavy_check_mark: | `string` or `object` |  `STAmount`   |     `N/A`     | Asset amount to deposit.                               |

##### 3.2.1.1 Failure conditions

- `Vault` object with the `VaultID` does not exist on the ledger.
- The asset type of the vault does not match the asset type the depositor is depositing.
- The depositor does not have sufficient funds to make a deposit.
- Adding the `Amount` to the `AssetsTotal` of the vault would exceed the `AssetsMaximum`.
- The `Vault` `lsfVaultPrivate` flag is set and the `Account` depositing the assets does not have credentials in the permissioned domain of the share.

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

If no `MPToken` object exists for the depositor, create one. For object details, see [2.1.6.2 `MPToken`](#2162-mptoken).

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

| Field Name        |     Required?      | JSON Type | Internal Type | Default Value | Description                                                                 |
| ----------------- | :----------------: | :-------: | :-----------: | :-----------: | :-------------------------------------------------------------------------- |
| `TransactionType` | :heavy_check_mark: | `string`  |   `UINT16`    |     `62`      | Transaction type.                                                           |
| `VaultID`         | :heavy_check_mark: | `string`  |   `HASH256`   |     `N/A`     | The ID of the vault from which assets are withdrawn.                        |
| `Amount`          | :heavy_check_mark: | `number`  |  `STAmount`   |       0       | The exact amount of Vault asset to withdraw.                                |
| `Destination`     |                    | `string`  |  `AccountID`  |     Empty     | An account to receive the assets. It must be able to receive the asset.     |
| `DestinationTag`  |                    | `number`  |   `UINT32`    |     Empty     | Arbitrary tag identifying the reason for the withdrawal to the destination. |

- If `Amount` is the Vaults asset, calculate the share cost using the [**Withdraw formula**](#21723-withdraw).
- If `Amount` is the Vaults share, calculate the assets amount using the [**Redeem formula**](#21722-redeem).

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
  - `MPToken(MPTokenIssuanceID, AccountID | Destination).lsfMPTLocked` flag is set (the asset is locked for the depositor or the destination).

- The `Asset` is an `IOU`:
  - The `lsfGlobalFreeze` flag is set on the issuing account (the asset is frozen).
  - The `lsfHighFreeze` or `lsfLowFreeze` flag is set on the `RippleState` object between the Asset `Issuer` and the `AccountRoot` of the `AccountID` or the `Destination`.

- The unit of `Amount` is not shares of the vault.
- The unit of `Amount` is not asset of the vault.

- There is insufficient liquidity in the vault to fill the request:
  - If `Amount` is the vaults share:
    - `MPTokenIssuance(Vault.ShareMPTID).OutstandingAmount` < `Amount` (attempt to withdraw more shares than there are in total).
    - The shares `MPToken.MPTAmount` of the `Account` is less than `Amount` (attempt to withdraw more shares than owned).
    - `Vault.AssetsAvailable` < $\Delta_{asset}$ (the vault has insufficient assets).

  - If `Amount` is the vaults asset:
    - The shares `MPToken.MPTAmount` of the `Account` is less than $\Delta_{share}$ (attempt to withdraw more shares than owned).
    - `Vault.AssetsAvailable` < `Amount` (the vault has insufficient assets).

- The `Destination` account is specified:
  - The account does not have permission to receive the asset.
  - The account does not have a `RippleState` or `MPToken` object for the asset.

##### 3.2.2.2 State Changes

- If the `Vault.Asset` is XRP:
  - Decrease the `Balance` field of _pseudo-account_ `AccountRoot` by $\Delta_{asset}$.
  - Increase the `Balance` field of the depositor `AccountRoot` by $\Delta_{asset}$.

- If the `Vault.Asset` is an `IOU`:
  - If the Depositor account does not have a `RippleState` object for the Vaults Asset, create the `RippleState` object.

  - Decrease the `RippleState` balance between the _pseudo-account_ `AccountRoot` and the `Issuer` `AccountRoot` by $\Delta_{asset}$.
  - Increase the `RippleState` balance between the depositor `AccountRoot` and the `Issuer` `AccountRoot` by $\Delta_{asset}$.

- If the `Vault.Asset` is an `MPT`:
  - If the Depositor account does not have a `MPToken` object for the Vaults Asset, create the `MPToken` object.

  - Decrease the `MPToken.MPTAmount` by $\Delta_{asset}$ of the _pseudo-account_ `MPToken` object for the `Vault.Asset`.
  - Increase the `MPToken.MPTAmount` by $\Delta_{asset}$ of the depositor `MPToken` object for the `Vault.Asset`.

- Update the `MPToken` object for the `Vault.ShareMPTID` of the depositor `AccountRoot`:
  - Decrease the `MPToken.MPTAmount` by $\Delta_{share}$.
  - If `MPToken.MPTAmount == 0`, delete the object.

- Update the `MPTokenIssuance` object for the `Vault.ShareMPTID`:
  - Decrease the `OutstandingAmount` field of the share `MPTokenIssuance` object by $\Delta_{share}$.

- Decrease the `AssetsTotal` and `AssetsAvailable` by $\Delta_{asset}$

##### 3.2.2.3 Invariants

**TBD**

[**Return to Index**](#index)

## 3.3 VaultClawback Transaction

#### 3.3.1 `VaultClawback` Transaction

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
  - If the `AccountRoot(Issuer)` object does not have `lsfAllowTrustLineClawback` flag set (the asset does not support clawback).
  - If the `AccountRoot(Issuer)` has the `lsfNoFreeze` flag set (the asset cannot be frozen).

- If `Vault.Asset` is an `MPT` and:
  - `MPTokenIssuance.Issuer` is not the submitter of the transaction.
  - `MPTokenIssuance.lsfMPTCanClawback` flag is not set (the asset does not support clawback).
  - If the `MPTokenIssuance.lsfMPTCanLock` flag is NOT set (the asset cannot be locked).

- The `MPToken` object for the `Vault.ShareMPTID` of the `Holder` `AccountRoot` does not exist OR `MPToken.MPTAmount == 0`.

##### 3.3.1.2 State Changes

- If the `Vault.Asset` is an `IOU`:
  - Decrease the `RippleState` balance between the _pseudo-account_ `AccountRoot` and the `Issuer` `AccountRoot` by `min(Vault.AssetsAvailable`, $\Delta_{asset}$`)`.

- If the `Vault.Asset` is an `MPT`:
  - Decrease the `MPToken.MPTAmount` by `min(Vault.AssetsAvailable`, $\Delta_{asset}$`)` of the _pseudo-account_ `MPToken` object for the `Vault.Asset`.

- Update the `MPToken` object for the `Vault.ShareMPTID` of the depositor `AccountRoot`:
  - Decrease the `MPToken.MPTAmount` by $\Delta_{share}$.
  - If `MPToken.MPTAmount == 0`, delete the object.

- Update the `MPTokenIssuance` object for the `Vault.ShareMPTID`:
  - Decrease the `OutstandingAmount` field of the share `MPTokenIssuance` object by $\Delta_{share}$.

- Decrease the `AssetsTotal` and `AssetsAvailable` by `min(Vault.AssetsAvailable`, $\Delta_{asset}$`)`

##### 3.3.1.3 Invariants

**TBD**

[**Return to Index**](#index)

## 3.4 Payment Transaction

### 3.4.1 `Payment` transaction

The Single Asset Vault does not introduce new `Payment` transaction fields. However, it adds additional failure conditions and state changes when transfering Vault shares.

#### 3.4.1.1 Failure Conditions

- If `Payment.Amount` is a `Vault` share AND:
  - The `Vault` `lsfVaultPrivate` flag is set and the `Payment.Destination` account does not have credentials in the permissioned domain of the Vaults Share.
  - The `Vault` `tfVaultShareNonTransferable` flag is set.

  - The `Vault.Asset` is `MPT`:
    - `MPTokenIssuance.lsfMPTCanTransfer` is not set (the asset is not transferable).
    - `MPTokenIssuance.lsfMPTLocked` flag is set (the asset is globally locked).
    - `MPToken(MPTokenIssuanceID, AccountID).lsfMPTLocked` flag is set (the asset is locked for the payer).
    - `MPToken(MPTokenIssuanceID, PseudoAccountID).lsfMPTLocked` flag is set (the asset is locked for the `pseudo-account`).
    - `MPToken(MPTokenIssuanceID, Destination).lsfMPTLocked` flag is set (the asset is locked for the destination account).

  - The `Vault.Asset` is an `IOU`:
    - The `lsfGlobalFreeze` flag is set on the issuing account (the asset is frozen).
    - The `lsfHighFreeze` or `lsfLowFreeze` flag is set on the `RippleState` object between the Asset `Issuer` and the payer account.
    - The `lsfHighFreeze` or `lsfLowFreeze` flag is set on the `RippleState` object between the Asset `Issuer` and the destination account.
    - The `lsfHighFreeze` or `lsfLowFreeze` flag is set on the `RippleState` object between the Asset `Issuer` and the `pseudo-account`.

#### 3.4.1.2 State Changes

- If `MPToken`object for shares does not exist for the destination account, create one.

[**Return to Index**](#index)

## 4. API

### 4.1 RPC `vault_info`

This RPC retrieves the Vault ledger entry and the IDs associated with it.

#### 4.1.1 Request Fields

We propose adding the following fields to the `ledger_entry` method:

| Field Name |     Required?      | JSON Type |                Description                 |
| ---------- | :----------------: | :-------: | :----------------------------------------: |
| `vault`    | :heavy_check_mark: | `string`  | The object ID of the Vault to be returned. |

#### 4.1.2 Response

| Field Name                       | Required? | JSON Type | Description                                                                                                                                            |
| -------------------------------- | --------- | --------- | ------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `vault`                          | `yes`     | `object`  | Root object representing the vault.                                                                                                                    |
| `vault.Account`                  | `yes`     | `string`  | The pseudo-account ID of the vault.                                                                                                                    |
| `vault.Asset`                    | `yes`     | `object`  | Object representing the asset held in the vault.                                                                                                       |
| `vault.Asset.currency`           | `yes`     | `string`  | Currency code of the asset stored in the vault.                                                                                                        |
| `vault.Asset.issuer`             | `no`      | `string`  | Issuer address of the asset.                                                                                                                           |
| `vault.AssetsAvailable`          | `yes`     | `string`  | Amount of assets currently available for withdrawal.                                                                                                   |
| `vault.AssetsTotal`              | `yes`     | `string`  | Total amount of assets in the vault.                                                                                                                   |
| `vault.Flags`                    | `no`      | `number`  | Bit-field flags associated with the vault.                                                                                                             |
| `vault.LedgerEntryType`          | `yes`     | `string`  | Ledger entry type, always "Vault".                                                                                                                     |
| `vault.LossUnrealized`           | `no`      | `string`  | Unrealized loss associated with the vault.                                                                                                             |
| `vault.Owner`                    | `yes`     | `string`  | ID of the Vault Owner account.                                                                                                                         |
| `vault.OwnerNode`                | `no`      | `string`  | Identifier for the owner node in the ledger tree.                                                                                                      |
| `vault.PreviousTxnID`            | `yes`     | `string`  | Transaction ID of the last modification to this vault.                                                                                                 |
| `vault.PreviousTxnLgrSeq`        | `yes`     | `number`  | Ledger sequence number of the last transaction modifying this vault.                                                                                   |
| `vault.Sequence`                 | `yes`     | `number`  | Sequence number of the vault entry.                                                                                                                    |
| `vault.ShareMPTID`               | `no`      | `string`  | Multi-purpose token ID associated with this vault.                                                                                                     |
| `vault.WithdrawalPolicy`         | `no`      | `number`  | Policy defining withdrawal conditions.                                                                                                                 |
| `vault.index`                    | `yes`     | `string`  | Unique index of the vault ledger entry.                                                                                                                |
| `vault.shares`                   | `yes`     | `object`  | Object containing details about issued shares.                                                                                                         |
| `vault.shares.Flags`             | `no`      | `number`  | Bit-field flags associated with the shares issuance.                                                                                                   |
| `vault.shares.Issuer`            | `yes`     | `string`  | The ID of the Issuer of the Share. It will always be the pseudo-account ID.                                                                            |
| `vault.shares.LedgerEntryType`   | `yes`     | `string`  | Ledger entry type, always "MPTokenIssuance".                                                                                                           |
| `vault.shares.OutstandingAmount` | `yes`     | `string`  | Total outstanding shares issued.                                                                                                                       |
| `vault.shares.OwnerNode`         | `no`      | `string`  | Identifier for the owner node of the shares.                                                                                                           |
| `vault.shares.PreviousTxnID`     | `yes`     | `string`  | Transaction ID of the last modification to the shares issuance.                                                                                        |
| `vault.shares.PreviousTxnLgrSeq` | `yes`     | `number`  | Ledger sequence number of the last transaction modifying the shares issuance.                                                                          |
| `vault.shares.Sequence`          | `yes`     | `number`  | Sequence number of the shares issuance entry.                                                                                                          |
| `vault.shares.index`             | `yes`     | `string`  | Unique index of the shares ledger entry.                                                                                                               |
| `vault.shares.mpt_issuance_id`   | `no`      | `string`  | The ID of the `MPTokenIssuance` object. It will always be equal to `vault.ShareMPTID`.                                                                 |
| `vault.Scale`                    | `yes`     | `number`  | The `Scale` specifies the power of 10 ($10^{\text{scale}}$) to multiply an asset's value by when converting it into an integer-based number of shares. |

#### 4.1.2.1 Example

Vault holding an `IOU`:

```type-script
 "result" :
 {
  "ledger_current_index" : 7,
  "status" : "success",
  "validated" : false,
  "vault" :
  {
   "Account" : "rKwvc1mgHLyHKY3yRUqVwffWtsxYb3QLWf",
   "Asset" :
   {
    "currency" : "IOU",
    "issuer" : "r9cZ5oHbdL4Z9Maj6TdnfAos35nVzYuNds"
   },
   "AssetsAvailable" : "100",
   "AssetsTotal" : "100",
   "Flags" : 0,
   "LedgerEntryType" : "Vault",
   "LossUnrealized" : "0",
   "Owner" : "rwhaYGnJMexktjhxAKzRwoCcQ2g6hvBDWu",
   "OwnerNode" : "0",
   "PreviousTxnID" : "1484794AE38DBB7C6F4E0B7536CC560B418135BEDB0F8904349F7F8A3B496826",
   "PreviousTxnLgrSeq" : 6,
   "Sequence" : 5,
   "ShareMPTID" : "00000001C752C42A1EBD6BF2403134F7CFD2F1D835AFD26E",
   "WithdrawalPolicy" : 1,
   "index" : "2DE64CA41250EF3CB7D2B127D6CEC31F747492CAE2BD1628CA02EA1FFE7475B3",
   "shares" :
   {
    "DomainID" : "3B61A239626565A3FBEFC32863AFBF1AD3325BD1669C2C9BC92954197842B564",
    "Flags" : 0,
    "Issuer" : "rKwvc1mgHLyHKY3yRUqVwffWtsxYb3QLWf",
    "LedgerEntryType" : "MPTokenIssuance",
    "OutstandingAmount" : "100",
    "OwnerNode" : "0",
    "PreviousTxnID" : "1484794AE38DBB7C6F4E0B7536CC560B418135BEDB0F8904349F7F8A3B496826",
    "PreviousTxnLgrSeq" : 6,
    "Sequence" : 1,
    "index" : "F84AE266C348540D7134F1A683392C3B97C3EEFDE9FEF6F2055B3B92550FB44A",
    "mpt_issuance_id" : "00000001C752C42A1EBD6BF2403134F7CFD2F1D835AFD26E"
   },
   "Scale": 6,
  }
 }
```

Vault holding an `MPT`:

```
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
  "Data": "5468697320697320617262697472617279206D657461646174612061626F757420746865207661756C742E",
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
    "mpt_issuance_id": "0000012FFD9EE5DA93AC614B4DB94D7E0FCE415CA51BED47",
    "value": "1",
  },
  "ShareTotal": 5000,
  "WithdrawalPolicy": "0x0001",
  "Scale": 0
}
```

Vault holding `XRP`:

```type-script
{
 "result" :
 {
  "ledger_hash" : "6FFF56DF92D54D01EE3D5487787F4430D66F89C6BC74B00C276262A0207B2FAD",
  "ledger_index" : 6,
  "status" : "success",
  "validated" : true,
  "vault" :
  {
   "Account" : "rBVxExjRR6oDMWCeQYgJP7q4JBLGeLBPyv",
   "Asset" :
   {
    "currency" : "XRP"
   },
   "AssetsAvailable" : "0",
   "AssetsTotal" : "0",
   "Flags" : 0,
   "LedgerEntryType" : "Vault",
   "LossUnrealized" : "0",
   "Owner" : "rwhaYGnJMexktjhxAKzRwoCcQ2g6hvBDWu",
   "OwnerNode" : "0",
   "PreviousTxnID" : "25C3C8BF2C9EE60DFCDA02F3919D0C4D6BF2D0A4AC9354EFDA438F2ECDDA65E4",
   "PreviousTxnLgrSeq" : 5,
   "Sequence" : 4,
   "ShareMPTID" : "00000001732B0822A31109C996BCDD7E64E05D446E7998EE",
   "WithdrawalPolicy" : 1,
   "index" : "C043BB1B350FFC5FED21E40535609D3D95BC0E3CE252E2F69F85BE0157020A52",
   "shares" :
   {
    "DomainID" : "3B61A239626565A3FBEFC32863AFBF1AD3325BD1669C2C9BC92954197842B564",
    "Flags" : 56,
    "Issuer" : "rBVxExjRR6oDMWCeQYgJP7q4JBLGeLBPyv",
    "LedgerEntryType" : "MPTokenIssuance",
    "OutstandingAmount" : "0",
    "OwnerNode" : "0",
    "PreviousTxnID" : "25C3C8BF2C9EE60DFCDA02F3919D0C4D6BF2D0A4AC9354EFDA438F2ECDDA65E4",
    "PreviousTxnLgrSeq" : 5,
    "Sequence" : 1,
    "index" : "4B25BDE141E248E5D585FEB6100E137D3C2475CEE62B28446391558F0BEA23B5",
    "mpt_issuance_id" : "00000001732B0822A31109C996BCDD7E64E05D446E7998EE"
   },
   "Scale": 0
  }
 }
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

### A-1.3 How can a depositor transfer shares to another account?

Vault shares are a first-class assets, meaning that they can be transfered and used in other on-ledger protocols that support MPTokens. However, the payee (or the receiver) of the shares must have permissions to hold the shares and the assset that the shares represent. For example, if the shares are for a private Vault containing `USDC` the destination account must be in the permissioned domain of the Vault, and have permissions to hold `USDC`.

In addion, any compliance mechanisms applied to `USDC` will also apply to the share. For example, if the Issuer of `USDC` freezes the Trustline of the payee, then the payee will not be able to receive any shares representing `USDC`.

### A-1.4 What is the difference between the `VaultOwner` and the `pseudo-account`?

XRP Ledger is an account based blockchain. That means that assets (XRP, IOU and MPT) must be held by an account. The Vault Object (or any other object, such as the AMM) cannot hold assets directly. Therefore, a pseudo-account is created that holds the assets on behalf of that object. The pseudo-account is a stand-alone account, that cannot receive funds, it cannot send transactions, it is there to only hold assets. So for example, when a depositor deposits assets into a vault, in reality this transaction moves the assets from the depositor account to the pseudo-account. Furthermore, the Vault `pseudo-account` is the Issuer of the Vault shares.

### A-1.5 Do `VaultDeposit` or `VaultWithdraw` transactions charge transfer fees?

No, neither of the transactions charge transfer fees when depositing or withdrawing assets to and from the Vault.
