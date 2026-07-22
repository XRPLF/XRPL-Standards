<pre>
xls: 103
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

This proposal introduces a new **closed-ended** vault kind that moves through three deterministic phases - **Subscription**, **Investment**, and **Redemption** - and restricts deposits and withdrawals according to the current phase. It adds three fields to the `Vault` ledger entry (`VaultKind`, `SubscriptionDate`, `RedemptionDate`) plus phase enforcement in the vault and lending transactors. Both phase boundaries are _date-driven_ and immutable: a vault leaves Subscription for Investment at `SubscriptionDate` (after which new deposits are rejected and capital is locked), and leaves Investment for Redemption at `RedemptionDate`. Open-ended vaults are behaviourally unaffected.

## 2. Introduction

A **closed-ended vault** is a fixed-term fund: capital is raised during a defined subscription window, locked for an investment period while it is deployed into loans, and then returned to depositors at a fixed redemption date. This proposal extends the [Single Asset Vault](../XLS-0065-single-asset-vault/README.md) (XLS-65) with a new `ClosedEnded` vault kind that enforces this lifecycle on-chain.

### 2.1 New Fields

To support fixed-term semantics, three new fields are added to the `Vault` ledger entry:

- **`VaultKind`** (`UINT8`, default `OpenEnded`) — distinguishes closed-ended vaults from the existing open-ended kind. Immutable after creation.
- **`SubscriptionDate`** (`UINT32`, required for closed-ended vaults) — a Ripple-epoch timestamp marking the end of the Subscription phase and the start of the Investment phase. Immutable after creation.
- **`RedemptionDate`** (`UINT32`, required for closed-ended vaults) — a Ripple-epoch timestamp marking the start of the Redemption phase. Immutable after creation.

The current phase is never stored on the ledger; it is derived at run time by comparing the parent ledger close time against `SubscriptionDate` and `RedemptionDate`.

### 2.2 Phase Derivation

A vault's phase is derived at run time and never stored. Let `now` be the parent ledger close time (seconds since the Ripple epoch). An open-ended vault has no phases and its phase is `NoPhase`. A closed-ended vault's phase is determined by comparing `now` against its two immutable dates:

| Condition                                  |     Phase      |
| ------------------------------------------ | :------------: |
| `VaultKind == OpenEnded`                   |   `NoPhase`    |
| `now < SubscriptionDate`                   | `Subscription` |
| `SubscriptionDate <= now < RedemptionDate` |  `Investment`  |
| `now >= RedemptionDate`                    |  `Redemption`  |

The vault kind is resolved from `sfVaultKind`: an absent field means `OpenEnded`; a present and recognised value decodes to that kind; any unrecognised value is treated as invalid.

### 2.3 Modified Transactors

Phase enforcement touches six existing transactors:

- **`VaultCreate`** — accepts the new optional `VaultKind` field; when `ClosedEnded`, also requires `SubscriptionDate` and `RedemptionDate` and validates their ordering and minimum gap.
- **`VaultSet`** — must reject any attempt to modify `VaultKind`, `SubscriptionDate`, or `RedemptionDate`, as these fields are immutable once set.
- **`VaultDeposit`** — new deposits are permitted only during `Subscription`. They are rejected in `Investment` (capital is locked) and `Redemption` (the raise is over).
- **`VaultWithdraw`** — withdrawals are permitted during `Subscription` (LPs may cancel) and `Redemption` (LPs exit at NAV), but blocked during `Investment` to enforce the lock-up.
- **`LoanSet`** — loan origination is restricted to the `Investment` phase; it is rejected during `Subscription` (capital not yet locked) and `Redemption` (depositors are exiting). Additionally, the loan's final scheduled payment must fall at least `REDEMPTION_BUFFER` before `RedemptionDate`, ensuring all repayments are collected before the redemption window opens.
- **`LoanAccept`** — activating a two-step loan is likewise restricted to the `Investment` phase for the same reasons as `LoanSet`.

The full permission matrix across all transactors and phases is:

| Transaction   | Open-ended | Subscription | Investment | Redemption |
| ------------- | ---------- | ------------ | ---------- | ---------- |
| VaultDeposit  | allowed    | allowed      | rejected   | rejected   |
| VaultWithdraw | allowed    | allowed      | rejected   | allowed    |
| VaultDonation | allowed    | allowed      | allowed    | allowed    |
| LoanSet       | allowed    | rejected     | allowed\*  | rejected   |
| LoanAccept    | allowed    | rejected     | allowed    | rejected   |
| LoanPay       | allowed    | allowed      | allowed    | allowed    |
| LoanManage    | allowed    | allowed      | allowed    | allowed    |
| LoanDelete    | allowed    | allowed      | allowed    | allowed    |
| VaultClawback | allowed    | allowed      | allowed    | allowed    |

\* `LoanSet` (and `LoanAccept`) are permitted only during the `Investment` phase. A closed-ended `LoanSet` is additionally constrained so the loan fully matures before `RedemptionDate` (see 3.5).

`VaultDonation`, `VaultClawback`, `LoanPay`, `LoanManage`, `LoanDelete`, and `VaultDelete` are permitted in all phases and require no changes. `VaultDelete` remains subject to the existing XLS-65 precondition that the vault be empty, which is independent of phase.

### 2.4 Redemption Buffer

This proposal defines one protocol constant, `REDEMPTION_BUFFER` (value `TBD`): the minimum buffer applied before `RedemptionDate`. It is used in two places. First, a closed-ended vault MUST satisfy `RedemptionDate - SubscriptionDate >= REDEMPTION_BUFFER`, so the Investment phase is long enough to deploy capital. Second, every loan's final payment MUST fall at least `REDEMPTION_BUFFER` before `RedemptionDate`, leaving a settlement buffer before depositors begin exiting (see 3.5).

## 3. Specification

Only the fields, failure conditions, and state changes newly introduced by this proposal are documented below. All existing XLS-65 and lending-protocol behaviour is inherited unchanged.

### 3.1. Ledger Entry: `Vault` (modified)

The following fields are added to the existing `ltVAULT` ledger entry. All are `SoeOptional`/`SoeDefault` so pre-existing serialized vaults remain valid; open-ended vaults retain their existing behaviour.

| Field Name         | Modifiable? |  Required   | JSON Type | Internal Type | Default Value | Description                                                                              |
| ------------------ | :---------: | :---------: | :-------: | :-----------: | :-----------: | --------------------------------------------------------------------------------------- |
| `VaultKind`        |     No      |     No      | `number`  |    `UINT8`    |      `0`      | The vault kind. Absent/`0` means open-ended. Immutable after creation.                  |
| `SubscriptionDate` |     No      | Conditional | `number`  |   `UINT32`    |     `N/A`     | End of Subscription / start of Investment phase. REQUIRED if `VaultKind == ClosedEnded`. |
| `RedemptionDate`   |     No      | Conditional | `number`  |   `UINT32`    |     `N/A`     | Start of Redemption phase. REQUIRED if `VaultKind == ClosedEnded`.                       |

### 3.2. Transaction: `VaultCreate` (modified)

#### 3.2.1. Fields

| Field Name         |     Required?      |     JSON Type      | Internal Type |      Default Value       | Description                                                                              |
| ------------------ | :----------------: | :----------------: | :-----------: | :----------------------: | :--------------------------------------------------------------------------------------- |
| `VaultKind`        |   No               |      `number`      |    `UINT8`    |            0             | **New.** The vault kind. `0` = `OpenEnded` (default); `1` = `ClosedEnded`. Immutable after creation.                                                  |
| `SubscriptionDate` |   No               |      `number`      |   `UINT32`    |          `N/A`           | **New.** End of Subscription / start of Investment phase. REQUIRED if `VaultKind == ClosedEnded`. Immutable after creation.                            |
| `RedemptionDate`   |   No               |      `number`      |   `UINT32`    |          `N/A`           | **New.** Start of Redemption phase. REQUIRED if `VaultKind == ClosedEnded`. Immutable after creation.                                                  |

#### 3.2.2. Failure Conditions

- If `sfVaultKind` holds an unrecognised enum value, return `temMALFORMED`.
- If `sfVaultKind` is `OpenEnded` or absent but `sfSubscriptionDate` or `sfRedemptionDate` is present, return `temMALFORMED`.
- If `sfVaultKind` is `ClosedEnded` but `sfSubscriptionDate` or `sfRedemptionDate` is absent, return `temMALFORMED`.
- If `sfVaultKind` is `ClosedEnded` and `SubscriptionDate` is not strictly after the ledger close time, return `temMALFORMED`.
- If `sfVaultKind` is `ClosedEnded` and `RedemptionDate - SubscriptionDate` is less than `REDEMPTION_BUFFER`, return `temMALFORMED`.

#### 3.2.3. State Changes

- If `sfVaultKind` is absent or `OpenEnded`: no change to existing state changes.
- If `sfVaultKind == ClosedEnded`: set `sfVaultKind`, `sfSubscriptionDate`, and `sfRedemptionDate` on the new `Vault` object.

#### 3.2.4. Invariants

- For a closed-ended vault, `RedemptionDate - SubscriptionDate >= REDEMPTION_BUFFER` always holds, which implies `SubscriptionDate < RedemptionDate`.
- A closed-ended vault's phase advances monotonically from Subscription to Investment to Redemption and never regresses, since both boundaries are immutable dates and the ledger close time only increases.

### 3.3. Transaction: `VaultDeposit` (modified)

#### 3.3.1. Fields

No changes.

#### 3.3.2. Failure Conditions

- If the vault phase (see 2.2) is `Investment` or `Redemption`, return `tecNO_PERMISSION`.

#### 3.3.3. State Changes

No changes.

#### 3.3.4. Invariants

- No `VaultDeposit` succeeds unless the vault's phase is `Subscription` or `NoPhase` (the latter being open-ended vaults, which are unaffected).

### 3.4. Transaction: `VaultWithdraw` (modified)

#### 3.4.1. Fields

No changes.

#### 3.4.2. Failure Conditions

- If the vault phase (see 2.2) is `Investment`, return `tecNO_PERMISSION`.

#### 3.4.3. State Changes

No changes.

#### 3.4.4. Invariants

- No `VaultWithdraw` succeeds when the vault's phase is `Investment` (closed-ended).

### 3.5. Transaction: `LoanSet` (modified)

#### 3.5.1. Fields

No changes.

#### 3.5.2. Failure Conditions

- If the vault phase (see 2.2) is not `Investment`, return `tecNO_PERMISSION`.
- If `startDate + (paymentInterval × paymentTotal) + REDEMPTION_BUFFER` is not strictly before `RedemptionDate`, return `tecNO_PERMISSION`.

#### 3.5.3. State Changes

No changes.

#### 3.5.4. Invariants

- No closed-ended `LoanSet` succeeds unless the vault's phase is `Investment`.
- No closed-ended `LoanSet` succeeds unless the loan's final scheduled payment plus `REDEMPTION_BUFFER` is strictly before `RedemptionDate`.

### 3.6. Transaction: `LoanAccept` (modified)

#### 3.6.1. Fields

No changes.

#### 3.6.2. Failure Conditions

- If the vault phase (see 2.2) is not `Investment`, return `tecNO_PERMISSION`.

#### 3.6.3. State Changes

No changes.

#### 3.6.4. Invariants

- No closed-ended `LoanAccept` succeeds unless the vault's phase is `Investment`.

### 3.7. Transaction: `VaultSet` (modified)

#### 3.7.1. Fields

No changes.

#### 3.7.2. Failure Conditions

- If the transaction attempts to set or alter `sfVaultKind`, `sfSubscriptionDate`, or `sfRedemptionDate`, return `temMALFORMED`.

#### 3.7.3. State Changes

No changes.

#### 3.7.4. Invariants

- `VaultKind`, `SubscriptionDate`, and `RedemptionDate` never change after creation.

## 4. Rationale

### 4.1. Two stored boundaries: date-driven phases

This proposal stores two immutable dates on the vault and derives all three phases from them and the parent ledger close time:

- **Subscription** - before `SubscriptionDate`. The vault is still raising capital; Liquidity Providers may deposit and may withdraw to cancel.
- **Investment** - on/after `SubscriptionDate` and before `RedemptionDate`. The subscription window has closed; deposits and withdrawals are locked while capital is deployed into loans.
- **Redemption** - at/after `RedemptionDate`, unconditionally.

Because both boundaries are calendar dates fixed at creation, the vault's lifecycle is fully deterministic and monotonic: it advances from Subscription to Investment to Redemption exactly once and never re-enters an earlier phase. Depositors know the exact subscription window and lock-up term before they commit capital, and the vault needs no knowledge of the loans funded against it to determine its phase.

### 4.2. Why not a maintained `LoanCount`?

An earlier design derived the Subscription-to-Investment boundary from the vault's _active-loan count_: a maintained `sfLoanCount` field, incremented when a loan became active and decremented when it was fully repaid or defaulted, with the vault in Subscription while `sfLoanCount == 0` and in Investment once `sfLoanCount > 0`. We considered this approach but discarded it: it would make the vault **aware of individual loans**, requiring the lending transactors (`LoanSet`, `LoanAccept`, `LoanPay`, `LoanManage`) to maintain a counter on the vault and keep it symmetric across every activation and resolution path. That coupling is easy to get wrong - a single missed increment or double decrement mis-signals the phase - and blurs the separation between the vault and the lending layer.

A date-driven `SubscriptionDate` keeps the vault entirely unaware of loans: the phase is a pure function of two immutable dates and the ledger close time, needs no maintenance across loan transactions, and cannot drift out of sync. The trade-off is that the Investment lock-up begins on a fixed calendar date rather than on actual capital deployment, which we consider an acceptable and more predictable contract for depositors.

## 5. Backwards Compatibility

- The feature is inert unless the amendment is enabled. Ledger entries and transactions are unchanged for nodes that have not activated it.
- **Open-ended vaults** retain their existing behaviour: their phase is `NoPhase`, so no deposit, withdrawal, or loan restriction is added.
- All new fields are `SoeOptional`, so existing serialised vaults deserialise unchanged.

## 6. Test Plan

- **VaultCreate:** valid closed-ended creation; missing `SubscriptionDate` or `RedemptionDate` returns `temMALFORMED`; `SubscriptionDate` in the past returns `temMALFORMED`; a gap smaller than `REDEMPTION_BUFFER` (including `SubscriptionDate >= RedemptionDate`) returns `temMALFORMED`; a gap exactly equal to `REDEMPTION_BUFFER` is accepted; open-ended (or absent kind) with `SubscriptionDate` or `RedemptionDate` present returns `temMALFORMED`; unknown `VaultKind` returns `temMALFORMED`.
- **Phase derivation:** the vault's phase is `Subscription` before `SubscriptionDate`, `Investment` on/after `SubscriptionDate` and before `RedemptionDate`, and `Redemption` at/after `RedemptionDate`; open-ended vaults are `NoPhase`.
- **VaultDeposit:** allowed in Subscription; rejected in Investment and Redemption; open-ended unaffected.
- **VaultWithdraw:** allowed in Subscription and Redemption; rejected in Investment; open-ended unaffected; `AssetsAvailable` cap still applies.
- **LoanSet:** rejected in Subscription and Redemption; permitted in Investment when the loan's final payment plus `REDEMPTION_BUFFER` is strictly before `RedemptionDate`; rejected when it is not.
- **LoanAccept:** rejected in Subscription and Redemption; permitted in Investment.
- **VaultSet:** attempts to mutate `VaultKind`, `SubscriptionDate`, or `RedemptionDate` return `temMALFORMED`.
- **Invariant checks:** end-to-end lifecycle (subscribe, invest, redeem) with multiple LPs and loans, asserting the per-transaction invariants (3.2.4, 3.3.4, 3.4.4, 3.5.4, 3.6.4, 3.7.4).

## 7. Reference Implementation

TBD

## 8. Security Considerations

- **Locked capital by design.** During Investment, LPs cannot withdraw. This is the intended contract, but it means LP capital is illiquid for the term. The `RedemptionDate` is set at creation and visible to depositors before they subscribe, so the lock-up ceiling cannot be silently extended.
- **Immutability enforcement.** `VaultKind`, `SubscriptionDate`, and `RedemptionDate` MUST be rejected by `VaultSet`; otherwise an owner could shorten the subscription window, extend the lock-up, or alter the term after capital is committed.
- **Fixed subscription window.** The Subscription-to-Investment boundary is the immutable `SubscriptionDate`, so the deposit window and the start of the lock-up are fixed at creation and cannot be shortened or extended after LPs commit capital.
- **Redemption buffer.** Enforcing `RedemptionDate - SubscriptionDate >= REDEMPTION_BUFFER` prevents a degenerate vault whose Investment phase is too short to deploy capital, which could otherwise be used to advertise a fixed-term product that effectively skips the lock-up.
- **Maturity bound on loans.** Requiring the loan's final payment plus `REDEMPTION_BUFFER` to fall strictly before `RedemptionDate` prevents the owner from originating loans that would keep capital illiquid past the advertised redemption date, and leaves a settlement buffer before depositors exit. Without this check a malicious or careless owner could strand LP funds.
- **Time source.** Both phase transitions rely on the ledger close time, which is consensus-derived and not manipulable by a single participant.

# Appendix

## Appendix A: FAQ.

### A.1: What happens if a loan defaults and is never repaid?

A defaulted or unrepaid loan has no effect on the vault's phase, which is derived solely from `SubscriptionDate` and `RedemptionDate`. The loan's `Loan` object nonetheless persists until `LoanDelete` and continues to hold a broker owner-count, so `LoanBrokerDelete` (and therefore `VaultDelete`) remains blocked until the defaulted loan is deleted. Redemption still begins on `RedemptionDate`; LPs redeem against whatever capital was recovered (`AssetsAvailable`), with any unrecovered principal reflected in NAV as usual.

### A.2: Can the owner change the redemption date if the raise is undersubscribed?

No. `RedemptionDate` is immutable. To run a different schedule the owner creates a new closed-ended vault. This preserves the guarantee LPs relied on when subscribing.

### A.3: Does originating or accepting a loan lock the vault?

No. A vault's phase is driven only by `SubscriptionDate` and `RedemptionDate`, not by whether any loans exist. Deposits remain open throughout Subscription regardless of loan activity, and the vault enters Investment at `SubscriptionDate` whether or not any loan has been originated.
