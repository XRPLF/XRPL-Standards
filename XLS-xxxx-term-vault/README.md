---
xls: TBD
title: Closed-Ended Single Asset Vault
description: Adds a fixed-term, phase-based vault kind to the Single Asset Vault so lenders can lock capital for a defined investment period.
author: TBD
status: Draft
category: Amendment
created: 2026-07-21
updated: 2026-07-21
---

<pre>
  title: WASM VM
  description: WebAssembly VM integration into rippled
  author: Mayukha Vadari (@mvadari), Peng Wang (@pwang200), Oleksandr Pidskopnyi (@oleks_rip), David Fuelling (@sappenin)
  proposal-from: https://github.com/XRPLF/XRPL-Standards/discussions/303
  status: Draft
  category: Amendment
  created: 2025-08-08
  updated: 2026-02-03
</pre>

# Closed-Ended Single Asset Vault

## 1. Abstract

The Single Asset Vault (XLS-65) is *open-ended*: depositors may deposit or withdraw at any time. When a vault's cash is deployed into loans (XLS-66), its liquid balance (`AssetsAvailable`) drops below its net asset value (`AssetsTotal`), and any withdrawal larger than the liquid balance fails with `tecINSUFFICIENT_FUNDS`. This makes an open-ended vault unsuitable for fixed-term lending, where liquidity is intentionally locked until loans mature.

This proposal introduces a new **closed-ended** vault kind that moves through three deterministic phases - **Subscription**, **Investment**, and **Redemption** - and restricts deposits and withdrawals according to the current phase. It adds two fields to the `Vault` ledger entry (`VaultKind`, `RedemptionDate`) plus a maintained `LoanCount` for O(1) loan tracking, and phase enforcement in the vault and lending transactors. The Subscription-to-Investment boundary is *loan-driven* - a vault leaves Subscription as soon as it has its first active loan (`LoanCount > 0`) - while the Investment-to-Redemption boundary is the immutable `RedemptionDate`. Open-ended vaults are behaviourally unaffected.

## 2. Motivation

TBD

## 3. Specification

This feature is gated behind `LendingProtocolV1_1`.

### 3.1. Enumerations

```c++
enum class VaultKind : uint8_t {
    OpenEnded      = 0,   // default; existing behaviour
    ClosedEndedFixed = 1, // fixed-term, phase-based
};

enum class VaultPhase : uint8_t {
    Invalid      = 0,     // returned for open-ended vaults (no phases)
    Subscription = 1,
    Investment   = 2,
    Redemption   = 3,
};
```

`VaultKind` is persisted on the ledger (in `sfVaultKind`). `VaultPhase` is **never stored**; it is derived at run time from the vault's kind, its `RedemptionDate`, its active-loan count (`sfLoanCount`), and the parent ledger close time (see 3.4).

### 3.2. New Serialized Fields

| SField             | Type   | Notes                                                        |
| ------------------ | ------ | ----------------------------------------------------------- |
| `sfVaultKind`      | UINT8  | Next free UINT8 index. Stores a `VaultKind` value.          |
| `sfRedemptionDate` | UINT32 | Next free UINT32 index. Seconds since Ripple epoch.         |
| `sfLoanCount`      | UINT32 | Next free UINT32 index. Count of *active* `Loan` objects.   |

> The exact numeric field codes MUST be assigned to currently-unused indices in
> `sfields.macro` at implementation time; they are intentionally left as "next
> free" here to avoid collisions with concurrent proposals.

**Design note** The phases are derived from the vault's active-loan count and `RedemptionDate` - a vault may move between Subscription and Investment more than once as loans are originated and resolved:

- **Subscription** (`sfLoanCount == 0`, before `RedemptionDate`): deposits and withdrawals are open. Capital can enter and exit freely while the vault holds no active loans.
- **Investment** (`sfLoanCount > 0`, before `RedemptionDate`): both deposits and withdrawals are rejected. The vault is locked while at least one active loan is deployed. Fully repaying or defaulting every active loan returns `sfLoanCount` to `0` and moves the vault back to Subscription (still before `RedemptionDate`).
- **Redemption** (on/after `RedemptionDate`): withdrawals open; new deposits rejected. Depositors exit at NAV.

See 4.1 for how the phases behave over the vault's lifetime.

### 3.3. Ledger Entry: `Vault` (modified)

The following fields are added to the existing `ltVAULT` ledger entry. All are `SoeOptional`/`SoeDefault` so pre-existing serialized vaults remain valid; open-ended vaults retain their existing behaviour.

| Field Name         | Constant | Required     | Internal Type | Default   | Description                                                              |
| ------------------ | -------- | ------------ | ------------- | --------- | ------------------------------------------------------------------------ |
| `VaultKind`        | Yes      | No           | UINT8         | `0`       | `VaultKind`. Absent/`0` means open-ended. Immutable after creation.      |
| `RedemptionDate`   | Yes      | Conditional  | UINT32        | N/A       | Start of Redemption phase. REQUIRED iff `VaultKind == ClosedEndedFixed`. |
| `LoanCount`        | No       | No           | UINT32        | `0`       | Number of *active* (outstanding) `Loan` objects funded by this vault. Maintained field.|

**Field semantics.**

- `VaultKind` and `RedemptionDate` are **immutable**: they are set only by `VaultCreate` and MUST NOT be changed by `VaultSet` or any other transaction.
- For a closed-ended vault, `RedemptionDate` MUST be strictly greater than the ledger close time at creation.
- `LoanCount` counts **active** loans only - loans that have been activated and still have outstanding obligations. It is incremented when a loan becomes active (immediate `LoanSet`, or `LoanAccept` in the two-step flow) and decremented when an active loan becomes inactive (fully repaid via `LoanPay`, or defaulted via `LoanManage`). A merely *pending* loan (two-step, awaiting `LoanAccept`) is **not** counted, and a fully-repaid or defaulted loan is no longer counted even though its `Loan` object persists until `LoanDelete`. `LoanCount > 0` gives an O(1) answer to "does this vault have any active loan?" (see 4.2) and is what distinguishes Subscription from Investment. It has no behavioural effect on open-ended vaults, for which `getVaultPhase` returns `Invalid`.

### 3.4. Helper: `getVaultPhase`

```c++
VaultPhase getVaultPhase(ReadView const& view, SLE::const_ref vault) 
{
    if (getVaultKind(vault) != VaultKind::ClosedEndedFixed)
        return VaultPhase::Invalid;          // open-ended: no phases
    now = view.parentCloseTime();            // seconds since Ripple epoch
    if (now >= vault[sfRedemptionDate])
        return VaultPhase::Redemption;
    if (vault[~sfLoanCount].value_or(0) == 0)
        return VaultPhase::Subscription;     // no active loan yet
    return VaultPhase::Investment;           // capital deployed, pre-redemption
}
```

`getVaultKind` mirrors `getVaultVersion`: it returns `OpenEnded` when `sfVaultKind` is absent, the decoded value when present and valid, and a distinct invalid sentinel otherwise.

### 3.5. Phase / Kind rules matrix

| Transaction   | Open-ended            | Subscription | Investment | Redemption |
| ------------- | --------------------- | ------------ | ---------- | ---------- |
| VaultDeposit  | allowed               | allowed      | rejected   | rejected   |
| VaultWithdraw | allowed               | allowed      | rejected   | allowed    |
| LoanSet       | allowed               | allowed\*    | allowed\*  | rejected   |
| LoanAccept    | allowed               | allowed      | allowed    | rejected   |
| LoanPay       | allowed               | allowed      | allowed    | allowed    |
| LoanManage    | allowed               | allowed      | allowed    | allowed    |
| LoanDelete    | allowed               | allowed      | allowed    | allowed    |
| VaultClawback | allowed               | allowed      | allowed    | allowed    |

The Subscription and Investment columns are not delimited by a stored date: a closed-ended vault is in **Subscription** while `sfLoanCount == 0` and in **Investment** once `sfLoanCount > 0` (both before `RedemptionDate`). Creating the first *active* loan is therefore what advances the vault from Subscription to Investment, and fully repaying or defaulting the last active loan returns `sfLoanCount` to `0` and moves the vault back to Subscription (see 4.1). `Redemption` begins unconditionally at `RedemptionDate`.

\* `LoanSet` (and `LoanAccept`) are permitted only before `RedemptionDate`. A closed-ended `LoanSet` is additionally constrained so the loan fully matures before Redemption (see 3.6.4).

### 3.6. Transaction changes

#### 3.6.1. `VaultCreate`

- Accepts a new OPTIONAL field `sfVaultKind`. If absent, the vault is `OpenEnded` and behaviour is unchanged.
- If `sfVaultKind == ClosedEndedFixed`:
  - `sfRedemptionDate` is REQUIRED.
  - `RedemptionDate >` ledger close time, otherwise `temMALFORMED`.
  - The transactor sets `sfVaultKind` and `sfRedemptionDate`. `sfLoanCount` is left absent (treated as `0`) until the first active loan increments it.
- If `sfVaultKind == OpenEnded` (or absent) but `sfRedemptionDate` is present, return `temMALFORMED`.
- If `sfVaultKind` holds an unknown enum value, return `temMALFORMED`.

#### 3.6.2. `VaultDeposit`

`preclaim` computes `getVaultPhase`. Regardless of vault kind, deposits are
rejected when the phase is `Investment` or `Redemption`, returning
`tecNO_PERMISSION`; they are permitted in `Subscription` and `Invalid`. Because
`getVaultPhase` returns `Invalid` for open-ended vaults, they are never rejected
and thus unaffected; closed-ended vaults are rejected in `Investment` and
`Redemption`.

#### 3.6.3. `VaultWithdraw`

`preclaim` computes `getVaultPhase`. Regardless of vault kind, withdrawals are rejected when the phase is `Investment`, returning `tecNO_PERMISSION`; they are permitted in `Subscription`, `Redemption`, and `Invalid`. Because `getVaultPhase` returns `Invalid` for open-ended vaults, they are always permitted and thus unaffected; closed-ended vaults are blocked only in `Investment`. The existing `AssetsAvailable` cap and share-pricing logic are unchanged.

#### 3.6.4. `LoanSet`

- **Immediate (one-step) flow:** the loan is disbursed and becomes active immediately, so `LoanSet` increments the funding vault's `sfLoanCount` and `view.update`s the vault.
- **Two-step (pending) flow:** `LoanSet` creates a pending (`lsfLoanPending`) loan that is not yet active and not yet disbursed. It MUST NOT change `sfLoanCount`; the increment is deferred to `LoanAccept` (3.6.5).
- For closed-ended vaults (both flows):
  - The vault MUST be before `RedemptionDate` (i.e. `getVaultPhase` is `Subscription` or `Investment`), else `tecNO_PERMISSION`.
  - The loan's final grace-period end, `startDate + (paymentInterval × paymentTotal) + gracePeriod`, MUST be `<= RedemptionDate`, else `tecNO_PERMISSION` (loan would outlive the term).

#### 3.6.5. `LoanAccept`

- Activates a pending loan created by the two-step `LoanSet`. Because the loan becomes active here, `LoanAccept` increments the funding vault's `sfLoanCount` and `view.update`s the vault.
- For closed-ended vaults, the vault MUST be before `RedemptionDate`, else `tecNO_PERMISSION` (a loan cannot be activated during Redemption). This is in addition to the existing `StartDate`-based proposal-expiry check.

#### 3.6.6. `LoanPay`

- When a payment causes an **active** loan to become fully repaid - i.e. `sfPaymentRemaining` transitions from `> 0` to `0` (at which point `sfPrincipalOutstanding` is also zeroed) - `LoanPay` decrements the funding vault's `sfLoanCount` and `view.update`s the vault. `LoanPay` already loads and updates the vault, so no extra lookup is required.
- The decrement MUST be driven by the `sfPaymentRemaining > 0 → 0` transition, **not** by the `tfLoanFullPayment` flag: a final *regular* installment also pays a loan off, and an early full payoff (`tfLoanFullPayment`) is only one way to reach zero. A payment that leaves `sfPaymentRemaining > 0` MUST NOT change `sfLoanCount`.
- A pending loan cannot be paid, so this path never applies to `lsfLoanPending` loans.

#### 3.6.7. `LoanManage`

- When `LoanManage` **defaults** an active loan (`tfLoanDefault`), the loan becomes inactive - its outstanding balances and `sfPaymentRemaining` are zeroed
  - so `LoanManage` decrements the funding vault's `sfLoanCount` and `view.update`s the vault.
- Impair/unimpair (`tfLoanImpair` / `tfLoanUnimpair`) do **not** change `sfLoanCount`: an impaired loan is still active (it retains outstanding obligations and may yet be repaid).

#### 3.6.8. `LoanDelete`

- `LoanDelete` MUST NOT change `sfLoanCount`. An active loan can only be deleted once it is fully repaid or defaulted, at which point it was already decremented by `LoanPay` or `LoanManage`; decrementing again would under-count. A pending loan was never counted. In all cases the count is left unchanged.

#### 3.6.9. `VaultSet`

- MUST reject any attempt to set/alter `sfVaultKind` or `sfRedemptionDate` with `temMALFORMED` (data verification) - these are immutable.

#### 3.6.10. `VaultDelete`

- Adds a defensive precondition: `sfLoanCount == 0`, returning `tecHAS_OBLIGATIONS` otherwise. (Complements the existing `AssetsTotal == 0` and empty-pseudo-directory checks.) `sfLoanCount` now counts only *active* loans, so a pending, fully-repaid, or defaulted loan is not counted. Such loans cannot orphan a vault regardless: a pending loan reserves principal (`sfAssetsReserved > 0`), and every undeleted `Loan` (pending, repaid, or defaulted) holds a broker owner-count that blocks `LoanBrokerDelete` (`sfOwnerCount != 0`), which in turn keeps the vault's pseudo-account directory non-empty and blocks `VaultDelete`. The existing asset/directory guards therefore already prevent deleting a vault while any `Loan` object exists.

### 3.7. Invariants

- `VaultKind` and `RedemptionDate` never change after creation.
- `sfLoanCount` changes by exactly `+1` (immediate `LoanSet` or `LoanAccept`) when a loan becomes active, or `-1` when an active loan becomes inactive (full repayment via `LoanPay`, or default via `LoanManage`); the pending `LoanSet` path, `LoanDelete`, and the deletion of a pending loan leave it unchanged.
- `sfLoanCount` counts active (outstanding) loans only; it is `> 0` whenever the vault has at least one active loan (directional check; a full O(N) count is not run per-transaction).
- Each loan is decremented at most once: a loan transitions active→inactive only once, because `LoanManage` cannot default a loan once `sfPaymentRemaining == 0` and `LoanPay` cannot pay a loan that is already repaid or defaulted, so the `LoanPay` and `LoanManage` decrement paths are mutually exclusive.
- No `VaultDeposit` succeeds unless `getVaultPhase` is `Subscription` or `Invalid` (the latter being open-ended vaults, which are unaffected).
- No `VaultWithdraw` succeeds when `getVaultPhase == Investment` (closed-ended).
- No `LoanSet`/`LoanAccept` succeeds when `getVaultPhase == Redemption` (closed-ended).

## 4. Rationale

### 4.1. One stored boundary: loan-driven Subscription to Investment

This proposal stores a single date (`RedemptionDate`) and derives the Subscription to Investment boundary from the vault's active-loan count:

- **Subscription** - `sfLoanCount == 0` and before `RedemptionDate`. The vault is still raising capital; no loan has been deployed. Liquidity Providers may deposit and may withdraw to cancel.
- **Investment** - `sfLoanCount > 0` and before `RedemptionDate`. Capital has been deployed into at least one active loan; deposits and withdrawals close.
- **Redemption** - at/after `RedemptionDate`, unconditionally.

The advantage is that the Subscription-to-Investment transition reflects the *actual* deployment of capital rather than a calendar estimate: a vault that raises and deploys early is locked exactly when its first loan goes live, and one that never deploys never leaves Subscription.

**Phase re-entry after early repayment is intended.** Because the boundary is derived from `sfLoanCount`, if *every* active loan becomes inactive - fully repaid or defaulted - before `RedemptionDate`, `sfLoanCount` returns to `0` and the vault re-enters Subscription, re-enabling deposits until the next loan is originated (no `LoanDelete` is required for re-entry). This is exactly how the vault is meant to behave: Subscription means no capital is currently at work, so a vault whose loans have all resolved correctly presents as subscribing again. The phases track live capital deployment, so a vault may re-enter Subscription whenever its active loans have all resolved before `RedemptionDate`.

### 4.2. Maintained `LoanCount` vs. directory enumeration

"Does this vault have an active loan?" cannot be answered cheaply from the vault's balances alone, and walking every broker's owner directory is O(N). A maintained `sfLoanCount` on the vault - incremented when a loan becomes active (immediate `LoanSet` or `LoanAccept`) and decremented when an active loan becomes inactive (fully repaid via `LoanPay`, or defaulted via `LoanManage`) - answers the question in O(1), drives the phase boundary (4.1), and provides a cheap defensive gate for `VaultDelete`. A loan is counted only while it has outstanding obligations: a fully-repaid or defaulted loan is *not* counted even though its `Loan` object persists until `LoanDelete`. This mirrors the existing `sfLEVersion` precedent (a small maintained field on the vault gated by a new amendment).

**Why the two-step flow defers the increment.** In the two-step flow a `LoanSet` only creates a *pending* proposal (`lsfLoanPending`) that reserves principal into `sfAssetsReserved` but disburses nothing; the loan is not economically live until the borrower accepts. Counting it at proposal time would flip the vault into Investment (halting deposits) on the strength of a proposal the borrower might never accept. Counting it at `LoanAccept` - when the principal is actually disbursed - keeps `sfLoanCount` aligned with capital that is genuinely deployed.

## 5. Backwards Compatibility

- The feature is inert unless the `ClosedEndedVault` amendment is enabled. Ledger entries and transactions are unchanged for nodes that have not activated it.
- **Open-ended vaults** retain their existing behaviour: `getVaultPhase` returns `Invalid`, so no deposit, withdrawal, or loan restriction is added. Such a vault may carry `sfLoanCount`, but it has no behavioural effect.
- All new fields are `SoeOptional`, so existing serialised vaults deserialise unchanged.

## 6. Test Plan

- **VaultCreate:** valid closed-ended creation; missing `RedemptionDate` returns `temMALFORMED`; `RedemptionDate` in the past returns `temMALFORMED`; open-ended (or absent kind) with `RedemptionDate` present returns `temMALFORMED`; unknown `VaultKind` returns `temMALFORMED`.
- **Phase derivation:** `getVaultPhase` returns `Subscription` while `sfLoanCount == 0`, `Investment` once `sfLoanCount > 0`, and `Redemption` at/after `RedemptionDate`; open-ended returns `Invalid`. Include the case where fully repaying or defaulting the last active loan before `RedemptionDate` returns the vault to `Subscription`.
- **VaultDeposit:** allowed in Subscription; rejected in Investment and Redemption; open-ended unaffected.
- **VaultWithdraw:** allowed in Subscription and Redemption; rejected in Investment; open-ended unaffected; `AssetsAvailable` cap still applies.
- **LoanSet (immediate):** rejected in Redemption; rejected when maturity + grace exceeds `RedemptionDate`; `sfLoanCount` increments and the vault is updated; a first loan moves the vault from Subscription to Investment.
- **LoanSet (two-step/pending):** `sfLoanCount` is *unchanged*; the vault stays in Subscription while the loan is pending.
- **LoanAccept:** `sfLoanCount` increments and the vault is updated; rejected in Redemption; accepting the first loan moves the vault from Subscription to Investment.
- **LoanPay (payoff):** `sfLoanCount` decrements and the vault is updated when a payment drives `sfPaymentRemaining` to `0`, whether via an early full payoff (`tfLoanFullPayment`) or a final regular installment; a partial payment that leaves `sfPaymentRemaining > 0` does *not* change `sfLoanCount`. Fully repaying the last active loan before `RedemptionDate` moves the vault from Investment back to Subscription.
- **LoanManage (default):** defaulting an active loan decrements `sfLoanCount` and updates the vault; impair/unimpair do *not* change `sfLoanCount`.
- **LoanDelete (active or pending):** `sfLoanCount` is *unchanged* (an active loan was already decremented when it was repaid or defaulted).
- **VaultDelete:** rejected when `sfLoanCount > 0`; also blocked (via the broker owner-count / directory guards, not `sfLoanCount`) while a pending loan reserves assets or a fully-repaid/defaulted `Loan` object remains undeleted.
- **VaultSet:** attempts to mutate `VaultKind`/`RedemptionDate` return `temMALFORMED`.
- **Invariant checks:** end-to-end lifecycle (subscribe, invest, redeem) across both loan flows with multiple LPs and loans, asserting each invariant in 3.7.

## 7. Reference Implementation
TBD

## 8. Security Considerations

- **Locked capital by design.** During Investment, LPs cannot withdraw. This is the intended contract, but it means LP capital is illiquid for the term. The `RedemptionDate` is set at creation and visible to depositors before they subscribe, so the lock-up ceiling cannot be silently extended.
- **Immutability enforcement.** `VaultKind` and `RedemptionDate` MUST be rejected by `VaultSet`; otherwise an owner could extend the lock-up or alter the term after capital is committed.
- **Phase re-entry after early repayment.** Because the Subscription and Investment phases are driven by `sfLoanCount`, fully repaying or defaulting every active loan before `RedemptionDate` re-enables deposits (4.1), with no `LoanDelete` required. This cannot extend the term (`RedemptionDate` is fixed) and cannot force-realise capital, but integrators SHOULD be aware that a closed-ended vault may accept fresh deposits after a full early repayment or after its outstanding loans default.
- **Maturity bound on loans.** Constraining loan maturity + grace to `<= RedemptionDate` prevents the owner from originating loans that would keep capital illiquid past the advertised redemption date. Without this check a malicious or careless owner could strand LP funds.
- **`LoanCount` integrity.** `sfLoanCount` must be maintained symmetrically: each increment (immediate `LoanSet` / `LoanAccept`) MUST pair with exactly one decrement, applied when the loan becomes inactive (full repayment via `LoanPay`, or default via `LoanManage`). The `LoanPay` decrement MUST fire on the `sfPaymentRemaining > 0 → 0` transition (so it is counted once, whether the payoff is an early full payment or a final regular installment); `LoanDelete` and the pending paths MUST NOT touch the count. A mismaintained count could block a legitimate `VaultDelete` (safe failure) or, if under-counted, mis-signal the phase; the independent `AssetsTotal == 0`, `AssetsReserved`, and empty-directory checks remain as guards so an incorrect count cannot by itself orphan loan objects.
- **Time source.** The Investment-to-Redemption transition relies on the ledger close time, which is consensus-derived and not manipulable by a single participant.

# Appendix

## Appendix A: FAQ.

### A.1: What happens if a loan defaults and is never repaid?

Defaulting an active loan (via `LoanManage`) makes it inactive, so `sfLoanCount` is decremented at default - a defaulted loan does **not** keep the vault in Investment. The loan's `Loan` object nonetheless persists until `LoanDelete` and continues to hold a broker owner-count, so `LoanBrokerDelete` (and therefore `VaultDelete`) remains blocked until the defaulted loan is deleted. Redemption still begins on `RedemptionDate`; LPs redeem against whatever capital was recovered (`AssetsAvailable`), with any unrecovered principal reflected in NAV as usual.

### A.2: Can the owner change the redemption date if the raise is undersubscribed?

No. `RedemptionDate` is immutable. To run a different schedule the owner creates a new closed-ended vault. This preserves the guarantee LPs relied on when subscribing.

### A.3: In the two-step flow, does proposing a loan lock the vault?

No. A two-step `LoanSet` only creates a *pending* proposal; it does not increment `sfLoanCount`, so the vault remains in Subscription and deposits stay open. The vault enters Investment only when the borrower accepts (`LoanAccept`), which is when the principal is actually disbursed and `sfLoanCount` is incremented.
