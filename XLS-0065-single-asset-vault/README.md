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
  updated: 2026-04-27
</pre>

# Single Asset Vault

## 1. Abstract

A Single Asset Vault is a new on-chain primitive for aggregating assets from one or more depositors, and making the assets available for other on-chain protocols. The Single Asset Vault uses [Multi-Purpose-Token](../XLS-0033-multi-purpose-tokens/README.md) to represent ownership shares of the Vault. The Vault serves diverse purposes, such as lending markets, aggregators, yield-bearing tokens, asset management, etc. The Single Asset Vault decouples the liquidity provision functionality from the specific protocol logic.

## 2. Introduction

The **Single Asset Vault** is an on-chain object that aggregates assets from one or more depositors and represents ownership through shares. Other protocols, such as the [Lending Protocol](../XLS-0066-lending-protocol/README.md), can access these assets via the vault, whether or not they generate yield. Currently, other protocols must be created by the same Account that created the Vault. However, this may change in the future.

The specification introduces a new `Vault` ledger entry, which contains key details such as available assets, shares, total value, and other relevant information.

### 2.1. Transactions

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

### 2.2. Vault Ownership and Management

A Single Asset Vault is owned and managed by an account called the **Vault Owner**. The account is reponsible for creating, updating and deleting the Vault object.

### 2.3. Access Control

A Single Asset Vault can be either public or private. Any depositor can deposit and redeem liquidity from a public vault, provided they own sufficient shares. In contrast, access to private shares is controlled via [Permissioned Domains](../XLS-0080-permissioned-domains/README.md), which use on-chain [Credentials](../XLS-0070-credentials/README.md) to manage access to the vault. Only depositors with the necessary credentials can deposit assets to a private vault. To prevent Vault Owner from locking away depositor funds, any shareholder can withdraw funds. Furthermore, the Vault Owner has an implicit permission to deposit and withdraw assets to and from the Vault. I.e. they do not have to have credentials in the Permissioned Domain.

### 2.4. Yield Bearing Shares

Shares represent the ownership of a portion of the vault's assets. On-chain shares are represented by a [Multi-Purpose Token](../XLS-0033-multi-purpose-tokens/README.md). When creating the vault, the Vault Owner can configure the shares to be non-transferable. Non-transferable shares cannot be transferred to any other account -- they can only be redeemed. If the vault is private, shares can be transferred and used in other DeFi protocols as long as the receiving account is authorized to hold the shares. The vault's shares may be yield-bearing, depending on the protocol connected to the vault, meaning that a holder may be able to withdraw more (or less) liquidity than they initially deposited.

### 2.5. Terminology

- **Vault**: A ledger entry for aggregating liquidity and providing this liquidity to one or more accessors.
- **Asset**: The currency of a vault. It is either XRP, a [Fungible Token](https://xrpl.org/docs/concepts/tokens/fungible-tokens/) or a [Multi-Purpose Token](../XLS-0033-multi-purpose-tokens/README.md).
- **Share**: Shares represent the depositors' portion of the vault's assets. Shares are a [Multi-Purpose Token](../XLS-0033-multi-purpose-tokens/README.md) created by the _pseudo-account_ of the vault.

### 2.6. Actors

- **Vault Owner**: An account responsible for creating and deleting The Vault.
- **Depositor**: An entity that deposits and withdraws assets to and from the vault.

### 2.7. Connecting to the Vault

A protocol connecting to a Vault must track its debt. Furthermore, the updates to the Vault state when funds are removed or added back must be handled in the transactors of the protocol. For an example, please refer to the [Lending Protocol](../XLS-0066-lending-protocol/README.md) specification.

## 3. Specification

### 3.1 Ledger Entry: `Vault`

The **`Vault`** ledger entry describes the state of the tokenized vault.

#### 3.1.1 Object Identifier

The key of the `Vault` object is the result of [`SHA512-Half`](https://xrpl.org/docs/references/protocol/data-types/basic-data-types/#hashes) of the following values concatenated in order:

- The `Vault` space key `0x0056` (capital V)
- The [`ACCOUNTID`](https://xrpl.org/docs/references/protocol/binary-format/#accountid-fields) of the account submitting the `VaultSet`transaction, i.e.`VaultOwner`.
- The transaction `Sequence` number. If the transaction used a [Ticket](https://xrpl.org/docs/concepts/accounts/tickets/), use the `TicketSequence` value.

#### 3.1.2 Fields

A vault has the following fields:

| Field Name          | Constant | Required |     JSON Type      | Internal Type | Default Value | Description                                                                                                                                            |
| ------------------- | :------: | :------: | :----------------: | :-----------: | :-----------: | :----------------------------------------------------------------------------------------------------------------------------------------------------- |
| `LedgerEntryType`   |    No    |   Yes    |      `string`      |   `UINT16`    |   `0x0084`    | Ledger object type.                                                                                                                                    |
| `LedgerIndex`       |    No    |   Yes    |      `string`      |   `UINT16`    |     `N/A`     | Ledger object identifier.                                                                                                                              |
| `Flags`             |   Yes    |   Yes    |      `string`      |   `UINT32`    |       0       | Ledger object flags.                                                                                                                                   |
| `PreviousTxnID`     |    No    |   Yes    |      `string`      |   `HASH256`   |     `N/A`     | Identifies the transaction ID that most recently modified this object.                                                                                 |
| `PreviousTxnLgrSeq` |    No    |   Yes    |      `number`      |   `UINT32`    |     `N/A`     | The sequence of the ledger that contains the transaction that most recently modified this object.                                                      |
| `Sequence`          |    No    |   Yes    |      `number`      |   `UINT32`    |     `N/A`     | The transaction sequence number that created the vault.                                                                                                |
| `OwnerNode`         |    No    |   Yes    |      `number`      |   `UINT64`    |     `N/A`     | Identifies the page where this item is referenced in the owner's directory.                                                                            |
| `Owner`             |    No    |   Yes    |      `string`      |  `ACCOUNTID`  |     `N/A`     | The account address of the Vault Owner.                                                                                                                |
| `Account`           |    No    |   Yes    |      `string`      |  `ACCOUNTID`  |     `N/A`     | The address of the Vaults _pseudo-account_.                                                                                                            |
| `Data`              |   Yes    |    No    |      `string`      |    `BLOB`     |     None      | Arbitrary metadata about the Vault. Limited to 256 bytes.                                                                                              |
| `Asset`             |    No    |   Yes    | `string or object` |    `ISSUE`    |     `N/A`     | The asset of the vault. The vault supports `XRP`, `IOU` and `MPT`.                                                                                     |
| `AssetsTotal`       |    No    |   Yes    |      `number`      |   `NUMBER`    |       0       | The total value of the vault.                                                                                                                          |
| `AssetsAvailable`   |    No    |   Yes    |      `number`      |   `NUMBER`    |       0       | The asset amount that is available in the vault.                                                                                                       |
| `LossUnrealized`    |    No    |   Yes    |      `number`      |   `NUMBER`    |       0       | The potential loss amount that is not yet realized expressed as the vaults asset.                                                                      |
| `AssetsMaximum`     |   Yes    |    No    |      `number`      |   `NUMBER`    |       0       | The maximum asset amount that can be held in the vault. Zero value `0` indicates there is no cap.                                                      |
| `ShareMPTID`        |    No    |   Yes    |      `number`      |   `UINT192`   |       0       | The identifier of the share MPTokenIssuance object.                                                                                                    |
| `WithdrawalPolicy`  |    No    |   Yes    |      `string`      |    `UINT8`    |     `N/A`     | Indicates the withdrawal strategy used by the Vault.                                                                                                   |
| `Scale`             |    No    |   Yes    |      `number`      |    `UINT8`    |       6       | The `Scale` specifies the power of 10 ($10^{\text{scale}}$) to multiply an asset's value by when converting it into an integer-based number of shares. |

##### 3.1.2.1 Flags

The `Vault` object supports the following flags:

| Flag Name         |  Flag Value  | Modifiable? |                 Description                  |
| ----------------- | :----------: | :---------: | :------------------------------------------: |
| `lsfVaultPrivate` | `0x00010000` |     No      | If set, indicates that the vault is private. |

#### 3.1.3 Pseudo-Account

An AccountRoot entry holds the XRP, IOU or MPT deposited into the vault. It also acts as the issuer of the vault's shares. The _pseudo-account_ follows the XLS-64 specification for pseudo accounts. The `AccountRoot` object is created when creating the `Vault` object.

#### 3.1.4 Ownership

The `Vault` objects are stored in the ledger and tracked in an [Owner Directory](https://xrpl.org/docs/references/protocol/ledger-data/ledger-entry-types/directorynode) owned by the account submitting the `VaultSet` transaction. Furthermore, to facilitate `Vault` object lookup from the vault shares, the object is also tracked in the `OwnerDirectory` of the _`pseudo-account`_.

#### 3.1.5 Owner Reserve

The `Vault` object costs one reserve fee per object created:

- The `Vault` object itself.
- The `MPTokenIssuance` associated with the shares of the Vault.

#### 3.1.6 Vault Shares

Shares represent the portion of the Vault assets a depositor owns. Vault Owners set the currency code of the share and whether the token is transferable during the vault's creation. These two values are immutable. The share is represented by a [Multi-Purpose Token](../XLS-0033-multi-purpose-tokens/README.md). The MPT is issued by the vault's pseudo-account.

##### 3.1.6.1 `Scale`

The **`Scale`** field enables the vault to accurately represent fractional asset values using integer-only MPT shares, which prevents the loss of value from decimal truncation. It defines a scaling factor, calculated as $10^{\text{Scale}}$, that converts a decimal asset amount into a corresponding whole number of shares. For example, with a `Scale` of `6`, a deposit of **20.3** assets is multiplied by $10^6$ and credited as **20,300,000** shares.

As a general rule, all calculations involving MPTs are executed with a precision of a single MPT, treating them as indivisible units. If a calculation results in a fractional amount, it will be rounded up, down or to the nearest whole number depending on the context. Crucially, the rounding direction is determined by the protocol and is not controlled by the transaction submitter, which may lead to unexpected results.

###### 3.1.6.1.1 `IOU`

When a vault holds an **`IOU`**, the `Scale` is configurable by the Vault Owner at the time of the vault's creation. The value can range from **0** to a maximum of **18**, with a default of **6**. This flexibility allows issuers to set a level of precision appropriate for their specific token.

###### 3.1.6.1.2 `XRP`

When a vault holds **`XRP`**, the `Scale` is fixed at **0**. This aligns with XRP's native structure, where one share represents one drop (the smallest unit of XRP), and one XRP equals 1,000,000 drops. Therefore, a deposit of 10 XRP to an empty Vault will result in the issuance of 10,000,000 shares ($10 \times 10^6$).

###### 3.1.6.1.3 `MPT`

When a vault holds `MPT`, its `Scale` is fixed at **0**. This creates a 1-to-1 relationship between deposited MPT units and the shares issued (for example, depositing 10 MPTs to an empty Vault issues 10 shares). The value of a single MPT is determined at the issuer's discretion. If an MPT is set to represent a large value, the vault owner and the depositor must be cautious. Since only whole MPT units are used in calculations, any value that is not a multiple of a single MPT's value may be lost due to rounding during a transaction.

##### 3.1.6.2 `MPTokenIssuance`

The `MPTokenIssuance` object represents the share on the ledger. It is created and deleted together with the `Vault` object.

###### 3.1.6.2.1 `MPTokenIssuance` Values

Here's the table with the headings "Field," "Description," and "Value":

| **Field**         | **Description**                                                                                                                 | **Value**            |
| ----------------- | ------------------------------------------------------------------------------------------------------------------------------- | -------------------- |
| `Issuer`          | The ACCOUNTID of the Vault's _pseudo-account_.                                                                                  | _pseudo-account_ ID  |
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

##### 3.1.6.3 `MPToken`

The `MPToken` object represents the amount of shares held by a depositor. It is created when the account deposits liquidity into the vault and is deleted when a depositor redeems (or transfers) all shares.

###### 3.1.6.3.1 `MPToken` Values

The `MPToken` values should be set as per the `MPT` [specification](../XLS-0033-multi-purpose-tokens/README.md#2112-fields).

| **Condition**     | **Transferable**   | **Non-Transferable** |
| ----------------- | ------------------ | -------------------- |
| **Public Vault**  | No Flags           | `lsfMPTAuthorized`   |
| **Private Vault** | `lsfMPTAuthorized` | `lsfMPTAuthorized`   |

#### 3.1.7 Exchange Algorithm

Exchange Algorithm refers to the logic that is used to exchange assets into shares and shares into assets. This logic is executed when depositing or redeeming liquidity. A Vault comes with the default exchange algorithm, which is detailed below.

##### 3.1.7.1 Unrealized Loss

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

##### 3.1.7.2 Exchange Rate Algorithms

This section details the algorithms used to calculate the exchange between assets and shares for deposits, redemptions, and withdrawals.

##### Key Variables

- **$\Gamma_{assets}$**: The total balance of assets held within the vault.
- **$\Gamma_{shares}$**: The total number of shares currently issued by the vault.
- **$\Delta_{assets}$**: The amount of assets being deposited, withdrawn, or redeemed.
- **$\Delta_{shares}$**: The number of shares being issued or burned.
- **$\iota$**: The vault's total **unrealized loss**.
- **$\sigma$**: The scaling factor derived from `Scale`, used to convert fractional assets into integer shares.

###### 3.1.7.2.1 Deposit

The deposit function calculates the number of shares a user receives for their assets.

**Calculation Logic**

The calculation depends on whether the vault is empty.

- **Initial Deposit**: For the first deposit into an empty vault, shares are calculated using a scaling factor, $\sigma = 10^{\text{Scale}}$, to properly represent fractional assets as whole numbers.
  $$\Delta_{shares} = \Delta_{assets} \times \sigma$$

- **Subsequent Deposits**: For all other deposits, shares are calculated proportionally. The resulting $\Delta_{shares}$ value is **rounded down** to the nearest integer.
  $$\Delta_{shares} = \frac{\Delta_{assets} \times \Gamma_{shares}}{\Gamma_{assets}}$$

Because the share amount is rounded down, the actual assets taken from the depositor ($\Delta_{assets'}$) are recalculated.

$$\Delta_{assets'} = \frac{\Delta_{shares} \times \Gamma_{assets}}{\Gamma_{shares}}$$

##### Vault State Update

The vault's totals are updated with the final calculated amounts.

- **New Total Assets**: $\Gamma_{assets} \leftarrow \Gamma_{assets} + \Delta_{assets'}$
- **New Total Shares**: $\Gamma_{shares} \leftarrow \Gamma_{shares} + \Delta_{shares}$

###### 3.1.7.2.2 Redeem

The redeem function calculates the asset payout for a user burning a specific number of shares.

**Calculation Logic**

The amount of assets a user receives is calculated by finding the proportional value of their shares relative to the vault's total holdings, accounting for any unrealized loss ($\iota$).

$$\Delta_{assets} = \frac{\Delta_{shares} \times (\Gamma_{assets} - \iota)}{\Gamma_{shares}}$$

**Vault State Update**

The vault's totals are reduced after the redemption.

- **New Total Assets**: $\Gamma_{assets} \leftarrow \Gamma_{assets} - \Delta_{assets}$
- **New Total Shares**: $\Gamma_{shares} \leftarrow \Gamma_{shares} - \Delta_{shares}$

###### 3.1.7.2.3 Withdraw

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

##### 3.1.7.3 Withdrawal Policy

Withdrawal policy controls the logic used when removing liquidity from a vault. Each strategy has its own implementation, but it can be used in multiple vaults once implemented. Therefore, different vaults may have different withdrawal policies. The specification introduces the following options:

###### 3.1.7.3.1 `first-come-first-serve`

The First Come, First Serve strategy treats all requests equally, allowing a depositor to redeem any amount of assets provided they have a sufficient number of shares.

#### 3.1.8 Frozen Assets

The issuer of the Vaults asset may enact a freeze either through a [Global Freeze](https://xrpl.org/docs/concepts/tokens/fungible-tokens/freezes/#global-freeze) for IOUs or [locking MPT](../XLS-0033-multi-purpose-tokens/README.md#21122-flags). When the vaults asset is frozen, it can only be withdrawn by specifying the `Destination` account as the `Issuer` of the asset. Similarly, a frozen asset _may not_ be deposited into a vault. Furthermore, when the asset of a vault is frozen, the shares corresponding to the asset may not be transferred.

#### 3.1.9 Transfer Fees

The Vault does not apply the [Transfer Fee](https://xrpl.org/docs/concepts/tokens/transfer-fees) to `VaultDeposit` and `VaultWithdraw` transactions. Furthermore, whenever a protocol moves assets from or to a Vault, the `Transfer Fee` must not be charged.

#### 3.1.10 Invariants

1. A transaction must not modify more than one `Vault` object.
2. `<Vault>.Asset == <Vault>'.Asset` (the asset is immutable).
3. `<Vault>.Account == <Vault>'.Account` (the _pseudo-account_ is immutable).
4. `<Vault>.ShareMPTID == <Vault>'.ShareMPTID` (the share MPT ID is immutable).
5. An updated `Vault` must always have an associated `MPTokenIssuance` (shares) object.
6. `IF MPTokenIssuance(Vault.ShareMPTID).OutstandingAmount == 0 THEN <Vault>'.AssetsTotal == 0 AND <Vault>'.AssetsAvailable == 0`.
7. `MPTokenIssuance(Vault.ShareMPTID).OutstandingAmount <= MPTokenIssuance(Vault.ShareMPTID).MaximumAmount`.
8. `<Vault>'.AssetsAvailable >= 0`.
9. `<Vault>'.AssetsAvailable <= <Vault>'.AssetsTotal`.
10. `<Vault>'.LossUnrealized <= <Vault>'.AssetsTotal - <Vault>'.AssetsAvailable`.
11. `<Vault>'.AssetsTotal >= 0`.
12. `<Vault>'.AssetsMaximum >= 0`.
13. Only `VaultCreate` may create a new `Vault` object.
14. Only `VaultDelete` may delete a `Vault` object.
15. `<Vault>.LossUnrealized == <Vault>'.LossUnrealized` for all vault transactions (only protocol transactions such as `LoanManage` and `LoanPay` may change `LossUnrealized`).

#### 3.1.11 Example JSON

```json
{
  "LedgerEntryType": "Vault",
  "LedgerIndex": "48B33DBFA762ECA23CF37CF1A4F93D6D3EBBA710F62F357CF9ADF1146A0E92B7",
  "Flags": 0,
  "PreviousTxnID": "",
  "PreviousTxnLgrSeq": 0,
  "Sequence": 3990518,
  "OwnerNode": "0",
  "Owner": "rfMpGAdXe6pjgnVisNe5FbCSxQ7YkfQG2D",
  "Account": "rDe7soaAox8bk2Srfi7n7Y1wzbmcn8RksQ",
  "Data": "555344204C656E64696E67205661756C74",
  "Asset": {
    "currency": "USD",
    "issuer": "rGTx5c5zRFtUXj3zsAaTEEhnAkYaH1bFAb"
  },
  "AssetsTotal": "0",
  "AssetsAvailable": "0",
  "LossUnrealized": "0",
  "AssetsMaximum": "100000",
  "ShareMPTID": "000000018AB77A8ADC472FBB7991AA311AAEB5D2FA7A793B",
  "WithdrawalPolicy": 1,
  "Scale": 6
}
```

### 3.2 Transaction: `VaultCreate`

All transactions introduced by this proposal incorporate the [common transaction fields](https://xrpl.org/docs/references/protocol/transactions/common-fields) that are shared by all transactions. Standard fields are only documented in this proposal if needed because this proposal introduces new possible values for such fields.

The `VaultCreate` transaction creates a new `Vault` object.

#### 3.2.1 Fields

| Field Name         | Required |     JSON Type      | Internal Type |      Default Value       | Description                                                                                                                                            |
| ------------------ | :------: | :----------------: | :-----------: | :----------------------: | :----------------------------------------------------------------------------------------------------------------------------------------------------- |
| `TransactionType`  |   Yes    |      `string`      |   `UINT16`    |           `58`           | The transaction type.                                                                                                                                  |
| `Flags`            |   Yes    |      `number`      |   `UINT32`    |            0             | Specifies the flags for the Vault.                                                                                                                     |
| `Data`             |    No    |      `string`      |    `BLOB`     |                          | Arbitrary Vault metadata, limited to 256 bytes.                                                                                                        |
| `Asset`            |   Yes    | `string or object` |    `ISSUE`    |          `N/A`           | The asset (`XRP`, `IOU` or `MPT`) of the Vault.                                                                                                        |
| `AssetsMaximum`    |    No    |      `number`      |   `NUMBER`    |            0             | The maximum asset amount that can be held in a vault.                                                                                                  |
| `MPTokenMetadata`  |    No    |      `string`      |    `BLOB`     |                          | Arbitrary metadata about the share `MPT`, in hex format, limited to 1024 bytes.                                                                        |
| `WithdrawalPolicy` |    No    |      `number`      |    `UINT8`    | `strFirstComeFirstServe` | Indicates the withdrawal strategy used by the Vault.                                                                                                   |
| `DomainID`         |    No    |      `string`      |   `HASH256`   |                          | The `PermissionedDomain` object ID associated with the shares of this Vault.                                                                           |
| `Scale`            |    No    |      `number`      |    `UINT8`    |            6             | The `Scale` specifies the power of 10 ($10^{\text{scale}}$) to multiply an asset's value by when converting it into an integer-based number of shares. |

#### 3.2.2 Flags

| Flag Name                     |  Flag Value  | Description                                                                              |
| ----------------------------- | :----------: | :--------------------------------------------------------------------------------------- |
| `tfVaultPrivate`              | `0x00010000` | Indicates that the vault is private. It can only be set during Vault creation.           |
| `tfVaultShareNonTransferable` | `0x00020000` | Indicates the vault share is non-transferable. It can only be set during Vault creation. |

##### 3.2.3 WithdrawalPolicy

The type indicates the withdrawal strategy supported by the vault. The following values are supported:

| Strategy Name                      |  Value   |                        Description                        |
| ---------------------------------- | :------: | :-------------------------------------------------------: |
| `vaultStrategyFirstComeFirstServe` | `0x0001` | Requests are processed on a first-come-first-serve basis. |

#### 3.2.4 Transaction Fees

The transaction creates an `AccountRoot` object for the `_pseudo-account_`. Therefore, the transaction [must destroy](../XLS-0064-pseudo-account/README.md) one incremental owner reserve amount.

#### 3.2.5 Failure Conditions

##### 3.2.5.1 Data Verification

1. `Data` field exceeds 256 bytes. (`temMALFORMED`)
2. `WithdrawalPolicy` is provided and is not `first-come-first-serve`. (`temMALFORMED`)
3. `DomainID` is provided but is zero. (`temMALFORMED`)
4. `DomainID` is provided but `tfVaultPrivate` flag is not set. (`temMALFORMED`)
5. `AssetsMaximum` is negative. (`temMALFORMED`)
6. `MPTokenMetadata` is provided but is empty or exceeds the maximum length. (`temMALFORMED`)
7. `Scale` is provided and the `Asset` is `XRP` or `MPT` (only valid for `IOU`). (`temMALFORMED`)
8. `Scale` is provided and exceeds 18. (`temMALFORMED`)

##### 3.2.5.2 Protocol-Level Failures

1. The `Asset` is an `IOU` and the issuer account does not exist. (`terNO_ACCOUNT`)
2. The `Asset` is an `IOU` and the issuer has not enabled `lsfDefaultRipple`. (`terNO_RIPPLE`)
3. The `Asset` is an `MPT` and the `MPTokenIssuance` object does not exist. (`tecOBJECT_NOT_FOUND`)
4. The `Asset` is an `MPT` and `lsfMPTCanTransfer` is not set on the `MPTokenIssuance`. (`tecNO_AUTH`)
5. The `Asset`'s issuer is a pseudo-account (e.g. vault shares or AMM LP tokens). (`tecWRONG_ASSET`)
6. The `Asset` is frozen or locked for the transaction submitter. (`tecFROZEN` for `IOU` / `tecLOCKED` for `MPT`)
7. The `PermissionedDomain` object does not exist for the provided `DomainID`. (`tecOBJECT_NOT_FOUND`)
8. The submitting account has insufficient balance to meet the owner reserve. (`tecINSUFFICIENT_RESERVE`)

#### 3.2.6 State Changes

1. Create a new `Vault` ledger object.
2. Create a new `MPTokenIssuance` ledger object for the vault shares.
   1. If the `DomainID` is provided: `MPTokenIssuance(Vault.ShareMPTID).DomainID = DomainID` (Set the Permissioned Domain ID).
   2. Create an `MPToken` object for the Vault Owner to hold Vault Shares.
3. Create a new `AccountRoot`[_pseudo-account_](../XLS-0064-pseudo-account/README.md) object setting the `PseudoOwner` to `VaultID`.

4. If `Vault.Asset` is an `IOU`:
   1. Create a `RippleState` object between the _pseudo-account_ `AccountRoot` and `Issuer` `AccountRoot`.

5. If `Vault.Asset` is an `MPT`:
   1. Create `MPToken` object for the _pseudo-account_ for the `Asset.MPTokenIssuance`.

#### 3.2.7 Invariants

1. The transaction must not modify an existing `Vault` object (i.e. no before-state).
2. `<Vault>'.AssetsAvailable == 0 AND <Vault>'.AssetsTotal == 0 AND <Vault>'.LossUnrealized == 0 AND MPTokenIssuance(Vault.ShareMPTID).OutstandingAmount == 0` (created vault must be empty).
3. `<Vault>'.Account == MPTokenIssuance(Vault.ShareMPTID).Issuer` (shares issuer must equal the vault's _pseudo-account_).
4. The shares issuer `AccountRoot` must exist and must be a _pseudo-account_.
5. The shares issuer _pseudo-account_ must reference the created vault via its `VaultID` field.

#### 3.2.8 Example JSON

```json
{
  "TransactionType": "VaultCreate",
  "Flags": 0,
  "Data": "555344204C656E64696E67205661756C74",
  "Asset": {
    "currency": "USD",
    "issuer": "rGTx5c5zRFtUXj3zsAaTEEhnAkYaH1bFAb"
  },
  "AssetsMaximum": "100000",
  "Account": "rfMpGAdXe6pjgnVisNe5FbCSxQ7YkfQG2D",
  "Fee": "200000",
  "Sequence": 3990518
}
```

### 3.3 Transaction: `VaultSet`

The `VaultSet` updates an existing `Vault` ledger object.

#### 3.3.1 Fields

| Field Name        | Required | JSON Type | Internal Type | Default Value | Description                                                                                                                             |
| ----------------- | :------: | :-------: | :-----------: | :-----------: | :-------------------------------------------------------------------------------------------------------------------------------------- |
| `TransactionType` |   Yes    | `string`  |   `UINT16`    |     `59`      | The transaction type.                                                                                                                   |
| `VaultID`         |   Yes    | `string`  |   `HASH256`   |     `N/A`     | The ID of the Vault to be modified. Must be included when updating the Vault.                                                           |
| `Data`            |    No    | `string`  |    `BLOB`     |               | Arbitrary Vault metadata, limited to 256 bytes.                                                                                         |
| `AssetsMaximum`   |    No    | `number`  |   `NUMBER`    |               | The maximum asset amount that can be held in a vault. The value cannot be lower than the current `AssetsTotal` unless the value is `0`. |
| `DomainID`        |    No    | `string`  |   `HASH256`   |               | The `PermissionedDomain` object ID associated with the shares of this Vault.                                                            |

#### 3.3.2 Failure Conditions

##### 3.3.2.1 Data Verification

1. `VaultID` is zero. (`temMALFORMED`)
2. `Data` is present but empty or exceeds 256 bytes. (`temMALFORMED`)
3. `AssetsMaximum` is negative. (`temMALFORMED`)
4. None of `DomainID`, `AssetsMaximum`, or `Data` are present (nothing to update). (`temMALFORMED`)

##### 3.3.2.2 Protocol-Level Failures

1. `Vault` object with the provided `VaultID` does not exist. (`tecNO_ENTRY`)
2. The submitting account is not the `Owner` of the vault. (`tecNO_PERMISSION`)
3. `DomainID` is provided and the vault does not have `lsfVaultPrivate` set. (`tecNO_PERMISSION`)
4. `DomainID` is provided, is non-zero, and the `PermissionedDomain` object does not exist. (`tecOBJECT_NOT_FOUND`)
5. `AssetsMaximum` is non-zero and less than the current `Vault.AssetsTotal`. (`tecLIMIT_EXCEEDED`)

#### 3.3.3 State Changes

1. Update mutable fields in the `Vault` ledger object.
2. If `DomainID` is provided:
   1. Set `MPTokenIssuance(Vault.ShareMPTID).DomainID = DomainID` (Set the Permissioned Domain).

#### 3.3.4 Invariants

1. The _pseudo-account_ asset balance must not change.
2. `<Vault>.AssetsTotal == <Vault>'.AssetsTotal` (assets total must not change).
3. `<Vault>.AssetsAvailable == <Vault>'.AssetsAvailable` (assets available must not change).
4. `IF <Vault>'.AssetsMaximum > 0 THEN <Vault>'.AssetsTotal <= <Vault>'.AssetsMaximum`.
5. `MPTokenIssuance(Vault.ShareMPTID).OutstandingAmount` must not change.

#### 3.3.5 Example JSON

```json
{
  "TransactionType": "VaultSet",
  "VaultID": "48B33DBFA762ECA23CF37CF1A4F93D6D3EBBA710F62F357CF9ADF1146A0E92B7",
  "Data": "5570646174656420566F756C74204D65746164617461",
  "AssetsMaximum": "200000",
  "Account": "rfMpGAdXe6pjgnVisNe5FbCSxQ7YkfQG2D",
  "Fee": "10",
  "Sequence": 3990519
}
```

### 3.4 Transaction: `VaultDelete`

The `VaultDelete` transaction deletes an existing vault object.

#### 3.4.1 Fields

| Field Name        | Required | JSON Type | Internal Type | Default Value |            Description             |
| ----------------- | :------: | :-------: | :-----------: | :-----------: | :--------------------------------: |
| `TransactionType` |   Yes    | `string`  |   `UINT16`    |     `60`      |         Transaction type.          |
| `VaultID`         |   Yes    | `string`  |   `HASH256`   |     `N/A`     | The ID of the vault to be deleted. |

#### 3.4.2 Failure Conditions

##### 3.4.2.1 Data Verification

1. `VaultID` is zero. (`temMALFORMED`)

##### 3.4.2.2 Protocol-Level Failures

1. `Vault` object with the provided `VaultID` does not exist. (`tecNO_ENTRY`)
2. The submitting account is not the `Owner` of the vault. (`tecNO_PERMISSION`)
3. `Vault.AssetsAvailable` is greater than zero. (`tecHAS_OBLIGATIONS`)
4. `Vault.AssetsTotal` is greater than zero. (`tecHAS_OBLIGATIONS`)
5. `MPTokenIssuance(Vault.ShareMPTID).OutstandingAmount` is greater than zero. (`tecHAS_OBLIGATIONS`)
6. The vault pseudo-account's `OwnerCount` is non-zero. (`tecHAS_OBLIGATIONS`)

#### 3.4.3 State Changes

1. Delete the `MPTokenIssuance` object for the vault shares.
2. Delete the `MPToken` or `RippleState` object corresponding to the vault's holding of the asset, if one exists.
3. Delete the `AccountRoot` object of the _pseudo-account_, and its `DirectoryNode` objects.
4. Release the Owner Reserve to the `Vault.Owner` account.
5. Delete the `Vault` object.

#### 3.4.4 Invariants

1. The `Vault` object must be deleted (i.e. no after-state).
2. The `MPTokenIssuance` object for the vault shares must also be deleted.
3. `MPTokenIssuance(Vault.ShareMPTID).OutstandingAmount == 0` (no shares outstanding at time of deletion).
4. `<Vault>.AssetsTotal == 0` (no assets outstanding at time of deletion).
5. `<Vault>.AssetsAvailable == 0` (no assets available at time of deletion).

#### 3.4.5 Example JSON

```json
{
  "TransactionType": "VaultDelete",
  "VaultID": "48B33DBFA762ECA23CF37CF1A4F93D6D3EBBA710F62F357CF9ADF1146A0E92B7",
  "Account": "rfMpGAdXe6pjgnVisNe5FbCSxQ7YkfQG2D",
  "Fee": "10",
  "Sequence": 3990520
}
```

### 3.5 Transaction: `VaultDeposit`

The `VaultDeposit` transaction adds Liqudity in exchange for vault shares.

#### 3.5.1 Fields

| Field Name        | Required |      JSON Type       | Internal Type | Default Value | Description                                            |
| ----------------- | :------: | :------------------: | :-----------: | :-----------: | :----------------------------------------------------- |
| `TransactionType` |   Yes    |       `string`       |   `UINT16`    |     `61`      | Transaction type.                                      |
| `VaultID`         |   Yes    |       `string`       |   `HASH256`   |     `N/A`     | The ID of the vault to which the assets are deposited. |
| `Amount`          |   Yes    | `string` or `object` |  `STAmount`   |     `N/A`     | Asset amount to deposit.                               |

#### 3.5.2 Failure Conditions

##### 3.5.2.1 Data Verification

1. `VaultID` is zero. (`temMALFORMED`)
2. `Amount` is zero or negative. (`temBAD_AMOUNT`)

##### 3.5.2.2 Protocol-Level Failures

1. `Vault` object with the provided `VaultID` does not exist. (`tecNO_ENTRY`)
2. The `Amount` asset does not match `Vault.Asset`. (`tecWRONG_ASSET`)
3. The `Vault.Asset` is an `MPT` and `lsfMPTCanTransfer` is not set on the `MPTokenIssuance` (asset is non-transferable). (`tecNO_AUTH`)
4. The `Vault.Asset` is an `IOU` and rippling is disabled on both the depositor's and vault's trust lines with the issuer. (`terNO_RIPPLE`)
5. The `Vault.Asset` is frozen for the depositor. (`tecFROZEN` for `IOU` / `tecLOCKED` for `MPT`)
6. The vault shares (`MPTokenIssuance`) are locked for the depositor. (`tecLOCKED`)
7. The vault is private, the depositor is not the vault owner, and the vault has no `DomainID` set. (`tecNO_AUTH`)
8. The vault is private, the depositor is not the vault owner, and the depositor does not have valid credentials in the vault's `PermissionedDomain`. (`tecNO_AUTH` / `tecOBJECT_NOT_FOUND`)
9. The `Vault.Asset` is an `MPT` and the depositor does not have an authorized `MPToken` for the asset. (`tecNO_AUTH`)
10. The depositor has insufficient balance to cover `Amount`. (`tecINSUFFICIENT_FUNDS`)
11. Depositing `Amount` would cause `Vault.AssetsTotal` to exceed `Vault.AssetsMaximum`. (`tecLIMIT_EXCEEDED`)
12. The deposit amount rounds down to zero shares due to precision loss. (`tecPRECISION_LOSS`)
13. An arithmetic overflow occurs during share calculation (e.g. large `Scale`). (`tecPATH_DRY`)

#### 3.5.3 State Changes

1. If no `MPToken` object exists for the depositor, create one. For object details, see [2.1.6.2 `MPToken`](#2162-mptoken).

2. Increase the `MPTAmount` field of the share `MPToken` object of the `Account` by $\Delta_{share}$.
3. Increase the `OutstandingAmount` field of the share `MPTokenIssuance` object by $\Delta_{share}$.
4. Increase the `AssetsTotal` and `AssetsAvailable` of the `Vault` by `Amount`.

5. If the `Vault.Asset` is `XRP`:
   1. Increase the `Balance` field of _pseudo-account_ `AccountRoot` by `Amount`.
   2. Decrease the `Balance` field of the depositor `AccountRoot` by `Amount`.

6. If the `Vault.Asset` is an `IOU`:
   1. Increase the `RippleState` balance between the _pseudo-account_ `AccountRoot` and the `Issuer` `AccountRoot` by `Amount`.
   2. Decrease the `RippleState` balance between the depositor `AccountRoot` and the `Issuer` `AccountRoot` by `Amount`.

7. If the `Vault.Asset` is an `MPT`:
   1. Increase the `MPToken.MPTAmount` by `Amount` of the _pseudo-account_ `MPToken` object for the `Vault.Asset`.
   2. Decrease the `MPToken.MPTAmount` by `Amount` of the depositor `MPToken` object for the `Vault.Asset`.

#### 3.5.4 Invariants

Let $\Delta_{asset}$ denote the change in the _pseudo-account_ asset balance and $\Delta_{share}$ denote the change in the depositor's share balance.

1. The _pseudo-account_ asset balance must increase: $\Delta_{asset} > 0$.
2. $\Delta_{asset}$ must not exceed `Amount`.
3. The depositor's asset balance must decrease by $\Delta_{asset}$ (unless the depositor is the asset issuer).
4. `IF <Vault>'.AssetsMaximum > 0 THEN <Vault>'.AssetsTotal <= <Vault>'.AssetsMaximum`.
5. $\Delta_{share} > 0$ (depositor shares must increase).
6. The change in `MPTokenIssuance(Vault.ShareMPTID).OutstandingAmount` must equal $\Delta_{share}$.
7. `<Vault>.AssetsTotal +` $\Delta_{asset}$ `== <Vault>'.AssetsTotal`.
8. `<Vault>.AssetsAvailable +` $\Delta_{asset}$ `== <Vault>'.AssetsAvailable`.

#### 3.5.5 Example JSON

```json
{
  "TransactionType": "VaultDeposit",
  "VaultID": "48B33DBFA762ECA23CF37CF1A4F93D6D3EBBA710F62F357CF9ADF1146A0E92B7",
  "Amount": {
    "currency": "USD",
    "issuer": "rGTx5c5zRFtUXj3zsAaTEEhnAkYaH1bFAb",
    "value": "5000"
  },
  "Account": "raZazWJ29vzR4EdcqKi9fh3TARP6Y11jQx",
  "Fee": "1",
  "Sequence": 3990518
}
```

### 3.6 Transaction: `VaultWithdraw`

The `VaultWithdraw` transaction withdraws assets in exchange for the vault's shares.

#### 3.6.1 Fields

| Field Name        | Required | JSON Type | Internal Type | Default Value | Description                                                                 |
| ----------------- | :------: | :-------: | :-----------: | :-----------: | :-------------------------------------------------------------------------- |
| `TransactionType` |   Yes    | `string`  |   `UINT16`    |     `62`      | Transaction type.                                                           |
| `VaultID`         |   Yes    | `string`  |   `HASH256`   |     `N/A`     | The ID of the vault from which assets are withdrawn.                        |
| `Amount`          |   Yes    | `number`  |  `STAmount`   |       0       | The exact amount of Vault asset to withdraw.                                |
| `Destination`     |    No    | `string`  |  `ACCOUNTID`  |     Empty     | An account to receive the assets. It must be able to receive the asset.     |
| `DestinationTag`  |    No    | `number`  |   `UINT32`    |     Empty     | Arbitrary tag identifying the reason for the withdrawal to the destination. |

- If `Amount` is the Vaults asset, calculate the share cost using the [**Withdraw formula**](#21723-withdraw).
- If `Amount` is the Vaults share, calculate the assets amount using the [**Redeem formula**](#21722-redeem).

In sections below assume the following variables:

- $\Gamma_{share}$ - the total number of shares issued by the vault.
- $\Gamma_{asset}$ - the total assets in the vault, including any future yield.

- $\Delta_{asset}$ - the change in the total amount of assets after a deposit, withdrawal, or redemption.
- $\Delta_{share}$ - che change in the total amount of shares after a deposit, withdrawal, or redemption.

#### 3.6.2 Failure Conditions

##### 3.6.2.1 Data Verification

1. `VaultID` is zero. (`temMALFORMED`)
2. `Amount` is zero or negative. (`temBAD_AMOUNT`)
3. `Destination` is present but is zero. (`temMALFORMED`)

##### 3.6.2.2 Protocol-Level Failures

1. `Vault` object with the provided `VaultID` does not exist. (`tecNO_ENTRY`)
2. The `Amount` asset is neither `Vault.Asset` nor the vault's share `MPTokenIssuance`. (`tecWRONG_ASSET`)
3. The `Vault.Asset` is an `MPT` and `lsfMPTCanTransfer` is not set on the `MPTokenIssuance` (asset is non-transferable). (`tecNO_AUTH`)
4. The `Vault.Asset` is an `IOU` and rippling is disabled on both the vault's and destination's trust lines with the issuer. (`terNO_RIPPLE`)
5. The destination account does not exist. (`tecNO_DST`)
6. The destination account requires a destination tag and none was provided. (`tecDST_TAG_NEEDED`)
7. The destination account has `lsfDepositAuth` set and the submitting account is not preauthorized. (`tecNO_PERMISSION`)
8. The `Vault.Asset` is an `IOU`, the destination is a third party, and the withdrawal amount would exceed the destination's trust line limit. (`tecNO_LINE`)
9. The destination's `IOU` trust line does not exist or is not authorized. (`tecNO_LINE` / `tecNO_AUTH`)
10. The `Vault.Asset` is frozen for the destination account. (`tecFROZEN` for `IOU` / `tecLOCKED` for `MPT`)
11. The vault shares are frozen for the submitting account. (`tecLOCKED`)
12. The submitting account holds fewer shares than required to cover the withdrawal. (`tecINSUFFICIENT_FUNDS`)
13. `Vault.AssetsAvailable` is less than the assets to be withdrawn. (`tecINSUFFICIENT_FUNDS`)
14. The withdrawal amount rounds down to zero shares due to precision loss. (`tecPRECISION_LOSS`)
15. An arithmetic overflow occurs during share calculation (e.g. large `Scale`). (`tecPATH_DRY`)

#### 3.6.3 State Changes

1. If the `Vault.Asset` is XRP:
   1. Decrease the `Balance` field of _pseudo-account_ `AccountRoot` by $\Delta_{asset}$.
   2. Increase the `Balance` field of the depositor `AccountRoot` by $\Delta_{asset}$.

2. If the `Vault.Asset` is an `IOU`:
   1. If the Depositor account does not have a `RippleState` object for the Vaults Asset, create the `RippleState` object.
   2. Decrease the `RippleState` balance between the _pseudo-account_ `AccountRoot` and the `Issuer` `AccountRoot` by $\Delta_{asset}$.
   3. Increase the `RippleState` balance between the depositor `AccountRoot` and the `Issuer` `AccountRoot` by $\Delta_{asset}$.

3. If the `Vault.Asset` is an `MPT`:
   1. If the Depositor account does not have a `MPToken` object for the Vaults Asset, create the `MPToken` object.
   2. Decrease the `MPToken.MPTAmount` by $\Delta_{asset}$ of the _pseudo-account_ `MPToken` object for the `Vault.Asset`.
   3. Increase the `MPToken.MPTAmount` by $\Delta_{asset}$ of the depositor `MPToken` object for the `Vault.Asset`.

4. Update the `MPToken` object for the `Vault.ShareMPTID` of the depositor `AccountRoot`:
   1. Decrease the `MPToken.MPTAmount` by $\Delta_{share}$.
   2. If `MPToken.MPTAmount == 0`, delete the object.

5. Update the `MPTokenIssuance` object for the `Vault.ShareMPTID`:
   1. Decrease the `OutstandingAmount` field of the share `MPTokenIssuance` object by $\Delta_{share}$.

6. Decrease the `AssetsTotal` and `AssetsAvailable` by $\Delta_{asset}$

#### 3.6.4 Invariants

Let $\Delta_{asset}$ denote the change in the _pseudo-account_ asset balance and $\Delta_{share}$ denote the change in the withdrawer's share balance.

1. The _pseudo-account_ asset balance must decrease: $\Delta_{asset} < 0$.
2. Exactly one destination account balance must increase by $|\Delta_{asset}|$ (unless the destination is the asset issuer).
3. $\Delta_{share} < 0$ (withdrawer shares must decrease).
4. The change in `MPTokenIssuance(Vault.ShareMPTID).OutstandingAmount` must equal $\Delta_{share}$.
5. `<Vault>.AssetsTotal +` $\Delta_{asset}$ `== <Vault>'.AssetsTotal`.
6. `<Vault>.AssetsAvailable +` $\Delta_{asset}$ `== <Vault>'.AssetsAvailable`.

#### 3.6.5 Example JSON

```json
{
  "TransactionType": "VaultWithdraw",
  "VaultID": "48B33DBFA762ECA23CF37CF1A4F93D6D3EBBA710F62F357CF9ADF1146A0E92B7",
  "Amount": {
    "currency": "USD",
    "issuer": "rGTx5c5zRFtUXj3zsAaTEEhnAkYaH1bFAb",
    "value": "4083.333642504084"
  },
  "Account": "raZazWJ29vzR4EdcqKi9fh3TARP6Y11jQx",
  "Fee": "1",
  "Sequence": 3990519
}
```

### 3.7 Transaction: `VaultClawback`

The `VaultClawback` transaction performs a Clawback from the Vault, exchanging the shares of an account. Conceptually, the transaction performs `VaultWithdraw` on behalf of the `Holder`, sending the funds to the `Issuer` account of the asset. In case there are insufficient funds for the entire `Amount` the transaction will perform a partial Clawback, up to the `Vault.AssetsAvailable`. The Clawback transaction must respect any future fees or penalties.

#### 3.7.1 Fields

| Field Name        | Required | JSON Type | Internal Type | Default Value | Description                                                                                                    |
| ----------------- | :------: | :-------: | :-----------: | :-----------: | :------------------------------------------------------------------------------------------------------------- |
| `TransactionType` |   Yes    | `string`  |   `UINT16`    |     `63`      | Transaction type.                                                                                              |
| `VaultID`         |   Yes    | `string`  |   `HASH256`   |     `N/A`     | The ID of the vault from which assets are withdrawn.                                                           |
| `Holder`          |   Yes    | `string`  |  `ACCOUNTID`  |     `N/A`     | The account ID from which to clawback the assets.                                                              |
| `Amount`          |    No    | `number`  |   `NUMBER`    |       0       | The asset amount to clawback. When Amount is `0` clawback all funds, up to the total shares the `Holder` owns. |

#### 3.7.2 Failure Conditions

##### 3.7.2.1 Data Verification

1. `VaultID` is zero. (`temMALFORMED`)
2. `Amount` is negative. (`temBAD_AMOUNT`)
3. `Amount` is provided and the asset is `XRP`. (`temMALFORMED`)

##### 3.7.2.2 Protocol-Level Failures

1. `Vault` object with the provided `VaultID` does not exist. (`tecNO_ENTRY`)
2. `Amount` is not provided and `Vault.Asset` is not `XRP`, and the asset issuer is the vault owner — the caller must specify an explicit `Amount` to resolve the ambiguity. (`tecWRONG_ASSET`)
3. The resolved clawback asset is the vault share (`MPTokenIssuance`) and the submitting account is not the vault owner. (`tecNO_PERMISSION`)
4. The resolved clawback asset is the vault share and `Vault.AssetsTotal` or `Vault.AssetsAvailable` is non-zero (vault owner can only burn shares when vault has no assets). (`tecNO_PERMISSION`)
5. The resolved clawback asset is the vault share, `Amount` is non-zero, and it does not equal the holder's full share balance (vault owner must burn all shares at once). (`tecLIMIT_EXCEEDED`)
6. The resolved clawback asset is `Vault.Asset` and `Vault.Asset` is `XRP`. (`tecNO_PERMISSION`)
7. The resolved clawback asset is `Vault.Asset` and the submitting account is not the asset issuer. (`tecNO_PERMISSION`)
8. The submitting account and `Holder` are the same account (issuer cannot clawback from itself). (`tecNO_PERMISSION`)
9. The `Vault.Asset` is an `MPT` and the `MPTokenIssuance` object does not exist. (`tecOBJECT_NOT_FOUND`)
10. The `Vault.Asset` is an `MPT` and `lsfMPTCanClawback` is not set on the `MPTokenIssuance`. (`tecNO_PERMISSION`)
11. The `Vault.Asset` is an `IOU` and the issuer does not have `lsfAllowTrustLineClawback` set, or has `lsfNoFreeze` set. (`tecNO_PERMISSION`)
12. The resolved clawback amount rounds down to zero shares due to precision loss. (`tecPRECISION_LOSS`)
13. An arithmetic overflow occurs during share calculation (e.g. large `Scale`). (`tecPATH_DRY`)

#### 3.7.3 State Changes

1. If the `Vault.Asset` is an `IOU`:
   1. Decrease the `RippleState` balance between the _pseudo-account_ `AccountRoot` and the `Issuer` `AccountRoot` by `min(Vault.AssetsAvailable`, $\Delta_{asset}$`)`.

2. If the `Vault.Asset` is an `MPT`:
   1. Decrease the `MPToken.MPTAmount` by `min(Vault.AssetsAvailable`, $\Delta_{asset}$`)` of the _pseudo-account_ `MPToken` object for the `Vault.Asset`.

3. Update the `MPToken` object for the `Vault.ShareMPTID` of the depositor `AccountRoot`:
   1. Decrease the `MPToken.MPTAmount` by $\Delta_{share}$.
   2. If `MPToken.MPTAmount == 0`, delete the object.

4. Update the `MPTokenIssuance` object for the `Vault.ShareMPTID`:
   1. Decrease the `OutstandingAmount` field of the share `MPTokenIssuance` object by $\Delta_{share}$.

5. Decrease the `AssetsTotal` and `AssetsAvailable` by `min(Vault.AssetsAvailable`, $\Delta_{asset}$`)`

#### 3.7.4 Invariants

Let $\Delta_{asset}$ denote the change in the _pseudo-account_ asset balance and $\Delta_{share}$ denote the change in the holder's share balance.

1. The transaction submitter must be the asset issuer, or the vault owner of an empty vault with outstanding shares.
2. If the vault holds assets: $\Delta_{asset} < 0$ (vault balance must decrease).
3. If the vault holds assets: `<Vault>.AssetsTotal +` $\Delta_{asset}$ `== <Vault>'.AssetsTotal`.
4. If the vault holds assets: `<Vault>.AssetsAvailable +` $\Delta_{asset}$ `== <Vault>'.AssetsAvailable`.
5. $\Delta_{share} < 0$ (holder shares must decrease).
6. The change in `MPTokenIssuance(Vault.ShareMPTID).OutstandingAmount` must equal $\Delta_{share}$.

#### 3.7.5 Example JSON

```json
{
  "TransactionType": "VaultClawback",
  "VaultID": "48B33DBFA762ECA23CF37CF1A4F93D6D3EBBA710F62F357CF9ADF1146A0E92B7",
  "Holder": "raZazWJ29vzR4EdcqKi9fh3TARP6Y11jQx",
  "Amount": "4083333642504084",
  "Account": "rGTx5c5zRFtUXj3zsAaTEEhnAkYaH1bFAb",
  "Fee": "1",
  "Sequence": 3990520
}
```

### 3.8 Transaction: `Payment`

The Single Asset Vault does not introduce new `Payment` transaction fields. However, it adds additional failure conditions and state changes when transfering Vault shares.

#### 3.8.1 Fields

The Single Asset Vault does not introduce or modify any `Payment` transaction fields. Refer to the existing [Payment transaction fields](https://xrpl.org/docs/references/protocol/transactions/types/payment).

#### 3.8.2 Failure Conditions

1. If `Payment.Amount` is a `Vault` share AND:
   1. The `Vault` `lsfVaultPrivate` flag is set and the `Payment.Destination` account does not have credentials in the permissioned domain of the Vaults Share.
   2. The `Vault` `tfVaultShareNonTransferable` flag is set.

   3. The `Vault.Asset` is `MPT`:
      1. `MPTokenIssuance.lsfMPTCanTransfer` is not set (the asset is not transferable).
      2. `MPTokenIssuance.lsfMPTLocked` flag is set (the asset is globally locked).
      3. `MPToken(MPTokenIssuanceID, ACCOUNTID).lsfMPTLocked` flag is set (the asset is locked for the payer).
      4. `MPToken(MPTokenIssuanceID, PseudoACCOUNTID).lsfMPTLocked` flag is set (the asset is locked for the `pseudo-account`).
      5. `MPToken(MPTokenIssuanceID, Destination).lsfMPTLocked` flag is set (the asset is locked for the destination account).

   4. The `Vault.Asset` is an `IOU`:
      1. The `lsfGlobalFreeze` flag is set on the issuing account (the asset is frozen).
      2. The `lsfHighFreeze` or `lsfLowFreeze` flag is set on the `RippleState` object between the Asset `Issuer` and the payer account.
      3. The `lsfHighFreeze` or `lsfLowFreeze` flag is set on the `RippleState` object between the Asset `Issuer` and the destination account.
      4. The `lsfHighFreeze` or `lsfLowFreeze` flag is set on the `RippleState` object between the Asset `Issuer` and the `pseudo-account`.

#### 3.8.3 State Changes

1. If `MPToken`object for shares does not exist for the destination account, create one.

#### 3.8.4 Example JSON

```json
{}
```

### 3.9 RPC: `vault_info`

This RPC retrieves the Vault ledger entry and the IDs associated with it.

#### 3.9.1 Request Fields

| Field Name | Required? | JSON Type |                Description                 |
| ---------- | :-------: | :-------: | :----------------------------------------: |
| `command`  |    Yes    | `string`  |          Must be `"vault_info"`.           |
| `vault`    |    Yes    | `string`  | The object ID of the Vault to be returned. |

#### 3.9.2 Response Fields

| Field Name                       | Always Present? | JSON Type | Description                                                                                                                                            |
| -------------------------------- | :-------------: | :-------: | ------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `vault`                          |       Yes       | `object`  | Root object representing the vault.                                                                                                                    |
| `vault.Account`                  |       Yes       | `string`  | The pseudo-account ID of the vault.                                                                                                                    |
| `vault.Asset`                    |       Yes       | `object`  | Object representing the asset held in the vault.                                                                                                       |
| `vault.Asset.currency`           |   Conditional   | `string`  | Currency code of the asset. Present when the asset is `XRP` or an `IOU`.                                                                               |
| `vault.Asset.issuer`             |   Conditional   | `string`  | Issuer address of the asset. Present when the asset is an `IOU`.                                                                                       |
| `vault.Asset.mpt_issuance_id`    |   Conditional   | `string`  | The `MPTokenIssuance` ID of the asset. Present when the asset is an `MPT`.                                                                             |
| `vault.AssetsAvailable`          |       Yes       | `string`  | Amount of assets currently available for withdrawal.                                                                                                   |
| `vault.AssetsTotal`              |       Yes       | `string`  | Total amount of assets in the vault.                                                                                                                   |
| `vault.Data`                     |       No        | `string`  | Arbitrary metadata about the Vault, in hex format.                                                                                                     |
| `vault.Flags`                    |       Yes       | `number`  | Bit-field flags associated with the vault.                                                                                                             |
| `vault.LedgerEntryType`          |       Yes       | `string`  | Ledger entry type, always `"Vault"`.                                                                                                                   |
| `vault.LossUnrealized`           |       Yes       | `string`  | Unrealized loss associated with the vault.                                                                                                             |
| `vault.Owner`                    |       Yes       | `string`  | ID of the Vault Owner account.                                                                                                                         |
| `vault.OwnerNode`                |       Yes       | `string`  | Identifier for the owner node in the ledger tree.                                                                                                      |
| `vault.PreviousTxnID`            |       Yes       | `string`  | Transaction ID of the last modification to this vault.                                                                                                 |
| `vault.PreviousTxnLgrSeq`        |       Yes       | `number`  | Ledger sequence number of the last transaction modifying this vault.                                                                                   |
| `vault.Scale`                    |       Yes       | `number`  | The `Scale` specifies the power of 10 ($10^{\text{scale}}$) to multiply an asset's value by when converting it into an integer-based number of shares. |
| `vault.Sequence`                 |       Yes       | `number`  | Sequence number of the vault entry.                                                                                                                    |
| `vault.ShareMPTID`               |       Yes       | `string`  | Multi-purpose token ID associated with the vault's shares.                                                                                             |
| `vault.WithdrawalPolicy`         |       Yes       | `number`  | Policy defining withdrawal conditions.                                                                                                                 |
| `vault.index`                    |       Yes       | `string`  | Unique index of the vault ledger entry.                                                                                                                |
| `vault.shares`                   |       Yes       | `object`  | Object containing details about issued shares.                                                                                                         |
| `vault.shares.DomainID`          |       No        | `string`  | The `PermissionedDomain` object ID associated with the shares, if set.                                                                                 |
| `vault.shares.Flags`             |       Yes       | `number`  | Bit-field flags associated with the shares issuance.                                                                                                   |
| `vault.shares.Issuer`            |       Yes       | `string`  | The ID of the Issuer of the Share. It will always be the pseudo-account ID.                                                                            |
| `vault.shares.LedgerEntryType`   |       Yes       | `string`  | Ledger entry type, always `"MPTokenIssuance"`.                                                                                                         |
| `vault.shares.MPTokenMetadata`   |       No        | `string`  | Arbitrary metadata about the share MPT, in hex format.                                                                                                 |
| `vault.shares.OutstandingAmount` |       Yes       | `string`  | Total outstanding shares issued.                                                                                                                       |
| `vault.shares.OwnerNode`         |       Yes       | `string`  | Identifier for the owner node of the shares.                                                                                                           |
| `vault.shares.PreviousTxnID`     |       Yes       | `string`  | Transaction ID of the last modification to the shares issuance.                                                                                        |
| `vault.shares.PreviousTxnLgrSeq` |       Yes       | `number`  | Ledger sequence number of the last transaction modifying the shares issuance.                                                                          |
| `vault.shares.Sequence`          |       Yes       | `number`  | Sequence number of the shares issuance entry.                                                                                                          |
| `vault.shares.index`             |       Yes       | `string`  | Unique index of the shares ledger entry.                                                                                                               |
| `vault.shares.mpt_issuance_id`   |       Yes       | `string`  | The ID of the `MPTokenIssuance` object. It will always be equal to `vault.ShareMPTID`.                                                                 |

#### 3.9.3 Failure Conditions

1. The `vault` field is not provided or is not a valid object ID (`invalidParams`).
2. The `Vault` object with the specified ID does not exist on the ledger (`entryNotFound`).

#### 3.9.4 Example Request

```json
{
  "command": "vault_info",
  "vault": "48B33DBFA762ECA23CF37CF1A4F93D6D3EBBA710F62F357CF9ADF1146A0E92B7"
}
```

#### 3.9.5 Example Response

Vault holding an `IOU`:

```json
{
  "result": {
    "ledger_current_index": 7,
    "validated": false,
    "vault": {
      "Account": "rKwvc1mgHLyHKY3yRUqVwffWtsxYb3QLWf",
      "Asset": {
        "currency": "USD",
        "issuer": "r9cZ5oHbdL4Z9Maj6TdnfAos35nVzYuNds"
      },
      "AssetsAvailable": "100",
      "AssetsTotal": "100",
      "Flags": 0,
      "LedgerEntryType": "Vault",
      "LossUnrealized": "0",
      "Owner": "rwhaYGnJMexktjhxAKzRwoCcQ2g6hvBDWu",
      "OwnerNode": "0",
      "PreviousTxnID": "1484794AE38DBB7C6F4E0B7536CC560B418135BEDB0F8904349F7F8A3B496826",
      "PreviousTxnLgrSeq": 6,
      "Sequence": 5,
      "ShareMPTID": "00000001C752C42A1EBD6BF2403134F7CFD2F1D835AFD26E",
      "WithdrawalPolicy": 1,
      "index": "2DE64CA41250EF3CB7D2B127D6CEC31F747492CAE2BD1628CA02EA1FFE7475B3",
      "shares": {
        "DomainID": "3B61A239626565A3FBEFC32863AFBF1AD3325BD1669C2C9BC92954197842B564",
        "Flags": 0,
        "Issuer": "rKwvc1mgHLyHKY3yRUqVwffWtsxYb3QLWf",
        "LedgerEntryType": "MPTokenIssuance",
        "OutstandingAmount": "100",
        "OwnerNode": "0",
        "PreviousTxnID": "1484794AE38DBB7C6F4E0B7536CC560B418135BEDB0F8904349F7F8A3B496826",
        "PreviousTxnLgrSeq": 6,
        "Sequence": 1,
        "index": "F84AE266C348540D7134F1A683392C3B97C3EEFDE9FEF6F2055B3B92550FB44A",
        "mpt_issuance_id": "00000001C752C42A1EBD6BF2403134F7CFD2F1D835AFD26E"
      }
    }
  },
  "status": "success",
  "type": "response"
}
```

Vault holding an `MPT`:

```json
{
  "result": {
    "ledger_current_index": 3990828,
    "validated": false,
    "vault": {
      "Account": "rQhUcbJoDfvgXr1EkMwarLP5QT3XinEBDg",
      "Asset": {
        "mpt_issuance_id": "002F830036E4E56185F871D70CFFC7BDD554F897606BB6D3"
      },
      "Data": "50726976617465207661756C7420666F72207475746F7269616C73",
      "Flags": 65536,
      "LedgerEntryType": "Vault",
      "Owner": "rJdYtgaiEgzL7xD2QdPKg5xoHkWc7CZjvm",
      "OwnerNode": "0",
      "PreviousTxnID": "F73B073028D7EF14C5DD907591E579EBFEDBA891F4AE0B951439C240C42AE0D4",
      "PreviousTxnLgrSeq": 3113735,
      "Sequence": 3113728,
      "ShareMPTID": "00000001FCE5D5E313303F3D0C700789108CC6BE7D711493",
      "WithdrawalPolicy": 1,
      "index": "9E48171960CD9F62C3A7B6559315A510AE544C3F51E02947B5D4DAC8AA66C3BA",
      "shares": {
        "DomainID": "17060E04AD63975CDE5E4B0C6ACB95ABFA2BA1D569473559448B6E556F261D4A",
        "Flags": 60,
        "Issuer": "rQhUcbJoDfvgXr1EkMwarLP5QT3XinEBDg",
        "LedgerEntryType": "MPTokenIssuance",
        "MPTokenMetadata": "7B226163223A2264656669222C226169223A7B226578616D706C655F696E666F223A2274657374227D2C2264223A2250726F706F7274696F6E616C206F776E65727368697020736861726573206F6620746865207661756C74222C2269223A226578616D706C652E636F6D2F7661756C742D7368617265732D69636F6E2E706E67222C22696E223A225661756C74204F776E6572222C226E223A225661756C7420536861726573222C2274223A22534841524531222C227573223A5B7B2263223A2277656273697465222C2274223A2241737365742057656273697465222C2275223A226578616D706C652E636F6D2F6173736574227D2C7B2263223A22646F6373222C2274223A22446F6373222C2275223A226578616D706C652E636F6D2F646F6373227D5D7D",
        "OutstandingAmount": "0",
        "OwnerNode": "0",
        "PreviousTxnID": "F73B073028D7EF14C5DD907591E579EBFEDBA891F4AE0B951439C240C42AE0D4",
        "PreviousTxnLgrSeq": 3113735,
        "Sequence": 1,
        "index": "F231A0382544EC0ABE810A9D292F3BD455A21CD13CC1DFF75EAFE957A1C8CAB4",
        "mpt_issuance_id": "00000001FCE5D5E313303F3D0C700789108CC6BE7D711493"
      }
    }
  },
  "status": "success",
  "type": "response"
}
```

Vault holding `XRP`:

```json
{
  "result": {
    "ledger_hash": "6FFF56DF92D54D01EE3D5487787F4430D66F89C6BC74B00C276262A0207B2FAD",
    "ledger_index": 6,
    "validated": true,
    "vault": {
      "Account": "rBVxExjRR6oDMWCeQYgJP7q4JBLGeLBPyv",
      "Asset": {
        "currency": "XRP"
      },
      "AssetsAvailable": "0",
      "AssetsTotal": "0",
      "Flags": 0,
      "LedgerEntryType": "Vault",
      "LossUnrealized": "0",
      "Owner": "rwhaYGnJMexktjhxAKzRwoCcQ2g6hvBDWu",
      "OwnerNode": "0",
      "PreviousTxnID": "25C3C8BF2C9EE60DFCDA02F3919D0C4D6BF2D0A4AC9354EFDA438F2ECDDA65E4",
      "PreviousTxnLgrSeq": 5,
      "Sequence": 4,
      "ShareMPTID": "00000001732B0822A31109C996BCDD7E64E05D446E7998EE",
      "WithdrawalPolicy": 1,
      "index": "C043BB1B350FFC5FED21E40535609D3D95BC0E3CE252E2F69F85BE0157020A52",
      "shares": {
        "DomainID": "3B61A239626565A3FBEFC32863AFBF1AD3325BD1669C2C9BC92954197842B564",
        "Flags": 56,
        "Issuer": "rBVxExjRR6oDMWCeQYgJP7q4JBLGeLBPyv",
        "LedgerEntryType": "MPTokenIssuance",
        "OutstandingAmount": "0",
        "OwnerNode": "0",
        "PreviousTxnID": "25C3C8BF2C9EE60DFCDA02F3919D0C4D6BF2D0A4AC9354EFDA438F2ECDDA65E4",
        "PreviousTxnLgrSeq": 5,
        "Sequence": 1,
        "index": "4B25BDE141E248E5D585FEB6100E137D3C2475CEE62B28446391558F0BEA23B5",
        "mpt_issuance_id": "00000001732B0822A31109C996BCDD7E64E05D446E7998EE"
      }
    }
  },
  "status": "success",
  "type": "response"
}
```

## 4. Rationale

The Single Asset Vault is intentionally decoupled from the protocols that rely on it for liquidity. Rather than embedding liquidity provisioning logic into each protocol the vault provides a reusable on-chain building block that a protocol can connect to. This separation means that protocol developers do not need to implement liquidity provisioning mechanics they simply draw from and return assets to the vault, while the vault handles share accounting, access control, and asset custody independently.

This design was chosen over a tightly-coupled alternative where each protocol manages its own depositor pool, because:

- **Reusability**: A single vault implementation serves multiple protocols, reducing code duplication and the surface area for bugs.
- **Composability**: Vault shares are first-class MPT assets that can be transferred, escrowed, or used in other DeFi protocols.
- **Separation of concerns**: Protocols connecting to the vault only need to track their debt and update vault state through well-defined interfaces, rather than managing individual depositor balances.

## 5. Security Considerations

The security properties of the Single Asset Vault are enforced through the invariant checks described in sections 3.1.10 and 3.2.7 through 3.7.4. These invariants guarantee conservation of assets across deposits, withdrawals, and clawbacks, immutability of critical vault parameters, and correctness of share issuance and redemption.

# Appendix

## Appendix A: FAQ

### A.1 Why does the specification allow both `Withdraw` and `Redeem` and not just one of them?

We chose this design in order to reduce the amount of off-chain math required to be implemented by XRPL users and/or developers

### A.2 Why can any account that holds Vaults shares submit a `VaultWithdraw` transaction?

The `VaultWithdraw` transaction does not respect the permissioned domain rules. In other words, any account that holds the shares of the Vault can withdraw them.

The decision was made to avoid a situation where a depositor deposits assets to a private vault to then have their access revoked by invalidating their credentials, and thus loosing access to their funds.

### A.3 How can a depositor transfer shares to another account?

Vault shares are a first-class assets, meaning that they can be transfered and used in other on-ledger protocols that support MPTokens. However, the payee (or the receiver) of the shares must have permissions to hold the shares and the assset that the shares represent. For example, if the shares are for a private Vault containing `USDC` the destination account must be in the permissioned domain of the Vault, and have permissions to hold `USDC`.

In addion, any compliance mechanisms applied to `USDC` will also apply to the share. For example, if the Issuer of `USDC` freezes the Trustline of the payee, then the payee will not be able to receive any shares representing `USDC`.

### A.4 What is the difference between the `VaultOwner` and the `pseudo-account`?

XRP Ledger is an account based blockchain. That means that assets (XRP, IOU and MPT) must be held by an account. The Vault Object (or any other object, such as the AMM) cannot hold assets directly. Therefore, a pseudo-account is created that holds the assets on behalf of that object. The pseudo-account is a stand-alone account, that cannot receive funds, it cannot send transactions, it is there to only hold assets. So for example, when a depositor deposits assets into a vault, in reality this transaction moves the assets from the depositor account to the pseudo-account. Furthermore, the Vault `pseudo-account` is the Issuer of the Vault shares.

### A.5 Do `VaultDeposit` or `VaultWithdraw` transactions charge transfer fees?

No, neither of the transactions charge transfer fees when depositing or withdrawing assets to and from the Vault.
