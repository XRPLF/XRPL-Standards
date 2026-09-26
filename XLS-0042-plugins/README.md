<pre>
  xls: 42
  title: XRPL Plugins
  description: A plugin transactor API to make it easier for developers to modify rippled for sidechains without needing C++ knowledge
  author: Mayukha Vadari <mvadari@ripple.com>
  proposal-from: https://github.com/XRPLF/XRPL-Standards/discussions/116
  status: Stagnant
  category: System
  created: 2023-06-26
</pre>

# XRPL Plugins

## Abstract

The plugin transactor API is a proposed project. The guiding question: **How can we make it easier for developers to modify `rippled` to build sidechains, without needing to know C++?**

The architecture will be as follows:

1.  A shared library (with wrappers to convert it into a native library) that is…
2.  Called by a program (the “plugin”) that is written by the user and contains all of the transaction logic, which is…
3.  Compiled as a dynamic library, via a thin C++ layer if needed, which is…
4.  Loaded by `rippled` at runtime, without needing to recompile

<p align="center">
  <img src="https://user-images.githubusercontent.com/8029314/245570318-d8694aeb-dc79-4c1e-a2c5-97eed404089a.png" />
</p>

The first non-C++ language in which to implement this design will be Python. This is because there is an easy-to-use and well-documented C/C++ API, which will make the connectors easier to write, and it is usually well-known by devs of C++/other similar languages.

We will initially implement this project in 2 languages:

- C++
- Python

_Note:_ this design only applies to transactions and ledger objects, not RPC requests. There will be a separate design for that at a later point in time, as it would also be useful to have plugin versions of those features. It will likely be similar.

## 1. Introduction

The main idea behind this project is to make transactions language-agnostic, so developers don’t need to intimately know C++ in order to modify `rippled` to add new features.

### Non-Goals

- Make it easy to make _any_ change in `rippled`.
  - This is too large of a scope to be easily doable.
  - The focus will be on new transaction types/ledger object types/RPCs.
- Add new features to mainnet in languages that aren’t C++.
  - This is less type-safe and (in some languages) less performant.
  - In addition, mainnet is purposefully conservative about what features are added, to ensure network stability.

### 1.1. Background

#### 1.1.1. Anatomy of a Transactor

The term "transactor" refers to the code in `rippled` that processes a transaction.

Every transaction is mainly made up of 5 functions:

- `preflight`
  - What is everything that you can check about the validity of the transaction without needing to check the current ledger state?
    - This method is run by the node that receives the submitted transaction before it is broadcast to peers, so any errors that are caught here helps make the network more efficient. An error caught here also does not incur a transaction fee.
- `preclaim`
  - What can you check about the validity of the transaction with _read-only_ access to the ledger state (within reason, since you don’t want to duplicate too much work between `preclaim` and `doApply`)?
- `doApply`
  - Do a few sanity checks, and actually try to apply the transaction.
- `calculateBaseFee`
  - Calculate the fee that the transaction needs to pay (usually this is just inherited from the base transactor, but some transactions, like `AccountDelete`, need higher fees).
- `makeTxConsequences`
  - Used when an account has multiple transactions queued to estimate whether it’ll be able to pay the fees for all of them.

There are several other methods that transactors call, but they only rarely need to be modified.

Other parts of transactions include:

- The params of a transaction (`TxFormats`)
- The transaction type ID (`TxType`)
- The strings in the JSON (`jss`)
- The flags for the transaction (`TxFlags`)
- The `SField`s in a transaction
- The types of the `SField`s in a transaction (Serialized Types)

#### 1.1.2. Dynamic Libraries

Shared libraries (`.so` on Unix-like systems, `.dylib` on macOS, and `.dll` on Windows), allow programs to load external libraries at runtime. This dynamic nature allows us to compile plugins separately from `rippled` and still include the plugin code in the `rippled` runtime.

During dynamic loading, the program specifies the shared library's name or path to the runtime loader, which handles the process. The loader locates the shared library file and maps it into the program's memory space. This step effectively integrates the library's code and data into the program, allowing seamless execution of the library's functionality.

## 2. C++ Shared Library (`xrpl_plugin`)

`xrpl_plugin` is a new static library that contains the core C++ code from `rippled` that the plugins need to be able to process and update data from `rippled`. To add support for plugins in a language, a wrapper will need to be written in the target language around this library.

The following classes/files will move from `rippled` to `xrpl_plugin`:

- `View`/`ReadView`/`OpenView`
- `ApplyView`/`ApplyViewBase`/`ApplyViewImpl`
- `LoadFeeTrack`
- `HashRouter`
- `SignerEntries`
- `TxConsequences` (pulled from `applySteps`)
- `validity` (pulled from `apply`)
- `error`

## 3. Plugin API

The plugin API is how the plugins communicate with `rippled`. It is a C-based API, so that plugins can be written in languages that don't have support for C++\-specific features (like `std::vector`).

To enable integration, plugins are compiled into a shared library. This shared library exposes C-style function pointers, which can be easily accessed from within the `rippled` runtime. The relevant sections of `rippled` can then invoke these function pointers to extract the required information from the plugins.

By adopting this approach, we establish a modular architecture that allows for extensibility and encapsulation. The C API acts as a bridge, enabling communication between the plugin functionality and the core `rippled` codebase, ensuring seamless interaction and facilitating the extraction of necessary data or operations.

There are several functions that the API exposes. Each returns an array of the structs described below it. This section describes the raw C-style API that is exposed to `rippled`; different languages may (and should) implement a neater API for exports on top of this lower-level API.

### 3.1. Transactors

- `extern “C” getTransactors`
  - `char const* txName;`
  - `std::uint16_t txType;`
  - `Param[] txFormat;`
  - `TxConsequences makeTxConsequences(PreflightContext const& ctx);`
  - `XRPAmount calculateBaseFee(ReadView const& view, STTx const& tx);`
  - `NotTEC preflight(PreflightContext const& ctx);`
  - `TER preclaim(PreclaimContext const& ctx);`
  - `TER doApply(ApplyContext& ctx, XRPAmount mPriorBalance, XRPAmount mSourceBalance);`
  - `typedef NotTEC checkSeqProxy(ReadView const& view, STTx const& tx, beast::Journal j);`
  - `NotTEC checkPriorTxAndLastLedger(PreclaimContext const& ctx);`
  - `TER checkFee(PreclaimContext const& ctx, XRPAmount baseFee);`
  - `NotTEC checkSign(PreclaimContext const& ctx);`

_Note: Every array will be represented as a `{pointer, size}` struct, since non-fixed-length arrays can’t be passed as parameters._

#### 3.1.1. `txName`

The name of the transaction.

#### 3.1.2. `txType`

The unique ID of the transaction.

#### 3.1.3. `txFormat`

The parameters of the transaction, and whether they're required or optional.

#### 3.1.4. `makeTxConsequences`

The function pointer for the `makeTxConsequences` function.

The `PreflightContext` variable provides access to the transaction being processed and other info like the currently-enabled amendments.

#### 3.1.5. `calculateBaseFee`

The function pointer for the `calculateBaseFee` function.

`ReadView` provides read-only access to the ledger state, and `tx` is the transaction being processed.

#### 3.1.6. `preflight`

The function pointer for the `preflight` function.

The `PreflightContext` variable provides access to the transaction being processed and other info like the currently-enabled amendments. `NotTEC` is any result code that doesn't start with `tec...`.

#### 3.1.7. `preclaim`

The function pointer for the `preclaim` function.

The `PreclaimContext` variable provides access to the transaction being processed and other info like the currently-enabled amendments, as well as read-only access to the ledger state. `TER` is any result code.

#### 3.1.8. `doApply`

The function pointer for the `doApply` function.

The `ApplyContext` variable provides access to the transaction being processed, as well as read _and_ write access to the ledger state. `mPriorBalance` is the balance of the account that submitted the transaction prior to running the transaction, and `mSourceBalance` is the current balance. `TER` is any result code.

#### 3.1.9. `checkSeqProxy`

This function won't need to be overridden very often. It validates the sequence number of the transaction and is run as a part of processing `preclaim`.

`beast::Journal` is a logging variable.

#### 3.1.10. `checkPriorTxAndLastLedger`

This function won't need to be overridden very often. It validates the `AccountTxnID` and `LastLedgerSequence` of a transaction and is run as a part of processing `preclaim`.

#### 3.1.11. `checkFee`

This function won't need to be overridden very often. It validates the fee of a transaction and is run as a part of processing `preclaim`.

#### 3.1.12. `checkSign`

This function won't need to be overridden very often. It validates the signature (or signatures) of a transaction and is run as a part of processing `preclaim`.

### 3.2. Ledger Object Types

- `extern “C” getLedgerObjects` (needed if there are new ledger objects)
  - `std::uint16_t type;`
  - `char const* name;`
  - `char const* rpcName;`
  - `Param[] format;`
  - `bool isDeletionBlocker;`
  - `TER deleteObject(Application& app, ApplyView& view, AccountID const& account, uint256 const& delIndex, std::shared_ptr<SLE> const& sleDel, beast::Journal j);`
  - `std::int64_t visitEntryXRPChange(bool  isDelete, std::shared_ptr<STLedgerEntry const> const&  entry, bool  isBefore);`

#### 3.2.1. `type`

The unique number for the ledger object type. This is analogous to the transaction type value.

#### 3.2.2. `name`

The name of the object, which will show up in the `LedgerEntryType` parameter. Should be in `CamelCase`.

#### 3.2.3. `rpcName`

The filter used in RPC commands, like `account_objects`. Should be in `snake_case`.

#### 3.2.4. `format`

The format (parameters and whether or not they're required) of the ledger object.

#### 3.2.5. `isDeletionBlocker`

Whether the object should be a blocker for account deletion. An example of a blocker is an escrow; an example of a non-blocker is a ticket.

#### 3.2.6 `deleteObject`

If an object is not an account deletion blocker, then the `AccountDelete` transaction needs to know how to delete it, since the object must be deleted when the owner account is removed from the ledger. This function handles that process. This function is only used (and must be included) if `isDeletionBlocker` is `false`.

#### 3.2.7. `visitEntryXRPChange`

This function is used as a part of the invariant check that determines whether the total amount of XRP has changed in the ledger. If an object stores value, like an Escrow, then this function is required.

### 3.3. `SField`s

An `SField` is a "serialized field" in `rippled`. All transaction fields and ledger object fields are `SField`s. While new transaction fields aren't strictly necessary (a lot of common ones already exist, like `Destination`), many new transactors will require new `SField`s. In `rippled`, `SField`s are declared in [`ripple/protocol/SField.h`](https://github.com/XRPLF/rippled/blob/develop/src/ripple/protocol/SField.h) and the variable names are preceded with `sf` (e.g. `sfDestination`).

- `extern “C” getSFields`
  - `int typeId;`
  - `int fieldValue;`
  - `const char * txtName;`

#### 3.3.1. `typeId`

This is the type of the field's value (e.g. is it a `UInt32` or an `AccountID`). For example, the `typeId` of `STAccount` (the type that represents accounts) is `8`.

#### 3.3.2. `fieldValue`

This is the unique value of the field. Every `SField` must have a unique `(typeId, fieldValue)` pair. For example, `sfDestination` has the pair `(8, 3)`.

#### 3.3.3. `txtName`

The actual text name of the `SField` (e.g. `Destination`).

### 3.4. Serialized Types

Serialized types are the valid types of `SField`s. For example, `STAccount` represents all account fields. 99.9% of the time, plugin devs will not need to create new serialized types, but if they do, they can import them in.

For an example of what a serialized type looks like in C++, you can refer to [`STAccount`](https://github.com/XRPLF/rippled/blob/develop/src/ripple/protocol/STAccount.h).

- `extern “C” getSTypes`
  - `int typeId;`
  - `Buffer parseValue(SField const& field, chat const* json_name, char const* fieldName, SField const* name, Json::Value value, Json::Value error);`
  - `char const* toString(int typeId, Buffer buf);`
  - `Json::Value toJson(int typeId, Buffer buf);`
  - `void toSerializer(int typeId, Buffer& buf, Serializer& s);`
  - `Buffer fromSerialIter(int typeId, SerialIter& st);`

#### 3.4.1. `typeId`

This is the type of the field's value (e.g. is it a `UInt32` or an `AccountID`). For example, the `typeId` of `STAccount` (the type that represents accounts) is `8`.

#### 3.4.2. `parseValue`

This function parses the data from a JSON. Most of the parameters are only for better error-handling.

#### 3.4.3. `toString`

This function generates a human-readable version of the data.

#### 3.4.4. `toJson`

This function generates the JSON version of the data. If this is not specified, it will use `toString`.

`Json::Value` is any JSON-safe object (such as `int` or `char const*`).

#### 3.4.5. `toSerializer`

This function serializes the new type to its serialized version.

#### 3.4.6. `fromSerialIter`

This function processes the new type from its serialization, such as in a transaction blob.

### 3.5. Amendments

New transactions should be guarded by [amendments](https://xrpl.org/amendments.html).

You can refer to [`Feature.h`](https://github.com/XRPLF/rippled/blob/develop/src/ripple/protocol/Feature.h) for more details on how amendments are processed.

- `extern “C” getAmendments` (needed if there are new amendments, which there should be)
  - `char const* name;`
  - `bool supported;`
  - `VoteBehavior vote;`

#### 3.5.1. `name`

The name of the amendment (e.g. `DisallowIncoming`).

#### 3.5.2. `supported`

Whether or not the amendment is complete and ready to be voted on. This will almost always be `True` (yes).

#### 3.5.3. `vote`

The default vote for the amendment for validators.

### 3.6. Result Codes

New transactions may introduce new result codes. This function facilitates the export of those result codes.

You can refer to [`TER.h`](https://github.com/XRPLF/rippled/blob/develop/src/ripple/protocol/TER.h) for more details about the result codes.

- `extern “C” getTERcodes` (needed if there are new transaction result codes)
  - `int code;`
  - `char const* codeStr;`
  - `char const* description;`

#### 3.6.1. `code`

The unique integer code for the result code (e.g. `temDISABLED` is `-273`). Each type of result (`tec`, `ter`, etc.) has its own range of valid codes.

#### 3.6.2. `codeStr`

The short string name of the code (e.g. `"temDISABLED"`).

#### 3.6.3 `description`

The longer description of the result (e.g. `"The transaction requires logic that is currently disabled."`).

### 3.7. Invariant Checks

[Invariant checking](https://xrpl.org/invariant-checking.html) is a safety feature of the XRP Ledger. It consists of a set of checks, separate from normal transaction processing, that guarantee that certain invariants hold true across all transactions. These invariants serve as crucial checks to maintain the consistency and integrity of the XRPL ledger, preventing any unexpected or undesirable behavior. Some examples include ensuring that no XRP was created and there aren't any offers with negative amounts.

You can refer to [`InvariantChecks.h`](https://github.com/XRPLF/rippled/blob/develop/src/ripple/app/tx/impl/InvariantCheck.h) for more details about the code.

Not all new ledger objects will require new invariant checks, but plugin devs can write their own invariant checks if needed.

- `extern “C” getInvariantChecks`
  - `void visitEntry(void* id, bool isDelete, std::shared_ptr<STLedgerEntry const> const& before, std::shared_ptr<STLedgerEntry const> const& after);`
  - `bool finalize(void* id, STTx const& tx, TER const result, XRPAmount const fee, ReadView const& view, beast::Journal const& j);`

#### 3.7.1. `visitEntry`

This function is called on each ledger entry that is touched in any given transaction. It processes the before and after state of the ledger object, to see what has changed for this invariant. For example, the "no XRP created" check totals up the XRP before and after the transaction is run.

`STLedgerEntry` represents a single ledger object. The `id` param is used to make it easier for plugins to store data between `visitEntry` and `finalize`.

#### 3.7.2. `finalize`

This function is called after all ledger entries that were touched by the given transaction have been visited. It determines the final status of the check: whether it has passed or failed.

`TER` is any result code, `ReadView` provides read-only access to the ledger, and `beast::Journal` is a logging variable.

### 3.8. Inner Object Formats

When working with nested objects (`STObject`), it is highly recommended that you create `InnerObjectFormat`s for those objects, so its shape is well-defined. One example of an inner object is `SignerEntry`, which is a sub-type inside of `SignerEntries`.

- `extern “C” getInnerObjectFormats` (needed if there are any `STObjects` used in the transactions or ledger objects)
  - `char const* name;`
  - `int code;`
  - `Param[] format;`

#### 3.8.1. `name`

The name of the inner object.

#### 3.8.2. `code`

The field code of the `SField` of the inner object.

#### 3.8.3. `format`

The parameters of the inner object.

### 3.9 Shutdown

Some languages, like Python and JavaScript, interact with C++ by running an interpreter in C++ that runs the code. Plugins written in these languages sometimes need to be told to shut down the interpreter when `rippled` shuts down. This is essentially a plugin cleanup function, and has a `void` return type.

- `extern “C” shutdown` (needed if any shutdown cleanup is needed)

## 4. Changes to `rippled`

There is no amendment required to add support for plugin transactors, and the changes are fully backwards-compatible.

## 5. Considerations

This functionality is primarily designed for sidechains and experimentation purposes, and is not intended for use on the mainnet due to potential security and performance concerns. It should be used with caution outside of sidechain or experimental contexts.

### 5.1. Security

An internet connection is not necessary unless you deliberately configure your transactor to interact with the internet, which is theoretically doable but inadvisable. This is also true of non-plugin transactors, so there is no change in the security model here.

To ensure the integrity and authenticity of the plugin, each validator should independently verify its correctness. This can be done by comparing file hashes distributed alongside the code. Validators can calculate the hash of the shared library and check if it matches the provided hash. This verification process helps confirm that the correct library is being used and reduces the risk of running unauthorized or modified code.

### 5.2. Performance

Certain languages, like Python, may have performance limitations compared to using native C++. In addition, there may be some performance issues in the FFI layer (these will be language-specific).

## 6. Additional Language Support

Introducing support for a new programming language typically involves modifying two key components.

First, wrappers need to be created around the C/C++ `xrpl_plugin` library code to transform it into a native package that can be seamlessly used within the new language's ecosystem. These wrappers act as an FFI bridge, enabling the interaction between the library and code written in the new language.

Second, a C API must be implemented to expose C-style function pointers from a shared library, following the API rules described in Section 3. In the case of higher-level languages like Python (which doesn't have any way to generate a shared library that exposes function pointers), an additional C++ wrapper layer may be necessary to bridge the gap between the C API and the language's specific constructs.

### 6.1. Python

Since Python does not support directly exposing function pointers, a thin C++ layer is needed, to expose those function pointers to the plugin API. This layer's sole responsibilities are exposing function pointers, managing memory, and retrieving data from the Python code. By acting as an intermediary, this C++ layer enables smooth integration between Python and the plugin API.

### 6.2. JavaScript

JavaScript plugins are still in an experimental phase, so there are likely additional challenges that need to be addressed. However, similar to Python, it will also require a thin C++ layer to communicate with `rippled`'s plugin API, since JavaScript also does not have support for directly exposing function pointers.
