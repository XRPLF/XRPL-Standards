<pre>
  xls: 30
  title: Automated Market Maker on XRPL
  description: Non-custodial automated market maker as a native feature to the XRPL DEX with unique auction mechanism for trading advantages
  author: Aanchal Malhotra <amalhotra@ripple.com>, David J. Schwartz <david@ripple.com>
  proposal-from: https://github.com/XRPLF/XRPL-Standards/discussions/78
  status: Final
  category: Amendment
  created: 2022-06-30
</pre>

# Automated Market Maker on XRP Ledger

### Abstract

The XRPL decentralized exchange (DEX) currently provides liquidity exclusively by manual market making and order books. This proposal adds non-custodial automated market maker (AMM) as a native feature to the XRPL DEX in a way that provides increased returns to those who provide liquidity for the AMM and minimizes the risk of losses due to volatility.

We propose a unique mechanism where the AMM instance continuously auctions off trading advantages to arbitrageurs, charging them and giving these earnings to its liquidity providers. This allows liquidity providers to take a large share of the profits that would normally be taken by arbitrageurs.

The AMM instance charges a spread on the trades that change the ratio of tokens in the instance's pools. This trading fee is added to the AMM instance's capital pool, thus adding to the liquidity providers' returns.

The AMM instances also provide governance rights to the largest share holders of the AMM instance. This allows them to vote on the trading fee the instance charges.

XRPL's AMM based DEX interacts with XRPL's limit order book (LOB)-based DEX so that users of AMM pools have access to all order flow and liquidity on LOB DEX, and vice versa. The payment and order placement transactors automatically determine whether swapping within a liquidity pool or through the order book will provide the best price for the user and execute accordingly. Pathfinding considers paths with both order books and AMMs in various combinations to improve the overall exchange rate.

### 1. Introduction

AMMs are agents that pool liquidity and make it available to traders according to a predetermined algorithm. This is a proposal for geometric mean market maker (GM3)-based DEX as a native XRPL feature. GM3 algorithmically discovers a fair exchange value, stabilized by arbitrage, to automatically produce liquidity. On XRPL, this would provide liquidity pools between XRP and issued assets as well as between any two issued assets. Arbitrageurs play a significant role in keeping the AMM DEX in a stable state with respect to external markets.

Several things that contribute to the costs that trading imposes on AMM pools are naturally much less significant on XRPL:

- **Low transaction fee:** An arbitrageur only submits a transaction when the expected profit from the transaction exceeds the transaction fee. XRPL’s transaction fees are much lower than those on most DeFi chains. This benefits the AMM instance pools by narrowing the time windows in which the instance suffers decreased trading volume due to its spot-market price being off due to volatility or asymmetric trading.

- **Fast finality:** Arbitrageurs take risk (for which they must be compensated at the instance pool’s expense) due to the block times. Prices may change while their transaction is in flux. XRPL has faster block times than many of the fastest competing major blockchains.

- **Canonical transaction ordering:** Transactions on XRPL are canonically ordered. Other blockchains have block producers, miners, or stakers who try to extract value from arbitrage transactions by delaying, reordering, front-running, or selectively including them to extract more value from the pool and the arbitrageurs. XRPL doesn’t have this.

AMMs are more effective and lucrative when transactions execute quickly, cheaply, and fairly. This means that XRPL AMM could provide more liquidity at lower prices, yet still provide a compelling return.

#### 1.1. Terminology

1. **Conservation Function**: We propose a weighted geometric mean market maker (GM3) for AMM price discovery:

$$C = \Gamma_{A}^{W_{A}} *  \Gamma_{B}^{W_{B}} \tag{I}$$

where,

- $\Gamma_{A}$: Current balance of token $A$ in the AMM instance pool
- $\Gamma_{B}$: Current balance of token $B$ in the AMM instance pool
- $W_{A}$: Normalized weight of token $A$ in the AMM instance pool
- $W_{B}$: Normalized weight of token $B$ in the AMM instance pool

In this version of the proposal, pools must be of equal value. The implicit normalized weights are $W_{A} = W_{B} = 0.5$.

2. **Liquidity Providers**: Liquidity providers (LPs) are the traders who add liquidity to the AMM instance's pools, thus earning shares of the pools in the form of `LPTokens`.

3. **LPTokens**: LP tokens represent the liquidity providers' shares of the AMM instance's pools. `LPTokens` are [tokens](https://xrpl.org/tokens.html) on XRPL. Each `LPToken` represents a proportional share of each pool of the AMM instance. The AMM instance account _issues_ the `LPTokens` to LPs upon liquidity provision. `LPTokens` are _balanced_ in the LPs trustline upon liquidity removal.

4. **Spot-Price**: Spot-price (SP) is the weighted ratio of the instance's pool balances. $SP_{A}^{B}$ is the spot-price of asset $A$ relative to asset $B$. $TFee$ is the trading fee paid by the trader for trades executed against the AMM instance.

<NOTE to self: This is the price of one unit of token A in terms of token B.>

$$SP_{A}^{B}  = \frac{\frac{\Gamma_B}{W_B}}{\frac{\Gamma_A}{W_A}} * \frac{1}{\left(1-TFee\right)} \tag{II}$$

5. **Effective-Price**: The effective price (EP) of a trade is defined as the ratio of the tokens the trader sold or swapped in (Token $B$) and the token they got in return or swapped out (Token $A$).

$$EP_{A}^{B} = \frac{\Delta_B}{\Delta_A} \tag{III}$$

<Note to self: This is the price of one unit of token A in terms of token B When we say the effective price of trade it always means the price of per out token in terms of in token>

6. **Slippage**: Slippage is defined as the percentage change in the effective price of a trade relative to the pre-swap spot-price.

#### 1.2. Overview of XRPL AMM features

**AMM Instance Representation**

- We propose the existing [**`AccountRoot`**](https://xrpl.org/accountroot.html) ledger entry and a new ledger entry **`AMM`** to represent an AMM instance with two asset pools. New transaction type **`AMMCreate`** is used to create **`AccountRoot`** and the corresponding **`AMM`** ledger entries. In this version we propose to allow for the creation of only one AMM instance per unique asset pair.

**Trading on AMM Instance**

- To enable adding and removing liquidity to and from the two pools of the AMM instance, we introduce two new transaction types **`AMMDeposit`** and **`AMMWithdraw`** respectively. The proposal allows for both _equal-asset_ as well as _single-sided_ deposits and withdrawals. Adding liquidity to an AMM instance yields pool shares called **`LPTokens`** that are issued by the AMM instance represented as XRPL [tokens](https://xrpl.org/tokens.html#tokens). **`LPTokens`** can be bought, sold and can be used to make payments exactly as other issued assets/tokens on the ledger.

- To enable exchanging one pool asset of the AMM instance for the other - a swap - we propose the existing [**`Payment`**](https://xrpl.org/payment.html) transaction.

**Votable Trading Fee**

- The AMM instance charges a trading fee on the portion of the trade that changes the ratio of tokens in the AMM instance. This fee is added to the AMM instance's pools and is distributed proportionally to the **`LPToken`** holders upon redemption of **`LPTokens`**.
  High trading fee may deter user participation, thus reducing the trading volume and consequently LPs revenue. On the other hand, low trading fee naturally means lower revenue for LPs. Instead of hardcoding the trading fee in the protocol, we propose it be a votable parameter for the **`LPToken`** holders. The assumption is that LPs being the significant stakeholders in an AMM instance are best positioned to collectively make this decision in a balanced way.

**Two-way Interoperable AMM and LOB-based DeXs**

- XRPL's AMM-based and the existing LOB-based DeXs are two-way interoperable, i.e. the interleaved execution of the AMM trades with the existing order book based DeX on XRPL. The key to this integration is transparent injection of the AMM offer into the liquidity stream, which is fed into the payment execution engine. This ensures aggregated liquidity across different DeXs and better exchange rate for the traders.

**Novel Feature: Continuous Auction Mechanism**

- Problem: Due to volatility or asymmetric trading, when relative price of assets in AMM pools goes out-of-sync with that of external markets, AMM does not adjust the prices automatically due to lack of external market information (price-feed) natively. As a result, arbitrageurs intervene, but they have to:
  - Wait until the profit from the arbitrage transaction (and thus the pool’s expected loss) exceeds the trading fees
  - Race/Compete against others, thus reducing their success probability

- Implications: Liquidity Providers lose because:
  - During the **wait window**, there is a decreased trading volume (and thus decreased revenue) for the pool
  - Arbitrageurs make profits from arbitrage transaction at pool's (LPs’) expense

- Our Approach: Create a mechanism that makes it:
  - Easy (higher success probability) for arbitrageurs by eliminating the race condition, AND
  - Profitable for liquidity providers by further narrowing the window of decreased trading volume for the pool and sharing the profits from arbitrage transaction

- Our Innovative Solution: To achieve the above mentioned, we introduce a mechanism for the AMM instance to continuously auction-off trading advantages for a 24-hour slot at zero trading fee! Anyone can bid for the auction slot with the units of **`LPtokens`**. The slot-holder can send the arbitrage transaction **immediately** without the need to wait for their profits to exceed the trading fee, thus eliminating the race condition for them. This also reduces the **time window** for which the pool suffers decreased trading volume. Additionally, part of proceeds (**`LPTokens`**) from the auction are deleted/burnt that effectively increases LP token holders' ownership in the pool proportionally. Since it's a continuous auction mechanism, if someone outbids an auction slot-holder, part of proceeds from the auction are refunded to the previous slot-holder (computed pro-rata). For details refer Section 5.

As slot holder will have significant advantages for arbitrage, it’s expected that arbitrageurs will bid up the price of the auction slot to nearly the value they extract through arbitrage.

- Expected Results
  - Eliminates wait time & race condition for auction slot holder (arbitrageur)
  - Narrows time windows in which the pool suffers decreased trading volume
  - Liquidity providers additionally reap a share of profits that would otherwise go JUST to arbitrageurs

## 2. Creating AMM instance on XRPL

### 2.1. On-Ledger Objects

We propose the existing **`AccountRoot`** object together with a new ledger object **`AMM`** to represent an AMM instance. Currently, the **`AccountRoot`** object type describes a single account, its settings, and XRP balance on the XRP ledger. The **`AccountRoot`** and the **`AMM`** objects that represent an AMM instance can be created using the new **`AMMCreate`** transaction. XRP balance of the AMM instance pools is always tracked via the existing `Balance` field of the **`AccountRoot`** object. The issued asset balances of the AMM instance pools and **`LPTokens`** are automatically tracked via trust lines. The AMM can be traded against using the new **`AMMDeposit`** and **`AMMWithdraw`** and the existing **`Payment`** transactions. Additionally, the AMM instance in "empty" state can be deleted using the `AMMDelete` transaction.

Note that in this version, only equal-weighted two asset pools are supported. However, differing weighted pools could be supported in future versions.

#### 2.1.1. Ledger Entries representing AMM instance

##### **`AccountRoot`** ledger entry

We introduce a new field called `AMMID` to the `AccountRoot` object. It provides an easy link to the corresponding `AMM` object and a way to identify the AMM `AccountRoot`.

| Field Name |     Required?      | JSON Type | Internal Type |
| ---------- | :----------------: | :-------: | :-----------: |
| `AMMID`    | :heavy_check_mark: | `string`  |   `UINT256`   |

`AMMID` specifies the `AMMID` as described below.

The unique ID of the **`AccountRoot`** object, a.k.a. **`AccountRootID`** is computed as follows:

- for (i = 0; i <= 256; i--)
  - Compute `AccountRootID` = `SHA512-Half`(i || [Parent Ledger Hash](https://xrpl.org/ledgerhashes.html) || `AMMID`)
  - If the computed `AccountRootID` exists, repeat
    - else, return `AccountRootID`

#### **`AMM`** ledger entry

The unique ID of the new **`AMM`** object , a.k.a **`AMMID`** is computed as follows:

- Calculate the `SHA512-Half` of some of the following values:
  - The `issuer` of the issued asset;
  - The `currency` of the issued asset;
  - The `issuer` of the second issued asset, if there exists one;
  - The `currency` of the second issued asset, if there exists one;
  <!-- `XRP` if the `Balance` field exists, i.e. if one of the assets is XRP "GT: why is this needed? We just use issuer/currency of each asset. XRP defaults both to 0."-->

The order of the fields to compute the hash is decided canonically. The **`AMMID`** associated with this **`AccountRootID`** is this hash to ensure the uniqueness of the AMM instance. The applications can look-up the **`AccountRootID`** for a specific AMM instance by providing the asset pair for that instance.

The **`AMM`** ledger entry contains the following fields for the **`AccountRoot`** object that represents the AMM instance.

1. **`Account`** specifies the ID of the `AccountRoot` object associated with this `AMM` ledger entry.
2. **`TradingFee`** specifies the fee, in basis point, to be charged to the traders for the trades executed against this AMM instance. Valid values for this field are between 0 and 1000 inclusive. A value of 1 is equivalent to 1/10 bps or 0.001%, allowing trading fee between 0% and 1%. Trading fee is a percentage of the trade size. It is charged on the asset being deposited for the `AMMDeposit` (if applicable) and `Payment` transactions and on the asset being withdrawn for the `AMMWithdraw` (if applicable) transaction. This fee is added to the AMM instance's pools and is distributed to the LPs in proportion to the `LPTokens` upon liquidity removal.

3. **`VoteSlots`** represents an array of `Vote` objects.
4. **`AuctionSlot`** represents the `Auction` object.
5. **`LPTokenBalance`** specifies the balance of outstanding liquidity Provider Tokens (LPTokens).
6. **`Asset`** specifies the one of the assets of the AMM instance.
7. **`Asset2`** specifies the other asset of the AMM instance.
8. **`OwnerNode`** specifies the page hint for the **DirectoryNode** entry to link the account root and the corresponding AMM objects.

Once the AMM **`AccountRoot`** object is created, we make sure that no further transactions can originate from this account. Conceptually, it is an account that is not owned by anyone. So every possible way of signing the transaction for this account MUST be automatically disabled.

### 2.2. Transaction for creating AMM instance

We define a new transaction **`AMMCreate`** specifically for creating a new AMM instance represented by an **`AccountRoot`** object and the corresponding **`AMM`** object.

Notes:

- **`AMMCreate`** is not allowed with `LPTokens`
- **`AMMCreate`** is not allowed if the token’s issuer has `DefaultRipple` flag disabled.

#### 2.2.1. Transaction fields for **`AMMCreate`** transaction

| Field Name        |     Required?      | JSON Type | Internal Type |
| ----------------- | :----------------: | :-------: | :-----------: |
| `TransactionType` | :heavy_check_mark: | `string`  |   `UINT16`    |

`TransactionType` specifies the new transaction type **`AMMCreate`**. The integer value is 35.

---

| Field Name |     Required?      | JSON Type | Internal Type |
| ---------- | :----------------: | :-------: | :-----------: |
| `Fee`      | :heavy_check_mark: | `string`  |   `AMOUNT`    |

`Fee` specifies the integer amount of XRP, in drops, to be destroyed as a cost of creating an AMM instance. We DO NOT propose to keep a reserve for the AMM instance.

---

<NOTE to self: Decide on the special fee for this transaction>

| Field Name |     Required?      |      JSON Type       | Internal Type |
| ---------- | :----------------: | :------------------: | :-----------: |
| `Amount`   | :heavy_check_mark: | `string` or `object` |   `AMOUNT`    |

`Amount` specifies one of the pool assets (XRP or token) of the AMM instance.

---

| Field Name |     Required?      |      JSON Type       | Internal Type |
| ---------- | :----------------: | :------------------: | :-----------: |
| `Amount2`  | :heavy_check_mark: | `string` or `object` |   `AMOUNT`    |

`Amount2` specifies the other pool asset of the AMM instance.

Both `Amount` and `Amount2` that represent issued assets MUST have `value` subfields specified.

---

| Field Name   |     Required?      | JSON Type | Internal Type |
| ------------ | :----------------: | :-------: | :-----------: |
| `TradingFee` | :heavy_check_mark: | `number`  |   `UINT16`    |

`TradingFee` specifies the fee, in basis point, to be charged to the traders for the trades executed against the AMM instance. Trading fee is a percentage of the trading volume. Valid values for this field are between 0 and 1000 inclusive. A value of 1 is equivalent to 1/10 bps or 0.001%, allowing trading fee between 0% and 1%.

---

The `AMMCreate` transaction MUST fail if the account issuing this transaction:

i. does not have sufficient balances, OR

ii. is NOT the `issuer` of either token AND the `RequireAuth` flag for the corresponding token is set AND the account initiating the transaction is not authorized.

If the transaction is successful,

i. Three new ledger entries **`AccountRoot`**, `AMM` and `DirectoryNode` are created.

ii. The regular key for the **`AccountRoot`** ledger entry is set to account zero, and the master key is disabled, effectively disabling all possible ways to sign transactions from this account.

iii. New trust lines are created.

#### 2.2.2. Trustlines

A successful `AMMCreate` transaction will automatically create the following trust lines:

- Trustlines that track the balance(s) of the issued asset(s) of the AMM instance's pool(s) between the AMM instance account and the issuer.
- Trustlines that track the balance of `LPTokens` between the AMM instance and the account that initiated the transaction. `LPTokens` are uniquely identified by the following:
  - issuer: AMM instance `AccountID` and;
  - currency: the currency code for `LPTokens` for currency codes cur1 and cur2 is formed deterministically as follows:

  - Compute `SHA256{cur1, cur2}`
  - `LPTokenID` = 0x03 + first 19 bytes from SHA256

The prefix 0x03 is added to identify `LPTokens`

The `value` field is computed as follows:

$$LPTokens = \Gamma_{A}^{W_{A}} *  \Gamma_{B}^{W_{B}} $$

where,

- $\Gamma_{A}$: Balance of asset $A$
- $\Gamma_{B}$: Balance of asset $B$
- $W_{A}$ & $W_{B}$: Normalized weights of asset $A$ and asset $B$ in the pool respectively

Initially by default, $W_{A}$ = $W_{B}$ = 0.5

<NOTE to self: Address the cases when authorization behaviours change on a trustline.>

#### 2.2.3. Cost of creating AMM instance `AccountRoot` and `AMM` ledger entries

Unlike other objects in the XRPL, there is no reserve for the `AccountRoot` and `AMM` ledger entries created by an `AMMCreate` transaction. Instead there is a higher `Fee` (~ 1 reserve) for `AMMCreate` transaction in XRP which is burned as a special transaction cost.

### 2.3. Deleting the AMM instance `AccountRoot`, `AMM` and `DirectoryNode` ledger entries

On final withdraw (i.e. when `LPTokens` balance is 0) the AMM instance automatically deletes up to 512 trust lines. If there are fewer then 512 trustlines then `AMM`, `AccountRoot` and `DirecotoryNode` objects are deleted.

However, if there are more than 512 trustlines then AMM instance remains in empty state (`LPTokens` balance is 0). To handle cleaning this up, we introduce a new transaction type `AMMDelete` to delete the remaining trustlines. Anyone can call the `AMMDelete` transactor. `AMMDelete` also has a limit of 512 trustlines and deletes the `AMM`, `AccountRoot` and `DirectoryNode` objects only if there are fewer than 512 trustlines at the time it executes. If there are more trustlines to delete, then `AMMDelete` returns the `tecINCOMPLETE` result code and the user should submit another `AMMDelete` to delete more entries.

In order to avoid destroying assets of the AMM instance, the implementation of the `AMMWithdraw` transaction MUST guarantee that the AMM instance has no asset reserves if no account owns its `LPTokens`.

#### 2.3.1. Fields of AMMDelete Transaction

---

| Field Name        |     Required?      | JSON Type | Internal Type |
| ----------------- | :----------------: | :-------: | :-----------: |
| `TransactionType` | :heavy_check_mark: | `string`  |   `UINT16`    |

`TransactionType` specifies the new transaction type **`AMMDelete`**. The integer value is 40.

---

| Field Name |     Required?      | JSON Type | Internal Type |
| ---------- | :----------------: | :-------: | :-----------: |
| `Asset`    | :heavy_check_mark: | `object`  |    `ISSUE`    |

`Asset` specifies one of the assets of the AMM instance against which the transaction is to be executed. The `ISSUE` `object` may have the following subfields:

| Field name |     Required?      | Description                                                                  |
| :--------: | :----------------: | :--------------------------------------------------------------------------- |
|  `issuer`  | :heavy_check_mark: | specifies the unique XRPL account address of the entity issuing the currency |
| `currency` | :heavy_check_mark: | arbitrary code for currency to issue                                         |

If the asset is XRP, then the issuer subfield is not mentioned.

---

| Field Name |     Required?      | JSON Type | Internal Type |
| ---------- | :----------------: | :-------: | :-----------: |
| `Asset2`   | :heavy_check_mark: | `object`  |    `ISSUE`    |

`Asset2` specifies the other asset of the AMM instance against which the transaction is to be executed. The `ISSUE` `object` may have the following subfields:

---

| Field name |     Required?      | Description                                                                  |
| :--------: | :----------------: | :--------------------------------------------------------------------------- |
|  `issuer`  | :heavy_check_mark: | specifies the unique XRPL account address of the entity issuing the currency |
| `currency` | :heavy_check_mark: | arbitrary code for currency to issue                                         |

### 2.4. AMM trade transactions

Users can trade against specific AMM instances using the new transactions **`AMMDeposit`** and **`AMMWithdraw`**, and the existing **`Payment`** transaction.

1. `AMMDeposit`: The deposit transaction is used to add liquidity to the AMM instance pool, thus obtaining some share of the instance's pools in the form of `LPTokens`.
2. `AMMWithdraw`: The withdraw transaction is used to remove liquidity from the AMM instance pool, thus redeeming some share of the pools that one owns in the form of `LPTokens`.
3. `Payment`: The payment transaction is used to exchange one asset of the AMM instance for the other.

#### 2.4.1. AMMDeposit transaction

With **`AMMDeposit`** transaction, XRPL AMM allows for both:

- **all assets** liquidity provision
- **single asset** liquidity provision

##### 2.4.1.1 Fields for AMMDeposit transaction

| Field Name        |     Required?      | JSON Type | Internal Type |
| ----------------- | :----------------: | :-------: | :-----------: |
| `TransactionType` | :heavy_check_mark: | `string`  |   `UINT16`    |

`TransactionType` specifies the new transaction type **`AMMDeposit`**. The integer value is 36.

---

| Field Name |     Required?      | JSON Type | Internal Type |
| ---------- | :----------------: | :-------: | :-----------: |
| `Asset`    | :heavy_check_mark: | `object`  |    `ISSUE`    |

`Asset` specifies one of the assets of the AMM instance against which the transaction is to be executed. The `ISSUE` `object` may have the following subfields:

| Field name |     Required?      | Description                                                                  |
| :--------: | :----------------: | :--------------------------------------------------------------------------- |
|  `issuer`  | :heavy_check_mark: | specifies the unique XRPL account address of the entity issuing the currency |
| `currency` | :heavy_check_mark: | arbitrary code for currency to issue                                         |

If the asset is XRP, then the issuer subfield is not mentioned.

---

| Field Name |     Required?      | JSON Type | Internal Type |
| ---------- | :----------------: | :-------: | :-----------: |
| `Asset2`   | :heavy_check_mark: | `object`  |    `ISSUE`    |

`Asset2` specifies the other asset of the AMM instance against which the transaction is to be executed.

---

| Field Name | Required? |      JSON Type       | Internal Type |
| ---------- | :-------: | :------------------: | :-----------: |
| `Amount`   |           | `string` or `object` |   `AMOUNT`    |

`Amount` specifies the amount of one of the pools assets. If the asset is XRP, then the `Amount` is a `string` specifying the number of drops. Otherwise it is an `object` with the following subfields:

| Field name |     Required?      | Description                                                                                                 |
| :--------: | :----------------: | :---------------------------------------------------------------------------------------------------------- |
|  `issuer`  | :heavy_check_mark: | specifies the unique XRPL account address of the entity issuing the currency                                |
| `currency` | :heavy_check_mark: | arbitrary code for currency to issue                                                                        |
|  `value`   |                    | specifies the maximum amount of this currency, in decimal representation, that the trader is willing to add |

---

| Field Name | Required? |      JSON Type       | Internal Type |
| ---------- | :-------: | :------------------: | :-----------: |
| `Amount2`  |           | `string` or `object` |   `AMOUNT`    |

`Amount2` specifies the details of other pool asset that the trader is willing to add.

---

| Field Name | Required? | JSON Type | Internal Type |
| ---------- | :-------: | :-------: | :-----------: |
| `EPrice`   |           | `string`  |   `AMOUNT`    |

`EPrice` specifies the effective-price of the token out after successful execution of the transaction. For **`AMMDeposit`** transaction, the token out is always `LPToken`.

Note that the relative pricing does not change in case of **all-asset** deposit transaction.
`EPrice` is an invalid field for all assets deposits. It should only be specified in case of single sided deposits.

---

| Field Name   | Required? | JSON Type | Internal Type |
| ------------ | :-------: | :-------: | :-----------: |
| `LPTokenOut` |           | `string`  |   `AMOUNT`    |

`LPTokenOut` specifies the amount of shares of the AMM instance pools.

---

| Field Name   | Required? | JSON Type | Internal Type |
| ------------ | :-------: | :-------: | :-----------: |
| `TradingFee` |           | `string`  |    `UINT8`    |

`TradingFee` specifies the trading fee for the AMM instance. This field is only valid if the option flag `tfTwoAssetIfEmpty` is set. In this case, the AMM instance is in the empty state and `AMMDeposit` becomes `AMMCreate` type transaction.

---

Let the following represent the pool composition of AMM instance before trade:

- $\Gamma_{A}$: Current balance of asset $A$
- $\Gamma_{B}$: Current balance of asset $B$
- $\Gamma_{LPTokens}$: Current balance of outstanding `LPTokens` issued by the AMM instance

Let the following represent the assets being deposited as a part of **`AMMDeposit`** transaction and the corresponding `LPTokens` being issued by the AMM instance.

- $\Delta_{A}$: Balance of asset $A$ being added
- $\Delta_{B}$: Balance of asset $B$ being added
- $\Delta_{LPTokens}$: Balance of `LPTokens` issued to the LP after a successful **`AMMDeposit`** transaction

And let $TFee$ represent the trading fee paid by the account that initiated the transaction to the AMM instance's account. This fee is added to the corresponding AMM instance pool and is proportionally divided among the `LPToken` holders.

#### 2.4.1.2. All assets deposit (pure liquidity provision)

If the trader deposits proportional values of both assets without changing their relative pricing, no trading fee is charged on the transaction. If $A$
and $B$ are the assets being deposited in return for
$\Delta_{LPTokens}$, then

$$\Delta_{A} = \left(\frac{\Delta_{LPTokens}}{\Gamma_{LPTokens}}\right) * \Gamma_{A} \tag{1}$$

AND

$$\Delta_{B} = \left(\frac{\Delta_{LPTokens}}{\Gamma_{LPTokens}}\right) * \Gamma_{B} \tag{2}$$

Following is the updated pool composition of the AMM instance after successful transaction:

- $\Gamma_{A} = \Gamma_{A} + \Delta_{A}$: Current new balance of asset $A$
- $\Gamma_{B} = \Gamma_{B} + \Delta_{B}$: Current new balance of asset $B$
- $\Gamma_{LPTokens} = \Gamma_{LPTokens} + \Delta_{LPTokens}$: Current new balance of outstanding `LPTokens`

#### 2.4.1.3 Single asset deposit

Let $B$ be the only asset being deposited in return for $\Delta_{LPTokens}$, then this is executed as a combination of _equal asset_ deposit and a _swap_ transaction. The trading fee is only charged on the _amount_ of asset being swapped.

Also let

- $F_{1} = (1-TFee)$
- $F_{2} = \frac{(1 - \frac{TFee}{2})}{F_1}$, then

$$
\Delta_{LPTokens} = \Gamma_{LPTokens} * \left[\frac{\frac{\Delta_{B}}{\Gamma_{B}} - \left[\left({F_2}^{\frac{1}{W_{B}}} + \frac{\Delta_{B}}{(\Gamma_{B}*F_1)}\right)^{W_B} - F_2\right]}
        {1 + {\left(F_2^{\frac{1}{W_B}} + \frac{\Delta_{B}}{(\Gamma_{B}*F_1)}\right)}^{W_{B}} - F_2}\right] \tag{3}
$$

Similarly, we can derive $\Delta{B}$ from the above equation. We call this equation 4.

Following is the updated pool composition of the AMM instance after successful trade:

- $\Gamma_{B} = \Gamma_{B} + \Delta_{B}$: Current new balance of asset $B$
- $\Gamma_{LPTokens} = \Gamma_{LPTokens} + \Delta_{LPTokens}$: Current new balance of outstanding `LPTokens`

#### 2.4.1.4. Specifying different parameters

The proposal allows for traders to specify different combinations of the above mentioned fields for **`AMMDeposit`** transaction. The implementation will determine the best possible sub operations based on trader's specifications.
We introduce the following flags to the `AMMDeposit` transaction to identify valid parameter combinations.

| Flag Name           | Hex Value  |                                                     Description                                                     |
| ------------------- | :--------: | :-----------------------------------------------------------------------------------------------------------------: |
| `tfLPToken`         | 0x00010000 |      If set, it indicates `LPTokenOut` parameter and may optionally include `Amount` and `Amount2` combination      |
| `tfSingleAsset`     | 0x00080000 |              If set, it indicates `Amount` parameter and may optionally include `LPTokenOut` parameter              |
| `tfTwoAsset`        | 0x00100000 | If set, it indicates `Amount` and `Amount2` parameter combination and may optionally include `LPTokenOut` parameter |
| `tfOneAssetLPToken` | 0x00200000 |                        If set, it indicates `Amount` and `LPTokenOut` parameter combination                         |
| `tfLimitLPToken`    | 0x00400000 |                          If set, it indicates `Amount` and `EPrice` parameter combination                           |
| `tfWithdrawAll`     | 0x00020000 |                           If set, it indicates proportional withdrawal of all `LPTokens`                            |
| `tfTwoAssetIfEmpty` | 0x00800000 |         If set, it indicates that this deposit can only be submitted on an empty state AMM (LPTokens == 0)          |

If `tfTwoAssetIfEmpty` is set, both amounts have to be specified and deposited into AMM as is. It is sort of like `AMMCreate` in an empty AMM state.

Following are the recommended valid combinations. Other invalid combinations may result in the failure of transaction.

- `LPTokenOut`, `[Amount]`, `[Amount2]`
- `Amount`, `[LPTokenOut]`
- `Amount` , `Amount2`, `[LPTokenOut]`
- `Amount` and `LPTokenOut`
- `Amount` and `EPrice`
- `Amount` , `Amount2`, `[TradingFee]`

Details for above combinations:

1. Fields specified: `LPTokenOut`, `[Amount]`, `[Amount2]` and Flag: `tfLPToken`

Such a transaction assumes proportional deposit of pools assets in exchange for the specified amount of `LPTokenOut` of the AMM instance. `Amount` and `Amount2`, if included, have to be provided both and specify minimum deposit amounts for each asset.
Deposit fails if the min deposit condition is not met

2. Fields specified: `Amount`, `[LPTokenOut]` and Flag: `tfSingleAsset`

Such a transaction assumes single asset deposit of the amount of asset specified by `Amount`. This is essentially an _equal_ asset deposit and a _swap_.

If the asset to be deposited is a token, specifying the `value` field is required, else the transaction will fail.

`LPTokenOut`, if included, specified minimum `LPTokens` amount that the user receives, else the transaction will fail.

3. Fields specified: `Amount`, `Amount2`, `[LPTokenOut]`, and Flag: `tfTwoAsset`

Such a transaction assumes proportional deposit of pool assets with the constraints on the maximum amount of each asset that the trader is willing to deposit.

`LPTokenOut`, if included, specified minimum `LPTokens` amount that the user receives, else the transaction will fail.

4. Fields specified: `Amount` and `LPTokenOut` and Flag: `tfOneAssetLPToken`

Such a transaction assumes that a single asset `Amount` is deposited to obtain some share of the AMM instance's pools represented by amount of `LPTokenOut`. Since adding liquidity to the pool with one asset changes the ratio of the assets in the two pools, thus changing the relative pricing, trading fee is charged only on the amount of the deposited asset that causes this change.

5. Fields specified: `Amount` and `EPrice` and Flag: `tfLimitLPToken`

Such a transaction assumes single asset deposit with the following two constraints:

a. amount of asset1 if specified in `Amount` specifies the maximum amount of asset1 that the trader is willing to deposit

b. The effective-price of the `LPTokenOut` traded out does not exceed the specified `EPrice`

6. Fields specified: `Amount`, `Amount2`, `[TradingFee]` and Flag: `tfTwoAssetIfEmpty`

Such a transaction assumes proportional deposit of pool assets in the empty state.

Following updates after a successful `AMMDeposit` transaction:

- The deposited asset, if XRP, is transferred from the account that initiated the transaction to the AMM instance account, thus changing the `Balance` field of each account
- The deposited asset, if tokens, are balanced between the AMM account and the issuer account trust line.
- The `LPTokenOut` ~ $\Delta_{LPTokens}$ are issued by the AMM instance account to the account that initiated the transaction and a new trustline is created, if there does not exist one.
- The pool composition is updated. Note that the conservation function is not preserved in case of liquidity provision.

For more details refer to Appendix A.

### 2.4.2. **`AMMWithdraw`** transaction

With `AMMWithdraw` transaction, this proposal allows for both the following:

- **all assets** liquidity withdrawal
- **single asset** liquidity withdrawal

#### 2.4.2.1 Fields

| Field Name        |     Required?      | JSON Type | Internal Type |
| ----------------- | :----------------: | :-------: | :-----------: |
| `TransactionType` | :heavy_check_mark: | `string`  |   `UINT16`    |

`TransactionType` specifies the new transaction type **`AMMWithdraw`**. The integer value is 37.

---

| Field Name |     Required?      | JSON Type | Internal Type |
| ---------- | :----------------: | :-------: | :-----------: |
| `Asset`    | :heavy_check_mark: | `object`  |    `ISSUE`    |

`Asset` specifies one of the assets of the AMM instance against which the transaction is to be executed.

---

| Field Name |     Required?      | JSON Type | Internal Type |
| ---------- | :----------------: | :-------: | :-----------: |
| `Asset2`   | :heavy_check_mark: | `object`  |    `ISSUE`    |

`Asset2` specifies the other asset of the AMM instance against which the transaction is to be executed.

---

| Field Name | Required? |      JSON Type       | Internal Type |
| ---------- | :-------: | :------------------: | :-----------: |
| `Amount`   |           | `object` or `string` |   `AMOUNT`    |

`Amount` specifies one of the pools assets that the trader wants to remove. If the asset is XRP, then the `Amount` is a `string` specifying the number of drops. Otherwise it is an `object` with the following subfields:

| Field name |     Required?      | Description                                                                        |
| :--------: | :----------------: | :--------------------------------------------------------------------------------- |
|  `issuer`  | :heavy_check_mark: | specifies the XRPL address of the issuer of the currency                           |
| `currency` | :heavy_check_mark: | specifies the currency code of the issued currency                                 |
|  `value`   |                    | specifies the minimum amount of this asset that the trader is willing to withdraw. |

---

| Field Name | Required? |      JSON Type       | Internal Type |
| ---------- | :-------: | :------------------: | :-----------: |
| `Amount2`  |           | `string` or `object` |   `AMOUNT`    |

`Amount2` specifies the other asset that the trader wants to remove.

---

| Field Name | Required? | JSON Type | Internal Type |
| ---------- | :-------: | :-------: | :-----------: |
| `EPrice`   |           | `object`  |   `AMOUNT`    |

`EPrice` specifies the effective-price of the token out after successful execution of the transaction. For `AMMWithdraw` transaction, the out is either XRP or issued token. The asset in is always `LPToken`. So `EPrice` is always an `object`.

Note that the relative pricing does not change in case of **all-asset** withdrawal. `EPrice` is an invalid field for all assets deposits. It should only be specified in case of single sided deposits.

---

| Field Name  | Required? | JSON Type | Internal Type |
| ----------- | :-------: | :-------: | :-----------: |
| `LPTokenIn` |           | `object`  |   `AMOUNT`    |

`LPTokenIn` specifies the amount of shares of the AMM instance pools that the trader wants to redeem or trade in.

---

Let following represent the pool composition of the AMM instance before withdrawal:

- $\Gamma_{A}$: Current balance of asset $A$
- $\Gamma_{B}$: Current balance of asset $B$
- $\Gamma_{LPTokens}$: Current balance of outstanding `LPTokens` issued by the AMM instance

Let following represent the assets being withdrawn as a part of `AMMWithdraw` transaction and the corresponding `LPTokens` being redeemed.

- $\Delta_A$: Balance of asset $A$ being withdrawn
- $\Delta_B$: Balance of asset $B$ being withdrawn
- $\Delta_{LPTokens}$: Balance of `LPTokens` being redeemed

Let $TFee$ represent the trading fee paid by the trader to the AMM instance, if applicable. The fee is added to the appropriate pool and is distributed proportionally among the `LPToken` holders upon liquidity withdrawal.

#### 2.4.2.1 All assets withdrawal (Pure liquidity withdrawal)

If the trader withdraws proportional values of both assets without changing their relative pricing, no trading fee is charged on the transaction.
If $A$ and $B$ are the assets being withdrawn by redeeming $\Delta_{LPTokens}$, then

$$\Delta_A = \left(\frac{\Delta_{LPTokens}}{\Gamma_{LPTokens}}\right) * \Gamma_A \tag{5}$$

AND

$$\Delta_B = \left(\frac{\Delta_{LPTokens}}{\Gamma_{LPTokens}}\right) * \Gamma_B \tag{6}$$

Following is the updated pool composition of the AMM instance after successful trade:

- $\Gamma_{A} = \Gamma_{A} - \Delta_{A}$: Current new balance of asset $A$
- $\Gamma_{B} = \Gamma_{B} - \Delta_{B}$: Current new balance of asset $B$
- $\Gamma_{LPTokens} = \Gamma_{LPTokens} - \Delta_{LPTokens}$: Current new balance of outstanding `LPTokens`

#### 2.4.2.2. Single asset withdrawal

Single asset withdrawal can be conceptualized as two sub trades of _equal_ asset withdrawal and a _swap_. Let asset $B$
be the only asset being withdrawn to redeem $\Delta_{LPTokens}$ and let

- $R = \frac{\Delta_B}{\Gamma_B}$
- $C = R * TFee + 2 - TFee$, then

$$\Delta_{LPTokens} = {\Gamma_{LPTokens} * \left[\frac{C -(C^{\frac{1}{W_B}} - 4 * R)^{W_B}}{2}\right]} \tag{7}$$

Similarly, we can derive $\Delta{B}$ from the above equation. We call this equation 8.

Following is the updated pool composition of the AMM instance after successful trade:

- $\Gamma_B = \Gamma_B - \Delta_{B}$: Current new balance of asset $B$
- $\Gamma_{LPTokens} = \Gamma_{LPTokens} - \Delta_{LPTokens}$: Current new balance of outstanding `LPTokens`

#### 2.4.2.3. Specifying different parameters

The proposal allows for traders to specify different combinations of the above mentioned fields for `AMMWithdraw` transaction. The implementation will figure out the best possible operations based on trader's specifications.

We introduce the following six transaction flags to the `AMMWithdraw` transaction to identify valid parameter combinations. Other invalid combinations may result in the failure of transaction.

| Flag Name               | Hex Value  |                                           Description                                            |
| ----------------------- | :--------: | :----------------------------------------------------------------------------------------------: |
| `tfLPToken`             | 0x00010000 |                         If set, it indicates `LPTokenIn` field parameter                         |
| `tfSingleAsset`         | 0x00080000 |                          If set, it indicates `Amount` field parameter                           |
| `tfTwoAsset`            | 0x00100000 |             If set, it indicates `Amount` and `Amount2` fields parameter combination             |
| `tfOneAssetLPToken`     | 0x00200000 |            If set, it indicates `Amount` and `LPTokenIn` fields parameter combination            |
| `tfLimitLPToken`        | 0x00400000 |             If set, it indicates `Amount` and `EPrice` fields parameter combination              |
| `tfWithdrawAll`         | 0x00020000 | If set, it indicates withdrawal of both assets equivalent to all `LPTokens` held by the account  |
| `tfOneAssetWithdrawAll` | 0x00040000 | If set, it indicates withdrawal of single asset equivalent to all `LPTokens` held by the account |

- `LPTokenIn`
- `Amount`
- `Amount` and `Amount2`
- `Amount` and `LPTokenIn`
- `Amount` and `EPrice`

Implementation details for the above combinations:

1. Fields specified: `LPTokenIn`

Such a transaction assumes proportional withdrawal of pool assets for the amount of `LPTokenIn`. Since withdrawing assets proportionally from the AMM instance pools does not change the ratio of the two assets in the pool and thus does not affect the relative pricing, trading fee is not charged on such a transaction.

2. Fields specified: `Amount`

Such a transaction assumes withdrawal of single asset equivalent to the amount specified in `Amount`

3. Fields specified: `Amount` and `Amount2`

Such a transaction assumes all assets withdrawal with the constraints on the maximum amount of each asset that the trader is willing to withdraw.

4. Fields specified: `Amount` and `LPTokenIn`

Such a transaction assumes withdrawal of single asset specified in `Amount` proportional to the share represented by the amount of `LPTokenIn`. Since a single sided withdrawal changes the ratio of the two assets in the AMM instance pools, thus changing their relative pricing, trading fee is charged on the amount of asset1 that causes that change.

5. Fields specified: `Amount` and `EPrice`

<NOTE to self: This is like saying I dont want to pay more than EPrice for AssetOut>

Such a transaction assumes withdrawal of single asset with the following constraints:

a. amount of asset1 if specified in `Amount` specifies the minimum amount of asset1 that the trader is willing to withdraw

b. The effective price of asset traded out does not exceed the amount specified in `EPrice`

Following updates after a successful transaction:

- The withdrawn asset, if XRP, is transferred from AMM instance account to the account that initiated the transaction, thus changing the `Balance` field of each account
- The withdrawn asset, if token, is balanced between the AMM instance account and the issuer account.
- The `LPTokens` ~ $\Delta_{LPTokens}$ are balanced between the AMM instance account and the account that initiated the transaction.
- The pool composition is updated. Conservation function is not preserved in case of liquidity withdrawal (and is not expected to.)

For more details refer to Appendix B.

### 2.5. `AMM Swap`

In order to exchange one asset of the AMM instance's pools for another, we DO NOT introduce a new transaction. Instead, we propose to use the existing [**`Payment`**](https://xrpl.org/payment.html) transaction.

Let the following represent the pool composition of the AMM instance before a swap.

- $\Gamma_{A}$: Current balance of asset $A$ in the pool
- $\Gamma_{B}$: Current balance of asset $B$ in the pool

Let the following represent the balances of assets $B$ and $A$ being swapped in and out of the AMM instance pools respectively with `Payment` transaction.

- $\Delta_{A}$: Balance of asset $A$ being swapped out of the AMM instance's pool
- $\Delta_{B}$: Balance of asset $B$ being swapped into the AMM instance's pool

We can compute $\Delta_{A}$, given $\Delta_{B}$ and $TFee$ as follows:

$$\Delta_{A} = \Gamma_{A}  *    \left[1 – \left(\frac{\Gamma_{B}}{\Gamma_{B}+ \Delta_{B} * \left(1-TFee\right)}\right)^\frac{W_{B}}{W_{A}}\right] \tag{9}$$

Similarly, we can compute $\Delta_{B}$, given $\Delta_{A}$ and $TFee$ as follows:

$$\Delta_{B} = \Gamma_{B} * \left[\left( \frac{\Gamma_{A}}{\Gamma_{A}- \Delta_{A}} \right) ^  \frac{W_A}{W_B}-1 \right] *  \frac{1}{1-TFee}\tag{10}$$

To change the spot-price of token $A$ traded out relative to token $B$ traded into the pool from $SP_{A}^{B}$ to $SP_{A}^{'B}$, required $\Delta_{B}$ can be computed as follows:

$$\Delta_B = \Gamma_{B} *  \left[ \left(\frac{SP_{A}^{'B}}{SP_{A}^{B}}\right)^{\left(\frac{W_A}{W_A+ W_B}\right) } - 1\right] \tag{11}$$

We can compute the average slippage $S(\Delta_B)$ for the token traded in as follows:

$$S(\Delta_B) = SS_B * \Delta_B \tag{12}$$

where $SS_B$, the slippage slope is the derivative of the slippage when the traded amount tends to zero.

$$SS_B = \frac{\left(1-TFee\right) * \left(W_B+W_A\right)}{2*\Gamma_B*W_A } \tag{13}$$

We can compute the average slippage $S(\Delta_A)$ for the token traded out as follows:
$$S(\Delta_A) = SS_{A} * \Delta_{A} \tag{14}$$

where $SS_A$, the slippage slope is the derivative of the slippage when the traded amount tends to zero.
$$SS_{A} = \frac{W_{A} + W_{B}}{2 * \Gamma_{B} * W_{A}} \tag{15}$$

The following is the updated pool composition after a successful transaction:

- $\Gamma_{A} = \Gamma_{A} - \Delta{A}$: Current new balance of asset
  $A$
- $\Gamma_{B} = \Gamma_{B} + \Delta_{B}$: Current new balance of asset
  $B$

Note that the conservation function is preserved, however the ratio of the two assets and hence their relative pricing changes after a successful swap.

Following updates after a successful transaction:

- The swapped asset, if XRP, is transferred from AMM instance account to the account that initiated the transaction or vice-versa, thus changing the `Balance` field of each account
- The swapped asset, if token, is balanced between the AMM instance account and the issuer account.
- The pool composition is updated.

#### 2.5.1. Interpreting **`Payment`** transaction for an AMM swap

An XRPL **`Payment`** transaction represents a transfer of value from one account to another. This transaction type can be used for several types of payments. One can accomplish an equivalent of a swap with the **`Payment`** transaction. Following are the relevant fields of a **`Payment`** transaction.

| Field Name | Required? |     JSON Type     | Internal Type |
| ---------- | :-------: | :---------------: | :-----------: |
| `Amount`   |           | `Currency Amount` |   `AMOUNT`    |

`Amount` field is used to specify the amount of currency that the trader wants to deliver to a destination account. For an AMM swap, this is the amount of currency that the trader wants to swap out of the pool.

| Field Name    | Required? | JSON Type | Internal Type |
| ------------- | :-------: | :-------: | :-----------: |
| `Destination` |           | `String`  |  `AccountID`  |

`Destination` field is used to specify the account that the trader wants to deliver the currency to. This should be either the same account as the transaction or any other account that the trader wishes to send this currency amount to.

| Field Name | Required? |     JSON Type     | Internal Type |
| ---------- | :-------: | :---------------: | :-----------: |
| `SendMax`  |           | `Currency Amount` |   `AMOUNT`    |

`SendMax` field is used to specify the maximum amount of currency that the trader is willing to send from the account issuing the transaction. For an AMM swap, this is the amount of currency that the trader is willing to swap into the pool.

#### 2.5.2. Flags

The `tfLimitQuality` flag is used to specify the **quality** of trade. This is defined as the ratio of the amount in to amount out. In other words, it is the ratio of amounts in `Amount` and `SendMax` fields of a `Payment` transaction.

For an AMM swap, if a trader wants to buy (swap out) one unit of currency specified in `Amount` field for not more than `X` units per currency specified in `SendMax`, the trader would use the following equation:
$$ SendMax = X \* Amount$$

where `X` is equal to the `LimitSpotPrice` for the trade, i.e. the threshold on the spot-price of asset out after trade.

#### 2.5.3. Transfer Fee

We propose that the [transfer fee](https://xrpl.org/transfer-fees.html) is not applied to `AMMCreate`, `AMMDeposit` and `AMMWithdraw` transactions.

AMM instance never pays the transfer fee. Transfer Fee will automatically apply to `Payments` transaction and conditionally in offer-crossing through `OfferCreate`.

## 3. Governance: Trading Fee Voting Mechanism

This proposal allows for the `TradingFee` of the AMM instance be a votable parameter. Any account that holds the corresponding `LPTokens` can cast a vote using the new `AMMVote` transaction.

We introduce a new field `VoteSlots` associated with each AMM instance in the **`AMM`** ledger entry. The `VoteSlots` field keeps a track of up to eight active votes for the instance.

| Field Name  | Required? | JSON Type | Internal Type |
| ----------- | :-------: | :-------: | :-----------: |
| `VoteSlots` |           |  `array`  |    `ARRAY`    |

`VoteSlots` is an array of `VoteEntry` objects representing the LPs and their vote on the `TradingFee` for this AMM instance.

### 3.1. Vote Entry object

Each member of the `VoteSlots` field is an object that describes the vote for the trading fee by the LP of that instance. A `VoteEntry` object has the following fields:

| Field Name |     Required?      | JSON Type | Internal Type |
| ---------- | :----------------: | :-------: | :-----------: |
| `Account`  | :heavy_check_mark: | `string`  |  `AccountID`  |

`Account` specifies the XRPL address of the LP.

---

| Field Name   |     Required?      | JSON Type | Internal Type |
| ------------ | :----------------: | :-------: | :-----------: |
| `TradingFee` | :heavy_check_mark: | `number`  |   `UINT16`    |

`TradingFee` specifies the fee, in basis point. Valid values for this field are between 0 and 1000 inclusive. A value of 1 is equivalent to 1/10 bps or 0.001%, allowing trading fee between 0% and 1%.

---

| Field Name   |     Required?      | JSON Type | Internal Type |
| ------------ | :----------------: | :-------: | :-----------: |
| `VoteWeight` | :heavy_check_mark: | `number`  |   `UINT32`    |

`VoteWeight` specifies the `LPTokens` owned by the account that issued the transaction. It is specified in basis points. Valid values for this field are between 0 and 100000. A value of 1 is equivalent to 1/10 bps or 0.001%, allowing the percentage ownership in the instance between 0% and 100%.

---

`TradingFee` for the AMM instance is computed as the weighted mean of all the current votes in the `VoteSlots` field.

$$TradingFee = \frac{\sum_{i=1}^{8}(w_i * fee_i)}{\sum_{i=1}^{8}(w_i)}$$

where $w_i$ and $fee_i$ represents the `VoteWeight` and the `FeeVal` of the corresponding `VoteEntry`.

### 3.2. **`AMMVote`** transaction

We introduce the new **`AMMVote`** transaction. Any XRPL account that holds `LPTokens` for an AMM instance may submit this transaction to vote for the trading fee for that instance.

#### 3.2.1. Fields

| Field Name |     Required?      | JSON Type | Internal Type |
| ---------- | :----------------: | :-------: | :-----------: |
| `Account`  | :heavy_check_mark: | `string`  |  `AccountID`  |

`Account` specifies the XRPL account that submits the transaction.

---

| Field Name        |     Required?      | JSON Type | Internal Type |
| ----------------- | :----------------: | :-------: | :-----------: |
| `TransactionType` | :heavy_check_mark: | `string`  |   `UINT16`    |

`TransactionType` specifies the new transaction type **`AMMVote`**. The integer value is 38.

---

| Field Name |     Required?      | JSON Type | Internal Type |
| ---------- | :----------------: | :-------: | :-----------: |
| `Asset`    | :heavy_check_mark: | `object`  |    `ISSUE`    |

`Asset` specifies one of the assets of the AMM instance against which the transaction is to be executed.

---

| Field Name |     Required?      | JSON Type | Internal Type |
| ---------- | :----------------: | :-------: | :-----------: |
| `Asset2`   | :heavy_check_mark: | `object`  |    `ISSUE`    |

`Asset2` specifies the other asset of the AMM instance against which the transaction is to be executed.

---

| Field Name   |     Required?      | JSON Type | Internal Type |
| ------------ | :----------------: | :-------: | :-----------: |
| `TradingFee` | :heavy_check_mark: | `number`  |   `UINT16`    |

`TradingFee` specifies the fee, in basis point. Valid values for this field are between 0 and 1000 inclusive. A value of 1 is equivalent to 1/10 bps or 0.001%, allowing trading fee between 0% and 1%.

---

### 3.3. How does **`AMMVote`** transaction work?

**`AMMVote`** transaction _always_ checks if all `VoteEntry` objects in the `VoteSlots` array are up-to-date, i.e. check if there is a change in the number of `LPTokens` owned by an account in the `VoteEntry` and do the following:

1. If one or more accounts in the `VoteEntry` does not hold the `LPTokens` for this AMM instance any more, then remove that `VoteEntry` object from the `VoteSlots` array or If the number of `LPTokens` held by one or more account in the `VoteEntry` has changed,
   - recompute the weights of all the votes and readjust them. Also recompute the `TradingFee` for the AMM instance and update it in the `AMM` object of that instance.

2. Check the `LPTokens` held by the account submitting the `AMMVote` transaction. If the account does not hold any `LPTokens`, then the transaction fails with an error code. Otherwise, there are following cases:
   - If there are fewer than eight `VoteEntry` objects in the updated `VoteSlots` array, then:
     a. Compute the weight of the current vote, add the computed weight of that vote as `VoteWeight` field to the object and readjust in the object.
     b. Add that `FeeVal` of the current vote to the `VoteEntry` object.
     c. Compute the `TradingFee` for the AMM instance as described above and update the `TradingFee` field value in the `AMM` object of the AMM instance.
   - If all eight `VoteEntry` slots are full, but this account holds more `LPTokens`, i.e. higher `VoteWeight` than the `VoteEntry` object with the lowest `VoteWeight`, this vote will replace the `VoteEntry` with the lowest `VoteWeight`. (Followed by same steps as above.)
   - If the account that submitted the transaction already holds a vote, then update that `VoteEntry` and `TradingFee` based on the transaction fields.

## 4. Continuous Auction Mechanism

We introduce a novel mechanism for an AMM instance to auction-off the trading advantages to users (arbitrageurs) at a **discounted** `TradingFee` for a 24 hour slot. Any account that owns corresponding `LPTokens` can bid for the auction slot of that AMM instance. This is a continuous auction, any account can bid for the slot any time. Part of the proceeds from the auction, i.e. `LPTokens` are refunded to the current slot-holder computed on a pro rata basis. Remaining part of the proceeds - in the units of `LPTokens`- is burnt, thus effectively increasing the LPs shares.

### 4.1. Mechanics

The bid price to purchase the slot must adjust dynamically to function as an auction. If the slot is full, i.e. if an account owns the auction slot, the following should hold:

- the price should drop as the slot gets older.
- one must pay more (per unit time) than the value at which the slot was bought.
- the previous slot holder may lose their slot, in which case they receive a pro-rata refund (for their remaining time) and the rest goes to the pool (LPs).

The complex mechanism is how the price to buy the slot should drop as the occupied slot gets older. We introduce the slot price-schedule algorithm to answer the following questions:

1. How is the additional price one must pay per unit time to replace the holder of an existing slot determined?
2. How is the additional amount shared between the pool and the account losing its slot?
3. What is the amount per unit time for a slot when the slot is empty?

#### 4.1.1. Slot pricing

The minimum price to buy a slot for 24-hour period is called `MinSlotPrice` (`M`). Total slot time of 24-hours is divided into 20 equal intervals. An auction slot can be in one of the following states at any given time:

1. **Empty** - no account currently holds the slot.

2. **Occupied** - an account owns the slot with at least 5% of the remaining slot time (i.e. in one of the 1-19 intervals).

3. **Tailing** - an account owns the slot with less than 5% of the remaining time (i.e, in the last interval).

The slot-holder owns the slot privileges when in State 2 or 3.

#### Slot pricing scheduling algorithm

I. Slot state - **Empty** or **Tailing**, then

Slot Price = `M`

II. Slot state - **Occupied**, then

Let the price at which the slot is bought be `B` - specified in `Amount` of `LPTokens`. Let `t` represent the fraction of used slot time for the current slot-holder. Note that for each interval `t` has a discrete value (0.05, 0.1, , ..., 1). Let `M` represent the minimum slot price.

| Interval | `t`  |
| :------- | :--: |
| (0,1]    | 0.05 |
| (1,2]    | 0.1  |
| (19, 20] |  1   |

The algorithm to compute the minimum bid price of the slot at any given time enforces the following rules:

1. The minimum bid price of the slot in the first interval is, i.e. for `t` = 0.05:

$$ f(t) = B \* 1.05 + M $$

1.  The slot price decays exponentially over time. For the price to decay very very slowly for most of the time intervals (~95%) and instantly drop to the **MinSlotPrice** as the slot gets closer to the expiration time (~5%), we choose a heuristic function that produces this behavior. The following equation determines the minimum bid price of the slot for $t \in [0.1, 1]$ :

$$ f(t) = B _ 1.05_(1-t^{60}) + M $$

Notice that the slot price approaches `M` as the slot approaches expiration (i.e., as `t` approaches 1).

1. The revenue from a successful `AMMBid` transaction is split between the current slot-holder and the pool. We propose to _always_ refund the current slot-holder of the remaining value of the slot computed from the price at which they bought the slot.
   $$ f(t) = (1-t)\*B $$

The remaining `LPTokens` are burnt/deleted, effectively increasing the LPs share in the pool.

4. Let `X` represent the minimum bid price computed by the price-scheduling algorithm, then,
   - If (`MinBidPrice` && `MaxBidPrice`):
     - return
     - If (`MinBidPrice`):m
       - if (`MinBidPrice` <= `X`): return `X`
       - else: return `MinBidPrice`
   - elif (`MaxBidPrice`):
     - if (`MaxBidPrice`>= `X`): return `X`
       - else: return `MaxBidPrice`

We implement the following as the **MinSlotPrice**:
$$M = LPTokens * \frac{tradingFee}{25}$$

#### 4.1.2. `AuctionSlot` field

We introduce a new object field `AuctionSlot` in the **`AMM`** object associated with each AMM instance. The `AuctionSlot` field has the following subfields:

| Field Name |     Required?      | JSON Type | Internal Type |
| ---------- | :----------------: | :-------: | :-----------: |
| `Account`  | :heavy_check_mark: | `string`  |  `AccountID`  |

`Account` represents the XRPL account that currently owns the auction slot.

---

| Field Name   |     Required?      | JSON Type | Internal Type |
| ------------ | :----------------: | :-------: | :-----------: |
| `Expiration` | :heavy_check_mark: | `string`  |   `UINT32`    |

`Expiration` represents the number of seconds since the [Ripple Epoch](https://xrpl.org/basic-data-types.html#specifying-time). This marks the end of the time from when slot was bought.

---

| Field Name      |     Required?      | JSON Type | Internal Type |
| --------------- | :----------------: | :-------: | :-----------: |
| `DiscountedFee` | :heavy_check_mark: | `string`  |   `UINT32`    |

`DiscountedFee` represents the `TradingFee` to be charged to this account for trading against the AMM instance. By default it is `TradingFee`/10.

---

| Field Name |     Required?      | JSON Type | Internal Type |
| ---------- | :----------------: | :-------: | :-----------: |
| `Price`    | :heavy_check_mark: | `string`  |   `AMOUNT`    |

`Price` represents the price paid for the slot specified in units of `LPTokens` of the AMM instance.

---

| Field Name     | Required? | JSON Type | Internal Type |
| -------------- | :-------: | :-------: | :-----------: |
| `AuthAccounts` |           |  `array`  |    `Array`    |

`AuthAccounts` represents an array of XRPL account IDs that are authorized to trade at the discounted fee against the AMM instance. The proposal allows for up to a maximum of four accounts.

---

#### 4.1.3. **`AMMBid`** transaction

We introduce a new transaction **`AMMBid`** to place a bid for the auction slot. The transaction may have the following optional and required fields:

| Field Name |     Required?      | JSON Type | Internal Type |
| ---------- | :----------------: | :-------: | :-----------: |
| `Account`  | :heavy_check_mark: | `string`  |  `AccountID`  |

`Account` represents the XRPL account that submits the transaction.

---

| Field Name        |     Required?      | JSON Type | Internal Type |
| ----------------- | :----------------: | :-------: | :-----------: |
| `TransactionType` | :heavy_check_mark: | `string`  |   `UINT16`    |

`TransactionType` specifies the new transaction type **`AMMBid`**. The integer value is 39.

---

| Field Name |     Required?      | JSON Type | Internal Type |
| ---------- | :----------------: | :-------: | :-----------: |
| `Asset`    | :heavy_check_mark: | `object`  |    `ISSUE`    |

`Asset` specifies one of the assets of the AMM instance against which the transaction is to be executed.

---

| Field Name |     Required?      | JSON Type | Internal Type |
| ---------- | :----------------: | :-------: | :-----------: |
| `Asset2`   | :heavy_check_mark: | `object`  |    `ISSUE`    |

`Asset2` specifies the other asset of the AMM instance against which the transaction is to be executed.

---

| Field Name    | Required? | JSON Type |  Internal Type  |
| ------------- | :-------: | :-------: | :-------------: |
| `MinBidPrice` |           | `string`  | `STRING NUMBER` |

`MinBidPrice` represents the minimum price that the bidder wants to pay for the slot. It is specified in units of `LPTokens`. This is not a required field. If specified let `MinBidPrice` be `X` and let the slot-price computed by price scheduling algorithm be `Y`, then bidder always pays the max(X, Y).

---

| Field Name     | Required? | JSON Type | Internal Type |
| -------------- | :-------: | :-------: | :-----------: |
| `AuthAccounts` |           |  `array`  |    `Array`    |

`AuthAccounts` represents an array of XRPL account IDs that are authorized to trade at the discounted fee against the AMM instance. The proposal allows for up to a maximum of four accounts.

---

| Field Name    | Required? | JSON Type |  Internal Type  |
| ------------- | :-------: | :-------: | :-------------: |
| `MaxBidPrice` |           | `string`  | `STRING NUMBER` |

`MaxBidPrice` represents the maximum price that the bidder wants to pay for the slot. It is specified in units of `LPTokens`. This is not a required field. If specified let `MaxBidPrice` be `X` and let the slot-price computed by price scheduling algorithm be `Y`, then bidder always pays the min(X, Y).

---

## Appendices

### Appendix A. Specifying different parameters for **`AMMDeposit`** transaction

The proposal allows for traders to specify different combinations of the fields for **`AMMDeposit`** transaction. The implementation will figure out the best possible sub operations based on trader's specifications. Here are the recommended valid combinations. Other invalid combinations may result in the failure of transaction.

- `LPTokenOut`, `[Amount]`, `[Amount2]`
- `Amount`, `[LPTokenOut]`
- `Amount` , `Amount2`, `[LPTokenOut]`
- `Amount` and `LPTokenOut`
- `Amount` and `EPrice`
- `Amount` , `Amount2`, `[TradingFee]`

Implementation details for above combinations:

1. Fields specified: `LPTokenOut`, `[Amount]`, `[Amount2]`

Such a transaction assumes proportional deposit of pools assets in exchange for the specified amount of `LPTokenOut` of the AMM instance.

- Use equations 1 & 2 to compute the amount of each asset to be deposited, given the amount of $\Delta_{LPTokenOut}$ specified as `LPTokenOut`

If the account that initiated the transaction holds sufficient balances, the transaction is successful. It fails otherwise with an error code.

Similarly, if `[Amount]`, `[Amount2]` are specified and the amount of either asset computed above is less than the amounts specified in these fields, then the transaction fails.

2. Fields specified: `Amount`, `[LPTokenOut]`

Such a transaction assumes single asset deposit of the amount of asset specified by `Amount`. This is essentially an _equal_ asset deposit and a _swap_.

- Check if the account that initiated the transaction holds the amount of `Amount`.
- If not, the transaction fails with an error code. Otherwise,
  - Use equation 3 to compute amount of `LPTokenOut` ~ $\Delta_{LPTokenOut}$ to be issued, given either the amount of drops of `XRP` or the amount of tokens in `Amount`.

If the asset to be deposited is a token, specifying the `value` field is required, else the transaction will fail.

If `LPTokenOut` field exists, and the amount of `LPTokenOut` computed above is less than the that specified in this field, then the transaction fails.

3. Fields specified: `Amount`, `Amount2` and `[LPTokenOut]`

Such a transaction assumes proportional deposit of pool assets with the constraints on the maximum amount of each asset that the trader is willing to deposit.

- Use equation 1 to compute the amount of $\Delta_{LPTokenOut}$, given the amount in `Amount`. Let this be `Z`
- Use equation 2 to compute the amount of asset2, given $\Delta_{LPTokenOut}$ ~ `Z`. Let the computed amount of asset2 be `X`.
  - If `X` <= amount in `Amount2`:
    - The amount of asset1 to be deposited is the one specified in `Amount`
    - The amount of asset2 to be deposited is `X`
    - The amount of `LPTokenOut` to be issued is `Z`
  - If X > amount in `Amount2`:
    - Use equation 2 to compute $\Delta_{LPTokenOut}$, given the amount in `Amount2`. Let this be `W`
    - Use equation 1 to compute the amount of asset1, given $\Delta_{LPTokenOut}$ ~ `W` from above. Let the computed amount of asset1 be `Y`
    - If `Y` <= amount in `Amount`:
      - The amount of asset1 to be deposited is `Y`
      - The amount of asset2 to be deposited is the one specified in `Amount2`
      - The amount of `LPTokenOut` to be issued is `W`

else, failed transaction.

If `LPTokenOut` field exists, and the amount of `LPTokenOut` computed above is less than the that specified in this field, then the transaction fails.

4. Fields specified: `Amount` and `LPTokenOut`

Such a transaction assumes that a single asset `asset1` is deposited to obtain some share of the AMM instance's pools represented by amount in `LPTokenOut`. Since adding liquidity to the pool with one asset changes the ratio of the assets in the two pools, thus changing the relative pricing, trading fee is charged on the amount of the deposited asset that causes this change.

- Check if the account that initiated the transaction holds the amount of `Amount`.
- If not, the transaction fails with an error code. Otherwise,
  - Use equation 4 to compute the amount of asset1 to be deposited, given $\Delta_{LPTokenOut}$ represented by amount of `LPTokenOut`

5. Fields specified: `Amount` and `EPrice`

Such a transaction assumes single asset deposit with the following two constraints:

a. amount of asset1 if specified in `Amount` specifies the maximum amount of asset1 that the trader is willing to deposit

b. The effective-price of the `LPToken` traded out does not exceed the specified `EPrice`

- Use equation 3 to compute the amount of `LPTokenOut` out, given the amount of `Amount`. Let this be `X`
- Use equation `III` to compute the effective-price of the trade given `Amount` amount as the asset in and the `LPTokens` amount ~ `X` as asset out. Let this be `Y`.
- If `Y` <= amount in `EPrice`:
  - The amount of asset1 to be deposited is given by amount in `Amount`
  - The amount of `LPTokenOut` to be issued is `X`
- If (`Y`>`EPrice`) OR (amount in `Amount` does not exist):
  - Use equations 3 & `III` and the given `EPrice` to compute the following two variables:
    - The amount of asset1 in. Let this be `Q`
    - The amount of `LPTokenOut` out. Let this be `W`
  - The amount of asset1 to be deposited is `Q`
  - The amount of `LPTokenOut` to be issued is `W`

Following updates after a successful **`AMMDeposit`** transaction:

- The deposited asset, if XRP, is transferred from account that initiated the transaction to AMM instance account, thus changing the `Balance` field of each account
- The deposited asset, if token, are balanced between the AMM account and the issuer account trustline.
- The `LPTokenOut` are issued by the AMM instance account to the account that initiated the transaction and a new trustline is created, if there does not exist one.
- The pool composition is updated. Note that the conservation function is not preserved in case of liquidity provision (and is not expected to.)

### Appendix B. Specifying different parameters for **`AMMWithdraw`** transaction

The proposal allows for traders to specify different combinations of the above mentioned fields for **`AMMWithdraw`** transaction. The implementation will figure out the best possible operations based on trader's specifications. Here are the recommended possible combinations. Other invalid combinations may result in the failure of transaction.

- `LPTokenIn`
- `Amount`
- `Amount` and `Amount2`
- `Amount` and `LPTokenIn`
- `Amount` and `EPrice`

Implementation details for the above combinations:

1. Fields specified: `LPTokenIn`

Such a transaction assumes proportional withdrawal of pool assets for the amount of `LPTokenIn`. Since withdrawing assets proportionally from the AMM instance pools does not change the ratio of the two assets in the pool and thus does not affect the relative pricing, trading fee is not charged on such a transaction.

- Check if the account that initiated the transaction holds the amount of `LPTokenIn`.
- If not, the transaction fails with an error code. Otherwise,
  - Use equations 5 & 6 to compute the amount of both the assets in the AMM instance pool, given the redeemed $\Delta_{LPTokenIn}$ represented by `LPTokenIn`

2. Fields specified: `Amount`

Such a transaction assumes withdrawal of single asset equivalent to the amount specified in `Amount`

- Use equation 7 to compute the $\Delta_{LPTokenIn}$, given the amount in `Amount`.

If the account that submitted the transaction holds the amount of $\Delta_{LPTokenIn}$ computed above, then the transaction is successful. It fails otherwise.

3. Fields specified: `Amount` and `Amount2`

Such a transaction assumes all assets withdrawal with the constraints on the maximum amount of each asset that the trader is willing to withdraw.

- Use equation 5 to compute $\Delta_{LPTokenIn}$, given the amount in `Amount`. Let this be `Z`
- Use equation 6 to compute the amount of asset2, given $\Delta_{LPTokenIn}$ ~ `Z`. Let the computed amount of asset2 be `X`
- If `X` <= amount in `Amount2`:
  - The amount of asset1 to be withdrawn is the one specified in `Amount`
  - The amount of asset2 to be withdrawn is `X`
  - The amount of `LPTokenIn` redeemed is `Z`
- If `X`> amount in `Amount2`:
  - Use equation 5 to compute $\Delta_{LPTokenIn}$, given the amount in `Amount2`. Let this be `Q`
  - Use equation 6 to compute the amount of asset1, given $\Delta_{LPTokenIn}$ ~ `Q`. Let the computed amount of asset1 be `W`
  - The amount of asset2 to be withdrawn is the one specified in `Amount2`
  - The amount of asset1 to be withdrawn is `W`
  - The amount of `LPTokenIn` redeemed is `Q`

The transaction MUST fail if the account initiating the transaction does not hold the amount of `LPTokenIn` computed above.

4. Fields specified: `Amount` and `LPTokenIn`

Such a transaction assumes withdrawal of single asset specified in `Amount` proportional to the share represented by the amount of `LPTokenIn`. Since a single sided withdrawal changes the ratio of the two assets in the AMM instance pools, thus changing their relative pricing, trading fee is charged on the amount of asset1 that causes that change.

- Check if the account that initiated the transaction holds the amount of `LPTokenIn`.
- If not, the transaction fails with an error code. Otherwise,
  - Use equation 8 to compute the amount of asset1, given the redeemed $\Delta_{LPTokenIn}$ represented by `LPTokenIn`. Let this be `Y`.
  - If (amount exists for `Amount` & `Y` >= amount in `Amount`) || (amount field does not exist for `Amount`):
    - The amount of asset out is `Y`
    - The amount of `LPTokens` redeemed is `LPTokenIn`

else transaction fails.

5. Fields specified: `Amount` and `EPrice`

<Note to self: This is like saying I dont want to pay more than EPrice for AssetOut>

Such a transaction assumes withdrawal of single asset with the following constraints:

a. amount of asset1 if specified in `Amount` specifies the minimum amount of asset1 that the trader is willing to withdraw

b. The effective price of asset traded out does not exceed the amount specified in `EPrice`

- Use equations 8 & `III` and amount in `EPrice`to compute the two variables, i.e.,
  - asset in as `LPTokenIn`. Let this be `X`
  - asset out as that in `Amount`. Let this be `Y`
- If (amount exists for `Amount` & `Y` >= amount in `Amount`) || (amount field does not exist for `Amount`):
  - The amount of assetOut is given by `Y`
  - The amount of LPTokens is given by `X`

else transaction fails.

Following updates after a successful **`AMMWithdraw`** transaction:

- The withdrawn asset, if XRP, is transferred from AMM instance account to the account that initiated the transaction, thus changing the `Balance` field of each account
- The withdrawn asset, if token, is balanced between the AMM instance account and the issuer account.
- The `LPTokens` ~ $\Delta_{LPTokenIn}$ are balanced between the AMM instance account and the account that initiated the transaction.
- The pool composition is updated. Conservation function is not preserved in case of liquidity withdrawal (and is not expected to.)

## Implementation

The reference implementation of this spec can be found in `rippled`:

- https://github.com/XRPLF/rippled/pull/4294
- https://github.com/XRPLF/rippled/pull/4626
- https://github.com/XRPLF/rippled/pull/4674
- https://github.com/XRPLF/rippled/pull/4682
