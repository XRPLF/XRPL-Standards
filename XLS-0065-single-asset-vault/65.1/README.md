<pre>
  xls: 65.1
  title: Unmodifiable Vault Fields
  description: Makes Sequence, OwnerNode, Owner, WithdrawalPolicy, Scale and LEVersion immutable on the Vault once set
  author: Vytautas Vito Tumas <vtumas@ripple.com>
  proposal-from: https://github.com/XRPLF/XRPL-Standards/discussions/192
  status: Draft
  category: Amendment
  created: 2026-09-04
  updated: 2026-09-08
</pre>

# Unmodifiable Vault Fields

## 1. Abstract

Under the `LendingProtocolV1_1` amendment, `Sequence`, `OwnerNode`, `Owner`, `WithdrawalPolicy`, `Scale` and `LEVersion` are immutable on a `Vault` once set, in addition to `Asset`, `Account` and `ShareMPTID`.

## 2. Motivation

The version field determines how the Vault values its shares. Changing `LEVersion` after creation would reprice every share in issue.

The identity and configuration fields are in the same position. `Sequence` and `OwnerNode` locate the entry and its directory page, `Owner` names the account that controls it, and `WithdrawalPolicy` and `Scale` fix how shares are redeemed and how finely the asset is denominated. None of them has a legitimate reason to change after creation.

Stating this as a ledger invariant means it holds for every transaction that touches the entry.

## 3. Specification

### 3.1 Ledger Entry: `Vault`

#### 3.1.1 Invariants

Before the amendment: `Vault.Asset == Vault'.Asset`, `Vault.Account == Vault'.Account`, and `Vault.ShareMPTID == Vault'.ShareMPTID`.

When the amendment is enabled: `Vault.Sequence == Vault'.Sequence`, `Vault.OwnerNode == Vault'.OwnerNode`, `Vault.Owner == Vault'.Owner`, `Vault.WithdrawalPolicy == Vault'.WithdrawalPolicy`, `Vault.Scale == Vault'.Scale`, `Vault.Asset == Vault'.Asset`, `Vault.Account == Vault'.Account`, and `Vault.ShareMPTID == Vault'.ShareMPTID`. If `Vault.LEVersion` is present, `Vault.LEVersion == Vault'.LEVersion`; if it is absent, it remains absent, except when the transaction creates the entry.

#### 3.1.2 Example JSON

```json
{
  "LedgerEntryType": "Vault",
  "Sequence": 5,
  "OwnerNode": "0",
  "Owner": "rwhaYGnJMexktjhxAKzRwoCcQ2g6hvBDWu",
  "WithdrawalPolicy": 1,
  "Scale": 6,
  "LEVersion": 1,
  "Asset": {
    "currency": "USD",
    "issuer": "rf1BiGeXwwQoi8Z2ueFYTEXSwuJYfV2Jpn"
  },
  "Account": "rHXuEaRYnnJHbDeuBH5w8yPh5uwNVh5zAg",
  "ShareMPTID": "00000001C752C42A1EBD6BF2403134F7CFD2F1D835AFD26E"
}
```

## 4. Rationale

Treating these fields as immutable rather than mutable-with-conditions avoids introducing transaction-specific exceptions into a ledger-wide invariant.

## 5. Security Considerations

The invariant is what allows a reader to cache the version and denomination of a Vault. Without it, every consumer would have to re-read the entry before valuing shares.

A field added to the `Vault` later is mutable unless it is included in this set.
