# Quickstart 
## Improved Concise Transaction Identifier (CTID) 

CTIDs are composed of 16 hex nibbles, and begin with a `C`.

```
CXXXXXXXYYYYZZZZ
```

The identifier is divided into three fields.

Char Offset | Field | Size (bits) |Explanation
-|-----|------|---------
0 | C| 4 | Lead-in (ignore)
1-7 | XXXXXXX | 28 |  Ledger Sequence
8-11 | YYYY | 16 | Transaction index (offset) within that ledger
12-16 | ZZZZ | 16 | Network ID.

Reference implementations are available for several languages. Click below to dive in.

Language | Implementation
-|-
Javascript | [ctid.js](https://github.com/XRPLF/ctid/blob/main/ctid.js)
Typescript | [ctid.ts](https://github.com/XRPLF/ctid/blob/main/ctid.ts)
C++ | [ctid.cpp](https://github.com/XRPLF/ctid/blob/main/ctid.cpp)
Python 3| [ctid.py](https://github.com/XRPLF/ctid/blob/main/ctid.py)
PHP 5|[ctid.php](https://github.com/XRPLF/ctid/blob/main/ctid.php)


### Function prototypes (pseudocode)
In this repo there are several reference implementations available for various languages but they all use the same function model.
```js
function encodeCTID (
  ledger_seq : number,
  txn_index  : number,
  network_id : number) -> string;
```
```js
function decodeCTID (ctid : string or number) -> { 
  ledger_seq : number,
  txn_index  : number,
  network_id : number };
```

### Mainnet example
[This transaction](https://livenet.xrpl.org/transactions/D42BE7DF63B4C12E5B56B4EFAD8CBB096171399D93353A8A61F61066160DFE5E/raw) encodes in the following way:
```js
encodeCTID(
  77727448, // ledger sequence number the txn appeared in
  54,       // `TransactionIndex` as per metadata
  0)        // Network ID of mainnet is 0
'C4A206D800360000'
```

### Hooks testnet v3 example
[This transaction](https://hooks-testnet-v3-explorer.xrpl-labs.com/tx/C4E284010276F8457C4BF96D0C534B7383087680C159F9B8C18D5EE876F7EFE7) encodes in the following way:
```js
encodeCTID(
  428986, // ledger sequence number the txn appeared in
  0,      // `TransactionIndex` as per metadata
  21338)  // Network ID of hooks v3 is 21338
'C0068BBA0000535A'
```
