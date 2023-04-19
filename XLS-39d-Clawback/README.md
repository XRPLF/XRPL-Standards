<pre>
  Title:        <b>Clawback Support</b>
  Revision:     <b>2</b> (2023-4-19)

<hr>  Author:       <a href="mailto:nikb@bougalis.net">Nikolaos D. Bougalis</a>
                <a href="mailto:shawnxie@ripple.com">Shawn Xie</a>
</pre>

# 1. Clawback Support

## 1.1. Abstract

Although the XRP Ledger offers rich support for [tokens](https://xrpl.org/tokens.html) (a.k.a. IOUs or issued assets), including offering issuers the ability to [freeze](https://xrpl.org/freezes.html) issuances, in order to meet regulatory requirements, some issuers need to be able to go further, by having the ability to "[clawback](https://en.wikipedia.org/wiki/Clawback)" their issued assets. 

----------------------- -------------------------------------------------------
:bangbang: This proposal deals only with issued assets. **The proposed clawback
           support _cannot_ be used to claw back XRP.**                                        
----------------------- -------------------------------------------------------

### 1.1.1. Advantages and Disadvantages

**Advantages**

- Issuers that are restricted from issuing on ledger because of regulatory requirements requiring the ability to clawback funds will be able to issue tokens.
- By being able to "clawback" issuers can ensure that the "on-chain" view is representative of the balance.
- Compared to other on-ledger features (e.g. freeze), clawback is minimal and trivial to implement.
- `Clawback` is implemented as an extension of the existing freeze feature, meaning that clawback can be toggled on/off from an `TrustLine` level. It also makes sense to bundle these two features to serve specific regulatory needs.
- By relying on the freeze flag, `Clawback` ensures that issuers who have enabled `lsfNoFreeze` will continue to be unable to access holder's funds, even after the introduction of the clawback feature. This reinforces trust among token holders, as they can be confident that their funds will remain secure and untouched.


**Disadvantages**

- Introduces an additional transaction, along with the complexity that comes with that.
- Issuers now get additional power, which may be concerning to token holders.
- Requires additional documentation, including highlighting the fact that clawback cannot be applied to XRP.

## 1.2. Creating and Transferring Tokens on XRPL

### 1.2.1. On-Ledger Data Structures

This proposal introduces no new on ledger structures.

## Transactions

This proposal introduces one new transaction: `Clawback`:

### The **`Clawback`** transaction

The **`Clawback`** transaction modifies a trustline object, by adjusting the balance accordingly and, if instructed to, by changing relevant flags. If possible (i.e. if the `Clawback` transaction would leave the trustline is in the "default" state), the transaction will also remove the trustline.

**An counterparty can be clawed back if and only if the trustline has been frozen.** There are two ways to enable freeze on a trustline, either through a `TrustSet` or `Clawback` where the `Flags` field is set accordingly. If a clawback transaction is attempted on a trustline that has not been frozen, the transaction will not be allowed and will return with an error code `tecNO_PERMISSION`.

The transaction supports all the existing "common" fields for a transaction.

#### Transaction-specific Fields

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

## Example **`Clawback`** transaction

```
{
  "TransactionType": "Clawback",
  "Account": "rp6abvbTbjoce8ZDJkT6snvxTZSYMBCC9S",
  "Amount": "LimitAmount": {
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

#### Execution

In execution, this transaction would freeze the trustline by setting the `Flag` to `1`, and claw back at most **314.159 FOO** issued by `rp6abvbTbjoce8ZDJkT6snvxTZSYMBCC9S` and held by `rsA2LpzuawewSBQXkiju3YQTMzW13pAAdW`. If `rsA2LpzuawewSBQXkiju3YQTMzW13pAAdW` did not have a trustline set up or that trustline was set to `0` then the error `tecNO_LINE` would be returned and a fee would be consumed.

### 1.3. Account Root modifications

This proposal does not introduce any new flags for the clawback functionality. But, if the issuer has already set the `lsfNoFreeze` flag, then it means that they will not be able to clawback either.

### 1.4 Amendment

This transaction will require an amendment. The proposed name is `XLS-39-Clawback`.

### 1.5 Compatibility with Compact Fungible Token (XLS-33d)
The Compact Fungible Token(CFT) proposes another token type. The clawback functionality can be extended to CFT because it supports the freeze feature, just like trustline. With CFT, the issuer can choose to freeze individual token holder's balance. If clawback is updated in order to accomodate for this new token, the `Clawback` transaction introduces a new field named `CFTokenAmount`:

---

| Field Name | Required?        | JSON Type | Internal Type |
|------------|:----------------:|:---------:|:-------------:|
| `CFTokenAmount`   || `object`  |   `CFTOKEN AMOUNT`  |

The `CFTokenAmount` encompasses `CFTokenIssuanceID` and `Value` to indicate the CFT and the amount to be clawed back.

With the addition of this field, the `Amount` field is now *optional*. But, either one of `CFTokenAmount` or `Amount` must be specified in the `Clawback` transaction, otherwise `temMALFORMED` is returned from the transaction.

---