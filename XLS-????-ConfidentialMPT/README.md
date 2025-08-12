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

### MPTokenIssuance Object Extension

The `MPTokenIssuance` object is extended to include the following optional fields to support confidential supply tracking and configurability:

| Field                             | Required | JSON Type | Internal Type         | Description                                                                                                                                                                                                                             |
|----------------------------------|----------|-----------|------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `ConfidentialOutstandingAmount`    | No       | Object    | Struct (EC Point Pair) | EC-ElGamal ciphertext representing the total confidential supply in circulation, encrypted under the issuer’s public key. Updated homomorphically as confidential tokens are issued.                                                  |
| `ConfidentialSupplyZKP`            | No       | Object    | Struct                 | A ZKP object proving that `ConfidentialOutstandingAmount` is well-formed and `ConfidentialOutstandingAmount + IssuerConfidentialBalance = Enc(pk_issuer, MaxAmount − OutstandingAmount − IssuerPublicBalance)`. Includes the ledger index where the proof was generated. Enables stateless public auditability.                        |
| `ConfidentialTransfersEnabled`     | No       | Boolean   | Bool                   | Flag indicating whether confidential transfers are enabled for this token.                                                                                                                                                              |
| `ConfidentialityConfigImmutable`   | No       | Boolean   | Bool                   | If `true`, the `ConfidentialTransfersEnabled` flag cannot be changed after issuance. Ensures regulatory compliance in certain jurisdictions.                                                                                            |
| `IssuerPublicBalance`              | No       | String    | Amount                 | (Optional) The issuer’s current public balance for this token. Useful for monitoring remaining issuance capacity in transparent form.                                                                                                   |
| `IssuerConfidentialBalance`        | No       | Object    | Struct (EC Point Pair) | (Optional) EC-ElGamal ciphertext representing the issuer’s confidential holdings. Used for audits and tracking confidential issuance reserves.                                                                                         |


#### ConfidentialSupplyZKP Structure

| Field         | Required | JSON Type | Internal Type | Description                                                                                                                                                                                                               |
|---------------|----------|-----------|----------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `Proof`       | Yes      | String    | Blob           | ZKP that proves `ConfidentialOutstandingAmount + IssuerConfidentialBalance = MaxAmount − OutstandingAmount − IssuerPublicBalance`. This ensures the total encrypted supply is bounded by the remaining issuance capacity. |
| `LedgerIndex` | Yes      | Number    | UInt32         | Ledger index at which the ZKP was generated. Included to support auditor traceability.                                                                                                                                    |

Example:
```json
{
  "Issuer": "rAlice",
  "Currency": "USD",
  "MaxAmount": "1000",
  "OutstandingAmount": "0",
  "ConfidentialTransfersEnabled": true,
  "ConfidentialityConfigImmutable": true,
  "IssuerPublicBalance": "400",
  "IssuerConfidentialBalance": {
    "A": "...",
    "B": "..."
  },
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

### MPToken Extension

The `MPToken` object (defined in XLS-33) is extended to optionally support confidential balances using EC-ElGamal encryption. These fields enable encrypted value tracking and public auditability without introducing a new ledger object type.

#### Extended Fields

| Field                     | Required     | JSON Type | Internal Type         | Description |
|--------------------------|--------------|-----------|------------------------|-------------|
| `EncryptedBalanceHolder` | No           | Object    | Struct (EC Point Pair) | EC-ElGamal ciphertext representing the balance encrypted under the holder’s public key. |
| `EncryptedBalanceIssuer` | Conditional  | Object    | Struct (EC Point Pair) | EC-ElGamal ciphertext representing the same balance encrypted under the issuer’s public key. Required for non-issuer accounts to enable supply auditability. |
| `HolderPublicKey`        | Conditional  | String    | Blob (compressed EC point) | Holder’s ElGamal public key. Required if `EncryptedBalanceHolder` is present. |


#### Example:

```json
{
  "LedgerEntryType": "MPToken",
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

The following constraints ensure the integrity, verifiability, and correct policy enforcement of confidential MPT balances and supply.

#### Encrypted Supply Bound

- The confidential supply must satisfy the following invariant at all times: `ConfidentialOutstandingAmount + IssuerConfidentialBalance = MaxAmount − OutstandingAmount − IssuerPublicBalance`

- This equality ensures that the encrypted supply (in circulation and held by the issuer) exactly matches the portion of `MaxAmount` that has not been issued or is still held transparently by the issuer.

- Transactions that modify confidential supply :
  - `ConfidentialMPTConvert` (when the sender is a non-issuer), and
  - `ConfidentialMPTSend` (when the sender is the issuer) —
    must preserve this constraint.

- The issuer is responsible for submitting an updated ZKP via the `UpdateConfidentialSupplyZKP` transaction to maintain public auditability.

- The most recent ZKP is stored in the `ConfidentialSupplyZKP` field of the `MPTokenIssuance` object. This allows public observers to verify that the confidential supply accounting is consistent and within bounds without decrypting any values.



#### Encrypted Balance Validity

- All encrypted balances must be well-formed EC-ElGamal ciphertexts.

- For non-issuer accounts, each `MPToken` object must include both:
  - `EncryptedBalanceHolder`: the balance encrypted under the holder’s ElGamal public key.
  - `EncryptedBalanceIssuer`: the same balance encrypted under the issuer’s ElGamal public key.

- Any transaction that creates or modifies confidential balances must include a ZKP that demonstrates:
  - Both ciphertexts are valid EC-ElGamal encryptions.
  - Both ciphertexts encrypt the same plaintext value (i.e., an equality proof).

- For issuer-held confidential balances:
  - The `EncryptedBalanceIssuer` field may be omitted.
  - No equality proof is required, since both ciphertexts would be under the issuer’s own key.




#### Confidential Transfer Policy Enforcement

- If the `ConfidentialTransfersEnabled` flag is set to `false` in the `MPTokenIssuance` object for a given `(Issuer, Currency)` pair, the following transactions must be rejected:
  - `ConfidentialMPTConvert`
  - `ConfidentialMPTSend`

- If `ConfidentialityConfigImmutable` is set to `true`, any attempt to modify the value of `ConfidentialTransfersEnabled` must also be rejected.

These protocol constraints ensure that the confidentiality policy defined at token issuance is strictly enforced, and that all confidential transactions maintain cryptographic integrity and compliance guarantees.


## Transaction Types

To enable confidential transfers of MPTs, this XLS introduces new transaction types that extend XLS-33 with encrypted balances and ZKPs. These transactions support public-to-confidential conversion, encrypted transfers, and audit-friendly supply validation.



---

### Transaction: ConfidentialMPTConvert

#### Purpose

Converts a visible (public) MPT balance into encrypted form by updating the sender’s `MPToken` object with encrypted balance fields. If the sender is the issuer, related supply-tracking fields in the `MPTokenIssuance` object such as `IssuerConfidentialBalance` is also updated.

#### Use Cases

- A non-issuer converts part of their public balance into confidential form for private transfers.
- An issuer converts public supply into confidential form to manage internal reserves or prepare for private issuance.
- Enables public auditability of confidential supply when non-issuers perform conversions.
- Supports hybrid ecosystems where both public and confidential balances coexist and are interoperable.


#### Transaction Fields

| Field                        | Required     | JSON Type | Internal Type         | Description |
|-----------------------------|--------------|-----------|------------------------|-------------|
| `TransactionType`           | Yes          | String    | UInt16                 | Must be `"ConfidentialMPTConvert"` |
| `Account`                   | Yes          | String    | AccountID              | The account initiating the conversion |
| `Issuer`                    | Yes          | String    | AccountID              | Issuer of the token being converted |
| `Currency`                  | Yes          | String    | Currency               | The token code (e.g., `"USD"`) |
| `Amount`                    | Yes          | String    | Amount                 | Public (visible) amount to convert |
| `EncryptedAmountForSender` | Yes          | Object    | Struct (EC Point Pair) | EC-ElGamal ciphertext under the sender’s ElGamal public key |
| `EncryptedAmountForIssuer` | Conditional  | Object    | Struct (EC Point Pair) | EC-ElGamal ciphertext under the issuer’s ElGamal public key. Required if sender is a non-issuer. |
| `SenderPublicKey`           | Yes          | String    | Blob (EC Point)        | The sender’s ElGamal public key |
| `ZKProof`                   | Yes          | Object    | Blob                   | ZKP proving both ciphertexts encrypt the same value and are well-formed |


#### Ledger Changes

- If the sender is a **non-issuer**:
  - Deduct `Amount` from the sender’s public `MPToken` balance.
  - Subtract `Amount` from `OutstandingAmount` in the `MPTokenIssuance` object.
  - Homomorphically add `EncryptedAmountForIssuer` to `ConfidentialOutstandingAmount`.
  - Add `EncryptedAmountForSender` to the sender’s `MPToken` object under the `EncryptedBalanceHolder` field.
  - Add `EncryptedAmountForIssuer` to the sender’s `MPToken` object under the `EncryptedBalanceIssuer` field.
  - Add `HolderPublicKey` to the sender’s `MPToken` object if not already present.

- If the sender is the **issuer**:
  - Subtract `Amount` from `IssuerPublicBalance` in the `MPTokenIssuance` object.
  - Homomorphically add `EncryptedAmountForSender` to `IssuerConfidentialBalance`.


#### Validator Checks

The following validation logic applies to all `ConfidentialMPTConvert` transactions.

##### Common Checks (all senders)

- Confirm `Amount` is a valid, positive value.
- Confirm `EncryptedAmountForSender` is present and well-formed.
- Confirm `SenderPublicKey` is present.
- Verify that the ZKP proves:
  - `EncryptedAmountForSender` is a valid EC-ElGamal encryption of `Amount`.

##### If the sender is a non-issuer:

- Confirm the account has sufficient public `MPToken` balance to cover `Amount`.
- Confirm `EncryptedAmountForIssuer` is present and well-formed.
- Verify the ZKP additionally proves:
  - `EncryptedAmountForIssuer` is a valid EC-ElGamal encryption.
  - It encrypts the same plaintext value as `EncryptedAmountForSender`.
- Ledger updates:
  - Subtract `Amount` from `OutstandingAmount` in `MPTokenIssuance`.
  - Add `EncryptedAmountForIssuer` to `ConfidentialOutstandingAmount`.
  - Update the sender’s `MPToken` object with both `EncryptedBalanceHolder` and `EncryptedBalanceIssuer`.

##### If the sender is the issuer:

- Confirm `Account == Issuer` for the specified `(Issuer, Currency)` pair.
- Confirm `EncryptedAmountForIssuer` is omitted.
- Confirm the issuer has sufficient remaining public balance:
  - `Amount ≤ IssuerPublicBalance`
- Ledger updates:
  - Homomorphically add `EncryptedAmountForSender` to `IssuerConfidentialBalance` in the `MPTokenIssuance` object.

  
### Example: Non-Issuer Converts Public MPT to Confidential Form

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

Transfers confidential MPTs from one account to another using EC-ElGamal encryption. This transaction supports both transfers between non-issuers and transfers from the issuer’s confidential reserve, without revealing the transferred amount.

#### Use Cases

- Issuer → User: Issue confidential tokens without exposing the amount.
- User → User: Transfer confidential tokens between non-issuer accounts privately.

#### Transaction Fields

| Field                         | Required | JSON Type | Internal Type         | Description |
|------------------------------|----------|-----------|------------------------|-------------|
| `TransactionType`            | Yes      | String    | UInt16                 | Must be `"ConfidentialMPTSend"` |
| `Account`                    | Yes      | String    | AccountID              | Sender’s XRPL account address |
| `Destination`                | Yes      | String    | AccountID              | Recipient’s XRPL account address |
| `Issuer`                     | Yes      | String    | AccountID              | Issuer of the MPT |
| `Currency`                   | Yes      | String    | Currency               | Token code (e.g., `"USD"`) |
| `EncryptedAmountForReceiver`| Yes      | Object    | Struct (EC Point Pair) | Ciphertext under receiver’s ElGamal public key |
| `EncryptedAmountForSender`  | Yes      | Object    | Struct (EC Point Pair) | Ciphertext under sender’s ElGamal public key (to subtract from their confidential balance) |
| `EncryptedAmountForIssuer`  | Yes      | Object    | Struct (EC Point Pair) | Ciphertext under issuer’s ElGamal public key (used for audit or supply tracking) |
| `ReceiverPublicKey`         | Yes      | String    | Blob (EC Point)        | Receiver’s ElGamal public key |
| `ZKProof`                   | Yes      | Object    | Blob                   | ZKP proving all ciphertexts encrypt the same value and satisfy balance and supply constraints |






#### Encryption Behavior

The same transfer amount is encrypted under three public keys:

- Receiver’s key → Added to the receiver’s `MPToken` object as `EncryptedBalanceHolder`.
- Sender’s key → Subtracted from the sender’s `MPToken` object as `EncryptedBalanceHolder`.
- Issuer’s key →
  - For non-issuer senders: included for auditability and supply tracking. It is not used in ledger updates.
  - For issuer senders: included for auditability; no supply fields are modified.

A ZKP must confirm:

- All three ciphertexts are well-formed EC-ElGamal encryptions.
- All encrypt the same plaintext amount.
- The transfer amount satisfies one of the following:
  - If the sender is a non-issuer: `Amount ≤ ConfidentialMPTBalance[sender]`
  - If the sender is the issuer: `Amount ≤ IssuerConfidentialBalance`


#### Ledger Changes

##### If the sender is the **issuer**:

- Homomorphically subtract `EncryptedAmountForSender` from `IssuerConfidentialBalance` in the `MPTokenIssuance` object.

- Create or update the receiver’s `MPToken` object:
  - Add `EncryptedAmountForReceiver` under the `EncryptedBalanceHolder` field.
  - Add `EncryptedAmountForIssuer` under the `EncryptedBalanceIssuer` field (for auditability).
  - Set or update `HolderPublicKey` with `ReceiverPublicKey` if not already present.
  - Homomorphically add `EncryptedAmountForIssuer` to `ConfidentialOutstandingAmount` in the `MPTokenIssuance` object.
> Note: `EncryptedAmountForSender` and `EncryptedAmountForIssuer` are encryptions of the same value under the issuer’s public key. Implementations may optimize processing by reusing them internally.

##### If the sender is a **non-issuer**:

- Homomorphically subtract `EncryptedAmountForSender` from the sender’s `MPToken` object (`EncryptedBalanceHolder` field).
- Homomorphically add `EncryptedAmountForReceiver` to the receiver’s `MPToken` object:
  - Add or update `EncryptedBalanceHolder`, `EncryptedBalanceIssuer`, and `HolderPublicKey`.
- `ConfidentialOutstandingAmount` in the `MPTokenIssuance` object remains unchanged.




#### Validator Checks

- Ensure all required fields are present and well-formed:
  - `EncryptedAmountForSender`
  - `EncryptedAmountForReceiver`
  - `EncryptedAmountForIssuer`
  - `ReceiverPublicKey`
  - `ZKProof`

- Verify that the `ZKProof` confirms:
  - All three ciphertexts (`EncryptedAmountForSender`, `EncryptedAmountForReceiver`, and `EncryptedAmountForIssuer`) are valid EC-ElGamal encryptions.
  - All three ciphertexts encrypt the same hidden value (i.e., they are ciphertexts of the same amount).

- Enforce value constraints based on the sender:
- If the sender is the issuer:
  - The `ZKProof` must prove:  
    `Amount ≤ IssuerConfidentialBalance` (stored in `MPTokenIssuance`).
  - Apply a homomorphic update to `ConfidentialOutstandingAmount` using `EncryptedAmountForIssuer`.

- If the sender is a non-issuer:
  - The `ZKProof` must prove:  
    `Amount ≤ EncryptedBalanceHolder` (in the sender’s `MPToken` object).
  - The `EncryptedAmountForSender` must be a valid encryption of the same amount proven in the ZKP and must be subtracted from `EncryptedBalanceHolder`.

- Apply ledger updates:
  - Homomorphically subtract `EncryptedAmountForSender` from the sender’s `EncryptedBalanceHolder`.
  - Homomorphically add `EncryptedAmountForReceiver` to the receiver’s `EncryptedBalanceHolder`.
  - Store `EncryptedAmountForIssuer` in the receiver’s `EncryptedBalanceIssuer`.


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

Allows the issuer of an MPT to update the ZKP (`ConfidentialSupplyZKP`) associated with the encrypted confidential supply (`ConfidentialOutstandingAmount`). This ensures public auditors can verify that the confidential supply remains within the `MaxAmount` limit without decrypting any values.

#### Purpose

- Maintain public auditability of the encrypted confidential token supply.
- Prove that `ConfidentialOutstandingAmount + IssuerConfidentialBalance = Enc(pk_issuer, MaxAmount − OutstandingAmount − IssuerPublicBalance).`
- Allow third-party auditors to verify supply compliance **using only on-ledger data**.

#### Transaction Fields

| Field             | Required | JSON Type | Internal Type | Description                                                                                                                                |
|-------------------|----------|-----------|----------------|--------------------------------------------------------------------------------------------------------------------------------------------|
| `TransactionType` | Yes      | String    | UInt16         | Must be `"UpdateConfidentialSupplyZKP"`                                                                                                    |
| `Account`         | Yes      | String    | AccountID      | Must match the `Issuer`                                                                                                                    |
| `Issuer`          | Yes      | String    | AccountID      | MPT issuer account address                                                                                                                 |
| `Currency`        | Yes      | String    | Currency       | Token code (e.g., `"USD"`)                                                                                                                 |
| `ZKP`             | Yes      | Object    | Blob           | ZKP that `ConfidentialOutstandingAmount + IssuerConfidentialBalance = Enc(pk_issuer, MaxAmount − OutstandingAmount − IssuerPublicBalance)` |
| `LedgerIndex`     | Yes      | Number    | UInt32         | Ledger index at which the proof was generated (for audit traceability)                                                                     |



### Validator Checks

- Authorize & locate token
  - Ensure `Account == Issuer` for the specified `(Issuer, Currency)` pair and the `MPTokenIssuance` object exists.

- Gather current state (pre-apply)
  - Read from `MPTokenIssuance`: `MaxAmount`, `OutstandingAmount`, `IssuerPublicBalance`,
    `ConfidentialOutstandingAmount`, `IssuerConfidentialBalance`,
    and the issuer’s ElGamal public key `pk_issuer`.
  - Compute the plaintext RHS: `rhs = MaxAmount − OutstandingAmount − IssuerPublicBalance`.
  - Form the ciphertext LHS: `LHS = ConfidentialOutstandingAmount + IssuerConfidentialBalance`.

- Verify the submitted proof
  - Verify that `ZKP` proves:
    - `LHS` encrypts the same plaintext as `Enc(pk_issuer, rhs)` (ciphertexts may use different randomness).
    - Both input ciphertexts are valid EC‑ElGamal under `pk_issuer`.
  - The proof must be bound (domain‑separated) to `(Issuer, Currency)` and this transaction type to prevent replay.

- On success
  - Update `MPTokenIssuance.ConfidentialSupplyZKP = { Proof: <bytes>, LedgerIndex }`.
  - No changes to supply fields (`ConfidentialOutstandingAmount`, `IssuerConfidentialBalance`, etc.) are made by this transaction.

- On failure
  - Reject if any field is missing/malformed, if ZKP verification fails, or if the input mismatch is detected.

##### Staleness Checks 

- The transaction MUST include:
  - `InputsLedgerIndex`: ledger index used to generate the ZKP.
  - `StateCommitment`: hash binding the proof to the exact inputs:
    ```
    StateCommitment = H(
      MaxAmount || OutstandingAmount || IssuerPublicBalance ||
      ConfidentialOutstandingAmount || IssuerConfidentialBalance ||
      pk_issuer || Issuer || Currency
    )
    ```
- At apply time, validators MUST:
  1. Read the current values of all inputs from `MPTokenIssuance` and `pk_issuer`.
  2. Recompute `StateCommitment_current` from those values.
  3. Reject if `InputsLedgerIndex` ≠ current ledger index OR `StateCommitment_current` ≠ `StateCommitment`.
  4. Verify the ZKP is transcript‑bound (domain separated) to  
     `(Issuer, Currency, InputsLedgerIndex, StateCommitment, "UpdateConfidentialSupplyZKP")`.

- Rationale:
  - Ensures the proof matches the exact state snapshot it was generated for avoiding acceptance of outdated. 
  - Even if the `InputsLedgerIndex` matches the expected ledger index, multiple transactions affecting the same `MPTokenIssuance` fields can be included in the same ledger close. Without `StateCommitment`, a proof could be computed against an earlier ledger state, causing mismatches that are not detectable by ledger index alone.
  - Allows proofs to remain valid when the ledger index changes but the underlying state values remain unchanged, reducing unnecessary rejections.



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
    - The transferred amount does not exceed `MaxAmount`
    - The dual encryptions (holder and issuer) are consistent (i.e., they encrypt the same value)

- The issuer submits a `ConfidentialSupplyZKP` via `UpdateConfidentialSupplyZKP`:
  - This ZKP proves that the encrypted `ConfidentialOutstandingAmount` is:
    - A well-formed EC-ElGamal ciphertext
    - `ConfidentialOutstandingAmount + IssuerConfidentialBalance
      = Enc(pk_issuer, MaxAmount − OutstandingAmount − IssuerPublicBalance)
      `


#### Audit Procedure

To verify the confidential supply of a specific `(Currency, Issuer)` pair:

1. Scan the ledger at a specific index to obtain:
- The `MPTokenIssuance` object.
- All `ConfidentialMPTBalance` entries encrypted under the issuer’s public key.

2. Filter balances where:
- `Issuer` matches (e.g., `"rAlice"`)
- `Currency` matches (e.g., `"USD"`)
- `PublicKey` equals the issuer’s ElGamal public key (e.g., `pkAlice`)


3. Aggregate the balances by summing all `EncryptedBalance` values homomorphically:
    ```
    Enc_total = Enc_issuer(X1) + Enc_issuer(X2) + ... + Enc_issuer(Xn)
    ```

4. Verify correctness:
- Compare `Enc_total` with `MPTokenIssuance.ConfidentialOutstandingAmount`
- Confirm that the associated `ConfidentialSupplyZKP` proves:
  - `Enc_total` is a well-formed EC-ElGamal ciphertext
  - `ConfidentialOutstandingAmount + IssuerConfidentialBalance
    = Enc(pk_issuer, MaxAmount − OutstandingAmount − IssuerPublicBalance).`

#### Audit Result

If `Enc_total` equals `ConfidentialOutstandingAmount` and the associated `ConfidentialSupplyZKP` successfully verifies, then:

- The confidential circulating supply is correct
- No over-issuance has occurred
- Privacy of individual balances is preserved


## Auditor View Key & Selective Disclosure

This  feature enables **selective disclosure** of confidential transfer amounts to authorized auditors, without revealing values to validators, the public, or other participants. It is designed for regulatory compliance or institutional oversight while preserving privacy for all other parties.

### Purpose
- Allow designated auditors to view confidential transfer amounts using a dedicated ElGamal view key.
- Guarantee correctness through ZKPs without revealing amounts to unauthorized parties.
- Complement public audit mechanisms (e.g., `ConfidentialSupplyZKP`) with scoped, entity-specific transparency.

### Design Overview
- The sender or issuer optionally includes an additional ciphertext encrypted under the auditor’s public view key.
- A ZKP is provided to prove that this ciphertext encrypts the same value as the relevant core transfer ciphertext (e.g., sender, receiver, or issuer encryption).
- The proof reveals no information about the value but guarantees consistency.

### Protocol Elements

| Field                       | Type    | Description                                                                          |
|-----------------------------|---------|--------------------------------------------------------------------------------------|
| `EncryptedAmountForAuditor` | Object  | EC-ElGamal ciphertext of the amount, encrypted under the auditor's public view key   |
| `AuditorPublicKey`          | Binary  | Auditor’s ElGamal public view key                                                    |
| `ZKProof`                   | Object  | Proof that `EncryptedAmountForAuditor` matches the amount in the core ciphertext(s)  |

**ZKP Requirements**
- `EncryptedAmountForAuditor` must be a well-formed EC-ElGamal ciphertext.
- The ZKP must prove equality between the auditor ciphertext and the reference ciphertext used in the transaction (sender, receiver, or issuer).

### Workflow
1. **Issuer/Sender**
  - Encrypts amount `v` under `pk_auditor` → `Enc(pk_auditor, v)`.
  - Generates a ZKP proving `Enc(pk_auditor, v)` matches the reference ciphertext.
2. **Auditor**
  - Verifies the ZKP using public parameters.
  - Decrypts `Enc(pk_auditor, v)` with their private key to learn `v`.
3. **Validators & Public**
  - Cannot decrypt the ciphertext.
  - Can verify the ZKP but learn nothing about `v`.

### Example Transaction Snippet
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

#### Benefits

- Scoped transparency: Only designated auditors with the correct view key can access specific amounts.
- Preserved privacy: Validators and unauthorized users cannot see confidential values.
- Regulatory compliance: Supports institutional audit needs without weakening end-user privacy.

This mechanism complements the broader public audit system (e.g., via `ConfidentialSupplyZKP`) and enables flexible, layered privacy across different trust models.

