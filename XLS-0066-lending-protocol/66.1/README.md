<pre>
  xls: 66.1
  title: Lending Protocol Cash-Basis Accounting
  description: Introduces Cash-Basis accounting for the Lending Protocol
  author: Vytautas Vito Tumas <vtumas@ripple.com>
  proposal-from: https://github.com/XRPLF/XRPL-Standards/discussions/190
  status: Draft
  category: Amendment
  created: 2026-09-04
  updated: 2026-09-08
</pre>

# Lending Protocol Cash-Basis Accounting

## 1. Abstract

Under the `LendingProtocolV1_1` amendment, for a Vault with `LEVersion == 1` (cash basis, see [XLS-65.1 cash-basis accounting](../../XLS-0065-single-asset-vault/65.1/vault-cash-basis.md)), `LoanBroker.DebtTotal` tracks loan principal only and `Vault.AssetsTotal` recognises interest when it is collected rather than when a Loan is issued.

## 2. Motivation

Under accrual accounting, issuing a Loan immediately increases `Vault.AssetsTotal` by the expected interest and `LoanBroker.DebtTotal` by the principal plus expected interest. The `AssetsMaximum` and `DebtMaximum` caps are therefore consumed by interest that has not been paid, and the first-loss capital requirement, which is a rate applied to `DebtTotal`, is sized against expected interest as well as principal.

## 3. Specification

### 3.1 Transaction: `LoanSet`

#### 3.1.1 Failure Conditions

For a Vault with `LEVersion == 1`, parent checks 6 and 14 do not apply, and the Broker cap checks 19 and 20 are replaced by principal-only checks:

19. `LoanBroker.DebtMaximum != 0` and `LoanBroker.DebtMaximum < LoanBroker.DebtTotal + PrincipalRequested`. (`tecLIMIT_EXCEEDED`)
20. `LoanBroker.CoverAvailable < (LoanBroker.DebtTotal + PrincipalRequested) × LoanBroker.CoverRateMinimum`. (`tecINSUFFICIENT_FUNDS`)

For a Vault with `LEVersion` absent, parent checks 6, 14, 19, and 20 apply unchanged.

#### 3.1.2 State Changes

For a Vault with `LEVersion == 1`, steps 6 and 7 of [3.8.6 State Changes](../README.md#386-state-changes) are replaced by the following; all other steps are unchanged. For a Vault with `LEVersion` absent, steps 6 and 7 apply unchanged:

6. Update `Vault` object:
   - Decrease `Vault.AssetsAvailable` by `PrincipalRequested`.
   - `Vault.AssetsTotal` is unchanged; `InterestDue` is not recognised at origination.
7. Update `LoanBroker` object:
   - Increase `LoanBroker.DebtTotal` by `PrincipalRequested` only; `InterestDue` is excluded.
   - Increment `LoanBroker.OwnerCount` by `1`.
   - Increment `LoanBroker.LoanSequence` by `1`.

### 3.2 Transaction: `LoanPay`

#### 3.2.1 State Changes

For a Vault with `LEVersion == 1`, steps 6 and 7 of [3.11.5 State Changes](../README.md#3115-state-changes) are replaced by the following; all other steps, including the asset transfers, are unchanged. For a Vault with `LEVersion` absent, steps 6 and 7 apply unchanged:

6. **`LoanBroker` Updates**:
   - `LoanBroker.DebtTotal` is decreased by `principalPaid` only; `valueChange` does not apply.
   - If fees were directed to the cover pool, `LoanBroker.CoverAvailable` increases by `totalToBroker`.
7. **`Vault` Updates**:
   - `Vault.AssetsAvailable` increases by `totalToVault`, which is `principalPaid + interestPaid` rounded to the Vault's asset scale.
   - `Vault.AssetsTotal` is increased by `interestPaid` only; `valueChange` does not apply.

Principal repayment does not reduce `Vault.AssetsTotal`. Because the cash-basis origination checks do not enforce `AssetsMaximum`, an interest receipt may increase `Vault.AssetsTotal` above `Vault.AssetsMaximum`; the cap restricts deposits, not interest receipts.

### 3.3 Transaction: `LoanManage`

#### 3.3.1 Failure Conditions

For a Vault with `LEVersion == 1`, parent check 8 is replaced by the following principal-only impairment check:

8. `tfLoanImpair` is specified and `Vault.LossUnrealized + Loan.PrincipalOutstanding > Vault.AssetsTotal - Vault.AssetsAvailable`. (`tecLIMIT_EXCEEDED`)

For a Vault with `LEVersion` absent, parent check 8 applies unchanged.

#### 3.3.2 State Changes

For a Vault with `LEVersion == 1`, the amount computations in items 1 to 3 of [3.10.5 State Changes](../README.md#3105-state-changes) are replaced by the following; nested substeps (flags, transfers, `DebtTotal`, and field clears) are unchanged except that they use these amounts. For a Vault with `LEVersion` absent, the parent amount computations in items 1 to 3 apply unchanged:

1. If the `tfLoanDefault` flag is specified:
   - Compute `DefaultAmount = Loan.PrincipalOutstanding`, replacing `Loan.TotalValueOutstanding - Loan.ManagementFeeOutstanding`. All downstream calculations use `DefaultAmount` unchanged.
2. If the `tfLoanImpair` flag is specified:
   - Compute `LossUnrealized = Loan.PrincipalOutstanding`, replacing `Loan.TotalValueOutstanding - Loan.ManagementFeeOutstanding`.
3. If the `tfLoanUnimpair` flag is specified:
   - Compute `LossReversed = Loan.PrincipalOutstanding`, replacing `Loan.TotalValueOutstanding - Loan.ManagementFeeOutstanding`.

## 4. Rationale

Interest could have been recognised on a schedule, one payment period at a time, rather than on receipt. That was rejected because it reintroduces the original problem in a smaller form: the Vault would still credit itself with interest for a period in which the Borrower ends up not paying.

## 5. Security Considerations

Principal-only accounting makes `DebtTotal` a smaller number for the same set of Loans, so a `CoverRateMinimum` that was calibrated under accrual accounting yields less first-loss capital. A Broker migrating to a cash-basis Vault should re-derive the rate rather than reuse it.

Both accounting models coexist on the ledger for as long as pre-amendment Vaults exist. An implementation must branch on `Vault.LEVersion` in every place it adjusts `AssetsTotal` or `DebtTotal`; branching in some places and not others corrupts the share exchange rate of the Vault.
