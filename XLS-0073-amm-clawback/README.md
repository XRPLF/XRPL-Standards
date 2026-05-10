<pre>
  xls: 73
  title: AMMClawback
  description: Amendment to enable token issuers to claw back tokens from AMM pools for regulatory compliance
  author: Shawn Xie <shawnxie@ripple.com>, Yinyi Qian <yqian@ripple.com>
  proposal-from: https://github.com/XRPLF/XRPL-Standards/discussions/212
  status: Draft
  category: Amendment
  requires: [XLS-39](../XLS-0039-clawback/README.md), [XLS-30](../XLS-0030-automated-market-maker/README.md)
  created: 2024-08-02
</pre>

# AMMClawback

## Abstract

The AMMClawback amendment enables token issuers to claw back tokens from wallets that have deposited into AMM pools, ensuring regulatory compliance. We introduced a new transaction type AMMClawback in this amendment and the AMMClawback transaction is allowed only when `lsfAllowTrustLineClawback` is enabled by the issuer. `lsfAllowTrustLineClawback` can be set only if the account has an empty owner directory through `AccountSet`.

## 1. Overview

This proposal introduces new improvements on how AMM interacts with frozen asset and clawback.

### 1.1. AMM and Frozen Asset

Currently if an asset in the AMM pool is frozen (either global or individual), we can still deposit the paired token into the AMM pool (if the paired asset is not frozen). This proposal introduces:

- Prohibit a wallet from depositing new tokens (single-sided and double-sided) into an AMM pool if at least one of the tokens the wallet owns has been frozen (either individually or globally) by the token issuer.

### 1.2. AMM and Unauthorized Asset

At present, if an account is not authorized to hold a token in the AMM pool, it can still make a single deposit of the other paired token, provided it is authorized for that token. This proposal introduces:

- Prevent a wallet from depositing new tokens (either single-sided or double-sided) into an AMM pool if it is not authorized to hold one or both of the tokens in the pool.

### 1.3. AMM and Clawback

Currently, accounts that have enabled clawback cannot create AMM pools. This proposal introduces the following:

- Allow an account to create AMM pool even if one of the tokens has enabled `lsfAllowTrustLineClawback`. However, token issuers will not be allowed to claw back from the AMM account using the `Clawback` transaction.
- Introduce a new `AMMClawback` transaction to allow token issuers to exclusively claw back from AMM pools that has one of their tokens, according to the current proportion in the pool.

## 2. Specification

### 2.1. Prohibiting the Deposit of New Tokens

This proposal introduces changes to the behavior of the `AMMDeposit` transaction when tokens in trustlines interact with Automated Market Maker (AMM) pools.

#### 2.1.1. AMMDeposit for Frozen Asset

Assume we have created an Automated Market Maker (AMM) pool with two assets: A and B. Currently, asset A is frozen (either individually or globally). The following table outlines whether specific scenarios are allowed or prohibited for the current behavior and proposed behavior:

| Scenario                | Current Behavior | Proposed Behavior |
| ----------------------- | ---------------- | ----------------- |
| Double-Asset Deposit    | Prohibited       | Prohibited        |
| Only Deposit A (frozen) | Prohibited       | Prohibited        |
| Only Deposit B          | Allowed          | Prohibited        |

As illustrated in the table above, the primary change is that when one asset in the AMM pool is frozen, depositing the other asset is no longer allowed. This means that deposits are prohibited for the non-frozen asset when its paired asset is frozen.

#### 2.1.1. AMMDeposit for Unauthorized Asset

Assume we have created an Automated Market Maker (AMM) pool with two assets: A and B. The issuer of A has set `lsfRequireAuth` and the holder is not authorized to hold A.
The table below summarizes the allowed and prohibited scenarios under the current and proposed behavior:

| Scenario                      | Current Behavior | Proposed Behavior |
| ----------------------------- | ---------------- | ----------------- |
| Double-Asset Deposit          | Prohibited       | Prohibited        |
| Only Deposit A (Unauthorized) | Prohibited       | Prohibited        |
| Only Deposit B                | Allowed          | Prohibited        |

The primary change is that when the holder is not allowed to hold one of the token in the AMM pool, depositing the other asset is no longer allowed.

### 2.2. Allowing AMM Pool Creation with Clawback-Enabled Tokens

Currently, when clawback is enabled for the issuer account by setting `lsfAllowTrustLineClawback` flag, `AMMCreate` is prohibited against this issuer. After the AMMClawback amendment, `AMMCreate` is allowed for clawback-enabled issuer. But the issuer can not clawback from the AMM account using `Clawback` transaction. `AMMClawback` transaction is needed for the issuer to clawback from an AMM account.

#### Example: Illustrating the AMMClawback Amendment

Suppose an issuer has enabled clawback by setting the `lsfAllowTrustLineClawback` flag through an `AccountSet` transaction. Additionally, two trustlines have been established between the holder and the issuer for currencies A and B

- **Pre-Amendment Behavior:**
  - If the holder attempts to create an AMM pool (`AMMCreate`) using the pair of trustline assets A and B associated with the issuer, the transaction will fail with a `tecNO_PERMISSION` error.

- **Post-Amendment Behavior:**
  - After the AMMClawback amendment, if the holder submits an `AMMCreate` transaction to create an AMM pool with assets A and B, the transaction will be successful.
  - However, if the issuer wants to clawback assets from the AMM account, they must use the `AMMClawback` transaction instead of the regular `Clawback` transaction.

This change allows for the creation of AMM pools with clawback-enabled issuers while introducing a new transaction type (`AMMClawback`) for issuers to clawback assets from AMM accounts.

### 2.3. Introducing a New Transaction for Clawback from AMM Pools

This proposal introduces a new transaction type `AMMClawback` to allow asset issuers to claw back their assets from the AMM pool.

Issuers can only claw back issued tokens in the AMM pool only if the `lsfAllowTrustLineClawback` flag is enabled. Attempting to do so without this flag set will result in an error code `tecNO_PERMISSION`.

By designating the holder account, asset, asset2 and amount, this transaction will:

- Claw back the specified amount of asset held by the specified holder account that are in the specified AMM account.
- This transaction will initiate a two-asset withdrawal of the specified amount of tokens on the current proportion from the AMM pool.
- Provided `Asset`'s issuer should match `Account`. Otherwise, `temMALFORMED` will be returned.
- If the issuer only issues one token in the AMM pool:
  - The issuer's `asset` will return to the issuer's account.
  - The paired `asset2` which is not issued by the issuer will be transferred back to the holder's account.
- If the two assets in the AMM pool are both issued by the issuer, this transaction will:
  - The issuer's `asset` will return to the issuer's account.
  - If `tfClawTwoAssets` flag is set, the paired `asset2` which is also issued by the issuer, will return to issuer as well.
  - If `tfClawTwoAssets` flag is not set, the paired `asset2` will go back to the holder.
- `tfClawTwoAssets` flag can only be set if the issuer issues both assets in the AMM pool. Otherwise, `tecNO_PERMISSION` will be returned.
- If the requested amount of tokens exceeds the holder's available balance in the AMM pool, all the tokens owned by the specified holder will be clawed back.
- If amount is not given in the request, all the tokens owned by the specified holder will be clawed back from the pool.

#### 2.3.1. Fields for AMMClawback transaction

| Field Name        |     Required?      | JSON Type | Internal Type |
| ----------------- | :----------------: | :-------: | :-----------: |
| `TransactionType` | :heavy_check_mark: | `string`  |   `UINT16`    |

`TransactionType` specifies the new transaction type `AMMClawback`. The integer value is 31. The recommended name is `ttAMM_CLAWBACK`.

---

| Field Name |     Required?      | JSON Type | Internal Type |
| ---------- | :----------------: | :-------: | :-----------: |
| `Account`  | :heavy_check_mark: | `string`  | `ACCOUNT ID`  |

`Account` designates the issuer of the asset being clawed back, and must match the account submitting the transaction.

---

| Field Name |     Required?      | JSON Type | Internal Type |
| ---------- | :----------------: | :-------: | :-----------: |
| `Holder`   | :heavy_check_mark: | `string`  | `ACCOUNT ID`  |

`Holder` specifies the holder account of the asset to be clawed back.

---

| Field Name |     Required?      | JSON Type | Internal Type |
| ---------- | :----------------: | :-------: | :-----------: |
| `Asset`    | :heavy_check_mark: | `object`  |    `ISSUE`    |

`Asset` specifies the token that the issuer wants to claw back from the AMM pool. `Asset`'s issuer must match with `Account`. If it does not, the system will return an error: `temMALFORMED`. Notice always put the token to be clawed back in `Asset` insead of `Asset2`.

It has the following subfields:

| Field name |     Required?      | Description                                                                                       |
| :--------: | :----------------: | :------------------------------------------------------------------------------------------------ |
|  `issuer`  | :heavy_check_mark: | specifies the issuer of the token being clawed back, this should be the same as the Account field |
| `currency` | :heavy_check_mark: | specifies the currency to be clawed back                                                          |

---

| Field Name |     Required?      | JSON Type | Internal Type |
| ---------- | :----------------: | :-------: | :-----------: |
| `Asset2`   | :heavy_check_mark: | `object`  |    `ISSUE`    |

`Asset2` specifies the other asset in the AMM pool.

It has the following subfields:

| Field name |     Required?      | Description                                       |
| :--------: | :----------------: | :------------------------------------------------ |
|  `issuer`  |                    | specifies the paired token's issuer, omit for xrp |
| `currency` | :heavy_check_mark: | specifies the paired token's currency             |

---

| Field Name | Required? | JSON Type | Internal Type |
| ---------- | :-------: | :-------: | :-----------: |
| `Amount`   |           | `object`  |   `AMOUNT`    |

`Amount` specifies the amount of token to be clawed back from the AMM account. It should match the `Asset` field.

- If `Amount` is not given, all the specified asset will be clawed back.
- If `Amount` exceeds the holder's current balance in the AMM pool, all the specified token will be clawed back.

It has the following subfields:

| Field name |     Required?      | Description                                                                                       |
| :--------: | :----------------: | :------------------------------------------------------------------------------------------------ |
|  `issuer`  | :heavy_check_mark: | specifies the issuer of the token being clawed back, this should be the same as the Account field |
| `currency` | :heavy_check_mark: | specifies the currency to be clawed back                                                          |
|  `value`   | :heavy_check_mark: | specifies the maximum amount of this currency to be clawed back                                   |

---

#### 2.3.2. Flags

| Flag Name         | Hex Value  |                                                    Description                                                    |
| ----------------- | :--------: | :---------------------------------------------------------------------------------------------------------------: |
| `tfClawTwoAssets` | 0x00000001 | Indicates if the issuer wants to claw back both tokens in the pool. The two assets must both issued by the issuer |

- It can be set only when the issuer issues both assets in the AMM pool.
- If set, both the `Asset` token and the paired toke `Asset2` will be clawed back.
- If not set, only the `Asset` token will be clawed back, and the paired token `Asset2` will go back to the holder.

#### 2.3.3. AMMClawback transaction examples

##### 2.3.3.1 Only one token is issued by the issuer

Assume we have an AMM pool consisting two tokens FOO and Bar. And the proportion of FOO and BAR is 1:2. And the issuer `rPdYxU9dNkbzC5Y2h4jLbVJ3rMRrk7WVRL` only issues FOO, BAR is issued by some other account.

```
{
  "TransactionType": "AMMClawback",
  "Account": "rPdYxU9dNkbzC5Y2h4jLbVJ3rMRrk7WVRL",
  "Holder": "rvYAfWj5gh67oV6fW32ZzP3Aw4Eubs59B",
  "Asset": {
      "currency" : "FOO",
      "issuer" : "rPdYxU9dNkbzC5Y2h4jLbVJ3rMRrk7WVRL"
  },
  "Asset2" : {
      "currency" : "BAR",
      "issuer" : "rHtptZx1yHf6Yv43s1RWffM3XnEYv3XhRg"
  },
  "Amount": {
      "currency" : "FOO",
      "issuer" : "rPdYxU9dNkbzC5Y2h4jLbVJ3rMRrk7WVRL",
      "value" : "1000"
  }
}
```

- Upon execution, this transaction enables the issuer `rPdYxU9dNkbzC5Y2h4jLbVJ3rMRrk7WVRL` to claw back at most 1000 FOO owned by holder `rvYAfWj5gh67oV6fW32ZzP3Aw4Eubs59B` from AMM pool FOO/BAR.
- The transaction will result in the withdrawal of two corresponding assets from the AMM account on the current proportion:
  - The asset issued by the `Account` will be returned to the issuer `Account`. So 1000 FOO will be returned to the issuer `rPdYxU9dNkbzC5Y2h4jLbVJ3rMRrk7WVRL`.
  - The other asset will be transferred back to the holder's wallet. Since the proportion of FOO and BAR is 1:2, 2000 BAR will be transferred back to the holder's wallet.
  - If `Amount` is not given or its subfield `value` exceeds the holder's available balance, then all the holder's FOO will be clawed back from the AMM pool.
- `tfClawTwoAssets` can not be set because BAR is not issued by the issuer.

##### 2.3.3.2 Both tokens are issued by the same issuer

Assume we have an AMM pool consisting two tokens FOO and Bar. And the proportion of FOO and BAR is 1:2. And the issuer `rPdYxU9dNkbzC5Y2h4jLbVJ3rMRrk7WVRL` issues both FOO and BAR.

```
{
  "TransactionType": "AMMClawback",
  "Account": "rPdYxU9dNkbzC5Y2h4jLbVJ3rMRrk7WVRL",
  "Holder": "rvYAfWj5gh67oV6fW32ZzP3Aw4Eubs59B",
  "Asset": {
      "currency" : "FOO",
      "issuer" : "rPdYxU9dNkbzC5Y2h4jLbVJ3rMRrk7WVRL"
  },
  "Asset2": {
      "currency" : "BAR",
      "issuer" : "rPdYxU9dNkbzC5Y2h4jLbVJ3rMRrk7WVRL"
  },
  "Amount": {
      "currency" : "FOO",
      "issuer" : "rPdYxU9dNkbzC5Y2h4jLbVJ3rMRrk7WVRL",
      "value" : "1000"
  },
  "Flags": 1
}
```

- In this example, `tfClawTwoAssets` is set in the `Flags`, so 1000 FOO and 2000 BAR will both go back to the issuer. (If `tfClawTwoAssets` is not set in the `Flags`, 1000 FOO will go back to the issuer and 2000 BAR will be transferred back to the holder.)
- If `Amount` is not given or its subfield `value` exceeds the holder's available balance, then we will claw back the holder's existing balance of FOO in the AMM pool. And whether BAR will be clawed back or go back to the holder is still determined by the flag `tfClawTwoAssets`.

##### 2.3.3.3 Clawback all the tokens

```
{
  "TransactionType": "AMMClawback",
  "Account": "rPdYxU9dNkbzC5Y2h4jLbVJ3rMRrk7WVRL",
  "Holder": "rvYAfWj5gh67oV6fW32ZzP3Aw4Eubs59B",
  "Asset": {
      "currency" : "FOO",
      "issuer" : "rPdYxU9dNkbzC5Y2h4jLbVJ3rMRrk7WVRL"
  },
  "Asset2" : {
      "currency" : "BAR",
      "issuer" : "rHtptZx1yHf6Yv43s1RWffM3XnEYv3XhRg"
  }
}
```

- Issuer will clawback all of the holder's FOO token balance in the AMM pool by omitting the `Amount` field.
- In this example, since BAR is issued by a different issuer, then `tfClawTwoAssets` is not allowed to be set. All holder's FOO in the AMM pool will be clawed back. And the corresponding BAR will go back to the holder.

##### 2.3.3.4 Clawback all the tokens issued by the same issuer

```
{
  "TransactionType": "AMMClawback",
  "Account": "rPdYxU9dNkbzC5Y2h4jLbVJ3rMRrk7WVRL",
  "Holder": "rvYAfWj5gh67oV6fW32ZzP3Aw4Eubs59B",
  "Asset": {
      "currency" : "FOO",
      "issuer" : "rPdYxU9dNkbzC5Y2h4jLbVJ3rMRrk7WVRL"
  },
  "Asset2" : {
      "currency" : "BAR",
      "issuer" : "rPdYxU9dNkbzC5Y2h4jLbVJ3rMRrk7WVRL"
  },
  Flags: 1
}
```

- In this example, both FOO and BAR are issued by the same issuer. So `tfClawTwoAssets` is allowed to be set.
- Since `Amount` is not given and `tfClawTwoAssets` is set, the issuer will clawback all the holder's FOO and the corresponding BAR from the AMM pool. (FOO and BAR clawed back amounts reflect the two-asset withdrawal amounts from redeeming all holder's LPtokens in the AMM pool.)
- `tfClawTwoAssets` is used to determine if BAR will be clawed back or goes back to the holder.

##### 2.3.3.5 Clawback token from a pool containing XRP

```
{
  "TransactionType": "AMMClawback",
  "Account": "rPdYxU9dNkbzC5Y2h4jLbVJ3rMRrk7WVRL",
  "Holder": "rvYAfWj5gh67oV6fW32ZzP3Aw4Eubs59B",
  "Asset": {
      "currency" : "FOO",
      "issuer" : "rPdYxU9dNkbzC5Y2h4jLbVJ3rMRrk7WVRL"
  },
  "Asset2" : {
      "currency" : "XRP",
  },
  "Amount": {
      "currency" : "FOO",
      "issuer" : "rPdYxU9dNkbzC5Y2h4jLbVJ3rMRrk7WVRL",
      "value" : "1000"
  }
}
```

- In this example, the issuer will clawback 1000 FOO from the AMM pool FOO/XRP. And the corresponding proportion of XRP will go back to the holder.
- Notice XRP can not be clawed back.
