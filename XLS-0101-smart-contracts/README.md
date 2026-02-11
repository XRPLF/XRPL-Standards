<pre>
  title: XRPL Smart Contracts
  description: An L1 native implementation of Smart Contracts on the XRP Ledger
  created: 2025-07-28
  author: Mayukha Vadari (@mvadari), Denis Angell (@dangell7)
  proposal-from: https://github.com/XRPLF/XRPL-Standards/discussions/271
  status: Draft
  category: Amendment
</pre>

# XRPL Smart Contracts

## Abstract

This document is a formal design of a smart contract system for the XRPL, which takes inspiration from several existing smart contract systems (including Xahau’s Hooks and the EVM).

Some sample use cases (a far-from-exhaustive list):

- Integration with a new bridging protocol
- A new DeFi protocol (e.g. derivatives or perpetuals)
- Issued token staking rewards

_Note: This document is still a fairly early draft, and therefore there are a few TODOs and open questions sprinkled through it on some of the more minor points. Any input on those questions would be especially appreciated._

## 1. Design Objectives

The main requirements we aimed to satisfy in our design:

- Permissionless (i.e. no need for UNL approval to deploy a smart contract)
- Easy access to native features/primitives (to build on the XRPL’s powerful building blocks)
- Easy learning for new developers (i.e. familiar design paradigms)
- Minimal impact to existing users/use-cases of the XRPL (especially with regard to payments and performance)
- Minimal impact to node/validator costs
- Able to auto-generate some sort of [ABI](https://www.alchemy.com/overviews/what-is-an-abi-of-a-smart-contract-examples-and-usage) from smart contract source code (to make tooling easier)

One of the great advantages of the XRPL is its human-readable transaction structure - unlike e.g. EVM transactions. In this design, we tried to keep that ethos of things being human-readable - such as keeping the ABI on-chain (even though that would increase storage).

### 1.1. General XRPL Programmability Vision

We envision programmability on the XRPL as the glue that seamlessly connects its powerful, native building blocks with the flexibility of custom on-chain business logic. This vision focuses on preserving what makes the XRPL special—its efficiency, reliability, and simplicity—while empowering builders to unlock new possibilities.

See [the blog post here](https://dev.to/ripplexdev/a-proposed-vision-for-xrp-ledger-programmability-1gdj) for more details.

## 2. Overview

This design for Smart Contracts combines the easy-to-learn overall design of EVM smart contracts (addresses with functions) with the familiarity of XRPL transactions. A Smart Contract lives on a [pseudo-account](../XLS-0064-pseudo-account/README.md) and is triggered via a new `ContractCall` transaction, which calls a specific function on the smart contract, with provided parameters. The Smart Contract can modify its own state data, or interact with other XRPL building blocks (including other smart contracts) via submitting its own XRPL transactions via its code.

The details of the WASM engine and the API will be in separate XLSes published later.

This proposal involves:

- Three new ledger entry types: `ContractSource`, `Contract`, and `ContractData`
- Six new transaction types: `ContractCreate`, `ContractCall`, `ContractModify`, `ContractDelete`, `ContractUserDelete`, and `ContractClawback`
- Two new RPC methods: `contract_info` and `event_history`
- One new RPC subscription: `eventEmitted`
- Modifications to the UNL-votable fee parameters (and the `FeeSettings` object that keeps track of that info)
- Three new serialized types: `STParameters`, `STParameterValues`, and `STData`

<!--TODO: should probably work with Vito on this and think of this spec as essentially a more general SAV-->

### 2.1. Background: Pseudo-Accounts

A pseudo-account ([XLS-64](../XLS-0064-pseudo-account/README.md)) is an XRPL account that is impossible for any person to have the keys for (it is cryptographically impossible to have those keys). It may be associated with other ledger entries.

Since it is not governed by any set of keys, it cannot be controlled by any user. Therefore, it may host smart contracts.

### 2.2. Background: Serialized Types

The XRPL encodes data into a set of serialized types (all of whose names begin with the letters `ST`, standing for “Serialized Type”).

For example:

- The `“Account”` field is of type `STAccount` (which represents XRPL account IDs)
- The `“Sequence”` field is of type `STUInt32` (which represents an unsigned 32-bit integer)
- The `“Amount”` field is of type `STAmount` (which represents all amount types - XRP, IOUs, and MPTs)

### 2.3. Design Overview

- Smart contracts (henceforth referred to as just “contracts”) are stored in pseudo-accounts
- `Contract` stores the contract info
- `ContractSource` is an implementation detail to make code storage more efficient
- `ContractData` stores any contract-specific data
- `ContractCreate` creates a new contract + pseudo-account, and allows the contract to do some setup work
- `ContractCall` is used to trigger the transaction and call one of its functions
- `ContractModify` allows the contract owner (or the contract itself) to modify a contract
- `ContractDelete` allows the contract owner (or the contract itself) to delete a contract
- `ContractUserDelete` allows a user of a smart contract to delete their data associated with a contract (and allows the contract to do any cleanup for that)
- `ContractClawback` allows a token issuer to claw back from a contract (and allows the contract to do any cleanup for that)
- There are some modifications to transaction common fields to support contract-submitted transactions
- The `contract_info` RPC fetches the ABI of a contract and any other relevant information.
- The `event_history` RPC fetches the event emission history for a contract.
- The `eventEmitted` subscription allows you to subscribe to “events” emitted from a contract.
- All computation limitations and fees will be configurable by UNL vote (just like transaction fees and reserves are currently).

### 2.4. Overview of Smart Contract Capabilities

- Contract data storage
- Per-user contract data storage
- On-chain verified ABI
- Read-only access to ledger state (any ledger entries)
- Other changes to the ledger state are done via transactions that the pseudo-account “submits” from within contract code
- Contract-level “environment/class variable” parameters that don’t require the source code to be changed
- May have an `init` function that runs on `ContractCreate` for any account setup

## 3. Ledger Entry: `ContractSource`

The objective of this object is to save space on-chain when deploying the exact same contract (i.e. if the same code is used by multiple contracts, the ledger only needs to store it once). This feature was heavily inspired by the existing Hooks `HookDefinition` object (see [this page](https://xrpl-hooks.readme.io/docs/reference-counting) for its documentation).

This object is essentially just an implementation detail to decrease storage costs, so that duplicate contracts don't need to have their source code copied on-chain. End-users won't have to worry about it. The core object in this design is the `Contract` object.

### 3.1. Fields

| Field Name           | Required? | JSON Type | Internal Type  | Description                                                                                                                 |
| :------------------- | :-------- | :-------- | :------------- | :-------------------------------------------------------------------------------------------------------------------------- |
| `LedgerEntryType`    | ✔️        | `string`  | `UInt16`       | The ledger entry's type (`ContractSource`).                                                                                 |
| `ContractHash`       | ✔️        | `string`  | `Hash256`      | The hash of the contract's code.                                                                                            |
| `ContractCode`       | ✔️        | `string`  | `blob`         | The WebAssembly (WASM) bytecode for the contract.                                                                           |
| `InstanceParameters` |           | `array`   | `STParameters` | The parameters that are provided by a deployment of this contract.                                                          |
| `Functions`          | ✔️        | `array`   | `STArray`      | The functions that are included in this contract.                                                                           |
| `ReferenceCount`     | ✔️        | `number`  | `UInt32`       | The number of `Contract` objects that are based on this `ContractSource`. This object is deleted when that value goes to 0. |

#### 3.1.1. Object ID

hash of prefix + `ContractHash`

#### 3.1.2. `InstanceParameters` and `Functions`

- Instance parameters are analogous to environment variables
- TODO: should there be default values for these parameters?

#### 3.1.3 `Functions`

- All parameter types must be valid XRPL `STypes` (maybe ban `STObjects` and `STArrays` and other complex STypes like `Transaction`)
  - Advantage of storing the parameter types separately: you don’t have to open the VM to check if the parameters provided are valid (more efficient). You also get the ABI on-chain.
  - TODO: Maybe all variables in the smart contract must be STypes?
- No more than 4 parameters allowed (for now - we can relax that restriction later)
- All parameters are required, no overloading allowed
  - This could potentially change in a future version
- Possible flags:
  - `tfSendAmount` - if the type is an `STAmount`, then that amount will be sent to the contract from your funds
  - `tfSendNFToken` - if the type is a `Hash256`, then the `NFToken` with that ID will be sent to the contract from your holdings
  - `tfAuthorizeTokenHolding` - if the type is an `STIssue` or `STAmount`, then you can automatically create a trustline/MPToken for that token (assuming it’s not XRP).
  - Something authorizing some amount of reserve to be claimed?
  - Others? We have space for 32 possible flags

### 3.2. Object Deletion

The `ContractSource` object does not have an owner.

- The object is deleted if the `ReferenceCount` ever goes to 0
  - This could be an invariant check - no `ContractSource` object should exist with a `ReferenceCount` value of 0

### 3.3. Example Object

```javascript
{
  LedgerEntryType:  "ContractSource",
  ContractHash: "610F33B8EBF7EC795F822A454FB852156AEFE50BE0CB8326338A81CD74801864",
  Code: "B80BE0CB156AEC7B852156AEFEC79FE50BE0CB83267E3267E5F822A454F1CD528574801864338A8610F33B8EBF95F822A454F1CD74801864338A8610F33B8EBF",
  InstanceParameters: [(0, "UInt16"), (0, "AccountID"), (tfSendAmount, "STAmount")],
  Functions: [
    {
      "name": "transfer",
      "parameters": [(0, "UInt32"), (tfSendAmount, "STAmount"), (0, "AccountID")]
    },
    {
      "name": "create",
      "parameters": [(0, "UInt32"), (0, "STAmount")]
    }
  ],
  ReferenceCount: 1
}
```

## 4. Ledger Entry: `Contract`

### 4.1. Fields

| Field Name                | Required? | JSON Type | Internal Type       | Description                                                                                                                    |
| :------------------------ | :-------- | :-------- | :------------------ | :----------------------------------------------------------------------------------------------------------------------------- |
| `LedgerEntryType`         | ✔️        | `string`  | `UInt16`            | The ledger entry's type (`Contract`).                                                                                          |
| `ContractAccount`         | ✔️        | `string`  | `AccountID`         | The pseudo-account that hosts this contract.                                                                                   |
| `Owner`                   | ✔️        | `string`  | `AccountID`         | The owner of the contract, which defaults to the account that deployed the contract.                                           |
| `Flags`                   | ✔️        | `number`  | `UInt32`            | Flags that may be on this ledger entry.                                                                                        |
| `Sequence`                | ✔️        | `string`  | `UInt16`            | The ledger entry's type (`ContractSource`).                                                                                    |
| `ContractHash`            | ✔️        | `string`  | `Hash256`           | The hash of the contract's code.                                                                                               |
| `InstanceParameterValues` |           | `array`   | `STParameterValues` | The parameters that are provided by this deployment of the contract.                                                           |
| `URI`                     |           | `string`  | `Blob`              | A URI that points to the source code of this contract, to make it easier for tooling to find the source code for the contract. |

_TODO: should the `URI` field live on `ContractSource` or `Contract`?_

#### 4.1.1. Object ID

hash of prefix + `ContractHash` + `Sequence`

#### 4.1.2. `Flags`

- `lsfImmutable` - the code can’t be updated.
- `lsfCodeImmutable` - the code can’t be updated, but the instance parameters can.
- `lsfABIImmutable` - the code can be updated, but the ABI cannot. This ensures backwards compatibility.
- `lsfUndeletable` - the contract can’t be deleted.

A `Contract` can have at most one of `lsfImmutable`, `lsfCodeImmutable`, and `lsfABIImmutable` enabled.

#### 4.1.3. `InstanceParameters`

The instance parameter list must match the types of the matching `ContractSource` object.

### 4.2. Account Deletion

The `Contract` object is a [deletion blocker](https://xrpl.org/docs/concepts/accounts/deleting-accounts/#requirements).

### 4.3. Example Object

```javascript
{
  LedgerEntryType:  "Contract",
  Owner: "rWYkbWkCeg8dP6rXALnjgZSjjLyih5NXm",
  ContractHash: "610F33B8EBF7EC795F822A454FB852156AEFE50BE0CB8326338A81CD74801864",
  InstanceParameters: [(0, 1), (0, "rABCD...."), (tfSendAmount, "myToken")]
}
```

## 5. Ledger Entry: `ContractData`

Data is serialized using the `STData` serialization format.

### 5.1. Fields

| Field Name        | Required? | JSON Type | Internal Type | Description                                                                                                           |
| :---------------- | :-------- | :-------- | :------------ | :-------------------------------------------------------------------------------------------------------------------- |
| `LedgerEntryType` | ✔️        | `string`  | `UInt16`      | The ledger entry's type (`ContractData`).                                                                             |
| `Owner`           | ✔️        | `string`  | `AccountID`   | The account that hosts this data.                                                                                     |
| `ContractAccount` |           | `string`  | `AccountID`   | The contract that controls this data. This field is only needed for user-owned data (where the `Owner` is different). |
| `Data`            | ✔️        | `string`  | `STData`      | The contract-defined contract data.                                                                                   |

#### 5.1.1. Object ID

hash of prefix + `Owner` [+ `ContractAccount`]

### 5.2. Account Deletion

The `ContractData` object is a [deletion blocker](https://xrpl.org/docs/concepts/accounts/deleting-accounts/#requirements).

### 5.3. Reserves

Probably one reserve per 256 bytes

See [Reserves](#reserves)

### 5.4. Example Object

```javascript
{
    LedgerEntryType: "ContractData",
    Owner: "rWYkbWkCeg8dP6rXALnjgZSjjLyih5NXm",
    Name: "dataForFunction1",
    Data: {
        "count": 3,
        "total": 12,
        "destination": "r3PDXzXky6gboMrwUrmSCiUyhzdrFyAbfu"
    }
}
```

## 6. Transaction: `ContractCreate`

This transaction creates a pseudo-account with the contract inside it.

This transaction will also trigger a special `init` function in the contract, if it exists - which allows smart contract devs to do their own setup work as needed.

### 6.1. Fields

| Field Name                | Required? | JSON Type | Internal Type       | Description                                                                                   |
| :------------------------ | :-------- | :-------- | :------------------ | :-------------------------------------------------------------------------------------------- |
| `TransactionType`         | ✔️        | `string`  | `UInt16`            | The transaction type (`ContractCreate`).                                                      |
| `Account`                 | ✔️        | `string`  | `AccountID`         | The account sending the transaction.                                                          |
| `ContractOwner`           |           | `string`  | `AccountID`         | The account that owns (controls) the contract. If not set, this is the same as the `Account`. |
| `Flags`                   |           | `number`  | `UInt32`            | Accepted bit-flags on this transaction.                                                       |
| `ContractCode`            |           | `string`  | `Blob`              | The WASM bytecode for the contract.                                                           |
| `ContractHash`            |           | `string`  | `Hash256`           | The hash of the WASM bytecode for the contract.                                               |
| `Functions`               |           | `array`   | `STArray`           | The functions that are included in this contract.                                             |
| `InstanceParameters`      |           | `array`   | `STParameters`      | The parameters that are provided by a deployment of this contract.                            |
| `InstanceParameterValues` |           | `array`   | `STParameterValues` | The values of the instance parameters that apply to this instance of the contract.            |

#### 6.1.1. `Flags`

- `tfImmutable` - the code can’t be changed and the instance parameters can't be updated either.
- `tfCodeImmutable` - the code can’t be updated, but the instance parameters can.
- `tfABIImmutable` - the code can be updated, but the ABI cannot.
- `tfUndeletable` - the contract can’t be deleted.

A contract may have at most one of `tfImmutable`, `tfCodeImmutable`, and `lsfABIImmutable` enabled.

#### 6.1.2. `ContractCode` and `ContractHash`

Exactly one of these two fields must be included.

`ContractCode` should be used if the code has not already been uploaded to the XRPL (i.e. there is already a matching `ContractSource` object). This transaction will be more expensive.

`ContractHash` should be used if the code has already been uploaded to the XRPL. This transaction will be cheaper, since the code does not need to be re-uploaded.

If `ContractCode` is provided even if the code has already been uploaded, it will have the same outcome as if the `ContractHash` had been provided instead (albeit with a more expensive fee).

If `ContractCode` is provided, `InstanceParameters` and `Functions` must also be provided.

### 6.2. Fee

Similar to `AMMCreate`, 1 object reserve fee (+ fees for running the `init` code, and probably also + fees per byte of code uploaded)

### 6.3. Failure Conditions

- `ContractHash` is provided but there is no existing corresponding `ContractSource` ledger entry.
- The `ContractCode` provided is invalid.
- The ABI provided in `Functions` doesn't match the code.
- `InstanceParameters` don't match what's in the existing `ContractSource` ledger entry.

### 6.4. State Changes

If the transaction is successful:

- The pseudo-account that hosts the `Contract` is created.
- The `Contract` object is created.
- If the `ContractSource` object already exists, the `ReferenceCount` will be incremented.
- If the `ContractSource` object does not already exist, it will be created.

### 6.5. Example Transaction

```javascript
{
  TransactionType:  "ContractCreate",
  Flags: tfImmutable,
  ContractCode: "74292CC654D754F217D0934762EA08742924F2762EA083DC8817D09341B1F2CC6C3DCDAE01565DB0994CA3E76E91C881B1F2DAE01565DB0994CA3E76E9154D75"
}
```

## 7. Transaction: `ContractCall`

This transaction triggers a specific function in a given contract, with the provided parameters

- Must match the parameter types/flags provided in the contract (and in the right order)

### 7.1. Fields

| Field Name        | Required? | JSON Type | Internal Type       | Description                                                                                              |
| :---------------- | :-------- | :-------- | :------------------ | :------------------------------------------------------------------------------------------------------- |
| `TransactionType` | ✔️        | `string`  | `UInt16`            | The transaction type (`ContractCall`).                                                                   |
| `Account`         | ✔️        | `string`  | `AccountID`         | The account sending the transaction.                                                                     |
| `ContractAccount` | ✔️        | `string`  | `AccountID`         | The contract to call.                                                                                    |
| `FunctionName`    | ✔️        | `string`  | `Blob`              | The function on the contract to call.                                                                    |
| `Parameters`      |           | `array`   | `STParameterValues` | The parameters to provide to the contract’s function. Must match the order and type of the on-chain ABI. |

### 7.2. Fee

The max number of instructions you’re willing to run (gas-esque behavior)

### 7.3. Failure Conditions

- The `ContractAccount` doesn't exist or isn't a smart contract pseudo-account.
- The function doesn't exist on the provided contract.
- The parameters don't match the function's ABI.

### 7.4. State Changes

If the transaction is successful, the WASM contract will be called. The WASM code will govern the state changes that are made.

### 7.5. Example Transaction

```javascript
{
  TransactionType: "ContractCall",
  ContractAccount: "rWYkbWkCeg8dP6rXALnjgZSjjLyih5NXm",
  FunctionName: "call_function", // could also be a number to save space
  Parameters: [
    {
      Flags: tfSendAmount,
      Amount: "1000000" // 1 XRP
    },
    {
      Flags: 0,
      Amount: {
        "currency": "USD",
        "issuer": "rJKnVATqzNsWa4jgnK5NyRKmK5s9QQWQYm",
        "value": "10"
      }
    },
    {
      Flags: 0,
      Account: "rMJAmiEQW4XUehMixb9E8sMYqgsjKfB1yC"
    },
    ...
  ]
}
```

## 8. Transaction: `ContractModify`

This transaction modifies a contract's code or instance parameters, if allowed.

### 8.1. Fields

| Field Name                | Required? | JSON Type | Internal Type       | Description                                                                                                                                        |
| :------------------------ | :-------- | :-------- | :------------------ | :------------------------------------------------------------------------------------------------------------------------------------------------- |
| `TransactionType`         | ✔️        | `string`  | `UInt16`            | The transaction type (`ContractModify`).                                                                                                           |
| `Account`                 | ✔️        | `string`  | `AccountID`         | The account sending the transaction.                                                                                                               |
| `ContractAccount`         |           | `string`  | `AccountID`         | The pseudo-account hosting the contract that is to be changed. This field is not needed if the pseudo-account is emitting this transaction itself. |
| `ContractOwner`           | ✔️        | `string`  | `AccountID`         | The new owner of the contract (so that contract ownership is transferrable).                                                                       |
| `Flags`                   |           | `number`  | `UInt32`            | Accepted bit-flags on this transaction.                                                                                                            |
| `ContractCode`            |           | `string`  | `Blob`              | The new WASM bytecode for the contract.                                                                                                            |
| `ContractHash`            |           | `string`  | `Hash256`           | The hash of the new WASM bytecode for the contract.                                                                                                |
| `Functions`               | ✔️        | `array`   | `STArray`           | The functions that are included in this contract.                                                                                                  |
| `InstanceParameters`      |           | `array`   | `STParameters`      | The parameters that are provided by a deployment of this contract.                                                                                 |
| `InstanceParameterValues` |           | `array`   | `STParameterValues` | The values of the instance parameters that apply to this instance of the contract.                                                                 |

#### 8.1.1. `Flags`

- `tfImmutable` - the code can’t be changed anymore.
- `tfCodeImmutable` - the code can’t be updated, but the instance parameters can.
- `tfABIImmutable` - the code can be updated, but the ABI cannot.
- `tfUndeletable` - the contract can’t be deleted anymore.

### 8.2. Fee

Will be equivalent to the per-byte/`init` fees of the `ContractCreate` transaction

### 8.3. Failure Conditions

- The `ContractAccount` doesn’t exist or isn’t a contract pseudo-account.
- The `Account` isn't the contract owner.
- If `ContractAccount` isn’t specified, the `Account` isn’t a contract pseudo-account.
- The contract has an `lsfImmutable` flag.
- The contract has `lsfABIImmutable` enabled and isn't backwards-compatible (function names or parameters are changed). (Note: functions may be added)
- `ContractCode` or `ContractHash` are provided but the contract has the `tfCodeImmutable` flag enabled.

### 8.4. State Changes

If the transaction is successful:

- The `Contract` object is updated accordingly.
- If the code is changed:
  - If the previous `Contract` object was the only user of a `ContractSource` object, the `ContractSource` object is deleted.
  - If the new `Contract` object does not have a corresponding existing `ContractSource` object, it is created.

## 9. Transaction: `ContractDelete`

This transaction deletes a contract. Only the pseudo-account itself or the owner of the transaction can do so.

### 9.1. Fields

| Field Name        | Required? | JSON Type | Internal Type | Description                                                                                                                                        |
| :---------------- | :-------- | :-------- | :------------ | :------------------------------------------------------------------------------------------------------------------------------------------------- |
| `TransactionType` | ✔️        | `string`  | `UInt16`      | The transaction type (`ContractDelete`).                                                                                                           |
| `Account`         | ✔️        | `string`  | `AccountID`   | The account sending the transaction.                                                                                                               |
| `ContractAccount` |           | `string`  | `AccountID`   | The pseudo-account hosting the contract that is to be changed. This field is not needed if the pseudo-account is emitting this transaction itself. |

### 9.2. Failure Conditions

- The `ContractAccount` doesn't exist or isn't a smart contract pseudo-account.
- The `ContractAccount` holds deletion blocker objects (e.g. `Escrow` or `ContractData`).
- The account submitting the transaction is neither the contract account itself nor the owner of the contract.

### 9.3. State Changes

If the transaction is successful:

- The contract will be deleted, along with the pseudo-account.
- All objects that are still owned by the account (which are not deletion blockers) will be deleted.
- All remaining XRP in the account will be returned to the owner.

## 10. Transaction: `ContractUserDelete`

This transaction allows a user to delete their data associated with a contract. Only the user can submit this transaction (if the contract wants to modify user data, it can do that from the WASM code).

This transaction will also trigger a special `user_delete` function in the contract, if it exists - which allows smart contract devs to do their own cleanup work as needed.

### 10.1. Fields

| Field Name        | Required? | JSON Type | Internal Type | Description                                                                                                                                        |
| :---------------- | :-------- | :-------- | :------------ | :------------------------------------------------------------------------------------------------------------------------------------------------- |
| `TransactionType` | ✔️        | `string`  | `UInt16`      | The transaction type (`ContractUserDelete`).                                                                                                       |
| `Account`         | ✔️        | `string`  | `AccountID`   | The account sending the transaction (the user).                                                                                                    |
| `ContractAccount` |           | `string`  | `AccountID`   | The pseudo-account hosting the contract that is to be changed. This field is not needed if the pseudo-account is emitting this transaction itself. |

### 10.2. Failure Conditions

- The `ContractAccount` doesn't exist or isn't a smart contract pseudo-account.
- The `Account` does not have any `ContractData` object for the contract in `ContractAccount`.

### 10.3. State Changes

If the transaction is successful:

- The user's `ContractData` object associated with the `ContractAccount` will be deleted.
- The `user_delete` function on the contract will be run to perform any cleanup work, if it exists.

## 11. Transaction: `ContractClawback`

This transaction allows issuers to claw back tokens from a contract, while also allowing smart contract devs to perform any cleanup they need to based on this clawback result.

This transaction will trigger a special `clawback` function in the contract, if it exists - which allows smart contract devs to do their own cleanup work as needed.

### 11.1. Fields

| Field Name        | Required? | JSON Type | Internal Type | Description                                                    |
| :---------------- | :-------- | :-------- | :------------ | :------------------------------------------------------------- |
| `TransactionType` | ✔️        | `string`  | `UInt16`      | The transaction type (`ContractClawback`).                     |
| `Account`         | ✔️        | `string`  | `AccountID`   | The account sending the transaction (the issuer of the token). |
| `ContractAccount` |           | `string`  | `AccountID`   | The pseudo-account hosting the contract that is to be changed. |
| `Amount`          | ✔️        | `object`  | `Amount`      | The amount to claw back from the contract.                     |

### 11.2. Failure Conditions

- The `ContractAccount` doesn't exist or isn't a smart contract pseudo-account.
- `Amount` is invalid in some way (e.g. is negative, token doesn't exist, is XRP).
- The `Account` isn't the issuer of the token specified in `Amount`.
- The `ContractAccount` doesn't hold the token specified in `Amount`.
- The `ContractAccount` holds the token specified in `Amount`, but holds less than the amount specified.

### 11.3. State Changes

If the transaction is successful:

- The balance of the `ContractAccount`'s token is decreased by `Amount`.

## 12. Transaction Common Fields

This standard doesn't add any new field to the [transaction common fields](https://xrpl.org/docs/references/protocol/transactions/common-fields/), but it does add another global transaction flag and add another metadata field.

### 12.1. `Flags`

| Flag Name                | Value        |
| :----------------------- | :----------- |
| `tfContractSubmittedTxn` | `0x20000000` |

This flag should only be used if a transaction is submitted from a smart contract. This signifies that the transaction shouldn't be signed. Any transaction that is submitted normally that includes this flag should be rejected.

Contract-submitted transactions will be processed in a method very similar to [Batch inner transactions](https://github.com/XRPLF/XRPL-Standards/tree/master/XLS-0056-batch) - i.e. executed within the `ContractCall` processing, rather than as a separate independent transaction. This allows the smart contract code to take actions based on whether the transaction was successful.

### 12.2. Metadata

Every contract-submitted transaction will contain an extra metadata field, `ParentContractCallId`, containing the hash of the `ContractCall` transaction that triggered its submission.

## 13. RPC: `contract_info`

This RPC fetches info about a deployed contract.

### 13.1. Request Fields

| Field Name         | Required? | JSON Type | Description                                             |
| :----------------- | :-------- | :-------- | :------------------------------------------------------ |
| `contract_account` | ✔️        | `string`  | The pseudo-account hosting the contract.                |
| `function`         |           | `string`  | The function to specifically get information for.       |
| `user_account`     |           | `string`  | An account to specifically get the contract’s data for. |

### 13.2. Response Fields

| Field Name         | Always Present?                              | JSON Type | Description                                                                  |
| :----------------- | :------------------------------------------- | :-------- | :--------------------------------------------------------------------------- |
| `contract_account` | ✔️                                           | `string`  | The pseudo-account hosting the contract.                                     |
| `code`             | ✔️                                           | `string`  | The WASM bytecode for the contract.                                          |
| `account_info`     | ✔️                                           | `object`  | The `account_info` output of the `contract_account`.                         |
| `functions`        | ✔️                                           | `array`   | The functions in the smart contract and their parameters.                    |
| `source_code_uri`  |                                              | `string`  | The URI pointing to the source code of the contract (if it exists on-chain). |
| `contract_data`    |                                              | `object`  | The contract’s stored data.                                                  |
| `user_data`        | If `user_account` is included in the request | `object`  | The contract’s stored data pertaining to that user.                          |

#### 13.2.1. `functions`

Each object in the array will contain the following fields:

| Field Name   | Always Present? | JSON Type | Description                                                                                                                                        |
| :----------- | :-------------- | :-------- | :------------------------------------------------------------------------------------------------------------------------------------------------- |
| `name`       | ✔️              | `string`  | The name of the function.                                                                                                                          |
| `parameters` | ✔️              | `array`   | A list of the parameters accepted for the function, in the format described above. This will be an empty list if the function takes no parameters. |
| `fees`       | ✔️              | `string`  | The amount, in XRP, that you would likely have to pay to execute this function. _TODO: not sure how doable this is, but it'd be nice if possible_  |

## 14. RPC Subscription: `eventEmitted`

Subscribe to events emitted from a contract.

### 14.1. Request Fields

| Field Name         | Required? | JSON Type | Description                                                                                                                  |
| :----------------- | :-------- | :-------- | :--------------------------------------------------------------------------------------------------------------------------- |
| `contract_account` | ✔️        | `string`  | The pseudo-account hosting the contract.                                                                                     |
| `events`           |           | `array`   | The event types to subscribe to, as an `array` of `string`s. If omitted, all events from the contract will be subscribed to. |

TODO: maybe you should also be able to subscribe to all instances of a `ContractSource`?

### 14.2. Response Fields

| Field Name         | Always Present? | JSON Type | Description                                                         |
| :----------------- | :-------------- | :-------- | :------------------------------------------------------------------ |
| `contract_account` | ✔️              | `string`  | The pseudo-account hosting the contract.                            |
| `events`           | ✔️              | `array`   | The events that were emitted from the contract, as explained below. |
| `hash`             | ✔️              | `string`  | The hash of the transaction that triggered the event.               |
| `ledger_index`     | ✔️              | `number`  | The ledger index in which the event was triggered.                  |

#### 14.2.1. `events`

Each object in the `events` array will contain the following fields:

| Field Name | Always Present? | JSON Type | Description                              |
| :--------- | :-------------- | :-------- | :--------------------------------------- |
| `name`     | ✔️              | `string`  | The name of the event.                   |
| `data`     | ✔️              | `object`  | The data emitted as a part of the event. |

The rest of the fields in this object will be dev-defined fields from the emitted event.

## 15. RPC Subscription: `event_history`

Fetch a list of historical events emitted from a given contract account.

### 15.1. Request Fields

| Field Name         | Required? | JSON Type     | Description                                                                                                                                                                                                                                                                                                                        |
| :----------------- | :-------- | :------------ | :--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `contract_account` | ✔️        | `string`      | The pseudo-account hosting the contract.                                                                                                                                                                                                                                                                                           |
| `events`           |           | `array`       | The event types to retrieve, as an `array` of `string`s. If omitted, all events from the contract will be retrieved.                                                                                                                                                                                                               |
| `ledger_index_min` |           | `number`      | Use to specify the earliest ledger to include events from. A value of `-1` instructs the server to use the earliest validated ledger version available.                                                                                                                                                                            |
| `ledger_index_max` |           | `number`      | Use to specify the most recent ledger to include events from. A value of `-1` instructs the server to use the most recent validated ledger version available.                                                                                                                                                                      |
| `ledger_index`     |           | `LedgerIndex` | Use to look for events from a single ledger only.                                                                                                                                                                                                                                                                                  |
| `ledger_hash`      |           | `string`      | Use to look for events from a single ledger only.                                                                                                                                                                                                                                                                                  |
| `binary`           |           | `boolean`     | Defaults to `false`. If set to `true`, returns events as hex strings instead of JSON.                                                                                                                                                                                                                                              |
| `limit`            |           | `number`      | Default varies. Limit the number of events to retrieve. The server is not required to honor this value.                                                                                                                                                                                                                            |
| `marker`           |           | `any`         | Value from a previous paginated response. Resume retrieving data where that response left off. This value is stable even if there is a change in the server's range of available ledgers. See [here](https://xrpl.org/docs/references/http-websocket-apis/api-conventions/markers-and-pagination) for details on how markers work. |
| `transactions`     |           | `boolean`     | Defaults to `false`. If set to `true`, returns the whole transaction in addition to the event. If set to falls, returns only the transaction hash.                                                                                                                                                                                 |

### 15.2. Response Fields

| Field Name         | Always Present? | JSON Type | Description                                                                                                               |
| :----------------- | :-------------- | :-------- | :------------------------------------------------------------------------------------------------------------------------ |
| `contract_account` | ✔️              | `string`  | The pseudo-account hosting the contract.                                                                                  |
| `events`           | ✔️              | `array`   | The events that were emitted from the contract.                                                                           |
| `ledger_index_min` |                 | `number`  | The ledger index of the earliest ledger actually searched for events.                                                     |
| `ledger_index_max` |                 | `number`  | The ledger index of the most recent ledger actually searched for events.                                                  |
| `limit`            |                 | `number`  | The limit value used in the request. (This may differ from the actual limit value enforced by the server.)                |
| `marker`           |                 | `any`     | Server-defined value indicating the response is paginated. Pass this to the next call to resume where this call left off. |

#### 15.2.1. `events`

Each object in the `events` array will contain the following fields:

| Field Name  | Always Present? | JSON Type | Description                                                                                                                                                    |
| :---------- | :-------------- | :-------- | :------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `name`      | ✔️              | `string`  | The name of the event.                                                                                                                                         |
| `data`      |                 | `object`  | The data emitted as a part of the event, in JSON. Included if `binary` is set to `false`.                                                                      |
| `data_blob` |                 | `string`  | The data emitted as a part of the event, in binary. Included if `binary` is set to `true`.                                                                     |
| `tx_json`   |                 | `object`  | The transaction that triggered the event, in JSON. Included if `transactions` is set to `true` and `binary` is set to `false`.                                 |
| `tx_blob`   |                 | `string`  | The transaction that triggered the event, in binary. Included if `transactions` is set to `true` and `binary` is set to `true`.                                |
| `tx_hash`   |                 | `string`  | The transaction that triggered the event, in binary. Included if `transactions` is set to `false`.                                                             |
| `validated` |                 | `boolean` | Whether or not the transaction that contains this event is included in a validated ledger. Any transaction not yet in a validated ledger is subject to change. |

### 15.3. Implementation Details

This RPC will use the account transactions database. It will iterate through all `ContractCall` transactions sent to the provided `contract_account` and filter out the events based on the other provided parameters.

## 16. UNL-Votable Parameters

- Number of drops per instruction run (in some unit that allows this to be <1)
- Maximum number of instructions allowed in a single transaction
  - Maybe separate values for contracts vs subroutines (and maybe separate values for each subroutine)
- Memory limits
- Memory costs?

Initial values will be high fees/low maxes, but via the standard UNL voting process for fees, this can be adjusted over time as needed.

## 17. Serialized Type: `STParameters`

This object is essentially just a list of `(Flag, SType value)` groupings.

- Name (maybe just a number to save space?)
  - This might not be needed - maybe just the parameters are encoded this way
- UInt16 indicating required flags
- Number of parameters
- For each parameter:
  - UInt32 indicating the required flags for each param (e.g. “this should send real money”)
  - UInt16 indicating the parameter STypes
- TODO: we might need an additional `SType` to describe a parameter
  - `UInt32` for flags
  - `UInt16` for SType
  - However many bytes for the encoded data

JSON representation is a name/number and the string names of the STypes - for example:

```javascript
[
  {
    name: "transfer", // may also be a number (for a smaller size)
    parameters: [
      (0, "UInt32"), // could also be a dictionary
      (tfSendAmount, "STAmount"),
      (0, "AccountID"),
    ],
  },
];
```

## 18. Serialized Type: `STParameterValues`

This object is essentially just a list of ``(Flag, SType value, value that is of type `SType`)`` groupings.

Each of these groupings looks like this:

- UInt32 indicating the required flags for each param (e.g. “this should send real money”)
- UInt16 indicating the parameter SType
- The byte encoding of the Value

JSON representation is a name/number and the string representation of the values - for example:

```javascript
[
  (0, "UInt32", 1234), // could also be a dictionary
  (tfSendAmount, "STAmount", "1000000000"),
  (0, "AccountID", "rABCD...")
}
```

## 19. Serialized Type: `STData`

The following, serialized one after another:

- Key-value pairs - this is repeated as many times as needed to cover all the data
  - A VL-encoded “key” (this could potentially be an `SType` if needed? Or just a number that the ABI defines?)
  - A VL-encoded “value”
- TODO: you probably want a way to nest dictionaries
- TODO: should this be called `STJson` instead and just handle JSON data?

JSON representation is a dictionary with the key-value pairs - for example:

```javascript
{
  "count": 3,
  "total": 12,
  "destination": "r3PDXzXky6gboMrwUrmSCiUyhzdrFyAbfu"
}
```

## 20. Examples

### 20.1. Sample Code

_Note: this is entirely made up, and is only intended to provide a rough idea of the concepts described in this document. The exact syntax is heavily subject to change (during both design iterations and in the implementation phase, as more details are figured out). For example, the final version will likely be in Rust._

```javascript
// This sample function pays the destination some funds and transfers some data to the destination
function transfer(UInt16 number, STAmountSend amount, AccountID destination)
{
  const { balance } = getUserData(this, this.caller)
  if (!balance || balance < number)
    reject("Not enough balance") // error message included in metadata
  const { balance: destBalance } = getUserData(this, destination)
  if (!destBalance)
    return "Destination hasn't authorized data" // failure
  setUserData(this, this.caller, { balance: balance - number }) // assuming the "user data and reserves are handled by the user" model of contract data reserves
  setUserData(this, destination, { balance: balance + number })
  submitTransaction({
    TransactionType: "Payment",
    Destination: destination,
    Amount: amount
  })
  console.log("Transfer finished") // This is printed in the rippled debug.log (for testing purposes)
  emitEvent("transfer", {
    account: this.caller,
    destination: destination,
    number: number,
    amount: amount
  }) // this is included in the metadata - there can be limits on how much data may be included
  return 0 // success
}
```

- Submitting transactions is like Hooks - the pseudo-account essentially “sends” transactions to do all of its on-chain modifications (other than contract-specific state)
- There's a special `init()` function that allows you to do any initial account setup (instead of needing to do it in a separate function call)
- `emitEvent` is used to emit an event that is stored in the metadata

## 21. Invariants

- No `ContractSource` object should have a `ReferenceCount` of 0
- Every `Contract` object should have an existing corresponding `ContractSource` object
- A `Contract` cannot have both `lsfImmutable` and `lsfCodeImmutable` enabled.

## 22. Security

### 22.1. Pseudo-Account Account-Level Permissions

These settings will all be enabled by default on a pseudo-account:

- Disable master key
- Enable `DepositAuth`

These functions will all be disallowed from pseudo-accounts:

- `SignerListSet`
- `SetRegularKey`
- Enable master key
- Disable `DepositAuth`
- `AccountPermissionsSet`

This prevents the contract account from receiving any funds directly (i.e. outside of the `ContractCall` transaction) and prevents any other account (malicious or otherwise) from submitting transactions directly from the contract account. This ensures that the contract account’s logic is entirely governed by the code, and nothing else.

### 22.2. Scam Contracts

Any amount you send to a contract can be rug-pulled. This is the same level of risk as any other scam on the XRPL right now - such as buying a rug-pulled token.

### 22.3. Fee-Scavenging/Dust Attacks

Don’t think this is possible here.

### 22.4. Re-entrancy Attacks

These will need to be guarded against in this design. One option for this is to disallow any recursion in calls - i.e. disallow `ContractCall` transactions from a contract account to itself. Other options are being investigated.

# Open Questions

- Pre-load all the contract instance params when opening the VM so it’s not expensive to fetch them?
- How should a contract handle if someone sends a token they don’t have a trustline for?
- [Borsh](https://borsh.io/) instead of JSON for `STData`?
  - Consider other binary encodings alongside consideration of Borsh (e.g., maybe [SSZ](https://ethereum.org/developers/docs/data-structures-and-encoding/ssz/) or [SCALE](https://github.com/paritytech/parity-scale-codec))
- Readonly contract functions like EVM? Might be for v2, or might be unnecessary given the human-readability of the `STData` type
- Should `ContractData` objects be stored in a separate directory structure (e.g. a new one, not the standard owner directory)?
- What should happen if `user_delete` or `clawback` fails or crashes in some way?
  - If it crashes due to running out of `ComputationAmount` the transaction should probably fail, if it crashes/fails for anything else (that is a result of the WASM code) the transaction should probably succeed
- Consider a separate data spec, possibly including the concept of Rent.
- What should happen to Gas fees -- burn them? Pay them out? something else?

## Reserves

The biggest remaining question (from the core ledger design perspective) is how to handle object reserves for any contract-specific data (reserves for all existing ledger entries can be handled as they are now).

The most naive option is for the contract account to hold all necessary funds for the reserves. However, this is quite the burden on the contract account (and therefore the deployer of the contract). Ideally, there should be some way to put some of the burden on the contract users for the parts of the data that they use.

One example to illustrate the difference: an ERC-20 contract holds all of its data (e.g. holders and the amount they hold) in the contract itself. However, on the XRPL, an MPT issuer does not need to cover reserves for all of its holders and their data - only the reserves for the issuance data. The EVM doesn’t have the concept of reserves (it’s essentially amortized in the transaction fees), this concern doesn’t apply to those chains.

### Account Reserve

The account reserve is essentially covered by the non-refundable `ContractCreate` transaction fee. This also covers the reserve for the `Contract`/`ContractSource` ledger entry, if needed.

TODO: perhaps there should also be limits on fields you can set in the `AccountRoot`.

### Object Reserve

How should object reserves be covered? Some options (numbered for ease of discussion):

1. You get some free objects via the `ContractCreate` fee and there's a hard cap. Higher fees for more reserves.
   - There could also be a way to up this number later (some sort of reserve bump transaction, maybe, with additional fees), that anyone can call.
2. Higher fees for anything that increases reserve on the account (reserves essentially burned)
   - Downside: it becomes harder to calculate a contract call tx fee because you don't know what will require more reserve
3. Some way to amortize higher fees for increasing reserve (a la EVM)
   - Could be on the contract writer to figure out a way to handle this
   - If not, could be complex to figure out a good system
4. A [Sponsor](../XLS-0068-sponsored-fees-and-reserves/README.md)-esque way of keeping track of who owns the burden for certain objects (perhaps with some API calls - could default to the contract creator if the API isn't used)
   - Downside: it would likely add an additional dependency to smart contracts (XLS-68)
5. Ignore the issue
   - This isn’t really a viable option, given the ledger load it would result in - it would defeat the purpose of reserves in the first place
6. User data and reserves are handled by the user
   - Inspired by Move
   - A “user data” object for contracts to store data for a particular user
   - Hash is `Contract ID` + `Account`, only one object stores all of a user’s data
   - N bytes per reserve charged (perhaps N=256), with some sort of limit towards the max amount of reserves that can be charged
   - Maybe a flag on function call to indicate acceptance of reserve usage
     - Or maybe you include a number of acceptable reserves?
   - Transaction to delete user data (to recover reserves) - contracts need to support this
     - Is this acceptable?
     - You can’t recover an escrow reserve until it’s cancellable or finishable so maybe this isn’t needed and it’ll be a norm
   - Object is a deletion blocker (for the contract and the user)

The authors lean towards something akin to Option 6, as it feels the most XRPL-y, but supporting data deletion becomes complicated, because otherwise contract developers can lock up users’ reserves without them being able to free that reserve easily.

# Appendix

## Appendix A: FAQ

### A.1: How does this compare to Hooks?

The main similarities:

- The smart contract API is mostly the same. The biggest changes are renaming functions (and a couple of extra methods added).
- Smart contracts interact with XRPL primitives by submitting/emitting transactions.
- A “contract definition” object is used so that the ledger doesn’t need to store the same data repeatedly.
- A WASM VM is used to process the smart contract code.

The main differences:

- Smart contracts are installed on pseudo-accounts instead of user accounts.
- Instead of being triggered by transactions, there is a special `ContractCall` transaction to trigger the smart contract.
- Smart contract data is stored differently.
- Users handle the reserves for their own data, instead of it all being handled by the smart contract account (TBD).
- Smart contracts can emit events that developers can subscribe to.
- Tools can auto-generate ABIs from source code (and ABIs are stored on-chain).

### A.2: How does this compare to EVM?

The main similarities:

- Smart contracts are installed at their own addresses.
- Smart contracts are organized by functions, and they are called by transactions that encode the function to call and its parameters.
- Smart contracts can emit events that developers can subscribe to.

The main differences:

- Since the XRPL has native features/primitives (unlike EVM chains), transaction emission allows smart contracts to interact with those primitives.
- Additional complexities due to the XRPL’s reserve system.
- A “contract definition” object is used so that the ledger doesn’t need to store the same data repeatedly (for example, Uniswap and ERC-20 contracts are repeatedly deployed onto EVM chains, adding a lot of data bloat).
  - For example, Uniswap v2 (the exact code) is [deployed](https://etherscan.io/find-similar-contracts?a=0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f&m=exact&ps=25&mt=0) more than 2,500 times across the 53 EVM chains that Etherscan tracks. This design paradigm would reduce that to 53 (one per chain).
- The VM used is WASM, not EVM.
- ABIs are stored on-chain.

### A.3: How can I implement account logic (like in Hooks) with this form of smart contracts?

Use something akin to Ethereum’s Account Abstraction design ([ERC-4337](https://www.erc4337.io/)).

Might involve [XLS-75 (Permission Delegation)](../XLS-0075-permission-delegation/README.md).

We're also investigating whether additional Smart Features can help with this problem.

### A.4: Will I be able to transfer (or copy/paste) EVM/SolVM/MoveVM/etc. bytecode to the XRPL?

No (well, not without a special tool that will do the conversion for you).

### A.5: Will I be able to write smart contracts in Solidity?

Solidity will not be prioritized by our team right now, but there are Solidity-to-WASM compilers that someone could use to make this possible.

Note that the syntax would likely not be the exact same as in the EVM. In addition, the conceptual meanings may not map either - for example, addresses are different between the EVM and the XRPL.

### A.6: Will I be able to implement something akin to ERC-20 with an XRPL smart contract?

Yes, but it will be more expensive and less efficient than the existing token standards (IOUs and MPTs) and won’t be integrated into the DEX or other parts of the XRPL.

An alternative strategy would be to create a smart contract that essentially acts as a wrapper to the XRPL’s native functionalities (e.g. a `mint` function that just issues a token via a `Payment` transaction).

### A.7. How will fees be handled for contract-submitted transactions?

It’ll be included in the fees paid for the contract call.

### A.8. What happens if a smart contract pseudo-account’s funds are clawed back, or are locked/frozen?

That’s for the smart contract author to deal with, just like in the EVM world.

### A.9: What languages can/will be supported?

Any language that can compile to WASM can be supported. We will likely start with Rust.

### A.10: Can a smart contract execute a multi-account Batch transaction with another account?

Yes, if the smart contract account submits the final transaction. Constructing a multi-account Batch transaction between two smart contracts will not be possible as a part of this spec. Support for that could be added with a separate design.

### A.11: Can I use [Smart Escrows](https://docs.google.com/document/u/0/d/1upiaBSHF8pTeHvdHcJ0BwPxwFK_znpsSJr1PToZY0Do/edit) with Smart Contracts?

Yes, a smart contract can emit an `EscrowCreate` transaction that has a `FinishFunction`.

### A.12: Will this design support read-only functions like EVM?

Not in the initial version/design, to keep it simple. This could be added in the future, though.

### A.13: How do I get the transaction history of a Contract Account?

Use the existing `account_tx` RPC.

### A.14: How does this design prevent abuse/infinite loops from eating up rippled resources, while allowing for sufficient compute for smart contract developers?

The `UNL-Votable Parameters` section addresses this. The UNL can adjust the parameters based on the needs and limitations of the network, to ensure that developers have enough computing resources for their needs, while ensuring that they cannot overrun the network with their contracts.

### A.15: Why store the ABI on-chain instead of in an Etherscan-like system?

Having the data on-chain removes the need for a centralized party to maintain this data - all the data to interact with a contract is available on-chain. This also means that it’s much easier (and therefore faster) for `rippled` to determine if the data passed into a contract function is valid, instead of needing to open up the WASM engine for that.

The tradeoff is that this means a contract will take up more space on-chain, and we need new STypes to store that information properly.
