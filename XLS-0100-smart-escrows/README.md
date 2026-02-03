<pre>
  title: Smart Escrows
  description: Custom release conditions for escrows written in WebAssembly (WASM)
  created: 2025-02-25
  updated: 2025-11-20
  author: Mayukha Vadari (@mvadari), David Fuelling (@sappenin)
  proposal-from: https://github.com/XRPLF/XRPL-Standards/discussions/270
  status: Draft
  category: Amendment
</pre>

## 1. Abstract

This proposal introduces a new layer of programmability to XRPL Escrows, enabling conditions beyond the current time-based or crypto-conditional constraints. The idea is to allow a small piece of code to reside on the `Escrow` object itself, controlling whether the escrow can be released or canceled. By adding programmatic conditions, we can expand the XRPL’s utility, making Escrows more versatile for scenarios such as notary approvals, compliance holds, and P2P conditional transactions.

## 2. Motivation

Smart Escrows are a first step toward expanding XRPL’s on-ledger functionality, enhancing use cases like auction mechanics, cascading real estate escrows, and peer-to-peer bets using oracle data, all within the security of the XRPL itself.

### 2.1. Example Use-Cases

- **Notary Escrows**: Only a specific account can release an escrowed asset.
- **Temporary Holds**: Hold funds for compliance checks or KYC verification.
- **Achievement Rewards**: Unlock funds upon the completion of a certification or milestone.
- **Closed Airdrops**: Enable token receipt only for holders of specific NFTs.
- **P2P Bets**: Enable value transfer based on oracle data, such as whether XRP’s price reaches a target value on a given date.
- **"Options" Contracts**: Condition release based on price oracles or DEX prices for derivative or options-like structures.
- **Token Swaps**: Trustless token swaps where one escrow releases funds only once another escrow is created.
- **NFT-Based Releases**: Condition the release of funds on the transfer or sale of a particular NFT.
- **Token Vesting**: Lock assets for investors, allowing gradual or milestone-based release.
- **Cascading Escrows**: Link escrows in sequences where one escrow depends on the completion of another (e.g., real estate transactions).
- **Auction Mechanisms**: Lock funds for auction participants, with conditions for finalization based on bid outcomes.
- **Treasury Management**: Structure conditions for internal treasury and custodial operations.

## 3. Overview

The design involves a minimal, programmable code block attached to an Escrow object that executes logic to determine whether the Escrow can be completed. This follows the model of a restricted, on-ledger “smart contract,” where conditions can be coded and verified directly on-chain. This is an incremental extension of XRPL's CryptoConditions, enhancing flexibility with custom validation while maintaining computational limits and simplicity.

The code block is attached to the Escrow on creation (in an `EscrowCreate` transaction) and executed on an `EscrowFinish` transaction for that escrow.

This design is essentially an extension of the idea of [using an Escrow as a Smart Contract](https://xrpl.org/docs/tutorials/how-tos/use-specialized-payment-types/use-escrows/use-an-escrow-as-a-smart-contract#use-an-escrow-as-a-smart-contract).

The details of the WASM engine and the API are in a separate XLS.

This proposal involves:

- Modifications to the `Escrow` and `FeeSettings` ledger objects
- Modifications to the `EscrowCreate`, `EscrowFinish`, and `SetFee` transactions

This feature will require an amendment, tentatively titled `SmartEscrow`.

### 3.1. Background: XRPL Escrows

There are currently two ways to release an escrow: **Time-based** and **Condition-based.**

A **time-based** escrow releases its funds after a certain specified time. In more technical terms, a time-based escrow has the `FinishAfter` field and can be released anytime after the time specified in the `FinishAfter` field.

A **condition-based** escrow essentially only releases its funds if a password is provided. In more technical terms, a condition-based escrow has the `Condition` field and can be released if the matching `Fulfillment` field (essentially the reverse of a hash) is provided on the `EscrowFinish` transaction.

#### 3.1.1. Table of Allowed Options

Currently, these are the combinations of allowed escrow options:

| Summary                           | `FinishAfter` | `Condition` | `CancelAfter` |
| :-------------------------------- | :------------ | :---------- | :------------ |
| Time-based                        | ✔️            |             |               |
| Time-based with expiration        | ✔️            |             | ✔️            |
| Timed conditional                 | ✔️            | ✔️          |               |
| Timed conditional with expiration | ✔️            | ✔️          | ✔️            |
| Conditional with expiration       |               | ✔️          | ✔️            |

### 3.2. Background: Crypto-Conditions

Crypto conditions are a standardized way to express a wide range of conditional requirements. These include something like hashlocks (essentially a password), but crypto-conditions also support more complex constructions like multi-signature requirements (note: this is different from the [existing XRPL multi-signature design](https://xrpl.org/docs/concepts/accounts/multi-signing)) or conditions involving specific data. When used to execute Escrows, the XRP Ledger currently only supports hashlock-like conditions, and not the full suite of available [Crypto Conditions](https://github.com/rfcs/crypto-conditions).

For more information around how crypto-conditions work with escrows, see [here](https://xrpl.org/docs/use-cases/payments/smart-contracts-uc#conditionally-held-escrow).

### 3.3. Background: XRPL Extensions

An **XRPL Extension** is a small piece of code attached to an XRPL building block, which allows users to add some custom logic to the existing primitives. This can be very useful for projects that like the existing features of the XRPL, but need a minor modification to a feature to be able to use it.

See [the blog post here](https://dev.to/ripplexdev/a-proposed-vision-for-xrp-ledger-programmability-1gdj) for more details.

## 4. Serialized Type: `STInt32`

### 4.1. `SType` Value

The `SType` value for `Int32` is `12`.

### 4.2. JSON Representation

An `Int32` will be represented as a `number` (or `int`) in JSON, in a fairly standard manner.

### 4.3. Additional Accepted JSON Inputs

Alternate inputs include:

- `uint` (if the value is less than `int32::max`)
- `string` (decimal unless a `0x` or `0b` prefix is used)

### 4.4. Binary Encoding

An `Int32` will be encoded in standard `int` [two's complement](https://en.wikipedia.org/wiki/Two%27s_complement) encoding.

### 4.5. Example JSON and Binary Encoding

`1` will be encoded as `0001`. `-1` will be encoded as `ffff`.

## 5. Ledger Entry: `Escrow`

The [`Escrow` object](https://xrpl.org/escrow-object.html) already exists on the XRPL. We propose a slight modification to support Smart Escrows.

### 5.1. Fields

<details>
<summary>

As a reference, [here](https://xrpl.org/docs/references/protocol/ledger-data/ledger-entry-types/escrow#escrow-fields) are the existing fields for the `Escrow` object.

</summary>

| Field Name          | Required? | JSON Type | Internal Type | Description                                                                                                                                                                                                                            |
| :------------------ | :-------- | :-------- | :------------ | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `Account`           | ✔️        | `string`  | `AccountID`   | The address of the owner (sender) of this escrow. This is the account that provided the funds, and gets it back if the escrow is canceled.                                                                                             |
| `Amount`            | ✔️        | `string`  | `Amount`      | The amount of funds currently held in the escrow.                                                                                                                                                                                      |
| `CancelAfter`       |           | `number`  | `UInt32`      | The escrow can be canceled if and only if this field is present \_and_the time it specifies has passed.                                                                                                                                |
| `Condition`         |           | `string`  | `Blob`        | A [PREIMAGE-SHA-256 crypto-condition](https://tools.ietf.org/html/draft-thomas-crypto-conditions-02#section-8.1), as hexadecimal. If present, the `EscrowFinish` transaction must contain a fulfillment that satisfies this condition. |
| `Destination`       | ✔️        | `string`  | `AccountID`   | The destination address where the funds are paid if the escrow is successful.                                                                                                                                                          |
| `DestinationNode`   |           | `string`  | `UInt64`      | A hint indicating which page of the destination's owner directory links to this object, in case the directory consists of multiple pages.                                                                                              |
| `DestinationTag`    |           | `number`  | `UInt32`      | An arbitrary tag to further specify the destination for this escrow, such as a hosted recipient at the destination address.                                                                                                            |
| `FinishAfter`       |           | `number`  | `UInt32`      | The time after which this escrow can be finished. Any `EscrowFinish` transaction before this time fails.                                                                                                                               |
| `LedgerEntryType`   | ✔️        | `string`  | `UInt16`      | The value `0x0075`, mapped to the string `Escrow`, indicates that this is an `Escrow` entry.                                                                                                                                           |
| `OwnerNode`         | ✔️        | `string`  | `UInt64`      | A hint indicating which page of the sender's owner directory links to this entry, in case the directory consists of multiple pages.                                                                                                    |
| `PreviousTxnID`     | ✔️        | `string`  | `Hash256`     | The identifying hash of the transaction that most recently modified this entry.                                                                                                                                                        |
| `PreviousTxnLgrSeq` | ✔️        | `number`  | `UInt32`      | The index of the ledger that contains the transaction that most recently modified this entry.                                                                                                                                          |
| `SourceTag`         |           | `number`  | `UInt32`      | An arbitrary tag to further specify the source for this escrow, such as a hosted recipient at the owner's address.                                                                                                                     |

</details>

We propose two additional fields:

| Field Name       | Required? | JSON Type | Internal Type | Description                                                                                              |
| :--------------- | :-------- | :-------- | :------------ | :------------------------------------------------------------------------------------------------------- |
| `FinishFunction` |           | `string`  | `Blob`        | Compiled WebAssembly (WASM) code that must execute correctly for the escrow to finish (size limits TBD). |
| `Data`           |           | `string`  | `Blob`        | User-defined extra data that can be accessed and modified by the `FinishFunction` (size limits TBD).     |

#### 5.1.1. `FinishFunction`

The compiled WASM code included in this field must contain a function named `finish` that takes no parameters and returns a signed integer (`int32`). If the function returns a value greater than 0, the escrow can be finished. Otherwise, the escrow cannot be finished. The function is triggered by an `EscrowFinish` transaction.

See Section 7 for more details.

### 5.2. Reserves

An `Escrow` object with a `FinishFunction` will cost 1. additional object reserve per 500 bytes (beyond the first 500 bytes, which are included in the first object reserve).

## 6. Transaction: `EscrowCreate`

The [`EscrowCreate` transaction](https://xrpl.org/escrowcreate.html) already exists on the XRPL. We propose a slight modification to support Smart Escrows.

### 6.1. Fields

<details>
<summary>

As a reference, [here](https://xrpl.org/docs/references/protocol/transactions/types/escrowcreate) are the existing fields for the `EscrowCreate` transaction.

</summary>

| Field Name       | Required? | JSON Type | Internal Type | Description                                                                                                                                                                                                                                                                                                                                                           |
| :--------------- | :-------- | :-------- | :------------ | :-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `Amount`         | ✔️        | `Amount`  | `Amount`      | Amount to deduct from the sender's balance and escrow.                                                                                                                                                                                                                                                                                                                |
| `Destination`    | ✔️        | `string`  | `AccountID`   | Address to receive escrowed funds.                                                                                                                                                                                                                                                                                                                                    |
| `Condition`      |           | `string`  | `Blob`        | Hex value representing a [PREIMAGE-SHA-256 crypto-condition](https://tools.ietf.org/html/draft-thomas-crypto-conditions-02#section-8.1). The funds can only be delivered to the recipient if this condition is fulfilled. If the condition is not fulfilled before the expiration time specified in the `CancelAfter` field, the funds can only revert to the sender. |
| `CancelAfter`    |           | `number`  | `UInt32`      | The time when this escrow expires. This value is immutable; the funds can only be returned to the sender after this time.                                                                                                                                                                                                                                             |
| `FinishAfter`    |           | `number`  | `UInt32`      | The time when the escrowed funds can be released to the recipient. This value is immutable, and the funds can't be accessed until this time.                                                                                                                                                                                                                          |
| `DestinationTag` |           | `number`  | `UInt32`      | Arbitrary tag to further specify the destination for this escrowed payment, such as a hosted recipient at the destination address.                                                                                                                                                                                                                                    |

</details>

We propose two additional fields:

| Field Name       | Required? | JSON Type | Internal Type | Description                                                                                                        |
| :--------------- | :-------- | :-------- | :------------ | :----------------------------------------------------------------------------------------------------------------- |
| `FinishFunction` |           | `string`  | `Blob`        | Compiled WASM code that serves as an additional condition that must pass for an escrow to be finished (completed). |
| `Data`           |           | `string`  | `Blob`        | User-defined extra data that can be accessed and modified by the `FinishFunction`.                                 |

Some rules about what conditions must be satisfied for a valid `EscrowCreate` transaction:

- Must have at least one of `CancelAfter`, `FinishAfter`, or `FinishFunction`. A `Condition` may still be specified, if desired.
- If multiple finish conditions are included, they must _all_ be true (in other words, AND not OR).
- If the `FinishFunction` field is included, then `CancelAfter` must also be included. For at least initial release of this feature, the escrow must be cancellable, in case something goes wrong with the `FinishFunction` code. _Note: A function-based escrow without an expiration could be added in the future._

_This table format is taken from [here](https://xrpl.org/docs/references/protocol/transactions/types/escrowcreate#escrowcreate-fields)._

**Bold** = new options

| Summary                                             | `FinishAfter` | `Condition` | `CancelAfter` | `FinishFunction` |
| :-------------------------------------------------- | :------------ | :---------- | :------------ | :--------------- |
| Time-based                                          | ✔️            |             |               |                  |
| Time-based with expiration                          | ✔️            |             | ✔️            |                  |
| Timed conditional                                   | ✔️            | ✔️          |               |                  |
| Timed conditional with expiration                   | ✔️            | ✔️          | ✔️            |                  |
| Conditional with expiration                         |               | ✔️          | ✔️            |                  |
| **Function-based with expiration**                  |               |             | ✔️            | ✔️               |
| **Timed Function with expiration**                  | ✔️            |             | ✔️            | ✔️               |
| **Conditional Function with expiration**            |               | ✔️          | ✔️            | ✔️               |
| **Time-based Conditional Function with expiration** | ✔️            | ✔️          | ✔️            | ✔️               |

### 6.2. Transaction Fee

An `EscrowCreate` with a `FinishFunction` costs costs 100 drops ($base\_fee * 10$) + 5 drops per byte in the `FinishFunction`.

### 6.3. Failure Conditions

The existing failure conditions still apply.

These failure conditions are added, if `FinishFunction` is included:

- The combination of fields specified in `FinishAfter`, `Condition`, `CancelAfter`, and `FinishFunction` is not allowed based on the above table.
- The hex code specified in `FinishFunction` is not valid WASM, or does not follow the specifications of the `FinishFunction` (specified in section 7).
- The length of `FinishFunction` is greater than the size limit (specified in `FeeSettings` below)

### 6.4. State Changes

There are no additional state changes, other than adding the new fields to the `Escrow` object.

## 7. Transaction: `EscrowFinish`

The [`EscrowFinish` transaction](https://xrpl.org/docs/references/protocol/transactions/types/escrowfinish) already exists on the XRPL. We propose a slight modification to support Smart Escrows.

### 7.1. Fields

<details>
<summary>

As a reference, [here](https://xrpl.org/docs/references/protocol/transactions/types/escrowfinish) are the existing fields for the `EscrowFinish` transaction.

</summary>

| Field           | Required? | JSON Type | Internal Type | Description                                                                                                                                                         |
| :-------------- | :-------- | :-------- | :------------ | :------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `Owner`         | ✔️        | `string`  | `AccountID`   | The source account that funded the escrow.                                                                                                                          |
| `OfferSequence` | ✔️        | `number`  | `UInt32`      | Transaction sequence of `EscrowCreate` transaction that created the escrow to finish.                                                                               |
| `Condition`     |           | `string`  | `Blob`        | The (previously-supplied) [PREIMAGE-SHA-256 crypto-condition](https://tools.ietf.org/html/draft-thomas-crypto-conditions-02#section-8.1) of the escrow.             |
| `CredentialIDs` |           | `array`   | `Vector256`   | Set of Credentials to authorize a deposit made by this transaction. Each member of the array must be the ledger entry ID of a Credential entry in the ledger.       |
| `Fulfillment`   |           | `string`  | `Blob`        | The [PREIMAGE-SHA-256 crypto-condition fulfillment](https://tools.ietf.org/html/draft-thomas-crypto-conditions-02#section-8.1.4) matching the escrow's `Condition`. |

</details>

We propose one additional field:

| Field Name             | Required? | JSON Type | Internal Type | Description                                                                                                                                       |
| :--------------------- | :-------- | :-------- | :------------ | :------------------------------------------------------------------------------------------------------------------------------------------------ |
| `ComputationAllowance` |           | `number`  | `UInt32`      | The amount of gas the user is willing to pay for the execution of the Smart Escrow. Required if the `Escrow` object has a `FinishFunction` field. |

### 7.2. Transaction Fee

There will be a higher transaction fee for executing an `EscrowFinish` transaction when there is a `FinishFunction` attached to the escrow. The exact amounts will be determined during the implementation process (and added to the spec here).

### 7.3. Failure Conditions

The existing failure conditions still apply.

These failure conditions are added:

- `ComputationAllowance` is included, but the `Escrow` doesn't have a `FinishFunction`
- The `Escrow` has a `FinishFunction`, but a `ComputationAllowance` isn't included
- The `ComputationAllowance` provided is not enough gas to complete the processing of the `FinishFunction`.
- The `FinishFunction` returns a `0` or negative number.

### 7.4. State Changes

There are no additional state changes.

### 7.5. Metadata Changes

There are two additional metadata fields:

| Field Name       | Validated? | Always Present? | Type     | Description                                                                               |
| :--------------- | :--------- | :-------------- | :------- | :---------------------------------------------------------------------------------------- |
| `GasUsed`        | Yes        | Conditional     | `UInt32` | The amount of gas actually used by the computation of the `FinishFunction` in the escrow. |
| `WasmReturnCode` | Yes        | Conditional     | `Int32`  | The integer code returned by the `FinishFunction`.                                        |

## 8. Ledger Object: `FeeSettings`

The [`FeeSettings` ledger object](https://xrpl.org/docs/references/protocol/ledger-data/ledger-entry-types/feesettings) already exists on the XRPL. The `FeeSettings` entry contains the current base transaction and reserve amounts as determined by [fee voting](https://xrpl.org/docs/concepts/consensus-protocol/fee-voting).

We propose a slight modification to support Smart Escrows. This will allow the UNL to vote on limits and prices of Smart Escrow execution, so that the network does not need a separate amendment to adjust them, and they can be adjusted on an as-needed basis (e.g. increasing caps and lowering fees as performance improvements are made).

### 8.1. Fields

<details>
<summary>

As a reference, [here](https://xrpl.org/docs/references/protocol/ledger-data/ledger-entry-types/feesettings) are the existing fields for the `FeeSettings` ledger object.

</summary>

| Field                   | Required? | JSON Type | Internal Type | Description                                                                                                                                     |
| :---------------------- | :-------- | :-------- | :------------ | :---------------------------------------------------------------------------------------------------------------------------------------------- |
| `BaseFeeDrops`          | ✔️        | `string`  | `Amount`      | The transaction cost of the "reference transaction" in drops of XRP.                                                                            |
| `Flags`                 | ✔️        | `number`  | `UInt32`      | A bitmap of boolean flags enabled for this object. Currently, the protocol defines no flags for `FeeSettings` objects. The value is always `0`. |
| `LedgerEntryType`       | ✔️        | `string`  | `UInt16`      | The value `0x0073`, mapped to the string `FeeSettings`, indicates that this object contains the ledger's fee settings.                          |
| `ReserveBaseDrops`      | ✔️        | `string`  | `Amount`      | The base reserve for an account in the XRP Ledger, as drops of XRP.                                                                             |
| `ReserveIncrementDrops` | ✔️        | `string`  | `Amount`      | The incremental owner reserve for owning objects, as drops of XRP.                                                                              |
| `PreviousTxnID`         | ✔️        | `string`  | `UInt256`     | The identifying hash of the transaction that most recently modified this entry.                                                                 |
| `PreviousTxnLgrSeq`     | ✔️        | `number`  | `UInt32`      | The index of the ledger that contains the transaction that most recently modified this entry.                                                   |

</details>

We propose three additional fields:

| Field                   | Required? | JSON Type | Internal Type | Description                                                                                                     |
| :---------------------- | :-------- | :-------- | :------------ | :-------------------------------------------------------------------------------------------------------------- |
| `ExtensionComputeLimit` | No        | `number`  | `UInt32`      | The maximum amount of gas that one extension can execute. The initial value is 100,000.                         |
| `ExtensionSizeLimit`    | No        | `number`  | `UInt32`      | The maximum size, in bytes, that an extension can be. The initial value is 100,000 (100kb).                     |
| `GasPrice`              | No        | `number`  | `UInt32`      | The cost of 1 gas, in micro-drops (1 millionth of a drop). The initial value is 1,000 (1 thousandth of a drop). |

## 9. Transaction: `SetFee`

A `SetFee` pseudo-transaction marks a change in transaction cost or reserve requirements as a result of [fee voting](https://xrpl.org/docs/concepts/consensus-protocol/fee-voting).

We propose a slight modification to support Smart Escrows. This will allow the UNL to vote on limits and prices of Smart Escrow execution, so that the network does not need a separate amendment to adjust them, and they can be adjusted on an as-needed basis (e.g. increasing caps and lowering fees as performance improvements are made).

### 9.1. Fields

<details>
<summary>

As a reference, [here](https://xrpl.org/docs/references/protocol/transactions/pseudo-transaction-types/setfee) are the existing fields for the `SetFee` transaction.

</summary>

| Field                   | Required? | JSON Type | Internal Type | Description                                                                                                                                                 |
| :---------------------- | :-------- | :-------- | :------------ | :---------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `BaseFeeDrops`          | ✔️        | `string`  | `Amount`      | The charge, in drops of XRP, for the reference transaction. (This is the transaction cost before scaling for load.)                                         |
| `ReserveBaseDrops`      | ✔️        | `string`  | `Amount`      | The base reserve, in drops.                                                                                                                                 |
| `ReserveIncrementDrops` | ✔️        | `string`  | `Amount`      | The incremental reserve, in drops.                                                                                                                          |
| `LedgerSequence`        | ✔️        | `number`  | `UInt32`      | The index of the ledger version where this pseudo-transaction appears. This distinguishes the pseudo-transaction from other occurrences of the same change. |

</details>

We propose three additional fields:

| Field                   | Required? | JSON Type | Internal Type | Description                                                                                                    |
| :---------------------- | :-------- | :-------- | :------------ | :------------------------------------------------------------------------------------------------------------- |
| `ExtensionComputeLimit` | No        | `number`  | `UInt32`      | The maximum amount of gas that one extension can execute. The initial value is 100,000.                        |
| `ExtensionSizeLimit`    | No        | `number`  | `UInt32`      | The maximum size, in bytes, that an extension can be. The initial value is 100000 (100kb).                     |
| `GasPrice`              | No        | `number`  | `UInt32`      | The cost of 1 gas, in micro-drops (1 millionth of a drop). The initial value is 1000 (1 thousandth of a drop). |

## 10. How the `FinishFunction` Field Works

The `FinishFunction` field will contain compiled WebAssembly (WASM) code that is uploaded to the XRPL. The details of how the WASM engine will execute the code will be provided in a separate XLS.

Some guidelines on what you can/cannot do in the WASM code:

- Gas limits on what you can execute (as specified in the `ExtensionComputeLimit` field in `FeeSettings`)
- Minimal data storage (each escrow has one 4kb `Data` field)
- Simple ABI - a function that takes the transaction and returns a true/false (whether the escrow can be finished/canceled)
- Read-access of ledger objects allowed
- No write access of other ledger objects (only to the `Data` field of the `Escrow`)
- No transaction emission / creation

## 11. Invariants

Any escrow with a `FinishFunction` field must have a `CancelAfter` field. This provides better security in case something goes wrong with the `FinishFunction`, either due to user error or due to a bug. This restriction may be relaxed in the future.

## 12. Security

The implementation will undergo rigorous testing and security audits to ensure that smart escrow developers cannot edit any other ledger object, and continue to obey all other rules of the XRPL.

## 13. Rationale

Smart Escrows are designed to address the limitations of XRPL’s current escrow mechanisms, which only support time-based and hashlock (crypto-condition) releases. The idea is to enable more expressive, programmable conditions for escrow release, unlocking use cases such as notary approvals, compliance holds, and oracle-driven transactions directly on XRPL.

### 13.1. Design Choices

- **WebAssembly (WASM) as the Execution Environment:** WASM was chosen for its portability, security, and deterministic execution. It is widely used in blockchain environments (e.g., Polkadot, Ethereum’s eWASM, Solana) and allows for safe, resource-limited execution of user code. Alternatives like Lua, JavaScript, or custom DSLs were considered but rejected due to WASM’s maturity and tooling. The full analysis is available [here](https://dev.to/ripplexdev/a-survey-of-vms-for-xrpl-programmability-eoa).
- **Minimal ABI and Data Access:** The ABI is intentionally simple, requiring only a `finish()` function with limited access to ledger data and a small, escrow-local `Data` field. This reduces attack surface and complexity, while still enabling meaningful programmability.
- **Mandatory `CancelAfter` for Smart Escrows:** To mitigate risks of stuck funds due to buggy or malicious WASM code, every Smart Escrow must be cancellable. This was debated, but consensus was that safety outweighs flexibility for initial deployment.
- **Fee and Resource Controls:** Gas limits, size caps, and fee voting via `FeeSettings` and `SetFee` allow the network to dynamically adjust resource usage and pricing, preventing abuse and adapting to future improvements.

### 13.2. Alternatives Considered

- **Expanding CryptoConditions:** Supporting the full CryptoConditions spec (multi-sig, threshold, etc.) was considered, but would not provide general programmability or support for external data/oracles.
- **On-Ledger Scripting Languages:** Custom scripting languages were rejected due to maintenance burden and lack of ecosystem support.
- **External Oracles or Sidechains:** Relying on external systems for conditional logic was deemed less secure and less integrated than on-ledger WASM execution.

### 13.3. Related Work

Other blockchains support similar programmable escrow mechanisms:

- **Ethereum:** Escrow logic is implemented via smart contracts, but with higher complexity and cost.
- **Polkadot:** Uses WASM for on-chain logic, including custom escrow pallets.
- **Solana:** Allows custom escrow programs in Rust, compiled to BPF.

XRPL’s approach is intentionally minimal and tightly scoped to maintain performance and security.

### 13.4. Objections and Concerns

- **Security Risks of On-Ledger Code Execution:** Concerns were raised about the risk of denial-of-service or infinite loops. These are mitigated by strict gas limits, code size caps, and mandatory cancellation.
- **Complexity vs. Simplicity:** Some community members preferred expanding existing CryptoConditions rather than introducing WASM. The design team determined that WASM provides greater flexibility and future extensibility.
- **Ledger Bloat:** The addition of code and data fields could increase ledger size. This is managed via reserve requirements and size limits.

Overall, Smart Escrows balance programmability, safety, and simplicity, providing a foundation for future XRPL extensions.

## 14. Code Examples

### 14.1. Notary Release

Only one notary account may release the escrow.

```rust
pub extern "C" fn finish() -> i32 {
    let escrow_finish = escrow_finish::get_current_escrow_finish();
    let tx_account = match escrow_finish.get_account() {
        Ok(v) => v,
        Err(e) => {
            return e.code(); // Must return to short circuit.
        }
    };

    (tx_account.0 == NOTARY_ACCOUNT) as i32
}
```

### 14.2. Temporary Hold

The escrow can only be released if the destination holds a specific [credential](https://xrpl.org/docs/concepts/decentralized-storage/credentials).

```rust
pub extern "C" fn finish() -> i32 {
    let current_escrow = current_escrow::get_current_escrow();

    let account_id = match current_escrow.get_destination() {
        Ok(account_id) => account_id,
        Err(e) => {
            return e.code(); // <-- Do not execute the escrow.
        }
    };

    let cred_type: &[u8] = b"termsandconditions";
    match credential_keylet(&account_id, &account_id, cred_type) {
        Ok(keylet) => {
            let slot =
                unsafe { xrpl_std::host::cache_ledger_obj(keylet.as_ptr(), keylet.len(), 0) };
            if slot < 0 {
                return 0; // credential doesn't exist, do not execute
            };
            1 // credential exists, execute the escrow
        }
        Err(e) => {
            let _ = trace_num("Error getting credential keylet", e.code() as i64);
            e.code() // <-- Do not execute the escrow.
        }
    }
}
```

### 14.3. Pseudo-Options

The escrow can only be released if the price of an [oracle](https://xrpl.org/docs/references/protocol/ledger-data/ledger-entry-types/oracle) says that a token is at least $1.

```rust
pub fn get_price_from_oracle(slot: i32) -> Result<u64> {
    let mut locator = Locator::new();
    locator.pack(sfield::PriceDataSeries);
    locator.pack(0);
    locator.pack(sfield::AssetPrice);

    let mut data: [u8; 8] = [0; 8];
    let result_code = unsafe {
        host::get_ledger_obj_nested_field(
            slot,
            locator.get_addr(),
            locator.num_packed_bytes(),
            data.as_mut_ptr(),
            data.len(),
        )
    };
    let asset_price = match match_result_code(result_code, || data) {
        Ok(asset_bytes) => get_u64_from_buffer(&asset_bytes[0..8]),
        Err(error) => {
            return Err(error); // Must return to short circuit.
        }
    };
    Ok(asset_price)
}

#[unsafe(no_mangle)]
pub extern "C" fn finish() -> i32 {
    let oracle_keylet = oracle_keylet_safe(&ORACLE_OWNER, ORACLE_DOCUMENT_ID);

    let slot: i32;
    unsafe {
        slot = xrpl_std::host::cache_ledger_obj(oracle_keylet.as_ptr(), oracle_keylet.len(), 0);
        if slot < 0 {
            return 0;
        };
    }

    let price = match get_price_from_oracle(slot) {
        Ok(v) => v,
        Err(e) => return e.code(),
    };

    (price > 1) as i32
}
```

# Appendix

## Appendix A: FAQ

### A.1: Isn't this kind of useless if I can only store XRP in an escrow?

Support for Issued Currencies and MPTs is currently (as of August 2025) up for voting as a part of the [TokenEscrow amendment](https://xrpl.org/resources/known-amendments#tokenescrow).

### A.2: Can an existing escrow be updated to have a `FinishFunction`?

No. An Escrow’s release condition(s) cannot be updated after it is created. The escrow's "contract" (in the legal sense, not in the smart contract sense) must remain the same after creation.

### A.3: Can the `FinishFunction` field be updated after the escrow has been created?

No. An Escrow’s release condition(s) cannot be updated after it is created.

### A.4: Can the `Data` field be updated with a transaction?

No, at this time the `Data` field can only be updated by the `FinishFunction` code.

### A.5: Do all nodes and validators need to run the `FinishFunction` code?

Yes. They need to in order to ensure that the error code returned (and validated) in the transaction is correct.

### A.6: How does this design prevent abuse/infinite loops from eating up rippled resources, while allowing for sufficient compute for Smart Escrow developers?

The UNL can adjust the parameters based on the needs and limitations of the network, to ensure that developers have enough computing resources for their needs, while also preventing them from overrunning the network with their extensions.

### A.7: Why not use an `STData` type for the `Data` field?

The `Data` field is an optional 4KB raw on ledger storage area attached to a (smart) escrow ledger object. It is currently treated as an opaque blob, with read and write operations applied to the entire 4KB block. This makes it somewhat difficult to work with. Theoretically, we could enhance the host functions to support partial reads and writes, or add utilities to assist with serialization.

We decided to keep the current design for the smart escrow feature for now and revisit it later, once we have a better sense of how people will use the field.

### A.8: Can there be an additional `init` function that is run on `EscrowCreate`?

The calling `init()` by `EscrowCreate` has at least the following two benefits:

1. It can help initializing the `Data` field of the `Escrow` ledger object, though a separate `EscrowFinish` transaction after the `EscrowCreate` can initialize the `Data` field too, or the user can upload their desired `Data` field in the `EscrowCreate`.
2. The `Escrow` creation can be conditional depending on the `init()` result.

We think those benefits are meaningful, but not sure how much. We can always add this feature as an amendment later on, depending on Smart Escrow usage and need.
