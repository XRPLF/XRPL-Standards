
XLS1d Contract Standard
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
* `URQ` — unordered request queue

## 1.2 Purpose
The purpose of this document is to define a standard by which codius `contracts` may be established on `nodes`, and by which the `instances` of these contracts may communicate with their `peers`, reach consensus, and make forward progress, and by which clients may interact with the contract by making requests and receiving responses.

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
Each instance listens on at least one port: a private `IIC` port and optionally a public `RPC` port. The private port must accept IIC messages. The public port, if open, must accept incoming requests from clients.

## 2.1 Public Port
The instance may choose to have a public port. This must be an TLS websocket and must accept JSON RPC 2.0 calls known as `requests`. Each request is interpreted as an attempt to call a function in the `FSM`. These requests may be throttled or discarded according to resource constraints. The instance which received the request has the sole responsibility to furnish to the client a `response`.

## 2.2 Private Port
Each instance must have a private port on which it emits and receives `IIC` messages from `cUNL` `peers`.

## 3.0 Inter-Instance Communication
`IIC` consists of notification messages including at least:
### 3.1 `request` message
A relayed client request that was made to another instance.
```
{
	"type": "request",
	"payload": /* client request verbatim */,
	"timestamp": /* micro unixtime UTC+0 */,
	"signature": /* peer signature of payload with appended timestamp  */,
	"pubkey": /* signing key, should be from cUNL */
}
```

### 3.2 `proposal` message
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
`//todo: define request hashes `
### 3.3 `validation` message
An announcement that a particular proposal was applied to the FSM, and the next round has begun.
Identical to proposal message but type is `validation`.

### 3.4 `copy` message
A request for a state transfer of part or all of the state merkle tree.
`//todo: finish when KVS options are reviewed`

GENERAL TODO
============

`//todo: define persistent contract state`

`//todo: define consensus round process and validation, and validated request set application to current state`

`//todo: define config file format including peers and cUNL`

`//todo: define keyfile format`

`//todo: complete nodejs interface including creating a contract instance, creating a client instance, get, put and call functions`

`//todo: complete a section on read-only vs state modifying requests and sync vs async interfaces`

`//todo: complete a section on interface discovery`

`//todo: complete a section on instance discovery for a given contract (DNS TXT records)`

`//todo: complete reference implementation and example contracts`

`//todo: provide example requests, responses on RPC, and examples of all messages on IIC`

