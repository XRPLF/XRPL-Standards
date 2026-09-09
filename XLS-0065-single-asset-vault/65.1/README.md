<pre>
  xls: 65.1
  title: Single Asset Vault Cash-Basis Accounting
  description: Introduces Cash-Basis accounting for the Single Asset Vault
  author: Vytautas Vito Tumas <vtumas@ripple.com>
  proposal-from: https://github.com/XRPLF/XRPL-Standards/discussions/192
  status: Draft
  category: Amendment
  created: 2026-09-04
  updated: 2026-09-08
</pre>

# Single Asset Vault Cash-Basis Accounting

## 1. Abstract

Under the `LendingProtocolV1_1` amendment, a Single Asset Vault accounts for the interest earned by its Loans on a cash basis. `AssetsTotal` counts interest only once a Borrower has paid it, rather than counting the interest a Loan is expected to earn from the moment the Loan is issued. The share exchange rate of the Vault therefore tracks the assets the Vault holds instead of the income it is owed, and a Borrower who stops paying costs the Vault only the principal it lent out. A Vault created before the amendment keeps accrual-basis accounting, in which `AssetsTotal` includes interest as it accrues, because changing the accounting model of an existing Vault would change the value of the shares it has already issued. Which model a Vault uses is recorded in its `LEVersion` field and fixed when the Vault is created.

## 2. Motivation

**Vault Cash-Basis Accounting.** Accrual-basis accounting credits a Vault with interest that a Borrower has not paid yet, so the share exchange rate reflects income the Vault has not received. A depositor can redeem shares at a rate inflated by interest that later defaults, and the loss falls on the depositors who remain. Cash-basis accounting removes that mismatch by recognising interest only when it is paid.

Existing Vaults cannot switch accounting models without changing the value of shares already issued, so the model has to be recorded per Vault rather than derived from the amendment state at the time of the transaction.

## 3. Specification

### 3.1 Ledger Entry: `Vault`

#### 3.1.1 Fields

| Field Name  | Constant | Required | Internal Type | Default Value | Description                                                                                                            |
| ----------- | :------: | :------: | :-----------: | :-----------: | ---------------------------------------------------------------------------------------------------------------------- |
| `LEVersion` |   Yes    |    No    |    `UINT8`    | absent (`0`)  | The accounting model the Vault applies to `AssetsTotal`. Absent is treated as `0` (accrual basis). Immutable once set. |

#### 3.1.2 `LEVersion`

`LEVersion` selects the accounting model of the Vault:

- `LEVersion` absent (treated as `0`, accrual basis): `AssetsTotal` includes the interest accrued over the life of the connected Loans. This is the pre-amendment behaviour and continues to apply to every Vault created before the amendment was enabled.
- `LEVersion = 1` (cash basis): `AssetsTotal` excludes uncollected interest and increases only as interest is collected in cash.

The field is written once by `VaultCreate` and is immutable after creation. A Vault created while the amendment is enabled is always cash-basis, and a Vault created before it is always accrual-basis; neither can be converted to the other.

#### 3.1.3 Invariants

- On an update to an existing Vault: `Vault.LEVersion == Vault'.LEVersion`.

#### 3.1.4 Partial Ledger Entry Example

The following excerpt shows the accounting fields introduced or affected by this patch; it is not a complete serialized `Vault` ledger entry:

```json
{
  "LedgerEntryType": "Vault",
  "LEVersion": 1,
  "Asset": {
    "currency": "USD",
    "issuer": "rf1BiGeXwwQoi8Z2ueFYTEXSwuJYfV2Jpn"
  },
  "AssetsTotal": "1000",
  "AssetsAvailable": "1000"
}
```

### 3.2 Transaction: `VaultCreate`

#### 3.2.1 Failure Conditions

No failure conditions related to cash-basis accounting are added or removed. `LEVersion` is not a transaction field and cannot be supplied by the submitter.

#### 3.2.2 State Changes

1. Create a new `Vault` ledger object, setting `Vault.LEVersion = 1`.

## 4. Rationale

**Vault Cash-Basis Accounting.** The alternative to a per-entry version field is to derive the accounting model from the amendment state at the time each Loan transaction executes. That was rejected because it would silently change the share exchange rate of every existing Vault on the ledger at the moment the amendment activates.

`LEVersion` is a version number rather than a boolean flag so that a later accounting change can be expressed as a further version without another field.

## 5. Security Considerations

**Vault Cash-Basis Accounting.** Cash-basis accounting reduces, but does not remove, the exposure of a depositor to an unpaid Loan: the Vault still carries the principal at face value until the Loan defaults or is impaired. `LossUnrealized` remains the mechanism for reporting an expected shortfall.

Because `LEVersion` is immutable, an implementation must read it from the `Vault` ledger entry rather than from the amendment state when computing the interest accounting of a Loan. Reading the amendment state instead would apply cash-basis rules to accrual-basis Vaults and misprice their shares.
