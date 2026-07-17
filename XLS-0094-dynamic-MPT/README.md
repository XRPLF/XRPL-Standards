<pre>
  xls: 94
  title: Dynamic Multi-Purpose Tokens
  description: This amendment enables selected fields and flags of MPTokenIssuance to be updated after creation.
  proposal-from: https://github.com/XRPLF/XRPL-Standards/discussions/289
  author: Yinyi Qian <yqian@ripple.com>
  status: Draft
  category: Amendment
  created: 2025-06-09
</pre>

# Dynamic Multi-Purpose Tokens

## Abstract

This proposal introduces a new amendment `DynamicMPT` as an extension to [XLS-33 Multi-Purpose Tokens](https://github.com/XRPLF/XRPL-Standards/blob/master/XLS-0033-multi-purpose-tokens/README.md). Dynamic Multi-Purpose Tokens (Dynamic MPTs) allow specific fields and MPT issuance flags within an `MPTokenIssuance` to be modified after creation via the `MPTokenIssuanceSet` transaction. By default, `MPTokenMetadata`, `TransferFee`, and a defined set of MPT issuance flags remain mutable for the life of the issuance. Issuers may instead choose to permanently make any of these fields or flags immutable — at creation, or at any later point — by setting the corresponding bit in a new `ImmutableFlags` field. Once a bit is set in `ImmutableFlags`, the corresponding field or flag can never be modified again. This accommodates evolving token use cases and compliance demands while giving issuers a way to make firm, permanent commitments about their issuance's behavior.

## 1. Overview

This proposal introduces:

- Transaction update for `MPTokenIssuanceCreate`:
  - A new optional field:
    - `sfImmutableFlags` - permanently makes specific fields or flags immutable.

- Ledger object update in `MPTokenIssuance`:
  - A new optional field:
    - `sfImmutableFlags` - records which fields or flags are immutable.

- Transaction update for `MPTokenIssuanceSet`:
  - New optional fields:
    - `sfMPTokenMetadata` - updates `MPTokenMetadata`
    - `sfTransferFee` - updates `TransferFee`
    - `sfImmutableFlags` - permanently makes specific fields or flags immutable
  - A set of new values under `sfFlags` to set MPT issuance flags.

- The target flags or fields to be set or updated for the ledger object `MPTokenIssuance`:
  - Field: `sfMPTokenMetadata`
  - Field: `sfTransferFee`
  - Bits of `sfFlags`:
    - `lsfMPTCanLock`
    - `lsfMPTRequireAuth`
    - `lsfMPTCanEscrow`
    - `lsfMPTCanTrade`
    - `lsfMPTCanTransfer`
    - `lsfMPTCanClawback`
    - `lsfMPTCanHoldConfidentialBalance` (from XLS-96 Confidential MPT)

This feature will require an amendment, `DynamicMPT`.
Setting `lsfMPTCanHoldConfidentialBalance` also requires the `ConfidentialTransfer` amendment to be enabled.

## 2. Declaring Immutability via MPTokenIssuanceCreate

By default without declaring `sfImmutableFlags`:

- `MPTokenMetadata` and `TransferFee` may be freely modified via `MPTokenIssuanceSet`.
- Each of the MPT issuance flags listed below may be enabled (one-way) via `MPTokenIssuanceSet` after issuance.

Declaring immutablity via `sfImmutableFlags`:

- Flags set in `sfImmutableFlags` indicates the corresponding field/flag is immutable. The issuer can not modify the field/flag via `MPTokenIssuanceSet` after issuance.

### 2.1. New Optional Field: `ImmutableFlags`

| Field Name       | Required? | JSON Type | Internal Type | Description                                                        |
| ---------------- | :-------: | :-------: | :-----------: | ------------------------------------------------------------------ |
| `ImmutableFlags` |           | `number`  |   `UInt32`    | Indicates specific fields or flags that are permanently immutable. |

To declare which fields or flags are immutable.

### Bit Layout of `ImmutableFlags`

Transaction-level bits are prefixed `tif`. The corresponding on-ledger bits (prefixed `lsif`) share the same numeric values — see [Section 3](#bit-layout-of-immutableflags-on-ledger).

| Flag Name                          |  Hex Value   | Decimal Value | Description                                                                       |
| ---------------------------------- | :----------: | :-----------: | --------------------------------------------------------------------------------- |
| [Reserved]                         | `0x00000001` |       1       | Reserved.                                                                         |
| `tifMPTCanLock`                    | `0x00000002` |       2       | Make flag `lsfMPTCanLock` immutable.                                              |
| `tifMPTRequireAuth`                | `0x00000004` |       4       | Make flag `lsfMPTRequireAuth` immutable.                                          |
| `tifMPTCanEscrow`                  | `0x00000008` |       8       | Make flag `lsfMPTCanEscrow` immutable.                                            |
| `tifMPTCanTrade`                   | `0x00000010` |      16       | Make flag `lsfMPTCanTrade` immutable.                                             |
| `tifMPTCanTransfer`                | `0x00000020` |      32       | Make flag `lsfMPTCanTransfer` immutable.                                          |
| `tifMPTCanClawback`                | `0x00000040` |      64       | Make flag `lsfMPTCanClawback` immutable.                                          |
| `tifMPTCanHoldConfidentialBalance` | `0x00000080` |      128      | Make flag `lsfMPTCanHoldConfidentialBalance` immutable. (XLS-96 Confidential MPT) |
| `tifMPTMetadata`                   | `0x00010000` |     65536     | Make field `MPTokenMetadata` immutable.                                           |
| `tifMPTTransferFee`                | `0x00020000` |    131072     | Make field `TransferFee` immutable.                                               |

### 2.2. Failure Conditions (`MPTokenIssuanceCreate` and `MPTokenIssuanceSet`)

1. `ImmutableFlags` is `0`, or contains a bit not defined above. (`temINVALID_FLAG`)
2. `ImmutableFlags` is present but `featureDynamicMPT` is disabled. (`temDISABLED`)
3. `tifMPTCanHoldConfidentialBalance` is set but `featureConfidentialTransfer` or `featureDynamicMPT` is not enabled. (`temDISABLED`)

## 3. On-Ledger Data Structure Change

This proposal adds a new optional field, `ImmutableFlags` to the `sfMPTokenIssuance` ledger object.

### 3.1. New Optional Field: `ImmutableFlags`

| Field Name       | Required? | JSON Type | Internal Type |
| ---------------- | :-------: | :-------: | :-----------: |
| `ImmutableFlags` |           | `number`  |   `UINT32`    |

The field is type `soeDEFAULT`. So if it is present in the ledger object, it must not be 0.
Being absent is equivalent to being 0.

### Bit Layout of `ImmutableFlags` (On-Ledger)

On-ledger bits are prefixed `lsif`, and share the same numeric values as the corresponding `tif` bits in [Section 2](#bit-layout-of-immutableflags).

| Flag Name                           |  Hex Value   | Decimal Value | Description                                                                           |
| ----------------------------------- | :----------: | :-----------: | ------------------------------------------------------------------------------------- |
| [Reserved]                          | `0x00000001` |       1       | Reserved.                                                                             |
| `lsifMPTCanLock`                    | `0x00000002` |       2       | Indicate flag `lsfMPTCanLock` immutable.                                              |
| `lsifMPTRequireAuth`                | `0x00000004` |       4       | Indicate flag `lsfMPTRequireAuth` immutable.                                          |
| `lsifMPTCanEscrow`                  | `0x00000008` |       8       | Indicate flag `lsfMPTCanEscrow` immutable.                                            |
| `lsifMPTCanTrade`                   | `0x00000010` |      16       | Indicate flag `lsfMPTCanTrade` immutable.                                             |
| `lsifMPTCanTransfer`                | `0x00000020` |      32       | Indicate flag `lsfMPTCanTransfer` immutable.                                          |
| `lsifMPTCanClawback`                | `0x00000040` |      64       | Indicate flag `lsfMPTCanClawback` immutable.                                          |
| `lsifMPTCanHoldConfidentialBalance` | `0x00000080` |      128      | Indicate flag `lsfMPTCanHoldConfidentialBalance` immutable. (XLS-96 Confidential MPT) |
| `lsifMPTMetadata`                   | `0x00010000` |     65536     | Indicate field `MPTokenMetadata` immutable.                                           |
| `lsifMPTTransferFee`                | `0x00020000` |    131072     | Indicate field `TransferFee` immutable.                                               |

## 4. `MPTokenIssuanceSet` Transaction Update

This proposal extends the functionality of the `MPTokenIssuanceSet` transaction, allowing the issuer to modify `MPTokenMetadata` and `TransferFee`, enable MPT issuance flags, and permanently make any of these immutable via `ImmutableFlags`. The `ImmutableFlags` provided in this transaction adds those bit to the current ledger object's `ImmutableFlags`, it is not a complete replacement.

For details on the original `MPTokenIssuanceSet` transaction see: [**The MPTokenIssuanceSet Transaction**](https://github.com/XRPLF/XRPL-Standards/blob/master/XLS-0033-multi-purpose-tokens/README.md#33-the-mptokenissuanceset-transaction)

### 4.1. New Fields

| Field Name        | Required? | JSON Type | Internal Type |
| ----------------- | :-------: | :-------: | :-----------: |
| `MPTokenMetadata` |           | `string`  |    `BLOB`     |

New metadata to replace the existing value. The transaction will be rejected if `lsifMPTMetadata` has been set in `ImmutableFlags`. Setting an empty `MPTokenMetadata` removes the field.

---

| Field Name    | Required? | JSON Type | Internal Type |
| ------------- | :-------: | :-------: | :-----------: |
| `TransferFee` |           | `number`  |   `UINT16`    |

New transfer fee value. The transaction will be rejected if `lsifMPTTransferFee` has been set in `ImmutableFlags`. Setting `TransferFee` to zero removes the field.

---

| Field Name       | Required? | JSON Type | Internal Type |
| ---------------- | :-------: | :-------: | :-----------: |
| `ImmutableFlags` |           | `number`  |   `UINT32`    |

To declare which fields or flags are immutable.
Once a bit is set, the corresponding field or flag can never be set or modified again. The bit layout is the same as `ImmutableFlags` in `MPTokenIssuanceCreate`.
Whether it was made immutable at creation through `MPTokenIssuanceCreate` or afterward via `MPTokenIssuanceSet`. Submitting a bit that is already set is harmless and has no additional effect.

### 4.2. New `Flags` Values

These flags are added to the the `sfFlags` field of `MPTokenIssuanceSet` (Original values see in [XLS-33: Transaction-specific Fields](https://github.com/XRPLF/XRPL-Standards/tree/master/XLS-0033-multi-purpose-tokens#3311-mptokenissuanceset-flags)). This proposal adds the following new `Flags` values to set MPT issuance flags. These flags are one-way: once set, they cannot be unset by `MPTokenIssuanceSet`.

| Flag Name                            |  Hex Value   | Decimal Value | Description                                                                                                                         |
| ------------------------------------ | :----------: | :-----------: | ----------------------------------------------------------------------------------------------------------------------------------- |
| `tfMPTSetCanLock`                    | `0x00000004` |       4       | Sets the `lsfMPTCanLock` flag. Enables the token to be locked both individually and globally.                                       |
| `tfMPTSetRequireAuth`                | `0x00000008` |       8       | Sets the `lsfMPTRequireAuth` flag. Requires individual holders to be authorized.                                                    |
| `tfMPTSetCanEscrow`                  | `0x00000010` |      16       | Sets the `lsfMPTCanEscrow` flag. Allows holders to place balances into escrow.                                                      |
| `tfMPTSetCanTrade`                   | `0x00000020` |      32       | Sets the `lsfMPTCanTrade` flag. Allows holders to trade balances on the XRPL DEX.                                                   |
| `tfMPTSetCanTransfer`                | `0x00000040` |      64       | Sets the `lsfMPTCanTransfer` flag. Allows tokens to be transferred to non-issuer accounts.                                          |
| `tfMPTSetCanClawback`                | `0x00000080` |      128      | Sets the `lsfMPTCanClawback` flag. Enables the issuer to claw back tokens via `Clawback` or `AMMClawback` transactions.             |
| `tfMPTSetCanHoldConfidentialBalance` | `0x00000100` |      256      | Sets the `lsfMPTCanHoldConfidentialBalance` flag. Enables the token to be held in a confidential balance. (XLS-96 Confidential MPT) |

**Terminology**:
We will call those flags `tfMPTSet*` as **capability-setting flags**.

**Note**:

- An MPT issuance flag can only be enabled by `MPTokenIssuanceSet` if the corresponding `lsif` bit is **not** set in the `MPTokenIssuance` object's `ImmutableFlags`.
- If an MPT issuance flag is already enabled, re-enabling it is valid and has no additional effect.
- A single `MPTokenIssuanceSet` transaction may enable multiple MPT issuance flags, as long as none of them have been made immutable via `ImmutableFlags`.
- Setting the flag and setting `ImmutableFlags` in the same transaction is allowed, and is atomic. We only check the existing ledger object's `ImmutableFlags` when validating if it is immutable. For example, setting `lsfMPTCanLock` and `lsifMPTCanLock` in the same transaction is allowed, setting `lsfMPTCanLock` will succeed because on the ledger, `lsifMPTCanLock` is not set yet. After this transaction, the ledger object will have both `lsfMPTCanLock` and `lsifMPTCanLock` set.

---

### 4.2. Failure Conditions

1. `MPTokenHolder` is present together with capability-setting flags (e.g. `tfMPTSetCanLock`, etc.), `MPTokenMetadata`, `TransferFee`, or `ImmutableFlags` (`temMALFORMED`)
2. `tfMPTLock` or `tfMPTUnlock` is set together with a capability-setting flag, `MPTokenMetadata`, `TransferFee`, or `ImmutableFlags` (`temMALFORMED`)
3. `TransferFee` exceeds the limit, which is 50000 (`temBAD_TRANSFER_FEE`)
4. `MPTokenMetadata` length exceeds the limit, which is 1024 (`temMALFORMED`)
5. A capability-setting flag, `MPTokenMetadata`, `TransferFee`, or `ImmutableFlags` is present but `featureDynamicMPT` is disabled (`temDISABLED`)
6. `ImmutableFlags` contains `tifMPTCanHoldConfidentialBalance` but `featureConfidentialTransfer` is disabled (`temDISABLED`)
7. `ImmutableFlags` is `0`, or contains a bit not defined. (`temINVALID_FLAG`)
8. A capability-setting flag is set, but the corresponding `lsif` bit is already set in `ImmutableFlags` (`tecNO_PERMISSION`)
9. `MPTokenMetadata` is present, but `lsifMPTMetadata` is set in `ImmutableFlags` (`tecNO_PERMISSION`)
10. `TransferFee` is present, but `lsifMPTTransferFee` is set in `ImmutableFlags` (`tecNO_PERMISSION`)
11. A non-zero `TransferFee` is included, `lsfMPTCanTransfer` is not already set on the ledger, and this same transaction does not also enable it via `tfMPTSetCanTransfer` (`tecNO_PERMISSION`)

### 4.3. `TransferFee` Modification Rules

The ability to modify `TransferFee` depends on two conditions:

- `lsfMPTCanTransfer`: must already be set on the ledger, **or** be enabled by this same transaction via `tfMPTSetCanTransfer`, in order to set a non-zero `TransferFee`.
- `lsifMPTTransferFee`: must **not** be set in `ImmutableFlags`, in order to modify `TransferFee` at all (zero or non-zero).

#### The rules break down as follows:

**Case 1**: `lsfMPTCanTransfer` not set, and not being enabled by this transaction:

- Setting `TransferFee` to zero: allowed (removes the field, if present), unless `lsifMPTTransferFee` has been set (making `TransferFee` immutable).
- Setting `TransferFee` to a non-zero value: always invalid, returns `tecNO_PERMISSION`.

**Case 2**: `lsfMPTCanTransfer` already set on the ledger, **or** being enabled by this same transaction via `tfMPTSetCanTransfer`:

- Setting `TransferFee` to any value (zero or non-zero): allowed, unless `lsifMPTTransferFee` has been set (making `TransferFee` immutable).

**Note**: enabling `lsfMPTCanTransfer` and setting a non-zero `TransferFee` **in the same transaction** is supported — there is no requirement to submit two separate transactions.

## 5. Examples

### 5.1. Example 1: Metadata mutable by default, then made immutable

#### 5.1.1. `MPTokenIssuanceCreate` Transaction

```js
{
  "TransactionType": "MPTokenIssuanceCreate",
  "Account": "rIssuer...",
  "AssetScale": "2",
  "MaximumAmount": "100000000",
  "MPTokenMetadata": "464F4F"
}
```

- No `ImmutableFlags` is set, so `MPTokenMetadata` remains mutable by default.

#### 5.1.2. `MPTokenIssuanceSet` Transactions

**Sample 1** (successful):

```js
{
  "TransactionType": "MPTokenIssuanceSet",
  "Account": "rIssuer...",
  "MPTokenMetadata": "575C5C"
}
```

- `MPTokenMetadata` was never made immutable, so this updates the metadata from `464F4F` to `575C5C`.

**Sample 2** (successful): Alice now decides to make the metadata immutable at its current value.

```js
{
  "TransactionType": "MPTokenIssuanceSet",
  "Account": "rIssuer...",
  "ImmutableFlags": 65536 // tifMPTMetadata
}
```

- `MPTokenMetadata` (currently `575C5C`) is now permanently immutable.

**Sample 3** (rejected):

```js
{
  "TransactionType": "MPTokenIssuanceSet",
  "Account": "rIssuer...",
  "MPTokenMetadata": "AABBCC"
}
```

- This is rejected because `lsifMPTMetadata` is now set in `ImmutableFlags`.

### 5.2. Example 2: Making a capability immutable at creation

#### 5.2.1. `MPTokenIssuanceCreate` Transaction

```js
{
  "TransactionType": "MPTokenIssuanceCreate",
  "Account": "rIssuer...",
  "AssetScale": "2",
  "MaximumAmount": "100000000",
  "ImmutableFlags": 4 // tifMPTRequireAuth
}
```

- `tifMPTRequireAuth` is set, permanently preventing `lsfMPTRequireAuth` from ever being set. All other MPT issuance flags remain mutable by default.

#### 5.2.2. `MPTokenIssuanceSet` Transaction

**Sample 1** (successful):

```js
{
  "TransactionType": "MPTokenIssuanceSet",
  "Account": "rIssuer...",
  "Flags": 48 // tfMPTSetCanEscrow (0x00000010) + tfMPTSetCanTrade (0x00000020)
}
```

- `lsfMPTCanEscrow` and `lsfMPTCanTrade` were never made immutable, so both are set by this transaction.

**Sample 2** (rejected):

```js
{
  "TransactionType": "MPTokenIssuanceSet",
  "Account": "rIssuer...",
  "Flags": 8 // tfMPTSetRequireAuth
}
```

- This is rejected because `tifMPTRequireAuth` was set at creation, permanently preventing `lsfMPTRequireAuth` from being set.

### 5.3. Example 3: `TransferFee` and `lsfMPTCanTransfer`

#### 5.3.1. `MPTokenIssuanceCreate` Transaction

```js
{
  "TransactionType": "MPTokenIssuanceCreate",
  "Account": "rIssuer...",
  "AssetScale": "2",
  "MaximumAmount": "100000000",
  "Flags": 2  // tfMPTCanLock
}
```

- `tfMPTCanTransfer` is not set, so `TransferFee` **MUST NOT** be present.
- No `ImmutableFlags` is set, so `TransferFee` and all MPT issuance flags remain mutable by default.

#### 5.3.2. `MPTokenIssuanceSet` Transactions

**Sample 1** (rejected):

```js
{
  "TransactionType": "MPTokenIssuanceSet",
  "Account": "rIssuer...",
  "TransferFee": 200
}
```

- Rejected: a non-zero `TransferFee` cannot be set unless `lsfMPTCanTransfer` is already set, or is being enabled by this same transaction.

**Sample 2** (successful): enabling `lsfMPTCanTransfer` and setting a non-zero `TransferFee` together.

```js
{
  "TransactionType": "MPTokenIssuanceSet",
  "Account": "rIssuer...",
  "Flags": 64, // tfMPTSetCanTransfer
  "TransferFee": 200
}
```

- Both effects apply atomically: `lsfMPTCanTransfer` is enabled, and `TransferFee` is set to 200 in the same transaction.

**Sample 3** (successful): Alice now permanently makes the transfer fee immutable at its current value.

```js
{
  "TransactionType": "MPTokenIssuanceSet",
  "Account": "rIssuer...",
  "ImmutableFlags": 131072 // tifMPTTransferFee
}
```

- `TransferFee` (currently 200) can no longer be changed.

**Sample 4** (rejected):

```js
{
  "TransactionType": "MPTokenIssuanceSet",
  "Account": "rIssuer...",
  "TransferFee": 0
}
```

- Rejected: `lsifMPTTransferFee` is now set in `ImmutableFlags`, so `TransferFee` can no longer be modified, even to remove it.

## Rationale

Dynamic MPT gives issuers control over which parts of their token issuance can evolve after creation, while defaulting to maximum flexibility: `MPTokenMetadata`, `TransferFee`, and MPT issuance flags are mutable unless the issuer takes explicit action to make them immutable. This "mutable by default, immutable on demand" design lets issuers respond to changing business needs — adjusting metadata, tuning a transfer fee, or enabling a capability that wasn't needed at launch — without requiring every possible future need to be anticipated and pre-declared at issuance time.

Making fields or flags immutable via `ImmutableFlags` is available both at creation and at any later point via `MPTokenIssuanceSet`, letting issuers progressively make firmer commitments as their token's design stabilizes — for example, making metadata immutable once its final content is set, while leaving other fields open for longer.

MPT issuance flag mutability remains intentionally one-way: once enabled via `MPTokenIssuanceSet`, a flag cannot be disabled. This preserves the issuer's ability to opt into additional issuance behavior without ever retracting behavior that holders, integrations, or compliance workflows may have relied on. Making a flag immutable via `ImmutableFlags` (whether before or after it is enabled) makes that one-way guarantee permanent and auditable on-ledger.

## Security

Only the issuer of the `MPTokenIssuance` can use `MPTokenIssuanceSet` to modify `MPTokenMetadata` or `TransferFee`, enable MPT issuance flags, or set `ImmutableFlags`.

`ImmutableFlags` bits are monotonic: once set, a bit is never cleared by any transaction, so a field or flag that has been made immutable remains immutable for the life of the issuance, regardless of who submits subsequent `MPTokenIssuanceSet` transactions.

MPT issuance flags are one-way and cannot be disabled through `MPTokenIssuanceSet` after being enabled, whether or not the corresponding `ImmutableFlags` bit is also set. Enabling a flag and immediately making it immutable via `ImmutableFlags` in the same transaction is supported and introduces no additional risk: the flag was already permanent once enabled, so making it immutable merely records that fact rather than changing what is achievable.
