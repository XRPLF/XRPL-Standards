<pre>
  xls: 23
  title: Lite Accounts
  description: A proposal for lite accounts with reduced account reserves but limited features
  author: Wietse Wind (@WietseWind)
  proposal-from: https://github.com/XRPLF/XRPL-Standards/discussions/56
  status: Stagnant
  category: Amendment
  created: 2021-08-27
</pre>

# LiteAccounts Amendment

By @RichardAH, @WietseWind

## Introduction

The XRP Ledger is a fast consensus-based blockchain which, unlike competing chains, maintains its user's balances as persistent state rather than as a graph of unspent transaction outputs. This imposes unique per-account storage costs on the network. These costs are passed on to the user.

The cost of creating an account on the ledger is, at time of writing, `5 XRP` with an additional lockup of `15 XRP` (which is redeemable if the account is later deleted). Collectively this is known as the Account Reserve. It has been argued the Account Reserve acts as a barrier to entry for new users and remains a major impedement to the expansion of the ecosystem.

The `AccountRoot` ledger object represents the authoritative state of an XRPL account.

It contains the following fields:

| Field               | Type      | Bytes       | Required | Lite Account |
| ------------------- | --------- | ----------- | -------- | ------------ |
| sfLedgerEntryType   | UInt16    | 3           | ✅       | ✅           |
| sfFlags             | UInt32    | 5           | ✅       | ✅           |
| sfAccount           | AccountID | 22          | ✅       | ✅           |
| sfSequence          | UInt32    | 5           | ✅       | ✅           |
| sfBalance           | Amount    | 9           | ✅       | ✅           |
| sfOwnerCount        | UInt32    | 5           | ✅       | ✅           |
| sfPreviousTxnID     | UInt256   | 33          | ✅       | ✅           |
| sfPreviousTxnLgrSeq | UInt32    | 5           | ✅       | ✅           |
| sfAccountTxnID      | UInt256   | 33          |          |              |
| sfRegularKey        | AccountID | 22          |          |              |
| sfEmailHash         | UInt128   | 17          |          |              |
| sfWalletLocator     | UInt256   | 33          |          |              |
| sfWalletSize        | UInt32    | 5           |          |              |
| sfMessageKey        | Blob      | 33          |          |              |
| sfTransferRate      | UInt32    | 5           |          |              |
| sfDomain            | Blob      | at most 256 |          |              |
| sfTickSize          | UInt8     | 4           |          |              |
| sfTicketCount       | UInt32    | 6           |          |              |
| sfSponsor^^         | AccountID | 22          |          | ✅           |

^^ Part of this proposal

An XRPL Account which owns no on-ledger objects (i.e: does not have any trustlines, escrows, offers, etc.), does not specify a `regular key` and does not set any of its other optional fields has a serialized size of `87 bytes` (excluding storage overhead.)

We propose that any such _minimal_ account root imposes such a small burden on the ledger that it should be able to be treated differently to _full_ account roots.

## Lite Accounts

We propose that a **lite account** is an XRPL Account with:

- a _minimal_ account root
- the _new_ `asfLiteAccount` account flag set, and,
- (optionally) the _new_ `sfSponsor` field set.

#### Lite accounts have an Account Reserve of `1/5th` the ledger's object reserve (i.e. `1 XRP` at time of writing.)

## ⚠️ Restrictions

A lite account **cannot**:

- Own on-ledger objects, and thus cannot:
  - Hold or create Trustline balances
  - Have non-default limits on incoming trustlines
  - Create Offers
  - Create Escrows
  - Create Checks
  - Create Payment Channels
  - Create or install Hooks (pending amendment)
  - Set or use a Signer List
  - Create Tickets
  - Require or use Deposit Authorizations
  - Set or use a Regular Key
- Become a sponsor for another lite account
- Perform `AccountSet` on any fields except `sfSponsor` and `sfFlags`

## New Fields and Flags

The following changes are made to fields and flags.

1. `sfSponsor` — a new optional _AccountID_ field on the acount root which indicates that another account owns the reserve for the account root.
2. `tfSponsor` — a new transaction flag that indicates the intent of the sender to create and sponsor a new lite account.
3. `asfLiteAccount` — a new account flag that can be set and unset subject to certain conditions, which indicates that the account is a lite account and subject to the restrictions of a lite account.

These are explained in further detail below.

## Sponsorship

Lite accounts may be _sponsored_. Sponsorship provides that another account pays the account reserve and, subject to conditions, is entitled to recover the entire account reserve should the lite account be later deleted. _Full_ accounts cannot be sponsored, only accounts with `asfLiteAccount` flag can be sponsored.

To sponsor a new account creation:
A `ttPAYMENT` transaction is created and successfully submitted, which:

1. Specifies an unfunded destination account,
2. Specifies the (new) `tfSponsor` flag, and
3. Sends at least as much `XRP` as the lite account reserve.

There is no way for an already established XRPL account (full or lite) to subsequently become a sponsored account. Sponsorship can only occur through account creation.

## Reclamation

A **sponsor** is entitled to _reclaim_ the Account Reserve on a lite account (for which they are the sponsor) subject to certain conditions:

### Scenario 1: AccountDelete

If a sponsored lite account:

- contains less than two times the lite account reserve, and
- does not sign and submit any transaction that results in a `tesSUCCESS` on a validated ledger for more than `1 million` ledgers,

Then the account's sponsor may recover the Account Reserve via an `AccountDelete` transaction. The spsonsor also receives the remaining balance in the lite account.

The `AccountDelete` transaction specifies the lite account as the `sfAccount` field but is signed by the sponsor.

### Scenario 2: AccountSet

If a sponsored lite account, at any time:

- contains at least two times the lite account reserve

Then the account's `sponsor` may recover the Account Reserve via an `AccountSet` transaction that _clears_ the `sfSponsor` field.

The `AccountSet` transaction specifies the lite account as the `sfAccount` field but is signed by the sponsor and can only be used to delete the `sfSponsor` field.

Doing so results in a balance mutation on both the lite account and the sponsor account to reflect the return of the lite Account Reserve.

## Upgrading

The owner of a lite account can upgrade their account twice:

### Scenario 1: Removal of Sponsor

The owner of a lite account may unilaterally unsponsor his or her own account by:

- ensuring the account contains at least twice the lite Account Reserve, and
- creating and successfully submitting an `AccountSet` transaction that _clears_ the `sfSponsor` field.

Doing so results in a balance mutation on both the lite account and the sponsor account to reflect the return of the lite Account Reserve.

### Scenario 2: Full Account

The owner of an unsponsored lite account may upgrade the account to a _full_ account by:

- ensuring the account contains at least the Full Account Reserve (at time of writing `20 XRP`)
- creating and successfully submitting an `AccountSet` transaction that _clears_ the `asfLiteAccount` flag.

## Downgrading

The owner of a _full_ account may opt to downgrade their account to a lite account by:

- creating and successfully submitting an `AccountSet` transaction that _sets_ the `asfLiteAccount` flag. This action frees up the difference between the full Account Reserve and the lite Account Reserve.

## Deletion of Lite Accounts

The owner of a lite account may delete their account subject to certain conditions:

### Scenario 1: Send all to Sponsor

If the lite account is sponsored then the owner of the lite account may:

- create and successfully submit an `AccountDelete` transaction, which
- specifies the account `sponsor` as the `Destination` field

### Scenario 2: Upgrade and Delete

If the lite account is sponsored then the owner of the lite account may upgrade their account to an unsponsored account.
Once the lite account is unspsonsored, the user may proceed with a normal `AccountDelete` operation (with the proceeds going to any desired `Destination`).
