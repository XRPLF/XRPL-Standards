<pre>
  Title:        <b>Clawback Support</b>
  Description:  Extending clawback functionality into freeze
  Revision:     <b>3</b> (2023-4-25)
<hr>  Author:       <a href="mailto:nikb@bougalis.net">Nikolaos D. Bougalis</a>
                <a href="mailto:shawnxie@ripple.com">Shawn Xie</a>
<hr>  Requires:     XLS 39
<hr>  core_protocol_changes_required:     true
</pre>

## 1. Abstract

Although the XRP Ledger offers rich support for [tokens](https://xrpl.org/tokens.html) (a.k.a. IOUs or issued assets), including offering issuers the ability to [freeze](https://xrpl.org/freezes.html) issuances, in order to meet regulatory requirements, some issuers need to be able to go further, by having the ability to "[clawback](https://en.wikipedia.org/wiki/Clawback)" their issued assets. 

----------------------- -------------------------------------------------------
:bangbang: This proposal deals only with issued assets. **The proposed clawback
           support _cannot_ be used to claw back XRP.**                                        
----------------------- -------------------------------------------------------

### Advantages and Disadvantages

**Advantages**

- Issuers that are restricted from issuing on ledger because of regulatory requirements requiring the ability to clawback funds will be able to issue tokens.
- By being able to "clawback" issuers can ensure that the "on-chain" view is representative of the balance.
- Compared to other on-ledger features (e.g. freeze), clawback is minimal and trivial to implement.
- `Clawback` serves as an extension of the existing freeze feature, meaning that clawback can be toggled on/off from an `TrustLine` level. It also makes sense to bundle these two features to serve specific regulatory needs. 
- By relying on the freeze flag, `Clawback` ensures that issuers who have enabled `lsfNoFreeze` will continue to be unable to access holder's funds, even after the introduction of the clawback feature. This reinforces trust among token holders, as they can be confident that their funds will remain secure and untouched.
- The issuer has the option to opt-out Clawback through an account level setting


**Disadvantages**

- Introduces an additional transaction, along with the complexity that comes with that.
- Issuers now get additional power, which may be concerning to token holders.
- Requires additional documentation, including highlighting the fact that clawback cannot be applied to XRP.

---

## 2. Motivation
Jurisdictions may require issuers of digital assets to have a way to recover funds in certain circumstances. The `Clawback` feature can provide a way to comply with these regulations.

The `Clawback` feature is designed to serve as an extension of the freeze flag, as freezing a trustline is typically a precursor to a clawback action. By making `Clawback` dependent on freeze, issuers of digital assets are provided with an additional layer of control and security over their assets. The purpose of `Clawback` is to provide issuers with a mechanism to recover funds that have been issued in error, to protect against fraudulent activities, to comply with regulatory requirements, and to maintain stability. 

`Clawback` is incorporated into freeze because, from the perspective of the token holder, the impact of `Clawback` is comparable to that of freeze. In particular, token holders who have already frozen trustlines would not be concerned by the introduction of the `Clawback` feature, as their funds are already inaccessible. Therefore, from the perspective of the holder, the presence or absence(after claw back) of funds in their frozen trustline is unsignficant. By tying `Clawback` to freeze, issuers can minimize the potential impact on token holders and avoid creating unnecessary concern. This approach provides issuers with greater flexibility and control over their assets, while also preserving the trust and confidence of token holders in the ecosystem.

---

## 3. Specification

### 3.1. On-Ledger Data Structures

This proposal introduces no new on ledger structures.



### 3.2. Account Root modifications

This proposal introduces 1 additional flag for the `Flags` field of `AccountRoot`:

| Flag Name       |  Flag Value  |
|:---------------:|:------------:|
| `lsfNoClawback` | `0x02000000` | 

Clawback is enabled by default. If the issuer wants to disable it, they must set this flag through an `AccountSet` transaction. Once set, the setting cannot be reverted and the issuer loses the ability to clawback permanently. 


### 3.3. Transactions
This proposal introduces one new transaction: `Clawback`

#### 3.3.1. `Clawback` transaction
The **`Clawback`** transaction modifies a trustline object, by adjusting the balance accordingly and, if instructed to, by changing relevant flags. If possible (i.e. if the `Clawback` transaction would leave the trustline is in the "default" state), the transaction will also remove the trustline.

**An counterparty can be clawed back if and only if the trustline has been frozen and `lsfNoClawback` is not set.** There are two ways to enable freeze on a trustline, either through a `TrustSet` or `Clawback` where the `Flags` field is set accordingly. If a clawback transaction is attempted on a trustline that has not been frozen, the transaction will not be allowed and will return with an error code `tecNO_PERMISSION`.

The transaction supports all the existing "common" fields for a transaction.

##### Transaction-specific Fields

| Field Name          | Required?        |  JSON Type    | Internal Type     |
|---------------------|:----------------:|:-------------:|:-----------------:|
| `TransactionType`   |:heavy_check_mark:|`string`       |   `UINT16`        |

Indicates the new transaction type **`Clawback`**. The integer value is `30`. The recommended name is `ttCLAWBACK`.

| Field Name    | Required?        |  JSON Type  | Internal Type     |
|---------------|:----------------:|:-----------:|:-----------------:|
| `Account`     |:heavy_check_mark:|`string`     | `ACCOUNT ID`      |

Indicates the account which is executing this transaction. The account **MUST** be the issuer of the asset being clawed back. Note that in the XRP Ledger, trustlines are bidirectional and, under some configurations, both sides can be seen as the "issuer" of an asset. In this specification, the term issuer is used to mean the side of the trustline that has an outstanding balance (i.e. 'owes' the issued asset) that it wishes to claw back.

---

| Field Name | Required?        | JSON Type | Internal Type |
|------------|:----------------:|:---------:|:-------------:|
| `Amount`   |:heavy_check_mark:| `object`  |   `AMOUNT`    |

Indicates the amount being clawed back, as well as the counterparty from which the amount is being clawed back from. It is not an error if the amount exceeds the holder's balance; in that case, the maximum available balance is clawed back. It is not an error if the amount is zero; in this case, the transaction does not claw back any funds but may adjust flags, as indicated by the `Flags` field.

It is an error if the counterparty listed in `Amount` is the same as the `Account` issuing this transaction; the transaction should fail execution with `temBAD_AMOUNT`.

:bangbang: The sub-field `issuer` within `Amount` represents the token holder's address instead of the issuer's.

---

| Field Name     | Required?        |  JSON Type  | Internal Type     |
|----------------|:----------------:|:-----------:|:-----------------:|
| `Flags`        |:heavy_check_mark:|`number`     | `UINT32`          |

Specifies the flags for this transaction. The universal transaction flags that are applicable to all transactions (e.g., `tfFullyCanonicalSig`) are valid. This proposal introduces the following new, transaction-specific flags:

>| Flag Name     |         Flag Value         |                                                         Description                                                         |
>|---------------|:---------------------------------------------------------------------------------------------------------------------------:|:----------------------------------------------------------------------------------------------------------------------------------------------------------------------:|
>| `tfSetFreeze`    |        `0x00000001`        | If set, either the `lsfHighFreeze` or `lsfLowFreeze` flag (as appropriate) will be set in the trust line. It is not an error to request to set a flag that has already been set. Enabling the `tfSetFreeze` flag simplifies the process of clawing back funds from a trustline. It allows the clawback transaction to freeze the trustline and reclaim the funds in a single transaction, without needing to set the `tfSetFreeze` flag through a `TrustSet` transaction beforehand. However, if the `tfSetFreeze` flag has not been set or the appropriate freeze flag hasn't been enabled on the trustline before attempting to clawback, then the transaction will fail and return the error code `tecNO_PERMISSION`.|
>| `tfClearFreeze`      |        `0x00000002`        | If set, either the `lsHighFreeze` or `lsfLowFreeze` flag (as appropriate) will be removed from the trust line. It is not an error to request to clear a flag that isn't set. Enabling the `tfClearFreeze` flag simplifies the process of unfreezing a trustline. With this flag enabled, the clawback transaction can reclaim the frozen funds and unfreeze the trustline at the same time, without requiring an additional `TrustSet` transaction to clear the freeze flag.|

The `tfSetFreeze` and `tfClearFreeze` flags are options that can be set in a `Clawback` transaction. They make the process of clawing back funds more convenient by combining multiple steps into one.

Usually, when you want to clawback funds from a trustline, you have to freeze the trustline first, then take back the funds, and finally, unfreeze the trustline if you choose to. With these two flags, you can clawback the funds and keep the trustline unfrozen at the same time by setting both of them simultaneously.

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

In execution, this transaction would freeze the trustline by setting the `Flag` to `1`, and claw back at most **314.159 FOO** issued by `rp6abvbTbjoce8ZDJkT6snvxTZSYMBCC9S` and held by `rsA2LpzuawewSBQXkiju3YQTMzW13pAAdW`. If `rsA2LpzuawewSBQXkiju3YQTMzW13pAAdW` did not have a trustline set up or that trustline was set to `0` then the error `tecNO_LINE` would be returned and a fee would be consumed.

### 3.4. Amendment

This transaction will require an amendment. The proposed name is `XLS-39-Clawback`.

---

## 4. Rationale

By default, `Clawback` is activated and an issuer would need to manually set `lsfNoClawback` to opt-out of this feature. If `Clawback` was not enabled by default, the issuer would need to follow extra steps to ensure their owner directory is empty before enabling `Clawback`, which could create confusion and alignment issues with the current implementation of freeze. To avoid such complications, it is best to keep `Clawback` enabled by default, especially as we expand it into Compact Fungible Tokens (CFT). This would ensure that both features share a similar default setting and minimize potential confusion or issues down the line.

While it may seem desirable to have these features disabled by default for the benefit of the token holder, it is important to prioritize design and usability considerations. The current practice of having freeze enabled by default has already been established and implemented, thus, clawback should follow this practice as well. Furthermore, there are already sufficient precautions in place, such as requiring the trustline to be frozen before `Clawback` can be done. These measures are designed to mitigate potential negative impact on the token holder while also ensuring the efficiency of the `Clawback` feature.

---

## 5. Backwards Compatibility
No backward compatbility issues found

---

## 6. Test Cases
Test cases need to ensure the following:

- The account that signs and submits `Clawback` transaction must be the token issuer 
- Token issuer cannot clawback from themselves
- Clawback can only be successful on the trustlines that have been already frozen, or, the `Clawback` has set the `tfSetFreeze` flag 
- The `tfSetFreeze` and `tfClearFreeze` flags of the `Clawback` transaction perform the intended freeze behavior on the trustline
- `Clawback` adheres to account flags `lsfGlobalFreeze` and `lsfNoFreeze`
- The issuer is only able to claw back the specific amount of funds that specified in the transaction, but can't exceed the maximum amount of funds the holder has
- Test that the `Clawback` feature does not interfere with any other features of the token, such as Offers