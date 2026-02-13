<pre>
  xls: 97
  title: Formats, Fields and Flags
  description: Adding ledger entry and transaction flags and formats to the server_definitions RPC response.
  implementation: https://github.com/XRPLF/rippled/pull/5702
  author: Chenna Keshava B S (@ckeshava), Mayukha Vadari (@mvadari)
  category: System
  status: Draft
  proposal-from: https://github.com/XRPLF/XRPL-Standards/discussions/418
  created: 2025-11-25
</pre>

# System XLS: Add Formats and Flags to `server_definitions`

## 1\. Abstract

The [server\_definitions RPC command](https://xrpl.org/docs/references/http-websocket-apis/public-api-methods/server-info-methods/server_definitions) is an existing API endpoint that provides client applications with essential protocol information needed to properly interact with the XRPL network. Currently, it returns all the details necessary to serialize and deserialize data encoded in the custom XRPL binary format. This document proposes new additions to the `server_definitions` RPC response. Specifically, it advocates adding transaction formats, ledger object formats, transaction flags and ledger specific flags in the `server_definitions` response.

## 2\. Motivation

This information helps client libraries understand how to serialize/deserialize XRPL data structures, construct valid transactions, and parse valid ledger entries. Essentially, the basics of an XRPL library in any programming language could be constructed just from the details of the `server_definitions` output with the additions.

Some of the envisioned benefits of this proposal:

* Import: Enables clients to import all supported transactions as well as the inputs/outputs.  
* Validation: Enables client-side validation before submitting to the network. Clients do not need to resort to blind-signing the transactions i.e. clients can infer the correct structure of the transactions using the response of the `server_definitions` RPC.  
* Better Error Messages: Applications can provide specific feedback about missing required fields. These error messages can be tailored to be more informative instead of the terse rippled error messages.  
* Protocol Compliance: Ensures applications stay in sync with protocol changes. This can be accomplished by periodically fetching the `server_definitions` RPC response

## 3\. RPC: `server_definitions`

The `server_definitions` RPC [already exists](https://xrpl.org/docs/references/http-websocket-apis/public-api-methods/server-info-methods/server_definitions). A sample output is available [here](https://xrpl.org/resources/dev-tools/websocket-api-tool?server=wss%3A%2F%2Fs1.ripple.com%2F&req=%7B%20%20%22command%22%3A%20%22server_definitions%22%0A%7D). This spec proposes some additions. 

### 3.1. Request Fields

There are no changes to the request fields. The current request fields are shown below:

| Field Name | Required? | JSON Type | Description |
| :---- | :---- | :---- | :---- |
| `command` | Yes | `string` | Must be "`server_definitions`" to access this RPC |
| `hash` | No | `string` | A hash of the `server_definitions` data. If this matches the hash the rippled server has, only the hash will be returned. |

### 3.2. Response Fields

Current response fields:

| Field Name | Always Present? | JSON Type | Description |
| :---- | :---- | :---- | :---- |
| `TYPES` | No, not included if `hash` matches the server's data hash | `object` | Map of data types to their ["type code"](https://xrpl.org/docs/references/protocol/binary-format#type-codes) for constructing field IDs and sorting fields in canonical order. Codes below 1 should not appear in actual data; codes above 10000 represent special "high-level" object types such as "Transaction" that cannot be serialized inside other objects. See the Type List for details of how to serialize each type.  |
| `LEDGER_ENTRY_TYPES` | No, not included if `hash` matches the server's data hash | `object` | Map of ledger objects to their data type. These appear in ledger state data, and in the "affected nodes" section of processed transactions' metadata.  |
| `FIELDS` | No, not included if `hash` matches the server's data hash | `array` | A sorted array of tuples representing all fields that may appear in transactions, ledger objects, or other data. The first member of each tuple is the string name of the field and the second member is an object with that field's properties. (See the "Field properties" table below for definitions of those fields.)  |
| `TRANSACTION_RESULTS` | No, not included if `hash` matches the server's data hash | `object` | Map of transaction result codes to their numeric values. Result types not included in ledgers have negative values; tesSUCCESS has numeric value 0; tec-class codes represent failures that are included in ledgers.  |
| `TRANSACTION_TYPES` | No, not included if `hash` matches the server's data hash | `object` | Map of all transaction types to their numeric values.  |
| `hash` | Yes | `string` | The hash of the `server_definitions` data that the rippled server has. |

Proposed additions:

| Field Name | Always Present? | JSON Type | Description |
| :---- | :---- | :---- | :---- |
| `LEDGER_ENTRY_FORMATS` | No, not included if `hash` matches the server's data hash | `object` | Detailed format specifications for all ledger entry types (`AccountRoot`, `RippleState`, `Offer`, etc.) \- namely, the fields and their optionality. |
| `TRANSACTION_FORMATS` | No, not included if `hash` matches the server's data hash | `object` | Detailed format specifications for all transaction types (`Payment`, `OfferCreate`, `TrustSet`, etc.) \- namely, the fields and their optionality. |
| `LEDGER_ENTRY_FLAGS` | No, not included if `hash` matches the server's data hash | `object` | Complete mapping of all ledger entry flags with their hexadecimal values. |
| `TRANSACTION_FLAGS` | No, not included if `hash` matches the server's data hash | `object` | Complete mapping of all transaction flags with their hexadecimal values.  |
| `ACCOUNT_SET_FLAGS` | No, not included if `hash` matches the server's data hash | `object` | Complete mapping of all `AccountSet` flags (`asf` flags) with their hexadecimal values.  |

#### 3.2.1. Fields

##### 3.2.1.1. LEDGER\_ENTRY\_FORMATS

The format of this field is an `object`. The keys of the `object` are the ledger entry type name (e.g. `Offer`), or `common` (for the common fields across all ledger entries). The values of the `object` are an array of elements described as follows:

| Field Name | Always Present? | JSON Type | Description |
| :---- | :---- | :---- | :---- |
| `name` | Yes | `string` | The name of the field. |
| `optionality` | Yes | `number` | The `soeREQUIRED` value of the field \- one of the following values: [-1, 2] (both inclusive). [More details found here](#3.2.1.1.1). |

##### 3.2.1.1.1 `optionality` number-text map

The `optionality` values are mapped to the following text <-> number combination. For the purpose of improved readability, this mapping is borrowed from the [`SOEStyle` enum definition](https://github.com/XRPLF/rippled/blob/e11f6190b74599737f9f554da3b141f269e43803/include/xrpl/protocol/SOTemplate.h#L13) in the rippled codebase.

| Number | Optionality |
| :---- | :---- |
| `-1` | `soeINVALID` |
| `0` | `soeREQUIRED` |
| `1` | `soeOPTIONAL` |
| `2` | `soeDEFAULT` |

##### 3.2.1.2. TRANSACTION\_FORMATS

The format of this field is an `object`. The keys of the `object` are the transaction type name (e.g. `OfferCreate`, or `common` (for the common fields across all transactions). The values of the `object` are an array of elements described as follows:

| Field Name | Always Present? | JSON Type | Description |
| :---- | :---- | :---- | :---- |
| `name` | Yes | `string` | The name of the field. |
| `optionality` | Yes | `number` | The `soeREQUIRED` value of the field \- one of the following values: [-1, 2] (both inclusive). [More details found here](#3.2.1.1.1). |

##### 3.2.1.3. LEDGER\_ENTRY\_FLAGS

The format of this field is an `object`, with the keys being the ledger entry type name (e.g. `Offer`) and the values being another `object`. This nested `object`'s keys are the `lsf` name (e.g. `lsfSell`), and its values are the corresponding integer values (e.g. `131072`).

Only ledger entry types that have flags are included in this.

##### 3.2.1.4. TRANSACTION\_FLAGS

The format of this field is an `object`, with the keys being the transaction type name (e.g. `OfferCreate`) and the values being another `object`. This nested `object`'s keys are the `tf` name (e.g. `tfPassive`), and its values are the corresponding integer values (e.g. `65536`).

Only transaction types that have flags are included in this.

##### 3.2.1.5. ACCOUNT\_SET\_FLAGS

The format of this field is an `object`, with the keys being the `asf` name (e.g. `asfDefaultRipple`) and the values being the corresponding integer values (e.g. `8`).

### 3.3. Failure Conditions

Currently, the only failure conditions are if the `hash` field submitted in the request is not a valid 256-bit hash.

There are no changes to the failure conditions of the `server_definitions` RPC. There are no new reasons for the RPC to return failure codes.

### 3.4. Sample Request

```json
{
    "command": "server_definitions"
}
```

### 3.5. Sample Response

A sample response is available [here](https://gist.github.com/mvadari/407732fee9d37678b372b4f9df01a311).

## 4\. Rationale

Currently, clients must manually hardcode or scrape this structural information from the `rippled` source, which is brittle and creates high maintenance overhead. Centralizing these definitions on the server offers:

* **Reduced Client Maintenance:** Clients fetch definitions directly, eliminating the need to update internal data with every protocol change.  
* **Better Tooling:** Enables dynamic, self-validating client applications (e.g., wallet forms) that ensure transaction correctness.  
* **Consistency:** Guarantees all client libraries use the single, authoritative view of the protocol.

### 4.1. Alternate Designs Rejected

* **Separate RPCs:** Rejected for requiring multiple network calls; consolidation is more efficient. In addition, this is essentially the purpose of the `server_definitions` RPC.

## 5\. Backwards Compatibility

New additions to the RPC responses do not affect backwards compatibility. None of the existing systems are affected if they choose to not make use of the proposed changes.

## 6\. Test Plan

This feature needs to be accompanied with suitable unit tests in the rippled code repository. The number of transactions, ledger objects, ledger-specific flags, and transaction flags are suitably determined at compile-time. The tests can validate the content of the RPC responses for specific transactions and ledger-objects. This is not as exhaustive as validating every transaction and ledger object. However, it is easier to maintain the test cases.

## 7\. Reference Implementation

A reference implementation can be found [here](https://github.com/XRPLF/rippled/pull/5702) and [here](https://github.com/XRPLF/rippled/pull/5616). Note: This implementation does not comprehensively implement all the proposed changes yet.

## 8\. Security Considerations

The information returned by the `server_definitions` RPC is already available in various configuration files across rippled. No private or confidential information is revealed by this proposal.

This RPC also does not modify any ledger state.

The server caches the `server_definitions` response, since it does not change while the server is running. This severely mitigates DoS risks.
