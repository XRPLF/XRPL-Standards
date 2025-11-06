<pre>
  xls: 66
  title: Lending Protocol
  description: XRP Ledger-native protocol for issuing uncollateralized, fixed-term loans using pooled funds, enabling on-chain credit origination.
  author: Vytautas Vito Tumas (@Tapanito) Aanchal Malhotra <amalhotra@ripple.com>
  status: Draft
  category: Amendment
  created: 2024-10-18
</pre>

## _Abstract_

Decentralized Finance (DeFi) lending represents a transformative force within the blockchain ecosystem. It revolutionizes traditional financial services by offering a peer-to-peer alternative without intermediaries like banks or financial institutions. At its core, DeFi lending platforms empower users to borrow and lend digital assets directly, fostering financial inclusion, transparency, and efficiency.

This proposal introduces fundamental primitives for an XRP Ledger-native Lending Protocol. The protocol offers straightforward on-chain uncollateralized fixed-term loans, utilizing pooled funds with pre-set terms for interest-accruing loans. The design relies on off-chain underwriting and risk management to assess the creditworthiness of the borrowers. However, the First-Loss Capital protection scheme absorbs some of the losses in case of a Loan Default.

This version intentionally skips the complex mechanisms of automated on-chain collateral and liquidation management. Instead, it focuses on the primitives and the essential components for on-chain credit origination. Therefore, the primary design principle is flexibility and reusability to enable the introduction of additional complex features in the future.

## Index

- [**1. Introduction**](#1-introduction)
  - [**1.1. Overview**](#11-overview)
  - [**1.2. Compliance Features**](#12-compliance-features)
  - [**1.3. Risk Management**](#13-risk-management)
  - [**1.4. Interest Rates**](#14-interest-rates)
  - [**1.5. Fees**](#15-fees)
  - [**1.6. Terminology**](#16-terminology)
  - [**1.7. System Diagram**](#17-system-diagram)
- [**2. Ledger Entries**](#2-ledger-entries)
  - [**2.1. LoanBroker Ledger Entry**](#21-loanbroker-ledger-entry)
    - [**2.1.1. Object Identifier**](#211-object-identifier)
    - [**2.1.2. Fields**](#212-fields)
    - [**2.1.3. LoanBroker _pseudo-account_**](#213-loanbroker-pseudo-account)
    - [**2.1.4. Ownership**](#214-ownership)
    - [**2.1.5. Reserves**](#215-reserves)
    - [**2.1.6. Accounting**](#216-accounting)
    - [**2.1.7. First-Loss Capital**](#217-first-loss-capital)
  - [**2.2. Loan Ledger Entry**](#22-loan-ledger-entry)
    - [**2.2.1. Object Identifier**](#221-object-identifier)
    - [**2.2.2. Fields**](#222-fields)
    - [**2.2.3. Ownership**](#223-ownership)
    - [**2.2.4. Reserves**](#224-reserves)
    - [**2.2.5. Impairment**](#225-impairment)
- [**3. Transactions**](#3-transactions)
  - [**3.1. LoanBroker Transactions**](#31-loanbroker-transactions)
    - [**3.1.1. LoanBrokerSet Transaction**](#311-loanbrokerset)
    - [**3.1.2. LoanBrokerDelete Transaction**](#312-loanbrokerdelete)
    - [**3.1.3. LoanBrokerCoverDeposit Transaction**](#313-loanbrokercoverdeposit)
    - [**3.1.4. LoanBrokerCoverWithdraw Transaction**](#314-loanbrokercoverwithdraw)
    - [**3.1.5. LoanBrokerCoverClawback Transaction**](#315-loanbrokercoverclawback)
  - [**3.2 Loan Transactions**](#32-loan-transactions)
    - [**3.2.1. LoanSet Transaction**](#321-loanset-transaction)
    - [**3.2.2. LoanDelete Transaction**](#322-loandelete-transaction)
    - [**3.2.3. LoanManage Transaction**](#323-loanmanage-transaction)
    - [**3.2.4. LoanPay Transaction**](#324-loanpay-transaction)
- [**Appendix**](#appendix)

## 1. Introduction

### 1.1 Overview

The Lending Protocol uses the [Vault](https://github.com/XRPLF/XRPL-Standards/discussions/192) on-chain object to provision assets from one or more depositors. A Loan Broker is responsible for managing the Lending Protocol and the associated Vault. The Vault Owner and Loan Broker must be on the same account, but this may change in the future.

The specification introduces two new ledger entries: `LoanBroker` and `Loan`. The `LoanBroker` object captures the Lending Protocol-specific details, such as fees and First-Loss Capital cover. Furthermore, it tracks the funds taken from the `Vault`. The `Loan` object captures the Loan agreement between the Loan Broker and the Borrower.

The specification introduces the following transactions:

- **`LoanBrokerSet`**: A transaction to create a new `LoanBroker` object.
- **`LoanBrokerDelete`**: A transaction to delete an existing `LoanBroker` object.
- **`LoanBrokerCoverDeposit`**: A transaction to deposit First-Loss Capital.
- **`LoanBrokerCoverWithdraw`**: A transaction to withdraw First-Loss Capital.
- **`LoanBrokerCoverClawback`**: A transaction to clawback the First-Loss Capital. This transaction can only be submitted by the Issuer of the asset.
- **`LoanSet`**: A transaction to create a new `Loan` object.
- **`LoanDelete`**: A transaction to delete an existing `Loan` object.
- **`LoanManage`**: A transaction to manage an existing `Loan`.
- **`LoanPay`**: A transaction to make a `Loan` payment.

The flow of the lending protocol is as follows:

1. The Loan Broker creates a `Vault` ledger entry.
2. The Loan Broker creates a `LoanBroker` ledger entry with a `LoanBrokerSet` transaction.
3. The Depositors deposit assets into the `Vault`.
4. Optionally, the Loan Broker deposits First-Loss Capital into the `LoanBroker` with the `LoanBrokerCoverDeposit` transaction.
5. The Loan Broker and Borrower create a `Loan` object with a `LoanSet` transaction and the requested principal (excluding fees) is transered to the Borrower.
6. If the Borrower fails to pay the Loan, the Loan Broker can default the `Loan` using the `LoanManage` transaction.
7. Once the Loan has matured (or defaulted), the Borrower or the Loan Broker can delete it using a `LoanDelete` transaction.
8. Optionally, the Loan Broker can withdraw the First-Loss Capital using the `LoanBrokerCoverWithdraw` transaction.
9. When all `Loan` objects are deleted, the Loan Broker can delete the `LoanBroker` object with a `LoanBrokerDelete` transaction.
10. When all `LoanBroker` objects are deleted, the Loan Broker can delete the `Vault` object.

### 1.2 Compliance Features

### 1.2.1 Clawback

Clawback is a mechanism by which an asset Issuer (IOU or MPT, not XRP) claws back the funds. The Issuer may clawback funds from the First-Loss Capital.

### 1.2.2 Freeze

Freeze is a mechanism by which an asset Issuer (IOUT or MPT, not XRP) freezes an `Account`, preventing that account from sending the Asset. Deep Freeze is a mechanism by which an asset Issuer prevents and `Account` from both sending and receiving and Asset. Finally, an Issuer may enact a global freeze, which prevents everyone from sending or receiving the Asset. Note that in both single-account and global freezes, the Asset can be sent to the Issuer.

If the Issuer freezes a Borrower's account, the Borrower cannot make loan payments. However, a frozen account does not lift the obligation to repay a Loan. If the Issuer Deep Freezes a Borrower's account, the Brrower cannot make loan payments.

A Deep Freeze does not affect the Loan Broker's functions. However, a Deep Freeze will prevent the Loan Broker from receing any Lending Protocol Fees.

The Issuer may also Freeze of Deep Freeze the `_pseudo-account_` of the Loan Broker. A Freeze on the `_pseudo-account_` will prevent the Loan Broker from creating new Loans. However existing Loans will not be affected. In contrast, a Deep Freeze, will also prevent the Loans from being paid.

### 1.3 Risk Management

Risk management involves mechanisms that mitigate the risks associated with lending. To protect investors' assets, we have introduced an optional first-loss capital protection scheme. This scheme requires the Loan Broker to deposit a fund that can be partially liquidated to cover losses in the event of a loan default. The amount of first-loss capital required is a percentage of the total debt owed to the Vault. In case of a default, a portion of the first-loss capital will be liquidated based on the minimum required cover. The liquidated capital is placed back into the Vault to cover some of the loss.

### 1.4 Interest Rates

There are three basic interest rates associated with a Loan:

- **`Interest Rate`**: The regular interest rate based on the principal amount. It is the cost of borrowing funds.
- **`Late Interest Rate`**: A higher interest rate charged for a late payment.
- **`Full Payment Rate`**: An interest rate charged for repaying the total Loan early.

### 1.5 Fees

The lending protocol charges a number of fees that the Loan Broker can configure. The protocol will not charge the fees if the Loan Broker has not deposited enough First-Loss Capital.

- **`Management Fee`**: This is a fee charged by the Loan Broker, calculated as a percentage of the interest earned on loans. It's deducted from the interest that would otherwise go to the Vault depositors. Essentially, borrowers pay the full interest, but before that interest reaches depositors, the Loan Broker takes their cut.
- **`Loan Origination Fee`**: A nominal fee paid to the Loan Broker taken from the principal lent.
- **`Loan Service Fee`**: A nominal fee paid on top of each loan payment.
- **`Late Payment Fee`**: A nominal fee paid on top of a late payment.
- **`Early Payment Fee`**: A nominal fee paid on top of an early payment.

### 1.6 Terminology

#### 1.6.1 Terms

- **`Fixed-Term Loan`**: A type of Loan with a known end date and a constant periodic payment schedule.
- **`Principal`**: The original sum of money borrowed that must be repaid, excluding interest or other fees.
- **`Interest`**: The cost of borrowing the Asset, calculated as a percentage of the loan principal, which the Borrower pays to the Lender over time.
- **`Default`**: The failure by the Borrower to meet the obligations of a loan, such as missing payments.
- **`First-Loss Capital`**: The portion of capital that absorbs initial losses in case of a Default, protecting the Vault from loss.
- **`Term`**: The period over which a Borrower must repay the Loan.
- **`Amortization`**: The gradual repayment of a loan through scheduled payments that cover both interest and principal over time.
- **`Repayment Schedule`**: A detailed plan that outlines when and how much a borrower must pay to repay the Loan fLoan.
- **`Grace Period`**: A set period after the Loan's due date after which the Loan Broker can default the Loan

#### 1.6.2 Actors

- **`LoanBroker`**: The entity issuing the Loan.
- **`Borrower`**: The account that is borrowing funds.

### 1.7 System Diagram

```
+-----------------+                          +-----------------+                       +-----------------+
|    Depositor    |                          |    LoanBroker   |                       |     Borrower    |
|   AccountRoot   |                          |   AccountRoot   |                       |   AccountRoot   |
|-----------------|                          |-----------------|                       |-----------------|
| Owner Directory |                          | Owner Directory | <-----OwnerNode       | Owner Directory | <---------
+-----------------+                          +-----------------+           |           +-----------------+          |
      ^         |                                     |                    |                    |                   |
      |       Reserve                  ____________Reserve____________     |                  Reserve               |
   Account      |                     |                               |    |                    |                   |
      |         V                     V                               V    |                    V                   |
+-----------------+          +-----------------+          +-----------------+          +-----------------+          |
|                 |          |                 |1        N|                 |1        N|                 |          |
|     MPToken     |          |      Vault      |--------->|   LoanBroker    |--------->|       Loan      |-OwnerNode-
|                 |          |                 |          |                 |          |                 |
+-----------------+          +-----------------+          +-----------------+          +-----------------+
         |                            ^                        |    ^                            |
      Issuance                        |                        |    |                            |
         |                         Account                     | Account                         |
         V                            |              -VaultNode-    |                            |
+-----------------+          +-----------------+     |    +-----------------+                    |
|      Share      |          |  Pseudo-Account |     |    |  Pseudo-Account |                    |
| MPTokenIssuance |<--Issuer-|   AccountRoot   |     |    |   AccountRoot   |                    |
|                 |          |-----------------|     |    |-----------------|                    |
+-----------------+          | Owner Directory | <----    | Owner Directory | <- LoanBrokerNode---
                             +-----------------+          +-----------------+
```

[**Return to Index**](#index)

## 2. Ledger Entries

### 2.1. LoanBroker Ledger Entry

The `LoanBroker` object captures attributes of the Lending Protocol.

#### 2.1.1 Object Identifier

The key of the `LoanBroker` object is the result of [`SHA512-Half`](https://xrpl.org/docs/references/protocol/data-types/basic-data-types/#hashes) of the following values concatenated in order:

- The `LoanBroker` space key `0x006C` (Lower-case `l`).
- The `AccountID`(<https://xrpl.org/docs/references/protocol/binary-format/#accountid-fields>) of the account submitting the `LoanBrokerSet` transaction, i.e. `Lender`.
- The transaction `Sequence` number. If the transaction used a [Ticket](https://xrpl.org/docs/concepts/accounts/tickets/), use the `TicketSequence` value.

#### 2.1.2 Fields

The `LoanBroker` object has the following fields:

| Field Name             | User Modifiable? | Constant? |      Required?      | JSON Type | Internal Type | Default Value | Description                                                                                                                                                                                                  |
| ---------------------- | :--------------: | :-------: | :-----------------: | :-------: | :-----------: | :-----------: | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `LedgerEntryType`      |       `No`       |   `Yes`   | :heavy\*check_mark: | `string`  |   `UINT16`    |   `0x0088`    | Ledger object type.                                                                                                                                                                                          |
| `LedgerIndex`          |       `No`       |   `Yes`   | :heavy_check_mark:  | `string`  |   `UINT16`    |     `N/A`     | Ledger object identifier.                                                                                                                                                                                    |
| `Flags`                |      `Yes`       |   `No`    | :heavy_check_mark:  | `string`  |   `UINT32`    |       0       | Ledger object flags.                                                                                                                                                                                         |
| `PreviousTxnID`        |       `No`       |   `No`    | :heavy_check_mark:  | `string`  |   `HASH256`   |     `N/A`     | The ID of the transaction that last modified this object.                                                                                                                                                    |
| `PreviousTxnLgrSeq`    |       `No`       |   `No`    | :heavy_check_mark:  | `number`  |   `UINT32`    |     `N/A`     | The sequence of the ledger containing the transaction that last modified this object.                                                                                                                        |
| `Sequence`             |       `No`       |   `Yes`   | :heavy_check_mark:  | `number`  |   `UINT32`    |     `N/A`     | The transaction sequence number that created the `LoanBroker`.                                                                                                                                               |
| `LoanSequence`         |       `No`       |   `Yes`   | :heavy_check_mark:  | `number`  |   `UINT32`    |       0       | A sequential identifier for Loan objects, incremented each time a new Loan is created by this LoanBroker instance.                                                                                           |
| `OwnerNode`            |       `No`       |   `Yes`   | :heavy_check_mark:  | `number`  |   `UINT64`    |     `N/A`     | Identifies the page where this item is referenced in the owner's directory.                                                                                                                                  |
| `VaultNode`            |       `No`       |   `Yes`   | :heavy_check_mark:  | `number`  |   `UINT64`    |     `N/A`     | Identifies the page where this item is referenced in the Vault's \_pseudo-account\* owner's directory.                                                                                                       |
| `VaultID`              |       `No`       |   `Yes`   | :heavy\*check_mark: | `string`  |   `HASH256`   |     `N/A`     | The ID of the `Vault` object associated with this Lending Protocol Instance.                                                                                                                                 |
| `Account`              |       `No`       |   `Yes`   | :heavy_check_mark:  | `string`  |  `AccountID`  |     `N/A`     | The address of the `LoanBroker` _pseudo-account_.                                                                                                                                                            |
| `Owner`                |       `No`       |   `Yes`   | :heavy_check_mark:  | `string`  |  `AccountID`  |     `N/A`     | The address of the Loan Broker account.                                                                                                                                                                      |
| `Data`                 |      `Yes`       |   `No`    |                     | `string`  |    `BLOB`     |     None      | Arbitrary metadata about the `LoanBroker`. Limited to 256 bytes.                                                                                                                                             |
| `ManagementFeeRate`    |       `No`       |   `Yes`   |                     | `number`  |   `UINT16`    |       0       | The 1/10th basis point fee charged by the Lending Protocol. Valid values are between 0 and 10000 inclusive. A value of 1 is equivalent to 1/10 bps or 0.001%                                                 |
| `OwnerCount`           |       `No`       |   `No`    | :heavy_check_mark:  | `number`  |   `UINT32`    |       0       | The number of active Loans issued by the `LoanBroker`.                                                                                                                                                       |
| `DebtTotal`            |       `No`       |   `No`    | :heavy_check_mark:  | `number`  |   `NUMBER`    |       0       | The total asset amount the protocol owes the Vault, including interest.                                                                                                                                      |
| `DebtMaximum`          |      `Yes`       |   `No`    | :heavy_check_mark:  | `number`  |   `NUMBER`    |       0       | The maximum amount the protocol can owe the Vault. The default value of 0 means there is no limit to the debt.                                                                                               |
| `CoverAvailable`       |       `No`       |   `No`    | :heavy_check_mark:  | `number`  |   `NUMBER`    |       0       | The total amount of first-loss capital deposited into the Lending Protocol.                                                                                                                                  |
| `CoverRateMinimum`     |       `No`       |   `Yes`   | :heavy_check_mark:  | `number`  |   `UINT32`    |       0       | The 1/10th basis point of the `DebtTotal` that the first loss capital must cover. Valid values are between 0 and 100000 inclusive. A value of 1 is equivalent to 1/10 bps or 0.001%.                         |
| `CoverRateLiquidation` |       `No`       |   `Yes`   | :heavy_check_mark:  | `number`  |   `UINT32`    |       0       | The 1/10th basis point of minimum required first loss capital that is liquidated to cover a Loan default. Valid values are between 0 and 100000 inclusive. A value of 1 is equivalent to 1/10 bps or 0.001%. |

#### 2.1.3 `LoanBroker` _pseudo-account_

The `LoanBroker` _pseudo-account_ holds the First-Loss Capital deposited by the LoanBroker, as well as Loan funds. The _pseudo-account_ follows the XLS-64d specification for pseudo accounts. The `AccountRoot` object is created when creating the `Vault` object.

#### 2.1.4 Ownership

The lending protocol object is stored in the ledger and tracked in an [Owner Directory](https://xrpl.org/docs/references/protocol/ledger-data/ledger-entry-types/directorynode) owned by the account submitting the `LoanBrokerSet` transaction. Furthermore, the object is also tracked in the `OwnerDirectory` of the `Vault` _`pseudo-account`_. The `_pseudo_account_` `OwnerDirectory` page is captured by the `VaultNode` field.

The `RootIndex` of the `DirectoryNode` object is the result of [`SHA512-Half`](https://xrpl.org/docs/references/protocol/data-types/basic-data-types/#hashes) of the following values concatenated in order:

- The `OwnerDirectory` space key `0x004F`
- The `LoanBrokerID`

#### 2.1.5 Reserves

The `LoanBroker` object costs two owner reserve for the account creating it.

#### 2.1.6 Accounting

The Lending Protocol tracks the funds owed to the associated Vault in the `DebtTotal` attribute. It captures the principal amount taken from the Vault and the interest due, excluding all fees. The `DebtMaximum` attribute controls the maximum debt a Lending Protocol may incur. Whenever the Lender issues a Loan, `DebtTotal` is incremented by the Loan principal and interest, excluding fees. When $DebtTotal \geq DebtMaximum$, the Lender cannot issue new loans until some of the debt is cleared. Furthermore, the Lender may not issue a loan that would cause the `DebtTotal` to exceed `DebtMaximum`.

**Example**

```
Example 1: # Issuing a Loan #

** Initial States **

-- Vault --
AssetsTotal         = 100,000 Tokens
AssetsAvailable     = 100,000 Tokens
SharesTotal         = 100,000 Shares

-- Lending Protocol --
DebtTotal           = 0
# The fee charged by the Lending Protocol against any interest.
ManagementFeeRate   = 0.1 (10%)


# The Lender issues the following Loan
-- Loan --
PrincipalRequested = 1,000 Tokens
InterestRate       = 0.1 (10%)

# SIMPLIfIED
TotalInterestOutstanding        = PrincipalRequested x InterestRate
                    = 100 Tokens

** State Changes **

-- Vault --
# Increase the potential value of the Vault
AssetsTotal     = AssetsTotal + ((TotalInterestOutstanding - (TotalInterestOutstanding x ManagementFeeRate)))
                = 100,000 + (100 - (100 x 0.1)) = 100,000 + 90
                = 100,090 Tokens

# Decrease Asset Available in the Vault
AssetsAvailable = AssetsAvailable - PrincipalRequested
                = 100,000 - 1,000
                = 99,000 Tokens

SharesTotal     = (UNCHANGED)

-- Lending Protocol --
# Increase Lending Protocol Debt
DebtTotal   = DebtTotal + PrincipalRequested + (TotalInterestOutstanding - (TotalInterestOutstanding x ManagementFeeRate))
            = 0 + 1,000 + (100 - (100 x 0.1)) = 1,000 + 90
            = 1,090 Tokens


---------------------------------------------------------------------------------------------------

Example 2: # Loan Payment #

** Initial States **

-- Vault --
AssetsTotal         = 100,090 Tokens
AssetsAvailable     = 99,000 Tokens
SharesTotal         = 100,000 Shares

-- Lending Protocol --
DebtTotal           = 1,090 Tokens
# The fee charged by the Lending Protocol against any interest.
ManagementFeeRate   = 0.1 (10%)

-- Loan --
PrincipalRequested = 1,000 Tokens
InterestRate       = 0.1 (10%)
# SIMPLIFIED
PaymentRemaining   = 2

# SIMPLIFIED
TotalInterestOutstanding = PrincipalRequested x InterestRate
                         = 100 Tokens


# The Borrower makes a single payment

PaymentAmount           = 550 Tokens
PaymentPrincipalPortion = 500 Tokens
PaymentInterestPortion  = 50 Tokens


** State Changes **

-- Vault --
AssetsTotal     = (UNCHANGED)

# Increase Asset Available in the Vault
AssetsAvailable = AssetsAvailable + PaymentPrincipalPortion + (PaymentInterestPortion - (PaymentInterestPortion x ManagementFeeRate))
                = 99,000 + 500 + (50 - (50 x 0.1))
                = 99,545 Tokens

SharesTotal     = (UNCHANGED)

-- Lending Protocol --

# Decrease Lending Protocol Debt
DebtTotal   = DebtTotal - PaymentPrincipalAmount - (PaymentInterestPortion - (PaymentInterestPortion x ManagementFeeRate)
            = 1,090 - 500 - (50 - (50 x 0.1))
            = 545 Tokens

```

#### 2.1.7 First-Loss Capital

The First-Loss Capital is an optional mechanism to protect the Vault depositors from incurring a loss in case of a Loan default. The first loss of capital absorbs some of the loss. The following parameters control the First-Loss Capital:

- `CoverAvailable` - the total amount of cover deposited by the Lending Protocol Owner.
- `CoverRateMinimum` - the percentage of `DebtTotal` that must be covered by the `CoverAvailable`.
- `CoverRateLiquidation` - the maximum percentage of the minimum required cover ($DebtTotal \times CoverRateMinimum$) that will be liquidated to cover a Loan Default.

Whenever the available cover falls below the minimum cover required, two consequences occur:

- The Lender cannot issue new Loans.
- The Lender cannot directly receive fees. The fees are instead added to the First Loss Capital to cover the deficit.

**Examples**

```
Example 1: Loan Default

** Initial States **

-- Vault --
AssetsTotal             = 100,090 Tokens
AssetsAvailable         = 99,000 Tokens
SharesTotal             = 100,000 Tokens

-- Lending Protocol --
DebtTotal               = 1,090 Tokens
CoverRateMinimum        = 0.1 (10%)
CoverRateLiquidation    = 0.1 (10%)
CoverAvailable          = 1,000 Tokens

-- Loan --
PrincipleOutstanding  = 1,000 Tokens
InterestOutstanding   = 90 Tokens


# First-Loss Capital liquidation maths

DefaultAmount = PrincipleOutstanding + InterestOutstanding
              = 1,000 + 90
              = 1,090

# The amount of the default that the first-loss capital scheme will cover
DefaultCovered      = min((DebtTotal x CoverRateMinimum) x CoverRateLiquidation, DefaultAmount)
                    = min((1,090 * 0.1) * 0.1, 1,090) = min(10.9, 1,090)
                    = 10.9 Tokens

Loss                = DefaultAmount - DefaultCovered
                    = 1,090 - 10.9
                    = 1,079.1 Tokens

FundsReturned       = DefaultCovered
                    = 10.9

# Note, Loss + FundsReturned MUST be equal to PrincipleOutstanding + InterestOutstanding

** State Changes **

-- Vault --
AssetsTotal     = AssetsTotal - Loss
                = 100,090 - 1,079.1
                = 99,010.9 Tokens

AssetsAvailable = AssetsAvailable + FundsReturned
                = 99,000 + 10.9
                = 99,010.9 Tokens

SharesTotal = (UNCHANGED)

-- Lending Protocol --
DebtTotal       = DebtTotal - PrincipleOutstanding + InterestOutstanding
                = 1,090 - (1,000 + 90)
                = 0 Tokens

CoverAvailable  = CoverAvailable - DefaultCovered
                = 1,000 - 10.9
                = 989.1 Tokens
```

[**Return to Index**](#index)

### 2.2. `Loan` Ledger Entry

A Loan ledger entry captures various Loan terms on-chain. It is an agreement between the Borrower and the loan issuer.

#### 2.2.1 Object Identifier

The `LoanID` is calculated as follows:

- Calculate [`SHA512-Half`](https://xrpl.org/docs/references/protocol/data-types/basic-data-types/#hashes) of the following values:
  - The `Loan` space key `0x004C` (capital L)
  - The [`AccountID`](https://xrpl.org/docs/references/protocol/binary-format/#accountid-fields) of the Borrower account.
  - The `LoanBrokerID` of the associated `LoanBroker` object.
  - The `LoanSequence` of the `LoanBroker` object.

#### 2.2.2 Fields

| Field Name                 | User Modifiable? | Constant? |     Required?      | JSON Type | Internal Type |                                   Default Value                                   | Description                                                                                                                                                           |
| -------------------------- | :--------------: | :-------: | :----------------: | :-------: | :-----------: | :-------------------------------------------------------------------------------: | --------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `LedgerEntryType`          |       `No`       |   `Yes`   | :heavy_check_mark: | `string`  |   `UINT16`    |                                     `0x0089`                                      | Ledger object type.                                                                                                                                                   |
| `LedgerIndex`              |       `No`       |   `Yes`   | :heavy_check_mark: | `string`  |   `UINT16`    |                                       `N/A`                                       | Ledger object identifier.                                                                                                                                             |
| `Flags`                    |      `Yes`       |   `No`    |                    | `string`  |   `UINT32`    |                                         0                                         | Ledger object flags.                                                                                                                                                  |
| `PreviousTxnID`            |       `No`       |   `No`    | :heavy_check_mark: | `string`  |   `HASH256`   |                                       `N/A`                                       | The ID of the transaction that last modified this object.                                                                                                             |
| `PreviousTxnLgrSeq`        |       `No`       |   `No`    | :heavy_check_mark: | `number`  |   `UINT32`    |                                       `N/A`                                       | The ledger sequence containing the transaction that last modified this object.                                                                                        |
| `LoanSequence`             |       `No`       |   `Yes`   | :heavy_check_mark: | `number`  |   `UINT32`    |                                       `N/A`                                       | The sequence number of the Loan.                                                                                                                                      |
| `OwnerNode`                |       `No`       |   `Yes`   | :heavy_check_mark: | `number`  |   `UINT64`    |                                       `N/A`                                       | Identifies the page where this item is referenced in the `Borrower` owner's directory.                                                                                |
| `LoanBrokerNode`           |       `No`       |   `Yes`   | :heavy_check_mark: | `number`  |   `UINT64`    |                                       `N/A`                                       | Identifies the page where this item is referenced in the `LoanBroker`s owner directory.                                                                               |
| `LoanBrokerID`             |       `No`       |   `Yes`   | :heavy_check_mark: | `string`  |   `HASH256`   |                                       `N/A`                                       | The ID of the `LoanBroker` associated with this Loan Instance.                                                                                                        |
| `Borrower`                 |       `No`       |   `Yes`   | :heavy_check_mark: | `string`  |  `AccountID`  |                                       `N/A`                                       | The address of the account that is the borrower.                                                                                                                      |
| `LoanOriginationFee`       |       `No`       |   `Yes`   | :heavy_check_mark: | `number`  |   `NUMBER`    |                                       `N/A`                                       | A nominal nds amount paid to the `LoanBroker.Owner` when the Loan is created.                                                                                         |
| `LoanServiceFee`           |       `No`       |   `Yes`   | :heavy_check_mark: | `number`  |   `NUMBER`    |                                       `N/A`                                       | A nominal funds amount paid to the `LoanBroker.Owner` with every Loan payment.                                                                                        |
| `LatePaymentFee`           |       `No`       |   `Yes`   | :heavy_check_mark: | `number`  |   `NUMBER`    |                                       `N/A`                                       | A nominal funds amount paid to the `LoanBroker.Owner` when a payment is late.                                                                                         |
| `ClosePaymentFee`          |       `No`       |   `Yes`   | :heavy_check_mark: | `number`  |   `NUMBER`    |                                       `N/A`                                       | A nominal funds amount paid to the `LoanBroker.Owner` when a payment full payment is made.                                                                            |
| `OverpaymentFee`           |       `No`       |   `Yes`   | :heavy_check_mark: | `number`  |   `UINT32`    |                                       `N/A`                                       | A fee charged on overpayments in 1/10th basis points. Valid values are between 0 and 100000 inclusive. (0 - 100%)                                                     |
| `InterestRate`             |       `No`       |   `Yes`   | :heavy_check_mark: | `number`  |   `UINT32`    |                                       `N/A`                                       | Annualized interest rate of the Loan in 1/10th basis points.                                                                                                          |
| `LateInterestRate`         |       `No`       |   `Yes`   | :heavy_check_mark: | `number`  |   `UINT32`    |                                       `N/A`                                       | A premium is added to the interest rate for late payments in 1/10th basis points. Valid values are between 0 and 100000 inclusive. (0 - 100%)                         |
| `CloseInterestRate`        |       `No`       |   `Yes`   | :heavy_check_mark: | `number`  |   `UINT32`    |                                       `N/A`                                       | An interest rate charged for repaying the Loan early in 1/10th basis points. Valid values are between 0 and 100000 inclusive. (0 - 100%)                              |
| `OverpaymentInterestRate`  |       `No`       |   `Yes`   | :heavy_check_mark: | `number`  |   `UINT32`    |                                       `N/A`                                       | An interest rate charged on overpayments in 1/10th basis points. Valid values are between 0 and 100000 inclusive. (0 - 100%)                                          |
| `StartDate`                |       `No`       |   `Yes`   | :heavy_check_mark: | `number`  |   `UINT32`    |                             `CurrentLedgerTimestamp`                              | The timestamp of when the Loan started [Ripple Epoch](https://xrpl.org/docs/references/protocol/data-types/basic-data-types/#specifying-time).                        |
| `PaymentInterval`          |       `No`       |   `Yes`   | :heavy_check_mark: | `number`  |   `UINT32`    |                                       `N/A`                                       | Number of seconds between Loan payments.                                                                                                                              |
| `GracePeriod`              |       `No`       |   `Yes`   | :heavy_check_mark: | `number`  |   `UINT32`    |                                       `N/A`                                       | The number of seconds after the Loan's Payment Due Date that the Loan can be Defaulted.                                                                               |
| `PreviousPaymentDueDate`   |       `No`       |   `No`    | :heavy_check_mark: | `number`  |   `UINT32`    |                                        `0`                                        | The timestamp of when the previous payment was made in [Ripple Epoch](https://xrpl.org/docs/references/protocol/data-types/basic-data-types/#specifying-time).        |
| `NextPaymentDueDate`       |       `No`       |   `No`    | :heavy_check_mark: | `number`  |   `UINT32`    |                   `LoanSet.StartDate + LoanSet.PaymentInterval`                   | The timestamp of when the next payment is due in [Ripple Epoch](https://xrpl.org/docs/references/protocol/data-types/basic-data-types/#specifying-time).              |
| `PaymentRemaining`         |       `No`       |   `No`    | :heavy_check_mark: | `number`  |   `UINT32`    |                              `LoanSet.PaymentTotal`                               | The number of payments remaining on the Loan.                                                                                                                         |
| `TotalValueOutstanding`    |       `No`       |   `No`    | :heavy_check_mark: | `number`  |   `NUMBER`    |                             `TotalValueOutstanding()`                             | The total outstanding value of the Loan, including all fees and interest.                                                                                             |
| `PrincipalOutstanding`     |       `No`       |   `No`    | :heavy_check_mark: | `number`  |   `NUMBER`    |                           `LoanSet.PrincipalRequested`                            | The principal amount that the Borrower still owes.                                                                                                                    |
| `ManagementFeeOutstanding` |       `No`       |   `No`    | :heavy_check_mark: | `number`  |   `NUMBER`    | `(TotalValueOutstanding() - PrincipalOutstanding) x LoanBroker.ManagementFeeRate` | The remaining Management Fee owed to the LoanBroker.                                                                                                                  |
| `PeriodicPayment`          |       `No`       |   `No`    | :heavy_check_mark: | `number`  |   `NUMBER`    |                              `LoanPeriodicPayment()`                              | The calculated periodic payment amount for each payment interval.                                                                                                     |
| `LoanScale`                |       `No`       |   `Yes`   |                    | `number`  |    `INT32`    |                                `LoanTotalValue()`                                 | The scale factor that ensures all computed amounts are rounded to the same number of decimal places. It is determined based on the total loan value at creation time. |

##### 2.2.2.1 Flags

The `Loan` object supports the following flags:

| Flag Name            |  Flag Value  | Modifiable? |                      Description                       |
| -------------------- | :----------: | :---------: | :----------------------------------------------------: |
| `lsfLoanDefault`     | `0x00010000` |    `No`     |     If set, indicates that the Loan is defaulted.      |
| `lsfLoanImpaired`    | `0x00020000` |    `Yes`    |      If set, indicates that the Loan is impaired.      |
| `lsfLoanOverpayment` | `0x00040000` |    `No`     | If set, indicates that the Loan supports overpayments. |

##### 2.2.2.2 TotalValueOutstanding

The total outstanding value of the Loan, including management fee charges against the interest. To calculate the outstanding interest portion, use this formula: `TotalInterestOutstanding = TotalValueOutstanding - PrincipalOutstanding - ManagementFeeOutstanding`.

##### 2.2.2.3 PrincipalOutstanding

The principal amount that the Borrower still owes. This amount decreases each time the borrower makes a successful loan payment. This field ensures that the loan is fully settled on the final payment.

##### 2.2.2.4 ManagementFeeOutstanding

The remaining Management Fee owed to the LoanBroker. This amount decreases each time the borrower makes a successful loan payment. This field ensures that the loan is fully settled on the final payment.

##### 2.2.2.5 PeriodicPayment

The periodic payment amount represents the precise sum the Borrower must pay during each payment cycle. For practical implementation, this value should be rounded UP when processing payments. The system automatically recalculates the PeriodicPayment following any overpayment by the borrower. For instance, when dealing with MPT loans, the calculated `PeriodicPayment` may be `10.251`. However, since MPTs only support whole number representations, the borrower would need to pay `11` units. The system maintains the precise periodic payment value at maximum accuracy since it is frequently referenced throughout loan payment computations.

#### 2.2.3 Ownership

The `Loan` objects are stored in the ledger and tracked in two [Owner Directories](https://xrpl.org/docs/references/protocol/ledger-data/ledger-entry-types/directorynode).

- The `OwnerNode` is the `Owner Directory` of the `Borrower` who is the main `Owner` of the `Loan` object, and therefore is responsible for the owner reserve.
- The `LoanBrokerNode` is the `Owner Directory` for the `LoanBroker` _pseudo-account_ to track all loans associated with the same `LoanBroker` object.

#### 2.2.4 Reserves

The `Loan` object costs one owner reserve for the `Borrower`.

#### 2.2.5 Loan Total Value

The loan's financial state is tracked through three key components:

- **PrincipalOutstanding**: Represents the remaining principal balance that the borrower must repay to satisfy the original loan amount.
- **TotalValueOutstanding**: Encompasses the complete remaining loan obligation, comprising the outstanding principal, all scheduled interest payments based on the original amortization schedule and the management fee paid on the interest. This value excludes any additional interest charges resulting from late payments, overpayments of full payments.
- **InterestOutstanding**: The total scheduled interest (including fee) remaining on the loan, derived as `TotalValueOutstanding - PrincipalOutstanding`.

**Asset-Specific Precision Handling**: Different asset types on the XRP Ledger have varying levels of precision that directly impact loan value calculations:

- **XRP (Drops)**: Only supports whole number values (1 drop = 0.000001 XRP)
- **MPTs (Multi-Purpose Tokens)**: Only support whole number values
- **IOUs**: Support up to 16 significant decimal digits

For loans denominated in discrete asset types (XRP drops and MPTs), all monetary values must be rounded to whole numbers. This rounding requirement means that:

1. **`TotalValueOutstanding`** is always rounded **up** to the nearest precision unit of an asset. This ensures the borrower pays at least the full theoretical value, preventing the loan from becoming underfunded due to rounding losses.

2. **`PrincipalOutstanding`** and **`ManagementFeeOutstanding`** are rounded to the nearest even number after each payment to avoid over-deducting from the borrower.

3. Due to the cumulative effect of rounding across multiple payment cycles, these on-ledger values may deviate by up to one asset unit from their theoretical mathematical values at any given time.

**Important**: Implementations must **not** recalculate these values from the theoretical formulas during payment processing. The stored ledger values are the authoritative source of truth. The pseudo-code in [Section 3.2.4.4](#3244-transaction-pseudo-code) demonstrates how to properly handle these rounding discrepancies while maintaining loan integrity.

**Late Payment Interest Treatment**: Late payment penalties and additional interest charges are calculated and collected separately from the core loan value. These charges do not modify the `TotalValueOutstanding` calculation, which remains anchored to the original scheduled payment terms.

#### 2.2.6 Impairment

When the Loan Broker discovers that the Borower cannot make an upcoming payment, impairment allows the Loan Broker to register a "paper loss" with the Vault. The impairment mechanism moves the Next Payment Due Date to the time the Loan was impaired, allowing to default the Loan more quickly. However, if the Borrower makes a payment, the impairment status is automatically cleared.

[**Return to Index**](#index)

## 3. Transactions

### 3.1. `LoanBroker` Transactions

In this section we specify the transactions associated with the `LoanBroker` ledger entry.

#### 3.1.1 `LoanBrokerSet`

The transaction creates a new `LoanBroker` object or updates an existing one.

| Field Name             |     Required?      | Modifiable? | JSON Type | Internal Type | Default Value | Description                                                                                                                                        |
| ---------------------- | :----------------: | :---------: | :-------: | :-----------: | :-----------: | :------------------------------------------------------------------------------------------------------------------------------------------------- |
| `TransactionType`      | :heavy_check_mark: |    `No`     | `string`  |   `UINT16`    |     `74`      | The transaction type.                                                                                                                              |
| `VaultID`              | :heavy_check_mark: |    `No`     | `string`  |   `HASH256`   |     `N/A`     | The Vault ID that the Lending Protocol will use to access liquidity.                                                                               |
| `LoanBrokerID`         |                    |    `No`     | `string`  |   `HASH256`   |     `N/A`     | The Loan Broker ID that the transaction is modifying.                                                                                              |
| `Flags`                |                    |    `Yes`    | `string`  |   `UINT32`    |       0       | Specifies the flags for the LoanBroker.                                                                                                            |
| `Data`                 |                    |    `Yes`    | `string`  |    `BLOB`     |     None      | Arbitrary metadata in hex format. The field is limited to 256 bytes.                                                                               |
| `ManagementFeeRate`    |                    |    `No`     | `number`  |   `UINT16`    |       0       | The 1/10th basis point fee charged by the Lending Protocol Owner. Valid values are between 0 and 10000 inclusive (1% - 10%).                       |
| `DebtMaximum`          |                    |    `Yes`    | `number`  |   `NUMBER`    |       0       | The maximum amount the protocol can owe the Vault. The default value of 0 means there is no limit to the debt. Must not be negative.               |
| `CoverRateMinimum`     |                    |    `No`     | `number`  |   `UINT32`    |       0       | The 1/10th basis point `DebtTotal` that the first loss capital must cover. Valid values are between 0 and 100000 inclusive.                        |
| `CoverRateLiquidation` |                    |    `No`     | `number`  |   `UINT32`    |       0       | The 1/10th basis point of minimum required first loss capital liquidated to cover a Loan default. Valid values are between 0 and 100000 inclusive. |

##### 3.1.1.1 Failure Conditions

- If `LoanBrokerID` is not specified:

  - `Vault` object with the specified `VaultID` does not exist on the ledger.
  - The submitter `AccountRoot.Account != Vault(VaultID).Owner`.

- If `LoanBrokerID` is specified:

  - `LoanBroker` object with the specified `LoanBrokerID` does not exist on the ledger.
  - The submitter `AccountRoot.Account != LoanBroker(LoanBrokerID).Owner`.
  - The submitter is attempting to modify fixed fields.

- Any of the fields are _invalid_.

##### 3.1.1.2 State Changes

- If `LoanBrokerID` is not specified:

  - Create a new `LoanBroker` ledger object.

  - Create a new `AccountRoot` _pseudo-account_ object, setting the `AccountRoot.LoanBrokerID` to `LoanBrokerID`.

    - If the `Vault(VaultID).Asset` is an `IOU`:

      - Create a `RippleState` object between the `Issuer` and the `LoanBroker` _pseudo-account_.

    - If the `Vault(VaultID).Asset` is an `MPT`:

      - Create an `MPToken` object for the `LoanBroker` _pseudo-account_.

  - Add `LoanBrokerID` to the `OwnerDirectory` of the submitting account.
  - Add `LoanBrokerID` to the `OwnerDirectory` of the Vault's _pseudo-account_.

- If `LoanBrokerID` is specified:
  - Update appropriate fields.

##### 3.1.1.3 Invariants

**TBD**

[**Return to Index**](#index)

#### 3.1.2 `LoanBrokerDelete`

| Field Name        |     Required?      | JSON Type | Internal Type | Default Value | Description                                          |
| ----------------- | :----------------: | :-------: | :-----------: | :-----------: | :--------------------------------------------------- |
| `TransactionType` | :heavy_check_mark: | `string`  |   `UINT16`    |     `75`      | The transaction type.                                |
| `LoanBrokerID`    | :heavy_check_mark: | `string`  |   `HASH256`   |     `N/A`     | The Loan Broker ID that the transaction is deleting. |

##### 3.1.2.1 Failure Conditions

- `LoanBroker` object with the specified `LoanBrokerID` does not exist on the ledger.
- The submitter `AccountRoot.Account != LoanBroker(LoanBrokerID).Owner`.

- The `OwnerCount > 0` there are loan objects.
- The `DebtTotal > 0` there are unpaid loans.

##### 3.1.2.2 State Changes

- Delete `LoanBrokerID` from the `OwnerDirectory` of the submitting account.
- Delete `LoanBrokerID` from the `OwnerDirectory` of the Vault's _pseudo-account_.

- If the `Vault(LoanBroker(LoanBrokerID).VaultID).Asset` is `XRP`:

  - Decrease the `Balance` field of `LoanBroker` _pseudo-account_ `AccountRoot` by `CoverAvailable`.
  - Increase the `Balance` field of the submitter `AccountRoot` by `CoverAvailable`.

- If the `Vault(LoanBroker(LoanBrokerID).VaultID).Asset` is an `IOU`:

  - Decrease the `RippleState` balance between the `LoanBroker` _pseudo-account_ `AccountRoot` and the `Issuer` `AccountRoot` by `CoverAvailable`.
  - Increase the `RippleState` balance between the submitter `AccountRoot` and the `Issuer` `AccountRoot` by `CoverAvailable`.

- If the `Vault(LoanBroker(LoanBrokerID).VaultID).Asset` is an `MPT`:

  - Decrease the `MPToken.MPTAmount` by `CoverAvailable` of the `LoanBroker` _pseudo-account_ `MPToken` object for the `Vault.Asset`.
  - Increase the `MPToken.MPTAmount` by `CoverAvailable` of the submitter `MPToken` object for the `Vault.Asset`.

- Delete the `LoanBroker` _pseudo-account_ `AccountRoot` object.
- Delete the `LoanBroker` ledger object.

##### 3.1.2.3 Invariants

- If `LoanBroker.OwnerCount = 0` the `DirectoryNode` will have at most one node (the root), which will only hold entries for `RippleState` or `MPToken` objects.

[**Return to Index**](#index)

#### 3.1.3 `LoanBrokerCoverDeposit`

The transaction deposits First Loss Capital into the `LoanBroker` object.

| Field Name        |     Required?      | JSON Type | Internal Type | Default Value | Description                                       |
| ----------------- | :----------------: | :-------: | :-----------: | :-----------: | :------------------------------------------------ |
| `TransactionType` | :heavy_check_mark: | `string`  |   `UINT16`    |     `76`      | The transaction type.                             |
| `LoanBrokerID`    | :heavy_check_mark: | `string`  |   `HASH256`   |     `N/A`     | The Loan Broker ID to deposit First-Loss Capital. |
| `Amount`          | :heavy_check_mark: | `object`  |   `AMOUNT`    |       0       | The Fist-Loss Capital amount to deposit.          |

##### 3.1.3.1 Failure Conditions

- `LoanBroker` object with the specified `LoanBrokerID` does not exist on the ledger.
- The submitter `AccountRoot.Account != LoanBroker(LoanBrokerID).Owner`.

- If the `Vault(LoanBroker(LoanBrokerID).VaultID).Asset` is `XRP`:

  - `AccountRoot(LoanBroker.Owner).Balance - Reserve(AccountRoot(LoanBroker.Owner).OwnerCount) < Amount` (LoanBroker does not have sufficient funds to deposit the First Loss Capital).

- If the `Vault(LoanBroker(LoanBrokerID).VaultID).Asset` is an `IOU`:

  - The `RippleState` object between the submitter account and the `Issuer` of the asset has the `lsfLowFreeze` or `lsfHighFreeze` flag set.
  - The `RippleState` between the `LoanBroker.Account` and the `Issuer` has the `lsfLowDeepFreeze` or `lsfHighDeepFreeze` flag set. (The Loan Broker _pseudo-account_ is frozen).
  - The `AccountRoot` object of the `Issuer` has the `lsfGlobalFreeze` flag set.
  - The `RippleState` object `Balance` < `Amount` (Depositor has insufficient funds).

- If the `Vault(LoanBroker(LoanBrokerID).VaultID).Asset` is an `MPT`:

  - The `MPToken` object for the `Vault(LoanBroker(LoanBrokerID).VaultID).Asset` of the submitter `AccountRoot`:
    - Has `lsfMPTLocked` flag set.
    - `MPTAmount` < `Amount`.
  - The `MPToken` object for the `Vault(LoanBroker(LoanBrokerID).VaultID).Asset` of the `LoanBroker.Account` `AccountRoot` has `lsfMPTLocked` flag set. (The Loan Broker _pseudo-account_ is locked).
  - The `MPTokenIssuance` object of the `Vault(LoanBroker(LoanBrokerID).VaultID).Asset` has the `lsfMPTLocked` flag set.
  - The `MPTokenIssuance` object of the `Vault(LoanBroker(LoanBrokerID).VaultID).Asset` does not have the `lsfMPTCanTransfer` flag set (the asset is not transferable).

##### 3.1.3.2 State Changes

- If the `Vault(LoanBroker(LoanBrokerID).VaultID).Asset` is `XRP`:

  - Increase the `Balance` field of `LoanBroker` _pseudo-account_ `AccountRoot` by `Amount`.
  - Decrease the `Balance` field of the submitter `AccountRoot` by `Amount`.

- If the `Vault(LoanBroker(LoanBrokerID).VaultID).Asset` is an `IOU`:

  - Increase the `RippleState` balance between the `LoanBroker` _pseudo-account_ `AccountRoot` and the `Issuer` `AccountRoot` by `Amount`.
  - Decrease the `RippleState` balance between the submitter `AccountRoot` and the `Issuer` `AccountRoot` by `Amount`.

- If the `Vault(LoanBroker(LoanBrokerID).VaultID).Asset` is an `MPT`:

  - Increase the `MPToken.MPTAmount` by `Amount` of the `LoanBroker` _pseudo-account_ `MPToken` object for the `Vault.Asset`.
  - Decrease the `MPToken.MPTAmount` by `Amount` of the submitter `MPToken` object for the `Vault.Asset`.

- Increase `LoanBroker.CoverAvailable` by `Amount`.

##### 3.1.3.3 Invariants

**TBD**

[**Return to Index**](#index)

#### 3.1.4 `LoanBrokerCoverWithdraw`

The `LoanBrokerCoverWithdraw` transaction withdraws the First-Loss Capital from the `LoanBroker`.

| Field Name        |     Required?      | JSON Type | Internal Type | Default Value | Description                                                             |
| ----------------- | :----------------: | :-------: | :-----------: | :-----------: | :---------------------------------------------------------------------- |
| `TransactionType` | :heavy_check_mark: | `string`  |   `UINT16`    |     `77`      | Transaction type.                                                       |
| `LoanBrokerID`    | :heavy_check_mark: | `string`  |   `HASH256`   |     `N/A`     | The Loan Broker ID from which to withdraw First-Loss Capital.           |
| `Amount`          | :heavy_check_mark: | `object`  |   `AMOUNT`    |       0       | The Fist-Loss Capital amount to withdraw.                               |
| `Destination`     |                    | `string`  |  `AccountID`  |     Empty     | An account to receive the assets. It must be able to receive the asset. |

##### 3.1.4.1 Failure conditions

- `LoanBroker` object with the specified `LoanBrokerID` does not exist on the ledger.
- The submitter `AccountRoot.Account != LoanBroker(LoanBrokerID).Owner`.

- The `Destination` account is specified and it does not have permission to receive the asset.

- If the `Vault(LoanBroker(LoanBrokerID).VaultID).Asset` is an `IOU`:

  - If the `Destination` field is not specified:

    - The `RippleState` object between the submitter account and the `Issuer` of the asset has the `lsfLowDeepFreeze` or `lsfHighDeepFreeze` flag set.

  - If the `Destination` field is specified:

    - The `RippleState` object between the `Destination` account and the `Issuer` of the asset does not exist.
    - If `Destination` is not the `Issuer` and the `RippleState` object between the `Destination` account and the `Issuer` of the asset has the `lsfLowFreeze` or `lsfHighFreeze` flag set.

  - The `AccountRoot` object of the `Issuer` has the `lsfGlobalFreeze` flag set and `Destination` is not the `Issuer` of the asset.
  - The `RippleState` between the `LoanBroker.Account` and the `Issuer` has the `lsfLowFreeze` or `lsfHighFreeze` flag set. (The Loan Broker _pseudo-account_ is frozen).

- If the `Vault(LoanBroker(LoanBrokerID).VaultID).Asset` is an `MPT`:

  - If the `Destination` field is not specified:

    - The `MPToken` object for the `Vault(LoanBroker(LoanBrokerID).VaultID).Asset` of the submitter `AccountRoot` has `lsfMPTLocked` flag set.

  - If the `Destination` field specified:

    - The `MPToken` object for the `Vault(LoanBroker(LoanBrokerID).VaultID).Asset` of the `Destination` `AccountRoot` does not exist.
    - If the `Destination` is not the `Issuer` and the `MPToken` object for the `Vault(LoanBroker(LoanBrokerID).VaultID).Asset` of the `Destination` `AccountRoot` has `lsfMPTLocked` flag set.

  - The `MPTokenIssuance` object of the `Vault(LoanBroker(LoanBrokerID).VaultID).Asset` has the `lsfMPTLocked` flag set and `Destination` is not the `Issuer` of the asset.
  - The `MPTokenIssuance` object of the `Vault(LoanBroker(LoanBrokerID).VaultID).Asset` does not have the `lsfMPTCanTransfer` flag set and `Destination` is not the `Issuer` of the asset (the asset is not transferable).
  - The `MPToken` object for the `Vault(LoanBroker(LoanBrokerID).VaultID).Asset` of the `LoanBroker.Account` `AccountRoot` has `lsfMPTLocked` flag set. (The Loan Broker _pseudo-account_ is locked).

- The `LoanBroker.CoverAvailable` < `Amount`.

- `LoanBroker.CoverAvailable - Amount` < `LoanBroker.DebtTotal * LoanBroker.CoverRateMinimum`

##### 3.1.4.2 State Changes

- If the `Vault(LoanBroker(LoanBrokerID).VaultID).Asset` is `XRP`:

  - Decrease the `Balance` field of `LoanBroker` _pseudo-account_ `AccountRoot` by `Amount`.
  - If `Destination` field is not specified:

    - Increase the `Balance` field of the submitter `AccountRoot` by `Amount`.

  - If `Destination` field is specified:
    - Increase the `Balance` field of the `Destination` `AccountRoot` by `Amount`.

- If the `Vault(LoanBroker(LoanBrokerID).VaultID).Asset` is an `IOU`:

  - Decrease the `RippleState` balance between the `LoanBroker` _pseudo-account_ `AccountRoot` and the `Issuer` `AccountRoot` by `Amount`.
  - If `Destination` field is not specified:

    - Increase the `RippleState` balance between the submitter `AccountRoot` and the `Issuer` `AccountRoot` by `Amount`.

  - If `Destination` field is specified:
    - Increase the `RippleState` balance between the `Destination` `AccountRoot` and the `Issuer` `AccountRoot` by `Amount`.

- If the `Vault(LoanBroker(LoanBrokerID).VaultID).Asset` is an `MPT`:

  - Decrease the `MPToken.MPTAmount` by `Amount` of the `LoanBroker` _pseudo-account_ `MPToken` object for the `Vault.Asset`.
  - If `Destination` field is not specified:

    - Increase the `MPToken.MPTAmount` by `Amount` of the submitter `MPToken` object for the `Vault.Asset`.

  - If `Destination` field is specified:
    - Increase the `MPToken.MPTAmount` by `Amount` of the `Destination` `MPToken` object for the `Vault.Asset`.

- Decrease `LoanBroker.CoverAvailable` by `Amount`.

##### 3.1.4.3 Invariants

**TBD**

[**Return to Index**](#index)

#### 3.1.5 `LoanBrokerCoverClawback`

The `LoanBrokerCoverClawback` transaction claws back the First-Loss Capital from the `LoanBroker`. The transaction can only be submitted by the Issuer of the Loan asset. Furthermore, the transaction can only clawback funds up to the minimum cover required for the current loans.

| Field Name        |     Required?      | JSON Type | Internal Type | Default Value | Description                                                                                                                                                                                            |
| ----------------- | :----------------: | :-------: | :-----------: | :-----------: | :----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `TransactionType` | :heavy_check_mark: | `string`  |   `UINT16`    |     `78`      | Transaction type.                                                                                                                                                                                      |
| `LoanBrokerID`    |                    | `string`  |   `HASH256`   |     `N/A`     | The Loan Broker ID from which to withdraw First-Loss Capital. Must be provided if the `Amount` is an MPT, or `Amount` is an IOU and `issuer` is specified as the `Account` submitting the transaction. |
| `Amount`          |                    | `object`  |   `AMOUNT`    |       0       | The First-Loss Capital amount to clawback. If the amount is `0` or not provided, clawback funds up to `LoanBroker.DebtTotal * LoanBroker.CoverRateMinimum`.                                            |

##### 3.1.5.1 Failure conditions

- Neither `LoanBrokerID` nor `Amount` are specified.
- `Amount` is specified and `Amount < 0`
- `Amount` specifies an XRP amount.
- If the `LoanBrokerID` is specified, the `LoanBroker` object with that ID does not exist on the ledger.
- If the `LoanBrokerID` is not specified, and can not be determined from `Amount`.
  - `Amount` specifies an MPT.
  - `Amount` specifies an IOU, and the `issuer` value is _not_ a pseudo-account with `Account(Amount.issuer).LoanBrokerID` set. If it is set, treat `LoanBrokerID` as `Account(Amount.issuer).LoanBrokerID` for the rest of this transaction.
- If both the `LoanBrokerID` and `Amount` are specified, and:

  - The `Amount.issuer` value does not match the submitter `Account` of the transaction or `LoanBroker(LoanBrokerID).Account` (the pseudo-account of the LoanBroker).
  - The `Vault(LoanBroker(LoanBrokerID).VaultID).Asset` is not the same asset type as `Amount`, allowing for an IOU `Amount.issuer` to specify `LoanBroker(LoanBrokerID).Account` instead of `Vault(LoanBroker(LoanBrokerID).VaultID).Asset`.

- If the `Vault(LoanBroker(LoanBrokerID).VaultID).Asset` is `XRP`.

- If `Vault(LoanBroker(LoanBrokerID).VaultID).Asset` is an `IOU` and:

  - The Issuer account is not the submitter of the transaction.
  - `Amount.issuer` value is not one of
    - The submitter of the transaction
    - `LoanBroker(LoanBrokerID).Account`
  - If the `AccountRoot(Issuer)` object does not have lsfAllowTrustLineClawback flag set (the asset does not support clawback).
  - If the `AccountRoot(Issuer)` has the lsfNoFreeze flag set (the asset cannot be frozen).

- If `Vault(LoanBroker(LoanBrokerID).VaultID).Asset` is an `MPT` and:

  - MPTokenIssuance.Issuer is not the submitter of the transaction.
  - If the `LoanBrokerID` is not specified.
  - MPTokenIssuance.lsfMPTCanClawback flag is not set (the asset does not support clawback).
  - If the MPTokenIssuance.lsfMPTCanLock flag is NOT set (the asset cannot be locked).

- `LoanBroker.CoverAvailable` <= `LoanBroker.DebtTotal * LoanBroker.CoverRateMinimum`

##### 3.1.5.2 State Changes

- If `Amount` is 0 or unset, set `Amount` to `LoanBroker.CoverAvailable - LoanBroker.DebtTotal * LoanBroker.CoverRateMinimum`.
- Otherwise set `Amount` to `min(Amount,`LoanBroker.CoverAvailable - LoanBroker.DebtTotal \* LoanBroker.CoverRateMinimum`).

- If the `Vault(LoanBroker(LoanBrokerID).VaultID).Asset` is an `IOU`:

  - Decrease the `RippleState` balance between the `LoanBroker` _pseudo-account_ `AccountRoot` and the `Issuer` `AccountRoot` by `Amount`.

- If the `Vault(LoanBroker(LoanBrokerID).VaultID).Asset` is an `MPT`:

  - Decrease the `MPToken.MPTAmount` by `Amount` of the `LoanBroker` _pseudo-account_ `MPToken` object for the `Vault.Asset`.

- Decrease `LoanBroker.CoverAvailable` by `Amount`.

[**Return to Index**](#index)

### 3.2. `Loan` Transactions

In this section we specify transactions associated with the `Loan` ledger entry.

#### 3.2.1 `LoanSet` Transaction

The transaction creates a new `Loan` object.

| Field Name                |     Required?      | JSON Type | Internal Type | Default Value | Description                                                                                                                                   |
| ------------------------- | :----------------: | :-------: | :-----------: | :-----------: | :-------------------------------------------------------------------------------------------------------------------------------------------- |
| `TransactionType`         | :heavy_check_mark: | `string`  |   `UINT16`    |     `80`      | The transaction type.                                                                                                                         |
| `LoanBrokerID`            | :heavy_check_mark: | `string`  |   `HASH256`   |     `N/A`     | The Loan Broker ID associated with the loan.                                                                                                  |
| `Flags`                   |                    | `string`  |   `UINT32`    |       0       | Specifies the flags for the Loan.                                                                                                             |
| `Data`                    |                    | `string`  |    `BLOB`     |     None      | Arbitrary metadata in hex format. The field is limited to 256 bytes.                                                                          |
| `Counterparty`            |                    | `string`  |  `AccountID`  |     `N/A`     | The address of the counterparty of the Loan.                                                                                                  |
| `CounterpartySignature`   | :heavy_check_mark: | `string`  |  `STObject`   |     `N/A`     | The signature of the counterparty over the transaction.                                                                                       |
| `LoanOriginationFee`      |                    | `number`  |   `NUMBER`    |       0       | A nominal funds amount paid to the `LoanBroker.Owner` when the Loan is created.                                                               |
| `LoanServiceFee`          |                    | `number`  |   `NUMBER`    |       0       | A nominal amount paid to the `LoanBroker.Owner` with every Loan payment.                                                                      |
| `LatePaymentFee`          |                    | `number`  |   `NUMBER`    |       0       | A nominal funds amount paid to the `LoanBroker.Owner` when a payment is late.                                                                 |
| `ClosePaymentFee`         |                    | `number`  |   `NUMBER`    |       0       | A nominal funds amount paid to the `LoanBroker.Owner` when an early full repayment is made.                                                   |
| `OverpaymentFee`          |                    | `number`  |   `UINT32`    |       0       | A fee charged on overpayments in 1/10th basis points. Valid values are between 0 and 100000 inclusive. (0 - 100%)                             |
| `InterestRate`            |                    | `number`  |   `UINT32`    |       0       | Annualized interest rate of the Loan in in 1/10th basis points. Valid values are between 0 and 100000 inclusive. (0 - 100%)                   |
| `LateInterestRate`        |                    | `number`  |   `UINT32`    |       0       | A premium added to the interest rate for late payments in in 1/10th basis points. Valid values are between 0 and 100000 inclusive. (0 - 100%) |
| `CloseInterestRate`       |                    | `number`  |   `UINT32`    |       0       | A Fee Rate charged for repaying the Loan early in 1/10th basis points. Valid values are between 0 and 100000 inclusive. (0 - 100%)            |
| `OverpaymentInterestRate` |                    | `number`  |   `UINT32`    |       0       | An interest rate charged on overpayments in 1/10th basis points. Valid values are between 0 and 100000 inclusive. (0 - 100%)                  |
| `PrincipalRequested`      | :heavy_check_mark: | `number`  |   `NUMBER`    |     `N/A`     | The principal amount requested by the Borrower.                                                                                               |
| `PaymentTotal`            |                    | `number`  |   `UINT32`    |       1       | The total number of payments to be made against the Loan.                                                                                     |
| `PaymentInterval`         |                    | `number`  |   `UINT32`    |      60       | Number of seconds between Loan payments.                                                                                                      |
| `GracePeriod`             |                    | `number`  |   `UINT32`    |      60       | The number of seconds after the Loan's Payment Due Date can be Defaulted.                                                                     |

##### 3.2.1.1 `Flags`

| Flag Name           |  Flag Value  | Description                                    |
| ------------------- | :----------: | :--------------------------------------------- |
| `tfLoanOverpayment` | `0x00010000` | Indicates that the loan supports overpayments. |

##### 3.2.1.2 `CounterpartySignature`

An inner object that contains the signature of the Lender over the transaction. The fields contained in this object are:

| Field Name      | Required? | JSON Type | Internal Type | Default Value | Description                                                                                                        |
| --------------- | :-------: | :-------: | :-----------: | :-----------: | :----------------------------------------------------------------------------------------------------------------- |
| `SigningPubKey` |           | `string`  |   `STBlob`    |     `N/A`     | The Public Key to be used to verify the validity of the signature.                                                 |
| `TxnSignature`  |           | `string`  |   `STBlob`    |     `N/A`     | The signature of over all signing fields.                                                                          |
| `Signers`       |           |  `list`   |   `STArray`   |     `N/A`     | An array of transaction signatures from the `Counterparty` signers to indicate their approval of this transaction. |

The final transaction must include exactly one of

1. The `SigningPubKey` and `TxnSignature` fields, or
2. The `Signers` field and, optionally, an empty `SigningPubKey`.

The total fee for the transaction will be increased due to the extra signatures that need to be processed, similar to the additional fees for multisigning. The minimum fee will be $(|signatures| + 1) \times base_fee$ where $|signatures| == max(1, |tx.CounterPartySignature.Signers|)$

The total fee calculation for signatures will now be $(1 + |tx.Signers| + |signatures|) \times base_fee$. In other words, even without a `tx.Signers` list, the minimum fee will be $2 \times base_fee$.

This field is not a signing field (it will not be included in transaction signatures, though the `TxnSignature` or `Signers` field will be included in the stored transaction).

##### 3.2.1.3 Multi-Signing

The `LoanSet` transaction is a mutual agreement between the `Borrower` and the `LoanBroke.Owner` to create a Loan. Therefore, the `LoanSet` transaction must be signed by both parties.

Either of the parties (Borrower or Loan Issuer) may initiate the transaction. The user flow is as follows:

- `Borrower` initiates the transaction:

  1. The `Borrower` creates the transaction from their account, setting the pre-agreed terms.

     - Optionally, the `Borrower` may set the `Counterparty` to `LoanBroker.Owner`. In case the `Counterparty` field is not set, it is assumed to be the `LoanBroker.Owner`.

  2. The `Borrower` signs the transaction setting the `SigningPubKey`, `TxnSignature`, `Signers`, `Account`, `Fee`, `Sequence` fields.
  3. The `Borrower` sends the transaction to the `Loan Issuer`.
  4. The `Loan Issuer` verifies the loan-terms are as agreed upon and verifies the signature of the `Borrower`.
  5. The `Loan Issuer` signs the transaction, filling the `CounterpartySignature` field.
  6. The `Loan Issuer` submits the transaction.

- `Loan Issuer` initiates the transaction:

  1. The `Loan Issuer` creates the transaction from their account setting the pre-agreed terms.

     - The `Loan Issuer` must set the `Counterparty` to the `Borrower` account ID.

  2. The `Loan Issuer` signs the transaction setting the `SigningPubKey`, `TxnSignature`, `Signers`, `Account`, `Fee`, `Sequence` fields.
  3. The `Loan Issuer` sends the transaction to the `Borrower`.
  4. The `Borrower` verifies the loan-terms are as agreed upon and verifies the signature of the `Loan Issuer`.
  5. The `Borrower` signs the transaction, filling the `CounterpartySignature` field.
  6. The `Borrower` submits the transaction.

##### 3.2.1.4 Fees

The account specified in the `Account` field pays the transaction fee.

##### 3.2.1.5 Failure Conditions

- `LoanBroker` object with the specified `LoanBrokerID` does not exist on the ledger.
- If neither the `Account` or the `Counterparty` field are the `LoanBroker.Owner`.
- If the `Counterparty` field is not specified and the `CounterpartySignature` is not from the `LoanBroker.Owner`.
- If the `Counterparty.TxnSignature` is invalid.

- If the `Vault(LoanBroker(LoanBrokerID).VaultID).Asset` is an `IOU`:

  - The `AccountRoot` object of the `Issuer` has the `lsfGlobalFreeze` flag set.
  - The `AccountRoot` object of the `Issuer` has the `lsfRequireAuth` flag set, and the `RippleState` object between the `Issuer` and the Borrower does not have the `lsfLowAuth` and `lsfHighAuth` flags set.

  - The `RippleState` between the `LoanBroker.Account` and the `Issuer` has the `lsfLowDeepFreeze` or `lsfHighDeepFreeze` flag set. (The Loan Broker _pseudo-account_ is frozen).
  - The `RippleState` between the `Vault(LoanBroker(LoanBrokerID).VaultID).Account` and the `Issuer` has the `lsfLowFreeze` or `lsfHighFreeze` flag set. (The Vault _pseudo-account_ is frozen).

  - The `RippleState` object between the Borrower account and the `Issuer` of the asset has the `lsfLowDeepFreeze` or `lsfHighDeepFreeze` flag set (The borrower cannot send and receive funds).
  - The `RippleState` object between the Borrower account and the `Issuer` of the asset has the `lsfLowFreeze` or `lsfHighFreeze` flag set (The borrower cannot send funds).

- If the `Vault(LoanBroker(LoanBrokerID).VaultID).Asset` is an `MPT`:

  - The `MPTokenIssuance` object of the `Vault(LoanBroker(LoanBrokerID).VaultID).Asset` has the `lsfMPTLocked` flag set.
  - The `MPTokenIssuance` object of the `Vault(LoanBroker(LoanBrokerID).VaultID).Asset` has the `lsfMPTRequireAuth` flag set and the `MPToken`of the Borrower `AccountRoot` does not have the `lsfMPTAuthorized` flag set.

  - The `MPToken` object for the `Vault(LoanBroker(LoanBrokerID).VaultID).Asset` of the `LoanBroker.Account` `AccountRoot` has `lsfMPTLocked` flag set. (The Loan Broker _pseudo-account_ is locked).
  - The `MPToken` object for the `Vault(LoanBroker(LoanBrokerID).VaultID).Asset` of the `Vault(LoanBroker(LoanBrokerID).VaultID).Account` `AccountRoot` has `lsfMPTLocked` flag set. (The Vault _pseudo-account_ is locked).

  - The `MPToken` object for the `Vault(LoanBroker(LoanBrokerID).VaultID).Asset` of the Borrower `AccountRoot` has `lsfMPTLocked` flag set (The Borrower MPToken is locked).

- Either of the `tfLoanDefault`, `tfLoanImpair` or `tfLoanUnimpair` flags are set.

- The `Borrower` `AccountRoot` object does not exist.

- `PaymentInterval` is less than `60` seconds.
- `GracePeriod` is greater than the `PaymentInterval`.

- The combination of `PrincipalRequested`, `InterestRate`, `PaymentTotal`, and `PaymentInterval` results in a total interest amount that is zero or negative due to precision limitations. This can happen if the loan term is too short or the principal is too small for any interest to accrue to a representable value.
- The loan terms result in a periodic payment that is too small to cover the interest accrued in the first period, leaving no amount to pay down the principal. This prevents the loan from being amortized correctly.
- The calculated periodic payment is so small that it rounds down to zero when adjusted for the asset's precision (e.g., drops for XRP, or the smallest unit of an IOU/MPT).
- The rounding of the periodic payment (due to asset precision) is significant enough that the total number of payments required to settle the loan is less than the specified `PaymentTotal`.

- Insufficient assets in the Vault:

  - `Vault(LoanBroker(LoanBrokerID).VaultID).AssetsAvailable` < `Loan.PrincipalRequested`.

- Exceeds maximum Debt of the LoanBroker:

  - `LoanBroker(LoanBrokerID).DebtMaximum` < `LoanBroker(LoanBrokerID).DebtTotal + Loan.PrincipalRequested + (TotalInterestOutstanding() - (TotalInterestOutstanding() x LoanBroker.ManagementFeeRate)`

- Insufficient First-Loss Capital:

  - `LoanBroker(LoanBrokerID).CoverAvailable` < `(LoanBroker(LoanBrokerID).DebtTotal + Loan.PrincipalRequested + (TotalInterestOutstanding() - (TotalInterestOutstanding() x LoanBroker.ManagementFeeRate)) x LoanBroker(LoanBrokerID).CoverRateMinimum`

##### 3.2.1.6 State Changes

- Create the `Loan` object.
- Increment `AccountRoot(Borrower).OwnerCount` by `1`.
- Increment `LoanBroker.LoanSequence` by `1`.

- If the `Vault(LoanBroker(LoanBrokerID).VaultID).Asset` is `XRP`:

  - Decrease the `Balance` field of `Vault` _pseudo-account_ `AccountRoot` by `Loan.PrincipalRequested`.
  - Increase the `Balance` field of `Borrower` `AccountRoot` by `Loan.PrincipalRequested - Loan.LoanOriginationFee`.
  - Increase the `Balance` field of `LoanBroker.Owner` `AccountRoot` by `Loan.LoanOriginationFee`.

- If the `Vault(LoanBroker(LoanBrokerID).VaultID).Asset` is an `IOU`:

  - Create a `RippleState` object between the `Issuer` and the `Borrower` if one does not exist.

  - Decrease the `RippleState` balance between the `Vault` _pseudo-account_ `AccountRoot` and the `Issuer` `AccountRoot` by `Loan.PrincipalRequested`.
  - Increase the `RippleState` balance between the `Borrower` `AccountRoot` and the `Issuer` `AccountRoot` by `Loan.PrincipalRequested - Loan.LoanOriginationFee`.

  - If the `RippleState` object between the `LoanBroker.Owner` `AccountRoot` and the `Issuer` of the asset has the `lsfLowDeepFreeze` or `lsfHighDeepFreeze` flag set (The LoanBroker cannot receive funds):

    - Increase the `RippleState` balance between the `LoanBroker` _pseudo-account_ `AccountRoot` and the `Issuer` `AccountRoot` by `Loan.LoanOriginationFee` (the loan origination fee was added to First Loss Capital, and thus transfered to the `LoanBroker` _pseudo-account_).
    - Increase `LoanBroker.CoverAvailable` by `Loan.LoanOriginationFee`.

  - Otherwise:

    - Increase the `RippleState` balance between the `LoanBroker.Owner` `AccountRoot` and the `Issuer` `AccountRoot` by `Loan.LoanOriginationFee`.

- If the `Vault(LoanBroker(LoanBrokerID).VaultID).Asset` is an `MPT`:

  - Create an `MPToken` object for the `Borrower` if one does not exist.

  - Decrease the `MPToken.MPTAmount` of the `Vault` _pseudo-account_ `MPToken` object for the `Vault.Asset` by `Loan.PrincipalRequested`.
  - Increase the `MPToken.MPTAmount` of the `Borrower` `MPToken` object for the `Vault.Asset` by `Loan.PrincipalRequested - Loan.LoanOriginationFee`.

  - The `MPToken` object for the `Vault(LoanBroker(LoanBrokerID).VaultID).Asset` of the `LoanBroker.Owner` `AccountRoot` has `lsfMPTLocked` flag set (The LoanBroker cannot receive funds):

    - Increase the `MPToken.MPTAmount` by `Loan.LoanOriginationFee` of the `LoanBroker` _pseudo-account_ `MPToken` object for the `Vault.Asset` (the loan origination fee was added to First Loss Capital, and thus transfered to the `LoanBroker` _pseudo-account_).
    - Increase `LoanBroker.CoverAvailable` by `Loan.LoanOriginationFee`.

  - Otherwise:
    - Increase the `MPToken.MPTAmount` of the `LoanBroker.Owner` `MPToken` object for the `Vault.Asset` by `Loan.LoanOriginationFee`

- `Vault(LoanBroker(LoanBrokerID).VaultID)` object state changes:

  - Decrease Asset Available in the Vault:

    - `Vault.AssetsAvailable -= Loan.PrincipalRequested`.

  - Increase the Total Value of the Vault:
    - `Vault.AssetsTotal += TotalInterestOutstanding() - (TotalInterestOutstanding() x LoanBroker.ManagementFeeRate)`.

- `LoanBroker(LoanBrokerID)` object changes:

  - `LoanBroker.DebtTotal += Loan.PrincipalRequested + (TotalInterestOutstanding() - (TotalInterestOutstanding() x LoanBroker.ManagementFeeRate)`
  - `LoanBroker.OwnerCount += 1`

  - Add `LoanID` to `DirectoryNode.Indexes` of the `LoanBroker` _pseudo-account_ `AccountRoot`.
  - Add `LoanID` to `DirectoryNode.Indexes` of the `Borrower` `AccountRoot`.

##### 3.2.1.7 Invariants

**TBD**

[**Return to Index**](#index)

#### 3.2.2 `LoanDelete` Transaction

The transaction deletes an existing `Loan` object.

| Field Name        |     Required?      | JSON Type | Internal Type | Default Value | Description                              |
| ----------------- | :----------------: | :-------: | :-----------: | :-----------: | :--------------------------------------- |
| `TransactionType` | :heavy_check_mark: | `string`  |   `UINT16`    |     `81`      | The transaction type.                    |
| `LoanID`          | :heavy_check_mark: | `string`  |   `HASH256`   |     `N/A`     | The ID of the Loan object to be deleted. |

##### 3.2.2.1 Failure Conditions

- A `Loan` object with the specified `LoanID` does not exist on the ledger.
- The Account submitting the `LoanDelete` is not the `LoanBroker.Owner` or the `Loan.Borrower`.
- The Loan is active:
  - `Loan.PaymentRemaining > 0`
  - `Loan.TotalValueOutstanding > 0`

##### 3.2.2.2 State Changes

- Delete the `Loan` object.

- Remove `LoanID` from `DirectoryNode.Indexes` of the `LoanBroker` _pseudo-account_ `AccountRoot`.
- If `LoanBroker.OwnerCount = 0`

  - Delete the `LoanBroker` _pseudo-account_ `DirectoryNode`.

- Remove `LoanID` from `DirectoryNode.Indexes` of the `Borrower` `AccountRoot`.

- `LoanBroker.OwnerCount -= 1`

##### 3.2.2.3 Invariants

- If `Loan.PaymentRemaining = 0` then `Loan.PrincipalOutstanding = 0 && Loan.TotalValueOutstanding = 0`

[**Return to Index**](#index)

#### 3.2.3 `LoanManage` Transaction

| Field Name        |     Required?      | JSON Type | Internal Type | Default Value | Description                              |
| ----------------- | :----------------: | :-------: | :-----------: | :-----------: | :--------------------------------------- |
| `TransactionType` | :heavy_check_mark: | `string`  |   `UINT16`    |     `82`      | The transaction type.                    |
| `LoanID`          | :heavy_check_mark: | `string`  |   `HASH256`   |     `N/A`     | The ID of the Loan object to be updated. |
| `Flags`           |                    | `string`  |   `UINT32`    |       0       | Specifies the flags for the Loan.        |

##### 3.2.3.1 `Flags`

`LoanManage` transaction `Flags` are mutually exclusive.

| Flag Name        |  Flag Value  | Description                                    |
| ---------------- | :----------: | :--------------------------------------------- |
| `tfLoanDefault`  | `0x00010000` | Indicates that the Loan should be defaulted.   |
| `tfLoanImpair`   | `0x00020000` | Indicates that the Loan should be impaired.    |
| `tfLoanUnimpair` | `0x00040000` | Indicates that the Loan should be un-impaired. |

##### 3.2.3.1 Failure Conditions

- A `Loan` object with the specified `LoanID` does not exist on the ledger.
- The `Account` submitting the transaction is not the `LoanBroker.Owner`.
- The `lsfLoanDefault` flag is set on the Loan object. Once a Loan is defaulted, it cannot be modified.

- If `Loan(LoanID).Flags == lsfLoanImpaired` AND `tfLoanImpair` flag is provided (impairing an already impaired loan).
- If `Loan(LoanID).Flags == 0` AND `tfLoanUnimpair` flag is provided (clearing impairment for an unimpaired loan).

- `Loan.PaymentRemaining == 0`.

- The `tfLoanDefault` flag is specified and:
  - `LastClosedLedger.CloseTime` < `Loan.NextPaymentDueDate + Loan.GracePeriod`.

##### 3.2.3.2 State Changes

- If the `tfLoanDefault` flag is specified:

  - Calculate the amount of the Default that First-Loss Capital covers:

    - The default Amount equals the outstanding principal and interest, excluding any funds unclaimed by the Borrower.
      - `DefaultAmount = (Loan.PrincipalOutstanding + Loan.InterestOutstanding)`.
    - Apply the First-Loss Capital to the Default Amount
      - `DefaultCovered = min((LoanBroker(Loan.LoanBrokerID).DebtTotal x LoanBroker(Loan.LoanBrokerID).CoverRateMinimum)  x LoanBroker(Loan.LoanBrokerID).CoverRateLiquidation, DefaultAmount)`
    - `DefaultAmount -= DefaultCovered`
    - `ReturnToVault = DefaultCovered`

  - Update the `Vault` object:

    - Decrease the Total Value of the Vault:
      - `Vault(LoanBroker(LoanBrokerID).VaultID).AssetsTotal -= DefaultAmount`.
    - Increase the Asset Available of the Vault by liquidated First-Loss Capital and any unclaimed funds amount:
      - `Vault(LoanBroker(LoanBrokerID).VaultID).AssetsAvailable += ReturnToVault`.
    - If `Loan.lsfLoanImpaired` flag is set:
      - `Vault(LoanBroker(LoanBrokerID).VaultID).LossUnrealized -= Loan.PrincipalOutstanding + TotalInterestOutstanding()` (Please refer to section [**3.2.4.1.5 Total Value Calculation**](#3242-total-loan-value-calculation), which outlines how to calculate total interest outstanding).

  - Update the `LoanBroker` object:

    - Decrease the Debt of the LoanBroker:
      - `LoanBroker(LoanBrokerID).DebtTotal -= Loan.PrincipalOutstanding + Loan.InterestOutstanding`
    - Decrease the First-Loss Capital Cover Available:
      - `LoanBroker(LoanBrokerID).CoverAvailable -= DefaultCovered`

  - Update the `Loan` object:

    - `Loan(LoanID).Flags |= lsfLoanDefault`
    - `Loan(LoanID).PaymentRemaining = 0`
    - `Loan(LoanID).PrincipalOutstanding = 0`

  - Move the First-Loss Capital from the `LoanBroker` _pseudo-account_ to the `Vault` _pseudo-account_:

    - If the `Vault(LoanBroker(Loan(LoanID).LoanBrokerID).VaultID).Asset` is `XRP`:

      - Decrease the `Balance` field of `LoanBroker` _pseudo-account_ `AccountRoot` by `ReturnToVault`.
      - Increase the `Balance` field of `Vault` _pseudo-account_ `AccountRoot` by `ReturnToVault`.

    - If the `Vault(LoanBroker(Loan(LoanID).LoanBrokerID).VaultID).Asset` is an `IOU`:

      - Decrease the `RippleState` balance between the `LoanBroker` _pseudo-account_ `AccountRoot` and the `Issuer` `AccountRoot` by `ReturnToVault`.
      - Increase the `RippleState` balance between the `Vault` _pseudo-account_ `AccountRoot` and the `Issuer` `AccountRoot` by `ReturnToVault`.

    - If the `Vault(LoanBroker(Loan(LoanID).LoanBrokerID).VaultID).Asset` is an `MPT`:

      - Decrease the `MPToken.MPTAmount` of the `LoanBroker` _pseudo-account_ `MPToken` object for the `Vault.Asset` by `ReturnToVault`.
      - Increase the `MPToken.MPTAmount` of the `Vault` _pseudo-account_ `MPToken` object for the `Vault.Asset` by `ReturnToVault`.

  - If `tfLoanImpair` flag is specified:

    - Update the `Vault` object (set "paper loss"):

      - `Vault(LoanBroker(LoanBrokerID).VaultID).LossUnrealized += Loan.PrincipalOutstanding + TotalInterestOutstanding()` (Please refer to section [**3.2.4.1.5 Total Value Calculation**](#3242-total-loan-value-calculation), which outlines how to calculate total interest outstanding)

    - Update the `Loan` object:
    - `Loan(LoanID).Flags |= lsfLoanImpaired`
      - If `currentTime < Loan(LoanID).NextPaymentDueDate` (if the loan payment is not yet late):
        - `Loan(LoanID).NextPaymentDueDate = currentTime` (move the next payment due date to now)

  - If the `tfLoanUnimpair` flag is specified:

    - Update the `Vault` object (clear "paper loss"):
    - `Vault(LoanBroker(LoanBrokerID).VaultID).LossUnrealized -= Loan.PrincipalOutstanding + TotalInterestOutstanding()` (Please refer to section [**3.2.4.1.5 Total Value Calculation**](#3242-total-loan-value-calculation), which outlines how to calculate total interest outstanding)

    - Update the `Loan` object:

      - Unset `lsfLoanImpaired` flag
      - `CandidateDueDate = max(Loan.PreviousPaymentDueDate, Loan.StartDate) + Loan.PaymentInterval`

      - If `CandidateDueDate > currentTime` (the loan was unimpaired within the payment interval):

        - `Loan(LoanID).NextPaymentDueDate = CandidateDueDate`

      - If `CandidateDueDate <= currentTime` (the loan was unimpaired after the original payment due date):
        - `Loan(LoanID).NextPaymentDueDate = currentTime + Loan(LoanID).PaymentInterval`

##### 3.2.3.3 Invariants

**TBD**

[**Return to Index**](#index)

#### 3.2.4 `LoanPay` Transaction

The Borrower submits a `LoanPay` transaction to make a Payment on the Loan.

| Field Name        |     Required?      | JSON Type | Internal Type | Default Value | Description                               |
| ----------------- | :----------------: | :-------: | :-----------: | :-----------: | :---------------------------------------- |
| `TransactionType` | :heavy_check_mark: | `string`  |   `UINT16`    |     `83`      | The transaction type.                     |
| `LoanID`          | :heavy_check_mark: | `string`  |   `HASH256`   |     `N/A`     | The ID of the Loan object to be paid to.  |
| `Amount`          | :heavy_check_mark: | `number`  |   `AMOUNT`    |     `N/A`     | The amount of funds to pay.               |
| `Flags`           |                    | `string`  |   `UINT32`    |       0       | Specifies the flags for the Loan Payment. |

##### 3.2.4.1 `Flags`

| Flag Name           |  Flag Value  | Description                                                                  |
| ------------------- | :----------: | :--------------------------------------------------------------------------- |
| `tfLoanOverpayment` | `0x00010000` | Indicates that remaining payment amount should be treated as an overpayment. |
| `tfLoanFullPayment` | `0x00020000` | Indicates that the borrower is making a full early repayment.                |

##### 3.2.4.2 Payment Processing

A `LoanPay` transaction is processed according to a defined workflow that evaluates the payment's timing, amount, and any specified flags. This determines how the funds are applied to the loan's principal, interest, and associated fees.

**Source of Truth**: The formulas in this section describe the financial theory for a conceptual understanding. The [pseudo-code](#3244-transaction-pseudo-code) describes the required implementation logic, which includes critical adjustments for rounding. **Implementations must follow the pseudo-code.**

**Payment Rounding**: The `Loan.PeriodicPayment` field stores a high-precision value. However, payments must be made in the discrete, indivisible units of the loan's asset (e.g., XRP drops, whole MPTs, or the smallest unit of an IOU). Therefore, the borrower is expected to make a periodic payment that is rounded **up** to the asset's scale.

For example:

- If a loan is denominated in an asset that only supports whole numbers (like an MPT) and the calculated `Loan.PeriodicPayment` is `10.12345`, the borrower is expected to pay `11`.
- If a loan is denominated in a USD IOU with two decimal places of precision and the `Loan.PeriodicPayment` is `25.54321`, the borrower is expected to pay `25.55`.

This rounded-up value, plus any applicable service fees, constitutes the minimum payment for a single period.

Each payment consists of three components:

- **Principal**: The portion that reduces the outstanding loan principle.
- **Interest**: The portion that covers the cost of borrowing for the period.
- **Fees**: The portion that covers any applicable `serviceFee`, `managementFee`, `latePaymentFee`, or other charges.

The system follows these steps to process a payment:

1.  **Timing Verification**: The transaction is first classified as either **On-time** or **Late** by comparing the ledger's close time to the `Loan.NextPaymentDueDate`.

2.  **Minimum Amount Validation**: The payment is checked against the minimum amount required for its timing classification. If the amount is insufficient, the transaction is rejected.

    - **Late Minimum**: `periodicPayment + serviceFee + latePaymentFee + lateInterest`
    - **On-time Minimum**: `periodicPayment + serviceFee`

3.  **Scenario Handling**: Based on the timing and transaction flags, the system proceeds with one of the following paths:

    - **A) Late Payment Processing**: If the payment is late, it must be for the exact amount calculated by the [late payment formula](#32422-late-payment).

      - **Constraint**: Overpayments are not permitted on late payments. Any amount paid beyond the exact total due will be ignored.

    - **B) On-Time Payment Processing**: If the payment is on-time, the system checks for special repayment scenarios before handling standard periodic payments.
      - **i. Full Early Repayment**: If the `tfLoanFullPayment` flag is set and the amount is sufficient to cover the [full payment formula](#32424-early-full-repayment), the loan is closed.
        - **Constraint**: This option is not available if only one payment remains on the loan.
      - **ii. Sequential Periodic Payments**: If it is not a full repayment, the system applies the funds to as many complete periodic payment cycles as possible. A single cycle consists of the `periodicPayment` plus the `serviceFee`.
      - **iii. Overpayment Application**: After all possible full periodic cycles are paid, any remaining amount is treated as an overpayment and applied to the principal.
        - **Constraint**: This step only occurs for on-time payments and requires two flags to be set: `lsfLoanOverpayment` on the `Loan` object and `tfLoanOverpayment` on the `LoanPay` transaction. If these conditions are not met, the excess amount is ignored.

**Note on Excess Funds**: In scenarios where funds are "ignored" (e.g., an overpayment on a late payment, or on a loan that does not permit overpayments), the transaction succeeds, the borrower is only charged the expected due amount, but not the excess.

**The `valueChange` Concept**

The `valueChange` is a critical accounting mechanism that represents the change in the _total future interest_ the vault expects to earn from the loan. It is triggered by events that alter the original amortization schedule.

- **Late Payment**: Adds new penalty interest, so `valueChange` is positive.
- **Overpayment**: Overpayment reduces principal, and thus the future interest, thus `valueChange` is negative.
- **Early Full Payment**: The `valueChange` for an early repayment can be either positive or negative, depending on the size of the early full payment configuration.

This `valueChange` is always split between the Vault (as a change in its net interest) and the Loan Broker (as a change in the `managementFee`).

###### 3.2.4.2.1 Regular Payment

For a standard, on-time payment, the total amount due from the borrower is the sum of the calculated periodic payment and applicable service fee.

$$
totalDue = periodicPayment + loanServiceFee
$$

The `periodicPayment` is calculated using the standard amortization formula, which ensures a constant payment amount over the life of the loan. This payment covers both the interest accrued for the period and a portion of the principal.

$$
periodicPayment = principalOutstanding \times \frac{periodicRate \times (1 + periodicRate)^{PaymentRemaining}}{(1 + periodicRate)^{PaymentRemaining} - 1}
$$

The `periodicRate` is the interest rate applied for each payment interval, derived from the annual rate:

$$
periodicRate = \frac{interestRate \times paymentInterval}{365 \times 24 \times 60 \times 60}
$$

From the calculated `periodicPayment`, the specific `interest` and `principal` portions for that period can be derived as follows:

$$
interest = principalOutstanding \times periodicRate
$$

$$
principal = periodicPayment - interest
$$

**Special Handling for the Final Payment**

When only a single payment remains (`PaymentRemaining = 1`), the standard amortization formula is overridden. Instead, the final `periodicPayment` is set to the exact `TotalValueOutstanding` (which is the sum of the remaining `principalOutstanding`, `interestOutstanding`, and `managementFeeOutstanding`).

This crucial adjustment prevents "residual dust", small leftover amounts caused by the cumulative effect of rounding individual payments over the loan's term (e.g., truncating fractions for XRP drops or MPTs). Without this override, the final formula-calculated payment might not perfectly match the remaining balance, making it impossible to fully clear the debt.

Formally:

```
If PaymentRemaining > 1:
  periodicPayment = result from amortization formula (rounded per asset rules)
If PaymentRemaining = 1:
  periodicPayment = TotalValueOutstanding (the sum of all remaining balances)
```

Example (integer-only MPT):

- Initial TotalValueOutstanding = 11 MPT
- PaymentTotal = 10
- Amortization produces periodicPayment = 1.1 MPT
- Asset supports only whole units ⇒ each scheduled payment is truncated to 1 MPT
  Progress:
  After 9 payments: Paid = 9 MPT, Remaining TotalValueOutstanding = 2 MPT
  If we applied the formula again for the 10th payment:
  periodicPayment (unrounded) = 1.1 MPT → truncated to 1 MPT
  Remaining after payment = 1 MPT (cannot be repaid; no payments left)
  Adjustment:
  Because PaymentRemaining = 1, set periodicPayment = TotalValueOutstanding = 2 MPT
  Final payment = 2 MPT clears the loan exactly (PrincipalOutstanding = 0, TotalValueOutstanding = 0).

Therefore, implementations must detect the single remaining payment case and substitute the outstanding value to guarantee full extinguishment of the debt.

###### 3.2.4.2.2 Late Payment

When a Borrower makes a payment after `NextPaymentDueDate`, they must pay the standard `periodicPayment` plus a nominal `latePaymentFee` and additional penalty interest (`latePaymentInterest`) for the overdue period.

The total amount due is calculated as:

$$
totalDue = periodicPayment + loanServiceFee + latePaymentFee + latePaymentInterest
$$

The penalty interest is calculated based on the number of seconds the payment is overdue:

$$
secondsOverdue = lastLedgerCloseTime - Loan.NextPaymentDueDate
$$

$$
latePeriodicRate = \frac{lateInterestRate \times secondsOverdue}{365 \times 24 \times 60 \times 60}
$$

$$
latePaymentInterest_{gross} = principalOutstanding \times latePeriodicRate
$$

A portion of this gross late interest is allocated to the Loan Broker as a management fee. The remaining net interest increases the total value of the loan.

$$
managementFee_{late} = latePaymentInterest_{gross} \times managementFeeRate
$$

The change in the total loan value is equent to the late payment interest, excluding any fees.

$$
valueChange = latePaymentInterest_{gross} - managementFee_{late}
$$

This `valueChange` represents the net increase in the loan's value, which must be reflected in `Vault.AssetsTotal`. However, this value change is not reflected in `Loan.TotalValueOutstanding` and `LoanBroker.DebtTotal` fields. It is an unanticipated increase in value. Note that `valueChange > 0` for late payments.

###### 3.2.4.2.3 Loan Overpayment

An overpayment occurs when an on-time payment exceeds the amount required for one or more periodic payments. The excess amount is used to pay down the principal early, which reduces the total future interest owed. This process involves two key calculations: charging fees on the overpayment itself and re-amortizing the loan.

**1. Processing the Overpayment Amount**

First, fees and interest are calculated on the `overpaymentAmount` (the funds remaining after all full periodic payments are settled).

$$
overpaymentInterest_{gross} = overpaymentAmount \times overpaymentInterestRate
$$

A management fee is taken from this interest:

$$
managementFee_{overpayment} = overpaymentInterest_{gross} \times managementFeeRate
$$

$$
overpaymentInterest_{net} = overpaymentInterest_{gross} - managementFee_{overpayment}
$$

A percentage fee may also be charged:

$$
overpaymentFee = overpaymentAmount \times overpaymentFee
$$

The portion of the overpayment that will be applied directly to the principal is:

$$
principalPortion = overpaymentAmount - overpaymentInterest_{net} - managementFee_{overpayment} - overpaymentFee
$$

**2. Re-Amortizing the Loan and Calculating `valueChange`**

Applying the `principalPortion` to the loan reduces the `PrincipalOutstanding`, which in turn changes the amortization schedule and the total interest that will be paid over the remainder of the loan's term. This change in total future interest is the primary `valueChange`.

The system performs the following logical steps (as detailed in the `do_overpayment` pseudo-code):

1.  The `principalPortion` is subtracted from the current `PrincipalOutstanding` to get a `newPrincipalOutstanding`.
2.  A `newPeriodicPayment` is calculated using the standard amortization formula based on the `newPrincipalOutstanding` and the `paymentsRemaining`.
3.  A `newTotalValueOutstanding` is calculated based on the `newPeriodicPayment` and `paymentsRemaining`.
4.  The `valueChange` is the difference between the old and new total future interest, adjusted for any existing rounding discrepancies to ensure numerical stability.

The total change in the loan's value from an overpayment is the sum of the net interest charged on the overpayment and the value change from re-amortization.

$$
valueChange = overpaymentInterest_{net} + valueChange_{re-amortization}
$$

Note, that an overpayment typically decreases the overall value of the loan, as the reduction in future interest from re-amortization outweighs interest charged on the overpayment amount itself. However, it is possible for an overpayment to increase the value, if the overpayment interest portion is greater than the value change caused by re-amortization.

###### 3.2.4.2.4 Early Full Repayment

A Borrower can close a Loan early by submitting the total amount needed to do so. This amount is the sum of the outstanding principal, any interest accrued since the last payment, a prepayment penalty, and a fixed prepayment fee.

$$
totalDue = principalOutstanding + accruedInterest + prepaymentPenalty + ClosePaymentFee
$$

The interest accrued since the last payment is calculated pro-rata:

$$
secondsSinceLastPayment = lastLedgerCloseTime - max(Loan.PreviousPaymentDueDate, Loan.startDate)
$$

$$
accruedInterest = principalOutstanding \times periodicRate \times \frac{secondsSinceLastPayment}{paymentInterval}
$$

The Lender may also charge a prepayment penalty, calculated as a percentage of the outstanding principal:

$$
prepaymentPenalty = principalOutstanding \times closeInterestRate
$$

Because the borrower is not paying all of the originally scheduled future interest, the total value of the loan asset changes. This `valueChange` is the difference between the interest and penalties the vault _will receive_ versus the interest it _expected_ to receive.

The total interest and penalties collected are `accruedInterest + prepaymentPenalty`. The total interest that was expected is `interestOutstanding`.

Therefore, the change in the loan's value is calculated as:

$$
valueChange = (accruedInterest + prepaymentPenalty) - interestOutstanding
$$

The `valueChange` for an early repayment can be either positive or negative, depending on the size of the `prepaymentPenalty` relative to the `interestOutstanding`.

- If `(accruedInterest + prepaymentPenalty) < interestOutstanding`, the `valueChange` will be negative, reflecting a decrease in the total value of the loan asset because the vault receives less interest than originally scheduled.
- If `(accruedInterest + prepaymentPenalty) > interestOutstanding`, the `valueChange` will be positive. This can occur if the lender imposes a significant prepayment penalty that exceeds the forgiven future interest.

This change in value must be reflected in `Vault.AssetsTotal` and `LoanBroker.DebtTotal`, accounting for the corresponding change in the `managementFee`.

##### 3.2.4.3 Conceptual Loan Value

The value of a loan is based on the present value of its future payments. Conceptually, this can be understood through the standard amortization formulas.

The `periodicPayment` is the constant amount required to pay off the `principalOutstanding` over the `PaymentRemaining` intervals at the given `periodicRate`.

$$
periodicPayment = principalOutstanding \times \frac{periodicRate \times (1 + periodicRate)^{PaymentRemaining}}{(1 + periodicRate)^{PaymentRemaining} - 1}
$$

From this, the theoretical `totalValueOutstanding` is the sum of all remaining payments.

$$
\text{Theoretical } totalValueOutstanding = periodicPayment \times PaymentRemaining
$$

And the theoretical `totalInterestOutstanding` is the portion of that total value that is not principal.

$$
\text{Theoretical } totalInterestOutstanding = \text{Theoretical } totalValueOutstanding - principalOutstanding
$$

And the theoretical `managementFeeOutstanding` is the portion of the interest that is due to the loan broker.

$$
\text{Theoretical } managementFeeOutstanding = \text{Theoretical } totalInterestOutstanding \times managementFeeRate
$$

The true `totalInterestOutstanding` is then updated to reflect this.

$$
\text{Theoretical } totalInterestOutstanding = \text{Theoretical } totalInterestOutstanding - managementFeeOutstanding
$$

**Important Note**: These formulas describe the theoretical financial model. The actual values stored on the `Loan` ledger object (`TotalValueOutstanding`, `PrincipalOutstanding`, `ManagementFeeOutstanding`) are continuously adjusted during payment processing to account for asset-specific rounding rules. Therefore, implementations **must not** rely on these formulas to derive the live state of a loan. The stored ledger fields are the single source of truth.

##### 3.2.4.4 Transaction Pseudo-code

The following is the pseudo-code for handling a Loan payment transaction.

```
function get_periodic_rate() -> (periodicRate):
  # Convert annual rate to rate per payment interval
  let SECONDS_PER_YEAR = 365 * 24 * 60 * 60
  let periodicRate = (loan.interestRate * loan.paymentInterval) / SECONDS_PER_YEAR

  return periodicRate

function compute_periodic_payment(principalOutstanding) -> (periodicPayment):
    let periodicRate = get_periodic_rate()
    let raisedRate = (1 + periodicRate)^loan.paymentsRemaining

    return principalOutstanding * (periodicRate * raisedRate) / (raisedRate - 1)

function compute_late_payment_interest(currentTime) -> (lateInterest, managementFee):
    let secondsOverdue = lastLedgerCloseTime() - loan.nextPaymentDueDate
    let latePeriodicRate = (loan.lateInterestRate * secondsOverdue) / (365 * 24 * 60 * 60)
    let latePaymentInterest = loan.principalOutstanding * latePeriodicRate

    let fee = (latePaymentInterest * loan.loanbroker.managementFeeRate).round(loan.loanScale, DOWN)

    return (latePaymentInterest - fee, fee)

function compute_full_payment(currentTime) -> (principal, interest, fee):
    let truePrincipalOutstanding = principal_outstanding_from_periodic()
    let periodicRate = get_periodic_rate()
    let secondsSinceLastPayment = lastLedgerCloseTime() - max(loan.PreviousPaymentDueDate, loan.startDate)

    let accruedInterest = truePrincipalOutstanding * periodicRate * (secondsSinceLastPayment / loan.paymentInterval)
    let prepaymentPenalty = truePrincipalOutstanding * loan.closeInterestRate
    let interest = (accruedInterest + prepaymentPenalty).round(loan.loanScale, DOWN)

    let managementFee = (interest * loan.loanbroker.managementFeeRate).round(loan.loanScale, DOWN)
    interest = interest - managementFee

    return (loan.principalOutstanding, interest, managementFee)

function principal_outstanding_from_periodic() -> (principalOutstanding):
    # Given the outstanding principal we can calculate the periodic payment
    # Equally, given the periodic payment we can calculate the principal outstanding at the current time
    let periodicRate = get_periodic_rate()

    # If the loan is zero-interest, the outstanding principal is simply periodicPayment * paymentsRemaining
    if periodicRate == 0:
        return loan.periodicPayment * loan.paymentsRemaining

    let raisedRate = (1 + periodicRate)^loan.paymentsRemaining
    let factor = (periodicRate * raisedRate) / (raisedRate - 1)

    return loan.periodicPayment / factor

# This function calculates what the loan state should be given the periodic payment and remaining payments
function calculate_true_loan_state(paymentsRemaining) -> (principalOutstanding, interestOutstanding, managementFeeOutstanding):
    let truePrincipalOutstanding = principal_outstanding_from_periodic()
    let trueInterestOutstanding = (loan.periodicPayment * paymentsRemaining) - truePrincipalOutstanding
    let trueManagementFeeOutstanding = (trueInterestOutstanding * loan.loanbroker.managementFeeRate)

    # Exclude the management fee from the interest rate
    trueInterestOutstanding = trueInterestOutstanding - trueManagementFeeOutstanding

    return (truePrincipalOutstanding, trueInterestOutstanding, trueManagementFeeOutstanding)

function calculate_payment_breakdown(principalOutstanding) -> (principal, interest):
    let periodicRate = get_periodic_rate()

    if periodicRate == 0:
        return (principalOutstanding / paymentsRemaining, 0)

    let interest = principalOutstanding * periodicRate
    let principal = loan.periodicPayment - interest

    return (principal, interest)

function calculate_rounded_principal_payment(truePrincipalOutstanding) -> (principal):
    let roundedPrincipalPayment = (loan.principalOutstanding - truePrincipalOutstanding).round(loan.loanScale, DOWN)

    # Ensure we do not have a negative principal payment
    roundedPrincipalPayment = max(0, roundedPrincipalPayment)

    # Ensure we do not exceed the outstanding principal amount
    return min(roundedPrincipalPayment, loan.principalOutstanding)


function calculate_rounded_interest_breakdown(roundedPrincipalPayment, trueInterestOutstanding, trueManagementFeeOutstanding, roundedPeriodicPayment) -> (interest, fee):
    if loan.interestRate == 0:
        return (0, 0)

    let loanInterestOutstanding = loan.totalValueOutstanding - loan.principalOutstanding - loan.managementFeeOutstanding

    # The interest due is the difference between our current value, and the future value after the next payment
    let roundedInterestPayment = (loanInterestOutstanding - trueInterestOutstanding).round(loan.loanScale, HALF_EVEN)

    # Since diffInterest can be negative, ensure the interest payment itself is not negative.
    roundedInterestPayment = max(0, roundedInterestPayment)

    # This caps the interest at the remaining portion of the periodic payment.
    roundedInterestPayment = min(roundedPeriodicPayment - roundedPrincipalPayment, roundedInterestPayment)

    # The Management Fee is the difference between our current value, and the future value after the next payment
    let roundedManagementFee = (loan.managementFeeOutstanding - trueManagementFeeOutstanding).round(loan.loanScale, HALF_EVEN)

    # Since diffManagementFee can be negative, ensure the final fee payment is not negative.
    roundedManagementFee = max(0, roundedManagementFee)

    # Ensure the fee payment does not exceed the total outstanding management fee.
    roundedManagementFee = min(roundedManagementFee, loan.managementFeeOutstanding)

    return (roundedInterestPayment, roundedManagementFee)

function compute_payment_due(roundedPeriodicPayment) -> (principal, interest, managementFee):
    # If this is the final payment, simply settle any outstanding amounts
    if loan.paymentsRemaining == 1:
        let outstandingInterest = loan.totalValueOutstanding - loan.principalOutstanding - loan.managementFeeOutstanding
        return (loan.principalOutstanding, outstandingInterest, loan.managementFeeOutstanding)

    # Determine the true state of the loan, excluding rounding errors. This calculation gives where the loan state is meant to be
    let (
      truePrincipalOutstanding,
      trueInterestOutstanding,
      trueManagementFeeOutstanding
    ) = calculate_true_loan_state(loan.paymentsRemaining - 1)

    # Given the true state we can calculate the rounded principal that accounts for deviation from the true state
    let roundedPrincipalPayment = calculate_rounded_principal_payment(truePrincipalOutstanding)

    let (roundedInterestPayment, roundedManagementFee) = calculate_rounded_interest_breakdown(
        roundedPrincipalPayment,
        trueInterestOutstanding,
        trueManagementFeeOutstanding,
        roundedPeriodicPayment
    )

    return (roundedPrincipalPayment, roundedInterestPayment, roundedManagementFee)

function do_overpayment(amount) -> (valueChange):
    # Calculate the ideal, unrounded ("true") state of the loan before the overpayment.
    let (truePrincipalOutstanding, trueInterestOutstanding, trueManagementFeeOutstanding) = calculate_true_loan_state(loan.paymetsRemaining)

    # For an accurate overpayment, we must preserve historical rounding errors.
    # These 'diff' variables capture the difference between the on-ledger rounded state and the ideal 'true' state.
    let diffTotal = loan.totalValueOutstanding - (truePrincipalOutstanding + trueInterestOutstanding + trueManagementFeeOutstanding)
    let diffPrincipal = loan.principalOutstanding - truePrincipalOutstanding
    let diffManagementFee = loan.managementFeeOutstanding - trueManagementFeeOutstanding

    # Re-amortize the loan based on the new, lower principal after the overpayment is applied.
    let newTruePrincipalOutstanding = truePrincipalOutstanding - amount
    let newTruePeriodicPayment = compute_periodic_payment(newTruePrincipalOutstanding)

    # From the new periodic payment, calculate the new ideal total value, interest, and fee.
    let newTrueTotalValueOutstanding = (newTruePeriodicPayment * loan.paymentsRemaining).round(loan.loanScale, HALF_EVEN)
    let newTrueInterestOutstanding = newTrueTotalValueOutstanding - newTruePrincipalOutstanding
    let newTrueManagementFeeOutstanding = (newTrueInterestOutstanding * loan.loanbroker.managementFeeRate).round(loan.loanScale, HALF_EVEN)
    newTrueInterestOutstanding = newTrueInterestOutstanding - newTrueManagementFeeOutstanding

    # Set the new on-ledger total value, adjusting for the historical rounding errors to maintain consistency.
    let newRoundedTotalValueOutstanding = (newTrueTotalValueOutstanding + diffTotal).round(loan.loanScale, DOWN)

    # The old total value, for comparison, is what the on-ledger value would have been if we just subtracted the overpayment amount.
    let oldRoundedTotalValueOutstanding = loan.totalValueOutstanding - amount

    # The change in the loan's value is the difference between the new re-amortized value and the old value.
    # This formula correctly calculates the change in future interest while preserving the existing rounding difference (diffTotal),
    # which is present in both newRoundedTotalValueOutstanding and implicitly in oldRoundedTotalValueOutstanding.
    let roundedValueChange = newRoundedTotalValueOutstanding - oldRoundedTotalValueOutstanding

    # Update loan state by applying the preserved rounding differences to the new 'true' state.
    loan.totalValueOutstanding = newTrueTotalValueOutstanding + diffTotal
    loan.principalOutstanding = (newTruePrincipalOutstanding + diffPrincipal).round(loan.loanScale, DOWN)
    loan.managementFeeOutstanding = (newTrueManagementFeeOutstanding + diffManagementFee).round(loan.loanScale, DOWN)

    return roundedValueChange

function make_payment(amount, currentTime) -> (principalPaid, interestPaid, valueChange, feePaid):
    if loan.paymentsRemaining == 0 || loan.principalOutstanding == 0:
        return "loan complete" error

    # ======== STEP 1: Process Late Payment ======== #
    if loan.nextPaymentDueDate < currentTime:
        let (principal, interest, managementFee) = compute_payment_due(amount)
        let (lateInterest, lateManagementFee) = compute_late_payment_interest(currentTime)

        # totalDue for late payment is the sum of expected periodic payment, and the accrued late interest and charges
        let totalDue = (principal + interest + managementFee + loan.serviceFee) + (lateInterest + lateManagementFee + loan.latePaymentFee)

        # Insufficient funds
        if amount < totalDue:
            return "insufficient amount paid" error

        loan.paymentsRemaining = loan.paymentsRemaining - 1
        loan.PreviousPaymentDueDate = loan.nextPaymentDueDate
        loan.nextPaymentDueDate = loan.nextPaymentDueDate + loan.paymentInterval
        loan.principalOutstanding = loan.principalOutstanding - principal
        loan.managementFeeOutstanding = loan.managementFeeOutstanding - managementFee
        
        # we do not adjust the total value by late interst or late managementFee as these were not included in the initial total value
        loan.totalValueOutstanding = loan.totalValueOutstanding - (principal + interest + managementFee)

        return (
            principal,                                                    # A late payment does not affect the principal portion due
            interest + lateInterest,                                      # A late payment incorporates both periodic interest and the late interest
            lateInterest,                                                 # The value of the loan increases by the lateInterest amount
            totalManagementFee + loan.serviceFee + loan.latePaymentFee    # The total fee paid for a loan payment
        )
    # ======== STEP 2: Process Full Payment ======== #
    let (fullPrincipal, fullInterest, fullManagementFee) = compute_full_payment(currentTime)
    let fullPaymentAmount = fullPrincipal + fullInterest + fullManagementFee + loan.closePaymentFee

    # If the payment is equal or higher than full payment amount and there is more than one payment remaining, make a full payment
    if is_set(tfLoanFullPayment) && amount >= fullPaymentAmount && loan.paymentsRemaining > 1:
        let totalInterestOutstanding = loan.totalValueOutstanding - loan.principalOutstanding - loan.managementFeeOutstanding
        let loanValueChange = fullInterest - totalInterestOutstanding

        loan.paymentsRemaining = 0
        loan.principalOutstanding = 0
        loan.managementFeeOutstanding = 0
        loan.totalValueOutstanding = 0

        return (
            fullPrincipal,                      # Full payment repays the entire outstanding principal
            fullInterest,                       # Full payment repays any accrued interest since the last payment and additional full payment interest
            loanValueChange,                    # A full payment changes the total value of the loan
            fullManagementFee + loan.closePaymentFee   # An early payment pays a specific closePaymentFee
        )
    # ======== STEP 3: Process Regular Payment(s) ======== #
    # Handle regular payments and overpayments
    let totalPaid = 0
    let (totalPrincipalPaid, totalInterestPaid, totalFeePaid) = (0, 0, 0)

    while totalPaid < amount && loan.paymentsRemaining > 0:
        # calculate the payment principal, interest and fee
        let (principal, interest, managementFee) = compute_payment_due(loan.periodicPayment.round(loan.loanScale, UP))
        let paymentAmount = principal + interest + managementFee + loan.serviceFee

        # Check if we have enough funds for this payment
        if totalPaid + paymentAmount > amount:
            break

        # Apply the payment
        loan.totalValueOutstanding = loan.totalValueOutstanding - (principal + interest + managementFee)
        loan.principalOutstanding = loan.principalOutstanding - principal
        loan.managementFeeOutstanding = loan.managementFeeOutstanding - managementFee
        loan.paymentsRemaining = loan.paymentsRemaining - 1

        loan.nextPaymentDueDate = loan.nextPaymentDueDate + loan.paymentInterval
        loan.PreviousPaymentDueDate = loan.nextPaymentDueDate - loan.paymentInterval

        totalPaid = totalPaid + paymentAmount
        totalPrincipalPaid = totalPrincipalPaid + principal
        totalInterestPaid = totalInterestPaid + interest
        totalFeePaid = totalFeePaid + managementFee + loan.serviceFee

    # ======== STEP 4: Process Overpayment ======== #
    let loanValueChange = 0
    # Handle overpayment if there are remaining payments, the loan supports overpayments, and there are funds remaining
    if loan.paymentsRemaining > 0 && is_set(loan.lsfLoanOverpayment) && is_set(tfLoanOverpayment) && totalPaid < amount:
        let overpaymentAmount = min(loan.principalOutstanding, amount - totalPaid)
    
        # ======== STEP 4.1: Determine Interest and Fee on Overpayment ======== #
  
        # overpayment amount is charged an interest that goes to the vault
        let overpaymentInterest = overpaymentAmount * loan.overpaymentInterestRate
        # and a management fee that goes to the broker charged on the interest
        
        let overpaymentManagementFee = overpaymentInterest * loan.loanbroker.managementFeeRate        
        overpaymentInterest = overpaymentInterest - overpaymentManagementFee

        # there is a second overpayment fee that goes to the broker
        let overpaymentFee = overpaymentAmount * loan.overpaymentFee

        # the value of the loan will increase by the overpayment interest portion
        loanValueChange = loanValueChange + overpaymentInterest
        let overpaymentPrincipal = overpaymentAmount - overpaymentInterest - overpaymentManagementFee - overpaymentFee

        # ======== STEP 4.2: Determine how the overpayment changes the value of the Loan ======== #
        # if the overpayment was not eaten by fees and interest, then apply it
        if overpaymentPrincipal > 0:
            # the valueChange is the decrease in the total interest caused by overpaying the principal
            let valueChange = do_overpayment(overpaymentPrincipal)

            # ajust the total loanValueChange
            loanValueChange = loanValueChange + valueChange

            totalPaid = totalPaid + overpaymentAmount
            totalPrincipalPaid = totalPrincipalPaid + overpaymentPrincipal
            totalInterestPaid = totalInterestPaid + overpaymentInterest
            totalFeePaid = totalFeePaid + overpaymentManagementFee + overpaymentFee

    return (
        totalPrincipalPaid,     # This will include the periodicPayment principal and any overpayment
        totalInterestPaid,      # This will include the periodicPayment interest and any overpayment
        loanValueChange,        # Value change in loan total value by overpayment
        totalFeePaid            # The total fee
    )
```

##### 3.2.4.5 Failure Conditions

- A `Loan` object with the specified `LoanID` does not exist on the ledger.
- The `Account` submitting the transaction is not the `Loan.Borrower`.
- The `Amount` field is invalid or specifies a negative value.

- The loan is already fully paid (`Loan.PaymentRemaining` is `0` or `Loan.TotalValueOutstanding` is `0`).
- The `tfLoanOverpayment` flag is set on the transaction, but the `lsfLoanOverpayment` flag is not set on the `Loan` object.
- The `tfLoanFullPayment` flag is set, but only one payment remains on the loan (`Loan.PaymentRemaining` is `1`).
- Both `tfLoanOverpayment` and `tfLoanFullPayment` transaction flags are specified.

- If the payment is late (`LastLedgerCloseTime > Loan.NextPaymentDueDate`):

  - The `Amount` is less than the calculated `totalDue` for a late payment, which is `periodicPayment + loanServiceFee + latePaymentFee + latePaymentInterest`.

- If the payment is on-time (`LastLedgerCloseTime <= Loan.NextPaymentDueDate`):

  - The `Amount` is less than the calculated `totalDue` for a periodic payment, which is `periodicPayment + loanServiceFee`.

- If the `tfLoanFullPayment` flag is specified:

  - The `Amount` is less than the calculated `totalDue` for a full early payment, which is `principalOutstanding + accruedInterest + prepaymentPenalty + ClosePaymentFee`.

- If the `Vault(LoanBroker(Loan(LoanID).LoanBrokerID).VaultID).Asset` is `XRP`:

  - The `Balance` of the `AccountRoot` object of the Borrower is less than `totalDue`.

- If the `Vault(LoanBroker(Loan(LoanID).LoanBrokerID).VaultID).Asset` is an `IOU`:

  - The `RippleState` object between the submitter account and the `Issuer` of the asset has the `lsfLowFreeze` or `lsfHighFreeze` flag set.
  - The `RippleState` between the `LoanBroker.Account` and the `Issuer` has the `lsfLowDeepFreeze` or `lsfHighDeepFreeze` flag set. (The Loan Broker _pseudo-account_ is frozen).
  - The `RippleState` between the `Vault(LoanBroker(Loan.LoanBrokerID).VaultID).Account` and the `Issuer` has the `lsfLowFreeze` or `lsfHighFreeze` flag set. (The Vault _pseudo-account_ is frozen).
  - The `AccountRoot` object of the `Issuer` has the `lsfGlobalFreeze` flag set.
  - The `RippleState` object `Balance` < `totalDue` (Borrower has insufficient funds).

- If the `Vault(LoanBroker(Loan(LoanID).LoanBrokerID).VaultID).Asset` is an `MPT`:

  - The `MPToken` object for the `Vault(LoanBroker(Loan(LoanID).LoanBrokerID).VaultID).Asset` of the submitter `AccountRoot` has
    - `lsfMPTLocked` flag set.
    - `MPTAmount` < `totalDue` (inssuficient funds).
  - The `MPToken` object for the `Vault(LoanBroker(Loan(LoanID).LoanBrokerID).VaultID).Asset` of the `LoanBroker.Account` `AccountRoot` has `lsfMPTLocked` flag set. (The Loan Broker _pseudo-account_ is locked).
  - The `MPToken` object for the `Vault(LoanBroker(Loan(LoanID).LoanBrokerID).VaultID).Asset` of the `Vault(LoanBroker(Loan(LoanID).LoanBrokerID).VaultID).Account` `AccountRoot` has `lsfMPTLocked` flag set. (The Vault _pseudo-account_ is locked).
  - The `MPTokenIssuance` object of the `Vault(LoanBroker(Loan(LoanID).LoanBrokerID).VaultID).Asset` has the `lsfMPTLocked` flag set.

##### 3.2.4.6 State Changes

Upon successful validation, the `LoanPay` transaction is processed according to the logic defined in the [Transaction Pseudo-code](#3244-transaction-pseudo-code). This process yields four key results: `principalPaid`, `interestPaid`, `feePaid`, and `valueChange`. These values are then used to apply the following state changes.

**1. High-Level Accounting**

First, the system determines the final destination of all funds.

1.  **Determine Fee Destination**: All collected fees are directed to one of two places:

    - **If First-Loss Capital is sufficient** (`LoanBroker.CoverAvailable >= LoanBroker.DebtTotal * LoanBroker.CoverRateMinimum`): The fees are paid to the `LoanBroker.Owner`.
    - **If First-Loss Capital is insufficient**: The fees are added to the first-loss pool to cover the deficit.

2.  **Define Final Fund Flows**:
    - `totalPaidByBorrower = principalPaid + interestPaid + feePaid`
    - `totalToVault = principalPaid + interestPaid`
    - `totalToBroker` = The total fee amount, directed to either the `LoanBroker.Owner` or the `LoanBroker` pseudo-account's cover pool.

**2. `Loan` Object State Changes**

The `Loan` object is updated to reflect the payment
.

- If the loan was impaired (`lsfLoanImpaired` flag was set), the flag is cleared.

- **For a Full Repayment**:

  - All outstanding balance fields (`PrincipalOutstanding`, `TotalValueOutstanding`, `ManagementFeeOutstanding`) are set to `0`.
  - `PaymentRemaining` is set to `0`.

- **For Other Payments**:

  - `PrincipalOutstanding` is decreased by the `principal` portion of each periodic payment settled.
  - `ManagementFeeOutstanding` is decreased by the `managementFee` portion of each periodic payment settled.
  - `TotalValueOutstanding` is decreased by the sum of the `principal`, `interest`, and `managementFee` portions of each periodic payment settled.
  - If an overpayment occurred, `TotalValueOutstanding` is further adjusted by the `valueChange` resulting from re-amortization. It is **not** adjusted for `valueChange` from late payment interest, as that interest was not part of the original loan value.
  - `PaymentRemaining` is decreased by `1` for each full periodic payment cycle covered.
  - `NextPaymentDueDate` is advanced by `Loan.PaymentInterval` for each periodic payment cycle covered.
  - `PreviousPaymentDueDate` is updated.
  - If an overpayment was made:
    - `PeriodicPayment` is recalculated based on the new outstanding principal and remaining term.

**3. `LoanBroker` and `Vault` Object State Changes**

The `LoanBroker` and `Vault` objects are updated to reflect the new accounting state. The `valueChange`—representing the net change in the loan's total future interest—is applied to both the `LoanBroker` and the `Vault`, but with an important distinction for late payments.

- **`LoanBroker` Updates**:

  - `LoanBroker.DebtTotal` is decreased by `totalToVault` (the principal and interest paid back).
  - If the payment resulted in a `valueChange` from an overpayment or early full repayment, `LoanBroker.DebtTotal` is adjusted by that `valueChange`. It is **not** adjusted for `valueChange` from late payment interest, as this represents a penalty paid directly to the vault, not an alteration of the original debt schedule.
    - `LoanBroker.DebtToal + valueChange`
  - If fees were directed to the cover pool, `LoanBroker.CoverAvailable` increases by `totalToBroker`.

- **`Vault` Updates**:
  - `Vault.AssetsAvailable` increases by `totalToVault`.
  - `Vault.AssetsTotal` is always adjusted by the total `valueChange`, reflecting the net change in the vault's expected future earnings from the loan.

**4. Low-Level Asset Transfers**

Finally, the actual asset transfers are executed on the ledger.

- The borrower's balance is **decreased** by `totalPaidByBorrower`.
- The `Vault` pseudo-account's balance is **increased** by `totalToVault`.
- The `LoanBroker.Owner`'s balance OR the `LoanBroker` pseudo-account's balance is **increawsed** by `totalToBroker`, depending on the fee destination.

These transfers are performed according to the asset type:

- **If the asset is XRP**:
  - The `Balance` of the borrower's `AccountRoot` is decreased.
  - The `Balance` of the `Vault` pseudo-account's `AccountRoot` is increased.
  - The `Balance` of the destination account for fees (`LoanBroker.Owner` or `LoanBroker` pseudo-account) is increased.
- **If the asset is an IOU**:
  - The `RippleState` balance between the borrower and the `Issuer` is decreased.
  - The `RippleState` balance between the `Vault` pseudo-account and the `Issuer` is increased.
  - The `RippleState` balance between the destination account for fees (`LoanBroker.Owner` or `LoanBroker` pseudo-account) and the `Issuer` is increased.
- **If the asset is an MPT**:
  - The `MPTAmount` in the borrower's `MPToken` object is decreased.
  - The `MPTAmount` in the `Vault` pseudo-account's `MPToken` object is increased.
  - The `MPTAmount` in the destination account for fees (`LoanBroker.Owner` or `LoanBroker` pseudo-account) `MPToken` object is increased.

##### 3.2.4.6 Invariants

**TBD**

# Appendix

## A-1 F.A.Q.

### A-1.1. What is the `LoanBroker.LoanSequence` field?

A sequential identifier for Loans associated with a LoanBroker object. This value increments with each new Loan created by the broker. Unlike `LoanBroker.OwnerCount`, which tracks the number of currently active Loans, `LoanBroker.LoanSequence` reflects the total number of Loans ever created.

### A-1-2. Why the `LoanBrokerCoverClawback` cannot clawback the full LoanBroker.CoverAvailable amount?

The `LoanBrokerCoverClawback` transaction allows the Issuer to clawback the `LoanBroker` First-Loss Capital, specifically the `LoanBroker.CoverAvailable` amount. The transaction cannot claw back the full CoverAvailable amount because the LoanBroker must maintain a minimum level of first-loss capital to protect depositors. This minimum is calculated as `LoanBroker.DebtTotal * LoanBroker.CoverRateMinimum`. When a `LoanBroker` has active loans, a complete clawback would leave depositors vulnerable to unexpected losses. Therefore, the system ensures that a minimum amount of first-loss capital is always maintained.
