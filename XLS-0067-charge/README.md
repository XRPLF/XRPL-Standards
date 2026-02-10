<pre>
  xls: 67
  title: Charge
  description: A feature that focuses on fee collection and makes monetization easier and simpler for platforms, wallet services, and users to use
  author: tequ (@tequdev)
  proposal-from: https://github.com/XRPLF/XRPL-Standards/discussions/194
  created: 2024-04-22
  status: Stagnant
  category: Amendment
</pre>

# Abstract

One way to monetize NFT, AMM and other platforms that use XRP Ledger is to charge a fee from separate Payment transaction. [XLS-56](../XLS-0056-batch/README.md) (Batch/Atomic Transaction) has already been proposed as a way to do this in a single transaction. Here, I propose a feature that focuses on fee collection and makes monetization easier and simpler for platforms, wallet services, and users to use.

# Specification

### Transaction common field

Add the following field as one of transaction common fields.
This field is an optional field and be available for any transaction.

| Field Name | Required? | JSON Type | Internal Type |
| ---------- | :-------: | :-------: | :-----------: |
| `Charge`   |           | `object`  |   `Object`    |

## `Charge` Field

| Field Name       | Required? |      JSON Type       | Internal Type |
| ---------------- | :-------: | :------------------: | :-----------: |
| `Amount`         |    ✅     | `object` or `string` |   `Amount`    |
| `Destination`    |    ✅     |       `string`       |   `Account`   |
| `DestinationTag` |           |       `number`       |   `UInt16`    |

#### `Amount` Field

Like the `Amount` field used in other transaction types, it represents a native token when specified as a string, or an issued token when specified as an object.

For tokens for which a TransferRate has been specified by the issuer, this field represents the amount of tokens sent by the sender of the transaction and doesn't guarantee the amount of tokens the destination account will receive.

### `Destination` Field

The account to which the fee will be sent.

It is not possible to specify the account from which the transaction originates or an account that has not been activated.

# Matters to Consider

These are not included in the above specifications, but are subject to discussion.

## `SendMax` Field

We could add `SendMax` to specify exactly how much the sender pays and how much the receiver receives, but that would be more complicated.

## CrossCurrency

It is possible to make cross-currency payments by specifying different currencies in the `SendMax` and `Amount` fields, but this will increase transaction load.

The `Path` field cannot specified and the default Path is used.
e.g.

- AAA/BBB without XLS-60
- AAA/XRP, BBB/XRP, AAA/BBB with XLS-60

## Multiple charges

Multiple currencies can be set as fees by specifying multiple `Charge` fields as an array in the `Charges` field, but this increases the transaction load (especially if cross-currency is also available).
