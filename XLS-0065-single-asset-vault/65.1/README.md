<pre>
  xls: 65.1
  title: Unmodifiable Vault Fields
  description: Moves the Vault immutability check into the generic unmodifiable-fields invariant and widens the unmodifiable field set
  author: Vytautas Vito Tumas <vtumas@ripple.com>, Aanchal Malhotra <amalhotra@ripple.com>
  proposal-from: https://github.com/XRPLF/XRPL-Standards/discussions/192
  status: Draft
  category: Amendment
  requires: [XLS-65](../README.md)
  created: 2026-09-04
  updated: 2026-09-04
</pre>

# Unmodifiable Vault Fields

## 1. Abstract

This patch of [XLS-65](../README.md) records the change the `LendingProtocolV1_1` amendment makes to the invariants of the `Vault` ledger entry. The amendment moves the immutability check out of the Vault-specific invariant and into the generic unmodifiable-fields invariant, and in doing so widens the set from `Asset`, `Account` and `ShareMPTID` to also cover `Sequence`, `OwnerNode`, `Owner`, `WithdrawalPolicy`, `Scale`, `LEVersion`, `VaultKind`, `SubscriptionDate` and `RedemptionDate`.

The consolidated specification is the top-level [README.md](../README.md).

## 2. Motivation

The lifecycle fields describe the terms on which a depositor commits assets to the Vault, and the version field determines how the Vault values its shares. A transaction that changed either after subscription would change the terms retroactively: extending `RedemptionDate` would lengthen a lock-up that a depositor already accepted, and altering `LEVersion` would reprice every share in issue.

The identity and configuration fields are in the same position. `Sequence` and `OwnerNode` locate the entry and its directory page, `Owner` names the account that controls it, and `WithdrawalPolicy` and `Scale` fix how shares are redeemed and how finely the asset is denominated. None of them has a legitimate reason to change after creation, and each was mutable by default before the amendment simply because nothing checked it.

Stating this as a ledger invariant rather than as a rule of `VaultSet` means it holds for every transaction that touches the entry, including transactions added later.

## 3. Specification

### 3.1 Ledger Entry: `Vault`

#### 3.1.1 Fields

No fields are added or removed by this patch.

#### 3.1.2 Invariants

Before the amendment, the unmodifiable set of the `Vault` entry is `Asset`, `Account` and `ShareMPTID`, enforced by the Vault-specific invariant. When the amendment is enabled the check is performed by the generic unmodifiable-fields invariant and the set is:

| Field              | Present before `LendingProtocolV1_1` |
| ------------------ | ------------------------------------ |
| `Sequence`         | Yes                                  |
| `OwnerNode`        | Yes                                  |
| `Owner`            | Yes                                  |
| `WithdrawalPolicy` | Yes                                  |
| `Scale`            | Yes                                  |
| `LEVersion`        | No                                   |
| `VaultKind`        | No                                   |
| `SubscriptionDate` | No                                   |
| `RedemptionDate`   | No                                   |
| `Asset`            | Yes                                  |
| `Account`          | Yes                                  |
| `ShareMPTID`       | Yes                                  |

The rule applied to each field of that set is:

- For an unmodifiable field `f`: `IF <vault>.f exists THEN <vault>'.f == <vault>.f`.
- An unmodifiable field that is absent before the transaction remains absent after it, except when the transaction creates the entry.

`LedgerEntryType` and `LedgerIndex` are unmodifiable for every ledger entry type, not only the `Vault`, and are checked independently of this amendment.

Before the amendment the four lifecycle and version fields are never written, so their immutability has no effect on entries created earlier. The remaining fields were already written at creation and never changed by any transactor, so extending the set records an existing property rather than restricting behaviour that was previously permitted.

#### 3.1.3 Example JSON

```json
{
  "LedgerEntryType": "Vault",
  "Sequence": 5,
  "OwnerNode": "0",
  "Owner": "rwhaYGnJMexktjhxAKzRwoCcQ2g6hvBDWu",
  "WithdrawalPolicy": 1,
  "Scale": 6,
  "LEVersion": 1,
  "VaultKind": 1,
  "SubscriptionDate": 800000000,
  "RedemptionDate": 830000000,
  "Asset": { "currency": "USD", "issuer": "rf1BiGeXwwQoi8Z2ueFYTEXSwuJYfV2Jpn" },
  "Account": "rHXuEaRYnnJHbDeuBH5w8yPh5uwNVh5zAg",
  "ShareMPTID": "00000001C752C42A1EBD6BF2403134F7CFD2F1D835AFD26E"
}
```

## 4. Rationale

Enforcing immutability in an invariant check, rather than only in the transactors that write the entry, is the conservative choice: a transactor can be added or changed without the guarantee being revisited, and an invariant failure is reported rather than silently accepted.

Treating the fields as immutable rather than mutable-with-conditions was chosen over allowing, for instance, a `RedemptionDate` to be brought forward. Any conditional rule needs a notion of consent from depositors, which the Vault has no way to express.

## 5. Security Considerations

The invariant is what allows a reader to cache the kind, the dates, the version and the denomination of a Vault. Without it, every consumer would have to re-read the entry before valuing shares.

An implementation that adds a field to the `Vault` entry should decide explicitly whether it belongs in the unmodifiable set. A field that is left out is mutable by default, which is the less safe of the two outcomes.
