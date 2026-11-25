<pre>
  xls: 66.5
  title: Lending Protocol Cleanup 3.4.0
  description: Lending Protocol changes of the fixCleanup3_4_0 amendment, including late-only impairment, exclusive due-date boundaries, and relaxed authorization and holding checks
  author: Vytautas Vito Tumas <vtumas@ripple.com>
  proposal-from: https://github.com/XRPLF/XRPL-Standards/discussions/190
  status: Final
  category: Amendment
  created: 2026-09-04
  updated: 2026-11-25
</pre>

# 66.5 Lending Protocol Cleanup 3.4.0

## 1. Abstract

Under the `fixCleanup3_4_0` amendment, a Loan can be impaired only after its payment is already overdue; impairing and unimpairing leave `Loan.NextPaymentDueDate` unchanged, and the payment due-date and default grace-period boundaries are exclusive: a payment is late only when the current ledger close time is greater than `Loan.NextPaymentDueDate`, and default is allowed only when it is greater than `Loan.NextPaymentDueDate + Loan.GracePeriod`. Equality at either boundary is not expired.

The amendment also removes the authorization checks on the pseudo-accounts that receive a `LoanPay`, runs the `LoanSet` holding check only when a holding must be created, allows `CredentialIDs` on `LoanBrokerCoverWithdraw`, checks that a holding can be created for a cover withdrawal to the submitter, and exempts the First-Loss Capital transfer of a `LoanManage` default from the freeze invariants.

## 2. Motivation

Pre-amendment impairment can fire before a payment is overdue and then pull `Loan.NextPaymentDueDate` forward so the Loan can be defaulted on a shortened clock. Unimpairing rewrites that date again. Treating equality with the due date or the grace-period end as already expired also defaults or late-pays a Loan on the exact boundary. The amendment keeps the payment schedule intact and treats the boundary as not yet late.

The other changes remove checks that could reject a valid transaction: a pseudo-account always holds the asset it receives, an existing holding needs no creation check, a cover withdrawal to a third party with deposit authorization needs a way to present credentials, and a default must be possible even when the Vault asset is frozen.

## 3. Specification

### 3.1 Transaction: `LoanManage`

#### 3.1.1 Failure Conditions

When the amendment is enabled, parent check 6 uses an exclusive grace-period boundary, and parent checks 7 and 8 keep their numbers. A new overdue-only impair check is added as parent check 9:

- Parent check 6: `tfLoanDefault` is specified and `currentTime <= Loan.NextPaymentDueDate + Loan.GracePeriod`. (`tecTOO_SOON`)
- Parent check 9: `tfLoanImpair` is specified and `currentTime <= Loan.NextPaymentDueDate` (can only impair a loan whose payment is already overdue). (`tecTOO_SOON`) This check runs before parent check 8.

When the amendment is not enabled, parent check 6 uses `currentTime < Loan.NextPaymentDueDate + Loan.GracePeriod`, and check 9 does not apply.

#### 3.1.2 State Changes

When the amendment is enabled, the `Loan.NextPaymentDueDate` rewrites in steps 2 and 3 of [3.10.5 State Changes](../README.md#3105-state-changes) do not apply; all other steps are unchanged. Those two steps become:

2. If the `tfLoanImpair` flag is specified:
   - `Loan.NextPaymentDueDate` is unchanged.
3. If the `tfLoanUnimpair` flag is specified:
   - `Loan.NextPaymentDueDate` is unchanged.

When the amendment is not enabled, the parent rewrites in those steps apply unchanged.

#### 3.1.3 Invariants

When the amendment is enabled, the freeze and lock invariants do not fail a `LoanManage` transaction with `tfLoanDefault` because of the transfer of First-Loss Capital from the `LoanBroker` _pseudo-account_ to the `Vault` _pseudo-account_. The exemption covers only the balances between the `Vault.Asset` issuer and those two _pseudo-accounts_, for the `Vault.Asset` only. When the amendment is not enabled, a frozen or locked asset fails the invariant.

### 3.2 Transaction: `LoanPay`

#### 3.2.1 Failure Conditions

When the amendment is enabled, parent check 11 uses an exclusive due-date boundary:

11. The `tfLoanLatePayment` flag is not specified and `currentTime > Loan.NextPaymentDueDate`. (`tecEXPIRED`)

When the amendment is not enabled, parent check 11 uses `currentTime >= Loan.NextPaymentDueDate`.

When the amendment is enabled, parent check 16 uses the same exclusive boundary:

16. The `tfLoanLatePayment` flag is specified and `currentTime <= Loan.NextPaymentDueDate`. (`tecTOO_SOON`)

When the amendment is not enabled, parent check 16 uses `currentTime < Loan.NextPaymentDueDate`.

When the amendment is enabled, the payment no longer fails if the Vault _pseudo-account_ or the account receiving the fee fails the asset authorization check. When the amendment is not enabled, a non-zero amount to the Vault _pseudo-account_, or a non-zero fee, requires the receiving account to pass that check.

#### 3.2.2 Transaction Fee

When the amendment is enabled:

- If `Amount <= 0`, the fee is the standard transaction fee.
- The late payment test in parent §3.11.3 uses the exclusive boundary: the payment is late if `currentTime > Loan.NextPaymentDueDate`.

### 3.3 Transaction: `LoanSet`

#### 3.3.1 Failure Conditions

When the amendment is enabled, parent §3.8.5.2 check 8 (cannot add asset holding) runs only if the Borrower has no holding of the `Vault.Asset`, or if `LoanOriginationFee` is non-zero and the `LoanBroker.Owner` has no holding of the `Vault.Asset`. When the amendment is not enabled, the check always runs.

### 3.4 Transaction: `LoanBrokerCoverWithdraw`

#### 3.4.1 Fields

When the amendment and `Credentials` are both enabled, the transaction accepts the optional `CredentialIDs` field:

| Field Name      | Required | JSON Type | Internal Type | Default Value | Description                                                                                                 |
| --------------- | :------: | :-------: | :-----------: | :-----------: | :---------------------------------------------------------------------------------------------------------- |
| `CredentialIDs` |    No    |  `array`  |  `VECTOR256`  |     Empty     | Credentials that authorize the submitter to deposit to a `Destination` that requires deposit authorization. |

When either amendment is not enabled, a transaction with `CredentialIDs` fails with `temDISABLED`.

#### 3.4.2 Failure Conditions

When the amendment is enabled, the following checks are added:

- Data verification: `CredentialIDs` is present and is empty, has more than the maximum number of entries, contains a zero entry, or contains a duplicate. (`temMALFORMED`)
- Protocol-level: a credential in `CredentialIDs` does not exist, does not have the submitter as its subject, or has not been accepted. (`tecBAD_CREDENTIALS`) This check runs before parent check 6.
- Protocol-level: parent check 8 (deposit authorization) passes if the `Destination` has preauthorized the credentials in `CredentialIDs`.
- Protocol-level: the destination is the submitter, the submitter has no holding of the `Vault.Asset`, and a holding cannot be added for it. This check runs after parent check 9.
- When the cover is transferred: the destination is not the submitter, `CredentialIDs` is present, and a listed credential has expired. The expired credentials are deleted, and the deletions are kept even though the transaction fails. (`tecEXPIRED`)

## 4. Rationale

Pulling the due date forward on impair was a way to accelerate default after the Broker had already booked a paper loss. That couples a reporting action to the payment calendar. Leaving `Loan.NextPaymentDueDate` alone keeps impairment as a Vault accounting mark, and the exclusive boundary avoids treating the due instant itself as already late.

Pseudo-accounts that receive a `LoanPay` already hold the asset, so their authorization checks could only reject a payment a Borrower is entitled to make. A Broker must be able to default an overdue Loan even if the Vault asset is frozen; otherwise a freeze would keep a defaulted Loan open.

## 5. Security Considerations

After the amendment, a Broker cannot impair a current Loan in order to default it before the original grace period ends. Implementations must use the exclusive comparison in every late-payment and default check; mixing inclusive and exclusive comparisons lets a payment on the due instant succeed in one path and fail in another.

The freeze-invariant exemption for a default is limited to the two _pseudo-accounts_ and the issuer of the Vault asset. A frozen line or a different asset touched by the same transaction still fails the invariant.
