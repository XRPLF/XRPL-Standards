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
- **ConfidentialSupplyZKP**: A zero-knowledge proof accompanying ConfidentialOutstandingAmount that proves the encrypted total is a well-formed non-negative value and does not exceed MaxAmount. This ZKP is updated in each confidential transfer and enables public auditors to verify supply compliance without decrypting the underlying values.

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

- The structure of `AccountRoot` remains unchanged.  
  - `ConfidentialMPTBalance` objects are stored in the account’s Owner Directory for modularity and scalability.

## Transaction Types

To enable confidential transfers of MPTs, we introduce new transaction types that extend XLS-33 with confidentiality. These transactions support internal conversion, confidential sends, and audit-friendly ledger updates using encryption and ZKPs

---

### Transaction: ConfidentialMPTConvert

#### Purpose
Converts publicly held MPT tokens into confidential form by replacing visible balances with encrypted equivalents. Supports privacy-preserving interaction with MPToken assets.

---

#### Use Cases
- A token holder (issuer or non-issuer) wants to convert part or all of their visible MPToken balance to confidential form.
- Enables gradual migration from transparent to confidential token ecosystems.
- For non-issuers: ensures confidential supply is auditable via issuer-key encrypted balances.
- For issuers: internal conversions remain private and do not affect `ConfidentialOutstandingAmount`.

---

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
| `ZKProof`                 | Object    | Zero-knowledge proof of correctness, including:  <br> (1)  Well-formed encryption  <br> (2) Equality of `EncryptedAmountForSender` and `EncryptedAmountForIssuer`  <br> (3) `Amount` ≤ sender’s public balance  <br> (4) `Amount` ≤ `MaxAmount` |

---

#### Encryption Behavior
- The transaction generates two ciphertexts for the `Amount`:
  - One encrypted under the **sender’s** ElGamal public key → used for the sender’s `ConfidentialMPTBalance`.
  - One encrypted under the **issuer’s** ElGamal public key → used to update `ConfidentialOutstandingAmount`.
- For the **issuer converting internally**, the second ciphertext may be omitted (no change to `ConfidentialOutstandingAmount`), and no equality proof is required.

---

#### Ledger Changes
- Deduct `Amount` from the sender’s **public** MPToken balance.
- Update or create a `ConfidentialMPTBalance` object under the sender’s Owner Directory:
  - Add `EncryptedAmountForSender` to their encrypted balance.
- For non-issuer accounts:
  - Homomorphically add `EncryptedAmountForIssuer` to `MPTokenIssuance.ConfidentialOutstandingAmount`.

---

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

---

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
