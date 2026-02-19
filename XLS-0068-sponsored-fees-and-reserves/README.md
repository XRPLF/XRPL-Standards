<pre>
  xls: 68
  title: Sponsored Fees and Reserves
  description: Allow an account to fund fees and reserves on behalf of another account
  author: Mayukha Vadari (@mvadari)
  category: Amendment
  status: Draft
  proposal-from: https://github.com/XRPLF/XRPL-Standards/discussions/196
  requires: XLS-74
  created: 2024-05-02
  updated: 2026-01-30
</pre>

# Sponsored Fees and Reserves

## 1. Abstract

This proposal adds a process for users to maintain control over their keys and account, but to have another account (e.g. a platform) submit the transaction and pay the transaction fee and/or reserves on their behalf. This proposal supports both account and object reserves.

Similar features on other chains are often called "sponsored transactions", "meta-transactions", or "relays".

## 2. Motivation

As the blockchain industry grows, many projects want to be able to build on the blockchain, but abstract away the complexities of using the blockchain - users don't need to submit transactions or deal with transaction fees themselves, they can just pay the platform to handle all that complexity (though, of course, the users still control their own keys).

Some projects also want to onboard users more easily, allowing users to create accounts without needing to pay for their own account reserve or needing to gift accounts free XRP to cover the reserve (this could get rather expensive if it is exploited).

The primary motivation for this design is to enable companies, token issuers, and other entities to reduce onboarding friction for end users by covering transaction fees and reserve requirements on their behalf. Today, users must self-fund both, or companies must essentially donate XRP to users with no controls over how they use it, before interacting with the XRPL. This creates a barrier to entry for use cases such as token distribution, NFT minting, or enterprise onboarding. Sponsorship provides a mechanism for entities with established XRP balances to subsidize these costs while maintaining strong on-chain accountability.

## 3. Overview

Accounts can include signatures from sponsors in their transactions that will allow the sponsors to pay the transaction fee for the transaction, and/or the reserve for any accounts/objects created in the transaction.

Sponsors can also pre-fund fees or reserves, if they do not want to deal with the burden of co-signing every sponsored transaction.

We propose:

- Modifying the ledger entry common fields
- Creating the `Sponsorship` ledger entry
- Modifying the `AccountRoot` ledger entry
- Modifying the `RippleState` ledger entry
- Modifying the transaction common fields
- Creating the `SponsorshipSet` transaction type
- Creating the `SponsorshipTransfer` transaction type
- Modifying the `Payment` transaction type (only flags)
- Modifying the `AccountDelete` transaction type (behavior only, not fields)
- Adding two additional granular permissions (`SponsorFee`, `SponsorReserve`)

In addition, there will be a modification to the `account_objects` RPC method, and a new Clio RPC method called `account_sponsoring`.

This feature will require an amendment, tentatively titled `Sponsor`.

### 3.1. Terminology

- **Sponsor**: The account that is covering the reserve or paying the transaction fee on behalf of another account.
- **Sponsee**: The account that the sponsor is paying a transaction fee or reserve on behalf of.
- **Owner**: The account that owns a given object (or the account itself). This is often the same as the sponsee.
- **Sponsored account**: An account that a sponsor is covering the reserve for (currently priced at 1 XRP).
- **Sponsored object**: A non-account ledger object that a sponsor is covering the reserve for (currently priced at 0.2 XRP).
- **Sponsor relationship**: The relationship between a sponsor and sponsee.
- **Sponsorship type**: The "type" of sponsorship - sponsoring transaction fees vs. sponsoring reserves.

### 3.2. The Sponsorship Flow (Not Pre-Funded)

In this scenario, the sponsor, Spencer, wants to pay the transaction fee and/or reserve for the sponsee Alice's transaction.

- Alice constructs her transaction and autofills it (so that all fields, including the fee and sequence number, are included in the transaction). She adds Spencer's account and sponsorship type to the transaction as well.
- Spencer signs the transaction and provides his signature to Alice.
- Alice adds Spencer's public key and signature to her transaction.
- Alice signs and submits her transaction as normal.

### 3.3. The Sponsorship Flow (Pre-Funded)

In this scenario, the sponsor, Spencer, wants to pay the transaction fee and/or reserve for the sponsee Alice's transaction, but would prefer to pre-fund the XRP necessary, so that he does not have to co-sign every single one of Alice's transactions.

- Spencer submits a transaction to initialize the sponsorship relationship and pre-fund Alice's sponsorship (note: these funds are not sent directly to Alice. She may only use the allocated funds for fees and reserves, and these are separate buckets).
  - Alice does not need to do anything to accept this.
- Alice constructs her transaction and autofills it (so that all fields, including the fee and sequence number, are included in the transaction). She adds Spencer's account and sponsorship type to the transaction as well.
- Alice signs and submits her transaction as normal.

_Note that Spencer does not need to be a part of Alice's signing and submission flow in this example._

### 3.4. Recouping a Sponsored Object Reserve

In this scenario, the sponsor, Spencer, would like to re-obtain the reserve that is currently trapped due to his sponsorship of Alice's object.

Spencer can submit a `SponsorshipTransfer` transaction, which allows him to pass the onus of the reserve back to Alice, or pass it onto another sponsor.

### 3.5. Recouping a Sponsored Account Reserve

In this scenario, the sponsor, Spencer, would like to retrieve his reserve from sponsoring Alice's account.

There are two ways in which he could do this:

- If Alice is done using her account, she can submit an `AccountDelete` transaction, which will send all remaining funds in the account back to Spencer.
- If Alice would like to keep using her account, or would like to switch to a different provider, she (or Spencer) can submit a `SponsorshipTransfer` transaction to either remove sponsorship or transfer it to the new provider.

## 4. Ledger Entries: Common Fields

This section describes the changes to the common fields of ledger entries, to indicate whether or not they are sponsored, and if so, who the sponsor is.

### 4.1. Fields

As a reference, here are the fields that all ledger objects currently have:

| Field Name        | Constant? | Required? | Default Value | JSON Type | Internal Type | Description                             |
| ----------------- | --------- | --------- | ------------- | --------- | ------------- | --------------------------------------- |
| `LedgerEntryType` | ✔️        | ✔️        | N/A           | `string`  | `UInt16`      | The type of ledger entry.               |
| `Flags`           | ✔️        | ✔️        | N/A           | `number`  | `UInt16`      | Set of bit-flags for this ledger entry. |

This spec proposes one additional field:

| Field Name | Constant? | Required? | Default Value | JSON Type | Internal Type | Description                                                                                                                                                                        |
| ---------- | --------- | --------- | ------------- | --------- | ------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `Sponsor`  |           |           | N/A           | `string`  | `AccountID`   | The sponsor paying the owner reserve for a given ledger object. When present, it indicates that the reserve burden for that object has been shifted from the owner to the sponsor. |

### 4.2. Ownership

Any sponsored object is still owned by the original owner, and the sponsor is not added as an additional owner.

### 4.3. Invariant Checks

#### 4.3.1. Allowed Ledger Entry Types

The `Sponsor` field **may** appear on the following ledger entry types:

- `AccountRoot` (for account reserve sponsorship)
- `Offer`
- `Escrow`
- `Check`
- `PayChannel`
- `DepositPreauth`
- `Ticket`
- `NFTokenPage`
- `NFTokenOffer`
- `AMM`
- `Bridge`
- `XChainOwnedClaimID`
- `XChainOwnedCreateAccountClaimID`
- `DID`
- Any other ledger entry type that contributes to an account's owner reserve, subject to implementation details

The `Sponsor` field **must not** appear on:

- `RippleState` objects (they instead use the `HighSponsor` and `LowSponsor` fields defined in section 7.1)
- `DirectoryNode` objects (these do not have reserves)
- `Amendments` objects (global ledger objects)
- `FeeSettings` objects (global ledger objects)
- `NegativeUNL` objects (global ledger objects)

#### 4.3.2. Constraints

- The field **must** be omitted when there is no sponsor.
- When present, the field **must** contain a valid `AccountID` that exists on the ledger.
- The field is added when sponsorship is established (either at object creation or via `SponsorshipTransfer`).
- The field is removed when sponsorship is dissolved via `SponsorshipTransfer`.
- The `Sponsor` must have a `SponsoringOwnerCount` that is greater than 0.
- The `Sponsor` value **must** differ from the object's owner (as indicated by the `Owner` or `Account` field). An account **may not** sponsor its own objects.
- The sponsor account **must** have sufficient XRP to meet its reserve requirements when creating/sponsoring new objects, including reserves for all objects and accounts it sponsors.

_NOTE: A sponsor may also be a sponsee._

#### 4.3.4. Authoritative Indication

The presence or absence of `Sponsor` is the authoritative indication of whether an object is sponsored for reserves. The presence of this field triggers the following behaviors:

- The object's reserve is counted against the sponsor's `SponsoringOwnerCount` (or `SponsoringAccountCount` for `AccountRoot`), not the owner's `OwnerCount`.
- The sponsor's `SponsoringOwnerCount` (or `SponsoringAccountCount` for `AccountRoot`) is incremented.
- The owner's `SponsoredOwnerCount` is incremented (for non-`AccountRoot` objects).
- The reserve calculation for both sponsor and owner accounts is adjusted accordingly.

_NOTE: These values are likely not recalculated later due to performance issues, and the implementation should make sure that the `SponsoringOwnerCount`, `SponsoredOwnerCount`, and `SponsoringAccountCount` fields in all accounts are updated appropriately. The accuracy will only be verifiable via off-chain mechanisms._

## 5. Ledger Entry: `Sponsorship`

`Sponsorship` is an object that reflects a sponsoring relationship between two accounts, `Sponsor` and `Sponsee`. This allows sponsors to "pre-fund" sponsees, if they so desire.

_Note: this object does not need to be created in order to sponsor accounts. It is an offered convenience, so that sponsors do not have to co-sign every sponsored transaction if they don't want to, especially for transaction fees. It also allows them to set a maximum balance even if they still want to co-sign transactions._

### 5.1. Object Identifier

#### 5.1.1. Key Space

The `Sponsorship` ledger entry uses a dedicated key space constant `spaceSponsorship`, which will be assigned a unique 16-bit value during implementation (e.g., `0x0053` or another available value in the key space range).

#### 5.1.2. ID Calculation Algorithm

The unique identifier for a `Sponsorship` object is calculated using [`SHA512-Half`](https://xrpl.org/docs/references/protocol/data-types/basic-data-types/#hashes) of the following values concatenated in order:

1. The `Sponsorship` space key (`'>'`)
2. The `AccountID` of the `Owner` (sponsor)
3. The `AccountID` of the `Sponsee`

This ensures that there can be at most one `Sponsorship` object per sponsor-sponsee pair, preventing duplicate relationships.

### 5.2. Fields

| Field Name          | Constant? | Required? | Default Value | JSON Type | Internal Type | Description                                                                                                                                            |
| ------------------- | --------- | --------- | ------------- | --------- | ------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `LedgerEntryType`   | ✔️        | ✔️        | N/A           | `string`  | `UInt16`      | The value `"Sponsorship"` (JSON) or a unique numeric value (internal, assigned during implementation) indicates this is a `Sponsorship` ledger object. |
| `Flags`             |           |           | `0`           | `number`  | `UInt32`      | A bit-map of boolean flags enabled for this object.                                                                                                    |
| `Owner`             | ✔️        | ✔️        | N/A           | `string`  | `AccountID`   | The sponsor associated with this relationship. This account also pays for the reserve of this object.                                                  |
| `Sponsee`           | ✔️        | ✔️        | N/A           | `string`  | `AccountID`   | The sponsee associated with this relationship.                                                                                                         |
| `FeeAmount`         |           |           |               | `string`  | `Amount`      | The (remaining) amount of XRP that the sponsor has provided for the sponsee to use for fees.                                                           |
| `MaxFee`            |           |           | N/A           | `string`  | `Amount`      | The maximum fee per transaction that will be sponsored. This is to prevent abuse/excessive draining of the sponsored fee pool.                         |
| `ReserveCount`      |           |           | `0`           | `string`  | `UInt32`      | The (remaining) number of `OwnerCount` that the sponsor has provided for the sponsee to use for reserves.                                              |
| `OwnerNode`         | ✔️        | ✔️        | N/A           | `string`  | `UInt64`      | A hint indicating which page of the sponsor's owner directory links to this object, in case the directory consists of multiple pages.                  |
| `SponseeNode`       | ✔️        | ✔️        | N/A           | `string`  | `UInt64`      | A hint indicating which page of the sponsee's owner directory links to this object, in case the directory consists of multiple pages.                  |
| `PreviousTxnID`     |           | ✔️        | N/A           | `string`  | `Hash256`     | The identifying hash of the transaction that most recently modified this entry.                                                                        |
| `PreviousTxnLgrSeq` |           | ✔️        | N/A           | `number`  | `UInt32`      | The ledger index that contains the transaction that most recently modified this object.                                                                |

### 5.3. Flags

There are two flags on this object:

| Flag Name                             | Flag Value   | Modifiable? | Description                                                                                                                                                                                                    |
| ------------------------------------- | ------------ | ----------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `lsfSponsorshipRequireSignForFee`     | `0x00010000` | Yes         | If set, indicates that every use of this sponsor for sponsoring fees requires a signature from the sponsor. If unset, no signature is necessary (the existence of the `Sponsorship` object is sufficient).     |
| `lsfSponsorshipRequireSignForReserve` | `0x00020000` | Yes         | If set, indicates that every use of this sponsor for sponsoring reserves requires a signature from the sponsor. If unset, no signature is necessary (the existence of the `Sponsorship` object is sufficient). |

### 5.4. Ownership

The object is owned by `Owner`, who also pays the reserve for this object.

### 5.5. Reserves

**Reserve Requirement:** Standard

The reserve is charged to the sponsor's account (the `Owner` field).

### 5.6. Deletion

#### 5.6.1. Deletion Transactions

`SponsorshipSet` with the `tfDeleteObject` flag

#### 5.6.2. Deletion Conditions

- The `SponsorshipSet` transaction must be submitted by the sponsor (the `Owner` of the `Sponsorship` object).
- The `tfDeleteObject` flag must be enabled.
- No other fields (`FeeAmount`, `MaxFee`, `ReserveCount`, or flag-setting fields) may be specified in the deletion transaction.
- **Note:** Non-zero `FeeAmount` and `ReserveCount` values **are** permitted at deletion time. Any remaining XRP in `FeeAmount` is returned to the sponsor's account upon deletion.

#### 5.6.3. Account Deletion Blocker

This object is a [deletion blocker](https://xrpl.org/docs/concepts/accounts/deleting-accounts/#requirements).

This object must be deleted before its owner account (the sponsor) can be deleted. The sponsor must either:

1. Delete the `Sponsorship` object via `SponsorshipSet` with `tfDeleteObject`, or
2. Wait for the sponsee to delete it (if the sponsee has permission to do so)

**Note on Existing Sponsored Objects:** Deleting a `Sponsorship` object **does not** affect already-sponsored ledger entries or accounts. Those existing sponsored objects/accounts will retain their `Sponsor` field and continue to be sponsored. To dissolve sponsorship for existing objects, the `SponsorshipTransfer` transaction must be used.

### 5.7. Invariants

The following invariants must always hold for a `Sponsorship` object:

- `Owner != Sponsee` (an account cannot create a `Sponsorship` object with itself as both sponsor and sponsee)
- `FeeAmount >= 0` AND `FeeAmount` is denominated in XRP (drops)
- `ReserveCount >= 0`
- At least one of `FeeAmount` and `ReserveCount` must be included
- Both `Owner` and `Sponsee` must be valid `AccountID` values that exist on the ledger

_NOTE: The invariants in [4.3](#43-invariant-checks) also apply to `Sponsorship` objects, as they apply to all objects._

### 5.8. RPC Name

The `snake_case` form of the ledger object name is `sponsorship`.

### 5.9. Example JSON

```json
{
  "LedgerEntryType": "Sponsorship",
  "Owner": "rN7n7otQDd6FczFgLdlqtyMVrn3HMfXpf",
  "Sponsee": "rfkDkFai4jUfCvAJiZ5Vm7XvvWjYvDqeYo",
  "FeeAmount": "1000000", // 1 XRP, 1 million drops
  "MaxFee": "1000", // 1000 drops
  "ReserveCount": 5,
  "Flags": 0,
  "OwnerNode": "0000000000000000",
  "SponseeNode": "0000000000000000",
  "PreviousTxnID": "1234567890ABCDEF1234567890ABCDEF1234567890ABCDEF1234567890ABCDEF",
  "PreviousTxnLgrSeq": 12345678
}
```

## 6. Ledger Entry: `AccountRoot`

An [`AccountRoot` ledger entry](https://xrpl.org/docs/references/protocol/ledger-data/ledger-entry-types/accountroot) type describes a single [account](https://xrpl.org/docs/concepts/accounts), its settings, and XRP balance.

### 6.1. Fields

As a reference, [here](https://xrpl.org/docs/references/protocol/ledger-data/ledger-entry-types/accountroot#accountroot-fields) are the fields that the `AccountRoot` ledger object currently has.

This spec proposes these additional fields:

| Field Name               | Constant? | Required? | Default Value | JSON Type | Internal Type | Description                                                                   |
| ------------------------ | --------- | --------- | ------------- | --------- | ------------- | ----------------------------------------------------------------------------- |
| `Sponsor`                |           |           | N/A           | `string`  | `AccountID`   | The sponsor that is paying the account reserve for this account.              |
| `SponsoredOwnerCount`    |           |           | `0`           | `number`  | `UInt32`      | The number of objects the account owns that are being sponsored by a sponsor. |
| `SponsoringOwnerCount`   |           |           | `0`           | `number`  | `UInt32`      | The number of objects the account is sponsoring the reserve for.              |
| `SponsoringAccountCount` |           |           | `0`           | `number`  | `UInt32`      | The number of accounts that the account is sponsoring the reserve for.        |

#### 6.1.1. `Sponsor`

The `Sponsor` field is already added in the ledger common fields (see section [4.1](#41-fields)), but it has some additional rules associated with it on the `AccountRoot` object.

This field is included if the account was created with a sponsor paying its account reserve. If this sponsored account is deleted, the destination of the `AccountDelete` transaction must equal `Sponsor`, so that the sponsor can recoup their fees.

_Note: The `Destination` field of `AccountDelete` will still work as-is if the account is not sponsored, where it can be set to any account._

### 6.2. Account Reserve Calculation

The existing reserve calculation is:

$$ acctReserve + objReserve \* acct.OwnerCount $$

The total account reserve should now be calculated as:

$$
\displaylines{
(acct.Sponsor \text{ ? } 0 : acctReserve) +
objReserve * (acct.OwnerCount + acct.SponsoringOwnerCount - acct.SponsoredOwnerCount) +
acctReserve * acct.SponsoringAccountCount
}
$$

### 6.3. Invariants

The following invariants must hold for `AccountRoot` objects with sponsorship fields:

- `SponsoredOwnerCount <= OwnerCount` (cannot have more sponsored objects than total owned objects)
- If `Sponsor` is present, it must be a valid `AccountID` that exists on the ledger
- The reserve calculation must always result in a non-negative value
- The `Sponsor`'s `SponsoringAccountCount` must be greater than 0

**Global Invariant (referenced in section 18.2):**

Across all accounts in the ledger:
$$\sum_{accounts} SponsoredOwnerCount = \sum_{accounts} SponsoringOwnerCount$$

This ensures that every sponsored object is properly accounted for on both the sponsee and sponsor sides.

### 6.4. Example JSON

```json
{
  "LedgerEntryType": "AccountRoot",
  "Account": "rfkDkFai4jUfCvAJiZ5Vm7XvvWjYvDqeYo",
  "Balance": "100000000", // 100 XRP, in drops
  "OwnerCount": 5,
  "Sponsor": "rN7n7otQDd6FczFgLdlqtyMVrn3HMfXpf",
  "SponsoredOwnerCount": 2,
  "SponsoringOwnerCount": 1,
  "SponsoringAccountCount": 1,
  "PreviousTxnID": "1234567890ABCDEF1234567890ABCDEF1234567890ABCDEF1234567890ABCDEF",
  "PreviousTxnLgrSeq": 12345679
}
```

## 7. Ledger Entry: `RippleState`

A `RippleState` ledger entry represents a [trust line](https://xrpl.org/docs/concepts/tokens/fungible-tokens) between two accounts. Each account can change its own limit and other settings, but the balance is a single shared value. A trust line that is entirely in its default state is considered the same as a trust line that does not exist and is automatically deleted. You can create or modify a trust line with a [TrustSet transaction](https://xrpl.org/docs/references/protocol/transactions/types/trustset).

### 7.1. Fields

As a reference, [here](https://xrpl.org/docs/references/protocol/ledger-data/ledger-entry-types/ripplestate#ripplestate-fields) are the fields that the `RippleState` ledger object currently has.

This spec proposes these additional fields:

| Field Name    | Constant? | Required? | Default Value | JSON Type | Internal Type | Description                                                                              |
| ------------- | --------- | --------- | ------------- | --------- | ------------- | ---------------------------------------------------------------------------------------- |
| `HighSponsor` |           |           | N/A           | `string`  | `AccountID`   | The sponsor that is paying the reserve on behalf of the "high" account on the trustline. |
| `LowSponsor`  |           |           | N/A           | `string`  | `AccountID`   | The sponsor that is paying the reserve on behalf of the "low" account on the trustline.  |

These additional fields are necessary for a trustline since the reserve for this object may be held by two accounts (in the case of a bidirectional trustline).

### 7.2. Invariants

Existing invariants remain.

- The common field `Sponsor` **must not** be on any `RippleState` objects (they must use `HighSponsor` and `LowSponsor` instead).
- If `LowSponsor` is included, `lsfLowReserve` **must** be enabled.
- If `HighSponsor` is included, `lsfHighReserve` **must** be enabled.

_NOTE: The invariants in [4.3](#43-invariant-checks) also apply to `RippleState` objects, as they apply to all objects._

### 7.3. Example JSON

```json
{
  "LedgerEntryType": "RippleState",
  "Balance": {
    "currency": "USD",
    "issuer": "rLowAccountAddressXXXXXXXXXXXXXXX",
    "value": "-10"
  },
  "HighLimit": {
    "currency": "USD",
    "issuer": "rHighAccountAddressXXXXXXXXXXXXXX",
    "value": "100"
  },
  "LowLimit": {
    "currency": "USD",
    "issuer": "rLowAccountAddressXXXXXXXXXXXXXXX",
    "value": "0"
  },
  "HighSponsor": "rN7n7otQDd6FczFgLdlqtyMVrn3HMfXpf",
  "LowSponsor": "rN7n7otQDd6FczFgLdlqtyMVrn3HMfXpf",
  "Flags": 262144,
  "HighNode": "0000000000000000",
  "LowNode": "0000000000000000",
  "PreviousTxnID": "ABCDEF0123456789ABCDEF0123456789ABCDEF0123456789ABCDEF0123456789",
  "PreviousTxnLgrSeq": 12345680
}
```

## 8. Transactions: Common Fields

### 8.1. Fields

As a reference, [here](https://xrpl.org/docs/references/protocol/transactions/common-fields/) are the fields that all transactions currently have.

We propose these modifications:

| Field Name         | Required? | JSON Type | Internal Type | Description                                                                                                                                                           |
| ------------------ | --------- | --------- | ------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `Sponsor`          |           | `string`  | `AccountID`   | The sponsoring account.                                                                                                                                               |
| `SponsorFlags`     |           | `number`  | `UInt32`      | Flags on the sponsorship, indicating what type of sponsorship this is (fee vs. reserve).                                                                              |
| `SponsorSignature` |           | `object`  | `STObject`    | This field contains all the signing information for the sponsorship happening in the transaction. It is included if the transaction is fee- and/or reserve-sponsored. |

##### 8.1.1. `SponsorFlags`

The `SponsorFlags` field allows the user to specify which sponsorship type(s) they wish to participate in. This field **must** be included if the `Sponsor` field is included in a transaction, and at least one flag **must** be specified if the `Sponsor` field is included in a transaction. The `SponsorFlags` field **must not** be included if the `Sponsor` field is not included in a transaction.

There are two flag values that are supported:

| Flag Name          | Flag Value   | Description                                                        |
| ------------------ | ------------ | ------------------------------------------------------------------ |
| `tfSponsorFee`     | `0x00000001` | Sponsoring (paying for) the fee of the transaction.                |
| `tfSponsorReserve` | `0x00000002` | Sponsoring the reserve for any objects created in the transaction. |

#### 8.1.2 `SponsorSignature`

| Field Name      | Required? | JSON Type | Internal Type | Description                                                                                                                                           |
| --------------- | --------- | --------- | ------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------- |
| `SigningPubKey` |           | `string`  | `STBlob`      | The `SigningPubKey` for `Sponsor`, if single-signing.                                                                                                 |
| `TxnSignature`  |           | `string`  | `STBlob`      | A signature of the transaction from the sponsor, to indicate their approval of this transaction, if single-signing.                                   |
| `Signers`       |           | `array`   | `STArray`     | An array of signatures of the transaction from the sponsor's signers to indicate their approval of this transaction, if the sponsor is multi-signing. |

##### 8.1.2.1. `SigningPubKey`, `TxnSignature` and `Signers`

Either `TxnSignature` or `Signers` must be included in the final transaction.

There will be no additional transaction fee required for the use of the `TxnSignature` field.

`TxnSignature` and `Signers` **will not** be signing fields (they will not be included in transaction signatures, though they will still be included in the stored transaction).

Either `SigningPubKey`+`TxnSignature` or `Signers` must be included in the transaction. There is one exception to this: if `lsfRequireSignatureForFee`/`lsfRequireSignatureForReserve` are not enabled for the type(s) of sponsorship in the transaction.

### 8.2. Transaction Fee

If the `SponsorSignature.Signers` field is necessary, then the total fee of the transaction will be increased, due to the extra signatures that need to be processed. This is similar to the additional fees for [multisigning](https://xrpl.org/docs/concepts/accounts/multi-signing/). The minimum fee will be $(|signatures|+1)*base\textunderscore fee$.

The total fee calculation for signatures will now be $( 1+|tx.Signers| + |tx.SponsorSignature.Signers|) * base\textunderscore fee$ (plus transaction-specific fees).

### 8.3. Failure Conditions

#### 8.3.1. General Failures

1. `SponsorSignature.TxnSignature` is invalid.
1. `SponsorSignature.Signers` is invalid (the signer list isn't on the account, quorum isn't reached, the public key(s) are invalid, or signature(s) are invalid).
1. `SponsorSignature.SigningPubKey` is invalid (the public key doesn't match the account's master key or regular key, or the public key is otherwise invalid).
1. The `Sponsor` doesn't exist on the ledger.
1. An invalid sponsorship flag is used.
1. `SponsorSignature.SigningPubKey`, `SponsorSignature.TxnSignature`, and `SponsorSignature.Signers` are all included (or other incorrect combinations of signing fields).
1. `Sponsor`, `SponsorFlags`, or `SponsorSignature` is included in a transaction that does not support sponsorship (see section [8.3.4](#834-transactions-that-cannot-be-sponsored)).
1. Only one or two of `Sponsor`, `SponsorFlags`, and `SponsorSignature` is included (they must either all be included, if the transaction is sponsored, or none, if it is not).
1. `SponsorFlags` includes invalid flags (currently, the only two valid flags are `tfSponsorFee` and `tfSponsorReserve`).

#### 8.3.2. Fee Sponsorship Failures

1. The sponsor's account does not have enough XRP to cover the sponsored transaction fee (`telINSUF_FEE_P`)

If a `Sponsorship` object exists:

1. The `lsfRequireSignatureForFee` flag is enabled and there is no sponsor signature included.
1. There is not enough XRP in the `FeeAmount` to pay for the transaction.
1. Paying fees via sponsorship will _not_ be able to [go below the reserve requirement](https://xrpl.org/docs/concepts/accounts/reserves#going-below-the-reserve-requirement).
1. The fee in `tx.Fee` is greater than `Sponsorship.MaxFee`

If a `Sponsorship` object does not exist:

1. There is no sponsor signature included.

Note: if a transaction doesn't charge a fee (such as an account's first `SetRegularKey` transaction), the transaction will still succeed.

#### 8.3.3. Reserve Sponsorship Failures

1. The sponsor does not have enough XRP to cover the reserve (`tecINSUFFICIENT_RESERVE`)
1. The transaction does not support reserve sponsorship (see section [8.3.4](#834-transactions-that-cannot-be-sponsored))

If a `Sponsorship` object exists:

1. The `lsfRequireSignatureForReserve` flag is enabled and there is no sponsor signature included.
1. There is not enough remaining count in the `ReserveCount` to pay for the transaction.

If a `Sponsorship` object does not exist:

1. There is no sponsor signature included.

Note: if a transaction doesn't charge a reserve (such as `AccountSet`), the transaction will still succeed.

#### 8.3.4. Transactions that cannot be sponsored

All transactions (other than pseudo-transactions) may use the `tfSponsorFee` flag, since they all have a fee.

However, some transactions will not support the `tfSponsorReserve` flag.

- [`Batch` transactions](../XLS-0056-batch/README.md)
  - `Batch` does not create any objects on its own, and therefore its use in the outer transaction would be confusing, as users may think that that means that all inner transactions are sponsored. The inner transactions should use `tfSponsorReserve` instead.
- All [pseudo-transactions](https://xrpl.org/docs/references/protocol/transactions/pseudo-transaction-types/pseudo-transaction-types) (currently `EnableAmendment`, `SetFee`, and `UNLModify`)
  - The fees and reserves for those objects are covered by the network, not by any one account.

Also, many transactions, such as `AccountSet`, will have no change in output when using the `tfSponsorReserve` flag, if they do not create any new objects or accounts.

### 8.4. State Changes

#### 8.4.1. Fee Sponsorship State Changes

If a `Sponsorship` object exists, the `tx.Fee` value is decremented from the `Sponsorship.FeeAmount`.

If a `Sponsorship` object does not exist, the `tx.Fee` value is decremented from the sponsor's `AccountRoot.Balance`.

#### 8.4.2. Reserve Sponsorship State Changes

Any account/object that is created as a part of the transaction will have a `Sponsor` field.

The sponsor's `SponsoringOwnerCount` field will be incremented by the number of objects that are sponsored as a part of the transaction, and the `SponsoringAccountCount` field will be incremented by the number of new accounts that are sponsored as a part of the transaction.

The sponsee's `SponsoredOwnerCount` field will be incremented by the number of objects that are sponsored as a part of the transaction.

The `SponsoredOwnerCount`, `SponsoringOwnerCount`, and `SponsoringAccountCount` fields will be decremented when those objects/accounts are deleted.

## 9. Transaction: `SponsorshipSet`

This transaction creates, updates, and deletes the `Sponsorship` object.

### 9.1. Fields

| Field Name        | Required? | JSON Type | Internal Type | Description                                                                                                                                                                                 |
| ----------------- | --------- | --------- | ------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `TransactionType` | ✔️        | `string`  | `UInt16`      | The transaction type (`SponsorshipSet`).                                                                                                                                                    |
| `Account`         | ✔️        | `string`  | `AccountID`   | The account sending the transaction. This may be either the sponsor or the sponsee.                                                                                                         |
| `Flags`           |           | `number`  | `UInt32`      | A bit-map of boolean flags enabled for this transaction. The flags are defined in [section 9.2](#92-flags).                                                                                 |
| `Sponsor`         |           | `string`  | `AccountID`   | The sponsor associated with this relationship. This account also pays for the reserve of this object. If this field is included, the `Account` is assumed to be the `Sponsee`.              |
| `Sponsee`         |           | `string`  | `AccountID`   | The sponsee associated with this relationship. If this field is included, the `Account` is assumed to be the `Sponsor`.                                                                     |
| `FeeAmount`       |           | `string`  | `Amount`      | The (remaining) amount of XRP that the sponsor has provided for the sponsee to use for fees. This value will replace what is currently in the `Sponsorship.FeeAmount` field (if it exists). |
| `MaxFee`          |           | `string`  | `Amount`      | The maximum fee per transaction that will be sponsored. This is to prevent abuse/excessive draining of the sponsored fee pool.                                                              |
| `ReserveCount`    |           | `number`  | `UInt32`      | The (remaining) amount of reserves that the sponsor has provided for the sponsee to use. This value will replace what is currently in the `Sponsorship.ReserveCount` field (if it exists).  |

### 9.2. Flags

| Flag Name                                 | Flag Value   | Description                                                                                                       |
| ----------------------------------------- | ------------ | ----------------------------------------------------------------------------------------------------------------- |
| `tfSponsorshipSetRequireSignForFee`       | `0x00010000` | Adds the restriction that every use of this sponsor for sponsoring fees requires a signature from the sponsor.    |
| `tfSponsorshipClearRequireSignForFee`     | `0x00020000` | Removes the restriction that every use of this sponsor for sponsoring fees requires a signature from the sponsor. |
| `tfSponsorshipSetRequireSignForReserve`   | `0x00040000` | Adds the restriction every use of this sponsor for sponsoring fees requires a signature from the sponsor.         |
| `tfSponsorshipClearRequireSignForReserve` | `0x00080000` | Removes the restriction every use of this sponsor for sponsoring fees requires a signature from the sponsor.      |
| `tfDeleteObject`                          | `0x00100000` | Removes the ledger object.                                                                                        |

### 9.3. Transaction Fee

**Fee Structure:** Standard

This transaction uses the standard transaction fee (currently 10 drops, subject to Fee Voting changes).

### 9.4. Failure Conditions

1. `tx.Account` is not equal to either `tx.Sponsor` or `tx.Sponsee` (`temMALFORMED`)
1. Both `Sponsor` and `Sponsee` are specified (`temMALFORMED`)
1. Neither `Sponsor` nor `Sponsee` is specified (`temMALFORMED`)
1. `Sponsor` is specified (which means that the `Sponsee` is submitting the transaction) and `tfDeleteObject` is not enabled, as only the sponsor can create/update the `Sponsorship` object (`temMALFORMED`)
1. `MaxFee` is less than the base fee or is not denominated in XRP (`temBAD_AMOUNT`)
1. `MaxFee` is greater than `FeeAmount` (`temBAD_AMOUNT`)
1. `FeeAmount` is not denominated in XRP (`temBAD_AMOUNT`)
1. `Sponsor` or `Sponsee` does not exist on the ledger (`terNO_ACCOUNT`)
1. `Owner == Sponsee` (attempting to create self-sponsorship) (`temMALFORMED`)
1. Sponsor does not have sufficient XRP to cover the reserve for the `Sponsorship` object (`tecINSUFFICIENT_RESERVE`)
1. If `tfDeleteObject` is enabled:
1. `FeeAmount` is specified (`temMALFORMED`)
1. `MaxFee` is specified (`temMALFORMED`)
1. `ReserveCount` is specified (`temMALFORMED`)
1. `tfSponsorshipSetRequireSignForFee` is enabled (`temINVALID_FLAG`)
1. `tfSponsorshipSetRequireSignForReserve` is enabled (`temINVALID_FLAG`)
1. `tfSponsorshipClearRequireSignForFee` is enabled (`temINVALID_FLAG`)
1. `tfSponsorshipClearRequireSignForReserve` is enabled (`temINVALID_FLAG`)
1. The `Sponsorship` object does not exist (`tecNO_ENTRY`)

### 9.5. State Changes

If creating a new `Sponsorship` object:

- Create the `Sponsorship` ledger entry with the specified fields
- Increment the sponsor's `OwnerCount` by 1
- Add the object to both the sponsor's and sponsee's owner directories
- Deduct the object reserve from the sponsor's available XRP

If updating an existing `Sponsorship` object:

- Update `Sponsorship.FeeAmount` to `tx.FeeAmount` (or 0 if omitted)
- Update `Sponsorship.MaxFee` to `tx.MaxFee` (or remove field if omitted)
- Update `Sponsorship.ReserveCount` to `tx.ReserveCount` (or 0 if omitted)
- Update flags based on `tfSponsorshipSetRequireSignForFee`, `tfSponsorshipClearRequireSignForFee`, `tfSponsorshipSetRequireSignForReserve`, and `tfSponsorshipClearRequireSignForReserve`
- If `FeeAmount` is increased, deduct the additional XRP from the sponsor's balance
- If `FeeAmount` is decreased, return the difference to the sponsor's balance

If deleting the `Sponsorship` object (`tfDeleteObject` flag):

- Delete the `Sponsorship` ledger entry
- Return all remaining XRP in `FeeAmount` to the sponsor's balance
- Decrement the sponsor's `OwnerCount` by 1
- Remove the object from both the sponsor's and sponsee's owner directories
- Return the object reserve to the sponsor's available XRP

_Note: Deleting a `Sponsorship` object does not affect already-sponsored ledger entries or accounts. Those existing sponsored objects/accounts will retain their `Sponsor` field and continue to be sponsored. To dissolve sponsorship for existing objects, the `SponsorshipTransfer` transaction must be used._

### 9.6. Example JSON

```json
{
  "TransactionType": "SponsorshipSet",
  "Account": "rN7n7otQDd6FczFgLdlqtyMVrn3HMfXpf",
  "Sponsee": "rfkDkFai4jUfCvAJiZ5Vm7XvvWjYvDqeYo",
  "FeeAmount": "1000000",
  "MaxFee": "1000",
  "ReserveCount": 5,
  "Fee": "12",
  "Sequence": 42
}
```

## 10. Transaction: `SponsorshipTransfer`

This transaction transfers a sponsor relationship for a particular ledger object's reserve. The sponsor relationship can either be passed on to a new sponsor, or dissolved entirely (with the sponsee taking on the reserve). Either the sponsor or sponsee may submit this transaction at any point in time.

There are three valid transfer scenarios:

- Transferring from sponsor to sponsee (sponsored to unsponsored)
  - Either the sponsor or sponsee may submit this transaction. Both have the right to end the relationship on that object at any time.
- Transferring from sponsee to sponsor (unsponsored to sponsored)
  - Only the sponsee may submit this transaction. It follows a standard sponsoring flow in terms of signing.
- Transferring from sponsor to new sponsor
  - Only the sponsee may submit this transaction. The old sponsor is not directly involved, and the new sponsor provides their signature via the standard signing flow.

### 10.1. Fields

| Field Name         | Required? | JSON Type | Internal Type | Description                                                                                                                                                           |
| ------------------ | --------- | --------- | ------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `TransactionType`  | ✔️        | `string`  | `UInt16`      | The transaction type (`SponsorshipTransfer`).                                                                                                                         |
| `Account`          | ✔️        | `string`  | `AccountID`   | The account sending the transaction. This may be either the current sponsor or the current sponsee.                                                                   |
| `ObjectID`         |           | `string`  | `Hash256`     | The ID of the object to transfer sponsorship.                                                                                                                         |
| `Sponsor`          |           | `string`  | `AccountID`   | The new sponsor of the object.                                                                                                                                        |
| `SponsorFlags`     |           | `number`  | `UInt32`      | Flags on the sponsorship, indicating what type of sponsorship this is (fee vs. reserve).                                                                              |
| `SponsorSignature` |           | `object`  | `STObject`    | This field contains all the signing information for the sponsorship happening in the transaction. It is included if the transaction is fee- and/or reserve-sponsored. |

#### 10.1.1. `ObjectID`

This field should be included if this transaction is dealing with sponsored object, rather than on a sponsored account. This field indicates which object the relationship is changing for.

If it is not included, then it refers to the account sending the transaction.

#### 10.1.2. `Sponsor`

The `Sponsor` field is already added in the transaction common fields (see section [6.1.1](#611-sponsor)), but it has some additional rules associated with it on the `SponsorshipTransfer` transaction.

In this case, if `Sponsor` is included with the `tfSponsorReserve` flag, then the reserve sponsorship for the provided object will be transferred to the `Sponsor` instead of passing back to the ledger object's owner.

If there is no `Sponsor` field, or if the `tfSponsorReserve` flag is not included, then the burden of the reserve will be passed back to the ledger object's owner (the former sponsee).

### 10.2. Sponsorship Transfer Scenarios

#### 10.2.1. Transferring from Sponsor to Sponsee (Sponsored to Unsponsored)

This scenario ends the sponsorship for a sponsored ledger object or account. The sponsor and sponsee both have the right to end the relationship at any time.

The following fields indicate this scenario:

- `ObjectID` must be included (if sponsored object)
- `Sponsor` must be excluded
- `SponsorFlags.tfSponsorReserve` must be excluded
- The object specified by `ObjectID` must be have a `Sponsor` field

#### 10.2.2. Transferring from Sponsee to Sponsor (Unsponsored to Sponsored)

This scenario sponsors an object or account that was not previously sponsored. Only the sponsee can submit this transaction.

The following fields indicate this scenario:

- `ObjectID` must be included (if sponsored object)
- `Sponsor` must be included
- `SponsorFlags.tfSponsorReserve` must be included
- The object specified by `ObjectID` must **not** have a `Sponsor` field

#### 10.2.3. Transferring from Sponsor to New Sponsor

This scenario migrates the sponsorship for a sponsored object or account to a new sponsor. Only the sponsee can submit this transaction.

The following fields indicate this scenario:

- `ObjectID` must be included (if sponsored object)
- `Sponsor` must be included
- `SponsorFlags.tfSponsorReserve` must be included
- The object specified by `ObjectID` must have a `Sponsor` field

_NOTE: The only difference between this scenario and the one specified in [10.2.2](#1022-transferring-from-sponsee-to-sponsor-unsponsored-to-sponsored) is that in this case, the object specified by `ObjectID` must already have a `Sponsor` field._

#### 10.2.4. Sponsorship Transfer for Accounts

The same 3 scenarios above apply to accounts as well. The only difference is that for accounts, the `ObjectID` field is not included, and instead the `Account` field is used to specify which account the sponsorship is changing for.

### 10.3. Transaction Fee

**Fee Structure:** Standard

This transaction uses the standard transaction fee (currently 10 drops, subject to Fee Voting changes).

### 10.4. Failure Conditions

All failure conditions mentioned in [section 8.3](#83-failure-conditions) still apply here.

Additional failure conditions specific to `SponsorshipTransfer`:

1. `ObjectID` is specified but does not exist on the ledger (`tecNO_TARGET`)
1. `ObjectID` is specified but does not have a `Sponsor` field (object is not sponsored) (`tecNO_PERMISSION`)
1. `ObjectID` is not specified and the `tx.Account` does not have a `Sponsor` field (account is not sponsored) (`tecNO_PERMISSION`)
1. `tx.Account` is neither the current sponsor nor the owner (sponsee) of the object/account specified by `ObjectID` (`tecNO_PERMISSION`)
1. If dissolving the sponsorship (no `Sponsor` field or `tfSponsorReserve` flag not set):
1. The owner does not have enough XRP to cover the reserve for this object/account (`tecINSUFFICIENT_RESERVE`)
1. If creating a new sponsorship (unsponsored to sponsored):
1. The transaction is not submitted by the sponsee (`tecNO_PERMISSION`)
1. The `Sponsor` field or the `SponsorFlags` field is missing (`temMALFORMED`)
1. The `SponsorFlags` field does not include the `tfSponsorReserve` flag (`temINVALID_FLAG`)
1. The new sponsor account does not exist (`terNO_ACCOUNT`)
1. The new sponsor does not have enough XRP to cover the reserve for this object/account (`tecINSUFFICIENT_RESERVE`)
1. If transferring the sponsorship to a new sponsor:
1. The transaction is not submitted by the sponsee (`tecNO_PERMISSION`)
1. The `Sponsor` field or the `SponsorFlags` field is missing (`temMALFORMED`)
1. The `SponsorFlags` field does not include the `tfSponsorReserve` flag (`temINVALID_FLAG`)
1. The new sponsor account does not exist (`terNO_ACCOUNT`)
1. The new sponsor does not have enough XRP to cover the reserve for this object/account (`tecINSUFFICIENT_RESERVE`)

### 10.5. State Changes

- The `Sponsor` field on the object specified by `ObjectID` is deleted if the `tx.Sponsor` is the object's `Owner`, otherwise the `Sponsor` field is updated to the new `tx.Sponsor`.
- The old sponsor (if applicable) has its `SponsoringOwnerCount`/`SponsoringAccountCount` decremented by one.
- The new sponsor (if applicable) has its `SponsoringOwnerCount`/`SponsoringAccountCount` incremented by one.
- If there is no new sponsor, then the owner's `SponsoredOwnerCount` will be decremented by one.

### 10.6. Example JSON

```json
{
  "TransactionType": "SponsorshipTransfer",
  "Account": "rfkDkFai4jUfCvAJiZ5Vm7XvvWjYvDqeYo",
  "ObjectID": "13F1A9B5C2D3E4F613F1A9B5C2D3E4F613F1A9B5C2D3E4F613F1A9B5C2D3E4F6",
  "Sponsor": "rNEWSponsor3LNcTz8JF2oJC6qaww6RZ7Lw",
  "SponsorFlags": 2,
  "Fee": "12",
  "Sequence": 43
}
```

## 11. Transaction: `Payment`

A Payment transaction represents a transfer of value from one account to another. (Depending on the path taken, this can involve additional exchanges of value, which occur atomically.) This transaction type can be used for several [types of payments](https://xrpl.org/docs/references/protocol/transactions/types/payment#types-of-payments).

Payments are also the only way to [create accounts](https://xrpl.org/docs/references/protocol/transactions/types/payment#creating-accounts).

As a reference, [here](https://xrpl.org/docs/references/protocol/transactions/types/payment) are the fields that `Payment` currently has.

### 11.1. Fields

This amendment proposes no changes to the fields, only to the flags and behavior.

### 11.2. Flags

As a reference, [here](https://xrpl.org/docs/references/protocol/transactions/types/payment#payment-flags) are the flags that `Payment` currently has:

| Flag Name          | Flag Value   | Description                                                                                                                                                                                        |
| ------------------ | ------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `tfNoRippleDirect` | `0x00010000` | Do not use the default path; only use paths included in the `Paths` field. This is intended to force the transaction to take arbitrage opportunities. Most clients do not need this.               |
| `tfPartialPayment` | `0x00020000` | If the specified `Amount` cannot be sent without spending more than `SendMax`, reduce the received amount instead of failing outright. See [Partial Payments](#partial-payments) for more details. |
| `tfLimitQuality`   | `0x00040000` | Only take paths where all the conversions have an input:output ratio that is equal or better than the ratio of `Amount`:`SendMax`. See [Limit Quality](#limit-quality) for details.                |

This spec proposes the following additions:

| Flag Name                 | Flag Value   | Description                                                                                                                                         |
| ------------------------- | ------------ | --------------------------------------------------------------------------------------------------------------------------------------------------- |
| `tfSponsorCreatedAccount` | `0x00080000` | This flag is only valid if the `Payment` is used to create an account. If it is enabled, the created account will be sponsored by the `tx.Account`. |

### 11.3. Failure Conditions

Existing failure conditions still apply (see [Payment documentation](https://xrpl.org/docs/references/protocol/transactions/types/payment)), with one exception:

1. If `tfSponsorCreatedAccount` is enabled, the XRP amount does not need to be greater than or equal to the account reserve requirement.

Additional failure conditions when `tfSponsorCreatedAccount` is enabled:

1. `tfNoRippleDirect`, `tfPartialPayment`, or `tfLimitQuality` are enabled (`temINVALID_FLAG`)
1. `Amount` specifies a non-XRP currency (`temBAD_AMOUNT`)
1. `Destination` already exists (`tecNO_SPONSOR_PERMISSION`)
1. `Account` does not have enough XRP to cover the account reserve requirement (`tecNO_DST_INSUF_XRP`)

### 11.4. State Changes

Existing state changes still apply (see [Payment documentation](https://xrpl.org/docs/references/protocol/transactions/types/payment)).

If `tfSponsorCreatedAccount` is enabled, the created account's `AccountRoot` will have a `Sponsor` field pointing to the `tx.Account`.

### 11.5. Example JSON

```json
{
  "TransactionType": "Payment",
  "Account": "rN7n7otQDd6FczFgLdlqtyMVrn3HMfXpf",
  "Destination": "rfkDkFai4jUfCvAJiZ5Vm7XvvWjYvDqeYo", // the new sponsored account
  "Amount": "1", // 1 drop, the minimum
  "Flags": 524288, // tfSponsorCreatedAccount
  "Fee": "10",
  "Sequence": 3
}
```

## 12. Transaction: `AccountDelete`

This transaction deletes an account.

As a reference, [here](https://xrpl.org/docs/references/protocol/transactions/types/accountdelete) are the fields that `AccountDelete` currently has.

### 12.1. Fields

This amendment proposes no changes to the fields, only to the behavior.

### 12.2. Failure Conditions

Existing failure conditions still apply (see [AccountDelete documentation](https://xrpl.org/docs/references/protocol/transactions/types/accountdelete)).

Additional failure conditions for sponsored accounts:

1. If the `AccountRoot` associated with `tx.Account` has a `Sponsor` field:

- The `Destination` is not equal to `AccountRoot.Sponsor` (`tecNO_PERMISSION` - sponsored account funds must go to sponsor)

2. If the `AccountRoot` associated with `tx.Account` has a non-zero `SponsoringOwnerCount` or `SponsoringAccountCount` field:

- The transaction fails with `tecHAS_OBLIGATIONS` (account is currently sponsoring other accounts or objects and cannot be deleted until those sponsorships are transferred or dissolved)

### 12.3. State Changes

Existing state changes still apply, including rules around deletion blockers.

If the `AccountRoot` associated with the `tx.Account` has a `Sponsor` field, the `Sponsor`'s `AccountRoot.SponsoringAccountCount` is decremented by 1.

If the `AccountRoot` associated with the `tx.Account` has a `SponsoredOwnerCount` field, the `Sponsor`'s `SponsoringOwnerCount` is decremented by the `tx.Account`'s `SponsoredOwnerCount`.

### 12.4. Example JSON

```json
{
  "TransactionType": "AccountDelete",
  "Account": "rWYkbWkCeg8dP6rXALnjgZSjjLyih5NXm",
  "Destination": "rN7n7otQDd6FczFgLdlqtyMVrn3HMfXpf", // the sponsor
  "Fee": "5000000",
  "Sequence": 2470665
}
```

## 13. Granular Permission: `SponsorFee`

### 13.1. Description

The `SponsorFee` permission allows an account to delegate its ability to sponsor other accounts' transaction fees.

### 13.2. Transaction Types Affected

This permission affects all transaction types that support the `Sponsor` field (see section [8.3.4](#834-transactions-that-cannot-be-sponsored)).

When a transaction includes a `Sponsor` field with the `tfSponsorFee` flag enabled, the sponsor must have granted the `SponsorFee` permission to the transaction submitter (the `tx.Account`), unless:

- The sponsor is signing the transaction directly (via `SponsorSignature.SigningPubKey` and `SponsorSignature.TxnSignature` or `SponsorSignature.Signers`), OR
- A `Sponsorship` object exists between the sponsor and sponsee with sufficient `FeeAmount`

### 13.3. Permission Value

65549

## 14. Granular Permission: `SponsorReserve`

### 14.1. Description

The `SponsorFee` permission allows an account to delegate its ability to sponsor other accounts' transaction fees.

### 14.2. Transaction Types Affected

This permission affects all transaction types that support the `Sponsor` field (see section [8.3.4](#834-transactions-that-cannot-be-sponsored)) and create new ledger objects or accounts.

When a transaction includes a `SponsorFlags` field with the `tfSponsorReserve` flag enabled, the sponsor must have granted the `SponsorReserve` permission to the transaction submitter (the `tx.Account`), unless:

- The sponsor is signing the transaction directly (via `SponsorSignature.SigningPubKey` and `SponsorSignature.TxnSignature` or `SponsorSignature.Signers`), OR
- A `Sponsorship` object exists between the sponsor and sponsee with sufficient `ReserveCount`

### 14.3. Permission Value

65550

## 15. RPC: `account_objects`

The [`account_objects` RPC method](https://xrpl.org/account_objects.html) already exists on the XRPL. This spec proposes an addition to the `account_objects` RPC method, to better support sponsored accounts.

### 15.1. Request Fields

As a reference, [here](https://xrpl.org/account_objects.html#request-format) are the fields that `account_objects` currently accepts.

### 15.2. Response Fields

The response fields remain the same.

### 15.3. Failure Conditions

There are no additional failure conditions.

### 15.4. Example Request

```json
{
  "command": "account_objects",
  "account": "rN7n7otQDd6FczFgLdlqtyMVrn3HMfXpf",
  "sponsored": true,
  "ledger_index": "validated",
  "type": "state"
}
```

### 15.5. Example Response

```json
{
  "account": "rN7n7otQDd6FczFgLdlqtyMVrn3HMfXpf",
  "account_objects": [
    {
      "Balance": {
        "currency": "USD",
        "issuer": "rrrrrrrrrrrrrrrrrrrrBZbvji",
        "value": "100"
      },
      "Flags": 65536,
      "HighLimit": {
        "currency": "USD",
        "issuer": "rN7n7otQDd6FczFgLdlqtyMVrn3HMfXpf",
        "value": "1000"
      },
      "HighNode": "0000000000000000",
      "HighSponsor": "rSponsor1VktvzBz8JF2oJC6qaww6RZ7Lw",
      "LedgerEntryType": "RippleState",
      "LowLimit": {
        "currency": "USD",
        "issuer": "rfkDkFai4jUfCvAJiZ5Vm7XvvWjYvDqeYo",
        "value": "0"
      },
      "LowNode": "0000000000000000",
      "PreviousTxnID": "1234567890ABCDEF1234567890ABCDEF1234567890ABCDEF1234567890ABCDEF",
      "PreviousTxnLgrSeq": 12345678,
      "index": "ABCDEF1234567890ABCDEF1234567890ABCDEF1234567890ABCDEF1234567890"
    }
  ],
  "ledger_hash": "FEDCBA0987654321FEDCBA0987654321FEDCBA0987654321FEDCBA0987654321",
  "ledger_index": 56789012,
  "validated": true
}
```

## 16. RPC: `account_sponsoring`

The `account_sponsoring` RPC method is used to fetch a list of objects that an account is sponsoring; namely, a list of objects where the `Sponsor` is the given account. It has a very similar API to the [`account_objects` method](https://xrpl.org/account_objects.html).

_[NOTE: This API will not be implemented in rippled, but will instead be implemented in Clio. This is due to the fact that this API would likely require another database to keep track of the sponsorship relationships, which would be too expensive to maintain in rippled.]_

### 16.1. Request Fields

| Field Name               | Required? | JSON Type            | Description                                                                                                             |
| ------------------------ | --------- | -------------------- | ----------------------------------------------------------------------------------------------------------------------- |
| `account`                | ✔️        | `string`             | The sponsor in question.                                                                                                |
| `deletion_blockers_only` |           | `boolean`            | If `true`, the response only includes objects that would block this account from being deleted. The default is `false`. |
| `ledger_hash`            |           | `string`             | A hash representing the ledger version to use.                                                                          |
| `ledger_index`           |           | `number` or `string` | The ledger index of the ledger to use, or a shortcut string to choose a ledger automatically.                           |
| `limit`                  |           | `number`             | The maximum number of objects to include in the results.                                                                |
| `marker`                 |           | `any`                | Value from a previous paginated response. Resume retrieving data where that response left off.                          |
| `type`                   |           | `string`             | Filter results by a ledger entry type. Some examples are `offer` and `escrow`.                                          |

### 16.2. Response Fields

The response fields are nearly identical to `account_objects`.

| Field Name             | Always Present? | JSON Type | Description                                                                                                                                                                                                                                                                                                                                                                           |
| ---------------------- | --------------- | --------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `account`              | ✔️              | `string`  | The account this request corresponds to.                                                                                                                                                                                                                                                                                                                                              |
| `sponsored_objects`    | ✔️              | `array`   | Array of ledger entries in this account's owner directory. This includes entries that are owned by this account and entries that are linked to this account but owned by someone else, such as escrows where this account is the destination. Each member is a ledger entry in its raw ledger format. This may contain fewer entries than the maximum specified in the `limit` field. |
| `ledger_hash`          |                 | `string`  | The identifying hash of the ledger that was used to generate this response.                                                                                                                                                                                                                                                                                                           |
| `ledger_index`         |                 | `number`  | The ledger index of the ledger that was used to generate this response.                                                                                                                                                                                                                                                                                                               |
| `ledger_current_index` |                 | `number`  | The ledger index of the open ledger that was used to generate this response.                                                                                                                                                                                                                                                                                                          |
| `limit`                |                 | `number`  | The limit that was used in this request, if any.                                                                                                                                                                                                                                                                                                                                      |
| `marker`               |                 | `any`     | Server-defined value indicating the response is paginated. Pass this to the next call to resume where this call left off. Omitted when there are no additional pages after this one.                                                                                                                                                                                                  |
| `validated`            |                 | `boolean` | If `true`, the information in this response comes from a validated ledger version. Otherwise, the information is subject to change.                                                                                                                                                                                                                                                   |

### 16.3. Failure Conditions

1. Any of the [universal error types](https://xrpl.org/docs/references/http-websocket-apis/api-conventions/error-formatting#universal-errors).
1. `invalidParams` - One or more fields are specified incorrectly, or one or more required fields are missing.
1. `actNotFound` - The [address](https://xrpl.org/docs/references/protocol/data-types/basic-data-types#addresses) specified in the `account` field of the request does not correspond to an account in the ledger.
1. `lgrNotFound` - The ledger specified by the `ledger_hash` or `ledger_index` does not exist, or it does exist but the server does not have it.

### 16.4. Example Request

```json
{
  "command": "account_sponsoring",
  "account": "rSponsor1VktvzBz8JF2oJC6qaww6RZ7Lw",
  "ledger_index": "validated",
  "limit": 10
}
```

### 16.5. Example Response

```json
{
  "account": "rSponsor1VktvzBz8JF2oJC6qaww6RZ7Lw",
  "sponsored_objects": [
    {
      "Balance": {
        "currency": "USD",
        "issuer": "rrrrrrrrrrrrrrrrrrrrBZbvji",
        "value": "100"
      },
      "Flags": 65536,
      "HighLimit": {
        "currency": "USD",
        "issuer": "rSponsee1ABC123XYZ456DEF789GHI",
        "value": "1000"
      },
      "HighNode": "0000000000000000",
      "HighSponsor": "rSponsor1VktvzBz8JF2oJC6qaww6RZ7Lw",
      "LedgerEntryType": "RippleState",
      "LowLimit": {
        "currency": "USD",
        "issuer": "rSponsor1VktvzBz8JF2oJC6qaww6RZ7Lw",
        "value": "0"
      },
      "LowNode": "0000000000000000",
      "PreviousTxnID": "E3FE6EA3D48F0C2B639448020EA4F03D4F4F8FFDB243A852A0F59177921B4879",
      "PreviousTxnLgrSeq": 14090896,
      "index": "9ED4406351B7A511A012A9B5E7FE4059FA2F7650621379C0013492C315E25B97"
    },
    {
      "Account": "rSponsee2XYZ789ABC123DEF456GHI",
      "Balance": "1000000",
      "Flags": 0,
      "LedgerEntryType": "AccountRoot",
      "OwnerCount": 3,
      "PreviousTxnID": "0D5FB50FA65C9FE1538FD7E398FFFE9D1908DFA4576D8D7A020040686F93C77D",
      "PreviousTxnLgrSeq": 14091574,
      "Sequence": 1,
      "Sponsor": "rSponsor1VktvzBz8JF2oJC6qaww6RZ7Lw",
      "index": "13F1A95D7AAB7108D5CE7EEAF504B2894B8C674E6D68499076441C4837282BF8"
    },
    {
      "LedgerEntryType": "Sponsorship",
      "Owner": "rSponsor1VktvzBz8JF2oJC6qaww6RZ7Lw",
      "Sponsee": "rSponsee3DEF456GHI789ABC123XYZ",
      "FeeAmount": "5000000",
      "MaxFee": "10000",
      "ReserveCount": 5,
      "OwnerNode": "0000000000000000",
      "SponseeNode": "0000000000000000",
      "PreviousTxnID": "B044D3861WL1HZ4WM4GURZVKTTdJPgM1v5T8QBKWJZQM",
      "PreviousTxnLgrSeq": 14091600,
      "index": "2B42F8F4E3D3D3D3D3D3D3D3D3D3D3D3D3D3D3D3D3D3D3D3D3D3D3D3D3D3D3D3"
    }
  ],
  "ledger_hash": "4C99E5F63C0D0B1C2283D3D3D3D3D3D3D3D3D3D3D3D3D3D3D3D3D3D3D3D3D3D3",
  "ledger_index": 14091625,
  "validated": true
}
```

## 17. Security Considerations

### 17.1. Security Axioms

Both the sponsee _and_ the sponsor must agree to enter into a sponsor relationship. The sponsee must actively consent to the sponsor handling the reserve, and the sponsor must be willing to take on that reserve. A signature from both parties ensures that this is the case.

A sponsor will never be stuck sponsoring an sponsee's account or object it no longer wants to support, because it can submit a `SponsorshipTransfer` transaction at any point.

The sponsor's signature must _always_ include the `Account` and `Sequence` fields, to prevent signature replay attacks (where the sponsor's signature can be reused to sponsor an object or account that they did not want to sponsor).

When sponsoring transaction fees, the sponsor must approve of the `Fee` value of the transaction, since that is the amount that they will be paying.

When sponsoring reserves, the sponsor's signature must include any aspects of the transaction that involve a potential account/object reserve. This would include the `Destination` field of a `Payment` transaction (and whether it is a new account) and the `TicketSequence` field of a `TicketCreate` transaction (since that dictates how many `Ticket` objects are created, each of which results in one object reserve).

A sponsee cannot take advantage of the generosity of their sponsor, since the sponsor must sign every transaction it wants to sponsor the ledger objects for. A sponsee also must not be able to change the sponsorship type that the sponsor is willing to engage in, as this could lock up to 500 of the sponsor's XRP (in the case of 250 tickets being created in one `TicketCreate` transaction).

An axiom that is out of scope: the sponsee may not have any control over a sponsorship transfer (the sponsor may transfer a sponsorship without the sponsee's consent). This is akin to a loanee having no control over a bank selling their mortgage to some other company, or a lender selling debt to a debt collection agency.

### 17.2. Signatures

Since a fee sponsorship must approve of the `Fee` field, and a reserve sponsorship must approve of a broad set of transaction fields, the sponsor must always sign the whole transaction. This also avoids needing to have different sponsorship processes for different sponsorship types. The same is true for the sponsee's transaction signature; the sponsee must approve of the sponsor and sponsorship type.

A sponsor's `Signature` cannot be replayed or attached to a different transaction, since the whole transaction (including the `Account` and `Sequence` values) must be signed.

## 18. Invariants

An [invariant](https://xrpl.org/docs/concepts/consensus-protocol/invariant-checking/) is a statement, usually an equation, that must always be true for every valid ledger state on the XRPL. Invariant checks serve as a last line of defense against bugs; the `tecINVARIANT_FAILED` error is thrown if an invariant is violated (which ideally should never happen).

### 18.1. Tracking Owner Counts

A transaction that creates a ledger object either increments an account's `OwnerCount` by 1 or increments two separate accounts' `SponsoringOwnerCount` and `SponsoredOwnerCount` by 1. The opposite happens when a ledger object is deleted.

The equivalent also should happen with `SponsoringAccountCount`.

### 18.2. Balancing `SponsoredOwnerCount` and `SponsoringOwnerCount`

$$ \sum*{accounts} Account.SponsoredOwnerCount = \sum*{accounts} Account.SponsoringOwnerCount $$

In other words, the sum of all accounts' `SponsoredOwnerCount`s must be equal to the sum of all accounts' `SponsoringOwnerCount`s. This ensures that every sponsored object is logged as being sponsored and also has a sponsor.

## 19. Example Flows

### 19.1. Fee Sponsorship

#### 19.1.1. The Unsigned Transaction

<details open>

```typescript
{
  TransactionType: "Payment",
  Account: "rOldB3E44wS6SM7KL3T3b6nHX3Jjua62wg",
  Destination: "rNewfcu9RJa5W1ncAuEgLH1Xpi4j1vzXjr",
  Amount: "20000000",
  Sequence: 3,
  Fee: "10",
  Sponsor: "rSponsor1VktvzBz8JF2oJC6qaww6RZ7Lw",
  SponsorFlags: 1
}
```

</details>

#### 19.1.2. The Signed Transaction

<details open>

```typescript
{
  TransactionType: "Payment",
  Account: "rSender7NwD9vmNf5dvTbW4FQDNSRsfPv6",
  Destination: "rDestinationT6N5fJdaHnRqLpW1D8oFrZ",
  Amount: "20000000",
  Sequence: 3,
  Fee: "10",
  Sponsor: "rSponsor1VktvzBz8JF2oJC6qaww6RZ7Lw",
  SponsorFlags: 1,
  SponsorSignature: {
    SigningPubKey: "03072BBE5F93D4906FC31A690A2C269F2B9A56D60DA9C2C6C0D88FB51B644C6F94", // rSponsor's public key
    Signature: "3045022100C15AFB7C0C4F5EDFEC4667B292DAB165B96DAF3FFA6C7BBB3361E9EE19E04BC70220106C04B90185B67DB2C67864EB0A11AE6FB62280588954C6E4D9C1EF3710904D"
  },
  SigningPubKey: "03A8D0093B0CD730F25E978BF414CA93084B3A2CBB290D5E0E312021ED2D2C1C8B", // rAccount's public key
  TxnSignature: "3045022100F2AAF90D8F9BB6C94C0C95BA31E320FC601C7BAFFF536CC07076A2833CB4C7FF02203F3C76EB34ABAD61A71CEBD42307169CDA65D9B3CA0EEE871210BEAB824E524B"
}
```

</details>

### 19.2. Account Sponsorship

The only way an account can be created is via a `Payment` transaction. So the sponsor relationship must be initiated on the `Payment` transaction.

#### 19.2.1. The Unsigned Transaction

<details open>

```typescript
{
  TransactionType: "Payment",
  Account: "rOldB3E44wS6SM7KL3T3b6nHX3Jjua62wg",
  Destination: "rNewfcu9RJa5W1ncAuEgLH1Xpi4j1vzXjr",
  Amount: "20000000",
  Sequence: 3,
  Fee: "10",
  Sponsor: "rSponsor1VktvzBz8JF2oJC6qaww6RZ7Lw",
  SponsorFlags: 2,
}
```

</details>

#### 19.2.2. The Signed Transaction

<details open>

```typescript
{
  TransactionType: "Payment",
  Account: "rOldB3E44wS6SM7KL3T3b6nHX3Jjua62wg",
  Destination: "rNewfcu9RJa5W1ncAuEgLH1Xpi4j1vzXjr",
  Amount: "20000000",
  Sequence: 3,
  Fee: "10",
  Sponsor: "rSponsor1VktvzBz8JF2oJC6qaww6RZ7Lw",
  SponsorFlags: 2,
  SponsorSignature: {
    SigningPubKey: "03072BBE5F93D4906FC31A690A2C269F2B9A56D60DA9C2C6C0D88FB51B644C6F94", // rSponsor's public key
    Signature: "30440220702ABC11419AD4940969CC32EB4D1BFDBFCA651F064F30D6E1646D74FBFC493902204E5B451B447B0F69904127F04FE71634BD825A8970B9467871DA89EEC4B021F8"
  },
  SigningPubKey: "03BC74CA0B765281E31E342017D97B3F6743A05FBA23D2114B98FC8AD26D92856C", // rAccount's public key
  TxnSignature: "30440220245217F931FDA0C5E68B935ABB4920211D5B6182878583124DE4663B19F00BEC022070BE036264760551CF40E9DAFC8B84036FA70E7EE7257BB7E39AEB7354B2EB86"
}
```

</details>

### 19.3. Object Sponsorship

#### 19.3.1. The Unsigned Transaction

<details open>

```typescript
{
  TransactionType: "TicketCreate",
  Account: "rAccount4yjv1j2x79wXxRVXnFbwsjUWXo",
  TicketCount: 100,
  Sequence: 3,
  Fee: "10",
  Sponsor: "rSponsor1VktvzBz8JF2oJC6qaww6RZ7Lw",
  SponsorFlags: 2,
}
```

</details>

#### 19.3.2. The Signed Transaction

<details open>

```typescript
{
  TransactionType: "TicketCreate",
  Account: "rAccount4yjv1j2x79wXxRVXnFbwsjUWXo",
  TicketCount: 100,
  Sequence: 3,
  Fee: "10",
  Sponsor: "rSponsor1VktvzBz8JF2oJC6qaww6RZ7Lw",
  SponsorFlags: 2,
  SponsorSignature: {
    SigningPubKey: "03072BBE5F93D4906FC31A690A2C269F2B9A56D60DA9C2C6C0D88FB51B644C6F94", // rSponsor's public key
    Signature: "30450221009878F3A321250341886FE344E0B50700C8020ABAA25301925BD84DDB5421D432022002A3C72C54BACB5E7DAEC48E2A1D75DCBB8BA3B2212C7FC22F070CCABAF76EC1"
  },
  SigningPubKey: "03BC74CA0B765281E31E342017D97B3F6743A05FBA23D2114B98FC8AD26D92856C", // rAccount's public key
  TxnSignature: "3044022047CB72DA297B067C0E69045B7828AD660F8198A6FA03982E31CB6D27F0946DDE022055844EB63E3BFF7D9ABFB26645AA4D2502E143F4ABEE2DE57EB87A1E5426E010"
}
```

</details>

## 20. Rationale

This section explains the key technical design decisions, why particular choices were made, and how this design compares to similar features on other chains.

### 20.1. Related Work

Sponsored transactions and reserves are a common feature across blockchain ecosystems:

- **Stellar** implements [sponsored reserves](https://developers.stellar.org/docs/learn/encyclopedia/sponsored-reserves) using a "sandwich transaction" pattern with `BeginSponsoringFutureReserves` and `EndSponsoringFutureReserves` operations wrapped around the sponsored operations.
- **Ethereum** supports meta-transactions through various standards (EIP-2771, EIP-3009) and account abstraction (ERC-4337), where a relayer submits transactions on behalf of users and pays the gas fees.
- **Solana** allows fee payers to be specified separately from the transaction signer.

This proposal draws inspiration from these implementations while adapting the concepts to fit the XRPL's account-based model and existing transaction structure.

### 20.2. Pre-Funded vs. Co-Signed Sponsorship

The design supports two modes of sponsorship: pre-funded (via the `Sponsorship` ledger object) and co-signed (via the `Sponsor` transaction field). This dual approach was chosen to accommodate different use cases:

- **Co-signed sponsorship** gives sponsors fine-grained control over each transaction, ideal for high-value or sensitive operations.
- **Pre-funded sponsorship** reduces operational overhead for sponsors who want to enable many transactions without being involved in each one, while still maintaining limits via `MaxFee` and `ReserveCount`.

### 20.3. Other Designs Considered

#### 20.3.1. Per-Transaction Sponsorship vs. Account-Level Sponsorship

An earlier design involved updating `AccountSet` to allow users to add a `Sponsor` to their account (with a signature from the sponsor as well). The sponsor would then sponsor every object from that account while the field was active, and either the sponsor or the account could remove the sponsorship at any time.

This approach was rejected because it made more sense for the relationship to be specific to a specific transaction(s), to prevent abuse—the sponsor should decide what objects they want to support and what objects they don't want to support. This philosophy (that the sponsorship relationship should be ephemeral to prevent abuse) aligns with Stellar's design.

The current design also supports having different sponsors for different objects, which allows users to use a broad set of services and platforms, instead of being locked into one.

<!--Stellar uses this philosophy ("the relationship should be ephemeral to prevent abuse") for their sponsored reserves design, which I like.-->

#### 20.3.2. Inner Object vs. Wrapper Transaction

An alternative design considered was a wrapper transaction (tentatively named `Relay`), similar to `Batch` in [XLS-56](../XLS-0056-batch/README.md), that the sponsor would sign. It would contain a sub-transaction from the sponsee.

It would look something like this:

| Field Name        | Required | JSON Type | Internal Type | Description                                                              |
| ----------------- | -------- | --------- | ------------- | ------------------------------------------------------------------------ |
| `TransactionType` | Yes      | `string`  | `UInt16`      | The transaction type (`Relay`).                                          |
| `Account`         | Yes      | `string`  | `AccountID`   | The sponsor of the transaction.                                          |
| `Transaction`     | Yes      | `object`  | `STTx`        | The sponsee's transaction.                                               |
| `Fee`             | Yes      | `string`  | `STAmount`    | The fee for the transaction. This should match the fee in `Transaction`. |

This was inspired by Stellar's sandwich transaction design, but the current inner object design felt cleaner. From an implementation perspective, it's easier to have the fee payer as a part of the existing transaction rather than as a part of a wrapper transaction, since that info needs to somehow get passed down the stack. Also, while the wrapper transaction paradigm will be used in XLS-56, they should be used sparingly in designs—only when necessary—as their flow is rather complicated in the `rippled` code.

In addition, the signing process becomes complicated (as discovered in the process of developing XLS-56). You have to somehow prevent the sponsor from submitting the as-is signed transaction to the network, without including it in the wrapper transaction.

#### 20.3.2. Create-Accept-Cancel Flow

Another design considered was to have a new set of transactions (e.g. `SponsorCreate`/`SponsorAccept`/`SponsorCancel`/`SponsorFinish`) where a sponsor could take on the reserve for an existing object.

This design was never seriously considered, as it felt too complicated and introduced several new transactions. It also doesn't support adding a sponsor to the object at object creation time, which is a much smoother UX and never requires the owner/sponsee to hold enough XRP for the reserve.

## 21. Backwards Compatibility

This amendment introduces new functionality while maintaining compatibility with existing ledger states and transactions.

### 21.1. Pre-Amendment Ledgers and Transactions

All ledgers and transactions created before the `Sponsor` amendment are activated remain valid. The amendment does not modify or invalidate any existing ledger entries or historical transactions.

### 21.2. Changes to `AccountDelete` Behavior

The `AccountDelete` transaction has two new behavioral changes:

1. **Destination Constraint for Sponsored Accounts**: If an account being deleted has a `Sponsor` field (indicating the account reserve is sponsored), the `Destination` field of the `AccountDelete` transaction must equal the `Sponsor`. This ensures sponsors can recoup their reserve. Accounts without sponsorship can still use `AccountDelete` with any valid destination as before.

2. **New Failure Condition**: `AccountDelete` will fail with `tecHAS_OBLIGATIONS` if the account has non-zero `SponsoringOwnerCount` or `SponsoringAccountCount` fields, indicating the account is currently sponsoring other accounts or objects. This prevents sponsors from deleting their accounts while they have active sponsorship obligations.

### 21.3. Reserve Accounting Changes

The amendment introduces new fields that affect reserve calculations:

- **New AccountRoot Fields**: `Sponsor`, `SponsoredOwnerCount`, `SponsoringOwnerCount`, and `SponsoringAccountCount` modify how an account's required XRP reserve is calculated.
- **New Ledger Entry Fields**: The `Sponsor` field (and `HighSponsor`/`LowSponsor` for `RippleState`) indicates when an object's reserve is sponsored.
- **Reserve Calculation**: The reserve formula changes from `acctReserve + objReserve * OwnerCount` to account for sponsored objects and sponsorship obligations (see section 6.2).

Accounts without these new fields continue to use the existing reserve calculation, ensuring backward compatibility.

### 21.4. Impact on Tooling and Applications

Legacy tooling that does not understand the new sponsorship fields may experience the following:

- **Display Issues**: Tools may not correctly display or interpret `Sponsor`, `SponsoredOwnerCount`, `SponsoringOwnerCount`, and `SponsoringAccountCount` fields.
- **Reserve Calculations**: Tools that calculate required reserves may produce incorrect results if they do not account for the new reserve formula.
- **RPC Methods**: The new `account_sponsoring` RPC method and the `sponsored` filter on `account_objects` will not be available in tools that have not been updated.
- **Transaction Construction**: Tools will need updates to support constructing transactions with the `Sponsor` field and handling the dual-signature flow.

Applications should be updated to recognize and handle these new fields to provide accurate information to users.

### 21.5. Amendment Activation

The `Sponsor` amendment must be enabled via the standard amendment process. Once activated:

- New transactions can include the `Sponsor` field to enable fee and reserve sponsorship.
- New ledger entries can include sponsorship-related fields.
- The new `Sponsorship` ledger entry type becomes available.
- The new `SponsorshipSet` and `SponsorshipTransfer` transaction types become available.
- The `Payment` transaction accepts the new `tfSponsorCreatedAccount` flag.

Before activation, transactions attempting to use these features will be rejected.

## 22. Test Plan

This section outlines the testing strategy for the sponsored fees and reserves feature. A comprehensive test plan is essential to ensure the correctness and security of this amendment.

### 22.1. Unit Tests for Ledger Entries

**`Sponsorship` Object Tests:**

- Creation of `Sponsorship` objects via `SponsorshipSet` with various field combinations
- Updates to existing `Sponsorship` objects (modifying `FeeAmount`, `MaxFee`, `ReserveCount`)
- Deletion of `Sponsorship` objects via `SponsorshipSet` with `tfDeleteObject` flag
- Validation of invariants: `Owner != Sponsee`, `FeeAmount >= 0` and denominated in XRP, `ReserveCount >= 0`
- Proper handling of `lsfSponsorshipRequireSignForFee` and `lsfSponsorshipRequireSignForReserve` flags
- Verification that `Sponsorship` objects are deletion blockers

**`AccountRoot` Field Tests:**

- Addition and removal of `Sponsor` field on accounts
- Correct tracking of `SponsoredOwnerCount`, `SponsoringOwnerCount`, and `SponsoringAccountCount`
- Reserve calculation with new fields (see section 6.2)
- Interaction between sponsored and unsponsored objects on the same account

**`RippleState` Field Tests:**

- Addition and removal of `HighSponsor` and `LowSponsor` fields
- Verification that `Sponsor` common field is not used on `RippleState` objects
- Proper handling of bidirectional trust line sponsorship

### 22.2. Unit Tests for Transactions

**`SponsorshipSet` Transaction Tests:**

- Creating new `Sponsorship` objects with valid and invalid parameters
- Updating existing `Sponsorship` objects
- Deleting `Sponsorship` objects and verifying fund return to sponsor
- Failure conditions: invalid account combinations, invalid fee/reserve values, conflicting flags
- Proper increment/decrement of owner counts and sponsorship counters

**`SponsorshipTransfer` Transaction Tests:**

- Transferring sponsorship of objects to new sponsors
- Dissolving sponsorship (returning reserve burden to owner)
- Transferring sponsorship of accounts
- Failure conditions: insufficient reserves, invalid accounts, unauthorized submitters
- Proper updates to `SponsoringOwnerCount`, `SponsoringAccountCount`, and `SponsoredOwnerCount`

**`Payment` Transaction Tests:**

- Creating sponsored accounts using `tfSponsorCreatedAccount` flag
- Fee sponsorship via `Sponsor` field with `tfSponsorFee` flag
- Reserve sponsorship for new accounts via `Sponsor` field with `tfSponsorReserve` flag
- Combined fee and reserve sponsorship
- Failure conditions: invalid sponsor signatures, insufficient sponsor funds

**`AccountDelete` Transaction Tests:**

- Deleting sponsored accounts with correct destination (must be sponsor)
- Failure when destination is not the sponsor for sponsored accounts
- Failure with `tecHAS_OBLIGATIONS` when account has non-zero `SponsoringOwnerCount` or `SponsoringAccountCount`
- Proper decrement of sponsor's counters upon successful deletion

**Common Transaction Field Tests:**

- Valid and invalid `Sponsor` field structures
- Single-signature sponsorship (`SigningPubKey` + `TxnSignature`)
- Multi-signature sponsorship (`Signers` array)
- Validation of `tfSponsorFee` and `tfSponsorReserve` flags
- Fee calculation with sponsor signatures (multi-sig overhead)
- Pre-funded sponsorship (using `Sponsorship` object) vs. co-signed sponsorship
- Signature validation and replay attack prevention

### 22.3. Invariant Tests

**Owner Count Balancing:**

- Verify that object creation increments either `OwnerCount` or both `SponsoringOwnerCount` and `SponsoredOwnerCount`
- Verify that object deletion decrements the appropriate counters
- Test the global invariant: `Σ SponsoredOwnerCount = Σ SponsoringOwnerCount`

**Account Count Balancing:**

- Verify that sponsored account creation increments `SponsoringAccountCount` on sponsor
- Verify that sponsored account deletion decrements `SponsoringAccountCount` on sponsor

**Reserve Consistency:**

- Verify that accounts always have sufficient XRP to meet their reserve requirements
- Test edge cases where sponsorship changes affect reserve calculations

### 22.4. Integration Tests

**End-to-End Co-Signed Sponsorship Flow:**

- Sponsee constructs and autofills transaction
- Sponsor signs transaction
- Sponsee adds sponsor signature and signs transaction
- Transaction is submitted and validated
- Verify correct state changes and fee/reserve handling

**End-to-End Pre-Funded Sponsorship Flow:**

- Sponsor creates `Sponsorship` object with `SponsorshipSet`
- Sponsee constructs transaction with `Sponsor` field
- Transaction is submitted without sponsor signature (using pre-funded amounts)
- Verify `FeeAmount` and `ReserveCount` are decremented correctly
- Test exhaustion of pre-funded amounts

**Error Case Testing:**

- Insufficient sponsor funds for fees
- Insufficient sponsor reserves for objects
- Exceeding `MaxFee` limit in `Sponsorship` object
- Exceeding `ReserveCount` limit in `Sponsorship` object
- Invalid or missing sponsor signatures
- Signature replay attempts

**Sponsorship Transfer Flows:**

- Sponsor transfers object sponsorship to new sponsor
- Sponsor dissolves sponsorship, returning burden to owner
- Owner transfers sponsorship to new sponsor
- Test with insufficient reserves on receiving party

### 22.5. RPC Tests

**`account_objects` with `sponsored` Filter:**

- Retrieve only sponsored objects (`sponsored: true`)
- Retrieve only unsponsored objects (`sponsored: false`)
- Retrieve all objects (omit `sponsored` parameter)
- Test pagination with `sponsored` filter
- Test interaction with `type` filter

**`account_sponsoring` RPC Method:**

- Retrieve all objects sponsored by an account
- Test pagination with `limit` and `marker`
- Test `deletion_blockers_only` filter
- Test with various `type` filters
- Verify correct response format and field presence
- Test error conditions: invalid account, missing ledger

### 22.6. Performance and Stress Tests

- Create maximum number of sponsored objects per account
- Test with large `Sponsorship` object counts
- Verify performance of reserve calculations with many sponsored objects
- Test transaction throughput with sponsored transactions

### 22.7. Amendment Activation Tests

- Verify that sponsorship features are unavailable before amendment activation
- Verify that sponsorship features become available after amendment activation
- Test that pre-amendment ledgers and transactions remain valid post-activation

## 23. Reference Implementation

https://github.com/XRPLF/rippled/pull/5887

## 24. n+1. Remaining TODOs/Open Questions

- Should fee sponsorship allow for the existing fee paradigm that allows users to dip below the reserve?
- Should a sponsored account be prevented from sponsoring other accounts? By default the answer is no, so unless there's a reason to do so, we should leave it as is.

# Appendix

## Appendix A: FAQ

### A.1: Does the sponsee receive any XRP for the reserve?

No, there is no XRP transfer in a sponsorship relationship - the XRP stays in the sponsor's account. The burden of the reserve for that object/account is just transferred to the sponsor.

### A.2: What happens if you try to delete your account and you have sponsored objects?

If the account itself is sponsored, then it can be deleted, but the destination of the `AccountDelete` transaction (in other words, where the leftover XRP goes) **must** be the sponsor's account. This ensures that the sponsor gets their reserve back, and the sponsee cannot run away with those funds.

If the sponsee still has sponsored objects, those objects will follow the same rules of [deletion blockers](https://xrpl.org/docs/concepts/accounts/deleting-accounts/#requirements). Whether or not they are sponsored is irrelevant.

If a sponsored object is deleted (either due to normal object deletion processes or, in the case of objects that aren't deletion blockers, because the owner account is deleted), the sponsor's reserve becomes available again.

### A.3: What if a sponsor that is sponsoring a few objects wants to delete their account?

An account cannot be deleted if it is sponsoring **any** existing accounts or objects. They will need to either delete those objects (by asking the owner to do so, as they cannot do so directly) or use the `SponsorshipTransfer` transaction to relinquish control of them.

### A.4: Does a sponsor have any powers over an object they pay the reserve for? I.e. can they delete the object?

No. If a sponsor no longer wants to support an object, they can always use the `SponsorshipTransfer` transaction instead to transfer the reserve burden back to the sponsee.

### A.5: What if a sponsee refuses to delete their account when a sponsor wants to stop supporting their account?

The sponsor will have the standard problem of trying to get ahold of a debtor to make them pay. They may use the `SponsorshipTransfer` transaction to put the onus on the sponsee. If the sponsee does not have enough XRP to cover the reserve for those objects, they will not be able to create any more objects until they do so.

### A.6: What happens if the sponsor tries to `SponsorshipTransfer` but the sponsee doesn't have enough funds to cover the reserve?

If the sponsor really needs to get out of the sponsor relationship ASAP without recouping the value of the reserve, they can pay the sponsee the amount of XRP they need to cover the reserve. These steps can be executed atomically via a [Batch transaction](../XLS-0056-batch/README.md), to ensure that the sponsee can't do something else with the funds before the `SponsorshipTransfer` transaction is validated.

### A.7: Would sponsored accounts carry a lower reserve?

No, they would still carry a reserve of 1 XRP at current levels.

### A.8: Can an existing unsponsored ledger object/account be sponsored?

Yes, with the `SponsorshipTransfer` transaction.

### A.9: Can a sponsored account be a sponsor for other accounts/objects?

Yes, though they will have to use their own XRP for this (not from another sponsor).

### A.10: Can a sponsored account hold unsponsored objects, or objects sponsored by a different sponsor?

Yes, and yes.

### A.11: What if I want different sponsors to sponsor the transaction fee vs. the reserve for the same transaction?

That will not be supported by this proposal. If you have a need for this, please provide example use-cases.

### A.12: Won't it be difficult to add two signatures to a transaction?

This is something that good tooling can solve. It could work similarly to how multisigning is supported in various tools.

### A.13. Why not instead do [insert some other design]?

See Appendix B for the alternate designs that were considered and why this one was preferred. If you have another one in mind, please describe it in the comments and we can discuss.

### A.14: How is this account sponsorship model different from/better than [XLS-23, Lite Accounts](../XLS-0023-lite-accounts/README.md)?

- Sponsored accounts do not have any restrictions, and can hold objects.
- Sponsored accounts require the same reserve as a normal account (this was one of the objections to the Lite Account proposal).
- Lite accounts can be deleted by their sponsor.

### A.15: How will this work for objects like trustlines, where multiple accounts might be holding reserves for it?

The answer to this question is still being explored. One possible solution is to add a second field, `Sponsor2`, to handle the other reserve.

### A.16: How does this proposal work in conjunction with [XLS-49](../XLS-0049-multiple-signer-lists/README.md)? What signer list(s) have the power to sponsor fees or reserves?

Currently, only the global signer list is supported. Another `SignerListID` value could be added to support sponsorship. Transaction values can only go up to $2^{16}$, since the `TransactionType` field is a `UInt16`, but the `SignerListID` field goes up to $2^{32}$, so there is room in the design for additional values that do not correlate to a specific transaction type.
