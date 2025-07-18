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

The `MPTokenIssuance` object is extended to include a new field:

- **ConfidentialOutstandingAmount**:An EC-ElGamal ciphertext (under the issuer’s public key) that represents the total amount of confidential tokens in circulation. This field is only created and updated after the first confidential transfer from the issuer. Homomorphic addition updates this field and ensure it never exceeds MaxAmount, with accompanying ZKPs for correctness.


```json
{
  "Issuer": "rAlice",
  "Currency": "USD",
  "MaxAmount": "1000",
  "OutstandingAmount": "0",
  "ConfidentialOutstandingAmount": {
    "A": "...", //EC-ElGamal ciphertext component
    "B": "..."
  }
}
```

### ConfidentialMPTBalance Object (New)

This is a new ledger object used to store encrypted token balances.

- Stored under: The token holder’s Owner Directory

- Fields:

    - Issuer: The MPT issuer account 
    - Currency: The token code (e.g., "USD")
    - PublicKey: ElGamal public key of the balance owner 
    - EncryptedBalance: EC-ElGamal ciphertext representing the balance
```json
{
  "LedgerEntryType": "ConfidentialMPTBalance",
  "Issuer": "rAlice",
  "Currency": "USD",
  "PublicKey": "pkBob",
  "EncryptedBalance": {
    "A": "...",
    "B": "..."
  }
}
```
### Ledger Constraints
- ConfidentialOutstandingAmount must always remain ≤ MaxAmount, enforced by ZKPs in transactions. 
- Encrypted balances must be non-negative and valid under both the holder’s and the issuer’s keys, enforced via dual encryption and equality proofs. 
- The structure of AccountRoot remains unchanged to preserve XRPL performance and compatibility.

## Transaction Types

To enable confidential transfers of Multi-Purpose Tokens (MPTs), we introduce new transaction types that extend XLS-33 with privacy-preserving features. These transactions support internal conversion, confidential sends, and audit-friendly ledger updates using encryption and zero-knowledge proofs.

---

### `ConfidentialMPTConvert`

**Purpose**:  
Converts publicly held MPT tokens into confidential form, moving them from a visible balance to an encrypted balance.

**Use Cases**:
- A token holder wants to hide part or all of their publicly visible MPT balance.
- Supports transitioning between public and confidential ecosystems.

**Transaction Fields**:

| Field                     | Type     | Description |
|--------------------------|----------|-------------|
| `TransactionType`        | String   | `"ConfidentialMPTConvert"` |
| `Account`                | Account  | Sender’s XRPL address |
| `Issuer`                 | Account  | Issuer of the MPT |
| `Currency`               | String   | Token code (e.g., "USD") |
| `Amount`                 | String   | Amount to convert (plain integer) |
| `EncryptedAmountForSender` | Object | EC-ElGamal ciphertext under sender's public key |
| `EncryptedAmountForIssuer` | Object | EC-ElGamal ciphertext under issuer's public key |
| `SenderPublicKey`        | Binary   | Sender’s ElGamal public key |
| `ZKProof`                | Object   | Zero-knowledge proof proving: <br> (1) the encryption is well-formed, <br> (2) `EncryptedAmountForSender == EncryptedAmountForIssuer`, <br> (3) amount ≤ public balance, <br> (4) amount ≤ `MaxAmount` |

**Encryption Behavior**:
- Converts a plain `Amount` into two ciphertexts:
    - One under the sender’s ElGamal key (used for their encrypted balance).
    - One under the issuer’s ElGamal key (used for tracking `ConfidentialOutstandingAmount`).
- Encrypted balances are created or updated for both.

**Ledger Changes**:
- Deduct `Amount` from sender’s public MPToken balance.
- Add `EncryptedAmountForSender` to sender’s `ConfidentialMPTBalance`.
- Add `EncryptedAmountForIssuer` to `MPTokenIssuance.ConfidentialOutstandingAmount` (homomorphically).

**Validator Checks**:
- Verify sender has enough public MPT balance.
- Verify correctness of all encryptions and equality via `ZKProof`.
- Ensure total confidential supply remains ≤ `MaxAmount`.

**Example JSON**:
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
