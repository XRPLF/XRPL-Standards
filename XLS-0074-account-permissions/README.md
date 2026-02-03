<pre>
  xls: 74
  title: Account Permissions
  description: Formalization of different types of transaction-based account permissions for subset capabilities
  author: Mayukha Vadari <mvadari@ripple.com>
  proposal-from: https://github.com/XRPLF/XRPL-Standards/discussions/217
  status: Final
  category: Amendment
  created: 2024-08-21
</pre>

# Account Permissions

## Abstract

This document formalizes different types of transaction-based account permissions. Permissions include all transactions, a single transaction, or a subset of a transaction's capabilities.

## 1. Overview

[XLS-49](../XLS-0049-multiple-signer-lists/README.md) proposed transaction-type-level permissions. These types of permissions can be used for multiple signer lists, as explained in XLS-49, but could also be used in conjunction with other features.

Currently, it's all or nothing - global signer lists and regular keys can do all transactions. Sometimes you want to provide an account permissions to a subset of features, like with `NFTokenMinter` - maybe a few transaction types (e.g. all AMM transaction), or a single transaction type (e.g. `NFTokenMint`), or even some portion of a transaction type (e.g. authorizing trustlines).

This standard formalizes those transaction-type permissions, and also adds more granular permission options.

### 1.1. Background: Integer Types

An [integer](https://www.techtarget.com/whatis/definition/integer) is a whole number, a number with no decimals. It is usually shortened to `int` in programming languages.

Lower-level languages, such as C++ (the language that `rippled` is written in), have two main types of integers: unsigned and signed. An unsigned integer represents only nonnegative integers (positive integers and 0), while a signed integer represents both positive and negative integers (and 0, which is neither).

The XRPL supports many types of integers, all of which are unsigned. The difference between the different types is the size: the number of bits used to represent the number. A bit is a value that can be either `0` or `1`, the lowest level of data that a computer supports; all other data types are implemented as bits at their lowest level. One bit can only have two values (`0` and `1`), but two bits can have four values (`00` or `0`, `01` or `1`, `10` or `2`, `11` or `3`). So $n$ bits can represent $2^n$ possible values ($0$ to $2^n-1$).

| Number of Bits | Number of Possible Values | Possible Values (in [Binary](https://www.lifewire.com/how-to-read-binary-4692830) and Decimal)                                             |
| -------------- | ------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------ |
| 1              | $2^1$ or 2                | `0` <br> `1`                                                                                                                               |
| 2              | $2^2$ or 4                | `00` or `0` <br> `01` or `1` <br> `10` or `2` <br> `11` or `3`                                                                             |
| 3              | $2^3$ or 8                | `000` or `0` <br> `001` or `1` <br> `010` or `2` <br> `011` or `3` <br> `100` or `4` <br> `101` or `5` <br> `110` or `6` <br> `111` or `7` |

And so on.

An integer type name includes information about what type of integer it is (signed vs. unsigned) and how many bits it uses. So a `UInt8` is an unsigned integer that uses 8 bits (the `U` stands for "unsigned"), and an `Int16` is a signed integer that uses 16 bits (if the `U` is omitted, it's a signed integer).

The integer types that the XRPL supports are as follows:

| Name      | Range                 | Example Field         |
| --------- | --------------------- | --------------------- |
| `UInt8`   | 0-255                 | `sfTransactionResult` |
| `UInt16`  | 0-65,535              | `sfTransactionType`   |
| `UInt32`  | 0-4,294,967,295       | `sfSequence`          |
| `UInt64`  | $0-2^{64}{\text -}1$  | `sfExchangeRate`      |
| `UInt96`  | $0-2^{96}{\text -}1$  | None right now        |
| `UInt128` | $0-2^{128}{\text -}1$ | `sfEmailHash`         |
| `UInt160` | $0-2^{160}{\text -}1$ | `sfTakerPaysCurrency` |
| `UInt192` | $0-2^{192}{\text -}1$ | `sfMPTokenIssuanceID` |
| `UInt256` | $0-2^{256}{\text -}1$ | `sfNFTokenID`         |
| `UInt384` | $0-2^{384}{\text -}1$ | None right now        |
| `UInt512` | $0-2^{512}{\text -}1$ | None right now        |

_The `sf` in the above table stands for "Serialized Field"._

## 2. Permissions

A permission is represented by a `UInt32`.

### 2.1. Global Permission

The global permission value is already used in existing signer lists; they have a `SignerListID` value of `0`. This is being retroactively redefined to mean that the signer list has global permissions (i.e. can submit any transaction on behalf of an account).

**`0`: all permissions**

### 2.2. Transaction Type Permissions

A transaction type is represented by a `UInt16`.

Transaction type permissions were previously defined in [XLS-49](../XLS-0049-multiple-signer-lists/README.md), section `2.1.1`.

**`1` to `65536` ($2^{16}$): all transaction types** (1 + their serialized value, which is represented by a `UInt16`)

Adding a new transaction type to the XRPL will automatically be supported by any feature that uses these permissions.

#### 2.2.1. `Batch` Transactions

The one exception to this rule is `Batch` transactions ([XLS-56](../XLS-0056-batch/README.md)). They will not have a separate permission, since `Batch` transactions on their own do not do anything. In order to execute a `Batch` transaction with a permission, the user will need to have permissions for all the inner transactions.

### 2.3. Granular Permissions

These permissions would support control over some smaller portion of a transaction, rather than being able to do all of the functionality that the transaction allows.

We are able to include these permissions because of the gap between the size of the `UInt16` and the `UInt32` (the size of the `SignerListID` field).

| Value   | Name                     | Description                                                                |
| ------- | ------------------------ | -------------------------------------------------------------------------- |
| `65537` | `TrustlineAuthorize`     | Authorize a trustline.                                                     |
| `65538` | `TrustlineFreeze`        | Freeze a trustline.                                                        |
| `65539` | `TrustlineUnfreeze`      | Unfreeze a trustline.                                                      |
| `65540` | `AccountDomainSet`       | Modify the domain of an account.                                           |
| `65541` | `AccountEmailHashSet`    | Modify the `EmailHash` of an account.                                      |
| `65542` | `AccountMessageKeySet`   | Modify the `MessageKey` of an account.                                     |
| `65543` | `AccountTransferRateSet` | Modify the transfer rate of an account.                                    |
| `65544` | `AccountTickSizeSet`     | Modify the tick size of an account.                                        |
| `65545` | `PaymentMint`            | Send a payment for a currency where the sending account is the issuer.     |
| `65546` | `PaymentBurn`            | Send a payment for a currency where the destination account is the issuer. |
| `65547` | `MPTokenIssuanceLock`    | Use the `MPTIssuanceSet` transaction to lock (freeze) a holder.            |
| `65548` | `MPTokenIssuanceUnlock`  | Use the `MPTIssuanceSet` transaction to unlock (unfreeze) a holder.        |

### 2.4. Adding Additional Granular Types

Many other granular permissions may be added. There is capacity for a total of 4,294,901,759 granular permissions, given the limits of the size of the `UInt32` vs. the size of the `UInt16` (for transaction types).

Some other potential examples include:

- `SponsorFee` - the ability to sponsor the fee of another account (from [XLS-68](../XLS-0068-sponsored-fees-and-reserves/README.md))
- `SponsorReserve` - the ability to sponsor the fee of another account/object (from [XLS-68](../XLS-0068-sponsored-fees-and-reserves/README.md))

#### 2.4.1. Limitations

The set of permissions must be hard-coded. No custom configurations are allowed. For example, we cannot add permissions based on specific currencies - the best you could theoretically do on that front is XRP vs. issued currency.

In addition, each permission needs to be implemented on its own in the source code, so adding a new permission requires an amendment.

## 3. Security

Giving permissions to other parties requires a high degree of trust, especially when the delegated account can potentially access funds (the `Payment` permission) or charge reserves (any transaction that can create objects). In addition, any account that has permissions for the entire `AccountSet`, `SetRegularKey`, or `SignerListSet` transactions can give themselves any permissions even if this was not originally part of the intention.

With granular permissions, however, users can give permissions to other accounts for only parts of transactions without giving them full control. This is especially helpful for managing complex transaction types like `AccountSet`.

# Appendix

## Appendix A: FAQ

### A.1: Could we add additional permission values for different groups of transactions, like all NFT transactions or all AMM transactions?

Theoretically, yes. However, that can also easily be handled with a group of transaction-level permissions. If you think there is a need for this that isn't already addressed by having a group of permissions, please explain in a comment below.
