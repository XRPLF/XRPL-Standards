<pre>
xls: TBD
proposal-from: https://github.com/XRPLF/XRPL-Standards/discussions/590
title: Closed-Ended Single Asset Vault
description: Adds a fixed-term, phase-based vault kind to the Single Asset Vault so lenders can lock capital for a defined investment period.
author: Jingchen Wu (@a1q123456), Vito Tumas (@Tapanito), Gregory Tsipenyuk (@gtsipenyuk)
status: Draft
category: Amendment
created: 2026-07-21
updated: 2026-09-14
</pre>

# Closed-Ended Single Asset Vault

## 1. Abstract

This proposal introduces a new **closed-ended** vault kind that moves through three deterministic phases - **Subscription**, **Investment**, and **Redemption** - and restricts deposits and withdrawals according to the current phase. It adds three fields to the `Vault` ledger entry (`VaultKind`, `SubscriptionDate`, `RedemptionDate`) plus phase enforcement in the vault and lending transactors. Both phase boundaries are _date-driven_ and immutable: a vault leaves Subscription for Investment at `SubscriptionDate` (after which new deposits are rejected and capital is locked), and leaves Investment for Redemption at `RedemptionDate`. Loans originated against a closed-ended vault must be scheduled to end a short buffer before `RedemptionDate`, so no payment is scheduled to fall due once Redemption has opened. Open-ended vaults are behaviourally unaffected.

## 2. Introduction

A **closed-ended vault** is a fixed-term fund. Unlike an open-ended vault, where depositors can come and go at any time, a closed-ended vault has a defined lifecycle: it collects capital for a limited period, puts that capital to work for a fixed term, and then winds down and returns the proceeds to depositors. Once the fund is under way, no new money can join and existing money cannot leave until the term ends. This gives the operator a stable, known amount of capital to deploy and gives depositors a clear, up-front understanding of when their funds are committed and when they will be returned.

A closed-ended vault moves through three stages in order, and never goes backwards:

- **Subscription** — the fund-raising window. Depositors put capital in, and may change their mind and withdraw while the window is open. The size of the fund is still settling during this stage.
- **Investment** — the lock-up. The subscription window has closed, the amount of capital is now fixed, and it is deployed into loans. Deposits and withdrawals are both suspended so the capital stays in place for the whole term.
- **Redemption** — the wind-down. The loan terms have ended, no new lending takes place, and depositors withdraw their share of whatever capital has been returned. Loans that were repaid late, or not at all, do not hold the phase open.

The move from one stage to the next happens automatically at pre-set dates that are chosen when the vault is created and cannot be changed afterwards. Because the schedule is fixed and public, everyone involved knows in advance when the fund-raising window closes, how long their capital is committed, and when they can expect to be repaid.

This proposal extends the [Single Asset Vault](../XLS-0065-single-asset-vault/README.md) (XLS-65) with a new `ClosedEnded` vault kind that enforces this lifecycle on-chain. Existing open-ended vaults are unaffected and continue to behave exactly as before.

### 2.1. Permission Matrix

The full permission matrix across all transactors and phases is:

| Transaction   | Open-ended          | Subscription | Investment | Redemption |
| ------------- | ------------------- | ------------ | ---------- | ---------- |
| VaultDeposit  | allowed             | allowed      | rejected   | rejected   |
| VaultWithdraw | allowed             | allowed      | rejected   | allowed    |
| VaultClawback | allowed             | allowed      | allowed    | allowed    |
| LoanSet       | allowed             | rejected     | allowed\*  | rejected   |
| LoanAccept    | allowed             | rejected     | allowed    | rejected   |
| LoanPay       | allowed             | allowed      | allowed    | allowed    |
| LoanManage    | allowed             | allowed      | allowed    | allowed    |
| LoanDelete    | allowed             | allowed      | allowed    | allowed    |
| LoanBrokerSet | create rejected\*\* | allowed      | allowed    | allowed    |

\* `LoanSet` (and `LoanAccept`) are permitted only during the `Investment` phase. A closed-ended `LoanSet` is additionally constrained so the loan's final scheduled payment falls at least `LOAN_REDEMPTION_BUFFER` seconds before `RedemptionDate` (see 7).

\*\* `LoanBrokerSet` depends on what it does, not on the phase. Creating a `LoanBroker` (no `LoanBrokerID`) is rejected on an open-ended vault, and allowed on a closed-ended vault in any phase. Updating one (with a `LoanBrokerID`) is never restricted, even on an open-ended vault. See 9.2.1 and 13.

`VaultClawback`, `LoanPay`, `LoanManage`, and `LoanDelete` are allowed in all phases and need no changes. `VaultSet`, `VaultDelete`, `LoanBrokerDelete`, and the three `LoanBrokerCover` transactions ignore the phase too, so they are left out of the matrix. `VaultDelete` still requires an empty vault, as in XLS-65; that rule has nothing to do with the phase.

### 2.2. Protocol Constants

This proposal defines three protocol constants. The investment period bounds are enforced at vault creation (see 4.2.1) and the redemption buffer at loan origination (see 7.2.1); the reasoning behind the values is in 12.2 and 12.3.

| Constant                 | Value       | Meaning                                                                                                             |
| ------------------------ | ----------- | ------------------------------------------------------------------------------------------------------------------- |
| `MIN_INVESTMENT_PERIOD`  | `180`       | Minimum length, in seconds, of the Investment phase.                                                                |
| `MAX_INVESTMENT_PERIOD`  | `946708560` | Maximum length, in seconds, of the Investment phase (30 Gregorian years of 365.2425 days).                          |
| `LOAN_REDEMPTION_BUFFER` | `60`        | Minimum gap, in seconds, between a loan's final scheduled payment and the `RedemptionDate` of the vault funding it. |

12.2 and 12.3 also refer to `MIN_PAYMENT_INTERVAL`: the existing XLS-66 minimum of `60` seconds for `LoanSet.PaymentInterval`. This proposal does not change it.

### 2.3. Amendments

- `SingleAssetVault` (`featureSingleAssetVault`), from [XLS-65](../XLS-0065-single-asset-vault/README.md): added the `Vault` ledger entry and the vault transactions this proposal extends.
- `LendingProtocol` (`featureLendingProtocol`), from [XLS-66](../XLS-0066-lending-protocol/README.md): added the `LoanBroker` and `Loan` ledger entries and the lending transactions this proposal gates by phase.
- `LendingProtocolV1_1` (`featureLendingProtocolV1_1`): an existing amendment that also carries other lending and vault changes. This proposal adds no amendment of its own; everything in it is gated by `LendingProtocolV1_1`. Without it, a `VaultCreate` carrying `VaultKind`, `SubscriptionDate`, or `RedemptionDate` returns `temDISABLED`, and no transactor checks the phase.

## 3. Ledger Entry: `Vault` (modified)

This proposal modifies the existing XLS-65 `Vault` ledger entry rather than introducing a new one. Its object identifier, ownership, reserve accounting, deletion rules, and RPC name are unchanged; only the fields listed below are added.

### 3.1. Fields

| Field Name         | Constant |  Required   | JSON Type | Internal Type | Default Value | Description                                                                              |
| ------------------ | :------: | :---------: | :-------: | :-----------: | :-----------: | ---------------------------------------------------------------------------------------- |
| `VaultKind`        |   Yes    |     No      | `number`  |    `UINT8`    |      `0`      | The vault kind. Absent/`0` means open-ended. Immutable after creation.                   |
| `SubscriptionDate` |   Yes    | Conditional | `number`  |   `UINT32`    |     `N/A`     | End of Subscription / start of Investment phase. REQUIRED if `VaultKind == ClosedEnded`. |
| `RedemptionDate`   |   Yes    | Conditional | `number`  |   `UINT32`    |     `N/A`     | Start of Redemption phase. REQUIRED if `VaultKind == ClosedEnded`.                       |

`VaultKind` defaults to `0` and is not stored when it holds that default, so an open-ended vault has no `VaultKind` field at all: an absent field and an explicit `OpenEnded` mean the same thing. `SubscriptionDate` and `RedemptionDate` are stored only on closed-ended vaults.

#### 3.1.1. VaultKind

`VaultKind` is a `UINT8` enum. The following values are valid; any other value is treated as invalid.

| Name          | Value | Description                                                                                              |
| ------------- | :---: | -------------------------------------------------------------------------------------------------------- |
| `OpenEnded`   |  `0`  | Default. An open-ended vault with no phases (`NoPhase`); existing XLS-65 behaviour. Applies when absent. |
| `ClosedEnded` |  `1`  | A closed-ended vault that moves through the Subscription, Investment, and Redemption phases.             |

### 3.2. Phase Derivation

A vault's phase is derived at run time and never stored. Let `now` be the parent ledger close time (seconds since the Ripple epoch). An open-ended vault has no phases and its phase is `NoPhase`. A closed-ended vault's phase is determined by comparing `now` against its two immutable dates:

| Condition                                 |     Phase      |
| ----------------------------------------- | :------------: |
| `VaultKind == OpenEnded`                  |   `NoPhase`    |
| `now <= SubscriptionDate`                 | `Subscription` |
| `SubscriptionDate < now < RedemptionDate` |  `Investment`  |
| `now >= RedemptionDate`                   |  `Redemption`  |

The vault kind is read from `sfVaultKind`: an absent field means `OpenEnded`, and a known value means that kind. `VaultCreate` rejects unknown values (see 4.2.1), so none can reach the ledger under this proposal. Everywhere else, any value other than `ClosedEnded` is treated as `OpenEnded`, and so as `NoPhase`. This rule exists so that a vault kind added by a future amendment falls back to open-ended behaviour instead of failing.

### 3.3. Invariants

- A closed-ended vault always has both `SubscriptionDate` and `RedemptionDate`.
- For a closed-ended vault, `SubscriptionDate + MIN_INVESTMENT_PERIOD <= RedemptionDate < SubscriptionDate + MAX_INVESTMENT_PERIOD` always holds (equivalently `MIN_INVESTMENT_PERIOD <= RedemptionDate - SubscriptionDate < MAX_INVESTMENT_PERIOD`), which implies `SubscriptionDate < RedemptionDate`. The bound is checked at creation (see 4.2.1) and kept by the immutability rule below.
- `VaultKind`, `SubscriptionDate`, and `RedemptionDate` are immutable: once set at creation they are never added, removed, or changed by any transaction.

### 3.4. Example JSON

```json
{
  "LedgerEntryType": "Vault",
  "Account": "rwCNM7SeUHTajEBQDiNqxDG8p1Mreizw85",
  "Asset": {
    "currency": "USD",
    "issuer": "rXJSJiZMxaLuH3kQBUV5DLipnYtrE6iVb"
  },
  "AssetsAvailable": "0",
  "AssetsMaximum": "1000000",
  "AssetsTotal": "0",
  "Data": "5661756C74206D65746164617461",
  "Flags": 0,
  "LossUnrealized": "0",
  "Owner": "rNGHoQwNG753zyfDrib4qDvvswbrtmV8Es",
  "OwnerNode": "0",
  "Scale": 6,
  "Sequence": 200370,
  "ShareMPTID": "0000000169F415C9F1AB6796AB9224CE635818AFD74F8175",
  "WithdrawalPolicy": 1,
  "VaultKind": 1,
  "SubscriptionDate": 711232800,
  "RedemptionDate": 721600800
}
```

## 4. Transaction: `VaultCreate` (modified)

### 4.1. Fields

| Field Name         |  Required?  | JSON Type | Internal Type | Default Value | Description                                                                                                                 |
| ------------------ | :---------: | :-------: | :-----------: | :-----------: | :-------------------------------------------------------------------------------------------------------------------------- |
| `VaultKind`        |     No      | `number`  |    `UINT8`    |       0       | **New.** The vault kind. `0` = `OpenEnded` (default); `1` = `ClosedEnded`. Immutable after creation.                        |
| `SubscriptionDate` | Conditional | `number`  |   `UINT32`    |     `N/A`     | **New.** End of Subscription / start of Investment phase. REQUIRED if `VaultKind == ClosedEnded`. Immutable after creation. |
| `RedemptionDate`   | Conditional | `number`  |   `UINT32`    |     `N/A`     | **New.** Start of Redemption phase. REQUIRED if `VaultKind == ClosedEnded`. Immutable after creation.                       |

### 4.2. Failure Conditions

#### 4.2.1. Data Verification

1. If `sfVaultKind` holds an unrecognised enum value, return `temMALFORMED`.
2. If `sfVaultKind` is `OpenEnded` or absent but `sfSubscriptionDate` or `sfRedemptionDate` is present, return `temMALFORMED`.
3. If `sfVaultKind` is `ClosedEnded` but `sfSubscriptionDate` or `sfRedemptionDate` is absent, return `temMALFORMED`.
4. If `sfVaultKind` is `ClosedEnded` and `SubscriptionDate + MIN_INVESTMENT_PERIOD` is greater than `RedemptionDate` or `RedemptionDate` is greater than or equal to `SubscriptionDate + MAX_INVESTMENT_PERIOD`, return `temMALFORMED`. Both sums MUST be computed without 32-bit overflow, so a `SubscriptionDate` too close to `UINT32_MAX` for any valid `RedemptionDate` to exist is rejected rather than wrapping around.

#### 4.2.2. Protocol-Level Failures

1. If `sfVaultKind` is `ClosedEnded` and `SubscriptionDate` is not strictly after the parent ledger close time, return `tecEXPIRED`.
2. If `sfVaultKind` is `ClosedEnded` and `RedemptionDate` is not strictly after the parent ledger close time, return `tecEXPIRED`.

### 4.3. State Changes

On Success (tesSUCCESS):

- If `sfVaultKind` is absent or `OpenEnded`: the new `Vault` object is the same as in XLS-65. None of the three fields are stored (see 3.1).
- If `sfVaultKind == ClosedEnded`: set `sfVaultKind`, `sfSubscriptionDate`, and `sfRedemptionDate` on the new `Vault` object.

### 4.4. Invariants

- Every `Vault` created with `VaultKind == ClosedEnded` has both dates present and satisfies `MIN_INVESTMENT_PERIOD <= RedemptionDate - SubscriptionDate < MAX_INVESTMENT_PERIOD`, which implies `SubscriptionDate < RedemptionDate`.

### 4.5. Example JSON

```json
{
  "TransactionType": "VaultCreate",
  "Account": "rNGHoQwNG753zyfDrib4qDvvswbrtmV8Es",
  "Asset": {
    "currency": "USD",
    "issuer": "rXJSJiZMxaLuH3kQBUV5DLipnYtrE6iVb"
  },
  "AssetsMaximum": "1000000",
  "Data": "5661756C74206D65746164617461",
  "Fee": "5000000",
  "Flags": 0,
  "MPTokenMetadata": "7B2274223A225473745368617265222C226E223A2254657374205661756C74205368617265222C2264223A22412074657374207661756C742073686172652E222C2269223A226578616D706C652E6F72672F73686172652D69636F6E2E706E67222C226163223A22727761222C226173223A22657175697479222C22696E223A224D53205465737420497373756572222C227573223A5B7B2275223A226578616D706C657969656C642E636F2F7473747368617265222C2263223A2277656273697465222C2274223A2250726F647563742050616765227D2C7B2275223A226578616D706C657969656C642E636F2F646F6373222C2263223A22646F6373222C2274223A225969656C6420546F6B656E20446F6373227D5D2C226169223A7B22766F6C6174696C697479223A226C6F77227D7D",
  "Scale": 6,
  "Sequence": 200370,
  "WithdrawalPolicy": 1,
  "VaultKind": 1,
  "SubscriptionDate": 711232800,
  "RedemptionDate": 721600800
}
```

## 5. Transaction: `VaultDeposit` (modified)

### 5.1. Fields

No changes.

### 5.2. Failure Conditions

#### 5.2.1. Protocol-Level Failures

1. If the vault is closed-ended and `now > SubscriptionDate` (`now` is the parent ledger close time), return `tecEXPIRED`. Equivalently, the vault's phase is `Investment` or `Redemption`.

### 5.3. State Changes

No changes.

### 5.4. Invariants

- No `VaultDeposit` succeeds unless the vault's phase is `Subscription` or `NoPhase` (the latter being open-ended vaults, which are unaffected).

### 5.5. Example JSON

No changes.

## 6. Transaction: `VaultWithdraw` (modified)

### 6.1. Fields

No changes.

### 6.2. Failure Conditions

#### 6.2.1. Protocol-Level Failures

1. If the vault is closed-ended and `SubscriptionDate < now < RedemptionDate` (`now` is the parent ledger close time), return `tecTOO_SOON`.

### 6.3. State Changes

No changes.

### 6.4. Invariants

- No `VaultWithdraw` succeeds when the vault's phase is `Investment` (closed-ended).

### 6.5. Example JSON

No changes.

## 7. Transaction: `LoanSet` (modified)

### 7.1. Fields

No changes.

### 7.2. Failure Conditions

#### 7.2.1. Protocol-Level Failures

1. If the vault is closed-ended and `now <= SubscriptionDate` (`now` is the parent ledger close time), return `tecTOO_SOON`.
2. If the vault is closed-ended and `now >= RedemptionDate`, return `tecEXPIRED`.
3. If the vault is closed-ended and, using arithmetic wide enough to represent the complete expression without overflow, `StartDate + (PaymentInterval × PaymentTotal) + LOAN_REDEMPTION_BUFFER` is greater than `RedemptionDate`, where `StartDate` is `now` (XLS-66 sets a new loan's `StartDate` to the ledger close time), return `tecNO_PERMISSION`. Equivalently, the loan's final scheduled payment MUST fall at least `LOAN_REDEMPTION_BUFFER` seconds before `RedemptionDate`.

### 7.3. State Changes

No changes.

### 7.4. Invariants

- No closed-ended `LoanSet` succeeds unless the vault's phase is `Investment`.
- No closed-ended `LoanSet` succeeds unless the loan's final scheduled payment is at least `LOAN_REDEMPTION_BUFFER` seconds before `RedemptionDate`. Because `StartDate` and `PaymentInterval` are immutable once the `Loan` exists and `PaymentRemaining` only decreases, the bound holds for the lifetime of the loan.

### 7.5. Example JSON

No changes.

## 8. Transaction: `LoanAccept` (modified)

### 8.1. Fields

No changes.

### 8.2. Failure Conditions

#### 8.2.1. Protocol-Level Failures

1. If the vault is closed-ended and `now <= SubscriptionDate` (`now` is the parent ledger close time), return `tecTOO_SOON`.
2. If the vault is closed-ended and `now >= RedemptionDate`, return `tecEXPIRED`.

### 8.3. State Changes

No changes.

### 8.4. Invariants

- No closed-ended `LoanAccept` succeeds unless the vault's phase is `Investment`.

### 8.5. Example JSON

No changes.

## 9. Transaction: `LoanBrokerSet` (modified)

### 9.1. Fields

No changes.

### 9.2. Failure Conditions

#### 9.2.1. Protocol-Level Failures

1. If `LoanBrokerID` is not specified (i.e. a new `LoanBroker` is being created) and the vault's `VaultKind` is not `ClosedEnded`, return `tecNO_PERMISSION`.

### 9.3. State Changes

No changes.

### 9.4. Invariants

- No `LoanBroker` is created against a vault whose `VaultKind` is not `ClosedEnded`.

### 9.5. Example JSON

No changes.

## 10. RPC: `vault_info` (modified)

The `vault_info` method retrieves a `Vault` ledger entry. This proposal does not change its request fields; it only adds the three new `Vault` fields to the response when they are present.

### 10.1. Request Fields

No changes.

### 10.2. Response Fields

The following fields are added to the `vault` object in the response. Only the newly introduced fields are listed here; all existing XLS-65 `vault_info` response fields are unchanged. These fields are present only for closed-ended vaults; open-ended vaults omit all three, which callers MUST interpret as `VaultKind = OpenEnded`.

| Field Name               | Required? | JSON Type | Description                                                                            |
| ------------------------ | --------- | --------- | -------------------------------------------------------------------------------------- |
| `vault.VaultKind`        | `no`      | `number`  | The vault kind. Absent means open-ended (`0`); `1` = `ClosedEnded`.                    |
| `vault.SubscriptionDate` | `no`      | `number`  | End of Subscription / start of Investment phase. Present only for closed-ended vaults. |
| `vault.RedemptionDate`   | `no`      | `number`  | Start of Redemption phase. Present only for closed-ended vaults.                       |

### 10.3. Failure Conditions

No changes.

### 10.4. Example Request

No changes.

### 10.5. Example Response

The `vault` object of a closed-ended vault, showing only the new fields (all existing fields are as in XLS-65):

```json
{
  "result": {
    "vault": {
      "LedgerEntryType": "Vault",
      "VaultKind": 1,
      "SubscriptionDate": 800000000,
      "RedemptionDate": 900000000
    }
  }
}
```

An open-ended vault omits `VaultKind`, `SubscriptionDate`, and `RedemptionDate`; its response is identical to the existing XLS-65 `vault_info` response.

## 11. RPC: `ledger_entry` (modified)

The `ledger_entry` method returns a `Vault` object when queried with a `vault` object ID. This proposal does not change its request fields; it only adds the three new `Vault` fields to the returned object when they are present.

### 11.1. Request Fields

No changes.

### 11.2. Response Fields

The same three fields added to `vault_info` (see 10.2) are added to the `Vault` object returned by `ledger_entry`. Only the newly introduced fields are listed here; all existing fields are unchanged. These fields are present only for closed-ended vaults; open-ended vaults omit all three, which callers MUST interpret as `VaultKind = OpenEnded`.

| Field Name         | Required? | JSON Type | Description                                                                            |
| ------------------ | --------- | --------- | -------------------------------------------------------------------------------------- |
| `VaultKind`        | `no`      | `number`  | The vault kind. Absent means open-ended (`0`); `1` = `ClosedEnded`.                    |
| `SubscriptionDate` | `no`      | `number`  | End of Subscription / start of Investment phase. Present only for closed-ended vaults. |
| `RedemptionDate`   | `no`      | `number`  | Start of Redemption phase. Present only for closed-ended vaults.                       |

### 11.3. Failure Conditions

No changes.

### 11.4. Example Request

No changes.

### 11.5. Example Response

The `node` object of a closed-ended vault, showing only the new fields (all existing fields are as in XLS-65):

```json
{
  "result": {
    "node": {
      "LedgerEntryType": "Vault",
      "VaultKind": 1,
      "SubscriptionDate": 800000000,
      "RedemptionDate": 900000000
    }
  }
}
```

## 12. Rationale

### 12.1. Two stored boundaries: date-driven phases

This proposal stores two immutable dates on the vault and derives all three phases from them and the parent ledger close time:

- **Subscription** - on/before `SubscriptionDate`. The vault is still raising capital; Liquidity Providers may deposit and may withdraw to cancel.
- **Investment** - after `SubscriptionDate` and before `RedemptionDate`. The subscription window has closed; deposits and withdrawals are locked while capital is deployed into loans.
- **Redemption** - on/after `RedemptionDate`, unconditionally.

Because both boundaries are calendar dates fixed at creation, the vault's lifecycle is fully deterministic and monotonic: it advances from Subscription to Investment to Redemption exactly once and never re-enters an earlier phase. Depositors know the exact subscription window and lock-up term before they commit capital, and the vault needs no knowledge of the loans funded against it to determine its phase.

### 12.2. Why loans must mature a buffer before `RedemptionDate`

`LoanSet` requires a closed-ended loan's final scheduled payment to fall at least `LOAN_REDEMPTION_BUFFER` seconds before `RedemptionDate` (see 7.2.1), rather than merely before it:

```
StartDate + (PaymentInterval × PaymentTotal) + LOAN_REDEMPTION_BUFFER <= RedemptionDate
```

Without the buffer, a loan's final payment could be scheduled on, or one second before, `RedemptionDate`. Redemption would then open while the last payment was still in flight, and because the vault uses cash-basis accounting (see A.5) the first depositors to withdraw would redeem against a pool that had not yet received it. The buffer reserves a window between the last scheduled payment and the start of Redemption in which that payment can be made and recorded.

The buffer is a floor on the schedule, not a guarantee of settlement: a borrower who pays late can still miss it. Its purpose is to stop a vault owner from _scheduling_ a loan that is structurally certain to be unsettled at the phase boundary.

A consequence worth noting for integrators: because the bound is measured against a fixed `RedemptionDate`, the maximum term available to a _new_ loan shrinks as the vault approaches that date, and no new loan can be originated at all once fewer than `MIN_PAYMENT_INTERVAL + LOAN_REDEMPTION_BUFFER` seconds remain.

### 12.3. Why `MIN_INVESTMENT_PERIOD` is 180 seconds

The floor is chosen so that even a minimum-length Investment phase can accommodate one loan: a `StartDate` strictly after `SubscriptionDate` (`+1` second), a single payment at the XLS-66 minimum `PaymentInterval` of `60` seconds, and `LOAN_REDEMPTION_BUFFER` — that is, `MIN_INVESTMENT_PERIOD >= 1 + MIN_PAYMENT_INTERVAL + LOAN_REDEMPTION_BUFFER`. Were the floor any lower, a vault could be created whose Investment phase admits no valid loan at all. The three constants are otherwise independent; only their sum is constrained, which is why 180 exceeds the 121 seconds strictly required.

## 13. Backwards Compatibility

- The feature is inert unless `LendingProtocolV1_1` is enabled (see 2.3). Ledger entries and transactions are unchanged for nodes that have not activated it.
- **Open-ended vaults** retain their existing behaviour: their phase is `NoPhase`, so no deposit, withdrawal, or loan restriction is added.
- All new fields are optional, so existing serialised vaults deserialise unchanged.
- **`VaultCreate` remains unrestricted.** Open-ended vaults are still legal objects and may still be created after the amendment; the closed-ended requirement binds at broker creation (9.2.1), not at vault creation.
- **Existing loan brokers are grandfathered.** The 9.2.1 restriction is evaluated only on the branch that creates a new `LoanBroker`. A `LoanBroker` already attached to an open-ended vault is unaffected: it may still be updated by a `LoanBrokerSet` carrying an explicit `LoanBrokerID`, and loans may still be originated against it, since an open-ended vault is `NoPhase` and the 7.2.1 gates therefore never apply to it.

## 14. Test Plan

### 14.1. VaultCreate

- A valid closed-ended creation succeeds.
- Creation with a missing `SubscriptionDate` or `RedemptionDate` returns `temMALFORMED`.
- Creation with a `SubscriptionDate` in the past (not strictly after the parent ledger close time) returns `tecEXPIRED`.
- Creation with a `RedemptionDate` in the past (not strictly after the parent ledger close time) returns `tecEXPIRED`.
- Creation with a gap smaller than `MIN_INVESTMENT_PERIOD` (including `SubscriptionDate >= RedemptionDate`) returns `temMALFORMED`.
- Creation with a gap of `MAX_INVESTMENT_PERIOD` or larger returns `temMALFORMED`.
- Creation with a gap exactly equal to `MIN_INVESTMENT_PERIOD` is accepted.
- Creation with a gap one second smaller than `MAX_INVESTMENT_PERIOD` is accepted.
- Creation of an open-ended vault (or one with an absent kind) that carries a `SubscriptionDate` or `RedemptionDate` returns `temMALFORMED`.
- Creation with an unknown `VaultKind` returns `temMALFORMED`.
- Boundary: a `SubscriptionDate` of `UINT32_MAX - MIN_INVESTMENT_PERIOD` with a `RedemptionDate` of `UINT32_MAX` is accepted, and both dates are stored unchanged.
- Boundary: a `SubscriptionDate` of `UINT32_MAX` returns `temMALFORMED` for every `RedemptionDate`, since no `RedemptionDate` can be `MIN_INVESTMENT_PERIOD` seconds later.

### 14.2. Phase derivation

- The vault's phase is `Subscription` on/before `SubscriptionDate`, `Investment` after `SubscriptionDate` and before `RedemptionDate`, and `Redemption` on/after `RedemptionDate`.
- Open-ended vaults are always `NoPhase`.

### 14.3. VaultDeposit

- A deposit is allowed during Subscription.
- A deposit is rejected during Investment and Redemption.
- Deposits into open-ended vaults are unaffected.

### 14.4. VaultWithdraw

- A withdrawal is allowed during Subscription and Redemption.
- A withdrawal is rejected during Investment.
- Withdrawals from open-ended vaults are unaffected.
- The `AssetsAvailable` cap still applies.

### 14.5. VaultClawback

- `VaultClawback` succeeds in each of Subscription, Investment, and Redemption; the Investment-phase lock does not apply to it.
- Clawback from an open-ended vault is unaffected.

### 14.6. LoanSet

- `LoanSet` is rejected during Subscription and Redemption.
- `LoanSet` is permitted during Investment when the loan's final payment is at least `LOAN_REDEMPTION_BUFFER` seconds before `RedemptionDate`.
- `LoanSet` is rejected when the loan's final payment is fewer than `LOAN_REDEMPTION_BUFFER` seconds before `RedemptionDate`, including a final payment exactly on `RedemptionDate` or after it.
- Boundary: a final payment exactly `LOAN_REDEMPTION_BUFFER` seconds before `RedemptionDate` is accepted, and one second later is rejected.
- A vault created with the minimum gap (`RedemptionDate - SubscriptionDate == MIN_INVESTMENT_PERIOD`) can still originate one loan at the minimum `PaymentInterval` while `now <= SubscriptionDate + MIN_INVESTMENT_PERIOD - MIN_PAYMENT_INTERVAL - LOAN_REDEMPTION_BUFFER` (the first 60 seconds of Investment), and rejects that same schedule once `now` passes that point.
- Several loans may be open against the same closed-ended vault at once; each is checked against `RedemptionDate` independently at origination.

### 14.7. LoanPay

- A payment made after `RedemptionDate`, on a loan whose schedule ended before it, still succeeds and adds the proceeds to the vault. The phase does not block repayment (see A.5).

### 14.8. LoanAccept

- `LoanAccept` is rejected during Subscription and Redemption.
- `LoanAccept` is permitted during Investment.

### 14.9. Pending loans

- A two-step loan whose start date has passed can no longer be accepted (`LoanAccept` is rejected), both while the vault is still in `Investment` and once it reaches `Redemption`.
- `LoanDelete` on such an expired pending loan succeeds in the `Investment` phase — freeing its reserved principal back into `AssetsAvailable` even during the lock-up — and likewise succeeds in `Redemption`.
- `VaultDelete` is blocked while a pending loan still exists and succeeds once that loan is deleted.

### 14.10. LoanBrokerSet

- Creating a `LoanBroker` against an open-ended vault returns `tecNO_PERMISSION`.
- Creating a `LoanBroker` against a closed-ended vault succeeds in every phase.
- Updating an existing `LoanBroker` (explicit `LoanBrokerID`) against an open-ended vault still succeeds.

### 14.11. RPC surface

- `vault_info` and `ledger_entry` return `VaultKind`, `SubscriptionDate`, and `RedemptionDate` for a closed-ended vault, and omit all three for an open-ended vault.

### 14.12. Invariant checks

- An invariant check asserts each of 4.4, 5.4, 6.4, 7.4, and 8.4, so no transaction can leave the ledger in a state that breaks them.
- 3.3 is covered in two parts: the date-presence and period bound are asserted on `VaultCreate` (the same check as 4.4), and the immutability of `VaultKind`, `SubscriptionDate`, and `RedemptionDate` is asserted on every transaction that modifies a `Vault`. A test changes each of the three fields on an existing closed-ended vault and expects the immutability check to fire.
- 9.4 has no invariant check. It is enforced by the failure condition in 9.2.1 and covered by the tests in 14.10.

### 14.13. End-to-end tests

- An end-to-end lifecycle (subscribe, invest, redeem) with multiple depositors and loans exercises every phase transition and verifies the expected deposit, withdrawal, and lending behaviour in each phase.

## 15. Reference Implementation

- [XRPLF/rippled#7921](https://github.com/XRPLF/rippled/pull/7921): the closed-ended vault kind, its fields, and phase enforcement.
- [XRPLF/rippled#8076](https://github.com/XRPLF/rippled/pull/8076): reject `LoanBroker` creation on open-ended vaults (9.2.1).
- [XRPLF/rippled#8151](https://github.com/XRPLF/rippled/pull/8151): the `LOAN_REDEMPTION_BUFFER` check on `LoanSet` (7.2.1).

## 16. Security Considerations

- **Locked capital by design.** During Investment, depositors cannot withdraw. This is the intended contract, but it means depositors' capital is illiquid for the term. The `RedemptionDate` is set at creation and visible to depositors before they subscribe, so the lock-up ceiling cannot be silently extended.
- **Immutability enforcement.** `VaultKind`, `SubscriptionDate`, and `RedemptionDate` are immutable after creation and cannot be modified by any transaction; otherwise an owner could shorten the subscription window, extend the lock-up, or alter the term after capital is committed.
- **Fixed subscription window.** The Subscription-to-Investment boundary is the immutable `SubscriptionDate`, so the deposit window and the start of the lock-up are fixed at creation and cannot be shortened or extended after depositors commit capital.
- **Investment period bounds.** `MIN_INVESTMENT_PERIOD <= RedemptionDate - SubscriptionDate < MAX_INVESTMENT_PERIOD` only keeps the dates well-formed; it says nothing about whether the term is sensible. A `180`-second floor does not guarantee a meaningful lock-up. Depositors should read `SubscriptionDate` and `RedemptionDate`, which are public before they subscribe, rather than assume a term from the bounds.
- **Maturity bound on loans.** The check in 7.2.1 limits a loan's _schedule_: an owner cannot create a loan whose final payment falls within `LOAN_REDEMPTION_BUFFER` seconds of `RedemptionDate`. It does not guarantee the borrower pays on time (see 12.2 and A.5).
- **Reserved/abandoned pending-loan capital.** An un-accepted two-step loan holds its principal outside redeemable `AssetsAvailable`, and keeps the broker's owner count non-zero, blocking `LoanBrokerDelete`. Once `now >= RedemptionDate` it can no longer be accepted (see A.6), so the principal is released only when the broker deletes the loan.
- **Asset-total changes during Investment.** The Investment-phase lock restricts _depositor_ deposits and withdrawals, not every change to the vault's asset total. A stranded two-step loan — one that can no longer be accepted because its start date has passed while the vault is still in Investment — MUST remain deletable, and deleting it MUST return its reserved principal to `AssetsAvailable`, raising the redeemable total even during the lock-up. Phase enforcement must therefore be scoped to block depositor-initiated withdrawals without preventing this legitimate return of reserved capital.
- **Time source.** Both phase transitions rely on the ledger close time, which is consensus-derived and not manipulable by a single participant.

# Appendix

## Appendix A: FAQ.

### A.1: What happens if a loan defaults and is never repaid?

A defaulted or unrepaid loan has no effect on the vault's phase, which is derived solely from `SubscriptionDate` and `RedemptionDate`. The loan's `Loan` object nonetheless persists until `LoanDelete` and continues to hold a broker owner-count, so `LoanBrokerDelete` remains blocked until the defaulted loan is deleted. `VaultDelete` stays blocked too: XLS-65 requires the vault to be empty and its pseudo-account's directory to be clear, and an unrepaid loan keeps `AssetsTotal` non-zero while the `LoanBroker` stays in that directory. Redemption still begins on `RedemptionDate`; Depositors redeem against whatever capital was recovered (`AssetsAvailable`), with any unrecovered principal reflected in NAV as usual.

### A.2: Can the owner change the redemption date if the raise is undersubscribed?

No. `RedemptionDate` is immutable. To run a different schedule the owner creates a new closed-ended vault. This preserves the guarantee depositors relied on when subscribing.

### A.3: Does originating or accepting a loan lock the vault?

No. A vault's phase is driven only by `SubscriptionDate` and `RedemptionDate`, not by whether any loans exist. Deposits remain open throughout Subscription regardless of loan activity, and the vault enters Investment at `SubscriptionDate` whether or not any loan has been originated.

### A.4: Why not a maintained `LoanCount`?

An earlier design derived the Subscription-to-Investment boundary from the vault's _active-loan count_: a maintained `sfLoanCount` field, incremented when a loan became active and decremented when it was fully repaid or defaulted, with the vault in Subscription while `sfLoanCount == 0` and in Investment once `sfLoanCount > 0`. We considered this approach but discarded it: it would make the vault **aware of individual loans**, requiring the lending transactors (`LoanSet`, `LoanAccept`, `LoanPay`, `LoanManage`) to maintain a counter on the vault and keep it symmetric across every activation and resolution path. That coupling is easy to get wrong - a single missed increment or double decrement mis-signals the phase - and blurs the separation between the vault and the lending layer.

A date-driven `SubscriptionDate` keeps the vault entirely unaware of loans: the phase is a pure function of two immutable dates and the ledger close time, needs no maintenance across loan transactions, and cannot drift out of sync. The trade-off is that the Investment lock-up begins on a fixed calendar date rather than on actual capital deployment, which we consider an acceptable and more predictable contract for depositors.

### A.5: What about late payments when they fall after `RedemptionDate`?

Redemption begins unconditionally at `RedemptionDate`, and depositors may withdraw from that point on. Because the vault uses cash-basis accounting, a withdrawing depositor only ever receives a share of the assets the vault has actually collected at that moment, which excludes any payment that has not yet arrived. A payment that lands after `RedemptionDate` is simply added to the vault's assets when it is received; it is not accrued in advance.

A practical consequence is that the timing of a withdrawal affects how much a depositor receives. Depositors who withdraw before a late final payment arrives are paid out of the assets on hand excluding that payment, while a depositor who chooses to withdraw after the final payment is collected redeems against a larger pool. The last depositor to withdraw therefore receives a proportionally larger amount than those who exited earlier, since the outstanding payment has by then been added to the vault.

### A.6: What happens to a pending two-step loan that is never accepted before Redemption?

Nothing changes on the ledger: the loan simply remains pending, exactly as if it had been created through the one-step flow and never accepted. The broker can still delete it, but it can no longer be accepted. `LoanAccept` is restricted to the Investment window, so once `now >= RedemptionDate` the loan cannot be activated; and because a loan's whole payment schedule must complete at least `LOAN_REDEMPTION_BUFFER` seconds before `RedemptionDate`, a pending loan whose start date has already passed can never be accepted either. In short, an unaccepted two-step loan cannot lock capital past `RedemptionDate` - it is left as a deletable, inert object.

### A.7: Can an existing open-ended vault be converted to closed-ended?

No, and the choice is therefore irreversible in both directions. `VaultKind`, `SubscriptionDate`, and `RedemptionDate` are immutable (see 3.3), and `VaultSet` does not accept any of the three: they are not in its transaction format, so a transaction carrying them is rejected at deserialisation, before preflight, rather than by a transactor failure condition.

This matters because of 9.2.1: a `LoanBroker` may only be created against a closed-ended vault. An operator who creates an open-ended vault, issues its share MPT, and takes deposits cannot later attach a broker to it — there is no conversion and no upgrade path, so the vault, its share issuance, and every depositor position would have to be unwound and rebuilt against a new closed-ended vault. The vault kind must therefore be chosen before shares are issued.
