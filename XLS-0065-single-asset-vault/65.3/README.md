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

Whether a mid-term exit is possible and what it costs are two separate decisions, and the field expresses both. An owner who sets no rate at all gets the closed-ended Vault unchanged, with no early exit at any price. An owner who sets a rate of `0` permits mid-term exits and charges nothing for them, which is the right configuration for a Vault whose term is a plan rather than a promise. Absence is the conservative default, so every Vault created before this amendment keeps its meaning (3.2.1).

Fixing the rate at creation and exposing it on the ledger means a depositor knows the exit terms before committing capital, in the same way they know `SubscriptionDate` and `RedemptionDate`.

## 3. Specification

This patch changes the parent [XLS-65](../README.md) sections named below, and the sections of [XLS-65.1.4](../65.1/65.1.4-closed-ended-vault.md) it identifies. All other parent behavior is unchanged. `LendingProtocolV1_1` is a hard prerequisite: `EarlyExitFeeRate` may only be set on a closed-ended Vault, and the only behavior it changes is the Investment-phase gate that [XLS-65.1.4](../65.1/65.1.4-closed-ended-vault.md) introduces.

### 3.1 Protocol Constants

| Constant                  | Value    | Meaning                                                                                                                                                                        |
| ------------------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `MAX_EARLY_EXIT_FEE_RATE` | `100000` | Inclusive upper bound on `EarlyExitFeeRate`, in 1/10th basis points. Equivalent to 100%. A rate of exactly this value is accepted; an early exit at that rate pays out nothing and still burns the shares (3.4.2). |

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
| `0 < rate <= MAX_EARLY_EXIT_FEE_RATE` | Permitted, and charged the fee of 3.4.2       |

The field is stored only on a Vault with `VaultKind == ClosedEnded`; `VaultCreate` rejects it on any other Vault, including when the rate is `0` (3.3.2).

The rate is expressed in 1/10th basis points, matching the rate convention of [XLS-66](../../XLS-0066-lending-protocol/README.md): a value of `1` is 1/10 bps, or 0.001%, and `100000` is 100%. Valid values are `0` to `MAX_EARLY_EXIT_FEE_RATE` inclusive. As a fraction, the rate is:

$$\phi = \frac{\text{EarlyExitFeeRate}}{100000}$$

#### 3.2.2 Invariants

Starting from `LendingProtocolV1_2`:

1. `EarlyExitFeeRate` is immutable. If present, it keeps its value; if absent, it stays absent. Only the transaction that creates the `Vault` may set it.
2. `EarlyExitFeeRate` never exceeds `MAX_EARLY_EXIT_FEE_RATE`.
3. Only a `Vault` with `VaultKind == ClosedEnded` may have an `EarlyExitFeeRate`.

#### 3.2.3 Example JSON

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

No changes.

### 3.4 Transaction: `VaultWithdraw`

`Amount` keeps its meaning in both denominations and is the **pre-fee** amount: a depositor who submits an asset-denominated `Amount` during Investment receives less than `Amount` whenever the Vault's rate is greater than `0` (Appendix A.1). On a Vault with a rate of `0` they receive `Amount` exactly. Parent 3.6.1 is otherwise unchanged.

#### 3.4.1 Failure Conditions

Replace parent check 14 of 3.6.2.2 — the Investment-phase gate added by [XLS-65.1.4](../65.1/65.1.4-closed-ended-vault.md) — and append one further check:

14. - `SingleAssetVault`: The check does not apply.
    - `LendingProtocolV1_1`: The Vault is closed-ended and `SubscriptionDate < now < RedemptionDate`, where `now` is the parent ledger close time. (`tecTOO_SOON`)
    - `LendingProtocolV1_2`: As above, and `Vault.EarlyExitFeeRate` is absent. (`tecTOO_SOON`)
15. `LendingProtocolV1_2`: $F$ of 3.4.2 is greater than `0` and `Vault.AssetsAvailable` is less than the payout $\Delta_{assets}^{paid}$. This supersedes parent checks 10.2 and 10.4, which measure `AssetsAvailable` against the pre-fee amount. Only the payout leaves the Vault, so the pre-fee test would reject withdrawals the Vault can fund (4.4). Parent checks 10.1 and 10.3, on the submitter's share balance, are unchanged and are made against $\Delta_{shares}$. (`tecINSUFFICIENT_FUNDS`)

No check rejects a zero payout. The parent's two precision-loss checks apply as follows:

- Parent check 11, that the computed share amount is zero, is unchanged. It is evaluated against $\Delta_{shares}$, which comes from the pre-fee amount and is unaffected by the fee.
- Parent check 12 is exempted in one case only: a withdrawal whose $\Delta_{assets}^{paid}$ is zero succeeds, burning $\Delta_{shares}$ and transferring nothing. A payout that is non-zero but too small to change the stored `Vault.AssetsTotal` is still rejected with `tecPRECISION_LOSS`, because the Vault would otherwise pay out assets it does not account for.

#### 3.4.2 State Changes

Compute $\Delta_{shares}$ and $\Delta_{assets}$ exactly as in parent 3.6.3. Then:

1. Transfer $\Delta_{assets}^{paid} = \Delta_{assets} - F$ from the Vault to the destination, decreasing `Vault.AssetsTotal` and `Vault.AssetsAvailable` by the same amount, where:
   - $F = 0$ if the Vault is not in its Investment phase, if `Vault.EarlyExitFeeRate` is `0`, or if the withdrawal burns the Vault's entire outstanding share supply (the **full-exit waiver**, 4.2);
   - otherwise $F = \lceil \Delta_{assets} \times \phi \rceil$, rounded **up** to the smallest representable unit of `Vault.Asset` (4.3).
2. Burn $\Delta_{shares}$ as in the parent.

##### 3.4.2.1 Worked Example

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

#### 3.4.3 Invariants

Amend parent 3.6.4 under `LendingProtocolV1_2`:

1. Supersedes invariant 1, which requires the Vault pseudo-account's asset balance to decrease by a positive amount. A withdrawal must not increase the Vault pseudo-account's asset balance.
2. Supersedes invariant 2, which requires the destination's asset balance to increase. A withdrawal must not decrease the destination's asset balance.
3. Either balance is unchanged only when $\Delta_{assets}^{paid}$ is zero. Invariants 3 and 6 hold as written, with both sides zero in that case.
4. The Investment-phase rule of [XLS-65.1.4](../65.1/65.1.4-closed-ended-vault.md) §3.5.1, that no `VaultWithdraw` succeeds during `Investment`, applies only when `Vault.EarlyExitFeeRate` is absent.

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

An early exit consumes uncommitted cash and shrinks the base over which the remaining depositors bear costs and unrealized losses. The fee compensates them. Paying it to the owner or the loan broker would reward the party that sets the rate for every exit. Retention also needs no new field and no transfer. Its only effect on the parent invariants is to admit a zero payout (3.4.3).

### 4.2 Why the last exiting shareholder pays no fee

A retained fee needs remaining shares to accrue to. If a withdrawal burns the whole share supply, the fee would leave assets against zero shares, which parent `Vault` invariant 7 forbids and which would make the Vault undeletable. The waiver applies when the share supply reaches zero, not when the submitter is the only holder, so a sole holder taking a partial withdrawal still pays (8).

### 4.3 Why the fee rounds up

Rounding down would make the fee zero on withdrawals small enough to underflow the asset's precision, so a depositor could exit fee-free in slices. Rounding up makes every non-zero withdrawal cost at least one unit. A withdrawal whose fee rounds to the whole amount succeeds and pays out nothing. Rejecting it would make the outcome depend on rounding, and a 100% Vault would reject every partial exit.

### 4.4 Why liquidity is checked against the post-fee payout

Only the payout leaves the Vault. Checking the pre-fee amount would reject withdrawals the Vault can satisfy.

## 5. Backwards Compatibility

The feature is inert unless `LendingProtocolV1_2` is enabled; ledger entries and transactions are unchanged for nodes that have not activated it. Because an enabled amendment is never disabled, a Vault carrying an `EarlyExitFeeRate` always has a phase to apply it in.

- **Open-ended Vaults are unaffected.** They cannot carry `EarlyExitFeeRate` (3.3.2), have no phases, and their withdrawal behavior is untouched.
- **Existing closed-ended Vaults are unaffected.** `EarlyExitFeeRate` is set at creation only, so every Vault created before the amendment has no rate and its Investment-phase withdrawals continue to be rejected with `tecTOO_SOON`. [XLS-65.1.4](../65.1/65.1.4-closed-ended-vault.md)'s behavior is the default both before and after this amendment.
- **Serialisation is compatible.** The new field is optional, so existing serialised Vaults deserialise unchanged. It is not elided at `0`, so a Vault that permits a free early exit carries the field explicitly and is distinguishable on the wire from one that permits none (3.2.1).
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
- The worked example of 3.4.2.1 reproduces exactly, including both post-state totals.
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
- The immutability rule of 3.2.2 is asserted on every transaction that modifies a `Vault`: a test that changes `EarlyExitFeeRate` on an existing Vault, and one that adds it to a Vault that lacks it, both expect the check to fire.
- A test asserts that no `VaultWithdraw` can leave a Vault with zero outstanding shares and non-zero `AssetsTotal`.

### 6.11 End-to-end

- A full lifecycle with several depositors: subscribe, enter Investment, originate loans, one depositor exits early and pays the fee, remaining depositors' share value rises, loans repay, Redemption opens, the remaining depositors redeem and receive their enlarged share. The sum of all payouts plus the final Vault balance reconciles against all deposits plus interest.
- The same lifecycle on a Vault with no rate configured confirms [XLS-65.1.4](../65.1/65.1.4-closed-ended-vault.md)'s behavior is unchanged: every mid-term withdrawal is rejected.
- The same lifecycle on a Vault with a rate of `0` permits every mid-term withdrawal that `AssetsAvailable` can fund, charges nothing, and leaves the remaining depositors' share value exactly where an open-ended Vault would.

## 7. Reference Implementation

_TBD_

## 8. Security Considerations

- **Permitting early exit makes a run possible during Investment.** Without a rate, no capital can leave a closed-ended Vault mid-term. With one, every holder can draw on `Vault.AssetsAvailable`, and under the `first-come-first-serve` policy the cash goes to whoever asks first. The fee does not stop a run. It only makes each exit cost its holder the configured rate. Depositors who need certain liquidity must wait for `RedemptionDate`.
- **A high rate destroys the position of whoever exits early.** An owner may configure a rate of 100%. A depositor who then withdraws during Investment burns their shares and receives nothing, and the transaction succeeds rather than failing (3.4.2). A client MUST compute and display the post-fee payout, which may be zero, before submitting a `VaultWithdraw` during Investment.
- **The owner cannot extract the fee, but does share in it.** The fee is never transferred, so no owner or broker action can capture it. An owner who holds shares nonetheless benefits from every early exit pro rata with the other remaining holders, which is a mild incentive to set a high rate. Immutability (3.2.2) bounds this. The rate is fixed and readable before any depositor subscribes, so an owner cannot raise it once capital is committed or lower it to let a favoured holder exit cheaply.
- **Permitting early exit introduces adverse selection during Investment.** A depositor who learns of an incoming loss can exit ahead of its realisation. The parent's `LossUnrealized` mechanism prices known impairment into the payout, and the fee adds a cost to leaving, but neither addresses a loss that has not yet been marked. A Vault without a rate has no such exposure during Investment.
- **The full-exit waiver is reachable only by holding every share.** A holder who accumulates 100% of the shares in issue exits without a fee (3.4.2). Reaching that position requires every other holder to sell, and once it is reached there is no remaining holder for a fee to compensate, so the waiver forfeits nothing (4.2). Share MPTs are transferable unless the Vault was created with `tfVaultShareNonTransferable`, so the path exists on any transferable-share Vault.

# Appendix

## Appendix A: FAQ

### A.1 If I ask to withdraw 100,000, do I receive 100,000?

Not during the Investment phase on a Vault with a non-zero rate. `Amount` is the pre-fee amount: shares are burned as if you withdrew 100,000, and you receive 100,000 less the fee. To receive a specific amount $X$ after the fee, request

$$\text{Amount} = \left\lceil \frac{X}{1 - \phi} \right\rceil$$

where $\phi$ is the rate as a fraction (3.2.1). At a 2% rate, request 102,041 to receive 100,000. At a rate of 100% no `Amount` produces a positive payout (3.4.2).

### A.2 Why is the rate flat rather than decaying as `RedemptionDate` approaches?

A flat rate is one immutable number a depositor can read off the ledger before subscribing. A decaying rate needs a second parameter and a schedule, and makes the payout depend on when within the term you ask.

### A.3 Does the fee apply to `VaultClawback`?

No. Clawback is compelled by the asset issuer, not chosen by the depositor, and charging it would let an issuer raise the Vault's share value at a chosen holder's expense.

### A.4 I exited early and now want back in. Can I re-deposit?

No. `VaultDeposit` is rejected for the whole Investment phase, and that is unchanged by this patch. An early exit is one-way for the remainder of the term.

### A.5 Does an early exit affect outstanding loans or the loan broker's first-loss capital?

No. It moves only uncommitted cash out of the Vault. No `Loan`, `LoanBroker.DebtTotal` or `CoverAvailable` is touched, and the broker's cover requirement is computed from `DebtTotal`.
