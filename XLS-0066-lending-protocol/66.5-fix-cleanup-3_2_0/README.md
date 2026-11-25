<pre>
  xls: 66.5
  title: Lending Protocol Cleanup 3.2.0
  description: Lending Protocol changes of the fixCleanup3_2_0 amendment to first-loss capital precision, minimum cover rounding, cover transfers and amortization rounding
  author: Vytautas Vito Tumas <vtumas@ripple.com>
  proposal-from: https://github.com/XRPLF/XRPL-Standards/discussions/190
  status: Final
  category: Amendment
  created: 2026-11-25
  updated: 2026-11-25
</pre>

# 66.5 Lending Protocol Cleanup 3.2.0

## 1. Abstract

Under the `fixCleanup3_2_0` amendment:

- First-loss capital deposits are rounded down to the precision of `LoanBroker.CoverAvailable`, and deposits, withdrawals and clawbacks that round to zero fail with `tecPRECISION_LOSS`.
- The minimum cover `LoanBroker.DebtTotal × LoanBroker.CoverRateMinimum` is rounded up to the precision of the Vault in every transaction that uses it.
- `LoanBrokerCoverWithdraw` does not check `lsfMPTCanTransfer`.
- `LoanBrokerDelete` fails if the broker _pseudo-account_ is frozen and holds cover.
- The amortization arithmetic avoids cancellation at near-zero rates, rounds each periodic payment's target principal up and target interest down, keeps the principal exact across an overpayment, and rounds the overpayment amount down to the Loan scale.

## 2. Motivation

Before the amendment, an amount finer than `LoanBroker.CoverAvailable` could be deposited or withdrawn without changing the stored cover, so the cover and the _pseudo-account_ balance drifted apart. Each transaction rounded the minimum cover at a different precision, so the same broker could pass the check in one transaction and fail it in another. An MPT issuer could clear `lsfMPTCanTransfer` and trap a broker's first-loss capital. The amortization arithmetic lost precision at near-zero rates, and on integer-scale Loans rounding to nearest could leave a payment with no principal.

## 3. Specification

No fields are added or removed.

### 3.1 Transaction: `LoanBrokerCoverDeposit`

#### 3.1.1 Failure Conditions

Parent §3.5.3.2 check 8: when the amendment is enabled, `Amount` rounded down to the precision of `LoanBroker.CoverAvailable` is zero or less. (`tecPRECISION_LOSS`) The funds check (parent check 9) uses the rounded amount. When the amendment is not enabled, the check does not apply.

#### 3.1.2 State Changes

When the amendment is enabled, the amount transferred and added to `LoanBroker.CoverAvailable` in parent §3.5.4 is `Amount` rounded down to the precision of `LoanBroker.CoverAvailable`. When the amendment is not enabled, it is `Amount`.

### 3.2 Transaction: `LoanBrokerCoverWithdraw`

#### 3.2.1 Failure Conditions

When the amendment is enabled:

- Parent check 5 does not check `lsfMPTCanTransfer`. Other transfer checks still apply.
- Parent check 13 rounds the minimum cover up to the precision of the Vault (§3.6).
- Parent check 15: `Amount` is zero, or rounds to zero at the precision of `LoanBroker.CoverAvailable`. (`tecPRECISION_LOSS`)

When the amendment is not enabled, an MPT without `lsfMPTCanTransfer` fails check 5 unless the destination is the issuer, check 13 rounds the minimum cover up to the precision of `LoanBroker.DebtTotal`, and check 15 does not apply.

### 3.3 Transaction: `LoanBrokerCoverClawback`

#### 3.3.1 Failure Conditions

When the amendment is enabled:

- Parent check 8 rounds the minimum cover up to the precision of the Vault (§3.6).
- Parent check 9: `ClawAmount` is zero, or rounds to zero at the precision of `LoanBroker.CoverAvailable`. (`tecPRECISION_LOSS`)

When the amendment is not enabled, check 8 rounds the minimum cover up without rounding it to the asset precision, and check 9 does not apply.

### 3.4 Transaction: `LoanBrokerDelete`

#### 3.4.1 Failure Conditions

Parent §3.4.3.2 check 6: when the amendment is enabled, `LoanBroker.CoverAvailable > 0` and the broker _pseudo-account_ is frozen for the `Vault.Asset`. (`tecFROZEN` for IOUs, `tecLOCKED` for MPTs) When the amendment is not enabled, the check does not apply.

### 3.5 Transaction: `LoanSet`

#### 3.5.1 Failure Conditions

Parent §3.8.5.2 check 20: when the amendment is enabled, the minimum cover is rounded up to the precision of the Vault (§3.6). When the amendment is not enabled, it is rounded up without rounding it to the asset precision.

### 3.6 Transactions: `LoanSet`, `LoanPay`, `LoanBrokerCoverWithdraw` and `LoanBrokerCoverClawback`

#### 3.6.1 Minimum Cover

`LoanSet`, `LoanPay`, `LoanBrokerCoverWithdraw` and `LoanBrokerCoverClawback` compute the minimum cover as `LoanBroker.DebtTotal × LoanBroker.CoverRateMinimum`. When the amendment is enabled, every one of them rounds this product up to the precision of the Vault: the precision of `Vault.AssetsTotal`, or the base scale for a Vault with `LEVersion` 2.

When the amendment is enabled, the fee destination test in parent §3.11.5 step 1 uses that rounding. When the amendment is not enabled, it rounds the product up to `Loan.LoanScale`.

#### 3.6.2 Amortization

When the amendment is enabled, the following change Appendix A-2 and A-3.3 of the parent. When it is not enabled, the parent text applies.

1. **Payment factor.** In the periodic payment factor (A-2 equation 6) and the principal derived from a periodic payment, `(1 + r)^n - 1` is computed as follows: if `n × r >= 10^-9`, as `(1 + r)^n - 1`; otherwise as the binomial sum `n·r + C(n,2)·r^2 + …`, stopping when the next term no longer changes the sum. The factor is `r × (1 + r)^n / ((1 + r)^n - 1)`.
2. **Periodic payment target.** In `compute_payment_due`, the target principal is rounded up (`UP`) and the target interest is rounded down (`DOWN`) to `Loan.LoanScale`. The target value and the target management fee are still rounded to nearest.
3. **Overpayment amount.** In `make_payment` STEP 4, the overpayment amount is rounded down to `Loan.LoanScale`. If the result is zero, no overpayment is made.
4. **Overpayment principal.** In `try_overpayment`, after the preserved rounding errors are added, the principal of `newTheoreticalState` is set to `loan.principalOutstanding - overpaymentComponents.trackedPrincipalDelta`, and its management fee is set to `(valueOutstanding - principalOutstanding) × managementFeeRate`, where `valueOutstanding` is the value of `newTheoreticalState`. The interest is derived from these values.

### 3.7 Transactions: `LoanBrokerCoverWithdraw` and `LoanPay`

#### 3.7.1 Invariants

When the amendment is enabled, the MPT transfer invariant does not require `lsfMPTCanTransfer` for an MPT moved between holders by `LoanBrokerCoverWithdraw` or `LoanPay`. When the amendment is not enabled, these transactions get no such waiver.

## 4. Rationale

Rounding a deposit down to the cover precision before it is transferred keeps `LoanBroker.CoverAvailable` equal to what the broker holds. Rejecting amounts that round to zero stops transactions that change nothing but charge a fee. One rounding rule for the minimum cover makes the same broker pass or fail the same test in every transaction.

First-loss capital is the broker's own collateral, and the broker must be able to recover it; `lsfMPTCanTransfer` controls transfers between holders, which a cover withdrawal is not.

At an integer scale, rounding the target principal to nearest can leave the principal component of a payment at zero while the interest component takes the whole payment. Rounding the target principal up keeps principal at its floor until the final payment, and rounding the target interest down lets interest absorb each payment.

## 5. Security Considerations

The `lsfMPTCanTransfer` waiver applies only to `LoanBrokerCoverWithdraw`. Freeze, authorization and other transfer checks still apply. The amortization changes alter how each payment is split, not the total the Borrower owes, and every component remains capped by the outstanding amounts.
