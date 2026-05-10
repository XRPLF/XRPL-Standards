<pre>
  xls: 69
  title: Simulating Transaction Execution
  description: A new API method for executing dry runs of transactions without submitting them to the network
  author: Mayukha Vadari <mvadari@ripple.com>, Elliot Lee (@intelliot)
  proposal-from: https://github.com/XRPLF/XRPL-Standards/discussions/199
  status: Final
  category: System
  created: 2024-03-22
</pre>

# Simulating Transaction Execution

## Abstract

The XRPL protocol supports numerous different transaction types, with more being added over time. Many transactions are complex and can have numerous modes, flags, and parameters. Some combinations of these can lead to unpredictable results, especially since transactions frequently behave differently depending on the current state of the ledger. This is particularly paramount for high-value transactions, as it is crucial to understand the likely outcome of the transaction and ensure that its effects align with expectations.

This spec proposes a new API method named `simulate`, which executes a [dry run](<https://en.wikipedia.org/wiki/Dry_run_(testing)>) of a transaction submission. Unlike the existing `submit` function, `simulate` never submits the transaction to the network. This allows users to test transactions and preview their results (including metadata) without committing them to the XRP Ledger.

The `simulate` API method offers an efficient way to safely experiment with transactions on any ledger, such as the Mainnet ledger. Unlike using test networks, which can require faithfully replicating an entire scenario for experimentation, `simulate` allows users to "apply" transactions to a Mainnet (or other) ledger without actually submitting the transaction to be applied permanently. This allows developers and users to test and refine their transactions with confidence before committing them for real.

## 1. Overview

This spec proposes a new RPC method called `simulate`.

This method has no effect on consensus or transaction processing. Therefore, this feature will not require an [amendment](https://xrpl.org/docs/concepts/networks-and-servers/amendments/).

## 2. RPC: `simulate`

The `simulate` method applies a transaction (and returns the result and metadata for review), but will never send it to the network to be confirmed or included in future ledgers. It can be thought of as a dry-run of the `submit` method. This method can be used to preview the potential results and effects (via the metadata) of a potential transaction, without actually sending it to the wider network.

### 2.1. Request Fields

| Field Name | JSON Type | Description                                                                                                                                                                                                                                |
| ---------- | --------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `tx_blob`  | `string`  | The transaction to simulate, in [binary format](https://xrpl.org/docs/references/protocol/binary-format/).                                                                                                                                 |
| `tx_json`  | `object`  | The transaction to simulate, in JSON format.                                                                                                                                                                                               |
| `binary`   | `boolean` | If `true`, return transaction data and metadata as binary [serialized](https://xrpl.org/docs/references/protocol/binary-format/) to hexadecimal strings. If `false`, return transaction data and metadata as JSON. The default is `false`. |

A valid request must have exactly one of `tx_blob` or `tx_json` included. The transaction **must** be unsigned. Public keys (`SigningPubKey`), if included, will be verified.

If the `Fee` field is omitted (not set) in the transaction, then the server will [automatically fill in](https://xrpl.org/docs/references/protocol/transactions/common-fields/#auto-fillable-fields) a value. The calculated `Fee` value will be present in the response. The same is true of the `Sequence` and `SigningPubKey` fields.

### 2.2. Response Fields

The shape of the return object is very similar to the [response of the `tx` method](https://xrpl.org/docs/references/http-websocket-apis/public-api-methods/transaction-methods/tx#response-format).

| Field Name     | Always Present?         | JSON Type | Description                                                                                                                                                                                                                          |
| -------------- | ----------------------- | --------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `tx_json`      | If `binary` was `false` | `object`  | The transaction that was simulated, including auto-filled values. Included if `binary` was `false`.                                                                                                                                  |
| `tx_blob`      | If `binary` was `true`  | `string`  | The serialized transaction that was simulated, including auto-filled values. Included if `binary` was `true`.                                                                                                                        |
| `ledger_index` | ✔️                      | `number`  | The ledger index of the ledger that includes this transaction.                                                                                                                                                                       |
| `meta`         | If `binary` was `false` | `object`  | Transaction metadata, which describes the results of the transaction. Not included if the transaction fails with a code that means it wouldn’t be included in the ledger (such as a non-TEC code). Included if `binary` was `false`. |
| `meta_blob`    | If `binary` was `true`  | `string`  | Transaction metadata, which describes the results of the transaction. Not included if the transaction fails with a code that means it wouldn’t be included in the ledger (such as a non-TEC code). Included if `binary` was `true`.  |

### 2.3. Error Cases

The RPC will error (i.e. not return a response in the shape described above) if:

- Both (or neither) `tx_json` and `tx_blob` are included in the request.
- Any of the fields are of an incorrect type.
- The transaction is signed.

## 3. Security

The transaction will not actually be submitted. Users and tooling will have to be careful to be using the right RPC when they want to submit vs. not submit.

Since the simulated transaction must be unsigned, a malicious `rippled` node cannot submit a transaction that a user only wanted to simulate, not submit.

However, a malicious `rippled` node could still lie about what your transaction does, or front-run your transaction.

Performance tests will need to be conducted in order to ensure that a malicious user cannot DoS a `rippled` node by calling this function too many times, especially when pertaining to a complex transaction that affects many ledger objects. If it is too taxing on a node, it may be implemented as an admin-only method.

## 4. Example

### 4.1. Payment

#### 4.1.1. Request

```
{
  "id": 2,
  "command": "simulate",
  "tx_json" : {
      "TransactionType" : "Payment",
      "Account" : "rf1BiGeXwwQoi8Z2ueFYTEXSwuJYfV2Jpn",
      "Destination" : "ra5nK24KXen9AHvsdFTKHSANinZseWnPcX",
      "Amount" : {
         "currency" : "USD",
         "value" : "1",
         "issuer" : "rf1BiGeXwwQoi8Z2ueFYTEXSwuJYfV2Jpn"
      }
   }
}
```

#### 4.1.2. Response

```
{
  "id": 2,
  "result": {
    "applied": false,
    "engine_result": "tesSUCCESS",
    "engine_result_code": 0,
    "engine_result_message": "The simulated transaction would have been applied.",
    "ledger_index": 3,
    "meta": {
      "AffectedNodes": [
        {
          "ModifiedNode": {
            "FinalFields": {
              "Account": "rf1BiGeXwwQoi8Z2ueFYTEXSwuJYfV2Jpn",
              "AccountTxnID": "4D5D90890F8D49519E4151938601EF3D0B30B16CD6A519D9C99102C9FA77F7E0",
              "Balance": "75159663",
              "Flags": 9043968,
              "OwnerCount": 5,
              "Sequence": 361,
              "TransferRate": 1004999999
            },
            "LedgerEntryType": "AccountRoot",
            "LedgerIndex": "13F1A95D7AAB7108D5CE7EEAF504B2894B8C674E6D68499076441C4837282BF8",
            "PreviousFields": {
              "AccountTxnID": "2B44EBE00728D04658E597A85EC4F71D20503B31ABBF556764AD8F7A80BA72F6",
              "Balance": "75169663",
              "Sequence": 360
            },
            "PreviousTxnID": "2B44EBE00728D04658E597A85EC4F71D20503B31ABBF556764AD8F7A80BA72F6",
            "PreviousTxnLgrSeq": 18555460
          }
        },
        {
          "ModifiedNode": {
            "FinalFields": {
              "Balance": {
                "currency": "USD",
                "issuer": "rrrrrrrrrrrrrrrrrrrrBZbvji",
                "value": "12.0301"
              },
              "Flags": 65536,
              "HighLimit": {
                "currency": "USD",
                "issuer": "rf1BiGeXwwQoi8Z2ueFYTEXSwuJYfV2Jpn",
                "value": "0"
              },
              "HighNode": "0",
              "LowLimit": {
                "currency": "USD",
                "issuer": "ra5nK24KXen9AHvsdFTKHSANinZseWnPcX",
                "value": "100"
              },
              "LowNode": "0"
            },
            "LedgerEntryType": "RippleState",
            "LedgerIndex": "96D2F43BA7AE7193EC59E5E7DDB26A9D786AB1F7C580E030E7D2FF5233DA01E9",
            "PreviousFields": {
              "Balance": {
                "currency": "USD",
                "issuer": "rrrrrrrrrrrrrrrrrrrrBZbvji",
                "value": "11.0301"
              }
            },
            "PreviousTxnID": "7FFE02667225DFE39594663DEDC823FAF188AC5F036A9C2CA3259FB5379C82B4",
            "PreviousTxnLgrSeq": 9787698
          }
        }
      ],
      "TransactionIndex": 0,
      "TransactionResult": "tesSUCCESS",
      "delivered_amount": {
        "currency": "USD",
        "issuer": "rf1BiGeXwwQoi8Z2ueFYTEXSwuJYfV2Jpn",
        "value": "1"
      }
    },
    "tx_json": {
      "Account": "rf1BiGeXwwQoi8Z2ueFYTEXSwuJYfV2Jpn",
      "DeliverMax": {
        "currency": "USD",
        "issuer": "rf1BiGeXwwQoi8Z2ueFYTEXSwuJYfV2Jpn",
        "value": "1"
      },
      "Destination": "ra5nK24KXen9AHvsdFTKHSANinZseWnPcX",
      "Fee": "10",
      "Sequence": 360,
      "TransactionType": "Payment"
    }
  },
  "status": "success",
  "type": "response"
}
```

# Appendix

## Appendix A: FAQ

### A.1: Will calling this method incur any fees?

No, because the transaction is not actually submitted to the consensus ledger and isn’t shared (broadcast) with other nodes.

### A.2: Is the `simulate` API call guaranteed to be the same as when I actually submit the transaction?

No, because the ledger state, which affects how a transaction is processed, may change between the two API calls.

### A.3: Can anyone run this function on any `rippled` node?

If the node is configured to provide public API access, yes. The load is similar to that of the `submit` method. If performance tests reveal that the function takes too much of a node’s resources even with [rate limits](https://xrpl.org/docs/references/http-websocket-apis/api-conventions/rate-limiting/), then it may be an admin-only method, which means that you would need administrator access to a node, or need to run your own node, to call this function.

### A.4: What types of transactions can be simulated?

All transaction types can be simulated. You can use it to ensure that your transaction is correctly formatted and has the right settings, or to determine the outcome of large or complex transactions, or something else entirely.

### A.5: Can I use this method for debugging transactions?

Absolutely! The simulate function is a valuable tool for debugging and troubleshooting transactions before they are submitted to the network. You can test different scenarios and identify potential issues before committing the actual transaction.

### A.6: Can I use this method to test transactions sent by accounts that I don’t control (such as a customer’s account)?

Yes, since the simulated transaction does not need to be signed.

### A.7: Why is this API useful if I can just replicate the scenario in a testnet?

If you're trying to run a complex transaction, or just a DEX transaction, it can be difficult to replicate the entire system in a testnet. There may also be factors and edgecases that your transaction will run into that you simply don't think about replicating in your testnet recreation.

### A.8: Why isn’t this function instead called [insert alternative here]?

Several other names were considered during the ideation process, such as `submit_dry_run`, `dry_run`, or `preview`, or even just including a `dry_run: true` parameter in the submit method. We decided against having the word `“submit”` anywhere in the name of the method to avoid confusion from people thinking that the method actually submits a transaction, and the name `"simulate"` has some precedent in being used by other systems and APIs.

### A.9: Will `NetworkID` also be autofilled?

No, because it's useful to ensure that users are running their transactions on the correct network.

## Appendix B: Example Use Cases

This is not intended to be an exhaustive list.

- Test high-value transactions to ensure they’ll execute as expected before actually submitting them.
- Run tests or experiments on Mainnet data without needing to recreate it all in a test network environment or needing to sync a node to spin up a new testnet environment with the data.
- Debug and troubleshoot transactions when they don’t execute as expected.
- Experiment with different features of the XRPL with real-world data without needing to spend any money.
- In user interfaces, provide users with a preview of what a transaction (e.g. `Payment`, `OfferCreate`, ...) can be expected to do.
- Get the current price of an AMM ([related issue](https://github.com/XRPLF/rippled/issues/5007)).

## Appendix C: Proposed Implementation

A proposed implementation is available here: https://github.com/XRPLF/rippled/pull/5069

As of 2024-10-17, the implementation is complete but awaiting code review approvals. You can build the PR branch, run `rippled`, [sync to the network of your choice](https://xrpl.org/docs/infrastructure/configuration/connect-your-rippled-to-the-xrp-test-net#connect-your-rippled-to-a-parallel-network) (e.g. Mainnet), and start using `simulate` today.
