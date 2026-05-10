<pre>
  xls: 39
  title: Clawback Support
  description: Enabling clawback for IOUs to meet regulatory requirements
  author: Nikolaos D. Bougalis <nikb@bougalis.net>, Shawn Xie <shawnxie@ripple.com>
  proposal-from: https://github.com/XRPLF/XRPL-Standards/discussions/94
  status: Final
  category: Amendment
  created: 2023-03-04
</pre>

## 1. Abstract

Although the XRP Ledger offers rich support for [tokens](https://xrpl.org/tokens.html) (a.k.a. IOUs or issued assets), including offering issuers the ability to [freeze](https://xrpl.org/freezes.html) issuances, in order to meet regulatory requirements, some issuers need to be able to go further, by having the ability to "[clawback](https://en.wikipedia.org/wiki/Clawback)" their issued assets. **Issued tokens can be clawed back by an issuer if, and only if, `lsfAllowTrustLineClawback` is set.**

---

:bangbang: This proposal deals only with issued assets. **The proposed clawback
support _cannot_ be used to claw back XRP.**

---

### Advantages and Disadvantages

**Advantages**

- Issuers that are restricted from issuing on ledger because of regulatory requirements requiring the ability to clawback funds will be able to issue tokens.
- By being able to "clawback" issuers can ensure that the "on-chain" view is representative of the balance.
- Compared to other on-ledger features (e.g. freeze), clawback is minimal and trivial to implement.
- `Clawback` is disabled by default, this gives token holders more confidence that they won't be clawed back randomly.

**Disadvantages**

- Introduces an additional transaction, along with the complexity that comes with that.
- Issuers now get additional power, which may be concerning to token holders.
- Requires additional documentation, including highlighting the fact that clawback cannot be applied to XRP.

---

## 2. Motivation

Jurisdictions may require issuers of digital assets to have a way to recover funds in certain circumstances. The `Clawback` feature can provide a way to comply with these regulations.

---

## 3. Specification

### 3.1. On-Ledger Data Structures

This proposal introduces no new on ledger structures.

### 3.2. Account Root modifications

This proposal introduces 1 additional flag for the `Flags` field of `AccountRoot`:

|          Flag Name          |  Flag Value  |
| :-------------------------: | :----------: |
| `lsfAllowTrustLineClawback` | `0x80000000` |

Clawback is disabled by default. The account must set this flag through an `AccountSet` transaction, which is successful only if the account has an empty owner directory, meaning they have no trustlines, offers, escrows, payment channels, or checks. Otherwise, the `AccountSet` returns `tecOWNERS`. After this flag has been successfully set, it cannot reverted, and the account permanently gains the ability to clawback on trustlines.

If the account attempts to set `lsfAllowTrustLineClawback` while `lsfNoFreeze` is set, the transaction will return `tecNO_PERMISSION` because clawback cannot be enabled on an account that has already disclaimed the ability to freeze trustlines. Reversely, if an account attempts to set `lsfNoFreeze` while `lsfAllowTrustLineClawback` is set, the transaction will also return `tecNO_PERMISSION`.

### 3.3. Transactions

This proposal introduces one new transaction: `Clawback`

#### 3.3.1. `Clawback` transaction

The **`Clawback`** transaction modifies a trustline object, by adjusting the balance accordingly and, if instructed to, by changing relevant flags. If possible (i.e. if the `Clawback` transaction would leave the trustline is in the "default" state), the transaction will also remove the trustline.

**Issued tokens can be clawed back by an issuer if, and only if, `lsfAllowTrustLineClawback` is set.** If this transaction is attempted while `lsfAllowTrustLineClawback` is unset, it will return with an error code `tecNO_PERMISSION`.

The transaction supports all the existing "common" fields for a transaction.

##### Transaction-specific Fields

| Field Name        |     Required?      | JSON Type | Internal Type |
| ----------------- | :----------------: | :-------: | :-----------: |
| `TransactionType` | :heavy_check_mark: | `string`  |   `UINT16`    |

Indicates the new transaction type **`Clawback`**. The integer value is `30`. The recommended name is `ttCLAWBACK`.

| Field Name |     Required?      | JSON Type | Internal Type |
| ---------- | :----------------: | :-------: | :-----------: |
| `Account`  | :heavy_check_mark: | `string`  | `ACCOUNT ID`  |

Indicates the account which is executing this transaction. The account **MUST** be the issuer of the asset being clawed back. Note that in the XRP Ledger, trustlines are bidirectional and, under some configurations, both sides can be seen as the "issuer" of an asset. In this specification, the term issuer is used to mean the side of the trustline that has an outstanding balance (i.e. 'owes' the issued asset) that it wishes to claw back.

---

| Field Name | Required? | JSON Type | Internal Type |
| ---------- | :-------: | :-------: | :-----------: |
| `Flags`    |           | `number`  |   `UINT32`    |

The universal transaction flags that are applicable to all transactions (e.g., `tfFullyCanonicalSig`) are valid. This proposal introduces no new transaction-specific flags.

---

| Field Name |     Required?      | JSON Type | Internal Type |
| ---------- | :----------------: | :-------: | :-----------: |
| `Amount`   | :heavy_check_mark: | `object`  |   `AMOUNT`    |

Indicates the amount being clawed back, as well as the counterparty from which the amount is being clawed back from. It is not an error if the amount exceeds the holder's balance; in that case, the maximum available balance is clawed back. It returns `temBAD_AMOUNT` is the amount is zero.

It is an error if the counterparty listed in `Amount` is the same as the `Account` issuing this transaction; the transaction should fail execution with `temBAD_AMOUNT`.

If there doesn't exist a trustline with the counterparty or that trustline's balance is `0`, the error `tecNO_LINE` is returned.

:bangbang: The sub-field `issuer` within `Amount` represents the token holder's address instead of the issuer's.

---

#### 3.3.2. Example **`Clawback`** transaction

```
{
  "TransactionType": "Clawback",
  "Account": "rp6abvbTbjoce8ZDJkT6snvxTZSYMBCC9S",
  "Amount": {
      "currency": "FOO",
      "issuer": "rsA2LpzuawewSBQXkiju3YQTMzW13pAAdW",
      "value": "314.159"
    },
  "Flags": 1,
  "Fee": 10,
  "Memos": [
        {
            "Memo": {
                "MemoType": "526561736f6e",
                "MemoData": "5468697320636c61776261636b2077617320617574686f72697a6564206279204a6f652e"
            }
        }
    ],
}
```

In execution, this transaction would claw back at most **314.159 FOO** issued by `rp6abvbTbjoce8ZDJkT6snvxTZSYMBCC9S` and held by `rsA2LpzuawewSBQXkiju3YQTMzW13pAAdW`. If `rsA2LpzuawewSBQXkiju3YQTMzW13pAAdW` did not have a trustline set up or that trustline's balance is `0` then the error `tecNO_LINE` would be returned and a fee would be consumed.

### 3.4. Amendment

This transaction will require an amendment. The proposed name is `Clawback`.

---

## 4. Rationale

Clawback is disabled by default and requires the issuer to have an empty owner directory (i.e., no existing trustlines, offers, etc) before the issuer is allowed to enable this feature. This design prefers a cautious approach where the issuer needs to take overt action to enable clawback capabilities. This helps ensure that token holders are aware of the possibility of clawback before they choose to hold any particular token.

---

## 5. Backwards Compatibility

No backward compatbility issues found

---

## 6. Test Cases

Test cases need to ensure the following:

- The account that signs and submits `Clawback` transaction must be the token issuer
- Token issuer cannot clawback from themselves
- `Clawback` adheres to account flags `lsfAllowTrustLineClawback`, `lsfGlobalFreeze` and `lsfNoFreeze`
- The issuer is only able to claw back the specific amount of funds that specified in the transaction, but can't exceed the maximum amount of funds the holder has
- Test that the `Clawback` feature does not interfere with any other features of the token, such as Offers

## 7. Compatibility with Automated Market Maker (XLS-30)

The Automated Market Maker (AMM) gives an account the ability to deposit issued tokens into AMM instance pool, in the form of `LPToken`. As of the current `Clawback` spec, it only allows an issuer to claw back the funds that are _spendable_. This would mean that the `AMMCreate` transaction will error if either of the tokens' issuers enabled the `lsfAllowTrustLineClawback` flag on their account.

If clawing back from an AMM instance pool is required, such change will need a separate specification.

## 8. Compatibility with Escrow & Paychannels (XLS-34)

The XLS-34 gives an account the ability to "lock" issued tokens into an escrow or paychannel, in the form of `LockedBalance`. As of the current `Clawback` spec, it only allows an issuer to claw back the funds that are _spendable_. This would mean that the funds deposited into an Escrow or Paychannel cannot be clawed back.

If clawing back tokens from an Escrow or Paychannel is required, such change will need a separate specification.
