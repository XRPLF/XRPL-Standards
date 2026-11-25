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
  updated: 2026-11-25
</pre>

# Single Asset Vault

## 1. Abstract

A Single Asset Vault is a new on-chain primitive for aggregating assets from one or more depositors, and making the assets available for other on-chain protocols. The Single Asset Vault uses [Multi-Purpose-Token](../XLS-0033-multi-purpose-tokens/README.md) to represent ownership shares of the Vault. A Vault may be open-ended, with ongoing deposits and withdrawals, or closed-ended, with fixed Subscription, Investment, and Redemption phases. The Vault serves diverse purposes, such as lending markets, aggregators, yield-bearing tokens, asset management, etc. The Single Asset Vault decouples the liquidity provision functionality from the specific protocol logic.

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

### 2.5. Vault Kinds

Under `LendingProtocolV1_1`, a Vault is either **open-ended** or **closed-ended**. The kind is chosen at creation (`VaultKind`) and cannot change afterward.

An **open-ended** Vault is the original Single Asset Vault. Depositors may deposit and withdraw whenever the other Vault rules allow. It has no subscription window, no investment lock-up, and no redemption date. Absence of `VaultKind`, or `VaultKind = 0`, means open-ended.

A **closed-ended** Vault is a fixed-term fund. It raises capital for a limited period, holds that capital for a fixed investment term, then opens for redemption. Once investment has begun, new deposits are rejected and withdrawals are blocked until redemption starts. The schedule is set at creation by two immutable timestamps:

- **`SubscriptionDate`** — last moment of fundraising. After it, the Vault enters investment and the pool size is fixed.
- **`RedemptionDate`** — first moment of wind-down. From then on, depositors may withdraw again; new deposits remain closed.

Between those dates the Vault is in **Investment**: capital stays in place so a connected protocol (for example the Lending Protocol) can deploy a known amount for a known term. The current phase is derived from the parent ledger close time; it is not a stored field. Open-ended Vaults have no phase. The closed-ended lifecycle, field rules, and deposit/withdraw gates are specified in [XLS-65.4.4](./65.4-lending-protocol-v1_1/65.4.4-closed-ended-vault.md).

### 2.6. Terminology

- **Vault**: A ledger entry for aggregating liquidity and providing this liquidity to one or more accessors.
- **Asset**: The currency of a vault. It is either XRP, a [Fungible Token](https://xrpl.org/docs/concepts/tokens/fungible-tokens/) or a [Multi-Purpose Token](../XLS-0033-multi-purpose-tokens/README.md).
- **Share**: Shares represent the depositors' portion of the vault's assets. Shares are a [Multi-Purpose Token](../XLS-0033-multi-purpose-tokens/README.md) created by the _pseudo-account_ of the vault.
- **Open-ended Vault**: A Vault with no fixed fundraising or lock-up schedule. Deposit and withdraw timing follow only the other Vault rules.
- **Closed-ended Vault**: A Vault with immutable `SubscriptionDate` and `RedemptionDate`, moving through Subscription, Investment, and Redemption.
- **Subscription**: The fundraising phase of a closed-ended Vault. Deposits and withdrawals are both allowed.
- **Investment**: The lock-up phase. Deposits and withdrawals are both rejected so deployed capital stays in place.
- **Redemption**: The wind-down phase. Withdrawals are allowed again; deposits remain rejected.

### 2.7. Actors

- **Vault Owner**: An account responsible for creating and deleting The Vault.
- **Depositor**: An entity that deposits and withdraws assets to and from the vault.

### 2.8. Connecting to the Vault

A protocol connecting to a Vault must track its debt. Furthermore, the updates to the Vault state when funds are removed or added back must be handled in the transactors of the protocol. For an example, please refer to the [Lending Protocol](../XLS-0066-lending-protocol/README.md) specification.

### 2.9. Amendments

- `SingleAssetVault` (`featureSingleAssetVault`): the original vault amendment. It introduced the `Vault` ledger entry and the vault transactions; that behaviour is the parent of the patches below.
- `fixCleanup3_1_3`, as described in [XLS-65.1](./65.1-fix-cleanup-3_1_3/README.md):
  - checks a share-denominated `VaultWithdraw` against the destination's trust-line limit at the asset value of the shares, and clamps a zero-`Amount` `VaultClawback` to `Vault.AssetsAvailable`
- `fixCleanup3_2_0`, as described in [XLS-65.2](./65.2-fix-cleanup-3_2_0/README.md):
  - rounds `VaultDeposit` to the posterior Vault precision, waives `LossUnrealized` for a sole shareholder, empties the Vault exactly on a full redemption, waives `lsfMPTCanTransfer` on withdrawal, and records `ReferenceHolding` on the share issuance
- `fixCleanup3_3_0`, as described in [XLS-65.3](./65.3-fix-cleanup-3_3_0/README.md):
  - replaces the `VaultDeposit` and `VaultWithdraw` freeze checks with checks on the depositor or submitter, the pseudo-account, and the destination
- `LendingProtocolV1_1`, as described in [XLS-65.4](./65.4-lending-protocol-v1_1/README.md):
  - [65.4.1 Unmodifiable Vault Fields](./65.4-lending-protocol-v1_1/65.4.1-unmodifiable-vault-fields.md): makes `Sequence`, `OwnerNode`, `Owner`, `WithdrawalPolicy`, `Scale` and `LEVersion` immutable on the Vault once set
  - [65.4.2 Vault Deletion Memo](./65.4-lending-protocol-v1_1/65.4.2-vault-deletion-memo.md): adds an optional `MemoData` field to `VaultDelete` that, if present, must be 1–256 bytes
  - [65.4.3 Cash-Basis Vault](./65.4-lending-protocol-v1_1/65.4.3-cash-basis-vault.md): adds `LEVersion`; Vaults created under the amendment recognise Loan interest when it is paid, and are not subject to the `LoanSet` cap checks
  - [65.4.4 Closed-Ended Vault](./65.4-lending-protocol-v1_1/65.4.4-closed-ended-vault.md): adds the `ClosedEnded` vault kind with `SubscriptionDate` and `RedemptionDate`, and phase-gates `VaultDeposit` and `VaultWithdraw` on such vaults
- `fixCleanup3_4_0`, as described in [XLS-65.5](./65.5-fix-cleanup-3_4_0/README.md):
  - admits one unit of rounding slack in the `LossUnrealized` invariant and in IOU accounting and state-change deltas for `VaultDeposit`, `VaultWithdraw` and `VaultClawback`, requires `LossUnrealized` to be non-negative, and narrows `VaultSet` cap enforcement to transactions that supply `AssetsMaximum` or otherwise change the cap
  - truncates the shares burned by `VaultWithdraw` and `VaultClawback`, adds `CredentialIDs` and private-Vault domain checks to third-party `VaultWithdraw`, and refuses a pseudo-account as withdrawal destination or clawback holder
- `fixCleanup3_5_0`, as described in [XLS-65.6](./65.6-fix-cleanup-3_5_0/README.md):
  - charges the asset transfer fee on third-party `VaultWithdraw`, rejects an unrepresentable `AssetsMaximum`, and refuses a `VaultClawback` against a missing holder
- `LendingProtocolV1_2`, as described in [XLS-65.7](./65.7-lending-protocol-v1_2/README.md):
  - [65.7.1 Fixed Precision Vault](./65.7-lending-protocol-v1_2/65.7.1-fixed-precision.md): fixes one precision grid per new Vault, adds `AssetsDeployed` and `YieldUnrealized`, derives `AssetsTotal`, and bounds optional inflows by capacity
  - [65.7.2 Vault Transactions in Batch](./65.7-lending-protocol-v1_2/65.7.2-vault-transactions-in-batch.md): allows the Vault transactions as `Batch` inner transactions

## 3. Specification

### 3.1 Ledger Entry: `Vault`

The **`Vault`** ledger entry describes the state of the tokenized vault.

#### 3.1.1 Object Identifier

The key of the `Vault` object is the result of [`SHA512-Half`](https://xrpl.org/docs/references/protocol/data-types/basic-data-types/#hashes) of the following values concatenated in order:

- The `Vault` space key `0x0056` (capital V)
- The [`AccountID`](https://xrpl.org/docs/references/protocol/binary-format/#accountid-fields) of the account submitting the `VaultCreate` transaction, i.e. `VaultOwner`.
- The transaction `Sequence` number. If the transaction used a [Ticket](https://xrpl.org/docs/concepts/accounts/tickets/), use the `TicketSequence` value.

#### 3.1.2 Fields

A vault has the following fields:

| Field Name          | Constant |  Required   |     JSON Type      | Internal Type | Default Value | Description                                                                                                                                                                                                                                                                                                                                                             |
| ------------------- | :------: | :---------: | :----------------: | :-----------: | :-----------: | :---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `LedgerEntryType`   |    No    |     Yes     |      `string`      |   `UINT16`    |   `0x0084`    | Ledger object type.                                                                                                                                                                                                                                                                                                                                                     |
| `LedgerIndex`       |    No    |     Yes     |      `string`      |   `UINT16`    |     `N/A`     | Ledger object identifier.                                                                                                                                                                                                                                                                                                                                               |
| `Flags`             |   Yes    |     Yes     |      `string`      |   `UINT32`    |       0       | Ledger object flags.                                                                                                                                                                                                                                                                                                                                                    |
| `PreviousTxnID`     |    No    |     Yes     |      `string`      |   `HASH256`   |     `N/A`     | Identifies the transaction ID that most recently modified this object.                                                                                                                                                                                                                                                                                                  |
| `PreviousTxnLgrSeq` |    No    |     Yes     |      `number`      |   `UINT32`    |     `N/A`     | The sequence of the ledger that contains the transaction that most recently modified this object.                                                                                                                                                                                                                                                                       |
| `Sequence`          |    No    |     Yes     |      `number`      |   `UINT32`    |     `N/A`     | The transaction sequence number that created the vault.                                                                                                                                                                                                                                                                                                                 |
| `OwnerNode`         |    No    |     Yes     |      `number`      |   `UINT64`    |     `N/A`     | Identifies the page where this item is referenced in the owner's directory.                                                                                                                                                                                                                                                                                             |
| `Owner`             |    No    |     Yes     |      `string`      |  `AccountID`  |     `N/A`     | The account address of the Vault Owner.                                                                                                                                                                                                                                                                                                                                 |
| `Account`           |    No    |     Yes     |      `string`      |  `AccountID`  |     `N/A`     | The address of the Vaults _pseudo-account_.                                                                                                                                                                                                                                                                                                                             |
| `Data`              |   Yes    |     No      |      `string`      |    `BLOB`     |     None      | Arbitrary metadata about the Vault. Limited to 256 bytes.                                                                                                                                                                                                                                                                                                               |
| `Asset`             |    No    |     Yes     | `string or object` |    `ISSUE`    |     `N/A`     | The asset of the vault. The vault supports `XRP`, `IOU` and `MPT`.                                                                                                                                                                                                                                                                                                      |
| `AssetsTotal`       |    No    |     Yes     |      `number`      |   `NUMBER`    |       0       | The total value of the vault. `LendingProtocolV1_1`: on a `CashBasis` Vault it excludes interest not yet paid ([XLS-65.4.3](./65.4-lending-protocol-v1_1/65.4.3-cash-basis-vault.md)). `LendingProtocolV1_2`: on a `FixedPrecision` Vault it is derived from `AssetsAvailable + AssetsDeployed` ([XLS-65.7.1](./65.7-lending-protocol-v1_2/65.7.1-fixed-precision.md)). |
| `AssetsAvailable`   |    No    |     Yes     |      `number`      |   `NUMBER`    |       0       | The asset amount that is available in the vault.                                                                                                                                                                                                                                                                                                                        |
| `LossUnrealized`    |    No    |     Yes     |      `number`      |   `NUMBER`    |       0       | The potential loss amount that is not yet realized expressed as the vaults asset.                                                                                                                                                                                                                                                                                       |
| `AssetsMaximum`     |   Yes    |     No      |      `number`      |   `NUMBER`    |       0       | The maximum asset amount that can be held in the vault. Zero value `0` indicates there is no cap.                                                                                                                                                                                                                                                                       |
| `ShareMPTID`        |    No    |     Yes     |      `number`      |   `UINT192`   |       0       | The identifier of the share MPTokenIssuance object.                                                                                                                                                                                                                                                                                                                     |
| `WithdrawalPolicy`  |    No    |     Yes     |      `string`      |    `UINT8`    |     `N/A`     | Indicates the withdrawal strategy used by the Vault.                                                                                                                                                                                                                                                                                                                    |
| `Scale`             |    No    |     No      |      `number`      |    `UINT8`    |       0       | The `Scale` specifies the power of 10 ($10^{\text{scale}}$) to multiply an asset's value by when converting it into an integer-based number of shares. Stored only when non-zero; absent for `XRP` and `MPT`. `VaultCreate` defaults it to 6 for an `IOU`.                                                                                                              |
| `LEVersion`         |   Yes    |     No      |      `number`      |    `UINT8`    |       0       | `LendingProtocolV1_1`: accounting version of the Vault, set at creation. Absent or `0` is `Legacy`, `1` is `CashBasis` ([XLS-65.4.3](./65.4-lending-protocol-v1_1/65.4.3-cash-basis-vault.md)), `2` is `FixedPrecision` ([XLS-65.7.1](./65.7-lending-protocol-v1_2/65.7.1-fixed-precision.md)).                                                                         |
| `AssetsDeployed`    |    No    |     No      |      `string`      |   `NUMBER`    |       0       | `LendingProtocolV1_2`: principal lent out by a `FixedPrecision` Vault ([XLS-65.7.1](./65.7-lending-protocol-v1_2/65.7.1-fixed-precision.md)).                                                                                                                                                                                                                           |
| `YieldUnrealized`   |    No    |     No      |      `string`      |   `NUMBER`    |       0       | `LendingProtocolV1_2`: scheduled interest owed to a `FixedPrecision` Vault and not yet received ([XLS-65.7.1](./65.7-lending-protocol-v1_2/65.7.1-fixed-precision.md)).                                                                                                                                                                                                 |
| `VaultKind`         |   Yes    |     No      |      `number`      |    `UINT8`    |       0       | `LendingProtocolV1_1`: Vault kind. Absent or `0` is open-ended; `1` is closed-ended.                                                                                                                                                                                                                                                                                    |
| `SubscriptionDate`  |   Yes    | Conditional |      `number`      |   `UINT32`    |     `N/A`     | `LendingProtocolV1_1`: End of Subscription and start of Investment; required for a closed-ended Vault.                                                                                                                                                                                                                                                                  |
| `RedemptionDate`    |   Yes    | Conditional |      `number`      |   `UINT32`    |     `N/A`     | `LendingProtocolV1_1`: Start of Redemption; required for a closed-ended Vault.                                                                                                                                                                                                                                                                                          |

##### 3.1.2.1 Flags

The `Vault` object supports the following flags:

| Flag Name         |  Flag Value  | Modifiable? |                 Description                  |
| ----------------- | :----------: | :---------: | :------------------------------------------: |
| `lsfVaultPrivate` | `0x00010000` |     No      | If set, indicates that the vault is private. |

##### 3.1.2.2 Vault Kind and Phase Derivation

`VaultKind` selects the lifecycle. Under `LendingProtocolV1_1`:

- Absent or `0` (`OpenEnded`): the Vault behaves as before this amendment. It has no phase (`NoPhase`). `SubscriptionDate` and `RedemptionDate` must be absent.
- `1` (`ClosedEnded`): the Vault is a fixed-term fund. Both dates are required and immutable. Deposits are allowed only through the end of Subscription; withdrawals are blocked for the whole Investment interval and allowed again from Redemption onward.

`VaultCreate` rejects an unknown `VaultKind`. Other logic that encounters a future, unknown kind already stored on the ledger treats it as `OpenEnded` and therefore as `NoPhase`.

The phase is not stored. For a closed-ended Vault it is derived from the parent ledger close time, `now`:

| Condition                                 |     Phase      |
| ----------------------------------------- | :------------: |
| `now <= SubscriptionDate`                 | `Subscription` |
| `SubscriptionDate < now < RedemptionDate` |  `Investment`  |
| `now >= RedemptionDate`                   |  `Redemption`  |

`SubscriptionDate` is the last second of Subscription. `RedemptionDate` is the first second of Redemption. Investment is the open interval between them. See [XLS-65.4.4](./65.4-lending-protocol-v1_1/65.4.4-closed-ended-vault.md) for the full closed-ended rules.

#### 3.1.3 Pseudo-Account

An AccountRoot entry holds the XRP, IOU or MPT deposited into the vault. It also acts as the issuer of the vault's shares. The _pseudo-account_ follows the XLS-64 specification for pseudo accounts. The `AccountRoot` object is created when creating the `Vault` object.

- `SingleAssetVault`: What the _pseudo-account_ owns is not checked.
- `fixCleanup3_5_0`: The _pseudo-account_ may own only its share `MPTokenIssuance`, its holding of `Vault.Asset`, and the `LoanBroker` entries of this Vault ([XLS-65.6](./65.6-fix-cleanup-3_5_0/README.md)).

#### 3.1.4 Ownership

The `Vault` objects are stored in the ledger and tracked in an [Owner Directory](https://xrpl.org/docs/references/protocol/ledger-data/ledger-entry-types/directorynode) owned by the account submitting the `VaultCreate` transaction. To find the `Vault` from the vault shares, the _pseudo-account_ that issues the shares has a `VaultID` field pointing back to the `Vault`.

#### 3.1.5 Owner Reserve

`VaultCreate` increases the Vault Owner's `OwnerCount` by 3:

- The `Vault` object itself.
- The _pseudo-account_ `AccountRoot`.
- The Vault Owner's `MPToken` for the vault shares.

The share `MPTokenIssuance` and the _pseudo-account_'s holding of `Vault.Asset` are counted on the _pseudo-account_, not the Vault Owner.

`VaultDelete` decreases the Vault Owner's `OwnerCount` by 2 for the `Vault` and the _pseudo-account_. It also deletes the Vault Owner's share `MPToken`, if one exists.

#### 3.1.6 Vault Shares

Shares represent the portion of the Vault assets a depositor owns. Vault Owners set the currency code of the share and whether the token is transferable during the vault's creation. These two values are immutable. The share is represented by a [Multi-Purpose Token](../XLS-0033-multi-purpose-tokens/README.md). The MPT is issued by the vault's pseudo-account.

##### 3.1.6.1 `Scale`

The **`Scale`** field enables the vault to accurately represent fractional asset values using integer-only MPT shares, which prevents the loss of value from decimal truncation. It defines a scaling factor, calculated as $10^{\text{Scale}}$, that converts a decimal asset amount into a corresponding whole number of shares. For example, with a `Scale` of `6`, a deposit of **20.3** assets is multiplied by $10^6$ and credited as **20,300,000** shares.

As a general rule, all calculations involving MPTs are executed with a precision of a single MPT, treating them as indivisible units. If a calculation results in a fractional amount, it will be rounded up, down or to the nearest whole number depending on the context. Crucially, the rounding direction is determined by the protocol and is not controlled by the transaction submitter, which may lead to unexpected results.

###### 3.1.6.1.1 `IOU`

When a vault holds an **`IOU`**, the `Scale` is configurable by the Vault Owner at the time of the vault's creation. The value can range from **0** to a maximum of **18**, with a default of **6**. This flexibility allows issuers to set a level of precision appropriate for their specific token.

- `SingleAssetVault`: the maximum is **18**.
- `LendingProtocolV1_2`: for a Vault created with `LEVersion` 2, the maximum is **10** ([XLS-65.7.1](./65.7-lending-protocol-v1_2/65.7.1-fixed-precision.md)).

###### 3.1.6.1.2 `XRP`

When a vault holds **`XRP`**, the `Scale` is fixed at **0**. This aligns with XRP's native structure, where one share represents one drop (the smallest unit of XRP), and one XRP equals 1,000,000 drops. Therefore, a deposit of 10 XRP to an empty Vault will result in the issuance of 10,000,000 shares ($10 \times 10^6$).

###### 3.1.6.1.3 `MPT`

When a vault holds `MPT`, its `Scale` is fixed at **0**. This creates a 1-to-1 relationship between deposited MPT units and the shares issued (for example, depositing 10 MPTs to an empty Vault issues 10 shares). The value of a single MPT is determined at the issuer's discretion. If an MPT is set to represent a large value, the vault owner and the depositor must be cautious. Since only whole MPT units are used in calculations, any value that is not a multiple of a single MPT's value may be lost due to rounding during a transaction.

##### 3.1.6.2 `MPTokenIssuance`

The `MPTokenIssuance` object represents the share on the ledger. It is created and deleted together with the `Vault` object.

###### 3.1.6.2.1 `MPTokenIssuance` Values

| **Field**          | **Description**                                                                                                                                  | **Value**            |
| ------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------ | -------------------- |
| `Issuer`           | The AccountID of the Vault's _pseudo-account_.                                                                                                   | _pseudo-account_ ID  |
| `MaximumAmount`    | Not set, so the number of shares that can be issued is bounded only by the protocol maximum.                                                     | _absent_             |
| `TransferFee`      | The fee paid to transfer the shares.                                                                                                             | 0                    |
| `MPTokenMetadata`  | Arbitrary metadata about the share MPT, in hex format.                                                                                           | -                    |
| `AssetScale`       | Represents orders of magnitude between the standard and the MPT unit. For IOUs it is set to `Vault.Scale`, otherwise it is `0`.                  | `Vault.Scale`        |
| `DomainID`         | The `PermissionedDomain` of a private Vault, if `VaultCreate` supplied one.                                                                      | `DomainID` or absent |
| `ReferenceHolding` | `fixCleanup3_2_0`: the ID of the _pseudo-account_'s holding of `Vault.Asset` ([XLS-65.2](./65.2-fix-cleanup-3_2_0/README.md)). Absent for `XRP`. | holding ID or absent |

`VaultCreate` omits `MaximumAmount` on the share issuance rather than storing an explicit cap. The number of shares in issue is therefore bounded by the protocol maximum for an `MPTokenIssuance`, `0x7FFFFFFFFFFFFFFF`, as defined in [XLS-33 §2.1.1.2.5](../XLS-0033-multi-purpose-tokens/README.md#21125-maximumamount).

###### 3.1.6.2.2 Flags

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

A well-informed depositor may learn of an incoming loss and redeem their shares early, causing the remaining depositors to bear the full loss. To discourage such behaviour, we introduce a concept of "paper loss," captured by the `Vault` object's `LossUnrealized` attribute. The "paper loss" captures a potential loss the vault may experience and thus temporarily decreases the vault value. Only a protocol connected to the `Vault` may increase or decrease the `LossUnrealized` attribute; for the [Lending Protocol](../XLS-0066-lending-protocol/README.md) that means `LoanManage` and `LoanPay` alone.

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

The following are the **key variables** used in the calculations:

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

- `SingleAssetVault`: $\Delta_{assets}$ is the deposited `Amount`.
- `fixCleanup3_2_0`: $\Delta_{assets}$ is `Amount` rounded toward zero at the scale of the posterior `Vault.AssetsTotal` ([XLS-65.2](./65.2-fix-cleanup-3_2_0/README.md)).
- `fixCleanup3_4_0`: $\Delta_{assets'}$ is further rounded down at that scale, without recomputing $\Delta_{shares}$ ([XLS-65.5](./65.5-fix-cleanup-3_4_0/README.md)).

###### 3.1.7.2.1.1 Vault State Update

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

This calculated $\Delta_{shares}$ amount is rounded to a whole number:

- `SingleAssetVault`: **rounded to the nearest whole number**.
- `fixCleanup3_4_0`: **truncated** (rounded down), so the payout never exceeds the requested amount ([XLS-65.5](./65.5-fix-cleanup-3_4_0/README.md)).
- `fixCleanup3_5_0`: when `VaultWithdraw` charges a transfer fee, $\Delta_{assets\_requested}$ is the requested amount plus that fee ([XLS-65.6](./65.6-fix-cleanup-3_5_0/README.md)).

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

The Vault does not apply the [Transfer Fee](https://xrpl.org/docs/concepts/tokens/transfer-fees) to `VaultDeposit`, `VaultClawback` or vault share transfers made by the Vault transactions. Furthermore, whenever a protocol moves assets from or to a Vault, the `Transfer Fee` must not be charged.

- `SingleAssetVault`: `VaultWithdraw` does not charge the transfer fee.
- `fixCleanup3_5_0`: `VaultWithdraw` charges the asset's transfer fee when the destination differs from the submitter and neither is the asset issuer ([XLS-65.6](./65.6-fix-cleanup-3_5_0/README.md)).

#### 3.1.10 Invariants

1. `Vault.AssetsAvailable >= 0`.
2. `Vault.AssetsTotal >= 0`.
3. `Vault.AssetsMaximum >= 0`.
4. `Vault.AssetsAvailable <= Vault.AssetsTotal`.
5. - `SingleAssetVault`: `Vault.LossUnrealized <= (Vault.AssetsTotal - Vault.AssetsAvailable)`.
   - `fixCleanup3_4_0`: If `Vault.Asset` is an `IOU`, `Vault.LossUnrealized <= (Vault.AssetsTotal - Vault.AssetsAvailable) + 1 unit` at the scale of `Vault.AssetsTotal`. For `XRP` and `MPT` the comparison remains strict `<=`.
   - `LendingProtocolV1_2`: For a Vault with `LEVersion` 2, `Vault.LossUnrealized <= Vault.AssetsDeployed` replaces both rules above ([XLS-65.7.1](./65.7-lending-protocol-v1_2/65.7.1-fixed-precision.md)).
6. - `SingleAssetVault`: The check does not apply.
   - `fixCleanup3_4_0`: `Vault.LossUnrealized >= 0`, for every asset type.
7. If `MPTokenIssuance(Vault.ShareMPTID).OutstandingAmount == 0`: `Vault.AssetsTotal == 0` and `Vault.AssetsAvailable == 0`. `LendingProtocolV1_2`: for a Vault with `LEVersion` 2, also `Vault.AssetsDeployed == 0`.
8. The `MPTokenIssuance` identified by `Vault.ShareMPTID` must exist, and its `OutstandingAmount` must not exceed its `MaximumAmount`. `VaultCreate` leaves `MaximumAmount` absent (§3.1.6.2.1), in which case the bound is the protocol maximum `0x7FFFFFFFFFFFFFFF`.
9. On creation, `Vault.AssetsTotal`, `Vault.AssetsAvailable`, `Vault.LossUnrealized` and the share `MPTokenIssuance.OutstandingAmount` are all zero. The share issuance has `Issuer == Vault.Account`, and `AccountRoot(Vault.Account)` is a _pseudo-account_ whose `VaultID` points to the new vault. Only `VaultCreate` may create a `Vault`.
10. Only `VaultDelete` may delete a `Vault`. It must also delete the share `MPTokenIssuance`, and the deleted vault must have `AssetsTotal == 0`, `AssetsAvailable == 0` and no outstanding shares.
11. There is no invariant requiring `Vault.AssetsTotal <= Vault.AssetsMaximum` to hold on every modification of the entry, because `Vault.AssetsTotal` grows with accrued interest and interest is not a deposit. The cap is instead enforced per transaction, by the checks in items 12 and 13 and by `LoanSet` (see the [Lending Protocol](../XLS-0066-lending-protocol/README.md) §3.8.5.2):
    - `SingleAssetVault`: `LoanSet` fails when `Vault.AssetsMaximum` is non-zero and either `Vault.AssetsTotal >= Vault.AssetsMaximum` or `Vault.AssetsTotal + InterestDue > Vault.AssetsMaximum`.
    - `LendingProtocolV1_1`: those `LoanSet` checks apply only to a Vault without `LEVersion` (`Legacy`). On a Vault with `LEVersion` 1 or later, origination does not change `AssetsTotal` and the checks do not apply ([XLS-65.4.3](./65.4-lending-protocol-v1_1/65.4.3-cash-basis-vault.md)).
12. `VaultDeposit` fails when `Vault.AssetsMaximum` is non-zero and the post-deposit `Vault.AssetsTotal` exceeds it.
13. - `SingleAssetVault`: `VaultSet` fails when `Vault.AssetsMaximum` is non-zero and `Vault.AssetsTotal` exceeds it.
    - `fixCleanup3_4_0`: `VaultSet` fails when `Vault.AssetsMaximum` is non-zero, `Vault.AssetsTotal` exceeds it, and the transaction supplies `AssetsMaximum` or the cap otherwise changes. A cap already exceeded by accrued interest no longer blocks a `VaultSet` that omits `AssetsMaximum` and does not otherwise change the cap.
14. - `SingleAssetVault`: `Vault.Asset`, `Vault.Account` and `Vault.ShareMPTID` are immutable once set.
    - `LendingProtocolV1_1`: `Vault.Sequence`, `Vault.OwnerNode`, `Vault.Owner`, `Vault.WithdrawalPolicy`, `Vault.Scale`, `Vault.LEVersion`, `Vault.VaultKind`, `Vault.SubscriptionDate`, `Vault.RedemptionDate`, `Vault.Asset`, `Vault.Account` and `Vault.ShareMPTID` are immutable once set. If `Vault.LEVersion`, `Vault.VaultKind`, `Vault.SubscriptionDate` or `Vault.RedemptionDate` is absent, it remains absent, except when the transaction creates the entry.
15. `Vault.LossUnrealized` may only be changed by `LoanManage` and `LoanPay`. Every other transaction that modifies the entry must leave it unchanged.
16. A `Vault` is modified only by a transaction type that declares a vault privilege — `VaultCreate`, `VaultSet`, `VaultDelete`, `VaultDeposit`, `VaultWithdraw`, `VaultClawback`, `LoanSet`, `LoanPay` and `LoanManage` — and at most one `Vault` is modified per transaction. `LoanManage` has `MayModifyVault` and may succeed without modifying one; each other listed transaction has `MustModifyVault` and must create, modify or delete one.
17. `LendingProtocolV1_1`: A closed-ended Vault has both `SubscriptionDate` and `RedemptionDate`, and `180 <= RedemptionDate - SubscriptionDate < 946708560`.
18. `LendingProtocolV1_2`: A Vault with `LEVersion` 2 also satisfies the invariants of [XLS-65.7.1](./65.7-lending-protocol-v1_2/65.7.1-fixed-precision.md) §3.3.2.

#### 3.1.11 Example JSON

```json
{
  "LedgerEntryType": "Vault",
  "Account": "rKwvc1mgHLyHKY3yRUqVwffWtsxYb3QLWf",
  "Asset": {
    "currency": "USD",
    "issuer": "r9cZ5oHbdL4Z9Maj6TdnfAos35nVzYuNds"
  },
  "AssetsAvailable": "100",
  "AssetsMaximum": "1000000",
  "AssetsTotal": "100",
  "Flags": 0,
  "LossUnrealized": "0",
  "Owner": "rwhaYGnJMexktjhxAKzRwoCcQ2g6hvBDWu",
  "OwnerNode": "0",
  "PreviousTxnID": "1484794AE38DBB7C6F4E0B7536CC560B418135BEDB0F8904349F7F8A3B496826",
  "PreviousTxnLgrSeq": 6,
  "Scale": 6,
  "Sequence": 5,
  "ShareMPTID": "00000001C752C42A1EBD6BF2403134F7CFD2F1D835AFD26E",
  "WithdrawalPolicy": 1
}
```

### 3.2 Transaction: `VaultCreate`

The `VaultCreate` transaction creates a new `Vault` object.

#### 3.2.1 Fields

| Field Name         |  Required   |     JSON Type      | Internal Type | Default Value | Description                                                                                                                                                                              |
| ------------------ | :---------: | :----------------: | :-----------: | :-----------: | :--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `TransactionType`  |     Yes     |      `string`      |   `UINT16`    |     `65`      | The transaction type (`ttVAULT_CREATE`).                                                                                                                                                 |
| `Flags`            |     Yes     |      `number`      |   `UINT32`    |       0       | Specifies the flags for the Vault.                                                                                                                                                       |
| `Data`             |     No      |      `string`      |    `BLOB`     |               | Arbitrary Vault metadata, limited to 256 bytes.                                                                                                                                          |
| `Asset`            |     Yes     | `string or object` |    `ISSUE`    |     `N/A`     | The asset (`XRP`, `IOU` or `MPT`) of the Vault.                                                                                                                                          |
| `AssetsMaximum`    |     No      |      `number`      |   `NUMBER`    |       0       | The maximum asset amount that can be held in a vault.                                                                                                                                    |
| `MPTokenMetadata`  |     No      |      `string`      |    `BLOB`     |               | Arbitrary metadata about the share `MPT`, in hex format, limited to 1024 bytes.                                                                                                          |
| `WithdrawalPolicy` |     No      |      `number`      |    `UINT8`    |      `1`      | Indicates the withdrawal strategy used by the Vault. Only `1` (`vaultStrategyFirstComeFirstServe`) is accepted.                                                                          |
| `DomainID`         |     No      |      `string`      |   `HASH256`   |               | The `PermissionedDomain` object ID associated with the shares of this Vault.                                                                                                             |
| `Scale`            |     No      |      `number`      |    `UINT8`    |       6       | The `Scale` specifies the power of 10 ($10^{\text{scale}}$) to multiply an asset's value by when converting it into an integer-based number of shares. Accepted only for an `IOU` asset. |
| `VaultKind`        |     No      |      `number`      |    `UINT8`    |       0       | `LendingProtocolV1_1`: `0` is open-ended and `1` is closed-ended.                                                                                                                        |
| `SubscriptionDate` | Conditional |      `number`      |   `UINT32`    |     `N/A`     | `LendingProtocolV1_1`: End of Subscription and start of Investment; required for a closed-ended Vault.                                                                                   |
| `RedemptionDate`   | Conditional |      `number`      |   `UINT32`    |     `N/A`     | `LendingProtocolV1_1`: Start of Redemption; required for a closed-ended Vault.                                                                                                           |

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

`VaultCreate` uses the standard transaction fee. The _pseudo-account_ it creates is paid for through the Vault Owner's reserve (§3.1.5).

#### 3.2.5 Failure Conditions

##### 3.2.5.1 Data Verification

1. The `MPTokensV1` amendment is not enabled. (`temDISABLED`)
2. `DomainID` is present and the `PermissionedDomains` amendment is not enabled. (`temDISABLED`)
3. - `SingleAssetVault`: `VaultKind`, `SubscriptionDate` or `RedemptionDate` is present. (`temDISABLED`)
   - `LendingProtocolV1_1`: The check does not apply.
4. `Flags` has a bit set other than `tfVaultPrivate` and `tfVaultShareNonTransferable`. (`temINVALID_FLAG`)
5. `Data` is present and is empty or longer than 256 bytes. (`temMALFORMED`)
6. `WithdrawalPolicy` is present and is not `1` (`vaultStrategyFirstComeFirstServe`). (`temMALFORMED`)
7. `DomainID` is present and is zero. (`temMALFORMED`)
8. `DomainID` is present and `tfVaultPrivate` is not set. (`temMALFORMED`)
9. `AssetsMaximum` is present and negative. (`temMALFORMED`)
10. - `SingleAssetVault`: The check does not apply.
    - `fixCleanup3_5_0`: `AssetsMaximum` is present and cannot be represented as an amount of `Asset` ([XLS-65.6](./65.6-fix-cleanup-3_5_0/README.md)). (`temMALFORMED`)
11. `MPTokenMetadata` is present and is empty or longer than 1024 bytes. (`temMALFORMED`)
12. `Scale` is present and `Asset` is `XRP` or an `MPT`. (`temMALFORMED`)
13. - `SingleAssetVault`: `Scale` is greater than 18. (`temMALFORMED`)
    - `LendingProtocolV1_2`: When the new Vault will have `LEVersion` 2, `Scale` is greater than 10 ([XLS-65.7.1](./65.7-lending-protocol-v1_2/65.7.1-fixed-precision.md)). (`temMALFORMED`)
14. `LendingProtocolV1_1`: `VaultKind` has an unrecognized value. (`temMALFORMED`)
15. `LendingProtocolV1_1`: `VaultKind` is absent or `OpenEnded`, but `SubscriptionDate` or `RedemptionDate` is present. (`temMALFORMED`)
16. `LendingProtocolV1_1`: `VaultKind` is `ClosedEnded`, but either date is absent. (`temMALFORMED`)
17. `LendingProtocolV1_1`: `VaultKind` is `ClosedEnded` and `SubscriptionDate + 180 > RedemptionDate` or `RedemptionDate >= SubscriptionDate + 946708560`. (`temMALFORMED`)

The sums in check 17 must be computed without 32-bit overflow.

##### 3.2.5.2 Protocol-Level Failures

1. A holding of `Asset` cannot be added:
   1. `Asset` is an `IOU` and its issuer account does not exist. (`terNO_ACCOUNT`)
   2. `Asset` is an `IOU` and its issuer does not have `lsfDefaultRipple` set. (`terNO_RIPPLE`)
   3. `Asset` is an `MPT` and its `MPTokenIssuance` does not exist. (`tecOBJECT_NOT_FOUND`)
   4. `Asset` is an `MPT` and `lsfMPTCanTransfer` is not set on its `MPTokenIssuance`. (`tecNO_AUTH`)
2. `Asset` is issued by a _pseudo-account_, for example the shares of another Vault. (`tecWRONG_ASSET`)
3. `Asset` is frozen for the Vault Owner: for an `IOU`, a global freeze or a freeze on the owner's trust line (`tecFROZEN`); for an `MPT`, a global or individual lock (`tecLOCKED`).
4. `DomainID` is present and the `PermissionedDomain` it names does not exist. (`tecOBJECT_NOT_FOUND`)
5. The _pseudo-account_ address derived for the new Vault is already in use. (`terADDRESS_COLLISION`)
6. `LendingProtocolV1_1`: `VaultKind` is `ClosedEnded` and `SubscriptionDate` is not strictly after the parent ledger close time. (`tecEXPIRED`)
7. `LendingProtocolV1_1`: `VaultKind` is `ClosedEnded` and `RedemptionDate` is not strictly after the parent ledger close time. (`tecEXPIRED`)
8. `LendingProtocolV1_2`: When the new Vault will have `LEVersion` 2, `AssetsMaximum` is not exactly representable on the Vault's base grid ([XLS-65.7.1](./65.7-lending-protocol-v1_2/65.7.1-fixed-precision.md)). (`tecPRECISION_LOSS`)
9. The Vault Owner's balance before the fee does not cover the reserve for the new objects (§3.1.5). (`tecINSUFFICIENT_RESERVE`)

#### 3.2.6 State Changes

1. Create a new `Vault` ledger object.
   - `Scale` is the transaction's `Scale`, or 6 when absent, for an `IOU`; 0 for `XRP` and `MPT`. It is stored only when non-zero.
   - `WithdrawalPolicy` is the transaction's value, or `1` when absent.
   - `Flags` is `lsfVaultPrivate` if `tfVaultPrivate` is set, otherwise 0.
   - `SingleAssetVault`: `VaultKind`, `SubscriptionDate`, and `RedemptionDate` are absent.
   - `LendingProtocolV1_1`: If `VaultKind == ClosedEnded`, store all three fields; otherwise leave all three absent.
   - `SingleAssetVault`: `LEVersion` is absent.
   - `LendingProtocolV1_1`: `LEVersion` is `1` ([XLS-65.4.3](./65.4-lending-protocol-v1_1/65.4.3-cash-basis-vault.md)), or `2` under [XLS-65.7.1](./65.7-lending-protocol-v1_2/65.7.1-fixed-precision.md).
2. Create a new `MPTokenIssuance` ledger object for the vault shares, issued by the _pseudo-account_, and assign its MPTID to `Vault.ShareMPTID`. Its values are as in §3.1.6.2.
   1. If the `DomainID` is provided:
      1. `MPTokenIssuance(Vault.ShareMPTID).DomainID = DomainID` (Set the Permissioned Domain ID).
   2. Create an `MPToken` object for the Vault Owner to hold Vault Shares. If `tfVaultPrivate` is set, the _pseudo-account_ authorizes it (`lsfMPTAuthorized`).
   3. - `SingleAssetVault`: `ReferenceHolding` is absent.
      - `fixCleanup3_2_0`: `ReferenceHolding` is the ID of the _pseudo-account_'s holding created in step 4 or 5 ([XLS-65.2](./65.2-fix-cleanup-3_2_0/README.md)).
3. Create a new `AccountRoot` [_pseudo-account_](../XLS-0064-pseudo-account/README.md) object with `VaultID` set to the new Vault's ID.

4. If `Vault.Asset` is an `IOU`:
   1. Create a `RippleState` object between the _pseudo-account_ `AccountRoot` and `Issuer` `AccountRoot`.

5. If `Vault.Asset` is an `MPT`:
   1. Create `MPToken` object for the _pseudo-account_ for the `Asset.MPTokenIssuance`.

6. Add the `Vault` to the Vault Owner's owner directory and increase the Vault Owner's `OwnerCount` by 3 (§3.1.5).

#### 3.2.7 Invariants

1. A newly created vault has zero `AssetsTotal`, `AssetsAvailable`, `LossUnrealized` and outstanding shares.
2. The share `MPTokenIssuance.Issuer` equals `Vault.Account`, and that account is a _pseudo-account_ whose `VaultID` points to the new vault.
3. Only `VaultCreate` may create a `Vault`; it must create rather than update one.
4. `LendingProtocolV1_1`: A newly created closed-ended Vault has both phase dates and satisfies `180 <= RedemptionDate - SubscriptionDate < 946708560`.
5. `LendingProtocolV1_2`: A newly created Vault with `LEVersion` 2 also has zero `AssetsDeployed` and `YieldUnrealized`.

#### 3.2.8 Example JSON

```json
{
  "TransactionType": "VaultCreate",
  "Account": "rwhaYGnJMexktjhxAKzRwoCcQ2g6hvBDWu",
  "Fee": "10",
  "Sequence": 5,
  "Flags": 0,
  "Asset": {
    "currency": "USD",
    "issuer": "r9cZ5oHbdL4Z9Maj6TdnfAos35nVzYuNds"
  },
  "AssetsMaximum": "1000000",
  "Scale": 6,
  "Data": "5468697320697320617262697472617279206D657461646174612061626F757420746865207661756C742E"
}
```

### 3.3 Transaction: `VaultSet`

The `VaultSet` updates an existing `Vault` ledger object.

#### 3.3.1 Fields

| Field Name        | Required | JSON Type | Internal Type | Default Value | Description                                                                                                                             |
| ----------------- | :------: | :-------: | :-----------: | :-----------: | :-------------------------------------------------------------------------------------------------------------------------------------- |
| `TransactionType` |   Yes    | `string`  |   `UINT16`    |     `66`      | The transaction type (`ttVAULT_SET`).                                                                                                   |
| `VaultID`         |   Yes    | `string`  |   `HASH256`   |     `N/A`     | The ID of the Vault to be modified. Must be included when updating the Vault.                                                           |
| `Data`            |    No    | `string`  |    `BLOB`     |               | Arbitrary Vault metadata, limited to 256 bytes.                                                                                         |
| `AssetsMaximum`   |    No    | `number`  |   `NUMBER`    |               | The maximum asset amount that can be held in a vault. The value cannot be lower than the current `AssetsTotal` unless the value is `0`. |
| `DomainID`        |    No    | `string`  |   `HASH256`   |               | The `PermissionedDomain` object ID associated with the shares of this Vault.                                                            |

#### 3.3.2 Failure Conditions

##### 3.3.2.1 Data Verification

1. The `VaultID` field is zero. (`temMALFORMED`)
2. The `Data` field, if provided, is empty or exceeds 256 bytes. (`temMALFORMED`)
3. The `AssetsMaximum` field, if provided, is negative. (`temMALFORMED`)
4. None of `Data`, `AssetsMaximum`, or `DomainID` are provided (nothing to update). (`temMALFORMED`)

##### 3.3.2.2 Protocol-Level Failures

1. The `Vault` object with the specified `VaultID` does not exist on the ledger. (`tecNO_ENTRY`)
2. The submitting account is not the `Owner` of the vault. (`tecNO_PERMISSION`)
3. - `SingleAssetVault`: The check does not apply.
   - `fixCleanup3_5_0`: The `AssetsMaximum` field is supplied and cannot be represented as an amount of `Vault.Asset` ([XLS-65.6](./65.6-fix-cleanup-3_5_0/README.md)). (`tecPRECISION_LOSS`)
4. The `DomainID` field is provided and the vault does not have `lsfVaultPrivate` set. (`tecNO_PERMISSION`)
5. The `DomainID` field is provided, is non-zero, and the referenced `PermissionedDomain` object does not exist. (`tecOBJECT_NOT_FOUND`)
6. - `SingleAssetVault`: The check does not apply.
   - `LendingProtocolV1_2`: The `AssetsMaximum` field is supplied and is not exactly representable at the Vault's scale. This applies to every Vault, whatever its `LEVersion` ([XLS-65.7.1](./65.7-lending-protocol-v1_2/65.7.1-fixed-precision.md)). (`tecPRECISION_LOSS`)
7. The `AssetsMaximum` field is supplied, is non-zero, and is less than the current `Vault.AssetsTotal`. (`tecLIMIT_EXCEEDED`)
8. The resulting `Vault.AssetsMaximum` is non-zero and the current `Vault.AssetsTotal` exceeds it. (`tecINVARIANT_FAILED`)
   - `SingleAssetVault`: This applies to every `VaultSet`, including one that supplies neither `AssetsMaximum` nor any other change to the cap.
   - `fixCleanup3_4_0`: This applies only when the transaction supplies `AssetsMaximum` or otherwise changes the cap. A `VaultSet` that omits `AssetsMaximum` and leaves the cap unchanged succeeds even when accrued interest has pushed `Vault.AssetsTotal` past the cap.

#### 3.3.3 State Changes

1. Update the mutable fields `Data` and `AssetsMaximum` in the `Vault` ledger object, if provided.
2. If `DomainID` is provided and non-zero: set `MPTokenIssuance(Vault.ShareMPTID).DomainID = DomainID`.
3. If `DomainID` is provided and is zero: remove `DomainID` from `MPTokenIssuance(Vault.ShareMPTID)`.

#### 3.3.4 Invariants

1. `VaultSet` must not change the vault pseudo-account's asset balance.
2. `VaultSet` must not change `Vault.AssetsTotal` or `Vault.AssetsAvailable`.
3. `VaultSet` must not change `MPTokenIssuance(Vault.ShareMPTID).OutstandingAmount`.
4. - `SingleAssetVault`: If `Vault.AssetsMaximum > 0`: `Vault.AssetsTotal <= Vault.AssetsMaximum`.
   - `fixCleanup3_4_0`: This is checked only if the transaction supplies `AssetsMaximum` or otherwise changes the cap.

#### 3.3.5 Example JSON

```json
{
  "TransactionType": "VaultSet",
  "Account": "rwhaYGnJMexktjhxAKzRwoCcQ2g6hvBDWu",
  "Fee": "10",
  "Sequence": 6,
  "VaultID": "2DE64CA41250EF3CB7D2B127D6CEC31F747492CAE2BD1628CA02EA1FFE7475B3",
  "AssetsMaximum": "2000000"
}
```

### 3.4 Transaction: `VaultDelete`

The `VaultDelete` transaction deletes an existing vault object.

#### 3.4.1 Fields

| Field Name        | Required | JSON Type | Internal Type | Default Value |                                                                Description                                                                 |
| ----------------- | :------: | :-------: | :-----------: | :-----------: | :----------------------------------------------------------------------------------------------------------------------------------------: |
| `TransactionType` |   Yes    | `string`  |   `UINT16`    |     `67`      |                                              Transaction type (`ttVAULT_DELETE` in rippled).                                               |
| `VaultID`         |   Yes    | `string`  |   `HASH256`   |     `N/A`     |                                                     The ID of the vault to be deleted.                                                     |
| `MemoData`        |    No    | `string`  |    `BLOB`     |     `N/A`     | A hexadecimal-encoded opaque reason for the deletion. When present, the decoded value must be 1–256 bytes. Requires `LendingProtocolV1_1`. |

#### 3.4.2 Failure Conditions

##### 3.4.2.1 Data Verification

1. The `VaultID` field is zero. (`temMALFORMED`)
2. - `SingleAssetVault`: The `MemoData` field is present. (`temDISABLED`)
   - `LendingProtocolV1_1`: The check does not apply.
3. - `LendingProtocolV1_1`: The `MemoData` field is present and is empty or longer than 256 bytes. (`temMALFORMED`)

##### 3.4.2.2 Protocol-Level Failures

1. The `Vault` object with the `VaultID` does not exist on the ledger. (`tecNO_ENTRY`)
2. The submitting account is not the `Owner` of the vault. (`tecNO_PERMISSION`)
3. `Vault.AssetsAvailable` is greater than zero. (`tecHAS_OBLIGATIONS`)
4. `Vault.AssetsTotal` is greater than zero. (`tecHAS_OBLIGATIONS`)
5. `MPTokenIssuance(Vault.ShareMPTID).OutstandingAmount` is greater than zero (outstanding shares remain). (`tecHAS_OBLIGATIONS`)
6. The _pseudo-account_'s `OwnerDirectory` still contains objects after cleanup (unexpected obligations remain). (`tecHAS_OBLIGATIONS`)

#### 3.4.3 State Changes

1. Delete the `MPToken` or `RippleState` object corresponding to the vault's holding of the asset, if one exists.
2. Delete the vault owner's `MPToken` for vault shares, if one exists.
3. Delete the `MPTokenIssuance` object for the vault shares.
4. Delete the `AccountRoot` object of the _pseudo-account_, and its `DirectoryNode` objects.
5. Remove the `Vault` object from the `Vault.Owner`'s `DirectoryNode` and decrement `OwnerCount` by 2.
6. Delete the `Vault` object.

#### 3.4.4 Invariants

1. Only a `VaultDelete` transaction may delete a `Vault` object; only `VaultDelete` may succeed without an after-state for the vault.
2. `VaultDelete` must also delete the share `MPTokenIssuance`.
3. At deletion: `Vault.AssetsTotal == 0`, `Vault.AssetsAvailable == 0`, and `MPTokenIssuance(Vault.ShareMPTID).OutstandingAmount == 0`.

#### 3.4.5 Example JSON

```json
{
  "TransactionType": "VaultDelete",
  "Account": "rwhaYGnJMexktjhxAKzRwoCcQ2g6hvBDWu",
  "Fee": "10",
  "Sequence": 7,
  "VaultID": "2DE64CA41250EF3CB7D2B127D6CEC31F747492CAE2BD1628CA02EA1FFE7475B3"
}
```

### 3.5 Transaction: `VaultDeposit`

The `VaultDeposit` transaction adds Liqudity in exchange for vault shares.

#### 3.5.1 Fields

| Field Name        | Required |      JSON Type       | Internal Type | Default Value | Description                                            |
| ----------------- | :------: | :------------------: | :-----------: | :-----------: | :----------------------------------------------------- |
| `TransactionType` |   Yes    |       `string`       |   `UINT16`    |     `68`      | Transaction type (`ttVAULT_DEPOSIT`).                  |
| `VaultID`         |   Yes    |       `string`       |   `HASH256`   |     `N/A`     | The ID of the vault to which the assets are deposited. |
| `Amount`          |   Yes    | `string` or `object` |  `STAmount`   |     `N/A`     | Asset amount to deposit.                               |

#### 3.5.2 Failure Conditions

##### 3.5.2.1 Data Verification

1. The `VaultID` field is zero. (`temMALFORMED`)
2. The `Amount` field is zero or negative. (`temBAD_AMOUNT`)

##### 3.5.2.2 Protocol-Level Failures

> The order below reflects the evaluation order in `VaultDeposit.cpp` (preclaim, then doApply).

1. The `Vault` object with the `VaultID` does not exist on the ledger. (`tecNO_ENTRY`)
2. - `SingleAssetVault`: The check does not apply.
   - `LendingProtocolV1_1`: The Vault is closed-ended and the parent ledger close time is greater than `Vault.SubscriptionDate`. (`tecEXPIRED`)
3. The `Amount` asset does not match `Vault.Asset`. (`tecWRONG_ASSET`)

4. If `Vault.Asset` is an `MPT`:
   1. The `lsfMPTCanTransfer` flag is not set in the `MPTokenIssuance` object (the asset is not transferable). (`tecNO_AUTH`)

5. Freeze checks:
   - `SingleAssetVault`:
     1. The asset is frozen for the depositor, including a global freeze or lock. (`tecFROZEN` for an `IOU`, `tecLOCKED` for an `MPT`)
     2. The vault shares are locked for the depositor. (`tecLOCKED`)
   - `fixCleanup3_3_0`: The asset is globally frozen, the depositor is individually frozen unless it is the issuer, or the _pseudo-account_ is individually frozen. The shares are not checked ([XLS-65.3](./65.3-fix-cleanup-3_3_0/README.md)). (`tecFROZEN` / `tecLOCKED`)

6. If the vault has `lsfVaultPrivate` set and the depositor is not the vault owner:
   1. No `PermissionedDomain` is configured on `MPTokenIssuance(Vault.ShareMPTID)`. (`tecNO_AUTH`)
   2. The depositor is not a valid member of the permissioned domain. (`tecNO_AUTH`) An expired credential is not a failure here, because the transaction deletes it.

7. The depositor does not have a required authorized holding for the vault asset (e.g., missing `MPToken` for a restricted `MPT`). (`tecNO_AUTH`)
8. - `SingleAssetVault`: The check does not apply.
   - `fixCleanup3_2_0`: The `Amount`, rounded toward zero at the posterior `Vault.AssetsTotal` scale, is zero ([XLS-65.2](./65.2-fix-cleanup-3_2_0/README.md)). (`tecPRECISION_LOSS`)
9. The depositor has insufficient balance to cover the deposit (the rounded amount under `fixCleanup3_2_0`). (`tecINSUFFICIENT_FUNDS`)
10. - `SingleAssetVault`: The check does not apply.
    - `fixCleanup3_2_0`: `Vault.Asset` is an `IOU`, the depositor is not its issuer, and the `Amount` rounds to zero at the scale of the depositor's balance. (`tecPRECISION_LOSS`)
11. The computed number of shares for the deposit is zero. (`tecPRECISION_LOSS`)
12. `fixCleanup3_4_0`: The deposit rounds down to zero at the posterior `Vault.AssetsTotal` scale, i.e. a non-zero $\Delta_{asset}$ that would credit the vault nothing at that scale, as described in [XLS-65.5](./65.5-fix-cleanup-3_4_0/README.md). (`tecPRECISION_LOSS`)
13. `fixCleanup3_4_0`: `Vault.Asset` is an `IOU` and debiting $\Delta_{asset}$ would leave the depositor's stored balance unchanged. (`tecPRECISION_LOSS`)
14. Arithmetic overflow during share calculation. (`tecPATH_DRY`)
15. `LendingProtocolV1_2`: On a Vault with `LEVersion` 2, the deposit would leave the Vault coarsened or outside its Open zone ([XLS-65.7.1](./65.7-lending-protocol-v1_2/65.7.1-fixed-precision.md)). (`tecLIMIT_EXCEEDED`)
16. `Vault.AssetsMaximum` is non-zero and adding the deposited amount to `Vault.AssetsTotal` would exceed it. (`tecLIMIT_EXCEEDED`)

#### 3.5.3 State Changes

1. If no share `MPToken` object exists for the depositor, create one. For private vaults, the `MPToken` is created only after domain authorization is verified.
2. Increase the `MPTAmount` field of the depositor's share `MPToken` by $\Delta_{share}$.
3. Increase the `OutstandingAmount` field of the share `MPTokenIssuance` by $\Delta_{share}$.
4. Increase `Vault.AssetsTotal` and `Vault.AssetsAvailable` by $\Delta_{asset}$.

5. If `Vault.Asset` is `XRP`:
   1. Increase the `Balance` field of the _pseudo-account_ `AccountRoot` by $\Delta_{asset}$.
   2. Decrease the `Balance` field of the depositor `AccountRoot` by $\Delta_{asset}$.

6. If `Vault.Asset` is an `IOU`:
   1. Increase the `RippleState` balance between the _pseudo-account_ `AccountRoot` and the `Issuer` `AccountRoot` by $\Delta_{asset}$.
   2. Decrease the `RippleState` balance between the depositor `AccountRoot` and the `Issuer` `AccountRoot` by $\Delta_{asset}$.

7. If `Vault.Asset` is an `MPT`:
   1. Increase the `MPToken.MPTAmount` of the _pseudo-account_ `MPToken` for `Vault.Asset` by $\Delta_{asset}$.
   2. Decrease the `MPToken.MPTAmount` of the depositor `MPToken` for `Vault.Asset` by $\Delta_{asset}$.

> **Note:** $\Delta_{asset}$ is the actual asset amount transferred, which may be slightly less than the requested `Amount` due to scale rounding for IOU assets.
>
> - `SingleAssetVault`: The vault accounting increases and both asset-balance moves use that same $\Delta_{asset}$. Where the depositor is the issuer of a non-`XRP` `Vault.Asset` it holds no balance of the asset — the transfer creates the asset at the issuer instead — so only the vault accounting fields and the vault's asset balance move. This is the issuer exception of invariant 2 below.
> - `fixCleanup3_4_0`: For an `IOU`, the persisted vault accounting deltas and the persisted asset-balance deltas may differ from each other by at most one unit at the comparison scale in [XLS-65.5](./65.5-fix-cleanup-3_4_0/README.md). For `XRP` and `MPT` they remain equal.

#### 3.5.4 Invariants

1. The vault pseudo-account's asset balance must increase by a positive amount not exceeding the transaction `Amount`.
2. - `SingleAssetVault`: Unless the depositor is the asset issuer, the depositor's asset balance must decrease by the same amount as the vault increases.
   - `fixCleanup3_4_0`: Unless the depositor is the asset issuer, for an `IOU` the comparison admits one unit at the comparison scale. For `XRP` and `MPT` it remains exact. The issuer exemption is unchanged.
3. The depositor's share `MPToken.MPTAmount` must increase by a positive amount.
4. The increase in `MPTokenIssuance(Vault.ShareMPTID).OutstandingAmount` must equal the increase in the depositor's share balance.
5. - `SingleAssetVault`: `Vault.AssetsTotal` and `Vault.AssetsAvailable` must each increase by the vault's asset balance increase.
   - `fixCleanup3_4_0`: For an `IOU`, each comparison admits one unit at the comparison scale. For `XRP` and `MPT` it remains exact.
6. - `SingleAssetVault`: If `Vault.AssetsMaximum` is non-zero, `Vault.AssetsTotal <= Vault.AssetsMaximum` after the deposit.
   - `fixCleanup3_4_0`: Unchanged. The cap remains a deposit invariant; the amendment only narrows `VaultSet` cap enforcement.
7. `LendingProtocolV1_1`: A deposit succeeds only when the Vault phase is `Subscription` or `NoPhase`.

#### 3.5.5 Example JSON

```json
{
  "TransactionType": "VaultDeposit",
  "Account": "rf1BiGeXwwQoi8Z2ueFYTEXSwuJYfV2Jpn",
  "Fee": "10",
  "Sequence": 12,
  "VaultID": "2DE64CA41250EF3CB7D2B127D6CEC31F747492CAE2BD1628CA02EA1FFE7475B3",
  "Amount": {
    "currency": "USD",
    "issuer": "r9cZ5oHbdL4Z9Maj6TdnfAos35nVzYuNds",
    "value": "100"
  }
}
```

### 3.6 Transaction: `VaultWithdraw`

The `VaultWithdraw` transaction withdraws assets in exchange for the vault's shares.

#### 3.6.1 Fields

| Field Name        | Required | JSON Type | Internal Type | Default Value | Description                                                                                                                                                 |
| ----------------- | :------: | :-------: | :-----------: | :-----------: | :---------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `TransactionType` |   Yes    | `string`  |   `UINT16`    |     `69`      | Transaction type (`ttVAULT_WITHDRAW`).                                                                                                                      |
| `VaultID`         |   Yes    | `string`  |   `HASH256`   |     `N/A`     | The ID of the vault from which assets are withdrawn.                                                                                                        |
| `Amount`          |   Yes    | `number`  |  `STAmount`   |       0       | The exact amount of Vault asset to withdraw.                                                                                                                |
| `Destination`     |    No    | `string`  |  `AccountID`  |     Empty     | An account to receive the assets. It must be able to receive the asset.                                                                                     |
| `DestinationTag`  |    No    | `number`  |   `UINT32`    |     Empty     | Arbitrary tag identifying the reason for the withdrawal to the destination.                                                                                 |
| `CredentialIDs`   |    No    |  `array`  |  `VECTOR256`  |     Empty     | `fixCleanup3_4_0`: credentials of the submitter used where the destination requires deposit authorization ([XLS-65.5](./65.5-fix-cleanup-3_4_0/README.md)). |

- If `Amount` is the Vaults asset, calculate the share cost using the [**Withdraw formula**](#31723-withdraw).
- If `Amount` is the Vaults share, calculate the assets amount using the [**Redeem formula**](#31722-redeem).

In sections below assume the following variables:

- $\Gamma_{share}$ - the total number of shares issued by the vault.
- $\Gamma_{asset}$:
  - `SingleAssetVault`: `Vault.AssetsTotal - Vault.LossUnrealized`.
  - `fixCleanup3_2_0`: if the withdrawer is the sole outstanding shareholder, the `LossUnrealized` deduction is waived and $\Gamma_{asset}$ = `Vault.AssetsTotal`, since the sole holder is entitled to the vault's full realized and unrealized value ([XLS-65.2](./65.2-fix-cleanup-3_2_0/README.md)).

- $\Delta_{asset}$ - the change in the total amount of assets after a deposit, withdrawal, or redemption.
- $\Delta_{share}$ - che change in the total amount of shares after a deposit, withdrawal, or redemption.

#### 3.6.2 Failure Conditions

##### 3.6.2.1 Data Verification

1. The `VaultID` field is zero. (`temMALFORMED`)
2. The `Amount` field is zero or negative. (`temBAD_AMOUNT`)
3. The `Destination` field, if provided, is zero. (`temMALFORMED`)
4. - `SingleAssetVault`: `CredentialIDs` is present. (`temDISABLED`)
   - `fixCleanup3_4_0`: `CredentialIDs` is present and the `Credentials` amendment is not enabled (`temDISABLED`), or `CredentialIDs` is empty, too long, or contains a zero or duplicate ID (`temMALFORMED`).

##### 3.6.2.2 Protocol-Level Failures

"Destination" below is the `Destination` field if provided, otherwise the submitting `Account`.

1. The `Vault` object with the `VaultID` does not exist on the ledger. (`tecNO_ENTRY`)
2. - `SingleAssetVault`: The check does not apply.
   - `LendingProtocolV1_1`: The Vault is closed-ended and `SubscriptionDate < parent ledger close time < RedemptionDate`. (`tecTOO_SOON`)
3. The `Amount` asset is neither `Vault.Asset` nor the vault share (`Vault.ShareMPTID`). (`tecWRONG_ASSET`)
4. The asset cannot be transferred from the _pseudo-account_ to the destination:
   - For an `MPT`: the `MPTokenIssuance` does not exist (`tecOBJECT_NOT_FOUND`), or `lsfMPTCanTransfer` is not set (`tecNO_AUTH`).
     - `SingleAssetVault`: `lsfMPTCanTransfer` is checked.
     - `fixCleanup3_2_0`: `lsfMPTCanTransfer` is not checked ([XLS-65.2](./65.2-fix-cleanup-3_2_0/README.md)).
   - For an `IOU`: rippling is disabled on both the _pseudo-account_'s and the destination's trust line to the issuer, or the line is absent and the issuer lacks `lsfDefaultRipple`. (`terNO_RIPPLE`)
5. `fixCleanup3_4_0`: `CredentialIDs` is present and a listed credential does not exist, does not have the submitter as its subject, or has not been accepted ([XLS-65.5](./65.5-fix-cleanup-3_4_0/README.md)). (`tecBAD_CREDENTIALS`)
6. `fixCleanup3_4_0`: The destination is a _pseudo-account_. (`tecPSEUDO_ACCOUNT`)
7. The `Destination` account, if specified, does not exist on the ledger. (`tecNO_DST`)
8. The `Destination` account, if specified, requires a destination tag but none is provided. (`tecDST_TAG_NEEDED`)
9. The `Destination` account, if specified, requires deposit authorization and the sender is not authorized. (`tecNO_PERMISSION`)
10. `Vault.Asset` is an `IOU`, the destination is neither the submitter nor the issuer, and the amount exceeds the room left under the destination's trust-line limit to the issuer. A destination with no trust line has no room. (`tecNO_LINE`) For `XRP` and `MPT` this check always passes.
    - `SingleAssetVault`: The check uses the transaction's `Amount`. When `Amount` is in shares it is an `MPT` amount, so the check always passes.
    - `fixCleanup3_1_3`: When `Amount` is in shares, the check uses the asset amount the shares convert to ([XLS-65.1](./65.1-fix-cleanup-3_1_3/README.md)).
11. The destination account does not have a required authorized holding for the vault asset. (`tecNO_AUTH`)
12. `fixCleanup3_4_0`: The destination is the submitter, it has no holding of the asset, and a holding cannot be added. (`terNO_ACCOUNT`, `terNO_RIPPLE`, `tecOBJECT_NOT_FOUND` or `tecNO_AUTH`)
13. `fixCleanup3_4_0`: The Vault has `lsfVaultPrivate` set, the destination is neither the submitter nor the asset issuer, and the submitter or the destination is not a member of the permissioned domain. (`tecNO_AUTH`, or the credential failure code)
14. Freeze checks:
    - `SingleAssetVault`: The asset is frozen for the destination, including a global freeze or lock (`tecFROZEN` / `tecLOCKED`). The vault shares are locked for the submitting account (`tecLOCKED`).
    - `fixCleanup3_3_0`: Unless the destination is the asset issuer: the asset is globally frozen; the _pseudo-account_ is individually frozen; the submitter is individually frozen and the destination is not the submitter; or the destination is deep frozen. The shares are not checked ([XLS-65.3](./65.3-fix-cleanup-3_3_0/README.md)). (`tecFROZEN` / `tecLOCKED`)
15. The computed share amount for the withdrawal is zero. (`tecPRECISION_LOSS`)
16. `LendingProtocolV1_2`: On a Vault with `LEVersion` 2, the withdrawal redeems every outstanding share while `Vault.AssetsDeployed` is non-zero ([XLS-65.7.1](./65.7-lending-protocol-v1_2/65.7.1-fixed-precision.md)). (`tecHAS_OBLIGATIONS`)
17. `fixCleanup3_4_0`: The withdrawal would move shares while moving no assets: a non-zero $\Delta_{asset}$ that leaves the stored `Vault.AssetsTotal` unchanged at its precision, or that rounds down to zero at the posterior `Vault.AssetsTotal` scale, as described in [XLS-65.5](./65.5-fix-cleanup-3_4_0/README.md). A fixed-share withdrawal whose pre-transaction `Vault.AssetsTotal == Vault.LossUnrealized` is exempt and may redeem shares for zero assets. (`tecPRECISION_LOSS`)
18. There is insufficient liquidity to fill the request:
    1. The submitter holds fewer shares than $\Delta_{share}$. (`tecINSUFFICIENT_FUNDS`)
    2. `Vault.AssetsAvailable` is less than the computed $\Delta_{asset}$. (`tecINSUFFICIENT_FUNDS`)
       - `fixCleanup3_4_0`: Unless the withdrawal redeems every outstanding share, this is also checked against $\Delta_{asset}$ before it is rounded at the posterior scale, so a withdrawal that is both too large and too small to represent fails with `tecINSUFFICIENT_FUNDS` rather than the rounding failure of item 17 ([XLS-65.5](./65.5-fix-cleanup-3_4_0/README.md)).
19. `fixCleanup3_5_0`: A transfer fee applies and reduces a non-zero $\Delta_{asset}$ to zero for the destination ([XLS-65.6](./65.6-fix-cleanup-3_5_0/README.md)). (`tecPRECISION_LOSS`)
20. Arithmetic overflow during share/asset calculation. (`tecPATH_DRY`)
21. `fixCleanup3_4_0`: The destination is not the submitter, `CredentialIDs` is present, and a listed credential has expired. The expired credentials are deleted, and the deletions are kept even though the transaction fails. (`tecEXPIRED`) This is checked when the assets are transferred, after the other checks ([XLS-65.5](./65.5-fix-cleanup-3_4_0/README.md)).

#### 3.6.3 State Changes

1. Decrease the `MPToken.MPTAmount` of the submitter's share `MPToken` by $\Delta_{share}$.
2. Decrease the `OutstandingAmount` of the share `MPTokenIssuance` by $\Delta_{share}$.
3. If the submitter is not the vault owner and their share `MPToken.MPTAmount` reaches zero, delete the `MPToken` object.
4. Decrease `Vault.AssetsTotal` and `Vault.AssetsAvailable` by $\Delta_{asset}$.
   - `SingleAssetVault`: This applies to every withdrawal.
   - `fixCleanup3_2_0`: When the withdrawal redeems every outstanding share, $\Delta_{asset}$ is `Vault.AssetsAvailable`, and `Vault.AssetsTotal` and `Vault.AssetsAvailable` are set to zero ([XLS-65.2](./65.2-fix-cleanup-3_2_0/README.md)).
   - `LendingProtocolV1_2`: A Vault with `LEVersion` 2 is not set to zero. The full-redemption payout of `Vault.AssetsAvailable` is applied through the balance update of [XLS-65.7.1](./65.7-lending-protocol-v1_2/65.7.1-fixed-precision.md), which then derives `Vault.AssetsTotal`.

5. If `Vault.Asset` is `XRP`:
   1. Decrease the `Balance` field of the _pseudo-account_ `AccountRoot` by $\Delta_{asset}$.
   2. Increase the `Balance` field of the destination `AccountRoot` by $\Delta_{asset}$.

6. If `Vault.Asset` is an `IOU`:
   1. If the destination does not have a `RippleState` object for the vault asset, create one.
   2. Decrease the `RippleState` balance between the _pseudo-account_ `AccountRoot` and the `Issuer` `AccountRoot` by $\Delta_{asset}$.
   3. Increase the `RippleState` balance between the destination `AccountRoot` and the `Issuer` `AccountRoot` by $\Delta_{asset}$.

7. If `Vault.Asset` is an `MPT`:
   1. If the destination does not have an `MPToken` object for the vault asset, create one.
   2. Decrease the `MPToken.MPTAmount` of the _pseudo-account_ `MPToken` for `Vault.Asset` by $\Delta_{asset}$.
   3. Increase the `MPToken.MPTAmount` of the destination `MPToken` for `Vault.Asset` by $\Delta_{asset}$.

> **Note:** "destination" is the `Destination` field if provided, otherwise the submitting `Account`.
>
> - `SingleAssetVault`: The vault accounting decreases and both asset-balance moves use that same $\Delta_{asset}$. Where the destination is the issuer of a non-`XRP` `Vault.Asset` it holds no balance of the asset — the transfer destroys the asset at the issuer instead — so only the vault accounting fields and the vault's asset balance move. This is the issuer exception of invariant 2 below.
> - `fixCleanup3_2_0`: For an `IOU`, an unrepresentable sub-ULP remainder may remain between vault outflow and destination inflow ([XLS-65.2](./65.2-fix-cleanup-3_2_0/README.md)).
> - `fixCleanup3_4_0`: For an `IOU`, the persisted vault accounting deltas and the persisted asset-balance deltas may differ from each other by at most one unit at the comparison scale in [XLS-65.5](./65.5-fix-cleanup-3_4_0/README.md). For `XRP` and `MPT` they remain equal. That one unit and the sub-ULP remainder above are alternative tolerances, not cumulative: the vault-to-destination comparison is satisfied by either.
> - `fixCleanup3_5_0`: When a transfer fee applies, the destination receives $\Delta_{asset}$ less the fee ([XLS-65.6](./65.6-fix-cleanup-3_5_0/README.md)).

#### 3.6.4 Invariants

1.  - `SingleAssetVault`: The vault pseudo-account's asset balance must decrease by a positive amount.
    - `fixCleanup3_4_0`: A fixed-share withdrawal may instead move zero assets when the pre-transaction `Vault.AssetsTotal == Vault.LossUnrealized`.
2.  Unless the destination is the asset issuer, the destination's asset balance must increase. The zero-asset exception in invariant 1 may leave the destination balance unchanged.
    - `fixCleanup3_2_0`: For an `IOU`, the destination's rounded increase may be zero when its trust line sits at a coarser scale ([XLS-65.2](./65.2-fix-cleanup-3_2_0/README.md)).
3.  - `SingleAssetVault`: The vault outflow and destination inflow must match in magnitude.
    - `fixCleanup3_2_0`: For an `IOU`, an unrepresentable sub-ULP remainder at the destination scale is also accepted.
    - `fixCleanup3_4_0`: For an `IOU`, the comparison is also satisfied when the two magnitudes agree within one unit at the comparison scale. That tolerance and the sub-ULP remainder are alternatives, not cumulative. For `XRP` and `MPT` it remains exact.
    - `fixCleanup3_5_0`: When a transfer fee applies, the expected inflow is the outflow less the fee, and the sub-ULP remainder is not accepted ([XLS-65.6](./65.6-fix-cleanup-3_5_0/README.md)).
4.  The submitter's share `MPToken.MPTAmount` must decrease by a positive amount.
5.  The decrease in `MPTokenIssuance(Vault.ShareMPTID).OutstandingAmount` must equal the decrease in the submitter's share balance.
6.  - `SingleAssetVault`: `Vault.AssetsTotal` and `Vault.AssetsAvailable` must each decrease by the vault's asset balance decrease.
    - `fixCleanup3_4_0`: For an `IOU`, each comparison admits one unit at the comparison scale. For `XRP` and `MPT` it remains exact.
7.  `LendingProtocolV1_1`: A withdrawal does not succeed while the Vault phase is `Investment`.
8.  When `Destination` names an account other than the submitter, the submitter's asset balance must not change, apart from the transaction fee.

#### 3.6.5 Example JSON

```json
{
  "TransactionType": "VaultWithdraw",
  "Account": "rf1BiGeXwwQoi8Z2ueFYTEXSwuJYfV2Jpn",
  "Fee": "10",
  "Sequence": 13,
  "VaultID": "2DE64CA41250EF3CB7D2B127D6CEC31F747492CAE2BD1628CA02EA1FFE7475B3",
  "Amount": {
    "currency": "USD",
    "issuer": "r9cZ5oHbdL4Z9Maj6TdnfAos35nVzYuNds",
    "value": "50"
  }
}
```

### 3.7 Transaction: `VaultClawback`

The `VaultClawback` transaction performs a Clawback from the Vault, exchanging the shares of an account. It has two uses:

- **Asset clawback.** The issuer of `Vault.Asset` claws back the asset from a `Holder`'s position. Conceptually, the transaction performs `VaultWithdraw` on behalf of the `Holder`, sending the funds to the issuer. If `Vault.AssetsAvailable` cannot cover the requested amount, the transaction performs a partial Clawback, up to `Vault.AssetsAvailable`.
- **Share burn.** The Vault Owner burns all of a `Holder`'s shares when the Vault has outstanding shares but no assets.

The transfer fee is not charged.

#### 3.7.1 Fields

| Field Name        | Required |      JSON Type       | Internal Type | Default Value | Description                                                                                                                                                                                                                                                                |
| ----------------- | :------: | :------------------: | :-----------: | :-----------: | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `TransactionType` |   Yes    |       `string`       |   `UINT16`    |     `70`      | Transaction type (`ttVAULT_CLAWBACK`).                                                                                                                                                                                                                                     |
| `VaultID`         |   Yes    |       `string`       |   `HASH256`   |     `N/A`     | The ID of the vault from which assets are withdrawn.                                                                                                                                                                                                                       |
| `Holder`          |   Yes    |       `string`       |  `AccountID`  |     `N/A`     | The account ID from which to clawback the assets.                                                                                                                                                                                                                          |
| `Amount`          |    No    | `string` or `object` |  `STAmount`   |       0       | The amount to claw back, in `Vault.Asset`, or in vault shares for a share burn. A zero amount claws back all of the `Holder`'s shares. When absent, it is a zero amount of vault shares if the submitter is the Vault Owner, and a zero amount of `Vault.Asset` otherwise. |

#### 3.7.2 Failure Conditions

##### 3.7.2.1 Data Verification

1. The `VaultID` field is zero. (`temMALFORMED`)
2. The `Amount` field, if provided, is negative. (`temBAD_AMOUNT`)
3. The `Amount` field, if provided, is `XRP`. (`temMALFORMED`)

##### 3.7.2.2 Protocol-Level Failures

1. The `Vault` object with the `VaultID` does not exist on the ledger. (`tecNO_ENTRY`)
2. - `SingleAssetVault`: The check does not apply.
   - `fixCleanup3_5_0`: The `Holder` account does not exist ([XLS-65.6](./65.6-fix-cleanup-3_5_0/README.md)). (`terNO_ACCOUNT`)
3. - `SingleAssetVault`: The check does not apply.
   - `fixCleanup3_4_0`: The `Holder` is a _pseudo-account_ ([XLS-65.5](./65.5-fix-cleanup-3_4_0/README.md)). (`tecPSEUDO_ACCOUNT`)
4. `Amount` is absent, `Vault.Asset` is not `XRP`, and the asset issuer is the Vault Owner, so the intended use is ambiguous. (`tecWRONG_ASSET`)
5. If `Amount` is in vault shares:
   1. The submitter is not the Vault Owner. (`tecNO_PERMISSION`)
   2. The Vault has no outstanding shares, or `Vault.AssetsTotal` or `Vault.AssetsAvailable` is non-zero. (`tecNO_PERMISSION`)
   3. `Amount` is non-zero and is not equal to the `Holder`'s share balance. (`tecLIMIT_EXCEEDED`)
6. If `Amount` is in `Vault.Asset`:
   1. `Vault.Asset` is `XRP`. (`tecNO_PERMISSION`)
   2. The submitter is not the asset issuer. (`tecNO_PERMISSION`)
   3. The `Holder` is the submitter. (`tecNO_PERMISSION`)
   4. If `Vault.Asset` is an `MPT`: the `MPTokenIssuance` does not exist (`tecOBJECT_NOT_FOUND`), or `lsfMPTCanClawback` is not set (`tecNO_PERMISSION`).
   5. If `Vault.Asset` is an `IOU`: the issuer does not have `lsfAllowTrustLineClawback` set, or has `lsfNoFreeze` set. (`tecNO_PERMISSION`)
7. `Amount` is in neither `Vault.Asset` nor vault shares. (`tecWRONG_ASSET`)
8. `LendingProtocolV1_2`: On a Vault with `LEVersion` 2, the clawback would burn every outstanding share while `Vault.AssetsDeployed` is non-zero ([XLS-65.7.1](./65.7-lending-protocol-v1_2/65.7.1-fixed-precision.md)). (`tecHAS_OBLIGATIONS`)
9. `fixCleanup3_4_0`: The clawback would burn shares while moving no assets: a non-zero $\Delta_{asset}$ that leaves the stored `Vault.AssetsTotal` unchanged at its precision, or that rounds down to zero at the posterior `Vault.AssetsTotal` scale, as described in [XLS-65.5](./65.5-fix-cleanup-3_4_0/README.md). A clawback against an already-empty vault is unaffected, because its $\Delta_{asset}$ is zero to begin with. (`tecPRECISION_LOSS`)
10. $\Delta_{share}$ is zero: the `Holder` holds no shares, or the clawback rounds to zero shares. (`tecPRECISION_LOSS`)
11. Arithmetic overflow during share/asset calculation. (`tecPATH_DRY`)

#### 3.7.3 State Changes

$\Delta_{share}$ and $\Delta_{asset}$ are derived as follows:

- **Share burn.** $\Delta_{share}$ is the `Holder`'s share balance and $\Delta_{asset}$ is zero.
- **Asset clawback.**
  1. If `Amount` is zero, $\Delta_{share}$ is the `Holder`'s share balance and $\Delta_{asset}$ is its value under the [Redeem formula](#31722-redeem). If `Amount` is non-zero, $\Delta_{share}$ is `Amount` converted with the [Withdraw formula](#31723-withdraw), and $\Delta_{asset}$ is the redeem value of $\Delta_{share}$.
  2. If $\Delta_{asset}$ exceeds `Vault.AssetsAvailable`, $\Delta_{asset}$ becomes `Vault.AssetsAvailable`. $\Delta_{share}$ is then recomputed from it with the withdraw formula, truncated to whole shares, and $\Delta_{asset}$ is recomputed from that $\Delta_{share}$.
     - `SingleAssetVault`: This step does not apply to a zero `Amount`.
     - `fixCleanup3_1_3`: This step applies to a zero `Amount` too ([XLS-65.1](./65.1-fix-cleanup-3_1_3/README.md)).
  3. - `SingleAssetVault`: Shares from a non-zero `Amount` are rounded to the nearest whole share, and $\Gamma_{asset}$ is `Vault.AssetsTotal - Vault.LossUnrealized`.
     - `fixCleanup3_4_0`: Shares are truncated, and $\Gamma_{asset}$ is `Vault.AssetsTotal` when the `Holder` is the sole shareholder. $\Delta_{asset}$ is rounded down at the posterior scale ([XLS-65.5](./65.5-fix-cleanup-3_4_0/README.md)).

Then:

1. Decrease `Vault.AssetsTotal` and `Vault.AssetsAvailable` by $\Delta_{asset}$.

2. Update the `MPToken` object for the `Vault.ShareMPTID` of the `Holder` `AccountRoot`:
   1. Decrease the `MPToken.MPTAmount` by $\Delta_{share}$.
   2. If `MPToken.MPTAmount == 0` and the `Holder` is not the Vault Owner, delete the object.

3. Update the `MPTokenIssuance` object for the `Vault.ShareMPTID`:
   1. Decrease the `OutstandingAmount` field of the share `MPTokenIssuance` object by $\Delta_{share}$.

4. If $\Delta_{asset}$ is greater than zero, transfer it from the _pseudo-account_ to the submitter (the asset issuer):
   1. If the `Vault.Asset` is an `IOU`, decrease the `RippleState` balance between the _pseudo-account_ `AccountRoot` and the `Issuer` `AccountRoot` by $\Delta_{asset}$.
   2. If the `Vault.Asset` is an `MPT`, decrease the `MPToken.MPTAmount` of the _pseudo-account_ `MPToken` for `Vault.Asset` by $\Delta_{asset}$.

> - `SingleAssetVault`: The vault accounting decreases and the vault asset-balance decrease use that same amount.
> - `fixCleanup3_4_0`: For an `IOU`, the persisted vault accounting deltas and the persisted vault asset-balance delta may differ from each other by at most one unit at the comparison scale in [XLS-65.5](./65.5-fix-cleanup-3_4_0/README.md). For `MPT` they remain equal.

#### 3.7.4 Invariants

1. The vault pseudo-account's asset balance must decrease, unless the Vault was already empty.
2. - `SingleAssetVault`: `Vault.AssetsTotal` and `Vault.AssetsAvailable` must each decrease by the vault's asset balance decrease.
   - `fixCleanup3_4_0`: For an `IOU`, each comparison admits one unit at the comparison scale. For `XRP` and `MPT` it remains exact.
3. The holder's share `MPToken.MPTAmount` must decrease by a positive amount.
4. The decrease in `MPTokenIssuance(Vault.ShareMPTID).OutstandingAmount` must equal the decrease in the holder's share balance.
5. The transaction must be submitted by the asset issuer, or by the Vault Owner when the Vault had outstanding shares and zero `AssetsTotal` and `AssetsAvailable` before the transaction.

#### 3.7.5 Example JSON

```json
{
  "TransactionType": "VaultClawback",
  "Account": "r9cZ5oHbdL4Z9Maj6TdnfAos35nVzYuNds",
  "Fee": "10",
  "Sequence": 21,
  "VaultID": "2DE64CA41250EF3CB7D2B127D6CEC31F747492CAE2BD1628CA02EA1FFE7475B3",
  "Holder": "rf1BiGeXwwQoi8Z2ueFYTEXSwuJYfV2Jpn",
  "Amount": {
    "currency": "USD",
    "issuer": "r9cZ5oHbdL4Z9Maj6TdnfAos35nVzYuNds",
    "value": "10"
  }
}
```

### 3.8 Transaction: `Payment`

The Single Asset Vault does not introduce new `Payment` transaction fields. However, it adds additional failure conditions and state changes when transferring Vault shares.

#### 3.8.1 Fields

The Single Asset Vault does not introduce or modify any `Payment` transaction fields. Refer to the existing [Payment transaction fields](https://xrpl.org/docs/references/protocol/transactions/types/payment).

#### 3.8.2 Failure Conditions

##### 3.8.2.1 Data Verification

_None._

##### 3.8.2.2 Protocol-Level Failures

1. If `Payment.Amount` is a `Vault` share AND:
   1. The `Vault` `lsfVaultPrivate` flag is set and the `Payment.Destination` account is not a member of the permissioned domain specified at `MPTokenIssuance(Vault.ShareMPTID).DomainID`.
   2. The `Vault` `tfVaultShareNonTransferable` flag is set.

   3. If the `Vault.Asset` is `MPT`:
      1. `MPTokenIssuance.lsfMPTCanTransfer` is not set (the asset is not transferable).
      2. `MPTokenIssuance.lsfMPTLocked` flag is set (the asset is globally locked).
      3. `MPToken(MPTokenIssuanceID, AccountID).lsfMPTLocked` flag is set (the asset is locked for the payer).
      4. `MPToken(MPTokenIssuanceID, AccountID).lsfMPTLocked` flag is set (the asset is locked for the `pseudo-account`).
      5. `MPToken(MPTokenIssuanceID, Destination).lsfMPTLocked` flag is set (the asset is locked for the destination account).

   4. If the `Vault.Asset` is an `IOU`:
      1. The `lsfGlobalFreeze` flag is set on the issuing account (the asset is frozen).
      2. The `lsfHighFreeze` or `lsfLowFreeze` flag is set on the `RippleState` object between the Asset `Issuer` and the payer account.
      3. The `lsfHighFreeze` or `lsfLowFreeze` flag is set on the `RippleState` object between the Asset `Issuer` and the destination account.
      4. The `lsfHighFreeze` or `lsfLowFreeze` flag is set on the `RippleState` object between the Asset `Issuer` and the `pseudo-account`.

#### 3.8.3 State Changes

1. If `MPToken`object for shares does not exist for the destination account, create one.

#### 3.8.4 Example JSON

A payment of vault shares:

```json
{
  "TransactionType": "Payment",
  "Account": "rf1BiGeXwwQoi8Z2ueFYTEXSwuJYfV2Jpn",
  "Destination": "rNGHoQwNG753zyfDrib4qDvvswbrtmV8Es",
  "Fee": "10",
  "Sequence": 14,
  "Amount": {
    "mpt_issuance_id": "00000001C752C42A1EBD6BF2403134F7CFD2F1D835AFD26E",
    "value": "1000000"
  }
}
```

### 3.9 RPC: `vault_info`

This RPC retrieves the Vault ledger entry and the IDs associated with it.

#### 3.9.1 Request Fields

The Vault is identified either by `vault_id`, or by `owner` and `seq` together. Exactly one of the two forms must be used. The standard `ledger_hash` and `ledger_index` fields select the ledger.

| Field Name     |  Required   |     JSON Type      | Description                                                                               |
| -------------- | :---------: | :----------------: | ----------------------------------------------------------------------------------------- |
| `vault_id`     | Conditional |      `string`      | The object ID of the Vault, as a hex string.                                              |
| `owner`        | Conditional |      `string`      | The Vault Owner's address. Used together with `seq`.                                      |
| `seq`          | Conditional |      `number`      | The `Sequence` (or `TicketSequence`) of the `VaultCreate` transaction. Used with `owner`. |
| `ledger_hash`  |     No      |      `string`      | The hash of the ledger to use.                                                            |
| `ledger_index` |     No      | `string or number` | The ledger index of the ledger to use, or a shortcut such as `validated`.                 |

#### 3.9.2 Response Fields

| Field Name                       | Always Present? | JSON Type | Description                                                                                                                                                              |
| -------------------------------- | :-------------: | :-------: | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `vault`                          |       Yes       | `object`  | Root object representing the vault.                                                                                                                                      |
| `vault.Account`                  |       Yes       | `string`  | The pseudo-account ID of the vault.                                                                                                                                      |
| `vault.Asset`                    |       Yes       | `object`  | Object representing the asset held in the vault.                                                                                                                         |
| `vault.Asset.currency`           |       Yes       | `string`  | Currency code of the asset stored in the vault.                                                                                                                          |
| `vault.Asset.issuer`             |       No        | `string`  | Issuer address of the asset.                                                                                                                                             |
| `vault.AssetsAvailable`          |       Yes       | `string`  | Amount of assets currently available for withdrawal.                                                                                                                     |
| `vault.AssetsTotal`              |       Yes       | `string`  | Total amount of assets in the vault.                                                                                                                                     |
| `vault.Flags`                    |       No        | `number`  | Bit-field flags associated with the vault.                                                                                                                               |
| `vault.LedgerEntryType`          |       Yes       | `string`  | Ledger entry type, always "Vault".                                                                                                                                       |
| `vault.LossUnrealized`           |       No        | `string`  | Unrealized loss associated with the vault.                                                                                                                               |
| `vault.Owner`                    |       Yes       | `string`  | ID of the Vault Owner account.                                                                                                                                           |
| `vault.OwnerNode`                |       No        | `string`  | Identifier for the owner node in the ledger tree.                                                                                                                        |
| `vault.PreviousTxnID`            |       Yes       | `string`  | Transaction ID of the last modification to this vault.                                                                                                                   |
| `vault.PreviousTxnLgrSeq`        |       Yes       | `number`  | Ledger sequence number of the last transaction modifying this vault.                                                                                                     |
| `vault.Sequence`                 |       Yes       | `number`  | Sequence number of the vault entry.                                                                                                                                      |
| `vault.ShareMPTID`               |       No        | `string`  | Multi-purpose token ID associated with this vault.                                                                                                                       |
| `vault.WithdrawalPolicy`         |       No        | `number`  | Policy defining withdrawal conditions.                                                                                                                                   |
| `vault.index`                    |       Yes       | `string`  | Unique index of the vault ledger entry.                                                                                                                                  |
| `vault.shares`                   |       Yes       | `object`  | Object containing details about issued shares.                                                                                                                           |
| `vault.shares.Flags`             |       No        | `number`  | Bit-field flags associated with the shares issuance.                                                                                                                     |
| `vault.shares.Issuer`            |       Yes       | `string`  | The ID of the Issuer of the Share. It will always be the pseudo-account ID.                                                                                              |
| `vault.shares.LedgerEntryType`   |       Yes       | `string`  | Ledger entry type, always "MPTokenIssuance".                                                                                                                             |
| `vault.shares.OutstandingAmount` |       Yes       | `string`  | Total outstanding shares issued.                                                                                                                                         |
| `vault.shares.OwnerNode`         |       No        | `string`  | Identifier for the owner node of the shares.                                                                                                                             |
| `vault.shares.PreviousTxnID`     |       Yes       | `string`  | Transaction ID of the last modification to the shares issuance.                                                                                                          |
| `vault.shares.PreviousTxnLgrSeq` |       Yes       | `number`  | Ledger sequence number of the last transaction modifying the shares issuance.                                                                                            |
| `vault.shares.Sequence`          |       Yes       | `number`  | Sequence number of the shares issuance entry.                                                                                                                            |
| `vault.shares.index`             |       Yes       | `string`  | Unique index of the shares ledger entry.                                                                                                                                 |
| `vault.shares.mpt_issuance_id`   |       No        | `string`  | The ID of the `MPTokenIssuance` object. It will always be equal to `vault.ShareMPTID`.                                                                                   |
| `vault.Scale`                    |       No        | `number`  | The `Scale` specifies the power of 10 ($10^{\text{scale}}$) to multiply an asset's value by when converting it into an integer-based number of shares. Absent when zero. |
| `vault.LEVersion`                |       No        | `number`  | `LendingProtocolV1_1`: accounting version of the Vault ([XLS-65.4.3](./65.4-lending-protocol-v1_1/65.4.3-cash-basis-vault.md)).                                          |
| `vault.AssetsDeployed`           |       No        | `string`  | `LendingProtocolV1_2`: principal lent out ([XLS-65.7.1](./65.7-lending-protocol-v1_2/65.7.1-fixed-precision.md)).                                                        |
| `vault.YieldUnrealized`          |       No        | `string`  | `LendingProtocolV1_2`: scheduled interest owed and not yet received ([XLS-65.7.1](./65.7-lending-protocol-v1_2/65.7.1-fixed-precision.md)).                              |
| `vault.VaultKind`                |       No        | `number`  | `LendingProtocolV1_1`: Vault kind; absent means open-ended and `1` means closed-ended.                                                                                   |
| `vault.SubscriptionDate`         |       No        | `number`  | `LendingProtocolV1_1`: End of Subscription and start of Investment; present only for closed-ended Vaults.                                                                |
| `vault.RedemptionDate`           |       No        | `number`  | `LendingProtocolV1_1`: Start of Redemption; present only for closed-ended Vaults.                                                                                        |

The standard `ledger_entry` RPC returns the same `Vault` ledger object. Under `LendingProtocolV1_1`, its object may therefore include `VaultKind`, `SubscriptionDate`, and `RedemptionDate` with the same meanings and presence rules: all three are present for a closed-ended Vault, while their collective absence means open-ended.

#### 3.9.3 Failure Conditions

- **`invalidParams`**: neither `vault_id` alone nor both `owner` and `seq` are given; `vault_id` is not a hex string; or `seq` is not a positive 32-bit integer.
- **`actMalformed`**: `owner` is not a valid address.
- **`entryNotFound`**: the Vault, or its share `MPTokenIssuance`, does not exist in the selected ledger, or `vault_id` is zero.
- Standard ledger selection errors apply if `ledger_hash` or `ledger_index` reference an unavailable ledger.

#### 3.9.4 Example Request

```json
{
  "method": "vault_info",
  "params": [
    {
      "vault_id": "2DE64CA41250EF3CB7D2B127D6CEC31F747492CAE2BD1628CA02EA1FFE7475B3",
      "ledger_index": "validated"
    }
  ]
}
```

#### 3.9.5 Example Response

Vault holding an `IOU`:

```json
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

```json
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
    "value": "1"
  },
  "ShareTotal": 5000,
  "WithdrawalPolicy": "0x0001",
  "Scale": 0
}
```

Vault holding `XRP`:

```json
{
  "result": {
    "ledger_hash": "6FFF56DF92D54D01EE3D5487787F4430D66F89C6BC74B00C276262A0207B2FAD",
    "ledger_index": 6,
    "status": "success",
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
      },
      "Scale": 0
    }
  }
}
```

### 4.2 RPC `vault_list` (Clio-only)

This RPC retrieves all Vaults created for a given asset. The asset can be `XRP`, an `IOU`, or an `MPT`.

Given an `asset`, this handler scans all `Vault` ledger objects and returns those whose `Asset` field matches the request. For each matching vault found, a summary is returned containing the vault ID, pseudo-account, owner, total assets, total shares, status, and flags.

The matching strategy depends on the asset type:

- **`MPT`**: Returns all `Vault` objects whose `Asset.mpt_issuance_id` equals the provided `mpt_issuance_id`.
- **`IOU`**: Returns all `Vault` objects whose `Asset.currency` and `Asset.issuer` match the provided values.
- **`XRP`**: Returns all `Vault` objects whose `Asset.currency` is `"XRP"`.

#### 4.2.1 Request Fields

| Field Name     |     Required?      |     JSON Type      | Description                                                                                                                                                                                          |
| -------------- | :----------------: | :----------------: | :--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `asset`        | :heavy_check_mark: | `string or object` | The asset to search for. Supports three formats: **XRP** — `{ "currency": "XRP" }`; **IOU** — `{ "currency": "<code>", "issuer": "<address>" }`; **MPT** — `{ "mpt_issuance_id": "<UINT192 hex>" }`. |
| `ledger_hash`  |                    |      `string`      | A 20-byte hex string for the ledger version to use.                                                                                                                                                  |
| `ledger_index` |                    | `string or number` | The ledger index of the ledger to use, or a shortcut string to choose a ledger automatically.                                                                                                        |
| `limit`        |                    |      `number`      | Limit the number of Vaults returned. Min `10`, max `400`, default `200`.                                                                                                                             |
| `marker`       |                    |      `string`      | Value from a previous paginated response. Resume retrieving data where that response left off.                                                                                                       |

#### 4.2.2 Response

| Field Name              | Required? | JSON Type          | Description                                                                                                          |
| ----------------------- | --------- | ------------------ | -------------------------------------------------------------------------------------------------------------------- |
| `asset`                 | `yes`     | `string or object` | The asset provided in the request, echoed back.                                                                      |
| `ledger_hash`           | `yes`     | `string`           | The identifying hash of the ledger version used to generate this response.                                           |
| `ledger_index`          | `yes`     | `number`           | The ledger index of the ledger version used to generate this response.                                               |
| `validated`             | `yes`     | `boolean`          | If `true`, the information comes from a validated ledger version.                                                    |
| `limit`                 | `yes`     | `number`           | The limit used in the request (after clamping).                                                                      |
| `marker`                | `no`      | `string`           | Server-defined value indicating the response is paginated. Pass this to the next call to resume where this left off. |
| `vaults`                | `yes`     | `array`            | Array of vault summary objects.                                                                                      |
| `vaults[].vault_id`     | `yes`     | `string`           | Unique index of the `Vault` ledger entry (hex).                                                                      |
| `vaults[].account`      | `yes`     | `string`           | The address of the Vault's _pseudo-account_.                                                                         |
| `vaults[].owner`        | `yes`     | `string`           | The account address of the Vault Owner.                                                                              |
| `vaults[].total_assets` | `yes`     | `string`           | The total value of the vault (`AssetsTotal`).                                                                        |
| `vaults[].total_shares` | `yes`     | `number`           | Total outstanding shares issued (`OutstandingAmount` from the share `MPTokenIssuance`).                              |
| `vaults[].status`       | `yes`     | `string`           | Status of the vault. `"active"` if flags are `0`, otherwise `"modified"`.                                            |
| `vaults[].flags`        | `yes`     | `number`           | Bit-field flags associated with the vault.                                                                           |

#### 4.2.3 Failure Conditions

- **`invalidParams`**: The `asset` field is missing, malformed, or not a valid asset object.
- **`entryNotFound`**: The asset references a ledger object that does not exist. This applies when the asset is an `MPT` and the `MPTokenIssuance` object identified by `mpt_issuance_id` does not exist, or the asset is an `IOU` and the `issuer` account does not exist in the specified ledger.
- Standard ledger selection errors apply if `ledger_hash` or `ledger_index` reference an unavailable ledger.

> **Note:** If the specified asset is valid and exists on the ledger, but no Vaults have been created for it, the response returns an empty `vaults` array. This is not an error condition.

#### 4.2.4 Example Request (MPT)

```json
{
  "method": "vault_list",
  "params": [
    {
      "asset": {
        "mpt_issuance_id": "00000001C752C42A1EBD6BF2403134F7CFD2F1D835AFD26E"
      },
      "limit": 50
    }
  ]
}
```

#### 4.2.5 Example Response (MPT)

```json
{
  "result": {
    "asset": {
      "mpt_issuance_id": "00000001C752C42A1EBD6BF2403134F7CFD2F1D835AFD26E"
    },
    "ledger_hash": "6FFF56DF92D54D01EE3D5487787F4430D66F89C6BC74B00C276262A0207B2FAD",
    "ledger_index": 6,
    "validated": true,
    "limit": 50,
    "vaults": [
      {
        "vault_id": "2DE64CA41250EF3CB7D2B127D6CEC31F747492CAE2BD1628CA02EA1FFE7475B3",
        "account": "rKwvc1mgHLyHKY3yRUqVwffWtsxYb3QLWf",
        "owner": "rwhaYGnJMexktjhxAKzRwoCcQ2g6hvBDWu",
        "total_assets": "100",
        "total_shares": 100,
        "status": "active",
        "flags": 0
      },
      {
        "vault_id": "C043BB1B350FFC5FED21E40535609D3D95BC0E3CE252E2F69F85BE0157020A52",
        "account": "rBVxExjRR6oDMWCeQYgJP7q4JBLGeLBPyv",
        "owner": "rwhaYGnJMexktjhxAKzRwoCcQ2g6hvBDWu",
        "total_assets": "500",
        "total_shares": 500,
        "status": "active",
        "flags": 0
      }
    ]
  }
}
```

#### 4.2.6 Example Request (IOU)

```json
{
  "method": "vault_list",
  "params": [
    {
      "asset": {
        "currency": "USD",
        "issuer": "r9cZ5oHbdL4Z9Maj6TdnfAos35nVzYuNds"
      },
      "limit": 20
    }
  ]
}
```

#### 4.2.7 Example Response (IOU)

```json
{
  "result": {
    "asset": {
      "currency": "USD",
      "issuer": "r9cZ5oHbdL4Z9Maj6TdnfAos35nVzYuNds"
    },
    "ledger_hash": "AB12CD34EF5678901234567890ABCDEF1234567890ABCDEF1234567890ABCDEF",
    "ledger_index": 42,
    "validated": true,
    "limit": 20,
    "vaults": [
      {
        "vault_id": "A1B2C3D4E5F6A1B2C3D4E5F6A1B2C3D4E5F6A1B2C3D4E5F6A1B2C3D4E5F6A1B2",
        "account": "rPqR7tSzR8v1M3K2pNqL5xW9Y4Z6A8B0CD",
        "owner": "rwhaYGnJMexktjhxAKzRwoCcQ2g6hvBDWu",
        "total_assets": "1000.50",
        "total_shares": 1000500000,
        "status": "active",
        "flags": 0
      }
    ]
  }
}
```

#### 4.2.8 Example Request (XRP)

```json
{
  "method": "vault_list",
  "params": [
    {
      "asset": {
        "currency": "XRP"
      },
      "limit": 100
    }
  ]
}
```

#### 4.2.9 Example Response (XRP)

```json
{
  "result": {
    "asset": {
      "currency": "XRP"
    },
    "ledger_hash": "6FFF56DF92D54D01EE3D5487787F4430D66F89C6BC74B00C276262A0207B2FAD",
    "ledger_index": 6,
    "validated": true,
    "limit": 100,
    "vaults": [
      {
        "vault_id": "C043BB1B350FFC5FED21E40535609D3D95BC0E3CE252E2F69F85BE0157020A52",
        "account": "rBVxExjRR6oDMWCeQYgJP7q4JBLGeLBPyv",
        "owner": "rwhaYGnJMexktjhxAKzRwoCcQ2g6hvBDWu",
        "total_assets": "10000000",
        "total_shares": 10000000,
        "status": "active",
        "flags": 0
      }
    ]
  }
}
```

## 4. Rationale

**A _pseudo-account_ holds the assets.** Assets on the XRP Ledger must be held by an account, and a ledger object cannot hold them directly. The Vault therefore holds its assets in a _pseudo-account_ that follows [XLS-64](../XLS-0064-pseudo-account/README.md). No one can sign for that account, so assets leave it only through the Vault transactions.

**Shares are Multi-Purpose Tokens.** Issuing shares as an MPT from the _pseudo-account_ makes them first-class assets that other ledger protocols can hold and transfer, while the Vault Owner can still make them non-transferable or restrict them to a Permissioned Domain. Share holders remain subject to the compliance controls of the underlying asset ([A.3](#a3-how-can-a-depositor-transfer-shares-to-another-account)).

**`Scale` converts fractional assets to whole shares.** MPT amounts are integers. Scaling asset amounts by $10^{Scale}$ before converting them to shares keeps fractional asset values without losing value to truncation.

**Unrealized loss lowers the share price before the loss is realized.** If a loss were reflected only when it is realized, an informed depositor could redeem early and leave the remaining depositors to bear it. `LossUnrealized` lowers the value of a share for withdrawals as soon as a loss is expected. Deposits use a separate exchange rate, so that a depositor cannot buy shares at the lowered price and profit when the loss is cleared ([§3.1.7.1](#3171-unrealized-loss)).

**The protocol chooses the rounding direction.** Share and asset conversions round in the direction the protocol specifies for each operation, not a direction the submitter chooses ([§3.1.6.1](#3161-scale)).

**Both `Withdraw` and `Redeem` forms exist.** `VaultWithdraw` accepts either an asset amount or a share amount, so that users do not have to compute the exchange rate off-chain ([A.1](#a1-why-does-the-specification-allow-both-withdraw-and-redeem-and-not-just-one-of-them)).

**Withdrawal is not gated by Permissioned Domain membership.** A depositor whose credentials expire or are revoked can still redeem the shares they hold, so a private Vault cannot lock a depositor's funds by removing their access ([A.2](#a2-why-can-any-account-that-holds-vaults-shares-submit-a-vaultwithdraw-transaction)).

## 5. Security Considerations

Closed-ended Vaults intentionally lock depositor capital during Investment: `VaultWithdraw` is rejected after Subscription and before Redemption. Depositors must inspect the immutable `SubscriptionDate` and `RedemptionDate` before depositing. `VaultClawback` remains available throughout Investment so an issuer's compliance controls are not blocked by the depositor withdrawal gate. See [XLS-65.4.4](./65.4-lending-protocol-v1_1/65.4.4-closed-ended-vault.md) for the full lifecycle and threat analysis.

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

`VaultDeposit` never charges a transfer fee.

- `SingleAssetVault`: `VaultWithdraw` does not charge a transfer fee either.
- `fixCleanup3_5_0`: `VaultWithdraw` charges the asset's transfer fee when the destination differs from the submitter and neither is the asset issuer ([XLS-65.6](./65.6-fix-cleanup-3_5_0/README.md)). Withdrawing to oneself, or to or from the issuer, stays free of the fee.

## Appendix B: Changelog

- [XLS-65.1](./65.1-fix-cleanup-3_1_3/README.md): `fixCleanup3_1_3`. Trust-line limit check for share-denominated withdrawals, and the zero-`Amount` clawback clamp.
- [XLS-65.2](./65.2-fix-cleanup-3_2_0/README.md): `fixCleanup3_2_0`. Deposit rounding, sole-shareholder waiver, exact full redemption, withdrawal `lsfMPTCanTransfer` waiver, `ReferenceHolding`, and invariant comparison scale.
- [XLS-65.3](./65.3-fix-cleanup-3_3_0/README.md): `fixCleanup3_3_0`. Deposit and withdrawal freeze checks.
- [XLS-65.4](./65.4-lending-protocol-v1_1/README.md): `LendingProtocolV1_1` Vault changes: [65.4.1 Unmodifiable Vault Fields](./65.4-lending-protocol-v1_1/65.4.1-unmodifiable-vault-fields.md), [65.4.2 Vault Deletion Memo](./65.4-lending-protocol-v1_1/65.4.2-vault-deletion-memo.md), [65.4.3 Cash-Basis Vault](./65.4-lending-protocol-v1_1/65.4.3-cash-basis-vault.md), and [65.4.4 Closed-Ended Vault](./65.4-lending-protocol-v1_1/65.4.4-closed-ended-vault.md).
- [XLS-65.5](./65.5-fix-cleanup-3_4_0/README.md): `fixCleanup3_4_0`. Admits one unit of rounding slack for IOU accounting invariants and for the matching `VaultDeposit`, `VaultWithdraw` and `VaultClawback` state-change deltas, requires `LossUnrealized` to be non-negative, and narrows `VaultSet` cap enforcement to transactions that supply `AssetsMaximum` or otherwise change the cap. Also truncates burned shares, adds `VaultWithdraw` credential and domain checks, and refuses pseudo-account destinations and holders.
- [XLS-65.6](./65.6-fix-cleanup-3_5_0/README.md): `fixCleanup3_5_0`. Withdrawal transfer fee, `AssetsMaximum` range checks, and missing-holder clawback.
- [XLS-65.7](./65.7-lending-protocol-v1_2/README.md): `LendingProtocolV1_2` Vault changes: [65.7.1 Fixed Precision Vault](./65.7-lending-protocol-v1_2/65.7.1-fixed-precision.md) and [65.7.2 Vault Transactions in Batch](./65.7-lending-protocol-v1_2/65.7.2-vault-transactions-in-batch.md).
