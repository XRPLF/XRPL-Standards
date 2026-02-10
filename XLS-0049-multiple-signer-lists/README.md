<pre>
  xls: 49
  title: Multiple Signer Lists
  description: A proposal to enable multiple signer lists per account on the XRP Ledger, allowing different signer lists to authorize specific transaction types.
  author: Mayukha Vadari <mvadari@ripple.com>
  proposal-from: https://github.com/XRPLF/XRPL-Standards/discussions/144
  status: Draft
  category: Amendment
  created: 2023-11-13
</pre>

# Multiple Signer Lists

## Abstract

The XRP Ledger currently only supports one global signer list per account. However, many users (such as token issuers) require more granularity. For example, they might want to have one signer list with the ability to mint new tokens, and another signer list with the ability to create and edit trustlines.

This document describes a proposal for supporting multiple signer lists per account. The current system of global signer lists will continue to be supported, but we propose adding **per-transaction-type signer lists**. Accounts can set up signer lists that only have the power to send **transactions of one specific type** on behalf of the account.

This proposal is related to [XLS-31](https://github.com/XRPLF/XRPL-Standards/discussions/77), but broader in scope.

## 1. Overview

We propose modifying one ledger object and one transaction:

- `SignerList` ledger object
- `SignerListSet` transaction

This change will require an amendment.

The important considerations to keep in mind are:

- `rippled` must be able to retrieve all possible signer lists for a transaction type quickly and easily, in order to check if a transaction has a valid multisign list.
- Any signer list that can sign transactions can drain the account's XRP via fees.

## 2. On-Ledger Object: **`SignerList`**

There is no change to the shape of a [`SignerList` ledger object](https://xrpl.org/signerlist.html), only in how it's used.

### 2.1. Fields

As a reference, the **`SignerList`** object currently has the following fields:

| Field Name          | Required? | JSON Type | Internal Type |
| ------------------- | --------- | --------- | ------------- |
| `LedgerIndex`       | ✔️        | `string`  | `HASH256`     |
| `LedgerEntryType`   | ✔️        | `string`  | `UINT16`      |
| `SignerEntries`     | ✔️        | `array`   | `STARRAY`     |
| `SignerQuorum`      | ✔️        | `number`  | `UINT32`      |
| `SignerListID`      | ✔️        | `number`  | `UINT32`      |
| `OwnerNode`         | ✔️        | `string`  | `UINT64`      |
| `PreviousTxnID`     | ✔️        | `string`  | `HASH256`     |
| `PreviousTxnLgrSeq` | ✔️        | `number`  | `UINT32`      |

The ledger index of this object is calculated by hashing together the owner's account ID with the value of `0`.

The only field whose usage is changing is `SignerListID`. All other fields will be used the same as they are now.

#### 2.1.1. `SignerListID`

This field is currently always set to `0`. The original [`Multisign` implementation](https://xrpl.org/known-amendments.html#multisign) only allowed for one signer list per account, but left the door open for the possibility of more.

We propose that this field is instead used for the transaction type that the signer is allowed to sign for, with `0` being the value for the global signer list (to ensure backwards compatibility). There is enough space in `SignerListID` for this field, because `TxType` is a `UInt16` and `SignerListID` is a `UInt32`. Since the `UInt32` is so much larger than the `UInt16`, there is extra room in the valid values for additional signer list usage proposals. The value of this field will also be used in the `index` calculation.

One problem: `Payment` has transaction type `0`, which would conflict with the global signer list. To get around that, we will instead use `1+TxType` in the `SignerListID` field. It is then very easy to check whether a multisign transaction is valid: the code can check the global signer list (look at the signer list with index `account + 0`), and the transaction-type-specific signer list (look at the signer list with index `account + (1+TxType)`).

Each additional `SignerList` that an account owns will, of course, cost an additional owner reserve (2 XRP at the time of writing).

## 3. Transaction: **`SignerListSet`**

The [`SignerListSet` transaction](https://xrpl.org/signerlistset.html) already exists on the XRPL. We propose a slight modification to support per-transaction-type signer lists.

### 3.1. Fields

As a reference, the **`SignerListSet`** transaction already has the following fields:

| Field Name        | Required? | JSON Type | Internal Type |
| ----------------- | --------- | --------- | ------------- |
| `TransactionType` | ✔️        | `string`  | `UInt16`      |
| `SignerEntries`   | ✔️        | `array`   | `STARRAY`     |
| `SignerQuorum`    | ✔️        | `number`  | `UInt32`      |

We propose adding a new optional field:
| Field Name | Required? | JSON Type | Internal Type |
|------------|-----------|-----------|---------------|
|`TransactionTypeBitmask` | |`array`|`HASH256`

#### 3.1.1. `TransactionTypeBitmask`

This field accepts a bitmask of transaction types, much like the [`HookOn` field](https://xrpl-hooks.readme.io/docs/hookon-field). A `0` bit is "on" and a `1` bit is "off". A value of `0` changes the global signer list. All other values change the many signer lists of the transactions they apply to, so that it is easier to modify many signer lists at once. The JSON will show a list of transactions.

## 4. Security

One important fact to remember is that any signer list that can sign transactions can drain the account's XRP via fees. This was why multiple signer lists were never implemented originally. There is [an open issue](https://github.com/XRPLF/rippled/issues/4476) proposing potential ways to prevent accidental high fees on transactions.

Also, any signer list that is added to `SignerListSet` can effectively give themselves powers over any other transaction(s) they desire.

# Appendix

## Appendix A: FAQ

### A.1: Should global signer lists still be able to send transactions that have specific signer lists enabled?

Yes, because global signer lists should be able to act exactly like master and regular keys. This proposal does not support changing that.

### A.2: Why not also use a bitmask for storage?

This design was strongly considered, but this spec is easier to use and understand. See Appendix B for more details.

### A.3: Why not just take a transaction type in the `TransactionTypeBitmask` field?

That was part of the original design, because it would be more user-friendly and easier to read. It was changed to allow accounts to modify multiple signer lists with one transaction.

### A.4: Can you remove the global signer list after removing the master and regular key?

No, you need to go through the standard blackhole procedure (setting the regular key to `ACCOUNT_ZERO`).

Theoretically, an account could only have a specific signer list on at least one of `SignerListSet`/`SetRegularKey`/`AccountSet` so that the blackholing can be changed. However, this addition seems unnecessary since the standard blackhole procedure already exists.

### A.5: Why not use crypto-conditions?

This was briefly considered, but we decided to go with this design instead. See Appendix C for more details.

## Appendix B: Bitmasks for `SignerListID`

Another design we developed (and seriously considered) was using a bitmask to determine which transaction types a signer list could sign for. This took inspiration from the [`HookOn` field](https://xrpl-hooks.readme.io/docs/hookon-field) in the hooks proposal.

The ledger modifications necessary for this design:

- The ledger object hash (`index`) is now derived from the sequence of the transaction that created the signer list (similar to how escrow hashes are derived). This sequence is stored in the `SignerListID` field.
- Modifying or deleting a signer list that isn't the global one (instead of creating a new one) requires specifying the `SignerListID` in the `SignerListSet` transaction.
- Using a signer list that isn't the global one requires specifying the `SignerListID` in the transaction (a new global optional field).

Ultimately, due to the pros and cons, we decided against this spec. If you have strong feelings about this design (positive _or_ negative), please comment, because it's still in consideration.

### B.1. Pros and Cons

**Existing Spec**

- Pros
  - Ease of use and understandability - same as existing processes
  - Only one signer list can access each transaction (technically two if you include the global signer list)
- Cons
  - One signer list per transaction, even if the same signer list is used for multiple transactions
  - One reserve per transaction
  - Only one signer list can access each transaction

**Bitmask**

- Pros
  - One signer list object regardless of how many transactions it controls (easier on ledger resources)
  - One reserve per signer list
  - Multiple signer lists can access each transaction
- Cons
  - More UX changes - you need to specify the `SignerListID` in the transaction. This is all less compatible with the existing UX for the global signer list.
  - Multiple signer lists can access each transaction (this could get messy and is more difficult to keep track of)
  - A larger change to the current usage of signer lists
  - What happens if/when we reach 256 transactions?

## Appendix C: Crypto-Conditions

Using crypto-conditions for implementing per-transaction-type multisign was considered, but it seemed overly complex for the use-cases that people have. If a crypto-condition-based multisign approach is implemented, it should probably be integrated into all signatures, and apply to both multi-sign _and_ single-sign.
