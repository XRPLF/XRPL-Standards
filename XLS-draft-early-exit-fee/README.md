<pre>
xls: TBD
proposal-from: TBD
title: Closed-Ended Vault Early-Exit Fee
description: Adds an optional early-exit fee that lets a closed-ended vault permit withdrawals during its Investment phase, with the fee retained in the vault.
author: Jingchen Wu (@a1q123456)
status: Draft
category: Amendment
created: 2026-09-15
updated: 2026-09-15
</pre>

# Closed-Ended Vault Early-Exit Fee

## 1. Abstract

This proposal adds one optional field, `EarlyExitFeeRate`, to the `Vault` ledger entry and to `VaultCreate`. It is accepted only on a closed-ended vault (see [Closed-Ended Single Asset Vault](../XLS-draft-closed-ended-vault/README.md)), is set at creation, and is immutable afterwards. When the rate is absent or `0` the vault behaves exactly as the closed-ended specification describes: withdrawals are rejected for the whole Investment phase. When the rate is greater than `0`, a `VaultWithdraw` is permitted during Investment and is charged a fee equal to that percentage of the pre-fee withdrawal amount. Shares are burned against the pre-fee amount, but only the post-fee amount leaves the vault; the difference is simply not withdrawn, so it stays in the vault and raises the value of every remaining share. The fee is disbursed to no party, including the vault owner, the loan broker, and the exiting depositor. The early exit remains subject to `Vault.AssetsAvailable`, so it is a best-efforts exit and not a guaranteed one. Outside the Investment phase, and on open-ended vaults, no fee applies and nothing changes.

## 2. Introduction

A closed-ended vault locks capital for a fixed term: once the subscription window closes, the Investment phase runs to `RedemptionDate` and no depositor can leave. This lock is the purpose of the structure, since it gives the operator a known amount of capital to deploy, but it admits no exceptions. A depositor who needs liquidity mid-term has no option at all, and an operator who would be willing to let a depositor out, on terms that do not penalize the depositors who stay, has no way to offer it.

This proposal adds that option as a per-vault setting. The vault owner may fix an **early-exit fee rate** at creation. If they do, a depositor may withdraw during the Investment phase and pay that percentage of their withdrawal for the privilege. The fee is not revenue: it never leaves the vault, so it accrues to the depositors who remain, compensating them for the liquidity that was consumed and the term that was cut short. If the owner does not set a rate, the vault is exactly the closed-ended vault of the parent proposal, with no early exit at any price.

The early exit has two limits:

- **It is not a redemption guarantee.** A withdrawal during Investment still draws on `Vault.AssetsAvailable`, the vault's uncommitted cash. Capital that has been lent out is not available, so an early exit succeeds only to the extent the vault is holding cash at that moment. A depositor who needs a certain exit must wait for Redemption.
- **It is one-way.** Deposits stay closed for the whole Investment phase (see the parent proposal). A depositor who exits early cannot re-enter, at any price.

The fee rate is fixed at creation and public from that moment, so a depositor knows the exit terms before committing capital, in the same way they know `SubscriptionDate` and `RedemptionDate`.

### 2.1. Permission Matrix

This proposal changes a single cell of the parent proposal's permission matrix, namely `VaultWithdraw` during Investment:

| Transaction   | Open-ended | Subscription | Investment    | Redemption |
| ------------- | ---------- | ------------ | ------------- | ---------- |
| VaultWithdraw | allowed    | allowed      | conditional\* | allowed    |

\* Permitted during Investment if and only if the vault's `EarlyExitFeeRate` is present and greater than `0`, in which case the fee of 3.2 applies. Otherwise rejected with `tecTOO_SOON`, as in the parent proposal.

Every other cell of that matrix is unchanged. In particular, `VaultDeposit` remains rejected for the whole Investment phase, so an early exit cannot be reversed, and `VaultClawback` remains permitted in every phase and is never charged the fee (see 8.5 and A.7). The lending transactions `LoanSet`, `LoanPay`, `LoanManage`, `LoanDelete` and `LoanBrokerSet` are unaffected, as are `VaultSet`, `VaultDelete`, `LoanBrokerDelete` and the `LoanBrokerCover` transactions, which the parent matrix omits.

### 2.2. Protocol Constants

This proposal defines two protocol constants. Both are used only by the `VaultCreate` range check in 4.2.1 and by the fee arithmetic in 3.2; the reasoning behind the cap is in 8.4.

| Constant                  | Value    | Meaning                                                                                                                                                                     |
| ------------------------- | -------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `MAX_EARLY_EXIT_FEE_RATE` | `50000`  | Inclusive upper bound on `EarlyExitFeeRate`, in 1/10th basis points. Equivalent to 50%. A rate of exactly this value is accepted.                                           |
| `RATE_ONE`                | `100000` | The 1/10th basis point value equal to `100%`, used as the denominator of the fee fraction. Follows the rate convention of [XLS-66](../XLS-0066-lending-protocol/README.md). |

### 2.3. Amendments

- `SingleAssetVault` (`featureSingleAssetVault`), from [XLS-65](../XLS-0065-single-asset-vault/README.md): added the `Vault` ledger entry, `VaultCreate`, `VaultWithdraw` and the exchange algorithm this proposal extends.
- `LendingProtocolV1_1` (`featureLendingProtocolV1_1`): added the `ClosedEnded` vault kind, `SubscriptionDate`, `RedemptionDate`, the phase derivation and the `VaultWithdraw` Investment-phase gate, through the [Closed-Ended Single Asset Vault](../XLS-draft-closed-ended-vault/README.md) proposal indexed in [XLS-65.1](../XLS-0065-single-asset-vault/65.1/README.md). This proposal is meaningless without it: `EarlyExitFeeRate` may only be set on a closed-ended vault, and the only behaviour it changes is the gate that proposal introduces. It is a hard prerequisite, and because an enabled amendment is never disabled, a vault carrying an `EarlyExitFeeRate` always has a phase to apply it in.
- `LendingProtocolV1_2` (`featureLendingProtocolV1_2`): the amendment that gates everything in this proposal. Without it, a `VaultCreate` carrying `EarlyExitFeeRate` returns `temDISABLED` (see 4.2.1), no vault holds the field, and `VaultWithdraw` behaves exactly as the parent proposals describe. This proposal adds no amendment of its own; `LendingProtocolV1_2` is the successor to `LendingProtocolV1_1` and is the amendment open for new lending work.
- `fixCleanup3_4_0` (`fixCleanup3_4_0`), from [XLS-65.2](../XLS-0065-single-asset-vault/65.2/README.md): not required by this proposal, and not changed by it. Its rounding tolerances and its zero-asset withdrawal exception apply to the post-fee payout in exactly the way they apply to an unmodified withdrawal, because the fee changes the amount withdrawn and not how that amount is accounted for (see 5.3).

## 3. Ledger Entry: `Vault` (modified)

This proposal modifies the existing `Vault` ledger entry rather than introducing a new one. Its object identifier, ownership, reserve accounting, deletion rules and RPC name are unchanged; only the field listed below is added.

### 3.1. Fields

| Field Name         | Constant | Required | JSON Type | Internal Type | Default Value | Description                                                                                                                     |
| ------------------ | :------: | :------: | :-------: | :-----------: | :-----------: | ------------------------------------------------------------------------------------------------------------------------------- |
| `EarlyExitFeeRate` |   Yes    |    No    | `number`  |   `UINT16`    |      `0`      | The early-exit fee, in 1/10th basis points, charged on a withdrawal made during the Investment phase. Immutable after creation. |

`EarlyExitFeeRate` defaults to `0` and is not stored when it holds that default, so both an absent field and an explicit `0` mean no early exit. The field is stored only on closed-ended vaults (`VaultKind == ClosedEnded`) that were created with a non-zero rate; `VaultCreate` rejects it on any other vault (see 4.2.1).

#### 3.1.1. `EarlyExitFeeRate`

The rate is expressed in 1/10th basis points, matching the rate convention of [XLS-66](../XLS-0066-lending-protocol/README.md): a value of `1` is 1/10 bps, or 0.001%, and `RATE_ONE` (`100000`) would be 100%. Valid values are `0` to `MAX_EARLY_EXIT_FEE_RATE` (`10000`, or 10%) inclusive. As a fraction, the rate is:

$$\phi = \frac{\text{EarlyExitFeeRate}}{100000}$$

A rate of `0`, or an absent field, disables early exit entirely: the parent proposal's Investment-phase rejection stands, and no fee arithmetic is ever performed. Any non-zero rate enables early exit at that price.

### 3.2. Fee Calculation

The fee is charged only by `VaultWithdraw`, and only when the conditions in 5.2.1 hold. It is not an accounting entry and it is not moved anywhere: it is an amount the vault does not pay out. Everything the parent specifications say about how a withdrawal is computed, rounded and accounted for is unchanged; a single subtraction is applied to the payout, and the vault's totals then follow the payout as they always have.

Using the variables of [XLS-65 3.1.7.2](../XLS-0065-single-asset-vault/README.md#3172-exchange-rate-algorithms):

- $\Gamma_{assets}$ — the vault's total assets, and $\iota$ its unrealized loss. The sole-shareholder waiver of [XLS-65 3.6.1](../XLS-0065-single-asset-vault/README.md#361-fields) applies unchanged.
- $\Delta_{shares}$ — the shares burned. Computed **exactly as today** from the transaction's `Amount`: by the _Redeem_ formula when `Amount` is denominated in shares, and by the _Withdraw_ formula when it is denominated in the vault asset. The fee does not enter this step.
- $\Delta_{assets}$ — the **pre-fee** asset amount those shares are worth, $\dfrac{\Delta_{shares} \times (\Gamma_{assets} - \iota)}{\Gamma_{shares}}$, again computed exactly as today.

The fee and the payout are then:

$$F = \left\lceil \Delta_{assets} \times \phi \right\rceil$$

$$\Delta_{assets}^{paid} = \Delta_{assets} - F$$

where $\lceil \cdot \rceil$ rounds **up** to the smallest amount of `Vault.Asset` representable at the precision at which the payout is transferred. Rounding up means any non-zero rate charges at least one unit on any non-zero withdrawal, so a withdrawal cannot be split into pieces small enough to round the fee away (see 8.3). If $\Delta_{assets}^{paid}$ is not positive, the withdrawal fails with `tecPRECISION_LOSS` (see 5.2.1) rather than burning shares for nothing.

One case is exempt. A withdrawal that burns the vault's entire outstanding share supply is charged no fee, so $F = 0$ and $\Delta_{assets}^{paid} = \Delta_{assets}$ (see 5.2.1).

Both `Vault.AssetsTotal` and `Vault.AssetsAvailable` decrease by $\Delta_{assets}^{paid}$, which is also the amount that moves from the vault's pseudo-account to the destination. Each of these follows XLS-65 exactly, substituting $\Delta_{assets}^{paid}$ for $\Delta_{assets}$. Because the shares burned are proportional to $\Delta_{assets}$ while the assets removed are only $\Delta_{assets}^{paid}$, the post-withdrawal exchange rate rises:

$$\frac{\Gamma_{assets} - \Delta_{assets} + F}{\Gamma_{shares} - \Delta_{shares}} \; > \; \frac{\Gamma_{assets}}{\Gamma_{shares}}$$

#### 3.2.1. Worked Example

A closed-ended vault in its Investment phase, with `EarlyExitFeeRate = 2000` (2%) and no unrealized loss:

| Quantity           | Before    |
| ------------------ | --------- |
| `AssetsTotal`      | 1,000,000 |
| `AssetsAvailable`  | 150,000   |
| Shares outstanding | 1,000,000 |
| Exchange rate      | 1.000     |

A depositor submits `VaultWithdraw` with `Amount` = 100,000 of the vault asset:

- $\Delta_{shares} = 100{,}000$ — burned against the pre-fee amount.
- $\Delta_{assets} = 100{,}000$ — the pre-fee value of those shares.
- $F = 100{,}000 \times 0.02 = 2{,}000$.
- $\Delta_{assets}^{paid} = 98{,}000$ — what the depositor receives, and what the vault needs in `AssetsAvailable`.

| Quantity           | After    |
| ------------------ | -------- |
| `AssetsTotal`      | 902,000  |
| `AssetsAvailable`  | 52,000   |
| Shares outstanding | 900,000  |
| Exchange rate      | 1.002222 |

The 2,000 that was not paid out is spread over the 900,000 shares still in issue, raising the value of every remaining depositor's holding by 0.2222%. The exiting depositor received 98,000 for shares that were worth 100,000 an instant earlier.

### 3.3. Invariants

- `EarlyExitFeeRate <= MAX_EARLY_EXIT_FEE_RATE` always holds. The bound is checked at creation (see 4.2.1) and kept by the immutability rule below.
- `EarlyExitFeeRate` is present only on a `Vault` with `VaultKind == ClosedEnded`.
- `EarlyExitFeeRate` is immutable: once set at creation it is never added, removed or changed by any transaction. Under `LendingProtocolV1_2` it joins the immutability set of [XLS-65.1.1](../XLS-0065-single-asset-vault/65.1/65.1.1-unmodifiable-vault-fields.md), enforced by the same invariant check as `VaultKind`, `SubscriptionDate` and `RedemptionDate`: if `Vault.EarlyExitFeeRate` is present, `Vault.EarlyExitFeeRate == Vault'.EarlyExitFeeRate`; if it is absent, it remains absent, except when the transaction creates the entry.
- Every XLS-65 `Vault` invariant, in particular `AssetsAvailable <= AssetsTotal` and the zero-shares rule (`OutstandingAmount == 0` implies `AssetsTotal == 0` and `AssetsAvailable == 0`), continues to hold unmodified. The waiver in 5.2.1 is what preserves the zero-shares rule (see 8.2).

### 3.4. Example JSON

```json
{
  "LedgerEntryType": "Vault",
  "Account": "rwCNM7SeUHTajEBQDiNqxDG8p1Mreizw85",
  "Asset": {
    "currency": "USD",
    "issuer": "rXJSJiZMxaLuH3kQBUV5DLipnYtrE6iVb"
  },
  "AssetsAvailable": "0",
  "AssetsMaximum": "1000000",
  "AssetsTotal": "0",
  "Data": "5661756C74206D65746164617461",
  "Flags": 0,
  "LossUnrealized": "0",
  "Owner": "rNGHoQwNG753zyfDrib4qDvvswbrtmV8Es",
  "OwnerNode": "0",
  "Scale": 6,
  "Sequence": 200370,
  "ShareMPTID": "0000000169F415C9F1AB6796AB9224CE635818AFD74F8175",
  "WithdrawalPolicy": 1,
  "VaultKind": 1,
  "SubscriptionDate": 711232800,
  "RedemptionDate": 721600800,
  "EarlyExitFeeRate": 2000
}
```

## 4. Transaction: `VaultCreate` (modified)

### 4.1. Fields

| Field Name         | Required? | JSON Type | Internal Type | Default Value | Description                                                                                                                                                                                                                                           |
| ------------------ | :-------: | :-------: | :-----------: | :-----------: | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `EarlyExitFeeRate` |    No     | `number`  |   `UINT16`    |      `0`      | **New.** The early-exit fee, in 1/10th basis points, charged on a withdrawal made during the Investment phase. Valid values are `0` to `MAX_EARLY_EXIT_FEE_RATE` inclusive. Permitted only when `VaultKind == ClosedEnded`. Immutable after creation. |

### 4.2. Failure Conditions

#### 4.2.1. Data Verification

1. If `LendingProtocolV1_2` is not enabled and `sfEarlyExitFeeRate` is present, return `temDISABLED`.
2. If `sfEarlyExitFeeRate` is present and `sfVaultKind` is absent or not `ClosedEnded`, return `temMALFORMED`.
3. If `sfEarlyExitFeeRate` is greater than `MAX_EARLY_EXIT_FEE_RATE`, return `temMALFORMED`.

#### 4.2.2. Protocol-Level Failures

No changes.

### 4.3. State Changes

On Success (tesSUCCESS):

- If `sfEarlyExitFeeRate` is absent or `0`: the new `Vault` object is unchanged from the parent proposals. The field is not stored (see 3.1).
- Otherwise: set `sfEarlyExitFeeRate` on the new `Vault` object.

### 4.4. Invariants

- Every `Vault` carrying `EarlyExitFeeRate` has `VaultKind == ClosedEnded` and `0 < EarlyExitFeeRate <= MAX_EARLY_EXIT_FEE_RATE`.

### 4.5. Example JSON

```json
{
  "TransactionType": "VaultCreate",
  "Account": "rNGHoQwNG753zyfDrib4qDvvswbrtmV8Es",
  "Asset": {
    "currency": "USD",
    "issuer": "rXJSJiZMxaLuH3kQBUV5DLipnYtrE6iVb"
  },
  "AssetsMaximum": "1000000",
  "Fee": "5000000",
  "Flags": 0,
  "Scale": 6,
  "Sequence": 200370,
  "WithdrawalPolicy": 1,
  "VaultKind": 1,
  "SubscriptionDate": 711232800,
  "RedemptionDate": 721600800,
  "EarlyExitFeeRate": 2000
}
```

## 5. Transaction: `VaultWithdraw` (modified)

### 5.1. Fields

No changes. `Amount` keeps its meaning in both denominations, and is the **pre-fee** amount: a depositor who submits an asset-denominated `Amount` during the Investment phase receives less than `Amount` (see A.2).

### 5.2. Failure Conditions

#### 5.2.1. Protocol-Level Failures

The parent proposal rejects every withdrawal made during the Investment phase. That condition is replaced, when `LendingProtocolV1_2` is enabled, by the following. All other `VaultWithdraw` failure conditions of XLS-65 and of the parent proposal apply unchanged.

1. If the vault is closed-ended, its phase is `Investment` (`SubscriptionDate < now < RedemptionDate`, where `now` is the parent ledger close time), and `EarlyExitFeeRate` is absent or `0`, return `tecTOO_SOON`.
2. If the fee applies (that is, the vault is closed-ended, its phase is `Investment`, `EarlyExitFeeRate` is greater than `0`, and $\Delta_{shares}$ is less than the outstanding share supply) and the post-fee payout $\Delta_{assets}^{paid}$ computed per 3.2 is not positive, return `tecPRECISION_LOSS`.
3. The XLS-65 liquidity check on `Vault.AssetsAvailable` is made against the **post-fee** payout: if `Vault.AssetsAvailable` is less than $\Delta_{assets}^{paid}$, return `tecINSUFFICIENT_FUNDS`. The fee is never paid out, so it is not liquidity the vault must hold (see 8.6). Outside the Investment phase, and when no fee applies, $\Delta_{assets}^{paid} = \Delta_{assets}$ and the check is identical to the parent's. The check on the submitter's share balance is unchanged and is made against $\Delta_{shares}$, which is computed from the pre-fee amount.

The fee is waived when a single withdrawal burns the vault's **entire outstanding share supply** ($\Delta_{shares}$ equals `MPTokenIssuance(Vault.ShareMPTID).OutstandingAmount`). There are then no remaining shares for a retained fee to accrue to, and retaining it would strand assets in a vault with no shares in issue — breaking XLS-65 `Vault` invariant 7 and blocking `VaultDelete` forever (see 8.2). This is a separate condition from, and independent of, the XLS-65 sole-shareholder waiver of the `LossUnrealized` deduction: a sole shareholder who withdraws only part of their holding gets that waiver and is still charged the fee.

### 5.3. State Changes

Unchanged from XLS-65, with $\Delta_{assets}^{paid}$ of 3.2 in the place of $\Delta_{assets}$ everywhere an asset amount is decreased or transferred:

1. The submitter's share `MPToken.MPTAmount` and the share `MPTokenIssuance.OutstandingAmount` decrease by $\Delta_{shares}$ — unchanged, and computed from the pre-fee amount.
2. `Vault.AssetsTotal` and `Vault.AssetsAvailable` decrease by $\Delta_{assets}^{paid}$.
3. The vault pseudo-account's asset balance decreases by $\Delta_{assets}^{paid}$ and the destination's increases by the same, by whichever of the `XRP`, `IOU` or `MPT` paths of XLS-65 3.6.3 applies.

The fee is not a transfer and has no state change of its own. It is the difference between what the burned shares were worth and what the vault paid out, and it remains in the vault as part of `AssetsTotal` and `AssetsAvailable`.

### 5.4. Invariants

- No `VaultWithdraw` succeeds during a closed-ended vault's `Investment` phase unless the vault's `EarlyExitFeeRate` is greater than `0`.
- When a fee is charged, `Vault.AssetsTotal` and `Vault.AssetsAvailable` each decrease by $\Delta_{assets}^{paid}$, which is strictly positive and strictly less than $\Delta_{assets}$. Both totals therefore still strictly decrease: a withdrawal never increases the vault's assets, so `AssetsMaximum` cannot be crossed by one.
- The XLS-65 `VaultWithdraw` invariants hold unmodified against $\Delta_{assets}^{paid}$: the vault's asset balance decreases by a positive amount, the destination's increases by the same magnitude (subject to the XLS-65.2 tolerances), and both accounting fields track the vault's asset balance decrease exactly.
- After a withdrawal that charged a fee, the vault's exchange rate is strictly greater than it was before, and the outstanding share supply is strictly greater than zero.

### 5.5. Example JSON

No changes.

## 6. RPC: `vault_info` (modified)

The `vault_info` method retrieves a `Vault` ledger entry. This proposal does not change its request fields; it only adds the new `Vault` field to the response when it is present.

### 6.1. Request Fields

No changes.

### 6.2. Response Fields

The following field is added to the `vault` object in the response. Only the newly introduced field is listed here; all existing response fields are unchanged.

| Field Name               | Required? | JSON Type | Description                                                                                                                                        |
| ------------------------ | --------- | --------- | -------------------------------------------------------------------------------------------------------------------------------------------------- |
| `vault.EarlyExitFeeRate` | `no`      | `number`  | The early-exit fee in 1/10th basis points. Absent means `0` — no early exit is possible. Present only on closed-ended vaults with a non-zero rate. |

### 6.3. Failure Conditions

No changes.

### 6.4. Example Request

No changes.

### 6.5. Example Response

The `vault` object of a closed-ended vault with an early-exit fee, showing only the new field (all existing fields are as in XLS-65 and the parent proposal):

```json
{
  "result": {
    "vault": {
      "LedgerEntryType": "Vault",
      "VaultKind": 1,
      "SubscriptionDate": 800000000,
      "RedemptionDate": 900000000,
      "EarlyExitFeeRate": 2000
    }
  }
}
```

A vault created without a rate omits `EarlyExitFeeRate`, which callers MUST interpret as `0`.

## 7. RPC: `ledger_entry` (modified)

The `ledger_entry` method returns a `Vault` object when queried with a `vault` object ID. This proposal does not change its request fields; it only adds the new `Vault` field to the returned object when it is present.

### 7.1. Request Fields

No changes.

### 7.2. Response Fields

The same field added to `vault_info` (see 6.2) is added to the `Vault` object returned by `ledger_entry`. Only the newly introduced field is listed here; all existing fields are unchanged.

| Field Name         | Required? | JSON Type | Description                                                                                                                                        |
| ------------------ | --------- | --------- | -------------------------------------------------------------------------------------------------------------------------------------------------- |
| `EarlyExitFeeRate` | `no`      | `number`  | The early-exit fee in 1/10th basis points. Absent means `0` — no early exit is possible. Present only on closed-ended vaults with a non-zero rate. |

### 7.3. Failure Conditions

No changes.

### 7.4. Example Request

No changes.

### 7.5. Example Response

```json
{
  "result": {
    "node": {
      "LedgerEntryType": "Vault",
      "VaultKind": 1,
      "SubscriptionDate": 800000000,
      "RedemptionDate": 900000000,
      "EarlyExitFeeRate": 2000
    }
  }
}
```

## 8. Rationale

### 8.1. Why the fee stays in the vault

The fee exists to price an externality. A depositor who exits during Investment consumes uncommitted cash the vault was holding to fund loans or to meet later obligations, and leaves the remaining depositors with a smaller base over which fixed costs and unrealized losses are spread. The parties who bear that cost are the depositors who stay, so they are the parties the fee compensates.

Paying it to the vault owner or the loan broker would invert the incentive: the owner sets the rate, and if they also collected it they would profit from every early exit and would be motivated to set the rate high and to encourage exits. Retaining it in the vault leaves the owner with no direct claim on it — they benefit only through whatever shares they themselves hold, pro rata with everyone else (see 12) — while giving the remaining depositors the entire benefit.

Retention is also the cheapest possible mechanism. Because the fee is defined as an amount _not withdrawn_ rather than an amount transferred, it needs no new accounting field, no distribution step, and no change to any XLS-65 invariant: the vault's totals follow the payout exactly as they always have, and the NAV rise falls out of the existing exchange-rate arithmetic (see 3.2).

### 8.2. Why the last exiting shareholder pays no fee

A retained fee only means anything if there are shares left for it to accrue to. If a withdrawal burns the entire outstanding share supply, retaining a fee would leave the vault holding assets against zero shares. That is not merely pointless, it is unrepresentable: XLS-65 `Vault` invariant 7 requires `AssetsTotal == 0` and `AssetsAvailable == 0` whenever `OutstandingAmount == 0`, and `VaultDelete` requires an empty vault — so the retained fee would be permanently stranded and the vault permanently undeletable. Waiving the fee on a full exit is what keeps this proposal's arithmetic inside the parent invariants.

The waiver is narrow by design. It triggers on the share supply reaching zero in a single withdrawal, not on the submitter being the only holder, so a sole holder taking a partial withdrawal still pays. Its exploitability is bounded by its precondition: a holder can only reach it by acquiring every other share in issue (see 12).

### 8.3. Why the fee rounds up

The fee is rounded up to the smallest representable unit of the vault asset, rather than down or to nearest. Rounding down would make the fee zero on any withdrawal small enough that the product underflows the asset's precision, and because withdrawals can be repeated, a depositor could exit an arbitrary position fee-free in small enough slices — bounded only by transaction fees. Rounding up guarantees that any non-zero rate costs at least one unit on any non-zero withdrawal, so slicing strictly increases the total fee paid, and the incentive points the right way.

The cost of rounding up is that the effective rate on a very small withdrawal exceeds the configured rate, up to the extreme case where the fee consumes the whole payout. Rather than burn shares for a zero payout, that case is rejected with `tecPRECISION_LOSS` (see 5.2.1).

### 8.4. Why the cap is 10%

`MAX_EARLY_EXIT_FEE_RATE` is `10000` (10%), which matches the type and bound of XLS-66's `LoanBroker.ManagementFeeRate` — a `UINT16` in 1/10th basis points capped at 10%. Reusing that shape keeps one rate convention across the lending specifications, and 10% is well above the 1–5% exit charge that term credit funds apply in practice.

A cap is necessary, not merely prudent. A rate at or near 100% would let an owner configure a vault whose only mid-term exit destroys the depositor's position: shares burned, nothing paid out. That case also collides with XLS-65's requirement that a withdrawal move a positive amount of assets, which would turn a legal configuration into a transaction that can only fail. Capping the rate keeps every configured rate usable. `UINT16` can express rates up to 65.535%, so the bound can be raised by a later amendment without changing the field's type or wire format.

### 8.5. Why `VaultClawback` is not charged

`VaultClawback` is the asset issuer forcibly removing assets from a depositor's position; the depositor is not choosing to exit. Charging an early-exit fee on it would transfer value from the clawed-back holder to the remaining holders on the strength of a decision neither made, and would let an issuer raise the vault's NAV at a chosen holder's expense. The clawback path is therefore untouched: it removes assets and burns shares exactly as XLS-65 specifies, in every phase.

### 8.6. Why liquidity is checked against the post-fee payout

Only the payout leaves the vault. The retained fee stays in `AssetsAvailable`, so requiring the vault to hold the full pre-fee amount in uncommitted cash would reject withdrawals the vault can plainly satisfy — for a 2% fee, any request between 98% and 100% of available cash. Checking the amount that actually moves is both correct and the least surprising rule: the pre-fee and post-fee thresholds differ by exactly the fee.

### 8.7. Alternatives considered

- **A fee that decays towards `RedemptionDate`.** Economically attractive — the cost of an early exit really does fall as the term runs out — but it requires a second stored parameter and a schedule, makes the payout a function of the ledger close time, and turns a one-line disclosure into a curve a depositor has to compute. A flat rate is a single immutable number a depositor can read off the ledger, and an owner who wants a decaying profile can approximate it with a sequence of vaults.
- **Making the rate mutable via `VaultSet`.** Rejected for the same reason `SubscriptionDate` and `RedemptionDate` are immutable: the rate is a term depositors rely on when they subscribe. A mutable rate could be raised to trap capital after it is committed, or dropped to zero to let a favoured holder exit cheaply.
- **Paying the fee to the vault owner or loan broker as a cover top-up.** Rejected; see 8.1.
- **Allowing early exit with no fee at all.** That is the open-ended vault. The fee is what makes an early exit fair to the depositors who stay, and it is what lets an owner offer mid-term liquidity without abandoning the fixed-term structure.
- **Guaranteeing the exit by forcing loan liquidation.** Out of scope, and not achievable: loans in this protocol cannot be called early by the vault. Early exit is best-efforts against uncommitted cash by construction (see 12).

## 9. Backwards Compatibility

- The feature is inert unless `LendingProtocolV1_2` is enabled (see 2.3). Ledger entries and transactions are unchanged for nodes that have not activated it.
- **Open-ended vaults are unaffected.** They cannot carry `EarlyExitFeeRate` (4.2.1), have no phases, and their withdrawal behaviour is untouched.
- **Existing closed-ended vaults are unaffected.** `EarlyExitFeeRate` is set at creation only, so every vault created before the amendment has no rate, and its Investment-phase withdrawals continue to be rejected with `tecTOO_SOON`. The parent proposal's behaviour is the default, both before and after this amendment.
- The new field is optional, so existing serialised vaults deserialise unchanged.
- **No XLS-65 or XLS-66 invariant changes.** The fee is an amount not withdrawn, so the accounting deltas, the share-burn accounting, and the XLS-65.2 rounding tolerances all apply to the payout exactly as they apply to an unmodified withdrawal.
- **Integrators must read the field before quoting a withdrawal.** A client that computes an expected payout from `Amount` and the exchange rate alone will over-quote by the fee for a withdrawal made during Investment. The field is exposed by both `vault_info` and `ledger_entry` (see 6 and 7).

## 10. Test Plan

### 10.1. VaultCreate

- A closed-ended creation with a valid non-zero `EarlyExitFeeRate` succeeds and stores the field.
- Creation with `EarlyExitFeeRate == 0` succeeds and does **not** store the field; the vault is indistinguishable from one created without it.
- Creation with `EarlyExitFeeRate == MAX_EARLY_EXIT_FEE_RATE` is accepted; one greater returns `temMALFORMED`.
- Creation of an open-ended vault (or one with an absent `VaultKind`) carrying `EarlyExitFeeRate` returns `temMALFORMED`, including when the rate is `0`.
- Before `LendingProtocolV1_2`, any `VaultCreate` carrying `EarlyExitFeeRate` returns `temDISABLED`.

### 10.2. VaultSet

- A `VaultSet` carrying `EarlyExitFeeRate` is rejected at deserialisation, for both closed-ended and open-ended vaults, with and without the amendment.

### 10.3. VaultWithdraw during Investment

- With a non-zero rate, an asset-denominated withdrawal succeeds; the payout equals $\Delta_{assets} - F$, the shares burned equal $\Delta_{shares}$ computed from the pre-fee amount, and `AssetsTotal` and `AssetsAvailable` each decrease by the payout only.
- With a non-zero rate, a share-denominated withdrawal (redeem) succeeds and is charged the same fee.
- With an absent or `0` rate, a withdrawal returns `tecTOO_SOON` (parent behaviour).
- The vault's exchange rate after a fee-charging withdrawal is strictly higher than before, and a second depositor redeeming an identical share amount immediately afterwards receives strictly more assets than the first.
- The worked example of 3.2.1 reproduces exactly, including both post-state totals.
- A withdrawal with a `Destination` behaves identically: the destination receives the post-fee amount.
- A fee-charging withdrawal on a vault with a non-zero `LossUnrealized` applies the fee to the post-`LossUnrealized` payout.

### 10.4. VaultWithdraw outside Investment

- A withdrawal during Subscription charges no fee, even with a non-zero rate configured.
- A withdrawal during Redemption charges no fee.
- Boundary: a withdrawal at `now == SubscriptionDate` charges no fee; at `now == SubscriptionDate + 1` it is charged. A withdrawal at `now == RedemptionDate` charges no fee; at `now == RedemptionDate - 1` it is charged.
- Withdrawals from open-ended vaults are unaffected.

### 10.5. Liquidity

- A withdrawal whose post-fee payout exceeds `AssetsAvailable` returns `tecINSUFFICIENT_FUNDS`.
- Boundary: a withdrawal whose post-fee payout equals `AssetsAvailable` succeeds, even though its pre-fee amount exceeds `AssetsAvailable`.
- A vault whose cash is fully deployed into loans rejects every early exit, and accepts them again as loan payments restore `AssetsAvailable`.
- An early exit does not affect any outstanding `Loan` or the broker's `CoverAvailable`.

### 10.6. Rounding and precision

- The fee is rounded up: a withdrawal whose exact fee falls between two representable amounts is charged the larger.
- A withdrawal small enough that the rounded-up fee equals or exceeds the pre-fee amount returns `tecPRECISION_LOSS`, and no shares are burned.
- Splitting a withdrawal into `n` pieces costs at least as much in total fees as taking it in one, for each of `XRP`, `IOU` and `MPT` assets.
- The tests are run for all three asset types and across the `Scale` range.

### 10.7. Full exit waiver

- A withdrawal during Investment that burns the entire outstanding share supply is charged no fee, empties the vault (`AssetsTotal == 0`, `AssetsAvailable == 0`), and the vault can then be deleted.
- A sole shareholder taking a partial withdrawal during Investment **is** charged the fee, and the XLS-65 sole-shareholder `LossUnrealized` waiver still applies to the pre-fee amount.
- With two holders, a withdrawal that burns all of one holder's shares but not the whole supply is charged the fee.

### 10.8. VaultClawback

- A clawback during Investment from a vault with a non-zero rate charges no fee; the assets removed and shares burned match XLS-65 exactly.

### 10.9. RPC surface

- `vault_info` and `ledger_entry` return `EarlyExitFeeRate` for a vault created with a non-zero rate, and omit it otherwise.

### 10.10. Invariant checks

- An invariant check asserts 4.4 on `VaultCreate` and 5.4 on `VaultWithdraw`.
- The immutability rule of 3.3 is asserted on every transaction that modifies a `Vault`: a test that changes `EarlyExitFeeRate` on an existing vault, and one that adds it to a vault that lacks it, both expect the check to fire.
- A test asserts that no `VaultWithdraw` can leave a vault with zero outstanding shares and non-zero `AssetsTotal`.

### 10.11. End-to-end tests

- A full lifecycle with several depositors: subscribe, enter Investment, originate loans, one depositor exits early and pays the fee, remaining depositors' NAV rises, loans repay, Redemption opens, the remaining depositors redeem and receive their enlarged share. The sum of all payouts plus the final vault balance reconciles against all deposits plus interest.
- The same lifecycle on a vault with no rate configured confirms the parent proposal's behaviour is unchanged.

## 11. Reference Implementation

_TBD_

## 12. Security Considerations

- **The fee is not a liquidity guarantee.** An early exit draws on `Vault.AssetsAvailable` only. A vault with its capital fully deployed cannot honour any early exit, whatever the rate, and a depositor MUST NOT treat a configured rate as a redemption right. Under the `first-come-first-serve` withdrawal policy the available cash goes to whoever asks first, so in a stressed vault early exit is a race. Depositors who need certain liquidity must wait for `RedemptionDate`.
- **Early exits compete with lending.** Cash consumed by an early exit is cash unavailable to `LoanSet`. An owner who configures a rate should expect the vault's deployable capital to be less predictable than in a vault without one, and size its cash buffer accordingly. Outstanding loans are never at risk: `AssetsAvailable` is uncommitted cash by definition, and an early exit cannot reach capital already lent out or the broker's first-loss cover.
- **The owner cannot extract the fee, but does share in it.** The fee is never transferred, so no owner or broker action can capture it. An owner who holds shares nonetheless benefits from every early exit pro rata with the other remaining holders, which is a mild incentive to set a high rate and to encourage exits. The cap of 8.4 and the immutability of the rate bound this: the rate is fixed before any depositor subscribes, and a depositor who does not accept it can decline to subscribe.
- **The rate cannot be changed after capital is committed.** `EarlyExitFeeRate` is immutable (3.3) and absent from `VaultSet`'s format, so an owner cannot raise it to trap committed capital, lower it to let a favoured holder exit cheaply, or add it to a vault that was advertised without one.
- **Adverse selection is reduced, not eliminated.** A depositor who learns of an incoming loss can still exit during Investment ahead of its realisation. The `LossUnrealized` mechanism of XLS-65 already prices known impairment into the payout, and the fee adds a further cost to leaving early, but neither addresses a loss that has not yet been marked. This is the same exposure the parent proposal has in its Redemption phase; the early-exit fee narrows the window's profitability rather than closing it.
- **The full-exit waiver is exploitable only by buying out the vault.** A holder who accumulates 100% of the shares in issue can exit without a fee (5.2.1). Reaching that position requires acquiring every other share on terms the other holders accept, which costs more than the fee it avoids, and the waiver is required to keep the vault's assets from being stranded (8.2). Note that share MPTs are transferable unless the vault was created with `tfVaultShareNonTransferable`, so this path exists on any transferable-share vault.
- **Fee rounding favours the vault, by a bounded amount.** The rounded-up fee exceeds the configured rate by less than one representable unit of the vault asset per withdrawal. This closes the dust-splitting bypass (8.3) at the cost of a sub-unit overcharge, and a withdrawal too small to leave a positive payout is rejected rather than allowed to burn shares for nothing.
- **No new time or trust dependency.** The fee is applied on the basis of the vault's phase, which is derived from the consensus ledger close time and two immutable dates, and its amount depends only on stored ledger values.

# Appendix

## Appendix A: FAQ.

### A.1: Why does the fee stay in the vault instead of going to the vault owner or the loan broker?

Because the depositors who stay are the ones who bear the cost of someone else leaving early. Paying the fee to the owner would also make the party who sets the rate the party who collects it. See 8.1.

### A.2: If I ask to withdraw 100,000, do I receive 100,000?

Not during the Investment phase. `Amount` is the pre-fee amount: shares are burned as if you withdrew 100,000, and you receive 100,000 less the fee. To receive a specific amount $X$ after the fee, request

$$\text{Amount} = \frac{X}{1 - \phi}$$

rounded up, where $\phi$ is the rate as a fraction (3.1.1) — for a 2% rate, ask for 102,041 to receive 100,000. Outside the Investment phase there is no fee and `Amount` behaves exactly as it does today.

### A.3: Can the owner add, remove or change the fee after the vault is created?

No. `EarlyExitFeeRate` is set by `VaultCreate` and is immutable (3.3). It is not part of `VaultSet`'s transaction format, so a `VaultSet` carrying it fails at deserialisation. A vault created without a rate can never gain one, and the choice is irreversible in both directions — as with `VaultKind` and the two phase dates.

### A.4: Why is the last depositor to exit not charged?

There would be no one left to receive the fee, and the retained assets would be stranded in a vault with no shares in issue, which XLS-65 forbids and which would block `VaultDelete` permanently. See 8.2.

### A.5: Does a configured fee mean I can always exit early?

No. The withdrawal still needs `Vault.AssetsAvailable` to cover the payout, and capital that has been lent out is not available. If the vault is holding no uncommitted cash, the withdrawal fails with `tecINSUFFICIENT_FUNDS` no matter what you are willing to pay. Early exit is best-efforts.

### A.6: Why is the rate flat rather than decaying as `RedemptionDate` approaches?

A flat rate is one immutable number a depositor can read off the ledger before subscribing. A decaying rate needs a second parameter and a schedule, and makes the payout depend on when within the term you ask. See 8.7.

### A.7: Does the fee apply to `VaultClawback`?

No. Clawback is compelled by the asset issuer, not chosen by the depositor, and charging it would let an issuer raise the vault's NAV at a chosen holder's expense. See 8.5.

### A.8: I exited early and now want back in. Can I re-deposit?

No. `VaultDeposit` is rejected for the whole Investment phase, and that is unchanged by this proposal. An early exit is one-way for the remainder of the term.

### A.9: Does an early exit affect outstanding loans or the loan broker's first-loss capital?

No. It moves only uncommitted cash out of the vault. No `Loan` object, no `LoanBroker.DebtTotal`, and no `CoverAvailable` is touched, and the broker's cover requirement is computed from `DebtTotal`, which an early exit does not change.

### A.10: Can I set the fee on an open-ended vault?

No. `VaultCreate` returns `temMALFORMED` if `EarlyExitFeeRate` is present on a vault that is not closed-ended (4.2.1). An open-ended vault has no Investment phase, so there is no period during which the fee could apply — its depositors can already withdraw at any time.
