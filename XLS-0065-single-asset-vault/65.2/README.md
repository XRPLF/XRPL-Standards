<pre>
  xls: 65.2
  title: VaultClawback Failure Conditions
  description: Rejects a pseudo-account holder and adds precision and overflow checks to VaultClawback
  author: Vytautas Vito Tumas <vtumas@ripple.com>, Aanchal Malhotra <amalhotra@ripple.com>
  proposal-from: https://github.com/XRPLF/XRPL-Standards/discussions/192
  status: Draft
  category: Amendment
  requires: [XLS-65](../README.md)
  created: 2026-09-04
  updated: 2026-09-04
</pre>

# VaultClawback Failure Conditions

## 1. Abstract

This patch of [XLS-65](../README.md) records the changes the `fixCleanup3_4_0` amendment makes to the `VaultClawback` transaction. A `Holder` that is a pseudo-account is rejected. A clawback of an amount too small to change the stored assets of the Vault is rejected instead of succeeding with no effect, and an overflow while evaluating that condition is reported rather than propagated.

The consolidated specification is the top-level [README.md](../README.md).

## 2. Motivation

A pseudo-account holds shares on behalf of a protocol, not on behalf of a person, and it has no key that can act for it. Clawing shares back from one removes the backing of whatever the protocol accounted for, and leaves an entry that the protocol did not write and cannot reconcile. The transaction has no correct outcome in that case, so it should not be applied.

The precision case is a silent no-op. `AssetsTotal` is stored at the scale of the Vault asset, so a clawback smaller than one unit at that scale burns shares while leaving the stored total unchanged, which moves value between the remaining holders. Reporting it as a precision failure tells the submitter that the amount was too small, rather than reporting success for a transaction that did nothing it was asked to do.

## 3. Specification

### 3.1 Transaction: `VaultClawback`

#### 3.1.1 Fields

No fields are added or removed.

#### 3.1.2 Failure Conditions

##### 3.1.2.1 Protocol-Level Failures

The following are added, in the order in which they are evaluated:

1. The `Holder` is a pseudo-account. (`tecPSEUDO_ACCOUNT`)
2. The computed clawback is non-zero dust that would not change the stored `Vault.AssetsTotal`. (`tecPRECISION_LOSS`)
3. Arithmetic overflow while evaluating the preceding condition. (`tecPATH_DRY`)

The existing failures are unchanged and continue to apply:

- `Vault.Asset` is not XRP, the issuer of `Vault.Asset` is the Owner of the Vault, and no `Amount` is given, so the target of the clawback is ambiguous. (`tecWRONG_ASSET`)
- The unit of `Amount` is neither the Vault share nor `Vault.Asset`. (`tecWRONG_ASSET`)
- The computed number of shares to destroy is zero. (`tecPRECISION_LOSS`)

Before the amendment, a pseudo-account `Holder` is accepted, and a dust clawback succeeds without changing the stored assets of the Vault.

#### 3.1.3 State Changes

Unchanged. The patch adds failure conditions; it does not change the effect of a transaction that succeeds.

#### 3.1.4 Example JSON

```json
{
  "TransactionType": "VaultClawback",
  "Account": "rf1BiGeXwwQoi8Z2ueFYTEXSwuJYfV2Jpn",
  "Fee": "10",
  "Sequence": 12345,
  "VaultID": "9CD5F03A9D0F4F7C0B8B4C5F5A4D3E2B1A0F9E8D7C6B5A493827160504030201",
  "Holder": "rHXuEaRYnnJHbDeuBH5w8yPh5uwNVh5zAg",
  "Amount": "100"
}
```

## 4. Rationale

`tecPSEUDO_ACCOUNT` is used rather than `tecNO_PERMISSION` because the reason for the failure is what the account is, not who submitted the transaction. The submitter cannot obtain permission by any means, and the code says so.

The dust condition is reported as `tecPRECISION_LOSS` rather than silently rounded up to one unit. Rounding up would take more from the Holder than the transaction asked for; rounding down is the no-op the amendment is removing.

Overflow is reported as `tecPATH_DRY` for consistency with the other arithmetic failures of the Vault transactions, rather than introducing a new code for a condition that a submitter cannot distinguish in practice.

## 5. Security Considerations

The dust check closes a path by which repeated small clawbacks burn shares without reducing the assets of the Vault, which raises the exchange rate for the remaining holders at the expense of the Holder being clawed back.

Rejecting a pseudo-account `Holder` protects an invariant of the protocol that owns the pseudo-account: its accounting assumes that shares it holds are removed only by transactions it issues.

The additional checks are gated on the amendment, so nodes disagree about the outcome of an affected transaction until it activates. This is the ordinary consequence of amendment gating and is why the checks are not applied unconditionally.
