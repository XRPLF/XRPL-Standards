<pre>
  xls: 65.1
  title: Closed-Ended Vault Lifecycle
  description: Adds the optional VaultKind, SubscriptionDate and RedemptionDate fields, which give a Vault a fixed subscription and redemption window
  author: Vytautas Vito Tumas <vtumas@ripple.com>, Aanchal Malhotra <amalhotra@ripple.com>
  proposal-from: https://github.com/XRPLF/XRPL-Standards/discussions/192
  status: Draft
  category: Amendment
  requires: [XLS-65](../README.md)
  created: 2026-09-04
  updated: 2026-09-04
</pre>

# Closed-Ended Vault Lifecycle

## 1. Abstract

This patch of [XLS-65](../README.md) records the changes the `LendingProtocolV1_1` amendment makes to `VaultCreate` and to the `Vault` ledger entry. The amendment adds an optional kind to a Vault. An open-ended Vault behaves as before and accepts deposits and withdrawals at any time. A closed-ended Vault carries a subscription time and a redemption time, which bound the period over which its assets are committed. The amendment also records the accounting model of the Vault in `LEVersion`.

The consolidated specification is the top-level [README.md](../README.md).

## 2. Motivation

A Vault that funds fixed-term Loans cannot honour an unbounded right of withdrawal: the assets are committed for the term of the Loan, so a redemption early in that term is paid out of the deposits of others rather than out of returned principal. A closed-ended Vault makes that commitment explicit by fixing when subscriptions and redemptions happen, which is what allows the Lending Protocol to attach a Loan Broker to it.

The kind and its dates have to be immutable, because a depositor subscribes on the strength of the redemption time. Making them mutable would let the Owner extend the lock-up after the fact.

## 3. Specification

### 3.1 Ledger Entry: `Vault`

#### 3.1.1 Fields

| Field Name         | Constant | Required | Internal Type | Default Value | Description                                                                                             |
| ------------------ | :------: | :------: | :-----------: | :-----------: | ------------------------------------------------------------------------------------------------------- |
| `LEVersion`        |   Yes    |    No    |    `UINT8`    | absent (`0`)  | Protocol-written schema version of the Vault. Absent or `0` is legacy; `1` is cash-basis accounting.     |
| `VaultKind`        |   Yes    |    No    |    `UINT8`    |    absent     | Kind of the Vault. Absent means `OpenEnded` (`0`); `ClosedEnded` is `1`.                                 |
| `SubscriptionDate` |   Yes    |    No    |   `UINT32`    |    absent     | Closed-ended Vault only: start of the investment window, in ledger time.                                 |
| `RedemptionDate`   |   Yes    |    No    |   `UINT32`    |    absent     | Closed-ended Vault only: start of the redemption window, in ledger time.                                 |

`LEVersion` is written by the protocol and is not a transaction field. The three lifecycle fields are absent on an open-ended Vault.

#### 3.1.2 Invariants

- `Vault.VaultKind`, `Vault.SubscriptionDate`, `Vault.RedemptionDate` and `Vault.LEVersion` are immutable once set.
- `Vault.SubscriptionDate` and `Vault.RedemptionDate` are present if and only if `Vault.VaultKind == 1`.

#### 3.1.3 Example JSON

```json
{
  "LedgerEntryType": "Vault",
  "LEVersion": 1,
  "VaultKind": 1,
  "SubscriptionDate": 800000000,
  "RedemptionDate": 830000000,
  "Asset": { "currency": "USD", "issuer": "rf1BiGeXwwQoi8Z2ueFYTEXSwuJYfV2Jpn" },
  "AssetsTotal": "1000",
  "AssetsAvailable": "1000"
}
```

### 3.2 Transaction: `VaultCreate`

#### 3.2.1 Fields

| Field Name         | Required? | JSON Type | Internal Type | Default Value | Description                                                             |
| ------------------ | :-------: | :-------: | :-----------: | :-----------: | ----------------------------------------------------------------------- |
| `VaultKind`        |    No     | `number`  |    `UINT8`    |    absent     | Kind of the Vault: `0` (`OpenEnded`) or `1` (`ClosedEnded`).             |
| `SubscriptionDate` |    No     | `number`  |   `UINT32`    |    absent     | Start of the investment window of a closed-ended Vault, in ledger time. |
| `RedemptionDate`   |    No     | `number`  |   `UINT32`    |    absent     | Start of the redemption window of a closed-ended Vault, in ledger time. |

All three fields require the amendment. If any of them is present while the amendment is disabled, the transaction is rejected in preflight with `temDISABLED`.

#### 3.2.2 Failure Conditions

##### 3.2.2.1 Data Verification

1. Any of `VaultKind`, `SubscriptionDate`, or `RedemptionDate` is present while `LendingProtocolV1_1` is disabled. (`temDISABLED`)
2. `VaultKind` is present and is neither `0` nor `1`. (`temMALFORMED`)
3. The Vault is open-ended, that is `VaultKind` is absent or `0`, and `SubscriptionDate` or `RedemptionDate` is present. (`temMALFORMED`)
4. The Vault is closed-ended and `SubscriptionDate` or `RedemptionDate` is missing. (`temMALFORMED`)
5. The Vault is closed-ended and the window does not satisfy `RedemptionDate >= SubscriptionDate + 180` and `RedemptionDate < SubscriptionDate + kMaxInvestmentPeriod`, where `kMaxInvestmentPeriod` is thirty Gregorian years in seconds. (`temMALFORMED`)

##### 3.2.2.2 Protocol-Level Failures

1. `parentCloseTime >= SubscriptionDate` or `parentCloseTime >= RedemptionDate`. The comparison is inclusive: the date has expired at the parent ledger close time, not only after it. (`tecEXPIRED`)

Data verification already requires `RedemptionDate >= SubscriptionDate + 180` for a closed-ended Vault, so an expired `RedemptionDate` implies an expired `SubscriptionDate`.

#### 3.2.3 State Changes

When the amendment is enabled, creating a Vault additionally:

1. Sets `Vault.LEVersion` to `1`.
2. Sets `Vault.VaultKind` from the transaction, defaulting to `OpenEnded` when the field is absent.
3. Writes `Vault.SubscriptionDate` and `Vault.RedemptionDate` from the transaction when the kind is `ClosedEnded`.

#### 3.2.4 Example JSON

```json
{
  "TransactionType": "VaultCreate",
  "Account": "rf1BiGeXwwQoi8Z2ueFYTEXSwuJYfV2Jpn",
  "Fee": "10",
  "Sequence": 12345,
  "Asset": { "currency": "USD", "issuer": "rf1BiGeXwwQoi8Z2ueFYTEXSwuJYfV2Jpn" },
  "VaultKind": 1,
  "SubscriptionDate": 800000000,
  "RedemptionDate": 830000000
}
```

## 4. Rationale

The kind is a numeric field rather than a flag so that a further lifecycle can be added without consuming another flag bit and without a combination of flags that has no meaning.

The minimum window of 180 seconds is a guard against a degenerate Vault whose subscription and redemption windows are effectively the same instant, not an economically meaningful term. The maximum of thirty years bounds the field to a range that ledger time can express without wrapping.

Rejecting the lifecycle fields on an open-ended Vault, rather than ignoring them, keeps the ledger entry unambiguous: a reader never has to decide whether a date on an open-ended Vault means anything.

## 5. Security Considerations

`tecEXPIRED` is evaluated against the parent ledger close time and is inclusive: the transaction fails when `parentCloseTime >= SubscriptionDate` or `parentCloseTime >= RedemptionDate`. A submitter who sets a `SubscriptionDate` equal to the current parent close time should expect `tecEXPIRED`, and should not treat the check as a guarantee that the window is still open when the Vault is created.

Because the lifecycle fields are immutable, an Owner cannot rescue a Vault created with the wrong dates. The remedy is to delete the Vault and create a new one, which is only possible while the Vault holds no assets.
