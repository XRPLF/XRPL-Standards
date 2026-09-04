<pre>
  xls: 66.1
  title: Principal-Only Debt Accounting
  description: Makes Vault.AssetsTotal and LoanBroker.DebtTotal principal-only for cash-basis Vaults and restricts lending to closed-ended Vaults
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

This patch of [XLS-66](../README.md) records the changes the `LendingProtocolV1_1` amendment makes to the Lending Protocol. For a Vault with `LEVersion == 1` (cash basis, see [XLS-65.1](../../XLS-0065-single-asset-vault/65.1/README.md)), `Vault.AssetsTotal` and `LoanBroker.DebtTotal` track loan principal only; interest is recognised when it is collected rather than when a Loan is issued. A `LoanBroker` may only be attached to a closed-ended Vault.

The consolidated specification is the top-level [README.md](../README.md).

## 2. Motivation

Under accrual accounting, issuing a Loan immediately increases `Vault.AssetsTotal` and `LoanBroker.DebtTotal` by the principal plus the whole of the expected interest. Two consequences follow. The `AssetsMaximum` cap and the `DebtMaximum` cap are consumed by interest that has not been paid, so a Broker reaches its debt ceiling earlier than the principal at risk implies. And the first-loss capital requirement, which is a rate applied to `DebtTotal`, is sized against expected interest as well as principal.

Restricting lending to closed-ended Vaults removes the second mismatch: an open-ended Vault allows redemptions at any time, so a depositor can exit at a share price that includes interest still owed by a Borrower.

## 3. Specification

### 3.1 Transaction: `LoanBrokerSet`

#### 3.1.1 Fields

No fields are added or removed.

#### 3.1.2 Failure Conditions

When a new `LoanBroker` is created (no `LoanBrokerID` supplied), the following protocol-level failure applies in addition to the existing checks:

1. The `Vault` identified by `VaultID` is not closed-ended, that is `Vault.VaultKind` is absent or not equal to `1`. (`tecNO_PERMISSION`)

The check is evaluated before the asset-holding and reserve checks. Modifying an existing `LoanBroker` does not re-evaluate it.

#### 3.1.3 State Changes

Unchanged.

#### 3.1.4 Example JSON

```json
{
  "TransactionType": "LoanBrokerSet",
  "Account": "rf1BiGeXwwQoi8Z2ueFYTEXSwuJYfV2Jpn",
  "Fee": "10",
  "Sequence": 12345,
  "VaultID": "9CD5F03A9D0F4F7C0B8B4C5F5A4D3E2B1A0F9E8D7C6B5A493827160504030201",
  "DebtMaximum": "100000"
}
```

### 3.2 Transaction: `LoanSet`

#### 3.2.1 Failure Conditions

For a Vault with `LEVersion == 1`, origination no longer credits `InterestDue` into `Vault.AssetsTotal`, so the `AssetsMaximum` origination check does not apply. The Broker cap checks are evaluated against principal instead:

1. `LoanBroker.DebtMaximum != 0` and `LoanBroker.DebtMaximum < LoanBroker.DebtTotal + PrincipalRequested`. (`tecLIMIT_EXCEEDED`)
2. `LoanBroker.CoverAvailable < (LoanBroker.DebtTotal + PrincipalRequested) × LoanBroker.CoverRateMinimum`. (`tecINSUFFICIENT_FUNDS`)

For a Vault with `LEVersion` absent, the corresponding accrual-basis checks apply unchanged.

#### 3.2.2 State Changes

For a Vault with `LEVersion == 1`, issuing a Loan increases `Vault.AssetsTotal` and `LoanBroker.DebtTotal` by `PrincipalRequested` only. For a Vault with `LEVersion` absent, both values increase by the principal plus the total expected interest.

### 3.3 Transaction: `LoanPay`

#### 3.3.1 State Changes

For a Vault with `LEVersion == 1`, a payment splits into principal and interest:

- The principal portion reduces `Vault.AssetsTotal` and `LoanBroker.DebtTotal` and increases `Vault.AssetsAvailable`.
- The interest portion, net of fees, increases `Vault.AssetsTotal` and `Vault.AssetsAvailable`. This is the point at which the Vault recognises the interest.

For a Vault with `LEVersion` absent, the interest was already included in `AssetsTotal` when the Loan was issued, so a payment moves value from `AssetsTotal` to `AssetsAvailable` without changing the total.

### 3.4 Transaction: `LoanManage`

#### 3.4.1 State Changes

For a Vault with `LEVersion == 1`, a default writes off principal only, because uncollected interest was never recognised. For a Vault with `LEVersion` absent, the write-off covers principal and accrued interest.

## 4. Rationale

Interest could have been recognised on a schedule, one payment period at a time, rather than on receipt. That was rejected because it reintroduces the original problem in a smaller form: the Vault would still credit itself with interest for a period in which the Borrower ends up not paying.

The closed-ended restriction is enforced at `LoanBrokerSet` rather than at `LoanSet` so that the constraint is checked once, when the Vault is attached, rather than on every Loan.

## 5. Security Considerations

Principal-only accounting makes `DebtTotal` a smaller number for the same set of Loans, so a `CoverRateMinimum` that was calibrated under accrual accounting yields less first-loss capital. A Broker migrating to a cash-basis Vault should re-derive the rate rather than reuse it.

Both accounting models coexist on the ledger for as long as pre-amendment Vaults exist. An implementation must branch on `Vault.LEVersion` in every place it adjusts `AssetsTotal` or `DebtTotal`; branching in some places and not others corrupts the share exchange rate of the Vault.
