<pre>
  xls: 56
  title: Atomic/Batch Transactions
  description: A design to allow multiple transactions to be packaged together and executed as a single atomic unit
  author: Mayukha Vadari <mvadari@ripple.com>
  proposal-from: https://github.com/XRPLF/XRPL-Standards/discussions/162
  status: Final
  category: Amendment
  created: 2023-12-13
  updated: 2026-02-10
</pre>

# Atomic/Batch Transactions

## Abstract

The XRP Ledger has a robust set of built-in features, enabling fast and efficient transactions without the need for complex smart contracts on every step. However, a key limitation exists: multiple transactions cannot be executed atomically. This means that if a complex operation requires several transactions, a failure in one can leave the system in an incomplete or unexpected state. Imagine building a house: you wouldn't want to lay the foundation and build the walls, and then discover you can't afford the roof, leaving you with an unfinished and unusable structure.

This document proposes a design to allow multiple transactions to be packaged together and executed as a single unit. It's like laying the foundation, building the walls, and raising the roof all in one single secure step, leveraging the existing strengths of the XRP Ledger. If you're unable to afford the roof, you won't even bother laying the foundation.

This eliminates the risk of partial completion and unexpected outcomes, fostering a more reliable and predictable user experience for complex operations. By introducing these batch transactions, developers gain the ability to design innovative features and applications that were previously hindered by the lack of native smart contracts for conditional workflows. This empowers them to harness the full potential of the XRP Ledger's built-in features while ensuring robust execution of complex processes.

Some use-cases that may be enabled by batch transactions include (but are certainly not limited to):

- All or nothing: Mint an NFT and create an offer for it in one transaction. If the offer creation fails, the NFT mint is reverted as well.
- Trying out a few offers: Submit multiple offers with different amounts of slippage, but only one will succeed.
- Platform fees: Package platform fees within the transaction itself, simplifying the process.
- Trustless swaps (multi-account): Trustless token/NFT swaps between multiple accounts.
- Flash loans: Borrowing funds, using them, and returning them all in the same transaction.
- Withdrawing accounts (multi-account): Attempt a withdrawal from your checking account, and if that fails, withdraw from your savings account instead.

## 1. Overview

This spec adds one new transaction: `Batch`. It also adds an addition to the common fields of all transactions. It will not require any new ledger objects, nor modifications to existing ledger objects. It will require an amendment, tentatively titled `featureBatch`.

The rough idea of this design is that users can include "sub-transactions" inside `Batch`, and these transactions are processed atomically. The design also supports transactions from different accounts in the same `Batch` wrapper transaction.

### 1.1. Terminology

- **Inner transaction**: the sub-transactions included in the `Batch` transaction, that are executed atomically.
- **Outer transaction**: the wrapper `Batch` transaction itself.
- **Batch mode** or **mode**: the "mode" of batch processing that the transaction uses. See section 2.2 for more details.

## 2. Transaction: `Batch`

### 2.1. Fields

| Field Name        | Required? | JSON Type | Internal Type | Description                                                                                                                        |
| ----------------- | --------- | --------- | ------------- | ---------------------------------------------------------------------------------------------------------------------------------- |
| `Flags`           | ✔️        | `number`  | `UInt32`      | A bit-map of boolean flags enabled for this transaction. These flags represent the batch mode of the transaction.                  |
| `RawTransactions` | ✔️        | `array`   | `STArray`     | The list of inner transactions that will be applied. (Minimum 2, Maximum 8)                                                        |
| `BatchSigners`    |           | `array`   | `STArray`     | An array of objects that represent signatures for a multi-account Batch transaction, signifying authorization of this transaction. |

#### 2.1.1. `Flags`

The `Flags` field represents the **batch mode** of the transaction. Exactly one must be specified in a `Batch` transaction.

This spec supports four modes:

- `ALLORNOTHING` or `tfAllOrNothing` (with a value of `0x00010000`)
- `ONLYONE` or `tfOnlyOne` (with a value of `0x00020000`)
- `UNTILFAILURE` or `tfUntilFailure` (with a value of `0x00040000`)
- `INDEPENDENT` or `tfIndependent` (with a value of `0x00080000`)

A transaction will be considered a failure if it receives any result that is not `tesSUCCESS`.

##### 2.1.1.1. `ALLORNOTHING`

All or nothing. All transactions must succeed for any of them to succeed.

##### 2.1.1.2. `ONLYONE`

The first transaction to succeed will be the only one to succeed; all other transactions either failed or were never tried.

While this can sort of be done by submitting multiple transactions with the same sequence number, there is no guarantee that the transactions are processed in the same order they are sent.

##### 2.1.1.3. `UNTILFAILURE`

All transactions will be applied until the first failure, and all transactions after the first failure will not be applied.

##### 2.1.1.4. `INDEPENDENT`

All transactions will be applied, regardless of failure.

#### 2.1.2. `RawTransactions`

`RawTransactions` contains the list of transactions that will be applied. There can be up to 8 transactions included. There must be at least 2 transactions. These transactions can come from one account or multiple accounts.

Each inner transaction:

- **Must** contain the `tfInnerBatchTxn` flag (see section 3 for details).
- **Must not** have a fee. It must use a fee value of `"0"`.
- **Must not** be signed (the global transaction is already signed by all relevant parties). They must instead have an empty string (`""`) in the `SigningPubKey` field, and the `TxnSignature` field must be omitted.

_Note: the 8 transaction limit can be relaxed in the future._

#### 2.1.3. `BatchSigners`

This field operates similarly to [multi-signing](https://xrpl.org/docs/concepts/accounts/multi-signing/) on the XRPL. It is only needed if multiple accounts' transactions are included in the `Batch` transaction; otherwise, the normal transaction signature provides the same security guarantees.

This field must be provided if more than one account has inner transactions included in the `Batch`. In that case, this field must contain signatures from all accounts whose inner transactions are included, excluding the account signing the outer transaction (if applicable).

Each object in this array contains the following fields:

| FieldName       | Required? | JSON Type | Internal Type |
| :-------------- | :-------- | :-------- | :------------ |
| `Account`       | ✔️        | `string`  | `STAccount`   |
| `SigningPubKey` |           | `string`  | `STBlob`      |
| `TxnSignature`  |           | `string`  | `STBlob`      |
| `Signers`       |           | `array`   | `STArray`     |

Either the `SigningPubKey` and `TxnSignature` fields must be included, or the `Signers` field.

##### 2.1.3.1. `Account`

This is an account that has at least one inner transaction.

##### 2.1.3.2. `SigningPubKey` and `TxnSignature`

These fields are included if the account is signing with a single signature (as opposed to multi-sign). They sign the `Flags` field and the hashes of the transactions in `RawTransactions`.

##### 2.1.3.3. `Signers`

This field is included if the account is signing with multi-sign (as opposed to a single signature). It operates equivalently to the [`Signers` field](https://xrpl.org/docs/references/protocol/transactions/common-fields/#signers-field) used in standard transaction multi-sign. This field holds the signatures for the `Flags` field and the hashes of the transactions in `RawTransactions`.

### 2.2. Transaction Fee

The fee for the outer transaction is:

$$(n+2)*base\textunderscore fee + \sum_{innerTxns} Txn.Fee$$
(where `n` is the number of signatures included in the outer transaction)

In other words, the fee is twice the base fee (a total of 20 drops when there is no fee escalation), plus the sum of the transaction fees of all the inner transactions (which incorporates factors like higher fees for `AMMCreate` or `EscrowFinish`), plus an additional base fee amount for each additional signature in the transaction (e.g. from `BatchSigners`).

The fees for the individual inner transactions are paid here instead of in the inner transaction itself, to ensure that fee escalation is calculated on the total cost of the transaction instead of just the overhead.

### 2.3. Failure Conditions

The standard transaction failure conditions still apply here.

1. The `Flags` field is not set to exactly one of the supported batch modes (`temINVALID_FLAG`).
1. Inner transactions
   1. There are fewer than 2 transactions in the `RawTransactions` field (`temARRAY_EMPTY`).
   2. There are more than 8 transactions in the `RawTransactions` field (`temARRAY_TOO_LARGE`).
   3. The `RawTransactions` field contains a transaction that is not a valid transaction.
   4. One of the inner transactions has a `Fee` greater than 0 (`temBAD_FEE`).
   5. One of the inner transactions has a `TxnSignature` field included (`temBAD_SIGNATURE`).
   6. One of the inner transactions has a non-empty `SigningPubKey` (`temBAD_REGKEY`).
   7. One of the inner transactions is has a `Signers` field included (`temBAD_SIGNER`).
   8. One of the inner transactions has `TransactionType` of `Batch` (`temINVALID`).
   9. One of the inner transactions has a different invalid `TransactionType` (`temINVALID_INNER_BATCH`).
   10. There is a duplicate transaction in the `RawTransactions` field (`temREDUNDANT`).
   11. One of the inner transactions does not have the `tfInnerBatchTxn` flag set (`temINVALID_FLAG`).
   12. One of the inner transactions fails its preflight checks (i.e. is invalid, irrespective of ledger state) (`temINVALID_INNER_BATCH`).
   13. Either both or neither of `TicketSequence` and `Sequence` are set (`temSEQ_AND_TICKET`).
1. `BatchSigners`
   1. The length of `BatchSigners` is greater than the number of transactions in `RawTransactions` (`temARRAY_TOO_LARGE`).
   2. The `BatchSigners` field contains a signature from the account signing the outer transaction (`temBAD_SIGNER`).
   3. The `BatchSigners` field contains a duplicate signature (`temREDUNDANT`).
   4. The `BatchSigners` field contains a signature from an account that does not have any inner transactions (`temBAD_SIGNER`).
   5. The `BatchSigners` field is missing a signature from an account that has inner transactions (`temBAD_SIGNER`).
   6. The `BatchSigners` field contains an invalid signature (`temBAD_SIGNATURE`).
1. Preclaim/doApply errors
   1. The public key for a signer is not a valid public key (`tefBAD_AUTH`). (This should be caught by preflight checks, but it is an additional backup check just in case).
   2. The batch signer is single-signing:
      1. The public key for a signer is not valid for the account ('`tefBAD_AUTH`).
      2. The account is signing with the account's master key, but the master key is disabled (`tefMASTER_DISABLED`).
   3. The batch signer is multi-signing:
      1. The account does not have a signer list (`tefNOT_MULTI_SIGNING`).
      2. The signing account is not a signer on the signer list (`tefBAD_SIGNATURE`).
      3. The `SigningPubkey` field in a `SignerEntry` field is empty or not a valid public key (`tefBAD_SIGNATURE`).
      4. The signing account is signing with the account's master key, but the master key is disabled (`tefMASTER_DISABLED`).
      5. The `SigningPubKey` field is not the `Account`'s master or regular key (`tefBAD_SIGNATURE`).
      6. There is not enough signing weight to meet the `SignerQuorum` (`tefBAD_QUORUM`).

### 2.4. State Changes

The state changes for the outer transaction are the same as for a normal transaction. The state changes for the inner transactions are the same as if they were submitted as normal transactions.

### 2.5. Metadata

The inner transactions will be committed separately to the ledger and will therefore have separate metadata. This is to ensure better backwards compatibility for legacy systems, so they can support `Batch` transactions without needing any changes to their systems.

For example, a ledger that only has one `Batch` transaction containing 2 inner transactions would look like this:

```
[
  OuterTransaction,
  InnerTransaction1,
  InnerTransaction2
]
```

#### 2.5.1. Outer Transactions

Each outer transaction will only contain the metadata for its sequence and fee processing, not for the inner transaction processing. The error code will also only be based on the outer transaction processing (e.g. sequence and fee), and it will return a `tesSUCCESS` error even if the inner transaction processing fails.

#### 2.5.2. Inner Transactions

Each inner transaction will contain the metadata for its own processing. Only the inner transactions that were actually committed to the ledger will be included. This makes it easier for legacy systems to still be able to process `Batch` transactions as if they were normal.

There will also be a pointer back to the parent outer transaction (`ParentBatchID`).

### 2.6. Example JSONs

#### 2.6.1. One Account

In this example, the user is creating an offer while trading on a DEX UI, and the second transaction is a platform fee.

##### 2.6.1.1. Sample Transaction

<details open>
<summary>

The inner transactions are not signed, and the `BatchSigners` field is not needed on the outer transaction, since there is only one account involved.

</summary>

```typescript
{
  TransactionType: "Batch",
  Account: "rUserBSM7T3b6nHX3Jjua62wgX9unH8s9b",
  Flags: 0x00010000,
  RawTransactions: [
    {
      RawTransaction: {
        TransactionType: "OfferCreate",
        Flags: 1073741824,
        Account: "rUserBSM7T3b6nHX3Jjua62wgX9unH8s9b",
        TakerGets: "6000000",
        TakerPays: {
          currency: "GKO",
          issuer: "ruazs5h1qEsqpke88pcqnaseXdm6od2xc",
          value: "2"
        },
        Sequence: 4,
        Fee: "0",
        SigningPubKey: ""
      }
    },
    {
      RawTransaction: {
        TransactionType: "Payment",
        Flags: 1073741824,
        Account: "rUserBSM7T3b6nHX3Jjua62wgX9unH8s9b",
        Destination: "rDEXfrontEnd23E44wKL3S6dj9FaXv",
        Amount: "1000",
        Sequence: 5,
        Fee: "0",
        SigningPubKey: ""
      }
    }
  ],
  Sequence: 3,
  Fee: "40",
  SigningPubKey: "022D40673B44C82DEE1DDB8B9BB53DCCE4F97B27404DB850F068DD91D685E337EA",
  TxnSignature: "3045022100EC5D367FAE2B461679AD446FBBE7BA260506579AF4ED5EFC3EC25F4DD1885B38022018C2327DB281743B12553C7A6DC0E45B07D3FC6983F261D7BCB474D89A0EC5B8"
}
```

</details>

##### 2.6.1.2. Sample Ledger

<details open>
<summary>
This example shows what the ledger will look like after the transaction is confirmed.

Note that the inner transactions are committed as normal transactions.

</summary>

```typescript
[
  {
    TransactionType: "Batch",
    Account: "rUserBSM7T3b6nHX3Jjua62wgX9unH8s9b",
    Flags: 0x00010000,
    RawTransactions: [
      {
        RawTransaction: {
          TransactionType: "OfferCreate",
          Flags: 1073741824,
          Account: "rUserBSM7T3b6nHX3Jjua62wgX9unH8s9b",
          TakerGets: "6000000",
          TakerPays: {
            currency: "GKO",
            issuer: "ruazs5h1qEsqpke88pcqnaseXdm6od2xc",
            value: "2",
          },
          Sequence: 4,
          Fee: "0",
          SigningPubKey: "",
        },
      },
      {
        RawTransaction: {
          TransactionType: "Payment",
          Flags: 1073741824,
          Account: "rUserBSM7T3b6nHX3Jjua62wgX9unH8s9b",
          Destination: "rDEXfrontEnd23E44wKL3S6dj9FaXv",
          Amount: "1000",
          Sequence: 5,
          Fee: "0",
          SigningPubKey: "",
        },
      },
    ],
    Sequence: 3,
    Fee: "40",
    SigningPubKey:
      "022D40673B44C82DEE1DDB8B9BB53DCCE4F97B27404DB850F068DD91D685E337EA",
    TxnSignature:
      "3045022100EC5D367FAE2B461679AD446FBBE7BA260506579AF4ED5EFC3EC25F4DD1885B38022018C2327DB281743B12553C7A6DC0E45B07D3FC6983F261D7BCB474D89A0EC5B8",
  },
  {
    TransactionType: "OfferCreate",
    Flags: 1073741824,
    Account: "rUserBSM7T3b6nHX3Jjua62wgX9unH8s9b",
    TakerGets: "6000000",
    TakerPays: {
      currency: "GKO",
      issuer: "ruazs5h1qEsqpke88pcqnaseXdm6od2xc",
      value: "2",
    },
    Sequence: 4,
    Fee: "0",
    SigningPubKey: "",
  },
  {
    TransactionType: "Payment",
    Flags: 1073741824,
    Account: "rUserBSM7T3b6nHX3Jjua62wgX9unH8s9b",
    Destination: "rDEXfrontEnd23E44wKL3S6dj9FaXv",
    Amount: "1000",
    Sequence: 5,
    Fee: "0",
    SigningPubKey: "",
  },
];
```

</details>

#### 2.6.2. Multiple Accounts

In this example, two users are atomically swapping their tokens, XRP for GKO.

##### 2.6.2.1. Sample Transaction

<details open>
<summary>

The inner transactions are still not signed, but the `BatchSigners` field is needed on the outer transaction, since there are two accounts' inner transactions in this `Batch` transaction.

</summary>

```typescript
{
  TransactionType: "Batch",
  Account: "rUser1fcu9RJa5W1ncAuEgLJF2oJC6",
  Flags: 0x00010000,
  RawTransactions: [
    {
      RawTransaction: {
        TransactionType: "Payment",
        Flags: 1073741824,
        Account: "rUser1fcu9RJa5W1ncAuEgLJF2oJC6",
        Destination: "rUser2fDds782Bd6eK15RDnGMtxf7m",
        Amount: "6000000",
        Sequence: 5,
        Fee: "0",
        SigningPubKey: ""
      }
    },
    {
      RawTransaction: {
        TransactionType: "Payment",
        Flags: 1073741824,
        Account: "rUser2fDds782Bd6eK15RDnGMtxf7m",
        Destination: "rUser1fcu9RJa5W1ncAuEgLJF2oJC6",
        Amount: {
          currency: "GKO",
          issuer: "ruazs5h1qEsqpke88pcqnaseXdm6od2xc",
          value: "2"
        },
        Sequence: 20,
        Fee: "0",
        SigningPubKey: ""
      }
    }
  ],
  BatchSigners: [
    {
      BatchSigner: {
        Account: "rUser2fDds782Bd6eK15RDnGMtxf7m",
        SigningPubKey: "03C6AE25CD44323D52D28D7DE95598E6ABF953EECC9ABF767F13C21D421C034FAB",
        TxnSignature: "304502210083DF12FA60E2E743643889195DC42C10F62F0DE0A362330C32BBEC4D3881EECD022010579A01E052C4E587E70E5601D2F3846984DB9B16B9EBA05BAD7B51F912B899"
      }
    },
  ],
  Sequence: 4,
  Fee: "60",
  SigningPubKey: "03072BBE5F93D4906FC31A690A2C269F2B9A56D60DA9C2C6C0D88FB51B644C6F94",
  TxnSignature: "30440220702ABC11419AD4940969CC32EB4D1BFDBFCA651F064F30D6E1646D74FBFC493902204E5B451B447B0F69904127F04FE71634BD825A8970B9467871DA89EEC4B021F8"
}
```

</details>

##### 2.6.2.2. Sample Ledger

<details open>
<summary>
This example shows what the ledger will look like after the transaction is confirmed.

Note that the inner transactions are committed as normal transactions.

</summary>

```typescript
[
  {
    TransactionType: "Batch",
    Account: "rUser1fcu9RJa5W1ncAuEgLJF2oJC6",
    Flags: 0x00010000,
    RawTransactions: [
      {
        RawTransaction: {
          TransactionType: "Payment",
          Flags: 1073741824,
          Account: "rUser1fcu9RJa5W1ncAuEgLJF2oJC6",
          Destination: "rUser2fDds782Bd6eK15RDnGMtxf7m",
          Amount: "6000000",
          Sequence: 5,
          Fee: "0",
          SigningPubKey: "",
        },
      },
      {
        RawTransaction: {
          TransactionType: "Payment",
          Flags: 1073741824,
          Account: "rUser2fDds782Bd6eK15RDnGMtxf7m",
          Destination: "rUser1fcu9RJa5W1ncAuEgLJF2oJC6",
          Amount: {
            currency: "GKO",
            issuer: "ruazs5h1qEsqpke88pcqnaseXdm6od2xc",
            value: "2",
          },
          Sequence: 20,
          Fee: "0",
          SigningPubKey: "",
        },
      },
    ],
    BatchSigners: [
      {
        BatchSigner: {
          Account: "rUser2fDds782Bd6eK15RDnGMtxf7m",
          SigningPubKey:
            "03C6AE25CD44323D52D28D7DE95598E6ABF953EECC9ABF767F13C21D421C034FAB",
          TxnSignature:
            "304502210083DF12FA60E2E743643889195DC42C10F62F0DE0A362330C32BBEC4D3881EECD022010579A01E052C4E587E70E5601D2F3846984DB9B16B9EBA05BAD7B51F912B899",
        },
      },
    ],
    Sequence: 4,
    Fee: "60",
    SigningPubKey:
      "03072BBE5F93D4906FC31A690A2C269F2B9A56D60DA9C2C6C0D88FB51B644C6F94",
    TxnSignature:
      "30440220702ABC11419AD4940969CC32EB4D1BFDBFCA651F064F30D6E1646D74FBFC493902204E5B451B447B0F69904127F04FE71634BD825A8970B9467871DA89EEC4B021F8",
  },
  {
    TransactionType: "Payment",
    Flags: 1073741824,
    Account: "rUser1fcu9RJa5W1ncAuEgLJF2oJC6",
    Destination: "rUser2fDds782Bd6eK15RDnGMtxf7m",
    Amount: "6000000",
    Sequence: 5,
    Fee: "0",
    SigningPubKey: "",
  },
  {
    TransactionType: "Payment",
    Flags: 1073741824,
    Account: "rUser2fDds782Bd6eK15RDnGMtxf7m",
    Destination: "rUser1fcu9RJa5W1ncAuEgLJF2oJC6",
    Amount: {
      currency: "GKO",
      issuer: "ruazs5h1qEsqpke88pcqnaseXdm6od2xc",
      value: "2",
    },
    Sequence: 20,
    Fee: "0",
    SigningPubKey: "",
  },
];
```

</details>

## 3. Transaction Common Fields

This standard doesn't add any new field to the [transaction common fields](https://xrpl.org/docs/references/protocol/transactions/common-fields/), but it does add another global transaction flag:

| Flag Name         | Value        |
| ----------------- | ------------ |
| `tfInnerBatchTxn` | `0x40000000` |

This flag should only be used if a transaction is an inner transaction in a `Batch` transaction. This signifies that the transaction shouldn't be signed. Any normal transaction that includes this flag should be rejected.

## 4. Rationale

The design of batch transactions prioritizes flexibility, security, and backward compatibility with the existing XRP Ledger infrastructure.

### 4.1. Multiple Batch Modes

Four distinct batch modes (`ALLORNOTHING`, `ONLYONE`, `UNTILFAILURE`, `INDEPENDENT`) were chosen to accommodate a wide range of use cases:

- **`ALLORNOTHING`** is essential for trustless swaps and any scenario where partial completion would leave the system in an undesirable state.
- **`ONLYONE`** enables try-multiple-options patterns, such as submitting offers with different slippage tolerances.
- **`UNTILFAILURE`** provides a middle ground for sequential operations that can partially succeed.
- **`INDEPENDENT`** allows for transaction bundling without strict interdependency.

Alternatives considered included a simpler single-mode design, but this would have forced users to work around limitations for their specific use cases.

### 4.2. Separate Metadata for Inner Transactions

Inner transactions are committed separately to the ledger with their own metadata rather than being embedded within the outer transaction's metadata. This design choice ensures backward compatibility with legacy systems that can continue processing transactions without understanding or adding special support for the `Batch` transaction type. A more compact design with nested metadata was considered but rejected due to the extensive changes it would require for existing infrastructure.

### 4.3. Transaction Limits

The current limit of 8 inner transactions and a minimum of 2 was chosen to balance utility against potential abuse vectors and performance concerns. This limit can be relaxed in future amendments as the community gains experience with how batch transactions are used in practice.

### 4.4. Inner Transaction Safety

Requiring the `tfInnerBatchTxn` flag, prohibiting signatures, and mandating zero fees on inner transactions creates a clear separation between inner and outer transactions. This prevents inner transactions from being extracted and submitted independently, which would bypass the atomicity guarantees and potentially enable theft in multi-account scenarios.

## 5. Security

### 5.1. Trust Assumptions

Regardless of how many accounts' transactions are included in a `Batch` transaction, all accounts need to sign the collection of transactions.

#### 5.1.1. Single Account

In the single account case, this is obvious; the single account must approve all of the transactions it is submitting. No other accounts are involved, so this is a pretty straightforward case.

#### 5.1.2. Multi Account

The multi-account case is a bit more complicated and is best illustrated with an example. Let's say Alice and Bob are conducting a trustless swap via a multi-account `Batch`, with Alice providing 1000 XRP and Bob providing 1000 USD. Bob is going to submit the `Batch` transaction, so Alice must provide her part of the swap to him.

If Alice provides a fully autofilled and signed transaction to Bob, Bob could submit Alice's transaction on the ledger without submitting his and receive the 1000 XRP without losing his 1000 USD. Therefore, the inner transactions must be unsigned.

If Alice just signs her part of the `Batch` transaction, Bob could modify his transaction to only provide 1 USD instead, thereby getting his 1000 XRP at a much cheaper rate. Therefore, the entire `Batch` transaction (and all its inner transactions) must be signed by all parties.

### 5.2. Inner Transaction Safety

An inner batch transaction is a very special case. It doesn't include a signature or a fee (since those are both included in the outer transaction). Therefore, they must be handled very carefully to ensure that someone can't somehow directly submit an inner `Batch` transaction without it being included in an outer transaction.

Namely:

- Inner transactions may not be broadcast (and won't be accepted if they happen to be broadcast, e.g. from a malicious node). They must be generated from the `Batch` outer transaction instead.
- Inner transactions may not be directly submitted via the `submit` RPC.

## 6. Integration Considerations

- An outer `Batch` transaction will return `tesSUCCESS` if the outer transaction succeeds, even if the inner transactions fail. The inner transaction metadata and result codes must be used to determine the actual outcome of each inner transaction.
  - The inner transactions, if validated, **will** be in the same ledger. If it is not in the same ledger, then it is likely a fraud attempt.
- An inner `Batch` transaction will not be validated on its own.
- Systems that don't specifically handle `Batch` transactions should be able to support them without any changes, since each inner transaction will be a valid transaction on its own.
  - All inner transactions that have a `tes` (success) or `tec` result code will be accessible via standard transaction-fetching mechanisms (such as `tx` and `account_tx`).
- Since only the inner transactions and batch mode flags are signed in a multi-account `Batch` transaction, the relayer (submitter of the outer transaction) can adjust the sequence number and fee of the outer transaction as needed, without needing to coordinate with the other parties.

### 6.1. Client Libraries

- `Batch` transactions have a special fee calculation that includes the sum of the inner transaction fees. Client libraries should provide a helper method to calculate the fee for a `Batch` transaction.
- Multi-account `Batch` transactions require a special signing flow where one party signs the outer transaction and the other parties sign the inner transactions. Client libraries should provide a helper method to construct a multi-account `Batch` transaction.
- When auto-filling a `Batch` transaction, the inner transactions must have their `Fee` set to 0 and the `SigningPubKey` and `TxnSignature` fields must be empty. Client libraries should provide a helper method to auto-fill a `Batch` transaction.

### 6.2. Wallets

Wallets should:

- Clearly display all inner transactions to users before requesting a signature, so users understand the full scope of what they are approving.
- For multi-account `Batch` transactions, provide a workflow for users to review and sign their portion of the batch, then export it for other parties to sign.
- Warn users if they are signing a `Batch` transaction that includes inner transactions from other accounts, as they are approving the entire batch.
- Display the batch mode (`ALLORNOTHING`, `ONLYONE`, `UNTILFAILURE`, `INDEPENDENT`) and explain its implications.
- Not auto-increment sequence numbers after successes/failures, since it depends on what/how many transactions are validated.

### 6.3. Explorers and Indexers

Explorers and indexers should:

- Display the relationship between outer `Batch` transactions and their inner transactions using the `ParentBatchID` field.
- Show inner transactions in context with their parent `Batch` transaction, rather than as standalone transactions.
- Consider grouping inner transactions with their outer transaction in transaction lists for clarity.

# Appendix

## Appendix A: FAQ

### A.1: What if I want a more complex tree of transactions that are AND/XORed together? Can I nest `Batch` transactions?

The original version of this spec supported nesting `Batch` transactions. However, upon further analysis, that was deemed a bit too complicated for an initial version of `Batch`, as most of the benefit from this new feature does not require nested transactions. Based on user and community need, this could be added as part of a V2.

### A.2: What if all of the transactions fail? Will a fee still be claimed?

Yes, just as they would if they were individually submitted.

### A.3: Would this feature enable greater frontrunning abilities?

That is definitely a concern. Ways to mitigate this are still being investigated. Some potential answers:

- Charge for more extensive path usage
- Have higher fees for `Batch` transactions
- Submit the `Batch` transactions at the end of the ledger

### A.4: What error is returned if the inner transactions fail (e.g. in `tfALLORNOTHING` or `tfONLYONE`)?

The only way to directly tell that this fails is because unless there is a `tec` error, no inner transaction would be validated. Some debug tools will be provided (such as parsing the rippled debug logs), and ideas to improve this in the future (such as a separate database to store `Batch` outputs) are being discussed.

### A.5: Can another account sign/pay for the outer transaction if they don't have any of the inner transactions?

If there are multiple parties in the inner transactions, yes. Otherwise, no. This is because in a single party `Batch` transaction, the inner transaction's "signature" (which signals approval of the transactions by the accounts submitting them) is provided by the normal transaction signing fields (`SigningPubKey` and `TxnSignature`).

### A.6: How is the `UNTILFAILURE` mode any different than existing behavior with sequence numbers?

Right now, if you submit a series of transactions with consecutive sequence numbers without the use of tickets or `Batch`, then if one fails in the middle, all subsequent transactions will also fail due to incorrect sequence numbers (since the one that failed would have the next sequence numbers).

The difference between the `UNTILFAILURE` mode and this existing behavior is that right now, the subsequent transactions will only fail with a non-`tec` error code. If the failed transaction receives an error code starting with `tec`, then a fee is claimed and a sequence number is consumed, and the subsequent transactions will still be processed as usual.

### A.7: How is the `INDEPENDENT` mode any different than existing behavior with [tickets](https://xrpl.org/docs/concepts/accounts/tickets)?

Tickets require temporarily having a reserve for all the tickets you want to create, but an `INDEPENDENT` mode `Batch` transaction doesn't, for the low cost of 10 extra drops.

On the flip side, tickets are still needed for other use-cases, such as needing to coordinate multiple signers or needing out-of-order transactions.

### A.8: Is it possible for inner transactions to end up in a different ledger than the outer transaction?

No, because the inner transactions skip the transaction queue. They are already effectively processed by the queue via the outer transaction. Inner transactions will also be excluded from consensus for the same reason.

### A.9: How does this work in conjunction with [XLS-75d](https://github.com/XRPLF/XRPL-Standards/discussions/218)? If I give an account powers over the `Batch` transaction, can it effectively run all transaction types?

No, `OnBehalfOf` will not be allowed on `Batch` transactions. Instead, the inner transactions must include the `OnBehalfOf` field.

### A.10: What if I want some error code types to be allowed to proceed, just as `tesSUCCESS` would, in e.g. an `ALLORNOTHING` case?

This was deemed unnecessary. If you have a need for this, please provide example use-cases.

### A.11: Why do the inner transactions need to include sequence numbers?

The primary use of sequence numbers is to prevent hash collisions - two otherwise-identical transactions must have different sequence numbers (or different `TicketSequence` values).

In addition, some objects, such as [offers](https://xrpl.org/docs/references/protocol/ledger-data/ledger-entry-types/offer/#offer-id-format) and [escrows](https://xrpl.org/docs/references/protocol/ledger-data/ledger-entry-types/escrow/#escrow-id-format), use the sequence number of the creation transaction as a part of their ledger entry ID generation, to ensure uniqueness of the IDs.

For this reason, inner transactions must include sequence numbers.

### A.12: What if I want the inner transaction accounts to handle their own fees?

That is not supported. This also allows fee escalation to be calculated on the total cost of the transaction, instead of just on the overhead, and ensures that even if all of the transactions fail, the transaction fees are still charged.

### A.13: Can I create an account and send transactions from it in the same `Batch`?

Yes, as long as you use the master key of that account. Setting a regular key/signer list in the middle of the `Batch` won't work, since that key isn't valid at the time of processing the outer transaction (when the signatures are checked).

### A.14: How will [transaction simulation](https://github.com/XRPLF/XRPL-Standards/tree/master/XLS-0069-simulate) work with Batch?

Some extra processing will be needed for that. As a result, Batch transactions likely won't be able to be simulated at first.
