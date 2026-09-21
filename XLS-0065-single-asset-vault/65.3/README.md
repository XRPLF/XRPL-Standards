<pre>
  xls: 65.3
  title: Closed-Ended Vault Early-Exit Fee
  description: Adds an optional, immutable early-exit fee that lets a closed-ended Vault permit withdrawals during Investment, with the fee retained in the Vault
  author: Jingchen Wu (@a1q123456)
  proposal-from: TBD
  status: Draft
  category: Amendment
  created: 2026-09-15
  updated: 2026-09-21
</pre>

# 65.3 Closed-Ended Vault Early-Exit Fee

## 1. Abstract

Under the `LendingProtocolV1_2` amendment, a closed-ended Vault may carry one additional immutable field, `EarlyExitFeeRate`, set at creation. When it is absent, the Vault behaves exactly as [XLS-65.1.4](../65.1/65.1.4-closed-ended-vault.md) describes: `VaultWithdraw` is rejected for the whole Investment phase. When it is present, a `VaultWithdraw` is permitted during Investment and is charged that percentage of the pre-fee withdrawal. A zero-percent rate permits the exit and charges nothing for it. At a rate of 100% the fee consumes the entire payout, so the withdrawal burns the shares and transfers nothing. Shares are burned against the pre-fee amount while only the post-fee amount leaves the Vault, so the difference stays in the Vault and raises the value of every remaining share. The fee is paid to no party. The exit still draws on `Vault.AssetsAvailable`, so it is best-efforts, not guaranteed. Open-ended Vaults, and closed-ended Vaults outside Investment, are unaffected.

## 2. Motivation

A closed-ended Vault locks capital for a fixed term. That lock is the point of the structure where it gives the operator a known amount of capital to deploy, but it admits no exceptions. A depositor who needs liquidity mid-term has no option at all, and an operator willing to let one out on terms that do not penalize the depositors who stay has no way to offer it.

An early-exit fee makes that option a per-Vault setting. The owner fixes a rate at creation; a depositor may then leave during Investment and pay that percentage for the privilege. The fee is not revenue. It never leaves the Vault, so it accrues to the depositors who remain, compensating them for the liquidity consumed and the term cut short.

Whether a mid-term exit is possible and what it costs are two separate decisions, and the field expresses both. An owner who sets no rate at all gets the closed-ended Vault unchanged, with no early exit at any price. An owner who sets a rate of `0` permits mid-term exits and charges nothing for them, which is the right configuration for a Vault whose term is a plan rather than a promise. Absence is the conservative default, so every Vault created before this amendment keeps its meaning (4.7).

Fixing the rate at creation and exposing it on the ledger means a depositor knows the exit terms before committing capital, in the same way they know `SubscriptionDate` and `RedemptionDate`.

## 3. Specification

This patch changes the parent [XLS-65](../README.md) sections named below, and the sections of [XLS-65.1.4](../65.1/65.1.4-closed-ended-vault.md) it identifies. All other parent behavior is unchanged. `LendingProtocolV1_1` is a hard prerequisite: `EarlyExitFeeRate` may only be set on a closed-ended Vault, and the only behavior it changes is the Investment-phase gate that [XLS-65.1.4](../65.1/65.1.4-closed-ended-vault.md) introduces.

### 3.1 Protocol Constants

| Constant                  | Value    | Meaning                                                                                                                                                                        |
| ------------------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `MAX_EARLY_EXIT_FEE_RATE` | `100000` | Inclusive upper bound on `EarlyExitFeeRate`, in 1/10th basis points. Equivalent to 100%. A rate of exactly this value is accepted; an early exit at that rate pays out nothing and still burns the shares (4.4). |

### 3.2 Ledger Entry: `Vault`

#### 3.2.1 Fields

Add this field to parent 3.1.2:

| Field Name         | Constant | Required | JSON Type | Internal Type | Default Value | Description                                                                                                                                                                                         |
| ------------------ | :------: | :------: | :-------: | :-----------: | :-----------: | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `EarlyExitFeeRate` |   Yes    |    No    | `number`  |   `UINT32`    |     `N/A`     | The early-exit fee, in 1/10th basis points, charged on a withdrawal made during the Investment phase. Its presence is what permits a withdrawal during Investment at all. Immutable after creation. |

An absent field and a `0` are not equivalent:

| `Vault.EarlyExitFeeRate`              | `VaultWithdraw` during Investment             |
| ------------------------------------- | --------------------------------------------- |
| Absent                                | Rejected with `tecTOO_SOON`, as in the parent |
| `0`                                   | Permitted, and charged no fee                 |
| `0 < rate <= MAX_EARLY_EXIT_FEE_RATE` | Permitted, and charged the fee of 3.2.2       |

The field is stored only on a Vault with `VaultKind == ClosedEnded`; `VaultCreate` rejects it on any other Vault, including when the rate is `0` (3.3.2).

The rate is expressed in 1/10th basis points, matching the rate convention of [XLS-66](../../XLS-0066-lending-protocol/README.md): a value of `1` is 1/10 bps, or 0.001%, and `100000` is 100%. Valid values are `0` to `MAX_EARLY_EXIT_FEE_RATE` inclusive. As a fraction, the rate is:

$$\phi = \frac{\text{EarlyExitFeeRate}}{100000}$$

#### 3.2.2 Fee Calculation

The fee is charged only by `VaultWithdraw`, and only when the conditions of 3.4.1 hold, which require a rate greater than `0`. Everything parent 3.1.7 and 3.6.3 say about how a withdrawal is computed, rounded, and accounted for is unchanged; a single subtraction is applied to the payout, and the Vault's totals then follow the payout as they always have.

A Vault whose rate is `0` permits the withdrawal and charges nothing: $F = 0$, $\Delta_{assets}^{paid} = \Delta_{assets}$, and the arithmetic below reduces to the parent's unmodified.

Using the variables of parent [3.1.7.2](../README.md#3172-exchange-rate-algorithms):

- $\Gamma_{assets}$ is the Vault's total assets and $\iota$ its unrealized loss. The sole-shareholder waiver of parent 3.6.1 applies unchanged.
- $\Delta_{shares}$, the shares burned, is computed exactly as in the parent from the transaction's `Amount`: by the _Redeem_ formula when `Amount` is denominated in shares, and by the _Withdraw_ formula when it is denominated in the Vault asset. The fee does not enter this step.
- $\Delta_{assets}$, the **pre-fee** asset amount those shares are worth, $\dfrac{\Delta_{shares} \times (\Gamma_{assets} - \iota)}{\Gamma_{shares}}$, is likewise computed exactly as in the parent.

The fee and the payout are then:

$$F = \left\lceil \Delta_{assets} \times \phi \right\rceil$$

$$\Delta_{assets}^{paid} = \Delta_{assets} - F$$

where $\lceil \cdot \rceil$ rounds **up** to the smallest amount of `Vault.Asset` representable at the precision at which the payout is transferred. Rounding up means any non-zero rate charges at least one unit on any non-zero withdrawal, so a withdrawal cannot be split into pieces small enough to round the fee away (4.3).

$\Delta_{assets}^{paid}$ may be zero, and a zero payout is **not** an error. The withdrawal succeeds, $\Delta_{shares}$ are burned, nothing is transferred, and the whole pre-fee value stays in the Vault. The fee is defined as an amount the Vault does not pay out, and a fee equal to the whole amount is the limit of that definition rather than a failure of the arithmetic (3.4.1). At the maximum rate of `100000`, $F = \Delta_{assets}$ for every withdrawal, so every fee-charging withdrawal on such a Vault pays out nothing and the depositor forfeits the shares they burn (4.4).

One case is charged no fee at all: a withdrawal that burns the Vault's entire outstanding share supply, so $F = 0$ and $\Delta_{assets}^{paid} = \Delta_{assets}$ (3.4.1).

Both `Vault.AssetsTotal` and `Vault.AssetsAvailable` decrease by $\Delta_{assets}^{paid}$, which is also the amount that moves from the Vault's pseudo-account to the destination. Each follows the parent exactly, substituting $\Delta_{assets}^{paid}$ for $\Delta_{assets}$. Because the shares burned are proportional to $\Delta_{assets}$ while the assets removed are only $\Delta_{assets}^{paid}$, the post-withdrawal exchange rate rises whenever $F > 0$:

$$\frac{\Gamma_{assets} - \Delta_{assets} + F}{\Gamma_{shares} - \Delta_{shares}} \; > \; \frac{\Gamma_{assets}}{\Gamma_{shares}}$$

##### 3.2.2.1 Worked Example

A closed-ended Vault in its Investment phase, with `EarlyExitFeeRate = 2000` (2%) and no unrealized loss:

| Quantity           | Before    |
| ------------------ | --------- |
| `AssetsTotal`      | 1,000,000 |
| `AssetsAvailable`  | 150,000   |
| Shares outstanding | 1,000,000 |
| Exchange rate      | 1.000     |

A depositor submits `VaultWithdraw` with `Amount` = 100,000 of the Vault asset:

- $\Delta_{shares} = 100{,}000$ — burned against the pre-fee amount.
- $\Delta_{assets} = 100{,}000$ — the pre-fee value of those shares.
- $F = 100{,}000 \times 0.02 = 2{,}000$.
- $\Delta_{assets}^{paid} = 98{,}000$ — what the depositor receives, and what the Vault needs in `AssetsAvailable`.

| Quantity           | After    |
| ------------------ | -------- |
| `AssetsTotal`      | 902,000  |
| `AssetsAvailable`  | 52,000   |
| Shares outstanding | 900,000  |
| Exchange rate      | 1.002222 |

The 2,000 that was not paid out is spread over the 900,000 shares still in issue, raising every remaining depositor's holding by 0.2222%. The exiting depositor received 98,000 for shares worth 100,000 an instant earlier.

#### 3.2.3 Invariants

Extend parent 3.1.10 invariant 14 under `LendingProtocolV1_2` with `EarlyExitFeeRate`. The field is immutable: if present, it remains equal to its prior value; if absent, it remains absent, except when the transaction creates the entry. This is the same rule [XLS-65.1.1](../65.1/65.1.1-unmodifiable-vault-fields.md) states for the Vault's other identity and configuration fields, and that [XLS-65.1.4](../65.1/65.1.4-closed-ended-vault.md) states for the phase schedule.

Add to parent 3.1.10:

18. `LendingProtocolV1_2`: If `Vault.EarlyExitFeeRate` is present, then `Vault.VaultKind == ClosedEnded` and `Vault.EarlyExitFeeRate <= MAX_EARLY_EXIT_FEE_RATE`. A present value of `0` is valid and is not elided.

Every other parent `Vault` invariant, in particular `AssetsAvailable <= AssetsTotal` and the zero-shares rule that `OutstandingAmount == 0` implies `AssetsTotal == 0` and `AssetsAvailable == 0`, continues to hold unmodified. The full-exit waiver of 3.4.1 is what preserves the zero-shares rule (4.2).

#### 3.2.4 Example JSON

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
  "LossUnrealized": "0",
  "Owner": "rNGHoQwNG753zyfDrib4qDvvswbrtmV8Es",
  "Scale": 6,
  "ShareMPTID": "0000000169F415C9F1AB6796AB9224CE635818AFD74F8175",
  "VaultKind": 1,
  "SubscriptionDate": 711232800,
  "RedemptionDate": 721600800,
  "EarlyExitFeeRate": 2000
}
```

### 3.3 Transaction: `VaultCreate`

#### 3.3.1 Fields

Add `EarlyExitFeeRate` from 3.2.1 to parent 3.2.1 with the same type. It is optional and has no default, and it is permitted only when `VaultKind == ClosedEnded`. Submitting it with a value of `0` is the way to create a closed-ended Vault that permits a mid-term exit free of charge; omitting it is the way to create one that permits none.

#### 3.3.2 Failure Conditions

Append these data-verification checks to parent 3.2.5.1, after the checks added by [XLS-65.1.4](../65.1/65.1.4-closed-ended-vault.md):

6. `LendingProtocolV1_2` is not enabled and `EarlyExitFeeRate` is present. (`temDISABLED`)
7. `EarlyExitFeeRate` is present and `VaultKind` is absent or not `ClosedEnded`, including when the rate is `0`. (`temMALFORMED`)
8. `EarlyExitFeeRate` is greater than `MAX_EARLY_EXIT_FEE_RATE`. (`temMALFORMED`)

Parent 3.2.5.2 is unchanged.

#### 3.3.3 State Changes

Extend parent 3.2.6 step 1:

1. If `EarlyExitFeeRate` is present, copy it from the transaction to the new `Vault` as submitted. 
2. If `EarlyExitFeeRate` is not present, leave field absent.

#### 3.3.4 Invariants

Add to parent 3.2.7:

5. `LendingProtocolV1_2`: A newly created `Vault` carrying `EarlyExitFeeRate` has `VaultKind == ClosedEnded` and `EarlyExitFeeRate <= MAX_EARLY_EXIT_FEE_RATE`. A `Vault` carries the field if and only if the `VaultCreate` that created it carried the field.

### 3.4 Transaction: `VaultWithdraw`

`Amount` keeps its meaning in both denominations and is the **pre-fee** amount: a depositor who submits an asset-denominated `Amount` during Investment receives less than `Amount` whenever the Vault's rate is greater than `0` (Appendix A.2). On a Vault with a rate of `0` they receive `Amount` exactly. Parent 3.6.1 is otherwise unchanged.

#### 3.4.1 Failure Conditions

Replace parent check 14 of 3.6.2.2 — the Investment-phase gate added by [XLS-65.1.4](../65.1/65.1.4-closed-ended-vault.md) — and append one further check:

14. - `SingleAssetVault`: The check does not apply.
    - `LendingProtocolV1_1`: The Vault is closed-ended and `SubscriptionDate < now < RedemptionDate`, where `now` is the parent ledger close time. (`tecTOO_SOON`)
    - `LendingProtocolV1_2`: As above, and additionally `Vault.EarlyExitFeeRate` is absent. A present rate lifts the gate whatever its value. 
15. `LendingProtocolV1_2`: The fee applies and `Vault.AssetsAvailable` is less than $\Delta_{assets}^{paid}$. This replaces the parent liquidity check for a fee-charging withdrawal; it is made against the post-fee payout because only the payout leaves the Vault (4.6). (`tecINSUFFICIENT_FUNDS`)

The fee **applies** when all of the following hold: the Vault is closed-ended, its phase is `Investment`, `Vault.EarlyExitFeeRate` is present and greater than `0`, and $\Delta_{shares}$ is less than `MPTokenIssuance(Vault.ShareMPTID).OutstandingAmount`. Outside Investment, and when no fee applies — including on a Vault whose rate is `0` — $\Delta_{assets}^{paid} = \Delta_{assets}$, check 15 reduces to the parent's, and the withdrawal path is the parent's unmodified. The check on the submitter's share balance is unchanged and is made against $(`tecTOO_SOON`)\Delta_{shares}$, which is computed from the pre-fee amount.

The last clause is the **full-exit waiver**: a withdrawal that burns the Vault's entire outstanding share supply is charged no fee. There are then no remaining shares for a retained fee to accrue to, and retaining it would strand assets in a Vault with no shares in issue — breaking parent `Vault` invariant 7 and blocking `VaultDelete` forever (4.2). This is separate from, and independent of, the parent sole-shareholder waiver of the `LossUnrealized` deduction: a sole shareholder who withdraws only part of their holding gets that waiver and is still charged the fee.

No check rejects a zero post-fee payout, and the parent's two precision-loss checks do not supply one:

- Parent check 11, that the computed share amount is zero, is unchanged. It is evaluated against $\Delta_{shares}$, which comes from the pre-fee amount and is unaffected by the fee.
- Parent check 12 is exempted in one case only: a fee-charging withdrawal whose $\Delta_{assets}^{paid}$ is zero succeeds, burning $\Delta_{shares}$ and transferring nothing. A payout that is non-zero but too small to change the stored `Vault.AssetsTotal` is still rejected with `tecPRECISION_LOSS`, because the Vault would otherwise pay out assets it does not account for. The exemption covers the fee consuming the payout, not the ledger failing to record one (4.3).

#### 3.4.2 State Changes

Parent 3.6.3 is unchanged, with $\Delta_{assets}^{paid}$ of 3.2.2 in place of $\Delta_{assets}$ everywhere an asset amount is decreased or transferred:

1. The submitter's share `MPToken.MPTAmount` and the share `MPTokenIssuance.OutstandingAmount` decrease by $\Delta_{shares}$ — unchanged, and computed from the pre-fee amount.
2. `Vault.AssetsTotal` and `Vault.AssetsAvailable` decrease by $\Delta_{assets}^{paid}$.
3. The Vault pseudo-account's asset balance decreases by $\Delta_{assets}^{paid}$ and the destination's increases by the same, by whichever of the `XRP`, `IOU` or `MPT` paths of parent 3.6.3 applies.

When $\Delta_{assets}^{paid}$ is zero, steps 2 and 3 are no-ops and no transfer is made. In particular no `RippleState` or `MPToken` is created for a destination that does not already hold the Vault asset, and the parent's authorization, freeze and lock checks on the destination still apply, so a zero-payout withdrawal to a frozen destination fails as it would for any other amount. Only step 1 changes the ledger: the shares are burned.

The fee is not a transfer and has no state change of its own. It is the difference between what the burned shares were worth and what the Vault paid out, and it remains in the Vault as part of `AssetsTotal` and `AssetsAvailable`.

#### 3.4.3 Invariants

Add to parent 3.6.4:

8. `LendingProtocolV1_2`: A withdrawal succeeds while the Vault phase is `Investment` only when `Vault.EarlyExitFeeRate` is present. When a fee is charged — the rate is greater than `0` and the withdrawal is not a full exit — `Vault.AssetsTotal` and `Vault.AssetsAvailable` each decrease by $\Delta_{assets}^{paid}$, which is non-negative and strictly less than $\Delta_{assets}$; the Vault's exchange rate after the withdrawal is strictly greater than before; and the outstanding share supply is strictly greater than zero. When the rate is `0`, the withdrawal satisfies every parent `VaultWithdraw` invariant unmodified and leaves the exchange rate unchanged.

This supersedes invariant 7 of [XLS-65.1.4](../65.1/65.1.4-closed-ended-vault.md) under `LendingProtocolV1_2`. The remaining parent `VaultWithdraw` invariants hold against $\Delta_{assets}^{paid}$, relaxed only to admit a zero payout: the Vault's asset balance decreases by a non-negative amount, the destination's increases by the same magnitude subject to the [XLS-65.2](../65.2/README.md) tolerances, and both accounting fields track the Vault's asset-balance decrease. When $\Delta_{assets}^{paid}$ is zero, no asset moves and no balance changes; only the share supply does.

### 3.5 Transaction: `VaultClawback`

Unchanged. `VaultClawback` is never charged the fee, in any phase, and parent 3.7 applies as written (4.5).

### 3.6 RPC: `vault_info`

#### 3.6.1 Response Fields

Add this field to parent 3.9.2. It is present on a closed-ended Vault created with the field, whatever its value, and absent otherwise. Callers MUST NOT interpret its absence as a rate of `0`: absence means no withdrawal is permitted during Investment, whereas `0` means one is permitted free of charge.

| Field Name               | Required? | JSON Type | Description                                                                                                                                              |
| ------------------------ | :-------: | :-------: | -------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `vault.EarlyExitFeeRate` |    No     | `number`  | `LendingProtocolV1_2`: The early-exit fee in 1/10th basis points. |

Example response fragment, showing only the fields this patch and [XLS-65.1.4](../65.1/65.1.4-closed-ended-vault.md) add:

```json
{
  "result": {
    "vault": {
      "LedgerEntryType": "Vault",
      "VaultKind": 1,
      "SubscriptionDate": 711232800,
      "RedemptionDate": 721600800,
      "EarlyExitFeeRate": 2000
    }
  }
}
```

### 3.7 RPC: `ledger_entry`

#### 3.7.1 Response Fields

When `ledger_entry` returns a `Vault`, add `EarlyExitFeeRate` with the meaning and presence rule in 3.6.1. Request fields and failure conditions are unchanged.

## 4. Rationale

### 4.1 Why the fee stays in the Vault

The fee prices an externality. A depositor who exits during Investment consumes uncommitted cash the Vault was holding to fund loans or meet later obligations, and leaves the remaining depositors with a smaller base over which fixed costs and unrealized losses are spread. The parties who bear that cost are the depositors who stay, so they are the parties the fee compensates.

Paying it to the Vault owner or the loan broker would invert the incentive: the owner sets the rate, and if they also collected it they would profit from every early exit and would be motivated to set the rate high and encourage exits. Retaining it leaves the owner no direct claim on it — they benefit only through whatever shares they hold, pro rata with everyone else — while giving the remaining depositors the entire benefit.

Retention is also the cheapest mechanism available. Because the fee is defined as an amount _not withdrawn_ rather than an amount transferred, it needs no new accounting field, no distribution step, and no change to any parent invariant: the Vault's totals follow the payout exactly as they always have, and the rise in share value falls out of the existing exchange-rate arithmetic.

### 4.2 Why the last exiting shareholder pays no fee

A retained fee only means anything if there are shares left for it to accrue to. If a withdrawal burns the entire outstanding share supply, retaining a fee would leave the Vault holding assets against zero shares. That is not merely pointless, it is unrepresentable: parent `Vault` invariant 7 requires `AssetsTotal == 0` and `AssetsAvailable == 0` whenever `OutstandingAmount == 0`, and `VaultDelete` requires an empty Vault — so the retained fee would be permanently stranded and the Vault permanently undeletable. Waiving the fee on a full exit is what keeps this patch's arithmetic inside the parent invariants.

The waiver is narrow by design. It triggers on the share supply reaching zero in a single withdrawal, not on the submitter being the only holder, so a sole holder taking a partial withdrawal still pays. Its exploitability is bounded by its precondition: a holder can only reach it by acquiring every other share in issue (8).

### 4.3 Why the fee rounds up

The fee rounds up to the smallest representable unit of the Vault asset rather than down or to nearest. Rounding down would make the fee zero on any withdrawal small enough that the product underflows the asset's precision, and because withdrawals can be repeated, a depositor could exit an arbitrary position fee-free in small enough slices, bounded only by transaction fees. Rounding up guarantees that any non-zero rate costs at least one unit on any non-zero withdrawal, so slicing strictly increases the total fee paid.

The cost is that the effective rate on a very small withdrawal exceeds the configured rate, up to the extreme case where the fee consumes the whole payout and the depositor receives nothing for the shares burned. That case succeeds rather than failing. Rejecting it would make a withdrawal's outcome depend on whether the fee happened to round to the entire amount, so an otherwise ordinary Vault would reject the smallest withdrawals while accepting larger ones at the same rate, and a 100% Vault would reject every partial exit. One rule for every rate is simpler to implement and simpler to disclose: the depositor pays the stated rate, and at a high enough rate that means receiving nothing (4.4).

### 4.4 Why the cap is 100%

The field reuses the rate convention of [XLS-66](../../XLS-0066-lending-protocol/README.md) — 1/10th basis points, the same unit as `LoanBroker.ManagementFeeRate` — so that one rate convention covers the lending specifications. It does not reuse the type: 100% is `100000` in this unit, which exceeds the 65,535 a `UINT16` can hold, so `EarlyExitFeeRate` is a `UINT32`. That is the only reason for the wider type; the unit, and therefore every rate a `ManagementFeeRate` can express, is identical.

The cap is set at the arithmetic limit of the mechanism rather than at a judgement about reasonable pricing. The fee is a fraction of the withdrawal that is not paid out, so 100% is the largest fraction that means anything: above it the payout would be negative. Term credit funds typically charge 1–5% to exit early, so the whole range above a few thousand 1/10ths of a basis point is already far outside normal practice, and the protocol has no basis on which to pick a lower number that is anything but arbitrary.

A rate at or very near 100% is accepted and is dangerous rather than merely degenerate. The fee consumes the whole payout, so a depositor who exits early burns their shares and receives nothing or nearly nothing (3.2.2). No error is returned: the transaction succeeds and the position is gone. This is deliberate. The rate is a price the owner sets and the depositor accepts by subscribing, and the protocol's role is to make that price known in advance rather than to rule on which prices are too high. What protects a depositor is therefore not the ceiling but disclosure and immutability. The rate is fixed at creation and readable from the ledger before any capital is committed, so reaching this outcome requires subscribing to a Vault whose posted terms say so and then choosing to exit early anyway (8).

An owner who wants no early exit should omit the field rather than price it out of reach. Omission says so directly, costs nothing to verify, and cannot be misread by a depositor who did not check the rate (4.7).

### 4.5 Why `VaultClawback` is not charged

`VaultClawback` is the asset issuer forcibly removing assets from a depositor's position; the depositor is not choosing to exit. Charging an early-exit fee on it would transfer value from the clawed-back holder to the remaining holders on the strength of a decision neither made, and would let an issuer raise the Vault's share value at a chosen holder's expense. The clawback path is therefore untouched, in every phase.

### 4.6 Why liquidity is checked against the post-fee payout

Only the payout leaves the Vault. The retained fee stays in `AssetsAvailable`, so requiring the Vault to hold the full pre-fee amount in uncommitted cash would reject withdrawals the Vault can plainly satisfy — for a 2% fee, any request between 98% and 100% of available cash. Checking the amount that actually moves is both correct and the least surprising rule: the pre-fee and post-fee thresholds differ by exactly the fee.

### 4.7 Why an absent rate and a zero rate differ

Two facts about a closed-ended Vault need to be expressible, and they are independent: whether it permits a mid-term exit at all, and what that exit costs. A single number cannot carry both unless one value is overloaded, and every overload loses something real. If `0` meant "no early exit", a Vault could not offer a free mid-term exit — an ordinary arrangement for a Vault whose term is a plan rather than a promise. If `0` meant "free early exit" and absence were read as `0`, every closed-ended Vault created before this amendment would silently start permitting free mid-term withdrawals, breaking the term its depositors subscribed to.

Using presence as the switch keeps both meanings and makes the conservative one the default. A Vault created without the field behaves exactly as [XLS-65.1.4](../65.1/65.1.4-closed-ended-vault.md) describes, so no existing Vault, and no client that has never heard of the field, changes behavior. Permitting a mid-term exit is opt-in, and it is opt-in in one place: the owner writes the field, at a rate of their choosing, including `0`.

The cost is that the field cannot be elided when it is `0`. A zero-rate Vault carries and serialises an extra `UINT32`, and clients MUST distinguish an absent field from a present `0` (3.6.1) rather than defaulting one to the other, which is the opposite of the convention most `Vault` fields follow. The alternative was a rule that cannot be stated at all, so the field carries its own presence.

### 4.8 Alternatives considered

- **A fee that decays towards `RedemptionDate`.** Economically attractive — the cost of an early exit really does fall as the term runs out — but it requires a second stored parameter and a schedule, makes the payout a function of the ledger close time, and turns a one-line disclosure into a curve a depositor has to compute. A flat rate is a single immutable number a depositor can read off the ledger, and an owner who wants a decaying profile can approximate it with a sequence of Vaults.
- **Making the rate mutable via `VaultSet`.** Rejected for the same reason `SubscriptionDate` and `RedemptionDate` are immutable: the rate is a term depositors rely on when they subscribe. A mutable rate could be raised to trap capital after it is committed, or dropped to zero to let a favoured holder exit cheaply.
- **Paying the fee to the Vault owner or loan broker as a cover top-up.** Rejected; see 4.1.
- **Guaranteeing the exit by forcing loan liquidation.** Out of scope, and not achievable: loans in this protocol cannot be called early by the Vault. Early exit is best-efforts against uncommitted cash by construction.

## 5. Backwards Compatibility

The feature is inert unless `LendingProtocolV1_2` is enabled; ledger entries and transactions are unchanged for nodes that have not activated it. Because an enabled amendment is never disabled, a Vault carrying an `EarlyExitFeeRate` always has a phase to apply it in.

- **Open-ended Vaults are unaffected.** They cannot carry `EarlyExitFeeRate` (3.3.2), have no phases, and their withdrawal behavior is untouched.
- **Existing closed-ended Vaults are unaffected.** `EarlyExitFeeRate` is set at creation only, so every Vault created before the amendment has no rate and its Investment-phase withdrawals continue to be rejected with `tecTOO_SOON`. [XLS-65.1.4](../65.1/65.1.4-closed-ended-vault.md)'s behavior is the default both before and after this amendment.
- **Serialisation is compatible.** The new field is optional, so existing serialised Vaults deserialise unchanged. It is not elided at `0`, so a Vault that permits a free early exit carries the field explicitly and is distinguishable on the wire from one that permits none (4.7).
- **The parent's zero-payout rejection is conditioned, not removed.** A fee-charging withdrawal whose post-fee payout is zero is exempt from parent check 12 of 3.6.2.2 (3.4.1). Only a Vault carrying an `EarlyExitFeeRate` can charge a fee, and no Vault created before this amendment carries one, so the exemption cannot change the outcome of any withdrawal on an existing Vault.
- **Integrators must read the field before quoting a withdrawal.** A client that computes an expected payout from `Amount` and the exchange rate alone will over-quote by the fee for a withdrawal made during Investment. The field is exposed by both `vault_info` and `ledger_entry` (3.6, 3.7).

## 6. Test Plan

### 6.1 `VaultCreate`

- A closed-ended creation with a valid non-zero `EarlyExitFeeRate` succeeds and stores the field.
- Creation with `EarlyExitFeeRate == 0` succeeds and **does** store the field, with the value `0`; the resulting Vault is distinguishable — on the ledger, over `vault_info` and over `ledger_entry` — from one created without the field.
- Creation with `EarlyExitFeeRate == MAX_EARLY_EXIT_FEE_RATE` is accepted; one greater returns `temMALFORMED`.
- Creation of an open-ended Vault, or one with an absent `VaultKind`, carrying `EarlyExitFeeRate` returns `temMALFORMED`, including when the rate is `0`.
- Before `LendingProtocolV1_2`, any `VaultCreate` carrying `EarlyExitFeeRate` returns `temDISABLED`.

### 6.2 `VaultSet`

- A `VaultSet` carrying `EarlyExitFeeRate` is rejected at deserialisation, for both closed-ended and open-ended Vaults, with and without the amendment.

### 6.3 `VaultWithdraw` during Investment

- With a non-zero rate, an asset-denominated withdrawal succeeds; the payout equals $\Delta_{assets} - F$, the shares burned equal $\Delta_{shares}$ computed from the pre-fee amount, and `AssetsTotal` and `AssetsAvailable` each decrease by the payout only.
- With a non-zero rate, a share-denominated withdrawal (redeem) succeeds and is charged the same fee.
- With an absent rate, a withdrawal returns `tecTOO_SOON`, in both denominations and with and without a `Destination`.
- With a rate of `0`, a withdrawal succeeds and is charged nothing: the payout equals $\Delta_{assets}$, `AssetsTotal` and `AssetsAvailable` decrease by $\Delta_{assets}$, the exchange rate is unchanged, and the result matches the same withdrawal made on an open-ended Vault with the same state.
- The exchange rate after a fee-charging withdrawal is strictly higher than before, and a second depositor redeeming an identical share amount immediately afterwards receives strictly more assets than the first.
- With a rate of `MAX_EARLY_EXIT_FEE_RATE`, a partial withdrawal succeeds, burns $\Delta_{shares}$, transfers nothing, and leaves both `AssetsTotal` and `AssetsAvailable` unchanged; the exchange rate rises and the remaining holders absorb the whole forfeited position.
- The worked example of 3.2.2.1 reproduces exactly, including both post-state totals.
- A withdrawal with a `Destination` behaves identically: the destination receives the post-fee amount.
- A fee-charging withdrawal on a Vault with a non-zero `LossUnrealized` applies the fee to the post-`LossUnrealized` payout.

### 6.4 `VaultWithdraw` outside Investment

- A withdrawal during Subscription charges no fee, even with a non-zero rate configured.
- A withdrawal during Redemption charges no fee.
- Boundary: a withdrawal at `now == SubscriptionDate` charges no fee; at `now == SubscriptionDate + 1` it is charged. A withdrawal at `now == RedemptionDate` charges no fee; at `now == RedemptionDate - 1` it is charged.
- Withdrawals from open-ended Vaults are unaffected.

### 6.5 Liquidity

- A withdrawal whose post-fee payout exceeds `AssetsAvailable` returns `tecINSUFFICIENT_FUNDS`.
- Boundary: a withdrawal whose post-fee payout equals `AssetsAvailable` succeeds, even though its pre-fee amount exceeds `AssetsAvailable`.
- A Vault whose cash is fully deployed into loans rejects every early exit, and accepts them again as loan payments restore `AssetsAvailable`.
- An early exit does not affect any outstanding `Loan` or the broker's `CoverAvailable`.

### 6.6 Rounding and precision

- The fee is rounded up: a withdrawal whose exact fee falls between two representable amounts is charged the larger.
- A withdrawal small enough that the rounded-up fee equals the pre-fee amount succeeds, burns $\Delta_{shares}$, transfers nothing, and leaves `AssetsTotal` and `AssetsAvailable` unchanged.
- A withdrawal whose post-fee payout is non-zero but too small to change the stored `AssetsTotal` still returns `tecPRECISION_LOSS`; the zero-payout exemption of 3.4.1 does not extend to it.
- Splitting a withdrawal into `n` pieces costs at least as much in total fees as taking it in one, for each of `XRP`, `IOU` and `MPT` assets.
- The tests are run for all three asset types and across the `Scale` range.

### 6.7 Full-exit waiver

- A withdrawal during Investment that burns the entire outstanding share supply is charged no fee, empties the Vault (`AssetsTotal == 0`, `AssetsAvailable == 0`), and the Vault can then be deleted.
- A sole shareholder taking a partial withdrawal during Investment **is** charged the fee, and the parent sole-shareholder `LossUnrealized` waiver still applies to the pre-fee amount.
- With two holders, a withdrawal that burns all of one holder's shares but not the whole supply is charged the fee.

### 6.8 `VaultClawback`

- A clawback during Investment from a Vault with a non-zero rate charges no fee; the assets removed and shares burned match the parent exactly.

### 6.9 RPC surface

- `vault_info` and `ledger_entry` return `EarlyExitFeeRate` for every Vault created with the field, including when its value is `0`, and omit it for every Vault created without it.
- The two RPC responses for a zero-rate Vault and a no-rate Vault differ only in the presence of this field.

### 6.10 Invariant checks

- An invariant check asserts 3.3.4 on `VaultCreate` and 3.4.3 on `VaultWithdraw`.
- The immutability rule of 3.2.3 is asserted on every transaction that modifies a `Vault`: a test that changes `EarlyExitFeeRate` on an existing Vault, and one that adds it to a Vault that lacks it, both expect the check to fire.
- A test asserts that no `VaultWithdraw` can leave a Vault with zero outstanding shares and non-zero `AssetsTotal`.

### 6.11 End-to-end

- A full lifecycle with several depositors: subscribe, enter Investment, originate loans, one depositor exits early and pays the fee, remaining depositors' share value rises, loans repay, Redemption opens, the remaining depositors redeem and receive their enlarged share. The sum of all payouts plus the final Vault balance reconciles against all deposits plus interest.
- The same lifecycle on a Vault with no rate configured confirms [XLS-65.1.4](../65.1/65.1.4-closed-ended-vault.md)'s behavior is unchanged: every mid-term withdrawal is rejected.
- The same lifecycle on a Vault with a rate of `0` permits every mid-term withdrawal that `AssetsAvailable` can fund, charges nothing, and leaves the remaining depositors' share value exactly where an open-ended Vault would.

## 7. Reference Implementation

_TBD_

## 8. Security Considerations

- **The fee is not a liquidity guarantee.** An early exit draws on `Vault.AssetsAvailable` only. A Vault with its capital fully deployed cannot honour any early exit, whatever the rate, and a depositor MUST NOT treat a configured rate as a redemption right. Under the `first-come-first-serve` withdrawal policy the available cash goes to whoever asks first, so in a stressed Vault early exit is a race. Depositors who need certain liquidity must wait for `RedemptionDate`.
- **Early exits compete with lending.** Cash consumed by an early exit is cash unavailable to `LoanSet`. An owner who configures a rate should expect the Vault's deployable capital to be less predictable than in a Vault without one, and size its cash buffer accordingly. Outstanding loans are never at risk: `AssetsAvailable` is uncommitted cash by definition, and an early exit cannot reach capital already lent out or the broker's first-loss cover.
- **A high rate destroys the position of whoever exits early.** The cap is the arithmetic limit, so an owner may configure a rate of 100%. A depositor who then withdraws during Investment burns their shares and receives nothing, and the transaction succeeds rather than failing (3.2.2, 4.4). Nothing in the protocol warns them. A depositor MUST read the rate before subscribing and treat an unreasonable one as a reason not to, and a client MUST compute and display the post-fee payout, which may be zero, before submitting a `VaultWithdraw` during Investment. Because the rate is immutable and readable over `vault_info` and `ledger_entry` from the moment the Vault exists, this is a term a depositor can always check in advance.
- **The owner cannot extract the fee, but does share in it.** The fee is never transferred, so no owner or broker action can capture it. An owner who holds shares nonetheless benefits from every early exit pro rata with the other remaining holders, which is a mild incentive to set a high rate and to encourage exits. The cap does not bound this, since a 100% rate is permitted. Immutability and disclosure do: the rate is fixed and readable before any depositor subscribes, so an owner cannot raise it once deposits are in.
- **The rate cannot be changed after capital is committed.** `EarlyExitFeeRate` is immutable (3.2.3) and absent from `VaultSet`'s format, so an owner cannot raise it to trap committed capital, lower it to let a favoured holder exit cheaply, or add it to a Vault that was advertised without one.
- **Adverse selection is reduced, not eliminated.** A depositor who learns of an incoming loss can still exit during Investment ahead of its realisation. The `LossUnrealized` mechanism of the parent already prices known impairment into the payout, and the fee adds a further cost to leaving early, but neither addresses a loss that has not yet been marked. This is the same exposure [XLS-65.1.4](../65.1/65.1.4-closed-ended-vault.md) has in its Redemption phase; the early-exit fee narrows the window's profitability rather than closing it.
- **The full-exit waiver is exploitable only by buying out the Vault.** A holder who accumulates 100% of the shares in issue can exit without a fee (3.4.1). Reaching that position requires acquiring every other share on terms the other holders accept, which costs more than the fee it avoids, and the waiver is required to keep the Vault's assets from being stranded (4.2). Share MPTs are transferable unless the Vault was created with `tfVaultShareNonTransferable`, so this path exists on any transferable-share Vault.
- **Fee rounding favours the Vault, by a bounded amount.** The rounded-up fee exceeds the configured rate by less than one representable unit of the Vault asset per withdrawal. This closes the dust-splitting bypass (4.3) at the cost of a sub-unit overcharge. A withdrawal small enough that the rounded-up fee equals the whole amount pays out nothing and still burns the shares, so slicing a position into dust destroys it rather than escaping the fee.
- **No new time or trust dependency.** The fee is applied on the basis of the Vault's phase, which is derived from the consensus ledger close time and two immutable dates, and its amount depends only on stored ledger values.

# Appendix

## Appendix A: FAQ

### A.1 Why does the fee stay in the Vault instead of going to the Vault owner or the loan broker?

Because the depositors who stay are the ones who bear the cost of someone else leaving early. Paying the fee to the owner would also make the party who sets the rate the party who collects it. See 4.1.

### A.2 If I ask to withdraw 100,000, do I receive 100,000?

Not during the Investment phase, unless the Vault's rate is `0`, in which case you receive 100,000 exactly. Otherwise `Amount` is the pre-fee amount: shares are burned as if you withdrew 100,000, and you receive 100,000 less the fee. To receive a specific amount $X$ after the fee, request

$$\text{Amount} = \frac{X}{1 - \phi}$$

rounded up, where $\phi$ is the rate as a fraction (3.2.1) — for a 2% rate, ask for 102,041 to receive 100,000. At a rate of 100% no `Amount` produces a positive payout, and the withdrawal burns shares for nothing (A.12). Outside the Investment phase there is no fee and `Amount` behaves exactly as it does today.

### A.3 Can the owner add, remove or change the fee after the Vault is created?

No. `EarlyExitFeeRate` is set by `VaultCreate` and is immutable (3.2.3). It is not part of `VaultSet`'s transaction format, so a `VaultSet` carrying it fails at deserialisation. A Vault created without a rate can never gain one, a Vault created with a rate of `0` can never charge for an exit, and a Vault created with a rate can never drop or raise it — the choice is irreversible in every direction, as with `VaultKind` and the two phase dates.

### A.4 Why is the last depositor to exit not charged?

There would be no one left to receive the fee, and the retained assets would be stranded in a Vault with no shares in issue, which the parent forbids and which would block `VaultDelete` permanently. See 4.2.

### A.5 Does a configured fee mean I can always exit early?

No. The withdrawal still needs `Vault.AssetsAvailable` to cover the payout, and capital that has been lent out is not available. If the Vault is holding no uncommitted cash, the withdrawal fails with `tecINSUFFICIENT_FUNDS` no matter what you are willing to pay. Early exit is best-efforts.

### A.6 Why is the rate flat rather than decaying as `RedemptionDate` approaches?

A flat rate is one immutable number a depositor can read off the ledger before subscribing. A decaying rate needs a second parameter and a schedule, and makes the payout depend on when within the term you ask. See 4.8.

### A.7 Does the fee apply to `VaultClawback`?

No. Clawback is compelled by the asset issuer, not chosen by the depositor, and charging it would let an issuer raise the Vault's share value at a chosen holder's expense. See 4.5.

### A.8 I exited early and now want back in. Can I re-deposit?

No. `VaultDeposit` is rejected for the whole Investment phase, and that is unchanged by this patch. An early exit is one-way for the remainder of the term.

### A.9 Does an early exit affect outstanding loans or the loan broker's first-loss capital?

No. It moves only uncommitted cash out of the Vault. No `Loan` object, no `LoanBroker.DebtTotal`, and no `CoverAvailable` is touched, and the broker's cover requirement is computed from `DebtTotal`, which an early exit does not change.

### A.10 Can I set the fee on an open-ended Vault?

No. `VaultCreate` returns `temMALFORMED` if `EarlyExitFeeRate` is present on a Vault that is not closed-ended (3.3.2). An open-ended Vault has no Investment phase, so there is no period during which the fee could apply — its depositors can already withdraw at any time.

### A.11 What is the difference between no `EarlyExitFeeRate` and `EarlyExitFeeRate = 0`?

Everything. The field's presence is what permits a withdrawal during Investment; its value is only the price.

- **Absent:** no early exit at any price. `VaultWithdraw` during Investment returns `tecTOO_SOON`, exactly as it does today.
- **Present and `0`:** early exit is permitted and free. The withdrawal behaves like any other, subject as always to `AssetsAvailable`.
- **Present and non-zero:** early exit is permitted and charged that rate.

A zero rate is stored rather than elided, so the two cases are distinguishable on the wire and over both RPCs. Do not default a missing field to `0`. See 4.7.

### A.12 Can the fee really be 100%?

Yes, and you should treat such a Vault as one you cannot exit from without losing the position. At a rate of `100000` an early exit burns your shares and pays you nothing. The transaction succeeds; it is not rejected, and nothing warns you (3.2.2). The cap sits at the arithmetic limit because that is the only non-arbitrary place for it, not because rates anywhere near it are sensible. In practice an early-exit fee is a few percent, and the rate is on the ledger before you subscribe. See 4.4.
