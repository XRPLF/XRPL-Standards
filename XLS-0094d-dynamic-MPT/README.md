<pre>
  xls: 94
  title: Dynamic Multi-Purpose Tokens
  description: This amendment enables selected fields and flags of MPTokenIssuance to be updated after creation.
  discussion-from: https://github.com/XRPLF/XRPL-Standards/discussions/289
  author: Yinyi Qian <yqian@ripple.com>
  status: Draft
  category: Amendment
  created: 2025-06-09
</pre>

# Dynamic Multi-Purpose Tokens

## Abstract

This proposal introduces a new amendment `DynamicMPT` as an extension to [XLS-33 Multi-Purpose Tokens](https://github.com/XRPLF/XRPL-Standards/blob/master/XLS-0033-multi-purpose-tokens/README.md). Dynamic Multi-Purpose Tokens (Dynamic MPTs) enable specific fields and flags within an `MPTokenIssuance` to be declared as mutable at the time of creation. By enabling controlled mutability, this feature accommodates evolving token use cases and compliance demands. Modifications to these mutable metadata can be made via the `MPTokenIssuanceSet` transaction.

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
    - `sfMutableFlags` - sets/clears flags (e.g.`tfMPTSetCanLock`, `tfMPTClearCanLock`)

This feature will require an amendment, `DynamicMPT`.

## 2. Declaring Mutability via `MPTokenIssuanceCreate`

If issuers want the ability to modify certain fields or flags after issuance, they must explicitly declare those fields or flags as mutable when creating the `MPTokenIssuance`.
Only a limited set of fields and flags may be declared mutable; all other fields remain permanently immutable.

### 2.1. Declaring Mutability

Issuers can specify mutability during `MPTokenIssuanceCreate` via the optional `MutableFlags` field.

Bits in `MutableFlags` indicate specific fields or flags may be modified after issuance. The fields or flags include:

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

| Flag Name                   |  Hex Value   | Decimal Value | Description                                                                                              |
| --------------------------- | :----------: | :-----------: | -------------------------------------------------------------------------------------------------------- |
| [Reserved]                  |  ️`0x0001`   |       1       | [Reserved; `lsfMPTLocked` is a flag to indicate the lock status of the token, not a configuration flag.] |
| `tfMPTCanMutateCanLock`     |  ️`0x0002`   |       2       | Indicates flag `lsfMPTCanLock` can be changed                                                            |
| `tfMPTCanMutateRequireAuth` |  ️`0x0004`   |       4       | Indicates flag `lsfMPTRequireAuth` can be changed                                                        |
| `tfMPTCanMutateCanEscrow`   |   `0x0008`   |       8       | Indicates flag `lsfMPTCanEscrow` can be changed                                                          |
| `tfMPTCanMutateCanTrade`    |   `0x0010`   |      16       | Indicates flag `lsfMPTCanTrade` can be changed                                                           |
| `tfMPTCanMutateCanTransfer` |  ️`0x0020`   |      32       | Indicates flag `lsfMPTCanTransfer` can be changed                                                        |
| `tfMPTCanMutateCanClawback` |  ️`0x0040`   |      64       | Indicates flag `lsfMPTCanClawback` can be changed                                                        |
| `tfMPTCanMutateMetadata`    | `0x00010000` |     65536     | Allows field `MPTokenMetadata` to be modified                                                            |
| `tfMPTCanMutateTransferFee` | `0x00020000` |    131072     | Allows field `TransferFee` to be modified                                                                |

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

| Flag Name                    |  Hex Value   | Decimal Value | Description                                       |
| ---------------------------- | :----------: | :-----------: | ------------------------------------------------- |
| [Reserved]                   |  ️`0x0001`   |       1       | [Reserved; used by `lsfMPTLocked`]                |
| `lsfMPTCanMutateCanLock`     |  ️`0x0002`   |       2       | Indicates flag `lsfMPTCanLock` can be changed     |
| `lsfMPTCanMutateRequireAuth` |  ️`0x0004`   |       4       | Indicates flag `lsfMPTRequireAuth` can be changed |
| `lsfMPTCanMutateCanEscrow`   |   `0x0008`   |       8       | Indicates flag `lsfMPTCanEscrow` can be changed   |
| `lsfMPTCanMutateCanTrade`    |   `0x0010`   |      16       | Indicates flag `lsfMPTCanTrade` can be changed    |
| `lsfMPTCanMutateCanTransfer` |  ️`0x0020`   |      32       | Indicates flag `lsfMPTCanTransfer` can be changed |
| `lsfMPTCanMutateCanClawback` |  ️`0x0040`   |      64       | Indicates flag `lsfMPTCanClawback` can be changed |
| `lsfMPTCanMutateMetadata`    | `0x00010000` |     65536     | Allows field `MPTokenMetadata` to be modified     |
| `lsfMPTCanMutateTransferFee` | `0x00020000` |    131072     | Allows field `TransferFee` to be modified         |

**Note**: Flag value `0x0001` is used by `lsfMPTLocked`. It is not a valid value for `MutableFlags`.

## 4. `MPTokenIssuanceSet` Transaction Update

This proposal extends the functionality of the `MPTokenIssuanceSet` transaction, allowing the issuer of the `MPTokenIssuance` to update fields or flags that were explicitly marked as mutable during creation.

For details on the original MPTokenIssuanceSet transaction see: [**The MPTokenIssuanceSet Transaction**](https://github.com/XRPLF/XRPL-Standards/blob/master/XLS-0033-multi-purpose-tokens/README.md#33-the-mptokenissuanceset-transaction)

### 4.1. New Fields

| Field Name        | Required? | JSON Type | Internal Type |
| ----------------- | :-------: | :-------: | :-----------: |
| `MPTokenMetadata` |           | `string`  |    `BLOB`     |

New metadata to replace the existing value.
The transaction will be rejected if `lsfMPTCanMutateMetadata` was not set in `MutableFlags`.
Setting an empty `MPTokenMetadata` removes the field.

---

| Field Name    | Required? | JSON Type | Internal Type |
| ------------- | :-------: | :-------: | :-----------: |
| `TransferFee` |           | `number`  |   `UINT16`    |

Updated transfer fee value.
The transaction will be rejected if `lsfMPTCanMutateTransferFee` was not set in `MutableFlags`.
Setting `TransferFee` to zero removes the field.

---

| Field Name     | Required? | JSON Type | Internal Type |
| -------------- | :-------: | :-------: | :-----------: |
| `MutableFlags` |           | `number`  |   `UINT32`    |

Set or clear the flags which were marked as mutable.

**The valid `MutableFlags` values**:

| Flag Name               | Hex Value | Decimal Value | Description                                                                                                             |
| ----------------------- | :-------: | :-----------: | ----------------------------------------------------------------------------------------------------------------------- |
| `tfMPTSetCanLock`       | ️`0x0001` |       1       | Sets the `lsfMPTCanLock` flag. Enables the token to be locked both individually and globally.                           |
| `tfMPTClearCanLock`     | ️`0x0002` |       2       | Clears the `lsfMPTCanLock` flag. Disables both individual and global locking of the token.                              |
| `tfMPTSetRequireAuth`   | ️`0x0004` |       4       | Sets the `lsfMPTRequireAuth` flag. Requires individual holders to be authorized.                                        |
| `tfMPTClearRequireAuth` | ️`0x0008` |       8       | Clears the `lsfMPTRequireAuth` flag. Holders are not required to be authorized.                                         |
| `tfMPTSetCanEscrow`     | `0x0010`  |      16       | Sets the `lsfMPTCanEscrow` flag. Allows holders to place balances into escrow.                                          |
| `tfMPTClearCanEscrow`   | `0x0020`  |      32       | Clears the `lsfMPTCanEscrow` flag. Disallows holders from placing balances into escrow.                                 |
| `tfMPTSetCanTrade`      | `0x0040`  |      64       | Sets the `lsfMPTCanTrade` flag. Allows holders to trade balances on the XRPL DEX.                                       |
| `tfMPTClearCanTrade`    | `0x0080`  |      128      | Clears the `lsfMPTCanTrade` flag. Disallows holders from trading balances on the XRPL DEX.                              |
| `tfMPTSetCanTransfer`   | ️`0x0100` |      256      | Sets the `lsfMPTCanTransfer` flag. Allows tokens to be transferred to non-issuer accounts.                              |
| `tfMPTClearCanTransfer` | ️`0x0200` |      512      | Clears the `lsfMPTCanTransfer` flag. Disallows transfers to non-issuer accounts.                                        |
| `tfMPTSetCanClawback`   | ️`0x0400` |     1024      | Sets the `lsfMPTCanClawback` flag. Enables the issuer to claw back tokens via `Clawback` or `AMMClawback` transactions. |
| `tfMPTClearCanClawback` | ️`0x0800` |     2048      | Clears the `lsfMPTCanClawback` flag. The token can not be clawed back.                                                  |

**Note**:

- Setting and clearing the same flag simultaneously will be rejected. For example, you can not provide both `tfMPTSetCanLock` and `tfMPTClearCanLock`.
- When `lsfMPTCanTransfer` is cleared, the `TransferFee` field is automatically removed.

---

### 4.2. Failure Conditions

| Failure Condition                                                                                                  | Error Code            |
| ------------------------------------------------------------------------------------------------------------------ | --------------------- |
| `MutableFlags` contains invalid value (0 is invalid as well)                                                       | `temINVALID_FLAG`     |
| `MPTokenHolder` is provided when `MutableFlags`, `MPTokenMetadata`, or `TransferFee` is present                    | `temMALFORMED`        |
| `Flags` (except `tfUniversal`) is provided when `MutableFlags`, `MPTokenMetadata`, or `TransferFee` is present     | `temMALFORMED`        |
| `TransferFee` exceeds the limit, which is 50000                                                                    | `temBAD_TRANSFER_FEE` |
| `MPTokenMetadata` length exceeds the limit, which is 1024                                                          | `temMALFORMED`        |
| Setting and clearing the same flag simultaneously, e.g., specifying both `tfMPTSetCanLock` and `tfMPTClearCanLock` | `temMALFORMED`        |
| Including a non-zero `TransferFee` when `lsfMPTCanTransfer` was not set                                            | `temMALFORMED`        |
| Including a non-zero `TransferFee` and `tfMPTClearCanTransfer` in the same transaction                             | `temMALFORMED`        |
| `MutableFlags`, `MPTokenMetadata`, or `TransferFee` is present but `featureDynamicMPT` is disabled                 | `temDISABLED`         |
| `MPTokenIssuanceID` does not exist                                                                                 | `tecOBJECT_NOT_FOUND` |
| `Account` is not the issuer of the target `MPTokenIssuance`                                                        | `tecNO_PERMISSION`    |
| `MutableFlags` attempts to modify flags not declared as mutable                                                    | `tecNO_PERMISSION`    |
| `MPTokenMetadata` is present but was not marked as mutable                                                         | `tecNO_PERMISSION`    |
| `TransferFee` is present but was not marked as mutable                                                             | `tecNO_PERMISSION`    |

### 4.3. `TransferFee` Modification Rules

Since `TransferFee` **MUST NOT** be present if `tfMPTCanTransfer` flag is not set during `MPTokenIssuanceCreate`, there are extra rules we should follow when it comes to mutating the `TransferFee` field.

The ability to modify `TransferFee` depends on two flags:

- `lsfMPTCanTransfer` : must already be set to allow any non-zero `TransferFee`.
- `lsfMPTCanMutateTransferFee`: must be set at creation (`MPTokenIssuanceCreate`) to allow any modification of the `TransferFee` field.

And `lsfMPTCanTransfer` can be modified through `tfMPTSetCanTransfer`/`tfMPTClearCanTransfer` if `lsfMPTCanMutateCanTransfer` is set.

#### Because these flags overlap in function, the rules break down as follows:

**Case1**: `lsfMPTCanTransfer` not set:

- Setting `TransferFee` to zero:
  - If `lsfMPTCanMutateTransferFee` is set: allowed; removes the `TransferFee` field.
  - If `lsfMPTCanMutateTransferFee` is not set: returns `tecNO_PERMISSION`.
- Setting `TransferFee` to a non-zero value:
  - Always invalid: returns `temMALFORMED`, regardless of `lsfMPTCanMutateTransferFee`.
  - ❗**Note**: Even including `tfMPTSetCanTransfer` in the same transaction returns `temMALFORMED`.
    - `lsfMPTCanTransfer` must already be set before assigning a non-zero `TransferFee`.

**Case2**: `lsfMPTCanTransfer` set:

- Setting `TransferFee` to a non-zero value:
  - If `lsfMPTCanMutateTransferFee` is set: allowed; modifies the `TransferFee` field.
    - ❗**Note**: `tfMPTClearCanTransfer` **MUST NOT** be included in the same transaction when setting a non-zero `TransferFee`: otherwise returns `temMALFORMED`.
  - If `lsfMPTCanMutateTransferFee` is not set: returns `tecNO_PERMISSION`.
- Setting `TransferFee` to zero:
  - If `lsfMPTCanMutateTransferFee` is set: allowed; removes the `TransferFee` field.
    - ❗**Note**: if `lsfMPTCanMutateCanTransfer` is set, `tfMPTClearCanTransfer` is allowed to be included when setting to a zero `TransferFee`: it removes `TransferFee` field and clears the `lsfMPTCanTransfer`.
  - If `lsfMPTCanMutateTransferFee` is not set: returns `tecNO_PERMISSION`.

## 5. Examples

### 5.1. Example 1

#### 5.1.1. `MPTokenIssuanceCreate` Transaction

```js
{
  "TransactionType": "MPTokenIssuanceCreate",
  "Account": "rIssuer...",
  "AssetScale": "2",
  "MaximumAmount": "100000000",
  "MutableFlags": 65536, // lsfMPTCanMutateMetadata
  "MPTokenMetadata": "464F4F",
  "TransferFee": 100
}
```

- `tfMPTCanChangeMetadata` is set, indicating the `MPTokenMetadata` field can be modified.

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
  "MutableFlags": 1, // tfMPTSetCanLock (0x0001)
  "MPTokenMetadata": "575C5C"
}
```

- This transaction attempts to set the `lsfMPTCanLock` flag by including `tfMPTSetCanLock` in the `MutableFlags` field. However, the mutation will be rejected because `lsfMPTCanLock` was not marked during creation.

### 5.2. Example 2

#### 5.2.1. `MPTokenIssuanceCreate` Transaction

```js
{
  "TransactionType": "MPTokenIssuanceCreate",
  "Account": "rIssuer...",
  "AssetScale": "2",
  "MaximumAmount": "100000000",
  "Flags": 32,  // tfMPTCanTransfer
  "MutableFlags": 131082,  // tfMPTCanMutateTransferFee + tfMPTCanMutateCanLock + tfMPTCanMutateCanEscrow
  "MPTokenMetadata": "464F4F",
  "TransferFee": 100
}
```

- `tfMPTCanMutateTransferFee` is set, indicating the `TransferFee` field can be modified.
- `tfMPTCanMutateCanLock` and `tfMPTCanMutateCanEscrow` are set, indicating `lsfMPTCanLock` and `lsfMPTCanEscrow` can be modified.

#### 5.2.2. `MPTokenIssuanceSet` Transaction

**Sample 1**(successful):

```js
{
  "TransactionType": "MPTokenIssuanceSet",
  "Account": "rIssuer...",
  "MutableFlags": 33,  // tfMPTSetCanLock(0x0001) + tfMPTClearCanEscrow (0x0020)
  "TransferFee": 200
}
```

- `TransferFee` was set mutable. It will be updated to 200.
- Set the `lsfMPTCanLock` flag and clear the `lsfMPTCanEscrow` flag, which were marked as mutable.

**Sample 2**(rejected):

```js
{
  "TransactionType": "MPTokenIssuanceSet",
  "Account": "rIssuer...",
  "MutableFlags": 4, // tfMPTSetRequireAuth (0x0004)
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
  "MutableFlags": 131104,  // tfMPTCanMutateTransferFee + tfMPTCanMutateCanTransfer
}
```

- `tfMPTCanMutateTransferFee` is set, allowing the `TransferFee` field to be modified.
- `tfMPTCanMutateCanTransfer` is set, allowing the `lsfMPTCanTransfer` flag to be modified.
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

- This will be rejected. Although `lsfMPTCanMutateTransferFee` is set, a non-zero `TransferFee` cannot be set without `tfMPTCanTransfer`.

**Sample 2**(rejected):

```js
{
  "TransactionType": "MPTokenIssuanceSet",
  "Account": "rIssuer...",
  "MutableFlags": 256, // tfMPTSetCanTransfer
  "TransferFee": 200
}
```

- This will be rejected. Although `lsfMPTCanMutateTransferFee` is set, setting non-zero `TransferFee` is still not allowed without `tfMPTCanTransfer`, even the user is trying to set `tfMPTSetCanTransfer` in the same transaction.

**Sample 3**(successful):  
The following sequence of transactions illustrates a successful case:

**Step1**:

```js
{
  "TransactionType": "MPTokenIssuanceSet",
  "Account": "rIssuer...",
  "MutableFlags": 256 // tfMPTSetCanTransfer
}
```

- Since `lsfMPTCanMutateCanTransfer` is set during creation, this transaction successfully sets the `lsfMPTCanTransfer` flag.

**Step2**:

```js
{
  "TransactionType": "MPTokenIssuanceSet",
  "Account": "rIssuer...",
  "TransferFee": 200
}
```

- With both `lsfMPTCanTransfer` and `lsfMPTCanMutateTransferFee` set, a non-zero `TransferFee` can now be applied.

**Step3**:

```js
{
  "TransactionType": "MPTokenIssuanceSet",
  "Account": "rIssuer...",
  "MutableFlags": 512 // tfMPTClearCanTransfer
}
```

- Since `lsfMPTCanMutateCanTransfer` is set, the `lsfMPTCanTransfer` flag can be cleared.
- Clearing `lsfMPTCanTransfer` automatically removes the `TransferFee` from the `MPTokenIssuance` object.
