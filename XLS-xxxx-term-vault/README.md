<pre>
xls: TBD
title: Closed-Ended Single Asset Vault
description: Adds a fixed-term, phase-based vault kind to the Single Asset Vault so lenders can lock capital for a defined investment period.
author: TBD
status: Draft
category: Amendment
created: 2026-07-21
updated: 2026-07-21
</pre>

# Closed-Ended Single Asset Vault

## 1. Abstract

The Single Asset Vault (XLS-65) is *open-ended*: depositors may deposit or withdraw at any time. When a vault's cash is deployed into loans (XLS-66), its liquid balance (`AssetsAvailable`) drops below its net asset value (`AssetsTotal`), and any withdrawal larger than the liquid balance fails with `tecINSUFFICIENT_FUNDS`. This makes an open-ended vault unsuitable for fixed-term lending, where liquidity is intentionally locked until loans mature.

This proposal introduces a new **closed-ended** vault kind that moves through three deterministic phases - **Subscription**, **Investment**, and **Redemption** - and restricts deposits and withdrawals according to the current phase. It adds three fields to the `Vault` ledger entry (`VaultKind`, `SubscriptionDate`, `RedemptionDate`) plus phase enforcement in the vault and lending transactors. Both phase boundaries are *date-driven* and immutable: a vault leaves Subscription for Investment at `SubscriptionDate` (after which new deposits are rejected and capital is locked), and leaves Investment for Redemption at `RedemptionDate`. Open-ended vaults are behaviourally unaffected.

## 2. Motivation

TBD

## 3. Specification

This feature is gated behind `LendingProtocolV1_1`.

### 3.1. Enumerations

`VaultKind` (`uint8_t`):

| Name               | Value | Description                 |
| ------------------ | :---: | --------------------------- |
| `OpenEnded`        | `0`   | Default; existing behaviour |
| `ClosedEnded`      | `1`   | Fixed-term, phase-based     |

`VaultPhase` (`uint8_t`):

| Name           | Value | Description                                |
| -------------- | :---: | ------------------------------------------ |
| `Invalid`      | `0`   | Returned for open-ended vaults (no phases) |
| `Subscription` | `1`   | Raising capital                            |
| `Investment`   | `2`   | Capital locked                             |
| `Redemption`   | `3`   | Depositors exit at NAV                     |

`VaultKind` is persisted on the ledger (in `sfVaultKind`). `VaultPhase` is **never stored**; it is derived at run time from the vault's kind, its `SubscriptionDate`, its `RedemptionDate`, and the parent ledger close time (see 3.4).

### 3.2. Vault Phases

The phases are derived from the vault's two immutable dates (`SubscriptionDate`, `RedemptionDate`; see 3.3) and the parent ledger close time - a closed-ended vault advances through them in one direction only:

- **Subscription** (before `SubscriptionDate`): deposits and withdrawals are open. Capital can enter and exit freely while the vault is still raising funds.
- **Investment** (on/after `SubscriptionDate`, before `RedemptionDate`): both deposits and withdrawals are rejected. The vault is locked while capital is deployed into loans.
- **Redemption** (on/after `RedemptionDate`): withdrawals open; new deposits rejected. Depositors exit at NAV.

See 4.1 for how the phases behave over the vault's lifetime.

### 3.3. Ledger Entry: `Vault` (modified)

The following fields are added to the existing `ltVAULT` ledger entry. All are `SoeOptional`/`SoeDefault` so pre-existing serialized vaults remain valid; open-ended vaults retain their existing behaviour.

| Field Name         | Constant | Required    | JSON Type | Internal Type | Default Value | Description                                                                                    |
| ------------------ | :------: | :---------: | :-------: | :-----------: | :-----------: | --------------------------------------------------------------------------------------------- |
| `VaultKind`        |   Yes    |     No      | `number`  |    `UINT8`    |      `0`      | `VaultKind`. Absent/`0` means open-ended. Immutable after creation.                            |
| `SubscriptionDate` |   Yes    | Conditional | `number`  |   `UINT32`    |     `N/A`     | End of Subscription / start of Investment phase. REQUIRED iff `VaultKind == ClosedEnded`.      |
| `RedemptionDate`   |   Yes    | Conditional | `number`  |   `UINT32`    |     `N/A`     | Start of Redemption phase. REQUIRED iff `VaultKind == ClosedEnded`.                            |

### 3.4. Phase derivation

A vault's phase is derived at run time and never stored. Let `now` be the parent ledger close time (seconds since the Ripple epoch). An open-ended vault has no phases and its phase is `Invalid`. A closed-ended vault's phase is determined by comparing `now` against its two immutable dates:

| Condition                                    | Phase          |
| -------------------------------------------- | :------------: |
| `now < SubscriptionDate`                     | `Subscription` |
| `SubscriptionDate <= now < RedemptionDate`   | `Investment`   |
| `now >= RedemptionDate`                       | `Redemption`   |

The vault kind is resolved from `sfVaultKind`: an absent field means `OpenEnded`; a present and recognised value decodes to that kind; any unrecognised value is treated as invalid.

### 3.5. Phase / Kind rules matrix

| Transaction   | Open-ended            | Subscription | Investment | Redemption |
| ------------- | --------------------- | ------------ | ---------- | ---------- |
| VaultDeposit  | allowed               | allowed      | rejected   | rejected   |
| VaultWithdraw | allowed               | allowed      | rejected   | allowed    |
| VaultDonation | allowed               | allowed      | allowed    | allowed    |
| LoanSet       | allowed               | allowed\*    | allowed\*  | rejected   |
| LoanAccept    | allowed               | allowed      | allowed    | rejected   |
| LoanPay       | allowed               | allowed      | allowed    | allowed    |
| LoanManage    | allowed               | allowed      | allowed    | allowed    |
| LoanDelete    | allowed               | allowed      | allowed    | allowed    |
| VaultClawback | allowed               | allowed      | allowed    | allowed    |

The Subscription and Investment columns are delimited by the immutable `SubscriptionDate`: a closed-ended vault is in **Subscription** before `SubscriptionDate` and in **Investment** on/after `SubscriptionDate` (and before `RedemptionDate`). Reaching `SubscriptionDate` is therefore what advances the vault from Subscription to Investment (see 4.1). `Redemption` begins unconditionally at `RedemptionDate`.

\* `LoanSet` (and `LoanAccept`) are permitted only before `RedemptionDate`. A closed-ended `LoanSet` is additionally constrained so the loan fully matures before Redemption (see 3.6.4).

`VaultDonation` is allowed regardless of phase (Subscription, Investment, and Redemption alike): a donation only adds assets to the vault and never withdraws capital, so it cannot violate the lock-up guarantees the phases enforce.

### 3.6. Transaction changes

#### 3.6.1. `VaultCreate`

- Accepts a new OPTIONAL field `sfVaultKind`. If absent, the vault is `OpenEnded` and behaviour is unchanged.
- If `sfVaultKind == ClosedEnded`:
  - `sfSubscriptionDate` and `sfRedemptionDate` are REQUIRED.
  - `SubscriptionDate >` ledger close time, otherwise `temMALFORMED`.
  - `SubscriptionDate < RedemptionDate`, otherwise `temMALFORMED`.
  - The transactor sets `sfVaultKind`, `sfSubscriptionDate`, and `sfRedemptionDate`.
- If `sfVaultKind == OpenEnded` (or absent) but `sfSubscriptionDate` or `sfRedemptionDate` is present, return `temMALFORMED`.
- If `sfVaultKind` holds an unknown enum value, return `temMALFORMED`.

#### 3.6.2. `VaultDeposit`

A deposit is rejected with `tecNO_PERMISSION` when the vault's phase (see 3.4) is `Investment` or `Redemption`; it is permitted in `Subscription` and `Invalid`. Open-ended vaults have phase `Invalid`, so they are never rejected and remain unaffected; a closed-ended vault rejects deposits in `Investment` and `Redemption`.

#### 3.6.3. `VaultWithdraw`

A withdrawal is rejected with `tecNO_PERMISSION` when the vault's phase (see 3.4) is `Investment`; it is permitted in `Subscription`, `Redemption`, and `Invalid`. Open-ended vaults have phase `Invalid`, so withdrawals are always permitted and remain unaffected; a closed-ended vault is blocked only in `Investment`. The existing `AssetsAvailable` cap and share-pricing logic are unchanged.

#### 3.6.4. `LoanSet`

- For closed-ended vaults (both the immediate and two-step flows):
  - **Origination timing:** the vault MUST be before `RedemptionDate` (i.e. its phase is `Subscription` or `Investment`), else `tecNO_PERMISSION`. `LoanSet` is rejected on/after `RedemptionDate`; no new loans are allowed once Redemption begins.
  - **Maturity constraint:** the loan's maturity, `startDate + (paymentInterval × paymentTotal) + gracePeriod`, MUST be strictly before `RedemptionDate`, else `tecNO_PERMISSION`. A loan whose maturity falls on/after `RedemptionDate` is rejected, ensuring all repayments are received before depositors begin exiting.
- `LoanSet` does not read or write any loan-tracking field on the vault; the vault remains unaware of individual loans.

#### 3.6.5. `LoanAccept`

- Activates a pending loan created by the two-step `LoanSet`.
- For closed-ended vaults, the vault MUST be before `RedemptionDate`, else `tecNO_PERMISSION` (a loan cannot be activated during Redemption). This is in addition to the existing `StartDate`-based proposal-expiry check.

#### 3.6.6. `LoanPay`

- `LoanPay` is unaffected by this proposal. Loan repayment does not read or write any phase-related field on the vault: the Subscription-to-Investment boundary is `SubscriptionDate`, not a loan count, so a payoff neither advances nor reverses the vault's phase.

#### 3.6.7. `LoanManage`

- `LoanManage` is unaffected by this proposal. Defaulting, impairing, or unimpairing a loan does not read or write any phase-related field on the vault; the vault's phase is derived solely from its dates.

#### 3.6.8. `LoanDelete`

- `LoanDelete` is unaffected by this proposal; it does not read or write any phase-related field on the vault.

#### 3.6.9. `VaultSet`

- MUST reject any attempt to set/alter `sfVaultKind`, `sfSubscriptionDate`, or `sfRedemptionDate` with `temMALFORMED` (data verification) - these are immutable.

#### 3.6.10. `VaultDelete`

- `VaultDelete` is unchanged by this proposal. The existing `AssetsTotal == 0` and empty-pseudo-directory checks already prevent deleting a vault while any `Loan` object exists: a pending loan reserves principal (`sfAssetsReserved > 0`), and every undeleted `Loan` (pending, repaid, or defaulted) holds a broker owner-count that blocks `LoanBrokerDelete` (`sfOwnerCount != 0`), which in turn keeps the vault's pseudo-account directory non-empty and blocks `VaultDelete`. Because the vault is deliberately unaware of individual loans, no loan-count guard is added.

### 3.7. Invariants

- `VaultKind`, `SubscriptionDate`, and `RedemptionDate` never change after creation.
- For a closed-ended vault, `SubscriptionDate < RedemptionDate` always holds (enforced at creation).
- A closed-ended vault's phase advances monotonically from Subscription to Investment to Redemption and never regresses, since both boundaries are immutable dates and the ledger close time only increases.
- No `VaultDeposit` succeeds unless the vault's phase is `Subscription` or `Invalid` (the latter being open-ended vaults, which are unaffected).
- No `VaultWithdraw` succeeds when the vault's phase is `Investment` (closed-ended).
- No `LoanSet`/`LoanAccept` succeeds when the vault's phase is `Redemption` (closed-ended).
- No closed-ended `LoanSet` succeeds whose loan maturity falls on/after `RedemptionDate`.

## 4. Rationale

### 4.1. Two stored boundaries: date-driven phases

This proposal stores two immutable dates on the vault and derives all three phases from them and the parent ledger close time:

- **Subscription** - before `SubscriptionDate`. The vault is still raising capital; Liquidity Providers may deposit and may withdraw to cancel.
- **Investment** - on/after `SubscriptionDate` and before `RedemptionDate`. The subscription window has closed; deposits and withdrawals are locked while capital is deployed into loans.
- **Redemption** - at/after `RedemptionDate`, unconditionally.

Because both boundaries are calendar dates fixed at creation, the vault's lifecycle is fully deterministic and monotonic: it advances from Subscription to Investment to Redemption exactly once and never re-enters an earlier phase. Depositors know the exact subscription window and lock-up term before they commit capital, and the vault needs no knowledge of the loans funded against it to determine its phase.

### 4.2. Why not a maintained `LoanCount`?

An earlier design derived the Subscription-to-Investment boundary from the vault's *active-loan count*: a maintained `sfLoanCount` field, incremented when a loan became active and decremented when it was fully repaid or defaulted, with the vault in Subscription while `sfLoanCount == 0` and in Investment once `sfLoanCount > 0`. We considered this approach but discarded it: it would make the vault **aware of individual loans**, requiring the lending transactors (`LoanSet`, `LoanAccept`, `LoanPay`, `LoanManage`) to maintain a counter on the vault and keep it symmetric across every activation and resolution path. That coupling is easy to get wrong - a single missed increment or double decrement mis-signals the phase - and blurs the separation between the vault and the lending layer.

A date-driven `SubscriptionDate` keeps the vault entirely unaware of loans: the phase is a pure function of two immutable dates and the ledger close time, needs no maintenance across loan transactions, and cannot drift out of sync. The trade-off is that the Investment lock-up begins on a fixed calendar date rather than on actual capital deployment, which we consider an acceptable and more predictable contract for depositors.

## 5. Backwards Compatibility

- The feature is inert unless the `ClosedEndedVault` amendment is enabled. Ledger entries and transactions are unchanged for nodes that have not activated it.
- **Open-ended vaults** retain their existing behaviour: their phase is `Invalid`, so no deposit, withdrawal, or loan restriction is added.
- All new fields are `SoeOptional`, so existing serialised vaults deserialise unchanged.

## 6. Test Plan

- **VaultCreate:** valid closed-ended creation; missing `SubscriptionDate` or `RedemptionDate` returns `temMALFORMED`; `SubscriptionDate` in the past returns `temMALFORMED`; `SubscriptionDate >= RedemptionDate` returns `temMALFORMED`; open-ended (or absent kind) with `SubscriptionDate` or `RedemptionDate` present returns `temMALFORMED`; unknown `VaultKind` returns `temMALFORMED`.
- **Phase derivation:** the vault's phase is `Subscription` before `SubscriptionDate`, `Investment` on/after `SubscriptionDate` and before `RedemptionDate`, and `Redemption` at/after `RedemptionDate`; open-ended vaults are `Invalid`.
- **VaultDeposit:** allowed in Subscription; rejected in Investment and Redemption; open-ended unaffected.
- **VaultWithdraw:** allowed in Subscription and Redemption; rejected in Investment; open-ended unaffected; `AssetsAvailable` cap still applies.
- **LoanSet:** rejected on/after `RedemptionDate`; rejected when loan maturity falls on/after `RedemptionDate`; permitted in Subscription and Investment when maturity is strictly before `RedemptionDate`.
- **LoanAccept:** rejected on/after `RedemptionDate`; permitted before `RedemptionDate`.
- **VaultSet:** attempts to mutate `VaultKind`, `SubscriptionDate`, or `RedemptionDate` return `temMALFORMED`.
- **Invariant checks:** end-to-end lifecycle (subscribe, invest, redeem) with multiple LPs and loans, asserting each invariant in 3.7.

## 7. Reference Implementation
TBD

## 8. Security Considerations

- **Locked capital by design.** During Investment, LPs cannot withdraw. This is the intended contract, but it means LP capital is illiquid for the term. The `RedemptionDate` is set at creation and visible to depositors before they subscribe, so the lock-up ceiling cannot be silently extended.
- **Immutability enforcement.** `VaultKind`, `SubscriptionDate`, and `RedemptionDate` MUST be rejected by `VaultSet`; otherwise an owner could shorten the subscription window, extend the lock-up, or alter the term after capital is committed.
- **Fixed subscription window.** The Subscription-to-Investment boundary is the immutable `SubscriptionDate`, so the deposit window and the start of the lock-up are fixed at creation and cannot be shortened or extended after LPs commit capital.
- **Maturity bound on loans.** Constraining loan maturity to be strictly before `RedemptionDate` prevents the owner from originating loans that would keep capital illiquid past the advertised redemption date. Without this check a malicious or careless owner could strand LP funds.
- **Time source.** Both phase transitions rely on the ledger close time, which is consensus-derived and not manipulable by a single participant.

# Appendix

## Appendix A: FAQ.

### A.1: What happens if a loan defaults and is never repaid?

A defaulted or unrepaid loan has no effect on the vault's phase, which is derived solely from `SubscriptionDate` and `RedemptionDate`. The loan's `Loan` object nonetheless persists until `LoanDelete` and continues to hold a broker owner-count, so `LoanBrokerDelete` (and therefore `VaultDelete`) remains blocked until the defaulted loan is deleted. Redemption still begins on `RedemptionDate`; LPs redeem against whatever capital was recovered (`AssetsAvailable`), with any unrecovered principal reflected in NAV as usual.

### A.2: Can the owner change the redemption date if the raise is undersubscribed?

No. `RedemptionDate` is immutable. To run a different schedule the owner creates a new closed-ended vault. This preserves the guarantee LPs relied on when subscribing.

### A.3: Does originating or accepting a loan lock the vault?

No. A vault's phase is driven only by `SubscriptionDate` and `RedemptionDate`, not by whether any loans exist. Deposits remain open throughout Subscription regardless of loan activity, and the vault enters Investment at `SubscriptionDate` whether or not any loan has been originated.
