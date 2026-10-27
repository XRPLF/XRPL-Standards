<pre>
  xls: 68.1
  title: Sponsored Account Create
  description: Adds the SponsoredAccountCreate transaction, which creates a zero-balance account sponsored by the submitter
  author: Oleksandr Pidskopnyi (@oleks-rip)
  proposal-from: https://github.com/XRPLF/XRPL-Standards/discussions/196
  status: Draft
  category: Amendment
  created: 2026-10-15
  updated: 2026-10-15
</pre>

# 68.1 Sponsored Account Create

## 1. Abstract

Under the `SponsorV1_1` amendment, a new `SponsoredAccountCreate` transaction creates an `AccountRoot` for `Destination` with a `Balance` of zero and a `Sponsor` field naming `tx.Account`, which takes on the new account's base reserve. In the same transaction the sponsor may also create a `Sponsorship` object for the new account, pre-funding its transaction fees (`FeeAmount`, `MaxFee`) and object reserves (`RemainingOwnerCount`).

## 2. Motivation

Under the `Sponsor` amendment the only way to create a sponsored account is a `Payment` with `tfSponsorCreatedAccount` ([XLS-68 §3.9](../README.md#39-transaction-payment)). That `Payment` must still deliver a positive XRP `Amount`, so the new account always starts with some XRP. Pre-funding the new account's fees then takes a second, separate `SponsorshipSet` transaction, which can only be submitted once the account exists.

`SponsoredAccountCreate` creates the account without transferring any XRP to it, and can create the `Sponsorship` object in the same transaction. The new account can submit transactions straight away, paying fees from the pre-funded `Sponsorship.FeeAmount` (`spfSponsorFee`), while the sponsor's XRP stays in the sponsor's own account.

## 3. Specification

### 3.1 Transaction: `SponsoredAccountCreate`

Transaction requires both the `Sponsor` and the `SponsorV1_1` amendments.

#### 3.1.1 Fields

| Field Name            | Required? | JSON Type | Internal Type | Default Value | Description                                                                                                           |
| --------------------- | --------- | --------- | ------------- | ------------- | --------------------------------------------------------------------------------------------------------------------- |
| `TransactionType`     | Yes       | `string`  | `UInt16`      | N/A           | The transaction type (`SponsoredAccountCreate`).                                                                      |
| `Account`             | Yes       | `string`  | `AccountID`   | N/A           | The sponsor. It pays the new account's base reserve and owns the `Sponsorship` object, if one is created.             |
| `Destination`         | Yes       | `string`  | `AccountID`   | N/A           | The account to create. It must not already exist.                                                                     |
| `FeeAmount`           | No        | `string`  | `Amount`      | N/A           | XRP to move from `Account` into the new `Sponsorship.FeeAmount`, for the new account to spend on transaction fees.    |
| `MaxFee`              | No        | `string`  | `Amount`      | N/A           | The maximum fee per transaction that the `Sponsorship` object will pay. Stored as `Sponsorship.MaxFee`.               |
| `RemainingOwnerCount` | No        | `number`  | `UInt32`      | N/A           | The number of object reserves the sponsor pre-funds for the new account. Stored as `Sponsorship.RemainingOwnerCount`. |

A `Sponsorship` object is created if and only if `FeeAmount` or `RemainingOwnerCount` is present.

#### 3.1.2 Flags

The transaction defines no flags of its own.

#### 3.1.3 Transaction Fee

**Fee Structure:** Standard

The fee may be sponsored with `spfSponsorFee` ([XLS-68 §3.6](../README.md#36-transactions-common-fields)). `spfSponsorReserve` is not supported; see [§3.1.4.1](#3141-data-verification), item 8.

#### 3.1.4 Failure Conditions

##### 3.1.4.1 Data Verification

1. The `Sponsor` or the `SponsorV1_1` amendment is not enabled (`temDISABLED`)
2. `Destination` is the all-zero account (`temDST_NEEDED`)
3. `Destination` is the same as `Account` (`temDST_IS_SRC`)
4. `FeeAmount` is present and is not XRP or is not positive (`temBAD_AMOUNT`)
5. `MaxFee` is present and is not XRP or is not positive (`temBAD_AMOUNT`)
6. `RemainingOwnerCount` is present and is `0` (`temINVALID`)
7. `MaxFee` is present but neither `FeeAmount` nor `RemainingOwnerCount` is present (`temMALFORMED`)
8. `SponsorFlags` includes `spfSponsorReserve`, because `SponsoredAccountCreate` is not on the reserve-sponsorship allow-list ([XLS-68 §3.6.3.4](../README.md#3634-transactions-that-cannot-be-sponsored)) (`temINVALID_FLAG`)

##### 3.1.4.2 Protocol-Level Failures

1. `Destination` already exists (`tecDUPLICATE`)
2. After the transaction fee it pays (if any) and `FeeAmount` are deducted, `Account` does not meet its reserve with one more `SponsoringAccountCount` and, if a `Sponsorship` object is created, one more `OwnerCount` (`tecINSUFFICIENT_RESERVE`)

#### 3.1.5 State Changes

1. Create an `AccountRoot` for `Destination`, with:
   1. `Account` set to `Destination`
   2. `Sequence` set to the current ledger index
   3. `Balance` set to `0`
   4. `Sponsor` set to `tx.Account`
2. Increment `tx.Account`'s `SponsoringAccountCount` by 1.
3. If `FeeAmount` or `RemainingOwnerCount` is present, create a `Sponsorship` object ([XLS-68 §3.3](../README.md#33-ledger-entry-sponsorship)) with:
   1. `Owner` set to `tx.Account` and `Sponsee` set to `Destination`
   2. `FeeAmount`, `MaxFee` and `RemainingOwnerCount` copied from the transaction; absent fields stay absent
   3. `Flags` set to `0`, so neither `lsfSponsorshipRequireSignForFee` nor `lsfSponsorshipRequireSignForReserve` is set
   4. The object added to the owner directories of both `tx.Account` and `Destination`
   5. `tx.Account`'s `OwnerCount` incremented by 1
   6. `FeeAmount`, if present, deducted from `tx.Account`'s `Balance`

No XRP is transferred to `Destination`. The `Sponsorship` object is an account deletion blocker for both accounts ([XLS-68 §3.3.6.3](../README.md#3363-account-deletion-blocker)).

#### 3.1.6 Invariants

In addition to the protocol-wide invariants of [XLS-68 §3.16](../README.md#316-invariants), `SponsoredAccountCreate` fails with `tecINVARIANT_FAILED` unless all of the following hold:

1. The transaction modifies only:
   1. the created `AccountRoot` and `Sponsorship` objects;
   2. `DirectoryNode` objects;
   3. the existing `AccountRoot` of `tx.Account`, and that of the fee sponsor if the fee is sponsored;
   4. the existing `Sponsorship` object between the fee sponsor and `tx.Account`, if the fee is sponsored;
   5. a deleted `Ticket`, when `TicketSequence` is used;
   6. the deleted `TransactionProposal` keyed to `tx.Account` and the consumed `TicketSequence` ([XLS-103 §4.5](../../XLS-0103-onchain-cosigner/README.md#45-deletion)), together with the `AccountRoot` of that proposal's `Owner` and of its reserve sponsor.

   No `AccountRoot` or `Sponsorship` is deleted, and no other ledger entry type is created, modified or deleted.

2. If the result is not `tesSUCCESS`, no `AccountRoot` and no `Sponsorship` is created.
3. If the result is `tesSUCCESS`:
   1. Exactly one `AccountRoot` is created, and it is the `Destination`'s.
   2. Its `Sponsor` is `tx.Account`.
   3. Its `Balance` is `0`.
   4. `tx.Account`'s `SponsoringAccountCount` increases by exactly 1.
   5. Exactly one `Sponsorship` is created if `FeeAmount` or `RemainingOwnerCount` is present, and none otherwise.
   6. A created `Sponsorship` has `Owner == tx.Account`, `Sponsee == Destination`, `FeeAmount` and `MaxFee` equal to the transaction's values (absent if absent), `RemainingOwnerCount` equal to the transaction's value or `0` if absent, and `Flags == 0`.

#### 3.1.7 Example JSON

```json
{
  "TransactionType": "SponsoredAccountCreate",
  "Account": "rN7n7otQDd6FczFgLdlqtyMVrn3HMfXpf",
  "Destination": "rfkDkFai4jUfCvAJiZ5Vm7XvvWjYvDqeYo",
  "FeeAmount": "1000000",
  "MaxFee": "1000",
  "RemainingOwnerCount": 2,
  "Fee": "10",
  "Sequence": 3
}
```

### 3.2 Account Creation in the Parent Specification

When the amendment is enabled, `SponsoredAccountCreate` is a second way to create a sponsored account, alongside a `Payment` with `tfSponsorCreatedAccount`. The parent's statements that `Payment` is the only way to create an account ([XLS-68 §3.9](../README.md#39-transaction-payment), [§3.17.2](../README.md#3172-account-sponsorship)) and that a new `AccountRoot` is sponsored only by such a `Payment` ([XLS-68 §3.6.4.2](../README.md#3642-reserve-sponsorship-state-changes), item 1) apply only before the amendment. In both paths the new account's `Sponsor` is `tx.Account`; there is still no third-party `spfSponsorReserve` path for account creation.

## 4. Rationale

A separate transaction was chosen over extending `Payment` because `Payment` always delivers a positive `Amount`. Creating a zero-balance account through `Payment` would mean changing its delivery semantics; a dedicated transaction keeps `Payment` unchanged.

Creating the optional `Sponsorship` object in the same transaction removes the window between account creation and pre-funding, during which a zero-balance account could not pay any transaction fee. The `Sponsorship` fields reuse the names and meaning of the existing `Sponsorship` object fields so that the stored object matches the transaction field by field.

The all-zero `Destination` is rejected with `temDST_NEEDED`, as `Payment` rejects it. An `AccountRoot` at the all-zero address could never submit a transaction, because a transaction with an all-zero `Account` is rejected, so its reserve would be locked permanently.

## 5. Security Considerations

The sponsor's exposure is bounded by the transaction: one base reserve for the new account, one object reserve for the `Sponsorship` object, and `FeeAmount`. `MaxFee` caps what a single sponsored transaction may draw from `FeeAmount`, and the reserve-checking failure in [§3.1.4.2](#3142-protocol-level-failures) ensures the sponsor stays above its own reserve after paying them.

As with `Payment`, `Destination` does not sign. Any account can create a sponsored account at an unfunded address. The new account's `Sponsor` field binds the reserve to the sponsor: if the account is later deleted, `AccountDelete` must send its remaining XRP to the sponsor ([XLS-68 §3.4.1.1](../README.md#3411-sponsor)).

The transaction-specific invariants list every ledger entry the transaction may touch. The only entries outside the new account and `Sponsorship` that it may delete are the consumed `Ticket` and the `TransactionProposal` keyed to that ticket, and the only third-party `AccountRoot`s it may modify are the fee sponsor's and those released by that proposal's deletion. A defect that modified any other account or object fails with `tecINVARIANT_FAILED`.
