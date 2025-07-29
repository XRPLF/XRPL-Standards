# XLS-Confidential-MPT: Confidential Multi-Purpose Token Extension for XRPL
**Authors:** Murat Cenk, Aanchal Malhotra  
**Status:** Draft

## Abstract

This specification introduces **confidential transaction capabilities** to Multi-Purpose Tokens (MPTs) on the XRP Ledger. Confidential MPTs maintain compatibility with the XLS-33 framework and use **EC-ElGamal encryption** with accompanying **zero-knowledge proofs (ZKPs)** for correctness and compliance.

## Motivation

XLS-33 enables powerful tokenization primitives and all transfers and balances are publicly visible. This proposal addresses:

- **Confidentiality**: Hiding the transferred amount
- **Auditability**: Ensuring total encrypted supply remains verifiable without compromising privacy


This is especially relevant for regulated institutions or privacy-sensitive applications.

## Scope

This XLS defines:

- **New transaction types**:
    - `ConfidentialMPTConvert`
    - `ConfidentialMPTSend`
    - `ConfidentialMPTBurn`

- **New ledger fields**:
    - `ConfidentialOutstandingAmount` in the `MPTokenIssuance` object
    - `ConfidentialSupplyZKP` accompanying ConfidentialOutstandingAmount.
    - `ConfidentialMPTBalance` objects stored under Owner Directory
    

- **Encryption mechanisms**:
    - EC-ElGamal with dual-key encryption (issuer + holder)

- **Proof requirements**:
    - ZKPs to validate encrypted transfers and total supply compliance

## Definitions

**MPTokenIssuance (Object):**  A ledger object defined by XLS-33 that records metadata about a MPT, including `Currency`, `Issuer`, `MaxAmount`, `OutstandingAmount`, and optionally `ConfidentialOutstandingAmount`. It resides under the issuer’s Owner Directory.

**MPToken (Object):**  A ledger object representing a user's public balance of a specific MPT. It is created when a non-issuer holds the token and is stored under the holder’s Owner Directory.

**Confidential MPT:**  An MPT balance that is encrypted using EC-ElGamal encryption. Both balances and transfers are private, and operations are verified via ZKPs.

**ConfidentialMPTBalance (Object):**  A new ledger object that stores an encrypted balance and ElGamal `PublicKey`. It is stored in the token holder’s Owner Directory.

**ConfidentialOutstandingAmount (Field):**  An optional field in the `MPTokenIssuance` object that stores the homomorphically accumulated ciphertext representing total confidential supply in circulation (i.e., transferred from issuer to non-issuers). It is an EC-ElGamal ciphertext under the issuer’s key.

**EC-ElGamal Encryption:**  A public-key encryption scheme supporting additive homomorphism. Used to encrypt balances and transfer amounts while allowing encrypted arithmetic and public audit of aggregate supply.

**Zero-Knowledge Proof (ZKP):**  A cryptographic mechanism proving the correctness of confidential operations (e.g., amount validity, consistency of dual encryptions) without revealing sensitive values.

**Dual Encryption:**  A mechanism where confidential token amounts are encrypted under two public keys:
- **Issuer’s ElGamal key:** enables validation and audit of circulating supply.
- **Holder’s ElGamal key:** enables the holder to track and update their encrypted balance.

**Owner Directory:**  A ledger-maintained directory that indexes all objects owned by an account, including `MPToken`, `MPTokenIssuance`, `Offer`, `Check`, and now `ConfidentialMPTBalance`.
## Ledger Format Changes

To support confidential MPTs, we introduce new fields and objects in the XRPL, while preserving compatibility with existing MPT infrastructure as defined in [XLS-33](https://github.com/XRPLF/XRPL-Standards/tree/master/XLS-0033-multi-purpose-tokens).

### MPTokenIssuance Object

The `MPTokenIssuance` object is extended to include two new fields:

- **ConfidentialOutstandingAmount**: An EC-ElGamal ciphertext (under the issuer’s public key) that represents the total amount of confidential tokens in circulation. This field is created upon the first confidential transfer from the issuer and is updated homomorphically as new confidential tokens are sent to non-issuers.
- **ConfidentialSupplyZKP**: A ZKP accompanying ConfidentialOutstandingAmount that proves the encrypted total is a well-formed non-negative value and does not exceed MaxAmount. This ZKP is updated in each confidential transfer and enables public auditors to verify supply compliance without decrypting the underlying values.

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
    "Proof": "zkp_bytes_here",  // ZKP that proves Enc(x) ≤ MaxAmount
    }
  }
```
### ConfidentialMPTBalance Object (New)

This is a new ledger object used to store encrypted token balances.

**Stored under:** Token holder’s Owner Directory

#### Fields

- `LedgerEntryType`: `"ConfidentialMPTBalance"`
- `Issuer`: The MPT issuer account (e.g., `"rAlice"`)
- `Currency`: The token code (e.g., `"USD"`)
- `HolderPublicKey`: The ElGamal public key of the balance owner
- `EncryptedBalanceHolder`: EC-ElGamal ciphertext encrypted under the holder’s key
- `EncryptedBalanceIssuer`: EC-ElGamal ciphertext encrypted under the issuer’s key  
  *(used for validating confidential supply; may be omitted if holder is issuer)*

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

- `ConfidentialOutstandingAmount` must always remain ≤ `MaxAmount`.  
  - This is enforced by ZKPs included with any confidential minting or conversion that increases circulating confidential supply.
  - The ZKP is stored in the `MPTokenIssuance` object to enable public auditability.

- Encrypted balances must be well-formed and non-negative.  
  - For non-issuer holders, each `ConfidentialMPTBalance` must include both:
    - `EncryptedBalanceHolder` (encrypted with holder’s public key)
    - `EncryptedBalanceIssuer` (encrypted with issuer’s public key)  
  - A ZKP must be included to prove equality of the two encryptions, ensuring dual encryption consistency.
  - For issuer-held balances, the issuer may omit `EncryptedBalanceIssuer`, and no equality proof is required.


## Transaction Types

To enable confidential transfers of MPTs, we introduce new transaction types that extend XLS-33 with confidentiality. These transactions support internal conversion, confidential sends, and audit-friendly ledger updates using encryption and ZKPs.


### Transaction: ConfidentialMPTConvert

#### Purpose
Converts publicly held MPT tokens into confidential form by replacing visible balances with encrypted equivalents. Supports privacy-preserving interaction with MPToken assets.


#### Use Cases
- A token holder (issuer or non-issuer) wants to convert part or all of their visible MPToken balance to confidential form.
- Enables gradual migration from transparent to confidential token ecosystems.
- For non-issuers: ensures confidential supply is auditable via issuer-key encrypted balances.
- For issuers: internal conversions remain private and do not affect `ConfidentialOutstandingAmount`.


#### Transaction Fields

| Field                      | Type      | Description |
|---------------------------|-----------|-------------|
| `TransactionType`         | String    | `"ConfidentialMPTConvert"` |
| `Account`                 | Account   | XRPL address of the converter (sender) |
| `Issuer`                  | Account   | Issuer of the MPToken |
| `Currency`                | String    | Token code (e.g., `"USD"`) |
| `Amount`                  | String    | Plain-text amount to convert |
| `EncryptedAmountForSender` | Object   | EC-ElGamal ciphertext (under sender's ElGamal public key) |
| `EncryptedAmountForIssuer` | Object   | EC-ElGamal ciphertext (under issuer's ElGamal public key); optional if sender **is** the issuer |
| `SenderPublicKey`         | Binary    | ElGamal public key of the sender |
| `ZKProof`                 | Object    | ZKP of correctness, including:  <br> (1)  Well-formed encryption  <br> (2) Equality of `EncryptedAmountForSender` and `EncryptedAmountForIssuer`  <br> (3) `Amount` ≤ sender’s public balance  <br> (4) `Amount` ≤ `MaxAmount` |


#### Encryption Behavior
- The transaction generates two ciphertexts for the `Amount`:
  - One encrypted under the **sender’s** ElGamal public key → used for the sender’s `ConfidentialMPTBalance`.
  - One encrypted under the **issuer’s** ElGamal public key → used to update `ConfidentialOutstandingAmount`.
- For the **issuer converting internally**, the second ciphertext may be omitted (no change to `ConfidentialOutstandingAmount`), and no equality proof is required.


 ### Ledger Changes

- Deduct `Amount` from the sender’s public `MPToken` balance.
- Update or create a `ConfidentialMPTBalance` object under the sender’s `Owner Directory`:
  - Add `EncryptedAmountForSender` to their encrypted balance.
- If the sender is a non-issuer:
  - Subtract `Amount` from `MPTokenIssuance.OutstandingAmount`.
  - Homomorphically add `EncryptedAmountForIssuer` to `MPTokenIssuance.ConfidentialOutstandingAmount`.

#### Validator Checks
- Verify:
  - The sender has enough public MPToken balance.
  - `Amount` ≤ `MaxAmount`.
  - The `ZKProof` proves:
    - Both ciphertexts are well-formed and encrypt the same value.
    - Encrypted amount is within valid range.
- If the sender is not the issuer:
  - Enforce homomorphic update to `ConfidentialOutstandingAmount`.
- If the sender is the issuer:
  - Skip updating `ConfidentialOutstandingAmount`.

#### Example JSON

```json
{
  "TransactionType": "ConfidentialMPTConvert",
  "Account": "rBob...",
  "Issuer": "rAlice...",
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
    "type": "DualEncEqualityAndRangeProof",
    "proof": "..."
  }
}
```
---
### Transaction: `ConfidentialMPTSend`

Transfers encrypted Multi-Purpose Tokens (MPTs) confidentially between two parties. Supports both issuer and non-issuer senders.

---

### Purpose

- Enables private token transfers using EC-ElGamal encryption and zero-knowledge proofs.
- Supports both issuer-initiated issuance and confidential transfers among non-issuers.

---

### Use Cases

- **Issuer → Recipient**: Begin confidential circulation of tokens.
- **User → User**: Preserve privacy while transferring confidential tokens.

---

### Transaction Fields

| Field                         | Type     | Description                                                                                      |
|------------------------------|----------|--------------------------------------------------------------------------------------------------|
| `TransactionType`            | String   | `"ConfidentialMPTSend"`                                                                          |
| `Account`                    | Account  | Sender’s XRPL address                                                                             |
| `Destination`                | Account  | Receiver’s XRPL address                                                                           |
| `Issuer`                     | Account  | Issuer of the token                                                                               |
| `Currency`                   | String   | Token code (e.g., `"USD"`)                                                                        |
| `EncryptedAmountForReceiver`| Object   | EC-ElGamal ciphertext under receiver’s public key                                                 |
| `EncryptedAmountForIssuer`  | Object   | EC-ElGamal ciphertext under issuer’s public key (for supply tracking)                            |
| `EncryptedAmountForSender`  | Object   | EC-ElGamal ciphertext under sender’s public key (used for balance subtraction)                   |
| `ReceiverPublicKey`         | Binary   | Receiver’s ElGamal public key                                                                     |
| `ZKProof`                   | Object   | Proves correctness of encryption and amount constraints (see below)                              |

---

### ZKProof Requirements

The zero-knowledge proof MUST attest to the following:

1. **Well-formed ciphertexts**:  
   `EncryptedAmountForReceiver`, `EncryptedAmountForIssuer`, and `EncryptedAmountForSender` are valid EC-ElGamal encryptions.

2. **Amount equality**:  
   All three ciphertexts encrypt the **same value**.

3. **Validity constraint**:  
   - If the sender is the **issuer**:  
     amount ≤ `MaxAmount − OutstandingAmount`
   - If the sender is a **non-issuer**:  
     amount ≤ sender’s `ConfidentialMPTBalance`

---

### Encryption Behavior

- The same amount is encrypted under three keys:
  - **Receiver’s key** → to update `ConfidentialMPTBalance[receiver]`
  - **Issuer’s key** → to update `ConfidentialOutstandingAmount`
  - **Sender’s key** → to deduct from `ConfidentialMPTBalance[sender]`
- The ZKP ensures these encryptions are consistent and the amount is valid.

---

### Ledger Changes

#### 🔹 If Sender is **Issuer**

- **No deduction** from issuer’s encrypted balance (unless holding internal confidential funds).
- **Homomorphically add** `EncryptedAmountForIssuer` to `MPTokenIssuance.ConfidentialOutstandingAmount`.
- **Update or create** `ConfidentialMPTBalance` for receiver:
  - `+ EncryptedAmountForReceiver` under `ReceiverPublicKey`.

#### 🔹 If Sender is **Non-Issuer**

- **Homomorphically subtract** `EncryptedAmountForSender` from sender’s on-ledger `ConfidentialMPTBalance`.
- **Homomorphically add** `EncryptedAmountForReceiver` to receiver’s `ConfidentialMPTBalance`.
- `ConfidentialOutstandingAmount` remains unchanged.

---

### Validator Checks

- Validate `ZKProof` for encryption correctness and value constraints.
- Verify that sender has sufficient encrypted balance (non-issuer).
- Perform homomorphic updates using submitted ciphertexts.
- Ensure ledger entries are updated consistently.

---

### Example (Issuer Sends Confidential Tokens to Bob)

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
    "type": "DualEncEqualityAndRangeProof",
    "proof": "..."
  }
}
```

### Transaction: ConfidentialMPTSend

#### Purpose
Transfers encrypted Multi-Purpose Tokens (MPTs) confidentially between two parties. Supports both issuer and non-issuer senders.

#### Use Cases
- **Issuer** sends confidential tokens to a recipient, initiating confidential circulation.
- **Non-issuer** sends confidential tokens to another party, preserving privacy across transfers.

#### Transaction Fields

| Field                      | Type     | Description                                                                 |
|---------------------------|----------|-----------------------------------------------------------------------------|
| `TransactionType`         | String   | `"ConfidentialMPTSend"`                                                    |
| `Account`                 | Account  | Sender’s XRPL address                                                       |
| `Destination`             | Account  | Receiver’s XRPL address                                                     |
| `Issuer`                  | Account  | Issuer of the token                                                         |
| `Currency`                | String   | Token code (e.g., `"USD"`)                                                  |
| `EncryptedAmountForReceiver` | Object   | EC-ElGamal ciphertext under receiver’s public key                           |
| `EncryptedAmountForIssuer`   | Object   | EC-ElGamal ciphertext under issuer’s public key (for supply tracking)       |
| `ReceiverPublicKey`       | Binary   | Receiver’s ElGamal public key                                               |
| `ZKProof`                 | Object   | ZKProof: Proves the following properties: (1) Both ciphertexts are well-formed EC-ElGamal     encryptions,  <br> (2) Both ciphertexts encrypt the same amount,  <br> (3) If sender is the issuer: amount ≤ (MaxAmount − OutstandingAmount),  <br> (4) If sender is a non-issuer: amount ≤ sender’s ConfidentialMPTBalance|

#### Encryption Behavior

- The transfer amount is encrypted twice:
  - Under the receiver’s ElGamal public key → to update their confidential balance.
  - Under the issuer’s ElGamal public key → to update `ConfidentialOutstandingAmount`.
- A zero-knowledge proof ensures:
  - Both encryptions represent the same amount.
  - The encrypted value is valid and ≤ MaxAmount.


#### Ledger Changes

#### If Sender is Issuer

- `MPTokenIssuance.ConfidentialOutstandingAmount += EncryptedAmountForIssuer`
- Create or update `ConfidentialMPTBalance` for the recipient:
  - `Destination.ConfidentialMPTBalance += EncryptedAmountForReceiver`
- Deduct the amount from the issuer’s `ConfidentialMPTBalance` if the issuer holds converted confidential tokens  
  

#### If Sender is Non-Issuer

- Subtract amount from sender’s `ConfidentialMPTBalance` (under `pkSender`)
- Add amount to recipient’s `ConfidentialMPTBalance` (under `pkReceiver`)
- `MPTokenIssuance.ConfidentialOutstandingAmount` remains unchanged

#### Validator Checks

- Check that sender has sufficient confidential balance
- Validate encryption and ZKP correctness


#### Example JSON (Issuer Sends)

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
  "ReceiverPublicKey": "pkBob...",
  "ZKProof": {
    "type": "DualEncEqualityAndRangeProof",
    "proof": "..."
  }
}
```
### Transaction: ConfidentialMPTBurn

The `ConfidentialMPTBurn` transaction enables a holder to burn confidentially held MPTs. This reduces the encrypted supply tracked in `ConfidentialOutstandingAmount` and updates the corresponding ZKP.



#### Preconditions

- `TransactionType` MUST be `"ConfidentialMPTBurn"`
- Required fields:
  - `Account`, `Issuer`, `Currency`
  - `EncryptedAmount` (ciphertext under issuer’s ElGamal key)
  - `ZKProof` (range proof for `0 ≤ Amount ≤ ConfidentialOutstandingAmount`)



#### Validation Steps

- Confirm `EncryptedAmount` is a valid EC-ElGamal ciphertext.

- Verify `ZKProof` proves:
  - `EncryptedAmount` is well-formed
  - `0 ≤ Amount ≤ ConfidentialOutstandingAmount`

- Confirm the sender has sufficient confidential balance to cover the burn:
  - Locate `ConfidentialMPTBalance` encrypted under sender’s public key
  - Check that the balance is sufficient



#### Ledger Changes

- Homomorphically subtract `EncryptedAmount` from the sender’s `ConfidentialMPTBalance`.

- Homomorphically subtract `EncryptedAmount` from `MPTokenIssuance.ConfidentialOutstandingAmount`.

- Replace `ConfidentialSupplyZKP` with a new proof showing:

  ```text
  Updated ConfidentialOutstandingAmount ≤ MaxAmount

---
### Public Audit of ConfidentialOutstandingAmount

This mechanism allows any observer — including validators, auditors, or third-party users — to **cryptographically verify** the total circulating supply of confidential tokens at any ledger index **without revealing individual balances**.

#### Assumptions

- Each token holder stores their `ConfidentialMPTBalance` encrypted under:
  - Their own public key (e.g., `pkBob`)
  - The issuer’s public key (e.g., `pkAlice`)
- The issuer maintains a `ConfidentialOutstandingAmount` field, which is an **EC-ElGamal ciphertext under `pkAlice`**, updated homomorphically whenever confidential tokens leave the issuer.
- For each confidential transfer (e.g., `ConfidentialMPTSend`, `ConfidentialMPTConvert`), a ZKP is included to:
  - Prove that the transferred amount is valid (non-negative and ≤ MaxAmount)
  - Ensure consistency between the dual encryptions (under issuer and holder keys)
- The issuer includes a **mandatory ZKP** (`ConfidentialSupplyZKP`) with every update to `ConfidentialOutstandingAmount`, proving that the encrypted total is **well-formed and ≤ MaxAmount**.


#### Ledger Storage

- **`MPTokenIssuance` object (under issuer’s Owner Directory)**:
  ```json
  {
    "Issuer": "rAlice",
    "Currency": "USD",
    "MaxAmount": "1000",
    "OutstandingAmount": "0",
    "ConfidentialOutstandingAmount": {
      "A": "...",  // EC-ElGamal component
      "B": "..."
    },
    "ConfidentialSupplyZKP": {
      "Proof": "zkp_bytes_here"  // ZKP: Enc(x) ≤ MaxAmount
    }
  }

- **`ConfidentialMPTBalance`** objects (under each account’s Owner Directory):
```json
  {
    "LedgerEntryType": "ConfidentialMPTBalance",
    "Issuer": "rAlice",
    "Currency": "USD",
    "PublicKey": "pkAlice",
    "EncryptedBalance": {
    "A": "...",
    "B": "..."
    }
  }
```

#### Audit Procedure
To verify the confidential supply:

- Scan the ledger at a specific index. 
- Collect all ConfidentialMPTBalance objects for a specific (Currency, Issuer) pair encrypted under the issuer's key (pkAlice). 
- Extract each:

```json
{
  "Issuer": "rAlice",
  "Currency": "USD",
  "PublicKey": "pkAlice",
  "EncryptedBalance": Enc_issuer(X)
}
```
- Sum all ciphertexts homomorphically:
- Enc_total = + Enc_issuer(X1) + Enc_issuer(X2) + ... 
- Compare Enc_total with ConfidentialOutstandingAmount in MPTokenIssuance.

#### Audit Result
If Enc_total == ConfidentialOutstandingAmount, and the accompanying ConfidentialSupplyZKP verifies that Enc_total ≤ MaxAmount, then:
- The confidential circulating supply is correct
- No over-issuance has occurred 
- Privacy of individual balances is preserved

## Appendix A: Receiver Privacy Extensions for Confidential MPTs

### A.1 Use Case: Receiver Anonymity with Confidential MPT Transfers

This extension introduces **receiver anonymity** to Confidential MPT transfers by allowing the sender to deliver encrypted MPT tokens to a stealth address derived from the recipient’s public viewing and spending keys.

The amount remains confidential (encrypted via EC-ElGamal), and the recipient’s identity is protected via a stealth address scheme.

This transaction:

- Hides both the **recipient’s identity** and the **transferred amount**
- Supports **issuer and non-issuer** senders
- Proves encrypted amount correctness and consistency using **ZKPs**
- Is compatible with `ConfidentialOutstandingAmount` tracking

---

### Transaction Type `ConfidentialMPTStealthSend`

| Field                      | Type      | Required | Description                                                            |
|---------------------------|-----------|----------|------------------------------------------------------------------------|
| `TransactionType`         | String    | Yes      | Must be set to `ConfidentialMPTStealthSend`                           |
| `Account`                 | Account   | Yes      | Sender’s XRPL account                                                  |
| `Issuer`                  | Account   | Yes      | MPT issuer                                                             |
| `Currency`                | String    | Yes      | MPT currency code                                                      |
| `EncryptedAmountReceiver` | Object    | Yes      | EC-ElGamal ciphertext under stealth receiver’s key                     |
| `EncryptedAmountIssuer`   | Object    | Yes      | EC-ElGamal ciphertext under issuer’s key                               |
| `StealthAddress`          | Blob      | Yes      | One-time public key: `P = s·G + B_spend`                               |
| `EphemeralKey`            | Blob      | Yes      | One-time key: `R = r·G`, used in stealth derivation                    |
| `ZKProof`                 | Object    | Yes      | ZKP proving ciphertext equality and range validity                     |

---

### Stealth Key Model

Recipients use two EC keypairs:

| Key Type       | Description                                                                  |
|----------------|------------------------------------------------------------------------------|
| `ViewingKey`   | Detects stealth payments: shared secret is `H(r · B_view)`                   |
| `SpendingKey`  | Spends funds sent to `P = s·G + B_spend`                                     |

---

### Validation and Ledger Behavior

#### Preconditions

- Sender may be issuer or non-issuer.
- `EncryptedAmountReceiver` and `EncryptedAmountIssuer` must be valid EC-ElGamal ciphertexts.
- `ZKProof` must validate:
  - Both ciphertexts encrypt the same value
  - Value is in range: `0 ≤ Amount ≤ MaxAmount`

#### Ledger Updates

#### Ledger Updates

- Subtract `EncryptedAmountReceiver` from the sender’s `ConfidentialMPTBalance`
- Add `EncryptedAmountReceiver` to a new `ConfidentialMPTBalance` under `StealthAddress`
- Add `EncryptedAmountIssuer` to `ConfidentialOutstandingAmount` (only if the sender is the issuer)
- Replace `ConfidentialSupplyZKP` with an updated proof validating the new encrypted total is still `≤ MaxAmount` (must be provided by the sender if supply is updated)

---

### JSON Example

```json
{
  "TransactionType": "ConfidentialMPTStealthSend",
  "Account": "rSenderABC123...",
  "Issuer": "rAlice...",
  "Currency": "USD",
  "EncryptedAmountReceiver": { "A": "...", "B": "..." },
  "EncryptedAmountIssuer": { "A": "...", "B": "..." },
  "StealthAddress": "03fcb9...9d4a",
  "EphemeralKey": "028a17...e5bf",
  "ZKProof": {
    "type": "DualEncEqualityAndRangeProof",
    "proof": "..."
  }
}
```
## Appendix B: Full Privacy Extension for Confidential MPTs

### B.1 Use Case: Full Sender and Receiver Privacy with Ring Signatures

This extension introduces **maximum privacy** for Confidential MPT transfers by combining:

- **Confidential amounts** (via EC-ElGamal encryption)
- **Receiver anonymity** (via stealth addresses)
- **Sender anonymity** (via linkable ring signatures)

In this model, tokens are stored and moved as **confidential notes**, rather than account-based balances. Each note is an encrypted commitment to a value, and transfers occur by spending and creating new notes without linking them to XRPL accounts.

---

### Ledger Object: `ConfidentialMPTNote`

