<pre>
Title:       <b>Disallow Receiving on Frozen Trustline</b>
Type:        <b>draft</b>

Author:      <a href="mailto:shawnxie@ripple.com">Shawn Xie</a>
Affiliation: <a href="https://ripple.com">Ripple</a>
</pre>

#  Disallow Receiving on Frozen Trustline

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
| Alice | ----------------------> | Issuer | <---------------------- |  Bob  |
+-------+                         +--------+    Issuer freezes Bob   +-------+

```

Consider the following scenario:

1. Issuer accounts issues USD to both Alice and Bob, each of which has a trustline
2. Issuer individually freezes Bob by setting lsfHighFreeze/lsfLowFreeze on Bob's trustline
3. Alice attempts to send a USD `Payment` transaction to Bob, who's frozen. In the existing behavior, Alice will be able to successfully send funds to Bob.

In this proposal, it suggests to change the behavior at __Step 3__ to 

> Alice attempts to send a USD `Payment` to Bob, who's frozen. The `Payment` transaction _fails_ because Bob's USD trustline has been frozen and can no longer receive funds.


#### 2.1.2. Order Book and AMM
In the payment engine, offers and AMM pools can be consumed in the path when cross-currency exchange is involved, it will result in change of trustline balance. Currently, offers are allowed to be consumed despite the 


### 2.2. `OfferCreate` transaction
This proposal proposes a new change to OfferCreate transaction. Currently, if the holder has been frozen, they are still allowed to submit a OfferCreate transaction that specifies `TakerPays` to be the frozen token, allowing them to receive more funds despite already being frozen by the issuer. We propose the following change:
* `OfferCreate` returns `tecUNFUNDED_OFFER` if the currency of `TakerPays` has been frozen by the issuer (either individually or globally)







