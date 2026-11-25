<pre>
  xls: 66.1
  title: Lending Protocol Cleanup 3.1.3
  description: Lending Protocol changes of the fixCleanup3_1_3 amendment to LoanPay fees, overpayments and LoanBroker cover invariants
  author: Vytautas Vito Tumas <vtumas@ripple.com>
  proposal-from: https://github.com/XRPLF/XRPL-Standards/discussions/190
  status: Final
  category: Amendment
  created: 2026-11-25
  updated: 2026-11-25
</pre>

# 66.1 Lending Protocol Cleanup 3.1.3

## 1. Abstract

Under the `fixCleanup3_1_3` amendment, the `LoanPay` transaction fee is capped at 20 base fees, an overpayment on a Loan that does not allow overpayments fails with `tecNO_PERMISSION` instead of `temINVALID_FLAG`, and the payment amount is truncated to the Loan scale before an overpayment is computed. A new invariant requires `LoanBroker.CoverAvailable` not to exceed the broker _pseudo-account_ balance.

## 2. Motivation

`LoanPay` processes at most 100 periodic payments per transaction, but the parent fee grows with `Amount` without limit. `temINVALID_FLAG` is a malformed-transaction code, but the failure depends on the `Loan` object, so it is a ledger-state failure. An overpayment computed from an amount finer than the Loan scale can produce components that round to zero.

## 3. Specification

No fields are added or removed.

### 3.1 Transaction: `LoanPay`

#### 3.1.1 Transaction Fee

In parent §3.11.3 step 2, when the amendment is enabled: if `Amount >= regularPayment × 100`, the fee is `20 × baseFee`. When the amendment is not enabled, the fee is not capped.

#### 3.1.2 Failure Conditions

Parent §3.11.4.2 check 3 (`tfLoanOverpayment` is set and `lsfLoanOverpayment` is not set on the Loan) returns:

- Before `fixCleanup3_1_3`: `temINVALID_FLAG`.
- `fixCleanup3_1_3`: `tecNO_PERMISSION`.

#### 3.1.3 State Changes

When the amendment is enabled, after the periodic payments of a regular payment are made, `Amount` is rounded toward zero to `Loan.LoanScale` before the remaining overpayment amount is computed (Appendix A-3.3, STEP 4). When the amendment is not enabled, the unrounded `Amount` is used.

### 3.2 Transaction: `LoanManage`

#### 3.2.1 State Changes

When the amendment is enabled, every successful `LoanManage` normalizes the stored amounts of the `Loan`, `LoanBroker` and `Vault` to the `Vault.Asset` precision. When the amendment is not enabled, `LoanManage` does not normalize them.

### 3.3 Ledger Entry: `LoanBroker`

#### 3.3.1 Invariants

Added to parent §3.1.8: when the amendment is enabled, `LoanBroker.CoverAvailable` is not greater than the broker _pseudo-account_ balance of the `Vault.Asset`, except in a `LoanBrokerDelete` transaction.

## 4. Rationale

Each 5 payments cost one base fee, so 100 payments cost 20 base fees; charging more pays for work the transaction does not do. Truncating the amount at the Loan scale avoids processing overpayment dust whose components round to zero.

## 5. Security Considerations

With the parent invariant, the new invariant makes `LoanBroker.CoverAvailable` equal to the _pseudo-account_ balance after every transaction other than `LoanBrokerDelete`, so first-loss capital cannot be reported that the broker does not hold.
