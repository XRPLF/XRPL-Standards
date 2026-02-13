<pre>
  xls: 15
  title: Concise Transaction Identifier
  description: Introduces concise transaction identifier
  author: RichardAH (@RichardAH)
  created: 2021-03-09
  proposal-from: https://github.com/XRPLF/XRPL-Standards/discussions/34
  status: Withdrawn
  withdrawal-reason: Superseded by XLS-37
  category: System
</pre>

## Change Log

This standard was amended on 25th March 2021:

### XLS15.1

- Add an optional 7 bit `control byte` to the most significant byte position.
- `Control byte` may be absent in which case assumed to be 0x00 for backwards compatibility.
- Credit for these changes to @nbougalis

### Current Identifiers

Transactions in the XRPL ecosystem are identified using the namespace-biased SHA512-half of their canonical byte-wise serialisation [[1]](https://xrpl.org/basic-data-types.html#hashes) whether or not the transaction has been submitted to consensus.

Ledgers are also identified by hashes. [[2]](https://xrpl.org/basic-data-types.html#ledger-index) However provided there is a human consensus about validation (sufficient UNL overlap) ledgers may instead be identified by their 4 byte sequence number. [[3]](https://xrpl.org/basic-data-types.html#ledger-index)

Transactions are recorded in the protocol-defined canonical order within each ledger. [[4]](https://xrpl.org/basic-data-types.html#ledger-index) This ordering means each transaction has a sequence number within the ledger. This offset is present in the transaction metadata as `TransactionIndex`.[[5]](https://xrpl.org/transaction-metadata.html)

It may be useful in a range of applications to be able to uniquely identify a transaction by the point at which it was validated rather than by its explicit contents. Thus for an unvalidated (unsubmitted or locally rejected) transaction this type of identifier would not apply.

### New Identifier: Concise Transaction Identifier

At time of the publication we assume for the foreseeable future that there will not be more than 65535 transactions in a given ledger. Therefore we can uniquely identify a txn within a ledger with a 2 byte integer, and we can uniquely identify the ledger by its 4 byte sequence number. Thus a 6 byte number uniquely identifies a validated transaction.

To prevent transcription errors (and to provide some validation for the contents) the first hex nibble of the ledger's canonical hash and the first hex nibble of the transaction's canonical hash are included in byte position 0, bringing the total number of bytes to 7. This is referred to a the checksum byte.

To future-proof this format an additional, optional, 7 bit control byte **may** be prepended to these 7 bytes. If this control byte is absent then it is assumed to be 0x00 which is referred to as the _simple case_. This is a change introduced in XLS15.1, and is strictly backwards compatible with existing CTIs.

The control byte (if set) allows the CTI to identify a transaction in:

- A different network (other than XRPL mainnet)
- With a double-wide `TransactionIndex`
- With a double-wide `LedgerSequence`
- Or any combination of these

In the simple case the CTI fits neatly and unambiguously in a positive signed 64 bit integer. In the advanced case, depending on which options are selected a big number may be required to store and process the CTI.

### CTI Format — Simple Case

_Must be handled by all implementations._
| Byte/s | Field |
|--------|--------------------------------------------------------------------------|
| 0 | `<first four bits of ledger hash> <first four bits of transaction hash>` |
| 1-3 | `<16 bit TransactionIndex>` |
| 3-7 | `<32 bit LedgerSequence>` |

### CTI Format — Advanced Case

_Required for implementations that need to handle non-mainnet transactions or for "fully future-proofed implementations", otherwise optional._
| Byte/s | Field |
|--------|-----------------------------------------------------------------------------------------------------------|
| 0 | `<reserved 00> <T double-wide txn bit> <L double-wide lgr bit> <four bits of network id>` |
| 1 | `<first four bits of ledger hash> <first four bits of transaction hash>` |

- Byte 0 is the control byte and may be absent which gracefully degrades into the `simple case` above.
- Most significant bit of the control byte is always 0 such that most CTIs can be encoded as a positively signed int64.
- The next most significant bit is reserved for future use and must also be zero.
- The `T double-wide txn bit`, when `1`, doubles the size of the `TransactionIndex` field.
- The `L double-wide lgr bit`, when `1`, doubles the size of the `LedgerSequence` field.
- Network ID is an unsigned 4 bit integer corresponding to a network identified in the range 0-15. A table of assigned values appears below.

Taken together the two double-wide bits inform the parsing application how to proceed:

Case 1: Normal Field Sizes `TL = 00`
| Byte/s | Field |
|--------|-----------------------------------------------------------------------------------------------------------|
| 2-4 | `<16 bit TransactionIndex>` |
| 4-8 | `<32 bit LedgerSequence>` |

Case 2: Double wide LedgerSequence `TL = 01`
| Byte/s | Field |
|--------|-----------------------------------------------------------------------------------------------------------|
| 2-4 | `<16 bit TransactionIndex>` |
| 4-12 | `<64 bit LedgerSequence>` |

Case 3: Double-wide TransactionIndex `TL = 10`
| Byte/s | Field |
|--------|-----------------------------------------------------------------------------------------------------------|
| 2-6 | `<32 bit TransactionIndex>` |
| 6-10 | `<32 bit LedgerSequence>` |

Case 4: Double-wide TransactionIndex and LedgerSequence `TL = 11`
| Byte/s | Field |
|--------|-----------------------------------------------------------------------------------------------------------|
| 2-6 | `<32 bit TransactionIndex>` |
| 6-14 | `<64 bit LedgerSequence>` |

### Network IDs

| Number | Network                        |
| ------ | ------------------------------ |
| 0      | XRPL mainnet                   |
| 1      | XRPL testnet                   |
| 2      | XRPL devnet                    |
| 3      | XRPL-Labs Public Hooks Testnet |
| 4..15  | Reserved for future use        |

### Canonical Presentation

To prevent copy-paste errors and non-canonical CTIs, presentation of CTIs to end users must be in decimal _without leading zeros_. The only allowable characters in a presented CTI are `[0-9]`.

In the case of an advanced CTI the smallest possible way to describe the transaction is always the Canonical CTI. Thus if `double-wide` bits are set but the high bytes of those fields are `0x00` then this is a non-canonical and therefore an invalid CTI. Any implementation that handles `advanced case` CTIs must identify this.

### Examples—Simple Case

This randomly selected transaction: [1C0FA22BBF5D0A8A7A105EB7D0AD7A2532863AA48584493D4BC45741AEDC4826](https://livenet.xrpl.org/transactions/1C0FA22BBF5D0A8A7A105EB7D0AD7A2532863AA48584493D4BC45741AEDC4826/raw)

- Has a transaction index of 25
- Resides in ledger 62084722
- The transaction hash's first nibble is `1`
- The ledger hash's first nibble is `F`
  Thus this transaction in CTI format encodes to
- CTI: `67835576823535218`
- Hex: `F1001903B35672`
- URI: `xrpl://cti/67835576823535218`

Another randomly selected transaction [AE1C4AD620251CA97C320052A5B9755CD002B5FBDBECC9A49F088FD58B71A44E](https://livenet.xrpl.org/transactions/AE1C4AD620251CA97C320052A5B9755CD002B5FBDBECC9A49F088FD58B71A44E)

- Has a transaction index of 9
- Resides in ledger 62090589
- CTI: `43347185130237277`
  You can resolve these CTIs right now: [cti-resolver](https://richardah.github.io/cti-resolver/index.html)

### CTI Reference Implementations—Simple Case

In C:

```C
int64_t
cti_encode(
        uint8_t* txn_hash,
        uint16_t txn_index,
        uint8_t* ledger_hash,
        uint32_t ledger_index)
{
    uint64_t cti = (((ledger_hash[0]>>4U) & 0xFU)<<4U) + ((txn_hash[0]>>4U) & 0xFU); // these are the 8 check bits
    cti <<= 16; // shift left 2 bytes to make space for the transaction index
    cti += txn_index;
    cti <<= 32; // shift left 4 bytes to make space for the ledger sequence number
    cti += ledger_index;
    return (int64_t)cti;
}

uint8_t
cti_is_simple(
        int64_t cti)
{
    return (cti >>56U) == 0;
}

uint16_t
cti_transaction_index(
        int64_t cti)
{
    return (cti >> 32U) & 0xFFFFU;
}

uint32_t
cti_ledger_index(
        int64_t cti)
{
    return (cti & 0xFFFFFFFFUL);
}

uint8_t
cti_ledger_check(
        int64_t cti)
{
    return (cti >> 52) & 0xFU;
}

uint8_t
cti_transaction_check(
        int64_t cti)
{
    return (cti >> 48) & 0xFU;
}
```

In JS:

```js
function cti_encode(
  txn_hash /* hex string */,
  txn_index,
  ledger_hash /* hex string */,
  ledger_index,
) {
  let ledger_check = BigInt(parseInt(ledger_hash.slice(0, 1), 16));
  let txn_check = BigInt(parseInt(txn_hash.slice(0, 1), 16));
  let cti = (ledger_check << 4n) + txn_check;
  cti <<= 16n;
  cti += BigInt(txn_index);
  cti <<= 32n;
  cti += BigInt(ledger_index);
  return cti;
}

function cti_is_simple(cti) {
  return cti >> 56n == 0;
}

function cti_transaction_index(cti) {
  return (cti >> 32n) & 0xffffn;
}

function cti_ledger_index(cti) {
  return cti & 0xffffffffn;
}

function cti_ledger_check(cti) {
  return (cti >> 52n) & 0xfn;
}

function cti_transaction_check(cti) {
  return (cti >> 48n) & 0xfn;
}
```

RH Note: Advanced case (XLS15.1) examples and reference implementations to be added shortly
