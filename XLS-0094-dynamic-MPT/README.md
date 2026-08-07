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

This proposal introduces a new amendment `DynamicMPT` as an extension to [XLS-33 Multi-Purpose Tokens](https://github.com/XRPLF/XRPL-Standards/blob/master/XLS-0033-multi-purpose-tokens/README.md). Dynamic Multi-Purpose Tokens (Dynamic MPTs) enable specific fields and MPT issuance flags within an `MPTokenIssuance` to be declared as mutable at the time of creation. By enabling controlled mutability, this feature accommodates evolving token use cases and compliance demands. Mutable fields can be modified via the `MPTokenIssuanceSet` transaction, while mutable MPT issuance flags can be enabled one time and then become immutable.

## 1. Overview

This proposal introduces:

- Transaction update for `MPTokenIssuanceCreate`:
  - A new optional field:
    - `sfMutableFlags` - indicates specific fields or flags are mutable after issuance.

- Ledger object update in `MPTokenIssuance`:
  - A new optional field:
    - `sfMutableFlags` - indicates specific fields or flags are mutable after issuance.

- Transaction update for `MPTokenIssuanceSet`:
  - New optional fields:
    - `sfMPTokenMetadata` - updates `MPTokenMetadata`
    - `sfTransferFee` - updates `TransferFee`
    - `sfMutableFlags` - enables MPT issuance flags that were declared mutable (e.g. `tmfMPTSetCanLock`)

This feature will require an amendment, `DynamicMPT`.

## 2. Declaring Mutability via `MPTokenIssuanceCreate`

If issuers want the ability to modify certain fields or flags after issuance, they must explicitly declare those fields or flags as mutable when creating the `MPTokenIssuance`.
Only a limited set of fields and flags may be declared mutable; all other fields remain permanently immutable.

### 2.1. Declaring Field Mutability and Flag Enablement

Issuers can specify mutability during `MPTokenIssuanceCreate` via the optional `MutableFlags` field.

Bits in `MutableFlags` indicate specific fields may be modified after issuance, or specific MPT issuance flags may be enabled after issuance. MPT issuance flags are one-way: once enabled, they cannot be disabled by `MPTokenIssuanceSet`. The fields or flags include:

- Fields:
  - `MPTokenMetadata`
  - `TransferFee`
- Flags:
  - Refer to [XLS-33 Multi-Purpose Tokens: Transaction-specific Fields](https://github.com/XRPLF/XRPL-Standards/tree/master/XLS-0033-multi-purpose-tokens#3111-transaction-specific-fields) (under `Flags` field)

#### 2.2. New Optional Field: MutableFlags

| Field Name     | Required? | JSON Type | Internal Type | Description                               |
| -------------- | :-------: | :-------: | :-----------: | ----------------------------------------- |
| `MutableFlags` |           | `number`  |   `UInt32`    | Indicate specific fields or flags mutable |

### Bit Layout of `MutableFlags` — Declaring Mutability at Creation (`MPTokenIssuanceCreate`)

`MutableFlags` are prefixed with `tmf` to clearly distinguish them from standard `tf` prefix used for `Flags`.

| Flag Name                    |  Hex Value   | Decimal Value | Description                                                                                  |
| ---------------------------- | :----------: | :-----------: | -------------------------------------------------------------------------------------------- |
| [Reserved]                   | `0x00000001` |       1       | [Reserved; To align with `Flags` values, the `MutableFlags` value starts from `0x00000002`.] |
| `tmfMPTCanEnableCanLock`     | ️`0x00000002` |       2       | Allows flag `lsfMPTCanLock` to be enabled after issuance                                     |
| `tmfMPTCanEnableRequireAuth` | ️`0x00000004` |       4       | Allows flag `lsfMPTRequireAuth` to be enabled after issuance                                 |
| `tmfMPTCanEnableCanEscrow`   | `0x00000008` |       8       | Allows flag `lsfMPTCanEscrow` to be enabled after issuance                                   |
| `tmfMPTCanEnableCanTrade`    | `0x00000010` |      16       | Allows flag `lsfMPTCanTrade` to be enabled after issuance                                    |
| `tmfMPTCanEnableCanTransfer` | ️`0x00000020` |      32       | Allows flag `lsfMPTCanTransfer` to be enabled after issuance                                 |
| `tmfMPTCanEnableCanClawback` | ️`0x00000040` |      64       | Allows flag `lsfMPTCanClawback` to be enabled after issuance                                 |
| `tmfMPTCanMutateMetadata`    | `0x00010000` |     65536     | Allows field `MPTokenMetadata` to be modified                                                |
| `tmfMPTCanMutateTransferFee` | `0x00020000` |    131072     | Allows field `TransferFee` to be modified                                                    |

**Note**: Flag value `0x0001` is used by `lsfMPTLocked`. It is not a valid value for `MutableFlags`.

### 2.3. Failure Conditions

| Failure Condition                                             | Error Code        |
| ------------------------------------------------------------- | ----------------- |
| Invalid values in `MutableFlags` field                        | `temINVALID_FLAG` |
| `MutableFlags` is present but `featureDynamicMPT` is disabled | `temDISABLED`     |

## 3. On-Ledger Data Structure Change

This proposal introduces updates to the `MPTokenIssuance` ledger object, including a new optional field `MutableFlags`.

## 3.1. New Optional Field: `MutableFlags`

A new optional field, `MutableFlags` (SField `sfMutableFlags`), is added to the `MPTokenIssuance` ledger object.

| Field Name     | Required? | JSON Type | Internal Type |
| -------------- | :-------: | :-------: | :-----------: |
| `MutableFlags` |           | `number`  |   `UINT32`    |

### Bit Layout of `MutableFlags` - Recording Mutability On-Ledger (`MPTokenIssuance`)

On-ledger `MutableFlags` are prefixed with `lmf` to clearly distinguish them from standard `lsf` prefix used for `Flags`.

| Flag Name                     |  Hex Value   | Decimal Value | Description                                                                                  |
| ----------------------------- | :----------: | :-----------: | -------------------------------------------------------------------------------------------- |
| [Reserved]                    | ️`0x00000001` |       1       | [Reserved; To align with `Flags` values, the `MutableFlags` value starts from `0x00000002`.] |
| `lsmfMPTCanEnableCanLock`     | ️`0x00000002` |       2       | Allows flag `lsfMPTCanLock` to be enabled after issuance                                     |
| `lsmfMPTCanEnableRequireAuth` | ️`0x00000004` |       4       | Allows flag `lsfMPTRequireAuth` to be enabled after issuance                                 |
| `lsmfMPTCanEnableCanEscrow`   | `0x00000008` |       8       | Allows flag `lsfMPTCanEscrow` to be enabled after issuance                                   |
| `lsmfMPTCanEnableCanTrade`    | `0x00000010` |      16       | Allows flag `lsfMPTCanTrade` to be enabled after issuance                                    |
| `lsmfMPTCanEnableCanTransfer` | ️`0x00000020` |      32       | Allows flag `lsfMPTCanTransfer` to be enabled after issuance                                 |
| `lsmfMPTCanEnableCanClawback` | ️`0x00000040` |      64       | Allows flag `lsfMPTCanClawback` to be enabled after issuance                                 |
| `lsmfMPTCanMutateMetadata`    | `0x00010000` |     65536     | Allows field `MPTokenMetadata` to be modified                                                |
| `lsmfMPTCanMutateTransferFee` | `0x00020000` |    131072     | Allows field `TransferFee` to be modified                                                    |

**Note**: Flag value `0x0001` is used by `lsfMPTLocked`. It is not a valid value for `MutableFlags`.

## 4. `MPTokenIssuanceSet` Transaction Update

This proposal extends the functionality of the `MPTokenIssuanceSet` transaction, allowing the issuer of the `MPTokenIssuance` to update fields that were explicitly marked as mutable during creation and to enable MPT issuance flags that were explicitly declared mutable.

For details on the original MPTokenIssuanceSet transaction see: [**The MPTokenIssuanceSet Transaction**](https://github.com/XRPLF/XRPL-Standards/blob/master/XLS-0033-multi-purpose-tokens/README.md#33-the-mptokenissuanceset-transaction)

### 4.1. New Fields

| Field Name        | Required? | JSON Type | Internal Type |
| ----------------- | :-------: | :-------: | :-----------: |
| `MPTokenMetadata` |           | `string`  |    `BLOB`     |

New metadata to replace the existing value.
The transaction will be rejected if `lsmfMPTCanMutateMetadata` was not set in `MutableFlags`.
Setting an empty `MPTokenMetadata` removes the field.

---

| Field Name    | Required? | JSON Type | Internal Type |
| ------------- | :-------: | :-------: | :-----------: |
| `TransferFee` |           | `number`  |   `UINT16`    |

New transfer fee value.
The transaction will be rejected if `lsmfMPTCanMutateTransferFee` was not set in `MutableFlags`.
Setting `TransferFee` to zero removes the field.

---

| Field Name     | Required? | JSON Type | Internal Type |
| -------------- | :-------: | :-------: | :-----------: |
| `MutableFlags` |           | `number`  |   `UINT32`    |

Enable MPT issuance flags that were marked as mutable. These flags are one-way: once enabled, they are immutable.

**The valid `MutableFlags` values**:

The `MutableFlags` use `tmf` as prefix.

| Flag Name              |  Hex Value   | Decimal Value | Description                                                                                                             |
| ---------------------- | :----------: | :-----------: | ----------------------------------------------------------------------------------------------------------------------- |
| `tmfMPTSetCanLock`     | ️`0x00000001` |       1       | Sets the `lsfMPTCanLock` flag. Enables the token to be locked both individually and globally.                           |
| `tmfMPTSetRequireAuth` | ️`0x00000002` |       2       | Sets the `lsfMPTRequireAuth` flag. Requires individual holders to be authorized.                                        |
| `tmfMPTSetCanEscrow`   | `0x00000004` |       4       | Sets the `lsfMPTCanEscrow` flag. Allows holders to place balances into escrow.                                          |
| `tmfMPTSetCanTrade`    | `0x00000008` |       8       | Sets the `lsfMPTCanTrade` flag. Allows holders to trade balances on the XRPL DEX.                                       |
| `tmfMPTSetCanTransfer` | ️`0x00000010` |      16       | Sets the `lsfMPTCanTransfer` flag. Allows tokens to be transferred to non-issuer accounts.                              |
| `tmfMPTSetCanClawback` | ️`0x00000020` |      32       | Sets the `lsfMPTCanClawback` flag. Enables the issuer to claw back tokens via `Clawback` or `AMMClawback` transactions. |

**Note**:

- An MPT issuance flag in the `MPTokenIssuance` object's `Flags` field can only be enabled by `MPTokenIssuanceSet` if the corresponding `lsmfMPTCanEnable*` permission flag is already set in the `MPTokenIssuance` object's `MutableFlags` field.
- If an MPT issuance flag is already enabled and its corresponding `lsmfMPTCanEnable*` permission flag is set, re-enabling the flag is valid and has no additional effect.
- A single `MPTokenIssuanceSet` transaction may enable multiple MPT issuance flags, as long as each requested flag has its corresponding `lsmfMPTCanEnable*` permission flag set in the `MPTokenIssuance` object's `MutableFlags`.

---

### 4.2. Failure Conditions

1. `MutableFlags` contains invalid value (0 is invalid as well) (`temINVALID_FLAG`)
2. `MPTokenHolder` is provided when `MutableFlags`, `MPTokenMetadata`, or `TransferFee` is present (`temMALFORMED`)
3. `Flags` (except `tfUniversal`) is provided when `MutableFlags`, `MPTokenMetadata`, or `TransferFee` is present (`temMALFORMED`)
4. `TransferFee` exceeds the limit, which is 50000 (`temBAD_TRANSFER_FEE`)
5. `MPTokenMetadata` length exceeds the limit, which is 1024 (`temMALFORMED`)
6. `MutableFlags`, `MPTokenMetadata`, or `TransferFee` is present but `featureDynamicMPT` is disabled (`temDISABLED`)
7. `MPTokenIssuanceID` does not exist (`tecOBJECT_NOT_FOUND`)
8. `Account` is not the issuer of the target `MPTokenIssuance` (`tecNO_PERMISSION`)
9. `MutableFlags` attempts to enable flags not declared as mutable (`tecNO_PERMISSION`)
10. `MPTokenMetadata` is present but was not marked as mutable (`tecNO_PERMISSION`)
11. `TransferFee` is present but was not marked as mutable (`tecNO_PERMISSION`)
12. Including a non-zero `TransferFee` when `lsfMPTCanTransfer` was not already set (`tecNO_PERMISSION`)

### 4.3. `TransferFee` Modification Rules

Since `TransferFee` **MUST NOT** be present if `tfMPTCanTransfer` flag is not set during `MPTokenIssuanceCreate`, there are extra rules we should follow when it comes to mutating the `TransferFee` field.

The ability to modify `TransferFee` depends on two flags:

- `lsfMPTCanTransfer` : must already be set to allow any non-zero `TransferFee`.
- `lsmfMPTCanMutateTransferFee`: must be set at creation (`MPTokenIssuanceCreate`) to allow any modification of the `TransferFee` field.

If `lsmfMPTCanEnableCanTransfer` is set, `lsfMPTCanTransfer` can be enabled through `tmfMPTSetCanTransfer`. Once enabled, it cannot be disabled by `MPTokenIssuanceSet`.

#### Because these flags overlap in function, the rules break down as follows:

**Case1**: `lsfMPTCanTransfer` not set:

- Setting `TransferFee` to zero:
  - If `lsmfMPTCanMutateTransferFee` is set: allowed; removes the `TransferFee` field.
  - If `lsmfMPTCanMutateTransferFee` is not set: returns `tecNO_PERMISSION`.
- Setting `TransferFee` to a non-zero value:
  - Always invalid: returns `tecNO_PERMISSION`, regardless of `lsmfMPTCanMutateTransferFee`.
  - ❗**Note**: Even including `tmfMPTSetCanTransfer` in the same transaction returns `tecNO_PERMISSION`.
    - `lsfMPTCanTransfer` must already be set before assigning a non-zero `TransferFee`.

**Case2**: `lsfMPTCanTransfer` set:

- Setting `TransferFee` to a non-zero value:
  - If `lsmfMPTCanMutateTransferFee` is set: allowed; modifies the `TransferFee` field.
  - If `lsmfMPTCanMutateTransferFee` is not set: returns `tecNO_PERMISSION`.
- Setting `TransferFee` to zero:
  - If `lsmfMPTCanMutateTransferFee` is set: allowed; removes the `TransferFee` field.
  - If `lsmfMPTCanMutateTransferFee` is not set: returns `tecNO_PERMISSION`.

## 5. Examples

### 5.1. Example 1

#### 5.1.1. `MPTokenIssuanceCreate` Transaction

```js
{
  "TransactionType": "MPTokenIssuanceCreate",
  "Account": "rIssuer...",
  "AssetScale": "2",
  "MaximumAmount": "100000000",
  "MutableFlags": 65536, // tmfMPTCanMutateMetadata
  "MPTokenMetadata": "464F4F",
  "TransferFee": 100
}
```

- `tmfMPTCanMutateMetadata` is set, indicating the `MPTokenMetadata` field can be modified.

#### 5.1.2. `MPTokenIssuanceSet` Transaction

**Sample 1**(successful):

```js
{
  "TransactionType": "MPTokenIssuanceSet",
  "Account": "rIssuer...",
  "MPTokenMetadata": "575C5C"
}
```

- `MPTokenMetadata` was set mutable, so this will update the metadata from `464F4F` to `575C5C`.

**Sample 2**(rejected):

```js
{
  "TransactionType": "MPTokenIssuanceSet",
  "Account": "rIssuer...",
  "MutableFlags": 1, // tmfMPTSetCanLock (0x0001)
  "MPTokenMetadata": "575C5C"
}
```

- This transaction attempts to set the `lsfMPTCanLock` flag by including `tmfMPTSetCanLock` in the `MutableFlags` field. However, the mutation will be rejected because `lsfMPTCanLock` was not marked during creation.

### 5.2. Example 2

#### 5.2.1. `MPTokenIssuanceCreate` Transaction

```js
{
  "TransactionType": "MPTokenIssuanceCreate",
  "Account": "rIssuer...",
  "AssetScale": "2",
  "MaximumAmount": "100000000",
  "Flags": 32,  // tfMPTCanTransfer
  "MutableFlags": 131082,  // tmfMPTCanMutateTransferFee + tmfMPTCanEnableCanLock + tmfMPTCanEnableCanEscrow
  "MPTokenMetadata": "464F4F",
  "TransferFee": 100
}
```

- `tmfMPTCanMutateTransferFee` is set, indicating the `TransferFee` field can be modified.
- `tmfMPTCanEnableCanLock` and `tmfMPTCanEnableCanEscrow` are set, indicating `lsfMPTCanLock` and `lsfMPTCanEscrow` can be enabled after issuance.

#### 5.2.2. `MPTokenIssuanceSet` Transaction

**Sample 1**(successful):

```js
{
  "TransactionType": "MPTokenIssuanceSet",
  "Account": "rIssuer...",
  "MutableFlags": 5,  // tmfMPTSetCanLock(0x0001) + tmfMPTSetCanEscrow (0x0004)
  "TransferFee": 200
}
```

- `TransferFee` was set mutable. It will be updated to 200.
- Set the `lsfMPTCanLock` and `lsfMPTCanEscrow` flags, which were marked as mutable.

**Sample 2**(rejected):

```js
{
  "TransactionType": "MPTokenIssuanceSet",
  "Account": "rIssuer...",
  "MutableFlags": 2, // tmfMPTSetRequireAuth (0x0002)
  "TransferFee": 200
}
```

- This will be rejected. It tries to set `lsfMPTRequireAuth`, which is not mutable.

**Sample 3**(rejected):

```js
{
  "TransactionType": "MPTokenIssuanceSet",
  "Account": "rIssuer...",
  "TransferFee": 200,
  "MPTokenMetadata": "575C5C"
}
```

- This will be rejected. It tries to set `MPTokenMetadata`, which is not mutable.

### 5.3. Example 3

#### 5.3.1. `MPTokenIssuanceCreate` Transaction

```js
{
  "TransactionType": "MPTokenIssuanceCreate",
  "Account": "rIssuer...",
  "AssetScale": "2",
  "MaximumAmount": "100000000",
  "Flags": 2,  // tfMPTCanLock
  "MutableFlags": 131104,  // tmfMPTCanMutateTransferFee + tmfMPTCanEnableCanTransfer
}
```

- `tmfMPTCanMutateTransferFee` is set, allowing the `TransferFee` field to be modified.
- `tmfMPTCanEnableCanTransfer` is set, allowing the `lsfMPTCanTransfer` flag to be enabled after issuance.
- `tfMPTCanLock` is set.
- `TransferFee` is not present (and **MUST NOT** be present) because `tfMPTCanTransfer` is not set.

#### 5.3.2. `MPTokenIssuanceSet` Transaction

**Sample 1**(rejected):

```js
{
  "TransactionType": "MPTokenIssuanceSet",
  "Account": "rIssuer...",
  "TransferFee": 200
}
```

- This will be rejected. Although `lsmfMPTCanMutateTransferFee` is set, a non-zero `TransferFee` cannot be specified unless `lsfMPTCanTransfer` is already enabled.

**Sample 2**(rejected):

```js
{
  "TransactionType": "MPTokenIssuanceSet",
  "Account": "rIssuer...",
  "MutableFlags": 16, // tmfMPTSetCanTransfer
  "TransferFee": 200
}
```

- This will be rejected. Even if `lsmfMPTCanMutateTransferFee` is set, a non-zero `TransferFee` cannot be specified unless `lsfMPTCanTransfer` is already enabled, even if the transaction also includes `tmfMPTSetCanTransfer`.

**Sample 3**(successful):
The following sequence of transactions illustrates a successful case:

**Step1**:

```js
{
  "TransactionType": "MPTokenIssuanceSet",
  "Account": "rIssuer...",
  "MutableFlags": 16 // tmfMPTSetCanTransfer
}
```

- Since `lsmfMPTCanEnableCanTransfer` is set during creation, this transaction successfully sets the `lsfMPTCanTransfer` flag.

**Step2**:

```js
{
  "TransactionType": "MPTokenIssuanceSet",
  "Account": "rIssuer...",
  "TransferFee": 200
}
```

- With both `lsfMPTCanTransfer` and `lsmfMPTCanMutateTransferFee` set, a non-zero `TransferFee` can now be applied.

**Step3**:

```js
{
  "TransactionType": "MPTokenIssuanceSet",
  "Account": "rIssuer...",
  "TransferFee": 0
}
```

- Since `lsmfMPTCanMutateTransferFee` is set, the `TransferFee` field can be removed by setting it to zero.
- The `lsfMPTCanTransfer` flag remains enabled. There is no `MutableFlags` value that disables it.

## Rationale

Dynamic MPT allows issuers to declare selected fields and MPT issuance flags as mutable at creation time, while keeping all other issuance properties immutable. Field mutability supports operational updates such as metadata changes and transfer fee adjustments without requiring a new issuance.

MPT issuance flag mutability is intentionally one-way. If the corresponding `lsmfMPTCanEnable*` flag was set during creation, the issuer may later enable the MPT issuance flag through `MPTokenIssuanceSet`; once enabled, that flag cannot be disabled by `MPTokenIssuanceSet`. This preserves the issuer's ability to opt into additional issuance behavior while avoiding later removal of behavior that holders, integrations, or compliance workflows may have relied on.

## Security

Only the issuer of the `MPTokenIssuance` can use `MPTokenIssuanceSet` to modify mutable fields or enable mutable MPT issuance flags. A field or MPT issuance flag can only be changed if it was explicitly declared mutable during `MPTokenIssuanceCreate`.

Mutable MPT issuance flags are one-way and cannot be disabled through `MPTokenIssuanceSet` after they are enabled. This prevents an issuer from weakening issuance behavior after participants may have relied on the enabled flag.
