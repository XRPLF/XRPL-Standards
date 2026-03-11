<pre>
  xls: [To be assigned]
  title: Concentrated Liquidity Automated Market Maker
  description: A capital-efficient AMM allowing liquidity providers to concentrate capital within specific price ranges
  author: Romain Thepaut (@RomThpt)
  category: Amendment
  status: Draft
  proposal-from: https://github.com/XRPLF/XRPL-Standards/discussions/427
  requires: XLS-20
  created: 2026-01-29
  updated: 2026-03-11
</pre>

# Concentrated Liquidity Automated Market Maker

## Index

1. [Abstract](#1-abstract)
2. [Motivation](#2-motivation)
3. [Introduction](#3-introduction)
    - 3.1 [Terminology](#31-terminology)
    - 3.2 [System Diagram](#32-system-diagram)
    - 3.3 [Summary](#33-summary)
4. [Specification](#4-specification)
    - 4.1 [Ledger Entries](#41-ledger-entries)
        - 4.1.1 [CLAMM](#411-ledger-entry-clamm)
        - 4.1.2 [CLAMMTick](#412-ledger-entry-clammtick)
        - 4.1.3 [CLAMMPosition](#413-ledger-entry-clammposition)
    - 4.2 [Transactions](#42-transactions)
        - 4.2.1 [CLAMMCreate](#421-transaction-clammcreate)
        - 4.2.2 [CLAMMDeposit](#422-transaction-clammdeposit)
        - 4.2.3 [CLAMMWithdraw](#423-transaction-clammwithdraw)
        - 4.2.4 [CLAMMSwap](#424-transaction-clammswap)
        - 4.2.5 [CLAMMCollectFees](#425-transaction-clammcollectfees)
        - 4.2.6 [CLAMMVote](#426-transaction-clammvote)
        - 4.2.7 [CLAMMBid](#427-transaction-clammbid)
    - 4.3 [RPCs](#43-rpcs)
        - 4.3.1 [clamm_info](#431-rpc-clamm_info)
        - 4.3.2 [clamm_positions](#432-rpc-clamm_positions)
        - 4.3.3 [clamm_ticks](#433-rpc-clamm_ticks)
        - 4.3.4 [clamm_quote](#434-rpc-clamm_quote)
    - 4.4 [Continuous Auction Mechanism](#44-continuous-auction-mechanism)
    - 4.5 [Math and Precision](#45-math-and-precision)
    - 4.6 [Swap Algorithm](#46-swap-algorithm)
    - 4.7 [Payment Engine Integration](#47-payment-engine-integration)
5. [Rationale](#5-rationale)
6. [Backwards Compatibility](#6-backwards-compatibility)
7. [Test Plan](#7-test-plan)
8. [Security Considerations](#8-security-considerations)
9. [Appendix](#9-appendix)
    - A. [FAQ](#appendix-a-faq)
    - B. [Design Discussion](#appendix-b-design-discussion)

---

## 1. Abstract

This specification defines a Concentrated Liquidity Automated Market Maker (CLAMM) for the XRP Ledger. Unlike the existing XLS-30 AMM which distributes liquidity uniformly across all prices, CLAMM allows liquidity providers (LPs) to concentrate their capital within specific price ranges. This design improves capital efficiency by up to 4000x for stablecoin pairs, enables tradeable LP positions via NFTokens, and allows fee collection without liquidity removal. The specification introduces three new ledger entry types (`CLAMM`, `CLAMMTick`, `CLAMMPosition`), seven new transaction types, and integrates with the existing XRPL payment engine for automatic routing.

---

## 2. Motivation

The current XRPL AMM (XLS-30) uses a constant product formula (`x * y = k`) where liquidity is distributed uniformly across all prices from 0 to infinity. This approach has several limitations:

### 2.1 Capital Inefficiency

In XLS-30, most liquidity sits idle at price points far from the current market price. For example, in an XRP/USD pool trading at $0.50:

- Liquidity at $0.01 or $5.00 is rarely used
- LPs earn fees only on a tiny fraction of their capital
- Capital efficiency is approximately 0.5% for typical pairs

### 2.2 Fungible Position Limitations

XLS-30 uses fungible LPTokens where all LPs share the same position:

- All LPs have identical exposure across the entire price range
- Fee collection requires partial or full withdrawal
- Positions cannot be traded on secondary markets
- No differentiation between LP strategies

### 2.3 Concentrated Liquidity Benefits

This specification addresses these limitations by enabling:

| Feature            | XLS-30 AMM          | CLAMM                     |
| ------------------ | ------------------- | ------------------------- |
| Capital Efficiency | ~0.5%               | Up to 4000x improvement   |
| Price Range        | 0 to infinity       | Custom range per LP       |
| Position Type      | Fungible LPToken    | Unique NFToken            |
| Fee Collection     | Requires withdrawal | Collect anytime           |
| Position Trading   | Not possible        | Via NFToken marketplace   |
| LP Strategy        | One-size-fits-all   | Customizable per position |

---

## 3. Introduction

### 3.1 Terminology

| Term                 | Definition                                                                                          |
| -------------------- | --------------------------------------------------------------------------------------------------- |
| **Tick**             | A discrete price point. Each tick represents a 0.01% to 2% price change depending on the fee tier.  |
| **Tick Spacing**     | The minimum interval between usable ticks, determined by the fee tier.                              |
| **Liquidity**        | The `L` value in the constant product formula `x * y = L^2`. Higher liquidity means lower slippage. |
| **Position**         | An LP's liquidity deployment within a specific price range (lower tick to upper tick).              |
| **Active Liquidity** | Liquidity currently in range and earning fees based on the current price.                           |
| **Fee Tier**         | One of four predefined fee/tick-spacing combinations (STABLE, LOW, MEDIUM, HIGH).                   |
| **SqrtPrice**        | The square root of the price, stored as a Q64.96 fixed-point number for precision.                  |
| **Fee Growth**       | Accumulated fees per unit of liquidity, tracked globally and per-tick for fee distribution.         |

### 3.2 System Diagram

```
                                    +---------------------+
                                    |      NFToken        |
                                    |  (Position Token)   |
                                    +----------+----------+
                                               | owns
                                               v
+-------------+    references    +-------------------------+
|    CLAMM    |<-----------------|    CLAMMPosition        |
|   (Pool)    |                  |  - LowerTick            |
|             |                  |  - UpperTick            |
| - Asset     |                  |  - Liquidity            |
| - Asset2    |                  |  - FeesOwed             |
| - FeeTier   |                  +-------------------------+
| - SqrtPrice |                              |
| - Liquidity |                              | bounded by
| - Auction   |                              v
+------+------+                  +-------------------------+
       |                         |      CLAMMTick          |
       |                         |  - TickIndex            |
       | contains                |  - LiquidityNet         |
       +------------------------>|  - FeeGrowthOutside     |
                                 +-------------------------+
```

### 3.3 Summary

#### 3.3.1 Ledger Entries

| Ledger Entry    | Purpose                                                              |
| --------------- | -------------------------------------------------------------------- |
| `CLAMM`         | Pool state: current price, active liquidity, fee tier, auction state |
| `CLAMMTick`     | Per-tick data: liquidity boundaries, fee growth tracking             |
| `CLAMMPosition` | LP position: tick range, liquidity amount, uncollected fees          |

#### 3.3.2 Transactions

| Transaction        | Purpose                                                   |
| ------------------ | --------------------------------------------------------- |
| `CLAMMCreate`      | Create a new CLAMM pool                                   |
| `CLAMMDeposit`     | Add liquidity within a price range, mint position NFToken |
| `CLAMMWithdraw`    | Remove liquidity, optionally burn position NFToken        |
| `CLAMMSwap`        | Execute a swap through the pool                           |
| `CLAMMCollectFees` | Collect accumulated fees without removing liquidity       |
| `CLAMMVote`        | Vote on auction slot parameters                           |
| `CLAMMBid`         | Bid for the auction slot to capture arbitrage value       |

#### 3.3.3 RPCs

| RPC               | Purpose                        |
| ----------------- | ------------------------------ |
| `clamm_info`      | Get pool information           |
| `clamm_positions` | Query positions for an account |
| `clamm_ticks`     | Query tick data for a pool     |
| `clamm_quote`     | Get a swap quote               |

---

## 4. Specification

### 4.1 Ledger Entries

#### 4.1.1 Ledger Entry: `CLAMM`

The `CLAMM` ledger entry represents a concentrated liquidity pool.

##### 4.1.1.1 Object Identifier

**Key Space:** `0x0043` ("C" for CLAMM)

**ID Calculation Algorithm:**
The ID is calculated by hashing the key space prefix `0x0043`, the `Asset` issue, the `Asset2` issue, and the `FeeTier` value. This ensures one pool per asset pair per fee tier.

##### 4.1.1.2 Fields

| Field Name          | Constant | Required | JSON Type | Internal Type | Default Value | Description                           |
| ------------------- | -------- | -------- | --------- | ------------- | ------------- | ------------------------------------- |
| `LedgerEntryType`   | Yes      | Yes      | `string`  | UINT16        | `0x0043`      | Identifies this as a CLAMM object     |
| `Asset`             | Yes      | Yes      | `object`  | ISSUE         | N/A           | First asset in the pair               |
| `Asset2`            | Yes      | Yes      | `object`  | ISSUE         | N/A           | Second asset in the pair              |
| `FeeTier`           | Yes      | Yes      | `number`  | UINT8         | N/A           | Fee tier (0-3)                        |
| `TickSpacing`       | Yes      | Yes      | `number`  | UINT16        | N/A           | Derived from FeeTier                  |
| `TradingFee`        | No       | Yes      | `number`  | UINT32        | N/A           | Trading fee in 1/1,000,000            |
| `CurrentTick`       | No       | Yes      | `number`  | INT32         | N/A           | Current active tick index             |
| `SqrtPrice`         | No       | Yes      | `string`  | UINT128       | N/A           | Current sqrt price (Q64.96)           |
| `Liquidity`         | No       | Yes      | `string`  | UINT128       | `"0"`         | Currently active liquidity            |
| `FeeGrowthGlobal0`  | No       | Yes      | `string`  | UINT128       | `"0"`         | Global fee growth for Asset           |
| `FeeGrowthGlobal1`  | No       | Yes      | `string`  | UINT128       | `"0"`         | Global fee growth for Asset2          |
| `ProtocolFees0`     | No       | Yes      | `string`  | UINT64        | `"0"`         | Accumulated protocol fees for Asset   |
| `ProtocolFees1`     | No       | Yes      | `string`  | UINT64        | `"0"`         | Accumulated protocol fees for Asset2  |
| `AuctionSlot`       | No       | No       | `object`  | STOBJECT      | N/A           | Current auction slot holder (see 4.4) |
| `OwnerNode`         | No       | Yes      | `string`  | UINT64        | N/A           | Directory hint                        |
| `PreviousTxnID`     | No       | Yes      | `string`  | HASH256       | N/A           | Previous modifying transaction        |
| `PreviousTxnLgrSeq` | No       | Yes      | `number`  | UINT32        | N/A           | Previous modifying ledger             |

**Field Details:**

**Fee Tiers:**

| FeeTier | Name   | TradingFee    | TickSpacing | Tick Base | Best For              |
| ------- | ------ | ------------- | ----------- | --------- | --------------------- |
| 0       | STABLE | 100 (0.01%)   | 1           | 1.0001    | Stablecoin pairs      |
| 1       | LOW    | 500 (0.05%)   | 10          | 1.0001    | Correlated assets     |
| 2       | MEDIUM | 3000 (0.30%)  | 60          | 1.0001    | Standard pairs        |
| 3       | HIGH   | 10000 (1.00%) | 200         | 1.0001    | Exotic/volatile pairs |

##### 4.1.1.3 Flags

| Flag Name        | Flag Value   | Description                           |
| ---------------- | ------------ | ------------------------------------- |
| `lsfCLAMMFrozen` | `0x00000001` | Pool is frozen (no swaps or deposits) |

##### 4.1.1.4 Ownership

**Owner:** Pool pseudo-account (see 4.1.1.7)

**Directory Registration:** The CLAMM object is registered in the pool pseudo-account's owner directory. The reserve for the CLAMM object is charged to the account that submits the `CLAMMCreate` transaction.

##### 4.1.1.5 Reserves

**Reserve Requirement:** Standard

This ledger entry requires the standard owner reserve increment (currently 0.2 XRP, subject to Fee Voting changes).

##### 4.1.1.6 Deletion

**Deletion Transactions:** There is no dedicated deletion transaction for CLAMM pools. A pool persists as long as it exists on the ledger.

**Deletion Conditions:**

- Pool has zero active liquidity (`Liquidity == 0`)
- No `CLAMMTick` entries reference the pool
- No `CLAMMPosition` entries reference the pool
- All protocol fees have been collected

**Account Deletion Blocker:** Yes. The CLAMM object must be removed before the creating account can be deleted.

##### 4.1.1.7 Pseudo-Account

**Uses Pseudo-Account:** Yes

- **Purpose:** To hold pool assets (both `Asset` and `Asset2`) on behalf of liquidity providers, similar to the XLS-30 AMM pseudo-account.
- **AccountID Derivation:** The pseudo-account's AccountID is derived by hashing the CLAMM pool's ledger entry ID with the key space prefix `0x0041` ("A" for AMM Account). This produces a deterministic, unique address for each pool.
- **Capabilities:** The pseudo-account can receive tokens from deposits and swaps, and send tokens for withdrawals, swaps, and fee collection. It cannot initiate transactions or hold XRP reserves itself -- reserves are funded by the creating account and subsequent LPs.

##### 4.1.1.8 Freeze/Lock

**Freeze Support:** Yes
**Lock Support:** No

When an issuer freezes an IOU held in the pool (via global freeze or individual trust line freeze to the pool pseudo-account), the pool's `lsfCLAMMFrozen` flag is set. While frozen:

- No swaps can be executed through the pool
- No new deposits are accepted
- Withdrawals are still permitted (so LPs can retrieve their assets)
- Fee collection is still permitted

The freeze is lifted when the issuer removes the freeze on the relevant trust line(s).

##### 4.1.1.9 Invariants

- `<CLAMM>.Asset != <CLAMM>.Asset2`
- `<CLAMM>.FeeTier IN {0, 1, 2, 3}`
- `<CLAMM>.SqrtPrice > 0`
- `<CLAMM>.Liquidity >= 0`
- `<CLAMM>.CurrentTick >= MIN_TICK AND <CLAMM>.CurrentTick <= MAX_TICK`
- `<CLAMM>.FeeGrowthGlobal0' >= <CLAMM>.FeeGrowthGlobal0` (fee growth is monotonically non-decreasing)
- `<CLAMM>.FeeGrowthGlobal1' >= <CLAMM>.FeeGrowthGlobal1`
- `<CLAMM>.TickSpacing == FeeTierToTickSpacing(<CLAMM>.FeeTier)`

##### 4.1.1.10 RPC Name

**RPC Type Name:** `clamm`

This is the name used in `account_objects` and `ledger_data` RPC calls to filter for CLAMM pool objects.

##### 4.1.1.11 Example JSON

```json
{
    "LedgerEntryType": "CLAMM",
    "Asset": {
        "currency": "USD",
        "issuer": "rIssuerAddress..."
    },
    "Asset2": {
        "currency": "XRP"
    },
    "FeeTier": 2,
    "TickSpacing": 60,
    "TradingFee": 3000,
    "CurrentTick": 1250,
    "SqrtPrice": "79228162514264337593543950336",
    "Liquidity": "1000000000000000000",
    "FeeGrowthGlobal0": "0",
    "FeeGrowthGlobal1": "0",
    "ProtocolFees0": "0",
    "ProtocolFees1": "0",
    "AuctionSlot": {
        "Account": "rAuctionHolder...",
        "Expiration": 750000000,
        "DiscountedFee": 2700,
        "Price": "1000000"
    },
    "Flags": 0,
    "OwnerNode": "0",
    "PreviousTxnID": "ABC123...",
    "PreviousTxnLgrSeq": 12345678
}
```

---

#### 4.1.2 Ledger Entry: `CLAMMTick`

The `CLAMMTick` ledger entry stores per-tick liquidity and fee data. Only ticks with active liquidity are stored (sparse representation).

##### 4.1.2.1 Object Identifier

**Key Space:** `0x0054` ("T" for Tick)

**ID Calculation Algorithm:**
The ID is calculated by hashing the key space prefix `0x0054`, the parent `PoolID`, and the `TickIndex` value. This ensures one tick entry per tick index per pool.

##### 4.1.2.2 Fields

| Field Name          | Constant | Required | JSON Type | Internal Type | Default Value | Description                           |
| ------------------- | -------- | -------- | --------- | ------------- | ------------- | ------------------------------------- |
| `LedgerEntryType`   | Yes      | Yes      | `string`  | UINT16        | `0x0054`      | Identifies this as a CLAMMTick        |
| `PoolID`            | Yes      | Yes      | `string`  | HASH256       | N/A           | Reference to parent CLAMM             |
| `TickIndex`         | Yes      | Yes      | `number`  | INT32         | N/A           | Tick index (divisible by TickSpacing) |
| `LiquidityGross`    | No       | Yes      | `string`  | UINT128       | `"0"`         | Total liquidity referencing this tick |
| `LiquidityNet`      | No       | Yes      | `string`  | INT128        | `"0"`         | Net liquidity change when crossing    |
| `FeeGrowthOutside0` | No       | Yes      | `string`  | UINT128       | `"0"`         | Fee growth outside for Asset          |
| `FeeGrowthOutside1` | No       | Yes      | `string`  | UINT128       | `"0"`         | Fee growth outside for Asset2         |
| `OwnerNode`         | No       | Yes      | `string`  | UINT64        | N/A           | Directory hint                        |
| `PreviousTxnID`     | No       | Yes      | `string`  | HASH256       | N/A           | Previous modifying transaction        |
| `PreviousTxnLgrSeq` | No       | Yes      | `number`  | UINT32        | N/A           | Previous modifying ledger             |

**Field Details:**

**Liquidity Net Behavior:**

When the price crosses a tick moving upward (Asset -> Asset2):

- `Liquidity += LiquidityNet`

When the price crosses a tick moving downward (Asset2 -> Asset):

- `Liquidity -= LiquidityNet`

##### 4.1.2.3 Flags

No ledger entry-specific flags are defined for `CLAMMTick`.

##### 4.1.2.4 Ownership

**Owner:** Pool pseudo-account

**Directory Registration:** The CLAMMTick object is registered in the pool pseudo-account's owner directory. The reserve for the CLAMMTick object is charged to the LP account that first initializes the tick via `CLAMMDeposit`, and refunded when the tick is deleted.

##### 4.1.2.5 Reserves

**Reserve Requirement:** Standard

This ledger entry requires the standard owner reserve increment (currently 0.2 XRP, subject to Fee Voting changes). The reserve is charged to the first LP who uses this tick and refunded when the tick is deleted (no more liquidity references it).

##### 4.1.2.6 Deletion

**Deletion Transactions:** `CLAMMWithdraw` (indirectly, when the last position referencing this tick is withdrawn)

**Deletion Conditions:**

- `LiquidityGross` reaches zero (no positions reference this tick)

**Account Deletion Blocker:** No. CLAMMTick objects are owned by the pool pseudo-account, not user accounts.

##### 4.1.2.7 Invariants

- `<CLAMMTick>.LiquidityGross >= 0`
- `<CLAMMTick>.TickIndex % TickSpacing == 0` (tick index must be aligned to pool's tick spacing)
- `<CLAMMTick>.TickIndex >= MIN_TICK AND <CLAMMTick>.TickIndex <= MAX_TICK`
- `IF <CLAMMTick>.LiquidityGross == 0 THEN the object MUST be deleted`
- `abs(<CLAMMTick>.LiquidityNet) <= <CLAMMTick>.LiquidityGross`

##### 4.1.2.8 RPC Name

**RPC Type Name:** `clamm_tick`

This is the name used in `account_objects` and `ledger_data` RPC calls to filter for CLAMMTick objects.

##### 4.1.2.9 Example JSON

```json
{
    "LedgerEntryType": "CLAMMTick",
    "PoolID": "ABC123...",
    "TickIndex": 1200,
    "LiquidityGross": "500000000000000000",
    "LiquidityNet": "250000000000000000",
    "FeeGrowthOutside0": "1000000000",
    "FeeGrowthOutside1": "2000000000",
    "OwnerNode": "0",
    "PreviousTxnID": "DEF456...",
    "PreviousTxnLgrSeq": 12345679
}
```

---

#### 4.1.3 Ledger Entry: `CLAMMPosition`

The `CLAMMPosition` ledger entry represents an LP's liquidity position, linked to an NFToken.

##### 4.1.3.1 Object Identifier

**Key Space:** `0x0050` ("P" for Position)

**ID Calculation Algorithm:**
The ID is calculated by hashing the key space prefix `0x0050` and the `NFTokenID`. This creates a 1:1 mapping between NFToken and position.

##### 4.1.3.2 Fields

| Field Name             | Constant | Required | JSON Type | Internal Type | Default Value | Description                        |
| ---------------------- | -------- | -------- | --------- | ------------- | ------------- | ---------------------------------- |
| `LedgerEntryType`      | Yes      | Yes      | `string`  | UINT16        | `0x0050`      | Identifies this as a CLAMMPosition |
| `PoolID`               | Yes      | Yes      | `string`  | HASH256       | N/A           | Reference to parent CLAMM          |
| `NFTokenID`            | Yes      | Yes      | `string`  | HASH256       | N/A           | Associated NFToken                 |
| `Owner`                | No       | Yes      | `string`  | ACCOUNTID     | N/A           | Current position owner             |
| `LowerTick`            | Yes      | Yes      | `number`  | INT32         | N/A           | Lower bound tick                   |
| `UpperTick`            | Yes      | Yes      | `number`  | INT32         | N/A           | Upper bound tick                   |
| `Liquidity`            | No       | Yes      | `string`  | UINT128       | N/A           | Liquidity amount                   |
| `FeeGrowthInside0Last` | No       | Yes      | `string`  | UINT128       | `"0"`         | Fee growth snapshot for Asset      |
| `FeeGrowthInside1Last` | No       | Yes      | `string`  | UINT128       | `"0"`         | Fee growth snapshot for Asset2     |
| `TokensOwed0`          | No       | Yes      | `string`  | UINT64        | `"0"`         | Uncollected fees for Asset         |
| `TokensOwed1`          | No       | Yes      | `string`  | UINT64        | `"0"`         | Uncollected fees for Asset2        |
| `OwnerNode`            | No       | Yes      | `string`  | UINT64        | N/A           | Directory hint                     |
| `PreviousTxnID`        | No       | Yes      | `string`  | HASH256       | N/A           | Previous modifying transaction     |
| `PreviousTxnLgrSeq`    | No       | Yes      | `number`  | UINT32        | N/A           | Previous modifying ledger          |

**Field Details:**

**NFToken Association:**

When a position is created via `CLAMMDeposit`:

1. An NFToken is minted with:
    - `tfTransferable` flag set (positions are tradeable)
    - `Taxon`: `0x434C414D` ("CLAM")
    - `URI`: Points to position metadata (pool, ticks, etc.)
2. The `CLAMMPosition` references this NFToken
3. Ownership transfers when the NFToken is transferred

**Minimum Liquidity:**

The minimum liquidity for a position is equivalent to 1 XRP worth of value at the time of deposit. This prevents dust positions that would bloat the ledger.

##### 4.1.3.3 Flags

No ledger entry-specific flags are defined for `CLAMMPosition`.

##### 4.1.3.4 Ownership

**Owner:** LP account (the `Owner` field)

**Directory Registration:** The CLAMMPosition object is registered in the LP account's owner directory. When the associated NFToken is transferred, the `Owner` field is updated and the directory registration moves to the new owner's directory.

##### 4.1.3.5 Reserves

**Reserve Requirement:** Standard

This ledger entry requires the standard owner reserve increment (currently 0.2 XRP, subject to Fee Voting changes).

##### 4.1.3.6 Deletion

**Deletion Transactions:** `CLAMMWithdraw`

**Deletion Conditions:**

- All liquidity is withdrawn (`Liquidity == 0`)
- All fees are collected (`TokensOwed0 == 0 AND TokensOwed1 == 0`)
- The associated NFToken is burned

**Account Deletion Blocker:** Yes. All CLAMMPosition objects must be deleted before their owner account can be deleted.

##### 4.1.3.7 Invariants

- `<CLAMMPosition>.Liquidity >= 0`
- `<CLAMMPosition>.LowerTick < <CLAMMPosition>.UpperTick`
- `<CLAMMPosition>.LowerTick >= MIN_TICK` (-887272 for tick base 1.0001)
- `<CLAMMPosition>.UpperTick <= MAX_TICK` (887272 for tick base 1.0001)
- `<CLAMMPosition>.LowerTick % TickSpacing == 0 AND <CLAMMPosition>.UpperTick % TickSpacing == 0`
- `<CLAMMPosition>.TokensOwed0 >= 0 AND <CLAMMPosition>.TokensOwed1 >= 0`
- `<CLAMMPosition>.Owner == NFTokenOwner(<CLAMMPosition>.NFTokenID)`

##### 4.1.3.8 RPC Name

**RPC Type Name:** `clamm_position`

This is the name used in `account_objects` and `ledger_data` RPC calls to filter for CLAMMPosition objects.

##### 4.1.3.9 Example JSON

```json
{
    "LedgerEntryType": "CLAMMPosition",
    "PoolID": "ABC123...",
    "NFTokenID": "GHI789...",
    "Owner": "rLPAddress...",
    "LowerTick": 1000,
    "UpperTick": 1500,
    "Liquidity": "100000000000000000",
    "FeeGrowthInside0Last": "500000000",
    "FeeGrowthInside1Last": "1000000000",
    "TokensOwed0": "1000000",
    "TokensOwed1": "2000000",
    "OwnerNode": "0",
    "PreviousTxnID": "JKL012...",
    "PreviousTxnLgrSeq": 12345680
}
```

---

### 4.2 Transactions

#### 4.2.1 Transaction: `CLAMMCreate`

Creates a new concentrated liquidity pool.

##### 4.2.1.1 Fields

| Field Name         | Required? | JSON Type | Internal Type | Default Value | Description                 |
| ------------------ | --------- | --------- | ------------- | ------------- | --------------------------- |
| `TransactionType`  | Yes       | `string`  | UINT16        | `CLAMMCreate` | Identifies this transaction |
| `Account`          | Yes       | `string`  | ACCOUNTID     | N/A           | Creator's account           |
| `Asset`            | Yes       | `object`  | ISSUE         | N/A           | First asset in the pair     |
| `Asset2`           | Yes       | `object`  | ISSUE         | N/A           | Second asset in the pair    |
| `FeeTier`          | Yes       | `number`  | UINT8         | N/A           | Fee tier (0-3)              |
| `InitialSqrtPrice` | Yes       | `string`  | UINT128       | N/A           | Initial sqrt price (Q64.96) |

##### 4.2.1.2 Flags

No transaction-specific flags are defined for `CLAMMCreate`.

##### 4.2.1.3 Transaction Fee

**Fee Structure:** Standard

This transaction uses the standard transaction fee (currently 10 drops, subject to Fee Voting changes). The account must also meet the reserve requirement for the new `CLAMM` ledger entry.

##### 4.2.1.4 Failure Conditions

###### 4.2.1.4.1 Data Verification

All Data Verification failures return a `tem` level error.

1. The CLAMM amendment is not enabled. (`temDISABLED`)
2. `Asset` or `Asset2` is not a valid issue. (`temMALFORMED`)
3. `Asset` is the same as `Asset2`. (`temMALFORMED`)
4. `Asset` is not lexicographically less than `Asset2` (canonical ordering violated). (`temMALFORMED`)
5. `FeeTier` is not 0, 1, 2, or 3. (`temMALFORMED`)
6. `InitialSqrtPrice` is zero or negative. (`temBAD_AMOUNT`)

###### 4.2.1.4.2 Protocol-Level Failures

Protocol-level failures return `tec` codes.

1. A pool with the same `Asset`, `Asset2`, and `FeeTier` already exists. (`tecDUPLICATE`)
2. If either asset is an IOU, the creator does not have a trust line to that issuer. (`tecNO_LINE`)
3. The creator's XRP balance is insufficient to meet the reserve for the new CLAMM object. (`tecINSUFFICIENT_RESERVE`)
4. An asset issuer has frozen the relevant trust line. (`tecFROZEN`)

##### 4.2.1.5 State Changes

**On Success (`tesSUCCESS`):**

- Create a new `CLAMM` ledger entry with the specified assets, fee tier, and initial sqrt price
- Create the pool pseudo-account
- Derive `CurrentTick` from `InitialSqrtPrice`
- Set `Liquidity` to zero (pool starts empty)
- Register the `CLAMM` object in the pool pseudo-account's owner directory
- Increment the creator's `OwnerCount`

##### 4.2.1.6 Example JSON

```json
{
    "TransactionType": "CLAMMCreate",
    "Account": "rCreator...",
    "Asset": {
        "currency": "USD",
        "issuer": "rIssuer..."
    },
    "Asset2": {
        "currency": "XRP"
    },
    "FeeTier": 2,
    "InitialSqrtPrice": "79228162514264337593543950336"
}
```

---

#### 4.2.2 Transaction: `CLAMMDeposit`

Adds liquidity within a price range and mints a position NFToken.

##### 4.2.2.1 Fields

| Field Name        | Required?   | JSON Type | Internal Type | Default Value  | Description                             |
| ----------------- | ----------- | --------- | ------------- | -------------- | --------------------------------------- |
| `TransactionType` | Yes         | `string`  | UINT16        | `CLAMMDeposit` | Identifies this transaction             |
| `Account`         | Yes         | `string`  | ACCOUNTID     | N/A            | LP's account                            |
| `PoolID`          | Yes         | `string`  | HASH256       | N/A            | Target pool                             |
| `LowerTick`       | Yes         | `number`  | INT32         | N/A            | Lower bound tick                        |
| `UpperTick`       | Yes         | `number`  | INT32         | N/A            | Upper bound tick                        |
| `Amount`          | Yes         | `object`  | AMOUNT        | N/A            | Maximum Asset to deposit                |
| `Amount2`         | Yes         | `object`  | AMOUNT        | N/A            | Maximum Asset2 to deposit               |
| `MinLiquidity`    | No          | `string`  | UINT128       | N/A            | Minimum liquidity (slippage protection) |
| `NFTokenID`       | No          | `string`  | HASH256       | N/A            | Existing position to add to             |

**Field Details:**

**Amount Calculation:**

The actual amounts deposited depend on the current price relative to the tick range:

- **Current price below range**: Only `Asset` is deposited
- **Current price above range**: Only `Asset2` is deposited
- **Current price in range**: Both assets deposited proportionally

##### 4.2.2.2 Flags

No transaction-specific flags are defined for `CLAMMDeposit`.

##### 4.2.2.3 Transaction Fee

**Fee Structure:** Standard

This transaction uses the standard transaction fee (currently 10 drops, subject to Fee Voting changes). The account must also meet the reserve requirements for any new `CLAMMPosition` and `CLAMMTick` objects created.

##### 4.2.2.4 Failure Conditions

###### 4.2.2.4.1 Data Verification

All Data Verification failures return a `tem` level error.

1. The CLAMM amendment is not enabled. (`temDISABLED`)
2. `PoolID` is not a valid 256-bit hash. (`temMALFORMED`)
3. `LowerTick` is greater than or equal to `UpperTick`. (`temMALFORMED`)
4. `LowerTick` is less than `MIN_TICK` (-887272). (`temMALFORMED`)
5. `UpperTick` is greater than `MAX_TICK` (887272). (`temMALFORMED`)
6. `Amount` or `Amount2` is zero or negative. (`temBAD_AMOUNT`)

###### 4.2.2.4.2 Protocol-Level Failures

Protocol-level failures return `tec` codes.

1. `PoolID` does not reference an existing `CLAMM` object. (`tecNO_ENTRY`)
2. The pool is frozen (`lsfCLAMMFrozen`). (`tecFROZEN`)
3. `LowerTick` or `UpperTick` is not divisible by the pool's `TickSpacing`. (`tecNO_PERMISSION`)
4. The account has insufficient balance of either asset. (`tecUNFUNDED`)
5. The resulting liquidity is below the minimum (1 XRP worth of value). (`tecINSUFFICIENT_RESERVE`)
6. The resulting liquidity is below `MinLiquidity` (slippage protection). (`tecPATH_PARTIAL`)
7. If `NFTokenID` is provided, the account does not own that NFToken. (`tecNO_PERMISSION`)
8. If `NFTokenID` is provided, the existing position's `PoolID`, `LowerTick`, or `UpperTick` does not match. (`tecNO_ENTRY`)
9. The account's XRP balance is insufficient for reserves (position + tick objects). (`tecINSUFFICIENT_RESERVE`)

##### 4.2.2.5 State Changes

**On Success (`tesSUCCESS`):**

- Transfer assets from LP to the pool pseudo-account
- If new position: mint an NFToken with `tfTransferable` and `Taxon` `0x434C414D`, create `CLAMMPosition` ledger entry
- If existing position (`NFTokenID` provided): add liquidity to existing `CLAMMPosition`
- Create or update `CLAMMTick` entries for boundary ticks (increment `LiquidityGross`, adjust `LiquidityNet`)
- Update pool's `Liquidity` if the position is in range (current tick between lower and upper)
- Increment owner's `OwnerCount` for any newly created objects

##### 4.2.2.6 Example JSON

```json
{
    "TransactionType": "CLAMMDeposit",
    "Account": "rLP...",
    "PoolID": "ABC123...",
    "LowerTick": -1200,
    "UpperTick": 1800,
    "Amount": {
        "currency": "USD",
        "issuer": "rIssuer...",
        "value": "1000"
    },
    "Amount2": {
        "currency": "XRP",
        "value": "2000000000"
    },
    "MinLiquidity": "100000000000000000"
}
```

---

#### 4.2.3 Transaction: `CLAMMWithdraw`

Removes liquidity from a position.

##### 4.2.3.1 Fields

| Field Name        | Required? | JSON Type | Internal Type | Default Value   | Description               |
| ----------------- | --------- | --------- | ------------- | --------------- | ------------------------- |
| `TransactionType` | Yes       | `string`  | UINT16        | `CLAMMWithdraw` | Identifies this transaction |
| `Account`         | Yes       | `string`  | ACCOUNTID     | N/A             | LP's account              |
| `NFTokenID`       | Yes       | `string`  | HASH256       | N/A             | Position NFToken          |
| `LiquidityAmount` | Yes       | `string`  | UINT128       | N/A             | Liquidity to remove       |
| `MinAmount`       | No        | `object`  | AMOUNT        | N/A             | Minimum Asset to receive  |
| `MinAmount2`      | No        | `object`  | AMOUNT        | N/A             | Minimum Asset2 to receive |

##### 4.2.3.2 Flags

No transaction-specific flags are defined for `CLAMMWithdraw`.

##### 4.2.3.3 Transaction Fee

**Fee Structure:** Standard

This transaction uses the standard transaction fee (currently 10 drops, subject to Fee Voting changes).

##### 4.2.3.4 Failure Conditions

###### 4.2.3.4.1 Data Verification

All Data Verification failures return a `tem` level error.

1. The CLAMM amendment is not enabled. (`temDISABLED`)
2. `NFTokenID` is not a valid 256-bit hash. (`temMALFORMED`)
3. `LiquidityAmount` is zero. (`temBAD_AMOUNT`)

###### 4.2.3.4.2 Protocol-Level Failures

Protocol-level failures return `tec` codes.

1. The account does not own the specified NFToken. (`tecNO_PERMISSION`)
2. The referenced `CLAMMPosition` does not exist. (`tecNO_ENTRY`)
3. `LiquidityAmount` exceeds the position's current liquidity. (`tecUNFUNDED`)
4. Output amounts are below `MinAmount` or `MinAmount2` (slippage protection). (`tecPATH_PARTIAL`)

##### 4.2.3.5 State Changes

**On Success (`tesSUCCESS`):**

- Transfer assets from pool pseudo-account to LP based on the withdrawn liquidity and current price
- Transfer accumulated fees to LP
- Reduce position's `Liquidity` by `LiquidityAmount`
- Update `CLAMMTick` entries (decrement `LiquidityGross`, adjust `LiquidityNet`)
- If position's `Liquidity` reaches zero: burn the NFToken, delete the `CLAMMPosition` ledger entry
- If a `CLAMMTick`'s `LiquidityGross` reaches zero: delete the tick
- Update pool's `Liquidity` if the position was in range
- Decrement owner's `OwnerCount` for any deleted objects

##### 4.2.3.6 Example JSON

```json
{
    "TransactionType": "CLAMMWithdraw",
    "Account": "rLP...",
    "NFTokenID": "GHI789...",
    "LiquidityAmount": "50000000000000000",
    "MinAmount": {
        "currency": "USD",
        "issuer": "rIssuer...",
        "value": "400"
    },
    "MinAmount2": {
        "currency": "XRP",
        "value": "800000000"
    }
}
```

---

#### 4.2.4 Transaction: `CLAMMSwap`

Executes a swap through the pool.

##### 4.2.4.1 Fields

| Field Name        | Required? | JSON Type | Internal Type | Default Value | Description                          |
| ----------------- | --------- | --------- | ------------- | ------------- | ------------------------------------ |
| `TransactionType` | Yes       | `string`  | UINT16        | `CLAMMSwap`   | Identifies this transaction          |
| `Account`         | Yes       | `string`  | ACCOUNTID     | N/A           | Trader's account                     |
| `PoolID`          | Yes       | `string`  | HASH256       | N/A           | Target pool                          |
| `AmountIn`        | Yes       | `object`  | AMOUNT        | N/A           | Amount to swap in                    |
| `MinAmountOut`    | No        | `object`  | AMOUNT        | N/A           | Minimum output (slippage protection) |
| `SqrtPriceLimit`  | No        | `string`  | UINT128       | N/A           | Price limit for partial fills        |

**Field Details:**

**Fee Distribution:**

Trading fees are distributed as follows:

1. `TradingFee` is deducted from the input amount
2. If an auction slot holder exists and is not expired:
    - Auction holder pays `DiscountedFee` instead of full `TradingFee`
    - Difference goes to protocol fees (distributed to LPs)
3. Fees accrue to `FeeGrowthGlobal0` or `FeeGrowthGlobal1`
4. LPs collect their share when collecting fees or withdrawing

##### 4.2.4.2 Flags

No transaction-specific flags are defined for `CLAMMSwap`.

##### 4.2.4.3 Transaction Fee

**Fee Structure:** Standard

This transaction uses the standard transaction fee (currently 10 drops, subject to Fee Voting changes).

##### 4.2.4.4 Failure Conditions

###### 4.2.4.4.1 Data Verification

All Data Verification failures return a `tem` level error.

1. The CLAMM amendment is not enabled. (`temDISABLED`)
2. `PoolID` is not a valid 256-bit hash. (`temMALFORMED`)
3. `AmountIn` is zero or negative. (`temBAD_AMOUNT`)
4. `AmountIn` does not match one of the pool's assets. (`temMALFORMED`)

###### 4.2.4.4.2 Protocol-Level Failures

Protocol-level failures return `tec` codes.

1. The pool does not exist. (`tecNO_ENTRY`)
2. The pool is frozen (`lsfCLAMMFrozen`). (`tecFROZEN`)
3. The pool has zero active liquidity. (`tecPATH_DRY`)
4. The account has insufficient balance for the input amount. (`tecUNFUNDED`)
5. The output amount is below `MinAmountOut` (slippage protection). (`tecPATH_PARTIAL`)
6. `SqrtPriceLimit` is reached with remaining input (partial fill). (`tecPATH_PARTIAL`)

##### 4.2.4.5 State Changes

**On Success (`tesSUCCESS`):**

- Transfer input asset from trader to pool pseudo-account
- Transfer output asset from pool pseudo-account to trader
- Deduct trading fee from input amount
- Update pool state: `CurrentTick`, `SqrtPrice`, `Liquidity`
- Update fee growth accumulators (`FeeGrowthGlobal0` or `FeeGrowthGlobal1`)
- If ticks are crossed: update `FeeGrowthOutside` for each crossed tick, adjust active `Liquidity`
- If auction slot holder is active: apply `DiscountedFee` rate, accrue difference to `ProtocolFees`

##### 4.2.4.6 Example JSON

```json
{
    "TransactionType": "CLAMMSwap",
    "Account": "rTrader...",
    "PoolID": "ABC123...",
    "AmountIn": {
        "currency": "USD",
        "issuer": "rIssuer...",
        "value": "100"
    },
    "MinAmountOut": {
        "currency": "XRP",
        "value": "180000000"
    }
}
```

---

#### 4.2.5 Transaction: `CLAMMCollectFees`

Collects accumulated fees without removing liquidity.

##### 4.2.5.1 Fields

| Field Name        | Required? | JSON Type | Internal Type | Default Value      | Description                    |
| ----------------- | --------- | --------- | ------------- | ------------------ | ------------------------------ |
| `TransactionType` | Yes       | `string`  | UINT16        | `CLAMMCollectFees` | Identifies this transaction    |
| `Account`         | Yes       | `string`  | ACCOUNTID     | N/A                | LP's account                   |
| `NFTokenID`       | Yes       | `string`  | HASH256       | N/A                | Position NFToken               |
| `MaxAmount`       | No        | `object`  | AMOUNT        | N/A                | Maximum Asset fees to collect  |
| `MaxAmount2`      | No        | `object`  | AMOUNT        | N/A                | Maximum Asset2 fees to collect |

##### 4.2.5.2 Flags

No transaction-specific flags are defined for `CLAMMCollectFees`.

##### 4.2.5.3 Transaction Fee

**Fee Structure:** Standard

This transaction uses the standard transaction fee (currently 10 drops, subject to Fee Voting changes).

##### 4.2.5.4 Failure Conditions

###### 4.2.5.4.1 Data Verification

All Data Verification failures return a `tem` level error.

1. The CLAMM amendment is not enabled. (`temDISABLED`)
2. `NFTokenID` is not a valid 256-bit hash. (`temMALFORMED`)

###### 4.2.5.4.2 Protocol-Level Failures

Protocol-level failures return `tec` codes.

1. The account does not own the specified NFToken. (`tecNO_PERMISSION`)
2. The referenced `CLAMMPosition` does not exist. (`tecNO_ENTRY`)
3. No fees are available to collect (`TokensOwed0 == 0 AND TokensOwed1 == 0`). (`tecCLAIM`)

##### 4.2.5.5 State Changes

**On Success (`tesSUCCESS`):**

- Calculate accumulated fees based on fee growth since last snapshot
- Transfer fee amounts from pool pseudo-account to LP (capped by `MaxAmount`/`MaxAmount2` if specified)
- Update position's `FeeGrowthInside0Last` and `FeeGrowthInside1Last` to current values
- Reset `TokensOwed0` and `TokensOwed1` (or reduce by collected amounts if capped)

##### 4.2.5.6 Example JSON

```json
{
    "TransactionType": "CLAMMCollectFees",
    "Account": "rLP...",
    "NFTokenID": "GHI789..."
}
```

---

#### 4.2.6 Transaction: `CLAMMVote`

Votes on auction slot parameters. Voting weight is proportional to liquidity.

##### 4.2.6.1 Fields

| Field Name        | Required? | JSON Type | Internal Type | Default Value | Description                                 |
| ----------------- | --------- | --------- | ------------- | ------------- | ------------------------------------------- |
| `TransactionType` | Yes       | `string`  | UINT16        | `CLAMMVote`   | Identifies this transaction                 |
| `Account`         | Yes       | `string`  | ACCOUNTID     | N/A           | LP's account                                |
| `PoolID`          | Yes       | `string`  | HASH256       | N/A           | Target pool                                 |
| `TradingFee`      | No        | `number`  | UINT32        | N/A           | Proposed trading fee (within tier bounds)   |
| `DiscountedFee`   | No        | `number`  | UINT32        | N/A           | Proposed discounted fee for auction winners |

##### 4.2.6.2 Flags

No transaction-specific flags are defined for `CLAMMVote`.

##### 4.2.6.3 Transaction Fee

**Fee Structure:** Standard

This transaction uses the standard transaction fee (currently 10 drops, subject to Fee Voting changes).

##### 4.2.6.4 Failure Conditions

###### 4.2.6.4.1 Data Verification

All Data Verification failures return a `tem` level error.

1. The CLAMM amendment is not enabled. (`temDISABLED`)
2. `TradingFee` is outside the valid range for the pool's fee tier. (`temMALFORMED`)
3. `DiscountedFee` is greater than or equal to `TradingFee`. (`temMALFORMED`)
4. Neither `TradingFee` nor `DiscountedFee` is provided. (`temMALFORMED`)

###### 4.2.6.4.2 Protocol-Level Failures

Protocol-level failures return `tec` codes.

1. The pool does not exist. (`tecNO_ENTRY`)
2. The account has no position in the pool. (`tecNO_PERMISSION`)

##### 4.2.6.5 State Changes

**On Success (`tesSUCCESS`):**

- Record the account's vote weighted by total liquidity held across all positions in the pool
- Recalculate the pool's `TradingFee` and/or `DiscountedFee` based on the liquidity-weighted average of all votes

##### 4.2.6.6 Example JSON

```json
{
    "TransactionType": "CLAMMVote",
    "Account": "rLP...",
    "PoolID": "ABC123...",
    "DiscountedFee": 2500
}
```

---

#### 4.2.7 Transaction: `CLAMMBid`

Bids for the auction slot to receive discounted trading fees.

##### 4.2.7.1 Fields

| Field Name        | Required? | JSON Type | Internal Type | Default Value | Description                                  |
| ----------------- | --------- | --------- | ------------- | ------------- | -------------------------------------------- |
| `TransactionType` | Yes       | `string`  | UINT16        | `CLAMMBid`    | Identifies this transaction                  |
| `Account`         | Yes       | `string`  | ACCOUNTID     | N/A           | Bidder's account                             |
| `PoolID`          | Yes       | `string`  | HASH256       | N/A           | Target pool                                  |
| `BidMin`          | No        | `object`  | AMOUNT        | N/A           | Minimum bid amount                           |
| `BidMax`          | No        | `object`  | AMOUNT        | N/A           | Maximum bid amount                           |
| `AuthAccounts`    | No        | `array`   | STARRAY       | N/A           | Up to 4 accounts authorized to use this slot |

**Field Details:**

**Auction Slot Mechanics:**

- Slot duration: 24 hours (86400 seconds), divided into 20 intervals
- Minimum bid increases over time within each interval
- Winning bid payment is distributed to LPs proportionally
- Slot holder (and authorized accounts) pay `DiscountedFee` instead of `TradingFee`

##### 4.2.7.2 Flags

No transaction-specific flags are defined for `CLAMMBid`.

##### 4.2.7.3 Transaction Fee

**Fee Structure:** Standard

This transaction uses the standard transaction fee (currently 10 drops, subject to Fee Voting changes).

##### 4.2.7.4 Failure Conditions

###### 4.2.7.4.1 Data Verification

All Data Verification failures return a `tem` level error.

1. The CLAMM amendment is not enabled. (`temDISABLED`)
2. More than 4 entries in `AuthAccounts`. (`temMALFORMED`)
3. `BidMin` is greater than `BidMax` (when both are specified). (`temMALFORMED`)
4. `AuthAccounts` contains duplicate accounts. (`temMALFORMED`)

###### 4.2.7.4.2 Protocol-Level Failures

Protocol-level failures return `tec` codes.

1. The pool does not exist. (`tecNO_ENTRY`)
2. The bid amount is below the minimum for the current auction interval. (`tecINSUFFICIENT_PAYMENT`)
3. The account has insufficient balance for the bid. (`tecUNFUNDED`)

##### 4.2.7.5 State Changes

**On Success (`tesSUCCESS`):**

- If an existing auction slot holder exists: refund the remaining slot value (pro-rated) to the previous holder
- Set the pool's `AuctionSlot` with the bidder's account, new expiration (current time + 24 hours), and `DiscountedFee`
- Distribute the bid payment to all in-range LPs proportionally to their active liquidity
- Set `AuthAccounts` if provided

##### 4.2.7.6 Example JSON

```json
{
    "TransactionType": "CLAMMBid",
    "Account": "rBidder...",
    "PoolID": "ABC123...",
    "BidMax": {
        "currency": "XRP",
        "value": "1000000000"
    },
    "AuthAccounts": [{ "Account": "rAuth1..." }, { "Account": "rAuth2..." }]
}
```

---

### 4.3 RPCs

#### 4.3.1 RPC: `clamm_info`

Returns information about a CLAMM pool.

##### 4.3.1.1 Request Fields

| Field Name     | Required?   | JSON Type        | Description                                                                     |
| -------------- | ----------- | ---------------- | ------------------------------------------------------------------------------- |
| `command`      | Yes         | `string`         | Must be `"clamm_info"`                                                          |
| `pool_id`      | Conditional | `string`         | Pool ID hash. Required if `asset`/`asset2`/`fee_tier` are not provided.         |
| `asset`        | Conditional | `object`         | First asset issue. Required with `asset2` and `fee_tier` if `pool_id` not provided. |
| `asset2`       | Conditional | `object`         | Second asset issue.                                                             |
| `fee_tier`     | Conditional | `number`         | Fee tier (0-3).                                                                 |
| `ledger_index` | No          | `string\|number` | Ledger version to query. Default `"validated"`.                                 |

##### 4.3.1.2 Response Fields

| Field Name | Always Present? | JSON Type | Description                            |
| ---------- | --------------- | --------- | -------------------------------------- |
| `status`   | Yes             | `string`  | `"success"` if the request succeeded   |
| `pool`     | Yes             | `object`  | Pool data including all CLAMM fields (pool_id, asset, asset2, fee_tier, tick_spacing, trading_fee, current_tick, sqrt_price, liquidity, fee_growth_global_0, fee_growth_global_1, auction_slot) |

##### 4.3.1.3 Failure Conditions

1. Neither `pool_id` nor the combination of `asset`/`asset2`/`fee_tier` is provided. (`invalidParams`)
2. `pool_id` is not a valid 256-bit hash. (`invalidParams`)
3. The specified pool does not exist. (`entryNotFound`)
4. The specified ledger version is not available. (`lgrNotFound`)

##### 4.3.1.4 Example Request

```json
{
    "command": "clamm_info",
    "pool_id": "ABC123...",
    "ledger_index": "validated"
}
```

##### 4.3.1.5 Example Response

```json
{
    "result": {
        "pool": {
            "pool_id": "ABC123...",
            "asset": { "currency": "USD", "issuer": "rIssuer..." },
            "asset2": { "currency": "XRP" },
            "fee_tier": 2,
            "tick_spacing": 60,
            "trading_fee": 3000,
            "current_tick": 1250,
            "sqrt_price": "79228162514264337593543950336",
            "liquidity": "1000000000000000000",
            "fee_growth_global_0": "1000000000",
            "fee_growth_global_1": "2000000000",
            "auction_slot": {
                "account": "rAuctionHolder...",
                "expiration": 750000000,
                "discounted_fee": 2700,
                "price": "1000000"
            }
        },
        "status": "success"
    }
}
```

---

#### 4.3.2 RPC: `clamm_positions`

Returns positions owned by an account.

##### 4.3.2.1 Request Fields

| Field Name     | Required? | JSON Type        | Description                                        |
| -------------- | --------- | ---------------- | -------------------------------------------------- |
| `command`      | Yes       | `string`         | Must be `"clamm_positions"`                        |
| `account`      | Yes       | `string`         | Account address to query positions for             |
| `pool_id`      | No        | `string`         | Filter positions by pool ID                        |
| `ledger_index` | No        | `string\|number` | Ledger version to query. Default `"validated"`.    |
| `limit`        | No        | `number`         | Maximum number of results to return. Default 200.  |
| `marker`       | No        | `string`         | Pagination marker from a previous response.        |

##### 4.3.2.2 Response Fields

| Field Name  | Always Present? | JSON Type | Description                                              |
| ----------- | --------------- | --------- | -------------------------------------------------------- |
| `status`    | Yes             | `string`  | `"success"` if the request succeeded                     |
| `positions` | Yes             | `array`   | Array of position objects (nftoken_id, pool_id, lower_tick, upper_tick, liquidity, tokens_owed_0, tokens_owed_1, in_range) |
| `marker`    | No              | `string`  | Pagination marker for retrieving the next page           |

##### 4.3.2.3 Failure Conditions

1. `account` is not a valid account address. (`invalidParams`)
2. The specified account does not exist. (`actNotFound`)
3. `pool_id` is provided but is not a valid 256-bit hash. (`invalidParams`)
4. The specified ledger version is not available. (`lgrNotFound`)

##### 4.3.2.4 Example Request

```json
{
    "command": "clamm_positions",
    "account": "rLP...",
    "pool_id": "ABC123...",
    "ledger_index": "validated"
}
```

##### 4.3.2.5 Example Response

```json
{
    "result": {
        "positions": [
            {
                "nftoken_id": "GHI789...",
                "pool_id": "ABC123...",
                "lower_tick": 1000,
                "upper_tick": 1500,
                "liquidity": "100000000000000000",
                "tokens_owed_0": "1000000",
                "tokens_owed_1": "2000000",
                "in_range": true
            }
        ],
        "status": "success"
    }
}
```

---

#### 4.3.3 RPC: `clamm_ticks`

Returns tick data for a pool within a range.

##### 4.3.3.1 Request Fields

| Field Name     | Required? | JSON Type        | Description                                       |
| -------------- | --------- | ---------------- | ------------------------------------------------- |
| `command`      | Yes       | `string`         | Must be `"clamm_ticks"`                           |
| `pool_id`      | Yes       | `string`         | Pool ID hash                                      |
| `tick_lower`   | No        | `number`         | Lower bound of tick range to query                |
| `tick_upper`   | No        | `number`         | Upper bound of tick range to query                |
| `ledger_index` | No        | `string\|number` | Ledger version to query. Default `"validated"`.   |
| `limit`        | No        | `number`         | Maximum number of results to return. Default 200. |
| `marker`       | No        | `string`         | Pagination marker from a previous response.       |

##### 4.3.3.2 Response Fields

| Field Name | Always Present? | JSON Type | Description                                                        |
| ---------- | --------------- | --------- | ------------------------------------------------------------------ |
| `status`   | Yes             | `string`  | `"success"` if the request succeeded                               |
| `ticks`    | Yes             | `array`   | Array of tick objects (tick_index, liquidity_gross, liquidity_net)  |
| `marker`   | No              | `string`  | Pagination marker for retrieving the next page                     |

##### 4.3.3.3 Failure Conditions

1. `pool_id` is not a valid 256-bit hash. (`invalidParams`)
2. The specified pool does not exist. (`entryNotFound`)
3. `tick_lower` is greater than `tick_upper` (when both are provided). (`invalidParams`)
4. The specified ledger version is not available. (`lgrNotFound`)

##### 4.3.3.4 Example Request

```json
{
    "command": "clamm_ticks",
    "pool_id": "ABC123...",
    "tick_lower": 1000,
    "tick_upper": 2000,
    "ledger_index": "validated"
}
```

##### 4.3.3.5 Example Response

```json
{
    "result": {
        "ticks": [
            {
                "tick_index": 1020,
                "liquidity_gross": "500000000000000000",
                "liquidity_net": "250000000000000000"
            },
            {
                "tick_index": 1080,
                "liquidity_gross": "300000000000000000",
                "liquidity_net": "-150000000000000000"
            }
        ],
        "status": "success"
    }
}
```

---

#### 4.3.4 RPC: `clamm_quote`

Returns a quote for a swap without executing it.

##### 4.3.4.1 Request Fields

| Field Name         | Required? | JSON Type        | Description                                     |
| ------------------ | --------- | ---------------- | ----------------------------------------------- |
| `command`          | Yes       | `string`         | Must be `"clamm_quote"`                         |
| `pool_id`          | Yes       | `string`         | Pool ID hash                                    |
| `amount_in`        | Yes       | `object`         | Amount to swap in (must match one pool asset)   |
| `sqrt_price_limit` | No        | `string`         | Price limit for partial fills (Q64.96)          |
| `ledger_index`     | No        | `string\|number` | Ledger version to query. Default `"validated"`. |

##### 4.3.4.2 Response Fields

| Field Name         | Always Present? | JSON Type | Description                            |
| ------------------ | --------------- | --------- | -------------------------------------- |
| `status`           | Yes             | `string`  | `"success"` if the request succeeded   |
| `amount_in`        | Yes             | `object`  | Input amount (echoed back)             |
| `amount_out`       | Yes             | `object`  | Estimated output amount                |
| `fee`              | Yes             | `object`  | Fee amount deducted from input         |
| `price_impact`     | Yes             | `string`  | Price impact as a decimal string       |
| `sqrt_price_after` | Yes             | `string`  | Estimated sqrt price after the swap    |
| `ticks_crossed`    | Yes             | `number`  | Number of initialized ticks crossed    |

##### 4.3.4.3 Failure Conditions

1. `pool_id` is not a valid 256-bit hash. (`invalidParams`)
2. The specified pool does not exist. (`entryNotFound`)
3. `amount_in` is not a valid amount or does not match a pool asset. (`invalidParams`)
4. The pool has zero active liquidity. (`noLiquidity`)
5. The specified ledger version is not available. (`lgrNotFound`)

##### 4.3.4.4 Example Request

```json
{
    "command": "clamm_quote",
    "pool_id": "ABC123...",
    "amount_in": {
        "currency": "USD",
        "issuer": "rIssuer...",
        "value": "100"
    },
    "ledger_index": "validated"
}
```

##### 4.3.4.5 Example Response

```json
{
    "result": {
        "amount_in": {
            "currency": "USD",
            "issuer": "rIssuer...",
            "value": "100"
        },
        "amount_out": { "currency": "XRP", "value": "185000000" },
        "fee": { "currency": "USD", "issuer": "rIssuer...", "value": "0.3" },
        "price_impact": "0.0015",
        "sqrt_price_after": "79300000000000000000000000000",
        "ticks_crossed": 2,
        "status": "success"
    }
}
```

---

### 4.4 Continuous Auction Mechanism

The continuous auction mechanism is adapted from XLS-30 to return arbitrage value to LPs rather than external arbitrageurs.

#### 4.4.1 Auction Slot Structure

```json
{
    "Account": "rSlotHolder...",
    "Expiration": 750000000,
    "DiscountedFee": 2700,
    "Price": "1000000",
    "AuthAccounts": [{ "Account": "rAuth1..." }, { "Account": "rAuth2..." }]
}
```

#### 4.4.2 Slot Duration and Pricing

- Total slot duration: 24 hours (86400 seconds)
- Divided into 20 intervals of 4320 seconds (~72 minutes) each
- Minimum bid = Previous price \* decay factor for current interval
- Decay factors: [1.0, 0.95, 0.9, 0.85, 0.8, 0.75, 0.7, 0.65, 0.6, 0.55, 0.5, 0.45, 0.4, 0.35, 0.3, 0.25, 0.2, 0.15, 0.1, 0.05]

#### 4.4.3 Fee Distribution

When a bid is successful:

1. Bid payment is distributed to all in-range LPs proportionally to their liquidity
2. Slot holder receives discounted fee rate for the slot duration
3. Difference between regular fee and discounted fee accrues to protocol fees

#### 4.4.4 Authorized Accounts

The slot holder can authorize up to 4 additional accounts to use the discounted fee rate. This allows trading operations across multiple accounts while sharing a single auction slot.

---

### 4.5 Math and Precision

#### 4.5.1 Number Representation

| Value      | Representation       | Precision                        |
| ---------- | -------------------- | -------------------------------- |
| SqrtPrice  | Q64.96 fixed-point   | 96 bits of fractional precision  |
| Liquidity  | UINT128              | Integer                          |
| Fee Growth | Q128.128 fixed-point | 128 bits of fractional precision |
| Tick Index | INT32                | Integer, range [-887272, 887272] |

#### 4.5.2 Price Calculation

```
price(tick) = 1.0001^tick
sqrtPrice(tick) = 1.0001^(tick/2)
```

To convert between tick and sqrt price:

```
tick = floor(log(sqrtPrice^2) / log(1.0001))
sqrtPrice = sqrt(1.0001^tick) * 2^96
```

#### 4.5.3 Liquidity Calculation

Given amounts of both tokens and a price range:

```
L = amount0 * (sqrt(upper) * sqrt(lower)) / (sqrt(upper) - sqrt(lower))
L = amount1 / (sqrt(current) - sqrt(lower))
```

The actual liquidity is the minimum of these two values.

#### 4.5.4 Amount Calculation

Given liquidity and price range:

```
amount0 = L * (sqrt(upper) - sqrt(current)) / (sqrt(upper) * sqrt(current))
amount1 = L * (sqrt(current) - sqrt(lower))
```

---

### 4.6 Swap Algorithm

```
function swap(amountIn, zeroForOne):
    amountRemaining = amountIn
    sqrtPriceCurrent = pool.sqrtPrice
    liquidityCurrent = pool.liquidity

    while amountRemaining > 0:
        // Find next initialized tick
        nextTick = getNextInitializedTick(pool.currentTick, zeroForOne)
        sqrtPriceTarget = getSqrtPriceAtTick(nextTick)

        // Calculate swap within current tick range
        (sqrtPriceNext, amountInStep, amountOutStep, feeAmount) =
            computeSwapStep(
                sqrtPriceCurrent,
                sqrtPriceTarget,
                liquidityCurrent,
                amountRemaining,
                pool.tradingFee
            )

        amountRemaining -= (amountInStep + feeAmount)
        amountOut += amountOutStep

        // Update fee growth
        if liquidityCurrent > 0:
            feeGrowthGlobal += feeAmount / liquidityCurrent

        // Cross tick if needed
        if sqrtPriceNext == sqrtPriceTarget:
            tick = getTick(nextTick)
            liquidityCurrent += tick.liquidityNet (or -= if zeroForOne)
            crossTick(tick)  // Update fee growth outside

        sqrtPriceCurrent = sqrtPriceNext

    // Update pool state
    pool.sqrtPrice = sqrtPriceCurrent
    pool.currentTick = getTickAtSqrtPrice(sqrtPriceCurrent)
    pool.liquidity = liquidityCurrent

    return amountOut
```

---

### 4.7 Payment Engine Integration

CLAMM pools are integrated into the XRPL payment engine, allowing automatic routing through concentrated liquidity pools alongside the DEX order book and XLS-30 AMM pools.

#### 4.7.1 Path Finding

The payment engine considers CLAMM pools when:

1. Finding paths for `Payment` transactions
2. Calculating best rates across all liquidity sources
3. Splitting orders across multiple venues for better execution

#### 4.7.2 Liquidity Aggregation

When executing a payment, the engine may:

- Route entirely through CLAMM
- Route entirely through DEX order book
- Route entirely through XLS-30 AMM
- Split across multiple sources for optimal execution

#### 4.7.3 Path Specification

Users can explicitly include CLAMM pools in payment paths:

```json
{
    "TransactionType": "Payment",
    "Account": "rSender...",
    "Destination": "rReceiver...",
    "Amount": { "currency": "EUR", "issuer": "rEURIssuer...", "value": "100" },
    "SendMax": { "currency": "USD", "issuer": "rUSDIssuer...", "value": "120" },
    "Paths": [[{ "clamm": "CLAMMPoolID..." }]]
}
```

---

## 5. Rationale

### 5.1 Why Concentrated Liquidity?

The uniform liquidity distribution of XLS-30 was appropriate for XRPL's first AMM implementation due to its simplicity. However, the DeFi ecosystem has evolved, and concentrated liquidity has become the standard for capital-efficient AMMs. This specification brings XRPL in line with industry best practices.

### 5.2 Why NFToken-Based Positions?

Alternative approaches considered:

| Approach                   | Pros                                      | Cons                                |
| -------------------------- | ----------------------------------------- | ----------------------------------- |
| Fungible LPTokens (XLS-30) | Simple, familiar                          | Cannot represent unique positions   |
| New position object type   | Purpose-built                             | Requires new trading infrastructure |
| **NFToken-based**          | Reuses existing infrastructure, tradeable | Slightly higher complexity          |

NFTokens were chosen because:

1. XRPL already has NFToken infrastructure (XLS-20)
2. Positions are naturally unique (different ranges)
3. Enables secondary market trading without new code
4. `Taxon` field allows easy categorization

### 5.3 Why Predefined Fee Tiers?

Independent fee configuration was considered but rejected due to:

1. Scam risk: Malicious actors could create 99% fee pools
2. Complexity: Users must understand fee/tick spacing relationship
3. Proven model: Uniswap V3's four tiers cover all use cases

The four predefined tiers (0.01%, 0.05%, 0.30%, 1.00%) are battle-tested and cover:

- Stablecoin pairs (minimal volatility)
- Correlated assets (low volatility)
- Standard pairs (medium volatility)
- Exotic pairs (high volatility)

### 5.4 Why Continuous Auction?

TWAP-based mechanisms were considered but rejected due to:

1. High storage cost for price observations
2. Vulnerability to slow manipulation
3. No existing TWAP infrastructure on XRPL

The continuous auction mechanism:

1. Is already proven on XRPL (XLS-30)
2. Has minimal storage requirements
3. Returns MEV to LPs rather than arbitrageurs
4. Provides predictable behavior

### 5.5 Why Payment Engine Integration?

Standalone `CLAMMSwap` transactions are useful but insufficient because:

1. Users must know which pool to use
2. No automatic best-price routing
3. Liquidity fragmentation across venues

Integration with the payment engine:

1. Provides seamless UX (just send a Payment)
2. Automatically finds best rates
3. Can split orders across multiple venues
4. Maintains backwards compatibility

---

## 6. Backwards Compatibility

### 6.1 No Breaking Changes

This specification introduces new ledger entry types and transaction types. It does not modify existing functionality.

### 6.2 Coexistence with XLS-30

CLAMM pools coexist with XLS-30 AMM pools:

- Both can exist for the same asset pair
- Payment engine routes through whichever offers better rates
- LPs can choose their preferred model

### 6.3 NFToken Dependency

This specification requires XLS-20 (NFToken) to be enabled. Positions cannot be created on networks without NFToken support.

---

## 7. Test Plan

### 7.1 Unit Tests

| Category        | Tests                                                           |
| --------------- | --------------------------------------------------------------- |
| Pool Creation   | Valid creation, duplicate rejection, invalid fee tier           |
| Deposits        | Single-sided, dual-sided, range calculations, minimum liquidity |
| Withdrawals     | Partial, full, fee collection, NFToken burning                  |
| Swaps           | Within tick, cross tick, multiple ticks, slippage protection    |
| Fee Calculation | Accumulation, distribution, auction discount                    |
| Auction         | Bidding, expiration, authorized accounts                        |
| Math            | Sqrt price conversion, liquidity calculation, overflow handling |

### 7.2 Integration Tests

| Scenario              | Description                                                |
| --------------------- | ---------------------------------------------------------- |
| Full Lifecycle        | Create pool -> deposit -> swap -> collect fees -> withdraw |
| Multi-LP              | Multiple LPs with overlapping ranges                       |
| Position Transfer     | Transfer NFToken, verify ownership update                  |
| Payment Routing       | Payment through CLAMM, DEX, and mixed paths                |
| Concurrent Operations | Multiple swaps in same ledger                              |

### 7.3 Invariant Tests

| Invariant             | Description                                             |
| --------------------- | ------------------------------------------------------- |
| Conservation          | Assets in = Assets out + fees                           |
| Liquidity Consistency | Sum of position liquidities = tick liquidity references |
| Price Bounds          | Sqrt price within valid tick range                      |
| Fee Growth            | Fee growth monotonically increasing                     |

### 7.4 Fuzz Tests

- Random deposit/withdraw sequences
- Random swap sequences
- Random price movements
- Edge cases: MIN_TICK, MAX_TICK, zero liquidity

---

## 8. Security Considerations

### 8.1 Price Manipulation

**Risk:** Attacker manipulates price to exploit LPs or other protocols.

**Mitigations:**

- Continuous auction mechanism makes manipulation expensive
- Slippage protection on all operations
- No oracle dependency (price is market-determined)

### 8.2 Reentrancy

**Risk:** Malicious token callbacks during swap execution.

**Mitigation:** XRPL's transaction model prevents reentrancy by design. All state changes are atomic within a transaction.

### 8.3 Integer Overflow

**Risk:** Calculations overflow, leading to incorrect amounts.

**Mitigations:**

- Use of 128-bit integers for liquidity and sqrt price
- Explicit overflow checks in all calculations
- Invariant tests for conservation

### 8.4 Dust Attacks

**Risk:** Attacker creates many tiny positions to bloat ledger.

**Mitigations:**

- Minimum liquidity requirement (1 XRP worth)
- Reserve requirements for positions and ticks
- Position creation cost (NFToken minting)

### 8.5 Front-Running

**Risk:** Attacker observes pending transactions and front-runs.

**Mitigations:**

- Continuous auction captures arbitrage value for LPs
- Slippage protection parameters
- XRPL's consensus ordering provides some protection

### 8.6 Liquidity Provider Risks

**Risk:** Impermanent loss from price movements.

**Mitigations:**

- This is an inherent AMM risk, not a protocol vulnerability
- Concentrated liquidity amplifies both gains and losses
- LPs should understand the risks before providing liquidity

### 8.7 Flash Loan Attacks

**Risk:** Attacker uses flash loans to manipulate pool state.

**Mitigation:** XRPL does not have native flash loans. Single-transaction manipulation is limited by account balances.

### 8.8 Tick Bitmap Manipulation

**Risk:** Attacker creates/deletes ticks to increase gas costs for other users.

**Mitigations:**

- Reserve requirements for tick creation
- Tick spacing limits number of possible ticks
- Minimum liquidity prevents trivial tick creation

---

## 9. Appendix

### Appendix A: FAQ

#### A.1: How does concentrated liquidity improve capital efficiency?

In traditional AMMs, liquidity is spread across all prices from 0 to infinity. If you provide $1000 of liquidity, only a tiny fraction earns fees at any given price. With concentrated liquidity, you can focus your $1000 on a specific range (e.g., $0.45 to $0.55 for an XRP/USD pair), earning fees as if you had provided much more liquidity.

#### A.2: What happens when the price moves outside my range?

Your position becomes inactive and stops earning fees. Your liquidity is converted entirely to one asset (the less valuable one at that point). You can:

1. Wait for price to return to range
2. Withdraw and create a new position at the current price
3. Add liquidity to a new range while keeping the old position

#### A.3: Can I have multiple positions in the same pool?

Yes. Each deposit creates a new position with its own NFToken. You can have multiple positions with different ranges in the same pool.

#### A.4: How are fees distributed among LPs?

Fees are distributed proportionally to liquidity within the active range. If your position is out of range, you earn no fees. If your position has 10% of the active liquidity, you earn 10% of the fees.

#### A.5: What is the auction slot for?

The auction slot allows arbitrageurs to bid for the right to pay reduced trading fees. The bid payments are distributed to LPs, returning MEV (Maximal Extractable Value) to liquidity providers rather than external bots.

#### A.6: How do I sell my LP position?

Your position is represented by an NFToken. You can sell it on any XRPL NFToken marketplace. The buyer receives ownership of the position, including any uncollected fees.

#### A.7: What are the risks of providing concentrated liquidity?

1. **Impermanent loss:** Price movements cause losses relative to holding
2. **Amplified IL:** Concentrated positions have higher IL than full-range
3. **Range management:** You must actively manage your range
4. **Smart contract risk:** Bugs could result in loss of funds

#### A.8: How do I choose the right fee tier?

| Pair Type             | Recommended Tier | Reason             |
| --------------------- | ---------------- | ------------------ |
| Stablecoins (USD/EUR) | STABLE (0.01%)   | Minimal volatility |
| Correlated (BTC/ETH)  | LOW (0.05%)      | Low volatility     |
| Standard (XRP/USD)    | MEDIUM (0.30%)   | Normal volatility  |
| Exotic/New tokens     | HIGH (1.00%)     | High volatility    |

#### A.9: Can multiple pools exist for the same asset pair?

Yes. You can have up to 4 pools per asset pair (one for each fee tier). This allows LPs to choose their preferred risk/reward profile.

#### A.10: How does this interact with the existing DEX?

CLAMM pools are integrated into the payment engine alongside the order book DEX and XLS-30 AMM. When you send a payment, the engine automatically finds the best rate across all liquidity sources.

---

### Appendix B: Design Discussion

#### B.1: Why Q64.96 for Sqrt Price?

The Q64.96 format provides:

- 64 bits for the integer part (sufficient for any realistic price)
- 96 bits for the fractional part (high precision for calculations)
- Compatibility with Uniswap V3's format (ecosystem familiarity)

#### B.2: Why Tick Spacing?

Without tick spacing, LPs could create positions at every possible tick, leading to:

- Higher storage costs (more tick objects)
- More tick crossings during swaps (higher compute)
- No clear relationship between fee and granularity

Tick spacing ensures that lower fee tiers (which require more precision) have finer granularity, while higher fee tiers have coarser granularity.

#### B.3: Why Not Support Custom Fee Tiers?

Custom fees were rejected because:

1. **Scam risk:** Malicious pools with 99% fees
2. **Complexity:** Users must understand fee/spacing relationship
3. **Fragmentation:** Liquidity spread across many fee levels
4. **Proven model:** Four tiers cover all real-world use cases

#### B.4: Why Continuous Auction Instead of TWAP?

| Factor         | Continuous Auction | TWAP                            |
| -------------- | ------------------ | ------------------------------- |
| Storage        | Minimal            | High (observation history)      |
| Manipulation   | Expensive          | Vulnerable to slow manipulation |
| Implementation | Proven on XRPL     | New infrastructure needed       |
| Complexity     | Medium             | High                            |

#### B.5: Position NFToken URI Format

The position NFToken's URI contains metadata about the position:

```json
{
    "standard": "CLAMM-Position-v1",
    "pool_id": "ABC123...",
    "asset": { "currency": "USD", "issuer": "rIssuer..." },
    "asset2": { "currency": "XRP" },
    "fee_tier": 2,
    "lower_tick": 1000,
    "upper_tick": 1500
}
```

This allows wallets and marketplaces to display position details without querying the ledger.

---

## References

- [Uniswap V3 Whitepaper](https://uniswap.org/whitepaper-v3.pdf)
- [Uniswap V3 Core Contracts](https://github.com/Uniswap/v3-core)
- [XLS-20 NFToken Specification](https://github.com/XRPLF/XRPL-Standards/tree/master/XLS-0020-non-fungible-tokens)
- [XLS-30 AMM Specification](https://github.com/XRPLF/XRPL-Standards/tree/master/XLS-0030-automated-market-maker)
- [XRPL Documentation](https://xrpl.org/docs/)
