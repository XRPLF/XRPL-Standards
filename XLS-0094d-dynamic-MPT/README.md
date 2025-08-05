<pre>
Title:       <b>Dynamic Multi-Purpose Tokens</b>
Type:        <b>draft</b>

Author:      <a href="mailto:yqian@ripple.com">Yinyi Qian</a>
Affiliation: <a href="https://ripple.com">Ripple</a>
</pre>

# Dynamic Multi-Purpose Tokens

## Abstract

This proposal introduces a new amendment `DynamicMPT` as an extension to [XLS-33 Multi-Purpose Tokens](https://github.com/XRPLF/XRPL-Standards/blob/master/XLS-0033-multi-purpose-tokens/README.md). Dynamic Multi-Purpose Tokens (Dynamic MPTs) enable specific fields and flags within an `MPTokenIssuance` to be declared as mutable at the time of creation. By enabling controlled mutability, this feature accommodates evolving token use cases and compliance demands. Modifications to these mutable metadata can be made via the `MPTokenIssuanceSet` transaction, but only for fields or flags that were marked as mutable in the `MPTokenIssuanceCreate` transaction.

## 1. Overview

This proposal introduces:

- Transaction update for `MPTokenIssuanceCreate`:
  - New flags:
    - `tfMPTCanChangeMetadata` — allows modification of `MPTokenMetadata`.
    - `tfMPTCanChangeTransferFee` — allows modification of `TransferFee`.
  - A new optional field:
    -  `sfMutableFlags` - indicates which flags are mutable.

- Ledger object update in `MPTokenIssuance`:
  - New flags:
    - `lsfMPTCanChangeMetadata`
    - `lsfMPTCanChangeTransferFee`
  - A new optional field:
    - `sfMutableFlags`

- Transaction update for `MPTokenIssuanceSet`:
  - New optional fields:
    - `sfMPTokenMetadata` - updates `MPTokenMetadata`
    - `sfTransferFee` - updates `TransferFee`
    - `sfMutableFlags` - sets/clears flags (eg.`tfMPTSetCanLock`, `tfMPTClearCanLock`)

This feature will require an amendment, `DynamicMPT`.

## 2. Declaring Mutability via `MPTokenIssuanceCreate`

If issuers want the ability to modify certain fields or flags after issuance, they must explicitly declare those fields or flags as mutable when creating the `MPTokenIssuance`.
Only a limited set of fields and flags may be declared mutable; all other fields remain permanently immutable.

### 2.1. Mutability Rules

In this spec, we refer to the flags defined for the `MPTokenIssuanceCreate` transaction as follows:

- <a name="mutability-flags">**Mutability Flags**</a> (cannot be changed later):
  -  `tfMPTCanChangeMetadata`
  -  `tfMPTCanChangeTransferFee`

- <a name="operational-flags">**Operational Flags**</a> (can be marked as mutable):
  -  `tfMPTCanLock`
  -  `tfMPTRequireAuth`
  -  `tfMPTCanEscrow`
  -  `tfMPTCanTrade`
  -  `tfMPTCanTransfer`
  -  `tfMPTCanClawback`. 
  
  These operational flags were originally defined in [XLS-33 Multi-Purpose Tokens: Transaction-specific Fields](https://github.com/XRPLF/XRPL-Standards/tree/master/XLS-0033-multi-purpose-tokens#3111-transaction-specific-fields) (under `Flags` field)
  They can be changed through `MPTokenIssuanceSet` if marked as mutable.

| What Can be Declared Mutable in `MPTokenIssuance`            | How to Declare as Mutable during `MPTokenIssuanceCreate` |
| -------------------------- | ------------------------------- |
| Field `MPTokenMetadata`  |   Set the `tfMPTCanChangeMetadata` flag in `Flags` field          |
| Field `TransferFee`|  Set the `TransferFeeMutable` flag in `Flags` field            |
| `Flags` (Only [Operational Flags](#operational-flags)) |  Set flags in the `MutableFlags` field to mark the corresponding operational flags as mutable.|


Note:
- `MutableFlags` **MUST NOT** include `tfMPTCanChangeMetadata`, `tfMPTCanChangeTransferFee`. These two flags are permanently immutable.
- Issuers can enable multiple mutability in a single `MPTokenIssuanceCreate` transaction.

### 2.2. Declaring Mutability

Issuers can declare mutability at the time of `MPTokenIssuanceCreate` using `Flags` and the optional `MutableFlags` field.

#### 2.2.1. Flags
| Flag Name                  | Hex Value    | Decimal Value | Description  |
| -------------------------- |:------------:|:-------------:|--------------|
| `tfMPTCanChangeMetadata`   | `0x00010000` | 65536	 	      | Allows `MPTokenMetadata` to be modified. |
| `tfMPTCanChangeTransferFee`| `0x00020000` | 131072        | Allows `TransferFee` to be modified.     | 

- These flags are used to indicate specific fields can be modified.

#### 2.2.2. MutableFlags

| Field Name     | Required? | JSON Type | Internal Type | Description                                           |
| -------------- |:---------:|:---------:|:-------------:| ----------------------------------------------------- |
| `MutableFlags` |           | `number`  | `UInt32`      | Follows the same bit layout as `MPTokenIssuanceCreate Flags`; each set bit enables mutability for that flag. Only [Operational Flags](#operational-flags) allowed. |


#### Bit Layout of `MutableFlags`:  

| Flag Name                   | Flag Value | Description                                          |
|-----------------------------|------------|------------------------------------------------------|
| `tfMPTCanMutateCanLock`     | ️`0x0002`   | If set, indicates `lsfMPTCanLock` can be changed     |
| `tfMPTCanMutateRequireAuth` | ️`0x0004`   | If set, indicates `lsfMPTRequireAuth` can be changed |
| `tfMPTCanMutateCanEscrow`   | `0x0008`   | If set, indicates `lsfMPTCanEscrow` can be changed   |
| `tfMPTCanMutateCanTrade`    | `0x0010`   | If set, indicates `lsfMPTCanTrade` can be changed    |
| `tfMPTCanMutateCanTransfer` | ️`0x0020`   | If set, indicates `lsfMPTCanTransfer` can be changed |
| `tfMPTCanMutateCanClawback` | ️`0x0040`   | If set, indicates `lsfMPTCanClawback` can be changed |

- These flags are set through `MPTokenIssuanceCreate`'s `MutableFlags` to declare flags can be modified.
- It follows the same bit layout as `MPTokenIssuanceCreate Flags`.

### 2.3. Failure Conditions

| Failure Condition                                                             | Error Code                  |
| ----------------------------------------------------------------------------- | --------------------------- |
| Invalid values in `Flags` field                                               | `temINVALID_FLAG`           |
| `MutableFlags` includes values not in [Operational Flags](#operational-flags) | `temINVALID_MUTABLE_FLAG`   |
| `MutableFlags` includes values in [Mutability Flags](#mutability-flags)       | `temINVALID_MUTABLE_FLAG`   |


## 3. On-Ledger Data Structure Change
This proposal introduces updates to the `MPTokenIssuance` ledger object, including additional flag values for the existing `Flags` field and a new optional field `MutableFlags`.

## 3.1. New Flags in `MPTokenIssuance`

This proposal defines additional flag values in the `MPTokenIssuance` object 

| Flag Name                   | Hex Value    | Decimal Value | Description       |
| --------------------------- |:------------:|:-------------:|-------------------|
| `lsfMPTCanChangeMetadata`   | `0x00010000` | 65536         | If set, indicates `MPTokenMetadata` is mutable|
| `lsfMPTCanChangeTransferFee`| `0x00020000` | 131072        | If set, indicates `TransferFee` is mutable|

## 3.2. New Optionbal Field: `MutableFlags`

A new optional field, `MutableFlags` (SField `sfMutableFlags`), is added to the `MPTokenIssuance` ledger object.

| Field Name       | Required?    | JSON Type | Internal Type |
| ---------------- |:------------:|:---------:|:-------------:|
| `MutableFlags`   |              | `number`  | `UINT32`      |

The bit layout of `MutableFlags` mirrors the existing `Flags` field in `MPTokenIssuanceCreate` to record mutable operational flags.

### Bit Layout of `MutableFlags`:

| Flag Name                    | Flag Value | Description                                          |
|------------------------------|------------|------------------------------------------------------|
| [Reserved]                   | ️`0x0001`   | [Reserved; used by `lsfMPTLocked`]                   |
| `lsfMPTCanMutateCanLock`     | ️`0x0002`   | If set, indicates `lsfMPTCanLock` can be changed     |
| `lsfMPTCanMutateRequireAuth` | ️`0x0004`   | If set, indicates `lsfMPTRequireAuth` can be changed |
| `lsfMPTCanMutateCanEscrow`   | `0x0008`   | If set, indicates `lsfMPTCanEscrow` can be changed   |
| `lsfMPTCanMutateCanTrade`    | `0x0010`   | If set, indicates `lsfMPTCanTrade` can be changed    |
| `lsfMPTCanMutateCanTransfer` | ️`0x0020`   | If set, indicates `lsfMPTCanTransfer` can be changed |
| `lsfMPTCanMutateCanClawback` | ️`0x0040`   | If set, indicates `lsfMPTCanClawback` can be changed |

- The table shows the flags under `MPTokenIssuance` ledger object's `sfMutableFlags` to record mutable operational flags.
- It follows the same bit layout as `MPTokenIssuance Flags`.
- Flag value `0x0001` is used by `lsfMPTLocked`. It is not a valid value for `MutableFlags`.

## 4. Modifying `MPTokenIssuance` via `MPTokenIssuanceSet`

This proposal extends the functionality of the `MPTokenIssuanceSet` transaction, allowing the issuer of the `MPTokenIssuance` to update fields or flags that were explicitly marked as mutable during creation.

For details on the original MPTokenIssuanceSet transaction see: [**The MPTokenIssuanceSet Transaction**](https://github.com/XRPLF/XRPL-Standards/blob/master/XLS-0033-multi-purpose-tokens/README.md#33-the-mptokenissuanceset-transaction)

### 4.1. New Fields

| Field Name        | Required? | JSON Type | Internal Type |
| ----------------- |:---------:|:---------:|:-------------:|
| `MPTokenMetadata` |           | `string`  | `BLOB`        |

New metadata to replace the existing value.
The transaction will be rejected if `lsfMPTCanChangeMetadata` was not set.

---

| Field Name    | Required? | JSON Type | Internal Type |
| ------------- |:---------:|:---------:|:-------------:|
| `TransferFee` |           | `number`  | `UINT16`      | 

Updated transfer fee value.
The transaction will be rejected if `lsfMPTCanChangeTransferFee` was not set.

---

| Field Name          | Required?        |  JSON Type    | Internal Type     |
| ------------------- |:----------------:|:-------------:|:-----------------:|
| `MutableFlags`      |                  |`string`       |   `UINT32`        |  

Set or clear the flags which are marked as mutable.

**The valid `MutableFlags` values**:

| Flag Name              | Hex Value | Decimal Value |  Description |
|------------------------|:---------:|:-------------:|--------------|
| `tfMPTSetCanLock`      | ️`0x0001`  | 1             |Sets the `lsfMPTCanLock` flag. Enables the token to be locked both individually and globally. |
| `tfMPTClearCanLock`    | ️`0x0002`  | 2             |Clears the `lsfMPTCanLock` flag. Disables both individual and global locking of the token. |
| `tfMPTSetRequireAuth`  | ️`0x0004`  | 4             |Sets the `lsfMPTRequireAuth` flag. Requires individual holders to be authorized. |
| `tfMPTClearRequireAuth`| ️`0x0008`  | 8             |Clears the `lsfMPTRequireAuth` flag. Holders are not required to be authorized. |
| `tfMPTSetCanEscrow`    | `0x0010`  | 16            |Sets the `lsfMPTCanEscrow` flag. Allows holders to place balances into escrow. |
| `tfMPTClearCanEscrow`  | `0x0020`  | 32            |Clears the `lsfMPTCanEscrow` flag. Disallows holders from placing balances into escrow. |
| `tfMPTSetCanTrade`     | `0x0040`  | 64            |Sets the `lsfMPTCanTrade` flag. Allows holders to trade balances on the XRPL DEX. |
| `tfMPTClearCanTrade`   | `0x0080`  | 128           |Clears the `lsfMPTCanTrade` flag. Disallows holders from trading balances on the XRPL DEX. |
| `tfMPTSetCanTransfer`  | ️`0x0100`  | 256           |Sets the `lsfMPTCanTransfer` flag. Allows tokens to be transferred to non-issuer accounts. |
| `tfMPTClearCanTransfer`| ️`0x0200`  | 512           |Clears the `lsfMPTCanTransfer` flag. Disallows transfers to non-issuer accounts. |
| `tfMPTSetCanClawback`  | ️`0x0400`  | 1024          |Sets the `lsfMPTCanClawback` flag. Enables the issuer to claw back tokens via `Clawback` or `AMMClawback` transactions. |
| `tfMPTClearCanClawback`| ️`0x0800`  | 2048          | Clears the `lsfMPTCanClawback` flag. The token can not be clawed back. |

**Note**: If both the Set and Clear variants of a flag are specified in the same transaction (e.g., `tfMPTSetCanLock` and `tfMPTClearCanLock`), they cancel each other out and have no effect. This applies to all flag pairs listed above.

---

### 4.2. Failure Conditions

| Failure Condition   											   	                     | Error Code            |
| ------------------------------------------------------------------ | --------------------- |
| `MPTokenIssuanceID` does not exist                                 | `tecOBJECT_NOT_FOUND` |
| `Account` is not the issuer of the target MPTokenIssuance          | `tecNO_PERMISSION`    |
| `MutableFlags` contains invalid value                              | `temINVALID_FLAG`     |
| `MutableFlags` attempts to modify flags not declared as mutable    | `tecNO_PERMISSION`    |
| `MPTokenMetadata` is present but was not marked as mutable         | `tecNO_PERMISSION`    |
| `TransferFee` is present but was not marked as mutable             | `tecNO_PERMISSION`    |
| `MPTokenHolder` is provided when `MutableFlags`, `MPTokenMetadata`, or `TransferFee` is present. | `temMALFORMED` |
| `Flags` is provided when `MutableFlags`, `MPTokenMetadata`, or `TransferFee` is present.         | `temMALFORMED` |


## 5. Examples
### 5.1. `MPTokenMetadata` is Mutable

#### 5.1.1. `MPTokenIssuanceCreate` Transaction

```js
{
  "TransactionType": "MPTokenIssuanceCreate",
  "Account": "rIssuer...",
  "AssetScale": "2",
  "MaximumAmount": "100000000",
  "Flags": 65536, // tfMPTCanChangeMetadata
  "MPTokenMetadata": "464F4F",
  "TransferFee": 100,
  "Fee": 10
}
```
- `tfMPTCanChangeMetadata` is set, indicating the `MPTokenMetadata` field can be modified.

#### 5.1.2. `MPTokenIssuanceSet` Transaction

**Sample 1**(successful):
```js
{
  "TransactionType": "MPTokenIssuanceSet",
  "Account": "rIssuer...",
  "MPTokenMetadata": "575C5C",
  "Fee": 10
}
```
- `MPTokenMetadata` was set mutable, so this will update the metadata from `464F4F` to `575C5C`.

**Sample 2**(rejected):
```js
{
  "TransactionType": "MPTokenIssuanceSet",
  "Account": "rIssuer...",
  "MutableFlags": 1, // tfMPTSetCanLock (0x0001)
  "MPTokenMetadata": "575C5C",
  "Fee": 10
}
```
- This transaction attempts to set the `lsfMPTCanLock` flag by including `tfMPTSetCanLock` in the `MutableFlags` field. However, the mutation will be rejected because `lsfMPTCanLock` was not marked during creation.

### 5.2. `TransferFee` and Some Flags are Mutable

#### 5.2.1. `MPTokenIssuanceCreate` Transaction
```js
{
  "TransactionType": "MPTokenIssuanceCreate",
  "Account": "rIssuer...",
  "AssetScale": "2",
  "MaximumAmount": "100000000",
  "Flags": 131080,  // tfMPTCanChangeTransferFee + tfMPTCanEscrow
  "MutableFlags": 10,  // tfMPTCanMutateCanLock + tfMPTCanMutateCanEscrow
  "MPTokenMetadata": "464F4F",
  "TransferFee": 100,
  "Fee": 10
}
```
- `tfMPTCanChangeTransferFee` is set, indicating the `TransferFee` field can be modified.
- `tfMPTCanMutateCanLock` and `tfMPTCanMutateCanEscrow` are set, indicating `lsfMPTCanLock` and `lsfMPTCanEscrow` can be modified.

#### 5.2.2. `MPTokenIssuanceSet` Transaction

**Sample 1**(successful):
```js
{
  "TransactionType": "MPTokenIssuanceSet",
  "Account": "rIssuer...",
  "Flags": 33,  // tfMPTSetCanLock(0x0001) + tfMPTClearCanEscrow (0x0020)
  "TransferFee": 200,
  "Fee": 10
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
  "TransferFee": 200,
  "Fee": 10
}
```
- This will be rejected. It tries to set `lsfMPTRequireAuth`, which is not mutable.

**Sample 3**(rejected):

```js
{
  "TransactionType": "MPTokenIssuanceSet",
  "Account": "rIssuer...",
  "TransferFee": 200,
  "Fee": 10,
  "MPTokenMetadata": "575C5C"
}
```
- This will be rejected. It tries to set `MPTokenMetadata`, which is not mutable.

## Appendix: FAQ

### Can Flags Declaring mutability be mutable?
No. Flags like `tfMPTCanChangeMetadata` and `tfMPTCanChangeTransferFee` are permanently immutable. They must be set during creation and cannot be altered later.
