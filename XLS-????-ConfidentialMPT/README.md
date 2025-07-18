# XLS-Confidential-MPT: Confidential Multi-Purpose Token Extension for XRPL
**Authors:** Murat Cenk, Aanchal Malhotra  
**Status:** Draft

## Abstract

This specification introduces **confidential transaction capabilities** to Multi-Purpose Tokens (MPTs) on the XRP Ledger. Confidential MPTs maintain compatibility with the XLS-33 framework and use **EC-ElGamal encryption** with accompanying **zero-knowledge proofs (ZKPs)** for correctness and compliance.

## Motivation

While XLS-33 enables powerful tokenization primitives (e.g., for CBDCs, reward points, stablecoins), all transfers and balances are publicly visible. This proposal addresses:

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

- **MPToken**: A Multi-Purpose Token defined by [XLS-33d](https://github.com/XRPLF/XRPL-Standards/tree/master/XLS-0033-multi-purpose-tokens), representing a fungible asset issued on XRPL with associated issuance metadata and ledger tracking.

- **Confidential MPT**: An MPT whose balance and transfer amounts are encrypted using EC-ElGamal encryption.

- **ConfidentialMPTBalance**: A ledger object representing an encrypted balance for a specific `(Currency, Issuer)` pair, associated with a holder's ElGamal public key. These are stored under the account's **Owner Directory**.

- **ConfidentialOutstandingAmount**: An encrypted field in the `MPTokenIssuance` object that tracks the total amount of confidential tokens in circulation. It is updated homomorphically with each confidential transfer leaving the issuer.

- **EC-ElGamal Encryption**: A public key encryption scheme used to encrypt balances and transfer amounts. It supports additive homomorphism, enabling encrypted values to be added without decryption.

- **Zero-Knowledge Proof (ZKP)**: A cryptographic proof that validates correctness of a confidential operation (e.g., that a transfer amount is non-negative and ≤ MaxAmount) without revealing any private information.

- **Dual Encryption**: Confidential token amounts are encrypted using both the **holder’s** and the **issuer’s** ElGamal public keys:
    - Holder encryption allows local balance updates.
    - Issuer encryption allows validation and audit of circulating supply.

- **Owner Directory**: A ledger structure used to index and store objects owned by an account, such as `MPToken`, `Offer`, and now `ConfidentialMPTBalance` objects.

## Ledger Format Changes

To support confidential MPTs, we introduce new fields and objects in the XRPL, while preserving compatibility with existing MPT infrastructure as defined in [XLS-33d](https://github.com/XRPLF/XRPL-Standards/tree/master/XLS-0033-multi-purpose-tokens).

### MPTokenIssuance Object

The `MPTokenIssuance` object is extended to include a new field:

- **ConfidentialOutstandingAmount**:An EC-ElGamal ciphertext (under the issuer’s public key) that represents the total amount of confidential tokens in circulation. This field is only created and updated after the first confidential transfer from the issuer. Homomorphic addition updates this field and ensure it never exceeds MaxAmount, with accompanying zero-knowledge proofs for correctness.


```json
{
  "Issuer": "rAlice",
  "Currency": "USD",
  "MaxAmount": "1000",
  "OutstandingAmount": "0",
  "ConfidentialOutstandingAmount": {
    "A": "...",  // EC-ElGamal ciphertext component
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
Converts publicly held MPT tokens into encrypted confidential form within the token holder's account.

**Use Cases**:
- An issuer converts their own tokens before distribution.
- A non-issuer (e.g., Bob) converts public tokens they received into confidential form.

**Transaction Fields**:

| Field                     | Type     | Description |
|--------------------------|----------|-------------|
| `TransactionType`        | String   | `"ConfidentialMPTConvert"` |
| `Account`                | Account  | The address initiating the conversion |
| `Issuer`                 | Account  | The MPT issuer |
| `Currency`               | String   | The token code (e.g., "USD") |
| `Amount`                 | UInt64   | Amount to convert (plaintext) |
| `PublicKey`              | Binary   | ElGamal public key of the converter (used to generate encrypted balance) |
| `ZKProof`                | Object   | Zero-knowledge proof of correct dual encryption (issuer & holder) |

**Encryption Behavior**:
- The `Amount` is encrypted twice using EC-ElGamal:
    - Under the token holder’s public key → to form the `ConfidentialMPTBalance`
    - Under the issuer’s public key → to increment the `ConfidentialOutstandingAmount`

**Ledger Changes**:
- Subtract `Amount` from the sender’s public MPToken balance.
- Create or update a `ConfidentialMPTBalance` object for the sender.
- Increment `MPTokenIssuance.ConfidentialOutstandingAmount` homomorphically.

**Validator Checks**:
- Ensure the sender has at least `Amount` in public MPToken balance.
- Verify zero-knowledge proof (ZKP) showing equality of both ciphertexts.
- Ensure updated `ConfidentialOutstandingAmount` does not exceed `MaxAmount`.

**Example JSON**:
```json
{
  "TransactionType": "ConfidentialMPTConvert",
  "Account": "rBob...",
  "Issuer": "rAlice...",
  "Currency": "USD",
  "Amount": "150",
  "PublicKey": "pkBob...",
  "ZKProof": {
    "type": "EqualityProof",
    "proof": "..."
  }
}
```
