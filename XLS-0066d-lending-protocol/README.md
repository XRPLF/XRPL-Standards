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

| Field Name                | User Modifiable? | Constant? |     Required?      | JSON Type | Internal Type |                 Default Value                 | Description                                                                                                                                                    |
| ------------------------- | :--------------: | :-------: | :----------------: | :-------: | :-----------: | :-------------------------------------------: | -------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `LedgerEntryType`         |       `No`       |   `Yes`   | :heavy_check_mark: | `string`  |   `UINT16`    |                   `0x0089`                    | Ledger object type.                                                                                                                                            |
| `LedgerIndex`             |       `No`       |   `Yes`   | :heavy_check_mark: | `string`  |   `UINT16`    |                     `N/A`                     | Ledger object identifier.                                                                                                                                      |
| `Flags`                   |      `Yes`       |   `No`    |                    | `string`  |   `UINT32`    |                       0                       | Ledger object flags.                                                                                                                                           |
| `PreviousTxnID`           |       `No`       |   `No`    | :heavy_check_mark: | `string`  |   `HASH256`   |                     `N/A`                     | The ID of the transaction that last modified this object.                                                                                                      |
| `PreviousTxnLgrSeq`       |       `No`       |   `No`    | :heavy_check_mark: | `number`  |   `UINT32`    |                     `N/A`                     | The ledger sequence containing the transaction that last modified this object.                                                                                 |
| `LoanSequence`            |       `No`       |   `Yes`   | :heavy_check_mark: | `number`  |   `UINT32`    |                     `N/A`                     | The sequence number of the Loan.                                                                                                                               |
| `OwnerNode`               |       `No`       |   `Yes`   | :heavy_check_mark: | `number`  |   `UINT64`    |                     `N/A`                     | Identifies the page where this item is referenced in the `Borrower` owner's directory.                                                                         |
| `LoanBrokerNode`          |       `No`       |   `Yes`   | :heavy_check_mark: | `number`  |   `UINT64`    |                     `N/A`                     | Identifies the page where this item is referenced in the `LoanBroker`s owner directory.                                                                        |
| `LoanBrokerID`            |       `No`       |   `Yes`   | :heavy_check_mark: | `string`  |   `HASH256`   |                     `N/A`                     | The ID of the `LoanBroker` associated with this Loan Instance.                                                                                                 |
| `Borrower`                |       `No`       |   `Yes`   | :heavy_check_mark: | `string`  |  `AccountID`  |                     `N/A`                     | The address of the account that is the borrower.                                                                                                               |
| `LoanOriginationFee`      |       `No`       |   `Yes`   | :heavy_check_mark: | `number`  |   `NUMBER`    |                     `N/A`                     | A nominal nds amount paid to the `LoanBroker.Owner` when the Loan is created.                                                                                  |
| `LoanServiceFee`          |       `No`       |   `Yes`   | :heavy_check_mark: | `number`  |   `NUMBER`    |                     `N/A`                     | A nominal funds amount paid to the `LoanBroker.Owner` with every Loan payment.                                                                                 |
| `LatePaymentFee`          |       `No`       |   `Yes`   | :heavy_check_mark: | `number`  |   `NUMBER`    |                     `N/A`                     | A nominal funds amount paid to the `LoanBroker.Owner` when a payment is late.                                                                                  |
| `ClosePaymentFee`         |       `No`       |   `Yes`   | :heavy_check_mark: | `number`  |   `NUMBER`    |                     `N/A`                     | A nominal funds amount paid to the `LoanBroker.Owner` when a payment full payment is made.                                                                     |
| `OverpaymentFee`          |       `No`       |   `Yes`   | :heavy_check_mark: | `number`  |   `UINT32`    |                     `N/A`                     | A fee charged on overpayments in 1/10th basis points. Valid values are between 0 and 100000 inclusive. (0 - 100%)                                              |
| `InterestRate`            |       `No`       |   `Yes`   | :heavy_check_mark: | `number`  |   `UINT32`    |                     `N/A`                     | Annualized interest rate of the Loan in 1/10th basis points.                                                                                                   |
| `LateInterestRate`        |       `No`       |   `Yes`   | :heavy_check_mark: | `number`  |   `UINT32`    |                     `N/A`                     | A premium is added to the interest rate for late payments in 1/10th basis points. Valid values are between 0 and 100000 inclusive. (0 - 100%)                  |
| `CloseInterestRate`       |       `No`       |   `Yes`   | :heavy_check_mark: | `number`  |   `UINT32`    |                     `N/A`                     | An interest rate charged for repaying the Loan early in 1/10th basis points. Valid values are between 0 and 100000 inclusive. (0 - 100%)                       |
| `OverpaymentInterestRate` |       `No`       |   `Yes`   | :heavy_check_mark: | `number`  |   `UINT32`    |                     `N/A`                     | An interest rate charged on overpayments in 1/10th basis points. Valid values are between 0 and 100000 inclusive. (0 - 100%)                                   |
| `StartDate`               |       `No`       |   `Yes`   | :heavy_check_mark: | `number`  |   `UINT32`    |           `CurrentLedgerTimestamp`            | The timestamp of when the Loan started [Ripple Epoch](https://xrpl.org/docs/references/protocol/data-types/basic-data-types/#specifying-time).                 |
| `PaymentInterval`         |       `No`       |   `Yes`   | :heavy_check_mark: | `number`  |   `UINT32`    |                     `N/A`                     | Number of seconds between Loan payments.                                                                                                                       |
| `GracePeriod`             |       `No`       |   `Yes`   | :heavy_check_mark: | `number`  |   `UINT32`    |                     `N/A`                     | The number of seconds after the Loan's Payment Due Date that the Loan can be Defaulted.                                                                        |
| `PreviousPaymentDate`     |       `No`       |   `No`    | :heavy_check_mark: | `number`  |   `UINT32`    |                      `0`                      | The timestamp of when the previous payment was made in [Ripple Epoch](https://xrpl.org/docs/references/protocol/data-types/basic-data-types/#specifying-time). |
| `NextPaymentDueDate`      |       `No`       |   `No`    | :heavy_check_mark: | `number`  |   `UINT32`    | `LoanSet.StartDate + LoanSet.PaymentInterval` | The timestamp of when the next payment is due in [Ripple Epoch](https://xrpl.org/docs/references/protocol/data-types/basic-data-types/#specifying-time).       |
| `PaymentRemaining`        |       `No`       |   `No`    | :heavy_check_mark: | `number`  |   `UINT32`    |            `LoanSet.PaymentTotal`             | The number of payments remaining on the Loan.                                                                                                                  |
| `PrincipalOutstanding`    |       `No`       |   `No`    | :heavy_check_mark: | `number`  |   `NUMBER`    |         `LoanSet.PrincipalRequested`          | The principal amount due to be paid by the Borrower.                                                                                                           |
| `TotalValueOutstanding`   |       `No`       |   `No`    | :heavy_check_mark: | `number`  |   `NUMBER`    |           `TotalValueOutstanding()`           | THe total outstanding value of the Loan.                                                                                                                       |

##### 2.2.2.1 Flags

The `Loan` object supports the following flags:

| Flag Name            |  Flag Value  | Modifiable? |                      Description                       |
| -------------------- | :----------: | :---------: | :----------------------------------------------------: |
| `lsfLoanDefault`     | `0x00010000` |    `No`     |     If set, indicates that the Loan is defaulted.      |
| `lsfLoanImpaired`    | `0x00020000` |    `Yes`    |      If set, indicates that the Loan is impaired.      |
| `lsfLoanOverpayment` | `0x00040000` |    `No`     | If set, indicates that the Loan supports overpayments. |

#### 2.2.3 Ownership

The `Loan` objects are stored in the ledger and tracked in two [Owner Directories](https://xrpl.org/docs/references/protocol/ledger-data/ledger-entry-types/directorynode).

- The `OwnerNode` is the `Owner Directory` of the `Borrower` who is the main `Owner` of the `Loan` object, and therefore is responsible for the owner reserve.
- The `LoanBrokerNode` is the `Owner Directory` for the `LoanBroker` _pseudo-account_ to track all loans associated with the same `LoanBroker` object.

#### 2.2.4 Reserves

The `Loan` object costs one owner reserve for the `Borrower`.

#### 2.2.5 Loan Total Value

The loan's financial state is tracked through three key components:

- **PrincipalOutstanding**: Represents the remaining principal balance that the borrower must repay to satisfy the original loan amount.
- **TotalValueOutstanding**: Encompasses the complete remaining loan obligation, comprising both the outstanding principal and all scheduled interest payments based on the original amortization schedule. This value excludes any additional interest charges resulting from late payments.
- **InterestOutstanding**: The total scheduled interest remaining on the loan, derived as `TotalValueOutstanding - PrincipalOutstanding`.

**Asset-Specific Precision Handling**: For discrete asset types (MPTs and XRP denominated in drops), both `TotalValueOutstanding` and `PrincipalOutstanding` values are truncated to whole numbers to ensure compatibility with the underlying asset precision requirements.

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
| `ManagementFeeRate`    |                    |    `No`     | `number`  |   `UINT16`    |       0       | The 1/10th basis point fee charged by the Lending Protocol Owner. Valid values are between 0 and 10000 inclusive.                                  |
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
2. The `Signers` field.

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

  - The `RippleState` object between the Borrower account and the `Issuer` of the asset has the `lsfLowFreeze` or `lsfHighFreeze` flag set.
  - The `RippleState` object between the LoanBroker account and the `Issuer` of the asset has the `lsfLowFreeze` or `lsfHighFreeze` flag set.
  - The `RippleState` between the `LoanBroker.Account` and the `Issuer` has the `lsfLowDeepFreeze` or `lsfHighDeepFreeze` flag set. (The Loan Broker _pseudo-account_ is frozen).
  - The `RippleState` between the `Vault(LoanBroker(LoanBrokerID).VaultID).Account` and the `Issuer` has the `lsfLowFreeze` or `lsfHighFreeze` flag set. (The Vault _pseudo-account_ is frozen).
  - The `AccountRoot` object of the `Issuer` has the `lsfGlobalFreeze` flag set.

- If the `Vault(LoanBroker(LoanBrokerID).VaultID).Asset` is an `MPT`:

  - The `MPToken` object for the `Vault(LoanBroker(LoanBrokerID).VaultID).Asset` of the LoanBroker `AccountRoot` has `lsfMPTLocked` flag set.
  - The `MPToken` object for the `Vault(LoanBroker(LoanBrokerID).VaultID).Asset` of the Borrower `AccountRoot` has `lsfMPTLocked` flag set.
  - The `MPToken` object for the `Vault(LoanBroker(LoanBrokerID).VaultID).Asset` of the `LoanBroker.Account` `AccountRoot` has `lsfMPTLocked` flag set. (The Loan Broker _pseudo-account_ is locked).
  - The `MPTokenIssuance` object of the `Vault(LoanBroker(LoanBrokerID).VaultID).Asset` has the `lsfMPTLocked` flag set.

- Either of the `tfLoanDefault`, `tfLoanImpair` or `tfLoanUnimpair` flags are set.

- The `Borrower` `AccountRoot` object does not exist.

- `PaymentInterval` is less than `60` seconds.
- `GracePeriod` is greater than the `PaymentInterval`.

- Insufficient assets in the Vault:

  - `Vault(LoanBroker(LoanBrokerID).VaultID).AssetsAvailable` < `Loan.PrincipalRequested`.

- Exceeds maximum Debt of the LoanBroker:

  - `LoanBroker(LoanBrokerID).DebtMaximum` < `Loan.PrincipalRequested + (TotalInterestOutstanding() - (TotalInterestOutstanding() x LoanBroker.ManagementFeeRate)`

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
  - Increase the `RippleState` balance between the `LoanBroker.Owner` `AccountRoot` and the `Issuer` `AccountRoot` by `Loan.LoanOriginationFee`.

- If the `Vault(LoanBroker(LoanBrokerID).VaultID).Asset` is an `MPT`:

  - Create an `MPToken` object for the `Borrower` if one does not exist.

  - Decrease the `MPToken.MPTAmount` of the `Vault` _pseudo-account_ `MPToken` object for the `Vault.Asset` by `Loan.PrincipalRequested`.
  - Increase the `MPToken.MPTAmount` of the `Borrower` `MPToken` object for the `Vault.Asset` by `Loan.PrincipalRequested - Loan.LoanOriginationFee`.
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

    - `Loan(LoanID).Flags &= ~lsfLoanImpaired`
    - `CandidateDueDate = max(Loan.PreviousPaymentDate, Loan.StartDate) + Loan.PaymentInterval`

    - If `CandidateDueDate > currentTime` (the loan was unimpaired within the payment interval):

      - `Loan(LoanID).NextPaymentDueDate = CandidateDueDate`

    - If `CandidateDueDate <= currentTime` (the loan was unimpaired after the original payment due date):
      - `Loan(LoanID).NextPaymentDueDate = currentTime + Loan(LoanID).PaymentInterval`

##### 3.2.3.3 Invariants

**TBD**

[**Return to Index**](#index)

#### 3.2.4 `LoanPay` Transaction

The Borrower submits a `LoanPay` transaction to make a Payment on the Loan.

| Field Name        |     Required?      | JSON Type | Internal Type | Default Value | Description                              |
| ----------------- | :----------------: | :-------: | :-----------: | :-----------: | :--------------------------------------- |
| `TransactionType` | :heavy_check_mark: | `string`  |   `UINT16`    |     `83`      | The transaction type.                    |
| `LoanID`          | :heavy_check_mark: | `string`  |   `HASH256`   |     `N/A`     | The ID of the Loan object to be paid to. |
| `Amount`          | :heavy_check_mark: | `number`  |   `AMOUNT`    |     `N/A`     | The amount of funds to pay.              |

##### 3.2.4.1 Payment Types

A Loan payment has four types:

- Regular payment is made on time, where the payment size and schedule are calculated with a standard amortization [formula](https://en.wikipedia.org/wiki/Amortization_calculator).

- A _late_ payment, when a Borrower makes a payment after `netxPaymentDueDate`. Late payments include a `LatePaymentFee` and `LateInterestRate`.

- An early _full_ payment is when a Borrower pays the outstanding principal. A `CloseInterestRate` is charged on the outstanding principal.

- An overpayment occurs when a borrower makes a payment that exceeds the required minimum payment amount.

The payment amount and timing determine the type of payment. A payment made before the `Loan.NextPaymentDueDate` is a regular payment and follows the standard amortization calculation. Any payment made after this date is considered a late payment.

The following diagram depicts how a payment is handled based on the amount paid.

```
   Rejected     Overpayment     Overpayment     Overpayment    Not charged
|------------|---------------|---------------|---------------|-------------|
      Periodic/Late      Periodic        Periodic          Full
     Payment Amount  Payment Amount  Payment Amount   Payment Amount
            I              II             N - 1

                          Payment Amount
```

The minimum payment required is determined by whether the borrower makes the payment before or on the `NextPaymentDueDate` or if it is late. Any payment below the minimum amount required is rejected. With a single `LoanPay` transaction, the Borrower can make multiple loan payments. For example, if the periodic payment amount is 400 Tokens and the Borrower makes a payment of 900 Tokens, the payment will be treated as two periodic payments, moving the NextPaymentDueDate forward to two payment intervals, and the remaining 100 Tokens will be an overpayment.

If the Loan Broker and the borrower have agreed to allow overpayments, any amount above the periodic payment is treated as an overpayment. However, if overpayments are not supported, the excess amount will not be charged and will remain with the borrower.

Each payment comprises three parts, `principal`, `interest` and `fee`. The `principal` is an amount paid against the principal of the Loan, `interest` is the interest portion of the Loan, and `fee` is the fee part paid by the Borrower on top of `principal` and `interest`.

###### 3.2.4.1.1 Regular Payment

A periodic payment amount is calculated using the amortization payment formula:

$$
totalDue = periodicPayment + loanServiceFee
$$

$$
periodicPayment = principalOutstanding \times \frac{periodicRate \times (1 + periodicRate)^{PaymentRemaining}}{(1 + periodicRate)^{PaymentRemaining} - 1}
$$

where the periodic interest rate is the interest rate charged per payment period:

$$
periodicRate = \frac{interestRate \times paymentInterval}{365 \times 24 \times 60 \times 60}
$$

The `principal` and `interest` portions can be derived as follows:

$$
interest = principalOutstanding \times periodicRate
$$

$$
principal = periodicPayment - interest
$$

When only a single payment remains (PaymentRemaining = 1) the periodic payment MUST be set equal to the current TotalValueOutstanding (i.e. principalOutstanding + interestOutstanding before any asset-specific rounding/truncation). This overrides the standard amortization formula for the last installment. The purpose is to eliminate residual dust created by iterative rounding (e.g. integer truncation for XRP drops or whole‑unit MPTs) that could otherwise make the loan impossible to fully extinguish.

Formally:
If PaymentRemaining > 1:
periodicPayment = formula result (rounded per asset rules)
If PaymentRemaining = 1:
periodicPayment = TotalValueOutstanding (rounded per asset rules; this sets TotalValueOutstanding to 0 after payment)

Rationale:
Repeated downward rounding (truncate / floor) of each scheduled payment can accumulate underpayment relative to the unrounded amortization schedule. Without this adjustment, the final formula-derived payment (after rounding) might be smaller than the remaining outstanding value, leaving a non-zero remainder that can never be cleared by any subsequent scheduled payment (because no payments remain).

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

Therefore, implementations MUST detect the single remaining payment case and substitute the outstanding value to guarantee full extinguishment of the debt.

###### 3.2.4.1.2 Late Payment

When a Borrower makes a payment after `NextPaymentDueDate`, they must pay a nominal late payment fee and an additional interest rate charged on the overdue amount for the unpaid period. The formula is as follows:

$$
totalDue = periodicPayment + latePaymentFee + latePaymentInterest
$$

$$
secondsSinceLastPayment = lastLedgerCloseTime - max(Loan.previousPaymentDate, Loan.startDate)
$$

A special, late payment interest rate is applied for the over-due period:

$$
latePaymentInterest = principalOutstanding \times \frac{lateInterestRate \times secondsSinceLastPayment}{365 \times 24 \times 60 \times 60}
$$

A late payment pays more interest than calculated when increasing the Vault value in the `LoanSet` transaction. Therefore, the total Vault value captured by `Vault.AssetsTotal` must be recalculated.

Assume the function `PeriodicPayment()` returns the expected periodic payment, split into `principalPeriodic` and `interestPeriodic`. Furthermore, assume the function `LatePayment()` that implements the Late Payment formula. The function returns the late payment split into `principalLate` and `interestLate`, where `interestLate` is calculated using the formula above. Note that `principalPeriodic == principalLate` and `interestLate > interestPeriodic` are used only when the payment is late. Otherwise, `interestLate == interestPeriodic`.

$$
valueChange = interestLate - interestPeriodic
$$

Note that `valueChange >= 0` for late payments, i.e. a late payment increases the value of the loan.

###### 3.2.4.1.3 Loan Overpayment

- Let $\mathcal{P}$ and $\mathcal{p}$ represent the total and outstanding Loan principal.
- Let $\mathcal{I}$ and $\mathcal{i}$ represent the total and outstanding Loan interest computed from $\mathcal{P}$ and $\mathcal{p}$ respectively.

$$
excess = min(\mathcal{p}, paymentAmountMade - minimumPaymentAmount)
$$

$$
interestPortion = excess \times overpaymentInterestRate
$$

$$
feePortion = excess \times overpaymentFee
$$

$$
principalPortion = excess - interestPortion - feePortion
$$

$$
\mathcal{p'} = \mathcal{p} - principalPortion
$$

Let $\mathcal{i}$ denote the outstanding interest computed from $\mathcal{p}$. Simillarly, let $\mathcal{i'}$ denote the outstanding interest computed from $\mathcal{p'}$. We compute the loan interest change as follows:

$$
valueChange =  \mathcal{i} - \mathcal{i'}
$$

###### 3.2.4.1.4 Early Full Repayment

A Borrower can close a Loan early by submitting the total amount needed to do so. This amount is the sum of the remaining balance, any accrued interest, a prepayment penalty, and a prepayment fee.

$$
totalDue = principalOutstanding + accruedInterest + prepaymentPenalty + ClosePaymentFee
$$

$$
secondsSinceLastPayment = lastLedgerCloseTime - max(Loan.previousPaymentDate, Loan.startDate)
$$

Accrued interest up to the point of early closure is calculated as follows:

$$
accruedInterest = principalOutstanding  \times periodicRate \times \frac{secondsSinceLastPayment}{paymentInterval}
$$

Finally, the Lender may charge a prepayment penalty for paying a loan early, which is calculated as follows:

$$
prepaymentPenalty = principalOutstanding \times closeInterestRate
$$

An early payment pays less interest than calculated when increasing the Vault value in the `LoanSet` transaction. Therefore, the Vault value (captured by `Vault.AssetsTotal`) must be recalculated after an early payment.

Assume a function `CurrentValue()` that returns `principalOutstanding` and `interestOutstanding` of the Loan. Furthermore, assume a function `ClosePayment()` that implements the Full Payment calculation. The function returns the total full payment due split into `principal` and `interest`.

The value change for an early full repayment is calculated as follows:

$$
valueChange = (prepaymentPenalty) - (interestOutstanding - accruedInterest)
$$

###### 3.2.4.1.5 Management Fee Calculations

The `LoanBroker` Management fee is charged against the interest portion of the Loan and subtracted from the total Loan value at Loan creation. However, the fee is charged only during Loan payments. Early and Late payments change the total value of the Loan by decreasing or increasing the value of total interest. Therefore, when an early, late or an overpayment payment is made, the management fee must be updated.

To update the management fee, we need to compute the new total management fee based on the new total interest after executing the early or late payment. Therefore, we need to capture the Loan value before the payment is made and the new value after the payment is made.

For the calculation, assume the following variables:

- Let $\mathcal{P}$ and $\mathcal{p}$ represent the total and outstanding Loan principal.
- Let $\mathcal{I}$ and $\mathcal{i}$ represent the total and outstanding Loan interest computed from $\mathcal{P}$ and $\mathcal{p}$ respectively.
- Let $\mathcal{V}$ and $\mathcal{v}$ represent the total and outstanding value of the Loan. $\mathcal{V} = \mathcal{P} + \mathcal{I}$ and $\mathcal{v} = \mathcal{p} + \mathcal{i}$.
- Finally, let $\mathcal{m}$ represent the management fee rate of the Loan Broker.

Assume $f(\mathcal{v})$ is a Loan payment, $f(\mathcal{v}) = \mathcal{v'}$, the new outstanding loan value is equal to the application of the payment transaction to the current outstanding value. Furthermore, assume $\mathcal{V} \xrightarrow{f(\mathcal{v})}$ $\mathcal{V'}$, is the change in the Loan total value as the result of applying $f(\mathcal{v})$.

we say that $\mathcal{V'} = \mathcal{P'} + \mathcal{I'}$. It's important to note that a payment transaction must never change the total principal. I.e. $\mathcal{P} = \mathcal{P'}$, the change in total value is caused by the change in total interest only.

$\Delta_{\mathcal{V}} = \mathcal{I'} - \mathcal{I}$ is the total value change of the Loan. When $\Delta_{\mathcal{V}} > 0$ the total value of the Loan increased, when $\Delta_{\mathcal{V}} < 0$ the total value decreased, and if $\Delta_{\mathcal{V}} = 0$ the value remained the same.

The total management fee is calculated as follows:

$$
managementFeeTotal = \mathcal{I} \times \mathcal{m}
$$

We compute the management fee paid so far as follows:

$$
managementFeePaid = (\mathcal{I} - \mathcal{i}) \times \mathcal{m}
$$

$$
managementFeeDue = managementFeeTotal - managementFeePaid
$$

Finally, we compute the change in management fee as follows:

$$
managementFeeChange = \mathcal{i'} \times \mathcal{m} - managementFeeDue
$$

The above calculation can be simplified to:

$$
managementFeeChange = \Delta_{\mathcal{V}} \times \mathcal{m}
$$

When the management fee change is negative, the Loan's value decreases, and thus, the Loan Broker's debt decreases.
Intuitively, a negative fee change suggests that the fee must be returned, increasing the loan broker's debt.

In contrast, if the management fee change is positive, the Loan's value increases, and a further fee must be deducted from the debt.
Intuitively, a positive fee change suggests that an additional fee must be paid due to the increase in the interest paid.

The LoanBroker debt is then updated as:

$$
LoanBroker.DebtTotal = LoanBroker.DebtTotal - managementFeeChange
$$

##### 3.2.4.2 Total Loan Value Calculation

At any point in time the following formulae can be used to calculate the total remaining value of the loan.

The periodic interest rate is the interest rate charged per payment period.

$$
periodicRate = \frac{interestRate \times paymentInterval}{365 \times 24 \times 60 \times 60}
$$

The payment is computed based on the periodic rate, principal outstanding, and number of payments remaining. (This means the payment amount can decrease if the borrow pays principal early.)

$$
periodicPayment = principalOutstanding \times \frac{periodicRate \times (1 + periodicRate)^{PaymentRemaining}}{(1 + periodicRate)^{PaymentRemaining} - 1}
$$

The total loan value is simply:

$$
totalValueOutstanding = periodicPayment \times PaymentRemaining
$$

We calculate the total interest outstanding as follows:

$$
totalInterestOutstanding = totalValueOutstanding - principalOutstanding
$$

##### 3.2.4.3 Transaction Pseudo-code

The following is the pseudo-code for handling a Loan payment transaction.

```
function make_payment(amount, current_time) -> (principal_paid, interest_paid, value_change, fee_paid):
    if loan.payments_remaining is 0 || loan.principal_outstanding is 0 {
        return "loan complete" error
    }

    // the payment is late
    if loan.next_payment_due_date < current_time {
        let late_payment = loan.compute_late_payment(current_time)
        if amount < late_payment {
            return "insufficient amount paid" error
        }

        loan.payments_remaining -= 1
        loan.principal_outstanding -= late_payment.principal

        loan.last_payment_date = loan.next_payment_due_date
        loan.next_payment_due_date = loan.next_payment_due_date + loan.payment_interval

        let periodic_payment = loan.compute_periodic_payment()

        // A late payment increases the value of the loan by the difference between periodic and late payment interest
        return (late_payment.principal, late_payment.interest, late_payment.interest - periodic_payment.interest, loan.late_payment_fee)
    }

    let full_payment = loan.compute_full_payment(current_time)

    // if the payment is equal or higher than full payment amount
    // and there is more than one payment remaining, make a full payment
    if amount >= full_payment && loan.payments_remaining > 1 {
        loan.payments_remaining = 0
        loan.principal_outstanding = 0
        let total_interest_outstanding = loan.lotal_value_outstanding - full_payment.principal
        // A full payment decreases the value of the loan by the difference between the interest paid and the expected outstanding interest
        return (full_payment.principal, full_payment.interest, full_payment.interest - total_interest_outstanding, full_payment.fee)
    }

    // PERIODIC (ON‑TIME) FLOW
    // Compute scheduled periodic payment. Override if this is the final installment to eliminate rounding dust.
    let periodic_payment = loan.compute_periodic_payment()
    if loan.payments_remaining == 1 {
        // Final scheduled payment: pay exactly all remaining value (principal + interest) before rounding.
        periodic_payment.principal = loan.principal_outstanding
        periodic_payment.interest  = loan.total_value_outstanding - loan.principal_outstanding
    }

    let periodic_payment_total = periodic_payment.principal + periodic_payment.interest

    // Determine how many full periodic installments this single Amount can cover (cannot exceed remaining)
    let full_periodic_payments = floor(amount / (periodic_payment_total + loan.service_fee))
    if full_periodic_payments < 1 {
        return "insufficient amount paid" error
    }
    if full_periodic_payments > loan.payments_remaining {
        full_periodic_payments = loan.payments_remaining
    }

    loan.next_payment_due_date = loan.next_payment_due_date + loan.payment_interval * full_periodic_payments
    loan.last_payment_date = loan.next_payment_due_date - loan.payment_interval

    let total_principal_paid = 0
    let total_interest_paid = 0
    let loan_value_change = 0
    let total_fee_paid = loan.service_fee * full_periodic_payments
    let loan_value_change = 0
  
    while full_periodic_payments > 0 {
        total_principal_paid += periodic_payment.principal
        total_interest_paid  += periodic_payment.interest
        loan.payments_remaining -= 1
        loan.principal_outstanding -= periodic_payment.principal

        if loan.payments_remaining == 0 {
            // All done; no further recomputation needed.
            break
        }

        // Recompute next periodic payment (may change after principal reduction).
        periodic_payment = loan.compute_periodic_payment()

        // If after recomputation only one payment remains, force final payoff to avoid residual dust.
        if loan.payments_remaining == 1 {
          periodic_payment.principal = loan.principal_outstanding
          periodic_payment.interest  = loan.total_value_outstanding - loan.principal_outstanding
      }

        full_periodic_payments -= 1
    }

    let overpayment = min(loan.principal_outstanding, amount % (periodic_payment + loan.service_fee))
    if overpayment > 0 && is_set(lsfOverpayment) {
        let interest_portion = overpayment * loan.overpayment_interest_rate
        let fee_portion = overpayment * loan.overpayment_fee
        let remainder = overpayment - interest_portion - fee_portion

        total_principal_paid += remainder
        total_interest_paid  += interest_portion
        total_fee_paid       += fee_portion

        let current_value = loan.compute_current_value()
        loan.principal_outstanding -= remainder
        let new_value = loan.compute_current_value()

        // loan_value_change: change in future interest due to principal reduction + interest just paid
        loan_value_change = (new_value.interest - current_value.interest) + interest_portion
    }

    // If final installment just executed, ensure outstanding principal hits zero (guard against residual 1-unit dust)
    if loan.payments_remaining == 0 {
        loan.principal_outstanding = 0
    }

    return (total_principal_paid, total_interest_paid, loan_value_change, total_fee_paid)
```

##### 3.2.4.4 Failure Conditions

Assume the payment is split into `principal`, `interest` and `fee`, and `totalDue = principal + interest + fee`. `totalDue` is the minimum payment due by the borrower.

Assume the payment is handled by a function that implements the [Pseudo-Code](#3242-transaction-pseudo-code) that returns `principal_paid`, `interest_paid`, `value_change` and `fee_paid`, where:

- `principal_paid` is the amount of principal that the payment covered.
- `interest_paid` is the amount of interest that the payment covered.
- `fee_paid` is the amount of fee that the payment covered.
- `totalPaid = principal_paid + interest_paid + fee_paid` is the total amount the borrower paid.
- `value_change` is the amount by which the total value of the Loan changed.
  - If `value_change` < `0`, Loan value decreased.
  - If `value_change` > `0`, Loan value increased, and if `value_change` = `0` the value remained the same.

Furthermore, assume `full_periodic_payments` variable represents the number of payment intervals that the payment covered.

- A `Loan` object with specified `LoanID` does not exist on the ledger.

- The submitter `AccountRoot.Account` is not equal to `Loan.Borrower`.

- `Loan.PaymentRemaining` or `Loan.TotalValueOutstanding` is `0`.

- The Borrower paid insufficient amount: `full_periodic_payments < 0`.

- If the `Vault(LoanBroker(Loan(LoanID).LoanBrokerID).VaultID).Asset` is an `IOU`:

  - The `RippleState` object between the submitter account and the `Issuer` of the asset has the `lsfLowFreeze` or `lsfHighFreeze` flag set.
  - The `RippleState` between the `LoanBroker.Account` and the `Issuer` has the `lsfLowDeepFreeze` or `lsfHighDeepFreeze` flag set. (The Loan Broker _pseudo-account_ is frozen).
  - The `RippleState` between the `Vault(LoanBroker(Loan.LoanBrokerID).VaultID).Account` and the `Issuer` has the `lsfLowFreeze` or `lsfHighFreeze` flag set. (The Vault _pseudo-account_ is frozen).
  - The `AccountRoot` object of the `Issuer` has the `lsfGlobalFreeze` flag set.

- If the `Vault(LoanBroker(Loan(LoanID).LoanBrokerID).VaultID).Asset` is an `MPT`:

  - The `MPToken` object for the `Vault(LoanBroker(Loan(LoanID).LoanBrokerID).VaultID).Asset` of the submitter `AccountRoot` has `lsfMPTLocked` flag set.
  - The `MPToken` object for the `Vault(LoanBroker(Loan(LoanID).LoanBrokerID).VaultID).Asset` of the `LoanBroker.Account` `AccountRoot` has `lsfMPTLocked` flag set. (The Loan Broker _pseudo-account_ is locked).
  - The `MPToken` object for the `Vault(LoanBroker(Loan(LoanID).LoanBrokerID).VaultID).Asset` of the `Vault(LoanBroker(Loan(LoanID).LoanBrokerID).VaultID).Account` `AccountRoot` has `lsfMPTLocked` flag set. (The Vault _pseudo-account_ is locked).
  - The `MPTokenIssuance` object of the `Vault(LoanBroker(Loan(LoanID).LoanBrokerID).VaultID).Asset` has the `lsfMPTLocked` flag set.

- If `LastClosedLedger.CloseTime >= Loan.NextPaymentDueDate` and `Amount` < `LatePaymentAmount()`

- If `LastClosedLedger.CloseTime < Loan.NextPaymentDueDate` and `Amount` < `PeriodicPaymentAmount()`

##### 3.2.4.5 State Changes

- `Loan` object state changes:

  - If `Loan(LoanID).Flags == lsfLoanImpaired`:

    - `Loan(LoanID).Flags = 0`

  - Decrease `Loan.PaymentRemaining` by `full_periodic_payments`.
  - Decrease `Loan.PrincipalOutstanding` by `principal_paid`.
  - Update `Loan.TotalValueOutstanding` = `(Loan.TotalValueOutstanding + value_change) - (principal_paid + interest_paid)`. 

  - If `Loan.PaymentRemaining > 0` and `Loan.PrincipalOutstanding > 0`:

    - Set the next payment date: `Loan.NextPaymentDueDate += Loan.PaymentInterval * full_periodic_payments`.
    - Set the previous payment date: `Loan.PreviousPaymentDate = Loan.NextPaymentDueDate - Loan.PaymentInterval`.

- `LoanBroker(Loan.LoanBrokerID)` object state changes:

  - Compute the management fee:

    - `feeManagement = interest_paid x LoanBroker.ManagementFeeRate`

  - Total paid, and what portion goes to the vault:

    - `totalPaid = principal_paid + interest_paid + fee_paid`
    - `totalPaidToVault = principal_paid + interest_paid`
    - `totalPaidToBroker = fee_paid`

  - Adjust the totals for the management fee:

    - `totalPaidToVault = totalPaidToVault - feeManagement`
    - `totalPaidToBroker = totalPaidToBroker + feeManagement`

  - If there is **not enough** first-loss capital: `LoanBroker.CoverAvailable < LoanBroker.DebtTotal x LoanBroker.CoverRateMinimum`:

    - Add the fee to to First Loss Cover Pool:

      - `LoanBroker.CoverAvailable = LoanBroker.CoverAvailable + (totalPaidToBroker)`

  - Decrease LoanBroker Debt by the amount paid:

    - `LoanBroker.DebtTotal = LoanBroker.DebtTotal - (totalPaid - fee_paid)`

  - Update the LoanBroker Debt by the Loan value change:

    - `LoanBroker.DebtTotal = LoanBroker.DebtTotal + valueChange`

  - Update the LoanBroker Debt by the change in the management fee:

    - `LoanBroker.DebtTotal = LoanBroker.DebtTotal - (valueChange x LoanBroker.ManagementFeeRate)`

- `Vault(LoanBroker(Loan.LoanBrokerID).VaultID)` state changes:

  - Increase available assets in the Vault by the amount paid:

    - `Vault.AssetsAvailable = Vault.AssetsAvailable + totalPaidToVault`

  - Update the Vault total value by the change in the Loan total value:

    - `Vault.AssetsTotal = Vault.AssetsTotal + valueChange`

  - Update the Vault total value by the change in the management fee:

    - `Vault.AssetsTotal = Vault.AssetsTotal - (vaultChange x LoanBroker.managementFeeRate)`

- If the `Vault(LoanBroker(Loan(LoanID).LoanBrokerID).VaultID).Asset` is `XRP`:

  - Increase the `Balance` field of `Vault` _pseudo-account_ `AccountRoot` by `principal_paid + (interest_paid - management_fee)`.

  - If `LoanBroker.CoverAvailable >= LoanBroker.DebtTotal x LoanBroker.CoverRateMinimum`:

    - Increase the `Balance` field of the `LoanBroker.Owner` `AccountRoot` by `fee_paid + management_fee`.

  - If `LoanBroker.CoverAvailable < LoanBroker.DebtTotal x LoanBroker.CoverRateMinimum`:

    - Increase the `Balance` field of the `LoanBroker` _pseudo-account_ `AccountRoot` by `fee_paid + management_fee`. (the payment and management fee was added to First Loss Capital, and thus transfered to the `LoanBroker` _pseudo-account_).
    - Increase `LoanBroker.CoverAvailable` by `fee_paid + management_fee`.

  - Decrease the `Balance` field of the submitter `AccountRoot` by `principal_paid + interest_paid + fee_paid`.

- If the `Vault(LoanBroker(Loan(LoanID).LoanBrokerID).VaultID).Asset` is an `IOU`:

  - Increase the `RippleState` balance between the `Vault` _pseudo-account_ `AccountRoot` and the `Issuer` `AccountRoot` by `principal_paid + (interest_paid - management_fee)`.

  - If `LoanBroker.CoverAvailable >= LoanBroker.DebtTotal x LoanBroker.CoverRateMinimum`:

    - Increase the `RippleState` balance between the `LoanBroker.Owner` `AccountRoot` and the `Issuer` `AccountRoot` by `fee_paid + management_fee`.

  - If `LoanBroker.CoverAvailable < LoanBroker.DebtTotal x LoanBroker.CoverRateMinimum`:

    - Increase the `RippleState` balance between the `LoanBroker` _pseudo-account_ `AccountRoot` and the `Issuer` `AccountRoot` by `fee_paid + management_fee` (the payment and management fee was added to First Loss Capital, and thus transfered to the `LoanBroker` _pseudo-account_).
    - Increase `LoanBroker.CoverAvailable` by `fee_paid + management_fee`.

  - Decrease the `RippleState` balance between the submitter `AccountRoot` and the `Issuer` `AccountRoot` by `principal_paid + interest_paid + fee_paid`.

- If the `Vault(LoanBroker(Loan(LoanID).LoanBrokerID).VaultID).Asset` is an `MPT`:

  - Increase the `MPToken.MPTAmount` by `principal_paid + (interest_paid - management_fee)` of the `Vault` _pseudo-account_ `MPToken` object for the `Vault.Asset`.

  - If `LoanBroker.CoverAvailable >= LoanBroker.DebtTotal x LoanBroker.CoverRateMinimum`:

    - Increase the `MPToken.MPTAmount` by `fee_paid + management_fee` of the `LoanBroker.Owner` `MPToken` object for the `Vault.Asset`.

  - If `LoanBroker.CoverAvailable < LoanBroker.DebtTotal x LoanBroker.CoverRateMinimum`:

    - Increase the `MPToken.MPTAmount` by `fee_paid + management_fee` of the `LoanBroker` _pseudo-account_ `MPToken` object for the `Vault.Asset` (the payment and management fee was added to First Loss Capital, and thus transfered to the `LoanBroker` _pseudo-account_).
    - Increase `LoanBroker.CoverAvailable` by `fee_paid + management_fee`.

  - Decrease the `MPToken.MPTAmount` by `principal_paid + interest_paid + fee_paid` of the submitter `MPToken` object for the `Vault.Asset`.

[**Return to Index**](#index)

##### 3.2.4.6 Invariants

**TBD**

# Appendix

## A-1 F.A.Q.

### A-1.1. What is the `LoanBroker.LoanSequence` field?

A sequential identifier for Loans associated with a LoanBroker object. This value increments with each new Loan created by the broker. Unlike `LoanBroker.OwnerCount`, which tracks the number of currently active Loans, `LoanBroker.LoanSequence` reflects the total number of Loans ever created.

### A-1-2. Why the `LoanBrokerCoverClawback` cannot clawback the full LoanBroker.CoverAvailable amount?

The `LoanBrokerCoverClawback` transaction allows the Issuer to clawback the `LoanBroker` First-Loss Capital, specifically the `LoanBroker.CoverAvailable` amount. The transaction cannot claw back the full CoverAvailable amount because the LoanBroker must maintain a minimum level of first-loss capital to protect depositors. This minimum is calculated as `LoanBroker.DebtTotal * LoanBroker.CoverRateMinimum`. When a `LoanBroker` has active loans, a complete clawback would leave depositors vulnerable to unexpected losses. Therefore, the system ensures that a minimum amount of first-loss capital is always maintained.
