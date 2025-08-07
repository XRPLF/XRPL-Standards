# XLS-Confidential-MPT: Confidential Multi-Purpose Tokens for XRPL

## Abstract

This specification extends [XLS-33](https://github.com/XRPLF/XRPL-Standards/tree/master/XLS-0033-multi-purpose-tokens) to introduce confidential Multi-Purpose Tokens (MPTs) on the XRP Ledger. It enables ledger-level confidentiality for token transfers and balances using EC-ElGamal encryption and accompanying ZKPs. Confidential MPTs maintain compatibility with existing XLS-33 infrastructure and support public auditability and auditor access.

## Motivation

XLS-33 provides flexible tokenization but exposes all balances and transfers on-chain. This proposal addresses key limitations:

- Confidentiality: Prevents public visibility of transferred amounts and account balances by encrypting them with ElGamal.
- Auditability: Enables public to verify correctness of the confidential supply using ZKPs, without decrypting individual balances.
- Selective disclosure: Allows issuers to optionally include auditor-encrypted ciphertexts, enabling scoped transparency without compromising broader privacy.

This capability is especially valuable for regulated institutions, tokenized financial instruments, and privacy-sensitive applications that require both confidentiality and compliance.

## Scope

This XLS introduces confidential functionality to MPTs by specifying the following components:

### New Transaction Types

- `ConfidentialMPTConvert`: Converts public MPT balances into encrypted form.
- `ConfidentialMPTSend`: Enables confidential token transfers between accounts.
- `UpdateConfidentialSupplyZKP`: Updates the publicZKP  for the total encrypted supply.

### New Ledger Fields and Objects

- `ConfidentialOutstandingAmount`: Encrypted total circulating supply, added to the `MPTokenIssuance` object.
- `ConfidentialSupplyZKP`: A ZKP proving that `ConfidentialOutstandingAmount` is well-formed and bounded by `MaxAmount`.
- `ConfidentialMPTBalance`: A new ledger object that stores encrypted token balances under the holder’s Owner Directory.

### Encryption Mechanisms

- EC-ElGamal encryption with dual-key encryption:
    - One ciphertext under the issuer’s public key (for auditability).
    - One ciphertext under the holder’s public key (for private balance tracking).

### Proof Requirements

- ZKPs are required to:
    - Validate encrypted transfers (e.g., equality and range proofs).
    - Enforce supply correctness via `ConfidentialSupplyZKP`.

## Definitions

**MPTokenIssuance (Object):** A ledger object defined by XLS-33 that stores metadata about a MPT, including `Currency`, `Issuer`, `MaxAmount`, and `OutstandingAmount`. This XLS extends it to optionally include a `ConfidentialOutstandingAmount` and a `ConfidentialSupplyZKP`. It resides in the issuer’s Owner Directory.

**MPToken (Object):** A ledger object representing a user's public balance of a specific MPT. It is created when a non-issuer holds the token and is stored in the holder’s Owner Directory.

**Confidential MPT:** An MPT whose balances and transfers are encrypted using EC-ElGamal. All value transfers are private and verified using ZKPs without revealing the underlying amounts.

**ConfidentialMPTBalance (Object):** A new ledger object introduced by this XLS. It stores encrypted balances under the holder’s Owner Directory, including ciphertexts under both the issuer’s and the holder’s ElGamal public keys.

**ConfidentialOutstandingAmount (Field):** An optional field in the `MPTokenIssuance` object that stores an EC-ElGamal ciphertext under the issuer’s key. It represents the total encrypted supply in circulation, homomorphically accumulated as tokens are sent confidentially from the issuer to others.

**EC-ElGamal Encryption:** A public-key encryption scheme with additive homomorphism. It supports encrypted arithmetic and enables encrypted balance storage and verifiable supply tracking.

**Zero-Knowledge Proof (ZKP):** A cryptographic proof that verifies correctness of operations (e.g., range bounds, encryption equality) without revealing the underlying values.

**Dual Encryption:** A technique in which the same token amount is encrypted twice—once under the holder’s ElGamal key and once under the issuer’s key. This enables holders to privately manage their balances and issuers (or auditors) to verify supply consistency.

**Owner Directory:** A ledger-maintained structure that indexes all objects owned by an account. It includes entries such as `MPToken`, `MPTokenIssuance`, `Offer`, `Check`, and now `ConfidentialMPTBalance`.

## Ledger Format Changes

To support confidential MPTs, this XLS introduces new fields and ledger objects on XRPL while preserving compatibility with existing MPT infrastructure as defined in XLS-33.

### MPTokenIssuance Object

The `MPTokenIssuance` object is extended to include the following optional fields to support confidential supply tracking and configurability:

| Field                             | Required | JSON Type | Internal Type         | Description                                                                                                                                                                                                                            |
|----------------------------------|----------|-----------|------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `ConfidentialOutstandingAmount`  | No       | Object    | Struct (EC Point Pair) | EC-ElGamal ciphertext representing the total confidential supply in circulation, encrypted under the issuer’s public key. Updated homomorphically as confidential tokens are issued.                                                   |
| `ConfidentialSupplyZKP`          | No       | Object    | Struct                 | A ZKP object proving that `ConfidentialOutstandingAmount` is well-formed and less than or equal to `MaxAmount - OutstandingAmount`. Includes the ledger index at which the proof was generated. Enables stateless public auditability. |
| `ConfidentialTransfersEnabled`   | No       | Boolean   | Bool                   | Flag indicating whether confidential transfers are enabled for this token.                                                                                                                                                             |
| `ConfidentialityConfigImmutable` | No       | Boolean   | Bool                   | If set to `true`, the `ConfidentialTransfersEnabled` flag cannot be changed after token issuance. Ensures regulatory compliance in certain regions.                                                                                    |



#### ConfidentialSupplyZKP Structure

| Field         | Required | JSON Type | Internal Type | Description |
|---------------|----------|-----------|----------------|-------------|
| `Proof`       | Yes      | String    | Blob           | ZKP that proves `Enc(x) ≤ MaxAmount` where `x` is the encrypted total confidential supply. |
| `LedgerIndex` | Yes      | Number    | UInt32         | Ledger index at which the ZKP was generated. Included to support auditor traceability. |

Example:
```json
{
  "Issuer": "rAlice",
  "Currency": "USD",
  "MaxAmount": "1000",
  "OutstandingAmount": "0",
  "ConfidentialOutstandingAmount": {
    "A": "...",
    "B": "..."
  },
  "ConfidentialSupplyZKP": {
    "Proof": "zkp_bytes_here",
    "LedgerIndex": 12345678
  }
}
```


### Protocol Rule Enforcement

To preserve the integrity of confidentiality controls, the following validation rules apply when processing confidential MPT transactions:

#### `ConfidentialTransfersEnabled`

- For a given `(Issuer, Currency)` pair, if `ConfidentialTransfersEnabled` is not `true` in the corresponding `MPTokenIssuance` object, then the following transactions must be rejected:
  - `ConfidentialMPTConvert`
  - `ConfidentialMPTSend`
- Validators must return no-permission if these transactions are submitted while confidentiality is disabled.

#### `ConfidentialityConfigImmutable`

- If `ConfidentialityConfigImmutable == true`, any transaction or mechanism that attempts to modify the value of `ConfidentialTransfersEnabled` must be rejected.
- This ensures that once a token’s confidentiality policy is set and locked and it cannot be changed for providing guarantees for regulatory.


### ConfidentialMPTBalance Object (New)

A new ledger object used to store encrypted token balances for a specific `(Issuer, Currency)` pair. Stored in the token holder’s Owner Directory.

#### Fields

| Field                   | Required | JSON Type | Internal Type         | Description |
|------------------------|----------|-----------|------------------------|-------------|
| `LedgerEntryType`      | Yes      | String    | UInt16                 | Must be `"ConfidentialMPTBalance"` |
| `Issuer`               | Yes      | String    | AccountID              | Issuer of the MPT |
| `Currency`             | Yes      | String    | Currency               | Token code (e.g., `"USD"`) |
| `HolderPublicKey`      | Yes      | String    | Blob (compressed EC point) | ElGamal public key of the balance holder |
| `EncryptedBalanceHolder` | Yes    | Object    | Struct (EC Point Pair) | Balance encrypted under the holder’s public key |
| `EncryptedBalanceIssuer` | No     | Object    | Struct (EC Point Pair) | Balance encrypted under the issuer’s public key (used for supply validation; required for non-issuer holders) |

#### Example: Non-Issuer Holding Confidential Balance

```json
{
  "LedgerEntryType": "ConfidentialMPTBalance",
  "Issuer": "rAlice",
  "Currency": "USD",
  "HolderPublicKey": "pkBob",
  "EncryptedBalanceHolder": {
    "A": "...",
    "B": "..."
  },
  "EncryptedBalanceIssuer": {
    "A": "...",
    "B": "..."
  }
}
```

### Ledger Constraints

The following constraints ensure the integrity and verifiability of confidential MPT balances and supply:

- `ConfidentialOutstandingAmount` must always satisfy: `ConfidentialOutstandingAmount ≤ MaxAmount - OutstandingAmount`
- This constraint is enforced via ZKPs included in transactions that increase the encrypted supply (e.g., `ConfidentialMPTConvert`, `ConfidentialMPTSend` from issuer).
- The latest proof is stored in the `ConfidentialSupplyZKP` field of the `MPTokenIssuance` object to enable public auditability.

- Encrypted balances must be well-formed and non-negative.
- For non-issuer accounts, each `ConfidentialMPTBalance` must include both:
  - `EncryptedBalanceHolder` — ciphertext under the holder’s public key
  - `EncryptedBalanceIssuer` — ciphertext under the issuer’s public key
- Transactions that create or update these balances must include a ZKP proving:
  - Both ciphertexts are valid EC-ElGamal encryptions.
  - Both encrypt the same plaintext value (equality proof).
- For issuer-held balances:
  - The issuer may omit `EncryptedBalanceIssuer`.
  - No equality proof is required in this case.

## Transaction Types

To enable confidential transfers of MPTs, this XLS introduces new transaction types that extend XLS-33 with encrypted balances and zero-knowledge proofs. These transactions support public-to-confidential conversion, encrypted transfers, and audit-friendly supply validation.

---

### Transaction: ConfidentialMPTConvert

#### Purpose

Converts a visible (public) MPT balance into encrypted form by creating a `ConfidentialMPTBalance` object and updating the confidential supply if applicable. Supports migration from transparent to confidential token ecosystems.

#### Use Cases

- A non-issuer converts part of their public balance into confidential form.
- An issuer privately manages internal confidential reserves.
- Enables public auditability of confidential supply when non-issuers convert.

#### Transaction Fields

| Field                        | Required | JSON Type | Internal Type | Description |
|-----------------------------|----------|-----------|----------------|-------------|
| `TransactionType`           | Yes      | String    | UInt16         | Must be `"ConfidentialMPTConvert"` |
| `Account`                   | Yes      | String    | AccountID      | The account initiating the conversion |
| `Issuer`                    | Yes      | String    | AccountID      | Issuer of the token being converted |
| `Currency`                  | Yes      | String    | Currency       | The token code (e.g., `"USD"`) |
| `Amount`                    | Yes      | String    | Amount         | Public (visible) amount to convert |
| `EncryptedAmountForSender` | Yes      | Object    | Struct (EC Point Pair) | EC-ElGamal ciphertext under the sender's ElGamal public key |
| `EncryptedAmountForIssuer` | Conditional | Object  | Struct (EC Point Pair) | EC-ElGamal ciphertext under the issuer’s key. Optional if sender is the issuer. |
| `SenderPublicKey`           | Yes      | String    | Blob (EC Point) | The sender's ElGamal public key |
| `ZKProof`                   | Yes      | Object    | Blob           | ZKP proving both ciphertexts encrypt the same value and are well-formed |


#### Ledger Changes

- Deduct `Amount` from sender’s public `MPToken` balance.
- If sender is a non-issue:
  - Subtract `Amount` from `OutstandingAmount`.
  - Add `EncryptedAmountForIssuer` homomorphically to `ConfidentialOutstandingAmount`.
- Add `EncryptedAmountForSender` to the sender’s `ConfidentialMPTBalance` (create or update).
- If sender is the issuer:
  - `OutstandingAmount` and `ConfidentialOutstandingAmount` remain unchanged.
  - `EncryptedAmountForIssuer` may be omitted.


#### Validator Checks

- Confirm that `Account` has sufficient `MPToken` balance.
- If sender is a non-issuer:
  - Enforce `ConfidentialOutstandingAmount + Amount ≤ MaxAmount`.
  - Require both ciphertexts and verify their ZKP.
- If sender is the issuer:
  - `EncryptedAmountForIssuer` may be omitted.
  - ZKP must still prove `EncryptedAmountForSender` is well-formed.
- ZKP must validate:
  - Both ciphertexts (if present) are valid EC-ElGamal encryptions.
  - Both ciphertexts encrypt the same `Amount`.

#### Encryption Behavior

- The transaction includes two EC-ElGamal ciphertexts representing the `Amount`:
  - One encrypted under the sender’s ElGamal public key, used to update the sender’s `ConfidentialMPTBalance`.
  - One encrypted under the issuer’s ElGamal public key, used to update the `ConfidentialOutstandingAmount`.

- If the sender is the issuer, `EncryptedAmountForIssuer` may be omitted.
  - No change is made to `ConfidentialOutstandingAmount`.
  - A ZKP is still required to prove that `EncryptedAmountForSender` is well-formed.


#### Example: Non-Issuer Converts Public MPT to Confidential Form

```json
{
  "TransactionType": "ConfidentialMPTConvert",
  "Account": "rBob",
  "Issuer": "rAlice",
  "Currency": "USD",
  "Amount": "150",
  "EncryptedAmountForSender": {
    "A": "...",
    "B": "..."
  },
  "EncryptedAmountForIssuer": {
    "A": "...",
    "B": "..."
  },
  "SenderPublicKey": "pkBob...",
  "ZKProof": {
    "type": "DualEncEqualityProof",
    "proof": "..."
  }
}
```
---
### Transaction: ConfidentialMPTSend

Transfers confidential MPTs from one account to another using EC-ElGamal encryption. Supports both issuer-initiated issuance and peer-to-peer confidential transfers.


#### Purpose

- Enables confidential transfers of MPTs between accounts.
- Supports confidential issuance from the issuer and confidential transfers between non-issuers.
- Ensures correctness and supply constraints through ZKPs.

#### Use Cases

- Issuer → User: Issue confidential tokens directly without revealing amounts.
- User → User: Transfer confidential tokens privately between non-issuer accounts.

#### Transaction Fields

| Field                        | Required | JSON Type | Internal Type         | Description |
|-----------------------------|----------|-----------|------------------------|-------------|
| `TransactionType`           | Yes      | String    | UInt16                 | Must be `"ConfidentialMPTSend"` |
| `Account`                   | Yes      | String    | AccountID              | Sender’s XRPL account address |
| `Destination`               | Yes      | String    | AccountID              | Recipient’s XRPL account address |
| `Issuer`                    | Yes      | String    | AccountID              | Issuer of the MPT |
| `Currency`                  | Yes      | String    | Currency               | Token code (e.g., `"USD"`) |
| `EncryptedAmountForReceiver`| Yes      | Object    | Struct (EC Point Pair) | Ciphertext under receiver’s ElGamal public key |
| `EncryptedAmountForSender` | Yes      | Object    | Struct (EC Point Pair) | Ciphertext under sender’s ElGamal public key (for subtraction) |
| `EncryptedAmountForIssuer` | Yes      | Object    | Struct (EC Point Pair) | Ciphertext under issuer’s ElGamal public key (used for supply audit or update) |
| `ReceiverPublicKey`         | Yes      | String    | Blob (EC Point)        | Receiver’s ElGamal public key |
| `ZKProof`                   | Yes      | Object    | Blob                   | ZKP proving all ciphertexts encrypt the same value and satisfy supply/balance constraints |


#### Encryption Behavior

The same transfer amount is encrypted under three public keys:

- Receiver’s key → Updates the receiver’s `ConfidentialMPTBalance`.
- Sender’s key → Subtracted from the sender’s `ConfidentialMPTBalance`.
- Issuer’s key →
  - If the sender is the issuer: added to `ConfidentialOutstandingAmount` to reflect issuance.
  - If the sender is a non-issuer: used to enable public auditability via encrypted supply tracking (but no ledger update).

A ZKP confirms:

- All three ciphertexts are well-formed EC-ElGamal encryptions
- All encrypt the same amount
- The encrypted amount satisfies one of the following:
  - Issuer case: `Amount ≤ MaxAmount − OutstandingAmount − ConfidentialOutstandingAmount`
  - Non-issuer case: `Amount ≤ ConfidentialMPTBalance[sender]`

#### Ledger Changes

##### If Sender is the Issuer

- Homomorphically subtract `EncryptedAmountForSender` from the issuer’s `ConfidentialMPTBalance`.

- Homomorphically add `EncryptedAmountForIssuer` to `MPTokenIssuance.ConfidentialOutstandingAmount`.

- Create or update the receiver’s `ConfidentialMPTBalance`:
  - Add `EncryptedAmountForReceiver` to the encrypted balance associated with `ReceiverPublicKey`.

> Note: In this case, `EncryptedAmountForSender` is equal to `EncryptedAmountForIssuer`. To optimize performance and reduce redundancy, implementations should take advantage of this equality during processing.

##### If Sender is a Non-Issuer

- Homomorphically subtract `EncryptedAmountForSender` from the sender’s `ConfidentialMPTBalance`.

- Homomorphically add `EncryptedAmountForReceiver` to the receiver’s `ConfidentialMPTBalance`.

- `ConfidentialOutstandingAmount` remains unchanged.

#### Validator Checks

- Validate that all required fields are present and well-formed.

- Verify the `ZKProof` confirms:
  - `EncryptedAmountForSender`, `EncryptedAmountForReceiver`, and `EncryptedAmountForIssuer` are well-formed EC-ElGamal ciphertexts.
  - All three ciphertexts encrypt the same plaintext amount.

- Enforce value constraints based on sender type:
  - If sender is the issuer:
    - Ensure `amount ≤ MaxAmount − OutstandingAmount − ConfidentialOutstandingAmount`
    - Apply homomorphic update to `ConfidentialOutstandingAmount`
  - If sender is a non-issuer:
    - Ensure `amount ≤ ConfidentialMPTBalance[sender]`

- Apply balance updates:
  - Subtract `EncryptedAmountForSender` from the sender’s confidential balance.
  - Add `EncryptedAmountForReceiver` to the receiver’s confidential balance.


#### Example: Issuer Sends Confidential Tokens to Bob

```json
{
  "TransactionType": "ConfidentialMPTSend",
  "Account": "rAlice",
  "Destination": "rBob",
  "Issuer": "rAlice",
  "Currency": "USD",
  "EncryptedAmountForReceiver": {
    "A": "...",
    "B": "..."
  },
  "EncryptedAmountForIssuer": {
    "A": "...",
    "B": "..."
  },
  "EncryptedAmountForSender": {
    "A": "...",
    "B": "..."
  },
  "ReceiverPublicKey": "pkBob...",
  "ZKProof": {
    "type": "DualEncEqualityProof",
    "proof": "..."
  }
}
```
### Transaction: UpdateConfidentialSupplyZKP

Enables the issuer of a MPT to update the ZKP (`ConfidentialSupplyZKP`) associated with the encrypted confidential supply (`ConfidentialOutstandingAmount`). This transaction allows public auditors to verify that the encrypted supply remains within the limits defined by `MaxAmount`, without decrypting any values.

#### Purpose

- Maintain public auditability of the encrypted confidential token supply.
- Ensure that the latest `ConfidentialOutstandingAmount` is provably less than or equal to `MaxAmount`.
- Enable third-party auditors to verify supply compliance using on-ledger data only.


#### Preconditions

- The transaction must be of type `"UpdateConfidentialSupplyZKP"`.
- The submitting account (`Account`) must be the issuer of the token.
- The `ConfidentialOutstandingAmount` field must already exist in the `MPTokenIssuance` object for the given `(Issuer, Currency)` pair.


#### Transaction Fields

| Field             | Required | JSON Type | Internal Type | Description                                                                 |
|------------------|----------|-----------|----------------|-----------------------------------------------------------------------------|
| `TransactionType`| Yes      | String    | UInt16         | Must be `"UpdateConfidentialSupplyZKP"`                                     |
| `Account`        | Yes      | String    | AccountID      | Must match the `Issuer` field                                               |
| `Issuer`         | Yes      | String    | AccountID      | Address of the token issuer                                                 |
| `Currency`       | Yes      | String    | Currency       | Token code (e.g., `"USD"`)                                                  |
| `ZKP`            | Yes      | Object    | Blob           | ZKP that `ConfidentialOutstandingAmount ≤ MaxAmount- OutstandingAmount`     |
| `LedgerIndex`    | Yes      | Number    | UInt32         | Ledger index at which the proof was generated (used for audit traceability) |

---

#### ZKP Requirements

The submitted ZKP must:

- Prove that `ConfidentialOutstandingAmount` is a valid EC-ElGamal ciphertext.
- Prove that the plaintext encrypted in `ConfidentialOutstandingAmount` is a non-negative integer less than or equal to `MaxAmount`.
- Be generated using the issuer’s ElGamal private key (since only the issuer knows the underlying plaintext).

### Ledger Changes

- Replace the `ConfidentialSupplyZKP` field in the relevant `MPTokenIssuance` object with the new ZKP and associated ledger index.

Example Format:

```json
"ConfidentialSupplyZKP": {
  "Proof": "zkp_bytes_here",
  "LedgerIndex": 12345678
}
```
### Validator Checks

- Ensure the `Account` field matches the `Issuer` for the specified `(Issuer, Currency)` pair.
- Verify that the submitted `ZKP` is valid and corresponds to the current `ConfidentialOutstandingAmount`.
- Update the `ConfidentialSupplyZKP` field in the associated `MPTokenIssuance` object.
- Accept and store the provided `LedgerIndex` for audit traceability, but do not verify its correctness.

### Submission Timing Notes

- The issuer is responsible for tracking updates to `ConfidentialOutstandingAmount`, which may change due to:
  - `ConfidentialMPTConvert` transactions (when the sender is a non-issuer)
  - `ConfidentialMPTSend` transactions (when initiated by the issuer)

- To monitor these changes, the issuer can:
  - Observe the ledger for transactions involving their issued token
  - Subscribe to ledger notifications or scan validated transactions related to the relevant `(Issuer, Currency)` pair

- It is recommended that the issuer submit an `UpdateConfidentialSupplyZKP` transaction:
  - Immediately after any state change to `ConfidentialOutstandingAmount`
  - Or periodically, to ensure the on-ledger audit record remains current

- Delayed updates may result in a stale ZKP, reducing auditability and transparency until the next update is submitted.

#### Example

```json
{
  "TransactionType": "UpdateConfidentialSupplyZKP",
  "Account": "rAlice",
  "Issuer": "rAlice",
  "Currency": "USD",
  "ZKP": {
    "Type": "RangeProofMaxAmount",
    "Proof": "zkp_bytes_here"
  },
  "LedgerIndex": 12345678
}
```
### Public Audit of ConfidentialOutstandingAmount

This mechanism allows any observer, including validators, auditors, or third-party users to cryptographically verify the total circulating supply of confidential tokens at any ledger index without revealing individual balances.

#### Assumptions

- Each token holder maintains a `ConfidentialMPTBalance` containing two ciphertexts:
  - One encrypted under the holder’s ElGamal public key (e.g., `pkBob`)
  - One encrypted under the issuer’s ElGamal public key (e.g., `pkAlice`)

- The issuer maintains a `ConfidentialOutstandingAmount` field in the `MPTokenIssuance` object:
  - This is an EC-ElGamal ciphertext under `pkAlice`
  - It is updated homomorphically whenever confidential tokens are transferred from the issuer to a non-issuer

- For each confidential transfer (`ConfidentialMPTSend`, `ConfidentialMPTConvert`):
  - A ZKP is included to prove:
    - The transferred amount is non-negative and does not exceed `MaxAmount`
    - The dual encryptions (holder and issuer) are consistent (i.e., they encrypt the same value)

- The issuer submits a `ConfidentialSupplyZKP` via `UpdateConfidentialSupplyZKP`:
  - This ZKP proves that the encrypted `ConfidentialOutstandingAmount` is:
    - A well-formed EC-ElGamal ciphertext
    - Encrypts a value ≤ `MaxAmount`
#### Ledger Storage

- `MPTokenIssuance` object (stored under the issuer’s Owner Directory):

```json
  {
    "Issuer": "rAlice",
    "Currency": "USD",
    "MaxAmount": "1000",
    "OutstandingAmount": "0",
    "ConfidentialOutstandingAmount": {
      "A": "...",  // EC-ElGamal ciphertext component
      "B": "..."
    },
    "ConfidentialSupplyZKP": {
      "Proof": "zkp_bytes_here"  // ZKP proving Enc(x) ≤ MaxAmount
    }
  }
```

- `ConfidentialMPTBalance` objects (under each account’s Owner Directory):
```json
  
{
  "LedgerEntryType": "ConfidentialMPTBalance",
  "Issuer": "rAlice",
  "Currency": "USD",
  "PublicKey": "pkAlice",  // Indicates encryption under the issuer’s public key for auditability
  "EncryptedBalance": {
  "A": "...",
  "B": "..."
  }
}
```
#### Audit Procedure

To verify the confidential supply of a specific `(Currency, Issuer)` pair:

1. Scan the ledger at a specific index to obtain:
  - The `MPTokenIssuance` object.
  - All `ConfidentialMPTBalance` entries encrypted under the issuer’s public key.

2. Filter balances where:
  - `Issuer` matches (e.g., `"rAlice"`)
  - `Currency` matches (e.g., `"USD"`)
  - `PublicKey` equals the issuer’s ElGamal public key (e.g., `pkAlice`)

   Example:
```json
    {
      "Issuer": "rAlice",
      "Currency": "USD",
      "PublicKey": "pkAlice",
      "EncryptedBalance": {
        "A": "...",
        "B": "..."
      }
    }
 ```

3. Aggregate the balances by summing all `EncryptedBalance` values homomorphically:
    ```
    Enc_total = Enc_issuer(X1) + Enc_issuer(X2) + ... + Enc_issuer(Xn)
    ```

4. Verify correctness:
  - Compare `Enc_total` with `MPTokenIssuance.ConfidentialOutstandingAmount`
  - Confirm that the associated `ConfidentialSupplyZKP` proves:
    - `Enc_total` is a well-formed EC-ElGamal ciphertext
    - The underlying plaintext is ≤ `MaxAmount`

#### Audit Result

If `Enc_total` equals `ConfidentialOutstandingAmount` and the associated `ConfidentialSupplyZKP` successfully verifies that the encrypted total is ≤ `MaxAmount`, then:

- The confidential circulating supply is correct
- No over-issuance has occurred
- Privacy of individual balances is preserved

### Auditor View Key Support

This feature enables selective disclosure for authorized auditors by allowing confidential amounts to be encrypted under an auditor’s public view key. It supports third-party auditability without exposing sensitive data to the public or validators.

#### Purpose

- Provide regulatory or institutional auditors with access to encrypted transfer amounts.
- Preserve full privacy for all other participants.
- Guarantee correctness through zero-knowledge proofs, without disclosing amounts.

#### Design Overview

- The sender or issuer optionally includes an additional ciphertext encrypted under the auditor’s ElGamal public key.
- A zero-knowledge proof is attached to demonstrate that this ciphertext encrypts the same value as the primary ciphertexts (e.g., sender, receiver, or issuer).

#### Protocol Elements

| Field                     | Type    | Description                                                  |
|---------------------------|---------|--------------------------------------------------------------|
| `EncryptedAmountForAuditor` | Object  | EC-ElGamal ciphertext under the auditor's public key         |
| `AuditorPublicKey`        | Binary  | Auditor’s ElGamal view key                                   |
| `ZKProof`                 | Object  | Zero-knowledge proof that auditor ciphertext matches others  |

#### ZKP Requirements

- `EncryptedAmountForAuditor` must be a well-formed EC-ElGamal ciphertext.
- It must encrypt the same value as the sender/receiver/issuer ciphertexts involved in the transaction.

#### Example Transaction Snippet
```json
{
  "EncryptedAmountForAuditor": {
    "A": "...",   // EC-ElGamal component
    "B": "..."
  },
  "AuditorPublicKey": "pkAuditor...",   // Auditor’s ElGamal public key
  "ZKProof": {
    "type": "TripleEncEqualityProof",   // Proves equality among sender, issuer, and auditor ciphertexts
    "proof": "..."                      // Encoded zero-knowledge proof
  }
}
```

### Selective Disclosure

View key support enables issuers or senders to disclose specific confidential transfer amounts to authorized auditors without revealing these amounts to the public, validators, or other participants.

#### Motivation

Confidential transactions encrypt amounts to protect user privacy. However, regulators or institutional auditors may require access to certain transaction values for compliance or oversight. Since public decryption is not an option, the protocol introduces a selective disclosure mechanism using auditor view keys.

#### Mechanism

The protocol supports optional auditor ciphertexts as part of confidential transfers:

- `EncryptedAmountForAuditor`: An EC-ElGamal ciphertext encrypted under the auditor’s public key (view key).
- `ZKP`: A zero-knowledge proof that confirms this ciphertext encrypts the same value as one of the core transfer ciphertexts (e.g., under sender, receiver, or issuer key).

The proof reveals no information about the underlying value but guarantees consistency across encryptions.

#### Workflow

1. The issuer or sender:
  - Encrypts the transfer amount `v` under the auditor’s public key → `Enc(pk_auditor, v)`
  - Generates a ZK proof that `Enc(pk_auditor, v) = Enc(pk_issuer, v)` (or another known ciphertext)
2. The auditor:
  - Verifies the ZKP using public parameters
  - Decrypts `Enc(pk_auditor, v)` using their private key to learn the plaintext amount
3. Validators and other third parties:
  - Cannot decrypt the ciphertext
  - Can verify the ZK proof but learn nothing about `v`

#### Benefits

- Scoped transparency: Only designated auditors with the correct view key can access specific amounts.
- Preserved privacy: Validators and unauthorized users cannot see confidential values.
- Regulatory compliance: Supports institutional audit needs without weakening end-user privacy.

This mechanism complements the broader public audit system (e.g., via `ConfidentialSupplyZKP`) and enables flexible, layered privacy across different trust models.
