<pre>
  xls: 65.1
  title: Single Asset Vault under LendingProtocolV1_1
  description: Records the changes the LendingProtocolV1_1 amendment makes to XLS-65
  author: Vytautas Vito Tumas <vtumas@ripple.com>, Aanchal Malhotra <amalhotra@ripple.com>
  proposal-from: https://github.com/XRPLF/XRPL-Standards/discussions/192
  status: Draft
  category: Amendment
  requires: [XLS-65](../README.md)
  created: 2026-09-04
  updated: 2026-09-08
</pre>

# Single Asset Vault under `LendingProtocolV1_1`

## 1. Abstract

This patch of [XLS-65](../README.md) records the changes the `LendingProtocolV1_1` amendment makes to the Single Asset Vault. The amendment is not yet live. The consolidated specification is the top-level [README.md](../README.md).

The amendment makes the following changes to XLS-65:

- **Unmodifiable Vault Fields** — Moves the immutability check out of the Vault-specific invariant and into the generic unmodifiable-fields invariant, and in doing so widens the set from `Asset`, `Account` and `ShareMPTID` to also cover `Sequence`, `OwnerNode`, `Owner`, `WithdrawalPolicy`, `Scale` and `LEVersion`.

## 2. Motivation

**Unmodifiable Vault Fields.** The version field determines how the Vault values its shares. A transaction that altered `LEVersion` would reprice every share in issue.

The identity and configuration fields are in the same position. `Sequence` and `OwnerNode` locate the entry and its directory page, `Owner` names the account that controls it, and `WithdrawalPolicy` and `Scale` fix how shares are redeemed and how finely the asset is denominated. None of them has a legitimate reason to change after creation, and each was mutable by default before the amendment simply because nothing checked it.

Stating this as a ledger invariant rather than as a rule of `VaultSet` means it holds for every transaction that touches the entry, including transactions added later.

## 3. Specification

### 3.1 Unmodifiable Vault Fields

#### 3.1.1 Ledger Entry: `Vault`

##### 3.1.1.1 Fields

This patch does not add or remove `Vault` fields. `LEVersion` is absent on entries created before `LendingProtocolV1_1`. This document records only the invariant check that applies once the field exists.

##### 3.1.1.2 Invariants

Before the amendment, the unmodifiable set of the `Vault` entry is `Asset`, `Account` and `ShareMPTID`, enforced by the Vault-specific invariant. When the amendment is enabled the check is performed by the generic unmodifiable-fields invariant and the set is:

| Field              | Present before `LendingProtocolV1_1` |
| ------------------ | ------------------------------------ |
| `Sequence`         | Yes                                  |
| `OwnerNode`        | Yes                                  |
| `Owner`            | Yes                                  |
| `WithdrawalPolicy` | Yes                                  |
| `Scale`            | Yes                                  |
| `LEVersion`        | No                                   |
| `Asset`            | Yes                                  |
| `Account`          | Yes                                  |
| `ShareMPTID`       | Yes                                  |

The rule applied to each field of that set is:

- For an unmodifiable field `f`: `IF <vault>.f exists THEN <vault>'.f == <vault>.f`.
- An unmodifiable field that is absent before the transaction remains absent after it, except when the transaction creates the entry.

`LedgerEntryType` and `LedgerIndex` are unmodifiable for every ledger entry type, not only the `Vault`, and are checked independently of this amendment.

Before the amendment `LEVersion` is never written, so its immutability has no effect on entries created earlier. The remaining fields were already written at creation and never changed by any transactor, so extending the set records an existing property rather than restricting behaviour that was previously permitted.

##### 3.1.1.3 Example JSON

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

**Unmodifiable Vault Fields.** Enforcing immutability in an invariant check, rather than only in the transactors that write the entry, is the conservative choice: a transactor can be added or changed without the guarantee being revisited, and an invariant failure is reported rather than silently accepted.

Treating these fields as immutable rather than mutable-with-conditions avoids introducing transaction-specific exceptions into a ledger-wide invariant.

## 5. Security Considerations

**Unmodifiable Vault Fields.** The invariant is what allows a reader to cache the version and denomination of a Vault. Without it, every consumer would have to re-read the entry before valuing shares.

An implementation that adds a field to the `Vault` entry should decide explicitly whether it belongs in the unmodifiable set. A field that is left out is mutable by default, which is the less safe of the two outcomes.
