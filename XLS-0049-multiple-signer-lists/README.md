<pre>
  xls: 49
  title: Multiple Signer Lists
  description: A proposal to enable multiple signer lists per account on the XRP Ledger, allowing different signer lists to authorize specific transaction types.
  author: Mayukha Vadari <mvadari@ripple.com>
  proposal-from: https://github.com/XRPLF/XRPL-Standards/discussions/144
  status: Draft
  category: Amendment
  requires: 74
  created: 2023-11-13
  updated: 2026-02-20
</pre>

# Multiple Signer Lists

## 1. Abstract

The XRP Ledger currently only supports one global signer list per account. However, many users (such as token issuers) require more granularity. For example, they might want to have one signer list with the ability to mint new tokens, and another signer list with the ability to create and edit trustlines.

This document describes a proposal for supporting multiple signer lists per account. The current system of global signer lists will continue to be supported, but we propose adding **per-transaction-type signer lists**. Accounts can set up signer lists that only have the power to send **transactions of one specific type** on behalf of the account.

## 2. Motivation

Global signer lists provide an "all or nothing" model of access control: any key that can sign for an account can submit all transaction types on its behalf. For complex operational setups, especially for issuers and institutional users, this makes it difficult to separate duties such as minting, trustline management, or account configuration.

Supporting multiple signer lists per account, each scoped to a specific transaction type, enables more granular permissioning. This reduces the blast radius of a compromised signer, and allows organizations to delegate narrowly scoped powers (for example, minting only, or trustline management only) without granting full control over the account.

## 3. Overview

We propose modifying one ledger entry and one transaction:

- `SignerList` ledger entry
- `SignerListSet` transaction

This change will require an amendment.

The important considerations to keep in mind are:

- `rippled` must be able to retrieve all possible signer lists for a transaction type quickly and easily, in order to check if a transaction has a valid multisign list.
- Any signer list that can sign transactions can drain the account's XRP via fees.

## 4. Ledger Entry: `SignerList`

There is no change to the shape of a [`SignerList` ledger entry](https://xrpl.org/signerlist.html), only in how it's used.

This amendment repurposes the `SignerListID` field and generalizes how the ledger index is derived so that multiple signer lists can coexist for a single account.

### 4.1. Object Identifier

Existing `SignerList` entries use an object identifier derived from the owner's account ID and a selector value of `0`. This amendment preserves that identifier for the global signer list (`SignerListID = 0`) and introduces additional identifiers of the form `account + (1 + TxType)` for per-transaction-type signer lists. The underlying tagged-hash key space for `SignerList` entries is unchanged.

### 4.2. Fields

For the complete list of fields, types, and defaults, see the canonical [`SignerList` ledger entry documentation](https://xrpl.org/docs/references/protocol/ledger-data/ledger-entry-types/signerlist#signerlist-fields). This amendment does not add or remove any `SignerList` fields; it only changes how the existing `SignerListID` field is interpreted, as described in §4.2.1.

#### 4.2.1. `SignerListID`

This field is currently always set to `0`. The original [`Multisign` implementation](https://xrpl.org/known-amendments.html#multisign) only allowed for one signer list per account, but left the door open for the possibility of more.

Under this amendment, `SignerListID` is used to scope signer lists:

- `SignerListID = 0` denotes the global signer list for an account (backwards compatible with existing behavior).
- For each transaction type with serialized type code `TxType` (a `UInt16`), the per-transaction-type signer list for that transaction type uses `SignerListID = 1 + TxType`.

There is enough space in `SignerListID` for this mapping because `TxType` is a `UInt16` and `SignerListID` is a `UInt32`. Since the `UInt32` is so much larger than the `UInt16`, there is extra room in the valid values for additional signer list usage proposals.

One problem: `Payment` has transaction type `0`, which would conflict with the global signer list. Using `1 + TxType` in the `SignerListID` field avoids this collision. It is then very easy to check whether a multisign transaction is valid: the code can check the global signer list (look at the signer list with index `account + 0`), and the transaction-type-specific signer list (look at the signer list with index `account + (1 + TxType)`).

Each additional `SignerList` that an account owns will, of course, cost an additional owner reserve (2 XRP at the time of writing).

### 4.3. Invariants

- `<entry>.SignerQuorum > 0` implies `<entry>.SignerEntries` is non-empty and the sum of all `SignerWeight` values in `<entry>.SignerEntries` is greater than or equal to `<entry>.SignerQuorum`, and likewise for `<entry>'`.
- For any update to an existing `SignerList` entry, `<entry>.SignerListID == <entry>'.SignerListID`; the scope of a signer list (global vs. per-transaction-type) does not change in-place.

### 4.4. Example JSON

```json
{
  "LedgerEntryType": "SignerList",
  "Flags": 0,
  "OwnerNode": "0000000000000000",
  "PreviousTxnID": "FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF",
  "PreviousTxnLgrSeq": 12345678,
  "SignerQuorum": 3,
  "SignerEntries": [
    {
      "Account": "rExampleSigner1XXXXXXXXXXXXXXXX",
      "SignerWeight": 1
    },
    {
      "Account": "rExampleSigner2XXXXXXXXXXXXXXXX",
      "SignerWeight": 2
    }
  ],
  "SignerListID": 1
}
```

## 5. Transaction: `SignerListSet`

The [`SignerListSet` transaction](https://xrpl.org/signerlistset.html) already exists on the XRPL. This amendment extends it to support per-transaction-type signer lists.

### 5.1. Fields

For the existing fields and validation rules, see the canonical [`SignerListSet` transaction documentation](https://xrpl.org/docs/references/protocol/transactions/types/signerlistset#signerlistset-fields). This amendment adds a single new optional field:

| Field Name               | Required? | JSON Type | Internal Type | Default Value | Description                                                                                                                                                                                 |
| ------------------------ | --------- | --------- | ------------- | ------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `TransactionTypeBitmask` | No        | `array`   | `HASH256`     | `N/A`         | Bitmask of transaction types this change applies to; JSON is a list of transaction type names. `0` updates the global signer list; other values map to scoped lists as defined in this XLS. |

#### 5.1.1. `TransactionTypeBitmask`

This field accepts a bitmask of transaction types, much like the [`HookOn` field](https://xrpl-hooks.readme.io/docs/hookon-field). A `0` bit is "on" and a `1` bit is "off". A value of `0` changes the global signer list (`SignerListID = 0`). All other values change the many signer lists of the transactions they apply to, so that it is easier to modify many signer lists at once. The JSON representation shows this field as a list of transaction types.

### 5.2. Failure Conditions

#### 5.2.1. Data Verification

1. `TransactionTypeBitmask` is present but is not an array, contains elements that are not valid transaction type identifiers, or decodes to a malformed bitmask (implementation-defined `tem`-class error code).

#### 5.2.2. Protocol-Level Failures

1. Applying the requested changes would require creating additional `SignerList` entries but the account does not hold enough XRP to meet the resulting owner reserve requirement for all affected lists (implementation-defined `tec`-class error code).

### 5.3. State Changes

On success (`tesSUCCESS`):

- If `TransactionTypeBitmask` is not present, the transaction behaves as the existing `SignerListSet` transaction: it creates, updates, or removes the global signer list (`SignerListID = 0`) for the account.
- If `TransactionTypeBitmask` is present, the transaction creates, updates, or removes one or more `SignerList` ledger entries whose `SignerListID` values are derived from the selected transaction types (for example, `SignerListID = 1 + TxType` for each enabled transaction type).
- The account's owner directory and owner reserve are updated to reflect any newly created or deleted `SignerList` entries.

### 5.4. Example JSON

```json
{
  "TransactionType": "SignerListSet",
  "Account": "rExampleAccountXXXXXXXXXXXXXXXXX",
  "Fee": "10",
  "Sequence": 12345,
  "SignerQuorum": 3,
  "SignerEntries": [
    {
      "Account": "rExampleSigner1XXXXXXXXXXXXXXXX",
      "SignerWeight": 1
    },
    {
      "Account": "rExampleSigner2XXXXXXXXXXXXXXXX",
      "SignerWeight": 2
    }
  ],
  "TransactionTypeBitmask": ["Payment", "TrustSet"]
}
```

## 6. Rationale

This proposal chooses a straightforward mapping from transaction types to separate `SignerList` entries: `SignerListID = 0` represents the existing global signer list, while `SignerListID = 1 + TxType` represents a signer list scoped to a single transaction type. This design keeps lookup logic simple, preserves existing semantics for the global list, and minimizes UX changes for wallets and other tooling.

Alternative designs, such as encoding permissions via a bitmask in `SignerListID` or implementing per-transaction-type multisign using crypto-conditions, were considered. These alternatives offer additional flexibility but introduce more complexity and larger changes to transaction formats and signing workflows. They are described in more detail in Appendix B and Appendix C.

## 7. Backwards Compatibility

Existing signer lists with `SignerListID = 0` continue to function as global signer lists and retain their current behavior. No changes are required for accounts that only use a single global signer list.

Per-transaction-type signer lists are added in a backward-compatible way by assigning nonzero `SignerListID` values derived from `1 + TxType`. Existing ledger entries and transactions remain valid, and transactions that do not use the new functionality behave exactly as before. Each additional signer list still consumes an owner reserve, as described above.

## 8. Security Considerations

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

- The ledger entry hash (`index`) is now derived from the sequence of the transaction that created the signer list (similar to how escrow hashes are derived). This sequence is stored in the `SignerListID` field.
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
