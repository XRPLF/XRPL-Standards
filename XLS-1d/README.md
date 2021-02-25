XLS-1d Contract Standard
=======================

## 1.0 Introduction
A _contract_ is a byzantine fault tolerant replicated finite state machine with a provable state. In other words—a _contract_ is a program that runs in a secure decentralised manner.

## 1.1 Definitions
* `client` — any user or other contract connecting to an _instance_ over the public _RPC_ interface.
* `contract` — BFT replicated program with one or more _instances_.
* `consensus` — BFT ordering of an unordered set via a series of proposal rounds.
* `cUNL` — contract unique node list, a list of public keys identifying all valid peers.
* `FSM` — finite state machine; refers to the business logic of the contract's code.
* `instance` — a copy of the contract's code running on a _node_.
* `IIC` — inter-instance communication, used to control the consensus process.
* `node` — a codius host.
* `peer` — another _instance_ of the _contract_ under examination running on another _node_.
* `request` — an RPC call made by a client.
* `response` — an RPC response sent to a client by an instance, in response to a previous request.
* `RPC` — remote procedure call protocol specifically JSON RPC 2.0.
* `state` — the sum total of the key-value store of a contract instance.
* `state hash` — a cryptographically secure representation of part or all of the state of an instance.
* `URQ` — unordered request queue

## 1.2 Purpose
The purpose of this document is to define a standard by which `instances` of codius `contracts` established on `nodes` communicate with their `peers`, reach consensus, and make forward progress, and by which `clients` interact with the contract by making `requests` and receiving `responses`. This specification defines a required set of  blackbox interfaces for contracts as well as an optional recommendations for their implementation.

## 1.3 Overview
```
*--------*        (RPC)         *-------------*             (IIC)
| client | ---- 1.request --->  | node A runs |  ---- 2. client request --*
| (user) | <--- 5.response ---  | instance A  |                 relayed   |
*--------*                      | contains:   |        (IIC)              V
                                | - FSM       | <- 3. consensus -> *-------------*
                                | - state     | <- 4. state  ----> | node B runs |
                                *-------------*       updated      | instance B  |
                                                                   | incl. FSM,  |
                                                                   | state       |
                                                                   *-------------*


```


## 2.0 Communication
Each instance listens on at least one port: a private `IIC` port and optionally a public `RPC` port. The private port must accept `IIC` messages. The public port, if open, must accept incoming requests from `clients`.

## 2.1 Public Port
The `instance` may choose to have a public port. This must be a TLS websocket and must accept JSON RPC 2.0 calls known as `requests`. Each `request` is interpreted as an attempt to call a function in the `FSM`. These `requests` may be throttled or discarded according to resource constraints. The `instance` which received the request has the sole responsibility to furnish to the client a `response`.

## 2.1.1 Request
A `request` is per s4 of the JSON-RPC 2.0 Specification.

## 2.1.2 Response
A `response` is per s5 of the JSON-RPC 2.0 Specification, and is optional as determined by the program logic of the `FSM`. If a `response` is furnished it may be immediate (i.e. a `read-only request`) or it may be furnished after one or more consensus cycles or according to some other timer or condition. More than one `response` may be furnished if the `request` is a subscription.

## 2.1.3 Error object
If a method returns abnormally it should return an error object as per s5.1 of JSON-RPC 2.0 Specification. In addition to the standard errors listed in that specification the following error codes are added:
* -32521 — `No Network` the connected instance is not currently serving public traffic due to loss of peer connectivity or inability to retrieve the current state of the contract.
* -32429 — `Busy` the connected instance has insufficient resources to serve the request.
* -32302 — `Moved` the instance does not wish to serve requests and provides a ```{"endpoint":"wss://..."}``` in the `data` section of the message telling the `client` about another `instance` to connect to.

## 2.1.4 Timeouts
Timeouts are in accordance with standard TLS websocket and the `nodes` TCP configuration. Additionally a contract may enforce a more stringent timeout criteria as its `FSM` dictates. It is up to the `client` to detect and deal with timeouts. `FSM` business logic should allow for the possibility of a haphazardly connecting `client` who could lose response objects through a bad connection. The contract makes no guarentees about the quality or integrity of the communication channel over which the client connects, and all responses are delivered in `at-most-once` semantics.

## 2.2 Private Port
Each `instance` must have a private port on which it emits and receives `IIC` messages from `peers`. The specific implementation of a `contracts` consensus mechanism and inter-instance messaging system is not mandated by this standard however guidance is given in section 3.

## 3.0 Inter-Instance Communication
How the contract implements its `IIC` is up to the developers, however due to the general complexity of BFT consensus this standard defines an example `IIC` messaging schema which _may_ be used if desired.

## 3.1 Message Types
`IIC` should consist of, at minimum, a set of messages implemented in a contract that allow its `instances` to:
* __relay__ incoming `client` `requests` from the receiving instance to all other active cUNL instances
* __propose__ a sequence for those `requests` through a chosen form of BFT consensus
* __validate__ the outcome of consensus so the `requests` may be applied to the FSM
* __copy__ part or all of the contract's state from one instance to a peer on demand to ensure consistent state across all instances (state transfer),

## 3.2 Security
In addition an `IIC` must cryptographically identify `peers` via a `cUNL` and validate each message from each `peer`.

## 3.3 Reference IIC Schema
This section provides one possible messaging schema that _may_ be used.

### 3.3.1 `relay` message
A relayed client request that was made to another instance. Each `request` is hashed by the receiving `instance` to form a `request hash`. This ensures that nodes do not include a request more than once in their `URQ`.
```
{
	"type": "relay",
	"payload": /* client request verbatim */,
	"timestamp": /* micro unixtime UTC+0 */,
	"signature": /* peer signature of payload with appended timestamp  */,
	"pubkey": /* signing key, should be from cUNL */
}
```

### 3.3.2 `proposal` message
A set of requests to include in this consensus round.
```
{
	"type": "proposal",
	"round": /* consensus round number: 0,1,2 */
	"payload": [request_1_hash, ..., request_n_hash],
	"timestamp": /* micro unixtime UTC+0 */,
	"state": /* root of the merkel state tree (hash) */,
	"signature": /* peer signature of payload with appended timestamp  */,
	"pubkey": /* signing key, should be from cUNL */
}
```

### 3.3.3 `validation` message
An announcement that a particular proposal was applied to the FSM, and the next round has begun.
Identical to proposal message but type is `validation`.

### 3.3.4 `copy` message
A request for a state transfer of part or all of the state merkle tree by referencing a `state hash`. If a leaf node of the merkle tree is requested then the data represented by it is sent. If a non-leaf node is requested then only the merkle tree below it is sent.

`//todo: finish`

## 4.0 State

The state of all `instances` must remain well synchronised and consistent. If an `instance` falls out of synchronisation it must be able to acquire the current state of the contract. It is recommended that contracts store their state in a persistent manner (e.g. filesystem) to provide for the possible of an all-instance outage.

### 4.1 State Representation
The complete current state of a contract _excluding_ pending or currently negotitated `requests` must be represented by a cryptographically secure hash called a `state hash`. It is recommended that contracts use a Merkle Tree representation for their state, e.g. a Merkle Patricia Trie, to avoid unnecessarily transfering the whole state each time there is a desynchronisation event.

### 4.2 State Transfer
An `instance` must be able to request a copy of the data represented by a valid recent `state hash` from any of its `peers`. An `instance` lacking the current state of the contract must not serve public `requests` (it should return an error object as per s2.1.3) until it is reasonably satisfied it has acquired the current state and is correctly performing consensus with its `peers`.

### 4.3 State Chain
Contracts must retain at least the previous `state hash` as an element of the current state. This provides a provable state chain. The current `state hash` must also be communicated to `peers` during each consensus round to ensure that each `instance` is performing consensus on the same state.

### 4.5 State Logging
Contracts may log as much or as little of the state as they wish. It is recommended that contracts retain a rolling log of recently applied states and `requests`.

## 5.0 Consensus
`//todo: define consensus round process and validation, and validated request set application to current state`

GENERAL TODO
============


`//todo: define config file format including peers and cUNL`

`//todo: define keyfile format`

`//todo: complete nodejs interface including creating a contract instance, creating a client instance, get, put and call functions`

`//todo: complete a section on read-only vs state modifying requests and sync vs async interfaces`

`//todo: complete a section on interface discovery`

`//todo: complete a section on instance discovery for a given contract (DNS TXT records)`

`//todo: complete reference implementation and example contracts`

`//todo: provide example requests, responses on RPC, and examples of all messages on IIC`


