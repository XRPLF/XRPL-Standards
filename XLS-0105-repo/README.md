<pre>
  title: Repo
  description: Bilateral repurchase agreements with on-ledger collateral and time-proportional interest.
  author: Denis Angell (@dangell7)
  proposal-from: https://gist.github.com/dangell7/a7bc0c5b3ef0767b36f09f21543abd81
  status: Draft
  category: Amendment
  requires: XLS-85
  created: 2026-08-04
  updated: 2026-09-11
</pre>

# Repo

## 1. Abstract

This amendment adds a repurchase agreement (repo) primitive to the XRP Ledger.
A seller locks collateral and receives cash from a buyer (leg 1). The seller has
a committed, enforceable right to buy the collateral back by paying principal
plus time-proportional interest before maturity (leg 2). If the seller does not
pay by maturity plus a grace period, anyone can trigger default and the buyer
keeps the collateral.

It is one ledger entry and five transactions, using the ledger's native
offer/accept idiom. Most of the machinery already exists: the locking comes
from Token Escrow (XLS-85) and the rate math, rounding and grace/default
semantics come from Lending (XLS-66). The genuinely new piece is a
payment-gated release, collateral that only unlocks when a specific payment
lands in the same transaction. Nothing on the ledger does that today.

## 2. Motivation

Repo is the plumbing of institutional liquidity. The US market alone runs about
$12.6T in daily exposures, and roughly 80% of tri-party volume is overnight.
Tokenized repo is also the largest proven blockchain use case in finance:
Broadridge clears about $9T a month on DLR, and JPMorgan's Kinexys has settled
over $3T. Kinexys' signature product is intraday repo, borrowing against
collateral for a few hours and paying interest only for the minutes outstanding.

Every live platform automates the same slice: atomic DvP creation, immobilized
collateral, deterministic unwind. None of them put margin calls, substitution
or netting on-chain. That all falls back to the GMRA legal framework, and
adoption happened anyway. This spec follows the same line: automate the
performing trade, leave enforcement exotica to the contract referenced in the
`Data` field.

The design choice that matters most: interest accrues on actual elapsed time.
That one choice gives overnight, term and intraday repo from the same object.

## 3. Specification

The key words "MUST", "MUST NOT", "SHOULD", "SHOULD NOT" and "MAY" in this
document are to be interpreted as described in RFC 2119 and RFC 8174.

### 3.1. Ledger Entry: `Repo`

#### 3.1.1. Object Identifier

**Key Space:** `0xXXXX` (TBD, next free value)

The ID is the tagged hash of the key space prefix, the seller's `AccountID`,
and the transaction `Sequence` (or ticket) of the creating `RepoCreate`. One
create, one object, no collisions.

#### 3.1.2. Fields

| Field Name        | Constant | Required    | Internal Type | Default | Description                                                                                             |
| ----------------- | -------- | ----------- | ------------- | ------- | ------------------------------------------------------------------------------------------------------- |
| LedgerEntryType   | Yes      | Yes         | UINT16        | TBD     | Identifies this as a `Repo` entry                                                                       |
| Account           | No       | Yes         | ACCOUNT       | N/A     | Seller (cash borrower). Owns the entry                                                                  |
| Counterparty      | No       | Yes         | ACCOUNT       | N/A     | Buyer (cash lender)                                                                                     |
| CollateralAmount  | No       | Yes         | AMOUNT        | N/A     | XRP, IOU or MPT locked for the term                                                                     |
| PurchasePrice     | No       | Yes         | AMOUNT        | N/A     | Cash delivered to the seller at accept. MUST be a different asset than the collateral                   |
| InterestRate      | No       | Yes         | UINT32        | N/A     | Annualized rate in 1/10 basis points (XLS-66 convention). 0 is valid                                    |
| Expiration        | No       | Yes         | UINT32        | N/A     | Pending offer expiry. After this, anyone MAY cancel                                                     |
| StartDate         | No       | Conditional | UINT32        | N/A     | Set by `RepoAccept` to that ledger's close time. Absent while pending                                   |
| MaturityDate      | No       | Yes         | UINT32        | N/A     | Latest permissible repurchase. MUST be greater than `StartDate`                                         |
| GracePeriod       | No       | Yes         | UINT32        | N/A     | Seconds after `MaturityDate` before default becomes possible                                            |
| TransferRate      | No       | Optional    | UINT32        | N/A     | Collateral issuer's transfer rate captured at create (XLS-85 pattern)                                   |
| Data              | No       | Optional    | BLOB          | N/A     | Up to 256 bytes. Pointer to the governing legal annex or trade ID. Institutions need the GMRA reference |
| OwnerNode         | No       | Yes         | UINT64        | N/A     | Owner directory hint (seller)                                                                           |
| DestinationNode   | No       | Yes         | UINT64        | N/A     | Owner directory hint (buyer)                                                                            |
| IssuerNode        | No       | Conditional | UINT64        | N/A     | Issuer directory hint for issued-asset collateral, per XLS-85                                           |
| PreviousTxnID     | No       | Yes         | HASH256       | N/A     | Standard                                                                                                |
| PreviousTxnLgrSeq | No       | Yes         | UINT32        | N/A     | Standard                                                                                                |

There is no haircut field. The haircut is whatever the parties negotiated into
`PurchasePrice` relative to the collateral's value. In cleared dealer flow the
haircut is often 0% anyway, and the protocol should not be pricing collateral.

The repurchase price is computed at close, not stored:

```
RepurchaseAmount = PurchasePrice * (1 + InterestRate * elapsed / 31,536,000)
elapsed          = min(closeTime, MaturityDate) - StartDate      [seconds]
```

Computed in `Number`, rounded up to the cash asset's precision per the XLS-66
rounding rules. The protocol never loses to rounding. Close after two hours,
pay two hours of interest. That is the intraday product.

#### 3.1.3. Flags

None in v1. The pending/active state is derived from the presence of
`StartDate`.

#### 3.1.4. Ownership

The entry is owned by `Account` (the seller) and appears in both parties'
owner directories, plus the issuer directory for issued-asset collateral
(XLS-85 pattern).

#### 3.1.5. Reserves

One owner reserve, charged to `Account`.

#### 3.1.6. Deletion

Deleted by exactly three paths: `RepoCancel` (pending), `RepoClose` (active,
paid) and `RepoDefault` (active, expired). An account with an open `Repo`
cannot be deleted.

#### 3.1.7. Freeze/Lock

Collateral locking follows XLS-85 exactly: issuer opt-in via
`lsfAllowTrustLineLocking` (IOU) and `lsfMPTCanEscrow` (MPT),
`sfLockedAmount` accounting, and the XLS-85 freeze tables at create, close
and default time.

#### 3.1.8. Invariants

1. A `Repo` is created (pending) if and only if exactly `CollateralAmount`
   becomes newly locked from `Account` and zero cash moves.
2. Pending to active via `RepoAccept` requires exactly `PurchasePrice`
   delivered from `Counterparty` to `Account` and `StartDate` set to that
   ledger's close time.
3. Deletion via `RepoCancel` requires full unlock to `Account` and zero cash
   moved. If the submitter is not the seller, the close time MUST be past
   `Expiration`.
4. Deletion via `RepoClose` requires the buyer credited at least the computed
   `RepurchaseAmount` (net of the cash asset's transfer rate) and the full
   collateral unlocked to the seller. `RepurchaseAmount >= PurchasePrice`
   always, since the rate is non-negative and rounding goes up.
5. Deletion via `RepoDefault` requires close time past
   `MaturityDate + GracePeriod`, full collateral delivered to `Counterparty`,
   and zero cash moved.
6. While any `Repo` exists, aggregate locked balances are at least the sum of
   open Repo and Escrow collateral. This extends the XLS-85 locked-balance
   invariant.
7. `CollateralAmount`, `PurchasePrice`, `InterestRate` and `MaturityDate` are
   immutable after create. Changing terms means close and recreate.

#### 3.1.9. RPC Name

`repo` (in `account_objects` and `ledger_entry`).

### 3.2. Transaction: `RepoCreate`

The seller's offer. Locks the collateral immediately and creates the entry in
a pending state. Locking at create matters: the buyer accepts against proven,
immobilized collateral, not a promise.

#### 3.2.1. Fields

| Field Name       | Required | Internal Type | Description                                        |
| ---------------- | -------- | ------------- | -------------------------------------------------- |
| Account          | Yes      | ACCOUNT       | Seller                                             |
| Counterparty     | Yes      | ACCOUNT       | Buyer. Pinned; open offers are out of scope for v1 |
| CollateralAmount | Yes      | AMOUNT        | Asset to lock                                      |
| PurchasePrice    | Yes      | AMOUNT        | Cash the buyer must deliver at accept              |
| InterestRate     | Yes      | UINT32        | Annualized, 1/10 basis points                      |
| Expiration       | Yes      | UINT32        | Offer expiry                                       |
| MaturityDate     | Yes      | UINT32        | Repurchase deadline                                |
| GracePeriod      | Yes      | UINT32        | Seconds of grace after maturity                    |
| Data             | Optional | BLOB          | Legal annex or trade ID reference                  |

#### 3.2.2. Failure Conditions

Follows the XLS-85 create table: frozen, unauthorized or non-lockable assets
fail. Additionally: the issuer of the collateral MUST be neither party,
collateral and cash MUST be different assets, `Counterparty` MUST NOT be
`Account`, and `MaturityDate` MUST be sane relative to `Expiration`.

#### 3.2.3. State Changes

Collateral locked from `Account` (XLS-85 machinery), `Repo` entry created in
both owner directories (plus issuer directory for issued assets), one owner
reserve charged.

### 3.3. Transaction: `RepoAccept`

The buyer's activation. Valid only from the pinned `Counterparty`, while
pending, before `Expiration`.

#### 3.3.1. Fields

| Field Name | Required | Internal Type | Description                                   |
| ---------- | -------- | ------------- | --------------------------------------------- |
| Account    | Yes      | ACCOUNT       | Buyer (must equal the entry's `Counterparty`) |
| RepoID     | Yes      | HASH256       | The pending `Repo` entry                      |

#### 3.3.2. Failure Conditions

Not the pinned counterparty, already active, past `Expiration`, or the
payment of `PurchasePrice` fails (insufficient funds, frozen cash asset).

#### 3.3.3. State Changes

`PurchasePrice` delivered from buyer to seller through the payment engine,
`StartDate` set to this ledger's close time. The repo is active. Interest runs
from when the cash actually moved, not from when the offer was posted.

### 3.4. Transaction: `RepoCancel`

Pre-accept exit. The seller at any time while pending, or anyone after
`Expiration` (keeper-friendly, same permissioning idea as EscrowCancel).

#### 3.4.1. Failure Conditions

Entry is active, or the submitter is neither the seller nor past `Expiration`.

#### 3.4.2. State Changes

Collateral unlocked back to the seller, entry deleted, reserve released. No
cash moves.

### 3.5. Transaction: `RepoClose`

Leg 2, and the new primitive. Submitted by the seller any time up to
`MaturityDate + GracePeriod`.

#### 3.5.1. Failure Conditions

Not the seller, entry still pending, past `MaturityDate + GracePeriod`, or the
payment of `RepurchaseAmount` fails. A failed payment fails the whole
transaction and the collateral stays locked. That gate is the primitive:
nothing else on the ledger releases an asset conditional on a payment landing.

#### 3.5.2. State Changes

In one transaction: `RepurchaseAmount` computed and paid seller to buyer
through the payment engine (buyer-side trustline/MPToken auto-creation per the
XLS-85 finish rules), collateral unlocked back to the seller, entry deleted.

### 3.6. Transaction: `RepoDefault`

Submittable by anyone once close time passes `MaturityDate + GracePeriod`,
same permissioning as EscrowFinish/Cancel so keepers can automate it.

#### 3.6.1. Failure Conditions

Entry pending, or close time not yet past `MaturityDate + GracePeriod`.

#### 3.6.2. State Changes

Collateral delivered to `Counterparty` at the stored `TransferRate`, entry
deleted. No oracle and no partial settlement. The buyer keeps all the
collateral, and the negotiated haircut is the seller's over-collateralization
loss. That mirrors GMRA close-out economics for a fully collateralized single
trade. Note the escrow model removes a failure mode traditional repo has to
patch: the buyer can never fail to return collateral, because the buyer never
holds it.

### 3.7. Lifecycle

```
  RepoCreate (seller)                       RepoAccept (buyer, before Expiration)
  collateral locked --> [ Repo: PENDING ] -- cash to seller --> [ Repo: ACTIVE ]
                              |                                      |
                   RepoCancel (seller anytime,     +-----------------+------------------+
                   anyone after Expiration)        |                                    |
                   unlock to seller, delete   RepoClose (seller,               RepoDefault (anyone,
                                              t <= Maturity+Grace)             t > Maturity+Grace)
                                              pays P*(1+r*elapsed/yr)          collateral to buyer,
                                              unlock to seller, delete         delete
```

Pending has one entrance and two exits. Active has two exits. There are no
other states. Single-shot atomic DvP is `Batch(RepoCreate, RepoAccept)`
(XLS-56). An open (rolling) repo is a daily
`Batch(RepoClose, RepoCreate, RepoAccept)`.

## 4. Rationale

**Offer/accept, not dual-signature.** An earlier draft used the XLS-66
`CounterpartySignature` dual-sign, both parties signing one transaction. I
dropped it. Collecting a second signature on one blob is operationally
hostile: no wallet supports it, institutional signing ceremonies add hours,
and there is no async path. It is also the exception pattern on this ledger.
Offers, Checks, NFTokenOffers and PayChan are all offer/accept, each party
signs its own transaction on its own schedule. A desk that can coordinate
signatures still gets single-shot atomic DvP by wrapping Create and Accept in
a Batch, so we lose nothing by choosing the simple path.

**Computed repurchase price.** Storing a fixed repurchase price would lock the
object to term repo. Computing it from elapsed time gives intraday repo for
free, which is the product Kinexys proved institutions actually pay for.

**Field-free haircut and no collateral pricing.** The protocol has no business
valuing collateral. Parties negotiate the price, the ledger enforces the
mechanics.

**All-collateral default with no oracle.** Oracle-priced surplus refund sounds
fair and adds an oracle to the trust model of a settlement primitive. For a
fully collateralized single trade, buyer-keeps-collateral is exactly the GMRA
close-out outcome. Surplus refund can come later as an opt-in (see FAQ).

**What v1 leaves out.** Collateral substitution, variation margin, repricing,
tri-party agent roles, GC baskets, netting, negative rates, coupon
pass-through, rehypothecation of locked collateral, and on-ledger matching.
Matching and negotiation stay off-ledger, same as every live platform.
Broadridge runs $9T a month without any of these, and about 80% of real volume
is overnight GC, which v1 covers completely.

**Privacy and market transparency.** Everything in a v1 `Repo` is public:
sizes, rates, maturities, counterparties. That is a deliberate trade.
Transparency is the product: a public ledger of real repo trades produces a
verifiable overnight rate curve. SOFR is computed by the NY Fed from data
nobody outside can audit. An on-chain repo market is its own benchmark, every
rate provable, every volume real. Only a public ledger can offer that, and it
is the actual differentiator against Broadridge and Kinexys, which get their
confidentiality from running permissioned chains. Desks that need privacy
today use omnibus and agent accounts, secrecy at the identity layer. Once
Confidential MPT (XLS-96) lands, v2 can make the amounts commitments while
the structure stays publicly enforceable. What we will not do is move the
terms off-chain into `Data`: if the rate and price are not on-chain,
`RepoClose` cannot compute or enforce anything, and the primitive degenerates
into off-chain repo with a hash attached.

## 5. Backwards Compatibility

None. This is a new amendment gated behind `featureRepo`, purely additive.
No existing entry, transaction or RPC changes behavior.

## 6. Test Plan

jtx suite covering: the full amendment-gating matrix, create/accept/cancel/
close/default across XRP, IOU and MPT collateral crossed with frozen, locked,
unauthorized and deep-frozen states (the XLS-85 tables), accrual rounding at
asset precision boundaries, `Expiration` and `GracePeriod` boundary ledgers,
third-party cancel and default permissioning, transfer-rate interaction on
both assets in `RepoClose`, invariant checks on every path, and the Batch
compositions (atomic DvP, rollover).

## 7. Reference Implementation

TBD. Sizing: one ledger entry, five transactions, one invariant class, RPC and
serialization support. Roughly 3 to 4k new C++ LOC, about 3.5 to 5.5
engineer-months to audit-ready, roughly twice TokenEscrow and well under half
of Lending. `Supported::Yes`, `VoteBehavior::DefaultNo`.

## 8. Security Considerations

- `RepoClose` is the novel money-movement path: a payment and an unlock on two
  different assets in one transaction, each with its own transfer rate. This
  is where the audit should spend its time.
- Accrual rounding reuses the XLS-66 round-up rules verbatim, the protocol
  never loses to rounding.
- Freeze, lock and authorization edge cases at create, close and default time
  follow the XLS-85 tables, which review has already litigated.
- Default is deliberately non-blockable. Neither party can prevent
  `RepoDefault` after the grace period, since anyone can submit it. A frozen
  cash asset can block `RepoClose`; the seller's remedy is the grace period
  and, failing that, default, which moves no cash.
- The pending state is bounded by `Expiration` and cancellable by anyone after
  it, so offers cannot be used to grief reserves indefinitely.

# Appendix

## Appendix A: FAQ

### A.1: Isn't this just Batch + TokenEscrow?

No, and provably. First, the leg-2 cash cannot be pre-funded: escrow debits at
create, and the repo seller by definition does not hold the repurchase cash
during the term. That is why the trade exists. Second, escrow is a one-way
conditional transfer, not an exchange: if the buyer escrows the collateral
back with `FinishAfter` at maturity, anyone can finish it after maturity and
the seller recovers the collateral without paying. Third, a dual-signed Batch
at maturity is not a commitment, it needs the buyer's fresh signature at
maturity, and if either party walks there is no on-ledger recourse. That is
off-chain repo with extra steps. And nothing in a composition accrues
time-proportional interest, triggers default, or keeps the collateral
immobilized during the term.

### A.2: Why a new ledger object instead of building it into Escrow?

Repo is an inverted escrow. Return-to-owner is the happy path and requires a
payment, delivery-to-destination is the default path after the deadline.
Building that into Escrow means a mode flag that flips the meaning of Finish
and Cancel and puts a payment inside EscrowCancel. Every existing integrator
assumes cancel refunds, finish delivers, and no other money moves. Breaking
that in already-audited transactors doubles their branch space and
contaminates Escrow with repo-only fields forever. This spec reuses Escrow's
machinery (lock helpers, locked-balance accounting, freeze tables) as shared
code, not its object or its transactors. Same engine, new nameplate.

### A.3: Doesn't the Lending Protocol (XLS-66) already cover this?

No. Lending is vault-intermediated, under-collateralized and amortizing. Repo
is bilateral, fully collateralized and bullet-maturity. Different products for
different counterparties.

### A.4: What happens if the collateral is worth less than the cash at default?

The buyer eats it, same as under-margined traditional repo. The haircut
negotiated into `PurchasePrice` is the buyer's protection, and v1 deliberately
has no oracle. If the market wants oracle-priced surplus refund or margining,
that is a v2 opt-in, not a v1 requirement. Every live tokenized-repo platform
ships without it.

### A.5: Can the buyer use the collateral during the term (rehypothecation)?

No. The collateral sits in the ledger lock, not in the buyer's account. That
is a feature: it removes the buyer-fail-to-return risk that GMRA mini
close-out exists to patch, and it is the same immobilization model Broadridge
runs at $9T a month.

## Appendix B: References

- XLS-85 Token Escrow: locking model, issuer flags, freeze tables
- XLS-66 Lending Protocol: rate math, GracePeriod and default handling
- XLS-56 Batch: atomic create+accept, rollover composition
- GMRA 2011: mini close-out, close-out netting. OFR and NY Fed US repo statistics
- Broadridge DLR (~$9T/month), JPMorgan Kinexys intraday repo (>$3T cumulative),
  Canton/Circle tokenized-UST repo: the adoption precedents this design follows
