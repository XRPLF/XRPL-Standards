<pre>
  xls: 66.1
  title: Principal-Only Debt Accounting
  description: Makes LoanBroker.DebtTotal principal-only and recognizes Vault interest on receipt for cash-basis Vaults
  author: Vytautas Vito Tumas <vtumas@ripple.com>, Aanchal Malhotra <amalhotra@ripple.com>
  implementation: https://github.com/XRPLF/rippled/pull/5270
  proposal-from: https://github.com/XRPLF/XRPL-Standards/discussions/190
  status: Draft
  category: Amendment
  requires: [XLS-66](../README.md), [XLS-65.1](../../XLS-0065-single-asset-vault/65.1/README.md)
  created: 2026-09-04
  updated: 2026-09-04
</pre>

# Principal-Only Debt Accounting

## 1. Abstract

This patch of [XLS-66](../README.md) records the changes the `LendingProtocolV1_1` amendment makes to the Lending Protocol. For a Vault with `LEVersion == 1` (cash basis, see [XLS-65.1](../../XLS-0065-single-asset-vault/65.1/README.md)), `LoanBroker.DebtTotal` tracks loan principal only and `Vault.AssetsTotal` recognises interest when it is collected rather than when a Loan is issued.

The consolidated specification is the top-level [README.md](../README.md).

## 2. Motivation

Under accrual accounting, issuing a Loan immediately increases `Vault.AssetsTotal` by the expected interest and `LoanBroker.DebtTotal` by the principal plus expected interest. The `AssetsMaximum` and `DebtMaximum` caps are therefore consumed by interest that has not been paid, and the first-loss capital requirement, which is a rate applied to `DebtTotal`, is sized against expected interest as well as principal.

## 3. Specification

### 3.1 Transaction: `LoanSet`

#### 3.1.1 Failure Conditions

For a Vault with `LEVersion == 1`, checks 6 and 14 of the parent specification do not apply, and the Broker cap checks 19 and 20 are replaced by principal-only checks:

1. `LoanBroker.DebtMaximum != 0` and `LoanBroker.DebtMaximum < LoanBroker.DebtTotal + PrincipalRequested`. (`tecLIMIT_EXCEEDED`)
2. `LoanBroker.CoverAvailable < (LoanBroker.DebtTotal + PrincipalRequested) × LoanBroker.CoverRateMinimum`. (`tecINSUFFICIENT_FUNDS`)

For a Vault with `LEVersion` absent, parent checks 6, 14, 19, and 20 apply unchanged.

#### 3.1.2 State Changes

For a Vault with `LEVersion == 1`, issuing a Loan leaves `Vault.AssetsTotal` unchanged and increases `LoanBroker.DebtTotal` by `PrincipalRequested`. For a Vault with `LEVersion` absent, issuing a Loan increases `Vault.AssetsTotal` by `InterestDue` and increases `LoanBroker.DebtTotal` by `PrincipalRequested + InterestDue`.

### 3.2 Transaction: `LoanPay`

#### 3.2.1 State Changes

For a Vault with `LEVersion == 1`, a payment splits into principal and interest:

- `Vault.AssetsTotal` increases by `interestPaid`.
- `LoanBroker.DebtTotal` decreases by `principalPaid`.
- `Vault.AssetsAvailable` increases by `totalToVault`, which is `principalPaid + interestPaid` rounded to the Vault's asset scale.

Principal repayment does not reduce `Vault.AssetsTotal`. Because the cash-basis origination checks do not enforce `AssetsMaximum`, an interest receipt may increase `Vault.AssetsTotal` above `Vault.AssetsMaximum`; the cap restricts deposits, not interest receipts.

For a Vault with `LEVersion` absent, the parent accrual-basis state changes apply unchanged.

### 3.3 Transaction: `LoanManage`

#### 3.3.1 State Changes

For a Vault with `LEVersion == 1`, a default writes off principal only, because uncollected interest was never recognised. For a Vault with `LEVersion` absent, the write-off covers principal and accrued interest.

## 4. Rationale

Interest could have been recognised on a schedule, one payment period at a time, rather than on receipt. That was rejected because it reintroduces the original problem in a smaller form: the Vault would still credit itself with interest for a period in which the Borrower ends up not paying.

## 5. Security Considerations

Principal-only accounting makes `DebtTotal` a smaller number for the same set of Loans, so a `CoverRateMinimum` that was calibrated under accrual accounting yields less first-loss capital. A Broker migrating to a cash-basis Vault should re-derive the rate rather than reuse it.

Both accounting models coexist on the ledger for as long as pre-amendment Vaults exist. An implementation must branch on `Vault.LEVersion` in every place it adjusts `AssetsTotal` or `DebtTotal`; branching in some places and not others corrupts the share exchange rate of the Vault.
