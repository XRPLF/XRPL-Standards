<pre>
  xls: 66.2
  title: Lending Protocol Impairment Timing
  description: Introduces late-only impairment, exclusive due-date boundaries, and leaves NextPaymentDueDate unchanged on impair and unimpair
  author: Vytautas Vito Tumas <vtumas@ripple.com>
  proposal-from: https://github.com/XRPLF/XRPL-Standards/discussions/190
  status: Draft
  category: Amendment
  created: 2026-09-04
  updated: 2026-09-09
</pre>

# Lending Protocol Impairment Timing

## 1. Abstract

Under the `fixCleanup3_4_0` amendment, a Loan can be impaired only after its payment is already overdue, impair and unimpair leave `Loan.NextPaymentDueDate` unchanged, and the payment due-date and default grace-period boundaries are exclusive: a payment is late only when the current ledger close time is greater than `Loan.NextPaymentDueDate`, and default is allowed only when it is greater than `Loan.NextPaymentDueDate + Loan.GracePeriod`. Equality at either boundary is not expired.

## 2. Motivation

**Impairment Timing.** Pre-amendment impairment can fire before a payment is overdue and then pull `Loan.NextPaymentDueDate` forward so the Loan can be defaulted on a shortened clock. Unimpairing rewrites that date again. Treating equality with the due date or the grace-period end as already expired also defaults or late-pays a Loan on the exact boundary. The amendment keeps the payment schedule intact and treats the boundary as not yet late.

## 3. Specification

### 3.1 Transaction: `LoanManage`

#### 3.1.1 Failure Conditions

When the amendment is enabled, parent check 6 uses an exclusive grace-period boundary, and parent checks 7 and 8 keep their numbers. A new overdue-only impair check is added as parent check 9:

6. `tfLoanDefault` is specified and `currentTime <= Loan.NextPaymentDueDate + Loan.GracePeriod`. (`tecTOO_SOON`)
9. `tfLoanImpair` is specified and `currentTime <= Loan.NextPaymentDueDate` (can only impair a loan whose payment is already overdue). (`tecTOO_SOON`)

When the amendment is not enabled, parent check 6 uses `currentTime < Loan.NextPaymentDueDate + Loan.GracePeriod`, and check 9 does not apply.

#### 3.1.2 State Changes

When the amendment is enabled, the `Loan.NextPaymentDueDate` rewrites in steps 2 and 3 of [3.10.5 State Changes](../README.md#3105-state-changes) do not apply; all other steps are unchanged. When the amendment is not enabled, those rewrites apply unchanged:

2. If the `tfLoanImpair` flag is specified:
   - `Loan.NextPaymentDueDate` is unchanged.
3. If the `tfLoanUnimpair` flag is specified:
   - `Loan.NextPaymentDueDate` is unchanged.

### 3.2 Transaction: `LoanPay`

#### 3.2.1 Failure Conditions

When the amendment is enabled, parent check 11 uses an exclusive due-date boundary:

11. The `tfLoanLatePayment` flag is not specified and `currentTime > Loan.NextPaymentDueDate`. (`tecEXPIRED`)

When the amendment is not enabled, parent check 11 uses `currentTime >= Loan.NextPaymentDueDate`.

## 4. Rationale

**Impairment Timing.** Pulling the due date forward on impair was a way to accelerate default after the Broker had already booked a paper loss. That couples a reporting action to the payment calendar. Leaving `Loan.NextPaymentDueDate` alone keeps impairment as a Vault accounting mark, and the exclusive boundary avoids treating the due instant itself as already late.

## 5. Security Considerations

**Impairment Timing.** After the amendment, a Broker cannot impair a current Loan in order to default it before the original grace period ends. Implementations must use the exclusive comparison in every late-payment and default check; mixing inclusive and exclusive comparisons lets a payment on the due instant succeed in one path and fail in another.
