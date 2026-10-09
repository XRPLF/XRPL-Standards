<pre>
  xls: 65.4
  title: Closed-Ended Vault Early-Exit Fee
  description: Adds an optional, immutable early-exit fee that lets a closed-ended Vault permit withdrawals during Investment, with the fee retained in the Vault
  author: Jingchen Wu (@a1q123456), Vito Tumas <vtumas@ripple.com>
  proposal-from: https://github.com/XRPLF/XRPL-Standards/discussions/643
  requires: XLS-65.1.4, XLS-65.2, XLS-65.3
  status: Draft
  category: Amendment
  created: 2026-09-15
  updated: 2026-10-09
</pre>

# 65.4 Closed-Ended Vault Early-Exit Fee

## 1. Abstract

Under the `LendingProtocolV1_2` amendment, a closed-ended Vault may define an optional immutable field at creation: `EarlyExitFeeRate`. This field controls whether depositors can withdraw funds during the Investment phase and establishes the fee rate charged.

Key properties of this feature include:

- **Default behavior (field absent):** The Vault preserves the behavior defined in [XLS-65.1.4](../65.1/65.1.4-closed-ended-vault.md). All `VaultWithdraw` transactions during the Investment phase are rejected with `tecTOO_SOON`.
- **Zero-percent fee (`EarlyExitFeeRate == 0`):** Depositors may withdraw during the Investment phase without incurring a fee.
- **Standard fee (`0 < EarlyExitFeeRate < 100%`):** Depositors may withdraw during the Investment phase. The specified percentage is deducted from the pre-fee withdrawal amount. If the rounded fee consumes the entire withdrawal amount, the withdrawal burns the requested shares and transfers no assets, as at a 100% rate.
- **Maximum fee (`EarlyExitFeeRate == 100%`):** Unless the withdrawal burns the entire outstanding share supply under the full-exit waiver, a withdrawal at a 100% fee rate burns the requested shares and transfers no assets.
- **Full-exit waiver:** A withdrawal that burns the entire outstanding share supply pays no fee (3.4.3).
- **Fee retention:** Retained fees remain in the Vault. Because shares are burned against the pre-fee amount while only the post-fee amount leaves the Vault, the difference remains in the Vault and raises the value of every remaining share.
- **Liquidity requirements:** Early withdrawals draw on `Vault.AssetsAvailable` and remain subject to available liquidity.
- **Scope:** Open-ended Vaults and closed-ended Vaults outside the Investment phase are unaffected.

## 2. Motivation

A closed-ended Vault locks capital for a fixed term, providing the operator with predictable capital to deploy. Under [XLS-65.1.4](../65.1/65.1.4-closed-ended-vault.md), this lock admits no exceptions:

- Depositors who need liquidity mid-term cannot exit.
- Operators cannot permit early withdrawals, even on terms that protect remaining depositors.

An early-exit fee makes mid-term withdrawals a configurable setting established at creation:

- **Capital protection:** All collected exit fees remain inside the Vault and accrue directly to remaining depositors, compensating them for consumed liquidity and shortened investment terms.
- **Predictability:** Setting an immutable rate at creation allows depositors to evaluate exit terms before committing capital, similar to `SubscriptionDate` and `RedemptionDate`.

The field expresses both whether a mid-term exit is possible and what it costs are two separate decisions:

- An owner who sets no rate preserves strict closed-ended behavior, disallowing early exit entirely.
- An owner who sets a rate of `0` permits mid-term exits free of charge, accommodating Vaults where the term is flexible.
- An owner who sets a positive rate permits mid-term exits while compensating remaining depositors.
- Absence serves as the conservative default, ensuring that Vaults created before this amendment retain their existing behavior (3.2.1).

## 3. Specification

This specification modifies the parent [XLS-65](../README.md) sections named below, as well as the identified sections of [XLS-65.1.4](../65.1/65.1.4-closed-ended-vault.md). All other parent behavior remains unchanged.

This specification and [XLS-65.3](../65.3/README.md) (Fixed Precision for Vault and Lending) are introduced together under the `LendingProtocolV1_2` amendment. Within that amendment, this specification depends on XLS-65.3 for its rounding and precision rules.

Two amendments are hard prerequisites of `LendingProtocolV1_2`:

| Prerequisite Amendment | Specification                                      | Reason                                                                                                                                                |
| ---------------------- | -------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------- |
| `LendingProtocolV1_1`  | [XLS-65.1.4](../65.1/65.1.4-closed-ended-vault.md) | `EarlyExitFeeRate` may only be set on a closed-ended Vault, and the only behavior it changes is the Investment-phase gate that XLS-65.1.4 introduces. |
| `fixCleanup3_4_0`      | [XLS-65.2](../65.2/README.md)                      | Defines the posterior scale rounding path on legacy Vaults, tightening precision loss and clawback semantics.                                         |

Within the `LendingProtocolV1_2` amendment, this specification depends on:

| Sibling Specification         | Name                                  | Reason                                                                                                                                                                                                                                                                                                                             |
| ----------------------------- | ------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [XLS-65.3](../65.3/README.md) | Fixed Precision for Vault and Lending | Sets fixed precision grid $P$, live exponent $e(R)$, live scale $s = -e(R)$, and the operation rule of 3.2.4. Under XLS-65.3, `VaultWithdraw` rounds outflows toward zero at the candidate posterior live exponent $e^\ast$ of `Vault.AssetsAvailable`. The post-fee payout is rounded on that grid, and the fee is the remainder. |

Amendment compatibility and version rules:

- `LendingProtocolV1_2` MUST NOT be enabled on a ledger where either prerequisite amendment (`LendingProtocolV1_1` or `fixCleanup3_4_0`) is not enabled.
- Closed-ended Vaults created under `LendingProtocolV1_1` have `Vault.LEVersion == 1` (`CashBasis`).
- Closed-ended Vaults created under `LendingProtocolV1_2` have `Vault.LEVersion == 2` (`FixedPrecision`).
- Early-exit fee functionality applies to closed-ended Vaults with `LEVersion >= 1` (both `CashBasis` and `FixedPrecision`).

### 3.1 Protocol Constants

| Constant                  | Value    | Meaning                                                                                                                                                                                                                                                                                         |
| ------------------------- | -------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `MAX_EARLY_EXIT_FEE_RATE` | `100000` | Inclusive upper bound on `EarlyExitFeeRate`, in tenths of a basis point. Equivalent to 100%. A rate of exactly this value is accepted. An early exit at this rate burns shares and transfers no assets, unless it burns the entire outstanding share supply under the full-exit waiver (3.4.3). |

### 3.2 Ledger Entry: `Vault`

#### 3.2.1 Fields

Add this field to parent 3.1.2:

| Field Name         | Constant | Required | JSON Type | Internal Type | Default Value | Description                                                                                                                                                                            |
| ------------------ | :------: | :------: | :-------: | :-----------: | :-----------: | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `EarlyExitFeeRate` |   Yes    |    No    | `number`  |   `UINT32`    |     `N/A`     | The early-exit fee, in tenths of a basis point, charged on withdrawals made during the Investment phase. Its presence permits withdrawals during Investment. Immutable after creation. |

An absent field and a value of `0` are distinct:

| `Vault.EarlyExitFeeRate`              | `VaultWithdraw` during Investment               |
| ------------------------------------- | ----------------------------------------------- |
| Absent                                | Rejected with `tecTOO_SOON`, as in the parent   |
| `0`                                   | Permitted, and charged no fee                   |
| `0 < rate <= MAX_EARLY_EXIT_FEE_RATE` | Permitted, and charged the fee defined in 3.4.3 |

The field is stored only on a Vault with `VaultKind == ClosedEnded` and `LEVersion >= 1` (for example, `CashBasis` or `FixedPrecision`). `VaultCreate` rejects the field on any other Vault configuration, including when the rate is `0` (3.3.2).

The rate is expressed in tenths of a basis point, matching the rate convention of [XLS-66](../../XLS-0066-lending-protocol/README.md):

- A value of `1` represents 0.1 basis points (0.001%).
- A value of `100000` represents 10,000 basis points (100%).
- Valid values range from `0` to `MAX_EARLY_EXIT_FEE_RATE` inclusive.

As a fraction, the rate is defined as:

$$\phi = \frac{\text{EarlyExitFeeRate}}{100000}$$

#### 3.2.2 Invariants

Amend parent 3.1.10 under `LendingProtocolV1_2`:

**Invariant 14 is extended**

14. `EarlyExitFeeRate` joins the set of fields that are immutable once set. If it is present, it keeps its value. If it is absent, it stays absent, except when the transaction creates the entry.

**Invariant 17 is appended**

17. If `EarlyExitFeeRate` is present:
    1. `EarlyExitFeeRate` only exists on a Vault with `VaultKind == ClosedEnded` and `LEVersion >= 1`.
    2. `EarlyExitFeeRate <= MAX_EARLY_EXIT_FEE_RATE`.

    A present value of `0` is valid and is not elided.

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

Add this field to parent 3.2.1:

| Field Name         | Required | JSON Type | Internal Type | Default Value | Description                                                                                            |
| ------------------ | :------: | :-------: | :-----------: | :-----------: | ------------------------------------------------------------------------------------------------------ |
| `EarlyExitFeeRate` |    No    | `number`  |   `UINT32`    |     `N/A`     | The early-exit fee in tenths of a basis point (3.2.1). Permitted only when `VaultKind == ClosedEnded`. |

#### 3.3.2 Failure Conditions

##### 3.3.2.1 Data Verification

Append to the existing checks:

6. `EarlyExitFeeRate` is present and either `LendingProtocolV1_2` or `fixCleanup3_4_0` is not enabled. (`temDISABLED`)
7. `EarlyExitFeeRate` is present and `VaultKind` is absent or not `ClosedEnded`. (`temMALFORMED`)
8. `EarlyExitFeeRate` is greater than `MAX_EARLY_EXIT_FEE_RATE`. (`temMALFORMED`)

##### 3.3.2.2 Protocol-Level Failures

No changes.

#### 3.3.3 State Changes

Extend parent 3.2.6 step 1:

1. If `EarlyExitFeeRate` is present, copy it from the transaction to the new `Vault` as submitted.
2. If `EarlyExitFeeRate` is not present, leave the field absent.

#### 3.3.4 Invariants

Append to parent 3.2.7 under `LendingProtocolV1_2`:

4. If `EarlyExitFeeRate` is present:
   1. `EarlyExitFeeRate` only exists on a Vault with `VaultKind == ClosedEnded` and `LEVersion >= 1`.
   2. `EarlyExitFeeRate <= MAX_EARLY_EXIT_FEE_RATE`.

### 3.4 Transaction: `VaultWithdraw`

In transaction parameters, `Amount` specifies the **pre-fee** amount in both denominations:

- **Asset-denominated withdrawals:** `Amount` represents a requested pre-fee value. Because parent 3.1.7.2.3 rounds $\Delta_{shares}$ to the nearest integer, the actual pre-fee asset delta $\Delta_{assets}$ may differ slightly from `Amount`.
- **Share-denominated withdrawals (redeem):** `Amount` specifies the exact number of shares to burn ($\Delta_{shares}$).

The net payout transferred to the destination is $\Delta_{assets}^{paid}$ (3.4.3), which equals the pre-fee asset amount less the fee ($F$).

#### 3.4.1 Fields

No changes.

#### 3.4.2 Failure Conditions

Under `LendingProtocolV1_2`, this section supersedes three failure checks from prior specifications:

- Parent 3.6.2.2 check 12 (precision loss).
- The Investment-phase gate of [XLS-65.1.4](../65.1/65.1.4-closed-ended-vault.md).
- Parent 3.6.2.2 checks 10.2 and 10.4 (available asset liquidity).

Parent 3.6.2.2 check 13 (arithmetic overflow during share or asset calculation, returning `tecPATH_DRY`) keeps its number and meaning. It extends to the payout and fee calculation in steps 4 and 5 of 3.4.3.

**Parent 3.6.2.2 check 12**, the precision-loss check of [XLS-65.2](../65.2/README.md) and XLS-65.3 3.2.4, is superseded by:

12. - `fixCleanup3_4_0`: As in the parent.
    - `LendingProtocolV1_2`: Pre-fee precision loss rules from [XLS-65.2](../65.2/README.md) (for `LEVersion == 1`) and [XLS-65.3](../65.3/README.md) 3.2.4 (for `LEVersion >= 2`) apply unchanged to the pre-fee amount $\Delta_{assets}$. The fee adds no further precision-loss condition:
      - **Fee consuming the withdrawal:** If the rounded fee equals the pre-fee amount ($F == \Delta_{assets}$, yielding $\Delta_{assets}^{paid} == 0$), the transaction succeeds. It burns $\Delta_{shares}$ and transfers no assets, the same outcome as at `MAX_EARLY_EXIT_FEE_RATE` (3.4.3, 4.3).
      - **No post-fee dust:** Step 5 of 3.4.3 rounds the payout down at the posterior scale of the balance it leaves. A positive payout therefore always moves the stored balance, and a payout that would not is rounded to zero and handled as above.

      The parent fixed-share exemption remains unchanged.

**The Investment-phase gate** of [XLS-65.1.4](../65.1/65.1.4-closed-ended-vault.md) is superseded by the rule below. That specification defines the gate as a protocol-level failure in its `VaultWithdraw` section:

- `SingleAssetVault`: The rule does not apply.
- `LendingProtocolV1_1`: The Vault is closed-ended and `SubscriptionDate < now < RedemptionDate`, where `now` is the parent ledger close time. (`tecTOO_SOON`)
- `LendingProtocolV1_2`: As above, and `Vault.EarlyExitFeeRate` is absent. (`tecTOO_SOON`)

**Parent 3.6.2.2 checks 10.2 and 10.4**, which evaluate `Vault.AssetsAvailable`, are superseded by:

10. Items 2 and 4, on `Vault.AssetsAvailable`, in both denominations:
    - `SingleAssetVault`: As in the parent.
    - `LendingProtocolV1_2`:
      - If $F == 0$: The transaction fails if `Vault.AssetsAvailable < \Delta_{assets}` (as in the parent).
      - If $F > 0$: The transaction fails if `Vault.AssetsAvailable < \Delta_{assets}^{paid}`. Only the payout leaves the Vault, so measuring against the pre-fee amount would reject withdrawals the Vault can fund (4.4). (`tecINSUFFICIENT_FUNDS`)

    Items 1 and 3, on the submitter's share balance, are unchanged and evaluate against $\Delta_{shares}$.

The fee $F$ is `0` under any of the following conditions:

- The Vault is open-ended.
- The Vault is closed-ended and outside the Investment phase.
- The Vault has `EarlyExitFeeRate == 0`.
- The withdrawal qualifies for the full-exit waiver (3.4.3).

In each of these cases, liquidity is evaluated against $\Delta_{assets}$ as in the parent specification. Only withdrawals with $F > 0$ evaluate liquidity against $\Delta_{assets}^{paid}$.

#### 3.4.3 State Changes

**Parent computation, unchanged**

1. Compute $\Delta_{shares}$ from `Amount` using the variables from parent 3.6.1:
   - If `Amount` is in the Vault asset, apply the _Withdraw_ formula (parent 3.1.7.2.3).
   - If `Amount` is in shares, apply the _Redeem_ formula (parent 3.1.7.2.2).
     Early-exit fees do not affect this step.
2. Compute the pre-fee asset amount:

   $$\Delta_{assets} = \frac{\Delta_{shares} \times \Gamma_{asset}}{\Gamma_{shares}}$$

3. Round $\Delta_{assets}$ down (toward zero) at the candidate posterior scale $s$ of the **reference balance** $R$. Check 12 of 3.4.2 is evaluated against the result.
   - The reference balance is the stored balance the cash leaves:

     | `LEVersion`             | Reference balance $R$   | Scale rule                                                                                                                                                                           |
     | ----------------------- | ----------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
     | `>= 2` (FixedPrecision) | `Vault.AssetsAvailable` | $s = -e^\ast$, where $e^\ast = e(R - \Delta_{assets})$ is the candidate posterior live exponent defined in XLS-65.3 3.2.3 and 3.2.4. One unit at $s$ is the live unit $10^{e^\ast}$. |
     | `== 1` (CashBasis)      | `Vault.AssetsTotal`     | $s$ is the posterior scale defined in XLS-65.2 3.1.2.3, the `STAmount` exponent of $R - \Delta_{assets}$ evaluated with round-to-nearest.                                            |

   - Both rules evaluate the posterior on the **pre-fee** delta of step 2.
   - For `XRP` and `MPT`, $s = 0$ ($e^\ast = 0$) at all times. Rounding at $s$ is an identity operation. One unit at $s$ corresponds to one drop of XRP or one MPT unit.

**Early-exit fee, added by this patch**

4. Compute the exact post-fee payout. Every rounding in this step lowers the result, so the value never exceeds $\Delta_{assets} \times (1 - \phi)$:

   $$\Delta_{assets}^{exact} = \Delta_{assets} - \lceil \Delta_{assets} \times \phi \rceil$$

   - The fee term is rounded up at the precision of the arithmetic, and the difference is rounded down to the asset's representable precision.
   - When `Vault.EarlyExitFeeRate == MAX_EARLY_EXIT_FEE_RATE`, $\Delta_{assets}^{exact} = 0$ without further computation.
   - The fee is waived, and $\Delta_{assets}^{paid} = \Delta_{assets}$ with $F = 0$, under any of the following conditions. Step 5 is skipped in these cases:
     - The Vault is not in its Investment phase.
     - `Vault.EarlyExitFeeRate` is `0`.
     - The withdrawal burns the entire outstanding share supply of the Vault (the **full-exit waiver**, 4.2).

5. Round the payout down (toward zero) at the candidate posterior scale $s^{paid}$ of the same reference balance $R$ as step 3, evaluated on the exact payout, and take the fee as the remainder (4.3):

   $$\Delta_{assets}^{paid} = \left\lfloor \Delta_{assets}^{exact} \right\rfloor_{s^{paid}}, \qquad F = \Delta_{assets} - \Delta_{assets}^{paid}$$

   | `LEVersion`             | Scale rule for $s^{paid}$                                                                                                  |
   | ----------------------- | -------------------------------------------------------------------------------------------------------------------------- |
   | `>= 2` (FixedPrecision) | $s^{paid} = -e^{paid}$, where $e^{paid} = e(R - \Delta_{assets}^{exact})$ is the candidate posterior live exponent.        |
   | `== 1` (CashBasis)      | $s^{paid}$ is the `STAmount` exponent of $R - \Delta_{assets}^{exact}$ evaluated with round-to-nearest (XLS-65.2 3.1.2.3). |

   For `XRP` and `MPT`, $s^{paid} = 0$ and the rounding is an identity operation.

   Properties of the result:
   - **Fee rounds up:** Rounding the payout down is equivalent to rounding the fee up, so $F \ge \Delta_{assets} \times \phi$.
   - **Minimum fee:** $\Delta_{assets}^{exact} < \Delta_{assets}$, so the posterior reference balance at step 5 is larger than at step 3 and $s^{paid} \le s$. The payout lies on the grid at $s$, and $F$ is a positive multiple of $10^{-s}$. When `Vault.EarlyExitFeeRate > 0`, the fee is at least one unit at scale $s$ (one drop for `XRP`, one unit for `MPT`).
   - **Scale boundary:** $s^{paid}$ is one step coarser than $s$ only when the posterior reference balance crosses a power of ten between the two evaluations (3.4.3.2).
   - **Zero payout:** If $\Delta_{assets}^{exact}$ is below one unit at $s^{paid}$, the payout rounds to zero and $F = \Delta_{assets}$. The pre-fee amount is retained in full, $\Delta_{shares}$ is burned, and nothing is transferred. This is the same outcome as at `MAX_EARLY_EXIT_FEE_RATE`, and the transaction succeeds (4.3).
   - **Representable posterior:** $\Delta_{assets}^{paid}$ lies on the grid of $R - \Delta_{assets}^{exact}$, so decreasing $R$ by $\Delta_{assets}^{paid}$ always yields a representable stored balance. For `LEVersion == 1` Vaults, the invariant in [XLS-65.2](../65.2/README.md) 3.1.2.2 continues to admit one unit of `IOU` slack at the exponent of the persisted `Vault.AssetsTotal`.

**Steps 6 to 9, superseding items 4 to 7**, with $\Delta_{assets}^{paid}$ in place of $\Delta_{asset}$:

6. Decrease `Vault.AssetsTotal` and `Vault.AssetsAvailable` by $\Delta_{assets}^{paid}$.
7. If `Vault.Asset` is `XRP`:
   1. Decrease the `Balance` field of the _pseudo-account_ `AccountRoot` by $\Delta_{assets}^{paid}$.
   2. Increase the `Balance` field of the destination `AccountRoot` by $\Delta_{assets}^{paid}$.
8. If `Vault.Asset` is an `IOU`:
   1. If $\Delta_{assets}^{paid}$ is greater than zero and the destination does not have a `RippleState` object for the vault asset, create one.
   2. Decrease the `RippleState` balance between the _pseudo-account_ `AccountRoot` and the `Issuer` `AccountRoot` by $\Delta_{assets}^{paid}$.
   3. Increase the `RippleState` balance between the destination `AccountRoot` and the `Issuer` `AccountRoot` by $\Delta_{assets}^{paid}$.
9. If `Vault.Asset` is an `MPT`:
   1. If $\Delta_{assets}^{paid}$ is greater than zero and the destination does not have an `MPToken` object for the vault asset, create one.
   2. Decrease the `MPToken.MPTAmount` of the _pseudo-account_ `MPToken` for `Vault.Asset` by $\Delta_{assets}^{paid}$.
   3. Increase the `MPToken.MPTAmount` of the destination `MPToken` for `Vault.Asset` by $\Delta_{assets}^{paid}$.

When $\Delta_{assets}^{paid}$ is zero, whether because `Vault.EarlyExitFeeRate == MAX_EARLY_EXIT_FEE_RATE`, because the rounded fee consumes the whole pre-fee amount, or under the parent fixed-share exemption:

- Steps 6 through 9 execute no balance transfers.
- No `RippleState` or `MPToken` object is created for the destination.
- Only share balance updates (items 1 through 3 of parent 3.6.3) are applied to the ledger.

**Full-redemption path, unchanged**

- The full-redemption path described in [XLS-65.2](../65.2/README.md) 3.1.2.2 (`fixCleanup3_2_0`) is preserved. It applies whenever $\Delta_{shares}$ equals the entire outstanding share supply, matching the condition for the full-exit waiver in step 4.
- A full redemption cannot execute if capital is deployed into loans or if `LossUnrealized` is non-zero. In those situations, pre-fee $\Delta_{assets}$ equals `Vault.AssetsTotal`, which exceeds `Vault.AssetsAvailable`. The transaction fails the liquidity check with `tecINSUFFICIENT_FUNDS`. Consequently, the waiver cannot leave remaining assets in a Vault that has zero outstanding shares.

##### 3.4.3.1 Worked Example

Consider a closed-ended Vault in its Investment phase, with `EarlyExitFeeRate = 2000` (2%) and no unrealized loss:

| Quantity           | Initial Value |
| ------------------ | ------------- |
| `AssetsTotal`      | 1,000,000     |
| `AssetsAvailable`  | 150,000       |
| Shares outstanding | 1,000,000     |
| Exchange rate      | 1.000         |

A depositor submits `VaultWithdraw` with `Amount = 100,000` of the Vault asset:

1. $\Delta_{shares} = 100{,}000$, burned against the pre-fee amount.
2. $\Delta_{assets} = 100{,}000$, representing the pre-fee value of those shares.
3. $F = 100{,}000 \times 0.02 = 2{,}000$.
4. $\Delta_{assets}^{paid} = 98{,}000$, representing the net payout to the depositor and the liquidity required from `AssetsAvailable`.

| Quantity           | Final Value |
| ------------------ | ----------- |
| `AssetsTotal`      | 902,000     |
| `AssetsAvailable`  | 52,000      |
| Shares outstanding | 900,000     |
| Exchange rate      | 1.002222    |

The retained fee of 2,000 remains in the Vault and is distributed across the 900,000 remaining shares, increasing the asset value per share by approximately 0.2222%. The exiting depositor receives 98,000 assets in exchange for burning shares originally valued at 100,000 assets.

##### 3.4.3.2 Worked Example: Scale Boundary

Consider a `FixedPrecision` Vault holding an `IOU` with `Scale = 6` and `EarlyExitFeeRate = 10000` (10%). The reference balance is `Vault.AssetsAvailable`:

| Quantity          | Initial Value      |
| ----------------- | ------------------ |
| `AssetsAvailable` | 10,500,000,000     |
| Pre-fee delta     | 550,000,000.123457 |

Steps 3 to 5 of 3.4.3 proceed as follows:

| Step | Quantity                      | Value                  | Note                                     |
| ---- | ----------------------------- | ---------------------- | ---------------------------------------- |
| 3    | $R - \Delta_{assets}$         | 9,949,999,999.876543   | 16 significant digits, so $s = 6$        |
| 3    | $\Delta_{assets}$             | 550,000,000.123457     | Already on the grid at $s = 6$           |
| 4    | $\Delta_{assets} \times \phi$ | 55,000,000.0123457     | Exact                                    |
| 4    | $\Delta_{assets}^{exact}$     | 495,000,000.1111113    | Exact                                    |
| 5    | $R - \Delta_{assets}^{exact}$ | 10,004,999,999.8888887 | 17 significant digits, so $s^{paid} = 5$ |
| 5    | $\Delta_{assets}^{paid}$      | 495,000,000.11111      | Rounded down at $s^{paid} = 5$           |
| 5    | $F$                           | 55,000,000.012347      | Remainder, a multiple of $10^{-6}$       |
| 6    | Posterior `AssetsAvailable`   | 10,004,999,999.88889   | Representable in 16 significant digits   |

Rounding the fee up at $s = 6$ instead would give $F = 55{,}000{,}000.012346$ and a payout of $495{,}000{,}000.111111$. The posterior `AssetsAvailable` would then be $10{,}004{,}999{,}999.888889$, which has 17 significant digits and cannot be stored. Deriving the payout scale from the balance the payout leaves avoids this (4.3).

#### 3.4.4 Invariants

Amend parent 3.6.4 under `LendingProtocolV1_2`. Invariants 1 and 2 adopt relaxed bounds to support zero-asset payouts (4.5):

1. Supersedes invariant 1, which requires the Vault pseudo-account's asset balance to decrease by a positive amount. A withdrawal must not increase the Vault pseudo-account's asset balance.
2. Supersedes invariant 2, which requires the destination's asset balance to increase. A withdrawal must not decrease the destination's asset balance.
3. A zero $\Delta_{assets}^{paid}$ leaves both balances unchanged. Invariants 3 and 6 hold as written, with both sides evaluating to zero in that case.
4. The Investment-phase rule in [XLS-65.1.4](../65.1/65.1.4-closed-ended-vault.md) 3.5.1 prohibiting `VaultWithdraw` during Investment applies only when `Vault.EarlyExitFeeRate` is absent.
5. On the full-redemption path (3.4.3), both `Vault.AssetsTotal` and `Vault.AssetsAvailable` reach zero. The asset balance decrease equals the prior `Vault.AssetsAvailable`, matching parent behavior. Because no fee is retained, parent `Vault` invariant 7 is satisfied.

### 3.5 Transaction: `VaultClawback`

A `VaultClawback` transaction claws back assets from a Vault by redeeming shares held by a specific account. The transaction functions conceptually as a `VaultWithdraw` executed on behalf of the `Holder`, sending the recovered funds to the asset `Issuer`. If available funds are insufficient for the entire `Amount`, the transaction performs a partial clawback up to `Vault.AssetsAvailable`.

Amendment behavior:

- `SingleAssetVault`: The specification noted that clawback transactions must respect future fees or penalties.
- `LendingProtocolV1_2`: `VaultClawback` exempts clawbacks from `EarlyExitFeeRate`. A clawback transaction transfers the full pre-fee asset amount and burns the corresponding shares across all phases and fee rates.

#### 3.5.1 Fields

No changes.

#### 3.5.2 Failure Conditions

No changes.

#### 3.5.3 State Changes

No changes.

#### 3.5.4 Invariants

No changes.

### 3.6 RPC: `vault_info`

#### 3.6.1 Response Fields

Add `vault.EarlyExitFeeRate` to parent 3.9.2:

- **Presence:** The field is included if the closed-ended Vault was created with `EarlyExitFeeRate` (including a value of `0`), and omitted otherwise.
- **Interpretation:** Clients MUST NOT interpret field absence as a rate of `0`. Absence indicates that withdrawals during the Investment phase are disallowed. A value of `0` indicates that early withdrawals are permitted without a fee.

| Field Name               | Required? | JSON Type | Description                                                           |
| ------------------------ | :-------: | :-------: | --------------------------------------------------------------------- |
| `vault.EarlyExitFeeRate` |    No     | `number`  | `LendingProtocolV1_2`: The early-exit fee in tenths of a basis point. |

Example response fragment, showing only the fields added by this specification and [XLS-65.1.4](../65.1/65.1.4-closed-ended-vault.md):

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

When `ledger_entry` returns a `Vault`, include `EarlyExitFeeRate` according to the presence and meaning rules in 3.6.1. Request fields and failure conditions are unchanged.

## 4. Rationale

### 4.1 Why the fee stays in the Vault

Retaining the early-exit fee inside the Vault serves several purposes:

- **Fair compensation:** An early exit draws on uncommitted liquidity and reduces the asset base that absorbs costs and unrealized losses. Leaving the fee in the Vault directly compensates remaining depositors.
- **Incentive alignment:** Distributing fees to the Vault owner or loan broker would create improper incentives for the party establishing the rate to encourage withdrawals.
- **Protocol simplicity:** Retaining funds within the Vault requires no external balance transfers and no additional ledger fields.
- **Invariant compatibility:** Retention requires only relaxing the positive-delta checks in parent 3.6.4 (invariants 1 and 2) to permit zero-payout withdrawals (3.4.4).

### 4.2 Why the last exiting shareholder pays no fee

Retained fees accrue to remaining shares. If a withdrawal burns the entire outstanding share supply:

- Retaining a fee would leave orphaned assets in a Vault with zero shares, violating parent `Vault` invariant 7 and preventing Vault deletion.
- Waiving the fee ensures the Vault can cleanly empty and delete upon full redemption.
- The waiver triggers solely when the total share supply reaches zero. If a sole shareholder executes a withdrawal that leaves remaining shares in the Vault, the transaction still incurs the fee (8).

### 4.3 Why the fee rounds up and a fee that consumes the withdrawal is accepted

Fee calculation enforces three rules on rounding and zero payouts:

1. **Rounding up and minimum fee:** Rounding down would make the fee zero on withdrawals small enough to underflow asset precision. Depositors could then exit fee-free in fractional slices. Rounding the payout down, and hence the fee up, ensures that every withdrawal with a non-zero fee rate pays at least the smallest chargeable unit at scale $s$ ($10^{-s}$).
2. **Acceptance when the fee consumes the withdrawal below 100%:** The rounded fee equals the pre-fee amount only when the exact payout is below one unit at $s^{paid}$. The transaction succeeds, burns $\Delta_{shares}$, and transfers nothing, for three reasons:
   - Rejecting it would make the outcome depend on rounding. A depositor would have to adjust `Amount` to work around a precision artifact rather than a rule of the Vault.
   - The forfeited value is bounded by $10^{-s^{paid}} / (1 - \phi)$, the smallest representable payout grossed up by the fee rate. At low fee rates, this is about one unit.
   - The outcome is identical to a withdrawal at `MAX_EARLY_EXIT_FEE_RATE`, which the protocol already accepts. One code path handles both.
3. **Acceptance at 100% rate:** When `Vault.EarlyExitFeeRate == MAX_EARLY_EXIT_FEE_RATE`, a 100% fee is the intended setting. Unless the withdrawal qualifies for the full-exit waiver, the transaction forfeits the entire payout to remaining depositors by design, so it succeeds.

The payout is rounded once, at the posterior scale of the balance it leaves, and the fee is the remainder, for four reasons:

- **One grid:** The stored balance must decrease by exactly the payout. Rounding the payout on the posterior grid of that balance guarantees the result is representable. Rounding the fee at the pre-fee scale $s$ instead, and taking the payout as the difference, leaves the posterior balance unrepresentable when it crosses a power of ten (3.4.3.2).
- **Consistent base:** The fee rate applies to the pre-fee withdrawal amount that would otherwise be paid out, matching the rounded asset delta from parent calculations.
- **Scale from the exact payout:** Deriving $s^{paid}$ from the exact payout is not circular. The exact payout is fully determined by $\Delta_{assets}$ and $\phi$ before any rounding at a scale takes place. Because $s^{paid} \le s$, the fee still lies on the pre-fee grid and is never below one unit at $s$.
- **Reproducibility:** The fee depends exclusively on $\Delta_{assets}$, $\phi$, and the reference balance, all of which are available on ledger, enabling client applications to recompute the exact fee and payout.

### 4.4 Why liquidity is checked against the post-fee payout

Liquidity checks evaluate whether the Vault holds sufficient uncommitted assets to fulfill an outflow. Because retained fees remain in the Vault, only the net payout ($\Delta_{assets}^{paid}$) leaves the Vault pseudo-account. Measuring liquidity against the pre-fee delta would incorrectly reject valid withdrawals that the Vault has sufficient cash to satisfy.

### 4.5 Why withdraw invariants use relaxed bounds

Parent 3.6.4 invariants 1 and 2 require a strictly positive decrease in the Vault asset balance and a strictly positive increase in the destination balance. Because a 100% fee results in a zero-asset payout, these invariants must accommodate zero deltas. Two design alternatives exist:

| Approach                    | Implementation                                                                          | Trade-off                                                                                                                                                                       |
| --------------------------- | --------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Conditional invariant       | Require positive deltas only when $\Delta_{assets}^{paid} > 0$.                         | Must replicate complex special cases, including issuer accounts (which hold no trust lines) and `IOU` rounding tolerances. Imperfect handling causes valid withdrawals to fail. |
| Relaxed invariant (adopted) | Require that Vault balance does not increase and destination balance does not decrease. | Seamlessly accommodates zero payouts without adding conditional exceptions. Existing issuer and precision rules remain intact.                                                  |

Relaxing the bounds avoids catastrophic invariant check failures on otherwise valid transactions while still preventing any improper balance increases.

## 5. Backwards Compatibility

The feature remains inert until `LendingProtocolV1_2` is enabled. Ledger entries and transactions behave identically to prior specifications on networks where the amendment is not active.

Key compatibility considerations:

- **Prerequisite amendment dependency:** The early-exit fee requires posterior scale definitions from XLS-65.3 or [XLS-65.2](../65.2/README.md). If `fixCleanup3_4_0` is not active, `VaultCreate` rejects `EarlyExitFeeRate` with `temDISABLED` (3.3.2), preventing the creation of Vaults with early-exit fees.
- **Open-ended Vaults:** Open-ended Vaults cannot include `EarlyExitFeeRate` and do not have phases. Their withdrawal behavior is unaffected.
- **Existing closed-ended Vaults:** `EarlyExitFeeRate` can only be set during `VaultCreate`. Vaults created prior to `LendingProtocolV1_2` lack this field, so withdrawals during their Investment phase continue to fail with `tecTOO_SOON` as defined in [XLS-65.1.4](../65.1/65.1.4-closed-ended-vault.md).
- **Serialization compatibility:** `EarlyExitFeeRate` is an optional field. Existing serialized `Vault` entries deserialize without modification. When set to `0`, the field is explicitly stored on the ledger, distinguishing a free early exit from a disallowed exit on the wire (3.2.1).
- **Zero payout below 100%:** If rounding causes the fee to consume the entire withdrawal amount while `EarlyExitFeeRate < MAX_EARLY_EXIT_FEE_RATE`, the transaction succeeds, burns the shares, and transfers nothing, as at `MAX_EARLY_EXIT_FEE_RATE` (4.3). Client software MUST quote the payout before submission (8).
- **Client quoting:** Client applications calculating expected withdrawal proceeds during Investment must account for `EarlyExitFeeRate`. Calculating payouts solely from `Amount` and the share exchange rate will overestimate the net payout by the fee amount. Clients can retrieve the rate via `vault_info` and `ledger_entry` (3.6, 3.7).

## 6. Test Plan

### 6.1 `VaultCreate`

- Creating a closed-ended Vault with a valid non-zero `EarlyExitFeeRate` succeeds and stores the field.
- Creating a closed-ended Vault with `EarlyExitFeeRate == 0` succeeds and stores the field with value `0`. The resulting Vault is distinguishable on ledger, over `vault_info`, and over `ledger_entry` from a Vault created without the field.
- Creating a Vault with `EarlyExitFeeRate == MAX_EARLY_EXIT_FEE_RATE` succeeds. A transaction specifying a rate greater than `MAX_EARLY_EXIT_FEE_RATE` fails with `temMALFORMED`.
- Creating an open-ended Vault or a Vault with absent `VaultKind` specifying `EarlyExitFeeRate` fails with `temMALFORMED`, even if the rate is `0`.
- Before `LendingProtocolV1_2` is enabled, any `VaultCreate` containing `EarlyExitFeeRate` fails with `temDISABLED`.
- If `LendingProtocolV1_2` is enabled while `fixCleanup3_4_0` is disabled, any `VaultCreate` containing `EarlyExitFeeRate` fails with `temDISABLED`, including when the rate is `0`.

### 6.2 `VaultSet`

- A `VaultSet` transaction containing `EarlyExitFeeRate` is rejected at deserialization for both closed-ended and open-ended Vaults, with and without the amendment.

### 6.3 `VaultWithdraw` during Investment

- With a non-zero rate, an asset-denominated withdrawal succeeds:
  - The payout transferred equals $\Delta_{assets} - F$.
  - The burned shares equal $\Delta_{shares}$ computed from the pre-fee amount.
  - `AssetsTotal` and `AssetsAvailable` decrease by the payout amount only.
- With a non-zero rate, a share-denominated withdrawal (redeem) succeeds and is charged the same fee.
- With an absent rate, a withdrawal fails with `tecTOO_SOON` in both denominations, with and without a specified `Destination`.
- With a rate of `0`, a withdrawal succeeds and incurs no fee:
  - The payout equals $\Delta_{assets}$.
  - `AssetsTotal` and `AssetsAvailable` decrease by $\Delta_{assets}$.
  - The resulting state, including the share exchange rate, matches an equivalent withdrawal on an open-ended Vault. The exchange rate is not required to be strictly identical because parent integer rounding of $\Delta_{shares}$ and $\Delta_{assets}$ can leave residual value in `AssetsTotal`.
- With a rate of `0` and an asset-denominated `Amount` that does not convert to a whole number of shares, the payout differs from `Amount` exactly as in the parent specification.
- The exchange rate after a fee-charging withdrawal is strictly higher than before. A subsequent depositor redeeming an identical share count immediately afterward receives strictly more assets than the first depositor.
- With a rate of `MAX_EARLY_EXIT_FEE_RATE`, a withdrawal that leaves remaining shares in the Vault succeeds, burns $\Delta_{shares}$, transfers no assets, and leaves `AssetsTotal` and `AssetsAvailable` unchanged. The exchange rate increases as remaining holders absorb the forfeited position.
- When `0 < EarlyExitFeeRate < MAX_EARLY_EXIT_FEE_RATE`, a withdrawal small enough that the rounded fee consumes the entire pre-fee delta succeeds, burns $\Delta_{shares}$, transfers no assets, and leaves `AssetsTotal` and `AssetsAvailable` unchanged.
- The worked examples in 3.4.3.1 and 3.4.3.2 reproduce exactly, including both post-state totals.
- A withdrawal specifying a `Destination` behaves identically, delivering the post-fee amount to the destination account.
- A fee-charging withdrawal on a Vault with non-zero `LossUnrealized` applies the fee to the net amount after deducting unrealized losses.

### 6.4 `VaultWithdraw` outside Investment

- A withdrawal during the Subscription phase incurs no fee, even when a non-zero fee rate is configured.
- A withdrawal during the Redemption phase incurs no fee.
- Boundary conditions:
  - A withdrawal at `now == SubscriptionDate` incurs no fee, whereas a withdrawal at `now == SubscriptionDate + 1` incurs the fee.
  - A withdrawal at `now == RedemptionDate` incurs no fee, whereas a withdrawal at `now == RedemptionDate - 1` incurs the fee.
- Withdrawals from open-ended Vaults remain unaffected across all ledger close times.

### 6.5 Liquidity

- A withdrawal whose post-fee payout exceeds `AssetsAvailable` fails with `tecINSUFFICIENT_FUNDS`.
- When $F = 0$, a withdrawal whose pre-fee amount exceeds `AssetsAvailable` fails with `tecINSUFFICIENT_FUNDS`. This behavior applies identically across open-ended Vaults, closed-ended Vaults with a rate of `0`, and closed-ended Vaults outside Investment.
- Boundary condition: a withdrawal whose post-fee payout exactly equals `AssetsAvailable` succeeds, even if its pre-fee amount exceeds `AssetsAvailable`.
- A Vault whose capital is fully deployed into loans rejects every early exit requiring a positive payout. The Vault accepts withdrawals again as loan repayments restore `AssetsAvailable`.
- A Vault with `AssetsAvailable == 0` accepts an early exit whose post-fee payout is zero, whether from `EarlyExitFeeRate == MAX_EARLY_EXIT_FEE_RATE` or from a rounded fee that consumes the whole pre-fee amount. The transaction burns $\Delta_{shares}$, transfers no assets, and leaves `AssetsTotal` and `AssetsAvailable` at their prior values. Check 10 of 3.4.2 passes because no cash leaves the Vault.
- An early exit does not alter any outstanding `Loan` entry or the broker's `CoverAvailable`.

### 6.6 Rounding and Precision

- The fee rounds up: a withdrawal whose exact fee falls between two representable amounts at the live scale is charged the larger amount.
- When `EarlyExitFeeRate > 0`, the minimum fee is the smallest chargeable unit at scale $s$, ensuring that the fee never rounds to zero.
- When `EarlyExitFeeRate < MAX_EARLY_EXIT_FEE_RATE`, a withdrawal small enough that the rounded fee equals the pre-fee amount succeeds, burns $\Delta_{shares}$, transfers no assets, and leaves `AssetsTotal` and `AssetsAvailable` unchanged. This is verified for `XRP` (one drop at a 0.001% rate) and for an `IOU` (one unit at `Scale`).
- When `EarlyExitFeeRate == MAX_EARLY_EXIT_FEE_RATE`, a withdrawal that leaves remaining shares in the Vault succeeds, burns $\Delta_{shares}$, transfers no assets, and leaves `AssetsTotal` and `AssetsAvailable` unchanged.
- A pre-fee delta that rounds down to zero at the live scale (or posterior scale for `LEVersion == 1`) fails with `tecPRECISION_LOSS` regardless of fee rate.
- For an `IOU` withdrawal where exact and rounded pre-fee deltas differ, the fee is computed on the rounded delta. The payout is rounded down at the posterior scale of the reference balance, and the fee is the remainder.
- When the exact payout moves the posterior reference balance across a power of ten, the payout is rounded at the coarser scale $s^{paid}$, the fee remains a multiple of $10^{-s}$, and the posterior `AssetsAvailable` is representable (3.4.3.2).
- At a rate whose product with the pre-fee delta needs more than 16 significant digits (for example 12.345%), the fee is still rounded up and the payout is never above $\Delta_{assets} \times (1 - \phi)$.
- Splitting a withdrawal into $n$ smaller transactions incurs at least as much in cumulative fees as taking the withdrawal in a single transaction, verified across `XRP`, `IOU`, and `MPT` assets.
- Precision test suites execute across all three asset types and across the full `Scale` range.

### 6.7 Full-Exit Waiver

- A withdrawal during Investment that burns the entire outstanding share supply incurs no fee, empties the Vault (`AssetsTotal == 0`, `AssetsAvailable == 0`), pays out the prior `AssetsAvailable`, and permits subsequent Vault deletion.
- A withdrawal during Investment that would burn the entire outstanding share supply while capital is deployed into loans or while `LossUnrealized` is non-zero fails with `tecINSUFFICIENT_FUNDS` and incurs no fee.
- A sole shareholder executing a withdrawal that leaves remaining shares in the Vault is charged the fee. The parent sole-shareholder `LossUnrealized` waiver continues to apply to the pre-fee amount.
- In a Vault with two holders, a withdrawal that burns all shares held by one account without exhausting the total supply incurs the fee.

### 6.8 `VaultClawback`

- A clawback transaction during Investment from a Vault with a non-zero fee rate incurs no fee. The assets removed and shares burned match parent calculations exactly (3.5).
- A clawback transaction during Investment from a Vault with `EarlyExitFeeRate == MAX_EARLY_EXIT_FEE_RATE` recovers the full pre-fee amount, whereas an equivalent `VaultWithdraw` transaction would transfer no assets.

### 6.9 RPC Surface

- `vault_info` and `ledger_entry` return `EarlyExitFeeRate` for every Vault created with the field (including value `0`) and omit the field for Vaults created without it.
- RPC responses for a zero-rate Vault and an absent-rate Vault differ solely in the presence of this field.

### 6.10 Invariant Checks

- Invariant assertions verify 3.3.4 on `VaultCreate` and 3.4.4 on `VaultWithdraw`.
- Immutability checks verify 3.2.2 on every transaction modifying a `Vault`. Modifying `EarlyExitFeeRate` on an existing Vault or adding the field to a Vault that lacks it triggers invariant failure.
- Invariant tests verify that no `VaultWithdraw` transaction can leave a Vault with zero outstanding shares and non-zero `AssetsTotal`.

### 6.11 End-to-End Lifecycle

- Multi-depositor lifecycle:
  1. Multiple depositors subscribe capital during the Subscription phase.
  2. The Vault transitions into the Investment phase and originates loans.
  3. A depositor executes an early withdrawal and incurs the early-exit fee.
  4. The asset value backing each remaining share increases.
  5. Borrowers repay outstanding loans.
  6. The Vault transitions into the Redemption phase.
  7. Remaining depositors redeem their shares and receive their increased asset allocations.
  8. Total payouts plus the final Vault balance reconcile against total deposits plus accrued interest.
- Executing the lifecycle on a Vault with no configured fee rate confirms that every early withdrawal is rejected with `tecTOO_SOON`.
- Executing the lifecycle on a Vault with `EarlyExitFeeRate == 0` confirms that mid-term exits incur no fee and match open-ended Vault behavior.

## 7. Reference Implementation

_TBD_

## 8. Security Considerations

- **Liquidity run risk during Investment:** Configuring an early-exit fee permits depositors to withdraw uncommitted capital during the Investment phase up to `Vault.AssetsAvailable`. Because withdrawals execute first-come, first-served, early withdrawals can deplete available liquid assets before later depositors submit requests. While the exit fee compensates remaining depositors, it cannot prevent liquidity depletion. Depositors requiring guaranteed redemptions must wait until loans repay and the Redemption phase begins.
- **Forfeiture under maximum fee rates:** Vault creators can set `EarlyExitFeeRate` up to `MAX_EARLY_EXIT_FEE_RATE` (100%). At a 100% fee rate, any withdrawal that does not burn the entire outstanding share supply burns the submitted shares while delivering zero assets to the destination (3.4.3). Below 100%, a withdrawal of at most a few units at the posterior scale has the same outcome (4.3). Client software MUST compute and display the expected post-fee payout ($\Delta_{assets}^{paid}$) before submitting a `VaultWithdraw` transaction during Investment.
- **Owner participation in retained fees:** Because early-exit fees remain in the Vault, the owner cannot directly extract them. However, if the owner holds Vault shares, the owner benefits pro rata alongside other remaining share holders. The immutability of `EarlyExitFeeRate` mitigates this risk. Because the fee rate is established at creation and recorded on ledger, an owner cannot retroactively increase the rate after capital is deposited or decrease it to favor specific accounts.
- **Adverse selection prior to loss recognition:** A depositor anticipating an impending borrower default might attempt an early exit before the broker marks `LossUnrealized`. Although the early-exit fee imposes a cost on leaving, it may not offset the depositor's avoided share of a severe pending loss. Vaults without an early-exit fee carry no such mid-term run exposure during Investment.
- **Full-exit waiver dynamics:** An entity that consolidates 100% of outstanding Vault shares can redeem the entire supply without incurring an early-exit fee (3.4.3). Because no other depositors remain to be compensated, waiving the fee preserves accounting integrity without harming any third party (4.2). On Vaults without `tfVaultShareNonTransferable`, secondary market purchases of MPT shares permit consolidating share ownership.

# Appendix

## Appendix A: FAQ

### A.1 If I request a withdrawal of 100,000 assets, do I receive 100,000 assets?

A depositor receives less than the requested amount during the Investment phase on a Vault with a non-zero fee rate, unless the withdrawal burns the entire share supply under the full-exit waiver:

- `Amount` specifies the pre-fee amount. Shares are burned as if 100,000 assets were withdrawn, and the depositor receives that amount less the early-exit fee ($F$).
- The payout transferred to the destination is always $\Delta_{assets}^{paid}$ (3.4.3).

To receive approximately $X$ assets after the fee, a client can request:

$$\text{Amount} = \left\lceil \frac{X}{1 - \phi} \right\rceil$$

where $\phi$ is the fee rate as a fraction (3.2.1). For example, at a 2% fee rate, requesting 102,041 assets yields approximately 100,000 assets.

This estimate is approximate because integer share rounding and candidate posterior live scale rounding ($s$) affect the calculation. Client applications MUST calculate the exact payout using the steps in 3.4.3 before presenting quotes to users (3.4).

Special cases:

- At a 100% fee rate, withdrawals that do not burn the entire share supply yield zero assets regardless of `Amount` (3.4.3).
- If a withdrawal request is so small that the rounded fee consumes the entire amount while the fee rate is below 100%, the transaction succeeds, burns the shares, and transfers nothing (3.4.3). Clients should quote the payout before submitting such a request.

### A.2 Why is the fee rate a fixed percentage throughout the term?

A constant rate provides simplicity and transparency:

- **Predictability:** Depositors evaluate a single immutable fee rate on ledger prior to subscribing.
- **Simplicity:** A decaying fee schedule would introduce additional configuration parameters, schedule rules, and time-dependent fee calculations.

### A.3 Does the early-exit fee apply to `VaultClawback`?

No. Section 3.5 supersedes the parent 3.7 provision stating that clawback transactions must respect future fees or penalties. A clawback removes the full pre-fee asset amount and burns the corresponding shares across all phases and fee rates.

### A.4 Can a depositor re-deposit into the Vault after an early exit?

No. `VaultDeposit` transactions remain prohibited throughout the Investment phase. An early exit cannot be reversed during the term.

### A.5 Does an early exit affect outstanding loans or broker cover capital?

No. Early withdrawals draw exclusively from uncommitted liquidity (`Vault.AssetsAvailable`). They do not modify outstanding `Loan` entries, `LoanBroker.DebtTotal`, or `CoverAvailable`. The broker's first-loss capital requirement remains pegged to `DebtTotal`.
