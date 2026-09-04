<pre>
  xls: 65.1
  title: Vault Cash-Basis Accounting
  description: Adds the Vault LEVersion field, which selects cash-basis accounting for the assets of a Vault
  author: Vytautas Vito Tumas <vtumas@ripple.com>, Aanchal Malhotra <amalhotra@ripple.com>
  proposal-from: https://github.com/XRPLF/XRPL-Standards/discussions/192
  status: Draft
  category: Amendment
  requires: [XLS-65](../README.md)
  created: 2026-09-04
  updated: 2026-09-04
</pre>

# Vault Cash-Basis Accounting

## 1. Abstract

This patch of [XLS-65](../README.md) records the changes the `LendingProtocolV1_1` amendment makes to the `Vault` ledger entry. The amendment adds a `LEVersion` field that selects the accounting model a Vault applies to `AssetsTotal`. Vaults created while the amendment is enabled use cash-basis accounting, in which `AssetsTotal` tracks principal only and grows only as interest is collected in cash. Vaults created before the amendment keep accrual-basis accounting, in which `AssetsTotal` includes interest as it accrues.

The consolidated specification is the top-level [README.md](../README.md).

## 2. Motivation

Accrual-basis accounting credits a Vault with interest that a Borrower has not paid yet, so the share exchange rate reflects income the Vault has not received. A depositor can redeem shares at a rate inflated by interest that later defaults, and the loss falls on the depositors who remain. Cash-basis accounting removes that mismatch by recognising interest only when it is paid.

Existing Vaults cannot switch accounting models without changing the value of shares already issued, so the model has to be recorded per Vault rather than derived from the amendment state at the time of the transaction.

## 3. Specification

### 3.1 Ledger Entry: `Vault`

#### 3.1.1 Fields

| Field Name  | Constant | Required | Internal Type | Default Value | Description                                                              |
| ----------- | :------: | :------: | :-----------: | :-----------: | ------------------------------------------------------------------------ |
| `LEVersion` |   Yes    |    No    |    `UINT8`    | absent (`0`)  | The accounting model the Vault applies to `AssetsTotal`. Absent is treated as `0` (accrual basis). Immutable once set. |

#### 3.1.2 `LEVersion`

`LEVersion` selects the accounting model of the Vault:

- `LEVersion` absent (treated as `0`, accrual basis): `AssetsTotal` includes the interest accrued over the life of the connected Loans. This is the pre-amendment behaviour and continues to apply to every Vault created before the amendment was enabled.
- `LEVersion = 1` (cash basis): `AssetsTotal` is principal-only and increases only as interest is collected in cash.

The field is immutable. A Vault created while the amendment is enabled is always cash-basis, and a Vault created before it is always accrual-basis; neither can be converted to the other.

#### 3.1.3 Invariants

- `Vault.LEVersion` is immutable once set.
- `Vault.LEVersion` is either absent or `1`.

#### 3.1.4 Example JSON

```json
{
  "LedgerEntryType": "Vault",
  "LEVersion": 1,
  "Asset": { "currency": "USD", "issuer": "rf1BiGeXwwQoi8Z2ueFYTEXSwuJYfV2Jpn" },
  "AssetsTotal": "1000",
  "AssetsAvailable": "1000",
  "SharesTotal": "1000"
}
```

### 3.2 Transaction: `VaultCreate`

#### 3.2.1 Failure Conditions

No failure conditions are added or removed. `LEVersion` is not a transaction field and cannot be supplied by the submitter.

#### 3.2.2 State Changes

When the amendment is enabled, the created `Vault` ledger entry has `LEVersion = 1`. When it is not enabled, the field is not written and the Vault is accrual-basis.

## 4. Rationale

The alternative to a per-entry version field is to derive the accounting model from the amendment state at the time each Loan transaction executes. That was rejected because it would silently change the share exchange rate of every existing Vault on the ledger at the moment the amendment activates.

`LEVersion` is a version number rather than a boolean flag so that a later accounting change can be expressed as a further version without another field.

## 5. Security Considerations

Cash-basis accounting reduces, but does not remove, the exposure of a depositor to an unpaid Loan: the Vault still carries the principal at face value until the Loan defaults or is impaired. `LossUnrealized` remains the mechanism for reporting an expected shortfall.

Because `LEVersion` is immutable, an implementation must read it from the `Vault` ledger entry rather than from the amendment state when computing the interest accounting of a Loan. Reading the amendment state instead would apply cash-basis rules to accrual-basis Vaults and misprice their shares.
