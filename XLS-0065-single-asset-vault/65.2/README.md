<pre>
  xls: 65.2
  title: VaultClawback Failure Conditions
  description: Rejects a pseudo-account Holder and reports VaultClawback precision loss as an explicit failure
  author: Vytautas Vito Tumas <vtumas@ripple.com>
  proposal-from: https://github.com/XRPLF/XRPL-Standards/discussions/192
  status: Draft
  category: Amendment
  created: 2026-09-04
  updated: 2026-09-04
</pre>

# VaultClawback Failure Conditions

## 1. Abstract

Under the `fixCleanup3_4_0` amendment, `VaultClawback` rejects a `Holder` that is a pseudo-account, and an asset clawback that would recover a non-zero amount too small to change stored `AssetsTotal` fails with `tecPRECISION_LOSS` rather than `tecINVARIANT_FAILED`.

## 2. Motivation

**VaultClawback Failure Conditions.** A pseudo-account holds shares on behalf of a protocol, not on behalf of a person, and it has no key that can act for it. Clawing shares back from one removes the backing of whatever the protocol accounted for, and leaves an entry that the protocol did not write and cannot reconcile. The transaction has no correct outcome in that case, so it should not be applied.

`AssetsTotal` is stored at the scale of the Vault asset, so a clawback smaller than one unit at that scale can tentatively burn shares while leaving the stored total unchanged. Before the amendment that inconsistent state is rejected as `tecINVARIANT_FAILED`. Reporting it as `tecPRECISION_LOSS` gives the submitter the specific cause.

## 3. Specification

### 3.1 Transaction: `VaultClawback`

#### 3.1.1 Failure Conditions

##### 3.1.1.1 Protocol-Level Failures

2.  - Before the amendment: the check does not apply. A `Holder` that is a pseudo-account is not rejected for that reason.
    - When the amendment is enabled: `Holder` is a pseudo-account. (`tecPSEUDO_ACCOUNT`)

3.  - Before the amendment: a computed non-zero recovery that rounds to zero at the scale of `AssetsTotal` is not reported here; an inconsistent tentative state fails later as `tecINVARIANT_FAILED`.
    - When the amendment is enabled: for an asset clawback, a computed non-zero recovered asset amount rounds down to zero at the scale of the resulting `AssetsTotal`. (`tecPRECISION_LOSS`)

4.  - Before the amendment: a computed non-zero recovery that does not change stored `AssetsTotal` fails as `tecINVARIANT_FAILED`.
    - When the amendment is enabled: for an asset clawback, the computed non-zero recovered asset amount would not change stored `AssetsTotal`. (`tecPRECISION_LOSS`)

5.  - Before the amendment: the check does not apply.
    - When the amendment is enabled: for an asset clawback, arithmetic overflows while evaluating the preceding non-zero recovery. (`tecPATH_DRY`)

Parent checks 1, 3–7, and 9 are unchanged.

## 4. Rationale

**VaultClawback Failure Conditions.** `tecPSEUDO_ACCOUNT` is used rather than `tecNO_PERMISSION` because the reason for the failure is what the account is, not who submitted the transaction. The submitter cannot obtain permission by any means.

The dust condition is reported as `tecPRECISION_LOSS` rather than silently rounded up to one unit. Rounding up would take more from the Holder than the transaction asked for; rounding down is the no-op the amendment is removing.

Overflow is reported as `tecPATH_DRY` for consistency with the other arithmetic failures of the Vault transactions, rather than introducing a new code for a condition that a submitter cannot distinguish in practice.

## 5. Security Considerations

**VaultClawback Failure Conditions.** Rejecting a pseudo-account `Holder` protects an invariant of the protocol that owns the pseudo-account: its accounting assumes that shares it holds are removed only by transactions it issues.

The dust check makes an expected input-dependent failure explicit as `tecPRECISION_LOSS`. The same tentative state was already uncommittable; only the error reported to the submitter changes.
