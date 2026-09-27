# XLS-draft: Post-Dated Checks (`DeliverAfter` Execution Window for XRPL Checks)

```
Title:       Post-Dated Checks for Subscriptions, Deferred Settlement & Non-Custodial Estate Planning
Author:      Chris Thompson
Status:      Draft
Type:        Standards Track (Amendment)
Created:     2026-08-06
Updated:     2026-09-27
Amendment:   featurePostDatedChecks
```

---

## Abstract

This proposal introduces an optional `DeliverAfter` timestamp field to the existing `CheckCreate` transaction on the XRP Ledger. By enforcing an on-chain start time before which a check cannot be cashed, this amendment enables **Post-Dated Checks**. 

This amendment solves three major architectural challenges across the ecosystem:
1. **Lightweight Subscriptions & Deferred Settlement**: Provides a user-sovereign alternative to heavy recurring subscription proposals (such as [XLS-78](https://github.com/XRPLF/XRPL-Standards/tree/master/XLS-0078-subscriptions)) by reusing the battle-tested XRPL `Check` ledger engine (`ltCHECK`). Users can issue a series of post-dated checks in a single atomic batch transaction (up to the current XLS-56d protocol limit of **8 checks per batch**, or **12** if the batch limit is expanded by a future amendment) while retaining full unilateral cancellation rights via `CheckCancel`.
2. **Non-Custodial Estate Planning & Trustless Dead-Man Switches**: Provides a minimal, zero-bloat alternative to complex inheritance proposals (such as [XLS-91d](https://github.com/XRPLF/XRPL-Standards/pull/217) `SetBeneficiary`). By combining `DeliverAfter` with `CheckCash`'s native partial-delivery mechanic (`sfDeliverMin`), an account owner can configure an estate succession check that enables the beneficiary to dynamically sweep liquid balances upon maturity without locking capital upfront in escrows or risking premature execution in multisig arrangements.
3. **Milestone Trust Funds, Milestone Vesting & Deferred Settlements**: Solves the fundamental constraint of `EscrowCreate` (total capital lockup) by enabling milestone gifts (e.g., reaching age of majority), enterprise employee retention bonuses, and tax-deferred legal installments to remain liquid and yield-earning in the payer's wallet until maturity, while preserving unilateral cancellation authority (`CheckCancel`).

---

## Motivation

### 1. The Problem with Complex Subscription Amendments (XLS-78)
Proposals like [XLS-78](https://github.com/XRPLF/XRPL-Standards/tree/master/XLS-0078-subscriptions) attempt to solve recurring payments by introducing an entire new subscription ledger engine (`ltSUBSCRIPTION`), along with custom claim loops, specialized period counters, and new transaction types (`SubscriptionCreate`, `SubscriptionClaim`, `SubscriptionCancel`). 

This approach adds significant protocol complexity, increases ledger state bloat, and forces validators to maintain complex state machines for a feature that can be achieved with existing primitives.

### 2. The Problem with Complex Inheritance Amendments (XLS-91d)
Proposals like [XLS-91d](https://github.com/XRPLF/XRPL-Standards/pull/217) (`SetBeneficiary`) attempt to solve estate succession and account recovery by introducing dedicated inheritance primitives, new transaction types, and on-chain inactivity tracking. This design introduces severe structural drawbacks:
* **Protocol Bloat & Attack Surface**: Modifies core account state (`AccountRoot`) or introduces new state objects to store `sfBeneficiary` and `sfTimeLock`, requiring specialized revocation flows and validation logic.
* **The Inactivity Heuristic Trap**: Defining "inactivity" or "death" on a decentralized ledger is notoriously unreliable. Automated airdrops, trustline distributions, or validator payouts can misclassify active users as deceased, while malicious actors can seek edge cases in sequence tracking to trigger early execution.
* **The Multi-Asset Sweep Problem**: Automatically reassigning or transferring all trustlines, token balances, and NFTs in a single inheritance transaction creates massive transactor complexity and introduces Denial-of-Service (DoS) vectors against validators.
* **Capital Lockup vs. Collusion**: Existing workarounds—such as locking funds into `Escrow` or using multi-sig thresholds (e.g. 2-of-3 with an executor)—either destroy capital liquidity while the owner is alive or expose the owner to premature theft through signer collusion.

### 3. The Problem with Escrow Capital Immobilization
Conditional payments on the XRPL currently rely on `EscrowCreate`. While effective for trustless counterparty atomic delivery, Escrow enforces rigid capital immobilization:
* **Total Illiquidity**: Once capital is committed to an escrow, the creator cannot deploy, trade, or access those funds under any circumstances until the escrow is either completed or cancelled after `CancelAfter`.
* **Zero Yield / Productive Utility**: Capital locked in escrow sits completely idle, unable to generate returns in Single-Asset Vaults or automated market maker (AMM) liquidity pools.
* **Lack of Unilateral Creator Cancellation**: If a parent sets up an escrow for their child's 18th or 21st birthday, the funds are untouchable for years—even if an catastrophic family medical emergency or financial bankruptcy occurs in the interim.

### 4. The Post-Dated Check Solution
The XRP Ledger already possesses a robust, secure `Check` primitive (`ltCHECK`). However, `CheckCreate` currently only supports an `Expiration` timestamp (the cutoff *after* which a check can no longer be cashed). It lacks a `DeliverAfter` timestamp (the start time *before* which a check cannot be cashed).

By adding `DeliverAfter` to `CheckCreate`:
1. **Zero New Ledger Object Types**: Reuses existing `ltCHECK` objects.
2. **User Sovereignty & Security**: The user maintains total custody. If a user wishes to cancel a subscription, update an estate plan, or revoke a milestone gift, they simply submit a `CheckCancel` transaction for remaining un-cashed checks.
3. **Active Capital Liquidity**: Payer funds remain liquid and can generate yield across DeFi primitives (AMM, Vaults) right up until the check is cashed, subject only to the standard owner-reserve increment per active check object.
4. **Batching Efficiency**: Under current XRPL Batch rules (XLS-56d), a user can sign up to **8 post-dated checks in a single batch transaction** (e.g. 8 billing cycles). If the batch size limit is later amended to 12, full annual 12-month coverage is unlocked automatically.
5. **Natural Renewal Bounds**: Forcing a re-authorization boundary every 8 billing periods prevents forgotten "zombie" subscriptions from draining user funds indefinitely.
6. **Trustless Dead-Man & Milestone Execution**: A check post-dated for future delivery cannot be cashed by anyone (even the beneficiary) before maturity (`tecNO_PERMISSION`), while maintaining full unilateral cancellation rights for the issuer.

---

## Specification

### 1. Transaction Field Modification: `CheckCreate`

Add an optional `DeliverAfter` field to the `CheckCreate` transaction format.

| Field | JSON Type | Internal Type | Required? | Description |
| :--- | :--- | :--- | :--- | :--- |
| `DeliverAfter` | Number | `STUInt32` | Optional | Time in seconds since the Ripple Epoch after which this check becomes cashable. |

#### Field Constraints:
- **Amendment Gating**: If the `featurePostDatedChecks` amendment is not enabled, any `CheckCreate` transaction containing `DeliverAfter` MUST fail with `temDISABLED`.
- **Value Validation**: If `DeliverAfter` is specified with a value of `0`, the transaction MUST fail with `temBAD_EXPIRATION`.
- **Temporal Ordering**: If both `DeliverAfter` and `Expiration` are specified, validation MUST enforce `DeliverAfter < Expiration`. Otherwise, the transaction MUST fail with `temBAD_EXPIRATION`.

> [!NOTE]
> **Client Implementation Note (Consensus Close-Time Resolution)**:
> In the XRP Ledger, ledger close times are rounded to the consensus close-time resolution (which dynamically adjusts between 2 and 20 seconds, typically ~3–5 seconds). Consistent with `EscrowCreate` (`FinishAfter` and `CancelAfter`), the consensus engine validates only strict mathematical ordering (`DeliverAfter < Expiration`). Client applications and wallets setting both fields should ensure an execution window sufficiently wide (e.g., several minutes or days) so that at least one ledger close event falls strictly within the cashable interval (`DeliverAfter < parent_close_time < Expiration`).

---

### 2. Ledger Object Modification: `Check` (`ltCHECK`)

Update the `Check` ledger entry structure to store the optional `DeliverAfter` field.

| Field | JSON Type | Internal Type | Required? | Description |
| :--- | :--- | :--- | :--- | :--- |
| `DeliverAfter` | Number | `STUInt32` | Optional | The timestamp before which this check cannot be cashed. |

---

### 3. Execution & Validation Rules

#### `CheckCash` Validation Logic
When a payee submits a `CheckCash` transaction referencing a `Check` object:
1. If the `Check` contains a `DeliverAfter` field:
   - The engine checks the current parent ledger close time (`parent_close_time`).
   - If `parent_close_time <= Check.DeliverAfter`, the transaction MUST fail with error code `tecNO_PERMISSION`.
2. If `parent_close_time > Check.DeliverAfter`, the transaction proceeds to normal balance and trustline settlement.

---

### 4. Subscription & Dead-Man Cancellation & Reserve Recovery

When a user decides to cancel a subscription or update an estate plan, the cancellation mechanism relies on the existing `CheckCancel` primitive:

1. **Unilateral User Revocation**: The creator can submit `CheckCancel` for any or all un-cashed post-dated checks at any time. The payee/beneficiary cannot block or delay this action.
2. **Atomic Batch Cancellation**: Using a single atomic batch transaction (XLS-56d), a user can cancel all remaining post-dated checks (e.g., Checks 4 through 8) in 1 single wallet signature.
3. **Instant Reserve Refund**: Submitting `CheckCancel` immediately deletes the `ltCHECK` ledger objects and releases the associated owner reserve back to the creator (or to the sponsoring account if created under XLS-68 reserve sponsorship).

---

## Application 1: Recurring Subscriptions

### Standard Workflow Example (8-Check Batch Example)

1. **Subscriber Initiates**: Subscriber wants an 8-period recurring subscription at 15 XRP / period.
2. **Single Batch Issuance**: The subscriber signs a single batch transaction containing 8 `CheckCreate` items (respecting the current 8-item batch limit):
   - Check 1: `DeliverAfter` = the current Ripple-Epoch timestamp (or omit `DeliverAfter`), `Expiration` = Day 30
   - Check 2: `DeliverAfter` = Day 30, `Expiration` = Day 60
   - Check 3: `DeliverAfter` = Day 60, `Expiration` = Day 90
   - ...
   - Check 8: `DeliverAfter` = Day 210, `Expiration` = Day 240
3. **Payee Cashing**: On Day 30, the merchant's automated worker submits `CheckCash` for Check 2. The ledger verifies `parent_close_time > Day 30` and settles 15 XRP.
4. **Subscription Cancellation**: If the subscriber cancels after Month 2, their wallet app submits a single batch transaction containing `CheckCancel` for Checks 3 through 8. Future payments are revoked on-chain instantly, and all remaining reserves are refunded.

### The Batch Boundary as a Consumer Protection & Regulatory Asset

A common question regarding post-dated checks for subscriptions centers on the current XLS-56d batch transaction limit of **8 transactions per batch** (meaning an 8-period issuance cadence before requiring a user renewal):

#### 1. Global Regulatory Mandates for Subscription Continuance
Across major legal jurisdictions, recurring automated billing is subject to increasingly strict consumer protection statutes designed to eliminate perpetual, non-consensual extraction:
* **European Union (Consumer Rights Directive)**: Prohibits indefinite, inertia-based recurring contracts without proactive reminders and explicit opt-in confirmation.
* **United States (FTC "Click-to-Cancel" Rule & ROSCA)**: Requires clear, conspicuous notice, explicit informed consent prior to renewal, and simple cancellation mechanisms that prevent negative-option billing traps.
* **California Automatic Renewal Law (ARL)**: Mandates formal renewal notices 15 to 45 days prior to recurring billing events, requiring affirmative user re-consent for multi-month terms.
* **United Kingdom (Digital Markets, Competition and Consumers Act)**: Enforces mandatory pre-renewal reminders and clear statutory off-ramps so consumers do not passively renew forgotten subscriptions.

On a decentralized blockchain, a smart contract or automated engine cannot verify off-chain conditions—it cannot prove that a merchant actually sent a renewal email or that the subscriber read and accepted modified terms of service. 

By contrast, the **batch renewal boundary provides irrefutable, on-chain cryptographic proof of affirmative consumer re-consent**. A user signing a fresh batch of post-dated checks (via a single biometric slide in their wallet) provides verifiable proof that they still find sufficient value in the service to authorize the next billing block.

#### 2. Protection Against Predatory Extraction & Involuntary Account Drainage
In traditional banking, forgotten or unwanted subscriptions ("zombie subscriptions") represent a multi-billion-dollar predatory business model built on user inertia and dark patterns. While traditional banking customers have access to credit card chargebacks, fraud claims, and overdraft stops, **blockchain settlements are irreversible**. An automated on-chain subscription engine with perpetual debit authority poses an immense systemic risk to user sovereignty.

Enforcing a periodic re-authorization boundary prevents account drainage across common life disruptions:
* **Temporarily Inaccessible Keys**: Users who temporarily lose their hardware device, travel abroad, or misplace credentials cannot have their balances slowly bled dry by unmonitored perpetual pull engines.
* **Military Deployment**: Active-duty service members deployed overseas in low-connectivity environments are protected from months of background drain while unable to access wallets.
* **Medical Incapacitation & Long-Term Hospitalization**: Individuals incapacitated by accidents, illness, or comas are shielded from having their life savings depleted by automated background contracts.
* **Deceased Accounts & Estate Succession**: Heirs inheriting a lost or cold-storage wallet do not inherit an empty shell drained by dozens of forgotten background recurring debits.
* **Unused / Abandoned Services**: Prevents merchants from silently extracting payments long after an application has been uninstalled or forgotten.

To characterize requiring a subscriber to execute a single 2-second biometric slide once every 8 billing periods as an "inconvenience" is to advocate for predatory extraction architectures. A decentralized financial protocol must prioritize user asset sovereignty over merchant convenience.

#### 3. Decoupling Batch Protocol Limits from Check Architecture
The 8-period threshold is strictly an artifact of the conservative batch transaction limit established in XLS-56d (`max_batch_items = 8`). 
* If the ecosystem or merchant community desires an annual 12-month billing cycle, that parameter is governed entirely by XLS-56d and can be expanded via a dedicated batch parameter amendment (e.g., increasing the batch ceiling to 12 or 16).
* The post-dated check primitive itself is completely agnostic to batch size. The constraint lies in the batch transport layer, not in the architectural integrity of `DeliverAfter`.

---

## Application 2: Non-Custodial Dead-Man Switch & Estate Succession

### The "Dynamic Balance Sweep" Mechanic (`DeliverMin`)
In traditional banking, writing a check for more than the account balance results in a bounce. On the XRP Ledger, `CheckCash` features built-in partial delivery semantics via **`sfDeliverMin`**:

$$\text{xrpDeliver} = \min(\text{sendMax}, \text{srcLiquid})$$

Where `srcLiquid` is the sender's account balance minus reserve requirements at the exact time of cashing.

By creating a check with a high `SendMax` (e.g. $100,000,000\text{ XRP}$) and having the beneficiary cash it with `DeliverMin: 1 drop`, partial delivery is bounded by `SendMax` and the payer's available liquid balance minus reserves and transaction fees. When cashed upon or after maturity, the transaction dynamically sweeps the available liquid balance (assuming the check has not expired or been canceled, and normal `CheckCash` settlement conditions are met; balance delivery fails with `tecPATH_PARTIAL` if available liquid balance is strictly below `DeliverMin`).

```mermaid
sequenceDiagram
    autonumber
    participant Alice as Alice (Living Wallet)
    participant Ledger as XRPL Consensus
    participant Jen as Jen (Beneficiary)

    Alice->>Ledger: CheckCreate (SendMax: 100M XRP, DeliverAfter: +365d, Dest: Jen)
    Note over Alice: Balance remains liquid. 0 capital locked.

    Note over Ledger,Jen: Scenario A: Premature Cashing Attempt (Day 30)
    Jen->>Ledger: CheckCash (DeliverMin: 1 drop)
    Ledger-->>Jen: tecNO_PERMISSION (parentCloseTime < DeliverAfter)

    Note over Alice,Ledger: Scenario B: Annual Renewal (Day 350, Alice Alive)
    Alice->>Ledger: Batch: CheckCancel(old) + CheckCreate(+365d)
    Ledger-->>Alice: tesSUCCESS (Timer renewed, 20 drops fee at base rate)

    Note over Ledger,Jen: Scenario C: Maturity Claim (Day 366, Alice Deceased)
    Jen->>Ledger: CheckCash (DeliverMin: 1 drop)
    Ledger->>Jen: tesSUCCESS (Sweeps available liquid balance)
```

### The Trustless 2-of-2 Hybrid Legal Vault
For users desiring an extra layer of fiduciary separation:
1. **Estate Account (`W_estate`)**:
   - Master key disabled (`asfDisableMasterKey`).
   - `SignerListSet` configured with **Quorum = 2**:
     - `Signer_A` (Weight 1): Seed A deposited in a sealed testamentary envelope with an estate attorney (released only upon verified death certificate).
     - `Signer_B` (Weight 1): Seed B held directly by the spouse/beneficiary.
2. **Funding**: Alice writes a post-dated check with `DeliverAfter: +1 Year` to `W_estate`.
3. **Zero Financial Exposure to Third-Party Disasters**:
   - If the lawyer's office burns down, the lawyer dies, or the firm dissolves: **Alice loses $0**.
   - Alice simply submits `CheckCancel` from her living wallet, generates new seeds for a new firm, and issues a fresh check.

### Fail-Safe Mechanics: What Happens if a User Misses Their Renewal?

A common failure mode in smart contract dead-man switches is automatic liquidation: if an owner is hospitalized or on vacation and misses a timer, their funds are irreversibly liquidated. 

Post-Dated Checks eliminate this hazard entirely through pull-based semantics:
1. **No Automatic Push**: The ledger does not automatically execute or move funds upon reaching `DeliverAfter`. It merely unlocks cashing permission.
2. **Exclusive Beneficiary Authority**: Only the designated beneficiary (`sfDestination`)—or an authorized account delegate operating under XLS-75 (delegated transactions)—possesses authorization to submit `CheckCash`. No unauthorized third-party bots, MEV searchers, or validators can claim or drain the funds.
3. **Information Asymmetry**: If the owner is still alive and simply missed their renewal date, the beneficiary is typically not actively monitoring the mempool or expecting an execution.
4. **Perpetual Unilateral Recall**: As long as the check has not been cashed, the living owner retains unilateral authority to submit `CheckCancel` at Day 370, Day 400, or any later date. The owner can cancel the matured check or roll it forward into a new one at any time with a single transaction.

---

## Application 3: Milestone Trust Funds, Milestone Vesting & Deferred Settlements

While `EscrowCreate` exists on the XRP Ledger for conditional value transfers, Escrow enforces an immutable constraint: **mandatory capital immobilization**. Once funds are locked in Escrow, the creator cannot deploy, trade, or access that capital under any circumstances until `CancelAfter` (if configured) or condition fulfillment. Furthermore, Escrow lacks unilateral creator cancellation authority prior to maturity.

`CheckCreate` with `DeliverAfter` introduces a complementary economic primitive: **deferred settlement with active capital liquidity and unilateral creator cancellation**.

### 1. Milestone Trust Funds & Age-of-Majority Transfers
- **Use Case**: A parent wishes to transfer capital (e.g., 25,000 RLUSD or XRP) to their child upon reaching adulthood (e.g., 18th or 21st birthday) or graduation.
- **The Capital Trap with Escrow**: If placed in Escrow with a multi-year lockup, the parent completely loses access to those funds. If a severe family medical emergency, legal expense, or sudden financial catastrophe strikes during that window, the parent cannot access their own capital.
- **The Post-Dated Check Model**:
  - The parent issues a check with `DeliverAfter: <18th_Birthday_Timestamp>`.
  - The capital remains unencumbered in the parent's wallet, continuing to earn AMM liquidity yields, Single-Asset Vault interest, or serving as an active emergency cushion.
  - **Unilateral Cancellation / Voiding Authority**: If the family encounters financial distress, or if circumstances change prior to maturity, the parent submits `CheckCancel` at any time to immediately void the check and release the owner reserve.
  - Upon reaching maturity, the adult child simply submits `CheckCash` to claim the gift.

### 2. Milestone Vesting & Employee Retention
- **Use Case**: An enterprise issues retention bonuses or performance tranches maturing annually across a multi-year employment agreement.
- **The Problem with Escrow**: Escrow forces the company to tie up working capital years in advance in rigid vaults. Revoking unvested tranches requires complex multisig, oracle arbitration, or mutual consent.
- **The Post-Dated Check Model**:
  - The corporate treasury signs post-dated checks maturing at Month 12, Month 24, and Month 36.
  - The treasury retains full operational custody and treasury yield on its working capital.
  - **Separation Voiding Authority**: If the employee voluntarily resigns, is terminated for cause, or breaches covenants prior to a milestone, the company invokes `CheckCancel` to void un-matured checks on-chain.
  - If the employee remains in good standing, each tranche becomes cashable on its exact maturity date.

### 3. Structured Legal Settlements & Fiscal Tax Installments
- **Use Case**: Commercial contract disputes, divorce decrees, or buyout agreements requiring installment payments structured across separate fiscal tax years (e.g., January 2 of consecutive calendar years) to avoid lump-sum tax realization.
- **The Post-Dated Check Model**:
  - Payer writes post-dated checks maturing on the first business day of future tax years.
  - The recipient is cryptographically prevented from pulling funds prematurely into the current tax year (`parentCloseTime < DeliverAfter` enforces `tecNO_PERMISSION`).
  - Ensures strict adherence to statutory payment timing without requiring an expensive legal escrow agent or escrow service fees.

### Comparative Architectural Analysis: Capital Immobilization vs. Liquid Deferral

| Dimension | `EscrowCreate` | `CheckCreate` with `DeliverAfter` |
| :--- | :--- | :--- |
| **Capital State** | Fully locked and immobilized on-ledger | Fully sovereign, unencumbered, and liquid |
| **Productive Yield** | Zero (Capital sits idle in escrow ledger object) | Retains ability to earn AMM or Vault yields |
| **Creator Cancellation** | Impossible prior to `CancelAfter` timestamp | Unilateral cancellation (`CheckCancel`) at any time |
| **Counterparty Assurance** | Guaranteed collateral (pre-funded) | Balance availability at cashing (settlement risk) |
| **Primary Optimal Fit** | Trustless counterparty trades & atomic swaps | Milestone gifts, employee retention, structured settlements |

---

## Reference xApp Architecture: Zero-Cost Static Dead-Man Client

To maximize accessibility, this standard can be supported by an open-source, zero-backend xApp ("EstateX / XRPL Heirloom"):

### 1. Zero-Cost, Serverless Architecture
- **Permanent Free Hosting**: Statically compiled HTML/TypeScript hosted indefinitely on **GitHub Pages** or **Cloudflare Pages** ($0 cost, resilient uptime, zero server maintenance).
- **Non-Custodial**: No private keys ever touch the application. All signing operations route securely via standard Xaman (Xumm) SDK or WalletConnect deep links.
- **Local Storage**: Stores tracking metadata (`CheckID`, beneficiary address, maturity timestamp) in encrypted local browser storage.

### 2. The 3-Question Onboarding Wizard
1. **"Who is your beneficiary?"**: Enter beneficiary `r-address` (or a 2-of-2 estate vault).
2. **"What would you like to pass on?"**: Select one asset per check. For native XRP, the app sets `SendMax: 100,000,000 XRP` paired with beneficiary cashing via `DeliverMin: 1 drop`; for an IOU/RLUSD, `SendMax` and `DeliverMin` must both be amounts in that issued currency.
3. **"Set renewal cadence"**: Default: **365 Days** (1 Year).

**Action**: User taps **"Activate Protection"**. The xApp generates `CheckCreate` with `DeliverAfter: now + 365 days` and prompts the user for 1 biometric signature in Xaman.

### 3. Frictionless Renewal Reminders (Opt-In)
Because the app has no backend database, users can opt into two native, zero-infrastructure reminder channels:
- **1-Click Calendar Sync (`.ics` / Google / Apple Calendar)**: Adds an annual reminder to the user's phone, laptop, and Apple Watch for **Day 350** (15 days prior) and **Day 358** (7 days prior), completely independent of web browsers or servers.
- **Xaman Mobile Push Notifications**: Subscribes the user to direct push notifications via Xaman's native notification dispatch.

### 4. The 1-Tap Annual Renewal (XLS-56d Atomic Batch)
When the reminder appears on Day 358:
- Prompt: *"Your Dead-Man Check matures in 7 days. Are you alive and well? Do you want to renew with [rBeneficiary]?"*
- User taps **"Renew for 1 Year"**.
- The xApp crafts a single **XLS-56d Atomic Batch Transaction** containing:
  1. `CheckCancel` (cancels expiring check, **immediately releasing the owner reserve**).
  2. `CheckCreate` (creates new check for next 365 days, **reusing the refunded reserve**).
- **User Action**: Exactly **1 biometric confirmation** in Xaman.
- **Net Cost**: ~20 drops ($0.00001). **Zero net change in account reserve**.

### 5. Beneficiary Claim Portal ("Heir Claim")
1. Beneficiary opens the xApp and connects their Xaman wallet.
2. The app scans the ledger for checks where `Destination == Beneficiary` and verifies `parentCloseTime >= DeliverAfter`.
3. If mature, the app displays: *"Estate Check Ready: [Amount] XRP Available"*.
4. Beneficiary taps **"Claim Estate"**, submitting `CheckCash` with `DeliverMin: 1 drop`.
5. The ledger dynamically sweeps available liquid balance into the beneficiary's wallet in ~3.5 seconds.

### 6. Synergy with XLS-75 (Delegated Cashing & Proof-of-Burn)
1. **Third-Party Executor Cashing**: Under XLS-75, a beneficiary can execute `DelegateSet` granting permission for `CheckCash` to an executor. The executor submits `CheckCash` on behalf of the beneficiary (`Delegate: rExecutor`), and funds transfer directly into the beneficiary's wallet without the executor ever holding custody.
2. **Delegated Blackhole Settlement (Proof-of-Burn)**: An account (`rBlackhole`) can execute `DelegateSet` granting permission for `CheckCash` to an external watcher, then permanently disable its master key (`asfDisableMasterKey`). If a post-dated check targeting `rBlackhole` reaches maturity, the watcher submits `CheckCash` on behalf of `rBlackhole`, sweeping and permanently burning the liquid balance without needing private key access.

---

## Comparison With Alternative Proposals

### Comparison 1: Subscriptions (XLS-78 vs. XLS-XXd)

| Feature | XLS-78 Subscriptions | XLS-XXd Post-Dated Checks |
| :--- | :--- | :--- |
| **New Ledger Object** | Requires new `ltSUBSCRIPTION` object | **Zero** new objects (uses `ltCHECK`) |
| **Protocol Footprint** | Large (4 new transaction types) | **Minimal** (1 field added to `CheckCreate`) |
| **User Control** | Complex cancellation / pause states | **Instant** `CheckCancel` batch revocation |
| **Merchant Risk** | Subject to balance failure at claim | Identified immediately upon cashing attempt |
| **Re-Authorization Boundary** | Can run indefinitely | Enforces explicit 8-check user review (or 12 if batch size amended) |

### Comparison 2: Inheritance & Estate Planning (XLS-91d vs. XLS-XXd)

| Metric / Scenario | XLS-91d (`SetBeneficiary`) | XLS-XXd Post-Dated Checks (`DeliverAfter`) |
| :--- | :--- | :--- |
| **New Transaction Types** | $\ge 1$ (`SetBeneficiary`) | **Zero** (re-uses `CheckCreate`, `CheckCash`, `CheckCancel`) |
| **Ledger Object Bloat** | Modifies `AccountRoot` or creates new entry | **Zero** (stores optional field in `ltCHECK`) |
| **Engine Code Impact** | High (inactivity tracking, new claim handlers) | **~37 lines of C++** in `xrpld` |
| **Fund Sweeping Mechanism** | Unspecified / complex multi-trustline loops | **Native** via `DeliverMin: 1 drop` in `CheckCash` |
| **Premature Execution Risk** | High if sequence tracking is gamed | **Zero** (strictly enforced by `parent_close_time`) |
| **Liquidity While Living** | Uncertain / frozen status states | **Fully Liquid**; user spends freely every day |
| **Third-Party Custodial Risk**| Dependent on external attestation/notary | **Zero**; full unilateral cancellation via `CheckCancel` |

---

## Technical Impact Assessment & Validator Resource Profile

To evaluate the operational impact on node operators and full-history validators, this section breaks down the computational, memory, state storage, and execution characteristics of `featurePostDatedChecks`:

### 1. Engine & Protocol Footprint
* **Engine Transactor Modification**: Exactly **37 lines of C++** across `CheckCreate.cpp` and `CheckCash.cpp`.
* **New Ledger Objects**: **Zero**. Re-uses the existing `ltCHECK` entry type.
* **New Transaction Types**: **Zero**. Modifies existing `ttCHECK_CREATE` (Type 16) and `ttCHECK_CASH` (Type 17).
* **Protocol Invariants**: Completely preserved. Evaluates deterministic time comparisons via `parentCloseTime` using the native `after()` helper.

### 2. Execution Path Analysis
* **Unused Execution Paths (Standard Checks)**:
  * For transactions that omit `DeliverAfter`, execution impact is **zero**.
  * `CheckCreate` skips serializing the optional field.
  * `CheckCash` checks field presence via `isFieldPresent()`; if absent, it continues standard settlement without delay.
* **In-Window Execution (Valid Cashing)**:
  * Evaluates a single unsigned 32-bit integer comparison in `preclaim` (`parentCloseTime > DeliverAfter`).
  * Incurs negligible CPU cycles before transitioning to standard payment logic.
* **Premature Cashing Rejection**:
  * If cashed before maturity, the transaction fails immediately in `preclaim` with `tecNO_PERMISSION`.
  * **Fee Burn**: Destroys only the baseline transaction fee (10–20 drops) to deter spam; executes zero state writes or balance adjustments.
  * **Client Mitigation**: Wallets (e.g. Xaman) and client SDKs read `DeliverAfter` directly from the ledger object and disable submission until maturity, preventing unnecessary network traffic.

### 3. Resource & Infrastructure Characteristics
* **Timer Queues & Daemon Work**: **Zero**. Unlike automated subscription proposals (e.g., XLS-78) or escrow sweeps, post-dated checks introduce no background pollers, timer queues, or engine wakeups. State is completely passive until an external transaction calls `CheckCash`.
* **Memory (RAM) & Compute**: Zero additional in-memory caches, lookup structures, or cryptographic routines.
* **Storage & State Overhead**:
  * Exactly one optional 4-byte `STUInt32` field (`sfDeliverAfter`) on `ltCHECK` only when explicitly specified.
  * Network overhead is minimal: 100,000 active concurrent post-dated checks require ~400 KB of total ledger state.
  * Checks are ephemeral: cashing (`CheckCash`) or cancellation (`CheckCancel`) completely prunes the object and field from the ledger, recovering the owner reserve.

### 4. Operational Summary Matrix

| Metric | Non-Dated Checks | Post-Dated Checks (In-Window) | Post-Dated Checks (Premature) |
| :--- | :--- | :--- | :--- |
| **CPU Delta** | 0 | 1 comparison (`uint32`) | 1 comparison (`uint32`) |
| **RAM Delta** | 0 | 0 | 0 |
| **Background Processes** | None | None | None |
| **State Storage Delta** | 0 bytes | +4 bytes (`STUInt32`) | 0 (rejected before state modification) |
| **Transaction Result** | `tesSUCCESS` | `tesSUCCESS` | `tecNO_PERMISSION` |
| **Client Mitigation** | N/A | N/A | UI disabled until maturity |

### 5. Technical Debt vs. Market Demand Analysis
* **Zero Latent Debt**: If zero post-dated checks are created following activation, the network incurs zero bytes of residual storage bloat and zero background processing overhead. It is a micro-enhancement to an established primitive, not an unproven monolithic engine.
* **Capturing Verified Ecosystem Demand**: The substantial community debate surrounding XLS-78 (Subscriptions) and XLS-91d (Inheritance) demonstrates that demand for deferred commercial payments and non-custodial succession exists. `featurePostDatedChecks` satisfies both needs without saddling validators with new transaction types, custom claim loops, or permanent state bloat.

---

## Reference Implementation (`xrpld` Code Diff)

A complete, production-ready reference implementation tested against `xrpld 3.5.0-b0` (passing all 2,511 unit test assertions with 0 failures) is published on GitHub at [`bigcjat/rippled@feature/post-dated-checks`](https://github.com/bigcjat/rippled/tree/feature/post-dated-checks).

The entire proposal is implemented across 6 existing files in `xrpld` with zero new object types or transactors:

### 1. Register Feature Flag
`include/xrpl/protocol/detail/features.macro`:
```diff
+XRPL_FEATURE(PostDatedChecks,             Supported::Yes, VoteBehavior::DefaultNo)
```

### 2. Define Serialized SField
`include/xrpl/protocol/detail/sfields.macro`:
```diff
+// 32-bit integers
+TYPED_SFIELD(sfDeliverAfter,             UINT32,    86)
```

### 3. Register Optional Field in `CheckCreate`
`include/xrpl/protocol/detail/transactions.macro`:
```diff
 TRANSACTION(ttCHECK_CREATE, 16, CheckCreate, ({.delegable = Delegation::Delegable}), ({
     {sfDestination, SoeRequired},
     {sfSendMax, SoeRequired, SoeMptSupported},
     {sfExpiration, SoeOptional},
     {sfDestinationTag, SoeOptional},
     {sfInvoiceID, SoeOptional},
+    {sfDeliverAfter, SoeOptional},
 }))
```

### 4. Register Optional Field in `ltCHECK` Ledger Object
`include/xrpl/protocol/detail/ledger_entries.macro`:
```diff
 LEDGER_ENTRY(ltCHECK, 0x0043, Check, check, ({
     {sfAccount,              SoeRequired},
     {sfDestination,          SoeRequired},
     {sfSendMax,              SoeRequired},
     {sfSequence,             SoeRequired},
     {sfOwnerNode,            SoeRequired},
     {sfDestinationNode,      SoeRequired},
     {sfExpiration,           SoeOptional},
+    {sfDeliverAfter,         SoeOptional},
     {sfInvoiceID,            SoeOptional},
     {sfSourceTag,            SoeOptional},
     {sfDestinationTag,       SoeOptional},
     {sfPreviousTxnID,        SoeRequired},
     {sfPreviousTxnLgrSeq,    SoeRequired},
 }))
```

### 5. Enforce Ordering in `CheckCreate` Transactor
`src/libxrpl/tx/transactors/check/CheckCreate.cpp`:

In `CheckCreate::preflight`:
```diff
+    auto const optDeliverAfter = ctx.tx[~sfDeliverAfter];
+    if (optDeliverAfter)
+    {
+        if (!ctx.rules.enabled(featurePostDatedChecks))
+            return temDISABLED;
+
+        if (*optDeliverAfter == 0)
+        {
+            JLOG(ctx.j.warn()) << "Malformed transaction: bad deliver after";
+            return temBAD_EXPIRATION;
+        }
+    }
+
     if (auto const optExpiry = ctx.tx[~sfExpiration])
     {
         if (*optExpiry == 0)
         {
             JLOG(ctx.j.warn()) << "Malformed transaction: bad expiration";
             return temBAD_EXPIRATION;
         }
+
+        if (optDeliverAfter && *optExpiry <= *optDeliverAfter)
+        {
+            JLOG(ctx.j.warn()) << "Malformed transaction: expiration must be after deliver after";
+            return temBAD_EXPIRATION;
+        }
     }
```

In `CheckCreate::doApply`:
```diff
     if (auto const expiry = ctx_.tx[~sfExpiration])
         sleCheck->setFieldU32(sfExpiration, *expiry);
+    if (auto const deliverAfter = ctx_.tx[~sfDeliverAfter])
+        sleCheck->setFieldU32(sfDeliverAfter, *deliverAfter);
```

### 6. Enforce Maturity Gate in `CheckCash` Transactor
`src/libxrpl/tx/transactors/check/CheckCash.cpp`:

In `CheckCash::preclaim`:
```diff
     if (hasExpired(ctx.view, sleCheck->at(~sfExpiration)))
     {
         JLOG(ctx.j.warn()) << "Cashing a check that has already expired.";
         return tecEXPIRED;
     }
+
+    if (ctx.view.rules().enabled(featurePostDatedChecks))
+    {
+        if (auto const deliverAfter = sleCheck->at(~sfDeliverAfter))
+        {
+            if (!after(ctx.view.parentCloseTime(), *deliverAfter))
+            {
+                JLOG(ctx.j.warn()) << "Cashing a check before deliver after time.";
+                return tecNO_PERMISSION;
+            }
+        }
+    }
```

### 7. Existing Native Cancellation (`CheckCancel.cpp`)
Zero modifications required. `CheckCancel.cpp` lines 41–55 enforce canonical cancellation rules: prior to expiration, either the check creator (`Account`) or recipient (`Destination`) may cancel the check; once expired, any account may cancel it to remove the ledger object and return the reserve to the reserve owner or sponsor.

### 8. Unit Test Suite (`Check_test.cpp`)
Implemented under `src/test/app/Check_test.cpp` via `testPostDatedChecks(features)` with helper `DeliverAfter` in `src/test/jtx/TestHelpers.h`. Passes all 15 cases (2,511 test assertions) with 0 failures:
- Disabled feature rejection (`temDISABLED`)
- Zero timestamp rejection (`temBAD_EXPIRATION`)
- Inverted boundary validation `DeliverAfter >= Expiration` (`temBAD_EXPIRATION`)
- Premature cashing prevention (`tecNO_PERMISSION`)
- Post-maturity cashing success (`tesSUCCESS`)
- Dynamic balance sweep (`DeliverMin: 1 drop`)
- Issuer unilateral cancellation (`CheckCancel`) before maturity

---

## Backwards Compatibility

This amendment is fully backwards compatible:
- Existing `CheckCreate` transactions without `DeliverAfter` continue to function identically.
- Clients and wallets that do not support `DeliverAfter` must not be assumed to preserve it; applications must use amendment-aware serialization and signing.
- Amendments required: `featurePostDatedChecks`.

---

## Security Considerations

1. **Deterministic Time Sync**: Uses the immutable `parent_close_time` of validated ledgers to ensure deterministic evaluation across all validators via the native `after()` consensus helper.
2. **No Reserve Exhaustion**: Checks consume standard `ltCHECK` owner reserves, which are fully refunded upon cashing or cancellation.
3. **Replay Protection**: Each check possesses a unique, immutable `CheckID` generated at creation time, preventing replay attacks.
4. **Zero-Lockup Sovereignty**: Because checks do not lock funds, user funds remain fully sovereign and unencumbered until the exact moment of cashing.

