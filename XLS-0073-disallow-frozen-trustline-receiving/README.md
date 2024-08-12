<pre>
Title:       <b>XLS-73d Disallow Receiving on Frozen Trustlines</b>
Type:        <b>draft</b>
Revision:    <b>1</b> (2024-07-29)
Author:      <a href="mailto:shawnxie@ripple.com">Shawn Xie</a>
Affiliation: <a href="https://ripple.com">Ripple</a>
</pre>

#  Disallow Receiving on Frozen Trustlines

## Abstract

This amendment empowers token issuers on the XRP Ledger to prevent token misuse by frozen account holders. The document outlines enhancements to the interactions between frozen assets and payments, ensuring that frozen token holders cannot receive funds until or unless their trustline is unfrozen. These changes will significantly improve use cases such as stablecoins and real world assets (RWA), where ensuring regulatory compliance is essential.

## 1. Overview
This proposal introduces new trustline flag,`lsfInboundFrozen`,  that interacts with payment, offers, DEX and AMM. In essence, issuers can block receiving of funds for holders who have been frozen inbound. **This is a breaking change.**


## 2. Specification
### 2.1. Inbound freeze mechanism
The Inbound Freeze feature is a setting on a trust line. When an issuer enables the Inbound Freeze setting, the following rules apply to the tokens in that trust line:
- The counterparty of that trust line can no longer increase its balance on the trust line, except in direct payments from the issuer.
- The counterparty can still send payments to others on the inbound frozen trustline
- The counterparty's offers to buy the tokens in the inbound frozen trustline are considered __unfunded__
#### 2.1.1. `RippleState` object
Two new flags lsfLowInboundFreeze and lsfHighInboundFreeze are introduced in the `RippleState` (trustline) object.
### 2.1. Payment Engine
Payment engine executes paths that is made of steps to connect the sender to the receiver. In general, funds can be deposited into a frozen trustline through one of two steps:
* Rippling
* Order book or AMM

This proposal proposes changes to both steps above to ensure a frozen trustline _cannot_ increase its balance.

#### 2.1.1. Rippling
In the current behavior, after the issuer freezes a trustline by setting `lsfHighFreeze`/`lsfLowFreeze` on the trustline (individual freeze) or `lsfGlobalFreeze` on the account (global freeze), the trustline cannot decrease its balance but can still increase its balance (allowing the receipt of funds). This proposal suggests a change to the behavior: __any frozen trustline can no longer increase its balance as a result of any transaction__. In other words, any receipt of funds in the frozen trustline will result in failure.

##### 2.1.1.1. Example
Let's take a look at an example where rippling is involved in transfering the funds and compare how the result differs between the current and proposed behaviors.

```
+-------+           USD           +---------+           USD           +-------+
| Alice | ----------------------> | Gateway | ----------------------> |  Bob  |
+-------+                         +---------+      (Bob is frozen)    +-------+
```

Consider the following scenario:

1. Issuer account issues USD to both Alice and Bob, each of which has a trustline.
2. Issuer individually freezes Bob's trustline.
3. Alice attempts to send a USD `Payment` transaction to Bob, who's frozen. In the current behavior, Alice will be able to successfully send funds to Bob.

This proposal suggests changing the behavior at __Step 3__ to 

> Alice attempts to send a USD `Payment` to Bob, who's frozen. The `Payment` transaction _fails_ because Bob's USD trustline has been frozen and can no longer receive funds.


#### 2.1.2. Order Book and AMM
In the payment engine, offers and AMM pools can be consumed in the path when cross-currency payment is involved, it will result in change of trustline balance. This proposal introduces behavior changes to how offers work, as they currently allow the receipt of funds on a frozen trustline. However, no changes are introduced for the AMM pool, as the AMM account already denies the receipt of funds if its trustlines are frozen by the issuer of the assets.

##### 2.1.2.1. Order Book
Currently, consumption of offers is allowed even if the buy amount (`TakerPays`) has been individually frozen. This proposal introduces a new change: __if the offer owner has been individually frozen on the trustline of `TakerPays` currency, the offer is considered to be _unfunded_ and therefore the step fails .__
##### 2.1.2.1.1. Example
Let's take a look at an example where offer is involved in transfering the funds and compare how the result differs between the current and proposed behaviors.


```
                                                                 Bob's Offer
+-------+         USD            +---------+        USD       +--------------+      XRP     +-------+
| Alice | ---------------------> | Gateway | ---------------> | Sell: 100 XRP| -----------> | Carol |
+-------+     SendMax: 100 USD   +---------+                  +--------------+              +-------+
              Amount: 100 XRP                                 | Buy: 100 USD |       
                                                              +--------------+
                                                               (Bob is frozen)                             
```

Consider the following scenario:

1. Issuer account issues USD to both Alice and Bob, each of which has a trustline.
2. Issuer individually freezes Bob's trustline.
3. Alice attempts to send XRP to Carol through a `Payment` transaction using Bob's offer to exchange USD for XRP. In the current behavior, Alice will be able to successfully send 100 XRP to Carol, and Bob receives 100 USD.

This proposal suggests changing the behavior at  __Step 3__ to 

> Alice attempts to send XRP to Carol through a `Payment` transaction using Bob's offer to exchange USD for XRP. Alice fails to send XRP to Carol because Bob's offer is unfunded due to the frozen trustline.

### 2.2. `OfferCreate` transaction
This proposal introduces a new change to the `OfferCreate` transaction. Currently, if the holder has been frozen, they are still allowed to submit a `OfferCreate` transaction that specifies `TakerPays` as the frozen token, allowing them to receive more funds despite already being frozen by the issuer. We propose the following change:
* `OfferCreate` returns `tecFROZEN` if the currency of `TakerPays` has been frozen by the issuer (either individually or globally)

Moreover, any existing offers with `TakerPays` currency frozen __can no longer be consumed and will be considered as an _unfunded_ offer that will be implicitly cancelled by new Offers that cross it.__

## 3. Invariants
One potential invariant could be disallowing any increase in the balance of a frozen trustline as a result of any type of transaction.






