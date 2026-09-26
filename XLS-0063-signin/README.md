<pre>
  xls: 63
  title: SignIn Transaction
  description: A dedicated transaction type for off-chain signing in with wallets
  author: Denis Angell (@dangell7)
  proposal-from: https://github.com/XRPLF/XRPL-Standards/discussions/187
  created: 2024-03-26
  status: Stagnant
  category: Ecosystem
</pre>

# Problem Statement

In the XRPL ecosystem, certain wallets (Ledger) restrict users from signing arbitrary hex messages as a security measure to protect against malicious activities. This limitation poses a challenge for applications that require user authentication through signature verification. As a result, some applications resort to using low drop Payment transactions as a workaround for authentication, which is not an ideal solution and can lead to unnecessary ledger bloat. To provide a more secure and efficient method for user authentication, a dedicated transaction type for signing in is necessary.

# Proposal

We propose the introduction of a new transaction type called "SignIn" that includes only the common transaction fields along with an additional field, `sfData`, which is an arbitrary data hex field. This transaction type will be specifically designed for applications to authenticate users by allowing them to sign a piece of data that can be verified by the application.

> Importantly, `SignIn` transactions are not intended to be submitted to the ledger.

## New Transaction Type: `SignIn`

The `SignIn` transaction is a new transaction type that allows users to sign an arbitrary piece of data for the purpose of authentication. This transaction type is not intended to transfer any funds or alter the ledger state in any way, but rather to provide a verifiable signature that applications can use to authenticate users.

The transaction has the following fields:

| Field             | Type           | Required | Description                                                               |
| ----------------- | -------------- | -------- | ------------------------------------------------------------------------- |
| sfTransactionType | String         | ✔️       | The type of transaction, which is "SignIn" for this proposal.             |
| sfAccount         | AccountID      | ✔️       | The account of the user signing in.                                       |
| sfData            | VariableLength | ✔️       | The arbitrary data to be signed by the user, represented as a hex string. |

Example `SignIn` transaction:

```json
{
  "Account": "rExampleAccountAddress",
  "TransactionType": "SignIn",
  "Data": "48656C6C6F205852504C2041757468656E7469636174696F6E"
}
```

In this example, the `Data` field contains a hex-encoded string that the user's wallet will sign. The application can then verify the signature against the user's public key to authenticate the user.
