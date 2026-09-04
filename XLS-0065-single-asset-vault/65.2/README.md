<pre>
  xls: 65.2
  title: VaultClawback Failure Conditions
  description: Corrects holder validation, conversion, precision, and overflow handling in VaultClawback
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

This patch of [XLS-65](../README.md) records the changes the `fixCleanup3_4_0` amendment makes to the `VaultClawback` transaction. It rejects a pseudo-account `Holder`, corrects share conversion for explicit amounts and sole shareholders, aligns recovered assets with the stored total's scale, and rejects precision loss instead of allowing a share burn with no corresponding asset change.

The consolidated specification is the top-level [README.md](../README.md).

## 2. Motivation

A pseudo-account holds shares on behalf of a protocol, not on behalf of a person, and it has no key that can act for it. Clawing shares back from one removes the backing of whatever the protocol accounted for, and leaves an entry that the protocol did not write and cannot reconcile. The transaction has no correct outcome in that case, so it should not be applied.

The precision case is a silent no-op. `AssetsTotal` is stored at the scale of the Vault asset, so a clawback smaller than one unit at that scale burns shares while leaving the stored total unchanged, which moves value between the remaining holders. Reporting it as a precision failure tells the submitter that the amount was too small, rather than reporting success for a transaction that did nothing it was asked to do.

## 3. Specification

### 3.1 Transaction: `VaultClawback`

#### 3.1.1 Fields

No fields are added or removed. The existing fields relevant to this patch are:

| Field Name | Required | JSON Type | Internal Type | Default Value | Description |
| ---------- | :------: | :-------: | :-----------: | :-----------: | ----------- |
| `VaultID` | Yes | `string` | `HASH256` | `N/A` | The ID of the Vault. |
| `Holder` | Yes | `string` | `AccountID` | `N/A` | The account whose Vault shares are destroyed. |
| `Amount` | No | `string` or `object` | `STAmount` | Implicit zero | The Vault asset or Vault share amount to claw back. |

If `Amount` is omitted, the implementation constructs a zero-valued `STAmount` denominated in the Vault share MPT when the submitter is `Vault.Owner`, and in `Vault.Asset` otherwise. The zero amount means all value represented by the `Holder`'s shares. If the Vault Owner is also the issuer of a non-XRP `Vault.Asset`, `Amount` must be explicit to select between a share burn and an asset clawback.

#### 3.1.2 Failure Conditions

##### 3.1.2.1 Protocol-Level Failures

After data verification, failures are evaluated in these phases and in this order:

1. The `Vault` object does not exist. (`tecNO_ENTRY`)
2. If `fixCleanup3_4_0` is enabled, `Holder` is a pseudo-account. (`tecPSEUDO_ACCOUNT`)
3. `Vault.Asset` is not XRP, its issuer is `Vault.Owner`, and `Amount` is omitted, making the branch ambiguous. (`tecWRONG_ASSET`)
4. If `Amount` is denominated in the Vault share MPT:
   1. The submitter is not `Vault.Owner`. (`tecNO_PERMISSION`)
   2. `OutstandingAmount == 0`, `AssetsTotal != 0`, or `AssetsAvailable != 0`. (`tecNO_PERMISSION`)
   3. `Amount` is non-zero and does not equal all shares held by `Holder`. (`tecLIMIT_EXCEEDED`)
5. If `Amount` is denominated in `Vault.Asset`:
   1. `Vault.Asset` is XRP. (`tecNO_PERMISSION`)
   2. The submitter is not the asset issuer. (`tecNO_PERMISSION`)
   3. `Holder` is the submitter. (`tecNO_PERMISSION`)
   4. For an MPT asset, its `MPTokenIssuance` does not exist. (`tecOBJECT_NOT_FOUND`)
   5. For an MPT asset, `lsfMPTCanClawback` is not set. (`tecNO_PERMISSION`)
   6. For an IOU asset, `lsfAllowTrustLineClawback` is not set or `lsfNoFreeze` is set on the issuer. (`tecNO_PERMISSION`)
6. The unit of `Amount` is neither the Vault share MPT nor `Vault.Asset`. (`tecWRONG_ASSET`)
7. During an asset clawback, arithmetic overflows while `assetsToClawback` computes `assetsRecovered` and `sharesDestroyed`. This check is not gated on `fixCleanup3_4_0`. (`tecPATH_DRY`)
8. The computed `sharesDestroyed` is zero. This check is not gated on `fixCleanup3_4_0`. (`tecPRECISION_LOSS`)
9. During an asset clawback with `fixCleanup3_4_0` enabled, the computed non-zero `assetsRecovered` would not change stored `AssetsTotal`. (`tecPRECISION_LOSS`)
10. During an asset clawback with `fixCleanup3_4_0` enabled, arithmetic overflows while evaluating the preceding non-zero-dust condition. (`tecPATH_DRY`)

Before the amendment, a pseudo-account `Holder` is accepted, and a dust clawback succeeds without changing the stored assets of the Vault.

#### 3.1.3 State Changes

The ledger objects changed by a successful transaction are unchanged, but `fixCleanup3_4_0` changes how a successful asset clawback computes the shares destroyed and assets recovered:

1. For an explicit non-zero `Amount`, `assetsToSharesWithdraw` uses `TruncateShares::Yes`. Because shares are integral, truncation ensures that converting the resulting shares back to assets does not recover more than the requested amount.
2. If `Holder` owns the entire outstanding share supply, both conversion directions use `WaiveUnrealizedLoss::Yes`. The exchange-rate numerator is therefore `AssetsTotal`, not `AssetsTotal - LossUnrealized`; for an implicit zero amount, `sharesDestroyed` is read directly from `OutstandingAmount`.
3. If the computed `assetsRecovered` is non-zero, it is passed to `clampToAssetsTotalScale` as a negative Vault delta. Integral assets pass through unchanged. For a non-integral asset, the helper determines the scale of the posterior `AssetsTotal` using nearest rounding and rounds the recovery magnitude downward to that scale. It does not recompute `sharesDestroyed`, so any trimmed sub-unit residue stays in the Vault for the remaining shareholders.

After those calculations, the transaction destroys `sharesDestroyed` shares, decreases `OutstandingAmount` by the same amount, decreases `AssetsTotal` and `AssetsAvailable` by `assetsRecovered`, and transfers `assetsRecovered` from the Vault pseudo-account to the asset issuer. A stranded-share burn by the Vault Owner destroys shares without changing or transferring Vault assets.

#### 3.1.4 Example JSON

```json
{
  "TransactionType": "VaultClawback",
  "Account": "rf1BiGeXwwQoi8Z2ueFYTEXSwuJYfV2Jpn",
  "Fee": "10",
  "Sequence": 12345,
  "VaultID": "9CD5F03A9D0F4F7C0B8B4C5F5A4D3E2B1A0F9E8D7C6B5A493827160504030201",
  "Holder": "rHXuEaRYnnJHbDeuBH5w8yPh5uwNVh5zAg",
  "Amount": {
    "currency": "USD",
    "issuer": "rf1BiGeXwwQoi8Z2ueFYTEXSwuJYfV2Jpn",
    "value": "100"
  }
}
```

## 4. Rationale

`tecPSEUDO_ACCOUNT` is used rather than `tecNO_PERMISSION` because the reason for the failure is what the account is, not who submitted the transaction. The submitter cannot obtain permission by any means, and the code says so.

The dust condition is reported as `tecPRECISION_LOSS` rather than silently rounded up to one unit. Rounding up would take more from the Holder than the transaction asked for; rounding down is the no-op the amendment is removing.

Overflow is reported as `tecPATH_DRY` for consistency with the other arithmetic failures of the Vault transactions, rather than introducing a new code for a condition that a submitter cannot distinguish in practice.

## 5. Security Considerations

The dust check closes a path by which repeated small clawbacks burn shares without reducing the assets of the Vault, which raises the exchange rate for the remaining holders at the expense of the Holder being clawed back.

Rejecting a pseudo-account `Holder` protects an invariant of the protocol that owns the pseudo-account: its accounting assumes that shares it holds are removed only by transactions it issues.

The pseudo-account rejection, conversion changes, scale clamp, and non-zero-dust evaluation are gated on the amendment, so nodes disagree about affected transactions until it activates; the general arithmetic-overflow and zero-share failures remain ungated.
