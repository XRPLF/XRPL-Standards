<pre>
  xls: 77
  title: Deep Freeze
  description: Enhancement to prevent token misuse by frozen account holders and improve regulatory compliance
  author: Shawn Xie <shawnxie@ripple.com>
  proposal-from: https://github.com/XRPLF/XRPL-Standards/discussions/220
  status: Final
  category: Amendment
  created: 2024-07-08
</pre>

# Deep-freeze

## Abstract

This amendment empowers token issuers on the XRP Ledger to prevent token misuse by frozen account holders. The document outlines enhancements to the interactions between frozen assets and payments, ensuring that frozen token holders cannot receive funds until or unless their trustline is unfrozen. These changes will enable token issuers to more easily comply with regulations on the XRPL. For example, prevent tokens from flowing to wallets identified on sanctions lists, thereby enhancing regulatory compliance for use cases such as regulated stablecoins and real-world assets (RWA).

## 1. Overview

This proposal introduces a new deep-freeze feature for the trustlines that interacts with payment, offers, DEX and AMM. In essence, issuers can block sending and receiving of funds for holders who have been deep-frozen.

## 2. Specification

### 2.1. Deep-freeze Mechanism

The Deep-freeze feature is a setting on a trust line and _requires that the issuer must have "regularly frozen" the trust line before they can enact a deep-freeze_. The issuer cannot enact a deep-freeze if they have enabled No Freeze on their account.

When an issuer enacts Deep-freeze, the following rules apply to the tokens in that trust line:

- Payments can still occur directly between the two parties of the deep-frozen trust line.
- The counterparty of that trust line can _no longer increase or decrease_ its balance on the deep-frozen trust line, except in direct payments to the issuer. The counterparty can only send the deep-frozen currencies directly to the issuer.
- The counterparty can neither send nor receive from others on the deep-frozen trustline
- The counterparty's offers to buy or sell the tokens in the deep-frozen trustline are considered **unfunded**

An individual address can deep-freeze its trust line to an issuer or financial institution. This has no effect on transactions between the institution and other users. However it does the following:

- It prevents other addresses from sending that financial institution's tokens to the individual address.
- It also prevents the individual address from sending the token to other non-issuer addresses.

#### 2.1.1. `RippleState` Object

Two new flags `lsfLowDeepFreeze` and `lsfHighDeepFreeze` are introduced in the `RippleState` (trustline) object.

> |      Flag Name      |  Flag Value  | Description                                                                                                       |
> | :-----------------: | :----------: | :---------------------------------------------------------------------------------------------------------------- |
> | `lsfLowDeepFreeze`  | `0x02000000` | The low account has deep-frozen the trust line, preventing the high account from sending and receiving the asset. |
> | `lsfHighDeepFreeze` | `0x04000000` | The high account has deep-frozen the trust line, preventing the low account from sending and receiving the asset. |

#### 2.1.2. `TrustSet` Transaction

Two new flags `tfSetDeepFreeze` and `tfClearDeepFreeze` are introduced in the `TrustSet` transaction.

> |      Flag Name      |  Flag Value  | Description                              |
> | :-----------------: | :----------: | :--------------------------------------- |
> |  `tfSetDeepFreeze`  | `0x00400000` | Deep freeze the trust line.              |
> | `tfClearDeepFreeze` | `0x00800000` | Clear the deep-freeze on the trust line. |

The `TrustSet` transaction trying to set `tfSetDeepFreeze` will succeed if and only if one of the following is true:

- The holder is already frozen, indicated by `lsfLowFreeze`/`lsfHighFreeze` on the trust line.
- `tfSetFreeze` is also set in the same `TrustSet` transaction.

The `TrustSet` also introduces an additional restriction:

- If the trust line is deep-frozen by the issuer (indicated by `lsfLowDeepFreeze`/`lsfHighDeepFreeze`), the `TrustSet` transaction fails if the issuer sets the `tfClearFreeze` flag without also setting the `tfClearDeepFreeze` flag. In other words, the issuer cannot clear the regular freeze on a trust line unless they also clear the deep-freeze.

### 2.2. Payment Engine

Payment engine executes paths that is made of steps to connect the sender to the receiver. In general, funds can be deposited into a trustline through one of two steps:

- Rippling
- Order book or AMM

This proposal proposes changes to both steps above to ensure a deep-frozen trustline _cannot_ increase its balance.

#### 2.2.1. Rippling

This proposal suggests an update: **the receipt of funds in a deep-frozen trust line as a result of a rippling step will fail.**

##### Example

Let's take a look at an example of how deep-freeze impacts rippling:

```
+-------+           USD           +---------+           USD           +-------+
| Alice | ----------------------> | Gateway | ----------------------> |  Bob  |
+-------+                         +---------+ (Bob is deep-frozen)    +-------+
```

Consider the following scenario:

1. Issuer account issues USD to both Alice and Bob, each of which has a trustline.
2. Issuer deep-freezes Bob's trustline by submitting a `TrustSet` with `tfSetFreeze` and `tfSetDeepFreeze` flags.
3. Alice attempts to send a USD `Payment` to Bob. The transaction _fails_ because Bob's USD trustline has been deep-frozen and can no longer receive funds.

#### 2.2.2. Order Book and AMM

In the payment engine, offers and AMM pools can be consumed in the path when a cross-currency payment is involved, resulting in a change to the trustline balance. This proposal introduces behavior changes to the order book step when trustlines have been deep-frozen.

##### 2.2.2.1. Order Book

This proposal introduces a change to the order book step: **if the offer owner has been deep-frozen for the `TakerPays` token (buy amount), the offer is considered to be _unfunded_ and the step fails.**

###### Example

Let's take a look at an example of how deep-freeze impacts order book:

```
                                                                 Bob's Offer
+-------+         USD            +---------+        USD       +--------------+      XRP     +-------+
| Alice | ---------------------> | Gateway | ---------------> | Sell: 100 XRP| -----------> | Carol |
+-------+     SendMax: 100 USD   +---------+                  +--------------+              +-------+
              Amount: 100 XRP                                 | Buy: 100 USD |
                                                              +--------------+
                                                            (Bob is deep-frozen)
```

Consider the following scenario:

1. Issuer account issues USD to both Alice and Bob, each of which has a trustline.
2. Issuer deep-freezes Bob's trustline by submitting a `TrustSet` with `tfSetFreeze` and `tfSetDeepFreeze` flags.
3. Alice attempts to send XRP to Carol through a `Payment` transaction using Bob's offer to exchange USD for XRP. Alice fails to send XRP to Carol because Bob's offer is unfunded due to the deep-frozen trustline.

##### 2.2.2.2. AMM

The AMM step does not require any changes because, currently, an AMM step fails if the AMM account is frozen for any involved asset. Since a deep-frozen asset would already be regularly frozen, no additional checks are needed when an asset is deep-frozen.

### 2.3. `OfferCreate` transaction

This proposal introduces a new change to the `OfferCreate` transaction:

- `OfferCreate` returns `tecFROZEN` if the `TakerPays` (buy amount) token has been _deep-frozen_ by the issuer

Moreover, any existing offers where the owner has been deep-frozen on the `TakerPays` token **can no longer be consumed and will be considered as an _unfunded_ offer that will be implicitly cancelled by new Offers that cross it.**

### 2.4. `AMMWithdraw` transaction

This proposal does not need to change the `AMMWithdraw` transaction due to the deep-freeze, as all deep-frozen tokens have already been regularly frozen, preventing the withdrawal of either regularly frozen or deep-frozen tokens.

## 3. Invariants

Possible invariants:

- Disallowing any increase in the balance of an deep-frozen trustline as a result of any type of transaction.
- A trust line cannot have the `lsfLowDeepFreeze` flag set without also having the `lsfLowFreeze` flag set, and the same applies to the `lsfHighDeepFreeze` flag.

## 4. FAQ

### Why can't we embed the disallow-receiving into the existing freeze without introducing a new flag?

Altering the existing freeze functionality to disallow receiving would be a significant breaking change, potentially disrupting the workflows of current users. Instead, it is preferable to introduce a configurable flag, offering additional flexibility without affecting the existing behavior.

### Why can't this be a separate feature named "block-receiving"?

The block-receiving feature shares similarities with the existing freeze functionality, as both aim to prevent unauthorized or blacklisted parties from transferring funds. Creating it as a separate feature would introduce unnecessary complexities, such as the need to add a new account-level flag to toggle the feature. Integrating it into the existing framework avoids these complications while maintaining consistency.

### How does MPT freeze/lock behavior differ from IOU?

The MPT freeze/lock functionality differs somewhat from how IOUs work today. When an MPT holder is locked, they cannot send or receive MPT payments, so a single flag is sufficient. In contrast, for IOUs, the regular freeze only disallows sending. If the issuer wants to block receiving as well, they must apply a deep-freeze.
