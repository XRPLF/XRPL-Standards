<pre>
  xls: 37
  title: Concise Transaction Identifier (CTID)
  description: A way to locate validated transactions using ledger sequence number, transaction index, and network ID rather than transaction hash
  author: Richard Holland (@RichardAH), Ryan Molley (@interc0der)
  proposal-from: https://github.com/XRPLF/XRPL-Standards/discussions/91
  status: Final
  category: System
  created: 2023-02-12
</pre>

> This proposal replaces the original proposal for Concise Transaction Identifiers XLS-15

# Quickstart

If you are a developer and want to get started quickly with integrating CTID, please visit [the quickstart](./QUICKSTART.md).

# Abstract

This standard provides a way to locate a _validated_ transaction on any XRP Ledger Protocol Chain using its ledger sequence number, transaction index, and network ID rather than its transaction hash.

This identifier is only applicable for validated transactions. Non-validated or unsubmitted transactions cannot be identified using a CTID.

# Specification

### Format

CTIDs are composed of 16 uppercase hex nibbles, and always begin with a `C`.
The identifier is divided into three fields and a single _lead-in_ nibble:

```
C [ XXXXXXX ] [ YYYY ] [ ZZZZ ]
```

### Fields

| Character Offset | Field   | Size (bits) | Description                    |
| ---------------- | ------- | ----------- | ------------------------------ |
| 0                | C       | 4           | Lead-in                        |
| 1-7              | XXXXXXX | 28          | Ledger Index / Sequence Number |
| 8-11             | YYYY    | 16          | Transaction Index              |
| 12-15            | ZZZZ    | 16          | Network ID                     |

# 1. Background

### 1.1 Existing Transaction Identifiers

The XRP Ledger historically identifies ledgers and transactions (and other objects) using a namespace-biased 'SHA-512Half' hashing function, which results in a 64 hex nibble unique identifier.[[1]](https://xrpl.org/basic-data-types.html#hashes)

Since these hashes are derived from the contents of the data, each identifier is completely independent of consensus.

Example Transaction Hash (ID):

> C4E284010276F8457C4BF96D0C534B7383087680C159F9B8C18D5EE876F7EFE7

### 1.2 An Alternative: Indexing

Ledgers and transactions can be identified by their sequenced position.

As new ledgers are validated on XRP Ledger Protocol Chains, they are assigned a sequence number, which is always the previous ledger sequence plus one. The first ledger sequence is the genesis ledger with a value of one.

Ledgers can therefore be uniquely identified by a `ledger_index` (sequence). [[2]](https://xrpl.org/basic-data-types.html#ledger-index) [[3]](https://xrpl.org/ledger-header.html) The only limitation is that the ledger needs to be closed before a sequence number can be used for identification.

Example Ledger Hash:

> F8A87917637D476E871D22A1376D7C129DAC9E25D45AD4B67D1E75EA4418654C

Example Ledger Index:

> 62084722

During consensus, all nodes on an XRP Ledger Chain will agree on the order of transactions within a given ledger. This unique sequence of transactions is referred to as the canonical order. [[4]](https://xrpl.org/consensus.html) This means that transactions, like ledgers, can also be identified by their index. This index is present in the transaction metadata as `TransactionIndex`.[[5]](https://xrpl.org/transaction-metadata.html)

Example:

```json
...
    "TransactionIndex":7
    "TransactionResult":"tesSUCCESS"
  }
"hash":"53726E6D021522A97602004841A2A7477D1900BD348ADA4D4DF812B466E56454"
"ledger_index":62084722
"date":1615278490000
}
```

### 1.3 Motivation

The XRP Ledger can support an ecosystem of cooperatively interconnected XRPL Protocol Chains. Users of these chains need to efficiently locate specific transactions on specific chains.

The CTID is a network-aware transaction identifier which improves the user experience for sidechains. It provides a way to efficiently locate a specific transaction without relying on transaction hashes, which can be difficult to find in a multi-chain environment.

CTIDs allow users to quickly and easily identify their transactions on a particular chain using the ledger sequence number, transaction index, and network ID. Users can thus identify their transactions and confirm their successful completion. Additionally, CTIDs require less storage space than transaction hashes, which can be beneficial for databases containing millions of transactions.

# 2. Considerations

### 2.1 Bit Allocations

To future-proof CTID identifiers, the parameters and their sizes and lifespans are considered:

| Field             | Size (bits) | Limit (decimal) | Lifespan                                                     | Explanation                                                                                                                                                                                                  |
| ----------------- | ----------- | --------------- | ------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Ledger Index      | 28          | 268,435,455     | 34 years from genesis                                        | This field would otherwise be 32 bits but for the C lead-in nibble. We feel the easily identified C is more useful than an extremely long lifespan.                                                          |
| Transaction Index | 16          | 65,535          | ∞ / until there are more than 65,535 transactions per ledger | It is very unlikely there will be more than 65535 transactions per ledger in any XRPL Protocol Chain for a long time. If there are then those above this limit still exist but cannot be identified as CTID. |
| Network ID        | 16          | 65,535          | ∞ / until there are more than 65535 ports allowed in TCP     | In XRPL Protocol Chains the Network ID should match the chosen peer port. Thus the natural limitation on Network ID is that of the TCP port (65536).                                                         |

### 2.2 Extensible

A leading `C` provides easy human identification of the format, but also room for growth. If the number of closed ledgers on a particular chain exceeds 268,435,455, the leading `C` may be incremented to `D`, `E` and `F` allowing for an additional 100 years of use. It is not expected this will be necessary as another standard will likely replace it by this time. As of 2023, all CTIDs always start with a `C` and this will almost certainly be the case for at least the next 20 years.

### 2.3 Space Reduction and Savings

Improved Concise Transaction Identifiers use a quarter of the space when compared to transaction hashes. This can save considerable space in databases containing references to millions of transactions.

# 3. Specification

This section is enclosed in the header of the proposal.

# 4. Implementations

Diverse implementations (in multiple languages) with test cases and explanations are available at [the quickstart repo](<[https://github.com/xrplf/ctid](https://github.com/xrplf/ctid)>).

Two different implementations for the Improved Concise Transaction Identifier (CTID) are presented in this XLS.

- Simple
- Advanced

The first is a simplified method which is intended for easier self-implementation and adoption. The second is a more robust version with type checking and error handling.

### 4.1 Simple

An example encoding routine in javascript follows:

```
const encodeCTID = (lgrIndex, txnIndex, networkId) => {
  return (
    ((BigInt(0xc0000000) + BigInt(lgrIndex)) << 32n) +
    (BigInt(txnIndex) << 16n) +
    BigInt(networkId)
  )
    .toString(16)
    .toUpperCase();
};

const decodeCTID = (ctid) => {
  if (typeof ctid == 'string') ctid = BigInt('0x' + ctid);
  return {
    lgrIndex: (ctid >> 32n) & ~0xc0000000n,
    txnIndex: (ctid >> 16n) & 0xffffn,
    networkId: ctid & 0xffffn,
  };
};

```

### 4.2 Advanced

See [here](https://github.com/standardconnect/xls-37d) for the source code.

Reference documentation is available [here](https://standardconnect.github.io/xls-37d/).

### 4.2.1 Getting Started

In an existing project (with package.json), install xls-37d with:

```
npm install xls-37d
```

or with yarn:

```
yarn add xls-37d
```

### 4.2.2 Encoding

An example encoding routine in typescript follows:

```tsx
import xls37d from "xls-37d";

const { ctid } = new xls37d.encode({
  networkId,
  lgrIndex,
  txnIndex,
});
```

### 4.2.3 Decoding

An example decoding routine in typescript follows:

```tsx
import xls37d from "xls-37d";

const { networkId, lgrIndex, txnIndex } = new xls37d.decode(ctid);
```

# References

[1] [https://xrpl.org/basic-data-types.html#hashes](https://xrpl.org/basic-data-types.html#hashes)

[2] [https://xrpl.org/basic-data-types.html#ledger-index](https://xrpl.org/basic-data-types.html#ledger-index)

[3] [https://xrpl.org/ledger-header.html](https://xrpl.org/ledger-header.html)

[4] [https://xrpl.org/consensus.html](https://xrpl.org/consensus.html)

[5] [https://xrpl.org/transaction-metadata.html](https://xrpl.org/transaction-metadata.html)
