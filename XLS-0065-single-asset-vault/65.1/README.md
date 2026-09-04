<pre>
  xls: 65.1
  title: Immutable Vault Lifecycle Fields
  description: Extends the Vault immutability invariant to the lifecycle and version fields added by LendingProtocolV1_1
  author: Vytautas Vito Tumas <vtumas@ripple.com>, Aanchal Malhotra <amalhotra@ripple.com>
  proposal-from: https://github.com/XRPLF/XRPL-Standards/discussions/192
  status: Draft
  category: Amendment
  requires: [XLS-65](../README.md)
  created: 2026-09-04
  updated: 2026-09-04
</pre>

# Immutable Vault Lifecycle Fields

## 1. Abstract

This patch of [XLS-65](../README.md) records the change the `LendingProtocolV1_1` amendment makes to the invariants of the `Vault` ledger entry. The fields the amendment adds — `VaultKind`, `SubscriptionDate`, `RedemptionDate` and `LEVersion` — join `Asset`, `Account` and `ShareMPTID` as fields that no transaction may modify once the Vault exists.

The consolidated specification is the top-level [README.md](../README.md).

## 2. Motivation

The lifecycle fields describe the terms on which a depositor commits assets to the Vault, and the version field determines how the Vault values its shares. A transaction that changed either after subscription would change the terms retroactively: extending `RedemptionDate` would lengthen a lock-up that a depositor already accepted, and altering `LEVersion` would reprice every share in issue.

Stating this as a ledger invariant rather than as a rule of `VaultSet` means it holds for every transaction that touches the entry, including transactions added later.

## 3. Specification

### 3.1 Ledger Entry: `Vault`

#### 3.1.1 Fields

No fields are added or removed by this patch.

#### 3.1.2 Invariants

`Vault.Asset`, `Vault.Account` and `Vault.ShareMPTID` are immutable once set. When the amendment is enabled, `Vault.VaultKind`, `Vault.SubscriptionDate`, `Vault.RedemptionDate` and `Vault.LEVersion` are immutable once set as well:

- For an unmodifiable field `f`: `IF <vault>.f exists THEN <vault>'.f == <vault>.f`.
- An unmodifiable field that is absent before the transaction remains absent after it, except when the transaction creates the entry.

Before the amendment the four additional fields are never written, so their immutability has no effect on entries created earlier.

#### 3.1.3 Example JSON

```json
{
  "LedgerEntryType": "Vault",
  "LEVersion": 1,
  "VaultKind": 1,
  "SubscriptionDate": 800000000,
  "RedemptionDate": 830000000,
  "Asset": { "currency": "USD", "issuer": "rf1BiGeXwwQoi8Z2ueFYTEXSwuJYfV2Jpn" },
  "Account": "rHXuEaRYnnJHbDeuBH5w8yPh5uwNVh5zAg"
}
```

## 4. Rationale

Enforcing immutability in an invariant check, rather than only in the transactors that write the entry, is the conservative choice: a transactor can be added or changed without the guarantee being revisited, and an invariant failure is reported rather than silently accepted.

Treating the fields as immutable rather than mutable-with-conditions was chosen over allowing, for instance, a `RedemptionDate` to be brought forward. Any conditional rule needs a notion of consent from depositors, which the Vault has no way to express.

## 5. Security Considerations

The invariant is what allows a reader to cache the kind, the dates and the version of a Vault. Without it, every consumer would have to re-read the entry before valuing shares.

An implementation that adds a field to the `Vault` entry should decide explicitly whether it belongs in the unmodifiable set. A field that is left out is mutable by default, which is the less safe of the two outcomes.
