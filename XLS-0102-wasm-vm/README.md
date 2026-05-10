<pre>
  title: WASM VM
  description: WebAssembly VM integration into rippled
  author: Mayukha Vadari (@mvadari), Peng Wang (@pwang200), Oleksandr Pidskopnyi (@oleks_rip), David Fuelling (@sappenin)
  proposal-from: https://github.com/XRPLF/XRPL-Standards/discussions/303
  status: Draft
  category: Amendment
  created: 2025-08-08
  updated: 2026-02-03
</pre>

# WASM VM Configuration

## Abstract

This document describes the integration of WebAssembly (WASM) into the XRP Ledger as a secure and deterministic execution environment for smart contract logic. WASM-based execution allows developers to write custom logic in a wide range of languages, compile to a portable binary format, and run within a sandboxed virtual machine governed by the consensus process. The standard outlines the interface, constraints, and security model for deploying, invoking, and validating WASM subroutines on-ledger, while ensuring compatibility with existing ledger primitives and transaction flow.

## 1. Overview

This document addresses several parts of the WASM integration into rippled:

- The implementation chosen
- The gas model
- The set of host functions
- Security measures

This feature does not (directly) involve any new transactions, ledger objects, or RPCs. It will be gated by the `SmartEscrow` amendment. Any modification to the details in this spec will require an amendment, as it will affect transaction processing (e.g. success/failure of an `EscrowFinish` transaction for a Smart Escrow).

### 1.1. How the WASM Engine Integrates into `rippled`

<img width="1020" height="495" alt="image" src="https://github.com/user-attachments/assets/8d8e90f4-cda6-4747-9438-e648bc89378b" />

Using [Smart Escrows](../XLS-0100-smart-escrows/README.md) as an example:

1. Process the transaction until it has done everything it needs to do before processing anything that requires the WASM engine (in this case, running the `FinishFunction` code to determine if the escrow is finishable).
2. Enter the WASM engine, where the WASM environment is set up to run the code.
3. Run the WASM code, using host functions to fetch on-ledger information.
4. Return the output (whether or not the escrow can be finished) to the transaction processing engine, and continue onwards with the rest of the transaction code.

### 1.2. Background: What is a “Host Function”?

A host function is a function expressed outside WebAssembly but passed to a module as an import. They’re somewhat analogous to precompiles in the EVM world.

In other words, it’s basically an API call that fetches/interacts with data or native compute outside of the WASM VM.

### 1.3. Background: WASM Native Types

There are only 4 native types in the [WASM spec](https://webassembly.github.io/spec/core/syntax/types.html): `i32` (a signed 32-bit integer), `i64` (a signed 64-bit integer), `f32` (a 32-bit floating point number), and `f64` (a 64-bit floating point number). However, the floating point numbers use a different encoding from what `rippled` uses.

So essentially, we only have `i32` and `i64` in terms of useful types. **Every parameter and return type must be represented as these two types.** This is manifested as [pointers](https://en.wikipedia.org/wiki/Pointer_%28computer_programming%29) and lengths. _Note that any language that has full support for XRPL extensions will have helper functions to abstract away most of the complexity (especially involving pointers and lengths)._

## 2. VM Runtime Choice

While WebAssembly has a [core specification](https://webassembly.github.io/spec/), different runtimes have flexibility in how they implement certain features that are not a part of the formal specification. For example, not all WASM runtimes can easily be embedded in a C++ project (such as `rippled`).

The most relevant part for the purpose of consensus is the gas cost for any operation or function. Different implementations may have different gas costs for executing a given function, due to implementation differences - e.g. some calculate gas costs by inserting additional instructions, while others have a counter in the VM logic. For instance, one basic Smart Escrow function cost 110 gas to run with [WasmEdge](https://wasmedge.org/), while it only cost 5 gas with [Wasmi](https://github.com/wasmi-labs/wasmi). This would cause consensus issues if the computation limit was set at 100, for example - one runtime would succeed, while the other would fail.

There are other metrics that are important as well, such as performance considerations. See Appendix A for the full analysis comparing different runtimes.

### 2.1. Gas

Gas consumption is determined by the WASM runtime used for execution. Different implementations may use different metering strategies, which yields different gas costs for identical WASM code. [This blog post](https://agryaznov.com/posts/wasm-gas-metering/) discusses several of the different strategies.

Gas will accumulate from:

- Execution of individual WASM instructions
- Memory operations (e.g. `grow_memory`)
- Calling host functions (e.g. accessing ledger data)

Exceeding the provided gas budget triggers immediate execution halting, with a deterministic failure consistent across implementations.

## 3. Execution Limits

The XRPL cannot allow unbounded execution, as there is a time limit for ledgers to close in order for consensus to execute in a timely manner. There are three methods of ensuring that the WASM code does not take too many resources:

- A size limit to the WASM code
- A computation limit
- A price for each unit of gas

All of these parameters will be UNL-votable, so that they do not need a separate amendment to be modified.

## 4. Memory Management Strategies

WebAssembly 1.0 (which is the WASM profile that the XRPL will support) does not include built-in memory management - there is no garbage collector or automatic heap allocation. Instead, memory is a contiguous linear buffer that can only grow (in fixed 64 KiB pages) and never shrink. That means WASM code must allocate and manage its own memory, typically via a custom allocator or language runtime, and explicitly track when memory is no longer needed. While there is [progress](https://developer.chrome.com/blog/wasmgc) on this front with WasmGC, it does not have full-fledged tooling support yet, and is currently only really useful for browser applications of WASM.

This is a bit of a problem for host functions, since data has to go back and forth between the caller (WASM dev) and the engine (`rippled`). Some data (e.g. parameters) may be generated on the WASM side, while some data (e.g. the return data) may be generated on the rippled side.

Therefore, in this design, the caller is responsible for allocating memory in advance, and must reuse or deallocate memory manually. See Appendix B for alternative designs that were considered and rejected.

## 5. Extension Host Functions

This section introduces WASM host functions for extensions on the XRP Ledger, enabling WASM bytecode (in an extension or smart contract) to securely interact with ledger data and the ledger’s native features. These functions provide controlled access to ledger state, transaction execution, and XRPL primitives while maintaining efficiency and security.

WASM code, whether in an extension or a smart contract, needs access to XRPL ledger data in order to be useful. A host function allows that access, in a secure way. Host functions can also be used to save gas/compute in WASM, as they can perform those same functions in C++ code instead, which will likely be more performant.

Some examples from [XLS-100](../XLS-0100-smart-escrows/README.md):

- A notary escrow extension needs access to the triggering `EscrowFinish` transaction (to know who is sending the transaction).
- An escrow checking for KYC needs access to ledger state, to determine if the destination has a given credential.

This spec only covers Smart Escrow host functions at this time.

These host functions will be accessible from extensions and smart contracts.

Note: all these functions return an `i32`, unless otherwise noted (or there is no buffer parameter). If the value is positive, it's a length. If it's negative, it's an error code.

### 5.1. General Ledger Data

This section includes ledger header data, amendments, and fees.

| Function Signature                                                                              | Description                                       | Gas Cost |
| :---------------------------------------------------------------------------------------------- | :------------------------------------------------ | :------- |
| `get_ledger_sqn(`<br/>&emsp;`out_buff_ptr: i32,`<br/>&emsp;`out_buff_len: i32`<br />`)`         | Get the sequence number of the last ledger.       | 60       |
| `get_parent_ledger_time(`<br/>&emsp;`out_buff_ptr: i32,`<br/>&emsp;`out_buff_len: i32`<br />`)` | Get the time (in Ripple Time) of the last ledger. | 60       |
| `get_parent_ledger_hash(`<br/>&emsp;`out_buff_ptr: i32,`<br/>&emsp;`out_buff_len: i32`<br />`)` | Get the hash of the last ledger.                  | 60       |
| `amendment_enabled(`<br/>&emsp;`amendment_ptr: i32,`<br/>&emsp;`amendment_len: i32`<br />`)`    | Check if a given amendment is enabled.            | 60       |
| `get_base_fee(`<br/>&emsp;`out_buff_ptr: i32,`<br/>&emsp;`out_buff_len: i32`<br />`)`           | Get the current transaction base fee.             | 60       |

### 5.2. Current Ledger Object data

The current ledger object is the ledger object that the extension lives on - for Smart Escrows that's an `Escrow` object.

| Function Signature                                                                                                                                                       | Description                                                                           | Gas Cost |
| :----------------------------------------------------------------------------------------------------------------------------------------------------------------------- | :------------------------------------------------------------------------------------ | :------- |
| `get_current_ledger_obj_field(`<br/>&emsp;`field: i32,`<br/>&emsp;`out_buff_ptr: i32,`<br/>&emsp;`out_buff_len: i32`<br />`)`                                            | Get a top-level field from the ledger object that the extension is on.                | 70       |
| `get_current_ledger_obj_nested_field(`<br/>&emsp;`locator_ptr: i32,`<br/>&emsp;`locator_len: i32,`<br/>&emsp;`out_buff_ptr: i32,`<br/>&emsp;`out_buff_len: i32`<br />`)` | Get a nested field from the ledger object that the extension is on.                   | 110      |
| `get_current_ledger_obj_array_len(`<br/>&emsp;`field: i32`<br />`)`                                                                                                      | Get the length of an array field on the ledger object that the extension is on.       | 40       |
| `get_current_ledger_obj_nested_array_len(`<br/>&emsp;`locator_ptr: i32,`<br/>&emsp;`locator_len: i32`<br />`)`                                                           | Get the length of a nested array field on the ledger object that the extension is on. | 70       |

#### 5.2.1. Locators

A Locator allows a WASM developer to reference any field in any object (even nested fields) by specifying a `slot_num` (1 byte); a `locator_field_type` (1 byte); then one of an `sfield` (4 bytes) or an `index` (4 bytes).

### 5.3. Current Transaction Data

The current transaction is the `EscrowFinish` that is executing the WASM logic

| Function Signature                                                                                                                                       | Description                                                                           | Gas Cost |
| :------------------------------------------------------------------------------------------------------------------------------------------------------- | :------------------------------------------------------------------------------------ | :------- |
| `get_tx_field(`<br/>&emsp;`field: i32,`<br/>&emsp;`out_buff_ptr: i32,`<br/>&emsp;`out_buff_len: i32`<br />`)`                                            | Get a top-level field from the transaction that triggered the extension.              | 70       |
| `get_tx_nested_field(`<br/>&emsp;`locator_ptr: i32,`<br/>&emsp;`locator_len: i32,`<br/>&emsp;`out_buff_ptr: i32,`<br/>&emsp;`out_buff_len: i32`<br />`)` | Get a nested field from the transaction that triggered the extension.                 | 110      |
| `get_tx_array_len(`<br/>&emsp;`field: i32`<br />`)`                                                                                                      | Get the length of an array field from the transaction that triggered the extension.   | 40       |
| `get_tx_nested_array_len(`<br/>&emsp;`locator_ptr: i32,`<br/>&emsp;`locator_len: i32`<br />`)`                                                           | Get the length of a nested array field on the ledger object that the extension is on. | 70       |

### 5.4. Any Ledger Object Data

Fetch data from any other ledger object

| Function Signature                                                                                                                                                                           | Description                                                    | Gas Cost |
| :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | :------------------------------------------------------------- | :------- |
| `cache_ledger_obj(`<br/>&emsp;`keylet_ptr: i32,`<br/>&emsp;`keylet_len: i32,`<br/>&emsp;`cache_num: i32`<br />`)`                                                                            | Cache a ledger object so that it can be used later.            | 5000     |
| `get_ledger_obj_field(`<br/>&emsp;`cache_num: i32,`<br/>&emsp;`field: i32,`<br/>&emsp;`out_buff_ptr: i32,`<br/>&emsp;`out_buff_len: i32`<br />`)`                                            | Get a top-level field from any ledger object.                  | 70       |
| `get_ledger_obj_nested_field(`<br/>&emsp;`cache_num: i32,`<br/>&emsp;`locator_ptr: i32,`<br/>&emsp;`locator_len: i32,`<br/>&emsp;`out_buff_ptr: i32,`<br/>&emsp;`out_buff_len: i32`<br />`)` | Get a nested field from any ledger object.                     | 110      |
| `get_ledger_obj_array_len(`<br/>&emsp;`cache_num: i32,`<br/>&emsp;`field: i32`<br />`)`                                                                                                      | Get the length of an array field from any ledger object.       | 40       |
| `get_ledger_obj_nested_array_len(`<br/>&emsp;`cache_num: i32,`<br/>&emsp;`locator_ptr: i32,`<br/>&emsp;`locator_len: i32`<br />`)`                                                           | Get the length of a nested array field from any ledger object. | 70       |

### 5.5. Keylets

A keylet is a unique hash that represents a ledger object on the XRP Ledger. It is a 256-bit hash, constructed from unique identifiers for an object. For example, an `AccountRoot`'s hash is constructed from its `AccountID`, and an `Oracle`'s hash is constructed from its `Owner` and `DocumentID`.

| Function Signature                                                                                                                                                                                                                                                                    | Description                                                | Gas Cost |
| :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | :--------------------------------------------------------- | :------- |
| `account_keylet(`<br/>&emsp;`account_ptr: i32,`<br/>&emsp;`account_len: i32,`<br/>&emsp;`out_buff_ptr: i32,`<br/>&emsp;`out_buff_len: i32`<br />`)`                                                                                                                                   | Calculate an `AccountRoot`'s keylet from its pieces.       | 350      |
| `amm_keylet(`<br/>&emsp;`issue1_ptr: i32,`<br/>&emsp;`issue1_len: i32,`<br/>&emsp;`issue2_ptr: i32,`<br/>&emsp;`issue2_len: i32,`<br/>&emsp;`out_buff_ptr: i32,`<br/>&emsp;`out_buff_len: i32`<br />`)`                                                                               | Calculate an `AMM`’s keylet from its pieces.               | 350      |
| `check_keylet(`<br/>&emsp;`account_ptr: i32,`<br/>&emsp;`account_len: i32,`<br/>&emsp;`sequence_ptr: i32,`<br/>&emsp;`sequence_len: i32,`<br/>&emsp;`out_buff_ptr: i32,`<br/>&emsp;`out_buff_len: i32`<br />`)`                                                                       | Calculate a `Check`'s keylet from its pieces.              | 350      |
| `credential_keylet(`<br/>&emsp;`subject_ptr: i32,`<br/>&emsp;`subject_len: i32,`<br/>&emsp;`issuer_ptr: i32,`<br/>&emsp;`issuer_len: i32,`<br/>&emsp;`cred_type_ptr: i32,`<br/>&emsp;`cred_type_len: i32,`<br/>&emsp;`out_buff_ptr: i32,`<br/>&emsp;`out_buff_len: i32`<br />`)`      | Calculate a `Credential`'s keylet from its pieces.         | 350      |
| `delegate_keylet(`<br/>&emsp;`account_ptr: i32,`<br/>&emsp;`account_len: i32,`<br/>&emsp;`authorize_ptr: i32,`<br/>&emsp;`authorize_len: i32,`<br/>&emsp;`out_buff_ptr: i32,`<br/>&emsp;`out_buff_len: i32`<br />`)`                                                                  | Calculate a `Delegate`'s keylet from its pieces.           | 350      |
| `deposit_preauth_keylet(`<br/>&emsp;`account_ptr: i32,`<br/>&emsp;`account_len: i32,`<br/>&emsp;`authorize_ptr: i32,`<br/>&emsp;`authorize_len: i32,`<br/>&emsp;`out_buff_ptr: i32,`<br/>&emsp;`out_buff_len: i32`<br />`)`                                                           | Calculate a `DepositPreauth`'s keylet from its pieces.     | 350      |
| `did_keylet(`<br/>&emsp;`account_ptr: i32,`<br/>&emsp;`account_len: i32,`<br/>&emsp;`out_buff_ptr: i32,`<br/>&emsp;`out_buff_len: i32`<br />`)`                                                                                                                                       | Calculate a `DID`'s keylet from its pieces.                | 350      |
| `escrow_keylet(`<br/>&emsp;`account_ptr: i32,`<br/>&emsp;`account_len: i32,`<br/>&emsp;`sequence_ptr: i32,`<br/>&emsp;`sequence_len: i32,`<br/>&emsp;`out_buff_ptr: i32,`<br/>&emsp;`out_buff_len: i32`<br />`)`                                                                      | Calculate an `Escrow`'s keylet from its pieces.            | 350      |
| `line_keylet(`<br/>&emsp;`account1_ptr: i32,`<br/>&emsp;`account1_len: i32,`<br/>&emsp;`account2_ptr: i32,`<br/>&emsp;`account2_len: i32,`<br/>&emsp;`currency_ptr: i32,`<br/>&emsp;`currency_len: i32,`<br/>&emsp;`out_buff_ptr: i32,`<br/>&emsp;`out_buff_len: i32`<br />`)`        | Calculate a trustline’s keylet from its pieces.            | 350      |
| `mpt_issuance_keylet(`<br/>&emsp;`issuer_ptr: i32,`<br/>&emsp;`issuer_len: i32,`<br/>&emsp;`sequence_ptr: i32,`<br/>&emsp;`sequence_len: i32,`<br/>&emsp;`out_buff_ptr: i32,`<br/>&emsp;`out_buff_len: i32`<br />`)`                                                                  | Calculate an `MPTIssuance`’s keylet from its pieces.       | 350      |
| `mptoken_keylet(`<br/>&emsp;`mptid_ptr: i32,`<br/>&emsp;`mptid_len: i32,`<br/>&emsp;`holder_ptr: i32,`<br/>&emsp;`holder_len: i32,`<br/>&emsp;`out_buff_ptr: i32,`<br/>&emsp;`out_buff_len: i32`<br />`)`                                                                             | Calculate an `MPToken`’s keylet from its pieces.           | 350      |
| `nft_offer_keylet(`<br/>&emsp;`account_ptr: i32,`<br/>&emsp;`account_len: i32,`<br/>&emsp;`sequence_ptr: i32,`<br/>&emsp;`sequence_len: i32,`<br/>&emsp;`out_buff_ptr: i32,`<br/>&emsp;`out_buff_len: i32`<br />`)`                                                                   | Calculate an `NFTOffer`'s keylet from its pieces.          | 350      |
| `offer_keylet(`<br/>&emsp;`account_ptr: i32,`<br/>&emsp;`account_len: i32,`<br/>&emsp;`sequence_ptr: i32,`<br/>&emsp;`sequence_len: i32,`<br/>&emsp;`out_buff_ptr: i32,`<br/>&emsp;`out_buff_len: i32`<br />`)`                                                                       | Calculate an `Offer`'s keylet from its pieces.             | 350      |
| `oracle_keylet(`<br/>&emsp;`account_ptr: i32,`<br/>&emsp;`account_len: i32,`<br/>&emsp;`document_id_ptr: i32,`<br/>&emsp;`document_id_len: i32,`<br/>&emsp;`out_buff_ptr: i32,`<br/>&emsp;`out_buff_len: i32`<br />`)`                                                                | Calculate an `Oracle`'s keylet from its pieces.            | 350      |
| `paychan_keylet(`<br/>&emsp;`account_ptr: i32,`<br/>&emsp;`account_len: i32,`<br/>&emsp;`destination_ptr: i32,`<br/>&emsp;`destination_len: i32,`<br/>&emsp;`sequence_ptr: i32,`<br/>&emsp;`sequence_len: i32,`<br/>&emsp;`out_buff_ptr: i32,`<br/>&emsp;`out_buff_len: i32`<br />`)` | Calculate a `PayChannel`’s keylet from its pieces.         | 350      |
| `permissioned_domain_keylet(`<br/>&emsp;`account_ptr: i32,`<br/>&emsp;`account_len: i32,`<br/>&emsp;`sequence_ptr: i32,`<br/>&emsp;`sequence_len: i32,`<br/>&emsp;`out_buff_ptr: i32,`<br/>&emsp;`out_buff_len: i32`<br />`)`                                                         | Calculate a `PermissionedDomain`’s keylet from its pieces. | 350      |
| `signers_keylet(`<br/>&emsp;`account_ptr: i32,`<br/>&emsp;`account_len: i32,`<br/>&emsp;`out_buff_ptr: i32,`<br/>&emsp;`out_buff_len: i32`<br />`)`                                                                                                                                   | Calculate a `SignerListSet`'s keylet from its pieces.      | 350      |
| `ticket_keylet(`<br/>&emsp;`account_ptr: i32,`<br/>&emsp;`account_len: i32,`<br/>&emsp;`sequence_ptr: i32,`<br/>&emsp;`sequence_len: i32,`<br/>&emsp;`out_buff_ptr: i32,`<br/>&emsp;`out_buff_len: i32`<br />`)`                                                                      | Calculate a `Ticket`'s keylet from its pieces.             | 350      |
| `vault_keylet(`<br/>&emsp;`account_ptr: i32,`<br/>&emsp;`account_len: i32,`<br/>&emsp;`sequence_ptr: i32,`<br/>&emsp;`sequence_len: i32,`<br/>&emsp;`out_buff_ptr: i32,`<br/>&emsp;`out_buff_len: i32`<br />`)`                                                                       | Calculate a `Vault`’s keylet from its pieces.              | 350      |

The singleton keylets (e.g. `Amendments`) are a bit unnecessary to include, as a dev can simply copy the keylet directly instead. They will be included as constants in `xrpl-wasm-stdlib` as well.

The directory keylets and `NFTokenPage` were not included, since they are a bit more complex to parse through and it seemed unnecessary for now. These can always be added in the future.

### 5.6. NFTs

Fetch information about NFTs.

| Function Signature                                                                                                                                                                                 | Description                                   | Gas Cost |
| :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | :-------------------------------------------- | :------- |
| `get_nft(`<br/>&emsp;`owner_ptr: i32,`<br/>&emsp;`owner_len: i32,`<br/>&emsp;`nft_id_ptr: i32,`<br/>&emsp;`nft_id_len: i32,`<br/>&emsp;`out_buff_ptr: i32,`<br/>&emsp;`out_buff_len: i32`<br />`)` | Get an NFT URI from its owner and ID.         | 1000     |
| `get_nft_issuer(`<br/>&emsp;`nft_id_ptr: i32,`<br/>&emsp;`nft_id_len: i32,`<br/>&emsp;`out_buff_ptr: i32,`<br/>&emsp;`out_buff_len: i32`<br />`)`                                                  | Extract the NFT issuer from the NFT ID.       | 350      |
| `get_nft_taxon(`<br/>&emsp;`nft_id_ptr: i32,`<br/>&emsp;`nft_id_len: i32,`<br/>&emsp;`out_buff_ptr: i32,`<br/>&emsp;`out_buff_len: i32`<br />`)`                                                   | Extract the NFT taxon from the NFT ID.        | 350      |
| `get_nft_flags(`<br/>&emsp;`nft_id_ptr: i32,`<br/>&emsp;`nft_id_len: i32`<br />`)`                                                                                                                 | Extract the NFT flags from the NFT ID.        | 350      |
| `get_nft_transfer_fee(`<br/>&emsp;`nft_id_ptr: i32,`<br/>&emsp;`nft_id_len: i32`<br />`)`                                                                                                          | Extract the NFT transfer fee from the NFT ID. | 350      |
| `get_nft_serial(`<br/>&emsp;`nft_id_ptr: i32,`<br/>&emsp;`nft_id_len: i32,`<br/>&emsp;`out_buff_ptr: i32,`<br/>&emsp;`out_buff_len: i32`<br />`)`                                                  | Extract the NFT serial from the NFT ID.       | 350      |

### 5.7. Utils

Miscellaneous utility functions.

| Function Signature                                                                                                                                                                                          | Description                                                                                                              | Gas Cost |
| :---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | :----------------------------------------------------------------------------------------------------------------------- | :------- |
| `check_sig(`<br/>&emsp;`message_ptr: i32,`<br/>&emsp;`message_len: i32,`<br/>&emsp;`signature_ptr: i32,`<br/>&emsp;`signature_len: i32,`<br/>&emsp;`pubkey_ptr: i32,`<br/>&emsp;`pubkey_len: i32,`<br />`)` | Check the validity of a signature. Returns a `0` for invalid and `1` for valid. Supports both `ED25519` and `SECP256K1.` | 2000     |
| `compute_sha512_half(`<br/>&emsp;`data_ptr: i32,`<br/>&emsp;`data_len: i32,`<br/>&emsp;`out_buff_ptr: i32,`<br/>&emsp;`out_buff_len: i32`<br />`)`                                                          | Calculate the `sha512` half hash of provided data.                                                                       | 2000     |

### 5.8. Floats

Helper functions for working with rippled-encoded floats (e.g. IOU amounts).

| Function Signature                                                                                                                                                                                                     | Description                                                       | Gas Cost |
| :--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | :---------------------------------------------------------------- | :------- |
| `float_from_int(`<br/>&emsp;`in_int: i64,`<br/>&emsp;`out_buf: i32,`<br/>&emsp;`out_len: i32,`<br/>&emsp;`rounding_modes: i32`<br />`)`                                                                                | Create a float in rippled format from a 64-bit integer.           | 1000     |
| `float_from_uint(`<br/>&emsp;`in_uint_ptr: i32,`<br/>&emsp;`in_uint_len: i32,`<br/>&emsp;`out_buf: i32,`<br/>&emsp;`out_len: i32,`<br/>&emsp;`rounding_modes: i32`<br />`)`                                            | Create a float in rippled format from a 64-bit unsigned integer.  | 1000     |
| `float_set(`<br/>&emsp;`exponent: i32,`<br/>&emsp;`mantissa: i64,`<br/>&emsp;`out_buf: i32,`<br/>&emsp;`out_len: i32,`<br/>&emsp;`rounding_modes: i32`<br />`)`                                                        | Create a float in rippled format from an exponent and a mantissa. | 1000     |
| `float_compare(`<br/>&emsp;`in_buf1: i32,`<br/>&emsp;`in_len1: i32,`<br/>&emsp;`in_buf2: i32,`<br/>&emsp;`in_len2: i32`<br />`)`                                                                                       | Compare two floats in rippled format.                             | 1000     |
| `float_add(`<br/>&emsp;`in_buf1: i32,`<br/>&emsp;`in_len1: i32,`<br/>&emsp;`in_buf2: i32,`<br/>&emsp;`in_len2: i32,`<br/>&emsp;`out_buf: i32,`<br/>&emsp;`out_len: i32,`<br/>&emsp;`rounding_modes: i32`<br />`)`      | Add two floats in rippled format.                                 | 1000     |
| `float_subtract(`<br/>&emsp;`in_buf1: i32,`<br/>&emsp;`in_len1: i32,`<br/>&emsp;`in_buf2: i32,`<br/>&emsp;`in_len2: i32,`<br/>&emsp;`out_buf: i32,`<br/>&emsp;`out_len: i32,`<br/>&emsp;`rounding_modes: i32`<br />`)` | Subtract two floats in rippled format.                            | 1000     |
| `float_multiply(`<br/>&emsp;`in_buf1: i32,`<br/>&emsp;`in_len1: i32,`<br/>&emsp;`in_buf2: i32,`<br/>&emsp;`in_len2: i32,`<br/>&emsp;`out_buf: i32,`<br/>&emsp;`out_len: i32,`<br/>&emsp;`rounding_modes: i32`<br />`)` | Multiply two floats in rippled format.                            | 1000     |
| `float_divide(`<br/>&emsp;`in_buf1: i32,`<br/>&emsp;`in_len1: i32,`<br/>&emsp;`in_buf2: i32,`<br/>&emsp;`in_len2: i32,`<br/>&emsp;`out_buf: i32,`<br/>&emsp;`out_len: i32,`<br/>&emsp;`rounding_modes: i32`<br />`)`   | Divide two floats in rippled format.                              | 1000     |
| `float_pow(`<br/>&emsp;`in_buf: i32,`<br/>&emsp;`in_len: i32,`<br/>&emsp;`pow: i32,`<br/>&emsp;`out_buf: i32,`<br/>&emsp;`out_len: i32,`<br/>&emsp;`rounding_modes: i32`<br />`)`                                      | Compute the nth power of a float in rippled format.               | 1000     |
| `float_root(`<br/>&emsp;`in_buf: i32,`<br/>&emsp;`in_len: i32,`<br/>&emsp;`root: i32,`<br/>&emsp;`out_buf: i32,`<br/>&emsp;`out_len: i32,`<br/>&emsp;`rounding_modes: i32`<br />`)`                                    | Compute the nth root of a float in rippled format.                | 1000     |
| `float_log(`<br/>&emsp;`in_buf: i32,`<br/>&emsp;`in_len: i32,`<br/>&emsp;`out_buf: i32,`<br/>&emsp;`out_len: i32,`<br/>&emsp;`rounding_modes: i32`<br />`)`                                                            | Compute the 10 based log of a float in rippled format.            | 1000     |

### 5.9. Trace

Output debug info to the `rippled` debug log (if trace logging is enabled). The maximum size of data that can be passed into these functions is 1024 bytes (attempting to pass in more will trigger an error).

Each of these host functions will return `0` on success and a negative value on failure.

| Function Signature                                                                                                                                      | Description                                             | Gas Cost |
| :------------------------------------------------------------------------------------------------------------------------------------------------------ | :------------------------------------------------------ | :------- |
| `trace(`<br/>&emsp;`msg_ptr: i32,`<br/>&emsp;`msg_len: i32,`<br/>&emsp;`data_ptr: i32,`<br/>&emsp;`data_len: i32,`<br/>&emsp;`as_hex: i32`<br />`)`     | A logging helper function.                              | 500      |
| `trace_num(`<br/>&emsp;`msg_ptr: i32,`<br/>&emsp;`msg_len: i32,`<br/>&emsp;`number:  i64`<br />`)`                                                      | A logging helper function for numbers.                  | 500      |
| `trace_opaque_float(`<br/>&emsp;`msg_ptr: i32,`<br/>&emsp;`msg_len: i32,`<br/>&emsp;`opaque_float_ptr: i32,`<br/>&emsp;`opaque_float_len: i32`<br />`)` | A logging helper function for floats in rippled format. | 500      |
| `trace_account(`<br/>&emsp;`msg_ptr: i32,`<br/>&emsp;`msg_len: i32,`<br/>&emsp;`account_ptr: i32,`<br/>&emsp;`account_len: i32`<br />`)`                | A logging helper function for accounts.                 | 500      |
| `trace_amount(`<br/>&emsp;`msg_ptr: i32,`<br/>&emsp;`msg_len: i32,`<br/>&emsp;`amount_ptr: i32,`<br/>&emsp;`amount_len: i32`<br />`)`                   | A logging helper function for amounts.                  | 500      |

### 5.10. Updating Fields

Update on-chain data associated with the WASM code.

This section is the only section of functions that will likely be different for each Smart Feature. Each may have its own way of storing data.

| Function Signature                                                           | Description                                                                                 | Gas Cost |
| :--------------------------------------------------------------------------- | :------------------------------------------------------------------------------------------ | :------- |
| `update_data(`<br/>&emsp;`data_ptr: i32,`<br/>&emsp;`data_len: i32`<br />`)` | Update the `Data` field in the ledger object that hosts the WASM code, e.g. a Smart Escrow. | 50       |

## 6. Security

### 6.1. Consensus

The WASM VM and spec guarantees that all WASM code will run identically on all machines (though, of course, a lot of testing will be done to ensure that this is the case).

WebAssembly is designed with deterministic execution in mind, and the specification ensures that properly constrained WASM code will produce the same output across all (compliant) runtimes. This XLS relies on those guarantees to ensure that all validators in the XRP Ledger network reach the same result when executing WASM code as part of transaction processing.

To that end:

- The runtime environment is fixed across all validator nodes, with an agreed-upon WebAssembly implementation (Wasmi), the Wasmi version, and a deterministic configuration (interpreted compile mode).
- Non-deterministic WASM features, such as floating point operations, access to time, randomness, or host system I/O, are explicitly disallowed or omitted from the runtime.
- A fixed, deterministic gas cost model is applied to all instructions, with enforced gas limits and metering to ensure bounded execution.

To ensure that all of this is the case, thorough testing across platforms and architectures will be conducted. Any divergence will be considered a critical consensus-breaking bug.

### 6.2. Mitigations for Bugs

If there happens to be a bug in the WASM execution layer, the UNL can shut down all usage of WASM code by setting the computation limit to 0.

### 6.3. Data Security

User-provided WASM code is executed within a strict sandbox. It has no access to system-level resources and can only interact with the XRP Ledger via an explicitly defined host function interface. These host functions enforce strict boundaries on what ledger data is visible and what operations are permitted. For example, there is no way for user-provided WASM code to directly modify a ledger object (to e.g. transfer XRP between accounts without permission).

A new WASM VM instance will be created for each WASM module execution. This ensures that there is no state that can be leaked between different executions, and that memory cannot be corrupted between runs.

WASM code cannot directly traverse arbitrary ledger directories or iterate through global ledger state. All access must be via bounded, predefined inputs (e.g., keylets or account IDs passed into the subroutine). This design ensures that malicious WASM code cannot manipulate or exfiltrate ledger state beyond the narrow scope allowed by the host API.

### 6.4. Resource Limiting

As discussed above, there is a strict gas limit and exceeding it will result in execution being immediately terminated with an exception.

Additionally, memory and stack usage are tightly constrained - the linear memory size is bounded to a fixed number of pages, and stack depth is capped to prevent runaway recursion or stack overflows.

These constraints prevent denial-of-service attacks and ensure that WASM execution remains fast and predictable, without any WASM-related transaction taking more than its share of `rippled` resources.

### 6.5. Future-Proofing

All future changes to this spec (even just a simple change to the gas cost of a host function) will need to be gated by an amendment. Updates to the `wasmi` package may also need to be gated by an amendment - every update will need to be tested for the potential of breaking changes.

For example, this is what it might look like to add a new host function:

```c
WASM_IMPORT_FUNC2(i, didKeylet, "did_keylet", hfs,     350);
WASM_IMPORT_FUNC2(i, escrowKeylet, "escrow_keylet", hfs,       350);
if (hfs->isAmendmentEnabled(featureLendingProtocol))
    WASM_IMPORT_FUNC2(i, loanKeylet, "loan_keylet", hfs,     350);
```

_(in `WasmVM.cpp`)_

This ensures that smart escrows cannot use the `loan_keylet` host function at all before the `LendingProtocol` amendment is activated, as the amendment proce`ss ensures that all nodes and validators have the code before it is run.

# Appendix

## Appendix A: Other WASM VMs Considered

### A.1. The Different WASM Compilation Modes

#### A.1.1. AOT (Ahead of Time)

AOT compiles WASM straight to native machine code ahead of time. If we were to use this compilation mode, users would have to store native machine code on the ledger.

**This isn’t useful for our needs**, as the compiled AOT code will be architecture-specific.

Can we figure out a way to support AOT? Possibly, but likely not without restricting rippled hardware to certain CPU architectures, and even then likely only one. Alternatively, to support AOT we would need to force WASM developers to supply variants that can run on any native architectures supported by rippled. Even if we imagine limiting rippled to 3 architectures, that would mean every smart contract developer would need to supply 3 different versions of their WASM, which would be wasteful from a space perspective. Last but not least, limiting rippled to 3 architectures seems counterproductive to decentralization.

#### A.1.2. JIT (Just-In-Time)

JIT compiles essentially as the code is run, or just before. This allows for additional caching and optimizations.

However, there are a few issues with JIT. From [this Stellar blog](https://stellar.org/blog/developers/why-doesnt-soroban-use-a-jit), JIT-based VMs are also not as secure and are susceptible to “JIT Bombs.” It has longer start times and greater memory usage. Mac also does not support JIT. The use of JIT may also result in different gas costs on different machines depending on what is in the cache, which would be a consensus-breaking change. Therefore, **JIT cannot be used for our needs**.

#### A.1.3. Interpreted

Interpreted mode just runs the code, like a REPL.

We decided on this mode because, well, the other two don't work for our needs, even though they're often more performant.

### A.2. The Different WASM Implementations

The 5 WASM VM implementations we investigated were:

- [WasmEdge](https://wasmedge.org/) (used by Xahau)
- [WasmTime](https://wasmtime.dev/)
- [Wasmer](https://github.com/wasmerio/wasmer)
- [Wasmi](https://github.com/wasmi-labs/wasmi) (used by Polkadot and Stellar’s Soroban)
- [WAMR](https://github.com/bytecodealliance/wasm-micro-runtime)

#### A.2.1. Initial Investigation

<img width="768" height="381" alt="image" src="https://github.com/user-attachments/assets/c3e4255c-f956-41f2-941f-90b643b3d567" />

Based on these findings, we narrowed down the search to **WasmEdge** and **WAMR**, and we then conducted further performance testing and analysis on those two options.

##### A.2.1.1. Performance Analysis

<img width="400" height="300" alt="image4" src="https://github.com/user-attachments/assets/7b82dfaa-e70a-4829-a987-20e6ae9ebb16" /><img width="400" height="300" alt="image2" src="https://github.com/user-attachments/assets/438255a5-cdae-4731-8f1a-0fe7218cb6ae" /><img width="400" height="300" alt="image1" src="https://github.com/user-attachments/assets/76fac8b0-63f6-43b1-b766-8a67799f5f59" />

These graphs clearly show that WAMR is much more performant.

#### A.2.2. Revisit

Several months later, we revisited the VM runtime decision. We found that Wasmi was a better fit for our needs than WAMR. See [this blog post](https://dev.to/ripplexdev/xrpl-programmability-wasm-runtime-revisit-2ak0) for more details.

## Appendix B: Memory Management Strategies Considered

Options:

1. Caller-Allocated: The contract developer (on the WASM side) allocates fixed size arrays for returning data. The user knows the pointer and the length.
   - This is really easy to implement, but means that the WASM dev needs to do their own memory allocation.
2. Host-Allocated: The host (rippled) allocates WASM memory in host functions and passes the pointer and the length to the WASM program.
   - This is super easy to use for devs, as they don’t need to worry about allocation. However, more research is needed to determine how possible it is, because currently the only way that we know how to do this involves allocating a new page every time (to ensure the host isn’t overwriting addresses in use).
3. Static Allocation: There is a static 4KB array in wasm that holds all output data. The pointer and length are fixed.
   - Pros
     1. This is pretty simple and clean to use
   - Cons
     1. Require an extra (2nd) copy step if the developer wants to use data from a previous host memory call (which is likely common)
4. The host uses a WASM-side defined allocator function in wasm to allocate, and returns a pointer and length tuple (this is what the devnet currently uses).
   - Pros
     1. This is pretty clean to use
   - Cons
     1. Increases the size of the WASM program because we use Vector allocation. To get around this we would need our own allocator.
     2. Takes more gas/makes the WASM bytecode long.

We decided on **Option 1** for the purpose of simplicity.

## Appendix C: FAQ

### C.1: How does this list of host functions compare to the Xahau Hooks [host functions](https://xrpl-hooks.readme.io/reference/hook-api-conventions)?

The host functions on this list are heavily inspired by the Hooks host functions. Most of the changes are just naming and simplifying the functions, and reworking how they're organized.

### C.2: Can we add a host function for [insert request here]?

Please share any request you have in the comments of this spec.

Some limitations:

- The transaction engine cannot access historical data - only current ledger state (since nodes aren’t required to hold any amount of past data).
- Due to security reasons, we don’t want to give host functions write access to raw ledger data (that would make exploits much easier to implement and it would be much harder for us to protect against them).

### C.3: Will gas fees be refundable if I pay for too much gas, like EVM?

Not at this time. This may be revisited later, and can be added in a future amendment.

Not all smart contract chains support refundable gas - for example, Solana does not.

### C.4: Will transactions that use the WASM VM be testable via `simulate`?

Yes, though that needs to be tested. This should make it easier for users to estimate gas usage.
