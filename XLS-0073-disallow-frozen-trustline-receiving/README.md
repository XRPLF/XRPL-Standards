<pre>
Title:       <b>XLS-73d Inbound-Freeze Trustlines</b>
Type:        <b>draft</b>
Revision:    <b>1</b> (2024-08-12)
Author:      <a href="mailto:shawnxie@ripple.com">Shawn Xie</a>
Affiliation: <a href="https://ripple.com">Ripple</a>
</pre>

#  Inbound-Freeze Trustlines

## Abstract

This amendment empowers token issuers on the XRP Ledger to prevent token misuse by frozen account holders. The document outlines enhancements to the interactions between frozen assets and payments, ensuring that frozen token holders cannot receive funds until or unless their trustline is unfrozen. These changes will significantly improve use cases such as stablecoins and real world assets (RWA), where ensuring regulatory compliance is essential.

## 1. Overview
This proposal introduces a new inbound-freeze feature for the trustlines that interacts with payment, offers, DEX and AMM. In essence, issuers can block receiving of funds for holders who have been inbound-frozen. 


## 2. Specification
### 2.1. Inbound-Freeze Mechanism
The Inbound-Freeze feature is a setting on a trust line. When an issuer enables the Inbound-Freeze setting, the following rules apply to the tokens in that trust line:
- The counterparty of that trust line can no longer increase their balance on the trust line, except in direct payments from the issuer.
- The counterparty can still send payments to others on the inbound-frozen trustline
- The counterparty's offers to buy the tokens in the inbound-frozen trustline are considered __unfunded__
#### 2.1.1. `RippleState` Object
Two new flags `lsfLowInboundFreeze` and `lsfHighInboundFreeze` are introduced in the `RippleState` (trustline) object.


> | Flag Name                  | Flag Value  | Description |
>|:---------------------------:|:-----------:|:------------|
>| `lsfLowInboundFreeze`                | `0x02000000`| The low account has inbound-frozen the trust line, preventing the high account from receiving the asset. |
>| `lsfHighInboundFreeze`                 | `0x04000000`| The high account has inbound-frozen the trust line, preventing the low account from receiving the asset. |

#### 2.1.2. `TrustSet` Transaction
Two new flags `tfSetInboundFreeze` and `tfClearInboundFreeze` are introduced in the `TrustSet` transaction.

> | Flag Name                  | Flag Value  | Description |
>|:---------------------------:|:-----------:|:------------|
>| `tfSetInboundFreeze`                | `0x00400000`| Inbound freeze the trust line. |
>| `tfClearInboundFreeze`                 | `0x00800000`| Inbound unfreeze the trustline |


### 2.2. Payment Engine
Payment engine executes paths that is made of steps to connect the sender to the receiver. In general, funds can be deposited into a trustline through one of two steps:
* Rippling
* Order book or AMM

This proposal proposes changes to both steps above to ensure a inbound-frozen trustline _cannot_ increase its balance.

#### 2.2.1. Rippling
This proposal suggests an update: __any _inbound-frozen_ trustline can not increase its balance as a result of any transaction__. In other words, any receipt of funds in the inbound-frozen trustline will result in failure.

##### Example
Let's take a look at an example of how inbound-freeze impacts rippling:

```
+-------+           USD           +---------+           USD           +-------+
| Alice | ----------------------> | Gateway | ----------------------> |  Bob  |
+-------+                         +---------+ (Bob is inbound-frozen) +-------+
```

Consider the following scenario:

1. Issuer account issues USD to both Alice and Bob, each of which has a trustline.
2. Issuer inbound-freezes Bob's trustline.
3. Alice attempts to send a USD `Payment` to Bob. The transaction _fails_ because Bob's USD trustline has been inbound-frozen and can no longer receive funds.

#### 2.2.2. Order Book and AMM
In the payment engine, offers and AMM pools can be consumed in the path when a cross-currency payment is involved, resulting in a change to the trustline balance. This proposal introduces behavior changes to the order book and AMM steps when trustlines have been inbound-frozen.

##### 2.2.2.1. Order Book
This proposal introduces a change to the order book step: __if the offer owner has been inbound-frozen on the trustline of the `TakerPays` token, the offer is considered to be _unfunded_ and the step fails.__

###### Example
Let's take a look at an example where offer is involved in transfering the funds and compare how the result differs between the current and proposed behaviors.


```
                                                                 Bob's Offer
+-------+         USD            +---------+        USD       +--------------+      XRP     +-------+
| Alice | ---------------------> | Gateway | ---------------> | Sell: 100 XRP| -----------> | Carol |
+-------+     SendMax: 100 USD   +---------+                  +--------------+              +-------+
              Amount: 100 XRP                                 | Buy: 100 USD |       
                                                              +--------------+
                                                            (Bob is inbound-frozen)                             
```

Consider the following scenario:

1. Issuer account issues USD to both Alice and Bob, each of which has a trustline.
2. Issuer inbound-freezes Bob's trustline.
3. Alice attempts to send XRP to Carol through a `Payment` transaction using Bob's offer to exchange USD for XRP. Alice fails to send XRP to Carol because Bob's offer is unfunded due to the inbound-frozen trustline.

##### 2.2.2.2. AMM
This proposal introduces a change to the AMM step: __if the AMM account has been inbound-frozen by the issuer on the trustline of the token that its trying to swap in, the step fails.__

###### Example
Let's take a look at an example where an AMM pool is involved in transfering the funds:


```
                                                                 AMM Pool
+-------+         USD            +---------+        USD       +-----------+      XRP     +-------+
| Alice | ---------------------> | Gateway | ---------------> |  1000 XRP | -----------> | Carol |
+-------+     SendMax: 100 USD   +---------+                  +-----------+              +-------+
              Amount: 100 XRP                                 |  100 USD  |       
                                                              +-----------+
                                                            (AMM Account is 
                                                            inbound-frozen for USD)                             
```

Consider the following scenario:

1. Issuer account issues USD to both Alice and Bob, each of which has a trustline.
2. An AMM pool is created with XRP and USD
2. Issuer inbound-freezes AMM account's USD trustline.
3. Alice attempts to send XRP to Carol through a `Payment` transaction using the AMM Pool to exchange USD for XRP. The transaction fails because AMM account's USD trustline has been inbound-frozen and can no longer swap in USD.

### 2.3. `OfferCreate` transaction
This proposal introduces a new change to the `OfferCreate` transaction:
* `OfferCreate` returns `tecINBOUND_FROZEN` if the `TakerPays` (buy amount) token has been _inbound-frozen_ by the issuer

Moreover, any existing offers where the owner has been inbound-frozen on the `TakerPays` token __can no longer be consumed and will be considered as an _unfunded_ offer that will be implicitly cancelled by new Offers that cross it.__

### 2.4. `AMMWithdraw` transaction
This proposal introduces a new change to the `AMMWithdraw` transaction:
* `AMMWithdraw` returns `tecINBOUND_FROZEN` if the holder is inbound-frozen for either of the assets in the pool.


## 3. Invariants
One potential invariant could be disallowing any increase in the balance of an inbound-frozen trustline as a result of any type of transaction.






