<pre>
Title:       <b>Disallow Receiving on Frozen Trustlines</b>
Type:        <b>draft</b>

Author:      <a href="mailto:shawnxie@ripple.com">Shawn Xie</a>
Affiliation: <a href="https://ripple.com">Ripple</a>
</pre>

#  Disallow Receiving on Frozen Trustlines

## Abstract

This amendment empowers token issuers on the XRP Ledger to regulate tokens in an effort to prevent misuse by blacklisted accounts. This document proposes enhancements to the interactions between frozen assets and payment. This proposal will ensure that blacklisted token holders can no longer receive funds, which will significantly improve use cases such as stablecoins, where ensuring regulatory compliance is essential.

## 1. Overview
This proposal introduces new improvements on how frozen trustlines interacts with payment, offers, DEX and AMM. In essence, trustlines, that have been frozen (either individually or globally), should not be able to receive funds in any way.


## 2. Specification
### 2.1. Payment Engine
Payment engine executes paths that is made of steps to connect the sender to the receiver. In general, funds can be deposited into a frozen trustline through one of the two steps:
* Rippling
* Order book or AMM

This proposal proposes changes to both steps above to ensure a frozen trustline _cannot_ increase its balance.

#### 2.1.1. Rippling
In the current behavior, after the issuer freezes a trustline by setting lsfHighFreeze/lsfLowFreeze on the trustline (individual freeze) or lsfGlobalFreeze on the account (global freeze), the trustline cannot decrease its balance but can still increase its balance (allowing the receipt of funds). This proposal suggests a change to the behavior: __any frozen trustline can no longer increase its balance as a result of any transaction__. In other words, any receipt of funds in the frozen trustline will result in failure.

##### 2.1.1.1. Example
Let's take a look at an example where rippling is involved in transfering the funds and compare how the result differs between the current and proposed behaviors.

```
+-------+           USD           +--------+           USD           +-------+
| Alice | ----------------------> | Issuer | ----------------------> |  Bob  |
+-------+                         +--------+      (Bob is frozen)    +-------+

```

Consider the following scenario:

1. Issuer accounts issues USD to both Alice and Bob, each of which has a trustline.
2. Issuer individually freezes Bob's trustline.
3. Alice attempts to send a USD `Payment` transaction to Bob, who's frozen. In the existing behavior, Alice will be able to successfully send funds to Bob.

In this proposal, it suggests to change the behavior at __Step 3__ to 

> Alice attempts to send a USD `Payment` to Bob, who's frozen. The `Payment` transaction _fails_ because Bob's USD trustline has been frozen and can no longer receive funds.


#### 2.1.2. Order Book and AMM
In the payment engine, offers and AMM pools can be consumed in the path when cross-currency exchange is involved, it will result in change of trustline balance. 
##### 2.1.2.1. Order Book
Currently, consumption of offers is allowed even if the offer owner has been individually frozen on the trustline of the buy amount (`TakerPays`). This proposal introduces a new change: __if the offer owner has been individually frozen on the trustline of `TakerPays`, the payment path fails and the offer becomes _unfunded_.__
##### 2.1.2.1.1. Example
Let's take a look at an example where offer is involved in transfering the funds and compare how the result differs between the current and proposed behaviors.


```

                                     Bob's Offer
+-------+         USD             +--------------+          XRP            +-------+
| Alice | ----------------------> | Sell: 100 XRP| ----------------------> | Carol |
+-------+     SendMax: 100 USD    +--------------+                         +-------+
              Amount: 100 XRP     | Buy: 100 USD |       
                                  +--------------+
                                   (Bob is frozen)                             

```

Consider the following scenario:

1. Issuer accounts issues USD to both Alice and Bob, each of which has a trustline.
2. Issuer individually freezes Bob's trustline.
3. Alice attempts to send a XRP to Carol through a `Payment` transaction using Bob's offer to exchange USD for XRP. In the existing behavior, Alice will be able to successfully send 100 XRP to Carol, and Bob receives 100 USD.

In this proposal, it suggests to change the behavior at __Step 3__ to 

> 3. Alice attempts to send a XRP to Carol through a `Payment` transaction using Bob's offer to exchange USD for XRP. Alice fails to send XRP to Carol because Bob's offer is unfunded due to the frozen trustline.


##### 2.1.2.2. AMM
Similarly, an AMM step can increase the trustline balance of a token holder despite they've been individually frozen. This proposal introduces a new change: __a payment path fails if the token, that is swapped out, results in the increase of balance of a frozen trustline__

##### 2.1.2.2.1. Example
Let's take a look at an example where AMM is involved in transfering the funds and compare how the result differs between the current and proposed behaviors.

```

                                     AMM Pool
+-------+        XRP              +------------+          USD            +-------+
| Alice | ----------------------> | 100 XRP    | ----------------------> |  Bob  |
+-------+     SendMax: 100 XRP    +------------+     (Bob is frozen)     +-------+
              Amount: 100 USD     | 10000 USD  |       
                                  +------------+
                                                                 

```

Consider the following scenario:

1. Issuer accounts issues USD to Bob, who has a trustline.
2. An AMM pool is created with USD and XRP assets and assume the pool has a quality good enough to provide XRP to USD swaps.
3. Alice attempts to send a cross-currency `Payment` transaction to Bob, who's frozen. In the existing behavior, Alice will be able to successfully send USD to Bob through the AMM pool by swapping XRP for USD.

In this proposal, it suggests to change the behavior at __Step 3__ to 

> Alice attempts to send a cross-currency `Payment` transaction to Bob, who's frozen. Alice _fails_ to send USD to Bob through the AMM pool because Bob has been individually frozen.

### 2.2. `OfferCreate` transaction
This proposal introduces a new change to the OfferCreate transaction. Currently, if the holder has been frozen, they are still allowed to submit a OfferCreate transaction that specifies `TakerPays` to be the frozen token, allowing them to receive more funds despite already being frozen by the issuer. We propose the following change:
* `OfferCreate` returns `tecUNFUNDED_OFFER` if the currency of `TakerPays` has been frozen by the issuer (either individually or globally)

### 2.3. `AMMDeposit` transaction
This proposal introduces a new change to the AMMDeposit transaction. Currently, `AMMDeposit` would allow an account to deposit tokens into the pool regardless whether the account's tokens are frozen.
This proposal introduces the following:
* `AMMDeposit` fails if one of the tokens has been frozen (either indivually or globally) by the issuer (for both single-sided and double-sided deposits).





